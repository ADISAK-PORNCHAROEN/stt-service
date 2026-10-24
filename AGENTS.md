# STT Services Agent Guide

This project transcribes Thai and English recordings with Whisper Turbo on CPU and exposes both a CLI and a localhost job service. Python 3.12, uv, the root `.venv`, and the committed lockfile define the development environment.

## Working agreements

- Preserve the split between CLI/API, media validation, shared pipeline, engine, persistence, and exporters. JSON remains canonical; TXT and SRT are derived from it. Segment times refer to the original recording.
- Keep Thai text in UTF-8. Use four-space indentation, type hints, `snake_case` functions/modules, `PascalCase` classes, and `test_*.py` test names.
- Before behavior changes, read `.scratch/stt-mvp/spec.md`, `.scratch/stt-mvp/architecture.md`, `docs/agents/issue-tracker.md`, and `CONTEXT.md`; read the active optimization spec and ticket when working on that effort.
- Use `uv` and the repository-root `.venv`. Copy `.env.local.example` to the ignored `.env.local` for machine-specific paths and pass it with `uv run --env-file .env.local`. Keep model weights, caches, databases, uploads, transcripts, credentials, and other runtime data outside Git.
- Do not run `uv sync` until `UV_CACHE_DIR` has been loaded from `.env.local` into the PowerShell environment. Keep `av<19` until faster-whisper supports newer PyAV.
- Before handoff, run the required checks in `docs/TESTING.md` for the changed behavior. Preserve external destinations and existing outputs; CLI output directories must be new and outside managed jobs/cache/lock paths.
- Keep local experimental profiles and approved baselines distinct. Update the canonical spec and tracker when accepted decisions or ticket status change; do not infer recognition acceptance from software checks alone.
- Update `uv.lock` with dependency changes. Benchmark reports record the hardware, software/model versions, and timing/resource fields required by the active ticket; identify whether timing includes model loading or warm reuse. Repeated comparisons are needed only for repeatable performance-improvement claims. Report CER/WER only against reviewed reference text with documented normalization and tokenization.
- Use concise imperative commit prefixes such as `feat:`, `fix:`, `test:`, and `docs:`. Handoffs state scope, validation, evidence, and limitations.
- Keep task-specific restrictions in the task record. Do not publish, deploy, operate production systems, or send external data unless the user authorized that action.

## Find the source

- Start at `src/stt_services/cli.py` for CLI commands and `src/stt_services/api.py` for HTTP routes.
- Follow media admission through `uploads.py` and `audio.py`; shared inference and output through `pipeline.py`, `engines/whisper.py`, `schemas.py`, and `exporters.py`.
- Follow durable jobs and lifecycle through `jobs.py` and `worker.py`; read `config.py` for environment-backed settings.
- Optimization workflows start at `evaluation.py`, `comparison.py`, and `references.py`. Confirm paths and callers against current source; use targeted `rg` searches when a route is unclear.
- The implementation boundaries and generated API contract are summarized in `docs/ARCHITECTURE.md` and `docs/API.md`; detailed MVP ownership remains in `.scratch/stt-mvp/architecture.md`.

## Read by task

| Task | Read first |
| --- | --- |
| Product behavior or acceptance | `PRODUCT.md`, `.scratch/stt-mvp/spec.md`, and the active feature spec/ticket |
| Domain terms | `CONTEXT.md` |
| Architecture or integration | `docs/ARCHITECTURE.md` and `.scratch/stt-mvp/architecture.md` |
| HTTP/API behavior | `docs/API.md`, `src/stt_services/api.py`, and `schemas.py` |
| Persistence or retention | `docs/SCHEMA.md`, `jobs.py`, and `worker.py` |
| Tests and quality checks | `docs/TESTING.md` and `.agents/skills/test-engineering/SKILL.md` |
| Any application code change | `.agents/skills/test-engineering/SKILL.md` and `.agents/skills/security-review/SKILL.md` |
| Security-sensitive change | `SECURITY.md`, `docs/SECURITY-MODEL.md`, and `.agents/skills/security-review/SKILL.md` |
| Specs, tickets, or workflow handoff | `docs/agents/issue-tracker.md`, the current `.scratch/<feature>/spec.md` and issue files, and `docs/agents/tools.md` |
| AI workflow setup or instruction maintenance | `docs/agents/tools.md`, `.agents/skills/ai-project-foundation/SKILL.md`, and `docs/AI-FOUNDATION-REPORT.md` |

## Completion

Report what changed, why, the exact checks actually run, and any limits or unresolved acceptance. Keep source inspection, AI review, native command results, and real-recording evidence distinct. Preserve the existing working tree and never claim a check or host behavior that was not observed.
