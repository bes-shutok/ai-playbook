# Plan: raced-pick continuation arm in the authoring payload contract

Backlog origin: docs/history/backlog/2026-11-06-authoring-payload-raced-pick-stand-down.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-11-06-plan-review-authoring-payload-raced-pick-continuation-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1.25h total, largest task 0.5h
Executed: yes (21a5630a8)
Authoring claim: 2026-11-06-authoring-payload-raced-pick-stand-down.md (session sess_59b05e7c-db01-42b6-8cd2-35da64f0478c)

## Terms

- Raced pick: a selection whose claim create refuses over a fresh foreign claim, or whose picked entry's worktree or branch appears between the pick and the create; the target-level race this plan prices.
- raced-(b): the recorded token for a raced pick; selection-rule unavailability condition (b) materialized after the pick, never an environmental stop gate.
- Availability conditions: the selection walk's two per-entry unavailability checks: (a) a `Frozen:` line on the entry, (b) a live authoring session for it (a fresh claim file keyed to the entry slug or one of its origins, or an existing authoring worktree or branch).
- Selection walk: the payload mandate's top-to-bottom availability walk over the rolling prompt log (file order is urgency), checking each entry's availability conditions.
- Claim create: the AUTHORING CLAIM duty's create-if-absent noclobber write of `docs/tmp/authoring-claims/<backlog-item-basename>.md`.
- Fresh-foreign-claim refusal: the pre-work gate's refuse-to-start over an existing claim file whose `updated:` is fresh (within one cadence period, 2 hours) and whose `session:` line names another session.
- Stale-foreign-claim takeover: the delete-then-create path over a foreign claim stale past one cadence period; unchanged by this plan.
- Back-to-back ordering: the walk and the claim create run adjacently, with the availability conditions re-verified from disk immediately before the create; the remaining start gates run after the create.
- Start gates: the covered and gone stand-down checks, the merge-or-rebase and done-lock checks, and the foreign-claim fire-time gate the pre-work gate paragraph runs before plan work.
- Own claim: this session's claim file, governed by the AUTHORING CLAIM duty's ownership-checked refreshes and deletes.
- Deferral-class trip: a guard trip the guards' User-directed override rule admits an interactive session past (the plain fleet-cap arms, a conservative admission refusal); distinct from the integrity stop gates, which are never overridable.
- Verified disjoint pick: an in-session pick whose target is disjoint from the peer material the tripped guard names (fresh claim set, live worktree, uncommitted dirt on shared paths).
- Override token: the `user-directed-override:<guard name>` decision-reason record the override rule orders.
- Blueprint-first lift: the origin entry's recommended arm shape: the arm lands in `agents/skills/maintenance/template-authoring.md`'s pre-work gate paragraph and the payload duties reference it, so mandates inherit it without per-payload wording.
- Directive lift: the `agents/skills/maintenance/zcode.md` rule that carrier prompt construction lifts lane directive text from a home at dispatch instead of baking aging clauses.
- Payload duties: the user-directed maintenance payload duties the Interactive dispatch template applies to interactive authoring asks.
- Cadence period: the 2-hour freshness bound shared by the claim gate, the G1a discovery arm, and the freeze rule.

## Why

The authoring payload contract's only named post-refusal branches stop the run: a fresh-foreign-claim refusal at claim time has no continuation arm, and the witnessed 2026-11-06 interactive authoring payload stood down 0/1 after losing the selection race to a firing idle carrier (the peer carried the pick regardless; the operator's authoring slot idled). The claim create and the availability walk are two separate moments, and a queued idle ticket becomes a live claim-bearing authoring run in minutes with no cancel primitive on the queued side, so the race window is material; the witnessed session also spent roughly eight minutes between the walk and the create on start-gate checks, widening it. The D2 selection consult already carries the skip-and-continue shape at selection time; the payload contract lacks the same complement after the pick.

## Gist & Examples

TLDR: the authoring payload contract gains the raced-pick continuation arm, so a fresh-foreign-claim refusal at claim time (or the picked entry's worktree or branch appearing) records the race as raced-(b) and continues the selection walk to the next available entry, the walk and the claim create run back-to-back, and an interactive session proceeds past deferral-class environmental trips on a verified disjoint in-session pick with the override token recorded, because a raced pick idles the operator's authoring slot while the peer carries the target anyway (efficiency).

Before (today): the claim-time refusal correctly protects the first writer's witness but leaves no productive move; the only named stop-and-report branches are environmental, so a target-level race reads as a full stand-down while the peer carries the target anyway.

After (this plan): the pre-work gate paragraph carries the raced-pick continuation arm beside the refusal: the refusal (or the picked entry's worktree or branch appearing) records raced-(b) with the foreign session id and continues the walk to the next available entry; the availability walk and the claim create run back-to-back with the availability conditions re-verified from disk immediately before the create and the remaining start gates after it, deleting the own claim on a gate refusal; environmental and integrity stop gates keep their stop semantics, and an interactive session proceeds past deferral-class environmental trips per the guards' User-directed override clause with the token recorded; the payload duties lift the arm from the blueprint instead of baking wording.

Example: an interactive author mandate walks the log, picks the first available entry, re-verifies the availability conditions from disk, and issues the noclobber create; the create refuses over a fresh foreign claim created minutes earlier by an idle carrier that just fired. The session records raced-(b) with the foreign session id and its `updated:` timestamp, continues the walk to the next available entry, and authors that entry's plan instead of standing down 0/1.

Edge cases: a genuinely concurrent second writer is still refused exactly as today (the refusal and its 2-hour freshness bound are preserved unchanged, and the raced pick's loser never clobbers the foreign witness); a stale foreign claim still takes the takeover path unchanged; an integrity gate (merge or rebase in progress, done lock held over owned writes, the failure cap) keeps its stop semantics; an unattended session keeps today's stand-down semantics, the override arm being interactive-only; a walk that exhausts the log after a raced pick ends in the mandate's ordinary empty-queue stop with the races recorded.

## Outcome

An authoring session that loses a selection race continues to the next available entry under its unchanged mandate instead of standing down, while the concurrent-writer protection stays exactly as witnessed.

- A claim-time fresh-foreign-claim refusal (or the picked entry's worktree or branch appearing) produces a recorded raced-(b) and a continued walk, never a 0/1 stand-down on its own.
- The availability walk and the claim create run back-to-back, shrinking the race window from minutes to seconds; the remaining start gates run after the create and delete the own claim on a refusal.
- An interactive session proceeds past deferral-class environmental trips on a verified disjoint in-session pick, recording the override token.
- The fresh-foreign-claim refusal and its 2-hour freshness bound are preserved unchanged.
- Gate delta: none (payload-contract text beside an existing refusal; no gate, validator, lock, ledger, or required ceremony added or removed; the arm removes a stand-down outcome class, the raced-pick 0/1 stop, while the fresh-foreign-claim refusal and its freshness bound are preserved, per the served PLAN-PROMPTS entry's "Machinery admission:" record for authoring-payload-raced-pick-continuation, which states no admission test applies).

## Assumptions

- assume the fresh-foreign-claim refusal and its 2-hour freshness bound stay byte-identical; the arm adds only the continuation complement beside them; basis: the served PLAN-PROMPTS entry's "Continuity disposition:" and "Scope arms:" record 3 for authoring-payload-raced-pick-continuation.
- assume a claim-time refusal over a picked target is availability condition (b) materialized after the pick, not an environmental stop gate; basis: the origin row's "Observed vs expected" record and the guards' enumeration, whose stop gates are environmental.
- assume the back-to-back ordering is a payload-shape duty for the selection-walk authoring form, not a change to the covered and gone gate semantics: the re-verification covers the availability conditions from disk immediately before the create, and the remaining start gates still run, only after the create; basis: the served PLAN-PROMPTS entry's "Scope:" record and the AUTHORING CLAIM duty's existing ownership-checked delete on owned stand-downs.
- assume the deferral-override statement rides the blueprint lift, citing the guards' User-directed override rule as the source of record; `agents/skills/maintenance/guards.md` itself is unamended; basis: the served PLAN-PROMPTS entry's "Rejected alternatives:" record 2 (the override bullet already admits interactive sessions past the plain fleet-cap arms).
- assume text-pinning regression coverage is the right test shape for a Markdown payload contract, scoped to the owning spans; basis: `scripts/test_maintenance_runtime_scope.py`'s stated convention and the served PLAN-PROMPTS entry's work-type verdict requiring regression coverage that the refusal protection still fires.
- assume the incident narrative stays in the origin row; skill text cites it in at most one line (the arm's dated added-note); basis: the repository guidelines' skill-text anti-growth rules.

Decision points requiring a grill: none remain (all resolved by recorded receipt under the maintenance-selected standing authorization; arm placement in the pre-work gate paragraph, the preserved refusal, and the blueprint-first lift are fixed by the served PLAN-PROMPTS entry's "Scope:", "Continuity disposition:", and "Scope arms:" records for authoring-payload-raced-pick-continuation).

## Standing constraints

- Machinery admission protocol: the arm adds no gate, validator, lock, ledger, or required ceremony; it is payload-contract text beside an existing refusal, and from the run-loss perspective it removes a stand-down outcome class.
- Refusal preservation: the fresh-foreign-claim refusal, its freshness bound, and the stale-foreign-claim takeover keep their exact semantics; the arm adds only the raced-pick complement.
- Skill-text anti-growth: the arm and the lift cite the origin row in at most one line; the byte-budget gate over the touched skill files must pass with its output recorded (warning-only posture).

## Evaluation Criteria

**Quality dimensions:**
- correctness: the arm fires exactly on a claim-time refusal over a picked target or on the picked entry's worktree or branch appearing, records raced-(b) with the foreign session id, and continues the walk; integrity and environmental stop gates keep their semantics
- completeness: the back-to-back ordering, the post-create gate order with the own-claim delete, the override statement with its token, and the payload-duty lift are all present; the refusal and freshness-bound tokens are pinned unchanged
- economy: the arm cites the guards rule and the origin by reference, grows the paragraph by its net delta, and adds no machinery

**Done when:**
- the raced-pick continuation arm exists in `agents/skills/maintenance/template-authoring.md`'s pre-work gate paragraph with the record-and-continue shape, the back-to-back ordering, and the override statement
- the payload duties in `agents/skills/maintenance/zcode.md`'s Interactive dispatch template lift the arm from the blueprint instead of restating it
- the text-pinning suite passes against the amended text, including the preserved-refusal tokens
- the maintenance pins suite and the hygiene scan exit 0; the byte-budget gate runs with its output recorded (warning-only)

**Ship when:**
- none stated (repository-verifiable work only)

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/template-authoring.md` (Task 2)
- `agents/skills/maintenance/zcode.md` (Task 3)

**Tests:**
- `scripts/test_authoring_raced_pick_continuation.py` (Task 1) *(new)*
- `scripts/check_maintenance_pins.sh` (Task 2) *(conditional span-token adjustment only; see Task 2)*

**Backlog:**
- `docs/history/backlog/2026-11-06-authoring-payload-raced-pick-stand-down.md` (review-only) *(covered flip rides the landing)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/guards.md`; reason: the User-directed override rule already admits interactive sessions past deferral-class trips; the payload lifts that authorization by citation instead of amending the rule
- `agents/skills/maintenance/decisions.md`; reason: D2's fresh-foreign-claim consult already carries the selection-time skip-and-continue shape this arm complements
- `agents/skills/maintenance/template-execution.md`; reason: the execution lane's payload is not this arm's home
- `scripts/done_run.sh`, `scripts/done-lock.sh`; reason: the claim machinery is unchanged; the arm is contract text beside the existing refusal

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_authoring_raced_pick_continuation.py -q
bash scripts/check_maintenance_pins.sh
bash scripts/scan-public-hygiene.sh
python3 scripts/skill_text_budget.py --check
```

### Task 1: Regression coverage pinning the raced-pick continuation arm and the preserved refusal

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_authoring_raced_pick_continuation.py` *(new)*

Primary class anchors:
- `Raced-pick continuation` in `agents/skills/maintenance/template-authoring.md`

- [x] New unittest suite following `scripts/test_maintenance_runtime_scope.py`'s stated convention (a Markdown policy pinned by normative tokens inside the owning span): extract the pre-work gate paragraph of `agents/skills/maintenance/template-authoring.md` (the paragraph beginning "Before writing anything: verify no merge or rebase is in progress") with a paragraph-extraction helper [class: REPOSITORY_TEST]
- [x] The same suite asserts, inside that paragraph span, the arm-identity tokens: the arm name "Raced-pick continuation", the classification span "selection-rule unavailability materialized after the pick", the record token "raced-(b)", and the continuation span "continues the walk to the next available entry" [class: REPOSITORY_TEST]
- [x] The same suite asserts, inside the paragraph span, the ordering tokens: the adjacency span "back-to-back", the re-verification span "immediately before the create", and the post-create span "deleting the own claim on a gate refusal" [class: REPOSITORY_TEST]
- [x] The same suite asserts, inside the paragraph span, the override tokens: the interactive span "interactive session proceeds past deferral-class environmental trips", the disjoint-pick span "verified disjoint in-session pick", and the guards citation "User-directed override" [class: REPOSITORY_TEST]
- [x] The same suite asserts the preserved-refusal tokens still present in the paragraph span: the refusal span "refuse to start: stand down and write nothing", the freshness bound "within one cadence period, 2 hours", the witness-preservation span "a second writer must never clobber the first writer's witness", and the takeover token "Stale-foreign-claim takeover" [class: REPOSITORY_TEST]
- [x] The same suite asserts, inside `agents/skills/maintenance/zcode.md`'s Interactive dispatch template section span, the lift tokens: the section header "## Interactive dispatch template", the blueprint citation "template-authoring.md", and the lift span "raced-pick continuation arm" [class: REPOSITORY_TEST]
- [x] The same suite also asserts, inside that section span, the Task 3 citation tokens: the lift-precedent citation "Directive lift", the dated origin-row note "authoring-payload-raced-pick-continuation origin row", and the override source naming "User-directed override" [class: REPOSITORY_TEST]
- [x] The same suite also asserts, inside the payload-block AUTHORING CLAIM DUTY segment of `agents/skills/maintenance/template-authoring.md` (the segment containing the sentence "a noclobber create refused by an existing claim file is a foreign or parallel claim on the item", which occurs exactly once in the file) [class: REPOSITORY_TEST]
- [x] The same suite pins, inside that segment, the continuation tokens: the arm name "raced-pick" and the continuation span "continues the walk", so the payload-side refusal sentence carries the same continuation as the body-side gate paragraph [class: REPOSITORY_TEST]
- [x] Run → expect RED: the suite fails at the current tree because every span-scoped assertion of an arm-unique token fails inside the owning spans; every preserved-refusal assertion is a persistence pin expected to pass at RED [class: REPOSITORY_TEST]
- [x] Commit: `test: pin raced-pick continuation arm tokens` [class: IMPLEMENTATION_REQUIRED]

### Task 2: The raced-pick continuation arm in the authoring blueprint's pre-work gate paragraph

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/template-authoring.md`
- `scripts/check_maintenance_pins.sh` *(conditional span-token adjustment only)*

Primary class anchors:
- `Raced-pick continuation` in `agents/skills/maintenance/template-authoring.md`

- [x] Insert the raced-pick continuation arm as its own dated sentence in the pre-work gate paragraph, immediately beside the fresh-foreign-claim refusal text and before the stale-foreign-claim takeover sentence; the arm sentence opens exactly "Raced-pick continuation (added 2026-11-06, the authoring-payload-raced-pick-continuation origin row):" so the Task 1 arm-name pin matches the prescribed bytes [class: IMPLEMENTATION_REQUIRED]
- [x] The arm's first clause classifies the trigger: a fresh-foreign-claim refusal at claim time over a target this session's mandate already picked (the mandate's own selection walk or its deciding turn's selection), or the picked entry's worktree or branch appearing, is selection-rule unavailability materialized after the pick [class: IMPLEMENTATION_REQUIRED]
- [x] The arm's second clause orders the continuation: the session records raced-(b) with the foreign session id and the claim's `updated:` timestamp and continues the walk to the next available entry under the unchanged mandate [class: IMPLEMENTATION_REQUIRED]
- [x] The same amendment reaches the file's payload-side AUTHORING CLAIM DUTY paragraph: the refusal sentence "a noclobber create refused by an existing claim file is a foreign or parallel claim on the item: stand this session down before any plan work" gains the same raced-pick continuation (a refusal over an already-picked target records raced-(b) and continues the walk per the body-side arm), keeping the never-clobber and no-touch-foreign-witness protections unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Evaluate the pre-work compact-mirror block ("PRE-WORK STAND-DOWN GATES"): it mirrors the covered and gone and the merge-or-rebase and done-lock gates and carries no foreign-claim refusal sentence, so it needs no raced-pick amendment; record this evaluation in the run log [class: IMPLEMENTATION_REQUIRED]
- [x] The arm carries the back-to-back ordering: the availability walk and the claim create run adjacently, with the availability conditions re-verified from disk immediately before the create, and the remaining start gates (the covered and gone checks, the merge-or-rebase and done-lock checks) run after the create, deleting the own claim on a gate refusal per the AUTHORING CLAIM duty's ownership-checked delete, so the race window shrinks from minutes to seconds [class: IMPLEMENTATION_REQUIRED]
- [x] The arm states the stop-gate carve-out: environmental and integrity stop gates keep their stop semantics, and an interactive session proceeds past deferral-class environmental trips (the plain fleet-cap arms, a conservative admission refusal) on a verified disjoint in-session pick per the guards' User-directed override rule with the override token recorded; integrity guards are never overridable and unattended sessions keep today's stand-down semantics [class: IMPLEMENTATION_REQUIRED]
- [x] The arm cites its origin in one line ("the authoring-payload-raced-pick-continuation origin row") and leaves the fresh-foreign-claim refusal, its freshness bound, and the stale-foreign-claim takeover unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN on the template-authoring.md assertions: the Task 1 suite's template-authoring.md span assertions pass against the amended text; the suite's zcode.md lift-span assertions stay RED until Task 3 lands [class: REPOSITORY_TEST]
- [x] Run the maintenance pins suite and the hygiene scan, expects exit 0 on both; where an existing pins assertion's span-scoped expectation fails over the amended paragraphs, adjust that assertion's span tokens to the amended text in the same change, never deleting an assertion, and record the adjustment in the run log; run the fleet-wide byte-budget gate (`python3 scripts/skill_text_budget.py --check`) and record its output (the breach report) in the run log, exit 0 expected [class: REPOSITORY_TEST]
- [x] Commit: `docs: add raced-pick continuation arm to the authoring payload blueprint` [class: IMPLEMENTATION_REQUIRED]

### Task 3: The payload duties lift the arm from the blueprint

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/zcode.md`

Primary class anchors:
- `Interactive dispatch template` in `agents/skills/maintenance/zcode.md`

- [x] Add one dated sentence to the Interactive dispatch template section's user-directed payload duties paragraph in `agents/skills/maintenance/zcode.md`: an interactive authoring mandate carries the raced-pick continuation arm, the back-to-back walk-and-create ordering, and the deferral-override statement lifted from the blueprint (`agents/skills/maintenance/template-authoring.md`'s pre-work gate paragraph) instead of baked per-payload wording [class: IMPLEMENTATION_REQUIRED]
- [x] The same sentence cites the Directive lift rule's home precedent, cites the origin row once (the dated added-note form), and names the guards' User-directed override rule as the override's source of record [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the full Task 1 suite passes, the zcode.md lift-span assertions now included [class: REPOSITORY_TEST]
- [x] Run the maintenance pins suite and the hygiene scan, expects exit 0 on both; run the fleet-wide byte-budget gate (`python3 scripts/skill_text_budget.py --check`) and record its output in the run log, exit 0 expected [class: REPOSITORY_TEST]
- [x] Commit: `docs: lift raced-pick continuation arm into the payload duties` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-11-06-authoring-payload-raced-pick-stand-down.md: covered by this plan's execution (branch 2026-11-06-raced-pick-continuation, pre-squash tip 21a5630a8 (rebased post-verification onto main@12e45a28e)); the row's execution flip records the completed-archive witness.

## Disposition of execution residuals

- Phase 3 r1 two-lens panel: zero blocking; residual candidates filed as docs/history/backlog/2026-11-06-raced-pick-ordering-precedence-tension.md and docs/history/backlog/2026-11-06-raced-pick-pin-hardening-residuals.md (commit 0fe5bb8df).
- Digest re-bind: r4 focused delta round over the executed bytes (source_digest 5b5019ead732e46456d1dad86e51ddb3a5c9de5dbc4f368c1af6652e890813f2), record pair .ai-playbook/reviews/2026-11-06-plan-review-authoring-payload-raced-pick-continuation-pbf01e2c0-r4.{md,stats.json}.
- Byte-budget gate: warning-only advisory breaches pre-existing (template-authoring.md, zcode.md), outputs recorded in the run log per the plan's standing constraint.
