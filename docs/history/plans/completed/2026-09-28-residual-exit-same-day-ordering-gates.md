# Plan: Residual-acceptance exit same-day ordering gates

Backlog origin: docs/history/backlog/2026-09-19-residual-exit-same-day-ordering-semantics.md
Driving force: external (source: P11 execution review r1, F4, recorded in the backlog origin and promoted 2026-09-26 under the direction triage as a self-serving witnessed defect; the live residual-acceptance exit gate's ordering proof refuses the skill-prescribed same-day record-then-round shape and anchors the boundary at UTC midnight of the sidecar round date, so the refusal depends on the operator's timezone offset). Justification: this is not one of the four driving principles, but it is implemented anyway because the defect pressures orchestrators toward backdating `recorded_at`, an input the driver cannot verify, and refuses the normal operator flow on the playbook's own pre-archive surface: a fail-closed gate seated against its documented intent. Park-triage would not take it because the defect is live on the playbook's own pre-archive gate and parking it keeps the backdating pressure active on every residual-acceptance exit.
Plan review record: the staging series docs/reviews/2026-09-28-plan-review-residual-exit-same-day-ordering-gates-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The residual-acceptance exit gate accepts the skill-prescribed same-day record-then-round shape in every timezone, and the ordering proof stops pressuring orchestrators to backdate the policy's `recorded_at` epoch.

- A residual policy recorded on the round's own calendar day passes the pre-archive ordering proof; the proof refuses only a policy recorded at or after the following machine-local midnight (strict again the next day).
- The UTC-midnight anchor is gone: the boundary is computed from the sidecar round date in the machine's local zone, so the accept/refuse boundary no longer depends on the operator's offset from UTC.
- The refusal message states the real bound (recorded no later than the round's day, same-day recording sanctioned) instead of demanding an unmeasurable "before the round ran" ordering.
- The execute-plan runtime contract and skill prose name the day-precision witness and the sanctioned same-day shape, and regression tests pin the same-day accept, the after-round-day refuse, and the local-anchor boundary in both an eastern and a western timezone.

## Terms

- **Residual-acceptance exit**: the bounded pre-archive exit (origin D) where a recorded `residual_policy` (named finding ids, grant source, recorded-at epoch) lets the gate accept the focused verification-round sidecar with out-of-set blocking rows as backlogged residuals.
- **Ordering proof**: the OR-branch sub-check in the pre-archive eligibility predicate that compares the policy's `recorded_at` against the sidecar round `date`; this plan changes only this sub-check and its refusal message.
- **Round-day end**: machine-local midnight beginning the calendar day after the sidecar round date, computed by naive local date arithmetic resolved through `datetime.timestamp()`.
- **Machine-local anchor**: the interpretation of the sidecar's plain `YYYY-MM-DD` date string in the machine's local timezone (the zone the review panel wrote the date in), replacing the forced-UTC anchor.

## Assumptions

- assume the sidecar `date` is the machine-local calendar date of the focused verification round; basis: review staging docs are authored by panels running on the operator machine and record the authoring date as a plain `YYYY-MM-DD` string, and the driver consumes that string unchanged.
- assume the witness stays day-precision and the prose keeps the stricter behavioral rule; basis: the driver cannot verify intra-day ordering of an operator-supplied epoch (the origin's own observation), so the gate witnesses "no later than the round's day" while `agents/skills/execute-plan/SKILL.md` continues to require recording the policy before the verification round runs.
- assume naive local date arithmetic plus `datetime.timestamp()` is the correct round-day-end computation; basis: a naive `datetime` resolved by `.timestamp()` uses the machine's local zone and is DST-aware through the platform; the documented approximation at a midnight DST transition (a one-hour boundary shift) is accepted and never exercised by the pinned test dates.
- assume tests pin the timezone through `os.environ["TZ"]` plus `time.tzset()` with an addCleanup restore whose exact semantics are pinned: record whether `TZ` was originally present, delete the variable when it was absent (an empty `TZ` is POSIX UTC, not unset), and re-run `time.tzset()` as the final cleanup step so a cached zone cannot outlive the test; skipped where `time.tzset` is absent; basis: the driver test suite already targets POSIX hermetically, and the unpinned runner zone must not decide boundary outcomes.
- assume the existing prior-day fixture (`recorded_at = ROUND_DAY_EPOCH - 86400`) passes under both the old and the new bound in every zone; basis: arithmetic: any local round-day end for the round date exceeds the prior-day epoch.
- assume the refusal message is evidence text, not a stable contract key; basis: driver refusal messages elsewhere are free text and the runtime contract prose is the documented behavior, so rewording the message breaks no consumer.
- assume no manifest schema or receipt field changes; basis: the change is confined to the OR-branch comparison and its message; the `archive_gate` receipt fields and the `residual_policy` input shape are untouched.
- assume every pre-existing residual-acceptance test keeps passing except `test_refuses_policy_recorded_after_verification_round`, which pins the old UTC-midnight boundary and the old refusal message and is retargeted in Task 1 under the Review Scope bound-collision exception; basis: read of `scripts/test_execute_plan_runtime.py` at authoring time: the accept arm records the policy a full day before the round date, but the retargeted test's refuse arms sit exactly on the moved boundary and its evidence assertion names the old message text (review r1 F1, verified by five workers).

Decision points requiring a grill: fix shape: realign the gate (round-day-end bound) over amending the prose to require prior-day recording (the origin's option B); source: the origin's fix shape plus the standing pre-authorization carried by the dispatching directive (the rolling-log entry's Standing pre-authorization line), decided 2026-09-28; affects Task 1's implement and retarget bullets, the Terms' Round-day end and Machine-local anchor entries, and the two-zone regression test. Anchor: machine-local midnights over a UTC round-day end; source: the origin's timezone-dependence complaint, decided 2026-09-28; affects the Terms, the Gist, and Task 1's timezone-pinned test set. Basis in both cases: the witnessed defect is the gate refusing the normal shape, so realigning the witness fixes it while option B would codify refusing it, and a UTC day-end anchor still refuses an honest same-evening recording west of UTC, preserving exactly the backdating pressure the origin witnesses. Both decided at authoring time per the standing pre-authorization (accept recommended options without asking).

## Gist & Examples

TLDR: The residual-acceptance exit's ordering proof now witnesses "the policy existed no later than the round's day" instead of "before UTC midnight of the round date", so the skill-prescribed same-day record-then-round flow passes in every timezone and only a policy recorded the day after the round refuses; the contract sentence, the refusal message, and the timezone-boundary tests move with it, answering the witnessed P11 defect.

What changes in the driver: inside the pre-archive eligibility predicate's residual-policy OR-branch, the boundary moves from UTC midnight of the sidecar round date to the machine-local midnight that ends the round day: `round_day_end = (datetime.strptime(round_date.strip(), "%Y-%m-%d") + timedelta(days=1)).timestamp()`, refusing when `recorded_at >= round_day_end`; a shape-valid date outside the representable range (the max date, where the old expression evaluated cleanly) gets a typed unorderable-date refusal beside the existing ValueError arm so the proof stays fail-closed. The refusal message is reworded to name that bound and to state that same-day recording is sanctioned. The missing-date refusal, the malformed-date refusal for genuinely malformed dates, the verdict narrowing, the membership rule, and the receipt shape are untouched. `timedelta` replaces the orphaned `timezone` in the import.

What changes in prose: the runtime contract's OR-branch sentence ("the policy's recorded-at predates the sidecar's round `date` ... so a policy recorded at or after the round day refuses") becomes the day-end sentence naming the machine-local anchor and the sanctioned same-day shape; the skill's Residual-acceptance exit row gains a clause sanctioning same-day recording and naming the day-precision witness.

Example regression fixture (the origin's shape): the orchestrator records `residual_policy:` at 14:00 local and the focused verification round runs the same day, sidecar dated that day. Today the gate refuses and the only sanctioned-looking repair is backdating `recorded_at` to the previous day. After this plan the same run passes the ordering proof. A policy recorded at 09:00 local the day after the round (sidecar still dated the round day) refuses under the new bound with the reworded message, and the boundary tests pin that this holds in both `Asia/Singapore` (UTC+8, the origin's witness) and `America/Los_Angeles` (UTC-7 in September, where the old anchor and a UTC day-end anchor would both refuse an honest 23:00 same-day recording).

## Evaluation Criteria

**Quality dimensions:**
- correctness: same-day recording passes at both boundary test zones and at UTC; recording at or after the following local midnight refuses; the pre-existing prior-day accept arm and the whole residual family stay green.
- fail-closed reliability: the bound stays fail-closed (at-or-after refuses); a shape-valid date outside the representable range gets a typed unorderable-date refusal instead of the raw OverflowError the naive arithmetic would raise; the missing-date refusal and the malformed-date refusal for genuinely malformed dates are byte-identical in behavior; a refusal leaves the manifest unchanged (the existing refusal-preservation assertion covers the new refuse tests).
- maintainability: one comparison and one message change; no new state, no new operation, no receipt or schema change.
- test coverage: a RED canary per new boundary (same-day accept, after-round-day refuse, two-zone local-anchor witness) plus the unchanged pre-existing family as the regression control.

**Done when:**
- `python3 scripts/test_execute_plan_runtime.py -k residual` exits 0.
- `python3 scripts/test_execute_plan_runtime.py -k shared_skill_bodies` exits 0.
- `python3 scripts/test_execute_plan_runtime.py` (full suite) exits 0.
- The five prose and message obligation greps in Validation Commands pass.

**Ship when:**
- Ship when:
- Consumer repositories that vendor the execute-plan skill and driver pick up the amended files on their next vendored sync; the upstream repo carries no deployment step for this change (driver behavior plus prose; no checklist item).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_runtime.py` (only the residual-policy OR-branch ordering proof inside the pre-archive eligibility predicate and its refusal message, plus the `timedelta` import; every other function in this file is frozen; reject any review finding that touches them)
- `agents/skills/execute-plan/SKILL.md` (only the Residual-acceptance exit row clause insertion; the rest of the file is frozen)
- `agents/skills/execute-plan/runtime-contract.md` (only the residual OR-branch sentence in the pre-archive input clause; the rest of the file is frozen)

**Tests:**
- `scripts/test_execute_plan_runtime.py` (only the new residual-adjacent tests and the timezone-pin helper, placed adjacent to the existing residual-acceptance fixtures; existing tests are frozen except where a proven bound collision exists, which would be a plan defect to report)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `README.md`; no skill catalog entry changes.
- `scripts/execute_plan_runtime_codex.py` and `agents/skills/execute-plan/runtime-adapters/`; verified at authoring time, the adapter layer carries no residual ordering logic and consumes the envelope without shape change.
- The verdict narrowing, membership rule, input shape guard, and receipt shape of the residual branch; this plan changes only the ordering boundary and its message.
- All other skills and docs; the backlog scopes this to the execute-plan skill, its runtime contract, and the driver.

## Validation Commands

Authoring-time execution record (rule 29): the em-dash scan (`scripts/check-no-em-dash.sh file`), the public-hygiene scan, and the structural pre-round readiness gate (`scripts/plan_readiness.py --pre-round`) were executed over the plan bytes before review round 1 (em-dash clean, hygiene exit 0, pre-round structural checks clean); the five prose and message obligation greps below were executed RED-today before review round 1 (patterns absent from the current tree; the fifth, the driver docstring obligation, was added by review r2 and verified absent at fold time), and the block passes `bash -n`.

```bash
python3 scripts/test_execute_plan_runtime.py -k residual || { echo "residual family regression failed"; exit 1; }
python3 scripts/test_execute_plan_runtime.py -k refuses_policy || { echo "retargeted boundary test failed"; exit 1; }
python3 scripts/test_execute_plan_runtime.py -k shared_skill_bodies || { echo "shared-body runtime-neutrality gate failed"; exit 1; }
python3 scripts/test_execute_plan_runtime.py || { echo "full driver suite failed"; exit 1; }
grep -qF "falls after the sidecar round date" scripts/execute_plan_runtime.py || { echo "driver round-day-end refusal message missing"; exit 1; }
grep -qF "before the end of the sidecar's round" agents/skills/execute-plan/runtime-contract.md || { echo "runtime-contract day-end obligation missing"; exit 1; }
grep -qF "following local midnight" agents/skills/execute-plan/runtime-contract.md || { echo "runtime-contract local-midnight anchor missing"; exit 1; }
grep -qF "same-day recording sanctioned" agents/skills/execute-plan/SKILL.md || { echo "SKILL.md same-day sanction missing"; exit 1; }
grep -qF "falls before the end of the sidecar's round date" scripts/execute_plan_runtime.py || { echo "driver docstring day-end obligation missing"; exit 1; }
```

### Task 1: Round-day-end ordering bound in the residual-acceptance OR-branch

Files:
- `scripts/execute_plan_runtime.py` (the OR-branch ordering proof and refusal message inside the pre-archive eligibility predicate, plus the `timedelta` import)
- `scripts/test_execute_plan_runtime.py` (existing file; new tests and the timezone-pin helper only, adjacent to the existing residual-acceptance fixtures)
- [x] RED: `test_accepts_same_day_residual_policy_recording` (library-level `pre_archive` entry, timezone pinned to UTC via the new helper); given the focused-round `residual_sidecar()` fixture dated `ROUND_DATE` and a `residual_policy(recorded_at=ROUND_DAY_EPOCH + 43200)` (noon UTC on the round's own day), expects the pre-archive stage to succeed: `archive_gate` recorded, `workflow_state` active, no `terminal_receipt` [class: REPOSITORY_TEST]
- [x] RED: `test_residual_day_end_anchor_is_machine_local` (library-level `pre_archive` entry, two timezone-pinned halves); with `TZ=America/Los_Angeles`, given `residual_policy(recorded_at=ROUND_DAY_EPOCH + 108000)` (23:00 on the round's own local day, which is already the next UTC day), expects success, pinning the machine-local anchor because a UTC-anchored day-end bound would refuse this recording; with `TZ=Asia/Singapore`, given `residual_policy(recorded_at=ROUND_DAY_EPOCH + 90000)` (09:00 local on the day after the round), expects a blocked `done-pending` refusal whose evidence names the reworded round-day message and asserts the manifest bytes are unchanged through the suite's existing refusal-preservation assertion, completing the origin's UTC+8 witness [class: REPOSITORY_TEST]
- [x] RED: `test_refuses_residual_policy_recorded_after_round_day` (library-level `pre_archive` entry, timezone pinned to UTC); given `residual_policy(recorded_at=ROUND_DAY_EPOCH + 90000)` (01:00 UTC on the day after the round), expects a blocked refusal whose evidence names the new message text, and asserts the manifest bytes are unchanged through the suite's existing refusal-preservation assertion [class: REPOSITORY_TEST]
- [x] RED: `test_refuses_policy_recorded_after_verification_round` is retargeted here under the Review Scope bound-collision exception (review r1 F1): rewrite the pre-existing test (adjacent to the residual fixtures) to the new semantics: its evidence assertion switches from the old "does not predate" fragment to the new message text, its refuse arms re-pin zone-safe inside the timezone-pinned helper with one arm recorded exactly at the computed local round-day end (the at-or-after strictness witness) and one arm strictly past it, a zone-pinned accept arm records the old UTC-midnight probe `ROUND_DAY_EPOCH` (now a sanctioned same-day recording), the test's comment block is rewritten from the old UTC rule to the round-day-end rule, and the hosting test class's docstring sentence restating the old predates-the-round-date rule is rewritten to the round-day-end wording under the same exception (review r2 F4); the retargeted test's id contains neither the `residual` nor the `create` selector substring, so `-k residual` alone misses it, and `-k refuses_policy` matches its existing id, which the retarget keeps [class: REPOSITORY_TEST]
- [x] RED: `test_residual_unorderable_max_date_sidecar_round_date` (library-level `pre_archive` entry, timezone pinned to UTC); given the residual sidecar fixture with `date` overridden to `9999-12-31` (shape-valid ISO, so the malformed-date refusal does not apply) and a policy with the realistic fixture-scale `recorded_at` `ROUND_DAY_EPOCH`, expects a blocked `done-pending` refusal whose evidence names the unorderable-date refusal text, and asserts the manifest bytes are unchanged through the suite's existing refusal-preservation assertion; red today on its status assertion, because the current UTC-anchored expression evaluates the max date cleanly (about 2.53e11) and the pinned `recorded_at` falls below it, so today's gate fail-opens and accepts the sidecar, exactly the defect the typed refusal closes; the message assertion turns red only after the typed refusal exists (review r2 F1, r3 F2) [class: REPOSITORY_TEST]
- [x] Run → expect RED: `python3 scripts/test_execute_plan_runtime.py -k residual` selects the residual family including the four new tests; `test_accepts_same_day_residual_policy_recording`, the `America/Los_Angeles` half, and the max-date witness fail against the current bound's behavior (the same-day accept and the LA half on status; the max-date witness fail-opens today, so its status assertion is red), and the two message-assertion arms fail on the message text while their status assertions are already green today (the `Asia/Singapore` half: `ROUND_DAY_EPOCH + 90000` is already refused by the current bound, so only the reworded-message evidence assertion is red); every pre-existing `-k residual`-selected test passes; `python3 scripts/test_execute_plan_runtime.py -k refuses_policy` selects exactly the retargeted test and expects it red on its accept arm and message arms; record the exact set [class: REPOSITORY_TEST]
- [x] Implement in `scripts/execute_plan_runtime.py`: change the import to `from datetime import datetime, timedelta` (the `timezone` name loses its last use with the UTC anchor); inside the residual-policy OR-branch, replace the UTC-midnight anchor with the machine-local round-day end, `round_day_end = (datetime.strptime(round_date.strip(), "%Y-%m-%d") + timedelta(days=1)).timestamp()`, and refuse when `float(residual_policy["recorded_at"]) >= round_day_end`; add an `except OverflowError` arm beside the existing `except ValueError` (the timedelta arithmetic overflows the representable range for the shape-valid max date `9999-12-31` where the old UTC expression evaluated cleanly) returning the typed refusal `clean-round review sidecar round date cannot order the residual policy proof: {round_date.strip()}`; reword the boundary refusal message to `residual policy recorded_at {recorded_at} falls after the sidecar round date {round_date}; the policy must be recorded in the manifest no later than the round's own day (same-day record-then-round recording is sanctioned; a policy recorded on a later day refuses)`; update the OR-branch paragraph of `_pre_archive_gate`'s docstring, which restates the ordering rule with the old UTC anchor, rewording it to state that the proof accepts when the policy's recorded-at falls before the end of the sidecar's round date and refuses at or after the following machine-local midnight, so the docstring cannot contradict the amended contract in the same diff (this paragraph is inside the declared must-fix scope); the missing-date refusal keeps its exact current text and order, and the malformed-date refusal keeps its exact current text and order for genuinely malformed dates [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/test_execute_plan_runtime.py -k residual`, `python3 scripts/test_execute_plan_runtime.py -k refuses_policy`, and `python3 scripts/test_execute_plan_runtime.py -k create` all exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `execute-plan: accept same-day residual-policy recording via a local round-day-end bound` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Contract and skill prose realignment

Files:
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/SKILL.md`
- [x] In `runtime-contract.md`, inside the pre-archive input clause's residual OR-branch sentence, replace the comparison clause "when the policy's recorded-at predates the sidecar's round date (the proof is strict at day precision, so a policy recorded at or after the round day refuses)" with "when the policy's recorded-at falls before the end of the sidecar's round date (the proof is strict at day precision and anchored at machine-local midnights, so a policy recorded on the round's own calendar day passes, the normal record-then-round shape, and a policy recorded at or after the following local midnight refuses)", keeping the backticks around the date field name as they appear in the file; every other clause of the sentence (the membership rule, the verdict narrowing, the integer-id refusal) stays byte-identical [class: IMPLEMENTATION_REQUIRED]
- [x] In `SKILL.md`'s Residual-acceptance exit row, immediately after `(the named finding set, the grant's source, and the date)`, insert `, same-day recording sanctioned (the pre-archive ordering proof witnesses the ordering at day precision, so only a policy recorded later than the round's day refuses)`; the rest of the row, including the BEFORE-the-verification-round behavioral rule, stays unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the five prose and message obligation greps from Validation Commands, plus `python3 scripts/test_execute_plan_runtime.py -k shared_skill_bodies` [class: REPOSITORY_TEST]
- [x] Commit: `execute-plan: realign residual-policy ordering prose with the round-day-end witness` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Full validation pass

Files:
- `scripts/test_execute_plan_runtime.py` (verification only; the file is executed by the task's gates, never edited by this task)
- [x] Run the complete Validation Commands block from the repository root → expect every gate GREEN (all nine commands exit 0, including the full driver suite) [class: REPOSITORY_TEST]
- [x] Fold-coherence self-audit (the reconciliation witness for the fold-hygiene class, review r3 and the reconciliation record): verify every count mention in the plan (command counts, grep counts, test-set sizes) matches the Validation Commands block, every named test id matches at least one `-k` selector in its owning task's RED and GREEN gates, every RED characterization matches computed current-tree behavior, and every coverage claim (refusal preservation) has its assertion mandated in the test bullet it covers; record the check and its result in the Task 3 report [class: REPOSITORY_TEST]
