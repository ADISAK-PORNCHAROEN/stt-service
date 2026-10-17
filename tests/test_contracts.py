"""Additional input, canonical output and crash-window acceptance contracts."""

import io
import os
import wave
from fractions import Fraction

import av
import pytest
from fastapi.testclient import TestClient

import stt_services.audio as audio_module
from stt_services.api import create_app
from stt_services.cli import main
from stt_services.jobs import DAY, JobStore
from stt_services.schemas import Segment
from stt_services.worker import Worker


def test_mp4_audio_offset_preserves_original_video_timeline(settings, engine_factory):
    buffer = io.BytesIO()
    with av.open(buffer, "w", format="mov") as container:
        video = container.add_stream("mpeg4", rate=1)
        video.width = video.height = 16
        video.pix_fmt = "yuv420p"
        audio = container.add_stream("pcm_s16le", rate=16000)
        audio.layout = "mono"
        for index in range(7):
            frame = av.VideoFrame(16, 16, "yuv420p")
            frame.pts = index
            frame.time_base = Fraction(1)
            for plane in frame.planes:
                plane.update(bytes(plane.buffer_size))
            for packet in video.encode(frame):
                container.mux(packet)
        for packet in video.encode():
            container.mux(packet)
        frame = av.AudioFrame(format="s16", layout="mono", samples=16000)
        frame.sample_rate = 16000
        frame.pts = 5 * 16000
        for plane in frame.planes:
            plane.update(bytes(plane.buffer_size))
        for packet in audio.encode(frame):
            container.mux(packet)
        for packet in audio.encode():
            container.mux(packet)
    with TestClient(create_app(settings)) as client, Worker(settings, engine_factory) as worker:
        response = client.post("/jobs", files={"file": ("delayed.mp4", buffer.getvalue())})
        assert response.status_code == 202, response.text
        worker.run_once()
        job_id = response.json()["job_id"]
        result = client.get(f"/jobs/{job_id}/result").json()
        assert result["duration_seconds"] == 7
        assert result["segments"][0]["start"] == 5.125
        assert result["segments"][0]["end"] == 5.875


def test_mp4_timestamp_gaps_are_restored(settings):
    buffer = io.BytesIO()
    with av.open(
        buffer,
        "w",
        format="mov",
        options={"movflags": "frag_keyframe+empty_moov", "frag_duration": "500000"},
    ) as container:
        audio = container.add_stream("pcm_s16le", rate=16000)
        audio.layout = "mono"
        for offset in (0, 3 * 16000):
            frame = av.AudioFrame(format="s16", layout="mono", samples=16000)
            frame.sample_rate = 16000
            frame.pts = offset
            for plane in frame.planes:
                plane.update(bytes(plane.buffer_size))
            for packet in audio.encode(frame):
                container.mux(packet)
        for packet in audio.encode():
            container.mux(packet)

    class GapEngine:
        def transcribe(self, path):
            return [Segment(0.125, 0.875, "ก่อนช่วงว่าง"), Segment(1.125, 1.875, "หลังช่วงว่าง")]

    with (
        TestClient(create_app(settings)) as client,
        Worker(settings, lambda _: GapEngine()) as worker,
    ):
        response = client.post("/jobs", files={"file": ("gaps.mp4", buffer.getvalue())})
        assert response.status_code == 202, response.text
        worker.run_once()
        result = client.get(f"/jobs/{response.json()['job_id']}/result").json()
        assert result["segments"][1]["start"] == 3.125
        assert result["segments"][1]["end"] == 3.875


def test_api_rejects_audio_with_too_many_source_timeline_spans(settings, monkeypatch):
    monkeypatch.setattr(audio_module, "MAX_TIMELINE_SPANS", 1, raising=False)
    buffer = io.BytesIO()
    with av.open(
        buffer,
        "w",
        format="mov",
        options={"movflags": "frag_keyframe+empty_moov", "frag_duration": "500000"},
    ) as container:
        audio = container.add_stream("pcm_s16le", rate=16000)
        audio.layout = "mono"
        for offset in (0, 3 * 16000):
            frame = av.AudioFrame(format="s16", layout="mono", samples=16000)
            frame.sample_rate = 16000
            frame.pts = offset
            for plane in frame.planes:
                plane.update(bytes(plane.buffer_size))
            for packet in audio.encode(frame):
                container.mux(packet)
        for packet in audio.encode():
            container.mux(packet)

    with TestClient(create_app(settings)) as client:
        response = client.post("/jobs", files={"file": ("fragmented.mp4", buffer.getvalue())})
    assert response.status_code == 422
    assert list(settings.jobs_dir.iterdir()) == []


def test_resampled_tail_rounding_remains_within_source_duration(settings, tmp_path):
    source = tmp_path / "fractional.wav"
    with wave.open(str(source), "wb") as audio:
        audio.setparams((1, 2, 44100, 0, "NONE", "not compressed"))
        audio.writeframes(b"\x00\x00" * 44101)

    class ResampledEngine:
        def transcribe(self, path):
            return [Segment(0, 16001 / 16000, "ปลายเสียง")]

    output = settings.data_dir / "tail-rounding"
    assert (
        main(
            ["transcribe", str(source), "--output-dir", str(output)],
            engine_factory=lambda _: ResampledEngine(),
        )
        == 0
    )
    import json

    transcript = json.loads((output / "transcript.json").read_text(encoding="utf-8"))
    assert transcript["segments"][0]["end"] == 44101 / 44100
    assert transcript["segments"][0]["end"] <= transcript["duration_seconds"]


@pytest.mark.parametrize(
    ("suffix", "format_name", "codec"),
    [
        (".mp3", "mp3", "libmp3lame"),
        (".m4a", "ipod", "aac"),
        (".flac", "flac", "flac"),
        (".mp4", "mp4", "aac"),
    ],
)
def test_supported_encoded_audio_can_be_uploaded_and_processed(
    settings, engine_factory, suffix, format_name, codec
):
    buffer = io.BytesIO()
    with av.open(buffer, "w", format=format_name) as container:
        stream = container.add_stream(codec, rate=16000)
        stream.layout = "mono"
        frame = av.AudioFrame(format="s16", layout="mono", samples=16000)
        frame.sample_rate = 16000
        frame.pts = 0
        for plane in frame.planes:
            plane.update(bytes(plane.buffer_size))
        for packet in stream.encode(frame):
            container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    with TestClient(create_app(settings)) as client, Worker(settings, engine_factory) as worker:
        response = client.post("/jobs", files={"file": ("recording" + suffix, buffer.getvalue())})
        assert response.status_code == 202, response.text
        assert worker.run_once()
        job_id = response.json()["job_id"]
        result = client.get(f"/jobs/{job_id}/result").json()
        assert result["segments"][0]["start"] == 0.125
        assert result["text"] == "ทดสอบ Apple ราคาใหม่"
        assert result["timing_source"] == "model"
        assert result["segments"][0]["id"] == 1
        assert ":\\" not in result["source_name"]


def test_srt_rounds_across_minute_and_keeps_original_silence_offset(tmp_path, settings):
    source = tmp_path / "minute.wav"
    with wave.open(str(source), "wb") as audio:
        audio.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        audio.writeframes(b"\x00\x00" * (61 * 16000))

    class TailEngine:
        def transcribe(self, path):
            return [Segment(59.9996, 60.5004, "ท้ายคลิป English")]

    output = settings.data_dir / "cli-tail"
    assert (
        main(
            ["transcribe", str(source), "--output-dir", str(output)],
            engine_factory=lambda _: TailEngine(),
        )
        == 0
    )
    assert (output / "transcript.srt").read_text(encoding="utf-8") == (
        "1\n00:01:00,000 --> 00:01:00,500\nท้ายคลิป English\n\n"
    )


def test_cli_cannot_publish_into_managed_cleanup_tree(
    settings, tmp_path, wav_bytes, engine_factory
):
    source = tmp_path / "audio.wav"
    source.write_bytes(wav_bytes)
    output = settings.jobs_dir / "custom"
    assert (
        main(
            ["transcribe", str(source), "--output-dir", str(output)], engine_factory=engine_factory
        )
        == 1
    )
    assert not output.exists()


def test_crash_after_result_rename_is_interrupted_and_never_advertised(
    settings, engine_factory, wav_bytes, monkeypatch
):
    from pathlib import Path

    rename = Path.rename

    def crash_after_rename(path, destination):
        result = rename(path, destination)
        if Path(destination).name == "result":
            raise KeyboardInterrupt("Simulated OS interruption after publication")
        return result

    with TestClient(create_app(settings)) as client:
        job_id = client.post("/jobs", files={"file": ("audio.wav", wav_bytes)}).json()["job_id"]
        with monkeypatch.context() as fault:
            fault.setattr(Path, "rename", crash_after_rename)
            with pytest.raises(KeyboardInterrupt), Worker(settings, engine_factory) as worker:
                worker.run_once()
        assert client.get(f"/jobs/{job_id}").json()["status"] == "running"
        assert (settings.jobs_dir / job_id / "result").is_dir()
        with Worker(settings, engine_factory):
            failed = client.get(f"/jobs/{job_id}").json()
            assert failed["error"] == "interrupted"
            assert client.get(f"/jobs/{job_id}/result").status_code == 409
        JobStore(settings).cleanup(now=failed["finished_at"] + DAY)
        assert not (settings.jobs_dir / job_id).exists()


def test_cleanup_removes_only_inactive_stale_orphans(settings):
    store = JobStore(settings)
    now = 2_000_000_000.0
    stale = settings.jobs_dir / ".upload-stale"
    stale.mkdir()
    (stale / "input.wav").write_bytes(b"orphan")
    os.utime(stale, (now - DAY, now - DAY))
    fresh = settings.jobs_dir / ".upload-fresh"
    fresh.mkdir()
    os.utime(fresh, (now, now))
    store.cleanup(now=now)
    assert not stale.exists()
    assert fresh.exists()
