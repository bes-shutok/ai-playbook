# The authoring self-landing recipe runs the duplicate-origin coverage gate before the landing commit

[github: https://github.com/admitriev/ai-playbook] Backlog origin: `docs/history/backlog/2026-10-01-self-landing-recipe-must-run-coverage-gate.md`
Driving force: reliability

## Gist TLDR

TLDR: add three sentences to the authoring blueprint's self-landing paragraph in `agents/skills/maintenance/prompt-templates.md` so the dispatched authoring child runs the plans lifecycle's duplicate-origin coverage hard gate before acquiring the landing lock, and runs `--mark-covered` in its worktree afterward so each named open origin's covered flip becomes one of the task's changed files and rides the landing commit - closing the witnessed gap where a second plan for an already-covered origin landed because the operational recipe never invoked the gate the lifecycle mandates.

Witnessed 2026-09-30 23:58: the duplicate plan `1d7ee68b` (origin ideas B+D) landed twenty-five minutes after the covering plan `5138a9fc` (same origin, ideas B+D+E); the gate detects the conflict on the same bytes today (exit 1, first-landed-wins remedy), so the landing flow that produced the duplicate never ran it. The lifecycle hard gate (plans SKILL.md, "Landing closeout - origin coverage and duplicate-origin refusal") owns the rule; the recipe the dispatched sessions follow step by step is the gap.

## Outcome + Gate delta

A dispatched authoring child whose plan names an already-covered origin refuses before acquiring any lock (worktree and branch kept, claim ensured deleted, the covering plan and remedy reported), and a clean landing carries the covered flip of its named origins in the landing commit itself, so the survey's covered-skip and the execution-side coverage guard see the flip without a manual follow-up.

Gate delta: three sentences added to one paragraph in `agents/skills/maintenance/prompt-templates.md` (the authoring blueprint's self-landing paragraph, between the done-skill sentence and the review-migration sentence); no script, hook, refusal class, hard gate, fence, or protocol layer is added - the sentences invoke the lifecycle's existing gate and marker modes.

## Terms

- **Coverage gate**: `check_plan_origins_closed.py --check-coverage <plan path>`, the lifecycle's duplicate-origin refusal (non-zero exit = refuse the landing, naming the covering plan and the first-landed-wins remedy).
- **Covered flip**: `check_plan_origins_closed.py --mark-covered <plan path>` flipping each named open origin's `Status:` to covered with the covering-plan witness, so surveys skip the origin and the landing commit carries the flip.

## Assumptions

- assume the gate runs against the primary checkout's plans directory with the authored plan's own path (absolute worktree path for the plan argument, `--repo-root` anchored at the primary checkout), because the authoring worktree branched before the covering plan landed and its own plans directory cannot see the conflict; basis: the witnessed incident's worktree (`orphan-manifest-disposition-20260930`) was created before the covering plan landed, and the conflict scan reads the active plans directory the `--repo-root` resolves.
- assume the covered flip runs in the authoring worktree (the default `--repo-root`), making the flipped origin item an uncommitted change of the task, so the recipe's existing copy-then-pathspec-commit machinery carries it with no pathspec surgery; basis: the recipe's copy step copies exactly the task's changed files, and a worktree-local flip is by construction one of them.
- assume the refusal shape reuses the paragraph's existing pre-commit failure family (keep worktree and branch, ensure this session's claim file is deleted per the AUTHORING CLAIM DUTY (the closeout deletion has normally already removed it), report the stranding) with no lock release clause, because the gate runs before the lock is acquired; basis: the paragraph's own failure-duty ordering.
- assume no other operational landing recipe needs the mirror: the execution blueprint's landing is the done skill's own closeout path, which the lifecycle's execution-side wiring (execute-plan Step 0.5's coverage gate) already gates; basis: the origin's Proposal item 2 names the mirror as optional and the execution-side wiring exists on main.
- assume the pins suite stays green with three additive sentences inside the blueprint paragraph: the suite pins spans and literals elsewhere in the file (the landing lock acquire literal, the claims directories, the facts-file transfer-in), none of which the insertion touches; basis: the pins suite's pin inventory (span pins on the re-arm duty, the fire-time gate, the worktree references) and rule 41's sweep, which the Validation Commands run.

Decision points requiring a grill: none remain.

### Task 1 - Three sentences in the authoring blueprint's self-landing paragraph

- [x] In `agents/skills/maintenance/prompt-templates.md`, the authoring blueprint's self-landing paragraph: insert three sentences between the done-skill sentence (insertion anchor: the literal `stop there and do not run execute-plan.`, present on main at authoring time; re-derive exact bytes from the worktree before the edit) and the review-migration sentence that follows it (anchor: the literal `If this session runs in an ad-hoc worktree, then before the done skill runs`), so the gate runs after the done skill completes and before the landing machinery starts. Sentence one: `Before acquiring the merge landing lock, run the plans lifecycle's duplicate-origin coverage gate against the primary checkout's plans directory (python3 <primary-root>/scripts/check_plan_origins_closed.py --check-coverage <authored-plan-abs-path> --repo-root <primary-root>; the worktree's own plans directory cannot see a covering plan that landed after this branch was created): a non-zero exit is a refused landing - keep the worktree and branch, ensure this session's claim file is deleted (the AUTHORING CLAIM DUTY's closeout deletion has normally already removed it), and report the stranding naming the covering plan and the first-landed-wins remedy (no lock was acquired; nothing to release).` Sentence two: `After the gate passes, run python3 scripts/check_plan_origins_closed.py --mark-covered <repo-relative plan path> from the authoring worktree, so each named open origin's covered flip (the lifecycle's landing closeout) becomes one of this task's changed files and rides the landing commit with the covering-plan witness: the flipped origin item file is one of this task's changed files for the landing copy below even though the done skill's commit predates the flip, and a non-zero exit from the marker itself is the same refused landing as the gate's (keep the worktree and branch, the claim duty, report the covering plan).` Sentence three: `The gate re-runs once immediately before the commit or the compare-and-swap ref update inside the critical section against the same primary-anchored invocation (a covering landing in the gate-to-commit window is the witnessed incident class): a non-zero exit there takes the paragraph's pre-commit failure path - revert the copy, release via merge-release-repo with the acquired exports, keep the worktree and branch, and report the covering plan.` [class: IMPLEMENTATION_REQUIRED]

### Task 2 - Validation

- [x] Run every Validation Command below from the worktree root; each must pass against the amended tree. [class: REPOSITORY_TEST]
- [x] Run the rule 22 mechanical audit over this plan: extract each pinned span below and verify it occurs exactly once in the task text that prescribes it; run `bash -n` over the extracted Validation Commands block (span-joined extraction of the numbered command lines); fix both sides of any mismatch in the same edit. [class: REPOSITORY_TEST]

## Evaluation Criteria

- A dispatched authoring child whose plan names an already-covered origin refuses before the landing lock, reporting the covering plan and remedy, with the worktree and branch kept for reconciliation.
- A clean self-landing carries the covered flip of its named origins in the landing commit, so no manual follow-up marks the origin covered.
- The pins suite stays green: the insertion is additive between pinned spans, and no pinned literal moves.

## Review Scope

Editable regions: `agents/skills/maintenance/prompt-templates.md` (the authoring blueprint's self-landing paragraph, the span between the done-skill sentence and the review-migration sentence).

Read-only: `agents/skills/plans/SKILL.md` (the lifecycle hard gate this plan invokes); `scripts/check_plan_origins_closed.py`; `scripts/check_maintenance_pins.sh` (a consumer, run but not edited); `agents/skills/execute-plan/SKILL.md`; every other file.

## Origins dispositions

The origin stays in place at the backlog top level while this plan is open; execution folds it per the Plan Lifecycle.

## Validation Commands

Run from the worktree root; every check fails closed (a miss or an error aborts non-zero). Baselines derived from main at authoring time 2026-10-01 (commit 505ff1b5); re-derive any drifted baseline at execution per the provenance rule before trusting a pass. Authoring-time record (rule 29): the em-dash `touched` scan over the plan bytes passed, the public-hygiene scan passed, `plan_readiness.py --pre-round` passed, and the pins suite passed on the unamended tree. Rule 19 RED-today evidence, verified 2026-10-01 against the worktree's main bytes: commands 1, 2, 3, 4, 5, 10, 11's pins are absent from prompt-templates.md (grep rc 1; the pinned sentences do not exist on main), and command 6's lifecycle-gate literal is present exactly once (green today; a regression guard). Rule 22 authoring-time mechanical audit: each pinned span occurs in Task 1's prescribing text exactly once (the gate sentence, the marker sentence, the refusal shape, the flip-carriage clause, the critical-section re-check, the marker exit duty).

1. `grep -q "duplicate-origin coverage gate against the primary checkout's plans directory" agents/skills/maintenance/prompt-templates.md || { echo FAIL: gate sentence missing; exit 1; }` and `test "$(grep -oF "duplicate-origin coverage gate against the primary checkout's plans directory" agents/skills/maintenance/prompt-templates.md | wc -l)" -eq 1 || { echo FAIL: gate sentence duplicated; exit 1; }` - the gate sentence exists exactly once (occurrence form per rule 33; zero hits on main at authoring time).
2. `grep -q -- "--check-coverage <authored-plan-abs-path> --repo-root <primary-root>" agents/skills/maintenance/prompt-templates.md || { echo FAIL: gate invocation missing; exit 1; }` - the gate's invocation form is pinned with the primary-anchored repository root.
3. `grep -q -- "--mark-covered <repo-relative plan path> from the authoring worktree" agents/skills/maintenance/prompt-templates.md || { echo FAIL: marker sentence missing; exit 1; }` and `test "$(grep -oF -- "--mark-covered <repo-relative plan path> from the authoring worktree" agents/skills/maintenance/prompt-templates.md | wc -l)" -eq 1 || { echo FAIL: marker sentence duplicated; exit 1; }` - the covered-flip sentence exists exactly once (zero hits on main at authoring time).
4. `grep -q "no lock was acquired; nothing to release" agents/skills/maintenance/prompt-templates.md || { echo FAIL: refusal shape missing; exit 1; }` - the refusal's pre-lock shape is pinned (no release clause before acquisition).
5. `grep -q "rides the landing commit with the covering-plan witness" agents/skills/maintenance/prompt-templates.md || { echo FAIL: flip carriage missing; exit 1; }` - the flip-rides-the-commit duty is pinned.
6. `grep -q "Landing closeout - origin coverage and duplicate-origin refusal (hard gate):" agents/skills/plans/SKILL.md || { echo FAIL: lifecycle gate gone; exit 1; }` - the lifecycle hard gate this plan invokes still exists (green on main at authoring time; a regression guard).
7. `bash scripts/check_maintenance_pins.sh || { echo FAIL: maintenance pins broken; exit 1; }` - the pins suite stays green with the three additive sentences (rule 41's sweep over the touched literals).
8. `bash scripts/check-no-em-dash.sh added-lines --base main agents/skills/maintenance/prompt-templates.md || { echo FAIL: em dash in added lines; exit 1; }` - the added-lines gate passes over the edited file against the committed baseline.
9. Run the public-hygiene scan from the user facts document's `public_hygiene_scan_script` key over the repository; exit 0 required.
10. `grep -q "The gate re-runs once immediately before the commit or the compare-and-swap ref update inside the critical section" agents/skills/maintenance/prompt-templates.md || { echo FAIL: critical-section recheck missing; exit 1; }` - the race-window re-check is pinned (zero hits on main at authoring time).
11. `grep -q "even though the done skill's commit predates the flip" agents/skills/maintenance/prompt-templates.md || { echo FAIL: flip carriage clause missing; exit 1; }` and `grep -q "a non-zero exit from the marker itself is the same refused landing as the gate's" agents/skills/maintenance/prompt-templates.md || { echo FAIL: marker exit duty missing; exit 1; }` - the carriage clause and the marker's fail-closed exit duty are pinned (zero hits on main at authoring time).
