# Plan: self-heal current-stage and recall

Backlog origins (scope of record):
- docs/history/backlog/2026-11-16-self-heal-defers-work-on-later-phase-gates.md
- docs/history/backlog/2026-11-14-self-heal-recall-surfaces-unnamed.md

Driving force: efficiency + code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-16-plan-review-self-heal-current-stage-and-recall-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 0.75h total, largest task 0.75h
Executed: yes (f2e7a343b2726db608cfaf16bcf9bdf552c24dee)
Authoring claim: 2026-11-16-self-heal-defers-work-on-later-phase-gates.md (session 01a1e033-74cc-7953-a390-2ed3f834e981)

## Terms

- **Current stage**: the caller workflow's present lifecycle step and the next action that the reported stop prevents.
- **Later-stage gate**: a requirement whose source names a later activation point, such as before merge or release, and whose unmet state does not prevent the current authorized action.
- **Recall surface**: an existing project or user source used to find a prior disposition, related backlog, or lesson before creating a duplicate record or asking for direction.

## Why

Self-heal was invoked repeatedly but did not resume authorized local implementation because it treated later merge obligations as current blockers. Its backlog step also names no sources to consult, even when the refusal has already been investigated.

## Gist & Examples

TLDR: make self-heal classify gates by their activation stage and consult named recall surfaces, improving efficiency through the existing recovery path.

**Before:** an unchecked `Before merge` follow-up is treated as a prerequisite to the next local implementation step, and self-heal creates or escalates a blocker without checking the relevant backlog, lessons, or session memory.

**After:** self-heal identifies the current step, the exact next action, and each gate's source-defined activation point. It carries later obligations through the caller's existing disposition, such as moving a release condition to `Ship when`, and continues only work already within scope. A gate that blocks the current action, or an unresolved user, owner, safety, or authorization decision, remains blocking.

**Examples:**
- A requirement explicitly due before merge stays recorded for that boundary while authorized local implementation continues.
- A current-stage prerequisite remains blocking when the next action depends on it.
- An external owner action stays blocking when that owner must act before the current step can proceed.
- An unclear activation point is reported as unresolved; self-heal does not infer that the gate is later or silently skip it.
- Before creating a duplicate backlog item or asking for direction, self-heal checks the caller's named recall rule, or the available project backlog, lesson corpus, and user-level session memory index.

## Outcome

Self-heal continues authorized work past later-stage obligations while preserving the gates that apply now and reusing relevant prior decisions.

- Later obligations remain visible and are handled at their stated boundary.
- Current prerequisites, user decisions, external-owner actions, and safety or authorization gates retain their existing force.
- Recovery consults existing evidence before creating duplicate records or asking the user.

Gate delta: +1 recovery classification instruction and +1 recall-surface instruction; removed: none; existing gates, refusal classes, retry limits, authority boundaries, and completion conditions are unchanged; no machinery is added; priced by the two open origin rows and their witnessed recovery and recall misses.

## Assumptions

- assume self-heal is the single canonical home for the generic recovery classification and recall instructions; basis: both origins identify its Recovery section, and the investigation found the caller already has a sanctioned later-stage disposition.
- assume the caller-specific recall rule takes precedence when present, with the project backlog, lesson corpus, and available user-level session memory index as the generic fallback; basis: the maintenance self-heal handoff already owns named surfaces without making them universal paths.
- assume one skill-text change is sufficient and no caller gate or validator change is needed; basis: the execute-plan inclusion gate already permits carrying non-executable release conditions into `Ship when`, while the incident lacked stage-boundary classification during recovery.
- assume unavailable recall surfaces are skipped and reported as unavailable rather than treated as a new blocker; basis: recovery must use accessible evidence without creating a new access prerequisite.
Decision points requiring a grill: none remain.

## Standing constraints

- Preserve the caller's authority, gates, retry limits, and completion boundary; a later-stage classification carries an obligation forward but never completes or bypasses it.
- Use an existing caller disposition for later-stage items; a new recovery rule does not change any caller gate.
- Add no validator, hook, lock, ledger, or required ceremony.

## Evaluation Criteria

**Quality dimensions:**
- Stage correctness: source-defined activation points distinguish current prerequisites from later obligations.
- Authority: existing gates and user or external-owner decisions retain force when the current action depends on them.
- Evidence: each classification cites its source; uncertain boundaries remain unresolved.
- Recall: the caller's named recall rule is preferred, with generic surfaces available before duplication or escalation.

**Done when:** the Recovery procedure and its examples meet all task witnesses, and the listed readiness, hygiene, and text-budget checks pass.

**Ship when:** the plan and review records land through the existing plan closeout.

**Done when:** the self-heal Recovery section requires stage and next-action classification, preserves later obligations through caller-authorized dispositions, keeps current-stage blockers intact, names the fallback recall surfaces, and the listed validation commands pass.

**Ship when:** the plan and review records land through the existing plan closeout.

## Documentation Impact Assessment

Scanned the existing `docs/` tree. No project documentation needs an update: this change defines a cross-project recovery workflow, whose canonical home is the self-heal skill; the caller and maintenance rules are verified as existing sources during implementation.

## Review Scope

**Explicit must-fix:** valid findings on the changed Recovery text, its caller-authority boundary, stage classification, and recall behavior.

**Documentation:**
- `agents/skills/self-heal/SKILL.md` (Task 1)

**Plan-related extension:** findings in the execute-plan inclusion rule or maintenance recall rule may inform the changed skill text, but those files are not task outputs; report any proposed edit before expanding scope.

**Out of scope; reject unless plan-related:** caller gate semantics, skip marks, validators, hooks, receipts, ledgers, retry budgets, authority rules, and duplicate recall lists; reason: the existing caller already defines safe dispositions, and one recovery-text change addresses both origins.

## Validation Commands

Authoring preflight before review round 1:
- `bash scripts/check-no-em-dash.sh touched`: passed.
- `bash scripts/scan-public-hygiene.sh`: passed.
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-11-16-self-heal-current-stage-and-recall.md`: passed.
- The full readiness command returned `OUTCOME: fail` only because no review artifact exists yet; sidecar and plan probes were skipped. This is the expected pre-review condition.
- Public hygiene passed; `python3 scripts/skill_text_budget.py --check` passed with 0 ceiling breaches and advisory cap, pilot, and cap-entry warnings.
- Validation-authoring rule 19 RED-today evidence: not applicable; no forbidden-phrase sweep is pinned.
- Validation-authoring rule 22 mechanical pin audit: not applicable; no literal spans are pinned.

```bash
python3 scripts/plan_readiness.py docs/history/plans/2026-11-16-self-heal-current-stage-and-recall.md
bash scripts/scan-public-hygiene.sh --files agents/skills/self-heal/SKILL.md
python3 scripts/skill_text_budget.py --check
```

### Task 1: Classify current-stage gates and name recall surfaces

Context surface: the plan Terms and Standing constraints, this task, both backlog origins, the investigation entry `self-heal-current-stage-and-recall`, the self-heal Recovery section, the execute-plan Inclusion Hard Gate, and the maintenance self-heal recall rule.

Files:
- `agents/skills/self-heal/SKILL.md`

- [x] Given an explicit `Before merge` requirement and an authorized local implementation action, expect the requirement to remain visible for merge and the local action to continue through the caller's existing disposition, such as `Ship when`. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a requirement that must hold before the next current-stage action, expect self-heal to preserve the stop until that prerequisite is resolved. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a user decision or external-owner action required before the next action, expect self-heal to keep it blocking and ask or route only under the caller's existing authority. [class: IMPLEMENTATION_REQUIRED]
- [x] Given an unclear activation boundary, expect self-heal to report it as unresolved without guessing, marking it complete, silently skipping it, or editing or bypassing its gate. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a caller recall rule, expect self-heal to consult it first; when none exists, expect it to search available project backlog, lesson corpus, and user-level session memory before creating a duplicate or asking for direction. [class: IMPLEMENTATION_REQUIRED]
- [x] Given any recovered stop, expect existing authority, user-only, retry, and completion boundaries to remain in force and no new machinery to be introduced. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the listed plan-readiness, public-hygiene, and text-budget checks against the resulting files. [class: REPOSITORY_TEST]
- [x] Commit: `self-heal: classify current-stage gates and recall evidence` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-16-self-heal-defers-work-on-later-phase-gates.md`: Task 1 completed the stage classification and later-boundary carry-forward behavior; disposition folded here and former origin deleted in the 2026-11-17 completion pass.
- `docs/history/backlog/2026-11-14-self-heal-recall-surfaces-unnamed.md`: Task 1 completed the caller-first and generic fallback recall behavior; disposition folded here and former origin deleted in the 2026-11-17 completion pass.
