# Backlog: dispatch ladder re-arm first action fails on automation-born sessions (emission suppression)

Status: covered (docs/history/plans/2026-11-03-dispatch-ladder-rearm-joint-hardening.md)
Priority: high
Class: fix-class
Origin class: learn Step 1.8 skills-corpus capture (2026-11-03 session-pattern harvest; first-hand witness in the capturing session)
Cluster: docs/history/backlog/2026-10-23-scheduling-asks-rearm-wording-candidates.md (same surface: the re-arm paragraphs in the scheduling contract and dispatch ladder; different defect class: wording precision versus emission reliability)
Added: 2026-11-03

## Observed versus expected

The dispatch ladder's child recipe requires an automation-born carrier child to emit a mutating automation primitive (create the recurring parent, or delete its own lingered spawner first) as its FIRST action. In one morning (2026-11-03) that step sat on the least-reliable joint three times: sessions decided the mutation, narrated it, and emitted repeated read-only listings instead (emission suppression, lesson 59's class):

- 00:57 stand-down: 4 listings, 0 mutations; recovered after live operator touch (scheduler-state rearm_note).
- ~10:03: a resume carrier's child suppressed its own spawner delete 3 times; the maintenance scheduler recurring parent ended the morning unrestored (scheduler-state turn_error, "2nd occurrence this lineage").
- ~10:05 (this session): a resume child suppressed the parent re-arm create 6 times; the daily 02:00 analysis carrier ended unrestored; the park (payload copy plus one memory-index line) carried the intent and the analysis work continued unblocked.

Both recurring parents went dark the same morning; loop liveness rode a 13:55 one-shot and fresh chats. Expected: the re-arm step does not depend on the automation-born session's own mutating emissions, or it carries an unbound fallback armed at recipe time.

## Reproduction evidence (trimmed)

- .ai-playbook/scheduler-state.json turn_error and rearm_note entries dated 2026-11-03 (quoted above).
- docs/tmp/pending-rearm-rem-parent-2026-11-03.md (park payload copy, created by the capturing session).
- Lesson 59 witness appended in-window by commit 981c62cc3 (in-context rule text does not immunize against the loop).

## Suspected root area

agents/skills/maintenance/zcode.md dispatch ladder step 2 and the re-arm recipes' first-action shape; the launchd clocked-order chain's pending promotion review (operative default only after the clocked-order discharge-verification gap row is dispositioned).

## Fix shape (arms, priced at plan time)

(1) Promotion review: activate the unbound launchd chain (or an equivalent deletion-tolerant carrier) as the operative re-arm and dispatch default for bound sessions, dispositioning the named gap row first. (2) Fresh-chat re-arm route: the child's first action becomes a file or state write that a fresh (never capped) session or the standing scheduler turn discharges, instead of a same-session mutating emission. (3) Keep the emission-suppression stand-down and park path as the backstop (it held all three times). No new gate or validator is proposed; the row removes a fragile ceremony dependency.
