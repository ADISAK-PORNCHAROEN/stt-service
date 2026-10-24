# Guarded Whisper optimization workflow

The active milestone uses the full Formal Words and Conversation with Kob originals for CPU-only homelab accuracy/API acceptance. Keep source media, publisher answers, reviewed references, manifests, and result bundles outside Git. See the [current scope](../.scratch/stt-optimization/spec.md#active-milestone-update-24-october-2026-owner-re-authorization) and [issue tracker](agents/issue-tracker.md).

## Follow-up research and proposed structure

The [quality/latency follow-up research](research/stt-quality-performance-followup-20261018.md) records additional findings from pinned faster-whisper/CTranslate2 sources. The [architecture proposal](research/stt-quality-performance-architecture-20261018.md) maps them to immutable profiles, one shared pipeline, truthful engine diagnostics, reviewed scoring, and a bounded experiment sequence. These are research/design documents; they do not change supported commands, ticket blockers, or acceptance status.

## Current commands

Use the root uv environment and the machine-specific dotenv file. Keep all authorized originals and answer files in external data storage. Choose a new destination for each command.

The private two-entry evaluation manifest must explicitly contain only the authorized identities, source paths, matching publisher references, and frozen roles. Keep it under the external data directory; do not commit source paths or reviewed reference text. Content hashes are checked against the approved catalog, rather than trusting hashes supplied by a manifest. There is no command-line option to replace that catalog. The injectable catalog on the Python CLI entry is for generated correctness fixtures at the existing test seam.

Keep a private manifest beside neither the originals nor the review drafts. It should bind Formal Words (`aC-QbxZB7RU`, role `tuning`) and Conversation with Kob (`8qcinxUA4YA`, role `final`) to their existing files by explicit paths. Do not use the broad source-download manifest because it includes unauthorized material.

Store the manifest and review drafts outside Git under the data root configured by `.env.local`. Relative paths resolve against the manifest's directory. Duplicate/unknown identities, changed originals, mismatched publisher references, changed roles, and wildcard selections are rejected. The run rechecks bound file identities after media validation, model loading, inference, and before publication. A detected replacement invalidates the evaluation.

## Startup profiles

The same environment-backed profile is resolved once by the CLI or persistent worker. Defaults remain Turbo, CPU INT8, four threads, beam five, sequential mode, automatic language, VAD on, and the existing temperature fallback schedule. Change one setting at a time for screening; restarting a worker is required to change its profile. Result JSON records the stable profile ID, requested profile, backend-reported effective settings, and separate per-recording observations. Initial prompt and hotwords are hashed in the report and their text is never written into result metadata; configure one at a time.

Examples for an explicitly selected trial profile:

```powershell
$env:STT_BEAM_SIZE = '3'
$env:STT_CPU_THREADS = '2'
uv run --env-file .env.local stt evaluate --manifest <approved-manifest.json> --recording aC-QbxZB7RU --output-dir <new-profile-run>
```

The explicit GPU command path remains documented in the implementation, but GPU trials are outside the active homelab portfolio scope.

The codebase still contains a batched path from earlier work. It is outside the current milestone and has no active ticket.

## Reference preparation

```powershell
uv run --env-file .env.local stt evaluate --manifest <approved-manifest.json> --output-dir <new-reference-directory> --prepare-references
```

This does not load inference. It creates one reference JSON and one review Markdown per recording, plus a manifest pointing to those drafts. The two answer files and review drafts already exist in the configured external data directory, so reuse them instead of regenerating. Publisher originals are not edited.

The first Thai-containing publisher line is a provisional speech suggestion; a cue without Thai retains its first line and is flagged uncertain. This is deliberately not an automatic determination of what was spoken. For each cue:

1. Listen to the corresponding original recording and correct only the proposed spoken text.
2. Retain spoken English, including English-only cues; remove only unspoken translations and romanization.
3. Mark `reviewed` true only after checking that cue. Clear `uncertain` only when the speech is sufficiently clear; explain unresolved passages in notes.
4. Record the actual reviewer and an ISO date/time with timezone. Do not invent a review identity or mass-approve unchecked cues.
5. Check each reference cue's start and end against the original speech. Record checked boundaries and any corrected times or uncertain edges in the external review draft. `timing_reviewed` means that someone checked the cue against the audio; it does not certify candidate subtitle timing.
6. Review candidate subtitle boundaries and important errors separately. Record names, numbers, omissions, insertions during silence, and repeated text. A checked reference does not prove that a candidate's timestamps or important words are correct.

Retain every publisher cue identity and its original `publisher_lines`, including unreviewed or uncertain cues. A truncated or altered publisher inventory is rejected before inference. Correct the proposed `text`, review flags, notes, and reviewed timing separately; do not delete unresolved cues to inflate coverage.

An incomplete review produces `pending_review` and no CER/WER. A complete reviewed reference permits numerical text scoring, while candidate important-error and timing acceptance still remain pending.

## Local functional run

The 23 October local run completed Formal Words through the CLI and Conversation with Kob through the local API and persistent worker. These runs show that both entry paths can complete; they do not prove reference-backed accuracy. The current local gate is to review both answers against speech and confirm the API result is accurate.

Label these outputs as local functional evidence. This workstation is not the i7-4770K homelab, and these runs do not complete OPT-01/OPT-06, establish reference-backed accuracy, or justify conditional optimization work. Package and deploy with Docker only after this local workflow has been verified.

## Homelab acceptance run

For the portfolio acceptance, make one complete inference call for each approved full recording. Use the CLI for one recording and the API with the persistent worker for the other. One call per original covers both supported paths. Run the calls serially on the homelab with no other heavy workload. Start external process-tree and system memory observation before worker model loading and continue through job completion so the recorded sample includes preload. The output JSON records the resolved profile; verify it matches the CPU INT8 baseline before accepting the run.

Apply these process-local overrides in each PowerShell terminal that starts the CLI, API, or worker. Repeat the block in each terminal because environment variables do not cross terminal sessions. This resets experimental `.env.local` values such as the local no-repeat and VAD settings.

Sequential mode defaults to batch size 1. Leave `STT_BATCH_SIZE` unset for this baseline; setting its numeric value through the current environment-backed configuration fails validation.

Use an absent output directory for the CLI call. Keep the approved full source path from the external manifest.

```powershell
$env:STT_MODEL = 'turbo'
$env:STT_DEVICE = 'cpu'
$env:STT_COMPUTE_TYPE = 'int8'
$env:STT_CPU_THREADS = '4'
$env:STT_BEAM_SIZE = '5'
$env:STT_MODE = 'sequential'
$env:STT_LANGUAGE_MODE = 'auto'
$env:STT_CONDITION_ON_PREVIOUS_TEXT = 'true'
$env:STT_TEMPERATURE_ZERO = 'false'
$env:STT_NO_REPEAT_NGRAM_SIZE = '0'
$env:STT_VAD_ENABLED = 'true'
$env:STT_VAD_THRESHOLD = '0.5'
$env:STT_VAD_MIN_SILENCE_DURATION_MS = '2000'
$env:STT_VAD_SPEECH_PAD_MS = '400'
Remove-Item Env:STT_INITIAL_PROMPT, Env:STT_HOTWORDS -ErrorAction SilentlyContinue
uv run --env-file .env.local stt transcribe <approved-full-source> --approved-only --output-dir <new-cli-output>
```

Use the other approved original for the API and worker path. Check its full-file SHA-256 against the approved manifest before upload and after job completion. The general `/jobs` API does not enforce the evaluation allowlist, so use the approved source manually. Start `stt serve` and `stt worker` in separate terminals, applying the same environment block in both. Submit one full recording, wait for a succeeded job, then download JSON, TXT, and SRT. Follow the [README run instructions](../README.md) and the [HTTP API contract map](API.md). Replace the README example media with the other approved original. Do not submit a second job for the same recording.

The basic acceptance does not require RTFx to reach one or repeated runs. Use `stt evaluate` and the comparison workflow only when a measured timing or reviewed quality issue justifies a candidate, or when making a repeatable performance-improvement claim. Those runs add inference calls and are not part of the basic portfolio path.

Keep direct transcription, API upload, queue wait, worker processing, and artifact download time distinct. Measure CLI wall time from process launch through successful publication and return. Measure API acceptance through retrieval of all three artifacts. The transcript's `total_seconds` stops before final JSON publication, so it is not the full-call wall time. The worker loads its model before polling jobs, and its per-job memory sampler excludes that preload. Start process-memory observation before worker startup and continue through job completion. Record both process and system memory. A successful result bundle does not by itself prove speech accuracy or subtitle timing.

## Scoring policy

The initial policy is `nfc-casefold-projections-v1`. Apply Unicode NFC, case-fold English, normalize curly apostrophes, replace other punctuation/symbols with spaces, and collapse whitespace. Thai tone and vowel marks are preserved. Keep raw and normalized full-text character error views.

- Thai CER projects Thai-script characters in order, including combining marks.
- English WER projects ASCII English word tokens, preserving internal apostrophes; numeric tokens are reported separately because their language assignment is ambiguous.
- Report substitutions, deletions, insertions, and reference-unit counts, including insertions against an empty group. A zero-length reference group has no defined error rate and is not a passing group.
- Projection scores do not prove correct ordering between languages. Normalized full-text CER, numeric changes, and manual names/numbers/omission/repetition review are necessary complements.
- No whole-recording accuracy pass is inferred from unreviewed or uncertain reference cues. Formal Words cannot establish absent workload categories or broad population accuracy.

## Other real-model checks

For a direct CLI smoke check, `transcribe` and `benchmark` accept `--approved-only`, which verifies a source's approved content hash before media processing and binds its identity through the pipeline. General production transcription remains usable for caller-provided files; this feature's real experiments must use the guard.

The opted-in real CLI test uses that flag. The separate-process HTTP test verifies the supplied source before starting service processes and checks that it remains unchanged around upload and completion. Set its media environment variable only to one of the two full authorized originals. Never substitute a short excerpt or another recording to shorten a run.

## Offline rescoring and comparison

When the reference review changes, rescore saved runs without loading a model. Prefer the evaluation report, which binds each output to a source and result hash:

```powershell
uv run --env-file .env.local stt evaluate --manifest <reviewed-manifest.json> --rescore-results <saved-evaluation-directory/evaluation.json> --output-dir <new-rescore-directory>
```

This checks each saved JSON/TXT/SRT bundle for consistency and writes a new comparison destination. For the single-call CLI and API portfolio outputs, create an explicit binding document with one entry per result. Include `recording_id`, the approved `source_sha256`, and the exact `transcript_json` path. The report labels a result without an embedded source hash as operator-attested legacy provenance. Offline rescoring adds no inference calls.

Each full evaluation also writes `review-template.json`. Reviewers fill a row only after checking its exact result hash against the full original and record reviewer/time, important-error findings, boundary regressions, and host activity for that run. The repeated comparison path is optional for the portfolio demo; use it when making a repeatable speed-improvement claim. Then compare the baseline and candidate reports:

```powershell
uv run --env-file .env.local stt compare --baseline <baseline/evaluation.json> --candidate <candidate/evaluation.json> --review <baseline/review-template.json> --review <candidate/review-template.json> --output-dir <new-comparison-directory>
```

Repeat `--baseline` or `--candidate` for separate recording reports from the same profile and host. The comparison validates saved transcript hashes, source identity, the baseline profile, host, model revision, reference revision, and scoring policy. It reports medians/ranges, full-call RTFx, RSS, reference units, text variability, quality differences, and review state. It does not run inference or promote a profile. This formal comparison requires at least three warm runs and reviewed references; those requirements apply to repeatable performance/accuracy claims, not to the basic homelab completion demonstration.

## Acceptance status

Earlier local runs verified both recordings across the CLI and API/worker paths. The current milestone needs reviewed references and a reference-backed check of the local API result. Homelab and Docker acceptance remain deferred until local work is complete. See the [progress report](optimization-progress-20261023.md) for historical run evidence and limits.
