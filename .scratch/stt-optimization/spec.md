# Whisper Turbo transcription optimization

Document state: Approved for implementation by owner instruction.
Status: In progress.
Triage label: ready-for-agent.

## Problem Statement

The owner needs one Thai/English recording to finish transcription sooner while retaining or improving the recognized text. The current supported runtime already uses Turbo, CPU INT8, and a persistent worker, but decoding settings are mostly fixed and effective configuration reporting is hard-coded. An earlier development-PC measurement was slower than real time and overlapped other work; it is not a controlled baseline for this work.

The owner wants both a home-server CPU configuration and a development-PC GPU configuration. Hardware presence alone does not establish runtime compatibility, speed, or accuracy. Publisher transcripts also contain translations and romanization, so treating every subtitle line as spoken reference text would produce misleading scores.

## Solution

Prepare a reproducible evaluation restricted to the two owner-selected recordings, establish a controlled baseline, and compare Turbo configurations through the existing transcription workflow. Publish complete JSON/TXT/SRT result bundles and reports identifying actual device, settings, model revision, timing, resource use, and reviewed quality. Select a configuration for each supported host only when its evidence supports the speed and quality claims.

### Authorized recording inventory

The complete real-recording allowlist for this work is:

| Recording | Source identifier | Measured duration | Publisher reference | Source SHA-256 |
| --- | --- | --- | --- | --- |
| Formal Words | aC-QbxZB7RU | 281.681270 seconds, approximately 4:42 | Original timed TXT | a76b7d7f787bb43912f5b1880f84ba8a301f41648583903f5364e49638d636ee |
| Conversation with Kob | 8qcinxUA4YA | 597.960272 seconds, approximately 9:58 | Timed SRT extracted from the creator's page | 556a18e23be94d3122478d86b9a19b4afc99d1c3a573fdd78718fa3ea8a54181 |

This positive allowlist is an execution constraint. No other real recording, derived media, additional reference dataset, or automatically discovered download may enter any experiment, benchmark, real-model integration check, or acceptance run under this feature without a new explicit owner instruction. Selecting an existing broad download manifest is insufficient authorization. The original two files remain intact and inference runs on those full originals; scoring can identify intervals without creating additional test media.

The broader desired workload includes Thai mixed with English, English-only speech, and speech with background music/noise. This phase evaluates only coverage actually present in the two authorized recordings. It must report unrepresented categories as unverified and must not introduce more recordings to fill those gaps.

## User Stories

1. As the operator, I want the evaluation to select only the two authorized recordings, so that a batch cannot expand the workload without my instruction.
2. As the operator, I want source identity and content hashes checked before processing, so that a renamed or replaced recording cannot silently enter the experiment.
3. As the owner, I want Formal Words evaluated with its matching TXT and Conversation with Kob with its matching SRT, so that each result is compared to the correct content.
4. As the reviewer, I want publisher originals preserved beside any reviewed reference, so that I can trace each correction without losing the source material.
5. As the reviewer, I want translations and romanization separated from actual speech, so that only spoken words affect text-error scores.
6. As a Thai/English user, I want spoken English retained even in English-only subtitle cues, so that reference preparation does not delete language switches.
7. As the reviewer, I want unreviewed or inaudible spans identified, so that a partial reference cannot appear to certify an entire recording.
8. As the maintainer, I want a tuning recording and a frozen final-evaluation recording, so that settings are not selected from final answer text.
9. As the CPU operator, I want to retain the existing Turbo CPU INT8 configuration as a reproducible baseline, so that each candidate has a meaningful comparison.
10. As the development-PC operator, I want to request GPU execution explicitly, so that the actual accelerator is known and recorded.
11. As the operator, I want unsupported GPU requirements or memory failures reported clearly, so that a failed GPU experiment cannot masquerade as a successful CPU result.
12. As the operator, I want beam and thread settings configurable, so that I can find a faster CPU configuration using the same workflow.
13. As the operator, I want to compare sequential and batched transcription, so that any batching benefit includes its memory and quality costs.
14. As the timing reviewer, I want original recording times preserved through VAD and batching, so that subtitles still refer to the source.
15. As a Thai/English user, I want language hints and vocabulary hints evaluated independently, so that a useful change can be attributed to the correct setting.
16. As the reviewer, I want names, numbers, omissions, and repeated text tracked, so that an improved average score does not conceal important errors.
17. As the operator, I want complete result bundles from a single inference result, so that requesting TXT or SRT does not add another transcription run.
18. As the benchmark reviewer, I want time measured through final bundle publication, so that reported turnaround matches what the caller waits for.
19. As the benchmark reviewer, I want cold loading, warm reuse, and queue wait reported separately, so that I can distinguish startup and processing costs.
20. As the operator, I want warm measurements to reuse the same loaded engine, so that a second fresh process is not mislabeled as a warm run.
21. As the benchmark reviewer, I want repeated isolated runs with hardware and revision details, so that timing differences can be assessed against run-to-run variation.
22. As the GPU operator, I want host RAM and device-memory observations distinguished, so that resource reports describe the actual constraint.
23. As the home-server operator, I want a baseline and candidate measured on that server, so that development-PC results are not substituted for server evidence.
24. As the owner, I want Thai and English quality reported separately, so that a gain in one language cannot hide a regression in the other.
25. As the owner, I want the real-time objective reported per recording and host, so that an unmet speed target remains visible.
26. As the service client, I want an accepted configuration to produce the same canonical result formats through the existing API and worker, so that CLI-only improvements do not diverge from service behavior.
27. As the operator, I want a safe return to the baseline configuration, so that an unsuccessful candidate does not strand the service.
28. As the owner, I want inconclusive or unsuccessful experiments reported honestly, so that unsupported performance or accuracy claims are not promoted.

## Implementation Decisions

### Existing boundaries and configuration

- Extend the existing CLI, benchmark caller, shared pipeline, engine adapter, environment-backed settings, and transcript configuration reporting. Prefer the existing injected engine factory over adding a parallel inference stack.
- Public transcription and benchmark behavior are the primary test seam. The existing HTTP job submission/status/result workflow is the additional delivery seam for service adoption. Lower-level checks are reserved for contracts that these public flows cannot meaningfully exercise.
- Preserve the existing CPU baseline: Turbo, INT8, four inference threads, beam five, automatic initial language detection, VAD enabled, segment timestamps, and no word timestamps.
- A run selects CPU or GPU explicitly. GPU uses a supported CUDA compute type whose effective resolution is recorded. Validate availability and requested settings before inference. Do not silently change device, precision, beam, language mode, batching, or model after failure.
- Use startup configuration shared by CLI and worker. Do not add per-request HTTP tuning or multiple worker processes. Existing model reuse, queue, readiness, recovery, retention, validation, and publication contracts continue to apply.
- Replace hard-coded reported settings with the actual resolved engine configuration. Keep existing transcript fields compatible; additions to configuration or benchmark reports must be additive and unambiguous.
- Record whether execution is sequential or batched, the actual batch size, language mode, hints identifier, context policy, VAD parameters, fallback policy, device, precision, threads, beam, runtime versions, and model revision. Keep private hint text and reviewed text in external evidence rather than sanitized reports.
- Engine diagnostics can be retained in external evaluation evidence without adding unstable decoder internals to the canonical segment contract. Confidence signals are diagnostics, not calibrated correctness probabilities.

### Scope guard and references

- Evaluation takes an explicit two-entry manifest with source identifiers, approved source hashes, reference identities, review state, and recording roles. Reject unknown entries, duplicate identities, replaced content, and attempts to use a folder scan or wildcard to select inputs. Perform this preflight before model loading, media decoding, reference-content loading for scoring, or inference. Bind the validated inputs to the actual files consumed; a detectable file change invalidates the run.
- Enforce the same recording guard in opt-in real-model CLI and separate API/worker acceptance. An environment variable pointing to another real recording is not an override of this feature's authorization.
- Preserve publisher references exactly. Create separate reviewed references by checking the actual speech, removing translations and romanization, and preserving spoken English, fillers, and repetitions under a documented policy. Record changes and uncertain or omitted spans. Publisher subtitle timing is not reviewed alignment.
- Proposed allocation: Formal Words is the tuning recording; Conversation with Kob is the final-evaluation recording. Freeze settings and the tuning-derived glossary before assessing candidate results on the latter. If final-evaluation results are subsequently used to retune, label that recording as consumed for tuning; do not claim a fresh independent holdout.
- Both recordings share a creator and are a small pilot. Do not claim independent-speaker, English-only, noise, or broad production generalization from absent coverage.
- Do not use an LLM rewrite, automatic captions, or a translation as a substitute for a reviewed reference. If review is incomplete, timing and pipeline behavior can be measured but numerical accuracy acceptance remains pending.

### Staged experiments

- Screen one factor at a time using the tuning recording. Keep the model snapshot, input hashes, scoring policy, and all other effective settings fixed. Do not run an exhaustive Cartesian product by default.
- CPU screening starts with beam one, three, and five and thread counts two and four. Any larger thread count is an explicit additional case subject to physical-core and contention measurements, not a presumed improvement.
- Establish GPU compatibility and an equivalent sequential GPU baseline before attributing differences to additional GPU tuning. Trial supported FP16 and mixed INT8/FP16 configurations only when the installed runtime and memory permit them.
- Compare sequential execution against the batched path at batch one as a decoding-path control, then batch two and four. Larger batches require a documented reason and successful resource checks first.
- Treat batching as a semantic change: preserve original segment timestamps, assess changed context behavior, and record effective retry/fallback behavior rather than assuming class substitution preserves decoding.
- Compare automatic language detection, a Thai language hint for Thai-dominant speech, and per-window multilingual detection. Evaluate short relevant vocabulary hints separately from language and previous-text conditioning. Do not extract a glossary from final-evaluation reference text.
- Retain baseline VAD/fallback behavior initially. Change it only in a separately identified case justified by observed missed speech, repetition, or retries; record the associated quality effect. Do not globally remove retries merely to lower timing.
- Full-file second-pass inference, selective stronger-model correction, alternate backends, and training are follow-on options requiring separate scoped work after these results.

### Measurement and quality decisions

- The primary warm turnaround measure wraps validation through complete JSON/TXT/SRT publication and caller return while reusing a loaded model. Measure cold full-call time separately, including model loading, and identify cached-download conditions. Queue wait is a separate service observation. Do not substitute transcript-internal timing, which ends earlier, for full-call time.
- Use an otherwise idle host and sequential measurements. Record screening results as exploratory. For the baseline and selected finalists, obtain at least three warm full-file runs per authorized recording on each host being accepted; report median, range, and whole-process peak RSS. Record device-memory observation method and limitations separately for GPU runs.
- Preserve every input and existing output. Each run uses a new destination, and aborted runs cannot advertise a partial successful bundle. Raw results, references, manifests, and model/cache data remain external to Git; only sanitized evidence belongs in versioned reports.
- The initial objective is real-time-or-better warm turnaround, equivalent to full-call RTFx at least one on each authorized recording. A partial improvement below that objective is reported as improvement with the target unmet; it must not be described as meeting the performance objective.
- Compare every candidate against a same-host baseline. The home-server CPU result requires actual execution there; local CPU and GPU results are separate evidence. Missing access or runtime compatibility leaves that host's acceptance pending rather than inventing a result.
- Freeze normalization and scoring before selecting a candidate. Preserve Thai vowel and tone marks, document Unicode normalization, define punctuation/case and number handling, and retain raw and normalized views. Thai CER and English WER require reviewed spoken text and a disclosed language-assignment/tokenization policy; score spoken English within these recordings without claiming a standalone English corpus result. If a reliable language assignment is unavailable, mark that score pending rather than inventing it.
- Include scored-reference coverage and unscored spans. Evaluate whole-recording omissions, insertions during silence, repeated text, and important names/numbers alongside per-language scores so that projection or normalization cannot hide an error.
- No candidate may be promoted merely for lower latency. It must show stable lower median warm full-call time than its same-host baseline on both authorized recordings, no worsening of reviewed Thai or English scores on either applicable recording, no increase in reviewed important errors, and no newly observed subtitle-boundary regression. An unmeasurable group is unverified, not a pass.
- The quality-improvement objective requires at least one observed reduction in a predeclared text-error measure without violating the non-regression checks. Equal-quality speedups are identified as such. Small-sample observations are not population accuracy estimates, and no new absolute CER/WER threshold is invented.
- Existing structural timestamp checks remain mandatory. Human timing review records which audible boundaries were checked and distinguishes model timing from reviewed alignment; no word-level timing capability is introduced.
- Keep the baseline selectable. Report each host as accepted, performance target unmet, quality evidence pending, unsupported, or inconclusive as applicable, with measured reasons. Do not mark full two-host acceptance complete while required evidence is missing.

## Testing Decisions

- Test observable outcomes: accepted/rejected evaluation inputs, exit behavior, complete bundles, effective metadata, deterministic scoring examples, timestamp preservation, and service readiness/results. Avoid tests coupled to private helper calls or decoder implementation details.
- Prefer the existing CLI entry with its injected engine factory, exercising real media validation and filesystem publication using tiny generated fixtures and fake inference. These correctness fixtures are not additional real-recording experiments or quality evidence.
- Follow existing CLI tests for JSON/TXT/SRT consistency, one inference per bundle, missing inputs, and preservation of sources. Follow existing input/contract tests for rejected media, source offsets/gaps, resampling tails, SRT rounding, and publication failures.
- Use fake inference through the existing HTTP application and persistent worker with real SQLite/filesystem interactions for profile propagation, model reuse, readiness failure, job isolation, and result download behavior. Do not add endpoints solely to make tests convenient.
- Exercise denied or replaced real-input identities using inert test doubles without loading or decoding an unapproved real file. Assert that rejected selections do not instantiate inference or produce experimental outputs.
- Use small hand-authored text examples for reference cleaning and Thai/English scoring, including spoken English-only cues, Thai combining marks, numbers, translation contamination, and missing review state. Do not place actual transcripts in Git.
- Opt-in real-model checks and performance measurements use only the two allowlisted full originals, with new external destinations and fixed revisions. No actual experiment or model run is part of preparing this specification.
- Distinguish fake-engine passing checks, model/runtime compatibility, controlled timing, reviewed text quality, and reviewed timing evidence. None substitutes for the others. Implementation tickets record commands, actual outcomes, evidence locations, and limitations before completion.

## Out of Scope

- All real recordings outside the positive two-entry allowlist, including extracts, substitutes, synthetic augmentations of real recordings, and additional reference datasets, until explicitly authorized by the owner.
- Additional downloads or transcription of other media to fill coverage gaps.
- Singing recognition, diarization, word timestamps, forced alignment, live streaming, queue-throughput optimization, and multiple workers.
- Public-network deployment, new authentication flows, external transcription services, and per-request HTTP tuning controls.
- Alternative engines/models, selective second-pass implementation, model training, new hardware purchases, or a new backend in this initial optimization delivery.
- Broad accuracy claims, verified alignment claims, or unsupported speed multipliers derived from these two recordings.
- Reopening or changing the accepted MVP tickets or the cancelled engine experiment.

## Further Notes

This specification synthesizes the accepted interview decisions and the owner's later restriction to exactly two recordings. That restriction narrows the earlier desired corpus breadth and replaces the approximate ten-minute corpus suggestion; the two original durations total approximately fourteen minutes forty seconds. It does not change the real-time processing objective.

The existing benchmark already reuses a loaded model; adding reuse is not new optimization work. Existing dependency compatibility constraints, including the current PyAV ceiling, continue to apply. GPU support is a proposed extension to the CPU-only MVP, not a statement that CUDA setup has passed.

The owner authorized implementation of the public test seams, tuning/final-evaluation allocation, and six-ticket breakdown. The tracker vocabulary is Planned, Blocked, In progress, and Complete; ready-for-agent is a triage label, with readiness determined separately by approval and completed blocking tickets.

See the [review package](review.md) and [published ticket breakdown](review.md#approved-tickets). The existing [domain glossary](../../CONTEXT.md) supplies terminology. This specification records scope and acceptance requirements; actual implementation progress and validation evidence are tracked separately in the tickets.
