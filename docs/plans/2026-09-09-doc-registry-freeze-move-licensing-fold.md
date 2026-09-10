# Plan: Fold successor-row freeze-move licensing into the doc-ownership plan

Origin backlog: `docs/history/backlog/2026-09-09-doc-registry-freeze-move-licensing.md` (plan-review r8 Low, plausible-edge, hypothesis confidence, on the related plan at digest 33bf86f3).

Related plan: `docs/plans/2026-09-08-doc-ownership-lifecycle.md` (certified r8, not yet executed).

## Terms

- **Target plan**: `docs/plans/2026-09-08-doc-ownership-lifecycle.md`, the certified plan this fold amends before its execution.
- **Ownership registry**: one central Layer 2 file mapping document identity to SOT status, archive location, aliases, and successor relations; `docs/maintenance/document-registry.md` by default (target plan Terms).
- **Registry validator**: `scripts/doc_registry_validator.py`, created by the target plan's Task 1 at execution; subcommands `validate`, `check-writes`, `inventory` plus a `--selftest` mode.
- **check-writes**: validator subcommand that gates changed paths against completed-history immutability; input channels: paths as argv, a path list on stdin (`--stdin`), or `git diff --name-only` output (`--diff`).
- **Corruption-override row**: registry row whose audit note licenses an in-place factual fix to a completed-history artifact (ADR-0001 semantics); today the only licensed write shape in the target plan's check-writes contract.
- **Successor row**: registry row carrying a successor/`superseded_by` relation with date and reason; licenses a freeze move, not an in-place edit.
- **Freeze move**: archive `git mv` of a completed-history file plus its successor registry row (the lifecycle move the target plan itself prescribes).
- **Skill-gate marker**: consent marker per `agents/hooks/skill-gate/README.md` Marker WRITE RECIPE (plans class); refresh before every plan-file write.
- **Session key**: empty-after-strip session id becomes literal `no-session`; otherwise `sha1(value)[:16]` hex.

## Assumptions

- assume the fold edits only the two pinned Task 1 spans of the target plan (the fixture-contract checklist line and the check-writes implement bullet); every other line of the target plan is frozen for this plan; basis: the backlog Scope line ("`scripts/doc_registry_validator.py` (Task 1 of the doc-ownership-lifecycle plan) and the Task 1 fixture contract").
- assume the fold is Markdown-only: the validator script does not exist yet and gets implemented when the target plan executes with the folded fixture contract; basis: authoring probe 2026-09-09 (no `scripts/doc_registry_validator.py` on disk).
- assume amending the certified target plan supersedes its r8 digest, so Task 2 runs the fresh review round that re-binds the digest; the target plan's later execution would fail the readiness gate on a stale digest otherwise; basis: the r8 sidecar `source_digest` 33bf86f3 bound to the pre-fold bytes plus the plans digest-binding rules.
- assume the fresh round runs focused (blind correctness-completeness probe plus the testing and contract-docs workers, the fold-affected domains), matching the target plan's own r8 focused precedent and the post-fold re-probe rules; escalation to the full panel follows review-panel-selection when a round reports blocking; basis: plans review-loop rules 3 and 4.
- assume the two straggler backlog items named by the authoring triage stay open and untouched (re-queue): both are already claimed by the open plan `docs/plans/2026-09-07-straggler-wording-pins.md` (still under `{plans_dir}`, not in `{plans_completed_dir}`), and the telemetry fixes have not landed (`scripts/review_usage_capture.py:200` still replaces every home occurrence); basis: the triage's verify-and-archive-or-re-queue rule plus authoring probes 2026-09-09.
- assume the origin backlog item stays in place under `{backlog_dir}` while this plan is open and moves to `{backlog_completed_dir}` with `Status: done` in this plan's completion pass; basis: plans Plan Lifecycle.

Decision points requiring a grill: none remain.

## Gist & Examples

**What changes.** The target plan's Task 1 fixture contract gains one fixture and one implement-bullet clause so `check-writes` licenses a legitimate freeze move out of a completed-history dir when the moved path's registry row carries a successor/superseded relation (date and reason), and so a declared out-of-scope first cut is recorded in the validator usage text instead of leaving the behavior unpinned. The amended plan is then re-certified at a fresh digest by one focused review round, so its later execution passes the readiness gate with the folded contract.

**Why.** The backlog item (plan-review r8 Low on the target plan) found the check-writes contract pins only the ADR-0001 corruption-override row as a write license under completed-history paths. A freeze move (archive `git mv` plus its successor registry row, per the target plan's own lifecycle) also produces a path change the validator must rule on, but no fixture pins that licensing shape. Today only the `--diff` channel observes staged moves at all: the argv and stdin channels see post-move paths that simply look like additions, which is what keeps the gap Low.

**Before (today).** Executing the target plan as certified: a staged move of a file out of an immutable dir shows up on `--diff` and hard-fails unless the registry row carries an audit-noted corruption override. A legitimate freeze move with a proper successor row has no licensed path in the contract, and an implementer who defers successor-row licensing for a first cut has no prescribed place to record that decision.

**After (this plan).** The Task 1 fixture list carries `test_check_writes_successor_row_licenses_move`: a staged move out of an immutable dir whose moved-path registry row carries a successor/superseded relation (date and reason) exits 0, and the same move without such a row exits 1. The implement bullet names the successor-row license, its `--diff`-only observability, and the usage-text fallback for a declared out-of-scope first cut. One fresh focused round re-certifies the amended plan at the new digest.

**Edge cases.** The corruption-override license (in-place factual fix) and the successor-row license (path change) stay distinct contract shapes; the fixture text names the distinction so the two cannot blur. Moves that never leave an immutable dir are unaffected. This plan adds no execution obligations beyond the target plan's own: the licensing behavior itself is implemented when the target plan executes.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the folded contract matches the backlog's suggested fix in substance (fixture name `test_check_writes_successor_row_licenses_move`; exit 0 with a successor/superseded relation row, exit 1 without; usage-text fallback for a declared out-of-scope first cut), and the corruption-override license stays verbatim alongside it.
- digest integrity: one fresh round on the post-fold digest reports ready=yes with zero unresolved blocking; its sidecar `source_digest` equals the amended plan's sha256; `python3 scripts/plan_readiness.py` exits 0 on the amended plan.
- immutability: the fold edits exactly the two pinned spans; `git diff -U0` over the target plan shows the two span insertions and no other line; the target plan's Validation Commands block stays byte-identical.
- hygiene: no em-dash in changed prose; `bash scripts/check-no-em-dash.sh file` exits 0 on both changed Markdown files; the public hygiene scan exits 0.

**Done when:**
- the two pinned spans exist in the target plan exactly as prescribed (each distinctive pin matching exactly once);
- the latest round artifact and its version-1 sidecar exist for the amended plan with `ready=yes` and zero unresolved blocking findings;
- `python3 scripts/plan_readiness.py docs/plans/2026-09-08-doc-ownership-lifecycle.md` exits 0;
- the Validation Commands block below exits 0 end to end.

**Ship when:**
- (none; all work is repository-local Markdown edits and review artifacts; the licensing implementation lands when the target plan executes with the folded contract)

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Documentation:**
- `docs/plans/2026-09-08-doc-ownership-lifecycle.md` (only: the Task 1 fixture-contract checklist line and the Task 1 implement bullet, at the two pinned spans; every other line frozen; reject any review finding that touches frozen lines)
- `docs/reviews/2026-09-09-plan-review-doc-ownership-lifecycle-r9.md` *(new)* and `docs/reviews/2026-09-09-plan-review-doc-ownership-lifecycle-r9.stats.json` *(new)* (round numbering continues r10, r11, ... when a fold forces another round; the exit gate always reads the latest round)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/doc_registry_validator.py`; reason: created by the target plan's own execution, not by this fold.
- `docs/plans/2026-09-07-straggler-wording-pins.md` and the straggler backlog files `docs/history/backlog/2026-09-06-prose-sweep-fold5-pin-gap.md` and `docs/history/backlog/2026-09-07-token-telemetry-r5-residuals.md`; reason: verified re-queue at authoring (claimed by that open plan, fixes not landed); untouched by this plan.
- `docs/history/backlog/2026-09-09-doc-registry-freeze-move-licensing.md` during execution; reason: it moves to `{backlog_completed_dir}` in this plan's completion pass, not by a task.

## Design Invariants (CR Guard)

- The corruption-override license (ADR-0001 audit-noted row, in-place write) is preserved verbatim; the successor-row license is purely additive and must never replace or blur it.
- Only the two pinned Task 1 spans of the target plan may change; its Validation Commands block, Review Scope, and every other line are frozen for this plan.
- This plan never executes the target plan, never creates or edits `scripts/doc_registry_validator.py`, and never touches the baseline-recording mechanism of the target plan's Task 1 (that item runs at that plan's own execution).
- Push, review, and user-approval authorization for the target plan's later execution are unchanged; execution branching follows the execute-plan skill's normal Phase 0 setup (backlog non-goal).

## Validation Commands

```bash
set -euo pipefail
TARGET_DOC="docs/plans/2026-09-08-doc-ownership-lifecycle.md"
test -f "$TARGET_DOC" || { echo 'FAIL: target plan missing'; exit 1; }

# Fold pins: each obligation gets its own dedicated probe against the target plan, count-pinned to exactly once
test "$(grep -cF 'test_check_writes_successor_row_licenses_move' "$TARGET_DOC")" -eq 1 || { echo 'FAIL: successor-row fixture pin missing or duplicated'; exit 1; }
test "$(grep -cF 'successor/superseded relation with date and reason' "$TARGET_DOC")" -eq 1 || { echo 'FAIL: successor-row relation clause missing or duplicated'; exit 1; }
test "$(grep -cF 'usage text instead of leaving the behavior unpinned' "$TARGET_DOC")" -eq 1 || { echo 'FAIL: usage-text fallback clause missing or duplicated'; exit 1; }
test "$(grep -cF 'argv and stdin channels see post-move paths' "$TARGET_DOC")" -eq 1 || { echo 'FAIL: diff-only observability clause missing or duplicated'; exit 1; }

# No-ambiguity anchors: the corruption-override license survives verbatim beside the successor-row license
grep -qF 'test_immutable_write_override_passes' "$TARGET_DOC" || { echo 'FAIL: corruption-override fixture lost'; exit 1; }
grep -qF 'audit-noted override row' "$TARGET_DOC" || { echo 'FAIL: override-row license clause lost'; exit 1; }

# Digest-bound readiness on the amended plan (latest round verdict, blocking count, sidecar digest binding)
python3 scripts/plan_readiness.py "$TARGET_DOC" || { echo 'FAIL: readiness gate'; exit 1; }

# Format gates over this plan's changed Markdown (the target-plan scan is whole-file by design:
# the file carries zero em-dash characters today, so no frozen region can fail it)
bash scripts/check-no-em-dash.sh file "$TARGET_DOC" docs/plans/2026-09-09-doc-registry-freeze-move-licensing-fold.md || { echo 'FAIL: em dash'; exit 1; }
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh || { echo 'FAIL: hygiene scan'; exit 1; }
```

Authoring-time record (2026-09-09, against the pre-edit tree): the four fold pins each returned 0 (RED-today, spans absent), the three no-ambiguity anchors each returned exactly 1, the target plan's sha256 equals the r8 sidecar `source_digest` 33bf86f3 (no out-of-process edits), the target plan carries zero em-dash characters, the public hygiene scan exited 0 (PASS), and `bash -n` over this plan's Validation Commands extract exits 0. The pins flip green exactly when Task 1 lands.

### Task 1: Fold the successor-row licensing contract into the target plan's Task 1

Files:
- `docs/plans/2026-09-08-doc-ownership-lifecycle.md`

- [ ] Record the fold base and pre-edit probe → expect RED: `FOLD_BASE="$(git rev-parse HEAD)"`, then `grep -cF 'test_check_writes_successor_row_licenses_move' docs/plans/2026-09-08-doc-ownership-lifecycle.md` returns 0 (span absent today); refresh the plans-class skill-gate marker per `agents/hooks/skill-gate/README.md` Marker WRITE RECIPE (plans class) before the edit (`SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"`, then `python3 ~/.ai-playbook/scripts/skill_gate.py --write-marker [--session-id "$SID"]`); abort loudly if the marker write fails.
- [ ] Span A edit: in the Task 1 fixture-contract checklist line, insert immediately after the `test_check_writes_diff_channel` sentence and before the `test_unknown_flag_fails_closed` sentence, exactly this text:
  "`test_check_writes_successor_row_licenses_move`; given a staged move out of an immutable dir whose registry row for the moved path carries a successor/superseded relation with date and reason, `check-writes --diff` expects exit 0 (the successor row licenses the freeze move), and the same move with no such row expects exit 1; distinct from the corruption-override license, which is the audit-noted override row licensing an in-place write."
- [ ] Span B edit: in the Task 1 implement bullet, extend the `check-writes` contract immediately after the clause `override = registry row audit note` with, exactly this text:
  "; a staged move out of an immutable dir is licensed by the moved path's registry row carrying a successor/superseded relation (date and reason) and is observable only on the --diff channel (argv and stdin channels see post-move paths); if successor-row licensing is out of scope for the first cut, record the decision in the validator's usage text instead of leaving the behavior unpinned"
- [ ] Post-edit mechanical audit → expect GREEN: `git diff -U0 "$FOLD_BASE" -- docs/plans/2026-09-08-doc-ownership-lifecycle.md` shows exactly the two span insertions and no other line; the Validation Commands fold pins and no-ambiguity anchors all pass against the edited file; `bash -n` over the target plan's Validation Commands extract passes (block untouched, syntax intact).
- [ ] Commit: `plans: fold successor-row freeze-move licensing into doc-ownership Task 1`

### Task 2: Re-certify the amended target plan at the fresh digest

Files:
- `docs/reviews/2026-09-09-plan-review-doc-ownership-lifecycle-r9.md` *(new)*
- `docs/reviews/2026-09-09-plan-review-doc-ownership-lifecycle-r9.stats.json` *(new)*

- [ ] Launch the `review-plan` skill as a sub-agent on the amended target plan (plans-skill sub-agent prompt template with the amended plan content): focused panel with the blind `correctness-completeness` probe plus the `testing` and `contract-docs` workers (fold-affected domains); reviewers treat the plan file as READ-ONLY; the round writes `docs/reviews/2026-09-09-plan-review-doc-ownership-lifecycle-r9.md` plus its version-1 `.stats.json` sidecar carrying `source_digest` set to the sha256 of the amended plan bytes, `panel_mode: focused` with `selection_reason`, and the `## Summary` section with counts, blocking ids, and the explicit ready verdict.
- [ ] Fold every accepted blocking finding into the two pinned spans only; a fold is a digest change: re-run the Task 1 mechanical audit, then launch the next fresh round (r10, r11, ... numbering continues) on the post-fold digest; never record an exit against a pre-fold digest. A blocking finding whose fix would require editing a frozen target-plan line never breaks the freeze in place: route it through review-reconciliation or stop for user direction, and record it as a backlog item when deferred.
- [ ] Exit gate → expect GREEN: the latest round's artifact Summary reports `ready=yes` with zero unresolved blocking findings, and `python3 scripts/plan_readiness.py docs/plans/2026-09-08-doc-ownership-lifecycle.md` exits 0 on the amended bytes (the gate verifies the sidecar digest binding mechanically).
- [ ] Commit: `plans: re-certify doc-ownership plan at successor-row fold digest`
