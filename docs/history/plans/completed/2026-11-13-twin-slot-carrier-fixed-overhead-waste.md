# Plan: same-slot exec carriers share survey lane state and one pinned selection ordering

Backlog origin: docs/history/backlog/2026-11-13-twin-slot-carrier-fixed-overhead-waste.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-11-13-plan-review-twin-slot-carrier-fixed-overhead-waste-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1.0h total, largest task 0.5h
Executed: yes (2b6f96a4c76eb131b9ef118b214fc916c262898f)

## Terms

- twin carriers: two one-shot maintenance exec carriers armed in the same slot (the same fire minute), each running the exec-mode session flow independently.
- lane-state file: the small JSON record an exec-mode session writes after its survey completes; a twin arriving while it is fresh reads it instead of re-surveying.
- staleness bound: the maximum age of a lane-state record a reader may trust; a record older than the bound is not consumed and the reader re-surveys. Basis: the witnessed same-slot arrival offsets are tens of seconds (33 s and 23 s), so a small multiple of the survey duration covers every witnessed twin; the bound is 10 minutes.
- survey overhead: the exec-mode session's expensive start-of-run work before selection: the Step 0 context load and the Step 1 survey legs (memory-index read, scheduler-state read, loop-liveness check, open-plans survey, digest verification, admission-consult inputs).
- lane-state record: the survey-output record only; the urgency ordering and the selection are re-derived per session from the shared candidate set (cheap), never consumed from the record.
- skip-and-continue doctrine: the D1 claimed-top-target arm: a session losing a claim race records the race and continues to the next target-disjoint candidate instead of standing down.
- selection-order token: the `selection-order:<segment>` decision_reason token that records which segment of the pinned ordering produced the dispatch.

## Why

Every same-slot pair of exec carriers repeats the full survey overhead and races the same claims, because no surface carries the first finisher's survey result to its twin, and the exec selection rule's prose admits more than one stated rationale for the same rulebook. This plan gives same-slot carriers one shared survey record and one pinned ordering. It is session-side cost reduction: the operator's standing no-duplicate-lookup rule for schedule asks stays untouched.

## Gist & Examples

TLDR: exec twins read a fresh survey lane-state file instead of re-surveying and the exec selection rule names one tie-broken ordering, cutting duplicated Step 0 overhead and divergent-rationale picks, for efficiency.

Before: two carriers armed at 20:50 each run the full Step 0 survey; the loser races the winner's claim 33 seconds after the take, releases its claim and worktree, and falls through per skip-and-continue. Two twins at 22:50 take two different plans, each citing a different selection rationale for the same rulebook.

After: the first finisher writes its survey output (candidate set of dispatchable open plans with digest dispositions, claim states as observed, written-at stamp, session id, observed HEAD sha) to `docs/tmp/exec-lane-state.json` atomically at the end of its survey legs; the slower twin, still mid-survey, checks the record at each of its remaining survey-leg boundaries, and when a fresh foreign record whose HEAD sha matches the current HEAD appears, it adopts the recorded candidate set as its survey output, skips the remaining legs, re-checks claims and digest dispositions at take time exactly as today, and picks by the one pinned ordering it derives itself, recording the selection-order token. A stale, non-matching, or absent record means a normal full survey.

Edge cases: the winner dies between survey and write, so no record exists and the twin re-surveys; the record is older than the staleness bound or its HEAD sha no longer matches, so the twin re-surveys and overwrites; a recorded top candidate's claim or digest state changes between the read and the take, so the take-time re-checks apply unchanged; the record's session id names this session, so the session refreshes its own record instead of consuming it; two twins finish near-simultaneously, so each write is atomic (temp file plus rename) and last-writer-wins under the freshness keys; the record fails to parse or lacks required fields, so the reader treats it as absent and re-surveys, never partial-adopting.

## Outcome

Same-slot exec carriers stop duplicating the survey overhead and cannot diverge on selection rationale.

- The first exec finisher of a slot's survey leaves a bounded-staleness lane-state record that a slower twin in the same window reads at its remaining survey-leg boundaries instead of re-running those legs, with claim and digest re-checks at take time unchanged.
- The exec-mode selection rule states exactly one tie-broken ordering, and every exec dispatch records the selection-order token, so two compliant sessions state the same rationale for the same rulebook.
- The schedule-ask side is unchanged: no duplicate-lookup pass is restored and no same-slot stagger is introduced.

Gate delta: adds one cross-session protocol layer (the survey-output lane-state record with its writer, reader, atomicity, and freshness keys) and one recording-token duty inside the existing Exec-mode selection rule; no new refusal class, no new gate or fence, no schema field, no dispatch-pause condition. Pricing: the protocol layer carries its completed-integrity-failure witness, the 2026-11-13 01:51 slot where an armed twin errored at zero turns against a lane an earlier same-window carrier had already emptied (a completed carrier failure recorded in the origin row and its cluster row docs/history/backlog/2026-11-13-errored-zero-turn-carrier-recovery.md); the token duty is priced by the 2026-11-12 22:50 slot where two compliant sessions applied different stated selection rationales to the same rulebook (the determinism contract's witnessed failure), and the token replaces that rule's free-form record-the-selected-order clause, the named simplification. The origin's rejected alternatives (schedule-side duplicate lookup, skip-and-continue removal, unbounded staleness) remain the shape-choice evidence, not the pricing.

## Assumptions

- The lane-state file lives at `docs/tmp/exec-lane-state.json` in the primary checkout so no scheduler-state schema change and no new sanctioned-writer class is needed; basis: docs/tmp/ already hosts per-session scratch surfaces the maintenance monitors sweep.
- Shape choice: the shared lane-state file over same-slot stagger; basis: stagger requires the arming session to detect a same-slot twin first, which is exactly the schedule-side duplicate lookup the operator's recorded standing direction forbids, while the file is session-side only and respects that boundary.
- Only survey output is shared; the urgency ordering and selection are re-derived per session from the shared candidate set; claim and digest dispositions recorded in the file are advisory and re-checked at take time; basis: the origin row's bounded-staleness requirement and the rejected unbounded-staleness alternative.
- Concurrent same-slot writers need no lock: writes are atomic (temp file plus rename), last-writer-wins under the freshness keys, and a malformed or partial record is treated as absent; basis: the reader's freshness keys (staleness, HEAD sha, parse integrity) make an interleaved stale write unconsumable without adding lock machinery.
Decision points requiring a grill: none remain.

## Standing constraints

- Byte-budget discipline: agents/skills/maintenance/decisions.md sits above its byte cap (advisory ratchet breach at authoring time), so any byte growth in it inside this plan's tasks deletes equivalent bytes in the same change, and scripts/skill_text_budget.py --check must end OUTCOME: pass with no ratchet breach line added beyond the pre-change baseline of three.
- Operative text cites its witness in one line: the divergent-rationale slot (2026-11-12 22:50 WET) and the two race slots (20:50, 21:50, same day) are each cited once as witness evidence, never as narrative.

## Evaluation Criteria

**Quality dimensions:**
- correctness: a lane-state reader cannot act on a record that fails its freshness keys (staleness bound, HEAD-sha equality, parse integrity); the keys and the take-time re-checks are explicit in the duty text.
- operator-rule compliance: no duty text requires or permits a schedule-side duplicate-lookup pass or a stagger; the boundary is stated once.
- determinism: the pinned ordering leaves no second compliant reading; each segment's tie-break is named and the segment vocabulary for the token is enumerated.

**Done when:**
- The maintenance skill's operative text names the lane-state writer, the reader, the staleness bound, and the unchanged take-time claim re-checks.
- The Exec-mode selection rule bullet names one tie-broken ordering and carries the selection-order token duty.
- python3 scripts/skill_text_budget.py --check ends OUTCOME: pass with the ratchet breach count not increased versus the pre-change baseline.
- agents/skills/maintenance/CHANGELOG.md gains one dated entry citing this plan.

**Ship when:**
- none; repository-internal change. The runtime copy sync rides the standing vendored-sync flow and is outside this plan's scope.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/survey-arms.md` (Task 1)
- `agents/skills/maintenance/decisions.md` (Task 2)
- `agents/skills/maintenance/CHANGELOG.md` (Task 3)

**Tests:**
- none; prose-only operative-text change validated by the budget gate and the readiness validators.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/zcode.md`; reason: the schedule-ask carrier creation form is unchanged by the chosen shape, and the origin row's schedule-side alternative was rejected.
- `scripts/*`; reason: no script behavior changes; the lane-state file is a prose-prescribed session surface, not machinery.

## Validation Commands

```bash
python3 scripts/skill_text_budget.py --check
bash scripts/check_maintenance_pins.sh
python3 scripts/plan_readiness.py docs/history/plans/2026-11-13-twin-slot-carrier-fixed-overhead-waste.md
grep -c "docs/tmp/exec-lane-state.json" agents/skills/maintenance/survey-arms.md
grep -c "selection-order:" agents/skills/maintenance/decisions.md
grep -c "Survey-result lane-state sharing" agents/skills/maintenance/survey-arms.md
test "$(wc -c < agents/skills/maintenance/decisions.md)" -le 99904
```

### Task 1: Exec-mode survey lane-state record and read duty

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/survey-arms.md`

Primary class anchors:
- `Survey-result lane-state sharing` in `agents/skills/maintenance/survey-arms.md`

- [x] The new arm states the writer duty: an exec-mode session writes `docs/tmp/exec-lane-state.json` in the primary checkout (explicit-rooted form) atomically (temp file plus rename) immediately after its survey legs complete [class: IMPLEMENTATION_REQUIRED]
- [x] The record holds written-at (ISO plus epoch), the writing session id, the observed HEAD sha, the ask-scope class, and the candidate set of dispatchable open plans with per-candidate digest dispositions and claim states as observed at survey time; the urgency ordering and selection are never written, each session derives them from the candidate set [class: IMPLEMENTATION_REQUIRED]
- [x] The new arm states the reader duty: an exec-mode session running behind its slot-mate checks the record at each of its remaining survey-leg boundaries (open-plans survey, digest verification, admission-consult inputs) [class: IMPLEMENTATION_REQUIRED]
- [x] The reader adopts the recorded candidate set and digest dispositions as its survey output and skips the remaining legs only when the record is from a different session and fresh: written-at within the 10-minute staleness bound, HEAD sha equal to the current HEAD, parse-complete with all required fields [class: IMPLEMENTATION_REQUIRED]
- [x] The adoption never replaces the take-time re-checks: every claim and digest disposition is re-checked at take time exactly as today, and the reader re-derives everything the pinned chain consumes that the record does not carry: its queue head, ask scope, agent-type affinity, quota reads, memory dependency-chain order from the memory index, and the parked-dependency actionability marking, which sits inside the skip window [class: IMPLEMENTATION_REQUIRED]
- [x] The new arm states the boundary conditions: a record older than the staleness bound or whose HEAD sha differs is re-surveyed and overwritten; a record that fails to parse or lacks required fields is treated as absent, never partial-adopted [class: IMPLEMENTATION_REQUIRED]
- [x] A session reading a record naming its own session id refreshes its own record instead of consuming it, and concurrent writers need no lock: last-writer-wins under the freshness keys [class: IMPLEMENTATION_REQUIRED]
- [x] The record carries only the plans segment survey output; a session that adopts it still reads the EXEC-PROMPTS log positions and ad-hoc eligibility itself (cheap reads) and derives the merged ordering over the union [class: IMPLEMENTATION_REQUIRED]
- [x] The new arm carries one witness line citing the 20:50 and 21:50 race slots of 2026-11-12 and the 01:51 slot of 2026-11-13 (the origin row's evidence basis) [class: IMPLEMENTATION_REQUIRED]
- [x] The arm keeps the schedule-ask boundary visible in one clause: session-side sharing only, no schedule-side duplicate lookup or stagger [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a lane-state record whose written-at is older than the staleness bound or whose HEAD sha differs from the current HEAD, expects the arriving session re-surveys and never consumes the record [class: REPOSITORY_TEST]
- [x] Safety witness: given a recorded top candidate whose claim or digest state changes between read and take, expects the take-time re-checks (the fresh-execution-claim skip and digest verification) to apply unchanged; grep needle: `grep -c "docs/tmp/exec-lane-state.json" agents/skills/maintenance/survey-arms.md` returns at least 1 [class: REPOSITORY_TEST]
- [x] The new arm stays compact: its added bytes stay under 1000 total (compose tight), and the run records the resulting survey-arms growth-watch line (advisory; the file has no cap breach) in the certification evidence [class: REPOSITORY_TEST]

### Task 2: Pin the exec selection ordering to one tie-broken chain

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/decisions.md`

Primary class anchors:
- `Exec-mode selection rule` in `agents/skills/maintenance/decisions.md`

- [x] The bullet names exactly one tie-broken ordering that rides the inherited contracts verbatim: the execution_queue head and execution_priority read first as today, then the parked-dependency unblock dispatch when actionable, then the plans segment in D1's full chain [class: IMPLEMENTATION_REQUIRED]
- [x] The pin names the plans segment as D1's full ordering by reference and names its precedence compactly: the fresh-plan continuation preference ahead of the memory dependency-chain order when available, noted-plan promotion ahead of the oldest-basename ordering within the digest-intact class, then the oldest-basename and oldest-open fallbacks; D1's own text stays the chain's single home and the bullet never copies the chain [class: IMPLEMENTATION_REQUIRED]
- [x] The ordering continues: ready EXEC-PROMPTS entries by log position, then ad-hoc-eligible items by the priority profile's group with the consumer-urgency exception promoting its item ahead of the preceding segment [class: IMPLEMENTATION_REQUIRED]
- [x] The within-segment tie-break is oldest basename for plans and ad-hoc items and log position for EXEC-PROMPTS entries, no stated rationale outside this ordering selects, and the pin carries no witness narrative (the 22:50 divergent-rationale citation lives once, in the Task 3 CHANGELOG entry, per the repo's land-the-rule-not-the-story rule); the "plans (D1's ordering)" cross-reference in D1 stays valid (the pin edits only the Exec-mode selection rule bullet) [class: IMPLEMENTATION_REQUIRED]
- [x] The bullet's "record the selected order in decision_reason" clause becomes the selection-order token duty: every exec dispatch records `selection-order:<segment>` naming the segment that produced it [class: IMPLEMENTATION_REQUIRED]
- [x] The segment vocabulary is queue-head, priority, parked-dependency, plans, exec-prompts, and ad-hoc, composing beside the bullet's existing tokens (`exec-plans-segment-first`, `exec-plans-segment-exhausted`, `mode-starved-bypass:<lane>`) unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Byte payment lands in the same change: decisions.md ends at or below its pre-change byte count of 99904 bytes (wc -c verified, the post-change count recorded beside the certification evidence; the file sits above its cap, so net growth is forbidden) [class: REPOSITORY_TEST]
- [x] The payment source is the Exec-mode selection rule bullet itself: the Ordering contract sentence the pin replaces, the parked-dependency/fresh-plan carry-over sentence ("D1's selection priorities carry into the merged set..."), plus any further sentence in the same bullet whose content duplicates D1's own text [class: REPOSITORY_TEST]
- [x] The payment keeps the consumer-urgency promotion clause and the D1 cross-reference phrase, the budget gate reports no new ratchet breach line beyond the pre-change baseline of three, and the grep needle `grep -c "selection-order:" agents/skills/maintenance/decisions.md` returns at least 1 [class: REPOSITORY_TEST]

### Task 3: Validation and changelog

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/CHANGELOG.md`

Primary class anchors:
- `CHANGELOG` in `agents/skills/maintenance/CHANGELOG.md`

- [x] One dated 2026-11-13 entry cites this plan, names the shared lane-state surface and the pinned ordering, and carries the once-per-slot witness citations: the 2026-11-12 20:50 and 21:50 race slots, the 22:50 divergent-rationale slot, and the 2026-11-13 01:51 empty-lane slot [class: IMPLEMENTATION_REQUIRED]
- [x] Run python3 scripts/skill_text_budget.py --check and record OUTCOME: pass with the ratchet breach count at or below the pre-change baseline of three [class: REPOSITORY_TEST]
- [x] Run bash scripts/check_maintenance_pins.sh (both edited skill files are pinned) and record exit 0 [class: REPOSITORY_TEST]
- [x] Run the hygiene scan from public_hygiene_scan_script in the user facts document over the changed files; exit 0 [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-13-twin-slot-carrier-fixed-overhead-waste.md`: completed by Tasks 1-3. Task 1 landed the survey-result lane-state sharing arm in `agents/skills/maintenance/survey-arms.md` (writer, reader, freshness keys, take-time re-checks unchanged); Task 2 pinned the exec selection ordering to one tie-broken chain with the `selection-order:<segment>` token in `agents/skills/maintenance/decisions.md`, byte-paid inside the same file; Task 3 landed the dated witness citations in `agents/skills/maintenance/CHANGELOG.md`. The origin row is folded here and deleted in the archive commit. One non-blocking Low residual from the execution code review r2 (revisions-ledger top-block date order) is deferred to `docs/history/backlog/2026-11-19-twin-slot-changelog-date-order-residual.md` with its owner named there.
