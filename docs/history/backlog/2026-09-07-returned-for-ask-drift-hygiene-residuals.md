# Backlog: returned-for-ask drift-hygiene residuals (r7 exit round, all deferred)

Origin: r7 exit round of execute-plan 2026-09-04-returned-for-ask-semantics (docs/reviews/2026-09-07-2026-09-04-returned-for-ask-semantics-code-review-r7.md). Zero blocking findings; all eight residuals are drift-hygiene/wording items deferred because the final round must not mutate the reviewed digest. Consolidated from correctness-completeness, risk, contract-docs, and the design-simplicity exit hybrid.

Status: open
Priority: deferred (efficiency/token/simplicity triage 2026-09-11: process-cosmetic or archived-record value only; revisit only if it starts costing real review rounds or tokens)


## Items

1. **Unscoped stop branch (Medium)**: receiving-review Fix-risk closing (~L399): scope the "or, when it is the top-level loop agent of a non-interactive run, it applies the stop" branch to "a must-stay-blocking ask", mirroring the sibling parenthetical.
2. **Parallel exit restatement (Medium)**: execute-plan Step 3.5 (~L662-669) and review-loop exit paragraph (~L130) restate the exit-surfacing contract in unlinked prose; cross-link or point one at the other.
3. **Tangled Fix-risk paragraph (Medium)**: receiving-review ~L399: split the ~350-word paragraph into 2-3 named rules per the skill's list idiom.
4. **Relay stop-class phrasing (Low)**: execute-plan ~L669: name failure/timeout/interrupt inside the stop-class enumeration (review-loop already carries the explicit form).
5. **Unwired scoping input (Low)**: subagent-prompts step 7 / address-review prompt template: convey the top-level run's interactivity (or default the sub-agent to always return the recorded question).
6. **Record-element divergence (Low)**: review-staging definition says "(with the question to relay)"; call sites say "the fix-risk rationale and returned-for-ask marker": align element naming.
7. **Citation hygiene (Low)**: drop the "per the Fix-risk section" deference from execute-plan gate item 6's non-interactive leg; single canonical reconciliation-precedence sentence per file.

## See also
- docs/history/backlog/2026-09-07-plan-task3-returned-for-ask-wording-drift.md (plan-body drift + sibling-plan forward conflict; archive-time/execution-gate handling)
- UL 304 (defined once, referenced by pointer)
