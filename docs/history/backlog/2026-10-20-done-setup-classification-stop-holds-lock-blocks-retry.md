# Backlog: done setup's classification stop exits holding the lock, so the remedy-then-retry path blocks on the session's own hold

- **Filed:** 2026-10-20, learn-plus-investigate closeout after the all-skills loader review (learn Step 1.8 capture)
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** session-witnessed runner ordering friction (lock acquired before a fail-closed stop that keeps it)
- **Class:** fix-class
- **Driving force:** simplicity (the stop's own remedies cannot be followed by a plain setup retry; the only exit is a hand release with a token the stopped run printed once)
- **Skill/step:** `scripts/done_run.sh` setup, `classify_partial` (the `exit 2` after "no new boundary written (read-only classification; pass --from-manifest to re-enter explicitly)"); `agents/skills/done/SKILL.md` Step 0 (setup composition order: wait-acquire precedes the partial-setup classification stop)
- **Capture hygiene:** repo-relative paths only; no personal or machine-specific data.
- **Dedup probe:** searched open backlog text for `partial-setup`, `classification stop`, `own hold`, `self-hold`, `re-enter`, `wait-acquire`; nearest rows are `2026-10-13-done-landing-commit-lock-span.md` (merge-lock spans around the landing commit) and `2026-10-20-done-run-authorized-restoration-hardening-candidates.md` (the authorized-restoration path); no open row owns the setup stop's lock handling.

- **Cluster:** docs/history/backlog/2026-10-20-finalize-ledger-append-after-landing-strands-dirt.md (shared mechanism: same runner or gate family; investigate 2026-10-20 roster)
- **Cluster:** docs/history/backlog/2026-10-13-done-landing-commit-lock-span.md (shared mechanism: same runner or gate family; investigate 2026-10-20 roster)
## Problem

Setup composes wait-acquire, then the partial-setup classification. When the classification finds a stale-marker or markerless interrupted manifest and no `--from-manifest` was passed, it prints the remedies (`recover-manifest`, adopt via `--from-manifest`, `finalize-manifest`, `disposition-manifest`) and exits 2 with the lock still held by the session, pinned to the invoking shell. Three of the four remedies are standalone commands that close the foreign boundary; after running one, the natural next step is a fresh `setup`, which wait-acquires against the session's own live hold, waits the full agent budget (90 seconds), and fails with "another done holds the lock". The operator then has to release by hand with the token the stopped setup printed, the one value the done skill says never to copy into records.

Witnessed 2026-10-20: a dead peer's lock was reclaimed by setup, the classification stop named the peer's interrupted manifest, `recover-manifest` closed it (vacuous deliverables witness), and the setup retry blocked for 90 seconds on this session's own hold before a manual `release` with the first token let the third setup succeed.

Witnessed again 2026-10-20 (execution-run closeout, a second stop class): setup's claim-or-foreign violation refusal, raised by a mis-partitioned foreign list, also exited holding the lock; the retry needed a hand release with the first token before it could run. Priority re-affirmed high: two distinct fail-closed stops share the hold-on-exit shape, so the fix belongs on the shared exit path, not on one stop.

## Expected

After a classification stop, following any named remedy and re-running `setup` succeeds without a hand release: either the stop leaves no hold behind, or the retry recognizes the hold as its own.

## Suggested fix

Smallest form first:

1. Release the just-acquired lock on the `exit 2` classification-stop path (and the fail-closed `exit 3` paths) before exiting: nothing else has been written at that point, so the stop is already a clean abort; the `--from-manifest` re-entry keeps today's behavior because it returns 0 and continues under the hold.
2. Alternatively, let wait-acquire treat a live hold whose pinned holder pid equals the caller's `DONE_LOCK_HOLDER_PID` as the caller's own and continue with the recorded token, so a retry in the same session never blocks on itself.

Rejected: documenting the manual release as the procedure (it asks the operator to re-type a token the skill text forbids copying, and spends a 90-second wait to discover the need); running the classification before the acquire (the classification reads the session directory that peers write under the lock, so it belongs inside the span); shortening the agent wait (the wait is correct for a genuine peer hold).
