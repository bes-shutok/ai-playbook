# Plan: Restore green baselines for machinery inventory and maintenance pins

Backlog origins (scope of record):
- docs/history/backlog/2026-10-30-machinery-inventory-post-repair-regrowth-two-release-scripts.md
- docs/history/backlog/2026-10-30-review-plan-attempt-state-pin-stale-at-baseline.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-31-plan-review-baseline-red-gates-regreen-r*.md
Execution budget: 1.5h total, largest task 0.5h
Authoring claim: baseline-red-gates-regreen.md (session 01a19171-0584-7930-b1ad-434c88bba61d)

## Terms

- **Keep row**: a machinery-registry entry that records an in-scope script as retained, with its path and a resolving witness.
- **Origin-kept-set witness**: a registry reference to a durable source that establishes why the script remains in the kept set.
- **Consumed-or-unknown attempt state**: a review-plan self-heal state that pauses another review until the operator gives direction.
- **Maintenance pin**: a literal check in `scripts/check_maintenance_pins.sh` that protects an intended instruction span from silent drift.
- **Baseline red**: a repo-wide validation command that fails before this plan's change is applied.
- **Regrowth check**: the machinery inventory scan that detects tracked scripts missing from the registry.

## Why

Two repository gates are red at the current base. The machinery inventory reports two tracked release scripts as unregistered, and the maintenance pin check expects a sentence that review-plan has intentionally replaced. These baseline failures hide later drift because the same gates cannot distinguish a new failure from the existing ones.

## Gist & Examples

TLDR: Restore green results for the machinery inventory and maintenance pin checks, improving code quality by removing known baseline failures.

Before (today): running `python3 scripts/machinery_inventory.py --check` reports `scripts/release-diagnostic-replay.sh` and `scripts/release-privacy-locators.py` as unregistered. Running `bash scripts/check_maintenance_pins.sh` reports `PIN FAIL: review-plan reads attempt state after resume` because the expected text no longer appears in the skill.

After (this plan): the same commands recognize both scripts as registered keep rows and find the current sentence that says a resumed review with a consumed or unknown attempt pauses before another review. Both commands finish with their existing success lines.

If either script later gains a witnessed reason for exemption, that is a separate decision; this plan records both as kept because they are ordinary tracked scripts. The pin remains enabled and follows the current rule wording. The optional release-lane checklist change and the separate doctrine-text note are outside these two repairs.

## Outcome

Both repository checks pass on the repaired base.

- The inventory records both existing release scripts as kept and continues to report future unregistered scripts.
- The maintenance pin recognizes the current consumed-or-unknown attempt pause wording and stays enabled.
- The registry witnesses remain valid after this plan is archived because they point to the completed release privacy gate plan.

Gate delta: no gate, refusal class, or validator behavior is added or removed; the existing inventory and pin checks return to green.

## Assumptions

- Register both release scripts as keep rows because the origins and current registry provide no reason to exempt either script. Basis: the two origin rows and the 2026-10-29 baseline repair precedent.
- Point the rows to the completed release privacy gate plan rather than this plan because it owns both script paths and remains in the completed archive after this plan moves. Basis: `docs/history/plans/completed/2026-10-26-release-privacy-gate-diagnostics-and-replay.md`.
- Keep the maintenance pin and update its expected literal to the current consumed-or-unknown pause clause. Basis: the pin protects an intentional review attempt-state rule, and the origin calls for a literal update rather than retirement.
- Use `docs/history/plans/completed/2026-10-26-release-privacy-gate-diagnostics-and-replay.md` as the resolving `origin-kept-set` witness for both registry rows. Basis: its Review Scope and Tasks explicitly own both release scripts, and its completed path is durable.

Decision points requiring a grill: none remain. The maintenance-selected authoring authorization resolves the source-supported choices above.

Scope extensions (grilled): none proposed. Optional items named by the prompt log are omitted under the maintenance-selected scope: the release landing checklist change and the doctrine-text registry note fold.

Sources inspected: not a tracker-linked request.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: both commands pass with their existing success outputs.
- Maintainability: registry entries follow the current row shape and point to a resolving plan; the pin matches the skill's current wording.
- Signal preservation: the inventory still reports future unregistered scripts, and the pin stays enabled.

**Done when:**
- Both targeted repository gates pass at the change tip.
- The registry contains exactly one keep row for each release script and no exemption or unrelated registry change.
- The maintenance pin remains present and its expected text occurs in `agents/skills/review-plan/SKILL.md`.

**Ship when:**
- None; these are repository-maintenance corrections with no external release dependency.

## Design Invariants

- Do not change either release script's behavior.
- Do not exempt the scripts or weaken inventory checks.
- Do not remove or broaden the maintenance pin; update only its expected literal.
- Do not add a new gate, validator, or release checklist step.

## Review Scope

**Explicit must-fix:**
- `scripts/machinery_registry.json` (Task 1): add the two resolving keep rows.
- `scripts/check_maintenance_pins.sh` (Task 2): replace the stale expected string for the named pin with the current skill clause.

**Production code:**
- No production behavior change is required.

**Validation:** See the commands in `Validation Commands` below.

**Out of scope; reject unless plan-related:**
- `scripts/release-diagnostic-replay.sh` and `scripts/release-privacy-locators.py` behavior; reason: the selected defect is missing registry coverage, while their implementation issues have separate origins.
- `agents/skills/release/SKILL.md`; reason: the optional checklist addition is not required to clear the current inventory failures.
- Other maintenance pins or registry rows; reason: they are outside the two witnessed baseline failures.
- Doctrine-text registry-note cleanup; reason: it has a separate origin and is not required for either gate to pass.

## Validation Commands

Run from the repository root:

```bash
python3 scripts/machinery_inventory.py --check
bash scripts/check_maintenance_pins.sh
```

### Task 1: Register the two existing release scripts

Context surface: this plan's Terms, Outcome, and registry invariant.

Files:
- `scripts/machinery_registry.json`

Primary class anchors:
- `main` in `scripts/machinery_inventory.py`
- `save_registry` in `scripts/machinery_inventory.py`

Evidence:
- The current inventory check reports both release scripts as unregistered.
- The registry already uses `keep` rows with `kind: script` for maintained scripts.
- Neither origin records an exemption rationale.

- [x] Add one `keep` row for each script, with a unique script ID, the exact script path, an empty tests list, and an `origin-kept-set` witness pointing to the durable completed release privacy gate plan; preserve the semantic content and ordering of unrelated rows, and do not normalize their pre-existing key ordering. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the inventory command listed in Validation Commands and confirm its existing success line with zero failures. [class: REPOSITORY_TEST]
- [x] Commit: `fix: register release scripts in machinery inventory` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Refresh the resume-state maintenance pin

Context surface: the maintenance pin and the resume-state rule in `agents/skills/review-plan/SKILL.md`.

Files:
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `pin` in `scripts/check_maintenance_pins.sh`

Evidence:
- The named pin currently searches for the retired sentence `A resumed post-fence workflow reads the latest value`.
- The current rule says the run reads the latest value and, when it is consumed or unknown, pauses before another review while reusing existing evidence.

- [x] Replace only this pin's expected literal with the current clause `the run reads the latest value and, when it is consumed or unknown, pauses before another review`; keep the pin name, target file, and check enabled. [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh` and confirm its existing `OUTCOME: pass` line. [class: REPOSITORY_TEST]
- [x] Run both commands in Validation Commands from the same final tree and confirm both return success with their existing success lines. [class: REPOSITORY_TEST]
- [x] Commit: `fix: refresh review resume state pin` [class: IMPLEMENTATION_REQUIRED]

## Documentation Impact Assessment

No additional documentation change is needed. The registry rows and the refreshed pin are the durable records for the two selected failures; release behavior and release checklist instructions remain unchanged.

## Disposition of migrated backlog items

- Origin rows docs/history/backlog/2026-10-30-machinery-inventory-post-repair-regrowth-two-release-scripts.md and docs/history/backlog/2026-10-30-review-plan-attempt-state-pin-stale-at-baseline.md: covered by this plan (Status: covered flips landed at base; rows deleted in this landing change), durable home = this completed plan twin.
- Phase 3 r1 blocking finding (fixture-layer twin of the retired resume-state sentence in scripts/test_plan_readiness.py) fixed in commit 200362407 as a causal-scope extension of Task 2 and certified clean by the focused r2 fresh-adversarial round.
- Registry canonical-serializer round-trip divergence: pre-existing, byte-identical between main and tip, owned by docs/history/plans/2026-10-31-machinery-registry-canonical-serializer-round-trip.md (out of scope here).
