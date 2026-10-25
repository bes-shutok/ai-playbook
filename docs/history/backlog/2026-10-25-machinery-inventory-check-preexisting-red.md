# Backlog: machinery_inventory --check fails with 30 pre-existing rows at main

Driving force: automation (witnessed by the 2026-10-25 description-length-gate-catch-promotion execution run, Task 1 validation)

`python3 scripts/machinery_inventory.py --check` exits 1 at main c3b53b0e3 with 30 failures unrelated to any in-flight change: 4 stale witness refs to moved plan/backlog paths, 24 unregistered script/state-field regrowth rows, and 1 removals-guard row whose path still exists (`maintenance-pins-recorded-red-consult` / `scripts/check_maintenance_pins.sh`). Any plan whose Validation Commands include the bare `--check` cannot reach green until this drift is repaired or the check gains a scoped mode. Repair should re-point witness refs to surviving paths, register or explicitly exempt the unregistered scripts, and resolve the removals-guard row whose path outlived its removal.
