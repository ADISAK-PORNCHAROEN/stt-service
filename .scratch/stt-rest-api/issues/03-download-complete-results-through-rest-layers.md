# 03 — Download complete job results through REST layers

**What to build:** A client can retrieve a succeeded Job's JSON, TXT, or SRT result through the new API layers while incomplete or expiring results remain unavailable.

**GitHub issue:** [#4](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/4) · **Parent spec:** [#1](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/1)

**Blocked by:** [#2 — Submit transcription jobs through REST layers](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/2).

**Status:** Complete · **Ready for agent:** Done.

- [x] JSON, TXT, and SRT remain available from one canonical transcript without another inference run.
- [x] Results remain unavailable until the Job is succeeded and the complete result bundle has been published.
- [x] Existing not-ready, missing/expired, and lease-conflict outcomes remain observable through the HTTP contract.
- [x] The result lease remains held until ASGI streaming completes or fails; retention cleanup cannot remove a file during an active download.
- [x] Public API and lifecycle tests verify complete publication, download behavior, and lease-versus-retention ordering.
- [x] Response DTOs and streaming response adapters remain API concerns; Job/result policy remains in the service/repository boundary.

**Validation evidence (2026-10-24):** Full suite passed (`uv run --env-file .env.local -- python -m pytest`, 133 passed, 2 deselected); Ruff, formatting, mypy, and `git diff --check` passed. The real API returned all three formats in the run recorded in issue #6.
