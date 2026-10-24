# Architecture map

## Runtime boundaries

| Boundary | Main source | Responsibility |
| --- | --- | --- |
| CLI and process startup | `src/stt_services/cli.py` | Parse `transcribe`, `benchmark`, `evaluate`, `compare`, `serve`, and `worker` commands; loopback API binding |
| Configuration | `src/stt_services/config.py` | Immutable environment-backed runtime settings and managed data paths |
| Media validation | `src/stt_services/uploads.py`, `audio.py` | Stream and bound HTTP uploads; restrict formats/protocols; inspect and decode media before admission/inference |
| Shared transcription | `src/stt_services/pipeline.py`, `engines/whisper.py` | Reuse the inference pipeline, map times to the source timeline, and stage complete artifacts |
| Transcript contract and export | `src/stt_services/schemas.py`, `exporters.py` | Canonical JSON schema plus deterministic TXT/SRT derivation |
| HTTP service | `src/stt_services/api.py` | FastAPI routes, request validation, job status/results, and health/readiness |
| Durable queue | `src/stt_services/jobs.py` | SQLite schema, admission/claim transactions, retention, leases, and recovery helpers |
| Persistent worker | `src/stt_services/worker.py` | Singleton ownership, startup recovery, one loaded model, sequential jobs, heartbeat and cleanup |
| Evaluation and comparisons | `src/stt_services/evaluation.py`, `comparison.py`, `references.py` | Guarded allowlisted recording evaluation, offline scoring, and immutable comparison artifacts |

## Data flow

CLI and API paths validate media before inference and call the shared pipeline. The pipeline produces canonical transcript data, derives text/subtitles, writes to staging, and publishes a complete bundle atomically on the destination filesystem. The service stores queued job metadata in SQLite and service-owned files under its managed jobs directory; a separate worker claims work and marks success only after publication. CLI destinations remain caller-owned and are not part of managed retention.

## Sources of truth

- Detailed MVP responsibilities, timeline behavior, storage layout, and lifecycle: [MVP architecture](../.scratch/stt-mvp/architecture.md).
- Accepted MVP behavior: [MVP specification](../.scratch/stt-mvp/spec.md).
- Current optimization design and dependency gates: [optimization specification](../.scratch/stt-optimization/spec.md), its ticket files, and [local tracker](agents/issue-tracker.md).
- Persisted entities and ownership: [schema guide](SCHEMA.md).
- HTTP route semantics: [API guide](API.md); FastAPI route declarations and annotations in `api.py` generate the OpenAPI document at runtime. `schemas.py` owns transcript data structures, not HTTP response models.

Source paths above are navigation aids. Confirm current definitions and callers in source before changing a boundary. There is no separate generated source graph or graph freshness signal configured by this setup.
