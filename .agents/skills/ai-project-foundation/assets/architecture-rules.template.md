# <Project>: AI-reviewed architecture boundaries

Architecture authority: <existing guide/ADR and actual module boundaries>
Owner / last reviewed: <person/team and date>

| ID / invariant | Scope and allowed exceptions | AI review criteria | Evidence / unresolved questions |
| --- | --- | --- | --- |
| <stable rule ID and observable constraint> | <paths/interfaces; exception owner/reason> | <what the agent traces and compares> | <source paths/lines or open question> |

## Review method

Read the current architecture guidance and changed source. Trace imports, calls,
data ownership and side effects across the affected boundary. Compare the code
with each invariant, cite file/line evidence, and separate confirmed violations
from uncertainty or uninspected scope.

## Existing project checks

<Link checks already owned by the project, if relevant. Do not add a checker,
hook or CI gate for this document.>

## Known limits and exceptions

- <baseline issue, accepted exception and reason>
- <scope not reviewed or behavior that source inspection cannot establish>
