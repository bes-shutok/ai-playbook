# Backlog: code-family certification identities go stale on every post-certification tip move (residual-append boundary, pre-landing rebase)

- **Filed:** 2026-10-21, execute-plan Phase 3/4 of certification-seal-landing-survival (same-session analysis)
- **Status:** done (covered by docs/history/plans/2026-10-24-code-family-cert-digest-scope.md, landed ba477eb80054f8d0a50e560c66b562d6bc335cda 2026-10-24; review r5 ready=yes zero blocking, seal .ai-playbook/review-certs/code-family-cert-digest-scope.md)
- **Workflow:** backlog
- **Priority:** medium
- **Cluster:** docs/history/backlog/2026-10-21-seal-landing-survival-review-residuals.md (same mechanism: the code-family anchor leg in `scripts/corrections_record.py`; residual R3 names the plan-family recovery population)
- **Cluster:** docs/history/backlog/2026-10-10-execute-plan-rebase-after-surface-refactor.md (same lifecycle point: the pre-landing rebase onto an advanced base)
- **Origin class:** observed execution friction
- **Class:** fix-class
- **Skill/step:** `agents/skills/execute-plan/SKILL.md` Phase 3 (Step 3.4 light boundary, the code-family round-close seal paragraph) and Phase 4; `agents/skills/review-plan/SKILL.md` (round-close seal paragraph); `scripts/corrections_record.py` (`verify_corrections` anchor leg, code-family arm)
- **Driving force:** efficiency (one certification per clean round, not three hand re-pins)

## Problem

A code-family round certifies a range `reviewed_base...reviewed_head` whose digest is pinned in four places: the seal block (`round_start_commit`, `round_close_commit`, `reviewed_head`, `range_digest`), the sidecar (`source_digest`, `extensions.certified_range`), the record's `Round:` and `Source digest:` lines, and the plans-egress backfill completion record. Two ordinary lifecycle steps then move the tip after the digest is taken:

1. The round-close residual append: the residual bullets the clean round backlogs are a tracked row, so their commit is a boundary commit above the certified head, and the sidecar's `source_digest` is stale the moment the row lands.
2. The pre-landing rebase: `land_squash.sh probe` requires containment of the live base tip, so a branch whose base advanced is rebased before the lock; every commit OID changes, the seal's anchors become non-ancestors, and the `git diff base...head` bytes (and so the digest) change with the new merge-base.

The code-family anchor leg refuses outright on a non-ancestor anchor (`the seal entry's ... is not an ancestor of HEAD`); the landed-anchor byte-identity resolution the 2026-10-20 plan added is plan-family only (`if landed_anchor is None and family == FAMILY_PLAN`). No skill sentence orders the residual append before the certifying digest or names the post-rebase re-pin, so the session re-derived and rewrote all four homes by hand three times (after the append, after the rebase, and again when the base pin had to move to the new merge-base).

## Expected

One of: (a) the execute-plan round-close ordering lands the residual row (and any other round-close tracked write) before the certifying digest is taken, and the Phase 4 text names a single re-pin step after a pre-landing rebase (seal, sidecar, record, backfill record, re-validated through `--source-code-repo`); or (b) the code-family anchor leg gains the same landed-anchor complement the plan family has, keyed on tree identity of the branch delta rather than commit OIDs, so a rebase that preserves the delta bytes keeps the certification. Either way a clean round's certification survives the two tip moves its own lifecycle prescribes.

## Evidence

2026-10-21 run: r2 certified at `fa3591d3b`; the residual append moved the tip to `b634c5587` (re-pin 1); the rebase onto `9ddd9698b` moved it to `9e33b48bc` (re-pin 2); the digest then had to be recomputed against the new merge-base because the seal's `reviewed_base` still named the pre-rebase base (`the round-start bytes do not re-hash to the seal entry's round-start digest`, re-pin 3). Each re-pin was verified green with `validate_review_staging.py --hard --source-code-repo . --source-code-plan <sidecar>`.

2026-10-21 re-witness (plan-validation-command-undefined-repo Phase 3 review r1): the trap has a skill-text accomplice. The execute-plan Step 3.4 sentence classifies backlog-item edits as bookkeeping, not digest mutations, while the code-record validator regenerates the whole branch diff at HEAD, so a post-review bookkeeping commit stales the record's exact-match digest like any other tracked write; the skill text affirmatively licenses the move rather than merely omitting an ordering. This round's recovery, recorded in its staging artifacts: hard-validate the record at the reviewed head before landing the bookkeeping commit, then commit. That is the per-round unilateral form of option (a), certify before tracked writes, and it needs no re-pin.

## Why not fixed now

The ordering fix is a skill-text change across two skills and the leg widening is a validator change with its own fixtures; both exceed the ad-hoc arm and the witnessing session ran under a stop-after-current-plan order.

## Source

- Observed 2026-10-21 during Phase 3 round close and Phase 4 landing of the certification-seal-landing-survival run; the r2 record and seal in the primary reviews and review-certs homes carry the final re-pinned identities.
- Witness 2026-10-21 (plan-validation-command-undefined-repo landing 28127e322): the code-source context regenerates the current diff as `git diff <reviewed_base>...HEAD` with the literal repository HEAD (validate_review_staging.py, the `current_diff = cr_module.diff_bytes(code_repo, code_range["base"], "HEAD")` call near the --source-code-plan parsing), so --verification-head does not pin the code-family current diff; a record re-pinned to the landed range per lesson 163 reads stale three minutes after landing once main advances, and only validates in a detached checkout at the landing commit (verified OUTCOME pass there). Threading the validated OID into that diff_bytes call is the one-line fix candidate.
