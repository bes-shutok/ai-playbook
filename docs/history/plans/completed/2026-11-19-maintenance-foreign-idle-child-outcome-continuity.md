# Plan: Maintenance Foreign Idle-Child Outcome Continuity

Backlog origin: docs/history/backlog/2026-11-19-maintenance-foreign-idle-child-check-blocks-codex.md
Driving force: automation
Plan review record: .ai-playbook/reviews/2026-11-19-plan-review-maintenance-foreign-idle-child-outcome-continuity-p1a4f74df-r*.md
Execution budget: 1.5h total, largest task 1.0h
Executed: yes (2e6a685d5e312ec0e08b32ae463f08a520423db7 - pre-squash branch tip)
Authoring claim: 2026-11-19-maintenance-foreign-idle-child-check-blocks-codex.md (session 01a1f45a-3820-70b3-8c2c-91b7b6b3d313)

## Terms

- **Idle child:** a maintenance child with `fire_at: null`, created for idle dispatch and recorded as pending or in progress.
- **Listing unavailable:** the active runtime has no supported way to query the child runtime's idle-task queue; this is missing evidence, not evidence that the child vanished.
- **Independent lane:** a candidate whose target and shared-resource use do not conflict with the unresolved child under the existing occupancy and exclusivity rules.

## Why

Maintenance stopped before selecting an open execution plan because it could not query a known foreign runtime's idle-task listing. The six-hour threshold is only a lane-hold horizon for a child still shown live, so missing listing evidence must not be converted into a failed child or prevent independent work.

## Gist & Examples

TLDR: Keep an unresolved foreign idle child pending while maintenance selects safe independent work, for automation continuity.

Before (today): a Codex maintenance turn reaches an old idle child recorded for a different runtime, cannot query that runtime's task listing, and stops before selecting an otherwise eligible plan. The child status stays unresolved, but the stop gives unrelated work no chance to proceed.

After (this plan): when the child has a recognized foreign runtime and only that runtime's listing is unavailable, maintenance preserves its pending outcome and failure count, then continues through the ordinary lane decision. A same-target conflict or shared exclusivity still holds. If the active runtime's own listing is unavailable, the existing blocker-recovery path runs and the child remains unresolved.

Edge case: a child still listed as live at six hours is not marked failed and accrues no failure credit; the existing six-hour G1 horizon still releases the lane when status is available, while a same-target hold continues past six hours as long as the foreign listing remains unavailable. A distinct-target candidate may proceed under G1/G2. A child shown vanished without progress follows the existing failure rule.

## Outcome

An unavailable foreign idle-task listing no longer blocks safe independent maintenance work or changes the child's outcome.

- While a foreign runtime listing is unavailable, its child remains pending with no failure credit; once listing evidence is available, the existing live or vanished rules decide the outcome.
- Same-target and shared-exclusivity conflicts continue to block candidate work across runtimes; same-target work stays held beyond six hours while the foreign listing is unavailable, while a distinct-target candidate remains eligible under G1/G2.
- Same-runtime uncertainty continues through the existing blocker-recovery path, and verified vanished children keep the existing failure-cap behavior.

Gate delta: removes the pre-decision stand-down for a recognized foreign-runtime listing gap only when candidate work passes existing G1 lane guards; preserves a same-target hold beyond six hours until foreign status resolves; G2 verified-failure handling and all other refusal classes remain unchanged. No gate, validator, lock, ledger, protocol layer, checked set, schema field, or dispatch pause is added.

Follow-up disposition: any implementation finding outside the stated foreign-listing gap is recorded with its evidence in a durable backlog row and routed through the existing investigation flow; no additional follow-up is expected from the planned policy change.

## Assumptions

- The child record's canonical `runtime_id` is sufficient to distinguish a recognized foreign runtime from the active runtime; an absent, invalid, or unknown identity retains shared handling. Basis: the maintenance runtime identity registry and the shared-unknown rule in `agents/skills/maintenance/guards.md`.
- Existing G1 same-target/global exclusivity and G2 verified-failure protections remain authoritative; the same-target hold persists beyond six hours only while this foreign listing remains unavailable. Basis: `agents/skills/maintenance/decisions.md` and `agents/skills/maintenance/guards.md`.
- The broader maintenance-loop continuity work remains separate from this single child-status blocker. Basis: the foreign-idle-child backlog row and the separate frozen maintenance-loop intake entry in `docs/history/backlog/PLAN-PROMPTS.md`.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: missing foreign-runtime evidence leaves the child pending and does not increment failures.
- Safety: same-target conflicts, shared exclusivity, live same-runtime occupancy, and verified failure limits retain their current outcomes.
- Maintainability: the unavailable-listing rule lives beside the existing idle-child outcome contract and is pinned by the existing maintenance runtime-scope contract suite.

**Done when:**
- The four listed/unavailable and foreign/same-runtime cases have explicit policy witnesses and passing focused contract checks; same-target work remains held after six hours while status is unavailable, and distinct-target admission follows G1/G2.
- No new provider, gate, validator, lock, or state field is introduced.
- The change passes the focused runtime-scope test module, public-hygiene scan, and em-dash check.

**Ship when:**
- No external release or deployment condition; the policy is consumed from the repository skill sources on the next maintenance turn.

## Review Scope

**Explicit must-fix:** policy behavior, cross-runtime evidence semantics, and regression coverage on these paths are in scope.

**Production code:**
- None; behavior is specified by the maintenance skill contract.

**Tests:**
- `scripts/test_maintenance_runtime_scope.py` (Task 1)

**Configuration:**
- None.

**Documentation:**
- `agents/skills/maintenance/failure-cap.md` (Task 1)
- `agents/skills/maintenance/guards.md` (Task 1)

**Out of scope:**
- Runtime status-provider additions; quota wake behavior; changes to idle-child dispatch; G1 occupancy changes outside the same-target hold exception while foreign status is unavailable; G2 verified-failure changes; the separate maintenance-loop continuity origins.

## Validation Commands

The broader `check_maintenance_pins.sh` script currently has an unrelated baseline failure in its `FINAL STEP prefix count` assertion: the pin expects three occurrences, while the current canonical authoring, execution, and unblock templates contain two. This plan does not edit that pin or those templates; its focused runtime-scope test covers the changed contract.

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_maintenance_runtime_scope.py -q
bash scripts/scan-public-hygiene.sh --files agents/skills/maintenance/failure-cap.md agents/skills/maintenance/guards.md scripts/test_maintenance_runtime_scope.py
bash scripts/check-no-em-dash.sh file agents/skills/maintenance/failure-cap.md agents/skills/maintenance/guards.md scripts/test_maintenance_runtime_scope.py
```

## Tasks

### Task 1: Pin and implement unavailable foreign child listing semantics

Files:
- `agents/skills/maintenance/failure-cap.md`
- `agents/skills/maintenance/guards.md`
- `scripts/test_maintenance_runtime_scope.py`

Context: Preserve the existing idle-child status distinction and six-hour live-child horizon. Keep missing evidence separate from a vanished task. While a recognized foreign listing remains unavailable, preserve the same-target G1 hold beyond six hours but allow distinct-target work that passes existing G1/G2. No other G1/G2 behavior changes and no machinery is added. Land the regression assertions before the policy edit in the same task so the expected behavior is demonstrated RED before it is implemented.

Acceptance criteria:
- [x] Add the behavior assertions in `scripts/test_maintenance_runtime_scope.py` → expect RED against the current contract for a recognized foreign runtime whose idle listing is unavailable, without weakening the existing same-target and global-occupancy assertions. [class: REPOSITORY_TEST]
- [x] Update the existing idle-time child rule in `agents/skills/maintenance/failure-cap.md`: leave a known foreign child pending with no failure credit when its runtime listing is unavailable; preserve same-runtime blocker recovery, the live-task horizon when status is available, and listed-vanished failure semantics. [class: IMPLEMENTATION_REQUIRED]
- [x] Update the G1 state-file rule in `agents/skills/maintenance/guards.md`: keep same-target work held beyond six hours until the unavailable foreign listing resolves; allow only distinct-target work that passes existing G1/G2. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the focused runtime-scope test command from Validation Commands → expect GREEN for foreign listing unavailable, same-runtime listing unavailable, listed-live at the horizon, listed-vanished without progress, and same-target/shared-exclusivity cases. [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: preserve independent work across foreign status gaps` [class: IMPLEMENTATION_REQUIRED]

## Documentation Impact Assessment

The unavailable foreign listing outcome is owned by `agents/skills/maintenance/failure-cap.md`, and the continued same-target G1 hold is owned by `agents/skills/maintenance/guards.md`; the existing runtime-scope tests pin both policy files. No new document or index entry is required.

## Notes

- Introduction history: `058bbb7e0` landed the child-outcome check and the current six-hour live-versus-vanished distinction; `def5dce98` later widened the check to `in_progress` children. The implementation here preserves those protections and adds only an unavailable-foreign-evidence disposition.
- Runtime scope is read from the canonical inventory `projects/.ai-playbook/execute-plan-runtime-inventory.toml`; this plan adds no capability or runtime identifier.

## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-19-maintenance-foreign-idle-child-check-blocks-codex.md`: completed by this plan. The policy keeps a recognized foreign idle child pending when its listing is unavailable, holds same-target work past six hours until the listing resolves, and admits distinct-target work only under existing G1/G2; focused contract tests and Phase 3 review passed. The former origin is deleted in this completion pass.
