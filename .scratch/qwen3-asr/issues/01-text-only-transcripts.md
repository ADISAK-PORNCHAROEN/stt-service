# 01 — Support text-only transcripts in the CLI

**Ticket ID:** QW-01  
**What to build:** Let a CLI transcription produce a complete readable transcript when its engine returns text without timed segments, while preserving Whisper's existing timed result bundle.  
**Blocked by:** None (can start immediately).  
**Status:** Cancelled  
**Ready for agent:** No — cancelled

Cancelled by user decision when the Qwen experiment was stopped. The implementation and its tests were removed; the prior validation below is historical and does not describe the current repository.

Triage label: `cancelled`

- [x] The shared engine/pipeline result keeps canonical full text independently from its optional timed segments and records whether timing is available.
- [x] The CLI publishes UTF-8 JSON and TXT for an untimed transcript, with an empty segment list and clear timing provenance; it does not publish an SRT artifact without timing.
- [x] Whisper's timed JSON/TXT/SRT, original recording offsets, and successful empty-speech behavior remain unchanged.
- [x] Fake-engine CLI tests cover text-only output, untimed export behavior, and regressions for existing Whisper-style results without downloading a model.
- [x] Ordinary pytest, Ruff lint/format, and mypy checks pass.

## Validation

`uv run --env-file .env.local pytest -q` passed (88 passed, 2 deselected); Ruff lint and format checks and mypy passed.
