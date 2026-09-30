# User direct request must override guard stand-downs

- **Filed:** 2026-09-28
- **Origin:** operator correction after the 18:21 interactive maintenance turn stood down D3 instead of executing
- **Status:** done (2026-09-30; executed+landed squash main 3f006be3 via docs/history/plans/completed/2026-09-30-user-directed-override-for-interactive-guard-standdowns.md)
- **Priority:** high
- **Origin class:** self-serving

## Problem

An interactive session given the explicit directive "execute plans one by one" observed a live peer on the primary checkout (fresh done-lock hold, uncommitted peer dirt, live authoring claim) and resolved the whole turn to D3 stand-down, reporting instead of working. The operator's correction: **"you shouldn't have done this."** An unattended scheduler turn standing down is correct behavior (it has no operator to decide with), but an interactive session carrying an explicit user directive has the operator present — the stand-down decision belongs to the user, not to the guard. The guards exist to prevent *unattended* sessions from colliding with peers; they were written before interactive user-directed sessions shared the same code path, and the maintenance skill currently gives an interactive session no way to say "the user told me to proceed anyway, record the risk and go."

The practical failure is lost throughput and a broken expectation: the user asked for execution, got a survey report, and had to re-issue the request with an explicit override.

## Fix shape

- Add a "User-directed override" rule to the maintenance skill (and mirror in the runtime overlay): when the session is interactive (the user is present and issued the current directive) and a guard that would only *defer or stand down* (G1e/G1a occupancy, G3 done-lock hold, landing-gate outstanding runs) trips, the session must (a) state the tripped guard and its evidence in one line, (b) choose a non-colliding execution surface — its own per-execution worktree (P57 isolation), landing-completion work for a *completed* unlanded run, or a target disjoint from the peer's in-flight one (verify disjointness from peer dirt/claims before selecting), and (c) proceed — instead of standing down. Never steal a peer's fresh lock or touch its in-flight target; isolation, not inaction, is the answer.
- Guards that protect *integrity* (G2 failure cap, corrupted merge-lock meta, foreign-dirt gates) are not overridable; an interactive override is recorded in `decision_reason` with the literal `user-directed-override` plus the tripped guard's name.
- Unattended sessions (automation-born, no live user turn) keep today's stand-down semantics unchanged — the override predicate is "the current turn's directive came from a live user message," not "the session feels confident."
- Add a witness-based self-test or review checklist item so future review rounds verify the override predicate is user-presence-based, not mood-based.

## Witness

- 2026-09-28 18:21 interactive turn: directive "execute plans one by one"; survey found live peer (done-lock `main-exec-done` 35s old, p71 claim fresh, peer dirt on scripts); turn recorded D3 stand-down and reported. Operator corrected within the same turn: "you shouldn't have done this. Please create backlog... and then proceed with the execution." On re-survey 18:24 the peer had already squash-landed maintenance-autonomous-pipeline (05644b4f) and p71 authoring (b463d3a3) — the stand-down bought nothing; a disjoint-target execution would have been safe and productive.
