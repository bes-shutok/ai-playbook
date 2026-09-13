# Plan: Doc-registry validator residuals close-out

Backlog origins (scope of record):
- `docs/history/backlog/2026-09-10-doc-registry-r7-residuals.md` (items 1-15; re-anchored against the post-argparse-rewrite validator)
- `docs/history/backlog/2026-09-11-doc-registry-fold-exit-surface-exception-coverage.md` (the `--bogus validate` characterization fixture)
- `docs/history/backlog/2026-09-13-doc-registry-cli-doc-precision.md` (3 Low CLI-doc items)

Anchor: every re-anchor in this plan was verified against the working tree at
base commit `7871ed7669d6d37137a3e4580fc6119b035e5cab` (2026-09-13), including
live probes of all four check-writes classification messages and the
`--bogus validate` exit. Tasks pin content anchors (function names, message
substrings), not line numbers; line numbers drift when peers commit.

## Terms

- **Validator**: `scripts/doc_registry_validator.py`; subcommands `validate`, `check-writes`, `inventory`, plus `--selftest`.
- **Registry**: `docs/maintenance/document-registry.md`, the Layer 2 ownership table the validator consumes.
- **Registered-src exemption**: the `check-writes` rule that licenses the `src` of a `completed`/`superseded` row only for the add/rename transition.
- **Audit note**: the optional registry cell holding the dated `user-approved YYYY-MM-DD:` confirmation token that licenses an override.
- **facts_paths**: `scripts/facts_paths.py`, the canonical facts TOML resolver.
- **Selftest**: a script's built-in check suite (`--selftest`); validator checks are `st.expect` fixtures with stable check names.

## Assumptions

- assume every re-anchor reflects the code at base commit `7871ed7` and that tasks may therefore pin message substrings and function names; basis: live probes on 2026-09-13 recorded in `docs/tmp/plan-requirements-doc-registry-validator-residuals.md`.
- assume the three origin items were deferred for round-budget reasons, not merit, so closing them now needs no scope re-litigation; basis: origin item 1 header ("valid, non-blocking review findings deferred at the round-budget stop per the backlog-deferral default").
- assume no living document pins the selftest check count, so adding fixtures needs no count-arithmetic updates; basis: grep over open plans, README, done, and doc-hierarchy on 2026-09-13 found none.
- assume the two scripts' inline selftests are the only test surface (no external test files exist for them); basis: repo layout, both selftests live inside the scripts they test.

Decision points requiring a grill: audit-scan dedup wording: one shared message template adopts the full real-non-future contract, validate side upgrades and two check-writes fixture pins flip, source: standing pre-authorization over the r7 F8 and H1 item texts, 2026-09-13, Task 1; case-only rename tier: near-match warn with a verify duty instead of documenting an override path, source: standing pre-authorization over the item's either/or, code route chosen, 2026-09-13, Task 2; untracked dir-collapse tier: stage-the-move hint naming the dir instead of expanding srcs, source: standing pre-authorization, smaller-surface option, 2026-09-13, Task 2; clock seam shape: `audit_note_valid` gains a `today` parameter plus midnight-robust fixture offsets, source: standing pre-authorization over the r7 F6 item text, subprocess fixtures cannot pass the parameter, 2026-09-13, Task 4; fold-exit coverage route: eighth characterization fixture, the archived plan's sentence is not edited, source: standing pre-authorization over the item's either/or, living-code route chosen, 2026-09-13, Task 5; done tmp_dir resolution: facts_paths gains a `resolve` CLI and done degrades to `docs/tmp` on an absent module, source: standing pre-authorization over the item's first-listed route adapted for vendored fail-open parity, 2026-09-13, Task 8; registry boilerplate rows: accepted-cost note in ADR-0003, the derive-by-default tier is declined, source: standing pre-authorization, proportionate option at Low severity, 2026-09-13, Task 9; exemption dedup surface: done Step 2.648 intro reduced to a pointer and README needs no edit, source: README verified pointer-only on 2026-09-13, 2026-09-13, Task 8.

## Gist & Examples

The doc-registry validator is the enforcement engine behind the document
ownership lifecycle: `validate` checks registry integrity, `check-writes`
gates writes to completed-history paths, and both the done skill and the
docs-branch flow invoke it. Three backlog items accumulated 19 findings
against it and its surrounding prose. All 19 were re-anchored against the
post-argparse-rewrite validator and all 19 are still live. This plan closes
them: it unifies the two hand-rolled audit-note scans into one helper with
one message template, fixes four classification and message defects in
`check-writes`, makes a silent degradation loud (facts module absent), makes
the clock-skew fixtures midnight-proof behind an injectable clock, removes a
dead branch and the ephemeral review-round provenance tags, adds the missing
`--bogus validate` characterization pin, and syncs the prose artifacts
(done Step 2.648, doc-hierarchy identity derivation, registry header, ADR-0003).

**Before (today) / After (this plan)**, same trigger each time:

1. Gate a body edit reported as porcelain `M  path`: today the HARD message
   prints a stray space ("change type M ;"); after, it prints "(change type M;".
   Classification unchanged.
2. Gate `?? docs/plans/completed/` (git collapsed a fully untracked dir):
   today the dir itself hits the generic HARD "immutable path written without
   override" with no remediation hint; after, it is a warn naming the dir with
   a stage-the-move duty, because the collapse means the individual files are
   invisible to this run, not that a protected write happened.
3. Gate `?? docs/plans/completed/A.md` when the registered src is `a.md`:
   today a generic HARD, while the byte-equal spelling gets the helpful
   stage-the-move warn; after, the case-variant untracked entry gets the same
   warn naming the registered spelling.
4. Gate the rename `R  a.md -> A.md` (case-only rename inside one directory):
   today the old side hard-blocks as a deletion, so a pure case normalization
   needs a corruption-override note; after, the old side takes the near-match
   warn tier with a verify duty (the new side already warns as a case-variant
   add).
5. Run the validator where `facts_paths.py` is missing: today facts keys
   silently resolve to defaults, gating default dirs while configured dirs go
   ungated with no diagnostic; after, a warn names the degradation.
6. Run `--bogus validate`: today exit 2 with usage, but no fixture pins it;
   after, the eighth dispatch-layer characterization fixture pins exit 2 and
   the `usage` substring, closing the fold plan's coverage-exception gap.

Edge cases that shaped the design: the status strip happens in the message
only (a parse-time strip would change `is_licensed_transition` semantics:
the two-char form `' A'` is NOT a licensed transition because the leading
space is status-column data, while the stripped `'A'` would match the
name-status letter rule and license the write); the two HARD-to-warn
reclassifications are the only ones the plan permits, and both carry an
explicit verify duty; the skew offsets move from +1/+2 to +0/+3 so a run
straddling local midnight cannot flip an expectation (today's +2 "bad"
fixture passes if the clock reads one day later at check time).

## Evaluation Criteria

**Quality dimensions:**
- correctness: each of the 19 findings lands exactly as re-anchored; the gate stays fail-closed; the only HARD-to-warn reclassifications are the two mandated ones (untracked dir collapse, case-only rename old side), each with an explicit verify duty; live probes in this repo's Validation Commands match the pinned strings.
- test coverage: every behavior change lands with an `st.expect` (or `st.check`) fixture; behavior fixes run RED before the fix and GREEN after; characterization pins (origin 2, successor-cycle protection) state GREEN-on-arrival.
- maintainability: one shared audit-note defect scan replaces two divergent hand-rolled scans; no dead branch remains in `successor_cycles`; zero provenance round tags remain in the validator source.
- documentation: wording synced and pinned by greps: done hard-findings list, done Step 2.648 pointer, facts_paths resolve CLI, doc-hierarchy flat-RFC clause, registry header clause, ADR-0003 cost note.

**Done when:**
- `python3 scripts/doc_registry_validator.py --selftest` exits 0 with all checks passing, new fixtures included.
- `python3 scripts/facts_paths.py --selftest` exits 0.
- `python3 scripts/doc_registry_validator.py validate` exits 0 on this repo.
- Every Validation Command in this plan exits 0 against the working tree.
- The three origin backlog items still sit under `docs/history/backlog/` (they move to `backlog/completed/` in the plan-completion pass, not in a task).

**Ship when:**
- Downstream copy-synced hosts pick up the validator, facts_paths, and done skill changes with their next runtime redeploy; this host's `~/.ai-playbook/scripts` is symlinked into the repo already, so no local action remains. (Prose only; no deploy task.)

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/doc_registry_validator.py`
- `scripts/facts_paths.py`

**Tests:**
- the inline selftests inside the two files above *(extended in place; no separate test files exist)*

**Documentation:**
- `agents/skills/done/SKILL.md` *(Step 2.648 intro paragraph, the Step 2.648 tmp-dir command block, and the hard-findings bullet only; all other steps frozen)*
- `agents/skills/doc-hierarchy/SKILL.md` *(identity-derivation paragraph only; rest frozen)*
- `docs/maintenance/project-decisions.md` *(ADR-0003 section only; an appended note)*
- `docs/maintenance/document-registry.md` *(HTML comment header only; table rows untouched)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/plans/completed/**`; reason: archived history is immutable
- `README.md`; reason: its exemption text is already pointer-only (verified 2026-09-13), no change required
- `docs/history/backlog/2026-09-10-doc-registry-r7-residuals.md`, `2026-09-11-doc-registry-fold-exit-surface-exception-coverage.md`, `2026-09-13-doc-registry-cli-doc-precision.md`; reason: origin items move to `backlog/completed/` in the completion pass, not by a task
- `docs/tmp/plan-requirements-doc-registry-validator-residuals.md`; reason: authoring scratch, removed at completion

## Design Invariants (CR Guard)

- Fail-closed direction preserved: no task may downgrade an existing HARD family to warn or skip, except the two mandated reclassifications (untracked dir collapse; case-only rename old side), which move to the warn tier WITH an explicit verify duty in the message.
- The registered-src exemption stays bounded to the add/rename transition; doc-hierarchy remains its prose SOT; done Step 2.648 keeps a pointer, not a restatement.
- Every warn tier names the cause and the duty (stage the move / verify); no silent passes.
- The facts-module-absent warn is additive diagnostics: resolution behavior (defaults) is unchanged.
- The selftests stay hermetic: fixture roots under tmp, monkeypatched module globals restored in `finally`, no writes outside fixture roots.

## Validation Commands

```bash
python3 scripts/doc_registry_validator.py --selftest
python3 scripts/facts_paths.py --selftest
python3 scripts/doc_registry_validator.py validate

# Round-tag sweep over the validator: every F+digit line EXCEPT the
# `# noqa: F401` lint directive at the facts import must be gone after
# Task 7. Two stages so each grep's exit status is observed individually;
# shape-anchored patterns stay out of this sweep on purpose (tags close
# with :, ), ,, ;, or a space, so no delimiter assumption is complete).
all_hits="$(grep -nE "F[0-9]" scripts/doc_registry_validator.py)"; rc1=$?
if [ "$rc1" -ge 2 ]; then echo "FAIL: grep error"; exit 1; fi
if [ "$rc1" -eq 0 ]; then
  tags="$(printf '%s\n' "$all_hits" | grep -v noqa)"; rc2=$?
  if [ "$rc2" -eq 0 ]; then echo "FAIL: provenance round tag remains"; printf '%s\n' "$tags"; exit 1
  elif [ "$rc2" -ge 2 ]; then echo "FAIL: grep error"; exit 1; fi
fi
# Clean pass: rc1=1 (no F+digit line at all) or rc2=1 (only the noqa line remains).

# Wording pins (fail-closed positives; each obligation gets its own grep).
grep -qF "malformed or ill-dated audit-note tokens" agents/skills/done/SKILL.md \
  || { echo "FAIL: done hard-findings wording"; exit 1; }
grep -qF "prose SOT for the registered-src exemption" agents/skills/done/SKILL.md \
  || { echo "FAIL: 2.648 exemption pointer missing"; exit 1; }
grep -qF "FACTS_PATHS_SCRIPT" agents/skills/done/SKILL.md \
  || { echo "FAIL: 2.648 tmp_dir not routed through facts_paths"; exit 1; }
grep -qF '== "resolve"' scripts/facts_paths.py \
  || { echo "FAIL: facts_paths resolve CLI missing"; exit 1; }
grep -qF "trailing -rfc" agents/skills/doc-hierarchy/SKILL.md \
  || { echo "FAIL: flat-RFC identity clause missing in doc-hierarchy"; exit 1; }
grep -qF "trailing -rfc" docs/maintenance/document-registry.md \
  || { echo "FAIL: flat-RFC identity clause missing in registry header"; exit 1; }
grep -qF "accepted ADR-0003 cost" docs/maintenance/project-decisions.md \
  || { echo "FAIL: ADR-0003 cost note missing"; exit 1; }

bash scripts/check-no-em-dash.sh touched
bash scripts/scan-public-hygiene.sh
```

### Task 1: One shared audit-note defect scan (origin 1 items 8 + 10)

Files:
- `scripts/doc_registry_validator.py`

Today `cmd_validate` (row loop, message "HARD malformed audit note '%s' in
registry row (src=%s); an override note must begin with 'user-approved
YYYY-MM-DD:' (ADR-0001 user confirmation)") and the `cmd_check_writes` row
scan (message "HARD invalid audit note '%s' on registry row for %s; an
override note must begin with a real, non-future 'user-approved YYYY-MM-DD:'
token (ADR-0001 user confirmation)") hand-roll the same contract with
divergent strings; the validate message omits the real-non-future date rule.

- [ ] Add RED fixture near the existing audit-note validate fixtures: given a registry whose completed row carries `self-approved quick fix`, `run(["--root", str(root), "validate"])` expects exit 1 with `want_substr="real, non-future"` (fails today; the validate message lacks the phrase). Name it `test_validate_audit_message_states_full_contract`.
- [ ] Run → expect RED on `test_validate_audit_message_states_full_contract` ONLY (every other check green): `python3 scripts/doc_registry_validator.py --selftest`.
- [ ] Implement in one edit: add module-level helper `audit_note_defects(rows)` returning the rows whose `state` is completed/superseded, whose non-empty `audit` fails `audit_note_valid`, plus `audit_note_hard_message(row)` returning the ONE shared message: `HARD malformed audit note '<audit>' in registry row (src=<src>); an override note must begin with a real, non-future 'user-approved YYYY-MM-DD:' token (ADR-0001 user confirmation)` (keeps the `malformed audit note` substring the validate fixtures pin); rewire `cmd_validate`'s audit branch and `cmd_check_writes`'s inline row-scan check (the check that fires before the multi-claim `continue`, keeping that ordering guarantee) to use the helper for detection and the template for the message (`cmd_check_writes` keeps its own `note_hard` counting and its separate override/standing-override audit reads); and flip the two check-writes fixture pins that expect the old wording: `test_check_writes_selfminted_note_hard_fails` and `test_multi_claimed_row_bad_audit_note_reported` change `want_substr="invalid audit note"` to `want_substr="malformed audit note"` (the flips land with the rewire; flipping them before the rewire would fail the RED run).
- [ ] Run → expect GREEN: `python3 scripts/doc_registry_validator.py --selftest`.
- [ ] Commit: `doc-registry: one shared audit-note defect scan with the full contract message`

### Task 2: Check-writes classification and message fixes (origin 1 items 2, 3, 4, 5)

Files:
- `scripts/doc_registry_validator.py`

All four probes were executed live on 2026-09-13; the RED expectations below
are the observed today-behaviors flipped.

- [ ] Item 2 (message whitespace): add RED fixture `test_hard_message_strips_status_padding`: given stdin `M  docs/plans/completed/a.md` (two-char porcelain form) against a fixture whose completed row registers `docs/plans/completed/a.md`, `check-writes --stdin` expects exit 1 with `want_substr="change type M;"` (today the output reads `change type M ;`; the probe confirmed it). Fix: apply `.strip()` to `change_type` in the HARD message interpolation ONLY (the raw two-char value stays semantic for `is_licensed_transition`).
- [ ] Item 4 (untracked case-variant): add RED fixture `test_untracked_case_variant_warns_stage_move`: given stdin `?? docs/plans/completed/A.md` with registered src `docs/plans/completed/a.md`, `check-writes --stdin` expects exit `0` on a folding host (`folds = sys.platform in ("darwin", "win32")`, the suite's anchored trait idiom) with `want_substr="is not the registered spelling"` and `want_substr="stage the move"`, and exit 1 on an identity host with `want_substr="immutable path written without override"` (on identity hosts the variant is a genuinely distinct file; today on a folding host: generic HARD, exit 1, probe confirmed). Fix: in the entries loop, after the byte-equal registered-src branch, an entry with `?` in its change type whose folded path is in `lifecycle_folded` but whose unfolded path is not in `lifecycle_srcs` prints `warn: untracked case-variant of registered lifecycle src; <rel> is not the registered spelling <stored>; stage the move (git add) so the change type can be checked` and continues.
- [ ] Item 3 (untracked dir collapse): add RED fixture `test_untracked_dir_collapse_hints_stage_move`: given a fixture whose `docs/plans/completed` directory exists (create it explicitly in the block) and stdin `?? docs/plans/completed/`, `check-writes --stdin` expects exit 0 with `want_substr="untracked directory"` and `want_substr="stage the move"` (today: generic HARD on `docs/plans/completed`, exit 1, probe confirmed). Fix: an untracked entry that is not a registered src but resolves to an existing directory under an immutable root (`(root / rel).is_dir()`) prints `warn: untracked directory <rel> under a completed-history dir; git collapsed its contents; stage the move (git add) so the individual change types can be checked` and continues.
- [ ] Item 5 (case-only rename): add RED fixture `test_case_only_rename_old_side_warns`: given stdin `R  docs/plans/completed/a.md -> docs/plans/completed/A.md`, `check-writes --stdin` expects exit `0` on a folding host (`folds = sys.platform in ("darwin", "win32")`, the suite's anchored trait idiom) with `want_substr="case-only rename"`, and exit 1 on an identity host with `want_substr="immutable path written without override"` (a case-only rename is only fold-equal, hence warnable, where the platform folds; on identity hosts the two paths are genuinely distinct files and the old side stays a HARD deletion; today on a folding host the probe showed the old side HARD as `change type D`, exit 1). Fix: in the registered-src HARD branch, before printing, when `change_type == "D"` and `entries` contains a sibling `(other_rel, other_ct)` with `other_ct is not None` (bare channel lines carry `None`, and `is_licensed_transition(None)` would raise), `is_licensed_transition(other_ct)` true, `posixpath.dirname(other_rel) == posixpath.dirname(rel)` and `_fold(other_rel) == _fold(rel)`, print `warn: case-only rename of registered lifecycle src; <rel> is the fold-equal old side of a same-directory rename; verify it is a pure case normalization, not a content change or a deletion` and continue (warn tier, not counted hard).
- [ ] Regression guard (no new fixtures; the suite already pins both edges): verify the EXISTING fixtures `test_rename_out_of_immutable_dir_fails` (`R  docs/plans/completed/a.md -> docs/live/a.md` stays exit 1) and `test_rename_into_registered_src_licensed` (`R  docs/tmp/x.md -> docs/plans/completed/a.md` stays exit 0) keep passing, proving the sibling detection does not leak across directories or fold-mismatched pairs.
- [ ] Run → expect the four new fixtures RED on their folding-host expectation and both existing regression fixtures still GREEN, then implement, then Run → expect GREEN: `python3 scripts/doc_registry_validator.py --selftest`.
- [ ] Commit: `doc-registry: check-writes classification and message fixes`

### Task 3: Warn when the facts module is absent (origin 1 item 1)

Files:
- `scripts/doc_registry_validator.py`

Today `_import_facts_paths()` returning `None` makes
`resolve_repo_relative_key` fall back to the default with no diagnostic (the
existing warn fires only on the exception arm), so a repo with non-default
facts keys gets default dirs gated and configured dirs ungated silently.

- [ ] Add RED fixture `test_facts_module_absent_warns`: inside the selftest, save `_import_facts_paths`, monkeypatch it to `lambda: None`, call `resolve_config(root)` on a minimal fixture root under `contextlib.redirect_stderr`, assert the captured stderr contains `facts_paths module not importable` and that all three resolved cfg values equal the documented defaults; restore the original in a `finally` (same save/set/finally idiom the selftest short-circuit fixture uses for `cmd_selftest`). Fails today because no warn is printed.
- [ ] Fix: in `resolve_repo_relative_key`, when `_import_facts_paths()` returns `None`, print `warn: facts_paths module not importable next to the validator; facts keys resolve to defaults` to stderr (mirrors the exception-arm warn). Once per key is acceptable; do not add global once-only state.
- [ ] Run → expect RED, implement, Run → expect GREEN: `python3 scripts/doc_registry_validator.py --selftest`.
- [ ] Commit: `doc-registry: warn when the facts module is not importable`

### Task 4: Injectable clock seam and midnight-robust skew fixtures (origin 1 item 6)

Files:
- `scripts/doc_registry_validator.py`

Today `audit_note_valid` reads `datetime.date.today()` at check time while
the skew fixtures compute `skew_ok` (+1 day) and `skew_bad` (+2 days) at
fixture-build time; a run straddling local midnight flips the +2 expectation.

- [ ] Add RED checks via `st.check` (direct calls, no CLI): `audit_note_valid("user-approved 2026-01-02: fix", today=datetime.date(2026, 1, 1))` is True, `audit_note_valid("user-approved 2026-01-03: fix", today=datetime.date(2026, 1, 1))` is False, `audit_note_valid("user-approved 2099-01-01: fix", today=datetime.date(2026, 1, 1))` is False. RED mode today: the selftest aborts with `TypeError: ... unexpected keyword argument 'today'` at the first direct call (the conditions evaluate eagerly), so RED is verified by that crash, not by three FAIL lines.
- [ ] Fix: `audit_note_valid(audit, today=None)` with `if today is None: today = datetime.date.today()`; the comparison uses the parameter; the production call sites pass nothing (behavior unchanged).
- [ ] Retarget the CLI skew fixtures to midnight-robust offsets in the same task and rename them to match: `skew_ok` becomes +0 days with the check renamed `test_audit_note_today_passes`, `skew_bad` becomes +3 days with the check renamed `test_audit_note_three_days_ahead_fails` (`+0` passes whether the check-time clock reads the build-day or the next; `+3` fails under both, since the tolerance is one day); update the comment to state the straddle argument.
- [ ] Run → expect the direct-call checks RED, implement, Run → expect GREEN: `python3 scripts/doc_registry_validator.py --selftest`.
- [ ] Commit: `doc-registry: injectable clock seam and midnight-robust skew fixtures`

### Task 5: Pre-subcommand unknown-flag pin and CLI doc precision (origin 2 + origin 3 items 1-2; item 3 of origin 3)

Files:
- `scripts/doc_registry_validator.py`

The dispatch-layer characterization block pins unknown-flag surfaces but has
no fixture for `--bogus validate` (probe 2026-09-13: argparse
`unrecognized arguments`, usage text, exit 2). The `_build_parser` docstring
declares many deltas but not the empty `--root=` value or the `--stdin`
before `--selftest` consequence; the dispatch-block NOTE overclaims.

- [ ] Add characterization fixture `test_unknown_flag_before_subcommand_fails_closed`: given `run(["--bogus", "validate"])`, expects exit 2 with `want_substr="usage"`. GREEN on arrival (behavior already correct; this is the coverage pin the fold plan's exception lacked). Place it beside the existing `--bogus --selftest` fixture.
- [ ] Extend the `_build_parser` docstring with two declared-delta bullets, no provenance tags: (a) `--root=` with an empty attached value resolves as no `--root` (the empty value is falsy, so repo-root search via git toplevel then cwd applies; fail-neutral); (b) `--stdin` before `--selftest` breaks the bare-token pre-scan, so argparse rejects the unknown top-level `--stdin` with usage exit 2 where the bare `--selftest` form would have run the suite (exit 0 to exit 2, left-to-right scan consequence; fail-closed).
- [ ] Rewrite the dispatch-block NOTE to the softened form: the block is order-dependent by design, and a reorder can silently rebind `root` to another valid fixture dir (a root-sensitive pin would keep passing against the wrong fixture), so bind a local fixture root if a root-sensitive pin is ever added. Remove the "failures are loud" claim.
- [ ] Run → expect GREEN throughout (characterization + docstring edits): `python3 scripts/doc_registry_validator.py --selftest`.
- [ ] Commit: `doc-registry: pin pre-subcommand unknown flag and declare CLI deltas`

### Task 6: Drop the dead else in successor_cycles (origin 1 item 13)

Files:
- `scripts/doc_registry_validator.py`

The while/else `seen_done.update(walked)` duplicates the unconditional update
on the next line; the `else:` clause is dead. The existing
`test_successor_cycle_fails` characterization already protects cycle
detection.

- [ ] Run → expect GREEN (characterization before refactor): `python3 scripts/doc_registry_validator.py --selftest` (records `test_successor_cycle_fails` passing).
- [ ] Delete the `else:` clause and its indented update, keeping the unconditional `seen_done.update(walked)`.
- [ ] Run → expect GREEN: `python3 scripts/doc_registry_validator.py --selftest`.
- [ ] Commit: `doc-registry: drop dead else in successor_cycles`

### Task 7: Strip ephemeral review-round provenance tags (origin 1 item 15)

Files:
- `scripts/doc_registry_validator.py`

74 lines carry an F+digit token (grep `-cE "F[0-9]"` on 2026-09-13): 73
provenance tags (`r6 F4`, bare `F4:`, `(F8)`, `r6 F1;`, `r5 F3 second`, ...)
that a public-repo reader cannot resolve, plus the `# noqa: F401` lint
directive at the facts import, which is a lint suppression, not a provenance
tag, and stays. Tags close with `:`, `)`, `,`, `;`, or a space, so the sweep
makes no delimiter assumption (it excludes the noqa line instead). Git
history preserves provenance. babe974 cleaned fences and formatting, not
these tags.

- [ ] Inventory: `grep -nE "F[0-9]" scripts/doc_registry_validator.py` and rewrite every tag hit (all except the noqa line) to keep the semantic content while removing the token (for example `# r6 F4: a malformed audit note on a multiply-claimed src row is reported...` becomes `# A malformed audit note on a multiply-claimed src row is reported...`; docstring `(r5 F2)` parentheticals drop the parenthetical). Do not introduce new tags; do not change any string that a fixture pins (the pinned substrings contain no tags; verified 2026-09-13).
- [ ] Run → expect GREEN: `python3 scripts/doc_registry_validator.py --selftest`.
- [ ] Run the Validation Commands round-tag sweep → expect the clean pass (RED today: 73 tag lines remain after the noqa exclusion, so the two-stage sweep prints `FAIL: provenance round tag remains`; after this task only the noqa line survives the first grep and the sweep falls through clean).
- [ ] Commit: `doc-registry: strip ephemeral review-round provenance tags`

### Task 8: done Step 2.648 syncs and the facts_paths resolve CLI (origin 1 items 9, 11, 14)

Files:
- `scripts/facts_paths.py`
- `agents/skills/done/SKILL.md`

Step 2.648 re-implements facts resolution with inline sed (a fourth parsing
style), restates the full registered-src exemption contract that doc-hierarchy
owns, and its hard-findings list says "malformed audit-note tokens" where the
contract is "malformed or ill-dated". README was verified pointer-only
already, so it needs no edit.

- [ ] facts_paths: extend `main()` so `resolve <key>` prints `resolve_toml_key_raw(Path.cwd(), key)` output (empty string when unresolved) and returns 0; every other non-selftest argv keeps the usage exit 2 (update the usage line to `usage: facts_paths.py --selftest | resolve <key>`).
- [ ] facts_paths selftest: add a check that an isolated directory containing a minimal `.ai-playbook/facts.md` resolves `tmp_dir` through `main(["resolve", "tmp_dir"])` (capture stdout); the check MUST `os.chdir` into the isolated directory first and restore the original cwd in a `finally`, because `main()` resolves via `Path.cwd()` and a missing chdir would read the repo's real gitignored `facts.md` and can pass vacuously; also check that an unknown key resolves empty and that a non-resolve non-selftest argv still exits 2 with usage.
- [ ] done Step 2.648 command block: replace the inline sed with `FACTS_PATHS_SCRIPT="${FACTS_PATHS_SCRIPT:-${HOME}/.ai-playbook/scripts/facts_paths.py}"` and `TMP_DIR_2648="$(python3 "$FACTS_PATHS_SCRIPT" resolve tmp_dir 2>/dev/null || true)"`; the existing `${TMP_DIR_2648:-docs/tmp}` fallback is unchanged, so an absent or old facts_paths degrades exactly as the absent-facts.md case did (fail-open parity; document that in one sentence beside the block).
- [ ] done Step 2.648 intro: replace the full exemption restatement with a pointer whose distinctive phrase is `The prose SOT for the registered-src exemption is the doc-hierarchy skill`; keep the validator resolution and the run instructions.
- [ ] done hard-findings bullet: change `malformed audit-note tokens` to `malformed or ill-dated audit-note tokens`.
- [ ] Run → expect GREEN: `python3 scripts/facts_paths.py --selftest`, then `python3 scripts/doc_registry_validator.py --selftest` (untouched, still green).
- [ ] Commit: `skills: route done tmp_dir through facts_paths and sync audit wording`

### Task 9: Flat-RFC identity clause and ADR-0003 cost note (origin 1 items 7 + 12)

Files:
- `agents/skills/doc-hierarchy/SKILL.md`
- `docs/maintenance/document-registry.md` (comment header only)
- `docs/maintenance/project-decisions.md`

The identity-derivation spec assumes a leading `YYYY-MM-DD-` prefix; flat
`*-rfc.md` names (migration-complete service repos) have no clause. The
registry header comment repeats the scheme and must stay aligned. The
~158-row registry appends one derivable row per completion; the item offers
a derive-by-default tier or an accepted-cost record; the accepted-cost record
is the proportionate close and lands in ADR-0003.

- [ ] doc-hierarchy identity-derivation paragraph: append the clause `For flat RFC filenames without a date prefix (*-rfc.md), identity is the filename minus the .md extension and the trailing -rfc` (wording may be folded into the existing sentence; the grep pins `trailing -rfc`).
- [ ] Registry header comment: extend the identity-scheme sentence with the same trailing `-rfc` clause so the two statements of the scheme do not diverge.
- [ ] project-decisions ADR-0003 section: append a note recording that each completion appends one filesystem-derivable registry row by design and that this per-row append is an accepted ADR-0003 cost; the derive-by-default tier was considered and declined (decision date 2026-09-13).
- [ ] Run the Validation Commands wording pins for this task → all three pass (RED today: none of the three phrases exists yet).
- [ ] Commit: `docs: flat-RFC identity clause and ADR-0003 accepted-cost note`

### Task 10: Final validation

Files: none (validation only)

- [ ] Run the full Validation Commands block → every command exits 0.
- [ ] `git status --porcelain` shows only this plan's files modified relative to the session's own commits.
- [ ] Commit (only if earlier tasks left any unstaged plan-owned change): `doc-registry: residual close-out final validation`
