# CPU transcription project status, 24 October 2026

## Scope

The active optimization work covers only the full Formal Words and Conversation with Kob recordings, their existing publisher answers, and CPU inference. The immediate work is local project readiness. Homelab access and Docker deployment are deferred until the local workflow is ready. Do not claim reference-backed accuracy while the answer review remains incomplete.

The approved media, references, review drafts, models, caches, manifests, and run outputs remain outside the public repository. No GitHub Actions workflow is present.

## Current evidence

- The existing source and publisher-reference pairs were verified against the approved identities and hashes. Formal Words has 87 cues; Conversation with Kob has 290.
- Existing review drafts show 0/87 Formal Words cues and 0/290 Kob cues reviewed for speech and timing. Reviewer identity, review time, and important-error review are still missing. No CER/WER or reference-backed accuracy claim is valid yet.
- Historical local CPU INT8 runs completed Formal Words through the CLI and Conversation with Kob through the API and persistent worker. They produced JSON, TXT, and SRT outputs. These runs establish path completion only; they do not establish reviewed accuracy or homelab behavior.
- A read-only connection check to the owner-designated homelab timed out. No remote command or deployment was performed.
- The default evaluation allowlist now binds both approved recording identities, immutable source/reference hashes, and their tuning/final roles. Other real recordings remain rejected.
- The `docs/formal-words/` convenience copy is ignored by Git. A targeted credential-pattern scan found no token or private-key matches in versioned files; local absolute paths in Markdown were replaced with a generic marker. This scan is not a general secret-scanning certification.
- Static security review found a possible unbounded ancestor loop in optional PR stack discovery when fork branch names collide. The code now rejects repeated PR ancestry before appending again; a focused Node runtime check covered normal ordering and the cycle case. A second diff review is required after this fix.
- `.gitignore` now also excludes dependency folders, common local upload/transcript/run/result directories, database files, subtitle outputs, and private-key container files. `.env.local.example` uses a generic external data path.

## Engineering checks run on 24 October

All commands ran from the project root using the root `.venv` and `.env.local`:

| Command | Result |
| --- | --- |
| `uv run --env-file .env.local -- python -m pytest tests/test_evaluation.py tests/test_comparison.py -q` | 25 passed. |
| `uv run --env-file .env.local -- python -m pytest` | 127 passed, 2 integration tests deselected. |
| `uv run --env-file .env.local -- ruff check .` | Passed. |
| `uv run --env-file .env.local -- ruff format --check .` | Passed; 226 files already formatted. |
| `uv run --env-file .env.local -- python -m mypy` | Passed; 17 source files checked. |
| `node --experimental-strip-types --input-type=module` with a focused stack-discovery check | Passed; normal ordering retained and cyclic fork branch ancestry rejected. |

Calling the `pytest` and `mypy` console scripts through `uv run` failed to canonicalize the script path on this Windows environment. Running them as Python modules with the same project environment succeeded; no dependency sync was needed.

The Bun test runner and `tsc` are not installed on this machine, so the new TypeScript unit-test file and strict package typecheck could not be run. The focused Node check executed the changed function directly but is not a substitute for those package checks.

## Ticket state

| Ticket | State | Remaining evidence |
| --- | --- | --- |
| OPT-01 | In progress | Review both answers against original speech and timing; validate a reference-matched local API result. |
| OPT-02 | Blocked, conditional | Use the reviewed baseline to identify a concrete need, or record evidence-backed N/A. |
| OPT-04 | Blocked, conditional | Test one batch candidate only if sequential processing is unsuitable; otherwise record N/A. |
| OPT-05 | Blocked, conditional | Test at most one hint only for a reference-confirmed error; otherwise record N/A. |
| OPT-06 | In progress | Complete the CPU portfolio workflow after OPT-01 and applicable conditional dispositions; homelab evidence is still pending. |
| OPT-03 | Cancelled | GPU work remains out of scope. |

The code and software checks do not close human review, local API accuracy, or homelab acceptance. Do not mark conditional tickets Complete while their trigger evidence is absent.
