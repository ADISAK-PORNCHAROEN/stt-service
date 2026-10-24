from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from python_multipart.exceptions import MultipartParseError
from starlette.concurrency import run_in_threadpool
from starlette.types import Receive, Scope, Send

from stt_services.api.dto.jobs_dto import JobAcceptedDTO, JobStatusDTO
from stt_services.application.job_errors import (
    JobExpired,
    JobNotFound,
    JobQueueFull,
    ResultMissing,
    ResultUnavailable,
)
from stt_services.application.job_repository import JobRepository
from stt_services.application.jobs_service import JobService, LeasedResult, ResultFormat
from stt_services.config import Settings
from stt_services.domain.job_entity import JobStatus
from stt_services.media.audio_inspector import InvalidMedia
from stt_services.media.upload_stager import receive_upload


class DownloadResponse(FileResponse):
    def __init__(self, result: LeasedResult) -> None:
        self.result = result
        try:
            super().__init__(
                result.path,
                media_type=result.media_type,
                filename=result.filename,
            )
        except BaseException:
            result.release()
            raise

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await super().__call__(scope, receive, send)
        finally:
            self.result.release()


class JobsController:
    def __init__(
        self,
        service: JobService,
        repository: JobRepository,
        settings: Settings,
    ) -> None:
        self.service = service
        self.repository = repository
        self.settings = settings

    async def submit(self, request: Request) -> JobAcceptedDTO:
        try:
            upload = await receive_upload(request, self.settings, self.repository)
        except MultipartParseError as exc:
            raise HTTPException(400, "Invalid multipart upload") from exc
        try:
            job = await run_in_threadpool(
                self.service.submit, upload.job_id, upload.suffix, upload.directory
            )
            return JobAcceptedDTO(job_id=job.id, status=JobStatus.QUEUED)
        except InvalidMedia as exc:
            raise HTTPException(422, str(exc)) from exc
        except JobQueueFull as exc:
            raise HTTPException(429, str(exc)) from exc
        finally:
            upload.close()

    def status(self, job_id: str) -> JobStatusDTO:
        try:
            return JobStatusDTO.from_entity(self.service.get_job(job_id))
        except JobExpired as exc:
            raise HTTPException(404, "Job expired") from exc
        except JobNotFound as exc:
            raise HTTPException(404, "Job not found") from exc

    def result(self, job_id: str, format: ResultFormat) -> DownloadResponse:
        try:
            result = self.service.acquire_result(job_id, format)
        except JobExpired as exc:
            raise HTTPException(404, "Job expired") from exc
        except ResultMissing as exc:
            raise HTTPException(404, "Result is no longer available") from exc
        except JobNotFound as exc:
            raise HTTPException(404, "Job not found") from exc
        except ResultUnavailable as exc:
            raise HTTPException(409, str(exc)) from exc
        return DownloadResponse(result)
