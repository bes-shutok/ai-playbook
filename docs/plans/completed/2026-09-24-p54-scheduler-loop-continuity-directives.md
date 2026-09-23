# Plan: P54 scheduler loop-continuity directives

Backlog origin: docs/history/backlog/2026-09-24-scheduler-discharge-parked-intents-in-same-session.md (anchor; the seven companion origins are listed with dispositions in "Origins and dispositions" below)
Driving force: external (user directives: the 2026-09-24 discharge-parked-intents directive and the 2026-09-23 parallel-fleet-cap directive) + efficiency
Justification (non-principle force): the anchors are explicit user directives recording live losses (the loop went dark 2026-09-24 01:00 with the p50 execution and the 2026-09-25 carrier re-arm parked, recoverable only by a manual ask); park-triage would not take them because the directives are dated, witnessed, and dispatch-blocking (P54 must precede P50's dispatch).

## Terms

- **Scheduler state file**: `.ai-playbook/scheduler-state.json` (gitignored), the maintenance loop's durable state; schema 4; additive fields never bump the version.
- **Parked intents**: the `pending_rearm` and `pending_dispatch` state fields, each paired with an identity-bound payload copy under `docs/tmp/` per the park-path pairing rule.
- **Discharge duty**: the new default that any able session observing parked intents drains them in-session, guard-bound.
- **Able session**: a session whose automation create/update primitives demonstrably work (a successful echo earlier in the session, or a first-attempt success); verified with the child-side primitive precheck discipline before any mutating leg.
- **Execution queue / priority**: the new `execution_queue` and `execution_priority` state fields carrying the ordered executable-plan list and the standing user ordering directive.
- **needs-recert flag**: the selection-record mark that keeps a digest-drifted plan dispatchable with the execute-plan re-cert pre-step as its first task.
- **Fleet cap**: the repo-wide cap of 4 concurrent children (mixed kinds) replacing the per-lane single-occupancy guards; the execution lane holds at one in-flight child until P57 lands the isolation mechanisms (interim constraint, review r1 F1).
- **Execution claim file**: `docs/tmp/execution-claims/<plan-slug>.md`, the fired execution session's "am I first?" witness, mirroring the authoring claim duty.
- **Byte-parity blueprint protocol**: the two child blueprints in `agents/skills/maintenance/prompt-templates.md` carry pinned paragraphs; every blueprint edit is registered as an entry in that file's deviations list, and the byte-identical re-arm FIRST ACTION paragraphs are never edited.
- **Pins suite**: `scripts/check_maintenance_pins.sh`, the mechanical structural gate for the loop's invariants.
- **Shared-body scan**: `find_forbidden_shared_terms` in `scripts/test_runtime_capabilities.py`, case-insensitive with word-edge rules and no path exemption, over the four shared skill files.

## Assumptions

- assume one plan covers all eight origins; basis: the P53-P56 grouping plus the authoring payload naming the seven origins as one scope.
- assume the four out-of-tree origin files land byte-verbatim from peer commit 3667bf7d (three files) and detached commit 3c0af847 (fleet cap); basis: those commits hold their only committed forms.
- assume the shared-body RED fix shape is origin 7's option (a) rewording with no matcher change; basis: the origin's own recommendation (smaller blast radius) plus the matcher's verified case-insensitive no-exemption scan.
- assume deferred-low 2 (the em-dash parenthetical in the archived hygiene plan) is resolved-by-archive without editing the archived plan; basis: archived plans are immutable context.
- assume the needs-recert flag rides the `execution_queue` entries origin 2 introduces; basis: origin 4's "queue/selection record" wording composed with origin 2's queue field.
- assume park-first chaining supersedes the after-failure-only park timing; basis: origin 2's item 3 text.
- assume the execution claim file mirrors the authoring claim duty's gate-before-write order; basis: origin 3's "analogous to docs/tmp/authoring-claims/" wording.
- assume the fleet cap counts four repo-wide across mixed kinds while the per-turn per-lane dispatch limits and the merge-landing-lock serialization stand, with the execution lane held at one in-flight child until P57's isolation lands; basis: the directive text, the P57 coordination boundary, and review r1 F1's interim constraint (accepted under the standing pre-authorization), 2026-09-24.
- assume the execution blueprint's Phase 0 stays branch-based in this plan; the per-execution worktree dispatch default is P57's design rework; basis: the P57 origin's rework list and the grouping's coordination note.

Decision points requiring a grill: single-plan shape (decision: one plan for all eight origins; source: the origin items' own grouping accepted under the standing pre-authorization "accept all recommended options and suggestions", user directive 2026-09-24; affects: plan shape); out-of-tree origin landing (decision: land the four origin files byte-verbatim in Task 1; source: same standing pre-authorization over the only committed forms, 2026-09-24; affects: Task 1); option-a reword (decision: reword the two sentences, no matcher change; source: origin 7's recommended option under the same standing pre-authorization, 2026-09-24; affects: Task 7); resolved-by-archive disposition (decision: no edit to the archived hygiene plan; source: the archive-immutability convention under the same standing pre-authorization, 2026-09-24; affects: disposition ledger); needs-recert rides the queue (decision: the flag is a queue-entry and selection-record field; source: origins 2 and 4 composed under the same standing pre-authorization, 2026-09-24; affects: Tasks 3 and 5); park-first timing (decision: pre-create park, consumed on success; source: origin 2 item 3 under the same standing pre-authorization, 2026-09-24; affects: Task 3); execution-claim mirror (decision: gate-before-write order mirroring the authoring claim; source: origin 3 under the same standing pre-authorization, 2026-09-24; affects: Task 4); fleet-cap counting model (decision: repo-wide count of four across mixed kinds, per-turn per-lane limits unchanged; source: the directive text plus the P57 coordination note under the same standing pre-authorization, 2026-09-24; affects: Task 6).

## Gist & Examples

TLDR: the maintenance loop gains an able-session park-discharge duty, a durable execution queue with a standing priority directive, dispatch dedup with fire-time execution claims, needs-recert dispatchability for drifted plans, and a repo-wide four-child fleet cap, and the shared-body scan goes green, so parked work drains itself instead of waiting for a human.

Today the loop is lossy exactly where it can least afford it. When a fired session cannot emit automation creates (the clocked-primitives-absent wedge), it parks `pending_rearm` + `pending_dispatch` correctly, and then nothing obliges the next able session to drain that park: the intents wait for a next scheduled turn that may not exist (the 2026-09-24 01:00 dark loop held the p50 execution and the carrier re-arm hostage until a human asked). The execution chain dies with the child's own primitive loss ("successor chain FAILED: session lacks clocked primitives"), a user ordering directive dies with its one-shot carrier, two user-directed dispatches can fire simultaneously and collide, a digest-drifted plan silently drops out of dispatch eligibility, and the lane guards treat four idle-capable slots as one. Example of the new shape: a fired execution child finishes, sees `pending_dispatch` set plus its own working create primitive, dispatches the parked target through the normal Step 5 path, and clears the field in one targeted edit before ending; a digest-drifted plan dispatches flagged needs-recert and the PRE-STEP re-certifies it; authoring and audit children fill a repo-wide fleet of four while the merge landing lock serializes landings, and the execution lane stays single until P57 lands the per-execution isolation its directive demands.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every state-field addition appears in the schema block, the sanctioned-writer enumeration, and the Step 6 carry-forward list; the pins suite exits 0 after every task that touches pinned spans.
- liveness: the discharge duty, the queue, the dedup guard, and the needs-recert flag each carry a mechanical pins needle; no new silent-skip path is introduced (every skip records a reason).
- consistency: the capabilities suite exits 0 on the reworded shared bodies and keeps its vendor-name behavior witnesses; the deviations list carries an entry for every blueprint edit.
- hygiene: no em-dash in the plan bytes; the public-hygiene scan exits 0.

**Done when:**
- all task checkboxes are checked and the final validation block exits 0 end to end.
- `bash scripts/check_maintenance_pins.sh` exits 0 with the new needles registered.
- `PYTHONPATH=scripts python3 -m unittest scripts.test_runtime_capabilities` exits 0 (0 failures).
- the plan passes `python3 scripts/plan_readiness.py` on its final bytes with a ready=yes zero-blocking round.

**Ship when:**
- the next live scheduler turn dispatches under the fleet cap and a real dark-loop recovery discharges its park in-session (operational witnesses; observed behavior, not repo-checkable).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/SKILL.md` (Steps 1, 2, 3, 5, State file, Invariants, Execution-lane concurrency stance, Revisions)
- `agents/skills/maintenance/zcode.md` (Child dispatch ladder, Child classification markers)
- `agents/skills/maintenance/prompt-templates.md` (deviations list + both blueprint bodies)
- `agents/skills/plans/SKILL.md` (one sentence region only: the suppression-risk sentence in the budget-gate pause protocol; all other content frozen)
- `agents/skills/execute-plan/SKILL.md` (one sentence region only: the suppression-risk sentence in the pause-protocol step 3; all other content frozen)
- `scripts/check_maintenance_pins.sh`
- `docs/history/backlog/2026-09-23-scheduler-execution-queue-and-durable-priority-directive.md` *(new on main)*
- `docs/history/backlog/2026-09-23-user-directed-dispatch-dedup-guard.md` *(new on main)*
- `docs/history/backlog/2026-09-23-d1-recert-drift-flag-instead-of-silent-skip.md` *(new on main)*
- `docs/history/backlog/2026-09-23-parallel-fleet-cap-four-children.md` *(new on main)*
- `docs/history/backlog/2026-09-22-dirt-gate-staged-deletion-edge.md` (Task 8 move; destination `docs/history/backlog/completed/2026-09-22-dirt-gate-staged-deletion-edge.md`)
- `docs/maintenance/document-registry.md` (routing rows only)

**Tests:**
- pins-suite needles live in `scripts/check_maintenance_pins.sh` (listed above)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/plans/completed/2026-09-21-scheduler-maintenance-loop-quality-hygiene.md`; reason: archived plan, immutable context; the deferred-low 2 disposition is recorded, not edited.
- `scripts/runtime_capabilities.py` and `scripts/test_runtime_capabilities.py` matcher logic; reason: origin 7 option (a) forbids a gate-contract change; only suite EXECUTION is in scope.
- `docs/plans/deferred/` and `docs/plans/completed/` content beyond the registry rows this plan's routing writes; reason: owned by their own plans' completion passes.

## Design Invariants (CR Guard)

- Byte-parity blueprint protocol: the two re-arm FIRST ACTION paragraphs in `agents/skills/maintenance/prompt-templates.md` are byte-identical and pinned; no task edits anything inside them. Every blueprint edit lands as a new deviations-list entry describing the insertion point and paraphrasing (never quoting) pinned spans so their count gates hold.
- Additive state fields never bump schema 4 (the additive-no-bump precedent: `pending_rearm`, `pending_landing`, `rate_limited_events`, `park_proposals`); the Step 6 carry-forward list must name every field whose authoritative writes occur outside Step 6.
- The recognition rule literals (recipe title and prompt template opening) and the duplicate-parent tripwire span stay byte-stable; new guards mirror their span shape without redefining them.
- The merge landing lock's semantics, the done lock, and the lane guards' not-visible fail-safe are unchanged; the fleet cap re-weights lane occupancy, never lock serialization.
- The execution lane is never routed in-session or through the idle-time primitive (SKILL.md Step 5); the fleet cap does not change carrier-class rules.
- P57 boundary: the per-execution ad-hoc worktree design rework (Phase 0 per worktree, done-lock scope, archive commit, per-worktree discovery arms, progress marks, blueprint Phase 0 rewrite) belongs to `docs/history/backlog/2026-09-24-reinstate-per-execution-adhoc-worktree-isolation.md`; this plan amends the guards to fleet counting and records the stance supersession only, and must not pre-empt P57's design decisions.
- The plans and execute-plan skill edits of Task 7 are single-sentence regions: all other content in those two files is frozen for this plan; reject any review finding that touches them elsewhere.

## Origins and dispositions

| Origin (basename under docs/history/backlog/) | Status at authoring | Disposition |
|---|---|---|
| `2026-09-24-scheduler-discharge-parked-intents-in-same-session` | open (anchor) | Implement: Tasks 2, 3 (park mechanics), 9 (pins). |
| `2026-09-23-scheduler-execution-queue-and-durable-priority-directive` | open on peer commit 3667bf7d, absent from main | Land byte-verbatim: Task 1. Implement: Task 3. |
| `2026-09-23-user-directed-dispatch-dedup-guard` | open on peer commit 3667bf7d, absent from main | Land byte-verbatim: Task 1. Implement: Task 4. |
| `2026-09-23-d1-recert-drift-flag-instead-of-silent-skip` | open on peer commit 3667bf7d, absent from main | Land byte-verbatim: Task 1. Implement: Task 5. |
| `2026-09-23-parallel-fleet-cap-four-children` | open on detached commit 3c0af847, absent from main | Land byte-verbatim: Task 1. Implement: Task 6, with the origin's item 3 (the standing PARALLEL-RUN DISCIPLINE payload sentence in both blueprints) deferred to P57 alongside its Phase 0 rework, since the sentence is meaningless before the blueprint gains the worktree duty; the interim execution-lane constraint records the partial disposition. |
| `2026-09-23-loop-quality-hygiene-review-r1-deferred-lows` | open | Implement items 1, 3, 4: Task 7. Item 2 resolved-by-archive: disposition ledger entry in Task 7. |
| `2026-09-23-runtime-capabilities-zcode-frozen-region-hits` | open | Implement option (a): Task 7. |
| `2026-09-23-dirt-gate-origin-disposition-unrecorded` | open | Implement the origin move + registry row: Task 8. |

## Validation Commands

```bash
#!/usr/bin/env bash
# Run from the repository root. Exit 0 = every gate holds. Each gate fails loud.
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1

# G1: the four out-of-tree origins exist on the current branch (Task 1).
for f in \
  docs/history/backlog/2026-09-23-scheduler-execution-queue-and-durable-priority-directive.md \
  docs/history/backlog/2026-09-23-user-directed-dispatch-dedup-guard.md \
  docs/history/backlog/2026-09-23-d1-recert-drift-flag-instead-of-silent-skip.md \
  docs/history/backlog/2026-09-23-parallel-fleet-cap-four-children.md ; do
  test -f "$f" || { echo "G1 FAIL: missing $f"; exit 1; }
done

# G2: the discharge duty exists with its able-session predicate and guard-bound
# wording in SKILL.md, and both blueprint bodies carry the closing discharge
# paragraph anchor (Task 2).
grep -q "park-discharge duty" agents/skills/maintenance/SKILL.md \
  || { echo "G2 FAIL: discharge duty anchor absent from SKILL.md"; exit 1; }
grep -q "discharges the parked intents in the same session before ending, guard-bound" agents/skills/maintenance/SKILL.md \
  || { echo "G2 FAIL: discharge duty operative phrase absent from SKILL.md"; exit 1; }
grep -q "able-session predicate" agents/skills/maintenance/SKILL.md \
  || { echo "G2 FAIL: able-session predicate absent from SKILL.md"; exit 1; }
grep -qf <(printf '%s\n' 'CLOSING PARK DISCHARGE DUTY') agents/skills/maintenance/prompt-templates.md \
  || { echo "G2 FAIL: blueprint discharge paragraph absent"; exit 1; }
test "$(grep -c 'CLOSING PARK DISCHARGE DUTY' agents/skills/maintenance/prompt-templates.md)" -eq 2 \
  || { echo "G2 FAIL: discharge paragraph must appear exactly once per blueprint body (2 total)"; exit 1; }

# G3: the two new state fields are declared in the schema block, carried forward,
# and named in the sanctioned-writer enumeration (Task 3).
for pat in execution_queue execution_priority; do
  test "$(grep -c "\"$pat\"" agents/skills/maintenance/SKILL.md)" -ge 1 \
    || { echo "G3 FAIL: $pat absent from the schema block"; exit 1; }
  grep -q "$pat" <(grep -A3 "carry forward" agents/skills/maintenance/SKILL.md) \
    || { echo "G3 FAIL: $pat absent from the Step 6 carry-forward list"; exit 1; }
done

# G4: the needs-recert flag and the dedup tripwire exist (Tasks 4, 5).
grep -q "needs-recert" agents/skills/maintenance/SKILL.md \
  || { echo "G4 FAIL: needs-recert flag absent"; exit 1; }
grep -q "duplicate-user-directed-dispatch" agents/skills/maintenance/SKILL.md \
  || { echo "G4 FAIL: user-directed dedup tripwire absent"; exit 1; }
grep -q "execution-claims" agents/skills/maintenance/SKILL.md \
  || { echo "G4 FAIL: execution claim directory absent from the discovery arm"; exit 1; }

# G5: the fleet cap wording replaced the serialized-cap wording at all four
# pinned sites, and the concurrency stance records the supersession (Task 6).
grep -q "fleet" agents/skills/maintenance/SKILL.md \
  || { echo "G5 FAIL: fleet cap wording absent"; exit 1; }
sed -n '/### Execution-lane concurrency stance/,/^## Revisions/p' agents/skills/maintenance/SKILL.md | grep -q "2026-09-24" \
  || { echo "G5 FAIL: stance supersession date absent"; exit 1; }
sed -n '/### Execution-lane concurrency stance/,/^## Revisions/p' agents/skills/maintenance/SKILL.md | grep -q "one in-flight child until P57" \
  || { echo "G5 FAIL: interim execution constraint absent from the stance"; exit 1; }

# G6: the shared-body scan is GREEN and the reworded sentences keep their
# dispatch-discipline pointer (Task 7).
PYTHONPATH=scripts python3 -m unittest scripts.test_runtime_capabilities 2>&1 | grep -q "^OK" \
  || { echo "G6 FAIL: capabilities suite not green"; exit 1; }
grep -q "agents/skills/maintenance/zcode" agents/skills/plans/SKILL.md \
  && { echo "G6 FAIL: frozen-region token still present in plans skill"; exit 1; }
grep -q "agents/skills/maintenance/zcode" agents/skills/execute-plan/SKILL.md \
  && { echo "G6 FAIL: frozen-region token still present in execute-plan skill"; exit 1; }
grep -q "Dispatch discipline and loop stand-down" agents/skills/plans/SKILL.md \
  || { echo "G6 FAIL: reworded sentence lost its section pointer (plans)"; exit 1; }
grep -q "Dispatch discipline and loop stand-down" agents/skills/execute-plan/SKILL.md \
  || { echo "G6 FAIL: reworded sentence lost its section pointer (execute-plan)"; exit 1; }

# G7: the deferred lows landed (Task 7).
grep -q 'an audit marker occupies only' agents/skills/maintenance/SKILL.md \
  || { echo "G7 FAIL: audit-marker widened-arm clause absent"; exit 1; }
grep -q -- '-7' <(grep -o 'FRICTION_AUDIT_CADENCE_DAYS:[^"]*' agents/skills/maintenance/zcode.md) \
  || { echo "G7 FAIL: cadence fallback absent from the invocation"; exit 1; }

# G8: the dirt-gate origin moved with its disposition line (Task 8).
grep -q "Status: done" docs/history/backlog/completed/2026-09-22-dirt-gate-staged-deletion-edge.md \
  || { echo "G8 FAIL: dirt-gate origin not routed done"; exit 1; }
test ! -f docs/history/backlog/2026-09-22-dirt-gate-staged-deletion-edge.md \
  || { echo "G8 FAIL: dirt-gate origin still at the top level"; exit 1; }

# G9: the mechanical suites (every task; final state here).
bash scripts/check_maintenance_pins.sh \
  || { echo "G9 FAIL: pins suite"; exit 1; }
bash scripts/scan-public-hygiene.sh \
  || { echo "G9 FAIL: hygiene scan"; exit 1; }
echo "VALIDATION OK"
```

### Task 1: Land the four out-of-tree origin backlog files onto main

Files:
- `docs/history/backlog/2026-09-23-scheduler-execution-queue-and-durable-priority-directive.md` *(new)*
- `docs/history/backlog/2026-09-23-user-directed-dispatch-dedup-guard.md` *(new)*
- `docs/history/backlog/2026-09-23-d1-recert-drift-flag-instead-of-silent-skip.md` *(new)*
- `docs/history/backlog/2026-09-23-parallel-fleet-cap-four-children.md` *(new)*

- [x] Extract the three queue/dedup/recert origin files byte-verbatim from commit 3667bf7d (`git show 3667bf7d:<path> > <path>` for each) and the fleet-cap file from commit 3c0af847; verify each extracted file's sha256 equals `git show <commit>:<path> | shasum -a 256` [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the four files carry `Status: open` and their header fields match the backlog convention of their siblings [class: REPOSITORY_TEST]
- [x] Commit: `backlog: land P54 companion origins from peer branches (queue/priority, dedup guard, d1 recert flag, fleet cap)` [class: REPOSITORY_TEST]

### Task 2: Able-session park-discharge duty (anchor origin)

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`

- [x] SKILL.md Step 1: append one park-discharge duty bullet after the Pending re-arm bullet: any session (scheduler turn, child, or interactive) that reads the state file and observes a set `pending_rearm` or `pending_dispatch` plus its own able-session predicate discharges the parked intents in the same session before ending, guard-bound: re-arm per the overlay recipe from the paired payload copy (consuming it per the field paragraph's consume-after-survival rule) and/or dispatch the retained target per its kind through the normal Step 5 path (the Step 1 reader's validation arms, the loop-mode and rate-pressure gates, and the landing gate all apply unchanged), then clear the discharged field in one targeted state edit; sessions that cannot mutate automations keep the park-and-stop behavior and the loop guard unchanged; the discharge writes join the sanctioned-writer enumeration (a discharging child appends its own `children[]` entry and clears the field in the same targeted edit discipline); two sessions discharging concurrently are governed by the targeted-edit drift-retry rules (the loser re-reads the fresh state and yields when the field is already cleared), never by first-writer trust [class: IMPLEMENTATION_REQUIRED]
- [x] prompt-templates.md: both blueprint bodies gain, immediately before their FINAL STEP compaction paragraph, a `CLOSING PARK DISCHARGE DUTY` paragraph (the literal anchor appears exactly once per body, 2 total): before ending, read the state file; when `pending_rearm` or `pending_dispatch` is set and the session passes the child-side primitive precheck (the overlay's ladder precheck discipline), discharge guard-bound per the SKILL.md duty; on primitive absence, leave the park standing (the existing park-and-stop behavior); register one deviations-list entry describing both insertions without quoting pinned spans [class: IMPLEMENTATION_REQUIRED]
- [x] zcode.md "Child dispatch ladder": add one bullet naming the discharge duty's primitive precheck routing (an absent create primitive routes a decided discharge to the park path, never to listings), mirroring the reduced-toolset inheritance note [class: IMPLEMENTATION_REQUIRED]
- [x] scripts/check_maintenance_pins.sh: register needles for the able-session predicate literal, the `pending_rearm or pending_dispatch` field predicate in SKILL.md, and the exactly-2 count of the `CLOSING PARK DISCHARGE DUTY` anchor in prompt-templates.md [class: REPOSITORY_TEST]
- [x] Verify the re-arm FIRST ACTION paragraphs are byte-identical to their pre-task bytes (the parity pin still passes in the pins suite run) [class: REPOSITORY_TEST]
- [x] Run the validation block G2 + G9; expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `skills: able-session park-discharge duty for parked rearm and dispatch intents (P54 anchor)` [class: REPOSITORY_TEST]

### Task 3: Execution queue, durable priority directive, park-first chaining

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`

- [x] SKILL.md State file: add top-level `execution_queue` (an ordered array of executable plan paths, dependency-chain and priority ordering applied; popped at the head on dispatch; written by scheduler turns and execution children) and `execution_priority` (object or null: `{"directive": "<user wording>", "set_at": "<iso>", "note": "<carrier instructions>"}`, written by a turn or session carrying an explicit user ordering directive, replaced or withdrawn by the same writer, the withdrawal leaving the datable `cleared_at` trace like `loop_mode`), both additive under schema 4 with no version bump; add both lines to the schema block, both fields to the sanctioned-writer enumeration, and both to the Step 6 carry-forward list [class: IMPLEMENTATION_REQUIRED]
- [x] SKILL.md Step 3 D1: when `execution_queue` is non-empty, the head is the selection candidate (still through the guards, the certification oracle, and the skip rules; an invalid head pops and the next head is evaluated, each pop recorded in `decision_reason`); when `execution_priority` is set, D1's ordering reads it before the memory dependency-chain order; a dispatching turn or child pops the dispatched head and records the pop [class: IMPLEMENTATION_REQUIRED]
- [x] SKILL.md sanctioned-writer enumeration: the execution-child successor-dispatch class gains the queue-prepend write (a finishing child prepends the next selected target to `execution_queue` in the same targeted edit family as its successor dispatch); no new writer class is created, the additions join the existing enumerations so the closed list stays closed [class: IMPLEMENTATION_REQUIRED]
- [x] prompt-templates.md execution blueprint successor paragraph: park-first chaining: the successor duty writes the `pending_dispatch` park plus the assembled successor payload copy under the dispatch kind's identity-bound payload filename BEFORE the reshape/create attempt (decision-first recording, the existing park-path pairing rule), and consumes the park in the same targeted edit when its dispatch then succeeds; register the deviations-list entry [class: IMPLEMENTATION_REQUIRED]
- [x] zcode.md "Child dispatch ladder" step on the successor duty: note the park-first ordering beside the both-legs-fail branch (the park now precedes the primitive phase; the failure branch's existing write becomes the consume-or-keep tail) [class: IMPLEMENTATION_REQUIRED]
- [x] scripts/check_maintenance_pins.sh: needles for both schema-block lines, the carry-forward mention, and the park-first anchor literal in the execution blueprint [class: REPOSITORY_TEST]
- [x] Run the validation block G3 + G9; expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `skills: execution_queue and durable priority directive with park-first successor chaining (P54 origin 2)` [class: REPOSITORY_TEST]

### Task 4: User-directed dispatch dedup guard and fire-time execution claims

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`

- [x] SKILL.md Step 2: add the duplicate-user-directed-dispatch tripwire after the Duplicate-parent tripwire: when the automation listing shows an ENABLED non-recurring automation whose prompt contains the resolved repository root and a plan-execution payload that is USER-DIRECTED by the mechanical negative shape (a plan-execution payload that neither is a scheduler-parent recognition match nor opens with the execution blueprint's payload opening literal, the first line the Step 5 dispatch slice places at the head of every scheduler-dispatched child prompt, whose stable prefix is "You are an unattended scheduled session in the repository at"), and this turn is about to create another user-directed execution dispatch for the same repository, defer the create instead (record the existing record's id in `decision_reason`); the overlap predicate is the armed record's existence itself (ENABLED with a future `nextRunAt` for the same repository), not directive-text matching, so two wordings of the same directive still collide and two genuinely different directives still serialize; a turn may collapse the duplicate only with an explicit user instruction [class: IMPLEMENTATION_REQUIRED]
- [x] SKILL.md Step 2 G1e discovery arm: add the execution-claim check mirroring the authoring arm: a claim file under the resolved tmp directory's `execution-claims/` (default `docs/tmp/execution-claims/`) whose `updated:` is fresher than one cadence period occupies the execution lane unless a pending execution `children[]` entry explains it (target-keyed matching on the plan slug); a stale claim occupies nothing [class: IMPLEMENTATION_REQUIRED]
- [x] prompt-templates.md execution blueprint: add an EXECUTION CLAIM duty paragraph after the re-arm duty paragraph in gate-before-write order: write `docs/tmp/execution-claims/<plan-slug>.md` in the primary checkout (explicit-rooted form; frontmatter session:, plan:, created:, updated:; create-if-absent noclobber), refresh `updated:` at every phase boundary, delete at closeout and on an owned stand-down; a fresh foreign claim refuses the start (stand down writing nothing), a stale foreign claim is taken over (re-read before the unlink); register the deviations-list entry [class: IMPLEMENTATION_REQUIRED]
- [x] zcode.md "Child classification markers": note the execution-claim file as the in-flight witness beside the authoring claim witness [class: IMPLEMENTATION_REQUIRED]
- [x] scripts/check_maintenance_pins.sh: needles for the tripwire literal, the user-directed negative-shape definition beside it (the payload-opening prefix the tripwire's filter tests), the claim directory in the discovery arm, and the blueprint claim duty anchor [class: REPOSITORY_TEST]
- [x] Run the validation block G4 + G9; expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `skills: user-directed dispatch dedup guard and fire-time execution claims (P54 origin 3)` [class: REPOSITORY_TEST]

### Task 5: needs-recert dispatchability for digest-drifted plans

Files:
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [x] SKILL.md Step 3 D1: a plan failing the certification oracle on a stale `source_digest` is not dropped from selection: mark it needs-recert on the selection record (or its `execution_queue` entry) and keep it dispatchable, the child's PRE-STEP re-certification being the designed drift handler; record the drift reason in `decision_reason`; keep the hard skip only for a plan that fails re-certification after the pre-step (the existing execute-plan behavior) [class: IMPLEMENTATION_REQUIRED]
- [x] SKILL.md Step 1 certification bullet: note that a drifted result records the needs-recert mark instead of a silent skip, so the survey output shows why a drifted plan remains eligible [class: IMPLEMENTATION_REQUIRED]
- [x] scripts/check_maintenance_pins.sh: needle for the needs-recert literal inside the D1 region [class: REPOSITORY_TEST]
- [x] Run the validation block G4 + G9; expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `skills: D1 flags re-cert digest drift instead of silently skipping (P54 origin 4)` [class: REPOSITORY_TEST]

### Task 6: Repo-wide fleet cap of four concurrent children

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`

- [x] SKILL.md Step 2: rework `G1e`/`G1a` into fleet-count guards: both lanes trip when the repo-wide count of live children reaches 4 (the count sums live peer sessions found by the discovery arms, pending `children[]` entries under the release rules, and armed child automations in the listing; a child is counted once, the strongest arm winning in the order state-file arm, then discovery arm, then listing arm); below the cap, D1 and D2 dispatch; INTERIM EXECUTION CONSTRAINT (review r1 F1): the execution lane stays at one in-flight child until P57 lands the isolation mechanisms, because the execution blueprint still runs branch-based Phase 0 in the shared primary checkout and a second branch-based execution would reproduce the documented collision list; the authoring and audit lanes may fill the remaining fleet slots; the per-turn dispatch limits (at most one execution and one authoring per turn) and the audit-lane occupancy rules stand unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] SKILL.md Invariants: replace the two single-occupancy bullets (at-most-one-per-lane-in-flight and strictly-sequential) with the fleet cap wording (repo-wide 4 across mixed kinds; the authoring and audit lanes fill the fleet slots; the execution lane holds at one in-flight child until P57's isolation lands, then worktree-isolated executions fill their slots; merge-lock landings); keep the post-review pre-landed single-run cap bullet unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] SKILL.md Execution-lane concurrency stance: rewrite the section to record the supersession chain by date (2026-09-15 rejection; 2026-09-19 stance; 2026-09-23 fleet-cap directive; 2026-09-24 worktree-isolation dispatch default) INCLUDING the interim constraint this plan lands (execution lane held at one until P57), keep the collision list as the rationale P57 owns, and name P57's origin file as the owner of the remaining design rework (Phase 0 per worktree, done-lock scope, archive commit, per-worktree discovery rework, progress marks, blueprint Phase 0 rewrite) [class: IMPLEMENTATION_REQUIRED]
- [x] zcode.md: the dispatch ladder's second-lane bullet and the child classification markers gain the fleet-counting note (the guards count, not exclude; authoring and audit children are fleet members counted toward the cap; the execution lane stays single until P57) [class: IMPLEMENTATION_REQUIRED]
- [x] scripts/check_maintenance_pins.sh: grep the suite for pins whose needle text matches the SKILL.md spans this task rewords (the widened-arm containment anchors and the Invariants single-occupancy wording) and update exactly those pins to the fleet-cap wording; verified at r2: no pin's needle matches the reworded spans today, so the diligent edit set is likely empty; the four execute-plan panel serialized-cap pins (the P48 Task 4 replacements keyed on the execute-plan skill file) are OUT OF SCOPE and must not be touched [class: REPOSITORY_TEST]
- [x] Run the validation block G5 + G9; expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `skills: repo-wide fleet cap of four concurrent children supersedes single-lane guards (P54 origin 5)` [class: REPOSITORY_TEST]

### Task 7: Shared-body RED fix and deferred lows bundle

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`

- [x] plans/SKILL.md (the one suppression-risk sentence region only): reword the parenthetical to drop the literal overlay path: reference "the maintenance skill's runtime overlay, its Dispatch discipline and loop stand-down section" without naming the overlay file; keep the sentence's meaning and the section pointer intact [class: IMPLEMENTATION_REQUIRED]
- [x] execute-plan/SKILL.md (the one suppression-risk sentence region only): the same rewording of the matching sentence [class: IMPLEMENTATION_REQUIRED]
- [x] SKILL.md Step 2 widened arm: add "an audit marker occupies only `G1a`" to the lane-classification enumeration (between the authoring-marker and execution-marker clauses), and add the marker-carriage sentence to the `G1a` lane paragraph (deferred low 1) [class: IMPLEMENTATION_REQUIRED]
- [x] zcode.md audit recipe invocation: inline the fallback so the canonical invocation reads `--cadence-days "${FRICTION_AUDIT_CADENCE_DAYS:-7}"` (deferred low 4); check the pins suite for a pinned invocation literal first and update it in the same edit if pinned [class: IMPLEMENTATION_REQUIRED]
- [x] Record the deferred-low 2 disposition in this plan's completion notes: resolved-by-archive (the hygiene plan is archived; archived plans are immutable; no edit) [class: REPOSITORY_TEST]
- [x] Verify RED-today first: before the rewording, `PYTHONPATH=scripts python3 -m unittest scripts.test_runtime_capabilities` reports exactly 2 failures naming the two shared skill files (witnessed at authoring 2026-09-24); after the rewording the suite reports OK, and the negative control is the suite's own behavior witness (a bare vendor token in a shared body flips it RED, `test_shared_skill_bodies_have_no_runtime_names`) [class: REPOSITORY_TEST]
- [x] Run the validation block G6 + G7 + G9; expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `skills: reword overlay references to fix shared-body scan, land deferred lows (P54 origins 6-7)` [class: REPOSITORY_TEST]

### Task 8: Dirt-gate origin disposition

Files:
- `docs/history/backlog/completed/2026-09-22-dirt-gate-staged-deletion-edge.md` (executed state of the Task 8 move from `docs/history/backlog/2026-09-22-dirt-gate-staged-deletion-edge.md`; files list updated by the 2026-09-24 non-semantic plan correction after the move landed)
- `docs/maintenance/document-registry.md`

- [x] Move `docs/history/backlog/2026-09-22-dirt-gate-staged-deletion-edge.md` to `docs/history/backlog/completed/` with `Status: done (executed via docs/plans/completed/2026-09-23-ai-harness-friction-audit.md, Task 4)`; verify the committed destination carries the content edits after the git-mv (rename-commit trap) [class: IMPLEMENTATION_REQUIRED]
- [x] Add the ownership-registry row for the moved origin (status completed, date, pointer to the audit plan) [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the audit record's lifecycle claim now holds for this item (the origin is discoverable from the plan's completion surfaces) [class: REPOSITORY_TEST]
- [x] Run the validation block G8 + G9; expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `backlog: route dirt-gate fix origin done with registry row (P54 origin 8)` [class: REPOSITORY_TEST]

### Task 9: Revisions ledger and closeout validation

Files:
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [x] SKILL.md Revisions: add the 2026-09-24 P54 entry recording the schema additions (`execution_queue`, `execution_priority`), the discharge duty, the dedup tripwire, the needs-recert flag, the fleet-cap guard rework, and the stance supersession, naming this plan [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full validation block end to end; expect `VALIDATION OK` [class: REPOSITORY_TEST]
- [x] Run `python3 scripts/plan_readiness.py docs/plans/2026-09-24-p54-scheduler-loop-continuity-directives.md`; expect exit 0 on the final digest [class: REPOSITORY_TEST]
- [x] Commit: `skills: P54 loop-continuity revisions ledger and closeout validation` [class: REPOSITORY_TEST]
