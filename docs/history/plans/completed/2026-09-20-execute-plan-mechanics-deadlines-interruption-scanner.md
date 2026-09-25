# Plan: execute-plan mechanics: deadlines, interruption recovery, scanner robustness

Origins (scope of record, under `docs/history/backlog/`):

- `2026-09-17-execute-plan-worker-deadline-contract.md` (HIGH)
- `2026-09-17-execute-plan-interruption-root-cause-inventory.md` (HIGH)
- `2026-09-17-r5-review-exit-residuals.md`
- `2026-09-17-checkbox-scanner-alternate-markers.md`
- `2026-09-17-fence-robust-checkbox-scanning.md`
- `2026-09-16-em-dash-insertion-scope-check.md`

Review artifacts: `docs/reviews/2026-09-20-plan-review-execute-plan-mechanics-deadlines-interruption-scanner-r<N>.md` (glob; one per round from r2 on; the r1 record ran under the short-slug filename before the slug fold).

## Terms

- Machine manifest: the driver-owned `runtime_state.json` (schema_version, tasks, claims, checkpoints, history, workflow_state).
- Claim / launch record: a task's durable execution lease (token, generation, owner, state, timestamp).
- Worker-result envelope: the JSON the caller passes to `--operation checkpoint --input`; the adapter's normalized host result uses the same reason-code vocabulary.
- Cross-runtime baseline: the launch/wait deadline values pinned in `agents/skills/execute-plan/package-manifest.toml` and named by `runtime-contract.md`.
- Capacity receipt: a validated worker result carrying reason code `capacity-unavailable`.
- waiting-capacity: the new claim state a capacity receipt parks a single-task claim in, with a bounded retry policy reusing the standard retry_policy shape.
- Terminal-refused event: the history event the terminal stage appends on each refusal, the history producer the diagnose classifier keys on for the terminal-gate class.
- Diagnose operation: the read-only `--operation diagnose` that walks manifest history and names the first failed transition and its classification.
- Line-anchored predicate: the checkbox reading where a line counts only when its first non-whitespace token is an unchecked task-list marker.
- Line-anchored evidence pin: the `line <N>:` evidence fragment produced from the scan helper's walk number, never from re-searching text.
- Fence map: the new whole-plan per-line fence-state table (backtick and tilde fences, CommonMark opening/closing rules) shared by the plan-scanning helpers.
- Added-lines mode: the new `check-no-em-dash.sh added-lines [--base REF]` command that scans only git-diff added lines.
- Bounded read: the shared `_read_plan_bounded` policy (safe path, regular file, byte-capped read).

## Assumptions

- The six origin files are the scope of record; every quoted span, line number, and quantity below was re-derived against the tree on 2026-09-20 (probes recorded in `docs/tmp/plan-requirements-execute-plan-mechanics.md`) and is re-derived again at execution by Task 1; basis: task constraint plus the three-executions caution (the driver surface executed three times after these origins were written).
- The interruption inventory's five referenced sub-items (`interrupted-task-ownership-recovery`, `conditional-readiness-gate`, `review-evidence-and-manifest-gate`, `terminal-completion-integrity`, `archive-before-task-completion`) are completed under `docs/history/backlog/completed/` and own their matrix rows; this plan closes only the drift-verified open rows and maps the landed rows in Gist; basis: the completed/ directory contents and driver probes (zero capacity state, no first-failed-transition diagnostic, `record_done` already requires non-empty log evidence).
- Task 1 stands down when a peer session holds the driver, test, contract, manifest, script, or backlog-item surfaces dirty; basis: repo parallel-session practice and the live peer edit of the interruption inventory item.
- The `waiting-capacity` mechanism keys on a provider-neutral reason code carried by the worker-result envelope; the driver never pattern-matches host output; basis: the contract's Codex adapter boundary keeps provider specifics out of the driver.
- The terminal archived-plan scan stays fence-blind by spec after the fence map lands; basis: the origin's own disposition and the contract's terminal backstop sentence.
- The em-dash legacy counts (`validate_review_staging.py` 23, `summarize_review_stats.py` 5) were re-verified on 2026-09-20; the added-lines mode gates insertions only and never sweeps those files whole; basis: origin plus today's grep.
- The lessons corpus mention of `TERMINAL_PLAN_READ_LIMIT` (one line in `projects/.ai-playbook/development_lessons.md`) is historical record and is not edited by the rename; basis: lessons are append-only history and the file is peer-dirty in the authoring session.
- Task 6's comment-id strip re-checks the certified sibling plans (`docs/plans/completed/2026-09-19-execute-plan-driver-residuals-batch-2-phase-*.md`) for pinned round-id literals before stripping; where a sibling pin collides, that comment keeps its id and the residual is recorded; basis: sibling plans are certified and their drift gates re-derive at their own execution.

Decision points requiring a grill: inventory arm scope: drift-scoped closure (capacity wait plus diagnose; landed rows mapped, not re-implemented), source: five completed sub-items plus driver probes plus the inventory's own keep-the-normal-path-simple rule, 2026-09-20, Gist and Tasks 3-4; deadline numbers: cross-runtime baseline launch 900 / wait 1500 with in-code defaults raised to match, source: origin's "not 30 seconds or five minutes" plus the driver lease comment's 20-minute worker budget plus standing pre-authorization, 2026-09-20, Task 2; capacity mechanism: envelope reason code `capacity-unavailable` drives the `waiting-capacity` claim state with bounded retry, source: contract provider-neutral boundary, 2026-09-20, Task 3; log-enforcement row: disposition landed (`record_done` log evidence requirement plus prose append semantics), source: driver probes, 2026-09-20, Gist mapping; CC5-2 shape: refuse whitespace-only and require at least one task heading at terminal, source: origin recommendation, 2026-09-20, Task 5; widening keeps the line-anchored predicate and stable evidence pins, source: origin text, 2026-09-20, Task 7; fence map applies to the readiness scan family only, terminal stays fence-blind, source: origin disposition, 2026-09-20, Task 8; em-dash mode: `added-lines [--base REF]` over added diff lines, all extensions, source: origin suggested fix, 2026-09-20, Task 9; timeout-recovery pin shape: the session-less launch expiry pins rotated-exactly-once with no duplicate claim row (matching the driver's deliberate rotation semantics for that shape), source: review r1 F1 code verification, 2026-09-20, Task 2; diagnose sourcing: inclusion rides `precondition-unverified` blocked receipts already in history, terminal-gate rides the new terminal-refused event the terminal refusal tail writes, user-interruption rides the existing `user-interrupt-recorded` event, cancellation classifies under the timeout, worker-failure, and cleanup-unverified codes its receipts already carry, source: review r1 F2 producer verification and review r2 F2 cleanup-unverified arm, 2026-09-20, Task 4; group-member capacity receipts keep the existing blocked claim shape so the group path owns recovery and the group fences stay untouched, source: review r1 F5 options plus the simplicity invariant, 2026-09-20, Task 3; readiness routes a `waiting-capacity` claim at the queue head to recovery with `preserve-and-reconcile` through the unprovable-next-task condition (the parked task is not claimable), no condition-text change, source: review r1 F9 recommended option refined by review r3 F2 queue-head verification, 2026-09-20, Task 3.

## Design Invariants (CR Guard)

- Provider-neutral driver: host command shapes, envelopes, and deadlines stay in `scripts/execute_plan_runtime_codex.py`; the driver sees only the normalized schema. No task may move provider detail into the driver or skill prose.
- Deadlines are owned by the runtime package: finite, positive, configurable only through the package manifest keys; no environment variable or CLI flag override is introduced.
- Fail-closed gates: every refusal leaves the manifest untouched and names the failed check; a refused operation is retriable through its documented recovery action. The one exception this plan introduces is the terminal refusal tail's history append, which is an evidence write ordered after the refusal outcome is composed and never changes the outcome.
- The manifest lock fences machine state only; no task may claim the lock fences external artifacts (the archived plan file, commits).
- History is append-only: new driver events extend `history`, never rewrite it; the diagnose operation is read-only.
- Keep the normal path simple (inventory required implementation 7): one new claim state, one new history event, and one read-only operation are the only state-machine additions; anything beyond is a backlog item, not a new recurring gate.

## Gist & Examples

Six origins, one mechanics pass over the execute-plan runtime. Each cluster below names its drift state so no landed work is re-implemented.

1. **Deadlines cover the worker contract (origin 1).** The contract already documents a cross-runtime baseline pinned in the package manifest (`launch_deadline_seconds = 900`, `wait_deadline_seconds = 300`, landed as r3 F20), but two defects remain. First, the wait baseline is five minutes, which is exactly the arbitrary short default the origin names: the driver's own lease comment sizes `CLAIM_LEASE_SECONDS` against a 20-minute per-worker budget, so an ordinary long worker or review panel is still terminated at the baseline. Second, the in-code adapter defaults (30 s launch, 300 s wait) contradict "the normal defaults must cover the actual contract". The baseline becomes launch 900 / wait 1500 (25 minutes, finite and bounded, above the 20-minute budget), the in-code defaults rise to the same values, and the missing witnesses land: a test pinning the shipped baseline against the contract sentence, a legitimate 20-minute wait that must not time out, evidence preservation on a real bounded timeout, a timeout-versus-malformed contrast, and a recovery pin showing a launch-deadline expiry is reconciled through the claim machinery exactly once, with the dead attempt's claim rotated and no duplicate claim row created.
2. **Interruption inventory (origin 2), drift-scoped.** Most matrix rows already landed through the five completed sub-items and executed plans; the mapping table below is the disposition of record. Two rows are still open in the driver: temporary capacity loss (no durable waiting state exists; zero `capacity`/`waiting-for`/`quota` hits in the driver) and the compact first-failed-transition diagnostic (only predecessor-ref diagnostics exist). This plan closes exactly those two rows: a `waiting-capacity` claim state driven by a provider-neutral `capacity-unavailable` envelope reason code with a bounded retry policy and in-place resume for single-task claims (group members keep the existing blocked shape so the group path owns recovery), and a read-only `diagnose` operation that names the first failed transition and classifies it (timeout, capacity-unavailable, worker-failure, stale-evidence, inclusion, terminal-gate, user-interruption, none).
3. **R5 residuals (origin 3), all still present.** The do-first hardening pair lands as prescribed: `_read_plan_bounded` loses its check-then-open window (open with `O_RDONLY|O_NONBLOCK|O_CLOEXEC`, `fstat` the descriptor, require a regular file before any read), and the terminal empty-artifact refusal stops accepting whitespace-only or sectionless archived plans (strip-based emptiness plus an at-least-one-task-heading requirement mirroring readiness). The reclaim fence extends from `aborted` to the full closed set (`aborted`, `complete`, `terminal`). The test pins (T5-1 through T5-4, R5-4), the doc-precision set (CD5-1 through CD5-5), and the polish set (DS5-1 through DS5-4, R5-5) land in the same pass.
4. **Checkbox widening (origin 4).** The single predicate site gains `* [ ]` and `+ [ ]` while keeping the line-anchored reading; all three consumers (terminal whole-file scan, pre-archive mirror, readiness per-section agreement) flow through that one helper. The contract's terminal predicate and readiness wording are updated in the same change, and the `line <N>:` evidence pins stay stable.
5. **Fence map (origin 5).** The single-level backtick parity toggle is replaced by a whole-plan CommonMark-grade fence map (backtick and tilde fences, closing fence same character and at least the opening width, bare closing lines, 0-3 space indent tolerance, unclosed fence open to end of file) shared by the section extractor and the task-heading search. The fenced pseudo-heading hijack stops being a documented residual and becomes a fixed, tested behavior; per-section parity restart disappears; the terminal backstop stays fence-blind by spec.
6. **Em-dash insertion scoping (origin 6).** `check-no-em-dash.sh` gains `added-lines [--base REF]`: a git-diff scan over added lines only, all extensions, so the two large validators with legacy em-dashes get insertion-scoped coverage instead of being excluded from gates entirely. The default base stays `HEAD`, so the mode gates working-tree insertions at authoring time; re-scanning already-committed insertions remains out of scope by design (the origin's own framing). Authoring-time simulation: from the parent of the validator's first-add commit (02348755), the added-lines pipeline yields exactly 23 U+2014 lines, matching the legacy count.

**Inventory cause-to-owner mapping (origin 2 disposition of record):**

| Inventory cause row | Disposition | Evidence |
|---|---|---|
| Deadline shorter than worker contract | This plan, Task 2 (baseline landed as r3 F20) | contract deadline paragraph; package-manifest.toml |
| Temporary capacity loss | This plan, Task 3 | zero `capacity` hits in the driver |
| Partial or fallback review | Landed in the driver; residuals item open | driver preserves non-clean reason codes; completed `2026-09-18-execute-plan-residual-acceptance-exit-for-review-loops.md`; residual findings tracked in the open item `2026-09-15-execute-plan-efficiency-plan-review-residuals.md` |
| Plan, manifest, claim, or digest drift | Landed | completed `conditional-readiness-gate` and `review-evidence-and-manifest-gate` items; digest-gated readiness in the driver |
| External work in task checklists | Landed | completed `scope-and-release-gate-separation` item |
| Missing or overwritten preceding logs | Landed (driver side) plus skill prose | `record_done` requires non-empty log evidence and stores `done_log_evidence`; SKILL.md append rules; agent-logs.md write semantics |
| Premature terminal response or archive | Landed | completed `terminal-completion-integrity` and `archive-before-task-completion` items; pre-archive gate |
| User input interrupts a wait | Landed | completed `interrupted-task-ownership-recovery` item; owner/token fences in the resume path; `user-interrupt-recorded` history event |
| Clarification mistaken for an abort | Landed | same ownership item; skill prose treats questions as non-terminal input |
| Readiness gate repeats on stable state | Landed | completed `conditional-readiness-gate` item |
| External work executable by implication | Landed | completed `scope-and-release-gate-separation` item |

Required-implementation rows 1 (state table), 3 (contract-owned deadlines), 4 (fallback coverage), 5 (terminal fail-closed), and 7 (simple normal path) are satisfied by the landed state machine plus this plan's two additions; row 2 (deterministic tests per cause) is carried by Tasks 2 through 5; row 6 (diagnostic report) is Task 4.

## Evaluation Criteria

**Quality dimensions:**

- Correctness: every origin defect named above has a witness with an honestly stated pre-fix expectation (a RED gate for behavior the change fixes, an explicit regression-pin label for behavior already correct); the full driver and codex suites stay green.
- Doc-code parity: every changed contract sentence describes behavior verified in the driver; each doc obligation gets its own dedicated probe that fails when that obligation is deleted.
- Simplicity: exactly one new claim state, one new history event, and one read-only operation; no new recurring gates; no provider detail in the driver; the parked claim's retry policy reuses the standard retry_policy shape.
- Hygiene: no em-dash in authored prose; no review-round-id comments left in the two code files; public hygiene scan exits 0; `plan_readiness.py` exits 0 on this plan.

**Done when:**

- `( cd scripts && python3 -m unittest test_execute_plan_runtime test_execute_plan_runtime_codex )` passes including every new witness.
- `python3 scripts/plan_readiness.py docs/plans/2026-09-20-execute-plan-mechanics-deadlines-interruption-scanner.md` exits 0.
- The six origins' defects are closed with the witnesses listed in Tasks 2 through 9, and the origin backlog items are still in place under `docs/history/backlog/` (they move to `completed/` only at plan completion).

**Ship when:**

- Peer sessions holding the same driver surfaces (the certified batch-2 phase plans) rebase and re-run their own drift gates against the landed hunks; this is a human-coordinated handoff, not an executable task.
- The interruption inventory item's residual acceptance criteria are re-checked against the landed state at execution review; anything still open becomes a backlog item rather than a gate.

## Review Scope

**Explicit must-fix; findings on these paths are always in scope (review and fix if valid):**

**Production code:**

- `scripts/execute_plan_runtime.py` (partially in scope: the methods and constants named by Tasks 2 through 8; all other methods are frozen; reject any review finding that touches frozen methods and track real frozen-region bugs as separate backlog notes)
- `scripts/execute_plan_runtime_codex.py` (deadline defaults and timeout evidence path only; frozen elsewhere)
- `scripts/runtime_capabilities.py` (narrowly: the `REASON_CODES` closed set gains `capacity-unavailable` and nothing else; frozen elsewhere)
- `scripts/check-no-em-dash.sh` *(the added-lines mode and usage text only)*
- `agents/skills/execute-plan/package-manifest.toml` (the `[adapters.codex]` deadline keys only)
- `agents/skills/execute-plan/runtime-contract.md` (partially in scope: the deadline paragraph, terminal predicate sentence and its empty-plan wording, readiness condition 4 wording and fence paragraph, reclaim/abort sentences, claim-state and reason-code lists, the Transition table's capacity row and preamble sentence, the new diagnose subsection; all other sections are frozen)

**Tests:**

- `scripts/test_execute_plan_runtime.py` (existing tests named by the tasks plus new witnesses; unrelated tests frozen)
- `scripts/test_execute_plan_runtime_codex.py` (deadline and timeout witnesses; unrelated tests frozen)

**Plan-related extension;** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `docs/history/backlog/**`; reason: origin items move to `completed/` at plan completion per the lifecycle and are never edited by tasks.
- `projects/.ai-playbook/development_lessons.md`; reason: peer-modified lessons corpus, learn-class gated, historical mentions stay.
- `README.md`; reason: verified to carry no sentences consuming the changed surfaces.
- `docs/plans/2026-09-19-no-silent-gate-satisfying-prose-rewrites.md`, `docs/plans/2026-09-19-scheduler-ops-contract-fix.md`, `docs/plans/2026-09-19-scheduler-ops-lanes-durability.md`; reason: peer-session drafts, foreign files.
- `docs/reviews/**`; reason: review artifacts, produced by the review loop, never edited by tasks.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"

# Full hermetic suites (driver + codex adapter; unittest, run from scripts/ so the flat imports resolve)
( cd "$REPO/scripts" && python3 -m unittest test_execute_plan_runtime test_execute_plan_runtime_codex )

# Mechanical readiness gate on this plan
( cd "$REPO" && python3 scripts/plan_readiness.py docs/plans/2026-09-20-execute-plan-mechanics-deadlines-interruption-scanner.md )

# Public hygiene scan (anchored; scanner resolves its root from cwd)
( cd "$REPO" && bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" )

# Em-dash policy over the authored prose files (plan and contract).
# The two legacy validators are excluded here by design; their insertions are gated by the added-lines mode.
( cd "$REPO" && bash scripts/check-no-em-dash.sh file docs/plans/2026-09-20-execute-plan-mechanics-deadlines-interruption-scanner.md agents/skills/execute-plan/runtime-contract.md )

# Em-dash policy over the authored non-prose surfaces (manifest deadline keys, script usage text):
# file mode silently skips non-prose extensions, so this arm sets CHECK_NO_EM_DASH_ALL=1 explicitly.
( cd "$REPO" && CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file agents/skills/execute-plan/package-manifest.toml scripts/check-no-em-dash.sh )

# Added-lines mode hermetic fixture: fires only on inserted em-dashes, passes when the working tree's
# added lines are em-dash-free (including an added clean line, so a context-scanning implementation
# fails the second arm). Teardown is failure-safe via EXIT trap; nothing leaks outside the temp dir.
( cd "$REPO" && tmp="$(mktemp -d)" && trap 'rm -rf "$tmp"' EXIT && git init -q "$tmp/repo" && cd "$tmp/repo" \
  && printf 'legacy line with \xe2\x80\x94 dash\nclean context line\n' > v.py && git add v.py && git -c user.email=t@t -c user.name=t commit -qm base \
  && printf 'legacy line with \xe2\x80\x94 dash\nnew line with \xe2\x80\x94 dash\n' > v.py \
  && if bash "$REPO/scripts/check-no-em-dash.sh" added-lines ; then echo "FAIL: added-lines did not fire on inserted dash"; exit 1; fi \
  && printf 'legacy line with \xe2\x80\x94 dash\nedited clean context line\n' > v.py \
  && if ! bash "$REPO/scripts/check-no-em-dash.sh" added-lines ; then echo "FAIL: added-lines fired on clean added line"; exit 1; fi )
```

### Task 1: Phase 0 drift gate (re-derive every pin before any edit)

Files:

- (read-only gate; no file edits)

- [x] Re-derive every quoted span, line number, count, and value in this plan against the current tree (`_read_plan_bounded` open path, the terminal and readiness empty-refusal predicates at their then-current lines, the reclaim workflow-state fence, the checkbox predicate, the fence-tracking block, the manifest deadline keys, the in-code adapter defaults, the legacy em-dash counts); where any pin moved, update this plan in the same task before any code edit [class: REPOSITORY_TEST]
- [x] Re-probe the pinned behaviors live, not by absence-grep: run the current `_read_plan_bounded` against a directory fixture to confirm the refusal fragment; run the em-dash added-lines simulation from the validator first-add parent and confirm 23 hits; parse `package-manifest.toml` and confirm the shipped deadline keys [class: REPOSITORY_TEST]
- [x] Drift-check the interruption inventory origin file's working-tree text (a peer session edits it live): re-read it immediately before authoring-close and record any scope change against Tasks 2 through 4 [class: REPOSITORY_TEST]
- [x] Stand-down check: if `git status --porcelain` shows the driver, test, contract, manifest, em-dash script, or any origin backlog file dirty from a peer session, stop and report instead of editing [class: REPOSITORY_TEST]
- [x] Grep the certified sibling plans for round-id literals pinned in their validation commands (`grep -nE "r[0-9] ?(F|R|T|DS|CD|CC)[0-9]" docs/plans/completed/2026-09-19-execute-plan-driver-residuals-batch-2-phase-*.md`) and record any collision with Task 6's strip set; colliding comments keep their ids [class: REPOSITORY_TEST]

### Task 2: Deadline baseline alignment (origin: worker-deadline-contract)

Files:

- `scripts/execute_plan_runtime_codex.py`
- `agents/skills/execute-plan/package-manifest.toml`
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/test_execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime_codex.py`

RED scope: only the baseline pin, the omitted-keys pin, and the long-wait witness fail before this task's edits; the bounded-timeout, distinct-reason, and recovery-reconciles witnesses pin behavior the adapter and driver already exhibit and are added as regression pins per the origin's follow-ups (they stay green before and after).

- [x] `test_package_manifest_pins_cross_runtime_baseline`; given the shipped `package-manifest.toml` `[adapters.codex]` block parsed the way `test_package_manifest_ambient_read` parses it, expects `launch_deadline_seconds == 900` and `wait_deadline_seconds == 1500`, and expects `runtime-contract.md` to contain a baseline sentence naming both values [class: REPOSITORY_TEST]
- [x] `test_omitted_manifest_keys_fall_back_to_contract_baseline`; given a manifest document whose `[adapters.codex]` block omits both deadline keys, expects the constructed adapter's `launch_deadline == 900.0` and `wait_deadline == 1500.0` [class: REPOSITORY_TEST]
- [x] `test_legitimate_long_wait_within_deadline_completes`; given a fake runner whose wait consumes 1200 simulated seconds of an injectable clock, constructed through the in-code default deadlines (no explicit `wait_deadline` argument, no temp manifest) so the RED expectation is deterministic, expects a success receipt and never a timeout [class: REPOSITORY_TEST]
- [x] `test_bounded_timeout_preserves_evidence` (regression pin); given a real deadline expiry at `deadline_seconds=0.01`, expects the blocked receipt's evidence to name the deadline exceeded and carry the owned-process handle representation, with the verified-timeout arm yielding reason `timeout` and the unverified arm yielding `cleanup-unverified` with retry mode `none` [class: REPOSITORY_TEST]
- [x] `test_timeout_receipt_distinct_from_malformed_result` (regression pin); given two runs over the same argv where the runner times out in arm A and returns malformed JSON in arm B, expects reason codes `timeout` and `malformed-result` respectively from the same translation path [class: REPOSITORY_TEST]
- [x] `test_timeout_recovery_reconciles_without_duplicate_claim` (regression pin); given a launch deadline expiry recorded on a claim and a subsequent continue on the same task, expects the session-less dead attempt's claim rotated exactly once (state `replaced`) and exactly one live claim row for the task afterwards, never a duplicate claim [class: REPOSITORY_TEST]
- [x] Run → expect RED for exactly the baseline, omitted-keys, and long-wait witnesses and GREEN for the three regression pins [class: REPOSITORY_TEST]
- [x] Raise `DEFAULT_LAUNCH_DEADLINE` to `900.0` and `DEFAULT_WAIT_DEADLINE` to `1500.0` in the codex adapter; set `wait_deadline_seconds = 1500` in `package-manifest.toml` [class: IMPLEMENTATION_REQUIRED]
- [x] Update `test_package_manifest_ambient_read`'s absent-var branch default literals and its rationale comment to the new contract baseline in the same commit, keeping the pin's intent that default drift fails the assertion [class: IMPLEMENTATION_REQUIRED]
- [x] Update the contract deadline paragraph: the cross-runtime baseline is launch 900 / wait 1500, the in-code defaults equal the baseline and apply only when a manifest omits the keys, profiles may still only set finite positive values, and the wait baseline is sized to cover a legitimate 20-minute worker body of work (same rationale as the reclaim lease comment) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the full suite passes [class: REPOSITORY_TEST]
- [x] Commit: `feat: align execute-plan adapter deadlines with the worker contract` [class: IMPLEMENTATION_REQUIRED]

### Task 3: waiting-capacity durable state (origin: interruption-root-cause-inventory, cause row 2)

Files:

- `scripts/execute_plan_runtime.py`
- `scripts/runtime_capabilities.py` (the `REASON_CODES` closed set only)
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`

- [x] `test_capacity_receipt_parks_claim_waiting_capacity`; given a validated worker receipt with reason code `capacity-unavailable` on a single-task claim, expects the claim state `waiting-capacity` carrying the standard retry-policy shape (`mode: bounded-resume`, `max_attempts: 3`, `attempts_remaining: 3`; the resume action is carried by the outcome's `recovery_action`, no `next_action` key) and a `worker-blocked` history event with that reason code [class: REPOSITORY_TEST]
- [x] `test_waiting_capacity_claim_resumes_in_place`; given a continue on a task whose claim is `waiting-capacity` with retry budget remaining, expects the same claim token and generation on the new launch, never a second claim row or a reclaim rotation [class: REPOSITORY_TEST]
- [x] `test_capacity_retry_exhaustion_moves_claim_to_blocked`; given successive capacity receipts exceeding `attempts_remaining`, expects the claim state `blocked` (the existing reclaimable lease state) [class: REPOSITORY_TEST]
- [x] `test_waiting_capacity_claim_refuses_lease_reclaim`; given a `waiting-capacity` claim older than the claim lease, expects the reclaim refused with evidence naming `waiting-capacity` and the manifest unchanged (the state is deliberately outside `RECLAIMABLE_CLAIM_STATES` while its retry policy is live) [class: REPOSITORY_TEST]
- [x] `test_manifest_validator_accepts_waiting_capacity_state`; given a manifest whose claim state set includes `waiting-capacity`, expects schema validation to pass [class: REPOSITORY_TEST]
- [x] `test_group_member_capacity_receipt_keeps_blocked_shape`; given a capacity receipt on a live batch-group member, expects the member's claim to persist in the existing `blocked` shape with the capacity reason code recorded (the parking branch applies only to single-task claims; the group path owns member recovery and the group fences stay untouched) [class: REPOSITORY_TEST]
- [x] `test_readiness_routes_waiting_capacity_to_recovery`; given a manifest whose first incomplete task's claim is `waiting-capacity` (the parked task at the queue head), expects the readiness outcome to carry decision `recovery` with recovery action `preserve-and-reconcile` through the unprovable-next-task condition, and the manifest unchanged [class: REPOSITORY_TEST]
- [x] Run → expect RED: the new tests fail against the current seven-state claim vocabulary, the closed reason-code set, and the absent readiness routing [class: REPOSITORY_TEST]
- [x] Add `capacity-unavailable` to the `REASON_CODES` closed set in `scripts/runtime_capabilities.py` (nothing else in that file changes) [class: IMPLEMENTATION_REQUIRED]
- [x] Implement the parking branch in the blocked-receipt classification (single-task claims only), the `waiting-capacity` claim state in the manifest validator's claim-state set, the standard-shape bounded retry policy on the claim, in-place resume on continue/resume, exhaustion transition to `blocked`, and the reclaim refusal; the readiness routing falls out of the existing blocked-claim fencing once the parking branch keeps the task outside the claimable set; extend the history event with the same reason code [class: IMPLEMENTATION_REQUIRED]
- [x] Update the contract: claim-state list gains `waiting-capacity` with its retry policy and exhaustion rule; the recognized reason-code list gains `capacity-unavailable`; the Transition table gains a `capacity-unavailable` row (claim parks `waiting-capacity`, bounded retry, resume-same-claim next action); one sentence states that a `waiting-capacity` claim at the queue head routes readiness to recovery with `preserve-and-reconcile` through the unprovable-next-task condition (the parked task is not claimable; the condition text is unchanged), and one sentence states that capacity receipts on live batch-group members keep the blocked shape under the group path [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: durable waiting-capacity state for execute-plan claims` [class: IMPLEMENTATION_REQUIRED]

### Task 4: first-failed-transition diagnose operation (origin: interruption-root-cause-inventory, required implementation 6)

Files:

- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`

- [x] `test_diagnose_names_first_failed_timeout`; given a manifest whose history carries `started` then a `worker-blocked` event with reason `timeout` for an incomplete task, expects the diagnose outcome to name that event as `first_failed_transition` with classification `timeout` [class: REPOSITORY_TEST]
- [x] `test_diagnose_classifies_capacity`; given a `worker-blocked` history event with reason `capacity-unavailable`, expects classification `capacity-unavailable` [class: REPOSITORY_TEST]
- [x] `test_diagnose_classifies_worker_failure_and_stale_evidence`; given three manifests whose failure events are a `worker-blocked` receipt with reason `malformed-result`, a `worker-blocked` receipt with reason `stale-claim`, and a `worker-blocked` receipt with reason `cleanup-unverified` (the adapter's non-resumable unverified-kill arm, persisted to history), expects classifications `worker-failure`, `stale-evidence`, and `worker-failure` respectively [class: REPOSITORY_TEST]
- [x] `test_diagnose_classifies_inclusion`; given a `worker-blocked` receipt with reason `precondition-unverified` (the code already flows through the blocked-persist path), expects classification `inclusion` [class: REPOSITORY_TEST]
- [x] `test_diagnose_classifies_terminal_gate`; given a manifest where the terminal stage appended its terminal-refused event (the refusal tail's evidence write), expects classification `terminal-gate` with the event named [class: REPOSITORY_TEST]
- [x] `test_diagnose_classifies_user_interruption`; given a `user-interrupt-recorded` history event (the existing event type) as the earliest uncompleted failure, expects classification `user-interruption` [class: REPOSITORY_TEST]
- [x] `test_diagnose_clean_terminal_reports_none`; given a manifest with a terminal receipt and no failure events, expects `first_failed_transition` null and classification `none` [class: REPOSITORY_TEST]
- [x] `test_diagnose_is_read_only`; given any manifest, expects the manifest file's bytes identical before and after the operation (digest comparison) [class: REPOSITORY_TEST]
- [x] Run → expect RED: `--operation diagnose` is not a recognized operation, and the terminal refusal tail writes no history event yet [class: REPOSITORY_TEST]
- [x] Implement the read-only `diagnose` operation: walk history in order, report the earliest classifiable failure event whose task has not since reached a progressed terminal state, classify through the fixed map (timeout, capacity-unavailable, worker-failure, stale-evidence, inclusion, terminal-gate, user-interruption, none); `inclusion` keys on `precondition-unverified` blocked receipts, `terminal-gate` on the terminal-refused event, `user-interruption` on `user-interrupt-recorded`, `worker-failure` keys on `malformed-result`, `runtime-error`, `runtime-policy-unavailable`, and `cleanup-unverified` receipts; cancellation is not a separate class because its receipts already carry the timeout, worker-failure, and cleanup-unverified codes; never mutate the manifest [class: IMPLEMENTATION_REQUIRED]
- [x] Add the terminal-refused history append to the terminal refusal tail (a mutating operation; the outcome is composed first and the append never changes it) so the terminal-gate class has a real producer [class: IMPLEMENTATION_REQUIRED]
- [x] Update the contract with a `Diagnose operation` subsection: read-only, the classification enum, each class's producing event or reason code (worker-failure including `cleanup-unverified`), the first-failed-transition selection rule, and the note that cancellation and unverified cleanup classify under their receipts' timeout and worker-failure codes [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: first-failed-transition diagnose operation for execute-plan` [class: IMPLEMENTATION_REQUIRED]

### Task 5: R5 hardening pair, reclaim fence, and test pins (origin: r5-review-exit-residuals, hardening + pins)

Files:

- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [x] `test_read_plan_bounded_opens_nonblocking_and_fstats` (the RED gate for the rewrite); given a spy or stub on the file-open path, expects `_read_plan_bounded` to open with `O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC` and to `fstat` the descriptor requiring `stat.S_ISREG` before any read; this fails against the current `Path.open` implementation [class: REPOSITORY_TEST]
- [x] `test_read_plan_bounded_refuses_fifo_without_open` (refusal pin; passes on the unfixed tree and must stay green after); given (posix-conditional, `skipUnless(hasattr(os, "mkfifo"))`) a FIFO created with `os.mkfifo` inside a `mktemp -d` directory and removed in teardown, expects the identical not-a-regular-file refusal fragment before any blocking read [class: REPOSITORY_TEST]
- [x] `test_terminal_refuses_whitespace_only_archived_plan` (RED before this task); given an archived plan of only whitespace bytes, expects the terminal blocked receipt naming the empty-artifact check (the refusal becomes `not plan_text.strip()`, not zero-byte) [class: REPOSITORY_TEST]
- [x] `test_terminal_refuses_archived_plan_without_task_sections` (RED before this task); given a non-empty archived plan with no `### Task <N>:` heading, expects the terminal blocked receipt naming the missing task sections (mirroring the readiness shape guard) [class: REPOSITORY_TEST]
- [x] `test_reclaim_refused_under_complete_and_terminal_workflows` (RED before this task); given an expired lease claim on a non-progressed task under `workflow_state` `complete` and then `terminal`, expects the reclaim refused with evidence naming the workflow state and the manifest unchanged (the fence extends from `aborted` to the full closed set) [class: REPOSITORY_TEST]
- [x] Extend `test_readiness_refuses_plan_without_task_sections` (regression pin); given the same fixture, additionally expects `recovery_action == "stop-or-recovery"` (T5-2) [class: REPOSITORY_TEST]
- [x] In the reclaim evidence pin test: delete the tautological literal-vs-literal assertion (T5-3) and add the swap detector at the helper level, `assertNotIn("replacement_token=seed-old-token", lines)` alongside the existing `assertIn` pair on the redacted envelope forms; add one sentence forbidding any change to the envelope redaction (T5-1) [class: REPOSITORY_TEST]
- [x] `test_read_limit_boundary_pair_terminal` (regression pin, classification already correct today); given an archived plan of exactly 1,000,000 bytes and then exactly 1,000,001 bytes, expects the first to pass the bounded-read gate (never the over-limit refusal) and the second to be refused with the over-limit evidence (R5-4) [class: REPOSITORY_TEST]
- [x] `test_read_limit_boundary_pair_readiness` (regression pin); given a `--plan` file at exactly the limit and at limit plus one, expects the same accepted/refused pair on the readiness path [class: REPOSITORY_TEST]
- [x] Run → expect RED for exactly the open-spy, whitespace-only, sectionless, and reclaim-fence witnesses; the refusal, readiness, boundary-pair, and swap-detector pins stay green as stated [class: REPOSITORY_TEST]
- [x] Rewrite `_read_plan_bounded`'s open path: `os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)`, `os.fstat` the descriptor and require `stat.S_ISREG` before wrapping in `os.fdopen` for the byte-capped read; the exists/is_file pre-checks disappear (no check-then-open window at all); keep the safe-path policy, the refusal fragments, and the limit refusal [class: IMPLEMENTATION_REQUIRED]
- [x] Change both empty-refusal sites (terminal and pre-archive/readiness mirror) to `not plan_text.strip()` and add the terminal at-least-one-task-heading check with refusal evidence naming the check; update the method docstrings ("zero-byte" wording becomes empty-or-whitespace-only, plus the heading requirement) [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the reclaim workflow-state fence to `{"aborted", "complete", "terminal"}`: `aborted` keeps the explicit-abort outcome; `complete`/`terminal` return the same preserve-and-stop shape with evidence naming the state; update the docstring [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: harden execute-plan bounded read, terminal refusal, and reclaim fence` [class: IMPLEMENTATION_REQUIRED]

### Task 6: R5 contract precision and comment polish (origin: r5-review-exit-residuals, docs + polish)

Files:

- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`

- [x] CD5-1: reword the mark_terminal save sentence to state plainly that the manifest lock does not fence the external archived-plan and commit artifacts and that a refused terminal call is re-run once the named check passes; the "best-effort best-order" phrase disappears [class: IMPLEMENTATION_REQUIRED]
- [x] CD5-2: add the readiness scoping sentence: transient contention carries reason code `stale-claim` with recovery action `resumable-conflict`, with the decision carried in the `decision` field, matching the driver's contention outcomes [class: IMPLEMENTATION_REQUIRED]
- [x] CD5-3: the terminal-path bullet gains the clause that the manifest carries at least one task (matching `mark_terminal`'s empty-manifest refusal) [class: IMPLEMENTATION_REQUIRED]
- [x] CD5-4: the recovery-action mapping gains `stop-or-recovery` for a plan with zero recognizable task sections (matching the driver's mapping) [class: IMPLEMENTATION_REQUIRED]
- [x] CD5-5: the Transition table preamble gains the sentence: each outcome names exactly one next action; take that one action, then re-classify the state [class: IMPLEMENTATION_REQUIRED]
- [x] DS5-1: strip the plan text once inside `_read_plan_bounded` so both empty-refusal sites and the readiness decision consume stripped text [class: IMPLEMENTATION_REQUIRED]
- [x] DS5-2: reduce the bounded-read policy prose at the three call-site docstrings to one-line pointers into the helper docstring [class: IMPLEMENTATION_REQUIRED]
- [x] DS5-3: strip review-round identifiers from code comments in the driver and test files, keeping self-contained rationale; comments pinned by certified sibling plans keep their ids per the Task 1 collision record [class: IMPLEMENTATION_REQUIRED]
- [x] DS5-4: rename `TERMINAL_PLAN_READ_LIMIT` to `PLAN_READ_LIMIT` everywhere it appears in the driver and the driver test file (the codex test file carries zero references); Task 1 re-derives the exact count; the lessons-corpus mention stays historical [class: IMPLEMENTATION_REQUIRED]
- [x] R5-5: document in the scan helper's docstring that evidence line numbers count `splitlines()` boundaries, which differ from `\n` splits on Unicode line separators; no behavior change [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: full suite passes after the rename and comment edits [class: REPOSITORY_TEST]
- [x] Dedicated probes (each in the final validation sweep, each failing when its obligation is deleted): the contract names `stale-claim` with `resumable-conflict` for contention; the terminal-path bullet carries the at-least-one-task clause; the mapping pairs `stop-or-recovery` with zero task sections; the Transition table preamble carries the exactly-one-next-action sentence; no `TERMINAL_PLAN_READ_LIMIT` remains in driver or tests [class: REPOSITORY_TEST]
- [x] Commit: `docs: execute-plan contract precision and comment hygiene` [class: IMPLEMENTATION_REQUIRED]

### Task 7: checkbox widening to all GFM task-list markers (origin: checkbox-scanner-alternate-markers)

Files:

- `scripts/execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/test_execute_plan_runtime.py`

- [x] `test_agreement_reports_star_marker_disagreement` (RED before this task); given a progressed task whose plan section contains an unchecked `* [ ]` line, expects the readiness agreement scan to report the disagreement through the count-only evidence text the readiness path emits for its plan-manifest condition (no line-number fragment: line pins live on the terminal and pre-archive scans; the dash-only predicate reports no disagreement for star lines today) [class: REPOSITORY_TEST]
- [x] `test_terminal_refuses_star_and_plus_markers` (RED before this task); given an archived plan containing an unchecked `* [ ]` line and then one containing `+ [ ]`, expects the terminal predicate to refuse in both cases with the `line <N>:` evidence fragment for the marker line (the terminal scan emits line-anchored evidence) [class: REPOSITORY_TEST]
- [x] `test_widened_marker_evidence_line_numbers_stable` (RED before this task, its fixture's first unchecked marker is a `* [ ]` line the dash-only predicate ignores); given a plan fixture where the first unchecked `* [ ]` sits at a known line number, expects the evidence pin prefix `line <known N>:` unchanged from the existing pin form [class: REPOSITORY_TEST]
- [x] `test_mid_prose_mention_still_ignored` (regression pin); given a section whose prose mentions the asterisk marker mid-line, expects no disagreement (the line-anchored reading is preserved) [class: REPOSITORY_TEST]
- [x] Run → expect RED for exactly the agreement, terminal star/plus, and evidence-stability witnesses (all three read star lines through the dash-only predicate today); the mid-prose pin stays green as stated [class: REPOSITORY_TEST]
- [x] Widen the single predicate site in `_unchecked_checkbox_pairs` to the three-marker form (first non-whitespace token one of dash, asterisk, plus, each followed by `[ ]`); every consumer inherits the widening through the helper [class: IMPLEMENTATION_REQUIRED]
- [x] Update the contract terminal predicate sentence and the readiness condition 4 wording to name the three markers under the same line-anchored reading; in the same edit update the empty-plan wording to empty-or-whitespace-only plus the terminal at-least-one-task-heading requirement for both the terminal and pre-archive mirrors (doc-code parity with Task 5's refusal changes); keep the fence-blind terminal sentence's meaning intact [class: IMPLEMENTATION_REQUIRED]
- [x] Dedicated probe (runs in the Task 10 sweep, failing when the obligation is deleted): the contract's terminal predicate sentence and readiness condition 4 wording each name the three markers `* [ ]` and `+ [ ]` alongside the dash form; the empty-plan wording names whitespace-only and the heading requirement [class: REPOSITORY_TEST]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: recognize all GFM task-list markers in execute-plan checkbox gates` [class: IMPLEMENTATION_REQUIRED]

### Task 8: CommonMark-grade fence map (origin: fence-robust-checkbox-scanning)

Files:

- `scripts/execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/test_execute_plan_runtime.py`

- [x] `test_fence_map_tilde_fence_hides_break_marker` (RED before this task); given a section whose `## `-style break marker sits inside a tilde-fenced block, expects the section extraction to run past it and the agreement scan to see checkboxes after the block [class: REPOSITORY_TEST]
- [x] `test_fence_map_nested_shorter_fence_does_not_close` (RED before this task); given a longer backtick fence containing a shorter backtick fence line and a tilde line, expects parity to hold until the matching closing fence [class: REPOSITORY_TEST]
- [x] `test_fence_map_unclosed_fence_fails_closed_for_later_sections` (behavior pin); given an unclosed fence in Task 1's body, expects Task 2's heading (inside the fence under whole-plan parity) to yield no scannable section and the readiness condition to fail closed naming Task 2, never to silently scan fenced content as prose [class: REPOSITORY_TEST]
- [x] `test_fence_map_indent_tolerance` (RED before this task for the four-space arm); given a fence opener indented three spaces it opens a fence, and given a fence-lookalike line indented four spaces it is literal text that toggles nothing [class: REPOSITORY_TEST]
- [x] `test_fence_map_fenced_pseudo_heading_does_not_hijack` (RED before this task); given a fenced pseudo-heading whose task number matches a manifest task ahead of the real heading, expects section extraction to bind to the real unfenced heading (the documented residual becomes fixed; rewrite the witness test that pinned the hijack) [class: REPOSITORY_TEST]
- [x] `test_fence_map_whole_plan_parity_not_per_section` (RED before this task); given a fence opened in Task 1 and closed after Task 2's heading, expects Task 2's extraction to treat its heading as fenced content and fail closed (no per-section parity restart) [class: REPOSITORY_TEST]
- [x] `test_terminal_backstop_stays_fence_blind` (regression pin); given an archived plan whose unchecked checkbox sits inside a fenced block, expects the terminal predicate to refuse (fence-blind by spec) [class: REPOSITORY_TEST]
- [x] Run → expect RED for exactly the tilde, nested-width, four-space-indent, pseudo-heading, unclosed-fence, and whole-plan-parity witnesses (the fence-blind heading search binds Task 2's real heading and scans fenced content as prose today, so the fail-closed expectation fails pre-fix); the fence-blind pin stays green as stated [class: REPOSITORY_TEST]
- [x] Implement `_plan_fence_map` over the whole plan's lines (backtick and tilde fences; opener run of three or more marker characters with an optional info string; closing line same character, at least the opening width, bare; indent tolerance of zero to three spaces; an unclosed fence stays open to end of file) and rewrite `_plan_task_section_lines` to consume it for both the heading search and the section walk [class: IMPLEMENTATION_REQUIRED]
- [x] Replace the contract's residual-fence paragraph with the CommonMark-grade description and drop the residual backlog pointer; the terminal fence-blind backstop sentence stays [class: IMPLEMENTATION_REQUIRED]
- [x] Dedicated probe (runs in the Task 10 sweep, failing when the obligation is deleted): the contract's readiness fence paragraph names tilde fences, nested widths of different sizes, unclosed fences, and the zero-to-three-space indent tolerance, and no sentence in the contract still points at the residual backlog item `2026-09-17-fence-robust-checkbox-scanning` [class: REPOSITORY_TEST]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: CommonMark-grade fence map for execute-plan plan scanning` [class: IMPLEMENTATION_REQUIRED]

### Task 9: insertion-scoped em-dash gate (origin: em-dash-insertion-scope-check)

Files:

- `scripts/check-no-em-dash.sh`

- [x] Implement the `added-lines [--base REF] [paths...]` command: `git diff -U0` (against `--base REF`, default `HEAD`) over the given paths or all tracked paths; scan added lines only for U+2014; report `file:new-file-line` per hit; exit 1 on any hit; git failures (exit status 2 or worse) abort non-zero instead of reading as clean; update the usage text [class: IMPLEMENTATION_REQUIRED]
- [x] Document in the usage text that the default base is `HEAD` (working-tree insertions at authoring time) and that re-scanning already-committed insertions is out of scope by design [class: IMPLEMENTATION_REQUIRED]
- [x] Run the hermetic fixture recipe from the plan's Validation Commands (fires on an inserted dash, passes on a clean added line with legacy content untouched, failure-safe teardown); expect it GREEN after this task's implementation [class: REPOSITORY_TEST]
- [x] Run the in-repo RED-today proof: `git diff -U0 02348755^ -- scripts/validate_review_staging.py | grep "^+" | grep -c "$(printf '\xe2\x80\x94')"` yields 23, matching the legacy count recorded at authoring time; record the observed number in the execution log [class: REPOSITORY_TEST]
- [x] Verify the consuming contracts: the two validators remain excluded from whole-file em-dash sweeps and are now covered by the added-lines mode; note the mode in the script usage text only (no README change; verified no consumer sentences exist) [class: REPOSITORY_TEST]
- [x] Commit: `feat: insertion-scoped em-dash gate for edited validators` [class: IMPLEMENTATION_REQUIRED]

### Task 10: final validation sweep

Files:

- (validation only; edits only to fix failures this sweep exposes)

- [x] Run the full Validation Commands block; expect all green (suite, readiness gate, hygiene, plan-and-contract prose em-dash, non-prose em-dash with CHECK_NO_EM_DASH_ALL=1, added-lines fixture) [class: REPOSITORY_TEST]
- [x] Run the Task 6 dedicated probes and the Task 7 and Task 8 contract-parity probes (each defined in its own task) as one fail-closed block; expect zero misses [class: REPOSITORY_TEST]
- [x] Confirm the six origin backlog items are still present and unmodified under `docs/history/backlog/` [class: REPOSITORY_TEST]
- [x] Commit (only if the sweep produced fixes): `test: execute-plan mechanics final validation sweep` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/completed/2026-09-17-execute-plan-interruption-root-cause-inventory.md: disposition folded into 2026-09-20-execute-plan-mechanics-deadlines-interruption-scanner.md (2026-09-25); per-item file deleted.
