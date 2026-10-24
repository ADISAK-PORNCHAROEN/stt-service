# 02: Compare configurable CPU decoding through complete result bundles

What to build: If OPT-01 evidence shows a concrete speed, memory, or reviewed-error need, compare no more than two CPU candidate profiles against the CPU INT8 baseline on the i7-4770K.
Blocked by: 01 - Prepare the two-recording evaluation and controlled CPU baseline.
Status: Blocked.
Ready for agent: No; await the OPT-01 baseline and reviewed-reference findings. Record N/A if neither trigger exists.
Triage label: ready-for-agent.

## Problem

Decoding is currently fixed at beam five and reported settings are hard-coded. A parameter experiment is not reproducible if runtime behavior, metadata, and the persistent worker disagree.

## Solution

Carry validated CPU candidate settings from shared startup configuration through actual inference, canonical result metadata, and benchmark comparison. Retain the existing default and source/output protections. Include the necessary narrow configuration/reporting prefactoring within this end-to-end slice.

## User stories

1. As the operator, I want a selected CPU configuration to determine actual decoding, so that its measured outcome is reproducible.
2. As the reviewer, I want resolved settings in JSON, so that a report cannot claim an option the engine ignored.
3. As the service operator, I want the same startup settings respected by the persistent worker, so that CLI candidates have a consistent delivery path.

## Implementation decisions

Use the existing settings, CLI/shared pipeline, and engine-factory seam. Configuration reporting must come from resolved inference behavior and remain compatible with the canonical transcript. Keep new reporting additive. Capture available evaluation diagnostics externally without presenting them as correctness probabilities.

Resolve one immutable profile at startup and carry segments plus effective engine metadata through the existing seam. Include this narrow prefactoring inside the complete configuration/result slice. Build fresh upstream arguments for every call, keep the model window fixed at 30 seconds, and distinguish requested/effective precision and forced/detected language. Preserve private hints/logs externally. Engine-reported temperature does not count fallback attempts; unavailable attempt counts remain explicit rather than estimated from the last temperature.

Give the resolved profile a stable versioned identity. Store each recording's detected language and other observations in its result, without changing that profile identity. An explicit experiment plan and per-run record bind the selected profile, actual settings, model/runtime identity, source role, output bundle, and applicable scoring-policy/reference revision. Use the same pipeline for CLI and worker; no generic profile registry or parallel inference stack is required.

Do not run a parameter matrix. After OPT-01, run at most two candidate profiles total, one at a time, changing only settings directly tied to a demonstrated problem. Keep device CPU, compute INT8, model, language/VAD/context/fallback settings at baseline unless the candidate specifically tests one of those settings. Use Formal Words for selection and Kob for a non-regression check; never use Kob reference text to select the candidate. No setting change justifies silent fallback or an overwrite of prior outputs. If the baseline meets the stated local/portfolio need and reviewed quality has no concrete error requiring tuning, write an N/A disposition and do not run candidates.

## Testing

Exercise public transcription and benchmark commands using injected engines, generated fixtures, real files, and observable complete bundles. Check invalid settings, actual metadata, model reuse, and recovery of the default. Follow existing CLI, output-publication, and source-timeline contract prior art. Actual experiments remain restricted to the two originals.

## Acceptance criteria

- [ ] Validated CPU beam/thread selections reach inference through the public CLI and shared worker startup configuration; invalid settings fail clearly before processing.
- [ ] Existing default behavior is reproducible, and result configuration reports actual resolved settings/model revision with no hard-coded contradictory metadata.
- [ ] Each candidate produces one consistent canonical JSON/TXT/SRT bundle without another inference for exporters; original source timeline, output ownership, and atomic publication are preserved.
- [ ] Run no more than two evidence-justified candidate profiles, one at a time; otherwise record N/A with the baseline and reference evidence that show no trigger.
- [ ] Any candidate comparison changes only the targeted factor, freezes settings before final evaluation, and records time/resource costs plus reviewed Thai/English/important-error outcomes.
- [ ] External diagnostics distinguish observed settings and decode behavior from an uncalibrated confidence estimate.
- [ ] Returned engine evidence drives published effective configuration; immutable profiles and fresh per-call arguments prevent cross-job state changes, including after a failed job.
- [ ] CLI, benchmark/evaluation, and worker results identify the same resolved startup profile; different per-file observations do not mutate that profile or trigger an unnecessary model reload. Reproducible experiment/run records bind profiles and output bundles to their actual execution evidence.
- [ ] Evaluation records actual language-source policy, available VAD/temperature observations, per-run canonical-text hashes/differences, and observed broad stage timing. Forced-language probability is not reported as measured detection confidence; unobserved retry counts/timing remain unavailable.
- [ ] Operator-visible reports identify beneficial, regressing, or inconclusive candidates without automatically replacing the baseline.
- [x] Profile/engine and worker-isolation fake-inference checks pass; full ordinary suite, lint, formatting, and types pass with commands recorded in the [implementation evidence](../../../docs/optimization-verification-20261018.md). Controlled CPU candidate comparisons remain pending.

## Out of scope

Other real recordings or derived test media; GPU; more than two CPU candidates; broad sweeps; batched decoding; language or vocabulary changes; extra HTTP tuning endpoints; automatically selecting a final service default.

## Further notes

Ticket 01 supplies the evaluation and reviewed-baseline contract. Shared profile configuration, actual engine metadata, run plans/results, and comparison reporting are implemented. No beam/thread candidate has been measured or selected; the ticket remains Blocked until OPT-01 acceptance permits controlled comparisons. See [implementation evidence](../../../docs/optimization-verification-20261018.md).
