# Plan: P48 post-execution residuals sweep (9 origins)

Origins (scope of record; each disposition-checked at authoring, 2026-09-23):

- `docs/history/backlog/2026-09-23-p36-phase3-low-residuals.md`
- `docs/history/backlog/2026-09-20-context-budget-plan-design-residues.md`
- `docs/history/backlog/2026-09-21-r429-execute-plan-ratelimit-end-residuals.md`
- `docs/history/backlog/2026-09-22-agent-aware-contract-review-r1-nonblocking-deferrals.md`
- `docs/history/backlog/2026-09-23-p37-rate-pressure-r1-review-residuals.md`
- `docs/history/backlog/2026-09-23-p37-turn-usage-variant-b-precision.md`
- `docs/history/backlog/2026-09-23-execute-plan-codex-adapter-evidence-verifier-completeness-mirror.md`
- `docs/history/backlog/2026-09-23-execute-plan-skill-telemetry-jsonl-runtime-name-violation.md`
- `docs/history/backlog/2026-09-23-execute-plan-unlanded-plan-worktree-cherry-pick.md`

Coordination context: `docs/tmp/execute-plan/2026-09-23-ai-harness-friction-audit/task2-reconciliation.md` section 3.5 (the "recheck the runtime plan's status" rule this plan's workstream dispositions apply).

## Terms

- **Origin**: a backlog item this plan disposition-checks; the item's own text is the scope of record for its fix.
- **Disposition-check**: the authoring-time verification of whether an origin's fix already landed (absorbed), is owned by the active runtime workstream, or is still open repo-side work. Every disposition below cites quoted evidence, per the deferral-sweep cross-check rule (`docs/history/backlog/2026-09-22-deferral-sweeps-must-cross-check-claimed-origins.md`).
- **The workstream**: the active runtime reconciliation execution on branch `2026-09-22-codex-execute-plan-runtime-reconciliation` (tip 19931145, committed 2026-09-23 15:18 +0100); until it lands, its changed files own the runtime surface and this plan does not edit them.
- **Pins suite**: `scripts/check_maintenance_pins.sh`, the literal-span gate over the maintenance and execute-plan skill bodies.

## Assumptions

- assume the disposition-check results recorded 2026-09-23 hold at execution time; basis: quoted landed spans in the disposition ledger below plus executed probes (the runtime capabilities suite witnessed RED today with 2 failures and the violation `agents/skills/execute-plan/SKILL.md: jsonl`; the pins suite baseline is green; the workstream branch diff was inspected file-by-file).
- assume the workstream is still active at execution; recheck its branch tip and whether it has landed on main before Task 1, and if it has landed, convert the workstream-owned deferral dispositions below to done-routing dispositions at closeout instead; basis: the coordination rule in the friction-audit reconciliation report section 3.5.
- assume the rate-pressure residuals R2 (the D1 threshold sentence's 24-hours phrase) and R4 (the doubled panel bound versus five-worker serialized panels) stay deferred: their own trigger conditions ("a fourth define-once trim pass opens", "revisit with panel-size data") have not fired and no task here fires them; basis: the origin item's own trigger text.
- assume p36 F1 stays deferred-with-trigger (no task here opens the budget-guard rotation module) and p36 F2 defers to the workstream (`scripts/execute_plan_runtime.py` is on the workstream branch); p36 F3 and F4 are guidance notes for future plans, not code fixes; basis: the origin item's suggested-fix text plus the branch file list.
- assume the context-budget sentence-drop stays deferred-with-trigger (it rides the next planned touch of `agents/skills/maintenance/prompt-templates.md`, which no task here opens); its sibling deferral is already resolved: the completed context-budget plan's header `Plan review:` line now names r7 as latest ready (verified 2026-09-23); basis: the origin item's ride-along discipline plus the header check.
- assume the telemetry-literal fix shape is the origin's option (b): reword `agents/skills/execute-plan/SKILL.md`; option (a) edits `scripts/runtime_capabilities.py`, which the workstream branch changes (94 added lines), so touching it here would collide with the active workstream; basis: the origin item's fix-shape analysis plus the branch diff.

Decision points requiring a grill: r429 route-as-absorbed (decision: route done at closeout with `docs/plans/completed/2026-09-22-p37-rate-pressure-ingestion-and-quota-scheduling.md` as implementation reference; source: verified landed spans in execute-plan/SKILL.md and that completed plan's own origin-7 sections, 2026-09-23; affects: disposition ledger); B42 defer-to-workstream (decision: record the disposition and implement nothing while the workstream is active; source: the branch's Evidence verifier section already carries the completeness clause and the coordination rule section 3.5 forbids unilateral moves, 2026-09-23; affects: disposition ledger); agent-aware F2-F4 defer-to-workstream (decision: record the disposition; source: both owned files are on the workstream branch, 2026-09-23; affects: disposition ledger); B43 option-b (decision: reword the SKILL.md literals; source: the runtime_capabilities.py collision on the branch, 2026-09-23; affects: Task 2); context-budget sentence-drop defer (decision: honor the item's own ride-along trigger; source: the item text accepted under standing pre-authorization, 2026-09-23; affects: disposition ledger); single-plan shape (decision: no quota-family/driver-family split; source: the P48 scope text's 600-line threshold plus this plan's projected size well under it, 2026-09-23; affects: plan shape).

## Gist & Examples

The execution wave of 2026-09-22/23 filed nine residual backlog items as its own annotated tails. This plan fixes the ones whose repo-side triggers have fired, records evidence-backed dispositions for the absorbed and workstream-owned ones, and leaves each deferred-with-trigger residual exactly where its own trigger discipline puts it. The disposition ledger is the plan's central artifact: every origin ends here with exactly one disposition and every disposition cites what was checked.

**Disposition ledger (verified 2026-09-23):**

| Origin | Verified state | Disposition |
|---|---|---|
| `2026-09-21-r429-execute-plan-ratelimit-end-residuals` | Fully absorbed: main's fan-out paragraph carries the 60-second backoff floor, the recovery-marker line, and the 24-hour durable re-derivation; the structured-reporting paragraph carries the budget-pause claim boundary, the claim-scoped receipt carrier, and the claim-less stop-lines derivation; the cap-1 serialized case doubles panel bounds. All four spans verified verbatim in `agents/skills/execute-plan/SKILL.md` (fan-out and structured-reporting paragraphs) and in the completed rate-pressure plan's Task 1 and "Backoff floor and scaled panel timeout (origin 7 items 2, 3)" sections. | Route done at closeout; implementation reference `docs/plans/completed/2026-09-22-p37-rate-pressure-ingestion-and-quota-scheduling.md` (landed main 394c5098). The five-worker edge beyond the doubling is R4, tracked on the rate-pressure residuals origin. |
| `2026-09-23-execute-plan-codex-adapter-evidence-verifier-completeness-mirror` | Covered by the workstream: the branch's `runtime-adapters/codex.md` Evidence verifier section now reads "and the plan-criterion coverage the changes satisfy", which is the mirror the origin asks for. | Defer to the workstream; route done with that plan as reference after it lands. No edit here. |
| `2026-09-23-execute-plan-skill-telemetry-jsonl-runtime-name-violation` | Open and repo-side: the suite is RED on pristine main (witnessed: 2 failures, violation `agents/skills/execute-plan/SKILL.md: jsonl`; both `.jsonl`-bearing lines are the Telemetry and Phase 4 archive sentences). Not covered by the workstream (its branch does not touch execute-plan/SKILL.md and its `runtime_capabilities.py` changes add no jsonl exemption). | Implement option (b): Task 2. |
| `2026-09-23-execute-plan-unlanded-plan-worktree-cherry-pick` | Open and repo-side: the linked-worktree bootstrap covers only gitignored inputs; the missing-plan case is unnamed (`cherry-pick` absent from execute-plan/SKILL.md, verified). Not covered by the workstream. | Implement: Task 1. |
| `2026-09-23-p37-rate-pressure-r1-review-residuals` | R1 and R5 triggers fire (this plan is a maintenance SKILL.md touch); R3's per-site pin pattern is introduced here while the pins suite is open for Task 3; R2 and R4 triggers have not fired. | Implement R1, R3, R5: Tasks 3 and 4. Record R2 and R4 as deferred-with-trigger. |
| `2026-09-23-p37-turn-usage-variant-b-precision` | Open and repo-side: the Variant B sentence and the Proxy ratio comma splice are in `agents/skills/maintenance/zcode.md` line 79 as described; the `turn_usage` pin is presence-only (`grep -qF 'turn_usage'`), so the reword is pin-safe. | Implement: Task 5. |
| `2026-09-22-agent-aware-contract-review-r1-nonblocking-deferrals` | F2, F3, F4 sit on `scripts/test_runtime_capabilities.py` and `runtime-adapters/codex.md`, both on the workstream branch; F1's named commits (144cfd33, 39193c42, cb7144a0) are reachable locally, so the bounded reconciliation is runnable. | F1 reconciliation attempt: Task 6. F2-F4: defer to the workstream, route after it lands. |
| `2026-09-20-context-budget-plan-design-residues` | Sentence-drop trigger names the next planned `prompt-templates.md` touch (not opened here); the sibling deferral (the completed plan's stale `Plan review:` header line) is already fixed on the archived bytes. | Record: sentence-drop deferred-with-trigger; sibling resolved. No edit. |
| `2026-09-23-p36-phase3-low-residuals` | F1's file is not opened by any task here; F2's file is on the workstream branch; F3 and F4 are guidance for future plans' validation shapes. | Record all four as deferred-with-trigger or workstream-owned. No edit. |

**What changes:** four files. `agents/skills/execute-plan/SKILL.md` gains the unlanded-plan bootstrap remedy (Task 1) and loses its `.jsonl` telemetry literals (Task 2). `agents/skills/maintenance/SKILL.md` loses the duplicated `rate_limited_events` carry-forward mention and gains the missing Revisions entry (Task 3). `scripts/check_maintenance_pins.sh` replaces the one-of-four serialized-cap pin with four per-site pins (Task 4), registers the unlanded-plan remedy pin (Task 1), and updates the dedup-ledger pin span (Task 3). `agents/skills/maintenance/zcode.md` gets the Variant B precision reword and the comma-splice fix (Task 5).

**Example (Task 3, before):** "and `rate_limited_events` (the Step 1 child-outcome ingestion appends its entries before Step 6, so the rewrite must carry them) plus `rate_limited_events` and the dedup ledger (the ledger is a top-level field...)". **After:** the second (duplicate) mention drops and the first mention keeps its own introduction: "and `rate_limited_events` (the Step 1 child-outcome ingestion appends its entries before Step 6, so the rewrite must carry them) plus the dedup ledger (the ledger is a top-level field...)".

**Example (Task 2, before):** "review-loop's docs/tmp/review-loop/<branch-slug>/context.jsonl". **After:** "review-loop's per-run context telemetry log under docs/tmp/review-loop/<branch-slug>/". The `docs/tmp/` literal prefixes stay (the payload-path convention), only the vendor-envelope `.jsonl` suffix leaves the shared body.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every implemented task's GREEN gate passes on the post-task tree; every disposition in the ledger cites quoted evidence verified at authoring.
- non-regression: the pins suite stays green (with its two in-task pin updates), the runtime capabilities suite goes from 2 witnessed failures to 35 passing tests, and the portability checker stays exit 0.
- completeness: all nine origins appear in the disposition ledger with exactly one disposition each; the closeout can route every origin from the ledger alone.

**Done when:**
- The whole Validation Commands block exits 0 on the final tree.
- The ledger covers 9/9 origins with evidence citations.
- R2, R4, p36 F1-F4, and the context-budget sentence-drop each have a recorded disposition naming their unfired trigger or owning surface.

**Ship when:**
- None; all work is repo-verifiable. The workstream-coordinated origins (B42, agent-aware F2-F4, p36 F2) land on the runtime reconciliation plan's own schedule and route at its closeout.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md` (two regions only: the Linked-worktree bootstrap block; the Telemetry sentence and the Phase 4 archive ordering sentence. All other content is frozen; reject any review finding that touches it.)
- `agents/skills/maintenance/SKILL.md` (two regions only: the Step 6 carry-forward sentence inside the scheduler-turn writer-class bullet; one appended `## Revisions` entry. All other content is frozen, including the D1 threshold sentence.)
- `agents/skills/maintenance/zcode.md` (one region only: the Proxy ratio bullet. All other content is frozen, including the Compaction bullet's existing em-dash.)
- `scripts/check_maintenance_pins.sh` (three regions only: the dedup-ledger pin span; the serialized-cap pin block; the Task 1 companion pin added beside the other execute-plan pins. All other content is frozen.)

**Tests:**
- No new or edited test files. The pins suite and the runtime capabilities suite are validation targets only.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/prompt-templates.md`; reason: the payload-path literals stay in literal form per the payload-path convention record, and the sentence-drop origin rides its own later planned touch of that file.
- `scripts/runtime_capabilities.py`, `scripts/test_runtime_capabilities.py`; reason: workstream-owned (both on the active branch); the fix shape deliberately avoids them.
- `agents/skills/execute-plan/runtime-adapters/codex.md`, `agents/skills/execute-plan/runtime-contract.md`; reason: workstream-owned.
- `scripts/execute_plan_runtime.py` and the budget-guard rotation module; reason: p36 F2 is workstream-owned and p36 F1 is deferred-with-trigger.
- `docs/plans/completed/` contents; reason: certified completed-plan bytes are immutable; dispositions reference them, never edit them.

## Validation Commands

Run from the repository root. Every gate aborts non-zero on failure; the absence gates implement the three-way polarity split (rc 0 forbidden match fails, rc 1 passes, rc 2 or higher is a tool error that aborts).

```bash
# Gate 0: plan readiness (schema, tags, scope categories, trailer).
python3 scripts/plan_readiness.py docs/plans/2026-09-23-p48-post-execution-residuals-sweep.md || { echo "GATE 0 FAIL: readiness validator" >&2; exit 1; }

expect_present() { grep -q "$1" "$2" || { echo "GATE FAIL: missing span: $1" >&2; exit 1; }; }
expect_absent() { local pat="$1"; shift; grep -n "$pat" "$@"; local rc=$?; if [ "$rc" -eq 0 ]; then echo "GATE FAIL: forbidden span present: $pat" >&2; exit 1; elif [ "$rc" -ge 2 ]; then echo "GATE ERROR: grep rc=$rc" >&2; exit 1; fi; }

# Gate 1 (Task 1): the unlanded-plan bootstrap remedy is present.
expect_present -F 'cherry-pick only the plan-authoring commit' agents/skills/execute-plan/SKILL.md
expect_present -F 'plan file does not exist' agents/skills/execute-plan/SKILL.md

# Gate 2 (Task 2): no vendor-envelope .jsonl literal remains in the shared body;
# suite green (RED today: 2 failures, violation 'agents/skills/execute-plan/SKILL.md: jsonl').
expect_absent 'jsonl' agents/skills/execute-plan/SKILL.md
PYTHONPATH=scripts python3 -m unittest scripts.test_runtime_capabilities 2>&1 | tail -3
PYTHONPATH=scripts python3 -m unittest scripts.test_runtime_capabilities >/dev/null 2>&1 || { echo "GATE 2 FAIL: runtime capabilities suite not green" >&2; exit 1; }

# Gate 3 (Task 3): carry-forward double-entry gone, corrected span present,
# and the Revisions log carries the dedup-ledger entry (region-scoped).
expect_present -F 'must carry them) plus the dedup ledger' agents/skills/maintenance/SKILL.md
expect_absent -F 'plus `rate_limited_events` and the dedup ledger' agents/skills/maintenance/SKILL.md
sed -n '/^## Revisions/,$p' agents/skills/maintenance/SKILL.md | grep -qF 'rate_limited_dedup_ledger' || { echo "GATE 3 FAIL: dedup-ledger Revisions entry missing" >&2; exit 1; }
sed -n '/^## Revisions/,$p' agents/skills/maintenance/SKILL.md | sed -n '2p' | grep -qF 'P48 post-execution residuals sweep' || { echo "GATE 3 FAIL: the new entry is not the newest Revisions bullet" >&2; exit 1; }

# Gate 4 (Task 4): per-site serialized-cap pins; the union pin is gone; the pins suite holds all of them.
bash scripts/check_maintenance_pins.sh || { echo "GATE 4 FAIL: pins suite" >&2; exit 1; }
expect_absent -F 'serialized cap doubles panel bounds' scripts/check_maintenance_pins.sh

# Gate 5 (Task 5): Variant B sums-based form present, splice gone, pin token intact.
expect_present -F 'none tracks context size via per-session sums' agents/skills/maintenance/zcode.md
expect_absent -F 'for exactly this reason), the store' agents/skills/maintenance/zcode.md
expect_present -F 'turn_usage' agents/skills/maintenance/zcode.md

# Gate 6 (repo hygiene): portability stays green; the plan file is em-dash clean;
# the public-hygiene scan exits 0.
python3 scripts/check_review_agent_portability.py || { echo "GATE 6 FAIL: portability checker" >&2; exit 1; }
bash scripts/check-no-em-dash.sh file docs/plans/2026-09-23-p48-post-execution-residuals-sweep.md || { echo "GATE 6 FAIL: em-dash in plan" >&2; exit 1; }
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" || { echo "GATE 6 FAIL: public-hygiene scan" >&2; exit 1; }
```

### Task 1: execute-plan linked-worktree bootstrap names the unlanded-plan case (origin: unlanded-plan-worktree-cherry-pick)

Files:
- `agents/skills/execute-plan/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [x] In the Linked-worktree bootstrap block (the paragraph introducing the recipe before the Step 0.5 gate), append exactly this sentence after the recipe's summary sentence: `When the Step 0.5 gate instead fails with the readiness validator's missing-plan error ("plan file does not exist: <resolved path>"), the plan bytes live on an unlanded authoring branch, not in this worktree: create the execution branch off the default branch and cherry-pick only the plan-authoring commit (the commit that adds the plan file under the resolved plans dir), drop any sibling plan files that rode along in that commit (git rm plus git commit --amend) so the final squash diff stays scoped to the executed plan, and re-run the Step 0.5 gate.` [class: IMPLEMENTATION_REQUIRED]
- [x] Add one companion pin beside the other execute-plan pins: `pin "worktree bootstrap names the unlanded-plan remedy" grep -qF 'cherry-pick only the plan-authoring commit' "$E"`; expect RED before the SKILL.md edit (the span is absent today, verified `grep -c cherry-pick` = 0) and GREEN after [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` (all pins hold, including the new one) [class: REPOSITORY_TEST]

### Task 2: reword the execute-plan telemetry literals out of the shared body (origin: skill-telemetry-jsonl-runtime-name-violation)

Files:
- `agents/skills/execute-plan/SKILL.md`

- [x] In the Telemetry sentence (the paragraph naming the checkpoint record shape), replace the two vendor-suffixed path mentions with: `review-loop's per-run context telemetry log under docs/tmp/review-loop/<branch-slug>/` (was "review-loop's docs/tmp/review-loop/<branch-slug>/context.jsonl") and `the execute-plan and authoring payload telemetry logs under docs/tmp/execute-plan/<plan-slug>/ and docs/tmp/authoring/<plan-slug>/` (was the two literal `context.jsonl` payload paths); keep the pinned-literal-path rationale clause and its "until that payload text is revisited in its own origin" tail unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] In the Phase 4 archive ordering sentence, replace "review-loop's docs/tmp/review-loop/<branch-slug>/context.jsonl and the authoring blueprint's docs/tmp/authoring/<plan-slug>/context.jsonl keep their live paths as their analysis home" with "review-loop's per-run context telemetry log under docs/tmp/review-loop/<branch-slug>/ and the authoring blueprint's payload telemetry log under docs/tmp/authoring/<plan-slug>/ keep their live paths as their analysis home" [class: IMPLEMENTATION_REQUIRED]
- [x] Verify these were the only two `.jsonl`-bearing lines in the file (authoring-time check: `grep -c jsonl` = 2), so Gate 2's absence sweep passes; keep the `docs/tmp/` literal prefixes everywhere (the payload-path convention record) so only the vendor-envelope suffix leaves the shared body [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `PYTHONPATH=scripts python3 -m unittest scripts.test_runtime_capabilities` (35 tests, 0 failures; RED today with the `jsonl` violation, witnessed at authoring) [class: REPOSITORY_TEST]

### Task 3: maintenance Step 6 carry-forward dedupe and the missing Revisions entry (origin: p37-rate-pressure-r1 residuals R1 and R5)

Files:
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [x] In the Step 6 carry-forward sentence (scheduler-turn writer-class bullet), drop the duplicated second `rate_limited_events` mention: the surviving first mention keeps its own introduction and parenthetical (`and \`rate_limited_events\` (the Step 1 child-outcome ingestion appends its entries before Step 6, so the rewrite must carry them)`), and the text that followed the duplicate collapses so the fragment reads exactly: `must carry them) plus the dedup ledger (the ledger is a top-level field the same ingestion writes before Step 6, so the rewrite must carry it the same way)`; change nothing else in the sentence [class: IMPLEMENTATION_REQUIRED]
- [x] Update the pin that quotes the defective span: replace `pin "step 6 carries the dedup ledger" grep -qF 'plus \`rate_limited_events\` and the dedup ledger' "$S"` with `pin "step 6 carries the dedup ledger" grep -qF 'plus the dedup ledger (the ledger is a top-level field' "$S"`, in the same task as the text it pins [class: REPOSITORY_TEST]
- [x] Append one dated entry as the newest `## Revisions` bullet: `- 2026-09-23 (P48 post-execution residuals sweep, docs/plans/2026-09-23-p48-post-execution-residuals-sweep.md Task 3): the revisions log records the state file's additive schema-4 top-level rate_limited_dedup_ledger (the rolling {ts, kind, target} dedup ledger pruned to the same 24-hour window the derived rate_pressure count uses, documented in the State file section's rate_limited_events field paragraph); the field landed with the rate-pressure ingestion and quota scheduling plan (main 394c5098) whose plan freeze shipped it without this log entry.` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` (the updated dedup-ledger pin holds; all others unchanged) [class: REPOSITORY_TEST]

### Task 4: per-site serialized-cap pins (origin: p37-rate-pressure-r1 residual R3)

Files:
- `scripts/check_maintenance_pins.sh`

- [x] Replace the single union pin `pin "serialized cap doubles panel bounds" grep -qF 'while the shaped fan-out cap is 1, panel wall-clock bounds double' "$E"` with four per-site pins, each asserting the doubled-bound phrase co-linear with its paragraph-unique anchor, so partial removal from any one timeout site fails its own pin: [class: REPOSITORY_TEST]
  `pin "serialized cap doubles the intermediate-panel bound" grep -q 'intermediate panels inherit the 20-minute timeout.*panel wall-clock bounds double' "$E"`
  `pin "serialized cap doubles the Step 3.1 bound" grep -q 'wall-clock from Step 3.1 start.*panel wall-clock bounds double' "$E"`
  `pin "serialized cap doubles the fanned-round bound" grep -q 'fanned address wave inherits the Step 3.1 timeout semantics.*panel wall-clock bounds double' "$E"`
  `pin "serialized cap doubles the omnibus bound" grep -q 'If a sequential sub-agent.*panel wall-clock bounds double' "$E"`
- [x] Positive control (authoring-time, verified): each of the four patterns matches today's execute-plan/SKILL.md, so all four pins are GREEN on arrival and each is RED exactly when its own site loses the phrase [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` (four per-site pins hold; the union pin is gone) [class: REPOSITORY_TEST]

### Task 5: zcode.md Variant B precision and comma-splice fix (origin: p37-turn-usage-variant-b-precision)

Files:
- `agents/skills/maintenance/zcode.md`

- [x] Reword the Proxy ratio bullet (the line-79 bullet beginning "Proxy ratio: pinned at ~4 chars/token") to exactly: `Proxy ratio: pinned at ~4 chars/token, and every telemetry record carrying it is labeled an estimate (the record's est_tokens_before / est_tokens_after fields take the est_ prefix for exactly this reason). The store's turn_usage table (verified 2026-09-23 per task notes) carries per-turn token columns, but none tracks context size via per-session sums (a per-row input_tokens value approximately tracks that single request's context, mostly cache-inflated), so the proxy stays the primary estimate and the est_ labeling remains load-bearing.`; this fixes the comma splice (the first independent clause now ends at a period) and narrows the Variant B negative to the sums-based form with the per-row caveat; touch nothing else in the file (the Compaction bullet one line below is frozen and carries the file's one sanctioned em-dash) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: Gate 5 spans in the Validation Commands block (new sums-based span present; old splice absent; `turn_usage` pin token intact for the presence-only pin) [class: REPOSITORY_TEST]

### Task 6: agent-aware F1 bounded reconciliation attempt (origin: agent-aware-contract-review-r1-nonblocking-deferrals, finding F1)

Files:
- none (read-only investigation; the outcome artifact lands in the gitignored session tmp directory)

- [x] In a `mktemp -d` scratch directory with explicit teardown, for each commit in `git rev-list 144cfd33..39193c42` (all three named commits verified reachable, including cb7144a0): create a detached temporary worktree at that commit (`git worktree add --detach "$tmp/wt-<sha>" <sha>`), run the shared-body scan of that commit's tree (`PYTHONPATH=scripts python3 -m unittest scripts.test_runtime_capabilities` inside the worktree; fall back to `python3 scripts/check_review_agent_portability.py` if the capabilities suite does not exist at that commit), record whether the output contains the `zcode` violation, then remove the worktree and the scratch directory on every exit path [class: REPOSITORY_TEST]
- [x] Write the outcome summary (per-commit results, and the verdict: which state, if any, explains the three witnesses' observed RED on "SKILL.md: zcode", or that no committed state does) to `docs/tmp/execute-plan/2026-09-23-p48-post-execution-residuals-sweep/f1-reconciliation.md`; the closeout cites this file in the origin's routing disposition; no edit to any certified plan byte, either way [class: REPOSITORY_TEST]

### Task 7: full validation sweep

Files: none (verification only)

- [x] Execute the WHOLE Validation Commands block from the repository root; record the first failing gate with its exit code if any gate fails, fix, and re-run until the block exits 0 [class: REPOSITORY_TEST]
