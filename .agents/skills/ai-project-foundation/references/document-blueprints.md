# Document blueprints

Read when creating or merging destination documentation. Code fences are templates: fill them with evidence, remove irrelevant sections and retain correct existing information.

## Layout by need

```text
project/
  AGENTS.md
  CLAUDE.md                      # Shared-rule bridge unless explicitly excluded
  PRODUCT.md
  CONTEXT.md                     # Agreed domain vocabulary
  DESIGN.md                      # UI projects
  mermaid.html                   # Requested database viewer/scaffold
  docs/
    ARCHITECTURE.md
    TESTING.md
    SCHEMA.md                    # Persisted data
    SECURITY-MODEL.md
    AI-FOUNDATION-REPORT.md
    agents/skills-checklist.md   # Selected project skill readiness and count
    adr/                         # Consequential decisions
  SECURITY.md
  .agents/skills/
    ai-project-foundation/
      assets/                    # Setup templates
      skills/                    # Markdown AI-agent workflows
    <project-task-skill>/SKILL.md
  <native source, tests, migrations, manifests and CI>
```

Read existing instructions first. Adapt names to established navigation. Monorepos use shared root rules and scoped package/service instructions; confirm loading with the actual host.

The foundation-v1 guide layout is this project's adoption convention, not a
vendor-required Markdown format. Host discovery/import rules remain authoritative.

## Document acceptance

Use the setup contract's applicability list and [delivery template](../assets/document-delivery.template.md)
in the foundation report or existing delivery record. Track the actual canonical
file, owner, required/applicable/excluded/not-applicable reason, source/accepted
reference, content review, links/checks and unresolved work. The delivery list
and foundation manifest record **all** required/applicable paths, not just a
passing subset.
Give each canonical file its own review result. Read prior open review findings;
replace vague grouped claims such as "source-backed documents" with the actual
resolved content, source pointers and remaining defects for each file.

Core setup includes current shared instructions, the CLAUDE bridge unless excluded,
product/current-task acceptance and a durable report. Add architecture/testing for
source projects, a glossary for confirmed domain terms, DESIGN for UI, schema for
persistence, security guidance for real trust boundaries and tool/workflow guides
for integrated capabilities. Honor explicitly requested artifacts as required.

Review existing content before reusing a filename. Fill confirmed missing content
or create the required file during setup. Resolve placeholders, contradictions,
obsolete paths and weak source pointers; preserve original intent/history through
migration. Consequential unknowns remain explicit partial work rather than invented
facts. No empty glossary, speculative schema or retroactive product acceptance is
needed for a document count. Audit reports gaps; setup completes authorized work.

Finish by checking every applicable file and traversing one task -> document/skill
-> source -> native verification/evidence route. Content review and structural
checks are separate evidence; the closing report links the actual reference set.

## Instruction migration

For an existing project, classify each effective rule against accepted intent,
current source and host requirements: current, historical, conflicting or unclear.
Preserve valid intent and framework-managed blocks. A historical sketch may supply
product facts without owning today's implementation instructions.

Rebuild the whole active shared guide using the AGENTS.md layout below. Its
foundation-v1 format is one `<Project> Agent Guide` title and exactly these four
H2 sections, in order: `Working agreements`, `Find the source`, `Read by task`,
`Completion`. Put additional current guidance under those sections. Verified
host-managed blocks are retained separately and recorded in the foundation manifest.
An already-current guide can remain unchanged; the new format is the adoption
default for existing guides as well as new projects.

Before normalizing an existing AGENTS.md/CLAUDE.md, save its exact original bytes
under the repository's existing history location, or `docs/history/agent-instructions/`.
Use a date/content-hash name and a history index recording original path, reason
and replacement. Reuse an identical archive; skip archival when no change is needed.
Use names such as `AGENTS.<date>-<hash>.md`, not another automatically loaded
`AGENTS.md`/`CLAUDE.md`. Historical files have no instruction authority and are
reached only for history.

In Git repositories, mark each immutable archive path `-text` in the existing
`.gitattributes` before staging, so newline conversion cannot change the original
bytes in another clone. Verify the staged Git blob against the original hash.
Scope attributes to the archive paths; keep normal document handling unchanged.

Move still-valid product facts, architecture and task restrictions to their owners;
replace obsolete active instructions with the current rule and source pointer.
An appended correction beside a contradictory rule does not complete migration.
Keep unsettled product choices explicit while fixing independently known facts.
Product visions, old directory trees and proposed agent/team roles are moved to
their canonical owners or the historical record. Preserve their meaning there;
the active guide carries current working rules and conditional pointers.

Before editing, capture the original bytes and SHA-256. After replacement record
the source path, archive path/hash and history index in `foundation.json`
`instructions`. Select mode `created`, `replaced` or `already-current` from the
actual operation; retain valid prior archive receipts on unchanged reruns. An
excluded bridge records the user's explicit scope reason. Review layout, import
and archive integrity directly; source/intent meaning still needs content review.

Review root/nested instructions, host bridges, task skills and TESTING.md together.
They must inherit the same mandatory native gates, then select additional checks
by behavior. Link/archive checks prove preservation and reachability; inspect
meaning separately for obsolete paths, incompatible instructions and invented intent.

## AGENTS.md

Keep shared rules and navigation at the root; reach API/schema detail through conditional pointers. Include system-specific instructions that change behavior. Keep temporary task restrictions in task records rather than permanent working agreements.

```markdown
# <Project> Agent Guide

<System, users and important runtime in one or two sentences>

## Working agreements

- Preserve observed <types, naming and module boundaries>.
- Read commands from <manifest/task runner> and versions from the lockfile.
- Before submission/commit, run <actual mandatory checks>.
- For <critical behavior>, select checks from docs/TESTING.md.
- Keep secrets, local credentials and test/production data out of Git.
- Perform requested reversible local work; use existing authorization for
  push, deploy, production operations and external data transfer.

## Find the source

- Use <available discovery skill/graph> to find entry points and callers.
- Check graph scope/freshness; confirm against current source.
- If unavailable, report the limitation and use targeted source search.

## Read by task

| Task | Read first |
| --- | --- |
| Behavior | PRODUCT.md and domain glossary |
| UI | DESIGN.md and <available page/design skill> |
| Architecture/API | docs/ARCHITECTURE.md and <contract/API skill> |
| Persistence | docs/SCHEMA.md and <database skill> |
| Verification | docs/TESTING.md and <validation skill> |
| Every code change | docs/TESTING.md, <test-engineering skill> and <security-review skill> |
| Security-sensitive changes | docs/SECURITY-MODEL.md and <review skill> |
| Tools/hooks/workflow maintenance | docs/agents/tools.md and <workflow-maintenance skill> |

## Completion

Report changes, reasons, actual validation and limitations.
Preserve existing working-tree changes and disclose unresolved failures.
```

Use confirmed native commands; npm examples do not apply to every stack. For frequently changing frameworks, point to installed-version documentation. See [OpenAI: AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) for Codex discovery/scope.

## CLAUDE.md

Standard setup supplies the shared-rule bridge unless the user excludes Claude
support. It supports later adoption without installing that host. When AGENTS.md
owns shared rules, use:

```text
@AGENTS.md
```

Archive before changing an existing bridge, retain genuine Claude-only rules and
import the shared owner once. File creation does not install Claude skills/hooks.
Verify import loading with [Claude Code memory imports](https://code.claude.com/docs/en/memory#import-additional-files); report unobserved host loading separately.

## PRODUCT.md

```markdown
# <Product>

## Users and purpose

<Users, problem and desired outcome>

## Critical journeys

| Journey | Trigger | Observable success | Failure behavior |
| --- | --- | --- | --- |
| <journey> | <action> | <acceptance> | <error/recovery> |

## Scope and constraints

<Scope, real constraints and unresolved questions>

## Acceptance examples

Given <state>, when <action>, then <observable outcome>.
<Relevant negative/concurrency example>
```

Connect accepted examples to tests. Distinguish owner-approved goals, AI observations and current source behavior.

## CONTEXT.md

```markdown
# <Domain> language

<The business/product context in one or two sentences>

## Language

**<Canonical term>**:
<What this project-specific domain concept is, in one or two sentences>
_Avoid_: <Previously confusing terminology>
```

Follow installed domain-modeling's CONTEXT format when available. Include only
resolved project-specific concepts and real confusing aliases; omit `_Avoid_`
when none are known. General programming terms do not become domain concepts
merely because the repository uses them. Create the glossary lazily after the
first confirmed term; preserve existing glossary names and bounded contexts.

CONTEXT.md owns vocabulary only. Routes/locale codes, libraries, source paths and
fallback mechanics belong in architecture/design; release status and acceptance
in PRODUCT/spec; ownership/state invariants in model/schema; trade-offs in ADRs;
progress and commands in task/tool records. Move misplaced information to those
owners before removing it from the glossary. Review definitions against agreed
language and source; do not infer new product commitments from implementation.

## DESIGN.md

Use the [DESIGN.md setup prompt](setup-prompts.md#designmd) and requested [getdesign.md pattern](https://getdesign.md/what-is-design-md). The publisher's [collection](https://github.com/VoltAgent/awesome-design-md) and [current guide](https://getdesign.md/blog/web-design-md/) provide examples/fallbacks if the requested page exposes only a loading shell.

For an existing UI, extract observed tokens, components and screens while preserving accepted identity. For a new UI, record the supplied direction and explicit assumptions. The publisher's guide links the [DESIGN.md format specification](https://github.com/google-labs-code/design.md/blob/main/docs/spec.md): optional supported YAML tokens plus ordered Markdown sections. Confirm current keys/order before writing; omit irrelevant sections and place additional guidance under relevant subsections. Existing code owns implementation values; documented snapshots cite source/revision and explain semantic roles.

Make the document sufficient for the next scoped UI change: concrete color roles,
type sizes/weights/line heights/tracking, container/gutter/gap/padding values,
breakpoints, radii, borders/shadows and implemented variants/states. Trace the final
CSS cascade and inspect representative rendered values when possible; explain
multiple canvas/header/surface tokens and responsive or locale overrides. Calling
an approximate style “fluid” or referring every value back to CSS is insufficient.
Use formulas when the implementation is fluid. Missing YAML alone is not a defect.

```markdown
# <Product> Design System

## Overview

<Mood, density, philosophy, owner-approved references and evidence/date>

## Colors

<Roles, observed values/source pointers, contrast and state usage>

## Typography

<Font sources, hierarchy, weights, line height and wrapping rules>

## Layout

<Spacing rhythm, grids, alignment and whitespace rules>

### Responsive and accessible behavior

<Breakpoints, collapse strategy, touch targets, keyboard, focus,
 labels, contrast, reduced motion and meaningful imagery>

## Elevation & Depth

<Surface hierarchy, borders, shadows and depth>

## Shapes

<Source-backed corner/border rules; distinguish unmeasured browser defaults>

## Components

<Reuse/variants; buttons, cards, fields and navigation;
 loading, empty, error, success, disabled, validation and recovery>

## Do's and Don'ts

<Accepted patterns, anti-patterns and rationale>

### Agent usage and visual acceptance

<Which work reads this file; implementation/token/catalog pointers;
 critical surfaces, viewport/theme/state and current visual evidence>
```

Impeccable applies the agreed brief; read its installed workflow before invoking tools. Keep existing design decisions authoritative.

## Architecture and ADRs

Document entry points, responsibilities, allowed dependencies, external boundaries and a critical journey. Link actual sources; use Mermaid where relationships become clearer.

Create an ADR for a consequential trade-off whose rationale needs to survive:

```markdown
# <Decision title>

<Context, chosen alternative and reason in one to three sentences>
<Consequences or implementation pointer where useful>
```

## API and event contracts

Use the native authoritative contract: OpenAPI, GraphQL, Protobuf or shared types. Describe actual inputs/outputs, validation, errors, identity/authorization, pagination and compatibility. Connect contract ? implementation ? callers ? integration tests.

Edit the authoritative input before regenerating clients/types/docs with compatible tooling. Follow generated-output policy and verify unchanged inputs regenerate without a diff. Human API documentation points to the contract instead of owning another schema copy.

Use [schema/security blueprints](schema-and-security.md) for data/security and [tooling/quality](tooling-and-quality.md) for TESTING.md/evidence. Requested database visualization follows the [Mermaid prompt](setup-prompts.md#database-mermaid-and-mermaidhtml).

Use the [AI-agent review workflow](ai-agent-review.md) for source-backed review criteria and Markdown findings.

## Project task skill

```markdown
---
name: <project-task-name>
description: <Specific scope and distinct trigger>
---

# <Task>

## Workflow

1. Establish input/scope; read <authoritative task source> and relevant AI skill.
2. Inspect <project-specific sources> against the Markdown review criteria. Record
   source paths/lines; on uncertainty, state the exact question or missing evidence.
3. Review existing project results when required. Record their owner and actual
   outcome separately from the AI review; clean up only resources created by the task.

## Completion

<Reviewed scope, source-backed findings, required existing project results and next action>
```

Shared rules stay in AGENTS.md. Task skills own task-specific review criteria; references load by branch.

For every code-bearing project, create two automatically discoverable project
skills alongside stack-specific workflows. Start from the bundled assets in
`assets/project-skills/`, retaining their methods and direct primary-source links
under the [installation contract](secure-testing-workflows.md#install-or-repair-the-project-skills).
Every setup/repair supplies each skill's internal contract: test-engineering's
`references/testing-contract.md` and security-review's `references/review-contract.md`.
Keep source principles/local mappings there, link them directly from SKILL.md
with their read conditions, and register both in `foundation.json` documents.
Adapt project facts, AI review criteria and report locations:

- Test engineering triggers on code behavior changes and test-authoring requests.
  It inherits native mandatory gates and chooses unit/integration/E2E/coverage
  based on the changed behavior.
- Security review triggers on every code diff, including executable config,
  dependencies and CI changes. It invokes the host's diff-review capability;
  whole-repository scans remain for explicit audit requests.

Read [secure and test workflows](secure-testing-workflows.md) for the references,
Codex Security route, result evidence and harness acceptance. Root routing,
test/security skills and their contracts, TESTING.md, quality profiles and CI must
agree on command ownership and verification/evidence routes.

## Feature artifacts

Read [project workflow](project-workflow.md) for feature adoption and existing tracker/domain conventions.

For setup or skill-routing changes, create the project skill checklist from
[`skills-checklist.template.md`](../assets/skills-checklist.template.md). Keep
its selected-skill total and complete/incomplete counts aligned with the
manifest; report runtime discovery separately from installed files.

- [Technical design](../assets/technical-design.template.md): alternatives, states and risks supplementing the canonical spec.
- [Traceability](../assets/traceability.template.md): requirement IDs, source/test locations and revision-bound outcomes outside path-free specs.
- [Handoff](../assets/handoff.template.md): pointers, decisions, checks and next action at the installed skill's destination.

Reuse the project's selected tracker and domain configuration, preserving canonical paths, glossary names, shared rules and host bridges. User-level tool availability alone does not configure a repository or create project planning artifacts.

## Execution and enforcement artifacts

- [Execution record](../assets/execution-record.template.md): milestones, discoveries/decisions, verification, recovery and next action in the canonical tracker/plan; reuse existing fields.
- [Architecture rules](../assets/architecture-rules.template.md): accepted boundaries, AI review criteria, source evidence and known limits.
- [Eval record](../assets/evals/run-record.template.md): real fresh-session outcomes, criterion evidence and metrics; follow [skill evaluation](skill-evaluation.md).

Use [execution and boundaries](execution-and-boundaries.md) for rollout. Add task-specific pointers rather than loading all artifact details into root rules.
