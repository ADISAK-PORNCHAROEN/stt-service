---
name: test-engineering
description: Select, update, and run checks for behavior or test changes in this Python 3.12 transcription service. Use for source/test changes and explicit verification requests; read the project testing contract first.
---

# Test engineering

## Method and project context

Before choosing test layers, interpreting coverage or reviewing test edits, read
[testing standards and project mapping](references/testing-contract.md) and apply
its relevant source guidance. It owns the detailed method and source-to-project
mapping. The project's testing guide and native configuration own commands,
fixtures, measured scope, thresholds and evidence paths. During setup, reconcile
outdated local procedures while preserving accepted project constraints.

## Workflow

1. Apply the referenced testing method to the accepted behavior. Read the root
   agent guide and the project's testing guide for the local constraints.
   Inspect native package scripts, test configuration, coverage scope, current
   failures and relevant tests before editing.
2. For each production behavior change, add or update a regression test whose
   expected result comes from the accepted contract, not merely from the new
   implementation. Include useful boundary, invalid-input, permission,
   exceptional or recovery cases for the changed behavior.
3. Choose the narrowest layer that proves the changed contract: unit for local
   logic, integration for interacting boundaries, and E2E for changed critical
   user journeys or cross-layer browser behavior. Do not duplicate a full E2E
   suite for changes that cannot affect a user journey.
4. Run the repository's mandatory baseline and all applicable changed-scope
   checks. Run coverage when changed production files are in the configured
   coverage scope or when coverage configuration changes. Inspect uncovered
   changed lines/branches and preserve existing thresholds. Use actual native
   commands from the manifest; do not invent `npm` aliases for another stack.
5. Review test diffs for deleted cases, weakened assertions, mocks that replace
   the behavior under test, and expectations copied from the implementation.
   Keep prior failures separate from regressions introduced by this change.

## Completion

Report the exact commands, revision/dirty scope, results and artifact paths.
State which test layers were selected and why, coverage scope/threshold and
uncovered risk, plus every skipped or unavailable check. Passing tests and a high
coverage percentage do not alone establish correctness or security.
Identify the contract sections/reference principles applied and accepted project exceptions;
report unavailable source reads honestly.

## References

Source roles and local adaptations are in the linked testing contract.

- [Google: How Much Testing is Enough?](https://testing.googleblog.com/2021/06/how-much-testing-is-enough.html)
- [Google: Code Coverage Best Practices](https://testing.googleblog.com/2020/08/code-coverage-best-practices.html)
- [Google code review: What to look for](https://google.github.io/eng-practices/review/reviewer/looking-for.html)
- [OWASP Secure Coding with AI Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Coding_with_AI_Cheat_Sheet.html)
- [OpenAI: A Practical Approach to Verifying Code at Scale](https://alignment.openai.com/scaling-code-verification/)

## Project workflow

- **Trigger:** application behavior or test changes, or an explicit request to verify behavior. For a documentation-only foundation setup, review the local mapping without running the application suite.
- **Inputs and scope:** inspect the accepted MVP/optimization spec and ticket, actual diff, relevant `src/stt_services/` modules and `tests/` cases. Read `docs/TESTING.md` and `references/testing-contract.md` first.
- **Authoritative sources:** `pyproject.toml` owns pytest/Ruff/mypy configuration; `uv.lock` owns resolved dependencies; `docs/TESTING.md` selects checks; the current spec/ticket owns expected behavior and the tracker/report owns acceptance evidence.
- **Execution:** use the repository-root `.venv` and commands in `docs/TESTING.md`; use `.env.local` for machine settings. Integration tests need explicit local media and downloaded model weights. Keep recordings and result bundles external and honor the evaluation allowlist.
- **Output:** report changed paths and behavior, selected layers, exact commands/results, revision/dirty scope, evidence path, and skipped checks. Save acceptance evidence in the ticket's existing owner path.
- **Failure recovery:** retain the first useful failure output, distinguish baseline failures from regressions, check effective settings/fixture ownership, and rerun only after a concrete correction. Never delete or overwrite user data to make a check pass.
- **Review criteria:** assertions cover observable CLI/API/filesystem/SQLite behavior; fake inference does not mock away the boundary under test; invalid-input, concurrency, publication, recovery, and retention cases are included where affected; changed uncovered production paths and test removals/weakenings are examined.
