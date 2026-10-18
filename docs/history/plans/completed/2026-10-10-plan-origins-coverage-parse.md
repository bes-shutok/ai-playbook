# Plan: Parse sanctioned origins shapes and report undercounts

Backlog origin: docs/history/backlog/2026-10-08-plan-origins-plural-block-parses-empty.md (the PLAN-PROMPTS entry `plan-origins-coverage-parse` carries the operator-confirmed prompt; the live extractor reproduction and the landing-closeout trace are recorded in the row)
Driving force: code-quality
Plan review record: the staging series docs/history/reviews/2026-10-10-plan-review-plan-origins-coverage-parse-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 1h total, largest task 0.4h
Authoring claim: docs/tmp/authoring-claims/2026-10-10-plan-origins-coverage-parse.md (session sess_72b1f155-dee1-439a-916f-fcc26d801c74)

## Terms

- Origins block: the plural `Backlog origins (scope of record):` header with its contiguous bulleted origin list (the agents/skills/plans/SKILL.md "Origins block shape" paragraph is the grammar contract of record; this plan changes no skill text).
- Singular line: the one-origin `Backlog origin:` line form, whose parser already takes the first whitespace-delimited token with optional backticks.
- Backtick-span arm: the in-block collector's existing behavior of taking every backtick span on the block's lines; retained for wrapped prose continuation lines.
- Bare-path arm: the new in-block acceptance this plan adds: the first whitespace-delimited token of a block item, with optional surrounding backticks stripped and trailing punctuation (`.,;:`) stripped, that ends with `.md` and resolves as a backlog reference through the existing `_is_backlog_ref` (the backlog, completed, and rejected directories), contributes its basename; the token scoping mirrors the singular line's grammar and keeps compound bullets from parsing a trailing path.
- Parser undercount: a parse whose origin set is missing basenames the plan's origins-dispositions section lists; the witnessed shape is a plural block of plain unbackticked bullets parsing to zero.
- Undercount audit: a warning-only comparison of origins-dispositions basenames against the parsed set. This plan adds the same warning to coverage and mark-covered modes before their no-origins early returns; it does not change their exit or mutation behavior.
- Set difference: the listed basenames absent from the parsed set, the audit warning condition; counts alone cannot distinguish a wrong-set parse at count parity.
- Vacuous pass: a gate passing because nothing parsed (zero origins to verify), the witnessed failure that let covered flips ride a landing unverified.
- First-landed wins: when more than one plan cites the same origin, the earliest landed plan owns it; a later plan must resolve the duplicate as a coverage conflict.
- Fold then delete: move accepted work from a covered backlog row into its covering plan, then delete the row as part of that same landing.
- Witnessed archived plan: docs/history/plans/completed/2026-10-07-done-readiness-closeout-boundary.md, whose two-origin plain-bullet block both extractors returned empty for (reproduced 2026-10-08 by direct invocation), and whose post-fix coverage check exposes a real first-landed-wins conflict (see Assumptions).

## Why

A landed plan's skill-sanctioned plural origins block parses to zero origins: the in-block item loop in scripts/check_plan_origins_closed.py collects only backtick spans, and the witnessed archived plan's bullets are plain paths, so both extractors returned `[]` on direct invocation (reproduced 2026-10-08). The two grammar halves disagree about backticks: the singular line accepts unbackticked paths, the plural block does not, so single-origin plans parse and multi-origin plans in the witnessed bullet style parse empty. The consequence is that the coverage gate had nothing to verify and `--mark-covered` had nothing to flip, so the witnessed landing's covered flips rode unverified and one row needed a manual flip at closeout (the row records the landing session's own words: "the mark-covered mode doesn't parse the plural origins block ... flipping both rows manually", and the word "again" records an earlier occurrence). The new comparison reports this undercount in warning-only form before the modes' no-origins early returns. It remains non-blocking until a production warning catches a real undercount and a separate reviewed change authorizes promotion.

## Gist & Examples

TLDR: improve code quality by making the origins checker parse each plural-block bullet's first path token and report undercounts as warnings in coverage and mutator modes, with fixtures pinning the witnessed shapes, dedup, compound-bullet scoping, and warning behavior.

Before: a two-origin plain-bullet plural block parses to zero, the coverage gate passes vacuously, the mutator flips nothing, and the undercount surfaces as a manual flip at landing closeout.

After: the same block parses both dated basenames in order, the coverage gate's duplicate-origin detection sees both (and on the witnessed plan names the real first-landed-wins conflict the vacuous pass was hiding), a parse that still misses listed basenames emits the set difference as a warning without changing the mode result, and the archive mode's existing warning is untouched.

Edge cases: a block mixing backticked and unbackticked bullets parses both (deduped by basename, first occurrence kept); the same basename appearing twice in different forms parses once; a compound bullet's bare-path arm takes only its leading token, backticked spans still parsing through the span arm; a `.md` token that is not a backlog reference is ignored by both arms exactly as the singular line ignores it; a plan with no origins block parses empty and the audit stays inert (nothing listed), while a block that parses empty with a non-empty dispositions list is exactly the shape the audit warns about; the singular line's behavior is unchanged.

## Outcome

Every origins shape the plans skill sanctions parses to the full named origin set, and a parse below the plan's own named set is reported as a warning instead of disappearing into a vacuous pass.

- The plural origins block parses the leading list token after its marker, strips optional backticks and trailing `.,;:`, and accepts backlog `.md` references as ordered deduped basenames through both extractors; the backtick-span arm, singular line, and blank-line grammar are unchanged.
- `--check-coverage` and `--mark-covered` report the listed-but-unparsed set difference through one shared warning helper without changing existing exit or mutation behavior; the archive mode's warning is unchanged.
- Suite fixtures pin the plain-bullet plural block, the mixed and duplicate-basename blocks, the compound-bullet token scoping, the wrapped-prose shape, the warning-only audit arms including the parsed-empty-but-listed shape, and the shared extractor's archive and corpus mode behavior over the widened parse.

Gate delta: none; the origins-closure coverage and mark-covered modes gain warning text only, with no new refusal condition, gate, fence, protocol layer, or schema state field. The bare-path arm widens parser acceptance; the guard liveness ledger's current catch-to-incident ratio at authoring time is 19 catches to 24 incidents (`python3 scripts/gate_liveness_ledger.py show`, TOTAL: catches=19 incidents=24 ratio=19:24 overrides=7, re-derived 2026-10-10), cited per the ledger-citation duty.

## Assumptions

- The undercount audit in coverage and mutator modes is warning-only until an operational true catch is recorded; it must not alter exit status or mutation behavior. This follows the repository Machinery admission protocol, because the witnessed parser failure was not caught by the archive audit. A later blocking promotion requires a separate reviewed change after the first production warning catches a listed-but-unparsed origin. The archive mode's existing warning stays unchanged in behavior and position.
- The audit's comparison set is the plan's origins-dispositions basenames (the existing `_dispositions_basenames` extraction), compared as a set difference against the same extractor the mode already consumes, and the comparison lives in one shared helper both new call sites use; the archive mode's inline copy stays frozen. Basis: the script's existing plan-mode audit pairing and the entry's own wording pointing at reuse rather than re-derivation.
- The bare-path arm reads the first whitespace-delimited token after the list marker on block items only (bulleted lines inside the block), never free prose, so compound and annotated bullets parse their leading path and never a trailing one. Basis: the singular line's own token grammar and the witnessed shapes being plain bullets.
- The arm's acceptance inherits `_is_backlog_ref` whole, including the rejected-archive arm: the entry prompt names the backlog and completed directories, and mirroring the singular line's own semantics adds the rejected archive; that widening is conscious and recorded here as the mirroring choice. Basis: the entry prompt's "mirroring the singular line's backtick-optional acceptance" and the shared predicate's definition.
- The parse widening is corpus-wide by design (one grammar in every mode, no second grammar to drift), and its blast is owned: plan mode re-run over completed plain-bullet plans may newly report stragglers for fold-then-delete origins whose rows are gone (not a standing duty over completed plans), and the corpus scan's warning count grows on the same class, which is the survey's honest new signal; Task 3 pins the archive and corpus mode behavior over the witnessed shape so the widening lands tested in every consumer. Basis: `extract_origin_basenames` is the shared parse of all three modes and the entry mandates one checker grammar.
- The witnessed plan's post-fix coverage result is a genuine duplicate-origin conflict, separate from the warning-only undercount audit: `--check-coverage` exits 1 naming docs/history/plans/completed/2026-10-06-authoring-staging-preflight-gates.md as the first-landed citer of the staging-series origin. The conflict is existing gate behavior and is not this plan's to resolve. Validation never runs the mutator against the live backlog tree. Basis: the peer plan's backticked origins block parses the staging-series origin today, and the origin row records that first-landed race.
- **Machinery admission for the coverage/mutator undercount audit:** the 2026-10-08 reproduction of the 2026-10-07 closeout failure is the concrete incident this warning is meant to surface, but it is not a true catch by the existing archive audit: that mode returns before the warning on an empty parse. Land the new audit warning-only and read-only with respect to control flow. Expected catch frequency is one per parser/grammar regression; the corpus rate is unmeasured. False-positive cost is one warning line and operator review, with no stopped operation or mutation change. Review on 2027-01-11; remove if no true warning catch occurs in the review window. Pre-register `script:origins-coverage-undercount-audit` in `scripts/machinery_registry.json`, naming the audit surface, sunset, and promotion criterion: a separate reviewed change may promote only after the warning catches a real listed-but-unparsed origin in an operational run. Pre-register the removal transition in that entry's note: if no production catch occurs by the review date, remove only the undercount-audit helper and its call sites, preserving `scripts/check_plan_origins_closed.py`'s shared parser and existing coverage/mutator behavior, and move the registry row into the registry's `removals` record with the no-catch sunset witness; if promotion criteria are met, a separate reviewed change records the promotion disposition instead.
- No skill text changes: the plans skill's "Origins block shape" paragraph already states the shape this fix makes true ("the origins checker parses exactly this grammar"), so the implementation moves to the skill text, not the reverse. Basis: the entry prompt's explicit constraint and the skill paragraph at agents/skills/plans/SKILL.md line 33.

Decision points requiring a grill: none remain (the entry prompt fixes the task order, the arm shape, and the rejected alternatives; the audit's sanction split, placement, and set-difference form are resolved above).

## Standing constraints

- agents/skills/plans/SKILL.md is byte-identical after this plan; no skill text, pins over skill text, or vendored twin action is in scope. Implementation and test edits are limited to two script files; Task 3 separately handles the three backlog bookkeeping paths and the machinery registry path it declares.
- The singular line's parsing behavior, the backtick-span arm, the blank-line grammar, and the archive mode's warning (including its position after that mode's early return) are unchanged; no existing suite test's expectations change.
- The pins suite, the hygiene scan, and the em-dash added-lines scan over the touched scripts stay green at every landing.
- No machine-specific absolute paths in any edited file; no em-dashes in new lines.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the witnessed archived plan's block parses to exactly its two dated basenames in order through both extractors; the mixed, duplicate-basename, and compound-bullet blocks parse per the token and dedup contracts; the coverage and mutator audits report the listed-but-unparsed set difference as warnings without changing exit status or mutation behavior, including the parsed-empty-but-listed shape.
- regression safety: the origins checker suite passes unchanged in all pre-existing tests; `python3 scripts/test_machinery_inventory.py` passes; the inventory check reports only its 18 recorded baseline failures and no new failure; the pins suite and hygiene scan pass; the singular line and archive-mode behaviors are pinned unchanged by the existing suite.
- scope discipline: production and test changes are exactly scripts/check_plan_origins_closed.py and scripts/test_check_plan_origins_closed.py; Task 3 also adds one pre-registered machinery row, deletes the completed origin row, and removes its two dependent metadata references, as required by the repository closeout contract.

**Done when:**
- Every span check in `## Validation Commands` holds on the executed tree.
- From the repository root, `REPO="$(git rev-parse --show-toplevel)"` resolves the checkout and `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )` exits 0.

**Ship when:**
- A plan landing with the witnessed plain-bullet plural shape passes through the coverage gate with real detection instead of a vacuous pass (including a truthful conflict verdict when a first-landed peer owns an origin), and any future grammar drift that parses below the plan's named origin set is reported with the missing names; blocking promotion waits for a true production catch and a separate review.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_plan_origins_closed.py` (the in-block item collection in `extract_origin_basenames` gains the token-scoped bare-path arm; one new shared undercount-audit helper; `run_check_coverage_mode` and `run_mark_covered_mode` call it before their no-origins early returns; the extractor is the shared parse of the archive and corpus modes, so the widening lands corpus-wide by design with its blast owned in Assumptions and pinned by fixtures)

**Tests:**
- `scripts/test_check_plan_origins_closed.py` (new fixtures inside the existing test class for the witnessed shapes, the dedup and compound-bullet contracts, the warning-only audit arms including the parsed-empty-but-listed shape, and the archive and corpus mode behavior over the widened parse)

**Machinery admission record:**
- `scripts/machinery_registry.json` (Task 3 adds the pre-registered warning-only audit row and its sunset/removal commitment; validation checks the row's required incident, frequency, cost, review-date, promotion, and removal markers)

**Read-only (referenced, never edited):**
- `agents/skills/plans/SKILL.md` (the "Origins block shape" paragraph; the grammar contract of record, frozen)
- `docs/history/plans/completed/2026-10-07-done-readiness-closeout-boundary.md` (the witnessed archived plan; the coverage-check target)
- `docs/history/plans/completed/2026-10-06-authoring-staging-preflight-gates.md` (the first-landed citer of the staging-series origin; named by the witnessed plan's post-fix conflict)
- `docs/history/backlog/PLAN-PROMPTS.md` (the plan's own dispatch entry; the maintenance monitor prunes it under the plan-file-exists rule before execution, with the plans-root witness receipt)

**Task 3 landing bookkeeping:**
- Delete `docs/history/backlog/2026-10-08-plan-origins-plural-block-parses-empty.md`; name this plan as the witness in the commit message.
- Remove every live metadata reference to the deleted row in `docs/history/backlog/2026-10-09-dangling-cluster-pointer-staging-series-gate-slug.md` and `docs/history/backlog/2026-10-09-primary-class-anchors-grammar-drift.md`: this is the `Skill/step` field in the first row and the `Cluster:` field in the second. Preserve their other references.

**Receipts:**
- Origin row: docs/history/backlog/2026-10-08-plan-origins-plural-block-parses-empty.md (deleted with the final task landing; the commit message names this plan as the witness)
- Prompt entry: docs/history/backlog/PLAN-PROMPTS.md `## plan-origins-coverage-parse` (frozen under docs/tmp/authoring-claims/2026-10-10-plan-origins-coverage-parse.md. The log rule assigns only a landing's own-entry prune to the landing leg; any other removal, including this existing plan's entry before execution, belongs to the maintenance monitor's rolling-log duties and carries its plans-root witness receipt. The monitor applies the prune rule to every existing plan entry, including this one; Task 3 does not edit prompt logs.)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link is weak or speculative, drop it as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/plans/SKILL.md`; its grammar contract is read-only for this plan.
- Other origin parsers and maintenance gates; this plan changes the shared extractor and its two named gate call sites only.

## Validation Commands

**Production:** The test suite includes an assertion against the witnessed archived plan and verifies both production extractors return the exact ordered origin basenames. Run it in the Tests commands below.

**Tests:**

Before this block, run the maintenance monitor's Step 3 rolling-log prune. That duty removes every PLAN-PROMPTS entry whose plan file already exists in the resolved plans directory, including this plan's entry, and records one plans-root witness receipt per removal. This is an independent monitor write outside Task 3; Task 3 does not edit prompt logs.

```bash
REPO="$(git rev-parse --show-toplevel)" || exit $?
python3 scripts/test_check_plan_origins_closed.py || exit $?   # exit 0, including plain-bullet, mixed, duplicate-basename, compound-bullet, wrapped-prose, warning-only audit, and archive/corpus-mode fixtures
python3 scripts/test_machinery_inventory.py || exit $?   # exit 0
inventory_output="$(python3 scripts/machinery_inventory.py --check 2>&1)"; inventory_status=$?; printf '%s\n' "$inventory_output"; test "$inventory_status" -eq 1 || exit "$inventory_status"
expected_inventory_failures="$(cat <<'BASELINE'
script:skill_text_budget.py: witness ref does not resolve to a tracked path: docs/history/plans/2026-10-10-maintenance-skill-size-refactor.md
regrowth: unregistered script file scripts/base_reflog_audit.py
regrowth: unregistered script file scripts/check_authoring_gist_sample.py
regrowth: unregistered script file scripts/check_authoring_plans_liveness.py
regrowth: unregistered script file scripts/check_run_continuity.py
regrowth: unregistered script file scripts/code_delta_classifier.py
regrowth: unregistered script file scripts/corrections_record.py
regrowth: unregistered script file scripts/deploy_runtime_helpers.sh
regrowth: unregistered script file scripts/execution_claim.sh
regrowth: unregistered script file scripts/fix_plan_em_dashes.py
regrowth: unregistered script file scripts/gate_liveness_ledger.py
regrowth: unregistered script file scripts/plan_delta_classifier.py
regrowth: unregistered script file scripts/plan_task_span.py
regrowth: unregistered script file scripts/read_freshness_probe.py
regrowth: unregistered script file scripts/run_plan_gates.sh
regrowth: unregistered script file scripts/staged_scope_guard.py
regrowth: unregistered script file scripts/sync_runtime_scripts.sh
regrowth: unregistered state field state-field:queued_execution
BASELINE
)"
observed_inventory_failures="$(printf '%s\n' "$inventory_output" | sed -n 's/^FAIL: //p' | sort)"
expected_inventory_failures="$(printf '%s\n' "$expected_inventory_failures" | sort)"
test "$observed_inventory_failures" = "$expected_inventory_failures" || exit 1   # expected baseline exit 1; compare all failure identities so no new failure can replace an old one
python3 - <<'PYREG'
import json
from pathlib import Path
entries = json.loads(Path("scripts/machinery_registry.json").read_text())["entries"]
rows = [row for row in entries if row.get("id") == "script:origins-coverage-undercount-audit"]
assert len(rows) == 1, "expected exactly one origins undercount machinery row"
note = rows[0].get("note", "")
for marker in ("warning-only", "2026-10-08 reproduction", "one per parser/grammar regression", "one warning line and operator review", "2027-01-11", "first production true catch", "removals record", "no-catch sunset witness", "undercount-audit helper and its call sites"):
    assert marker in note, f"machinery row note missing admission marker: {marker}"
PYREG
( cd "$REPO" && bash scripts/check_maintenance_pins.sh ) || exit $?   # exit 0
MERGE_BASE="$(git merge-base HEAD main)" || exit $?
bash scripts/check-no-em-dash.sh added-lines --base "$MERGE_BASE" -- scripts/check_plan_origins_closed.py scripts/test_check_plan_origins_closed.py || exit $?   # exit 0 on new lines only
( cd "$REPO" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh ) || exit $?   # exit 0 from the repo root
if output=$(python3 scripts/check_plan_origins_closed.py --check-coverage docs/history/plans/completed/2026-10-07-done-readiness-closeout-boundary.md 2>&1); then
  echo "expected the witnessed duplicate-origin conflict to fail coverage" >&2
  exit 1
else
  status=$?
  test "$status" -eq 1 || exit "$status"
  printf '%s\n' "$output" | grep -F "2026-10-06-authoring-staging-preflight-gates.md" >/dev/null || {
    echo "coverage failed without naming the witnessed first-landed citer" >&2
    exit 1
  }
fi   # exit 1 and name the first-landed citer: the fix exposes the real conflict the vacuous pass hid
```

### Task 1: the token-scoped bare-path arm in the plural-block parser

Files:
- `scripts/check_plan_origins_closed.py`

Primary class anchors:
- `extract_origin_basenames` in `scripts/check_plan_origins_closed.py`, owns the in-block item collection this plan widens.

- [x] In `extract_origin_basenames`'s item loop, add a bare-path arm beside the retained backtick-span arm: remove the list marker, take the first whitespace-delimited token, strip optional surrounding backticks and trailing `.,;:`, and accept only `.md` tokens recognized by `_is_backlog_ref`; append the basename to the shared ordered, seen-deduped list. [class: IMPLEMENTATION_REQUIRED]
- [x] A bullet whose leading token is not a `.md` path contributes only its backtick spans. Keep singular-line parsing, header matching, blank-line grammar, and `extract_coverage_origin_basenames`'s bare-header-line arm unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `feat: parse bare backlog origins in plural blocks` [class: IMPLEMENTATION_REQUIRED]


### Task 2: the shared undercount audit in the coverage gate and the mutator

Files:
- `scripts/check_plan_origins_closed.py`

Primary class anchors:
- `run_check_coverage_mode` in `scripts/check_plan_origins_closed.py`, owns the coverage gate this plan arms.
- `run_mark_covered_mode` in `scripts/check_plan_origins_closed.py`, owns the mutator this plan arms.

- [x] Add one shared helper that takes parsed basenames and plan text and returns the listed-but-unparsed basenames using the existing `_dispositions_basenames` extraction. [class: IMPLEMENTATION_REQUIRED]
- [x] Call the shared audit immediately after parsing and before the no-origins early return in both `run_check_coverage_mode` and `run_mark_covered_mode`; emit a warning on a non-empty difference without changing mode outcome, before any mutator flip, and report the gap in the archive audit's shape. [class: IMPLEMENTATION_REQUIRED]
- [x] Distinguish an empty parse of a matched origins block from an unmatched header line in the audit warning; preserve the archive mode's inline warning behavior and position byte-identically. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `feat: audit uncovered plan origins before coverage actions` [class: IMPLEMENTATION_REQUIRED]


### Task 3: fixtures, warning-only audit, and closeout bookkeeping

Files:
- `scripts/check_plan_origins_closed.py`
- `scripts/test_check_plan_origins_closed.py`
- `scripts/machinery_registry.json`
- `docs/history/backlog/2026-10-08-plan-origins-plural-block-parses-empty.md`
- `docs/history/backlog/2026-10-09-dangling-cluster-pointer-staging-series-gate-slug.md`
- `docs/history/backlog/2026-10-09-primary-class-anchors-grammar-drift.md`

Primary class anchors:
- `PlanOriginsClosedTest` in `scripts/test_check_plan_origins_closed.py`, the suite class the new fixtures join.

- [ ] Add extractor fixtures inside `PlanOriginsClosedTest` for the witnessed archived plan and the plain and mixed bullet forms, duplicate basename, compound bullet, wrapped prose, non-backlog `.md` token, and leading-token punctuation on bare paths and punctuation inside backticked paths; assert both extractors' outputs and preserve the existing main-block placement. [class: REPOSITORY_TEST]
- [ ] Task 3 supersedes Task 2's checked fail-loud clause: change the undercount audit in coverage and mutator modes to warning-only, preserving their pre-existing exit and mutation behavior and leaving the archive warning unchanged. A later blocking promotion requires a separate reviewed change after a production true catch. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add audit fixtures that report the missing basename without changing coverage exit status or mutator flips; include parsed-empty-but-listed and unmatched-header-with-listed-dispositions shapes. [class: REPOSITORY_TEST]
- [ ] Add the pre-registered warning-only row `script:origins-coverage-undercount-audit` to `scripts/machinery_registry.json`, with the 2027-01-11 review date, explicit first-production-catch promotion criterion, and the no-catch sunset transition removing only the undercount-audit helper/call sites while preserving the shared checker, then moving the row to the `removals` record with its witness. [class: IMPLEMENTATION_REQUIRED]
- [ ] Pin archive and corpus mode behavior over the widened plain-bullet parse through their existing entry points. [class: REPOSITORY_TEST]
- [ ] Run the `## Validation Commands` block and record every actual status in the execution manifest, including the expected inventory baseline report. [class: REPOSITORY_TEST]
- [ ] Delete the completed origin backlog row; remove its reference from the `Skill/step` field of `2026-10-09-dangling-cluster-pointer-staging-series-gate-slug.md` and from the `Cluster:` field of `2026-10-09-primary-class-anchors-grammar-drift.md`, preserving their other references; name this plan as the witness in the commit message. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `test: cover plural origin parsing and undercount audit (plan-origins-coverage-parse)` [class: REPOSITORY_TEST]

