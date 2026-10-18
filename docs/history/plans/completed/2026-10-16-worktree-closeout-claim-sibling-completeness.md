# Worktree closeout: gate derives required stats siblings from claimed review records

Slug: worktree-closeout-claim-sibling-completeness
Budget: 1.5h authoring; declared execution budget 1.5h (one focused guard change + fixtures + two one-sentence recipe edits)

## Backlog origins (scope of record)

- docs/history/backlog/2026-10-13-worktree-closeout-claims-sidecar-siblings.md

## Terms

- Claimed record: a `.md` review-record path named by the gate-removal claims file, or a plan label-line citation that resolves under the primary reviews home.
- Required sibling: the `.stats.json` sidecar at the same stem (`Path.with_suffix(".stats.json")` on the record path), required by the staging validator's twin contract for owned staging records.
- Target home: the primary checkout's configured reviews home the gate verifies presence against.
- Worktree staging home: the facts-resolved reviews home under the worktree being removed, where staging records and their sidecars are authored before migration.

## Why

Witnessed 2026-10-13 (origin row): a claims file naming two review records' markdown paths only passed `gate-removal`; teardown removed the worktree with both `.stats.json` sidecars; the records are permanently invalid in the primary corpus. The gate's preservation inventory (plan label-line citations plus claims entries) verifies what it is named, and nothing stops the removal while a named record's sibling still exists only inside the worktree. The fix is a completeness extension of the existing inventory keyed to the destruction condition, not a new gate.

## Gist & Examples

TLDR: the worktree-removal gate refuses teardown while a claimed record's stats sibling would be destroyed by it (the sibling exists in the worktree staging home and is absent from the primary home), so a claim set that names records but not sidecars can no longer strand binding metadata.

Before: claims name `2026-10-13-plan-review-x-r1.md` only; the gate verifies that path at the home and passes; removal deletes `r1.stats.json` sitting in the worktree staging home; the validator later reports the record as an owned half-pair.

After: the same invocation refuses before any removal verdict, naming the worktree-side sibling and the transfer remedy; transfer the sidecar with the corrected claim set and the gate passes.

## Outcome

Teardown can no longer destroy a claimed record's required sidecar.

- `gate-removal` refuses (OUTCOME: fail) when a claimed or exact-cited `.md` record's `.stats.json` sibling exists in the worktree staging home and is absent from the target home, naming the missing-from-home sibling path and the transfer remedy, before the removal verdict.
- The sibling arm is an inventory extension: containment, refusal, series, and branch-closeout arms stay byte-identical otherwise, and every existing pass-shaped fixture (records whose siblings exist nowhere) stays green unchanged.
- The producer recipes name the sibling-enumeration step in one sentence each (done Step 2; the plans skill's Final Step closeout paragraph); the maintenance authoring payload's existing move step already names every staging doc and sidecar and is pinned by an acknowledgment fixture, not edited.

Gate delta: none - the change extends an existing gate's claim inventory with a destruction-conditioned derived requirement (fix-class, origin-cited; the admission facts below), adds no new gate, refusal class, fence, protocol layer, or schema field, and no task pauses dispatch or later work.

Machinery admission: incident = the 2026-10-13 sidecar loss (origin row), whose sidecars existed only in the worktree - exactly the condition the arm keys to; expected catch = every future teardown about to destroy a claimed record's worktree-only sibling, one true catch witnessed; false-positive cost = a teardown refusal when a worktree-side sibling is genuinely not required (for example a skip-waived record), remedied by transferring it or correcting the claim set, never a byte loss; review date 2027-01-16; retires or demotes nothing (pure inventory extension). Pre-registered condition: a witnessed false refusal narrows the record grammar rather than removing the arm; removing the arm re-opens the witnessed loss and requires an operator decision recorded in the origin row.

## Assumptions

- The refusal condition is the destruction condition (sibling present in the worktree staging home, absent from the target home), so the legacy corpus of sidecar-less records and the validator's skip-waiver class produce no refusal: nothing worktree-side exists to destroy; basis: the validator's missing-sidecar fail-closed arm ("missing required stats sidecar") and skip waiver govern corpus validity separately, and the witnessed loss had worktree-only sidecars.
- The check applies to claims entries and exact-token citations that verify under the home; series citations keep their witness-presence semantics with no sibling derivation for any member, witness included; `.stats.json`-suffixed claims verify as themselves and derive nothing; basis: the origin names the claim inventory as the gap, and the series arm's contract is a separate witnessed surface.
- A worktree with no resolvable staging home (no facts-resolved reviews home under it) takes no worktree-side probe and cannot refuse on the sibling arm; basis: the worktree provisioning contract (facts transfer) and the gate's own home resolution pattern.
- verify-records parity is deliberately out of scope: the binding surface is the removal gate; the pre-check keeps its plain-exit reporting contract; basis: rejected arm below.
- The new refusal line joins the existing missing/refused aggregate, so one run names incomplete records and destroyed siblings together before the shared remedy; basis: the gate's existing aggregate output shape.
- Review-layer execution duty: the executor runs the Validation Commands battery before landing; this restates Task 3's acceptance items and existing execute-plan law, so no separate blocking-duty declaration is made.

Decision points requiring a grill: none remain: the origin row's Expected adjudicates gate-derives-plus-recipes-name-it over prose-only recipes (a recipe alone cannot stop a removal already in flight) and over rebuilding stranded sidecars after teardown (the no-fabrication rule); verify-records parity is rejected as an advisory-surface change with no binding effect; a second completeness validator is rejected by the machinery protocol

## Standing constraints

- Never push to origin; stage by explicit path only; never amend a commit reachable from main.
- The hygiene scan (exit 0) runs before every commit; no em-dashes and no absolute personal home directory paths in committed files.
- Bounded repair only: never edit a gate or validator mid-lane to unblock the lane.
- Skills-repo edits follow the vendored-sync rules: the repo copies land in this change; the runtime twin carries a tracked landing path if it is not synced in the same run.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the refusal fires exactly for claimed or exact-cited `.md` records whose home sibling is missing, and never for present-sibling or sidecar-suffixed claims.
- safety: the sibling check runs before the removal verdict and never weakens the existing containment, refusal, series, or branch-closeout arms.
- simplicity: one derivation helper over the already-verified record paths; no second inventory, ledger, or validator.

**Done when:**
- the Validation Commands battery exits 0 and the fixtures cover the refusal, both pass shapes, and the series-untouched control.

**Ship when:**
- the landing carries the plan, gate change, fixtures, both recipe sentences, and the origin row disposition.

## Review Scope

Category: Primary implementation

- `scripts/worktree_closeout_migrate.py`

Task 1 - Gate derives required siblings (destruction-conditioned):

- [x] `cmd_gate_removal` derives the required sibling for every verified claims entry and exact-token citation whose path ends `.md` and refuses when that sibling exists in the worktree staging home (the facts-resolved reviews home under the worktree being removed) and is absent from the target home: the refusal joins the existing aggregate naming the missing-from-home sibling path and the transfer remedy, and the gate returns 1 before any removal verdict; a sibling absent from the worktree staging home (never existed, already transferred, or the record carries none) never refuses. [class: IMPLEMENTATION_REQUIRED]
- [x] The module usage text names the sibling arm: given the gate-removal paragraph in the module docstring, expects one added sentence stating the gate refuses teardown while a claimed record's `.stats.json` sibling exists in the worktree staging home and is absent from the home, with the rest of the paragraph unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Series and sidecar arms stay untouched: given a `-r*.md` series citation whose highest-round witness is present, expects the existing witness-presence verdict with no sibling derivation for any member, witness included; given a claims entry ending `.stats.json`, expects it verifies as itself and derives nothing. [class: IMPLEMENTATION_REQUIRED]
- [x] Aggregate ordering holds: given a claims file with one absent record and one record whose worktree-side sibling would be destroyed, expects one run printing both the missing-record line and the sibling-destruction line before the shared remedy and OUTCOME: fail. [class: IMPLEMENTATION_REQUIRED]

Primary class anchors:

- `cmd_gate_removal` in `scripts/worktree_closeout_migrate.py`
- `_series_members` in `scripts/worktree_closeout_migrate.py` (untouched-semantics witness)

Category: Producer recipes

- `agents/skills/done/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/maintenance/template-authoring.md` *(acknowledgment fixture only; read-only)*

Task 2 - Recipes name the sibling step:

- [x] Done Step 2 names the sibling requirement: given the gated-removal claims text, expects one added sentence stating the claims set names each claimed review record's `.stats.json` sibling and the gate refuses teardown while a worktree-side sibling would be destroyed, with no other Step 2 text changed and the prescribed-invocation pins intact. [class: IMPLEMENTATION_REQUIRED]
- [x] Plans Final Step names the sibling requirement: given the closeout paragraph of the plans skill's Final Step section, expects one added sentence stating the same sibling requirement, with no other Final Step text changed. [class: IMPLEMENTATION_REQUIRED]
- [x] Authoring payload acknowledgment: given the maintenance authoring payload's existing move step, expects it already names every review staging doc and `.stats.json` sidecar this task wrote, so that site is verified read-only and edited by no task. [class: REPOSITORY_TEST]

Category: Tests

- `scripts/test_worktree_closeout_migrate.py`

Task 3 - Fixtures and battery:

- [x] Destruction-refusal fixture: given a home with `r1.md` present (no sidecar), the sidecar present in the worktree staging home, and a claims file naming the record, expects gate-removal OUTCOME: fail naming the worktree-side sibling path. [class: REPOSITORY_TEST]
- [x] Label-line refusal fixture: given the same worktree/home shape driven by a plan label line citing the record and no claims file, expects the same sibling refusal through the exact-token arm. [class: REPOSITORY_TEST]
- [x] Pass fixtures: given the sidecar present at both the worktree staging home and the home (transferred), expects OUTCOME: pass; given the sidecar existing nowhere (the legacy sidecar-less record shape), expects OUTCOME: pass with no refusal. [class: REPOSITORY_TEST]
- [x] Sidecar-claims control: given a claims file naming the `.stats.json` sidecar itself (present at the home), expects it verifies as itself and derives nothing. [class: REPOSITORY_TEST]
- [x] Untouched-semantics control: given the existing suite run, expects all prior gate-removal fixtures green unchanged (their staged records carry no worktree-side siblings, so the arm never fires on them). [class: REPOSITORY_TEST]

Category: Riders (landing change, not execution scope)

- `docs/history/backlog/PLAN-PROMPTS.md` (landing prune rider, its own entry only)
- `docs/history/backlog/2026-10-13-worktree-closeout-claims-sidecar-siblings.md` (origin row; covered flip at landing)

Excluded with reasons:

- `scripts/validate_review_staging.py`; reason: the twin contract is the requirement source and stays unchanged; the gate only consumes its naming (`Path.with_suffix(".stats.json")`).
- `cmd_verify_records` in `scripts/worktree_closeout_migrate.py`; reason: advisory pre-check parity rejected in Assumptions; its plain-exit contract is a separate witnessed surface.
- A second completeness validator or claims ledger; reason: the machinery protocol prefers the smallest change inside the existing gate.
- Amending any existing suite fixture; reason: the destruction-conditioned arm never fires on records whose siblings exist nowhere, so every existing pass-shaped fixture stays green unchanged by design.

## Validation Commands

Run from the repository root. The venv python runs the suite when present; the bare fallback is acceptable when the venv is absent.

- `$HOME/.agents/venvs/ai-playbook-test/bin/python3 -m pytest scripts/test_worktree_closeout_migrate.py` (fallback when the venv is absent: `python3 -m pytest scripts/test_worktree_closeout_migrate.py`)
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-16-worktree-closeout-claim-sibling-completeness.md`
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh`
- `bash scripts/check-no-em-dash.sh touched`
- `bash scripts/check_maintenance_pins.sh`

## Disposition of migrated backlog items

The origin row `docs/history/backlog/2026-10-13-worktree-closeout-claims-sidecar-siblings.md` carries `Status: open` and is covered-flipped by this plan's landing rider, whose disposition preserves the machinery admission's pre-registered condition verbatim (a witnessed false refusal narrows the record grammar rather than removing the arm; removing the arm re-opens the witnessed loss and requires an operator decision recorded in the row). The PLAN-PROMPTS entry `worktree-closeout-claim-sibling-completeness` is pruned by the landing's own receipt. No other backlog rows are touched.
