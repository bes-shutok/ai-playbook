# Plan: P55 audit machinery deployment gaps and plans gate blind spots

Backlog origin: docs/history/backlog/2026-09-23-stale-validator-rejected-enum-deployment-gap.md (anchor; the four companion origins are listed with dispositions in "Origins and dispositions" below)
Driving force: code-quality + simplicity

## Terms

- **Deployment-gap signature**: done-skill wording that classifies a gate failure as a stale or missing runtime-home copy routed to a standard copy remedy, never to the investigate path or the recorded-stop exception; Task 1 adds the doc-registry gate's `**Stale-deployment signature:**` instance of it.
- **Runtime home**: `~/.ai-playbook/scripts/`, the deployed host copy of repo scripts; validator staleness is the origin-1 lag window (repo copy fixed, deployed copy lagging).
- **Docs-branch shadow**: the single orphan `docs` branch carrying gitignored LLM artifacts (`docs/reviews`, `docs/tmp`), synced by the docs-branch skill; the only durable copy of review records.
- **check-ignore gate**: the snapshot step's test (docs-branch SKILL.md Step 1) accepting a shadow candidate only when `git check-ignore -q` accepts it.
- **Count-gate pin**: an exact-count validation grep over a span; **joint simulation** runs a file's complete count-gate set against a temp copy carrying all prescribed insertions, instead of only the new gate against old spans.
- **Scope-classification probe**: `scope_classification_problem` in `scripts/plan_readiness.py`, the enforcement side of the classification-tag rule.

## Assumptions

- assume one plan covers all five origins; basis: the P55 authoring payload names them as one scope (standing pre-authorization, 2026-09-24).
- assume origin 3's scope is the docs-branch reviews-dir check-ignore silent drop: a shadow candidate that exists but fails `git check-ignore` is skipped without a word at both candidate filters, so lost ignore coverage silently drops review records from the shadow; basis: the payload text is the scope of record (no standalone backlog file exists) plus the 2026-09-24 probes: snapshot-step gate at `agents/skills/docs-branch/SKILL.md` (Step 1 block starting `SNAPSHOT_TMP=`, line ~106), `docs/reviews` ignored, `docs/history/reviews` NOT ignored on this host, the Step 2 `.gitignore` filter list anticipating both reviews spellings.
- assume origin 2 resolves no-change per its own Suggested fix (yagni; the trigger, a sixth consumer, does not exist); basis: the origin's Suggested fix text; inventory re-verified 2026-09-24 (five consumers plus the validator's state-vocabulary spellings).
- assume origin 5 lands both suggested sides (the SKILL.md first-line placement rule and the validator placement check); basis: the origin's Suggested fix (a)+(b) under the standing pre-authorization.
- assume the origin-5 validator check is a fail-loud problem reason, not a printed warning; basis: the probe family's `str | None` contract has no warning channel and the origin's "fails loud" wording; zero trips across the open plan corpus (2026-09-24 probe over `docs/plans/*.md` and `docs/plans/deferred/`; one archived plan under `docs/plans/completed/` carries the legacy wrapped-tag defect, which is out of gate scope because archived plans are immutable and never re-gated), so the check is regression-safe for every plan the readiness gate still evaluates.
- assume origin 4's sibling surface is review-plan SKILL.md Step 5 item 5; basis: the 2026-09-24 probe showing the testing lens (`agents/skills/review-agents/testing.md`) carries no fold-verification checklist, so the Step 5 amend list is the only sibling wording.
- assume origin 1 is a done-prose change with no validator code change; basis: the origin's Suggested fix; the deployed validator probed byte-identical to the repo copy on 2026-09-24, so the signature covers the next lag window, not a live one.

Decision points requiring a grill: origin-3 scope pinning (decision: pin the silent-drop gap from machinery probes; source: the payload text as scope of record plus the standing pre-authorization "accept all recommended options and suggestions", user directive 2026-09-24; affects: Task 2); origin-2 no-change disposition (decision: leave the scattered literals and record the disposition; source: the origin's own Suggested fix under the same standing pre-authorization, 2026-09-24; affects: the dispositions ledger); origin-5 fail-loud shape (decision: a misplaced tag returns a problem reason; source: the standing pre-authorization over the warning-versus-problem shapes, 2026-09-24; affects: Task 4); sibling-surface choice (decision: review-plan Step 5 item 5; source: the 2026-09-24 sibling probe under the same standing pre-authorization; affects: Task 3).

## Gist & Examples

TLDR: the audit gates stop failing silently, so stale-copy failures route to the copy remedy, a lost reviews-dir ignore rule names itself, count-gate pins re-simulate jointly, and a misplaced classification tag is reported as a placement.

Today the audit machinery fails in the quiet direction exactly where a loud failure is the point. A stale deployed validator prints `invalid state value` for the first real rejected row and done routes the operator to investigate the registry instead of the one-command copy remedy, while the same stale copy silently misses body edits under the rejected archives it predates. The docs-branch shadow, the only durable home of review records, skips a shadow candidate whose ignore coverage drifted without printing anything, so the records vanish from the next shadow sync with no trace. plans rule 36 simulates a new count gate against old spans but never the reverse, so a fold can leave an older count-1 anchor gate deterministically unsatisfiable (the origin's witnessed 3-occurrence flip) and the regression surfaces one review round later. And a classification tag wrapped onto a continuation line is invisible to the readiness parser, so a visually present tag classifies the item untagged and the operator chases a phantom. Example of the new shape: the docs-branch operator sees `shadow candidate 'docs/reviews' exists but is not gitignored (git check-ignore rejects it); NOT synced` with the exact remediation, and the readiness probe returns `classification tag on a non-checkbox line in Task 2; tags must sit on the item's first (checkbox-marker) line` instead of a misleading untagged verdict.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every origin's mechanism is verified by a probe or a RED-today gate recorded at authoring (2026-09-24), not by inheriting the origin text's claims.
- fail-loud consistency: no task adds a silent-skip path; the docs-branch change keeps the skip behavior and adds visibility only.
- regression safety: the validator placement check trips zero open plans (probed 2026-09-24 over `docs/plans/*.md` and `docs/plans/deferred/`) and the new test suite covers the backtick false-positive direction.
- hygiene: no em-dash in the plan bytes; the public-hygiene scan exits 0.

**Done when:**
- all task checkboxes are checked and the final validation block exits 0 end to end (`VALIDATION OK`).
- `PYTHONPATH=scripts python3 -m unittest scripts.test_plan_readiness` exits 0 (0 failures).
- the plan passes `python3 scripts/plan_readiness.py` on its final bytes with a ready=yes zero-blocking round.

**Ship when:**
- the next real stale-deploy event routes to the copy remedy through the new signature instead of the investigate path (operational witness; observed behavior, not repo-checkable) [class: OPERATIONS_FOLLOW_UP].
- the runtime-home validator redeploy stays a host-level op owned by the done skill's remedy; evidence owner: the operator session observing the failure; closure condition: sha256 match between the repo and deployed validator copies [class: OPERATIONS_FOLLOW_UP].

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/done/SKILL.md` (the doc-registry gate bullet only; all other content frozen)
- `agents/skills/docs-branch/SKILL.md` (the snapshot step's script block, the block starting `SNAPSHOT_TMP=` in Step 1, and its following prose note only; the Step 2 sync script and the restore leg are frozen)
- `agents/skills/plans/SKILL.md` (Validation Commands rule 36 and the Classification tag rule line only; all other content frozen)
- `agents/skills/review-plan/SKILL.md` (Step 5 amend list item 5 only; all other content frozen)
- `scripts/plan_readiness.py` (the `scope_classification_problem` function, its docstring, and any new module-level helper it needs; all other content frozen)

- `docs/plans/2026-09-24-p55-audit-deployment-gaps-gate-blind-spots.md` (the plan's own bytes; Task 5 gates them through `plan_readiness.py`)

**Tests:**
- `scripts/test_plan_readiness.py` *(new)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/check_plan_origins_closed.py`, `scripts/docs_branch_backlog_dedupe.py`, `scripts/docs_branch_plan_guard.py`, `scripts/done_sweep_gates_lib.py`, `scripts/doc_registry_validator.py`; reason: origin 2's yagni disposition keeps the scattered rejected-dir literals, and origin 1 prescribes no validator code change.
- Deployed runtime-home copies under `~/.ai-playbook/scripts/`; reason: host-level operational state owned by the done skill's copy remedy (Ship when), not repo content.
- `docs/plans/completed/` and `docs/plans/deferred/` content; reason: archived plans are immutable context.

## Design Invariants (CR Guard)

- Frozen regions: outside the regions named in Review Scope, the four skill files and `plan_readiness.py` are frozen for this plan; reject any review finding that touches them elsewhere.
- No new silent-skip path anywhere; the docs-branch snapshot keeps its skip semantics (a not-ignored candidate must never be force-staged: that would corrupt the docs branch's ignore contract) and gains only the loud warning.
- `scope_classification_problem` checks (a) untagged, (b) Ship-when-only class, and (c) vocabulary, plus the four-name vocabulary itself, keep their semantics; the placement check is additive and runs first within each task section because it explains why an item reads untagged.
- plans rule numbering is cross-referenced by number elsewhere (rules 18-20, 22, 36); rule 36 extends in place and nothing renumbers.
- Every pinned validation span in this plan is a single-occurrence obligation in its target; every fold re-runs the rule-22 mechanical audit (pin extraction, exactly-once verification, `bash -n` over this block) in the same edit.

## Origins and dispositions

| Origin (basename under docs/history/backlog/) | Status at authoring | Disposition |
|---|---|---|
| `2026-09-23-stale-validator-rejected-enum-deployment-gap` | open (anchor) | Implement the stale-deployment signature: Task 1. |
| `2026-09-23-rejected-archive-dir-hardcoded-consumers` | open | Resolve no-change (yagni per the origin's own Suggested fix); the inventory and trigger stand as written; routed done at plan completion with no code edit. |
| docs-branch reviews-dir check-ignore (no standalone file; payload text is the scope of record) | open | Implement the loud-warning arm: Task 2 (payload origin 3). |
| `2026-09-23-plan-rule36-reverse-duplicate-simulation` | open | Implement the joint-direction duty: Task 3 (payload origin 4). |
| `2026-09-23-plans-classification-tag-continuation-line-invisible` | open | Implement both sides: Task 4 (payload origin 5). |

## Validation Commands

```bash
#!/usr/bin/env bash
# Run from the repository root. Exit 0 = every gate holds. Each gate fails loud.
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1

# G1: the doc-registry stale-deployment signature exists with its copy remedy (Task 1).
grep -qF "Stale-deployment signature" agents/skills/done/SKILL.md \
  || { echo "G1 FAIL: stale-deployment signature absent from done SKILL.md"; exit 1; }
grep -qF "not a registry defect" agents/skills/done/SKILL.md \
  || { echo "G1 FAIL: stale-deployment routing clause absent"; exit 1; }
grep -qF "cp scripts/doc_registry_validator.py ~/.ai-playbook/scripts/" agents/skills/done/SKILL.md \
  || { echo "G1 FAIL: validator copy remedy absent"; exit 1; }

# G2: the docs-branch snapshot skip is loud (warning text, prose anchor, stderr routing) and the edited snapshot block still parses (Task 2).
grep -qF "exists but is not gitignored" agents/skills/docs-branch/SKILL.md \
  || { echo "G2 FAIL: check-ignore warning arm absent from the snapshot block"; exit 1; }
grep -qF "never a silent skip" agents/skills/docs-branch/SKILL.md \
  || { echo "G2 FAIL: loud-skip prose anchor absent"; exit 1; }
G2_BT="$(printf '\140\140\140')"
G2_TMP="$(mktemp -d)" || exit 1
awk -v bt="$G2_BT" \
  '$0 == bt "bash" {f=1; buf=""; next} $0 == bt && f {if (buf ~ /SNAPSHOT_TMP=/) {printf "%s", buf; exit} f=0; next} f {buf = buf $0 "\n"}' \
  agents/skills/docs-branch/SKILL.md > "$G2_TMP/step0.sh"
bash -n "$G2_TMP/step0.sh" \
  || { echo "G2 FAIL: snapshot block has a shell syntax error"; rm -rf "$G2_TMP"; exit 1; }
grep -qF ">&2" "$G2_TMP/step0.sh" \
  || { echo "G2 FAIL: warning arm does not route to stderr"; rm -rf "$G2_TMP"; exit 1; }
rm -rf "$G2_TMP"

# G3: rule 36 names the joint direction and review-plan Step 5 carries it into fold verification (Task 3).
test "$(grep -cF 'complete count-gate set' agents/skills/plans/SKILL.md)" -eq 1 \
  || { echo "G3 FAIL: joint-simulation clause missing or duplicated in rule 36"; exit 1; }
grep -qF "verifying every expected count simultaneously" agents/skills/plans/SKILL.md \
  || { echo "G3 FAIL: joint-simulation obligation absent from rule 36"; exit 1; }
grep -qF "joint re-simulation" agents/skills/review-plan/SKILL.md \
  || { echo "G3 FAIL: review-plan Step 5 sibling wording absent"; exit 1; }

# G4: the classification tag rule names the first-line placement and the validator enforces it (Task 4).
test "$(grep -cF 'FIRST (checkbox-marker) line' agents/skills/plans/SKILL.md)" -eq 1 \
  || { echo "G4 FAIL: first-line placement rule missing or duplicated"; exit 1; }
grep -qF "non-checkbox line" scripts/plan_readiness.py \
  || { echo "G4 FAIL: placement problem absent from the scope-classification probe"; exit 1; }
PYTHONPATH=scripts python3 -m unittest scripts.test_plan_readiness 2>&1 | grep -q "^OK" \
  || { echo "G4 FAIL: plan_readiness test suite not green"; exit 1; }

# G5: mechanical suites and repo hygiene (final state).
PYTHONPATH=scripts python3 -m unittest scripts.test_plan_readiness 2>&1 | grep -q "^OK" \
  || { echo "G5 FAIL: plan_readiness suite"; exit 1; }
bash scripts/scan-public-hygiene.sh \
  || { echo "G5 FAIL: hygiene scan"; exit 1; }
echo "VALIDATION OK"
```

### Task 1: done doc-registry gate gains the stale-deployment signature

Files:
- `agents/skills/done/SKILL.md`

- [x] In the doc-registry gate bullet, immediately after the "An absent validator is fail-open" sentence, insert the sentence opening `**Stale-deployment signature:**` and continuing: a doc-registry failure printing `invalid state value` on a state value the repo-copy validator accepts is a stale runtime-home validator, not a registry defect: redeploy with `cp scripts/doc_registry_validator.py ~/.ai-playbook/scripts/` and re-run the gate; the same redeploy covers the silent direction (a pre-fix deployed copy lacks the rejected-archive immutability and licensed-transition coverage, so a body edit or deletion under a rejected archive passes the gate silently until redeploy); never route a stale deployment to the investigate path or the recorded-stop exception [class: IMPLEMENTATION_REQUIRED]
- [x] Authoring-time RED evidence (recorded 2026-09-24): all three G1 pins absent from done SKILL.md (0 hits); the validator's real failure print is `HARD invalid state value '<state>' in registry row` (scripts/doc_registry_validator.py line ~733), so the signature keys on text the validator actually emits; the deployed copy probed byte-identical today, so the signature covers the next lag window [class: REPOSITORY_TEST]
- [x] Run validation gates G1; expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `skills: done doc-registry gate gains the stale-deployment signature (P55 origin 1)` [class: REPOSITORY_TEST]

### Task 2: docs-branch snapshot skip goes loud on lost check-ignore coverage

Files:
- `agents/skills/docs-branch/SKILL.md`

- [x] In the snapshot step's candidate loop only (docs-branch SKILL.md Step 1, the block starting `SNAPSHOT_TMP=$(mktemp -d)`), add an elif arm to the check-ignore gate: when the candidate path exists but `git check-ignore -q` rejects it AND `git ls-files --error-unmatch` also rejects it (the warning arm fires only for disk-only, untracked content; an unignored but git-tracked candidate is product content and stays silently out of the shadow by design, ignore-else-track), echo to stderr: `docs-branch: shadow candidate '$clean' exists but is not gitignored (git check-ignore rejects it); NOT synced to the docs branch shadow. Add the ignore rule to .gitignore or correct the facts reviews_dir/tmp_dir key, then re-run.`; the skip behavior itself is unchanged (a not-ignored candidate is never staged) [class: IMPLEMENTATION_REQUIRED]
- [x] Immediately after that script block (before the Step 1.5 heading), add one prose sentence: a candidate that exists but fails the check-ignore gate is skipped with the loud warning above, never a silent skip, because the reviews-dir shadow is the only durable copy of review records and lost ignore coverage must name itself, while an unignored but git-tracked candidate stays silently out of the shadow by design (ignore-else-track) [class: IMPLEMENTATION_REQUIRED]
- [x] The Step 2 sync script and the restore leg stay byte-identical; their independent candidate filter keeps its ignore-else-track semantics [class: REPOSITORY_TEST]
- [x] Authoring-time RED evidence (recorded 2026-09-24): both G2 pins absent (0 hits); probe witnesses the gap today: `docs/reviews` is ignored while `docs/history/reviews` is NOT, so a review record written under the latter would vanish from the shadow without a word [class: REPOSITORY_TEST]
- [x] Run validation gates G2 (including the `bash -n` parse of the extracted snapshot block); expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `skills: docs-branch shadow candidate skip goes loud on lost check-ignore coverage (P55 origin 3)` [class: REPOSITORY_TEST]

### Task 3: plans rule 36 joint count-gate simulation and review-plan fold wording

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-plan/SKILL.md`

- [x] Extend Validation Commands rule 36 in place (no renumbering) with the joint-direction duty: the duplicate simulation also runs in the joint direction, so a fold that adds or moves a count obligation on a file re-simulates that file's complete count-gate set (the pre-existing gates plus the new one) against a temp copy carrying ALL prescribed insertions for that file, verifying every expected count simultaneously in the same mechanical-audit pass rule 22 mandates, because the single-direction witness is not sufficient (the origin's witness: a fold's new count-2 gate over a strict superstring span left the pre-existing count-1 anchor gate deterministically unsatisfiable at three post-insertion occurrences, surfacing one review round later) [class: IMPLEMENTATION_REQUIRED]
- [x] Replace review-plan SKILL.md Step 5 amend item 5 with the joint wording: add verification commands for each folded behavioral finding, and when the fold adds or moves a count obligation on a file, its verification includes the joint re-simulation of that file's complete count-gate set over a temp copy carrying all prescribed insertions (plans Validation Commands rule 36) [class: IMPLEMENTATION_REQUIRED]
- [x] Authoring-time joint-simulation witness: build a temp file carrying one anchor bullet plus two sibling join entries that all contain the anchor phrase; run gate A (`count 1` over the bare anchor span) and gate B (`count 2` over the superstring span) against it and record that the single-direction simulation (B alone) passes while the joint simulation (A and B) fails with A reading 3; remove the temp file afterward [class: REPOSITORY_TEST]
- [x] Run validation gates G3; expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `skills: plans rule 36 joint count-gate simulation and review-plan fold wording (P55 origin 4)` [class: REPOSITORY_TEST]

### Task 4: classification tag placement made visible end to end

Files:
- `agents/skills/plans/SKILL.md`
- `scripts/plan_readiness.py`
- `scripts/test_plan_readiness.py` *(new)*

- [x] Write `scripts/test_plan_readiness.py` first, unittest style run via `PYTHONPATH=scripts python3 -m unittest scripts.test_plan_readiness`, importing `scope_classification_problem` from `plan_readiness`, with four fixture tests over minimal task-section texts: `test_continuation_line_tag_reports_placement` given a wrapped checklist item whose `[class: IMPLEMENTATION_REQUIRED]` tag sits on the second (continuation) line, expects a reason containing `non-checkbox line` and the task label; `test_first_line_tag_clears` given the same item with the tag moved onto the checkbox-marker line, expects None; `test_backticked_tag_mention_in_prose_clears` given a properly tagged item set plus a prose line inside the task section quoting the tag syntax inside backticks, expects None (the false-positive guard); `test_untagged_item_still_fails` given an item with no tag anywhere, expects a reason containing `carries no` (the fail-closed regression guard); run the suite and record RED: the placement test fails today because the probe returns the misleading untagged reason instead [class: REPOSITORY_TEST]
- [x] Extend `scope_classification_problem` with the placement check, scanned per task section before the per-item loop: any non-blank line that is not a checkbox item and carries a `[class: ...]` token outside backtick spans returns `classification tag on a non-checkbox line in {label}; tags must sit on the item's first (checkbox-marker) line: {line!r}`; update the function docstring's checks list with the new check and its precedence rationale (it explains why an item reads untagged); keep checks (a), (b), (c) and the vocabulary unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Run the suite; expect GREEN with all four tests passing [class: REPOSITORY_TEST]
- [x] In the plans SKILL.md Classification tag rule line, after the `[class: REPOSITORY_TEST]` sentence, insert: the tag sits on the item's FIRST (checkbox-marker) line; a multi-line (wrapped) item never carries the tag on a continuation line, where the readiness parser cannot see it, and `scope_classification_problem` reports the placement instead of classifying the item untagged [class: IMPLEMENTATION_REQUIRED]
- [x] Authoring-time regression probe (recorded 2026-09-24): the placement scan over the open plan corpus (`docs/plans/*.md`, `docs/plans/deferred/`) returns zero trips, so the new check cannot strand a gated plan's readiness gate; one archived plan under `docs/plans/completed/` carries the legacy wrapped-tag defect and is out of gate scope (archived plans are immutable, never re-gated) [class: REPOSITORY_TEST]
- [x] Run validation gates G4; expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `scripts+skills: classification tag placement made visible end to end (P55 origin 5)` [class: REPOSITORY_TEST]

### Task 5: closeout validation

Files:
- `docs/plans/2026-09-24-p55-audit-deployment-gaps-gate-blind-spots.md`

- [x] Run the full validation block end to end; expect `VALIDATION OK` [class: REPOSITORY_TEST]
- [x] Run `python3 scripts/plan_readiness.py docs/plans/2026-09-24-p55-audit-deployment-gaps-gate-blind-spots.md`; expect exit 0 on the final digest with the latest ready round's sidecar [class: REPOSITORY_TEST]
- [x] Confirm the four origin backlog items remain in place under `docs/history/backlog/` while the plan is open (the completion step routes them per the dispositions table) [class: REPOSITORY_TEST]
