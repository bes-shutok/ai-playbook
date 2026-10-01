# Plan: Parked-dependency unblock template — worktree-complete landing rework

- **Date:** 2026-10-02
- **Workflow:** plans
- **Origin class:** self-serving
- **Class:** fix-class
- **Priority:** high

Backlog origin: docs/history/backlog/2026-10-02-unblock-landing-worktree-rework.md

## Terminology and core concepts

- **The unblock template**: the fenced `## Parked-dependency unblock child (execution-blueprint family)` payload in `agents/skills/maintenance/prompt-templates.md` (its numbered recipe steps 1-8 plus the gate-refusal deferral tail). Its step 6 lands the dependency branch under the merge landing lock.
- **The Worktree arm**: the single landing arm the execution blueprint's final-merge paragraph has spelled since the worktree-complete landing lifecycle plan (`docs/history/plans/completed/2026-10-02-worktree-complete-landing-lifecycle.md`): rebase and squash run inside the run worktree; the checkout holding the default branch receives only the final squash commit through one compare-and-swap ref update; the pre-swap and post-landing parentage-gate invocations, the inverse compare-and-swap rollback with its do-not-retry disposition, the origin-leg keep, and the exit-2 stop are the arm's own spelled mechanics.
- **The retired shape**: the template's current step 6 default path — the squash commit made in the checkout that holds the default branch (`<default-checkout>`), with `UNBLOCK_PRE_TIP` captured there and the bespoke checkout-holding exit routing (the first-parent-shape dispatch and the `reset --merge` rollback arms keyed to a landing commit present on that checkout's HEAD). This is the exact shape the lifecycle plan retired for the main blueprint; the lifecycle plan conformed only the template's one pointer phrase and recorded this rework as a follow-up origin for the filing lane — this plan is that filing's plan.
- **Paraphrase duty**: the template's own header rule — literals the pins suite freezes are paraphrased in prose entries, never quoted.

## Review Scope

Review rounds cover the plan's own bytes plus the touched-surface claims against `agents/skills/maintenance/prompt-templates.md` (the unblock template's step 6 paragraph and the deviation list prepend position), `scripts/check_maintenance_pins.sh` (the unblock pin families and any literal inside the rewrite span), and the no-mirror claim for `agents/skills/maintenance/zcode.md`. Step 4 (the temp-worktree detached rebase), step 7 (post-landing reconcile and the `landed_as` recording), and step 8 (re-cert obligation) are claimed untouched and are in scope as unchanged-surface witnesses, not edit targets.

### Task 1: rework the template's step 6 to the Worktree arm

Files:
- `agents/skills/maintenance/prompt-templates.md`

Replace the step 6 paragraph's retired shape with the Worktree arm as the only landing arm, keeping the dependency-branch specifics:

- The landing (the squash merge and the compare-and-swap ref update) runs per the execution blueprint's Worktree arm — anchored as "the Worktree arm of the execution blueprint's final-merge paragraph in `agents/skills/maintenance/prompt-templates.md`", the same file+section delegation form the template already uses for the post-landing reconciliation implementation — verbatim in delegation form (name the arm; do not re-spell its internals). The default checkout receives only the final squash commit through the arm's compare-and-swap ref update, and a squash commit made in the checkout holding the default branch is prohibited.
- Step 4 is untouched and outside this plan's scope: its rebase keeps its own shape — a temporary worktree detached at the `<blocked_on>` tip, never checking the branch out — which is a different mechanism from the landing's run-worktree squash and is not moved by this plan.
- The pre-landing-tip capture keeps the arm's spelled timing: the default-branch ref's value is captured immediately before the squash commit inside the run worktree (the arm consumes it in the pre-swap parentage-gate invocation and in the compare-and-swap's refusal-on-tip-movement), replacing the `<default-checkout>` capture sentence and the `--new-commit refs/heads/<default>` invocation with the arm's own gate invocations routed per its spelled mechanics.
- Retire the bespoke checkout-holding exit routing (the first-parent-shape dispatch, the `reset --merge` rollback arms that presuppose HEAD carrying the landing commit in the default checkout, and the no-default-checkout fallback sentence — the fallback is vacuous once the Worktree arm is the only arm). Every refusal takes the recipe's existing deferred-landing record path.
- Keep, at the Worktree arm's gate position: the dependency-branch landing-race discipline, opening with its verify-squash clause kept verbatim (verify the squash against the actual pre-landing main — the merge base re-read from the default-branch ref at the commit moment, never the branch lineage), continuing with (the gate set re-runs against a moved default-branch ref between lock acquisition and landing, the peer-byte guard's merge base recomputed from the moved ref, the dirt regression gate against the new merge base, the landed-commit test probing the dependency-landing record identity), and the dependency-landing record identity clause verbatim — both clauses are keyed by existing pins in the pins suite (see Task 3), so their wording may not drift.
- The step 7 post-landing reconcile sentence and the step 8 re-cert obligation are untouched.

- [ ] Apply the six bullets above as the step 6 rewrite [class: IMPLEMENTATION_REQUIRED]

### Task 2: dated deviation-list entry

Files:
- `agents/skills/maintenance/prompt-templates.md`

Prepend one entry to the deviation list, before the `- Worktree-first standard consolidation (2026-09-28` entry: dated 2026-10-02, naming this plan, stating that the unblock template's landing moved to the worktree-complete shape (the retired checkout-holding capture and its exit routing paraphrased as retired, never quoted), and that the recorded residual in the completed worktree-complete landing lifecycle plan is discharged by this plan.

- [ ] Prepend the dated deviation-list entry [class: IMPLEMENTATION_REQUIRED]

### Task 3: pins suite

Files:
- `scripts/check_maintenance_pins.sh`

Re-derived at main b2e63486: exactly two existing pins key literals inside the step 6 span — the `Dependency-landing record identity` presence pin, whose clause Task 1 keeps verbatim, and the `dependency-branch landing-race discipline span` pin whose needle is the verify-squash clause's opening — and both clauses are kept verbatim by Task 1, so the two pins stay green untouched. Note the discipline-span pin is not by itself enforcement for the rewrite: its needle also occurs in the untouched deviation-list history entries, so it stays green even if step 6 drops the clause — which is why Task 3 adds the body-scoped check below. The other unblock pin families (the re-arm sentence counts, the dispatch-slice tag counts, the wrapper count, the worktree-first reference spans) key text outside the landing span, and no pin keys the retired capture or exit-routing literals. Add three pins beside the existing unblock pin family: (a) a wrap-tolerant absence check freezing the retired `<default-checkout>` capture literal absent from the whole file (the suite's normalized/flat absence idiom); (b) a wrap-tolerant presence pin (fixed string under the suite's normalization helper) on the new step 6 delegation sentence naming the Worktree arm with its file+section anchor inside the unblock body; (c) a body-scoped presence check (the suite's existing unblock-body filter plus normalization count) requiring the verify-squash needle exactly once inside the unblock fenced body — the whole-file discipline-span pin cannot fail while the deviation list carries the same needle, so this body-scoped check is the real enforcement that the clause survives the rewrite.

- [ ] Add pins (a), (b), and (c) beside the existing unblock pin family [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the pins suite (scoping any pre-existing unrelated failure per the standing coordination rule) [class: REPOSITORY_TEST]

### Task 4: validation

Files: none (verification only)

Validation checklist (all witness-only, no edits):

- [ ] Run → expect exit 0: the hygiene scan [class: REPOSITORY_TEST]
- [ ] Run → expect exit 0: `python3 scripts/validate_review_staging.py --hard` over the round records [class: REPOSITORY_TEST]
- [ ] Run → expect exit 0: `python3 scripts/plan_readiness.py` on the final bytes [class: REPOSITORY_TEST]

## Assumptions

- The rework is text-only: no script changes, no runtime behavior change outside the payload prose, so no unittest selftest is required; the pins suite is the enforcement witness.
- `agents/skills/maintenance/zcode.md` needs no mirror edit: it carries no unblock-template prose (verified at b2e63486 — its only landing prose is the Merge landing lock bullet, which the lifecycle plan already mirrored).

Decision points requiring a grill: whether delegating to the Worktree arm verbatim (rather than re-spelling its mechanics inside the template) leaves the child session enough context to execute the landing without re-deriving the arm (resolved: the child receives the template block alone, so the new delegation sentence carries the file+section anchor — the template's established bare-reference precedent for family-internal mechanics is the deferred-landing record duty, and this plan upgrades the anchor to the reconcile precedent's file+section form so the reference resolves by reading, not by repo search); whether retiring the no-default-checkout fallback loses a reachable shape (resolved: with the Worktree arm as the only arm, the arm runs regardless of what checkouts exist, so the fallback's condition can no longer arise).
