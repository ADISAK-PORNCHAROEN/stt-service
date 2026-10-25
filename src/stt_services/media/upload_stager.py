import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from fastapi import HTTPException, Request
from python_multipart import MultipartParser
from python_multipart.multipart import parse_options_header

from stt_services.application.job_repository import JobRepository, Lease
from stt_services.config import SUPPORTED_JOB_MODELS, Settings
from stt_services.media.audio_inspector import SUPPORTED_SUFFIXES


@dataclass(slots=True)
class StagedUpload:
    job_id: str
    suffix: str
    directory: Path
    lease: Lease
    model: str | None = None
    closed: bool = False

    @property
    def input_path(self) -> Path:
        return self.directory / f"input{self.suffix}"

    def close(self) -> None:
        if self.closed:
            return
        try:
            shutil.rmtree(self.directory, ignore_errors=True)
        finally:
            self.lease.release()
            self.closed = True


async def receive_upload(
    request: Request, settings: Settings, repository: JobRepository
) -> StagedUpload:
    kind, options = parse_options_header(request.headers.get("content-type", ""))
    boundary = options.get(b"boundary", b"")
    if kind != b"multipart/form-data" or not boundary or len(boundary) > 200:
        raise HTTPException(400, "Expected multipart/form-data with one file field")
    for _ in range(16):
        job_id = uuid.uuid4().hex
        lease = repository.try_acquire_lease(job_id)
        if lease is not None:
            break
    else:
        raise HTTPException(429, "Upload storage is busy; retry shortly")
    directory = settings.jobs_dir / f".upload-{job_id}"
    try:
        directory.mkdir()
    except BaseException:
        lease.release()
        raise
    stream: BinaryIO | None = None
    suffix = ""
    size = 0
    body_size = 0
    parts = 0
    complete = False
    headers: dict[bytes, bytes] = {}
    field = bytearray()
    value = bytearray()
    header_bytes = 0
    current_part: str | None = None
    model_bytes = bytearray()
    received_file = False
    received_model = False

    def part_begin() -> None:
        nonlocal parts, header_bytes
        parts += 1
        if parts > 2:
            raise HTTPException(400, "Expected one file and at most one model field")
        headers.clear()
        field.clear()
        value.clear()
        header_bytes = 0

    def header_field(data: bytes, start: int, end: int) -> None:
        field.extend(data[start:end])
        check_header_size(end - start)

    def header_value(data: bytes, start: int, end: int) -> None:
        value.extend(data[start:end])
        check_header_size(end - start)

    def check_header_size(amount: int) -> None:
        nonlocal header_bytes
        header_bytes += amount
        if header_bytes > 8192:
            raise HTTPException(400, "Multipart headers are too large")

    def header_end() -> None:
        headers[bytes(field).lower()] = bytes(value)
        field.clear()
        value.clear()

    def headers_finished() -> None:
        nonlocal stream, suffix, current_part, received_file, received_model
        disposition, params = parse_options_header(headers.get(b"content-disposition", b""))
        if disposition != b"form-data":
            raise HTTPException(400, "Expected multipart form-data fields")
        name = params.get(b"name")
        if name == b"file":
            if received_file or b"filename" not in params:
                raise HTTPException(400, "Exactly one file field is required")
            filename = params[b"filename"].decode("utf-8", errors="replace")
            suffix = Path(filename).suffix.lower()
            if suffix not in SUPPORTED_SUFFIXES:
                raise HTTPException(415, "Supported formats: WAV, MP3, M4A, FLAC, MP4")
            stream = (directory / f"input{suffix}").open("xb")
            received_file = True
            current_part = "file"
        elif name == b"model":
            if received_model or b"filename" in params:
                raise HTTPException(400, "Model must be a single text field")
            received_model = True
            current_part = "model"
        else:
            raise HTTPException(400, "Expected a file field and optional model field")

    def part_data(data: bytes, start: int, end: int) -> None:
        nonlocal size
        chunk = data[start:end]
        if current_part == "file":
            size += len(chunk)
            if size > settings.max_bytes:
                raise HTTPException(413, "File exceeds the size limit")
            if stream is None:
                raise HTTPException(400, "Missing file headers")
            stream.write(chunk)
        elif current_part == "model":
            if len(model_bytes) + len(chunk) > 64:
                raise HTTPException(422, "Model must be turbo or large-v3")
            model_bytes.extend(chunk)
        else:
            raise HTTPException(400, "Missing multipart field headers")

    def end() -> None:
        nonlocal complete
        complete = True

    parser = MultipartParser(
        boundary,
        callbacks={
            "on_part_begin": part_begin,
            "on_header_field": header_field,
            "on_header_value": header_value,
            "on_header_end": header_end,
            "on_headers_finished": headers_finished,
            "on_part_data": part_data,
            "on_end": end,
        },
    )
    try:
        async for chunk in request.stream():
            body_size += len(chunk)
            if body_size > settings.max_bytes + 65536:
                raise HTTPException(413, "Request exceeds the upload size limit")
            parser.write(chunk)
        parser.finalize()
        if not complete or stream is None or not received_file:
            raise HTTPException(400, "Incomplete file upload")
        if not size:
            raise HTTPException(422, "Empty audio file")
        model: str | None = None
        if received_model:
            try:
                model = model_bytes.decode("utf-8", errors="strict")
            except UnicodeDecodeError as exc:
                raise HTTPException(422, "Model must be turbo or large-v3") from exc
            if model not in SUPPORTED_JOB_MODELS:
                raise HTTPException(422, "Model must be turbo or large-v3")
        stream.close()
        return StagedUpload(job_id, suffix, directory, lease, model)
    except BaseException:
        if stream:
            stream.close()
        shutil.rmtree(directory, ignore_errors=True)
        lease.release()
        raise
