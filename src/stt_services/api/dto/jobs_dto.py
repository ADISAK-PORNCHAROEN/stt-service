from pydantic import BaseModel, ConfigDict

from stt_services.domain.job_entity import Job, JobFailure, JobStatus


class JobAcceptedDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    status: JobStatus


class JobStatusDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    status: JobStatus
    progress_percent: int
    created_at: float
    started_at: float | None
    finished_at: float | None
    updated_at: float
    error: JobFailure | None
    error_message: str | None
    model: str

    @classmethod
    def from_entity(cls, job: Job) -> "JobStatusDTO":
        return cls(
            id=job.id,
            status=job.status,
            progress_percent=job.progress_percent,
            created_at=job.created_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
            updated_at=job.updated_at,
            error=job.error,
            error_message=(
                {
                    JobFailure.INTERRUPTED: (
                        "Worker stopped during processing; submit a new job to retry"
                    ),
                    JobFailure.PROCESSING_FAILED: (
                        "Transcription failed; check worker logs and submit a new job"
                    ),
                    JobFailure.MODEL_LOAD_FAILED: (
                        f"The requested Whisper model '{job.model}' could not be loaded; "
                        "check worker logs and submit a new job"
                    ),
                }.get(job.error)
                if job.error is not None
                else None
            ),
            model=job.model,
        )
