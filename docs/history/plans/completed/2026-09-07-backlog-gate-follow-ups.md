# Plan: backlog-gate follow-ups (Windows portability + r5 doc drift)

Backlog origin: `docs/history/backlog/2026-09-07-backlog-gate-windows-portability.md` (primary, behavior surface) and `docs/history/backlog/2026-09-07-backlog-gate-r5-doc-drift.md` (documentation annotations). Source review: `docs/reviews/2026-09-06-backlog-gate-hardening-code-review-r5.md` (findings F1-F4, all Low, deferred at the round cap).

## Terms

- hot dir: a rule-1 scanned directory, from the optional `backlog_hot_dirs` facts key or the built-in `HOT_DIRS` defaults.
- backlog home: the resolved `(backlog_dir, backlog_completed_dir)` pair anchoring the rule-2 exclusion.
- arm: one independent fixture case inside a `_selftest_*` function.
- winport probe: the new in-process Windows-portability selftest checks introduced by Task 1 (gate-unique labels `winport#...`).

## Assumptions

- assume the repo copies under `scripts/` are canonical for this work (the `~/.ai-playbook/scripts` runtime tree is a symlink farm into the repo; runtime redeploy is out of scope); basis: repo runtime-registry model.
- assume no Windows host is available in this workflow, so the two Windows-specific branches are verified by in-process probes: the portable segmentation helper is exercised directly on POSIX, and the cross-drive branch is exercised by patching `os.path.relpath` to raise `ValueError`; basis: the deferral rationale in both backlog items.
- assume the archived-plan edits are annotation-only; the embedded `resolve_hot_dirs` code snippet in `docs/plans/completed/2026-09-04-backlog-gate-hardening.md` stays frozen as the historical prescription; basis: the backlog item's explicit carve-out.
- assume POSIX gate behavior is unchanged for all realistic entries: on POSIX a backslash is a literal filename character, `os.path.relpath` never raises `ValueError` for in-repo paths, and the one behavioral exception (a configured entry naming a directory whose name literally contains a backslash stops matching; see the Gist) is an accepted trade; basis: r5 F1/F2 analysis.
- assume the seventh hot-dirs arm (`dotdot-prefixed-name`) was added by commit aac741e (r4 address pass); basis: `git show --stat aac741e` (verified at authoring time).

## Gist & Examples

Two portability holes in `scripts/check_backlog_inbox_location.py` only manifest on Windows, where the gate cannot be empirically tested in this workflow; this plan converts both crash/silent-inert modes into the documented warn-and-fallback or portable-segmentation behavior, verified through in-process probes that run on any host. On top of that, two documentation residues from the same r5 exit are folded in as the second task.

**Hot-dir segmentation (r5 F1).** `resolve_hot_dirs` validates entries with `os.path.normpath`, which on Windows yields native backslash separators, but `scan_repo` builds the segment tuples with `h.split("/")`. A configured entry like `docs\maintenance` therefore passes validation yet never matches `Path.parts`.

- Before (today, Windows): `backlog_hot_dirs = "docs\\maintenance"` warns nowhere, passes every validation branch, and `hot_dir_parts` becomes `("docs\\maintenance",)` (one segment); no scanned path's parts ever match, so rule 1 silently ignores that hot dir while the rest of the gate stays up.
- After (this plan): segmentation normalizes separators before splitting (`\` to `/` then split), so the tuple is `("docs", "maintenance")`, the walk fires rule 1 for token files under it, and the never-silently-disables invariant holds on Windows too. On POSIX the normalization changes behavior only in the theoretical case of a configured entry naming a real directory whose name literally contains a backslash: today's `split("/")` matches such a directory, the helper's tuple never does (the entry goes silently inert, the same invariant class this plan closes). The trade is accepted: repo-relative directory names with literal backslashes are not a real-world configuration on POSIX, and honoring them would forfeit the Windows fix; the "POSIX unaffected" framing elsewhere in this plan means "unchanged for all realistic entries", and the invariant cost is recorded here rather than hidden.

**Cross-drive relpath (r5 F2).** `resolve_backlog_home` computes `os.path.relpath(home, repo_root)` before its degenerate and containment guards. On Windows, a facts value resolving to a different drive makes `os.path.relpath` raise an uncaught `ValueError`.

- Before (today, Windows): a cross-drive `backlog_dir` crashes the gate with a traceback instead of the documented warn-and-fallback; exit is nonzero but for the wrong reason, and the run dies mid-resolution.
- After (this plan): the relpath computation catches `ValueError` and treats it as the degenerate case: the standard warn-and-fallback fires (`resolves outside the repo root` family warning, default home applied), so rule 2 keeps gating with the default home. This matches the existing resolved-containment branch, which would reject a cross-drive home anyway; the guard order just arrives there without crashing.

**Doc drift (r5 F3/F4).** `_selftest_hot_dirs_key_repo`'s docstring says "Six arms:" but enumerates only six of the now-seven arms (`dotdot-prefixed-name` was added by aac741e); the archived hardening plan's Gist item 3 still says invalid entries are "`..`-prefixed" (shipped semantics: `..` itself or a path whose FIRST segment is `..`; a name merely starting with `..` is valid), and Task 4's GREEN-line annotation stops at the sixth arm. Both get one-line annotation fixes; the archived plan's embedded code snippet intentionally stays as the historical prescription.

Edge cases motivating the design: the segmentation helper must tolerate entries that already use forward slashes (the POSIX and default case) and mixed values; the `ValueError` fallback must land on the same default-home path as the existing degenerate branches so downstream behavior is identical; and the new probes must be exception-contained so the RED run records a labeled FAIL instead of aborting the selftest harness.

## Evaluation Criteria

**Quality dimensions:**

- correctness: `python3 scripts/check_backlog_inbox_location.py --selftest` exits 0 including the two new winport probes; no pre-existing fixture regresses.
- portability fidelity: the segmentation helper produces the documented parts tuple for a backslash entry when run on POSIX (the normalization is host-independent); the cross-drive branch is reachable via the patched-relpath probe and lands on the default home with a stderr warning.
- consistency: the fixture docstring arm count matches the enumerated arms; the archived-plan annotations match the shipped first-segment semantics without touching the frozen snippet.
- minimalism: no POSIX behavior change beyond the accepted theoretical literal-backslash case recorded in the Gist, no new dependencies, and no new TOP-LEVEL module imports (the winport probe uses function-local `unittest.mock` and `contextlib` imports, matching the existing function-local `tempfile` pattern in `run_selftest`).

**Done when:**

- The full selftest exits 0 with the `winport#hot-dir-backslash-parts` and `winport#cross-drive-relpath-fallback` probes present and passing.
- `scripts/check_backlog_inbox_location.py` contains no "Six arms" text; the "Seven arms:" line enumerates arm 7 (`dotdot-prefixed-name`).
- The archived plan carries the first-segment Gist wording and the seventh-arm/r4 annotation parenthetical; all Validation Commands pass.

**Ship when:**

- External prerequisite (prose only; never a plan checklist task and no exception receipt is sought): a Windows-host run of `python3 scripts/check_backlog_inbox_location.py --selftest` passing. Ownership: whoever next runs the gate on a Windows host (a future Windows-support pass); no Windows host exists in this workflow, so this is not repository-verifiable and stays out of the executable checklist.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `scripts/check_backlog_inbox_location.py` (scoped: the new `_hot_dir_parts` helper, its single `scan_repo` call site, the `relpath` computation block in `resolve_backlog_home`, the new `_selftest_windows_portability` function, the `run_selftest` registration line, and the `_selftest_hot_dirs_key_repo` docstring count line plus its appended arm-7 enumeration sentence only)

**Tests:**

- `scripts/check_backlog_inbox_location.py` selftest additions live in the same file (the `_selftest_windows_portability` probes above); all other `_selftest_*` functions and fixtures are frozen; reject any review finding that touches them

**Documentation:**

- `docs/plans/completed/2026-09-04-backlog-gate-hardening.md` (annotations only: Gist item 3 sentence and the Task 4 GREEN-line parenthetical; the embedded code snippet and every other line are frozen; reject any finding that edits the snippet or rewords completed history elsewhere)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `README.md`; reason: no behavior or contract change to document (the `backlog_hot_dirs` row already describes the key).
- `scripts/facts_paths.py`; reason: the facts parser is untouched by both fixes.
- `~/.ai-playbook/scripts/*` runtime copies; reason: symlink-farmed from the repo; redeploy is a separate operational step, not plan work.

## Validation Commands

```bash
set -u
REPO="$(git rev-parse --show-toplevel)"
SCRIPT="$REPO/scripts/check_backlog_inbox_location.py"
PLAN="$REPO/docs/plans/completed/2026-09-04-backlog-gate-hardening.md"

test -f "$SCRIPT" || { echo "FAIL: missing $SCRIPT"; exit 1; }
test -f "$PLAN" || { echo "FAIL: missing $PLAN"; exit 1; }

# 1. Full selftest, including the two winport probes (Task 1 RED, Task 2 GREEN).
python3 "$SCRIPT" --selftest || { echo "FAIL: selftest not green"; exit 1; }

# 2. Fixture docstring count fix (Task 3): arm 7 enumerated, "Six arms" gone.
grep -Fq 'Seven arms: (1) override' "$SCRIPT" \
  || { echo 'FAIL: Seven arms docstring line missing'; exit 1; }
if grep -Fn 'Six arms' "$SCRIPT"; then
  echo 'FAIL: stale Six arms docstring'; exit 1
fi

# 2b. Call-site wiring pin (Task 2): the inline split must be gone from
# scan_repo; only the helper performs segmentation. The fixed string
# 'h.split("/")' cannot match the helper body ('...").split("/")'), so a
# zero-match sweep here is meaningful.
if grep -Fn 'h.split("/")' "$SCRIPT"; then
  echo 'FAIL: inline hot-dir split still present; scan_repo not rewired'
  exit 1
fi

# 3. Archived-plan annotations (Task 3): first-segment Gist wording and the
# seventh-arm/r4 parenthetical. The embedded snippet stays untouched.
grep -Fq 'itself or a path whose first segment is' "$PLAN" \
  || { echo 'FAIL: Gist first-segment amendment missing'; exit 1; }
grep -Fq 'seventh arm, dotdot-prefixed-name' "$PLAN" \
  || { echo 'FAIL: seventh-arm annotation parenthetical missing'; exit 1; }
# The legacy Gist clause must be gone (single-backtick form; the frozen
# snippet's double-backtick ``..``-prefixed text cannot match this fixed
# string and stays untouched).
if grep -Fn '`..`-prefixed' "$PLAN"; then
  echo 'FAIL: legacy ..-prefixed Gist clause still present'; exit 1
fi

echo "validation ok"
```

### Task 1: RED winport probes in the selftest

Files:

- `scripts/check_backlog_inbox_location.py`

- [x] `_selftest_windows_portability#hot-dir-backslash-parts`; given the new module-level helper called as `_hot_dir_parts(("docs\\maintenance", "docs/tmp"))`, expects the return value `(("docs", "maintenance"), ("docs", "tmp"))`; contained in a new `_selftest_windows_portability(root, check)` function; today the helper does not exist, so wrap BOTH `_hot_dir_parts` invocations in a SINGLE `try/except NameError` block (an undefined module-level function raises `NameError`, not `AttributeError`) that records the one FAIL label `check(False, "winport#hot-dir-backslash-parts: _hot_dir_parts helper missing")` on the error path, keeping the probe's label count at exactly one (exception-contained RED, per the selftest harness contract); given a forward-slash entry the same call must return `(("docs", "tmp"),)` unchanged
- [x] `_selftest_windows_portability#cross-drive-relpath-fallback`; given a fixture repo with facts `backlog_dir = "docs/history/backlog/"` and `backlog_completed_dir = "docs/history/backlog/completed/"` (reuse the `run_case`-style scaffold pattern of the sibling fixtures), with `os.path.relpath` patched to `raise ValueError` for the duration of a single `resolve_backlog_home(repo_root)` call (patch via `unittest.mock.patch("os.path.relpath", side_effect=ValueError)` inside `try/finally`, capturing stderr with `contextlib.redirect_stderr`), expects the returned pair to equal the two default homes `(repo_root / "docs/history/backlog", repo_root / "docs/history/backlog/completed")` and the captured stderr to contain `falling back`; today the `ValueError` propagates, so contain the call in `try/except ValueError` and `check(False, "winport#cross-drive-relpath-fallback: uncaught ValueError (no fallback)")`
- [x] Register `_selftest_windows_portability` in the `run_selftest` tuple between `hot_dirs_key_repo` and `hot_dir_symlink_repo`
- [x] Run → expect RED: `python3 scripts/check_backlog_inbox_location.py --selftest` exits 1 with exactly the two new `winport#...` FAIL labels on stderr and every pre-existing fixture still passing (no other label may fail at this point)
- [x] Commit: `test: winport RED probes for portable hot-dir segmentation and cross-drive relpath fallback`

### Task 2: GREEN portable segmentation + cross-drive fallback

Files:

- `scripts/check_backlog_inbox_location.py`

- [x] Add the module-level helper `def _hot_dir_parts(hot_dirs):` returning `tuple(tuple(h.replace("\\", "/").split("/")) for h in hot_dirs)` with a docstring noting separator normalization keeps Windows-native entries matchable against `Path.parts` and matches forward-slash entries exactly as before
- [x] Replace the inline computation in `scan_repo` (`hot_dir_parts = tuple(tuple(h.split("/")) for h in hot_dirs)`) with a call to `_hot_dir_parts(hot_dirs)`; no other call site exists (verified at authoring time)
- [x] In `resolve_backlog_home`, wrap the `rel = os.path.relpath(home, repo_root)` computation in `try/except ValueError`: on `ValueError` print `warning: {key} resolves outside the repo root; falling back to {default}` on stderr and set `home = None` (same fallback path and wording family as the existing degenerate/containment branches); the existing degenerate and containment checks keep their current order and semantics on the non-error path
- [x] Run → expect GREEN: `python3 scripts/check_backlog_inbox_location.py --selftest` exits 0 with zero FAIL labels (both winport probes flipped; every pre-existing fixture, including the winport sibling arms added in Task 1, stays green)
- [x] Commit: `fix: portable hot-dir segmentation and cross-drive relpath fallback in backlog gate`

### Task 3: doc-drift annotations (non-behavior)

Files:

- `scripts/check_backlog_inbox_location.py`
- `docs/plans/completed/2026-09-04-backlog-gate-hardening.md`

- [x] In the `_selftest_hot_dirs_key_repo` docstring, change "Six arms:" to "Seven arms:" and append the arm-7 enumeration sentence after arm (6): `(7) dotdot-prefixed-name - a real in-repo directory whose NAME starts with ``..`` is honored, pinning the first-segment escape test` (single docstring line edit; no fixture code changes)
- [x] In the archived plan's Gist item 3, replace the clause "invalid entries (absolute, `.`, `..`-prefixed)" with "invalid entries (absolute, `.`, `..` itself or a path whose first segment is `..`; a name merely starting with `..` is valid)" (annotation only; the embedded `resolve_hot_dirs` snippet on the neighboring lines stays byte-identical as the historical prescription)
- [x] In the archived plan's Task 4 GREEN line, extend the existing parenthetical to "(a sixth arm, escaping-top-level, was added by the r1 review address pass; a seventh arm, dotdot-prefixed-name, was added by the r4 address pass, aac741e, pinning the first-segment semantics)"
- [x] Run → expect GREEN: the full Validation Commands block above passes (selftest stays green from Task 2; the five doc pins flip green in this task)
- [x] Commit: `docs: backlog-gate r5 doc-drift annotations (arm counts, first-segment semantics)`
