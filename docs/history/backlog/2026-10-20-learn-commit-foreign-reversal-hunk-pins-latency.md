# Backlog: a learn commit staged a foreign pure-reversal hunk in a pinned maintenance surface and no gate noticed for a day

- **Filed:** 2026-10-20, learn pass over the 06:35 scheduled exec run (the run's pins reconciliation found and repaired the clobber); second witness folded 2026-10-20 by the learn pass over the 11:00 scheduler turn's session
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** session-witnessed skill-usage issue (learn Step 1.8 commit rule's own-edit check did not stop a foreign hunk; no detection cadence for a red pin on the base branch)
- **Class:** fix-class
- **Driving force:** correctness (operative skill text silently reverted on the base branch)
- **Skill/step:** `agents/skills/learn/step-1-extract.md` Step 1.8 commit rule (the "verify the working-tree delta for that path is this session's own edit" sentence); `agents/skills/investigate/SKILL.md` Stage 4 write bullet (its same-turn entry commit names no own-edit check at all); `scripts/check_maintenance_pins.sh` run cadence (the suite runs inside the ad-hoc arm, the plan execution gates, and the done sweep, not on direct corpus commits)
- **Severity/source:** ce3a984b8 (learn commit, 2026-10-19 13:44) with direct parent 19866b067 (exec landing, 13:35) committed `agents/skills/maintenance/survey-arms.md` with a pure deletion of the Verify-successor leg sentence 19866b067 had added; pin `clocked-order consult verify-successor leg` red on main until a42e0e1d4 (2026-10-20) restored the sentence byte-verbatim from 19866b067
- **Second witness:** 563d2e2e (investigate entry commit, 2026-10-19 15:39) re-added the `done-immediate-commit-single-homing` dispatch entry that the peer's direct commit 0c6a66f3f (15:38:57) had pruned seventeen seconds earlier, as a pure-addition hunk inside the commit's own declared rolling log `docs/history/backlog/PLAN-PROMPTS.md`; the resurrected entry stayed dispatchable until the 93fff300b monitor prune (2026-10-20). Lesson 134 now carries the addition-direction arm.
- **Capture hygiene:** repo-relative paths only; no personal or machine-specific data.
- **Dedup probe:** searched open backlog filenames and text for `clobber`, `foreign hunk`, `survey-arms`, `stale write`, `own edit`, `pins`; no open row covers the direct-commit staging check or the pins run cadence. Nearest: `docs/history/backlog/2026-10-10-execute-plan-rebase-after-surface-refactor.md` (execution-branch rebase scope, not direct commits).

## Problem

The learn skill's Step 1.8 commit rule already says: before staging each non-backlog path, verify the working-tree delta for that path is this session's own edit, and on foreign or unrecognizable hunks skip the path. The 2026-10-19 learn run staged `agents/skills/maintenance/survey-arms.md` anyway. The hunk was a pure deletion of a 4000-plus-character line's newest sentence, in a commit whose subject named two lessons and a backlog witness and nothing about the maintenance survey. The most plausible mechanism is a whole-file write from a working-tree copy read before 19866b067 landed (lesson 134 in `docs/maintenance/development_lessons.md` records the signature).

Two gaps compound:

1. The own-edit check is a judgment sentence with no mechanical shape. It names no probe (word-diff, `git log -1 -- <path>` age versus the session's read, pure-deletion test) that would have made the foreign hunk obvious; a run reading the dirty path as "my edit" passes the check by assumption. Lesson 6 states the clobber signature for squash landings; the direct-commit path inherits it only through lesson 134, not through the skill text that drives the commit.
2. Nothing runs the pins suite on a direct commit that touches `agents/skills/maintenance/`. The suite runs inside the ad-hoc arm, the plan execution gates (`scripts/run_plan_gates.sh`), and the done sweep (`scripts/done_sweep_gates_lib.py`), so a pin broken by a learn or backlog commit stays red on main until an unrelated run happens to execute the suite and must then reconcile a failure it did not cause (the suite-failure clause of the ad-hoc arm). Here that latency was about a day.
3. The signature has an addition direction the first witness does not show: a stale-read write re-adds a span a peer just pruned, inside a path the commit legitimately names, so the pure-deletion test and the declared-path test both pass and only the path-age test fires. The investigate skill's Stage 4 bullet carries the write-time re-read rule but no commit-time own-edit check, so the resurrection in 563d2e2e reached main unexamined and the pruned dispatch entry was live again for about twenty hours.

## Expected

A direct commit by explicit path never carries a hunk the committing session did not author; a pure-deletion hunk on a path the commit's purpose does not name, or a pure-addition hunk the session did not write, is a stop, not a stage. A pin broken on the base branch is reported by the commit that broke it, not by the next run that trips over it.

## Suggested fix

Smallest form first, per the repository guidelines' Machinery admission protocol (no new blocking gate):

1. Skill text, one sentence each in the learn Step 1.8 commit rule and the investigate Stage 4 write bullet: name the mechanical shape of the own-edit check (word-diff each staged path against HEAD; a pure-deletion hunk, a pure-addition hunk the session did not write, or a path whose last landing is newer than the session's read of it, is foreign; cite lesson 134 in at most one line, per the anti-growth rules). The runtime skill registry symlinks to this repository's `agents/skills/`, so the single edit per skill is the landing.
2. Report-only pins run: when a learn or investigate commit stages a path under `agents/skills/maintenance/`, run `bash scripts/check_maintenance_pins.sh` before the commit and print its result; a failure is reported in the run output, never a block. Admission: incident ce3a984b8; expected catch frequency low (one witnessed in the corpus's history); false-positive cost a few seconds per such commit; review date 2027-01-20 (retire if no second catch).

Rejected: a repository-wide pre-commit hook (the `commit-tree` plus `update-ref` landing path never runs it, hooks install per agent, and it would be a new blocking gate with one incident); a pins run on every learn commit regardless of path (pays the suite's cost on commits that cannot break a pin).
