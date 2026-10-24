# Whisper Turbo transcription optimization

> Archived scope: this document records the former two-recording homelab optimization plan. The active owner-approved scope is now [local transcription workflow and REST API architecture](../stt-rest-api/spec.md), tracked by [GitHub issue #1](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/1) and its tickets. Do not use the historical gates below as current work. The owner removed OPT-02, OPT-04, and OPT-05 from the active plan; their local ticket files have been deleted. Homelab acceptance is deferred.

## Historical milestone update (24 October 2026)

This was the prior owner-authorized plan. It is retained as historical rationale only and has been superseded by the local-only scope in the current spec linked above.

Keep media, references, models, caches, databases, and run outputs outside Git. `.env` and local environment files must remain ignored. Do not add GitHub Actions, use GPU, change models, run broad sweeps, test on another host, deploy, or make production-SLA/general-accuracy claims. The public repository may contain only source and sanitized project documentation, never private runtime data. Earlier 24 October local-only scope and any contradictions in historical notes are superseded by this owner re-authorization. Reference review and host acceptance remain unproven until their evidence exists.

Document state: Archived; superseded for current work.
Status: Historical.
Triage label: none.

## Historical scope update (23 October 2026)

The owner narrowed delivery to a CPU-only homelab test and portfolio demonstration on the i7-4770K system with 16 GB RAM and a 1 TB SSD. The system must complete the approved transcription workflow on that machine, stay within available memory, and publish usable results. Record actual runtime and quality evidence. Real-time throughput is a reported metric, not a release gate; no production availability or service-level claim is in scope. This update supersedes the earlier development-PC GPU, two-host comparison, and mandatory RTFx-at-least-one objectives.

Keep only the two already authorized full recordings. Reuse their existing publisher answer files as inputs to reference review; do not create a new corpus. GPU work is cancelled for this delivery. CPU batching and broad language/hint sweeps are conditional follow-ups, only if the homelab run or reviewed errors show a need.

Execution order update (23 October 2026): first verify the full local CPU workflow on the current Windows workstation with the approved originals, using fresh external output and service-runtime directories. Treat those results as local functional evidence only; they do not satisfy the i7-4770K homelab acceptance gate or reference review. Prepare Docker deployment after the local workflow is verified. Homelab testing and portfolio acceptance remain the final target-host phase.

## Problem Statement

The original issue was that Thai/English recordings needed to finish transcription on a home server while retaining or improving recognized text, but decoding settings were fixed and effective configuration reporting was hard-coded. The implementation now supports resolved profiles and effective-setting metadata. This delivery verifies that workflow on the home server, which remains the only target for acceptance evidence.

The owner will use the home server for testing and a portfolio demonstration. Publisher transcripts contain translations and romanization, so treating every subtitle line as spoken reference text would produce misleading scores; use the existing answer files and review their spoken-text content before scoring.

Exploratory comparison of Conversation with Kob against a provisional Thai-line subtitle projection produced warm Thai CER median 44.22%, range 42.73-52.62%, with differing recognized text across runs. The references have not been reviewed against speech, and publisher timing has not been verified. This is a substantial text-disagreement warning, not a validated percentage of speech recognized incorrectly. The operator needs to distinguish reference/orthography mismatches, genuine recognition errors, and run-to-run decoding variation before selecting an optimization.

## Solution

Use the existing references for the two owner-selected recordings and establish a CPU INT8 baseline on the homelab. Only if the references or measured turnaround identify a concrete need, compare at most two CPU candidate profiles through the existing workflow. Complete full-file transcription, publish JSON/TXT/SRT bundles, and record actual settings, model revision, elapsed time, memory, and reviewed quality. Do not require real-time speed or make a production-performance claim.

Keep the selected CPU profile consistent across CLI and worker, return actual engine observations with recognized segments, and compare saved results against the reviewed references offline. Retain the baseline if candidates do not improve a reviewed error without unacceptable slowdown or resource use. Run a batch or language/hint follow-up only when the baseline or reference review identifies a concrete reason.

### Implementation and acceptance status (18 October 2026)

The following status records the 18 October scope. The active 23 October scope above supersedes its repeated-run and real-time acceptance gates.

As of 18 October, the software foundation for all six tickets was implemented in the working tree: guarded evaluation and offline rescoring; versioned immutable profiles and truthful engine metadata; explicit CPU/CUDA and sequential/batched options; reference/run-bound comparison reports; and worker profile-isolation coverage. This records code availability, not ticket completion. Engineering checks then passed (113 ordinary tests, lint, formatting, and type checks); the commands and measurements are in [implementation evidence](../../docs/optimization-verification-20261018.md).

One fresh real STT call per authorized recording completed on the default Turbo CPU profile. Formal Words completed in 186.934 seconds (full-call RTFx 1.507); Conversation with Kob completed in 1,606.925 seconds (RTFx 0.372). Under the 18 October scope, these single non-isolated runs did not satisfy the repeated idle-host baseline or establish an optimization gain. The Kob result contains four U+FFFD characters pending review. Publisher references still require human speech/timing review, so accuracy remains unaccepted. The 23 October scope supersedes the repeated-run gate and the current ticket table records active status.

Real acceptance remained open on 18 October. Reference drafts had not received full human speech/timing review. Existing CPU measurements were exploratory because unrelated host CPU activity was observed. Against the former RTFx target, Conversation with Kob measured below real time; the 23 October scope treats throughput as descriptive. CUDA capability discovery was observed, but no GPU model load or transcription was accepted. No CPU candidate, batch, language, hint, home-server, or final service profile had been selected from reviewed evidence. The current tracker records remaining work.

The owner later requested a targeted CPU quality correction and real-model job-progress verification. Three two-original diagnostic trials now exist: temperature zero; temperature zero with context disabled (rejected for long repetition); and temperature zero with context enabled and a decoder n-gram limit of eight. The last is selected experimentally in local `.env.local`, with the original baseline and profile identities retained. Four real HTTP integration invocations passed, including both originals under the selected profile. Observable corruption/repetition symptoms improved, while spelling/name errors, reference/timing review and full OPT acceptance remain pending. The [follow-up report](../../docs/cpu-quality-progress-20261018.md) records actual commands, private artifact links, test outcomes and limitations. This targeted owner instruction does not close the staged optimization gates or claim final default promotion.

### Authorized recording inventory

The current real-recording allowlist contains exactly two recordings:

| Recording | Source identifier | Duration | Role | Publisher reference | Source SHA-256 | Reference SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| Formal Words | aC-QbxZB7RU | 281.681270 seconds, approximately 4:42 | Tuning | Original timed TXT | a76b7d7f787bb43912f5b1880f84ba8a301f41648583903f5364e49638d636ee | c2722da771b40d9964ec7cdb0fd1ca369609e85bfb9de5c6e95b9477b9ef2231 |
| Conversation with Kob | 8qcinxUA4YA | 597.960272 seconds, approximately 9:58 | Final evaluation | Timed SRT from creator page | 556a18e23be94d3122478d86b9a19b4afc99d1c3a573fdd78718fa3ea8a54181 | 819b8a647b64f081f5156822e22a0645e374d0be628e7fa5f96d9d2d47fd7306 |

This positive allowlist is an execution constraint. No other real recording, derived media, additional reference dataset, or automatically discovered download may enter any experiment, benchmark, real-model integration check, or acceptance run under this feature. Selecting an existing broad download manifest is insufficient authorization. Keep both original sources intact; scoring can identify intervals without creating additional test media.

The broader desired workload includes Thai mixed with English, English-only speech, and speech with background music/noise. This phase evaluates only coverage present in Formal Words. It must report unrepresented categories as unverified and must not introduce more recordings to fill those gaps.

## User Stories

1. As the operator, I want the evaluation to select only the one authorized recording, so that a batch cannot expand the workload without my instruction.
2. As the operator, I want source identity and content hashes checked before processing, so that a renamed or replaced recording cannot silently enter the experiment.
3. As the owner, I want Formal Words evaluated with its matching TXT, so that the result is compared to the correct spoken content.
4. As the reviewer, I want publisher originals preserved beside any reviewed reference, so that I can trace each correction without losing the source material.
5. As the reviewer, I want translations and romanization separated from actual speech, so that only spoken words affect text-error scores.
6. As a Thai/English user, I want spoken English retained even in English-only subtitle cues, so that reference preparation does not delete language switches.
7. As the reviewer, I want unreviewed or inaudible spans identified, so that a partial reference cannot appear to certify an entire recording.
8. As the maintainer, I want a tuning recording and a frozen final-evaluation recording, so that settings are not selected from final answer text.
9. As the CPU operator, I want to retain the existing Turbo CPU INT8 configuration as a reproducible baseline, so that each candidate has a meaningful comparison.
10. As the homelab operator, I want a full recording to finish on the target CPU, so that the portfolio workflow is demonstrated on the machine it is meant to run on.
11. As the operator, I want actual runtime and memory use recorded, so that the demonstrated result fits the homelab's resources.
12. As the operator, I want beam and thread settings configurable, so that I can find a faster CPU configuration using the same workflow.
13. As the operator, I want batching considered only if the CPU baseline is too slow for my use, so that an extra inference path is not required for the portfolio demo.
14. As the timing reviewer, I want original recording times preserved through VAD, so that subtitles still refer to the source.
15. As a Thai/English user, I want a language or vocabulary hint tried only for a reference-confirmed error, so that a useful change can be attributed without a broad parameter sweep.
16. As the reviewer, I want names, numbers, omissions, and repeated text tracked, so that an improved average score does not conceal important errors.
17. As the operator, I want complete result bundles from a single inference result, so that requesting TXT or SRT does not add another transcription run.
18. As the benchmark reviewer, I want time measured through final bundle publication, so that reported turnaround matches what the caller waits for.
19. As the benchmark reviewer, I want model-load and queue-wait times reported separately when measured, so that I can distinguish startup and processing costs.
20. As an operator making a speed comparison, I want warm measurements to reuse the same loaded engine, so that a second fresh process is not mislabeled as a warm run.
21. As a benchmark reviewer making a repeatable performance claim, I want repeated isolated runs with hardware and revision details, so that timing differences can be assessed against run-to-run variation.
22. As the homelab operator, I want process memory and available system memory recorded, so that a full run can be shown to fit the target machine.
23. As the home-server operator, I want a baseline and candidate measured on that server, so that development-PC results are not substituted for server evidence.
24. As the owner, I want Thai and English quality reported separately, so that a gain in one language cannot hide a regression in the other.
25. As the owner, I want full-call time and RTFx reported for each recording, so that portfolio viewers can see the measured speed without implying a real-time service guarantee.
26. As the service client, I want an accepted configuration to produce the same canonical result formats through the existing API and worker, so that CLI-only improvements do not diverge from service behavior.
27. As the operator, I want a safe return to the baseline configuration, so that an unsuccessful candidate does not strand the service.
28. As the owner, I want inconclusive or unsuccessful experiments reported honestly, so that unsupported performance or accuracy claims are not promoted.
29. As the reviewer, I want exploratory subtitle-disagreement scores clearly distinguished from reviewed speech scores, so that a high percentage cannot be mistaken for a measured fraction of incorrectly recognized words.
30. As the reviewer, I want saved result bundles rescored without another transcription, so that correcting a reference does not waste inference time or masquerade as improved recognition.
31. As the maintainer, I want actual detected or forced language identified, so that a forced-language probability cannot be mistaken for measured confidence.
32. As the maintainer, I want repeat-run text differences and observable fallback evidence, so that unstable results and slow calls can be investigated without guessing their cause.
33. As the worker operator, I want a profile fixed throughout a worker lifetime, so that one job cannot mutate the next job's decoding behavior.
34. As the batch reviewer, I want effective segmentation, context, fallback, and timestamp settings identified, so that a class change cannot hide a change in recognition behavior.
35. As the language reviewer, I want spoken English and Thai-script representations handled under a frozen policy, so that a writing-convention change cannot silently distort language-specific scores.
36. As the operator, I want explicit missing-diagnostic and unsupported-runtime outcomes, so that an unavailable observation is not replaced with invented evidence.
37. As the maintainer, I want per-recording language and diagnostic observations kept separate from the startup profile, so that a job's observations cannot mutate the configuration used by the next job.
38. As the experiment operator, I want each run bound to an explicit plan and identifiable profile, so that I can reproduce a comparison without reconstructing options from scattered commands.
39. As the owner, I want one comparison summary showing time, resources, reviewed quality, and pending evidence, so that selecting a configuration does not require interpreting every raw result directory.

## Implementation Decisions

### Existing boundaries and configuration

- Extend the existing CLI, benchmark caller, shared pipeline, engine adapter, environment-backed settings, and transcript configuration reporting. Prefer the existing injected engine factory over adding a parallel inference stack.
- Public transcription and benchmark behavior are the primary test seam. The existing HTTP job submission/status/result workflow is the additional delivery seam for service adoption. Lower-level checks are reserved for contracts that these public flows cannot meaningfully exercise.
- Preserve the existing CPU baseline: Turbo, INT8, four inference threads, beam five, automatic initial language detection, VAD enabled, segment timestamps, and no word timestamps.
- Active acceptance uses CPU INT8 only. Validate requested CPU settings before inference. Do not silently change precision, beam, language mode, or model after failure. The implemented GPU path is outside this delivery.
- Use startup configuration shared by CLI and worker. Do not add per-request HTTP tuning or multiple worker processes. Existing model reuse, queue, readiness, recovery, retention, validation, and publication contracts continue to apply.
- Resolve a versioned, immutable profile once at startup and use it throughout a worker lifetime. Keep the model window at 30 seconds in this phase and build fresh upstream argument dictionaries for every call; mutable VAD/window state must not leak across jobs. Keep configuration/refactoring within the existing complete transcription slice rather than creating a general profile framework.
- Replace hard-coded reported settings with the actual resolved engine configuration. Keep existing transcript fields compatible; additions to configuration or benchmark reports must be additive and unambiguous.
- Return recognized segments and effective runtime metadata together through the existing engine seam. The pipeline publishes that resolved evidence rather than reconstructing requested settings as though they had been applied. Distinguish requested precision from the runtime's actual compute representation.
- Record the actual CPU device, precision, thread count, beam, language mode, VAD/context/fallback settings, runtime versions, and model revision. Keep private hint text and reviewed text in external evidence rather than sanitized reports.
- Engine diagnostics can be retained in external evaluation evidence without adding unstable decoder internals to the canonical segment contract. Confidence signals are diagnostics, not calibrated correctness probabilities.
- Distinguish forced/detected language and initial/per-window policy. A forced language's returned probability of one is not measured detection confidence. Segment temperature is an engine observation, not a retry count; report retry attempts/time only when genuinely observed and otherwise mark them unavailable. Retain detailed private logs externally. Any diagnostic artifact included in a result bundle must be finalized before atomic publication.

### Shared processing and evaluation interfaces

- The configuration module resolves one immutable startup profile with a stable identity and version. Keep per-recording observations, such as detected language and retained speech duration, in the engine result rather than changing the startup profile or its identity.
- The Whisper adapter owns persistent CPU model loading, sequential invocation, complete generator consumption, and effective engine metadata. The existing engine interface is the seam shared by the real and fake adapters; changes to its result contract are delivered with all existing callers in the same narrow slice.
- The shared pipeline owns validation, original-recording time restoration, canonical transcript construction, and atomic result publication. CLI and worker both invoke it; optional GPU or batching paths do not introduce another pipeline and are not required for this delivery.
- Reference preparation and offline scoring belong to evaluation. The production recognizer never receives a reviewed reference or final-evaluation answer text. Reuse the existing public evaluation workflow for inference-free comparison rather than adding another recognition stack.
- Each experiment plan identifies the authorized recordings and roles, requested profile and resolved settings, model/runtime identity, reviewed-reference revision, and scoring policy. Run records bind those identities to complete output bundles and observed timing. Missing provenance prevents acceptance claims.
- Produce one homelab CPU summary with actual profile, one full-file call per recording, process and system memory, reviewed Thai/English errors with reference-unit counts, important-error and timing review state, and candidate disposition. Report whether model loading or cache reuse occurred and report RTFx as a descriptive value. Keep unavailable values explicit. Keep raw content and detailed diagnostics in external evidence.

### Scope guard and references

- Evaluation takes an explicit one-entry manifest with source identifier, approved source hash, reference identity, review state, and role. Reject unknown entries, duplicates, replaced content, and attempts to use a folder scan or wildcard. Perform preflight before model loading, media decoding, reference loading, or inference. Bind validated inputs to files consumed; a detectable change invalidates the run.
- The opt-in real-model CLI enforces the recording allowlist and source hash. The general local `/jobs` API does not consult the evaluation manifest. For API/worker acceptance, verify the Formal Words source hash immediately before upload and confirm the original remains unchanged after completion. Submit only this authorized original.
- Preserve publisher references exactly. Create separate reviewed references by checking the actual speech, removing translations and romanization, and preserving spoken English, fillers, and repetitions under a documented policy. Record changes and uncertain or omitted spans. Publisher subtitle timing is not reviewed alignment.
- Formal Words is the sole recording in this milestone. It is a small pilot; do not claim independent-speaker, English-only, noise, or broad production generalization from absent coverage.
- Do not use an LLM rewrite, automatic captions, or a translation as a substitute for a reviewed reference. If review is incomplete, timing and pipeline behavior can be measured but numerical accuracy acceptance remains pending.
- Permit offline comparison of saved canonical results with their matching reviewed references without loading a model or performing inference. Validate recording/result/reference identities and record their revisions; preserve existing outputs. Reference corrections change the scoring evidence, not the recognized transcript.
- Keep provisional publisher-line comparisons explicitly exploratory. Freeze orthography/transliteration, fillers/repetitions, numeric handling, normalization, language-assignment, and coverage before candidate selection. Report reference-unit counts and raw/normalized full-text error alongside script projections. Partial reference review must not be compared against an entire hypothesis as though the scopes matched; acceptance remains pending unless a separately defined reviewed scoring scope is supported.

### Staged experiments (outside current milestone)

CPU-profile, batch, language/hint, GPU, and other model comparisons are excluded from the current local milestone. The following historical guidance does not schedule those tasks.

- Screen one factor at a time using the tuning recording. Keep the model snapshot, input hashes, scoring policy, and all other effective settings fixed. Do not run an exhaustive Cartesian product by default.
- Start from the existing CPU INT8/four-thread/beam-five profile. Screen at most two CPU candidates, one setting change at a time, only when the reference review or measured turnaround identifies a reason. Do not run an exhaustive parameter sweep.
- Keep sequential inference and automatic language detection as the active path. CPU batching and alternate language/hint profiles are optional follow-ups, not portfolio acceptance requirements. If one is tried, tie it to a measured slowdown or reference-confirmed error and compare its complete outputs against the baseline.
- Retain baseline VAD/fallback behavior initially. Change it only in a separately identified case justified by observed missed speech, repetition, or retries; record the associated quality effect. Do not globally remove retries merely to lower timing.
- Observe fallback behavior before proposing a separately labeled restricted-temperature comparison on Formal Words. Positive-temperature sampling is a possible explanation for variation, not a proven cause of Kob errors; temperature zero alone is neither a correctness guarantee nor a promise of identical results across devices.
- Full-file second-pass inference, selective stronger-model correction, alternate backends, and training are follow-on options requiring separate scoped work after these results.

### Measurement and quality decisions

- For each portfolio call, measure full caller time through complete JSON/TXT/SRT publication and caller return. Include model loading when it occurs inside that path. Record API upload, queue wait, worker startup/model loading, and job processing separately when observable. Use warm repeated comparisons only for a repeatable performance-improvement claim. Do not substitute transcript-internal timing, which ends earlier, for full-call time.
- Homelab runtime, memory, and performance measurements are outside the current milestone. The retained OPT-06 ticket describes future work only.
- Include per-run canonical-text hashes/differences and associated quality observations, rather than relying on whole-JSON hashes containing changing timing metadata. Record broad validation, engine-processing, and publication timing where observable; do not invent encoder/decoder or retry-stage measurements without appropriate observations. Approximate unrelated CPU counters inform the host-isolation review but do not prove an idle host.
- Preserve every input and existing output. Each run uses a new destination, and aborted runs cannot advertise a partial successful bundle. Raw results, references, manifests, and model/cache data remain external to Git; only sanitized evidence belongs in versioned reports.
- The current local milestone must finish Formal Words through the API and publish complete JSON/TXT/SRT bundles; accuracy remains pending until its reference is reviewed.
- Compare any candidate against the homelab CPU baseline. Do not claim speed or accuracy gains from development-host results or unsupported cross-host comparisons.
- Freeze normalization and scoring before selecting a candidate. Preserve Thai vowel and tone marks, document Unicode normalization, define punctuation/case and number handling, and retain raw and normalized views. Thai CER and English WER require reviewed spoken text and a disclosed language-assignment/tokenization policy; score spoken English within these recordings without claiming a standalone English corpus result. If a reliable language assignment is unavailable, mark that score pending rather than inventing it.
- Include scored-reference coverage and unscored spans. Evaluate whole-recording omissions, insertions during silence, repeated text, and important names/numbers alongside per-language scores so that projection or normalization cannot hide an error.
- Do not promote a profile that worsens reviewed Thai/English text, important errors, or subtitle boundaries on the applicable recordings. Prefer a profile only when it fixes a reference-confirmed error without making full-call time or memory use impractical. An unmeasurable group remains unverified.
- The quality-improvement objective requires at least one observed reduction in a predeclared text-error measure without violating the non-regression checks. Equal-quality speedups are identified as such. Small-sample observations are not population accuracy estimates, and no new absolute CER/WER threshold is invented.
- Existing structural timestamp checks remain mandatory. Human timing review records which audible boundaries were checked and distinguishes model timing from reviewed alignment; no word-level timing capability is introduced.
- Keep the baseline selectable. Report the homelab run as complete, quality review pending, unsupported, or inconclusive as applicable, with measured reasons. Do not label one portfolio demonstration as a production or generalization result.

## Testing Decisions

- Test observable outcomes: accepted/rejected evaluation inputs, exit behavior, complete bundles, effective metadata, deterministic scoring examples, timestamp preservation, and service readiness/results. Avoid tests coupled to private helper calls or decoder implementation details.
- Prefer the existing CLI entry with its injected engine factory, exercising real media validation and filesystem publication using tiny generated fixtures and fake inference. These correctness fixtures are not additional real-recording experiments or quality evidence.
- Follow existing CLI tests for JSON/TXT/SRT consistency, one inference per bundle, missing inputs, and preservation of sources. Follow existing input/contract tests for rejected media, source offsets/gaps, resampling tails, SRT rounding, and publication failures.
- Use fake inference through the existing HTTP application and persistent worker with real SQLite/filesystem interactions for profile propagation, model reuse, readiness failure, job isolation, and result download behavior. Do not add endpoints solely to make tests convenient.
- Exercise denied or replaced real-input identities using inert test doubles without loading or decoding an unapproved real file. Assert that rejected selections do not instantiate inference or produce experimental outputs.
- Use small hand-authored text examples for reference cleaning and Thai/English scoring, including spoken English-only cues, Thai combining marks, numbers, translation contamination, and missing review state. Do not place actual transcripts in Git.
- Verify offline rescoring with fake adapters that fail if inference is constructed or invoked. Cover reference/result identity mismatches, review gates, coverage, and source/output preservation through the public evaluation workflow.
- Verify two sequential worker calls, including an initial failure, preserve the resolved profile and fresh VAD arguments. Test observable effective metadata and text/timing behavior rather than upstream private decoder internals; distinguish forced-language probability and unavailable retry telemetry in reports.
- Opt-in real-model checks and performance measurements use only the two allowlisted full originals, with new external destinations and fixed revisions. No actual experiment or model run is part of preparing this specification.
- Distinguish fake-engine passing checks, model/runtime compatibility, controlled timing, reviewed text quality, and reviewed timing evidence. None substitutes for the others. Implementation tickets record commands, actual outcomes, evidence locations, and limitations before completion.

## Out of Scope

- All real recordings outside the two-entry Formal Words and Conversation with Kob allowlist, extracts, substitutes, synthetic augmentations, and additional reference datasets.
- Additional downloads or transcription of other media to fill coverage gaps.
- Singing recognition, diarization, word timestamps, forced alignment, live streaming, queue-throughput optimization, and multiple workers.
- Public-network deployment, new authentication flows, external transcription services, and per-request HTTP tuning controls.
- Alternative engines/models, selective second-pass implementation, model training, new hardware purchases, or a new backend in this initial optimization delivery.
- Broad accuracy claims, verified alignment claims, or unsupported speed multipliers derived from this single recording.
- Reopening or changing the accepted MVP tickets or the cancelled engine experiment.

## Further Notes

This specification retains historical decisions and reports. The current owner-approved local-only scope is recorded in the REST/API spec linked at the top of this document.

The existing benchmark already reuses a loaded model; adding reuse is not new optimization work. Existing dependency compatibility constraints, including the current PyAV ceiling, continue to apply. GPU support exists in the implementation but is outside this delivery.

The earlier public test seams and ticket breakdown are historical. OPT-02, OPT-04, and OPT-05 are no longer active, and OPT-03 GPU work remains cancelled. Current implementation and acceptance work is tracked only by the newer owner-approved REST/API issue set.

The owner subsequently requested the Kob problem/remedies be added to this specification and tickets, followed by further source research and a manageable structure. This elaborates the already approved seams and six-ticket breakdown. The [follow-up research](../../docs/research/stt-quality-performance-followup-20261018.md) and [architecture proposal](../../docs/research/stt-quality-performance-architecture-20261018.md) supply version-specific rationale. Future media-decode reuse, model/backend changes, and selective second passes in those notes remain outside this delivery. Documentation changes do not complete reference review, controlled timing, or any implementation acceptance criterion.

See the [historical review package](review.md). The existing [domain glossary](../../CONTEXT.md) supplies terminology. Current implementation progress and validation evidence are tracked in the issues linked from the active REST/API spec.
