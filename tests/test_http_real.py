"""Optional actual-process HTTP/worker acceptance with cached model weights."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
import psutil
import pytest

from stt_services.evaluation import authorize_media


def stop_tree(process):
    try:
        parent = psutil.Process(process.pid)
        children = parent.children(recursive=True)
        for child in reversed(children):
            child.terminate()
        parent.terminate()
        psutil.wait_procs([*children, parent], timeout=10)
        for child in [*children, parent]:
            if child.is_running():
                child.kill()
    except psutil.NoSuchProcess:
        pass
    process.wait(timeout=15)


@pytest.mark.integration
def test_real_separate_api_and_worker_processes(tmp_path):
    media = os.environ.get("STT_TEST_MEDIA")
    if not media:
        pytest.skip("Set STT_TEST_MEDIA to a supported recording")
    job_timeout = float(os.environ.get("STT_TEST_JOB_TIMEOUT_SECONDS", "1800"))
    assert 0 < job_timeout <= 14400, "STT_TEST_JOB_TIMEOUT_SECONDS must be in (0, 14400]"
    authorized = authorize_media(Path(media))
    port = int(os.environ.get("STT_TEST_PORT", "18765"))
    base_url = f"http://127.0.0.1:{port}"
    try:
        httpx.get(f"{base_url}/health", timeout=0.5)
    except httpx.TransportError:
        pass
    else:
        pytest.fail(f"Port {port} already in use; set STT_TEST_PORT")
    env = {**os.environ, "STT_DATA_DIR": str(tmp_path / "service-data"), "PYTHONUTF8": "1"}
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    processes = []
    progress_samples = []
    with (tmp_path / "service.log").open("w", encoding="utf-8") as log:
        try:
            for command in (["serve", "--port", str(port)], ["worker"]):
                processes.append(
                    subprocess.Popen(
                        [sys.executable, "-m", "stt_services.cli", *command],
                        env=env,
                        stdout=log,
                        stderr=log,
                        creationflags=flags,
                    )
                )
            with httpx.Client(base_url=base_url, timeout=120) as client:
                deadline = time.monotonic() + 180
                while True:
                    assert all(p.poll() is None for p in processes), log.name
                    try:
                        if client.get("/health").status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    assert time.monotonic() < deadline, "Worker did not become ready"
                    time.sleep(0.2)
                with authorized.source.open("rb") as source:
                    authorized.assert_unchanged()
                    assert os.path.samestat(os.fstat(source.fileno()), authorized.source.stat())
                    response = client.post(
                        "/jobs", files={"file": (authorized.source.name, source)}
                    )
                    authorized.assert_unchanged()
                assert response.status_code == 202, response.text
                job_id = response.json()["job_id"]
                job_started = time.monotonic()
                deadline = job_started + job_timeout
                while True:
                    assert all(p.poll() is None for p in processes), log.name
                    response = client.get(f"/jobs/{job_id}")
                    assert response.status_code == 200, response.text
                    status = response.json()
                    percent = status["progress_percent"]
                    assert isinstance(percent, int) and not isinstance(percent, bool)
                    assert 0 <= percent <= 100
                    if progress_samples:
                        assert percent >= progress_samples[-1]["progress_percent"]
                    sample = {
                        "elapsed_seconds": time.monotonic() - job_started,
                        "status": status["status"],
                        "progress_percent": percent,
                    }
                    progress_samples.append(sample)
                    with (tmp_path / "progress.jsonl").open("a", encoding="utf-8") as evidence:
                        evidence.write(json.dumps(sample) + "\n")
                    if status["status"] != "succeeded":
                        assert percent < 100
                    assert status["status"] != "failed", status
                    if status["status"] == "succeeded":
                        assert percent == 100
                        break
                    assert time.monotonic() < deadline, "Job did not finish"
                    time.sleep(0.5)
                assert any(
                    row["status"] == "running" and 0 < row["progress_percent"] < 99
                    for row in progress_samples
                ), "No intermediate real-inference progress was observed"
                for format_name in ("json", "txt", "srt"):
                    result = client.get(f"/jobs/{job_id}/result?format={format_name}")
                    assert result.status_code == 200
                    assert result.content
                    (tmp_path / f"transcript.{format_name}").write_bytes(result.content)
                transcript = json.loads((tmp_path / "transcript.json").read_text(encoding="utf-8"))
                assert transcript["segments"]
                assert transcript["versions"]["model_revision"] != "unreported"
                assert transcript["metrics"]["model_load_seconds"] == 0
                assert all(
                    0 <= segment["start"] <= segment["end"] <= transcript["duration_seconds"]
                    for segment in transcript["segments"]
                )
                assert client.get("/health").status_code == 200
                authorized.assert_unchanged()
        finally:
            for process in reversed(processes):
                stop_tree(process)
