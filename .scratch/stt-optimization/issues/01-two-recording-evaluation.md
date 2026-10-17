# 01: Prepare the two-recording evaluation and controlled CPU baseline

What to build: An operator can explicitly evaluate Formal Words and Conversation with Kob against their matching reviewed references and obtain a reproducible controlled CPU baseline, with source restrictions checked before processing.
Blocked by: None.
Status: In progress.
Ready for agent: Yes; approved and implementation started.
Triage label: ready-for-agent.

## Problem

Current source downloads include publisher material that is not yet a reviewed speech reference. Existing timing was not isolated, and ordinary discovery must not broaden this evaluation beyond the two authorized originals.

## Solution

Provide an explicit manifest-based evaluation at the existing benchmark/CLI boundary. Validate the two source identities and hashes before loading inference or processing media, preserve source references, prepare separately reviewed spoken text, and report actual coverage and baseline measurements.

## User stories

1. As the operator, I want unknown inputs rejected before processing, so that only authorized recordings can be tested.
2. As the reviewer, I want publisher text distinguished from reviewed speech, so that translations and romanization cannot contaminate scores.
3. As the maintainer, I want a controlled baseline with timing and quality evidence, so that later candidates can be compared fairly.

## Implementation decisions

Use the existing public benchmark workflow, shared pipeline, injected engine seam, and external storage. Do not create a second inference implementation. The approved originals are Formal Words and Conversation with Kob; the specification owns their immutable source identities and hashes. Keep raw media/references, corrections, run outputs, and private reports outside Git.

The complete real-recording test inventory is Formal Words (approximately 4:42, matching original TXT) and Conversation with Kob (approximately 9:58, matching original SRT). No other recording may be tested without a new explicit owner authorization. This restriction applies to every dependent optimization ticket, including benchmarks and real-model integration checks.

The proposed tuning recording is Formal Words and proposed final-evaluation recording is Conversation with Kob. Freeze scoring/normalization and record scored coverage. Do not expose final-evaluation error details to vocabulary or setting selection. Freeze Thai/English language-assignment rules before reporting CER/WER; if a reference or required group cannot be reviewed, report quality acceptance pending.

## Testing

Use public CLI/evaluation behavior with fake inference, inert denied inputs, tiny generated correctness fixtures, and real filesystem interactions. Check rejection before engine construction, deterministic hand-authored scoring cases, source preservation, complete bundles, and failed-run visibility. Real measurements use only the two authorized full originals and new destinations.

## Acceptance criteria

- [x] Evaluation accepts only the two manifest-approved identities with matching source hashes; unknown, duplicate, replaced, or implicitly discovered inputs fail before media processing or inference. Public CLI guard and canonical-source binding regressions pass.
- [ ] Matching publisher TXT/SRT originals are preserved, and separate reviewed references remove translations/romanization while preserving actual English speech and documenting uncertain spans and corrections.
- [ ] Normalization, language-assignment/tokenization, important-error categories, reviewed timing boundaries, and scored coverage are documented before comparisons; unreviewed material cannot produce an accuracy pass.
- [x] The agreed tuning/final-evaluation allocation is recorded without claiming independent-speaker coverage.
- [ ] The current Turbo CPU INT8/four-thread/beam-five configuration yields complete canonical JSON/TXT/SRT bundles for both originals and a development-host baseline with cold full-call timing plus at least three isolated warm measurements per recording, median/range, full-call RTFx, revision/settings, and peak RSS.
- [ ] Evidence distinguishes compatibility, speed, text accuracy, and timing review, and records the limits of English-only and noise coverage.
- [x] Relevant fake-inference checks and configured implementation-quality checks pass; 95 ordinary checks pass, with Ruff lint/format and mypy passing. Actual commands and scoped review outcomes are recorded in the linked progress evidence; this does not complete real-model or human acceptance.

## Out of scope

Any real input beyond the two positive-allowlist originals; derived test media; extra downloads; GPU or changed decoding; service rollout; treating publisher subtitles as already reviewed.

## Further notes

This is the evaluation contract consumed by subsequent candidate tickets. If human review is not available, timing evidence may be gathered but this ticket cannot be marked Complete with quality criteria unmet. Validation evidence: [implementation progress and review follow-up](../../../docs/optimization-verification-20261018.md). Guarded evaluation/reference preparation, review fixes, and ordinary checks are implemented. Formal Words has four complete bundles and exploratory timing; unrelated CPU activity prevents idle-host baseline acceptance. Conversation with Kob has four complete exploratory bundles: cold 1,033.993 seconds, warm 1,164.670/1,196.164/1,086.004 seconds, warm median 1,164.670 seconds, and median full-call RTFx 0.513. The run did not meet real-time performance and its system CPU counters show substantial activity; human quality acceptance and controlled idle-host evidence remain pending. Full specification and review package are available from the feature index.
