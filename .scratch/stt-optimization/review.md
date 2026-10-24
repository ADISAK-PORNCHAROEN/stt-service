# Review: Whisper Turbo optimization

Document state: Approved by the owner's instruction to implement the specification and tickets.

## Active scope update (24 October 2026, owner re-authorization)

The owner re-authorized OPT-01, OPT-02, OPT-04, OPT-05, and OPT-06 for CPU-only acceptance on the i7-4770K homelab, using the full Formal Words and Conversation with Kob originals and their existing publisher answers. Review speech and timing before scoring. Start with CPU INT8. Run no more than two CPU candidate profiles when a measured baseline or reviewed reference shows a need. Test batching only if sequential is unsuitable and one hint only for a specific reference-confirmed error. Document N/A when a conditional ticket is not needed. Keep GPU work cancelled and do not deploy.

Both inputs have prior complete local CLI/API-worker runs, but the review drafts remain unreviewed at 0/87 Formal Words cues and 0/290 Kob cues. Those historical runs do not prove homelab acceptance or reviewed accuracy.

## Scope and test seams

Only the two named full originals are authorized for current real-recording checks. Do not use excerpts, derived media, or additional datasets. Existing public CLI behavior and HTTP job/worker/result workflow remain available. Tiny generated fake-inference fixtures support correctness checks and are not a real-recording corpus.

Use both supplied publisher answers as review inputs and preserve their originals. Formal Words is tuning material; Kob is final evaluation material. Neither supports broad speaker, language, or production accuracy claims. Publisher text still requires confirmation against audio before any accuracy score.

## Approved tickets

1. **OPT-01: Verify accurate local transcription and API workflow**
   - Blocked by: None.
   - Delivers: reviewed references, CPU INT8 baseline, and accurate CLI/API-worker bundles for both recordings.
   - [Ticket](issues/01-two-recording-evaluation.md)
2. **OPT-02: Compare at most two CPU profiles when evidence requires it.** [Ticket](issues/02-cpu-decoding-profiles.md)
3. **OPT-04: Test batching only if sequential results are unsuitable.** [Ticket](issues/04-batched-transcription.md)
4. **OPT-05: Test one hint only for a reviewed specific error.** [Ticket](issues/05-language-vocabulary-hints.md)
5. **OPT-06: Verify the complete two-recording homelab portfolio workflow.**
   - Depends on OPT-01 and any needed conditional dispositions.
   - [Ticket](issues/06-host-selection-service-acceptance.md)

OPT-03 GPU execution remains cancelled. OPT-02, OPT-04, and OPT-05 are conditional; their existing implementation does not count as acceptance. Close each only with its trigger evidence or a documented N/A disposition under the ticket criteria.

## Approval

The owner originally approved the six-ticket plan, then re-authorized the two-recording homelab scope on 24 October. OPT-03 GPU remains cancelled. Completed or cancelled tickets remain closed.

## Kob quality follow-up and architecture detail

The owner requested the observed Kob problem and remedies be added, followed by further primary-source research and a manageable implementation structure. The existing public seams and six-ticket breakdown were already approved, so this update elaborates those tickets without introducing another approval gate or duplicate ticket.

- OPT-01 adds explicit exploratory-score interpretation and offline rescoring of preserved canonical bundles with reviewed references and fixed coverage/representation rules.
- Profile, GPU, batching, and hint work is historical implementation context, not active ticket work in this milestone.
- OPT-06 verifies the single homelab CPU workflow and traceable portfolio evidence.

See the [source research](../../docs/research/stt-quality-performance-followup-20261018.md) and [architecture proposal](../../docs/research/stt-quality-performance-architecture-20261018.md) for historical rationale. The two-recording allowlist and quality review remain. Real-time and two-host gates are superseded by the homelab portfolio objective; no new runtime implementation, accepted baseline, reviewed accuracy, or completed ticket is claimed by this documentation update.

## Implementation handoff

The current handoff covers the five owner-selected tickets. Use the existing CLI/evaluation seam and worker/result workflow. Keep media, references, model/cache data, and run artifacts outside Git.

| Ticket | Work to fix or add | Independently verifiable deliverable | Blocked by |
| --- | --- | --- | --- |
| OPT-01 | Review both publisher references; freeze scoring/review policy; establish CPU INT8 baseline; verify CLI/API-worker results and offline scoring. | Both original/reference pairs are hash-bound; reviewed speech/timing and important-error coverage are recorded; outputs are complete; accuracy stays pending if review is incomplete. | None |
| OPT-02 | Compare at most two CPU candidates only when the baseline or reviewed reference identifies a concrete need. | A candidate fixes a reviewed error or a measured turnaround/resource issue without unacceptable quality, time, or memory regression; otherwise record N/A with baseline evidence. | OPT-01 |
| OPT-04 | Check one batch candidate only when sequential is unsuitable. | Evidence demonstrates a sequential limitation, and a bounded batch result preserves reviewed speech/timing and complete outputs; otherwise record N/A. | OPT-02 disposition |
| OPT-05 | Try at most one hint case for one specific reviewed error. | Tuning evidence names the error; final Kob results check non-regression without using its answer text to build the hint; otherwise record N/A. | OPT-02 disposition and reviewed source |
| OPT-06 | Run both approved originals on the i7-4770K through CLI and API/worker with fresh external outputs. | Complete JSON/TXT/SRT for both; profile/model revision, time, RTFx, memory, reference state, and limitations recorded. Deployment remains out of scope. | OPT-01 and applicable conditional dispositions |

The software implementation pass covers the existing code paths. The feature remains In progress: reference review and homelab CPU evidence are pending. GPU execution is cancelled; batching and broad language work are not prerequisites. Earlier MVP or exploratory checks do not substitute for homelab evidence; see the [optimization verification report](../../docs/optimization-verification-20261018.md) and current ticket statuses.

Future media-decode reuse, persistent audio/feature caching, another model/backend, and selective second-pass processing are not new tickets in this delivery. Their research notes establish options to reconsider after measured stage costs and the current quality/latency outcomes justify separate scope.
