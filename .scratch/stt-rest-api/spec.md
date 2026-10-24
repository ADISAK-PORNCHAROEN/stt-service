# Local transcription workflow and REST API architecture

Status: Owner-approved and published as [GitHub issue #1](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/1). This spec combines the accepted REST layering and file naming direction with the previously agreed local transcription scope. It does not change runtime implementation.

## Problem Statement

The project already transcribes recordings through a CLI and an asynchronous localhost REST API, but the API and job lifecycle responsibilities are concentrated in a few modules. The owner wants a conventional REST structure with routes, controllers, DTOs, services, repositories, and entities, using filenames that make each API module's purpose obvious. The implementation must remain understandable and preserve the existing job, worker, upload, and result lifecycle.

The immediate product goal is to verify accurate CPU transcription and API delivery locally using only the supplied Formal Words recording and its 87-cue reference. CPU comparisons, conditional optimization experiments, homelab testing, and deployment are not part of this local milestone.

## Solution

Restructure the API around the Job resource using feature-scoped conventional layers: routes bind HTTP endpoints, controllers adapt HTTP input/output, DTOs define HTTP payloads, a Job service owns application policy, a repository contract separates persistence, and Job entities represent internal state. Use descriptive role suffixes such as `jobs_routes.py`, `jobs_controller.py`, and `jobs_dto.py` in their corresponding API folders. Keep route and controller responsibilities distinct; combine them if one would only forward calls.

Preserve the current asynchronous REST contract and separate persistent worker. Keep the shared transcription pipeline available to both CLI and worker. After the structural migration, verify the local CPU path against the Formal Words reference and confirm the API returns complete JSON, TXT, and SRT results.

## User Stories

1. As a local client, I can submit one recording as a Job resource and receive a durable queued response without waiting for inference to finish.
2. As a client, I can poll a Job and read its status, progress, timestamps, and safe failure information through a stable HTTP response DTO.
3. As a client, I can retrieve JSON, TXT, or SRT after a Job succeeds, and I cannot receive a partial result bundle.
4. As an operator, I can distinguish API readiness from worker/model readiness through the health endpoint.
5. As a maintainer, I can find route, controller, DTO, service, repository, and entity responsibilities by their folder and filename.
6. As a maintainer, I can change an HTTP DTO without changing the internal Job entity or SQLite row representation.
7. As a maintainer, I can change Job application policy without putting FastAPI request/response types or SQL operations into that policy.
8. As an operator, I can keep one persistent CPU model in the separate worker while CLI and worker share the same transcription pipeline.
9. As a reviewer, I can use the supplied Formal Words MP4 and 87-cue reference as the only real recording/reference pair in this milestone.
10. As an operator, I can run the local CPU transcription and API workflow on the current computer without requiring a homelab connection.
11. As a user, I can inspect a reference-backed result and clearly distinguish software/API success from human-checked transcription accuracy.
12. As a maintainer, I can validate structural changes using public API/CLI behavior with fake inference and SQLite/filesystem effects, then run the approved local recording workflow for acceptance.
13. As a data owner, I can keep the source audio, reference text, model data, caches, and raw result bundles out of public issues and outside Git wherever the repository's ignore policy requires it.

## Implementation Decisions

- Use a feature-scoped REST layout. API modules are grouped by responsibility under API folders, with resource-and-role filenames such as `jobs_routes.py`, `jobs_controller.py`, `jobs_dto.py`, and corresponding health modules.
- Keep API DTOs separate from `Job` and transcript entities. DTOs represent public HTTP contracts; entities represent internal application state; persistence rows remain adapter details.
- Keep the dependency direction inward: routes/controllers depend on application services and DTOs; services depend on entities and repository contracts; concrete SQLite/filesystem code implements repository contracts at the outer boundary.
- Routes register HTTP paths, methods, dependencies, and OpenAPI metadata. Controllers translate HTTP requests, responses, and application errors. Do not create a controller that adds no work beyond forwarding a route call.
- The Job service owns application-level submission, status, expiration, and result-availability policy. FastAPI-specific request parsing and response streaming stay at the API boundary.
- Keep SQLite admission and staging-to-managed-file movement coordinated as one durable repository operation, including failure compensation. Do not split this invariant across independent database and storage calls.
- Preserve result leases until ASGI file streaming completes. Retention cleanup must continue to skip active jobs and leased downloads.
- Keep the persistent worker's singleton lock, startup recovery, heartbeat, cleanup, and single loaded model. The worker uses lifecycle operations through the repository boundary and the shared transcription pipeline for inference.
- Preserve the canonical transcript and output contract: JSON remains canonical; TXT and SRT derive from the same transcript; segment times remain on the original recording timeline; success is visible only after complete atomic result publication.
- Keep the existing CPU Whisper baseline for this milestone. Do not compare CPU profiles, run batching or language/hint experiments, test on the i7-4770K homelab, or deploy. Docker/deployment remains later work after local acceptance.
- Limit real-recording work to the supplied Formal Words MP4 and its matching 87-cue reference, using the existing ignored project-local copy. Do not include source media or reference text in GitHub issue bodies. Use the existing reference workflow and report review/coverage status honestly; do not claim verified accuracy for unchecked cues.
- Completed MVP work remains complete. The Qwen/GPU experiment is cancelled. The owner's later request to remove OPT-02 through OPT-05 from the active plan supersedes the stale optimization breakdown for this milestone. The previous OPT-01 local/API and reference goal is narrowed to Formal Words on the current computer; homelab acceptance is deferred.

## Testing Decisions

- Prefer the highest public seam that proves behavior: exercise HTTP routes through the FastAPI test client with fake inference, real temporary SQLite/filesystem state, and observable responses; exercise CLI behavior through its public command entry point.
- Test route status codes and payloads, validation and safe errors, queue capacity/admission rollback, restart recovery, complete result publication, and lease-versus-retention behavior. Tests assert behavior visible to clients/operators rather than private helper calls.
- Preserve existing contract and lifecycle tests as prior art. Add or adapt cases only where the migration changes a public outcome or exposes a missing regression check.
- After structural checks, run the approved local Formal Words CPU path and inspect its result against the supplied reference. Keep command output and sanitized evidence separate from the private audio, reference, and raw results.
- Do not use fake-inference checks as evidence of recognition accuracy. Record unchecked reference cues, timing limitations, and any unresolved errors instead of making a blanket accuracy claim.

## Out of Scope

- CPU profile comparison, parameter sweeps, batching, language/vocabulary hints, alternate models/engines, GPU work, and performance optimization claims.
- Homelab/server testing, Docker packaging, deployment, public-network operation, GitHub Actions, and production readiness.
- Any real recording or reference other than the supplied Formal Words pair; additional datasets, excerpts, or generated substitutes.
- Reopening completed MVP tickets or the cancelled Qwen/GPU work.
- Changing the public REST contract unless required to fix an explicitly documented defect and accepted separately.

## Further Notes

The current implementation already exposes a Job-oriented asynchronous REST API. This work changes internal organization and makes the requested layer boundaries explicit; it should preserve endpoint behavior. The earlier architecture review found that `api.py` combines HTTP adaptation with Job policy, `jobs.py` owns several persistence and filesystem lifecycle concerns, and upload handling obtains a lease capability by constructing another store.

The approved verification seam is the existing public HTTP and CLI workflow with fake inference and real SQLite/filesystem behavior, followed by the single approved local Formal Words run. The owner approved this seam and the five-ticket dependency breakdown before publication.
