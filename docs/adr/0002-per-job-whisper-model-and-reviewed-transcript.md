# ADR 0002: Select Whisper models per job and store reviewed transcript text

Status: Accepted
Date: 2026-10-26

## Context

The service needs to accept Turbo or large-v3 per job, preserve that selection while jobs wait or the service restarts, and support human text corrections without changing the ASR result or segment timing. The worker runs sequentially on a CPU host and must not retain both model variants. Result downloads and retention already serialize through a per-job filesystem lease.

## Decision

- Keep `WhisperEngine` as the shared adapter. Persist the selected model on each new job; if `POST /jobs` omits it, snapshot `STT_MODEL`. Legacy rows remain nullable and resolve through the current setting. The CLI continues using its configured model unchanged.
- Keep only one loaded worker pipeline. Release the current engine before constructing another model, reuse it for consecutive jobs selecting the same model, and fail a job explicitly if the requested model cannot load.
- Keep the published ASR bundle immutable. Save only the latest reviewed canonical JSON as `transcript.latest.json` with a same-directory atomic file replacement while holding the job result lease. TXT/SRT downloads are derived from that file; `original-json` always serves the original ASR JSON.
- Keep no edit history and do not extend result retention. Serialize transcript writes, downloads, and cleanup through the existing per-job lease.

## Consequences

- A queue delay or service restart cannot change a newly submitted job's selected model.
- Switching models releases the old pipeline before loading the next one, so both large model variants are not intentionally resident together. Model-load failures remain visible on the requested job and never use a different model silently.
- Transcript publication has one canonical latest-file pointer at the filesystem level. A failed temporary write or atomic replacement leaves the prior original/latest transcript in place; TXT/SRT always derive from one JSON snapshot.
- Legacy jobs remain readable without rewriting every database row. Their model resolves from the current service default because no historical selection was stored.
- Loading may make worker readiness unavailable while a model switch is in progress. A failed load keeps it unavailable until a later job loads successfully.
