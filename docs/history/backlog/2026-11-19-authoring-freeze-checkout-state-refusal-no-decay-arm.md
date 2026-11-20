# Backlog: the authoring freeze's landing sweep refuses on checkout record state with no unattended decay arm

- **Filed:** 2026-11-19, standalone learn over the 04:00 author carrier session (sess_bb40bf45, one-shot automation-1a3f6579)
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed availability defect (walk-invariant stop; 2026-11-10 arc via the log-path class, 2026-11-19 01:00 and 04:00 carriers via this class)
- **Class:** fence-class
- **Skill/step:** the freeze consumers (`agents/skills/plans/phase-0-placement.md` Entry freeze; the authoring blueprint's Phase 0 in `agents/skills/maintenance/template-authoring.md`); the landing-sweep gates that scan primary-checkout record state (`plans-archive-twin`, `doc-registry`) inside the `done_run.sh commit` rolling-log transaction; D-19's scope in `docs/maintenance/operator-directives.md`
- **Cluster:** docs/history/backlog/2026-11-19-stale-capture-record-commit-peer-clobber.md (that row owns repairing this instance's residue bytes and the record-commit preflight; this row owns the missing decay/recovery arm for the refusal class itself); docs/history/backlog/2026-11-10-authoring-lane-stale-residue-self-heal.md (covered; its fix D-19 pre-gives the operator direction for the log-path staged-delta class only); docs/history/plans/completed/2026-11-19-maintenance-dry-exit-conversion-fall-through.md (covered; same witnessed stand-down family: that plan owns the dry-exit conversion and D-18 line duties, this row the wall-side refusal class)

## Observed versus expected

Observed: an authoring session's Phase 0 freeze acquires the done lock cleanly, stages only its declared log path, and is then refused by the landing sweep's checkout-state gates over foreign stranded record state the session does not own (`plans-archive-twin` rc=1: a dated plan basename at both the living root and the completed archive; `doc-registry` rc=1 HARD: an immutable completed path present without override). The blueprint's refusal arms cover lock refusals only, so the sweep refusal leaves the session holding an acquired lock, and the transient shell's exit strands it (recovered via lesson 109's `release-orphaned` arm). Three 2026-11-19 author carriers stopped 0/1 on this shape (01:00, 03:00, 04:00; the 03:00 stand-down is recorded in the window's session records); the stop is walk-invariant for entry-keyed authoring because every such run needs the same freeze write.

Expected: the unattended-decay treatment D-19 gave the log-path class, extended to this class: either a scope extension pre-giving the operator direction for decayed checkout record-state residue (age, dead-holder, non-log-path, blob-preserving conditions), or a sanctioned bounded-wait/skip-with-report arm at the freeze for this refusal class, so one occurrence does not burn a carrier; plus the blueprint's freeze stand-down arm naming the lock-release and owned-delta cleanup duty for the sweep-refusal shape (release or finalize inside the transaction shell before it exits).

## Evidence

- This session: `done_run.sh commit` refused `OUTCOME: fail` naming both gates; no plan bytes written; claim deleted ownership-checked, lock orphan-released (holder pid verified dead), frozen-line edit reverted, foreign surfaces untouched.
- The 01:00 carrier's stand-down on the same state (witnessed in `docs/history/backlog/2026-11-19-stale-capture-record-commit-peer-clobber.md` Evidence).
- D-19's six conditions all key on "a staged delta on a rolling prompt log path"; none reach non-log checkout record state.
- Second refusal shape, same session minutes later: the entry-emission log write was refused by the runner's pre-stage guard on a foreign staged prune of the log itself (staged deletion of the frozen trio's entry sections, index blob 352a3470cf526095c4caa0b55544e4239ede1a24 recorded; two of the three pruned plans sit in the completed archive, no fresh claim or run-start attributes the staged prune; own worktree delta removed, foreign bytes preserved untouched). A staged DELETION is outside D-19's adds-lines-only condition (2) as well, so the log-path class itself carries an uncovered sub-class.
- Resolution witnesses, same day (the interactive arc session that hit the twin class next): the twin-state instance cleared through an operator-directed migration landing (9d098910c: living-root copy removed, completed twin tracked, the two registry rows folded into the parsed first table) and the staged-deletion shape landed verbatim (62209adf9) under explicit per-path operator direction; both were interactive operator round-trips, the treatment an unattended carrier cannot perform, so the row's unattended-decay ask stays open.


## Dedup probe

Searched open backlog for `release-orphaned`, `entry-freeze`, `freeze refusal`, `sweep-refusal`, `Phase 0 freeze`: the 2026-11-10 row owns the log-path staged class (covered by D-19); the set-aside recipe row owns log-path foreign bytes; the stale-capture row owns this instance's bytes, the repair arm, and the record-commit preflight; no row owns the checkout-record-state refusal class or the freeze stand-down's missing lock-release duty.
