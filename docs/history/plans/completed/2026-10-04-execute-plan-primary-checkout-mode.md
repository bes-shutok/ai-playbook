# Plan: Declared primary-checkout execution mode for the plan-execution lane

Backlog origin: docs/history/backlog/2026-10-04-execute-plan-primary-checkout-policy.md
Prompt source: docs/history/backlog/PLAN-PROMPTS.md entry `execute-plan-primary-checkout-mode` (frozen 2026-10-04, in-session authoring)
Driving force: simplicity (primary) + automation (secondary)
Plan review record: the staging series docs/reviews/2026-10-04-plan-review-execute-plan-primary-checkout-mode-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- `worktree_policy`: the per-project facts-document key whose closed value set this plan extends; semantics are owned by the single-source Project worktree policy paragraph in the Worktree-first standard (agents/skills/execute-plan/SKILL.md).
- `primary-execution` placement: the new third spelled `worktree_policy` value; it authorizes exactly the plan-execution lane to run in the primary checkout for the declaring project, under the safeguards this plan names.
- Named lanes: the plan lanes the Worktree-first standard governs (the plan-execution lane and the plan-authoring lane).
- Primary-checkout landing class: the landing arm of lifecycle step 4 whose squash executes in the base branch's primary checkout through `scripts/land_squash.sh land` under the acquired merge lock, never a hand-composed squash-and-commit sequence; this plan binds the class as the prohibition of record for primary placements, not an invoked leg.
- Execution claim: the per-run claim file the execute-plan run writes under the resolved tmp directory's `execution-claims/` at the primary checkout.
- Manifest identity block: the session manifest block that records the canonical run checkout (`run_worktree`, `run_branch`), filled when Phase 0 completes.
- Serialization refusal: the fresh-run refusal that stops a new primary-placement execution run while another live claim or recorded witness occupies the primary checkout.
- Base branch: the per-project base branch resolved by the Worktree-first standard's Base-branch resolution rule.
- Transfer-out: lifecycle step 5, the migration of gitignored run artifacts from a run worktree to the primary checkout before worktree deletion.

## Why

A project whose workflow requires work in its primary checkout can declare a primary placement today, but the declaration is ineffective for plan execution: every plan-execution run still reports the isolation conflict and stops for operator direction, so the operator repeats the same direction on every run. A supported, explicitly declared mode keeps the worktree default for every other project while honoring the declaring project's real constraint, and it removes the recurring manual direction the stop forces.

## Outcome

A project that declares `worktree_policy = "primary-execution"` runs its plan-execution lane in its primary checkout, serialized and recorded, instead of stopping.

- The declaring project's execution runs proceed on the primary checkout's recorded branch; the witnessed same-day stop class does not re-fire for declared projects.
- Unconfigured and `worktrees` projects, and the disabling `primary` declaration, keep today's resolutions byte-for-byte.
- A primary placement is serialized (one live primary-placement execution run per project), recorded in the execution claim and the manifest identity block, and stable across resume.
- The landing leg is the primary-checkout landing class under the merge lock; a run already on the base branch records no landing; transfer-out is a no-op by construction.

Gate delta: +1 spelled form and +1 resolution arm in the single-source policy paragraph (the `primary-execution` placement), priced by the refusal-class removal it enables for declared projects (the conflict-and-stop the origin witnesses as ineffective); +1 fresh-run refusal class (the serialization refusal) and +2 stand-down conditions (a non-base current branch at run start; a resume branch mismatch), all refusal-path additions on the fix-class origin carrying one origin-cited no-exit justification: the sanctioned-exit default is impossible because a second concurrent primary run has no other sanctioned checkout to resolve to and a non-base primary HEAD has no landing exit (the landing helper resolves the base from the primary checkout's HEAD and self-squashes into its terminal empty-diff refusal, verified at r1), the false-positive-removal default is impossible because the collisions are the witnessed shared-checkout dirt class the worktree-first standard's own consolidation retired (docs/history/plans/completed/2026-09-28-worktree-first-standard-only-mode.md), and the flow-simplification default is impossible because dropping serialization or the base-branch condition reintroduces exactly those classes, the failures the origin's "interacts with an existing run and claim" and safeguard demands exist to prevent (origin: docs/history/backlog/2026-10-04-execute-plan-primary-checkout-policy.md); +0 new state fields: the placement rides the existing execution-claim body and the existing manifest identity block fields, whose consumer arms (the resume-adopting reads) already exist; a review-layer duty whose violation blocks: none new.

## Assumptions

- assume the authorization takes the form of a third spelled `worktree_policy` value, not a companion facts key; basis: the closed-set validation ("a value outside the spelled forms is treated as unconfigured with a named report") already lives in the single-source paragraph, so one declaration surface keeps placement single-sourced; the log entry's arm 1 names both options and delegates the choice to authoring.
- assume the mode covers the plan-execution lane only; the plan-authoring lane stays worktree-requiring; basis: the entry's own adjacency note ("the witnessed demand is execution-side"), and the authoring lane's review-round and self-landing machinery is worktree-shaped, so widening it would add unowned surface.
- assume a primary-placement run works on the primary checkout's current branch without switching it, records that branch at start, and stands down on a branch mismatch at resume; basis: the witnessed demand is "same-branch execution without a worktree" (origin Evidence), and switching a shared checkout's branch mid-flight is the peer-collision class the standard's consolidation retired.
- assume the mode is valid only when the primary checkout's current branch is the base branch at run start, and every primary-placement run therefore records no landing; basis: `scripts/land_squash.sh` resolves the base branch from the primary checkout's checked-out HEAD and requires HEAD to equal `--expected-tip`, so a non-base HEAD self-squashes into the helper's terminal empty-diff refusal (review round r1 verified this dead-end), and the checkout transition a landing would need reintroduces the peer-collision class this plan's arms forbid; the origin's Expected ("proceed on the selected branch when that mode is valid") invites exactly this validity condition, and the frozen entry's arm-3 safeguard binds as the prohibition of record (never a hand-composed squash-and-commit sequence), not an invoked leg.
- assume the frozen entry's arm-3 prestage-gate clause is dispensed by reference; basis: the Worktree-first standard's lifecycle-step-4 bytes already own the pre-stage freshness gate for every residual primary staging lane, and the primary placement adds no residual staging path of its own (per-task commits are ordinary commits, not landing staging), so restating the clause in the placement resolution would duplicate a live obligation (adjudicated at the r3 fold).
- assume no separate dispatching-payload placement-adoption arm exists; basis: the placement consult resolves the mode fresh from the one facts key at run start, reading the same source a dispatching payload would have recorded, so a separate adoption arm duplicates the resolution for no witnessed failure (the frozen entry's arm 2 extension adjudicated away at the r1 fold).
- assume execution re-derives the policy paragraph's anchors from live bytes before editing; basis: the log entry's adjacency note records the review-cert relaxation census and the monolith extraction both touching execute-plan regions ahead of this plan's likely execution.

Decision points requiring a grill: the declaration form (third value vs companion key) resolved to the third value, source: the log entry's arm-1 adjudication mandate plus the standing loop pre-authorization to accept recommended options, 2026-10-04, affected section: Why and Task 1; the lane scope (execution-only vs authoring-joining) resolved to execution-only, source: the entry's adjacency note "the witnessed demand is execution-side" plus the same standing pre-authorization, 2026-10-04, affected section: Assumptions and Task 1.

## Gist & Examples

TLDR: a declared `primary-execution` project runs its plan-execution lane in the primary checkout under serialization, recording, and the landed landing class, replacing a conflict-and-stop that made the declaration ineffective; why: simplicity, the declaration works as declared, with automation removing the per-run operator repetition.

Before (today): a service repository whose facts carry no `worktree_policy` (or declare `"primary"`) receives an execute-plan run the operator deliberately wants in the primary checkout on the current branch. Phase 0 Step 0.1 consults the policy paragraph, the lane is named and worktree-requiring, no worktree is authorized, and the run stops at the hard gate before Phase 1. The operator repeats the same-branch direction; the run stops again or the operator falls back to the Recovery path, the one sanctioned in-checkout arm, which is scoped to resuming work already sitting in the checkout.

After (this plan): the project declares `worktree_policy = "primary-execution"` in its facts document. The placement consult resolves the plan-execution lane to the primary placement: no worktree is created; the run records the placement (claim line plus identity block, no run worktree) and the checkout's current branch as the run branch; a fresh run refuses to start only while another live claim or recorded witness occupies the primary checkout; the run works on that recorded branch. At start the run verifies the checkout's current branch is the base branch (a non-base branch stands the run down naming the operator remedy, because the landing helper resolves the base from the primary checkout's HEAD and a non-base HEAD self-squashes into its terminal empty-diff refusal); the per-task commits therefore land on the base branch directly and the run records no landing, while the primary-checkout landing class stays the prohibition of record for any residual primary staging. Transfer-out never runs because there is no run worktree, and the plan says so.

Edge cases the design pins down: an unconfigured project keeps stopping the named lanes as today (the witnessed stop stays the resolution for undeclared projects); a `worktrees` project keeps opt-in worktrees; the disabling `primary` declaration keeps the conflict-and-stop for both named lanes; an invalid value keeps the named-report-unconfigured treatment; a concurrent second primary run is refused by the serialization arm instead of colliding on the shared checkout; a resume re-enters the recorded placement and never re-consults into the other mode mid-run; a branch mismatch at resume stands the run down instead of switching the shared checkout's branch or re-recording the switched branch; a run started on a non-base current branch stands down at start naming the operator remedy (check out the base branch or take the worktree lane), the validity condition that keeps every primary-placement commit on the base branch.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every new resolution is stated once, in the single-source policy paragraph, and the consumers (plans Phase 0 consult, done Run placement consult) still resolve their placements by reference with no byte change.
- regressions: the unconfigured, `worktrees`, and disabling-`primary` resolutions, the user-request override ladder, and the invalid-value named report survive verbatim; the pins suite and the shared-body runtime-neutrality test stay green.
- fail-closed validation: each new obligation has a dedicated, distinctive, region-appropriate grep that fails when the obligation is deleted, and the whole Validation block is executed end to end at authoring with its RED-today evidence recorded.

**Done when:**
- The policy paragraph carries the `primary-execution` resolution, the serialization and recording arms, the base-branch validity and no-landing arms, and the transfer-out no-op statement, each exactly once.
- The facts-key table row names the third form in its fallback cell.
- Phase 0 Step 0.1 carries the authorized primary-placement arm with the resume branch-mismatch enforcement point, and the arm's own text declares the recorded primary placement as satisfying the hard gate instead of a created worktree (the hard-gate paragraph itself is untouched by this plan).
- The full Validation block exits 0 on the branch bytes, and the RED-today execution record (first failing gate on the base tree, each vacuous pass) is in the Validation preamble.

**Ship when:**
- The operator re-runs the witnessed same-branch execution request in a declaring project and the run proceeds past placement without the stop; cross-repo, human-owned, not a checklist item.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md` *(partially in scope: the Project worktree policy paragraph, the standard's opening charter sentence, the facts-key configuration table `worktree_policy` row, and Phase 0 Step 0.1 only; every other region of the file is frozen; reject any review finding that touches them)*

**Tests:**
- none new; the mechanical checks are the plan's own Validation Commands block (the 2026-10-02 sibling plan adjudicated prose wiring over an enforcement script for this same policy family).

**Plan-related extension:** implementation and review may change files not listed above when the change is causally related to this plan: a re-keyed pin in scripts/check_maintenance_pins.sh if a prescribed insertion touches a pinned span (update the owning pin in the same edit per the log entry's arm 4; when this fires, check 6's expected changed-file set widens in the same fold and the plan bytes record the widened set before certification), or a consumer-surface sentence that a validation arm proves stale.

**Out of scope; reject unless plan-related:**
- `scripts/land_squash.sh` and `scripts/prestage_freshness_gate.py`; reason: consumed as-is, the mode reuses the landed landing class and gate rather than extending them.
- `agents/skills/plans/SKILL.md` and `agents/skills/done/SKILL.md`; reason: single-source consumers that keep referencing the one paragraph; validation pins their unchanged consult counts instead of editing them.
- the Recovery path's in-checkout exception; reason: scoped to resuming inline work already in the primary checkout; widening it conflates recovery with placement (log entry rejected alternative).
- the monolith-extraction regions of execute-plan SKILL.md; reason: a separate frozen log entry sequencing-gated behind the relaxation plan's execution.

## Validation Commands

Authoring-time records (preamble, updated as the loop lands receipts):

- RED-today evidence: executed 2026-10-04 against the base bytes at main 066d3095 (the wt-epcm authoring worktree's tree, tip-identical to main, re-derived at run time): checks 0 through 3b all green (public hygiene `OUTCOME: pass`; em-dash added-lines silent; pins `all hold`; shared-body test `OK`, 1 test), then the block failed at its first new-span arm, `check 4: primary-execution declaration count` (count 0, exit 1): the prescribed bytes are absent from the base tree, so the gate is RED-today and flips GREEN exactly when Task 1 lands. No vacuous passes: every swept path exists at the base tree.
- Rule 22 mechanical audit plus rule 44 extraction proof: executed 2026-10-04; the two prescribed text-fenced insertion blocks and the fallback-cell text were extracted from this plan's own bytes by a fenced-block parser (never re-typed), the pin/text contract verified (each check 4 grep literal occurs exactly once in its prescribed source span), the spans applied to a scratch copy of the target file at the named seams (both named tails verified surviving), and every check 4 count arm re-run GREEN on the scratch tree (all 15 count arms plus the land_squash and prestage reference arms); the flip probe then removed the serialization sentence from the scratch tree and the serialization arm read 0 (RED polarity). The audit corrected two authoring-time gate defects before any review round: the `primary-execution` whole-file surface count is 4 (declaration value, placement-adjective use, Step 0.1 arm reference, facts-key cell), not the 2 first drafted, and check 3b runs the direct-file unittest form because the stdlib-only host has no pytest module.
- Round r1 fold receipts: all nine staged findings folded (the 4 blocking: F1 line-count-vs-occurrence arm, F2 stage-unrunnable interim verification, F3 non-base landing dead-end, F4 invalid gate-delta payment; the 5 non-blocking folded by consequence); the surface-count arm moved to the occurrence-count form, the base-branch validity replaced the non-base landing leg, the gate delta's recording-field payment moved to the existing-field route, the resume-mismatch stand-down gained its Step 0.1 enforcement point, and the Done-when satisfaction wording was aligned with the prescribed text; the mechanical audit re-runs on the folded spans before round 2.
- Round r2 fold receipts: the one blocking finding (r2 F1: the consumer-leak arm's multi-file `grep -c` emits `file:count` pairs, so the `-eq 0` test could never pass) was split into the two single-file arms; the two non-blocking Lows were folded by consequence (Done-when subject aligned to the arm-declares-satisfaction shape with the hard-gate paragraph explicitly untouched; the operator remedy spelled inside both prescribed stand-down spans so the skill bytes carry it, with the verify-arm grep literal updated to the new span prefix); the mechanical audit re-runs on the folded spans before round 3.
- Round r3 fold receipts: the closed-set contradiction (r3 F1: the paragraph's own "outside the two spelled forms" sentence would have classified the new third form as unconfigured) closed by a third prescribed edit amending "two" to "three" with the named tail preserved and two new count arms; the unstated execution topology (r3 F2: check 6 unreachable because the plan record itself rides the authoring branch) closed by the sibling plan's landed-record precondition arm plus a topology comment; the frozen entry's arm-3 prestage clause (r3 F3, non-blocking) adjudicated as dispensed by reference in a new assumption; the mechanical audit re-runs on the folded spans before round 4.
- Round r4 fold receipts: ready=yes zero blocking with two material non-blocking Mediums folded by consequence: the charter-scope contradiction (r4 F1: the standard's opening sentence called the Recovery path "the one sanctioned arm") closed by a prescribed charter amendment naming both sanctioned in-checkout arms with three new validation arms; the unwitnessed seam tails (r4 F2: a mutation probe ate all three named tails with every arm green) closed by three dedicated named-tail survival arms; the mechanical audit re-runs on the folded spans before round 5.
- Round r5 (the configured cap) cap-closure receipts: the round reported ready=no with one blocking finding, re-priced here before closure: the r4 charter fold's fifth `primary-execution` occurrence left the surface-occurrence arm pinned at 4 (r5 F1, testing#count-semantics-mismatch), now `-eq 5` with the charter span added to its diagnostic and both stage expectations restated (3 of final 5 after Task 1, 4 of final 5 after Task 2); the Review Scope editable-region enumeration widened to name the charter sentence (r5 F2, consistency#scope-contradiction); no further panel launches follow the cap; the final round sidecar re-binds to the post-closure bytes with `extensions.cap_closure` declared.

```bash
set -e
# Executor note: run from the repository root. set -e makes the block fail
# closed: the first failing check aborts with its own non-zero status. Each
# byte-level arm carries its own diagnostic. The single-quoted grep literals
# below quote the plan's prescribed spans verbatim; no pattern sweeps the plan
# file itself, so no self-match escape is needed.

# 0) the validated bytes are the branch's bytes
[ -z "$(git status --porcelain -- agents/skills/execute-plan/SKILL.md)" ] || { echo "check 0: validation target dirty against HEAD:"; git status --porcelain -- agents/skills/execute-plan/SKILL.md; exit 1; }

# 1) public hygiene (exit 0 required)
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh

# 2) em-dash gate over the changed bytes against main
bash scripts/check-no-em-dash.sh added-lines --base main

# 3) the full pins suite (exit 0 required)
bash scripts/check_maintenance_pins.sh

# 3b) shared-body runtime neutrality (the paragraph lives in a shared skill body);
#     direct-file unittest form: the stdlib-only host has no pytest module, and
#     running the file directly puts scripts/ on sys.path for its sibling imports
python3 scripts/test_execute_plan_runtime.py -k shared_skill_bodies

# 4) landed bytes: the new resolutions land exactly once each, the preserved
#    sibling resolutions survive, and the key stays single-sourced
[ "$(grep -cF 'worktree_policy = "primary-execution"' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: primary-execution declaration count"; exit 1; }
[ "$(grep -c 'authorizes exactly one named lane, the plan-execution lane, to run in the primary checkout' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: authorized-resolution span"; exit 1; }
[ "$(grep -c 'refuses to start while another live execution claim or recorded witness occupies the primary checkout' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: serialization refusal span"; exit 1; }
[ "$(grep -c 'records that branch at start (in the execution claim and the manifest identity block' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: placement recording span"; exit 1; }
[ "$(grep -c "is valid only when the primary checkout's current branch is the base branch at run start" agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: base-branch validity span"; exit 1; }
[ "$(grep -c 'its per-task commits therefore land on the base branch directly and the run records no landing' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: no-landing span"; exit 1; }
[ "$(grep -c 'stays the prohibition of record, never a hand-composed squash-and-commit sequence in the primary' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: landing prohibition span"; exit 1; }
[ "$(grep -c "verify the checkout's current branch is the base branch and stand down with the remedy named in its stand-down report" agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: base-branch verify arm span"; exit 1; }
[ "$(grep -c "verifies the checkout's current branch still equals the recorded run branch before any recording" agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: resume enforcement span"; exit 1; }
[ "$(grep -c 'transfer-out is a no-op by construction on a primary placement' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: transfer-out no-op span"; exit 1; }
[ "$(grep -c 'Authorized primary-placement arm' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: Step 0.1 arm heading span"; exit 1; }
[ "$(grep -c 'satisfied by the recorded primary placement instead of a created worktree' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: hard-gate satisfaction span"; exit 1; }
[ "$(grep -c 'execution lane authorized in the primary per the policy paragraph' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: facts-key fallback cell span"; exit 1; }
# the surface count is an OCCURRENCE count: two prescribed occurrences share the
# declaration sentence's line, so a line-count form (grep -c) reads 3 and false-fails
[ "$(grep -o 'primary-execution' agents/skills/execute-plan/SKILL.md | wc -l | tr -d ' ')" -eq 5 ] || { echo "check 4: primary-execution surface occurrence count (declaration value + placement-adjective use + charter sanctioned-arms span + Step 0.1 arm reference + facts-key cell)"; exit 1; }
# the charter sentence names both sanctioned in-checkout arms (the r4 F1 amendment)
[ "$(grep -c 'never in the primary checkout by default' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: charter default qualifier missing"; exit 1; }
[ "$(grep -c 'are the sanctioned in-checkout arms' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: charter sanctioned-arms span missing"; exit 1; }
[ "$(grep -c 'is the one sanctioned arm' agents/skills/execute-plan/SKILL.md)" -eq 0 ] || { echo "check 4: stale one-sanctioned-arm charter survived"; exit 1; }
# the closed-set sentence counts its own new form (the r3 F1 amendment)
[ "$(grep -c 'outside the three spelled forms' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: closed-set three-form amendment missing"; exit 1; }
[ "$(grep -c 'outside the two spelled forms' agents/skills/execute-plan/SKILL.md)" -eq 0 ] || { echo "check 4: stale two-form sentence survived"; exit 1; }
# preserved sibling resolutions (regression pins; green on the base tree)
[ "$(grep -c 'the lane requires an isolated checkout the project setting forbids' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: primary conflict clause survived"; exit 1; }
[ "$(grep -c 'treated as unconfigured with a named report, never a silent fallback' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: invalid-value treatment survived"; exit 1; }
[ "$(grep -c 'an explicit user request for a worktree overrides the project policy' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: user-request override survived"; exit 1; }
[ "$(grep -c '^| `worktree_policy` |' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: facts-key row count"; exit 1; }
# consumers stay single-sourced by reference (byte-unchanged)
[ "$(grep -c 'worktree policy' agents/skills/plans/SKILL.md)" -eq 1 ] || { echo "check 4: plans consult count changed"; exit 1; }
[ "$(grep -c 'worktree policy' agents/skills/done/SKILL.md)" -eq 1 ] || { echo "check 4: done consult count changed"; exit 1; }
[ "$(grep -c 'worktree_policy' agents/skills/plans/SKILL.md)" -eq 0 ] && [ "$(grep -c 'worktree_policy' agents/skills/done/SKILL.md)" -eq 0 ] || { echo "check 4: key names must live only in the single-source paragraph"; exit 1; }
[ "$(grep -c 'primary-execution' agents/skills/plans/SKILL.md)" -eq 0 ] || { echo "check 4: mode name leaked into plans"; exit 1; }
[ "$(grep -c 'primary-execution' agents/skills/done/SKILL.md)" -eq 0 ] || { echo "check 4: mode name leaked into done"; exit 1; }
# named-tail survival (mechanical witnesses for the seam tails; green on the base tree)
[ "$(grep -c 'a project that opts into worktrees allows ad-hoc worktrees' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: insertion-1 named tail eaten"; exit 1; }
[ "$(grep -cF '**Hard gate:** Do not proceed to Phase 1 until the worktree setup is complete' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: insertion-2 named tail eaten"; exit 1; }
[ "$(grep -c ', or an unresolvable root, is treated as unconfigured with a named report, never a silent fallback.' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: closed-set amendment named tail eaten"; exit 1; }
# landing helpers the mode consumes still exist and are still referenced
[ "$(grep -c 'scripts/land_squash.sh' agents/skills/execute-plan/SKILL.md)" -ge 1 ] || { echo "check 4: land_squash reference lost"; exit 1; }
[ "$(grep -c 'scripts/prestage_freshness_gate.py' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: prestage gate reference drift"; exit 1; }
# the paragraph stays the first thing in the standard (order anchor)
[ "$(grep -bo 'Project worktree policy' agents/skills/execute-plan/SKILL.md | head -1 | cut -d: -f1)" -lt "$(grep -boF '1. **Create the worktree.**' agents/skills/execute-plan/SKILL.md | head -1 | cut -d: -f1)" ] || { echo "check 4: policy paragraph not before step 1"; exit 1; }

# 5) structural gate: the readiness validator's pre-round mode over the plan bytes
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-04-execute-plan-primary-checkout-mode.md

# 6) changed-file scope: main is an ancestor of the execution branch tip, and
#    the branch differs from main in exactly the one skill file. Execution
#    topology: the accepted plan record is already landed on main when execution
#    runs (this authoring landing precedes execution on a fresh branch), so the
#    plan file itself is not in the diff; the pin re-key extension, when it
#    fires, widens this expected set in the same fold and re-certifies before
#    landing
[ "$(git diff --name-only main -- docs/history/plans/2026-10-04-execute-plan-primary-checkout-mode.md | wc -l | tr -d ' ')" -eq 0 ] || { echo "check 6: plan record not yet on main; land the accepted plan record first (a check-6 failure listing only docs/ entries means this landing commit is missing)"; exit 1; }
[ "$(git rev-parse main)" = "$(git merge-base main HEAD)" ] || { echo "main is not an ancestor of the execution branch tip"; exit 1; }
[ "$(git diff --name-only main | LC_ALL=C sort)" = "agents/skills/execute-plan/SKILL.md" ] || { echo "unexpected changed-file set against main:"; git diff --name-only main; exit 1; }
```

### Task 1: the single-source policy paragraph carries the declared primary-execution placement

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `grep -cF 'worktree_policy = "primary-execution"' agents/skills/execute-plan/SKILL.md` and the Task 1 check-4 arms; covers the declaration, authorized-resolution, serialization, recording, base-branch-validity, no-landing, prohibition, transfer-out, charter-amendment, and closed-set-amendment criteria.

Prescribed insertion (into the Project worktree policy paragraph, immediately after the sentence ending "instead of creating a worktree or silently degrading;"; the following text beginning "a project that opts into worktrees" is the named tail and must survive the replacement verbatim):

```text
a project whose facts explicitly declare `worktree_policy = "primary-execution"` runs ordinary work in the primary checkout and authorizes exactly one named lane, the plan-execution lane, to run in the primary checkout for that project: the placement consult resolves the execution lane's placement to the primary checkout instead of the conflict-and-stop resolution, and every other named lane keeps its worktree-requiring resolution unchanged; a primary-execution placement is serialized, so a fresh execution run in the primary checkout refuses to start while another live execution claim or recorded witness occupies the primary checkout (the same foreign-claim conjunct the provisioned-worktree adoption rule applies), and a resumed run adopts the recorded placement and never re-consults into the other mode mid-run; a primary-placement execution run works on the primary checkout's current branch and records that branch at start (in the execution claim and the manifest identity block, the primary placement recorded as no run worktree), standing down on a branch mismatch at resume instead of switching the shared checkout's branch; a primary-placement execution run is valid only when the primary checkout's current branch is the base branch at run start, and a run finding a non-base current branch stands down with the remedy named in its stand-down report (check out the base branch or take the worktree lane for this run) instead of switching the shared checkout's branch; its per-task commits therefore land on the base branch directly and the run records no landing, while the primary-checkout landing class (lifecycle step 4) stays the prohibition of record, never a hand-composed squash-and-commit sequence in the primary; transfer-out is a no-op by construction on a primary placement (there is no run worktree), and the worker-layer dirty-worktree gates are untouched;
```

Third prescribed edit (the standard's opening charter sentence): in the sentence beginning "Every plan-authoring and plan-execution run works inside an ad-hoc worktree, never in the primary checkout", replace the semicolon-joined span "never in the primary checkout; the standard governs fresh run work (the Recovery path's in-checkout exception over work already sitting in the primary checkout is the one sanctioned arm)" with "never in the primary checkout by default; the standard governs fresh run work (the Recovery path's in-checkout exception over work already sitting in the primary checkout and an explicitly declared project's authorized primary-execution placement, the Project worktree policy paragraph's resolution for its declaring project, are the sanctioned in-checkout arms)"; the charter no longer contradicts the placement the paragraph authorizes.

Fourth prescribed edit (the paragraph's own closed-set sentence): in the sentence beginning "a `worktree_policy` value outside the two spelled forms", replace the word "two" with "three"; the named tail ", or an unresolvable root, is treated as unconfigured with a named report, never a silent fallback." survives the replacement verbatim, so the paragraph's invalid-value treatment classifies its own new form instead of contradicting it.

Fifth prescribed edit (the facts-key configuration table `worktree_policy` row): extend the fallback cell `ordinary work: primary; named lanes: this standard` to read `ordinary work: primary; named lanes: this standard; primary-execution: execution lane authorized in the primary per the policy paragraph`, preserving the row's leading cells and trailing pipe.

- [x] Apply the prescribed insertion at the named seam; verify the named tail text survives verbatim (executed 2026-10-04; tail arm GREEN) [class: IMPLEMENTATION_REQUIRED]
- [x] Apply the charter-sentence amendment (executed 2026-10-04; order-anchor and boundary arms GREEN) [class: IMPLEMENTATION_REQUIRED]
- [x] Apply the closed-set sentence amendment ("two" to "three") (executed 2026-10-04; named-tail arm GREEN) [class: IMPLEMENTATION_REQUIRED]
- [x] Apply the facts-key row cell extension (executed 2026-10-04; fallback-cell arm GREEN) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → Task 1 stage-scoped arms GREEN (executed 2026-10-04; re-verified GREEN post-Task-2 in the full block) (the insertion-span arms through the facts-cell arm, the surface-occurrence count reading 4 of its final 5 by occurrence semantics (the plan's r5 restatement carried line-count numbers; corrected at exec review r1), and the preserved-sibling arms still GREEN); the Task 2 and full-block arms are not runnable at this stage (their spans do not exist yet) and stay with Tasks 2 and 3 [class: REPOSITORY_TEST]
- [x] Commit: `fix: authorize declared primary-execution placement in the single-source policy` (a8b653f6 post-rebase) [class: IMPLEMENTATION_REQUIRED]

### Task 2: Phase 0 run setup records and serializes the authorized placement

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `grep -c 'Authorized primary-placement arm' agents/skills/execute-plan/SKILL.md` and the Task 2 check-4 arms; covers the Step 0.1 arm and hard-gate satisfaction criteria.

Prescribed insertion (into Phase 0 Step 0.1, immediately after the Already-provisioned recognition arm paragraph and before the paragraph beginning "**Hard gate:** Do not proceed to Phase 1"; that hard-gate paragraph is the named tail and must survive verbatim):

```text
Authorized primary-placement arm: when the project worktree policy consult resolves the plan-execution lane to a primary placement (the primary-execution declaration), skip worktree creation: verify the checkout's current branch is the base branch and stand down with the remedy named in its stand-down report (check out the base branch or take the worktree lane for this run) when it is not; record the placement in the execution claim body and the manifest identity block (run_worktree carrying the no-worktree primary form, run_branch the verified branch), refuse to start while another live execution claim or recorded witness occupies the primary checkout per the policy paragraph's serialization arm, and treat the placement half of run setup as complete once the placement is recorded and the serialization check passes; a resume of a recorded primary placement verifies the checkout's current branch still equals the recorded run branch before any recording and stands down on a mismatch instead of re-recording the switched branch; the hard gate below is satisfied by the recorded primary placement instead of a created worktree, and the transfer-in step is vacuous because the run already sits in the checkout that holds the facts file.
```

- [x] Apply the prescribed insertion at the named seam; verify the named hard-gate paragraph survives verbatim (executed 2026-10-04; hard-gate tail arm GREEN) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → Task 2 stage-scoped arms GREEN with the surface count at 4 of 5 (executed 2026-10-04) (the arm-heading, base-branch-verify, resume-enforcement, and hard-gate-satisfaction arms) and the surface-occurrence count now reading 5 of its final 5 by occurrence semantics (corrected at exec review r1): re-run the Task 1 and Task 2 count arms [class: REPOSITORY_TEST]
- [x] Commit: `fix: record and serialize the authorized primary placement at run setup` (da961d81 post-rebase) [class: IMPLEMENTATION_REQUIRED]

### Task 3: full validation block end to end (verification only)

Files:
- none (read-only verification)

Evidence:
- the whole Validation Commands block, run end to end from the repository root; covers the Done-when block exit, the RED-today flip, and the changed-file scope.

- [x] Run the whole Validation Commands block → exit 0 on the branch bytes (executed 2026-10-04 after one rebase over peer b0b0228a; inputs per UL#468 copied in) [class: REPOSITORY_TEST]
- [x] Flip probe: the serialization arm run directly on the probe tree (the whole block cannot run on a dirty tree: check 0 refuses) → RED as expected naming the serialization refusal span; restored, tree clean, full block re-run exit 0 [class: REPOSITORY_TEST]
- [x] Record the RED-today and mechanical-audit receipts in the Validation preamble (verified present; authoring receipts intact) [class: REPOSITORY_TEST]

## Residual findings (cap closure)

Cap round: r5 (the configured cap of five). Both staged findings of the cap round carried their fixes into the plan bytes before closure; no residual carries forward.

- testing#count-semantics-mismatch (r5 F1, blocking): disposition folded; the surface-occurrence arm re-priced to 5 with the charter span in its diagnostic and both stage expectations restated.
- consistency#scope-contradiction (r5 F2, non-blocking): disposition folded; the Review Scope editable-region enumeration now names the standard's opening charter sentence.

## Disposition

Executed 2026-10-04 from worktree ai-playbook-wt-epcmx (branch plan-epcm-exec, rebased over peer b0b0228a). Task 1 landed as a8b653f6 (policy-paragraph insertion at the named seam, charter amendment, closed-set two-to-three amendment, facts-key cell extension; all named tails survive verbatim). Task 2 landed as da961d81 (Authorized primary-placement arm inserted before the hard-gate paragraph). Full Validation Commands block exit 0 (checks 0-6; gitignored inputs copied in per UL#468; one rebase over peer b0b0228a mid-run). Flip probe: the serialization arm run directly on the probe tree (check 0 refuses a dirty tree, so the whole block cannot run there) read RED as expected; restored clean and the full block re-ran exit 0. Receipts commit f9dbb84a. Exec review r1 ready=yes zero blocking; 2 Low dispositioned (check-6-at-HEAD receipts boundary adjudicated done as the executor's inherent post-verification bookkeeping; receipt unit mismatch corrected to occurrence semantics). Origin row folded with this landing; the frozen prompt-log entry was already pruned at the authoring landing (553f2f8c).
