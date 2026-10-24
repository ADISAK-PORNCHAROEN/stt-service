# Qwen3-ASR 0.6B Local Transcription Spec

**Status: Cancelled.** The Qwen experiment was stopped by user decision after CPU inference proved impractical for this workflow. Whisper remains the supported engine. The speech/music evaluation is incomplete, so this spec is retained as a historical record only.

This is a new, separate follow-up to the accepted Whisper MVP. It does not replace or revise the existing MVP spec or tickets 01–06. Its first release adds Qwen as a CLI/benchmark experiment only; the existing API and worker continue to use Whisper.

## Problem Statement

The local Whisper pipeline works for Thai and English, but the user wants to evaluate Qwen3-ASR-0.6B, particularly on music, and needs a maintainable way to download and run it without creating a second transcription application. The current engine contract requires timed segments, while Qwen's ASR output provides full text without Thai alignment timestamps.

## Solution

Add Qwen3-ASR-0.6B as an optional engine in the existing Python 3.12/uv environment and shared CLI pipeline. Let the user explicitly prepare the model in the existing Hugging Face cache on D:. Keep full transcript text independent from timed segments. Qwen results produce JSON and TXT with no segments or SRT; Whisper output and behavior remain unchanged. Evaluate Qwen on the same speech and music recordings used for Whisper review before considering service support.

## User Stories

1. As a local operator, I can keep using Whisper with the current configuration and commands without installing Qwen-specific dependencies.
2. As an operator trying Qwen, I can install its optional runtime into the existing repository `.venv` with uv rather than maintaining a second application environment.
3. As an operator managing disk space, I can explicitly download Qwen3-ASR-0.6B before transcription and keep its weights in the configured Hugging Face cache outside the repository.
4. As an operator on a disconnected or unreliable network, I receive a clear missing-cache or download error before inference rather than a partially completed result.
5. As a local user, I can select `qwen` through `.env.local` for CLI transcription and benchmarks while Whisper remains the default engine.
6. As a user reading a Qwen result, I can see the complete UTF-8 Thai/English recognition in JSON and TXT even though Qwen supplies no segment timestamps.
7. As a subtitle user, I am not given fabricated SRT timings; an untimed result clearly indicates that timing is unavailable and omits the SRT artifact.
8. As a Whisper user, I continue to receive the existing full text, timed segments, JSON, TXT, and SRT with the same timeline restoration behavior.
9. As an operator, I can reuse a loaded Qwen model for cold and warm runs within one benchmark process and inspect the selected engine, model revision, runtime versions, CPU configuration, timing, and peak process RAM.
10. As an operator, I cannot accidentally start the existing API or worker with Qwen selected before those entry points support untimed results; the command explains the current limitation.
11. As a maintainer, I can test engine selection, downloads, text-only exports, and failures with fake engines/mocked Hub calls without network access or model weights.
12. As a model evaluator, I can compare Qwen and Whisper on the same speech and music recordings, review the output against the supplied lyric reference, and report observations without claiming unmeasured accuracy.

## Implementation Decisions

- Use the official `qwen-asr` Python package with its Transformers backend on CPU in the existing uv-managed `.venv`. Keep Qwen dependencies optional so the default Whisper installation does not gain PyTorch and its transitive packages. Resolve and lock compatible package versions through `uv.lock`. Do not use vLLM, a second Python environment, or the third-party C runtime in this scope.
- Add a model-neutral engine result carrying full `text` plus zero or more timed `segments`. A transcript records whether timing is available. Whisper continues to return timed segments and preserve current source-timeline mapping; Qwen returns recognized text with no segments and unavailable timing.
- Keep the canonical JSON shape compatible with existing fields: Qwen uses a full `text`, an empty `segments` list, and transcript-level `timing_source="unavailable"`. Timed Whisper transcripts retain `timing_source="model"`. TXT is written from canonical transcript text. SRT is written only when timing is available; an empty Whisper transcript still follows the current timed-engine export behavior.
- Add `STT_ENGINE` with `whisper` as the default and `qwen` as the opt-in value. The CLI and benchmark honor it. `serve` and `worker` reject `qwen` with an actionable message until a separate API/worker spec enables that path. Qwen metadata must not report Whisper-only configuration or package versions.
- Provide an explicit `stt model download qwen3-asr-0.6b` preparation command. It fetches the official `Qwen/Qwen3-ASR-0.6B` repository into the configured Hugging Face cache (defaulting under `[private local path]`), reports the resolved revision, and is safe to repeat. Inference requires the prepared local snapshot and explains how to download it if absent. Never place weights or private transcripts in version control.
- Keep the existing fake-engine CLI/Pipeline boundary as the primary test seam. Model loading and Hugging Face calls are isolated behind the Qwen adapter and mocked for ordinary tests. Real CPU inference is an explicit smoke/benchmark check.
- Do not change the existing Whisper MVP's behavior, API contracts, worker lifecycle, or six completed ticket records. Keep Qwen decisions and issues in this feature namespace.

## Testing Decisions

- Prefer observable public CLI/Pipeline behavior over assertions about internal adapter helpers. Existing `tests/test_cli.py`, `tests/test_contracts.py`, and `tests/test_real_model.py` provide prior art for fake-engine outputs, timing invariants, and explicitly opted-in real-model checks.
- Ordinary tests cover the default Whisper path, Qwen selection, JSON/TXT full text with no segments, omitted SRT, unchanged Whisper SRT, empty speech, output atomicity, CLI rejection by `serve`/`worker`, cache-missing diagnostics, repeatable model preparation, and dependency/load/download failures. They must not download weights or require Qwen packages.
- Run `uv run pytest`, Ruff lint/format checks, and mypy. Add a separately opted-in Qwen CPU smoke check that requires the optional dependency group and downloaded model.
- The model evaluation reports the exact model revision, package versions, host/hardware, cache/download state, cold/warm time, inference and wall RTFx, and peak process RSS. Compare like-for-like recordings and manually review Thai/English text. Use the user-supplied lyric reference when available; compute CER/WER only with documented reference normalization and tokenization. No numeric quality or speed threshold is approved in this spec.

## Out of Scope

Qwen support in FastAPI or the worker; Thai forced alignment, segment/word timestamps, or SRT generation for Qwen; Whisper-assisted alignment; vLLM/streaming; C-runtime or GPU execution; model training/fine-tuning; automatic model downloads during transcription; UI; and claims that Qwen is more accurate or faster without recorded evidence.

## Further Notes

Qwen's official model documentation lists Thai and singing/music among supported inputs, but this is not evidence of accuracy on the user's recordings. It documents the `qwen-asr` Transformers backend and explicit Hugging Face download path: [Qwen3-ASR repository](https://github.com/QwenLM/Qwen3-ASR) and [Qwen3-ASR-0.6B model card](https://huggingface.co/Qwen/Qwen3-ASR-0.6B). Its ForcedAligner language list does not include Thai, which is why this release does not promise timed output. The C inference alternative currently documents CPU BLAS support for Linux/macOS without a Windows build path: [antirez/qwen-asr](https://github.com/antirez/qwen-asr).

The planned operator flow is to set `UV_CACHE_DIR` before syncing (uv does not read `.env.local` during sync), install the optional Qwen group into the repository `.venv`, then use `uv run --env-file .env.local stt model download qwen3-asr-0.6b`. Set `STT_ENGINE=qwen` in the ignored local environment only after preparation; removing or setting it to `whisper` keeps the current engine selected. The implementation must document exact commands after the optional group and CLI entry point are added.
