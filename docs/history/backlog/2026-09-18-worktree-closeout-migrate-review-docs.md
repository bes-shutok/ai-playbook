# Backlog: worktree closeout must migrate fresh review docs to the main checkout

Status: open
Workflow: backlog
Source: Andrey 2026-09-18: "we might need execution or plan authoring when it works on worktree and squash merge afterwards to also bring all freshly created review docs from the worktree to the main project and branch." Motivated by the same post-mortem as the parked legacy verdict-grammar plan (whose coverage gaps name the main-checkout-bound corpus); root-caused 2026-09-18: zero worktree handling exists in execute-plan, done, or any maintenance asset, the temp-worktree squash pattern lives only in session memories.
Severity: Medium (silent evidence loss: every worktree run that ends in squash-merge plus worktree deletion destroys its review staging docs and session logs; certification chains break retroactively)
Scope: agents/skills/execute-plan/SKILL.md (Phase 0 baseline + Phase 5 migration step), agents/skills/maintenance/prompt-templates.md (execution and authoring blueprint closeouts), agents/skills/done/SKILL.md (worktree pointer), agents/skills/docs-branch/SKILL.md (ordering note only)

## Problem

The run artifacts that matter most are exactly the ones git does not carry:

- Review staging docs (`docs/reviews/*.md` + `.stats.json` sidecars), the
  Phase 3 review evidence and the sidecars the readiness gate and the sweep
  read;
- Session tmp logs and the run manifest (`docs/tmp/execute-plan/<PLAN_SLUG>/`)
 , the resume, learn, and audit trail;
- Other gitignored run debris under `docs/tmp/`.

All are gitignored. When a plan execution or an authoring run happens in a
temp worktree, a recurring pattern when the main checkout is blocked by
untracked-state conflicts or peer branch occupancy, and the advised pattern in
past runs (temp-worktree squash merges are recorded in session notes; the
2026-09-15 maintenance revision deliberately removed worktree isolation from
maintenance children, so worktree use today is operator- or plan-prescribed
and entirely unprescribed by skill text), the final squash merge to the main
branch carries only TRACKED changes. Deleting the worktree then silently
destroys the run's review evidence:

1. The archived plan's certification chain breaks in the main checkout: the
   live readiness gate there finds no sidecars for the plan's review rounds
   (the same main-checkout-bound corpus problem recorded as coverage gap 2 of
   the parked legacy verdict-grammar plan).
2. Review freshness, drift analysis, and review-reconciliation lose the
   rounds they exist to reconcile.
3. The learn/done value of session `.md` logs is lost, or stranded on a docs
   branch sync performed from the worktree, which writes the orphan branch but
   never the main checkout's on-disk corpus.

## Suggested fix

A closeout migration step, mandatory whenever the run's checkout is not the
main checkout, in both execution and authoring flows:

- **Phase 0 baseline**: at run start, record the existing file set under the
  gitignored doc dirs (`docs/reviews/`, `docs/tmp/`) so closeout can enumerate
  exactly what the run added or modified (a one-line `find -newer` marker file
  or a captured listing under the session tmp dir).
- **Closeout migration (before any worktree removal)**: enumerate new and
  modified files against the baseline; copy each to the MAIN checkout at the
  identical path; verify the copy (byte size or checksum); record the migrated
  list in the run manifest / execution log. Copy, never move-first: the
  worktree is the backup until the main-copy checksum verifies.
- **Collision policy**: the main checkout is shared, a peer may have created
  same-slug docs there mid-run. If the target exists and differs, keep BOTH:
  rename the incoming copy with a run suffix (e.g. `<name>.wt-<plan-slug>`
  before the extension) and note the rename in the manifest; never silently
  overwrite; identical bytes → skip. Review-staging naming conventions own the
  rest.
- **Explicit exclusions**: the `.ai-playbook/` runtime dir (scheduler state,
  facts) is main-checkout-bound by design and is NOT migrated; tracked changes
  ride the squash merge as today and are out of scope for this step.
- **Ordering rules**: worktree removal is allowed only after verified
  migration; a `docs-branch` sync runs in the MAIN checkout AFTER migration
  (so the orphan branch and the on-disk corpus agree); if the main checkout is
  mid-merge/rebase or done-locked, stand down G3-style and retry migration,
  do not delete the worktree while blocked.
- **Post-migration evidence**: re-run the certification oracle (and, when the
  flow gates on it, the live readiness gate) in the MAIN checkout so the
  archive/completion claim is evidenced where the corpus actually lives.
- **Cross-volume edge**: worktrees on another disk/volume get copy semantics
  with the same verification; nothing in the step may assume `rename(2)`.

## Acceptance criteria

- A worktree execution or authoring run ends with every review staging doc and
  session log the run created present (verified) in the main checkout, with
  the migrated list recorded in the run manifest, before the worktree is
  removed.
- No migration step ever silently overwrites an existing main-checkout file;
  collisions resolve to renamed coexistence with a note.
- The certification/live-gate evidence for the completed plan is re-established
  in the main checkout, not only in the worktree.
- The non-worktree (in-place) flow is unchanged: the step is a no-op when the
  run's checkout IS the main checkout.
