# Execute-plan runtime r4 deferred findings: registry adapter coupling, capability over-declaration, manifest seeding, policy-token validator unification, low-severity residuals

Status: done
Disposition (2026-09-11): plain fix close-out via plan 2026-09-10-execute-plan-runtime-residuals: F13/F14/overflow(b) by Task 5 (generic entrypoint resolution, deferrals section, generated activation fixture), F15 by Task 8 (`create` seeding operation), F18 by Task 6 (unified policy-token validator), overflow(a) plus done-lock smalls by Task 9, overflow(c)/(d)/(e) by Task 10 (single-home prose, lock-section verify-and-close, README row move).
Workflow: backlog
Source: docs/reviews/2026-09-09-branch-review-agent-agnostic-execute-plan-r4.md (branch review round r4, findings F13, F14, F15, F18 + 5 overflow items; deferred from the r4 receiving-review pass on branch 2026-09-09-agent-agnostic-execute-plan)

## Problem

1. **F13 (`architecture#dependency-direction`, Medium)**: `resolve_adapter()` in `scripts/runtime_capabilities.py` (~line 226, now shifted by r4 fixes) contains a name-based special case `if profile["adapter_entrypoint"] == "runtime-adapter:codex": from execute_plan_runtime_codex import CodexAdapter`. The provider-neutral registry module imports the vendor adapter by name, so every future adapter requires editing the shared function, and the `adapter_entrypoint` values for 7 of 8 eligible profiles are dead data resolving only to the fail-closed stub.
2. **F14 (`simplification#yagni`, Medium)**: `projects/.ai-playbook/execute-plan-runtime-inventory.toml` declares seven lifecycle capabilities for eight eligible profiles, but every non-codex profile has launch/wait/resume `unsupported` and resolves to `UnsupportedAdapter`; consumers read only three cells per profile (`parent_continuation`, `final_response`, `resume`, plus `hooks_probe` reading `final_response`). Users selecting an eligible claude/cursor profile hit a fail-closed block the eligibility flag implied would not happen; the registry over-claims and carries ~150 lines of near-identical TOML no consumer reads.
3. **F15 (`architecture#dual-state-ownership`, Medium)**: `create_manifest` in `scripts/execute_plan_runtime.py` is called by no skill step, sub-agent prompt, or CLI operation; no documented boundary translates plan checkboxes into `runtime_state.json`, while the pre-existing checkbox flow remains a second completion record. Each run improvises manifest creation and checkbox/manifest states can drift.
4. **F18 (`simplification#shrink`, Low)**: three divergent policy-token validators: `_valid_policy_token` (`scripts/execute_plan_runtime_codex.py` ~lines 25-39, accepts any absolute repo_root, ignores generation), `_validate_policy_token` (same file, requires repo_root equality and generation match), and the driver's `validate_action_envelope` canonicalization in `scripts/execute_plan_runtime.py`. Rule drift between them yields confusing fail-closed blocks and double maintenance.
5. **Overflow residuals (Low)**: (a) `DONE_LOCK_GENERATION` in `scripts/done-lock.sh` (~line 280 print_exports region) is a tautological alias of the token while release hard-fails when the alias var is missing; (b) the activation fixture at `scripts/testdata/execute-plan/activation/loaded/` commits ~2,100 lines of byte-copied runtime scripts that must be re-synced on every script edit (r4 re-synced them twice); generate the loaded tree from live scripts at test setup and delete the committed copies; (c) the capability-boundary paragraph is pasted into three hook READMEs and restated in two more docs (`agents/hooks/skill-gate/README.md` ~line 428 et al.); keep the full statement once in `agents/skills/execute-plan/runtime-contract.md` with pointer sentences elsewhere; (d) runtime-contract.md (~line 276 pre-r4 numbering) lists the done-lock session fence among meta.env fields though it is a separate file matched by generation and token; (e) README.md (~line 84) lists runtime-contract.md in the Scripts table among executables; move the row beside the execute-plan skill catalog entry.

## Location

- `scripts/runtime_capabilities.py` (`resolve_adapter`)
- `projects/.ai-playbook/execute-plan-runtime-inventory.toml` (profile schema)
- `agents/skills/execute-plan/SKILL.md` (Phase 0/1 seeding boundary), `scripts/execute_plan_runtime.py` (`create_manifest`, CLI operation set)
- `scripts/execute_plan_runtime_codex.py` (policy-token validators)
- `scripts/done-lock.sh`, `scripts/testdata/execute-plan/activation/`, `agents/hooks/*/README.md`, `agents/skills/execute-plan/runtime-contract.md`, `README.md` (overflow items)

## Suggested fix

- F13: resolve adapters generically from an in-module entrypoint mapping (or the package manifest) via `importlib`, keeping `UnsupportedAdapter` for unbound profiles.
- F14: either move the seven no-adapter runtimes into a deferrals section with reason "no verified adapter", or shrink the profile schema to what consumers read (adapter entrypoint plus the three receipt capabilities). Pairs naturally with F13.
- F15: add one documented seeding boundary (a `create` driver operation translating plan checkboxes into machine state), named in SKILL.md Phase 0/1 as the only such path, plus a resume reconciliation rule (manifest wins; divergent checkboxes rewritten via the skill-gate step).
- F18: keep one validator in `runtime_capabilities.py`, parameterized by expected repo_root/generation, called at both boundaries.
- Overflow: per-item minimal fixes as described above.

## Severity

Medium (F13, F14, F15), Low (F18 and all five overflow items). All verified valid by the r4 receiving-review triage; none fixed in this pass.

## Why not fixed now

Post-fix budget management in a regenerating review loop: r4 is the fourth fresh round and r5 is the last planned round, and F13-F15 are structural registry/skill-schema changes whose fix surface (inventory TOML schema + `validate_inventory` + catalog tests + SKILL.md procedure text) would regenerate findings across worker domains in the final round. Deferred per the fix-risk triage rule (refuse further structural surgery late in the loop); the orchestrator's r5 composition should account for the r4 fixed-findings domains (driver state machine, codex adapter, done-lock, contract/SKILL docs, test witnesses).
