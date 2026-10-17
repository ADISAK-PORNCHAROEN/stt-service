# 05 — Harden media validation, queue limits, and restart recovery

What to build: Verified boundary, concurrency, and interruption behavior for the service.
Blocked by: 03.
Status: Complete.
Ready for agent: Completed; verified implementation and regression checks.

Triage label: ready-for-agent

## Problem

Large or invalid uploads, simultaneous submissions, and process crashes can break a seemingly working queue. The MVP needs evidence for these cases rather than only a successful single-job path.

## Solution

Audit and harden ticket 03's contracts through public behavior checks and targeted fault/concurrency tests. Close gaps in bounded validation, transactional admission, singleton claims, and deterministic restart outcomes.

## User stories

- As a client, I can submit supported audio at the allowed boundaries and receive predictable rejection for malformed, oversized, overlong, or audio-free media. Even when other clients submit simultaneously, the service accepts no more than ten waiting jobs and rejected submissions leave no retained input or job record.
- As an operator, I can restart a worker during inference or publication and identify interrupted jobs as failed while untouched queued jobs survive. Restarting the API alone leaves active worker work intact, and an attempted second worker cannot claim or incorrectly recover another worker's jobs.

## Implementation decisions

Exercise WAV/MP3/M4A/FLAC/MP4, the inclusive 1 GiB and two-hour limits, decoded content checks, bounded streaming, and safe generated upload paths. Use [spec error and lifecycle rules](../spec.md). Enforce capacity and claims within transactions rather than request-local counts. Separate worker recovery from API startup and exclude autoretry.

Test crash windows before publication and after directory publication but before success commit. Failed interrupted work must not become a downloadable success; preserve safe orphan identification for retention. Make job failures isolated from later queued work. This ticket strengthens existing contracts without changing endpoint shapes or state vocabulary.

## Testing

Use fake-engine public CLI/API checks plus targeted SQLite/process fault injection where needed. Simulate byte/duration boundaries without allocating huge fixture files. Check competing admissions and claims, eleven waiting submissions, one running plus ten queued, invalid filename/content combinations, model failure, API-only restart, worker restart, retained queue order, and stale readiness. Real model integration remains opt-in; ordinary tests need no network/model.

## Acceptance criteria

- [x] Every accepted media type and exact input boundary has explicit validation evidence.
- [x] Invalid, oversized, overlong, or excessively fragmented uploads receive specified errors without retained rejected data.
- [x] Concurrent admission never exceeds ten queued jobs in addition to one running job.
- [x] Duplicate workers/claims cannot run the same work or recover a live owner's job.
- [x] Worker interruption and publication crash windows produce failed/interrupted outcomes, retained queued work, and no automatic retry.
- [x] API-only restart and long-running inference preserve accurate job state/readiness.
- [x] Required public behavior, concurrency/fault checks, and static checks pass with evidence.

## Out of scope

Retention scheduling, cancellation, retry endpoints, multiple-worker operation, and public-service abuse controls.

## Further notes

Ticket 05 can proceed independently of ticket 04 after ticket 03. Ticket 06 uses its fault cases when verifying cleanup safety.

Validation evidence: See [verification report](../../../docs/verification-20261017.md). Public CLI/API fake-engine checks, all supported media types and scaled boundaries, concurrency/recovery/retention regressions, Ruff and mypy pass. Real-model CLI plus separate actual HTTP/worker process smoke tests passed on the 15-second excerpt. No accuracy claim is made.
