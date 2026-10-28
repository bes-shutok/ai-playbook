# Plan: Bind Certification Landing Receipts to Their Own Landing

Backlog origin: docs/history/backlog/2026-10-21-landing-diagnostic-selects-foreign-plan.md
Driving force: code-quality
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/landing-diagnostic-own-plan-target.md (session 01a17c5b-bdc9-7781-86f5-38e0cd2c16dd)
Plan review record: the staging series .ai-playbook/reviews/2026-10-28-plan-review-landing-diagnostic-own-plan-target-pc62dc674-r*.md (the highest rN for this source-plan path is authoritative)

## Terms

- **Landing receipt:** the warning-only post-squash certification diagnostic record.
- **Run identity:** the plan path and source worktree belonging to the landing being closed out.
- **Primary ledger:** `docs/history/certification-seal-landing-diagnostics.md`.
- **Fallback ledger:** `docs/history/certification-seal-landing-diagnostic-write-failures.md`.

## Why

A certification landing receipt can currently name another plan and worktree, so it does not describe the landing that produced it. Bind receipt identity to the current run and preserve the diagnostic's warning-only behavior.

## Gist & Examples

TLDR: bind each certification landing receipt to its run-owned plan and worktree, improving code-quality by keeping unrelated receipts out of the landing record.

Before, a landing receipt could resolve “this plan” to a peer plan and a third session's worktree. After, a receipt uses the plan path and source worktree recorded for its own landing; if either identity differs, the diagnostic records the mismatch through the existing fallback ledger without running validators or blocking closeout.

## Outcome

Every certification landing receipt identifies the plan and source worktree for the landing that produced it.

- Matching run identities continue through the existing readiness and staging diagnostic branches.
- A mismatch is recorded with expected and observed identities, the `not_observed` warning, and the existing fallback path.
- Receipt identity failures remain warning-only and do not delay landing or closeout.

Gate delta: none; preserve the current warning-only diagnostic and add no closeout condition, refusal class, lock, retry loop, or other blocker.

## Assumptions

- Select the exact done-run manifest using the captured `DONE_RUN_ID` and `DONE_RUN_MANIFEST`. Derive its expected source worktree root from the facts-resolved `{tmp_dir}/done-session/run-manifest-<run_id>.json` path. Require the current source worktree root from the diagnostic context and `git rev-parse --show-toplevel` to equal that path-derived root. Compare manifest `repo_root` to the canonical SHA-256 digest of that root, and require the matching `run_id` plus sole `owned_plan_paths` entry. Read the expected source-worktree head from that same root. Basis: `RunManifest.repo_root` stores a root digest, and the manifest is stored in its owning checkout.
- Keep the completed plan `docs/history/plans/completed/2026-10-20-certification-seal-landing-survival.md` unchanged under ADR-0001. Move the current operative outcome matrix into the existing Plan Lifecycle diagnostic home and update both ledger headers to point there; the archived matrix remains a historical snapshot, not a second operative source. Basis: completed-plan history is frozen, while the origin asks for a live mismatch row and a single behavior source.
- An identity mismatch is diagnostic evidence, not a reason to reject or retry a landing. Preserve the existing warning-only and transcript-recovery behavior.
- The Plan Lifecycle landing diagnostic is the right home because it already owns post-squash receipt behavior; no new top-level section or new ledger is needed.
- Missing, unreadable, ambiguous, or unequal manifest identity is inconclusive: run neither validator, record expected and observed plan/worktree identities, use `not_observed`, and route directly to the fallback ledger without fabricating a primary-write error. If that fallback append fails, preserve the same serialized receipt and fallback-write error in the maintenance transcript for the existing sunset recovery; do not retry or stop closeout. The primary ledger header limits its one-receipt statement to outcomes the matrix routes there.
- The user requested plan authoring only. This plan does not execute the change or edit completed history.

Scope extensions (grilled): none proposed.
Sources inspected: not a tracker-linked request.
Decision points requiring a grill: none remain.

## Standing constraints

- Keep the diagnostic warning-only. Do not add a landing refusal, closeout condition, retry, lock, producer script, or ledger.
- Keep one operative outcome matrix in the living Plan Lifecycle procedure. Do not edit the archived completed plan.
- Balance operative skill-text growth by deleting equivalent bytes from the existing diagnostic procedure in the same change.

## Evaluation Criteria

**Quality dimensions:** identity correctness, warning-only behavior, one operative source, and byte balance.

**Done when:**
- The live outcome matrix binds `plan_path` and `source_worktree_head` to the current run's recorded identity.
- Its mismatch row records expected and observed values, skips both validators, sets the warning to `not_observed`, and routes to the fallback ledger.
- Both ledger headers point to the living matrix and distinguish identity mismatch from primary append failure; both-fallback-failure transcript recovery remains intact.
- The completed plan remains byte-identical, no new blocking behavior is added, and the Plan Lifecycle skill has no net byte growth.

**Ship when:** not applicable; this is a documentation contract change.

## Documentation Impact Assessment

The backlog row contains the incident details. The living Plan Lifecycle procedure owns the current receipt matrix; the primary and fallback ledger headers point to it. The completed plan remains an unchanged historical record. No incident narrative, validator, lock, or separate policy document is added.

## Review Scope

**Explicit must-fix:** findings on these paths are in scope.

**Documentation:**
- `agents/skills/plans/SKILL.md` (Task 1)
- `docs/history/certification-seal-landing-diagnostics.md` (Task 1)
- `docs/history/certification-seal-landing-diagnostic-write-failures.md` (Task 1)

**Read-only historical reference:**
- `docs/history/plans/completed/2026-10-20-certification-seal-landing-survival.md` (review-only). Preserve its bytes under ADR-0001.

**Plan-related extension:** only changes needed to make the identity contract, fallback record, and byte-balanced living matrix consistent.

**Out of scope; reject unless plan-related:**
- New runtime scripts, ledgers, locks, retries, closeout conditions, or validator gates.
- Edits to the completed plan or unrelated receipt fields and rows.

## Validation Commands

```bash
python3 scripts/doc_registry_validator.py validate
bash scripts/check-no-em-dash.sh touched
bash scripts/scan-public-hygiene.sh --files agents/skills/plans/SKILL.md docs/history/certification-seal-landing-diagnostics.md docs/history/certification-seal-landing-diagnostic-write-failures.md
```

### Task 1: Bind the live receipt matrix to the landing identity

Context surface: `## Terms`, `## Standing constraints`, and this task.

Files:
- `agents/skills/plans/SKILL.md`
- `docs/history/certification-seal-landing-diagnostics.md`
- `docs/history/certification-seal-landing-diagnostic-write-failures.md`

- [ ] Make the Plan Lifecycle procedure the single operative home for the receipt outcome matrix. Carry forward its existing context, readiness, staging, append-failure, both-appends-fail, and transcript-recovery outcomes without changing their warning values or destinations. [class: IMPLEMENTATION_REQUIRED]
- [ ] Select the setup manifest via `DONE_RUN_ID` and `DONE_RUN_MANIFEST`; derive the expected worktree root from its facts-resolved done-session path and require the diagnostic source-worktree root and Git toplevel to equal it. [class: IMPLEMENTATION_REQUIRED]
- [ ] Compare manifest `repo_root` to the canonical SHA-256 digest of that path-derived root; require the matching `run_id` and sole `owned_plan_paths` entry. [class: IMPLEMENTATION_REQUIRED]
- [ ] Read `source_worktree_head` from that same root; a different worktree with the same HEAD must fail the root-path comparison. [class: IMPLEMENTATION_REQUIRED]
- [ ] For missing, unreadable, ambiguous, or unequal identity, run neither validator, record expected and observed values, set `not_observed`, and route directly to fallback without claiming a primary-write failure. [class: IMPLEMENTATION_REQUIRED]
- [ ] Update both ledger headers to name the living Plan Lifecycle matrix as the operative source; scope the primary ledger's one-receipt statement to outcomes routed there. [class: IMPLEMENTATION_REQUIRED]
- [ ] Clarify that the fallback ledger receives direct identity-mismatch records as well as records whose primary append failed. [class: IMPLEMENTATION_REQUIRED]
- [ ] If a direct fallback append fails, emit the same receipt and fallback-write error to the maintenance transcript for existing sunset recovery; add no retry or closeout stop. Retain both-ledgers-fail recovery for the primary-append path. [class: IMPLEMENTATION_REQUIRED]
- [ ] Leave the completed plan byte-identical. Remove equivalent redundant diagnostic prose from the existing Plan Lifecycle text so the changed skill file has no net byte growth; report before-and-after byte counts in the implementation commit. [class: IMPLEMENTATION_REQUIRED]
- [ ] Verify the finished matrix against the two witnessed receipts and cases for a foreign plan, a foreign worktree with the same HEAD, missing or ambiguous run identity, and fallback append failure; matching receipts retain their paths, and every mismatch remains warning-only. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `plans: bind certification landing receipt identity`. [class: IMPLEMENTATION_REQUIRED]
