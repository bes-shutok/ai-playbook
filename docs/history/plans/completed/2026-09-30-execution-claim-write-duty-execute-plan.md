# Plan: Execution-claim write duty in the execute-plan worktree-first flow

Backlog origin: docs/history/backlog/2026-09-30-execution-claim-cross-session-visibility.md
Driving force: reliability
Plan review record: the staging series docs/reviews/2026-09-30-plan-review-execution-claim-write-duty-execute-plan-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Make an in-flight plan execution visible to every other session at plan-selection time, so a peer cannot select and execute a plan that is already being executed.

- An execute-plan run of any provenance (scheduler-dispatched, queue-drain chained, or interactive) writes a claim file in the primary checkout before starting plan work, so the maintenance survey guards and any selecting session see "plan X is in flight" before choosing it.
- A colliding second run fails fast at Phase 0 with the first run's witness (who, where, when) instead of after implementing several tasks.
- A crashed run leaves a stale claim that decays by freshness and is taken over instead of silently reused, so the guard cannot wedge the queue on a dead session; a live-but-silent run (no refresh events for over one cadence period) is takeover-eligible by the same freshness rule, a residual inherited from the P54 protocol this plan deliberately does not touch.

Gate delta: fix-class origin; adds one refusal path (Phase 0 refuses a start on a fresh foreign execution claim) and one checked condition (claim presence at selection). No-exit justification per the origin body's Rejected alternatives: relying on landing-boundary detection is today's witnessed failure (a full execution wasted); committing the machine manifest to a tracked path is rejected because it carries owner-only approval-receipt material; a single global repository lock is rejected because the repository legitimately runs concurrent authoring, review, and execution lanes, so per-plan claim stubs are the minimal exclusion scope. Paying sibling arm: the reader side already exists (the G1e discovery arm's execution-claim check and the P54 EXECUTION CLAIM paragraph in the maintenance prompt template); this plan only wires the missing writer into the flow that was not writing. The three class-default alternatives are unavailable: adding a sanctioned exit is impossible because no sanctioned exit exists today (collision detection lands only at the landing boundary, the witnessed failure); there is no false positive to remove (the primary checkout's claim surface is empty for worktree-first runs, so the guard never fires); simplifying the flow would mean removing either the worktree-first isolation or the payload-side claim duty, both load-bearing.

## Terms

- **Execution claim**: the claim file at the primary checkout's literal `docs/tmp/execution-claims/<plan-slug>.md` (four frontmatter lines: `session:`, `plan:`, `created:`, `updated:`), the cross-session "this plan is in flight" witness the maintenance `G1e` discovery arm reads.
- **Cadence period**: the freshness unit the claim protocol uses (2 hours); a claim whose `updated:` is fresher than one cadence period is fresh, otherwise stale.
- **Procedure of record**: `agents/skills/maintenance/prompt-templates.md` EXECUTION CLAIM paragraph, the single home of the claim write/refresh/takeover/delete mechanics.

## Assumptions

- assume the reader side needs no new machinery; basis: maintenance SKILL.md Step 2 `G1e` discovery arm already reads `docs/tmp/execution-claims/` with the freshness rule, and the P54 EXECUTION CLAIM paragraph defines the writer mechanics; the witnessed 2026-09-30 collision happened because no session executing outside the payload template ever wrote a claim, not because a reader was missing.
- assume the claim file stays gitignored-by-design (it lives under the gitignored `docs/tmp/` in the primary checkout); basis: the origin body's rejected alternative rules out tracking it.
- assume Phase 0 is the right failure boundary for a colliding start; basis: origin proposal point 3 names Phase 0, and Phase 0 is the boundary every provenance passes through.
- assume the origin's stub-field wishlist (run branch, worktree path, start commit) and its dead-root liveness probing are narrowed to the procedure of record's four-line freshness claim; basis: the origin marks its proposal a "minimal shape, for plan authoring to refine", and the procedure of record already owns the liveness and takeover semantics the guards read.
- assume the freshness-decay false-takeover case (a live-but-silent run taken over after one cadence period) stays a P54-protocol residual, out of scope here; basis: the procedure of record is the plan's declared out-of-scope surface, and fixing it belongs to a plan that owns that paragraph.
Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the execute-plan Phase 0 gains the execution-claim write/refresh/delete duty so parallel sessions cannot duplicate a whole plan execution, closing the witnessed 2026-09-30 duplicate run.

Today the claim duty exists only in the scheduler dispatch payload and the queue-drain chaining paragraph; an executor following `agents/skills/execute-plan/SKILL.md` on its own never writes the claim, so the primary checkout's `docs/tmp/execution-claims/` stays empty while a worktree-first run is mid-flight, and a peer session's survey sees the plan as open. After this plan, Phase 0 registers the run in the primary checkout before any plan work, keeps the registration fresh through the run, and deletes it at closeout or an owned stand-down. Example: session A starts a plan in its ad-hoc worktree; its Phase 0 writes `docs/tmp/execution-claims/<slug>.md` in the primary checkout naming session A. Session B's survey later trips its `G1e` discovery arm on that fresh claim and stands down or selects a different plan; if B nevertheless reaches Phase 0 for the same plan, B refuses with A's witness instead of implementing tasks A is already implementing.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every execute-plan provenance (payload-dispatched, chained, interactive) passes through the claim registration exactly once per plan run, and the refusal/takeover branches match the procedure of record's freshness semantics.
- single-source: the skill text references the EXECUTION CLAIM paragraph as procedure of record instead of duplicating its constants, so the two surfaces cannot drift.
- non-regression: the shared-skill runtime-neutrality gate and the existing execute-plan test suite stay green.

**Done when:**
- `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime` exits 0.
- `bash scripts/check-no-em-dash.sh touched` exits 0 over the changed files.
- The validation block below exits 0 against the changed tree.

**Ship when:** no external conditions; this is a repository-local skill fix.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md` (Phase 0 section only; all other sections frozen)
- `agents/skills/maintenance/SKILL.md` (Step 3 D1 bullet only; all other sections frozen)

**Tests:**
- none new; the plan gates itself with existing suites and literal greps.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/prompt-templates.md`; reason: it already owns the claim mechanics and this plan deliberately does not touch them.
- `scripts/test_execute_plan_runtime.py`; reason: no behavioral code changes; only its existing gates are run as validation.

## Validation Commands

```bash
# Run from the repository root.
# 1. The Phase 0 claim registration exists with the procedure-of-record pointer and the refusal path.
# "Execution claim registration" and "deletes the claim at closeout" are literals of the new Phase 0
# paragraph only (the queue-drain paragraph at the bottom of the file uses different wording), as is
# "fresh foreign claim refuses the start" (the queue-drain paragraph says "guard-fire stop" instead),
# so the discriminating gates are 1c, 1d, and 1e; 1a-1b also match the pre-existing queue-drain
# paragraph and are kept as presence pins, not as the discriminating proof.
grep -qF "EXECUTION CLAIM" agents/skills/execute-plan/SKILL.md \
  || { echo "FAIL: Phase 0 execution-claim duty missing"; exit 1; }
grep -qF "docs/tmp/execution-claims/" agents/skills/execute-plan/SKILL.md \
  || { echo "FAIL: claim root literal missing from execute-plan skill"; exit 1; }
grep -qF "fresh foreign claim refuses the start" agents/skills/execute-plan/SKILL.md \
  || { echo "FAIL: refusal path missing"; exit 1; }
grep -qF "Execution claim registration" agents/skills/execute-plan/SKILL.md \
  || { echo "FAIL: Phase 0 registration paragraph missing"; exit 1; }
tr '\n' ' ' < agents/skills/execute-plan/SKILL.md | tr -s ' ' | grep -qF "deletes the claim at closeout" \
  || { echo "FAIL: Phase 0 delete duty missing"; exit 1; }
# 2. The D1 selection-time consult references the execution claim with a D1-specific literal
# (the generic phrase "execution claim" already occurs in Step 1, so it cannot discriminate).
grep -qF "also skips a plan whose fresh execution claim" agents/skills/maintenance/SKILL.md \
  || { echo "FAIL: D1 claim consult missing"; exit 1; }
# 3. Shared-body runtime neutrality stays green (insertions into shared skill bodies).
PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime \
  -k test_shared_skill_bodies_remain_runtime_neutral 2>&1 | grep -q "^OK" \
  || { echo "FAIL: shared-body runtime-neutrality gate RED"; exit 1; }
# 4. The full execute-plan runtime suite stays green.
PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime 2>&1 | grep -q "^OK" \
  || { echo "FAIL: execute-plan runtime suite RED"; exit 1; }
```

### Task 1: Phase 0 execution-claim registration duty

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `grep -qF "fresh foreign claim refuses the start" agents/skills/execute-plan/SKILL.md`; covers the Phase 0 registration and refusal path
- `bash scripts/check-no-em-dash.sh touched`; covers the em-dash gate over changed files

- [x] In the Phase 0 section (`## Phase 0: Run Setup`), immediately after the bolded `**Transfer-in (before the Step 0.5 gate):**` paragraph, add an "Execution claim registration" paragraph: before any plan work, the run writes and thereafter honors the claim file per the EXECUTION CLAIM paragraph in `agents/skills/maintenance/prompt-templates.md`, the procedure of record (that paragraph owns the four frontmatter lines, the create-if-absent noclobber, the refresh cadence across phase boundaries, task completions, and review rounds, and the stale-claim takeover), at the primary checkout's literal `docs/tmp/execution-claims/<plan-slug>.md`, resolving the primary checkout as the first `worktree` entry of `git worktree list --porcelain` (the same resolution the Transfer-in implementation uses) and standing down writing nothing when the primary checkout cannot be resolved; a fresh foreign claim refuses the start (stand down writing nothing); the run deletes the claim at closeout and on an owned stand-down. The paragraph changes no review gate or landing gate; it makes the run's claim visible to the guards the payload template and the queue-drain chaining paragraph already honor. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: `grep -qF "fresh foreign claim refuses the start" agents/skills/execute-plan/SKILL.md` (absent before the edit; verified at authoring 2026-09-30) [class: REPOSITORY_TEST]
- [x] Apply the paragraph edit; refresh the plans skill-gate marker against this worktree root before the write [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Validation Commands block, checks 1a through 1e [class: REPOSITORY_TEST]
 - [x] Commit: `feat: execute-plan phase 0 writes the cross-session execution claim` [class: IMPLEMENTATION_REQUIRED]

### Task 2: D1 selection-time claim consult

Files:
- `agents/skills/maintenance/SKILL.md`

Evidence:
- `grep -qF "also skips a plan whose fresh execution claim" agents/skills/maintenance/SKILL.md`; covers the D1 selection consult sentence

- [x] In the Step 3 D1 bullet, in the sentence introducing the selection skips (the dependency-blocked skip sentence), append one clause: the selection also skips a plan whose fresh execution claim (the `G1e` discovery arm's data, a claim whose `updated:` is fresher than one cadence period naming a foreign session) is present in the primary checkout, the skip recorded in `decision_reason`, with the stale-claim takeover left to the claim protocol rather than the selection. In the same bullet's must-dispatch exemption enumeration (the "guard, quota, dependency, external-gate, rate-pressure, loop-mode, or cycle-gate reason" sentence), add the fresh-execution-claim skip as a sanctioned exemption reason so a claim-only-skipped queue in the guard-reads-before-selection race window is not classified as a dispatch-defect `turn_error`. Keep the sentence in the existing skip chain so no new skip class machinery is added; the clause prices itself as restating the guard's own data at the selection site. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: `grep -cF "also skips a plan whose fresh execution claim" agents/skills/maintenance/SKILL.md` returns 0 before the edit (the generic phrase already occurs once in Step 1, which is why the D1-specific literal is the gate; verified at authoring 2026-09-30) [class: REPOSITORY_TEST]
- [x] Apply the clause edit; refresh the plans skill-gate marker against this worktree root before the write [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Validation Commands block, check 2 [class: REPOSITORY_TEST]
 - [x] Commit: `feat: d1 selection skips a plan with a fresh foreign execution claim` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Full-suite and mechanical gates

Files: none new (verification only)

Evidence:
- `PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime`; covers the full suite and the shared-body gate
- `bash scripts/scan-public-hygiene.sh`; covers the public-hygiene gate over changed files

- [x] Run → expect GREEN: the complete Validation Commands block (checks 1 through 4) [class: REPOSITORY_TEST]
- [x] Run `bash scripts/scan-public-hygiene.sh` from the repository root; expect exit 0 [class: REPOSITORY_TEST]
 - [x] Commit: `test: verify execution-claim duty gates green` [class: IMPLEMENTATION_REQUIRED]

## Completion record (backfill 2026-09-30)

The executing session archived this plan without marking its task checkboxes (archived byte-identical to the authored state; witnessed in the landing that moved it). An after-the-fact verification session re-ran this plan's complete Validation Commands block against current main and every check passed, so the checkboxes above are backfilled as complete. Evidence of record: the plan's own Validation Commands, run 2026-09-30 in the primary checkout at main (execution-claim checks 1-4 green; recovery-baseline checks 1-7 green), plus the landing diffs of the execution commits. The ceremony gap itself is filed as backlog: docs/history/backlog/2026-09-30-execution-ceremony-prevention-witnesses.md.
