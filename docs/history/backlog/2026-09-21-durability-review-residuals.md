# Durability-plan review residuals (r1, 2026-09-21)

Driving force: the scheduler-ops-lanes-durability execution's Phase 3 r1 panel returned 0 blocking but several valid non-blocking residuals that were not fixed on the branch; this item keeps them durable. Status: open.

- Budget-guard decision log grows unboundedly with a full-file read under the shared guard lock on every allow invocation; add rotation/tail-read or a dated heartbeat sidecar (O(1) like the fired-marker), and document the `--hook-outcomes-log` test-override convention once for future suites.
- `quota_at_decision` field names (`percent_used`/`minutes_to_reset`) do not match the probe's output keys (`used_percent`/`minutes_remaining`), forcing a silent rename at transcription; align names or document the mapping at the Step 1 snapshot action. The snapshot-source enum value `pricing cache` has no producing condition anywhere (the pricing cache holds windows/multipliers, never a quota reading) — define it or drop it from all three surfaces.
- The authoring-claim O_EXCL create is demanded in prose but no executable mechanism (e.g. noclobber create) is pinned; pin a literal recipe plus a pin needle.
- Overlay: one sentence that a delete reflecting an already-gone record is success-shaped (confirm-listing TOCTOU residual), and date-tag the re-arm step-(1) recycling leg + "pending entry holding the recorded id" arm as migration-compat under the fresh-id model so a future simplifier does not delete live migration-period behavior.
- SKILL.md fresh-window rule's "well over an hour left" is non-mechanical; replace with a constant in a follow-up, and clarify whether D4 outcomes record `quota_at_decision` under "every lane decision".

Source: Phase 3 r1 panel (correctness-completeness, testing, design-simplicity, contract-docs, risk), 2026-09-21.

## r3 additions (final clean round, 2026-09-21)

- Claim protocol races in prompt-templates.md AUTHORING CLAIM duty/gate: (a) the stale-foreign-claim takeover deletes read-then-unlink without re-reading the file immediately before the unlink — two sessions racing the same stale claim can each delete the other's fresh claim; add a re-read-before-delete guard (delete only while it still names the same foreign session id with stale updated:); (b) ownership re-check failure (this session's claim was taken over) is report-only — the disowned session should stand down instead of continuing to author the same item; (c) a claim file with no parseable session: line has no named disposition (treat as foreign: fresh refuse, stale takeover).
- execute-plan discovery-ladder rung 1: a live parent between tasks (direct-continuation shape: no live claim, no done handoff, no blocked claim) resolves "no live session" without reaching rung 2's heartbeat; bound the closure to a terminal/completed workflow_state or fall through to rung 2.
- maintenance SKILL.md Step 3 near-reset branch: the now-relative survey snapshot's minutes ignore the dispatch's own start offset; record that the comparison uses the raw reading or add the offset (Step 4's fire-time leg still enforces at the slot).
- budget_guard_core module docstring says "always append" while lock-acquisition failure skips lines (code and README are correct); fix the docstring.
