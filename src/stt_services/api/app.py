from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import RequestResponseEndpoint
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import Response

from stt_services.api.controllers.health_controller import HealthController
from stt_services.api.controllers.jobs_controller import (
    MAX_TRANSCRIPT_EDIT_BYTES,
    JobsController,
)
from stt_services.api.dto.transcript_dto import TranscriptUpdateDTO
from stt_services.api.routes.health_routes import create_health_router
from stt_services.api.routes.jobs_routes import create_jobs_router
from stt_services.application.jobs_service import JobService
from stt_services.config import Settings
from stt_services.infrastructure.sqlite_job_repository import SQLiteJobRepository


class STTServiceApp(FastAPI):
    def openapi(self) -> dict[str, Any]:
        openapi_schema = super().openapi()
        components = openapi_schema.setdefault("components", {}).setdefault("schemas", {})
        if "TranscriptUpdateDTO" not in components:
            transcript_schema = TranscriptUpdateDTO.model_json_schema(
                ref_template="#/components/schemas/{model}"
            )
            components.update(transcript_schema.pop("$defs", {}))
            components["TranscriptUpdateDTO"] = transcript_schema
        return openapi_schema


def error_response(status: int, message: str) -> JSONResponse:
    code = {
        400: "invalid_request",
        403: "forbidden_origin",
        404: "not_found",
        409: "result_unavailable",
        413: "file_too_large",
        415: "unsupported_format",
        422: "invalid_input",
        429: "queue_full",
    }.get(status, "internal_error")
    return JSONResponse(
        {"detail": message, "error": {"code": code, "message": message}}, status_code=status
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    repository = SQLiteJobRepository(settings)
    service = JobService(repository, settings)
    app = STTServiceApp(title="Local STT Jobs", version="0.1.0")
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"]
    )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return error_response(exc.status_code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(422, "Invalid request parameters")

    @app.middleware("http")
    async def local_requests(request: Request, call_next: RequestResponseEndpoint) -> Response:
        origin = request.headers.get("origin")
        if origin and origin not in {
            f"http://{request.headers.get('host')}",
            f"https://{request.headers.get('host')}",
        }:
            return error_response(403, "Cross-origin requests are not allowed")
        if request.method in {"POST", "PUT"}:
            length = request.headers.get("content-length")
            if length:
                try:
                    if int(length) < 0:
                        raise ValueError
                    limit = (
                        settings.max_bytes + 65536
                        if request.method == "POST"
                        else MAX_TRANSCRIPT_EDIT_BYTES
                    )
                    if int(length) > limit:
                        return error_response(413, "Request too large")
                except ValueError:
                    return error_response(400, "Invalid Content-Length")
        return await call_next(request)

    app.include_router(create_jobs_router(JobsController(service, repository, settings)))
    app.include_router(create_health_router(HealthController(service)))
    return app
