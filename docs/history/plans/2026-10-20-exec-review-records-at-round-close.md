# Plan: Produce and validate execution review records at round close

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-20-exec-review-records-produced-at-round-close.md`
Driving force: efficiency
Plan review record: the staging series `.ai-playbook/reviews/2026-10-20-plan-review-exec-review-records-at-round-close-r*.md` (the highest rN for this source-plan path is authoritative).
Authoring claim: `docs/tmp/authoring-claims/2026-10-20-exec-review-records-produced-at-round-close.md` (session `01a15484-176a-70a1-814d-785fd68e1975`)
Execution budget: 1.5h total, largest task 1.0h

## Terms

- **Execution review record:** the Phase 3 review Markdown and `.stats.json` sidecar for one execute-plan review round.
- **Findings-bearing record:** a review record containing one or more findings and their triage data.
- **Plans-egress guard:** the existing landing check that verifies an execution receipt binds to the exact archived plan bytes.
- **Phase 4 archive check:** the existing `check-archive` validation of the archive commit, run before the done handoff.
- **Execution receipt:** the `-plan-review-<slug>-exec-r<N>.md` file that carries the SHA-256 digest required by the plans-egress guard.
- **Round close:** the Step 3.5 decision to proceed to Phase 4 after either the fresh blocking-clean exit or a satisfied recorded residual-acceptance policy; rounds that return to Step 3.1 are not receipt-production points.
- **Staging validator:** `scripts/validate_review_staging.py`, which validates the record and its sidecar.

## Why

Phase 3 can close a review round before the staging validator checks its record and before the plans-egress execution receipt exists. The first mechanical checks then happen during landing, after the archive commit, causing coupled repair cycles and a refused landing. The Phase 4 disposition then changes the plan bytes, so the receipt must be refreshed before the archive check. Findings-bearing records also lack a producer path, so authors hand-build their Markdown and sidecar against validator fixture shapes.

## Gist & Examples

TLDR: validate review artifacts before triage and produce the execution receipt after Phase 3 selects an exit, reducing repair cycles and landing retries through earlier feedback.

For example, Step 3.1 validates every staged record before Step 3.2, while Step 3.5 writes the initial execution receipt only after it selects a Phase 4 exit. Phase 4 refreshes it after appending the archive disposition and before its archive check. Both the blocking-clean and satisfied residual-acceptance exits produce a receipt; a continue decision does not. A producer helper creates findings-bearing Markdown and sidecar from structured review data and checks the result with the existing validator.

## Outcome

Each Phase 3 round has a validator-approved review pair before triage proceeds, and every Phase 3 exit to Phase 4 has an execution receipt that Phase 4 refreshes to the archived plan bytes before its archive check. Findings-bearing pairs can be produced through a repeatable helper.

- Existing landing gates continue to verify the receipt and migrated review evidence.
- `scripts/regenerate_review_sidecar.py` remains a repair-only tool and never invents a findings-bearing record.
- No new blocking gate, validator, lock, ledger, or refusal class is introduced.

Gate delta: no new refusal class or blocking check. Step 3.1 already requires the staging document to satisfy its format and parsing criterion; this plan names the existing validator as mechanical evidence for that same criterion at the same boundary. Receipt production follows the existing Step 3.5 exit decision and supplies the existing landing check.

## Assumptions

- The existing validator is the source of truth for record and sidecar grammar. A probe of a current findings-bearing record passed with `python3 scripts/validate_review_staging.py <record>` and ended with `OUTCOME: pass`.
- The validator's `_current_finding` and `_current_findings_markdown` fixture builders are the documented shape reference for the producer helper; the helper must validate its output through the public CLI rather than changing validator rules.
- The egress guard expects a dated `*-plan-review-<plan-slug>-exec-r<N>.md` record with the archived plan bytes' SHA-256. Step 3.5 writes the initial receipt after selecting either Phase 4 exit; Phase 4 refreshes it after appending the archive disposition and before `check-archive`; done closeout verifies and migrates the refreshed receipt.
- Lesson 107 already describes the execution receipt and records the latest landing refusal. This plan updates it to identify the terminal Step 3.5 exit as the production point and Phase 4 as the refresh point; the done skill records that closeout verifies and migrates the refreshed receipt.
- Sources inspected: the origin backlog item, `docs/history/backlog/PLAN-PROMPTS.md`, `agents/skills/execute-plan/SKILL.md`, `agents/skills/done/SKILL.md`, `docs/maintenance/development_lessons.md` lesson 107, `scripts/validate_review_staging.py`, `scripts/regenerate_review_sidecar.py`, and the plans-egress fixture in `scripts/test_land_squash.py`.

Decision points requiring a grill: none remain. The maintenance authoring entry pre-authorizes the recommended scope.

## Standing constraints

- Run `python3 scripts/validate_review_staging.py --hard <record>` for each round record before Step 3.2; proceed only when the command succeeds and its final outcome is `OUTCOME: pass`.
- Derive the producer's record and sidecar shapes from the validator's current grammar and validate generated output with the existing CLI.
- Keep `regenerate_review_sidecar.py` repair-only and preserve its zero-findings posture.
- When Step 3.5 selects Phase 4 after either the blocking-clean exit or a satisfied recorded residual-acceptance exit, write one execution receipt with the final Phase 3 plan digest; when Step 3.5 continues to another round, write none. Keep the existing filename and digest contract unchanged.
- In Phase 4, refresh the receipt after appending the archive disposition and before committing the archive or running its `check-archive`; hash the exact archived plan bytes.
- During done closeout, verify and migrate the refreshed receipt without changing its digest.
- Do not add a new gate, validator mode, lock, ledger, or landing refusal class.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: malformed or incomplete review pairs are found before triage, and the receipt binds to the exact plan bytes later archived.
- Usability: findings-bearing pairs have a repeatable producer that returns validator-approved artifacts.
- Maintainability: validation grammar remains owned by the existing validator, and receipt production is tied to the existing Phase 3 exit decision.

**Done when:** Step 3.1 validates each round record before Step 3.2; the producer helper creates and validates a findings-bearing Markdown/sidecar pair; Step 3.5 writes the correctly named receipt after either Phase 4 exit and writes none on continuation; Phase 4 refreshes the receipt to final archive bytes before `check-archive`; the done skill verifies and migrates it and lesson 107 names both production and refresh points; existing egress and sweep behavior is unchanged.

**Ship when:** none; this is a repository-local workflow and tooling update.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope.

**Production code:**
- `scripts/produce_exec_review_record.py` - new findings-bearing record producer.
- `scripts/validate_review_staging.py` - existing validator and fixture grammar; only change if a narrow shared formatting seam is needed by the helper.
- `scripts/regenerate_review_sidecar.py` - preserve its repair-only and zero-findings behavior.

**Docs:**
- `agents/skills/execute-plan/SKILL.md` - Step 3.1 verification gate and Step 3.5 exit decision.
- `agents/skills/plans/SKILL.md` - Phase 4 refreshes the receipt after the disposition edit and before archive `check-archive`.
- `agents/skills/done/SKILL.md` - closeout verifies and migrates the Phase 4 refreshed receipt.
- `docs/maintenance/development_lessons.md` - update lesson 107 to name the round-close producer.
- `.ai-playbook/reviews/` - generated execution receipt under the existing reviews home.

The plans skill's authoring landing rider owns deleting the source backlog row and pruning the served prompt entry; these authoring records are not execute-plan implementation files.

**Out of scope:**
- Changes to the plans-egress guard, landing sweep, or their refusal behavior.
- New validation rules or sidecar schema fields.
- Changes to ordinary code-review record naming or review-panel selection.
- Turning `regenerate_review_sidecar.py` into a findings authoring tool.

## Validation Commands

- Run `python3 scripts/validate_review_staging.py --selftest` and focused producer-helper tests for findings-bearing and empty records.
- Run `python3 scripts/validate_review_staging.py <record>` on every generated fixture and confirm each ends with `OUTCOME: pass`.
- Run the plans-egress fixture proving the Step 3.5 receipt name and digest satisfy the unchanged guard contract.
- Run `python3 scripts/plan_readiness.py docs/history/plans/2026-10-20-exec-review-records-at-round-close.md` after the final plan bytes are written.
- Run the public hygiene scan and `git diff --check` before landing.

### Task 1: Validate staged records before triage

Context surface: this task, `## Terms`, `## Outcome`, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/SKILL.md` *(edited)*
- `scripts/validate_review_staging.py` *(read-only invocation)*

Primary class anchors:
- `Step 3.1 verification gate` in `agents/skills/execute-plan/SKILL.md`
- `Step 3.2: Triage input` in `agents/skills/execute-plan/SKILL.md`

- [ ] Given a staged review Markdown file and its sidecar, expect Step 3.1 to run python3 scripts/validate_review_staging.py --hard <record> before Step 3.2 and continue only when the command succeeds and its final outcome is `OUTCOME: pass`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a malformed record for which soft validation exits zero with `OUTCOME: fail`, expect Phase 3 to stop before Step 3.2; a workflow test proves the soft-mode failure cannot enter triage. [class: REPOSITORY_TEST]
- [ ] Given a valid findings-bearing record and a valid clear record, expect both to pass the same hard-mode validator invocation without a new schema rule. [class: REPOSITORY_TEST]
- [ ] Given the existing review loop, expect no additional blocking gate, lock, ledger, refusal class, or validator mode. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: validate execution review records before triage` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Produce findings-bearing review pairs

Context surface: this task and the validator-grammar assumption in `## Assumptions`.

Files:
- `scripts/produce_exec_review_record.py` *(new)*
- `scripts/validate_review_staging.py` *(edited only if a shared formatting seam is needed)*
- `scripts/regenerate_review_sidecar.py` *(verify unchanged repair-only behavior)*

Primary class anchors:
- `_current_finding` in `scripts/validate_review_staging.py`
- `_current_findings_markdown` in `scripts/validate_review_staging.py`
- `validate_current_payload` in `scripts/validate_review_staging.py`

- [ ] Given structured review metadata and findings, expect the producer to emit a Markdown record and `.stats.json` sidecar matching the validator's current findings-bearing grammar. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given generated artifacts, expect the producer to report success only when the validator's final outcome is `OUTCOME: pass`; exit code zero alone is insufficient because soft mode can report `OUTCOME: fail`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a malformed generated pair, expect a producer test to verify refusal with the record path and validator result, including a soft-mode exit-zero failure outcome. [class: REPOSITORY_TEST]
- [ ] Given findings with varied severity and triage states, expect the generated Markdown counts and sidecar findings to agree with the validator's parity rules. [class: REPOSITORY_TEST]
- [ ] Given an empty findings set, expect the existing repair helper's zero-findings behavior to remain unchanged and the new producer not to claim that it repaired an existing record. [class: REPOSITORY_TEST]
- [ ] Given repeated producer inputs, expect deterministic Markdown and sidecar bytes; isolate validator telemetry under a temporary metrics home or scope filesystem assertions to producer-owned writes. [class: REPOSITORY_TEST]
- [ ] Commit: `feat: produce validated execution review records` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Write the execution receipt after the Phase 3 exit decision

Context surface: this task, `## Terms`, `## Outcome`, and lesson 107.

Files:
- `agents/skills/execute-plan/SKILL.md` *(edited)*
- `agents/skills/plans/SKILL.md` *(edited)*
- `agents/skills/done/SKILL.md` *(edited)*
- `docs/maintenance/development_lessons.md` *(edited)*
- `.ai-playbook/reviews/` *(generated execution receipt)*

Primary class anchors:
- `Step 3.5: Continue or exit loop` in `agents/skills/execute-plan/SKILL.md`
- `Phase 4: Archive Plan` in `agents/skills/execute-plan/SKILL.md`
- `Landing closeout - origin coverage and duplicate-origin refusal` in `agents/skills/plans/SKILL.md`

- [ ] Given Step 3.5 selects Phase 4 after a fresh blocking-clean review, expect it to write one dated record under `{reviews_dir}` using the current plans-egress execution-receipt naming grammar and the SHA-256 of the final Phase 3 plan bytes. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given Step 3.5 selects Phase 4 under a satisfied recorded residual-acceptance policy, expect it to write the same receipt with the final Phase 3 plan digest even though blocking findings remain in the accepted named set. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given either Phase 4 exit, expect repository tests to assert the receipt name and digest match the final Phase 3 plan bytes; the residual-acceptance case proves accepted named findings do not suppress receipt production. [class: REPOSITORY_TEST]
- [ ] Given Step 3.5 selects another Phase 3 round, expect it to write no execution receipt. [class: REPOSITORY_TEST]
- [ ] Given Phase 4 appends the required disposition after Step 3.5 receipt creation, expect the plans lifecycle to refresh the digest to the final archived plan bytes before the archive commit and its `check-archive`; a workflow test proves the check sees the refreshed digest. [class: REPOSITORY_TEST]
- [ ] Given done closeout, expect the skill to verify and migrate the Phase 4 refreshed receipt without changing its digest. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given lesson 107, expect its rule to name Step 3.5's selected Phase 4 exit as the receipt production point while retaining its observed refusal as evidence. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the existing egress guard and landing sweep, expect their commands, inputs, and refusal behavior to remain unchanged. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: produce execution receipt at review round close` [class: IMPLEMENTATION_REQUIRED]
