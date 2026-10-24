---
name: security-review
description: Review every application-code, executable-configuration, dependency or CI diff for security regressions before a change is handed off. Use for code changes; use a full repository audit only when explicitly requested.
---

# Security review

## Method and project context

Before selecting risks, verification requirements or abuse cases, read
[security standards and project mapping](references/review-contract.md) and apply
its relevant source guidance. It owns the detailed method and versioned
source-to-project mapping. The project security model supplies actual assets,
trust boundaries, controls and invariants; `SECURITY.md` owns reporting policy.
During setup, reconcile outdated procedures while preserving verified facts and policy.

## Workflow

1. Read the root agent guide, `SECURITY.md`, the current security model and the
   accepted change. Inspect the actual working-tree diff, including untracked
   executable files, then follow changed data through nearby callers and trust
   boundaries.
2. Use the installed host security-review capability for the diff. In Codex,
   invoke `$codex-security:security-diff-scan`. Read that skill before use and
   follow its scope, validation and reporting rules. Use
   `$codex-security:security-scan` only for an explicitly requested whole-repo
   or scoped baseline audit without a patch; use its deep-scan skill only when
   the user requests multi-pass scanning.
3. Check the affected OWASP Top 10:2025 risks and read selected ASVS 5.0.0
   requirements or WSTG v4.2 scenarios that match the real application. The Top 10
   is a risk index, not proof of complete security. Trace sources, checks,
   transformations and sinks; consider authorization, hostile input, output,
   secrets, dependencies, exceptional paths and logging as relevant.
4. Validate candidate findings against reachability, preconditions, existing
   controls and impact. Keep confirmed issues, unvalidated candidates,
   suppressed results and unreviewed scope distinct. Do not modify code or
   publish/track a finding unless the task authorizes that action.
5. If the host diff scanner is unavailable, perform a bounded manual review
   using the same data-flow and threat-boundary method. State that automated
   scanning was unavailable; never imply the fallback was an automated scan.

## Completion

Report the base/head or dirty scope, changed paths, actual tool and mode,
validated findings, evidence, exclusions and coverage gaps. Link source locations
and explain attacker preconditions and reachable impact. A clean result describes
only the reviewed scope and does not certify the project against OWASP.
Include applied contract sections, OWASP categories, versioned requirement/scenario IDs, justified
exclusions and unavailable source reads.

## References

Source roles, version selection and local adaptations are in the linked review contract.

- [OWASP Top 10:2025](https://top10.owasp.org/2025/0x00_2025-Introduction/)
- [OWASP ASVS 5.0.0](https://github.com/OWASP/ASVS/tree/v5.0.0/5.0)
- [OWASP WSTG v4.2](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/)
- [OWASP Secure Code Review Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Code_Review_Cheat_Sheet.html)
- [OWASP Secure Coding with AI Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Coding_with_AI_Cheat_Sheet.html)
- [OpenAI Codex Security](https://help.openai.com/en/articles/20001107-codex-security)
