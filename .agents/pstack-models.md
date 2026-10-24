# pstack model configuration for this project. Codex model IDs use the `model` argument; reasoning effort is separate.
# Model selection: easy work uses gpt-6-luna at xhigh; harder work uses gpt-6-luna at max when sufficient.
# Use gpt-6.1-sol at medium for work that needs deeper reasoning or analysis.
# budget: small (medium)
# Role-specific effort lines override the budget and are passed as `reasoning_effort`.
# Panel effort entries align by position with the models on the matching role line.
# effort feature, refactoring: xhigh
feature, refactoring: gpt-6-luna
# effort bug-fix: max
bug-fix: gpt-6-luna
# effort perf-issue: medium
perf-issue: gpt-6.1-sol
# effort hillclimb: max
hillclimb: gpt-6-luna
# effort judgment and prose: xhigh
judgment and prose: gpt-6-luna
# effort hardest tasks: max
hardest tasks: gpt-6-luna
# effort how explorer: medium
how explorer: gpt-6.1-sol
# effort how explainer: xhigh
how explainer: gpt-6-luna
# effort why investigators: medium
why investigators: gpt-6.1-sol
# effort why synthesizer: medium
why synthesizer: gpt-6.1-sol
# effort reflect tooling: medium
reflect tooling: gpt-6.1-sol
# effort reflect judgment, divergent, synthesizer: medium
reflect judgment, divergent, synthesizer: gpt-6.1-sol
# effort arena runners: xhigh, max
arena runners: gpt-6-luna, gpt-6-luna
# effort arena cross-judge pool: max, medium
arena cross-judge pool: gpt-6-luna, gpt-6.1-sol
# effort swarm workers: medium
swarm workers: gpt-6.1-sol
# effort architect runners: xhigh, medium
architect runners: gpt-6-luna, gpt-6.1-sol
# effort interrogate reviewers: medium, medium
interrogate reviewers: gpt-6.1-sol, gpt-6.1-sol
