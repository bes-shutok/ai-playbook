# Backlog: stale Codex worktrees can mistake a moved pin baseline for a landing blocker

- **Filed:** 2026-10-15, execute-plan-outcome-reporting ad-hoc landing recovery
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** observed execution interruption
- **Class:** maintenance landing recovery
- **Driving force:** reliability + operator time
- **Cluster:** docs/history/backlog/2026-10-15-post-impl-pins-baseline-adjective.md
- **Cluster:** docs/history/backlog/2026-10-07-witnessed-fail-arm-enumeration-stale.md (backlog-wide survey: maintenance pins baseline and expected-literal alignment)
- **Skill/step:** `agents/skills/maintenance/SKILL.md`, ad-hoc execution landing; `scripts/check_maintenance_pins.sh`
- **Incident:** Codex ad-hoc branch `codex/adhoc-execute-plan-outcome-reporting`, initial base `c52d57def5d694e7017e4cb4fc4a0c2cf1d2c575`
- **Catch frequency:** observed once; exact frequency of stale-base pin failures is unknown
- **False-positive cost:** authorized work remains stranded and its worktree/branch remain allocated until someone notices that the baseline moved
- **Review date:** 2026-11-15

## Problem

The ad-hoc execution branch started at `c52d57d`. The two skill spans were already present there, but `scripts/check_maintenance_pins.sh` still searched for retired literals: `runs dual and records the ambiguity in its decision channels` and `classifies exec, execute, execution wording as exec mode`. A later local `main` revision updated those pin expectations to the current skill text. Rebasing the unchanged task delta onto that tip made the pins suite pass. The original refusal treated stale pin expectations on the branch base as a task blocker and left the branch and worktree allocated.

## Expected

Keep each maintenance pin's expected literal aligned with its owning skill text. When a task branch's pin suite fails, compare the pin script's expected literals with the actual spans at that branch's base before attributing the failure to the task. If local `main` contains the corrected pin expectations, refresh the task branch and rerun the suite before deciding whether the task is blocked. Keep a genuine current-tree pin failure blocking; do not weaken or bypass a failing pin.

For this incident, after the reviewed change is verified on the target branch, remove the completed ad-hoc worktree and its dedicated branch, verifying the worktree is clean and the landing commit is reachable first.

## Suggested direction

Trace the two pin literals through the commits that changed the skill text and the pins suite. Keep the existing pins and update their expected spans to match their current source, with a fixture or direct probe that proves both the matching and mismatch shapes. Preserve the normal freshness check, containment, merge lock, and compare-and-swap. After review and a successful landing, verify the commit is reachable and the worktree has no untransferred changes, then remove the completed incident worktree and branch. Do not demote or skip the pins suite, and do not add another ledger or gate.

## Alternatives

- Weaken the two pins or allow landing when the suite fails: rejected because both skill spans existed at the original base and the defect was the pins' obsolete expected literals; updating the literals restored the suite without removing its checks (`scripts/check_maintenance_pins.sh`, `OUTCOME: pass` on the refreshed branch).
- Keep the refusal and ask the operator to diagnose it: rejected because the exact cause was a mismatch between checker literals and source text, and rebasing onto the current local target provided a compliant recovery; the maintenance skill's Blocker recovery rule requires using a safe workaround.
- Add a separate freshness validator or persistent landing ledger: rejected because `land_squash.sh` already has a check-landing base-freshness gate and normal containment/CAS checks; no incident demonstrates a missing persistent record (`scripts/land_squash.sh`, `land-worktree` contract).
