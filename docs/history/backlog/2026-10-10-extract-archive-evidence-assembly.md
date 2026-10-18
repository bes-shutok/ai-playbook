# Backlog: simplify archive evidence assembly

- **Filed:** 2026-10-10
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** fresh review maintainability finding
- **Class:** maintainability
- **Driving force:** simplicity
- **Skill/step:** `scripts/done_sweep_gates_lib.py`, `_derive_archived_plans`
- **Cluster:** `docs/history/backlog/2026-10-10-deduplicate-committed-archive-charters.md` (same archive derivation function; this row covers evidence assembly and fail-closed source handling, while the sibling covers duplicate charter reporting).

- **Cluster:** docs/history/backlog/2026-10-10-consolidate-archive-index-read.md (backlog-wide survey: done archive evidence assembly)
## Problem

`_derive_archived_plans` combines staged/worktree, committed-history, and stale-deliverables discovery with repeated directory charter/task assembly. The larger coordinator also signals some evidence failures by adding unchecked-box sentinel text and later matching diagnostic substrings. This makes future changes harder to audit and risks divergence between archive sources.

A fresh review also found that `_archive_text_at_index_or_worktree` treated every nonzero result from its post-read `git ls-files --error-unmatch` recheck as proof that the path remained untracked. Only exit 1 means absent; other failures (for example exit 128) leave the index state unknown and must refuse closed. The current execution applies that narrow guard and regression while this extraction remains open.

The r7-r11 reviews found archive evidence-boundary failures: task-file symlinks, task-directory symlinks, and a regular file named `tasks` could evade enumeration or cause out-of-repo reads; diagnostics could be downgraded to notes, and the rejected-state checkbox exemption could swallow staged archive read errors. The current execution records these blockers, returns task-read errors separately from informational notes, checks staged and HEAD entry modes, rejects non-directory `tasks/` paths before traversal, blocks unreadable archives regardless of disposition, and adds gate-level staged/committed regressions. The broader helper extraction remains open.

The r14 risk review found that committed-range discovery only visited `completed/`, leaving committed `rejected/` archives without staged status or a deliverables entry outside structural validation. The current execution scans all archive state directories for committed additions/renames and adds a committed rejected-symlink regression. Rejected-state checkbox and review exemptions remain intact; file-mode and task-structure errors still block.

## Expected

Extract focused helpers for locating archive sources and assembling directory-plan evidence. Preserve each source's distinct byte authority; at the post-read index recheck, treat only exit 1 as still-untracked and fail closed on other lookup errors. Require archived Markdown task members and archive charters/files to use regular Git file modes (100644 or 100755) in both the index and HEAD. Require `tasks/` to be a real directory in the worktree, index, and HEAD, and never traverse a symlink or accept a file at that path. Return read errors separately from informational notes so each rejected archive read blocks the ceremony without diagnostic-string matching. The rejected-state exemption applies to unchecked boxes and missing execution-review evidence, not unreadable or non-regular archive bytes.

## Workaround

Keep the existing source-specific paths and verify each fail-closed regression test after changes. Do not refactor as part of the current plan execution; the five-path flow is covered and the current run can close with this maintainability work tracked.

## Source

- 2026-10-10 fresh simplicity review of archive-ceremony hardening.
