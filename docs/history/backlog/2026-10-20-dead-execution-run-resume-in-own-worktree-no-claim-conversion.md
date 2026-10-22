# Backlog: resuming a dead execution run inside its surviving worktree has no claim-conversion step; the gateway's stale-takeover arm refuses when the worktree exists

- **Filed:** 2026-10-20, operator-directed resume of the done-immediate-commit-single-homing closeout
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Cluster:** docs/history/backlog/completed/2026-10-19-authoring-claim-closeout-delete-duty.md (same artifact class: claim files outliving their session)
- **Cluster:** docs/history/backlog/2026-10-13-execution-claim-retry-ceiling-unpinned.md (same gateway: `scripts/execution_claim.sh` arms)
- **Cluster:** docs/history/backlog/2026-10-11-ad-hoc-worktree-lifecycle-owner-gap.md (same artifact class: a run's worktree and claim outliving their session; investigate 2026-10-20 roster)
- **Origin class:** observed recovery gap
- **Class:** fix-class
- **Skill/step:** `agents/skills/maintenance/template-execution.md` (EXECUTION CLAIM paragraph: stale-foreign takeover arm); `agents/skills/execute-plan/SKILL.md` (Execution claim registration; Recovery section); `scripts/execution_claim.sh` (branch-occupant pre-takeover gate)
- **Driving force:** reliability (an operator-directed resume should leave a truthful claim, never a dead session id kept fresh by hand)

## Problem

The claim protocol has two shapes: a fresh foreign claim refuses the start, and a stale foreign claim is taken over through the gateway's `take`, which unlinks the stale claim and creates this session's own. The gateway refuses that takeover before it starts when the branch is held by an existing worktree, which is exactly the state a dead run leaves behind: on 2026-10-20 the dispatched session zcode-exec-operator-20261020-1450 hit the usage wall after staging the archive, leaving its worktree, branch, done lock, and a claim with a 14:56Z heartbeat. The interactive session resumed inside that worktree on operator direction. No text names what the resumer does with the claim, so it refreshed `updated:` in place while the file still named the dead session, making a dead claim read fresh to every consult surface for the rest of the closeout. The same shape recurred earlier (the 2026-10-19 takeover of dead session 01a1501c, recorded only in a commit message). The done lock had a sanctioned recovery (`release-orphaned`, holder verified dead); the claim did not.

## Correction (same-day investigate pass)

The conversion step exists: the gateway's arm 3 (`resume_evidence_matches` in `scripts/execution_claim.sh`, plan 2026-10-10-coordination-single-writer-ttl Task 2, landed in f3894756d) lets a new session's `take` take over a foreign claim when the run worktree's manifest names the claim holder as `Session:` and the plan as `Plan:`. It is unreachable in production: the arm greps `^Session: <holder>$`, while every execute-plan manifest on disk (the dead run's and both live peers') writes `session_id: <holder>` and no skill text pins a `Session:` line; only the arm's own fixture in `scripts/test_execution_claim.py` writes `Session:`. So the mismatch is a receipt-to-row key drift between the gateway and the manifest the execute-plan skill writes, and the resume recipe (re-run `take` with the same `--branch` and `--worktree-parent`) is named nowhere a resuming session reads.

## Expected

Arm 3 verifies against the manifest shape the skill actually writes (accept `session_id:` beside `Session:`, or pin the key once in the execute-plan manifest contract and the fixture), with a fixture that writes the real manifest shape; the execute-plan Recovery section names the resume recipe (verify the holder dead through the done lock's holder state, then re-run the pinned `take` invocation, whose arm-3 takeover converts the claim and records the takeover). No manual `session:` rewrite, no new mode.

## Why not fixed now

The fix touches the claim gateway (a guard-bearing path, plan route only) plus the manifest contract and the recovery text; the live witness was closed by hand.

## Refusal-path no-exit analysis

- **Add a sanctioned exit:** the existing `take` command owns existing-claim conversion; `claim` creates a fresh claim and cannot replace it. The planned status provider authorizes conversion only for the exact prior session in terminal state, with completed-run evidence and both existing locks held; missing or unusable provider configuration retains the current refusal. `done-lock release-orphaned` recovers a dead lock holder but does not establish claim-owner status.
- **Remove the false positive:** accepting a live, paused, unresolved, or unknown owner, or incomplete run evidence, can leave two sessions editing the same run. The two recorded dead-owner incidents support exact-ID terminal status and complete parent-owned task/review boundaries before conversion.
- **Simplify the flow:** retain the existing `take` gateway and locks: its per-worktree done-lock covers the recovery evidence, and the repository merge-lock serializes all claim operations. This avoids a manual claim rewrite, a separate conversion mode, or a new lock family while eliminating the unlink/create gap through atomic replacement.

The plan pre-registers the configured exact-ID status-provider check, completed-run boundary, and existing-lock serialization before enabling recovery. It cites the two witnessed incidents, prices a false positive as one refused resume, and sets review on 2027-04-21 with removal if no additional catch occurs by then. A done-lock PID is not treated as proof of session identity.

## Source

- Landing cfb909995; the claim `docs/tmp/execution-claims/done-immediate-commit-single-homing.md` was refreshed at 15:20Z and 15:28Z under the dead session id, then deleted at closeout.
