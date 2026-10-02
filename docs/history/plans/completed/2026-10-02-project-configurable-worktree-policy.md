# Plan: Project-configured worktree policy (primary default, opt-in worktrees, conflict reporting)

Backlog origin: docs/history/backlog/2026-10-02-project-configurable-worktree-policy.md
Driving force: simplicity (fix-class user-request: worktree use is currently inferred from workflow defaults, so ordinary project work can be moved into a worktree without the user asking and project-specific constraints have no configuration field dispatchers can consult; the operator direction is recorded in the origin's Evidence section)
Plan review record: the staging series docs/reviews/2026-10-02-plan-review-project-configurable-worktree-policy-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Worktree use becomes an explicit, project-configured choice: the project facts document may declare a worktree policy (the primary checkout by default; opt-in worktrees with a location rule), every plan-work dispatch consults it before creating or entering a worktree, an explicit user request overrides it, a mandatory workflow rule that disagrees with a disabling project setting reports the conflict and stops, and the existing worktree-requiring plan lanes keep their lifecycle guarantees as named lanes.

- The Worktree-first standard (agents/skills/execute-plan/SKILL.md, the canonical lifecycle both plan lanes reference) carries the policy paragraph: the keys (`worktree_policy` = `primary` default or `worktrees`, and `worktree_root` when enabled), the precedence ladder (explicit user direction over project policy over the standard's own default), the five resolution outcomes spelled (unconfigured, disabling, opt-in with location rule, explicit user request, worktree-requiring workflow), and the conflict report.
- The plans skill's Phase 0 authoring setup and the done skill's Run placement paragraph carry the same consult at their decision points, so all three dispatch surfaces read one contract.
- Closeout safeguards are untouched: the transfer-out ordering, the migration-before-removal rule, and the lock matrix keep their current bytes; a policy never skips a migration.

Gate delta: prose-only wiring in three skill files (agents/skills/execute-plan/SKILL.md, agents/skills/plans/SKILL.md, agents/skills/done/SKILL.md); no runtime script bytes, no new gates, no enforcement script. This is a contract addition whose pricing is carried by the origin itself (a user-request capturing an operator direction about the active checkout's predictability, with the witnessed cost that ordinary project work can move into a worktree the user never asked for). The class-default alternative (an enforcement script simulating dispatch decisions) is rejected under the machinery cost-benefit adjudication: the policy is consulted by the agent at dispatch, so the contract's enforcement surface is the skill text the agent already follows, and a simulator would test the prose against itself.

## Terms

- **Worktree policy**: the project facts document's declared choice for whether ad-hoc worktrees may be used for non-lane work, and where: `worktree_policy = "primary"` (the default; the primary project checkout) or `worktree_policy = "worktrees"` (ad-hoc worktrees allowed), with `worktree_root` declaring the location rule (a path template) when worktrees are enabled. Declared in the project's `.ai-playbook/facts.md` beside its existing keys.
- **Precedence ladder**: an explicit user direction for the current work outranks the project policy; the project policy outranks the Worktree-first standard's own default. Absent all three, work runs in the primary checkout for ordinary work and in the plan lanes' worktrees per the named-lane rule below.
- **Named worktree-requiring lanes**: the plan-authoring and plan-execution lanes whose isolation is load-bearing (the Worktree-first standard's own scope: the witnessed parallel-session model, the P57 worktree isolation plan, and the execution claims that name run worktrees). These lanes keep their worktrees by default; their consult obligation is the conflict report: when a project's policy disables worktrees, the dispatcher reports the conflict (the lane requires an isolated checkout the project setting forbids) and stops for operator direction instead of creating the worktree or silently working in the primary checkout.
- **Ordinary work**: any work outside the named lanes and outside an explicit user request; it runs in the primary project checkout under the default.
- **Conflict report**: a named stop: the dispatcher reports the disagreeing pair (the workflow rule and the project setting) and takes no worktree or checkout action until operator direction resolves it.

## Assumptions

- assume the policy lives in the project facts document; basis: the facts document is this repository's established per-project configuration surface (every skill's Configuration section reads it), so a worktree policy is a facts row, not a new config file.
- assume the plan-authoring and plan-execution lanes stay worktree-requiring named lanes whose policy consult reports conflicts rather than silently degrading to the primary checkout; basis: their isolation is load-bearing (execution claims name run worktrees, the witnessed parallel-session model runs multiple worktrees against one repository, and the P57 worktree isolation plan landed that standard), and the origin's own Expected reconciles mandatory workflows "as named exceptions" whose safeguards stay intact.
- assume the docs-branch skill is out of scope; basis: its worktree use is intrinsic to the docs orphan-branch sync (a temporary worktree for the docs branch checkout, created and removed inside one locked section), not an ordinary-work placement decision, and the origin scopes the contract to "the shared project-work dispatch paths".
- assume prose wiring with no enforcement script; basis: the machinery cost-benefit adjudication caps machinery growth, the policy is consulted by the agent at dispatch from skill text the agent already follows, and a behavioral simulator would test prose against itself for two configuration keys; the five origin scenarios are covered as explicit resolution outcomes in the contract paragraph (each scenario's resolution is spelled, not prose-hoped).
- assume opt-in is recorded as permission semantics, deliberately narrower than the origin's config-enables arm for ordinary work; basis: a blanket ordinary-work mandate re-introduces the inferred-worktree behavior the origin's own Problem section records, the named lanes and explicit requests already warrant worktrees, and the machinery cap weights against a new ordinary-work dispatch surface; the completion pass states this partial delivery in the origin's fold disposition.
- Sources inspected: `agents/skills/execute-plan/SKILL.md` Worktree-first standard (read 2026-10-02: the intro paragraph, the six lifecycle steps, the Base-branch resolution rule, the Reference contract paragraph, and the section end at the Phase 0 heading) and the Configuration section (line 518, the facts-key table); `agents/skills/plans/SKILL.md` Phase 0 Step 0.1 (the creation step the consult attaches to); `agents/skills/done/SKILL.md` Run placement paragraph (line 64, the primary-default dispatch placement and the ad-hoc-worktree sanctioned arm); the origin's Expected, Suggested fix, and operator direction.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: worktree use stops being inferred and becomes a project-configured choice with a fixed precedence ladder (user direction over project policy over the standard's default); the Worktree-first standard, the plans authoring setup, and the done Run placement all consult it, conflicts are reported instead of silently resolved, and the plan lanes keep their isolation as named lanes (simplicity force).

Before (today): the standard says every plan run works in an ad-hoc worktree and nothing else consults anything, so ordinary project work can inherit a worktree from a skill's defaults, a project whose instructions forbid worktrees has no field to say so, and the agent's active checkout is whatever the last default chose.

After (this plan): the project facts document may declare `worktree_policy`; the three dispatch surfaces read it before creating or entering a worktree; an unconfigured project gets the primary checkout for ordinary work and the plan lanes' worktrees as today; a disabling project gets a clear conflict report on the plan lanes instead of a silent degradation; an opting-in project gets worktrees at its declared location rule; an explicit user request overrides everything; and the closeout migration-before-removal safeguard is untouched.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the five origin scenarios each have one spelled resolution in the contract paragraph, and the precedence ladder is total (no unordered pair).
- safeguard preservation: the closeout migration sentence and invocation are pinned by check 5, and the three-file changed-file scope (check 6) is the byte-scope guarantee.
- single source: the contract paragraph is the one full statement; the plans and done edits reference it and never restate the keys.

**Done when:**
- The Worktree-first standard carries the policy paragraph and the Configuration table carries the two keys; the plans Phase 0 and the done Run placement carry their consult references; the pins suite stays green; all Validation Commands exit 0.

**Ship when:**
- [class: OPERATIONS_FOLLOW_UP] The runtime twins of the three touched skills are refreshed per the operators' normal vendored-asset sync (the `~/.agents/skills/` copies), so live sessions load the consult; owner: the execution session's closeout sync step as the preferred first arm, and unconditionally a vendored-sync backlog item naming the three skill files (left even when the sync step is claimed, closed only on grep evidence for the inserted consult text in all three twins; the item also names the known non-vendored runtime copies (autonomous agent-managed skill directories) so their refresh is tracked even though the sync rules exclude them). Consumer repositories declare their own policy rows in their facts documents.

## Review Scope

- `docs/history/plans/2026-10-02-project-configurable-worktree-policy.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/done/SKILL.md`
- `docs/history/backlog/2026-10-02-project-configurable-worktree-policy.md`

## Validation Commands

Authoring-time records: (1) RED-today evidence: the consult text is absent from all three base files at main 37445449, re-derived 2026-10-02 (`grep -c 'worktree_policy' agents/skills/execute-plan/SKILL.md` prints 0; the same for the plans and done files; the facts document carries no worktree_policy key). (2) Baselines on the base tree: the pins suite exits 0; the `## Worktree-first standard` heading count 1 in execute-plan; the `## Phase 0: Run Setup (Run Once at Start)` heading count 1 in execute-plan and 0 in plans (plans' own heading is `## Phase 0: Authoring Worktree Setup (Run at Every Authoring Session Start)`, a different string, also count 1); the Run placement paragraph occurs once in done. (3) Rule 29 pre-round gates on the plan bytes: em-dash `touched` exit 0; the public-hygiene scan exit 0; `plan_readiness.py --pre-round` clean (with the facts copy in the worktree). (4) Rule 22 mechanical audit plus rule 44 extraction proof: the plan's fences were extracted with the signature-keyed parser `re.findall(r"```(?:bash)?\n(.*?)\n```", plan, re.S)` (the validation fence identified by its `set -e` opening, the task fences paired in document order) and applied to a scratch clone of main with the plan committed onto the clone's main first; the ENTIRE Validation block was executed end to end from the extracted bytes with exit 0, and the flip probes (the policy paragraph deleted from the standard; the plans consult sentence deleted) each aborted fail-closed with their own diagnostics; both flips restored and the block re-ran green. (5) r1 fold receipt and later receipts: recorded as rounds land.

```bash
set -e
# Executor note: run from the repository root. set -e makes the block fail
# closed: the first failing check aborts with its own non-zero status. Each
# byte-level arm carries its own diagnostic.

# 0) the validated bytes are the branch's bytes
[ -z "$(git status --porcelain -- agents/skills/execute-plan/SKILL.md agents/skills/plans/SKILL.md agents/skills/done/SKILL.md)" ] || { echo "check 0: validation targets dirty against HEAD:"; git status --porcelain -- agents/skills/execute-plan/SKILL.md agents/skills/plans/SKILL.md agents/skills/done/SKILL.md; exit 1; }

# 1) public hygiene (exit 0 required)
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh

# 2) em-dash gate over the changed bytes against main
bash scripts/check-no-em-dash.sh added-lines --base main

# 3) the full pins suite (exit 0 required)
bash scripts/check_maintenance_pins.sh

# 4) landed bytes: the contract paragraph and both consult references land
#    exactly once each, and the declared keys appear in the contract paragraph
[ "$(grep -c 'worktree_policy = "primary"' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: standard policy declaration line count"; exit 1; }
[ "$(grep -c 'Project worktree policy' agents/skills/execute-plan/SKILL.md)" -eq 2 ] || { echo "check 4: standard policy paragraph heading count (paragraph + Integration Points entry)"; exit 1; }
[ "$(grep -c '^| `worktree_policy` |' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: configuration table row count"; exit 1; }
[ "$(grep -c '^| `worktree_root` |' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: worktree_root configuration row count"; exit 1; }
[ "$(grep -cF 'see `agent-runtime-layout.md` there |' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: shared_docs_dir row tail survived"; exit 1; }
[ "$(grep -c 'an explicit user direction against the worktree reports the isolation conflict' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: lane-direction resolution present"; exit 1; }
[ "$(grep -c 'are mechanical fixtures that need no consult' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: fixture exemption present"; exit 1; }
[ "$(grep -c 'only an explicitly declared `worktree_policy` is a disabling declaration' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: presence-sensitivity rule"; exit 1; }
[ "$(grep -c 'the lane requires an isolated checkout the project setting forbids' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: lane-conflict clause"; exit 1; }
[ "$(grep -c 'another repository.s toplevel or git directory is rejected' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: location-rule validation"; exit 1; }
[ "$(grep -c 'opt-in is permission, not a mandate placing ordinary work' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: opt-in permission clause"; exit 1; }
[ "$(grep -c 'reports the conflict and stops for operator direction' agents/skills/plans/SKILL.md)" -eq 1 ] || { echo "check 4: plans conflict-and-stop span"; exit 1; }
[ "$(grep -c "the done skill.s Run placement consult" agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: Reference contract done naming"; exit 1; }
[ "$(grep -c 'no policy ever skips the transfer-out ordering' agents/skills/done/SKILL.md)" -eq 1 ] || { echo "check 4: done safeguard span"; exit 1; }
[ "$(grep -bo 'Project worktree policy' agents/skills/execute-plan/SKILL.md | head -1 | cut -d: -f1)" -lt "$(grep -boF '1. **Create the worktree.**' agents/skills/execute-plan/SKILL.md | head -1 | cut -d: -f1)" ] || { echo "check 4: policy paragraph not before step 1"; exit 1; }
[ "$(grep -bo 'The setup consults the project worktree policy' agents/skills/plans/SKILL.md | head -1 | cut -d: -f1)" -lt "$(grep -boF 'Create the ad-hoc worktree on its own branch' agents/skills/plans/SKILL.md | head -1 | cut -d: -f1)" ] || { echo "check 4: plans consult not before creation"; exit 1; }
[ "$(grep -c 'an explicit user request for a worktree overrides the project policy' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: user-request override span"; exit 1; }
[ "$(grep -c 'treated as unconfigured with a named report, never a silent fallback' agents/skills/execute-plan/SKILL.md)" -eq 1 ] || { echo "check 4: invalid-value treatment span"; exit 1; }
[ "$(grep -c 'resolves to the primary checkout with the placement reported' agents/skills/done/SKILL.md)" -eq 1 ] || { echo "check 4: done disabling resolution span"; exit 1; }
[ "$(grep -c 'worktree policy' agents/skills/plans/SKILL.md)" -eq 1 ] || { echo "check 4: plans consult count"; exit 1; }
[ "$(grep -c 'worktree policy' agents/skills/done/SKILL.md)" -eq 1 ] || { echo "check 4: done consult count"; exit 1; }
[ "$(grep -c 'worktree_policy' agents/skills/plans/SKILL.md)" -eq 0 ] && [ "$(grep -c 'worktree_policy' agents/skills/done/SKILL.md)" -eq 0 ] || { echo "check 4: key names must live only in the single-source paragraph"; exit 1; }

# 5) safeguard preservation: the closeout migration-before-removal bytes are
#    untouched (the migration sentence survives verbatim in done)
[ "$(grep -c 'before the worktree is removed' agents/skills/done/SKILL.md)" -eq 1 ] || { echo "check 5: done migration-before-removal sentence drift"; exit 1; }
[ "$(grep -c 'worktree_closeout_migrate.py migrate' agents/skills/done/SKILL.md)" -eq 1 ] || { echo "check 5: done migration invocation drift"; exit 1; }

# 5b) execution precondition: the accepted plan record is already landed on
#     main (a check-6 failure listing only docs/ entries means this landing
#     commit is missing and must be created before re-running the block)
[ "$(git diff --name-only main -- docs/history/plans/2026-10-02-project-configurable-worktree-policy.md docs/reviews/ | wc -l | tr -d ' ')" -eq 0 ] || { echo "check 5b: plan/review records not yet on main; land the accepted plan record first"; exit 1; }

# 6) changed-file scope: main is an ancestor of the execution branch at its
#    tip, and the branch differs from main in exactly the three skill files
#    (the plan bytes are already on main at execution)
[ "$(git rev-parse main)" = "$(git merge-base main HEAD)" ] || { echo "main is not an ancestor of the execution branch tip"; exit 1; }
[ "$(git diff --name-only main | LC_ALL=C sort)" = "$(printf 'agents/skills/done/SKILL.md\nagents/skills/execute-plan/SKILL.md\nagents/skills/plans/SKILL.md')" ] || { echo "unexpected changed-file set against main:"; git diff --name-only main; exit 1; }
```

### Task 1: the Worktree-first standard carries the project-policy contract

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- Validation check 4's execute-plan arms and check 6

Four verbatim operations: Edits (a), (b), and (c). Edit (a) inserts the contract paragraph at the head of the Worktree-first standard's lifecycle: replace the anchor (the step-1 opening prefix, single occurrence in the file, so the consult paragraph sits between the section's intro and step 1, read before any create-or-adopt instruction):

```
1. **Create the worktree.**
```

with:

```
**Project worktree policy (consulted at dispatch):** a project's facts document may declare `worktree_policy = "worktrees"` (enabling ad-hoc worktrees, with `worktree_root` declaring the location rule); an absent key means the primary checkout for ordinary work and never disables the named lanes below: only an explicitly declared `worktree_policy` is a disabling declaration. The precedence ladder is fixed: an explicit user request for a worktree overrides the project policy and this standard's default; on a named worktree-requiring lane, an explicit user direction against the worktree reports the isolation conflict and stops for operator confirmation, mirroring the project-policy conflict path. The resolutions: an unconfigured project runs ordinary work in the primary checkout and the plan lanes below in their worktrees as today; a project whose facts explicitly declare `worktree_policy = "primary"` runs ordinary work in the primary checkout, and the named lanes report the conflict (the lane requires an isolated checkout the project setting forbids) and stop for operator direction instead of creating a worktree or silently degrading; a project that opts into worktrees allows ad-hoc worktrees at the declared `worktree_root` location rule when a worktree is otherwise warranted by an explicit request or a named lane (opt-in is permission, not a mandate placing ordinary work); A worktree already provisioned for a named lane is adopted for that lane's resume and closeout even under a disabling declaration; the disabling conflict arms govern only new provisioning. The named worktree-requiring lanes are this standard's plan lanes; other workflows whose worktrees are created and removed inside one automated section of their own operation (the docs-branch docs checkout, the release rewrite worktree outside the repository tree; the worktree-complete landing critical section executes inside the run worktree and is not a placement decision) are mechanical fixtures that need no consult. The location rule, or its absent-key fallback resolution, resolves to a canonical path outside the primary checkout, every registered worktree, and every other git repository's work tree (a parent directory resolving as another repository's toplevel or git directory is rejected), with the run's branch name or plan slug substituting per run so the resolved path is unique; a `worktree_policy` value outside the two spelled forms, or an unresolvable root, is treated as unconfigured with a named report, never a silent fallback. The policy is consulted before any run-placement worktree decision, never after, and the resolved placement is reported with the worktree path and branch name this section already requires, or reported as a primary-checkout resolution in the same run-record line when no worktree is warranted. Closeout safeguards are unchanged: the transfer-out ordering and the migration-before-removal rule apply to every worktree this policy enables, and the primary checkout's own closeout discipline is untouched.

1. **Create the worktree.**
```

Edit (b) adds the two keys to the Configuration table; replace the anchor:

```
| Key | Purpose | Fallback |
|-----|---------|----------|
| `shared_docs_dir` | Coding/stack guidelines for implement sub-agent | Resolve from `~/.ai-playbook/facts.md`; see `agent-runtime-layout.md` there |
```

with:

```
| Key | Purpose | Fallback |
|-----|---------|----------|
| `worktree_policy` | Project worktree placement; semantics owned by the Worktree-first standard's policy paragraph | ordinary work: primary; named lanes: this standard |
| `worktree_root` | Location rule for newly created worktrees when the policy declares `worktrees` | sibling of the primary checkout, unique per run |
| `shared_docs_dir` | Coding/stack guidelines for implement sub-agent | Resolve from `~/.ai-playbook/facts.md`; see `agent-runtime-layout.md` there |
```

- [ ] Run → expect RED: `grep -c 'worktree_policy' agents/skills/execute-plan/SKILL.md` prints 0 at base (re-derived at main 37445449, 2026-10-02) [class: REPOSITORY_TEST]
- [ ] Apply both verbatim edits (the heading anchor occurs exactly once in the file, verified at authoring time; the table anchor likewise) [class: IMPLEMENTATION_REQUIRED]
Edit (c) appends two entries to the Integration Points section (before its closing):

```
- Consumed by the plans skill: Phase 0 Step 0.1 consults the Project worktree policy paragraph before creating or adopting a worktree.
- Consumed by the done skill: the Run placement paragraph consults the policy paragraph before provisioning or adopting any worktree.
```

Edit (c) also names the new consumer in the standard's Reference contract sentence; replace the anchor prefix (single occurrence; the sentence is one unwrapped line in the file, so the printed prefix matches its bytes exactly):

```
**Reference contract:** the plans skill's authoring worktree setup (plan creation, update, and completion sessions) and the mainte
```

with:

```
**Reference contract:** the plans skill's authoring worktree setup (plan creation, update, and completion sessions), the done skill's Run placement consult, and the mainte
```

- [ ] Run → expect GREEN: `grep -c 'worktree_policy = "primary"' agents/skills/execute-plan/SKILL.md` prints exactly 1 (the contract paragraph's declaration), `grep -c 'Project worktree policy' agents/skills/execute-plan/SKILL.md` prints exactly 2 (the paragraph and the Integration Points entry), `grep -c '^| `worktree_policy` |' agents/skills/execute-plan/SKILL.md` prints exactly 1 (the Configuration table row), and `grep -c 'Consumed by the done skill: the Run placement paragraph consults' agents/skills/execute-plan/SKILL.md` prints exactly 1 [class: REPOSITORY_TEST]

### Task 2: the plans authoring setup consults the policy

Files:
- `agents/skills/plans/SKILL.md`

Evidence:
- Validation check 4's plans arms

One verbatim replacement at the head of Phase 0 Step 0.1's creation paragraph, so the landed byte order is consult, then create (the policy is never consulted after a worktree exists); replace the paragraph's opening sentence (single occurrence; verified byte-exact at authoring time):

```
Create the ad-hoc worktree on its own branch off the base branch resolved by the canonical section's **Base-branch resolution rule**, and report the worktree path and branch name.
```

with:

```
The setup consults the project worktree policy per the Worktree-first standard's policy paragraph before creating or adopting anything: on a disabling project this authoring lane reports the conflict and stops for operator direction. Create the ad-hoc worktree on its own branch off the base branch resolved by the canonical section's **Base-branch resolution rule**, and report the worktree path and branch name.
```

- [ ] Run → expect RED: `grep -c 'worktree policy' agents/skills/plans/SKILL.md` prints 0 at base (re-derived at main 37445449, 2026-10-02) [class: REPOSITORY_TEST]
- [ ] Apply the replace (single occurrence) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `grep -c 'worktree policy' agents/skills/plans/SKILL.md` prints exactly 1, and `grep -c 'worktree_policy' agents/skills/plans/SKILL.md` prints 0 (the keys stay single-sourced in the standard) [class: REPOSITORY_TEST]

### Task 3: the done Run placement names the policy

Files:
- `agents/skills/done/SKILL.md`

Evidence:
- Validation check 4's done arms and check 5

One verbatim insertion into the Run placement paragraph; replace the anchor:

```
The primary checkout is the default dispatch placement for a done closeout; an ad-hoc-worktree done run is sanctioned when isolation is needed and owes the Step 2 transfer-out ordering before its worktree is removed.
```

with:

```
The primary checkout is the default dispatch placement for a done closeout; an ad-hoc-worktree done run is sanctioned per the project worktree policy below and owes the Step 2 transfer-out ordering before its worktree is removed. A done closeout consults the project worktree policy per the Worktree-first standard's policy paragraph before provisioning or adopting any worktree: the arm follows that paragraph's resolutions (an explicit user request for isolation in this run, or the paragraph's opt-in warrant for the named lanes; a disabling project's non-lane closeout resolves to the primary checkout with the placement reported in the run record; no policy ever skips the transfer-out ordering or the migration-before-removal rule).
```

- [ ] Run → expect RED: `grep -c 'worktree policy' agents/skills/done/SKILL.md` prints 0 at base (re-derived at main 37445449, 2026-10-02) [class: REPOSITORY_TEST]
- [ ] Apply the replace (the anchor sentence occurs once in the Run placement paragraph; verified at authoring time) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `grep -c 'worktree policy' agents/skills/done/SKILL.md` prints exactly 1, `grep -c 'worktree_policy' agents/skills/done/SKILL.md` prints 0, and check 5's two safeguard arms hold [class: REPOSITORY_TEST]
- [ ] Commit: `skills: project-configured worktree policy (primary default, opt-in worktrees, conflict reporting)` [class: IMPLEMENTATION_REQUIRED]

### Task 4: validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block

- [ ] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]

## Residual findings (cap closure)

(none at authoring time; this section records the cap round's dispositions if the loop reaches its configured cap)

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-02-project-configurable-worktree-policy.md`: this plan's own promoted origin. On completion, fold disposition into the archived plan (contract landed in the three dispatch surfaces, five scenarios spelled, safeguards verified untouched, opt-in delivered as permission semantics narrower than the origin's config-enables arm per Assumption 5) and delete the origin file in the same completion pass per the archive gate.
