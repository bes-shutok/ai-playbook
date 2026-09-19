# Backlog: maintenance has no park/defer path for externally gated plans

Status: open
Workflow: backlog
Source: 2026-09-18 post-mortem of the legacy verdict-grammar deletion plan (parked by hand the same day at docs/plans/deferred/2026-09-15-plan-readiness-legacy-verdict-grammar-deletion.md after Andrey asked why maintenance never proposed the deferral); root-caused against agents/skills/maintenance/SKILL.md as deployed 2026-09-18
Severity: Medium (latent: a wasted child dispatch and a spurious G2 loop halt are one selection step away; no damage yet)
Scope: agents/skills/maintenance/SKILL.md (Steps 1 and 3, the failure-cap section, the Invariants list); scripts/check_maintenance_pins.sh (invariant pins move if D4 lands); agents/skills/maintenance/zcode.md only if the overlay carries classification helpers

## Problem

The maintenance skill manages the plan queue (survey, guards, decide, dispatch)
but its decision space is D1 execute / D2 author / D3 no-op. Deferral exists in
the skill only as an INPUT exclusion, the Invariants list says
"`docs/plans/deferred/` plans are never auto-picked (human revival only)", and
as the fossil of a one-off human triage (2026-09-11 efficiency/token/simplicity
pass, recorded in docs/plans/deferred/README.md). Nothing in Steps 0-6 can MOVE
a plan into `docs/plans/deferred/`, propose moving one, or even flag one as a
park candidate. A plan that can never legally execute therefore sits in the
top-level survey forever unless a human notices.

Concrete miss: `docs/plans/2026-09-15-plan-readiness-legacy-verdict-grammar-
deletion.md` was eligibility-gated by its own Ship-when section (sweep coverage
covered==total, measured 235/478 at authoring and NOT converging, the
uncovered pool held at ~244 while the corpus grew) from the day it was
certified. It sat top-level and digest-intact for three days of recurring
maintenance turns. No turn flagged it, proposed parking it, or recorded why
executing it would be wasted. It was parked on 2026-09-18 only because Andrey
asked directly.

Four root causes, all in SKILL.md:

1. **D1 selection is eligibility-blind.** Selection reads exactly three
   signals: memory dependency-chain order, digest-intactness (certification
   oracle), and oldest basename. A plan whose Ship-when names an external
   prerequisite (an eligibility gate, a date gate, a named unfunded effort) is
   indistinguishable to D1 from a dispatchable plan. The parked plan was
   NEXT-IN-LINE by the skill's own fallback rule: after
   2026-09-15-budget-gate-decision-table-attribution was dispatched and
   archived on 2026-09-18, the legacy-verdict plan (basename 2026-09-15) was
   the oldest digest-intact top-level plan (scheduler state 2026-09-18T17:24Z:
   survey 7 open / 6 digest-intact). It was spared only by soft memory-index
   ordering and lane occupancy, luck, not design. Any turn where the chain
   order is unavailable or lists it first dispatches a plan whose own Task 1
   then mandates a stand-down.
2. **The stand-down collides with the failure cap.** The progress predicate
   for an execution child is "target plan archived OR checked-checkbox count
   increased". A stand-down-gated plan executed correctly edits nothing
   (Task 1: "Edit nothing, commit nothing"), so its checkbox count is static
   forever: outcome `failed`, and with the plan as the only dispatchable
   target the cap arms at three consecutive outcomes and the `alert` halts the
   whole loop until a human clears it. The failure cap converts a CORRECT
   stand-down into a loop failure. Every re-dispatch burns another child run.
3. **D1's must-dispatch pressure has no gate exemption.** "The execution lane
   must not idle by choice: ... a turn that ends with the lane free and no
   dispatch while a dispatchable plan exists, without a guard, quota, or
   dependency reason, records a `turn_error` (dispatch defect)." A turn that
   correctly refuses to dispatch a gated plan has no listed reason class for
   doing so and would record itself as defective.
4. **No aging/starvation signal.** Nothing anywhere in the turn surfaces
   "open for N days, zero checkbox movement, external prerequisite not
   satisfiable by anything in the survey", the exact signature that made the
   2026-09-11 human triage park ten plans.

## Suggested fix

Add a park-aware lane to the scheduler turn, minimal first. All fixes keep the
existing invariant that deferred plans are never auto-picked and revival stays
human-only; the change is about ENTERING the deferred state and about not
burning children on plans that cannot progress.

- **Fix A (selection-side skip, owns the wasted-child and loop-halt hazards):**
  Step 1's survey classifies each open plan as externally gated or not, and D1
  skips gated plans exactly like dependency-blocked ones, with the mirrored
  self-heal (a plan whose gate becomes satisfied is no longer skipped). The
  skip reason is also added to the D1 dispatch-defect exemption list (root
  cause 3), so a correct refusal is not a `turn_error`. Gate classification
  must stay mechanical, see the classification options below.
- **Fix B (park proposal, owns the invisibility):** a new Step 3 decision `D4
  (propose park)`: when an open plan is externally gated AND its gate is not
  satisfiable by anything in the current survey (no open backlog item or open
  plan names the gate's prerequisite) AND the plan has zero checkbox progress
  for a threshold period (suggest 7 days), the turn records a park proposal,
  a `park-proposal` memory note (repo-keyed like the other notes) plus a
  `decision_reason` entry, and the plan keeps being skipped. A human parks
  per docs/plans/deferred/README.md. No autonomous `git mv` of certified work.
- **Fix C (auto-park, only after Fix A/B have run in production long enough to
  trust the classifier):** D4 graduates to executing the park itself,
  byte-identical `git mv` plus backlog-origin move plus `Priority: deferred`
  header per the deferred/README convention (the parked plan's review digest
  stays valid, and revival is a documented human protocol, so the action is
  reversible). Recommendation: do NOT take C in the same change as A/B; gate
  classification false positives parking certified plans is the bad case.
- **Gate classification options (pick one, record the choice):**
  - (i) Plan-declared gate line: a plan may declare its external gate in a
    machine-readable header (same metadata surface as the driving-force item
    docs/history/backlog/2026-09-18-plan-driving-force-and-gist-tldr-metadata.md
   , coordinate the two so plans declare one metadata block, not two). The
    turn trusts the declaration and checks only satisfaction evidence in the
    survey (is the named prerequisite now an open item/plan, or has the named
    date passed). Cheapest; risk: a stale or missing declaration, mitigated by
    treating "no declaration" as not gated (preserves today's behavior for
    ungated plans).
  - (ii) Stand-down detection from evidence: a plan whose most recent execution
    child ended in a Task-1-style STOP (state-file child record with outcome
    failed/progress but zero checkbox delta and a stand-down report in the
    execution log) is marked gated in the state file. No plan-text parsing, but
    costs one wasted child to learn, which is exactly what Fix A is meant to
    avoid, usable only as a secondary signal.
  - (iii) Free-text Ship-when parsing by the turn model: most general, least
    mechanical, hardest to pin in scripts/check_maintenance_pins.sh; not
    recommended as the primary mechanism.
- **Failure-cap carve-out (independent of A-C, take it regardless):** when the
  only reason an execution child made no checkbox progress is a recorded
  stand-down (the child's own report says STOP/stand-down and the plan file is
  unchanged), the outcome does not accrue failure credit, same spirit as the
  existing evidenced-provider-stop and evidenced-stopped exceptions. This
  decouples "the loop punished a correct no-op" from the classification
  question entirely.

## Acceptance criteria

- A certified, digest-intact, top-level plan whose external gate is unsatisfied
  is never selected by D1 (skipped with a recorded reason, exempt from the
  dispatch-defect turn_error).
- A correctly executed stand-down never accrues child failure credit and can
  never alone trip the G2 alert.
- A park proposal (or park, under Fix C) is visible in the turn output, the
  state file, and a repo-keyed memory note, and names the plan, the gate, and
  the evidence that the gate is unsatisfied.
- The pins suite (scripts/check_maintenance_pins.sh) is updated only after the
  new invariants settle; the deferred/ never-auto-picked invariant is unchanged.
- No plan file bytes change while parked (byte-identical convention preserved).
