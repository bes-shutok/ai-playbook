# Plan: stacked PR review size policy

Executed: yes (6a8a10efb2cefe753f3206698cef01ca10e91b8b)

Backlog origins (scope of record):
- docs/history/backlog/2026-11-05-stacked-pr-review-size-policy.md
Driving force: code-quality (primary), efficiency (secondary)
Plan review record: the staging series {reviews_dir}/2026-11-05-plan-review-stacked-pr-review-size-policy-p<identity-token>-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2h total, largest task 1h
Authoring claim: stacked-pr-review-size-policy.md (session sess_2ef2f7d4-cfc2-4dac-8d4b-fde95273bf35)

## Terms

- PR-size policy: the target repository's authoritative changed-line standard for a reviewable PR: a normal target, a hard maximum, and the file classes excluded from the count, resolved from applicable company/repository guidance and target facts.
- Immediate PR base: the predecessor branch a stacked task's draft PR targets; the measurement base for that task's delta, never the trunk or the cumulative stack diff.
- Changed-line measure: additions plus deletions across the files a policy counts, computed from the final tree diff against the immediate PR base.
- Normal target: the advisory per-PR ceiling, resolved as the stricter of the 450-line stack target, configured target and applicable policy target, preserving source inclusivity. Above it a slice needs a split or recorded rationale. Tests and documentation are excluded by default.
- PR-description standard: the minimum description shape every PR carries: What (summary of the change), Why (the problem or requirement solved), How (the approach and notable design decisions), Testing (how the change was verified), and Notes for reviewers (attention areas, known limitations, follow-ups); a reviewer understands the intent before reading any code.
- Hard maximum: the policy's absolute per-PR ceiling; a slice above it is split before the draft PR is created.
- Policy exclusions: file classes the policy removes from the count (typically tests and documentation), named as path-classification rules in the policy configuration.
- Split-or-rationale disposition: the required record when a measured slice sits between the normal target and the hard maximum: either split the slice further, or the draft PR description states why the work cannot be split, recorded in the description's Notes for reviewers section.
- Policy disposition: the outcome of applying the policy to one measured slice: under target, over target with rationale, or over hard maximum requiring a split.

## Why

A completed stack produced a 577-line production and API-contract delta against its PR base while the target standard targets fewer than 500 production lines and requires an explanation between 500 and 1,000; neither the stack plan nor the execution measured the slice or captured a rationale, so the oversized PR reached review unexplained. The shared stack skills budget tasks by ownership and buildability only, and no shared surface resolves a target repository's line-size policy.

## Gist & Examples

TLDR: stack planning budgets each slice against the target repository's PR-size policy, stack execution measures each task's delta against its immediate PR base and requires the standard What/Why/How/Testing/Notes description before creating the draft PR, so over-target slices are split or carry their rationale inside a description a reviewer can read before any code.

Before (today): a stack task is sliced by file ownership and buildable boundaries; execution creates the draft PR against the immediate predecessor without measuring anything; the 577-line slice ships as a draft whose description says nothing about size; the only size machinery anywhere is a file-count split guide that never resolves a repository's line policy.

After (this plan): the authoring contract budgets each planned slice against the policy's normal target (advisory, split oversized slices at planning when clean boundaries exist); at draft-PR time the run measures the task's changed-line count against the immediate PR base under the policy's exclusions, and applies the policy disposition: under target proceeds, between target and hard maximum requires the split-or-rationale disposition in the PR description, above the hard maximum splits before the draft PR is created; the measurement and disposition land in the session log beside the existing per-task records.

Example: a planned slice budgets 300 lines (under the 450-line stack target) and executes at 577 measured against its predecessor base; the disposition requires the draft PR description to state why the slice cannot be split further (one coupled contract migration), which the reviewer reads at review time instead of discovering the size after approval.

Edge cases: no applicable policy or facts settings means the portable default applies (normal target 450 changed lines excluding tests and documentation, no hard-maximum band); an above-hard-maximum slice (possible only under a configured policy) stops before any draft PR exists and routes the split back to planning, even when the original plan under-budgeted it; a predecessor base that is itself an unmerged stacked branch measures only that task's delta, never the stack's cumulative diff; excluded classes follow the configured policy when present, otherwise the default's tests-and-documentation exclusion; a description whose sections cannot be filled honestly (for example Testing with no verification run) says so in that section rather than omitting it.

## Outcome

Stacked PRs reach review at or under the target repository's review-size policy, or carry the policy's required rationale, with the measurement recorded per task.

- A planned stack budgets its slices against the target policy before execution starts.
- Each draft PR's delta is measured against its immediate base with the policy's exclusions applied.
- An over-target slice either splits or records its split rationale in the PR description.
- The measurement and disposition are part of the session log's per-task record.
- Applicable company/repository restrictions apply by default even without numeric facts; overrides cannot weaken them.
- An optional documentation-only first or last PR keeps disjoint ownership, honest descriptions and ordinary validation duties.
- Gate delta: replace file-count sizing checks (target fewer than 10 non-doc files, hard maximum 15, and even-size mandate) with the source-governed PR-size disposition at the existing pre-creation boundary. Its unresolved-policy and above-maximum outcomes withhold PR creation. Witness: the origin Evidence records a completed 577-line draft with required rationale missing, a wrong persisted PR description, not a prevented failure. No validator, lock, registry or separate ceremony is added. Current liveness ledger ratio: 30 catches to 48 incidents (2026-11-05).

## Assumptions

- Resolve applicable company/repository guidance before facts settings or fallback; missing numeric facts never disable that guidance. Facts refine its limits and exclusions without weakening restrictions. The current user request sets the stack target to 450; effective targets use the stricter configured or applicable policy value and permits an optional documentation-only first or last slice. The supplied company ground rules version 3 was read through the connected service; private provenance and boundary examples stay in the run log.
- assume every PR carries the PR-description standard's five labeled sections; basis: the operator direction of 2026-11-05 (this session) supplied the standard verbatim and github-pr-workflow already owns PR-description authoring rules, so the standard lands inside the existing "PR Descriptions and Stats" rules with their omit-verification bullet amended into the same single rule, and the stacked draft-PR step consumes the standard by pointer.
- assume the shared lookup and measurement semantics live in github-pr-workflow, consumed by pointer from the stack skills; basis: the origin row assigns "the shared policy lookup and GitHub mechanics" there and its dedup probe found that skill already owns PR splitting mechanics; execute-plan-stack already carries a facts-resolved Configuration section and github-pr-workflow gains the policy section, while plan-stack carries no configuration surface and consumes the policy by pointer only, keeping the lookup single-homed.
- assume the final measure is the actual PR-base delta, and planning estimates stay advisory; basis: the origin row's Expected states this directly.
- assume no new validator, registry, or ledger lands on this single witness; basis: the origin row's own machinery bar and the repository Machinery admission protocol.

Decision points requiring a grill: none. Current user direction sets 450 production changed lines, mandatory applicable company restrictions by default, and an optional documentation-only first or last slice.
Scope extensions (grilled): none proposed.
Sources inspected: supplied company Engineering Ground Rules, version 3. Private source locator, policy boundaries and restrictions are recorded in the run log.

## Standing constraints

- No organizational values in shared skill text: no organization-specific threshold or file-classification value lands in shared skill text; the single portable default (450 normal target, tests and documentation excluded) is the stated fallback that the target repository's policy configuration overrides, and skill text names keys and fallback behavior only.
- Preserve the stack contract: independent task slices, predecessor-base targeting, draft-first PRs, per-task validation evidence, and the end-of-stack record set are unchanged; this plan adds a measurement and a disposition to the existing steps.
- Machinery admission: apply authoritative restrictions by default, as explicitly requested on 2026-11-05. The origin Evidence is the completed wrong-description witness; catch frequency is unknown beyond that one failure. False-positive cost is one human policy clarification or replanning round. Review this prose duty by 2027-02-05; remove the old file-count and evenness checks in the same change. No mechanical validator or separate ceremony is introduced.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the measurement counts the immediate PR-base delta with the policy's exclusions, never the cumulative stack diff
- portability: no skill text carries an organization-specific threshold or file-classification value; the single portable default (450 normal target, tests and documentation excluded) is the stated fallback the target configuration refines subject to applicable restrictions
- coherence: the three skills reference one lookup home without duplicating the measurement procedure

**Done when:**
- the policy section exists in github-pr-workflow with the lookup, classification, and measurement semantics and the documented unconfigured fallback
- plan-stack's authoring contract carries the advisory planning budget against the policy
- execute-plan-stack's draft-PR step carries the measure-and-disposition duty and the session-log record fields
- the hygiene scan and the pins suite exit 0

**Ship when:**
- none stated (repository-verifiable work only)

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Docs:**
- `agents/skills/github-pr-workflow/SKILL.md` (Task 1)
- `docs/history/backlog/PLAN-PROMPTS.md` (Task 1)
- `agents/skills/plan-stack/SKILL.md` (Task 2)
- `agents/skills/execute-plan-stack/SKILL.md` (Task 3)
- `docs/history/backlog/2026-11-05-stacked-pr-review-size-policy.md` (Task 3) *(coverage flip rides the landing)*

**Tests:**
- none planned; validation is the Validation Commands block's pinned set (the pins suite, the hygiene scan, the machinery inventory check) plus a documented rehearsal walkthrough in the run log (the disposition duty is prose workflow text with no executable unit to test in this repository)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- any blocking validator, gate, registry, or state ledger for PR size; reason: the origin row's machinery bar rejects new machinery on this single witness
- `agents/skills/doing-code-review/SKILL.md`; reason: the panel of record is plan-route only

## Validation Commands

```bash
# Run every command from the target repository root.
bash scripts/scan-public-hygiene.sh
bash scripts/check_maintenance_pins.sh
python3 scripts/machinery_inventory.py --check
```

### Task 1: PR-size policy section in github-pr-workflow

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/github-pr-workflow/SKILL.md`
- `docs/history/backlog/PLAN-PROMPTS.md`

Primary class anchors:
- `## PR size policy` in `agents/skills/github-pr-workflow/SKILL.md`

- [x] Define facts keys for target, optional maximum and optional path exclusions. The effective target is the stricter of 450, the configured target and applicable policy target; absent exclusions default to tests/docs. No maximum applies only when neither applicable guidance nor facts defines one [class: IMPLEMENTATION_REQUIRED]
- [x] Resolve applicable company and repository policy before facts overrides or fallback. Unconfigured facts never disable applicable restrictions; stricter constraints prevail. Preserve source boundary inclusivity and exception prerequisites; never self-authorize an exception [class: IMPLEMENTATION_REQUIRED]
- [x] Treat missing or contradictory applicable policy input as unresolved before PR creation, never silently substitute an unrestricted fallback [class: IMPLEMENTATION_REQUIRED]
- [x] The policy section defines the changed-line measure: additions plus deletions from the final tree diff against a caller-supplied base, with the exclusion classifications applied by path [class: IMPLEMENTATION_REQUIRED]
- [x] The policy section defines the policy disposition outcomes (under target, over target with rationale inside the description, over hard maximum requiring a split) carrying no organization-specific threshold; the portable default is the only stated fallback value [class: IMPLEMENTATION_REQUIRED]
- [x] In PR Descriptions and Stats require What, Why, How, Testing and Notes for reviewers for every PR. Testing states actual verification or that none ran; an unfillable section states that fact. Replace the contradictory omit-verification bullet; additional verification detail stays omit-unless-asked [class: IMPLEMENTATION_REQUIRED]
- [x] Replace the independent fewer-than-10/maximum-15 non-doc-file sizing and even-distribution checks with policy sizing, keeping mechanical splitting steps intact. Condense superseded prose to pay for growth [class: IMPLEMENTATION_REQUIRED]
- [x] Restore shared rules and prior receipts accidentally deleted from PLAN-PROMPTS.md by this plan's authoring landing, using its parent bytes. Keep the current own-entry prune receipt and do not resurrect this plan's dispatch entry; pins must pass unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Run the hygiene scan and the pins suite, expects exit 0 on both [class: REPOSITORY_TEST]
- [x] Commit: `docs: add PR size policy lookup and measurement section to github-pr-workflow` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Advisory planning budget in plan-stack authoring contract

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/plan-stack/SKILL.md`

Primary class anchors:
- `## Authoring contract` in `agents/skills/plan-stack/SKILL.md`

- [x] Budget each planned slice against the stricter of 450 changed production lines, configured target and applicable policy target. Split an over-target slice when clean boundaries exist; consume the shared policy by pointer without duplicating thresholds [class: IMPLEMENTATION_REQUIRED]
- [x] Permit one optional documentation-only task as the first or last stack PR, with disjoint file ownership and honest intended/current-state descriptions. Tests stay with their behavior; documentation required to understand or safely use a code slice stays with it [class: IMPLEMENTATION_REQUIRED]
- [x] Pay for growth: tighten existing task-slicing and required-content prose while adding the budget and documentation option [class: IMPLEMENTATION_REQUIRED]
- [x] Run the hygiene scan and the pins suite, expects exit 0 on both [class: REPOSITORY_TEST]
- [x] Commit: `docs: budget stack slices against the target PR-size policy at planning` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Measure-and-disposition duty in execute-plan-stack draft-PR step

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan-stack/SKILL.md`
- `docs/history/backlog/2026-11-05-stacked-pr-review-size-policy.md` *(coverage flip rides the landing)*

Primary class anchors:
- `## Workflow` in `agents/skills/execute-plan-stack/SKILL.md`
- `## PR size policy` in `agents/skills/github-pr-workflow/SKILL.md`

- [x] The draft-PR workflow step requires, before creating the draft PR: measure the task's changed-line count against its immediate predecessor base through the github-pr-workflow policy lookup, apply the policy disposition, write the description in the PR-description standard's five labeled sections, and record the split-or-rationale disposition inside the description's Notes for reviewers section when over the normal target [class: IMPLEMENTATION_REQUIRED]
- [x] A slice measuring above the hard maximum stops before draft-PR creation and routes the split back to planning (the executor records the over-maximum disposition in the session log and stops; a re-authoring round owns the new task boundaries); the executor never improvises extra PR branches outside the plan's task list, preserving one task per PR and the plan as scope of record [class: IMPLEMENTATION_REQUIRED]
- [x] The session log records policy provenance, resolved limits/exclusions, immediate base/head identities, measured additions plus deletions and disposition beside existing per-task records. Optional first/last documentation-only slices retain descriptions, reviews and applicable validation [class: IMPLEMENTATION_REQUIRED]
- [x] Rehearse 450/451 changed lines, source-policy boundary inclusivity and hard maximum, absent or weaker overrides, unresolved policy input, predecessor-only counting and exclusions. A coupled over-target slice needs rationale; over maximum stops before PR creation; documentation-only end slices count zero production lines and retain review/validation duties [class: REPOSITORY_TEST]
- [x] Pay for growth: fold the workflow step's existing pre-creation verification prose with the new measure-and-disposition duty where both describe the same pre-PR gate, so the step does not grow by the full added text [class: IMPLEMENTATION_REQUIRED]
- [x] Run the hygiene scan and the pins suite, expects exit 0 on both [class: REPOSITORY_TEST]
- [x] Commit: `docs: measure stack task delta against PR-size policy before draft PR` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-11-05-stacked-pr-review-size-policy.md: covered by this plan and deleted in the same completion pass after execution.
