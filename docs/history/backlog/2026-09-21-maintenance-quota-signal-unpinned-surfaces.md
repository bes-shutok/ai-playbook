# Backlog: maintenance in-session dispatch surfaces lack pin coverage

Status: open
Origin: execute-plan run 2026-09-20-quota-aware-scheduling-semantics, Task 5 Step 1.2b r1 (testing lens observations)
Driving force: the Task 5 acceptance pins cover the D2 span and the stand-down gate only; the (in-session) target-marker convention, the null-automation-id recording rule, the schema example's quota_signal field, and the 2026-09-20 Revisions ledger entry have no pin or grep gate, so a silent revert of any of them stays green everywhere.

Proposed direction: add region-scoped pins (per the pins script's own convention for cross-file groups) for the (in-session) marker in maintenance SKILL.md and the schema-block quota_signal line; decide whether ledger entries deserve pins at all (precedent warns whole-file greps are satisfiable by ledger copies).

Found 2026-09-21; deferred per the backlog-deferral default (non-blocking, plan mandates exactly two pins).
