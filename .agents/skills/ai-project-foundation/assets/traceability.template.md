# <Feature>: Requirement and review map

Canonical spec: <URL/path and relevant section>
Owner: <responsible person/team>
Reviewed revision: <HEAD plus relevant working-tree changes; not HEAD alone when dirty>
Scope: <source/tests/contracts/configs covered; exclusions with reason>
Updated: <timestamp with timezone>

## Requirement coverage

| ID | Accepted behavior / example | Implementation source | AI review question or existing project scenario | Status | Current evidence |
| --- | --- | --- | --- | --- | --- |
| <FEATURE-01 or tracker ID> | <observable outcome> | <current file/symbol> | <AI review question or scenario> | <planned/implemented/reviewed/blocked> | <Markdown review note or existing project evidence> |

IDs remain stable when paths move. Mark implemented from current source; mark reviewed only when the AI agent compares it with accepted behavior and cites evidence for the current scope. Keep missing requirements and negative cases visible. Existing project test results remain separate evidence.

## Check evidence

| Review / existing check | AI skill or existing project command | Revision and dirty scope | Outcome | Time | Evidence artifact |
| --- | --- | --- | --- | --- | --- |
| <review/check ID> | <AI skill or existing project command> | <current revision/scope> | <passed/failed/skipped/not-run> | <actual review/run time> | <Markdown note or existing report> |

Separate AI source review from existing project command results and remote CI evidence. Link Markdown reports produced by the review. Record unavailable checks and reasons instead of marking them passed.

## Security and remaining gaps

<Map applicable security invariants to AI review criteria and relevant existing tests, referencing the security model. Record unresolved decisions, exclusions, and the next review needed.>

## Freshness

<When relevant source/spec/contract/test guidance changes after review, mark the review note stale. Have the AI agent reopen the affected source and criteria, then record the new revision and evidence.>
