# Plan: Summarizer hardening round 2

Backlog origins: `docs/history/backlog/2026-09-01-strict-audit-summary-lag.md`, `docs/history/backlog/2026-09-01-private-dir-symlink-toctou.md`, `docs/history/backlog/2026-09-01-stale-snapshot-arm-parse-helper-dedup.md`, `docs/history/backlog/2026-08-28-summarizer-cli-followups.md` (F12 half; F4 already completed).

## Terms

- **publish_with_recheck**: the pre-publish recheck gate in `scripts/summarize_review_stats.py` (~:1898) that re-verifies each input's on-disk generation before `publish_fn` runs and retries bounded times on change.
- **retry-absorbed mutation**: an input change detected and absorbed by one bounded retry inside `publish_with_recheck`; the publish succeeds but ledger-derived caller state was computed from the pre-race read.
- **private-path helpers**: `tighten_parent_ai_playbook` (~:181), `ensure_private_dir` (~:204), `create_private_file_exclusive` (~:230), `read_private_file` (~:258), `_atomic_write_private` (~:2012) in `scripts/summarize_review_stats.py`.
- **chronic-unreadable sidecar**: a sidecar unparseable at the initial buffer read, classified into `ledger["unreadable"]`; not retry-induced.
- **first-call hook**: the `_rewrite_on_first_call` patch idiom of the `strict_audit_stale_snapshot` family (~:2943): the first `publish_with_recheck` invocation rewrites sidecars on disk, then delegates to the real function.
- **source-flag table**: the single tuple in `scripts/validate_review_staging.py` mapping `(--source-plan|--source-rfc|--source-doc)` to the argparse dest and `source_kind`, replacing the tripled wiring.

## Assumptions

- assume the completed 2026-09-01 publish-lock plan's freeze on the neighboring helpers expired at its archive; basis: `docs/plans/completed/2026-09-01-summarizer-publish-lock-hardening.md` is completed history and this plan's backlog items say the freeze was that plan's own scope rule.
- assume selftests inside the two scripts (the `--selftest` registries) are the only test layer; basis: both scripts verified green today via `python3 scripts/<name> --selftest`; no external suite exists.
- assume no external CLI contract changes: `publish_with_recheck` gains a return value (both existing selftest call sites at ~:2799 and ~:2820 ignore it), and F12 keeps all three source flags; basis: backlog suggested-fix texts.
- assume plans authoring rules are cited by name (rule numbering in `agents/skills/plans/SKILL.md` is mid-renumber by a parallel session); basis: working-tree history commit 430773b.

## Design Invariants (CR Guard)

- Invariant 9 (bounded retry): `publish_with_recheck` keeps its retry semantics and in-place buffer refresh; the attempts signal is additive. Verified live in the completed plan's `strict_audit_stale_snapshot` family (published-report-equals-fresh arm, ~:3005).
- The effectiveness report builder and serializers (`build_effectiveness_report`, `serialize_effectiveness_json`, `serialize_effectiveness_markdown`) stay frozen; report shape unchanged. The parse-drop count stays a stderr note; it does NOT enter the report.
- Private-path guarantee: private data is never written to or read from a symlink target; modes stay 0600/0700, never create-then-chmod on create paths.
- F12 keeps the three CLI flags and their mutual exclusivity; flag names and help text stay stable.

## Gist & Examples

Four defects close in one pass over the summarizer pair:

1. **Strict-audit summary lag** (`2026-09-01-strict-audit-summary-lag.md`): after a retry-absorbed mutation, `cmd_strict_audit` (~:2040) computes `anomalies` (~:2130) from the pre-race buffers while the published report is rebuilt from the refreshed buffers. Example: baseline snapshotted sidecar payload A; a hook rewrites it to payload B at the publish gate; the retry absorbs it and publishes B, but `replaced` was computed against A so the command exits 0 although the on-disk sidecar no longer matches the baseline. Fix: `publish_with_recheck` returns the attempts count; on attempts > 1 the caller recomputes `replaced` over the refreshed buffers and emits a stderr note before computing the exit code.
2. **Parse-drop note delta** (rider in the same backlog file): the `dropped N unparseable sidecar(s)` note (~:2109) fires on every run for chronic-unreadable sidecars (probe-verified today: a corpus with one unparseable sidecar prints the note and `classes=..., unreadable=1, ...`). Fix: emit the note only for the retry-induced delta `dropped - len(ledger["unreadable"])`; chronic sidecars remain visible in the `classes=` summary.
3. **Private-path symlink TOCTOU** (`2026-09-01-private-dir-symlink-toctou.md`): the helpers defend with a `_reject_symlink` pre-check only; between the check and the subsequent open/mkdir/write/rename a local attacker can swap in a symlink. Fix: kernel-grade defenses: `O_NOFOLLOW | O_CLOEXEC` opens for file reads, `O_DIRECTORY | O_NOFOLLOW` parent dirfds with dirfd-relative `os.mkdir(..., dir_fd=...)` / `os.replace(..., src_dir_fd=..., dst_dir_fd=...)` / fstat/fchmod for directory operations, so the pre-check becomes advisory. Plus the F9 rider: a raced symlink on the lock path surfaces as a friendly `PermissionsError` naming the lock path instead of a raw `OSError` (ELOOP) traceback. The kernel race window itself is not stageable in a selftest; the fixtures pin the mechanism (flags/dirfd usage) and the clean-failure behavior on statically symlinked paths.
4. **Stale-snapshot arm dedup** (`2026-09-01-stale-snapshot-arm-parse-helper-dedup.md`): the `skipped2` (~:3044-3055) and `skipped4` (~:3131-3142) arms duplicate a twelve-line guarded-parse idiom. Fix: extract `_skipped_malformed_of(path)` beside `_read_or_empty` (~:2973) and call it from both arms. Characterization: both arms GREEN before and after.
5. **F12 source-flag triplication** (F12 half of `2026-08-28-summarizer-cli-followups.md`): three argparse entries (~:5312-5343), an empty-value loop (~:5350-5359), a mutual-exclusivity list (~:5385-5394), and an if/elif routing chain (~:5395-5412) in `scripts/validate_review_staging.py` triple one wiring; the three CLI selftest families `_selftest_source_plan_cli` (~:3452), `_selftest_source_rfc_cli` (~:3534), `_selftest_source_doc_cli` (~:3621) repeat the same cases with visible drift. Fix: one source-flag table drives the empty-check, the mutual-exclusivity list, and the routing; the three families become one parameterized family run once per kind.

## Evaluation Criteria

**Quality dimensions:**

- correctness: after a retry-absorbed mutation the strict-audit exit code, `anomalies` count, and stderr reflect the refreshed buffers; the delta-note semantics fire only for retry-induced drops (probed RED-today: chronic-unreadable corpus currently prints the note every run).
- security: every private-path helper performs its kernel call through a symlink-refusing primitive (O_NOFOLLOW open, or an O_DIRECTORY parent dirfd with dir_fd-relative syscalls); statically symlinked paths fail with `PermissionsError` naming the path.
- maintainability: the guarded-parse idiom exists once; the source-flag wiring is driven by one table; one parameterized CLI selftest family replaces three.
- compatibility: `python3 scripts/summarize_review_stats.py --selftest` and `python3 scripts/validate_review_staging.py --selftest` green after every task.

**Done when:**

- All new/changed selftest checks pass on the implemented tree and the final Validation Commands block exits 0.

**Ship when:**

- The four backlog origin files are archived to `docs/history/backlog/completed/` with `Status: done` in the plan-completion pass (Plan Lifecycle).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `scripts/summarize_review_stats.py`: in scope only for: `publish_with_recheck` (return value + docstring), `cmd_strict_audit` (post-publish recompute + notes), `_publish` closure note text, `tighten_parent_ai_playbook`, `ensure_private_dir`, `create_private_file_exclusive` (parent-dirfd rewrite only), `read_private_file`, `telemetry_lock` (ELOOP translation only), `_atomic_write_private`, and the new `_skipped_malformed_of` helper. All other functions in this file are frozen; reject any review finding that touches them.
- `scripts/validate_review_staging.py`: in scope only for: `main()` source-flag wiring (argparse entries, empty-value loop, mutual-exclusivity list, routing) and the `_selftest_source_plan_cli` / `_selftest_source_rfc_cli` / `_selftest_source_doc_cli` families replaced by the parameterized family. All other functions in this file are frozen; reject any review finding that touches them.

**Tests:**

- `scripts/summarize_review_stats.py` `--selftest` families touched by the tasks below (same file, selftest registry).
- `scripts/validate_review_staging.py` `--selftest` families listed above.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `docs/plans/completed/2026-09-01-summarizer-publish-lock-hardening.md`; frozen history, not reworded (same disposition as the dedup backlog item's factual note).
- `docs/history/backlog/**`; origin files move only in the completion pass.
- `agents/skills/plans/SKILL.md` and `docs/plans/2026-09-02-phase3-residue-pass.md`; owned by the parallel residue-pass work on this branch.
- `~/.ai-playbook/scripts/**`; runtime copies, synced from the repo, never edited directly.

## Validation Commands

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"

# Full selftests (canonical executables, cwd-anchored).
( cd "$REPO_ROOT" && python3 scripts/summarize_review_stats.py --selftest )
( cd "$REPO_ROOT" && python3 scripts/validate_review_staging.py --selftest )

# Kernel-grade mechanism pins (per-helper, fail-closed).
SRS="$REPO_ROOT/scripts/summarize_review_stats.py"
grep -q "O_NOFOLLOW" "$SRS" || { echo "missing O_NOFOLLOW"; exit 1; }
sed -n '/^def read_private_file/,/^def [a-z_]*(/p' "$SRS" | grep -q "O_NOFOLLOW" \
  || { echo "read_private_file lacks O_NOFOLLOW"; exit 1; }
sed -n '/^def ensure_private_dir/,/^def [a-z_]*(/p' "$SRS" | grep -q "dir_fd" \
  || { echo "ensure_private_dir lacks dir_fd-relative mkdir"; exit 1; }
sed -n '/^def _pinned_parent/,/^def tighten_parent_ai_playbook/p' "$SRS" | grep -q 'os.O_RDONLY | os.O_DIRECTORY' \
  || { echo "_pinned_parent lacks O_DIRECTORY parent dirfd"; exit 1; }
test "$(grep -c '_pinned_parent(' "$SRS")" -ge 6 || { echo "expected _pinned_parent def + 5 call sites"; exit 1; }
sed -n '/^def create_private_file_exclusive/,/^def read_private_file/p' "$SRS" | grep -q "dir_fd" \
  || { echo "create_private_file_exclusive lacks parent dirfd"; exit 1; }
sed -n '/^def tighten_parent_ai_playbook/,/^def ensure_private_dir/p' "$SRS" | grep -q "fchmod" \
  || { echo "tighten_parent_ai_playbook lacks fchmod"; exit 1; }
# ELOOP translation scoped to telemetry_lock (the identifier also appears in
# a comment and an existing selftest, so a file-wide grep would alias).
sed -n '/^def telemetry_lock/,/^# ---/p' "$SRS" | grep -q "errno[.]ELOOP" \
  || { echo "telemetry_lock lacks ELOOP translation"; exit 1; }

# Old duplicate parse idiom gone from the stale-snapshot family (zero-match
# sweep; the sweep targets only the script, so the literals stay unescaped).
if grep -n "skipped2: object = None" "$SRS"; then echo "dup idiom remains (skipped2)"; exit 1; fi
if grep -n "skipped4: object = None" "$SRS"; then echo "dup idiom remains (skipped4)"; exit 1; fi
grep -q "_skipped_malformed_of" "$SRS" || { echo "helper missing"; exit 1; }
test "$(grep -c "_skipped_malformed_of" "$SRS")" -ge 3 || { echo "helper not used from both arms + def"; exit 1; }

# Old parse-drop note wording replaced by the delta form (self-match-immune
# escape; RED against the current tree, GREEN only after Task 3).
if grep -n 'dropped {dropped} unparseable' "$SRS"; then echo "old note wording remains"; exit 1; fi
grep -q 'dropped {delta} unparseable' "$SRS" || { echo "delta note wording missing"; exit 1; }

# F12: one table drives the wiring (self-match-immune escape).
VRS="$REPO_ROOT/scripts/validate_review_staging.py"
grep -q "_SOURCE_FLAG_TABLE" "$VRS" || { echo "source-flag table missing"; exit 1; }
test "$(grep -c -E "elif args[.]source_(rfc|doc)" "$VRS")" -eq 0 \
  || { echo "if/elif routing chain remains"; exit 1; }
if grep -n "if args[.]source_plan:" "$VRS"; then echo "explicit plan routing branch remains"; exit 1; fi
grep -q "^def _selftest_source_cli(" "$VRS" || { echo "parameterized family missing"; exit 1; }
if grep -n "def _selftest_source_plan_cli" "$VRS"; then echo "old plan family remains"; exit 1; fi
if grep -n "def _selftest_source_rfc_cli" "$VRS"; then echo "old rfc family remains"; exit 1; fi
if grep -n "def _selftest_source_doc_cli" "$VRS"; then echo "old doc family remains"; exit 1; fi

# Attempts-signal pin (the recheck signature returns int).
sed -n '/^def publish_with_recheck/,/^    attempt = 0/p' "$SRS" | grep -q -- "-> int" \
  || { echo "publish_with_recheck does not return int"; exit 1; }
# amended 2026-09-05 by docs/plans/2026-09-05-summarizer-round-3-residuals.md (parent-dirfd scaffold extracted to the shared manager)
```

### Task 1: RED: strict-audit summary-lag arm + attempts checks

Files:
- `scripts/summarize_review_stats.py` (selftest family `strict_audit_stale_snapshot` only)

- [x] In the `strict_audit_stale_snapshot` family, after the existing first arm: re-baseline a single sidecar (payload A), then run `_audit_with_hook` with a first-call rewrite of the sidecar to a DIFFERENT valid payload B (e.g. `counts.raw_findings` moved to another size bucket). Add checks: `strict_audit_stale_snapshot: summary-lag arm recomputes anomalies`; given the retry-absorbed rewrite, expects audit rc == 1 (the recomputed `replaced` counts the mutated sidecar) and stderr names the retry-absorbed mutation (expected phrase `retry-absorbed mutation; summary recomputed`). Today this is RED (rc == 0, no note).
- [x] Add checks pinning the attempts signal at the `publish_with_recheck` level (same family, using the existing `_rewrite_on_first_call` idiom): `strict_audit_stale_snapshot: clean publish reports one attempt`; given no mutation, expects the returned count == 1; `strict_audit_stale_snapshot: retry-absorbed publish reports two attempts`; given a first-call rewrite, expects the returned count == 2. Today RED (function returns None).
- [x] Run → expect RED: `python3 scripts/summarize_review_stats.py --selftest` (the new checks fail; ALL pre-existing checks stay green).
- [x] Commit: `test: summary-lag + attempts RED fixtures in stale-snapshot family`

### Task 2: GREEN: attempts signal + refreshed-buffer summary recompute

Files:
- `scripts/summarize_review_stats.py`

- [x] `publish_with_recheck` returns `int`: the attempt count on the success path (1 when no retry, N+1 after N absorbed retries); update the docstring contract paragraph to state the return. Call sites at ~:2799 and ~:2820 ignore the return (compatible).
- [x] `cmd_strict_audit` captures the return; when attempts > 1, recompute `replaced` over the refreshed `buffers` (same digest compare against `snapshot_by_path`) and emit a stderr note `strict audit: retry-absorbed mutation; summary recomputed from refreshed buffers` from the same refreshed-buffer recompute block that derives the `anomalies` count (~:2130), but only when the recompute actually CHANGED the replaced set (r3 F1: a rewrite to digest-identical content leaves the summary unchanged and the note would be noise); when unchanged, stay silent. The `classes=` ledger summary stays ledger-pinned (cohort membership contract, docstring ~:1920).
- [x] Update the pre-existing stale-snapshot checks the recompute deterministically flips, in the SAME edit (r1 F1): the retry-absorbed arms' rc expectations at ~:2980 (first arm), ~:3035 (malformed-at-retry), ~:3077 (unparseable-at-retry), ~:3117 (both-counters), and ~:3159 (no-report) each change from rc == 0 to rc == 1 (the hooked sidecar now differs from its baseline snapshot, a real `replaced` anomaly), and the first arm's no-stderr-note check at ~:2982 changes to expect the recomputed-summary note. The Task 1 chronic-unreadable arm (Task 3) has NO hook mutation and keeps rc == 0.
- [x] Run → expect GREEN: `python3 scripts/summarize_review_stats.py --selftest` (Task 1's RED checks and the updated pre-existing arms all pass; entire suite green).
- [x] Run → expect GREEN: `python3 scripts/validate_review_staging.py --selftest` (unchanged suite stays green).
- [x] Commit: `feat: strict-audit summary recomputed from refreshed buffers after retry`

### Task 3: parse-drop note becomes retry-delta based

Files:
- `scripts/summarize_review_stats.py` (selftest family + `_publish` closure)

- [x] RED check first (same family, new chronic-unreadable arm): build the two-sidecar corpus where one sidecar is written unparseable BEFORE `cmd_init_baseline` (probe-verified idiom: the family's facts/TOML setup, second sidecar `b.stats.json` with `{ not json`). Add check: `strict_audit_stale_snapshot: chronic-unreadable sidecar does not fire the parse-drop note`; given a chronic-unreadable sidecar present at the initial read, expects stderr contains NO `dropped N unparseable sidecar(s)` note while stdout `classes=` still shows `unreadable=1`. Today RED (note fires every run; probed live 2026-09-02).
- [x] GREEN: in the `_publish` closure, capture `chronic = set(ledger["unreadable"])`, compute `retry_drops = unparseable_now - chronic`, `delta = len(retry_drops)`, and emit the note only when `retry_drops` is non-empty, wording `dropped {delta} unparseable sidecar(s) (retry-induced)`; the existing unparseable-at-retry and both-counters arms keep firing the note with the new wording (their pinned phrases update in the same edit). (amended 2026-09-05 by docs/plans/2026-09-05-summarizer-round-3-residuals.md; originally pinned the count-based subtraction)
- [x] Run → expect GREEN: `python3 scripts/summarize_review_stats.py --selftest` (chronic arm flips green; retry arms stay green with the delta wording).
- [x] Commit: `feat: parse-drop note reserved for retry-induced drops`

### Task 4: kernel-grade TOCTOU defenses at directory granularity

Files:
- `scripts/summarize_review_stats.py` (helpers `tighten_parent_ai_playbook`, `ensure_private_dir`, `_atomic_write_private`; selftest families covering them)

- [x] RED checks (selftest family for the permissions helpers; follow the existing family style): `tighten_parent_ai_playbook refuses symlinked parent`; `ensure_private_dir refuses symlinked private dir`; `_atomic_write_private refuses symlinked target and parent`, each given a statically symlinked path, expects `PermissionsError` whose message names the path (and, for the write helper, expects no temp-file residue in the real parent). All three are GREEN today via the `_reject_symlink` pre-check; add them as characterization anchors BEFORE the rewrite so the kernel-grade rewrite cannot silently regress the static case. Pin the refusal messages exactly.
- [x] GREEN rewrite, keeping the same `PermissionsError` contract: `tighten_parent_ai_playbook` opens the parent with `os.open(..., O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC)`, reads the mode via `os.fstat(fd)`, and tightens via `os.fchmod(fd, 0o700)`; `ensure_private_dir` opens the parent dirfd the same way and creates the final component with `os.mkdir(name, 0o700, dir_fd=fd)` under the cleared umask, re-asserting the mode via fstat/fchmod on the created dirfd, and on the idempotent exists-path too: re-open the existing dir with `O_DIRECTORY | O_NOFOLLOW` and re-assert via `os.fstat`/`os.fchmod` on the fd, never `os.chmod(str(path))` on the path string (r4 F2: the path-string chmod would follow a raced symlink on the idempotent branch); `_atomic_write_private` opens the parent dirfd with `O_DIRECTORY | O_NOFOLLOW`, creates the temp file with `os.open(tmp, O_CREAT | O_EXCL | O_WRONLY | O_NOFOLLOW | O_CLOEXEC, 0o600, dir_fd=fd)`, and replaces via `os.replace(tmp_name, target_name, src_dir_fd=fd, dst_dir_fd=fd)`; the `except BaseException` failure-path cleanup unlinks the temp file dirfd-relative too (`os.unlink(tmp_name, dir_fd=fd)`; r3 F2: leaving the absolute `os.unlink(tmp_name)` re-resolves through the parent path and re-opens a narrow parent-swap window inside the very helper being hardened); `create_private_file_exclusive` gets the same parent-dirfd treatment (r2 F1: it shares the parent-swap window its Terms entry and the Evaluation security bullet cover): parent opened `O_DIRECTORY | O_NOFOLLOW`, final component created with `os.open(name, O_CREAT | O_EXCL | O_WRONLY | O_NOFOLLOW | O_CLOEXEC, 0o600, dir_fd=fd)`; its existing `BaselineExists` translation is unchanged. `_reject_symlink` stays as the fast pre-check; the kernel flags close the check-to-use window.
- [x] Run → expect GREEN: `python3 scripts/summarize_review_stats.py --selftest` (characterization anchors stay green; entire suite green).
- [x] Commit: `feat: dirfd-relative kernel-grade private-path helpers`

### Task 5: read_private_file O_NOFOLLOW + lock ELOOP rider (F9)

Files:
- `scripts/summarize_review_stats.py` (`read_private_file`, `telemetry_lock`; selftest families)

- [x] RED checks: `read_private_file refuses symlinked file`; given a symlinked final component, expects `PermissionsError` naming the path (GREEN today via pre-check; characterization anchor, message pinned exactly). `telemetry_lock translates a race-window symlink swap into a friendly error` (r1 F2: a STATIC lock-path symlink already yields the friendly `PermissionsError` via the `_reject_symlink` pre-check, so the discriminating ELOOP arm reuses the `snapshot_races` family's no-op-patch idiom: monkeypatch `this_mod._reject_symlink` to a no-op, place a symlink at the lock path, enter `telemetry_lock`): today a raw `OSError` (ELOOP) propagates (RED); post-fix the friendly translation fires. Pin the exact post-fix message.
- [x] GREEN: `read_private_file` opens with `os.open(str(path), O_RDONLY | O_NOFOLLOW | O_CLOEXEC)` and translates `OSError` with `errno.ELOOP` into `PermissionsError` naming the path; `telemetry_lock` wraps its `os.open` and translates `errno.ELOOP` into `PermissionsError(f"telemetry lock path is a symlink (possible tampering): {lock_path}")`.
- [x] Update the existing `snapshot_races` arm (d) in the SAME task (r1 F3): `PermissionsError` extends `Exception`, not `OSError`, so after the translation the arm's `except OSError` no longer catches and its `raised_d.errno == errno.ELOOP` check at ~:2875-2876 cannot pass. Restate the arm to catch `PermissionsError`, assert the exact friendly message (the translation intentionally loses `errno`; the arm-(d) comment records that the kernel ELOOP detail is replaced by the operator-facing message). The `not created` and clean-exit checks are unaffected.
- [x] Run → expect GREEN: `python3 scripts/summarize_review_stats.py --selftest`.
- [x] Commit: `feat: O_NOFOLLOW private reads + friendly lock ELOOP error`

### Task 6: stale-snapshot arm parse helper (dedup)

Files:
- `scripts/summarize_review_stats.py` (selftest family `strict_audit_stale_snapshot` only)

- [x] Characterization: run → expect GREEN `python3 scripts/summarize_review_stats.py --selftest` (captures the skipped2/skipped4 arms' current behavior before refactor).
- [x] Extract `_skipped_malformed_of(path)` beside `_read_or_empty` (~:2973) with the backlog item's body: `_read_or_empty`, guarded `json.loads(...).get("availability", {})`, `isinstance` dict check, `.get("skipped_malformed")`; replace the `skipped2` (~:3044-3055) and `skipped4` (~:3131-3142) blocks with `skipped2 = _skipped_malformed_of(out2)` / `skipped4 = _skipped_malformed_of(out4)`. No other arm changes.
- [x] Run → expect GREEN: `python3 scripts/summarize_review_stats.py --selftest` (both arms and the whole suite unchanged-green).
- [x] Commit: `refactor: one skipped-malformed parse helper for stale-snapshot arms`

### Task 7: F12: source-flag table + parameterized CLI family

Files:
- `scripts/validate_review_staging.py` (`main()` wiring + the three `_selftest_source_*_cli` families)

- [x] Characterization: run → expect GREEN `python3 scripts/validate_review_staging.py --selftest` (pins the three families' cases before consolidation).
- [x] Introduce `_SOURCE_FLAG_TABLE` near `main()`: one tuple of `(flag_name, dest, source_kind)` rows for `--source-plan`/`--source-rfc`/`--source-doc`; drive the empty-value loop (~:5350), the mutual-exclusivity list (~:5385), and the routing (~:5395-5412) from it (keep each flag's argparse entry and help text verbatim; the table references the dest attributes via `getattr(args, dest)`).
- [x] Replace the three families with one parameterized `_selftest_source_cli(kind)` driven by the same table shape: per kind it builds the artifact bytes, staging doc, fresh/stale/other-file/wrong-source_kind/mutual-exclusivity/empty-value cases (the union of today's cases, so the plan family's empty-value case, the doc family's mutual-exclusivity case, and the doc and rfc families' source_kind-mismatch cases all survive (r4 F1)), registering under one dotted selftest name iterating the three kinds. Preserve every discriminating assertion (correct-file exit 0, wrong-file exit 1, stale digest exit 1, source_kind mismatch error, mutual exclusivity rc 2 with the phrase, empty value rc 2 with the phrase).
- [x] Run → expect GREEN: `python3 scripts/validate_review_staging.py --selftest` (parameterized family covers all three kinds; no other family regressed).
- [x] Run → expect GREEN: `python3 scripts/summarize_review_stats.py --selftest` (cross-file check: unrelated suite untouched).
- [x] Commit: `refactor: one source-flag table + parameterized CLI selftest family`

### Task 8: final validation + inventory

Files:
- none (validation only)

- [x] Run the full `## Validation Commands` block → expect exit 0 on the implemented tree (including `bash -n` syntax check of the block itself before running it).
- [x] Inventory check: `git diff --stat` touches only `scripts/summarize_review_stats.py` and `scripts/validate_review_staging.py`; anything else is investigated before commit.
- [x] Note for completion (Plan Lifecycle): the four backlog origin files move to `docs/history/backlog/completed/` with `Status: done` in the completion pass; the F4 half of `2026-08-28-summarizer-cli-followups.md` is already recorded as completed in that file's Problem section.

## Disposition of migrated backlog items

- docs/history/backlog/completed/2026-09-02-summarizer-hardening-round-2-r5-residuals.md: disposition folded into 2026-09-02-summarizer-hardening-round-2.md (2026-09-25); per-item file deleted.
