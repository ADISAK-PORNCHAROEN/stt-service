# Local STT Services

## Users and purpose

Local operators need Thai/English transcription of long recordings with readable text and segment times on modest CPU hardware. They need repeatable CLI output and a durable localhost service that reuses one loaded model while keeping private inputs and generated results under predictable ownership and retention.

## Critical journeys

| Journey | Trigger | Observable success | Failure behavior |
| --- | --- | --- | --- |
| Local transcription | Operator runs `stt transcribe` on a supported recording | A new output directory contains a canonical JSON transcript and derived TXT/SRT, with timestamps on the original recording timeline | Invalid input or processing failure returns a nonzero CLI result with useful diagnostics; source and prior outputs remain untouched |
| Service job lifecycle | Local client submits one recording to `POST /jobs`, polls status, then requests a result | Validated input is durably queued; a separate persistent worker processes it; success is reported only after the complete result bundle is published | Invalid/oversized input is rejected before queueing; interrupted work is failed without automatic retry; unfinished results are unavailable |

## Scope and constraints

- Approved MVP scope and acceptance remain in `.scratch/stt-mvp/spec.md`; implementation boundaries remain in `.scratch/stt-mvp/architecture.md`.
- The current optimization delivery is a CPU-only homelab test and portfolio demonstration, defined by `.scratch/stt-optimization/spec.md` and `docs/agents/issue-tracker.md`. GPU work is cancelled; decoding comparisons, batching, and language/hint trials are conditional. Only the two allowlisted real recordings in the evaluation specification are approved for that workflow.
- The local service is designed for loopback use and has no authentication or cross-origin browser support. Do not describe it as safe for LAN or Internet exposure.
- Whisper Turbo/faster-whisper on CPU INT8 is the MVP baseline. Local experimental profiles do not replace the approved baseline.
- No UI, speaker diarization, translation, or human alignment is in the accepted MVP scope.

## Acceptance examples

- Given a supported recording and a new destination, the CLI publishes JSON/TXT/SRT together and leaves the source and existing outputs unchanged. See MVP stories 1–4 and tests in `tests/test_cli.py`, `tests/test_contracts.py`, and `tests/test_inputs.py`.
- Given exactly one valid multipart `file`, the service returns a queued job only after durable acceptance; a result is served only after success. See MVP stories 5–14, `docs/API.md`, and `tests/test_api.py`, `tests/test_lifecycle.py`, and `tests/test_scheduling.py`.
- Given an optimization evaluation request, only the approved source allowlist and recorded input hashes are accepted. Software behavior checks do not substitute for the human text/timing review and experiment gates in the optimization spec and tracker.

These examples summarize existing accepted requirements; the linked specs and tickets remain canonical. Source inspection and ordinary tests do not establish full-recording recognition accuracy or home-server performance.
