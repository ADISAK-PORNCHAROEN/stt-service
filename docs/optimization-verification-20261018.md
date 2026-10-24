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

The report is retained under `[private local path]`, with canonical manifest, findings, coverage, threat model, and SARIF alongside it. No shared threat-model cache was read or replaced. Preflight passed; no persistent configuration was changed. The existing implementation goal remained active.

Applied the security contract's source/control/sink tracing, changed-boundary review, finding validation bar, test-integrity review, and capability/evidence accounting. Relevant risk areas were OWASP Top 10:2025 A01, A03, A05, A08, and A10. File size/content and trusted path construction were assessed using [ASVS 5.0.0 V5.2.1, V5.2.2 and V5.3.2](https://raw.githubusercontent.com/OWASP/ASVS/v5.0.0/5.0/en/0x14-V5-File-Handling.md). [WSTG v4.2 BUSL-08](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/10-Business_Logic_Testing/08-Test_Upload_of_Unexpected_File_Types/) informed rejection-case review; no dynamic upload penetration test is claimed. The [Secure Code Review guidance](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Code_Review_Cheat_Sheet.html) informed incremental data-flow inspection, and the [Secure Coding with AI guidance](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Coding_with_AI_Cheat_Sheet.html) informed test/dependency scrutiny.

The review excludes unrelated pre-existing dirty work and future implementation. No new authentication/session/cryptographic boundary is introduced. Native dependency internals, advisory feeds, runtime ACLs, and unsupported public hosting were not audited. No selected source read was unavailable. This result certifies neither the whole repository nor real quality/performance acceptance.

## Follow-up implementation pass

The approved software foundation now spans all six OPT tickets. The additions are present in the working tree; tracker statuses remain In progress/Blocked because real acceptance gates are not met. This pass performed no real-model inference and used no recording. It does not change or upgrade the exploratory CPU measurements documented below.

Implemented software contracts include:

- `stt evaluate --rescore-results` verifies previously saved result bundles offline and reports `inference_performed: false`; a source/result/reference mismatch or inconsistent canonical JSON/TXT/SRT bundle is rejected.
- Startup settings resolve to an immutable versioned profile shared by CLI and worker. Result metadata separates requested/effective configuration and per-recording observations; private prompt/hotword contents are represented by hashes.
- Whisper supports explicit CPU/CUDA and sequential/batched paths, with no silent device fallback, runtime-reported effective settings, and explicit unsupported/ignored-option evidence.
- Batched startup profiles reject disabled VAD until full-file clip timestamps are explicitly supported; the pinned batched API does not provide the sequential path's default full-file clip range for long recordings.
- Evaluation records plan/profile/source/result/text identities and stage timing. `stt compare` builds an offline report with repeated-run timing, resource observations, reference-unit counts, text variability, quality/review gates, and pending dispositions; it does not promote a profile.
- Worker lifecycle tests cover profile stability across a failed job. GPU capability discovery is kept distinct from model load and completed inference.
- Comparison rejects repeated evaluation reports and duplicate saved-result hashes, so the same artifact cannot meet the three-warm-run gate by repetition. Baseline/candidate overlap is also rejected.
- The comparison carries the evaluator's approximate per-run other-CPU activity into the summary and requires a hash-bound human host-isolation review for every warm run. Missing activity evidence or a pending review remains pending; reported contention blocks acceptance.

Latest engineering checks after review fixes:

| Command | Observed outcome |
| --- | --- |
| `uv run --env-file .env.local pytest` | 113 passed, 2 integration tests deselected, in 9.91 seconds |
| `uv run --env-file .env.local pytest tests/test_comparison.py tests/test_evaluation.py -q` | 24 passed after review fixes |
| `uv run --env-file .env.local mypy` | Passed, 17 production source files |
| `uv run --env-file .env.local ruff check .` | Passed |
| `uv run --env-file .env.local ruff format --check .` | Passed, 67 files |
| `git diff --check` | Passed; only Git line-ending normalization notices were printed |

These are software checks, not runtime/accuracy acceptance. The two integration tests were deselected; they were not run against any audio. Reference drafts still need human speech and boundary review; idle-host CPU repeats, CUDA model loading/transcription, batch/language/hint comparisons, home-server evidence, and full persistent-service configuration acceptance remain open. The verification report and ticket checkboxes distinguish those gates from the implementation checks.

The spec re-review confirmed duplicate-run rejection and the host-isolation gate. It also identified that faster-whisper 1.2.1's batched API does not inherit the sequential API's default full-file clip range when VAD is disabled. Profile resolution now rejects batched/VAD-off settings before inference; a regression test was observed failing before the guard and passing after it. This source-level check used no recording and performed no model inference.

The final Codex Security diff scan (`da687d8e-e682-4b46-a414-ed4e0c489cda`) completed with zero reportable findings and complete static coverage of the nine changed production source files. Changed tests were also reviewed for generated-only fixtures and inference guards. Its immutable source snapshot is `codex-security-snapshot/v1:sha256:6d965acb9ebf9b495554c5f19ef0d37bc44e9237bbbe0803bd434a78fdc4ff40`; preflight capability results were reused from the same session because configuration had not changed. The scan ran no runtime service, model, or audio. The sealed [security report](<[private local path]>) is stored outside the repository.

## Real measurements and pending acceptance

External artifacts are under `[private local path]`. The source snapshot and hashes identify the implementation used for the first CPU baseline process. The approved two-entry manifest and separate reference-review drafts are in that external location.

Formal Words completed one fresh-process cold call and three reused-model warm calls with Turbo, CPU INT8, four threads, beam five, automatic language, VAD, and segment timestamps. Cold full-call time was 188.042 seconds; warm times were 190.828, 172.363, and 178.534 seconds. Median was 178.534 seconds, range 172.363–190.828, and full-call RTFx 1.578 for the 281.681-second original. Complete JSON/TXT/SRT bundles exist for all four calls.

No other inference or heavy test job was launched by this implementation during the measurement window. However, system CPU counters recorded substantial unrelated busy time; a subsequent two-second process sample observed browser/display activity. This is exploratory timing evidence, not an accepted idle-host baseline. A controlled repetition is still required. See the [sanitized timing report](../benchmarks/reports/20261018-optimization-cpu-exploratory.md). Code/test fixes ran only after the measurement process exited successfully.

The CTranslate2 capability query detected one RTX 3050 with 6144 MiB and advertised supported CUDA compute types. This is device/runtime capability discovery, not successful GPU model loading or GPU transcription evidence.

Conversation with Kob measurement completed in a separate fresh process after code/test checks, on implementation commit `8cc973898e392c99c10e9679d74de2d04bbf0735`, using the same two-entry approved manifest and unchanged CPU baseline settings. The process exited successfully and all four JSON/TXT/SRT bundles plus `evaluation.json` are present under external `cpu-baseline-kob`. Cold was 1,033.993 seconds; warm calls were 1,164.670, 1,196.164, and 1,086.004 seconds. Warm median was 1,164.670 seconds (range 1,086.004–1,196.164), with median full-call RTFx 0.513; the real-time target was not met. The evaluation reported approximate other-system CPU of 2,281–3,543 CPU-seconds across calls, so this is exploratory timing rather than an isolated-host acceptance baseline. Quality remains pending human reference review. No production source changes, heavy tests, or other inference were introduced during that run.

Human review of the prepared references remains pending. Home-server access or execution instructions remain pending. Neither is substituted with inferred text accuracy or development-PC timing. OPT-01 remains In progress and OPT-02 through OPT-06 remain dependency-blocked; the active implementation objective has not been narrowed or marked complete.

## Next acceptance readiness check

At 2026-10-18 05:06 Asia/Bangkok, the external approved manifest still contained only the two authorized IDs and both source/reference hashes matched their immutable catalog entries. The prepared reference drafts had no reviewer identity or review timestamp. A five-second workstation sample showed 16.1% CPU utilization, 2,054,471,680 bytes of available RAM, and 407 running processes. No real-model run was started from this check: it is not evidence of an idle host. The earlier Formal Words and Kob measurements remain exploratory; rerun controlled timing when the host is otherwise idle. Numerical accuracy acceptance remains pending until the reference drafts are reviewed.

## Direct STT runs on the current implementation

After the readiness check above, one fresh `stt transcribe --approved-only` invocation was run for each of the two authorized originals on commit `4193036b7b6dcfe217f502f2433baf01dd5387ff`. No other recording was processed. Both used the resolved default Turbo profile: CPU, requested INT8 (actual `int8_float32`), four CPU threads, beam size five, automatic language detection, sequential batch size one, and VAD. The exact result bundles are outside Git:

| Recording | Audio duration | Total time | Inference time | Full-call RTFx | Peak RAM | Segments | Source SHA-256 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Formal Words | 281.681 s | 186.934 s | 177.586 s | 1.507 | 1.862 GB | 129 | `a76b7d7f787bb43912f5b1880f84ba8a301f41648583903f5364e49638d636ee` |
| Conversation with Kob | 597.960 s | 1,606.925 s | 1,597.667 s | 0.372 | 1.998 GB | 210 | `556a18e23be94d3122478d86b9a19b4afc99d1c3a573fdd78718fa3ea8a54181` |

Output directories are `[private local path]` and `[private local path]`. Their `transcript.json` SHA-256 values are respectively `378667c887f5a3c982db1796b8dc1319a158b3ed61b24e870c8a6c38da321ccb` and `f984ddb55fa1975d03f1ca5a09ddd8466111ed12efd3af6b3655acad6408b800`. Both bundles contain JSON/TXT/SRT and embed the matching authorized source hash. Kob output contains four literal U+FFFD characters in four segments; inspect those intervals against the recording and reviewed reference before classifying them as recognition or text-pipeline errors.

These are successful real STT executions, but each is a single run on a host that was not verified idle. They do not replace the required cold-plus-repeated-warm controlled baseline, and the Kob time cannot be attributed to a profile regression or improvement against earlier exploratory runs. Human speech/timing review is still absent, so no CER/WER or accuracy claim is accepted. Thus OPT-01 remains In progress, while OPT-02 through OPT-06 remain dependency-blocked; the blocker is acceptance evidence and follow-on experiments, not absence of transcription output.
