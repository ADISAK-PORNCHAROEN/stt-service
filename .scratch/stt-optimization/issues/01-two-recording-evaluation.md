# 01: Verify accurate local transcription and API workflow

What to build: Review both approved publisher answers against their original audio, then verify CPU INT8 transcription through the CLI and API/worker on the i7-4770K homelab.
Blocked by: None.
Status: In progress.
Ready for agent: Yes; approved and implementation started.
Triage label: ready-for-agent.

## Problem

The matching publisher answer files already exist, but neither review draft is marked reviewed. Validate and correct only these existing answers instead of creating new reference material. Current evidence records 0/87 Formal Words cues and 0/290 Kob cues reviewed. The owner re-authorized homelab acceptance; deployment remains out of scope.

Exploratory Kob comparison yielded a 44.22% warm-median Thai CER against a provisional publisher projection, with differing output across runs. Its unreviewed multilingual subtitles cannot establish a fraction of incorrectly recognized speech. Reference mismatch and actual STT errors need distinct evidence before tuning.

## Solution

Use the existing explicit manifest and evaluation boundary. Validate both source identities and hashes before inference, preserve their publisher references, review spoken text/timing, score saved results against reviewed speech, and verify the CPU INT8 workflow through CLI and API/worker on the homelab.

## User stories

1. As the operator, I want unknown inputs rejected before processing, so that only authorized recordings can be tested.
2. As the reviewer, I want publisher text distinguished from reviewed speech, so that translations and romanization cannot contaminate scores.
3. As the maintainer, I want a controlled baseline with timing and quality evidence, so that later candidates can be compared fairly.

## Implementation decisions

Use the existing public evaluation workflow, shared pipeline, injected engine seam, and explicit two-recording allowlist. Do not create a second inference implementation. The specification owns each immutable source identity and hash. Keep originals, references, reviewed corrections, model/cache data, run outputs, and private reports outside Git; the local Formal Words copy is Git-ignored.

The complete real-recording inventory is Formal Words (4:42) and Conversation with Kob (9:58), each with its existing publisher answer. No other recording may be tested.

Use Formal Words for tuning and Kob for final evaluation. Freeze scoring/normalization and record reviewed/scored coverage. Freeze Thai/English language-assignment rules before reporting CER/WER; if either reference cannot be reviewed, report its quality acceptance pending and do not substitute an exploratory score.

Compare preserved canonical bundles with reviewed reference revisions offline without constructing inference. Preserve publisher lines, review provenance, result identity, scoring-policy identity, and existing outputs. Freeze orthography/transliteration policy and report unit counts with raw/normalized full-text error. Do not turn a partial reference into a whole-recording score. Disclose the already inspected Kob results and keep future candidate selection on Formal Words.

Bind saved result hashes to their source/evaluation records rather than inferring identity from a basename. Legacy results lacking reliable provenance need an explicit binding or unavailable-identity outcome before acceptance scoring.

## Testing

Use public CLI/evaluation behavior with fake inference, inert denied inputs, tiny generated correctness fixtures, and real filesystem interactions. Check rejection before engine construction, deterministic hand-authored scoring cases, source preservation, complete bundles, and failed-run visibility. Real-media acceptance uses the two authorized originals only and new external destinations.

## Acceptance criteria

- [ ] Evaluation accepts only the two approved manifest identities with matching source and publisher-reference hashes; unknown, duplicate, replaced, or implicitly discovered inputs fail before media processing or inference. Verify public CLI/API boundaries.
- [ ] Matching publisher TXT/SRT originals are preserved, and separate reviewed references remove translations/romanization while preserving actual English speech and documenting uncertain spans and corrections.
- [x] Normalization, language-assignment/tokenization, important-error categories, reviewed timing boundaries, and scored coverage are documented before comparisons; unreviewed material cannot produce an accuracy pass. See the [scoring policy](../../../docs/optimization.md#scoring-policy), [reference preparation and review](../../../docs/optimization.md#reference-preparation), and the `score_reference` review gate in `src/stt_services/evaluation/reference_review.py`.
- [ ] Existing publisher-projection percentages are labeled exploratory disagreement; a reviewed comparison identifies reference/representation issues and genuine errors without translating CER into a literal fraction of incorrect words.
- [x] Saved canonical result bundles can be rescored through the public evaluation workflow without model construction/inference, with matching source/result/reference identities, review gates, policy/revision evidence, unchanged outputs, and reference-unit counts. Fake-inference tests verify offline execution and reject mismatched/tampered bindings; real reviewed-reference scoring remains pending.
- [x] Offline scoring writes a new comparison destination, binds each result to the authorized source instead of trusting its basename, rejects mismatched/tampered bundles, and identifies the recording, saved result, reviewed-reference revision, and scoring policy used for every reported value. Fake-inference tests verify offline execution and rejection behavior; real reviewed-reference accuracy remains pending.
- [x] The agreed tuning/final-evaluation allocation is recorded without claiming independent-speaker coverage.
- [x] Both originals have historical full local CLI/API-worker completions with JSON/TXT/SRT output evidence. These runs predate the homelab acceptance and do not close the current gate.
- [ ] Review the existing publisher answers against audio, then rescore saved local outputs through the offline public workflow. Keep accuracy pending until review is complete.
- [ ] Verify that a reference-matched transcription is retrievable through the local API as JSON/TXT/SRT.
- [ ] Evidence distinguishes compatibility, speed, text accuracy, and timing review, and records the limits of English-only and noise coverage.
- [x] Relevant fake-inference checks and configured implementation-quality checks pass: the latest ordinary suite and Ruff lint/format and mypy outcomes are recorded in the linked progress evidence. This does not complete real-model or human acceptance.

Offline rescoring, duplicate-run rejection, and the added public-behavior checks are implemented. One fresh default-profile STT call produced complete bundles for each authorized original on the development workstation (Formal Words: 186.934 s, RTFx 1.507; Conversation with Kob: 1,606.925 s, RTFx 0.372). These 18 October measurements are historical and uncontrolled. Human reference review and reviewed accuracy/timing evidence remain open. The active 23 October scope accepts one full call per recording for the homelab portfolio; repeated runs are needed only for a repeatable performance claim. The Kob result also contains four U+FFFD characters that need interval review.

## Local-first evidence (23 October 2026)

The owner requested local functionality before Docker work. Formal Words now completes through the guarded CLI and Conversation with Kob through the local API/worker on the current i3-12100F Windows workstation, using the CPU INT8 baseline and fresh external paths. See the [local run report](../../../docs/optimization-progress-20261023.md) and external evidence at `[private local path]`. This confirms both local paths only; it does not satisfy the unchecked homelab or reference-review criteria above.

The 23 October follow-up audit reconfirmed that both source recordings and matching publisher answers exist and match the approved manifest. Their private review drafts remain at `[private local path]`: Formal Words has 0/87 speech cues and 0/87 timing cues reviewed; Conversation with Kob has 0/290 for each. Neither has reviewer/date provenance or completed important-error review. No audio cue was checked in this audit, so no score or reference-backed error finding was added. The owner asked to finish local work first and leave Docker deployment until last. Target-host acceptance remains outstanding.

The follow-up fixed the offline saved-SRT validator and added a public CLI regression using two cues. The targeted test passed, and the ordinary suite passed (127 passed, 2 integration tests deselected); Ruff lint/format and mypy also passed. Offline rescore produced two results at `[private local path]`, both `pending_review` with null CER/WER and inference disabled. The Formal source is bound by embedded source hash; Kob uses an explicit operator-attested legacy upload binding. Neither binding constitutes human reference review. The validated results and commands are recorded in the [23 October progress report](../../../docs/optimization-progress-20261023.md). Ticket status and review gates are unchanged.

## Out of scope

Any real input beyond the two positive-allowlist originals; derived test media; extra downloads; GPU; production rollout; treating publisher subtitles as already reviewed.

## Further notes

This is the evaluation contract consumed by the CPU candidate and homelab acceptance tickets. If reference review is incomplete, timing and pipeline behavior can be demonstrated but no accuracy improvement can be claimed. Validation evidence: [23 October progress report](../../../docs/optimization-progress-20261023.md) and [18 October implementation evidence](../../../docs/optimization-verification-20261018.md). Guarded evaluation/reference preparation, offline rescore, profile/run binding, and ordinary checks are implemented. Earlier development-host runs produced complete bundles but do not substitute for the homelab run. The supplied answer review drafts remain unreviewed. Full specification and review package are available from the feature index.
