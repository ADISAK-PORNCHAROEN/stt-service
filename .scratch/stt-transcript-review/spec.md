# Whisper Model Selection and Transcript Review API

**GitHub spec:** [stt-service#10](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/10)
**Related product spec:** [frontend-stt#8](https://github.com/ADISAK-PORNCHAROEN/frontend-stt/issues/8)
**Status:** Backend acceptance for #11 and #12 passed locally; PR merge is pending. Keep this parent spec issue #10 open as requested. Frontend UI integration remains in frontend-stt #9/#10.

## Problem Statement

The STT service starts with one configured Whisper model for every job, and completed results have no supported transcript-edit path. The frontend needs stable API behavior for per-job model choice and owner-reviewed transcript text.

## Solution

Extend the service job lifecycle so callers can choose Turbo or large-v3 per job, the worker uses the persisted choice while keeping only one model loaded, and the API can save a text-only transcript correction without changing the original ASR output or segment timing.

This is the service-side contract for the product workflow in [frontend-stt issue #8](https://github.com/ADISAK-PORNCHAROEN/frontend-stt/issues/8). Frontend controls and same-origin proxy integration are tracked in that repository.

## User Stories

1. As an API caller, I want to choose Turbo or large-v3 for a submitted job, so that each recording can use the model I selected.
2. As an existing API or CLI caller, I want omitted model selection to keep using STT_MODEL, so that current workflows remain compatible.
3. As an API caller, I want the job to remember its selected model, so that queue delays and service restarts do not change the requested inference.
4. As an operator, I want the worker to keep only one model loaded, so that model switching has predictable memory use on the CPU host.
5. As an API caller, I want model-load errors reported against the requested job, so that the service never silently transcribes with a different model.
6. As a reviewer, I want to submit all corrected segment texts in one operation, so that an edit is stored as one consistent result.
7. As a reviewer, I want the original ASR result and segment timing preserved, so that corrections remain auditable and exports stay synchronized.
8. As a client, I want normal result and export formats to use the latest saved text and an explicit format to return the original, so that both versions remain available without edit history.

## Implementation Decisions

- Keep WhisperEngine as the adapter; Turbo and large-v3 are model variants, not separate engines.
- POST /jobs accepts an optional multipart model field restricted to turbo or large-v3. When omitted, use configured STT_MODEL. Communicate the configured default through the health/readiness contract so the frontend can show the matching initial choice. Keep CLI behavior unchanged.
- Persist model selection with each Job and migrate existing SQLite databases safely. Jobs lacking a selection use the configured default.
- Keep at most one model loaded in the worker. Reuse a loaded matching model; load the requested model when it changes. Fail that job clearly if loading fails; never silently fall back.
- PUT /jobs/{job_id}/transcript accepts the complete existing segment ID/text set. Accept edits only for succeeded jobs, reject any missing/extra/duplicate/mismatched IDs, change text only, and save all changes atomically.
- Preserve the original ASR transcript and the latest saved text, with no per-edit history. Normal json, txt, and srt result formats use the latest saved transcript; original-json returns the immutable ASR transcript. TXT/SRT remain derived from the canonical JSON transcript.
- Keep existing service retention and job lifecycle rules.
- Clarify Engine versus Model in the glossary, record an ADR for per-job model selection and the one-loaded-model worker policy, and update service API documentation.

## Persistence and concurrency details

- New jobs store the selected model in SQLite. Existing rows keep a null model after the additive migration and resolve it from the current `STT_MODEL` setting when read.
- The original result bundle stays immutable. A reviewed save builds the complete updated JSON in memory, writes a same-directory temporary file, flushes it, and atomically replaces `transcript.latest.json` while holding the existing per-job result lease. A failed write or replace leaves the previous latest transcript intact.
- Regular JSON uses `transcript.latest.json` after the first edit. TXT/SRT are rendered from that canonical latest JSON for each download. `original-json` always uses the original `transcript.json`. The service keeps no earlier edit; result downloads, edits, and retention cleanup serialize through the existing lease.
- The transcript update body is bounded to 16 MiB and streamed before JSON validation.

## Testing Decisions

- Test behavior through the public API and CLI with fake inference and real SQLite/filesystem state.
- Cover model validation/defaults, stored selection and migration, worker reuse/switch/failure, edit eligibility, exact segment preservation, atomic saves, original result preservation, and exports from saved text.
- Use one real API run per model with only the owner-approved Formal Words recording and its 87 reviewed cues. Follow the existing scoring policy, report actual results plus model/software versions, runtime, and RAM, and set no new CER/WER threshold. Keep audio, reference text, and raw results outside Git/GitHub.
- Backend implementation checks and the two required real API runs are recorded in the [#11 ticket](issues/01-select-whisper-model.md), [#12 ticket](issues/02-review-edit-transcript.md), and [Formal Words acceptance report](../../docs/formal-words-model-api-acceptance-20261026.md). Output important-error and timing review remain pending; the reported scores have no acceptance threshold.

## Out of Scope

- Frontend UI and same-origin proxy implementation; those remain in frontend-stt issues.
- Additional engines/models, fine-tuning, dataset creation, automatic correction suggestions, word-level timestamps, or editing segment times.
- Edit history, extended retention, GPU/homelab tests, Docker deployment, or public/LAN exposure.
- Uploading media, reference text, model weights, or raw evaluation results to GitHub.

## Further Notes

- This service spec supports the product workflow in [frontend-stt#8](https://github.com/ADISAK-PORNCHAROEN/frontend-stt/issues/8).
- [stt-service#11](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/11) covers per-job model persistence and worker execution. [stt-service#12](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/12) covers saved transcript updates and result formats. They are independent backend tickets.
- Frontend controls are tracked separately in [frontend-stt#9](https://github.com/ADISAK-PORNCHAROEN/frontend-stt/issues/9) and [frontend-stt#10](https://github.com/ADISAK-PORNCHAROEN/frontend-stt/issues/10).
- Keep this spec open until its service-side work has been accepted.
