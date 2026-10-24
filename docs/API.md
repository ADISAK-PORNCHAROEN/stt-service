# HTTP API contract map

The local service is a loopback FastAPI application. `src/stt_services/api/app.py` creates the application and configures middleware and error mapping. Route declarations under `src/stt_services/api/routes/` define the HTTP endpoints and generate `/openapi.json`; controllers adapt HTTP requests and responses through application services, while DTOs define public payloads. The transcript data shape is owned separately by `src/stt_services/domain/transcript_entities.py`; it is not the source of HTTP response models. The MVP specification owns detailed accepted semantics and error mapping.

| Route | Contract summary |
| --- | --- |
| `POST /jobs` | Accept exactly one multipart field named `file`; validate the uploaded media before durable queue admission; return `202` with `job_id` and `status=queued`. |
| `GET /jobs/{job_id}` | Return lifecycle status, progress, timestamps, and safe error fields for a valid, retained job identifier. |
| `GET /jobs/{job_id}/result?format=json|txt|srt` | Return an artifact only after success. JSON is the default; result lease conflicts and unavailable results remain observable. |
| `GET /health` | Report API and worker/model readiness; a missing, loading, stopped, or stale worker produces unavailable readiness. |

Important boundaries include bounded streaming uploads, pre-admission media inspection, loopback binding, Host/Origin checks, response-time result leases, and safe public errors. This is not an authenticated multi-user API and does not support cross-origin browser clients.

`JobsController` maps upload parsing, application errors, and leased result streaming to HTTP responses. `JobService` owns job lookup, expiration, readiness, and result availability policy; `JobRepository` defines lifecycle persistence operations. `SQLiteJobRepository` implements that contract with coordinated SQLite and filesystem behavior. Health routes use a separate controller and DTO.

When changing a route, update the accepted spec if the user-visible contract changes, the FastAPI route declaration and annotations that generate OpenAPI, and relevant tests through API callers. Review error status/envelopes, privacy of returned paths/details, queue/result races, and readiness transitions. See `docs/TESTING.md`, `docs/SECURITY-MODEL.md`, and the MVP spec's HTTP contracts.
