"""Cold-model and warm-model runs in one process, with explicit timing scope."""

import hashlib
import json
import platform
import time
from pathlib import Path

import psutil

from stt_services.pipeline import Pipeline


def benchmark(source: Path, output_dir: Path, pipeline: Pipeline) -> None:
    if output_dir.exists():
        raise ValueError("Benchmark output directory already exists")
    output_dir.mkdir(parents=True)
    runs = []
    for name in ("cold", "warm"):
        print(f"Starting {name} run...", flush=True)
        started = time.perf_counter()
        result = pipeline.run(source, output_dir / name)
        wall_seconds = time.perf_counter() - started
        runs.append(
            {
                "run": name,
                "wall_seconds": wall_seconds,
                "rtfx_total": result.duration_seconds / max(wall_seconds, 1e-9),
                "metrics": result.to_dict()["metrics"],
            }
        )
        print(f"Finished {name} run: {runs[-1]['wall_seconds']:.2f}s", flush=True)
    with source.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    report = {
        "source_sha256": digest,
        "source_bytes": source.stat().st_size,
        "duration_seconds": result.duration_seconds,
        "hardware": {
            "os": platform.platform(),
            "processor": platform.processor(),
            "logical_cpus": psutil.cpu_count(),
            "ram_bytes": psutil.virtual_memory().total,
        },
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
