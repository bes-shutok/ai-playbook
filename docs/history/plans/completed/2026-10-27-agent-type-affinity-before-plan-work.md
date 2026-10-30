# Agent-type affinity before plan work

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-27-agent-type-affinity-before-plan-work.md`

Plan review record: the staging series .ai-playbook/reviews/2026-10-30-plan-review-agent-type-affinity-before-plan-work-p2e9269e1-r*.md (the highest rN for this source-plan path is authoritative)
Authoring claim: docs/tmp/authoring-claims/2026-10-27-agent-type-affinity-before-plan-work.md (session 01a17c5b-bdc9-7781-86f5-38e0cd2c16dd)

Driving force: token-usage; secondary: simplicity

## Terms

- **Agent type**: a recognized canonical runtime ID from `projects/.ai-playbook/execute-plan-runtime-inventory.toml` that identifies the agent conducting this workflow.
- **Required agent type**: an optional canonical runtime ID on a backlog origin, carried into its plan, that limits which agent runtime may start the work; when absent, the work is runtime-neutral.
- **Runtime-neutral work**: work with no Required agent type; any supported agent runtime may select it.

## Why

On 2026-10-27, maintenance selected a backlog origin whose environment context explicitly names the ZCode desktop runtime while the active session was Codex. The operator stopped authoring before a plan or implementation artifact was written; the initial worktree, branch, and claim were removed. This proves selection crossed an explicit runtime boundary before setup, while the separate ZCode session-channel defect remains a different issue. The origin's runtime requirement must travel with the work, and each selection or direct-entry boundary must compare it with the invoking agent before setup or execution.

## Gist & Examples

**TLDR:** Carry an optional required runtime ID from backlog origin into plan metadata and check it before authoring or execution, preventing wasted wrong-runtime setup while preserving neutral work.

**Before:** An origin names a runtime in prose, but D1/D2 and direct plans/execute-plan entry do not reliably compare that requirement with the active agent. Work can enter setup in an incompatible runtime, and a plan can lose the origin context later.

**After:** `Required agent type: zcode` is explicit metadata on the witnessed origin and is carried into its plan. The invoking agent supplies its active identity, which is normalized through the existing runtime inventory. Missing metadata stays neutral. A mismatch reports the required runtime and holds the origin or plan open; another runtime is never dispatched automatically. A missing or unknown active identity, or an unrecognized declared target, holds only that explicitly targeted work and reports the missing or invalid identity.

**Example:** Given an origin requiring `zcode` and an invoking agent identifying as `codex`, D1/D2 and direct authoring or execution entry identify the mismatch before setup and leave the work open for a compatible session. Given no requirement, the same origin remains eligible across runtimes.

## Outcome

Add one shared, blocking compatibility rule across maintenance D1/D2, direct plan authoring, and execute-plan entry. Use the existing runtime inventory for IDs and aliases, preserve runtime-neutral work, backfill the explicit ZCode witness, and propagate the optional requirement into plan metadata. The ZCode session-channel implementation is outside this plan.

## Gate delta

Add one protocol refusal class at four workflow entry surfaces after a warning-only compatibility check records its first true catch against the witnessed mismatch. The block prevents authoring or execution setup that cannot meet the origin's explicit runtime requirement; it does not hold neutral work. The fix-class origin's alternatives were checked: the sanctioned exit is to hold the item open, report the required runtime, and let a later compatible session select it; continuing now contradicts the origin's Expected behavior to proceed only when compatible. The origin's Suggested investigation also proposes routing to a compatible agent, but automatic cross-runtime dispatch is excluded by the user-confirmed hold-and-report outcome; preserving later compatible-session selection supplies the available exit without adding a router. Removing the false positive would require erasing the explicitly evidenced ZCode requirement, while making selection simpler by omitting comparison leaves the witnessed wrong-runtime setup path open. The witnessed incident is one mismatch, with future catch frequency unknown. The current guard-liveness ledger ratio is 29:48 (29 catches to 48 incidents). False-positive cost is a correctly targeted origin being misclassified and held until its runtime metadata or invoking identity is corrected. The operator approved the blocking outcome after the warning-only catch. Review by 2027-01-27. No existing blocker is retired because the operator explicitly approved this net addition after the true catch. The active machinery admission row carries the pre-registered removal commitment in its note; the registry's `removals` list cannot contain an active path and is populated when the mechanism is retired. Promotion criteria: the warning-only comparison reports the witnessed Codex-versus-ZCode mismatch before setup, and that catch is recorded in the existing gate-liveness ledger before the refusal becomes blocking.

## Assumptions

- The existing runtime inventory remains the canonical source for runtime IDs and aliases; it is an identity vocabulary, not an active-session detector. Basis: `projects/.ai-playbook/agent-runtime-layout.md` and `projects/.ai-playbook/execute-plan-runtime-inventory.toml`.
- The invoking agent can accurately supply its active runtime identity at each workflow boundary. Basis: user-confirmed choice on 2026-10-27; normalize the value through the existing inventory and hold targeted work when it is absent or unknown.
- `projects/.ai-playbook/agent-runtime-layout.md` can own the shared affinity contract beside the existing runtime identity documentation. Basis: that document already owns runtime identity and inventory references.
- Compatibility reporting can use the existing hold/stand-down behavior; no cross-runtime dispatch queue or second inventory is needed. Basis: user-confirmed mismatch outcome on 2026-10-27.
- The plan carries the origin's optional target value; it does not infer target runtime from creator identity. Basis: user-confirmed metadata decision on 2026-10-27.
- The 2026-10-26 ZCode session-channel origin is a witness only; its helper implementation is unrelated to affinity and remains untouched. Basis: distinct `Skill/step` and `Expected` behavior in that origin.
Decision points requiring a grill: explicit target on the origin was confirmed as an optional target field (user response “sure”, 2026-10-27, scope and migration); active runtime identity was confirmed as supplied by the invoking agent and normalized through the inventory (user response “sure”, 2026-10-27, Terms and workflow checks); mismatch handling was confirmed as hold-and-report with no auto-dispatch (user response “sure”, 2026-10-27, Outcome); the blocking outcome after a warning-only true catch was approved (user response “yes”, 2026-10-27, Gate delta).

## Evaluation Criteria

- **Correctness:** Given an explicit compatible target, each entry permits work; given an explicit mismatch, each entry holds it before setup; given absent metadata, work remains eligible; given an absent or unknown invoking identity, or an unrecognized declared target for targeted work, it holds only that targeted work and reports the missing or invalid identity.
- **Maintainability:** One shared contract and the existing runtime inventory define semantics; consumer skills reference the contract instead of duplicating it.
- **Scope control:** The ZCode helper is unchanged; no second runtime inventory, blanket labels, or automatic cross-runtime dispatch are added.
- **Done when:** the warning-only check records its true catch against the witnessed origin; all four workflow boundaries apply the promoted blocking rule; the target value is carried into plan metadata; the registry and readiness gates accept the final records.
- **Ship when:** No external deployment, team, or human-owned prerequisite applies.

## Review Scope

**Explicit must-fix:**
- `projects/.ai-playbook/agent-runtime-layout.md` (Task 1)
- `agents/skills/maintenance/decisions.md` (Task 1)
- `agents/skills/plans/SKILL.md` (Task 1)
- `agents/skills/execute-plan/SKILL.md` (Task 1)
- `docs/history/backlog/2026-10-26-session-channel-zcode-runtime-derivation-empty.md` (Task 1)
- `scripts/machinery_registry.json` (Task 2)
- `scripts/gate_liveness_ledger.json` (Task 2)

## Validation Commands

```bash
python3 scripts/machinery_inventory.py --check
python3 scripts/gate_liveness_ledger.py show
python3 scripts/plan_readiness.py docs/history/plans/2026-10-27-agent-type-affinity-before-plan-work.md
```

### Task 1: Define and exercise the shared compatibility contract

Context surface: Terms, Outcome, Gate delta, and the four workflow surfaces; use the shared contract by reference.

Files:
- `projects/.ai-playbook/agent-runtime-layout.md`
- `agents/skills/maintenance/decisions.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `docs/history/backlog/2026-10-26-session-channel-zcode-runtime-derivation-empty.md`
- `scripts/gate_liveness_ledger.json`

- [x] Given an origin with no `Required agent type`, D1/D2, direct plan authoring, and execute-plan remain runtime-neutral; given a recognized declared target and supplied identity, each surface normalizes both through the existing inventory and reports compatibility or mismatch before setup; given an unrecognized declared target, it holds that origin open and reports the invalid ID. [class: IMPLEMENTATION_REQUIRED]
- [x] Given absent or unknown active identity for explicitly targeted work, each surface holds that work open and reports the required runtime; given a mismatch, it does not dispatch to another runtime. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the optional `Required agent type` field and propagation rule to the shared contract; reference it from all four consumer boundaries without cloning the rule. Label the witnessed origin `zcode` from its explicit environment context, while leaving the session-channel helper and its defect unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Apply the integrated compatibility check in warning-only mode to the witnessed Codex-versus-ZCode origin before any setup; expect a warning naming both identities, and record the true catch with the origin as evidence in `scripts/gate_liveness_ledger.json`. [class: REPOSITORY_TEST]

### Task 2: Promote the witnessed compatibility check to a blocker

Context surface: Task 1's recorded true catch and the shared contract; change only its outcome from warning to hold.

Files:
- `projects/.ai-playbook/agent-runtime-layout.md`
- `agents/skills/maintenance/decisions.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `scripts/machinery_registry.json`
- `scripts/gate_liveness_ledger.json`

- [x] Given Task 1's catch record exists, promote the mismatch outcome at all four workflow boundaries to a blocking hold before authoring or execution setup; neutral work remains eligible. [class: IMPLEMENTATION_REQUIRED]
- [x] Register the blocker with the witnessed incident, one known mismatch with future frequency unknown, the false-positive cost, operator-approved net growth, and the 2027-01-27 review date; include the pre-registered removal commitment and promotion evidence in the active registry note, then move the row to `removals` only when retired. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the documented mismatch is reversed or metadata is removed, the corresponding workflow accepts the now-compatible or runtime-neutral work; the ZCode helper remains outside the diff. [class: REPOSITORY_TEST]
- [x] Run the Validation Commands above and confirm the machinery registry and liveness ledger remain valid. [class: REPOSITORY_TEST]
- [x] Commit: `docs: enforce agent-type affinity before plan work` [class: IMPLEMENTATION_REQUIRED]

## Plan-related extension

Review and implementation may include another file only to repair a direct contradiction caused by the tasks above. Name and justify it before editing. Do not expand into the ZCode session-channel helper defect.
