# Testing standards and project mapping

Read before selecting test layers, interpreting coverage or reviewing test edits.
During foundation setup/repair, adapt this contract to verified source and native
configuration. Retain every source below and document how its principle affects
the project's checks, including justified exclusions. Native commands, thresholds
and fixture ownership remain authoritative in the manifest, configuration and
project testing guide; link those owners from the generated contract.

## Sources and application

| Source | Principle to apply | Project mapping to establish |
| --- | --- | --- |
| [Google: How Much Testing is Enough?](https://testing.googleblog.com/2021/06/how-much-testing-is-enough.html) | A unit-test base, integration boundaries and E2E for critical user journeys | Identify real behavior/boundaries, relevant existing suites and missing critical journeys |
| [Google: Code Coverage Best Practices](https://testing.googleblog.com/2020/08/code-coverage-best-practices.html) | Coverage is a gap signal; inspect changed uncovered lines/branches and assertion quality | Identify measured production scope, accepted gates, reports and important unmeasured behavior |
| [Google code review: What to look for](https://google.github.io/eng-practices/review/reviewer/looking-for.html) | Suitable tests accompany behavior changes and detect broken implementation | Derive expected results from accepted requirements and review mocks/assertions against the actual boundary |
| [OWASP Secure Coding with AI Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Coding_with_AI_Cheat_Sheet.html) | Adversarial cases and independent review of AI-authored test changes | Identify negative/recovery cases for the touched trust boundary; preserve assertions and gates |
| [OpenAI: A Practical Approach to Verifying Code at Scale](https://alignment.openai.com/scaling-code-verification/) | Behavioral testing and code review provide complementary evidence | Connect native test results with the separate diff review and accepted evidence workflow |

These public sources inform project policy; they do not prescribe one universal
company workflow or coverage percentage. Read the relevant primary-source text
when establishing or revising a mapping. Retain unavailable links and report
failed reads; distinguish source guidance from accepted project exceptions.

## Select checks from changed behavior

For each affected boundary, record the accepted observable result, relevant
source/test paths, native check and evidence location. Use units for local logic,
integration tests for interacting modules/services, and E2E for changed critical
user journeys. An inapplicable layer needs a reason grounded in the actual system;
an applicable layer with no runner remains an evidenced gap.

Inherit mandatory native gates from the project quality profile. Inspect changed
production coverage and uncovered branches when in scope; preserve accepted
thresholds. Separate coverage for production files from test/helper rows and
report unavailable measurements. Native configuration owns the numeric gates.

For a bug fix, demonstrate the regression against broken behavior and the pass
after an authorized correction where feasible. Review test diffs for deleted
cases, weak assertions, expectations copied from buggy code and mocks replacing
the boundary. Preserve prior failures as separate evidence.

## Connect the workflow and evidence

The generated SKILL.md routes here directly and states the local execution root,
native command owners, failure recovery and completion. Connect security-sensitive
cases to the installed security-review skill and the project's evidence owner.
Record selected layers/principles, exact commands, revision/dirty scope, exits,
coverage scope/gaps, inspected artifacts and skipped/unavailable checks.
Keep fixture isolation, cleanup and custom/disabled controls consistent with
the project's existing harness and accepted action boundaries.
