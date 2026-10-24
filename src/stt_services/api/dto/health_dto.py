from pydantic import BaseModel, ConfigDict

from stt_services.domain.job_entity import WorkerHealth


class HealthDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ready: bool
    api: str
    worker: str
    model_ready: bool
    heartbeat_at: float | None
    heartbeat_age_seconds: float | None

    @classmethod
    def from_entity(cls, health: WorkerHealth) -> "HealthDTO":
        return cls(
            ready=health.ready,
            api="ready",
            worker=health.worker,
            model_ready=health.model_ready,
            heartbeat_at=health.heartbeat_at,
            heartbeat_age_seconds=health.heartbeat_age_seconds,
        )
