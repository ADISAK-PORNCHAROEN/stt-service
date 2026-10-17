"""Loopback HTTP job interface. Inference runs in a separate worker process."""

import shutil
import time
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from filelock import FileLock, Timeout
from python_multipart.exceptions import MultipartParseError
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import RequestResponseEndpoint
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import Response
from starlette.types import Receive, Scope, Send

from stt_services.audio import InvalidMedia, inspect_audio
from stt_services.config import Settings
from stt_services.jobs import JobStore, QueueFull, terminal_retention
from stt_services.uploads import receive_upload


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


class DownloadResponse(FileResponse):
    def __init__(self, *args: Any, lease: FileLock, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.lease = lease

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await super().__call__(scope, receive, send)
        finally:
            self.lease.release()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    store = JobStore(settings)
    app = FastAPI(title="Local STT Jobs", version="0.1.0")
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
        if request.method == "POST":
            length = request.headers.get("content-length")
            if length:
                try:
                    if int(length) < 0:
                        raise ValueError
                    if int(length) > settings.max_bytes + 65536:
                        return error_response(413, "Request too large")
                except ValueError:
                    return error_response(400, "Invalid Content-Length")
        return await call_next(request)

    @app.post("/jobs", status_code=202)
    async def submit(request: Request) -> dict[str, str]:
        try:
            job_id, suffix, directory, lease = await receive_upload(request, settings)
        except MultipartParseError as exc:
            raise HTTPException(400, "Invalid multipart upload") from exc
        try:
            await run_in_threadpool(inspect_audio, directory / f"input{suffix}", settings)
            await run_in_threadpool(store.enqueue, job_id, suffix, directory)
        except InvalidMedia as exc:
            raise HTTPException(422, str(exc)) from exc
        except QueueFull as exc:
            raise HTTPException(429, str(exc)) from exc
        finally:
            try:
                if directory.exists():
                    shutil.rmtree(directory, ignore_errors=True)
            finally:
                lease.release()
        return {"job_id": job_id, "status": "queued"}

    def get_job(job_id: str) -> dict[str, Any]:
        if len(job_id) != 32 or any(c not in "0123456789abcdef" for c in job_id):
            raise HTTPException(404, "Job not found")
        job = store.get(job_id)
        if job is None:
            raise HTTPException(404, "Job not found")
        if job["finished_at"] is not None:
            ttl = terminal_retention(job["status"])
            if time.time() - job["finished_at"] >= ttl:
                raise HTTPException(404, "Job expired")
        return job

    @app.get("/jobs/{job_id}")
    def status(job_id: str) -> dict[str, Any]:
        job = get_job(job_id)
        result = {key: value for key, value in job.items() if key != "suffix"}
        result["updated_at"] = job["finished_at"] or job["started_at"] or job["created_at"]
        result["error_message"] = {
            "interrupted": "Worker stopped during processing; submit a new job to retry",
            "processing_failed": "Transcription failed; check worker logs and submit a new job",
        }.get(job["error"])
        return result

    @app.get("/jobs/{job_id}/result")
    def result(job_id: str, format: Literal["json", "txt", "srt"] = "json") -> FileResponse:
        job = get_job(job_id)
        if job["status"] != "succeeded":
            raise HTTPException(409, "Result is not available")
        lease = store.result_lock(job_id)
        try:
            lease.acquire()
        except Timeout as exc:
            raise HTTPException(409, "Result is busy; retry shortly") from exc
        try:
            path = settings.jobs_dir / job_id / "result" / f"transcript.{format}"
            if not path.is_file():
                raise HTTPException(404, "Result is no longer available")
            return DownloadResponse(
                path,
                lease=lease,
                media_type={
                    "json": "application/json",
                    "txt": "text/plain",
                    "srt": "application/x-subrip",
                }[format],
                filename=f"transcript.{format}",
            )
        except BaseException:
            lease.release()
            raise

    @app.get("/health")
    def health() -> JSONResponse:
        state = store.health()
        return JSONResponse(state, status_code=200 if state["ready"] else 503)

    return app
