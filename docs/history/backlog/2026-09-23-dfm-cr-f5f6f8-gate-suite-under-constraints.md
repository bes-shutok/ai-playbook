# Backlog: dfm code-review r1 F5/F6/F8 + r2 F1 — plan Validation-Commands under-constraints

- Backlog origin: docs/reviews/2026-09-23-driving-force-gist-tldr-metadata-code-review-r1.md F5, F6, F8 (Low, non-blocking, deferred; extended 2026-09-23 with r2 F1 instances 4-6)
- Driving force: external (deferred findings from the driving-force/gist-tldr plan execution)
- Status: open

Three measured gaps in the plan's gate suite (requires editing the archived plan's Validation Commands or their successors; plan bytes frozen post-cert, so deferred):
1. (F5) Exactly-once count gates see only the awk-extracted template region; a duplicate placeholder literal outside it passes. Add whole-file count gates `grep -cF ... -eq 1`.
2. (F6) `grep -q "contradicts the plan"` is satisfied by the boundary sixth family without any pricing sentence; narrow to `contradicts the plan's content is blocking`.
3. (F8) Taxonomy tail (`external` must-cite-source) and the park-triage half of the justification rule have no needles; add tail-span and `park-triage would or would not` needles.

4. (r2 F1) `grep -q "Declaration audit"` over `$REV` — the r1 F2 producer step is ungated; deleting review-plan Step 1 item 8 leaves all gates green.
5. (r2 F1) `grep -q "otherwise the line reads \`Backlog origin: none\`"` over `$PLANS` — the r1 F1 conditionality bracket is ungated.
6. (r2 F1) `grep -q "four driving principles (\`efficiency\`, \`token-usage\`, \`simplicity\`, \`code-quality\`)"` over `$PLANS` — the r1 F3 enumeration is ungated.
