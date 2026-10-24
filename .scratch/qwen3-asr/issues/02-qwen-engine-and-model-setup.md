# 02 — Add the Qwen engine and explicit model preparation

**Ticket ID:** QW-02  
**What to build:** Let the operator prepare Qwen3-ASR-0.6B locally and select it for CLI transcription and benchmarks through the existing settings, without disrupting Whisper defaults.  
**Blocked by:** QW-01 — Support text-only transcripts in the CLI.  
**Status:** Cancelled  
**Ready for agent:** No — cancelled

Cancelled by user decision because CPU-only Qwen inference was impractical for this workflow. Runtime code and dependencies have been removed; the model cache remains at `[private local path]` because automatic review blocked recursive deletion. Whisper remains supported.

Triage label: `cancelled`

- [ ] The official `qwen-asr` Transformers runtime is an optional uv dependency group in the existing `.venv`; default Whisper installation remains usable without it.
- [ ] `stt model download qwen3-asr-0.6b` prepares `Qwen/Qwen3-ASR-0.6B` in the configured Hugging Face cache, reports the resolved revision, and succeeds safely when repeated.
- [ ] `STT_ENGINE=qwen` selects a persistent CPU Qwen adapter for CLI transcription and cold/warm benchmark runs; default selection remains Whisper.
- [ ] Qwen JSON/TXT output contains the full recognized text, no invented timing, and engine/model/runtime metadata appropriate to Qwen.
- [ ] Selecting Qwen for `serve` or `worker` fails with a clear explanation that those entry points still require Whisper.
- [ ] Fake-engine and mocked-download tests cover selection, missing optional runtime, missing cache, download failures, and model reuse without accessing the network.
- [ ] A real, opt-in CPU smoke transcription succeeds on a short local recording; private audio and weights stay outside version control.
- [ ] Setup and `.env.local` example instructions explain uv installation, cache location, model preparation, and switching back to Whisper.
