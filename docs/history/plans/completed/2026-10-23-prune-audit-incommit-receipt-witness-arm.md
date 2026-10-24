# Plan: Recognize In-Commit Prompt Log Prune Receipts

Backlog origin: docs/history/backlog/2026-10-22-prune-audit-landing-token-never-resolves.md
Driving force: code-quality
Plan review record: .ai-playbook/reviews/2026-10-23-plan-review-prune-audit-incommit-receipt-witness-arm-p00cbed88-r*.md
Execution budget: 1h total, largest task 1h
Authoring claim: docs/tmp/authoring-claims/2026-10-22-prune-audit-landing-token-never-resolves.md (session 01a1638f-189d-7b02-9cf8-0990eb6f3dfd)

## Terms

- **In-commit receipt:** a newly added prompt-log ledger line naming the removed entry and using the literal token `landing` in the same commit as the removal.
- **Same-log receipt:** a ledger line in the same rolling prompt log whose entry heading is removed.
- **Receipt without removal:** a commit that adds a ledger receipt line to a log but removes no entry from that log; the audit reports this as a warning.
- **Resolvable ledger token:** a receipt token that names an existing commit or a path in the removal commit's tree.
- **Log post-image:** the contents of one rolling prompt log after a particular commit.
- **Rolling prompt logs:** `PLAN-PROMPTS.md` and `EXEC-PROMPTS.md`, the two logs the prune audit examines.

## Why

The audit recognizes ledger receipts only when their token resolves to a commit or a path in that commit's tree. The rolling logs also use the literal token `landing` for a receipt added with its entry removal, so conformant same-commit prunes are incorrectly flagged as unwitnessed.

## Gist & Examples

TLDR: Recognize a same-commit `landing` receipt for its removed entry, improving code-quality by matching the prune audit to the rolling logs' receipt convention.

Before: a commit removes `probe-entry` and adds `EXEC-PROMPTS-PRUNE: probe-entry -> landing in this commit`; the audit emits `REMOVED-WITHOUT-WITNESS` and exits 1.

After: the same commit emits `PRUNE-OK: probe-entry -> landing (in-commit receipt)` and exits 0 when no other removal is unwitnessed.

## Outcome

The prune audit accepts a new same-log `landing` receipt as evidence for the entry removed in that commit.

- A receipt is accepted only for its exact slug, exact token, log, and removal commit.
- An earlier unresolvable `landing` receipt or a receipt in the sibling log does not satisfy the new witness; existing resolvable log-ledger receipts retain their current behavior.
- A receipt-only commit continues to emit `RECEIPT-WITHOUT-REMOVAL` without changing the exit code.

Gate delta: the existing `REMOVED-WITHOUT-WITNESS` refusal remains for every removal without an accepted witness and narrows only for a newly added same-log `landing` receipt naming that exact removal; no new refusal class, hard gate, fence, protocol layer, schema field, or condition that pauses later work; no existing refusal is removed; normal plan certification duties are unchanged, with no blocking review-layer duty added or removed.

## Assumptions

- The new accepted receipt class contributes to the existing log-ledger receipt count because the summary counts accepted log-ledger witnesses; basis: `walk_audit_commits` and `prune_audit` in `scripts/check_prompt_log_origins.py`.
- assume the focused integration module is run with pytest; basis: its fixture-parameterized tests and module docstring identify the venv pytest runner as canonical.
- The existing `RECEIPT-WITHOUT-REMOVAL` warning remains the guard for a receipt added without removing an entry from that same log; basis: the origin row and current checker branch.
- The related warning-only audit for staged or working-tree receipt removals stays separate; basis: `docs/history/backlog/2026-10-20-prompt-log-pending-prune-audit-warning.md`.
- Admission record for this guard-class widening: the origin row links the four initial 2026-10-22 witnesses; current history re-check found eight same-day receipt/removal pairs. Expected catch: each conformant same-commit ad hoc prune in an audit range covering its landing. False-positive cost: near zero because matching requires a newly added same-log receipt with the exact removed slug and literal `landing` token. Review date: 2027-01-18, the existing receipt-without-removal warning sunset.

Decision points requiring a grill: maintenance-selected authorization resolves summary accounting: increment the existing log-ledger receipt count for this accepted class; source `scripts/check_prompt_log_origins.py`, 2026-10-23, Evaluation Criteria.

## Standing constraints

- Keep receipt matching scoped to one rolling log and one removed slug. Preserve the existing plan-file and commit-message witnesses and their precedence.
- Keep the pending staged or working-tree receipt audit out of this plan; it is tracked separately and remains warning-only.

## Evaluation Criteria

- **Correctness:** only a receipt line newly added in the removal commit's own log post-image, for the removed slug and exact token `landing`, produces the new classification.
- **Safety:** an earlier unresolvable `landing` receipt cannot satisfy the new witness, a sibling-log receipt cannot cross-witness, and a receipt-only commit still warns with exit 0.

**Quality dimensions:**
- Classification accuracy: the exact conformant case passes and the nonmatching cases retain their current outcomes.
- Audit clarity: the new classification identifies the accepted receipt form and is counted in the existing log-ledger summary.

**Done when:** the focused prune-audit integration tests and the plan readiness gate pass.

**Ship when:** none; implementation and its verification are repository-local.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_prompt_log_origins.py`

**Tests:**
- `scripts/test_check_prompt_log_origins.py`

**Out of scope; reject unless plan-related:**
- `docs/history/backlog/2026-10-20-prompt-log-pending-prune-audit-warning.md`; reason: it covers staged and working-tree receipt removals, not committed same-log receipt classification.
- `docs/history/backlog/completed/2026-10-15-plan-prompts-prune-end-anchor-overreach.md`; reason: its receipt-line preservation fix is complete and remains an invariant, not an implementation target here.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest -q scripts/test_check_prompt_log_origins.py
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-23-prune-audit-incommit-receipt-witness-arm.md
```

### Task 1: Recognize the in-commit receipt and preserve the existing audit boundaries

Context surface: the plan's Terms and this task.

Files:
- `scripts/check_prompt_log_origins.py`
- `scripts/test_check_prompt_log_origins.py`

Primary class anchors:
- `walk_audit_commits` in `scripts/check_prompt_log_origins.py`

- [x] Given a removal and a newly added same-log receipt with the exact slug and token `landing`, expects `PRUNE-OK: <slug> -> landing (in-commit receipt)`, a pass when no other removal is unwitnessed, and an increment to the existing log-ledger count. [class: IMPLEMENTATION_REQUIRED]
- [x] The receipt delta compares `(slug, token)` counts in each log before and after the removal commit, so only a newly added matching line qualifies and a sibling-log receipt cannot cross-witness. [class: IMPLEMENTATION_REQUIRED]
- [x] Extract the per-log receipt-delta comparison into a small helper and keep the witness-classification order visible in `walk_audit_commits`. [class: IMPLEMENTATION_REQUIRED]
- [x] Pass one shared sanitized environment to every fixture Git and checker subprocess: remove inherited `GIT_*` variables, disable system and global Git configuration, and add only required fixture values. [class: IMPLEMENTATION_REQUIRED]
- [x] A regression fixture sets `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_COMMON_DIR`, and `GIT_OBJECT_DIRECTORY` to a separate temporary repository and proves fixture writes stay in the intended repository. [class: REPOSITORY_TEST]
- [x] A receipt with another token, a different slug, or only an earlier `landing` line does not satisfy the new witness arm; existing resolvable log-ledger receipts keep their current behavior. [class: REPOSITORY_TEST]
- [x] A same-log receipt-only commit still emits `RECEIPT-WITHOUT-REMOVAL` and exits 0; existing plan-file, resolvable ledger, commit-message receipt, and cross-log cases retain their results. [class: REPOSITORY_TEST]
- [x] Update the checker docstring and CLI help to list the in-commit receipt alongside the existing witness classes. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the focused integration suite and the plan readiness pre-round gate. [class: REPOSITORY_TEST]
