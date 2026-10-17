"""faster-whisper adapter for the immutable startup profile."""

import hashlib
import math
import os
import shutil
import subprocess
from pathlib import Path
from statistics import fmean
from typing import Any, cast

from stt_services.config import ResolvedProfile, Settings
from stt_services.schemas import EngineResult, Segment


class WhisperEngine:
    def __init__(self, settings: Settings) -> None:
        settings.prepare()
        self.profile = settings.resolve_profile()
        if self.profile.device == "cuda":
            self.runtime_capability = self._validate_cuda_runtime()
        else:
            self.runtime_capability = {"device_capability": "cpu_selected"}

        from faster_whisper import WhisperModel, download_model

        model_path = download_model(self.profile.model)
        self.revision = Path(model_path).name
        self.model = WhisperModel(
            model_path,
            device=self.profile.device,
            device_index=self.profile.device_index,
            compute_type=self.profile.compute_type,
            cpu_threads=self.profile.cpu_threads,
        )
        backend_model = getattr(self.model, "model", None)
        self.runtime_capability = {
            **self.runtime_capability,
            "model_load": "succeeded",
            "actual_device": str(getattr(backend_model, "device", "unreported")),
            "actual_compute_type": str(getattr(backend_model, "compute_type", "unreported")),
        }
        self.batched_model: Any | None = None
        if self.profile.mode == "batched":
            from faster_whisper import BatchedInferencePipeline

            self.batched_model = BatchedInferencePipeline(model=self.model)

    def _validate_cuda_runtime(self) -> dict[str, object]:
        try:
            import ctranslate2  # type: ignore[import-untyped]

            count = ctranslate2.get_cuda_device_count()
        except (ImportError, RuntimeError, OSError) as exc:
            raise RuntimeError(
                "CUDA was requested, but the installed CTranslate2 runtime cannot query devices"
            ) from exc
        if self.profile.device_index >= count:
            raise RuntimeError(
                f"CUDA device {self.profile.device_index} is unavailable; "
                f"the runtime reports {count} visible device(s)"
            )
        try:
            supported = ctranslate2.get_supported_compute_types("cuda", self.profile.device_index)
        except (RuntimeError, OSError) as exc:
            raise RuntimeError("Could not query CUDA compute types from CTranslate2") from exc
        if self.profile.compute_type not in supported:
            choices = ", ".join(sorted(supported)) or "none"
            raise RuntimeError(
                f"CUDA compute type {self.profile.compute_type} is unsupported on device "
                f"{self.profile.device_index}; supported types: {choices}"
            )
        return {
            "device_capability": "available",
            "visible_device_count": count,
            "device_index": self.profile.device_index,
            "supported_compute_types": sorted(supported),
            "requested_compute_type_supported": True,
        }

    def transcribe(self, path: Path) -> EngineResult:
        profile = self.profile
        target = self.batched_model if profile.mode == "batched" else self.model
        assert target is not None
        language, multilingual = _language_arguments(profile)
        # BatchedInferencePipeline mutates this dictionary by removing
        # max_speech_duration_s, so every invocation receives a new object.
        vad_parameters = dict(profile.vad_parameters) if profile.vad_enabled else None
        options: dict[str, object] = {
            "task": "transcribe",
            "language": language,
            "multilingual": multilingual,
            "beam_size": profile.beam_size,
            "temperature": profile.temperature_schedule,
            "vad_filter": profile.vad_enabled,
            "vad_parameters": vad_parameters,
            "condition_on_previous_text": profile.condition_on_previous_text,
            "word_timestamps": False,
            "without_timestamps": False,
            "chunk_length": profile.model_window_seconds,
            "initial_prompt": profile.initial_prompt,
            "hotwords": profile.hotwords,
        }
        if profile.mode == "batched":
            # The pinned batched implementation documents previous-text
            # conditioning as unused and only consumes the first temperature.
            options.pop("condition_on_previous_text")
            options["batch_size"] = profile.batch_size
        gpu_memory_before = (
            _gpu_memory_snapshot(profile.device_index) if profile.device == "cuda" else None
        )
        raw_segments, info = target.transcribe(str(path), **options)
        gpu_memory_after = (
            _gpu_memory_snapshot(profile.device_index) if profile.device == "cuda" else None
        )
        raw_segments = list(raw_segments)
        segments = [
            Segment(
                min(float(segment.start), float(info.duration)),
                min(float(segment.end), float(info.duration)),
                segment.text.strip(),
            )
            for segment in raw_segments
        ]
        return EngineResult(
            segments=segments,
            effective_configuration=self._effective_configuration(),
            observations=self._observations(
                info,
                upstream_segments=raw_segments,
                gpu_memory_before=gpu_memory_before,
                gpu_memory_after=gpu_memory_after,
            ),
        )

    def _effective_configuration(self) -> dict[str, object]:
        backend_model = getattr(self.model, "model", None)
        actual_device = getattr(backend_model, "device", None)
        actual_compute_type = getattr(backend_model, "compute_type", None)
        profile = self.profile
        temperatures = profile.temperature_schedule
        effective_temperatures = temperatures if profile.mode == "sequential" else temperatures[:1]
        effective_context: bool | str = (
            profile.condition_on_previous_text
            if profile.mode == "sequential"
            else "unsupported_ignored"
        )
        return {
            "status": "reported_by_faster_whisper_adapter",
            "profile_id": profile.profile_id,
            "runtime": self.runtime_capability,
            "device": {
                "requested": profile.device,
                "actual": str(actual_device) if actual_device is not None else "unreported",
                "device_index": profile.device_index if profile.device == "cuda" else None,
            },
            "compute_type": {
                "requested": profile.compute_type,
                "actual": str(actual_compute_type)
                if actual_compute_type is not None
                else "unreported",
            },
            "cpu_threads": profile.cpu_threads if profile.device == "cpu" else None,
            "beam_size": profile.beam_size,
            "mode": profile.mode,
            "batch_size": profile.batch_size if profile.mode == "batched" else 1,
            "language_mode": profile.language_mode,
            "condition_on_previous_text": effective_context,
            "temperature_schedule_requested": temperatures,
            "temperature_schedule": effective_temperatures,
            "fallback_behavior": "upstream_temperature_retries"
            if profile.mode == "sequential" and len(temperatures) > 1
            else "single_temperature_only",
            "fallback_thresholds": {
                "status": "pinned_upstream_defaults"
                if profile.mode == "sequential"
                else "unsupported_ignored_by_batched_path",
                "compression_ratio_threshold": 2.4,
                "log_prob_threshold": -1.0,
                "no_speech_threshold": 0.6,
                "best_of": 5,
                "patience": 1.0,
            },
            "vad_filter": profile.vad_enabled,
            "vad_parameters": profile.vad_parameters if profile.vad_enabled else None,
            "model_window_seconds": profile.model_window_seconds,
            "word_timestamps": False,
            "segment_timestamps": True,
            "language_detection_threshold": 0.5,
            "language_detection_segments": 1,
            "initial_prompt_sha256": _hash_private(profile.initial_prompt),
            "hotwords_sha256": _hash_private(profile.hotwords),
            "inference_completed": True,
        }

    def _observations(
        self,
        info: object,
        *,
        upstream_segments: list[object],
        gpu_memory_before: dict[str, object] | None,
        gpu_memory_after: dict[str, object] | None,
    ) -> dict[str, object]:
        profile = self.profile
        language = getattr(info, "language", None)
        raw_probability = getattr(info, "language_probability", None)
        if profile.language_mode == "th":
            language_observation: dict[str, object] = {
                "source": "forced",
                "language": "th",
                "probability": None,
                "probability_scope": "not_measured_forced_language",
            }
        else:
            language_observation = {
                "source": "per_window_multilingual"
                if profile.language_mode == "multilingual_per_window"
                else "automatic_initial_detection",
                "language": language,
                "probability": _finite_number(raw_probability),
                "probability_scope": "initial_detection_observation",
            }
        duration = _finite_number(getattr(info, "duration", None))
        after_vad = _finite_number(getattr(info, "duration_after_vad", None))
        return {
            "language": language_observation,
            "language_source": language_observation["source"],
            "detected_language": language if profile.language_mode != "th" else None,
            "measured_language_probability": language_observation["probability"],
            "vad": {
                "input_seconds": duration,
                "retained_seconds": after_vad,
                "removed_seconds": (
                    max(0.0, duration - after_vad)
                    if duration is not None and after_vad is not None
                    else None
                ),
            },
            "fallback_attempt_count": None,
            "fallback_attempt_timing": None,
            "fallback_observability": "not_exposed_by_pinned_faster_whisper_generator",
            "segment_diagnostics": _summarize_segment_diagnostics(upstream_segments),
            "gpu_memory": _summarize_gpu_memory(gpu_memory_before, gpu_memory_after),
        }


def _language_arguments(profile: ResolvedProfile) -> tuple[str | None, bool]:
    if profile.language_mode == "th":
        return "th", False
    if profile.language_mode == "multilingual_per_window":
        return None, True
    return None, False


def _hash_private(value: str | None) -> str | None:
    return hashlib.sha256(value.encode("utf-8")).hexdigest() if value is not None else None


def _finite_number(value: object) -> float | None:
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return float(value)


def _summarize_segment_diagnostics(segments: list[object]) -> dict[str, object]:
    # Recognized text is intentionally omitted from this diagnostic summary.
    # Segment.temperature is reported as an output property, never as retry count.
    result: dict[str, object] = {"count": len(segments)}
    for attribute in ("avg_logprob", "no_speech_prob", "compression_ratio", "temperature"):
        values = [
            number
            for segment in segments
            if (number := _finite_number(getattr(segment, attribute, None))) is not None
        ]
        result[attribute] = (
            {
                "minimum": min(values),
                "mean": fmean(values),
                "maximum": max(values),
                "observed_count": len(values),
            }
            if values
            else {"status": "unavailable"}
        )
    result["temperature_note"] = "Returned segment temperature; not a fallback-attempt count."
    return result


def _gpu_memory_snapshot(device_index: int) -> dict[str, object]:
    executable = shutil.which("nvidia-smi")
    if executable is None and os.name == "nt":
        system_root = os.environ.get("SystemRoot")
        if system_root:
            candidate = Path(system_root) / "System32" / "nvidia-smi.exe"
            if candidate.is_file():
                executable = str(candidate)
    if executable is None:
        return {"status": "unavailable", "method": "nvidia-smi not found"}
    try:
        completed = subprocess.run(
            [
                executable,
                f"--id={device_index}",
                "--query-gpu=memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            check=False,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"status": "unavailable", "method": "nvidia-smi query failed"}
    if completed.returncode != 0:
        return {"status": "unavailable", "method": "nvidia-smi query failed"}
    try:
        used, total = (int(value.strip()) for value in completed.stdout.strip().split(",", 1))
    except (ValueError, TypeError):
        return {"status": "unavailable", "method": "nvidia-smi output was not parseable"}
    return {
        "status": "observed",
        "used_mib": used,
        "total_mib": total,
        "method": "nvidia-smi device-wide reading at a transcription-call boundary",
    }


def _summarize_gpu_memory(
    before: dict[str, object] | None, after: dict[str, object] | None
) -> dict[str, object]:
    if before is None and after is None:
        return {"status": "not_applicable_cpu"}
    observed = [
        value
        for value in (before, after)
        if value is not None and value.get("status") == "observed"
    ]
    if not observed:
        return {
            "status": "unavailable",
            "before": before,
            "after": after,
            "attribution": "device-wide reading may include other processes",
        }
    used_memory = [
        cast(int, value["used_mib"]) for value in observed if isinstance(value.get("used_mib"), int)
    ]
    total_memory = observed[0].get("total_mib")
    if not used_memory or not isinstance(total_memory, int):
        return {
            "status": "unavailable",
            "before": before,
            "after": after,
            "method": "nvidia-smi returned invalid memory values",
            "attribution": "device-wide reading may include other processes",
        }
    return {
        "status": "observed",
        "before": before,
        "after": after,
        "sampled_max_used_mib": max(used_memory),
        "total_mib": total_memory,
        "sampling_scope": "call boundaries only; may miss transient peaks",
        "attribution": "device-wide reading may include other processes",
    }
