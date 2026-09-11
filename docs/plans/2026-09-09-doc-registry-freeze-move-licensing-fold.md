# Plan: Doc-registry validator: successor-row freeze-move pin and argparse CLI rewrite

Origin backlog:
- `docs/history/backlog/2026-09-09-doc-registry-freeze-move-licensing.md` (plan-review r8 Low, plausible-edge, hypothesis confidence, on the doc-ownership-lifecycle plan at digest 33bf86f3)
- `docs/history/backlog/2026-09-10-doc-registry-validator-argparse-cli-rewrite.md` (rider folded into this plan 2026-09-11; source: `docs/reviews/2026-09-10-2026-09-08-doc-ownership-lifecycle-code-review-r1.md`, finding F12)
- `docs/history/backlog/2026-09-10-doc-registry-follow-up-plan-orphaned-diff-channel.md` (rider folded into this plan 2026-09-11; source: `docs/reviews/2026-09-10-2026-09-08-doc-ownership-lifecycle-code-review-r4.md`, finding F9)

Related plan: `docs/plans/completed/2026-09-08-doc-ownership-lifecycle.md` (executed and archived 2026-09-10; it created the validator this plan amends).

Review rounds: `docs/reviews/2026-09-11-plan-review-doc-registry-freeze-move-licensing-fold-r*.md` (round numbering continues from the r2 certification of the previous revision; the latest round governs).

## Terms

- **Registry validator**: `scripts/doc_registry_validator.py`; subcommands `validate`, `check-writes`, `inventory` plus a hermetic `--selftest` mode whose fixture set (99 checks today) is the regression net.
- **Dispatch layer**: the full body of `_dispatch` in the validator: the pre-/post-subcommand flag loops, the post-parse input-channel gathering with its guards (the `--stdin` versus argv-paths conflict, the needs-paths guard, the backslash rejection), the `USAGE` constant, and the `run()`/`main()` wrappers; everything past dispatch (`cmd_validate`, `cmd_check_writes`, `cmd_inventory`, `cmd_selftest`) is contract-frozen.
- **check-writes**: validator subcommand gating changed paths against completed-history immutability; input channels: paths as argv, or porcelain/name-status lines on stdin (`--stdin`). The former `--diff` channel was removed in the doc-ownership execution r2 fix round and now exits 2 (`test_removed_diff_channel_fails_closed`).
- **Porcelain stdin channel**: `git status --porcelain` / `git diff --name-status --no-renames` lines fed to `--stdin`; renames parse on the porcelain `R old -> new` form only; both sides are gated (the old side typed as a deletion, the new side carrying the rename letter).
- **Registered-src lifecycle exemption**: a path whose normalized form equals the `src` of a registry row with `state` completed or superseded is licensed only for a clean add or rename; every other write of it is a HARD finding unless an audit note licenses the override.
- **Successor row**: registry row with `state: superseded` carrying the successor relation (`successor` column, with archived date and reason); licenses the freeze move, never an in-place edit.
- **Freeze move**: the archive `git mv` whose new side lands on a registered lifecycle `src` (a move out of an immutable dir is the artifact leaving and gates HARD unless audit-noted; pinned today by `test_rename_out_of_immutable_dir_fails`).
- **Corruption-override row**: registry row whose audit note licenses an in-place factual fix to a completed-history artifact (ADR-0001 semantics); stays verbatim and distinct from the successor-row license.

## Assumptions

- assume this plan executes against the shipped validator, not by amending a plan document: the doc-ownership-lifecycle plan executed and was archived on 2026-09-10 (`docs/plans/completed/2026-09-08-doc-ownership-lifecycle.md`, squash 7dcdf6c), so the previous revision's mechanism (folding a contract into that plan's Task 1 spans before its execution) no longer has an amendable target and the previous `TARGET_DOC` path is gone from `{plans_dir}`; basis: on-disk probes 2026-09-11 (the archived file is present; `docs/plans/2026-09-08-doc-ownership-lifecycle.md` is absent).
- assume the origin premise is partially absorbed by the shipped validator and the residual is the pinning fixture: `check-writes` already licenses a clean rename into a registered completed/superseded `src` (probe 2026-09-11: a superseded row with successor and reason cells plus `R  docs/live/a.md -> docs/plans/completed/a.md` exits 0; a living row exits 1), so the origin contract lands as a characterization fixture per the re-scope guidance in `docs/history/backlog/2026-09-10-doc-registry-follow-up-plan-orphaned-diff-channel.md`; basis: code read of `cmd_check_writes`/`is_licensed_transition` plus the executed probe.
- assume every `--diff` reference in the previous revision is void: the channel was removed in the doc-ownership execution r2 round (usage exit 2) and all staged-move observability flows through the porcelain stdin channel; basis: `test_removed_diff_channel_fails_closed` and the validator docstring, 2026-09-11.
- assume the argparse rider's r1-era details are adapted, not copied: the finding predates the `--diff` removal, so its "mutually-exclusive `--stdin`/`--diff` group" and its "unreachable `known_flags` branch" describe code that no longer exists (probe 2026-09-11: zero argparse imports, no `known_flags` in the source); the rewritten scope keeps its core: argparse subparsers for `validate`/`check-writes`/`inventory`, native exit-2 fail-closed on unknown input, behavior otherwise unchanged; basis: the rider item text plus source read.
- assume the selftest fixture set stays byte-verbatim through the CLI rewrite: the argparse layer is adapted to the fixtures (exit codes and pinned substrings), never the reverse, and the only fixture changes are this plan's additive pins; basis: the rider's own regression-net framing plus the receiving-review fix-risk triage (structural rewrite only under a green net).
- assume this rewrite supersedes the r2 certification (digest f7c1e0ad) of the previous revision; the fresh review rounds re-binding the digest run in this authoring flow, and no plan document is edited at execution; basis: plans digest-binding rules.
- assume all three origin backlog items stay in place under `{backlog_dir}` while this plan is open and move to `{backlog_completed_dir}` with `Status: done` in the completion pass; basis: plans Plan Lifecycle.

Decision points requiring a grill: none remain.

## Gist & Examples

**What changes.** Two execution tasks on `scripts/doc_registry_validator.py`. First, an additive selftest fixture pair pins the successor-row freeze-move licensing through the porcelain stdin channel: a rename whose new side lands on the `src` of a `superseded` row (successor and reason filled) exits 0, and the same arrival against a `living` row exits 1. Second, the dispatch layer is rewritten with argparse subparsers (`validate`, `check-writes`, `inventory`), preserving the fail-closed exit-2 CLI contract with the full selftest fixture set passing unmodified.

**Why.** The three origin items share one script. The successor-row item predates the validator's implementation; the shipped code already implements the licensing shape it asked for (via the registered-src lifecycle exemption), so its remaining value is a pinning fixture in the regression net. The argparse item is a simplification of the same script's CLI layer: today `_dispatch` hand-rolls argv parsing with two duplicated flag loops (pre-subcommand and post-subcommand), so every flag relationship is maintained twice by hand. Its r1-era text also predates the `--diff` removal, so the fold re-derives both scopes to the validator as it ships today. The previous revision of this plan can no longer pass its own validation (its target plan is archived and its fixture spec names the removed `--diff` channel), which is why the plan pivots to the shipped script; the follow-up item (r4 F9) supplies that re-scope guidance, and its one residual demand (the successor-row fixture pinned through the porcelain stdin channel) is Task 1.

**Before (today).** A contributor renaming a living doc into its registered completed-history location (the freeze move) is pinned only by the generic registered-src fixture (`test_rename_into_registered_src_licensed`, `completed` state); the `superseded` shape with successor and reason cells has no pin, so a refactor of the exemption could silently drop it. The CLI layer parses argv with two hand-rolled flag loops; adding or moving a flag means editing both loops and re-reasoning their interaction.

**After (this plan).** `test_check_writes_successor_row_licenses_move` and `test_check_writes_move_without_successor_row_fails` pin the superseded-row freeze move in both directions, and stay green through the CLI rewrite. The dispatch layer is declared with argparse subparsers with `allow_abbrev=False`; the `--stdin` versus argv-paths conflict stays an explicit exit-2 check keyed on channel state (F7); the `USAGE` constant is retained and surfaced in the adapted error output. Fixture-pinned CLI behavior before the rewrite covers three cases (unknown flag, removed `--diff` channel, `--stdin` with argv paths); Task 2 adds seven characterization fixtures for the currently unpinned exit-2 behaviors (missing subcommand, unknown subcommand word, `--root` after the subcommand, `--selftest` after the subcommand, `--root` without a value, a literal `--` argument, bare `check-writes` with no paths and no `--stdin`); the pre-subcommand `--stdin` duplicate-conflict case keeps its exit-2 outcome through the declared fail-closed delta and argparse-native rejection rather than a dedicated fixture (the silent-accept cases flip from exit 0 to exit 2 under the same delta, as declared above), so the rewrite lands under a widened net instead of an unverified coverage claim. Two deliberate CLI-surface deltas are declared, both fail-closed: `--stdin` is accepted only on `check-writes` (today it is silently ignored on `validate`/`inventory` and honored before the subcommand; both become usage exit 2), and `allow_abbrev=False` disables abbreviation matching (today only exact flags work, so no working invocation changes). All 108 selftest checks pass with the existing 99 byte-verbatim.

**Edge cases.** The corruption-override license (audit-noted in-place write) is untouched and stays distinct from the successor-row license. The stdin line grammar (`parse_change_line`: porcelain and name-status forms, tab-rename rejection, backslash rejection, arrow-bearing literal paths, unknown name-status letters) is outside the dispatch layer and does not change. argparse error paths raise `SystemExit`; the dispatch wrapper converts it to the exit code so `run()` keeps returning `(code, output)` without raising (the selftest drives the CLI through `run()`).

## Evaluation Criteria

**Quality dimensions:**
- correctness: the fixture pair matches the probed contract (exit 0 for the superseded-row arrival, exit 1 for the living-row arrival, both feeding `R  docs/live/a.md -> docs/plans/completed/a.md` to `check-writes --stdin`); the argparse rewrite keeps every CLI-level fixture green without modifying any existing check.
- behavior preservation: subcommand names, flags (`--root`, `--stdin`, `--selftest`), and exit semantics (0 clean/licensed, 1 findings, 2 usage) are unchanged; callers per `agents/skills/done/SKILL.md` Step 2.648 (`validate`, `check-writes`, `inventory`) are unaffected; `python3 scripts/doc_registry_validator.py --selftest` exits 0 reporting 108 checks.
- structural simplification: `import argparse` present at module top; the duplicated pre-/post-subcommand flag loops are replaced by one parser declaration.
- hygiene: no em-dash in this plan's Markdown; the public hygiene scan exits 0.

**Done when:**
- the selftest block carries `test_check_writes_successor_row_licenses_move` exactly once and `test_check_writes_move_without_successor_row_fails`, and `--selftest` exits 0;
- the dispatch layer is declared with argparse (`import argparse` present) and the full selftest set passes with zero existing checks modified;
- the Validation Commands block below exits 0 end to end.

**Ship when:**
- (none; all work is repository-local script and review artifacts)

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/doc_registry_validator.py` (scoped: the dispatch layer and the `--selftest` fixture block; all other regions, in particular `parse_change_line`, `is_licensed_transition`, `cmd_check_writes`, `cmd_validate`, `cmd_inventory`, are frozen; reject any review finding that alters the stdin line grammar, the licensing tiers, or an existing fixture)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/plans/completed/2026-09-08-doc-ownership-lifecycle.md`; reason: immutable archived history; this plan never edits it.
- `docs/history/backlog/2026-09-10-doc-registry-follow-up-plan-orphaned-diff-channel.md`; reason: folded as an origin item (r4 F9); this plan absorbs its premise repair (the `--diff` re-derivation and the Task 1 porcelain re-scope), the item file is never edited during execution, and it moves with the other origin items at the completion pass.
- `docs/history/backlog/2026-09-10-doc-registry-r7-residuals.md`; reason: separate open residual family (facts-import warn, message cosmetics, untracked dir collapse, clock seam); no overlap with the dispatch layer or the pinning fixture.
- `agents/skills/done/SKILL.md`, `agents/skills/doc-hierarchy/SKILL.md`, `docs/maintenance/document-registry.md`; reason: they describe semantics this plan preserves unchanged, so findings there are out of scope unless plan work breaks them.

## Design Invariants (CR Guard)

- The corruption-override license (ADR-0001 audit-noted row, in-place write) is preserved verbatim; the successor-row pin is purely additive and must never replace or blur it (`test_immutable_write_override_passes` stays green).
- The licensing semantics (`is_licensed_transition`, `cmd_check_writes` tiers) and the stdin line grammar (`parse_change_line`) are frozen; the CLI rewrite touches only the dispatch layer.
- The selftest fixture set is a byte-verbatim regression net: argparse is adapted to the fixtures (exit codes and pinned substrings, including the lowercase `usage` substring the CLI fixtures pin), never a fixture edited to fit argparse; the only fixture changes are this plan's additive pins (Task 1: two contract fixtures; Task 2: seven CLI characterization fixtures added before the rewrite so it lands under a widened net).
- The exit-code contract is unchanged: 0 clean or licensed, 1 findings, 2 usage; argparse-native failures must preserve exit-2 fail-closed (`test_unknown_flag_fails_closed` and `test_removed_diff_channel_fails_closed` stay green).
- Execution branching follows the execute-plan skill's normal Phase 0 setup (backlog non-goal for this plan).

## Validation Commands

```bash
set -euo pipefail
VALIDATOR="scripts/doc_registry_validator.py"
PLAN_DOC="docs/plans/2026-09-09-doc-registry-freeze-move-licensing-fold.md"
test -f "$VALIDATOR" || { echo 'FAIL: validator missing'; exit 1; }

# Pin probes: each obligation gets its own dedicated probe, count-pinned
test "$(grep -cF 'import argparse' "$VALIDATOR")" -ge 1 || { echo 'FAIL: argparse import missing'; exit 1; }
test "$(grep -cF 'test_check_writes_successor_row_licenses_move' "$VALIDATOR")" -eq 1 || { echo 'FAIL: successor-row fixture pin missing or duplicated'; exit 1; }
test "$(grep -cF 'test_check_writes_move_without_successor_row_fails' "$VALIDATOR")" -eq 1 || { echo 'FAIL: negative successor-row fixture missing or duplicated'; exit 1; }
test "$(grep -cF 'test_missing_subcommand_fails_closed' "$VALIDATOR")" -eq 1 || { echo 'FAIL: missing-subcommand fixture missing or duplicated'; exit 1; }
test "$(grep -cF 'test_unknown_subcommand_fails_closed' "$VALIDATOR")" -eq 1 || { echo 'FAIL: unknown-subcommand fixture missing or duplicated'; exit 1; }
test "$(grep -cF 'test_root_after_subcommand_fails_closed' "$VALIDATOR")" -eq 1 || { echo 'FAIL: root-after-subcommand fixture missing or duplicated'; exit 1; }
test "$(grep -cF 'test_selftest_after_subcommand_fails_closed' "$VALIDATOR")" -eq 1 || { echo 'FAIL: selftest-after-subcommand fixture missing or duplicated'; exit 1; }
test "$(grep -cF 'test_root_requires_value_fails_closed' "$VALIDATOR")" -eq 1 || { echo 'FAIL: root-requires-value fixture missing or duplicated'; exit 1; }
test "$(grep -cF 'test_double_dash_argument_fails_closed' "$VALIDATOR")" -eq 1 || { echo 'FAIL: double-dash fixture missing or duplicated'; exit 1; }
test "$(grep -cF 'test_check_writes_needs_paths_fails_closed' "$VALIDATOR")" -eq 1 || { echo 'FAIL: needs-paths fixture missing or duplicated'; exit 1; }

# Net-integrity anchors: the regression net was not weakened
test "$(grep -cF 'test_unknown_flag_fails_closed' "$VALIDATOR")" -eq 1 || { echo 'FAIL: unknown-flag fixture lost'; exit 1; }
test "$(grep -cF 'test_removed_diff_channel_fails_closed' "$VALIDATOR")" -eq 1 || { echo 'FAIL: removed-channel fixture lost'; exit 1; }
test "$(grep -cF 'test_immutable_write_override_passes' "$VALIDATOR")" -eq 1 || { echo 'FAIL: corruption-override fixture lost'; exit 1; }
test "$(grep -cF 'test_rename_out_of_immutable_dir_fails' "$VALIDATOR")" -eq 1 || { echo 'FAIL: rename-out fixture lost'; exit 1; }

# Regression net: the full selftest set passes end to end
SELFTEST_OUT="$(python3 "$VALIDATOR" --selftest 2>&1)" || { echo 'FAIL: selftest exited non-zero'; exit 1; }
grep -qF 'selftest OK' <<<"$SELFTEST_OUT" || { echo 'FAIL: selftest verdict line missing'; exit 1; }

# Format gates over this plan's authored Markdown
bash scripts/check-no-em-dash.sh file "$PLAN_DOC" || { echo 'FAIL: em dash'; exit 1; }
REPO="$(git rev-parse --show-toplevel)"
( cd "$REPO" && bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" ) || { echo 'FAIL: hygiene scan'; exit 1; }
```

Authoring-time record (2026-09-11, against the pre-edit tree at digest f7c1e0ad): `--selftest` exits 0 reporting `selftest OK: 99 checks passed`; the argparse pin returns 0, both Task 1 fixture pins return 0, and all seven Task 2 CLI fixture pins return 0 (RED-today; they flip green exactly when their tasks land); the four net-integrity anchors each return exactly 1; the executed probes pin the fixture contracts against real behavior (superseded-row arrival exit 0, living-row arrival exit 1; the seven CLI cases each exit 2 with the `usage` substring present); the plan file carries zero em-dash characters; the public hygiene scan exits 0; `bash -n` over this block exits 0. Fold re-audit (2026-09-11, after folding the diff-channel rider): the same authoring-time outcomes re-verified against the folded bytes; pins RED-today, the four net-integrity anchors each return exactly 1, `--selftest` exits 0 at 99 checks, zero em-dash, hygiene exit 0, `bash -n` 0.

### Task 1: Pin the successor-row freeze-move licensing in the selftest

Files:
- `scripts/doc_registry_validator.py` (selftest fixture block only)

- [ ] Record the plan base for the final audit: `BASE_SHA="$(git rev-parse HEAD)"`.
- [ ] Characterization baseline → expect GREEN: `python3 scripts/doc_registry_validator.py --selftest` exits 0 reporting 99 checks (the net is green before any edit).
- [ ] Add the fixture pair to the selftest block, additive only. `test_check_writes_successor_row_licenses_move`; given a fixture registry whose row for `docs/plans/completed/a.md` is `| doc-s | no | superseded | 2026-01-01 | r | docs/plans/completed/a.md | doc-new |  |  |` (superseded state, successor and reason cells filled) and porcelain stdin `R  docs/live/a.md -> docs/plans/completed/a.md` fed to `check-writes --stdin`, expects exit 0 with `licensed lifecycle add` in the output (the freeze move arriving on the registered src of a superseded row is the licensed lifecycle transition). `test_check_writes_move_without_successor_row_fails`; given the same arrival against a `living`-state row `| doc-s | no | living |  |  | docs/plans/completed/a.md |  |  |  |`, expects exit 1 with `immutable path written without override` (no completed/superseded relation, no lifecycle exemption). Both fixtures follow the existing `make_fixture` + `run()` + `st.expect` pattern (probe-verified 2026-09-11).
- [ ] Run → expect GREEN: `python3 scripts/doc_registry_validator.py --selftest` exits 0 reporting 101 checks; every pre-existing check name and body byte-identical (`git diff` over the file shows only the two added fixture blocks).
- [ ] Commit: `validator: pin successor-row freeze-move licensing in selftest`

### Task 2: Rewrite the dispatch layer with argparse subparsers

Files:
- `scripts/doc_registry_validator.py` (dispatch layer only; the selftest block is frozen for this task)

- [ ] Characterization baseline → expect GREEN: `python3 scripts/doc_registry_validator.py --selftest` exits 0 reporting 101 checks before any edit.
- [ ] Add seven CLI characterization fixtures to the selftest block, additive only, each expecting exit 2 with the `usage` substring in the output (probe-verified 2026-09-11 against today's parser; these seven fixtures plus the three already-pinned ones cover the preserved dispatch-layer exit-2 surface, except the pre-subcommand `--stdin` paths, whose exit-2 outcome survives through the declared fail-closed delta and argparse-native rejection rather than dedicated fixtures): `test_missing_subcommand_fails_closed`; given `run([])`, expects exit 2. `test_unknown_subcommand_fails_closed`; given `run(["frobnicate"])`, expects exit 2. `test_root_after_subcommand_fails_closed`; given `run(["check-writes", "--root", str(root)])`, expects exit 2. `test_selftest_after_subcommand_fails_closed`; given `run(["check-writes", "--selftest"])`, expects exit 2. `test_root_requires_value_fails_closed`; given `run(["--root"])`, expects exit 2. `test_double_dash_argument_fails_closed`; given `run(["--"])`, expects exit 2 (today a literal `--` hits the unknown-flag branch; the rewrite must preserve this, not let argparse consume it as an end-of-options separator). `test_check_writes_needs_paths_fails_closed`; given `run(["--root", str(root), "check-writes"])` (no paths, no `--stdin`), expects exit 2 (bare `check-writes` must keep failing closed; an argparse `nargs='*'` rewrite that drops the needs-paths guard would exit 0 and skip the write gate entirely).
- [ ] Run → expect GREEN: `python3 scripts/doc_registry_validator.py --selftest` exits 0 reporting 108 checks; every pre-existing check name and body byte-identical.
- [ ] Replace the hand-rolled argv parser with an argparse declaration: `import argparse` at module top; top-level parser with `prog` pinned to `doc_registry_validator.py`, `allow_abbrev=False`, options `--root PATH` and `--selftest`, and required subparsers `validate`, `check-writes`, `inventory` (reconciled with bare `--selftest`: a `--selftest` appearing before any subcommand token short-circuits to `cmd_selftest` before subparser validation and before inspecting the remaining argv, preserving today's outcome where even `--selftest --bogus` runs the selftest, while `check-writes --selftest` exits 2 as its fixture pins); the `check-writes` subparser carries `--stdin` (store_true) and positional paths `nargs='*'`; re-carry the dispatch guards with their exit codes: the `--stdin` versus argv-paths conflict keyed on channel state (F7: empty stdin must not silently discard argv paths), the needs-paths guard, and the backslash rejection.
- [ ] Preserve the fail-closed contract against the widened fixture net unmodified: unknown flags and unknown subcommand words exit 2 with usage text (adapt argparse output so the lowercase `usage` substring the CLI fixtures pin stays present); `--root` after the subcommand, `--selftest` after the subcommand, a missing subcommand, `--root` without a value, a literal `--` argument, and bare `check-writes` each exit 2 as the new fixtures pin; `run()` keeps returning `(code, output)` without raising by converting argparse's `SystemExit` to its exit code with stderr captured; `main()`, `cmd_validate`, `cmd_check_writes`, `cmd_inventory`, `cmd_selftest`, and `parse_change_line` are unchanged.
- [ ] Declare the two deliberate CLI-surface deltas in the adapted help/error output: `--stdin` is accepted only on `check-writes` (today it is silently ignored on `validate`/`inventory` and honored before the subcommand; both become usage exit 2, fail-closed), and abbreviation matching is disabled (`allow_abbrev=False`; today only exact flags work, so no working invocation changes).
- [ ] Run → expect GREEN: the full selftest set passes with zero existing checks modified (108 checks, names unchanged; `git diff` over the selftest block shows only the seven added fixtures from this task).
- [ ] Commit: `validator: rewrite CLI dispatch with argparse subparsers`

### Task 3: Full validation and commit audit

- [ ] Run the Validation Commands block end to end → expect GREEN (the argparse pin flips green with Task 2; both fixture pins flipped green with Task 1).
- [ ] Commit audit: each of this plan's commits shows only `scripts/doc_registry_validator.py` in `git show --name-only --format= <sha>`; a foreign commit swept into the range since `BASE_SHA` is joint state (report it, never rewrite it).
