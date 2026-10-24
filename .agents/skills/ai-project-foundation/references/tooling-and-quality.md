# Tooling and quality gates

Read for source-backed AI review and existing project testing. Foundation setup uses Markdown criteria and AI-agent skills; it does not install a JavaScript checker, helper script, hook or CI gate into the destination project.

## Capability inventory

Inspect the manifest, configuration, source or CI owner needed by each selected deliverable. Discover only the named executable or upstream skill that deliverable requires; do not scan every installed tool or host skill. Record actual versions/paths and distinguish:

| Status | Evidence |
| --- | --- |
| Available | Executable, skill or package exists |
| Configured | Configuration and scope suit the system |
| Verified | Current-revision run with actual outcomes |
| Unavailable | Concrete limitation or missing prerequisite |
| Not applicable | Capability absent by product scope, with reason |

A project manifest may describe existing native commands. They remain project-owned and are run only when existing rules or the task require them.

Use [tool entry points](tool-entrypoints.md) for routing to Markdown criteria,
AI-agent skills and existing project commands. The AI agent reviews semantic
document quality directly; a command result is separate evidence and does not
prove acceptance or automatic host selection.

In setup, use the [setup contract](setup-contract.md) to create and review applicable documents and AI skills. Tool/dependency installation and executable automation are separate, explicit requests. In audit/documents-only, report gaps without installation.

## Graphify

1. Locate the installed upstream skill/executable and read its instructions before graph creation/refresh. If installation is in scope, use [upstream installation](https://github.com/Graphify-Labs/graphify#install) for the actual host/OS and confirm discovery. Commands vary by distribution.
2. Inspect existing `graphify-out/graph.json` scan metadata/manifest for relevant code/test/document coverage and supported revision/mtime/fingerprint evidence.
3. Query actual symbols, paths or English terms, for example `graphify query "authentication session ownership"` when supported. Use upstream `explain`/`path` for relationships.
4. Read identified source to confirm current behavior. Graph discovery is not runtime proof; missing nodes do not establish feature absence.
5. Refresh stale affected scope. Code AST updates and Markdown semantic extraction may use different flows; confirm changed Markdown content was actually read.
6. Report unavailable/incomplete tooling and use targeted `rg` plus source reads instead of inventing graph results.

Exclude secrets, database contents, dependency/build outputs and auth fixtures. Confirm privacy before external source transfer. Preserve hooks/instruction blocks; document reproduction and generated-graph tracking policy.

## Impeccable and UI

Use the [setup prompt](setup-prompts.md#impeccable) and [official reference](https://impeccable.style/#why) when the user requests this tool or the project routes recurring UI work to it. Verify its installation scope and discovery before invoking. If unavailable, follow the project design context and report the missing capability; do not claim the host skill is installed. Documentation-only changes need no UI detector or visual redesign.

For UI work, follow DESIGN.md, product brief and supplied visual references. Have
the AI agent inspect hierarchy, component consistency, accessibility, responsive
states and performance using authorized browser/screenshots/reports. Record the
states reviewed and cite visual evidence in Markdown. Tool-specific detectors and
automated hooks are not part of Foundation review.

## Select test layers by behavior

For code-bearing projects, route implementation and bug-fix work through the
project test-engineering skill. Every behavior change gets an automated test at
the narrowest useful layer; add unit tests for changed domain logic, integration
tests for component boundaries, and E2E for changed critical user journeys. Run
the repository's mandatory baseline every time. Run coverage when changed source
is in the measured scope or when test/coverage configuration changes; read the
uncovered lines and branches instead of optimizing only a percentage. Exact
selection, adversarial cases and evidence live in
[secure and test workflows](secure-testing-workflows.md#test-engineering).

| Layer | Verifies | Useful scenario |
| --- | --- | --- |
| Static/lint/types | Conventions and compatible shapes | Contract/caller mismatch |
| Unit | Domain logic | Boundary values, rounding, transitions |
| Integration | Combined components | Route, validation and transaction |
| E2E | Real user journey | Login, owned-resource action, recovery |
| Visual/accessibility | Appearance and operation | Focus, keyboard, responsive/error states |
| Security | Security invariants | User A cannot access user B's resource |

Assert observable outcomes rather than implementation details or mock calls alone. Reuse sufficient project-owned tests and add scenarios for unverified behavior/risk. The AI agent reviews docs/templates for structure, links, consistency and source support.

Integration/E2E need isolated data, deterministic fixtures, setup/teardown and bounded cleanup. Use temporary databases/tenants and local accounts. Confirm write targets, ports and process ownership before running smoke checks. Verify the native builder accepts the fixture's dependency layout; external dependency junctions may be unsupported. Attribute harness/setup failures separately from application failures and retain both attempts.

## Existing project commands

When project instructions or the current task require execution checks, the AI
agent may use commands already owned by that project. Read the actual manifest,
lockfile and documented command before running one; do not create a new runner
or add JavaScript merely to check Foundation documents. Node, Python, Go, .NET
and other projects keep their own native verification choices.

## Meaningful coverage

Define production-source scope including untested files. Report statements, branches, functions and lines separately. Exclude only generated/irrelevant files with reasons; uncovered critical logic remains a gap.

Measure baseline and set thresholds from critical paths and accepted goals. Preserve stricter gates. Improve scenarios rather than hiding difficult logic; explain denominator/exclusion changes.

Consult installed-version [Vitest coverage configuration](https://vitest.dev/config/coverage), especially include/exclude/threshold behavior. Report backend-only coverage as backend-only.

## E2E and reports

Select critical success, validation, recovery and permission journeys. Use user-facing locators and condition-based assertions. Choose browser/viewports from actual users/product scope.

Isolate server/data from development and production. Check baseURL, server command and reuse policy. Tie prerequisite builds to the test lifecycle. Preserve useful screenshots/traces and document output paths.

Use the installed [Playwright webServer lifecycle](https://playwright.dev/docs/test-webserver) and [HTML report](https://playwright.dev/docs/running-tests#test-reports). Associate artifacts with the actual run/revision; label dated historical reports as baselines.

For visual evidence, read the destination's capture/trace configuration and preserve its policy, including all-test full-page captures when already configured. Inspect relevant current screenshots and expected/actual/diff images for comparison failures; map their paths, route, viewport/state and run/revision to acceptance. Record what was inspected and any unavailable browser/image capability. Capture and semantic review have distinct evidence. Review a proposed change before updating baselines, then rerun comparisons without the update flag. See [recording options](https://playwright.dev/docs/test-use-options#recording-options) and [visual comparisons](https://playwright.dev/docs/test-snapshots).

## AI review and existing project gates

Use Markdown review criteria routed from `AGENTS.md` to the relevant AI skill.
The skill reads acceptance, the current diff/source and project security or design
context, then reports findings and evidence in Markdown. Foundation setup does
not add a project-local hook or CI script.

Existing project-owned gates remain under their current owner. Do not duplicate,
reconfigure or replace them as part of Foundation document setup. If repository
rules require those gates, run them as a separate part of the project task and
report results separately from AI review.

| Change | Additional checks beyond mandatory repository gates |
| --- | --- |
| Docs/instructions | Links, placeholders, metadata and config consistency |
| Domain/API/backend | Relevant unit/integration, types/build, scoped coverage |
| UI/journey | Types/build, relevant E2E and visual/accessibility review |
| Schema/migrations | Constraints, upgrades, compatibility, transactions, ownership |
| Auth/permissions/external input | Abuse cases and scoped security review |

Use native CI runtime and deterministic lockfile installs. Retain failure artifacts under team policy, minimize workflow permissions and prevent secret leakage.

Use the [AI-agent review](ai-agent-review.md) for Markdown-led source and
requirements checks. Executable automation is outside standard Foundation setup.

## Code review and security tools

Review **Spec** against acceptance/design intent/negative cases and **Standards** against boundaries/contracts/lifecycle/repository rules. Use actual diff/source evidence; separate confirmed regressions from optional out-of-scope improvements.

For every code diff, route the change through the installed security diff-review
skill and inspect its evidence. For Codex Security, this is
`codex-security:security-diff-scan`; the full-repository
`codex-security:security-scan` is for an explicit no-diff repository audit, not a
substitute for patch review. If the diff skill/tool is unavailable, perform a
bounded manual review against the changed trust boundaries and OWASP references,
then report that automated scanning was unavailable. Scanner output requires
triage before claiming application exploitation. See [secure and test workflows](secure-testing-workflows.md#security-review) and [schema and security](schema-and-security.md).

## TESTING.md and evidence

Document source configuration, suite selection, data lifecycle, coverage scope/threshold ownership, critical journeys, reports and mock limits. Point to easily discoverable manifest commands rather than duplicating every script.

```markdown
| Check | Exact command | Revision / dirty scope | Outcome | Evidence |
| --- | --- | --- | --- | --- |
| <check> | <command> | <revision and relevant dirty files> | <exit/count> | <report/time> |

Skipped/unavailable: <check, reason and prerequisites>
Resources: <owned temporary data/processes and cleanup outcomes>
```

Exit 0 alone may not cover critical journeys; disclose material scope gaps.

## Requirement coverage and continuation

Use [project workflow](project-workflow.md) and [traceability](../assets/traceability.template.md) to connect accepted IDs to behavior, source, scenarios and current evidence. Requirement coverage differs from code coverage.

Select checks by actual task scope. Changed scoped source/contracts/specs/test configuration invalidate affected evidence; recheck it. Gate success does not establish untested acceptance.

Hand off pointers to canonical spec, decisions, source map and current reports rather than chat history. Record revision/dirty scope in the [handoff](../assets/handoff.template.md) so the next session can assess freshness.

## Architecture enforcement and skill quality

Use [execution and boundaries](execution-and-boundaries.md) for AI review of
module boundaries and accepted invariants. Preserve existing gates and report
baseline violations/limitations; do not create a new helper script by default.

Application tests and skill evals provide different evidence. For skill/routing changes, use [skill evaluation](skill-evaluation.md) with comparable cases to assess routing, scope, outcomes and cost. Keep evals/LLM graders out of automatic application tests and Stop hooks.
