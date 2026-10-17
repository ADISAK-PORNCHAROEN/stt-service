# 06: Select host configurations and verify persistent-service delivery

What to build: The owner receives host-specific, evidence-backed configuration decisions, complete results through the persistent service, and a documented way to return to the baseline, with unmet objectives clearly identified.
Blocked by: 03 - Explicit GPU transcription; 04 - Batched transcription comparison; 05 - Language/vocabulary comparison.
Status: Blocked.
Ready for agent: No; approved; waiting for tickets 03, 04, and 05.
Triage label: ready-for-agent.

## Problem

Individual experiments do not establish that their combination is useful, that service clients receive the same behavior, or that a home-server CPU result can be inferred from development-host measurements.

## Solution

Freeze finalist configurations from the completed evidence, measure them on each target host against its own baseline, and verify the existing CLI/API/worker workflow with the selected configuration. Publish sanitized acceptance evidence and retain explicit baseline selection.

## User stories

1. As the owner, I want a configuration decision for each host, so that the service uses settings supported by that host's evidence.
2. As the client, I want complete consistent results through CLI and HTTP, so that selected optimizations work in the delivered workflow.
3. As the operator, I want baseline recovery and visible failed-target outcomes, so that missing evidence cannot cause an unsupported default change.

## Implementation decisions

Combine device/precision, beam/thread, batching, and language/context/hint choices only after their isolated outcomes are available. Re-measure combined finalists rather than multiplying individual reported speedups. Keep startup selection explicit, maintain one persistent engine/worker, and avoid silent fallback.

Use Formal Words and Conversation with Kob only, with no new derived media. Freeze settings before final evaluation and disclose any consumed holdout. Obtain at least three isolated warm full-call measurements per original for baseline/finalists on each accepted host, plus separate cold startup evidence. The real-time objective is full-call RTFx at least one for each original; sub-target improvements remain visibly below target.

Apply the specification's per-language and important-error gates on reviewed coverage and assess subtitle timing. A passing implementation test does not substitute for human reference review. If no candidate meets speed/quality criteria, retain the baseline and report the failed objective; do not make up a passing configuration. Home-server acceptance remains pending until measured there.

## Testing

Use the existing CLI and public HTTP submission/polling/download flow with fake inference, real SQLite/filesystem state, and separate worker behavior to verify configuration propagation, readiness, reuse, errors, and complete bundles. Follow existing lifecycle, scheduling, publication, retention, and source-time prior art where configuration changes affect them.

Opt-in separate-process real-model CLI and HTTP checks must validate recording identity before using either authorized original; inherited media environment settings cannot broaden the allowlist. Preserve inputs and every existing result destination.

## Acceptance criteria

- [ ] Frozen finalists or a documented baseline-retention decision are selected from combined measurements rather than assumed additive speedups.
- [ ] Development-host GPU and home-server CPU each have actual same-host baseline/finalist evidence for both authorized originals, including repeated warm full-call timing, cold loading, resolved settings/revision, resource observations, and reviewed text/timing results.
- [ ] Reports identify real-time target achievement per recording, reject quality regressions, disclose unknown groups/coverage and holdout limitations, and distinguish equal-quality speedups from observed quality improvement.
- [ ] Selected startup configuration propagates through CLI and the persistent API/worker workflow, preserves one model instance, and produces matching canonical JSON/TXT/SRT behavior with original recording times.
- [ ] Readiness, failed inference/resource cases, job isolation, queue/recovery/retention behavior, immutable publication, and source/output ownership remain correct under applicable configuration changes.
- [ ] Baseline selection/recovery and compatible runtime setup are documented, including explicit failure behavior and host-specific limits.
- [ ] Required ordinary/public behavior checks, opted-in two-recording acceptance, lint/format/types, and sanitized evidence are recorded with actual outcomes. Missing host access, unsupported runtime, or unreviewed quality remains pending rather than a completed acceptance claim.

## Out of scope

Any additional real input or derived test media; model/backend replacement; selective second-pass implementation; new endpoints; changing completed MVP or cancelled experiment statuses; broad English-only/noise/generalization claims.

## Further notes

Individual capability tickets can complete with a fully evidenced useful or unsuccessful experiment, but this final ticket cannot be marked Complete while its required two-host or reviewed-quality acceptance remains unperformed. Performance-target failure is a reportable outcome, not permission to lower the target or relax a quality gate. Validation evidence: Pending implementation.
