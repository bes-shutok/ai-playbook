# Plan: claimed-top-target skip-and-continue in exec-mode selection

Backlog origin: docs/history/backlog/2026-11-05-twin-standdown-skips-next-candidate.md
Driving force: efficiency
Plan review record: the staging series {reviews_dir}/2026-11-05-plan-review-claimed-top-target-skip-and-continue-p<identity-token>-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1.25h total, largest task 0.5h
Executed: yes (a5ebd9172)
Authoring claim: 2026-11-05-twin-standdown-skips-next-candidate.md (session sess_7af47cd4-f4c8-474d-9fc0-e4c56c7ea248)

Execution record: the implementation (Tasks 1-3) landed to main in squash a5ebd9172 by the 2026-11-06 execution run (see that landing commit for the full record); commit 2a1781a5c then reopened the archived plan because its archived bytes still carried Executed: no and unchecked boxes; this pass closes the reopened lifecycle: checkbox marks, the Executed flip citing the landed execution commit, and the archive. Task validations re-verified on the current tree: pinning suite 7 passed, hygiene exit 0, byte-budget gate exit 0 (pins suite carries a pre-existing main baseline red: two STALE PLAN-PROMPTS entries owned by other open plans, unchanged by this plan).

## Terms

- Claimed top target: the exec-mode selection's current best open plan whose fresh execution claim names a live foreign session.
- Skip-and-continue: the selection records the collision, skips the claimed target, and continues to the next eligible candidate under the same mandate cap.
- Target-disjoint candidate: a candidate whose owned-path set shares no repository path with any outstanding run's owned-path set, judged with the dispatch admission consult's semantics by reference.
- Owned-path set: the repository paths a run claims as its own edit surface, derived pre-run from the covering plan's `Files:` lists, and from the done-setup manifest once a run exists.
- Dispatch admission consult: the target-disjointness check in `scripts/dispatch_admission.py` (`check_admission`), reused here as the naming home of the judgment's semantics by reference, never invoked in the selection path.
- Full stand-down: the run ends with zero executions under its mandate instead of picking another candidate.
- Twin-standdown convention: the memory-only precedent that a session whose top target is claimed stands down beside any claimed top target; superseded by this arm for the target-disjoint case.
- D1 selection: the execution-lane plan-selection bullet `D1 (execute)` in `agents/skills/maintenance/decisions.md`, the arm's one home.
- decision_reason: the scheduler state file's per-decision record field where skips, pops, and collisions are recorded.
- Fresh-claim skip: D1's existing skip of a plan whose fresh execution claim names a foreign session.
- Stale-claim takeover: the claim protocol's path that lets a session take over a claim stale past one cadence period.
- Survey-only flag: the scheduler state file's incident `survey_only` operator stop switch.
- Carrier window: one fired carrier run's execution window; the resource wasted when a run executes nothing.
- execution_queue: the scheduler state file's explicit execution-order queue whose head is the selection candidate.
- Held-candidate fall-through: the Exec-mode selection rule's clause that continues the turn to the next urgency-ordered candidate while one is held.
- Mandate cap: the operator ask's total-execution count limit (for example "at most 1"), which bounds how many plans a run executes, never which one.
- Pay-for-growth fold: the review-time discipline that pays added operative text with an equivalent deletion in the same change.
- Covered flip: the landing-time edit that marks a backlog origin row `Status: covered (<plan path>)`.
- Byte-budget gate: the warning-only per-file byte-budget check (`scripts/skill_text_budget.py`) whose breach report records growth debt.
- Done-setup manifest: the per-run manifest the done skill writes at run setup, from which a run's owned paths resolve once it exists.

## Why

The D1 selection already continues past a fresh-claimed plan while something remains, but the continuation carries no disjointness qualifier, no explicit stand-down enumeration, and no supersession of the memory-only twin-standdown convention; a witnessed exec run (2026-11-05 00:42 WET one-shot) misapplied that convention as a fleet-wide stand-down and ended 0/1 while target-disjoint candidates and operator budget remained. The convention lives only in session memory, so each session re-derives its scope and the over-broad stand-down is its natural failure mode; the wasted carrier window is the witnessed cost.

## Gist & Examples

TLDR: the D1 selection gains the claimed-top-target skip-and-continue arm, so an exec-mode session whose top plan carries a fresh foreign claim records the collision and continues to the next eligible candidate that is target-disjoint against every outstanding run, under the same mandate cap, and the memory-only convention is superseded in skill text.

Before (today): the D1 selection skips a fresh-claimed plan and continues while candidates remain, but the continuation states no disjointness judgment, no queue-head interaction, no pre-dispatch re-check, and no resolution for an ambiguous operator ask; the memory-only twin-standdown convention fills that silence and over-generalizes to a full stand-down.

After (this plan): the arm records the collision, pops a claimed `execution_queue` head like an invalid head, and continues the scan to the next candidate judged target-disjoint against every outstanding run's owned-path set with the consult's semantics (exact `Files:`-span intersection, the done-setup manifest once a run exists, the conservative same-target verdict on empty or underivable sets), re-reads the chosen candidate's claim state immediately before dispatch, resolves an ask's target scope only from named targets (a count cap is never a target scope), and holds under the arm's own stand-down conditions when nothing eligible remains; an admission-refused candidate is a recorded hold and the scan continues past it.

Example: a one-shot exec mandate (urgency order, at most 1, stop after the first) finds its top plan claimed at selection time by a live sibling; the session records the collision, pops the claimed queue head, selects the next candidate whose `Files:` spans intersect no outstanding run, re-checks the candidate's claim immediately before dispatch, and executes it under the same one-plan cap instead of standing down 0/1.

Edge cases: a same-target second session still refuses exactly as today (the fresh-claim skip and the stale-claim takeover semantics are unchanged; the arm adds only the complement); a queue emptied by the skips ends in the arm's own stand-down hold when no outstanding run stands, and hands the lane to the landing-completion resolution per the existing landing-gate refusal rule when one does, alongside the existing fall-through for the enumerated skip classes; a fleet or quota cap, rolling rate pressure, or a standing survey-only flag binds exactly as today and is a valid full stand-down; an operator ask that names one target does not continue past that target's claim, while a count cap ("at most 1") never scopes the run to a target; a candidate claimed between selection and dispatch is caught by the pre-dispatch claim re-check and the scan continues.

## Outcome

An exec-mode session whose top target is claimed by a live peer continues to eligible target-disjoint work under its unchanged mandate, and the deconfliction rule lives in skill text instead of session memory.

- A claimed top target no longer produces a 0/1 stand-down while target-disjoint candidates remain, in both the deciding-turn selection and the queue-head path.
- The collision, the queue-head pop, and the continuation are recorded in the deciding session's `decision_reason`.
- The stand-down conditions (exhausted queue, binding cap, named single-target ask) are enumerated in the rule itself.
- The memory-only twin-standdown convention is superseded by this arm for the target-disjoint case, its same-target collision refusal preserved.
- Gate delta: none (no gate, validator, lock, ledger, or fence added or removed; the arm relocates an existing decision rule from memory into skill text and cites the admission consult's semantics by reference, per the served PLAN-PROMPTS entry's "Machinery admission:" record for twin-standdown-skips-next-candidate, which states the protocol's admission fields do not apply).

## Assumptions

- assume the fresh-foreign-claim refusal stays in force with unchanged semantics; the D1 sentence that carries it is reworded by the pay-for-growth fold, so the refusal's behavior is unchanged while that sentence's bytes change; basis: the served PLAN-PROMPTS entry's "Continuity disposition:" record for twin-standdown-skips-next-candidate keeps it because same-target double execution is the witnessed harm.
- assume target disjointness is judged with the dispatch admission consult's semantics by reference, never by invoking the script in the selection path; basis: the served PLAN-PROMPTS entry's "Scope:" record for twin-standdown-skips-next-candidate and the skill-text anti-growth rules.
- assume the arm lands inside the existing D1 selection bullet in `agents/skills/maintenance/decisions.md` (its one home) and names the Exec-mode selection rule's Held-candidate fall-through as a consumer, so both continuation statements compose; basis: the origin row's `Skill/step:` field and the exec bullet's own Held-candidate fall-through text.
- assume the memory supersession is a run-owned record in the maintenance skill's persistent project memory index, outside this repository, and therefore carries no repo diff beyond the origin row's covered flip; basis: the origin row's `## Problem` section (the convention lives only in session memory).
- assume text-pinning regression coverage is the right test shape for a Markdown policy rule, scoped to the owning D1 bullet span rather than file-wide; basis: `scripts/test_maintenance_runtime_scope.py`'s stated convention (policy authored as Markdown, pinned by normative tokens inside the owning bullet).

Decision points requiring a grill: none remain (all resolved by recorded receipt under the maintenance-selected standing authorization; arm placement, stand-down conditions, and reference-not-invocation resolution fixed by the served PLAN-PROMPTS entry's "Scope:" and "Continuity disposition:" records for twin-standdown-skips-next-candidate).
Scope extensions (grilled): none proposed.
Sources inspected: not a tracker-linked request.

## Standing constraints

- Machinery admission protocol: the arm adds no gate, validator, lock, ledger, or fence; it relocates an existing decision rule from memory into skill text (the served PLAN-PROMPTS entry's "Machinery admission:" record for twin-standdown-skips-next-candidate states the protocol's admission fields do not apply).
- Same-target protection preserved: the fresh-claim skip and the stale-claim takeover keep their semantics; the arm adds only the skip-and-continue complement for remaining candidates.
- Skill-text anti-growth: the arm cites the admission consult's semantics by reference, never restates its procedure, and folds the fresh-claim skip's takeover cross-reference instead of restating it; the byte-budget gate over `agents/skills/maintenance/decisions.md` must pass after the arm lands.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the arm fires exactly when the selection's top candidate carries a fresh foreign claim, composes with the queue-head pop rule and the Exec-mode selection rule's fall-through, and never weakens the same-target refusal
- completeness: all three full-standdown conditions are enumerated in the arm text, the disjointness judgment carries the consult's conservative defaults, and the pre-dispatch claim re-check closes the selection-to-dispatch race
- economy: the consult's semantics are cited by reference; the D1 bullet grows by the arm's net delta minus the folded takeover tail, with the byte-budget gate's breach report standing as the record (warning-only posture)

**Done when:**
- the claimed-top-target skip-and-continue arm exists in the D1 selection rules with the stand-down conditions, the queue-head pop, the disjointness defaults, the pre-dispatch re-check, and the supersession clause
- the text-pinning suite passes against the amended skill text, region-scoped to the D1 bullet
- the maintenance pins suite and the hygiene scan exit 0, and the byte-budget gate runs with its breach report recorded (warning-only)
- the memory index entries carrying the twin-standdown convention state the supersession pointer

**Ship when:**
- none stated (repository-verifiable work only; the memory amendment is run-owned bookkeeping verified by read-back)

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Docs:**
- `agents/skills/maintenance/decisions.md` (Task 2)
- `docs/history/backlog/2026-11-05-twin-standdown-skips-next-candidate.md` (Task 3) *(coverage flip rides the landing)*

**Tests:**
- `scripts/test_claimed_target_skip_and_continue.py` (Task 1) *(new)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/template-execution.md`; reason: its successor-dispatch duty selects its target by the D1 rule, whose skip classes this arm extends, so the landed arm is inherited there without editing that file
- `scripts/dispatch_admission.py`; reason: reused as the naming home of the judgment's semantics by reference, never modified or invoked in the selection path
- `agents/skills/maintenance/guards.md`; reason: the lane occupancy guards are unchanged by this arm

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_claimed_target_skip_and_continue.py -q
bash scripts/check_maintenance_pins.sh
bash scripts/scan-public-hygiene.sh
python3 scripts/skill_text_budget.py --check
```

### Task 1: Regression coverage pinning the claimed-top-target skip-and-continue arm

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_claimed_target_skip_and_continue.py` *(new)*

Primary class anchors:
- `Claimed-top-target skip-and-continue` in `agents/skills/maintenance/decisions.md`

- [x] New unittest suite following `scripts/test_maintenance_runtime_scope.py`'s stated convention (a Markdown policy pinned by normative tokens inside the owning bullet's span): extract the `D1 (execute)` bullet from `agents/skills/maintenance/decisions.md` with a `bullet()`-style helper and assert the arm's tokens inside that span: the arm name "Claimed-top-target skip-and-continue" and the origin citation "the twin-standdown-skips-next-candidate origin row" [class: REPOSITORY_TEST]
- [x] The same suite asserts, inside the D1 bullet span: the supersession clause "superseded by this arm", the arm's own by-reference citation span "invoked nowhere in the selection path", and the admission-consult reference "scripts/dispatch_admission.py" [class: REPOSITORY_TEST]
- [x] The same suite asserts, inside the D1 bullet span, the remaining arm tokens: the cap clause "under the unchanged mandate cap", a cap-bind span ("a cap binds"), the stand-down conditions "no eligible candidate remains" and "the operator ask's own wording scopes the run to that one target", and the quoted spans "immediately before dispatching the continuation candidate" and "a count cap being a mandate cap never a target scope" [class: REPOSITORY_TEST]
- [x] The same suite also asserts, inside the D1 bullet span, the carve-out spans "no eligible candidate remains and no outstanding run stands" and "hands the lane to the landing-completion resolution" and the exemption span "a disjointness-refusal reason" [class: REPOSITORY_TEST]
- [x] The same suite also asserts, inside the D1 bullet span, the quoted Task 2 spans "a claimed `execution_queue` head pops" and "the conservative same-target verdict when a set is empty or underivable" and "re-reads its execution-claim state" [class: REPOSITORY_TEST]
- [x] The same suite also asserts the folded takeover token "stale-claim takeover left to the claim protocol" exactly once in the D1 bullet and positionally inside the arm (an index-order assertion from the arm-name span to the takeover token, the reference suite's `assertLess` pattern) [class: REPOSITORY_TEST]
- [x] The same suite finally asserts the preserved fresh-claim skip tokens "naming a foreign session" and "the skip recorded in `decision_reason`" still present in the D1 bullet [class: REPOSITORY_TEST]
- [x] Run → expect RED: the suite fails at the current tree because every span-scoped assertion of an arm-unique token fails inside the D1 bullet; the admission-consult reference pin is a persistence pin expected to pass at RED [class: REPOSITORY_TEST]
- [x] Commit: `test: pin claimed-top-target skip-and-continue arm tokens` [class: IMPLEMENTATION_REQUIRED]

### Task 2: The claimed-top-target skip-and-continue arm in the D1 selection rules

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/decisions.md`

Primary class anchors:
- `D1 (execute)` in `agents/skills/maintenance/decisions.md`

- [x] Insert the claimed-top-target skip-and-continue arm as its own dated sentence in the D1 selection bullet, immediately after the fresh-execution-claim skip text: the collision recorded in `decision_reason` naming the claimed plan and the claim's session id; a claimed `execution_queue` head pops with the pop recorded like an invalid head; the scan continuing to the next eligible candidate judged target-disjoint against every outstanding run's owned-path set [class: IMPLEMENTATION_REQUIRED]
- [x] The arm judges disjointness with the dispatch admission consult's semantics by reference (`scripts/dispatch_admission.py` `check_admission` names the vocabulary, invoked nowhere in the selection path; no new ledger, gate, or validator): exact set intersection over the backticked repo-path spans of the plans' `Files:` lists, the done-setup manifest read once a run exists, and the conservative same-target verdict when a set is empty or underivable [class: IMPLEMENTATION_REQUIRED]
- [x] The judgment and the scan run all under the unchanged mandate cap (the arm changes which candidate consumes the slot, never how many); an admission-refused candidate is a recorded hold for the turn and the scan continues past it [class: IMPLEMENTATION_REQUIRED]
- [x] The arm's holds and stand-down record under a named sanctioned must-dispatch exemption reason joining D1's exemption enumeration (a disjointness-refusal reason; the claimed-target skip riding the existing fresh-execution-claim reason), and when every remaining candidate is admission-held while an outstanding run stands, the lane resolves to the landing-completion work per the existing landing-gate refusal rule [class: IMPLEMENTATION_REQUIRED]
- [x] The arm closes the selection-to-dispatch race and fixes the ask-scope reading: immediately before dispatching the continuation candidate the session re-reads its execution-claim state and a claim appearing after selection records the new collision and continues the scan; an ask scopes the run to one target only when its wording names that target or an explicit target set, a count cap being a mandate cap never a target scope [class: IMPLEMENTATION_REQUIRED]
- [x] The arm enumerates the full-standdown conditions: no eligible candidate remains and no outstanding run stands (the arm's own hold governs the pass-over class; an outstanding run standing hands the lane to the landing-completion resolution per the existing landing-gate refusal rule), a cap binds (the fleet cap, the quota leg, rolling rate pressure, or the state's survey-only flag), or the operator ask's own wording scopes the run to that one target [class: IMPLEMENTATION_REQUIRED]
- [x] The arm states the Exec-mode selection rule's Held-candidate fall-through continues through this skip only to a target-disjoint candidate [class: IMPLEMENTATION_REQUIRED]
- [x] The arm cites its origin ("the twin-standdown-skips-next-candidate origin row"), records the memory-only twin-standdown convention as superseded by this arm for the target-disjoint case, and keeps the same-target collision refusal in force as the fresh-claim skip itself with the takeover cross-reference folded into that clause [class: IMPLEMENTATION_REQUIRED]
- [x] Pay for growth: fold the fresh-claim skip sentence's takeover cross-reference ("with the stale-claim takeover left to the claim protocol rather than the selection") into the arm's preserved-refusal clause, so the D1 bullet grows by the arm's net delta minus the folded tail and the takeover rule is stated once [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Task 1 suite passes against the amended text [class: REPOSITORY_TEST]
- [x] Run the maintenance pins suite and the hygiene scan, expects exit 0 on both; run the byte-budget gate over `agents/skills/maintenance/decisions.md` and record its output (the breach report) in the run log, exit 0 expected [class: REPOSITORY_TEST]
- [x] Commit: `docs: add claimed-top-target skip-and-continue arm to exec-mode selection` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Memory supersession record for the twin-standdown convention

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/history/backlog/2026-11-05-twin-standdown-skips-next-candidate.md` *(coverage flip rides the landing)*

- [x] Amend the maintenance skill's persistent project memory index entries carrying the twin-standdown convention (the memory home outside this repository, so this item produces no repo diff): each amended entry contains the literal span "2026-11-05-twin-standdown-skips-next-candidate" and a "D1" literal naming the landed rule, keeping the same-target collision rationale the entries witness [class: IMPLEMENTATION_REQUIRED]
- [x] Read-back verification (manual, receipt recorded in the run log): a fixed-string search over the memory index for both literal spans returns the amended entries; the repository working tree for this task shows only the origin row's covered flip [class: REPOSITORY_TEST]
- [x] Commit: `docs: cover twin-standdown-skips-next-candidate origin row` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

Origin row `docs/history/backlog/2026-11-05-twin-standdown-skips-next-candidate.md` is fully served and is deleted in this completion pass. Witness: its rule body (the claimed-top-target skip-and-continue arm with the enumerated stand-down conditions and the consult-semantics-by-reference judgment) landed to main in squash a5ebd9172 (2026-11-06 execution run; D1 bullet in `agents/skills/maintenance/decisions.md`), with the Task 1 pinning suite `scripts/test_claimed_target_skip_and_continue.py` (7 tests) and the Task 3 memory supersession record landed run-owned outside the repository; the row's own covered flip, its witnessed catch and false-positive framing, and the 2026-11-04 genuine-cap contrast note are preserved in the row's git history at the deletion's parent commit and summarized in this plan's Why and Gist sections. The 2026-12-05 review-date concern transfers to the landed arm's home text.
