"""Public startup-profile behavior through the CLI and shared pipeline."""

import json
import wave

import pytest
from pydantic import ValidationError

from stt_services.cli import main
from stt_services.config import Settings
from stt_services.schemas import EngineResult, Segment


def test_cli_uses_one_resolved_profile_and_publishes_engine_observations(tmp_path, monkeypatch):
    source = tmp_path / "speech.wav"
    with wave.open(str(source), "wb") as audio:
        audio.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        audio.writeframes(b"\x00\x00" * 16000)
    monkeypatch.setenv("STT_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("STT_CPU_THREADS", "2")
    monkeypatch.setenv("STT_BEAM_SIZE", "3")
    constructed_profiles = []

    class ObservedEngine:
        def __init__(self, configured):
            self.profile = configured.resolve_profile()
            constructed_profiles.append(self.profile)

        def transcribe(self, path):
            return EngineResult(
                segments=[Segment(0.125, 0.875, "Hello สวัสดี")],
                effective_configuration={
                    "device": "cpu",
                    "compute_type": "int8",
                    "beam_size": self.profile.beam_size,
                    "cpu_threads": self.profile.cpu_threads,
                },
                observations={
                    "language_source": "auto_detected",
                    "detected_language": "th",
                    "measured_language_probability": 0.91,
                    "fallback_attempt_count": None,
                },
            )

    output = tmp_path / "result"
    assert (
        main(
            ["transcribe", str(source), "--output-dir", str(output)],
            engine_factory=ObservedEngine,
        )
        == 0
    )
    report = json.loads((output / "transcript.json").read_text(encoding="utf-8"))
    configuration = report["configuration"]
    assert constructed_profiles[0].beam_size == 3
    assert constructed_profiles[0].cpu_threads == 2
    assert configuration["profile_id"] == constructed_profiles[0].profile_id
    assert configuration["effective"] == {
        "device": "cpu",
        "compute_type": "int8",
        "beam_size": 3,
        "cpu_threads": 2,
    }
    assert configuration["observations"]["measured_language_probability"] == 0.91
    assert report["source_sha256"] is None


def test_resolved_profile_is_immutable_and_has_stable_identity():
    settings = Settings(cpu_threads=2, beam_size=3)
    profile = settings.resolve_profile()

    assert profile.profile_id == settings.resolve_profile().profile_id
    assert profile.cpu_threads == 2
    assert profile.beam_size == 3
    try:
        profile.beam_size = 5
    except Exception as exc:
        assert "frozen" in str(exc).lower()
    else:
        raise AssertionError("Resolved startup profiles must be immutable")


@pytest.mark.parametrize(
    "values",
    [
        {"device": "cuda", "compute_type": "int8"},
        {"mode": "sequential", "batch_size": 2},
        {"mode": "batched", "vad_enabled": False},
        {"initial_prompt": "context", "hotwords": "hint"},
    ],
)
def test_invalid_profile_combinations_fail_during_settings_resolution(values):
    with pytest.raises(ValidationError):
        Settings(**values).resolve_profile()


def test_invalid_environment_profile_fails_before_media_processing(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("STT_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("STT_DEVICE", "cuda")
    monkeypatch.setenv("STT_COMPUTE_TYPE", "int8")
    output = tmp_path / "result"

    def forbidden_engine(configured):
        raise AssertionError("Invalid startup profile must fail before inference")

    assert (
        main(
            ["transcribe", str(tmp_path / "missing.wav"), "--output-dir", str(output)],
            engine_factory=forbidden_engine,
        )
        == 1
    )
    assert "cuda transcription requires" in capsys.readouterr().err.lower()
    assert not output.exists()
