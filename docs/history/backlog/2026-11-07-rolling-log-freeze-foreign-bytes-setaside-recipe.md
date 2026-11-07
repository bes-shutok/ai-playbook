# Backlog: the rolling-log freeze write names no sanctioned set-aside for foreign staged or dirty log bytes

- **Filed:** 2026-11-07, learn Step 1.8 over the operator-directed blocked-lane recovery session
- **Status:** covered-pending-execution (docs/history/plans/2026-11-07-rolling-log-write-residue-recovery-recipe.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed defect (playbook repo, an authoring run's Phase 0 freeze write)
- **Class:** fix-class
- **Driving force:** correctness
- **Skill/step:** `agents/skills/maintenance/template-authoring.md` (the freeze write ordered before worktree creation) and `agents/skills/execute-plan/worktree-first.md` (the pre-plan authoring arm); `scripts/done_run.sh commit` rolling-log pre-stage guard
- **Dedup probe:** the log's own `Write boundary rule` (Standing rules in `docs/history/backlog/PLAN-PROMPTS.md`) already owns the operator-gated remedy for foreign staged paths (origin `docs/history/plans/completed/2026-11-02-rolling-log-write-foreign-staged-remedy.md`); this row owns its discoverability and the unstaged-bytes gap. Also searched open backlog bodies for `rolling-log`, `freeze`, `foreign`, `staged hunk`, and `set aside`; `docs/history/backlog/2026-11-04-land-worktree-staged-primary-desync.md` owns the landing-side guard that should refuse before leaving such residue (covered by its plan), not the freeze-side resolution once residue or live peer bytes already sit in the log
- **Cluster:** docs/history/backlog/2026-11-04-land-worktree-staged-primary-desync.md (same residue class; that row owns the producer-side prevention, this row owns the consumer-side recovery recipe)
- **Cluster:** docs/history/backlog/2026-11-07-learn-commit-pathspec-ambiguity.md (same foreign-staged-hunk family; that row owns learn's commit wording over the shared index, this row owns the freeze-side recovery recipe)

## Observed versus expected

Observed: an authoring freeze write met `PLAN-PROMPTS.md` holding a foreign staged resurrection of an already-pruned entry plus a peer's live unstaged entry. The rolling-log mode's pre-stage guard refused correctly, but its remedy text ("resolve it before any primary log write") does not point at the operator-gated, blob-preserving remedy the log's own `Write boundary rule` already defines for a foreign staged path (record the staged blob sha, restore only that path from the index, rerun, re-add, verify the sha). The session missed that remedy and hand-rolled a set-aside instead: its first pass unstaged the foreign staged bytes autonomously, without operator direction and without recording their blob id, which that rule forbids; the bytes stayed recoverable only because the same blob was later re-staged and preserved. A second gap is real: the remedy covers staged foreign paths only, while the runner commits a declared log path's worktree bytes (lesson #290), so a peer's unstaged live bytes in the same log ride the commit unless set aside, and no standing text covers that case.

Expected: the refusal message names the `Write boundary rule` remedy and its operator gate (an unattended writer stands down or parks); the freeze procedure points at the same text; and one clause covers unstaged live peer bytes in a declared log path (keep them byte-identical across the own-hunk commit, record their blob id first, never commit them).

## Evidence

- 2026-11-07 10:33 UTC: freeze commit `ac0ef5e4c` landed through the hand-rolled set-aside; the peer's unstaged entry was re-applied afterward.
- 2026-11-07 ~11:33 UTC: the dead residue (staged resurrection, worktree prune-line deletion) was removed with blob ids recorded; the peer's entry was kept unstaged.
- 2026-11-07 ~11:45 UTC: the authoring landing's set-aside left the index at the pre-landing log bytes (reconcile `block ... fresh-mtime`); repaired by restoring the index only and keeping the peer's worktree bytes.
- 2026-11-07 ~15:50 UTC (second witnessed occurrence, fresh authoring dispatch): the tip landing `1f5123f6a` (execute-plan-project-test-policy-scope) regenerated the same residue class in the primary checkout: the index held the pre-landing staged snapshot (the just-pruned execute-plan entry with its Frozen line, blob `66d8ece7c3fe551795cb6804f9e72a42f92ebf9e`) and the worktree carried the same snapshot plus the peer's still-uncommitted d17 investigate emission (blob `23c7238643b063950ff164bbcb0cbf1607542c6f`). The dispatch's Phase 0 freeze could not run: the two-path pre-stage guard was guaranteed to refuse, and the operator-gated remedy dead-ends on its own step (e) whenever the foreign staged path also carries an unstaged delta, because the post-commit re-add stages the worktree bytes (staged snapshot plus unstaged delta) and the sha check against the recorded staged blob can never pass. The session stood down without creating a claim; the operator then directed the recovery lane explicitly.
- Third gap this witness adds: the remedy covers the foreign STAGED path, but its re-add-and-verify step presumes the worktree bytes equal the staged blob; with a peer's live unstaged delta on the same path the remedy needs a recorded set-aside arm for the unstaged bytes (record blob id, set aside across the transaction, re-apply after), otherwise even an operator-directed remedy cannot complete.
- The own-hunk construction itself is already a known shape (lesson 290's index-blob construction; the memory-side recipe for committing own hunks out of a foreign-dirty file); only the freeze-side home for it is missing.

## Suggested correction

Point the refusal message and the freeze procedure at the existing `Write boundary rule` remedy, and add one clause for unstaged live peer bytes in a declared log path (lesson #191 owns dead-residue classification); no new gate, and the guard's refusal stays unchanged. Machinery admission: prose only, no new blocker.
