# Plan: Recurrence-note promotion for covered-pending-execution plans

Backlog origin: docs/history/backlog/2026-11-08-recurrence-during-pending-execution-unrecorded.md
Cluster: docs/history/plans/completed/2026-11-07-admission-conservative-block-stalls-nonstop-loop.md (the executed covering plan whose witnessed harm's recurrence went unrecorded; it owns the refusal mechanism itself, deliberately not consumed here, see Out of scope)
Required agent type: none (runtime-neutral)
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-11-09-plan-review-recurrence-during-pending-execution-unrecorded-p044d7457-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1h total, largest task 0.5h
Executed: yes (54d8bbf1c)
Authoring claim: 2026-11-08-recurrence-during-pending-execution-unrecorded.md (session sess_51c7ea68-4969-42a5-bd57-02eb8fc9d985)

## Terms

- execution pick: the exec lane's plan selection (the `D1` bullet and the Exec-mode selection rule in `agents/skills/maintenance/decisions.md`), which orders dispatchable open plans and dispatches the most urgent.
- origin row: a backlog item file under `docs/history/backlog/`; a plan's `Backlog origin:` header line names exactly one.
- covered-pending-execution: a landed covering plan whose origin row still waits for its execution landing; the row's `Status:` witness reads the covered-pending-execution token (or the later covered form) while the plan header reads `Executed: no`.
- `Recurrence:` line: the one-line note this plan defines on an origin row, `Recurrence: <YYYY-MM-DD> <witness pointer>`, one line per witnessed recurrence event of the covering plan's incident class.
- witness pointer: a durable record of the recurrence event (a session record, stand-down report, or memory entry path); never session chat text.
- promotion: the `D1` arm this plan adds: a noted plan orders ahead of same-age peers without a note, behind the existing precedence and checks.
- same-age peers: the plans a candidate is otherwise ordered against by the age-based orderings (the oldest-basename ordering and its digest-intact class).
- digest-intact: the `D1` ordering's freshness class; a plan whose bytes still re-hash to its latest ready review digest dispatches without re-certification.
- oldest-basename ordering: the `D1` age ordering: the oldest basename among digest-intact plans, otherwise the oldest open plan.
- fresh-plan continuation preference: the `D1` arm that selects the latest authoring completion's freshly landed plan ahead of the memory dependency-chain ordering.
- memory dependency-chain order: the first plans ordering when the memory index marks chains; the promotion never overrides it.
- skip class: a `D1` exclusion reason (dependency-blocked, externally gated, fresh-execution-claim, agent-type-affinity, parked-dependency); the promotion bypasses none. (The exec rule's machinery-quarantine exclusion applies to ad-hoc items and entries, never to plans in the D1 ordering.)
- `decision_reason`: the scheduler state file's per-turn decision record; the promotion records its firing there.
- Backlog capture: receiving-review's backlog filing section (`agents/skills/receiving-review/SKILL.md`, "Backlog capture for valid findings not fixed in scope"); the note convention's single home.
- Executed-field dispatch input: the decisions.md input that filters candidate plans by their header `Executed:` field; executed plans never reach the candidate set the promotion orders.

## Why

When a landed plan's witnessed incident class recurs while the plan waits in the covered-pending-execution queue, nothing records the recurrence on any surface the execution pick reads: the evidence lives in separate sessions' records and the queue position stays unchanged. The conservative-admission refusal recurred on three consecutive days while both covering plans sat unexecuted in the same queue. A one-line row note plus one ordering clause makes the recurrence visible at the pick.

## Gist & Examples

TLDR: a `Recurrence:` line on an origin row plus one promotion clause in the execution pick's plans ordering surfaces a covered-pending-execution plan's recurring incident at pick time, for efficiency.

Before: an exec session is stood down by the same conservative-admission refusal for the third day in a row. Its covering plan landed yesterday and sits unexecuted. The pick reads age and dependency marks only, learns nothing about the recurrence, and the harm keeps firing while fixes drain at one to two plans per run.

After: the stand-down session appends `Recurrence: 2026-11-07 <report path>` to the covering row. The next execution pick reads the line, promotes that plan ahead of same-age peers (still behind the queue head, priority, parked-dependency, continuation, and dependency-chain precedence, and through every skip class and gate), and the fix executes before the harm fires again. No new state, ledger, or gate.

## Outcome

Incident recurrence during covered-pending-execution is recorded on the origin row and read by the execution pick, so a recurring harm's covering plan is promoted ahead of same-age peers and executes before the recurrence compounds.

- A witnessed recurrence lands as a `Recurrence:` line on the origin row, written by the witnessing session under the row's existing write conventions.
- The execution pick promotes a noted plan ahead of same-age peers behind every existing precedence, skip class, and gate, recording the promotion in `decision_reason`.
- No state schema, scheduler ledger, gate, validator, or lock is added; the row is the record and the pick already reads rows.

Gate delta: none (a one-line row-note convention and a selection-ordering clause; no refusal class, hard gate, fence, protocol layer, schema field, or dispatch-pausing condition added; the ordering change is a filter input per the Executed-field dispatch input precedent and the entry's Machinery admission paragraph, which names the incident, expected catch, false-positive cost, and the 2027-02-08 review date)

## Assumptions

- Assume the Exec-mode selection rule needs no edit; basis: its ordering contract reads "plans (D1's ordering)" and states "D1's selection priorities carry into the merged set", so the merged urgency set inherits the `D1` arm (source: the rule's Ordering contract sentence in decisions.md, 2026-11-09, affected sections: Task 2 / Standing constraints).
- Assume the promotion is a filter input, not machinery; basis: the Executed-field dispatch input's precedent sentence ("a filter input, not a gate or validator; it adds no refusal path") and the entry's Machinery admission paragraph (source: decisions.md, 2026-11-09, affected sections: Gate delta / Task 2).
- Assume no freshness bound on the note; basis: the origin's Expected names no bound and the row lifecycle bounds it (the fold-and-delete at execution removes the row, and the Executed-field dispatch input already drops an executed plan from the candidate set) (source: origin row Expected and the plans lifecycle, 2026-11-09, affected sections: Task 1).
- Assume plans whose header reads `Backlog origin: none` simply never promote; basis: the plan header's origin line is the only row pointer the pick reads (source: the plans skill Backlog origin bullet, 2026-11-09, affected sections: Task 2 / Terms).
- Origin class consumption receipt: the origin row's `Class:` line reads fix-class; the plan keeps the fix-class shape (it adds a decision-input read and a note convention, no refusal path).
- Growth-payment receipt: both edits reuse existing vocabulary (the same-turn commit duty, the skip-class list, the oldest-basename tiebreak) by reference, add no second home, and carry no incident narrative (the origin row and the entry stay the story's homes); the residual unbalanced byte growth of the two insertions is accepted and recorded here as the review-time payment record.
Decision points requiring a grill: promotion home = the `D1` bullet in `agents/skills/maintenance/decisions.md` as the single home, the Exec-mode selection rule inheriting it by reference with no second copy (source: the rule's "plans (D1's ordering)" reference and the repository anti-growth single-homing rules, 2026-11-09, affected sections: Task 2 / Standing constraints); note-shape home = receiving-review's Backlog capture section as a lifecycle-note paragraph beside the capture-write paragraph, deliberately outside the capture-time required-content list because the note is written when a recurrence is witnessed, not at capture (source: the origin row's Surface line and the section's scope, 2026-11-09, affected sections: Task 1); promotion precedence = behind the queue-head, `execution_priority`, parked-dependency unblock, fresh-plan continuation preference, and the memory dependency-chain order when available, noted plans ahead of the oldest-basename ordering within the digest-intact class, the noted subset keeping the oldest-basename tiebreak (source: entry scope arm 2 and the entry's rejected alternatives, 2026-11-09, affected sections: Task 2); note cardinality = one line per witnessed recurrence event appended, the pick reading presence (source: entry scope arm 1 read against append-only row notes, 2026-11-09, affected sections: Task 1); writer and timing = the witnessing session, only while the covering plan is still unexecuted, a recurrence witnessed after completion routing to a new backlog capture instead (source: entry scope arm 1 and the row lifecycle, 2026-11-09, affected sections: Task 1).

## Standing constraints

- Operative-text anti-growth (repository guidelines): both edits cite existing vocabulary by reference, add no new vocabulary or second home, and carry no incident narrative; the origin row and the PLAN-PROMPTS entry stay the story's homes.
- Single-homing: the note convention lives only in receiving-review's Backlog capture; the promotion clause lives only in the `D1` bullet; each names the other by reference in one line.
- No machinery: no script, state-file field, validator, lock, ledger, or gate changes; `docs/history/backlog/PLAN-PROMPTS.md` and `docs/history/backlog/EXEC-PROMPTS.md` are not edit targets of this plan.
- decisions.md stays runtime-agnostic: no tool names in the inserted arm.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the promotion text names its precedence bounds, its ordering position, the note read path, and the `decision_reason` record; the note convention names the shape, the writer, the timing guard, and the executed-plan routing.
- single-homing: one promotion home in the `D1` bullet; one note home in Backlog capture; each cross-reference is one line.
- minimality: the execution run's changed file set names the two skill files only; no scripts, schema, or state changes.

**Done when:**
- The presence and position witnesses pass from the executing worktree, RED before each task's edit and GREEN after (anchor spans unique, insertions inside the pinned regions).
- The pins suite exits 0, or its only failing pin is the prompt-log all-served stale-entry pin recorded red at this plan's authoring (a foreign rolling-log drift owed the maintenance monitor's prune duty; both named entries predate this plan and neither names this plan's changed files); no pin attributable to this plan's changed files fails.
- The public-hygiene scan and the em-dash added-lines gate each exit 0.
- `python3 scripts/plan_readiness.py docs/history/plans/2026-11-09-recurrence-during-pending-execution-unrecorded.md` exits 0 with the final `OUTCOME: pass` line at execution start, before the first checkbox flip.

**Ship when:**
- The next execution pick that reads a noted row promotes that plan ahead of same-age peers and records the promotion in `decision_reason` (live-behavior evidence; prose only).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Docs and skill text:**
- `agents/skills/receiving-review/SKILL.md` (Task 1)
- `agents/skills/maintenance/decisions.md` (Task 2)

**Tests:**
- (none added; verification is the presence and position witnesses plus the repository's standing suites under Validation Commands)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/state-file.md` and any `scripts/` code; reason: no state schema or code change (entry scope arm 3).
- The `D1` skip classes, the fresh-plan continuation preference, and the memory dependency-chain ordering; reason: the promotion sits behind them and must not restate or retighten them.
- `docs/history/backlog/PLAN-PROMPTS.md` and `docs/history/backlog/EXEC-PROMPTS.md`; reason: the rolling logs' writes follow the logs' own Standing rules, never this plan.
- `docs/history/plans/completed/2026-11-07-admission-conservative-block-stalls-nonstop-loop.md` and `docs/history/backlog/2026-11-06-raced-pick-ordering-precedence-tension.md` (the Cluster rows); reason: the executed covering plan owns the refusal mechanism and the ordering-precedence family is adjacent, neither consumed here.
- The two stale PLAN-PROMPTS entries the authoring run recorded (backlog-completed-dir-regrowth, test-suite-runtime-residual-optimization-path); reason: their prune is the maintenance monitor's duty (omit-extension), never this plan's edit.

## Validation Commands

Authoring-time record (rule 29 preflight, run over the plan bytes before the first review round; outcomes recorded here at authoring): see the Validation preamble paragraph below.

```bash
# Presence and position witnesses (Tasks 1-2), from the executing worktree root.
# RED before the matching task's edit, GREEN after:
python3 -c 'import sys; s=open("agents/skills/receiving-review/SKILL.md").read(); a=["The capture write carries a same-turn commit duty","### Backlog driving-force taxonomy"]; p=[s.find(x) for x in a]; assert -1 not in p, "anchor missing: %r" % (p,); assert all(s.count(x)==1 for x in a), "anchor not unique"; start,tax=p; f=s.find("`Recurrence:` lifecycle note", start); assert 0 < f < tax, "note paragraph not between the capture-write paragraph and the taxonomy heading (count today: %d)" % s.count("`Recurrence:` lifecycle note"); print("recurrence-note witnesses pass")'
python3 -c 'import sys; s=open("agents/skills/maintenance/decisions.md").read(); a=["Fresh-plan continuation preference (added 2026-09-28","Needs-recert dispatchability (added 2026-09-24"]; p=[s.find(x) for x in a]; assert -1 not in p, "anchor missing: %r" % (p,); assert all(s.count(x)==1 for x in a), "anchor not unique"; cont,recert=p; f=s.find("Recurrence-note promotion", cont); assert 0 < f < recert, "promotion arm not between the continuation preference and needs-recert (count today: %d)" % s.count("Recurrence-note promotion"); print("promotion-arm witnesses pass")'
# Standing gates, from the executing worktree root:
bash scripts/check_maintenance_pins.sh
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base <base-ref>   # <base-ref> = the execution run's base commit
python3 scripts/plan_readiness.py docs/history/plans/2026-11-09-recurrence-during-pending-execution-unrecorded.md
```

Validation preamble (authoring-time outcomes, recorded per validation rule 29; updated in place as boundaries run):
- rule 19 RED-today evidence (2026-11-09, worktree reads at the authoring base c75bbee65): the recurrence-note witness exits non-zero with "note paragraph not between the capture-write paragraph and the taxonomy heading (count today: 0)" and the promotion-arm witness exits non-zero with "promotion arm not between the continuation preference and needs-recert (count today: 0)", so both gates fire before their edits and can only turn GREEN through Tasks 1-2's insertions; all four anchor spans verified unique in their target files.
- pins suite at the authoring base: exit 1 with exactly one failing pin, "prompt log has no all-served (stale) entry" (two stale PLAN-PROMPTS entries whose prunes are owed the maintenance monitor's rolling prompt log duty; both entries predate this plan and neither names this plan's changed files); recorded as the pre-existing baseline this plan's Done-when arm excepts.
- public-hygiene scan: OUTCOME: pass (2026-11-09, worktree root).
- em-dash scan (touched, plan bytes): OUTCOME: pass, 0 substitutions (fixer and gate).
- readiness `--pre-round`: OUTCOME: pass (structural checks clean; the one advisory FILES-COVERAGE warning class adjudicated: Task 3's verification commands are single-homed in this block, and the sibling-declared path reads are read-only verification over Tasks 1-2's edits, correctly undeclared in Task 3's Files: list).

### Task 1: Recurrence note convention in Backlog capture

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/receiving-review/SKILL.md`

- [x] In the "Backlog capture for valid findings not fixed in scope" section, insert the lifecycle-note paragraph (the paragraph contains the exact literal `` `Recurrence:` lifecycle note ``, the span the presence witness finds) immediately after the paragraph beginning "The capture write carries a same-turn commit duty" and before the "### Backlog driving-force taxonomy" heading; both quoted anchors survive verbatim [class: IMPLEMENTATION_REQUIRED]
- [x] The paragraph defines the `Recurrence:` line shape, `Recurrence: <YYYY-MM-DD> <witness pointer>`, one line per witnessed recurrence event appended to the row, the witness pointer naming a durable record of the event (a session record, stand-down report, or memory entry path), never chat text [class: IMPLEMENTATION_REQUIRED]
- [x] The writer and timing guard: the session that witnesses the recurrence writes the line as one targeted append under the same-turn commit duty above, only while the covering plan header's `Executed:` field is not a literal `yes (<recorded tip>)` (the Executed-field dispatch input's field semantics: a missing field reads pending) [class: IMPLEMENTATION_REQUIRED]
- [x] The executed routing: a recurrence witnessed when that field reads the executed literal routes to a new backlog capture instead, never a row note [class: IMPLEMENTATION_REQUIRED]
- [x] The reader pointer: one closing line names the execution pick's promotion input (the `D1` bullet's recurrence-note promotion in the maintenance decisions), no mechanics restated [class: IMPLEMENTATION_REQUIRED]
- [x] Presence witness (RED before, GREEN after, from the executing worktree): the Validation Commands block's recurrence-note gate exits 0 (first occurrence between the capture-write paragraph and the taxonomy heading; both anchor spans unique) [class: REPOSITORY_TEST]
- [x] Commit: `wip: recurrence note convention in Backlog capture` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Recurrence-note promotion arm in the D1 bullet

Context surface: the plan's Terms, Task 1's note convention, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/decisions.md`

- [x] In the `D1 (execute)` bullet, insert the promotion arm (the arm opens with the exact literal `Recurrence-note promotion`, the span the presence witness finds) immediately after the fresh-plan continuation preference sentence (the sentence ending "the preference is recorded in `decision_reason` when it fires") and before "Needs-recert dispatchability"; the two witness anchors from the Validation Commands block survive verbatim [class: IMPLEMENTATION_REQUIRED]
- [x] The arm's opening names itself `Recurrence-note promotion (added 2026-11-09, the recurrence-during-pending-execution-unrecorded plan):`, matching the bullet's existing "(added <date>, <source>)" naming convention [class: IMPLEMENTATION_REQUIRED]
- [x] The arm names its precedence bounds: behind the queue-head, `execution_priority`, parked-dependency, and fresh-plan continuation precedence, and never ahead of the memory dependency-chain order when it is available; the promotion bypasses no skip class, the certification oracle, the quota leg, the landing gate, or the rate-pressure condition [class: IMPLEMENTATION_REQUIRED]
- [x] The arm states the ordering position: within the digest-intact class the noted plans read ahead of the oldest-basename ordering, the noted subset keeping the same oldest-basename tiebreak [class: IMPLEMENTATION_REQUIRED]
- [x] The arm states the read path and record: the `Recurrence:` line is read at selection time from the origin row named by the plan's `Backlog origin:` header (a plan without that line never promotes); the note's shape and write duty cited to receiving-review's Backlog capture by reference; the promotion recorded in `decision_reason` when it fires [class: IMPLEMENTATION_REQUIRED]
- [x] One arm line states the exec lane's merged urgency set inherits the promotion through the Exec-mode selection rule's "plans (D1's ordering)" reference, foreclosing an exhaustive reading of the rule's carry enumeration [class: IMPLEMENTATION_REQUIRED]
- [x] Presence witness (RED before, GREEN after, from the executing worktree): the Validation Commands block's promotion-arm gate exits 0 (first occurrence between the continuation preference and needs-recert; both anchor spans unique) [class: REPOSITORY_TEST]
- [x] Commit: `wip: recurrence-note promotion arm in the D1 bullet` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Standing gates and unchanged-surface verification

Context surface: the plan's Terms, Tasks 1-2's edits, and `## Standing constraints`.

Files:
- (none; read-only verification over Tasks 1-2's changes)

- [x] From the executing worktree run the Validation Commands block's standing gates: the pins suite per the Done-when arm (exit 0, or only the recorded foreign stale-entry pin failing) and the public-hygiene scan exit 0 [class: REPOSITORY_TEST]
- [x] Run the Validation Commands block's em-dash added-lines gate over the run's change with the execution run's base commit; expect exit 0 [class: REPOSITORY_TEST]
- [x] Changed-file-set witness: `git diff --name-only <base-ref>..HEAD` names `agents/skills/receiving-review/SKILL.md` and `agents/skills/maintenance/decisions.md` only, proving every other surface byte-unchanged [class: REPOSITORY_TEST]
- [x] At execution start, before the first checkbox flip, the Validation Commands block's readiness invocation exits 0 with the final `OUTCOME: pass` line [class: REPOSITORY_TEST]
