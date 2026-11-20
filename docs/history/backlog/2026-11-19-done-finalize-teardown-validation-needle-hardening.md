# Validation-gate needle hardening for done-finalize-teardown-order-conflict

Driving force: code-quality
Cluster: none
Origin: code review r1 of the executed plan docs/history/plans/2026-11-18-done-finalize-teardown-order-conflict.md (record .ai-playbook/reviews/2026-11-19-done-finalize-teardown-order-conflict-code-review-r1.md; findings F1 Medium, F2 Low, F4 Low moved to overflow at the per-worker Low budget; witness branch 2026-11-18-done-finalize-teardown-order-conflict tip a5709e1e6355caf2120b253f1edd36637d88390a)

## Concern

The plan's Validation Commands block does not pin three claims its Outcome asserts, so a future re-run or a keep-both merge resolution can land while every gate stays green:

1. The Span B cut leg is unwitnessed: a landing inserting the post-finalize closeout paragraph but keeping the old Step 2 copy passes G1-G7 (measured). Add `expect_absent 'Operator branch closeout (operator-run' "$DONE"` beside the G1 absence pin; the needle is discriminating post-merge (0 on HEAD, 1 on the uncut landing, 1 on the main tip a1d50cda7 bytes).
2. The G3 position check pins the Step 6 section, not the prescribed slot after the "Finalize also assembles the report inputs" paragraph; a wrong-slot placement inside Step 6 passes. Anchor the lower bound on that paragraph text.
3. Span A's removal-reassignment tail clause ("never to this step") is referenced by no needle. Add `expect_count 'never to this step' "$DONE" 1`.

Optional (from dropped F3): the G3 integer comparisons fail open on multi-match heading anchors; taking the first match via `head -1` is cheap hardening.

Note: the plan bytes are certified by the r1 review; the needles land through a follow-up plan or an operator-directed validation-block amendment, not by editing the certified bytes in this run. The landing-time mitigation for the concrete merge risk (modify-vs-move conflict vs main a1d50cda7) is the standing union-of-intents resolution plus post-resolution re-verification re-grepping removed spans absent.
