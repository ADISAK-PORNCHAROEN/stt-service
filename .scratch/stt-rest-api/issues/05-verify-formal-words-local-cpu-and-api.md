# 05 — Verify Formal Words transcription through the local CPU API

**What to build:** On the current computer, the approved Formal Words recording completes through the CPU transcription workflow and its result can be retrieved as JSON, TXT, and SRT and checked against the supplied 87-cue reference.

**GitHub issue:** [#6](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/6) · **Parent spec:** [#1](https://github.com/ADISAK-PORNCHAROEN/stt-service/issues/1)

**Blocked by:** None; acceptance is complete and GitHub issues #1 and #6 were closed with gh on 2026-10-25.

**Status:** Complete · **Ready for agent:** Done; GitHub issue #6 is closed.

- [x] Only the supplied full Formal Words MP4 and its matching reference are used for real-recording acceptance.
- [x] The existing CPU Whisper baseline runs locally; this ticket does not add CPU comparisons or profile experiments.
- [x] A local API Job reaches succeeded and provides complete JSON, TXT, and SRT without a second inference run.
- [x] The project owner approved all 87 reference cue texts and reference timings; no reference cue remains uncertain.
- [x] The project owner approved all 87 reference cues and the saved API transcript/subtitle timing after review under the documented policy.
- [x] The evidence distinguishes API/software completion from reference-backed accuracy and does not claim generalization beyond this recording.
- [x] Private audio, reference contents, model/cache data, and raw result bundles are not copied into GitHub issues or committed outputs.
- [x] No homelab connection, Docker deployment, public deployment, or GitHub Actions workflow is used.

**Validation evidence (2026-10-24):** The real integration test passed against the approved CPU baseline (`1 passed in 309.12s`): `uv run --env-file <external sanitized baseline env> -- python -m pytest -m integration tests/test_http_real.py -v --basetemp <external temp directory>`. It completed one local API Job and downloaded JSON, TXT, and SRT. The existing API result is bound to the approved recording by an explicit operator binding for a legacy result; the transcript does not independently prove inference provenance. Private source, reference, and result files remain outside Git.

**Reference and API review (2026-10-25):** The project owner approved all 87 reference cue texts/timings and approved the saved API transcript/subtitle timing. The saved API result was rescored under the documented policy without inference; no new CER/WER acceptance threshold was introduced. The report, review attestation, reference, and raw result bundle remain outside Git and GitHub. The transcript uses an explicit operator binding for a legacy result and has no embedded source hash; the binding and stored job input hash match the approved source.

**GitHub status:** The GitHub app integration rejected writes with `403 Resource not accessible by integration`. The authenticated gh CLI updated the public issue bodies and closed #6 and #1; readback confirmed both are closed. No audio, reference text, raw result bundle, or scores were added to GitHub.
