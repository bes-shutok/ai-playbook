# Plan: placement closing-move doctrine enforcement

Backlog origin: docs/history/backlog/2026-10-09-plan-authoring-primary-placement.md
Driving force: simplicity + automation
Plan review record: the staging series .ai-playbook/reviews/2026-10-16-plan-review-placement-closing-doctrine-enforcement-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; the artifact slug is the plan's feature slug lowercased)
Execution budget: 3h total, largest task 1h

## Terms

- worktree policy: the facts-document key `worktree_policy`; after this plan it spells exactly two values, `worktrees` and `primary`.
- primary resolution: the single non-worktree resolution; run work happens in the primary checkout on its current branch under the immediate-commit rule; authoring and execution lanes both authorized.
- immediate-commit rule: every change is committed right after the change is made by a plain path-limited commit of the session's own paths; the done skill runs once at the end of the session's work, so its learn and other closeout steps fire once rather than per change; subagents return learnings and issues to the parent session, committing nothing themselves; the branch never carries dangling session-owned work product at a done boundary.
- dangling change: a modified, staged-but-uncommitted, or untracked session-owned work-product file still on the branch at the session's done boundary.
- direct-commit class: the small-change eligibility contract authored by the certified small-change plan of 2026-10-13, which is execution-ready and not yet in operative skill text; this plan's advisory carries its own bounds inline and does not depend on the class paragraph.
- closing move: for `worktrees` projects, the end-of-run sequence: transfer untracked artifacts, one squash landing under the merge-landing lock, mechanical hash or reference corrections riding the recorded-correction path, teardown of the run worktree and branch as the final step.
- pin guard: the placement-pins section added to `scripts/check_maintenance_pins.sh`; verifies required doctrine spans exist verbatim in the placement-owning skill files; warning-only.
- placement-owning skills: `agents/skills/execute-plan/SKILL.md`, `agents/skills/plans/SKILL.md`, `agents/skills/done/SKILL.md`, `agents/skills/maintenance/SKILL.md`.
- recorded correction: the zero-round re-bind path for mechanical post-landing deltas (plans skill review boundary).
- RED-today witness: executing the pin check against a tree with one pinned span removed and recording that it fires, before the guard's own task lands.

## Why

The closing-move doctrine is written down but enforced only by each session's self-judgment, and two overlapping non-worktree policy values exist where one simpler option suffices. The gaps bite: an oversized behavior-bearing change landed directly in the primary checkout past the tiny-edit class (2026-10-16), run worktrees stood for days after their work ended, and a consumer project declaring the primary policy cannot author plans at all because the authoring lane dead-ends. One consolidated non-worktree resolution with an immediate-commit rule, plus mechanical pins over the doctrine text, closes the blocker and stops later edits from diluting the rules silently.

## Gist & Examples

TLDR: one non-worktree policy resolution with an immediate-commit rule, plus a pin guard that fails loudly when any closing-move doctrine span is edited away.

Before: a project declaring the primary policy stops plan authoring dead; two non-worktree values (`primary`, `primary-execution`) overlap; a 152-line behavior-bearing change lands straight on the base branch through a lane that self-judged the tiny-edit class; nothing notices when a skill edit deletes a doctrine sentence.

After: the primary resolution authorizes all named lanes in the primary checkout with the immediate-commit rule (each change is committed as it is made by a plain commit, the done skill runs once at the end of the work; dangling work product is named at the done boundary); the direct-commit advisory flags an oversized direct landing by name; the pin guard verifies the doctrine spans on every pins run and reports exactly which span went missing; worktree-policy projects keep today's closing move unchanged.

## Outcome

Every worktree policy value resolves to a defined, mechanically pinned work placement and closing discipline.

- A primary-policy project can author and execute plans in its primary checkout without an operator override, closing the promoted consumer blocker.
- The closing-move rules survive later skill edits: deleting any pinned span fails the pins check with the span named.
- Hash or reference corrections after moving changed files ride the recorded-correction zero-round path, stated explicitly in the plans skill.

Gate delta: adds one warning-only read-only check section (the placement pins in `scripts/check_maintenance_pins.sh`; admission: incident 9a046452e, an oversized behavior-bearing direct landing past the direct-commit class witnessed 2026-10-16 in this repository's git history, plus five-day worktree residue; catch frequency: every pins run over skill text edits, at minimum once per authoring cycle touching the four files; false-positive cost: a legitimate rewording trips a pin until the pin list is updated in the same change, a one-line same-change edit; sunset: review after the first true catch, promotion only with a pre-registered registry-removal row) and one refusal-path sharpening in the done closeout (session-owned dangling work product is a named stop; Rule 42 origin-cited no-exit walk: the promoted origin and the 2026-10-16 operator decision record that worktree isolation is rejected for primary-policy projects, so immediate commit is the only isolation substitute, and each class-default alternative is impossible on the recorded evidence: silent pass is the exact shape that carried the 9a046452e oversized landing unnoticed, advisory-only is the posture the same incident showed being self-judged away, and reusing only the existing foreign-dirt refusal cannot cover this case because its predicate is other sessions' paths, never the session's own work product, so the named stop is the only remaining shape); removes the conflict-and-stop arm and the separate `primary-execution` value, both replaced by the consolidated primary resolution, with the stand-down route pins they carry in the pins checker retired in the same change; no other refusal class, gate, fence, protocol layer, or schema field is added, removed, or re-aimed.

## Assumptions

- assume the new primary resolution is a consolidation of the existing two values, not a third value; basis: the operator's 2026-10-16 decision that one non-worktree option is simpler, and no repository in this deployment declares either non-worktree value today.
- assume the promoted origin's "keep primary-execution separate" clause is superseded by that same operator decision; basis: the clause itself allows a distinct explicit decision to change it, recorded 2026-10-16.
- assume the branch-removal rule keeps its existing conditional shape: removed only when the work is content-verified accounted for, otherwise preserved with a named report and the safe-removal condition; basis: docs/history/backlog/2026-10-15-authoring-branch-retention-explanation.md and the plans Final Step.
- assume the lifecycle-owner registry ask of docs/history/backlog/2026-10-11-ad-hoc-worktree-lifecycle-owner-gap.md stays out of scope; basis: this plan pins existing teardown text and closes the placement blocker; ownership registry is a separate mechanism decision.
- assume the placement-decision owners are the four files in Terms; basis: repo-wide grep; other carriers of the policy key (docs-branch, bootstrap-ai-playbook, two scripts) resolve or report placement but own no placement decision, and stay out of scope.
- assume the direct-commit class paragraph is not in operative skill text: the certified small-change plan (docs/history/plans/completed/2026-10-13-small-change-direct-commit-policy.md) is execution-ready and unexecuted, and its class text exists only in that plan document; basis: repo-wide grep at authoring time, zero matches under agents/ and scripts/. This plan's advisory therefore carries its own bounds inline and pins no eligibility span.
- assume lesson 60 governs the audit arm: every rule verified against on-disk skill bytes, never against dispatch text or session claims.
- assume the primary resolution composes existing machinery (execution-claim serialization, company task-branch arm, done commit path) rather than new gates; basis: those mechanisms exist in the Worktree-first standard today.

Decision points requiring a grill: branch doctrine authored in this plan - user decision, AskUserQuestion receipt 2026-10-16, Scope and Tasks; one non-worktree option consolidating the two values - user decision, chat receipt 2026-10-16, Task 1; immediate-commit discipline via the done skill - user decision, chat receipt 2026-10-16, Task 2; policy-conditional scoping - user decision, mid-turn receipt 2026-10-16, Terms; supersession of the promoted origin's keep-separate clause - operator decision 2026-10-16 recorded in this section, Scope; done-runs-once cadence with plain per-change commits, subagent boundary is return-only (learnings and issues ride the parent's end-of-work learn capture and candidate emission; investigate stays operator-directed) - user decision, chat receipts 2026-10-16, Task 2; relocation clause names the corrections chain as its carrier and the plan-rename carve-out - operator question receipt 2026-10-16, Task 3.

## Standing constraints

- Single-homing: the Worktree-first standard's policy paragraph owns placement; consumer skills reference it and never restate it.
- Anti-growth: operative text cites each incident in at most one line; the dossier stays in records, backlog rows, and commit messages.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every pinned span quoted verbatim from the post-task text this plan prescribes; the pin check demonstrably fires when a span is removed (RED-today witness recorded before certification).
- no-regression: `worktrees`-policy behavior byte-identical; no existing operative doctrine sentence changed except the consolidation and the additions this plan prescribes; the consolidated primary resolution keeps the existing serialization and company task-branch sub-arms.
- maintainability: doctrine edits single-homed in the policy paragraph and the done placement section; the pin list lives in one script section.

**Done when:**
- `bash scripts/check_maintenance_pins.sh` reports `placement pins: all hold` and exits 0 on the landed tree.
- Removing any one pinned span from a placement-owning skill file makes the pins section report that span by name (witnessed once in-repo during execution, then restored).
- The retired value token appears nowhere in `agents/skills/execute-plan/SKILL.md`.
- The full Validation Commands block exits 0.

**Ship when:**
- none; repository-verifiable only.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/done/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `scripts/check_maintenance_pins.sh`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/land_squash.sh`; frozen landing machinery, this plan changes no landing helper bytes.
- `scripts/done_sweep_gates_lib.py`; its string naming the retired mode is a code constant consumed at runtime, not placement doctrine text; retargeting it is recorded as out of scope with this reason.
- `agents/skills/review-plan/SKILL.md` and other review skills; the review boundary is consumed, not changed.
- `docs/history/backlog/2026-10-15-authoring-branch-retention-explanation.md` and `docs/history/backlog/2026-10-11-ad-hoc-worktree-lifecycle-owner-gap.md`; alignment constraints recorded in Assumptions, their own fixes stay their own plans.
- `docs/history/backlog/2026-10-09-plan-authoring-primary-placement.md`; promoted origin, kept in place while this plan is open, folded at completion per the plans lifecycle.

## Validation Commands

```bash
set -e
set -o pipefail
cd "$(git rev-parse --show-toplevel)"
# placement pins hold (the section is warning-only for the script exit, so its summary line is the assertion)
bash scripts/check_maintenance_pins.sh | tee /tmp/pced-pins.txt
grep -q "placement pins: all hold" /tmp/pced-pins.txt || { echo "placement pins do not all hold"; exit 1; }
# the retired non-worktree value is gone from the placement owner and its normative contract (negated zero-match)
if grep -q "primary-execution" agents/skills/execute-plan/SKILL.md agents/skills/execute-plan/runtime-contract.md; then echo "retired policy value still present"; exit 1; fi
# the consolidated enum sentence is present (distinctive span from Task 1)
grep -q "outside the two spelled forms" agents/skills/execute-plan/SKILL.md || { echo "enum sentence missing"; exit 1; }
# the primary resolution carries its commit-cadence span (distinctive span from Task 1)
grep -q "immediate-commit rule" agents/skills/execute-plan/SKILL.md || { echo "primary resolution missing immediate-commit rule"; exit 1; }
# the done skill carries the commit cadence, the dangling-change stop, and the worker-boundary clause (distinctive spans from Task 2)
grep -q "committed right after the change" agents/skills/done/SKILL.md || { echo "immediate-commit commit cadence missing"; exit 1; }
grep -q "editing no tracked corpus and committing nothing" agents/skills/done/SKILL.md || { echo "worker-boundary clause missing"; exit 1; }
grep -q "dangling session-owned work product" agents/skills/done/SKILL.md || { echo "dangling-change stop missing"; exit 1; }
# the oversized-direct-landing advisory exists (distinctive span from Task 2)
grep -q "exceeds the direct-commit class bounds" agents/skills/done/SKILL.md || { echo "direct-landing advisory missing"; exit 1; }
# teardown-last and dispatch-isolation spans unchanged (distinctive spans pinned verbatim from current text)
grep -q "Delete only after verification" agents/skills/execute-plan/SKILL.md || { echo "teardown gate span missing"; exit 1; }
grep -q "before any worktree removal, migrate the run" agents/skills/execute-plan/SKILL.md || { echo "transfer-out span missing"; exit 1; }
grep -qF "per-execution ad-hoc worktrees per the Worktree-first standard" agents/skills/maintenance/SKILL.md || { echo "dispatch isolation span missing"; exit 1; }
test "$(grep -cF "execution children run in per-execution ad-hoc worktrees per the Worktree-first standard (isolation landed 2026-09-24, P57)" agents/skills/maintenance/SKILL.md)" -eq 1 || { echo "dispatch isolation span not unique to the operative bullet"; exit 1; }
# the recorded-correction path names the Task 3 span
grep -q "relocation-digest correction" agents/skills/plans/SKILL.md || { echo "recorded-correction relocation clause missing"; exit 1; }
# typography and hygiene over the touched set
bash scripts/check-no-em-dash.sh touched
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh"
```

Authoring-time record: the fixer `scripts/fix_plan_em_dashes.py` ran over these bytes before the first write; the em-dash scan, the public-hygiene scan, and `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-16-placement-closing-doctrine-enforcement.md` all ran against this draft; outcomes are recorded in this section's authoring-time record and in the staged review records. Validation greps pin spans prescribed in Tasks 1, 2, and 3 plus two verbatim current-text spans (teardown, transfer-out) and one verbatim dispatch span (maintenance fleet cap); they are RED against today's tree by construction and flip GREEN exactly when those tasks land (rule 19/22 posture; the pins-section grep additionally requires Task 4, so the full block passes only at Task 4's close). The rule 22 mechanical audit (each pinned span occurs exactly once per owning block; `bash -n` over this block) ran at authoring time and passed.

### Task 1: Consolidate the non-worktree policy resolution

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/check_maintenance_pins.sh`

- [x] Rewrite the Project worktree policy paragraph's resolution arms to exactly two spelled values, `worktrees` and `primary`, with the sentence naming `outside the two spelled forms, or an unresolvable root, is treated as unconfigured with a named report, never a silent fallback`. [class: IMPLEMENTATION_REQUIRED]
- [x] Replace the conflict-and-stop arm and the primary-execution authorization with one primary resolution: all run work, ordinary and named lanes including plan authoring and plan execution, happens in the primary checkout on its current branch, serialized by the existing execution-claim rules; personal and pet profiles verify the current branch is the base branch at run start; the company task-branch sub-arm is kept verbatim. [class: IMPLEMENTATION_REQUIRED]
- [x] State the immediate-commit rule inside the primary resolution: under the primary resolution every change is committed right after the change is made by a plain path-limited commit of the session's own paths, and a minutes-scale closeout is acceptable; the done skill runs once at the end of the session's work, so its learn and other closeout steps fire once rather than per change; the rule text carries the literal `immediate-commit rule`. [class: IMPLEMENTATION_REQUIRED]
- [x] Remove every occurrence of the retired value token from both files, including the placement table row and the Phase 0 authorized-primary-placement arm's cross-references in the skill and the corresponding contract line in runtime-contract.md, retargeting each to the primary resolution; the mode-name string inside the done sweep gates lib stays and is recorded as out of scope in Review Scope. [class: IMPLEMENTATION_REQUIRED]
- [x] In the same change retire or rewrite the four stand-down route pins in `scripts/check_maintenance_pins.sh` that pin the removed arm's text (the one-run worktree route pin, the retired-value declaration route pin, the fail-closed no-authorization rule pin, and the step-0.1 two-routes relay pin), replacing them with pins over the consolidated primary resolution's stand-down-relevant sentences so no pin targets removed text. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the transfer-out ordering and migration-before-removal sentence untouched; the primary resolution records that transfer-out is a no-op by construction there, as today. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the three dedicated greps for this task's spans from Validation Commands and record all GREEN in the task log. [class: REPOSITORY_TEST]

Evidence: the policy paragraph spells two values; the retired token has zero matches in the file; the immediate-commit rule sentence sits inside the primary resolution arm; the serialization and company task-branch sub-arms read as today.

### Task 2: Immediate-commit boundary and direct-landing advisory in the done skill

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/done/SKILL.md`

- [x] In the run setup section (Step 0) add the primary-policy arm: on a project resolving the primary resolution, the consult routes every session's work to the primary checkout and the immediate-commit rule applies; each change is committed right after the change is made by a plain path-limited commit, and the done skill runs once at the end of the session's work. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the worker-boundary clause beside it: a subagent or worker reaching its work boundary under the primary resolution returns its learnings and the issues it saw to the parent session in its result, editing no tracked corpus and committing nothing. [class: IMPLEMENTATION_REQUIRED]
- [x] Complete the clause with the parent-run ownership: the parent's single end-of-work run captures those learnings through the learn skill and commits the corpora, and routes issues needing follow-up work through the done boundary's candidate emission or an operator-directed investigate run; the full done closeout (docs-branch persistence, run manifest, done-lock release) belongs to that parent run alone. [class: IMPLEMENTATION_REQUIRED]
- [x] Sharpen the commit-run boundary (Step 3): at the done boundary, dangling session-owned work product (modified, staged-but-uncommitted, or untracked files the session owns) is a named stop listing each path, distinct from the existing foreign-dirt refusal; the session resolves it by committing or explicitly standing down with the list recorded. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the warning-only advisory: a direct landing whose diff exceeds the direct-commit class bounds (a behavior, API, or schema change, or more than four files) prints a named advisory citing the class and the worktree lane; it never blocks the landing. [class: IMPLEMENTATION_REQUIRED]
- [x] Cite each incident in one line beside its new text per the standing anti-growth constraint; no dossier text enters the skill. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the four dedicated greps for this task's spans from Validation Commands and record all four GREEN in the task log. [class: REPOSITORY_TEST]

Evidence: the three prescribed spans match exactly once each in the file; the advisory carries no exit-code change; the anti-growth one-line citations are present and no incident narrative entered the skill body.

### Task 3: Recorded-correction relocation clause

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/plans/SKILL.md`

- [x] Extend the existing recorded-correction sentence in the review boundary with the relocation-digest correction case: mechanical hash or reference corrections caused by moving changed files (a worktree relocation or a squash landing changing commit ids) ride the same zero-round re-bind when every hunk is mechanical, carried as a verified corrections-chain entry that names the moved paths and the pre- and post-move digests. [class: IMPLEMENTATION_REQUIRED]
- [x] State the clause's boundary: the corrections chain covers reference and digest corrections only; a plan-file rename after certification keeps its fail-closed shape (revert the rename or re-certify), and an unrecorded drift keeps its unwitnessed-mutation refusal, so downstream gates never read a recorded relocation as broken or incomplete reviews. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the relocation-span grep from Validation Commands and record GREEN in the task log. [class: REPOSITORY_TEST]

Evidence: the recorded-correction sentence carries exactly one added clause naming the relocation-digest correction; no other review-boundary sentence changed. Deviation (2026-10-16, operator-directed honest reword after executed probes): the landed clause conditions the zero-round re-bind on classifier-exempt hunks and routes unclassified mechanical substitutions to a fresh round until a sanctioned route lands; witness docs/history/backlog/2026-10-16-corrections-chain-unclassified-mechanical-hops.md.

### Task 4: Placement pin guard in the pins checker

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `check_maintenance_pins` in `scripts/check_maintenance_pins.sh`

- [x] Add a placement-pins section pinning the Validation Commands' spans over the placement-decision owners: the two-spelled-forms enum, the primary resolution's commit-cadence span, the done skill's commit-cadence, worker-boundary, dangling-change, and advisory spans, the teardown and transfer-out spans, the maintenance dispatch-isolation span, and the plans skill's Task 3 span; one dedicated grep per span, each failing when that span is absent. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the section warning-only: it appends its result line to the checker's existing summary posture and never moves the exit code; the summary line reads `placement pins: all hold` when every pin matches and names the first missing span when one does not. [class: IMPLEMENTATION_REQUIRED]
- [x] RED-today witness: remove one pinned span from a working-tree copy of a placement-owning skill file, run the checker, record that the section names the missing span, restore the file, and record both runs in the task log; perform this before the section's own GREEN run. [class: REPOSITORY_TEST]
- [x] Record the admission fields beside the section in one comment line: the incident, catch frequency, false-positive cost, and the first-true-catch sunset. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full Validation Commands block and record its first failing gate plus each GREEN gate in the task log. [class: REPOSITORY_TEST]

Evidence: the pins section reports `placement pins: all hold` on the landed tree; the RED-today run is recorded with the named span; the checker's exit-code posture for pre-existing sections is unchanged; Task 1's rewritten stand-down pins coexist with the new section.
