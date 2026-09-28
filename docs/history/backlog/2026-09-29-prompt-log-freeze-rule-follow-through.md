Status: open
Priority: medium
Workflow: backlog
Class: gate consistency (the freeze rule's consumer surfaces lag the landed rule; one predicate ambiguity)
Driving force: correctness

# Prompt-log freeze rule follow-through: investigate integration claim, in-session self-freeze, freshness bound, regression witness

## Problem

The prompt-log freeze rule landed 2026-09-29 (commits 6503b763 + 45db30f8: the log's standing rules plus the maintenance skill's queue-depth token, duty (b) "prune and freeze", duty (c) "top surviving unfrozen entry", duty (h)). The pins suite holds and the doc-registry validator is clean, but four consumer-side residues remain:

1. **Integration Points under-claim (investigate):** `agents/skills/investigate/SKILL.md` line 58 (Integration Points, maintenance consumer) says the scheduler monitor "reads the emitted entries for its read, prune, and dispatch duties" — the duties it enumerates are now stale: duty (b) is prune AND freeze. The bidirectional-integration rule requires each side's claim to match the other's actual steps.
2. **No self-freeze at in-session authoring start:** when the monitor's duty (c) authors a log entry in-session, nothing writes the entry's `Frozen:` line at that moment — the entry stays unfrozen during its own authoring and is only frozen by the NEXT turn's duty (b) via the claim-file witness. A concurrent session in that window reads the entry as dispatchable until it runs its own claim check. The witness (the slug-keyed claim file) already exists; the mark-writing duty does not.
3. **Freshness bound unstated:** the freeze predicate says "a live authoring claim file" without defining live. The corpus convention (the `G1a` discovery arm) bounds claim freshness at one cadence period and routes stale claims through takeover, not freeze; the freeze rule should name that bound instead of leaving "live" to inference.
4. **No regression witness:** nothing pins or self-tests the freeze rule text (the log's freeze bullet, the duty (b) freeze clause), so a wholesale rewrite of the duties bullet could silently drop freeze the way the S15 re-key narrowed a pin's coverage.

## Observed versus expected

- Observed: investigate's consumer line enumerates prune without freeze; in-session authoring leaves its entry unfrozen mid-run; "live claim" is undefined in the freeze rule; no pin or test protects the rule text.
- Expected: the consumer line names freeze; the in-session authoring writes the Frozen mark as its first log write (witness: its own claim file); the freeze rule carries the one-cadence-period freshness bound with stale claims routed to the existing takeover rule; a pin or self-test arm fails when the freeze clause disappears from duty (b) or the log's standing rules.

## Suggested fix

One small plan (authoring only): (1) reword the investigate Integration Points consumer line to "read, prune, freeze, and dispatch duties"; (2) extend duty (c)/(d) so in-session log-entry authoring writes the entry's `Frozen:` line before plan work, naming its own claim file as the witness, mirroring the claim duty's refresh discipline; (3) add the freshness sentence to the freeze rule (both the log's standing rule and duty (b)): live means the claim's `updated:` fresher than one cadence period per the `G1a` discovery arm, a stale claim taking the takeover path instead of freezing; (4) add the regression witness (a pins-suite presence pin on the duty (b) freeze clause, re-keyed per the freeze-literal convention, or a self-test arm); (5) validate per the testing guidelines: exercise the rule against a simulated fresh claim (entry freezes, never dispatches, unfreezes on abort) and a landed plan (prune still fires), including the p89 live case as the witnessed instance.

## Source reference

Witnessed 2026-09-29 during the interactive grouping pass that landed the rule: the corpus sweep (`grep -rln "PLAN-PROMPTS" agents/skills/ scripts/`) shows exactly two consumer files (investigate, maintenance); the maintenance side was amended in the landing commits, the investigate side was not. Pins suite `bash scripts/check_maintenance_pins.sh` exit 0 after the landing; `doc_registry_validator.py validate` exit 0 with 0 hard findings (neither edited document is registry-rowed, so no audit notes were owed).

## Dedup probe

Search of the open backlog corpus (2026-09-29) for "freeze", "Frozen", "frozen entry": zero open items own the freeze-rule follow-through; the p92-p97 entries grouped the same day own unrelated surfaces. The rule's own landing is recorded in the log's standing rules and the maintenance skill, not in any backlog item, so this file is the first and only home for the residue.

## Origin class

Origin class: self-serving
