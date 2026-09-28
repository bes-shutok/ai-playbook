# Backlog: Make execute-plan seed, readiness, and prelaunch recovery contracts agree

- **Filed:** 2026-09-29
- **Status:** done (2026-09-30; executed by plan completed/2026-09-29-execute-plan-seed-readiness-prelaunch-recovery.md, landed main 2f108210, impl review r1 zero blocking)
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** PROJ-607 execution was blocked before a worker could start because an already-seeded task contract exceeded the runtime evidence limit, with no supported recovery transition for that claimed prelaunch state.
- **Origin class:** consumer-feedback (company)
- **Driving force:** reliability; secondary simplicity
- **Source:** PROJ-607 execute-plan run, 2026-09-29. The machine manifest remained unmodified; task 8 had a claimed prepared-handoff successor and no worker launch.

## Problem

The execute-plan workflow allowed incompatible assumptions across plan readiness, manifest seeding, runtime validation, and recovery:

1. Plan readiness reported `ValueError: evidence criterion exceeds UTF-8 item byte limit` because seeded PROJ-607 required-criteria entries exceeded the runtime's 512-byte `MAX_EVIDENCE_ITEM_BYTES` limit. Several entries ranged from 526 to 1537 UTF-8 bytes. The failure occurred during readiness after manifest creation, so the invalid contract was not rejected at its earliest boundary.
2. The task was already `claimed` with a prepared handoff successor, but no worker had launched. The documented `recover-evidence-contract` path handles a launched malformed-result hold. There was no sanctioned transition to correct or retire this prelaunch claim, and direct manifest edits are prohibited.
3. Before readiness, the plan's `Files:` entries used the plans convention `*(new)*` for planned files. `plan_readiness.py --pre-round` requires that marker for not-yet-created paths, while the runtime's task `Files:` parser only accepts a bare path. Removing the marker let the ordinary parser accept the declaration but made readiness semantics and runtime scope parsing diverge.

These are linked boundary failures: a plan can pass one stage with declarations that a later stage cannot consume, and a resulting prelaunch claim can become stranded without a supported correction path.

## Location

- `agents/skills/execute-plan/SKILL.md`, task-local evidence derivation, manifest seeding, and `Files:` declaration contract.
- `agents/skills/execute-plan/runtime-contract.md`, readiness/preflight, evidence limits, and sanctioned recovery operations.
- `scripts/runtime_capabilities.py`, evidence criterion byte limits.
- `scripts/execute_plan_runtime.py`, manifest creation, task file declaration parser, readiness, and recovery transitions.
- `scripts/plan_readiness.py`, pre-round new-file declaration semantics.

## Expected behavior

Before a claim or manifest is created, every task's criteria and file declarations must be representable by all downstream consumers, or be explicitly encoded in a compatible form. Readiness, plan pre-round validation, manifest creation, preflight, and runtime task scope must apply one documented contract to the same declarations. If a valid correction is needed after a claim exists but before worker launch, the driver must offer a receipt-fenced recovery transition that preserves audit history and refuses once work has launched. Operators must not need to edit machine state manually or weaken fail-closed scope and evidence checks.

## Dedup probe and scope boundary

- `docs/history/backlog/2026-09-27-execute-plan-task-scoped-verification-contract.md` owns deriving task-local verifiers and refusing whole-plan verifier contracts before manifest creation. This item consumes that contract and addresses compatibility across readiness/runtime limits plus recovery of an already-created prelaunch claim.
- `docs/history/backlog/2026-09-29-execute-plan-legacy-evidence-contract-compat.md` owns validation compatibility for legacy-digest manifests. This item covers new/current seeded contracts and does not weaken legacy integrity rules.
- `docs/history/backlog/2026-09-29-execute-plan-reviewed-scope-recovery-successor.md` owns receipt-fenced refresh of a reviewed task `Files:` scope. This item covers evidence-contract correction and parser representation parity; it must compose with that recovery without duplicating its scope-refresh behavior.
- `docs/history/backlog/2026-09-29-execute-plan-preflight-declaration-parse-hardening.md` owns duplicate or ambiguous declaration refusal. This item covers the valid `*(new)*` representation that readiness accepts but runtime parsing currently rejects.

## Acceptance

- A single declaration contract is documented and used by pre-round readiness, task parsing, manifest creation, ordinary readiness, and preflight for `Files:` entries, including planned-new paths. A valid new-file declaration is accepted consistently; malformed or ambiguous declarations still fail closed.
- Evidence criteria are validated against the runtime's actual byte/count limits before a machine manifest or claim is created. Errors identify the task and criterion and give an actionable correction. No later readiness call can fail with an uncaught `ValueError` for a contract that the seed boundary accepted.
- The contract explains the byte unit (UTF-8 bytes) and provides an authoring rule for long criteria, such as splitting them into independently verifiable criteria while preserving complete acceptance coverage. Limits are not silently raised without evidence that storage and all consumers support the new bound.
- A locked, audited driver recovery path handles a malformed or incompatible task contract on a claimed prelaunch task with no worker launch or active reservation. It binds task id, claim token, generation, plan digest, corrected contract, and current scope; validates the replacement through ordinary contract rules; atomically closes or rotates the stale claim and returns the task to a state that can pass ordinary preflight; and is replay-safe.
- Recovery refuses after any worker launch, on stale or foreign identity, plan or scope drift, invalid replacement evidence, or active reservation. Every refusal leaves machine state byte-identical. Recovery records enough history to explain the prior and corrected contract identities.
- Regression tests cover oversized criteria rejected at seed time, accepted criteria at the exact byte boundary, Unicode byte counting, compatible new-file declarations through both readiness and runtime parsing, malformed declaration refusal, valid prelaunch recovery, replay, and each refusal case.
- Existing launched `recover-evidence-contract` semantics, legacy-digest compatibility, task-local verifier requirements, and reviewed-scope recovery remain intact; update only the owning contracts and consumers needed to establish end-to-end parity.

## Rejected alternatives

- Raising the 512-byte limit to fit the witnessed criteria without proving every consumer supports the larger contract: rejected because this moves the mismatch and may expand persisted evidence unsafely.
- Editing `runtime_state.json` directly or reclaiming/relaunching the task: rejected because this bypasses the driver's identity fence and does not provide a sanctioned transition from the claimed prelaunch state.
- Removing the `*(new)*` marker from readiness declarations: rejected because readiness uses it to distinguish planned files from missing existing files; weakening that distinction hides a real scope error.
- Treating the earlier fixes to the consumer plan text as a complete solution: rejected because they work around individual parser mismatches without preventing incompatible contracts from being seeded or stranded again.
