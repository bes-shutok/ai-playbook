# no-charter owned-set entry shape refuses only at key level

Driving force: correctness (preservation on a corrupted manifest)

The no-charter cleanup arm's aggregated owned-set proof (Task 1 of docs/history/plans/2026-10-28-plan-authoring-stand-down-before-charter.md) enforces key-level shape (present and list) for `owned_review_paths`/`owned_paths` but silently drops non-string entries inside the list, so a manifest with `owned_review_paths: [123, ""]` passes zero-owned. Extend the shape refusal to entry level (non-string entry refuses; empty-string skip may stay). Origin: intermediate review round 4 finding, execute-plan run 2026-10-31 (probe-verified; producer never writes this shape, corruption-only corner).
