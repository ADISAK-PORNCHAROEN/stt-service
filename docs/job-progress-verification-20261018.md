# API job progress — 18 October 2026

The owner approved estimated transcription progress through the existing
`GET /jobs/{job_id}` endpoint. `progress_percent` is a persisted integer: zero
while queued, increasing estimates up to 99 during inference, and 100 only after
publication and the success transaction. Failed/interrupted jobs retain the last
estimate. Clients must inspect `status` as well as progress. No ETA is provided.

The Whisper adapter reports segment positions while consuming the upstream
iterator. The shared pipeline converts decoded-audio positions into bounded,
monotone integers and emits at most 99 updates per job. SQLite writes affect only
running jobs. A serialized migration preserves existing records and backfills old
succeeded jobs to 100; other legacy jobs start at zero. There are no dependency,
endpoint, origin-policy, deployment, or model-profile changes.

## Observed validation

Executed against the working tree based on
`4193036b7b6dcfe217f502f2433baf01dd5387ff`. Production changes are confined to
`engines/whisper.py`, `pipeline.py`, `worker.py`, and `jobs.py` under
`src/stt_services/`; `tests/test_progress.py` adds seven regression cases.
Pre-existing unrelated documentation changes remain in the working tree.

| Command | Observed result |
| --- | --- |
| `uv run --env-file .env.local pytest tests/test_progress.py tests/test_api.py tests/test_whisper_engine.py -q` | 14 passed in 3.93 s |
| `uv run --env-file .env.local pytest -q` | 120 passed, 2 integration tests deselected, in 14.82 s |
| `uv run --env-file .env.local ruff check .` | Passed |
| `uv run --env-file .env.local ruff format --check .` | Passed, 68 files |
| `uv run --env-file .env.local mypy` | Passed, 17 production files |
| `git diff --check` | Passed; Git printed line-ending normalization notices |

HTTP/SQLite integration tests observe progress during inference and publication,
completion, inference/export failures, API recreation, interrupted recovery, and
a second silence-only job in the same worker. Targeted store tests verify legacy
migration, monotonicity, and queued/terminal update exclusion. Adapter tests use a
lazy fake upstream iterator in sequential and batched modes to prove updates occur
before the next segment is requested. Existing non-progress engines still pass
the ordinary suite. No tests or assertions were removed.

This follows the test-engineering contract's behavioral boundary and negative-case
guidance: HTTP/SQLite integration for client-visible state, narrow iterator tests
for incremental reporting, and the full ordinary regression suite. No frontend
exists for browser E2E testing. No coverage threshold or measurement is configured.
All new inference fixtures are generated or mocked; no real recording, model
download, or GPU inference was performed. Real-model progress remains unverified.

## Security diff review

Codex Security prompt-driven diff scan
`875decb1-eb20-4c3a-a2e7-13a9efa9788d` completed with zero reportable findings and
complete static coverage of the four changed production inventory items. The
parent performed source/control/sink review without an independent worker. Tests
and nearby API, audio, upload, configuration, publication and retention code were
supporting context. Review checked parameter binding, finite/bounded numeric
handling, bounded write count, running-only monotone updates, serialized migration,
callback isolation and publication-before-success ordering. Applicable risks were
OWASP Top 10:2025 A01, A05, A06 and A10. The attempted ASVS 5.0.0 primary-source read
returned HTTP 404; no specific ASVS compliance claim is made.

The source snapshot is
`codex-security-snapshot/v1:sha256:10b5c32cd571c6dc82949605072922be4486a1485c19d381b3caa465cb675419`.
The sealed [security report](<[private local path]>) was read back after completion.
This verification note and the tracker entry were added afterward; production
source and tests were unchanged. Native dependencies, advisory feeds, OS ACLs,
real-model runtime and unsupported public hosting were excluded. This review does
not certify the whole repository. Completion usage reported 967,991 total tokens,
964,680 input tokens, including 928,256 cached input tokens; measurement coverage
was complete and came from the workbench's owning-thread rollout accounting.

Restart API and worker processes to load the new code. Poll status every 1–2
seconds. Estimates may stall or jump during validation, VAD, silence and batch
processing; they measure audio position rather than elapsed work or time remaining.

## Subsequent real-model verification

The [CPU quality/progress follow-up](cpu-quality-progress-20261018.md) records four
successful real-model HTTP invocations on both full authorized originals, including
two under the locally selected profile. Polling observed intermediate monotone
percentages and 100 only with succeeded, with JSON/TXT/SRT downloads and source
hash/timeline checks. Real-model progress is therefore now exercised on the
development CPU; frontend and home-server execution remain unverified.
