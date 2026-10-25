# Backlog: scheduling-ask verb contract lacks an ambiguous clock-time confirmation rule

Status: open
Priority: high
Class: fence-class (a one-clause confirmation rule; no machinery)
Origin class: session-communication (learn Step 1 over the 2026-10-24 carrier-arming session; see development_lessons.md #220)
Driving force: reliability (witnessed 2026-10-24: the ask "schedule at 9-17 pm" was misread twice - first collapsed to a single 21:00 fire, then re-read as an hourly 21:00-16:59 window - before the intended 21:17 reading surfaced via operator correction; two avoidable correction rounds, each a patched carrier)

## Gap

The repo guidelines' "Scheduling asks (verb contract)" section binds how a schedule ask is satisfied (session-owned automation, deconfliction, fallbacks) but says nothing about resolving the ask's TIME TOKEN itself. A compact hour-minute shorthand ("9-17", "9h17") plus an am/pm marker reads as a range or a pair of endpoints as easily as the intended single time H:MM, and the contract's "schedules at ... never executes the payload in the same turn" leaves the session to arm on an inferred reading with no confirmation arm.

## Candidate remedy

One clause in the verb contract: when the ask's time token is a compact `H-M`/`HhMM` form or is otherwise ambiguous, the scheduling session reads it as the single time H:MM with the am/pm marker applied, and confirms by asking one question whose options each name the CONCRETE resolved clock time (for example "21:17"), never a restatement of the shorthand; no carrier is armed on an inferred reading.

## Non-goals

No new gate, script, or validator: the rule is interpretive and pre-arming, so machinery cannot catch it after the fact. Removal-shaped; no admission wording owed.
