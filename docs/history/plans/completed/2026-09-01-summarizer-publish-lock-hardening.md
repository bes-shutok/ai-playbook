# Plan: Summarizer publish-path hardening (stale-snapshot rebuild + lock O_NOFOLLOW)

Backlog origin: `docs/history/backlog/2026-08-28-summarizer-cli-followups.md` (item 1, F4) and `docs/history/backlog/2026-08-28-telemetry-lock-symlink-toctou.md` (ride-along; same file). Requirements buffer: `docs/tmp/plan-requirements-summarizer-publish-lock.md`.

## Terms

- **Strict-audit publish path**: the classify/build/publish block inside `cmd_strict_audit` (`scripts/summarize_review_stats.py` :2056-2088) that classifies sidecars from parsed buffers, builds the effectiveness report, serializes JSON + Markdown bytes, and publishes them via `publish_with_recheck(buffers, _publish)`.
- **`publish_with_recheck`**: the pre-publish freshness gate (:1895-1932). Compares each input's on-disk generation against the cached buffer; on mismatch retries up to `MAX_PUBLISH_RETRIES = 3` (:116, Design Invariant 9), re-reading the `buffers` dict IN PLACE (:1931-1932), then invokes `publish_fn` once per attempt after a passing recheck; raises `PublishRace` when retries are exhausted.
- **Stale-snapshot publish**: the defect where `publish_fn` writes report bytes serialized from the ORIGINAL buffers while the recheck verified the REFRESHED ones. Reproduced live (probe A): a sidecar mutated once mid-flight published `size_bucket: "1-5"` while the recheck-verified input parsed to `"6-15"`.
- **`telemetry_lock`**: process-wide advisory flock (:271-298) over `LOCK_FILE_NAME = ".summarizer.lock"` (:124) inside the private telemetry dir; pre-checks the lock path with `_reject_symlink` (:280) then opens with `os.open(..., os.O_CREAT | os.O_RDWR, 0o600)` (:283-287).
- **Lock TOCTOU**: the defect that between the symlink pre-check and `os.open`, a local actor can swap the lock path to a symlink; the open follows it, breaking the private-dir guarantee and the lock's mutual exclusion. Reproduced live (probe B): with the pre-check raced away, the lock was acquired through a symlink and the attacker-chosen file was created `0o600` outside the private dir.
- **`O_NOFOLLOW`**: open-time kernel flag that refuses to follow a symlink at the final component, raising `OSError` `errno.ELOOP`; closes the race window that the pre-check alone cannot (probe C verified on this platform).
- **First-call mutation hook**: test technique for the RED fixture - a wrapper around `publish_with_recheck` whose FIRST invocation rewrites the on-disk sidecar to the gen-2 payload and every invocation delegates to the real function (restored in `finally`, same module-attribute patch idiom as the existing `on_disk_generation` patch). The hook point sits between the initial buffer read and the first recheck in BOTH the pre-fix and post-fix trees, so the pre-fix run publishes stale bytes (RED) and the post-fix run absorbs the change through the bounded retry and publishes rebuilt bytes (GREEN).
- **Pre-check-bypass patch**: test technique for the lock race fixture - temporarily replacing the module's `_reject_symlink` with a no-op so the fixture reaches `os.open` while a symlink sits at the lock path; this simulates exactly the raced-away pre-check, no sleeps or threads.
- **Fresh-expectation derivation**: the RED fixture's expected GREEN bytes are computed after `cmd_strict_audit` returns by parsing the current on-disk sidecar and running the real pipeline (`parse_payload` -> `build_effectiveness_report([("baseline", payload)])` -> `serialize_effectiveness_json`), never by hand-editing observed output (UL#253). The derivation's byte-equality relies on the deterministic serializer, which the existing `determinism` selftest family guards (the dependency was verified against it in this plan's probes).
- **Skill-gate marker**: consent marker at `~/.ai-playbook/runtime/skill-invoked/plans.<project>.<session>.marker` refreshed before every plan-file write per `agents/hooks/skill-gate/README.md` (Marker WRITE RECIPE); `session` derives from the `session_channel.py` subprocess output (empty-after-strip -> literal `no-session`; otherwise `sha1(value)[:16]`).
- **Session key**: the `session_channel.py` subprocess idiom `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"`, passed as `--session-id "$SID"`; omitted when empty.

## Assumptions

- assume the F4 fix keeps `publish_with_recheck`'s bounded-retry contract and rebuilds report bytes inside the caller's publish closure from the current buffers, rather than failing fast on first change; basis: Design Invariant 9 (`MAX_PUBLISH_RETRIES = 3`, :116) and existing selftests pin "exhaust retries then raise", "publish NOT called on race" (:2724-2765), and success-path digest match (:2767-2785); the backlog lists the rebuild shape as an accepted fix.
- assume the in-place `buffers` refresh (:1931-1932) becomes documented, load-bearing contract in `publish_with_recheck`'s docstring (stateful-helper rule: the mutated parameter is named); basis: the fix makes `publish_fn` correctness DEPEND on seeing refreshed buffers.
- assume the lock fix adds `os.O_NOFOLLOW | os.O_CLOEXEC` to the existing `os.open` flags and keeps the `_reject_symlink` pre-check; basis: backlog suggestion, probe C (ELOOP raised, target not created), `O_CLOEXEC` prevents fd inheritance across the selftest's own subprocess/multiprocessing use.
- assume new selftests live beside the behavior they pin: the stale-report fixture as a NEW end-to-end family (harness = the `_t_baseline_lifecycle` HOME-isolation wrapper :2562-2577 plus the `_lifecycle_inner` body :2579-2640) and the lock fixtures as two arms inside `snapshot_races` (:2685); basis: `snapshot_races` is the existing race family (subset `permissions`), and the only existing selftest caller with report arguments (`historical_immutability`, :4041-4056) checks return code and input immutability, not publish freshness, so the mutation scenario needs its own family (the CLI dispatch is the other report-argument caller and flows through the same closure, needing no separate change).
- assume the backlog file `2026-08-28-telemetry-lock-symlink-toctou.md` moves to `backlog_completed_dir` at plan completion while `2026-08-28-summarizer-cli-followups.md` STAYS in place with F4 marked fixed (F12 remains open); basis: backlog lifecycle (one item of two done).

## Gist & Examples

Both defects live in `scripts/summarize_review_stats.py`, the tool that aggregates review sidecars and publishes effectiveness reports - the reporting chain of this repo's review quality gate. Today both are silent: one publishes a report that contradicts the input the safety gate just verified; the other can be redirected by a symlink swap into writing the lock file at an attacker-chosen path.

**Change 1 - rebuild at publish time.** `cmd_strict_audit` computes the report once, then hands `publish_with_recheck` a closure holding the serialized bytes. When the gate detects an input change it re-reads the buffers and rechecks against the fresh bytes - but the closure still writes the old bytes. Example (executed probe A): sidecar says `raw_findings: 1` (bucket `1-5`) at read time; a concurrent write makes it `raw_findings: 8` (bucket `6-15`); the recheck detects the change, retries, verifies the `6-15` bytes, and then publishes a report whose cohort says `1-5`. After this plan the publish closure recomputes the report from the current `buffers` dict inside `publish_fn`, so the published bytes are derived from exactly the input the recheck verified (`6-15`). The bounded-retry semantics do not change: a persistently changing input still exhausts 3 retries and raises `PublishRace` without publishing.

**Change 2 - kernel-level symlink refusal on the lock open.** `telemetry_lock` rejects a symlink sitting at the lock path, then opens with plain `O_CREAT | O_RDWR`. A symlink swapped into the window is followed (probe B: lock acquired through it, `0o600` file created at the attacker-chosen path). After this plan the open carries `O_NOFOLLOW | O_CLOEXEC`, so a symlink at open time raises `OSError` `ELOOP` and nothing is created through it (probe C). The pre-check stays for the friendly `PermissionsError` on the static case.

**Edge cases that shaped the design.** The mutation may land before the first recheck (single retry, publish proceeds with fresh bytes) or keep landing (exhaust retries, `PublishRace` - existing pinned behavior, unchanged). The static symlink case keeps its existing `PermissionsError` (characterization fixture). `O_CLOEXEC` is added with `O_NOFOLLOW` because the selftest suite itself uses subprocess/multiprocessing and an inherited lock fd would extend the flock's lifetime beyond the holder's intent.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the stale-report fixture (Task 1) fails on today's bytes and passes after Task 2; the published report equals an independently derived serialization of the recheck-verified input; bounded-retry pins (:2724-2785) stay green unchanged.
- security: the lock race fixture fails on today's bytes and passes after Task 3; a symlinked lock path never creates a file through the symlink (`ELOOP`, target absent); static-symlink `PermissionsError` preserved.
- maintainability: the in-place `buffers` refresh and the publish-time rebuild contract are stated in `publish_with_recheck`'s docstring; no signature changes anywhere.
- test coverage: every new behavior has a fixture that is RED before its GREEN task and GREEN after, run through the real entry points (`cmd_strict_audit`, `telemetry_lock`), not replicas.

**Done when:**
- `python3 scripts/summarize_review_stats.py --selftest` exits 0 with all new fixtures green.
- The Task 1 fixture demonstrates RED on the pre-fix tree and GREEN after Task 2 (recorded outputs in the task log).
- Arm (d) of `snapshot_races` demonstrates RED on the pre-fix tree and GREEN after Task 3; arm (c) (characterization) stays green on both trees.
- No function signature changed; `rg -n "def publish_with_recheck|def telemetry_lock" scripts/summarize_review_stats.py` shows the same parameters as today.

**Ship when:**
- The change rides the repository's normal feature-branch merge; no external deployment or cross-team condition applies (local tooling).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/summarize_review_stats.py` - ONLY these regions: `cmd_strict_audit`'s classify/build/publish block (:2056-2088 in today's tree), including extracting a local report builder used by the publish closure; `publish_with_recheck`'s docstring (:1901-1908); `telemetry_lock`'s `os.open` call (:283-287); the `snapshot_races` selftest family (:2685-2786); the new end-to-end selftest family (new, placed beside the other `@_test` families); one line in `_SUBSET_OF` (:4109) mapping the new family to a subset tag.

**Tests:**
- contained in `scripts/summarize_review_stats.py` (the selftest suite is in-file; listed above).

**Freeze note:** all other regions of `scripts/summarize_review_stats.py` are frozen, including `publish_with_recheck`'s control flow and signature, `on_disk_generation`, `read_byte_buffer`, `_reject_symlink`, `parse_payload`, `build_effectiveness_report`, the baseline/ledger commands, and every selftest family not named above; reject any review finding that touches them unless it is plan-related under the extension rule.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- F12 source-flag triplication in `scripts/validate_review_staging.py`; reason: a separate backlog item (validator selftest pass) deliberately excluded from this plan.
- `scripts/scan-public-hygiene.sh` and other repo gates; reason: untouched by this plan's contract.

## Validation Commands

```bash
cd "$(git rev-parse --show-toplevel)"
python3 scripts/summarize_review_stats.py --selftest
python3 scripts/summarize_review_stats.py --selftest --subset permissions,lifecycle
rg -n "O_NOFOLLOW.*O_CLOEXEC|O_CLOEXEC.*O_NOFOLLOW" scripts/summarize_review_stats.py
```

The scoped `--subset permissions,lifecycle` run gates the race/lock arms (`permissions`) and the new stale-snapshot family (`lifecycle`); the full `--selftest` adds the remaining families plus the pinned bounded-retry behavior; the `rg` pin expects exactly one match after Task 3 (the `os.open` flags line in `telemetry_lock` carrying BOTH new flags, so the close-on-exec half of the change is pinned too; the Task 3 comment is worded to avoid both flag tokens, and the selftest fixtures assert `ELOOP` behavior without naming either flag), validating the flags survived review edits.

### Task 1: RED fixtures for stale-snapshot publish and lock race (fail today, no production change)

Files:
- `scripts/summarize_review_stats.py`

- [x] New selftest family `summarize_review_stats#strict_audit_stale_snapshot` (placed beside the other `@_test` families; add a `_SUBSET_OF` entry mapping it to `"lifecycle"`); harness = copy the HOME-isolation wrapper from `_t_baseline_lifecycle` (:2562-2577, sets and restores the `HOME` environment variable) around the `_lifecycle_inner` body pattern (:2579-2640): facts table with `personal_projects_root`, repo with `.ai-playbook/facts.md` `reviews_dir = "docs/reviews/"`, sidecar `docs/reviews/x.stats.json` = `_make_current_payload(["quality"])`, `tel = td/review-telemetry`, `bp = tel/baseline.json`, `cmd_init_baseline(facts, bp, tel)` must succeed.
- [x] In the same family, install the first-call mutation hook before the audit: wrap the module's `publish_with_recheck` so its FIRST invocation rewrites the sidecar via `_write_private_sidecar(sc, p2)` where `p2 = _make_current_payload(["quality"])` with `p2["counts"]["raw_findings"] = 8` (size bucket `1-5` -> `6-15`), and every invocation delegates to the real function; restore the original in `finally`. The hook fires between the initial buffer read and the first recheck in both the pre-fix and post-fix trees, so the pre-fix run absorbs the change through the retry and publishes stale bytes, and the post-fix run publishes rebuilt bytes. Patch and restore the module attribute exactly like the existing `on_disk_generation` patch (:2740-2763).
- [x] `strict_audit_stale_snapshot: published report matches recheck-verified input` (check label in the file's `family: description` convention); given the harness above and `cmd_strict_audit(facts, bp, tel, json_report=out)` (out under the temp dir), expects return code 0 (the one-time change is absorbed by the bounded retry, no `PublishRace`), and ONE combined check that (a) the bytes of `out` equal the fresh-expectation derived AFTER the call by parsing the current on-disk sidecar and computing `serialize_effectiveness_json(build_effectiveness_report([("baseline", payload)]))` AND (b) those bytes differ from `serialize_effectiveness_json(build_effectiveness_report([("baseline", parse of the original gen-1 payload)]))` - one combined predicate, not two separate checks, because pre-fix the differ half is ALSO false (the serializer is deterministic, so the stale bytes equal the gen-1 derivation) and the differ half exists to prove the scenario is observable, not to gate independently (period is `"baseline"` because the sidecar is in the baseline snapshot - init ran after sidecar creation). Run -> expect RED exactly on this combined check (today the closure writes the pre-mutation bytes; witnessed by probe A3/A4).
- [x] In `snapshot_races`, arm (c) `snapshot_races: static symlink at lock path rejected` (characterization, GREEN today): FIRST remove arm (a)'s leftover regular lock file (`lock_path.unlink(missing_ok=True)`), then pre-create the symlink target's parent under the fixture temp dir (`t2 = td_path / "t2"; t2.mkdir()`) so the not-created assertion is falsifiable, then create `os.symlink(t2 / "target", lock_path)` UNGUARDED and assert `lock_path.is_symlink()` (a guarded create is wrong here: the path's occupation by the arm (a) lock file is itself the fixture hazard this removal addresses), then enter `with telemetry_lock(tel):` inside try/except so the exception surfaces at `__enter__` (a bare call only constructs the context manager and runs nothing), expects `PermissionsError` and `t2 / "target"` NOT created; then `lock_path.unlink()` (asserting removal) so arm (d) starts from a clean lock path.
- [x] In `snapshot_races`, arm (d) `snapshot_races: symlink swap in race window fails closed` (RED today): pre-create the attack-target parent under the fixture temp dir with `evil = td_path / "evil"; evil.mkdir()` (outside the telemetry dir, inside the TemporaryDirectory so teardown cleans it), create `lock_path` as a symlink to `evil/outside.lock` UNGUARDED and assert `lock_path.is_symlink()` (the same create discipline as arm (c), not a bare existence check), patch the module's `_reject_symlink` to a no-op (comment: simulates the pre-check passing before the swap - the race window this arm pins), enter `with telemetry_lock(tel):` inside try/except, expects `OSError` with `exc.errno == errno.ELOOP` specifically (an errno-specific check distinguishing ELOOP from any other open-time OSError; note the module's permission error class is a summarizer error, not an `OSError` subclass, so arm (c) catches it by its module name), the attack target NOT created, and the original `_reject_symlink` restored in `finally` - write the ELOOP expectation and the target-not-created expectation as two separate checks (the Task 1 and Task 2 failure counts assume check granularity); then `lock_path.unlink()` (asserting removal) so the family ends with a clean lock path on both the RED and GREEN outcomes. Run -> expect RED exactly on the ELOOP and target-not-created checks (today the open follows the symlink; witnessed by probe B1/B2).
- [x] Run `python3 scripts/summarize_review_stats.py --selftest` -> expect RED: failures reported exactly on the new family's combined fresh-equality-and-gen-1-differ check and arm (d)'s ELOOP and target-not-created checks (three failing checks total); every pre-existing family and the arm (c) characterization stay green.
- [x] Commit: `test: red fixtures for stale-snapshot publish and lock symlink race`

### Task 2: GREEN - rebuild report bytes from current buffers at publish time

Files:
- `scripts/summarize_review_stats.py`

- [x] In `cmd_strict_audit`'s classify/build/publish block (:2056-2088), replace the pre-publish report construction with a `_publish()` closure that: (1) classifies from the CURRENT `buffers` dict (snapshot-path membership + ledger growth membership, exactly as the pre-existing :2056-2067 block does - extract that classification into one local helper so the rules exist once), (2) builds the report via `build_effectiveness_report(classified)`, (3) emits the `skipped_malformed` stderr note (:2071-2078 wording) from THAT same report before writing, so the operator pointer always matches published bytes (on a race exhaustion nothing is published, so nothing is emitted and nothing is written - an accepted delta from today's pre-gate placement, with no selftest pinning the stderr text; the note's emission stays independent of whether output paths are None and remains gated on a nonzero skipped count as today), (4) serializes both formats and writes via the two `_atomic_write_private` calls. The `publish_with_recheck(buffers, _publish)` call itself is unchanged, and the anomaly ledger (`audit`/`ledger`/`replaced`) keeps its pre-publish placement, untouched.
- [x] Update `publish_with_recheck`'s docstring (:1901-1908) to state the load-bearing contract: the `buffers` dict is refreshed IN PLACE on retry, `publish_fn` is invoked after that refresh, and a `publish_fn` that writes bytes serialized before the recheck - ignoring the refreshed buffers - publishes a stale snapshot that passes the gate; every caller MUST derive published bytes from the current buffers. Cohort membership is pinned to the pre-publish ledger (only payload content follows the refreshed buffers): recomputing membership would require the conservation-ledger computation earlier in the function, which this plan freezes, so the classification helper keeps the pre-publish ledger as-is.
- [x] Run `python3 scripts/summarize_review_stats.py --selftest` -> expect the suite STILL RED by design at this point: the Task 1 combined fresh-equality-and-gen-1-differ check now passes and the three pre-existing race pins (`changed input retries then fails publish`, `publish NOT called on race`, `published digest matches parse buffer`) stay green WITHOUT modification, while arm (d)'s ELOOP and target-not-created checks remain RED until Task 3 (suite exits nonzero with exactly those two failures; do NOT pull the Task 3 flag change into this commit).
- [x] Commit: `fix: strict audit rebuilds report bytes from recheck-verified buffers`

### Task 3: GREEN - open the telemetry lock with O_NOFOLLOW|O_CLOEXEC

Files:
- `scripts/summarize_review_stats.py`

- [x] In `telemetry_lock` (:283-287), change the open flags to `os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC`, keeping both new flags on the same line as each other in the open call (the validation pin is line-based); keep the `_reject_symlink(lock_path)` pre-check and the umask save/restore exactly as they are; add a one-line comment stating the kernel flag refuses a symlinked final component at open time (ELOOP), closing the pre-check-to-open race window, and CLOEXEC keeps the lock fd out of child processes. The comment must NOT contain the literal flag token, so the Validation Commands single-match pin stays true.
- [x] Run `python3 scripts/summarize_review_stats.py --selftest` -> expect GREEN (full suite, first time since Task 1): arm (d)'s ELOOP and target-not-created checks now pass; arm (c) `PermissionsError` stays green; `snapshot_races: second holder blocked` stays green (the flock path is unchanged for regular files).
- [x] Run `rg -n "O_NOFOLLOW.*O_CLOEXEC|O_CLOEXEC.*O_NOFOLLOW" scripts/summarize_review_stats.py` -> expect exactly one match: the `os.open` flags line in `telemetry_lock` carrying both new flags (order-insensitive, so a correct implementation in either flag order passes), so the close-on-exec half of the change is pinned too; the Task 3 comment and the fixtures name neither token, so the flags line is the only possible match.

### Task 4: backlog lifecycle (partial: telemetry item closes, summarizer file stays open)

Files:
- `docs/history/backlog/2026-08-28-telemetry-lock-symlink-toctou.md`
- `docs/history/backlog/completed/2026-08-28-telemetry-lock-symlink-toctou.md` *(new)*
- `docs/history/backlog/2026-08-28-summarizer-cli-followups.md`
- `docs/history/backlog/2026-09-01-private-dir-symlink-toctou.md` *(new)*

- [x] `git mv docs/history/backlog/2026-08-28-telemetry-lock-symlink-toctou.md docs/history/backlog/completed/` and mark its header `Status: closed 2026-09-01 (fixed by docs/plans/2026-09-01-summarizer-publish-lock-hardening.md: O_NOFOLLOW lock open)`, matching the repo's completed-backlog convention; append a one-sentence residual-risk note stating the same threat model remains open for the private-path helpers that rely on pre-check-only symlink defenses (`ensure_private_dir`, `_atomic_write_private`, `tighten_parent_ai_playbook`, `read_private_file`; kernel-grade fix out of scope here) and pointing at the successor item.
- [x] Create `docs/history/backlog/2026-09-01-private-dir-symlink-toctou.md` (`Status: open`, `Workflow: backlog`, source: `docs/reviews/2026-09-01-plan-review-summarizer-publish-lock-r1.md`, round r1, findings F6 + F9, risk worker) capturing the symlink TOCTOU follow-up for the class of private-path helpers that defend symlink swaps with a pre-check only, naming all four sites (`ensure_private_dir`, `_atomic_write_private`, `tighten_parent_ai_playbook` at dir granularity; `read_private_file` at file granularity; `create_private_file_exclusive` is file-level safe via its exclusive create and carries only the parent-dir window), with a rider noting the raced lock failure surfaces as a raw ELOOP traceback with no pointer to the lock path (operator-UX follow-up).
- [x] In `2026-08-28-summarizer-cli-followups.md`, update item 1's status in place: F4 fixed 2026-09-01 by this plan; F12 remains open (do not move this file to `completed/`).
- [x] Verify with `git status --short` that the move is staged as a rename and the summarizer file is modified in place, not deleted.
- [x] Commit: `docs: close telemetry TOCTOU backlog item, open dir-level successor, keep summarizer F12 open`

### Task 5: final validation

Files:
- none (verification only)

- [x] Run the full Validation Commands block; all three commands green (`--selftest` exit 0, `--subset permissions,lifecycle` exit 0, single flags-line match for the two-flag pin).
- [x] Freeze audit: `git diff "$(git merge-base main HEAD)" -- scripts/summarize_review_stats.py` touches only the regions named in Review Scope (strict-audit publish block, `publish_with_recheck` docstring, `telemetry_lock` open flags, `snapshot_races` arms, new family + `_SUBSET_OF` line); any other hunk is a defect to fix before done.
