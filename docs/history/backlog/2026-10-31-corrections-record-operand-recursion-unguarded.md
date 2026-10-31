Filed: 2026-10-31
Status: open
Workflow: backlog
Priority: low
Origin class: consumer-feedback
Class: fix-class
Skill-step: execute-plan Step 1.2b intermediate review (run corrections-chain-recursion-refusal-and-pins)
Cluster: corrections-chain-recursion-refusal-and-pins
Dedup probe: "load_corrections" "append_corrections" "RecursionError" in docs/history/backlog/ - no sibling row names the corrections-record operand sites

# Backlog: Contain RecursionError at the corrections-record operand sites

Driving force: code-quality

`load_corrections` (scripts/corrections_record.py:339-340) and `append_corrections` (parse at :1477-1478, `json.dumps` at :1494) catch only `(ValueError, UnicodeDecodeError)` / serialize outside any recursion guard, so an adversarially deep corrections-record operand escapes as a bare `RecursionError` instead of the named "record operand is not decodable JSON" refusal. Fail-closed direction (a crash never grants authority), so Low severity.

Origin: witness from the 2026-10-29-corrections-chain-recursion-refusal-and-pins execution intermediate review (both lens workers, 2026-10-31); extends the decode-error catch-tuple family of development_lessons #142. Suggested fix mirrors that plan's landed shape: add `RecursionError` to the two parse except tuples AND to the append guard's except tuple (`except OSError` at :1498 cannot catch RecursionError), and move the append `dumps` inside that guard.

Accepted residuals recorded by the Phase 3 r1 panel (2026-10-31), same family:

- The scheduler-state writer's serialization RecursionError renders under the append-leg message "the scheduler state file is not writable: ..." (scripts/corrections_record.py:1333-1336), a false cause prefix for the recursion family; plan-pinned verbatim leg reuse. At the next contract-touching change, keep the leg name but render "not writable" only for the OSError family.
- The same writer guard does not catch the MemoryError / giant-string failure class of the same dumps call (parse-clean ~100k-deep state serializes to ~20GB with indent=2); fail-closed, no authority impact. Fold a MemoryError-arm decision (widen the guard, or record the indent-amplification as an accepted writer-contract risk) into the fix this row drives.

Capture hygiene: scan-public-hygiene --files pass (2026-10-31).
