# Plan: maintenance dry-exit conversion fall-through

Backlog origin: docs/history/backlog/2026-11-19-authoring-dry-exit-conversion-fall-through.md
Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/2026-11-19-plan-review-maintenance-dry-exit-conversion-fall-through-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1.5h total, largest task 1.5h
Executed: yes (aac1b86fe139f06ce89cb5dca9f1048b2672dac3)
Authoring claim: 2026-11-19-authoring-dry-exit-conversion-fall-through.md (session 01a1f00b-aa83-7302-beb4-04360f9747d5)

## Terms

- Dry authoring exit: an author-mode maintenance run whose prompt and selected authoring inputs yield no dispatchable plan or plan prompt.
- Unconverted backlog row: an eligible open backlog item that has no origin match in either rolling prompt log or a plans-root plan, and no recorded skip disposition.
- Investigate unit: one invocation of the investigate skill over the next eligible uncovered group, complete only when every routed prompt-log entry validates and commits, or the group receives an investigate-defined recorded skip disposition.
- Loop-liveness line: the D-18 closing line naming the exit or standing-carrier exemption and the carrier identity and fire time.
- Reset-anchored successor: the existing one-shot continuation scheduled from the quota probe's reset instant plus its standing arming margin.

## Why

The existing continuity contract handles true queue exhaustion, blocked exits, and the 5h quota wall. A witnessed dry authoring run treated an empty prompt segment as loop emptiness while eligible backlog rows still needed investigation. The per-cycle harvest only considers findings witnessed in that cycle, so a separate unobserved row can remain dark even though the loop has a bounded investigate procedure.

## Gist & Examples

TLDR: make a dry authoring exit investigate one remaining eligible backlog group through investigate’s corpus survey, so maintenance continues automatically.

Before: a run finds no usable plan prompt and records or reports a dry end while backlog rows remain outside both prompt logs and open plans.

After: the dry exit reads the conversion predicate across eligible uncovered backlog groups, runs one complete investigate group when work remains and quota permits, and records the D-18 liveness disposition; the existing 5h wall still arms its reset-anchored successor.

## Outcome

Maintenance continues converting eligible backlog work until no eligible queue remains or the existing 5h wall schedules the next window.

- An unrepresented eligible backlog row prevents a false queue-empty exit.
- A dry authoring exit processes no more than one investigation unit through the existing prompt-log writer and its guards.
- True queue exhaustion, blocked stops, operator stops, and quota-wall recovery retain their existing D-17/D-18 behavior.

Gate delta: no gate, validator, lock, refusal class, fence, protocol layer, or state field is added or removed; the dry exit adds a distinct full-corpus selection form for the existing investigate capability, while the normal per-cycle harvest remains limited to findings witnessed in its cycle. Existing prompt-log write, quota, and successor guards remain in force.

Follow-up disposition: a finding that reveals a separate stop-path defect is captured through the existing backlog and investigate flows; it does not widen this plan's implementation task. No candidate rejection is anticipated.

## Assumptions

- assume the existing reset-anchored successor already meets the requested 5h behavior; basis: current D-18 and the completed 2026-11-10 and 2026-11-13 continuity plans.
- assume the existing investigate skill is the smallest supported conversion route; basis: its Stage 0 corpus survey, Stage 1 grouping and skip rules, and existing prompt-log write boundary.
- assume the 2026-11-16 continuity plan's author-to-execution fall-through does not cover backlog rows that still need investigation; basis: its switched-lane reach is the D1 plans-only selection and current D-18's loop-scoped pin reads through that reach.
- assume the intended implementation is the focused dry-exit gap named by the user's current maintenance request and the open backlog origin; no broader maintenance-stop audit is included.
Decision points requiring a grill: none remain.

## Standing constraints

- Follow the repository skill-text anti-growth and machinery admission rules; keep incident narrative in the backlog row and cite it in operative text at most once.
- Preserve D-17 and D-18's existing stop classes and the existing reset-anchored successor shape.
- Do not bypass or edit the prompt-log writer gates; one investigation unit uses the investigate skill's own contract.

## Evaluation Criteria

- Correctness: the empty predicate distinguishes true queue exhaustion from eligible backlog work not yet represented in the prompt logs or plans.
- Continuity: a dry authoring exit selects the next eligible uncovered backlog group across the full corpus and completes at most one investigate group invocation when quota allows; every routed entry validates and commits before the unit completes, and the exit records its liveness disposition.
- Safety: the existing project-class, survey-only, user-stop, quota-wall, blocked-retry, and prompt-log write guards remain authoritative.

**Done when:**
- `python3 scripts/skill_text_budget.py --check` exits 0 with no ceiling breach.
- `bash scripts/scan-public-hygiene.sh` exits 0.
- `git diff --check` exits 0.
- All changed source surfaces describe one consistent dry-exit predicate, one-group investigation, D-18 record, and existing 5h successor.

**Ship when:** a real dry authoring run with no ready prompt and an unrepresented eligible row produces the complete routed entry set for one group and reports its liveness disposition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Documentation:**
- `agents/skills/maintenance/SKILL.md` (Task 1)
- `agents/skills/maintenance/decisions.md` (Task 1)
- `agents/skills/maintenance/template-authoring.md` (Task 1)
- `agents/skills/investigate/SKILL.md` (Task 1)
- `docs/maintenance/operator-directives.md` (Task 1)

**Plan-related extension:** review may include a directly implicated workflow reference if the final path set requires it to keep the new dry-exit behavior coherent; any such addition must be causally tied to the converter and D-18 behavior.

**Out of scope; reject unless plan-related:**
- The 5h quota probe, reset scheduling primitives, and carrier creation machinery; reason: the existing D-18 reset successor already covers the witnessed 5h pause.
- Other maintenance stop classes and unrelated backlog selection rules; reason: no evidence in this origin row requires redesigning them.
- Validator, lock, ledger, or schema additions; reason: the existing harvest and prompt-log writer already provide the required bounded mechanism and guards.

## Design Invariants

- The completed 2026-11-10 continuity plan establishes the no-dark-exit and reset-successor contract; preserve its queue-empty, blocked-retry, operator-stop, and quota-wall distinctions.
- The completed 2026-11-16 continuity plan composes the author-mode starvation switch into the author lane's terminal exit and defines D-18 queue-empty through switched-lane reach; extend that input universe to conversion work without weakening its D1 selection or survey-only precedence. Investigate Stage 0 defines the eligible backlog corpus and Stage 1 defines grouping and skip behavior; the dry-exit form uses those rules and selects beyond findings witnessed in the current cycle.
- The completed 2026-11-13 interactive-lane plan makes the 5h kill path recover through the reset-anchored successor; leave its trigger and timing unchanged.
- Update investigate Purpose to allow every validated and committed rolling-log entry routed for one group, while keeping the skill bounded to one group invocation and ending without dispatch or execution. A mixed-verdict group may route entries to both logs, and the unit is incomplete until every routed entry has validated and committed or the group has a recorded investigate-defined skip disposition.

## Validation preamble

- `bash scripts/check-no-em-dash.sh added-lines --base 21bb4c4074eaf237d8d8abfde7ca2e2773332122`: pass.
- `bash scripts/scan-public-hygiene.sh`: pass.
- `bash scripts/check_maintenance_pins.sh`: fail in the current worktree on the unrelated `Step 1.2 pre-prompt task-scope digest record (region-scoped)` pin. Source inspection at the recorded branch base confirms the required phrase is absent in `agents/skills/execute-plan/SKILL.md`, and the completed `execute-plan` read-only verification plan records the same pin as a pre-existing baseline red. This plan does not change that file. The checker stops at this pin, so it cannot serve as an acceptance check for this scope. Do not edit or bypass the checker here; the owning execute-plan work remains separate.
- `python3 scripts/skill_text_budget.py --check`: pass, with advisory ratchet/caps messages and zero ceiling breaches.
- `git diff --check`: pass.
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-11-19-maintenance-dry-exit-conversion-fall-through.md`: pass.
- Validation-authoring rule 19 RED-today evidence: not applicable; the plan has no forbidden-phrase sweep. Rule 22 exact-text mechanical audit: not applicable; the plan has no validation span pinned against prescribed task text.

## Validation Commands

```bash
python3 scripts/skill_text_budget.py --check
bash scripts/scan-public-hygiene.sh
git diff --check
```

### Task 1: Include backlog conversion in dry-exit continuity

Context surface: Terms, this task, Standing constraints, and Design Invariants.

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/decisions.md`
- `agents/skills/maintenance/template-authoring.md`
- `agents/skills/investigate/SKILL.md`
- `docs/maintenance/operator-directives.md`

Primary class anchors:
- `Starvation switch` in `agents/skills/maintenance/SKILL.md`
- `Per-cycle harvest duty` in `agents/skills/maintenance/decisions.md`
- `FINAL STEP` in `agents/skills/maintenance/template-authoring.md`
- `D-18` in `docs/maintenance/operator-directives.md`

- [x] `Starvation switch` and D-18 queue-empty reading include the next eligible uncovered backlog group from the full open-backlog corpus using investigate Stage 0 survey and Stage 1 grouping, eligibility, and skip rules: given an eligible row outside the current cycle findings and not represented by either log or a plans-root plan, expects queue-empty to remain false [class: IMPLEMENTATION_REQUIRED]
- [x] The authoring closeout performs at most one investigate group invocation at a dry exit when the quota and standing directive permit, with a dry-exit corpus selection independent of current-cycle findings; given the monitor already investigated during the same cycle, expects no duplicate pass [class: IMPLEMENTATION_REQUIRED]
- [x] Investigate Purpose permits all entries routed for one group while preserving the one-group invocation boundary and no-dispatch/no-execution end; given a mixed-verdict group, expects every routed entry to pass its destination checker and commit before the unit completes [class: IMPLEMENTATION_REQUIRED]
- [x] Maintenance and investigate Integration Points reciprocally document the dry-exit corpus invocation and the one-group, all-routed-entries completion boundary [class: IMPLEMENTATION_REQUIRED]
- [x] Any prompt-log writer refusal or incomplete routed entry follows the existing D-18 blocked-retry path and cannot produce a queue-empty report [class: IMPLEMENTATION_REQUIRED]
- [x] D-18 reporting preserves all exit tokens and the `loop-liveness:` carrier or exemption details; given no converter input remains, expects the existing queue-empty outcome, and given a 5h wall, expects the existing reset-anchored successor at reset plus its standing margin [class: IMPLEMENTATION_REQUIRED]
- [x] Existing project-class, survey-only, explicit-stop, blocked-retry, prompt-log writer, and quota guards remain controlling; given each existing stop condition, expects its current disposition [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Validation Commands and confirm all listed checks return success [class: REPOSITORY_TEST]
- [x] Commit: `fix: keep maintenance alive for unconverted backlog work` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-19-authoring-dry-exit-conversion-fall-through.md`: covered by this completed plan; its execution flip changed the origin witness to `covered (docs/history/plans/2026-11-19-maintenance-dry-exit-conversion-fall-through.md)`, and this completion pass folds the disposition here before deleting the origin.
