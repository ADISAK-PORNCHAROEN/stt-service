import time
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from stt_services.application.job_errors import (
    JobExpired,
    JobNotFound,
    ResultBusy,
    ResultMissing,
    ResultUnavailable,
)
from stt_services.application.job_policy import terminal_retention
from stt_services.application.job_repository import JobRepository, Lease
from stt_services.config import Settings
from stt_services.domain.job_entity import Job, JobStatus, WorkerHealth
from stt_services.media.audio_inspector import inspect_audio

JOB_ID_PATTERN = "0123456789abcdef"


class ResultFormat(StrEnum):
    JSON = "json"
    TXT = "txt"
    SRT = "srt"


@dataclass(slots=True)
class LeasedResult:
    path: Path
    media_type: str
    filename: str
    lease: Lease
    released: bool = False

    def release(self) -> None:
        if not self.released:
            self.lease.release()
            self.released = True


class JobService:
    def __init__(self, repository: JobRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings

    def submit(self, job_id: str, suffix: str, staging: Path) -> Job:
        inspect_audio(staging / f"input{suffix}", self.settings)
        return self.repository.enqueue(job_id, suffix, staging)

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
        )

    def acquire_result(self, job_id: str, format: ResultFormat) -> LeasedResult:
        job = self.get_job(job_id)
        if job.status != JobStatus.SUCCEEDED:
            raise ResultUnavailable("Result is not available")
        lease = self.repository.try_acquire_lease(job_id)
        if lease is None:
            raise ResultBusy("Result is busy; retry shortly")
        try:
            path = self.repository.result_path(job_id, format.value)
            if not path.is_file():
                raise ResultMissing("Result is no longer available")
            return LeasedResult(
                path=path,
                media_type={
                    ResultFormat.JSON: "application/json",
                    ResultFormat.TXT: "text/plain",
                    ResultFormat.SRT: "application/x-subrip",
                }[format],
                filename=f"transcript.{format.value}",
                lease=lease,
            )
        except BaseException:
            lease.release()
            raise
