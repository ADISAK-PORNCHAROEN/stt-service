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
