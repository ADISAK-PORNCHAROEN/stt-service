# HTTP API contract map

Thai overview: [API endpoints and purpose](API-ENDPOINTS.md).

The local service is a loopback FastAPI application. `src/stt_services/api/app.py` creates the application and configures middleware and error mapping. Route declarations under `src/stt_services/api/routes/` define the HTTP endpoints and generate `/openapi.json`; controllers adapt HTTP requests and responses through application services, while DTOs define public payloads. The transcript data shape is owned separately by `src/stt_services/domain/transcript_entities.py`; it is not the source of HTTP response models. The MVP specification owns detailed accepted semantics and error mapping.

| Route | Contract summary |
| --- | --- |
| `POST /jobs` | Accept one multipart `file` and optional `model` (`turbo` or `large-v3`); omitted model snapshots `STT_MODEL`. Return `202` with `job_id` and `status=queued`. |
| `GET /jobs/{job_id}` | Return lifecycle status, selected model, progress, timestamps, and safe error fields for a valid, retained job identifier. |
| `GET /jobs/{job_id}/result?format=json|txt|srt|original-json` | Return an artifact only after success. JSON/TXT/SRT use the latest saved transcript; `original-json` returns the immutable ASR result. |
| `PUT /jobs/{job_id}/transcript` | Replace text for the complete set of segment IDs on a succeeded job; timing and segment structure remain unchanged. |
| `GET /health` | Report API and worker/model readiness and the configured default model; a missing, loading, stopped, or stale worker produces unavailable readiness. |

## Model selection and transcript review

`POST /jobs` accepts `model=turbo` or `model=large-v3` as an optional multipart text field. If omitted, the service snapshots its configured `STT_MODEL` value when the job is created. The chosen model is persisted with the job and returned in its status. `/health` exposes the configured default as `default_model`. The worker loads one model at a time, reuses the currently loaded model, and reports a clear failed job if the requested model cannot load.

`PUT /jobs/{job_id}/transcript` accepts JSON shaped as `{"segments":[{"id":1,"text":"corrected text"}]}` and requires one entry for every existing segment ID. IDs must be unique and match the complete original set; unknown fields, including timing edits, are rejected. The request body is limited to 16 MiB and the canonical JSON document to 64 MiB. The save changes segment text only and updates derived top-level text. A single atomic file replacement stores the latest reviewed JSON beside the immutable original result. TXT and SRT are generated from that JSON when requested. No edit history is stored, and edits do not extend the existing result retention period.

`format=original-json` downloads the original ASR document as `transcript-original.json`; the usual JSON response remains `transcript.json` and uses the latest saved text. A job must be `succeeded` before it can be edited or its results downloaded. Busy lease conflicts remain `409`; invalid edit data is `422`.

Important boundaries include bounded streaming uploads, pre-admission media inspection, loopback binding, Host/Origin checks, response-time result leases, and safe public errors. This is not an authenticated multi-user API and does not support cross-origin browser clients.

`JobsController` maps upload parsing, application errors, and leased result streaming to HTTP responses. `JobService` owns job lookup, expiration, readiness, and result availability policy; `JobRepository` defines lifecycle persistence operations. `SQLiteJobRepository` implements that contract with coordinated SQLite and filesystem behavior. Health routes use a separate controller and DTO.

When changing a route, update the accepted spec if the user-visible contract changes, the FastAPI route declaration and annotations that generate OpenAPI, and relevant tests through API callers. Review error status/envelopes, privacy of returned paths/details, queue/result races, and readiness transitions. See `docs/TESTING.md`, `docs/SECURITY-MODEL.md`, and the MVP spec's HTTP contracts.
