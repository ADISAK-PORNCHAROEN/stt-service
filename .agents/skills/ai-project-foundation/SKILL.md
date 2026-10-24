---
name: ai-project-foundation
description: Set up AI coding workflows with Markdown instructions and AI-agent skills, then review them against source. Project checks use agents and Markdown criteria; this skill provides no checker scripts or hooks. Use for onboarding, audits or documents-only adoption, not routine feature implementation.
---

# AI Project Foundation

Establish product goals, system boundaries, coding conventions and verifiable outcomes for AI-assisted development. Adapt to the destination's native stack and preserve existing decisions.

## Reuse

Install this skill in the AI host's skill directory. Project setup creates Markdown instructions and AI-agent skills in the destination; it does not add a Foundation checker or executable hook. If the host requires a project-local skill, include its `SKILL.md`, linked references, agent metadata and static templates. See [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills).

```text
Use $ai-project-foundation to set up this project's AI coding workflow.
Inspect existing instructions and source; fill gaps with Markdown guidance and AI
skills while preserving the stack, design, conventions and existing controls.
Install selected skills in the project only when requested; never modify global
skill installations or settings. Verify every skill the project guide routes to.
Report what the AI reviewed and any existing project checks separately.
```

An invocation to set up/adopt the workflow defaults to `setup`: create applicable project instructions and AI-agent skills, then have the relevant agent review them against the source. Use `audit` for inspection requests and `documents-only` when the user limits work to documents. Tool installation and executable automation are separate, explicit requests. Read [Setup contract](references/setup-contract.md) for required deliverables, applicability and completion; it governs every setup branch.

## Read by branch

| When | Reference |
| --- | --- |
| Setup/adoption scope, required deliverables or incomplete rollout | [Setup contract](references/setup-contract.md) |
| New/existing onboarding or starting/resuming a feature | [Project workflow](references/project-workflow.md) |
| Writing or merging agent/product/design/architecture documents | [Document blueprints](references/document-blueprints.md) |
| DESIGN.md pattern, Impeccable installation, or database Mermaid/mermaid.html prompts | [Setup prompts](references/setup-prompts.md) |
| Discovery, design tooling, tests, coverage, E2E or CI | [Tooling and quality](references/tooling-and-quality.md) |
| Per-change security review or test selection | [Secure and test workflows](references/secure-testing-workflows.md) |
| AI-skill routing, existing project commands or experiment cleanup | [Tool entry points](references/tool-entrypoints.md) |
| Reviewing project requirements, source or existing work | [AI-agent review](references/ai-agent-review.md) |
| Persistence, identities, public input, external integration or AI/tool risks | [Schema and security](references/schema-and-security.md) |
| Multi-session work or module/data boundary changes | [Execution and boundaries](references/execution-and-boundaries.md) |
| Changing skill routing or measuring quality/cost | [Skill evaluation](references/skill-evaluation.md) |

Load only relevant branches. This workflow connects existing controls; it does not prescribe model roles, replace the stack or interview the user for every task.

## 1. Discover scope and current capabilities

1. Read effective repository/host/nested instructions. Inspect the working tree and preserve existing work.
2. Establish `audit`, `documents-only` or `setup` from the request and existing authorization. Setup authorizes reversible Markdown and AI-skill changes; apply the setup contract and do not infer authorization to add executable checks or hooks.
3. Build the setup worklist from the request, source and applicable deliverables. Inspect only the manifests, configuration, source and reports needed for that worklist. Follow the [Graphify workflow](references/tooling-and-quality.md#graphify) only when code/content discovery is needed, then confirm relevant results against current source.
4. Identify users, product goals, critical journeys, data ownership, deployment boundaries and supplied design references. Ask only for consequential information that cannot be inferred; continue independent work.
5. Record capability, source/config, status, gap and next action. Distinguish `available`, `configured`, `verified`, `unavailable` and `not applicable`.
6. Choose the new/existing branch from source/manifests, capture its baseline and follow the rollout guide. Preserve pre-existing host, upstream and project skills; update only exact Foundation-owned paths. Enumerate the requested and workflow-routed skills, install them at the requested scope, and verify each selected skill remains installed and discoverable. A project-only request requires selected project skills under a supported project-local path and forbids global changes. For an existing older Foundation install, remove legacy Foundation checker artifacts and references and verify their absence under the [setup contract](references/setup-contract.md#perform-the-setup). Verify named upstream skills such as Impeccable before routing them; do not treat disk presence alone as discoverability or invoke explicit-only skills automatically.

Exit: native stack/package manager, effective rules, edit scope and evidenced gaps are known; product/design assumptions are explicit.

## 2. Establish document ownership

Read [document migration and the new guide format](references/document-blueprints.md#instruction-migration) before writing shared instructions. Rebuild the active AGENTS.md from that guide, archive its exact original first, and move valid product/architecture/history facts to their owners. Retain verified host-managed blocks and current project rules within the new layout. Fill templates with confirmed facts and create only artifacts the system needs:

| Artifact | Owns | Read for |
| --- | --- | --- |
| `AGENTS.md` | Shared rules, navigation, quality gates and action boundaries | Work in that scope |
| `CLAUDE.md` | Shared-rule import, usually `@AGENTS.md` | Standard setup bridge; honor explicit host exclusions |
| `PRODUCT.md` | Users, journeys, acceptance and product scope | Behavior changes |
| `CONTEXT.md` | Agreed project-specific domain vocabulary | Domain modeling |
| `DESIGN.md` | Accepted visual system and interaction | UI work |
| `docs/ARCHITECTURE.md` | Boundaries, entry points and data flow | Structure/integration changes |
| Native API contract | Requests/responses/events and compatibility | API/integration changes |
| `docs/SCHEMA.md` | Entities, constraints, ownership, ERD and migrations | Persistence changes |
| `docs/TESTING.md` | Suite selection, isolation, coverage and reports | Verification |
| `SECURITY.md` | Reporting policy and security-model pointer | Security maintenance |
| `docs/SECURITY-MODEL.md` | Trust boundaries, abuse cases and invariants | Risky paths |
| `docs/agents/skills-checklist.md` | Selected project skills, install completeness and discovery status | Setup and skill changes |
| `docs/adr/` | Consequential trade-offs and decision rationale | Durable decisions |

Names are navigation conventions, not automatic loading. Put conditional pointers in `AGENTS.md` or task skills. Keep each rule authoritative in one place; use imports/links elsewhere. Preserve host-specific rules. Record durable conventions in repository instructions and task-only restrictions in the task record.

Exit before AI review: use the [document delivery list](references/document-blueprints.md#document-acceptance) to review shared instructions, glossary and design separately and resolve known local defects. Create every required/applicable file from its owner or bundled template, filling confirmed facts as they are discovered. Keep required paths in the foundation manifest and delivery list. Final review opens those paths and checks their content against source; record semantic review and unobserved host loading separately.

## 3. Add task skills where a distinct workflow exists

Use supported discovery directories and `SKILL.md` frontmatter with `name` and a discriminating `description`. Put conditional detail in `references/`; keep project checks in Markdown instructions for AI agents.

Before changing a skill location, capture the exact affected directory inventory and selected skill files. Update only Foundation-owned skill paths; preserve sibling, host-level, upstream and project skills. The selected skill list must include every skill explicitly requested and every skill the new project guide routes to as a normal workflow. For project-only setup, install those selected skills locally when the supported host allows it; do not modify global installations/settings or count a host-global copy as a project deliverable. Verify local discovery and invocation policy for every selected project skill; if any is absent, mark setup partial and give its exact gap.

Required for every code-bearing project: create or repair both complete skill folders from bundled assets under the [installation contract](references/secure-testing-workflows.md#install-or-repair-the-project-skills). Every setup/repair supplies `test-engineering/references/testing-contract.md` and `security-review/references/review-contract.md`, maps sources to verified project checks/boundaries, routes each contract directly from its `SKILL.md`, and records both paths in the foundation manifest and delivery list. Read each bundled contract before writing or routing its skill. Add other skills for recurring project-specific workflows such as discovery/Graphify; API contract-to-handler-to-caller tests; backend suites/coverage/HTTP smoke; page composition/design/UI review; schema/ownership/migrations; or source-derived documentation.

Inspect recurring project work and create project skills for distinct workflows that benefit from project knowledge. Verify any selected upstream skill before routing to it; preserve its invocation policy and do not create duplicate replacements. Each project task skill states trigger, inputs/scope, authoritative sources, outputs, failure recovery, AI review criteria and completion. Use Markdown instructions that let the agent inspect and report findings. Add workflow-maintenance guidance when recurring setup/repair differs from application work. Use real files in task routing; a table alone does not complete extraction.

When existing project tools matter, document their actual commands, owner and limits in a compact [tool entry point](references/tool-entrypoints.md). Route semantic review to AI skills; do not add setup/check scripts. Root rules point to relevant guidance; task skills load only needed capabilities.

Route to `domain-modeling`, `codebase-design`, `tdd` and `handoff` only when the selected workflow needs them and their actual availability is verified. For explicit-only skills, point to the explicit invocation and preserve upstream prerequisites/decisions. For project-only setups, list selected project-local skills in the manifest rather than relying on a host-only route.

Exit: triggers are distinct; both default skill folders and every additional selected skill contain their required files/resources and applicable project mappings, and are routed from the project guide. `requiredSkills` and `skillPaths` match all project-local skill deliverables. Review declared paths, local links, discoverability and invocation policy against actual files. Do not represent unavailable plugins or commands as installed.

## 4. Use AI agents for project checks

Use Markdown criteria and the relevant AI-agent skill to review changed documents, source and requirements. For code changes, route the diff through the security-review and test-engineering skills; they inspect the actual change and report concrete evidence. Do not add Foundation JavaScript checkers, helper scripts, Git hooks or CI gates as part of standard setup.

Existing project-owned test, lint, type and build commands remain governed by that project's instructions. Run them only when the task or existing project rules call for them, and report their outcomes separately from the AI review. Tool installation or new executable automation requires an explicit request. See [Tooling and quality](references/tooling-and-quality.md) for review scope and evidence.

Exit: the relevant AI agent has reviewed every required/applicable path against its Markdown criteria, findings cite source evidence, and any project-native checks that were required are reported accurately.

## 5. Establish schema and security workflows

Define entity ownership and invariants before implementation. Confirm existing migrations/source; document contracts, failure behavior, transactions and compatibility, with isolated-data verification.

Security review records scope/revision, trust boundaries, concrete attack paths, evidence and confirmed/candidate/coverage-gap distinctions. Route every code diff through the installed diff-review skill; use a whole-repository scan only for an explicit repository audit. Keep findings/fixes in authorized local artifacts.

Workflow setup and executing a security scan are separate deliverables. Use authorized targets and isolated data. Production operations, deployments, publishing findings and external data transfer require authorization covering those actions.

Exit: invariants/verification match the actual system and reported finding status stays within available evidence.

## 6. Verify and hand off

1. Finish required/applicable files, the foundation manifest and `docs/agents/skills-checklist.md`, then complete targeted final review as described in the [setup contract](references/setup-contract.md#perform-the-setup). Review each declared path and content separately; file presence is not semantic acceptance. Keep the portable skill free of destination names, machine paths, ports and databases.
2. Follow one representative journey: find entry point/caller, relevant design/schema, appropriate checks and acceptance evidence. Documents-only traces documents/source without implementing a feature.
3. Have the relevant AI-agent skill review the required paths and follow their local links. Record the files reviewed, source evidence, findings and any project-native commands that existing rules required. Do not install or invoke a Foundation JavaScript checker as the project's review mechanism.
4. Write the destination's existing foundation report or `docs/AI-FOUNDATION-REPORT.md`: findings, changes, capabilities, actual checks, gaps and next commands. Include the selected-skill total, complete/incomplete counts, and a link to the checklist. In audit/documents-only, list unconfigured/unrun items and their next steps.
5. For workflow or routing changes, have a fresh AI session use affected representative cases and record actual outcomes. Separate agent behavior from simple file/link review; do not use a helper script to grade semantic quality.
6. Trace canonical spec, decisions, ticket dependencies, requirement/code/test evidence and handoff. Distinguish document traversal, program checks and actual host behavior.

Done: every required/applicable setup deliverable is implemented and checked, documents and project skills connect to source, the skills checklist reports the selected-skill total and complete/incomplete counts, and required checks pass. A missing prerequisite must have an attempted local remedy and concrete blocker evidence. Remaining required work means `partial setup` or `blocked setup`, even when documented honestly; a list of next commands does not make setup complete. Separate unavailable host dispatch/remote verification from completed local configuration.

## Keep the foundation current

| Change | Update the authoritative source |
| --- | --- |
| Behavior/acceptance | Product/spec and behavior tests |
| Domain terms | Domain glossary |
| Boundaries/integration | Architecture; ADR for consequential trade-offs |
| Visual rules/interaction | DESIGN.md and visual evidence |
| Data shape/ownership/migrations | Schema, contracts and security invariants |
| Runners/commands/coverage | Configuration and suite-selection guidance |
| Permissions/auth/trust | Security model and abuse-case tests |
| Stale graph/inventory | Affected-scope upstream refresh |

Prefer event-driven updates. Add a background loop only when requested, with interval, start/status/stop, lock, errors and evidence from multiple real runs. Distinguish UI polling from source scans; show stale/disabled state and preserve the user's stopped state.

A useful report states configured capability, executed revision/scope, report location and unavailable checks. Document count or a success badge alone does not establish runtime behavior.
