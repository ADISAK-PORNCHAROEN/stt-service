# Project workflow

Read for new-project setup, existing-project adoption or starting/resuming features through this foundation. Use the project's canonical planning and tracker documents; use Markdown instructions and AI-agent skills for project checks.

## Choose the project branch

| Branch | Start from | Preserve | Setup outcome |
| --- | --- | --- | --- |
| New | Brief, users, constraints and starter | Settled stack/provider/product choices | Source pointers, Markdown review criteria, tracker/domain integration and first scoped feature ready for a spec |
| Existing | Source, contracts, tests, configuration, plans/issues and dirty tree | Behavior, design, schema, existing project checks and user work | Current document/source review and one resumable task |

Absent source does not authorize choosing the product/stack for the user. Distinguish pre-existing failures from changes and resolve mandatory failures under repository rules.

## New-project onboarding

1. Read settled decisions; identify consequential unknowns about product, stack, hosting, ownership and visual direction. Ask only where necessary and keep reusable answer pointers.
2. Identify the AI skill and Markdown criteria each selected deliverable needs. Create useful shared instructions and product context; add schema/security/UI guidance only where applicable. Document existing project commands when they are required by project rules. Use the linked [setup prompts](setup-prompts.md) for requested DESIGN.md, Impeccable or Mermaid work.
3. Reuse the project's existing tracker and domain conventions when the user selects that workflow. Do not create tracker accounts, integrations, or tickets as part of routine onboarding.
4. Select one small end-to-end feature and establish its canonical spec/acceptance through the lifecycle below. Avoid speculative backlogs.
5. Have the relevant AI skill review the documents against the source and deliver a foundation report with findings and next action. List any existing project commands separately when required.

Exit: a new collaborator can reach decisions/source/checks and distinguish configured capabilities from proposed design. Foundation setup does not implement the first feature.

## Existing-project adoption

1. Inspect dirty scope, revision and the instructions, plans/issues, contracts, schema, tests and existing project controls relevant to the selected deliverables. Confirm current source.
2. Record existing behavior, documented project checks and AI-review gaps. Retain established document names; link the canonical PLAN/issue section instead of moving all plans to a template.
3. In setup, follow [instruction migration](document-blueprints.md#instruction-migration): archive exact originals and rebuild the shared guide in foundation-v1 format, even when new navigation was already appended. Resolve known document findings and route relevant AI skills. Preserve existing project controls. A historical plan remains history; identify current acceptance rather than promoting stale implementation rules.
4. Map one representative task to requirements/source/tests before scaling. Separate implemented, verified, planned and uncertain status.
5. Follow the lifecycle until durable continuation artifacts exist. Report document workflow separately from actual host/runtime verification.

Exit: existing work resumes from canonical artifacts without retroactive specs for every feature or unrelated architecture changes.

## Feature lifecycle

| Phase | Input / route | Artifact and exit condition |
| --- | --- | --- |
| Discover | Task, glossary/ADRs, scoped source/graph | Existing and target behavior separated; factual unknowns investigated, product decisions identified |
| Align | grill-with-docs for unsettled decisions; codebase-design for unclear interfaces/seams | Settled acceptance, exclusions, interfaces, seams and constraints |
| Specify | Accepted request or existing canonical project plan | Stories, behavior/errors, implementation/testing choices; relevant risks/alternatives |
| Slice | Existing project planning convention when multi-slice work needs it | Independently verifiable work items and blocking edges; small work reuses the current plan |
| Implement | Relevant task skill; tdd when chosen | Accepted behavior and repository rules; new decisions update spec/ADR; scoped implementation |
| Verify | AI-agent review of changed source and scoped security/UI/schema criteria | Current requirement/source map and cited evidence; findings/gaps disclosed |
| Handoff / resume | Established project artifact | Plan/decision/check pointers, dirty scope, blockers and actionable next step |

Match process to the task. A typo or clear reversible edit needs no new interview/spec. Large/high-risk work needs reviewable design before implementation while reusing accepted decisions and authorization.

## Technical design and states

The canonical spec owns settled what/why/how. Use the [technical addendum](../assets/technical-design.template.md) only for missing:

- Actual alternatives/trade-offs, decision status and rationale.
- Contracts/inputs/errors, actors/ownership, transitions and invariants.
- Relevant security/privacy, storage, migration/recovery, i18n/accessibility.
- Accepted examples and verification at approved external interfaces.

Link authoritative schema/contracts/DESIGN.md rather than duplicating them. Proposed choices remain proposed until agreed.

## Requirement/code/test evidence

Use existing tracker IDs or feature-local IDs in [traceability](../assets/traceability.template.md). Map requirement → observable behavior → implementation → scenario → run evidence. Keep unstable paths here rather than in path-free canonical specs.

Implemented requires matching source; verified requires current-scope evidence for accepted behavior. Code coverage cannot replace requirement coverage.

Keep task scope and review freshness in the canonical Markdown spec or handoff. When relevant source or acceptance changes, have the AI skill reopen the affected files and record the current revision and evidence. Scope reviews to relevant source/contracts and exclude generated outputs/secrets.

## Handoff and context budget

Follow the installed destination using the [handoff contract](../assets/handoff.template.md). Send pointers rather than copies and keep canonical artifacts durable before OS-temp handoff.

Resume from handoff, inspect revision/dirty scope, refresh stale pointers and start the next action instead of re-summarizing the project. Changed acceptance/scope updates the canonical spec and invalidates affected verification.

Use the relevant [tool entry](tool-entrypoints.md), inspect inactive/available/
configured/exercised status and recover failed prerequisites through the supported
route. Reuse settled product answers. Verify owned fixture/process cleanup and
leave exact leftovers when automatic review or platform limits prevent it.

AGENTS.md owns shared rules/navigation; task skills own workflows; references own conditional detail; templates use confirmed facts. AI-agent skills inspect meaning, source boundaries and decisions, then record findings in Markdown. No coder/reviewer model roles are prescribed.

## Forward-check before claiming verified

Use scoped disposable workspaces/artifacts:

1. **New:** settled stack/tracker brief; native pointers/config and one canonical spec/map with accepted examples. Optional glossary/ADRs do not create empty-document blockers.
2. **Existing:** canonical plan, custom hooks and dirty user work; reuse the plan/issue, map one task, preserve merges/idempotence and report existing failures honestly.

Also check handoff resume, review freshness after source/spec changes and whether required evidence is present. Keep actual artifacts/results; format/link review does not establish full AI workflow behavior.

## Long tasks, boundaries and measured evaluation

Use [execution and boundaries](execution-and-boundaries.md) for milestones/decisions in canonical plans and AI review criteria for module/data boundaries.

For skill changes or host/project rollout, use [evaluation](skill-evaluation.md) and the [case suite](../assets/evals/cases.json). Choose affected branches and record measured outcomes, corrections, time and usage. Compare matched baseline/candidate before claiming savings; unknown stays unknown. Avoid per-turn evaluation/progress rewriting.
