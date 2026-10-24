# AI-agent review

Use this workflow when checking project instructions, requirements, implementation or an existing task. The AI agent reads Markdown criteria, inspects the current source and reports evidence in Markdown. Foundation does not install a JavaScript checker, a helper script, a Git hook or a CI gate for this review.

## Review steps

1. Read the applicable `AGENTS.md`, the accepted requirement/specification and the relevant architecture, design, schema or security guidance.
2. Establish the review scope from the requested paths, current diff and affected callers. Preserve unrelated user changes.
3. Turn each accepted requirement into an observable question. Follow changed data and control flow through callers, validation, ownership checks, side effects and error paths.
4. Inspect existing tests or project reports as context when they help establish expected behavior. Do not claim a test passed unless an actual project-owned command was run and its result was observed.
5. Report concrete findings with severity, file and line, affected behavior, evidence and a focused remedy. Separate confirmed findings from questions, out-of-scope observations and uninspected areas.
6. Record the reviewed revision/diff, paths, criteria, findings and any existing project command results in a Markdown review note.

## Upgrade from an older Foundation install

For every setup or repair of an existing project, check for artifacts created by previous Foundation versions. A completed upgrade has no active Foundation-owned JavaScript checker/helper files (including `.mjs` scripts), hooks, configuration, routing references, or project-local planning-skill copies that the old Foundation setup installed. Remove those legacy artifacts as part of the upgrade; the current Foundation package and destination workflow do not need them. This is an ownership rule, not a ban on application `.mjs` files or user/upstream skills.

Establish ownership before removal: inspect the known legacy Foundation paths, their tracked/untracked state and diffs, and read `.git/ai-project-foundation/hooks-install.json` when it exists. Follow prior manifests or reports to locate references. Keep the inspection targeted to Foundation-owned paths and configuration; do not sweep the project for every `.mjs` file.

- Remove old files under `.agents/skills/ai-project-foundation/scripts/` and `.agents/skills/ai-project-foundation/assets/codex-hooks/` when they are unmodified Foundation copies.
- Remove obsolete project-local planning-skill copies and their active routes only when the prior Foundation manifest, delivery report, Git history or file provenance confirms that Foundation installed them. Preserve user-owned or upstream-managed copies, especially in host/global skill directories.
- Remove `.codex/hooks/` entries that point to the old Foundation hook helpers, plus `.codex/quality-gates.json` or the Foundation pre-commit marker only when their contents identify them as Foundation-owned.
- Preserve application `.mjs` scripts/tests, unrelated hook handlers, user-edited helpers and shared configuration. For modified Foundation files, retain user-owned changes while removing separable Foundation checker behavior. If ownership is unclear or a mixed file cannot be separated safely, leave it and report the exact artifact/reference as unresolved; do not claim the upgrade complete.
- Review `docs/agents/workflow.json`, evidence files and manifests before editing. Remove or update only obsolete Foundation checker references; preserve canonical project requirements and historical reports.
- Update the project guide to route checks to Markdown criteria and AI-agent skills. Do not run the old checker to verify its own removal; inspect the targeted paths and configuration directly, confirm Foundation-owned checker artifacts and active references are absent, and record that evidence in the review.

## Review note

```markdown
# AI review: <task>

- Revision / diff:
- Scope:
- Requirements and source documents read:
- AI skill used:

## Findings

- <severity> | <path:line> | <evidence, impact and focused remedy>

## Review coverage

- Reviewed:
- Not reviewed / uncertain:
- Existing project commands run, if required: <command, result, evidence>
```

AI review is advisory: it cannot block a command, commit or deployment. A clean review means no confirmed issue was found in the stated scope; it does not establish that uninspected paths, external services or runtime behavior are correct.

## Routine project use

Route checks from `AGENTS.md` to the relevant project AI skill, such as `security-review` or `test-engineering`. Keep the review criteria in Markdown beside their owning skill or document. Invoke the agent when the task calls for a review; do not turn this workflow into background polling or an automatic commit gate.
