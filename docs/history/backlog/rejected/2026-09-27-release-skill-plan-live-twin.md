# Backlog: release-skill plan live-vs-archive basename twin

Status: rejected (2026-09-28; duplicate of docs/history/backlog/2026-09-27-plans-archive-move-only-gate.md: same witnessed live-vs-archive twin, removed by the 2026-09-27 dedup pass, pins exit 0 re-verified at disposition)
Priority: medium
Urgency remark: witnessed: `bash scripts/check_maintenance_pins.sh` exits 1 at committed HEAD (012dd94e, clean tree) with `PIN FAIL: live-vs-archive basename twin: docs/history/plans/2026-09-26-release-skill.md also archived at docs/history/plans/completed/2026-09-26-release-skill.md`, so every downstream pins gate starts red
Origin: surfaced 2026-09-27 by the r2 testing-lens review worker of docs/history/plans/2026-09-27-deferred-residual-dispositions.md (plan review r2 finding F2, testing#gate-red-at-baseline); the plan itself exempts exactly this named failure and files this item as the tracked repair path (source class: self-serving witnessed defect)

## Problem

The live plans home holds `docs/history/plans/2026-09-26-release-skill.md` while the same basename also exists under `docs/history/plans/completed/`. The basename-twin pin (scripts/check_maintenance_pins.sh, live-vs-archive check) treats that as a failed archive routing: a completed plan's live copy should have been moved, not copied, when the release execution landed (commit 012dd94e).

## Expected behavior

Exactly one of the two files remains: either the live copy is removed (its content already archived) or it is moved over the archive copy with the landing history noted. The pins suite then exits 0 at baseline again, and the exempting arm in the dispositions plan's Validation Commands (Assumptions bullet naming this twin) can be retired at that plan's next natural edit.

## Scope

Resolve the twin (remove or relocate one copy), run `bash scripts/check_maintenance_pins.sh` to exit 0, and verify no plan-review-record pointer needs updating (the staged reviews for the release-skill plan live under docs/reviews/, keyed by feature slug, not by the live copy).
