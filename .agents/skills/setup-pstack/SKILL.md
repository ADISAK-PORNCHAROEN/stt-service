---
name: setup-pstack
description: Configure pstack model IDs and reasoning effort per role. Detects available models and writes the settings for the active harness; Codex in this project uses `.agents/pstack-models.md`. Use for /setup-pstack, "configure pstack models", "pstack budget", or changing pstack's model choices.
---

# Setup pstack

Write pstack's model settings, one model per role:

- **Cursor:** `~/.cursor/rules/pstack-models.mdc`, an always-applied rule.
- **Claude Code:** `~/.claude/rules/pstack-models.md`. Claude Code loads every file in `~/.claude/rules/` into each new session.
- **Codex in this project:** the project-root `.agents/pstack-models.md`. Keep settings inside the active project. Other harnesses use `~/.agents/pstack-models.md`; these harnesses don't load it on their own, so pstack skills read it when they pick a model.

"The settings file" below means the file for your harness. In Claude Code, if that file is missing, read `~/.agents/pstack-models.md` instead, where older versions of this skill wrote it.

## Steps

### 1. Detect available models

Enumerate the model slugs you can pass to a subagent in this session (Cursor `Task`, Claude Code `Agent`, OpenCode `task`, Codex `spawn_agent`). That is the dependable source. If your harness also has a command that lists the user's models, prefer it for completeness (for example `opencode models` or `pi --list-models`). If you cannot detect any, ask the user to paste the slugs they have access to. Never write a real slug you have not confirmed is available. The aliases `inherit-parent` and `auto` are always valid even though they are not detected slugs.

### 2. Load current state

For Codex in this project, read only `.agents/pstack-models.md`; do not read or write the user-level settings file. Treat its `# budget`, role values, and `# effort <role label>: <effort>` entries as current choices. Otherwise start from the defaults. A line whose role is not in step 5, such as `how critics`, is from a retired role. Drop it.

### 3. Budget, map, and confirm

**(a) Ask for a budget.** Prefer your structured-question tool (`request_user_input_async` in Codex, `AskQuestion` in Cursor, `AskUserQuestion` in Claude Code, `question` in OpenCode) over free text. Offer these four options with these exact labels, and name the current budget when the settings file records one. With no settings file, say that `large` matches the skill defaults.

- `unlimited — max reasoning`
- `large — xhigh reasoning`
- `medium — high reasoning`
- `small — medium reasoning`

**(b) Apply it.** Build the working table from the skill defaults, and on a re-run keep any role you changed by family, list, or alias (`inherit-parent`, `auto`). `unlimited`, `large`, `medium`, and `small` set the effort token of every real slug, panel entries included, to `max`, `xhigh`, `high`, or `medium`. For Codex, put exact model IDs on role lines and record reasoning effort in `# effort <role label>: <effort>` lines; panel effort lists align by position with their model lists. The effort token is the last token, or the one before a trailing `fast`, on the ladder `max` > `xhigh` > `high` > `medium` > `low`. If the result is not a detected slug, use the same family's detected slug with the highest effort at or below the target, else mark the role as needing a choice. `inherit-parent` and `auto` do not change. So `unlimited` turns `claude-opus-5-5-xhigh` into `claude-opus-5-5-max`. Grok slugs top out at `xhigh`, so under `unlimited` the fallback puts Grok at `xhigh` and keeps `grok-4.7-xhigh-fast` as it is. `large` keeps both defaults. `small` turns them into `claude-opus-5-5-medium` and `grok-4.7-medium-fast`.

**(c) Show the roles and confirm.** Show every role with its model, marking any real slug not in the detected set as needing a choice. Also list each line step 2 dropped. Ask whether to accept as-is or change specific roles, offering the detected models plus `inherit-parent` and `auto` (both mean: this role runs on the parent chat model, which is how Auto users stay on Auto) as the options. Prefer your structured-question tool over free text. For panel roles (arena runners, architect runners, interrogate reviewers) the value is a list, and one subagent runs per entry, alias entries included, so the list length sets the count. `arena cross-judge pool` is also a list, but Arena selects one value from it whose model family differs from the parent's when possible. `swarm workers` is the default model for every worker unless a race or comparison assigns another model per arm.

### 4. Validate

Every real slug written must be in the detected set. `inherit-parent` and `auto` always pass. If a chosen real slug is not available, stop and ask again.

### 5. Write the rule

For Codex in this project, write `.agents/pstack-models.md` with a `# budget` line, one model line per role using the labels poteto-mode uses, and any explicit `# effort <role label>: <effort>` overrides. Keep the file inside this project. In Cursor, include the frontmatter below with `alwaysApply: true`. In other harnesses, write the settings file without the frontmatter (start at the first `#` line). Overwrite the whole file so re-runs stay idempotent. Shape:

```
---
description: pstack per-role model choices (overrides skill defaults)
alwaysApply: true
---
# pstack model configuration. One model line per role. Delete a line to fall back to the skill default.
# `inherit-parent` or `auto` as a value: the role runs on the parent chat model (omit the subagent `model`). Alias entries in a panel list still count toward its fan-out.
# budget: large (xhigh)
feature, refactoring: grok-4.7-xhigh-fast
bug-fix: grok-4.7-xhigh-fast
perf-issue: grok-4.7-xhigh-fast
hillclimb: grok-4.7-xhigh-fast
judgment and prose: claude-opus-5-5-xhigh
hardest tasks: claude-opus-5-5-xhigh
how explorer: grok-4.7-xhigh-fast
how explainer: claude-opus-5-5-xhigh
why investigators: grok-4.7-xhigh-fast
why synthesizer: claude-opus-5-5-xhigh
reflect tooling: grok-4.7-xhigh-fast
reflect judgment, divergent, synthesizer: claude-opus-5-5-xhigh
arena runners: claude-opus-5-5-xhigh, grok-4.7-xhigh-fast
arena cross-judge pool: claude-opus-5-5-xhigh, grok-4.7-xhigh-fast
swarm workers: grok-4.7-xhigh-fast
architect runners: claude-opus-5-5-xhigh, grok-4.7-xhigh-fast
interrogate reviewers: claude-opus-5-5-xhigh, grok-4.7-xhigh-fast
```

### 6. Confirm

Tell the user which file was written. In Codex, pstack skills read the active project's `.agents/pstack-models.md`; re-running this skill updates only that project file.

### 7. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a `verify-*` skill, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with /create-verification-skill." On yes, invoke `/create-verification-skill` (resolves wherever pstack is installed: workspace, user, or plugin). On no, move on without pushing.

### 8. Offer a formal verification skill (optional)

Check whether the project already has a formal verification skill (a project skill that runs a model checker, a proof, or another verifier against the code). If not, offer once: "want a formal verification skill, so agents can prove a key property of your code holds in every case in scope, not only the cases tests reach? I can generate one with /create-formal-verification-skill." On yes, invoke `/create-formal-verification-skill` (resolves wherever pstack is installed: workspace, user, or plugin). On no, move on without pushing.
