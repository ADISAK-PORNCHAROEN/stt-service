# Security standards and project mapping

Read before selecting risks, verification requirements or abuse cases for a diff.
During foundation setup/repair, adapt this contract to actual source, assets,
trust boundaries and policy. Retain every source below with its role, version
and local application. Link the project security model and SECURITY.md as the
owners of observed boundaries/invariants and reporting policy.

## Sources and application

| Source / edition | Principle to apply | Project mapping and evidence to establish |
| --- | --- | --- |
| [OWASP Top 10:2025](https://top10.owasp.org/2025/0x00_2025-Introduction/) | Identify applicable risk categories from changed boundaries | Map actual inputs, controls and sinks to relevant categories with justified exclusions |
| [OWASP ASVS 5.0.0](https://github.com/OWASP/ASVS/tree/v5.0.0/5.0) | Select concrete, testable security requirements | Read selected requirement text and record version-prefixed IDs, applicability, source control and actual verification outcome |
| [OWASP WSTG v4.2](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/) | Select applicable verification scenarios | Record versioned scenario, authorized local target, prerequisites, procedure and outcome |
| [OWASP Secure Code Review Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Code_Review_Cheat_Sheet.html) | Incremental diff review, data flow and validation of candidate issues | Trace attacker-controlled input through checks/transformations to reachable sinks in the reviewed patch |
| [OWASP Secure Coding with AI Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Coding_with_AI_Cheat_Sheet.html) | Review AI-generated code, test changes and tooling provenance | Inspect dependency/tool changes, altered assertions, negative/recovery cases and preserved native gates |
| [OpenAI Codex Security](https://help.openai.com/en/articles/20001107-codex-security) | Contextual investigation and isolated validation | Use the installed host diff workflow's actual preflight, artifact and recovery rules and record capability gaps |

Keep versioned editions stable until an authorized workflow update reviews the
new edition and mappings. Read exact selected requirement/scenario text before
recording IDs. Recheck evolving cheat sheets or host documentation when a decision
depends on them; preserve unavailable links and report failed reads honestly.
Top 10 categories alone do not prove complete coverage or OWASP compliance.

## Map and review actual boundaries

For each affected asset/boundary, identify the source/caller, attacker control,
validation, transformation, sink, accepted invariant and relevant tests. Follow
the real diff, including new executable files, into supporting callers. Examine
authorization, hostile input, output, secrets, dependencies, exceptional paths
and logging where reachable. Explain excluded web/session scenarios from the
actual application; revisit them when a change introduces those boundaries.

Use the installed diff-review capability for patches. Repository/scoped baseline
audits and multi-pass scans require their explicit task scope. Preserve the same
durable scan identity and its recovery rules. If the capability is unavailable,
record the blocker and identify the bounded manual review actually performed.

Before confirming a candidate, establish reachability, prerequisites, protections
and concrete impact. Keep confirmed issues, candidates and unreviewed scope
distinct. A correctness defect alone does not establish exploitable impact.

## Connect the workflow and evidence

The generated SKILL.md routes here directly and connects to the installed
test-engineering skill for relevant negative/regression checks. Inherit the
native quality profile, reporting policy, evidence owner and isolated fixture
rules. Keep custom hooks, disabled controls and action authorization consistent
with the existing harness. Report patch identity, paths, actual tool/mode,
selected requirements/cases, findings/candidates, exclusions and coverage gaps.
A clean result applies only to the reviewed snapshot.
