# Backlog: corrections chain refusal tuples and index pins

- **Filed:** 2026-10-21, from Phase 3 code review r1 of `corrections-chain-operator-ack-end-to-end`
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** fail-closed consistency
- **Class:** fix-class
- **Driving force:** security; secondary: testing
- **Skill/step:** `scripts/corrections_record.py`, `load_correction_authorizations` / `record_correction_authorization` catch tuples and state-parse legs
- **Cluster:** docs/history/backlog/completed/2026-10-16-corrections-chain-unclassified-mechanical-hops.md
- **Dedup probe:** extends the decode-error catch-tuple family (lessons 142-143) with the remaining escapes; no existing row covers RecursionError or the two test pins.

## Problem

Phase 3 review r1 (risk lens, verified by probe) found a deeply nested scheduler-state JSON makes `json.loads` raise `RecursionError`, which the `(OSError, ValueError)` catch tuples at the three state-read sites (verifier load, writer pre-read, writer drift re-read) do not catch; the writer's `json.dumps` re-serialization sits outside any try. The outcome is a bare traceback instead of the named `unresolvable witness ... not decodable JSON` refusal. Direction is fail-closed (a crash never passes a gate) and the input is unreachable from sanctioned writers, hence non-blocking, but it is the last escape of the malformed-state crash class this plan otherwise closed.

Same round, testing lens found two unwitnessed legs: the valid-JSON non-object state refusal (`is not a JSON object`) has no test in any of the four homes, and no test pins the classification bypass index alignment for an operator-acked hop at index greater than zero in a mixed multi-hop chain (`state_acked_hops` built over `rows` consumed over `enumerate(history[1:])`); a mixed-chain probe against HEAD showed the implementation correct today, so both are regression-guard gaps.

## Expected

Add `RecursionError` to the three catch tuples (and guard the writer's dumps), mirroring the landed decode-error fix; add the non-object state refusal arm and the mixed multi-hop bypass index pin.
