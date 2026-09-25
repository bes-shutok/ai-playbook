# docs-branch shadow-gate execution residuals (deferrals from the shadow-candidate plan run)

Driving force: code-quality
Status: open

Discharged-by-deferral candidates staged by the intermediate reviews and the r1 review round of `docs/plans/completed/2026-09-25-docs-branch-shadow-candidate-inclusion-and-completed-corpus-deletion.md` (executed 2026-09-26). None blocks; each is a hardening or provenance nit.

- F1 (Low, staged r1): docs-branch commit 89261aaa's subject claims "(README restored)" and the Task 6 text's premise says README is "absent on the docs branch as of authoring" — both stale: a prior sync had already delivered README, the copy arm was a no-op. Fix: none needed on the branch (append-only, never pushed); correct the provenance claim if the covering registry row or a future docs-branch plan cites it.
- F2 (Low): the Task 5 stance clause "wholesale-synced" overstates for branch-tracked `extra_shadow_dirs` roots whose extras copy loop is ignored-descendants-only, not wholesale; reachable only for drifted extra roots. Fix when extras copy semantics are next touched (the plan's Out-of-scope already reserves that surface).
- F3 (Low): `doc_registry_validator.py check-writes` override matcher is row-src-keyed, so a covering-row audit note cannot license deletions of unregistered paths (witnessed: 6 HARD on the Task 6 reconcile while the mandated `validate` gate passed). Fix: widen the matcher for covering-row-licensed deletions or document per-item row backfill as the license path.
- F4 (Low): optional hardening notes from the Task 1 inter-review — note the `grep -qF` pipeline's pipefail interaction at any future fence that sets `set -o pipefail`, and keep `docs_branch_candidate_ignored` call sites in condition context only (a bare top-level call under `set -e` would exit).
