# Backlog: worktree closeout migration robustness residues (review r1 F6)

<<<<<<<< HEAD:docs/history/backlog/completed/2026-09-20-closeout-migration-robustness-residues.md
Status: done
Priority: low
========
Status: open
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; robustness residues deferred at r1. Revive on a witnessed migration failure of these shapes, or a project-priority-profile change.)
>>>>>>>> f8fbd660 (backlog: defer 72 formal items per project-priority full sweep):docs/history/backlog/deferred/2026-09-20-closeout-migration-robustness-residues.md
Workflow: backlog
Date: 2026-09-20
Class: closeout tool hardening (review r1 deferred set)

## Problem

Four residues deferred from review r1 of scripts/worktree_closeout_migrate.py
and related surfaces:

1. `capture` crashes with a raw traceback on a dangling symlink inside the
   captured dirs (loud but unclean; blocks run start).
2. The migration manifest is written only after the full copy loop: a
   mid-loop exception orphans already-copied, verified files from the audit
   record (write in a finally, or per-file entries).
3. The testing verify-error arm patches `_copy_file`, bypassing production
   copy semantics; the copy-never-move invariant is only incidentally
   covered. Tamper the verify seam instead, or add an unpatched
   source-survives assertion.
4. docs-branch SKILL.md prose made stale by the run: the failure-semantics
   enumeration omits the new certified-downgrade refusal, and execute-plan's
   throwaway-script rationale still says docs-branch "never auto-prunes".

Also guard residues (r1 F4 + risk lens): `check-restored --plans-dir` is
accepted but unused; a missing dedupe script skips silently while the guard
warns loud; an unreadable plan file makes the guard fail closed by accident
(traceback instead of a named skip-and-warn).
