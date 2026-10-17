"""A complete local transcription behind one reusable interface."""

import json
import platform
import shutil
import tempfile
import threading
import time
from collections.abc import Callable
from importlib.metadata import version
from pathlib import Path
from typing import Protocol

import psutil

from stt_services.audio import inspect_audio
from stt_services.config import Settings
from stt_services.engines.whisper import WhisperEngine
from stt_services.exporters import write_exports
from stt_services.schemas import RunMetrics, Segment, Transcript


class Engine(Protocol):
    def transcribe(self, path: Path) -> list[Segment]: ...


EngineFactory = Callable[[Settings], Engine]


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

    def load(self) -> float:
        if self.engine is not None:
            return 0
        started = time.perf_counter()
        self.engine = self.engine_factory(self.settings)
        return time.perf_counter() - started

    def run(
        self,
        source: Path,
        output_dir: Path,
        *,
        source_guard: Callable[[], None] | None = None,
    ) -> Transcript:
        started = time.perf_counter()
        if output_dir.exists():
            raise ValueError("Output directory already exists; choose a new directory")
        if source_guard:
            source_guard()
        audio = inspect_audio(source, self.settings)
        if source_guard:
            source_guard()
        self.settings.prepare()
        metrics = RunMetrics()
        with MemorySampler() as sampler:
            metrics.model_load_seconds = self.load()
            assert self.engine is not None
            if source_guard:
                source_guard()
            inference_started = time.perf_counter()
            segments = self.engine.transcribe(source)
            metrics.inference_seconds = time.perf_counter() - inference_started
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
                    "device": "cpu",
                    "compute_type": "int8",
                    "cpu_threads": self.settings.cpu_threads,
                    "vad_filter": True,
                    "beam_size": 5,
                    "language": "auto",
                },
                versions={
                    "python": platform.python_version(),
                    "model_revision": str(getattr(self.engine, "revision", "unreported")),
                    **{name: version(name) for name in ("faster-whisper", "ctranslate2", "av")},
                },
            )
            output_dir.parent.mkdir(parents=True, exist_ok=True)
            staging = Path(tempfile.mkdtemp(prefix=".stt-", dir=output_dir.parent))
            try:
                write_exports(result, staging)
                metrics.total_seconds = time.perf_counter() - started
                metrics.rtfx_total = audio.duration_seconds / max(metrics.total_seconds, 1e-9)
                metrics.rtfx_inference = audio.duration_seconds / max(
                    metrics.inference_seconds, 1e-9
                )
                metrics.peak_ram_bytes = sampler.peak
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
