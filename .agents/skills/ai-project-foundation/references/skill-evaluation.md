# Skill evaluation

Read when changing skill instructions/routing, adopting the skill on a new host, or investigating repeated AI failures. Select affected cases from [the case suite](../assets/evals/cases.json). Evaluation is an AI-agent review of real outputs; it is never an application script, commit hook or background task.

## Prepare and run

1. Save the exact candidate skill revision and fixture revision. For comparison, preserve the baseline and use the same prompt, fixture, host/model and criteria.
2. Materialize the case in a disposable repository. Give a fresh AI session only the realistic prompt, normal skill discovery and repository context.
3. For implicit routing cases, do not name or preload the target skill. For explicit cases, invoke it as the user would.
4. Have an independent AI reviewer inspect the actual files, diffs and outputs against every criterion. Do not grade from a success claim or wording alone.
5. Record the skill and fixture revisions, host/model when known, prompt, outcome, per-criterion evidence, corrections and limitations in Markdown. Unknown usage/time values stay unknown.
6. Keep secrets and private reasoning out of reports. Preserve only task outputs, review evidence and concise decision summaries.
7. After capturing required outputs, remove evaluation-owned executable fixture files and their package manifests. Keep concise Markdown findings and durable run evidence; verify the report contains no generated `.mjs` or `.js` fixture files. Preserve application files that belong to the evaluated project.

## Markdown run record

Use [the run-record template](../assets/evals/run-record.template.md) in the report directory. Link evidence files relative to that directory. Record `not-run`, `blocked`, `failed` or `passed` accurately; a case passes only when the reviewer can point to evidence for every criterion.

## Compare outcomes

The suite covers onboarding, instruction migration, document completeness, glossary/design accuracy, AI-skill routing, source/security review, cleanup, negative triggers, stale review evidence and resume. Add cases only for demonstrated failures or new supported workflows.

Compare matched baseline and candidate sessions before claiming an improvement. Record elapsed time, corrections and token/tool usage only when observed; unknown stays unknown. Repeat cases when output varies or differences are too small to conclude. One run does not establish reliability.

## Adopt results

Fix demonstrated instruction/routing problems and repeat affected cases in a fresh session. Keep failures and unrun cases visible. File/link inspection and AI behavior review are separate evidence: review every required file directly, then use a fresh session for implicit routing. Do not use a JavaScript helper to grade skill records or semantic behavior.

References: [OpenAI skill triggers](https://learn.chatgpt.com/docs/build-skills) and [Anthropic agent evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents). Actual installed behavior and current evidence remain authoritative.
