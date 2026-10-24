from fastapi.responses import JSONResponse

from stt_services.api.dto.health_dto import HealthDTO
from stt_services.application.jobs_service import JobService


class HealthController:
    def __init__(self, service: JobService) -> None:
        self.service = service

    def health(self) -> JSONResponse:
        health = HealthDTO.from_entity(self.service.health())
        return JSONResponse(health.model_dump(), status_code=200 if health.ready else 503)
