from dataclasses import dataclass
from enum import StrEnum


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class JobFailure(StrEnum):
    INTERRUPTED = "interrupted"
    PROCESSING_FAILED = "processing_failed"
    MODEL_LOAD_FAILED = "model_load_failed"


@dataclass(frozen=True, slots=True)
class Job:
    id: str
    status: JobStatus
    suffix: str
    created_at: float
    started_at: float | None
    finished_at: float | None
    error: JobFailure | None
    progress_percent: int
    model: str = "turbo"

    @property
    def updated_at(self) -> float:
        return self.finished_at or self.started_at or self.created_at


@dataclass(frozen=True, slots=True)
class WorkerState:
    status: str
    heartbeat_at: float


@dataclass(frozen=True, slots=True)
class WorkerHealth:
    ready: bool
    worker: str
    model_ready: bool
    heartbeat_at: float | None
    heartbeat_age_seconds: float | None
    default_model: str = "turbo"
