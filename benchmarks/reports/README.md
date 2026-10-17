# Benchmark reports

Only sanitized methodology and measurement summaries belong here. Private media,
transcripts, raw JSON/SRT/TXT and benchmark artifacts stay outside the repository.

Use `uv run stt benchmark <media> --output-dir <new-directory>` for a cold-model run
and a warm-model run in the same fresh process. Record model revision, dependency
versions, configuration, hardware, cache/download conditions, timing scope, RTFx
and process RSS sampling limitations. Never extrapolate PC results to the server.

Text/timestamp inspection is qualitative without reviewed reference text. CER/WER
requires documented normalization and tokenization, particularly for Thai.
