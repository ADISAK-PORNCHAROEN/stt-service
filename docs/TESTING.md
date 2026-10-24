# Testing and verification

## Native checks

Run from the repository root with the root `.venv` and machine settings in `.env.local`:

```powershell
uv run --env-file .env.local -- python -m pytest
uv run --env-file .env.local ruff check .
uv run --env-file .env.local ruff format --check .
uv run --env-file .env.local -- python -m mypy
```

`pyproject.toml` owns pytest markers/options, Ruff rules, and mypy scope. The default pytest command excludes `integration`; ordinary tests use fake inference while retaining real filesystem and SQLite interactions. No numeric coverage threshold or coverage command is configured. Do not invent a percentage gate.

Before `uv sync --locked`, load `UV_CACHE_DIR` from `.env.local` into the PowerShell environment as described in `README.md`; `uv sync` does not load dotenv files. Do not sync dependencies for a documentation-only task.

## Select checks by behavior

| Change | Relevant evidence |
| --- | --- |
| CLI, transcript contract, export, or media validation | `tests/test_cli.py`, `test_contracts.py`, `test_inputs.py`; include output ownership, invalid formats, and original-timeline behavior as applicable |
| HTTP routes, upload admission, status, or errors | `tests/test_api.py`; use `tests/test_http_real.py` only for explicit local service/integration acceptance |
| SQLite, queue, recovery, retention, or leases | `tests/test_lifecycle.py`, `test_scheduling.py`, and the relevant API cases |
| Whisper settings/progress/profile behavior | `tests/test_whisper_engine.py`, `test_profiles.py`, `test_progress.py`, and `test_comparison.py` as affected |
| Real model behavior | `tests/test_real_model.py` and/or `tests/test_http_real.py` with explicit `STT_TEST_MEDIA`, downloaded Whisper weights, and integration opt-in |
| Optimization quality/performance acceptance | Follow the active ticket's isolated evaluation commands, allowlist, hashes, review gates, and evidence requirements; ordinary fake-inference tests do not close these gates |

Use the narrowest layer that proves the contract, then run the ordinary suite and relevant lint/format/type checks required by project rules. Regression cases should assert public behavior at a real boundary. Keep user recordings and result bundles outside Git and follow the two-recording allowlist for approved optimization work.

## Evidence and limits

Record exact commands, revision/dirty scope, pass/fail counts, and evidence paths in the owning ticket or verification report. Read `docs/agents/issue-tracker.md` before changing ticket status. Existing historical report results are not fresh results for the current revision. Source inspection, fake-inference tests, and a passing suite do not establish transcription accuracy, complete real-recording timing review, GPU support, or home-server performance. Report skipped integration/real-model checks explicitly.

Benchmark reports include the hardware, software/model versions, timing scope, RTFx, and peak process memory required by the active ticket. The basic homelab portfolio acceptance needs one complete run per approved recording; repeated comparisons are needed only for a repeatable performance-improvement claim. Report CER/WER only against reviewed reference text with documented normalization and tokenization; otherwise record the manual observations and limitations without presenting a score.
