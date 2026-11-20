# Plan: Bind execution resume to its own run identity

Backlog origin: docs/history/backlog/2026-11-04-execution-resume-run-identity-confusion.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-06-plan-review-execution-resume-authoring-claim-identity-confusion-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1h total, largest task 1h
Executed: no
Authoring claim: execution-resume-authoring-claim-identity-confusion.md (session 01a1b1a0-11de-7783-a7ad-04da3f7bb607)

## Terms

- Requested plan: the exact repository-relative plan path the execution request names.
- Execution manifest: the saved execution record identifying the requested plan, its immutable origin, current owner, worktree, and branch.
- Immutable origin: `run_session_id`, retained across an authorized owner conversion so earlier task evidence remains bound to its original run.
- Current owner: the manifest `session_id` and execution claim `session`, bound to the active session through the existing claim gateway.
- Active session: the identity returned by the shared session-channel helper for the invoking runtime.
- Execution claim: the existing ownership record for one plan's execution.
- Authoring claim: a record for authoring a backlog item or plan; it does not identify an execution run.
- Registered placement: the run's recorded checkout and branch cross-checked against Git worktree registration, or its recorded primary placement.
- Recovery procedure: the existing procedure in `agents/skills/maintenance/template-execution.md`, including same-owner resume, terminal-owner conversion, and preservation on refusal.
- Stranded-input handoff: the existing closeout of an unlanded authored plan selected by that exact plan's permanent authoring marker and matching claim.
- Supporting regression: execution-selected coverage that exercises the plan-owned acceptance scenarios without a new production guard.

## Why

A resumed execution selected an authoring claim for a different backlog item and created the wrong worktree. The instructions also describe an immutable run identity as the claim-holding session in one place, obscuring the distinction between the original run and its current owner.

## Gist & Examples

TLDR: Clarify execution resume selection and current-owner identity for code quality, preventing an unrelated authoring claim from redirecting the requested run.

Before: an operator resumes plan A after a context break. A same-session authoring claim for item B is nearby, so the agent uses B's authoring branch while passing A to closeout. Existing execution records already identify A, but their precedence over authoring evidence is not explicit at selection.

After: the same request starts from A's exact path and saved execution identity, checks A's execution claim and registered placement, then uses the existing recovery procedure for the current owner. B's authoring claim cannot select A's execution checkout. When A's evidence cannot be reconciled, the run preserves the existing work and reports the missing or conflicting identity.

Edge cases: the immutable origin may differ from the active session after an authorized conversion; the current owner still follows the existing gateway. An absent manifest for a genuinely fresh run follows existing fresh setup. A known interrupted run with missing or conflicting evidence is preserved for recovery. The exact-plan stranded-input handoff may finish authoring, but does not supply a replacement execution identity.

## Outcome

Resume instructions select the requested execution's own records and preserve work when that selection cannot be proved.

- A same-session authoring claim for another item cannot redirect an execution resume.
- The original run identity remains stable while the current owner follows the existing claim and conversion rules.
- Setup and placement instructions point to one identity contract with consistent missing-evidence handling.

Gate delta: none. This clarifies the existing exact-plan and current-owner predicates and their recovery routing; it adds no validator, lock, ledger, schema field, refusal class, or additional conversion condition. Existing claim and placement refusals keep their current eligibility and outcomes.

## Assumptions

- Assume the existing `Run-level ownership and repository placement` section is the identity home; its ownership predicate covers resume selection, so a separate selector section is unnecessary.
- Assume the existing claim gateway remains the executable owner of conversion; its stable-tuple handling preserves the immutable origin and checks the current claim owner separately.
- Assume the stranded-input handoff remains available only for the exact requested plan's missing authored inputs; it never chooses that plan's execution run from an unrelated authoring claim.
- The origin declares fence-class. The scoped correction clarifies already-required identity binding and removes contradictory prose rather than growing the checked set; a new blocking selector is omitted.

Decision points requiring a grill: identity home and correction shape: maintenance-selected standing authorization on 2026-11-06 selects clarification of existing ownership and recovery instructions over new machinery, based on the gateway's existing immutable-origin/current-owner separation.
Scope extensions (grilled): none proposed.
Sources inspected: not a tracker-linked request.

## Standing constraints

- Keep the recovery procedure's provider evidence, owner checks, exact placement binding, bounded legacy handling, and preservation outcomes unchanged.
- Replace contradictory identity wording and shorten existing setup repetitions to pay for added operative bytes within each changed skill file. Keep incident narrative in the origin and at most one operative citation.
- Scope is execution resume selection. Authoring-run ownership transfer, queue classification, resource cleanup, and live memory or claim mutations are outside this plan.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the plan A / authoring B scenario selects A's execution records or preserves A for evidence recovery, and never selects B's checkout.
- Compatibility: same-owner and authorized converted-owner resumes retain their existing eligibility, with immutable origin and current owner distinct.
- Economy: one identity home and short consumer pointers replace overlapping or contradictory descriptions without new production machinery.

**Done when:**
- The three instruction surfaces express the same execution identity order and current-owner distinction.
- Supporting regressions cover the acceptance scenarios, including preservation and ordinary valid resumes.
- Scoped verification, public hygiene, prose policy, and applicable pins pass.

**Ship when:**
- None; all deliverables are repository-verifiable instructions and supporting regression evidence.

## Review Scope

**Explicit must-fix:**

**Docs:**
- `agents/skills/execute-plan/runtime-contract.md` (Task 1): Run-level ownership and repository placement, plus the contradictory State-shape identity sentence only.
- `agents/skills/execute-plan/SKILL.md` (Task 1): live-session recovery routing, Step 0.1 resume selection, and Step 0.4 identity description only.
- `agents/skills/execute-plan/worktree-first.md` (Task 1): existing-worktree selection and the exact-plan stranded-input handoff distinction only.

**Tests:** supporting regression paths are selected from repository evidence during execution and recorded before worker launch; the plan fixes the scenarios, not a guessed test inventory.

**Plan-related extension:** include unlisted paths only when causally required to implement or verify this identity contract. Record execution-selected supporting paths before worker launch. All unrelated portions of the named files stay frozen.

**Out of scope; reject unless plan-related:**
- Claim gateway code, recovery conversion eligibility, new identity stores, new runtime controls, authoring ownership transfer, queue classification, and resource teardown policy.

## Validation Commands

Run from the execution checkout. Execute the selected supporting regression scope before this policy battery; record its exact command and outcomes in the task log.

```bash
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1
BASE_REF="$(python3 -c 'import pathlib,tomllib; print(tomllib.loads(pathlib.Path(".ai-playbook/facts.md").read_text().split("```toml",1)[1].split("```",1)[0])["base_branch"])')" || exit 1
BASE="$(git merge-base HEAD "$BASE_REF")" || exit 1
bash scripts/check_maintenance_pins.sh || exit 1
bash scripts/scan-public-hygiene.sh || exit 1
bash scripts/check-no-em-dash.sh added-lines --base "$BASE" || exit 1
python3 scripts/skill_text_budget.py --check || exit 1
```

### Task 1: Clarify the existing execution identity contract and its consumers

Context surface: the plan's Terms, this task, and Standing constraints.

Files:
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/worktree-first.md`

Primary class anchors:
- `run_session_id` in `agents/skills/execute-plan/runtime-contract.md`
- `run_worktree` in `agents/skills/execute-plan/SKILL.md`
- `Provisioned-worktree adoption` in `agents/skills/execute-plan/worktree-first.md`

- [ ] Given requested execution A and an unrelated same-session authoring claim B, expects selection from A's exact plan path and execution manifest, cross-checked with A's execution claim and registered placement; B never selects A's checkout. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given an existing execution manifest, expects its immutable origin to bind historical evidence while the active session and mutable current owner are reconciled through the existing recovery procedure before any saved-manifest refresh or worktree provisioning. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given same-owner resume or an authorized owner conversion, expects the existing valid path to remain eligible, the immutable origin unchanged, and the claim's current owner bound to the active session; never substitute the origin ID for the active identity. [class: REPOSITORY_TEST]
- [ ] Given missing or conflicting evidence for a known interrupted execution, expects existing preservation and recovery routing, with the conflicting plan, owner, or placement named; no unrelated authoring claim, branch-name resemblance, or newest timestamp supplies the missing identity. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given genuinely fresh execution with no saved run, expects existing fresh setup; given the exact-plan stranded-input handoff, expects authoring closeout to supply only that plan's inputs, followed by execution setup or recovery under its own identity. [class: REPOSITORY_TEST]
- [ ] Before rewriting prose, select supporting regression coverage from repository evidence, record its owned paths, and run the selection scenarios to expose today's instruction ambiguity or contradiction; retain ordinary valid-resume evidence as green compatibility coverage. [class: REPOSITORY_TEST]
- [ ] Replace the State-shape phrase that makes the immutable origin the claim-holding session, home the selection and owner distinction in existing Run-level ownership and repository placement, and shorten setup/placement repetitions to consumer pointers without changing executable claim or recovery commands. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the selected regression scope after the correction, rehearse the A/B and missing-evidence cases against the edited instructions, and run the Validation Commands battery; every claimed outcome must have recorded evidence. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: bind execution resume to its own identity` [class: IMPLEMENTATION_REQUIRED]
