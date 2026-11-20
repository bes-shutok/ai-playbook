# Plan: Loop continuity self-heal (no-dark-exit operation and decayed-residue standing direction)

Backlog origins (scope of record):
- docs/history/backlog/2026-11-10-authoring-lane-stale-residue-self-heal.md
- docs/history/backlog/2026-11-10-loop-no-dark-exit-successor-contract.md

Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/2026-11-10-plan-review-loop-continuity-self-heal-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1.25h total, largest task 0.5h
Executed: yes (48e1db4bb)
Authoring claim: loop-continuity-self-heal.md (session sess_2b51c910-597e-4972-9924-7f5eb673bd0f)

## Terms

- **Maintenance loop**: the unattended backlog-processing loop of `agents/skills/maintenance/SKILL.md`, its scheduler turns and its dispatched or in-session payload sessions.
- **Exit point**: any boundary at which a maintenance session ends or pauses its lane work: a completed unit, a deferral, an integrity-gate stop, the quota wall, or the empty-queue stop.
- **Exit token**: the `loop-exit:<class>` record (`queue-empty`, `quota-wall`, `blocked-retry`, `operator-stop`, `operator-park`) naming which exit form fired, carried in the turn's `decision_reason` or the session's closing report; a session boundary that leaves the loop's standing carrier armed is a recorded exemption under D-18, named by the loop-liveness line instead of a token.
- **Reset-anchored successor**: the one-shot carrier armed at the quota probe's `reset_at_epoch` plus the standing arming margin, defined in `agents/skills/maintenance/zcode.md` (the reset-anchored successor bullet).
- **Bounded blocked-retry successor**: the near-future retry one-shot armed through the occupied-lane chaining duty's arm shape and coverage consult (`agents/skills/maintenance/decisions.md`), whose payload re-derives the block from disk before any dispatch.
- **Directives home**: `docs/maintenance/operator-directives.md`, whose records win on conflict with any prompt, carrier-payload, or state-file clause, and which Step 0 orders every turn to read before acting on a directive-bearing clause; dispatched child sessions reach it through the duties-core refusal-consult clause this plan binds.
- **Standing direction**: an operator directive recorded in the directives home that pre-gives, for a stated class with stated conditions, a direction a rule otherwise requires per-incident.
- **Stale foreign staged log hunk**: a staged delta on a rolling prompt log path (PLAN-PROMPTS.md or EXEC-PROMPTS.md) staged by a session other than the acting session, aged past one cadence period (2 hours), with no live writer or live claim attribution.
- **Decayed residue**: a stale foreign staged log hunk that also passes the additive-only, unstaged-clean, and single-entry-section conditions of D-19.
- **Loop-liveness line**: the closing report line stating `loop-liveness:` plus the carrier state in one line, already ordered by the user-directed payload duty.
- **Cadence period**: 2 hours, the freshness constant the G1a discovery arm binds.
- **Verbatim completion**: resolving a decayed residue by committing its staged bytes unchanged through the sanctioned done-locked transaction, so the landed blob equals the recorded pre-image sha.

## Why

The loop stops on two things no standing text lets it resolve alone: a dead session's staged log bytes (the boundary rule's remedy needs per-incident operator direction, so the authoring lane starved two hours on 2026-11-10 while a quota-rich window ran empty), and its own exit paths (the same stop armed no successor, leaving the next authoring chance to a carrier fire recorded over twenty hours out). The operator has directed indefinite operation: run until the queue empties or the 5h wall, and at the wall schedule the successor right after reset.

## Gist & Examples

TLDR: the maintenance loop gains two standing operator directives, one binding every exit to arm its successor or record its exemption, one pre-giving the boundary rule's operator direction for decayed foreign staged log residue, so the loop runs indefinitely until the eligible queue empties or the 5h wall; automation (each shape today spends human direction and window time the loop already has).

Before (today): the 2026-11-10 12:47Z authoring dispatch re-verified its pick from disk and then stood down without writing anything: the entry freeze needs a primary log write, the primary index held a dead session's staged entry (staged 10:58Z, its rows committed, writer gone), and the boundary rule's remedy requires the operator's explicit direction per path - an unattended session has none. The stop armed nothing; the state file's recorded next fire sat over twenty hours out. The block resolved twenty minutes after the operator gave the direction, and a parallel operator-directed session committed the bytes verbatim (55d7a3c9c, recorded staged blob 56f7ef597).

After (this plan): the same session, reaching the same refusal, reads the directives home - the scheduler turn and in-session forms through Step 0's ordered read, dispatched children through the duties-core refusal-consult clause this plan adds (and, once the coordinated residue-recovery run lands, through the done_run.sh refusal message naming the remedy's home) - and finds D-19 pre-giving the direction for the decayed class: it checks the six conditions from disk, runs the boundary rule's remedy as written, and proceeds. The same session's exits all take one of D-18's five recorded token classes: queue-empty stop, quota-wall pause with the reset-anchored successor armed at reset+margin, blocked stop with one bounded retry successor whose payload re-derives the block from disk, operator-stop on an explicit operator stop or pause order, and operator-park after two consecutive blocked retries over the same block; continuing in-session per D-17 is no exit, and a session boundary that leaves the loop's standing carrier armed is a recorded exemption named by the loop-liveness line. No exit ends dark.

Edge cases: a fresh or attributable residue keeps the operator gate (conditions fail, gate stands); a desync snapshot (the staged delta deletes lines) keeps the gate; a residue whose content a live peer's fresh claim matches keeps the gate; an explicit operator stop request still stops without arming and records `loop-exit:operator-stop`; an automation-born session whose create is capped walks the existing dispatch ladder's legs and parks per its terminal rung, recording `loop-exit:operator-park`.

## Outcome

The maintenance loop runs indefinitely until the eligible queue is empty or the primary 5h wall, and recovers from dead-session log residue without a human.

- An unattended session meeting decayed residue resolves it itself through the existing blob-preserving remedy, with both blob shas recorded, and never stops for it again.
- Every exit arms the carrier its class orders or records its exemption; quota-wall pauses schedule the successor right after reset.
- The 2026-11-02 blob-preservation guarantees, the empty-queue stop, the explicit-stop stops, and the D-17 continuation semantics all stand unchanged.
- No new gate, validator, lock, ledger, automation primitive, or schema field exists after this plan.

Gate delta: no gate, fence, validator, lock, ledger, refusal class, protocol layer, or schema field added or removed; one existing refusal remedy's operator gate is pre-satisfied for the decayed-residue class by the standing direction D-19 (removal-shaped, priced by the witnessed incidents: five residue events 2026-11-02 through 2026-11-10, the origin row's Evidence section, and the operator's same-day verbatim direction 55d7a3c9c); text duties added for exit recording bind existing arming primitives by reference and add no ceremony with a dispatch or later-work pause; all other machinery unchanged; no blocking review-layer duty added.

## Assumptions

- assume the directives home is the operative placement for both records: its records win on conflict with prompt and payload clauses, Step 0 orders the home read before acting on any directive-bearing clause, and both arms are operator will, which that home exists to carry; basis: the directives home's own precedence clause and the Step 0 Operator directives home read bullet.
- assume D-9's self-service-reclaim predicate cannot absorb anonymous staged residue (it keys on recorded holders; staged bytes carry none), so D-19 extends D-9 rather than re-reading it; basis: D-9's directive text ("self-service reclaim of a foreign hold requires a liveness proof that the holder is verifiably dead").
- assume a pre-recorded standing direction satisfies the boundary rule's "the operator's explicit direction for that foreign path" for the decayed class; basis: the clause's own wording plus the directives home's precedence clause, and the operator's same-session direction choosing verbatim commit for exactly this shape (55d7a3c9c).
- assume the mechanical edits to the boundary rule text and the done_run.sh refusal message stay with the coordinated pending plan (docs/history/plans/2026-11-07-rolling-log-write-residue-recovery-recipe.md, execution pending): both paths sit in that run's recorded owned set, so this plan amends neither and cites the rule by reference; D-19's discovery for dispatched children rides two legs this plan owns or witnesses - the duties-core refusal-consult clause (Task 3, a surface every dispatched child loads before any gate or phase) and, once that run lands, its Task 3 refusal message naming the remedy's home; basis: that run's admission record and the Seam rule, that plan's Task 3 success criterion (the refusal message names the Write boundary rule's operator-gated remedy and its Standing rules home), and template-authoring.md's duties-core load lines.
- assume D-18 extends D-17 and D-6 without superseding either: D-17's continuation, the primary 5h pause, the empty-queue stop, and explicit stop requests all stand; basis: D-6's supersession note and D-17's directive text.
- assume the decay conditions are probe-able with existing tools alone (done-lock status, git diff against HEAD, file mtime, the claims directories, and the staged diff read against a fresh read of the log) so no probe script is added; basis: each condition names one existing read; the entry-structure condition reads the staged diff against the log's own Standing rules (the log pins targeted section edits and entry sections), no separate structural checker existing in the repo (corrected per review round 1, finding F3).

Decision points requiring a grill: none remain.

## Standing constraints

- Admission disjointness: this run's changed-file set intersects no outstanding run's recorded owned-path set; the authoritative enumeration is every `docs/tmp/execution-claims/*-admission.json` present at check time (authoring-time restatement: the read-budget run owns decisions.md, zcode.md, plans/SKILL.md, execute-plan/SKILL.md, skill_text_budget.py, the caps json, test_skill_text_budget.py, the pins script, machinery_registry.json, agterm/reference.md; the residue-recovery run owns PLAN-PROMPTS.md, template-authoring.md, worktree-first.md, done_run.sh); a task discovering it must touch any listed or recorded file stops and reports instead.
- Pinned spans stay byte-identical: every literal the pins suite carries over the touched files survives unchanged; a needed pin change stops the task for an operator decision (the pins file itself is in a coordinated run's owned set).
- Byte budget: each touched skill file stays within its own cap in the same edit (duties-core.md cap 16599, current 10315; SKILL.md cap 44233); if a growth exceeds the remaining headroom the excess is paid by relocating dated provenance parentheticals to the maintenance CHANGELOG in the same change (the anti-growth pay rule).

## Evaluation Criteria

**Quality dimensions:**
- correctness: D-18's five exit-token classes and D-19's six decay conditions name only states probe-able from disk with existing tools, and every arming shape cites its existing primitive by reference without restating it
- anti-growth: the touched skill file's net growth stays within its cap headroom (verified by the budget check in check mode), and no provenance narrative moves into operative text
- compatibility: the empty-queue stop, explicit stops, D-17 continuation, the quota pause, and every pins-carried literal survive byte-identical; the branch's added lines (`git diff` against the Validation Commands base) name no file path recorded in any coordinated run's admission record on disk, and D-19 cites the Write boundary rule by label only, never by file path

**Done when:**
- both directive records exist in docs/maintenance/operator-directives.md in the home's record format with the conditions and tokens this plan pins
- the router binding names D-18's exit duty in the Cycle gate paragraph, the Invariants section, and the Step 0 directives-home-read clause, and the dispatched-child binding sits in the duties-core intro paragraph
- the validation battery exits 0 and the coordination grep witnesses no touched file in either coordinated owned set

**Ship when:**
- none stated (no external release condition; the change is repository policy and skill text)

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `docs/maintenance/operator-directives.md` (Tasks 1 and 2)
- `agents/skills/maintenance/SKILL.md` (Task 3)
- `agents/skills/maintenance/duties-core.md` (Task 3)
- `agents/skills/maintenance/CHANGELOG.md` (Task 3)

**Tests:**
- none (the change is policy records and skill text; verification rides the sweep suite, the budget check, and the coordination grep, no test files are added)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/decisions.md` and `agents/skills/maintenance/zcode.md`; reason: owned by the outstanding read-budget run (its admission record also owns plans/SKILL.md, execute-plan/SKILL.md, skill_text_budget.py, the caps json, test_skill_text_budget.py, the pins script, machinery_registry.json, agterm/reference.md); D-18/D-19 cite their primitives by reference and the home wins on conflict
- `docs/history/backlog/PLAN-PROMPTS.md` and `scripts/done_run.sh`; reason: owned by the coordinated residue-recovery run; the boundary rule text and refusal message are that plan's surface, cited by reference here
- `agents/skills/maintenance/template-authoring.md`, `template-execution.md`, and `agents/skills/execute-plan/worktree-first.md`; reason: the blueprints' FINAL STEP paragraphs already apply directives from the home by path, the dispatched-child discovery rides duties-core instead, and one file is owned by the coordinated run
- `scripts/skill_text_budget.py`, `scripts/test_skill_text_budget.py`, `scripts/check_maintenance_pins.sh`, `scripts/machinery_registry.json`, `agents/skills/agterm/reference.md`; reason: owned by the outstanding read-budget run; this plan runs them read-only and adds no pin or registry row
- any owned path of an execution claim whose admission record appears after authoring (the outstanding-run population is read from the claims directory at witness time, so this list cannot pre-name late claimers); reason: reject unless plan-related per the Review Scope default

## Validation Commands

```bash
bash scripts/check-no-em-dash.sh added-lines --base 2cc52a65632b3ee1db5154ef4135e06c3e237942
bash scripts/scan-public-hygiene.sh
bash scripts/check_maintenance_pins.sh
python3 scripts/skill_text_budget.py --check
```

Validation preamble (authoring-time record, rule 29; per-round state lives in the review series):
- pending first authored bytes; the battery runs at the pre-review sweep boundary and its outcomes are recorded here

### Task 1: Record D-18 in the directives home

Context surface: the plan's Terms, this task.

Files:
- `docs/maintenance/operator-directives.md`

- [x] The home carries record D-18 (indefinite loop operation; every exit arms the successor or records the exemption) in the home's record format: issued 2026-11-10, status active, expiry: none (standing direction), scope, directive, superseded_by: none, witness [class: IMPLEMENTATION_REQUIRED]
- [x] D-18's scope covers every maintenance session exit, both lanes, dispatched and in-session forms [class: IMPLEMENTATION_REQUIRED]
- [x] D-18's directive body pins the exit tokens: continue per D-17 (no exit); `loop-exit:queue-empty` stop; `loop-exit:quota-wall` pause arming the reset-anchored successor at the probe's reset_at_epoch plus the standing arming margin before stopping; `loop-exit:blocked-retry` stop arming one bounded retry successor through the occupied-lane chaining duty's arm shape and coverage consult [class: IMPLEMENTATION_REQUIRED]
- [x] D-18 pins the retry successor's re-deriving payload (re-derives the block from disk first) and the consecutive-blocked cap: after two consecutive blocked retries over the same block the session parks for the operator and records `loop-exit:operator-park`; no exit leaves the loop without an armed carrier or a recorded exemption [class: IMPLEMENTATION_REQUIRED]
- [x] D-18 pins `loop-exit:operator-stop`: an explicit current stop request or pause order still stops without arming (D-17 preserved) and records `loop-exit:operator-stop` with the operator's stop reason [class: IMPLEMENTATION_REQUIRED]
- [x] D-18 pins the recorded population, matching the token taxonomy: the five token classes record the loop-carrier exit events; a unit completion whose lane continues under D-17 or the parent's cadence and a deferral whose coverage consult found a standing carrier are recorded exemptions - the loop-liveness line names the standing carrier with the exemption noted; the automation-cap ladder-terminal park is a `loop-exit:operator-park` instance [class: IMPLEMENTATION_REQUIRED]
- [x] D-18 pins the loop-liveness binding: the closing report's `loop-liveness:` line names the exit token (or the standing carrier, for a recorded exemption) and the armed carrier's id and fire time; the record adds no automation primitive, schema field, or gate, citing the arming shapes by reference [class: IMPLEMENTATION_REQUIRED]
- [x] D-18 adds no supersession: D-17 and D-6 stay unedited; the D-18 body states its extension relation to D-17 in one sentence; its witness section carries one-line citations only (the stand-down, the two origin rows, commit 55d7a3c9c) [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: record D-18 no-dark-exit standing direction` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Record D-19 in the directives home

Context surface: the plan's Terms, this task, Task 1's record.

Files:
- `docs/maintenance/operator-directives.md`

- [x] The home carries record D-19 (standing direction for decayed foreign staged log residue) in the home's record format, scoped to the Write boundary rule's operator-direction clause in both rolling prompt logs and every session its refusal stops; the record cites the rule by label only, never by file path [class: IMPLEMENTATION_REQUIRED]
- [x] D-19's directive body pre-gives the direction for a staged path meeting all six conditions checked from disk, pinned: (1) the primary done lock reads free and stays held by this session through the remedy; (2) the staged delta against HEAD adds lines only; (3) the path's worktree bytes equal its staged blob [class: IMPLEMENTATION_REQUIRED]
- [x] D-19's condition (4) pinned: the worktree file mtime is at least one cadence period (2 hours) old [class: IMPLEMENTATION_REQUIRED]
- [x] D-19's condition (5) pinned, the match predicate explicit: each claims-directory file with a fresh `updated:` has its `item:` field (authoring claims) or `plan:` field (execution claims) compared against the slugs and basenames the delta's added lines reference; a match or an unparseable claim file keeps the operator gate (fail-closed); every `Frozen:` line inside the delta resolves to no live session [class: IMPLEMENTATION_REQUIRED]
- [x] D-19's condition (6) pinned as a disk-readable entry-structure check: the delta's added lines form exactly one complete entry section of the destination log per its Standing rules - one `## <slug>` heading and its body, no Standing rules line added, removed, or amended, no receipt line touched outside the entry - read from the staged diff against a fresh read of the log [class: IMPLEMENTATION_REQUIRED]
- [x] D-19 orders the remedy run as the rule writes it at execution time, with the pre-image and landed blob shas recorded in the report and turn record and the record named; any failing condition keeps the ordinary operator gate; the 2026-11-02 blob-preservation guarantees apply to every application [class: IMPLEMENTATION_REQUIRED]
- [x] D-19 adds no supersession: D-9 stays unedited; the D-19 body states its extension relation to D-9 in one sentence; its witness section carries one-line citations only (the same arc, the origin row, D-9) [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: record D-19 decayed-residue standing direction` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Bind the router to the records and run the validation battery

Context surface: the plan's Terms, this task, `## Standing constraints`.

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/duties-core.md`
- `agents/skills/maintenance/CHANGELOG.md`

- [x] The Cycle gate paragraph's loop-ending sentence is extended in place: after the sentence naming explicit stops, the primary quota pause, and the empty queue as loop-ending, one added sentence binds D-18 - a blocked stop arms the bounded retry successor, the quota pause arms the reset-anchored successor at reset+margin before stopping, and no exit ends the loop without an armed carrier or a recorded exemption [class: IMPLEMENTATION_REQUIRED]
- [x] The Invariants section gains one bullet naming the no-dark-exit duty (D-18): every token-class exit records its loop-exit token in the turn's decision_reason or the closing report, every standing-carrier exemption D-18 pins rides the closing loop-liveness line, and that line names the token or the standing carrier plus the armed carrier's id and fire time [class: IMPLEMENTATION_REQUIRED]
- [x] The Step 0 Operator directives home read bullet gains one clause: a session meeting a refusal whose remedy is gated on operator direction reads the home before standing down, and a standing direction recorded there for the refusal's class (D-19 for a decayed foreign staged log path) is that direction, its conditions checked from disk before any application [class: IMPLEMENTATION_REQUIRED]
- [x] The duties-core intro paragraph gains one sentence, the dispatched-child twin of the Step 0 clause: before standing down or parking on any refusal whose remedy gates on operator direction, the child reads the directives home; a standing direction recorded there for the refusal's class (D-19 for a decayed foreign staged log path) is that direction, its conditions checked from disk before any application [class: IMPLEMENTATION_REQUIRED]
- [x] The duties-core intro paragraph gains a second sentence, the dispatched-child twin of the Invariants bullet: the child's closing report carries the loop-liveness line D-18 orders, naming the exit token or the standing-carrier exemption and the armed carrier's id and fire time, so the no-dark-exit recording duty reaches dispatched children [class: IMPLEMENTATION_REQUIRED]
- [x] Each touched skill file stays within its cap: the budget check in check mode exits clean, and any growth beyond remaining headroom is paid in the same edit by relocating dated provenance parentheticals to the maintenance CHANGELOG with a matching CHANGELOG entry [class: REPOSITORY_TEST]
- [x] Coordination witness: the branch diff names none of the owned paths recorded in any docs/tmp/execution-claims/*-admission.json present at witness time (the records are the authoritative enumeration; the Standing constraints restatement is its authoring-time copy), verified by git diff --name-only against the base recorded in Validation Commands [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the full Validation Commands battery exits 0 from the placement root over the branch delta [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: bind router to D-18 exit duty and D-19 standing direction` [class: IMPLEMENTATION_REQUIRED]
