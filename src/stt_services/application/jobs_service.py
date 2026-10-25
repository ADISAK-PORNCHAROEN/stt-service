import json
import shutil
import tempfile
import threading
import time
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from stt_services.application.job_errors import (
    InvalidModel,
    JobExpired,
    JobNotFound,
    ResultBusy,
    ResultMissing,
    ResultUnavailable,
    TranscriptTooLarge,
)
from stt_services.application.job_policy import terminal_retention
from stt_services.application.job_repository import JobRepository, Lease
from stt_services.config import SUPPORTED_JOB_MODELS, Settings
from stt_services.domain.job_entity import Job, JobStatus, WorkerHealth
from stt_services.media.audio_inspector import inspect_audio
from stt_services.transcription.transcript_exporter import write_transcript_export
from stt_services.transcription.transcript_review import apply_reviewed_text

JOB_ID_PATTERN = "0123456789abcdef"
MAX_TRANSCRIPT_DOCUMENT_BYTES = 64 * 1024 * 1024


class ResultFormat(StrEnum):
    JSON = "json"
    TXT = "txt"
    SRT = "srt"
    ORIGINAL_JSON = "original-json"


@dataclass(slots=True)
class LeasedResult:
    path: Path
    media_type: str
    filename: str
    lease: Lease
    cleanup_directory: Path | None = None
    released: bool = False

    def release(self) -> None:
        if not self.released:
            try:
                if self.cleanup_directory is not None:
                    shutil.rmtree(self.cleanup_directory, ignore_errors=True)
            finally:
                self.lease.release()
                self.released = True


class JobService:
    def __init__(self, repository: JobRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings
        self._transcript_io_lock = threading.Lock()

    def submit(self, job_id: str, suffix: str, staging: Path, model: str | None = None) -> Job:
        if model is not None and model not in SUPPORTED_JOB_MODELS:
            raise InvalidModel("Model must be turbo or large-v3")
        inspect_audio(staging / f"input{suffix}", self.settings)
        return self.repository.enqueue(job_id, suffix, staging, model or self.settings.model)

    def get_job(self, job_id: str) -> Job:
        if len(job_id) != 32 or any(character not in JOB_ID_PATTERN for character in job_id):
            raise JobNotFound
        job = self.repository.get(job_id)
        if job is None:
            raise JobNotFound
        if job.finished_at is not None and time.time() - job.finished_at >= terminal_retention(
            job.status
        ):
            raise JobExpired
        return job

    def health(self) -> WorkerHealth:
        state = self.repository.worker_state()
        age = max(0, time.time() - state.heartbeat_at) if state else None
        ready = bool(
            state
            and state.status == "ready"
            and age is not None
            and age < self.settings.heartbeat_timeout_seconds
        )
        return WorkerHealth(
            ready=ready,
            worker="ready" if ready else "unavailable",
            model_ready=ready,
            heartbeat_at=state.heartbeat_at if state else None,
            heartbeat_age_seconds=age,
            default_model=self.settings.model,
        )

    def acquire_result(self, job_id: str, format: ResultFormat) -> LeasedResult:
        lease = self.repository.try_acquire_lease(job_id)
        if lease is None:
            raise ResultBusy("Result is busy; retry shortly")
        cleanup_directory: Path | None = None
        try:
            job = self.get_job(job_id)
            if job.status != JobStatus.SUCCEEDED:
                raise ResultUnavailable("Result is not available")
            original_json = self.repository.result_path(job_id, "json")
            latest_json = self.repository.latest_transcript_path(job_id)
            filename = f"transcript.{format.value}"
            if format == ResultFormat.ORIGINAL_JSON:
                path = original_json
                filename = "transcript-original.json"
            elif format == ResultFormat.JSON:
                path = latest_json if latest_json.is_file() else original_json
                filename = "transcript.json"
            elif latest_json.is_file():
                with self._transcript_io_lock:
                    document = json.loads(self._read_transcript_bytes(latest_json))
                    cleanup_directory = Path(
                        tempfile.mkdtemp(prefix=".download-", dir=latest_json.parent)
                    )
                    path = cleanup_directory / filename
                    write_transcript_export(document, format.value, path)
            else:
                path = self.repository.result_path(job_id, format.value)
            if not path.is_file():
                raise ResultMissing("Result is no longer available")
            return LeasedResult(
                path=path,
                media_type={
                    ResultFormat.JSON: "application/json",
                    ResultFormat.TXT: "text/plain",
                    ResultFormat.SRT: "application/x-subrip",
                    ResultFormat.ORIGINAL_JSON: "application/json",
                }[format],
                filename=filename,
                lease=lease,
                cleanup_directory=cleanup_directory,
            )
        except BaseException:
            if cleanup_directory is not None:
                shutil.rmtree(cleanup_directory, ignore_errors=True)
            lease.release()
            raise

    def update_transcript(self, job_id: str, edits: list[tuple[int, str]]) -> None:
        if len(job_id) != 32 or any(character not in JOB_ID_PATTERN for character in job_id):
            raise JobNotFound
        lease = self.repository.try_acquire_lease(job_id)
        if lease is None:
            raise ResultBusy("Result is busy; retry shortly")
        try:
            job = self.get_job(job_id)
            if job.status != JobStatus.SUCCEEDED:
                raise ResultUnavailable("Transcript can be edited only after job success")
            original_path = self.repository.result_path(job_id, "json")
            latest_path = self.repository.latest_transcript_path(job_id)
            source = latest_path if latest_path.is_file() else original_path
            if not source.is_file():
                raise ResultMissing("Original result is no longer available")
            with self._transcript_io_lock:
                try:
                    document = json.loads(self._read_transcript_bytes(source))
                except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ResultMissing("Transcript result is no longer available") from exc
                if not isinstance(document, dict):
                    raise ResultMissing("Transcript result is no longer available")
                reviewed = apply_reviewed_text(document, edits)
                content = json.dumps(reviewed, ensure_ascii=False, indent=2).encode("utf-8")
                if len(content) > MAX_TRANSCRIPT_DOCUMENT_BYTES:
                    raise TranscriptTooLarge("Transcript document exceeds the 64 MiB limit")
                self.repository.save_reviewed_transcript(job_id, content)
        finally:
            lease.release()

    def _read_transcript_bytes(self, path: Path) -> bytes:
        with path.open("rb") as transcript_file:
            content = transcript_file.read(MAX_TRANSCRIPT_DOCUMENT_BYTES + 1)
        if len(content) > MAX_TRANSCRIPT_DOCUMENT_BYTES:
            raise TranscriptTooLarge("Transcript document exceeds the 64 MiB limit")
        return content
