# Backlog: matched-line claim clearance names an unreachable takeover leg and the resolver pin does not reach the adoption path

- **Filed:** 2026-11-19, execution of docs/history/plans/2026-11-13-session-identity-runtime-channel-duty.md (Phase 3 r1 focused panel, three lenses, zero blocking)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Class:** fix-class (duty-text reachability gap)
- **Origin class:** witnessed Phase 3 finding
- **Skill/step:** `agents/skills/maintenance/template-authoring.md` AUTHORING CLAIM duty (matched-line deletion gate; identity resolver firing point)
- **Cluster:** docs/history/plans/2026-11-13-session-identity-runtime-channel-duty.md (the executed plan whose Terms pin the inherited wording; the plan's own r4 certification carries the same clearance pair)

## Problem

Two non-blocking Phase 3 findings on the delivered duty text. (1) The matched-line deletion gate names the stale-foreign-claim takeover as a clearance path for a fresh claim whose session line matches the discovering session, but the takeover arm's unchanged precondition keys on a session id other than the discovering session's, so that leg is unreachable from the refusing session and only the operator path can clear such a claim (safe direction: refuse-and-preserve; wording inherited from the plan Terms). (2) The identity resolver pin fires at the foreign-claim fire-time gate's entry, while the claim-adoption arm performs identity-keyed classification and a session-id-line rewrite before that gate reads the claim, so the pin's firing point and loud-refusal class do not reach the adoption route (narrow blast radius: wall-carrier authoring prompts). Two smaller observations folded here: the compression dropped the payload-mirror report's first-line positional pin with no consumer; the CHANGELOG's growth crossed its advisory byte cap (a new advisory ratchet row, the standing record).

## Expected

One authoring pass: either extend the takeover arm's precondition to admit a matched-line claim whose updated: is stale past one cadence period (making the named clearance leg reachable), or reword the deletion gate to name the operator as the sole clearance path for the matched class; and either move the resolver firing point to cover the adoption route's identity-keyed classification or scope the pin's stated reach explicitly to the foreign-claim gate route.
