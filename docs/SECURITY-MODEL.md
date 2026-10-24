# Security model

## Scope and assets

The reviewed design is a local single-operator transcription CLI plus a loopback FastAPI service, SQLite queue, persistent worker, media parsers, and local model/cache storage. Assets include original recordings, transcripts/subtitles, job metadata, environment credentials/paths, and model/dependency integrity. The current MVP has no authentication and is not designed for LAN or Internet exposure.

## Trust boundaries and controls

| Attacker-controlled input or boundary | Asset/path and impact | Source-backed controls | Verification pointer |
| --- | --- | --- | --- |
| Local client request and multipart upload | Upload stream → staging → parser → job storage; resource exhaustion, malformed media handling, or unintended protocol access | Loopback bind plus Host/Origin checks; bounded body/field/header/file sizes; one generated upload path; allowlisted suffix/demuxer and `file,pipe` protocols; full decode and duration/sample validation before queue admission | `api.py`, `uploads.py`, `audio.py`; `tests/test_api.py`, `test_inputs.py`; ASVS 5.0.0 V5.2.1/V5.2.2; WSTG v4.2 WSTG-BUSL-08 |
| Local API client polling/results | Job ID → status/result and filesystem paths | Generated 32-lowercase-hex IDs validated at route boundary; only retained succeeded jobs serve results; safe error messages; response lease and cleanup coordination | `api.py`, `jobs.py`; `tests/test_api.py`, `test_lifecycle.py` |
| Worker/API concurrency and local filesystem | SQLite queue, active job input, result publication, readiness state | Transactional admission and FIFO claim; singleton worker lock; recovery marks interrupted jobs failed; staging then atomic directory publication; heartbeat independent of long work; leases protect active results/cleanup | `jobs.py`, `worker.py`, `pipeline.py`; `tests/test_lifecycle.py`, `test_scheduling.py`, `test_progress.py` |
| Local files, config and dependencies | Private recordings/results, environment settings, model cache, software supply chain | Runtime data is external to Git; service retention is bounded; dependencies are pinned through `uv.lock`; input/output ownership distinguishes API-managed from CLI-owned data | `config.py`, `jobs.py`, `.gitignore`, `pyproject.toml`, `uv.lock`; review data paths and dependency diffs |
| Evaluation recordings and reference text | Private authorized originals, reviewed references, generated evaluation bundles | Evaluation restricts source names/hashes to the approved allowlist and separates offline rescoring; reports point to external/private evidence | `evaluation.py`, `references.py`, `comparison.py`; `tests/test_evaluation.py`, `test_comparison.py`; active optimization spec/tickets |

## Invariants and known limits

- Run the service only on loopback. Host/Origin checks reduce browser/request exposure but do not authenticate local clients or provide a LAN security boundary.
- Validate size, suffix/content, format, duration, audio stream, and full decoded media before durable admission/inference. Never pass arbitrary demuxer/protocol selection from a request.
- Treat source media and reference text as private. Keep raw recordings, transcripts, logs containing user data, credentials, and cache artifacts outside Git.
- Publish a result only after the complete artifact bundle is written. A crash between filesystem rename and success commit must not expose an unfinished job as succeeded.
- Keep failure details safe for clients; do not return private server paths or tracebacks.
- Service cleanup applies only to terminal API-owned jobs and must skip active jobs/download leases. It must not expire CLI-owned sources/results.
- A local filesystem, process, dependency, or parser compromise is outside the protection provided by loopback-only binding. OS account permissions and host security remain deployment responsibilities.

## Review workflow

For every application-code, executable-configuration, dependency, or CI diff, use `.agents/skills/security-review/SKILL.md` and review the actual diff plus affected callers. Pair reachable input/abuse cases with `.agents/skills/test-engineering/SKILL.md`. A whole-repository scan is a separate explicit task. Record the base/revision, changed paths, selected threats/requirements, confirmed findings vs candidates, exclusions, and coverage gaps; a clean bounded review is not a security certification.

Current standard references are mapped in the project's security-review contract. ASVS V5.2.1 and V5.2.2 and WSTG-BUSL-08 are selected as relevant upload guidance; they are not claims of conformance or passed verification. Recheck exact versions/text when changing the mapping.
