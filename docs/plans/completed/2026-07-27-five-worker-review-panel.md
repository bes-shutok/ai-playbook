# Plan: Phase 1 - Five-Worker Review Panel

Follow-up: `docs/plans/2026-07-27-phase-2-review-telemetry.md`

Plan review: `docs/reviews/2026-07-27-plan-review-five-worker-review-panel-r4.md` (latest, not ready)

## Terms

- **Worker**: one launched review sub-agent. Every descendant sub-agent is an additional worker.
- **Lens**: a specialist pattern catalog loaded by a worker.
- **Full panel**: `correctness-completeness`, `testing`, `design-simplicity`, `contract-docs`, and `risk`.
- **Focused panel**: fewer than five workers selected for a narrow review, with an explicit reason.
- **Escalation worker**: one optional sixth worker for an independent high-risk domain or explicit user request.
- **Blocking**: whether a finding must be resolved before the workflow proceeds, independent from severity.
- **Source digest**: SHA-256 of the exact reviewed diff or document content.
- **Active review run**: one review-fix sequence managed by an orchestrator.

## Gist & Examples

Historical review artifacts across personal and company repositories show a common 7-to-10-agent panel, substantial overlap between quality and implementation, overlap between architecture and simplification, and a high discard rate during synthesis. Phase 1 bundles compatible lenses into five workers while preserving lens-level pattern IDs.

| Worker | Lenses | Primary ownership |
|--------|--------|-------------------|
| `correctness-completeness` | `quality`, `implementation` | Runtime correctness, requirements, wiring, compatibility |
| `testing` | `testing` | Test strategy, discriminating assertions, failure paths |
| `design-simplicity` | `architecture`, `simplification` | Dependency direction, maintainability, unnecessary structure |
| `contract-docs` | `documentation`, plus `consistency` for plans and RFCs | Contracts, source-of-truth drift, prose, cross-section consistency |
| `risk` | `security`, plus signaled `concurrency` and `premortem` | Security, ordering, rollout, and operational failures |

Every worker fully expands all Critical findings, all blocking findings, up to five additional non-blocking High/Medium findings, and up to two additional non-blocking Low findings. Remaining credible non-blocking candidates use a compact overflow manifest.

All reviews use `Critical`, `High`, `Medium`, and `Low`. Document inconsistency alone is Low. It becomes Medium only when two plausible implementations and a realistic harmful outcome exist, and High only when following the document is likely to cause wrong normal-path behavior or an incompatible contract.

Findings are grouped Critical, High, Medium, Low. Within a group: blocking first, then blast radius, reachability, confidence, and finding ID.

The initial review uses the selected full panel. After fixes, the next pass uses blind `correctness-completeness` plus every distinct worker that owned a finding or whose domain the fixes affected. One fresh review of the current digest with no unresolved blocking finding ends the loop.

Implementation started before this plan was corrected to the canonical template. Checked items below reflect changes verified in the current working tree; unchecked items are required before completion.

## Evaluation Criteria

**Quality dimensions:**

- Launch cost: a normal full code, plan, or RFC review launches exactly the five named workers.
- Coverage: every worker records loaded lenses and lens-prefixed pattern IDs.
- Safety: review workers do not launch nested review agents; descendants are flattened and count toward the six-worker ceiling.
- Finding quality: all Critical and blocking findings are fully expanded; non-blocking overflow follows the shared budget.
- Severity realism: document inconsistency without demonstrated behavior impact remains Low.
- Presentation: findings are grouped and ordered from Critical to Low with deterministic tie-breakers.
- Readiness: clean and ready means zero unresolved findings with `blocking: true`.
- Cycle cost: post-fix review selects blind correctness plus every owning or affected worker and exits after one fresh blocking-clean digest.
- Compatibility: legacy review Markdown and sidecars validate without rewrites.
- Producer compatibility: every review producer emits the current staging hierarchy and sidecar fields without manual repair.
- Panel integrity: failed, timed-out, duplicated, or wrong-lens workers never satisfy completed full-panel coverage.
- Freshness: every current source digest is a lowercase 64-character SHA-256 and is compared with the current artifact.
- Conservation: Markdown findings, sidecar findings, counts, worker attribution, and readiness fields agree.

**Release gates:**

- Tracked and runtime validator self-tests pass.
- The active runtime validator is byte-identical to the tracked validator.
- Positive fixtures cover a five-worker full panel and legacy artifacts.
- Negative fixtures cover concealed descendants, Critical overflow, severity order, focused-panel metadata, sixth-worker metadata, and blocking/severity independence.
- Negative fixtures cover worker status and lens mismatches, typed fields, finding-budget boundaries, Markdown/sidecar disagreement, invalid digests, and readiness outcomes.
- Each producer template generates a representative artifact that passes hard staging validation.
- Tracked and active runtime review-staging hooks are byte-identical.
- Anonymized self-test fixtures reproduce representative legacy formats without depending on gitignored review files.
- Searches find no active 7-to-10-agent defaults, old document severities, nested persona launches, or two-clear exit rules.
- No historical review artifact changes.
- Changed-file public hygiene, no-em-dash, and `git diff --check` pass.
- One fresh five-worker review of the implementation has no unresolved blocking findings.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope:

**Skill policy and producers:**

- `agents/skills/review-agents/SKILL.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/review-agents/severity-calibration.md`
- `agents/skills/review-agents/premortem.md`
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/rfc-design/SKILL.md`
- `agents/skills/rfc-design/references/eval-cases.md`
- `agents/skills/review-confluence-doc/SKILL.md`
- `agents/skills/premortem/SKILL.md`

**Cycle consumers and shared staging:**

- `agents/skills/review-staging/SKILL.md`
- `agents/skills/review-loop/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/agent-logs.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/receiving-code-review/SKILL.md`
- `agents/skills/using-skills/SKILL.md`
- `agents/skills/how-to-write-skills/SKILL.md`

**Validation and documentation:**

- `scripts/validate_review_staging.py`
- `~/.ai-playbook/scripts/validate_review_staging.py` *(runtime deployment only)*
- `cursor/hooks/review-staging-gate.sh`
- `~/.cursor/hooks/review-staging-gate.sh` *(runtime deployment only)*
- `scripts/scan-public-hygiene.sh`
- `~/.ai-playbook/scripts/scan-public-hygiene.sh` *(runtime deployment only)*
- `~/.ai-playbook/runtime/phase1-review-baseline.sha256` *(temporary runtime guard)*
- `README.md`
- `projects/.ai-playbook/agent-runtime-layout.md`
- `docs/plans/2026-07-27-five-worker-review-panel.md`
- `docs/plans/2026-07-27-phase-2-review-telemetry.md`

**Plan-related extension**; implementation and review may change an unlisted file only when it is causally required to complete a listed policy migration, fix a regression introduced here, or update a contract changed by this plan. Add repeatedly affected paths to the explicit list.

**Out of scope; reject unless plan-related:**

- Historical review Markdown and sidecars; immutable compatibility inputs only.
- Product code under personal and company project roots; audit inputs only.
- Strict token telemetry, durable cross-session lineage, and historical aggregation; Phase 2.
- Unrelated review lens catalog rewrites.

## Design Invariants

1. `review-panel-selection.md` is the single source for panel composition, focused selection, escalation, launch accounting, and worker-to-lens ownership.
2. `severity-calibration.md` is the single source for severity, blocking, ordering, and finding budgets.
3. `review-staging` is the single source for the staging hierarchy and current sidecar fields.
4. Worker bundling preserves lens provenance and existing pattern IDs.
5. Blocking controls readiness independently from severity.
6. Historical review artifacts remain immutable.
7. Follow-up review is independent work, not orchestrator self-approval.
8. Strict telemetry and durable lineage remain Phase 2 concerns.

## Validation Commands

```bash
python3 -m py_compile scripts/validate_review_staging.py
python3 scripts/validate_review_staging.py --selftest
python3 ~/.ai-playbook/scripts/validate_review_staging.py --selftest
cmp -s scripts/validate_review_staging.py ~/.ai-playbook/scripts/validate_review_staging.py
cmp -s cursor/hooks/review-staging-gate.sh ~/.cursor/hooks/review-staging-gate.sh
cmp -s scripts/scan-public-hygiene.sh ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/scan-public-hygiene.sh --changed-from main
shasum -c ~/.ai-playbook/runtime/phase1-review-baseline.sha256

! rg -n 'default (7|8|9)-agent|default (7|8|9) agent|7 default agents|8 shared agents|9-agent default|up to 10 agents|8 shared sub-agents' \
  agents/skills/ README.md projects/.ai-playbook/agent-runtime-layout.md
! rg -n 'Critical/Suggestion/Advisory|2-3 findings max per agent|2-3 findings per persona|two consecutive clear|Launch each persona as a distinct thinking thread' \
  agents/skills/

rg -n 'correctness-completeness|testing|design-simplicity|contract-docs|risk' \
  agents/skills/review-agents/review-panel-selection.md
rg -n 'Critical|High|Medium|Low|blast_radius|reachability|confidence' \
  agents/skills/review-agents/severity-calibration.md

test -z "$(git diff --name-only main...HEAD -- '*/docs/history/reviews/**')"
bash ~/.ai-playbook/scripts/check-no-em-dash.sh touched
git diff --check
```

### Task 1: Define the five-worker policy and migrate producers

Files:

- `agents/skills/review-agents/SKILL.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/review-agents/severity-calibration.md`
- `agents/skills/review-agents/premortem.md`
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/rfc-design/SKILL.md`
- `agents/skills/rfc-design/references/eval-cases.md`
- `agents/skills/review-confluence-doc/SKILL.md`
- `agents/skills/premortem/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/using-skills/SKILL.md`
- `agents/skills/how-to-write-skills/SKILL.md`
- `README.md`
- `projects/.ai-playbook/agent-runtime-layout.md`
- `docs/plans/2026-07-27-phase-2-review-telemetry.md`

- [x] Define the recommended five workers and their lens ownership in `review-panel-selection.md`.
- [x] Define focused panels, one sixth-worker escalation, descendant accounting, and the no-nested-review rule.
- [x] Define Critical/High/Medium/Low consequence tiers, document calibration, deterministic ordering, and the finding budget.
- [x] Convert premortem personas into reasoning sections inside the `risk` worker for review mode.
- [x] Replace producer-specific panel counts and caller-specific document severities with shared-policy references.
- [x] Preserve strict telemetry and durable lineage as a separate Phase 2 plan.
- [x] Run the stale-policy searches across every file in this task; expect no active old defaults or severities.
- [x] Commit: `review: adopt five-worker panel policy`

### Task 2: Enforce staging, validation, and revision-aware cycles

Files:

- `agents/skills/review-staging/SKILL.md`
- `agents/skills/review-loop/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/agent-logs.md`
- `agents/skills/receiving-code-review/SKILL.md`
- `scripts/validate_review_staging.py`
- `~/.ai-playbook/scripts/validate_review_staging.py` *(runtime deployment only)*

- [x] Add worker/lens attribution, descendant declarations, focused and escalation metadata, source digest, tangible consequence fields, ordered severity groups, and overflow to current staging output.
- [x] `run_selftest#current_five_worker_clear`; given a full five-worker panel with empty descendant lists and all severity groups, expects hard validation success.
- [x] `run_selftest#concealed_descendant`; given a worker that declares an unflattened child launch, expects hard validation failure.
- [x] `run_selftest#critical_overflow`; given a non-blocking Critical candidate in overflow, expects hard validation failure.
- [x] `run_selftest#severity_order`; given Low before High, expects ordering validation failure.
- [x] Preserve legacy parsing and verify the existing r1/r2 plan-review artifacts validate.
- [x] Replace repeated-clear cycle rules with initial full panel, targeted owner/affected follow-up, and one fresh blocking-clean exit.
- [x] `run_selftest#focused_panel_reason`; given a focused panel without `selection_reason`, expects hard validation failure.
- [x] `run_selftest#sixth_worker_escalation`; given six launches without `escalation_reason`, expects hard validation failure.
- [x] `run_selftest#blocking_independence`; given blocking Low and non-blocking Medium findings, expects readiness to block only on the Low.
- [x] Run -> expect GREEN: `python3 scripts/validate_review_staging.py --selftest`.
- [x] Deploy `scripts/validate_review_staging.py` to `~/.ai-playbook/scripts/validate_review_staging.py`.
- [x] Run -> expect GREEN and byte parity: runtime self-test plus `cmp -s`.
- [x] Commit: `review: enforce five-worker staging and cycles`

### Task 3: Close the current contract and complete the local release

Files:

- All files listed in Tasks 1 and 2
- `cursor/hooks/review-staging-gate.sh`
- `~/.cursor/hooks/review-staging-gate.sh` *(runtime deployment only)*
- `scripts/scan-public-hygiene.sh`
- `~/.ai-playbook/scripts/scan-public-hygiene.sh` *(runtime deployment only)*
- `~/.ai-playbook/runtime/phase1-review-baseline.sha256` *(temporary runtime guard)*
- `docs/plans/2026-07-27-five-worker-review-panel.md`

- [x] Inspect the full per-file diff and remove contradictory worker, severity, readiness, or cycle instructions.
- [x] Run every command under `## Validation Commands`; expect green except the known pre-existing full-repository hygiene finding outside this task.
- [x] Run a changed-file public-hygiene scan; expect zero findings in this plan's files.
- [x] Verify `git diff --name-only` contains no historical review artifacts.
- [x] Create an isolated worktree that is not the live skill registry; prepare every remaining tracked change there and do not deploy runtime files yet.
- [x] Before remaining Task 3 edits, record SHA-256 digests for every current file under the resolved `reviews_dir` in `~/.ai-playbook/runtime/phase1-review-baseline.sha256`; this guard protects Task 3 only and does not claim retroactive coverage of Tasks 1 and 2.
- [x] Extract neutral payload builders and one self-test function per contract family; keep `run_selftest()` as a dispatcher.
- [x] Add `run_selftest#producer_artifacts`, `#readiness_independence`, `#full_panel_completion`, `#typed_current_schema`, `#finding_conservation`, `#finding_budget`, and `#source_digest`; run them before implementation and expect RED.
- [x] For plan, RFC, and document reviews, define the digest as SHA-256 of the exact reviewed UTF-8 bytes; for code review, define it as SHA-256 of the exact stored diff bytes.
- [x] Require each orchestrator to supply the expected digest and source kind to the validator; fail on mismatch, not only invalid syntax.
- [x] Replace legacy producer output examples with current Metadata, Worker/Lens statistics, tangible finding fields, ordered `Critical`/`High`/`Medium`/`Low` groups, and `#### F<N>` findings.
- [x] Define a blocking decision procedure with code, plan, RFC, and document examples; blocking means remediation is required before safe execution or release.
- [x] Require each base worker exactly once with its required lenses and completed status; count failed and timed-out rows as launches but never completed coverage.
- [x] Enforce typed fields, finding-budget boundaries, Markdown/sidecar conservation, and source-digest authority.
- [x] Add anonymized in-selftest legacy code, plan, RFC, and document shapes so compatibility does not depend on gitignored local artifacts.
- [x] Add `scan-public-hygiene.sh --changed-from <ref>` with self-tests so final hygiene checks cover only changed public files while still applying the local deny-pattern file.
- [x] Run all new validator and hygiene tests in the isolated worktree; expect GREEN.
- [x] Confirm no review workflow is active. Back up the active runtime validator and hook, then fast-forward the complete tracked change into the live registry in one controlled cutover.
- [x] Install the validator, hook, and hygiene scanner through same-directory temporary files plus atomic rename; run installed-path canaries and parity checks.
- [x] If any installed-path canary or parity check fails, atomically restore all runtime backups and stop.
- [x] Run the fresh plan review with the tracked validator before enabling the strict installed hook as the final activation step.
- [x] Run `shasum -c ~/.ai-playbook/runtime/phase1-review-baseline.sha256`; expect every Task 3 baseline artifact unchanged, then remove the runtime guard.
- [x] Run every command under `## Validation Commands`; expect green except the documented pre-existing full-repository hygiene finding outside this plan.
- [x] Run a fresh five-worker review because the fixes affect every worker’s staging or readiness contract; expect zero unresolved blocking findings.
- [x] Record the review staging document and valid current sidecar.
- [x] Commit: `review: close five-worker review contract`
