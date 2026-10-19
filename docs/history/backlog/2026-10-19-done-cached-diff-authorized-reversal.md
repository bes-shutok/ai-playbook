# Backlog: done cached-diff guard blocks an explicitly authorized ancestor restoration

- **Filed:** 2026-10-19, witnessed during an explicitly requested closeout
- **Status:** covered (docs/history/plans/2026-10-19-done-cached-diff-authorized-reversal.md)
- **Workflow:** backlog
- **Priority:** normal
- **Origin class:** witnessed closeout blocker
- **Class:** fix-class
- **Driving force:** reliability + simplicity
- **Skill/step:** `agents/skills/done/SKILL.md` Step 3; `scripts/done_run.sh` cached-diff guard; `scripts/revert_set_classifier.py`

## Problem

The cached-diff guard refuses a declared staged path whenever its content matches any ancestor vintage, labeling it a leaked revert. That is a useful accidental-reversal check, but it has no narrow way to recognize an intentional ancestor restoration that the operator explicitly authorized as part of the task. A user-authorized migration consolidation removed an obsolete Compose mount while combining its SQL into the prior migration; the resulting Compose file matched an ancestor and closeout stopped, although the restoration was the requested change. The bounded workaround is to make a minimal, behavior-preserving edit in the same file so the resulting tree no longer equals the old ancestor. That workaround adds incidental churn and does not solve the recurring class.

## Expected

Preserve accidental-reversal detection while allowing a narrowly evidenced, user-authorized content restoration to pass through the existing closeout. The authorization must bind to the exact path and intended outcome, be consumed by the current run only, and leave unrelated ancestor-matching paths refusing. Do not add a broad bypass or weaken stale-checkout adjudication.

## Evidence and deduplication

- The current runner extracts any declared `reversal: ... dirty state equals ancestor ...` path as leaked and exits before landing (`scripts/done_run.sh`, cached-diff-guard stage).
- The completed declared-deletion plan intentionally added a shape-specific passage for absent declared paths while retaining refusal for content reversals (`docs/history/plans/completed/2026-10-15-done-run-declared-deletion-path.md`). This incident is the missing content-restoration complement, not another declared-deletion defect.
- The open staged-reversal backlog concerns the primary index being mutated by squash landing (`docs/history/plans/completed/2026-10-14-post-landing-reconciliation-enforcement.md`); it does not cover this guard's classification of an explicitly intended staged file.
- The user-directed gate-recovery clause permits safe workarounds within existing authority, but explicitly does not authorize bypassing a refusing gate (`docs/history/plans/completed/2026-10-17-investigate-user-directed-gate-workaround.md`).

## Resolution space

Recommended: retain the cached-diff guard and add an invocation-local authorization option for one user-authorized ancestor restoration, bound to the exact repo-relative path and operator-supplied expected blob. Resolve it against the current run, preserve the accepted declared-set tree through configured hooks, and update only the branch identity captured before hooks if its symbolic target and OID still match. Revalidate the token-owned run lock immediately before the ref update. This directly removes the false positive without removing accidental-reversal protection or creating a standing receipt.

Rejected alternatives:
- Remove the cached-diff guard: rejected because the guard exists to stop accidental ancestor-vintage content from being committed (`agents/skills/done/SKILL.md`, Step 3; `scripts/done_run.sh`, cached-diff-guard stage).
- Keep the guard unchanged and require incidental content edits: rejected because the witnessed authorized restoration still blocks closeout and the workaround creates unrelated churn (this incident).
- Add a generic `--force` or user-directed bypass: rejected because the user-directed recovery policy expressly forbids bypassing a refusing gate (`docs/history/plans/completed/2026-10-17-investigate-user-directed-gate-workaround.md`).

Rule 42 no-exit alternatives for the fix-class refusal surface:
- Add the sanctioned exit: this is possible and is the selected behavior. Bind it to one current-run path and operator-supplied blob; a generic skip would not preserve the guard for adjacent paths.
- Remove the false positive: unconditionally accepting ancestor-matching declared paths would also accept accidental reversals. Removing the classifier or cached-diff check breaks that contract; narrowing the exception requires the same explicit path/blob authorization.
- Simplify the flow: leaving the guard unchanged and requiring an incidental edit is the only current workaround, but preserves recurring manual churn. The current path-limited `git commit` can re-read worktree bytes after the staged-blob check (reproduced in review r3 F1); a no-pathspec commit can include unrelated staged entries and lose the declared-scope contract. No simpler existing commit form satisfies both constraints.
- Further alternative recorded above: a generic force or user-directed bypass violates recovery policy and is not admissible.

Any added commit protocol must bind intent to the active run, exact path, expected blob, and actual landing tree without a standing bypass. The commit has exactly one parent at captured `HEAD`. Pre-update commit hooks can change the symbolic branch target or release and replace the run lock, so the final boundary revalidates run/lock ownership and atomically verifies `HEAD` identity with the captured ref update. In detached mode, update direct `HEAD` by captured-OID CAS without creating a branch. Configured `reference-transaction` hooks are trusted Git transaction participants: preserve their standard phases and veto behavior, but make no wrapper guarantee against their own side effects. `post-commit` follows a successful update. Price this machinery with the re-derivable completed-integrity-failure witness; prefer a smaller existing mechanism only if it preserves the declared-scope and hook contracts.
