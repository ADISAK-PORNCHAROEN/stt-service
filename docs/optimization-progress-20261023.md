# CPU optimization progress and local run evidence, 23 October 2026

## Current scope update (24 October 2026)

The owner narrowed the active milestone to Formal Words transcription quality and local API verification on this computer. The source audio, publisher reference, and one-entry manifest now live in `docs/formal-words/`; file hashes were verified against the original dataset. Reference review remains 0/87 cues, and Formal Words API/worker verification remains open. Homelab and deployment work are deferred.

## Ticket state

The final acceptance target remains the owner's CPU-only i7-4770K homelab with 16 GB RAM and a 1 TB SSD. The owner asked to verify the local workflow first and defer Docker until last. Local functional evidence is now complete on this Windows workstation; it does not satisfy reference review or homelab acceptance. The only authorized recordings are Formal Words and Conversation with Kob. OPT-03 is cancelled. OPT-02, OPT-04, and OPT-05 remain conditional. OPT-01 remains In progress; OPT-06 remains Blocked.

The implementation audit found no required runtime gap for the narrowed scope. The CLI enforces the source allowlist and hash. The API and worker path is available, with an operator hash check required for this acceptance run. Offline rescoring and profile consistency already exist. The remaining gates are reviewed reference and target-host evidence.

## Local verification

The current workstation is an Intel i3-12100F system with four cores, eight threads, and 15.8 GB visible RAM. It is not the target homelab. Both authorized full originals have now completed once on this workstation using the CPU INT8 baseline: Formal Words through the guarded CLI and Conversation with Kob through the local API and persistent worker. These are local functional runs, not acceptance runs.

These transcription runs used the dirty working tree based on HEAD `4193036b7b6dcfe217f502f2433baf01dd5387ff` and completed without runtime source changes during the runs. A later follow-up in this continuation fixed the saved-SRT validator in `src/stt_services/evaluation.py` and added a two-cue regression in `tests/test_evaluation.py`; its validation results are recorded below.

| Check | Result |
| --- | --- |
| `.venv\Scripts\ruff.exe check .` | Passed. |
| `.venv\Scripts\ruff.exe format --check .` | Passed. All 227 files were formatted. |
| `.venv\Scripts\python.exe -m pytest` | Passed. 127 passed, 2 integration tests deselected. |
| `.venv\Scripts\python.exe -m mypy` | Passed. No issues in 17 source files. |
| `git diff --check` | Passed; only existing CRLF warnings were reported. |

The direct `uv run ... pytest` and `.venv\Scripts\mypy.exe` wrappers failed with `Failed to canonicalize script path`; the Python module forms above passed. The ordinary suite uses fake inference and does not prove homelab runtime, memory use, or recognition quality.

The CLI help confirms `stt transcribe --approved-only` supports one guarded inference call. The `stt evaluate` command performs repeated calls, so it is unnecessary for the basic portfolio run. Use it only when a candidate comparison or repeatable performance claim requires additional runs.

## Local full-original functional run

The external evidence bundle is `[private local path]`. It contains `local-first-run-evidence.json`, the source/result binding sidecar, per-run timings, sampled resource observations, and the complete JSON/TXT/SRT bundles. The samples are periodic observations, not a continuously measured peak.

| Recording | Path | Segments | External full-flow time | Recording duration | Descriptive RTFx | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Formal Words | CLI with `--approved-only` | 52 | 211.4 s | 281.681 s | 1.332 | Exit 0; JSON/TXT/SRT complete. |
| Conversation with Kob | API plus persistent worker | 212 | 1,136.2 s from upload request through all three downloads | 597.960 s | 0.526 | Job `ea2fd623d7e249a19ee5d311ff5c0477` succeeded at 100%; JSON/TXT/SRT complete. |

Both calls used profile `whisper-profile-v1-24b36874898eeab9e274` and model revision `0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf`. Requested settings were Turbo, CPU INT8, four threads, beam five, sequential batch one, automatic language, context enabled, temperature-zero disabled, no-repeat limit zero, and VAD enabled with the baseline parameters. The backend reported actual device `cpu` and compute type `int8_float32` for requested `int8`. The API job's recorded worker processing interval was 1,105.836 seconds; worker startup to readiness was observed at about 18.8 seconds, and the worker logged model load in 11.433 seconds.

For Formal Words, the sampled process-tree working set reached 1,209 MB and sampled available system RAM reached a minimum of 1.86 GB. Its first observation was 32.7 seconds after CLI launch, so it does not establish memory use during model loading. For Kob, the worker process-tree sample reached 1,478 MB and available RAM reached a minimum of 977 MB during the job. One post-readiness sample recorded 1,008 MB working set and 2.15 GB available; model-load memory was not continuously sampled. Neither run measured a continuous process or system peak.

Every output was checked for the three formats, matching JSON/SRT segment counts, matching TXT/JSON text (apart from the expected final newline), profile identity, model revision, and SHA-256. The CLI transcript embeds the approved source hash. The general API transcript leaves `source_sha256` null, so the binding sidecar records the original hash before/after upload and verifies that the stored job upload has the same hash. All three API downloads match the worker's stored result files.

One initial detached CLI launch was stopped by a Fortran runtime `window-CLOSE` event before producing artifacts. The completed foreground run above is authoritative; the first attempt's external logs were preserved. The baseline preflight also exposed that explicitly setting `STT_BATCH_SIZE='1'` fails settings validation. Sequential batch one is the default, so the documented baseline now leaves that variable unset. `.env.local` was not edited.

These runs establish local functional behavior and produce descriptive timing only. No reviewed speech reference was available for an accuracy score, and local measurements do not establish homelab completion or memory fit.

## Reference and host evidence

The approved source files and matching publisher answer files are located at:

- Formal Words source: `[private local path]`; publisher answer: `[private local path]`.
- Conversation with Kob source: `[private local path]`; publisher answer: `[private local path]`.

Their hashes match the approved manifest. The existing private reference drafts remain unreviewed. Formal Words has 0 of 87 cues checked for spoken text or timing. Conversation with Kob has 0 of 290 cues checked. Neither draft has a reviewer or review time, and neither has completed important-error review. No reference-backed accuracy claim is accepted.

At the initial local-first preflight, the owner said that no homelab connection had been configured. No remote command was run at that stage. The local functional results do not satisfy the homelab portions of OPT-01 or OPT-06. Reference review also remains an OPT-01 blocker.

## Follow-up ticket audit (23 October 2026)

The owner clarified that work should make the project usable on this computer first, with Docker deployment last. The owner had previously said that no homelab connection was configured. This follow-up did not confirm a homelab target, did not select another host, and ran no remote command.

The source recordings and matching publisher answer files listed above still exist and their hashes match the approved manifest and the local-first evidence. The review drafts are under `[private local path]`. Formal Words has 87 cues and Conversation with Kob has 290; both drafts record zero speech checks and zero timing checks, no reviewer/date, and no completed important-error review. This audit verified paths, hashes, and review metadata only. It did not listen to the recordings or mark cues reviewed, so no accuracy score or confirmed recognition error is available.

The read-only conditional-ticket audits found no activation evidence and no basis for an N/A disposition. OPT-02 remains conditional on a homelab turnaround problem or a reviewed error that decoding may fix. OPT-04 remains conditional on a sequential homelab result that is unsuitable for the intended use. OPT-05 remains conditional on a specific reference-confirmed recognition error. Keep all three Blocked until their required evidence exists; absent evidence does not establish that the work is unnecessary.

Current dispositions remain OPT-01 In progress, OPT-02/04/05 Blocked, OPT-06 Blocked, and OPT-03 Cancelled. Local functionality is demonstrated for both approved recordings, but OPT-01 and OPT-06 acceptance remain open for reference review and homelab evidence. Docker deployment remains last.

## Swarm audit

Three earlier read-only swarm reviews checked ticket dependencies, implementation coverage, and existing external evidence. Two more read-only workers audited ticket gates and runtime paths at the current HEAD. The audits found no mandatory runtime gap for the narrowed scope. They confirmed that the CLI enforces the source guard, while the API and worker require an operator hash check. They also confirmed that transcript `total_seconds` ends before final bundle publication and the worker's per-job memory sampler excludes model preload. The workflow and tickets now require external full-call timing and memory observation across worker startup and job completion.

The current document pass clarified the OPT-02 dependency on OPT-06, added an evidence-backed N/A policy for untriggered conditional work, listed `Cancelled` as an allowed status, and separated historical workstation decoding trials from a controlled homelab candidate comparison. It also records the external timing and memory method needed because transcript metrics end before publication and the worker loads its model before the per-job sampler starts. No runtime source change was needed, and no swarm worker edited shared files. A final independent read-only evidence review reconciled the Formal Words resource CSV and documented that local sampling did not cover model preload or a continuous peak.

Three parallel read-only continuation audits used the project-configured `gpt-6.1-sol` medium worker at HEAD `4193036b7b6dcfe217f502f2433baf01dd5387ff`. The reference inventory checked the exact source/answer paths and hashes, confirming they match the review drafts while all 377 speech/timing cues remain unchecked. The conditional-ticket audit found no trigger or N/A evidence for OPT-02, OPT-04, or OPT-05. The OPT-06 readiness audit verified all six local output hashes and identified the explicit batch-size setting in `.env.local.example`; I removed it and verified sequential mode still resolves to batch size one. Workers made no edits, ran no tests or inference, read no secret values, and contacted no host.

## Remaining work

1. Review each publisher cue against the corresponding original. Preserve publisher text and review provenance. Check spoken text, subtitle timing, uncertain spans, and important errors separately.
2. After the owner authorizes homelab access, run one approved full original through the CLI and the other through the API and persistent worker on the i7-4770K. Use the same resolved CPU INT8 baseline for both.
3. Record target-host JSON/TXT/SRT outputs, profile, model revision, host, full external wall time, process and system memory including worker preload, and limitations. Rescore saved output offline against reviewed references.
4. Evaluate OPT-02, OPT-04, and OPT-05 triggers from reference review and homelab baseline evidence. Run only a justified candidate; otherwise record why the trigger was false.
5. Package/deploy with Docker only after the local workflow is verified and when the owner resumes deployment work.

The append-only decision trail and audit addendum are stored outside the repository under `[private local path]`. The canonical six-field ledger is `opt-tickets-20261023-normalized-v1.tsv`; the original raw log remains preserved.

## Offline rescore and security review (23 October 2026)

The saved-bundle validator had expected an extra blank line between SRT cues and did not accept the exporter's trailing newline. It now validates the emitted one-blank-line cue separator and final newline. The public CLI rescore regression creates two SRT cues and verifies both are preserved. The targeted regression passed (1 passed, 20 deselected), followed by the ordinary suite and quality checks listed above.

Offline rescore was run against the approved manifest with explicit bindings at `[private local path]` (SHA-256 `FA78A1B89F4A1A19C32B866FA616E053BD321BCA3F738C4D39AE84BC197CD044`). The new output is `[private local path]`; its `comparison.json` SHA-256 is `B84DB42C301B9836AD0F1DD8EE468B454FA7C5E55A73A85A04F8F1F34AC00104`. It contains two `pending_review` results, `inference_performed=false`, and null CER/WER. Formal Words is associated through its embedded transcript source hash; Kob uses the explicit operator-attested legacy upload binding. These are provenance bindings, not reference validation. Both results remain unscored until the cue-by-cue audio review is done.

A Codex Security diff review completed for the fixed working-tree snapshot. It closed all 31 security-review inventory rows, validated three candidates, and recorded zero reportable findings. The formula-injection candidates did not establish an exploitable spreadsheet path in the tested/documented consumers. The `watch-pr --pretty` terminal-control candidate was suppressed because that local developer tool is outside the supplied transcription-service threat model, and raw ESC delivery from GitHub was not verified. The scan covered the selected changed-file inventory, not all 261 files in the broader dirty snapshot or the whole repository. Report and coverage artifacts are retained under `[private local path]`.

The local setup audit also caught `STT_BATCH_SIZE=1` in `.env.local.example`, despite the documented environment parser rejecting an explicitly supplied string value. The example now comments that setting out; sequential mode supplies batch size one by default. The real `.env.local` did not define `STT_BATCH_SIZE` and was not changed. With inherited `STT_*` variables temporarily cleared, `.venv\Scripts\python.exe -c 'from stt_services.config import Settings; s=Settings(_env_file=".env.local.example"); assert s.batch_size == 1; assert s.resolve_profile().mode == "sequential"; assert s.resolve_profile().batch_size == 1'` passed. This improves fresh local setup and does not change homelab ticket status.

## Docker readiness check (23 October 2026)

The local preflight ran `rg --files -g 'Dockerfile*' -g '*docker*' -g '*compose*.yml' -g '*compose*.yaml' -g '*.dockerignore'` and found no container files. `Get-Command docker` returned no command, and `docker --version` reported that PowerShell could not find `docker`. No image build or deployment ran. Docker remains the final phase; this check does not satisfy any OPT acceptance criterion.

## SSH target and scope clarification (24 October 2026)

The SSH client is available. The user's SSH config contains four non-wildcard host stanzas, including a duplicate entry. The owner identified a configured alias as the i7-4770K homelab, then clarified that work must stay in this project for now. No connection attempt or remote command has run, and homelab work is not authorized yet. Continue project-local work; wait for the owner to explicitly authorize homelab access before connecting.

## Current milestone and ticket cleanup (24 October 2026)

The owner narrowed the current milestone to accurate transcription and a working API on this computer. OPT-02 through OPT-05 were removed from the active ticket set and their issue files deleted. Their earlier status and review notes above are historical records only. OPT-01 now covers local reference review, scoring, and API result verification. OPT-06 remains deferred for future homelab work. No server connection or deployment is part of this milestone.

The owner then narrowed the real-recording allowlist to Formal Words only. Its MP4 and publisher TXT were copied to `[private local path]`; both SHA-256 values match the originals. A one-entry manifest now points to those stable external paths. Kob and MIT media remain outside current authorization.
