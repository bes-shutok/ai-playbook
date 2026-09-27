# P58 execution review deferred Lows (2026-09-24)

- Status: rejected (2026-09-27; residual review polish; one entry explicitly optional)

Driving force: code-quality (residual polish from the P58 execution review panel; none blocking, all deferred per the backlog-deferral default).

- Vacuous completeness clause: Task 2's second selftest phrasing "expect ALLOW with no second write" is not asserted (a consult structurally cannot write markers); if the count assertion is ever wanted, add a marker-count check after the consult in `write_marker_cli_cwd_passthrough_keys_worktree` (scripts/skill_gate.py, selftest region only). Also carried as r3 plan-review overflow.
- Learn-class recipe keying gap: the learn Marker WRITE RECIPE inherits the write-target keying MUST by reference but shows no `[--cwd <write-target project root>]` operand and no mechanical alternative for ad-hoc-worktree sessions; P58 froze the learn text by design (non-goals). A future pass should mirror the plans-class step-5 operand.
- Step-4 dirname-fallback summary drops the absolute-target qualifier: claude.sh/cursor.sh engage the dirname(target) fallback only when the payload cwd is empty AND the target is absolute; the repo's detailed wiring note already carries the qualifier, so the recipe sentence is a lossy summary. Optional precision pass.
