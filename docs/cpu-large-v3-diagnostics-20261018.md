# Residual recognition diagnostics on CPU — 18 October 2026

Status: In progress. The owner's quality-repair goal is not complete merely
because the earlier Turbo profiles removed corruption/repetition symptoms.
The [Turbo correction and real-progress evidence](cpu-quality-progress-20261018.md)
remains valid; residual word/name errors motivated this follow-up.

## Decision and scope

After three serial Turbo profile trials, the agent selected an isolated
`large-v3` trial using the existing faster-whisper engine and CPU INT8. This is
an evidence-backed diagnostic under the owner's newer quality goal, separate
from the initial Turbo-only optimization delivery. It is not a final model
promotion, a Qwen restart, a new backend, or model training. Only the same two
full approved originals are authorized; no extracts or other recordings enter
these trials. Original references and all prior artifacts are preserved.

OpenAI reports larger Turbo degradation for Thai in its [release announcement](https://github.com/openai/whisper/discussions/2363).
That motivates testing rather than proving the cause or promising a gain on this
recording. Native weights for `Systran/faster-whisper-large-v3` were prepared in
the existing external Hugging Face cache before service timing; model revision
is `edaa852ec7e145841d8ffdb056a99866b5f0a478`. No GPU inference is used.

## Trial 04 — large-v3 without prompt

Settings match Turbo experiment 01 except for the model: CPU INT8, four threads,
beam five, temperature zero, previous-text context on, automatic language,
sequential batch one, baseline VAD, and no n-gram constraint or vocabulary hint.
Profile: `whisper-profile-v1-b321dedfc3f2c25d2890`.

Formal Words passed the real separate-process HTTP test in 562.82 seconds.
Internal pipeline time was 541.890 seconds, with 42 segments and approximately
3.070 GB sampled process RSS. These are single functional observations, not an
isolated performance comparison. The final poll was succeeded/100 at 542.5 seconds
after acceptance; intermediate progress was observed and `/health` returned 200
with a fresh heartbeat during inference.

Thai orthography improved in inspected passages, but the result omits several
spoken English terms present in the unreviewed publisher's mixed-language lines.
This is a regression concern, not a balanced quality acceptance. Kob has not been
run under trial 04; the profile was not selected for deployment.

Private evidence:

- [Formal TXT](<[private local path]>) and [SRT](<[private local path]>).
- [Frozen plan](<[private local path]>) and [mid-inference readiness](<[private local path]>).

## Trial 05 — generic bilingual prompt

Only a short generic Thai/English initial prompt
changes from trial 04. It contains no answer words from either recording or
publisher reference. The aim is to test English retention while preserving the
Thai spelling improvement. Prompt details remain in the [external frozen plan](<[private local path]>).

Formal Words passed the real HTTP test in 480.30 seconds, with internal pipeline
time 461.752 seconds. All four inspected English lexical probes recovered to the
counts present in the temperature-zero Turbo tuning result, alongside the Thai
orthography improvement. These are tuning diagnostics against an unreviewed
publisher reference, not CER/WER or a whole-file quality pass.

Profile `whisper-profile-v1-2d2b6edb52f35ad772a8` was frozen after that
inspection and before the full-original Kob run. Kob passed the separate-process
HTTP test in 1695.55 seconds (internal pipeline: 1677.641 seconds); polling ended
at succeeded/100. The result still has substantial word errors in the opening,
the glasses discussion and code-switched passages. The model was not promoted.
The test driver supports optional `STT_TEST_JOB_TIMEOUT_SECONDS` in (0, 14400],
retaining the 1800-second default; this run used 5400 seconds. That timeout is a
functional-test allowance, not latency acceptance. Production source did not
change between the large-v3 runs.

Private evidence: [Formal TXT](<[private local path]>) and [SRT](<[private local path]>); [Kob TXT](<[private local path]>) and [SRT](<[private local path]>).
The external [inspection script](<[private local path]>) completed the two-original binding, source hashes, profile/revision, canonical exports and progress checks.

## Thai-specific and code-switching candidates

Trial 06 tested the native CTranslate2 conversion of
`biodatlab/distill-whisper-th-large-v3` at revision
`8c2a2e1caf92c41fb01e3a67f99a473e9817edfa`. Its generic bilingual prompt and CPU
settings passed the full Formal HTTP test in 161.52 seconds, but the transcript
contained long repetitions and rendered spoken English terms phonetically in
Thai. It was rejected before a Kob run. The [upstream model card](https://huggingface.co/biodatlab/distill-whisper-th-large-v3)
warns about performance on other languages.

The [NECTEC Pathumma FastConformer-RNNT model](https://huggingface.co/nectec/Pathumma-stt-th-fastconformer-rnnt-large)
is explicitly trained for Thai-English code-switching and documents CPU inference.
Its unofficial [INT8 ONNX conversion](https://huggingface.co/chanasia/Pathumma-stt-th-fastconformer-rnnt-large-int8)
was inspected and run through ONNX Runtime's CPU provider with four threads. The
conversion has greedy decoding and no timestamps. Formal retained mixed-language
phrases, while Kob still had repetitions and missed the spoken glasses term. Kob
was processed from the full authorized source in memory using Silero VAD ranges;
the 26-range and 60-range plans both preserved source timing and created no audio
files. This candidate was not integrated or promoted. Full text and progress
observations remain in the private experiment 06 directory.

An additional CPU-only experiment loaded the official NECTEC `.nemo` checkpoint at revision
`066561cf32838bb25954b9338ddd247df981d7c0` with Python 3.12, PyTorch 2.7.1 CPU,
NeMo Toolkit 3.0.0 and four CPU threads in an external Windows virtual environment.
The full 597.96-second Kob waveform ran in memory and took 512.106 seconds; its
long-input SRT collapsed to one segment cue. A second pass used the same full source
and 57 in-memory Silero VAD chunks (500 ms minimum silence), producing 182
character-timestamp SRT cues in 23.848 seconds. Source SHA-256 matched before and
after both passes. Chunking improved runtime substantially on this workstation, but
did not fix the priority recognition errors: the glasses term remained `วันตา`,
`polyglot` remained phonetically garbled, and the `flow` and `Frisbee` passages still
contained insertions or repetition. The candidate was not integrated or promoted;
these workstation timings do not predict performance on the owner's home server.
The [private NeMo comparison and artifacts](<[private local path]>)
record the full transcript, SRT, selected VAD passages, model revision and limits.

The two original MP4 files are stereo, but both channels are almost identical
(correlations 0.9997 and 0.999999); averaging them changes RMS by less than
0.001 dB. This rules out channel cancellation as the cause of the observed errors.
See the private [full-source channel observations](<[private local path]>).

## Decoder-width and prompt checks

Trial 07 changed Turbo's beam size from five to ten, keeping temperature zero,
previous-text context, n-gram size eight and CPU INT8. The real HTTP tests passed
for Formal in 227.63 seconds and Kob in 599.77 seconds; Kob's final progress trace
ended succeeded/100. Beam ten kept more readable `flow` text and recovered some
Formal spellings, but Kob still rendered the glasses term as `วันตา`, as did the
beam-five and large-v3 results. Kob inference increased from 441.086 to 591.627
seconds, with no broad accuracy gain established. This profile was not promoted.

Trial 08 added only the generic bilingual prompt to the beam-ten Formal profile.
Formal passed in 237.61 seconds; the inspected English probes were unchanged and
there was no clear quality gain. No Kob run was made under this prompt. It was
not selected.

The ignored local `.env.local` selects Turbo, beam five, CPU INT8, temperature
zero, previous-text context, n-gram size eight and VAD minimum silence 500 ms.
This experimental selection is not a production promotion; the Python default
and approved baseline retain VAD 2,000 ms. Trial 15 also tested context off with
VAD 500 ms and n-gram size eight; it did not establish a balanced improvement.
All recorded runs used CPU only; no result measures the owner's home server. References remain
unreviewed publisher material. Human review and a balanced full-recording quality
acceptance remain pending; no CER/WER or whole-file accuracy claim is made.

## Language-mode and prompt checks

Trial 09 changed only `language_mode` from `auto` to
`multilingual_per_window` for a full Kob API/worker run. It passed in 437.53 seconds,
with progress ending succeeded/100. All 322 segment texts matched the selected
baseline byte for byte; inference was 423.981 seconds versus 440.077 seconds for
baseline. Treat the small timing difference as run variation, not a quality gain.

Trial 10 changed only `language_mode` to forced Thai. It passed in 448.71 seconds,
with succeeded/100. All 322 segment texts again matched baseline byte for byte;
inference took 437.067 seconds. Neither language mode changed recognition, so both
candidates were rejected.

Trial 11 changed only the generic bilingual `initial_prompt`. The full API/worker
test passed in 511.95 seconds and progress remained monotone through succeeded/100,
but quality regressed sharply: the output grew from 322 baseline segments to 580,
with 569 segments repeating `And we're wearing glasses.` The prompt profile was
rejected and remains only in external diagnostics.

Full results and progress traces for trials 09–11 remain under
`[private local path],10,11}/`. The private [Kob passage comparison](<[private local path]>) places five source-timed excerpts beside the CPU candidates and unreviewed publisher subtitles. The [official NeMo comparison](<[private local path]>) records its full-input and VAD-chunk results.

## Hotword and VAD checks

Trial 12 added only the user-provided guest-name hotword `Kob`. The full CPU
API/worker test passed in 467.25 seconds and progress reached succeeded/100, but
the output regressed sharply: one 30-second segment repeated fragments, and the
result had 263 segments versus 322 in baseline. Reject this hotword profile.

Trial 13 changed only VAD minimum silence from 2,000 to 500 ms on Kob. The full
API/worker test passed in 470.53 seconds; progress reached succeeded/100. The
selected flow passage contained fewer malformed repeats and Frisbee terms remained
recognizable, but the glasses word was still wrong. Kob inference rose from
440.077 to 458.689 seconds. This is a candidate for human review, not a proven
quality improvement.

Trial 14 checked the same VAD setting on full Formal Words. The real API/worker
test passed in 161.22 seconds with succeeded/100; inference fell from 188.915 to
153.672 seconds. Text changed across 156 segment positions. Human review and the
existing repeated warm-run and quality gates remain open. The local experimental
profile now selects 500 ms; the Python default and approved baseline stay at
2,000 ms. Trial 15 compared context off against the VAD 500 ms Kob result: it
passed in 379.89 seconds, but the glasses term remained wrong and English `flow`
rendering regressed to Thai-script spellings in the selected passage. It was not
promoted. The private [Kob comparison pack](<[private local path]>)
links results and progress traces for trials 12–14. See the private [trial 15
review](<[private local path]>) and
its progress/results under `[private local path]`.
Trial 16 repeated the local VAD 500 ms profile on full Kob. It passed in 455.28
seconds with succeeded/100; all 320 segment records and TXT/SRT bytes exactly
matched trial 13. This demonstrates run-to-run stability on this workstation,
not accuracy. Its [private review](<[private local path]>)
contains the hashes and progress trace.

Trials 17 and 18 tested Turbo beam 1 and 3 on full Kob through the real
API/worker. Both reached succeeded/100 with monotone progress. Beam 1 inference
took 257.880 seconds but kept the `วันตา` error; beam 3 took 357.794 seconds and
fragmented the English `flow` passage into `Flo`/`Satana`. Neither is promoted.
See the private [beam-1 review](<[private local path]>)
and [beam-3 review](<[private local path]>).

Trial 19 tried a short prompt containing only candidate-transcript vocabulary
(`Polyglot. Flow. Frisbee.`), not publisher-reference text. The full Kob
API/worker test passed in 456.40 seconds with succeeded/100. It did not correct
the glasses or polyglot phrases and changed English `flow` into Thai phonetic
text with repeated `สาธานะ` cues. Reject the prompt. Its [private review](<[private local path]>)
links the full output and progress trace.
