Status: open
Priority: high
Class: fix-class
Cluster: docs/history/backlog/2026-11-03-review-plan-cap-closure-seal-anchor-composition.md (same surface and defect class: the seal duty text versus the validator seal contract)
Origin class: learn Step 1.8 (skill-usage issue capture, witnessed in an authoring closeout, 2026-11-03)

# review-plan seal duty text omits the full-40-hex commit-field requirement the validator enforces

Skill and step: `agents/skills/review-plan/SKILL.md`, the Round-close seal duty (plan family) - the duty's paragraph, not its example.

Observed: the duty's paragraph names the four fields `load_seal_entry` reads but nowhere states the field-value shape the seal resolver enforces: `HEX40_RE` in `scripts/corrections_record.py` (`load_seal_entry`) accepts only full 40-hex values for `round_start_commit` and `round_close_commit`, and any abbreviated sha parses the entry as unresolvable, degrading the round's certification to the exact-match digest rule (the `corrections grading degraded` warning). The duty's own example block is not at fault - it shows full-form placeholder OIDs (`round_start_commit: 1111111111111111111111111111111111111111`, `round_close_commit: 2222222222222222222222222222222222222222`), so copying it verbatim produces a resolvable shape.

Correction record (2026-11-03, re-derivation fence): this row was first filed claiming the example block itself carries a short anchor (`round_start_commit: 0903abc4`); the fence's two-command disk re-derivation found 0 hits for that value in the working tree and at HEAD, and the example's actual placeholders are full-form. The short anchors behind the witnessed failures came from the working-tree cert corpus's own short-form exemplars (`.ai-playbook/review-certs/*.md` written before HEX40 landed, e.g. `review-plan-project-strictness.md`, `worktree-removal-migration-gate.md`) plus the paragraph's silence - the defect home is the duty paragraph's missing shape clause, not the example.

Expected: the duty paragraph states, in one clause, that both commit fields take full 40-hex ids and that an abbreviated sha degrades the round (the corpus lesson #32 cross-referenced), so a drafter abbreviating an oid - the natural reflex the cert corpus's older exemplars model - is corrected at the primary reference.

Evidence: third witness of development_lessons.md #32 (2026-11-02, an authoring closeout): short 9-hex commit fields read as unresolved, rewritten full-form resolved. Fourth witness (2026-11-03, an authoring closeout): same degraded warning from short anchors; the re-derivation fence then falsified the initial attribution to the skill's example and localized the gap to the paragraph (this row's correction record above).

Environment: playbook repo, ZCode runtime, 2026-11-03; repo copy of the skill (vendored runtime copies inherit the same text).

Suspected root area: the duty paragraph predates the validator's HEX40 field-shape gate (introduced in commit 294e91068) and was never extended with the shape requirement; the example happened to carry full-form placeholders, masking the gap for verbatim copiers.

Remedy sketch: add one clause to the duty paragraph stating both commit fields take full 40-hex ids and abbreviated forms degrade the round (cross-reference corpus lesson #32); verify by drafting a seal from the paragraph alone with a deliberately abbreviated oid and confirming the staging validator's degraded warning, then with the full form and confirming resolution.
