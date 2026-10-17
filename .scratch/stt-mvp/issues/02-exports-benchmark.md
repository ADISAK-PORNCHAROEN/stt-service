# 02 — Add TXT/SRT exports and measure the baseline

What to build: Derived text/subtitle artifacts and a reproducible real-recording baseline.
Blocked by: 01.
Status: Complete.
Ready for agent: Done; owner accepted two phrase-level examples with the broader-review gap disclosed.

Triage label: ready-for-agent

## Problem

Canonical JSON needs useful reading/subtitle formats. The chosen CPU baseline also needs actual timing, memory, and manual quality observations before anyone can assess its suitability.

## Solution

Derive TXT and SRT from the canonical transcript and include them in atomic CLI publication. Measure the supplied MP4 in cold and warm conditions, keeping private artifacts outside the repository and recording a sanitized methodology and findings.

## User stories

- As a reviewer, I can obtain readable Thai/English text and correctly numbered subtitles for the same transcript without another inference run. Segment offsets remain aligned to the original recording, including through silence and at millisecond/hour rounding boundaries.
- As an operator, I can distinguish model loading from inference and complete output time, compare a fresh-process run with reuse of a loaded model, and inspect actual text and timing issues. I can reproduce the conditions without treating another machine's claims as measurements on this hardware.

## Implementation decisions

Use JSON as the only source for exporters; deterministic formatting preserves UTF-8. Complete JSON/TXT/SRT before publishing the bundle. Use the [spec benchmark protocol](../spec.md#testing-and-acceptance). Remeasure the supplied recording's approximate 400.684-second duration and 18.3 MiB size. Identify hardware, versions/model revision, settings, cache/download conditions, timing boundaries, and peak RAM method.

Report load time, inference, total publication time, and both defined RTFx denominators. A warm measurement must reuse a loaded engine within a process; it may use an evaluation harness before the service worker exists. Distinguish download time from cold model load. Manually inspect Thai/English text, names, numbers, silence, and segment boundaries. Report observations without inventing an accuracy threshold or claiming home-server performance.

## Testing

Use fake-engine public CLI checks for all artifacts, exporter failures and atomicity, Thai text, empty transcripts, cue sequencing, and timestamp rounding. Verify exports do not invoke inference again. Run ordinary checks and perform explicitly opted-in real measurements. CER/WER are permitted only with reviewed ground truth and documented normalization/tokenization.

## Acceptance criteria

- [x] Completed CLI bundles include JSON, TXT, and SRT generated from one transcript.
- [x] Deterministic UTF-8 exports, empty output, rounding, and original offsets are verified.
- [x] Export failures cannot expose a partial published bundle.
- [x] Cold/warm methodology and actual load/inference/total/RTFx/peak-RAM observations are recorded.
- [x] Two user-reviewed phrase corrections and their model-derived timing limitations are recorded without raw transcript in Git.
- [x] Owner-directed closure records the two phrase-level text corrections, defers full-recording text/timing review explicitly, and makes no CER/WER or overall accuracy claim.
- [x] Appropriate ordinary checks pass; private media, transcripts, and raw reports remain external.

## Out of scope

HTTP delivery, alternative models, ground-truth creation as a prerequisite, and performance optimization beyond establishing the baseline.

## Further notes

Ticket 04 consumes these exporters. Owner decision (2026-10-17): close this ticket based on the completed exports/benchmark and two user-reviewed phrase corrections, with the remaining full-recording review gap explicitly retained. This limited-sample acceptance does not mean all Thai/English text, names, numbers, silence, boundaries, or original offsets were reviewed.

Validation evidence: [Engineering verification](../../../docs/verification-20261017.md) and [baseline measurements](../../../benchmarks/reports/20261017-turbo-cpu.md). Cold/warm run completed on the supplied MP4; final implementation paths received separate short real-model integration checks. Ticket closed at the owner's direction with two user-reviewed phrase corrections; exact timing and broader listening review remain unverified, so no overall transcription-quality claim is made.
