# Backlog: code-review r1 non-blocking findings (agent-aware execute-plan contract)

Captured: 2026-09-22
Status: open
Priority: low
Origin: code review r1 (docs/reviews/2026-09-22-code-review-agent-aware-execute-plan-skill-contract-r1.md, sidecar .stats.json; verdict ready=yes, zero blocking) of branch 2026-09-22-execute-plan-agent-aware-runtime-reliability, executed plan docs/plans/2026-09-22-agent-aware-execute-plan-skill-contract.md. All four findings deferred to backlog under the pre-authorized review closeout (accept review suggestions; backlog-deferral default; no address pass ran in round r1). Source review round for every finding: code review r1, 2026-09-22.

## Finding F1 (Medium, non-blocking): executed-plan Task 2 gate line records a RED state the committed trail contradicts

File: docs/plans/2026-09-22-agent-aware-execute-plan-skill-contract.md, Task 2 run line (review anchors line 152).

One line: the checked Task 2 checkbox certifies that the shared-skill portability test "remains RED only on the `zcode` host-overlay term that Task 3 removes", but review r1's git inspection at 144cfd33, cd01f4e0, and 6f937a71 found zero forbidden terms in the four shared skill files, concluding the portability test was already GREEN at Task 2 and that the correction commit cb7144a0 replaced an accurate all-GREEN expectation with an inaccurate one.

Disputed premise (record both sides): three independent witnesses, the Task 1 implement worker, the Task 1 intermediate review, and the r5 re-cert reviewer, each observed the portability test RED exactly on "SKILL.md: zcode" between commits 144cfd33 and 39193c42, which contradicts F1's claim that the files were clean at 144cfd33. Both sides stand recorded here. The deferral itself is premise-independent: the final tree is GREEN and correct, so no shipped artifact or gate is wrong. Any future closure attempt must reconcile the two observations (for example by locating a working-tree or intermediate state that explains the observed RED) before amending the Task 2 gate line, rather than assuming either side is simply right.

Driving force: testability (the executed plan is the audit trail for the RED-to-GREEN sequence; a recorded gate state that cannot be re-derived from the committed bytes defeats a future auditor's re-derivation regardless of which side is correct).

## Finding F2 (Low, non-blocking): incident-obligation pin asserts against combined contract+profile text

File: scripts/test_runtime_capabilities.py (review anchors line 361).

One line: `ADAPTER_INCIDENT_OBLIGATIONS` markers are asserted against the normalized combined contract+profile text, so a future edit that strips the Codex profile's mirrored obligation and refusal prose (capacity-witness refusals, handoff owner-mismatch and replay refusals, non-resumable interruption state) leaves both the obligation pin and the coherence test green because the contract alone still carries every marker; review verified this with an executed flip probe in a temp copy. Suggested fix when picked up: assert each obligation marker set against the profile text separately (or per-home with an OR of exact homes), keeping the combined assertion as a floor.

Driving force: testability (the profile is the contract's named host-specific carrier; a mirror that can silently rot while the suite stays green is an unpinned obligation).

## Finding F3 (Low, non-blocking): profile-ownership pin misses inline prose re-assignments with drifted values

File: scripts/test_runtime_capabilities.py (review anchors line 408).

One line: the `REGISTRY_OWNED_PROFILE_FIELDS` no-assignment regex matches only line-start and table-row shapes and the value-copy check catches only exact registry values, so an inline prose restatement of a registry-owned field with a drifted value (for example a mid-sentence "the retry budget is 9") passes both ownership tests; review verified this with an executed flip probe in a temp copy. Suggested fix when picked up: add a per-field occurrence bound for registry-owned field names in profile prose, or extend the assignment shape to possessive prose forms ("the {field} is/are ...").

Driving force: testability (the exact drift the pin exists to refuse, a profile asserting capability values that disagree with the registry, survives in the most natural prose shape an editor would write).

## Finding F4 (Low, non-blocking): the profile-deferred bounded liveness window has no pinned value

File: agents/skills/execute-plan/runtime-adapters/codex.md (review anchors line 134).

One line: the neutral runtime contract's stalled-worker refusal and the execute-plan SKILL watchdog paragraph both key on "the profile's bounded liveness window", but the Codex profile references that window without defining it anywhere (the timeout hook pins `launch_deadline_seconds = 900` and `wait_deadline_seconds = 1500`, which are deadline baselines, not a heartbeat or liveness window), so an adapter implementer cannot compute "stalled" from the profile as written and the refusal witness is not machine-checkable for this runtime yet. Suggested fix when picked up: pin the liveness window in the profile's timeout hook, or state the derivation rule from the pinned deadlines; a natural landing spot is the separate runtime implementation plan.

Driving force: correctness (the boundary this plan documents is precisely "neutral core defers host values to the profile"; a deferred knob with no pinned value reproduces the under-specification the adapter-profile split was meant to eliminate).

## Why not fixed now

The r1 verdict (ready=yes, zero blocking) is the branch exit gate for the executed plan. All four findings are non-blocking. Any edit to the executed plan's certified bytes (F1) or to the pinned contract, profile, and test artifacts (F2 through F4) would change the certified digest and force a fresh review round on a tree that has already passed its exit gate, which the pre-authorized closeout declined to spend on Medium-and-Low residuals.
