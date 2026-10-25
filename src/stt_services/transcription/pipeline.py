import gc
import json
import math
import platform
import shutil
import tempfile
import threading
import time
from collections.abc import Callable
from importlib.metadata import version
from pathlib import Path
from typing import Protocol, runtime_checkable

import psutil

from stt_services.config import Settings
from stt_services.domain.transcript_entities import EngineResult, RunMetrics, Segment, Transcript
from stt_services.engines.whisper import WhisperEngine
from stt_services.media.audio_inspector import inspect_audio
from stt_services.transcription.transcript_exporter import write_exports


class Engine(Protocol):
    def transcribe(self, path: Path) -> EngineResult | list[Segment]: ...


EngineFactory = Callable[[Settings], Engine]


@runtime_checkable
class ProgressEngine(Protocol):
    def transcribe_with_progress(
        self, path: Path, on_progress: Callable[[float], None] | None = None
    ) -> EngineResult | list[Segment]: ...


class MemorySampler:
    def __init__(self) -> None:
        self.peak = 0
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._sample, daemon=True)

    def _sample(self) -> None:
        process = psutil.Process()
        while True:
            self.peak = max(self.peak, process.memory_info().rss)
            if self.stop_event.wait(0.05):
                return

    def __enter__(self) -> "MemorySampler":
        self.thread.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.stop_event.set()
        self.thread.join()


class Pipeline:
    def __init__(self, settings: Settings, engine_factory: EngineFactory = WhisperEngine) -> None:
        self.settings = settings
        self.engine_factory = engine_factory
        self.engine: Engine | None = None
        self.profile = settings.resolve_profile()
        self.model_load_peak_ram_bytes = 0

    def load(self) -> float:
        if self.engine is not None:
            return 0
        started = time.perf_counter()
        with MemorySampler() as sampler:
            self.engine = self.engine_factory(self.settings)
        self.model_load_peak_ram_bytes = sampler.peak
        return time.perf_counter() - started

    def unload(self) -> None:
        engine = self.engine
        self.engine = None
        if engine is not None:
            close = getattr(engine, "close", None)
            if callable(close):
                close()
        del engine
        gc.collect()

    def run(
        self,
        source: Path,
        output_dir: Path,
        *,
        source_guard: Callable[[], None] | None = None,
        source_sha256: str | None = None,
        on_progress: Callable[[int], None] | None = None,
        model_load_seconds: float = 0,
    ) -> Transcript:
        started = time.perf_counter() - model_load_seconds
        if output_dir.exists():
            raise ValueError("Output directory already exists; choose a new directory")
        if source_guard:
            source_guard()
        validation_started = time.perf_counter()
        audio = inspect_audio(source, self.settings)
        if source_guard:
            source_guard()
        self.settings.prepare()
        metrics = RunMetrics()
        metrics.validation_seconds = time.perf_counter() - validation_started
        with MemorySampler() as sampler:
            metrics.model_load_seconds = self.load() + model_load_seconds
            assert self.engine is not None
            if source_guard:
                source_guard()
            inference_started = time.perf_counter()
            last_percent = 0

            def report_progress(seconds: float) -> None:
                nonlocal last_percent
                if on_progress is None or not math.isfinite(seconds):
                    return
                percent = int(min(99.0, max(0.0, seconds / audio.decoded_seconds * 100)))
                if percent > last_percent:
                    on_progress(percent)
                    last_percent = percent

            if on_progress is not None and isinstance(self.engine, ProgressEngine):
                engine_result = self.engine.transcribe_with_progress(source, report_progress)
            else:
                engine_result = self.engine.transcribe(source)
            metrics.inference_seconds = time.perf_counter() - inference_started
            # Generation is complete, including silence-only input. Publication is pending.
            report_progress(audio.decoded_seconds)
            if isinstance(engine_result, EngineResult):
                segments = engine_result.segments
                effective_configuration = engine_result.effective_configuration
                observations = engine_result.observations
            else:
                segments = engine_result
                effective_configuration = {"status": "not_reported_by_engine"}
                observations = {"status": "unavailable_from_engine"}
            if source_guard:
                source_guard()
            previous_start = 0.0
            restored = []
            for segment in segments:
                if segment.start < previous_start:
                    raise ValueError("Engine returned timestamps outside the original timeline")
                previous_start = segment.start
                start = audio.source_time(segment.start)
                end = audio.source_time(segment.end, end=True)
                restored.append(Segment(start, max(start, end), segment.text))
            result = Transcript(
                duration_seconds=audio.duration_seconds,
                segments=restored,
                metrics=metrics,
                model=self.settings.model,
                source_name=source.name,
                configuration={
                    "profile_id": self.profile.profile_id,
                    "device": _actual_value(effective_configuration, "device"),
                    "compute_type": _actual_value(effective_configuration, "compute_type"),
                    "cpu_threads": effective_configuration.get("cpu_threads", "unreported"),
                    "vad_filter": effective_configuration.get("vad_filter", "unreported"),
                    "beam_size": effective_configuration.get("beam_size", "unreported"),
                    "language": effective_configuration.get("language_mode", "unreported"),
                    "requested": self.profile.public_configuration,
                    "effective": effective_configuration,
                    "observations": observations,
                },
                versions={
                    "python": platform.python_version(),
                    "model_revision": str(getattr(self.engine, "revision", "unreported")),
                    **{name: version(name) for name in ("faster-whisper", "ctranslate2", "av")},
                },
                source_sha256=source_sha256,
            )
            output_dir.parent.mkdir(parents=True, exist_ok=True)
            staging = Path(tempfile.mkdtemp(prefix=".stt-", dir=output_dir.parent))
            try:
                publication_started = time.perf_counter()
                write_exports(result, staging)
                metrics.publication_seconds = time.perf_counter() - publication_started
                metrics.total_seconds = time.perf_counter() - started
                metrics.rtfx_total = audio.duration_seconds / max(metrics.total_seconds, 1e-9)
                metrics.rtfx_inference = audio.duration_seconds / max(
                    metrics.inference_seconds, 1e-9
                )
                metrics.peak_ram_bytes = max(sampler.peak, self.model_load_peak_ram_bytes)
                (staging / "transcript.json").write_text(
                    json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
                )
                # Every artifact is final before the only publication operation.
                # Full time through publication is measured by the benchmark caller.
                if source_guard:
                    source_guard()
                staging.rename(output_dir)
            finally:
                if staging.exists():
                    shutil.rmtree(staging)
        return result


def _actual_value(configuration: dict[str, object], key: str) -> object:
    value = configuration.get(key, "unreported")
    if isinstance(value, dict):
        return value.get("actual", "unreported")
    return value
