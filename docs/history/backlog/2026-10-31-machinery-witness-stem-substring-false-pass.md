# Machinery witness stem containment is bare substring; superstring identifiers false-pass

Driving force: code-quality

Cluster: docs/history/plans/completed/2026-10-30-machinery-witness-ref-validation.md

`scripts/machinery_inventory.py` stem containment is bare substring (`stem not in content`, lines ~282-284), so a witness test naming only `unregistered_tool` satisfies a `registered_tool` row — the fixture itself contains this collision pair. The plan's recorded false-positive cost covers only the opposite (false-block, indirect helper) direction; the false-pass direction via superstring identifiers is unrecorded. Fix shape: word-boundary or token-aware stem matching, plus a collision-pair regression test. Review at the next machinery-inventory maintenance pass (the plan's declared review date). Residual from the 2026-10-31 execution of docs/history/plans/2026-10-30-machinery-witness-ref-validation.md (Phase 3 r1, testing lens; landing commit records the disposition).
