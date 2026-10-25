# 01 — Select and Run a Whisper Model per Job

**GitHub ticket:** [stt-service#11](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/11)
**Status:** Complete — merged in [PR #13](https://github.com/ADISAK-PORNCHAROEN/stt-service/pull/13)
**Ready for agent:** Yes — no blockers.

## Parent

[Whisper Model Selection and Transcript Review API](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/10)

## Related product spec

[Whisper Model Choice and Transcript Review](https://github.com/ADISAK-PORNCHAROEN/frontend-stt/issues/8)

## What to build

Allow each API job to select Turbo or large-v3, persist that selection, and have the worker use it while keeping only one model loaded at a time. Preserve compatibility for existing jobs and CLI callers.

## Acceptance criteria

- [x] POST /jobs accepts an optional multipart model field and rejects values outside turbo and large-v3.
- [x] If callers omit model, the job uses configured STT_MODEL; the service exposes that configured default through health/readiness for the frontend's initial selection.
- [x] The selected model persists with the job. Existing SQLite databases migrate safely, and existing jobs without a model remain readable using the configured default.
- [x] CLI invocation and default behavior remain unchanged.
- [x] The worker keeps at most one model loaded, reuses it when jobs select the same model, and loads the selected model when jobs switch.
- [x] A model-load failure marks the requested job failed with a clear error and never silently uses a different model.
- [x] Backend tests cover request validation, defaulting, persistence/migration, worker reuse/switching, and load failure.
- [x] Run the real API once per model using only the owner-approved Formal Words recording and 87 reviewed cues. Follow the existing scoring policy; report actual results, model/software versions, runtime, and RAM without inventing a CER/WER threshold. Keep recording, reference, and raw results outside Git and GitHub.
- [x] Update service API/product documentation, clarify Engine versus Model in the glossary, and record an ADR for per-job selection and one loaded model at a time.

## Blocked by

None (can start immediately).

## Validation evidence

- Test revision: `43d55de28f0e15f0e360e1d24c2a906fd67568f7`; the working tree was clean during the final verification run.
- `uv run --env-file .env.local -- python -m pytest` — 154 passed, 2 deselected.
- `uv run --env-file .env.local ruff check .` — passed.
- `uv run --env-file .env.local ruff format --check .` — passed (260 files).
- `uv run --env-file .env.local -- python -m mypy` — passed (41 source files).
- Real API and existing-policy score summary: [Formal Words model API acceptance](../../../docs/formal-words-model-api-acceptance-20261026.md). The run used the feature implementation snapshot based on `d648ce9`, later committed as `9494cfb`; `00fa280` and `43d55de` only register the transcript request schema in OpenAPI components. Private run bundles and raw results remain outside Git/GitHub.
- Output transcript important-error and timing review remain pending; scores are measurements only, with no newly defined threshold.
