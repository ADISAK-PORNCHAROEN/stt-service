# Security review and test engineering

Read when authoring or routing the two per-project skills required for code
projects, or when reconciling AGENTS.md, TESTING.md, verification skills, native
gates and CI.

## Evidence behind the workflow

- [OpenAI's code-verification article](https://alignment.openai.com/scaling-code-verification/)
  reports automated review on every PR at OpenAI and many engineers using
  `/review` before pushing. It frames review as defense in depth alongside
  behavioral testing and favors high-signal findings over maximizing recall.
- [Anthropic's `/security-review` guidance](https://support.anthropic.com/en/articles/11932705-automated-security-reviews-in-claude-code/)
  recommends on-demand checks and PR automation as a complement to existing
  security and manual review. The [security-engineering example](https://www-cdn.anthropic.com/58284b19e702b49db9302d5b6f135ad8871e7658.pdf)
  describes its security team using Claude Code with test-driven development.
- Google's [code-review checklist](https://google.github.io/eng-practices/review/reviewer/looking-for.html)
  asks for suitable unit, integration or E2E tests in the same change and checks
  that they would fail if the implementation broke. Its [testing strategy](https://testing.googleblog.com/2021/06/how-much-testing-is-enough.html)
  calls for a solid unit base, integration testing and E2E coverage of critical
  user journeys. Its [coverage guidance](https://testing.googleblog.com/2020/08/code-coverage-best-practices.html)
  treats coverage as a lossy gap-finding signal, not a quality score or universal
  percentage target.
- [OWASP Top 10:2025](https://top10.owasp.org/2025/0x00_2025-Introduction/)
  organizes common web risks; [ASVS 5.0.0](https://github.com/OWASP/ASVS/tree/v5.0.0/5.0)
  supplies versioned verification requirements. The [Secure Code Review Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Code_Review_Cheat_Sheet.html)
  distinguishes baseline audits from incremental diff reviews. The [Secure Coding with AI Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Coding_with_AI_Cheat_Sheet.html)
  calls out adversarial tests, human review of test edits and risks from an agent
  weakening tests or trusting its own generated test suite.

These sources support the workflow design below; they do not establish a single
company-wide policy beyond each source's explicit statements. OWASP Top 10 is an
awareness list, not exhaustive proof of security or a substitute for applicable
ASVS requirements and the project's threat model.

## Install or repair the project skills

This required packaging is foundation policy using progressive disclosure:
essential steps in SKILL.md, detailed mappings in directly linked references.
See [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills) and
[Anthropic: Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).

This installation contract covers only the two named Foundation-owned project
skill folders. It does not authorize replacing their parent directory or
removing sibling, host-level or upstream skills. Follow the
[setup contract](setup-contract.md) for the before/after preservation record.

Every setup/repair of a code-bearing project must supply both complete project
skill folders from `assets/project-skills/`. Read each bundled SKILL.md and its
contract before extraction. Create or reconcile these required destination files:

| Skill | Required internal reference | Read before |
| --- | --- | --- |
| test-engineering | `references/testing-contract.md` | Selecting layers, interpreting coverage or reviewing test edits |
| security-review | `references/review-contract.md` | Selecting risks, requirements or abuse cases |

Keep the essential workflow and a direct local contract pointer in each SKILL.md.
Its contract owns detailed source principles and project mappings: retain every
bundled primary-source URL, explain its role, and connect it to actual source/test
paths, native check owners, evidence or justified exclusions. Also retain the
compact direct source list in SKILL.md for provenance and retention diagnostics.
Adapt verified commands, evidence locations and boundaries; preserve an existing
contract when it already meets these requirements, and repair stale mappings.
Read relevant primary-source text when establishing/revising a mapping and record
unavailable reads honestly. The internal contract must be usable without copying
an entire external manual or depending on a network fetch for every ordinary run.

Treat existing `TESTING.md` and `SECURITY-MODEL.md` as inputs for verified project
facts: commands, fixtures, coverage scope/thresholds, critical journeys, assets,
trust boundaries and accepted invariants. Rebuild the skills' methods from the
bundled Google/OWASP guidance, then reconcile outdated procedures in those project
documents. A wrapper that only links to old documents leaves skill extraction
incomplete, even when those documents contain the external references. Preserve
accepted project constraints, reporting policy, custom tooling and disabled controls.

Route both AI-agent skills from the root guide and keep their names/paths in
`requiredSkills` and `skillPaths`. Add both internal contracts to
`foundation.json` documents as part of the expected structure. Preserve existing
project-owned quality gates and CI; Foundation adds no checker scripts or hooks.

Give every required skill file a row in the delivery list. Review the required
files in both generated folders against the bundled assets:
open each `SKILL.md` and contract, follow the direct local contract pointers, and
confirm source retention and project mappings. Use the repository's existing
native validator only when it is already part of the required workflow for those
files. Report both skills and contracts, retained sources, local adaptations,
reconciled documents and applicable checks before declaring setup complete. A
file/path review does not prove source application or fresh-session discovery;
report those outcomes separately.

## Security review

The project skill description must trigger on implementation, bug fixes and
changes to application code, security configuration, dependencies, CI workflows
or other executable boundaries. Run it after the relevant diff exists so review
covers actual changes.

For Codex Security, choose by artifact:

| Request/artifact | Skill |
| --- | --- |
| Working-tree patch, commit, branch diff or PR | `codex-security:security-diff-scan` |
| Whole repository or scoped directory audit with no diff | `codex-security:security-scan` |
| Deep multi-pass repository audit explicitly requested | `codex-security:deep-security-scan` |

The full-repository scan is not a substitute for review of each patch. If the
host lacks the applicable scanner, perform a bounded manual diff review and
record that automated scanning was unavailable. Do not claim that the project
was certified against OWASP or is vulnerability-free.

Review the project security model and trace changed sources, validation and
transformations to sensitive sinks across trust boundaries. Consider the
relevant OWASP Top 10:2025 categories and select versioned ASVS requirements only
when they apply. Examine negative/abuse cases such as unauthorized resource
access, malformed or hostile input, unsafe output, exceptional behavior,
dependency/CI integrity and sensitive logging as the changed path warrants.
Use scan findings as candidates until reachability, preconditions and impact are
validated. Preserve user work; a review-only request must not grow into a fix or
external issue without the corresponding authorization.

Record the reviewed base/head or dirty scope, paths, tool/mode, validated
findings, coverage gaps and actual evidence. Findings and test output must not
include credentials or private data.

## Test engineering

The project skill description must trigger on behavior changes and test
authoring, including tests requested without an implementation change. For every
production behavior change, add or update a regression test at the narrowest
useful layer. Define the expected behavior from accepted requirements or current
contract independently of the generated implementation. Add invalid-input,
boundary, authorization, failure/recovery or concurrency cases where the changed
behavior creates those risks.

Select layers by the boundary changed:

| Layer | Prefer when |
| --- | --- |
| Unit | Pure domain logic, transformation, state transition or boundary values |
| Integration | Multiple modules, route/handler, persistence, identity or external adapter interact |
| E2E | A critical user journey, rendered route, browser interaction, public headers or cross-layer recovery changes |
| Coverage | Changed production code is in the configured scope, coverage settings change, or uncovered risk needs evidence |

Run the repository's mandatory baseline on every submission. Run E2E for affected
critical user journeys and coverage for touched measured code; do not claim a
layer passed when it was skipped. Inspect uncovered statements and branches in
critical/changed paths. Keep the configured threshold if one exists; do not raise
or lower thresholds merely to turn a run green. Do not weaken/delete an existing
test, assertion or quality gate to pass CI without preserving the behavior and
reviewing the reason. An agent-authored test pass alone is not security evidence.

## Agent review alignment

Use Markdown as the source of review criteria. The project security and test
skills read the changed source, relevant contracts and existing project guidance,
then report concrete evidence and unreviewed areas. Foundation setup does not add
JavaScript harness checks, quality profiles or hook handlers. Preserve existing
project-owned tests and CI without extending them for Foundation document review.

Review required skill files, direct local links, metadata and primary-source
references against the bundled assets. Open each required `SKILL.md` and
contract, follow its local links, and compare its guidance with the actual source
and existing project rules. Do not treat file presence or a heading match as
semantic review. Report missing paths, unsupported claims and stale commands in
Markdown, then repair the owning document or skill.

At the end of a code task, report which AI skill reviewed the change, the exact
scope and paths, evidence-backed findings, any existing project commands run,
revision/dirty scope, report location and remaining gaps. Keep AI review separate
from existing application test results and unobserved host behavior.
