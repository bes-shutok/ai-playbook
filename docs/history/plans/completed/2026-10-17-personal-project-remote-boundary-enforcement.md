# Plan: Keep the personal-project remote-operation boundary instruction-only and wire the consumer pointers

Backlog origin: docs/history/backlog/2026-10-10-agent-remote-operation-scope-guard.md
Authoring claim: docs/tmp/authoring-claims/personal-project-remote-boundary-enforcement.md (session sess_automation-7903ef3f)
Driving force: security; off-taxonomy justification: the origin is a witnessed authorization-boundary breach (a branch-cleanup instruction was read as permission for remote PR create-and-merge on a personal project), and this plan keeps that boundary's protection while making the shared gate explicit at the two skill steps that issue or inherit remote commands, adding no machinery
Plan review record: the staging series .ai-playbook/reviews/2026-10-17-plan-review-personal-project-remote-boundary-enforcement-p5fb774b5-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1h total, largest task 30m

## Terms

- remote operation: any command that reads or changes remote state (git fetch/pull/push, gh queries, PR operations, remote merges, remote-branch deletion), per the shared gate's own enumeration.
- project scope: the personal, company, or pet classification resolved from the applicable facts document, per the shared gate's resolution rule.
- consumer pointer: one sentence in a consuming skill's workflow step naming the shared gate it already inherits, by reference; the pointer never restates the gate's rule.
- personal-and-pet stop: the shared gate's arm that stops personal and pet projects before remote access (its Personal-or-pet-project arm).

## Why

The 2026-10-10 incident crossed the local-only boundary on a personal project because a shared PR skill exposed remote commands with no project-scope gate; commit 202d8b7f0 landed the gate in agents/skills/github-pr-workflow/SKILL.md plus a docs/AGENTS.md hard rule, and the gate declares doing-code-review and receiving-review as consumers. Neither consumer's own steps name the gate: a session executing either skill reads no boundary text unless the indirect shared-primitive delegation routes it there, and doing-code-review embeds its own remote read of the base branch. The authoring investigation found no verified cross-agent interception point for enforcement: every shell-interception hook in the tree (cursor/hooks/git-safety.sh and cursor/hooks/review-staging-gate.sh's commit mode) is Cursor-only by the shared README, and the one non-Cursor precedent, agents/hooks/budget-guard/, is an optional per-agent install whose two-runtime PreToolUse backstop carries no project-scope resolution, so enforcement would exist only where the instruction is already loaded. The origin row pre-commits the retention decision for exactly this finding ("If no reliable cross-agent enforcement point exists, document the evidence and retain the shared instruction gate as the smallest safe mechanism"); the consumer pointers are this plan's own mechanism for closing the consumption gap the row documents, by reference instead of machinery.

## Gist & Examples

TLDR: the personal-project remote-operation boundary stays instruction-only with no new blocker, and the two consumer skills gain one-line pointers to the shared gate at their remote-touching steps, naming security and simplicity.

Before: the shared gate's text declares doing-code-review and receiving-review as consumers, but neither skill's own steps mention the gate; consumption rides an indirect shared-primitive route, and doing-code-review's base-branch remote read carries no boundary text of its own.

After: each consumer's remote-touching step carries a one-line reference to the github-pr-workflow Project-scope and remote-operation gate; no hook, validator, or other machinery is added, and the docs/AGENTS.md hard rule and the gate text are unchanged.

Edge cases: ad-hoc repositories and unknown scope keep today's instruction behavior (fail-closed by instruction, never by a new gate); the revisit evidence bar is recorded here so any future blocker proposal arrives with its admission evidence pre-registered: (a) a second remote-state change on a personal or pet project while the docs/AGENTS.md hard rule and both consumer pointers are in force on the default branch, filed as a backlog row by the breach-handling session, or (b) a repo-configurable PreToolUse-on-Bash surface present across the agent entrypoints docs/AGENTS.md maps for this repository.

## Outcome

The boundary stays instruction-only, and both skills the shared gate declares as consumers (doing-code-review, receiving-review) name the gate they inherit; all other remote-touching skills stay covered indirectly per the Assumptions.

- doing-code-review and receiving-review each carry the one-sentence gate reference drafted in their tasks, placed before the skill's first remote-touching step text and referencing (never restating) the shared gate.
- No new hook, validator, lock, or state field exists after this plan; the change is two skill-text sentences, one provider-side Integration Points entry, and three text-presence pin lines in the existing pins suite acting as witnesses.
- The revisit evidence bar is recorded in this plan's Edge cases, giving any future guard proposal its pre-registered admission inputs.

Gate delta: none: no gate, fence, protocol depth, state field, or dispatch-pausing condition is added or removed; the change adds three text-presence pin lines to the existing pins suite (witnesses on the provider heading and the two drafted pointer fragments, so a future gate rename breaks a mechanical witness instead of drifting silently) with no refusal-surface change; the removal-shaped pricing is the origin row's own fallback clause (retain the shared instruction gate as the smallest safe mechanism when no reliable cross-agent enforcement point exists) and the machinery admission protocol's no-incident-no-gate rule (one witnessed incident, no verified interception point, unknown catch frequency, a real fail-closed false-positive surface on ad-hoc repositories).

## Assumptions

- assume the design space the dispatch entry enumerates (keep the instruction-only rule, add a repo-owned guard at a PreToolUse hook, limit enforcement to shell commands, or remove the local-only rule) is pinned; the origin row's fallback clause pre-commits the first option when no reliable cross-agent enforcement point exists, and the authoring investigation verified that finding against cursor/hooks/README.md (Cursor-only scope statement covering both cursor shell hooks) and agents/hooks/skill-gate/ (write-gate adapters, not shell-command gates; the separate budget-guard backstop is two-runtime but carries no project-scope resolution).

Decision points requiring a grill: none remain; the design space is pinned by the origin row's fallback clause and the entry's rejected alternatives, verified by the authoring investigation.
- assume the consumers keep consuming the gate indirectly for every surface the pointers do not name; the pointers close the verified gap, they do not restate or duplicate the gate's rule text, keeping one canonical owner per the repository guidelines' cross-cutting integration rule.
- assume no remote state inspection is performed by this plan or its execution, and branch-retention behavior stays out of scope, per the origin row's constraints.
- Sources inspected: the origin row; agents/skills/github-pr-workflow/SKILL.md (Project-scope and remote-operation gate); agents/skills/doing-code-review/SKILL.md (base-branch pull step); agents/skills/receiving-review/SKILL.md (shared-primitive delegation steps); docs/AGENTS.md (personal-projects hard rule and merge-strategy line); commit 202d8b7f0 (the introducing change); cursor/hooks/README.md; agents/hooks/skill-gate/ (adapter precedent).

## Standing constraints

- Validators and test suites run with `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH"` prefixed.
- No em-dash in committed files; run scripts/fix_plan_em_dashes.py over changed plan-adjacent docs before commit.
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` exits 0 before every commit.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each pointer names the gate's actual section (Project-scope and remote-operation gate in the github-pr-workflow skill) and inherits rather than restates its rule; no gate text changes.
- simplicity: two sentences total across both skills; no machinery of any kind.
- maintainability: the pointers name the provider skill and section, and the Task 3 heading pin makes a future gate rename break a mechanical witness instead of drifting silently.

**Done when:**
- both consumer skills carry the drafted pointer sentence before their first remote-touching step text, the three pins land in the suite, and the pins suite and hygiene scan exit 0;
- any pointer defect found after landing is remediated by reverting the one drafted sentence (the bounded response).

**Ship when:**
- none stated.

## Review Scope

**Explicit must-fix:** findings on the files below are always in scope.

**Production code:**
- `agents/skills/doing-code-review/SKILL.md` *(modified: the drafted gate-reference sentence at the head of Step 1)*
- `agents/skills/receiving-review/SKILL.md` *(modified: the drafted gate-reference sentence in Feedback-source Workflow step 1)*
- `agents/skills/github-pr-workflow/SKILL.md` *(modified: one Integration Points entry; the gate's rule text is unchanged)*
- `scripts/check_maintenance_pins.sh` *(modified: three text-presence pins)*

**Tests:**
- none beyond the pins additions: the pins suite lines above are the mechanical witnesses for the drafted sentences and the gate heading; the hygiene scan stays the content witness.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the gate's rule text in agents/skills/github-pr-workflow/SKILL.md (its Project-scope and remote-operation gate section's operative sentences); reason: the plan keeps the shared rule unchanged; only the Integration Points section gains an entry.
- any hook, validator, or enforcement script; reason: the origin row's fallback clause and the machinery admission protocol price against machinery here (no verified cross-agent interception point).
- branch-retention behavior and docs/AGENTS.md wording; reason: operator-set rule, unchanged by this plan.

## Validation Commands

```bash
bash scripts/check_maintenance_pins.sh
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

### Task 1: doing-code-review consumer pointer

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/doing-code-review/SKILL.md` *(modified)*

Primary class anchors:
- `Step 1 head (Gather Context)` in `agents/skills/doing-code-review/SKILL.md`

- [x] At the head of Step 1, before its first remote-touching instruction, add exactly this one sentence verbatim: "This step inherits the github-pr-workflow Project-scope and remote-operation gate: on personal and pet projects it stops before remote access, and the operator alone handles remote operations."; [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given the pointer text, a session executing the doing-code-review steps encounters the boundary reference in its own step text before the step's first remote operation (the PR-URL resolution via the shared workflow and the base-branch `git pull origin` reads), and the gate's own text remains the only rule statement (the pointer references, never restates); [class: REPOSITORY_TEST]
- [x] Commit: `skills: point doing-code-review at the shared remote-operation gate` [class: IMPLEMENTATION_REQUIRED]

### Task 2: receiving-review consumer pointer and validation battery

Context surface: the plan's Terms, this task, and `## Standing constraints`. Wording constraint: the receiving-review pointer must not contain the literals `personal projects` or a personal-class limit phrase (both absence-pinned by the pins suite); the drafted sentence below already avoids them.

Files:
- `agents/skills/receiving-review/SKILL.md` *(modified)*

Primary class anchors:
- `Feedback-source Workflow step 1` in `agents/skills/receiving-review/SKILL.md`

- [x] In Feedback-source Workflow step 1, before the fetch-inventory instruction, add exactly this one sentence verbatim: "Feedback-source steps inherit the github-pr-workflow Project-scope and remote-operation gate: on personal and pet projects it stops before remote access, leaving remote operations to the operator."; [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given the pointer, the sentence precedes the first remote-touching workflow step in file order, so a receiving-review session reads it before any inherited remote operation, and the pointer adds no new rule text; [class: REPOSITORY_TEST]
- [x] Run the full validation battery from `## Validation Commands` and expect every command green; [class: REPOSITORY_TEST] (green at the landing rider after the PLAN-PROMPTS prune; witnessed pre-prune red as the sole PIN FAIL)
- [x] Commit: `skills: point receiving-review at the shared remote-operation gate` [class: IMPLEMENTATION_REQUIRED]

### Task 3: provider integration entry and pins-suite witnesses

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/github-pr-workflow/SKILL.md` *(modified)*
- `scripts/check_maintenance_pins.sh` *(modified)*

Primary class anchors:
- `Integration Points section` in `agents/skills/github-pr-workflow/SKILL.md`
- `exact-sentence pin idiom` in `scripts/check_maintenance_pins.sh`

- [x] In the provider's Integration Points section, add a one-sentence entry "### With `doing-code-review`" naming it as a consumer whose review flow inherits the Project-scope and remote-operation gate, completing the bidirectional declaration the gate's consumer line starts; [class: IMPLEMENTATION_REQUIRED]
- [x] Add three text-presence pins in the suite's existing exact-match idiom: the provider heading line `## Project-scope and remote-operation gate` in agents/skills/github-pr-workflow/SKILL.md, and one stable fragment from each drafted pointer sentence (the `Project-scope and remote-operation gate:` lead) in each consumer file, so a gate rename or a pointer deletion breaks the battery; [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given the branch state before Tasks 1 and 2, the two consumer-fragment pins refuse (the fragments are absent) and after them they pass; the provider-heading pin passes at both states, so a future gate-section rename alone breaks it; [class: REPOSITORY_TEST]
- [x] Run the full validation battery from `## Validation Commands` and expect every command green; [class: REPOSITORY_TEST] (green at the landing rider after the PLAN-PROMPTS prune; witnessed pre-prune red as the sole PIN FAIL)
- [x] Commit: `skills: pin the remote-operation gate heading and the consumer pointers` [class: IMPLEMENTATION_REQUIRED]
