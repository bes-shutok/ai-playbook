# Plan: invoke self-heal before recoverable workflow stops

Backlog origin: docs/history/backlog/2026-10-27-self-heal-before-workflow-stop.md
Driving force: code-quality + efficiency
Plan review record: `.ai-playbook/reviews/2026-10-27-plan-review-self-heal-before-workflow-stop-r*.md` (highest round for this source plan is authoritative)
Execution budget: 1h total, largest task 1h
Authoring claim: `docs/tmp/authoring-claims/2026-10-27-self-heal-before-workflow-stop.md` (session `01a17c5c-b1b6-7c02-8203-5bc9bf7f9ab3`)

## Terms
- **Recoverable stop**: A workflow failure whose cause and an authorized remedy can be determined from repository evidence, available tools, or an existing procedure.
- **Recovery disposition**: The outcome self-heal records after resolving the refusal, preserving it for a user decision, or finding no authorized recovery.
- **Normal closeout**: The plans skill's required done handoff and the done skill's final closeout sequence.

## Why
The generic `using-skills` rule already routes recoverable stops through self-heal, but the witnessed plan closeout stopped on a done-run refusal before using that path. Explicit handoffs at normal plan and done closeout make the existing recovery route visible where these workflows can stop, while retaining each owner's gates and authority rules.

## Gist & Examples
Title: invoke self-heal before recoverable workflow stops

TLDR: Make the existing self-heal handoff explicit at normal plan and done closeout stops.

Before: the central rule exists, but a recoverable done-run refusal stopped the plan workflow until the user invoked self-heal.

After: plans and done route recoverable stops through self-heal before asking the user to initiate routine recovery; existing gates and user-only decisions remain in force.

Edge cases: preserve fail-closed refusals, retry budgets, ownership checks, and completion witnesses; do not repeat a recovery already dispositioned or add machinery.

## Outcome
The plans and done skills explicitly route ordinary recoverable workflow stops through self-heal. The reciprocal integration map describes their roles alongside existing consumers. Recovery remains bounded by the caller's authority and existing gates.

- Done-run refusals remain fail-closed until self-heal finds an already-authorized recovery and the refused gate passes.
- Existing review-loop, execute-plan, review-plan, maintenance, using-skills, and investigate integrations retain their specialized triggers.
- No new gate, validator, hook, state, ledger, ceremony, retry allowance, or recovery mechanism is introduced.
- Each touched skill's operative text pays for growth with an equivalent deletion.

Gate delta: zero gates or workflow machinery added or removed; the change is skill-text integration only, and the existing done-run refusal stays fail-closed.

## Assumptions
- The witnessed miss is a consumer handoff gap: `using-skills` already routes recoverable stops, while plans names only review-loop recurrence and done only describes stop conditions. Evidence: the origin and the current skills named there.
- The done-run refusal must remain fail-closed; self-heal may use an existing remedy but cannot bypass the refused gate. Evidence: `self-heal/SKILL.md` Recovery and the origin.
- Existing specialized integrations remain authoritative for their lanes. Evidence: `self-heal/SKILL.md` Integration Points and each named consumer.
Decision points requiring a grill: none remain; maintenance-selected authorization selects the focused plans/done handoff from the origin's alternatives.

## Standing constraints
- Invoke self-heal before stopping for an ordinary recoverable plans or done workflow refusal.
- Preserve caller scope, retry budgets, ownership checks, hard gates, and user-only decisions.
- Do not repeat self-heal after a recovery disposition already resolves the stop.
- Add no machinery and balance operative-text growth in each edited skill file.

## Evaluation Criteria
- Plans and done identify when to invoke self-heal and keep their closeout boundaries explicit.
- Self-heal's integration map and the two consumer skills describe reciprocal roles without duplicating existing specialized triggers.
- Done-run refusals, retry limits, ownership rules, user decisions, and completion evidence remain unchanged.
- Realistic workflow examples cover a recoverable refusal, an unresolved user decision, and a completed recovery disposition without a duplicate call.
- Every touched skill file has at least as many operative bytes removed as added; no new machinery appears.

**Quality dimensions:** Correctness: handoffs preserve existing gates and authority. Efficiency: routine recovery is considered before the user must initiate it.

**Done when:** the three skill files specify the reciprocal handoffs, preserve existing refusal behavior, pass realistic-context review, and meet the byte-balance rule.

**Ship when:** documentation and plan land through the existing plan closeout.

## Review Scope

**Explicit must-fix:**

**Documentation:**
- `agents/skills/plans/SKILL.md` (Task 1)
- `agents/skills/done/SKILL.md` (Task 1)
- `agents/skills/self-heal/SKILL.md` (Task 1)

**Plan-related extension:** none; report any required additional path before editing it.

**Out of scope; reject unless plan-related:** workflow scripts, validators, gates, hooks, state files, runtime recovery behavior, and other consumer skills; reason: the origin requests an explicit skill-text handoff and no new mechanism.

## Validation Commands

- `python3 scripts/plan_readiness.py docs/history/plans/2026-10-27-self-heal-before-workflow-stop.md`
- `bash scripts/scan-public-hygiene.sh --files agents/skills/plans/SKILL.md agents/skills/done/SKILL.md agents/skills/self-heal/SKILL.md`

## Tasks

### Task 1: Add explicit self-heal handoffs at ordinary closeout stops

Context surface: the origin and requirements record, `using-skills` Step 1, plans Final Step, done Workflow continuity, and self-heal Recovery and Integration Points.

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/done/SKILL.md`
- `agents/skills/self-heal/SKILL.md`

- [x] Add a plans handoff for recoverable normal authoring and closeout stops; preserve review-loop triggers and completion evidence. [class: IMPLEMENTATION_REQUIRED]
- [x] Add a done handoff before stopping on a recoverable workflow failure; preserve fail-closed runner refusals and user-only decisions. [class: IMPLEMENTATION_REQUIRED]
- [x] Update self-heal's reciprocal integration map for plans and done; preserve all existing consumer-specific triggers. [class: IMPLEMENTATION_REQUIRED]
- [x] Specify that one resolved recovery disposition ends the handoff, with no duplicate self-heal call for that stop. [class: IMPLEMENTATION_REQUIRED]
- [x] Validate realistic recoverable, user-decision, and resolved-recovery examples; confirm existing gates and authority remain intact. [class: IMPLEMENTATION_REQUIRED]
- [x] Remove equivalent operative bytes from each edited skill file and add no machinery. [class: IMPLEMENTATION_REQUIRED]
- [x] Run plan readiness and the public hygiene scan for the changed files. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: route recoverable closeout stops through self-heal` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-27-self-heal-before-workflow-stop.md`: covered by this plan (Status: covered recorded 2026-10-27; origin deleted in this completion pass; implementation witness: `execute-plan: land self-heal-before-workflow-stop`, 2026-10-27).
- `docs/history/backlog/2026-10-27-self-heal-done-staging-classification-asks-label.md`: covered by Task 1 review correction (Status: covered recorded 2026-10-27; origin deleted on 2026-10-28; implementation witness: the done handoff names the side-repo staging asks and Step 0 lock return, 2026-10-27).
- `docs/history/backlog/2026-10-27-self-heal-disposition-taxonomy-provider-enumeration.md`: covered by Task 1 review correction (Status: covered recorded 2026-10-27; origin deleted on 2026-10-28; implementation witness: consumer handoffs refer to one recorded recovery disposition, 2026-10-27).
