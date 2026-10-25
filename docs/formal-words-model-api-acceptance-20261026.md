# Formal Words model API acceptance — 2026-10-26

## Scope and method

The real API was run once for each supported model using only the owner-approved Formal Words recording and its reviewed 87-cue reference. The existing `nfc-casefold-projections-v1` scoring policy was used without adding a CER/WER threshold. The reference has 87/87 speech-reviewed and timing-reviewed cues, with no uncertain cues.

Both API jobs succeeded. This was a single run per model on the tuning recording; the measurements do not establish general accuracy or a repeatable speed comparison. The output transcript's important-error and timing reviews remain pending. The reference itself was reviewed, but no claim is made that a person listened through either new API transcript.

The recording, reference text, job bundles, raw transcripts, and scorer output remain in local ignored or external storage. This report contains aggregate measurements only.

## Environment

- Host: Windows 11, Intel Core i3-12100F (4 physical / 8 logical cores), 15.84 GiB RAM.
- Runtime: Python 3.12.10; stt-services 0.1.0; faster-whisper 1.2.1; CTranslate2 4.8.3; PyAV 18.1.0.
- Inference: CPU, 4 threads, requested INT8, effective `int8_float32`, beam size 5, sequential decoding, batch size 1, automatic language detection, temperature 0, VAD enabled.
- Scoring: offline rescore of the API-produced JSON; `inference_performed=false` in the scorer. The API's legacy result format did not include a source hash, so the local run recorded an explicit operator binding between each submitted recording and its job. That binding is not an independently verifiable proof of source provenance.
- Code scope: the real API run used the feature implementation in the working tree based on `d648ce9`, subsequently committed as `9494cfb`. The later `00fa280` and `43d55de` commits only register the transcript request schema in OpenAPI components; they do not change runtime inference or transcript handling.

## Results

| Model | Model revision | Model load | Inference | Pipeline total | API submit to terminal | Peak sampled RSS | Thai CER | English WER | Normalized full CER |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Turbo | `0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf` | 7.923 s at worker startup; 0 s attributed to the job | 145.356 s | 145.682 s | 148.868 s | 1,963,991,040 B (1.83 GiB) | 10.4324% | 58.6207% | 16.5449% |
| large-v3 | `edaa852ec7e145841d8ffdb056a99866b5f0a478` | 14.629 s model switch/load | 517.829 s | 532.818 s | 534.095 s | 3,395,870,720 B (3.16 GiB) | 21.0707% | 93.1034% | 29.5929% |

The Turbo worker loaded its configured model before accepting the job, so its 7.923-second startup load is reported separately from the per-job `model_load_seconds`. For large-v3, the job caused a model switch and its load time is included in that job's pipeline duration. API submit-to-terminal includes job/service overhead. Peak RSS is sampled by the pipeline at 50 ms intervals, so it may miss shorter peaks.

## Interpretation and limitations

On this one Formal Words run, Turbo had lower measured error rates and shorter runtime than large-v3. No acceptance threshold was defined, and this single tuning sample is not a general quality claim or a controlled benchmark. Existing scoring notes require manual important-error review to detect cross-language ordering errors; that review, as well as timing review of the new output, remains pending. Result-level `important_error_review` and `timing_review` are therefore not accepted as complete.
