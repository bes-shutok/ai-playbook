# Plan: review-staging series-wide lint sweep at non-certification round closes

Authoring claim: docs/tmp/authoring-claims/review-staging-series-wide-round-close-scope.md (session zcode-auth-automation-fd67f4d3-2314)

Backlog origins (scope of record):
- docs/history/backlog/2026-10-09-review-staging-series-wide-round-close-gate.md

Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/*-plan-review-review-staging-series-wide-round-close-scope-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 1h total, largest task 0.5h

## Terms

- Series sweep: the round-close duty added by this plan: after a non-certification plan-review round's own validation pass, loop the existing validator `--preflight` over every earlier member of the plan-review series and read the results as warnings. No new validator mode, flag, or code path is added.
- Series member: one `*-plan-review-<artifact-slug>-r<N>.md` record plus its `.stats.json` sidecar under the reviews home; the round being closed is its own exception anchor.
- Lint level: the `--preflight` report-only check class per review-staging's Record validation levels subsection; the sweep runs exactly this class by construction, because it IS `--preflight`.
- Warning posture: the sweep never blocks a round close; any member outcome that is not a clean preflight (findings, indeterminate, unreadable) becomes one report-only warning line naming the member and the leg, and the close proceeds.
- Certification close: the round close that records the certifying verdict; per the Record validation levels partition it keeps the existing full `--hard` series validation at the seal and runs no sweep.
- Sidecar: the `.stats.json` file paired with a staging record, carrying the machine-checked schema the validator reads.
- Pattern owner: the declared worker-plus-lens a staged finding's pattern ID belongs to, per the review panel's tiered ownership table.
- Guard liveness ledger: scripts/gate_liveness_ledger.json, the catch-to-incident record that prices machinery and owns the promotion path.
- Renormalization: the witnessed post-hoc repair across already-closed rounds' sidecars and records (the origin row's incident shape).
- Counts-parity check: the interim counts-parity reconciliation rule; named here only because this plan's exclusions cite its row.
- Removals row: the pre-registered scripts/machinery_registry.json row naming the sweep's sunset and promotion criteria.
- Fail-open: a sweep iteration that cannot produce a clean preflight emits its warning and continues; nothing in the sweep can block or fail a round close.

## Why

Cross-round staging-record defects (a pattern owner outside the declared lens set, a worker over the non-blocking Low budget, a stale digest) surface today only at certification or by the next panel, and the observed repair is a post-hoc renormalization across already-closed rounds. This plan adds a lint-level, warning-posture series sweep at non-certification plan-review round closes so the introducing round hears about the defect while its round is still open.

## Gist & Examples

TLDR: adds a fail-open lint-level sweep of the plan-review series' earlier records to every non-certification plan-review round close, so cross-round record defects surface at the introducing close instead of at certification; declared force code-quality, motivated by reliability (the witnessed renormalization across closed rounds is the cost this removes).

Before: the round-close gate validates only the current round's staging path; the 2026-10-08 memory-index-consolidation certification flagged pattern-owner and Low-budget defects living in earlier rounds, and the repair touched the r2 and r3 sidecars post-close.
After: each non-certification plan-review close runs one per-member loop of the existing `--preflight` over the earlier members, echoing each member and converting any non-clean outcome into a warning naming that member and the finding(s); certification keeps its existing hard series validation unchanged, and the swept-member count is always reported so a zero-member sweep is a named line, never a bare pass.
Edge cases: a series of one round sweeps nothing and reports zero earlier members; an unreadable or indeterminate earlier member emits its warning and the close proceeds (fail-open); the sweep is advisory and never changes an exit code or a verdict.

## Outcome

One report-only duty that moves cross-round discovery earlier.
- Every non-certification plan-review round close runs the series sweep and reads its warnings before the round is reported complete.
- A defect in an earlier round's record or sidecar is named at the introducing close, with the member file and the finding leg, while repair is still round-local.
- Certification's hard series validation, the round-close full-gate precondition, and the execution and finalization gates are unchanged.
- The duty carries its machinery admission record and a pre-registered removals row in the same change, and the origin row's disposition rides the landing with its completion deleting the row per the commit guideline.

Gate delta: adds one report-only duty (the series sweep) priced by the machinery admission record with its pre-registered removals row (warning-only at landing; promotion to blocking only after a first true catch per the admission protocol); the guard liveness ledger's review-staging-validator row reads catches=3 incidents=1 at authoring time; no refusal, hard gate, fence, protocol layer, schema field, or validator code path is added or removed.

## Assumptions

- assume lint level means the `--preflight` check class, applied to prior rounds' records and sidecars; basis: review-staging's Record validation levels subsection defines lint level as the `--preflight` pass, so the loop form is the lint class by construction.
- assume the sweep covers every series member except the round being closed, whose own staging path is the exception anchor the closer already holds; basis: the origin row's "every ... in the series for the artifact slug, not only the current round" and the round-close context.
- assume warning posture with a fail-open per-member interception: any non-clean member outcome becomes a warning and the close proceeds; basis: the repository Machinery admission protocol's warning-only landing mandate and the origin row's own Severity line ("the cost is a post-hoc renormalization pass across closed records, never a wrong verdict").
- assume repair routing for a swept finding is the existing record-side repair class (a sanctioned post-round record edit beside corrections rows and triage marks), never a re-round; basis: the plans skill's staging-pair duty clause this plan extends.
- assume promotion of the sweep to blocking runs only through the guard liveness ledger's first-true-catch path with the removals row's criteria; basis: the repository Machinery admission protocol.
- assume the counts-parity check, the other cheap targeted checks, and the stale-latest-record recovery route stay out of scope; basis: those checks' own separate backlog rows (docs/history/backlog/2026-10-09-review-staging-counts-parity-validation.md and the stale-latest row), not the scope-of-record row.
- assume the origin row's acceptance sentence ("a sidecar defect in any earlier round fails the current round's close naming that round's file and finding; a clean series passes with one invocation") is superseded in both clauses by the warning posture and the per-member loop; the row flips covered at this plan's landing and is deleted at execution completion in the same change per the commit guideline, so the fail-closed text cannot invite a blocking implementation, and Task 2's admission note carries the re-point duty naming the completed plan twin as the witness ref (the registry's claim-fence precedent); basis: the plans skill's origin-acceptance-rewrite rule and the Machinery admission protocol.
- assume the pins suite's currently failing set (the 21 documented baseline failures) is unchanged by this plan; basis: the failing rows live in the dispatch/resume pin region, not the sentences this plan touches; each touched task verifies the failing set is byte-identical before and after.

Decision points requiring a grill: sweep posture read as warning-only fail-open rather than the row's fail-closed acceptance: resolved by the Machinery admission protocol's warning-only mandate and the row's own Severity line, 2026-10-14, affected sections: Terms, Task 1, Task 2, Gate delta; sweep mechanism read as the per-member loop over the existing `--preflight` (the origin row's cheapest form) rather than a new validator mode: resolved by the Machinery admission protocol's fewer-blockers default plus r1 review findings F1/F5/F6, 2026-10-14, affected sections: Terms, Task 1, Gate delta.

## Standing constraints

- Advisory only: the sweep never blocks, never changes an exit code or verdict, and never gates a lane; its only output is warning lines and the swept-member count.
- Certification strength unchanged: the certification close's full `--hard` series validation, the round-close full-gate precondition, and the execution and finalization gates keep their existing strength byte-for-byte, per the Record validation levels partition this plan extends rather than restates.
- Growth priced: the duty bullet links the certification carve-out to the existing partition sentence instead of restating it, and the change lands the admission record and removals row in the same change as the duty.
- Pins failing-set invariance: each task that touches pinned text verifies the pins suite's failing set is byte-identical before and after the change (the 21 documented baseline failures are pre-existing and out of scope).

## Evaluation Criteria

**Quality dimensions:**
- correctness: the validator's full `--selftest` passes unchanged (no code path is touched), and the pins suite's failing set is byte-identical before and after each task.
- behavior preservation: certification closes, the seal's series validation, and every existing validator mode behave identically.
- admission integrity: the machinery registry carries the duty's admission record and removals row in the same change as the duty.
- measurability: every sweep warning names the member file and the leg, and the swept-member count is always reported.

**Done when:**
- The Record validation levels subsection carries the plan-review-scoped sweep duty, with all three consumer sentences naming it by reference.
- scripts/machinery_registry.json carries the admission record and the pre-registered removals row.
- The origin row's disposition is carried: the covered flip at landing and the deletion at execution completion, with the re-point duty in the admission note.
- The pins suite's failing set is byte-identical to the base state's.

**Ship when:**
- none; this plan is repository-internal with no external release surface.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/machinery_registry.json`
- `scripts/check_maintenance_pins.sh` (pins re-aims only)

**Documentation:**
- `agents/skills/review-staging/SKILL.md` (Record validation levels subsection)
- `agents/skills/review-plan/SKILL.md` (the Step 4 subordination sentence)
- `agents/skills/plans/SKILL.md` (the staging-pair duty's subordination sentence)
- `agents/skills/review-loop/SKILL.md` (the mechanical-gate sentence naming the same subsection)

**Backlog rows (disposition):**
- `docs/history/backlog/2026-10-09-review-staging-series-wide-round-close-gate.md` *(deleted at execution completion; covered flip at landing)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, or reconciles a pins row the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the counts-parity check and the other cheap targeted checks; reason: their own separate backlog rows own them.
- the stale-latest-record recovery route; reason: it repairs a different defect at a different surface and is routed as its own entry.
- promoting the sweep to blocking; reason: admission protocol requires a first true catch on the ledger first.
- any validator code change; reason: the sweep is the per-member loop over the existing `--preflight`, and a new mode is this plan's recorded rejected alternative.

## Validation Commands

```bash
( cd "$(git rev-parse --show-toplevel)" && python3 scripts/validate_review_staging.py --selftest )
( cd "$(git rev-parse --show-toplevel)" && bash scripts/check_maintenance_pins.sh )
( cd "$(git rev-parse --show-toplevel)" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh )
```

Validation preamble (rule 29 record): the pre-round structural gate ran OUTCOME: pass before round 1 on 2026-10-14; the authoring-time em-dash fixer pass and the public-hygiene scan (exit 0) are recorded at authoring; this plan pins no literal spans or counts, so no rule-22 audit set applies; rule 19 RED-today record: the pins suite is the first actually-failing validation gate at authoring (exit 1, the 21 documented baseline failures, unchanged by this plan's scope and pinned invariant by the Standing constraints), the machinery inventory check is likewise red at authoring (exit 1, 20 documented baseline failures, held to the same invariance in Task 2), the hygiene scan passes, and there are no vacuous passes.

The validator selftest is the unchanged-behavior witness (no validator code path is touched) and the pins failing-set invariance is a per-task gate.

### Task 1: the sweep duty in the Record validation levels subsection

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-loop/SKILL.md`
- `scripts/check_maintenance_pins.sh` (pins re-aims only)

- [x] The Record validation levels subsection gains one duty bullet scoped to plan-review series closes: at every non-certification plan-review round close, after the round's own validation pass (lint or full), loop the existing validator `--preflight --source-plan <the plan under review>` over every earlier member of the plan-review series, the round being closed being the exception anchor [class: IMPLEMENTATION_REQUIRED]
- [x] The same plan anchors every member's digest check per the origin row's digest-check sentence, so a stale earlier sidecar digest surfaces as a report-only preflight finding [class: IMPLEMENTATION_REQUIRED]
- [x] The duty bullet's interception rule: each member path is echoed, any non-clean member outcome (findings, indeterminate, unreadable) becomes one warning naming the member and the finding(s), echoing the member's preflight report, and the swept-member count is always reported, the invocation resolves the validator repo-local first, and swept findings route through the existing record-side repair class [class: IMPLEMENTATION_REQUIRED]
- [x] The duty bullet's scoping rule: certification closes run no sweep per the partition above, which the bullet links to rather than restates [class: IMPLEMENTATION_REQUIRED]
- [x] The three consumer sentences (review-plan Step 4's, the plans staging-pair duty's, and review-loop's mechanical-gate sentence) each gain one clause naming the sweep by reference to the subsection, scoped to plan-review series for review-plan and plans and recording that code-family rounds carry no sweep for review-loop, adding no second copy of the duty [class: IMPLEMENTATION_REQUIRED]
- [x] Each skill file in this task's Files list carries the same change to its vendored twin in the same run, or the change leaves the tracked vendored-sync landing path naming the changed files [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect one grep hit per deliverable: the duty bullet and its interception rule in agents/skills/review-staging/SKILL.md and each consumer clause in its own file, at the spans this task prescribes [class: REPOSITORY_TEST]
- [x] Run → expect the validator selftest green unchanged and the pins suite's failing set byte-identical to the base state's, re-aiming any row whose matched literal moved beside its provenance in the same change [class: REPOSITORY_TEST]
- [x] Commit: `docs: series lint sweep duty at non-certification plan-review round closes` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the machinery admission record and removals row

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/machinery_registry.json`

- [x] The registry carries the duty's admission record: incident with link docs/history/backlog/2026-10-09-review-staging-series-wide-round-close-gate.md (the 2026-10-08 memory-index-consolidation post-close renormalization across the r2 and r3 sidecars); expected catch frequency: every multi-round plan-review series at each non-certification close, surfacing cross-round lint-detectable record or sidecar defects at the introducing close rather than at certification [class: IMPLEMENTATION_REQUIRED]
- [x] The admission record carries the false-positive cost (one report-only warning line per non-clean member), the execution cost shape (per-close passes equal the earlier-member count; the series total is quadratic in rounds, bounded by the round cap; accepted because the duty replaces certification-time renormalization passes), and the landing posture (warning-only) [class: IMPLEMENTATION_REQUIRED]
- [x] The admission note carries the origin row's disposition per this plan's assumptions: covered at landing, deleted at execution completion in the same change, re-point duty naming the completed plan twin as the witness ref [class: IMPLEMENTATION_REQUIRED]
- [x] The registry carries the pre-registered removals row with empty paths per the live-surface precedent, naming the co-removal set (the subsection duty bullet, the three consumer clauses, the pins re-aims, and the registry rows themselves, removed together in one reviewed change), the sunset (review at 90 days or the first promotion decision, whichever first), and the promotion criteria (a first true catch recorded on the guard liveness ledger) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect the machinery inventory check's failing set byte-identical to the base state's (20 documented baseline failures at authoring), with no new failure naming the rows this task adds, and the pins suite's failing set byte-identical to the base state's [class: REPOSITORY_TEST]
- [x] Commit: `chore: admit review staging series lint sweep duty warning-only with removals row` [class: IMPLEMENTATION_REQUIRED]
