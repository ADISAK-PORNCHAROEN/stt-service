---
name: test-engineering
description: Design, add and run the right unit, integration, E2E and coverage checks for application behavior changes or test-authoring requests. Use for code and test changes.
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
