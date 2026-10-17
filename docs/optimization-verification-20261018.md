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

## Real measurements and pending acceptance

External artifacts are under `D:\ai-stt\output\optimization-20261018-015630`. The source snapshot and hashes identify the implementation used for the first CPU baseline process. The approved two-entry manifest and separate reference-review drafts are in that external location.

Formal Words completed one fresh-process cold call and three reused-model warm calls with Turbo, CPU INT8, four threads, beam five, automatic language, VAD, and segment timestamps. Cold full-call time was 188.042 seconds; warm times were 190.828, 172.363, and 178.534 seconds. Median was 178.534 seconds, range 172.363–190.828, and full-call RTFx 1.578 for the 281.681-second original. Complete JSON/TXT/SRT bundles exist for all four calls.

No other inference or heavy test job was launched by this implementation during the measurement window. However, system CPU counters recorded substantial unrelated busy time; a subsequent two-second process sample observed browser/display activity. This is exploratory timing evidence, not an accepted idle-host baseline. A controlled repetition is still required. See the [sanitized timing report](../benchmarks/reports/20261018-optimization-cpu-exploratory.md). Code/test fixes ran only after the measurement process exited successfully.

The CTranslate2 capability query detected one RTX 3050 with 6144 MiB and advertised supported CUDA compute types. This is device/runtime capability discovery, not successful GPU model loading or GPU transcription evidence.

Human review of the prepared references remains pending. Home-server access or execution instructions remain pending. Neither is substituted with inferred text accuracy or development-PC timing. OPT-01 remains In progress and OPT-02 through OPT-06 remain dependency-blocked; the active implementation objective has not been narrowed or marked complete.
