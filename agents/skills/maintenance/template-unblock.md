# Template: parked-dependency unblock child (execution-blueprint family)

Extracted module of the maintenance prompt-templates file (agents/skills/maintenance/prompt-templates.md); moved 2026-10-10 by plan docs/history/plans/2026-10-10-maintenance-skill-size-refactor.md Task 4; the dispatched child loads this file plus agents/skills/maintenance/duties-core.md, nothing else.
## Parked-dependency unblock child (execution-blueprint family)

The deciding turn schedules this payload when Step 3 D1 selects the parked-dependency unblock dispatch (an actionable `parked_dependencies` entry). The dispatch target is `"<plan path> (unblock <blocked_on>)"`, so the execution-claim check's plan-slug keying resolves against the leading plan path before " (unblock". The payload carries the overlay-pinned execution markers, so the Step 2 widened arm classifies it as an execution payload. The done-lock, label, and gate literals are pinned and paraphrased here, never quoted. The fenced body:

```
<prompt for the parked-dependency unblock session>
You are an unattended scheduled session in the repository at {REPO_ROOT}; the chaining
prohibition of the execution blueprint applies scoped to the duties this payload actually
carries: the re-arm duty below is carried in recipe-delegating form and the single
successor-dispatch duty is this unblock child's own queue-prepend plus re-dispatch
(no further chaining); the user has pre-authorized
everything below: never block on questions, decide and proceed; never push to origin.

FIRST ACTION, before any gate or phase: restore the maintenance loop parent state-first, without listing first, per the recipe in
agents/skills/maintenance/zcode.md ("Recurring automation recipe"), following that recipe's full decision ladder, its HOST CAVEAT, and its
park-path pairing rule; a refused re-arm records the "rearm_note" field per the recipe
and the session continues with its work order below.

PER-EXECUTION WORKTREE: this run works inside its own ad-hoc worktree created per the
Worktree-first standard section in agents/skills/execute-plan/SKILL.md (the duty every
execution payload carries), the primary checkout's gitignored facts file copied in first
(the first copy of the standard's transfer-in step; complete the standard's transfer-in
for the run's other gitignored inputs), landing under the standard's merge-landing-lock
discipline; a failed create stands down writing nothing.

WORK ORDER (the target plan is the serialized plan named by the live ledger entry; the
blocked ref is <blocked_on>, the bare ref name from the entry's blocked_on field):
1. Acquire the execution claim per the normal claim duty (the execution blueprint's
   EXECUTION CLAIM paragraph); the plan slug every slug-keyed surface resolves is the
   target's leading plan path before " (unblock".
2. Verify the <blocked_on> ref resolves (git rev-parse --verify against the local
   namespace first, then the remote namespace; fetch when only the remote form resolves).
3. BEFORE any rebase, check `git worktree list` for a worktree holding the <blocked_on>
   branch checked out: when one exists, take the gate-refusal deferral path below with
   the peer checkout named (a branch another worktree holds is never moved: a forced
   ref update would succeed where a branch update refuses and would corrupt the peer
   worktree's branch underneath it).
4. Otherwise perform the rebase in a temporary worktree detached at the <blocked_on> tip
   (detached rebase onto the current default-branch ref, then one compare-and-swap
   update-ref of the <blocked_on> ref), never by checking the branch out; a refused ref
   update takes the gate-refusal deferral path.
5. Run the branch's own validation gate set (the branch's own tests, checks, and the
   repository's hygiene gates; a dependency branch has no plan-owned gate list, so the
   branch's own gate set and the unblock child's own final gates below are the gate set).
6. Land the branch under the merge landing lock applying the dependency-branch landing
   discipline: verify the squash against the actual pre-landing main (the merge base
   re-read from the default-branch ref at the commit moment, never the branch lineage);
   when a parallel landing is detected between lock acquisition and commit (the
   default-branch ref moved), the landing gate set re-runs against the moved main before
   the landed-bytes verification: the PII and hygiene gates, the peer-byte guard with its
   merge base recomputed from the moved default-branch ref, the gmail-author check, the
   dirt regression gate against the new merge base, and the landed-commit test probing
   the dependency-landing record identity below.
   The landing itself (the rebase onto the current default tip, the squash merge, the gate set
   detached at the current default tip, the pre-swap and post-landing parentage-gate invocations
   and their per-leg refusal routing including the inverse compare-and-swap rollback with its
   do-not-retry disposition, and the compare-and-swap ref update that
   delivers the final squash commit to the default branch) runs per the Worktree arm of the
   execution blueprint's final-merge paragraph in `agents/skills/maintenance/prompt-templates.md`
   - that arm is the only landing arm, and a squash commit made in the checkout holding the
   default branch is prohibited. The default-branch ref's value is captured immediately before
   the squash commit inside the run worktree (the arm consumes it in its pre-swap parentage-gate
   invocation and in the compare-and-swap's refusal-on-tip-movement), the arm's gate invocations
   are routed per its spelled mechanics, and every refusal takes this recipe's deferred-landing
   record path (the arm's four-outcome stops included: the exit-2
   indeterminate arm, the exit-3 tool-error arm, and a parentage-gate run
   with no final `OUTCOME:` line, which the outcome contract reads as tool
   error).
   Dependency-landing record identity (for any deferred-landing record this run writes
   through the execution blueprint's deferred-landing record duty): landed_path must be
   a path the dependency branch itself changes (a path absent from the default branch
   until the landing lands); the record's plan field names the serialized plan path with
   the unblock target recorded in the note; the read-back's content-equality arm compares
   the branch tip's copy of landed_path; a record fill whose landed-commit plus
   content-equality test can pass without the landing is forbidden, so teardown of the
   recorded branch and worktree stays gated on a verified dependency-branch landing.
7. On a verified landing: after the landing's critical section, reconcile live checkouts of the base branch per the post-landing reconciliation implementation in the Worktree-first standard section of agents/skills/execute-plan/SKILL.md (fast-forward plus verified completion, named-block refusal, stale-witness restore-and-record), then record the landing's squash commit sha as the entry's
   "landed_as" in its own targeted edit FIRST (the sha must be durably observable before
   any clear, so the survey arm's ancestry resolution can fire when the later clear write
   is lost), then clear the ledger entry in a second targeted edit, and queue-prepend the
   serialized plan to "execution_queue" (prepend only when it is not already queued),
   then dispatch or record per the normal successor duty.
8. Re-cert obligation (the drift gate records it by name): the serialized plan's
   implementation resumes only after a fresh focused review-plan round over the
   re-baselined touched surfaces with the digest re-bound.

GATE-REFUSAL DEFERRAL: on any gate refusal (the peer-checkout hold of step 3, a refused
ref update in step 4, or a failing validation gate), the child records the deferral as
its own "children[]" entry outcome write using outcome "failed" with outcome_reason
"deferred" plus the refused gate named in the same field, sets the entry's "deferred_until"
to one cadence period out, and stands down, never landing without the gates. The deferral's
entry update (deferred_until, refusal_count incremented, refused_tip set to the
resolving-ref tip sha at the refusal) is the unblock child's own targeted entry edit.

CLOSING PARK DISCHARGE DUTY, before ending: read the primary checkout's
`.ai-playbook/scheduler-state.json` (explicit-rooted form per the claim duty's precedent; a
cwd-relative edit from the ad-hoc worktree would write a per-worktree gitignored file no
reader reads); when pending_rearm or pending_dispatch is set and this session passes the able-session precheck,
discharge the parked intents in this same session before ending, guard-bound, then clear
the discharged field in one targeted state edit; on primitive absence, leave the park
standing and end.

FINAL STEP, after the report: end this run after the report; the next scheduled payload
starts in a fresh, compacted context, because the dispatch boundary is the compaction boundary
and compaction itself is operator-only.
</prompt>

{REPO_ROOT}: <repository root>
<blocked_on>: <bare-ref-name>
```

