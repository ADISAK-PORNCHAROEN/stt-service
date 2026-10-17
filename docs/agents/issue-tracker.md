# Local MVP issue tracker

This file tracks implementation work locally. Read the [specification](../../.scratch/stt-mvp/spec.md), [architecture](../../.scratch/stt-mvp/architecture.md), and [CONTEXT](../../CONTEXT.md) before changing behavior. Runtime implementation is present; delivery status below reflects actual evidence in the [verification report](../verification-20261017.md), not merely code existence.

| Ticket | What to build | Blocked by | Status | Ready for agent |
| --- | --- | --- | --- | --- |
| [01](../../.scratch/stt-mvp/issues/01-cli-json.md) | CLI and reusable JSON pipeline | None | Complete | Done |
| [02](../../.scratch/stt-mvp/issues/02-exports-benchmark.md) | TXT/SRT and measured baseline | 01 | Complete | Owner accepted two phrase-level samples; broader-review gap recorded |
| [03](../../.scratch/stt-mvp/issues/03-api-worker-json.md) | Local API, SQLite queue, persistent worker, JSON | 01 | Complete | Done |
| [04](../../.scratch/stt-mvp/issues/04-api-exports.md) | TXT/SRT result delivery over HTTP | 02, 03 | Complete | Done |
| [05](../../.scratch/stt-mvp/issues/05-validation-recovery.md) | Validation, queue admission, restart hardening | 03 | Complete | Done |
| [06](../../.scratch/stt-mvp/issues/06-retention-acceptance.md) | Retention and full acceptance evidence | 04, 05 | Complete | Owner accepted closure; full-recording review gap recorded |

After 01, 02 and 03 may proceed independently. After 03, 05 may proceed alongside remaining export work. Accept/close 04 only after both 02 and 03 pass; accept/close 06 only after both 04 and 05 pass.

## Qwen3-ASR experiment (cancelled)

The separate `QW-*` namespace is retained only as a historical record. The original MVP tickets 01–06 and their status above are unchanged. The user cancelled Qwen after CPU inference proved impractical; Whisper remains the supported engine.

| Ticket | What to build | Blocked by | Status | Ready for agent |
| --- | --- | --- | --- | --- |
| [QW-01](../../.scratch/qwen3-asr/issues/01-text-only-transcripts.md) | Text-only transcript behavior through CLI exports | None | Cancelled | No — cancelled |
| [QW-02](../../.scratch/qwen3-asr/issues/02-qwen-engine-and-model-setup.md) | Qwen adapter, selection, and explicit model preparation | QW-01 | Cancelled | No — cancelled |
| [QW-03](../../.scratch/qwen3-asr/issues/03-qwen-whisper-evaluation.md) | Reproducible Qwen/Whisper speech and music evaluation | QW-02 | Cancelled | No — cancelled |

These tickets are not actionable. See the cancelled [Qwen3-ASR spec](../../.scratch/qwen3-asr/spec.md) and withdrawn [runtime ADR](../adr/0001-qwen3-asr-runtime.md) for the historical plan.

## Whisper Turbo optimization

The owner approved the [specification](../../.scratch/stt-optimization/spec.md), [test seams and ticket breakdown](../../.scratch/stt-optimization/review.md), and instructed implementation. All six tickets carry the ready-for-agent triage label; start eligibility still requires completed blockers. Only Formal Words and Conversation with Kob are authorized real-recording inputs.

The owner's Kob quality follow-up is incorporated into the existing specification and six tickets: reviewed/offline scoring, immutable profiles, truthful language/fallback evidence, GPU/batch compatibility, and consecutive-job isolation. The [research](../research/stt-quality-performance-followup-20261018.md) and [structure proposal](../research/stt-quality-performance-architecture-20261018.md) explain the additions. A software implementation pass now covers those contracts across all six slices; its 110 passing ordinary checks do not satisfy real-recording, human-review, GPU-inference, host, or per-ticket experiment gates. The dependency/status table below remains authoritative.

The [implementation handoff](../../.scratch/stt-optimization/review.md#implementation-handoff) identifies the fixes/additions and independently verifiable deliverable for every ticket. Current code/evidence status and remaining acceptance gates are recorded in the [optimization verification report](../optimization-verification-20261018.md) and each linked ticket. Implementation progress across OPT-02–OPT-06 does not bypass their experiment dependencies.

| Ticket | What to build | Blocked by | Status | Ready for agent |
| --- | --- | --- | --- | --- |
| [OPT-01](../../.scratch/stt-optimization/issues/01-two-recording-evaluation.md) | Guarded two-recording evaluation and controlled CPU baseline | None | In progress | Yes; implementation started |
| [OPT-02](../../.scratch/stt-optimization/issues/02-cpu-decoding-profiles.md) | Configurable CPU decoding and actual settings in result bundles | OPT-01 | Blocked | No; waiting for OPT-01 |
| [OPT-03](../../.scratch/stt-optimization/issues/03-gpu-transcription.md) | Explicit GPU transcription and same-host comparison | OPT-02 | Blocked | No; waiting for OPT-02 |
| [OPT-04](../../.scratch/stt-optimization/issues/04-batched-transcription.md) | Batched transcription with reviewed text/timing differences | OPT-02 | Blocked | No; waiting for OPT-02 |
| [OPT-05](../../.scratch/stt-optimization/issues/05-language-vocabulary-hints.md) | Controlled language/context/vocabulary comparisons | OPT-02 | Blocked | No; waiting for OPT-02 |
| [OPT-06](../../.scratch/stt-optimization/issues/06-host-selection-service-acceptance.md) | Host-specific choices and persistent-service acceptance | OPT-03, OPT-04, OPT-05 | Blocked | No; waiting for OPT-03, OPT-04, OPT-05 |

The completed MVP and cancelled-experiment dispositions above remain historical acceptance records. No optimization acceptance is inferred from them.

## Updating status

Use Planned, Blocked, In progress, or Complete. Ready for agent means approved scope, sufficient acceptance criteria, and every blocker complete; it does not mean implemented or verified. Keep this table and each ticket's metadata consistent. Mark a ticket Complete only when all acceptance checkboxes have evidence, required checks pass, and material limitations are recorded. Record the actual validation command, outcome, and evidence location in that ticket; never substitute a planned check for a passing result. Preserve private evidence under external storage and link only sanitized summaries from versioned documentation.

## Local ticket template

```markdown
# NN — Title

What to build: Observable capability.
Blocked by: Ticket numbers or None.
Status: Planned or Blocked.
Ready for agent: Yes or No, with dependency reason.

## Problem

## Solution

## User stories

## Implementation decisions

Describe contracts and responsibilities without prescribing source paths or code.

## Testing

List meaningful checks and required evidence; indicate that execution is pending.

## Acceptance criteria

- [ ] Observable outcome with evidence.

## Out of scope

## Further notes

Validation evidence: Pending implementation.
```
