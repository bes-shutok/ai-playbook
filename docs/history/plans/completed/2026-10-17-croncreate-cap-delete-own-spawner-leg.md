# Plan: the operator-ordered schedule surface exhausts delete-own-spawner before any fallback

Backlog origin: docs/history/backlog/2026-10-17-croncreate-cap-delete-own-spawner-leg.md
Grouping entry: docs/history/backlog/PLAN-PROMPTS.md, `## croncreate-cap-delete-own-spawner-leg`
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-10-17-plan-review-croncreate-cap-delete-own-spawner-leg-p3d3fb07f-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-17-croncreate-cap-delete-own-spawner-leg.md (session sess_zcode-auth-20261017-2051)

## Terms

- cap refusal: the scheduler's refusal of a `CronCreate` inside a session already bound to a scheduled task, while any record of that session's lineage holds the one armed-automation slot.
- lingered spawner record: the session's own completed one-shot automation record (enabled false, lifecycle completed) that still occupies the lineage slot.
- delete-own-spawner leg: the `CronDelete`-shaped mutation of the session's own lingered spawner record, the witnessed 2026-10-13 cap-lift primitive.
- exhaust-delete-first: the ordering duty to attempt the delete-own-spawner leg (a recorded deletion attempt or a proven-absent deletion primitive) before any fallback arms.
- operator-ordered schedule surface: a direct operator "schedule at ..." ask delivered to the session, whose payload the session arms; owned today by the Clocked operator order duty in the dispatch ladder section, distinct from loop child dispatch.
- loop child dispatch: the scheduler turn's own authoring or execution child dispatch, governed by the landed dispatch ladder's ordering.
- default-in-waiting: the covering plan's coinage for the launchd chain's child-dispatch posture: named, priced, and guarded, but not the operative default until its promotion review activates it.
- sibling plan: docs/history/plans/2026-10-17-schedule-ask-session-owned-automation.md, the landed satisfaction-side correction whose declared sentences Task 2 carries verbatim.
- launchd clocked-order fallback: arming the order through the launchd clocked-order chain (`scripts/execute_plan_runtime.py --operation clocked-order-schedule`) when the in-session create primitive is unavailable or refused.
- degraded toolset: a session toolset whose probe finds no deletion surface for its own lingered record; this plan's ladder paragraph owns its sanctioned shape, a terminal-shaped park (intent record plus payload copy), not the landed listing-only rung's predicate.
- re-arm surface: the carrier re-arm duty's own delete-plus-create path in the Recurring automation recipe, already ordered delete-first by the landed text.
- Clocked operator order duty: the landed zcode.md duty (the Dispatch discipline bullet, added 2026-10-05) that arms a clocked operator order through the watcher chain and parks on refusal; the refusal leg Task 1 reorders.
- never-executes-inline clause: the original bullet's closing literal "it never executes the payload in the same turn" (the sibling plan's check 5 form).
- bound session: a session whose lineage holds a scheduled-task record, the cap model's bound side.
- second carrier: an additional automation carrier (here the launchd clocked-order job) armed beside the still-lingering spawner record the cap model treats as the lineage's automation.
- schedule ask contract: the repository guidelines' Scheduling asks section (create or patch, report id and next fire time, never execute inline).

## Why

Witnessed 2026-10-16 and operator-corrected 2026-10-17 ("you should have deleted existing schedule to create the one I asked for"): a cap-refused bound session armed an operator-ordered schedule through the launchd fallback without exhausting the delete-own-spawner leg, leaving a second carrier beside the still-lingering spawner record. The landed text owns the surface through the Clocked operator order duty, which orders the uncorrected behavior (chain-first arming, park-on-refusal, no delete-first exhaustion); the landed ladder orders delete-first for the re-arm surface and demotes loop child dispatch to a launchd default-in-waiting, so the corrected ordering exists for neither the duty nor a dedicated operator-ordered paragraph, and every future operator schedule ask in a bound session re-bites.

## Gist & Examples

TLDR: the dispatch ladder gains an operator-ordered schedule surface paragraph that orders the delete-own-spawner leg before any fallback and bounds the launchd fallback to a recorded deletion attempt or a proven-absent deletion primitive, because the witnessed session armed through the fallback with a reachable direct create and the operator corrected the ordering by name. Driving force: efficiency.

Before: a bound session is asked to schedule a one-shot order, `CronCreate` is cap-refused on its own lingered record, and the session routes straight to the launchd clocked-order chain; the record stays, a second carrier appears, and nothing names the skipped leg. After: the same session deletes its own lingered record first (lifting the cap), creates directly, and only a toolset whose probe proves no deletion surface takes the paragraph's terminal-shaped park (intent record plus payload copy), which a verified launchd fallback arming clears or marks satisfied so no discharge later re-dispatches a carrier-carried payload; the report names which leg was exhausted.

## Outcome

An operator schedule ask in a cap-refused bound session is satisfied by the asking session's own automation record whenever a deletion mechanism exists, and the fallback's legitimacy is bounded and reported.

- The ladder text owns the operator-ordered surface separately from loop child dispatch, so the landed default-in-waiting ordering keeps governing child dispatch unchanged.
- The per-toolset deletion mechanism is named, and the ladder paragraph owns the degraded-toolset rule itself as a terminal-shaped park (intent record plus payload copy), instead of unwritten convention or the landed listing-only rung's predicate.
- The schedule ask contract carries the exhaust-delete-first bound by name, so the ordering is discoverable from the verb's own section.

Gate delta: none - no refusal class, gate, fence, protocol layer, or schema field is added or removed; the change is warning-shaped operative text plus stability needles over spans the plan declares stable. The per-toolset probe leg is read-only and warning-shaped, so no blocking-gate admission record is required; the incident is carried by the origin row and the grouping entry's admission block.

## Assumptions

- assume the re-arm surface's landed delete-first ordering (the in-message delete of the state-recorded record before the create) stays byte-stable; basis: the landed ladder text and the executed landing 8d72b319a on main, verified 2026-10-17.
- assume loop child dispatch's launchd default-in-waiting stays as landed and this plan does not re-order child dispatch; basis: the same executed landing's scope, verified 2026-10-17.
- assume the interactive toolset probe finds no Bash-side deletion surface today (no automation command, no host-store automations table); basis: the 2026-10-17 disk probe recorded in the grouping entry's Orientation and the origin row's Witness (the 2026-10-16 interactive no-op echo).
- assume the sibling plan's satisfaction sentences are NOT yet in AGENTS.md: its landing 06eb1202f carried no AGENTS.md edit, so the section carries only the original bullet on disk; this plan lands those declared sentences verbatim in the same Task 2 edit and the run report surfaces the sibling landing's missing operative edit; basis: the landing's diffstat on main and the AGENTS.md section bytes, verified 2026-10-17.
- assume the grouping entry's scope arm 3 discharges as: the operator correction binds this plan's operator-ordered surface paragraph and stands recorded as binding input to the covering plan's arm-3 promotion review, so the future activation decision cannot cite the covering plan's terms alone; basis: the grouping entry's scope arm 3 read against the executed landing 8d72b319a.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the ladder paragraph carries all three origin-ask elements: delete-own-spawner exhausted first, the per-toolset deletion mechanism named with the degraded-toolset rule, and the fallback bounded to a recorded deletion attempt or a proven-absent deletion primitive.
- minimality: warning-shaped text only, no new gate, validator, or state field; the schedule ask contract gains one bound clause, not a second ordering home.
- readability: a bound-session reader finds the ordering from either the ladder section or the schedule ask section, each naming the other once.

**Done when:**
- the dispatch ladder carries the operator-ordered schedule surface paragraph with the exhaust-delete-first ordering, the fallback legitimacy bound, and the report-names-the-exhausted-leg duty.
- the schedule ask contract carries the exhaust-delete-first bound naming the ladder paragraph as the ordering owner.
- the pins suite exits 0 with the new stability needles green: one count pin over the re-arm surface's delete-first ordering sentence and presence pins over the schedule ask contract's create-then-report and never-executes-inline clause literals, so every span the plan declares stable verifies mechanically.

**Ship when:**
- none; no deployed or human-owned condition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/template-authoring.md`
- `agents/skills/maintenance/survey-arms.md`
- `AGENTS.md`

**Tests:**
- `scripts/check_maintenance_pins.sh` (the Task 2 stability needles edit it by design; an existing needle moves only if a pinned span shifts, and the default shape inserts new needles between pinned spans)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the re-arm hygiene bullet's landed delete-first ordering; reason: landed by 083c6e883, rewritten and pinned by 8d72b319a, declared stable by this plan.
- the loop child dispatch default-in-waiting ordering; reason: the executed covering plan's scope, declared stable by this plan.
- `scripts/execute_plan_runtime.py`; reason: the clocked-order operation's behavior is unchanged; the plan binds when the fallback may be chosen, not how it arms.

## Validation Commands

```bash
bash scripts/check_maintenance_pins.sh
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh touched
bash scripts/scan-public-hygiene.sh
```

Task 2's Run step additionally carries the sibling plan's exact-once greps over the landed satisfaction sentences (its checks 1-4 and 7 literals, quoted from the sibling plan's Task 1 After block) and the check-8 token sweep re-scoped with the bound-clause span excluded.

### Task 1: The operator-ordered schedule surface paragraph in the dispatch ladder

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/template-authoring.md`
- `agents/skills/maintenance/survey-arms.md`

Primary class anchors:
- `zcode.md` in `agents/skills/maintenance/zcode.md`

- [x] The ladder carries an operator-ordered schedule surface paragraph: given a cap-refused `CronCreate` in a bound session holding a direct operator schedule order, expects the paragraph to order the delete-own-spawner leg first, the launchd fallback legitimate only after a recorded deletion attempt or a proven-absent deletion primitive, the report naming which leg was exhausted [class: IMPLEMENTATION_REQUIRED]
- [x] The paragraph names the Scheduling asks section once as the verb-side discoverability surface, and the section names the paragraph back through Task 2's bound clause [class: IMPLEMENTATION_REQUIRED]
- [x] The paragraph names the per-toolset deletion mechanism inventory: given the recorded 2026-10-17 disk-probe outcome, expects the paragraph to name, per toolset, the concrete deletion mechanism or its proven absence (the headless CLI session's automation primitives against a lingered record), before the degraded-toolset park applies [class: IMPLEMENTATION_REQUIRED]
- [x] The paragraph owns the degraded-toolset rule: given a toolset whose probe finds no deletion surface (the recorded 2026-10-17 outcome), expects a terminal-shaped park (intent record plus payload copy) as the sanctioned outcome, the park standing where no carrier arms [class: IMPLEMENTATION_REQUIRED]
- [x] The park discharges beside a carrier without duplication: given a verified launchd fallback arming, expects the same step to clear the parked record or record the carrier's id beside it as the satisfaction mark, so no discharge re-dispatches a carrier-carried payload [class: IMPLEMENTATION_REQUIRED]
- [x] The paragraph names the landed sibling orderings as boundaries: the re-arm surface's delete-first ordering, the loop child dispatch default-in-waiting, and the Clocked operator order duty's ownership of the incident surface, so the surfaces read as one ladder without restating each other [class: IMPLEMENTATION_REQUIRED]
- [x] The Clocked operator order duty's create-refusal leg routes through the new paragraph: given a clocked operator order whose in-session arm refuses, expects the duty text to order the exhaust-delete-first leg before the launchd chain and to park only when the degraded-toolset rule fires, replacing the chain-first park-on-refusal ordering on that leg [class: IMPLEMENTATION_REQUIRED]
- [x] The duty's blueprint and pickup twins reconcile to the same ordering: given the authoring blueprint's embedded clocked operator order duty and the survey pickup arm's refused-pickup sentence, expects each to route its refusal leg through the paragraph's exhaust-delete-first ordering instead of parking or chain-arming without the delete-first attempt [class: IMPLEMENTATION_REQUIRED]
- [x] The two assigned reconciliations are owned: given the sibling plan's Delivery-channel intent rule and its reduced-toolset reporting arms, expects one clause each naming which text governs (the decline-to-arm sanction against the exhaust-delete-first ordering; the park-or-launchd-carrier outcome reported beside the sibling's unscheduled-report duty) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the pins suite over the ladder region (the arm-guard pins and section anchors still present; the paragraph inserts beside them without moving pinned spans), then the em-dash and hygiene scans over the touched surface before the commit [class: REPOSITORY_TEST]
- [x] Commit: `docs: order delete-own-spawner before schedule-ask fallbacks in the ladder` [class: IMPLEMENTATION_REQUIRED]

### Task 2: The schedule ask contract carries the exhaust-delete-first bound

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `AGENTS.md`
- `scripts/check_maintenance_pins.sh` (the stability needles only)

Primary class anchors:
- `Scheduling asks (verb contract)` in `AGENTS.md`

- [x] The Scheduling asks section carries the sibling plan's declared satisfaction sentences verbatim (the session-ownership satisfaction clause, the deconfliction-context rule, and the unscheduled-report duty, from the sibling plan's own task wording), its original clauses byte-unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] The section carries one exhaust-delete-first bound clause, worded to name "the operator-ordered schedule surface paragraph in agents/skills/maintenance/zcode.md" as its ordering owner without the sibling plan's fenced tokens where the fence stands: given a schedule ask in a cap-refused bound session, expects the clause to require the delete-own-spawner leg exhausted first [class: IMPLEMENTATION_REQUIRED]
- [x] The clause records its fence supersession in the AGENTS.md clause text itself: given the sibling plan's validation block forbids its tokens inside this section, expects the landed clause to carry the supersession sentence adjudicating that fence for exactly this clause, and Task 2's Run step to carry the sibling block's exact-once greps over the landed sentences plus the check-8 token sweep re-scoped with the bound-clause span excluded [class: IMPLEMENTATION_REQUIRED]
- [x] The sibling plan's residue is dispositioned durably: given Task 2 lands the sibling's declared sentences, expects a one-line disposition note landed in the sibling plan file itself (its Task 1 satisfied by this landing, verified not re-applied; its remainder verify-only) beside the run-report line, so a later survey offer or executor reads the disposition before running its stale check-8 block [class: IMPLEMENTATION_REQUIRED]
- [x] Stability needles land in the same change: given the spans the plan declares stable, expects one count pin over the re-arm surface's delete-first ordering sentence in zcode.md, presence pins over the schedule ask contract's whole original bullet (framing prefix through the scheduling act, the sibling plan's check 6 form), its never-executes-inline literal, and the bound clause's owner-naming literal, keeping every deliverable and declared-stable span mechanically watched [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the pins suite with the new needles, the sibling exact-once greps (checks 1-4 and 7) and the re-scoped check-8 token sweep per the Validation Commands block, then the em-dash and hygiene scans over the touched surfaces [class: REPOSITORY_TEST]
- [x] Commit: `docs: bind the schedule ask fallback to the ladder delete-first ordering` [class: IMPLEMENTATION_REQUIRED]
