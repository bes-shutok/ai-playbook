# Backlog: rearm-form-field-writer-attribution r3 residual gate hardenings

Status: open
Workflow: backlog
Source: rearm-form-field-writer-attribution plan review r3 (ready=yes zero blocking; four non-blocking Lows deferred digest-frozen so the certified bytes 8b101794 could land without a fourth round)
Severity: Low
Priority: low
Consumer urgency: future executors and re-certifications of the parent_automation_form amendments; each item is a one-line gate addition to the plan's Validation Commands block or a documented coverage limit.
Driving force: correctness

## Problem

The certified plan exits r3 with four non-blocking gate-coverage Lows:

1. zcode.md's turn-start bullet form-branch sentence (`a recorded recurring form or form-unknown keeps the delete at the cap-refused create`, line 32) has no post-edit full-text sentinel; only its `cap-refused create` substring count (= 2) covers it, so a reword preserving the substring exits green. The SKILL.md twin has a full-text sentinel.
2. The carry-forward replacement's operative tail (`writes no form, so the rewrite must carry it`) is unpinned; a tail-truncating partial apply passes every gate line.
3. The asymmetry parenthetical is pinned by head only (`deliberately asymmetric subsets`); the insertion adjacency (`dispatch-discipline bounds (`) and the parenthetical tail are unpinned post-edit.
4. Design Invariant CR1's mechanical enforcement is partial for two adjacent spans: the zero-listings exception list (`(the state-file-cannot-decide listing, the pending-rearm armed verification)`) next to Task 2's insertion point, and the `read keys on the form recorded beside the currently recorded parent_automation_id` phrase next to Task 1's field-paragraph edit; both are covered only by the pre-edit drift check.

## Suggested fix

At the next natural edit of the plan's Validation Commands block (for example during execution closeout or a re-certification), add the three one-line gates: `rg -F -q 'a recorded recurring form or form-unknown keeps the delete at the cap-refused create' agents/skills/maintenance/zcode.md`; `rg -q 'writes no form, so the rewrite must carry it' agents/skills/maintenance/SKILL.md`; `rg -F -q 'dispatch-discipline bounds (the two zero-listings exception lists are deliberately asymmetric subsets' agents/skills/maintenance/zcode.md`; and either add sentinels for the two CR1-adjacent spans or record their coverage limit in the invariant text.

## Why not fixed now

Each addition changes the certified digest and would force a fourth full round; the Lows are additive hardenings, not correctness gaps (the testing worker's simulation showed the certified gates already trip all five plausible wrong-edit shapes), and the repo's digest-frozen deferral convention routes them here instead.

Promote: fold into the parent plan's next re-certification round, or a small gates-hardening plan under `{plans_dir}`; on completion fold disposition into the completed plan, then delete this file.

capture hygiene: scan-public-hygiene --files pass (re-run after edits).
