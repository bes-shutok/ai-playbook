# Plan: maintenance consults self-heal before stopping on blockers

Backlog origins (scope of record):
- docs/history/backlog/2026-11-02-maintenance-self-heal-first-on-blocks.md
- docs/history/backlog/2026-10-15-codex-stale-worktree-pins-landing-recovery.md
Driving force: efficiency + code-quality
Plan review record: the staging series `.ai-playbook/reviews/2026-11-02-plan-review-maintenance-self-heal-first-on-blocks-r*.md` (the highest rN for this source plan is authoritative, including any deferred-residual list)
Execution budget: 1h total, largest task 0.5h
Authoring claim: `maintenance-self-heal-first-on-blocks.md` (session sess_582ef6ad-56d7-43ae-971b-59c20834c8b8)

## Terms

- **Blocker stop**: a maintenance scheduler turn, lane decision, or dispatched child session ending on, or asking the operator about, a refusal, failed tool, or unclear remedy that interrupted authorized work.
- **Self-heal consultation**: one invocation of the self-heal skill for one blocker that classifies the refusal from evidence, checks whether the guard is correctly applied, and applies or reports the smallest authorized remedy.
- **Disposition**: the single recorded result of a self-heal consultation for one blocker: a recovery applied and the refused gate re-run, a preserved user decision, or a report that no authorized recovery exists.
- **Stale-baseline refusal**: a check refusal whose expected literals or baseline no longer match the checked branch because the branch's base moved; for example a pins suite failure on a task branch whose base predates the pin expectations current main carries.
- **User-only stop**: a decision or action the existing workflow assigns to the operator: missing authority, ambiguous ownership, an unsafe target, an external-owner action, or an explicit operator stop.

## Why

The universal skill-use rule already requires consulting self-heal before judging a skill-workflow stop unrecoverable, but maintenance's own Blocker recovery wording admits only "an unexpected issue with a safe, compliant workaround", so routine guard refusals, failed tools, and apparent design decisions fell outside the obvious trigger and the workflow stopped twice while the operator had to invoke self-heal by hand. A second witnessed stop treated a moved pin baseline as a task blocker and stranded authorized work although the existing refresh-and-rerun remedy was available. Both stops are wording and handoff gaps on one shared surface, not missing machinery.

## Gist & Examples

TLDR: Align maintenance's blocker-recovery trigger and handoffs with the universal self-heal rule, so one consultation by one owner precedes every non-user-only stop, improving efficiency.

**Before (today):** maintenance invokes self-heal only for "an unexpected issue with a safe, compliant workaround". A lane that hits a routine guard refusal, a failed tool, or a refusal that merely looks like a design question can stand down or ask the operator without any self-heal consultation; the operator had to issue two self-heal prompts to resume and finish one authorized maintenance effort. On a task branch whose base moved, a pins suite failure over stale expected literals was reported as a task blocker and the worktree stayed allocated, although refreshing the branch onto current main made the unchanged suite pass.

**After (this plan):** before a maintenance lane, scheduler turn, or child session ends on a blocker or asks the operator about one, the owning surface consults self-heal once: it classifies the refusal from evidence, checks whether the guard is correctly applied, and applies or reports the smallest authorized remedy. A child's returned disposition is carried by its parent without a second call. Maintenance-owned architectural and design tradeoffs are decided and recorded, not asked. A baseline-dependent refusal is classified against the branch's base before being attributed to the task, and the refresh-and-rerun remedy is applied when current main holds corrected expectations, while a genuine current-tree failure keeps blocking.

**Edge cases:** an explicit operator stop and every user-only stop stay with the operator and require no consultation. Correctly applied quota, ownership, safety, and authorization guards remain blocking; self-heal never edits or bypasses a valid gate. One recorded disposition ends the self-heal handoff for that blocker, so an exhausted recovery is never repeated. No validator, classifier, ledger, retry loop, or ceremony is added.

## Outcome

A maintenance session consults self-heal before any non-user-only blocker becomes a stop or an operator question, and stale baseline evidence is re-evaluated before it blocks authorized work.

- Routine guard refusals and failed tools route through one self-heal consultation by the owning surface before a stand-down or an operator ask.
- A recovery disposition returned for a child's blocker is carried by the deciding turn without a duplicate call.
- Maintenance-owned architectural and design tradeoffs are decided and recorded under the standing mandate, with questions reserved for user-only stops.
- A pins suite failure over a moved branch base is classified and refreshed before it is attributed to the task; a genuine current-tree failure still blocks.
- No new gate, validator, ledger, retry allowance, or recovery mechanism is introduced, and each edited skill file removes at least as many operative bytes as it adds.

Gate delta: none. No gate, fence, refusal class, protocol layer, schema field, blocking review duty, or dispatch-pausing condition is added or removed; two existing skill-text wordings are realigned and the existing checks (pins suite, hygiene scan) apply unchanged.

## Assumptions

- The gap is maintenance's own wording, not the universal rule: `using-skills` already routes recoverable stops through self-heal, and the witnessed session stopped twice anyway. Evidence: the primary origin row and `agents/skills/using-skills/SKILL.md` Proactive Usage Principles.
- The single-disposition rule already exists in self-heal; the fix carries it into maintenance's own wording rather than inventing a new rule. Evidence: `agents/skills/self-heal/SKILL.md` Recovery step 4 ("one recorded recovery disposition ends the handoff for that stop").
- The stale-baseline remedy needs no new checker: the classification and the refresh-and-rerun route land as recovery guidance in the same Blocker recovery flow, with the witnessed incident cited in one line. Evidence: the stale-pin origin row's Expected section and its alternatives (weaken-the-pins and new-validator alternatives rejected there).
- Maintenance standing pre-authorization already makes recurring runs decide and proceed without questions; the plan states the contrast explicitly (AI-owned tradeoffs decided and recorded; questions reserved for user-only stops) instead of adding an authorization mechanism. Evidence: `agents/skills/maintenance/SKILL.md` standing pre-authorization sentence.
- Valid quota, retry, ownership, and authorization boundaries are untouched. Evidence: both origin rows preserve guards; the completed self-heal handoff plans (2026-10-27, 2026-10-29) established the same preservation pattern for plans and done.
Decision points requiring a grill: one owner per blocker is the blocker's owning surface (the deciding turn, or the child session it dispatched for that surface), decided from the origin's trace scope without a template-side owner registry; source: origin Scope, 2026-11-02, affected sections: Terms, Task 1; the trigger extension covers every non-user-only stop, not only unexpected failures with known remedies; source: origin alternatives and the 2026-10-29 completed plan's same inversion finding, 2026-11-02, affected sections: Why, Task 1; the stale-baseline remedy lands as recovery classification guidance, never a validator or freshness gate; source: stale-pin origin alternatives and the machinery admission protocol, 2026-11-02, affected sections: Task 2, Gate delta; scope extensions: none proposed (omit-extension for the operator-directives carrier text, which already lifts its clauses from the directives home at dispatch and needs no edit).

## Standing constraints

- Add no gate, validator, classifier, ledger, retry loop, recovery allowance, or required ceremony; the Repository Guidelines' Machinery admission protocol requires a witnessed catch before any blocking machinery, and no origin witnesses one here.
- Every edited skill file removes at least as many operative bytes as it adds.
- Preserve existing guards, the single-disposition rule, caller limits, user-only boundaries, and completion evidence.

## Evaluation Criteria

- Trigger correctness: the reworded Blocker recovery text consults self-heal before any non-user-only stop is judged unrecoverable or surfaced to the operator, and names the owning surface that consults.
- Disposition continuity: the text carries a returned disposition across the child-to-parent handoff exactly once and forbids a repeat consultation for the same blocker.
- Guard preservation: quota, ownership, safety, explicit-stop, retry, and authorization boundaries read as unchanged in every edited file.
- Stale-baseline handling: the recovery flow distinguishes a stale-baseline refusal (classify against the branch base, refresh and rerun) from a genuine current-tree failure (stays blocking) without adding a check.
- Text balance: each edited file has an operative-byte delta at or below zero, measured in bytes over the diff's added versus removed body lines, the deletions each task's rewording performs (the retired narrower-trigger phrases and their surrounding sentences) being the payment source for its additions.
- No machinery: no new gate, validator, ledger, or ceremony appears in any edited file.

**Quality dimensions:**
- Correctness: the reworded trigger and handoffs preserve every existing boundary; examples cover routine refusal, user-only stop, carried disposition, stale baseline, and genuine failure.
- Maintainability: the wording stays in the existing homes (decisions.md Blocker recovery, the two Integration Points entries), single-sourced, with the incident cited in one line per the witness budget.

**Done when:**
- The three edited files state the aligned trigger, one-owner consultation, and disposition-carry rules with the stale-baseline classification in the recovery flow, and each file's operative-byte delta is at or below zero.
- The pins suite result is unchanged relative to its pre-existing base status (no new pin failure introduced by the rewording), and the public hygiene scan exits 0.

**Ship when:**
- None stated; the change is repository-owned skill text with no external release condition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code (skill text):**
- `agents/skills/maintenance/decisions.md` (Task 1)
- `agents/skills/maintenance/decisions.md` (Task 2)
- `agents/skills/maintenance/SKILL.md` (Task 1)
- `agents/skills/self-heal/SKILL.md` (Task 1)

**Tests:**
- none; the change is skill text verified by the pins suite and hygiene scan against their pre-existing base status.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/using-skills/SKILL.md`; reason: the universal rule is already correct and is the fixed reference point, not an edit target.
- `docs/maintenance/operator-directives.md`; reason: the directives home is operator-owned and lifted at dispatch, not edited by this plan.
- `scripts/check_maintenance_pins.sh`; reason: no pin covers the reworded spans; a pin failure is classified per Task 2, and pin edits are execution-discovered repair, not planned scope.

## Validation Commands

```bash
bash scripts/check_maintenance_pins.sh
bash scripts/check-no-em-dash.sh added-lines --base <branch point this run started from>
bash scripts/scan-public-hygiene.sh
```

### Task 1: One consultation, one owner, carried disposition

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `agents/skills/maintenance/decisions.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/self-heal/SKILL.md`

- [x] The Blocker recovery section in `agents/skills/maintenance/decisions.md` states the universal trigger: given a non-user-only blocker (a routine guard refusal, a failed tool, or an unclear remedy) on any maintenance stop path, expects the wording to require one self-heal consultation before the stop is judged unrecoverable, a pause is recorded, or the operator is asked. [class: IMPLEMENTATION_REQUIRED]
- [x] The same section names the owning surface: given a blocker on a surface a dispatched child owns, expects the child to consult once and return a disposition, and the deciding turn to carry that disposition without a second call for the same blocker; given a blocker the deciding turn itself owns, expects the turn to consult once directly. [class: IMPLEMENTATION_REQUIRED]
- [x] The section preserves boundaries: given an explicit operator stop, a user-only decision, or a correctly applied quota, ownership, safety, or authorization guard, expects the wording to keep it blocking and outside the consultation requirement, with self-heal never editing or bypassing a valid gate. [class: IMPLEMENTATION_REQUIRED]
- [x] The self-heal Integration Points entry in `agents/skills/maintenance/SKILL.md` and the maintenance entry in `agents/skills/self-heal/SKILL.md` describe the same trigger and single-consultation contract, with neither entry carrying a stale narrower trigger phrase; both Integration Points entries state each side's role without duplicating operative rules. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the rewording leaves the pinned spans in the edited files intact and the pins suite result unchanged relative to its pre-existing base status; the section's operative-byte delta per file is at or below zero. [class: REPOSITORY_TEST]

### Task 2: Stale-baseline classification and AI-owned tradeoffs

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `agents/skills/maintenance/decisions.md`

- [x] The Blocker recovery flow classifies stale baseline evidence: given a baseline-dependent refusal (for example a pins suite failure whose expected literals do not match the spans at the task branch's base), expects the wording to require comparing the refused check's expectations against the branch's base before attributing the failure to the task. [class: IMPLEMENTATION_REQUIRED]
- [x] The same flow names the authorized stale-baseline remedy and its boundary: given a refusal classified stale-baseline, expects the wording to name the remedy, rebase the branch onto the current default tip (`git rebase`) and rerun the unchanged check; given a failure that reproduces on the rebased branch, expects the wording to keep it blocking. [class: IMPLEMENTATION_REQUIRED]
- [x] The same flow states the AI-owned boundary: given a maintenance-owned architectural or design tradeoff surfaced by a blocker, expects the wording to decide it under the standing mandate and record the choice with its rationale, reserving operator questions for missing authority, ambiguous ownership, an unsafe target, an external-owner action, or an explicit operator stop. [class: IMPLEMENTATION_REQUIRED]
- [x] The stale-baseline class cites its witness in at most one line (the stale-pin origin row), the incident narrative staying in the origin rows per the witness budget. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the pins suite result is unchanged relative to its pre-existing base status and the file's operative-byte delta is at or below zero. [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-02-maintenance-self-heal-first-on-blocks.md` (origin row): covered by this plan; deleted at landing.
- `docs/history/backlog/2026-10-15-codex-stale-worktree-pins-landing-recovery.md` (origin row): covered by this plan; deleted at landing; decisions.md's stale-baseline witness re-pointed to this archived plan as the row's durable home.
- Residual rows filed in-branch and still open: `docs/history/backlog/2026-11-02-blocker-recovery-byte-payment-source.md`, `docs/history/backlog/2026-11-02-ip-boundary-pause-arm-compression.md`, `docs/history/backlog/2026-11-02-stale-baseline-arm-byte-debt.md`.
