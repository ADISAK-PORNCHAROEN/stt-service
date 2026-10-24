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

## Project testing profile

`pyproject.toml` sets pytest's test root to `tests`, excludes `integration` by
default, and configures Ruff plus strict production mypy checks. There is no
coverage command, numeric threshold, or coverage report currently configured;
do not invent one. `docs/TESTING.md` and root `AGENTS.md` own command invocation
and required gates. Normal tests use fake inference with real filesystem and
SQLite interactions; opt-in real-model tests need a caller-supplied recording
and Whisper weights.

| Changed boundary | Existing evidence to inspect |
| --- | --- |
| CLI, input checks, transcript/export contract | `tests/test_cli.py`, `test_inputs.py`, `test_contracts.py` |
| FastAPI/upload/result behavior | `tests/test_api.py`; `test_http_real.py` for explicit service integration |
| Queue, concurrency, recovery, cleanup | `tests/test_lifecycle.py`, `test_scheduling.py`, `test_progress.py` |
| Whisper engine/settings and comparisons | `tests/test_whisper_engine.py`, `test_profiles.py`, `test_comparison.py` |
| Evaluation allowlist and offline score flow | `tests/test_evaluation.py`, `test_comparison.py` |
| Real model behavior | `tests/test_real_model.py`, `tests/test_http_real.py`; opt-in only |

Choose the layer from the actual changed contract, not merely from the module
name. Use public CLI/API boundaries for user-visible behavior and direct
storage fault tests for transaction/recovery guarantees. A test pass does not
close optimization human text/timing, CPU-performance, GPU, or persistent-
service acceptance gates unless the canonical ticket records those outcomes.

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
