# Plan: Budget-gate resume fallbacks: landed-substance preservation and precheck closure

Executed 2026-09-23 (ad-hoc worktree ai-playbook-exec-budgetgate on main 28630705; branch 2026-09-23-budget-gate-resume-fallbacks): commits 295c2955 (Task 1 preservation pins, full nine-pin flip matrix in the body), e671c577 (Task 2 precheck origin closure augmentation), 94862485 (execution-time plan corrections + checkbox flips + date-note fix). Reviews: plan-review r1-r4 (authoring), r5 focused re-cert (execution-time corrections, ready=yes), r6 post-execution re-cert (checkbox-flips-only delta, SHA-256-proven, ready=yes); code-review r1 (2 blocking fixed, 1 Low fixed) and r2 (clean). Two execution-time drifts absorbed: the precheck origin was already closed and archived externally (Task 2 became pointer-augmentation), and commit 8a77ec46 reworded the plans-skill mirror (gates 6b/7b needles re-frozen).

External gate: scheduler-maintenance-loop-quality-hygiene

Backlog origins (scope of record) and their supersession record:

- `docs/history/backlog/2026-09-18-budget-gate-scheduling-on-automation-bound-sessions.md`: SUPERSEDED to done while this plan was open. Commit e71fd55a (2026-09-21 19:17, the quota-aware-scheduling-semantics delivery) landed the canonical lineage-cap branch (pause-protocol step 3 and the Standing resume watcher create, with the armed-parent skip refinement), the `Resume carrier fallback ordering (canonical)` paragraph (OffPeakCreate wired, launchd wired via the driver's scheduler chain at schedulable boundaries, report-only last, with the wired-state marks), carrier-aware `resume_scheduled`, and the plans-skill mirror amendments; the item is archived at `docs/history/backlog/completed/2026-09-18-budget-gate-scheduling-on-automation-bound-sessions.md` marked done. The origin's launchd disposition is resolved as IMPLEMENTED, superseding the origin's 2026-09-18 unwired observation. This plan's residue: preserve the landed spans (nothing pins them today) and verify the closure is complete.
- `docs/history/backlog/completed/2026-09-19-scheduler-toolset-precheck-before-dispatch.md`: verify-and-close (the fix is landed; this plan verifies the residue and closes the item). Execution-time drift note (2026-09-23): an external closeout already flipped the item closed and moved it to `completed/` (status `closed (fixed by 37877753; ladder precheck live in the zcode overlay; verified 2026-09-23)`); Task 2 therefore augments the already-closed item with the landed-surface pointer instead of performing the flip itself.

Coordination (binding): the gate slug names the hygiene plan (`docs/plans/2026-09-21-scheduler-maintenance-loop-quality-hygiene.md`, now landed on main as an open plan via 82f5edff); per the landed satisfaction rule the gate reads satisfied while that plan is open, and unsatisfied after it archives (the strand window and the D4 park backstop are triaged in the carve-out plan's Coordination section, same family). This plan's Task 1 edits the pins suite additively beside the hygiene plan's Task 6 pin work (different sections, union-merge precedent).

## Terms

- **Landed substance**: the origin-2 fix text that e71fd55a landed in `agents/skills/execute-plan/SKILL.md` and `agents/skills/plans/SKILL.md` (the canonical lineage-cap branch, the Resume carrier fallback ordering paragraph, the carrier-aware record semantics).
- **Preservation pin**: a count-gated pin over already-landed text whose duty is to stay green (a regression - the span's deletion or duplication - fails the suite); unlike this family's other plans, these gates are GREEN at authoring time by design.
- **Verify-and-close**: the disposition for an origin whose fix already landed: verify each acceptance clause against its landed surface, record the verification, flip the item closed with a pointer, and add no implementation.

## Assumptions

- assume the landed substance is complete against the superseded origin's three prevention items (the lineage-cap branch in the pause protocol; the ordered fallbacks with wired-vs-unwired marks; the launchd implement-or-stop-advertising disposition); basis: clause-by-clause reading of the landed bytes at the r3 fold (2026-09-21): all three are present, with the launchd rung wired via the driver's scheduler chain; the verification task re-checks this on the execution-time bytes and records it.
- assume the precheck origin's residue is documentation-only (a Status flip with a pointer); basis: the landed surfaces verified 2026-09-21 - the overlay's Ladder precheck bullet (lane-scoped precheck, both `turn_error` reasons, the park-or-retain rule, zero listings), the `agents/skills/maintenance/SKILL.md` Step 5 ladder-precheck precondition, the dispatch-discipline bullet's dated Precheck witness, and the pins suite's toolset-precheck block.
- assume preservation pins over the landed spans belong to this plan and not to the executing plan that landed them; basis: that plan is archived (its review loop closed before the spans existed as freeze candidates), and this family owns the budget-gate resume surface.
- assume the landed substance stays complete on the execution-time bytes; basis: the r3 fold's clause-by-clause reading (2026-09-21), and Task 2's final Validation Commands run re-witnesses the landed spans through gates 1 through 7 before the closure flip.

Decision points requiring a grill: supersession handling (rebase this plan to preservation plus closure instead of dropping it or re-implementing landed text): resolved by the task prompt's standing pre-authorization, accept all recommended options without asking, 2026-09-21 authoring prompt, applied to the r2 F1 supersession finding; affected section: the supersession record above and Task 1. Preservation-pin scope (nine landed spans, count-gated): same standing pre-authorization receipt; affected section: Task 1. Verify-and-close disposition for the precheck origin: same standing pre-authorization receipt; affected section: Task 2.

## Gist & Examples

This plan was authored as the implementation plan for the budget-gate resume fallbacks. While its review loop ran, the substance landed from another channel: commit e71fd55a delivered the quota-aware-scheduling-semantics plan, whose message names "budget-gate resume fallbacks", and its bytes now carry everything this plan prescribed and more - the lineage-cap branch (delete the session's own completed spawner record, retry once, never delete an armed recurring parent, record the deletion and retry outcome), the Resume carrier fallback ordering paragraph with honest wired-state marks (OffPeakCreate wired; launchd wired via the driver's scheduler chain at schedulable boundaries; report-only last), and carrier-aware `resume_scheduled` - in the canonical protocol and mirrored in the plans skill. The origin item is archived marked done.

**Before (this plan's original shape)**: prescribe those edits. **After (this plan now)**: keep them from silently regressing and close what remains open. Nothing pins the landed spans today: a future edit could drop the lineage-cap branch or the fallback ordering and no mechanical gate would fail. Task 1 adds count-gated preservation pins over the nine gate spans. Task 2 verifies the toolset-precheck origin clause-by-clause against its landed surfaces and augments the already-closed item with the landed-surface pointer (the last open residue of this family's origins).

Worked example of the preservation pin's value: a refactor rewords the pause protocol's step 3 and drops the sentence "The create carries the canonical lineage-cap branch" - the pins suite fails with `PIN FAIL: canonical lineage-cap branch span count`, naming the deleted obligation, instead of the regression landing silently.

## Design Invariants (CR Guard)

- **Preservation, not re-implementation**: no task re-edits the landed substance; the only edits are additive pins and the backlog item closures.
- **Honest closure**: each origin closure maps every acceptance clause to a landed surface named in the pointer; a clause with no landed surface would be a finding, not a closure.
- **Additive pin work**: the new pin block sits beside (never inside) the hygiene plan's Task 6 pin sections; the existing suite stays untouched.
- **No em-dashes in prescribed text**: the exact-needle greps guard the pins; the pinned files carry legacy em-dashes in frozen regions (measured 2026-09-21: four in execute-plan SKILL.md), so no whole-file sweep is prescribed.

## Evaluation Criteria

**Quality dimensions:**

- durability: the nine pinned anchor spans (the exact spans and counts the Validation Commands gates 1 through 7 pin) each carry a count-gated pin that fails on deletion or duplication; the pins guard the anchor spans, not every operative clause of the landed substance (receipted pin scope, r4 F1 option b).
- verification discipline: each origin clause maps to its landed surface in the task log before any Status flip.
- safety (no regressions): the pins suite exits 0 on the post-task tree and every existing pin is untouched.

**Done when:**

- All tasks checked; the Validation Commands block exits 0 on the post-task tree.
- `bash scripts/check_maintenance_pins.sh` exits 0 including the nine new preservation pins.
- `python3 scripts/plan_readiness.py docs/plans/2026-09-21-budget-gate-resume-fallbacks.md` exits 0.
- Both backlog items read closed with landed-surface pointers (origin 2's archive verified done; the precheck item augmented in place).

**Ship when:**

- The next real budget pause inside an automation-born run resumes through the landed recipe or the OffPeakCreate rung without operator intervention; observed operationally by the loop. Loop-owned; prose only. [class: OPERATIONS_FOLLOW_UP]

## Review Scope

**Explicit must-fix; findings on these paths are always in scope (review and fix if valid):**

**Production code:**

- `docs/history/backlog/completed/2026-09-19-scheduler-toolset-precheck-before-dispatch.md`

**Tests:**

- `scripts/check_maintenance_pins.sh`

**Partially-in-scope files:** in the pins suite, only the new preservation-pin block (a single additive section) and its freeze-literal origin note are open. In the precheck backlog item, only the Status line and one appended pointer line are open. The landed substance files (`agents/skills/execute-plan/SKILL.md`, `agents/skills/plans/SKILL.md`) are READ-ONLY for this plan: they are the verification and pinning TARGETS, never edit targets. The archived origin-2 item is read-only verification input.

**Plan-related extension;** findings are in scope when causally related to this plan.

**Out of scope; reject unless plan-related:**

- `scripts/quota_window_probe.py` and the driver (`scripts/execute_plan_runtime.py`); reason: owned by the landed quota-aware delivery and the watcher plans.
- The overlay (`agents/skills/maintenance/zcode.md`); reason: its precheck surfaces are verification TARGETS, not edit targets.
- Pre-existing em-dashes in the pinned files (measured 2026-09-21: four in execute-plan SKILL.md); reason: frozen regions; the pin needles are em-dash-free spans.

## Validation Commands

First executed at authoring time against the pre-task tree (2026-09-21, post-rebase bytes); re-frozen 2026-09-23 against the execution-time bytes after commit 8a77ec46 reworded the plans-skill mirror (the two mirror needles of gates 6b and 7b re-frozen to the current spans): the preservation gates over the landed substance are GREEN today by design (the spans are landed; their duty is to stay green), and the two closure gates differ (the precheck closure gate, gate 9, is RED; origin 2's archive gate, gate 8, is GREEN). The FIRST failing gate is gate 9 (the precheck closure), exit 1. The preservation gates' failure direction is deletion or duplication of a landed span, proven per pin in Task 1's flip probes.

```bash
REPO="$(git rev-parse --show-toplevel)"
E="$REPO/agents/skills/execute-plan/SKILL.md"
PL="$REPO/agents/skills/plans/SKILL.md"
B="$REPO/docs/history/backlog/completed/2026-09-19-scheduler-toolset-precheck-before-dispatch.md"
DONE="$REPO/docs/history/backlog/completed/2026-09-18-budget-gate-scheduling-on-automation-bound-sessions.md"
PIN="$REPO/scripts/check_maintenance_pins.sh"
fail=0
for f in "$E" "$PL" "$B" "$DONE" "$PIN"; do
  [ -f "$f" ] || { echo "FAIL: missing $f"; fail=1; }
done
count() { grep -oF -- "$2" "$1" 2>/dev/null | wc -l | tr -d ' '; }
# 1. The canonical lineage-cap branch is landed and preserved
n=$(count "$E" 'The create carries the canonical lineage-cap branch')
[ "$n" -eq 1 ] || { echo "FAIL: canonical lineage-cap branch span count $n != 1"; fail=1; }
# 2. The Resume carrier fallback ordering paragraph is landed and preserved
n=$(count "$E" 'Resume carrier fallback ordering (canonical)')
[ "$n" -eq 1 ] || { echo "FAIL: fallback ordering paragraph count $n != 1"; fail=1; }
# 3. The OffPeakCreate rung's pause-boundary application is preserved
n=$(count "$E" 'the OffPeakCreate rung first')
[ "$n" -eq 1 ] || { echo "FAIL: OffPeakCreate pause rung count $n != 1"; fail=1; }
# 4. The launchd wired-state mark is preserved (the honest-advertising resolution)
n=$(count "$E" "wired via the driver's scheduler chain")
[ "$n" -eq 1 ] || { echo "FAIL: launchd wired mark count $n != 1"; fail=1; }
# 5. The OffPeakCreate prompt contract is preserved
n=$(count "$E" 'the prompt must carry the reset epoch and a wait instruction')
[ "$n" -eq 1 ] || { echo "FAIL: OffPeakCreate prompt contract count $n != 1"; fail=1; }
# 6. The carrier-aware record semantics are preserved (canonical and mirror)
n=$(count "$E" 'or when the OffPeakCreate rung carries the resume')
[ "$n" -eq 1 ] || { echo "FAIL: canonical carrier-aware record count $n != 1"; fail=1; }
n=$(count "$PL" 'or when the host idle-time automation rung carries the resume')
[ "$n" -eq 1 ] || { echo "FAIL: mirror carrier-aware record count $n != 1"; fail=1; }
# 7. The mirror's lineage-cap branch is preserved
n=$(count "$PL" "deletes the session's own completed spawner record and retries the create once")
[ "$n" -eq 1 ] || { echo "FAIL: mirror lineage-cap branch count $n != 1"; fail=1; }
n=$(count "$PL" 'host idle-time automation rung')
[ "$n" -eq 3 ] || { echo "FAIL: mirror OffPeakCreate rung count $n != 3"; fail=1; }
# 8. Origin 2's archive is verified done
grep -qF 'Status: done (executed via docs/plans/completed/2026-09-20-quota-aware-scheduling-semantics.md' "$DONE" || { echo "FAIL: origin 2 archive marker drifted"; fail=1; }
# 9. The precheck origin reads closed with the landed-surface pointer (RED until Task 2)
grep -qF 'Status: closed (verified landed' "$B" || { echo "FAIL: precheck origin not closed"; fail=1; }
grep -qF 'Ladder precheck bullet' "$B" || { echo "FAIL: closure pointer missing the landed surface"; fail=1; }
# 10. Pins suite green (existing pins plus the Task 1 preservation pins)
bash "$PIN" || { echo "FAIL: maintenance pins do not hold"; fail=1; }
[ "$fail" -eq 0 ] && echo "validation: all hold" || exit 1
```

### Task 1: Preservation pins over the landed substance

Files:
- `scripts/check_maintenance_pins.sh`

- [x] Add one additive section (a comment header naming this plan as the origin) after the budget-gate resume mirrors block, with count-gated pin lines in the suite's standalone shape (`fail=1` on mismatch): NINE lines, exactly the spans and counts the Validation Commands gates 1 through 7 pin - the canonical lineage-cap branch (1), the `Resume carrier fallback ordering (canonical)` heading (1), the OffPeakCreate pause rung (1), the launchd wired mark (1), the OffPeakCreate prompt-contract span (1), the canonical carrier-aware record span (1), the mirror carrier-aware record span (`or when the host idle-time automation rung carries the resume`, 1), the mirror lineage-cap branch (1), and the mirror `host idle-time automation rung` span (3) [class: REPOSITORY_TEST]
- [x] Append the freeze-literal origin note per the suite header's protocol (the preservation spans' origin is this plan; their text was landed by e71fd55a); simulate every new pin's failure direction once against a mutated temp copy (span deleted, then span duplicated) and record the flip-probe outcomes in the commit message body [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` exits 0 on the current tree (the spans are landed; the pins are preservation gates) [class: REPOSITORY_TEST]
- [x] Commit: `test: preservation pins for the landed budget-gate resume fallback substance` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Precheck origin verify-and-close

Files:
- `docs/history/backlog/completed/2026-09-19-scheduler-toolset-precheck-before-dispatch.md`

- [x] Verify each acceptance clause against its landed surface and record the verification per clause in the task log: (a) a turn lacking the needed primitive ends with `turn_error: clocked-primitives-absent` (overlay Ladder precheck bullet, lane-scoped, plus `idle-primitive-absent` for the idle lane); (b) zero listings performed on a tripped precheck (the bullet's "zero listings performed" wording); (c) the dispatch retained or parked per the trap rule (the bullet's park-or-retain sentence and the `agents/skills/maintenance/SKILL.md` Step 5 ladder-precheck precondition); (d) the guard fires only on genuine listing-without-mutation loops thereafter (the dispatch-discipline bullet's dated Precheck witness); (e) the surfaces are pinned (the pins suite's toolset-precheck block: the Step 5 needle, the overlay bullet needle, both stand-down reasons) [class: IMPLEMENTATION_REQUIRED]
- [x] The item is already closed by an external closeout (see the supersession-record drift note); augment it in place: amend the existing `Status:` line to read `Status: closed (verified landed; fixed by 37877753; ladder precheck live in the zcode overlay; verified 2026-09-23)`, plus one appended pointer line naming `Ladder precheck bullet` in the overlay, the `agents/skills/maintenance/SKILL.md` Step 5 ladder-precheck precondition, and the pins suite's toolset-precheck block; no other edit to the item [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN on Validation Commands gate 9 and the full block (all gates green at this boundary) [class: REPOSITORY_TEST]
- [x] Commit: `docs: close the toolset precheck origin as verified landed` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Final validation

- [x] Run → expect GREEN: full Validation Commands block, exit 0 [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `python3 scripts/plan_readiness.py docs/plans/2026-09-21-budget-gate-resume-fallbacks.md` exits 0 [class: REPOSITORY_TEST]
