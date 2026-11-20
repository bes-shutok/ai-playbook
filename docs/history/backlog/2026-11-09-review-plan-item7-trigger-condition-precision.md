# Backlog: review-plan Step 5 item 7 trigger-condition precision polish

- **Status:** open
- **Driving force:** efficiency

Origin: Phase 3 lens 1 (correctness) finding of the review-fold-premise-verification execution run (branch 2026-11-09-review-fold-premise-verification, commit 88662a527).

Problem: review-plan Step 5 item 7's parenthetical says the reconciliation fold batch "already runs the sibling accounting re-derivation under review-reconciliation's Fold-propagation probe" without restating the probe's trigger condition (fold-propagation trigger class). Sibling item 6 carries that condition explicitly ("when its trigger was fold-propagation class"); the on-disk source (agents/skills/review-reconciliation/SKILL.md lines 99, 130) conditions the re-run on trigger class. The implemented text transcribes the plan criterion verbatim, so this is precision polish, not execution drift.

Fix: add the trigger-class condition to item 7's parenthetical (or cross-reference item 6's condition) in one bounded edit; re-run the plan's validation trio.
