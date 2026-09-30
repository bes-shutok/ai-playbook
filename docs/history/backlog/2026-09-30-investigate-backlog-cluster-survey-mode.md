- **Filed:** 2026-09-30
- **Status:** done (2026-09-30; executed+landed docs/history/plans/completed/2026-09-30-investigate-cluster-survey-anchored.md, squash main 85122e7e, exec review r1 ready=yes zero blocking)
- **Priority:** high (operator-directed superurgent, queue top, 2026-09-30)
- **Origin class:** self-serving (operator question 2026-09-30: why does investigate take only one backlog item at a time; direction: file the fix)
- **Driving force:** efficiency
- **Class:** fix-class

# Investigate: proactive whole-backlog cluster survey mode

The investigate skill's Stage 1 group discovery is anchored: it searches for siblings only of the single input item the maintenance scheduler hands it (maintenance duty (e): the highest-priority remaining ungrouped open backlog item, at most one investigation per turn). A cluster whose members never surface as the anchor — or whose link is missed on the first anchored pass — stays ungrouped until one of its members eventually becomes the top-priority pick, then self-heals at one-item-per-turn pacing. Grouped origins discovered late mean plans authored single-origin that must later be reconciled with sibling origins, or parallel sessions rejecting grouped origins as unrelated (the failure mode the 2026-09-27 roster-recording rule was written to prevent).

## Desired behavior

A survey capability that sweeps the entire open backlog for clusters (shared mechanism, shared surfaces, same defect class) regardless of which item is the anchor, so groups are discovered at survey pace, not anchor pace. Open design questions the plan must settle:

1. **Mode shape:** a standalone survey invocation of the investigate skill, a new scheduler duty in maintenance, or a widening of Stage 1's scan scope when invoked on an anchor. Each has different pacing and churn consequences.
2. **Output contract:** whether a survey emits full log entries for discovered clusters (competing with anchored entries in the dispatch queue) or annotates existing log entries / backlog items with rosters so the next anchored investigation picks the group up.
3. **Churn guard:** how a survey avoids re-reporting already-grouped origins every run — the existing skip rule (origins intersecting an existing log entry's `Origins:` line or a plans-root plan file) is the precedent to extend.
4. **Bidirectional contract:** the change touches the investigate/maintenance Integration Points pair, which must attest the same invocation contract from both sides (repo rule: verify the peer skill's actual steps when documenting its behavior); README catalog updates if the invocation surface changes.

Not in scope: changing the one-log-entry-per-investigation artifact rule, or the hard gate that investigate never executes or dispatches.
