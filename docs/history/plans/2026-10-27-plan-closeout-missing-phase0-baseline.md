# Plan: document the refusal boundary for a missing Phase 0 baseline
Backlog origin: docs/history/backlog/2026-10-26-plan-closeout-missing-phase0-baseline.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-10-27-plan-review-plan-closeout-missing-phase0-baseline-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1h total, largest task 1h
Authoring claim: docs/tmp/authoring-claims/2026-10-26-plan-closeout-missing-phase0-baseline.md (session 01a17c5c-b1b6-7c02-8203-5bc9bf7f9ab3)

## Terms
- **Source run**: The original authoring worktree, branch, plan, and review artifacts for the closeout that missed its canonical baseline.
- **Identity-bound artifact**: A source-run artifact whose path, ownership, and digest can be re-derived and matched to the reviewed plan.
- **Canonical baseline**: The Phase 0 `closeout-baseline.json` captured before plan gates or plan-file writes for the original run.
- **Baseline capture receipt**: An existing record that binds a baseline digest and path to the run identity and capture time; the current baseline format has no such receipt.
- **Plan-session slug**: The slug resolved by execute-plan Step 0.4 and `done_run` from either a dated plan file or a dated plan directory containing `PLAN.md`.

## Why
A missing Phase 0 baseline correctly blocks closeout migration. Investigation found that a fresh worktree cannot preserve the active run identity, and the current baseline format has no receipt binding its contents to a run or capture time. Document the canonical path check before Phase 0 and keep the existing refusal when the baseline is absent; do not infer provenance from an alternate path or a copy digest.

## Gist & Examples
Title: document the refusal boundary for a missing Phase 0 baseline

TLDR: Verify the canonical date-stripped baseline path before Phase 0 and retain the existing refusal if the required baseline is absent.

Before: A path mismatch can leave done-run unable to find the baseline, while a fresh-worktree or copied-file workaround cannot prove the same run identity and capture time.
After: For dated plan files and dated directories containing `PLAN.md`, use the exact slug resolved by both Phase 0 and done-run; when the baseline is absent, use only its sibling `closeout-baseline-skip.json` if it is a valid skip. Otherwise retain the refusal.
Edge cases: A present baseline goes through migration and a sibling skip never overrides its refusal; do not accept an alternate path, create a parallel worktree or branch, rewrite run identity, capture late, or synthesize a skip.

## Outcome
The Phase 0 capture and done-run migration use one verified date-stripped slug. The runner consults a valid skip sibling only when the canonical baseline file is absent; a present baseline is sent through the existing migration checks and a skip does not override a refusal.

- No alternate baseline is accepted based only on its path, contents, timestamp, or copy digest.
- No parallel worktree, branch, claim, or manifest identity is introduced.
- The existing scoped-copy procedure remains available only for a valid sibling skip beside an absent baseline.

Gate delta: Documentation only; the existing missing-baseline refusal and valid-skip behavior stay unchanged.

## Assumptions
- The original baseline refusal and the prohibition on late capture remain mandatory; evidence: the completed single-start baseline plan and current Phase 0 duty in `agents/skills/plans/SKILL.md`.
- The baseline JSON contains `dirs`, `files`, and `skipped` but no run identity, capture time, or baseline digest receipt; evidence: `scripts/worktree_closeout_migrate.py` capture schema. The valid skip is selected only when the canonical baseline is absent.
- Run identity is bound to the registered worktree and branch by the existing claim and manifest contract; evidence: `agents/skills/execute-plan/SKILL.md` identity block and the maintenance recovery procedure.
- An alternate baseline cannot be trusted without an independent receipt that the current capture procedure does not produce; therefore this plan preserves refusal instead of adding a new receipt mechanism.
- The context-compaction origin is distinct, already covered, and remains untouched; evidence: its live row names the completed recovery plan, whereas this row records missing migration-baseline evidence.
Decision points requiring a grill: none remain.

## Standing constraints
- Do not edit the migration refusal, create a late baseline, or synthesize a capture-failure skip.
- Do not create a parallel worktree or branch, re-key an alternate baseline, or rewrite the existing claim or manifest identity.
- Do not capture a late baseline or synthesize a skip; retain the existing refusal when the canonical baseline and valid skip are absent.

## Evaluation Criteria
- Phase 0 and done-run resolve the same plan-session slug for both dated plan files and dated directories containing `PLAN.md`, before capture or migration.
- The Phase 0 capture path is checked against done-run’s resolved canonical plan-session slug before capture.
- Missing canonical baseline without a valid sibling skip retains the existing refusal.
- A present baseline is passed to migration; malformed JSON or missing/empty `dirs` retains the migration refusal even when a valid skip sibling exists. Do not claim broader schema validation.
- The context-compaction origin remains separate and unchanged.
- Realistic-context validation confirms slug agreement for dated plan files and dated directories containing `PLAN.md`, alternate-path refusal, the valid sibling-skip route, and malformed-baseline refusal with a skip sibling.

**Quality dimensions:**
- Correctness: Phase 0 and done-run resolve the same canonical slug, and the missing-baseline and invalid-baseline refusal cases remain observable.
- Efficiency: the path check prevents slug mismatch while preserving the existing valid-skip route without adding machinery.

**Done when:** Phase 0 and closeout document canonical slug agreement and exact baseline/skip precedence; realistic-context validation covers alternate-path refusal, valid sibling-skip use, and malformed-baseline refusal; plan readiness passes.

**Ship when:** none.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Documentation:**
- `agents/skills/execute-plan/SKILL.md` (Task 1)
- `agents/skills/execute-plan/worktree-first.md` (Task 1)

**Tests:**
- Realistic-context validation of Phase 0 and closeout instructions for canonical-path agreement, alternate-path refusal, valid sibling-skip use, and malformed-baseline refusal with a skip sibling (Task 1)

**Plan-related extension:** No other path may change unless required to resolve a direct contradiction introduced by Task 1; report the path and reason before editing it.

**Out of scope; reject unless plan-related:**
- `scripts/worktree_closeout_migrate.py`, validators, gates, skip-record producers, and the separate context-compaction origin.

## Validation Commands

```bash
python3 scripts/plan_readiness.py docs/history/plans/2026-10-27-plan-closeout-missing-phase0-baseline.md
```

### Task 1: Document the canonical path check and missing-baseline refusal

Context surface: the plan's Terms and Standing constraints; Phase 0 capture and canonical worktree closeout own the path and refusal rules.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/worktree-first.md`

Primary class anchors:
- `Closeout baseline` in `agents/skills/execute-plan/SKILL.md`
- `Ad-hoc-worktree closeout` in `agents/skills/execute-plan/worktree-first.md`
- `Transfer-out-and-deletion implementation` in `agents/skills/execute-plan/worktree-first.md`

- [ ] Extend Phase 0 and Ad-hoc-worktree closeout: use the full execute-plan Step 0.4 slug rule for dated plan files and dated plan directories, and verify the capture path equals done-run’s path before capture. Keep procedure ownership in these existing sections. [class: IMPLEMENTATION_REQUIRED]
- [ ] Document that closeout accepts only the canonical baseline path or a valid sibling skip when that baseline is absent; an alternate path alone is not provenance. [class: IMPLEMENTATION_REQUIRED]
- [ ] Preserve refusal when the canonical baseline is absent without a valid sibling skip. A present baseline is passed to migration; malformed JSON or missing/empty `dirs` refuses, and a sibling skip does not override it. [class: IMPLEMENTATION_REQUIRED]
- [ ] Do not claim migration rejects every semantically invalid baseline or use a sibling skip to bypass a present baseline; schema hardening stays out of scope. [class: IMPLEMENTATION_REQUIRED]
- [ ] Do not re-key an alternate baseline or rewrite the claim or manifest identity: the capture format has no receipt binding baseline digest, path, and time to the run. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the revised instructions with realistic contexts: dated plan-file and dated plan-directory slug agreement, alternate-path-only candidate, missing baseline and skip, valid sibling skip with absent baseline, and malformed baseline with a valid skip sibling. Confirm the existing pass/refusal outcomes. [class: IMPLEMENTATION_REQUIRED]
- [ ] Route any failed path check or verification through the existing refusal; never capture a late baseline or synthesize a skip. [class: IMPLEMENTATION_REQUIRED]
- [ ] Keep the context-compaction origin separate and unchanged; replace redundant closeout prose in the edited skill with the precise canonical-path check and existing refusal behavior and delete at least as many operative bytes as the new text adds. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run plan readiness for the resulting documentation and commit: `docs: document missing baseline refusal boundary`. [class: IMPLEMENTATION_REQUIRED]
