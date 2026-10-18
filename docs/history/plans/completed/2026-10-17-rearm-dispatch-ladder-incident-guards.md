# Plan: re-arm dispatch-ladder incident guards

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-16-automation-spawner-ownership-inference-peer-delete.md`
- `docs/history/backlog/2026-10-16-automation-create-misroute-after-carrier-delete.md`
- `docs/history/backlog/2026-10-16-loop-child-dispatch-launchd-collapse.md`
- `docs/history/backlog/2026-10-13-rearm-cap-lift-delete-target-own-spawner.md`
- `docs/history/backlog/2026-10-08-rearm-confirming-listing-truncation-arm.md`
- `docs/history/backlog/2026-10-10-clocked-order-discharge-no-payload-session.md`

Grouping entry: docs/history/backlog/PLAN-PROMPTS.md, `## rearm-dispatch-ladder-incident-guards` (its Prompt, scope arms, admission wording, and rejected alternatives are this plan's spec of record).

Driving force: reliability (off the driving-principle taxonomy; implemented anyway because this repository's product is an unattended, hands-off maintenance loop, and the witnessed incident class, foreign automation records deleted plus misdirected create emissions leaving the loop dark, recurs without the guards; park-triage would not take it because the harm landed once and the near-miss predates the park machinery)

Plan review record: the staging series .ai-playbook/reviews/2026-10-17-plan-review-rearm-dispatch-ladder-incident-guards-p7ffd23f5-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)

Execution budget: 2h total, largest task 0.5h

Authoring claim: docs/tmp/authoring-claims/rearm-dispatch-ladder-incident-guards.md (session sess_dbec0621-d67c-458d-9416-9f7a02107f3b; stale-claim takeover from sess_6556bee4-5d0c-4e20-926d-43bd49707871, 2026-10-17)

## Terms

- re-arm dispatch ladder: the operative steps a maintenance session follows to keep the loop carrier armed and to dispatch children (delete-plus-create, rollback, escalation), defined in the runtime overlay `agents/skills/maintenance/zcode.md` ("Dispatch ladder", "Recurring automation recipe").
- ownership allowlist: the rule that a session may delete only automation records whose ids its own lineage's state file records as its spawner or created child; anything else is untouchable and parks for the operator.
- lingered-completed record: a one-shot automation that fired and remains listed with enabled false and lifecycle completed.
- post-delete probe: one read-only automation listing taken after any delete and before the next create, as that create's decision input.
- distinct-failure rollback: a retry after a failed automation create must change mechanism rather than re-issue the identical failed emission; a repeated identical failure parks the loop with the intent recorded.
- arm (1, 2, 3): this plan's three guard arms, numbered as the grouping entry's scope arms number them: arm 1 the ownership allowlist, arm 2 the post-delete probe with the distinct-failure rollback, arm 3 the launchd default-in-waiting and the rung demotion.
- cap-lift delete: an automation-record delete performed to lift the automation-born cap before a create.
- default-in-waiting: the launchd chain's posture under this plan: named, priced, and guarded, but not the operative dispatch default until the promotion review activates it.
- truncation arm: the 2026-10-08 decision rule for a listing-as-decision-input step reading a truncated listing: never read absence from the visible prefix, never re-poll; adjudicate fail-safe and record the truncation.
- covered flip: the landing-time status change of an origin backlog row to covered with its covering-plan witness (the plan lifecycle's landing closeout).
- launchd clocked-order chain: the host scheduler path that records and arms an ordered payload through `scripts/execute_plan_runtime.py --operation clocked-order-schedule`; unbound to any automation record.
- automation-born cap: the host rule that a session bound to an automation record cannot create another until the binding lifts.
- recognition rule: the title plus prompt-opening plus repository-root match that identifies the loop carrier in an automation listing; repo-scoped, so it cannot discriminate lineages.
- promotion review: the future decision that flips the launchd chain from default-in-waiting to the operative child dispatch for bound sessions, gated on the clocked-order gap row's disposition.

## Why

The 2026-10-16 incident deleted two peer-lineage lingered spawner records and then burned five misdirected create emissions on fabricated ids before the surface stood down, leaving the loop dark for one window. Both harm legs are consequences of the ladder's own text: its live-child stand-down stops at ENABLED records, so the lingered-completed class is unprotected, and its rollback retries the identical create, so a deterministic misroute consumed the whole budget. Text discipline can make the class unreachable.

## Gist & Examples

TLDR: guard the re-arm dispatch ladder with an ownership allowlist, a post-delete probe with a distinct-failure rollback, and a demotion of the delete-plus-create rungs behind a launchd default-in-waiting, so the witnessed delete-and-misroute incident class cannot recur through ladder text alone, for reliability.

Before: a cap-lift delete targets records by prompt recognition alone; two peer-lineage lingered records match the template and are deleted. After: the allowlist admits only the session's own state-recorded ids, so a foreign lingered record is never emitted a delete, and the dispatch parks for the operator instead.

Before: a post-delete create misfires on a fabricated id; the rollback re-issues the same primitive and the emission repeats until the surface stands down. After: one read-only probe precedes the first create, and the first not-on-a-supplied-id refusal or second identical failure parks the loop with the intent recorded instead of repeating.

Before: a bound session must delete its armed record to create a child, so the cap-lift delete is on every dispatch's critical path. After: the launchd chain is the named default-in-waiting whose activation is the promotion review's decision once the clocked-order gap row is dispositioned; the delete-plus-create rungs stay operative only as a documented fallback behind the two new rule sets, so the incident's machinery is guarded and priced for removal rather than preserved.

## Outcome

The re-arm and child-dispatch surfaces carry standing rules that make the witnessed incident class unreachable by text discipline, and the machinery that produced it is demoted and priced for removal rather than preserved.

- A cap-lift delete can only ever target ids the session's own lineage state records; foreign records, live or lingered, are never emitted a delete and park for the operator.
- A failed post-delete create parks the loop with its intent recorded instead of repeating the identical emission, and the sanctioned mechanism switch is the launchd chain that needs no automation-record create.
- The launchd clocked-order chain is the named default-in-waiting for bound-session child dispatch, with its activation gated on the promotion review after the clocked-order gap row's disposition; until then the guarded fallback stays operative, so the loop's delivery path never depends on an unproven default.

Gate delta: none added and none removed in the counted classes; the change is warning-shaped skill text only (no new refusal class, hard gate, fence, protocol layer, validator, or state-schema field; the pin rows Task 4 registers are the standing companion duty for operative-text changes, not a new gate). The structural changes are two removals of operative rungs, both named: arm 1 retires the ladder's null-id sole-span-match fallback delete (the ownership allowlist leaves a null recorded id no admissible delete target, so the Otherwise arm's span-match fallback becomes an operator park), and arm 3's demotion stops the unconditional mid-session delete-plus-create path from being the default child dispatch for sessions already bound to an armed record, demoting it to a documented fallback firing only behind the arm-1 and arm-2 rule sets, with the launchd chain named as the default-in-waiting whose activation is gated by the promotion review; arm 2 additionally narrows the rollback sentence's identical-retry allowance under the distinct-failure rollback rule and adds the post-delete probe listing to the dispatch-discipline exception enumeration (an exception-list addition, not a new gate); the recycling-optimization leg's status is unchanged (already demoted and flip-gated). No existing refusal, check, or state-schema field is removed. Machinery admission (arms 1 and 2, recorded here per the repository's Machinery admission protocol): incident, the state file's 2026-10-16T15:52 note plus the near-miss row docs/history/backlog/2026-10-13-rearm-cap-lift-delete-target-own-spawner.md; expected catch, every future cap-lift delete or post-delete create on this ladder (three witnessed hit or near instances in four days); false-positive cost, a parked dispatch or re-arm discharged mechanically by the next primitive-capable actor, bounded and self-healing (witnessed by the 2026-10-16 16:12 first-try recovery); review, the next friction-audit registry cycle after this landing, which reads the rules' witnessed parks in turn outputs and decision_reason records as its cost evidence, and in any case the arm-3 promotion review, whichever comes first; the two reviews ask different questions (the guard park costs, then the dispatch default), so neither stands in for the other.

## Assumptions

- assume the change stays text-only (no validator, state-schema, or gate-mechanism edit); basis: the grouping entry's warning-shaped-text-only constraint; registering companion pin rows in scripts/check_maintenance_pins.sh is the standing companion duty for operative-text changes, not a new gate, so Task 4 registers them.
- assume duties-core.md carries the child-side re-arm copy and is amended in the same change as the overlay; basis: the authoring payload's RE-ARM FIRST ACTION pointer and the duties-core header naming it the byte-identical shared duty set.
- assume the pins suite is green to amend against; basis: `bash scripts/check_maintenance_pins.sh` exits 0 on the authoring base (verified 2026-10-17).
- assume recognition matching cannot discriminate lineages because it is repo-scoped; basis: the recognition rule's three conjuncts (title, prompt opening, repository root) in the runtime overlay; the origin row docs/history/backlog/2026-10-16-automation-spawner-ownership-inference-peer-delete.md recording that own is decided by prompt-text recognition against one repository's template; and the state file's 2026-10-16T15:52 note recording the two deletions themselves.
- assume the one-assistant-message delete-plus-create shape yields to the post-delete probe when the probe intervenes; basis: the dispatch-discipline section's own exception concept, which already admits duty-mandated listings between mutations.
- origin-row disposition (recorded, per the Done-when mapping): rows 2026-10-16-automation-spawner-ownership-inference-peer-delete.md and 2026-10-16-automation-create-misroute-after-carrier-delete.md are served by Task 1 and Task 2; row 2026-10-16-loop-child-dispatch-launchd-collapse.md is served by Task 3 with its promotion arm gated exactly as the row suggests; row 2026-10-08-rearm-confirming-listing-truncation-arm.md is served in its probe leg by the probe's truncation-arm inheritance, with a recorded narrowing: the other surfaces that row's Expected names (the re-arm ladder's confirming listing, the turn-start duty's listing arms, the pending-rearm armed verification) are not touched by this plan and remain that row's open residual for a later cycle or an operator decision; row 2026-10-10-clocked-order-discharge-no-payload-session.md stays the open gate row and is covered, not closed, by Task 3's citation; row 2026-10-13-rearm-cap-lift-delete-target-own-spawner.md is served with a recorded narrowing: its expected fix (the delete-first ordering covering both the recorded carrier id and the session's own spawner record) is preserved, while the case its body also implies, deleting a divergent third record that is neither, deliberately parks under the allowlist instead of deleting; the safety narrowing is this plan's answer to that row and is recorded here as its disposition.

Decision points requiring a grill: none remain.

## Standing constraints

- Every new sentence is warning-shaped text: it directs and records; it adds no gate, validator, refusal path, or state-schema field; the removals name the rungs they retire (arm 1: the null-id sole-span-match fallback delete; arm 3: the delete-plus-create default for bound sessions) and the review the activation waits behind.
- Witness budget: each rule cites its incident in at most one line; the narrative lives in the origin rows and the state file notes.
- External pin reconciliation: a task edit that touches a literal pinned by scripts/check_maintenance_pins.sh reconciles the pin beside its provenance comment in the same edit; Task 4 registers the new rows, and the suite runs green in Validation Commands.
- Committed files carry no em-dash and no absolute user paths; the pin suite's advisory pilot-over lines are warning posture and never move an exit.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each rule's text matches the incident facts re-derived from the state file's 2026-10-16T15:52 and 16:12 notes and the named origin rows; a reviewer can trace every witness link to its recorded source.
- enforceability: every insertion span is pinned by a dedicated fail-closed validation grep that is RED on the authoring tree and GREEN after its task lands.
- anti-growth: the three skill files grow only by the arm sentence sets and their one-line witness citations; no other operative prose changes.

**Done when:**
- the Validation Commands block exits 0 on the finished tree.
- the pins suite exits 0 with no new breach line.
- each of the six origin rows is either covered by the landing (per the lifecycle's covered flip with receipts) or named in the recorded Assumptions disposition.

**Ship when:**
- none stated.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/duties-core.md`
- `agents/skills/maintenance/SKILL.md`

**Tests:**
- `scripts/check_maintenance_pins.sh` (the pin rows are this plan's verification surface)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- any `scripts/*` path other than `scripts/check_maintenance_pins.sh`; reason: the change is text-only by constraint, and the pins registry is its single scripted companion.
- the six origin backlog rows and docs/history/backlog/PLAN-PROMPTS.md; reason: the rows close through the landing's covered-flip rider with receipts and the entry prunes through the log's own landing-rider prune rule, not through plan tasks.

## Validation Commands

```bash
# Run from the repository root. RED-today: every span pin below fails on the
# authoring tree and flips GREEN exactly when its task's insertion lands.
cd "$(git rev-parse --show-toplevel)" || exit 1

fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }

# External pin suite over the touched skill files (advisory pilot-over lines
# are warning posture; the suite's own exit decides).
bash scripts/check_maintenance_pins.sh || fail "pins suite"
# Em-dash and hygiene over the changed set.
bash scripts/check-no-em-dash.sh touched || fail "em-dash"
if bash "${HOME}/.ai-playbook/scripts/scan-public-hygiene.sh"; then :; else fail "hygiene"; fi

# Count-exact span pins, one dedicated grep per obligation.
expect1() { n=$(grep -oF -- "$2" "$1" | wc -l | tr -d ' '); [ "$n" -eq 1 ] || fail "expect 1 hit in $1 for: $2 (got $n)"; }
# Arm 1 (ownership allowlist).
expect1 agents/skills/maintenance/zcode.md "Ownership allowlist (every automation delete on this ladder)"
expect1 agents/skills/maintenance/zcode.md "A null recorded id has no deletable record"
expect1 agents/skills/maintenance/zcode.md "Bind at create: a successful create's returned id"
expect1 agents/skills/maintenance/zcode.md "the ownership allowlist is the test and recognition matching is repo-scoped"
expect1 agents/skills/maintenance/zcode.md "stay the delete-first targets"
expect1 agents/skills/maintenance/zcode.md "never a span-matched fallback delete"
expect1 agents/skills/maintenance/zcode.md "the Otherwise arm below parks that dispatch for the operator per the ownership allowlist"
expect1 agents/skills/maintenance/zcode.md "Form-unknown or a recorded recurring form"
expect1 agents/skills/maintenance/duties-core.md "never any other lingered record in the listing"
expect1 agents/skills/maintenance/SKILL.md "The overlay's ownership allowlist governs every automation delete"
# Arm 2 (post-delete probe, distinct-failure rollback, emission-shape reconciliation).
expect1 agents/skills/maintenance/zcode.md "Post-delete probe: after any automation delete on this ladder"
expect1 agents/skills/maintenance/zcode.md "Distinct-failure rollback: a retry after a failed create must change mechanism"
expect1 agents/skills/maintenance/zcode.md "never re-poll against the same cap"
expect1 agents/skills/maintenance/zcode.md "the distinct-failure rollback rule supersedes the identical-retry budget"
expect1 agents/skills/maintenance/zcode.md "and the post-delete probe listing), which precedes or intervenes"
expect1 agents/skills/maintenance/zcode.md "plus the mandated post-delete probe listing between them"
expect1 agents/skills/maintenance/duties-core.md "one read-only listing probe precedes the create"
# Arm 3 (demotion names the retired rung class and the activation gate).
expect1 agents/skills/maintenance/zcode.md "Demoted fallback (arm 3)"
expect1 agents/skills/maintenance/zcode.md "stops being the default child dispatch for sessions already bound to an armed record"
expect1 agents/skills/maintenance/zcode.md "takes over as the operative default for bound sessions only when the promotion review"

echo "VALIDATION OK"
```

### Task 1: ownership allowlist for automation deletes

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/duties-core.md`
- `agents/skills/maintenance/SKILL.md`

- [x] Insert the allowlist rule set into the overlay's Re-arm hygiene bullet, spliced after the semicolon that ends the clause "and a create cap-refusal after an in-message delete takes the existing escalation paths with no further emission;" (the splice point is the semicolon, never mid-sentence), using insertion A below. [class: IMPLEMENTATION_REQUIRED]
- [x] Capitalize the splice continuation's first word so the mid-chain seam reads as a sentence boundary: "form-unknown or a recorded recurring form keeps" becomes "Form-unknown or a recorded recurring form keeps". [class: IMPLEMENTATION_REQUIRED]
- [x] Widen the ladder's live-child stand-down in the Dispatch ladder's automation-born step: append the widening sentence after the sentence ending "record `turn_error: armed-child-record-conflict` and stop without deleting or creating.", using insertion B below. [class: IMPLEMENTATION_REQUIRED]
- [x] Mirror the allowlist in the child-side FIRST ACTION copy: append insertion C below to the duties-core.md step (3) sentence ending "deleting your own lingered completed spawner record first when the create is refused for the automation-born cap". [class: IMPLEMENTATION_REQUIRED]
- [x] Mirror the allowlist in the maintenance SKILL.md Step 0 turn-start carrier re-arm duty: add insertion D below as a new sentence after the sentence ending "the check's listing-derived bookkeeping edits and its child-duty exemption are unchanged)." (a new sentence, never spliced onto a period or semicolon). [class: IMPLEMENTATION_REQUIRED]
- [x] Amend the ladder's null-id references so the retirement is enacted at every sentence that orders or advertises the fallback: replace the parenthetical "(fall back to the listing's sole span-match automation when the id is null)" with insertion H below, and replace the pointer parenthetical "(the Otherwise arm below falls back to its sole span-match automation when the id is null)" with insertion H2 below (both spans count-exact 1 in zcode.md today). [class: IMPLEMENTATION_REQUIRED]
- [x] Run the arm-1 span pins from Validation Commands and confirm each flips GREEN. [class: REPOSITORY_TEST]

Prescribed insertions (exact text):

Insertion A (agents/skills/maintenance/zcode.md, Re-arm hygiene bullet):

"Ownership allowlist (every automation delete on this ladder): the only records a session may delete are ids its own lineage's state file records as its own, either the recorded parent_automation_id or a children[] automation_id that the same lineage wrote; a delete that would target any other listing record, lingered completed included, is never emitted: the session parks that dispatch for the operator, names the record's id in its turn output, and continues with any work that needs no delete, since a foreign record's presence in a listing is never by itself a stand-down. A null recorded id has no deletable record: the ladder's null-id sole-span-match fallback delete is retired and its cap-refused create parks for the operator. The allowlist never removes the own-record deletes the ladder already orders: the state-recorded carrier id and the session's own spawner record, whatever its form, stay the delete-first targets. Bind at create: a successful create's returned id is written into the state file (the entry's automation_id, or parent_automation_id for the carrier) before the next automation call, so the allowlist holds its key the moment the record exists. Witness: the 2026-10-16 incident deleted two peer-lineage lingered spawner records that recognition matching could not discriminate (state file notes 2026-10-16T15:52)."

Insertion B (agents/skills/maintenance/zcode.md, Dispatch ladder automation-born step, after the armed-child-record-conflict sentence):

"The protection class widens beside that stand-down: a non-recurring record whose lifecycle is completed or whose enabled flag is false passes the same test, because the ownership allowlist is the test and recognition matching is repo-scoped and cannot discriminate lineages, so a lingered record of another lineage is untouchable exactly as a live one and the delete-first ordering skips it, parking for the operator; a completed or disabled record that is the session's own state-recorded id stays deletable per the allowlist."

Insertion C (agents/skills/maintenance/duties-core.md, FIRST ACTION step (3), appended to the sentence ending "deleting your own lingered completed spawner record first when the create is refused for the automation-born cap"):

", and the record deleted first must be an id this session's own state file records as its spawner, never any other lingered record in the listing (the overlay's ownership allowlist applies to this duty unchanged: a foreign lingered record is untouchable, and a cap that no own-record delete can lift parks per step (4))"

Insertion D (agents/skills/maintenance/SKILL.md, Step 0 turn-start carrier re-arm duty, as a new sentence after the sentence ending "the check's listing-derived bookkeeping edits and its child-duty exemption are unchanged)."):

"The overlay's ownership allowlist governs every automation delete here too: the recorded delete targets only the session's own state-recorded id, a foreign lingered record is untouchable and parks for the operator, and the duty's null-id path has no deletion at all."

Insertion H (agents/skills/maintenance/zcode.md, Dispatch ladder automation-born step, replacing the parenthetical "(fall back to the listing's sole span-match automation when the id is null)"):

"(a null recorded id has no deletable record per the ownership allowlist: park that dispatch for the operator, never a span-matched fallback delete)"

Insertion H2 (agents/skills/maintenance/zcode.md, the same step's case-3 confirm-listing sentence, replacing the parenthetical "(the Otherwise arm below falls back to its sole span-match automation when the id is null)"):

"(the Otherwise arm below parks that dispatch for the operator per the ownership allowlist when the id is null)"

### Task 2: post-delete probe and distinct-failure rollback

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/duties-core.md`

- [x] Insert the probe and distinct-failure rule set into the overlay's Dispatch ladder automation-born step, immediately after the sentence ending "retry the rollback create up to twice." (before the ambiguous-outcome carve-out), using insertion E below. [class: IMPLEMENTATION_REQUIRED]
- [x] Amend the rollback sentence in the same edit: replace "retry the rollback create up to twice." with the supersession clause below, so the old identical-retry budget yields to the distinct-failure rollback rule. [class: IMPLEMENTATION_REQUIRED]
- [x] Reconcile the probe with the emission-shape rules: apply insertion I below at its two named spans (the dispatch-discipline exception enumeration and the step-2 two-mutating-calls parenthetical). [class: IMPLEMENTATION_REQUIRED]
- [x] Mirror the probe and the mechanism-switch park in the child-side FIRST ACTION copy: append insertion F below to the duties-core.md step (3) precheck sentence ending "on absence route to the escalation in (4), whose park path carries the decided re-arm, without burning listings on statically absent primitives". [class: IMPLEMENTATION_REQUIRED]
- [x] Run the arm-2 span pins from Validation Commands and confirm each flips GREEN. [class: REPOSITORY_TEST]

Prescribed insertions (exact text):

Insertion E (agents/skills/maintenance/zcode.md, Dispatch ladder automation-born step, after the rollback-retry sentence):

"Post-delete probe: after any automation delete on this ladder, one read-only listing precedes the first create, and the create's decision reads that listing (the deleted record's absence verified against its id, never assumed); the probe is a listing-as-decision-input step and inherits the truncation arm: never read absence from a truncated listing and never re-poll against the same cap; record cannot-decide in the rearm_note field (the 2026-10-08 confirming-listing truncation row is the witness). Distinct-failure rollback: a retry after a failed create must change mechanism rather than repeat the emission; the first refusal naming a fabricated or unknown id, and any second consecutive identical failure, parks the loop with the intent recorded (pending_rearm plus its paired payload copy) instead of a third emission, and the sanctioned mechanism switch is the launchd clocked-order chain (scripts/execute_plan_runtime.py --operation clocked-order-schedule), which is unbound and deletion-tolerant (the harmed lineage's same-day mid-mandate continuation through its launchd carrier, landing 7b0f48390, is the witness; the 2026-10-16 incident's five identical emissions on fabricated ids are this rule's witness, and the first-try create after the session continuation shows the misroute is episodic, which is what keeps the park bounded)."

Rollback-sentence supersession (agents/skills/maintenance/zcode.md, same step, replacing the sentence "retry the rollback create up to twice."):

"retry the rollback create up to twice, never re-issuing a failed call twice consecutively: the distinct-failure rollback rule supersedes the identical-retry budget when a failure repeats."

Insertion I (agents/skills/maintenance/zcode.md, two reconciliation spans):

Span 1, in "Dispatch discipline and loop stand-down", replacing "the pending-rearm armed verification), which precedes the mutations without being the loop signature":

"the pending-rearm armed verification, and the post-delete probe listing), which precedes or intervenes between the mutations without being the loop signature"

Span 2, in the Dispatch ladder automation-born step, replacing "(two mutating calls, the shortest surface the action-selection loop can be given;":

"(two mutating calls plus the mandated post-delete probe listing between them, the shortest surface the action-selection loop can be given;"

Insertion F (agents/skills/maintenance/duties-core.md, FIRST ACTION step (3), appended to the precheck sentence ending "on absence route to the escalation in (4), whose park path carries the decided re-arm, without burning listings on statically absent primitives"):

"; after any delete this duty performs, one read-only listing probe precedes the create (the overlay's post-delete probe rule; never read absence from a truncated listing), and a repeated identical create failure parks per step (4) with the mechanism switch to the launchd clocked-order chain rather than a third identical emission"

### Task 3: launchd default-in-waiting and the rung demotion

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `agents/skills/maintenance/zcode.md`

- [x] Insert the demotion and promotion-review paragraph at the head of the Dispatch ladder's automation-born step, immediately after the step's own opening parenthetical that ends "the recycling update call is demoted to the optimization leg closing this step):", using insertion G below; the paragraph names the retired rung class and the review the activation waits behind. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the arm-3 span pins and the retired-rung naming pin from Validation Commands and confirm each flips GREEN. [class: REPOSITORY_TEST]

Prescribed insertions (exact text):

Insertion G (agents/skills/maintenance/zcode.md, Dispatch ladder automation-born step, at the head of the step body):

"Demoted fallback (arm 3): for a session already bound to an armed automation record, the priced default child dispatch is the launchd clocked-order chain (scripts/execute_plan_runtime.py --operation clocked-order-schedule): the chain is unbound, so the automation-born cap never applies to it and no delete is ever needed to lift one, and a deleted spawner record does not stop a launchd fire (the harmed lineage's same-day mid-mandate continuation through its launchd carrier, landing 7b0f48390, is the deletion-tolerance witness). The unconditional mid-session delete-plus-create path stops being the default child dispatch for sessions already bound to an armed record: it becomes a documented fallback firing only behind both guard rule sets of this change (the ownership allowlist and the post-delete probe with the distinct-failure rollback), and the launchd chain takes over as the operative default for bound sessions only when the promotion review records that activation after the clocked-order discharge-verification gap row (docs/history/backlog/2026-10-10-clocked-order-discharge-no-payload-session.md, the instant-death class a launchd default raises the stakes on) is dispositioned, so an open gap leaves the guarded fallback as the operative path. CronCreate stays the path for fresh chats, which are never bound and never capped, and for the standing loop carrier itself; the recycling-optimization leg keeps its existing demoted, flip-gated status. The promotion review and the guard rules' cost review are separate decisions (the dispatch default, then the guards' witnessed park costs), so neither stands in for the other."

### Task 4: register the companion pin rows

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/check_maintenance_pins.sh`

- [x] Register one pin row per insertion span (the Validation Commands span literals for arms 1 through 3) in scripts/check_maintenance_pins.sh, each a `pin "<name>"` row grepping its literal count-exactly against the owning file variable. [class: IMPLEMENTATION_REQUIRED]
- [x] Give each new row a provenance comment naming this plan (docs/history/plans/2026-10-17-rearm-dispatch-ladder-incident-guards.md), and place the rows per the script's placement guidance (the baseline is green, so any placement before the earliest fail checkpoint executes). [class: IMPLEMENTATION_REQUIRED]
- [x] Run the pins suite (`scripts/check_maintenance_pins.sh`) and confirm exit 0 with no new breach line. [class: REPOSITORY_TEST]
