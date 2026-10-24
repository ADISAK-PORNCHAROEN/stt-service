# Setup prompts

Read for source-backed design guidance and explicitly requested Mermaid work. A Mermaid viewer remains an explicit request. Preserve audit/documents-only scope, existing decisions and tools.

## DESIGN.md

```text
Write or update DESIGN.md following the pattern at
https://getdesign.md/what-is-design-md.
Inspect the existing UI, tokens, components and supplied references first.
Preserve accepted design decisions; document visual direction, semantic colors,
typography, components/states, layout, elevation, design constraints,
responsive/accessibility rules and agent usage with visual acceptance evidence.
Use the current reference format and source-backed values; distinguish proposed
choices from observed behavior. Link implementation sources and the UI catalog.
```

Read [document blueprints](document-blueprints.md#designmd) for the artifact contract. Reach the provided reference when writing the file, not on every turn. If it cannot be read, use the publisher's [collection](https://github.com/VoltAgent/awesome-design-md) or [guide](https://getdesign.md/blog/web-design-md/), recording the fallback. Its linked [format specification](https://github.com/google-labs-code/design.md/blob/main/docs/spec.md) defines supported tokens and section order; confirm current requirements with destination tooling.

Completion: concrete source-backed values, semantic roles, responsive/locale
overrides and implemented component states are covered; accepted identity is
preserved and UI tasks point to DESIGN.md. Review the final cascade and relevant
rendered states; section order and optional tokens alone do not establish quality.

## Impeccable

```text
Use this branch when the user asks for Impeccable or when the project workflow
routes recurring UI work to it. Read its installed skill instructions and
source-backed design guidance. Record the exact source and target paths before
setup. If the user requested project-only setup, copy the complete skill folder
and referenced resources into the supported project-local skills directory;
never install or modify a global copy. Preserve existing files, settings and
callbacks, and verify the project-local skill remains discoverable after
Foundation changes. Keep design documents in Markdown and have the AI agent
inspect relevant rendered states. Do not add hooks unless separately requested.
```

The [official site](https://impeccable.style/#why) describes the tool. Read the installed upstream skill for invocation and design behavior. Follow [tooling](tooling-and-quality.md#impeccable-and-ui) for source-backed AI review.

Completion: context resolves the intended product/design records and the AI
agent records source-backed design findings or remaining questions. For
project-only setup, Impeccable is listed in `requiredSkills` and `skillPaths`
and its local discovery/invocation behavior is verified; otherwise report the
exact missing prerequisite and leave setup partial.

## Database Mermaid and mermaid.html

```text
Inspect the database currently used by this project and generate its diagram
in Mermaid format, with a web viewer available as mermaid.html.
If a database/schema exists, derive an ER diagram from authoritative schema,
migrations and persistence code; show confirmed keys, relationships and cardinality.
If only an agreed database design exists, render it as proposed, not implemented.
If neither exists, prepare the viewer/source structure with a clear pending-schema
state; leave the diagram empty and do not invent tables, relationships or migrations.
Preserve the native stack and existing viewers/docs; report source and render checks.
```

Use [schema and security](schema-and-security.md) for ownership/constraints, [Mermaid ER syntax](https://mermaid.js.org/syntax/entityRelationshipDiagram.html) for notation and [Mermaid integration](https://mermaid.js.org/config/usage.html) for the installed compatible renderer.

1. Inspect schema/migrations/ORM definitions, persistence code and agreed design artifacts. Query codebase discovery first when required. Prefer these sources over inspecting live data; unavailable production access is not permission to create a replacement database.
2. Choose `implemented`, `proposed` or `pending schema` from evidence. Foreign keys and nullability guide optionality; a foreign key alone does not prove every parent has a child. Separate application relationships from enforced constraints and note uncertainty.
3. Keep canonical Mermaid source in the existing schema document or a native artifact such as `docs/schema.mmd`. Make `mermaid.html` render that source via the existing build/generation path, avoiding two independently edited diagrams. For framework public assets, place it in the supported static directory so `/mermaid.html` works; document actual path/URL.
4. In the no-schema branch, provide a pending state, intended source location and next steps. Keep an empty source slot; a TODO node is not an implemented ER model. Prepare integration points without adding database packages or migrations.
5. Use the native/pinned Mermaid renderer and its documented API. Default to local dependencies/assets. External CDN loading is a separate environment choice; show offline/dependency/render failures explicitly. Keep diagram text as data and use strict security settings for labels/input.
6. Verify schema-to-diagram accuracy, syntax with the installed parser/CLI when available, and the served HTML page when authorized browser tooling is available. Verify pending/error states for the scaffold. Report source checks separately from actual rendering; record unavailable browser/parser checks honestly.

Completion: existing/agreed schema is represented accurately, or an explicit pending scaffold exists; source ownership and refresh steps are documented and the viewer's actual verification status is recorded. This documentation work does not authorize database redesign, migrations, deployment or public hosting.
