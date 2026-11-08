# Backlog: archive rider lands after the closeout sweep, red-ing every later landing's archive-ceremony gate

- **Filed:** 2026-11-07, authoring lane blocked at its Phase 0 freeze write
- **Status:** covered (docs/history/plans/completed/2026-11-07-archive-rider-sweep-ordering.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** correctness
- **Cluster:** docs/history/backlog/2026-10-18-acrem-certification-residuals.md (same gate surface; that row owns certification-test residuals, this row owns a live archived plan missing its execution-evidence record)
- **Cluster:** docs/history/backlog/2026-11-07-plan-readiness-consumer-ordering-residuals.md (same executed plan; that row owns consumer-ordering residuals, this row owns the archive ceremony's missing record)

## Observed versus expected

Observed: since commit `fef5ebd2a` (2026-11-07 01:36 UTC, the plan-readiness-planned-path-lifecycle archive rider), every primary rolling-log commit that runs the landing sweep fails the archive-ceremony gate with rc=1: "archived plan docs/history/plans/completed/2026-11-06-plan-readiness-planned-path-lifecycle.md has no exec-review record". Two authoring sessions' Phase 0 freeze writes were blocked on this wall within minutes of each other (2026-11-07 ~02:09 UTC; one proceeded past its own residue, one stood down); the gate red is checkout-wide and blocks all primary log writes until repaired.

Expected: an archive the derivation surfaces must carry execution evidence resolvable by the gate's two acceptance routes (a `*-plan-review-<slug>-exec-r<N>` filename-series record under the reviews home, or a bound receipt whose sidecar binds the plan identity, the reviewed-bytes digest, and a yes verdict), at the moment the next sweep runs.

## Evidence

- The executed plan's exec round record exists but is code-review-kind: `.ai-playbook/reviews/2026-11-07-code-review-plan-readiness-planned-path-lifecycle-exec-r1.md` (mtime 01:33, three minutes before the archive commit). `_has_exec_review_record` requires the literal `-plan-review-` infix, so the name never matches; its sidecar carries no `plan_identity` and no `source_digest`, so `_find_bound_review_receipt` skips it too.
- The authoring-round r2 receipt binds the authored bytes digest `64b4cbd1…` with verdict yes, but the archive's reviewed bytes are the executed bytes (the plan blob at `cdfa34626`, digest `72423179…`): execution-side edits (checkbox flips, `Executed:` flip) changed the bytes after certification, so no live receipt binds them.
- The 00:47 UTC exec run's own closeout sweep passed because it ran before its archive rider landed: the rider is the last commit (`fef5ebd2a`), so no sweep evaluated the archive as in-range until the next writer's sweep. This ordering gap is why the red surfaced only after the landing completed.
- Witness: the blocked authoring freeze attempt's done_run commit refusal (rc=1, archive-ceremony finding verbatim) and the gate source at `scripts/done_sweep_gates_lib.py` `_find_bound_review_receipt` / `_has_exec_review_record`; a stale active run manifest (`20261106T113643Z-2d0f40831dbf`, complete but undispositioned, start commit `3326026d2`, an ancestor) widens shape (b)'s diff range so the archive surfaces for every later sweep, but is not the defect's cause.

- Plan-bytes digest chain (`compute_source_digest("plan", ...)`, prefixes): authored bytes bound by plan-review r2 `64b4cbd1`; authoring branch tip `e7cfeb3af` `2f2f6f8e`; landed at `cdfa34626` `72423179`; archived twin `d1e71051`. The execution round's recorded `9ecf0c6a` is a sha256 over the code diff `eb764faab..HEAD`, not a plan-bytes digest, so no recorded certificate binds any plan byte state.
- Second witness, 2026-11-07 ~10:00 UTC: `docs/history/plans/completed/2026-11-06-authoring-continuation-owner-attribution.md` (executed `6b97eb59b`, archive rider `8cdc8ef65`) hit the same red: its exec rounds are code-review-kind (r2 code digest `b38adde7`) and its plan-review r1/r2 sidecars carry no plan identity; plan digests authored-r2 `f8380ca2`, landed `083e7ea9`, archived `56f3dba7`. The first plan had meanwhile fallen out of the active manifest's diff range (start `196754e41`), so the gate went quiet on it without any repair.

## Recovery applied

Operator-directed (2026-11-07, Option A approved, then self-heal to completion): two marked-reconstruction exec-review pairs, produced by `scripts/produce_exec_review_record.py` and validator-clean in hard mode, were installed in the reviews home (untracked): `2026-11-07-plan-review-plan-readiness-planned-path-lifecycle-exec-r1` and `2026-11-07-plan-review-authoring-continuation-owner-attribution-exec-r1`. Each title says MARKED RECONSTRUCTION; each finding note names its transcribed source finding; the sidecar verdict is `no`, so neither certifies anything. Caveats: the Source digest names the archived plan bytes only as the attachment identity, never as reviewed bytes; the producer's full five-worker panel table overstates the plan-readiness original (one reviewer over four lens families); two r2 Low findings stay only in the original r2 record because the per-worker Low budget would otherwise need invented attributions. The landing sweep re-ran green after the install.

## Suggested correction

The gate is correct and stays unchanged; no gate demotion, known-red ledger, or new authoring-lane blocker. Scope arms for a plan to price (machinery admission applies; this row is the incident witness, two catches in one day; each arm lands warning-only or message-only first):

1. Post-rider re-sweep at the owning closeout: the run that lands an archive rider re-runs archive-ceremony after the rider and may not report complete while its own archive is red. This also closes the lane selectivity gap, since sweeps under a newer manifest start postdate the rider and stop seeing it.
2. The exec-review record producer checks the `-plan-review-<slug>-exec-r<N>` name grammar and the sidecar binding fields at write time, warning-only first, so a code-review-kind exec record cannot silently stand in for the plan-family record.
3. The archive-ceremony refusal message states whether the archive came from this run's range or a prior landing and points to open blocker rows (message text only).
4. Before building anything, verify whether an existing duty dispositions stale complete-but-undispositioned run manifests (for example `run-manifest-20261106T113643Z-2d0f40831dbf`), which widen shape (b)'s range.
