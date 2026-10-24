# Project skills checklist

This checklist covers only the selected project-local skills recorded in
`docs/agents/foundation.json`. Existing unrelated project skills are preserved
and are not counted as Foundation deliverables.

- Selected project skills: 3
- Complete project-local installations: 3/3
- Incomplete or missing installations: 0/3
- Runtime discovery verified: 3/3

Mark an installation complete when its project folder contains `SKILL.md` and
all linked resources, its name/path are recorded in the manifest, and the
project guide routes to the correct path. Keep fresh-session discovery separate
from file presence and the active session's discovery snapshot.

| Complete | Skill | Project path | Required files/resources | Manifest and route | Runtime discovery | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| [x] | `ai-project-foundation` | `.agents/skills/ai-project-foundation` | Complete 27-file package: `SKILL.md`, `agents/openai.yaml`, linked references, static templates, and bundled project-skill templates | Registered in `requiredSkills`/`skillPaths`; routed by `AGENTS.md` and `docs/agents/tools.md` | Verified in fresh agent catalog | Catalog lists this project-local skill; host invocation was not exercised. |
| [x] | `test-engineering` | `.agents/skills/test-engineering` | `SKILL.md`; `references/testing-contract.md` | Registered and routed by `AGENTS.md` and `docs/agents/tools.md` | Verified in active session catalog | Existing project-local installation reviewed and reused. |
| [x] | `security-review` | `.agents/skills/security-review` | `SKILL.md`; `references/review-contract.md` | Registered and routed by `AGENTS.md` and `docs/agents/tools.md` | Verified in active session catalog | Existing project-local installation reviewed and reused. |

## Review evidence

- Project revision / dirty scope: base commit `4193036`; pre-existing modified
  application, test, and documentation files were preserved. This setup added
  only the Foundation skill folder and changed its listed workflow documents.
- Discovery method/session: a fresh agent session catalog lists all three
  selected skills from the project `.agents/skills` root. Host invocation was
  not exercised.
- Preservation baseline: the target Foundation folder was absent. The project
  skills root had 58 sibling skill folders and 139 files before the copy; their
  tree digest is recorded in `docs/AI-FOUNDATION-REPORT.md`.
- Last checked: 2026-10-23.
