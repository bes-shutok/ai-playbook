# Plan: backlog Origin class provenance and the periodic deferred-corpus re-triage lane

Backlog origins (scope of record):
- `docs/history/backlog/2026-09-26-backlog-origin-class-provenance-line.md`
- `docs/history/backlog/2026-09-26-maintenance-deferred-corpus-retriage-lane.md`

Backlog origin context (updated 2026-09-27, r6 re-cert): a third 2026-09-26 item, `docs/history/backlog/2026-09-26-plans-plain-outcome-summary.md` (fold-then-deleted at P65 execution), belongs to the same capture-time-classifiability family but is deliberately NOT an origin of this plan: it was the certified scope of the P65 plan `docs/history/plans/completed/2026-09-26-p65-plans-corpus-history-home-and-outcome-template.md` (executed and archived 2026-09-26, squash b3971208; its Task 1 added the required `## Outcome` section to the plans template). This plan implements no Outcome-template work and touches no plans-skill or review-plan bytes, so the family landed without a double implementation; the Outcome extension is already live, so no sequencing dependency remains.

Plan review: docs/reviews/2026-09-26-plan-review-origin-class-provenance-and-deferred-retriage-lane-r1.md (r1, ready=no, all 19 staged findings folded) · docs/reviews/2026-09-26-plan-review-origin-class-provenance-and-deferred-retriage-lane-r2.md (r2, ready=no, all 14 staged findings folded) · docs/reviews/2026-09-26-plan-review-origin-class-provenance-and-deferred-retriage-lane-r3.md (r3, ready=no, all 15 staged and 4 overflow findings folded) · docs/reviews/2026-09-26-plan-review-origin-class-provenance-and-deferred-retriage-lane-r4.md (r4, ready=no, all 18 staged and 5 overflow findings folded) · docs/reviews/2026-09-26-plan-review-origin-class-provenance-and-deferred-retriage-lane-r5.md (r5, ready=no, final cap round; all 10 staged and 4 overflow findings folded, 2 medium findings recorded as residuals below) · review cap reached, residuals recorded per the task directive · docs/reviews/2026-09-26-plan-review-origin-class-provenance-and-deferred-retriage-lane-r6.md (r6, verification-only re-cert 2026-09-27: two-worker panel verified the r5 residual dispositions and byte identity with the authoring commit; 5 blocking findings all P65-migration stale-path folds, folded same round; ready=yes over the final bytes)

Driving force: efficiency (secondary: token-usage)
Force note: both origins trade a one-time capture-time or lane-machinery cost for a recurring per-triage saving: provenance recorded at capture replaces re-reading every deferred item body to classify it (the witnessed 2026-09-26 triage read all 91 deferred bodies), and the periodic lane replaces ad-hoc hand-run sweeps of the deferred corpora. The token-usage secondary names the same saving expressed in corpus reads. Both forces are driving principles, so no non-principle justification is required; park-triage would take the plan anyway because both items are class=real owner directives with a witnessed cost, and neither is formal-hardening.

## Outcome

Record where every backlog item came from at the moment it is captured, and let the maintenance loop re-triage the deferred corpora on a cadence instead of by hand, so classifying the queue stops meaning re-reading the whole corpus.

- Every newly captured backlog item carries an `Origin class:` line, so equal-priority ordering (consumer project feedback before skills-repo self-improvements) is readable without opening item bodies.
- The maintenance survey stamps each item's origin class beside its class token, and authoring selection orders consumer-feedback items before self-serving items within a priority group.
- The deferred corpora get a recurring re-triage lane in the maintenance loop that mirrors the friction-audit lane: due-read from its state record, one capped child on the authoring lane, the rubric read from the deferred README's standing rule, and the ordered gate chain before every sweep commit.
- No existing backlog item is retro-edited: the corpus gains `Origin class:` lines only through new captures and natural touches.

## Terms

- **Origin class**: the provenance value a captured backlog item declares in its `Origin class:` header line: `self-serving`, `consumer-feedback (company)`, or `consumer-feedback (pet)`.
- **Origin token**: the survey's decision_reason token `<backlog-item-basename>:origin=<self-serving|consumer-company|consumer-pet|unknown>`, recorded beside the existing class token.
- **Re-triage lane**: the maintenance loop lane that periodically re-runs the 2026-09-26 direction triage over the deferred corpora under the friction-audit lane's mechanics.
- **Re-triage record**: the lane's state file `retriage-state.json`, beside the audit `state.json` under the resolved `friction_audit_dir`, carrying `next_due`, a corpus digest, the dispatch caps, the durable `awaiting_authorization` hold with its `authorized_section_digest`, the in-flight sweep's move list, and the last sweep's counts.
- **Rubric SOT**: the "2026-09-26 direction triage (standing rule)" section of `docs/history/plans/deferred/README.md`; the lane pins the pointer and never copies the classes into the skill.
- **Done-record stray**: a deferred-corpus copy whose document-registry row or completed twin records done; the sweep removes it and appends a note to the authoritative row.

## Assumptions

- assume the plans-template Outcome extension (family member `2026-09-26-plans-plain-outcome-summary.md`, fold-then-deleted at P65 execution) is implemented by the P65 plan (executed and archived 2026-09-26, squash b3971208), not here; basis: P65's header origin list names that item, P65's own header Plan review line records its r5 review as ready=yes (final round), and the repo's no-double-coverage discipline forbids re-authoring a plan's certified scope; confirmed by the standing pre-authorization (accept all recommended options, task directive 2026-09-26).
- assume the non-capture surfaces need no edit (execute-plan off-plan capture, review-loop, review-reconciliation all route valid unfixed findings through receiving-review's capture rules); basis: authoring-time grep 2026-09-26: execute-plan SKILL.md lines 188, 656, 834, 842; review-loop SKILL.md lines 143, 168, 198; review-reconciliation SKILL.md "With receiving-review" section (lines 135-137, "Use the existing triage and backlog rules for valid findings that are deferred"); no capture vocabulary restated in any of the three.
- assume the claimed checker runs over every candidate in one invocation, keeping the second origin's wording; basis: the script declares `--slug` with `action="append"` and a "Repeatable `--slug`" docstring (source read 2026-09-26, after the r1 workers measured the interface against the orchestrator's misread single-slug probe), and the maintenance bulk disposition sweep gate prescribes the same one-invocation shape; a claimed verdict is skip-and-annotate and aborts the sweep's remaining moves per that gate's exit-1 semantics.
- assume the claimed-check-to-move residual race is accepted; basis: the window between the one-invocation check and a candidate's move is minutes-to-hours per roughly-30-day sweep, and the recovery is cheap: the next sweep re-runs the checker over the moved candidates (it accepts paths under `rejected/`) and restores a mismatch with a registry note; confirmed by the standing pre-authorization.
- assume the re-triage record is named `retriage-state.json` beside the audit `state.json` under the resolved `friction_audit_dir`; basis: the origin's "beside the friction-audit record" placement plus the audit state's own naming; confirmed by the standing pre-authorization.
- assume the corpus digest is sha256 over one `<file-sha256>  <repo-relative-path>` line per deferred entry (top-level `.md` files of `docs/history/plans/deferred/` and of the resolved backlog deferred directory, README files excluded), with lines sorted by path; basis: the origin requires "a corpus digest" without a formula and this is the cheapest drift witness between sweeps; confirmed by the standing pre-authorization.
- assume "small corpus" for the in-turn sweep allowance means at most 10 deferred entries across both corpora (README files excluded); above that the lane dispatches the capped child; confirmed by the standing pre-authorization.
- assume `pending_dispatch`'s `kind` enum gains `retriage` (additive under schema 4, no version bump, the same additivity with which the audit kind joined, including the sibling surfaces the audit kind's landing and the P54 fleet-cap rework had to edit per the file's own Revisions ledger and inline dated annotations: the `children[]` entry example, the `pending_dispatch` shape and the sanctioned-writer enumeration's scheduler-turn class mode list, the widened-arm lane classification, the state-file arm's completion evidence, the failure cap's progress definitions, the G1a exclusivity sentence, the Invariants scheduling and fleet-kinds bullets, the fleet-cap enumerations, the Step 6 carry-forward clause, the pins-suite literals, and this plan's Revisions-ledger entry); basis: the State file field paragraph and the audit-kind precedent; confirmed by the standing pre-authorization.
- assume the deferred README's standing-rule section is the live standing owner directive at authoring time (verified on disk 2026-09-26: the "2026-09-26 direction triage (standing rule)" section of `docs/history/plans/deferred/README.md`, which already anticipates this lane), so unattended rejection acts under it, while the without-directive fallback (proposal report plus `awaiting-authorization`) stays in the skill for the day the section changes, and the child re-checks the section's liveness against the recorded authorized-section digest immediately before each sweep commit.
- assume the origin token's base-name placeholder follows the sibling class token's `<backlog-item-basename>` shape and its value vocabulary comes from the first origin (fix direction 3; notation only, the value set and semantics are unchanged); basis: the two tokens sit beside each other in one survey sentence, the repo's naming-consistency convention, and the first origin's token wording; confirmed by the standing pre-authorization.

- residual (review cap, unfolded, r5 overflow): the sweep critical section has no checkout-dirt discrimination, so a peer's uncommitted edit to a moved candidate can ride the sweep commit and crash reconciliation could misclassify peer staged edits; mitigation recorded instead of a fold: the merge-lock hold, the 20-candidate bound, the single-owner repo, and git recoverability (r5 risk finding, recorded per the task directive's cap-finalize rule).
- residual (review cap, unfolded, r5 overflow): an aborted sweep's record write evidences progress, so persistently gate-failed sweeps accrue no failure credit; mitigation recorded instead of a fold: the one-day retry bounds the churn, the failing gate is named in `decision_reason` each turn, and the corpus-digest drift witness records every non-moving sweep (r5 risk finding, recorded per the cap-finalize rule).

Decision points requiring a grill: item-3 disposition (covered by the executed P65 plan, no Outcome-template task in this plan) - resolved by standing pre-authorization accepting the recommended no-double-coverage option, task directive 2026-09-26; affects Backlog origin context and Review Scope; re-triage record name and corpus digest formula - resolved by standing pre-authorization, task directive 2026-09-26; affects Terms and Task 4; dispatch kind-enum extension (the retriage kind joins the execute, author, audit set in the dispatch field paragraph) - resolved by standing pre-authorization, task directive 2026-09-26; affects Task 4; small-corpus threshold for the in-turn sweep - resolved by standing pre-authorization, task directive 2026-09-26; affects Task 4; authorization-abort retry cadence (the record's next_due advances by one day on an authorization-aborted sweep, a short retry instead of the full cadence) - resolved by standing pre-authorization, task directive 2026-09-26; affects Task 4 Authorization sub-bullet; co-due lane precedence (the audit consult is served first regardless of cadence values) - resolved by standing pre-authorization, task directive 2026-09-26; affects Task 4 contention clause; origin=unknown rank (sorts between the consumer-feedback items and self-serving items, so a malformed consumer value is never demoted below self-serving) and company-before-pet family tiebreak (deterministic; the profile schema defines no ordering key) - resolved by standing pre-authorization, task directive 2026-09-26; affects Task 3; retriage state-writer sanction (the scheduler-turn class gains the re-triage park, dispatch append, and in-turn entry modes, no new writer class) - resolved by standing pre-authorization, task directive 2026-09-26; affects Task 4 State file items; retriage blueprint shape (a pointer stub riding the audit child's payload arrangement, carrying none of the counted dispatch-slice spans) - resolved by standing pre-authorization, task directive 2026-09-26; affects Task 4 prompt-templates item

## Gist & Examples

TLDR: backlog capture and the maintenance loop record each item's origin class and re-triage the deferred corpora on a cadence, so classifying the queue stops meaning re-reading every deferred body.

What changes, in two moves. First, capture-time provenance: receiving-review's Backlog capture required-content list gains an `Origin class:` bullet with exactly three closed-set values and the equal-priority ordering semantics (consumer-feedback outranks self-serving) stated next to the existing `Consumer urgency:` rule; the two lines compose, neither replaces the other. learn Step 1.8 already follows receiving-review's item shape by reference, so its reference extends; maintenance's Step 7 measurement-rider filing bullet and the friction-audit lane's new-item duty gain their first receiving-review references in this plan; the vocabulary is never restated. The maintenance survey then records the class in its decision_reason origin token beside the existing class token, and D2 authoring selection orders consumer-feedback items before self-serving items within the same priority group. Second, the periodic lane: maintenance gains a deferred-corpus re-triage consult mirroring the friction-audit consult (a `next_due` read from `retriage-state.json`, at most one capped child occupying the authoring lane, an in-turn sweep when the corpus is small), reading its rubric from the deferred README's standing-rule section, moving rejects into the rejected archives under the five ordered gates, and advancing `next_due` like the audit lane.

Example: the 2026-09-26 hand-run triage had to read all 91 deferred bodies before it could order anything, and the promotion pass recorded the classification only in remarks on promoted items; after Task 3 the survey's decision_reason carries `<backlog-item-basename>:class=real` beside `<backlog-item-basename>:origin=consumer-company` for an item that declares its provenance, with no body reading. Example: today the deferred corpora regrow stale entries silently until someone re-runs the triage by hand; after Task 4 the lane re-runs it on its cadence under the README's standing rule, with the claimed checker, the registry validator, the check-writes gate, the origins gate, and the em-dash scan gating every sweep commit in that order.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: every prescribed insertion lands at its named anchor or named section (the load-bearing anchors carry adjacency witnesses), and the post-execution Validation battery exits `VALIDATION OK` from the repository root (G1-G4 green, G5 checked and green, G6 and G7 clean).
- Single-sourcing: the canonical `Origin class:` value literals appear only in `agents/skills/receiving-review/SKILL.md` among the touched skills (the G2 negative gates), and the lane text pins the rubric pointer without restating a reject or keep class.
- Mechanism reuse: the re-triage lane reuses the audit lane's consult shape, caps, lane occupancy, guard enumerations, sanctioned-writer modes, failure-cap arms, and pending-dispatch arbitration, and its whole sweep critical section serializes under the merge landing lock; no second parallel mechanism is introduced (the second origin's own "no second parallel mechanism" heading is the review lens).
- Scope safety: no existing backlog item is edited and no non-capture surface is touched (the G5 execution checks against the recorded base, including the rubric SOT and both rejected archives; the final battery run requires a checked G5, not a skipped one).

**Done when:**
- `bash -n` over the Validation Commands block passes and the block exits `VALIDATION OK` after Task 4 with `PLAN_BASE` set (a G5-skipped run does not satisfy this gate).
- The pre-round readiness validator, the em-dash scan, and the public-hygiene scan exit clean over the plan bytes (authoring record in the Validation preamble).
- `python3 scripts/doc_registry_validator.py check-writes <edited skill files>` exits 0 over the edited skill files (re-probed 2026-09-26 over the five Task-edited paths: `agents/skills/receiving-review/SKILL.md agents/skills/learn/SKILL.md agents/skills/maintenance/SKILL.md agents/skills/maintenance/zcode.md agents/skills/maintenance/prompt-templates.md`; receipt: "check-writes: 0 unprotected immutable write(s) of 5 path(s), 0 registry audit-note defect(s)").

**Ship when:**
- No external release conditions: every check is repository-verifiable; no deploy, cross-team, or human-owned gate applies to this documentation-only change.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/receiving-review/SKILL.md` (edit; the "Required content per item" list and one sentence in the existing "With `maintenance` skill" Integration Points entry only; all other sections are frozen, reject findings that touch them)
- `agents/skills/learn/SKILL.md` (edit; the Step 1.8 item-shape sentence only; frozen elsewhere)
- `agents/skills/maintenance/SKILL.md` (edit; the Configuration table rows including the `friction_audit_dir` purpose cell, the Step 1 survey and the Step 1 audit consult's dedupe-and-fold clause and the re-triage consult block, the Step 1 pending-dispatch bullet, the Step 2 widened-arm lane-classification sentence, the state-file arm's completion-evidence enumeration, the fleet-cap guard bullet, the failure cap's progress-definitions bullets, the Step 3 D2 selection and the re-triage same-turn contention clause, the G1a exclusivity sentence and the Invariants scheduling and fleet-kinds bullets, the Step 7 weekly measurement rider's filing bullet, the State file `pending_dispatch` field paragraph, `children[]` entry example, sanctioned-writer enumeration's scheduler-turn class mode list, and the Step 6 carry-forward clause, and the Revisions section (this plan's entry only); frozen elsewhere)
- `agents/skills/maintenance/zcode.md` (edit; the child-recognition clause list and the fleet-cap member enumeration only; frozen elsewhere)
- `agents/skills/maintenance/prompt-templates.md` (edit; the re-triage child pointer-stub section only)
- `scripts/check_maintenance_pins.sh` (edit; pin literals and citation comments only, this plan's companion pins)

**Tests:**
- none; the change is documentation-only and verified by the Validation battery's gate greps (the `[class: REPOSITORY_TEST]` items run gates and dry runs, not test files)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/history/plans/deferred/README.md`; reason: the rubric SOT must stay untouched so the lane's pointer reads the owner's standing rule, never the skill's copy
- top-level items under `docs/history/backlog/`; reason: the first origin's no-bulk-retrofit acceptance block
- `agents/skills/plans/SKILL.md`, `agents/skills/review-plan/SKILL.md`; reason: the Outcome-template family member is the executed P65 plan's certified scope
- `agents/skills/execute-plan/**`, `agents/skills/review-loop/**`, `agents/skills/review-reconciliation/**`; reason: capture routing verified at authoring, no edit (first origin, fix direction 4)
- `scripts/**` except `scripts/check_maintenance_pins.sh`; reason: the lane reuses the existing gate scripts; the pins script is in scope for pin literals only

## Validation Commands

Run from the repository root. Post-execution form: G1 flips green by Task 1, G2 by Task 2, G3 by Task 3, G4 by Task 4, and G7 (the maintenance pins suite) passes at authoring and guards the existing pins through execution; interim per-task runs execute only that task's letter block (the later blocks' pins are not yet inserted and must stay RED). G5 is the execution-time scope check and reads the base sha from `PLAN_BASE`: record as `PLAN_BASE` the last commit whose tree does not contain this plan's landing (verify before recording that `git grep -q 'Deferred-corpus re-triage consult' "$PLAN_BASE" -- agents/skills/maintenance/SKILL.md` FAILS; a base whose tree already carries the landing hollows out G5 and G6); without `PLAN_BASE` the block logs its skip and the remaining gates still run, but only a checked G5 run satisfies the Done-when. G6 gates only the lines this plan adds (`added-lines` against the base), because the two maintenance files carry pre-existing committed em-dashes outside this plan's anchors that a whole-file scan would trip on. Authoring record 2026-09-26: the battery was executed against the unedited tree before round 1 and re-executed after the r1, r2, r3, and r4 folds with the same result (the FIRST failing gate is G1's `Origin class: self-serving` pin, exit 1; the G2 negative gates pass vacuously at authoring since the vocabulary is not yet restated anywhere, so absence proves nothing until Task 2 lands; G5 logs its skip without `PLAN_BASE`; the added-lines em-dash scan exits 0 over the authoring diff; G7 passes over the unedited tree; a stray r3-worker simulation commit found at HEAD was dropped by mixed reset before r4 so the branch sits at its d5f63977 base). The pre-round readiness validator, the em-dash `file` scan, and the public-hygiene scan over these plan bytes exit clean before each round (recorded in the review staging docs).

```bash
set -u
fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }
expect_no_match() { pattern="$1"; shift; grep -qF "$pattern" "$@"; rc=$?; if [ "$rc" -eq 0 ]; then fail "forbidden literal present: $pattern"; elif [ "$rc" -ne 1 ]; then fail "grep rc=$rc for $pattern"; fi; }
RR=agents/skills/receiving-review/SKILL.md
MS=agents/skills/maintenance/SKILL.md
REGION=$(awk '/Deferred-corpus re-triage consult/,/^### Step 2: guards/' "$MS")

# G1: receiving-review carries the Origin class SOT (Task 1)
awk '/^Required content per item/,/^Capture sources:/' "$RR" | grep -qF 'Origin class: self-serving' || fail "G1 self-serving value"
awk '/^Required content per item/,/^Capture sources:/' "$RR" | grep -qF 'Origin class: consumer-feedback (company)' || fail "G1 company value"
awk '/^Required content per item/,/^Capture sources:/' "$RR" | grep -qF 'Origin class: consumer-feedback (pet)' || fail "G1 pet value"
awk '/^Required content per item/,/^Capture sources:/' "$RR" | grep -qF 'consumer-feedback outranks self-serving' || fail "G1 ordering semantics"
awk '/^Required content per item/,/^Capture sources:/' "$RR" | grep -qF 'neither replaces the other' || fail "G1 composition clause"

# G2: consumers extend by reference; the canonical value literals stay single-sourced (Task 2)
grep -qF 'for item shape, including its `Origin class:` provenance line' agents/skills/learn/SKILL.md || fail "G2 learn reference"
awk '/^- On success: append the digest/,/^- Fail open:/' "$MS" | grep -qF 'with its `Origin class:` line set per receiving-review' || fail "G2 rider filing reference"
grep -qF "composed per receiving-review's Backlog capture required content" "$MS" || fail "G2 audit new-item reference"
grep -qF 'The Step 7 measurement-rider filing and the Step 1 audit consult' "$RR" || fail "G2 integration points entry"
# the `Origin class:` prefix is load-bearing: the bare word legitimately appears in the prescribed filing texts
expect_no_match 'Origin class: self-serving' agents/skills/learn/SKILL.md "$MS" agents/skills/maintenance/zcode.md agents/skills/maintenance/prompt-templates.md
expect_no_match 'consumer-feedback (company)' agents/skills/learn/SKILL.md "$MS" agents/skills/maintenance/zcode.md agents/skills/maintenance/prompt-templates.md
expect_no_match 'consumer-feedback (pet)' agents/skills/learn/SKILL.md "$MS" agents/skills/maintenance/zcode.md agents/skills/maintenance/prompt-templates.md

# G3: survey origin token and consumer-first selection (Task 3)
grep -qF '<backlog-item-basename>:origin=<self-serving|consumer-company|consumer-pet|unknown>' "$MS" || fail "G3 origin token shape"
grep -qF 'judged from the item body at survey time' "$MS" || fail "G3 unknown-from-body rule"
grep -qF 'orders consumer-feedback items before self-serving items within the same priority group' "$MS" || fail "G3 selection ordering"
grep -qF 'sorts between the consumer-feedback items and self-serving items' "$MS" || fail "G3 unknown rank"
grep -qF 'company items precede pet items' "$MS" || fail "G3 family tiebreak"
grep -qF 'outside the closed set' "$MS" || fail "G3 invalid-value mapping"
# adjacency: the ordering sentence lives inside the D2 bullet, not anywhere in the file
awk '/D2 .author./{f=1} f && /orders consumer-feedback items before self-serving/{print; exit}' "$MS" | grep -q . || fail "G3 D2 anchor adjacency"

# G4: the periodic deferred-corpus re-triage lane (Task 4)
grep -qF 'deferred_retriage_cadence_days' "$MS" || fail "G4 cadence key"
grep -qE 'deferred_retriage_cadence_days.+\| 30 \|$' "$MS" || fail "G4 fallback 30 table row"
test "$(grep -cE '^\| .deferred_retriage_cadence_days' "$MS")" -eq 1 || fail "G4 cadence row singleton"
printf '%s' "$REGION" | grep -qF 'Deferred-corpus re-triage consult' || fail "G4 consult bullet"
printf '%s' "$REGION" | grep -qF 'retriage-state.json' || fail "G4 state record"
printf '%s' "$REGION" | grep -qE 'Rubric SOT:.*docs/history/plans/deferred/README\.md' || fail "G4 rubric pointer"
printf '%s' "$REGION" | grep -qF 'never a copy' || fail "G4 pointer-not-copy rule"
printf '%s' "$REGION" | grep -qF 'git mv' || fail "G4 sweep move"
printf '%s' "$REGION" | grep -qF 'awaiting-authorization' || fail "G4 authorization fallback"
printf '%s' "$REGION" | grep -qF 're-reads the standing-rule section immediately before the sweep commit' || fail "G4 authorization re-read"
printf '%s' "$REGION" | grep -qF 'not re-judged before the next due date' || fail "G4 kept-items no-churn"
printf '%s' "$REGION" | grep -qF 'temp file plus atomic replace' || fail "G4 record write discipline"
printf '%s' "$REGION" | grep -qF 'records a corruption annotation' || fail "G4 corrupt-record handling"
printf '%s' "$REGION" | grep -qF 'sweep-time drift witness' || fail "G4 digest consumer"
printf '%s' "$REGION" | grep -qF 'at most 10 deferred entries' || fail "G4 small-corpus threshold"
printf '%s' "$REGION" | grep -qF '<file-sha256>  <repo-relative-path>' || fail "G4 digest formula"
printf '%s' "$REGION" | grep -qF 're-triage child occupies the authoring lane' || fail "G4 lane occupancy"
printf '%s' "$REGION" | grep -qF 'merge-wait-acquire --label deferred-retriage-sweep' || fail "G4 sweep commit lock"
printf '%s' "$REGION" | grep -qF 'holds it across the moves, the gate chain, and the commit' || fail "G4 critical-section lock"
printf '%s' "$REGION" | grep -qF 'at most 20 candidates per invocation' || fail "G4 sweep size bound"
printf '%s' "$REGION" | grep -qF 'reverses the already-executed dispositions' || fail "G4 gate-failure reversal"
printf '%s' "$REGION" | grep -qF 'prior `Status:` header line' || fail "G4 move-list restoration scope"
printf '%s' "$REGION" | grep -qF 'never aborts' || fail "G4 origins advisory carve-out"
printf '%s' "$REGION" | grep -qF 'every sweep outcome writes the record' || fail "G4 non-moving record semantics"
printf '%s' "$REGION" | grep -qF 'awaiting_authorization' || fail "G4 durable authorization hold"
printf '%s' "$REGION" | grep -qF 'authorized_section_digest' || fail "G4 authorized-section digest"
printf '%s' "$REGION" | grep -qF 'advances by one day on an authorization-aborted sweep' || fail "G4 abort retry cadence"
printf '%s' "$REGION" | grep -qF 'retriage-proposal-' || fail "G4 proposal report home"
printf '%s' "$REGION" | grep -qF 'names the reject class from the standing-rule section' || fail "G4 verdict class citation"
printf '%s' "$REGION" | grep -qF 'a large cadence value suspends the lane' || fail "G4 disable idiom"
grep -qF 'plus the re-triage record' "$MS" || fail "G4 purpose cell"
grep -qF 'a re-triage marker occupies only `G1a`' "$MS" || fail "G4 widened-arm classification"
grep -qF 'for a re-triage child, the re-triage record' "$MS" || fail "G4 completion-evidence class"
grep -qF 'Progress for a re-triage child means' "$MS" || fail "G4 failure-cap progress arm"
grep -qF 'never runs alongside an authoring child, another re-triage child' "$MS" || fail "G4 G1a exclusivity sentence"
grep -qF 'one re-triage child per cadence period' "$MS" || fail "G4 invariants scheduling carve-out"
grep -qF 'execution, authoring, audit, re-triage' "$MS" || fail "G4 invariants fleet kinds"
grep -qF 'the authoring, audit, and re-triage kinds' "$MS" || fail "G4 step-2 fleet-cap enumeration"
grep -qF 'the retriage-kind pending-dispatch park write' "$MS" || fail "G4 sanctioned park mode"
grep -qF "the retriage-kind park and the in-turn lane-hold entry" "$MS" || fail "G4 carry-forward clause"
grep -qF 'retriage-lane-due' scripts/check_maintenance_pins.sh || fail "G4 companion pins registered"
test "$(grep -cF 'like the authoring and audit kinds' "$MS")" -eq 1 || fail "G4 frozen ledger twin preserved"
grep -qF 'a retained execute, author, or retriage dispatch' "$MS" || fail "G4 park arbitration enumeration"
grep -qF 'the deferred-corpus re-triage lane joined' "$MS" || fail "G4 revisions ledger entry"
grep -qF 'for a retriage-kind target the validation is the re-triage consult re-read' "$MS" || fail "G4 retriage-kind validation"
grep -qF 'dispatches through the re-triage consult dispatch discipline' "$MS" || fail "G4 retriage-kind dispatch path"
test "$(grep -oF '"execute|author|audit|retriage"' "$MS" | wc -l)" -eq 2 || fail "G4 kind enum sites (field paragraph and children[] example)"
grep -qF 'authoring, audit, re-triage, and execution children' agents/skills/maintenance/zcode.md || fail "G4 fleet-cap enumeration"
grep -qF 'deferred re-triage lane' agents/skills/maintenance/zcode.md || fail "G4 child recognition"
grep -qF 'deferred re-triage lane' agents/skills/maintenance/prompt-templates.md || fail "G4 retriage blueprint"
# the consult block sits in Step 1 (the awk region includes its end anchor only when the block is placed before Step 2)
printf '%s' "$REGION" | grep -q '^### Step 2: guards' || fail "G4 consult placement"
# the five sweep gates appear inside the consult block in the prescribed order (wrapping-independent chain)
printf '%s' "$REGION" | tr '\n' ' ' | grep -qE 'check_backlog_claimed\.py.*doc_registry_validator\.py validate.*check-writes.*check_plan_origins_closed\.py.*added-lines em-dash scan' || fail "G4 gate order chain"
# no reject or keep class from the rubric SOT is restated in the skill (distinctive README class fragments)
expect_no_match 'adds gates, validators, or fail-closed checks' "$MS"
expect_no_match 'personal-fork protection' "$MS"

# G5: no-bulk-retrofit and routing-untouched (execution-time; PLAN_BASE from the execution log)
if [ -n "${PLAN_BASE:-}" ]; then
  git cat-file -e "${PLAN_BASE}^{commit}" 2>/dev/null || fail "G5 invalid PLAN_BASE"
  SCOPE_FILES=$({ git log --name-only --format= "$PLAN_BASE..HEAD"; git diff --name-only "$PLAN_BASE"; git diff --cached --name-only; git ls-files --others --exclude-standard; } | sort -u)
  if printf '%s\n' "$SCOPE_FILES" | grep -q '^docs/history/backlog/[^/]*\.md$'; then fail "G5 backlog item written or edited"; fi
  if printf '%s\n' "$SCOPE_FILES" | grep -qE 'agents/skills/(execute-plan|review-loop|review-reconciliation)/'; then fail "G5 non-capture surface edited"; fi
  if printf '%s\n' "$SCOPE_FILES" | grep -qE '^docs/history/plans/(deferred/README\.md|rejected/)|^docs/history/backlog/rejected/'; then fail "G5 rubric SOT or rejected archive touched"; fi
else
  echo "G5 SKIPPED: PLAN_BASE unset" >&2
fi
if git status --porcelain -- docs/history/plans/deferred docs/history/plans/rejected docs/history/backlog | grep -q .; then fail "G5 corpus dirt (dry-run or sweep leak)"; fi

# G6: em-dash over the lines this plan adds (the pre-existing committed em-dashes in the maintenance files are outside this plan's anchors)
bash scripts/check-no-em-dash.sh added-lines --base "${PLAN_BASE:-HEAD}" || fail "G6 em-dash scan"

# G7: the maintenance pins suite holds over the edited skill text (passes at authoring; guards the pins through execution)
bash scripts/check_maintenance_pins.sh || fail "G7 maintenance pins suite"
echo "VALIDATION OK"
```

### Task 1: Origin class line in receiving-review's Backlog capture SOT

Files:
- `agents/skills/receiving-review/SKILL.md`

- [x] In the "Required content per item" list, directly after the bullet beginning "When the item fixes shared skills used by other repos" (the `Consumer urgency:` rule), insert this exact bullet (indented code line; copy it verbatim, one line, no leading spaces in the target file) [class: IMPLEMENTATION_REQUIRED]

    - Origin class: exactly one provenance value on every newly captured item, from the closed set: `Origin class: self-serving` (the failure or improvement was witnessed on the skills repo's own runtime; no consumer project is involved), `Origin class: consumer-feedback (company)` (witnessed in a company project that consumes these skills), or `Origin class: consumer-feedback (pet)` (witnessed in the owner's personal pet projects that consume these skills). Ordering semantics, next to the Consumer urgency rule above: at equal priority, consumer-feedback outranks self-serving, and the company/pet tag names which project family's priority profile (guidelines rule 68) applies when a shared-skill fix trades one consumer family against the other. A consumer-feedback item that also meets the Consumer urgency conditions carries both lines; the two lines compose (provenance plus never-profile-deferred), neither replaces the other.

- [x] `OriginClassCapture#sot_region`; given the edited receiving-review SKILL.md, expects every G1 grep to pass (the three value literals, the ordering phrase, and the composition clause each found inside the Required-content-to-Capture-sources region) [class: REPOSITORY_TEST]
- [x] Capture dry run: route one sample review finding through the edited Backlog capture required-content list and record the produced `Origin class:` line and its value in the execution log; the dry run composes the required-content verdict only and writes no backlog item file anywhere under the backlog home (first origin acceptance clause 1) [class: REPOSITORY_TEST]
- [x] Run the G1 block → expect GREEN; G2-G4 stay RED (their pins are later tasks' insertions); G6 and G7 exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `skills: receiving-review requires an Origin class line on captured backlog items` [class: IMPLEMENTATION_REQUIRED]

### Task 2: extend the by-reference consumers (learn Step 1.8, the two maintenance surfaces, the provider entry)

Files:
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/learn/SKILL.md`
- `agents/skills/maintenance/SKILL.md`

- [x] In `agents/skills/learn/SKILL.md` Step 1.8, change the sentence beginning "Follow receiving-review's "Backlog capture for valid findings not fixed in scope" for item shape, and apply" so it reads "...for item shape, including its `Origin class:` provenance line, and apply"; no other learn edit [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/maintenance/SKILL.md` Step 7's filing bullet ("On success: append the digest..."), directly after "header fields (newest = the backlog item whose filename sorts last lexicographically)", insert ", with its `Origin class:` line set per receiving-review's capture rule (a measurement-rider filing is self-serving unless the measured cost was witnessed in a consumer project)"; the explicit value rule wins over the header-mimicry clause; no value literal is restated [class: IMPLEMENTATION_REQUIRED]
- [x] In the Step 1 audit consult bullet's dedupe-and-fold clause ("dedupe-and-fold: evidence on existing items becomes a dated evidence line, new items only after checking open plus completed plus deferred"), extend the clause to read "...new items only after checking open plus completed plus deferred, composed per receiving-review's Backlog capture required content with its `Origin class:` line set per that rule (an audit-lane filing is self-serving unless the witnessed defect was seen in a consumer project)" [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/receiving-review/SKILL.md`'s "With `maintenance` skill" Integration Points entry, append one sentence: "The Step 7 measurement-rider filing and the Step 1 audit consult's new-item duty follow **Backlog capture** required content, including the `Origin class:` line." [class: IMPLEMENTATION_REQUIRED]
- [x] `OriginClassCapture#by_reference_consumers`; given the edited files, expects the four G2 reference greps to pass (learn, the rider bullet, the audit new-item clause, the Integration Points entry) and all three `expect_no_match` sweeps over learn, maintenance SKILL.md, zcode.md, and prompt-templates.md to stay clean (the canonical value literals exist only in receiving-review) [class: REPOSITORY_TEST]
- [x] Run the G2 block → expect GREEN; G3-G4 stay RED; G1 stays GREEN [class: REPOSITORY_TEST]
- [x] Commit: `skills: learn and maintenance extend Origin class capture by reference` [class: IMPLEMENTATION_REQUIRED]

### Task 3: survey origin token and consumer-first selection ordering

Files:
- `agents/skills/maintenance/SKILL.md`

- [x] In the Step 1 survey's "Priority profile resolution" bullet, directly after the sentence ending "so a plan's origin list is auditable against the profile.", insert this exact sentence (indented code line; copy verbatim, one line, no leading spaces in the target file) [class: IMPLEMENTATION_REQUIRED]

    Beside the class token, record the item's origin class in the token form `<backlog-item-basename>:origin=<self-serving|consumer-company|consumer-pet|unknown>`, mapping the item's `Origin class:` header value to its token form (the self-serving value to self-serving, the company value to consumer-company, the pet value to consumer-pet); a present header line whose value is outside the closed set records `origin=unknown` with the non-enum value noted in the survey output, never normalized into the item; a missing header line is judged from the item body at survey time and the judged value is recorded in the token, never by editing the item, with `origin=unknown` when the body does not settle it.

- [x] In the Step 3 `D2 (author)` bullet, directly after "schedule an authoring child for the highest-priority plan-uncovered open backlog item.", insert this exact sentence (indented code line; copy verbatim, one line, no leading spaces in the target file) [class: IMPLEMENTATION_REQUIRED]

    Within the profile's priority groups, D2 also orders consumer-feedback items before self-serving items within the same priority group, reading the survey's origin token (an absent header line stays the survey-time body judgment); an `origin=unknown` item sorts between the consumer-feedback items and self-serving items within the group (a malformed consumer value is never demoted below self-serving), and between the two consumer families company items precede pet items.

- [x] `OriginClassSurvey#token_and_ordering`; given the edited SKILL.md, expects all six G3 greps and the D2 adjacency probe to pass (the token shape, the body-judgment rule, the ordering phrase inside the D2 bullet, the re-positioned unknown rank, the family tiebreak, and the invalid-value mapping) [class: REPOSITORY_TEST]
- [x] Run the G3 block → expect GREEN; G4 stays RED; G1-G2 stay GREEN [class: REPOSITORY_TEST]
- [x] Commit: `skills: maintenance survey records origin tokens and orders selection consumer-first` [class: IMPLEMENTATION_REQUIRED]

### Task 4: the periodic deferred-corpus re-triage lane in maintenance

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/prompt-templates.md`
- `scripts/check_maintenance_pins.sh`

- [x] In the Configuration table, directly after the `friction_audit_cadence_days` row, add this table row (indented code line; copy verbatim, one line, no leading spaces in the target file) [class: IMPLEMENTATION_REQUIRED]

    | `deferred_retriage_cadence_days` | Re-triage lane cadence consumed by the re-triage record's `next_due` write | 30 |

- [x] In the same table, append `, plus the re-triage record (`retriage-state.json`) for the deferred re-triage lane` to the `friction_audit_dir` row's purpose cell, keeping the existing parenthetical [class: IMPLEMENTATION_REQUIRED]
- [x] Directly after the Step 1 "Friction-audit consult" bullet, insert the consult bullet and its five sub-bullets with exactly the pin-bearing content below (full prose may be polished around the pins, but every pinned fragment stays verbatim and in order) [class: IMPLEMENTATION_REQUIRED]

Consult bullet pins, all present in one bullet: `Deferred-corpus re-triage consult`; `retriage-state.json` (the record beside the audit state under the resolved `friction_audit_dir`; a missing record is a cold start and reads due); `children[]` entry and claim check with park/retain on quota pressure under the same pending-dispatch arbitration as the audit consult; idle/off-peak preferred; the in-turn sweep allowed when the corpus is small (at most 10 deferred entries across both corpora, README files excluded) and the turn's guard pass left the authoring lane free with the done-lock and merge-lock reads clear (it runs after the Step 2 guards and the turn's dispatch leg, never before, and the contention clause below gives the in-turn variant the same slot and D3 resolution); hard caps of at most 2 sub-agents and a total token budget recorded in the re-triage record; the re-triage child occupies the authoring lane (`G1a`) and its kind, completion evidence, and progress witness mirror the audit child's state-file and failure-cap arms; the child prompt carries the literal `deferred re-triage lane` plus the repository root (the literal the zcode.md recognition clause matches; the prompt-templates.md retriage pointer stub owns the payload); the corpus digest definition (sha256 over one `<file-sha256>  <repo-relative-path>` line per deferred entry, top-level `.md` files of both deferred directories, README files excluded, sorted by path).

Sub-bullets:
- Rubric SOT: reads the "2026-09-26 direction triage (standing rule)" section of `docs/history/plans/deferred/README.md`; the skill pins the pointer, `never a copy`, and no reject or keep class is restated in the skill.
- Sweep mechanics: the sweep records a move-list entry per candidate (from-path, to-path, prior `Status:` header line) into the re-triage record, written before the first move and rewritten after each move so a mid-move death leaves the list on disk for the next sweep's reversal; rejects move with `git mv` into the `rejected/` directory under the resolved backlog home (fallback `docs/history/backlog/rejected/`), plans: the `rejected/` directory under the resolved plans home (fallback `docs/history/plans/rejected/`), plus exactly one header status-line rewrite (`Status: rejected (<date>; <reason>)`) whose reason names the reject class from the standing-rule section the item was rejected under, and document-registry rows with audit notes; a registry identity collision takes the MMDD suffix plus directory tag; a done-record stray is removed with a note appended to the authoritative row; the sweep moves at most 20 candidates per invocation, a larger corpus moves across consecutive sweeps each under its own lock hold and gate chain; the check-to-move residual race of the claimed gate is recovered by the next sweep re-running the checker over the moved candidates and restoring a mismatch with a registry note; the sweep (child or in-turn) acquires the merge landing lock with a bounded wait before its first move and holds it across the moves, the gate chain, and the commit (`bash scripts/done-lock.sh merge-wait-acquire --label deferred-retriage-sweep --max-wait 300`; on timeout the sweep defers with the reason recorded in `decision_reason`), re-verifies the checkout holds the default branch at commit time, and the in-turn variant records its lane hold as a `children[]` entry carrying the re-triage completion-evidence class and the `(in-session)` marker, taking the in-session outcome rule.
- Gates, in order, before the sweep commit: `check_backlog_claimed.py` over every candidate in one invocation (the repeatable `--slug`; a claimed verdict is skip-and-annotate and aborts the sweep's remaining moves per the bulk disposition sweep gate), then `doc_registry_validator.py validate`, then the `check-writes` gate over changed paths, then the origins gate `check_plan_origins_closed.py` (its corpus arm for backlog candidates, its plan arm for deferred plans; an origins-gate verdict is recorded in `decision_reason` and never aborts), then the `added-lines em-dash scan`; a claimed-abort sweep leaves every candidate unmoved, records the skip annotations in `decision_reason`, and advances `next_due` by the cadence; on any other gate failure, and on the authorization abort below, the sweep reverses the already-executed dispositions: per the recorded move list it performs the inverse `git mv`, restores the candidate's prior `Status:` header line, and reverts the appended registry audit note, names the failing gate or the abort in `decision_reason`, and advances `next_due` by one day; a sweep that dies mid-move is reconciled by the next sweep, which applies the same full reversal to staged-but-uncommitted sweep dispositions found in the checkout before any new move.
- Authorization: unattended rejection acts only under the live standing owner directive recorded in the deferred README section; the record's `authorized_section_digest` carries the digest of the section text the owner's directive was last verified against (the sweep's record write seeds it on a record that lacks it, from the section text verified at that sweep's re-read; only an owner-recorded digest change rewrites it), and the child re-reads the standing-rule section immediately before the sweep commit comparing against that recorded digest; on section absence or a mismatch against the recorded digest, the sweep aborts with the reversal rule above, records `awaiting-authorization` in `decision_reason`, sets the durable `awaiting_authorization` hold, and falls through to the proposal-report path; a cold-start or re-armed record's first sweep moves nothing and writes only the proposal report (seeding the digest), so no sweep acts on a digest nothing has verified; when no live standing directive is recorded there at all, the child writes the proposal report instead; the proposal report lands under the resolved `friction_audit_dir` beside the record as `retriage-proposal-<YYYY-MM-DD>.md` (newest-wins); every sweep outcome writes the record through the atomic path below; while the hold is set the consult defers the sweep but still writes one proposal per period; the hold clears only when the owner updates the record (deleting the re-triage record is the only sanctioned cold-start re-arm; recording the changed section's new digest after reviewing the change is the only sanctioned hold clear); `next_due` advances by one day on an authorization-aborted sweep (a short retry) and by the cadence on a proposal-report sweep.
- Output: counts (moved, strays removed, kept, skipped-claimed) land in `decision_reason`; the corpus digest, `next_due` (completion time plus the `deferred_retriage_cadence_days` cadence), the dispatch caps, and the last sweep's counts are written to the re-triage record through a temp file plus atomic replace; an unparseable or schema-invalid record defers the consult with a one-day backoff, follows the proposal-report path, records a corruption annotation in `decision_reason` plus a `turn_error: retriage-record-corrupt` so the escalation rails reach the owner, and never writes the corrupt bytes in place (deletion is the only sanctioned cold-start re-arm; the digest update is the only sanctioned hold clear, so corruption cannot re-arm the lane by side effect); the corpus digest is the sweep-time drift witness (each sweep recomputes it and records a mismatch with the recorded digest in `decision_reason` before any move); kept items are `not re-judged before the next due date`; a large cadence value suspends the lane and deleting the re-triage record re-arms it.

- [x] In the Step 2 widened-arm lane-classification sentence, directly after "an audit marker occupies only `G1a`, an execution marker occupies only `G1e`", insert ", a re-triage marker occupies only `G1a`" [class: IMPLEMENTATION_REQUIRED]
- [x] In the Step 2 state-file arm's completion-evidence enumeration, directly after the audit child clause ("for an audit child, the audit state file's digest and `next_due` updated after the entry's `created_at`"), insert ", and for a re-triage child, the re-triage record's corpus digest and `next_due` updated after the entry's `created_at`" [class: IMPLEMENTATION_REQUIRED]
- [x] In the Step 2 fleet-cap guard bullet only (the same string also appears verbatim in the frozen 2026-09-24 Revisions ledger entry; leave that copy untouched), change "counted toward the cap of four like the authoring and audit kinds" to "counted toward the cap of four like the authoring, audit, and re-triage kinds", and change the tail "the per-turn dispatch limits (at most one execution and one authoring per turn) and the audit-lane occupancy rules stand unchanged" to "the per-turn dispatch limits (at most one execution and one authoring per turn) stand unchanged, and the authoring-lane occupancy rules extend to the re-triage child per its consult" [class: IMPLEMENTATION_REQUIRED]
- [x] In the Step 1 audit consult bullet's park-arbitration sentence, change "a retained execute or author dispatch already occupies it" to "a retained execute, author, or retriage dispatch already occupies it" [class: IMPLEMENTATION_REQUIRED]
- [x] In the Step 2 state-file arm's in-session branch, extend the per-kind release-evidence parenthetical with the re-triage class: "for an in-turn re-triage sweep, the re-triage record's corpus digest and `next_due` updated after the entry's `created_at`" [class: IMPLEMENTATION_REQUIRED]
- [x] In the failure cap's progress-definitions bullets, directly after the audit child's progress clause ("Progress for an audit child means..."), insert "Progress for a re-triage child means the re-triage record's corpus digest and `next_due` updated after the recorded `created_at` (the same witness as its completion evidence, the state-file arm), so a re-triage child neither accrues credit while running nor holds the lane after finishing" [class: IMPLEMENTATION_REQUIRED]
- [x] In the G1a exclusivity sentence ("an audit child never runs alongside an authoring child or another audit child"), append "; a re-triage child occupies this same lane and never runs alongside an authoring child, another re-triage child, or an audit child" [class: IMPLEMENTATION_REQUIRED]
- [x] In the Invariants scheduling bullet, beside the audit carve-out, add the re-triage slot-taking clause: the authoring lane serves at most one re-triage child per cadence period, per its `next_due` [class: IMPLEMENTATION_REQUIRED]
- [x] In the Invariants fleet-counting bullet, change "(execution, authoring, audit; the `G1e` / `G1a` fleet counting)" to "(execution, authoring, audit, re-triage; the `G1e` / `G1a` fleet counting)" [class: IMPLEMENTATION_REQUIRED]
- [x] In the State file section's `children[]` entry example, change the kind enum `"execute|author|audit"` to `"execute|author|audit|retriage"` (the same additive extension as the field paragraph) [class: IMPLEMENTATION_REQUIRED]
- [x] In the State file section's `pending_dispatch` field paragraph, change the kind enum `"execute|author|audit"` to `"execute|author|audit|retriage"` (additive, no version bump) [class: IMPLEMENTATION_REQUIRED]
- [x] In the State file section's sanctioned-writer enumeration, extend the scheduler-turn class's mode list with the re-triage dispatch's `children[]` append, the retriage-kind pending-dispatch park write, and the in-turn sweep's `children[]` lane-hold entry (the same scheduler-turn class, no new writer class, mirroring the audit naming) [class: IMPLEMENTATION_REQUIRED]
- [x] In the Step 6 carry-forward clause, append this exact tail (indented code line; copy verbatim, one line, no leading spaces in the target file) [class: IMPLEMENTATION_REQUIRED]

    plus the re-triage lane's scheduler-state writes (the retriage-kind park and the in-turn lane-hold entry, so the rewrite must carry them)
- [x] In the Step 1 "Pending dispatch" bullet, directly after the audit-kind validation clause, insert the clause "for a retriage-kind target the validation is the re-triage consult re-read (the re-triage record's `next_due`, or its cold-start absence), the same shape as the audit-kind read; a valid retriage-kind target dispatches through the re-triage consult dispatch discipline" [class: IMPLEMENTATION_REQUIRED]
- [x] In Step 3, directly after the "Audit-lane same-turn contention" bullet, insert this bullet (indented code line; copy verbatim, one line, no leading spaces in the target file) [class: IMPLEMENTATION_REQUIRED]

    - Retriage-lane same-turn contention (the Step 1 re-triage consult precedes these decisions, so the turn knows before deciding): when the re-triage consult reads due and the authoring lane is free, the re-triage dispatch takes the authoring lane's slot for the turn and D2 resolves to D3 with reason `retriage-lane-due` (a sanctioned must-dispatch exemption, so no dispatch-defect `turn_error` fires), and the in-turn sweep variant takes the same slot and resolution; when the re-triage consult reads due but the authoring lane is held, the re-triage consult parks a retriage-kind `pending_dispatch` entry under the audit arbitration (the sanctioned scheduler-turn park mode) and the next turn's Step 1 reader re-dispatches it when the lane frees; when the audit and re-triage consults are co-due, audit precedence applies (the audit consult is served first regardless of cadence values) and the re-triage consult re-fires next turn because its `next_due` still reads due.

- [x] In `agents/skills/maintenance/zcode.md`, directly after the "Audit child" recognition clause, insert: "  - Re-triage child (added 2026-09-26, origin-class provenance and deferred-corpus re-triage lane): a prompt containing `deferred re-triage lane` plus the resolved repository root (the same containment gate the execution marker applies) occupies only `G1a`, mirroring the audit-child rule, so a listed re-triage record never occupies both lanes; the re-triage child is dispatched idle/off-peak preferred per the SKILL.md re-triage consult; the sweep mechanics are repo-side, so the SKILL.md consult block owns them and no runtime recipe section is added." [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/maintenance/zcode.md`'s fleet-cap sentence, change "authoring, audit, and execution children are fleet members" to "authoring, audit, re-triage, and execution children are fleet members" [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/maintenance/prompt-templates.md`, add a retriage child pointer stub beside the existing child blueprints: it carries none of the counted dispatch-slice spans (no `<prompt` wrapper paragraph, no re-arm paragraph, no HOST CAVEAT, no primitive-precheck sentence) and states that the retriage child's payload is assembled per the dispatch ladder (including the re-arm-first action it requires of every child payload) with the SKILL.md re-triage consult block as the procedure of record, carrying the `deferred re-triage lane` recognition literal plus the repository root [class: IMPLEMENTATION_REQUIRED]
- [x] In `scripts/check_maintenance_pins.sh`, register companion pins for the lane's operative spans (the consult bullet's distinctive fragment, the `retriage-lane-due` reason literal, the zcode.md recognition literal, the fleet-cap enumeration, the prompt-templates stub) and replace the two-count `execute|author|audit` State-file pin with the four-kind literal; pin literals and citation comments only [class: IMPLEMENTATION_REQUIRED]
- [x] Insert at the top of the Revisions section, above the existing 2026-09-26 entries, one entry: "- 2026-09-26 (origin-class provenance and deferred-corpus re-triage lane, `docs/history/plans/2026-09-26-origin-class-provenance-and-deferred-retriage-lane.md`): the survey gained the origin token and consumer-first ordering; the deferred-corpus re-triage lane joined (consult block, sweep sub-bullets, contention clause, widened-arm, completion-evidence, and progress arms, kind-enum extension, sanctioned-writer modes, carry-forward clause); companion pins registered in the pins suite." [class: IMPLEMENTATION_REQUIRED]
- [x] `RetriageLane#consult_and_gates`; given the edited files, expects every G4 grep to pass, including the placement probe, the no-restatement negative gates, the wrapping-independent gate-order chain, the two kind-enum sites, the purpose-cell, widened-arm, completion-evidence, progress-arm, sanctioned-writer, carry-forward, and enumeration pins, and the zcode.md and prompt-templates pins [class: REPOSITORY_TEST]
- [x] Corpus dry run: run the sweep mechanics in a no-move mode over the current deferred corpora and record the verdicts in the execution log: kept items stay, zero files touched under the rejected archives, promoted items not re-judged, claimed items (if any) skipped and annotated with the claiming plan; the dry run performs the authorization re-read and records the merge-lock holder read (holder absence expected) instead of acquiring the lock (second origin acceptance clause 2) [class: REPOSITORY_TEST]
- [x] Run the FULL battery from the repository root with `PLAN_BASE` set to the base sha already recorded in the execution log before the first task commit (a run whose G5 is skipped does not satisfy this gate) → expect `VALIDATION OK` (G1-G4 green, G5 checked against that base, G6 and G7 green); after the final commit, re-run the G5 block once (it then covers the closing commit itself) → expect the same pass [class: REPOSITORY_TEST]
- [x] Commit: `skills: maintenance gains the periodic deferred-corpus re-triage lane` [class: IMPLEMENTATION_REQUIRED]
