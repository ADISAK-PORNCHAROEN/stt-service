# 04 — Migrate worker and shared callers to the Job boundary

**What to build:** The persistent worker and CLI continue to process and publish transcription jobs through the shared pipeline after the Job repository and REST boundaries are established.

**GitHub issue:** [#5](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/5) · **Parent spec:** [#1](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/1)

**Blocked by:** [#2 — Submit transcription jobs through REST layers](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/2); [#3 — Read job status and service health through REST layers](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/3); [#4 — Download complete job results through REST layers](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/4).

**Status:** Complete · **Ready for agent:** Done.

- [x] Worker claim, progress, finish, failure, recovery, heartbeat, retention, and singleton ownership preserve existing lifecycle behavior.
- [x] The worker still loads one model per process and reuses the shared transcription pipeline.
- [x] CLI behavior and output ownership remain unchanged; CLI and worker do not depend on FastAPI DTOs or controllers.
- [x] The target package layout groups media, transcription, worker, and evaluation responsibilities without creating generic pass-through layers.
- [x] Existing callers are migrated before obsolete persistence/API entry points are removed.
- [x] The architecture/API documentation and local tracker point to the accepted module ownership and new issue set.
- [x] Lifecycle, scheduling, CLI, API, and pipeline checks pass; evidence records exact commands and limitations.

**Validation evidence (2026-10-24):** Full suite passed (`uv run --env-file .env.local -- python -m pytest`, 133 passed, 2 deselected); Ruff, formatting, mypy, and `git diff --check` passed. A full local CPU/API integration run is recorded in issue #6. The diff security review found no reportable findings; it records documentation and host-configuration follow-ups.
