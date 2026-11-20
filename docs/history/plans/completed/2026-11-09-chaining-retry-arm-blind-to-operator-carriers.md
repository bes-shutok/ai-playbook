# Plan: Occupied-lane chaining coverage consult for operator-armed carriers

Backlog origin: docs/history/backlog/2026-11-09-chaining-retry-arm-blind-to-operator-carriers.md
Cluster: docs/history/backlog/2026-11-08-capacity-aware-chaining-phase3-residuals.md (same chaining-duty surface; that row owns the covering plan's plan-text divergence and the 5h-wall arming-edit writer-enumeration gap, each with its own recorded disposition; deliberately not consumed here, see Out of scope)
Required agent type: none (runtime-neutral)
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-09-plan-review-chaining-retry-arm-blind-to-operator-carriers-p102378c7-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 0.5h total, largest task 0.5h
Executed: yes (692bddce8354e4faffc68651d442d06fb45bc12c)
Authoring claim: 2026-11-09-chaining-retry-arm-blind-to-operator-carriers.md (session sess_26d0ec53-4829-4b47-b89a-304b47de25f4)

## Terms

- Occupied-lane chaining duty: the Step 3 bullet in `agents/skills/maintenance/decisions.md` that arms a near-future retry one-shot when a lane decision defers on an occupancy- or lock-shaped reason, and the reset-anchored successor when the quota window fits no other run; this plan's single edit surface.
- near-future retry one-shot: the one-shot that duty arms for a held lane, the slot defaulting to +45 minutes from the decision and never earlier than the freshest blocking claim's likely completion, recorded as a `children[]` entry with the armed automation id.
- reset-anchored successor (the 5h-wall arm): the duty's only cross-window arm; the chain one-shot armed at the quota probe's `reset_at_epoch` plus the standing 10-minute arming margin when the window is unfit for another run.
- coverage consult: the one-listing decision step this plan adds before either arm's create; found in-window coverage records the existing carrier and skips the arm.
- coverage window: the arm's own coverage span. Retry arm: from the decision through the slot the turn would arm (the +45-minute default included). 5h-wall arm: from the decision through the reset-anchored fire time.
- matching record: an ENABLED one-shot in the automation listing whose prompt contains the resolved repository root and carries a lane marker or the scheduler prompt opening, with a fire time inside the coverage window.
- lane marker: the payload-marker spans the runtime overlay's Child classification markers section defines for this repository's lanes; cited by reference, never enumerated in the duty text.
- scheduler prompt opening: the scheduler prompt template's first line ("You are the maintenance scheduler for the repository at"), the recognition span the duplicate-parent tripwire matches; a record of this shape inside the window means the loop itself re-decides the lane inside the span.
- ENABLED repository-contained one-shot: an automation-listing record with enabled true whose prompt contains this repository's resolved root (the containment gate the markers apply).
- refresh-nothing semantics: the bullet's existing standing-retry disposition: refresh nothing, record the existing carrier, never stack a second retry.
- operator-armed carrier: a lane payload an operator schedule ask armed directly; by standing directive such asks run no duplicate-lookup pass and write nothing to the scheduler state file, so no state-file reader can see them.
- park fallback: the bullet's existing decided-but-unschedulable disposition: the turn records the decided retry in `pending_dispatch` with the payload copy per the park-path pairing rule, and the next capable turn's parked-dispatch discharge owns the arm.
- `decision_reason`: the scheduler state file's per-turn decision record; the consult records found coverage there (existing writer shape, no new field).
- `children[]`: the scheduler state file's pending-child entries array; the duty's existing already-exists predicate reads only it, which is exactly the surface operator-armed carriers never appear in.

## Why

The chaining duty decides its arming state-first from the scheduler state file alone, so operator-armed lane one-shots are invisible to it: those asks are armed without any state write by standing doctrine. A turn can therefore arm a second carrier over an already-covered window, as witnessed on 2026-11-08 22:15Z when a retry landed four minutes before an operator-armed authoring one-shot and had to be stood down before emission. One read-only listing before the arm create closes the blind spot at the decision point.

## Gist & Examples

TLDR: a one-listing coverage consult before the Occupied-lane chaining duty arms a retry one-shot or a reset-anchored successor closes the duty's blind spot to operator-armed carriers, for code-quality.

Before: a lane defers on an occupied-lane reason while operator-armed one-shots already cover the coming window. The turn reads only `children[]`, sees no standing retry, and arms a scheduler-template retry one-shot. The fired session's listing then shows the collision (seven armed operator one-shots in the witnessed turn) and the retry must be stood down mid-flight; a session that arms before listing instead stacks two carriers firing the same lane mandate in one window.

After: the same turn runs one automation listing before the arm create. Any matching record inside the coverage window records the existing carrier and skips the arm; an unusable listing takes the existing park fallback, so the consult never blocks a lane or the turn. Both existing tripwires are untouched, and no state field is added.

## Outcome

The Occupied-lane chaining duty sees operator-armed carrier coverage before arming, so a covered window never receives a second carrier.

- A retry-arm decision with an in-window matching record skips the arm and records the existing carrier, instead of arming a duplicate.
- The reset-anchored successor carries the same consult, so the two arming shapes cannot diverge.
- An unusable listing parks the decided arm through the existing fallback instead of arming blind, and never blocks.
- Both existing tripwires, the state schema, and the runtime overlay's primitive bullets are unchanged.

Gate delta: none (a read-only decision-input listing on an existing arming path; no refusal class, hard gate, fence, protocol layer, schema field, or dispatch-pausing condition added; both existing tripwires unchanged; no blocking-machinery admission row owed per the entry's Machinery admission paragraph)

## Assumptions

- Assume the consult is sanctioned as a duty-mandated decision-input listing by the dispatch discipline's generic exception clause without any overlay edit; basis: `agents/skills/maintenance/zcode.md` "Dispatch discipline and loop stand-down" bullet ("the exception is a listing a duty mandates as its decision input", the enumerated forms illustrative), and consult-then-create is listing-then-mutating, which trips no loop signature.
- Assume the consult adds no state field and records found coverage in `decision_reason`; basis: the bullet's closing "the duty adds no new state fields" and the entry's Machinery admission paragraph (read-only listing step, no gate, validator, lock, ledger, or required ceremony).
- Assume runtime-agnostic wording ("one automation listing") is correct for `decisions.md`, the concrete primitive staying the runtime overlay's; basis: the bullet's existing "arming route is the runtime overlay's existing clocked-child dispatch shape" sentence and the overlay's Listing bullet.
- Assume the coverage window is the arm's own coverage span; basis: the entry scope arm 1's "with a fire time inside the window" read against the duty's purpose, and the 12:24Z witness where a next-day parent slot left the lane dark, so only in-window coverage counts.
- Assume a parent carrier in chain form counts as coverage when its fire time falls inside the window; basis: the matching predicate's "or the scheduler prompt opening" alternative (the entry's own wording), since a parent turn inside the window re-runs the lane decision.
- Assume the single consult home is the Occupied-lane chaining bullet and the overlay's primitive bullets need no edit; basis: the overlay's "Occupied-lane retry one-shot" and "Reset-anchored successor" bullets defer to the duty's single home by name, so a second copy of the consult wording in the overlay would drift.
- Origin class consumption receipt: the origin row's `Class:` line reads fence-class; the body re-derivation (the origin records a decision-input gap, a consult missing on an arming path, not a completed fence failure) keeps the plan at the fix-class shape: it adds a read-only consult, no fence, no refusal path, so the fence-class bar is not triggered.
- Growth-payment receipt: the consult wording reuses the existing Child classification markers vocabulary and the existing park fallback by reference, adds no new vocabulary or second home, and carries no incident narrative (the bullet's existing witness line stays the story's home); the residual unbalanced byte growth of the two consult sentences is accepted and recorded here as the review-time payment record.
Decision points requiring a grill: consult placement = the Occupied-lane chaining bullet in `agents/skills/maintenance/decisions.md` (the duty's single home), the retry-arm consult in the Arm shape paragraph and a mirrored sentence beside the 5h-wall arm, no overlay copy (source: entry scope arms 1 and 3, and the overlay bullets deferring to the duty's single home, 2026-11-09, affected sections: Task 1 / Review Scope); matching predicate = ENABLED repository-contained one-shot whose prompt contains the resolved repository root and carries a lane marker or the scheduler prompt opening, fire time inside the window (source: entry scope arm 1 verbatim, 2026-11-09, affected sections: Task 1 / Terms); found-coverage disposition = record the existing carrier and skip the arm under the existing refresh-nothing semantics, recorded in `decision_reason`, no state write (source: entry scope arm 1 and the bullet's existing refresh-nothing clause, 2026-11-09, affected sections: Task 1); failure posture = unusable or cannot-decide listing takes the existing park fallback instead of arming, never blocking (source: entry scope arm 2 and the bullet's existing probe-failure park posture, 2026-11-09, affected sections: Task 1); tripwires unchanged = the duplicate-parent tripwire and the duplicate-user-directed-dispatch tripwire keep their exact text (source: entry scope arm 4, 2026-11-09, affected sections: Task 1 / Review Scope).

## Standing constraints

- Operative-text anti-growth (repository guidelines): the consult wording cites existing vocabulary by reference, adds no new vocabulary or second home, and carries no incident narrative; the entry and the origin dossier stay the story's homes.
- `decisions.md` stays runtime-agnostic: the consult names "one automation listing", never a tool name; the runtime overlay owns the concrete primitive.
- Both tripwires are unchanged: no insertion restates, retightens, or re-enumerates the duplicate-parent tripwire or the duplicate-user-directed-dispatch tripwire.
- Root discipline: authoring-time witness simulations read `decisions.md` at the primary checkout; execution-time witnesses run from the executing worktree.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the consult text names the matching predicate, the coverage window, the found-coverage disposition, and the unusable-listing posture, each traceable to an entry scope arm or the entry's rejected-alternatives section.
- single-homing: one consult home in the Occupied-lane chaining bullet; the runtime overlay's primitive bullets stay pointer-accurate with zero edits.
- minimality: the execution run's changed file set names `agents/skills/maintenance/decisions.md` only; no scripts, schema, or state-field changes.

**Done when:**
- The presence and position witnesses pass from the executing worktree, RED before Task 1's edit (count 0) and GREEN after (count at least 2 with both regions pinned): the Validation Commands block's coverage-consult gate exits 0.
- Both consult sentences sit inside the Occupied-lane chaining bullet with every quoted anchor's tail text intact.
- The pins suite, the public-hygiene scan, and the em-dash added-lines gate each exit 0.
- `python3 scripts/plan_readiness.py docs/history/plans/2026-11-09-chaining-retry-arm-blind-to-operator-carriers.md` exits 0 with the final `OUTCOME: pass` line at execution start, before the first checkbox flip.

**Ship when:**
- The next scheduler turn that resolves an occupied-lane deferral consults the listing before arming and demonstrably skips the arm when operator-armed coverage exists inside the window (live-behavior evidence; prose only).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- (none; this plan changes no production code)

**Docs and skill text:**
- `agents/skills/maintenance/decisions.md` (Task 1)

**Tests:**
- (none added; verification is the presence and position witnesses plus the repository's standing suites listed under Validation Commands)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/zcode.md`; reason: the primitive bullets defer to the duty's single home and the dispatch discipline's generic clause already sanctions duty-mandated decision-input listings; a second consult copy would drift.
- The duplicate-parent tripwire and the duplicate-user-directed-dispatch tripwire; reason: entry scope arm 4 keeps both unchanged.
- `agents/skills/maintenance/state-file.md` and any `scripts/` code; reason: the consult adds no state field and no code.
- `docs/history/backlog/2026-11-08-capacity-aware-chaining-phase3-residuals.md` (the Cluster row); reason: its two advisories carry recorded dispositions on the same surface and are deliberately not consumed here.

## Validation Commands

Authoring-time record (rule 29 preflight, run over the plan bytes before the first review round; outcomes recorded here at authoring): see the Validation preamble paragraph below.

```bash
# Presence and position witnesses (Task 1), from the executing worktree root.
# RED before Task 1's edit (count 0 fails the first region assert), GREEN after:
python3 -c 'import sys; s=open("agents/skills/maintenance/decisions.md").read(); a=["Arm shape: at most one near-future retry one-shot","The retry one-shot is a child, never a parent","The 5h-wall arm (the reset-anchored successor)","The arming route is the runtime overlay"]; p=[s.find(x) for x in a]; assert -1 not in p, "anchor missing: %r" % (p,); assert all(s.count(x)==1 for x in a), "anchor not unique"; arm,child,wall,route=p; f=s.find("coverage consult", arm); assert 0 < f < child, "consult-1 not in Arm shape region (count today: %d)" % s.count("coverage consult"); g=s.find("coverage consult", wall); assert 0 < g < route, "consult-2 not beside the 5h-wall arm"; assert s.count("coverage consult") >= 2, "count < 2"; print("coverage consult witnesses pass")'
# Standing gates, from the executing worktree root:
bash scripts/check_maintenance_pins.sh
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base <base-ref>   # <base-ref> = the execution run's base commit
python3 scripts/plan_readiness.py docs/history/plans/2026-11-09-chaining-retry-arm-blind-to-operator-carriers.md
```

Validation preamble (authoring-time outcomes, recorded per validation rule 29; updated in place as boundaries run):
- rule 19 RED-today evidence (2026-11-09, primary-checkout read of `agents/skills/maintenance/decisions.md`): the coverage-consult witness command exits non-zero with "consult-1 not in Arm shape region (count today: 0)", so the gate fires before the edit and can only turn GREEN through Task 1's insertions; all four anchor spans verified unique in the target file.
- em-dash scan (`touched`, plan bytes): `OUTCOME: pass`, 0 substitutions (fixer and gate).
- public-hygiene scan: `OUTCOME: pass` (2026-11-09, worktree root).
- readiness `--pre-round`: first run refused one 546-byte evidence criterion (over the 512-byte item cap); split into two items; second run `OUTCOME: pass` (structural checks clean). Residual advisory FILES-COVERAGE warnings adjudicated: Task 2's verification commands are single-homed in this block, and the one sibling-declared path warning (`agents/skills/maintenance/decisions.md` in Task 2's changed-file-set witness) is adjudicated as read-only verification over Task 1's edit, correctly undeclared in Task 2's Files: list.

### Task 1: Coverage consult in the Occupied-lane chaining bullet

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/decisions.md`

- [x] In the Occupied-lane chaining bullet's Arm shape paragraph, immediately after the clause ending "never stacking a second retry" and before "The retry one-shot is a child, never a parent", insert the coverage consult sentences; both quoted anchors survive verbatim [class: IMPLEMENTATION_REQUIRED]
- [x] The consult order: one automation listing before emitting the arm's create, run after the `children[]` already-exists check finds no standing retry [class: IMPLEMENTATION_REQUIRED]
- [x] The matching predicate: any ENABLED repository-contained one-shot whose prompt contains the resolved repository root and carries a lane marker or the scheduler prompt opening, with a fire time inside the coverage window; found coverage records the existing carrier in `decision_reason` and skips the arm under the existing refresh-nothing semantics [class: IMPLEMENTATION_REQUIRED]
- [x] The consult inherits the arm's failure posture: an unusable or cannot-decide listing (tool error, truncated or unreadable listing) takes the bullet's existing park fallback instead of arming, never blocking a lane or the turn [class: IMPLEMENTATION_REQUIRED]
- [x] The lane marker term cites the overlay's Child classification markers by reference (no marker enumeration restated); the scheduler prompt opening names the scheduler prompt template's first line as the recognition span, without restating either tripwire's rules [class: IMPLEMENTATION_REQUIRED]
- [x] Insert the mirror sentence beside the 5h-wall arm: after "every retry one-shot landing inside the current window behind the fit test" and before "The arming route is the runtime overlay", the same one-listing consult applies to the successor's create with the coverage window spanning from the decision through the reset-anchored fire time; both anchors survive verbatim [class: IMPLEMENTATION_REQUIRED]
- [x] Consult witness (retry arm): given a lane deferral whose coverage window holds a matching record, expects found coverage recorded in `decision_reason` and the arm skipped (no create emitted, no `children[]` entry appended) [class: REPOSITORY_TEST]
- [x] Consult witness (5h-wall and posture): given a stop whose quota leg defers past reset and an in-window matching record, expects the successor skipped the same way; given an unusable listing on either arm, expects the park fallback per the existing park shape and no create [class: REPOSITORY_TEST]
- [x] Presence and position witnesses, failing before the edit and passing after, from the executing worktree: the Validation Commands block's coverage-consult gate exits 0 (count at least 2; first occurrence inside the Arm shape paragraph region, second beside the 5h-wall arm; all four anchor spans unique) [class: REPOSITORY_TEST]
- [x] Commit: `wip: coverage consult in the Occupied-lane chaining bullet` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Standing gates and unchanged-surface verification

Context surface: the plan's Terms, Task 1's edit, and `## Standing constraints`.

Files:
- (none; read-only verification over Task 1's change)

- [x] From the executing worktree run the Validation Commands block's standing gates (pins suite, public-hygiene scan); expect exit 0 on both (the decisions.md pins are presence greps, none pins the chaining bullet, and the insertions must not reword any pinned literal) [class: REPOSITORY_TEST]
- [x] Run the Validation Commands block's em-dash added-lines gate over the run's change with the execution run's base commit; expect exit 0 [class: REPOSITORY_TEST]
- [x] Changed-file-set witness: `git diff --name-only <base-ref>..HEAD` names `agents/skills/maintenance/decisions.md` only, proving both tripwires and every other surface byte-unchanged [class: REPOSITORY_TEST]
- [x] At execution start, before the first checkbox flip, the Validation Commands block's readiness invocation exits 0 with the final `OUTCOME: pass` line [class: REPOSITORY_TEST]
