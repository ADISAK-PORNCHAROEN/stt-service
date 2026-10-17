# Review: Whisper Turbo optimization

Document state: Approved by the owner's instruction to implement the specification and tickets.

## Scope and test seams

Only Formal Words and Conversation with Kob are authorized real-recording inputs. All experiments, including real-model acceptance, must use that positive allowlist. Existing public CLI transcription/benchmark behavior with an injected engine is the primary seam; the existing HTTP job/worker/result workflow verifies final service adoption. Tiny generated fake-inference fixtures support correctness checks and are not a new real-recording corpus.

The proposed split uses Formal Words for tuning and freezes the chosen settings before final evaluation on Conversation with Kob. The owner authorized this allocation; it does not establish an independent-speaker test set.

## Approved tickets

1. **OPT-01: Prepare the two-recording evaluation and controlled CPU baseline**
   - Blocked by: None.
   - Delivers: explicit input guarding, matching reviewed references, quality/timing reports, and a reproducible development-host CPU baseline.
   - [Ticket](issues/01-two-recording-evaluation.md)
2. **OPT-02: Compare configurable CPU decoding through complete result bundles**
   - Blocked by: OPT-01, whose guarded evaluation and baseline establish the comparison contract.
   - Delivers: beam/thread candidates through CLI and shared startup configuration, actual settings in JSON, and an evidence-based CPU comparison.
   - [Ticket](issues/02-cpu-decoding-profiles.md)
3. **OPT-03: Transcribe and measure with the existing GPU explicitly**
   - Blocked by: OPT-02, which supplies the shared configuration and reporting contract.
   - Delivers: opt-in GPU complete bundles and a same-host CPU/GPU comparison, with clear compatibility/resource failures.
   - [Ticket](issues/03-gpu-transcription.md)
4. **OPT-04: Compare batched transcription while preserving text and timing**
   - Blocked by: OPT-02, which supplies the candidate configuration/reporting contract. GPU work is not required for a CPU batch comparison.
   - Delivers: independently verifiable sequential/batched CPU candidates and original-timeline bundles; GPU batching is evaluated in final acceptance if available.
   - [Ticket](issues/04-batched-transcription.md)
5. **OPT-05: Compare language and vocabulary hints for mixed speech**
   - Blocked by: OPT-02, which supplies controlled candidate settings and comparison metadata.
   - Delivers: Thai/English hint candidates with reviewed error comparisons and protected final-evaluation content.
   - [Ticket](issues/05-language-vocabulary-hints.md)
6. **OPT-06: Select host configurations and verify persistent-service delivery**
   - Blocked by: OPT-03, OPT-04, OPT-05.
   - Delivers: frozen host-specific choices or explicit unmet/pending outcomes, same-host acceptance evidence, service verification, and documented baseline recovery.
   - [Ticket](issues/06-host-selection-service-acceptance.md)

OPT-03, OPT-04, and OPT-05 can proceed independently after OPT-02. OPT-06 integrates their outcomes; an unsuccessful optimization experiment is still useful evidence, but a ticket cannot claim a capability passed when it did not.

## Approval

The owner instructed implementation of the specification and tickets. The six tickets are published in the configured local tracker with the ready-for-agent triage label. Readiness still depends on completed blockers and acceptance evidence.

## Kob quality follow-up and architecture detail

The owner requested the observed Kob problem and remedies be added, followed by further primary-source research and a manageable implementation structure. The existing public seams and six-ticket breakdown were already approved, so this update elaborates those tickets without introducing another approval gate or duplicate ticket.

- OPT-01 adds explicit exploratory-score interpretation and offline rescoring of preserved canonical bundles with reviewed references and fixed coverage/representation rules.
- OPT-02 adds immutable resolved profiles, engine-returned effective metadata, truthful language/fallback diagnostics, and repeat-run text comparisons within the existing complete configuration slice.
- OPT-03 adds exact installed-runtime compatibility evidence and clear separation of discovery, model load, and GPU inference.
- OPT-04 adds explicit path-specific VAD/window/timestamp semantics and fresh per-call arguments.
- OPT-05 adds reviewed code-switch/orthography/error-propagation analysis and evidence-justified fallback comparison.
- OPT-06 adds consecutive-job profile isolation and traceable host-specific disposition.

See the [source research](../../docs/research/stt-quality-performance-followup-20261018.md) and [architecture proposal](../../docs/research/stt-quality-performance-architecture-20261018.md). The recording allowlist, tuning/final allocation, blocking edges, and real-time/quality gates continue to apply. No new runtime implementation, accepted baseline, reviewed accuracy, or completed ticket is claimed by this documentation update. Broader model/backend/preprocessing proposals remain future scope.

## Implementation handoff

The owner's renewed to-spec/to-tickets request is published as refinements to these six existing vertical slices. Each slice delivers observable behavior through the already approved CLI/evaluation seam and, where applicable, the existing worker/result workflow. The original seam and ticket structure already have approval; no additional interview or duplicate ticket is required for these refinements.

| Ticket | Work to fix or add | Independently verifiable deliverable | Blocked by |
| --- | --- | --- | --- |
| OPT-01 | Correct interpretation of exploratory Kob scores; reviewed speech/coverage rules; add offline rescoring with result provenance. | Existing bundles can be compared in a new report without inference; unreviewed/mismatched references cannot produce an accuracy pass; both originals have controlled baseline evidence before closure. | None |
| OPT-02 | Replace hard-coded configuration reporting; add immutable profile identity, engine-returned metadata, per-file observations, and reproducible run records. Include necessary narrow prefactoring here. | A selected CPU beam/thread profile reaches real CLI/worker inference and complete bundles; actual settings and observed diagnostics agree, including after sequential success/failure cases. | OPT-01 |
| OPT-03 | Add explicit GPU execution and exact-runtime compatibility/resource evidence. | Complete GPU bundles or clear unsupported/resource-failure outcomes, with a same-host CPU/GPU comparison. | OPT-02 |
| OPT-04 | Add explicit batched mode with resolved VAD/context/fallback/timestamp semantics and fresh per-call arguments. | Sequential, batch-one control, and batch-two/four cases produce reviewed timing/text/resource comparisons without cross-job profile drift. | OPT-02 |
| OPT-05 | Add independent language/context/vocabulary comparisons and evidence-justified VAD/fallback cases. | Reviewed Thai/English, code-switch, orthography, omission, repetition, and important-error evidence identifies useful/regressing/inconclusive settings without tuning on Kob answers. | OPT-02 |
| OPT-06 | Add a consolidated host/profile comparison and adopt supported profiles through the persistent worker with baseline recovery. | Frozen finalists or explicit baseline-retention decisions have traceable evidence and consistent CLI/HTTP results; missing host/reference evidence remains visible. | OPT-03, OPT-04, OPT-05 |

The software implementation pass now covers all six slices, including the refinements in this handoff. The feature remains In progress: checkboxes record only outcomes with current software evidence, while real-recording comparisons, reference review, GPU model execution, home-server evidence, and service acceptance remain pending. Earlier MVP or exploratory checks do not substitute for these gates; see the [optimization verification report](../../docs/optimization-verification-20261018.md) and current ticket statuses. GPU, batching, and language work can proceed independently after OPT-02 acceptance, as already defined.

Future media-decode reuse, persistent audio/feature caching, another model/backend, and selective second-pass processing are not new tickets in this delivery. Their research notes establish options to reconsider after measured stage costs and the current quality/latency outcomes justify separate scope.
