from fastapi.testclient import TestClient

from stt_services.api import create_app
from stt_services.worker import Worker


def test_upload_queue_worker_and_json_download(settings, engine_factory, wav_bytes):
    with TestClient(create_app(settings)) as client:
        assert client.get("/health").status_code == 503
        response = client.post("/jobs", files={"file": ("ไทย.wav", wav_bytes, "audio/wav")})
        assert response.status_code == 202
        job_id = response.json()["job_id"]
        assert client.get(f"/jobs/{job_id}").json()["status"] == "queued"
        assert client.get(f"/jobs/{job_id}/result").status_code == 409
        with Worker(settings, engine_factory) as worker:
            assert client.get("/health").status_code == 200
            assert worker.run_once()
            assert client.get(f"/jobs/{job_id}").json()["status"] == "succeeded"
            result = client.get(f"/jobs/{job_id}/result")
            assert result.status_code == 200
            assert result.json()["segments"][0]["text"] == "ทดสอบ Apple ราคาใหม่"
        assert client.get("/health").status_code == 503
