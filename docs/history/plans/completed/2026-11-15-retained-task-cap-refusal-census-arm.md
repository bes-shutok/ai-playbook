# Plan: Retained-task cap census arm for refused schedule asks

Backlog origin: docs/history/backlog/2026-11-15-global-retained-task-cap-refusal-no-census-arm.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-11-15-plan-review-retained-task-cap-refusal-census-arm-p39d55f67-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list).
Authoring claim: 2026-11-15-global-retained-task-cap-refusal-no-census-arm.md (session sess_45bd2c26-e701-4ee0-b075-dbf6c34af845)
Execution budget: 0.5h total, largest task 0.5h
Executed: yes (bb930d325)

## Terms

- **Retained-task cap:** the runtime's global limit (20) on retained automation records; an automation create is refused once the fleet table holds 20.
- **Fleet census:** one read-only listing of the retained automation fleet plus its classification and counts.
- **Census arm:** the sanctioned read-only census-and-report fallback a cap-refused schedule-ask session exhausts before reporting the ask unscheduled.
- **Live one-shot:** a retained one-shot carrier that is enabled with a pending fire time.
- **Lingered one-shot:** a retained one-shot that already fired or was disabled (enabled false, lifecycle completed or disabled) and still occupies the table.
- **Recurring carrier:** a retained automation with recurrence enabled (the loop parent or a recurring fallback).
- **Safe-deletion candidate:** a retained record an operator can delete to clear cap room, fired-and-complete one-shots first.
- **Scheduling asks section:** the root AGENTS.md `## Scheduling asks (verb contract)` section.
- **Sibling-span fence:** the pinned validation contract in completed plan docs/history/plans/completed/2026-10-17-schedule-ask-session-owned-automation.md that sweeps the Scheduling asks section, excluding the cap-refused bound-session bullet onward, for dispatch-ladder and cap-refusal vocabulary.
- **Cap-refused session:** a schedule-ask session whose automation create was refused with an error naming the retained-task cap.

## Why

On 2026-11-15 a one-shot schedule ask was refused at the runtime's global retained-task cap and the asking session had no sanctioned in-turn arm: it reported the ask unscheduled with an unaided manual-delete remedy. The fleet sits at the cap nightly (17 active one-shot carriers stacked on one execution queue plus lingered records), so every future ask is one refused create away from the same dead end.

## Gist & Examples

TLDR: A schedule ask refused at the global retained-task cap gains one sanctioned read-only census arm plus an AGENTS.md pointer naming it, so the refusal report carries a concrete fleet census and safe-deletion candidates instead of an unaided manual remedy, restoring efficiency to the cap-refusal path.

Before: the create is refused at the cap; the session reports the ask unscheduled; the remedy is "delete a task on the Automations page, then re-ask" with no census and no classification of what occupies the table.

After: the same refusal runs one read-only census: list the fleet, classify live one-shot versus lingered one-shot versus recurring carrier, report the counts and the safe-deletion candidates (fired-and-complete one-shots first), stop, and still report the ask unscheduled; the operator deletes from a concrete candidate list.

Edge cases: a bound session at the cap keeps its delete-own-spawner-first ordering (the census adds no reorder and runs beside it); a truncated or unreadable listing is reported as cannot-decide, never guessed around; the census never deletes, never runs a duplicate-lookup or deconfliction pass, and never satisfies the ask.

## Outcome

The cap-refusal dead end closes: a refused session's report carries the census instead of an unaided remedy.

- The scheduling-primitives module owns the census arm: trigger, classification vocabulary, safe-deletion reporting, stop boundary, and the machinery admission fields.
- The AGENTS.md Scheduling asks section names the arm as the sanctioned fallback a cap-refused session exhausts before reporting unscheduled.
- The no-duplicate-lookup rule and the report-unscheduled semantics stay byte-identical; no autonomous deletion, no new scheduling primitive, no gate.

Gate delta: refusal classes, hard gates, fences, protocol layers, and schema fields are all explicitly none (none added, removed, or changed); one prose-only reporting duty is added (the read-only census arm plus its AGENTS.md pointer bullet), priced by its witnessed incident docs/history/backlog/2026-11-15-global-retained-task-cap-refusal-no-census-arm.md and the admission fields recorded in Assumptions; no gate, ledger, lock, or state field changes.

## Assumptions

- The refusal trigger keys to the observed refusal shape (an error naming the global retained-task limit), never an error code; basis: the 2026-11-15 witnessed refusal recorded in the origin row's Evidence section, read 2026-11-15.
- The census lists through the runtime's own listing primitive (CronList) and classifies per the linger model the module's Listing bullet already records; basis: agents/skills/maintenance/zcode-scheduling-primitives.md Listing bullet, read 2026-11-15.
- Machinery admission for the census duty: incident docs/history/backlog/2026-11-15-global-retained-task-cap-refusal-no-census-arm.md; expected catch every future cap-refused ask while the fleet sits at or near the cap; false-positive cost one extra fleet listing per refusal (report-only); review date 2026-12-15. The warning-only refusal-path gate alternative is rejected: the report-only arm closes the witnessed gap and a gate emits into the same report that already reached the operator; basis: the origin row and the machinery admission protocol, read 2026-11-15.
- The module bullet grows agents/skills/maintenance/zcode-scheduling-primitives.md within its cap (no ceiling breach reported by the blocking gate on 2026-11-15); growth above a cap is paid by same-file deletions in the same change; AGENTS.md is not walked by the byte-budget gate; basis: scripts/skill_text_budget.py --check, 2026-11-15.
- The AGENTS.md insertion point (immediately after the cap-refused bound-session bullet) keeps the sibling-span fence's swept region byte-identical; basis: the fence contract sweeps the section excluding the cap-refused bullet onward (validation block #8 in docs/history/plans/completed/2026-10-17-schedule-ask-session-owned-automation.md), read 2026-11-15.

Decision points requiring a grill: census arm home: appended as the module's closing bullet, the simpler-design pick over a new module file (the module already owns the listing primitive and refusal-shape vocabulary and the origin names this module), source: origin row Suggested correction, 2026-11-15, affected: Task 1; AGENTS.md pointer placement: immediately after the cap-refused bound-session bullet, keeping the sibling-span fence's swept region untouched instead of amending completed-history pins, source: the completed 2026-10-17 plan's fence contract, 2026-11-15, affected: Task 2; census scope: session-agnostic per the origin's Expected wording with bound sessions keeping their delete-own-spawner-first ordering, source: origin row Observed versus expected, 2026-11-15, affected: Task 1; machinery alternative: rejected the warning-only gate with the admission fields recorded in Assumptions, source: the entry prompt's decision rule and the machinery admission protocol, 2026-11-15, affected: Assumptions and Outcome (maintenance-selected standing authorization).

## Standing constraints

- Add no gate, validator, lock, ledger, scheduling primitive, or state field; the census is read-only and report-only, and every automation delete stays operator-gated.
- Preserve the operator's no-duplicate-lookup rule and the report-unscheduled semantics byte-identical; the census never substitutes a deconfliction pass and never satisfies the ask.
- Land the rule, not the story: each operative surface cites the incident row in at most one line.
- Keep the edited skill file within its byte cap; pay for growth with same-file deletions in the same change.

## Evaluation Criteria

**Quality dimensions:**
- correctness: both operative surfaces state the trigger, the census body (list, classify, report, stop), and the unscheduled-report boundary.
- pin coverage: each inserted span carries a dedicated exactly-once presence check that fails when the span is absent.
- byte balance: the blocking byte-budget gate passes with no cap breach.
- simplicity: the diff adds no gate, validator, lock, ledger, or state field.

**Done when:**
- the module carries the census arm bullet with its classification vocabulary, admission fields, and the one-line incident citation;
- the AGENTS.md section carries the pointer bullet naming the arm and the unscheduled boundary;
- the sibling-span fence echo check passes over the swept region;
- the byte-budget, pin, hygiene, and no-em-dash checks pass.

**Ship when:** none (repository-only operative-text change).

## Documentation Impact Assessment

Only the two operative surfaces change; both already own the duties they pin, so no new document, README row, or registry change is needed: the skill names, paths, and invocations do not change. Router note: the module-dispatch enumeration in agents/skills/maintenance/zcode.md is a non-normative summary; load-on-dispatch loads the module's whole text, so the enumeration lagging one bullet after landing is accepted and out of scope.

## Design Invariants

The scheduling-primitives module is the single home for scheduling primitive and refusal-shape vocabulary on this runtime, so the census arm extends it as the closing bullet rather than a new file; the module's bullet style (added-date annotation, origin citation in the opener) is preserved. The Scheduling asks section's completed-plan pins and the sibling-span fence are load-bearing contracts: the pointer bullet inserts below the cap-refused bound-session bullet, outside the fence's swept region, so no pinned byte moves. The census arm cites the operator-ordered schedule surface paragraph (its home is agents/skills/maintenance/zcode-dispatch-ladder.md) as the delete-ownership boundary without restating its ordering.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/zcode-scheduling-primitives.md` (Task 1)
- `AGENTS.md` (Task 2)

**Tests:**
- none; no test file is added or changed by this plan.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Partially-in-scope files:** within `AGENTS.md`, only the `## Scheduling asks (verb contract)` section is open; all other AGENTS.md sections are frozen, and review findings there are out of scope.

**Documentation:** the two operative surfaces are the sole homes; do not duplicate the census arm in the maintenance SKILL.md router, the guards module, or the dispatch-ladder module.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/zcode.md` and `agents/skills/maintenance/zcode-dispatch-ladder.md`; reason: the operator-ordered schedule surface paragraph stays byte-identical (the census arm cites it, never rewrites it).
- `scripts/check_maintenance_pins.sh`, `scripts/skill_text_budget.py`, `scripts/check_plan_origins_closed.py`, `scripts/check-no-em-dash.sh`; reason: validators and gates stay byte-identical.
- `docs/history/backlog/PLAN-PROMPTS.md` and `docs/history/backlog/EXEC-PROMPTS.md` entry bodies; reason: no entry bytes change (landing riders excepted).
- `docs/history/plans/completed/2026-10-17-schedule-ask-session-owned-automation.md`; reason: completed history is immutable; the fence is honored by placement, not amended.

## Validation Commands

Validation preamble (authoring record, rule 29): `python3 scripts/plan_readiness.py --pre-round` failed once over task 1's 640-byte acceptance item (512 cap), fixed by splitting the opener and classification criteria (task 2's quoted bullet split the same way), then passed structural-clean from the worktree root (a warning-only FILES-COVERAGE notice remains over the quoted bullet's leading `- ` parsing as a path-like span; task 2's Files list declares AGENTS.md). `python3 scripts/fix_plan_em_dashes.py` ran at every write with zero substitutions; `bash scripts/check-no-em-dash.sh added-lines --base 10ca42138` passed. `bash scripts/scan-public-hygiene.sh` passed (report-only notice over an existing docs path, no findings). `python3 scripts/skill_text_budget.py --check` passed with no cap breach. `bash scripts/check_maintenance_pins.sh` exits 1 on one pre-existing failure, "prompt log has no all-served (stale) entry": the frozen maintenance-integrity-stop-scope-and-retry entry awaits its authoring landing on main (pre-existing state at this branch point, the same condition a sibling authoring run recorded the same day); the failure is unrelated to this plan's files, none of which the pins script gates, and no pin of this plan fails. Review round r1 (record 2026-11-15-plan-review-retained-task-cap-refusal-census-arm-p39d55f67-r1.md, completed 2026-11-16) returned ready=yes with zero blocking and four Low findings: F2 and F3 folded in this revision (the two Gist edge clauses landed as a dedicated Task 1 item; the module safety-clause pin and the AGENTS.md middle-clause pin added, taking the pin set to nine), F4 accepted via the Documentation Impact Assessment router note, F1 accepted as documenting the out-of-scope boundary (the reviewer verified this plan's zcode-dispatch-ladder.md citation is the correct home). Rule 19 RED-today evidence: the original seven pins were executed 2026-11-15 against the current tree and returned 0; the two r1-fold pins were executed 2026-11-16 against the current tree and returned 0; all nine flip GREEN exactly when Tasks 1 and 2 land. Rule 22 mechanical audit: each pinned span occurs exactly once within the task sections; the Validation Commands block passed `bash -n`; the fence echo command sweeps AGENTS.md only, so the plan's own embedded patterns cannot self-match (rule 15).

```bash
python3 scripts/skill_text_budget.py --check
bash scripts/check-no-em-dash.sh touched
bash scripts/scan-public-hygiene.sh
test "$(grep -cF 'Global retained-task cap census arm (added 2026-11-15' agents/skills/maintenance/zcode-scheduling-primitives.md)" -eq 1 || { echo "census arm opener pin missing or duplicated"; exit 1; }
test "$(grep -cF 'fired-and-complete one-shots first' agents/skills/maintenance/zcode-scheduling-primitives.md)" -eq 1 || { echo "safe-deletion pin missing or duplicated"; exit 1; }
test "$(grep -cF 'expected catch every future cap-refused ask' agents/skills/maintenance/zcode-scheduling-primitives.md)" -eq 1 || { echo "admission catch pin missing or duplicated"; exit 1; }
test "$(grep -cF 'false-positive cost one extra fleet listing per refusal' agents/skills/maintenance/zcode-scheduling-primitives.md)" -eq 1 || { echo "admission false-positive pin missing or duplicated"; exit 1; }
test "$(grep -cF '2026-11-15-global-retained-task-cap-refusal-no-census-arm.md' agents/skills/maintenance/zcode-scheduling-primitives.md)" -eq 1 || { echo "incident citation must appear exactly once in the module"; exit 1; }
test "$(grep -cF 'runs no duplicate-lookup or deconfliction pass' agents/skills/maintenance/zcode-scheduling-primitives.md)" -eq 1 || { echo "module safety-clause pin missing or duplicated"; exit 1; }
test "$(grep -cF 'the census deletes nothing, and the ask still reports' AGENTS.md)" -eq 1 || { echo "AGENTS.md middle-clause pin missing or duplicated"; exit 1; }
test "$(grep -cF 'exhausts the read-only census-and-report arm in agents/skills/maintenance/zcode-scheduling-primitives.md' AGENTS.md)" -eq 1 || { echo "AGENTS.md pointer pin missing or duplicated"; exit 1; }
test "$(grep -cF 'the ask still reports unscheduled until the operator clears room' AGENTS.md)" -eq 1 || { echo "AGENTS.md unscheduled-boundary pin missing or duplicated"; exit 1; }
tmpdir="$(mktemp -d)"
awk '/^## Scheduling asks/{f=1;next} f && /^## /{exit} f' AGENTS.md | sed '/^- In a cap-refused bound session/,$d' > "$tmpdir/swept.txt"
test -s "$tmpdir/swept.txt" || { echo "FAIL: fence sweep region empty (awk anchor drift)"; rm -rf "$tmpdir"; exit 1; }
rc=0
grep -Ein 'dispatch ladder|cap-refus|delete-own-spawner|delete-plus-create|pending_rearm|re-arm' "$tmpdir/swept.txt" || rc=$?
test "$rc" -eq 1 || { echo "FAIL: fence sweep rc=$rc (0 = encroachment, >=2 = tool error)"; rm -rf "$tmpdir"; exit 1; }
rm -rf "$tmpdir"
echo "retained-task-cap census arm checks: all pass"
```

### Task 1: Add the census arm to the scheduling primitives module

Context surface: the plan's Terms, this task, Standing constraints, and `agents/skills/maintenance/zcode-scheduling-primitives.md`.

Files:
- `agents/skills/maintenance/zcode-scheduling-primitives.md`

- [x] The module's closing bullet opens `Global retained-task cap census arm (added 2026-11-15, origin docs/history/backlog/2026-11-15-global-retained-task-cap-refusal-no-census-arm.md)` and, given a schedule-ask session's automation create refused with an error naming the runtime's global retained-task limit, orders one read-only census-and-report pass that then stops. [class: IMPLEMENTATION_REQUIRED]
- [x] The census pass lists the fleet with the listing primitive, classifies each retained record live one-shot, lingered one-shot (completed or disabled), or recurring carrier, and reports the counts plus the safe-deletion candidates (fired-and-complete one-shots first). [class: IMPLEMENTATION_REQUIRED]
- [x] The same bullet states the census deletes nothing, runs no duplicate-lookup or deconfliction pass, never substitutes for the report-unscheduled semantics the Scheduling asks section pins, and cites the operator-ordered schedule surface paragraph (agents/skills/maintenance/zcode-dispatch-ladder.md) as the boundary that keeps every automation delete operator-gated. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a truncated or unreadable fleet listing, the same census arm reports the census as cannot-decide rather than guessing around it, and given a bound session at the cap, the same bullet states the census adds no reorder to the delete-own-spawner-first ordering. [class: IMPLEMENTATION_REQUIRED]
- [x] The same bullet records the machinery admission fields with no gate added: incident the origin row cited above; expected catch every future cap-refused ask; false-positive cost one extra fleet listing per refusal; review date 2026-12-15. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the edited file within its byte cap; pay for any growth with same-file deletions in this change. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Validation Commands block and confirm the module pins pass and the byte-budget gate reports no cap breach. [class: REPOSITORY_TEST]
- [x] Commit: `docs: add retained-task cap census arm to scheduling primitives` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Name the census arm in the AGENTS.md scheduling asks section

Context surface: the plan's Terms, this task, Standing constraints, and the root `AGENTS.md` `## Scheduling asks (verb contract)` section.

Files:
- `AGENTS.md`

- [x] Given the same cap-refused create, the Scheduling asks section carries exactly one new bullet inserted immediately after the cap-refused bound-session bullet, reading in full the two spans pinned below. [class: IMPLEMENTATION_REQUIRED]
- [x] The new bullet opens: `- At a create refusal naming the runtime's global retained-task limit, the asking session exhausts the read-only census-and-report arm in agents/skills/maintenance/zcode-scheduling-primitives.md before reporting the ask unscheduled:` [class: IMPLEMENTATION_REQUIRED]
- [x] The new bullet continues: `list the fleet, classify live versus lingered (completed or disabled) one-shots and recurring carriers, report the safe-deletion candidates, and stop; the census deletes nothing, and the ask still reports unscheduled until the operator clears room.` [class: IMPLEMENTATION_REQUIRED]
- [x] The insertion keeps every pinned byte of the section (bullet 1 framing, satisfaction clause, deconfliction arm, cap-refused clause) unchanged and leaves the sibling-span fence's swept region byte-identical. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Validation Commands block: the AGENTS.md pins pass, the fence echo check passes, and the byte-budget, hygiene, and no-em-dash checks pass. [class: REPOSITORY_TEST]
- [x] Commit: `docs: name the census arm as the cap-refused schedule ask fallback` [class: IMPLEMENTATION_REQUIRED]
