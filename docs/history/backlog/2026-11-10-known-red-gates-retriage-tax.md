# Backlog: panels re-triage known-red baseline gates every round; a consumed baseline would end the tax

- **Filed:** 2026-11-10, learn Step 1.9 capture from the 24h session-pattern harvest (playbook repo)
- **Status:** covered (docs/history/plans/2026-11-13-known-red-gates-consumed-baseline.md)
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** session-witnessed flow gap (review-panel startup versus baseline-red machinery)
- **Class:** fix-class
- **Skill/step:** `agents/skills/review-agents/` (worker prompt and pins surfaces) + `scripts/skill_text_budget.py` advisory output + the pins-suite staleness pin
- **Cluster:** docs/history/backlog/2026-11-10-byte-budget-advisory-lens-divergence.md (same advisory-signal surface); the machinery-inventory-baseline-red-repair EXEC-PROMPTS-PRUNE receipt (covered 2026-11-16; the baseline-red defect class this row consumes from the inventory side)
- **Source reference:** 2026-11-09/10 window: the prompt-log staleness PIN FAIL was classified pre-existing by hand in five worker instances across three sessions (memory-index-retirement-pass authoring x2, the 23:00 exec carrier, the test-policy-scope exec run x2), zero catches; `check_maintenance_pins.sh` red on the main baseline was classified through a 7-probe manual pass in the published-stack-review-coverage-gap authoring session; skill-text-budget BREACH lines were re-read by two exec sessions
- **Why not fixed now:** harvest-only session
- **Dedup probe:** the machinery-inventory-baseline-red-repair EXEC entry (landed 2026-11-16; its prune receipt owns the record) delivered the baseline-red repair arm (the check now exits 0); this row owns the consumer side (panels re-classifying per round while the reds persist); no merge
- **Cluster:** docs/history/backlog/2026-11-19-rolling-log-prune-receipt-accumulation.md (the size cause behind the oversize advisory this row's sessions re-triage)

## Problem

Guards that are red at baseline (the staleness pin, advisory budget breaches) are surfaced to every review worker and exec preflight as if actionable. Each panel re-derives the same not-pre-existing classification by hand: five worker instances in the window, zero catches attributable to the re-triage, while genuinely new reds receive the same attention weight.

## Expected

The known-red set the machinery inventory already records is consumed at worker startup: a rendered known-red marker (a file or lens-preamble line naming each baseline-red guard) lets a panel treat exactly those as pre-existing and everything else as actionable. The marker regenerates from the inventory rather than being maintained by hand.

## Suggested fix

Extend the machinery inventory's record into a machine-readable baseline file consumed by review worker prompts and exec preflights. Admission fields ride the emitted entry: incident (the five re-triage instances above), catch frequency (every multi-worker round while the pins stay red), false-positive cost (a stale baseline masks new reds if the underlying repair lands without regenerating), review date (2026-12-10). The removal-shaped alternative (repairing the two baseline reds so no baseline file is needed) is priced in the existing repair entry.
Recurrence: 2026-11-18 six-plus window sessions re-triaged the same pre-existing reds before proceeding: the pins stale-entry FAIL re-verified against an untouched base in at least five sessions (one burned six calls, one had a pipe-masked exit code), the EXEC-PROMPTS oversize advisory re-triaged in two, the decisions.md budget advisory in one; witnesses in the 2026-11-19 harvest investigate entries (PLAN: stale-capture-record-commit-peer-clobber; PLAN: rolling-log-prune-receipt-accumulation)
