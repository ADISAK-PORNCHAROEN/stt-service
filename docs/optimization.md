# Guarded Whisper optimization workflow

The approved specification and six tickets are indexed in the local issue tracker. Only the full original Formal Words recording (aC-QbxZB7RU) and Conversation with Kob recording (8qcinxUA4YA) are authorized real-recording inputs for this work. File presence, folder membership, or an inherited media environment variable does not authorize another recording.

## Follow-up research and proposed structure

The [quality/latency follow-up research](research/stt-quality-performance-followup-20261018.md) records additional findings from pinned faster-whisper/CTranslate2 sources. The [architecture proposal](research/stt-quality-performance-architecture-20261018.md) maps them to immutable profiles, one shared pipeline, truthful engine diagnostics, reviewed scoring, and a bounded experiment sequence. These are research/design documents; they do not change supported commands, ticket blockers, or acceptance status.

## Current commands

Use the root uv environment and the machine-specific dotenv file. All media, publisher transcripts, reviewed references, manifests, and result bundles stay outside Git. Choose a new destination for each command.

The evaluation manifest must explicitly contain both authorized identities, original source paths, matching publisher-reference paths, and their frozen roles. Content hashes are checked against the approved catalog, rather than trusting hashes supplied by a manifest. There is no command-line option to replace that catalog. The injectable catalog on the Python CLI entry is for generated correctness fixtures at the existing test seam.

```json
{
  "schema_version": 1,
  "recordings": [
    {
      "id": "aC-QbxZB7RU",
      "source": "D:/ai-stt/datasets/stt-evaluation-20261018-011855/aC-QbxZB7RU/video.mp4",
      "reference": "D:/ai-stt/datasets/stt-evaluation-20261018-011855/aC-QbxZB7RU/reference.original.txt",
      "role": "tuning"
    },
    {
      "id": "8qcinxUA4YA",
      "source": "D:/ai-stt/datasets/stt-evaluation-20261018-011855/8qcinxUA4YA/video.mp4",
      "reference": "D:/ai-stt/datasets/stt-evaluation-20261018-011855/8qcinxUA4YA/reference.original.srt",
      "role": "final"
    }
  ]
}
```

Relative paths resolve against the manifest's own directory. Duplicate/unknown identities, changed originals, mismatched publisher references, changed roles, and wildcard selections are rejected. The run rechecks bound file identities after media validation, model loading, inference, and before publication. A detected replacement invalidates the evaluation.

## Startup profiles

The same environment-backed profile is resolved once by the CLI or persistent worker. Defaults remain Turbo, CPU INT8, four threads, beam five, sequential mode, automatic language, VAD on, and the existing temperature fallback schedule. Change one setting at a time for screening; restarting a worker is required to change its profile. Result JSON records the stable profile ID, requested profile, backend-reported effective settings, and separate per-recording observations. Initial prompt and hotwords are hashed in the report and their text is never written into result metadata; configure one at a time.

Examples for an explicitly selected trial profile:

```powershell
$env:STT_BEAM_SIZE = '3'
$env:STT_CPU_THREADS = '2'
uv run --env-file .env.local stt evaluate --manifest <approved-manifest.json> --recording aC-QbxZB7RU --output-dir <new-profile-run>
```

For GPU trials, set `STT_DEVICE=cuda` and a supported `STT_COMPUTE_TYPE` such as `float16` or `int8_float16`. The adapter checks visible CUDA devices and supported compute types before downloading/loading the model, and it never falls back to CPU. A returned result distinguishes capability discovery, model load, and completed inference. Device memory uses boundary samples from `nvidia-smi`; it is device-wide and may include other processes or miss brief peaks.

The batched path is explicit with `STT_MODE=batched` and `STT_BATCH_SIZE=1`, `2`, or `4`. It reports that previous-text conditioning and retry thresholds are ignored by the pinned batched implementation, that only the first temperature is used, and that segment timestamps remain enabled. It builds a new VAD argument dictionary per transcription call. The current profile rejects batched mode with VAD disabled: the pinned batched API does not provide the sequential API's default full-file clip range for long recordings. Batch one is the path control before comparing larger batches.

## Reference preparation

```powershell
uv run --env-file .env.local stt evaluate --manifest <approved-manifest.json> --output-dir <new-reference-directory> --prepare-references
```

This does not load inference. It creates one reference JSON and one review Markdown per recording, plus a manifest pointing to those drafts. Publisher originals are not edited.

The first Thai-containing publisher line is a provisional speech suggestion; a cue without Thai retains its first line and is flagged uncertain. This is deliberately not an automatic determination of what was spoken. For each cue:

1. Listen to the corresponding original recording and correct only the proposed spoken text.
2. Retain spoken English, including English-only cues; remove only unspoken translations and romanization.
3. Mark `reviewed` true only after checking that cue. Clear `uncertain` only when the speech is sufficiently clear; explain unresolved passages in notes.
4. Record the actual reviewer and an ISO date/time with timezone. Do not invent a review identity or mass-approve unchecked cues.
5. Keep subtitle-boundary and important-error review separate. A checked reference is not evidence that a candidate's timestamps or names/numbers are correct.

Retain every publisher cue identity and its original `publisher_lines`, including unreviewed or uncertain cues. A truncated or altered publisher inventory is rejected before inference. Correct the proposed `text`, review flags, notes, and reviewed timing separately; do not delete unresolved cues to inflate coverage.

An incomplete review produces `pending_review` and no CER/WER. A complete reviewed reference permits numerical text scoring, while candidate important-error and timing acceptance still remain pending.

## Controlled baseline

Run each recording in its own fresh CLI process for independent cold measurements, with no simultaneous tests, inference, or other heavy workloads. Each command performs one initial load and three warm full-file runs reusing the same model instance. All outputs must be new.

```powershell
$env:STT_MODEL = 'turbo'
$env:STT_CPU_THREADS = '4'
uv run --env-file .env.local stt evaluate --manifest <approved-manifest.json> --recording aC-QbxZB7RU --output-dir <new-formal-baseline-directory>
uv run --env-file .env.local stt evaluate --manifest <approved-manifest.json> --recording 8qcinxUA4YA --output-dir <new-kob-baseline-directory>
```

The second command starts only after the first has completed. Without `--recording`, both originals are evaluated serially in one process; later instance loading is correctly labeled `model_load`, not an independent cold start. Keep download/cache conditions explicit.

Per-run `wall_seconds` covers media validation through final JSON/TXT/SRT publication and caller return, including model load when needed. Authorization hashing/reference preflight, evaluation/scoring overhead, and total evaluation wall time are separate report fields. The internal transcript total ends earlier and must not be substituted for full caller time. A CLI run has no service queue wait.

The report records hardware, actual run metadata, host RSS, warm median/range, full-call RTFx, and whether each recording met the real-time objective. Approximate other-process CPU busy time is reported to help identify contention; counters alone cannot certify an idle host. An RTFx below one is below the objective even when faster than a previous run.

Individual calls retain their quality results. The recording summary keeps the worst observed value for each error measure across all cold/model-load and warm calls, rather than presenting only the last call. Measures may come from different calls; inspect individual bundles for their corresponding transcripts. Manual candidate names/numbers and timing review remains separate.

## Scoring policy

The initial policy is `nfc-casefold-projections-v1`. Apply Unicode NFC, case-fold English, normalize curly apostrophes, replace other punctuation/symbols with spaces, and collapse whitespace. Thai tone and vowel marks are preserved. Keep raw and normalized full-text character error views.

- Thai CER projects Thai-script characters in order, including combining marks.
- English WER projects ASCII English word tokens, preserving internal apostrophes; numeric tokens are reported separately because their language assignment is ambiguous.
- Report substitutions, deletions, insertions, and reference-unit counts, including insertions against an empty group. A zero-length reference group has no defined error rate and is not a passing group.
- Projection scores do not prove correct ordering between languages. Normalized full-text CER, numeric changes, and manual names/numbers/omission/repetition review are necessary complements.
- No whole-recording accuracy pass is inferred from unreviewed or uncertain reference cues. These two recordings cannot establish absent workload categories or broad population accuracy.

## Other real-model checks

For a direct CLI smoke check, `transcribe` and `benchmark` accept `--approved-only`, which verifies a source's approved content hash before media processing and binds its identity through the pipeline. General production transcription remains usable for caller-provided files; this feature's real experiments must use the guard.

The opted-in real CLI test uses that flag. The separate-process HTTP test verifies the supplied source before starting service processes and checks that it remains unchanged around upload and completion. Set its media environment variable only to one of the two full authorized originals. Never substitute a short excerpt or another recording to shorten a run.

## Offline rescoring and comparison

When the reference review changes, rescore saved runs without loading a model. Prefer the evaluation report, which binds each output to a source and result hash:

```powershell
uv run --env-file .env.local stt evaluate --manifest <reviewed-manifest.json> --rescore-results <saved-evaluation-directory/evaluation.json> --output-dir <new-rescore-directory>
```

This checks each saved JSON/TXT/SRT bundle for consistency and writes a new comparison destination. For a legacy transcript without an embedded source hash, an explicit binding document can name each `recording_id`, approved `source_sha256`, and exact `transcript_json` path. The report labels that source binding as operator-attested legacy provenance.

Each full evaluation also writes `review-template.json`. Reviewers fill a row only after checking its exact result hash against the full original and record reviewer/time, important-error findings, boundary regressions, and host-isolation evidence for that run. The comparison rejects duplicate evaluation reports or transcript result hashes, carries each run's observed other-CPU time forward, and stays pending until warm-run isolation is reviewed; any recorded contention blocks acceptance. Then compare the baseline and candidate reports:

```powershell
uv run --env-file .env.local stt compare --baseline <baseline/evaluation.json> --candidate <candidate/evaluation.json> --review <baseline/review-template.json> --review <candidate/review-template.json> --output-dir <new-comparison-directory>
```

Repeat `--baseline` or `--candidate` for separate recording reports from the same profile and host. The comparison validates saved transcript hashes, source identity, the baseline profile, host, model revision, reference revision, and scoring policy. It reports medians/ranges, full-call RTFx, RSS/device-memory observations, reference units, text variability, quality differences, and human-review state. It does not run inference or promote a profile. Missing reviews, fewer than three warm runs, a changed host, or an unreviewed reference cannot produce an acceptance disposition.

## Acceptance status

The goal is a measured speed improvement with no reviewed Thai/English or important-error regression, followed by separate service and host acceptance. Home-server evidence requires actual execution on that server. Source-code implementation, fake-inference passing checks, runtime compatibility, controlled timing, and human review are recorded independently. Consult the local ticket evidence for current progress rather than treating this workflow document as a passing result.
