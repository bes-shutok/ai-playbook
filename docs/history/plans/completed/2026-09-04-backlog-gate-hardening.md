# Plan: Backlog-gate hardening (fixtures, symlink traversal, hot-dirs facts key)

Plan review: docs/reviews/2026-09-06-plan-review-backlog-gate-hardening-r10.md (latest plan-review, ready) | code-review loop: docs/reviews/2026-09-06-backlog-gate-hardening-code-review-r5.md (clean exit at the 5-round cap; 4 Low deferred to backlog)

Backlog origins (scope of record):

- `docs/history/backlog/2026-09-03-backlog-gate-absolute-home-fixture.md`
- `docs/history/backlog/2026-09-03-backlog-gate-parser-unavailable-fixture.md`
- `docs/history/backlog/2026-09-03-backlog-gate-symlink-dir-bypass.md`
- `docs/history/backlog/2026-09-03-backlog-gate-hot-dirs-facts-key.md`
- `docs/history/backlog/2026-09-03-backlog-gate-collapse-classification-tail.md`

Prior plan: `docs/plans/completed/2026-09-03-backlog-inbox-location-gate.md` (the gate these five items harden; archived).

## Terms

- **Hot dir**: a directory whose untracked contents rule 1 gates by filename shape. Defaults: `docs/maintenance`, `docs/architecture`, `docs/tmp` (module constant `HOT_DIRS`).
- **Backlog home**: the resolved `(backlog_dir, backlog_completed_dir)` pair from `.ai-playbook/facts.md`; rule 2 exempts pair-token files inside it.
- **Pair-token file**: a basename containing both `backlog` and `deferred` (case-insensitive); rule 2 fires on such files outside the backlog home.
- **Carve-out**: the `_tmp_carve_out` exemptions under `docs/tmp` (segment `execute-plan`, basename prefix `plan-requirements-`).
- **Traversal path**: the path as walked during the rule-1 scan; for a file found behind a symlinked directory it is the LINK path (for example `docs/maintenance/link/f.md`), not the resolved target path.
- **run_case fixture**: a selftest fixture function with an inner `run_case(name, ...)` helper building one throwaway git repo per case (pattern of `_selftest_degenerate_home_repo`).

## Assumptions

- assume `backlog_hot_dirs` is a quoted, whitespace/comma-separated STRING, not a TOML array; basis: `facts_paths.resolve_toml_key_raw` is scalar-only (regex `key = "value"`, `scripts/facts_paths.py:138`); probed 2026-09-04: an array value parses as None, i.e. silently missing.
- assume configured hot dirs REPLACE the defaults (not union); basis: origin item "externalize ... with the current three as fallback defaults".
- assume symlinked hot-dir entries whose resolved target stays inside the same hot dir are traversed; all other symlinked entries are flagged on stderr and skipped; the scan never leaves the hot dir; basis: origin item primary recommendation plus its "or flag it for manual review" alternative. A hot-dir ENTRY that is itself a symlink INSIDE the repo is still followed at the top level (pre-existing parity for the built-in defaults; the origin item scopes hardening to links INSIDE hot dirs); revised by review r7: an entry (any entry, defaults included) whose RESOLVED target lies OUTSIDE the repo root is skipped with a warning, because `backlog_hot_dirs` turns the entry set into per-repo facts-file input consumed by the shared `done` skill in every vendored repo, so top-level containment is enforced.
- assume a MISSING `backlog_hot_dirs` key falls back to defaults silently (the key is new; warning on every vendored repo would be permanent noise), while present-but-blank, invalid entries, and an empty effective set warn and fall back; basis: blank-key precedent in `resolve_backlog_home`.
- assume no external consumer of the script's internals; basis: repo-wide grep found only `skill_gate.py`'s unrelated same-named `classify_path`; the `done` skill Step 2.645 invokes the CLI only.
- assume no runtime-copy deploy step; basis: `~/.ai-playbook/scripts/check_backlog_inbox_location.py` is a symlink into the repo (verified 2026-09-04).
- assume the five origins move to `backlog_completed_dir` at execution completion via Task 6; basis: repo plan practice (validator-pass, summarizer round 2 plans).

## Gist & Examples

The gate script `scripts/check_backlog_inbox_location.py` works but has three blind spots and two untested branches. This plan closes the blind spots, pins the untested branches with selftest fixtures, and collapses a duplicated classification tail.

1. **Absolute/~ home fixture (test gap).** The absolute and `expanduser` arms of `resolve_backlog_home` have no fixture; a regression re-anchoring absolute facts values against the repo root would kill the rule-2 exclusion while `--selftest` stays green. New fixture `run_case` with three cases: absolute home inside the repo (exit 0, exclusion hits), absolute home outside the repo (rule 2 fires on a tracked pair-token file inside the repo), tilde home with `HOME` overridden (same). All three are GREEN today; they pin existing correct behavior.

2. **Parser-unavailable fixture (test gap).** No fixture drives the `facts_paths is None` ImportError branch. New fixture copies the script ALONE into a scratch dir, clears `PYTHONPATH`, and runs it over a git repo whose facts (present but necessarily ignored) configure a home that does NOT contain a committed pair-token violation; expects exit 1, the rule-2 line, and `facts parser unavailable` on stderr. With a working parser the same fixture would exit 0, so the assertion discriminates the branch.

3. **Hot-dirs facts key (behavior change).** `HOT_DIRS` hardcodes this repo's layout in a gate the shared `done` skill runs in every vendored repo; in a repo with a different layout rule 1 silently no-ops. New optional facts key (string form; the TOML parser is scalar-only by design):

   ```toml
   backlog_hot_dirs = "custom-hot docs/archive, plans-gated"
   ```

   The configured list replaces the defaults. Missing key: silent defaults. Blank, invalid entries (absolute, `.`, `..` itself or a path whose first segment is `..`; a name merely starting with `..` is valid), or an empty effective set: stderr warning plus fallback so rule 1 can never silently disable. Docstring and the README row document the key and the degradation.

   Before: `custom-hot/override-deferred-backlog.md` invisible to rule 1 (tracked, it fires rule 2 instead). After: `custom-hot/override-deferred-backlog.md: rule 1`; `docs/maintenance/...` no longer scanned (replace semantics).

4. **Symlinked hot-dir subdirectory bypass (behavior change).** Rule 1's `os.walk` never descends symlinked directories, so a misfiled inbox file behind such a symlink is invisible when its real path is invisible too (untracked, or hidden by a carve-out). Replacement explicit stack walk: symlinked dir entries resolving INSIDE the hot dir are traversed with link-path reporting and a visited-set for cycle safety; everything else (outside the hot dir, outside the repo, broken) is flagged on stderr (once per traversal encounter, not globally once) and skipped. `followlinks=True` stays banned (no escape from the scanned tree).

   Before: `docs/maintenance/link/linked-deferred-backlog.md` and `docs/tmp/evadelink/task-backlog-log.md` (a carve-out evasion) invisible. After: both reported as rule 1 under their link paths; a link resolving to `/outside` or to `docs/plans/hide` emits `warning: hot-dir symlink not traversed: ...` and is not scanned.

5. **Classification-tail collapse (refactor).** The rule-1 walk loop and the rule-2 `git ls-files` loop both do classify-then-`setdefault`. One `_record(rel_path, backlog_home, hot_dir_parts, violations)` helper replaces both tails, keeping setdefault first-wins semantics. Characterization witness: `_selftest_main_repo` already feeds tracked hot-dir files through BOTH loops and pins exactly-once rule-1 reporting.

Edge cases motivating design decisions: unresolved temp paths on symlinked macOS temp roots trip the degenerate-home guard, so absolute facts values in fixtures MUST be composed from `repo.resolve()`; symlink cycles are exercised with cross-links over REAL directories (never link-to-link, whose full `Path.resolve()` semantics under ELOOP are environment-dependent); permission-denied subdirectories keep `os.walk`'s skip semantics but now warn.

## Design Invariants (CR Guard)

- **No escape from the scanned tree**: the rule-1 traversal must never descend outside the hot dir; `followlinks=True` is banned; escape-adjacent links are flagged, not followed.
- **Rule-1 precedence**: rule 1 fires before the backlog-home exclusion (a configured home under a hot dir does not exempt files there); preserved by `_selftest_hot_dir_home_repo`.
- **First-wins classification**: an intersection file (tracked AND under a hot dir) reports exactly once, via `violations.setdefault` inside `_record` only.
- **Rule 1 never silently disables**: an empty or fully-invalid hot-dirs configuration falls back to the defaults with a warning, never to a zero-dir gate.
- **facts parser stays scalar-only**: `scripts/facts_paths.py` is not modified; the new key fits the existing single-string parser.

## Evaluation Criteria

**Quality dimensions:**

- correctness: `--selftest` green with four new fixture functions; tasks 4-5 record their RED-today state before the fix and GREEN after; real-repo scan exits 0.
- maintainability: classification has ONE helper path (`_record`); hot dirs resolve at ONE point (`resolve_hot_dirs`); `HOT_DIRS` remains the single default source (the derived `HOT_DIR_PARTS` constant is removed with Task 4).
- observability: every degraded configuration (blank key, dropped entry, empty effective set, parser unavailable) and every non-traversed hot-dir symlink emits a stderr warning with stable text.
- hermeticity: new fixtures isolate ambient state (`PYTHONPATH` cleared for the lone-copy run, `HOME` overridden for the tilde case, facts values composed from resolved paths).
- documentation: script docstring and README row state the key, its string form, and the fallback semantics.

**Done when:**

- The final Validation Commands block passes from the repo root.
- The five backlog origins sit under `docs/history/backlog/completed/` with `Status: done`.

**Ship when:**

- Vendored repos pick up the gate through their own registries; the runtime copy is already a repo symlink, so no deploy step exists. (External, prose only.)

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `scripts/check_backlog_inbox_location.py` (its selftest section is also the test surface for this plan)

**Docs:**

- `README.md` (the script's catalog row; hot-dirs key mention)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

- `docs/history/backlog/completed/2026-09-03-backlog-gate-*.md` (Task 6 git-mv destinations; the Status edits ride the renames)

**Out of scope; reject unless plan-related:**

- `scripts/facts_paths.py`; reason: parser stays scalar-only by design (string-delimiter key avoids array parsing)
- `agents/skills/done/SKILL.md`; reason: Step 2.645 CLI invocation unchanged
- `agents/skills/bootstrap-ai-playbook/SKILL.md`; reason: key is optional with defaults; the generated facts template is unchanged
- `scripts/skill_gate.py`; reason: its `classify_path` is an unrelated same-named function
- `docs/reviews/` staging artifacts; reason: review-loop scratch, not a plan deliverable

## Validation Commands

Interim gates run the selftest command only. The full block below is the FINAL gate (Task 6); earlier obligations it pins do not exist until Tasks 3-5 land.

```bash
cd "$(git rev-parse --show-toplevel)" || { echo "FAIL: not a repo"; exit 1; }
python3 scripts/check_backlog_inbox_location.py --selftest || { echo "FAIL: selftest"; exit 1; }
python3 scripts/check_backlog_inbox_location.py --repo-root . || { echo "FAIL: repo scan"; exit 1; }
grep -q "def _record(" scripts/check_backlog_inbox_location.py || { echo "FAIL: _record helper missing"; exit 1; }
test "$(grep -cE '^[[:space:]]+violations\.setdefault' scripts/check_backlog_inbox_location.py)" -eq 1 || { echo "FAIL: classification tail not collapsed (setdefault outside _record)"; exit 1; }
grep -q "def resolve_hot_dirs(" scripts/check_backlog_inbox_location.py || { echo "FAIL: resolve_hot_dirs missing"; exit 1; }
grep -q "def _iter_hot_dir_files(" scripts/check_backlog_inbox_location.py || { echo "FAIL: symlink traversal helper missing"; exit 1; }
grep -qF 'optional ``backlog_hot_dirs``' scripts/check_backlog_inbox_location.py || { echo "FAIL: hot-dirs key undocumented in script docstring"; exit 1; }
grep -qF '`backlog_hot_dirs`' README.md || { echo "FAIL: hot-dirs key undocumented in README row"; exit 1; }
if grep -q "followlinks=True" scripts/check_backlog_inbox_location.py; then echo "FAIL: banned followlinks=True present"; exit 1; fi
grep -qF 'hot-dir symlink not traversed' scripts/check_backlog_inbox_location.py || { echo "FAIL: escape-flag warning text missing"; exit 1; }
echo "validation: ok"
```

The `grep -cE '^[[:space:]]+violations\.setdefault'` count (anchored to indented code lines so a docstring mention inside `_record` cannot fail the gate) is 2 at authoring time (RED-today) and must be exactly 1 after Task 3 (only inside `_record`). The `followlinks=True` sweep guards future edits; the prescribed walk never contains it.

### Task 1: absolute/~ backlog-home anchoring selftest fixture

Files:
- `scripts/check_backlog_inbox_location.py` (selftest section)

- [x] Add `_selftest_absolute_home_repo(root, check)` with a run_case-style inner helper (mirror of `_selftest_degenerate_home_repo` + `_selftest_hot_dir_home_repo`); register it in the `run_selftest` fixture list after `hot_dir_home_repo`
- [x] `_selftest_absolute_home_repo#abs-inside`; given a git repo whose facts set `backlog_dir = "<repo>/abs-home"` and `backlog_completed_dir = "<repo>/abs-done"` as ABSOLUTE strings composed from `str(repo.resolve())`, with committed `abs-home/pair-deferred-backlog.md` and `abs-done/pair-deferred-backlog.md`, expects exit 0, `check_backlog_inbox_location: ok` on stdout, and no `warning` on stderr (the absolute-home exclusion must hit; an unresolved value on a symlinked temp root trips the degenerate guard, so the resolved composition is load-bearing)
- [x] `_selftest_absolute_home_repo#abs-outside`; given facts pointing both keys at `<tmp>/outside-home` (outside the repo) and a committed `docs/plans/outside-home-deferred-backlog.md` inside the repo, expects exit 1 with that path reported as rule 2, the outside-home file absent from stdout, AND stderr containing `of the repo root` plus `falling back` (mirrors the tilde-case discriminator: the outside-anchored absolute home trips the degenerate guard and the default home applies)
- [x] `_selftest_absolute_home_repo#tilde`; given facts `backlog_dir = "~/tilde-home"` and `backlog_completed_dir = "~/tilde-home/done"`, run via `_run_script(..., env_extra={"HOME": str(fakehome)})` where `fakehome/tilde-home/tilde-pair-deferred-backlog.md` exists outside the repo and `docs/plans/tilde-home-deferred-backlog.md` is committed inside, expects exit 1 with the rule-2 line for the committed file, the fakehome file absent from stdout, AND `of the repo root` plus `falling back` on stderr (the expanduser-arm discriminator: expansion anchors the home outside the fixture repo so the degenerate guard rejects it and the default home applies; a no-expansion regression anchors the literal `~/tilde-home` inside the repo, emits no such warning, and would fail this assertion)
- [x] Run → expect GREEN: `python3 scripts/check_backlog_inbox_location.py --selftest` (characterization: all three cases pass against today's implementation; every pre-existing fixture stays green) (a fourth and fifth arm, abs-outside-link and abs-rootlink, were added by the r3 review address pass)
- [x] Commit: `test: absolute/~ backlog-home anchoring selftest fixture`

### Task 2: facts-parser-unavailable selftest fixture

Files:
- `scripts/check_backlog_inbox_location.py` (selftest section)

- [x] Add `_selftest_parser_unavailable_repo(root, check)`: build a git repo whose facts set `backlog_dir = "inside-home"` (a home INSIDE the repo), commit the pair-token file at `inside-home/lone-parser-deferred-backlog.md` (INSIDE that configured home), `shutil.copy` the script ALONE into a scratch subdir (no `facts_paths.py` beside it), and run the copy with `--repo-root` via a direct `subprocess.run` (`_run_script` targets `__file__` and cannot run the copy; it also cannot DELETE env keys, and `env_extra={"PYTHONPATH": ""}` would inject an empty sys.path entry) under `env = {k: v for k, v in _clean_git_env().items() if k != "PYTHONPATH"}` (delete the key, never empty it) with `cwd=str(scratch_dir)` pinned, so no ambient `PYTHONPATH` or repo-adjacent `facts_paths.py` can satisfy the import
- [x] `_selftest_parser_unavailable_repo#facts-ignored`; given the scratch copy with no importable `facts_paths` and the fixture above, expects exit 1, `inside-home/lone-parser-deferred-backlog.md: rule 2` on stdout, and `facts parser unavailable` on stderr (the exit code discriminates the branch: with a working parser the file sits inside the configured home, is excluded, and the run exits 0; with the parser unavailable the default home does not contain it and rule 2 fires)
- [x] Run → expect GREEN: `python3 scripts/check_backlog_inbox_location.py --selftest` (characterization; the new fixture passes against today's ImportError branch)
- [x] Commit: `test: facts-parser-unavailable selftest fixture`

### Task 3: collapse duplicated classification tail

Files:
- `scripts/check_backlog_inbox_location.py`

- [x] Run → expect GREEN baseline: `python3 scripts/check_backlog_inbox_location.py --selftest` (characterization before refactor)
- [x] Extract `_record(rel_path, backlog_home, hot_dir_parts, violations)` performing classify-then-`violations.setdefault` (first-wins), and call it from BOTH the rule-1 walk loop and the rule-2 `git ls-files` loop; pass `HOT_DIR_PARTS` for now (Task 4 replaces the constant with per-repo parts in the same edit as its callers; the `hot_dir_parts` parameter is accepted-but-unconsumed at this commit by design (`classify_path` gains the parameter only in Task 4)). Characterization witness, no new fixture: `_selftest_main_repo` feeds tracked hot-dir files through both loops and pins exactly-once rule-1 reporting
- [x] Run → expect GREEN: `python3 scripts/check_backlog_inbox_location.py --selftest` (identical verdicts; `grep -c "violations.setdefault"` on the file must now be 1)
- [x] Commit: `refactor: collapse scan_repo classification tails into _record`

### Task 4: externalize hot dirs to a facts key

Files:
- `scripts/check_backlog_inbox_location.py`
- `README.md`

- [x] Add `_selftest_hot_dirs_key_repo(root, check)` with run_case-style cases:
- [x] `hot_dirs_key#override`; given facts `backlog_hot_dirs = "custom-hot"` with committed `custom-hot/override-deferred-backlog.md` AND committed `docs/maintenance/replaced-backlog.md` (single token, so rule 2 cannot fire on it either way), expects exit 1, `custom-hot/override-deferred-backlog.md: rule 1` reported, and `docs/maintenance/replaced-backlog.md` NOT reported (replace semantics: the configured list fully replaces the defaults; a union regression would flag it via rule 1)
- [x] `hot_dirs_key#blank`; given facts `backlog_hot_dirs = ""` with committed `docs/tmp/blank-deferred-backlog.md`, expects exit 1 with its rule-1 line and a `present but empty` warning on stderr (blank must not disable rule 1)
- [x] `hot_dirs_key#escaping-entry`; given facts `backlog_hot_dirs = "custom-hot,../outside docs/tmp"` (mixed comma and space separators, pinning the comma half of the split contract) with committed `custom-hot/kept-deferred-backlog.md` and `docs/tmp/kept-deferred-backlog.md`, expects exit 1 with both rule-1 lines and a stderr warning naming `../outside`
- [x] `hot_dirs_key#missing-entry`; given facts `backlog_hot_dirs = "custom-hot ghost-hot"` with committed `custom-hot/kept-deferred-backlog.md`, expects exit 1 with its rule-1 line and a `does not exist` warning naming `ghost-hot` (a lexically valid but absent entry must not silently no-op; the built-in defaults keep their silent absent-dir tolerance, key entries warn)
- [x] `hot_dirs_key#all-escaping`; given facts `backlog_hot_dirs = "../only"` with committed `docs/tmp/fallback-deferred-backlog.md`, expects exit 1 with its rule-1 line plus a `has no valid entries` warning on stderr (empty effective set falls back to defaults)
- [x] Run → expect RED: `python3 scripts/check_backlog_inbox_location.py --selftest` (today the key is ignored: the override case reports BOTH the default-dir file as rule 1 and the custom file as rule 2, since a tracked pair-token file outside the default backlog home fires rule 2; the `present but empty` warning does not exist; the escaping-entry case reports the custom-hot file as rule 2 instead of rule 1 and emits no drop warning)
- [x] Commit RED fixtures: `test: backlog_hot_dirs facts-key RED fixtures`
- [x] Implement `resolve_hot_dirs(repo_root) -> tuple[str, ...]`:

```python
def resolve_hot_dirs(repo_root: Path) -> tuple[str, ...]:
    """Hot dirs for rule 1: optional facts key, defaults as fallback.

    ``backlog_hot_dirs`` is an optional quoted string of repo-relative
    directories separated by whitespace and/or commas (the TOML fence
    parser is scalar-only; an array literal parses as missing). A missing
    key falls back to ``HOT_DIRS`` silently (normal vendored case);
    ``facts_paths`` unavailable also falls back silently (the parser
    warning already fired). ``~``-prefixed entries are expanduser-ed
    first; an expanded absolute result is dropped by the invalid-entry
    rule (sibling facts keys honor ``~``). Blank, invalid entries
    (absolute, ``.``, ``..``-prefixed), entries resolving to a
    nonexistent repo path, or an empty effective set warn and fall back
    so rule 1 never silently disables.
    """
    defaults = tuple(HOT_DIRS)
    if facts_paths is None:
        return defaults
    raw = facts_paths.resolve_toml_key_raw(repo_root, "backlog_hot_dirs")
    if raw is None:
        return defaults
    if not raw.strip():
        print("warning: backlog_hot_dirs present but empty in "
              ".ai-playbook/facts.md; falling back to defaults",
              file=sys.stderr)
        return defaults
    dirs: list[str] = []
    for entry in re.split(r"[,\s]+", raw.strip()):
        if not entry:
            continue
        entry = os.path.expanduser(entry)
        norm = os.path.normpath(entry)
        if os.path.isabs(norm) or norm == "." or norm.startswith(".."):
            print(f"warning: backlog_hot_dirs entry {entry!r} is not a "
                  "repo-relative directory; dropping it", file=sys.stderr)
            continue
        if not (repo_root / norm).is_dir():
            print(f"warning: backlog_hot_dirs entry {entry!r} does not "
                  "exist in the repo; dropping it", file=sys.stderr)
            continue
        if norm not in dirs:
            dirs.append(norm)
    if not dirs:
        print("warning: backlog_hot_dirs has no valid entries; "
              "falling back to defaults", file=sys.stderr)
        return defaults
    return tuple(dirs)
```

- [x] Thread per-repo hot dirs through the scan: `scan_repo` computes `hot_dirs = resolve_hot_dirs(repo_root)` once plus `hot_dir_parts = tuple(tuple(h.split("/")) for h in hot_dirs)`; for EACH hot dir, before walking, enforce top-level containment: `if not (repo_root / hot).resolve().is_relative_to(repo_root):` print `warning: hot dir '<hot>' resolves outside the repo root; skipping` on stderr and `continue` (the facts key turns the entry set into per-repo input consumed by the shared `done` skill, so lexical `..` validation alone is insufficient because a committed symlinked entry must not walk outside the repo; see the revised symlink assumption); the rule-1 loop iterates the surviving `hot_dirs`; `classify_path` gains a `hot_dir_parts` parameter and matches hot-dir membership by PREFIX of arbitrary segment count: `under_hot = any(path.parts[:len(hp)] == hp for hp in hot_dir_parts)` (the current `path.parts[:2] in HOT_DIR_PARTS` slice hard-assumes two-segment dirs and misclassifies a one-segment configured dir like `custom-hot`); `_record` passes the parts through. `HOT_DIRS` remains the default constant; delete the now-unconsumed derived `HOT_DIR_PARTS` together with its single-source comment in the same edit, since `classify_path` takes per-repo parts and `resolve_hot_dirs` reads `HOT_DIRS` directly
- [x] Add `import re` to the module imports; leave `_tmp_carve_out` unchanged (inert unless `docs/tmp` is among the active hot dirs); extend the module docstring with a hot-dirs paragraph containing the exact phrase `optional ``backlog_hot_dirs`` key` (whitespace/comma-separated string, repo-relative, replace semantics, fallback rules); extend the README row for the script with a `backlog_hot_dirs` mention in single backticks
- [x] Run → expect GREEN: `python3 scripts/check_backlog_inbox_location.py --selftest` (all five new cases flip GREEN; every pre-existing fixture stays green since none sets the key) (a sixth arm, escaping-top-level, was added by the r1 review address pass; a seventh arm, dotdot-prefixed-name, was added by the r4 address pass, aac741e, pinning the first-segment semantics)
- [x] Commit: `feat: externalize backlog-gate hot dirs to backlog_hot_dirs facts key`

### Task 5: traverse in-hot-dir symlinks, flag escaping links

Files:
- `scripts/check_backlog_inbox_location.py`

- [x] Add `_selftest_hot_dir_symlink_repo(root, check)` with cases:
- [x] `symlink#link-path reported`; given `docs/maintenance/realdir/linked-deferred-backlog.md` and symlink `docs/maintenance/link -> realdir`, expects exit 1 with BOTH `docs/maintenance/realdir/linked-deferred-backlog.md: rule 1` AND `docs/maintenance/link/linked-deferred-backlog.md: rule 1` (the link-path form is the regression witness; probed 2026-09-04: absent today)
- [x] `symlink#carve-out evasion`; given `docs/tmp/execute-plan/someplan/task-backlog-log.md` (allowed at its real path by the carve-out) and symlink `docs/tmp/evadelink -> execute-plan/someplan`, expects `docs/tmp/evadelink/task-backlog-log.md: rule 1` (the carve-out must not be evadable through a symlink)
- [x] `symlink#escape flagged not scanned`; given symlink `docs/maintenance/outsidelink -> <tmp>/outside-dir` containing `outside-deferred-backlog.md`, and symlink `docs/maintenance/escapelink -> ../plans/hide` (inside the repo, outside the hot dir) containing `hidden-backlog-notes.md`, expects exit 0 (no violation anywhere), stderr containing `hot-dir symlink not traversed` for both links, and NEITHER target file reported on stdout
- [x] `symlink#cycle visited-set terminates`; given real dirs `docs/maintenance/a` and `docs/maintenance/b`, symlinks `docs/maintenance/la -> b`, `docs/maintenance/lb -> a`, and `docs/maintenance/b/lc -> ../a` (symlink targets are relative to the link's own directory), run via a `_run_script` `timeout` parameter (60s, `subprocess.TimeoutExpired` counts as failure), expects the run to complete with exit 0, no violations, and NO `hot-dir symlink not traversed` warning on stderr (already-visited targets are skipped silently; the flag text means escaping or broken only; probed 2026-09-04: the prescribed walk emits no flag over this scenario; link-to-link loops are deliberately avoided because `Path.resolve()` semantics under ELOOP are environment-dependent)
- [x] `symlink#file-link parity`; given `docs/plans/plain-notes.txt` and symlink `docs/maintenance/filelink-deferred-backlog.md -> ../plans/plain-notes.txt`, expects `docs/maintenance/filelink-deferred-backlog.md: rule 1` (characterization: os.walk classifies symlinked files under their link basename today, and the stack-walk rewrite must keep that parity via the symlinked-file yield branch)
- [x] `symlink#broken`; given symlink `docs/maintenance/brokenlink -> ../nonexistent`, expects exit 0 with no violations and stderr containing `hot-dir symlink not traversed` naming the link (pins the broken-symlink flag arm, the most common real-world symlink state)
- [x] The `except OSError` read-error arm (`cannot read hot-dir subtree`) is deliberately waived from fixture coverage: portable permission simulation is platform-dependent (chmod-000 is unreliable under root/Windows); the waiver is recorded here rather than leaving the branch silently uncovered
- [x] Run → expect RED: `python3 scripts/check_backlog_inbox_location.py --selftest` (probed 2026-09-04: link-path and evasion lines absent; no flags emitted; the timeout parameter does not exist yet, so add it in the same RED commit)
- [x] Commit RED fixtures: `test: hot-dir symlink traversal RED fixtures` (folded into the Task 5 feat commit 4e5db9b; RED state captured in the task-5 implement log)
- [x] Replace the rule-1 `os.walk` with an explicit stack walk:

```python
def _flag_untraversed(entry: Path) -> None:
    print(f"warning: hot-dir symlink not traversed: {entry}", file=sys.stderr)


def _iter_hot_dir_files(hot_path: Path):
    """Yield file paths under hot_path along their traversal path.

    Symlinked dir entries resolve against the hot-dir root: targets inside
    the hot dir are traversed (link-path reporting, visited-set cycle
    safety); targets outside are flagged on stderr and skipped, so the
    walk never leaves the hot dir (followlinks stays off). Symlinked
    files yield under their link name (os.walk parity); broken symlinks
    are flagged; already-visited targets are skipped silently. The stack
    carries (link_path, resolved_dir) pairs and iterates the RESOLVED
    directory captured at containment-check time, so a post-check symlink
    swap cannot redirect the read (TOCTOU hardening; a real directory
    itself being swapped for a symlink after the check is an accepted
    residual). Directory read errors warn and skip the subtree,
    preserving os.walk's tolerance. A target reachable through several
    routes is flagged once per traversal encounter, not globally once.
    """
    root = hot_path.resolve()
    stack = [(hot_path, root)]
    visited = {root}
    while stack:
        dirpath, real = stack.pop()
        try:
            entries = sorted(real.iterdir())
        except OSError as exc:
            print(f"warning: cannot read hot-dir subtree {dirpath}: {exc}",
                  file=sys.stderr)
            continue
        for entry_real in entries:
            entry = dirpath / entry_real.name
            if entry_real.is_symlink():
                try:
                    resolved = entry_real.resolve()
                except OSError:
                    _flag_untraversed(entry)
                    continue
                if resolved.is_dir():
                    if not resolved.is_relative_to(root):
                        _flag_untraversed(entry)
                    elif resolved not in visited:
                        visited.add(resolved)
                        stack.append((entry, resolved))
                elif resolved.exists():
                    yield entry
                else:
                    _flag_untraversed(entry)
                continue
            if entry_real.is_dir():
                stack.append((entry, entry_real))
            elif entry_real.is_file():
                yield entry
```

- [x] Rewire the rule-1 loop: `for absolute in _iter_hot_dir_files(hot_path): rel = os.path.relpath(absolute, repo_root); _record(rel, backlog_home, hot_dir_parts, violations)`; files behind a traversed symlink surface under their LINK path, which is what the two link-path witnesses assert; keep the existing `if not hot_path.is_dir(): continue` guard ahead of the walk call (only the os.walk body is replaced; absent hot dirs stay silently tolerated, and no fixture asserts a `cannot read hot-dir subtree` warning for them)
- [x] Run → expect GREEN: `python3 scripts/check_backlog_inbox_location.py --selftest` (all six symlink cases flip GREEN; every pre-existing fixture stays green) (a seventh arm, default-dir-escape, was added by the r2 review address pass)
- [x] Extend the module docstring's rule-1 paragraph with one sentence covering in-hot-dir symlink traversal, link-path reporting, and the `hot-dir symlink not traversed` / `cannot read hot-dir subtree` warning texts (Task 4's docstring edit covers only the `backlog_hot_dirs` key)
- [x] Commit: `feat: traverse in-hot-dir symlinks, flag escaping hot-dir links`

### Task 6: validation and backlog archival

Files:
- `docs/history/backlog/2026-09-03-backlog-gate-absolute-home-fixture.md` (moves to `docs/history/backlog/completed/`)
- `docs/history/backlog/2026-09-03-backlog-gate-parser-unavailable-fixture.md` (moves)
- `docs/history/backlog/2026-09-03-backlog-gate-symlink-dir-bypass.md` (moves)
- `docs/history/backlog/2026-09-03-backlog-gate-hot-dirs-facts-key.md` (moves)
- `docs/history/backlog/2026-09-03-backlog-gate-collapse-classification-tail.md` (moves)

- [x] Run the full Validation Commands block from the repo root → expect every line green ending in `validation: ok`
- [x] `git mv` each of the five origin files to `docs/history/backlog/completed/` and set `Status: done` in the same edit (the two fixture files gain a `Status: done` header line; the three code items flip `Status: open` to `Status: done`); keep every other header line intact
- [x] Commit the archival: `chore: archive backlog-gate hardening origins to completed`
- [x] UL#277 guard: verify each committed destination carries its Status edit via `git show <sha>:docs/history/backlog/completed/<name>` (a rename-only commit with the content edits left unstaged is the known trap; amend if the edits did not land)
