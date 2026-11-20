# Backlog: the known-red baseline stales within hours under landing traffic and its consumption is unverifiable at the reporting boundary

- **Filed:** 2026-11-20, 24h session-pattern harvest learn run (learn Step 1.8; known-red baseline family)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Class:** fix-class
- **Origin class:** witnessed defect (baseline file digests re-derived from disk against the evening's landing sequence; post-landing transcripts scanned for consumption evidence)
- **Skill/step:** `scripts/machinery_inventory.py` (`--render-baseline` producer and the controlling-input digest staleness rule); `agents/skills/plans/plan-quality-gate.md` (known-red baseline classification clause); `agents/skills/execute-plan/implementation-loop.md` (Step 1.4 and Phase 2 pointers)
- **Cluster:** docs/history/backlog/2026-11-10-known-red-gates-retriage-tax.md (covered: that row owns the pre-baseline re-triage tax this mechanism was built to end; this row owns the post-landing effectiveness gap); docs/history/backlog/2026-11-19-known-red-baseline-phase3-r1-residuals.md (same mechanism, code-level residuals); docs/history/backlog/2026-11-19-survey-arms-byte-cap-overage-payment.md (the budget-advisory red the stale section failed to pre-classify)

## Observed versus expected

Observed: the baseline rendered 2026-11-19 16:32Z. Within six hours two of its three producer sections were stale by the mechanism's own rule: the machinery_inventory section's 3 of 3 controlling inputs changed (the landing of the known-red-gates plan itself, hours after the render), and the skill_text_budget section's controlling-input set spans the whole skill corpus, so 17 of 138 inputs changed by the evening's landings (the twin-slot landing alone touched four). Only the maintenance_pins section stayed fresh, and it lists the exact persistent red (`PIN FAIL: FINAL STEP prefix count`). The fail-open arm then legally demotes every stale section to hand classification, and the fresh pins section was not consulted either: four post-landing runs (22:28, 22:53, 23:10, 00:16) hand-verified the same pin failure against main with zero references to the baseline file across their transcripts (probe: no occurrence of the baseline filename or the render flag in any of the four sessions), each re-deriving the pre-existing classification the clause prescribes deriving from the baseline pointer. A fifth run (00:43) engaged the mechanism but its landing pushed survey-arms further past its cap, re-opening the budget red the stale section could not pre-classify.

Expected: under the loop's own landing traffic the baseline sections stay fresh enough to classify at consumption time, and when a run classifies a baseline-listed red the classification cites the baseline section, so non-consumption is visible at review instead of indistinguishable from a hand re-derivation.

## Suggested direction

Two independent arms, priced separately. (1) Freshness: attach a section re-render to the boundary that staled the section, the landing pass that touches one of a producer's controlling inputs re-renders that producer's section as a landing rider (warning-only, fail-open unchanged), or narrow per-line controlling inputs so a whole section does not stale on an unrelated skill edit; the either/or is the design input. (2) Consumption evidence: the Phase 2 classification clause's deferral phrasing gains an evidence-form requirement, a baseline-listed classification names the baseline section (generated_at or section digest) the way other receipts name their digests, making the fresh-section non-consumption witnessed above a review-visible miss.

## Machinery admission

No new gate proposed: arm (1) is a rider on the existing landing pass or a producer-shape change, arm (2) is an evidence-form duty on existing report lines. The witnessed cost is five hand re-triage passes in one evening on one pin line, zero catches attributable to any of them; a rider re-render carries a false-positive cost of one extra render per touching landing, sunset/review 2027-02-20.

## Rejected alternatives

- Repair the persistent reds so no baseline is needed: already priced by the covered retriage-tax row's sibling repair entry and still open for the pins line; independent of this row, which prices the mechanism's effectiveness whatever the red set.
- Drop the staleness rule so stale sections keep classifying: rejected; stale lines mask repaired reds and re-list repaired ones, the rule protects the baseline's truthfulness (the classification clause's own rationale).
- Gate every validation battery on a fresh render (render-or-refuse): rejected; a required render per run reintroduces the per-run cost the baseline exists to remove, and the fail-open arm already bounds the blast radius of staleness.

## Evidence

- Baseline file at `.ai-playbook/maintenance/baseline-known-red-gates.json`: generated_at 2026-11-19T16:32:45Z; pins section captured with the `PIN FAIL: FINAL STEP prefix count` line; digest re-derivation 2026-11-20 ~02:15 shows machinery_inventory 3/3 inputs changed, skill_text_budget 17/138 changed, maintenance_pins 0/2 changed.
- Post-landing transcripts (sessions running 22:28 to 00:16): zero occurrences of the baseline filename or the render flag; closing reports hand-classify the pin failure as pre-existing on main with wording like "needs an owner".
- The 00:43 run's residual row `2026-11-19-survey-arms-byte-cap-overage-payment.md`: the budget red reopened past the cap by a post-render landing.

## Acceptance

- After a landing that touches a producer's controlling input, the section is re-rendered (or its controlling inputs are narrowed so it is not), and a validation-battery classification of a baseline-listed red cites the baseline section in the deferral line; both suites stay green.

## Dedup probe

Searched open backlog rows for baseline staleness, controlling-input freshness, render rider, and consumption-evidence phrasing: the phase3-residuals row owns code-level findings (placement semantics, digest recipe citation, render path safety), none owns the traffic-pattern staleness or the report-side evidence form; the covered retriage-tax row ends at delivering the rendered baseline.
