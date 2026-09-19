# Backlog: P11 obligation-probe gaps and new-marker robustness notes

Status: open
Origin: P11 execution review r1 (F12, F13, F14; workers testing + correctness-completeness)
Date: 2026-09-19

Three related residuals from the P11 execution:
1. Obligation-probe gaps (F12, two-class deferral per ADR-0002): the freeze-citation sentence (Task 3 obligation 4), the cap-row-pointer sub-obligation, and Task 5's composition-note check have no `expect_match` spans in the plan's Validation Commands; deleting those deliverables keeps the block green.
2. New-marker spellings (F13): `*(New)*` (capitalized) and the historical backticked-paren shape are treated as absent by clause (c), producing a false nonexistent-path violation; no corpus exposure today.
3. Receipt audit gap (F14): the `archive_gate` receipt does not record that the residual-exit path fired or echo the policy, so runtime_state.json is indistinguishable post-archive between a clean-round and a residual-exit archive; the prose manifest line is the only audit record (tension with the "sanctioned exits stay auditable" invariant).

Trigger: the archive sweep of this plan group (~Oct-Nov 2026) or any edit to the touched surfaces.
