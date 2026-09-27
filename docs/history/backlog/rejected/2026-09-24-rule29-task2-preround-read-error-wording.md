# Backlog: rule29 Task 2 run_pre_round conflates I/O read failures with decode failures

- Status: rejected (2026-09-27; error-message wording; exit contract already fail-closed and correct)
- Date: 2026-09-24
- Driving force: code-quality
- Origin: intermediate review of Task 2 (execute-plan run, worktree ai-playbook-exec-rule29, 2026-09-24); Low, non-blocking.

`run_pre_round`'s single `except (OSError, UnicodeDecodeError)` labels every read failure "cannot read plan bytes (not valid UTF-8)", so a non-decode I/O error (permission denied, race deletion) is mislabeled. The exit contract stays fail-closed and correct; the plan only pinned the decode case. On the next natural touch, split the OSError leg into its own reason string mirroring the full gate's wording.
