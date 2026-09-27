# Deferred review nits from review-agents corpus family Task 1 (drive-by capture)

Driving force: external + code-quality (intermediate-review candidates from execute-plan Step 1.2b on the corpus-family execution; deferring keeps the reviewed digest binding while preserving the findings durably).

Status: open

- Low (testing#non-attributing-span-asserts): `scripts/test_review_agent_doors.py::test_panel_signal_names_both_doors` asserts the migration-renumber trigger, the dual-entry trigger, and each worker pairing as four independent full-text spans; a future reword attaching a pairing to the wrong trigger branch keeps the selftest green. Fix: replace with two compound-span asserts matching the landed bullet text verbatim.
- Low (registry-integrity gap): the targeted-follow-up bullet in `agents/skills/review-agents/review-panel-selection.md` carries the two new door ids as cross-pointers with no test pin; a silent deletion of the parenthetical fails no gate. Fix: add `assertIn` pins for `architecture#dual-surface-policy-parity` and `testing#cross-surface-policy-witness` in the panel-signal test.
- Info (consistency#baseline-count-comment-drift): the corpus-family plan's Validation Commands comment reads "three landed plus eight new" declaration tests but the base commit carries four landed `*_declared` tests; the `-ge 11` count pin still passes at the true total of 12. A future editor of the (now archived) plan or a successor item should correct the comment.
