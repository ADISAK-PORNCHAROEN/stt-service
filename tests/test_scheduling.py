"""Observable lifecycle scheduling through the HTTP interface."""

import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event

from fastapi.testclient import TestClient

from stt_services import jobs
from stt_services.api import create_app
from stt_services.jobs import DAY
from stt_services.worker import Worker


def test_startup_cleanup_expires_old_results(settings, engine_factory, wav_bytes, monkeypatch):
    now = [time.time()]
    monkeypatch.setattr(jobs.time, "time", lambda: now[0])
    with TestClient(create_app(settings)) as client:
        response = client.post("/jobs", files={"file": ("audio.wav", wav_bytes)})
        job_id = response.json()["job_id"]
        with Worker(settings, engine_factory) as worker:
            worker.run_once()
        directory = settings.jobs_dir / job_id
        assert directory.exists()
        now[0] += 7 * DAY
        with Worker(settings, engine_factory):
            assert not directory.exists()
            assert client.get(f"/jobs/{job_id}").status_code == 404


def test_cleanup_runs_hourly_without_waiting_for_another_job(
    settings, engine_factory, wav_bytes, monkeypatch
):
    # A clock boundary is controlled externally; observe files and API, not scheduler internals.
    import stt_services.worker as worker_module

    real_monotonic = time.monotonic
    elapsed = [0.0]
    now = [time.time()]
    monkeypatch.setattr(jobs.time, "time", lambda: now[0])
    monkeypatch.setattr(worker_module.time, "monotonic", lambda: real_monotonic() + elapsed[0])
    configured = settings.model_copy(update={"heartbeat_seconds": 0.01})
    with TestClient(create_app(configured)) as client:
        job_id = client.post("/jobs", files={"file": ("audio.wav", wav_bytes)}).json()["job_id"]
        with Worker(configured, engine_factory) as worker:
            worker.run_once()
            source = configured.jobs_dir / job_id / "input.wav"
            now[0] += DAY
            elapsed[0] += 3601
            deadline = real_monotonic() + 5
            while source.exists() and real_monotonic() < deadline:
                time.sleep(0.01)
            assert not source.exists()
            assert client.get(f"/jobs/{job_id}/result").status_code == 200


def test_heartbeat_remains_fresh_while_inference_is_blocked(settings, engine_factory, wav_bytes):
    entered, release = Event(), Event()
    delegate = engine_factory(settings)

    class SlowEngine:
        def transcribe(self, path):
            entered.set()
            assert release.wait(5)
            return delegate.transcribe(path)

    configured = settings.model_copy(
        update={"heartbeat_seconds": 0.01, "heartbeat_timeout_seconds": 0.1}
    )
    with (
        TestClient(create_app(configured)) as client,
        Worker(configured, lambda _: SlowEngine()) as worker,
        ThreadPoolExecutor(max_workers=1) as pool,
    ):
        job_id = client.post("/jobs", files={"file": ("audio.wav", wav_bytes)}).json()["job_id"]
        running = pool.submit(worker.run_once)
        try:
            assert entered.wait(5)
            time.sleep(0.25)
            assert client.get(f"/jobs/{job_id}").json()["status"] == "running"
            assert client.get("/health").status_code == 200
        finally:
            release.set()
        assert running.result(5)


def test_slow_cleanup_does_not_block_heartbeat(settings, engine_factory, wav_bytes, monkeypatch):
    from pathlib import Path

    import stt_services.worker as worker_module

    real_monotonic = time.monotonic
    elapsed = [0.0]
    now = [time.time()]
    monkeypatch.setattr(jobs.time, "time", lambda: now[0])
    monkeypatch.setattr(worker_module.time, "monotonic", lambda: real_monotonic() + elapsed[0])
    entered, release = Event(), Event()
    configured = settings.model_copy(
        update={"heartbeat_seconds": 0.01, "heartbeat_timeout_seconds": 0.1}
    )
    with TestClient(create_app(configured)) as client, Worker(configured, engine_factory) as worker:
        job_id = client.post("/jobs", files={"file": ("audio.wav", wav_bytes)}).json()["job_id"]
        worker.run_once()
        source = configured.jobs_dir / job_id / "input.wav"
        unlink = Path.unlink

        def delayed_unlink(path, *args, **kwargs):
            if path == source:
                entered.set()
                assert release.wait(5)
            return unlink(path, *args, **kwargs)

        with monkeypatch.context() as fault:
            fault.setattr(Path, "unlink", delayed_unlink)
            now[0] += DAY
            elapsed[0] += 3601
            try:
                assert entered.wait(5)
                now[0] += 1
                time.sleep(0.25)
                assert client.get("/health").status_code == 200
            finally:
                release.set()
