# Backlog: delete legacy Summary verdict grammar from plan_readiness

Status: open
Priority: deferred (2026-09-18, Andrey decision: corpus convergence is not organic and the pre-migration review rounds will be removed by a dedicated archive sweep in roughly Oct-Nov 2026; until that sweep lands, the plan's Task 1 eligibility stand-down makes execution impossible. The certified plan is parked byte-identical at docs/plans/deferred/2026-09-15-plan-readiness-legacy-verdict-grammar-deletion.md, do not edit it, its review digest db071188 must stay valid; revival protocol is in docs/plans/deferred/README.md. Parked INCOMPLETE: the coverage gaps below must fold into the plan at revival, before its mandatory fresh review round.)
Workflow: backlog
Source: 2026-09-04-plan-readiness-sidecar-verdict-field acceptance criterion 3 (legacy grammar deletion lands only after the corpus sweep confirms no remaining pre-adoption artifacts), spun off by the 2026-09-05 plan-readiness-migration plan
Severity: Low (time-gated)
Scope: scripts/plan_readiness.py

## Coverage gaps to fold in at revival (recorded 2026-09-18)

The certified plan does not cover these marginal cases; each needs a plan edit
at revival and must survive the revival drift check and fresh review round:

1. Primary-checkout-bound execution. The live corpus `docs/reviews/` (551
   plan-review artifacts measured 2026-09-18) and `.ai-playbook/facts.md` are
   gitignored and exist only in the main checkout. In a temp worktree every
   Task 1 and Task 5 command fails wiring: no facts file -> "cannot resolve
   plans_dir/reviews_dir from the facts"; facts present without the corpus ->
   the r6 Z5 "configured reviews_dir does not exist on disk" failure. The plan
   must state that execution happens in the primary checkout (its transient
   tolerances already assume live parallel sessions there), and either
   prescribe or explicitly forbid the undocumented r4 X5 cwd-preference
   workaround (running the worktree script from the main checkout root).
2. The Validation block's live gate on the plan itself resolves this plan's
   own review sidecars from the same checkout-local corpus, so certification
   and execution evidence are main-checkout-bound, not just the sweep.
3. Stale eligibility arithmetic. The authoring measurement (total 478,
   covered 235, 2026-09-15) is stale: 2026-09-18 measures total 551, covered
   307, uncovered 244 (190 sidecars with no `verdict` key, 2 with a legacy
   non-conforming verdict shape, 54 with no sidecar file at all). Convergence
   is NOT organic, the uncovered pool held at ~243-244 while the corpus grew
   by 73 in three days; the archive sweep is the only convergence path.
4. Deployed runtime copy coupling. The plan scopes deployed `~/.ai-playbook`
   copies out as ops, but per session notes the deployed validator copy is
   currently absent and consumers fall back to the repo copy; a later
   redeploy from a stale source would resurrect the deleted fallback outside
   the repo. The out-of-scope note should name the redeploy sequencing
   (redeploy only from a post-deletion source).

## Problem

The Summary total-rule grammar remains in `evaluate_readiness` as the legacy
fallback for pre-adoption artifacts: when a round's sidecar lacks a conforming
`verdict` field, the verdict is established by scanning the review Markdown
`## Summary` for word-bounded `ready=yes` / `ready=no` tokens (last occurrence
wins). The migration plan added the sidecar verdict field and the consumer
precedence rule, but deliberately kept the fallback while any live artifact
predates the producer contract.

## Eligibility gate

Eligible only when `python3 scripts/plan_readiness.py --sweep` prints coverage
with total is positive and covered equal to total: every live `*-plan-review-*.md` under `{reviews_dir}`
has a sidecar carrying a conforming `verdict` field (`yes` or `no` string).
Until then the fallback must stay; deleting it early would newly fail readiness
for every pre-adoption artifact.

## Verdict-source drift disposition

Deleting the fallback also ends the only verdict-source drift signal that
compares the sidecar against the artifact prose. The fix must do one of the
following:

- add a sweep anomaly for a conforming sidecar `verdict` that contradicts the
  artifact Summary's last verdict token (keeping drift detection alive on the
  sweep side), or
- explicitly record the end of Summary-token drift detection as an accepted
  consequence of the deletion (once the sidecar field is the sole verdict
  source, a stray Summary token can no longer flip readiness and need not be
  monitored).

## Suggested fix

Delete the Summary fallback path from the verdict step of `evaluate_readiness`
(keep the sweep's mention detector), keeping the sidecar `verdict` field as the
sole verdict source. Remove the now-dead `VERDICT_TOKEN_RE` machinery and its
comment block, update the selftest fixtures that pin the fallback behavior, and
update the precedence documentation in `agents/hooks/plan-readiness/README.md`
and `agents/skills/review-plan/SKILL.md` to drop the fallback clause.
