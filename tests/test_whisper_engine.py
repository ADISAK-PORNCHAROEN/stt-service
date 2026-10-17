"""Pinned faster-whisper adapter contracts tested without loading model weights."""

from types import SimpleNamespace

import ctranslate2
import faster_whisper
import pytest

from stt_services.config import Settings
from stt_services.engines.whisper import WhisperEngine
from stt_services.schemas import EngineResult


class FakeModel:
    def __init__(self, *, actual_device="cpu", actual_compute_type="int8_float32"):
        self.model = SimpleNamespace(device=actual_device, compute_type=actual_compute_type)
        self.calls = []

    def transcribe(self, path, **kwargs):
        self.calls.append(kwargs)
        if kwargs.get("vad_parameters") is not None:
            kwargs["vad_parameters"].pop("max_speech_duration_s", None)
        segments = [
            SimpleNamespace(
                start=0.125,
                end=0.875,
                text=" Hello สวัสดี ",
                avg_logprob=-0.2,
                no_speech_prob=0.01,
                compression_ratio=1.1,
                temperature=0.0,
            )
        ]
        info = SimpleNamespace(
            duration=1.0,
            duration_after_vad=0.9,
            language="th",
            language_probability=1.0,
        )
        return iter(segments), info


def patch_sequential_model(monkeypatch, actual_compute_type="int8_float32"):
    model = FakeModel(actual_compute_type=actual_compute_type)
    monkeypatch.setattr(faster_whisper, "download_model", lambda model_name: "revision-test")
    monkeypatch.setattr(
        faster_whisper,
        "WhisperModel",
        lambda *args, **kwargs: _check_and_return_model(model, kwargs),
    )
    return model


def _check_and_return_model(model, kwargs):
    model.constructor_kwargs = kwargs
    return model


def test_sequential_engine_uses_profile_and_returns_actual_observations(tmp_path, monkeypatch):
    model = patch_sequential_model(monkeypatch)
    settings = Settings(data_dir=tmp_path, language_mode="th", condition_on_previous_text=False)
    engine = WhisperEngine(settings)
    first = engine.transcribe(tmp_path / "one.wav")
    second = engine.transcribe(tmp_path / "two.wav")

    assert isinstance(first, EngineResult)
    assert first.segments[0].text == "Hello สวัสดี"
    assert model.constructor_kwargs["device"] == "cpu"
    assert model.constructor_kwargs["compute_type"] == "int8"
    assert model.calls[0]["language"] == "th"
    assert model.calls[0]["condition_on_previous_text"] is False
    assert model.calls[0]["word_timestamps"] is False
    assert model.calls[0]["without_timestamps"] is False
    assert model.calls[0]["chunk_length"] == 30
    assert model.calls[0]["vad_parameters"] == model.calls[1]["vad_parameters"]
    assert model.calls[0]["vad_parameters"] is not model.calls[1]["vad_parameters"]
    assert first.effective_configuration["compute_type"] == {
        "requested": "int8",
        "actual": "int8_float32",
    }
    assert first.observations["language_source"] == "forced"
    assert first.observations["measured_language_probability"] is None
    assert first.observations["fallback_attempt_count"] is None
    assert first.observations["segment_diagnostics"]["count"] == 1
    assert (
        second.effective_configuration["profile_id"] == first.effective_configuration["profile_id"]
    )


def test_batched_engine_explicitly_reports_semantic_changes_and_fresh_vad(monkeypatch, tmp_path):
    model = FakeModel(actual_device="cpu", actual_compute_type="int8_float32")
    expected_model = model
    batched_calls = []

    class FakeBatch:
        def __init__(self, model):
            assert model is expected_model

        def transcribe(self, path, **kwargs):
            batched_calls.append(kwargs)
            kwargs["vad_parameters"].pop("max_speech_duration_s", None)
            return model.transcribe(path, **kwargs)

    monkeypatch.setattr(faster_whisper, "download_model", lambda model_name: "revision-test")
    monkeypatch.setattr(faster_whisper, "WhisperModel", lambda *args, **kwargs: model)
    monkeypatch.setattr(faster_whisper, "BatchedInferencePipeline", FakeBatch)
    engine = WhisperEngine(Settings(data_dir=tmp_path, mode="batched", batch_size=2))
    result = engine.transcribe(tmp_path / "speech.wav")
    engine.transcribe(tmp_path / "speech-again.wav")

    assert batched_calls[0]["batch_size"] == 2
    assert batched_calls[0]["without_timestamps"] is False
    assert batched_calls[0]["word_timestamps"] is False
    assert batched_calls[0]["temperature"] == [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    assert result.effective_configuration["temperature_schedule"] == [0.0]
    assert result.effective_configuration["fallback_behavior"] == "single_temperature_only"
    assert result.effective_configuration["condition_on_previous_text"] == "unsupported_ignored"
    assert batched_calls[0]["vad_parameters"] is not batched_calls[1]["vad_parameters"]
    assert result.effective_configuration["mode"] == "batched"
    assert result.effective_configuration["model_window_seconds"] == 30


def test_explicit_cuda_without_runtime_fails_without_constructing_cpu_model(tmp_path, monkeypatch):
    model_construction = []
    monkeypatch.setattr(faster_whisper, "download_model", lambda model_name: "revision-test")
    monkeypatch.setattr(
        faster_whisper,
        "WhisperModel",
        lambda *args, **kwargs: model_construction.append(kwargs),
    )
    monkeypatch.setattr(ctranslate2, "get_cuda_device_count", lambda: 0)

    with pytest.raises(RuntimeError, match="CUDA device"):
        WhisperEngine(Settings(data_dir=tmp_path, device="cuda", compute_type="float16"))
    assert model_construction == []


def test_multilingual_window_mode_and_private_prompt_are_reported_truthfully(tmp_path, monkeypatch):
    model = patch_sequential_model(monkeypatch)
    settings = Settings(
        data_dir=tmp_path,
        language_mode="multilingual_per_window",
        initial_prompt="private allowed vocabulary",
        temperature_zero=True,
    )
    engine = WhisperEngine(settings)
    result = engine.transcribe(tmp_path / "speech.wav")

    assert model.calls[0]["language"] is None
    assert model.calls[0]["multilingual"] is True
    assert model.calls[0]["temperature"] == [0.0]
    assert model.calls[0]["initial_prompt"] == "private allowed vocabulary"
    assert result.effective_configuration["language_mode"] == "multilingual_per_window"
    assert result.effective_configuration["initial_prompt_sha256"]
    assert "private allowed vocabulary" not in str(result.effective_configuration)
    assert result.observations["language_source"] == "per_window_multilingual"
    assert result.observations["fallback_attempt_count"] is None


def test_cuda_success_records_capability_load_and_device_wide_memory(monkeypatch, tmp_path):
    model = FakeModel(actual_device="cuda", actual_compute_type="float16")
    monkeypatch.setattr(faster_whisper, "download_model", lambda model_name: "revision-test")
    monkeypatch.setattr(faster_whisper, "WhisperModel", lambda *args, **kwargs: model)
    monkeypatch.setattr(ctranslate2, "get_cuda_device_count", lambda: 1)
    monkeypatch.setattr(
        ctranslate2, "get_supported_compute_types", lambda device, device_index=0: {"float16"}
    )
    memory = [
        {"status": "observed", "used_mib": 700, "total_mib": 6144},
        {"status": "observed", "used_mib": 1800, "total_mib": 6144},
    ]
    import stt_services.engines.whisper as whisper_module

    monkeypatch.setattr(whisper_module, "_gpu_memory_snapshot", lambda index: memory.pop(0))
    result = WhisperEngine(
        Settings(data_dir=tmp_path, device="cuda", compute_type="float16")
    ).transcribe(tmp_path / "speech.wav")

    assert result.effective_configuration["runtime"]["device_capability"] == "available"
    assert result.effective_configuration["runtime"]["model_load"] == "succeeded"
    assert result.effective_configuration["compute_type"] == {
        "requested": "float16",
        "actual": "float16",
    }
    assert result.observations["gpu_memory"]["sampled_max_used_mib"] == 1800
    assert result.observations["gpu_memory"]["attribution"] == (
        "device-wide reading may include other processes"
    )


def test_unsupported_cuda_compute_fails_before_model_download(monkeypatch, tmp_path):
    downloaded = []
    monkeypatch.setattr(
        faster_whisper, "download_model", lambda model_name: downloaded.append(model_name)
    )
    monkeypatch.setattr(ctranslate2, "get_cuda_device_count", lambda: 1)
    monkeypatch.setattr(
        ctranslate2, "get_supported_compute_types", lambda device, device_index=0: {"float16"}
    )

    with pytest.raises(RuntimeError, match="unsupported"):
        WhisperEngine(Settings(data_dir=tmp_path, device="cuda", compute_type="int8_float16"))
    assert downloaded == []
