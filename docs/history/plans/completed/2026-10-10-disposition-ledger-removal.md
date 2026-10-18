# Plan: Remove the disposition-ledger workflow (machinery audit Part 4 item 7)

Backlog origin: docs/history/backlog/2026-10-10-disposition-ledger-removal.md (the PLAN-PROMPTS entry `disposition-ledger-removal` carries the operator "next" walk; the audit's Part 4 item 7, the one deletion target the completed demotion program never covered)
Driving force: simplicity
Design input: docs/maintenance/machinery-blocker-audit-2026-10-09.md (Part 4 item 7; the 677-line ledger with 606 findings and zero fixed-here entries)
Plan review record: the staging series docs/history/reviews/2026-10-10-plan-review-disposition-ledger-removal-r*.md (created by this plan's review loop, r1 onward; the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 2h total, largest task 0.75h
Authoring claim: docs/tmp/authoring-claims/2026-10-10-disposition-ledger-removal.md (session sess_5c51c846-299a-4dfe-a00c-4238d7883663)

## Terms

- The inventory leg: `scripts/review_store_disposition_inventory.py` (391 lines) and its skeleton-generation duty - it enumerates the `docs/reviews/` store (a gitignored store that is empty at authoring time, re-derived 2026-10-10) and writes the markdown ledger skeleton naming un-dispositioned findings; the audited 677-line ledger with 606 findings and zero fixed-here entries is this leg's product. Removal deletes the script, its test, and its registry rows into the removals record.
- The cap-round ledger contract (OUT OF SCOPE, re-scoped at review r1): the cap-round disposition ledger in agents/skills/review-staging/SKILL.md and review-plan rule 8 - re-derived at review r1 as LIVE, load-bearing machinery, not the audited zero-rent record: it is a sanctioned terminal exit path carried by six skill files (plans, execute-plan, done, receiving-review, review-plan, review-staging), its enforcement constants are imported at runtime by scripts/plan_readiness.py (deleting them tool-errors every readiness gate), and the landed review-loop-round-budget plan pins the shape byte-identical and just amended rule 8. The entry's Task-1 second clause misidentified it as part of the audited workflow; this plan records that finding and defers the leg (an operator decision owed if that ceremony is ever to be removed), never touching its surfaces.
- The removals record: the machinery registry's `removals` array, gaining the inventory leg's row with this plan as witness (one registry row covers the script and its test).
- The folding duty: the blocking-findings folding duty (fold accepted blocking findings, mark triage resolved) - untouched; the removal is the bookkeeping, not the folding.

## Why

The audit's item 7 dispositioned the disposition-ledger workflow for deletion: its product is a 677-line ledger with 606 findings and zero entries fixed by the workflow itself - a record nobody consumes, generating per-finding ceremony at cap rounds and skeleton writes over a store that no longer holds records. The one deletion target the completed demotion program never covered. A removal-shaped arm needs no admission test; the measured zero-rent record is its own justification. The entry's Task-1 second clause also targeted the cap-round disposition ledger contract; the review r1 archaeology re-derived that contract as live load-bearing machinery (the sanctioned terminal exit path across six skill files, runtime-imported by the readiness oracle, byte-identical-pinned by the landed round-budget plan), so this plan removes only the inventory leg and records the re-scope beside the origin row - the folding duty and the cap-round bookkeeping stay exactly as they are.

## Gist & Examples

TLDR: delete the inventory skeleton generator and its test into the removals record; the cap-round ledger leg is re-scoped out on the review r1 evidence (live machinery), its finding recorded beside the origin row.

Before: an inventory script can generate a markdown ledger skeleton over a store that holds nothing, and once produced a 677-line, 606-finding ledger that nothing fixed and nobody read.

After: the inventory script, its test, and their registry rows are gone with this plan named as the removal witness; the cap-round ledger contract stays exactly as it is (live machinery, the re-scope finding recorded beside the origin row with the operator decision it owes).

Edge cases: the archaeology gate (Task 0) - if git history shows the audited ledger is NOT the product of these surfaces, the plan stops before any deletion and reports; a cap round with zero accepted risks records no watchlist lines (existing contract behavior, untouched by this plan); legacy records already carrying `cap_closure` stay as history - the removal is forward-looking and never rewrites landed records.

## Outcome

The inventory leg is deleted with registry rows in the removals record naming this plan; the cap-round ledger leg is re-scoped out with the finding recorded beside the origin row; the folding duty, the fold receipts, the cap-closure contract, and the review suites are untouched and green.

Gate delta: one script + one test deleted into the removals record (a removal-shaped arm, no admission test needed per the entry); one dated re-scope note beside the origin row; pins deleted with their spans beside provenance; no new machinery, no schema addition, no refusal added, no skill file edited.

## Assumptions

- Task 0's archaeology is the deletion gate, already partly discharged at authoring time: the inventory script's docstring names its product (the ledger skeleton over `docs/reviews/`), the store is empty at HEAD (re-derived 2026-10-10), and the audited 677-line/606-finding ledger matches that product's shape; the execution-time step re-runs the history check (the ledger artifact's git provenance naming these surfaces) and stops on a mismatch. Basis: the entry's Task 0 wording and the re-derived store state.
- The cap-round ledger leg is out of scope on the review r1 evidence: the shape is a sanctioned terminal exit path (six skill files), its enforcement constants are runtime-imported by the readiness oracle (deletion = every readiness gate tool-errors), the landed round-budget plan pins it byte-identical, and the replacement shape the entry named (the watchlist section) does not match the accepted-risk home it needs. The re-scope is recorded as a dated note beside the origin row at the landing rider, and the operator decision it owes (remove the cap-round ceremony or keep it) is named there. Basis: the review r1 findings P1-P5 (the runtime import graph, the six-file exit path, the round-budget pin, the rule-8 interweaving, the unacknowledged supersession).
- Residual accepted: the audited ledger artifact itself (the 677-line record) lives in git history and is never deleted; the removal is forward-looking (no future generation), and the Task 0 receipt is its provenance of record. Basis: the record-only doctrine for landed history.
- Residual accepted: any workflow documentation outside the named surfaces that still references the inventory script (a stale mention in a landed plan or an old record) is history and stays; the removal covers the operative surfaces (the script, its test, the pins, the registry) only. Basis: the removal's operative-surface scope.

Decision points requiring a grill: none remain (the operator's "next" walk pre-authorized the entry; the entry fixes the two legs it named, the archaeology gate, and the rejected alternatives (the review r1 re-scope superseding its second leg on the live-machinery evidence) including the consumer-building and sampling shapes).

## Standing constraints

- The blocking-findings folding duty stays untouched: the removal is the bookkeeping, not the folding; every existing fold receipt in the staging records survives verbatim.
- No pins weakened: pins are re-aimed beside their provenance or deleted only when their span is deleted with them.
- The review suites stay green at every task landing (the staging validator suite, the review-plan boundary regressions, the pins suite, the parallel-work regressions suite, the liveness test, em-dash, hygiene); a red suite stops the task for reconciliation, never a weakened check.
- Deploy truth: the skill edits reach their runtime homes at this plan's merge-locked landing (the landing is the deploy).
- No machine-specific absolute paths; nothing pushed to origin; the branch rebases onto current main at each fold with the task-start currency check and the stop-and-report arm.
- Rollback arm: revert the offending task's commit; Task 1's deletions restore the script and test byte-identically; Task 2's re-scope note reverts with its commit; the removals row reverts with the registry edit.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the archaeology receipt names the ledger artifact's provenance and the store's state; the re-scope note records the cap-round leg's out-of-scope status with the r1 evidence.
- regression safety: every suite green at every landing; the pins carry only surviving spans; landed records with `cap_closure` remain valid history.
- scope discipline: the changes touch only the inventory leg's surfaces (the script, its test, the registry, the pins) plus the dated re-scope note beside the origin row, and nothing else - no skill file edited.

**Done when:**
- Every span check in `## Validation Commands` holds on the executed tree.
- The battery is green.

**Ship when:**
- No skeleton generation exists to run, the removals record names this plan, and the re-scope note beside the origin row carries the operator decision owed; they follow from the executed tree.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/review_store_disposition_inventory.py` (Task 1: deleted)
- `scripts/test_review_store_disposition_inventory.py` (Task 1: deleted)

**Tests:**
- `scripts/check_maintenance_pins.sh` (Task 1: pins deleted with their spans)

**Docs:**
- `scripts/machinery_registry.json` (Task 1: the rows moved to the removals record with this plan as witness)
- `docs/history/backlog/2026-10-10-disposition-ledger-removal.md` (Task 2: the dated re-scope note beside the row)

**Read-only (referenced, never edited):**
- `docs/maintenance/machinery-blocker-audit-2026-10-09.md` (Part 4 item 7; the audited ledger's evidence)
- `docs/reviews/` (the empty store; the inventory leg's target, read-only archaeology)

**Receipts:**
- Origin row: docs/history/backlog/2026-10-10-disposition-ledger-removal.md (Status: open; the landing rider flips it covered naming this plan)
- Prompt entry: docs/history/backlog/PLAN-PROMPTS.md `## disposition-ledger-removal` (frozen under docs/tmp/authoring-claims/2026-10-10-disposition-ledger-removal.md; pruned by the landing rider with the prune receipt)

## Validation Commands

**Production:**
```bash
test ! -e scripts/review_store_disposition_inventory.py   # the inventory leg deleted
test ! -e scripts/test_review_store_disposition_inventory.py   # its test deleted
python3 -c "import json; d=json.load(open('scripts/machinery_registry.json')); assert any('review_store_disposition_inventory' in json.dumps(r) and r.get('disposition')=='delete' for r in d['removals'])"   # the removals row names this plan
```

**Tests:**
```bash
python3 scripts/test_plan_review_boundary_examples.py   # exit 0
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )   # exit 0
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh   # exit 0 from the repo root
```

### Task 0: the archaeology gate

Files: (none - read-only archaeology recorded in the session log)

- [x] Confirm by git history that the audited ledger (677 lines, 606 findings, zero fixed-here entries) is the product of `scripts/review_store_disposition_inventory.py`'s skeleton generation over the `docs/reviews/` store: locate the ledger artifact in history, run or simulate the generation against the store state it reads, and match the shape; record the provenance receipt (artifact path at its commit, the generation command, the shape match) in the session log; re-derive the store's current emptiness (a nonexistent `docs/reviews/` counts as the empty store - the path is gitignored and machine-local); a mismatch stops this plan before any deletion and reports. [class: REPOSITORY_TEST]

### Task 1: the inventory leg deleted

Files:
- scripts/review_store_disposition_inventory.py
- scripts/test_review_store_disposition_inventory.py
- scripts/machinery_registry.json
- scripts/check_maintenance_pins.sh

- [x] Delete `scripts/review_store_disposition_inventory.py` and `scripts/test_review_store_disposition_inventory.py`; move their machinery-registry rows to the removals record with this plan as the removal witness (disposition `delete`); re-aim or delete with their spans every pin touching them. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the pins suite, the parallel-work regressions suite (`python3 scripts/test_plan_review_boundary_examples.py`), and the hygiene scan green, and land this task as its own commit. [class: REPOSITORY_TEST]

### Task 2: the cap-round ledger leg re-scoped (the finding recorded, the surfaces untouched)

Files:
- docs/history/backlog/2026-10-10-disposition-ledger-removal.md

- [x] Record the re-scope beside the origin row as a dated note: the entry's Task-1 second clause (the cap-round disposition ledger contract) targeted live machinery on the review r1 evidence - a sanctioned terminal exit path across six skill files, runtime-imported by the readiness oracle, byte-identical-pinned by the landed review-loop-round-budget plan, with the entry's named replacement home not matching the accepted-risk record shape - so the leg is deferred and the operator decision it owes (remove the cap-round ceremony or keep it) is named with this evidence; the note never rewrites the row's historical text. [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the untouched surfaces stay green: the validator selftest, the boundary regressions, the pins suite, the liveness test, em-dash over the touched paths, and the hygiene scan; record each exit code in the session log and fix any red span before reporting the task done. [class: REPOSITORY_TEST]
