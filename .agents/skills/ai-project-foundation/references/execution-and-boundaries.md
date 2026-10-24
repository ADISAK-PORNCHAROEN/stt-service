# Execution records and architecture checks

Read execution guidance for multi-session tasks, milestones or durable dependencies/decisions. Read boundaries for module/data setup or changes. Continue the [project workflow](project-workflow.md) using established artifacts and AI-agent review criteria.

## Durable execution state

1. Select the canonical spec/ticket and shared progress location. Reuse fields/sections; otherwise place the [execution record](../assets/execution-record.template.md) beside the spec/in the configured tracker. Avoid duplicate PLANS.md/progress files created only to satisfy names.
2. Record current milestone, completed/pending work, findings, decisions, checks and next action with authoritative pointers. Proposed/unrun remains separate from agreed/passed.
3. Update at milestone completion, consequential decisions/blockers or unfinished handoff. Retain owner/date/revision and relevant dirty scope rather than rewriting chat every turn.
4. Resume from record/spec/review notes, confirm branch/revision/dirty scope and have the relevant AI skill re-review stale sources. Start the actionable next step; changed goals update the spec before progress advances.
5. Large/high-risk implementation needs appropriate owner/domain-review decision evidence. Reuse accepted choices and authorization; small work does not gain an approval round merely from a template.

Preserve installed upstream handoff destinations, including OS temp, after keeping durable progress/decisions/evidence in repository/shared storage. The [handoff](../assets/handoff.template.md) carries pointers. A necessary self-contained execution plan includes only task-relevant context and accessible authoritative references.

Exit: a fresh session can recover the goal, evidenced state, decision rationale and next action without old chat. Verify through the resume [eval case](../assets/evals/cases.json).

## AI review of boundaries

1. Read the project's architecture guidance and the relevant changed source. Select the agreed correctness or security invariants for this task; do not impose another stack's layer model.
2. Map invariant → affected paths/interfaces → expected behavior → source evidence in [architecture rules](../assets/architecture-rules.template.md). Preserve accepted exceptions with their reasons.
3. Ask the relevant AI skill to follow imports, calls, ownership and data flow across the changed boundary. Cite paths and line numbers for findings; distinguish confirmed violations from questions and areas not inspected.
4. Review any existing project-owned test or CI evidence when repository rules require it. Do not create a JavaScript helper, Git hook or new gate to perform this review.
5. Keep criteria few and actionable. Record the reviewed diff/revision, paths, findings, evidence and remaining uncertainty in Markdown.

| Invariant | AI-agent review focus |
| --- | --- |
| Client persistence access through approved API | Trace changed calls/imports to the approved boundary, including aliases/re-exports |
| Allowed module dependency direction | Follow changed imports and report any path that crosses the agreed direction |
| Public API protects module internals | Inspect exported surfaces and changed callers for unintended access |
| Trust boundaries enforce ownership/data shape | Trace input to sensitive operations and compare checks with the accepted invariant |

Exit: the relevant AI skill has reviewed the declared scope, reports evidence for each finding and clearly identifies what it did not inspect. Existing project gates remain separate evidence.

Further guidance: [OpenAI execution plans](https://developers.openai.com/cookbook/articles/codex_exec_plans) and [Anthropic long-running harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents). Adapt useful mechanisms rather than copying all conventions.
