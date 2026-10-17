# Repository Guidelines

## Project Structure

This Python 3.12 project transcribes Thai/English with Whisper Turbo on CPU. Code is in `src/stt_services/`, tests in `tests/`, and sanitized measurements in `benchmarks/reports/`. Before changing behavior, read `.scratch/stt-mvp/spec.md`, `.scratch/stt-mvp/architecture.md`, and `docs/agents/issue-tracker.md`. `STT-HANDOFF.md` is background; `CONTEXT.md` defines project terms.

## Setup and Development Commands

Use uv and the root `.venv`. Set `HF_HOME`, `UV_CACHE_DIR`, and `STT_DATA_DIR` outside the repository. Run commands from the root:

- `uv sync --locked` installs the pinned environment.
- `uv run stt transcribe <file> --output-dir <new-directory>` writes JSON, TXT, and SRT.
- `uv run stt benchmark <file> --output-dir <new-directory>` measures cold and warm runs.
- `uv run stt serve --port 8000` and `uv run stt worker` start the API and persistent worker in separate terminals.
- `uv run pytest` runs the ordinary suite with fake inference; integration tests are excluded by default.
- `uv run ruff check .`, `uv run ruff format --check .`, and `uv run mypy` lint, check formatting, and check production types.

For real-model acceptance, set `STT_TEST_MEDIA` to a local recording and run `uv run pytest -m integration tests/test_real_model.py tests/test_http_real.py -v`. This uses Whisper weights and launches local service processes.

## Style and Testing

Use four-space indentation, type hints, `snake_case` modules/functions, and `PascalCase` classes. Keep Thai UTF-8. Preserve the split between CLI/API, media validation, shared pipeline, engine, persistence, and exporters. JSON is canonical; derive TXT/SRT from it. Segment times follow the original recording timeline.

Name tests `test_*.py`. Cover CLI/API behavior with fake inference plus real filesystem/SQLite interactions; use real-model tests for engine contracts. No coverage threshold is set. Benchmark reports include hardware, versions, cold/warm timing, RTFx, and peak memory. Report CER/WER only against reviewed reference text with documented normalization and tokenization.

## Contributions and Data

The initial commit uses `docs:`. Use concise imperative prefixes such as `feat:`, `fix:`, `test:`, and `docs:`. Pull requests state scope, validation, evidence, and limitations; update the spec/tracker when decisions change.

Keep model weights, caches, uploads, databases, transcripts, and credentials outside Git, usually under `D:\ai-stt\`. Preserve sources and existing outputs; CLI destinations must be new and outside managed jobs/cache/lock paths. Update `uv.lock` with dependencies; retain `av<19` until faster-whisper supports newer PyAV.
