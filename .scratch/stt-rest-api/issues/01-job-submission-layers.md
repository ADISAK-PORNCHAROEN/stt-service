# 01 — Submit transcription jobs through REST layers

**What to build:** A client can submit a bounded recording upload and receive a durable queued Job response through the new route, controller, DTO, service, and repository boundaries.

**GitHub issue:** [#2](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/2) · **Parent spec:** [#1](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/1)

**Blocked by:** None (can start immediately).

**Status:** Complete · **Ready for agent:** Done.

- [x] `POST /jobs` preserves its accepted response and existing validation/error behavior.
- [x] The public request/response DTO is separate from the internal Job entity and SQLite representation.
- [x] Queue admission still atomically coordinates the SQLite transaction with the staging-to-managed-file move and failure cleanup.
- [x] Rejected, oversized, malformed, and cancelled uploads do not leave an accepted Job or retained staging input.
- [x] Public API tests exercise acceptance and rejection behavior using temporary SQLite/filesystem state and fake inference.
- [x] The API files use resource-and-role names such as `jobs_routes.py`, `jobs_controller.py`, and `jobs_dto.py`; no layer is a pass-through without distinct behavior.

**Validation evidence (2026-10-24):** Full suite passed (`uv run --env-file .env.local -- python -m pytest`, 133 passed, 2 deselected); Ruff, formatting, mypy, and `git diff --check` passed. The real API integration run is recorded in issue #6.
