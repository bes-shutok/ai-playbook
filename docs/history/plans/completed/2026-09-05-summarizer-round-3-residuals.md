# Plan: summarizer round-3 residuals

Backlog origins (scope of record, read in full from `docs/history/backlog/`):

- `docs/history/backlog/2026-09-04-summarizer-dirfd-flag-constant.md` (item 1)
- `docs/history/backlog/2026-09-05-summarizer-read-path-ancestor-dirfd.md` (item 2)
- `docs/history/backlog/2026-09-04-summarizer-set-based-retry-delta.md` (item 3)
- `docs/history/backlog/2026-09-05-summarizer-lag-arm-classes-witness.md` (item 4)
- `docs/history/backlog/2026-09-05-missing-parent-arm-path-predicate.md` (item 5)

## Terms

- **Parent-dirfd scaffold**: the hand-copied block inside a private-path helper that opens `path.parent` with `os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC`, applies the r2 F2 errno-split translation, and closes the fd in a `finally`. Four copies exist today (`tighten_parent_ai_playbook`, `ensure_private_dir`, `create_private_file_exclusive`, `_atomic_write_private`).
- **`_pinned_parent(parent, refusal_text)`**: the shared context manager this plan introduces. Opens the parent with the pinned flags, translates `ELOOP`/`ENOTDIR` to `PermissionsError(refusal_text)` and every other errno to `PermissionsError(f"cannot open parent directory: {parent}: {exc}")`, yields the fd, and closes it in a `finally`.
- **Chronic unreadable**: a sidecar already in `ledger["unreadable"]` at the initial conservation pass (unparseable before `cmd_init_baseline`). Not retry-induced.
- **Retry-delta (set-based)**: the retry-induced parse-drop population computed as a set difference `unparseable_now - chronic`, replacing the count subtraction `dropped - len(ledger["unreadable"])`.
- **Ledger-pinned classes**: the stdout `classes=` summary tail derives from the pre-race classification ledger, never from the refreshed publish-time buffers.
- **Skill-gate marker**: consent marker per `agents/hooks/skill-gate/README.md` (plans class); refreshed on every plan-file write via the `skill_gate.py --write-marker` CLI with `project` from `facts_paths.resolve_project_key` and `session` from the `session_channel.py` subprocess (empty-after-strip becomes `no-session`).
- **Session key**: the value returned by `python3 ~/.ai-playbook/scripts/session_channel.py`; hashed `sha1(value)[:16]` when non-empty.

## Assumptions

- assume the archived round-2 plan `docs/plans/completed/2026-09-02-summarizer-hardening-round-2.md` is amended in place in the same change where its pinned wording would falsify (Validation Commands block in Task 2, Task 3 GREEN bullet in Task 3); basis: the user prompt and both backlog items 1 and 3 explicitly require the same-change amendment because that block operates as a living regression gate.
- assume the shared manager takes a per-caller `refusal_text` parameter instead of unifying the four refusal messages; basis: the message contracts deliberately differ (`tighten_parent_ai_playbook` says `parent is not a directory: {parent}`, the other three say `refusing symlinked parent: {path.parent}`) and pinned selftest messages must not drift.
- assume `read_private_file`'s parent-open refusal reuses the sibling wording `refusing symlinked parent: {path.parent}` while the final-component `ELOOP`/`ENOTDIR` keeps the existing `refusing to follow symlink target: {path}` message; basis: backlog item 2 ("with the r2 F2 errno translation ... translating ELOOP/ENOTDIR-family errnos to the existing PermissionsError message") plus the sibling helpers' established contract.
- assume the retry-drop note literal keeps the f-string variable name `delta` (`dropped {delta} unparseable sidecar(s) (retry-induced)`), computed as `delta = len(retry_drops)`; basis: the round-2 Validation block pins that literal (`grep -q 'dropped {delta} unparseable'`), so keeping the name keeps that pin green without an extra amendment.
- assume the lag-arm's second sidecar (`y.stats.json`) is introduced at the lag arm and `unlink()`-ed after the arm, restoring the single-sidecar corpus the later arms were written against; basis: minimal-coupling choice, keeps every downstream arm's pinned expectations byte-identical.
- assume the new parent-open failure semantics for `read_private_file` (a missing or non-directory parent now raises `PermissionsError("cannot open parent directory: ...")` where a raw `OSError` propagated before); basis: the sibling create/tighten helpers already fail closed exactly this way, and every caller treats any exception as a read failure.
- assume the final-component open in `read_private_file` translates `ENOTDIR` alongside `ELOOP` to the existing `refusing to follow symlink target: {path}` message, where today only `ELOOP` is translated at that site; basis: darwin returns `ENOTDIR` for an `O_NOFOLLOW` symlink open (the same family join the sibling helpers already apply), the message text itself is unchanged, and the behavior only fires in the pre-check-bypassed race window.

## Gist & Examples

Five deferred review findings in `scripts/summarize_review_stats.py` land together because three of them share one mechanism.

**Items 1+2 (one pattern).** Four helpers hand-copy the same parent-dirfd scaffold, and the read path never got it at all. Before (today): `read_private_file` opens the full path string `os.open(str(path), O_RDONLY | O_NOFOLLOW | O_CLOEXEC)`, so `O_NOFOLLOW` guards only the final component; an attacker who can write to an ancestor directory can swap in a symlink after the `_reject_symlink` pre-check and redirect the read. After (this plan): a single `_pinned_parent` context manager owns the pinned parent open, the errno-split refusal translation, and the close; the four create/tighten helpers call it instead of their local copies, and `read_private_file` opens the parent through it, then opens the final component `dir_fd`-relative with `O_NOFOLLOW`. Before: `_pinned_parent` does not exist and `grep -c "_pinned_parent(" scripts/summarize_review_stats.py` is 0; after: it is at least 6 (def plus five call sites) and no helper body contains `os.open(str(...))` for the parent any more.

**Item 3.** Before: the parse-drop note computes `delta = dropped - len(ledger["unreadable"])`. Mask scenario: sidecar B is chronically unreadable, sidecar A is healthy; during the retry window the hook repairs B and breaks A. `dropped` is 1, the chronic count is 1, `delta` is 0, and the note stays silent even though a genuine retry-induced drop of A occurred. After: the note is driven by the set difference `unparseable_now - chronic`; A is unparseable now and not chronic, so the note fires with count 1. The published note wording is unchanged.

**Item 4.** The lag arm's classes-half assertion (`_classes_of(lag_out) == base_classes`) is a weak witness: its payload rewrite keeps class membership identical, so the regressed implementation (recomputing the classes summary from refreshed buffers) passes it too. After: the hook simultaneously rewrites a second, valid sidecar to unparseable bytes at the publish gate. In a refreshed-ledger world that sidecar would move into `unreadable` and change the tail, so only the regression changes the tail; the correct (ledger-pinned) implementation still prints the baseline tail and the check discriminates.

**Item 5.** The missing-parent arm asserts the message contains `str(missing_parent)`, but for the three child-taking helpers the exercised path is `missing_parent / "child"`, so a regression that renamed the error to name the child would still pass (the parent string is a substring of the child path). After: the predicate also excludes the child path, `str(missing_parent / "child") not in msg`, so only a message naming the parent passes.

Edge cases that shaped the design: the four scaffolds' refusal texts differ (hence `refusal_text`); `ENOTDIR` joins `ELOOP` on darwin for `O_NOFOLLOW` symlink opens (existing code comment); the lag arm's new sidecar would otherwise change the downstream arms' pinned expectations (hence the `unlink()`); the note literal keeps `delta` so the round-2 validation pin survives.

## Design Invariants (CR Guard)

- Message contracts are preserved per helper: `tighten_parent_ai_playbook` keeps `parent is not a directory: {parent}` on `ELOOP`/`ENOTDIR`; the three sibling helpers keep `refusing symlinked parent: {path.parent}`; `read_private_file` keeps `refusing to follow symlink target: {path}` on final-component `ELOOP`/`ENOTDIR`. No message text changes in this plan.
- Fail-closed contract unchanged: every helper still refuses on symlinked parents/targets and closes every opened fd exactly once (`finally` ownership moves into `_pinned_parent`, never duplicates).
- The `classes=` summary stays ledger-pinned (cohort membership contract); the set-based retry-delta changes only the note trigger, never exit code derivation, the published report, or the ledger.
- The r2 F2 errno-split shape survives verbatim inside `_pinned_parent`: symlink-indicating errnos produce the refusal text, every other errno produces `cannot open parent directory: {parent}: {exc}`.
- The archived round-2 plan is amended ONLY where this plan's implementation falsifies its pinned wording (Validation block per-helper pin in Task 2; Task 3 GREEN formula bullet in Task 3). Every other byte of that file is frozen.

## Evaluation Criteria

**Quality dimensions:**

- correctness: full selftest suite green; the three new RED fixtures (ancestor-swap read refusal, mask-scenario note, missing-parent `read_private_file` entry) flip green only after their owning GREEN tasks; the strengthened witnesses (lag arm, missing-parent predicate) stay green throughout.
- security: `read_private_file` refuses a symlinked ancestor even with `_reject_symlink` patched to a no-op (kernel flags are the only guard left, mirroring the existing bypass-arm idiom).
- maintainability: exactly one parent-dirfd open/translate/close implementation; `grep -c "_pinned_parent("` is 6 or more and no helper body contains `os.open(str(` for a parent.
- doc/history fidelity: the round-2 plan's amended Validation block exits 0 against the implemented tree; its other pinned lines are untouched.

**Done when:**

- `python3 scripts/summarize_review_stats.py --selftest` exits 0 with the new and strengthened checks present.
- The final `## Validation Commands` block exits 0.
- `git diff --stat` touches only `scripts/summarize_review_stats.py` and `docs/plans/completed/2026-09-02-summarizer-hardening-round-2.md`.

**Ship when:**

- The five backlog origin files move to `docs/history/backlog/completed/` with `Status: done` in the plan-completion pass (Plan Lifecycle).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `scripts/summarize_review_stats.py`: in scope only for `_pinned_parent` (new), `tighten_parent_ai_playbook`, `ensure_private_dir`, `create_private_file_exclusive`, `read_private_file`, `_atomic_write_private` (parent-dirfd rewrite only; each helper's other logic is frozen), the `_classify_current`/`_publish` closure pair inside `cmd_strict_audit` (set-based delta only), and the selftest arms named in the tasks (`private_permissions` bypass arms, `strict_audit_stale_snapshot` lag/unparseable/both-counters/chronic/mask arms, missing-parent check). All other functions and arms in this file are frozen; reject any review finding that touches them.

**Tests:**

- `scripts/summarize_review_stats.py` `--selftest` families touched by the tasks below (same file, selftest registry).

**Docs (same-change amendment):**

- `docs/plans/completed/2026-09-02-summarizer-hardening-round-2.md`: in scope only for the Validation Commands block lines named in Task 2 and the Task 3 GREEN bullet named in Task 3. Everything else in this file is frozen; reject any review finding that touches it.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `docs/history/backlog/**`; origin files move only in the completion pass.
- `~/.ai-playbook/scripts/**`; runtime copies, synced from the repo, never edited directly.
- `scripts/validate_review_staging.py`; not implicated by any task (its r2-plan pins do not falsify).
- Other plans under `docs/plans/`; frozen history, not reworded.

## Validation Commands

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"

# Full selftests (canonical executable, cwd-anchored).
( cd "$REPO_ROOT" && python3 scripts/summarize_review_stats.py --selftest )

SRS="$REPO_ROOT/scripts/summarize_review_stats.py"

# Shared manager: pinned-flags body plus def + five call sites (fail-closed).
sed -n '/^def _pinned_parent/,/^def [a-z_]*(/p' "$SRS" | grep -q "O_DIRECTORY" \
  || { echo "_pinned_parent lacks O_DIRECTORY parent dirfd"; exit 1; }
test "$(grep -c '_pinned_parent(' "$SRS")" -ge 6 \
  || { echo "_pinned_parent def + 5 call sites missing"; exit 1; }

# No helper body opens the parent by path string any more, and every
# helper consumes the shared manager (per-file/per-helper gates, no
# context spillover; the manager's own os.open(str(parent)) is outside
# these ranges by construction).
for h in tighten_parent_ai_playbook ensure_private_dir create_private_file_exclusive _atomic_write_private; do
  sed -n "/^def $h/,/^def [a-z_]*(/p" "$SRS" | grep -q "os.open(str(" \
    && { echo "$h still opens the parent by path string"; exit 1; }
  sed -n "/^def $h/,/^def [a-z_]*(/p" "$SRS" | grep -q "_pinned_parent(" \
    || { echo "$h lacks _pinned_parent usage"; exit 1; }
done

# read_private_file: final component opened dir_fd-relative under the
# pinned parent; O_NOFOLLOW stays on the final-component open.
sed -n '/^def read_private_file/,/^def [a-z_]*(/p' "$SRS" | grep -q "dir_fd=parent_fd" \
  || { echo "read_private_file lacks dir_fd-relative final component"; exit 1; }
sed -n '/^def read_private_file/,/^def [a-z_]*(/p' "$SRS" | grep -q "O_NOFOLLOW" \
  || { echo "read_private_file lacks O_NOFOLLOW"; exit 1; }

# Set-based retry-delta: count-subtraction formula gone, set difference
# present, note literal (and the r2 pin variable name) unchanged.
if grep -nF 'delta = dropped - len(ledger["unreadable"])' "$SRS"; then
  echo "count-based retry-delta formula remains"; exit 1
fi
grep -qF "unparseable_now - chronic" "$SRS" \
  || { echo "set-based retry-delta difference missing"; exit 1; }
grep -qF 'dropped {delta} unparseable sidecar(s) (retry-induced)' "$SRS" \
  || { echo "retry-induced note literal drifted"; exit 1; }

# Task 1 witness pins.
grep -qF 'str(missing_parent / "child") not in msg' "$SRS" \
  || { echo "missing-parent arm predicate not tightened"; exit 1; }
grep -qF 'kernel-refuses symlinked ancestor' "$SRS" \
  || { echo "read-path ancestor bypass arm missing"; exit 1; }
grep -qF 'mask arm fires on repaired-chronic plus fresh drop' "$SRS" \
  || { echo "retry-delta mask arm missing"; exit 1; }

# Same-change amendment of the archived round-2 plan: manager pin present,
# stale per-helper pin gone, Task 3 formula wording set-based.
R2="$REPO_ROOT/docs/plans/completed/2026-09-02-summarizer-hardening-round-2.md"
grep -qF '_pinned_parent' "$R2" \
  || { echo "r2 plan Validation block not amended"; exit 1; }
grep -qF 'retry_drops = unparseable_now - chronic' "$R2" \
  || { echo "r2 plan Task 3 formula wording not amended"; exit 1; }
if grep -nF '_atomic_write_private lacks O_DIRECTORY parent dirfd' "$R2"; then
  echo "r2 plan stale per-helper pin remains"; exit 1
fi
```

Authoring-time RED/GREEN proof (2026-09-05 tree, executed): `_pinned_parent(` count 0; `dir_flags`/scaffold `os.open(str(` present in all four helper bodies; the count-based formula present at `:2305`; `unparseable_now - chronic`, the child-exclusion predicate, and the ancestor-arm phrase all absent; the note literal `dropped {delta} unparseable sidecar(s) (retry-induced)` present exactly once. The forbidden sweeps above therefore fire today and flip only via their owning tasks.

### Task 1: RED fixtures (items 2, 3) + witness strengthening (items 4, 5)

Files:
- `scripts/summarize_review_stats.py` (selftest families `private_permissions` and `strict_audit_stale_snapshot` only)

- [x] `private_permissions` family, beside the existing `_reject_symlink`-bypass arms (~:3167): add `permissions: read_private_file kernel-refuses symlinked ancestor with pre-check disabled`; given a real directory containing the target file, a symlinked ANCESTOR directory pointing at it, and `_reject_symlink` patched to a no-op (same save/restore-in-finally idiom as the existing bypass arms), expects `_expect_refusal` matches the exact post-fix message `refusing symlinked parent: {path.parent}` (same exact-match idiom the neighboring bypass arms use). Today RED: the full-path `O_NOFOLLOW` open follows the ancestor symlink and returns the bytes with no refusal.
- [x] `strict_audit_stale_snapshot` family, after the chronic-unreadable arm: add the mask arm `strict_audit_stale_snapshot: mask arm fires on repaired-chronic plus fresh drop`; given sidecar `sc` valid on disk and sidecar `sc_b` written unparseable BEFORE `cmd_init_baseline` (chronic), then (same enumerated idiom as the sibling arms) `bp.unlink()` followed by the `re-init with chronic-unreadable sidecar succeeds`-style `cmd_init_baseline` check, then a fresh first-call hook rewrites `sc_b` to a valid `_make_current_payload(["risk"])` (repairs the chronic sidecar) and simultaneously rewrites `sc` to `b"{ not json"` (fresh drop), expects audit rc == 1 (both sidecars' refreshed buffers differ from their `build_baseline` snapshot digests, which cover every discovered sidecar including the unparseable one) and stderr contains `dropped 1 unparseable sidecar(s) (retry-induced)`. Today RED: count subtraction yields `delta == 0` and the note stays silent (probed shape matches the existing arms ~:3734).
- [x] Lag-arm strengthening (item 4, same family, ~:3611): before the lag arm's re-init, write a second valid sidecar `sc2 = repo / "docs" / "reviews" / "y.stats.json"` via `_write_private_sidecar(sc2, _make_current_payload(["risk"]))`; pass it to the hook as `{sc: p_b, sc2: b"{ not json"}` so the publish-gate rewrite also moves a valid sidecar into would-be-`unreadable`; update the `classes=` check's comment to state the new discrimination (a refreshed-ledger regression now changes the tail via `sc2`, so only the correct ledger-pinned implementation passes); after the report-half check, `sc2.unlink()` with a comment restoring the single-sidecar corpus for the downstream arms. Update the comment in the both-counters arm that currently says it introduces the second sidecar (it now re-uses the path; its `_write_private_sidecar` call stays as the re-assertion). Expect GREEN before and after (the check discriminates a regression; today's implementation already passes it).
- [x] Missing-parent predicate tightening (item 5, `private_permissions` family missing-parent check ~:3155): extend the combined predicate with `and str(missing_parent / "child") not in msg` so a message naming the child path fails while the parent-naming message passes (trivially true for `tighten_parent_ai_playbook`, which takes no child). Also add a `read_private_file` arm as its own check beside the loop (NOT a new entry in the shared loop, r5 F1): given `missing_parent / "child"` with the same msg-capture pattern but `except (PermissionsError, OSError) as exc` (today a missing parent surfaces as a raw `FileNotFoundError` that would ESCAPE the loop's `except PermissionsError` and abort the whole family at `run_selftest` ~:5273, killing the arms after it), same check name pattern and combined predicate. Today the arm is RED but contained: the raw OSError string is captured, the predicate is false, the check fails, and the family still runs to completion; after Task 2's manager rewrite the parent-open refusal is the `PermissionsError("cannot open parent directory: ...")` message and the check passes. Expect GREEN immediately for the four existing loop helpers (current messages name the parent only).
- [x] Keep every pinned literal introduced by this task on a single line in the implemented file: the final Validation block pins the ancestor-arm phrase, the mask-arm phrase, and the child-path predicate with single-line `grep -qF`, so a wrapped literal breaks its pin even though the implementation is correct (r3 F1).
- [x] Run → expect RED overall: `python3 scripts/summarize_review_stats.py --selftest` exits non-zero with exactly the three RED fixtures failing (ancestor arm, mask arm, missing-parent `read_private_file` entry); ALL pre-existing checks and the strengthened lag-arm witness stay green.
- [x] Commit: `test: summarizer r3 RED fixtures + witness strengthening`

### Task 2: GREEN items 1+2: shared `_pinned_parent` manager + dirfd-relative read path

Files:
- `scripts/summarize_review_stats.py`
- `docs/plans/completed/2026-09-02-summarizer-hardening-round-2.md` (Validation Commands block lines named below only)

- [x] Add `@contextmanager def _pinned_parent(parent: Path, refusal_text: str) -> Iterator[int]` near the private-path helpers (module already imports `contextmanager` at :52): open `os.open(str(parent), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)`; on `OSError` with `errno` in `(ELOOP, ENOTDIR)` raise `PermissionsError(refusal_text) from exc`, otherwise `PermissionsError(f"cannot open parent directory: {parent}: {exc}") from exc` (r2 F2 split verbatim); yield the fd; close it in a `finally`.
- [x] Rewrite the four helpers onto the manager, deleting ONLY each helper's parent-open scaffold (the local `os.open(str(...))` call, its errno-split translation, and the owning `finally: os.close(...)`): `tighten_parent_ai_playbook` also drops its now-unused `flags = ...` local; `create_private_file_exclusive` and `_atomic_write_private` also drop their now-unused `dir_flags = ...` locals. `ensure_private_dir` KEEPS a local flags local (rename it `final_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC`) because its retained final-component reopen still consumes it; update THAT call site in the same edit from `os.open(name, dir_flags, dir_fd=parent_fd)` (~:251) to `os.open(name, final_flags, dir_fd=parent_fd)` (deleting the local without the rename would NameError the helper). Call sites: `tighten_parent_ai_playbook` uses `with _pinned_parent(parent, f"parent is not a directory: {parent}") as fd:` around its existing `fstat`/`S_ISDIR`/`fchmod` block; `ensure_private_dir`, `create_private_file_exclusive`, and `_atomic_write_private` each use `with _pinned_parent(path.parent, f"refusing symlinked parent: {path.parent}") as parent_fd:` around their existing dirfd-relative bodies, unchanged otherwise.
- [x] Rewrite `read_private_file` (item 2): `_reject_symlink(path)` stays; then `with _pinned_parent(path.parent, f"refusing symlinked parent: {path.parent}") as parent_fd:` and inside it `fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent_fd)`, translating `ELOOP`/`ENOTDIR` on THIS open to the existing `PermissionsError(f"refusing to follow symlink target: {path}") from exc` and re-raising other `OSError`s; the existing best-effort 0600 `fchmod` re-assert on the fd is unchanged, and the fd is closed where it is today. Update the docstring's kernel-grade paragraph to describe the pinned-parent + final-component-open mechanism.
- [x] Run → expect: `python3 scripts/summarize_review_stats.py --selftest` exits non-zero with ONLY the Task 1 mask arm still failing (the ancestor arm and the missing-parent `read_private_file` entry flip green with the manager rewrite; every pre-existing check, including all pinned refusal messages, is green). The mask arm's GREEN lands in Task 3.
- [x] Amend the archived round-2 plan's Validation Commands block IN THE SAME CHANGE (its `_atomic_write_private` per-helper pin now falsifies): replace the two lines `sed -n '/^def _atomic_write_private/,/^def cmd_/p' "$SRS" | grep -q "O_DIRECTORY"` plus its `|| { echo "_atomic_write_private lacks O_DIRECTORY parent dirfd"; exit 1; }` with a manager pin `sed -n '/^def _pinned_parent/,/^def [a-z_]*(/p' "$SRS" | grep -q "O_DIRECTORY"` plus `|| { echo "_pinned_parent lacks O_DIRECTORY parent dirfd"; exit 1; }`, and append a count pin `test "$(grep -c '_pinned_parent(' "$SRS")" -ge 6 || { echo "expected _pinned_parent def + 5 call sites"; exit 1; }`. Append one dated note line under the block: amended 2026-09-05 by `docs/plans/2026-09-05-summarizer-round-3-residuals.md` (parent-dirfd scaffold extracted to the shared manager). No other line of the block changes.
- [x] Run → expect GREEN (pin subset only): from the amended round-2 Validation block, the per-helper/kernel pin lines through the attempts-signal pin exit 0 against the implemented tree. Of the block's two full-selftest lines, the `summarize_review_stats.py --selftest` line is expected RED at this stage (the mask arm's GREEN lands in Task 3) while the `validate_review_staging.py --selftest` line is untouched by this plan and stays green; the whole block goes green after Task 3.
- [x] Commit: `feat: shared parent-dirfd context manager + dirfd-relative read path`

### Task 3: GREEN item 3: set-based retry-delta

Files:
- `scripts/summarize_review_stats.py`
- `docs/plans/completed/2026-09-02-summarizer-hardening-round-2.md` (Task 3 GREEN bullet only)

- [x] Change `_classify_current` (~:2289) to return `(classified, unparseable)` where `unparseable: set[Path]` collects the sidecars whose `parse_payload` returned None (replacing the `dropped` counter; signature updated, no other caller exists). In `_publish`, rename the unpacking binding in the same edit: `classified, unparseable_now = _classify_current()`.
- [x] In `_publish` (~:2298): capture `chronic = set(ledger["unreadable"])`; compute `retry_drops = unparseable_now - chronic`; keep the note literal by computing `delta = len(retry_drops)`; gate the notes block on `if skipped or retry_drops:`. Rewrite the comment paragraph above the delta line to state the set semantics: a sidecar unparseable at publish time counts only when it was NOT chronically unreadable at the initial classification; count subtraction masked the repaired-chronic-plus-fresh-drop window (backlog origin item 3); chronic sidecars stay visible via the ledger-pinned `classes=` summary.
- [x] Run → expect GREEN: `python3 scripts/summarize_review_stats.py --selftest` (mask arm flips green; the unparseable-at-retry, both-counters, and no-report arms keep firing the note with count 1; the chronic-unreadable arm stays silent; entire suite green).
- [x] Amend the archived round-2 plan's Task 3 GREEN bullet IN THE SAME CHANGE: replace the formula sentence `compute delta = dropped - len(ledger["unreadable"]) and emit the note only when delta > 0` with the set-based prescription `capture chronic = set(ledger["unreadable"]), compute retry_drops = unparseable_now - chronic and emit the note only when retry_drops is non-empty`, keeping the pinned `dropped {delta} unparseable sidecar(s) (retry-induced)` wording in that sentence, and append `(amended 2026-09-05 by docs/plans/2026-09-05-summarizer-round-3-residuals.md; originally pinned the count-based subtraction)`. Keep the `unparseable_now - chronic` difference expression on a single line in the implemented file (the Validation block pins it with single-line `grep -qF`; r3 F1).
- [x] Run → expect GREEN: the round-2 Validation block still exits 0 (its `dropped {delta}` pin is unchanged by the kept variable name).
- [x] Commit: `feat: set-based retry-delta parse-drop note`

### Task 4: final validation

Files:
- none (verification only)

- [x] Run the full `## Validation Commands` block → expect exit 0 (after a `bash -n` syntax check of the block itself, extracted between its fences).
- [x] Inventory check: `git diff --stat` touches only `scripts/summarize_review_stats.py` and `docs/plans/completed/2026-09-02-summarizer-hardening-round-2.md`; anything else is investigated before commit.
- [x] Note for completion (Plan Lifecycle): the five backlog origin files move to `docs/history/backlog/completed/` with `Status: done` in the completion pass.
