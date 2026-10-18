# Review-staging soft runs stop claiming pass, and the validator owns counts parity

Slug: review-staging-outcome-and-counts-contract
Budget: 1.5h authoring; declared execution budget 2h (one label-derivation change + four parity arms + two contract sentences + fixture battery)

Driving force: reliability (off the five driving principles: truthful machine verdicts and validator-owned counts parity answer witnessed defects on live gate-consumed surfaces, and park-triage would not take it because both origins name failures the current gates pass through)

## Backlog origins (scope of record)

- docs/history/backlog/2026-10-09-review-staging-soft-mode-outcome-pass-on-fail.md (the pass-on-fail trap; probe witness with the exact tail line)
- docs/history/backlog/2026-10-09-review-staging-counts-parity-validation.md (the counts drift gap; the 13-vs-12 memory-index-consolidation r2 witness)

## Terms

- Soft run: a `validate_review_staging.py` invocation with neither `--hard` nor `--preflight`; today it never gates (exit 0) and ends `OUTCOME: pass` even when the record failed.
- Truthful label: the final `OUTCOME:` label and the JSON `outcome` field derive from the validation result (`result.ok`), not from the exit code.
- Counts parity: every declared counts surface (record Markdown Combined line, per-severity Counts table, sidecar `counts`, per-worker Findings lists, overflow count) equals the record's itemized findings rows.

## Why

Two witnessed defects share the validator's reporting tail. (1) The plain-run tail keys both the label and the JSON outcome on the exit code (`OUTCOME_LABELS[exit_code]`, exit forced 0 for non-hard runs), so a soft run over a record with 16 schema errors prints the errors, prints `FAIL:`, and still ends `OUTCOME: pass` with JSON `outcome: pass` (the origin's probe, 2026-10-09). A contract-literal caller gating on the label accepts a failing record. (2) The validator reads declared counts as inputs but cross-checks almost none of them: only `workers_launched` vs panel rows and `counts.staged_findings` vs sidecar findings exist today, so a Combined-line/per-severity/per-worker/overflow drift survives every mechanical check until the next round's panel reads the record (the 13-claimed/12-itemized r2 slip; review-plan's Step 4 gate carries an interim manual reconciliation paragraph as the incumbent).

## Gist & Examples

TLDR: a findings-bearing soft run ends `OUTCOME: fail` (exit stays 0, JSON outcome truthful) and the validator refuses records whose declared counts disagree with their itemized rows, retiring review-plan's manual reconciliation paragraph (reliability).

Before: soft run over a broken record: `FAIL:` then `OUTCOME: pass`; a counts-drifted record passes the round-close gate and is caught only by the next round's panel.

After: the same soft run ends `OUTCOME: fail` with exit 0 (soft runs report, they never gate; the label is truthful and the contract says so); a counts-drifted record fails validation naming the mismatched surface and both values; `--hard` and `--preflight` behavior stay byte-identical.

## Outcome

- The soft-mode tail derives the final label and the JSON `outcome` field from `result.ok`; valid-record soft runs keep `OUTCOME: pass`; findings-bearing soft runs end `OUTCOME: fail` with exit 0 retained; `--hard` grading and `--preflight` behavior stay byte-identical on conforming and unchanged shapes (the parity arms surface only on drifted records); the in-file selftest arm flips to pin the fail-label-plus-exit-0 pair and the clean-soft pass.
- `scripts/OUTCOME_CONTRACT.md` gains the report-only reading rule for the soft plain run's findings-class pass/fail tail: that tail's exit code never gates (it reports), its final label always carries the verdict, and callers that gate on a result must invoke the hard form; the tool-error and corrections exits keep their existing meanings.
- The reading rule names the soft plain run and never claims preflight: preflight keeps its documented inventory posture where findings never move its exit or its label, so the contract sentence stays true for every non-hard form; the validator usage text and the review-staging step text say the same in their own voices.
- The validator's counts validation gains the missing parity arms: per-severity staged sums equal the itemized rows at that severity, each panel worker's Findings list (built in the legacy panel-table shape carrying the Findings column) equals the workers fields on that worker's itemized findings, the overflow count equals the itemized overflow rows, and the record Markdown Combined line equals the sidecar `counts` on the quantities with sidecar twins (staged, workers); every refusal names the mismatched surface and both values; existing parity arms stay.
- The review-plan Step 4 manual reconciliation paragraph is replaced by a one-line statement that the validator owns counts parity (the incumbent retired in the same change that promotes the check).
- Fixtures: one mismatch witness per new parity surface, with the per-severity witness pinned to the same-total/different-split drift shape the surface exists to catch, the soft fail-label shape, a soft --json fixture asserting the JSON outcome field reads fail at exit 0, hard and preflight unchanged pins, and a conforming-corpus compatibility pass.

Gate delta: adds one refusal family to an existing guard-bearing validator (counts parity) with the incident pre-registered (the row's 13-vs-12 witness) and retires the incumbent manual reconciliation step in the same change; changes one label-derivation line plus the JSON field on the soft path (fix-class, origin-cited probe); no new gate files, no schema field, no caller migration; `--preflight` keeps its documented report-only inventory posture; no task pauses dispatch or later work.

Admission fields: expected catch frequency, the witnessed counts-drift class (the 13-vs-12 r2 slip and the soft-run probe); false-positive cost, a false parity refusal blocks a round close until the record is fixed and is answered by fixing the record, never by editing the gate; absent declared surfaces are skipped by the parity arms because schema coverage governs presence, not parity; review date 2027-01-16, with the pre-registered removal condition that the arms demote to warning-only if no true catch lands by that date; the compatibility acceptance runs the conforming corpus set from the origins' witnesses, not a single record.

## Assumptions

- Label/exit pairing: the contract's "exit code and final OUTCOME: line carry the outcome together" is amended by an explicit report-only rule for the soft plain run rather than silently decoupled: the exit keeps meaning "the run gated" (hard) or "the run reported" (the soft plain run's findings tail), the label always carries the verdict. Basis: the origin's suggested direction names exactly this contract-level declaration as the sanctioned shape, and the entry forbids silent decoupling.
- Preflight is out of the label change: its docstring documents findings-never-move-exit as its inventory role, and its callers read the inventory, not a verdict. Basis: the entry's separate-treatment instruction.
- The parity check keys on the itemized findings rows as the single derived source; declared surfaces are witnesses that must agree with it, never a second source of truth. Basis: the origin's canonical-source instruction.
- The two existing parity arms (workers_launched, staged_findings-vs-sidecar) stay byte-identical; the new arms extend the same validation site. Basis: worktree read of the validator's counts block.

Decision points requiring a grill: none remain: the origin rows adjudicate truthful-label-plus-explicit-contract-rule over label/exit-coupled soft runs (the probe shows the coupled shape accepts failing records) and over exit-1 soft runs (that is hard mode; soft runs keep their non-gating process semantics), and validator-owned parity over a second manual pass (the incumbent paragraph is the drift the row witnessed).

## Standing constraints

- Never push to origin; stage by explicit path only; never amend a commit reachable from main.
- The hygiene scan (exit 0) runs before every commit; no em-dashes and no absolute personal home directory paths in committed files.
- Bounded repair only: never edit a gate or validator mid-lane to unblock the lane.
- Preserve: `--hard` grading, `--preflight` inventory semantics, the four existing output channels (valid record, unreadable input, usage error, preflight inventory), the two existing parity arms, and the callers' current invocation forms.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the label derivation reads exactly one source (`result.ok`); every new parity arm names the mismatched surface and both values; no existing refusal text changes.
- Preservation: `--hard`, `--preflight`, valid-soft, unreadable-input, and usage-error emissions stay byte-identical on the fixture battery.
- Docs truthfulness: the contract, usage, and step texts describe the shipped semantics and no others.

**Done when:**
- The validator selftest passes with the new arms (soft fail-label, clean-soft pass, hard pin, preflight pin, one mismatch fixture per parity surface).
- The conforming corpus set from the primary reviews home (`.ai-playbook/reviews`) still validates unchanged (compatibility pass recorded in the run log).
- review-plan's Step 4 carries the replacement statement; hygiene scan exit 0; no em-dashes in touched files.

**Ship when:**
- A soft run over a broken record ends `OUTCOME: fail`, and a counts-drifted record is refused naming the surface, on the origin witnesses' shapes.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/validate_review_staging.py` (the soft-path label derivation, the JSON outcome field on that path, the counts-parity arms, the in-file selftest arms)

**Docs:**
- `scripts/OUTCOME_CONTRACT.md` (the report-only reading rule)
- `agents/skills/review-plan/SKILL.md` (the Step 4 reconciliation paragraph replacement)
- `agents/skills/review-staging/SKILL.md` and the validator usage text, where they describe soft-run semantics

**Tests:**
- the validator's in-file selftest corpus (new arms and fixtures)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py` and the downstream gates' consumption of the verdict (they already read hard or sidecar fields; no caller migration).
- The preflight inventory's semantics and output channels (documented, unchanged).
- The corrections arm and cap-closure shapes (distinct validator surfaces with their own rows).

## Validation Commands

Run from the repository root. The venv python runs the suite when present; the bare fallback is acceptable when the venv is absent.

- `python3 scripts/validate_review_staging.py --selftest` (exit 0; the in-file suite with the new arms)
- `$HOME/.agents/venvs/ai-playbook-test/bin/python3 -m pytest scripts/test_review_landing_receipt.py` (fallback: `python3 -m pytest scripts/test_review_landing_receipt.py`; the downstream receipt consumer must stay green)
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-16-review-staging-outcome-and-counts-contract.md`
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh`
- `bash scripts/check-no-em-dash.sh touched`

## Disposition of migrated backlog items

- 2026-10-09-review-staging-soft-mode-outcome-pass-on-fail: covered by this landing (the soft tail derives the label from the result; the contract carries the reading rule; the landing commit is the witness).
- 2026-10-09-review-staging-counts-parity-validation: covered by this landing (the four parity arms land; the incumbent manual reconciliation paragraph retires; the landing commit is the witness).
