# 04 — Deliver TXT and SRT through the result endpoint

What to build: HTTP access to the same completed text/subtitle artifacts as the CLI.
Blocked by: 02, 03.
Status: In progress.
Ready for agent: Implementation present; measurement/quality acceptance remains open.

Triage label: ready-for-agent

## Problem

Service clients need reading and subtitle formats without a separate transcription or a second formatting implementation.

## Solution

Connect the existing canonical exporters to service result bundles and support JSON, TXT, and SRT through the approved format selector.

## User stories

- As a local client, I can request a succeeded job's JSON, TXT, or SRT and receive the matching completed artifact with an appropriate media type. Changing format does not consume another inference run or change the transcript.
- As a reviewer, I can compare CLI and API artifacts from the same canonical transcript and obtain consistent Thai/English text, cue ordering, and original recording offsets. Requests made before success or with an invalid format produce the documented errors instead of partial content.

## Implementation decisions

Reuse the exporters from ticket 02 and the [HTTP contract](../spec.md#http-contract). JSON is the default format. Prepare all enabled outputs before the service publishes the result directory and records success. Serve only completed artifacts referenced by succeeded jobs; never derive a second transcript to satisfy a download.

## Testing

Use httpx and a counting fake engine to verify all three formats, content types/encoding, default format, invalid selector, pending/failed/unknown jobs, Thai text, empty speech, and matching CLI/API formatting. Inject export failure and confirm no successful partial bundle. Run ordinary and static checks.

## Acceptance criteria

- [x] Result requests support JSON/TXT/SRT with the specified default and response semantics.
- [x] CLI and API share canonical exporters and consistent output.
- [x] Fetching any number of formats does not rerun inference.
- [x] Export failure prevents success and partial publication.
- [x] HTTP seam checks and required lint/format/type checks pass with evidence.

## Out of scope

New export formats, regenerated transcripts, UI, retention, and alternate engines.

## Further notes

Ticket 06 requires this ticket and ticket 05. Results remain model-timed rather than manually aligned.

Validation evidence: [Engineering verification](../../../docs/verification-20261017.md) and [baseline measurements](../../../benchmarks/reports/20261017-turbo-cpu.md). JSON/TXT/SRT delivery through the API and actual separate API/worker processes are verified. Cold/warm CPU measurements are recorded; this ticket remains open until its benchmark dependency 02 completes human review.
