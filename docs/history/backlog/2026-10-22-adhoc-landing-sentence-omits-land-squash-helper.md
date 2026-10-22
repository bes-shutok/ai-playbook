# Backlog: the ad-hoc arm's landing sentence never routes to the squash-landing helper

- **Filed:** 2026-10-22 (learn capture over the 2026-10-22 parallel exec-mode run)
- **Status:** open
- **Priority:** medium
- **Workflow:** backlog
- **Origin class:** review-residual (learn Step 1.9 project issue)
- **Class:** investigate-then-fix (discoverability gap with a thrice-witnessed cost)
- **Driving force:** reliability
- **Skill/step:** the Ad-hoc backlog arm's landing sentence (`agents/skills/maintenance/decisions.md`, "one merge-landing-lock-serialized squash landing"); `scripts/land_squash.sh land` (the sanctioned landing form); lesson 99 in `docs/maintenance/development_lessons.md`
- **Environment:** playbook repo, ad-hoc exec worktree landings, 2026-10-22
- **Suspected root area:** the arm's landing sentence names the lock and the receipt contract but never names `scripts/land_squash.sh land` as the mechanism, so exec sessions hand-compose the landing (manual rebase, `git commit-tree` or `merge --squash`, manual `git update-ref`) and skip the helper's parentage, tree-equality, and reconciliation gates
Cluster: docs/history/backlog/2026-10-15-codex-stale-worktree-pins-landing-recovery (same surface: the squash-landing route and its helper)

## Observed vs expected

Observed: lesson 99's hand-composed-landing class was re-witnessed twice on 2026-10-22 alone, in two independent exec runs (one `git merge --squash` in the primary checkout, one `git commit-tree` plus two-value `git update-ref` from a run worktree), each landing correct only by luck and each skipping the helper's gates; the second run also skipped lesson 12's post-landing reconciliation and repaired the primary checkout's reversal dirt by hand. Expected: the text that authorizes the ad-hoc landing names the sanctioned mechanism, so a session assembling the landing reads the route instead of re-deriving (or skipping) it.

## Evidence and archaeology (2026-10-22)

- `scripts/land_squash.sh` header: "the lock-bound squash-landing helper for a primary checkout ... The only sanctioned way to run a squash landing"; its `land` mode covers a source worktree addressed through its own flags, so the ad-hoc worktree shape is in contract.
- Lesson 99 (2026-10-19 witness; re-witnessed twice 2026-10-22, both ad-hoc runs) records hand-composed landings skipping the archive-egress, parentage, and tree-equality gates; lesson 12 (re-witnessed 2026-10-22) records the skipped post-landing reconciliation.
- The Ad-hoc backlog arm's landing sentence (`agents/skills/maintenance/decisions.md`) specifies lock serialization and the `Ad-hoc-panel-pass:` receipt three-way equality but contains no `land_squash` reference; working-tree grep at the tip agrees.
- The helper itself is surfaced only in lesson 99's text and its own header; no skill text an exec session reads at landing time names it.

## Scope to resolve

Add the helper route to the arm's landing sentence (one clause naming `scripts/land_squash.sh land` as the mechanism, its worktree-source flags included), or record why the arm deliberately leaves the mechanism open. Price whether the execute-plan closeout landing text needs the same pointer.

## Alternatives to assess

- Enforce the helper mechanically (a guard refusing a landing commit not produced by the helper): rejected by the Machinery admission protocol unless a witnessed escaped-defect incident exists beyond "correct by luck" landings; the discoverability fix is removal-shaped and needs no admission case.
- Leave lesson 99 as the only pointer: rejected as the default because the lesson is read at learn time, not at landing time, and the thrice-witnessed recurrence shows landing-time text is where the route must live.
