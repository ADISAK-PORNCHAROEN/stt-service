# 02 — Read job status and service health through REST layers

**What to build:** A client can poll a Job and check API/worker readiness through stable HTTP responses backed by typed application data.

**GitHub issue:** [#3](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/3) · **Parent spec:** [#1](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/1)

**Blocked by:** [#2 — Submit transcription jobs through REST layers](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/2).

**Status:** Complete · **Ready for agent:** Done.

- [x] `GET /jobs/{job_id}` preserves lifecycle status, progress, timestamps, expiry, and safe error details.
- [x] Unknown, malformed, or expired Job identifiers retain their documented HTTP outcomes.
- [x] `GET /health` continues to distinguish API readiness from absent, loading, stopped, or stale worker/model readiness.
- [x] HTTP DTOs do not expose SQLite row shapes, private filesystem paths, or internal exceptions.
- [x] Public API tests cover queued, running, terminal, expired, and worker-readiness behavior through the application boundary.
- [x] Route registration, controller adaptation, service policy, and repository access each have a distinct responsibility.

**Validation evidence (2026-10-24):** Full suite passed (`uv run --env-file .env.local -- python -m pytest`, 133 passed, 2 deselected); Ruff, formatting, mypy, and `git diff --check` passed.
