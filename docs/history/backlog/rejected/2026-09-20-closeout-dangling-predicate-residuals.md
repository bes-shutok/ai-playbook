# Backlog: closeout dangling-symlink predicate residuals (Task 6 review)

Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; errno-classification nuance, hypothetical. Revive on a witnessed EACCES-class stat failure swallowed, or a project-priority-profile change.)

Status: rejected (2026-09-26; unwitnessed hardening: hypothetical errno-classification and structural-marker nuances; no witnessed case)
- Origin: Task 6 intermediate review (r1 F1, F2) of 2026-09-20-merge-landing-lock-grouping; verdict backlogged-candidates
- Driving force: the dangling-symlink containment classifies by `Path.exists()`, which conflates ENOENT with any stat OSError (e.g. EACCES behind an unsearchable parent), and a verify-seam failure after a successful copy leaves that copied target recorded only via the incomplete marker's message.

## Items

1. If the containment scope is ever tightened, restrict the dangling classification to errno ENOENT so EACCES-class stat failures propagate loudly instead of skip-warning.
2. When `_verify_copy` fails after `_copy_file` succeeded, consider recording the destination path in the incomplete marker (the message usually carries it, but not structurally).
