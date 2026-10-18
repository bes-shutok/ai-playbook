# Plan: Plan-scope gist surface (audit Part 5 item 5a, admission-protocol shape)

Backlog origin: docs/history/backlog/2026-10-10-plan-scope-gist-surface.md (the PLAN-PROMPTS entry `plan-scope-gist-surface` carries the operator "next" + discipline-instruction walk; the audit's Part 5 item 5a)
Driving force: automation-neutral
Design input: docs/maintenance/machinery-blocker-audit-2026-10-09.md (Part 5 item 5a); the admission protocol (Part 5 item 2 and its reconciliation); the witnessed rejection of record (the strictness plan certified at r6 and rejected by the operator)
Plan review record: the staging series docs/history/reviews/2026-10-10-plan-review-plan-scope-gist-surface-r*.md (created by this plan's review loop, r1 onward; the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 1h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-10-plan-scope-gist-surface.md (session sess_5c51c846-299a-4dfe-a00c-4238d7883663)

## Terms

- The gist surface: when authoring produces a plan, the gist and budget are emitted at the plan-created, before-first-review transition in the plans skill and before the first review round in scheduled authoring; the authoring closeout also carries the same content. The five gist lines are the plan title, TLDR, Before, After, and Edge cases, each copied or concisely summarized from the matching source field without adding claims.
- Report channels: the scheduled authoring child uses the pre-review handoff, Cycle gate readiness report, and final report; in-session authoring emits at the plans skill's plan-created, before-first-review transition and its existing closeout/report instruction. The pre-review emission adds no gate or state-schema change.
- Referral handling is out of scope for this report-surface change. The existing interruption rules do not define an active-plan scope-change route; a separate plan must establish that contract before the skill claims it.
- The promotion arm: one further witnessed certified-then-rejected rejection after this surface lands (a plan certified through the review loop and then rejected by the operator, witnessed in the records) records a proposed threshold for a separate activation contract; the second witness alone does not activate a stop, and no stop exists in this surface.

## Why

The audit's Part 5 item 5a wants the operator to see a plan's gist and budget before review rounds run, to prevent the witnessed waste class: a plan certified at r6 and then rejected by the operator. The literal shape (a per-plan operator approval gate) fails the audit's own admission protocol - a blocking human gate whose false-positive cost is the entire autonomous loop, forbidden by the never-block invariant and directive D-6, for a catch that has occurred exactly once. The advisory shape delivers the gist and budget before review starts through the scheduled report paths and the named in-session plan-created transition, and records the promotion criterion without adding a stop today. Active-plan referral handling is deferred because the current re-entry rules do not define it.

## Gist & Examples

TLDR: authoring closeout reports gain a defined five-line gist and declared budget; active-plan referral behavior is deferred to a separate contract change; a second witnessed certified-then-rejected rejection is a proposed threshold only; a separate, explicitly approved activation contract must land before any stop can exist.

Before: the operator sees a landing commit message and a queue; the strictness-class waste (certify-then-reject) is invisible until the rejection lands. In-session authoring has no named gist emission at the plan-created, before-first-review transition.

After: the gist and declared budget are reported at the in-session plan-created, before-first-review transition, before scheduled authoring's first review, and again at authoring closeout; active-plan referral handling remains unchanged and is not claimed by this plan; the proposed threshold sits in the text; a separate activation contract and approval are required before any stop can exist.

Edge cases: an unattended closeout emits the same report content - nothing requires an operator to be present (directive D-6 intact: the report never stops the loop); a plan with no declared budget line reports the budget as undeclared (the declared-line-is-optional grammar); a rejected plan's gist stays in the closeout report of record at emit time, while the promotion arm's durable evidence trail is the rejected/ egress plus the plan-review record series (which the Assumptions name).

## Outcome

The gist behavior carries the plan gist and budget through the pre-review and closeout report paths with zero added stop behavior and zero state-schema change; active-plan referral behavior is explicitly deferred; the proposed threshold (one further witnessed certified-then-rejected rejection) is recorded with its evidence trail; the witness does not activate a stop, which requires a separately approved and landed activation contract. A separate Task 3 execution-recovery slice updates existing archive eligibility/evidence checks so the completed dated plan can pass closeout; it does not change the gist behavior's advisory contract.

Gist-surface gate delta: report-channel text only - two report sections gain their content lines and one paragraph records the proposed threshold and the separate activation-contract requirement; no new approval gate, ceremony, or stop behavior is added, and the report sections this extends are named per the admission rule. Separate Task 3 recovery delta: the existing archive gate accepts valid dated plan filenames and validates the staged archive evidence it already consumes; this is a narrowly scoped change to existing closeout eligibility, covered by dedicated regressions and required to archive this plan.

## Assumptions

- The five report lines use the plan title and its TLDR, Before, After, and Edge cases fields, one concise line per field; these fields are required by the plans template, so no new summary source or computation is introduced. Basis: the plans skill's Gist & Examples template.
- The declared budget line reports verbatim when present and as "undeclared" when absent, matching the plans skill's declared-line-is-optional grammar (a plan without the line keeps configured semantics, so there is nothing to report). Basis: the budget-line grammar and the review-loop budget plan's optional-member rule.
- Active-plan referral handling is deferred: the existing re-entry and interruption rules do not establish the named-plan scope-change behavior. Backlog: `docs/history/backlog/2026-10-10-plan-referral-runtime-contract-gap.md`.
- The promotion criterion's evidence trail is the plan-review record series and the operator's rejection (a plans/rejected/ egress or an equivalent recorded decision): a "witnessed certified-then-rejected rejection" means a plan whose staging series certifies clean and whose operator rejection is recorded, and the strictness-plan rejection (certified r6, rejected, archived to rejected/) is the first witness this plan counts. Basis: the witnessed incident of record and the rejected-egress archive shape.
- Residual accepted: an operator may not read a nonblocking report during an unattended stretch; reporting before review still makes the information available through the existing report path without adding a stop. Basis: the advisory-first admission posture.

Decision points requiring a grill: none remain (the operator's "next" with the discipline instruction pre-authorized the entry; the entry fixes the advisory shape, the promotion criterion, and the rejected alternatives including the blocking-gate shape the admission protocol forbids).

## Standing constraints

- The gist behavior remains report-channel text only: no state-schema change, no new approval gate, no new ceremony, and no stop behavior of any kind before the promotion criterion's second witness exists; directive D-6 intact. Task 3 is the separately scoped archive-closeout recovery described above.
- The pins covering the Cycle gate, scheduled report spans, and plans skill pre-review transition stay green: extend beside them, re-aim only if wording moves them.
- Deploy truth: the skill edits reach their runtime homes at this plan's merge-locked landing (the landing is the deploy).
- The full battery stays green at every task landing (pins, parallel-work regressions, liveness, em-dash, hygiene); no machine-specific absolute paths; nothing pushed to origin; branch rebased onto current main at each fold with the task-start currency check and the stop-and-report arm.
- Rollback arm: revert the offending task's commit; the surface is report text, so a revert restores the prior reports exactly with no data or schema residue.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the pre-review and closeout report channels carry the gist and budget as prescribed, the promotion criterion names its first witness and its evidence trail.
- regression safety: the pins suite green (Cycle gate and report spans untouched or re-aimed beside provenance); the battery green.
- scope discipline: the gist behavior stays limited to `agents/skills/maintenance/template-authoring.md`, `agents/skills/maintenance/templates-CHANGELOG.md`, `agents/skills/maintenance/SKILL.md`, `agents/skills/plans/SKILL.md`, and `scripts/check_maintenance_pins.sh`. Execution uncovered a separate archive-closeout blocker; its smallest validated workaround is included as a clearly separate execution-recovery slice in Review Scope: `agents/skills/execute-plan/runtime-contract.md`, `scripts/done_sweep_gates_lib.py`, `scripts/execute_plan_runtime.py`, their focused tests, and the document-registry receipt. Recovery backlog records remain independent open items and are not claimed as gist-plan outcomes.

**Done when:**
- Every span check in `## Validation Commands` holds on the executed tree.
- The battery is green.

**Ship when:**
- The first post-landing scheduled pre-review handoff and in-session plan-created transition each emit the defined five-line gist and budget before review starts, and the first authoring closeout carries the same content; the promotion criterion remains recorded in the landed maintenance text. Evidence owners: the scheduled authoring pre-review handoff, the in-session authoring session record, the maintenance authoring closeout report, and the landed maintenance text. Closure condition: the first post-landing scheduled and in-session authoring runs show gist and budget before their first review; the first closeout carries both; the landed text contains the promotion criterion. Follows from the executed tree. [class: OPERATIONS_FOLLOW_UP]

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/template-authoring.md` (edit scheduled pre-review handoff and final-report instructions to require the gist and budget)
- `agents/skills/maintenance/SKILL.md` (edit Cycle gate readiness and in-session authoring closeout/report instructions; document the promotion paragraph)
- `agents/skills/plans/SKILL.md` (add the gist output at the plan-created, before-first-review transition in the in-session authoring flow)
- `agents/skills/maintenance/templates-CHANGELOG.md` (record the scheduled template behavior change)

**Docs:**
- `docs/history/backlog/2026-10-10-plan-scope-gist-surface.md` (origin row deleted in the same completion pass)
- `docs/maintenance/document-registry.md` (archive and origin-disposition receipts)
- Execution blockers recorded separately in `docs/history/backlog/2026-10-10-execute-plan-rebase-after-surface-refactor.md`, `docs/history/backlog/2026-10-10-extract-archive-evidence-assembly.md`, `docs/history/backlog/2026-10-10-plan-scope-receipt-currency.md`, `docs/history/backlog/2026-10-10-promotion-threshold-activation-contract.md`, `docs/history/backlog/2026-10-10-review-selector-kind-suffix-alias.md`, `docs/history/backlog/2026-10-10-code-review-panel-worker-capacity.md`, and `docs/history/backlog/2026-10-10-done-lock-live-owner-blocks-plan-closeout.md` (independent open records, not gist-plan deliverables)

**Execution evidence (tracked fixture; retained with the plan):**
- `scripts/fixtures/authoring-gist-sample.md` (tracked realistic sample for in-session and scheduled pre-review and closeout output)

**Tests:**
- `scripts/check_maintenance_pins.sh` (add section-scoped pins for pre-review reporting, closeout reporting, and the promotion criterion)
- `scripts/check_authoring_gist_sample.py` (compare sample report fields with the source plan; verify all five channels, first-review ordering, and the undeclared-budget continuation case)

**Execution recovery (separate from gist behavior):**
- `agents/skills/execute-plan/runtime-contract.md` (accept dated plan filenames used by archive closeout)
- `scripts/done_sweep_gates_lib.py` and `scripts/execute_plan_runtime.py` (validate staged archive evidence and resolve dated plan identity)
- `scripts/test_done_sweep_gates_lib.py` and `scripts/test_execute_plan_runtime.py` (focused regression coverage)

**Separate blocker records (open, not outcomes of the gist plan):**
- `docs/history/backlog/2026-10-10-code-review-panel-worker-capacity.md`
- `docs/history/backlog/2026-10-10-done-lock-live-owner-blocks-plan-closeout.md`
- `docs/history/backlog/2026-10-10-execute-plan-rebase-after-surface-refactor.md`
- `docs/history/backlog/2026-10-10-extract-archive-evidence-assembly.md`
- `docs/history/backlog/2026-10-10-plan-scope-receipt-currency.md`
- `docs/history/backlog/2026-10-10-promotion-threshold-activation-contract.md`
- `docs/history/backlog/2026-10-10-review-selector-kind-suffix-alias.md`
- `docs/history/backlog/2026-10-09-scheduler-turn-boundary-stops-live-lanes.md` (modified during blocker capture)

**Read-only (referenced, never edited):**
- `docs/maintenance/machinery-blocker-audit-2026-10-09.md` (Part 5 item 5a; the admission protocol)
- `docs/history/plans/rejected/` (the strictness-plan rejection, the first promotion witness)

**Receipts:**
- Origin row: `docs/history/backlog/2026-10-10-plan-scope-gist-surface.md` was deleted in this completion pass; `docs/maintenance/document-registry.md` records the completed plan and origin disposition.
- Prompt entry: docs/history/backlog/PLAN-PROMPTS.md `## plan-scope-gist-surface` (frozen under docs/tmp/authoring-claims/2026-10-10-plan-scope-gist-surface.md; pruned by the landing rider with the prune receipt)

## Validation Commands

**Production:**
```bash
bash scripts/check_maintenance_pins.sh   # report-contract and promotion-criterion pins, including the plans pre-review transition, pass exactly once
```

**Tests:**
```bash
python3 scripts/test_plan_review_boundary_examples.py   # exit 0
python3 scripts/test_authoring_plans_liveness.py   # exit 0
python3 -m pytest -q scripts/test_done_sweep_gates_lib.py   # exit 0; full archive-evidence suite
python3 scripts/test_execute_plan_runtime.py   # exit 0; dated plan identity recovery
python3 scripts/doc_registry_validator.py validate   # exit 0 hard findings; existing warning inventory is reported
bash scripts/check-no-em-dash.sh file agents/skills/maintenance/SKILL.md   # exit 0
bash scripts/check-no-em-dash.sh file agents/skills/maintenance/template-authoring.md   # exit 0
bash scripts/check-no-em-dash.sh file agents/skills/maintenance/templates-CHANGELOG.md   # exit 0
bash scripts/check-no-em-dash.sh file agents/skills/plans/SKILL.md   # exit 0
bash scripts/check-no-em-dash.sh file agents/skills/execute-plan/runtime-contract.md   # exit 0
bash scripts/check-no-em-dash.sh file scripts/done_sweep_gates_lib.py   # exit 0
bash scripts/check-no-em-dash.sh file scripts/execute_plan_runtime.py   # exit 0
bash scripts/check-no-em-dash.sh file scripts/check_maintenance_pins.sh   # exit 0
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh   # exit 0 from the repo root
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh --files scripts/check_maintenance_pins.sh   # exit 0 from the repo root
bash -c 'touched_docs=(); while IFS= read -r -d "" f; do touched_docs[${#touched_docs[@]}]="$f"; done < <(git diff main --name-only --diff-filter=ACMR -z -- docs); bash ~/.ai-playbook/scripts/scan-public-hygiene.sh --files "${touched_docs[@]}"'   # exit 0; every changed tracked doc
python3 scripts/check_authoring_gist_sample.py   # exit 0 from a clean checkout; tracked fixture, source fields, five report channels, first-review ordering, and undeclared-budget fallback
```

### Task 1: the pre-review and closeout report channels carry the gist and budget

Files:
- agents/skills/maintenance/template-authoring.md
- agents/skills/maintenance/SKILL.md
- agents/skills/maintenance/templates-CHANGELOG.md
- agents/skills/plans/SKILL.md
- scripts/check_maintenance_pins.sh
- scripts/check_authoring_gist_sample.py
- scripts/fixtures/authoring-gist-sample.md (tracked test fixture)

- [x] Emit the defined five-line gist and budget at the plan-created, before-first-review transition in the in-session plans authoring flow and before the scheduled author's first review round. [class: IMPLEMENTATION_REQUIRED]
- [x] Include the same gist and budget in scheduled Cycle gate readiness and final reports, and in the in-session authoring closeout report. [class: IMPLEMENTATION_REQUIRED]
- [x] Define the five lines as the title, TLDR, Before, After, and Edge cases, each copied or concisely summarized from its matching plan field without adding claims; report the declared execution budget verbatim or "undeclared" when absent. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep all gist and budget content advisory: it never blocks a lane or stops the loop (directive D-6 intact). Add section-scoped pins for each required report path, including the plans skill's in-session pre-review transition. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the pins suite, the em-dash scan over the touched path, and the hygiene scan green, and land this task as its own commit. [class: REPOSITORY_TEST]

### Task 2: the promotion criterion recorded

Files:
- agents/skills/maintenance/SKILL.md
- scripts/check_maintenance_pins.sh

- [x] Record one further witnessed certified-then-rejected rejection as a proposed threshold for a separate activation contract; the second witness alone does not activate a stop. [class: IMPLEMENTATION_REQUIRED]
- [x] Name the strictness-plan rejection as the first witness, using its rejected/ egress as evidence; a stop requires a separately approved and landed activation contract naming its owner, authoritative witness, activation action, and reader. Add a section-scoped pin for the proposed threshold, first witness, evidence, and activation boundary. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full verification battery on the executed tree: the pins suite, the parallel-work regressions suite (`python3 scripts/test_plan_review_boundary_examples.py`), the liveness test, the em-dash scan over the touched path, and the hygiene scan; record each exit code in the session log and fix any red span before reporting the task done. [class: REPOSITORY_TEST]

### Task 3: recover archive closeout for dated plans (execution blocker)

Primary class anchors:
- `_pre_archive_gate` in `scripts/execute_plan_runtime.py`
- `_derive_archived_plans` in `scripts/done_sweep_gates_lib.py`
- `_archive_text_at_index_or_worktree` in `scripts/done_sweep_gates_lib.py`

Files:
- agents/skills/execute-plan/runtime-contract.md
- scripts/execute_plan_runtime.py
- scripts/done_sweep_gates_lib.py
- scripts/test_execute_plan_runtime.py
- scripts/test_done_sweep_gates_lib.py
- docs/maintenance/document-registry.md

- [x] Let pre-archive validation accept either the bare plan slug or a valid dated `<YYYY-MM-DD>-<plan_slug>.md` filename while preserving fail-closed path and resume-record checks. [class: IMPLEMENTATION_REQUIRED]
- [x] Let archive evidence resolve the dated plan identity and read the exact staged archive bytes; refuse staged/worktree mismatch and surface archive tree listing failures with path-specific evidence. [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the dated-identity and archive evidence paths with `python3 scripts/test_execute_plan_runtime.py` and `python3 -m pytest -q scripts/test_done_sweep_gates_lib.py`; both pass. [class: REPOSITORY_TEST]
- [x] Record the completed plan and origin disposition in the document registry. [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-10-plan-scope-gist-surface.md`: implemented by this plan; the file is deleted in the same completion pass. The separate active-plan referral contract remains open at `docs/history/backlog/2026-10-10-plan-referral-runtime-contract-gap.md`.
- The execution-recovery code above unblocked archive closeout; its rebase, review-capacity, lock, archive-evidence, receipt-currency, promotion, and selector blockers remain separate open backlog items and are not covered by the gist plan.
