Status: open
Priority: low
Workflow: backlog
Class: plan-gate fidelity (a validation command derives its input through the fallback arm only, skipping the primary source the operative rule names)
Driving force: correctness

# Plan G7 skips the base_branch facts key and derives the base from the origin-HEAD fallback only

**Exact location:** `docs/history/plans/2026-09-28-worktree-first-standard-only-mode.md`, Validation Commands block, gate G7 (`BASE_BRANCH="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')"`). The rule it lags: the canonical Worktree-first standard section's **Base-branch resolution rule** in `agents/skills/execute-plan/SKILL.md` (the base resolves from the facts key `base_branch` or the owning skill's configuration first; the origin-HEAD symbolic ref is the absent-key fallback derivation for a default-branch-integration project).

## Problem

The plan's G7 hardwires the fallback derivation as the only derivation: it reads the origin HEAD symbolic ref and fails when that is unresolvable, never consulting the `base_branch` facts key the canonical rule names as the primary source. Two consequences: a project whose facts pin `base_branch` to something the origin-HEAD fallback would not produce runs G7 against the wrong base (gates keyed on `--base "$BASE_BRANCH"`, such as the added-lines em-dash scan, diff against the wrong range), and a checkout-flow project (base = the operator's checked-out branch) has no arm in G7 at all. The gap is latent in this repository (origin HEAD resolves to the default branch and the facts pin no divergent value), so it is a fidelity defect against the canonical rule, not a witnessed failure.

## Observed versus expected

- Observed: G7 derives `BASE_BRANCH` through the origin-HEAD fallback only and stand-downs when that ref is absent, treating the fallback as the rule.
- Expected: G7 derives the base per the canonical rule's full ladder (facts `base_branch` key or the owning skill's configuration first, then the class-keyed fallback derivation), or the plan states explicitly that its gates deliberately assume the default-branch-integration fallback shape for this run.

## Suggested fix

Routes through a plan-file edit, not an address-pass prose change: either a correction branch that rewrites the G7 derivation lines to the canonical ladder, or folding the fix into the plan's next revision before archive. The address pass is barred from editing plan files, so the fix is captured here.

## Source reference

docs/reviews/2026-09-28-worktree-first-standard-only-mode-code-review-r3.md (round 3 address pass; staged finding set item "plan G7 base-key skip"). Capture hygiene: scan-public-hygiene --files pass (rc 0, recorded in the execution log review-r3-receiving-review.log.md). Why not fixed now: the staging surface is a plan file and the pass contract bars plan edits; Severity: Low (latent, no witnessed failure).

Dedup probe: searched the open backlog corpus (filenames plus Problem bodies) for "G7", "base branch", "base_branch", "origin HEAD": zero open items own the plan's G7 derivation; the nearest item is this plan's own closeout baseline (landed, not a backlog item); no overlap, no merge.

Origin class: self-serving
