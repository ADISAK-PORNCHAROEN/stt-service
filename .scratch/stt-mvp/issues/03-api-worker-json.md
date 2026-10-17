# 03 — Add localhost API, durable queue, and persistent worker

What to build: Asynchronous JSON transcription through a loopback API and one separate worker.
Blocked by: 01.
Status: Blocked.
Ready for agent: No; ticket 01 must be complete.

## Problem

CLI users cannot submit durable asynchronous work or reuse a loaded model across service jobs. HTTP inference inside request handlers would also couple request lifetime to long CPU processing.

## Solution

Introduce FastAPI, SQLite job persistence, and one separate serial worker using the shared pipeline. Provide submission, status, JSON result, and API/worker readiness endpoints from the approved contract.

## User stories

- As a local client, I can upload a valid recording, receive `202` with a durable queued ID, and poll until the worker publishes a complete JSON result. I can distinguish pending, failed, and unknown jobs without accessing filesystem paths or waiting for transcription in the upload response.
- As an operator, I can start the API independently of the worker and see separate readiness. Once the worker loads its model, several queued jobs reuse that instance; restarting only the API leaves live worker jobs alone, while worker restart fails interrupted jobs and preserves queued work.

## Implementation decisions

Use the [HTTP and lifecycle contracts](../spec.md). Stream bounded uploads, validate inputs before acceptance, enforce the ten-queued-job cap transactionally, and use generated storage identities. Persist inputs before committing queued records. Atomically claim queued jobs with a single worker owner; document the cross-process ownership mechanism and heartbeat cadence/stale threshold. Keep health fresh throughout long inference and require successful model loading for worker readiness.

Implement the four states, explicit interrupted failure recovery, and no automatic retries. Publish before recording success and withhold results for all nonsucceeded states. Preserve queued work on restart. Keep filesystem/database crash windows explicit and identifiable for later cleanup. Baseline validation, capacity enforcement, and recovery must work here; ticket 05 supplies adversarial boundary/race hardening rather than permission to omit these contracts.

## Testing

Use httpx with fake-engine service seams for submission/status/JSON delivery, error responses, durable state, separate process lifecycle behavior, model reuse, model-load failure, stale heartbeat, singleton worker ownership, queue saturation, and restart recovery. Confirm no model is loaded by HTTP handlers. Include CLI regressions and run ordinary lint/format/type checks.

## Acceptance criteria

- [ ] Loopback endpoints implement durable `202` acceptance, state polling, JSON delivery, and documented errors.
- [ ] One separate worker serially processes jobs with one persistent model instance.
- [ ] SQLite claims and admission preserve the ten queued plus one running limit.
- [ ] Worker restart marks running work failed/interrupted, retains queued jobs, and never autoretries.
- [ ] API restart cannot fail a live worker's job; ownership prevents a second worker from consuming work.
- [ ] Health reports API/worker/model readiness accurately, including loading and stale-worker cases.
- [ ] Success follows complete atomic publication; public fake-engine checks and required static checks pass.

## Out of scope

HTTP TXT/SRT, retention scheduling, public deployment, and multiple workers.

## Further notes

Tickets 04 and 05 build on this service. Document startup/shutdown instructions and validated configuration during implementation.

Validation evidence: Pending implementation; no API or worker exists by virtue of this ticket.
