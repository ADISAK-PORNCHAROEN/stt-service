# Local MVP issue tracker

This file tracks implementation work locally. Read the [specification](../../.scratch/stt-mvp/spec.md), [architecture](../../.scratch/stt-mvp/architecture.md), and [CONTEXT](../../CONTEXT.md) before changing behavior. Runtime implementation is present; delivery status below reflects actual evidence in the [verification report](../verification-20261017.md), not merely code existence.

| Ticket | What to build | Blocked by | Status | Ready for agent |
| --- | --- | --- | --- | --- |
| [01](../../.scratch/stt-mvp/issues/01-cli-json.md) | CLI and reusable JSON pipeline | None | Complete | Done |
| [02](../../.scratch/stt-mvp/issues/02-exports-benchmark.md) | TXT/SRT and measured baseline | 01 | Complete | Owner accepted two phrase-level samples; broader-review gap recorded |
| [03](../../.scratch/stt-mvp/issues/03-api-worker-json.md) | Local API, SQLite queue, persistent worker, JSON | 01 | Complete | Done |
| [04](../../.scratch/stt-mvp/issues/04-api-exports.md) | TXT/SRT result delivery over HTTP | 02, 03 | Complete | Done |
| [05](../../.scratch/stt-mvp/issues/05-validation-recovery.md) | Validation, queue admission, restart hardening | 03 | Complete | Done |
| [06](../../.scratch/stt-mvp/issues/06-retention-acceptance.md) | Retention and full acceptance evidence | 04, 05 | Blocked | Runtime verified; awaits full-recording owner review |

After 01, 02 and 03 may proceed independently. After 03, 05 may proceed alongside remaining export work. Accept/close 04 only after both 02 and 03 pass; accept/close 06 only after both 04 and 05 pass.

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
