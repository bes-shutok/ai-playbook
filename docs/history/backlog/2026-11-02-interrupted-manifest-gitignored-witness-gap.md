# Backlog: dead-run dispositions can never witness gitignored-only deliverables

Status: open
Priority: medium
Class: fix-class
Origin class: self-serving
Added: 2026-11-02, learn + investigate over the interactive maintenance auth session

## Problem

The sweep-gates lib's dead-root disposition refuses witness-first when the run's owned deliverables resolve through none of the witness arms (recorded path on disk, HEAD copy, completed-archive twin, landed deletion, note-backed). A run interrupted while its deliverables lived only under gitignored homes (a review round's staging pair under the reviews home) leaves those files in the dead worktree: they never land, they have no HEAD copy or archive twin, and a note cannot prove content that no longer exists. Two dead heads are stuck in exactly this shape; the per-turn census records them and the operator direction stays owed, and the drain entry deliberately scopes witness-refused heads out of its arm, so nobody owns the subclass.

## Exact location

- `scripts/done_sweep_gates_lib.py`, `disposition-manifest` witness arms and usage text.
- The survey's interrupted-manifest census arm (turn_error channel) that keeps recording the stuck heads.

## Suggested direction

Keep the witness bar. Add the smallest arm that lets a gitignored-only deliverable disposition on recorded evidence: the census record plus the turn-recorded refusal evidence (dated, naming the artifact and its loss class) accepted as the witness, priced under the machinery admission protocol (incident: the stuck heads; catch frequency: every interrupted run owning gitignored-only deliverables; false-positive cost: a disposition on lost evidence, bounded by requiring the recorded refusal evidence chain; review date 2026-12-02). Do not weaken the arms for tracked paths; do not delete residue.

## Evidence and scope

Witness: two dead heads refusing witness-first across consecutive census turns (2026-10-25 and 2026-11-01 heads); census records under the done-session corpus. Impact: census residue never drains mechanically and the operator ask recurs per turn.

## Dedup probe

Searched open rows and both rolling logs for disposition witness arms and gitignored witnesses. The orphaned-manifest-pool family and the drain entry cover the drainable pool and deliberately exclude witness-refused heads; no open item owns the witness-arm gap for gitignored-only deliverables.

## Update (2026-11-04, learn + investigate over the closeout-clobber authoring session)

One of the two stuck heads is now dispositioned without needing this row's proposed arm: the 2026-11-01 head refused disposition-manifest dead-root witness-first, but its five review sidecars had survived the owning run's closeout at the primary reviews home (untracked), so the existing note-backed arm resolved them once the note named each path verbatim; the manifest closed as accounted (lane work landed on main, riders and finalize pass verified from the scheduler-state record). The remaining head (2026-10-25) is the standing operator park per the 2026-11-01 investigate disposition, not a census-growth case, and the census record now shows the drained baseline. The row's open scope is unchanged and narrower: it now owns only the truly-lost-content arm (deliverables that no longer exist anywhere, where a note cannot attest a surviving home), which no witnessed head currently exercises. Priority held at medium on that reduced scope; the composition rule for the note-backed arm is recorded as the second witness of project lesson 45.
