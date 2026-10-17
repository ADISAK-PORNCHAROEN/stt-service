# 06 — Add managed retention and record MVP acceptance

What to build: Safe API data expiry and end-to-end acceptance evidence.
Blocked by: 04, 05.
Status: Blocked.
Ready for agent: Runtime acceptance is verified; waiting for tickets 02 and 04 acceptance.

Triage label: ready-for-agent

## Problem

API-owned recordings and results can accumulate indefinitely, while careless cleanup can destroy active work or user-owned sources. The completed MVP also needs a consolidated record of what was actually verified.

## Solution

Run coordinated cleanup at startup and hourly with the agreed terminal-state clocks, then verify the complete CLI/service workflow and record measured acceptance evidence and limitations.

## User stories

- As an operator, I can rely on successful API uploads expiring one day after success, successful status/results after seven days, and failed input/status after one day. Old queued or running work survives cleanup, and CLI-owned media/results remain mine to manage.
- As a local client, I can use a completed result until expiry and receive an unknown/expired response afterward without seeing a half-deleted bundle. Filesystem errors during a sweep can be retried safely instead of silently stranding private data or deleting unrelated storage.
- As the owner accepting the MVP, I can review passing behavior checks, actual recording measurements, and manual text/timing observations together. I can see which hardware was measured and which capabilities or accuracy claims remain unverified.

## Implementation decisions

Follow the [retention policy](../spec.md#storage-and-retention): use recorded UTC terminal times and elapsed 24-hour days. Coordinate sweeps with queue claims, publication, and downloads. Exclude active jobs and all user-managed CLI sources/results. Reconcile inactive staging, abandoned uploads, and unpublished orphan results only within managed storage; failed-job orphan artifacts use failed retention.

Make cleanup idempotent and recoverable across missing files, open files, partial deletion, and process restart. Keep enough bookkeeping to retry filesystem failures while preventing access to expired/incomplete bundles. Preserve caches and environment. Finalize operator instructions for environment/cache setup, CLI, separate API/worker startup, readiness, retention, and opted-in integration/benchmark execution.

## Testing

Use fake-engine public API checks and a controllable clock at just-before, exact, and after each expiry boundary. Exercise startup/hourly scheduling, active jobs older than retention, concurrent claims/publication/downloads, orphan data, deletion failures/retries, and repeated sweeps. Verify user-owned CLI artifacts and original supplied media are untouched.

Run the ordinary suite, Ruff lint/format, and configured type checking. Perform opt-in real-recording acceptance through the final workflow; retain or update ticket 02's cold/warm measurements with explicit conditions. Record load/inference/total/RTFx/peak RAM and manual Thai/English text/timing observations. Do not compute CER/WER without reviewed ground truth and documented normalization/tokenization.

## Acceptance criteria

- [x] Startup and hourly cleanup enforce every success/failure retention clock at the exact boundary.
- [x] Queued/running jobs, active result access, user-owned CLI artifacts, caches, and environment are protected.
- [x] Inactive staging/orphans are reclaimed safely and cleanup tolerates/retries partial failures.
- [x] Expired statuses/results are unavailable with consistent HTTP behavior.
- [x] End-to-end fake-engine checks, ordinary tests, lint, format, and type checking pass with recorded commands/outcomes.
- [x] Real MP4 cold/warm measurements are recorded with hardware, versions, conditions, and limitations.
- [x] Two user phrase corrections and their model-derived timing limitations are recorded without raw transcript in Git.
- [ ] Manual text/timing review across the original audio is recorded, including remaining unverified categories and limitations.
- [x] Operator instructions and sanitized acceptance summary distinguish measured evidence from remaining gaps.

## Out of scope

Deletion of user-managed sources/results, cache eviction, new engines, public deployment, invented performance thresholds, and unreviewed accuracy scores.

## Further notes

The implementation evidence is complete for tickets 01, 03, and 05. Ticket 02's manual text/timing review remains necessary before tickets 04 and 06 can close. Home-server behavior remains unmeasured.

Validation evidence: [Engineering verification](../../../docs/verification-20261017.md) and [baseline measurements](../../../benchmarks/reports/20261017-turbo-cpu.md). Runtime, retention, lifecycle, API/worker, and opt-in real-model paths are verified. Cold/warm measurements and two user-reviewed phrases are recorded; full text/timing acceptance remains open.
