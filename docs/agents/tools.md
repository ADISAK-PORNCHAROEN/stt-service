# Agent tools and workflow entry points

## Project commands

| Need | Existing command | Owner and limits |
| --- | --- | --- |
| Install/sync pinned dependencies | `uv sync --locked` | `pyproject.toml` and `uv.lock`; set `UV_CACHE_DIR` from `.env.local` in PowerShell before running. Not needed for a docs-only change. |
| Behavior checks | `uv run --env-file .env.local -- python -m pytest` | `pyproject.toml` and `docs/TESTING.md`; ordinary fake-inference suite, integration tests excluded. |
| Lint / formatting / production types | `uv run --env-file .env.local ruff check .`; `uv run --env-file .env.local ruff format --check .`; `uv run --env-file .env.local -- python -m mypy` | `pyproject.toml` and root `AGENTS.md`; run for source changes as applicable. |
| Real-model acceptance | `uv run --env-file .env.local -- python -m pytest -m integration tests/test_real_model.py tests/test_http_real.py -v` | Requires `STT_TEST_MEDIA` set in ignored `.env.local`, downloaded weights, and local service processes. It is opt-in and uses approved private media. |
| CLI/API/worker | `uv run --env-file .env.local stt ...` | `README.md`; output destinations must be new and outside managed job/cache/lock paths. The service is loopback-only. |

Use these commands as documented; this guide adds no aliases, scripts, hooks, or CI gates.

## AI review skills

| Trigger | Skill and inputs | Review output and limits |
| --- | --- | --- |
| Behavior/test change or explicit verification request | `.agents/skills/test-engineering/SKILL.md`; read `docs/TESTING.md`, accepted spec/ticket, actual diff, relevant source and tests | Recommend layers from the changed behavior; report exact checks, scope, failures, coverage limitations, and evidence. Do not infer model accuracy from fake-engine tests. |
| Application code, executable configuration, dependency, or CI diff | `.agents/skills/security-review/SKILL.md`; read `SECURITY.md`, `docs/SECURITY-MODEL.md`, actual diff and affected callers | Route to host `$codex-security:security-diff-scan`; record findings/candidates and limits. Use whole-repository scan only when explicitly requested. |
| Specs and issue slices | `.scratch/<feature>/spec.md`, `.scratch/<feature>/issues/`, and `docs/agents/issue-tracker.md` | Preserve accepted decisions and ticket IDs; verify status against source and evidence. Do not invent scope. Publish external issues only when the owner explicitly authorizes it, then record their IDs and dependencies locally. |
| Domain or architecture vocabulary | `CONTEXT.md`, `docs/ARCHITECTURE.md`, and relevant source | Keep agreed terms in the glossary, module/data boundaries in architecture, and consequential rationale in `docs/adr/`. |
| Workflow/instruction maintenance | Project-local `.agents/skills/ai-project-foundation/SKILL.md`; read its setup contract and this report before edits | Update the manifest, skills checklist, delivery list, instructions, applicable skill routes, and content review together. Do not add Foundation checkers or hooks as part of ordinary setup. |

The project-local skills live under `.agents/skills/`; the Foundation manifest lists the selected set and records runtime discovery separately. A file or route alone does not prove that a fresh host session loaded or invoked it.

## Current project journey

The current CPU-only homelab portfolio workflow is tracked by `OPT-01` and `OPT-06` in `docs/agents/issue-tracker.md`. It uses only the approved Formal Words and Conversation with Kob recordings. `src/stt_services/evaluation/evaluation_service.py` enforces the source allowlist/hash path and supports evaluation; `tests/test_evaluation.py` covers rejection of unknown sources before inference/output. Each full recording needs one complete homelab run for basic acceptance, with reference review and timing/resource evidence recorded. `docs/optimization-verification-20261018.md` contains earlier measurements from another host and does not establish the homelab result; its accuracy notes also remain subject to human reference review.

For a resumed task, read the ticket/spec and report, inspect the current diff/source/tests, then run only the ticket's authorized checks on approved inputs. Preserve private recordings and result bundles outside Git and write new evidence to the owner's declared location.
