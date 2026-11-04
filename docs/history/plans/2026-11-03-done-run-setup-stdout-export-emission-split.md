# Plan: done run setup stdout export emission split

Backlog origin: docs/history/backlog/2026-11-03-done-run-setup-stdout-export-emission-split.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-03-plan-review-done-run-setup-stdout-export-emission-split-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2h total, largest task 1h

Authoring claim: done-run-setup-stdout-export-emission-split.md (session sess_0579a3dc-7408-418d-bdf3-b7eea257a06e)

## Terms

- acquisition surface: the stdout a caller evaluates to enter a done run or hold a lock: the `done_run.sh setup` exports and the `done-lock.sh` acquire / wait-acquire export echo.
- eval-safe: stdout that parses as shell assignment lines only, so a whole-stdout `eval` or `source` cannot abort on prose.
- payload line: an `export`-prefixed assignment line whose bytes must not change between the old and new emission.

## Why

The done skill tells callers to evaluate only the `export` lines of the acquisition output, but `done_run.sh setup` prints human-readable status lines on the same stdout, and a refusal path can still reach stdout through printf-based relay emissions. Two field runs consumed the whole stdout anyway, the status lines aborted the parse mid-file, and each failure leaked an acquired lock plus a partial run boundary that a later invocation had to re-enter or orphan-release. The `done-lock.sh` acquire echo already routes its prose to stderr (measured at review r1); this plan keeps that shape true by pinning it in its focused suite instead of re-implementing it.

## Gist & Examples

TLDR: the setup acquisition stdout carries only eval-able assignment lines and every status, advisory, and diagnostic line (plain echo or printf relay) moves to stderr, while the already-compliant lock acquire echo gets pinned by its suite, so the documented filter rule becomes a belt instead of the only thing standing between the caller and a leaked hold (driving force: code-quality).

**Before (today):** a caller runs `eval "$(bash scripts/done_run.sh setup ...)"`. The stdout mixes one or more `done_run setup: ...` status lines with the `export DONE_RUN_MANIFEST=...` block. A status line containing shell metacharacters (the 2026-11-03 witness raised a brace parse error) aborts the eval after setup already acquired the lock and wrote the boundary, leaving the caller with no exports in env and a live hold. The 2026-10-26/27 witness sourced a tee'd capture and the interleaved prose aborted `source` mid-file the same way.

**After (this plan):** the same setup run prints only `export` lines on stdout; every `done_run setup: ...` line, whether a plain echo or a printf relay, goes to stderr. The same `eval` consumes clean assignments, the caller's env carries the exports, and a status line can never abort the parse. The `done-lock.sh` acquire echo already behaves this way (success stdout is exactly the two export assignment lines, blocked stdout is empty, diagnostics are on stderr); its focused suite pins that shape so it cannot regress. A caller that still evaluates only the `export` lines (the done skill's Step 0 rule) behaves identically, because the payload lines are byte-identical.

**Edge cases:**
- Blocked acquire and wait-acquire timeouts already print holder diagnostics; those diagnostics must land on stderr in both scripts so a blocked acquire leaves stdout empty.
- The re-entered boundary path (`--from-manifest`) and the interrupted partial-marker classification stop also emit status lines beside exports; both move to stderr with their exports unchanged.
- The commit and finalize subcommands of `done_run.sh` and every `done-lock.sh` release, status, stale-clean, and selftest path are out of scope: this plan splits the acquisition surfaces only.

## Outcome

The machine-consumed acquisition output is eval-safe by construction, so a caller that evaluates the whole stdout can no longer abort mid-parse after a hold was taken.

- `done_run.sh setup` success, re-entry, and refusal paths keep stdout to `export` lines only; status, advisory, diagnostic, and printf-relayed lines print on stderr.
- The `done-lock.sh` acquire and wait-acquire echoes are already eval-safe in the current bytes; their focused suite pins the measured shapes (success stdout assignments-only, blocked stdout empty, holder diagnostics on stderr) so the shape cannot regress.
- The two focused suites pin the operative shapes, and the done skill's Step 0 sentence states stdout is now eval-safe (correcting the stale one-status-line sentence) while the evaluate-only-export-lines rule stays as the consumer-side guard.

Gate delta: none (an emission split only; no refusal class, hard gate, fence, protocol layer, or schema field is added or removed, and no dispatch-pausing condition is introduced).

## Assumptions

- assume the payload export lines stay byte-identical between the old and new surfaces; basis: origin row Expected section (the documented filter rule becomes a belt, so existing filtered consumers see no change).
- assume stderr is the destination for status, advisory, and diagnostic lines; basis: origin row Suspected root area names exactly this split.
- assume no consumer depends on the removed stdout status lines; basis: Task 3's sweep verifies each consumer of the banner patterns and names its post-change behavior instead of assuming.
- assume the acquisition scope is exactly `done_run.sh setup` and the `done-lock.sh` acquire / wait-acquire echo, with the lock echo already measured compliant so its arm is a pinning arm, not a move arm; basis: origin row Suspected root area, the origin entry's scope arms, and review r1 finding F1's measured probe of the current bytes.
- assume done-lock timeout values, stale-clean thresholds, and recovery arms are unchanged; basis: origin entry Rejected alternatives (no policy split, no new machinery, no gate).

Decision points requiring a grill: none remain.

## Evaluation Criteria

- correctness: every status, advisory, and diagnostic emission on the acquisition path carries a stderr redirect; the stdout of a successful setup or acquire contains only `export`-prefixed lines.
- compatibility: the export payload lines are byte-identical before and after; a whole-stdout eval of a successful acquire parses without error, and a blocked acquire contributes nothing to stdout.
- test coverage: the focused suites assert the assignment-lines-only stdout shape and the stderr presence for status lines, including a fixture status line carrying shell metacharacters.
- documentation: the done skill Step 0 sentence names the stdout as eval-safe and keeps the filter rule as the consumer-side guard.

**Done when:**
- both focused suites pass green at the new shapes.
- a scripted eval of a fixture `done_run.sh setup` stdout completes with the exports set and no parse error.
- the consumer sweep greps clean: no consumer parses a removed stdout status line.

**Ship when:**
- none stated (repository-verifiable only).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_run.sh` (Task 1)
- `scripts/done-lock.sh` (Task 2)

**Tests:**
- `scripts/test_done_run_wrapper.py` (Task 1)
- `scripts/test_done_lock_holder_visibility.sh` (Task 2)

**Documentation:**
- `agents/skills/done/SKILL.md` (Task 3)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/done_run.sh` commit and finalize subcommand banners; reason: the origin scopes the acquisition surfaces (setup, acquire, wait-acquire), not the commit and finalize emissions.
- `done-lock.sh` release, release-repo, release-orphaned, status, stale-clean, and selftest emission shapes; reason: those paths already carry their prose on stderr in the current bytes and sit outside the acquisition echo this plan splits.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_run_wrapper.py -q
bash scripts/test_done_lock_holder_visibility.sh
```

### Task 1: Split the setup acquisition emission in scripts/done_run.sh

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/done_run.sh`
- `scripts/test_done_run_wrapper.py`

Primary class anchors:
- `cmd_setup` in `scripts/done_run.sh`

- [ ] `cmd_setup` delivers eval-safe acquisition stdout: given a successful fixture setup run over a scratch checkout, expects stdout lines that all parse as shell assignment lines (every line starts with `export `) and the full stdout evaluating without error under `eval` [class: REPOSITORY_TEST]
- [ ] `cmd_setup` delivers the byte-identical payload contract: given the same fixture run captured before and after the change, expects the `export` lines byte-identical between the two captures [class: REPOSITORY_TEST]
- [ ] `cmd_setup` delivers the stderr split: given the re-entered boundary path and the interrupted partial-marker classification stop, expects their `done_run setup: ...` status and diagnostic lines on stderr and their exports unchanged on stdout [class: REPOSITORY_TEST]
- [ ] `cmd_setup` delivers the eval-safe refusal shape: given a refused fixture setup run, expects stdout carries no unparseable prose (printf-relayed release-output and writer-echo lines included in the move set, alongside plain echoes; the contract's `OUTCOME:` channel line stays on its own contract-owned channel and is not part of this move set) [class: REPOSITORY_TEST]
- [ ] Run the canary additions against the current tree; expect RED: the success-path stdout still carries plain status `echo` lines beside the export block (tests and fixture wiring are selected at execution from the suite's existing harness) [class: REPOSITORY_TEST]
- [ ] Move every status, advisory, and diagnostic emission on the `cmd_setup` acquisition path to stderr regardless of the emitting builtin (plain `echo` lines and printf-based relay lines alike), keeping each `export` line byte-identical on stdout [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the new cells pass, and the suite's stdout-pinned cells that assert the moved status lines in `proc.stdout` are updated to the new shapes in the same task (execution derives the affected cells from the suite; the current tree pins at least the residue-sweep relay family, failing-sweep relay, foreign-by-arrival writer-echo relay, and adopt-forward note in stdout), leaving the updated suite green [class: REPOSITORY_TEST]
- [ ] Commit: `fix: setup stdout carries only eval-able export lines, status lines to stderr` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Pin the already-eval-safe acquire and wait-acquire echo in scripts/done-lock.sh

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/done-lock.sh`
- `scripts/test_done_lock_holder_visibility.sh`

Primary class anchors:
- `cmd_acquire` in `scripts/done-lock.sh`
- `cmd_wait_acquire` in `scripts/done-lock.sh`

This task is a pinning task, not a move task: review r1's measured probe found the acquire and wait-acquire acquisition surfaces already eval-safe in the current bytes (a blocked wait-acquire and a blocked direct acquire each print zero bytes on stdout, a successful acquire prints exactly the two export assignment lines, and the holder diagnostics already print on stderr), so the origin's move arm is already satisfied and this task characterizes and pins that shape instead of re-implementing it.

- [ ] `cmd_acquire` and `cmd_wait_acquire` deliver eval-safe acquisition stdout: given a successful fixture acquire over a scratch lock directory, expects stdout lines that all parse as shell assignment lines and a whole-stdout eval completing without error [class: REPOSITORY_TEST]
- [ ] The lock echo delivers the blocked-path shape: given an acquire or wait-acquire that hits a held lock or times out, expects stdout empty of prose (holder wait diagnostics, timeout reports, and blocked holder evidence on stderr) and no partial assignment line on stdout [class: REPOSITORY_TEST]
- [ ] Characterization cells assert the measured shapes above against the current tree; expect GREEN before any change (execution adds them to `scripts/test_done_lock_holder_visibility.sh` only where the suite does not already pin the shape, per its own r1 finding F1 verification) [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the characterization cells pass with no production change; if any cell cannot pass against the current bytes, that measured gap is a real regression and is reported for triage instead of being papered over [class: REPOSITORY_TEST]
- [ ] Commit: `test: pin the lock acquisition echo eval-safe shapes (already compliant)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Consumer sweep and done skill Step 0 sentence

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/done/SKILL.md`

- [ ] Sweep consumers of the acquisition banner: grep scripts and skills for consumers that eval, source, tee, or otherwise parse the setup or acquire stdout (the `DONE_RUN_` and lock-export banner patterns), name each consumer and its post-change behavior in the task log, and verify none depends on a removed stdout status line; a consumer that does gets its minimal fix folded here as plan-related work [class: REPOSITORY_TEST]
- [ ] The done skill Step 0 success paragraph is corrected in place: the stale sentence stating setup prints one status line plus eval-able exports is rewritten to the new shape (stdout carries only eval-able export lines; status and diagnostics on stderr), and the same passage notes the stdout is now eval-safe while the evaluate-only-export-lines prescription stays as the consumer-side guard [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the final battery: both focused suites green (Validation Commands above) and a scripted whole-stdout eval of a fixture acquire completing with the lock exports set [class: REPOSITORY_TEST]
- [ ] Commit: `docs: done Step 0 notes eval-safe acquisition stdout` [class: IMPLEMENTATION_REQUIRED]
