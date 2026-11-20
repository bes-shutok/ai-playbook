# exec-plan checkbox marking stranded in the primary checkout

- **Status:** open
- **Priority:** medium
- **Class:** skill-text
- **Driving force:** code-quality
- **Origin:** dirt attribution investigation 2026-11-06 (interactive exec run over plan 2026-11-02-review-staging-archived-plan-source-identity)

**Finding:** a worktree-placement execution session marked its Task 1 checkbox flips `[ ]`→`[x]` on the primary checkout's copy of the executing plan instead of the executing worktree's copy. The flips sat uncommitted on main while the worktree's plan copy stayed clean at HEAD, and main held dirt on exactly the path the landing's Phase 4 archive pass renames — a shape that refuses the landing merge over locally modified files and blocks the lane's own completion. Doctrine (plans SKILL.md landing closeout; execute-plan SKILL.md execution-status flip duty) builds plan-file edits and riders on the authoring branch in the worktree so uncommitted edits ride the landing squash, as landed f9fcdc7b1 did.

**Disposition of the instance (2026-11-06 ~17:52, with the owning session live and holding no merge lock):** the flip blob (4a71831db) was mirrored byte-identically into the worktree's plan copy (verified by blob hash, rides the landing squash) and the primary checkout was reverted to HEAD; main is clean, no completed leg redone.

**Durable fix candidate:** a skill-text clarification in `agents/skills/execute-plan/` (worktree-first placement section) stating that during worktree-placement execution all owned-plan file edits — including per-task checkbox marking — are made on the executing worktree's copy of the plan, never the primary checkout's copy; the primary's plan path is read-only for the executing session until the landing carries the archived result. Non-blocking; the instance above is the motivating witness (second witness required before any gate promotion per the machinery admission protocol).

**Witness 2026-11-18 (second instance, same mechanism):** the corrections-writer execution window left the primary checkout's copy of `docs/history/plans/2026-11-13-corrections-writer-distinct-session-dispatch-gap.md` carrying the execution's checkbox flips (blob 4fed118aa) byte-identical to the run worktree's copy, the primary copy uncommitted at the 2026-11-19 filing while the canonical executed bytes live on the run branch. The second witness the durable-fix candidate required has arrived; the gate-promotion question is now ripe for the authoring lane.

**Cluster:** docs/history/backlog/2026-11-19-stale-capture-record-commit-peer-clobber.md (same window; that row owns the commit that swept a dead peer's stranded staged state into history on the same shared-checkout hazard)
