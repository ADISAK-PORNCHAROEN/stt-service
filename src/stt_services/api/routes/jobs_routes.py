from typing import Literal

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from stt_services.api.controllers.jobs_controller import JobsController
from stt_services.api.dto.jobs_dto import JobAcceptedDTO, JobStatusDTO
from stt_services.api.dto.transcript_dto import TranscriptSavedDTO
from stt_services.application.jobs_service import ResultFormat


def create_jobs_router(controller: JobsController) -> APIRouter:
    router = APIRouter()

    @router.post(
        "/jobs",
        status_code=202,
        response_model=JobAcceptedDTO,
        openapi_extra={
            "requestBody": {
                "required": True,
                "content": {
                    "multipart/form-data": {
                        "schema": {
                            "type": "object",
                            "required": ["file"],
                            "properties": {
                                "file": {"type": "string", "format": "binary"},
                                "model": {
                                    "type": "string",
                                    "enum": ["turbo", "large-v3"],
                                },
                            },
                            "additionalProperties": False,
                        }
                    }
                },
            }
        },
    )
    async def submit(request: Request) -> JobAcceptedDTO:
        return await controller.submit(request)

    @router.get("/jobs/{job_id}", response_model=JobStatusDTO)
    def status(job_id: str) -> JobStatusDTO:
        return controller.status(job_id)

    @router.get("/jobs/{job_id}/result", response_class=FileResponse)
    def result(
        job_id: str,
        format: Literal["json", "txt", "srt", "original-json"] = "json",
    ) -> FileResponse:
        return controller.result(job_id, ResultFormat(format))

    @router.put(
        "/jobs/{job_id}/transcript",
        response_model=TranscriptSavedDTO,
        openapi_extra={
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["segments"],
                            "properties": {
                                "segments": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "required": ["id", "text"],
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "text": {"type": "string"},
                                        },
                                        "additionalProperties": False,
                                    },
                                }
                            },
                            "additionalProperties": False,
                        }
                    }
                },
            }
        },
    )
    async def update_transcript(job_id: str, request: Request) -> TranscriptSavedDTO:
        return await controller.update_transcript(job_id, request)

    return router
