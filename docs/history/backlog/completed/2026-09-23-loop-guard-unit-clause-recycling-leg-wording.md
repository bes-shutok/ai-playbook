# Loop-guard unit clause: qualify the re-arm shape deferral for the (inoperative) recycling leg

- Priority: low
- Status: open
- Origin: Phase 3 code review r1 finding F2 (correctness#unit-clause-shape-identity-overbroad), execution of docs/plans/completed/2026-09-21-loop-guard-one-recorded-mutation-carve-out.md, 2026-09-23
- Driving force: the carve-out's unit clause says "a parent re-arm's shape is the recipe's delete-plus-create", which overstates the recipe's conditional shape: a live recycling-update leg exists for update-primitive sessions (currently inoperative on this host, flip REFUTED 2026-09-19). The governing "per the recipe's operative shape" deferral plus the refuted flip make the sentence safe today, but a future verified flip would make the flat identity claim wrong.
- Fix sketch: reword the unit-clause parenthetical to "a parent re-arm's shape is per the recipe's operative shape (delete-plus-create today; the recycling leg only if a verified flip reopens it)" in zcode.md and update the two identical pins + the plan freeze literal in the same edit.
- Constraint: the sentence is pinned by `scripts/check_maintenance_pins.sh` count gates and quoted in the plan's Validation Commands; all three surfaces change in one commit.
