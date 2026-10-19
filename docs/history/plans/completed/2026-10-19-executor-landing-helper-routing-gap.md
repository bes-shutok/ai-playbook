# Plan: Route executor worktree landings through the landing helper

Backlog origin: docs/history/backlog/2026-10-19-executor-landing-helper-routing-gap.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/YYYY-MM-DD-plan-review-executor-landing-helper-routing-gap[-p<identity-token>]-r*.md
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-19-executor-landing-helper-routing-gap.md (session 01a1501c-2267-70b3-9423-7dd6ba3e4dd8)

## Terms

- **Worktree-complete landing:** the landing class whose rebase and squash run in the run worktree, with one final compare-and-swap update of the base ref.
- **Landing helper:** `scripts/land_squash.sh land-worktree`, which owns the worktree-complete class gates and ref update.
- **Deployment gap:** the sole authorized repository-local helper is absent, so the worktree-complete landing is deferred and the missing deployment is recorded; no alternate helper copy or hand-composed fallback is authorized.

## Why

Executors can follow the critical-section description and hand-compose a landing without invoking the helper that owns the base-freshness and plans-egress archive gates. The entry point needs to make the helper the required composition while preserving the existing refusal and recovery details.

## Gist & Examples

TLDR: route worktree-complete landings through the helper, code-quality by making its existing gates unavoidable in the normal path.

Before: an executor follows the detailed rebase, squash, and ref-update prose and skips the helper-owned checks. After: the first instruction names the helper as the only sanctioned composition; the following prose explains failure handling. If the repository-local helper is absent, the executor records a deployment gap and defers the landing instead of composing the operation by hand.

## Outcome

Worktree-complete landings use the helper, and a missing deployment is recorded before the landing is deferred.

- The ordinary landing path runs the helper's base-freshness, archive, parentage, and compare-and-swap checks.
- The execution blueprint gives the same routing instruction to dispatched children.
- Helper absence is visible in the landing record, and no undocumented hand-composed operation bypasses the helper-owned gates.

Gate delta: none; no new gate, validator, ledger, state, or blocking review duty is added, and the existing helper checks remain the enforcement surface.

## Assumptions

- The current blueprint source is `agents/skills/maintenance/template-execution.md`; `prompt-templates.md` now contains pointer stubs and does not contain the execution landing section. The origin's suggested path is corrected to the current source of record.
- The only authorized helper path for this class is the repository-local `scripts/land_squash.sh`; the executor standard and maintenance blueprint do not authorize a deployed copy as an alternate source. If the repository-local helper is absent, there is no safe ordinary-landing hand recipe in the sources; record the deployment gap and defer. Route valid final outcomes by their existing contracts: `pass` completes; ordinary modeled `fail` outcomes defer the landing; `indeterminate` or `tool_error` stops for re-derivation. Preserve two special `fail` paths: a pre-swap tree-identical landing refusal stops for adjudication and records the existing content-bearing commit; a post-ref-move `reconcile-gate` refusal keeps the landing, records the receipt and refusal, runs the named reconciliation command, and completes closeout on a valid receipt. Neither is an ordinary deferred failure. An invocation/tool failure without a valid final outcome line is a tool error and also stops for re-derivation.
- The backlog's phrase “manual fallback” is not carried forward: the source defines no ordinary worktree-complete recipe or substitute for the helper-owned gates, so deferring on helper absence is the safe, evidence-supported disposition.
- The existing review-plan growth-balance finding applies to the small prose addition; this plan adds no review-panel duty or finding-class file.

Decision points requiring a grill: none remain.

## Standing constraints

- Keep the existing critical-section prose as failure-path documentation, preserving the worktree-complete helper outcome handling and the separate severed-ancestry lane.
- Do not add a gate or rewrite the helper's owned checks.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the helper invocation is the only sanctioned ordinary composition, and its existing gates remain named and reachable.
- consistency: the execution blueprint mirrors the same routing and fail-closed helper-absence disposition.
- maintainability: existing failure-path details remain available without reading as an alternate landing recipe.

**Done when:** both source files place the routing sentence at the start of their landing instructions; absence of the repository-local helper leads to a recorded deployment gap and a deferred landing without selecting an alternate deployed copy; valid helper outcomes follow their existing branches (`pass` completes; ordinary `fail` defers; `indeterminate` or `tool_error` stops for re-derivation), the pre-swap tree-identical refusal stops for adjudication and records the existing content-bearing commit, a post-ref-move `reconcile-gate` refusal keeps the landing and completes only after the receipt, named rerun, and valid closeout receipt, and an invocation/tool failure without a valid final outcome is a tool error; a corpus grep confirms no other executor-facing prose sanctions a competing worktree-complete hand recipe; the pins suite and public-hygiene scan pass.

**Ship when:** the two source edits, the origin disposition, and this plan's dispatch-entry prune land together; no external release condition remains.

## Review Scope

**Explicit must-fix:**

**Production code:** none.

**Tests:** none; the change is documentation-only and uses the existing pins suite.

**Documentation:**
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/maintenance/template-execution.md`
- `docs/history/backlog/2026-10-19-executor-landing-helper-routing-gap.md` *(deleted in the landing change)*
- `docs/history/backlog/PLAN-PROMPTS.md` *(landing prune rider for this plan's entry only)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it implements a task, fixes a regression caused by plan work, closes wiring or docs implied by a must-fix change, or contradicts a contract this plan changes. If the link is weak or speculative, drop it as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/land_squash.sh`; reason: its existing gates and behavior are not part of this prose-routing fix.
- `agents/skills/maintenance/prompt-templates.md`; reason: it is a pointer-stub file, not the current execution blueprint source.

## Validation Commands

```bash
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-19-executor-landing-helper-routing-gap.md
bash scripts/check_maintenance_pins.sh
bash scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh touched
rg -n -i 'land-worktree|git merge --squash|git update-ref refs/heads|only sanctioned composition' agents/skills/execute-plan/SKILL.md agents/skills/maintenance
```

### Task 1: Require helper routing in executor guidance

Context surface: the plan's Terms and Standing constraints, the origin backlog row, the current landing step in `agents/skills/execute-plan/SKILL.md`, and the worktree arm in `agents/skills/maintenance/template-execution.md`.

- [x] At the head of the worktree-complete branch of `Land under the lock`, prescribe the named `land-worktree` helper invocation as its only sanctioned composition; state that the following critical-section prose documents failure paths and does not authorize a hand-composed equivalent. Preserve the existing separate prescription for severed ancestry. [class: IMPLEMENTATION_REQUIRED]
- [x] Mirror the helper-only routing instruction in the execution blueprint's worktree arm in `agents/skills/maintenance/template-execution.md`; do not authorize an alternate deployed copy or hand-composed substitute. [class: IMPLEMENTATION_REQUIRED]
- [x] When the repository-local helper is absent, require a recorded deployment gap and defer the landing. [class: IMPLEMENTATION_REQUIRED]
- [x] Route valid helper outcomes by their existing contracts: `pass` completes; ordinary modeled `fail` outcomes defer; `indeterminate` or `tool_error` stops for re-derivation. Preserve the pre-swap tree-identical refusal as a special adjudication path that stops and records the existing content-bearing commit. [class: IMPLEMENTATION_REQUIRED]
- [x] Preserve the post-ref-move `reconcile-gate` refusal path: keep the landing, record the receipt and refusal, run the named reconciliation command, and complete closeout only on a valid receipt. [class: IMPLEMENTATION_REQUIRED]
- [x] Treat an invocation/tool failure without a valid final outcome line as a tool error and stop for re-derivation. [class: IMPLEMENTATION_REQUIRED]
- [x] Inventory executor-facing landing instructions with the corpus grep; confirm no other surface authorizes a competing hand-composed recipe for the worktree-complete class, while retaining necessary failure-path descriptions. [class: IMPLEMENTATION_REQUIRED]
- [x] At landing, delete the completed origin row, tidy surviving `Cluster:` pointers to it, prune only this plan's frozen dispatch entry, and print one `PLAN-PROMPTS-PRUNE` receipt for this slug, using this plan file as the witness. [class: IMPLEMENTATION_REQUIRED]

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/maintenance/template-execution.md`
- `docs/history/backlog/2026-10-19-executor-landing-helper-routing-gap.md`
- `docs/history/backlog/PLAN-PROMPTS.md`

Primary class anchors:
- `Worktree-first standard: Land under the lock` in `agents/skills/execute-plan/SKILL.md`
- `Worktree arm` in `agents/skills/maintenance/template-execution.md`
