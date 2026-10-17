# MVP verification — 17 October 2026

## Scope and current acceptance

Implemented the approved six-ticket runtime scope: uv/root `.venv`, shared Turbo
pipeline, CLI, JSON/TXT/SRT, localhost API, SQLite admission/claims, separate
persistent worker, interruption recovery, readiness, and managed retention.
The initial documentation baseline is Git `19a6f22`. Private recordings, raw
transcripts, databases, model weights and test artifacts remain outside Git.

Engineering checks below are complete. Full-recording cold/warm measurement and
human listening review are tracked separately; their absence must not be treated
as evidence of transcription quality or a numerical accuracy pass.

## Commands and observed evidence

| Check | Observed result |
| --- | --- |
| `uv sync --locked` | Passed; Python 3.12.10, 51 installed packages, repository `.venv` |
| `uv run pytest -q` | 75 passed, 2 real-model tests deselected (10.11 seconds) |
| `uv run pytest tests/test_scheduling.py -q` | 4 passed; startup/hourly cleanup and heartbeat during inference/slow cleanup |
| `uv run ruff check .` | Passed after formatting |
| `uv run ruff format --check .` | Passed |
| `uv run mypy` | Passed, 14 production files |
| Opted-in real-model CLI and subprocess HTTP tests | 2 passed in 63.16 seconds after final timeline hardening |

The integration command was:

```powershell
$env:HF_HOME = 'D:\ai-stt\cache\huggingface'
$env:STT_TEST_MEDIA = 'D:\ai-stt\audio\acceptance-15s.wav'
uv run pytest -m integration tests/test_real_model.py tests/test_http_real.py --basetemp 'D:\ai-stt\output\integration-final-20261017' -v
```

The WAV is a 15-second mono/16-kHz excerpt decoded from the supplied MP4, not a
replacement for it. Actual CLI inference and separate API/worker processes used
the cached real Turbo model. HTTP upload, polling, all three downloads, model
readiness, zero per-job model reload time, model revision and process cleanup
were verified. Both outputs had three segments bounded by the 15-second source.
This is a functional smoke test, not an accuracy score or isolated performance
experiment. Do not reuse an existing pytest `--basetemp` containing artifacts
you intend to keep.

Ordinary tests use generated media and fake inference while exercising public
CLI/API behavior with real filesystem and SQLite interactions. They cover all
five accepted formats, video without audio, malformed/empty requests, forced
demuxer rejection of disguised playlists, size/duration equality and rejection
using scaled limits, MP4 PTS offsets/gaps and resampling-tail bounds, fragmented
timeline rejection, filename traversal, Origin/Host rejection, concurrent
admission, additional running capacity, singleton worker ownership, API restart,
interruption before/after publication, job isolation after failure, heartbeat
expiry/loading failure, deterministic UTF-8/LF exports and SRT minute rounding.

Retention tests cover one/seven-day boundaries, GET expiry before cleanup,
startup/hourly scheduling, active jobs/download leases, filesystem deletion
failure/retry, stale orphans, and protection of CLI files. No numeric coverage
threshold was agreed; coverage was not measured. A maximum-size 1-GiB upload or
two-hour recording was not physically generated; scaled boundary tests and the
settings ceilings provide the corresponding evidence.

## Review

Standards and Spec reviews were delegated separately. Fixes included finalizing
all artifacts before directory publication, protecting CLI output from managed
cleanup paths, full-stream media validation, strict timestamp ranges, canonical
metadata, consistent HTTP errors, source PTS/gap mapping, resampling-tail
handling, bounded span mapping, and independent heartbeat/cleanup threads. A
security follow-up confirmed the 16,384-span cap and cached binary-search
boundaries address the source-amplification candidate; the public API regression
checks `422` and empty rejected-upload storage. Current review follow-up results
are recorded in ticket evidence.

Codex Security diff scan `03578183-7786-40f3-bb10-e778da668e2e` completed its
15-file source/manifest inventory. One conditional Unix lock-file accumulation
candidate was remediated with 1,024 fixed lock stripes and suppressed after
source validation. The current Windows host did not reproduce the original Unix
condition. Rejection/concurrency/lifecycle tests passed after the correction.

The workbench warns that working-tree contents changed during the scan; its
sealed result is associated with the starting snapshot. Follow-up source review
and tests cover the fixes, so this is **not** a claim that the final Git tree has
an immutable automated security certification. The scan report is retained in the
Codex Security workbench under the scan ID above. Native parser fuzzing, advisory
database auditing, Unix execution and public-network deployment were excluded.

The follow-up source-amplification candidate was closed after limiting a
decoded-to-source timeline to 16,384 discontinuous spans and caching its search
boundaries. Read-only media checks accepted 16,384 spans, rejected 16,385, and
merged 20,000 contiguous frames into one span. The public API regression returns
422 and leaves no rejected upload directory. This cap intentionally rejects
pathological discontinuous timelines; contiguous audio remains frame-count
unlimited by this rule.

The scoped guidance applied was WSTG v4.2 malicious file upload (`BUSL-09`) and
directory traversal (`ATHZ-01`), with OWASP Top 10:2025 used as a risk index.
Behavioral checks and independent review complement each other as described by
[Google's review guidance](https://google.github.io/eng-practices/review/reviewer/looking-for.html).
The referenced Google testing-blog page could not be fetched (redirect/access
error); no claim is made that its full text was consulted. Session/authentication
testing is outside this deliberately localhost-only, session-free MVP.

## Remaining acceptance evidence

- Full MP4 cold/warm runs: completed. See the
  [baseline report](../benchmarks/reports/20261017-turbo-cpu.md).
- Human listening comparison remains pending. Text/timeline structure has been
  inspected, but timestamp accuracy and questionable Thai terms are unverified.
- No reviewed reference text exists, so CER/WER and numerical accuracy claims
  are intentionally absent. Home-server performance remains unmeasured.
