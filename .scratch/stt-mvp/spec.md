# STT MVP specification

Status: approved scope; implementation planned. This document records requirements, not evidence of working software. No dependencies, models, tests, or benchmark results are established by this documentation task.

Read [architecture](architecture.md) for planned structure, [tickets](../../docs/agents/issue-tracker.md) for execution order, and [glossary](../../CONTEXT.md) for domain language. The approved requirements here supersede exploratory alternatives in [the handoff](../../STT-HANDOFF.md).

## Problem

A local user needs to transcribe long Thai/English recordings into readable text and segment timestamps on modest CPU hardware. The workflow needs a measurable CLI baseline and a local asynchronous service that reuses the same transcription behavior without repeatedly loading a model for each service job.

## Solution

Build the CLI baseline first, then a localhost FastAPI service with a durable SQLite queue and one separate worker. Use Python 3.12, uv, and a repository-root `.venv`. Run Whisper Turbo through faster-whisper on CPU with INT8 computation and four inference threads. The worker keeps one model instance loaded across jobs. PyTorch is not required by this backend.

JSON is the canonical transcript. TXT and SRT are derived from that JSON without inference. Publication exposes a complete result directory at once. Store runtime data under configurable `D:\ai-stt\`; the root `.venv` is the environment exception.

## User stories

- As a local operator, I can run `uv run stt transcribe <file> --output-dir <directory>` and receive a complete transcript while retaining my original recording. When validation, inference, or export fails, I receive a nonzero exit and useful error information without a partial published result or replacement of existing results.
- As someone reviewing Thai mixed with English, I can read UTF-8 text and match each segment to seconds in the original recording, including after silence or preprocessing. I can distinguish model timing from manually verified alignment through `timing_source=model`.
- As a local client, I can upload a recording, receive a job ID immediately after durable acceptance, poll its state, and fetch JSON, TXT, or SRT after success. I can distinguish a queued job from a running job and a failed job from an expired or unknown ID.
- As an operator restarting the service, I retain queued work and see interrupted running work fail explicitly. A separate worker loads the model once and processes one job at a time; failures do not silently trigger retries.
- As a user managing private recordings and limited disk space, I can predict when API-owned inputs and results expire. Cleanup preserves active work, and the CLI never deletes my sources or completed results.
- As a maintainer assessing usefulness, I can reproduce cold and warm baseline measurements on the supplied recording, inspect actual text and timing, and separate measured observations from unverified performance or accuracy claims.

## Implementation decisions and observable contracts

### Inputs and CLI

Accept WAV, MP3, M4A, FLAC, and MP4 containing decodable audio. Each input must be at most 1 GiB (1,073,741,824 bytes) and at most two hours (7,200 seconds); equality is allowed. Reject empty, corrupt, unsupported, audio-free, oversized, or overlong inputs before inference. Validate decoded content as well as the declared extension; upload filenames are untrusted metadata.

CLI results belong below the configured external storage root; `--output-dir` identifies the final result directory. Require that target to be absent, stage beside it on the same volume, and publish it only after all requested files are complete. Fail safely on a conflicting target. Never delete or overwrite a source or existing result. The JSON baseline is delivered in ticket 01; ticket 02 adds TXT/SRT to the completed bundle.

### Canonical transcript and exports

The versioned JSON contract includes `schema_version`, source display name and duration in seconds, model identity and effective CPU/INT8/four-thread settings, `timing_source` set to `model`, full `text`, and ordered `segments`. Each segment has an ID, `start`, `end`, and UTF-8 `text`. Timestamps are finite seconds from the beginning of the original recording, with `0 <= start <= end <= duration` and chronological start order. Preserve model overlap if present; do not invent word alignment. Source metadata must not disclose local absolute paths through HTTP.

Any chunking or silence removal must restore original offsets before canonical JSON is built. Empty speech is a valid successful transcript with empty text and segments. TXT preserves transcript text; SRT uses sequential cue numbers and `HH:MM:SS,mmm` boundaries derived from segments with deterministic rounding. Export validation must handle rounding boundaries and empty transcripts. Changing export format never reloads the model or reruns transcription.

### HTTP contract

Bind to loopback only, default `127.0.0.1`; public interfaces are outside scope. No public hosting, authentication scheme, or browser UI is included.

| Request | Contract |
| --- | --- |
| `POST /jobs` | Multipart `file`; validate and durably store input plus queued record before returning `202` with `id` and `state=queued`. |
| `GET /jobs/{id}` | `200` with ID, state, created/updated timestamps, terminal completion time when present, and a safe failure code/message when failed; no transcript text required. |
| `GET /jobs/{id}/result?format=json\|txt\|srt` | Default JSON; `200` for a succeeded job's completed requested artifact, with an appropriate media type and UTF-8 text encoding. |
| `GET /health` | API and worker readiness reported separately; overall `200` only when both are ready, otherwise `503`. Include model readiness and fresh worker heartbeat information without private paths. |

Unknown or expired IDs return `404`. Results for queued, running, or failed jobs return `409`. Unsupported result formats return `422`. Invalid media returns `422`; exceeding the byte limit returns `413`. Queue saturation returns `429`. Use consistent structured errors with a stable code and readable message; exclude stack traces and private data. API JSON delivery arrives in ticket 03; TXT/SRT routes become available in ticket 04.

At most ten jobs may be in `queued`, in addition to at most one `running` job. Admission checks and enqueue must be atomic across concurrent requests. Rejected uploads leave no queued row or retained input. Stream uploads with a byte cap; avoid buffering a potentially 1 GiB file in memory.

### Job lifecycle and readiness

Allowed transitions: `queued -> running -> succeeded|failed`; restart recovery also changes `running -> failed` with failure code `interrupted`. Terminal states do not transition back to queued. Queued jobs survive restart, and retries are never automatic.

Worker startup owns recovery while holding exclusive worker ownership, before claiming retained queued jobs. Restarting only the API must not fail a job held by a live worker. Model loading must succeed before worker readiness; model loading failure or a stale heartbeat makes worker readiness false. Health must distinguish API responsiveness from worker availability. Heartbeat cadence and stale threshold must be explicit, configurable, and verified during implementation.

Success is recorded only after atomic result directory publication. A crash between publication and recording success leaves an interrupted failed job on recovery; its unadvertised output is an orphan for safe cleanup, never a succeeded result. A failure in one job must not silently lose the other queued jobs.

### Storage and retention

Set `HF_HOME` and `UV_CACHE_DIR` under the external storage root before downloads. Use a single Hugging Face model cache, with no duplicate model tree. Keep uploads, queue database, staging data, results, caches, and runtime reports outside the repository. The supplied private MP4 currently in the workspace is an existing evaluation source, must be preserved, and must not be committed; newly created copies and artifacts use external storage.

| API-owned data | Retention clock |
| --- | --- |
| Successful job input | Delete when at least one day has elapsed since success. |
| Successful job results and status | Delete when at least seven days have elapsed since success. |
| Failed job input and status | Delete when at least one day has elapsed since failure, including interrupted failures. |

Use recorded UTC terminal timestamps and elapsed 24-hour days. Queued/running jobs are active and excluded from retention cleanup even if old. Run cleanup at startup and hourly, coordinating with worker ownership and queue operations. Also remove abandoned staging data and unpublished orphan results only after establishing they are inactive. Cleanup is idempotent, stays within managed storage, tolerates missing files, and retries filesystem failures on a later sweep without advertising an incomplete result as success. Failed-job orphan artifacts follow failed-job retention. Cache/environment deletion is outside cleanup scope. CLI sources and results are never subject to this retention policy.

## Testing and acceptance

Ordinary tests exercise public CLI/API behavior with an injected fake engine, require no model or network download, and use pytest and httpx. Verify original offsets, UTF-8 Thai/English, JSON schema, deterministic exports, output collisions, interrupted publication, invalid uploads, concurrent queue admission, restart behavior, readiness, and time-controlled cleanup. Real-model integration is explicitly opt-in. Use Ruff lint/format checks and a configured type checker; select and document the type-check command during scaffolding. No coverage threshold is agreed.

Planned commands after scaffolding: `uv sync`, `uv run stt transcribe <file> --output-dir <directory>`, `uv run pytest`, `uv run ruff check .`, and `uv run ruff format --check .`. Generate and version `uv.lock` during implementation. None of these commands is claimed to work yet.

Use the supplied MP4 (approximately 400.684 seconds, 18.3 MiB; remeasure before reporting). Record actual hardware, OS, Python/dependency/model versions and model revision, effective configuration, load time, inference time, total time through completed publication, and peak process RAM. Define timing boundaries and RAM measurement method. Report both `RTFx_inference = duration / inference_seconds` and `RTFx_total = duration / total_seconds`.

A cold run starts a fresh process with an unloaded model; report separately whether downloads or filesystem cache conditions affect it. A warm run reuses an already loaded model, as in the persistent worker, and records load reuse explicitly rather than suggesting a second CLI process retains a model. Separate downloads from steady-state measurements. Review actual Thai/English text, names, numbers, silence, segment boundaries, and original offsets manually; document observations and limitations. CER/WER require reviewed reference text and documented normalization/tokenization. No numerical performance or accuracy target is approved, and no server result may be inferred from development-PC measurements.

## Out of scope

GPU execution, Qwen or other alternative backends, EmbeddingGemma reader experiments, diarization, word timestamps, forced alignment, UI, public networking, automatic retries, multiple workers, and model training.

## Further notes

The handoff's external `.venv`, optional models, and thread comparisons are historical exploration. This MVP fixes the root environment and four-thread Turbo baseline. Home-server OS and actual performance remain unverified. Six dependency-ordered tickets define delivery; checking in these plans does not complete any ticket.
