# Deferred review nits from review-agents corpus family Task 3 (drive-by capture)

Driving force: external + code-quality (Step 1.2b intermediate-review candidates on the corpus-family execution; deferred so the reviewed digest stays binding).

Status: open (discharged 2026-09-28 by the corpus-family successor polish plan)

- Low (documentation corpus): `agents/skills/review-agents/documentation.md` Severity (phase 2) uses the plan-pinned temporal qualifier "the new severity-calibration row" in two sentences (carve-out and Do-not-assign reword); once the row is landed, "new" is stale. A future editor should reword to "the severity-calibration Category defaults row" (spaced form matching the heading; the hyphenated form was corrected in doing-code-review SKILL.md by the r1 review fix) together with the owning grep-pin update (the plan's Validation Commands pin the current wording; any plan edit forces a fresh review round).
- Low (testing): the `documentation#prose-relocatable-identifier-inventory` declaration window has only 122 chars of headroom (measured at execution; the earlier ~132 figure was an estimate) before the declaration; a future boundary-sentence extension longer than that fails the selftest (fail-loud, never silent). A future editor can trim the boundary sentence or widen the window.
