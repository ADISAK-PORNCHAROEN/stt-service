# 04 — Deliver TXT and SRT through the result endpoint

What to build: HTTP access to the same completed text/subtitle artifacts as the CLI.
Blocked by: 02, 03.
Status: Blocked.
Ready for agent: No; tickets 02 and 03 must both be complete.

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

- [ ] Result requests support JSON/TXT/SRT with the specified default and response semantics.
- [ ] CLI and API share canonical exporters and consistent output.
- [ ] Fetching any number of formats does not rerun inference.
- [ ] Export failure prevents success and partial publication.
- [ ] HTTP seam checks and required lint/format/type checks pass with evidence.

## Out of scope

New export formats, regenerated transcripts, UI, retention, and alternate engines.

## Further notes

Ticket 06 requires this ticket and ticket 05. Results remain model-timed rather than manually aligned.

Validation evidence: Pending implementation.
