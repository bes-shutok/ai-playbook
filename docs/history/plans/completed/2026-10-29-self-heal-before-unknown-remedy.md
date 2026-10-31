# Plan: invoke self-heal before an unknown remedy stops the workflow

Backlog origin: docs/history/backlog/2026-10-29-self-heal-unknown-remedy-trigger.md
Driving force: efficiency + code-quality
Plan review record: `.ai-playbook/reviews/2026-10-29-plan-review-self-heal-before-unknown-remedy-r*.md` (highest round for this source plan is authoritative)
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: `docs/tmp/authoring-claims/2026-10-29-self-heal-unknown-remedy-trigger.md` (session `01a1875f-5fcf-74f2-8a58-18f079231711`)

## Terms
- **Disposition**: the single result of self-heal for a stop: recovery and gate recheck, preserved user decision, or no authorized recovery.
- **Named fail-closed remedy**: the specific remedy an existing refusal procedure permits while keeping its gate closed.
- **User-only stop**: a decision or action the existing workflow assigns to the user or another owner.

## Why
The current handoffs require the caller to recognize a failure as recoverable before invoking self-heal, even though self-heal searches for the authorized recovery. A closeout refusal therefore reached a request for user help before the existing recovery sources were checked.

## Gist & Examples
TLDR: Invoke self-heal before an uncertain workflow stop, improving efficiency through the existing recovery path.

**Before:** `done` asks the user for a backup location when a closeout refusal leaves the remedy uncertain; `plans` accepts a refusal without knowing whether `done` already considered recovery.

**After:** The owning caller invokes self-heal once before deciding that a non-user-only failure or refusal has no authorized recovery. `done` returns its disposition; `plans` carries it without a duplicate call and invokes self-heal only for an un-dispositioned closeout refusal.

**Examples:**
- An uncertain recoverable refusal invokes self-heal before the caller decides recovery is unavailable; an authorized remedy is applied and the refused gate is rerun.
- If self-heal finds no authorized remedy, the caller preserves the exact refusal and stops under existing rules; it does not weaken the gate or invent authority.
- A user-only ownership or staging choice remains with the user; self-heal does not choose for them or route around the decision.
- When `done` returns a recovery disposition for its closeout, `plans` records and carries that result without calling self-heal again.
- When a closeout refusal reaches `plans` without a disposition, `plans` invokes self-heal once before forwarding the refusal; named fail-closed remedies remain limited to their existing procedure.

## Outcome
Plans and done check the existing recovery path before stopping on uncertain non-user-only failures.
- Callers no longer require proof of recoverability before invoking the recovery skill.
- The plans-to-done closeout boundary preserves one disposition and does not repeat recovery.
- Existing user decisions, refusal gates, and completion evidence continue to control closeout.

Gate delta: no gates, refusal classes, fences, protocol layers, schema fields, blocking review duties, or task conditions are added or removed; the existing repo-wide review-time byte-balance discipline applies unchanged; no recovery allowance changes.

## Assumptions
- assume the origin's two handoff sections are the complete scope; basis: frozen prompt names only those paths and the current incident concerns that boundary.
- assume examples may be concise operative prose in those handoffs; basis: the selected prompt requires five cases and the prior plan established this style.
- assume no invocation validator or receipt is justified; basis: the origin records no witnessed mechanical signal and repository machinery admission requires a true catch before promotion.
Decision points requiring a grill: retain the plans and done caller handoffs; source: frozen prompt and predecessor plan, 2026-10-29, affected sections: Why and Task 1; invoke before deciding the remedy is known; source: origin and witnessed closeout row, 2026-10-29, affected sections: Gist & Examples and Task 1; omit an invocation validator or receipt; source: origin alternatives and machinery admission contract, 2026-10-29, affected sections: Gate delta and Review Scope.

## Evaluation Criteria
- Correctness: trigger precedes recoverability judgment; named fail-closed remedies and user-only decisions remain authoritative.
- Continuity: `done` returns one disposition; `plans` carries it without repeating self-heal and handles an un-dispositioned closeout refusal once.
- Scope discipline: missing-evidence and report-retention behavior, retry limits, ownership checks, completion evidence, and the separate review-loop trigger remain unchanged.
- Examples: all five requested cases are stated with observable caller behavior.
- Text balance: each changed skill file removes at least as many operative bytes as it adds.

**Done when:** both handoffs encode the trigger and boundary semantics, the five cases are covered, invariants remain unchanged, text balance holds, and plan readiness and hygiene checks pass.

**Ship when:** the plan and review records land through the existing plan closeout.

## Review Scope

**Explicit must-fix:** all valid findings on the two handoff sections are in scope.

**Documentation:**
- `agents/skills/plans/SKILL.md` (Task 1)
- `agents/skills/done/SKILL.md` (Task 1)

**Plan-related extension:** no additional paths; report any causally necessary path before editing it.

**Out of scope; reject unless plan-related:** gates, validators, receipts, ledgers, schemas, hooks, self-heal recovery procedure, other consumer skills, report retention, and missing-evidence behavior; reason: the origin requests only a caller-trigger correction and boundary disposition.

## Validation Commands

```bash
python3 scripts/plan_readiness.py docs/history/plans/2026-10-29-self-heal-before-unknown-remedy.md
bash scripts/scan-public-hygiene.sh --files agents/skills/plans/SKILL.md agents/skills/done/SKILL.md
```

### Task 1: Invoke self-heal before deciding an uncertain stop is unrecoverable

Context surface: the origin, this plan's Terms, task, and evaluation criteria.

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/done/SKILL.md`

- [x] Update `plans` to invoke self-heal before classifying an imminent non-user-only stop as unrecoverable, while carrying `done`'s one disposition and handling a closeout refusal without one. [class: IMPLEMENTATION_REQUIRED]
- [x] Update `done` to invoke self-heal before deciding whether an imminent non-user-only failure has an authorized recovery; keep user-only decisions and named fail-closed remedies within their existing boundaries. [class: IMPLEMENTATION_REQUIRED]
- [x] State observable examples for uncertain recovery, no authorized remedy, user-only stop, returned disposition, and un-dispositioned closeout refusal. [class: IMPLEMENTATION_REQUIRED]
- [x] Preserve retry, ownership, completion, missing-evidence, report-retention, and review-loop behavior; add no machinery. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the listed plan-readiness and hygiene checks for the resulting plan and changed skill files. [class: REPOSITORY_TEST]
- [x] Commit: `docs: invoke self-heal before deciding recovery is unknown` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-29-self-heal-unknown-remedy-trigger.md` (origin row, Status: covered) — fully served by Task 1; deleted from the living backlog in this completion pass; durable home is this archived plan.
- `docs/history/backlog/2026-10-30-self-heal-integration-points-recoverable-precondition.md`: not a migrated origin, a follow-up row created by the execution run's Step 1.2b review (self-heal/using-skills Integration Points drift); landed ad-hoc 2026-10-31 (covered-row deletion in the self-heal caller-map restoration change).
