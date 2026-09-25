# Plan: Summarizer tail trio (full-path read errors, pinned sidecar reads, window-aware chronicity)

Backlog origin:
- `docs/history/backlog/2026-09-06-dirfd-open-error-loses-path-context.md` (item 1)
- `docs/history/backlog/2026-09-06-read-byte-buffer-ancestor-symlink-residual.md` (item 2)
- `docs/history/backlog/2026-09-06-chronic-reabsorption-masks-rebreak.md` (item 3; accepted-limit candidate, premise re-verified by executed probe before planning, see Assumptions)

## Terms

- **sidecar**: a `*.stats.json` review artifact under `{reviews_dir}` discovered by `discover_sidecars`.
- **chronic sidecar**: a sidecar unparseable at the strict audit's initial buffer classification (a member of `ledger["unreadable"]`).
- **retry window**: the span between the initial buffer read in `cmd_strict_audit` and the final `publish_with_recheck` attempt, including every in-place buffer refresh.
- **pinned parent**: the `_pinned_parent` context manager: parent opened once with `O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC`, returned as a dirfd for dirfd-relative final-component opens.
- **strict audit**: `cmd_strict_audit` (`--strict-audit`): read-only sidecar conservation pass with baseline snapshot comparison and the retry-delta stderr note.
- **selftest family**: a named check group inside the script's `--selftest` suite (for example `private_permissions`, `strict_audit_stale_snapshot`); this script has no external test files.

## Assumptions

- assume item 3's premise is real (accepted-limit re-verified before planning): an executed end-to-end probe (`docs/tmp/probe-chronic-reabsorption.py`, run 2026-09-06 against today's tree) reproduced the double flip (chronic sidecar repaired then re-broken inside one retry window, final buffers unparseable) and the drop note stayed silent; basis: probe output, five `read_byte_buffer` reads observed, stderr empty.
- assume a diagnostics-only message change in `read_private_file` is safe: its sole production caller is `load_baseline` (line ~685), which propagates the raw `OSError` unchanged; basis: call-site inventory of the module.
- assume `read_byte_buffer` has no caller relying on following a swapped symlink: the `_reject_symlink` pre-check already refuses symlink targets, and all callers pass discovered existing paths; basis: call-site inventory (records ~40 call sites, all on discovered sidecar/manifest paths).
- assume selftest arms may patch module functions with save/restore-in-finally: this is the established family idiom (first-call publish hook, `_reject_symlink` no-op bypass arms); basis: existing arms in `private_permissions` and `strict_audit_stale_snapshot`.

## Design Invariants (CR Guard)

- Exit code, published report, and ledger classes are unaffected by the drop-note logic (round-3 residuals plan invariant, item 3): the chronicity change may only alter WHEN the stderr note fires, never `rc`, `serialize_effectiveness_json/markdown` output, or the `classes=` ledger summary.
- `_pinned_parent`'s documented residual (intermediate ancestors above the pinned parent resolve by path; r2 sibling contract, review r1 F1) must not be "fixed" here; both consumers inherit that contract via its docstring.
- `publish_with_recheck`'s load-bearing contract (buffers refreshed IN PLACE on retry; publish_fn derives content from current buffers) is preserved; the new observer is additive and read-only.
- The `classes=` ledger summary stays ledger-pinned (pre-publish); cohort membership does not follow the refreshed buffers.
- Existing errno translation tuples (`ELOOP`/`ENOTDIR` to `PermissionsError`) are untouched; item 1 wraps ONLY the non-translated re-raise branch.

## Gist & Examples

**Item 1, full-path OSError context.** At authoring time, `read_private_file` opened the final component dirfd-relative (`os.open(path.name, ..., dir_fd=parent_fd)`), so a non-translated `OSError` message surfaced only the bare file name.

Before (at authoring time): calling `read_private_file` on a missing file inside an existing directory raised `FileNotFoundError: [Errno 2] No such file or directory: 'absent.json'` with no directory context.
After (this plan): the same call raises an `OSError` whose message carries the full path, for example `cannot read private file: /tmp/td/reviews/absent.json: [Errno 2] No such file or directory: 'absent.json'`, chained via `from exc`. The symlink translations (`ELOOP`/`ENOTDIR` to `PermissionsError`) and the parent-open failures (surfaced by `_pinned_parent`) are unchanged.

**Item 2, pinned sidecar reads.** At authoring time, `read_byte_buffer` (the reader the strict audit uses for sidecar content) still opened the full path string with only the target pre-check, so an attacker who could write a sidecar ancestor directory could swap a symlink into an ancestor and redirect the read.

Before (at authoring time): with `_reject_symlink` bypassed, `read_byte_buffer(anc_link / "target.json")` (where `anc_link` is a symlink to a real ancestor directory) followed the ancestor and returned the bytes.
After (this plan): the same call is refused with `PermissionsError: refusing symlinked parent: {anc_link}`, because the read now pins the parent via `_pinned_parent` and opens the final component dirfd-relative with `O_NOFOLLOW`, mirroring `read_private_file`. The read stays pure: no mode management (unlike `read_private_file`, which re-tightens to 0600); sidecar modes are managed at write time.

**Item 3, window-aware chronicity.** At authoring time, chronicity for the retry-delta (`retry_drops = unparseable_now - chronic`) was decided from the initial-buffer snapshot alone. A chronic sidecar repaired and then re-broken inside the same retry window ended unparseable (retry-induced final state) yet stayed in `chronic`, so the operability stderr note stayed silent even though the drop was retry-induced. Verified against the authoring-time tree by the executed probe.

Before (at authoring time): the probe scenario yielded stderr with NO `dropped ... unparseable sidecar(s) (retry-induced)` note (probe output: stderr empty, rc 0, final disk unparseable).
After (this plan): the same scenario emits `strict audit: dropped 1 unparseable sidecar(s) (retry-induced)`. A plain chronic sidecar (unparseable at init and at publish, never parseable in the window) stays excluded exactly as today, and rc, report, and ledger stay identical (probe rc 0 is pinned in the new arm).

Mechanism for item 3: `publish_with_recheck` gains an optional keyword-only `attempt_observer` invoked after each in-place buffer refresh; `cmd_strict_audit` passes an observer that records the parseable set of every refreshed buffer snapshot into an `ever_parseable` set; `_publish` then computes `chronic = set(ledger["unreadable"]) - ever_parseable`. A sidecar counts as chronic only if it was never parseable at any observed point in the retry window. Existing `publish_with_recheck` callers pass no observer and are byte-for-byte unaffected.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the three new selftest arms flip RED to GREEN in their owning tasks; the existing chronic-unreadable arm (plain-chronic exclusion pin) is GREEN before and after; `--selftest` exits 0 at the end.
- security: with the pre-check bypassed, `read_byte_buffer` refuses a symlinked ancestor with the exact `refusing symlinked parent` message (kernel-grade, matching the `read_private_file` ancestor arm).
- diagnostics: a non-translated `read_private_file` open failure message contains the full path string and chains the original exception via `from exc`.
- invariant preservation: the double-flip arm pins `rc == 0`; the existing mask arm (repaired chronic plus fresh drop), the lag arm, and the full suite stay green throughout.

**Done when:**
- `python3 scripts/summarize_review_stats.py --selftest` exits 0 with the three new arms present and green and all pre-existing checks green.

**Ship when:**
- None. This is a repo-local diagnostics and hardening change with no deploy, cross-team, or human-owned condition.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/summarize_review_stats.py`; in-scope methods ONLY: `read_private_file` (final-component except branch), `read_byte_buffer` (whole body), `publish_with_recheck` (signature and the refresh site), `cmd_strict_audit` (`_publish` closure and the `publish_with_recheck` call site). All other methods in this file are frozen; reject any review finding that touches them.

**Tests:**
- `scripts/summarize_review_stats.py`; the `private_permissions` and `strict_audit_stale_snapshot` selftest families (new arms only, plus the arm-local hook helpers they introduce).

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/validate_review_staging.py`; separate service, no contract touched by this plan.
- `docs/history/backlog/**`; backlog lifecycle moves happen at plan completion, not during implementation.
- `docs/tmp/probe-chronic-reabsorption.py`; authoring-time verification scratch, owned by the authoring session's cleanup, not by implementation.
- Any other script or doc in the repository; this plan is single-file by design.

## Validation Commands

```bash
python3 scripts/summarize_review_stats.py --selftest
```

### Task 1: RED fixtures (items 1, 2, 3) plus existing-coverage acknowledgment

Files:
- `scripts/summarize_review_stats.py`

- [x] `private_permissions` family, beside the existing `read_private_file` missing-parent arm (~:3182, same msg-capture idiom, `except (PermissionsError, OSError)` so any failure stays contained): add the arm `permissions: read_private_file non-symlink open failure names the full path`; given an existing real directory (`tel`) and a missing child (`tel / "absent.json"`), expects the captured message contains the full string `str(tel / "absent.json")`. Today RED: the dirfd-relative open surfaces `[Errno 2] No such file or directory: 'absent.json'` with only the bare final component (backlog item 1 premise; basis: r3 review F1 plus the dirfd `os.open` message contract). The existing missing-parent arm must stay untouched: its parent-open failure surfaces from `_pinned_parent` and already names the parent.
- [x] `private_permissions` family, inside the pre-check-bypass block (after the `read_private_file` symlinked-ancestor arm ~:3292, reusing its `anc_real` / `anc_link` fixtures): add the arm `permissions: read_byte_buffer kernel-refuses symlinked ancestor with pre-check disabled`; given `_reject_symlink` patched to a no-op (same save/restore-in-finally idiom as the sibling bypass arms) and `anc_link` a symlink to the real ancestor directory containing `target.json`, expects `_expect_refusal` matches the exact message `refusing symlinked parent: {anc_link}`. Today RED: `read_byte_buffer` opens the full path string, follows the ancestor symlink, and returns the bytes with no refusal (backlog item 2 premise).
- [x] `strict_audit_stale_snapshot` family, after the existing mask arm: add the double-flip arm `strict_audit_stale_snapshot: re-broken chronic sidecar counts as retry-induced`; given sidecar `sc` valid on disk, sidecar `sc_b` written unparseable (`b"{ not json"`) BEFORE `cmd_init_baseline` (chronic), then inside ONE `cmd_strict_audit` run: a first-call `publish_with_recheck` hook (same idiom as the existing first-call hook) repairs `sc_b` to a distinct valid payload (`raw_findings` changed, so no duplicate class), and a `read_byte_buffer` patch with a read counter (realpath-matched to `sc_b`, save/restore-in-finally) re-breaks `sc_b` to `b"{ not json"` just before the third read of `sc_b` (read 1: initial buffer; read 2: re-read after the repair-triggered retry; read 3: the next attempt's recheck digest read), expects audit rc == 0 (exit-code invariant pinned; the probe observed rc 0 today) AND the read counter for `sc_b` equals 5 exactly (pins the observed retry sequence so a future recheck-loop refactor fails diagnosably instead of silently) AND stderr contains `dropped 1 unparseable sidecar(s) (retry-induced)`. Today RED: the note is absent (probe-verified 2026-09-06: stderr empty after the full five-read double flip; this fixture shape is exactly the executed probe `docs/tmp/probe-chronic-reabsorption.py`).
- [x] Acknowledge the existing plain-chronic coverage (fold of r2 F2): the family already contains a chronic-unreadable arm (~:3884) that pins a strictly stronger stderr-absence check for a plain chronic sidecar (unparseable at init and at publish) than the characterization this plan needs; NO new characterization arm is added. That existing arm is the regression pin for chronic exclusion: it is green today and must stay green after Task 3.
- [x] Run → expect RED overall: `python3 scripts/summarize_review_stats.py --selftest` exits non-zero with exactly the three new RED arms failing (full-path arm, ancestor arm, double-flip arm); the existing chronic-unreadable arm and ALL other pre-existing checks stay green.
- [x] Commit: `test: summarizer tail trio RED fixtures + chronic characterization`

### Task 2: GREEN items 1 and 2 (read-path diagnostics and pinning)

Files:
- `scripts/summarize_review_stats.py`

- [x] `read_private_file` final-component except branch (~:358): replace the bare `raise` with `raise type(exc)(f"cannot read private file: {path}: {exc}") from exc` so the original exception subclass and message survive the re-raise (note: the reconstructed exception does NOT carry the original `errno`/`filename` attributes; verified r2 F1 that no caller inspects them, so message-based pins are unaffected); keep the `ELOOP`/`ENOTDIR` `PermissionsError` translation branch above it byte-identical. The message contract of the parent-open failures (`_pinned_parent`) is untouched.
- [x] `read_byte_buffer` (~:549): route the read through the pinned-parent mechanism, mirroring `read_private_file` WITHOUT mode management: `_reject_symlink(path)`; `with _pinned_parent(path.parent, f"refusing symlinked parent: {path.parent}") as parent_fd:` then `os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent_fd)`; translate `ELOOP`/`ENOTDIR` to `PermissionsError(f"refusing to follow symlink target: {path}")` chained `from exc`, and wrap any other `OSError` as `raise type(exc)(f"cannot read byte buffer: {path}: {exc}") from exc` (subclass and message preserved; `errno`/`filename` attributes not carried, no caller inspects them); read the bytes via `os.fdopen(fd, "rb")` with the fd closed on the `os.fdopen` failure path (close fd then re-raise) and the file object owning the fd afterwards. Update the docstring: kernel-grade like `read_private_file`, parent pinned, final component `O_NOFOLLOW`, symlink swaps refused instead of followed; explicitly note the read is pure (no mode re-tightening; sidecar modes are managed at write time) and inherits `_pinned_parent`'s intermediate-ancestor residual contract.
- [x] Run → expect partially GREEN: `python3 scripts/summarize_review_stats.py --selftest` still exits non-zero with ONLY the double-flip arm failing (its GREEN lands in Task 3); the full-path arm, the ancestor arm, the existing chronic-unreadable arm, and all pre-existing checks are green (the whole suite is the regression net for the `read_byte_buffer` rerouting: every sidecar read in every family now goes through the pinned-parent path).
- [x] Commit: `feat: full-path read errors + pinned-parent reads for read_byte_buffer`

### Task 3: GREEN item 3 (window-aware chronicity)

Files:
- `scripts/summarize_review_stats.py`

- [x] `publish_with_recheck` (~:2029): add a keyword-only parameter `attempt_observer: Callable[[dict[Path, bytes]], None] | None = None` (after `retries`, default None so every existing caller is unaffected); invoke `attempt_observer(dict(buffers))` immediately after the in-place re-read loop (`for path in list(buffers.keys()): buffers[path] = read_byte_buffer(path)`), passing a shallow COPY so the observer cannot mutate the live buffers the recheck loop depends on (fold of r3 F1); extend the docstring with one paragraph: the observer is informational, invoked after each refresh with a snapshot of the refreshed buffers, and lets a caller track per-attempt parse state that the single final `publish_fn` invocation cannot observe. Document the residual there as well (fold of r3 F2): transient parse states that keep the byte size equal and are visible only to a recheck digest read (repair and re-break of equal-size content between two refreshes) are unobservable at the refresh site; this accepted residual is analogous to `_pinned_parent`'s documented intermediate-ancestor residual.
- [x] `cmd_strict_audit`: before `_publish`, define `ever_parseable: set[Path] = set()`; pass `attempt_observer=` a closure that computes the parseable subset of the refreshed buffers (`parse_payload(buf)[0] is not None`) and updates `ever_parseable`; inside `_publish`, also union `set(sidecars) - unparseable_now` into `ever_parseable` (final-attempt state), then compute `chronic = set(ledger["unreadable"]) - ever_parseable` instead of the bare snapshot set. Update the comment block above those lines: a sidecar counts as chronic only if it was never parseable at any observed point of the retry window; a chronic sidecar repaired and re-broken inside the window is retry-induced; exit code, published report, and ledger stay unaffected.
- [x] Run → expect GREEN (full suite): `python3 scripts/summarize_review_stats.py --selftest` exits 0 with the double-flip arm now green (note fires, rc 0 pinned) and the existing chronic-unreadable arm still green; all pre-existing checks green.
- [x] Commit: `feat: window-aware chronicity for strict-audit drop note`

### Task 4: final validation

Files: none (verification only)

- [x] Run → expect GREEN: the full Validation Commands block passes on the final tree: `python3 scripts/summarize_review_stats.py --selftest` exits 0.
