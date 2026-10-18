# Plan: company execute-plan runs choose their task branch

Backlog origins (scope of record):
- docs/history/backlog/2026-10-12-execute-plan-operator-selected-start-branch.md

Driving force: operator control (primary) + continuity (secondary)

Plan review record: the staging series {reviews_dir}/2026-10-13-plan-review-execute-plan-company-task-branch-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

Execution budget: 3h total, largest task 1.5h

## Terms

- `primary-execution placement`: the declared project mode (`worktree_policy = "primary-execution"`) authorizing the plan-execution lane to run in the primary checkout, serialized, instead of an ad-hoc worktree.
- `base branch`: the confirmed `base_branch` fact; today it is both the required checkout branch for a primary-placement run and the landing target.
- `task branch`: the branch a company primary-placement run commits its tasks to under this plan: the operator keeps the current branch or names a new branch created from the current HEAD; it receives the per-task commits and stays available as the source of a later GitHub PR.
- `PR target`: `base_branch` in its preserved role: the branch a later PR merges into; the run never integrates onto it.
- `start commit`: the commit the task branch pointed at when the run started, recorded so resume and review scope bind to the recorded state.
- `company profile`: the project profile class the bootstrap skill's interview records; personal and pet profiles are the untouched comparison classes.

## Why

A company primary-placement run today refuses to start unless the shared checkout sits on `base_branch`, forcing the operator off the branch that carries the plan and its prerequisite context, and conflating the branch tasks commit to with the branch a PR later targets.

## Gist & Examples

TLDR: company primary-placement runs gain a per-run operator choice to keep the current branch or create a named task branch from HEAD, with the choice bound into the claim and manifest and `base_branch` preserved as the PR target, so company work continues on its own branch without retargeting anything (operator control).

Before (today): the operator is on a feature branch holding the plan and its prerequisites; the placement gate refuses (only the base branch is valid), the stand-down remedy says check out the base branch or take the worktree lane, and the plan may not exist on the base at all - the witnessed 2026-10-12 stop.

After (this plan): on a company project the operator chooses keep-current or create-a-task-branch-from-HEAD; the recorded branch and start commit go into the execution claim and the manifest identity block; per-task commits land on that task branch; the run records no landing and its record names the PR pairing (task branch as source, `base_branch` as target); a resume on any other branch stands down exactly as today. A personal or pet project's primary-placement run still requires the base branch byte-identically.

Edge cases: the chosen task-branch name already exists and carries foreign work (refuse, ask again); the checkout is dirty at start (branch creation carries the working-tree state over as any checkout would; the worker-layer dirty gates and the stale-checkout discriminator are untouched); a resume finds the shared checkout on a different branch than recorded (stand down naming the recorded branch, never switch); `base_branch` unresolvable (the existing stand-down stands); the operator names the base branch itself as the task branch (that is the keep-base form and stays valid); a non-company project request for the choice (unavailable - the arm is company-profile-only).

## Outcome

A company primary-placement run continues on the operator's branch and leaves it PR-ready, without touching the confirmed base or personal and pet behavior.

- The placement arm admits a recorded task branch for company profiles and keeps the base-branch-only rule for personal and pet profiles.
- The claim and manifest carry the task branch and start commit, so resume and review scope bind to the recorded state instead of the checkout's live state.
- The run records no landing and names the PR pairing; every existing serialization, base-immutability, and primary-checkout-landing prohibition is unchanged.

Gate delta: no new gate, refusal class, fence, protocol layer, validator, ledger, or round. One existing placement arm (the primary-execution base-branch-only validity sentence) is narrowed to personal and pet profiles with a company-profile alternative arm added beside it, priced by the origin's witnessed stop (a requested run could not start without abandoning its own context branch); the claim file's recorded surface grows by two lines (`branch:` written when `--branch` is passed, `start-commit:` beside it - the claim file carries neither today), recorded in existing claim and manifest records with no new record type; two pins are added to the existing pins suite. No refusal is removed: the personal and pet validity rule, the resume mismatch stand-down, the serialization refusal, and the primary-checkout landing prohibition all stand.

## Assumptions

- assume a per-run choice, not a persistent setting: the origin's suggested direction prefers the per-run form and the witnessed need is a single continuation, so the bootstrap profile interview gains no new key and `worktree_policy` gains no new value; basis: the origin's Suggested direction and Alternatives (a persistent start-ref setting is explicitly listed for rejection in the dispatch entry).
- assume the plan touches skill text plus the claim script only: the placement checks live in the Worktree-first standard's primary-execution sentences and the Base-branch resolution rule (both in `agents/skills/execute-plan/SKILL.md`), and the claim records through `scripts/execution_claim.sh` (which already carries `--branch` on the claim form as occupancy evidence); no runtime-python change is needed because `scripts/execute_plan_runtime.py` holds no base-branch or placement logic; basis: greps of both surfaces at the 2026-10-13 tip.
- assume review scope binds to the recorded start commit by a placement-arm clause rather than a new review-side rule: the task-branch arm's reviews diff the recorded start commit, stated once in the placement arm this plan edits (single-homed, per the repository's single-sourcing rule); basis: the shared-state trace discipline and the absence of an existing exec-side review diff-base key to extend.
- assume the base-branch resolution rule's landing sentence needs only a carve-out clause: the confirmed base still governs worktree creation and every worktree-lane landing; the task-branch arm simply records no landing (the primary-placement class's existing no-landing shape), so the sentence gains a company task-branch clause instead of a rewrite; basis: the arm text at the tip and the origin's completion requirement (leave the branch PR-ready).

Decision points requiring a grill: none remain.

## Standing constraints

- Personal and pet profile behavior is byte-unchanged: every personal and pet sentence in the touched regions keeps its exact text; the company arm is added beside them, never instead of them.
- Plan scripts and validators run under `python3` (3.14); commands stay repo-relative with no machine-specific absolute paths; committed text carries no em-dashes.
- The pins suite carries 21 pre-existing peer-owned maintenance-skill failures red at the 2026-10-13 base tip; the pins criterion here is scoped to touched spans and the new rows, never a whole-suite green.
- Every existing pin whose expected span lives in the touched regions (the take-invocation pins at `scripts/check_maintenance_pins.sh` lines 2638-2639 and the placement pins) must stay green; the take invocation string is untouched by this plan.

## Evaluation Criteria

**Quality dimensions:**
- correctness: a company run on a feature branch starts, records, resumes, and stands down exactly as the clauses specify; a personal or pet run's behavior is provably unchanged (the untouched sentences quoted verbatim in the task evidence).
- continuity: the recorded branch and start commit are the only identity a resume trusts; no clause consults the checkout's live branch over the recorded one.
- minimalism: two skill regions and one script option; no new mode, key, value, validator, or record type.

**Done when:**
- the three touched surfaces carry the clauses with the origin witnessed in each.
- the claim fixture exercises claim/refresh/release with `--branch` and `--start-commit`, including the takeover-recreate rebuild carrying both lines.
- `test_execution_claim.py` passes and the scoped pins pass.

**Ship when:**
- landed on main with its dispatch entry pruned by the landing rider per the log's prune rule and the origin row closed through the existing lifecycle.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md` (the Worktree-first standard's primary-execution arm and every other base-branch-only placement site, lifecycle steps 1 and 3, the Phase 0 arm and hard gate, the run-setup summary, the Base-branch resolution rule)
- `scripts/execution_claim.sh` (the claim/refresh option surface and claim-file lines)

**Tests:**
- `scripts/test_execution_claim.py` (new cases for --start-commit and the recorded task-branch shape)
- `scripts/check_maintenance_pins.sh` (the two new pin rows and the touched-span pins this plan must keep green)

**Documentation (claim-record prose owner):**
- `agents/skills/maintenance/template-execution.md` (the EXECUTION CLAIM paragraph's line inventory, Task 2)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. The landing's own riders ride the landing branch per the log charter. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/bootstrap-ai-playbook/SKILL.md`; reason: no persistent setting is admitted (Assumption 1), so the profile interview is untouched.
- The worktree lane and its landing path; reason: `base_branch` keeps governing worktree creation and worktree-lane landings unchanged.
- `scripts/land_squash.sh` and the landing critical sections; reason: the task-branch arm records no landing, so no landing code changes.
- Personal and pet placement behavior; reason: byte-unchanged by standing constraint; findings there are pre-existing and out of scope.

## Validation Commands

```bash
python3 -m pytest scripts/test_execution_claim.py -q
bash scripts/check_maintenance_pins.sh
python3 scripts/skill_text_budget.py --check
python3 scripts/fix_plan_em_dashes.py agents/skills/execute-plan/SKILL.md
python3 scripts/fix_plan_em_dashes.py scripts/execution_claim.sh
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh --files scripts/execution_claim.sh
```

The pins suite carries the 21 pre-existing peer-owned failures noted in the standing constraints; the em-dash fence operands are both edited files (a nonzero substitution count on either before commit is a task failure); the suite is pytest-collected (run under an interpreter whose environment provides pytest).

### Task 1: The placement arm admits a recorded company task branch

Files:
- agents/skills/execute-plan/SKILL.md

- [x] Rewrite the primary-execution validity sentences in the Worktree-first standard's placement paragraph: the base-branch-only validity rule stays for personal and pet profiles verbatim; the company-profile arm gains the per-run operator choice - keep the current branch or create a named task branch from the current HEAD (a name colliding with an existing branch carrying foreign work refuses and re-asks; naming the base branch itself is the valid keep-base form). [class: IMPLEMENTATION_REQUIRED]
- [x] Carry the same carve-out through three more base-branch-only sites so the operative path is consistent: Phase 0 Step 0.1's authorized primary-placement arm (the verify-current-branch sentence, around line 362), lifecycle step 3's run-work sentence (around line 210), and the Phase 0 hard gate's primary-placement sentence (around line 364); the recorded task branch satisfies the placement check for a company run, and the personal and pet forms stay verbatim. [class: IMPLEMENTATION_REQUIRED]
- [x] Carry the carve-out through the remaining three sites: the run-setup summary in the sequential overview (around line 967) and the Execution claim registration paragraph's claim copy (around line 409) get the same recorded-task-branch alternative. [class: IMPLEMENTATION_REQUIRED]
- [x] Repair the claim-registration site's stale procedure-of-record pointer: it names agents/skills/maintenance/prompt-templates.md, an eleven-line stub, as the owner of the claim-file inventory, while the EXECUTION CLAIM paragraph and the inventory live in agents/skills/maintenance/template-execution.md. [class: IMPLEMENTATION_REQUIRED]
- [x] Bind the choice like the existing recorded-branch sentence binds it today: the recorded task branch goes into the execution claim and the manifest identity block, a resume finding the shared checkout on any other branch stands down naming the recorded branch, and no clause ever switches the shared checkout's branch. [class: IMPLEMENTATION_REQUIRED]
- [x] State the capture mechanism: the choice comes from the operator's run directive (keep-current named explicitly, or the task-branch name given); an unattended run with no directive keeps the current branch by default and records that default, so a scheduled company lane never stalls on an ask. [class: IMPLEMENTATION_REQUIRED]
- [x] In the same arm, replace the per-task-commit and landing consequences for the company task-branch arm: per-task commits land on the recorded task branch, the run records no landing (the primary-placement class's existing no-landing shape), and the run record names the PR pairing (the task branch as source, the confirmed base as target) so completion leaves the branch PR-ready. [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the lifecycle step 1 primary sentence with the matching recording step (record the chosen or created task branch and the start commit with the claim invocation), and state the dirty-checkout behavior: branch creation carries the working-tree state over, with the worker-layer dirty gates and the stale-checkout discriminator untouched. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the carve-out clause to the Base-branch resolution rule: the confirmed base still governs worktree creation and every worktree-lane landing, and a company task-branch run records no landing, so nothing integrates onto the confirmed base during the run; the review scope clause for the task-branch arm diffs the recorded start commit, stated in this placement arm as the single home. [class: IMPLEMENTATION_REQUIRED]
- [x] Record in the task completion evidence the personal-and-pet invariance check: quote the untouched personal and pet sentences verbatim and confirm the company clauses are additive beside them (the claim-to-task ownership sweep applied to this plan's own claim sections). [class: REPOSITORY_TEST]

Evidence: the three regions read as one contract; no personal or pet sentence changed; the take-invocation pins' expected string is untouched; the budget gate reports no new advisory line for the file.

### Task 2: The claim records the task branch and start commit

Files:
- scripts/execution_claim.sh
- scripts/test_execution_claim.py
- agents/skills/maintenance/template-execution.md

- [x] Make the claim form write a `branch:` line when `--branch` is passed: today the claim file carries exactly the session, plan, created, and updated lines plus an optional `base:` line, so this is a new line, not a kept one; the takeover and refresh-recreate rebuild path (create_claim_noclobber) writes the same lines, so the rebuild must carry `branch:` and `start-commit:` too, or a resume takeover silently drops the recorded identity. [class: IMPLEMENTATION_REQUIRED]
- [x] Add an optional `--start-commit <sha>` to the claim and refresh forms: the value must resolve to an existing commit (`git rev-parse --verify --quiet <sha>^{commit}`), is recorded as a `start-commit:` line in the claim file, and is preserved by refresh and by the recreate path. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the script profile-blind - a task branch under a non-company profile is the placement arm's concern, not the script's - and keep the take mode's occupancy-evidence behavior untouched. [class: IMPLEMENTATION_REQUIRED]
- [x] Update the usage text for the new option and extend `scripts/test_execution_claim.py`: a claim with `--branch` and `--start-commit` writes both lines; an unresolvable `--start-commit` is a usage refusal writing nothing; refresh and the recreate path preserve both lines; release refuses a foreign claim; the suite stays green. Script tests cover the claim file only: the branch-mismatch stand-down is placement-arm behavior with no script witness. [class: REPOSITORY_TEST]
- [x] Update the claim-record prose owner: the EXECUTION CLAIM paragraph in agents/skills/maintenance/template-execution.md owns the claim file's line inventory (today it names the four frontmatter lines and the fifth base line); carry the new branch and start-commit lines into that inventory so the prose owner matches the file. [class: IMPLEMENTATION_REQUIRED]

Evidence: the pytest suite green; a live claim/refresh/release cycle in a temp fixture carries both lines end to end; no existing pin on the script breaks.

### Task 3: Pin the new clauses

Files:
- scripts/check_maintenance_pins.sh

- [x] Add exactly two pins beside the existing execute-plan pins: one pinning the placement arm's company task-branch choice clause (a distinctive multi-word fragment verified unique in the skill file), one pinning the PR-pairing consequence clause (same distinctiveness bar); each pin carries a provenance comment naming this plan. [class: IMPLEMENTATION_REQUIRED]

Evidence: the two new pins pass; no pin whose span this plan touched fails; the pre-existing peer-owned baseline red is recorded, never repaired.

## Rejected alternatives

- Require switching to `base_branch` before execution: rejected because the observed plan and prerequisite history were on the current feature branch, while the configured PR target lacked the plan (witnessed: docs/history/backlog/2026-10-12-execute-plan-operator-selected-start-branch.md).
- Change `base_branch` to the selected feature branch: rejected because that would retarget the PR destination instead of preserving it (witnessed: agents/skills/execute-plan/SKILL.md, Base-branch resolution rule).
- Keep current-branch commits but add a separate squash landing into `base_branch`: rejected because the operator clarified that company work should remain on a task branch for the normal GitHub PR workflow; separate integration is unnecessary for that path (witnessed: docs/history/backlog/2026-10-12-execute-plan-operator-selected-start-branch.md).
- Add a persistent start-ref setting before establishing whether the choice is stable: rejected because the observed need is a per-run branch continuation, and the existing base-branch setting already names the PR target (witnessed: agents/skills/bootstrap-ai-playbook/SKILL.md).
- Remove `primary-execution` serialization and branch checks wholesale: rejected because the current contract protects shared-checkout serialization and resume identity; this plan adapts branch identity while retaining those protections (witnessed: agents/skills/execute-plan/SKILL.md).
- Extend the choice to personal and pet profiles in the same change: rejected because no witnessed incident asks for it there and the entry orders personal and pet behavior unchanged (witnessed: docs/history/backlog/2026-10-12-execute-plan-operator-selected-start-branch.md).
- Record the task branch in the manifest only, skipping the claim: rejected because resume adjudicates through the claim first and the manifest identity block second; a claim without the recorded branch would let a resume adopt the wrong checkout state (witnessed: the placement arm's recorded-branch resume sentence).
