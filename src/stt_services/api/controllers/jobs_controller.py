from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import ValidationError
from python_multipart.exceptions import MultipartParseError
from starlette.concurrency import run_in_threadpool
from starlette.types import Receive, Scope, Send

from stt_services.api.dto.jobs_dto import JobAcceptedDTO, JobStatusDTO
from stt_services.api.dto.transcript_dto import TranscriptSavedDTO, TranscriptUpdateDTO
from stt_services.application.job_errors import (
    InvalidModel,
    InvalidTranscript,
    JobExpired,
    JobNotFound,
    JobQueueFull,
    ResultMissing,
    ResultUnavailable,
    TranscriptTooLarge,
)
from stt_services.application.job_repository import JobRepository
from stt_services.application.jobs_service import JobService, LeasedResult, ResultFormat
from stt_services.config import Settings
from stt_services.domain.job_entity import JobStatus
from stt_services.media.audio_inspector import InvalidMedia
from stt_services.media.upload_stager import receive_upload

MAX_TRANSCRIPT_EDIT_BYTES = 16 * 1024 * 1024


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
                self.service.submit,
                upload.job_id,
                upload.suffix,
                upload.directory,
                upload.model,
            )
            return JobAcceptedDTO(job_id=job.id, status=JobStatus.QUEUED)
        except InvalidMedia as exc:
            raise HTTPException(422, str(exc)) from exc
        except JobQueueFull as exc:
            raise HTTPException(429, str(exc)) from exc
        except InvalidModel as exc:
            raise HTTPException(422, str(exc)) from exc
        finally:
            upload.close()

    async def update_transcript(self, job_id: str, request: Request) -> TranscriptSavedDTO:
        if request.headers.get("content-type", "").partition(";")[0].strip().lower() != (
            "application/json"
        ):
            raise HTTPException(400, "Expected application/json")
        body = bytearray()
        async for chunk in request.stream():
            if len(body) + len(chunk) > MAX_TRANSCRIPT_EDIT_BYTES:
                raise HTTPException(413, "Transcript update is too large")
            body.extend(chunk)
        try:
            update = TranscriptUpdateDTO.model_validate_json(body)
        except ValidationError as exc:
            raise HTTPException(422, "Invalid transcript update") from exc
        edits = [(segment.id, segment.text) for segment in update.segments]
        try:
            await run_in_threadpool(self.service.update_transcript, job_id, edits)
            return TranscriptSavedDTO()
        except JobExpired as exc:
            raise HTTPException(404, "Job expired") from exc
        except ResultMissing as exc:
            raise HTTPException(404, "Transcript result is no longer available") from exc
        except JobNotFound as exc:
            raise HTTPException(404, "Job not found") from exc
        except ResultUnavailable as exc:
            raise HTTPException(409, str(exc)) from exc
        except InvalidTranscript as exc:
            raise HTTPException(422, str(exc)) from exc
        except TranscriptTooLarge as exc:
            raise HTTPException(413, str(exc)) from exc

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
        except TranscriptTooLarge as exc:
            raise HTTPException(413, str(exc)) from exc
        return DownloadResponse(result)
