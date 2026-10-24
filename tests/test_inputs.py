import asyncio
import io
from types import SimpleNamespace

import av
import pytest
from fastapi.testclient import TestClient

import stt_services.media.upload_stager as upload_stager
from stt_services.api.app import create_app
from stt_services.cli import main
from stt_services.infrastructure.sqlite_job_repository import SQLiteJobRepository
from stt_services.media.upload_stager import receive_upload
from stt_services.workers.job_worker import Worker


@pytest.fixture
def video_only_mp4():
    buffer = io.BytesIO()
    with av.open(buffer, mode="w", format="mp4") as container:
        stream = container.add_stream("mpeg4", rate=1)
        stream.width = stream.height = 16
        stream.pix_fmt = "yuv420p"
        frame = av.VideoFrame(16, 16, "yuv420p")
        for plane in frame.planes:
            plane.update(bytes(plane.buffer_size))
        for packet in stream.encode(frame):
            container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    return buffer.getvalue()


@pytest.fixture
def local_playlist(tmp_path):
    segment = tmp_path / "private-audio.ts"
    with av.open(str(segment), mode="w", format="mpegts") as container:
        stream = container.add_stream("mp2", rate=48000)
        stream.layout = "mono"
        for _ in range(4):
            frame = av.AudioFrame(format="s16", layout="mono", samples=1152)
            frame.sample_rate = 48000
            for plane in frame.planes:
                plane.update(bytes(plane.buffer_size))
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    playlist = (
        "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:1\n"
        f"#EXT-X-MEDIA-SEQUENCE:0\n#EXTINF:0.096,\nfile:{segment.as_posix()}\n#EXT-X-ENDLIST\n"
    ).encode()
    playlist_path = tmp_path / "valid-playlist.m3u8"
    playlist_path.write_bytes(playlist)
    # Prove the hostile payload can resolve/decode a local reference when sniffed.
    with av.open(str(playlist_path)) as container:
        assert container.streams.audio
        assert next(container.decode(audio=0), None) is not None
    return playlist


@pytest.mark.parametrize("suffix", [".wav", ".mp4"])
def test_api_rejects_playlist_disguised_as_supported_media(settings, local_playlist, suffix):
    with TestClient(create_app(settings)) as client:
        response = client.post("/jobs", files={"file": (f"disguised{suffix}", local_playlist)})
        assert response.status_code == 422, response.text
    assert list(settings.jobs_dir.iterdir()) == []


@pytest.mark.parametrize("suffix", [".wav", ".mp4"])
def test_cli_rejects_playlist_before_loading_engine(settings, local_playlist, tmp_path, suffix):
    source = tmp_path / f"disguised{suffix}"
    source.write_bytes(local_playlist)
    output = settings.data_dir / "cli-result"

    def forbidden_factory(config):
        pytest.fail("Playlist input reached model loading")

    assert (
        main(
            ["transcribe", str(source), "--output-dir", str(output)],
            engine_factory=forbidden_factory,
        )
        == 1
    )
    assert not output.exists()
    assert source.read_bytes() == local_playlist


@pytest.mark.parametrize(
    ("name", "payload", "status"),
    [
        ("broken.wav", b"not a media container", 422),
        ("empty.wav", b"", 422),
        ("audio.exe", None, 415),
    ],
)
def test_invalid_upload_leaves_no_owned_input(settings, wav_bytes, name, payload, status):
    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/jobs", files={"file": (name, wav_bytes if payload is None else payload)}
        )
        assert response.status_code == status, response.text
        assert "job_id" not in response.json()
    assert list(settings.jobs_dir.iterdir()) == []


def test_video_without_audio_is_rejected(settings, video_only_mp4):
    with TestClient(create_app(settings)) as client:
        response = client.post("/jobs", files={"file": ("silent.mp4", video_only_mp4)})
        assert response.status_code == 422, response.text
        assert "audio" in response.text.lower()
    assert list(settings.jobs_dir.iterdir()) == []


@pytest.mark.parametrize("difference", [-1, 0, 1])
def test_upload_byte_limit_is_inclusive(settings, wav_bytes, difference):
    configured = settings.model_copy(update={"max_bytes": len(wav_bytes) + difference})
    with TestClient(create_app(configured)) as client:
        response = client.post("/jobs", files={"file": ("audio.wav", wav_bytes)})
        assert response.status_code == (413 if difference < 0 else 202), response.text
    assert len(list(configured.jobs_dir.iterdir())) == (0 if difference < 0 else 1)


@pytest.mark.parametrize("limit", [0.999, 1.0, 1.001])
def test_upload_duration_limit_is_inclusive(settings, wav_bytes, limit):
    configured = settings.model_copy(update={"max_duration_seconds": limit})
    with TestClient(create_app(configured)) as client:
        response = client.post("/jobs", files={"file": ("audio.wav", wav_bytes)})
        assert response.status_code == (422 if limit < 1 else 202), response.text
    assert len(list(configured.jobs_dir.iterdir())) == (0 if limit < 1 else 1)


def test_streamed_upload_enforces_byte_limit_without_content_length(settings, wav_bytes):
    configured = settings.model_copy(update={"max_bytes": len(wav_bytes) - 1})
    body = (
        b'--test\r\nContent-Disposition: form-data; name="file"; filename="audio.wav"'
        b"\r\nContent-Type: audio/wav\r\n\r\n" + wav_bytes + b"\r\n--test--\r\n"
    )
    with TestClient(create_app(configured)) as client:
        response = client.post(
            "/jobs",
            content=(body[i : i + 1024] for i in range(0, len(body), 1024)),
            headers={"content-type": "multipart/form-data; boundary=test"},
        )
        assert "content-length" not in response.request.headers
        assert response.status_code == 413, response.text
    assert list(configured.jobs_dir.iterdir()) == []


def test_cancelled_upload_removes_staging_and_releases_lease(settings, monkeypatch):
    repository = SQLiteJobRepository(settings)
    job_id = "a" * 32
    monkeypatch.setattr(upload_stager.uuid, "uuid4", lambda: SimpleNamespace(hex=job_id))

    class CancelledRequest:
        headers = {"content-type": "multipart/form-data; boundary=test"}

        async def stream(self):
            yield (
                b"--test\r\n"
                b'Content-Disposition: form-data; name="file"; filename="audio.wav"\r\n'
                b"Content-Type: audio/wav\r\n\r\n"
            )
            yield b"partial upload"
            raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(receive_upload(CancelledRequest(), settings, repository))

    assert list(settings.jobs_dir.iterdir()) == []
    lease = repository.try_acquire_lease(job_id)
    assert lease is not None
    lease.release()
    with repository.connect() as database:
        assert database.execute("SELECT count(*) FROM jobs").fetchone()[0] == 0


@pytest.mark.parametrize("ending", [b"", b"\r\n--unfinished", b"\r\n--test\r\n"])
def test_incomplete_multipart_is_rejected_and_removed(settings, wav_bytes, ending):
    body = (
        b'--test\r\nContent-Disposition: form-data; name="file"; filename="audio.wav"'
        b"\r\nContent-Type: audio/wav\r\n\r\n" + wav_bytes + ending
    )
    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/jobs", content=body, headers={"content-type": "multipart/form-data; boundary=test"}
        )
        assert response.status_code == 400, response.text
    assert list(settings.jobs_dir.iterdir()) == []


@pytest.mark.parametrize("field_name", ["wrong_field", "file"])
def test_upload_requires_exactly_one_file(settings, wav_bytes, field_name):
    files = [(field_name, ("one.wav", wav_bytes))]
    if field_name == "file":
        files.append(("file", ("two.wav", wav_bytes)))
    with TestClient(create_app(settings)) as client:
        response = client.post("/jobs", files=files)
        assert response.status_code == 400, response.text
    assert list(settings.jobs_dir.iterdir()) == []


@pytest.mark.parametrize(
    "filename", ["../../escape.wav", r"..\..\escape.wav", "D:/outside/escape.wav"]
)
def test_upload_filename_cannot_escape_owned_storage(
    settings, wav_bytes, engine_factory, tmp_path, filename
):
    sentinel = tmp_path / "escape.wav"
    sentinel.write_bytes(b"user-owned")
    with TestClient(create_app(settings)) as client:
        response = client.post("/jobs", files={"file": (filename, wav_bytes)})
        assert response.status_code == 202, response.text
        job_id = response.json()["job_id"]
        owned = settings.jobs_dir / job_id
        assert owned.parent == settings.jobs_dir
        assert (owned / "input.wav").read_bytes() == wav_bytes
        assert {path.name for path in settings.jobs_dir.iterdir()} == {job_id}
        with Worker(settings, engine_factory) as worker:
            assert worker.run_once()
        assert client.get(f"/jobs/{job_id}/result").status_code == 200
    assert sentinel.read_bytes() == b"user-owned"
    assert not (settings.data_dir / "escape.wav").exists()


@pytest.mark.parametrize(
    ("headers", "expected"),
    [
        ({"host": "attacker.example"}, 400),
        ({"origin": "https://attacker.example"}, 403),
        ({"origin": "null"}, 403),
        ({"host": "localhost:8000", "origin": "http://localhost:8000"}, 202),
        ({"host": "127.0.0.1:8000", "origin": "http://127.0.0.1:8000"}, 202),
    ],
)
def test_host_and_origin_guards_apply_to_uploads(settings, wav_bytes, headers, expected):
    with TestClient(create_app(settings)) as client:
        response = client.post("/jobs", files={"file": ("audio.wav", wav_bytes)}, headers=headers)
        assert response.status_code == expected, response.text
    assert len(list(settings.jobs_dir.iterdir())) == (1 if expected == 202 else 0)


@pytest.mark.parametrize("case", ["corrupt", "unsupported", "no_audio", "bytes", "duration"])
def test_cli_rejects_invalid_media_before_loading_engine(
    settings, wav_bytes, video_only_mp4, tmp_path, monkeypatch, capsys, case
):
    payload = wav_bytes
    suffix = ".wav"
    if case == "corrupt":
        payload = b"broken media"
    elif case == "unsupported":
        suffix = ".exe"
    elif case == "no_audio":
        payload, suffix = video_only_mp4, ".mp4"
    elif case == "bytes":
        monkeypatch.setenv("STT_MAX_BYTES", str(len(wav_bytes) - 1))
    elif case == "duration":
        monkeypatch.setenv("STT_MAX_DURATION_SECONDS", "0.999")
    source = tmp_path / f"source{suffix}"
    source.write_bytes(payload)
    output = settings.data_dir / "cli-result"

    def forbidden_factory(config):
        pytest.fail("Invalid media reached model loading")

    assert (
        main(
            ["transcribe", str(source), "--output-dir", str(output)],
            engine_factory=forbidden_factory,
        )
        == 1
    )
    assert "stt:" in capsys.readouterr().err
    assert source.read_bytes() == payload
    assert not output.exists()
    assert not list(output.parent.glob(".stt-*"))


def test_cli_missing_input_does_not_publish(settings, tmp_path, capsys):
    source = tmp_path / "missing.wav"
    output = settings.data_dir / "cli-result"

    def forbidden_factory(config):
        pytest.fail("Missing media reached model loading")

    assert (
        main(
            ["transcribe", str(source), "--output-dir", str(output)],
            engine_factory=forbidden_factory,
        )
        == 1
    )
    assert "exist" in capsys.readouterr().err.lower()
    assert not output.exists()
