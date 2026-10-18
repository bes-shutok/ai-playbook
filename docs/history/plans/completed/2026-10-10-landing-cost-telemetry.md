# Plan: Per-landing cost telemetry (machinery audit Part 4 item 8)

Backlog origin: docs/history/backlog/2026-10-10-landing-cost-telemetry.md (the PLAN-PROMPTS entry `landing-cost-telemetry` carries the operator "next" walk; the audit's Part 4 item 8, with item 7 as the replacement target)
Driving force: automation
Design input: docs/maintenance/machinery-blocker-audit-2026-10-09.md (Part 4 item 8 and item 7; the Limits section's incident-derived-bias admission); the landed telemetry doctrine (the context-telemetry machinery's never-blocking posture, the Phase 4 archive ordering, the absence-record pattern)
Plan review record: the staging series docs/history/reviews/2026-10-10-plan-review-landing-cost-telemetry-r*.md (created by this plan's review loop, r1 onward; the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 1.5h total, largest task 0.75h
Authoring claim: docs/tmp/authoring-claims/2026-10-10-landing-cost-telemetry.md (session sess_5c51c846-299a-4dfe-a00c-4238d7883663)

## Terms

- The landing-cost record: one newline-delimited JSON line `{plan_slug, landing_commit, wall_hours, review_rounds, gate_refusals, operator_interventions, tokens_est, recorded_at}` appended to `docs/history/metrics/landing-costs.jsonl` by the done skill's closeout, every field nullable, an absent record carried as a named absence reason instead (the telemetry-absence pattern's own shape), add-only.
- Never-blocking doctrine: telemetry is analysis data, never correctness evidence - a missing, failed, or incomplete record never refuses or delays any closeout step; a failed append is reported and the closeout continues.
- Mining replacement: the friction-audit registry task and the weekly measurement rider gain the cost-question rule - per-landing ceremony cost questions answer from the JSONL (a local read), and their store-mining passes stay scoped to their non-cost sources (the watermarks, the token-budget accounting, and every non-cost source byte-untouched). The audit's item-7 replacement intent lands as this scoped rule: the wholesale mining-sub-agent replacement the audit names is realized as the JSONL becoming the answering surface for the cost class it can serve.
- The monthly machinery review: the audit's delete-bottom-quartile-by-catch-count review (Part 4 item 8's own wording), whose contract of record this plan re-homes from the audit prose to the JSONL as its measured input, enforcing Task 1's sunset.
- The admission fields: concrete incident (the audit's incident-derived bias per its Limits section, linked, plus the 700k-950k-token mining runs of Part 4 item 7), expected catch frequency (one append per landing, read monthly), false-positive cost (zero blocking - fail-open, never gates), sunset (three consecutive monthly reviews with no machinery removal or demotion decision citing the JSONL remove the writer duty), and the pre-registered machinery-registry removals row.

## Why

The audit's ratings are incident-derived and skewed - its Limits section says so itself - and the repo cannot measure what a landing costs. The context-telemetry machinery records context-size checkpoints only, and the freshest witness is an absence record (the docs-branch run of 2026-10-09 created no context-telemetry.log across all its run artifacts). The only cost source today is the friction-audit mining run, priced at 700k-950k tokens each and named for replacement. One closeout-native append per landing gives every future machinery removal decision its measured basis at zero marginal ceremony: the append rides the closeout the landing already runs, and the consumers that currently mine read the line instead.

## Gist & Examples

TLDR: each done closeout appends one JSON line of landing cost facts (nullable, fail-open, absent-reason-carrying); the friction-audit and weekly rider answer per-landing ceremony cost questions from that line with their store-mining passes scoped to non-cost sources; the monthly machinery review deletes bottom-quartile machinery by catch count from the JSONL's evidence, and the writer duty removes itself after three such reviews pass without citing it.

Before: a cost question costs a 700k-950k-token mining run (or goes unanswered); the audit's own success measure ("per-landing telemetry present for every new landing") is unevaluable; machinery removal decisions rest on incident-derived ratings the audit itself disclaims.

After: the same question reads one local JSONL line; every landing carries exactly one record or a named absence reason; the monthly review's delete-bottom-quartile contract has its measured input; zero closeout refusals are ever caused by telemetry.

Edge cases: a closeout that cannot write the file (read-only checkout, missing directory) reports and continues, writing nothing; a landing with no plan (a rider commit, a registry edit) records `plan_slug: null` with the absence reason in a `note` field, or no line at all when the run recorded no landing - the never-blocking doctrine outranks completeness; the JSONL lives under the gitignored metrics home the Phase 4 archive already preserves on the docs branch, so the main-branch corpus never grows and no hygiene or pins surface changes.

## Outcome

Every new landing carries exactly one landing-cost record or a named absence reason, with zero closeout refusals caused by telemetry; the friction-audit and weekly rider answer per-landing ceremony cost questions from the JSONL with their store-mining passes scoped to non-cost sources; the monthly machinery review reads the JSONL as its measured input; the writer duty carries its admission fields, its sunset, and a pre-registered removals row.

Gate delta: one closeout receipt bullet in the done skill (an append the closeout already runs), two registry-task bodies gain the cost-question rule (the JSONL answers the per-landing ceremony cost class; the mining passes stay scoped to non-cost sources), one audit-doc contract sentence gains its measured input, one machinery-registry registration with its removals row; no new script, no new gate, no refusal added or removed, no schema state field; the JSONL is analysis data under the gitignored metrics home (docs-branch preserved), so the main corpus, the pins suite, and the hygiene scan are untouched by the record itself.

## Assumptions

- The append rides the done skill's closeout as skill text (the recipe in the closeout's receipt section), not a new script: one append is a shell one-liner over fields the run already knows, a helper would be machinery without a catch, and the admission protocol prices machinery by incident. Basis: the origin row's "the done skill's closeout appends", the minimal-arm wording, and the admission test's own zero-blocking posture.
- The JSONL sits under `docs/history/metrics/` (the metrics_dir home the Phase 4 archive resolves and preserves on the docs branch), which is gitignored on main: the record is docs-branch-preserved analysis data, the main-branch corpus does not grow, and the existing archive ordering carries it without new wiring. Basis: the metrics home's landed preservation doctrine and the origin row's rejected alternative naming the docs-branch preservation.
- The monthly machinery review's contract of record is the audit prose (Part 4 item 8's review-monthly wording) operating through the friction-audit registry task's machinery-mining duties: Task 3 re-homes the input sentence in the audit doc beside the item it interprets, and Task 2's task-body edits are where the review's cost questions actually get answered, so no new recurring task is created. If execution finds the review contract carried elsewhere (a registry task body naming the bottom-quartile review), that body is the edit surface instead, recorded in the session log. Basis: the audit doc's item 8 wording, the friction-audit task's mining duties, and the rejected alternative forbidding a second home.
- `tokens_est` is best-effort and nullable: the closeout records the session's own context accounting when it has one and null when it does not, and no consumer treats a null as an absence of cost - the record's purpose is trend evidence, not billing. Basis: the origin row's every-field-nullable shape.
- The friction-audit and weekly-rider edits stop only COST mining dispatches: the store-mining watermarks, the token-budget accounting, and every non-cost source those tasks read stay byte-untouched, because the audit priced only the cost-mining runs for replacement. Basis: the origin row's Task 2 wording.
- Residual accepted: a landing executed outside a done closeout (a direct rider commit on another lane's landing) produces no record; the JSONL measures done-closeout landings, which is where the ceremony cost lives, and the monthly review reads what exists. Basis: the writer duty's own closeout placement.

Decision points requiring a grill: none remain (the operator's "next" walk pre-authorized the entry; the entry fixes the record shape, the consumers, the review contract, the admission fields, and the rejected alternatives including the second-home and post-hoc-derivation shapes).

## Standing constraints

- Telemetry never blocks: no closeout step, gate, or landing may refuse or stall on a missing, failed, or incomplete record; the append is fail-open with a reported-and-continued failure.
- The context-telemetry doctrine's landed spans are pinned: this plan extends beside them and re-aims pins only if its wording moves them, never by rewriting pinned spans.
- Deploy truth: the skill and task-body edits reach their runtime homes at this plan's merge-locked landing (the landing is the deploy) (the symlinked skills registry and the task bodies the recurring turns read resolve the primary checkout).
- The full battery stays green at every task landing: the pins suite, the parallel-work regressions suite, the authoring-plans liveness test, the em-dash scan over touched paths, and the public hygiene scan; a red suite at a task boundary stops for reconciliation, never a weakened check.
- No machine-specific absolute paths in any edited file; nothing is pushed to origin; execution runs on a branch kept rebased onto current main at each fold with the plan's task-start currency check and the stop-and-report arm.
- Rollback arm: revert the offending task's commit (the JSONL is add-only data and survives; the skill bullet, the task-body edits, and the registry row revert cleanly); the registry removals row reverts with the registration.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the record shape matches the origin row's eight fields exactly; the consumers read the JSONL for cost questions and nothing else changes in their sources; the admission fields in the skill text and the registry row agree.
- regression safety: the pins suite green (the done skill's pinned spans untouched or re-aimed beside their provenance); both registry-task suites of duties that must stay (watermarks, budgets) byte-unchanged; the battery green at every landing.
- scope discipline: the changes touch only the done skill, the two registry-task bodies, the audit doc's item-8 sentence, the machinery registry, and the JSONL itself; no new script, no new gate, no schema change.

**Done when:**
- Every span check in `## Validation Commands` holds on the executed tree.
- The battery is green.

**Ship when:**
- The next done closeout appends its record (or its named absence reason) with zero telemetry-caused refusals, the next friction-audit run answers its cost questions from the JSONL, and the monthly review names the JSONL as its input; they follow from the executed tree.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/done/SKILL.md` (the landing-cost record bullet: the append recipe, the nullable fields, the absence reasons, the fail-open posture, the admission fields)
- `docs/maintenance/recurring-tasks/friction-audit.md` (the cost-mining replacement: cost questions read the JSONL)
- `docs/maintenance/recurring-tasks/weekly-measurement-rider.md` (the same cost-question replacement)

**Docs:**
- `docs/maintenance/machinery-blocker-audit-2026-10-09.md` (Task 3: the item-8 review contract gains the JSONL as its input and the sunset enforcement)
- `scripts/machinery_registry.json` (the writer-duty registration with its admission fields and the pre-registered removals row)

**Tests:**
- `scripts/check_maintenance_pins.sh` (only if a pinned span moves; extend beside, re-aim beside provenance)

**Read-only (referenced, never edited):**
- `docs/history/metrics/landing-costs.jsonl` (the record's home; gitignored, docs-branch preserved)
- `docs/history/metrics/2026-10-09-docs-branch-scope-and-tmp-retention.log` (the absence-record witness)
- `docs/history/backlog/2026-10-10-landing-cost-telemetry.md` (the origin row; flipped covered by the landing rider)
- `docs/history/backlog/2026-10-10-machinery-admission-protocol.md` (the sibling cluster row; this telemetry is its measured evidence base)

**Receipts:**
- Origin row: docs/history/backlog/2026-10-10-landing-cost-telemetry.md (Status: open; the landing rider flips it covered naming this plan)
- Prompt entry: docs/history/backlog/PLAN-PROMPTS.md `## landing-cost-telemetry` (frozen under docs/tmp/authoring-claims/2026-10-10-landing-cost-telemetry.md; pruned by the landing rider with the prune receipt)

## Validation Commands

**Production:**
```bash
grep -c "landing-costs.jsonl" agents/skills/done/SKILL.md   # expect >=1 (the writer duty)
grep -cE "never[- ]blocking" agents/skills/done/SKILL.md   # expect >=1 (the doctrine sentence near the append)
grep -cF "landing-costs.jsonl" scripts/check_maintenance_pins.sh   # expect >=1 (the never-blocking pin)
grep -c "landing-costs.jsonl" docs/maintenance/recurring-tasks/friction-audit.md   # expect >=1
grep -c "landing-costs.jsonl" docs/maintenance/recurring-tasks/weekly-measurement-rider.md   # expect >=1
grep -c "landing-costs" docs/maintenance/machinery-blocker-audit-2026-10-09.md   # expect >=1 (the item-8 input)
python3 -c "import json; d=json.load(open('scripts/machinery_registry.json')); assert any('landing-cost' in json.dumps(r) and r.get('disposition')=='delete' for r in d['removals'])"   # the registration AND its own removals row (row-specific: the generic delete-disposition check passes on pre-existing rows)
```

**Tests:**
```bash
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )   # exit 0
python3 scripts/test_plan_review_boundary_examples.py   # exit 0
python3 scripts/test_authoring_plans_liveness.py   # exit 0
bash scripts/check-no-em-dash.sh file agents/skills/done/SKILL.md docs/maintenance/recurring-tasks/friction-audit.md docs/maintenance/recurring-tasks/weekly-measurement-rider.md   # exit 0
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh   # exit 0 from the repo root
```

### Task 1: the landing-cost record (done-skill closeout bullet + registry registration)

Files:
- agents/skills/done/SKILL.md
- scripts/machinery_registry.json
- scripts/check_maintenance_pins.sh

- [x] Add the landing-cost record bullet to the done skill's Step 7 receipt bullets (the receipt section the closeout already runs): the append recipe (one newline-delimited JSON line with the eight fields to `docs/history/metrics/landing-costs.jsonl`, created add-only as a single-line `>>` write; readers skip blank or unparseable lines), every field nullable with the named absence-reason shape for landings without a plan, `wall_hours` sourced from the run's start marker to the closeout time (null when the run recorded no start), the never-blocking posture stated beside the recipe (a failed append is reported and the closeout continues; telemetry is analysis data, never correctness evidence), and the admission fields (concrete incident, expected catch frequency, false-positive cost, sunset: three consecutive monthly reviews with no removal or demotion decision citing the JSONL remove the writer duty). [class: IMPLEMENTATION_REQUIRED]
- [x] Register the writer duty in `scripts/machinery_registry.json` within the schema's fixed shape (the posture, the admission-field citation, and the sunset in the entry `note`; the removals row in the `removals` array with disposition `delete`; no invented fields); `python3 scripts/machinery_inventory.py --check` adds no new finding naming it. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the never-blocking pin to `scripts/check_maintenance_pins.sh` beside the done-skill pin block: the doctrine sentence (the never-blocking posture and the reported-and-continued failure) frozen verbatim in the done skill, so a future edit relocating the bullet into a required path or weakening the fail-open tail fails the suite; do not reproduce any phrase a count-gated pin already counts (the suite run below is the immediate check). [class: IMPLEMENTATION_REQUIRED]
- [x] Run the pins suite, the em-dash scan over the touched paths, and the hygiene scan green, and land this task as its own commit. [class: REPOSITORY_TEST]

### Task 2: the mining replacement (friction-audit + weekly rider read the JSONL)

Files:
- docs/maintenance/recurring-tasks/friction-audit.md
- docs/maintenance/recurring-tasks/weekly-measurement-rider.md

- [x] In the friction-audit task body, add the cost-question rule beside the existing run procedure: per-landing ceremony cost questions answer from `docs/history/metrics/landing-costs.jsonl` (a local read), and the store-wide mining passes stay scoped to their non-cost sources (the watermarks, the token-budget accounting, and every non-cost source byte-untouched); the same body gains the monthly machinery review's operative input sentence (the review reads the JSONL as its measured input and enforces the Task 1 sunset), which is the operative home a recurring turn actually loads. [class: IMPLEMENTATION_REQUIRED]
- [x] In the weekly measurement rider task body's Run procedure, add the same cost-question rule sentence (per-landing ceremony cost questions read the JSONL), keeping the rider's existing script passes byte-untouched. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the pins suite, the liveness test, and the hygiene scan green, and land this task as its own commit. [class: REPOSITORY_TEST]

### Task 3: the monthly review contract gains its measured input, and final verification

Files:
- docs/maintenance/machinery-blocker-audit-2026-10-09.md

- [x] Add the one-line provenance note beside the audit's item 8: the review's operative input home is the friction-audit task body (Task 2), which reads `docs/history/metrics/landing-costs.jsonl` and enforces the Task 1 sunset; the note never rewrites the item's historical text (the audit doc is a dated snapshot; the task body is what a recurring turn loads). [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full verification battery on the executed tree: the pins suite, the parallel-work regressions suite, the liveness test, the em-dash scan over all touched paths, and the hygiene scan; record each exit code in the session log and fix any red span before reporting the task done. [class: REPOSITORY_TEST]
