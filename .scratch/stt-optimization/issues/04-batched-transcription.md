# 04: Compare batched transcription while preserving text and timing

What to build: An operator can explicitly compare sequential and batched Turbo transcription through the same public workflow and inspect complete result bundles, timing/resource costs, and reviewed text/timestamp differences.
Blocked by: 02 - Compare configurable CPU decoding through complete result bundles.
Status: Blocked.
Ready for agent: No; approved; waiting for ticket 02.
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

Screen on Formal Words, freeze candidate settings, and evaluate Conversation with Kob without using its reference to tune the candidate. Measure complete results and memory, not just model-call return. A CPU batch comparison does not require GPU implementation; combined GPU batching is evaluated after both capabilities are available.

## Testing

Prefer public CLI/evaluation cases with fake inference for mode metadata, valid segment contracts, silent/empty output, memory/error publication behavior, and deterministic exports. Reuse existing contract cases for source offsets, discontinuous timelines, resampling tails, VAD silence, and rounding. Real batch measurements use only the two authorized full originals.

## Acceptance criteria

- [ ] Explicit sequential/batched selection and supported batch sizes produce complete canonical JSON/TXT/SRT bundles through the public workflow.
- [ ] Metadata discloses actual batching, context, timestamp, language, VAD, and fallback semantics, including unsupported options rather than pretending they took effect.
- [ ] Segment ordering, finite bounds, original offsets/gaps, and exported subtitle times satisfy the existing source-timeline contract without double restoration or invented alignment.
- [ ] Controlled CPU results include the sequential path, batch-one control, and batch-two/four cases or explicit resource-failure evidence, with reviewed speech coverage, repetition/omission checks, full-call timing, and peak RAM.
- [ ] Failed/unsupported/resource-exhausted candidates preserve sources and prior outputs and cannot publish success or silently change mode/batch size.
- [ ] Appropriate fake-engine public behavior and configured quality checks pass, with commands/evidence recorded; beneficial or unsuccessful batch outcomes are both reported honestly.

## Out of scope

Any additional real recording or derived media; unrestricted automatic batching; per-job HTTP options; model/backend changes; assuming GPU capability is required for this CPU slice.

## Further notes

Ticket 06 can compare GPU batching once tickets 03 and 04 are both complete. This ticket must not claim equivalent sequential quality based on identical argument names. Validation evidence: Pending implementation.
