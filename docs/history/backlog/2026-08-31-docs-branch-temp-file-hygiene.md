# Backlog: docs-branch temp-file hygiene pass (trap registration ordering)

Status: open
Workflow: backlog
Source: docs/reviews/2026-08-31-branch-review-2026-08-30-v1-gate-trio-r6.md, round r6, finding F5 (Low, security#cleanup-trap-registered-after-resource-creation); residual of the r2 F2 fix

## Problem

In the docs-branch embedded script, the three mktemp files
(DOCS_STAGED_DELETES_FILE, RESTORED_PATHS_FILE, DOCS_TMP_SWEEP_FILE) are
cleaned up only by the `docs_branch_cleanup` trap, but the trap registers
after the `if [ ${#SHADOW_PATHS[@]} -eq 0 ]; then exit 0; fi` early exit.
Runs hitting that exit leak the three files into $TMPDIR. Contents are
repo-relative path names; mktemp modes are 0600, so this is disk hygiene,
not disclosure.

## Suggested fix

Move the `trap docs_branch_cleanup EXIT INT TERM` registration to
immediately after the mktemp calls (or create the files only after the
SHADOW_PATHS empty check).

## Why not now

The docs-branch temp-file region regenerated review findings in r2 (leak),
r5 (use-after-delete from the r2 fix's placement), and r6 (this item).
Per the fix-risk triage rule (stop surgery on regressing families), the
reorder belongs to one dedicated pass with the whole temp-file lifecycle
(creation, consumption points, trap) reviewed together.
