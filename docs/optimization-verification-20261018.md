# Whisper optimization implementation evidence

Status: In progress. This is not a completed feature or an accuracy/performance acceptance claim.

## Scope

The owner approved the specification and six-ticket breakdown and instructed implementation. Real-recording work is restricted to Formal Words and Conversation with Kob. Tiny generated correctness fixtures and inert denied-input bytes are used for ordinary fake-inference checks; they are not an additional recorded-media corpus.

## Implemented OPT-01 foundation

- Explicit evaluation manifests with fixed source/reference hashes, roles, duplicate/unknown/wildcard rejection, and file-identity checks around media validation, engine loading, inference, and publication.
- Public evaluation through the existing CLI/shared pipeline, complete JSON/TXT/SRT result bundles, a selected-recording option, one first load and three reused-model warm runs by default, and honest labeling of later in-process instance loading.
- Publisher reference preparation into external JSON/Markdown drafts, retaining English-only cues as uncertain rather than discarding them.
- Numerical scoring gated on review provenance and cue review state, with Thai tone/vowel preservation, English-word projection, full-text raw/normalized errors, numeric changes, and explicit remaining review limits.
- Hardware and full-call timing reports distinguish media processing, authorization/reference preflight, scoring/evaluation overhead, internal transcript timing, and approximate unrelated CPU activity.
- Opt-in real CLI/HTTP tests preflight the permitted source identities; generic production transcription is not limited to the evaluation corpus.

## Observed checks after review fixes

| Command | Observed outcome |
| --- | --- |
| `uv run --env-file .env.local pytest tests/test_evaluation.py tests/test_cli.py tests/test_contracts.py -q` | 39 passed in 3.19 seconds |
| `uv run --env-file .env.local pytest -q` | 95 passed, 2 integration checks deselected, in 9.30 seconds |
| `uv run --env-file .env.local mypy` | Passed, 16 source files |
| `uv run --env-file .env.local ruff check .` | Passed |
| `uv run --env-file .env.local ruff format --check .` | Passed, 60 files |

These checks cover the current OPT-01 software foundation, not completion of the six-ticket feature. The ordinary suite uses fake inference, generated fixtures, real filesystem/SQLite interactions, and existing CLI/API boundaries. No coverage threshold is configured and no coverage measurement is claimed. Actual-process model integration and human quality/timing acceptance remain pending.

## Review follow-up

Two independent read-only review axes inspected the OPT-01 working-tree foundation against implementation-start revision `b93404ece55645db75b4f566284d00dd1f58e497`. Standards found no hard documented-standard violation; a timezone-provenance validation gap was noted. Spec review identified:

1. Approved-source CLI/HTTP consumers must use the canonical authorized path rather than resolving a user alias again.
2. A reviewed reference must account for every publisher cue; completeness cannot be calculated only against a possibly truncated submitted cue list.
3. Reference preparation must recheck file identity after reading and before publishing a provenance-bearing draft.

All three follow-ups and timezone-aware review provenance are fixed. Their public CLI regressions were observed failing against the prior code and passing after correction. A further regression verifies that the worst per-measure error across repetitions survives the quality summary even when the last run is correct. The two review axes rechecked the actual changes and reported no remaining actionable findings in this bounded foundation. This review is separate from the required security diff review and does not constitute completion or security certification.

## Security diff review

Codex Security prompt-driven diff scan `106274db-fc1d-4275-940f-f6f23f9cc066` completed and its sealed documents were read back. The immutable range is `b93404ece55645db75b4f566284d00dd1f58e497..8cc973898e392c99c10e9679d74de2d04bbf0735`; all 22 changed files were accounted for, including the six source inventory entries, three tests, the dependency lock, and twelve documents. Result: zero reportable findings and complete static coverage of that diff. An independent source-backed architecture pass supported the review. No source or test execution was performed by the security scan.

The report is retained under `C:\Users\computer\.codex\state\plugins\codex-security\scans\stt-services\8cc973898e392c99c10e9679d74de2d04bbf0735_20261017T192148Z_kxovnw2r\report.md`, with canonical manifest, findings, coverage, threat model, and SARIF alongside it. No shared threat-model cache was read or replaced. Preflight passed; no persistent configuration was changed. The existing implementation goal remained active.

Applied the security contract's source/control/sink tracing, changed-boundary review, finding validation bar, test-integrity review, and capability/evidence accounting. Relevant risk areas were OWASP Top 10:2025 A01, A03, A05, A08, and A10. File size/content and trusted path construction were assessed using [ASVS 5.0.0 V5.2.1, V5.2.2 and V5.3.2](https://raw.githubusercontent.com/OWASP/ASVS/v5.0.0/5.0/en/0x14-V5-File-Handling.md). [WSTG v4.2 BUSL-08](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/10-Business_Logic_Testing/08-Test_Upload_of_Unexpected_File_Types/) informed rejection-case review; no dynamic upload penetration test is claimed. The [Secure Code Review guidance](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Code_Review_Cheat_Sheet.html) informed incremental data-flow inspection, and the [Secure Coding with AI guidance](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Coding_with_AI_Cheat_Sheet.html) informed test/dependency scrutiny.

The review excludes unrelated pre-existing dirty work and future implementation. No new authentication/session/cryptographic boundary is introduced. Native dependency internals, advisory feeds, runtime ACLs, and unsupported public hosting were not audited. No selected source read was unavailable. This result certifies neither the whole repository nor real quality/performance acceptance.

## Real measurements and pending acceptance

External artifacts are under `D:\ai-stt\output\optimization-20261018-015630`. The source snapshot and hashes identify the implementation used for the first CPU baseline process. The approved two-entry manifest and separate reference-review drafts are in that external location.

Formal Words completed one fresh-process cold call and three reused-model warm calls with Turbo, CPU INT8, four threads, beam five, automatic language, VAD, and segment timestamps. Cold full-call time was 188.042 seconds; warm times were 190.828, 172.363, and 178.534 seconds. Median was 178.534 seconds, range 172.363–190.828, and full-call RTFx 1.578 for the 281.681-second original. Complete JSON/TXT/SRT bundles exist for all four calls.

No other inference or heavy test job was launched by this implementation during the measurement window. However, system CPU counters recorded substantial unrelated busy time; a subsequent two-second process sample observed browser/display activity. This is exploratory timing evidence, not an accepted idle-host baseline. A controlled repetition is still required. See the [sanitized timing report](../benchmarks/reports/20261018-optimization-cpu-exploratory.md). Code/test fixes ran only after the measurement process exited successfully.

The CTranslate2 capability query detected one RTX 3050 with 6144 MiB and advertised supported CUDA compute types. This is device/runtime capability discovery, not successful GPU model loading or GPU transcription evidence.

Conversation with Kob measurement started in a separate fresh process after code/test checks, on implementation commit `8cc973898e392c99c10e9679d74de2d04bbf0735`, using the same two-entry approved manifest and unchanged CPU baseline settings. Its new external destination is `cpu-baseline-kob`, and `kob-run.json` records the process/revision context. This process is still running; no completed cold/warm time, median, or acceptance result is claimed yet. No production source changes, heavy tests, or other inference are introduced during that run.

Human review of the prepared references remains pending. Home-server access or execution instructions remain pending. Neither is substituted with inferred text accuracy or development-PC timing. OPT-01 remains In progress and OPT-02 through OPT-06 remain dependency-blocked; the active implementation objective has not been narrowed or marked complete.
