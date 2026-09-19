# Fence-robust checkbox scanning (CommonMark-grade fence map)

Status: open

## Problem

The execute-plan runtime's plan scanning helpers, `_plan_task_section_lines`
and `_unchecked_checkbox_pairs`, track only single-level triple-backtick
fences. Residual fence shapes can still truncate or shift the mid-run
readiness agreement scan:

- `~~~` fences (tilde-fenced blocks are invisible to the backtick scanner).
- Nested fences of different widths (a shorter fence inside a longer one
  scrambles open/close parity).
- Unclosed fences (parity stays open to end of file and swallows later
  sections).
- Indented fence-lookalikes (an indented ``` line toggles parity in the
  current scanner, so indented prose can open or close a fence where
  CommonMark would treat it as literal text).
- Fence-blind start-heading search (a fenced pseudo-heading whose task number
  matches a manifest task can hijack that task's section; pinned as
  documented residual behavior by the readiness witness test).
- Per-section parity restart (each section restarts the fence state closed
  instead of carrying parity across the whole plan).

## History

This family has regenerated across review rounds r2 and r3 of the
2026-09-16-execute-plan-integrity-quad plan: backtick fences were fixed in
r2, and r3 found the tilde, nested-width, unclosed-fence, and start-search
holes in the same scanner family.

## Disposition

Deferred per the two-regenerating-classes rule (ADR-0002): a partial fix per
round keeps regenerating adjacent holes, so the full CommonMark-grade fence
map is tracked here instead of being patched piecemeal.

The terminal backstop is unaffected and remains the safety net: `mark_terminal`
scans the whole archived plan fence-blind and fails closed on any unchecked
checkbox line.
