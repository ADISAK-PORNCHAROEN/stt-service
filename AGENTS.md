# Repository Guidelines

## Current State & Project Structure

This workspace contains planning documents and a user-provided MP4; application code, manifests, and tests do not exist yet. Read `STT-HANDOFF.md` for background. The agreed MVP uses Whisper Turbo for Thai/English transcription: CPU INT8, four threads, and segment timestamps.

Use the planned `src/stt_services/` package, `tests/`, and `benchmarks/reports/`. Separate CLI, configuration, schemas, pipeline, engine, and exporters. CLI and the API worker share the pipeline. Add a localhost-only FastAPI interface, SQLite queue, and one separate worker after the CLI baseline works.

Store the agreed spec, architecture, and dependency-ordered tickets under `.scratch/stt-mvp/` when created. Planned paths and commands are not existing implementation.

## Environment & Development Commands

Use Python 3.12 and uv with the repository-root `.venv` as the primary environment. Commit `uv.lock` once generated. After scaffolding, support:

- `uv sync` — install locked dependencies.
- `uv run stt transcribe <file> --output-dir <directory>` — transcribe locally.
- `uv run pytest` — run ordinary tests without models.
- `uv run ruff check .` — lint code.
- `uv run ruff format --check .` — verify formatting.

These commands are not configured yet. Use faster-whisper; this backend does not require PyTorch.

## Coding Style & Contracts

Use four-space indentation, type hints, snake_case functions/modules, and PascalCase classes. Use Ruff and preserve UTF-8 Thai text.

Keep inference independent of HTTP and persistence. Use JSON as the canonical transcript; derive TXT/SRT without rerunning inference. Timestamps reference the original recording in seconds. Preserve source files and publish only complete outputs.

## Testing Guidelines

Use pytest and httpx with `test_*.py` names. Exercise CLI/API behavior using a fake engine; separate real-model integration tests. Cover timestamps, exports, invalid uploads, queue limits, interrupted jobs, and cleanup. No coverage threshold is established.

Use the supplied MP4 for initial manual evaluation. Report hardware, versions, cold/warm timings, RTFx, and peak RAM. Report CER/WER only with reviewed reference text and documented normalization/tokenization.

## Contributions & Data

No Git history is available. Use imperative commit subjects; describe scope, validation, and limitations in pull requests.

Keep models, caches, API uploads, databases, and results under configurable `D:\ai-stt\` storage, except `.venv`. Set `HF_HOME` and `UV_CACHE_DIR` before downloads. Exclude private media, transcripts, credentials, and generated artifacts from version control.
