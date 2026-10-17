"""Cold-model and warm-model runs in one process, with explicit timing scope."""

import csv
import hashlib
import json
import os
import platform
import shutil
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

import psutil

from stt_services.pipeline import Pipeline


def hardware_report() -> dict[str, object]:
    return {
        "os": platform.platform(),
        "processor": platform.processor(),
        "physical_cpus": psutil.cpu_count(logical=False),
        "logical_cpus": psutil.cpu_count(),
        "ram_bytes": psutil.virtual_memory().total,
        "gpus": _gpu_inventory(),
    }


def _gpu_inventory() -> dict[str, object]:
    executable = shutil.which("nvidia-smi")
    if executable is None and os.name == "nt":
        system_root = os.environ.get("SystemRoot")
        if system_root:
            candidate = Path(system_root) / "System32" / "nvidia-smi.exe"
            if candidate.is_file():
                executable = str(candidate)
    if executable is None:
        return {"status": "not_detected", "method": "nvidia-smi not found"}
    try:
        completed = subprocess.run(
            [
                executable,
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            check=False,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"status": "unavailable", "method": "nvidia-smi query failed"}
    if completed.returncode != 0:
        return {"status": "unavailable", "method": "nvidia-smi query failed"}
    devices = []
    for row in csv.reader(completed.stdout.splitlines(), skipinitialspace=True):
        if len(row) == 3:
            try:
                memory_mib = int(row[1].strip())
            except ValueError:
                memory_mib = None
            devices.append(
                {
                    "name": row[0].strip(),
                    "memory_total_mib": memory_mib,
                    "driver_version": row[2].strip(),
                }
            )
    return {
        "status": "observed" if devices else "no_visible_devices",
        "devices": devices,
        "method": "nvidia-smi device inventory; does not establish model compatibility",
    }


def benchmark(
    source: Path,
    output_dir: Path,
    pipeline: Pipeline,
    *,
    source_guard: Callable[[], None] | None = None,
    source_sha256: str | None = None,
    recording_id: str | None = None,
    role: str | None = None,
) -> None:
    if output_dir.exists():
        raise ValueError("Benchmark output directory already exists")
    output_dir.mkdir(parents=True)
    runs = []
    previous_text: str | None = None
    for name in ("cold", "warm"):
        print(f"Starting {name} run...", flush=True)
        started = time.perf_counter()
        result = pipeline.run(
            source, output_dir / name, source_guard=source_guard, source_sha256=source_sha256
        )
        wall_seconds = time.perf_counter() - started
        canonical_text = str(result.to_dict()["text"])
        runs.append(
            {
                "run": name,
                "recording_id": recording_id,
                "source_sha256": source_sha256,
                "profile_id": result.configuration.get("profile_id"),
                "wall_seconds": wall_seconds,
                "rtfx_total": result.duration_seconds / max(wall_seconds, 1e-9),
                "metrics": result.to_dict()["metrics"],
                "result_json": f"{name}/transcript.json",
                "result_json_sha256": hashlib.sha256(
                    (output_dir / name / "transcript.json").read_bytes()
                ).hexdigest(),
                "canonical_text_sha256": hashlib.sha256(canonical_text.encode("utf-8")).hexdigest(),
                "text_changed_from_previous_run": (
                    canonical_text != previous_text if previous_text is not None else None
                ),
            }
        )
        previous_text = canonical_text
        print(f"Finished {name} run: {runs[-1]['wall_seconds']:.2f}s", flush=True)
    with source.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    report = {
        "source_sha256": digest,
        "recording_id": recording_id,
        "role": role,
        "source_bytes": source.stat().st_size,
        "duration_seconds": result.duration_seconds,
        "hardware": hardware_report(),
        "model": result.model,
        "configuration": result.configuration,
        "versions": result.versions,
        "runs": runs,
        "timing_scope": "wall_seconds/rtfx_total cover validation through complete directory "
        "publication. Transcript metrics.total_seconds/rtfx_total stop before the final "
        "JSON metrics serialization and atomic rename, to keep the published bundle immutable.",
        "cold_definition": "First model load in this process; includes download if not cached. "
        "OS page cache is not flushed. Warm reuses the same model instance.",
        "quality": "Pending human comparison against audio; no reviewed reference, no CER/WER.",
    }
    (output_dir / "benchmark.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
