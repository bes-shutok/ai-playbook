# Backlog: docs-branch loud-skip remediation enumeration omits extra_shadow_dirs and .git/info/exclude

- Priority: low
- Status: closed
- Workflow: backlog
- Scope: `agents/skills/docs-branch/SKILL.md` (Step 1 snapshot block, loud-skip warning remediation text)
- Owner: playbook maintenance
- Source: code review r1 F5 for plan 2026-09-24-p55-audit-deployment-gaps-gate-blind-spots (Low, non-blocking)
- Driving force: code-quality + simplicity

Disposition: 2026-09-25 (routed via docs/plans/2026-09-25-docs-branch-shadow-candidate-inclusion-and-completed-corpus-deletion.md, Task 7): closed by that plan's Task 5 — the Step 1 loud-skip warning's remediation enumeration now names all four sanctioned recoveries on one physical line (the .gitignore rule, .git/info/exclude as the local-only fallback when .gitignore cannot be committed, the extra_shadow_dirs facts key for an extra shadow root whose ignore coverage drifted, and the facts reviews_dir/tmp_dir key correction); live needle re-verified on the execution base: the warning line greps for both info/exclude and extra_shadow_dirs and remains a single physical line.

Origin: docs/reviews/2026-09-24-2026-09-24-p55-audit-deployment-gaps-gate-blind-spots-code-review-r1.md, finding F5. The loud-skip warning's remediation enumerates two recoveries only ("Add the ignore rule to .gitignore or correct the facts reviews_dir/tmp_dir key"). It omits the two other sanctioned recoveries the same skill documents: `.git/info/exclude` (the Rules section's local-only fallback for repos that cannot commit `.gitignore`) and the `extra_shadow_dirs` facts key (an extra shadow root whose ignore coverage drifted needs its ignore rule, not a reviews_dir/tmp_dir key correction).

Suggested fix: widen the remediation enumeration in the Step 1 warning text to name `.git/info/exclude` as the local-only fallback and the `extra_shadow_dirs` facts key for extra shadow roots, keeping the message a single line.
