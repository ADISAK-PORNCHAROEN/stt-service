import json
import wave

from stt_services.cli import main
from stt_services.domain.transcript_entities import Segment


class FakeEngine:
    def transcribe(self, path):
        return [Segment(start=0.125, end=0.875, text="ทดสอบ Apple ราคาใหม่")]


def test_cli_transcribes_to_json_and_preserves_original(tmp_path, settings):
    source = tmp_path / "ตัวอย่าง.wav"
    with wave.open(str(source), "wb") as audio:
        audio.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        audio.writeframes(b"\x00\x00" * 16000)
    original = source.read_bytes()
    output = tmp_path / "result"
    assert (
        main(
            ["transcribe", str(source), "--output-dir", str(output)],
            engine_factory=lambda settings: FakeEngine(),
        )
        == 0
    )
    result = json.loads((output / "transcript.json").read_text(encoding="utf-8"))
    assert result["segments"][0] == {
        "id": 1,
        "start": 0.125,
        "end": 0.875,
        "text": "ทดสอบ Apple ราคาใหม่",
        "timing_source": "model",
    }
    assert result["model"] == "turbo"
    assert source.read_bytes() == original


def test_cli_exports_srt_and_utf8_text_without_retranscribing(tmp_path, settings):
    source = tmp_path / "sample.wav"
    with wave.open(str(source), "wb") as audio:
        audio.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        audio.writeframes(b"\x00\x00" * 16000)
    output = tmp_path / "result"
    assert (
        main(
            ["transcribe", str(source), "--output-dir", str(output)],
            engine_factory=lambda settings: FakeEngine(),
        )
        == 0
    )
    assert (output / "transcript.txt").read_text(encoding="utf-8") == "ทดสอบ Apple ราคาใหม่\n"
    assert (output / "transcript.srt").read_text(encoding="utf-8") == (
        "1\n00:00:00,125 --> 00:00:00,875\nทดสอบ Apple ราคาใหม่\n\n"
    )


def test_cli_empty_speech_is_success(tmp_path, settings, wav_bytes):
    source = tmp_path / "silence.wav"
    source.write_bytes(wav_bytes)

    class SilentEngine:
        def transcribe(self, path):
            return []

    output = tmp_path / "result"
    assert (
        main(
            ["transcribe", str(source), "--output-dir", str(output)],
            engine_factory=lambda _: SilentEngine(),
        )
        == 0
    )
    assert json.loads((output / "transcript.json").read_text())["segments"] == []
    assert (output / "transcript.srt").read_text() == ""


def test_cli_refuses_existing_output_without_overwriting(
    tmp_path, settings, wav_bytes, engine_factory
):
    source = tmp_path / "speech.wav"
    source.write_bytes(wav_bytes)
    output = tmp_path / "result"
    output.mkdir()
    marker = output / "keep.txt"
    marker.write_text("keep")
    assert (
        main(
            ["transcribe", str(source), "--output-dir", str(output)], engine_factory=engine_factory
        )
        == 1
    )
    assert marker.read_text() == "keep"
    assert list(output.iterdir()) == [marker]


def test_cli_rejects_invalid_engine_timestamps_without_publishing(tmp_path, settings, wav_bytes):
    source = tmp_path / "speech.wav"
    source.write_bytes(wav_bytes)

    class BadEngine:
        def transcribe(self, path):
            return [Segment(0.5, 10, "outside the one-second recording")]

    output = tmp_path / "result"
    assert (
        main(
            ["transcribe", str(source), "--output-dir", str(output)],
            engine_factory=lambda _: BadEngine(),
        )
        == 1
    )
    assert not output.exists()


def test_cli_export_failure_does_not_publish_partial_bundle(
    tmp_path, settings, wav_bytes, engine_factory, monkeypatch
):
    from pathlib import Path

    source = tmp_path / "speech.wav"
    source.write_bytes(wav_bytes)
    original_write = Path.write_text

    def fail_srt(path, *args, **kwargs):
        if path.suffix == ".srt":
            raise OSError("Disk full")
        return original_write(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_srt)
    output = tmp_path / "result"
    assert (
        main(
            ["transcribe", str(source), "--output-dir", str(output)], engine_factory=engine_factory
        )
        == 1
    )
    assert not output.exists()
    assert not list(tmp_path.glob(".stt-*"))
    assert source.read_bytes() == wav_bytes


def test_benchmark_reuses_loaded_model_for_warm_run(tmp_path, settings, wav_bytes):
    source = tmp_path / "speech.wav"
    source.write_bytes(wav_bytes)
    output = tmp_path / "bench"
    loaded = False

    def factory(_):
        nonlocal loaded
        if loaded:
            raise RuntimeError("Engine must be reused in the warm run")
        loaded = True
        return FakeEngine()

    assert (
        main(["benchmark", str(source), "--output-dir", str(output)], engine_factory=factory) == 0
    )
    report = json.loads((output / "benchmark.json").read_text())
    assert [run["run"] for run in report["runs"]] == ["cold", "warm"]
    assert report["runs"][1]["metrics"]["model_load_seconds"] == 0
    assert (output / "cold/transcript.txt").read_bytes() == (
        output / "warm/transcript.txt"
    ).read_bytes()
