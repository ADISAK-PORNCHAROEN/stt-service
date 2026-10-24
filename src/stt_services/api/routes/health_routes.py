from fastapi import APIRouter
from fastapi.responses import JSONResponse

from stt_services.api.controllers.health_controller import HealthController
from stt_services.api.dto.health_dto import HealthDTO


def create_health_router(controller: HealthController) -> APIRouter:
    router = APIRouter()

    @router.get("/health", response_model=HealthDTO)
    def health() -> JSONResponse:
        return controller.health()

    return router
