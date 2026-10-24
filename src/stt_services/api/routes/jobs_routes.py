from typing import Literal

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from stt_services.api.controllers.jobs_controller import JobsController
from stt_services.api.dto.jobs_dto import JobAcceptedDTO, JobStatusDTO
from stt_services.application.jobs_service import ResultFormat


def create_jobs_router(controller: JobsController) -> APIRouter:
    router = APIRouter()

    @router.post("/jobs", status_code=202, response_model=JobAcceptedDTO)
    async def submit(request: Request) -> JobAcceptedDTO:
        return await controller.submit(request)

    @router.get("/jobs/{job_id}", response_model=JobStatusDTO)
    def status(job_id: str) -> JobStatusDTO:
        return controller.status(job_id)

    @router.get("/jobs/{job_id}/result", response_class=FileResponse)
    def result(job_id: str, format: Literal["json", "txt", "srt"] = "json") -> FileResponse:
        return controller.result(job_id, ResultFormat(format))

    return router
