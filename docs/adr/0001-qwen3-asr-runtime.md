# ADR 0001: Run Qwen3-ASR through the official Python runtime

Status: Withdrawn — Qwen experiment cancelled
Date: 2026-10-17

This decision is retained for history only. The user stopped the experiment after CPU inference proved impractical for the current workflow; Qwen runtime code and dependencies have been removed. The downloaded model cache remains because automatic review blocked recursive deletion. Whisper remains the supported engine.

## Context

The repository is a Python 3.12/uv application on Windows with a shared `Engine`/`Pipeline` boundary and a configured Hugging Face cache on D:. Qwen3-ASR-0.6B is being evaluated as an additional CPU-capable model. The official package provides a Transformers backend; a third-party C implementation documents CPU BLAS paths for Linux and macOS but does not document a Windows build path. Qwen ASR itself does not provide Thai timestamps, and the official ForcedAligner does not list Thai support.

## Decision

Use the official `qwen-asr` Transformers backend as an optional dependency group in the existing `.venv`, run it on CPU, and prepare weights explicitly in the existing Hugging Face cache. Add Qwen as a CLI/benchmark engine behind the current pipeline boundary. Represent its output as full transcript text with unavailable timing and no segments; do not synthesize SRT timestamps. Keep the API and worker on Whisper until a separate design addresses untimed service results.

## Consequences

- The default Whisper installation and behavior remain unchanged; Qwen adds a sizable optional PyTorch dependency set.
- Model downloads are explicit and remain outside version control; benchmarks can identify the resolved model revision.
- Qwen users receive JSON/TXT but no SRT until Thai alignment is supported by an evaluated approach.
- CPU compatibility and quality on this Windows host must be demonstrated by an opt-in smoke run and measured comparison; documentation alone is not acceptance evidence.
