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

The owner re-authorized the CPU-only homelab milestone on 2026-10-24. Work only on OPT-01, OPT-02, OPT-04, OPT-05, and OPT-06, using the approved full Formal Words and Conversation with Kob originals and existing publisher answers. Reference review is still incomplete. OPT-02/04/05 remain conditional on their documented evidence gates; OPT-03 GPU work stays cancelled. No deployment, GitHub Actions, model replacement, broad sweeps, or production claim is in scope.

The original audio and publisher references remain outside Git. `docs/formal-words/` contains a local copy for convenience, but Git ignores its MP4 and reference TXT. Both recordings have complete original source/reference pairs and unreviewed drafts under the external evaluation dataset and review directory. Exact file hashes and cue counts are recorded in the active spec and the current progress report. Earlier local runs and code checks do not substitute for reviewed references or homelab acceptance.

See the [active spec](../../.scratch/stt-optimization/spec.md#active-milestone-update-24-october-2026-owner-re-authorization), the [implementation handoff](../../.scratch/stt-optimization/review.md#implementation-handoff), and the [current progress report](../optimization-progress-20261024.md). Preserve every existing output and use fresh external destinations.

| Ticket | What to build | Blocked by | Status | Ready for agent |
| --- | --- | --- | --- | --- |
| [OPT-01](../../.scratch/stt-optimization/issues/01-two-recording-evaluation.md) | Reviewed references, controlled CPU baseline, and accurate CLI/API results | None | In progress | Yes; acceptance evidence is open |
| [OPT-02](../../.scratch/stt-optimization/issues/02-cpu-decoding-profiles.md) | At most two CPU profiles if evidence shows a need | OPT-01 | Blocked | No; await OPT-01 evidence or record N/A |
| [OPT-04](../../.scratch/stt-optimization/issues/04-batched-transcription.md) | One bounded batch check only if sequential is unsuitable | OPT-02 | Blocked | No; conditional on sequential evidence |
| [OPT-05](../../.scratch/stt-optimization/issues/05-language-vocabulary-hints.md) | At most one hint case for a reference-confirmed error | OPT-02 | Blocked | No; conditional on reviewed error |
| [OPT-06](../../.scratch/stt-optimization/issues/06-host-selection-service-acceptance.md) | Full two-recording CPU portfolio acceptance on i7-4770K | OPT-01 | In progress | Yes; target readiness and runs remain open |

The completed MVP and cancelled GPU experiment remain closed. Conditional tickets must end with their specified N/A evidence or completed acceptance; a blocked dependency is not completion.

Historical local run evidence remains in the [23 October optimization progress report](../optimization-progress-20261023.md). The latest read-only inventory confirms publisher references and drafts exist, but audio review remains 0/87 Formal Words cues and 0/290 Kob cues. No ticket is Complete from local code or fake-inference checks alone.

## API job progress extension

Owner-approved on 2026-10-18: add persisted `progress_percent` to the existing job
status endpoint. Status: Complete for the software extension. Progress increases
from zero to at most 99 while running; only successful result publication and the
success transaction set 100. Failures/interruption retain the last estimate, and
existing databases upgrade without losing jobs.

The [original verification report](../job-progress-verification-20261018.md) records
seven new generated/fake-inference regression cases and 120 passing ordinary tests.
The [real-model follow-up](../cpu-quality-progress-20261018.md) now records four
successful separate API/worker CPU invocations across both authorized full
originals and two profiles, including intermediate monotone progress and final
succeeded/100. Latest engineering checks are 127 ordinary passes, lint, format,
types and a completed six-file security diff review. Frontend integration remains
unexercised. No OPT acceptance gate is closed by these functional checks.

## Targeted CPU quality correction

Owner-directed on 2026-10-18 alongside real progress verification. Corrective
implementation and local experimental profile application: Complete. Reviewed
whole-recording accuracy acceptance remains pending under the existing OPT gates.
The local profile uses temperature zero, previous-text context on, a bounded
decoder no-repeat n-gram size of eight and VAD minimum silence 500 ms. Python
defaults and the approved baseline remain available unchanged at 2,000 ms VAD.

The [follow-up evidence](../cpu-quality-progress-20261018.md) preserves all three
trials and their raw private bundles. Kob replacement characters fell from four
to zero and unexpected-script letters from 38 to zero; the selected trial has
zero detector-flagged repeated motifs. Context-off was rejected for two long
repetitive spans. Residual spelling/name errors and unreviewed speech/timing remain
explicit; these diagnostics are not CER/WER or full optimization acceptance.

The owner's broader recognition-quality goal remains In progress. The completed
[CPU follow-ups](../cpu-large-v3-diagnostics-20261018.md) found no balanced model
profile that clearly fixes Kob: large-v3 retained more English but left key Thai
errors and was slow; the Thai-only candidate repeated text; Pathumma preserved
more code-switch terms but the tested INT8 conversion has no timestamps. The
official NECTEC NeMo checkpoint exposes timestamps and ran in 23.848 seconds on
this workstation when given 57 in-memory VAD chunks, but it retained the same key
Kob recognition errors; its unchunked pass took 512.106 seconds. Turbo beam ten
improved a few passages but left the glasses word wrong and increased Kob runtime
to about ten minutes. On full Kob API/worker runs, per-window multilingual and
forced-Thai modes produced exactly the same 322 segment texts as baseline. A generic
bilingual prompt caused severe repetition, so it was rejected. `.env.local`
currently selects Turbo with beam five, CPU INT8, temperature zero, context on,
n-gram size eight and VAD 500 ms for local evaluation; Python defaults and the
approved baseline remain unchanged. Progress is verified through the actual
API/worker with real CPU inference. No test was run on the owner's GPU-free home
server. A `Kob` hotword caused severe repetition. VAD minimum silence 500 ms
reduced malformed fragments in selected Kob passages and passed a Formal check,
but did not fix the glasses word and changed text substantially. Trial 15 tested
context off with n-gram 8 and VAD 500 ms: it passed with monotone progress but
still misheard the glasses term and weakened English `flow` rendering, so it was
not promoted. A repeated full Kob API/worker run with VAD 500 ms then reproduced
all 320 segments and TXT/SRT byte for byte, with monotone progress through
succeeded/100; this verifies stability, not recognition accuracy. Human review of the publisher
references is still needed before accuracy claims. Beam 1 and 3 were also tested
on full Kob through the real API/worker. Beam 1 remained wrong on the glasses
word; beam 3 fragmented the `flow` phrase, so beam 5 stays selected. The existing
two-original allowlist remained in effect when these trials were recorded. The
2026-10-23 homelab scope update supersedes the GPU and two-host acceptance gates.
A short candidate-vocabulary prompt also failed to correct the glasses/polyglot terms and weakened `flow`, so
the local profile remains prompt-free.

## Updating status

Use Planned, Blocked, In progress, Complete, or Cancelled. Cancelled means the owner removed the work from scope; keep the ticket as a historical record. Keep conditional tickets Blocked until evidence establishes whether their trigger occurred. When a ticket has alternative acceptance branches, mark the unused branch N/A and cite the evidence that makes it inapplicable. Do not use N/A when required evidence is missing. Ready for agent means approved scope, sufficient acceptance criteria, and every blocker complete; it does not mean implemented or verified. Keep this table and each ticket's metadata consistent. Mark a ticket Complete only when each acceptance criterion has passed or has an evidence-backed N/A disposition, required checks pass, and material limitations are recorded. Record the actual validation command, outcome, and evidence location in that ticket; never substitute a planned check for a passing result. Preserve private evidence under external storage and link only sanitized summaries from versioned documentation.

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
