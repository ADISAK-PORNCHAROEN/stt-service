# STT quality and latency follow-up

Date: 18 October 2026. Research and design input only. No inference, tests, model downloads, or media processing were performed for this note. The inspected environment and lockfile contain faster-whisper **1.2.1** and CTranslate2 **4.8.3**.

## What the Kob result establishes

The exploratory comparison reported Kob warm-run Thai CER median 44.22%, range 42.73-52.62%. It used an unreviewed projection of multilingual publisher subtitles. These values establish a mismatch to that projection; they do not establish the proportion of speech recognized incorrectly. Thai translations, English speech, romanization, subtitle editing, and actual recognition errors need separate review. Some inspected passages contain apparent substitutions and omissions, so reference problems do not explain away every mismatch. Private transcript examples remain outside Git.

Create a **reviewed reference** from the actual speech, with original-recording intervals, language tags, review state, and explicit exclusions. Preserve both raw publisher subtitles and the reviewed derivative. Report scoring coverage and the normalization version alongside CER/WER. A missing English reference slice is unavailable evidence, not zero English errors. Formal Words remains the tuning recording; freeze the candidate before evaluating Conversation with Kob. Earlier inspection of Kob means this is a small, partly observed evaluation set, not an untouched statistical holdout.

## What is new compared with the first research note

The [earlier research](whisper-turbo-optimization-20261018.md) already proposed beam/thread sweeps, language/context hints, batching, VAD checks, fallback diagnostics, and GPU comparisons. The useful additions here are **specific pitfalls in the pinned code**, their effect on a persistent worker, and an experiment order that avoids mixing them together.

| New finding from inspected code | Consequence for this project |
| --- | --- |
| Returned segment temperature is not a retry count. When every fallback attempt fails thresholds, the implementation can choose an earlier candidate while returning the last attempted temperature. | Store this as the engine-reported temperature. Retry counts and retry time require attempt-level instrumentation; use unavailable/null when not captured. |
| A forced language produces `language_probability=1` by construction. | Record whether language was forced or detected; never show the forced value as measured confidence. |
| Sequential VAD defaults wait for 2000 ms silence; batched defaults use 160 ms and cap speech chunks by the chunk length. | Compare effective VAD options, retained intervals, and model timing as well as batch size. A class swap changes segmentation. |
| The batched path removes `max_speech_duration_s` from a supplied VAD dictionary. | Materialize a fresh dictionary from the profile for every call. Shared mutable configuration can otherwise drift. |
| A nondefault `chunk_length` updates shared feature-extractor frame/sample limits without resetting them on a subsequent omitted value. | Keep the 30-second window fixed in the current phase. Future window experiments need isolated engine instances, or an explicitly designed reset contract. |
| Explicit batched clips longer than 30 seconds are warned about and only their first 30 seconds are transcribed. | Any future selective retry must split bounded clips and retain recording offsets; it cannot submit arbitrary long suspect spans. |

These are supported by the installed sources and their tagged upstream equivalents: [fallback and language/VAD/batch implementation](https://github.com/SYSTRAN/faster-whisper/blob/v1.2.1/faster_whisper/transcribe.py), [mutable feature extractor](https://github.com/SYSTRAN/faster-whisper/blob/v1.2.1/faster_whisper/feature_extractor.py#L198-L205). The latter is also described in [upstream issue 1661](https://github.com/SYSTRAN/faster-whisper/issues/1661); the recommendation follows from the code rather than treating an issue report as proof of a fix. These observations identify future experiment risks; they do not prove that current Kob runs encountered them.

## Priority experiments

Every row is a hypothesis to measure, not a promised speedup. Use only the two authorized recordings. Tune on Formal Words, preserve the baseline, and perform the frozen Kob evaluation after choosing settings. Repeatedly selecting settings using Kob would turn it into tuning data.

The order below is research priority, not a change to ticket dependencies. All execution still obeys the existing OPT blockers; changed VAD/fallback policies belong to a separately justified OPT-05 case after its prerequisites, and do not replace the initial baseline.

| Order | Controlled comparison | Reason and acceptance evidence |
| --- | --- | --- |
| 1 | Reviewed reference and idle-host baseline, with effective settings and stage timings | Establish Thai CER, English WER where supported, omissions, critical words, model timing, warm full-call median/spread, and peak RSS. Separate queue wait, model load, preprocessing, full engine consumption, and export costs. The generator must be consumed before inference timing stops. |
| 2 | Diagnose fallback before changing it; compare default schedule with temperature 0 alone on Formal Words | Positive-temperature fallback samples candidates and repeats decoding when thresholds fail. It is a plausible source of both variable output and longer calls. Record attempts if genuinely observable; a temperature-0 result is not guaranteed correct or universally deterministic. Keep `best_of`, beam, and other settings fixed. |
| 3 | Beam 5/3/1, then CPU threads 4/2 in separate sweeps | CPU INT8 is already appropriate. Four physical cores are a reason to start with one four-thread worker, not to assume eight logical threads or multiple workers shorten one recording. Select speed only under reviewed quality constraints. |
| 4 | Auto language versus forced Thai; previous-text context on/off; short glossary as independent comparisons | Investigate language switches and error propagation. Keep `task=transcribe`. A Thai language hint does not guarantee correct embedded English. Initial detection can miss later switches; per-window multilingual detection is not word-level routing. Glossary terms must come from permitted domain knowledge, never the evaluation answer key. |
| 5 | Same-host GPU sequential `float16`/`int8_float16` candidates, once capabilities and available VRAM are known | Most promising hardware route when CPU inference dominates; exact gain and fit are unknown. Use the same model revision, audio, decoding policy, and quality checks. Capture GPU memory as well as process RSS. Fail an unsupported explicit GPU request clearly instead of silently measuring CPU. |
| 6 | Sequential versus batched path at batch 1, then batched 2/4 | Batch 1 exposes path/segmentation/context differences before changing parallel work. Preserve `word_timestamps=false`, explicitly require segment timestamps, and inspect omissions, overlap, and original-recording offsets. Do not compare defaults as though batching were the only change. |
| 7 | VAD sensitivity only if evidence shows silence cost or missed speech | Adjust one setting at a time and review quiet words/boundaries. More removed audio is not automatically better. Keep speech coverage separate from recognized-text diagnostics. |

The pinned implementation shows default temperature fallback and optional previous-text context; disabling context can reduce repetition loops while losing cross-window consistency. Its batched path uses only the first temperature and disables previous-text context, with several sequential quality thresholds unused. The existing adapter discards these diagnostics, so instrumentation should precede conclusions about why Kob varies. [Pinned sequential/batched implementation](https://github.com/SYSTRAN/faster-whisper/blob/v1.2.1/faster_whisper/transcribe.py).

CTranslate2 recommends CPU INT8, avoiding worker-thread products above physical core count, and larger GPU batches when possible. More workers mainly address concurrent work and can compete for resources; that differs from shortening one recording. [Performance guidance](https://opennmt.net/CTranslate2/performance.html), [parallelism guidance](https://opennmt.net/CTranslate2/parallel.html).

## GPU and benchmark caveats

The first-party faster-whisper table supports investigating batching, but its CPU numbers use the **small** model on an i7-12700K; its GPU numbers use **large-v2** on an RTX 3070 Ti. The table itself names faster-whisper 1.1.0. Neither measures this project's Turbo/i3/RTX 3050 configuration. Treat external times and memory as examples, not forecasts. [Versioned benchmark and requirements](https://github.com/SYSTRAN/faster-whisper/blob/v1.2.1/README.md#benchmark).

For the exact CT2 4.8.3 wheel, capability diagnostics matter more than a generic installation recipe. Tagged installation documentation mentions cuDNN 8, while the tagged Windows build script installs CUDA 12.8/cuDNN 9.10 and configures `WITH_CUDNN=OFF`; faster-whisper's README describes CUDA 12/cuDNN 9. These sources do not form one consistent runtime checklist. Inspect the installed wheel, supported compute types, driver/runtime loading, and available memory before choosing dependencies. Do not blindly install cuDNN 8 or downgrade the project. [CT2 tagged installation](https://github.com/OpenNMT/CTranslate2/blob/v4.8.3/docs/installation.md), [tagged Windows build](https://github.com/OpenNMT/CTranslate2/blob/v4.8.3/python/tools/prepare_build_environment_windows.sh), [supported compute type API](https://opennmt.net/CTranslate2/python/ctranslate2.get_supported_compute_types.html).

FP16/INT8 GPU support depends on hardware capability, and CT2 may convert unsupported compute types at load. Record the effective capability/type rather than relying on a profile's name. [Quantization and fallback tables](https://opennmt.net/CTranslate2/quantization.html).

## Management and quality decisions

Use immutable, versioned experiment profiles with a resolved settings snapshot. Associate every result bundle with profile identity, model revision, runtime versions, host, reference revision, and review coverage. Keep experimental diagnostics in an internal versioned sidecar so canonical transcript/export contracts remain manageable. Keep raw audio, text, prompts, and detailed logs outside Git; commit sanitized measurements only.

Treat `avg_logprob`, compression ratio, no-speech probability, and language probabilities as diagnostic signals. Their use inside decoding heuristics does not establish a calibrated probability that a transcript is correct. Speech can be omitted before any text exists, so low-score segments alone cannot find every failure. A future selective retry needs reviewed trigger precision, speech-coverage checks, bounded extra time, recording-offset restoration, and deduplication. It should follow validated single-pass profiles rather than become the first optimization. [Pinned decoding/VAD code](https://github.com/SYSTRAN/faster-whisper/blob/v1.2.1/faster_whisper/transcribe.py), [VAD behavior](https://github.com/SYSTRAN/faster-whisper/blob/v1.2.1/faster_whisper/vad.py).

OpenAI explicitly notes larger Turbo degradation for Thai. This limits what parameter tuning can promise; it does not prove the cause of this recording's errors. Keep the approved Turbo/backend scope. A model replacement, fine-tuning, external correction model, or another backend needs a separate evidence-backed decision after these measurements. [First-party Turbo announcement](https://github.com/openai/whisper/discussions/2363).

Next deliverable: a reviewed-reference comparison report and an idle-host baseline with trustworthy effective settings. Then advance the existing CPU, GPU, batching, and language/context tickets with the controls above. Promote a profile only when its quality, timing, resource use, and persistent-worker behavior are supported by evidence.
