# closeout migrate: zero-delta carry is reported as success-shaped silence

Status: open
Priority: medium
Class: fence-class
Origin class: learn Step 1.9 project issue capture (2026-10-28 exec closeout witness)

## Observed versus expected

`worktree_closeout_migrate.py migrate` is baseline-relative: it copies only
changes made after the closeout baseline capture. When the baseline capture
postdates the run's edits (for example, the capture happened at closeout start
while the implement and review work predates it), the migrate leg reports
`Migrated 0` and returns clean, and the run's records never reach the primary
checkout. The zero result is indistinguishable, in the tool's own output, from
"a correct carry of an empty delta", so a closeout that trusts the success
shape strands every run-era record as residue in the removed worktree.

Witnessed 2026-10-28 (playbook repo, an execution closeout): migrate returned
`Migrated 0` for a run with 35 run-era records and 221 scratch files; the delta
was recovered by a direct worktree-versus-primary comparison with a manual copy
plus an append-merge of the shared telemetry ledger (replace would have
truncated the primary's live ledger rows).

## Suspected root area

`scripts/worktree_closeout_migrate.py` migrate/report leg.

## Remedy sketch (warning-only; machinery admission fields inline)

Admission: prevents the witnessed 2026-10-28 stranded-carry incident (this
row); expected catch frequency: every closeout whose baseline postdates owned
edits (silent-stranding class, observed once); false-positive cost: a warning
line on a legitimately empty delta; sunset: review after three closeouts or
promotion to a hard report on the next true catch, warning-only at landing per
the machinery admission protocol.

Smallest arm: when the migrate leg completes with zero migrated entries, print
a zero-delta report naming the baseline capture timestamp against the newest
mtime among the run's owned paths, so "no delta" and "stale baseline" are
distinguishable in the tool's own output. Rejected arm (pre-rejected here):
making the migrate leg re-baseline automatically, which would let a late
capture silently claim edits it never saw; the report-only arm keeps the
operator-visible decision.

## Cluster

- docs/history/backlog/2026-10-05-done-dirt-regression-blocks-reviewed-fix.md (closeout migration family)
