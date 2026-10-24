# Tool entry points

Read when routing project tasks to Markdown guidance, AI skills or existing
project commands. Make the next review action clear without adding a runner.

## Project routing

Create or extend the project's tool guide, commonly `docs/agents/tools.md`.
For each applicable AI review record: trigger, inputs/scope, authoritative sources,
review criteria, expected Markdown findings/evidence and known limits. For an
existing project command, record its documented invocation and owner. Link the
relevant skill and upstream instructions; do not invent aliases or new checkers.

AGENTS.md points to the guide by task. A task skill selects the relevant Markdown
criteria and inherits the project's existing rules. Extract a project
workflow-maintenance skill when instruction repair is recurring and distinct.
Keep one skill per useful workflow, not per command.

## Setup entry point

Run `$ai-project-foundation` through the AI host. The skill creates Markdown
project guidance and agent skills directly; a destination setup command, helper
script or hook is not required. If the user explicitly requests executable
automation, handle that as a separate scoped task.

## Task lifecycle and cleanup

For a selected accepted task, maintain its canonical spec/source/scenario/review
map in Markdown. The AI skill reopens affected sources and criteria after a
source/spec change; record what it reviewed and cite evidence. Preserve existing
project controls and disabled states.

For behavioral experiments record exact owned directories/processes before
creation, preserve evidence under its declared storage policy, then remove owned
temporary resources within authorization and verify absence. If automatic review
blocks cleanup, record the exact leftovers and rejection; never claim deletion or
retry the rejected action through a different tool. Avoid a copied application
when a small self-cleaning fixture proves the needed property.
