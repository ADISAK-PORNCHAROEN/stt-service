# 04: Compare batched transcription while preserving text and timing

What to build: Only if the homelab CPU INT8 sequential baseline is unsuitable for the stated portfolio workflow, test one bounded batched profile and compare it with sequential results.
Blocked by: 02 - Compare configurable CPU decoding through complete result bundles.
Status: Blocked.
Ready for agent: No; wait for OPT-02 and the sequential homelab evidence. Record N/A if sequential is suitable.
Triage label: ready-for-agent.

## Problem

Batching may improve CPU use, but the pinned implementation changes context, fallback, and timestamp behavior. A faster result is not acceptable if speech disappears, subtitles shift, or the report falsely describes equivalent decoding.

## Solution

Add a selected batched mode behind the existing inference boundary, return the same canonical segment/result contract, record its effective semantics, and compare controlled CPU cases through guarded evaluation.

## User stories

1. As the operator, I want batch size selected explicitly, so that speed and memory use can be reproduced.
2. As the reviewer, I want sequential and batched decoding differences disclosed, so that an algorithm change is not presented as a hardware-only gain.
3. As the subtitle user, I want original recording timestamps retained, so that faster processing still yields usable subtitles.

## Implementation decisions

Use the same Turbo model boundary, canonical transcript, exporters, and startup-configuration contract. Compare sequential inference to the batched path with batch one as a path control, followed by batch two/four. Keep explicit baseline settings where the batched implementation supports them and record ignored or changed semantics truthfully. Require segment timestamps compatible with original-source mapping.

Resolve effective VAD options explicitly: the pinned sequential and batched defaults use different silence thresholds, context, fallback, and timestamp behavior. Materialize fresh VAD arguments per call to avoid dictionary mutation. Keep the 30-second model window fixed, explicitly request segment timestamps, and retain disabled word timestamps. The current implementation rejects batched/VAD-off profiles during startup resolution; support that combination only after the adapter can supply and verify full-file clip timestamps. The pinned API lacks the sequential full-file clip default for recordings of 30 seconds or longer. Compare cross-job behavior as well as a single successful bundle.

Do not sweep batch sizes. If sequential is unsuitable, select one supported CPU batch configuration tied to the observed bottleneck, test it once per authorized original, and compare complete output, reviewed speech/timing, and memory. Keep Kob as final non-regression evidence and do not use its reference text to select a profile. No GPU or second candidate is in scope.

## Testing

Prefer public CLI/evaluation cases with fake inference for mode metadata, valid segment contracts, silent/empty output, memory/error publication behavior, and deterministic exports. Reuse existing contract cases for source offsets, discontinuous timelines, resampling tails, VAD silence, and rounding. Real batch measurements use only the two authorized full originals.

## Acceptance criteria

- [ ] Explicit sequential/batched selection and supported batch sizes produce complete canonical JSON/TXT/SRT bundles through the public workflow.
- [ ] Metadata discloses actual batching, context, timestamp, language, VAD, and fallback semantics, including unsupported options rather than pretending they took effect.
- [ ] Explicit VAD/window/timestamp behavior and repeated-call argument isolation are verified; a batch-one control exposes path differences, and quiet-speech/boundary omissions are reviewed before increasing batch size.
- [x] Batched profiles with VAD disabled fail during profile resolution until the implementation can provide verified full-file clip timestamps; fake profile tests cover this guard.
- [ ] Segment ordering, finite bounds, original offsets/gaps, and exported subtitle times satisfy the existing source-timeline contract without double restoration or invented alignment.
- [ ] If the trigger is met, one bounded batch candidate is compared to sequential with reviewed speech coverage, repetition/omission checks, full-call timing, and peak RAM; if not, record N/A with sequential evidence.
- [ ] Failed/unsupported/resource-exhausted candidates preserve sources and prior outputs and cannot publish success or silently change mode/batch size.
- [x] Fake sequential/batched adapter and profile checks pass; full ordinary suite, lint, formatting, and types pass, with commands in the [implementation evidence](../../../docs/optimization-verification-20261018.md). No real batch experiment or quality/timing outcome is claimed.

## Out of scope

Any additional real recording or derived media; batch-size sweep; more than one batch candidate; unrestricted automatic batching; per-job HTTP options; model/backend changes; GPU.

## Further notes

Explicit sequential/batched execution, effective semantic reporting, fresh per-call VAD arguments, and comparison reporting are implemented. No batch-one/two/four real recordings or reviewed timing/text outcomes have been produced. Ticket 06 may compare GPU batching only after tickets 03 and 04 acceptance. See [implementation evidence](../../../docs/optimization-verification-20261018.md).
