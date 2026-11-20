# Plan: Self-Heal Recovery Retry and Re-entry

Backlog origins (scope of record):
- docs/history/backlog/2026-11-19-self-heal-one-shot-refusal-retry-scope.md
- docs/history/backlog/2026-11-19-self-heal-reentry-state-revalidation.md
Driving force: efficiency + code-quality
Plan review record: .ai-playbook/reviews/2026-11-19-plan-review-self-heal-recovery-retry-and-reentry-p01eaead7-r*.md
Execution budget: 0.5h total, largest task 0.5h
Executed: yes (ceb57eab44b1ac78b04b25764a587ce4274821ce)
Authoring claim: 2026-11-19-self-heal-one-shot-refusal-retry-scope.md (session 01a1de3a-5a3d-7b51-a0e7-6259c1198bfb)

## Terms

- **Caller-owned retry budget:** the bounded number of recovery attempts granted by the workflow that owns the refused gate.
- **Re-entry:** a new authorized recovery attempt after a refusal or a renewed user request.
- **Ambiguous owner:** a resource whose current writer or claim holder cannot be reliably identified.

## Why

Self-heal treated repeated one-call claim refusals as proof that the recovery workflow had no retry budget left, then stopped without a concrete next action. On a later request it also needed to re-derive whether a peer had completed the work before resuming; the peer had completed it through the ordinary gate in the meantime.

## Gist & Examples

TLDR: make self-heal recheck state and honor the caller's bounded retry budget, reducing avoidable recovery stops.

Before: one refused claim call was treated as proof the whole workflow had no retry budget left. After: each explicit renewed request rechecks completion, owner, and resource state, then makes at most one attempt through the original gate. For example, a transient claim-lock refusal alone does not prove a peer finished; a later request re-reads the claim and plan archive, skips if a peer completion is proven, and otherwise makes one claim attempt. A stricter caller budget, including zero, wins; without a caller-specific budget, the renewed request authorizes only that one attempt and no automatic repeat. Active or unclear ownership is preserved, and an unresolved refusal names the next owner, action, and needed evidence.

Edge cases: verified peer completion skips execution; active or ambiguous ownership is preserved; a zero or stricter caller budget prevents another gate attempt; no same-invocation automatic retry is allowed.

## Outcome

Self-heal continues a renewed, authorized recovery through the existing gate when the owning workflow still allows an attempt, while preserving current ownership and reporting unresolved stops with a concrete next action.

- A single gate refusal is reported as that invocation's result, not as proof that an outer workflow budget is exhausted.
- Each re-entry starts from current evidence and skips work with a verified peer completion record.
- Active or ambiguous owners remain protected, and retries remain bounded by the workflow that owns them.
- Unresolved work ends with the exact refusal, state checks performed, next owner, action, and evidence required.

Gate delta: no gates, validators, locks, ledgers, schema fields, or review-layer blockers are added, removed, or widened; this plan clarifies existing self-heal recovery prose while the claim gateway and provider configuration remain unchanged.

Follow-up disposition: if implementation review finds a separate recovery defect outside this plan's retry and re-entry contract, capture it as a backlog item with an investigate prompt; otherwise no follow-up item remains.

## Assumptions

- assume one explicit renewed user request authorizes one fresh state evaluation and at most one original-gate attempt when no stricter caller budget applies; basis: the user confirmed re-derivation on every renewed request and that the original gate alone may be retried. A stricter caller budget, including zero, wins, and no automatic repeat is allowed.
- assume retry limits are supplied by the workflow that owns the refused gate and cannot be borrowed from another phase; basis: execute-plan assigns its three-launch allowance only to pre-start worker launches, while claim acquisition has one attempt per invocation (`agents/skills/execute-plan/launch-rules-and-gates.md`, `scripts/execution_claim.sh`).
- assume a durable completion record is sufficient to skip a peer-completed target after current state is re-derived; basis: the completed plan archive and its landing commit were available when the later request resumed.
- assume the provider-status plan and claim gateway remain outside scope; basis: the user confirmed this boundary during requirements discovery.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: every renewed attempt uses current completion, owner, and resource evidence and passes through the existing gate.
- Reliability: a one-shot refusal is not treated as an exhausted outer budget; one explicit renewed request permits at most one new gate attempt unless the owner supplies a stricter budget, including zero.
- Safety: active and ambiguous owners remain protected; retries never bypass the gate or become unbounded.
- Clarity: an unresolved stop names the exact refusal, checks performed, next owner, action, and evidence.
- Minimality: edit only the self-heal recovery contract and pay for every byte of growth in the same skill file.

**Done when:**
- Self-heal distinguishes per-invocation refusal from an exhausted caller-owned budget and defines one bounded re-entry path through the original gate.
- Every re-entry and terminal report requires fresh target, owner, and resource checks; verified peer completion is skipped.
- Active or ambiguous ownership remains protected, and unresolved outcomes identify a concrete next action and evidence.
- The skill-text budget and public hygiene checks pass.
- After landing, the executing agent verifies `~/.agents/skills/self-heal/SKILL.md` resolves to the tracked skill, `cmp -s` returns 0, and both SHA-256 values match; record the path and hashes in closeout.

**Ship when:** none; the canonical runtime registry resolves to the tracked repository skill through the verified symlink described in `projects/.ai-playbook/agent-runtime-layout.md`.

## Documentation Impact Assessment

- `agents/skills/self-heal/SKILL.md` owns the Recovery steps and is the vendored copy consumed from this repository.
- `~/.agents/skills` is a symlink to this repository's tracked `agents/skills` registry per `projects/.ai-playbook/agent-runtime-layout.md`; landing the tracked file updates the active runtime bytes. The executing agent verifies the resolved path and byte equality after landing as a repository closeout check; no separate source write is needed.
- No README or runtime catalog change is needed because the skill name and invocation contract do not change.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/self-heal/SKILL.md` (Task 1)

**Tests:** none; this task changes workflow instructions only.

**Plan-related extension:** implementation and review may change files not listed above when causally related to a task or required to correct this plan's changed contract.

**Out of scope; reject unless plan-related:**
- `scripts/execution_claim.sh` and claim gateway behavior; reason: the observed gate refusal is protected behavior and no gateway defect is in scope.
- Runtime provider configuration or cross-session status lookup; reason: a separate active plan owns provider discovery and this plan preserves the provider boundary.
- New retry machinery, validators, or ledgers; reason: the missing behavior is instruction-level re-entry within an existing caller-owned budget.
- `agents/skills/done/SKILL.md`; reason: this plan changes self-heal recovery before execution and does not change closeout ownership or landing evidence.

## Validation Commands

```bash
python3 scripts/skill_text_budget.py --check
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
python3 scripts/plan_readiness.py docs/history/plans/2026-11-19-self-heal-recovery-retry-and-reentry.md
```

## Validation

Authoring preflight record (rules 29 and Phase 1, placement root = the authoring worktree):
- `bash scripts/check-no-em-dash.sh added-lines --base 2f85e7058c11e01fc09fa1617bac3702214491b2`: pass.
- Public hygiene scan: pass; three pre-existing report paths were listed.
- Structural readiness: pass (`OUTCOME: pass`). Review r1: `ready=no`, two blocking Medium findings and one nonblocking Low finding. Review r2: `ready=no`, one blocking Medium finding on external runtime-source ownership was corrected in r3. Review r3: `ready=no`, one blocking Medium finding showed the source path resolves to the same tracked file; this revision removes the self-copy and makes path-resolution and byte-equality verification an owner-assigned post-landing closeout criterion for r4.
- Runtime source sync: source and repository copy were byte-identical at authoring start; execution must preserve that equality.

### Task 1: Clarify bounded retry and state revalidation in self-heal

Context surface: the plan's Terms, this task, and `## Assumptions`; read the full plan if the task slice does not resolve a decision.

Files:
- `agents/skills/self-heal/SKILL.md`

Primary class anchors:
- `Self-heal` in `agents/skills/self-heal/SKILL.md`

- [x] `Recovery` distinguishes a one-invocation gate refusal from an exhausted caller-owned budget: given one refused claim acquisition and no evidence the owning workflow exhausted its budget, expects self-heal to report that invocation's refusal and permit only an authorized, bounded re-entry through the same gate. [class: IMPLEMENTATION_REQUIRED]
- [x] `Recovery` re-derives state before each renewed attempt and terminal disposition: given a prior refusal followed by a renewed request, expects a fresh completion-record, current-owner, and resource-state check; a verified peer completion is skipped, while active or ambiguous ownership is preserved. [class: IMPLEMENTATION_REQUIRED]
- [x] `Recovery` ends unresolved work with an actionable disposition: given a gate that still refuses or an owner that remains ambiguous, expects the exact refusal, checks performed, next owner, action, and evidence needed to proceed. [class: IMPLEMENTATION_REQUIRED]
- [x] The update preserves the prohibition on bypassing the original gate and on unbounded retries, and does not borrow another phase's retry budget. [class: IMPLEMENTATION_REQUIRED]
- [x] Edit only self-heal recovery prose; leave provider configuration, claim gateway behavior, and retry machinery unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the skill-text budget and public hygiene checks; do not add tests for this prose-only change. [class: REPOSITORY_TEST]
- [x] Commit: `docs: clarify self-heal recovery re-entry` [class: IMPLEMENTATION_REQUIRED]
## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-19-self-heal-one-shot-refusal-retry-scope.md`: completed by Task 1, which distinguishes one refused invocation from exhausted caller-owned retry scope and permits only an authorized, bounded retry through the same gate. The work is in `agents/skills/self-heal/SKILL.md`, committed in `ab3ef0f51b9457a8bf0366ccdd975d886385e634` and refined after Phase 3 review in `ceb57eab44b1ac78b04b25764a587ce4274821ce`. The origin row is folded here and deleted in the archive commit.
- `docs/history/backlog/2026-11-19-self-heal-reentry-state-revalidation.md`: completed by Task 1, which requires fresh completion, owner, and resource checks before any retry or terminal disposition, including the initial refusal, and preserves active or ambiguous ownership. The implementation and review commits are the same as above. The origin row is folded here and deleted in the archive commit.
