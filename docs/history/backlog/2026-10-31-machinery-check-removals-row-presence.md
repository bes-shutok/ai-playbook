# machinery_inventory --check does not gate removals-row presence

- **Cluster:** machinery-registry-hygiene
- **Status:** open
- **Priority:** medium
- **Driving force:** reliability

## Problem

`python3 scripts/machinery_inventory.py --check` validates entries-row shape, witnesses, and registered-script presence, but it does not gate `removals` rows: deleting a row from the `removals` list exits 0, with the only signal being the printed removals count changing. A removals row is a durable disposition record; its silent loss weakens the registry's audit trail.

Witnessed 2026-10-31 by the testing lens of the machinery-registry-canonical-serializer-round-trip execution review (r1, disposable-clone mutation: dropping a `removals` row exits 0; dropping an `entries` row exits 1 as expected).

## Expected

`--check` fails (exit 1, named failure line) when a `removals` row present in the committed-HEAD registry is missing from the working-tree registry, mirroring the existing regrowth-red gate's shape; the check stays green when removals rows are unchanged or added.

## Suggested direction

Extend the existing HEAD-comparison leg in `scripts/machinery_inventory.py` that already re-derives committed contents for the regrowth gate to also diff the `removals` row ids, emitting a named failure per missing id. Keep it warning-free per the machinery admission protocol: this names the witnessed bite above.
