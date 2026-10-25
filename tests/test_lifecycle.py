from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Barrier, Event

import pytest
from fastapi.testclient import TestClient

from stt_services.api.app import create_app
from stt_services.cli import main
from stt_services.domain.transcript_entities import EngineResult, Segment
from stt_services.infrastructure import sqlite_job_repository as jobs
from stt_services.infrastructure.sqlite_job_repository import SQLiteJobRepository
from stt_services.workers.job_worker import Worker

DAY = 86400


def submit(client, wav_bytes):
    response = client.post("/jobs", files={"file": ("recording.wav", wav_bytes, "audio/wav")})
    assert response.status_code == 202, response.text
    job_id = response.json()["job_id"]
    assert client.get(f"/jobs/{job_id}").json()["status"] == "queued"
    return job_id


def state(client, job_id):
    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize(
    ("format_name", "media_type"), [("txt", "text/plain"), ("srt", "application/x-subrip")]
)
def test_api_downloads_txt_srt_without_reloading_or_inference(
    settings, engine_factory, wav_bytes, format_name, media_type
):
    loads = []
    calls = []
    delegate = engine_factory(settings)

    class CountingEngine:
        def transcribe(self, path):
            calls.append(path)
            return delegate.transcribe(path)

    def factory(config):
        loads.append(config)
        return CountingEngine()

    with TestClient(create_app(settings)) as client, Worker(settings, factory) as worker:
        job_id = submit(client, wav_bytes)
        assert worker.run_once()
        assert state(client, job_id)["status"] == "succeeded"
        canonical = client.get(f"/jobs/{job_id}/result")
        assert canonical.status_code == 200
        text = canonical.json()["segments"][0]["text"]
        expected = (
            text + "\n" if format_name == "txt" else f"1\n00:00:00,125 --> 00:00:00,875\n{text}\n\n"
        )
        for _ in range(2):
            response = client.get(f"/jobs/{job_id}/result", params={"format": format_name})
            assert response.status_code == 200
            assert response.headers["content-type"].startswith(media_type)
            assert f"transcript.{format_name}" in response.headers["content-disposition"]
            assert response.content.decode("utf-8") == expected
        assert client.get(f"/jobs/{job_id}/result?format=pdf").status_code == 422
        assert len(loads) == len(calls) == 1


def test_concurrent_admissions_are_bounded_and_rejected_inputs_removed(settings, wav_bytes):
    configured = settings.model_copy(update={"max_queued": 3})
    gate = Barrier(8)
    with TestClient(create_app(configured)) as client:

        def upload(index):
            gate.wait(timeout=10)
            return client.post("/jobs", files={"file": (f"audio-{index}.wav", wav_bytes)})

        with ThreadPoolExecutor(max_workers=8) as pool:
            responses = list(pool.map(upload, range(8)))
        assert sorted(response.status_code for response in responses) == [202] * 3 + [429] * 5
        accepted = {
            response.json()["job_id"] for response in responses if response.status_code == 202
        }
        assert len(accepted) == 3
        assert all(state(client, job_id)["status"] == "queued" for job_id in accepted)
    assert {path.name for path in configured.jobs_dir.iterdir()} == accepted
    assert all(
        (configured.jobs_dir / job_id / "input.wav").read_bytes() == wav_bytes
        for job_id in accepted
    )


def test_second_worker_cannot_load_or_recover_live_work(settings, engine_factory, wav_bytes):
    entered, release = Event(), Event()
    delegate = engine_factory(settings)

    class BlockingEngine:
        def transcribe(self, path):
            entered.set()
            assert release.wait(timeout=10), "Test did not release inference"
            return delegate.transcribe(path)

    def forbidden_factory(config):
        pytest.fail("Second worker loaded a model despite the ownership lock")

    with TestClient(create_app(settings)) as client:
        job_id = submit(client, wav_bytes)
        with Worker(settings, lambda config: BlockingEngine()) as worker:
            with ThreadPoolExecutor(max_workers=1) as pool:
                running = pool.submit(worker.run_once)
                try:
                    assert entered.wait(timeout=10)
                    assert state(client, job_id)["status"] == "running"
                    with pytest.raises(RuntimeError, match="worker"):
                        with Worker(settings, forbidden_factory):
                            pytest.fail("Two workers acquired the same storage")
                    assert state(client, job_id)["status"] == "running"
                    with TestClient(create_app(settings)) as restarted:
                        assert state(restarted, job_id)["status"] == "running"
                        assert restarted.get("/health").status_code == 200
                finally:
                    release.set()
                assert running.result(timeout=10)
        assert state(client, job_id)["status"] == "succeeded"
        with Worker(settings, engine_factory) as replacement:
            assert not replacement.run_once()


def test_running_job_is_additional_to_queue_capacity(settings, engine_factory, wav_bytes):
    configured = settings.model_copy(update={"max_queued": 2})
    entered, release = Event(), Event()
    delegate = engine_factory(configured)

    class BlockingEngine:
        def transcribe(self, path):
            entered.set()
            assert release.wait(timeout=10), "Test did not release inference"
            return delegate.transcribe(path)

    with TestClient(create_app(configured)) as client:
        first = submit(client, wav_bytes)
        with Worker(configured, lambda config: BlockingEngine()) as worker:
            with ThreadPoolExecutor(max_workers=1) as pool:
                running = pool.submit(worker.run_once)
                try:
                    assert entered.wait(timeout=10)
                    assert state(client, first)["status"] == "running"
                    waiting = [submit(client, wav_bytes) for _ in range(2)]
                    rejected = client.post("/jobs", files={"file": ("excess.wav", wav_bytes)})
                    assert rejected.status_code == 429, rejected.text
                    assert {path.name for path in configured.jobs_dir.iterdir()} == {
                        first,
                        *waiting,
                    }
                finally:
                    release.set()
                assert running.result(timeout=10)
            assert worker.run_once()
            following = submit(client, wav_bytes)
            assert worker.run_once()
            assert worker.run_once()
            assert not worker.run_once()
        for job_id in (first, *waiting, following):
            assert state(client, job_id)["status"] == "succeeded"


def test_interrupted_job_fails_on_worker_restart_and_queued_job_survives(
    settings, engine_factory, wav_bytes
):
    class InterruptedEngine:
        def transcribe(self, path):
            raise KeyboardInterrupt

    with TestClient(create_app(settings)) as client:
        interrupted = submit(client, wav_bytes)
        with pytest.raises(KeyboardInterrupt):
            with Worker(settings, lambda config: InterruptedEngine()) as worker:
                worker.run_once()
        assert state(client, interrupted)["status"] == "running"
        queued = submit(client, wav_bytes)
        with Worker(settings, engine_factory) as worker:
            recovered = state(client, interrupted)
            assert recovered["status"] == "failed"
            assert recovered["error"] == "interrupted"
            assert client.get(f"/jobs/{interrupted}/result").status_code == 409
            assert state(client, queued)["status"] == "queued"
            assert worker.run_once()
            assert state(client, queued)["status"] == "succeeded"
            assert client.get(f"/jobs/{queued}/result").status_code == 200
            assert not worker.run_once(), "Interrupted jobs must never retry automatically"


def test_failed_engine_job_does_not_lose_next_queued_job(settings, engine_factory, wav_bytes):
    delegate = engine_factory(settings)
    calls = []

    class FailOnceEngine:
        def transcribe(self, path):
            calls.append(path)
            if len(calls) == 1:
                raise RuntimeError("private engine details must not reach HTTP")
            return delegate.transcribe(path)

    with TestClient(create_app(settings)) as client:
        failed, following = submit(client, wav_bytes), submit(client, wav_bytes)
        with Worker(settings, lambda config: FailOnceEngine()) as worker:
            assert worker.run_once()
            status = state(client, failed)
            assert status["status"] == "failed"
            assert status["error"] == "processing_failed"
            assert "private engine" not in str(status)
            assert client.get(f"/jobs/{failed}/result").status_code == 409
            assert state(client, following)["status"] == "queued"
            assert worker.run_once()
            assert state(client, following)["status"] == "succeeded"
            assert client.get(f"/jobs/{following}/result").status_code == 200
            assert not worker.run_once()
        assert len(calls) == 2


def test_worker_keeps_one_profile_after_a_failed_job(settings, wav_bytes):
    configured = settings.model_copy(update={"cpu_threads": 2, "beam_size": 3})
    loaded_profiles = []
    calls = []

    class ProfileEngine:
        def __init__(self, startup_settings):
            self.profile = startup_settings.resolve_profile()
            loaded_profiles.append(self.profile)

        def transcribe(self, path):
            calls.append(path)
            if len(calls) == 1:
                raise RuntimeError("simulated failed inference")
            return EngineResult(
                segments=[Segment(0.125, 0.875, "สวัสดี Apple")],
                effective_configuration={
                    "device": {"requested": "cpu", "actual": "cpu"},
                    "compute_type": {"requested": "int8", "actual": "int8_float32"},
                    "cpu_threads": self.profile.cpu_threads,
                    "beam_size": self.profile.beam_size,
                    "vad_filter": True,
                    "language_mode": "auto",
                },
                observations={"language_source": "automatic_initial_detection"},
            )

    with TestClient(create_app(configured)) as client:
        failed, succeeded = submit(client, wav_bytes), submit(client, wav_bytes)
        with Worker(configured, ProfileEngine) as worker:
            expected_profile = worker.pipeline.profile
            assert worker.run_once()
            assert worker.run_once()
            assert worker.pipeline.profile.profile_id == expected_profile.profile_id
        assert state(client, failed)["status"] == "failed"
        assert state(client, succeeded)["status"] == "succeeded"
        transcript = client.get(f"/jobs/{succeeded}/result").json()
        assert transcript["configuration"]["profile_id"] == expected_profile.profile_id
        assert transcript["configuration"]["effective"]["beam_size"] == 3
        assert transcript["configuration"]["effective"]["cpu_threads"] == 2
    assert len(loaded_profiles) == 1
    assert len(calls) == 2


def test_health_becomes_unready_at_stale_heartbeat_boundary(settings, engine_factory, monkeypatch):
    now = [2_000_000_000.0]
    monkeypatch.setattr(jobs.time, "time", lambda: now[0])
    configured = settings.model_copy(update={"heartbeat_seconds": 3600})
    with TestClient(create_app(configured)) as client:
        assert client.get("/health").status_code == 503
        with Worker(configured, engine_factory):
            healthy = client.get("/health")
            assert healthy.status_code == 200
            assert healthy.json()["api"] == "ready"
            assert healthy.json()["worker"] == "ready"
            now[0] += configured.heartbeat_timeout_seconds - 0.001
            assert client.get("/health").status_code == 200
            now[0] += 0.001
            stale = client.get("/health")
            assert stale.status_code == 503
            assert stale.json()["ready"] is False
            assert stale.json()["api"] == "ready"
            assert stale.json()["worker"] == "unavailable"


def test_loading_failure_never_reports_worker_ready(settings, wav_bytes):
    def unavailable(config):
        raise RuntimeError("model unavailable")

    with TestClient(create_app(settings)) as client:
        job_id = submit(client, wav_bytes)
        with Worker(settings, unavailable) as worker:
            assert client.get("/health").status_code == 503
            assert client.get("/health").json()["ready"] is False
            assert worker.run_once()
        health = client.get("/health")
        assert health.status_code == 503
        assert health.json()["api"] == "ready"
        assert health.json()["ready"] is False
        assert state(client, job_id)["error"] == "model_load_failed"


def test_success_retention_exact_boundaries_preserve_cli_artifacts(
    settings, engine_factory, wav_bytes, monkeypatch
):
    now = [2_000_000_000.0]
    monkeypatch.setattr(jobs.time, "time", lambda: now[0])
    source = settings.data_dir / "user-audio.wav"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(wav_bytes)
    output = settings.data_dir / "cli-result"
    assert (
        main(
            ["transcribe", str(source), "--output-dir", str(output)], engine_factory=engine_factory
        )
        == 0
    )
    cli_artifacts = {path.name: path.read_bytes() for path in output.iterdir()}
    with TestClient(create_app(settings)) as client:
        job_id = submit(client, wav_bytes)
        with Worker(settings, engine_factory) as worker:
            assert worker.run_once()
        completed = state(client, job_id)["finished_at"]
        input_path = settings.jobs_dir / job_id / "input.wav"
        downloaded = {
            format_name: client.get(f"/jobs/{job_id}/result?format={format_name}").content
            for format_name in ("json", "txt", "srt")
        }
        store = SQLiteJobRepository(settings)
        store.cleanup(now=completed + DAY - 0.001)
        assert input_path.read_bytes() == wav_bytes
        store.cleanup(now=completed + DAY)
        assert not input_path.exists()
        for age in (DAY, 7 * DAY - 0.001):
            store.cleanup(now=completed + age)
            assert state(client, job_id)["status"] == "succeeded"
            for format_name, content in downloaded.items():
                response = client.get(f"/jobs/{job_id}/result?format={format_name}")
                assert response.status_code == 200
                assert response.content == content
        for _ in range(2):
            store.cleanup(now=completed + 7 * DAY)
            assert client.get(f"/jobs/{job_id}").status_code == 404
            for format_name in downloaded:
                assert client.get(f"/jobs/{job_id}/result?format={format_name}").status_code == 404
        assert not (settings.jobs_dir / job_id).exists()
    assert source.read_bytes() == wav_bytes
    assert {path.name: path.read_bytes() for path in output.iterdir()} == cli_artifacts


@pytest.mark.parametrize("interrupted", [False, True])
def test_failed_retention_at_one_day(settings, engine_factory, wav_bytes, interrupted):
    class BrokenEngine:
        def transcribe(self, path):
            if interrupted:
                raise KeyboardInterrupt
            raise RuntimeError("inference failed")

    with TestClient(create_app(settings)) as client:
        job_id = submit(client, wav_bytes)
        if interrupted:
            with pytest.raises(KeyboardInterrupt):
                with Worker(settings, lambda config: BrokenEngine()) as worker:
                    worker.run_once()
            with Worker(settings, engine_factory):
                assert state(client, job_id)["error"] == "interrupted"
        else:
            with Worker(settings, lambda config: BrokenEngine()) as worker:
                assert worker.run_once()
        failed = state(client, job_id)
        assert failed["status"] == "failed"
        input_path = settings.jobs_dir / job_id / "input.wav"
        store = SQLiteJobRepository(settings)
        store.cleanup(now=failed["finished_at"] + DAY - 0.001)
        assert input_path.read_bytes() == wav_bytes
        assert state(client, job_id)["status"] == "failed"
        assert client.get(f"/jobs/{job_id}/result").status_code == 409
        for _ in range(2):
            store.cleanup(now=failed["finished_at"] + DAY)
            assert client.get(f"/jobs/{job_id}").status_code == 404
            assert client.get(f"/jobs/{job_id}/result").status_code == 404
        assert not input_path.parent.exists()


def test_cleanup_excludes_old_running_and_queued_jobs(settings, engine_factory, wav_bytes):
    entered, release = Event(), Event()
    delegate = engine_factory(settings)

    class BlockingEngine:
        def transcribe(self, path):
            entered.set()
            assert release.wait(timeout=10), "Test did not release inference"
            return delegate.transcribe(path)

    with TestClient(create_app(settings)) as client:
        running_id, queued_id = submit(client, wav_bytes), submit(client, wav_bytes)
        with Worker(settings, lambda config: BlockingEngine()) as worker:
            with ThreadPoolExecutor(max_workers=1) as pool:
                running = pool.submit(worker.run_once)
                try:
                    assert entered.wait(timeout=10)
                    assert state(client, running_id)["status"] == "running"
                    future = state(client, queued_id)["created_at"] + 8 * DAY
                    SQLiteJobRepository(settings).cleanup(now=future)
                    assert state(client, running_id)["status"] == "running"
                    assert state(client, queued_id)["status"] == "queued"
                    for job_id in (running_id, queued_id):
                        assert (settings.jobs_dir / job_id / "input.wav").read_bytes() == wav_bytes
                        assert client.get(f"/jobs/{job_id}/result").status_code == 409
                finally:
                    release.set()
                assert running.result(timeout=10)
            assert worker.run_once()
            assert not worker.run_once()
        assert state(client, running_id)["status"] == "succeeded"
        assert state(client, queued_id)["status"] == "succeeded"


@pytest.mark.parametrize("succeeded", [True, False])
def test_get_expiry_at_exact_boundary_before_cleanup(
    settings, engine_factory, wav_bytes, monkeypatch, succeeded
):
    now = [2_000_000_000.0]
    monkeypatch.setattr(jobs.time, "time", lambda: now[0])

    class FailedEngine:
        def transcribe(self, path):
            raise RuntimeError("failed inference")

    factory = engine_factory if succeeded else lambda config: FailedEngine()
    with TestClient(create_app(settings)) as client:
        job_id = submit(client, wav_bytes)
        with Worker(settings, factory) as worker:
            assert worker.run_once()
        terminal = state(client, job_id)
        ttl = 7 * DAY if succeeded else DAY
        now[0] = terminal["finished_at"] + ttl - 0.001
        assert state(client, job_id)["status"] == ("succeeded" if succeeded else "failed")
        for format_name in ("json", "txt", "srt"):
            response = client.get(f"/jobs/{job_id}/result?format={format_name}")
            assert response.status_code == (200 if succeeded else 409)
        for offset in (0, 0.001):
            now[0] = terminal["finished_at"] + ttl + offset
            assert client.get(f"/jobs/{job_id}").status_code == 404
            for format_name in ("json", "txt", "srt"):
                assert client.get(f"/jobs/{job_id}/result?format={format_name}").status_code == 404
        assert (settings.jobs_dir / job_id / "input.wav").is_file()
        if succeeded:
            assert (settings.jobs_dir / job_id / "result" / "transcript.json").is_file()


def test_cleanup_retries_input_deletion_failure_and_continues_other_jobs(
    settings, engine_factory, wav_bytes, monkeypatch
):
    with TestClient(create_app(settings)) as client:
        job_ids = [submit(client, wav_bytes) for _ in range(2)]
        with Worker(settings, engine_factory) as worker:
            assert worker.run_once()
            assert worker.run_once()
        completed = max(state(client, job_id)["finished_at"] for job_id in job_ids)
        protected = settings.jobs_dir / job_ids[0] / "input.wav"
        original_unlink = Path.unlink
        denied = []

        def deny_once(path, *args, **kwargs):
            if path == protected and not denied:
                denied.append(path)
                raise PermissionError("Simulated file in use")
            return original_unlink(path, *args, **kwargs)

        monkeypatch.setattr(Path, "unlink", deny_once)
        store = SQLiteJobRepository(settings)
        store.cleanup(now=completed + DAY)
        assert denied == [protected]
        assert protected.is_file()
        assert not (settings.jobs_dir / job_ids[1] / "input.wav").exists()
        for job_id in job_ids:
            assert state(client, job_id)["status"] == "succeeded"
            assert client.get(f"/jobs/{job_id}/result").status_code == 200
        store.cleanup(now=completed + DAY)
        assert not protected.exists()


def test_inflight_http_download_survives_cleanup_then_expires(settings, engine_factory, wav_bytes):
    sending, release = Event(), Event()
    app = create_app(settings)

    class PausedDownload:
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            async def paused_send(message):
                if (
                    scope["type"] == "http"
                    and scope["path"].endswith("/result")
                    and message["type"] == "http.response.body"
                ):
                    sending.set()
                    assert release.wait(timeout=10), "Test did not release download"
                await send(message)

            await self.app(scope, receive, paused_send)

    app.add_middleware(PausedDownload)
    delegate = engine_factory(settings)

    class LargeTranscriptEngine:
        def transcribe(self, path):
            return [
                replace(segment, text=segment.text * 10000) for segment in delegate.transcribe(path)
            ]

    with TestClient(app) as client:
        job_id = submit(client, wav_bytes)
        with Worker(settings, lambda config: LargeTranscriptEngine()) as worker:
            assert worker.run_once()
        expires = state(client, job_id)["finished_at"] + 7 * DAY
        with ThreadPoolExecutor(max_workers=1) as pool:
            download = pool.submit(client.get, f"/jobs/{job_id}/result")
            try:
                assert sending.wait(timeout=10)
                SQLiteJobRepository(settings).cleanup(now=expires)
                assert (settings.jobs_dir / job_id / "result" / "transcript.json").is_file()
            finally:
                release.set()
            response = download.result(timeout=10)
            assert response.status_code == 200
            assert response.json()["segments"]
        SQLiteJobRepository(settings).cleanup(now=expires)
        assert client.get(f"/jobs/{job_id}").status_code == 404
        assert client.get(f"/jobs/{job_id}/result").status_code == 404
