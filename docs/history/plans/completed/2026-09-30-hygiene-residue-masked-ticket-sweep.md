# Masked-ticket residue sweep over tracked plan artifacts and the named pre-publish hygiene step

[github: https://github.com/admitriev/ai-playbook] Backlog origin: `docs/history/backlog/2026-09-29-hygiene-residue-landed-completed-plans-scan-scope.md`
Driving force: reliability (privacy integrity); secondary simplicity

Plan review: docs/reviews/2026-09-30-plan-review-hygiene-residue-masked-ticket-sweep-r2.md (the highest round of the r1-r2 staging series; r2 verdict ready=yes, zero blocking)

## Gist TLDR

TLDR: mask the employer ticket prefix in the four tracked plan artifacts that still carry it (nine completed-plan occurrences plus the four in the open backlog item), using the operator-approved generic form under the 2026-09-27 masking precedent, and add the named pre-publish step to the done skill so a run verifies tracked files with the full pattern file before publishing; the default scan scope stays result-only by standing operator decision.

## Outcome

The employer ticket identifier no longer occurs in any tracked file, in any letter case, except the two crm-reconcile backlog items' FILENAMES and the `Cluster:` pointer lines that cite them (an operator-directed residual: a rename breaks their identity and every reference to them), and this plan's own instruction literals (the exact forms the mask replaces must be named once to stay executable). The three completed plans, the open backlog item, the runtime test module, the two crm-reconcile items' bodies, and this plan's own census prose carry the generic form (`CRM-<ID>`/`crm-<id>` shape-preserving placeholders), matching the sanitized files from the 2026-09-29 remediation (commit 4a60a5c4). The done skill's hygiene guidance names the verification step a run performs before publishing: the explicit changed-files or full pattern-file sweep over tracked docs, not the default strict-tree scan, whose scope the operator fixed as result-only on 2026-09-27 and which this plan does not re-widen.

Corrected facts this plan records against the origin item (whose authoring-time facts drifted):

- The origin's "landed plan" arm is moot: `2026-09-29-execute-plan-task-local-verifier-declarations.md` has since executed and archived; all residue-holding plan artifacts now sit under `docs/history/plans/completed/`.
- The residue grew with later landings: three completed plans now carry nine occurrences (the origin knew of two files, six occurrences).
- `docs/reviews/` and `docs/tmp/` copies are gitignored (not tracked) and out of the public-leak surface; the sweep covers tracked files only.
- The open backlog item holding residue (`2026-09-29-execute-plan-post-squash-artifact-cleanup.md`) also carries peer working-tree modifications in the primary checkout; this plan's mask edits the committed bytes through the executing worktree and never touches the primary's working tree.

## Assumptions

- The masking disposition follows the standing operator decision recorded by commit 4a60a5c4 (2026-09-29, the generic-form masking of the employer ticket prefix across tracked docs): completed-history artifacts, the test module, and the two crm-reconcile bodies take the same substitution, replacing each real ticket id and its lowercase forms with shape-preserving placeholders (`CRM-<ID>`, `crm-<id>`). The artifacts' narrative value is unaffected - the ids are witness labels, not content.
- No digest re-certification is owed: every masked plan artifact is already archived under `completed/`, so no execution lane reads a certified digest for them (the origin's digest-re-cert arm applied only to the then-unexecuted landed plan, which has since archived).
- The scope arm is the fix-shaped one the origin names: the done runbook gains the named pre-publish verification step; the default scan scope stays as the operator's result-only adjudication (2026-09-27 lineage, applied by commit 4a60a5c4) fixed it. Re-widening the default scope is explicitly operator direction and is not taken here.
- The open backlog item's residue is masked in the same pass (its four occurrences are witness prose; the generic form preserves the narrative), and the item itself stays open for its own subject matter.

Decision points requiring a grill: none - both dispositions follow standing operator precedents the origin itself cites; the scope arm takes the fix-shaped default the origin marks as operator-accepted.

### Task 1 - Mask the four tracked artifacts

- [ ] In the executing worktree, replace every ticket-id occurrence with the generic `CRM-<ID>` form and every lowercase `crm607` variant with `crm-<id>` in exactly these tracked files: `docs/history/plans/completed/2026-09-28-execute-plan-codex-worker-terminal-recovery.md`, `docs/history/plans/completed/2026-09-29-execute-plan-continuation-admission-and-capacity.md`, `docs/history/plans/completed/2026-09-29-execute-plan-task-local-verifier-declarations.md`, `docs/history/backlog/2026-09-29-execute-plan-post-squash-artifact-cleanup.md`, `scripts/test_execute_plan_runtime.py`, and the bodies of the two `2026-09-30-crm-607-reconcile-*` backlog items. This plan file's own census prose self-applies the same mask. No other byte changes; the generic form is the operator-approved shape per commit 4a60a5c4. The two crm-reconcile items' FILENAMES carry the id too; a rename breaks their identity and is recorded as an operator-directed residual, not taken here. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the case-insensitive pattern sweep over tracked files (`git grep -icE "crm[-_]?607"` content matches) and verify zero remain (gitignored `docs/reviews/` and `docs/tmp/` copies are out of scope: untracked; the two crm-reconcile FILENAMES are outside a content sweep by construction). [class: REPOSITORY_TEST]

### Task 2 - Done skill: the named pre-publish verification step

- [ ] In `agents/skills/done/SKILL.md`, the sensitive-data-scan remediation guidance bullet: append one sentence - before publishing or landing changes that touch tracked prose under `docs/`, run the hygiene scan in explicit changed-files mode (the scan script's `--files` form) or the full pattern-file sweep over the touched tracked files, because the default scan scope covers only the strict source trees per the standing result-only adjudication (2026-09-27); a residue hit is sanitized to the operator-approved generic form in the same run. [class: IMPLEMENTATION_REQUIRED]

### Task 3 - Validation

- [ ] All checks in Validation Commands pass from the worktree root. [class: REPOSITORY_TEST]

## Evaluation Criteria

- Zero `CRM-<ID>` occurrences remain in tracked files (the full pattern sweep over `git ls-files` output exits clean); the four artifacts carry `CRM-<ID>`.
- The done skill's remediation bullet names the explicit changed-files verification step with the result-only adjudication citation; the default scope is not re-widened anywhere.
- No other file changes; the masking is the only byte delta in the three completed plans and the backlog item.

## Review Scope

Files: the seven body-masked tracked artifacts named in Task 1 (masking only; the two crm-reconcile FILENAMES untouched), `agents/skills/done/SKILL.md` (the sensitive-data-scan remediation bullet only). Contract files referenced read-only: the origin backlog item, the result-only adjudication record (2026-09-27 lineage, applied 2026-09-29 by commit 4a60a5c4), the machine-local scan script's modes (via the facts key), the gitignored `docs/reviews/` copies (out-of-surface evidence).

## Validation Commands

Run from the worktree root; every check fails closed:

1. `git grep -inE "crm[-_]?607" -- . ':(exclude)*hygiene-residue-masked-ticket-sweep.md' | grep -viE 'cluster:' | wc -l | xargs test 0 -eq` the gitignored copies never appear; run standalone, its exit status is not consumed).
2. `grep -qF 'explicit changed-files mode' agents/skills/done/SKILL.md || { echo FAIL: pre-publish step missing; exit 1; }` - the runbook step exists.
3. `grep -qF 'result-only' agents/skills/done/SKILL.md || { echo FAIL: adjudication citation missing; exit 1; }` - the standing-decision citation is pinned.
4. `test "$(git diff --name-only main -- | wc -l | tr -d ' ')" -eq 6 || { echo FAIL: scope drift; exit 1; }` - exactly the six in-scope files changed (the five masked artifacts plus done SKILL.md; run before staging this plan file, or expect 7 with it).
5. `bash scripts/check-no-em-dash.sh added-lines --base main || { echo FAIL: em dash; exit 1; }` and `bash scripts/scan-public-hygiene.sh || { echo FAIL: hygiene; exit 1; }` - both exit 0.
