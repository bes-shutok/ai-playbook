# Plan: Worktree-first standard as the only sanctioned run mode

> Executed 2026-09-28 in an ad-hoc worktree (Tasks 1-5, five review rounds r1-r6 with one reconciliation pass, zero blocking at exit); backlog origin docs/history/backlog/2026-09-28-worktree-first-standard-only-mode.md folded into this completed plan and deleted at archive time per the promoted-backlog rule (the origin's full scope is this plan's Outcome and tasks; its base-branch user clarification is recorded in Assumptions).

Backlog origin: docs/history/backlog/2026-09-28-worktree-first-standard-only-mode.md
Driving force: simplicity
Plan review record: the staging series docs/reviews/2026-09-28-plan-review-worktree-first-standard-only-mode-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Make the ad-hoc-worktree run shape the single sanctioned mode for every plan-authoring and plan-execution run, expressed as one canonical recipe owned by one skill section.

- One canonical worktree-first recipe (create an ad-hoc worktree on its own branch off the per-project base branch, transfer artifacts in, do the work, squash merge to that base branch, move all run artifacts back to the primary checkout and verify them there, then delete the worktree and branch) lives in one owned section of the execute-plan skill.
- The duplicated per-payload worktree prose in the maintenance child blueprints and the in-checkout branch-setup arms in the plans and execute-plan skills are replaced by references to that recipe; no in-checkout arm remains for authoring or execution.
- Base-branch selection resolves through a per-project default (the project facts document or the owning skill configuration), never a hardcoded repository name in shared prose: a default-branch integration project pins its default branch; a checkout-flow project defaults to the operator's checked-out branch at run start.
- Concurrent authoring and execution runs stop sharing the primary checkout, retiring the witnessed dirt classes the per-payload variants produced: half-landed bytes in checkouts, orphaned worktrees, stranded review sidecars, and checkout collisions between sessions.

## Assumptions

- assume the canonical recipe is owned by a new section in the execute-plan skill (`agents/skills/execute-plan/SKILL.md`); basis: the origin names "execute-plan or maintenance, one owner", and execute-plan already owns the run-lifecycle Phase 0 semantics the plans skill shares by cross-reference; the standing pre-authorization in the dispatching log entry (2026-09-28) accepts the recommended option.
- assume base-branch selection behavior as clarified by the user on 2026-09-28 (recorded in the origin): default-branch integration projects (this repository) pin the default branch even when the run starts from another branch; checkout-flow projects default to the operator's checked-out branch at run start; the default resolves from facts or owning-skill configuration.
- assume the plan adds no new mechanical gate; the recipe replaces paragraphs, and where the blueprints already script worktree creation and artifact verification, those steps are consolidated, not re-gated; basis: origin suggested fix and the dispatching log entry ("deletion-of-prose plan").
- assume the execute-plan runtime contract's worker-worktree gates (dirty-worktree startup semantics, quarantined relaunch, worker worktrees) are a different layer (worker lifecycle, not run branch setup) and stay untouched; basis: survey of `agents/skills/execute-plan/runtime-contract.md` worktree references (all worker-lifecycle concerns, none branch-setup).
- assume review-artifact transfer-out duties already carried by the blueprints (move docs/reviews staging and .stats.json sidecars into the primary checkout and verify them there before worktree deletion) keep their meaning and are consolidated verbatim in meaning, not redesigned; basis: origin observed-versus-expected list.

Decision points requiring a grill: recipe owner = execute-plan skill canonical section; receipt: standing pre-authorization in the PLAN-PROMPTS.md entry worktree-first-standard-only-mode (user direction, 2026-09-28) accepting recommended options; affects Task 1.

## Gist & Examples

TLDR: one canonical ad-hoc-worktree recipe replaces the per-payload worktree prose and every in-checkout branch arm, so authoring and execution runs stop sharing the primary checkout; driving force: simplicity (active elimination of duplicated, drifting prose).

**Before (today):** the worktree lifecycle is carried as long per-payload prose. The maintenance authoring blueprint restates its own creation command and duty sentences; the execution blueprint carries a per-execution worktree paragraph; the plans and execute-plan skills each carry in-checkout branch-setup phases (propose a branch, create it in the checkout, verify) that describe a way of working the standard no longer sanctions. The variants drift: some payloads lack the artifact transfer-in, some lack the transfer-out verification, and every deviation has produced dirt (half-landed bytes, orphaned worktrees, stranded review sidecars, sessions colliding in the primary checkout).

**After (this plan):** a single `## Worktree-first standard` section in the execute-plan skill owns the lifecycle. An authoring payload, an execution run, and the plans skill's Phase 0 all say the same short thing: run inside an ad-hoc worktree created per the worktree-first standard, with the base branch resolved by the per-project rule. A concrete example of the resolution rule: in this repository (a default-branch integration project) an authoring run started from any branch creates its worktree off the default branch, because landings must integrate onto the default branch regardless of the operator's checkout state; in a checkout-flow project the same run bases its worktree on the operator's checked-out branch at run start. Neither rule is written as a repository name in shared prose; the project class comes from the facts document or the owning skill configuration.

**Edge cases that shaped the design:** a worktree creation failure stands the run down without writing anything (fail closed, matching the existing authoring stand-down); the transfer-out step verifies moved artifacts in the primary checkout before the worktree is deleted, so verification failure keeps the worktree and branch (the existing stranding shape); the runtime contract's worker-worktree machinery is deliberately out of scope because it governs worker processes inside a run, not which checkout hosts the run.

## Evaluation Criteria

**Quality dimensions:**
- consolidation completeness: no target file restates the recipe's steps; each entry point carries only a reference plus its own payload-critical literals
- correctness: the canonical section's lifecycle matches the witnessed run shape (creation, transfer-in, work, merge-locked squash landing, transfer-out with verification, deletion, fail-closed stand-downs)
- runtime neutrality: the edited shared skill bodies pass the shared-body runtime-neutrality gate (no tool or runtime specific tokens in the prescribed text)
- maintainability: the pins suite stays green; every pin whose pinned span the consolidation rewrote is updated in the same edit

**Done when:**
- the canonical section exists exactly once in `agents/skills/execute-plan/SKILL.md` and carries the base-branch resolution rule
- the in-checkout branch-setup arms are gone from `agents/skills/execute-plan/SKILL.md` and `agents/skills/plans/SKILL.md`, replaced by references to the canonical section
- the maintenance child blueprints reference the canonical section and keep only their payload-critical literals; the pins suite exits 0
- the shared-body runtime-neutrality gate, the no-em-dash scan over touched lines, and the public hygiene scan all exit 0
- `scripts/plan_readiness.py` exits 0 on the final plan bytes

**Ship when:**
- consumer repositories that vendor these skills pick the consolidated bodies up on their next sync (prose only; no deploy step in this repository)

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md` (canonical section *(new within the file)*; Phase 0 rewrite)
- `agents/skills/plans/SKILL.md` (Phase 0 rewrite)
- `agents/skills/maintenance/prompt-templates.md` (payload prose replacement)
- `scripts/check_maintenance_pins.sh` (pin updates riding the consolidation)

**Tests:**
- none *(the plan adds no test files; the verification obligations run existing gates: the pins suite, the shared-body runtime-neutrality test, the no-em-dash and hygiene scanners, and the readiness validator)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. In particular, references to the replaced prose shapes in `agents/skills/maintenance/SKILL.md`, `agents/skills/maintenance/zcode.md`, and `README.md` are in scope where the consolidation would leave them dangling, with any owning pin updated in the same edit. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/runtime-contract.md`; reason: worker-lifecycle layer (dirty-worktree gates, quarantine, worker worktrees), not run branch setup
- `agents/skills/execute-plan/subagent-prompts.md`, `agents/skills/execute-plan/agent-logs.md`; reason: worker prompt and log surfaces, not run entry points
- any new script or gate under `scripts/`; reason: the plan consolidates prose and must not add a validation layer

## Validation Commands

Validation preamble (authoring-time execution record, per the plans skill's rule 29 and rule 19 duties): the block below was executed against the pre-implementation tree before the first review round. Because the block is fail-fast, the gates were executed individually to record each one's outcome: G1 FAILED (exit 1: the canonical section does not exist yet, so the exactly-once count reads 0; a presence gate over an absent span fails, it does not pass vacuously) and G2 FAILED for the same absent-span reason; all six removal probes (G3 probes 1-3 and G4 probes 1-3) FIRED RED on the current bytes (every target span exists today), and each probe was also verified in the opposite direction against a stripped temp copy (span removed, probe passes), so both the bypass and the over-blocking directions are exercised; G5 exited 0 (pins suite green pre-consolidation, the baseline the re-pin task must restore); G6 passed with the test virtualenv interpreter (1 passed, 426 deselected). Rule 29 authoring outcomes on the drafted plan bytes: the no-em-dash file scan exited 0; the public hygiene scan exited 0; the readiness pre-round gate exited 0 after one classification-tag fix (the Task 5 commit item initially carried no class tag). Review correction record: round 2 caught a transcription inversion in the original G3 probe 1 (found-as-pass); the polarity was corrected and the both-directions verification above re-executed post-fix, so the fired-RED claims in this preamble are post-fix measurements, not the original transcription's behavior. Simulate the swapped shape before trusting any order-sensitive gate.

```bash
REPO="$(git rev-parse --show-toplevel)"

# G1: the canonical section exists exactly once in the owning skill
test "$(grep -c '^## Worktree-first standard' "$REPO/agents/skills/execute-plan/SKILL.md")" -eq 1 \
  || { echo "FAIL G1: canonical section missing or duplicated"; exit 1; }

# G2: the base-branch resolution rule lives inside the canonical section (region-scoped; probe literal is unique to the rule paragraph, not the lifecycle steps)
awk '/^## Worktree-first standard/{f=1; next} /^## /{if (f) exit} f' \
  "$REPO/agents/skills/execute-plan/SKILL.md" | grep -qF 'never a hardcoded repository name' \
  || { echo "FAIL G2: base-branch resolution rule missing from the canonical section"; exit 1; }

# G3: the in-checkout branch arms are gone from execute-plan (three-way polarity: only rc 1 passes each probe)
rc=0; grep -q '^### Step 0.1a: Definitive branch match' "$REPO/agents/skills/execute-plan/SKILL.md"; rc=$?
if [ "$rc" -ge 2 ]; then echo "FAIL G3: probe tool error (rc $rc)"; exit 1; fi
if [ "$rc" -eq 0 ]; then echo "FAIL G3: in-checkout branch-match arm still present"; exit 1; fi
rc=0; grep -qF 'git checkout -b' "$REPO/agents/skills/execute-plan/SKILL.md"; rc=$?
if [ "$rc" -ge 2 ]; then echo "FAIL G3: probe tool error on checkout probe (rc $rc)"; exit 1; fi
if [ "$rc" -eq 0 ]; then echo "FAIL G3: in-checkout branch-create recipe still present"; exit 1; fi
rc=0; grep -qiF 'known, tracked branch' "$REPO/agents/skills/execute-plan/SKILL.md"; rc=$?
if [ "$rc" -ge 2 ]; then echo "FAIL G3: probe tool error on anti-pattern probe (rc $rc)"; exit 1; fi
if [ "$rc" -eq 0 ]; then echo "FAIL G3: in-checkout anti-pattern row still present"; exit 1; fi

# G4: the in-checkout branch arms are gone from plans (three-way polarity: only rc 1 passes each probe)
rc=0; grep -qF 'git checkout -b "$BRANCH_NAME"' "$REPO/agents/skills/plans/SKILL.md"; rc=$?
if [ "$rc" -ge 2 ]; then echo "FAIL G4: probe tool error (rc $rc)"; exit 1; fi
if [ "$rc" -eq 0 ]; then echo "FAIL G4: plans in-checkout branch-create recipe still present"; exit 1; fi
rc=0; grep -qF 'Automatic path from clean trunk (fail-closed)' "$REPO/agents/skills/plans/SKILL.md"; rc=$?
if [ "$rc" -ge 2 ]; then echo "FAIL G4: probe tool error on truth-table probe (rc $rc)"; exit 1; fi
if [ "$rc" -eq 0 ]; then echo "FAIL G4: plans automatic-path truth table still present"; exit 1; fi
rc=0; grep -qF 'Verify branch state' "$REPO/agents/skills/plans/SKILL.md"; rc=$?
if [ "$rc" -ge 2 ]; then echo "FAIL G4: probe tool error on verify-step probe (rc $rc)"; exit 1; fi
if [ "$rc" -eq 0 ]; then echo "FAIL G4: plans in-checkout verify step still present"; exit 1; fi

# G5: the maintenance pins suite is green after the consolidation (owns the exact payload-span pins)
bash "$REPO/scripts/check_maintenance_pins.sh" >/dev/null \
  || { echo "FAIL G5: maintenance pins suite red after consolidation"; exit 1; }

# G6: the edited shared skill bodies stay runtime-neutral (run with the
# repository's test interpreter: the project test virtualenv's python when
# plain python3 lacks pytest, resolved per the executing environment)
python3 -m pytest "$REPO/scripts/test_execute_plan_runtime.py" -k shared_skill_bodies -q \
  || { echo "FAIL G6: shared skill body carries a forbidden term"; exit 1; }

# G7: no em-dash in the run's added lines (base branch derived per the canonical section's per-project rule, never hardcoded)
BASE_BRANCH="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')"
[ -n "$BASE_BRANCH" ] || { echo "FAIL G7: cannot resolve the base branch; resolve it per the canonical section's per-project rule and set BASE_BRANCH"; exit 1; }
bash "$REPO/scripts/check-no-em-dash.sh" added-lines --base "$BASE_BRANCH" \
  || { echo "FAIL G7: em-dash in added lines"; exit 1; }

# G8: public hygiene scan over the repository
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" \
  || { echo "FAIL G8: hygiene scan hit"; exit 1; }

# G9: readiness validator over the final plan bytes
( cd "$REPO" && python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-09-28-worktree-first-standard-only-mode.md ) \
  || { echo "FAIL G9: readiness pre-round structural gate"; exit 1; }
```

### Task 1: Canonical worktree-first section in the execute-plan skill

Files:
- `agents/skills/execute-plan/SKILL.md`

- [x] Add a `## Worktree-first standard` section to `agents/skills/execute-plan/SKILL.md`, placed before the Phase 0 section, carrying the canonical lifecycle in imperative steps: (1) create an ad-hoc worktree on its own branch off the per-project base branch; (2) transfer the run's gitignored input artifacts in (the project facts file and any other gitignored inputs the run needs); (3) do the work inside the worktree on its own branch; (4) land the result as a squash merge to the base branch under the repository's merge-landing-lock discipline; (5) move all run artifacts (review staging documents, stats sidecars, telemetry) back to the primary checkout and verify them present there; (6) delete the worktree and its branch only after that verification. State the fail-closed stand-downs: a worktree creation failure stands the run down without writing anything; a transfer-out verification failure keeps the worktree and branch and reports the stranding. [class: IMPLEMENTATION_REQUIRED]
- [x] Encode the base-branch resolution rule inside that section: the base is a per-project default resolved from the project facts document or the owning skill configuration, never a hardcoded repository name in shared prose; a default-branch integration project pins its default branch even when the run starts from another branch; a checkout-flow project defaults to the operator's checked-out branch at run start. [class: IMPLEMENTATION_REQUIRED]
- [x] State the reference contract in that section: the plans skill's plan-creation phase and the maintenance child blueprints run under this standard and must not restate the lifecycle steps in their own bodies; each carries only its payload-critical literals (claim directory, facts transfer-in, review-artifact transfer-out). [class: IMPLEMENTATION_REQUIRED]
- [x] Run the shared-body runtime-neutrality gate over the edited file; expect GREEN (`python3 -m pytest scripts/test_execute_plan_runtime.py -k shared_skill_bodies -q`). [class: REPOSITORY_TEST]

### Task 2: execute-plan Phase 0 becomes the worktree-first run setup

Files:
- `agents/skills/execute-plan/SKILL.md`

- [x] Replace the in-checkout branch-setup steps (the definitive-match, plausible-match, and propose-creation steps with their in-checkout branch creation and verification recipes) with a worktree-first run setup: the run creates its ad-hoc worktree per the `## Worktree-first standard` section, the worktree's own branch being the Phase 0 dedicated branch, and the hard gate keeps its shape (do not proceed to Phase 1 until the worktree setup is complete; a creation failure stands the run down). [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the invocation-detection gate and the session bootstrap step byte-compatible in behavior; only the branch-setup interior is replaced. [class: IMPLEMENTATION_REQUIRED]
- [x] Disposition the two existing operational recipes that overlap the canonical lifecycle instead of leaving competing prose copies: fold the Step 0.4 Linked-worktree bootstrap (with its unlanded-plan cherry-pick remedy) in as the canonical section's named transfer-in implementation, and fold the Phase 5 ad-hoc-worktree closeout (with its tracked-dirt inversion check and worktree closeout migration script) in as the named transfer-out-and-deletion implementation, keeping their mechanical specifics and cross-referencing them from the canonical section so the lifecycle has one normative home and one operational home; any pinned span reworded by this fold updates its owning pin in the same edit per Task 4's duty. [class: IMPLEMENTATION_REQUIRED]
- [x] Sweep the skill body for any remaining in-checkout branch-setup alternative for authoring or execution runs and remove or re-point each hit to the canonical section; the sweep explicitly covers the anti-pattern table row asserting work must happen on a known, tracked branch (re-point it to the worktree-first setup) and every branch-setup cross-reference outside the Phase 0 region. [class: IMPLEMENTATION_REQUIRED]

### Task 3: plans Phase 0 becomes the authoring worktree-first setup

Files:
- `agents/skills/plans/SKILL.md`

- [x] Replace the in-checkout Phase 0 branch setup (the propose, create, and verify steps with the automatic-path truth table and the in-checkout `git checkout -b` recipe) with the authoring worktree-first setup referencing the canonical section: create the ad-hoc worktree off the per-project base branch, transfer the facts document in, key plan-file writes to the worktree root (the skill-gate marker recipe's write-target derivation), and stand down without writing anything when worktree creation fails. Keep the Phase 1 requirements gates untouched. [class: IMPLEMENTATION_REQUIRED]
- [x] Rewrite the create-vs-update rule in the skill's opening block so the worktree-first setup runs for update and completion authoring sessions too: Phase 0's worktree setup is not skipped for plan updates or completion (only Phase 1's requirements discovery keeps its create-only scoping), so no authoring path retains a standing in-checkout arm. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the branch-agnostic plan-content rule (session constraints are not plan constraints) fully intact, and sweep the rewritten section of any wording that instructs execution to stay on a named branch or forbids branch creation. [class: REPOSITORY_TEST]
- [x] Sweep the plans skill body outside the Phase 0 region for branch-setup cross-references and re-point each hit to the canonical worktree-first section, explicitly dispositioning the skill-relationship sentence asserting shared Phase 0 branch-setup semantics with branch reuse ("reuses an existing feature branch when appropriate") and create-only scoping: that sentence must name the worktree-first standard, drop the branch-reuse claim, and drop the create-only scoping claim now that the folded rule runs the worktree setup for update and completion authoring too. [class: IMPLEMENTATION_REQUIRED]

### Task 4: maintenance payload prose consolidation

Files:
- `agents/skills/maintenance/prompt-templates.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`

- [x] Replace the authoring blueprint's worktree duty sentence set, the execution blueprint's per-execution worktree paragraph, and the unblock template's per-execution worktree paragraph with one- to two-sentence references to the worktree-first standard (naming the canonical section in `agents/skills/execute-plan/SKILL.md`), keeping only the payload-critical literals: the authoring-claims directory, the facts-file transfer-in, the review-artifact transfer-out with its primary-checkout verification, and the merge-locked landing. [class: IMPLEMENTATION_REQUIRED]
- [x] Update `scripts/check_maintenance_pins.sh` in the same edit, treating the coupled pin sites as one unit: re-key the authoring-body identification filter and the authoring worktree presence pin on the new reference sentence's distinctive span (which must live inside the authoring fenced body and be unique there), update the file-wide count pin for the retired authoring worktree literal, and update or drop the execution-paragraph pins whose spans the per-execution worktree paragraph replacement retires (the create-literal count pin, the linked-worktree bootstrap span pin, and the per-run pre-Phase-0 gate span pin); then run the pins suite and expect GREEN before leaving the task. [class: REPOSITORY_TEST]
- [x] Sweep `agents/skills/maintenance/SKILL.md` and `agents/skills/maintenance/zcode.md` for references to the replaced prose shapes (the worktree duty mirror sets, the per-execution worktree paragraph) and re-point each dangling reference to the canonical section, updating any owning pin in the same edit. [class: IMPLEMENTATION_REQUIRED]

### Task 5: corpus verification and commit

Files:
- none *(verification task; touches only the files above)*

- [x] Run the full Validation Commands block; expect exit 0 with every gate green. [class: REPOSITORY_TEST]
- [x] Commit: `skills: consolidate worktree-first standard into one canonical recipe` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

The backlog origin `docs/history/backlog/2026-09-28-worktree-first-standard-only-mode.md` was folded into this completed plan (its full scope is this plan's Outcome and tasks; the base-branch user clarification is recorded under Assumptions) and its per-item file deleted at archive time per the promoted-backlog rule.
