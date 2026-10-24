# 05 — Verify Formal Words transcription through the local CPU API

**What to build:** On the current computer, the approved Formal Words recording completes through the CPU transcription workflow and its result can be retrieved as JSON, TXT, and SRT and checked against the supplied 87-cue reference.

**GitHub issue:** [#6](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/6) · **Parent spec:** [#1](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/1)

**Blocked by:** Human review of the supplied 87-cue Formal Words reference; implementation ticket #5 is complete.

**Status:** Blocked · **Ready for agent:** No; reference review remains pending.

- [x] Only the supplied full Formal Words MP4 and its matching reference are used for real-recording acceptance.
- [x] The existing CPU Whisper baseline runs locally; this ticket does not add CPU comparisons or profile experiments.
- [x] A local API Job reaches succeeded and provides complete JSON, TXT, and SRT without a second inference run.
- [ ] The result is checked against the supplied reference under the documented review/scoring policy; unchecked cues, uncertain speech, and timing limits remain explicit.
- [x] The evidence distinguishes API/software completion from reference-backed accuracy and does not claim generalization beyond this recording.
- [x] Private audio, reference contents, model/cache data, and raw result bundles are not copied into GitHub issues or committed outputs.
- [x] No homelab connection, Docker deployment, public deployment, or GitHub Actions workflow is used.

**Validation evidence (2026-10-24):** The real integration test passed against the approved CPU baseline (`1 passed in 309.12s`): `uv run --env-file <external sanitized baseline env> -- python -m pytest -m integration tests/test_http_real.py -v --basetemp <external temp directory>`. It completed one local API Job and downloaded JSON, TXT, and SRT. Offline reference preparation/rescoring remains `pending_review`; 0/87 cue text and timing checks are marked reviewed, so CER/WER and recognition acceptance remain unclaimed. Private source, reference, and result files remain outside Git.
