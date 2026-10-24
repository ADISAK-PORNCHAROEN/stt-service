# Whisper Turbo speed and Thai/English quality research

Date: 18 October 2026. Research and proposed experiments only; no inference, runtime changes, or new performance measurements were performed.

## Current authorized evaluation scope

The owner's later instruction restricts real-recording experiments to Formal Words and Conversation with Kob. Corpus-size and category suggestions below are historical research proposals, not permission to run other media. Use the new feature's two-entry allowlist for real inference, benchmarks, and integration acceptance; a downloaded asset or inherited media environment setting is not authorization. See the [draft specification](../../.scratch/stt-optimization/spec.md) and [review package](../../.scratch/stt-optimization/review.md).

## What this repository already establishes

The current engine uses faster-whisper 1.2.1/CTranslate2, CPU INT8, four threads, beam five, automatic language detection, VAD, and segment timestamps. The persistent worker already reuses its loaded model. The adapter discards engine diagnostics when converting results to the project's `Segment` objects. See [engine](../../src/stt_services/engines/whisper.py), [pipeline](../../src/stt_services/transcription/pipeline.py), [architecture](../../.scratch/stt-mvp/architecture.md), and [specification](../../.scratch/stt-mvp/spec.md).

The [existing baseline](../../benchmarks/reports/20261017-turbo-cpu.md) measured 400.684 seconds of audio on an i3-12100F with eight logical CPUs: warm inference 820.576 seconds, full call 820.607 seconds, RTFx 0.4883; cold model load 11.847 seconds. Inference dominates this recording. The cold/warm difference is much larger than loading alone; CPU contention was documented, so it cannot establish an isolated cache or warm-up speedup. Full-recording human accuracy review remains absent. Ticket closure does not establish an accuracy baseline.

## Primary-source evidence

### Turbo has a relevant Thai limitation

OpenAI's release announcement says Turbo reduces the decoder from 32 to four layers and notes larger degradation for Thai and Cantonese. This is a reason to compare Thai quality against `large-v3` on reviewed local audio, not evidence that any replacement is necessarily better on this recording. The architecture also means decoder-only tuning cannot remove all encoder computation. [OpenAI release announcement](https://github.com/openai/whisper/discussions/2363).

### Batching has CPU evidence, with limits

The official faster-whisper benchmark reports CPU small-model INT8/beam-five transcription of 13 minutes at 1m42s sequential versus 51s with batch eight; reported RAM rises from 1477 MB to 3608 MB. Hardware is an i7-12700K with eight threads. These are **small-model results**, not Turbo on the project's i3. The same README publishes GPU batching improvements, supports `int8_float16`/FP16 GPU execution, and requires the corresponding NVIDIA runtime libraries. Similar settings and comparable transcript quality are essential in comparisons. [faster-whisper 1.2.1 README](https://github.com/SYSTRAN/faster-whisper/blob/v1.2.1/README.md).

### Relevant decoding semantics in the pinned version

In 1.2.1, normal transcription defaults to temperature fallback `(0,.2,.4,.6,.8,1)` and previous-text conditioning. Fallback can repeat decoding. Disabling conditioning can reduce repetition loops but lose consistency. `language=None` detects an initial language; `multilingual=True` detects per window, not every word. `initial_prompt` and `hotwords` provide text hints, not mandatory vocabulary. Returned segment diagnostics include average log probability, repetition/compression measures, no-speech probability, and temperature.

The batched path is semantically different: it disables previous-text conditioning, keeps only the first temperature, and marks compression/log-probability/no-speech thresholds unused. It also defaults `without_timestamps=True`, unlike the normal path. Therefore swapping classes is not a controlled performance-only change. Explicitly preserve required timestamp behavior and review text/timing. [Pinned transcription implementation](https://raw.githubusercontent.com/SYSTRAN/faster-whisper/v1.2.1/faster_whisper/transcribe.py).

### CPU threads and quantization

CTranslate2 recommends CPU INT8 and avoiding a product of inter-operation and intra-operation threads above physical core count. It recommends larger GPU batches. [Performance tips](https://opennmt.net/CTranslate2/performance.html). Intra-operation threads divide one operation; multiple workers need concurrent submitted batches to provide parallelism. [Parallelism documentation](https://opennmt.net/CTranslate2/parallel.html). Increasing worker count therefore does not inherently shorten one recording and can compete for CPU/RAM.

### VAD can help or remove useful speech

Pinned VAD defaults include threshold 0.5, minimum silence 2000 ms, speech padding 400 ms. The source recommends tuning threshold to the dataset. It explicitly discards chunks below configured minimum speech length. More aggressive filtering therefore needs a missed-speech check, especially at quiet words and boundaries. [Pinned VAD implementation](https://raw.githubusercontent.com/SYSTRAN/faster-whisper/v1.2.1/faster_whisper/vad.py).

## Proposed experiments, in priority order

These are hypotheses, not promised speed or accuracy gains. Keep private recordings and transcripts outside Git, and keep the approved baseline intact while investigating.

| Priority | Experiment | What decides whether it helps |
| --- | --- | --- |
| 1 | Re-measure baseline alone, then beam 1, 3, and 5 with all other options fixed | Warm full-call time plus reviewed Thai, English names, numbers, omissions, and repeated text. Fewer beams may speed decoding but can change quality; five beams do not guarantee better text. |
| 2 | Sweep CPU threads 2, 4, and 8 separately from beam changes | Measure actual wall time and CPU contention. Eight logical CPUs are not proof that eight inference threads win. Do not add multiple workers first. |
| 3 | Compare automatic language with `language="th"` for Thai-dominant recordings; separately test `multilingual=True` on genuine alternating-language audio | English word retention, unwanted translation/transliteration, and dropped speech at switches. A single Thai hint is not proof that embedded English will disappear or improve. Per-window detection cannot solve every within-sentence switch. |
| 4 | Add a short, relevant Thai/English glossary using a prompt or hotwords; compare previous-text conditioning on/off independently | Correct names/technical terms versus inserted glossary words, repetitions, and consistency. Avoid a long instruction-like prompt or indiscriminate dictionary. |
| 5 | Compare sequential inference with batch 2 and 4 before trying 8 | Full-file time, RAM, text quality, and source-timeline timestamps. Treat changed context/fallback as part of the experiment. Batch one can help distinguish batching-path changes from batch-size effects. |
| 6 | Inspect fallback frequency, then compare default fallback with a restricted policy | Count retries and quality on hard passages before removing them. Existing adapter diagnostics are insufficient for a defensible selective-retry decision. A confidence score is not a calibrated correctness probability. |
| 7 | Tune VAD only if recordings contain meaningful silence or missed quiet speech | Speech retained at boundaries, false text during silence/music, and time saved. Preserve original recording offsets and gaps; avoid merging chunks with incorrect timestamps. |

After a fast profile is measured, a second pass over suspicious spans is a plausible design: reprocess only those spans with a more conservative profile or a stronger model, with surrounding context and deduplication. This can cost less than two full runs, but a first pass can omit speech without low-confidence text; add speech-coverage checks and human evaluation. It is not yet an implemented or validated policy.

If CPU changes cannot meet the desired turnaround, an optional compatible NVIDIA GPU is a separate experiment likely to change the compute constraint substantially; do not infer exact speed, required VRAM, or purchasing suitability from a different model's benchmark. Compare Turbo and `large-v3` on the same GPU/audio/settings if Thai quality is the goal. GPU and alternative execution engines are outside the current MVP spec.

An optional CPU backend experiment is `whisper.cpp` with OpenVINO: its official documentation supports OpenVINO encoder execution on x86 CPUs and supported Intel GPUs, with device compilation/cache considerations. This establishes an available acceleration path, not superiority over this project's faster-whisper INT8 Turbo. Match model, beam, language, timestamps, and reviewed quality before comparing total time. [whisper.cpp OpenVINO documentation](https://github.com/ggml-org/whisper.cpp#openvino-support).

## Decision rule

Proposed evaluation pilot: privately review 10–20 minutes covering Thai, English, language switches, names, numbers, quiet speech, silence, and music. This is a practical initial scope, not a statistically certified quality estimate. Reserve held-out recordings for final comparison, separate from prompt/parameter tuning. Report Thai CER under a documented Unicode normalization preserving tone marks and vowel/other combining marks; report English WER; report Thai WER only with a fixed, documented tokenizer. Preserve raw and normalized scoring views, and count critical-token mistakes, omissions, repetition, and audible timestamp errors separately. WER/CER measure substitutions, insertions, and deletions against reference text; normalization can substantially change scores without changing the underlying transcript. [Hugging Face ASR evaluation course](https://huggingface.co/learn/audio-course/en/chapter5/evaluation).

For timing, use an otherwise idle machine, the same cached model revision and effective options, and at least three warm measurements per finalist; report median and spread plus peak RAM. Record fallback telemetry and speech coverage as well as text. Preserve timestamps on the original recording timeline throughout chunking, VAD, and second-pass assembly.

Choose measured configurations on the speed/quality frontier: no other candidate should be faster with at least equal reviewed quality. A useful outcome may be two profiles, one for quick drafts and one for difficult Thai/English recordings. No setting here proves both higher accuracy and lower latency universally. Use held-out recordings to ensure a glossary or parameter choice improves new material, and record effective options, model revision, runtime versions, full-call RTFx, and peak RSS alongside the text-quality evidence.
