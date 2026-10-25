import sqlite3

import pytest
from fastapi.testclient import TestClient

from stt_services.api.app import create_app
from stt_services.domain.transcript_entities import EngineResult, Segment
from stt_services.infrastructure.sqlite_job_repository import SQLiteJobRepository
from stt_services.workers.job_worker import Worker


def _submit(client, wav_bytes, model=None):
    parts = [("file", ("recording.wav", wav_bytes, "audio/wav"))]
    if model is not None:
        parts.insert(0, ("model", (None, model)))
    response = client.post("/jobs", files=parts)
    assert response.status_code == 202, response.text
    return response.json()["job_id"]


def _edit(client, job_id, texts):
    return client.put(
        f"/jobs/{job_id}/transcript",
        json={"segments": [{"id": index, "text": text} for index, text in enumerate(texts, 1)]},
    )


def test_job_model_is_selected_persisted_and_exposed(settings, wav_bytes):
    with TestClient(create_app(settings)) as client:
        assert client.get("/health").json()["default_model"] == settings.model
        default_job_id = _submit(client, wav_bytes)
        selected_job_id = _submit(client, wav_bytes, "large-v3")

        store = SQLiteJobRepository(settings)
        assert store.get(default_job_id).model == settings.model
        assert store.get(selected_job_id).model == "large-v3"
        assert client.get(f"/jobs/{selected_job_id}").json()["model"] == "large-v3"


def test_job_default_model_uses_service_setting_without_restricting_cli_config(settings, wav_bytes):
    configured = settings.model_copy(update={"model": "existing-custom-model"})
    with TestClient(create_app(configured)) as client:
        job_id = _submit(client, wav_bytes)
        assert SQLiteJobRepository(configured).get(job_id).model == "existing-custom-model"
        assert client.get("/health").json()["default_model"] == "existing-custom-model"


@pytest.mark.parametrize("model_first", [False, True])
def test_model_field_is_supported_before_or_after_file(settings, wav_bytes, model_first):
    file_part = ("file", ("recording.wav", wav_bytes, "audio/wav"))
    model_part = ("model", (None, "large-v3"))
    parts = [model_part, file_part] if model_first else [file_part, model_part]
    with TestClient(create_app(settings)) as client:
        response = client.post("/jobs", files=parts)
        assert response.status_code == 202, response.text
        assert SQLiteJobRepository(settings).get(response.json()["job_id"]).model == "large-v3"


def test_openapi_describes_model_selection_and_transcript_edits(settings):
    with TestClient(create_app(settings)) as client:
        schema = client.get("/openapi.json").json()
    submit_schema = schema["paths"]["/jobs"]["post"]["requestBody"]["content"][
        "multipart/form-data"
    ]["schema"]
    assert submit_schema["properties"]["model"]["enum"] == ["turbo", "large-v3"]
    assert "file" in submit_schema["required"]
    update_schema = schema["paths"]["/jobs/{job_id}/transcript"]["put"]["requestBody"]["content"][
        "application/json"
    ]["schema"]
    assert update_schema["properties"]["segments"]["items"]["required"] == ["id", "text"]
    format_parameter = next(
        parameter
        for parameter in schema["paths"]["/jobs/{job_id}/result"]["get"]["parameters"]
        if parameter["name"] == "format"
    )
    assert "original-json" in format_parameter["schema"]["enum"]


@pytest.mark.parametrize("model", ["", "base", "Turbo", "large_v3", "large-v3 "])
def test_job_rejects_unsupported_model_without_queueing(settings, wav_bytes, model):
    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/jobs", files=[("file", ("recording.wav", wav_bytes)), ("model", (None, model))]
        )
        assert response.status_code == 422
        with SQLiteJobRepository(settings).connect() as database:
            assert database.execute("SELECT count(*) FROM jobs").fetchone()[0] == 0
    assert list(settings.jobs_dir.iterdir()) == []


@pytest.mark.parametrize(
    "parts_suffix",
    [
        [("model", (None, "turbo")), ("model", (None, "large-v3"))],
        [("model", ("model.txt", b"turbo", "text/plain"))],
    ],
)
def test_job_rejects_duplicate_or_file_valued_model(settings, wav_bytes, parts_suffix):
    parts = [("file", ("recording.wav", wav_bytes, "audio/wav")), *parts_suffix]
    with TestClient(create_app(settings)) as client:
        response = client.post("/jobs", files=parts)
        assert response.status_code == 400
    assert list(settings.jobs_dir.iterdir()) == []


def test_worker_reuses_switches_and_releases_models_before_loading_next(settings, wav_bytes):
    loads = []
    active = []

    class ModelEngine:
        def __init__(self, configured):
            assert not active, "the previous model must be released before another is loaded"
            self.model = configured.model
            active.append(self)
            loads.append(self.model)

        def transcribe(self, path):
            return EngineResult(
                segments=[Segment(0.1, 0.9, self.model)],
                effective_configuration={},
            )

        def close(self):
            active.remove(self)

    with TestClient(create_app(settings)) as client:
        job_ids = [
            _submit(client, wav_bytes),
            _submit(client, wav_bytes, "turbo"),
            _submit(client, wav_bytes, "large-v3"),
            _submit(client, wav_bytes, "large-v3"),
            _submit(client, wav_bytes, "turbo"),
        ]
        with Worker(settings, ModelEngine) as worker:
            for job_id in job_ids:
                assert worker.run_once()
                result = client.get(f"/jobs/{job_id}/result").json()
                assert result["model"] == SQLiteJobRepository(settings).get(job_id).model
        assert loads == ["turbo", "large-v3", "turbo"]
        assert not active


def test_model_load_failure_fails_requested_job_without_fallback(settings, wav_bytes):
    loaded = []

    class SelectiveEngine:
        def __init__(self, configured):
            if configured.model == "large-v3":
                raise RuntimeError("load failed at a private path")
            self.model = configured.model
            loaded.append(configured.model)

        def transcribe(self, path):
            return [Segment(0.1, 0.9, self.model)]

        def close(self):
            pass

    with TestClient(create_app(settings)) as client:
        failed_job = _submit(client, wav_bytes, "large-v3")
        next_job = _submit(client, wav_bytes, "turbo")
        with Worker(settings, SelectiveEngine) as worker:
            assert worker.run_once()
            failed = client.get(f"/jobs/{failed_job}").json()
            assert failed["status"] == "failed"
            assert failed["error"] == "model_load_failed"
            assert "large-v3" in failed["error_message"]
            assert "private path" not in failed["error_message"]
            assert client.get(f"/jobs/{failed_job}/result").status_code == 409
            assert worker.run_once()
            assert client.get(f"/jobs/{next_job}/result").json()["model"] == "turbo"
    assert loaded == ["turbo", "turbo"]


def test_legacy_database_model_migration_preserves_jobs_and_default(settings):
    settings.prepare()
    with sqlite3.connect(settings.database) as database:
        database.execute(
            "CREATE TABLE jobs (id TEXT PRIMARY KEY, status TEXT NOT NULL, suffix TEXT NOT NULL, "
            "created_at REAL NOT NULL, started_at REAL, finished_at REAL, error TEXT, "
            "progress_percent INTEGER NOT NULL DEFAULT 0)"
        )
        database.execute(
            "INSERT INTO jobs(id,status,suffix,created_at) VALUES('legacy','queued','.wav',1)"
        )

    configured = settings.model_copy(update={"model": "large-v3"})
    first = SQLiteJobRepository(configured)
    assert first.get("legacy").model == "large-v3"
    second = SQLiteJobRepository(configured)
    assert second.get("legacy").model == "large-v3"
    with second.connect() as database:
        assert database.execute("SELECT count(*) FROM jobs").fetchone()[0] == 1


def test_reviewed_transcript_updates_all_exports_and_preserves_original(settings, wav_bytes):
    class TwoSegments:
        def transcribe(self, path):
            return [Segment(0.125, 0.5, "original one"), Segment(0.75, 1.0, "original two")]

    with TestClient(create_app(settings)) as client:
        job_id = _submit(client, wav_bytes)
        with Worker(settings, lambda _: TwoSegments()) as worker:
            assert worker.run_once()

        original_response = client.get(f"/jobs/{job_id}/result?format=original-json")
        assert original_response.status_code == 200
        original = original_response.json()
        original_path = settings.jobs_dir / job_id / "result" / "transcript.json"
        original_bytes = original_path.read_bytes()
        finished_at = client.get(f"/jobs/{job_id}").json()["finished_at"]

        updated = _edit(client, job_id, ["ร้าน", "ศรีษะ"])
        assert updated.status_code == 200, updated.text
        assert updated.json() == {"status": "saved"}
        assert client.get(f"/jobs/{job_id}").json()["finished_at"] == finished_at

        latest = client.get(f"/jobs/{job_id}/result?format=json").json()
        assert latest["text"] == "ร้าน\nศรีษะ"
        assert [segment["text"] for segment in latest["segments"]] == ["ร้าน", "ศรีษะ"]
        for old, new in zip(original["segments"], latest["segments"], strict=True):
            assert {key: value for key, value in new.items() if key != "text"} == {
                key: value for key, value in old.items() if key != "text"
            }
        assert client.get(f"/jobs/{job_id}/result?format=original-json").json() == original
        assert client.get(f"/jobs/{job_id}/result?format=txt").content.decode() == "ร้าน\nศรีษะ\n"
        assert client.get(f"/jobs/{job_id}/result?format=srt").content.decode() == (
            "1\n00:00:00,125 --> 00:00:00,500\nร้าน\n\n2\n00:00:00,750 --> 00:00:01,000\nศรีษะ\n\n"
        )
        assert original_path.read_bytes() == original_bytes
        assert (original_path.parent / "transcript.latest.json").is_file()
        assert not list(original_path.parent.glob("transcript.latest-*.json"))


def test_transcript_save_requires_succeeded_job_and_exact_text_only_segments(settings, wav_bytes):
    class OneSegment:
        def transcribe(self, path):
            return [Segment(0.125, 0.875, "original")]

    with TestClient(create_app(settings)) as client:
        queued = _submit(client, wav_bytes)
        assert _edit(client, queued, ["edited"]).status_code == 409

        succeeded = _submit(client, wav_bytes)
        with Worker(settings, lambda _: OneSegment()) as worker:
            assert worker.run_once()
            assert worker.run_once()
        before = client.get(f"/jobs/{succeeded}/result?format=json").content
        invalid_payloads = [
            {"segments": []},
            {"segments": [{"id": 1, "text": "edited"}, {"id": 2, "text": "extra"}]},
            {"segments": [{"id": 1, "text": "edited"}, {"id": 1, "text": "duplicate"}]},
            {"segments": [{"id": True, "text": "edited"}]},
            {"segments": [{"id": 1, "text": "edited", "start": 5}]},
            {"segments": [{"id": 1, "text": 10}]},
            {"segments": [{"id": 1, "text": "edited"}], "text": "changed top level"},
        ]
        for payload in invalid_payloads:
            response = client.put(f"/jobs/{succeeded}/transcript", json=payload)
            assert response.status_code == 422, response.text
            assert client.get(f"/jobs/{succeeded}/result?format=json").content == before

        assert (
            client.put("/jobs/" + "f" * 32 + "/transcript", json={"segments": []}).status_code
            == 404
        )


def test_second_edit_replaces_latest_without_changing_original(settings, wav_bytes):
    class OneSegment:
        def transcribe(self, path):
            return [Segment(0.125, 0.875, "original")]

    with TestClient(create_app(settings)) as client:
        job_id = _submit(client, wav_bytes)
        with Worker(settings, lambda _: OneSegment()) as worker:
            assert worker.run_once()
        original = client.get(f"/jobs/{job_id}/result?format=original-json").content
        assert _edit(client, job_id, ["first edit"]).status_code == 200
        assert _edit(client, job_id, ["latest edit"]).status_code == 200
        assert (
            client.get(f"/jobs/{job_id}/result?format=json").json()["segments"][0]["text"]
            == "latest edit"
        )
        assert client.get(f"/jobs/{job_id}/result?format=original-json").content == original
        files = list((settings.jobs_dir / job_id / "result").glob("transcript.latest*.json"))
        assert len(files) == 1


def test_failed_atomic_replace_keeps_previous_transcript(settings, wav_bytes, monkeypatch):
    class OneSegment:
        def transcribe(self, path):
            return [Segment(0.125, 0.875, "original")]

    with TestClient(create_app(settings)) as client:
        job_id = _submit(client, wav_bytes)
        with Worker(settings, lambda _: OneSegment()) as worker:
            assert worker.run_once()
        assert _edit(client, job_id, ["saved text"]).status_code == 200
        previous = client.get(f"/jobs/{job_id}/result?format=json").content
        real_replace = __import__("os").replace

        def fail_latest_replace(source, destination):
            if str(destination).endswith("transcript.latest.json"):
                raise OSError("simulated publication failure")
            real_replace(source, destination)

        monkeypatch.setattr(
            "stt_services.infrastructure.sqlite_job_repository.os.replace", fail_latest_replace
        )
        with TestClient(create_app(settings), raise_server_exceptions=False) as failing_client:
            response = _edit(failing_client, job_id, ["must not publish"])
        assert response.status_code == 500
        assert client.get(f"/jobs/{job_id}/result?format=json").content == previous
        assert client.get(f"/jobs/{job_id}/result?format=txt").content.decode() == "saved text\n"


def test_chunked_transcript_body_is_size_limited(settings, wav_bytes, monkeypatch):
    monkeypatch.setattr(
        "stt_services.api.controllers.jobs_controller.MAX_TRANSCRIPT_EDIT_BYTES", 128
    )

    class OneSegment:
        def transcribe(self, path):
            return [Segment(0.125, 0.875, "original")]

    with TestClient(create_app(settings)) as client:
        job_id = _submit(client, wav_bytes)
        with Worker(settings, lambda _: OneSegment()) as worker:
            assert worker.run_once()
        response = client.put(
            f"/jobs/{job_id}/transcript",
            content=(chunk for chunk in (b"{" * 100, b" " * 100)),
            headers={"content-type": "application/json"},
        )
        assert "content-length" not in response.request.headers
        assert response.status_code == 413


def test_oversized_transcript_document_is_rejected_without_changing_original(
    settings, wav_bytes, monkeypatch
):
    class OneSegment:
        def transcribe(self, path):
            return [Segment(0.125, 0.875, "original")]

    with TestClient(create_app(settings)) as client:
        job_id = _submit(client, wav_bytes)
        with Worker(settings, lambda _: OneSegment()) as worker:
            assert worker.run_once()

        original_path = settings.jobs_dir / job_id / "result" / "transcript.json"
        original_bytes = original_path.read_bytes()
        assert _edit(client, job_id, ["first edit"]).status_code == 200
        latest_path = original_path.parent / "transcript.latest.json"
        latest_bytes = latest_path.read_bytes()
        monkeypatch.setattr(
            "stt_services.application.jobs_service.MAX_TRANSCRIPT_DOCUMENT_BYTES",
            len(latest_bytes) - 1,
        )

        assert _edit(client, job_id, ["second edit"]).status_code == 413
        assert client.get(f"/jobs/{job_id}/result?format=txt").status_code == 413
        assert client.get(f"/jobs/{job_id}/result?format=json").content == latest_bytes
        assert client.get(f"/jobs/{job_id}/result?format=original-json").content == original_bytes
        assert latest_path.read_bytes() == latest_bytes
