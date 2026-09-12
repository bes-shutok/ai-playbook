# Backlog: jvm review coverage r1 residuals

Status: open
Priority: high (revived 2026-09-12 per user decision: code quality added as the fourth driving principle (guidelines section 64) - review-coverage and validator-correctness value is no longer priced at zero)

Workflow: backlog
Source: docs/reviews/2026-09-10-2026-09-10-strengthen-jvm-review-coverage-code-review-r1.md (plan docs/plans/2026-09-10-strengthen-jvm-review-coverage.md, round 1)
Severity: Low (all items)
Class: deferred review findings

## Problem

Five valid Low findings from review round 1 were deferred rather than fixed
inline. Items 2 and 3 are ADR-0002 sibling-doc restatement class; items 1, 4,
and 5 sit on plan-prescribed verbatim text whose rewording is an authoring-level
decision.

1. `implementation#compat-witness-owner-drift`: the java-spring.md overlay
   ownership sentence routes "the compatibility witness to implementation",
   but rule #24's witness is by definition a required executable test, and the
   tiered ownership table in review-panel-selection.md routes missing-or-weak
   test findings to `testing`. A missing-witness finding therefore has two
   contradictory routing homes, risking wrong-owner discard or relabeling
   during dedup. Fix by narrowing the overlay sentence or adding an explicit
   witness row to the tiered table. Evidence: r1 finding F1.

2. `architecture#trigger-surface-list-duplication`: the same four-surface
   trigger list (shared helpers, flag wiring, timeout boundaries, living-doc
   claims) is restated at four wiring sites across three orchestrator files
   (doing-code-review Step 2.5, execute-plan Steps 3.1 and 3.4,
   review-panel-selection), plus the java-spring.md trigger section as a
   fifth restated site, with drifting phrasing, and the plan's validation
   probes ran once at execution rather
   than persisting as a repo script, so future surface renames can leave
   three of four sites stale with nothing to catch the drift. Remedies:
   name one file the surface-list owner and reference it from the other
   sites, or persist the probe set as a small check script. ADR-0002
   sibling-doc restatement class. Evidence: r1 finding F6.

3. `simplification#overlay-trigger-section-overlap`: the java-spring.md
   overlay names each new rule twice, once as a Review-wide bullet and again
   in the "Rollout, timeout, and shared-helper triggers (Spring)" section,
   whose only unique content is the Spring vocabulary; five of the ten new
   overlay lines are rule-number and surface pairings duplicated across the
   two blocks, so a future rule edit must touch both. Fix by folding each
   trigger line's Spring annotations into the matching Review-wide bullet or
   reducing the section to a one-line pointer. ADR-0002 sibling-doc
   restatement class. Evidence: r1 finding F7.

4. `simplification#rule-25-example-overbuilt`: the rule #25 worked example in
   java_guidelines.md spends most of its bulk on a backlog-ticket mock rather
   than the reconciliation check itself; sibling rule examples are leaner.
   Trim the example to the reconciliation evidence plus a one-line handoff
   pointer. Evidence: r1 finding F8 (overflow manifest).

5. `security#risk-floor-near-universal-trigger`: the review-panel-selection
   risk-signal floor now lists "shared conversion or persistence helpers
   reused across callers" and "feature-flag and configuration wiring that
   gates capability readiness" as always-on risk signals, so the floor fires
   on almost any non-trivial Java diff (shared converters and mappers are
   ubiquitous), eroding the focused-panel precedence the same file
   establishes. Fix by narrowing qualifiers, for example "reused across
   callers when the reuse changes or adds a caller". Evidence: r1 finding F11.

## Suggested fix

Schedule a follow-up authoring round for the strengthen-jvm-review-coverage
surfaces: resolve the witness ownership routing (item 1), pick one trigger-list
drift guard (item 2), de-duplicate the overlay trigger section (item 3), trim
the rule #25 example (item 4), and calibrate the risk-floor qualifiers (item
5). Each item is non-blocking; none changes landed behavior on its own.

6. `implementation#cross-skill-contract-drift`: the execute-plan Step 3.4
   item 6 Release-gate ledger field list (five required fields) does not
   enumerate the residual-rationale content that java_guidelines rules #23
   and #24 direct into the ledger ("accepted residual with its rationale",
   "residual runtime risk"), so a worker can produce a gate-complete ledger
   without that content. Source: code review r4 F1
   (docs/reviews/2026-09-10-2026-09-10-strengthen-jvm-review-coverage-code-review-r4.md).
   Remedies: add a rationale/residual-note field to the execute-plan item 6
   list, or name the backlog-item form as the canonical location in rules
   #23/#24 (they already accept "a backlog item with an owner" as an equally
   valid durable record, so the directive is satisfiable today). Deferred
   under the Hard Gate 23 stop rule at round 4: new-class finding, folding it
   would mutate a ledger contract owned by a prior plan and force a fifth
   round for an authoring-level decision.
