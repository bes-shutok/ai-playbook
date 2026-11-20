# Plan: doing-code-review staging-doc scaffold pointer

Backlog origin: docs/history/backlog/2026-10-30-doing-code-review-staging-doc-scaffold-pointer.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/*-plan-review-doing-code-review-staging-doc-scaffold-pointer-p450326e1-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 0.5h total, largest task 0.5h
Executed: yes (9a772ba6ff0c850fbfcbb646d41be7692dc25b07)

Authoring claim: 2026-10-30-doing-code-review-staging-doc-scaffold-pointer.md (session sess_3ea5814f-de46-4593-b00d-9c056140b0ab)

## Terms

- staging record pair: the staged Markdown review record plus its `.stats.json` sidecar that the doing-code-review staging-doc gate mandates as the review deliverable.
- Finding-construction recipe: the `## Finding-construction recipe (scaffold before drafting)` section of `agents/skills/review-staging/SKILL.md`, the construction path of record for the pair.
- scaffold mode: the `validate_review_staging.py` metadata exit `--scaffold` that prints the current structural template a drafter fills instead of recalling the shape from memory.
- panel skill: the doing-code-review skill, the canonical review-panel procedure whose file is excluded from ad-hoc edits (plan route only).

## Why

The doing-code-review staging-doc gate mandates the staging record pair but never names its construction path, so a correctly-run panel session can still draft the pair by imitating a recently landed record and pay repeated validator refusals re-deriving a shape review-staging's Finding-construction recipe already prescribes. One cross-reference sentence at the gate closes that gap.

## Gist & Examples

TLDR: one cross-reference sentence at the doing-code-review staging-doc gate points drafters at review-staging's Finding-construction recipe, so the mandated staging record pair is drafted from the validator's generated scaffold instead of from imitated records, cutting the witnessed repeated validator-refusal rounds per record, driving force: efficiency.

Before: the gate paragraph says "Always produce the staging doc" and the hard gates call the doc the deliverable, but the nearest in-file construction guidance sits pages deeper in the Stats sidecar paragraph, so a panel runner who starts at the gate drafts from a recent record and iterates through missing severity groups, missing per-finding Comment and Analysis blocks, missing Review Statistics, the run-id pair, soften-table parity, and calibration fields before the first validator pass (witnessed 2026-10-30: six-plus refusals per record, twice in one session).
After: the same gate paragraph names the Finding-construction recipe (scaffold before drafting; `validate_review_staging.py --scaffold`) as the construction path, so the first draft starts from the generated scaffold and the first validator run grades substance instead of format.

## Outcome

A reader of the doing-code-review staging-doc gate reaches the canonical construction path for the staging record pair in one hop.

- The gate paragraph names the Finding-construction recipe and the scaffold mode as the drafting source, so new panel sessions start from the generated scaffold instead of imitated records.
- Fewer format-refusal iterations per staged review; validator runs grade findings substance earlier.
- No behavior change anywhere else: the recipe, the validator, and every other byte of the panel skill stay as they are.

Gate delta: none (one prose cross-reference sentence; no refusal class, hard gate, fence, protocol layer, schema field, or dispatch-pausing condition is added or removed).

## Assumptions

- assume the sentence lands appended to the existing "Always produce the staging doc" paragraph in `agents/skills/doing-code-review/SKILL.md` (the cluster beside the Modes table); basis: the origin entry's scope arms name that cluster as the first permitted site, verified against the file's current bytes.
- assume the Modes-table Staged row alternative is rejected; basis: the receipt in the decision-points trailer below.
- assume the pointer target stays unchanged (review-staging's Finding-construction recipe section and the validator `--scaffold` exit); basis: both verified present at authoring time, and single-homing keeps the recipe the one construction source.
- assume no pin, suite, or budget regression; basis: the two maintenance pins over this file grep fixed strings elsewhere in it, the referencing suites read integration spans elsewhere, and the file sits about 18 KB under its byte cap (all verified 2026-11-06).

Decision points requiring a grill: pointer placement: gate-cluster paragraph over Modes Staged row, basis: the cluster is the pre-drafting read surface while a table cell is a mode selector and carries pointer prose poorly, recorded under the maintenance-selected standing authorization 2026-11-06, affects the Task 1 edit spec

## Evaluation Criteria

**Quality dimensions:**
- correctness: the inserted sentence names the recipe section and the `--scaffold` flag exactly as they exist in `agents/skills/review-staging/SKILL.md` and `scripts/validate_review_staging.py`.
- containment: the whole change is one sentence appended to one paragraph in one file; every other byte identical.
- non-regression: the maintenance pins, the referencing suites, the byte-budget advisory, and the hygiene scan all stay green.

**Done when:**
- the prescribed sentence is the final sentence of the "Always produce the staging doc" paragraph in `agents/skills/doing-code-review/SKILL.md`, and a grep over the file finds exactly one occurrence of `Finding-construction recipe`.
- all Validation Commands exit 0 over the changed tree.

**Ship when:**
- none: repository-local skill text; no deployed, cross-team, or human-owned release condition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/doing-code-review/SKILL.md` (Task 1) *(one appended sentence; prose only)*

**Tests:**
- none *(no new tests; the plan runs the existing suites named in Validation Commands)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/review-staging/SKILL.md`; reason: the pointer target, unchanged by design (single-homing the construction recipe).
- `scripts/validate_review_staging.py`; reason: the validator surface is unchanged; the sentence only cites its existing `--scaffold` exit.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_review_contract_impact_closure.py scripts/test_review_agent_normative_example_selection.py -q
bash scripts/check_maintenance_pins.sh
python3 scripts/skill_text_budget.py --check
bash scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base <merge-base>
```

### Task 1: Point the staging-doc gate at the scaffold-first recipe

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/doing-code-review/SKILL.md` *(one appended sentence; no other bytes)*

No Primary class anchors block: this task changes panel skill prose only; no production class owns the behavior.

Prescribed sentence (byte-exact; the only content change of this plan):

    Draft the staging record pair per `review-staging`'s Finding-construction recipe (scaffold before drafting; `validate_review_staging.py --scaffold`), never by imitating a recent record.

- [x] Gate-cluster probe: given `agents/skills/doing-code-review/SKILL.md` at the execution base, expects the "Always produce the staging doc" paragraph present verbatim and zero occurrences of `Finding-construction recipe` in the file, so the insertion state is pinned before editing [class: REPOSITORY_TEST]
- [x] Append the prescribed sentence as the final sentence of that paragraph, changing no other byte in the file [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: every Validation Command exits 0 over the changed tree (suites, pins, budget advisory with no new breach, hygiene scan, and the added-lines em-dash gate over the task diff) [class: REPOSITORY_TEST]
- [x] Commit: `docs: point doing-code-review staging gate at the scaffold-first recipe` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-10-30-doing-code-review-staging-doc-scaffold-pointer.md — covered by this plan's execution landing 9a772ba6ff0c850fbfcbb646d41be7692dc25b07 (one appended sentence at the doing-code-review staging-doc gate; Task 1 validated, gates green, pins failure pre-existing on main); origin row deleted in the same change.
