# Telemetry lock file symlink TOCTOU (O_NOFOLLOW missing)

Status: open
Workflow: backlog
Source: docs/reviews/2026-08-28-review-artifact-contracts-code-review-r1.md, round r1, risk worker, pattern `security#symlink-lock-toctou` (Discarded table, out-of-scope; validated as a real defect)

## Problem

`telemetry_lock` in `scripts/summarize_review_stats.py` (around line 271) calls `_reject_symlink(lock_path)` and then opens the lock path with `os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)`. Between the symlink rejection and the open, a local attacker can replace the lock file with a symlink (TOCTOU): the open then follows the symlink and writes/locks through it, defeating the symlink defense and potentially creating the lock file at an attacker-chosen location (privilege-bound to the summarizer user, but breaks the private-dir guarantee and the lock's mutual exclusion).

## Location

- `scripts/summarize_review_stats.py`, `telemetry_lock` (lock open call, ~line 283).

## Suggested fix

Open with `os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW` (and optionally `os.O_CLOEXEC`) so the kernel refuses to follow a symlink at open time; keep the pre-check only as a friendly error. Add a selftest staging a symlinked lock path and asserting a clean failure. macOS supports `O_NOFOLLOW`.

## Severity

Low/Medium (local attacker with write access to the private telemetry dir; pre-existing on main, untouched by the review-artifact-contracts branch).

## Why not fixed now

Out of scope for the review-artifact-contracts receiving-review run: the defect pre-exists on main and the branch did not touch the lock path (risk worker verified). Decision made by the receiving-review agent per orchestrator instructions ("create a durable backlog item; do not fix the code in this run").
