# Architecture map

## Runtime boundaries

| Boundary | Main source | Responsibility |
| --- | --- | --- |
| CLI and process startup | `src/stt_services/cli.py` | Parse `transcribe`, `benchmark`, `evaluate`, `compare`, `serve`, and `worker` commands; loopback API binding |
| Configuration | `src/stt_services/config.py` | Immutable environment-backed runtime settings and managed data paths |
| Media validation | `src/stt_services/media/upload_stager.py`, `media/audio_inspector.py` | Stage bounded HTTP uploads; restrict formats and protocols; inspect media before admission and inference |
| Shared transcription | `src/stt_services/transcription/pipeline.py`, `engines/whisper.py` | Reuse inference for CLI and worker, preserve source timeline, and publish complete artifacts |
| Transcript contract and export | `src/stt_services/domain/transcript_entities.py`, `transcription/transcript_exporter.py` | Engine-independent transcript types, canonical JSON, and deterministic TXT/SRT derivation |
| HTTP application | `src/stt_services/api/app.py` | Construct FastAPI services, configure middleware and error mapping, and register routers |
| HTTP routes, controllers, and DTOs | `src/stt_services/api/routes/`, `api/controllers/`, `api/dto/` | Register endpoint/OpenAPI metadata, adapt HTTP input/output, and define public payloads |
| Job application layer | `src/stt_services/application/jobs_service.py`, `job_repository.py`, `job_policy.py`, `domain/job_entity.py` | Apply job, per-job model, result, and transcript-review policy through typed entities and a persistence contract |
| SQLite/filesystem adapter | `src/stt_services/infrastructure/sqlite_job_repository.py` | Implement durable admission, claim, lifecycle, retention, lease, and recovery operations |
| Persistent worker | `src/stt_services/workers/job_worker.py` | Own singleton startup/recovery, one loaded model, sequential jobs, heartbeat, and cleanup |
| Evaluation and comparisons | `src/stt_services/evaluation/` | Guard allowlisted recording evaluation, offline scoring, and immutable comparison artifacts |

## Dependency direction

FastAPI routes call controllers, which translate HTTP data and errors while using application services and DTOs. Job services depend on domain entities and the `JobRepository` contract; the SQLite/filesystem adapter implements that contract. The API application and worker select the concrete adapter at process boundaries. The CLI and worker share the transcription pipeline, which depends on media inspection, the engine interface, transcript entities, and artifact exporters. Persistence rows remain internal to the adapter, and HTTP DTOs remain separate from job and transcript entities.

## Data flow

CLI and API paths validate media before inference and call the shared pipeline. The pipeline produces canonical transcript data, derives text/subtitles, writes to staging, and publishes a complete original bundle atomically on the destination filesystem. Each service Job stores its selected Whisper model in SQLite; one worker releases its current engine before loading a different model and reuses a matching one across jobs. After success, a transcript edit validates the full segment-ID set under the result lease and atomically replaces one latest JSON file. TXT/SRT downloads are derived from that JSON, while `original-json` reads the immutable original. CLI destinations remain caller-owned and are not part of managed retention.

## Sources of truth

- Detailed MVP responsibilities, timeline behavior, storage layout, and lifecycle: [MVP architecture](../.scratch/stt-mvp/architecture.md).
- Accepted MVP behavior: [MVP specification](../.scratch/stt-mvp/spec.md).
- Current optimization design and dependency gates: [optimization specification](../.scratch/stt-optimization/spec.md), its ticket files, and [local tracker](agents/issue-tracker.md).
- Persisted entities and ownership: [schema guide](SCHEMA.md).
- HTTP route semantics: [API guide](API.md); route declarations and annotations under `api/routes/` generate the OpenAPI document at runtime. `domain/transcript_entities.py` owns transcript data structures, not HTTP response models.

Source paths above are navigation aids. Confirm current definitions and callers in source before changing a boundary. There is no separate generated source graph or graph freshness signal configured by this setup.
