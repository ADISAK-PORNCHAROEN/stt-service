# <Feature>: Technical design addendum

Canonical spec: <configured tracker URL or repository artifact>
Owner: <responsible person/team>
Status: <proposed / agreed / superseded>
Decision evidence: <conversation/issue/review reference and date>

Fill only gaps in the canonical spec; link existing context and remove irrelevant sections. Use its existing Further Notes/technical-decisions section where supported instead of creating a second spec.

## Context and constraints

Current behavior: <observed behavior and evidence>
Target behavior: <accepted outcome; link user stories/requirement IDs>
Constraints and out of scope: <compatibility, deployment, product and operational constraints>

## Alternatives and decision

| Option | Benefits | Costs / risks | Decision and reason |
| --- | --- | --- | --- |
| <actual alternative> | <benefit> | <trade-off> | <chosen/rejected/proposed with evidence> |

## Interfaces and data flow

<Actors, entry points, stable module/interface names, caller responsibilities, inputs, outputs and errors. Link canonical contract/schema/architecture. Use a diagram when it explains relationships.>

## States and invariants

| From | Trigger / actor | Preconditions / ownership | To / observable outcome | Failure or concurrent behavior |
| --- | --- | --- | --- | --- |
| <state> | <action> | <invariant> | <state/result> | <error/idempotency/race behavior> |

## Risks and lifecycle

<Relevant security/privacy, sensitive data, storage, migration/backfill, compatibility, recovery, i18n/accessibility and operational implications. Record assumptions and unresolved decisions explicitly.>

## Acceptance and verification

<Reference accepted positive/negative examples, approved testing seams and the checks that establish the intended behavior. Source/test paths, revision and run results belong in the linked traceability record.>

Traceability: <artifact pointer>
Related decisions: <ADR pointers only when warranted>
Open questions: <decision, owner, and the work it blocks; or none>
