# Backlog: learn-authored project-corpus edit hunks strand uncommitted on the primary checkout when the writing session's commit legs skip the corpus leg

- **Filed:** 2026-11-20, 24h session-pattern harvest learn run (learn Step 1.8; learn-corpus durability family)
- **Status:** open (the witness's stranded bytes landed in-repo same turn, verified; the write-time durability floor decision pending)
- **Workflow:** backlog
- **Priority:** low
- **Class:** fix-class
- **Origin class:** witnessed orphan-dirt incident (family recurrence; writer session bracketed by its own skill-gate marker and commit trail)
- **Skill/step:** `agents/skills/learn/step-1-extract.md` Step 1.8 commit rule (the bounded-span commit leg for learn-authored corpus hunks in a shared checkout)
- **Cluster:** docs/history/backlog/2026-11-19-caps-ratchet-regen-uncommitted-orphan-dirt.md (same uncommitted-primary-write defect family; that row owns the caps-table surface and holds the pending detection-arm decision); docs/history/backlog/2026-11-02-primary-tree-backlog-writes-no-commit-leg.md (that row owns untracked record FILES whose writing session died before any commit leg; this row owns tracked-corpus EDIT hunks whose writer kept committing other paths and skipped the corpus leg); docs/history/backlog/2026-10-23-dirt-gate-head-pinned-after-classification-window.md (the worktree-side dirt gate sibling; the primary tree between runs stays outside its inspection)

## Problem

Witnessed sequence, all legs on disk:

1. 2026-11-20 08:58 local, a learn skill-gate marker was written (`learn.433a6a3482712b29.91780d1dc9c515f3.marker`, the HOME-anchored runtime store), proving the writing session invoked the learn skill's corpus-write recipe in this project.
2. 08:59:01, two second-witness paragraphs (lessons 331 and 476, four added lines) were written into the tracked corpus `docs/maintenance/development_lessons.md` on the primary working tree. Their subject: the same session's own codex provider plan work (the landing that deleted the provider-availability origin row and added the app-server residual whose Cluster line named the deleted origin).
3. 09:01, the same session committed the cluster retarget that fixed exactly the stale pointer those witnesses describe, and skipped the corpus hunks. Three further commits followed through 09:25 (backlog row, investigate entry, plan freeze), none carrying the corpus file. The session then ended with the hunks uncommitted.
4. The stranded hunks sat through the morning's landing traffic (the 10:00 exec run and later) invisible to every gate: the corpus file is outside the run-worktree dirt gate's scope, no closeout inspects the primary tree between runs, and a second-witness append produces no validator artifact. The next session's 24h harvest (this run) found them as the only working-tree delta, verified their claims against disk, and landed them.

Structural reason nothing detected or committed them: Step 1.8's commit rule already names the two sanctioned arms for exactly this shape (commit the hunks in the same bounded span as the gated write, or record each written path's blob id at the write), and its stop-path arm covers runs that stop at a pause or quota wall. The witnessed writer took neither arm, was not stop-path (it kept committing other paths for over 25 minutes after the write), and no step after the write checks that one of the two arms ran. The durability of learn-authored corpus content therefore rides on undischarged discipline, and a skipped leg leaves the bytes silent until an operator ask or a harvest ask notices the dirt.

## Suggested direction

Write-time durability floor (wording-level, no gate): in Step 1.8's commit rule, make the write-time blob record (`git hash-object -w <path>`, one whole-file blob per written path) the unconditional floor for every learn-authored project-corpus write in a shared checkout, with the bounded-span commit remaining the goal arm. A skipped commit leg then leaves the bytes attributable and recoverable from the session's own output instead of silently stranded. The stop-path arm's existing blob-record vocabulary already carries the shape; the change folds the floor into the same sentence family and absorbs its growth into the existing sentences. No new gate, validator, or lock; the caps-ratchet row's pending detection-arm decision stays independent and untouched.

## Machinery admission

No machinery proposed: the fix is a duty clarification inside an existing commit rule, removal-shaped on the silent-strand outcome (a skipped commit leg stops being invisible). The witnessed incident is this row; expected catch frequency is low (rare skipped commit legs; the caps row's incident is the family's first witness); false-positive cost is one extra `git hash-object` invocation per corpus write; review date 2027-02-20 if the floor is later promoted into a gate.

## Rejected alternatives

- Treat this as a one-off discipline miss and record the witness only: rejected; the family now holds three distinct legs in one month (the caps-table regen strand, this corpus write, and the 2026-11-19 checkpoint-revert strand), each surfaced only by an operator ask or a harvest ask.
- Extend the stop-path arm's commit-or-record mandate to every learn write boundary: rejected as over-broad; the in-span commit leg lands in the ordinary case and stays the goal arm, so only the write-time floor needs to be unconditional.
- Add the warning-only primary-dirt detector now: rejected; the caps-ratchet row holds that machinery decision pending with its own admission fields, and this row adds a witness to that family rather than a competing arm (evidence basis: that row's Detection arm paragraph).

## Evidence

- Corpus file mtime 2026-11-20 08:59:01; the working-tree delta at harvest time was exactly the two second-witness hunks (lessons 331 and 476, four added lines).
- Skill-gate marker `learn.433a6a3482712b29.91780d1dc9c515f3.marker` mtime 08:58, one minute before the write.
- Commit bracket: d78c0f7dc 08:56 (the residuals investigate that added the app-server residual row), 2f0ad973a 09:01 (the cluster retarget, two minutes after the corpus write, not carrying it), 8334a2ab1 / 86a909470 / 91e5d203a 09:21-09:25 (the self-heal recovery trio), none touching the corpus file.
- Witness claims verified on disk at harvest: the completed codex plan exists at HEAD; landing 1b3503c37 deleted the provider-availability origin row and added the app-server residual whose Cluster line named that deleted row; retarget 2f0ad973a re-pointed the cluster line to the completed twin.
- Repair landing of the stranded bytes: commit 09793c48f (same turn as this row, verification stated in its message).
- Family precedents: the caps-row repair landing b7c469d30 (verified stranded regen landed same-day) and the Step 1.8 stop-path arm landing c6c978995 (the sanctioned blob-record shape).
