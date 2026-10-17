# Two-recording optimization: exploratory CPU observations

Status: incomplete evidence; not an accepted controlled baseline or a quality claim.

## Host and reproducibility

- Development host: Intel Core i3-12100F, four physical/eight logical CPUs, Windows 11 build 26200, 17,006,338,048 bytes RAM.
- Turbo, CPU INT8, four threads, beam five, automatic language, VAD enabled, segment timestamps.
- Python 3.12.10, faster-whisper 1.2.1, CTranslate2 4.8.3, PyAV 18.1.0.
- Cached model revision: `0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf`; offline Hugging Face mode. OS page cache was not flushed.
- Implementation base: `b93404ece55645db75b4f566284d00dd1f58e497` plus the external frozen source snapshot. This measurement preceded the subsequent reference/alias/report review fixes; it must not be attributed to a later commit without that distinction.
- External evidence: `D:\ai-stt\output\optimization-20261018-015630\cpu-baseline-formal\evaluation.json`; implementation snapshot and file hashes are beside it in `source-snapshot` and `source-snapshot.json`.

The positive allowlist contains only Formal Words and Conversation with Kob. No other real recording was used in this observation. No numerical CER/WER is available because publisher subtitles have not been reviewed against speech.

## Formal Words

Original duration: 281.681270 seconds. Original SHA-256: `a76b7d7f787bb43912f5b1880f84ba8a301f41648583903f5364e49638d636ee`.

| Call | Full-call seconds | Sampled peak process RSS, bytes | Approximate other CPU seconds |
| --- | ---: | ---: | ---: |
| Cold | 188.042 | 1,953,243,136 | 441.016 |
| Warm 1 | 190.828 | 1,426,608,128 | 604.734 |
| Warm 2 | 172.363 | 1,427,271,680 | 316.406 |
| Warm 3 | 178.534 | 1,428,332,544 | 393.688 |

Warm median: **178.534 seconds**; range: **172.363–190.828 seconds**; recording duration / median full-call time: **1.578 RTFx**. The observed median is faster than recording playback, but does not establish repeatability on an idle host or an optimization gain against a same-host controlled baseline. No candidate configuration has been compared.

Full-call time covers original-media validation, loading if needed, inference, complete JSON/TXT/SRT publication, and caller return. Authorization hashing and evaluation reporting are outside that interval. Cold model load took 8.575 seconds. RSS is sampled whole-process memory and may miss brief peaks. Approximate other CPU time is system busy time minus this process; it cannot identify contention precisely or certify isolation.

The process completed successfully and all four bundles are present. No simultaneous inference or heavy tests were launched by this implementation, but unrelated system activity was substantial. This run is retained as exploratory evidence; the idle-host baseline criterion remains unmet.

## Conversation with Kob and remaining evidence

The matching full-original run started in a separate fresh process on commit `8cc973898e392c99c10e9679d74de2d04bbf0735`, after the reference/alias/report review fixes and ordinary checks. It uses the same CPU settings, two-entry manifest, cached model, and offline mode; artifacts will be under `cpu-baseline-kob` in the external evidence root. The run is still active; no completed timing result is available yet. Controlled repetitions for both originals, reviewed Thai/English references, names/numbers and timing review, candidate comparisons, and actual home-server evidence remain required. This report does not close OPT-01 or any dependent ticket.
