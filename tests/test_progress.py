import sqlite3
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import stt_services.transcription.pipeline as pipeline_module
from stt_services.api.app import create_app
from stt_services.domain.transcript_entities import Segment
from stt_services.engines.whisper import WhisperEngine
from stt_services.infrastructure.sqlite_job_repository import SQLiteJobRepository
from stt_services.workers.job_worker import Worker


@pytest.mark.parametrize("failure", [None, "inference", "publication"])
def test_http_progress_during_inference_publication_and_next_job(
    settings, wav_bytes, monkeypatch, failure
):
    observed = []
    calls = 0
    with TestClient(create_app(settings)) as client:
        job_id = client.post("/jobs", files={"file": ("one.wav", wav_bytes)}).json()["job_id"]

        def snapshot():
            response = client.get(f"/jobs/{job_id}")
            assert response.status_code == 200
            return response.json()

        assert snapshot()["progress_percent"] == 0

        class ProgressEngine:
            def transcribe(self, path):
                raise AssertionError("Worker must use live progress when available")

            def transcribe_with_progress(self, path, on_progress=None):
                nonlocal calls
                calls += 1
                assert snapshot()["progress_percent"] == 0
                if calls == 2:
                    return []  # Silence-only jobs still complete after publication.
                for seconds in (0.25, 0.25, 0.1, float("nan"), 0.75, 1.0):
                    on_progress(seconds)
                    observed.append(snapshot()["progress_percent"])
                    assert snapshot()["status"] == "running"
                    assert client.get(f"/jobs/{job_id}/result").status_code == 409
                if failure == "inference":
                    raise RuntimeError("Generated inference failure")
                return [Segment(0.0, 1.0, "ทดสอบ progress")]

        write_exports = pipeline_module.write_exports

        def check_publication(result, staging):
            assert snapshot()["status"] == "running"
            assert snapshot()["progress_percent"] == 99
            assert client.get(f"/jobs/{job_id}/result").status_code == 409
            if failure == "publication" and calls == 1:
                raise OSError("Generated publication failure")
            write_exports(result, staging)

        monkeypatch.setattr(pipeline_module, "write_exports", check_publication)
        with Worker(settings, lambda configured: ProgressEngine()) as worker:
            assert worker.run_once()
            assert observed == [25, 25, 25, 25, 75, 99]
            finished = snapshot()
            assert finished["status"] == ("failed" if failure else "succeeded")
            assert finished["progress_percent"] == (99 if failure else 100)
            assert client.get(f"/jobs/{job_id}/result").status_code == (409 if failure else 200)
            with TestClient(create_app(settings)) as restarted:
                assert (
                    restarted.get(f"/jobs/{job_id}").json()["progress_percent"]
                    == (finished["progress_percent"])
                )
            job_id = client.post("/jobs", files={"file": ("two.wav", wav_bytes)}).json()["job_id"]
            assert snapshot()["progress_percent"] == 0
            assert worker.run_once()
            assert snapshot()["progress_percent"] == 100
            assert client.get(f"/jobs/{job_id}/result").json()["segments"] == []


def test_interrupted_progress_is_retained_and_terminal_updates_are_ignored(settings, wav_bytes):
    with TestClient(create_app(settings)) as client:
        job_id = client.post("/jobs", files={"file": ("one.wav", wav_bytes)}).json()["job_id"]
        store = SQLiteJobRepository(settings)
        store.update_progress(job_id, 80)  # Queued jobs cannot receive progress.
        assert store.get(job_id).progress_percent == 0
        store.claim()
        store.update_progress(job_id, -10)
        store.update_progress(job_id, 55)
        store.update_progress(job_id, 20)
        store.fail_interrupted_jobs()
        store.update_progress(job_id, 100)
        state = client.get(f"/jobs/{job_id}").json()
        assert state["status"] == "failed"
        assert state["error"] == "interrupted"
        assert state["progress_percent"] == 55


def test_legacy_database_upgrade_preserves_jobs_and_is_repeatable(settings):
    settings.prepare()
    with sqlite3.connect(settings.database) as db:
        db.execute(
            "CREATE TABLE jobs (id TEXT PRIMARY KEY, status TEXT NOT NULL, "
            "suffix TEXT NOT NULL, created_at REAL NOT NULL, "
            "started_at REAL, finished_at REAL, error TEXT)"
        )
        for status in ("queued", "running", "failed", "succeeded"):
            db.execute(
                "INSERT INTO jobs(id,status,suffix,created_at) VALUES(?,?,'.wav',1)",
                (status, status),
            )
    store = SQLiteJobRepository(settings)
    store.update_progress("running", 42)
    store = SQLiteJobRepository(settings)
    assert store.get("queued").progress_percent == 0
    assert store.get("failed").progress_percent == 0
    assert store.get("running").progress_percent == 42
    assert store.get("succeeded").progress_percent == 100
    store.update_progress("succeeded", 60)
    assert store.get("succeeded").progress_percent == 100


@pytest.mark.parametrize("mode", ["sequential", "batched"])
def test_whisper_reports_progress_before_consuming_next_segment(settings, tmp_path, mode):
    engine = object.__new__(WhisperEngine)
    engine.profile = settings.model_copy(update={"mode": mode}).resolve_profile()
    engine.runtime_capability = {}
    observed = []

    def segments():
        yield SimpleNamespace(start=0.0, end=0.5, text="Hello")
        assert observed == [0.5]
        yield SimpleNamespace(start=0.5, end=1.0, text="สวัสดี")
        assert observed == [0.5, 1.0]

    class Model:
        def transcribe(self, path, **options):
            return segments(), SimpleNamespace(duration=1.0)

    engine.model = Model()
    engine.batched_model = Model() if mode == "batched" else None
    result = engine.transcribe_with_progress(tmp_path / "generated.wav", observed.append)
    assert [segment.text for segment in result.segments] == ["Hello", "สวัสดี"]
