# Backlog: standing loop-mode directives have no durable carrier that survives parent re-arms

Captured: 2026-09-21 (operator analysis after the 2026-09-20 authoring-only loop start produced zero plans overnight)
Status: open
Priority: high
Workflow: backlog

## What was witnessed

The 2026-09-20 split-loop directive ("maintenance loop: authoring lane only, one plan at a time"; the peer chain owns executions) was carried by three prose surfaces only: (1) an AUTHORING-ONLY MODE paragraph appended to the recurring parent's prompt, (2) decision_reason strings in the scheduler state file, (3) agent memory notes. Overnight the parent died (absent since 21:37Z) and both re-arm attempts failed (emission-suppression guard stand-down at 23:53; primitive-absence escalation in execution child automation-636eef07 at 00:45Z). The only carriers that survived were prose: each rearm_note had to instruct the next actor that the parent "MUST be created with the AUTHORING-ONLY MODE paragraph appended". Had any actor re-armed from the recipe text alone — as the child blueprints literally prescribe ("create the parent exactly per the recipe") — the restored parent would have been pure dual-lane, and a later tick could have dispatched an execution child against the standing directive with nothing but an unread memory note in its way.

Root causes, in order:

1. **The mode lives in the parent prompt, and every parent re-creation path rebuilds that prompt from the pure recipe template.** The child blueprints' re-arm duties and fallback legs say "create the parent exactly per the recipe"; the recipe has no mode slot, so the appendix has no sanctioned home and dies with the record it rides.
2. **The state schema has no loop-mode field, and its carry-forward list is closed.** Even an ad-hoc top-level field would be dropped by the next Step 6 whole-document rewrite, which carries forward only the enumerated fields (parent_automation_id, rearm_note, successor-appended children[] entries, pending_dispatch / parent_absent_since, park_proposals, pricing_cache).
3. **Memory notes are advisory, not binding.** Step 1's read-back rules name specific note types (loop-parent-missing, successor-chain-failed, pricing-verification-failed, park-proposal); a mode directive has no reader rule tied to any decision, so a turn that never opens the note runs dual-lane legally.

## Suggested fix

- Add an additive `loop_mode` field to the scheduler state (schema 4, no version bump, per the additive-no-bump precedent): `{"mode": "authoring-only" | "dual" | "execution-only", "directive": "<user wording>", "set_at": "<iso>", "note": "<carrier instructions>"}`, and add it to the Step 6 carry-forward list explicitly.
- Step 3 enforcement: the per-lane decision reads `loop_mode` before D1/D4/D2, so a pure-prompt turn still honors the directive and records it in decision_reason (resolution semantics identical to the mode paragraph: authoring-only resolves D1 and D4 to D3).
- Step 0 self-heal: when the armed parent's prompt lacks the mode appendix that a non-dual `loop_mode` requires, re-append it with one update-primitive call, changing nothing else (this exact self-heal ran in the 2026-09-20 23:51 payload design and is the model for the pinned version).
- Child re-arm/re-create legs (both blueprints): when re-creating the parent, read `loop_mode` from the state file and append the mode paragraph from the field's directive; the recipe gains a "mode appendix sourced from state" clause so "exactly per the recipe" includes it.
- Pins-suite updates for the new field, the carry-forward entry, and the enforcement sentences.

## Sequencing constraint

Touches the same files as the in-flight scheduler-ops-lanes-durability execution (agents/skills/maintenance/SKILL.md state-schema and Step 6 sections). Sequence after it lands; do not run the two in parallel (same back-to-back constraint the 2026-09-20 evening ranking pins for the SKILL.md-rewriting pair).

## Evidence pointers

- State file history 2026-09-20/21: rearm_note texts (both carried the mode instruction as prose only); parent_automation_id churn 5652f65a → null → automation-96938576 (hand re-armed 2026-09-21 ~07:11 local WITH the appendix).
- Memory note `maintenance-authoring-only-mode` (the durable directive copy that did survive; also records the split: authoring side loop, execution side peer chain).
- The recovered parent's prompt carries the appendix by hand today; the NEXT child re-arm will wipe it again unless this item lands first.
- Related: `2026-09-21-successor-duty-primitive-absence-park-fallback.md` (re-arm recovery record), `2026-09-20-maintenance-primitive-emission-suppression-and-resume-carriers.md` (suppression witness), `2026-09-19-scheduler-toolset-precheck-before-dispatch.md` (precheck twin).
