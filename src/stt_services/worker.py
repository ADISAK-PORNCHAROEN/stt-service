"""One persistent inference process protected by an OS-backed file lock."""

import logging
import threading
import time
import uuid
from types import TracebackType

from filelock import FileLock, Timeout

from stt_services.config import Settings
from stt_services.engines.whisper import WhisperEngine
from stt_services.jobs import JobStore
from stt_services.pipeline import EngineFactory, Pipeline

logger = logging.getLogger(__name__)


class Worker:
    def __init__(self, settings: Settings, engine_factory: EngineFactory = WhisperEngine) -> None:
        self.settings = settings
        self.store = JobStore(settings)
        self.pipeline = Pipeline(settings, engine_factory)
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
            self.store.recover()
            self.store.heartbeat(self.owner, self.phase)
            self.thread = threading.Thread(target=self._heartbeat, daemon=True)
            self.thread.start()
            load_seconds = self.pipeline.load()
            logger.info("Model loaded in %.3fs", load_seconds)
            self.phase = "ready"
            self.store.heartbeat(self.owner, self.phase)
            self.store.cleanup()
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
                self.store.heartbeat(self.owner, self.phase)
            except Exception:
                logger.exception("Could not refresh worker heartbeat")

    def _cleanup_loop(self) -> None:
        # Filesystem sweeps must never block the independent readiness heartbeat.
        while not self.stop_event.wait(self.settings.heartbeat_seconds):
            if time.monotonic() - self.last_cleanup >= 3600:
                try:
                    self.store.cleanup()
                    self.last_cleanup = time.monotonic()
                except Exception:
                    logger.exception("Retention cleanup failed; retrying on a later sweep")

    def run_once(self) -> bool:
        if not self.active:
            raise RuntimeError("Worker must be started as a context manager")
        job = self.store.claim()
        if job is None:
            return False
        directory = self.settings.jobs_dir / job["id"]
        try:
            # A crash can leave an unpublished staging directory or complete result.
            # Recovery marks interrupted jobs failed; they are never claimed again.
            self.pipeline.run(
                directory / f"input{job['suffix']}",
                directory / "result",
                on_progress=lambda percent: self.store.update_progress(job["id"], percent),
            )
            self.store.finish(job["id"])
            logger.info("Job %s succeeded", job["id"])
        except Exception:
            logger.exception("Job %s failed", job["id"])
            self.store.finish(job["id"], error="processing_failed")
        return True

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
            self.store.heartbeat(self.owner, "stopped")
        finally:
            self.active = False
            self.lock.release()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._close()
