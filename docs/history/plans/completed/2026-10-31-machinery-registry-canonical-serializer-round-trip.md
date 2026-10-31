# Plan: Restore byte round-trip for machinery_registry.json under its canonical serializer

Backlog origins (scope of record):
- docs/history/backlog/2026-10-30-machinery-registry-canonical-serializer-non-round-trip.md
Driving force: reliability
Plan review record: the staging series .ai-playbook/reviews/2026-10-31-plan-review-machinery-registry-canonical-serializer-round-trip-r*.md
Execution budget: 1h total, largest task 0.5h
Authoring claim: machinery-registry-canonical-serializer-round-trip.md (session sess_28903bc6-3d71-49c1-a3d6-2d90117c66b2)

## Terms

- **Canonical form**: the exact byte shape `save_registry()` writes: `json.dumps(registry, indent=2, sort_keys=True)` plus a trailing newline.
- **Round-trip**: a canonical dump of the parsed file equals the file bytes byte-for-byte.
- **Drifted row**: a registry object whose keys sit in insertion order rather than sorted order, so canonicalizing the current bytes rewrites that row.
- **Normalize-only change**: a change whose diff reorders object keys only; no row, field, value, or file outside the registry's byte shape is touched.
- **Regrowth red**: the two witnessed `--check` failures naming `scripts/release-diagnostic-replay.sh` and `scripts/release-privacy-locators.py` as unregistered, owned by the open plan `docs/history/plans/2026-10-31-baseline-red-gates-regreen.md`.

## Why

The registry's single writer defines the canonical form (`save_registry()` at `scripts/machinery_inventory.py:155`, `json.dumps(..., indent=2, sort_keys=True)` plus a trailing newline), but the on-disk file does not round-trip under it: canonicalizing the current bytes reorders keys in at least three `removals` rows (`guard:maintenance-pins-recorded-red-consult`, `script:check-prompt-log-origins-receipt-without-removal-warning`, `release-recovery-push-rails`). Any code path that re-serializes through the writer smears those rows' bytes into an unrelated diff, every future registry editor inherits the textual-insertion workaround with its schema-drift risk, and the drift is invisible to `machinery_inventory.py --check`, which validates row shape and witnesses but not key order. Witnessed while registering `protocol:agent-type-affinity-check` at the agent-type-affinity Task 2 boundary, where the registration had to fall back to textual insertion to avoid the smear.

## Gist & Examples

TLDR: Normalize `scripts/machinery_registry.json` to its canonical serializer form by re-writing it through its own writer, so the file round-trips byte-identically and future registry edits can re-serialize safely, restoring reliability of the registry's diff hygiene.

Before (today): `json.dumps(json.loads(raw), indent=2, sort_keys=True) + "\n"` differs from the file bytes; a canonical dump reorders keys inside the drifted `removals` rows, and registering a new row must avoid the writer to keep the diff scoped.

After (this plan): the same canonical dump equals the file bytes exactly, `git diff` for the normalize commit shows only key reordering inside the previously drifted rows, and `machinery_inventory.py --check` reports no new failure beyond the witnessed regrowth reds.

Edge cases: if the open baseline-red-gates-regreen plan lands first, `--check` is fully green and the acceptance reads "no failure at all"; the round-trip equality is asserted over the whole file, not just the three named rows; a registry edit landing mid-run invalidates the normalize, so the write re-derives from disk immediately before writing. The whole-file equality check catches an interleaved edit that introduces key-order drift (the textual-insertion practice); a writer-mediated interleaved edit stays canonical and round-trips; its semantic delta is carried by that session's own commit, so the re-derive guards the byte shape, not the content.

## Outcome

`scripts/machinery_registry.json` byte-identically round-trips under its own writer's canonical form, and registry sessions can re-serialize through `save_registry()` without smearing unrelated bytes into their diffs.

- The normalize commit's `scripts/machinery_registry.json` diff contains only key reordering on the drifted rows; the commit may also carry this plan's own checkbox-tick edits per the boundary-commit convention.
- The writer (`save_registry`) is unchanged; no gate, validator, or standing check is added or removed (the one-time round-trip proof is this plan's acceptance evidence, and the rejected `--check` round-trip leg stays rejected).
- The known regrowth reds are untouched; their repair belongs to the open baseline-red-gates-regreen plan.

Gate delta: no gate, refusal class, or validator behavior is added or removed; the registry's content is unchanged and only its byte order is normalized.

## Assumptions

- The normalize re-writes the file through the registry's own writer (`load_registry(repo)` then `save_registry(repo, registry)`) rather than an equivalent inline dump, because using the single writer guarantees canonical-form fidelity by construction. Basis: `save_registry` at `scripts/machinery_inventory.py:155` is the writer whose form defines canonical.
- `sort_keys=True` reorders keys at every object level, so rows already in sorted order produce no byte change; the diff lands as key reordering inside the drifted rows only. Basis: the drifted rows are the minority of the file (the origin row names three `removals` rows) and the acceptance is whole-file byte equality.
- No semantic content change is intended or permitted: same rows, same values, same top-level key set. Basis: the origin row's Expected section (diffs carry only intended changes after the fix).
- The normalize is a dedicated change, not a rider on a semantic registry edit, so the diff stays reviewable as pure reordering. Basis: the origin row's Suggested direction and the plan-route-only status of the registry file.

Decision points requiring a grill: none remain. The maintenance-selected authoring authorization resolves the source-supported choices above.

Scope extensions (grilled): none proposed. The origin row's clause "any registry-touching session can carry it as a rider within that plan's own scope rules" is realized by this dedicated plan rather than a rider; the rejected `--check` round-trip leg and the two release-script registrations are omitted under the maintenance-selected scope.

Sources inspected: not a tracker-linked request.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the canonical dump equals the file bytes after the change.
- Diff hygiene: the normalize commit's diff shows only key reordering.
- Signal preservation: `--check` behavior is unchanged; no new gate appears.

**Done when:**
- `python3 -c` round-trip assertion over `scripts/machinery_registry.json` passes at the change tip.
- The normalize commit's `scripts/machinery_registry.json` diff shows only key-order changes inside the drifted rows (the commit may also carry this plan's own checkbox-tick hunks per the boundary-commit convention).
- `python3 scripts/machinery_inventory.py --check` reports no new failure beyond the witnessed regrowth reds (or nothing at all when those are already repaired).

**Ship when:**
- None; this is a repository-maintenance correction with no external release dependency.

## Design Invariants

- No semantic content change: identical rows, values, and top-level keys before and after.
- The writer `save_registry()` and the check `machinery_inventory.py --check` are not modified.
- No new gate, validator, test file, or standing check is added; the round-trip proof is a one-time acceptance command recorded in the validation log.
- Only `scripts/machinery_registry.json` changes.

## Review Scope

**Explicit must-fix:**
- `scripts/machinery_registry.json` (Task 1): normalize to the canonical form through the registry's own writer.

**Production code:**
- No production behavior change is required.

**Validation:** See the commands in `Validation Commands` below.

**Out of scope; reject unless plan-related:**
- `save_registry()` or `load_registry()` behavior; reason: the writer is correct, the file drifted from it.
- A round-trip leg in `machinery_inventory.py --check`; reason: rejected under the machinery admission protocol (no second witnessed bite; this bullet's inline reason is the durable rejection record; the origin row's source reference pointed into swept `docs/tmp/` scratch).
- The two unregistered release scripts; reason: owned by the open plan `docs/history/plans/2026-10-31-baseline-red-gates-regreen.md`.
- The doctrine-text registry note citation; reason: separate origin (`docs/history/backlog/2026-10-30-doctrine-text-precision-residuals.md`), not required for round-trip.

## Validation Commands

Run from the repository root:

```bash
python3 -c "import json; raw=open('scripts/machinery_registry.json','rb').read(); canon=(json.dumps(json.loads(raw), indent=2, sort_keys=True)+chr(10)).encode(); assert raw==canon, 'registry does not round-trip under the canonical serializer form'; print('round-trip: ok')"
python3 scripts/machinery_inventory.py --check
```

### Task 1: Normalize the registry to its canonical form

Context surface: this plan's Terms, Design Invariants, and the origin row's Problem section.

Files:
- `scripts/machinery_registry.json`

Primary class anchors:
- `save_registry` in `scripts/machinery_inventory.py`
- `load_registry` in `scripts/machinery_inventory.py`

Evidence:
- The canonical dump of the current bytes differs from the file bytes (witnessed 2026-10-31, and re-derivable with the Validation Commands one-liner).
- The drifted rows are `removals` entries whose keys sit in insertion order; the first drifted row landed textually in f3894756d (2026-10-18).
- `save_registry()` at `scripts/machinery_inventory.py:155` writes `json.dumps(registry, indent=2, sort_keys=True)` plus a trailing newline.

- [x] Re-derive the registry from disk and re-write it through the registry's own writer (`load_registry(repo)` then `save_registry(repo, registry)` via `python3 -c`), so the file lands in the canonical form; confirm `git diff --stat` names only `scripts/machinery_registry.json`. [class: IMPLEMENTATION_REQUIRED]
- [x] Inspect `git diff scripts/machinery_registry.json` and confirm every hunk is key reordering inside the previously drifted rows: no row added or removed, no value changed, no trailing-whitespace or newline difference beyond the writer's canonical trailing newline. [class: REPOSITORY_TEST]
- [x] Commit: `fix: normalize machinery registry key order to canonical form` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Acceptance battery at the change tip

Context surface: this plan's Outcome, Done when, and Validation Commands.

Files:
- none (verification-only task)

Primary class anchors:
- `main` in `scripts/machinery_inventory.py`

Evidence:
- The origin row's three acceptance conditions: diff touches only key ordering, `--check` reports no new failure beyond the known regrowth reds, canonical dump equals file bytes.

- [x] Run the Validation Commands round-trip one-liner and confirm it prints `round-trip: ok`. [class: REPOSITORY_TEST]
- [x] Run `python3 scripts/machinery_inventory.py --check` and confirm every failure line names one of the two witnessed regrowth reds (`scripts/release-diagnostic-replay.sh`, `scripts/release-privacy-locators.py`): zero, one, or both of them; any failure line naming anything else fails the task. [class: REPOSITORY_TEST]
- [x] Re-run the round-trip one-liner a second time after the `--check` run to confirm the check's read path left the bytes unchanged. [class: REPOSITORY_TEST]

## Documentation Impact Assessment

No additional documentation change is needed. The normalize commit itself is the durable record of the byte-shape repair; the origin row carries the witness narrative, and this plan's rejection record for the `--check` round-trip leg preserves the admission-protocol reasoning.

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-30-machinery-registry-canonical-serializer-non-round-trip.md` — covered by this plan (normalize commit 0ef9d70aa: pure key reordering inside the three named drifted rows; round-trip one-liner passes at the change tip; `--check` fully green at landing because the regrowth reds were repaired by the baseline-red-gates-regreen landing 404aef056, the plan's anticipated "nothing at all" edge case). The row was deleted from the living backlog directory in the same change; this archived plan is its durable home.
- Review r1 testing-lens finding F-1 (`--check` does not gate removals-row presence) was captured as the new backlog row `docs/history/backlog/2026-10-31-machinery-check-removals-row-presence.md` (commit acd5f244), not folded into this plan's scope.
