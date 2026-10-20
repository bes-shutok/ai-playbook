# Backlog: operator-acked contract doc residues

- **Filed:** 2026-10-21, from Phase 3 code review r1 of `corrections-chain-operator-ack-end-to-end`
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** documentation drift
- **Class:** fix-class
- **Driving force:** documentation; secondary: security disclosure
- **Skill/step:** `agents/skills/review-staging/SKILL.md` operator-acked kind definition; `agents/hooks/skill-gate/README.md` alarm paragraph; `scripts/session_channel.py` docstring and `agents/hooks/lessons-recall/README.md` pinned-idiom sentence; `agents/skills/maintenance/state-file.md` correction_authorizations paragraph
- **Cluster:** docs/history/backlog/2026-10-21-corrections-chain-writer-discipline-consolidation.md; docs/history/backlog/2026-10-20-validation-authoring-rule29-stale-sanctioned-route.md
- **Dedup probe:** r1 contract-docs and correctness lens doc findings; lesson 151's sweep covered disclaimers and case-space inventories at Task 4 time, these are the cross-file residues it could not see.

## Problem

Four doc residues from Phase 3 r1 (correctness Medium, the rest Low; executable behavior stays correct and fail-closed in every case):

1. The review-staging operator-acked kind definition is family-blind: it now describes only the plan-family state route (fixed selector, `author_session_id`, primary-state resolution) while the code-family turn-record route (`resolve_ack_receipt` via the code gate's `--ack-witness`) remains live and was covered by the pre-change wording. Following the text for a code-family row refuses fail-closed with no discoverable route.
2. The skill-gate README's trailing sentence still says Codex/Cursor/agy empty is documented steady state unconditionally, one paragraph below the all-source empty rule it now defers to.
3. The session-channel single-source consumer inventory (helper docstring and the lessons-recall pinned-idiom sentence) still names only the two hook adapters and the plans-skill marker recipe; the corrections-chain session-identity derivations (writer identity, operator-acked emission author) are the new third consumer class.
4. The forgeable-environment trust boundary of the distinct-session authorization (workflow-compliance evidence, never an enforced boundary against a process controlling its own env) is stated only in the plan document, which archives on completion; the durable contracts (state-file.md field paragraph, plans rule 2) carry no strength qualifier.

## Expected

Scope the kind definition per family (one sentence deferring the code-family witness shape to the `--ack-witness` contract); qualify the skill-gate README sentence with "only when every supported source is unset or empty"; widen both consumer inventories with the corrections-chain derivations; add the workflow-evidence qualifier clause to the state-file paragraph (offsettable under the anti-growth rule).
