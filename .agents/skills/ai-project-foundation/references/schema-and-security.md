# Schema and security foundations

Read for persisted data, public input, identities/tenants, external services or AI/tool execution. Select sections relevant to the actual product.

## Domain and schema design

Start with entities, ownership, lifecycle and business invariants; confirm current schema/migrations/queries. Separate existing behavior from proposed changes. New systems need explicit assumptions and acceptance before implementation.

| Concern | Required context |
| --- | --- |
| Identity | Stable identifiers, uniqueness scope and external IDs |
| Ownership | Row/document owner, tenant boundary and allowed actors |
| Relationships | Cardinality, references, optionality and deletion |
| Values | Types/units, money precision, timezones, null/default constraints |
| State | Legal transitions, actors and concurrent actions |
| Integrity | Constraints, transactions, idempotency and races |
| Access | Authorization predicates, query patterns and indexes |
| Lifecycle | Retention, deletion/anonymization, audit and sensitive fields |
| Evolution | Migration order, compatibility, backfill and recovery |

Enforce integrity in the appropriate persistence layer and authorization at each server resource boundary. DTOs expose only client-appropriate fields.

An invariant such as users editing only their own records must connect ownership, queries/authorization, contracts and negative integration tests. UI visibility is not permission enforcement.

## SCHEMA.md blueprint

```markdown
# Data model

## Source of truth

<Schema definitions, migration directory and persistence entry points>

## Entities and ownership

| Entity | Owner / tenant | Identity | Lifecycle | Sensitive data |
| --- | --- | --- | --- | --- |
| <entity> | <owner> | <key> | <states/retention> | <classification> |

## Relationships

<Useful Mermaid ERD with source-confirmed cardinality>

## Invariants and access

| Rule | Enforcement source | Verification |
| --- | --- | --- |
| <constraint/permission> | <schema/query/server path> | <scenario> |

## Migration lifecycle

<Order, prerequisites, compatibility, recovery, isolated checks and deploy coordination>

## Open questions

<Unresolved assumptions/limitations>
```

Keep dumps/credentials out of documentation. ERDs describe the system; migrations retain implementation ownership. For the requested source-derived diagram and `mermaid.html`, follow the [database Mermaid prompt](setup-prompts.md#database-mermaid-and-mermaidhtml): implemented schema, agreed proposal or pending scaffold are distinct branches. Consult [Mermaid ER syntax](https://mermaid.js.org/syntax/entityRelationshipDiagram.html) and the installed renderer's [integration API](https://mermaid.js.org/config/usage.html).

## Migration verification

- Run migrations on isolated clean and supported previous-version databases.
- Check constraints, representative queries, upgrade compatibility and critical invariants; include concurrency for multiple writers.
- Verify repeatable/resumable backfills where required. Test the chosen recovery, which may be a forward fix rather than rollback.
- Document app/schema deployment order and destructive-change risks. Prepare reviewable validation/plans before authorized production operations.

## Security model before tools

Trace actual entry points, flows and trust boundaries. Identify assets, identities, privileges, attacker-controlled input and required protections. Connect the model to enforcement/tests rather than a generic vulnerability list.

| Boundary | Relevant review topics |
| --- | --- |
| Identity/session | Login/logout, expiry, revocation, cookies/tokens |
| User/tenant/resource | Object authorization, role changes, bulk/read/write |
| Input/database/output | Validation, parameterized queries, rendering, error leaks |
| Browser/server | Auth-appropriate CSRF/CORS, headers, uploads/downloads |
| Server/external service | Destinations, SSRF, webhook signatures/replay |
| Files/processes | Traversal, extraction, shell/argument injection |
| Resources | Payload/file limits, pagination, timeouts, retries, abuse |
| Secrets/dependencies/CI | Secret scope, artifacts/logs, provenance, permissions |
| AI/tools/RAG | Untrusted content, tool permissions, data access, approval boundaries |

Treat retrieved documents, webpages and user inputs as untrusted data, separate from system policy. Scope tools/data by identity, validate outputs used for execution and test that prompt injection cannot bypass permissions.

Use the current [OWASP Top 10](https://owasp.org/www-project-top-ten/) for risk categories and [OWASP ASVS](https://owasp.org/projects/asvs) to select testable application requirements. Record edition/version for IDs; a checklist does not establish compliance. For each code diff, invoke the applicable diff-review workflow even when the changed feature has no obvious security label; keep scope proportional to the changed paths and affected boundaries.

## SECURITY.md and SECURITY-MODEL.md

SECURITY.md owns agreed reporting channels/policy, supported versions and the model pointer. Use accepted real contacts; explicitly mark undefined channels rather than inventing an email or SLA.

```markdown
# Security model

## Scope and evidence

<Environment, revision, source paths and review date>

## Assets, identities and boundaries

<Data classification, identities/roles and flow diagram>

## Required invariants

| Invariant | Enforcement | Abuse-case verification |
| --- | --- | --- |
| <rule> | <current code/config> | <negative test> |

## Threat scenarios and assumptions

<Attacker entry → reachable path → asset/impact → controls>
<Deployment assumptions and unverified areas>

## Review workflow

<Available skill/tool, scope selection and local report location>
```

## Select the review workflow

1. **Diff/PR:** use the host's security diff-review skill for every code change; inspect an immutable base/head or working-tree patch snapshot, changed files, affected callers and necessary surrounding enforcement.
2. **Repository scan:** use the whole-repository scan skill only for a requested system review with directories, exclusions and explicit unreviewed coverage. Do not substitute a baseline scan for a diff review.
3. **Finding triage:** existing finding applicability, preconditions and source-to-sink evidence.
4. **Fix/verification:** requested scoped remediation plus abuse/regression verification. Review-only requests produce findings without expanding into implementation.

Read the matching installed Codex Security/tool entry skill and follow its version's lifecycle. If unavailable, perform evidenced source review and report limits. Policy/tool setup and scan execution are separate deliverables.

## Findings and evidence

For each candidate, record controlled input, entry point, reachable path, controls, preconditions, impact and source locations. Confirm conditions before marking confirmed. Base severity on exploitability/impact in the actual environment; separate weaknesses from deployment assumptions.

```markdown
Scope: <revision/patch/environment and exclusions>
Finding: <title; candidate / confirmed / fixed / verified>
Path: <entry → checks → sink/asset with locations>
Conditions: <attacker requirements and existing controls>
Impact: <reachable effect and severity rationale>
Evidence: <source review / isolated reproduction / test>
Remediation: <invariant-preserving change and verification>
Coverage gaps: <unverified areas>
```

Use nondestructive reproduction and authorized targets; keep local reports free of secrets/raw credentials. Distinguish proposals, implemented fixes and actually verified fixes.

Account for changed files/critical paths in scope and settle reportable candidates. A conclusion of no confirmed findings states reviewed scope and limits; it is not a vulnerability-free guarantee. Issues/advisories, messages and publication require action-specific authorization.
