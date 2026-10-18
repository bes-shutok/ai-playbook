# Demoted closeout-sweep arms (survey advisories)

The done closeout's per-run sweep roster no longer carries the two zero-catch
sweeps below. Their duties survive as periodic survey arms, recorded here so
the duty outlives the roster change (the done target-state plan's survey-note
checkbox). Each arm runs on survey cadence at the operator's or the loop's
discretion; neither ever gates a done run.

- **Editor residue scan (periodic).** On survey, scan the repository for
  editor swap and backup residue (`*.swp`, `*.swo`, `*~`, `.DS_Store` under
  tracked trees) and file or sweep findings per the survey's disposition
  ladder. Cadence: one pass per weekly survey cycle is sufficient.
- **Backlog-inbox filing audit (periodic).** On survey, audit that findings
  captured by receiving-review's capture step actually landed as backlog rows
  (the filing duty moved to that capture step when the per-run roster check
  was demoted); file the missing rows or record the gap.

Ledger: each arm's evidence intake lands its own `gate_liveness_ledger.json`
row update under `vim-swap-sweep` / `backlog-inbox` when it fires.
