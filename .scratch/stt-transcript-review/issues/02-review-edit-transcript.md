# 02 — Save and Export a Reviewed Transcript

**GitHub ticket:** [stt-service#12](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/12)
**Status:** Complete (acceptance passed; merge pending)
**Ready for agent:** Yes — no blockers.

## Parent

[Whisper Model Selection and Transcript Review API](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/10)

## Related product spec

[Whisper Model Choice and Transcript Review](https://github.com/ADISAK-PORNCHAROEN/frontend-stt/issues/8)

## What to build

Let a client save corrected text for a completed job without rerunning inference. Preserve the original ASR transcript and segment timing, and make regular result/export formats use the latest saved text.

## Acceptance criteria

- [x] PUT /jobs/{job_id}/transcript accepts the complete existing segment ID/text set only for succeeded jobs.
- [x] Reject missing, extra, duplicate, or mismatched segment IDs and reject changes to fields other than text.
- [x] Save the full transcript atomically; a failed update leaves the previously saved result intact.
- [x] Preserve the original ASR transcript separately and immutably. Keep only the original and latest saved transcript; do not add edit history.
- [x] GET /jobs/{job_id}/result?format=json|txt|srt returns the latest saved text; format=original-json returns the original ASR result.
- [x] TXT and SRT remain derived from the matching JSON transcript and preserve existing segment times.
- [x] Transcript editing does not change job eligibility or the current media/result retention policy.
- [x] Backend tests cover successful-job-only edits, validation, atomicity, original preservation, timing preservation, and all output formats.
- [x] Update the service API/product documentation for save, original-result, export, and retention behavior.

## Blocked by

None (can start immediately).

## Validation evidence

- `uv run --env-file .env.local -- python -m pytest` — 154 passed, 2 deselected.
- `uv run --env-file .env.local ruff check .` — passed.
- `uv run --env-file .env.local ruff format --check .` — passed (260 files).
- `uv run --env-file .env.local -- python -m mypy` — passed (41 source files).
- API, SQLite, and filesystem cases are covered by `tests/test_job_models_and_transcript_review.py`, `tests/test_api.py`, `tests/test_lifecycle.py`, and `tests/test_inputs.py`.
