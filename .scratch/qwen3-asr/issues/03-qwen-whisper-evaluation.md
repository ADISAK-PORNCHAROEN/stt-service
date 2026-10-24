# 03 — Evaluate Qwen against the Whisper baseline

**Ticket ID:** QW-03  
**What to build:** Give the user reproducible evidence about Qwen recognition and resource use on the same local speech and music recordings used for Whisper review.  
**Blocked by:** QW-02 — Add the Qwen engine and explicit model preparation.  
**Status:** Cancelled  
**Ready for agent:** No — cancelled

Cancelled by user decision after the CPU Qwen experiment proved impractical. The planned comparison was not completed; do not treat it as benchmark evidence.

Triage label: `cancelled`

- [ ] Run cold and warm Qwen benchmarks on the existing speech baseline and the supplied music recording; record exact model/runtime revisions and hardware.
- [ ] Compare Qwen and Whisper full text on the same recordings, including manual review against the supplied lyric reference when available.
- [ ] Record cache/download state, CPU settings, model-load/inference/full-call times, RTFx, peak process RSS, text observations, and limitations in a sanitized versioned report.
- [ ] Keep media, raw transcripts, and benchmark output outside the repository; commit no private recordings or model weights.
- [ ] Make no accuracy/speed claim or CER/WER claim without reviewed reference text and documented normalization/tokenization; this ticket sets no numeric acceptance threshold.
