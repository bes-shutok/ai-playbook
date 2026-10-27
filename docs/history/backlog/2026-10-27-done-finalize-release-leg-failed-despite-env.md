# Backlog: a failed finalize release reports neither the env values it read nor the manifest's completion state

- **Filed:** 2026-10-27
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Cluster:** `docs/history/backlog/2026-10-18-done-lock-from-holder-generation-binding.md` (same surface - `done_run.sh` finalize's done-lock release - different defect: that row owns the `--from-holder` generation-binding risk, this row owns the release leg's refusal observability)
- **Skill/step:** `scripts/done_run.sh` finalize (the done-lock release leg and the post-release FAILED status check, scripts/done_run.sh ~2198)
- **Class:** fix-class
- **Origin class:** session witness (ad-hoc exec run closeout mechanics)

## Finding

In an ad-hoc worktree run whose setup-phase done-lock exports died with their tool-call shells, the session re-derived the lock dir and token from the live hold's `meta.env` on disk and re-ran finalize with that env exported. The first finalize pass completed the run manifest ("the manifest already finalized; nothing to refresh") but then reported `FAILED: done lock status is not free after the release` - the release leg did not free the hold, and its output named neither which env values it consumed nor whether the manifest had completed. A second invocation with cleanly hardcoded env values released the lock immediately. Re-derivation at filing time (2026-10-27): the first pass's token was produced by an unverified shell capture whose pipeline echoed the token to stdout (a malformed-capture signature), so the session-side env is the suspected cause and the release leg's contract behavior is not proven defective; the witnessed, transferable cost is the diagnosis round the session spent guessing, because the failed release is silent about its own inputs and the FAILED line does not distinguish a completed manifest from an incomplete one.

## Expected

A release-leg refusal (or a FAILED post-release check) names the lock dir and a token prefix it actually read (or reports the env as empty/malformed), and the FAILED line distinguishes a completed manifest (a release-only retry is safe) from an incomplete one.

## Suggested direction

Bounded arm: string-level output edits on the release leg's refusal path and the FAILED check in scripts/done_run.sh, plus a suite pin per shape if the wrapper suite pins those lines. No behavior change to the lock contract; no new lock, gate, or ceremony.

## Evidence

- Witnessed 2026-10-27 in an ad-hoc exec run's pick closeout: first finalize pass output (manifest-complete line, held-status block, the FAILED line), second pass output (release removed, status free) - both re-read from the run output before this row was filed.
- The hold's `meta.env` carried the same repo_root, label, and dead holder PID in both passes; the release subcommand's env-verification refusal shape is visible in `scripts/done-lock.sh` (release requires matching `DONE_LOCK_DIR`/`DONE_LOCK_TOKEN`).
