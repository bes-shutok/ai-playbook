Status: open
Priority: high
Workflow: backlog
Class: automation
Driving force: reliability
Origin class: witnessed-incident (2026-09-30 duplicate authoring of docs/history/backlog/2026-09-29-execute-plan-prior-invocation-scope-leak; user direction: analyze root cause and file)

# Origin coverage lifecycle: a landed plan must close the origin and the landing gate must catch duplicates

## Problem

A backlog origin reads `Status: open` from filing until a plan's execution folds it. Nothing flips the origin when a plan covering it is authored or landed, so the selection queue keeps offering the origin to every survey in that window, and nothing at landing compares origin references, so a second plan for the same origin can be reviewed, landed, and even executed unnoticed. The guards that do exist are plan-slug-scoped: the execution-claim stub and the D1 selection-time skip key on the plan's own slug, so once two plans share one origin, each carries its own claim file and every later guard treats them as independent work - duplication is never reconciled mechanically, it compounds.

Two additional defects make the collision class stickier:

- Discovery is incidental. No landing or preflight step greps landed plans for the same origin reference; the 2026-09-30 collision was found only because a session happened to run `git worktree list` after its own landing.
- The manual mitigation is invisible to the racing lane. The coverage note for the witnessed incident (main `c8a244a6`) landed on main while the peer's authoring worktree was already checked out at an earlier commit; the peer continued folding review findings (`f18d818c`) without seeing it. A note on main does not reach in-flight worktrees.
- Origin references are fragmented across two shapes: some plans open with an origins block (`Backlog origins (scope of record)`, consumed by `scripts/check_plan_origins_closed.py`), others carry a single-line `Origin:` reference. A mechanical coverage check must normalize both or the convention must unify, or coverage will be blind to one shape.

Witnessed 2026-09-30: session A landed `0f4b7cf5` (origin 2026-09-29-execute-plan-prior-invocation-scope-leak) while a peer lane had independently authored the same origin (`a7b470e3`/`f18d818c`, branch `author-scope-leak-20260930`, unlanded). Only an ad-hoc hand-written status note reconciled them; no gate enforces that reconciliation.

## Observed versus expected

- Observed: the origin stayed open after the covering plan landed; the selection queue offered it to both lanes; neither the landing nor any gate compared origin references; the manual coverage note existed only on main and only because a human-direction-driven session chose to write it.
- Expected: landing a plan that names an open origin flips that origin to a covered state naming the plan, and a landing whose origin is already covered is refused with the covering plan's witness until the two are reconciled to one.

## Proposal (minimal shape, for plan authoring to refine)

1. Covered-at-landing: when a plan whose origin reference names an open backlog item lands (the landing flow's closeout, mirroring how execution later folds the origin), flip the origin's Status to `covered` naming the covering plan. The survey skips covered origins when selecting authoring targets, but still offers covered-not-yet-executed origins for execution selection.
2. Duplicate-origin landing gate: a readiness or landing gate fails when another plan already cites the same origin (mechanical check: normalize both reference shapes to the backlog path, grep the resolved plans directories for it), naming the covering plan and the remedy - reconcile to one plan, with the loser rejected as superseded with a decision note (precedent: the 2026-09-28 direct-claim-prelaunch-recovery rejection).
3. Precedence rule, stated once in the gate's guidance: first-landed wins; a later plan for the same origin folds into the winner as an amendment instead of competing, unless it adds material scope the winner lacks - in which case the winner is amended, not replaced.

## Rejected alternatives

- Fold the origin at authoring time: rejected; an authored plan may never land, and the origin must stay selectable if the authoring run aborts - authoring-time invisibility is the authoring-claim item's problem, not this one.
- Rely on exec-lane claims to dedupe: rejected; those claims are plan-slug-scoped by design, so two same-origin plans execute "once each" and the duplication passes every execution-time guard.
- Human-only reconciliation: rejected; it already failed once (the coverage note did not reach the racing lane) and the scheduler lanes run with reduced context.

## Witnesses

- Landed covering plan `0f4b7cf5` with origin still `Status: open` until manual note `c8a244a6`; peer authoring `a7b470e3`/`f18d818c` continued without seeing the note (worktree pre-dated it).
- The origins-closure gate (`scripts/check_plan_origins_closed.py`) only consumes origins-block headers and only verifies archive moves, not cross-plan coverage; single-line `Origin:` references (used by the witnessed plans) are outside its parse.
