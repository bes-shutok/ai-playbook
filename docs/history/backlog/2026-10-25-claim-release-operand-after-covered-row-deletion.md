# Backlog: execution-claim release needs an operand path that survives the covered-row deletion lifecycle

- **Filed:** 2026-10-25, learn Step 1.9 over the 2026-10-24 ad-hoc exec run
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Class:** fence-class (the release gateway's operand contract and the covered-row deletion rule are each correct alone; the gap is their missing complement)
- **Origin class:** session witness (closeout mechanics)
- **Cluster:** docs/history/backlog/2026-10-06-claim-fence-test-coverage-gaps.md; docs/history/backlog/2026-10-07-claim-fence-stem-case-drift.md; docs/history/backlog/2026-10-07-execution-claims-dir-resolution-drift.md (same surface: the execution-claim gateway; distinct defect classes, each already represented by a plans-root plan record)

## Finding

`scripts/execution_claim.sh release` derives the claim's artifact slug from the
plan operand file and requires that operand to be a readable on-disk file
(readable-file check near the usage header; `derive_slug` runs
`plan_readiness.py --print-artifact-slug` on the operand). The sanctioned
covered-row lifecycle deletes each entry's origin row from
`docs/history/backlog/EXEC-PROMPTS.md` in the same landing that covers it, so
by closeout time the operand the claim was taken against no longer exists and
every release refuses on the unreadable operand. The witnessed workaround
(restore the exact origin bytes with `git show <landing>^:<origin-path>` into
a gitignored `docs/tmp/` scratch path, keeping the original basename because
the slug derives from the filename, release against it, delete the scratch)
worked first try for all three claims in the run, but it is an undocumented
per-session improvisation.

## Suggested direction

One bounded arm, no new machinery: give `release` (and the sweep arm, which
reports preservation-scan inconclusiveness on the same shape) a documented
operand-recovery posture - either a `--operand-source <commit>:<path>`
flag that reads the operand bytes from git object storage instead of the
working tree, or a release-note line in the refusal text naming the exact
`git show` restore recipe the lesson now records (project-corpus lesson 226).
The flag arm is preferred: it removes the scratch-file dance without adding a
validator, and the slug derivation is unchanged.

## Evidence

- `scripts/execution_claim.sh` readable-operand requirement (usage-header
  region, "must be a readable file; its canonical artifact slug derives
  through plan_readiness.py --print-artifact-slug") and `derive_slug` at the
  script's slug section.
- Witnessed 2026-10-24: three consecutive closeouts (entries
  execution-claim-take-refusal-remedy-text, deciding-turn-inherits-step-order,
  children-cap-write-assert, landed as three same-day squash landings) each
  refused the release on the deleted origin row until the operand was
  restored from the landing's parent commit.
- Project-corpus witness: `docs/maintenance/development_lessons.md` #226.
