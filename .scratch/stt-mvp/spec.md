# STT MVP specification

Approved scope with implementation present. This specification records required behavior and the current source contracts; source inspection is not evidence that acceptance checks passed. Real-recording cold/warm measurements are recorded; human text/timing review remains in progress. The parent maintains ticket status and validation evidence in the [local tracker](../../docs/agents/issue-tracker.md).

Read the [architecture](architecture.md) for current responsibilities, [README](../../README.md) for operator commands, and [glossary](../../CONTEXT.md) for domain terms. This approved MVP supersedes exploratory alternatives in the [handoff](../../STT-HANDOFF.md).

## Problem Statement

A local user needs Thai/English transcription of long recordings with readable text and segment timestamps on modest CPU hardware. The workflow needs a reproducible CLI baseline and a durable asynchronous localhost service that shares transcription behavior and reuses a loaded model across service jobs. Private media and generated results require predictable ownership, publication, and retention.

## Solution

Use Python 3.12, uv, and the repository-root `.venv`. Transcribe using Whisper Turbo through faster-whisper on CPU INT8 with four inference threads as the agreed baseline. Provide `stt transcribe <file> --output-dir <directory>` and reuse its pipeline from one separate persistent-model worker behind a loopback FastAPI interface and SQLite queue.

JSON is the canonical transcript. Derive TXT/SRT from the same transcript without another inference run. Finalize all artifacts in staging before publishing a complete directory. Keep managed runtime data under configurable `D:\ai-stt\`, with a single Hugging Face model cache. The CLI accepts caller-selected destinations outside managed jobs/cache/locks; an external storage destination is recommended.

## User Stories

1. As a local operator, I can transcribe a supported audio/video file with the approved CLI and choose its output directory. My source remains unchanged, existing result directories are preserved, and failures produce a nonzero exit with useful diagnostics.
2. As someone reviewing Thai mixed with English, I can read UTF-8 full text and segments in JSON, TXT, and SRT without a translation step or loss of Thai characters. All formats describe the same recognized speech.
3. As a timing reviewer, I can locate segments in the original recording, including silence skipped by VAD. Times are finite seconds within the recording duration, and `timing_source=model` distinguishes estimated boundaries from reviewed alignment.
4. As a user requesting subtitles, I receive deterministically numbered SRT cues and millisecond time formatting from canonical segments. Requesting another export format does not reload a model or rerun inference, and silence-only input can yield an empty successful transcript.
5. As a local client, I can submit exactly one multipart `file`, receive `202` with `job_id` and `status=queued` after durable acceptance, and poll that identifier without holding a request open through transcription.
6. As a client tracking work, I can distinguish queued, running, succeeded, and failed status, inspect creation/start/finish/update times, and read safe failure details without being given private server paths.
7. As a client downloading results, I can choose JSON, TXT, or SRT after success. Before success I receive `409`; an unknown or expired identifier yields `404`, and incomplete staging is never served as a successful result.
8. As an operator, I can submit WAV, MP3, M4A, FLAC, or MP4 with audio up to and including 1 GiB and two hours. Empty, unsupported, malformed, corrupt, audio-free, oversized, or overlong submissions receive predictable errors before inference.
9. As an operator with limited CPU/RAM, I have at most ten queued jobs in addition to one running job, including during simultaneous submissions. Rejected uploads leave neither an accepted job record nor retained input.
10. As an operator running multiple jobs, I launch one worker independently of the API and reuse one model instance across sequential jobs. A second worker for the same data directory cannot claim work or recover another live worker's jobs.
11. As an operator restarting the worker, I see previously running work fail with `interrupted`, retain queued work, and receive no automatic retries. Restarting the API alone leaves a live worker's job intact.
12. As an operator checking readiness, I can distinguish a responsive API from a model-ready worker with a fresh heartbeat. Loading, stopped, absent, or stale workers make overall readiness false, including during long inference.
13. As a user receiving results, I see a complete directory only after every JSON/TXT/SRT artifact and its final metadata are written. Export, inference, or process failure cannot advertise a partial result as succeeded.
14. As an operator managing private data, I can rely on API successful inputs expiring after one day, successful results/status after seven days, and failed inputs/artifacts/status after one day. Startup/hourly cleanup excludes queued/running work and active downloads, retries filesystem failures, and never expires CLI-owned sources/results.
15. As a maintainer assessing this baseline, I can reproduce cold/warm measurements on the supplied MP4, identify model revision and effective configuration, distinguish model-load/inference/full-publication time, and inspect peak process RAM plus manual text/timing observations. Accuracy scores require reviewed reference text and documented normalization/tokenization.

## Implementation Decisions

### Runtime and stack

The manifest requires Python `>=3.12,<3.13` and uv manages the root `.venv` with `uv.lock`. Runtime dependencies are faster-whisper `>=1.2.1,<2`, PyAV `av>=18,<19`, FastAPI `>=0.115,<1`, uvicorn `>=0.34,<1`, python-multipart `>=0.0.20,<1`, pydantic-settings `>=2.8,<3`, psutil `>=7,<8`, and filelock `>=3.18,<4`. SQLite is provided by Python. PyAV is capped below 19 because faster-whisper 1.2.1 uses the `metadata_errors` argument removed in PyAV 19; the manifest and README record this upstream compatibility rationale. No PyTorch or separately installed FFmpeg is required by this stack.

The agreed inference baseline remains Turbo, CPU, INT8, four threads. Current settings expose model/thread configuration; record actual effective settings for every measurement rather than treating an override as evidence for the approved baseline. Transcription uses automatic language detection, VAD, beam size five, and no word timestamps. `faster_whisper.download_model` resolves the cached snapshot before model construction, and the snapshot directory name is recorded as `versions.model_revision`.

Set `HF_HOME` and `UV_CACHE_DIR` before downloads. Defaults are under the storage root; explicitly provided environment values take precedence. Use one HF cache rather than copying weights to a second model tree. `STT_DATA_DIR` defaults to `D:\ai-stt` on Windows and `~/.local/share/ai-stt` elsewhere. File-size, duration, and queued-job settings may lower but cannot exceed the approved ceilings. Storage is local disk; network shares are outside this design.

### CLI, validation, and output ownership

`uv run stt transcribe <file> --output-dir <directory>` accepts a caller-selected absent destination. Require it outside managed jobs/cache/locks; recommend an external location such as `D:\ai-stt\output\run-01`. There is no requirement that every CLI destination be a descendant of the external root. Never delete a source or expire/overwrite CLI results. CLI validation/processing errors return 1; keyboard interruption returns 130.

Accept WAV, MP3, M4A, FLAC, and MP4 containing decodable audio. Inclusive limits are 1,073,741,824 bytes and 7,200 seconds. Validate the suffix, file existence/size, audio stream, metadata duration, and the entire decoded frame stream before inference. Force the expected demuxer (`wav`, `mp3`, `mov`, or `flac`) and restrict protocols to `file,pipe` to prevent arbitrary playlist/protocol probing. Reject corrupt frames, invalid sample rates, and timelines with more than 16,384 discontinuous source spans. Sum decoded sample counts divided by frame sample rates using exact fractions; enforce the decoded-sample ceiling and also preserve the original recording duration, including container duration and audio PTS offsets. Cache decoded-span boundaries so mapping each timestamp uses binary search.

### Canonical transcript and publication

Current JSON includes `schema_version=1`, `source_name`, `duration_seconds`, `model`, `engine`, `configuration`, `versions`, `metrics`, full text under `text`, `timing_source=model`, and `segments`. Segment serialization adds one-based `id` values; each segment contains `start`, `end`, `text`, and `timing_source=model`. `source_name` is a basename, not an absolute path; API-managed inputs currently appear as `input.<extension>`.

Segments must have finite times, `0 <= start <= end <= duration_seconds`, and nondecreasing start order. Model overlap is allowed. Map decoded model times back through source PTS spans so initial offsets, source gaps, and VAD-skipped silence remain on the original timeline. Allow only the single 16-kHz sample of resampling tail rounding, clamped to recording duration; there is no broader duration tolerance or invented word alignment. Empty speech produces empty text and segments. Full text joins stripped segment text with newlines. TXT emits one stripped segment per line; SRT uses sequential cue numbers and `HH:MM:SS,mmm` with deterministic millisecond rounding.

The pipeline creates sibling staging on the destination filesystem and writes `transcript.json`, `transcript.txt`, and `transcript.srt`. Final metrics JSON is serialized while still staged, then the directory is renamed once to the absent destination. Published bundles are immutable; no metadata is rewritten after publication. Service success is committed only after publication. A crash after rename but before success commit becomes failed/interrupted on recovery and leaves an unadvertised artifact for managed cleanup.

### HTTP contracts

`uv run stt serve --port 8000` binds `127.0.0.1`; `uv run stt worker` launches the separate worker. Host/Origin checks reinforce loopback-only operation; cross-origin browser clients are unsupported.

| Request | Observable response |
| --- | --- |
| `POST /jobs` | Exactly one multipart `file`; `202` with `{"job_id":"<id>","status":"queued"}` after validated input and durable queued record. |
| `GET /jobs/{job_id}` | `200` with `id`, `status`, `created_at`, `started_at`, `finished_at`, `updated_at`, `error`, and `error_message`. Times are UTC epoch seconds, absent lifecycle times are null. `updated_at` is derived from finish/start/create in that order. |
| `GET /jobs/{job_id}/result?format=json\|txt\|srt` | JSON default; `200` completed artifact with JSON, plain-text, or SubRip media type, preserving UTF-8. |
| `GET /health` | `ready`, `api`, `worker`, `model_ready`, `heartbeat_at`, and `heartbeat_age_seconds`; `200` only when worker/model readiness is fresh, otherwise `503`. |

IDs are generated lowercase 32-character hexadecimal identifiers. Failure `error` is `interrupted` or `processing_failed`; `error_message` is a safe explanation, not a traceback. Result lease contention can also return `409`, and a missing result artifact returns `404`.

Errors use `{"detail":"<message>","error":{"code":"<code>","message":"<message>"}}` for application validation/HTTP errors. Preserve these mappings:

| Condition | HTTP | Error code |
| --- | --- | --- |
| Malformed multipart/request or invalid Content-Length | 400 | `invalid_request` |
| Disallowed Origin | 403 | `forbidden_origin` |
| Unknown/expired job or unavailable artifact | 404 | `not_found` |
| Nonsucceeded result or busy result lease | 409 | `result_unavailable` |
| File/request exceeds size limit | 413 | `file_too_large` |
| Unsupported extension | 415 | `unsupported_format` |
| Empty/corrupt/audio-free/overlong/over-fragmented input or invalid request parameter/format | 422 | `invalid_input` |
| Ten queued jobs already present | 429 | `queue_full` |

Stream uploads with bounded multipart headers/body overhead; do not buffer a 1 GiB file in memory. Validate before enqueue. Transactional admission permits ten queued jobs plus one running job; rejected input staging is removed. All error/readiness checks still require acceptance evidence; source inspection alone does not establish exhaustive coverage.

### Queue, worker, and retention

Allowed status transitions are `queued -> running -> succeeded|failed`; worker recovery also maps previous running jobs to failed with `interrupted`. No automatic retry occurs. SQLite transactions protect capacity and FIFO claims. A filelock OS-backed lock on `worker.lock` establishes singleton ownership before recovery. API startup does not recover jobs. The worker loads once and reuses the pipeline engine; heartbeat runs separately during loading/inference, every five seconds by default, with a 30-second stale threshold. Model loading must succeed for ready status.

Managed layout is `jobs.sqlite3`, `worker.lock`, 1,024 fixed `locks/bucket-<0000..1023>.lock` lease markers, `jobs/<job_id>/input.<extension>`, and `jobs/<job_id>/result/*`. Upload staging and result staging are private sibling directories. Worker cleanup runs after startup/model initialization and hourly on a maintenance thread independent of heartbeat. Hash-bucket leases bound marker storage; concurrent unrelated IDs can briefly contend, and result contention returns `409`. Apply elapsed UTC 24-hour days from `finished_at`:

| API-owned data | Expiry |
| --- | --- |
| Successful input | One day after success |
| Successful results/status | Seven days after success |
| Failed input/artifacts/status | One day after failure, including interrupted failure |

Queued/running jobs are excluded regardless of age. Unknown inactive upload/orphan directories become cleanup candidates after one day. File locks protect active uploads/downloads from cleanup. Delete terminal filesystem data before removing its database record so failures can retry; missing files are tolerated. GET rejects expired status/results even before a sweep. Fixed lock markers contain no transcript/media and may persist. Cleanup stays within managed jobs storage and preserves caches, environment, CLI-owned data, and the supplied source MP4.

## Testing Decisions

Use pytest/httpx through public CLI/API seams with fake engines for ordinary checks, without model downloads or network. Cover Thai/English UTF-8, empty speech, original offsets/gaps and strict duration bounds, resampling-tail rounding, fragmented-timeline rejection, exports/rounding, invalid inputs and exact limits, output conflicts, staged publication failures, concurrent capacity/claims, worker ownership/restart, stale readiness, retention boundaries, active downloads, orphan cleanup, and filesystem failure retry. Targeted storage/fault tests support crash/race invariants. No coverage threshold is approved.

Dev dependencies include pytest `>=8,<10`, httpx `>=0.28,<1`, Ruff `>=0.11,<1`, mypy `>=1.15,<2`, and types-psutil `>=7,<8`. Configured commands are `uv sync --locked`, `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, and `uv run mypy`. Default pytest excludes integration; opt in with `STT_TEST_MEDIA` and `uv run pytest -m integration tests/test_real_model.py`. These are configured checks, not a claim of passing execution in this documentation update.

Run `uv run stt benchmark <file> --output-dir <directory>` using the supplied MP4 (approximately 400.684 seconds and 18.3 MiB; verify actual measurements). Keep private benchmark artifacts outside the repository. Capture source hash/size, actual hardware/OS, versions/model revision, settings, cold/warm load/inference times, full publication time, RTFx, and peak process RSS. Cold is the first unloaded-model run in a fresh benchmark process; warm reuses that model. OS page cache is not flushed. First-load download time is included if uncached, so disclose it and use cached weights for steady-state comparison.

Benchmark `wall_seconds` wraps the complete pipeline call through publication and its return; top-level per-run `rtfx_total` is duration divided by that wall time. Transcript `metrics.total_seconds` and its `rtfx_total` stop before final metrics JSON serialization/rename, so they are not full-publication metrics. Report inference RTFx separately. psutil samples process RSS every 50 ms during pipeline processing; sampling can miss brief peaks and does not isolate model-only RAM.

Manually review actual Thai/English text, names, numbers, silence, boundary timing, and original offsets; document observations and limitations. CER/WER require reviewed ground truth and documented normalization/tokenization. No performance/accuracy threshold is approved, and development-PC measurements establish no home-server result. Benchmark/review and acceptance evidence remain pending/in progress under parent ownership.

## Out of Scope

GPU execution, Qwen or alternative engines, EmbeddingGemma reader experiments, diarization, word timestamps, forced alignment, UI, public networking, cross-origin browser clients, automatic retries, multiple workers, model training, and automatic deletion of CLI-owned files/results.

## Further Notes

The full six-ticket scope remains accepted; this update neither changes ticket criteria nor marks implementation/quality acceptance complete. Current source and README replace earlier planned module names and invented response-field/output-root restrictions. Existing repository guidance describes a pre-scaffolding snapshot; the files now present establish implementation structure, while the parent-owned tracker records verification evidence. Home-server OS/runtime behavior and actual quality/performance remain unverified until measured and reviewed there.
