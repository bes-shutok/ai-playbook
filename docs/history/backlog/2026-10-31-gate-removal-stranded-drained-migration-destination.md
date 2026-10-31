# 2026-10-31 — gate-removal stranded by a drained migrated destination (no disposition route)

Status: open
Priority: high
Class: fence-class
Origin class: learned (2026-10-31 resume session, plan-authoring-stand-down-before-charter closeout)

**Observed:** `scripts/worktree_closeout_migrate.py gate-removal` refuses worktree/branch teardown when any migration-manifest entry's destination is missing under the target (`migrated artifact(s) missing under the target`). The migration manifest is cross-run append-only, so an entry a dead prior run recorded (a `docs/tmp/done-session/gate-reports/*.txt` report from a 2026-10-28 session) can have its destination legitimately drained later by the docs/tmp sweep's retention policy. With the source gone on both sides, no sanctioned remedy exists: the file cannot be restored faithfully, the manifest has no drain/disposition marking, and the gate fails closed — the worktree and branch stay retained indefinitely (witness: the parked `2026-10-28-plan-authoring-stand-down` worktree + branch, closeout-migration.json under `docs/tmp/execute-plan/plan-authoring-stand-down-before-charter/`).

**Expected:** a bounded route for a provably-drained destination: either (a) the docs/tmp sweep records drained done-session gate-report paths somewhere the gate consults, (b) the manifest gains a disposition marking (drained-at, with the sweep commit as witness) that the gate accepts as accounting closure, or (c) the gate's destination check gains a stale-entry arm distinguishing "missing because never transferred" from "missing because drained after a verified transfer".

**Suspected root area:** `scripts/worktree_closeout_migrate.py` gate-removal destination accounting + `scripts/docs_branch_sync.sh`/docs-tmp-sweep retention of `docs/tmp/done-session/`.

**Reproduction:** run gate-removal for the parked worktree named above; it refuses naming the missing 2026-10-28 gate-report destination whose source exists nowhere on disk.
