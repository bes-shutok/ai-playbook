# Backlog: darkness detection concurrent-done double-create race

Status: open
Workflow: backlog
Origin: 2026-09-16-maintenance-scheduler-liveness r1 review (finding R-5, deferred to backlog by the triage as accepted-by-design)
Severity: Low (accepted residual; narrow window, self-healing aftermath)
Scope: agents/skills/maintenance/SKILL.md (rearm-on-touch surfaces), agents/skills/done/SKILL.md (one-line pointer; frozen otherwise)

## Problem

Darkness detection has no self-contained in-repo actor that owns the
re-arm decision atomically. The in-repo observer is the rearm-on-touch
check, which runs in a touching session before that session takes the done
lock. Two done sessions starting concurrently in a repository whose parent
is dark can both run the check, both classify darkness (neither has taken
the lock yet, and the re-arm create happens before either could exclude the
other), and both create a recurring parent: a duplicate-parent outcome that
the duplicate-parent tripwire then flags for a human.

The accepted-by-design remedy was deferred when the liveness plan was
authored: an external launchd heartbeat (a self-contained detector outside
any session) was considered and rejected for that plan to avoid new
infrastructure, with the existing idle-time watchdog and rearm-on-touch
coverage named as sufficient detectors.

## Consequence

In the race window, a dark repository gains two parents instead of one. The
aftermath is fail-safe, not fail-alive: the duplicate-parent tripwire trips
both lane guards, records the duplicate reason in the state file, and stops
scheduling until a human collapses the duplicates; no runaway loop occurs.
The residual is the human toil and one wasted automation record.

Mitigation already in place: the tripwire described above, plus the Step 1
memory-note read-back that adopts a live ENABLED recognition match when the
recorded id is lost.

## Fix sketch (when picked up)

Preferred: implement the launchd heartbeat deferred by the plan's Decision
points requiring a grill (the launchd external heartbeat entry, which names
the idle-time watchdog and rearm-on-touch as the sufficient detectors), making darkness detection self-contained (the heartbeat owns a
repo-keyed lock file or claims the state file's `parent_absent_since` field
as its claim marker before creating, so a second detector sees the claim and
stands down). Minimal alternative: serialize the in-repo observers by having
the rearm-on-touch check take the done lock (or a dedicated re-arm lock)
before its create path, accepting that a touch session then briefly holds a
lock the done skill also uses; document the lock's re-arm use in both skills
and add a pins-suite needle for the lock acquisition ordering.

## Corpus note (2026-09-17, r2 review)

The same accepted family has a second member: the re-arm duty's step (3)
recycle leg has no exists-signal either. A child session decides from a
listing that showed no parent, but a concurrent actor can arm one between
that listing and the recycle create; the create then succeeds and the
repository holds two parents. A stale negative listing can therefore create
a duplicate parent exactly as two concurrent done sessions can. Same
accepted family, same mitigation: the duplicate-parent tripwire flags the
outcome for a human, and no runaway loop occurs.

## Corpus note (2026-09-17, r3 review)

A third member of the same accepted family: the concurrent-actor
single-record recycling race. Two overlapping scheduler turns can both walk
the dispatch ladder's confirm arm on the same recorded record: each lists
once, each sees the armed parent confirmation, and both proceed with the
recycling update of that one record; the last update wins and the loser's
dispatched child payload is silently overwritten, leaving a ghost pending
children[] entry whose lane hold runs for the full six-hour horizon while
no real child is in flight. The root cause is that the update primitive
carries no compare-and-swap, so the ladder cannot detect the lost update.
Same accepted family, same mitigation shape: the window is seconds wide,
the ghost entry self-releases at its horizon, and the aftermath stays
fail-safe (a quiet lane gap or a human-visible turn_error), never a runaway
loop. A candidate fix is a state-file intent token written before the
recycling update and compared after it, at the cost of one extra targeted
edit per recycling dispatch.

## Corpus note (2026-09-17, r4 review)

A fourth member of the same accepted family: stacked terminal refusals on
the successor path. When a completing execution child's successor duty
exhausts both dispatch legs (the reshape and its delete-plus-create
fallback) and the parent re-create is also refused, the session ends with
the loop dark and a repo-keyed `successor-chain-failed` memory note as the
only marker. The note's only automated reader, the scheduler turn's Step 1
survey read-back, cannot run while the loop is dark: the parent the leg
failed to re-create is the thing that fires the turn. The note is surfaced
by the next touch session's or human read-back of the memory index, and by
the next scheduler turn's survey read-back only when the loop has been
re-armed by some actor; no watchdog exists on this path. Same accepted
family (darkness with a fail-safe aftermath, never a runaway loop), same
candidate fix family (a self-contained detector that does not depend on the
loop it detects, or a touch-session read-back that re-arms before it
decides).
