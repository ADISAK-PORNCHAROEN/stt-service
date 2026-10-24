# CPU quality correction and real progress — 18 October 2026

The owner requested improved transcription, especially Conversation with Kob,
and verification of job progress using the real model. The corrective software
and real-progress checks are complete. The local machine selects an experimental
CPU profile based on the observed corruption/repetition symptoms below. This is
not full-recording accuracy acceptance or final OPT profile promotion.

## Applied local profile

The ignored `.env.local` now contains:

```dotenv
STT_TEMPERATURE_ZERO=true
STT_CONDITION_ON_PREVIOUS_TEXT=true
STT_NO_REPEAT_NGRAM_SIZE=8
STT_VAD_MIN_SILENCE_DURATION_MS=500
```

Resolved identity: `whisper-profile-v2-56a4fc7db42bc732c76b`. The actual local
settings were checked against the profile embedded in the successful real HTTP
result. Other settings remain Turbo, CPU INT8, four threads, beam five, automatic
language, sequential batch one, VAD, and a 30-second model window. The backend
reported CPU `int8_float32`. No GPU inference was used or required. This is a
local experimental selection based on two identical Kob runs and one Formal
check; the Python default and approved baseline still use 2,000 ms VAD silence.

The new bounded `STT_NO_REPEAT_NGRAM_SIZE` setting accepts 0–20; zero disables
the decoder constraint. Both sequential and batched adapters forward and report
the actual value. Zero preserves existing schema-v1 public profiles and their
hashes, including baseline `whisper-profile-v1-24b36874898eeab9e274`; nonzero
values use schema v2. The offline comparison rejects a nonzero setting as the
approved CPU baseline. Python defaults remain the existing baseline, and no
existing result or profile is rewritten.

These settings apply when CLI/API/worker processes next start with `.env.local`.
Existing persistent workers must restart to load a changed startup profile.
To restore the original baseline, set temperature-zero to false and the n-gram
size to zero, retain previous-text context true, and set
`STT_VAD_MIN_SILENCE_DURATION_MS=2000`.

## Observed quality symptoms

Only the two authorized full originals were processed. Source identities and
hashes were checked; originals, references and prior outputs were preserved.
No publisher answer text was supplied as a prompt or hotword. No recognized text
was removed, replaced, or automatically corrected after inference.

| Kob profile | U+FFFD count | Letters outside Thai/Latin | Repeated-motif segments |
| --- | ---: | ---: | ---: |
| Preserved original baseline | 4 | 38 | 0 |
| Temperature zero, context on | 0 | 0 | 1 |
| Temperature zero, context off | 0 | 0 | 2 |
| Temperature zero, context on, n-gram 8 | 0 | 0 | 0 |

The detector flags a 1–12-character motif repeated at least six times within
one segment. Its counts are diagnostics, not accuracy scores or proof that all
repetition is absent. Genuine repetitions can also match such a detector.

Temperature zero removed the observed replacement characters and unexpected
scripts, but introduced a repeated-text symptom around 119.94 seconds. Disabling
context was rejected: it produced long repetitive segments at 119.98–149.98 and
403.04–433.04 seconds. The n-gram-8 trial has no detector flags and contains
continuous text through these intervals, including spoken English terms. The
private review pack preserves publisher lines beside the candidate for checking.
Formal Words has zero replacement/unexpected-script letters and no detector
flags under all three experimental profiles.

Spelling, names, phonetic substitutions and some English/Thai orthography remain
imperfect. The n-gram constraint can suppress legitimate repeated phrases and
alter word choices; selected examples show residual errors. Do not treat absence
of these corruption symptoms as a full quality pass. Human speech/timing review,
reviewed references and CER/WER acceptance remain pending. Kob has prior exposure,
including the repetition diagnosis, and is not an untouched holdout. The broader
OPT tickets remain at their existing acceptance gates. OpenAI also reports larger
Turbo degradation for Thai in its [model announcement](https://github.com/openai/whisper/discussions/2363);
that supports caution, not a diagnosis of every remaining error in this recording.

## Private result bundles and evidence

The selected experimental results are actual downloads from separate API and
worker processes using the real cached Turbo model:

- Formal Words: [TXT](<[private local path]>) and [SRT](<[private local path]>).
- Conversation with Kob: [TXT](<[private local path]>) and [SRT](<[private local path]>).
- [All candidate diagnostics, result hashes and progress observations](<[private local path]>).
- [Kob review pack with unreviewed publisher lines](<[private local path]>).

Experiments 01 and 02 are preserved alongside experiment 03 under external
`[private local path]`. Each has a frozen plan and an
inspection script. The final script validates canonical JSON/TXT/SRT consistency,
original-timeline bounds/order, unchanged model/runtime versions, uploaded-copy
hashes, and monotone progress ending at succeeded/100. HTTP transcripts use managed
source names; the source binding is established by uploaded-copy hashes and test
preflight rather than an embedded original-source hash. The inspected production
source fingerprints were unchanged during the real-model runs.

## Real progress verification

`tests/test_http_real.py` now records every polled status to external
`progress.jsonl` and asserts integer bounds, monotonicity, intermediate progress,
100 only with success, successful downloads in all formats, original timeline
bounds, readiness and zero per-job model reload time. It checks that owned service
processes remain alive throughout polling and cleans them up after each test.

Four actual HTTP test invocations passed, using both full originals under both
the temperature-zero and n-gram-8 profiles. Selected-profile evidence:

| Recording | HTTP test elapsed | Poll samples | Last observed job state |
| --- | ---: | ---: | --- |
| Formal Words | 201.87 s | 375 | succeeded, 100% |
| Conversation with Kob | 451.36 s | 873 | succeeded, 100% |

Both traces include zero and intermediate percentages. Kob also contains an
observed running/99 sample before succeeded/100. HTTP test elapsed includes test
startup/readiness, submission, polling and downloads; it is not model-only time
or an isolated benchmark. Internal transcript totals were 189.252 and 441.086
seconds and stop before final metrics serialization/rename. No speed multiplier,
real-time acceptance or home-server measurement is claimed.

Commands were run from the repository root with `.env.local`. For each original,
the first profile set `STT_TEMPERATURE_ZERO=true`; the final profile additionally
set context true and `STT_NO_REPEAT_NGRAM_SIZE=8`. Every invocation used:

```powershell
# Set STT_TEST_MEDIA to the matching authorized full original.
uv run --env-file .env.local pytest -m integration tests/test_http_real.py --basetemp '<new external directory>' -v
```

Exact basetemp directories were experiment 01/03 `formal-http` and `kob-http`
as linked above. First-profile tests passed in 217.61 and 524.73 seconds. The
context-off diagnostic instead used `stt transcribe <authorized original>
--approved-only --output-dir <new external directory>` for each full original;
both completed, and that profile was rejected for repetition.

## Follow-up model and decoder diagnostics

Further complete-original CPU experiments are recorded in the [residual quality report](cpu-large-v3-diagnostics-20261018.md). Large-v3 plus a generic prompt passed the HTTP test for both approved sources, but Kob still contains material Thai and code-switching errors and took 1695.55 seconds end to end. A Thai-only Whisper conversion produced repetition on Formal. A Thai-English Pathumma INT8 ONNX model ran through the CPU provider and retained several English phrases, but it still missed key Kob words; it has no timestamps in the tested conversion and was not integrated.

The official NECTEC NeMo checkpoint was also tested on CPU at pinned revision
`066561cf32838bb25954b9338ddd247df981d7c0`. On this workstation, the full Kob
waveform took 512.106 seconds as one input. Processing the same source in 57
in-memory VAD chunks took 23.848 seconds and generated a full TXT/SRT pair with
182 grouped character-timestamp cues. The chunked transcript still misheard the
glasses term and retained code-switching errors, so this speed result did not justify
changing the selected Whisper profile. No audio chunks were written, and the source
hash remained unchanged. These are workstation measurements, not home-server
benchmarks. See the [NeMo comparison and artifacts](<[private local path]>).

Two full real API/worker language-mode trials (`multilingual_per_window` and forced
Thai) passed with monotone progress and succeeded/100, but both produced the exact
same 322 segment texts as the current auto-language profile. A generic bilingual
initial prompt also passed through the API/worker, but caused 569 of 580 segments
to repeat `And we're wearing glasses.` The prompt was rejected. Profiles and raw
progress traces remain under `[private local path],10,11}/`;
none changed the local profile or improved Kob quality.

A `Kob` hotword caused severe Thai fragment repetition and was rejected. A VAD
minimum-silence change from 2,000 to 500 ms kept the full Kob job successful and
reduced malformed fragments in selected English passages, but still misheard the
glasses word and added about 19 seconds of Kob inference. The same profile passed
Formal API/worker acceptance and ran about 35 seconds faster, though its text
changed substantially. Both tests reached succeeded/100. `.env.local` now selects
VAD 500 ms for local evaluation; it is not promoted pending human review and
repeated warm runs. The Python default and approved baseline remain at 2,000 ms.
The [review pack](<[private local path]>)
links the TXT/SRT and progress evidence.

Trial 15 kept VAD 500 ms and n-gram-8 settings, then disabled previous-text
conditioning for a full Kob CPU API/worker run. It passed in 379.89 seconds with
736 monotone progress samples ending succeeded/100; inference took 370.887
seconds. The transcript still rendered the glasses term as `วันตา`, and the flow
passage switched several English spellings into Thai script. This did not
establish a balanced quality gain, so previous-text conditioning stays on in the
selected local profile. Full artifacts and the frozen plan are under
`[private local path]`; see the private
[trial 15 review](<[private local path]>).

Trial 16 repeated the selected VAD 500 ms profile through separate real API and
worker processes. It passed in 455.28 seconds with 885 monotone progress samples
ending succeeded/100. Its 320 segments and TXT/SRT were byte-identical to trial
13. This verifies repeatability on this CPU workstation, not speech accuracy;
the glasses error is unchanged. See the private [trial 16 review](<[private local path]>).

Trials 17 and 18 tested Turbo beam sizes 1 and 3 on full Kob through the same
real API/worker path. Both passed with monotone progress ending succeeded/100.
Beam 1 took 257.880 seconds of inference and still rendered the glasses term as
`วันตา`; beam 3 took 357.794 seconds and fragmented `flow` into `Flo`/`Satana`.
Neither showed a balanced quality gain, so the local beam-5 profile remains
selected. Their [beam-1 review](<[private local path]>)
and [beam-3 review](<[private local path]>)
link complete outputs and progress traces. All measurements remain workstation
CPU results, not home-server benchmarks.

Trial 19 tested a short vocabulary-only prompt sourced from words in the
candidate transcript. It passed the real CPU API/worker test in 456.40 seconds
with 884 monotone progress samples ending succeeded/100. It did not fix the
glasses or polyglot terms, changed `flow` into Thai phonetic text, and repeated
`สาธานะ` across several cues. Reject the prompt; the local profile remains
prompt-free. See the private [trial 19 review](<[private local path]>).

Turbo beam size ten was tested through the actual API and worker after the Formal run showed several better spellings. The full Kob job passed in 599.77 seconds; progress reached 100 only on success. It improved some code-switch rendering, but the glasses term remained wrong and the extra inference time did not establish a broad improvement. A generic bilingual prompt on Formal produced no clear change. Neither experiment was promoted. The local experimental profile is Turbo beam five with temperature zero, context on, n-gram size eight and VAD silence 500 ms; Python defaults and the approved baseline remain unchanged.

Stereo analysis of both full originals found near-identical channels and no cancellation from mono averaging. The [CPU diagnostic report](cpu-large-v3-diagnostics-20261018.md) links the private transcripts, channel analysis, model details and experiment records. Publisher subtitles remain unreviewed, so recognition quality is still pending human review and balanced acceptance. No trial used a GPU or the owner's home server.

## Engineering checks and review

Ordinary tests isolate profile environment variables from machine settings;
integration-marked tests retain the operator's chosen real profile. This prevents
the selected local profile from silently changing synthetic baseline fixtures.
No existing assertion was removed or weakened.

| Command | Observed result after local profile selection |
| --- | --- |
| `uv run --env-file .env.local pytest -q` | 127 passed, 2 integration functions deselected, 12.67 s |
| `uv run --env-file .env.local ruff check .` | Passed |
| `uv run --env-file .env.local ruff format --check .` | Passed, 69 files |
| `uv run --env-file .env.local mypy` | Passed, 17 production files |
| `git diff --check` | Passed before documentation-only additions; line-ending notices only |

Five new decoder/profile tests were observed failing before implementation and
passing afterward. Additional regressions cover baseline comparison rejection and
schema-version misuse. This applies the test-engineering contract's behavioral
boundaries and negative-case guidance: generated decoder/configuration units,
public offline comparison, ordinary HTTP/SQLite interactions, and actual-process
HTTP/model checks. No frontend exists for browser E2E. No coverage threshold or
coverage measurement is configured.

Codex Security prompt-driven diff scan `30f32009-e9c2-449b-bdab-0ad8bbf6c40e`
completed with zero reportable findings and complete static coverage of six
changed production files: configuration, comparison, Whisper adapter, pipeline,
jobs and worker. The parent traced settings/media/IDs through validation to
decoder, parameterized SQL, progress callbacks and publication. Changed tests
and local settings selection were supporting context. Applied risks were OWASP
Top 10:2025 A01, A05, A06, A08 and A10. ASVS requirement text was unavailable in
the preceding review (HTTP 404); no specific ASVS compliance is claimed.

The [sealed report](<[private local path]>) and canonical documents were read back after completion.
This was a parent-only static review, not an independent audit or accuracy
certificate. Native dependencies/advisories, OS ACLs, unsupported public hosting
and model internals were excluded. Production source remained unchanged after
sealing; these documentation updates followed the scan. Workbench owning-thread
usage accounting reported 7,867,006 total tokens, 7,839,416 input tokens, including
7,789,824 cached input tokens, with complete measurement coverage.
