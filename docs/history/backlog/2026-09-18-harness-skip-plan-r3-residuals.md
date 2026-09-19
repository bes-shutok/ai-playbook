# Backlog: harness-skip plan r3 non-blocking residuals (4 findings, deferred at exit)

Status: open
Priority: high
Workflow: backlog
Origin: review-plan r3 of docs/plans/2026-09-18-harness-detection-and-budgeting-skip.md
(ready=yes zero blocking at digest 46f7e1d4; the four findings below are non-blocking
and were deferred at the clean exit per the ADR-0002 backlog-deferral default instead
of paying one more full review round; fix them in the plan before or during execution)

## Findings and fix sketches

1. (Medium) The Task 2 enum-line item says "replace the recorded quota_status
   enumeration line with exactly ..." but the real schema line in
   agents/skills/maintenance/SKILL.md is shared with other schema fields (the
   reviewer measured that a destructive whole-line replacement passes both G7
   gates while deleting the `outcome` field and invalidating the JSON example).
   Fix: reword to an in-place fragment extension (extend the enumeration VALUE
   `ok|unknown` to `ok|unknown|skipped-unsupported-harness`, do not replace the
   whole line), and consider re-pinning G7b to the value fragment rather than the
   whole line.
2. (Low) Done-when says "per-file pins G5 through G7b pass", dropping G8 (the
   fold moved the range end); the Task 2 GREEN step still says G5 through G8.
   Fix: make both ranges name G5, G6, G7, G7b, and G8 explicitly.
3. (Low) The G3 block's comment and fail message attribute today's rc 1 to the
   file-presence answer; the measured cause today is the missing helper module
   (ModuleNotFoundError). Fix: reword to "the gate fails today because the helper
   module does not exist yet; post-fix the seam patch is the input".
4. (Low) The CLI none test inherits the ambient ancestry walk, so on a codex-hosted
   executor it would answer codex and fail in the safe direction (false RED).
   Fix: give `main()` an injectable detector argument defaulting to
   `detect_harness`, and have the CLI test pass a stub answering none.
