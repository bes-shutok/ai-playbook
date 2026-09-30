# Plan: User-directed maintenance payload re-arm and loop-liveness duties

Backlog origin: docs/history/backlog/2026-09-30-user-directed-maintenance-payload-rearm-duty-gap.md
Driving force: reliability
Plan review record: the staging series docs/reviews/2026-09-30-plan-review-user-directed-maintenance-payload-rearm-duties-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

A session started by a user-directed maintenance payload (manual `CronCreate`, or the runtime overlay's interactive dispatch template - not a blueprint-dispatched child and not a scheduler-template turn) performs the turn-start carrier re-arm duty before payload work and reports loop-liveness at its done/report step, so the maintenance loop can no longer go dark silently behind the template-issued payload class or a payload session that loads the skill; a manually issued payload whose session loads neither surface stays outside the mandate, and the parked-record discharge precedence remains its recovery path - the residual is named here so the record carries no false assurance.

- After this plan, the interactive dispatch template no longer disclaims the re-arm duty: the issued payload instructs the receiving session to run the turn-start carrier re-arm duty per the overlay's Recurring automation recipe before payload work, with the selection-loop guard's park (a standing `pending_rearm` record) as the sanctioned fallback, and the payload's closing report verifies that an ENABLED recognition match exists or the parked record stands, stating `loop-liveness:` plus the state in one line.
- The maintenance skill's Step 0 gains the audience-scoping bullet so a payload session that loads the skill sees its duties by name; blueprint-dispatched children keep the FIRST ACTION re-arm duty their payloads already carry, and scheduler turns keep Step 0 unchanged.
- The duty stays durable: the pins suite holds presence pins for the duty literal in the skill and the template sentence in the overlay.

Gate delta: adds one audience-scoping bullet (Step 0), one template reword plus duty sentence (the overlay's Interactive dispatch template), one liveness-verification reporting duty, and two pins-suite presence pins; removes nothing - the disclaimed sentence is reworded from "no child re-arm duty" to its narrowed truth (no BLUEPRINT child re-arm duty; the lightweight user-directed-payload duty applies); priced by the witnessed 2026-09-30 01:41 dark-window: a one-shot user-directed payload fired in an automation-born session, attempted the re-arm duty only voluntarily, hit the selection-loop stand-down on the primitive surface, and parked `pending_rearm` with no armed carrier and no blueprint child to re-arm it, leaving recovery to ride solely on a later primitive-capable touch.

## Terms

- **User-directed maintenance payload**: a maintenance-task payload issued outside the scheduler prompt template and outside the blueprints - manual `CronCreate` from a fresh chat, or the interactive dispatch template's filled text; the receiving session is automation-born and sees only the payload text unless it loads the skill itself.
- **Turn-start carrier re-arm duty**: the runtime overlay's Turn-start carrier re-arm duty (the recipe the Step 0 bullet already names); for this payload class it runs before any payload work, with the selection-loop guard's stop and the `pending_rearm` park write as its sanctioned fallback when the toolset cannot carry the work.
- **Loop-liveness**: the state file records either an ENABLED recognition match (the recipe's title plus prompt-opening literals) for the loop carrier in either of its legal forms, or a standing `pending_rearm` record; a closing report states `loop-liveness:` plus which in one line.
- **Blueprint-dispatched child**: a session fired from an authoring or execution blueprint in `agents/skills/maintenance/prompt-templates.md`; its payloads already carry the FIRST ACTION re-arm duty and are byte-pinned - unchanged by this plan.

## Assumptions

- assume the fix surface is the interactive dispatch template plus a Step 0 audience bullet, never the byte-pinned blueprint payloads; basis: the origin's own suspected root area names the payload blueprint AUDIENCE (the class of payload that carries no duty), and the user-directed class's actual issuing surfaces are the template and manual `CronCreate` - the blueprints already carry the duty and editing them would churn the pins for no gap closure.
- assume the witness's voluntary attempt and its selection-loop park are the correct fallback shape to keep: the duty's failure mode is the overlay's already-pinned park discipline (`pending_rearm` plus payload copy), and this plan adds no new park kind; basis: the origin's reproduction evidence and the expected fix (b) reading the parked record as an acceptable liveness state.
- assume "the session attempted the turn-start carrier re-arm duty voluntarily" proves the duty is discoverable but not mandated for this class, so the fix is an obligation sentence in the two issuing/loading surfaces, not a new recipe; basis: the recipe in the overlay is already the single creation source and stays byte-untouched as a recipe.
- assume the template's parenthetical "(no child re-arm duty)" was written for the blueprint child's full duty and reads as a total disclaimer only by accident; basis: the template sentence's own context ("interactive asks from a fresh session") predates the 2026-09-30 witness class.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: payloads issued by hand or through the interactive template now carry a mandated re-arm-first duty and must close with a one-line loop-liveness report, closing the dark-window class witnessed on 2026-09-30 01:41 where a user-directed payload parked the re-arm and left the loop with neither an armed carrier nor a blueprint child to restore it.

**Before (today):** A one-shot payload ("execute plans one by one", manual `CronCreate`) fires in an automation-born session. The payload text carries no re-arm instruction; the session attempts the duty voluntarily, trips the selection-loop guard on the primitive surface, parks `pending_rearm`, and ends. The loop has no armed carrier, no blueprint child scheduled to re-arm it, and no operator-visible signal - recovery waits for a later primitive-capable session to discharge the parked record by luck.

**After (this plan):** The same payload text, issued through the interactive dispatch template, instructs the re-arm duty before payload work; the voluntary attempt is now a mandated first step with the same park fallback. At closeout the report reads "loop-liveness: ENABLED recognition match <id>" or "loop-liveness: parked re-arm stands" - darkness is visible in the closing summary instead of silent. A payload session that loads the maintenance skill finds the duty named in Step 0, and the pins suite fails if either surface loses the duty text.

## Evaluation Criteria

**Quality dimensions:**

- audience correctness: the duty binds exactly the user-directed payload class (manual `CronCreate`, interactive-template issues); blueprint-dispatched children and scheduler-template turns are named as unchanged, and no duty is duplicated for audiences that already carry one.
- by-reference discipline: the overlay's Recurring automation recipe stays the single creation source and byte-untouched as a recipe; the skill bullet and the template sentence reference it, never restate its steps; the byte-pinned blueprints in `agents/skills/maintenance/prompt-templates.md` are byte-untouched.
- fail-closed liveness: the closing report's liveness line has two named states (ENABLED recognition match, or parked record stands) and no silent third; the pins suite fails if either new surface loses its duty text.

**Done when:**

- `bash scripts/check_maintenance_pins.sh` exits 0 including the two new presence pins.
- The Validation Commands block below exits 0 end to end.
- The em-dash gate (`scripts/check-no-em-dash.sh touched`) exits 0 on the changed tree, and the hygiene scan named by `public_hygiene_scan_script` in the user facts exits 0.

**Ship when:**

- None; skill prose and a pins-suite extension only.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`

**Tests:**

- the pins suite invocation (`bash scripts/check_maintenance_pins.sh`) is the test surface; no separate test file is added

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `agents/skills/maintenance/prompt-templates.md`; byte-pinned child blueprints (pins suite) - the gap's class never receives blueprint text.
- The overlay's Recurring automation recipe steps; single creation source, referenced not restated.
- `scripts/plan_readiness.py`; the certification oracle stays a byte-property gate.

## Validation Commands

```bash
# Tasks 1-3: per-file wiring obligations (each token below is verified absent from its file at authoring time, so a skipped task fails its grep; run from the repo root)
grep -qF 'User-directed maintenance payload duties' agents/skills/maintenance/SKILL.md || { echo "FAIL: Step 0 audience bullet missing"; exit 1; }
grep -qF 'loop-liveness:' agents/skills/maintenance/SKILL.md || { echo "FAIL: liveness duty missing from the skill"; exit 1; }
grep -qF 'loop-liveness:' agents/skills/maintenance/zcode.md || { echo "FAIL: liveness duty missing from the overlay"; exit 1; }
grep -qF 'no blueprint child re-arm duty' agents/skills/maintenance/zcode.md || { echo "FAIL: template disclaimer not reworded"; exit 1; }
grep -qF 'the user-directed maintenance payload duties below apply' agents/skills/maintenance/zcode.md || { echo "FAIL: template reword missing"; exit 1; }
grep -qF 'turn-start carrier re-arm duty per this overlay' agents/skills/maintenance/zcode.md || { echo "FAIL: template re-arm instruction missing"; exit 1; }

# Task 4: the durable pin (RED until Tasks 1 and 2 land, GREEN after)
bash scripts/check_maintenance_pins.sh || { echo "FAIL: maintenance pins suite"; exit 1; }

# Negative guard: the old total disclaimer is gone
if grep -qF '(no child re-arm duty)' agents/skills/maintenance/zcode.md; then echo "FAIL: stale disclaimer still present"; exit 1; fi

# By-reference: the pinned blueprints and the recipe stay byte-untouched
git diff --quiet "$(git merge-base main HEAD)" -- agents/skills/maintenance/prompt-templates.md || { echo "FAIL: blueprints changed"; exit 1; }

# Em-dash gate on the changed tree
bash scripts/check-no-em-dash.sh touched || { echo "FAIL: em dash in changed tree"; exit 1; }
```

### Task 1: Interactive dispatch template reword and duty sentence

Files:

- `agents/skills/maintenance/zcode.md`

Evidence:

- The Validation Commands block's overlay greps and the negative guard; each covers one prescribed literal below.

- [ ] Reword the template's closing paragraph sentence "This block is for interactive asks from a fresh session (no child re-arm duty)." to the narrowed truth: "This block is for interactive asks from a fresh session (no blueprint child re-arm duty; the user-directed maintenance payload duties below apply)." [class: IMPLEMENTATION_REQUIRED]
- [ ] Append one duty sentence to the same paragraph, worded so it does NOT repeat the exact span `Turn-start carrier re-arm duty` (the suite count-pins that capitalized span at exactly one occurrence and this plan leaves that pin untouched - the lowercase referent keeps the count at 1): the issued payload instructs the receiving session to perform the turn-start carrier re-arm duty per this overlay's Recurring automation recipe before any payload work, with the selection-loop guard's stop and the `pending_rearm` park write as the sanctioned fallback when the toolset cannot carry the work (the overlay's carry-ability vocabulary: an absent primitive routes the duty to its next leg, its escalation, or its park path), and the payload's closing report verifies that an ENABLED recognition match exists or a standing `pending_rearm` record stands, stating `loop-liveness:` plus the state in one line [class: IMPLEMENTATION_REQUIRED]
- [ ] The duty sentence carries a dated witness citation (2026-09-30, the user-directed payload re-arm duty origin; witness: the 01:41 dark window) per the overlay's revision convention [class: IMPLEMENTATION_REQUIRED]

### Task 2: Step 0 audience-scoping bullet

Files:

- `agents/skills/maintenance/SKILL.md`

Evidence:

- The Validation Commands block's skill greps and the Task 4 pins cover the bullet's title literal and the liveness token; the bullet's remaining clauses (audience parenthetical, unchanged-audiences sentence, write-class basis) are verified by review, not by grep.

- [ ] Add one bullet to the Step 0 context-load list, after the turn-start carrier re-arm bullet, titled `- User-directed maintenance payload duties (added 2026-09-30, the user-directed payload re-arm duty origin; witness: the 2026-09-30 01:41 dark window)`: [class: IMPLEMENTATION_REQUIRED]
- [ ] The bullet binds the audience in runtime-agnostic wording (SKILL.md names no runtime primitive): a session started by a user-directed maintenance payload (a manually created one-shot schedule ask from a fresh chat, or an interactive-dispatch-template issue - not a blueprint-dispatched child, whose payloads carry the FIRST ACTION re-arm duty, and not a scheduler-template turn) runs the turn-start carrier re-arm duty before any payload work, the overlay's Recurring automation recipe owning the steps [class: IMPLEMENTATION_REQUIRED]
- [ ] The bullet names the fallback and the reporting duty: the selection-loop guard's stop and the `pending_rearm` park write are the sanctioned fallback; at the done/report step the session verifies that an ENABLED recognition match exists or a standing `pending_rearm` record stands and reports `loop-liveness:` plus the state in one line [class: IMPLEMENTATION_REQUIRED]
- [ ] The bullet closes with the unchanged-audiences sentence: blueprint-dispatched children and scheduler-template turns keep their existing duties unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] The bullet names the write-class basis: the duty's state edits ride the existing sanctioned writer classes (the turn-start arming edit per the Scheduler-turns class, the park write per its sanctioned park mode) - no new writer class is created [class: IMPLEMENTATION_REQUIRED]

### Task 3: Consistency cross-checks

Files:

- none (verification-only task)

Evidence:

- The negative guard and the by-reference checks in the Validation block.

- [ ] Verify the total disclaimer is gone and only the narrowed form remains: the Validation block's negative guard fails on any surviving "(no child re-arm duty)" literal, and the reword grep passes only when the narrowed sentence landed [class: REPOSITORY_TEST]

### Task 4: Durable pins

Files:

- `scripts/check_maintenance_pins.sh`

Evidence:

- `bash scripts/check_maintenance_pins.sh`; RED until Tasks 1 and 2 land, GREEN after; covers the durability criterion.

- [ ] Add two presence pins using the suite's existing `pin()` helper with fixed-string greps: `User-directed maintenance payload duties` present in the skill, and `no blueprint child re-arm duty` present in the overlay, described so a PIN FAIL names which file lost the duty text [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend the header comment's pin-family enumeration with the user-directed-payload-duties family [class: IMPLEMENTATION_REQUIRED]

### Task 5: Validation execution

Files:

- none (execution-only task)

Evidence:

- The Validation Commands block, run end to end from the executing worktree root; covers every Done-when criterion.

- [ ] Run the Validation Commands block end to end and record its exit 0 in the execution evidence, then run the hygiene scan named by `public_hygiene_scan_script` in the user facts over the changed tree and record exit 0 [class: REPOSITORY_TEST]
