# Plan: Scope maintenance capacity by agent runtime

Backlog origin: docs/history/backlog/2026-10-31-maintenance-runtime-scoped-capacity.md
Driving force: efficiency
Authoring claim: 2026-10-31-maintenance-runtime-scoped-capacity.md (session 01a19171-0584-7930-b1ad-434c88bba61d)
Execution budget: 3.0h total, largest task 1.0h
Plan review record: the staging series .ai-playbook/reviews/2026-10-31-plan-review-maintenance-runtime-scoped-capacity-p9542243e-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)

## Terms

- **Active runtime:** identity supplied by the invoking agent and normalized through `projects/.ai-playbook/execute-plan-runtime-inventory.toml`; the inventory does not detect active sessions.
- **Shared unknown occupant:** live work with absent, invalid, or unverifiable runtime identity; it counts against every runtime's cap.
- **Per-runtime fleet count:** live children in the active runtime plus shared unknown occupants, deduplicated by the existing evidence order.
- **Account quota governor:** the host-wide provider quota state and policy in `agents/skills/maintenance/quota-policy.md`.
- **Skill-gate marker:** `plans.<project>.<session>.marker` in `~/.ai-playbook/runtime/skill-invoked/`; project uses `facts_paths.resolve_project_key` for the plan write target, session is SHA-1 of the non-empty session ID truncated to 16 hexadecimal characters.
- **Session key:** `python3 ~/.ai-playbook/scripts/session_channel.py` output; this session is `01a19171-0584-7930-b1ad-434c88bba61d`.

## Why

The maintenance guard applies a repository-wide child cap and global lane-occupancy holds. Three live ZCode execution claims can fill the fleet and trip G1e even when Codex has no child, holding urgent Codex execution and authoring. Runtime-scoped capacity applies to both the cap and ordinary lane occupancy while the account-wide quota governor controls shared provider load.

## Gist & Examples

TLDR: Count maintenance children by canonical runtime, because efficiency requires independent urgent work across agent runtimes.

Before: three ZCode claims fill the shared cap and hold both lanes; one ZCode execution can independently trip G1e and hold the execution lane. After: known ZCode work on a distinct target neither consumes Codex capacity nor holds Codex G1e/G1a; three Codex children still fill its cap. Same-target work, unknown identities, and audit/re-triage exclusivity still hold; exhausted account quota still holds both lanes.

## Outcome

A maintenance turn can use its own runtime's capacity when another known runtime is busy.

- A known runtime can dispatch eligible work when only another known runtime has reached its three-child cap.
- Same-runtime and unknown-runtime occupancy retain conservative protections.
- Account quota limits and serialized landing continue to apply.

Gate delta: retain the existing G1e/G1a refusal and threshold of three per runtime; scope known ordinary occupants to the active canonical runtime across every occupancy arm, including state, automation, widened, and claim discovery; keep same-target and audit/re-triage holds global; add runtime identity as non-blocking metadata to authoring/execution claims and child records; preserve unknown records as shared occupants; remove distinct-target known cross-runtime occupancy as a reason to hold capacity; add no new blocker class, lock, ledger, or quota exception; keep the account quota governor unchanged. The observed three-ZCode-claims no-dispatch is the witnessed catch supporting this fix-class correction. Existing review gates remain unchanged.

## Assumptions

- assume each supported runtime supplies its own active identity; basis: `projects/.ai-playbook/agent-runtime-layout.md` assigns identity supply to the invoking agent and the runtime inventory defines canonical IDs.
- assume old records without runtime identity remain shared until their existing expiry or completion rule releases them; basis: existing lane fail-safe and claim schemas.
- assume per-runtime capacity can reuse the three-child threshold and current deduplication order; basis: P54 capacity model and P57 execution worktree isolation.

Decision points requiring a grill: active identity comes from the invoking agent and is normalized by the runtime inventory; source: `projects/.ai-playbook/agent-runtime-layout.md` Agent-type affinity contract, 2026-10-31, affects Terms and Tasks; unknown identities count as shared occupants; source: existing maintenance fail-safe and the operator-directed backlog acceptance criteria, 2026-10-31, affects Terms and Tasks; quota stays account-wide; source: `agents/skills/maintenance/quota-policy.md` Account governor policy, 2026-10-31, affects Why, Outcome, and Tasks.

## Standing constraints

- Never infer runtime from session-name prefixes, task labels, branch names, or worktree paths.
- Preserve same-runtime lane and target checks, audit/re-triage exclusivity, strongest-evidence deduplication, account quota, worktree isolation, and serialized landing.
- Keep the separate Codex compaction and ZCode fresh-session backlog items open and out of scope.

## Evaluation Criteria

**Quality dimensions:**
- Capacity: known work in another runtime does not consume this runtime's cap; three same-runtime children still do.
- Safety: unknown work remains shared; target and audit/re-triage holds and account quota remain independent.
- Records: decision reasons name active runtime, counted work, and excluded known cross-runtime work.

**Done when:**
- Focused regressions cover Codex with three ZCode children, three Codex children, unknown identities, same-target holds, audit/re-triage exclusivity, and exhausted account quota.
- Maintenance pins and claim lifecycle checks pass and owning skill text agrees on runtime identity and unknown fallback.

**Ship when:** None; no external release condition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/guards.md` (Task 2)
- `agents/skills/maintenance/state-file.md` (Task 1)
- `agents/skills/maintenance/template-authoring.md` (Task 1)
- `scripts/execution_claim.sh`, `scripts/check_authoring_plans_liveness.py`, and `scripts/OUTCOME_CONTRACT.md` (Task 1)
- `agents/skills/maintenance/decisions.md` and `agents/skills/maintenance/SKILL.md` (Task 2)
- `agents/skills/execute-plan/SKILL.md`, `agents/skills/execute-plan/runtime-contract.md`, `agents/skills/execute-plan/worktree-first.md`, and `agents/skills/execute-plan-stack/SKILL.md` (Task 3)
- `agents/skills/maintenance/template-execution.md`, `agents/skills/maintenance/prompt-templates.md`, `agents/skills/maintenance/zcode.md`, `agents/skills/maintenance/CHANGELOG.md`, and `agents/skills/maintenance/templates-CHANGELOG.md` (Task 3)

**Tests:**
- `scripts/test_execution_claim.py` and `scripts/test_authoring_plans_liveness.py` (Task 1)
- `scripts/check_maintenance_pins.sh`, `scripts/execution_claim.sh`, `scripts/test_execution_claim.py`, and focused maintenance regression coverage chosen from repository evidence (Task 3)
- `scripts/test_maintenance_runtime_scope.py` (Task 3)

**Plan-related extension:** implementation and review may change files not listed above when the change implements a task, fixes its regression, closes implied wiring, or contradicts a changed contract. Otherwise reject as out of scope with a reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/quota-policy.md`; reason: preserve the account governor without changing its policy.
- `docs/history/backlog/2026-10-31-maintenance-autopilot-codex-same-session-compaction.md` and `docs/history/backlog/2026-10-31-maintenance-autopilot-zcode-session-per-pick.md`; reason: separate runtime-specific context behavior.

## Validation Commands

```bash
bash scripts/check_maintenance_pins.sh
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_execution_claim.py'
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_authoring_plans_liveness.py'
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_maintenance_runtime_scope.py'
```

### Task 1: Record runtime identity on child and claim witnesses

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/state-file.md`
- `agents/skills/maintenance/template-authoring.md`
- `scripts/execution_claim.sh`
- `scripts/check_authoring_plans_liveness.py`
- `scripts/OUTCOME_CONTRACT.md`
- `scripts/test_execution_claim.py`
- `scripts/test_authoring_plans_liveness.py`

Primary class anchors:
- `create_claim_noclobber()` in `scripts/execution_claim.sh`
- `write_claim_stamped()` in `scripts/execution_claim.sh`
- `try_dead_run_conversion()` in `scripts/execution_claim.sh`
- `load_claims()` in `scripts/check_authoring_plans_liveness.py`
- `AUTHORING CLAIM` in `agents/skills/maintenance/template-authoring.md`
- `children` in `agents/skills/maintenance/state-file.md`

- [x] The execution-claim interface accepts `--runtime <canonical-id>` and validates it through the runtime inventory: given a recognized ID, expects it to reach each writer; given missing or invalid identity, expects shared-unknown behavior without inference. [class: IMPLEMENTATION_REQUIRED]
- [x] `create_claim_noclobber()` and `write_claim_stamped()` record or preserve runtime identity on claim, take, takeover, refresh, and refresh-recreate paths. [class: IMPLEMENTATION_REQUIRED]
- [x] `try_dead_run_conversion()` writes the resumer runtime identity on its replacement claim while preserving the verified prior optional fields. [class: IMPLEMENTATION_REQUIRED]
- [x] The execution-claim outcome contract documents `--runtime`, the persisted `runtime_id`, and the shared-unknown fallback. [class: IMPLEMENTATION_REQUIRED]
- [x] Authoring claim writers record `runtime_id`, and `load_claims()` classifies legacy or invalid values as shared unknown. [class: IMPLEMENTATION_REQUIRED]
- [x] Child entries carry `runtime_id`, and state rewrites preserve it; legacy entries remain readable as shared unknown. [class: IMPLEMENTATION_REQUIRED]
- [x] Run focused checks for initial claim, take, takeover, refresh, refresh-recreate, dead-run conversion, authoring claims, and unknown legacy forms. [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: record child runtime identity` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Scope the existing fleet cap and lane reasons by runtime

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/guards.md`
- `agents/skills/maintenance/decisions.md`
- `agents/skills/maintenance/SKILL.md`

Primary class anchors:
- `G1e` in `agents/skills/maintenance/guards.md`
- `G1a` in `agents/skills/maintenance/guards.md`

- [x] Every ordinary G1e/G1a occupancy arm and the fleet cap scope known occupants to the active runtime: given one fresh ZCode execution claim on a distinct target and a Codex session, expects G1e free and D1 eligible when all other guards pass. [class: IMPLEMENTATION_REQUIRED]
- [x] Three same-runtime children still fill the existing cap: given three live Codex children, expects both lanes to hold for capacity. [class: IMPLEMENTATION_REQUIRED]
- [x] Unknown occupant or active identity remains conservative: given an unknown peer, expects it to count for all runtimes; given unknown active identity, expects the original shared lane holds and cap. [class: IMPLEMENTATION_REQUIRED]
- [x] Same-target claims still hold across runtimes and audit/re-triage exclusivity stays global: given a matching target or occupied exclusive lane, expects the relevant lane to hold despite free fleet capacity. [class: IMPLEMENTATION_REQUIRED]
- [x] Decision reasons report active runtime, count, and excluded known cross-runtime work; exhausted quota independently holds both lanes. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `maintenance: scope fleet capacity by runtime` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Align payloads and add regression coverage

Context surface: the plan's Terms, this task, and `## Standing constraints`. The required pin suite also covers the cycle-gate advisory wording drift tracked in `docs/history/backlog/2026-10-31-pins-cycle-gate-gist-drift.md`; Task 3 re-aims those stale pins to the current text.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/worktree-first.md`
- `agents/skills/execute-plan-stack/SKILL.md`
- `agents/skills/maintenance/template-execution.md`
- `agents/skills/maintenance/prompt-templates.md`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/CHANGELOG.md`
- `agents/skills/maintenance/templates-CHANGELOG.md`
- `scripts/check_maintenance_pins.sh`
- `scripts/execution_claim.sh`
- `scripts/test_execution_claim.py`
- `scripts/test_maintenance_runtime_scope.py`

Primary class anchors:
- `pin()` in `scripts/check_maintenance_pins.sh`

- [x] Every maintained claim-creation invocation supplies its own canonical `--runtime` value: given Codex or ZCode execution, expects the matching `runtime_id` on new claims and child records without name inference. [class: IMPLEMENTATION_REQUIRED]
- [x] Execute-plan, stack, runtime-contract, worktree, and maintenance payload instructions agree on the claim runtime argument and preserve unknown fallback. [class: IMPLEMENTATION_REQUIRED]
- [x] Focused regressions exercise state-file and armed/fired/widened evidence for fresh foreign execution and authoring claims; cross-runtime same-target collisions still hold. [class: REPOSITORY_TEST]
- [x] Focused regressions distinguish unknown peer from unknown active identity, and cover same-runtime saturation, audit/re-triage exclusivity, and account quota holds. [class: REPOSITORY_TEST]
- [x] Maintenance pin coverage checks claim call-site and overlay identity wiring without adding a new blocker class; the full pins suite passes after re-aiming the cycle-gate advisory pins to current wording. [class: REPOSITORY_TEST]
- [x] Changelog records the capacity change and the isolation, landing, and quota invariants it preserves. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `test: cover runtime-scoped maintenance capacity` [class: IMPLEMENTATION_REQUIRED]

## Design Invariants

- The child cap remains three for each known runtime and covers the existing execution, authoring, audit, re-triage, and ad-hoc kinds.
- Known work from another runtime does not consume this runtime's capacity; unknown work counts across runtimes.
- Existing deduplication, lane-specific checks, account quota, worktree isolation, and serialized landing remain in force.
- Runtime identity is supplied by the active agent and normalized by the runtime inventory, never inferred from task labels, session text, branches, or worktree names.
- Every execution-claim creation and conversion path receives `runtime_id` from the invoking agent; refresh preserves the existing identity.
- All maintained execution-claim callers pass the canonical runtime ID explicitly; an unknown or absent value stays a shared unknown occupant.
- This plan adds no lock, ledger, account-quota exemption, or new blocking guard class.

## Disposition of migrated backlog items

- docs/history/backlog/2026-10-31-maintenance-runtime-scoped-capacity.md: covered by this plan's completed implementation of runtime-scoped lane occupancy and fleet counting; the origin file is deleted in this archive transition.
- docs/history/backlog/2026-10-31-pins-cycle-gate-gist-drift.md: covered by Task 3's correction of the maintenance pin assertions after their wording drift; the origin file is deleted in this archive transition.
