Status: open
Priority: medium
Class: fix-class
Origin class: witnessed defect (2026-11-06 cross-session learn+investigate harvest over the prior 24h)
Cluster: docs/history/backlog/2026-10-31-malformed-closeout-baseline-json-refusal.md (same capture-contract surface; that row owns the malformed-JSON refusal shape) and docs/history/backlog/2026-11-02-stale-baseline-arm-byte-debt.md (same surface; that row owns the stale-baseline arm's byte debt); this row owns the entry-order trigger
Dedup probe: rg -il "baseline" docs/history/backlog/ (nearest: the malformed-JSON refusal row and the stale-baseline byte-debt row; both own refusal and byte-debt arms of the capture contract, neither owns the entry-order trigger; no merge)
Driving force: efficiency
Capture hygiene: scan-public-hygiene --files pass (2026-11-06)

# A back-to-back session chain skips the Phase 0 baseline capture; two same-evening late captures in one mandate chain

## Problem

Two interactive authoring sessions in the same evening (2026-11-05, roughly 18:25 and 19:21 WET, one mandate chain of back-to-back picks) entered plan-scoped work before the Phase 0 closeout-baseline capture: the first skipped the capture (recorded as a late-capture deviation), the second ran done setup post-edit and fell to the baseline-less closeout arm (manual scoped-copy digest plus late capture, recorded as a capture-failure deviation). The contract held both times: the deviations were recorded honestly and neither closeout corrupted. The friction is entry-order: in a chain of same-mandate sessions the session's attention starts at the inherited context (peer claims, prior picks, cleanup continuations), and the capture mandate lives in the execute-plan Phase 0 text that the entry moment never re-anchors.

## Observed vs expected

Observed: late or skipped Phase 0 baseline captures on chained entries, caught only as recorded deviations after the fact.
Expected: a chained entry treats the Phase 0 capture as its first owned action, exactly like a cold start; the entry-path text states this where the chain entry happens (next-pick and continuation flows), so the deviation arm stays a backstop rather than the operating mode.

## Evidence (trimmed)

- Run records of the two sessions: "Phase 0 closeout-baseline capture skipped (late capture)" and "done setup ran post-edit, Baseline-less closeout arm, late baseline capture as recorded capture-failure deviation".
- The contract text exists and is correct (execute-plan SKILL.md Phase 0: capture at Phase 0 before plan-scoped work, once, never late; resumed runs keep the original baseline by design); no entry-path text re-anchors the capture for chained entries.
- Two witnesses of the same deviation class within roughly one hour, different sessions, same mandate chain.

## Suspected root area

agents/skills/execute-plan/SKILL.md Phase 0 prose and the chained-entry flows of the maintenance auth/exec loop: a pointer-class clarification (one sentence at the entry path), no new gate; the deviation recording stays the failure backstop.

## Ship when

The chained-entry path states that the Phase 0 baseline capture precedes the first owned edit (or the sanctioned skip is recorded before work starts); the deviation arm remains the backstop; hygiene scan green; no gate or validator added.
