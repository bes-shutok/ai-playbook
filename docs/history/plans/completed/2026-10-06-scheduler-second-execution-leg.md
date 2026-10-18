# Plan: the scheduler's directive-bound second execution leg

Backlog origin: docs/history/backlog/2026-10-06-parallel-execution-turn-cap-and-fired-arm.md
Driving force: efficiency
Plan review record: the staging series docs/history/reviews/2026-10-06-plan-review-scheduler-second-execution-leg-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 1.5h total, largest task 1h
Authoring claim: docs/tmp/authoring-claims/2026-10-06-scheduler-second-execution-leg.md (session sess_1e13991c-8e25-4535-9a7e-ae31500fc603)

## Terms

- per-turn cap: the Step 5 bullet "Schedule at most one child per lane per scheduler turn (one execution AND one authoring at most)" in `agents/skills/maintenance/SKILL.md`.
- second execution leg: the directive-bound capacity-parallel in-session execution this plan adds beside the turn's one clocked dispatch.
- live execution directive: a standing operator directive naming execution throughput, or the deciding turn's own user-directed payload text.
- same-directive session: a deciding turn whose prompt carries the same standing operator directive the fired child's recurring payload text carries; the session shape the fired arm's release rule admits (narrower than a live execution directive, which also covers the turn's own user-directed payload text).
- fired arm: the `G1e` sub-bullet holding the lane for a fired execution child fewer than six hours past its `fire_at`.
- the overlay: `agents/skills/maintenance/zcode.md`, the runtime overlay whose Execution-lane fallback legs bullet carries the P64 carrier-selection primitives.
- maintenance pins suite: `scripts/check_maintenance_pins.sh`, the grep-pinned literals over the maintenance skill files.
- quota leg: the Step 4 quota-window pricing that fixes a dispatch's final fire time and primitive selection.
- pre-dispatch landing gate: the lane gate that refuses a dispatch while an unlanded run or surviving note stands at the final slot.
- fleet cap: the both-lanes cap counting live children per turn (added 2026-09-24, P54).
- `G1a`: the authoring-lane occupancy guard, the authoring-side twin of `G1e`.
- `G3b`: the merge-lock-hold guard whose final-slot effect defers the affected lane's dispatch.
- clocked dispatch: a one-shot automation created with a fire time at least 5 minutes out.
- the entry: the `docs/history/backlog/PLAN-PROMPTS.md` entry `scheduler-second-execution-leg`, the promoted prompt this plan implements.

## Why

Two mechanisms jointly serialize the fleet to roughly one execution per day under the standing one-by-one directives: the per-turn cap reads as one dispatch and stop, and the fired arm's six-hour horizon holds the lane every morning after the nightly payload fires. The origin row witnessed the shape live: the 06:47 turn dispatched one child and executed nothing itself while thirteen digest-intact plans sat open.

## Outcome

A turn carrying a live execution directive can execute a second distinct-target plan in-session beside its one clocked dispatch, and a same-directive session is no longer blocked by a fired recurring payload's lane hold on a distinct target.

- The fleet's throughput under a live directive rises from the witnessed one plan per turn toward the several plans the fleet cap already sanctions.
- Every guard keeps its current bytes: the second leg re-reads them at the decision, and the fired arm's horizon and failure cap stay untouched.

Gate delta: grows two checked-condition sets in existing guard machinery (the per-turn cap's directive-bound release leg with its enumerated guard re-reads, and the `G1e` fired arm's same-directive distinct-target release) and adds two companion pin rows; no refusal class, hard gate, fence, protocol layer, or schema state field is added, and the six-hour horizon, the failure cap, and every integrity guard keep their current bytes; the growth is priced by the origin row's witnessed idle (one execution per turn while thirteen digest-intact plans sat open, investigation receipt 2026-10-06), the release legs being the paying fix that witness buys rather than new enforcement.

## Assumptions

- assume the second execution leg is in-session only (no second clocked create beside the first); basis: the entry's prompt prescribes "execute one additional distinct-target plan in-session beside the one clocked dispatch", and the rejected alternatives that remove the cap or widen the carrier-selection ordering are recorded as rejected in the entry.
- assume target-distinctness for the second leg is checked against every armed and pending `children[]` entry in the state file (both lanes); basis: the entry's guard enumeration names "every armed and pending child entry" without lane restriction; recorded disagreement: the origin row's fix shape reads "every armed/pending execution child" (lane-restricted), and this plan keeps the wider both-lane reading because executing a plan currently under a live authoring child is the harm the wider check prevents, the divergence resolving in the conservative direction (a spurious hold, never a wrong release), per the filing-class rule that the arms shape to the stricter class when a declared line contradicts the body.
- assume the pins suite passes with the two new rows and no other row change; basis: the suite is grep-based over the maintenance files, the needles are new text absent today, and no existing row pins a span this plan edits.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the scheduler's per-turn cap gains a directive-bound second in-session execution leg and the fired arm releases for a same-directive session on a distinct target, so a live directive turns the fleet from one plan per turn toward parallel execution (efficiency).

**Before (today):** a turn carrying a live execution directive dispatches its one clocked child and stops; the nightly 01:20 payload's fired arm holds the execution lane until 07:20; the 06:47 turn dispatched one child for 11:35 and executed nothing while thirteen digest-intact plans sat open.

**After (this plan):** the same turn may execute one additional distinct-target plan in-session through every guard re-read at the decision, recording the standard `(in-session)` children[] entry; a same-directive session's distinct-target candidate releases the fired arm's hold; a fired scheduler-dispatched child without such a session holds the lane exactly as today.

## Evaluation Criteria

**Quality dimensions:**
- correctness: both release legs carry their full guard enumerations; a same-directive session with a same-target candidate still holds; the pins suite passes with the two new rows.
- regression safety: the cap bullet's default sentence, the fired arm's six-hour sentence, and the failure cap keep their current bytes; the em-dash added-lines scan and the hygiene scan report no findings.
- scope discipline: only `agents/skills/maintenance/SKILL.md`, `agents/skills/maintenance/zcode.md`, and `scripts/check_maintenance_pins.sh` change; no state schema, no runtime script, no other skill file is touched.

**Done when:**
- `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )` exits 0 including the two new rows.
- Every span check in `## Validation Commands` holds on the executed tree.

**Ship when:**
- A turn under a live directive demonstrably executes or dispatches two distinct plans in one turn without tripping the guards, witnessed in the scheduler state's `children[]`; it follows from the executed tree under the next live directive.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/SKILL.md` (the Step 5 cap bullet's second leg and the Step 2 `G1e` fired arm's release rule)
- `agents/skills/maintenance/zcode.md` (the Execution-lane fallback legs bullet's reference to the new leg)
- `scripts/check_maintenance_pins.sh` (the two companion rows)

**Tests:**
- none (the pins suite is the verification surface and is listed above)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the Execution-lane carrier-selection ordering's fallback legs and their trigger order (SKILL.md Step 3, overlay bullet): reason: the entry keeps the ordering untouched because it selects the carrier for the one primary dispatch when primitives are absent, a different trigger than a capacity-parallel second execution.
- the six-hour horizon's length and the failure cap's floor: reason: the entry keeps both byte-for-byte; the rejected alternative lowering the horizon globally reopens the double-dispatch window the floor closes.

## Validation Commands

Authoring-time evidence (rule 29 pre-round): the plan bytes passed the pre-round gate with exit 0 and `OUTCOME: pass` in the authoring worktree; the rule 19 RED-today probe ran each pinned span with grep against its owning target (the new-duty spans returned no match: the second-leg, carve-out, and overlay needles 0 each in their skill files; the preserved spans matched: the idle-time tail as the closing-backtick phrase without the sentence period, the fired arm's ENABLED tail, the overlay bullet's park-pairing tail, and the quota-leg pins anchor at 1 each); the rule 22 mechanical audit verified every pinned span occurs in its owning prescribed snippet (rule 36 mirrors included: each needle appears as checker literals beside its Task prescription) and `bash -n` accepted the Validation Commands block; the em-dash touched scan and the hygiene scan both exited 0. Round-start state for r1: authoring worktree ai-playbook-wt-ssel, branch 2026-10-06-scheduler-second-execution-leg, plan bytes at the draft commit.

```bash
REPO="$(git rev-parse --show-toplevel)"
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )
( cd "$REPO" && test "$(grep -oF 'directive-bound second execution leg' agents/skills/maintenance/SKILL.md | wc -l)" -eq 1 )
( cd "$REPO" && test "$(grep -oF 'releases for a same-directive session' agents/skills/maintenance/SKILL.md | wc -l)" -eq 1 )
( cd "$REPO" && test "$(grep -oF 'not one of these fallback legs' agents/skills/maintenance/zcode.md | wc -l)" -eq 1 )
( cd "$REPO" && test "$(grep -cF 'directive-bound second execution leg' scripts/check_maintenance_pins.sh)" -eq 1 )
( cd "$REPO" && test "$(grep -cF 'releases for a same-directive session' scripts/check_maintenance_pins.sh)" -eq 1 )
( cd "$REPO" && bash scripts/check-no-em-dash.sh added-lines --base main )
( cd "$REPO" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh )
```

### Task 1: the per-turn cap's directive-bound second execution leg

Context surface: the plan's Terms and this task.

Files:
- `agents/skills/maintenance/SKILL.md` (Step 5, the cap bullet region)
- `agents/skills/maintenance/zcode.md` (the Execution-lane fallback legs bullet)
- `scripts/check_maintenance_pins.sh` (the maintenance block)

Evidence:
- `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )`; covers the pins-reconciliation criterion: the new row passes and no existing row's literal broke
- the span checks in `## Validation Commands`; covers the insertion criterion: the second-leg needle, the overlay reference needle, and the pins row needle each at their pinned counts

- [x] In `agents/skills/maintenance/SKILL.md`, insert a new bullet immediately after the Step 5 bullet whose final sentence ends with the literal `an idle-time run (no scheduled fire time)` followed by a closing backtick and a sentence period, and before the `- In-session dispatch mode:` bullet, with the bullet opening `The cap's directive-bound second execution leg (added 2026-10-06, origin docs/history/backlog/2026-10-06-parallel-execution-turn-cap-and-fired-arm.md): the "at most one child per lane per scheduler turn" default stands, and a turn carrying a live execution directive may execute one additional distinct-target plan in-session beside the turn's one clocked dispatch.` and continuing: a live execution directive is a standing operator directive naming execution throughput or the turn's own user-directed payload text; the second leg still re-reads every guard at the decision (the lane guards `G1e`/`G1a`, the quota leg, the `G3b` final-slot effect, the pre-dispatch landing gate, the fleet cap, and target-distinctness against every armed and pending `children[]` entry), records the standard `(in-session)` children[] entry the in-session dispatch mode already writes, and stays outside the Execution-lane carrier-selection ordering because that ordering selects the carrier for the one primary dispatch when primitives are absent, a different trigger than a capacity-parallel second execution beside a working clocked leg [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/maintenance/zcode.md`, append to the `- Execution-lane fallback legs (added 2026-09-26, P64):` bullet, after its final sentence ending `the pairing part of the park's own targeted-edit step).`, the sentence: `The SKILL.md cap's directive-bound second execution leg is capacity-parallel beside the primary dispatch and not one of these fallback legs; the ordering's trigger stays absent-or-retired primitives for the one primary dispatch.` keeping the bullet's existing text byte-identical [class: IMPLEMENTATION_REQUIRED]
- [x] In `scripts/check_maintenance_pins.sh`, add one companion row in the maintenance block anchored immediately after the `quota leg binds every clocked dispatch path` pin row, with a one-line origin comment above naming the origin row by its backlog path (`docs/history/backlog/2026-10-06-parallel-execution-turn-cap-and-fired-arm.md`), never the plan title: `pin "cap second execution leg" grep -qF 'directive-bound second execution leg' "$S"` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )` exits 0 with the new row passing; the second-leg and overlay span checks read 1 each [class: REPOSITORY_TEST]
- [x] Commit: `feat: the per-turn cap's directive-bound second execution leg` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the fired arm's same-directive release rule

Context surface: the plan's Terms and this task.

Files:
- `agents/skills/maintenance/SKILL.md` (Step 2, the `G1e` Fired arm bullet)
- `scripts/check_maintenance_pins.sh` (the maintenance block)

Evidence:
- `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )`; covers the pins-reconciliation criterion: the second new row passes with the suite still green
- the span check in `## Validation Commands`; covers the insertion criterion: the fired-arm carve-out needle at exactly 1 in the skill and 1 in the pins suite

- [x] In `agents/skills/maintenance/SKILL.md`, append to the `- Fired arm:` bullet, after its final sentence ending `a listing record counts only while it is ENABLED.`, the sentences: `The hold releases for a same-directive session when the fired child is a standing operator-defined recurring payload (the fired automation's prompt carries the same standing operator directive the deciding session's prompt carries, the standing user surface the User-directed override's presence predicate lacks for automation-born sessions) and the session's candidate target is distinct from the fired child's target, the comparison reading the target-bearing span of the fired child's listing prompt against the candidate plan path. A fired scheduler-dispatched child holds the lane as today, and the six-hour horizon and the post-fire outcome-horizon floor stay byte-for-byte with every integrity guard non-overridable.` keeping the bullet's existing text byte-identical [class: IMPLEMENTATION_REQUIRED]
- [x] In `scripts/check_maintenance_pins.sh`, add one companion row in the maintenance block anchored immediately after the `cap second execution leg` pin row, with a one-line origin comment above naming the origin row by its backlog path, never the plan title: `pin "fired arm same-directive carve-out" grep -qF 'releases for a same-directive session' "$S"` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )` exits 0 with both new rows passing; the fired-arm span check reads 1 [class: REPOSITORY_TEST]
- [x] Commit: `feat: the fired arm releases for a same-directive session on a distinct target` [class: IMPLEMENTATION_REQUIRED]


## Disposition

Executed 2026-10-06 in-session under the operator directive "start execution right away" (worktree wt-sseln, branch plan-ssel-exec).

- Task 1: the directive-bound second-leg bullet inserted at the prescribed anchor with the prescribed opening literal verbatim; the overlay's Execution-lane fallback legs bullet carries the capacity-parallel carve-out sentence; the companion pin row added with the origin comment naming the backlog path.
- Task 2: the fired arm's same-directive release sentences appended after the ENABLED tail byte-verbatim; the second companion pin row added beside the first.
- Gates: pins suite green with both new rows, em-dash added-lines 0, hygiene 0, pre-round pass; all span checks at their pinned counts.
- Exec review r4: ready=yes, zero blocking (adversarial sub-agent byte-comparing every prescribed span against main's prefixes and the plan's quoted literals); record 2026-10-06-plan-review-scheduler-second-execution-leg-r4.
- The origin row was already folded by the plan's own landing commit; no origin fold rides this execution.
