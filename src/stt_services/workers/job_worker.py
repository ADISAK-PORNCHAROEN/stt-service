import logging
import threading
import time
import uuid
from types import TracebackType

from filelock import FileLock, Timeout

from stt_services.config import Settings
from stt_services.domain.job_entity import JobFailure
from stt_services.engines.whisper import WhisperEngine
from stt_services.infrastructure.sqlite_job_repository import SQLiteJobRepository
from stt_services.transcription.pipeline import EngineFactory, Pipeline

logger = logging.getLogger(__name__)


class Worker:
    def __init__(self, settings: Settings, engine_factory: EngineFactory = WhisperEngine) -> None:
        self.settings = settings
        self.repository = SQLiteJobRepository(settings)
        self.engine_factory = engine_factory
        self.pipeline = Pipeline(settings, engine_factory)
        self.loaded_model: str | None = None
        self.owner = uuid.uuid4().hex
        self.lock = FileLock(settings.data_dir / "worker.lock", timeout=0)
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.cleanup_thread: threading.Thread | None = None
        self.phase = "loading"
        self.active = False
        self.last_cleanup = 0.0

    def __enter__(self) -> "Worker":
        try:
            self.lock.acquire()
        except Timeout as exc:
            raise RuntimeError("Another worker is already running for this data directory") from exc
        try:
            self.repository.fail_interrupted_jobs()
            self.repository.heartbeat(self.owner, self.phase)
            self.thread = threading.Thread(target=self._heartbeat, daemon=True)
            self.thread.start()
            try:
                load_seconds = self.pipeline.load()
                self.loaded_model = self.settings.model
                logger.info("Model %s loaded in %.3fs", self.loaded_model, load_seconds)
                self.phase = "ready"
            except Exception:
                logger.exception("Configured default Whisper model could not be loaded")
                self.pipeline.unload()
                self.loaded_model = None
                self.phase = "unavailable"
            self.repository.heartbeat(self.owner, self.phase)
            self.repository.cleanup()
            self.last_cleanup = time.monotonic()
            self.active = True
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self.cleanup_thread.start()
            return self
        except BaseException:
            self._close()
            raise

    def _heartbeat(self) -> None:
        while not self.stop_event.wait(self.settings.heartbeat_seconds):
            try:
                self.repository.heartbeat(self.owner, self.phase)
            except Exception:
                logger.exception("Could not refresh worker heartbeat")

    def _cleanup_loop(self) -> None:
        while not self.stop_event.wait(self.settings.heartbeat_seconds):
            if time.monotonic() - self.last_cleanup >= 3600:
                try:
                    self.repository.cleanup()
                    self.last_cleanup = time.monotonic()
                except Exception:
                    logger.exception("Retention cleanup failed; retrying on a later sweep")

    def run_once(self) -> bool:
        if not self.active:
            raise RuntimeError("Worker must be started as a context manager")
        job = self.repository.claim()
        if job is None:
            return False
        directory = self.settings.jobs_dir / job.id
        try:
            model_load_seconds = self._ensure_model(job.model)
        except Exception:
            logger.exception(
                "Could not load requested Whisper model %s for job %s", job.model, job.id
            )
            self.repository.finish(job.id, error=JobFailure.MODEL_LOAD_FAILED)
            return True
        try:
            self.pipeline.run(
                directory / f"input{job.suffix}",
                directory / "result",
                on_progress=lambda percent: self.repository.update_progress(job.id, percent),
                model_load_seconds=model_load_seconds,
            )
            self.repository.finish(job.id)
            logger.info("Job %s succeeded", job.id)
        except Exception:
            logger.exception("Job %s failed", job.id)
            self.repository.finish(job.id, error=JobFailure.PROCESSING_FAILED)
        return True

    def _ensure_model(self, model: str) -> float:
        if self.loaded_model == model:
            return 0
        self.phase = "loading"
        self.repository.heartbeat(self.owner, self.phase)
        self.pipeline.unload()
        self.loaded_model = None
        model_settings = self.settings.model_copy(update={"model": model})
        self.pipeline = Pipeline(model_settings, self.engine_factory)
        try:
            load_seconds = self.pipeline.load()
        except Exception:
            self.pipeline.unload()
            self.phase = "unavailable"
            self.repository.heartbeat(self.owner, self.phase)
            raise
        self.loaded_model = model
        self.phase = "ready"
        self.repository.heartbeat(self.owner, self.phase)
        return load_seconds

    def run_forever(self) -> None:
        while not self.stop_event.is_set():
            if not self.run_once():
                self.stop_event.wait(self.settings.poll_seconds)

    def _close(self) -> None:
        self.stop_event.set()
        if self.thread:
            self.thread.join()
        if self.cleanup_thread:
            self.cleanup_thread.join()
        try:
            self.repository.heartbeat(self.owner, "stopped")
        finally:
            try:
                self.pipeline.unload()
            finally:
                self.loaded_model = None
                self.active = False
                self.lock.release()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._close()
