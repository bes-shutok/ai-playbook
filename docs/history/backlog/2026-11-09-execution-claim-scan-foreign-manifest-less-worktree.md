# Backlog: execution-claim gateway globally blocked by a manifest-less foreign worktree
- **Cluster:** docs/history/backlog/2026-11-07-dispatch-admission-manifest-less-outstanding-conservative-global-block.md

Created: 2026-11-09, interactive exec run for docs/history/plans/2026-11-09-hook-timeout-recurrence-diagnostic.md (session-held preserved claim, worktree 2026-11-09-hook-consult-profiling)

Driving force: correctness (lane-blocking refusal with no in-authority remedy)

## Observed refusal

`scripts/execution_claim.sh take` refuses with `conversion refused: the registered-manifest scan is inconclusive: registered worktree <path>: missing facts (no manifest path is guessed)` whenever ANY registered worktree in `git worktree list` lacks a readable `.ai-playbook/facts.md`. The refusal preserved the fresh claim and created worktree for operator reconciliation. Witnessed twice on 2026-11-09 ~22:14-22:15 WET: first against this run's own pre-created facts-less worktree (self-inflicted, removed and re-taken), then against the foreign detached worktree `2026-11-09-test-suite-heavy-trial` (owned by the live test-suite peer run, claim 21:40), which this run must not touch.

## Evidence-backed cause

- `.ai-playbook/facts.md` is untracked (gitignored), so every freshly created worktree lacks facts until its own run's transfer-in step.
- `scan_registered_manifest` (scripts/execution_claim.sh, `facts_tmp_dir_for`/`manifest_path_for`) walks ALL registered worktrees and returns `inconclusive` on the first facts discovery refusal, fail-closed by design (a manifest could hide behind unreadable facts).
- Net effect: while any facts-less registered worktree exists (a scratch/detached peer worktree qualifies), every take in the repository is refused, and the preserved-claim recovery path requires the scan to complete too. Same shape previously recorded as the admission-stall witness of 2026-11-07 18:06Z (manifest-less peer global refusal).

## Investigation (bounded, this run)

Root cause and alternatives were derived directly from scripts/execution_claim.sh (scan walk, refusal arms, `cmd_take` flow, `cmd_claim`/`cmd_refresh`/`cmd_sweep` command set) during the blocked take; no separate investigate log entry was filed because the full causal chain above is the investigation record. Alternatives rejected: writing facts into the foreign worktree (foreign-session write, outside authority); removing the foreign worktree (operator declined, 2026-11-09 in-session); primary-placement lane (`claim` mode) (worktree_policy = "worktrees" mandates worktree placement for executions).

## Smallest proposed correction

Scope the preservation scan's fail-closed inconclusive to worktrees plausibly holding a manifest for the claimed slug (for example, only worktrees whose branch or record names the slug, or only worktrees created before the take's claim), or make the scan tolerate facts-less worktrees that carry no docs/tmp at all, recording the residual risk in the scan's contract comment. Machinery admission: name an incident (this row), catch frequency, false-positive cost, and land warning-only first.

## Workaround of record (this run)

The operator reconciled the preserved claim in-session (2026-11-09): continue on the preserved claim after verifying no manifest for the slug exists at any resolvable registered-worktree path. This is an operator-directed reconciliation, not a gate edit; the scan itself is unchanged.
