# Backlog: Resolve review strictness from authoritative workspace facts

- **Filed:** 2026-10-07, operator-directed after strictness-classification review
- **Status:** rejected (2026-10-08; the resolver and project-class design was rejected under the corrected requirements; no resolver script is needed.)
- **Workflow:** backlog
- **Priority:** high
- **Class:** fence-class
- **Skill/step:** `agents/skills/review-plan/SKILL.md`, Project strictness classes and Iteration Discipline; `agents/skills/receiving-review/SKILL.md`, Triage class
- **Severity:** medium; a wrong project class can apply the wrong review cap and consultation policy, causing excess review work or bypassing company-specific handling.
- **Source reference:** operator correction in the `plan-detail-boundary` authoring session, 2026-10-07; current review-plan class check considered only `personal_projects_root` in project-local facts and treated an absent key as standard, while the authoritative user facts hold both personal and company workspace roots. This led to an incorrect standard-class conclusion for the ai-playbook repository. Capture hygiene: `scan-public-hygiene.sh --files` pass.
- **Driving force:** reliability
- **Origin class:** self-serving
- **Consumer urgency:** high. Company projects that consume the shared review skills need correct company classification and policy selection; the skills-repo personal priority profile must not park this consumer-impacting fix as formal-hardening.
- **Environment:** Codex desktop, linked worktree for a personal skills repository; user facts and project facts inspected.
- **Dedup probe:** Searched open backlog filenames and Problem bodies for strictness, project class, round cap, company project, `company_projects_root`, and `personal_projects_root`. Nearest: `2026-10-06-review-round-cap-operator-gate.md`, which addresses operator reflection and decisions at the cap, not how a repository is classified; `2026-10-05-execute-plan-risk-floor-panel-cap-conflict.md`, which addresses conflicting panel and cap rules, not workspace-root resolution.

## Problem

`review-plan` resolves its strictness class by looking for `personal_projects_root` in the current project's facts and otherwise choosing `standard`. The authoritative workspace roots are supplied through `user_facts_path`, and include both `personal_projects_root` and `company_projects_root`. Project-local facts need not duplicate those keys. A linked worktree can also live outside either workspace root even though its shared Git directory identifies the owning checkout. As a result, personal projects can be treated as standard, and company projects have no explicit class for applying company-specific review and triage policy. In this session, the resolver was incorrectly treated as standard because the project-local key was absent, despite the owning checkout being under the personal workspace root; that conclusion affected whether the personal round limit applied.

## Expected

Resolve strictness from the authoritative workspace facts and the owning repository identity. Distinguish personal, company, and standard projects using component-wise root containment. When operating in a linked worktree, resolve the owning checkout before classifying it so the temporary worktree location cannot change the policy. Apply the appropriate round limit and cross-profile triage or consultation rules for each class. If facts or repository identity cannot be resolved, report that condition rather than silently treating it as standard.

Add regression coverage for main checkouts and linked worktrees under personal and company roots, plus a repository outside both roots and unresolved or malformed facts. Pin that project-local facts do not need to duplicate user workspace roots and that the resolved class selects the intended review and triage policy.

At promotion, settle whether company projects use the existing standard round limit with company-specific consultation policy, or need a distinct company review limit sourced from company policy. Keep this decision in the canonical review policy rather than duplicating it in user facts or individual plans.

## Why not fixed now

The operator asked to record the strictness resolver correction as a separate ai-playbook backlog item. The active plan changes plan-detail ownership and execution scope discovery; changing review-policy classification is separate workflow machinery. For the current plan, classify the owning checkout using the authoritative workspace roots and honor its personal strictness class.

## Source

- `agents/skills/review-plan/SKILL.md`, Project strictness classes and Iteration Discipline
- `~/.ai-playbook/facts.md`, Workspace roots and `user_facts_path`
- `docs/AGENTS.md`, Context loading policy and facts hierarchy
- `plan-detail-boundary` review records r6 and r7, which exposed the bootstrap and test-witness recurrence
