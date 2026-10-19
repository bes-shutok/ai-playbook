# Plan: Complete operator-acked correction verification

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-16-corrections-chain-unclassified-mechanical-hops.md`
- `docs/history/backlog/2026-10-10-plan-delta-classifier-excluded-region-gap.md`
Driving force: code-quality
Plan review record: .ai-playbook/reviews/YYYY-MM-DD-plan-review-corrections-chain-operator-ack-end-to-end-pd6a14f5f-r*.md
Authoring claim: docs/tmp/authoring-claims/2026-10-16-corrections-chain-unclassified-mechanical-hops.md (session 01a1501c-2267-70b3-9423-7dd6ba3e4dd8)
Execution budget: 3.0h total, largest task 1.5h

## Terms

- **Correction hop:** one recorded change from a certified before digest to an after digest, bound to an evidence commit.
- **Operator-acked row:** a correction row whose unclassified hunks have a separate authorization witness and a committed classifier-gap record.
- **Correction row identity:** the SHA-256 digest of the canonical JSON encoding of the full correction row, excluding only `receipt.authorization_witness` so the fixed selector does not create a cycle.
- **Authorization witness:** one `correction_authorizations` entry in primary scheduler state, created in a later interactive session after an explicit operator direction. It binds the full correction-row digest to that session identity. This is workflow evidence under the primary-state writer contract, not a cryptographic signature against an actor with direct state-file write access; session identity is environment-derived and forgeable by the invoking process, so the distinct-session refusal is workflow-compliance evidence, never an enforced boundary against a session that controls its own subprocess environment.
- **Plan-family row:** a correction row recorded by the plan-delta classifier for plan-bytes changes.
- **Code-family row:** a correction row recorded for code changes; its classifier and receipt behavior never changes under this plan.
- **Script-verified row:** a plan-family row whose hunks the classifier fully classified, verified without an operator-ack receipt.
- **Operator-ack receipt:** the committed receipt naming the fixed `.ai-playbook/scheduler-state.json#correction_authorizations` selector that marks a row as operator-acked.
- **Classifier:** the plan-delta classifier that assigns correction rows to classified or unclassified hunks; this plan never changes its taxonomy.
- **Fresh-review path:** the existing review route a hop stays on when no valid authorization witness exists.
- **Readiness consumers:** hard staging validation, direct plan readiness, and done readiness, the three gates that resolve the authorization witness.
- **Schema-4 additive-field convention:** the scheduler state file's schema-4 rule that new array fields need no version bump or external migration.
- **Scheduler-turn writer class:** the existing targeted-edit state-file writer used at scheduler turns, whose Step 6 full rewrite carries arrays forward.
- **Classifier-gap record:** a backlog row that preserves the unclassified hunk evidence and its disposition.
- **Certification seal:** the artifact's round-start and round-close commit and digest record.
- **Source digest:** the SHA-256 digest of the plan bytes bound by the review record.
- **Cap closure:** the terminal review state authorized at the configured review-round limit, subject to its recorded dispositions and zero unresolved blocking findings.

## Why

The operator-acked correction contract promises a way to preserve a user-authorized, unclassified change, but the verifier still applies its strict classifier after resolving the receipt. Plan readiness also omits the witness, so both paths reject a complete authorization. This breaks the certification contract and blocks plan closeout.

## Gist & Examples

TLDR: Verify operator-acked correction hops end to end, because code quality depends on one consistent certification contract.

For example, a valid operator-acked plan edit with a matching receipt and classifier-gap record should pass the correction chain after seal and digest checks. A missing witness, changed hunk, wrong artifact, or absent gap record should still refuse. The classifier remains narrow; the receipt authorizes only the recorded hop.

## Outcome

Plan readiness accepts a fully verified operator-acked correction hop while every existing binding and review safety check continues to hold.

- Staging validation and plan readiness agree on the result for the same correction record and witness.
- Script-verified corrections and code-family corrections retain their current behavior.
- The two origin rows are removed when this plan completes, under the plan lifecycle closeout rule.

Gate delta: add `author_session_id` to operator-acked plan-family correction rows only, plus one durable `correction_authorizations` state field, under the existing schema-4 additive-field convention; the live interactive maintenance workflow may invoke the acknowledgment writer only after explicit operator direction, while scheduled workflows never invoke it and keep the fresh-review path; the writer does not claim to detect interactive or scheduled mode; remove caller-selected witness paths and the ephemeral `last_turn.correction` assumption; remove the unconditional classifier refusal only after the exact row digest, authorization entry, operator-ack receipt, classifier-gap record, seal, linkage, and terminal bytes all verify; retain every existing refusal for missing, malformed, mismatched, or self-authored evidence; update the state-file, maintenance, plans, and review-staging contracts; existing review and cap-closure duties remain unchanged. This closes the existing operator-ack route and adds no new lane blocker or writer class.

## Assumptions

- The operator-acked row is intended to authorize a specific unclassified correction hop, because the completed graded-certification plan and current plans and review-staging contracts define that route.
- Only an operator-acked plan-family correction row records `author_session_id`; script-verified plan-family rows and all code-family rows never carry the key, and the row schema treats it as absent-tolerated so every archived row recorded before this change re-validates unchanged. On an operator-acked row the producer records a nonempty `author_session_id` from `scripts/session_channel.py`, the shared session identity helper used by runtime adapters. It resolves `CLAUDE_CODE_SESSION_ID`, then `CURSOR_SESSION_ID`, then `CURSOR_CONVERSATION_ID`, then `CODEX_SESSION_ID`; if all are unset or empty, the producer refuses the operator-acked emission and the hop remains on the fresh-review path. The Codex source is not a generic `SESSION_ID` fallback. The receipt names the fixed selector `.ai-playbook/scheduler-state.json#correction_authorizations`; production reads the array from the primary checkout selected by the existing first-entry `git worktree list --porcelain` resolver. Each entry carries `row_digest`, `writer_session_id`, `operator_direction`, `recorded_at`, `author_session_id`, `artifact_path`, `before_digest`, `after_digest`, `evidence_commit`, and ordered hunk digests; the copied subject fields exist for audit readability, and a copied field that contradicts the matched row refuses. The acknowledgment writer obtains `writer_session_id` from `scripts/session_channel.py` and never accepts it as a caller argument; it refuses when that identity equals `author_session_id`, and it also refuses when its derived identity is empty (all supported sources unset or empty), mirroring the empty-author refusal; the verifier treats an entry whose `writer_session_id` or `author_session_id` is empty or whitespace-only as malformed and refuses. The writer requires a nonempty `operator_direction` equal to the row receipt's directive; an entry with an empty `operator_direction` is malformed and refuses. The live interactive maintenance workflow invokes the writer only after explicit operator direction; scheduled workflows never invoke it and retain the fresh-review path. The writer does not infer or enforce invocation mode from the session ID. `row_digest` is the lowercase SHA-256 of canonical JSON for the full row, excluding only the fixed `receipt.authorization_witness` selector. Rows are keyed by that digest, exact repeated writes are idempotent, and conflicting duplicates refuse. The array is append-only for the state file's lifetime and survives full rewrites; no sidecar search or pruning procedure is required. Missing, malformed, or non-unique matches refuse. Sidecar text and a caller-supplied path never select authority.
- The route does not authorize a general review bypass; existing fresh-review and cap-closure conditions still govern readiness.
- The state file uses schema 4 additive fields, so this field needs no version bump or external migration. Its append is a targeted edit under the existing scheduler-turn writer class and the existing full-rewrite carry-forward path.

Decision points requiring a grill: author_session_id kind scope and legacy-row evolution: pinned to operator-acked plan-family rows only with absent-tolerated legacy rows; source: operator cap-closure direction closing the review loop, 2026-10-19; affected sections: Gate delta, Assumptions, Task 1, Task 3.

## Standing constraints

- Keep the script-verified row path classifier-proven and preserve the code-family correction semantics.
- Resolve every receipt and chain check before the operator-acked kind can bypass only the classifier leg; an ack never bypasses the seal, date, linkage, digest, terminal-byte, or readiness checks.
- Keep the existing classifier taxonomy unchanged. This plan uses the operator-acked route for both clustered origins instead of adding a new exempt class.
- When editing skill text, land the operative contract with a same-change deletion of equivalent bytes from that skill file, and record the byte-budget gate's breach report where that gate applies.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: a valid operator-acked hop verifies only after every authorization and chain leg passes.
- Safety: missing, incomplete, self-authored, mismatched, stale, or dangling evidence retains a named refusal.
- Compatibility: script-verified and code-family corrections keep their current results.
- Consistency: review-staging and plans documentation match the executable verifier and its readiness consumers.

**Done when:**
- A distinct-session authorization survives a full state rewrite and passes hard staging validation, direct readiness, and done readiness; same-session, scheduled, row-mismatch, state-loss, and secondary-worktree shadow cases refuse as specified.
- Existing correction-record, plan-readiness, and done-sweep gate tests pass with no failures beyond the recorded baseline plus this plan's own RED->GREEN flips.
- Both backlog origins are deleted in the same completion change that archives this plan.

**Ship when:**
- No external deployment or human-owned condition; the behavior is repository-local.

## Review Scope

**Explicit must-fix:**

**Production code:**
- `scripts/corrections_record.py`
- `scripts/plan_delta_classifier.py`
- `scripts/session_channel.py`
- `agents/hooks/skill-gate/codex.sh`
- `agents/hooks/lessons-recall/codex.sh`
- `scripts/validate_review_staging.py`
- `scripts/plan_readiness.py`
- `scripts/done_sweep_gates_lib.py`
- `agents/hooks/lessons-recall/cursor.sh`
- `agents/hooks/skill-gate/claude.sh`
- `agents/hooks/skill-gate/cursor.sh`
- `agents/hooks/skill-gate/agy.sh`
- `agents/hooks/lessons-recall/claude.sh`
- `agents/hooks/lessons-recall/agy.sh`

**Documentation:**
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/state-file.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-staging/SKILL.md`
- `agents/hooks/skill-gate/README.md`
- `agents/hooks/lessons-recall/README.md`

**Out of scope; reject unless plan-related:**
- `scripts/plan_delta_classifier.py` exempt-class taxonomy; preserve every classification and exemption result.
- Other review families and unrelated readiness refusal behavior.
- New generic authorization, signature, or review-bypass mechanisms.

## Validation Commands

```bash
python3 -m unittest scripts.test_corrections_record scripts.test_plan_readiness
~/.agents/venvs/ai-playbook-test/bin/python -m pytest scripts/test_done_sweep_gates_lib.py
python3 scripts/validate_review_staging.py --selftest
python3 scripts/session_channel.py --selftest
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-18-corrections-chain-operator-ack-end-to-end.md
python3 scripts/check_plan_origins_closed.py --check-coverage docs/history/plans/2026-10-18-corrections-chain-operator-ack-end-to-end.md
bash scripts/check-no-em-dash.sh touched
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

### Task 1: Honor only a verified operator-acked correction hop

Context surface: the plan's Terms and Standing constraints.

Files:
- `scripts/corrections_record.py`
- `scripts/plan_delta_classifier.py`

Primary class anchors:
- `verify_corrections` in `scripts/corrections_record.py`
- `resolve_ack_receipt` in `scripts/corrections_record.py`

- [ ] Valid hop: given an unclassified plan delta with a receipt naming the canonical selector defined in Terms, a matching primary-state object, evidence commit, seal, and committed gap record, expects the operator-acked chain to verify after every non-classification leg passes. [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety refusals: given a missing, malformed, duplicate, or mismatched `correction_authorizations` entry, same-session writer, empty writer or author session identity, caller-selected witness path, invalid receipt, changed row digest, absent gap record, or broken digest link, expects the existing named refusal and no accepted chain. [class: REPOSITORY_TEST]
- [ ] Compatibility: given a script-verified plan hop or a code-family operator-acked hop, expects its current classifier and receipt behavior unchanged. [class: REPOSITORY_TEST]
- [ ] Baseline: run the Validation Commands before any edit, record the pre-existing red set, and scope every GREEN criterion and the Done-when to no failures beyond the recorded baseline plus this plan's own RED->GREEN flips; sync this worktree with the current default-branch tip first. [class: REPOSITORY_TEST]
- [ ] Ordering prerequisite: the legacy-identity readiness plan (`docs/history/plans/2026-10-17-review-record-legacy-identity-blocks-readiness.md`) lands before execution; its open record-identity defect turns readiness selftests red for reasons outside this plan. [class: REPOSITORY_TEST]
- [ ] Run -> expect RED: execute the correction-record checks for the valid and refusal cases. [class: REPOSITORY_TEST]
- [ ] Emit `author_session_id` only on operator-acked plan-family correction rows and derive the canonical row digest in the shared verifier; write the narrow kind-aware classification leg and keep code-family receipt behavior unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run -> expect GREEN: execute the correction-record checks and confirm all correction-chain legs remain covered. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: verify receipt-backed correction hops` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Carry the authorization witness through plan readiness

Context surface: the plan's Terms and Standing constraints.

Files:
- `scripts/validate_review_staging.py`
- `scripts/plan_readiness.py`
- `scripts/done_sweep_gates_lib.py`
- `scripts/corrections_record.py`

Primary class anchors:
- `main` in `scripts/validate_review_staging.py`
- `evaluate_readiness` in `scripts/plan_readiness.py`
- `gate_plan_readiness` in `scripts/done_sweep_gates_lib.py`

- [ ] Readiness pass: given a valid plan-family correction row and a unique matching authorization emitted by a distinct interactive operator-ack session with explicit direction, expects hard staging validation, direct plan readiness, and the done plan-readiness gate to resolve that same object and accept the same terminal digest. [class: REPOSITORY_TEST]
- [ ] Readiness refusal: given absent or malformed primary state, missing, duplicate, or mismatched authorization, writer identity equal to the row author or empty, or caller-selected `--ack-witness` path, expects staging validation, direct readiness, and done readiness to refuse; code-family behavior remains unchanged. [class: REPOSITORY_TEST]
- [ ] Scheduled path: given scheduled maintenance, expects no writer invocation and no authorization; staging, direct readiness, and done readiness refuse through the missing-witness leg. [class: REPOSITORY_TEST]
- [ ] Primary-state shadow: from a secondary worktree, given a matching primary entry plus a conflicting local decoy, expects pass; given invalid or absent primary state plus a valid local decoy, expects refusal. [class: REPOSITORY_TEST]
- [ ] Review boundary: given an unclassified change without a valid ack, expects the existing review path to remain required and never pass through the new readiness wiring. [class: REPOSITORY_TEST]
- [ ] Run -> expect RED: exercise the current operator-acked staging and plan-readiness paths with a complete witness. [class: REPOSITORY_TEST]
- [ ] Resolver: use the existing first-entry `git worktree list --porcelain` primary-checkout resolver to read the canonical selector defined in Terms; the correction-record helper stays a stdlib-only leaf receiving the already-resolved primary-checkout path from each consumer. [class: IMPLEMENTATION_REQUIRED]
- [ ] Centralize row-digest, authorization, and unique-match validation in the correction-record helper and have done-sweep, plan readiness, and staging validation consume it; done-sweep's existing primary-checkout resolver remains the dirty-state owner. For plan-family rows, require the fixed selector in the receipt and reject caller-selected witness paths; preserve code-family resolution. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run -> expect GREEN: execute the production-shaped valid and refusal checks through staging and done readiness. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: thread correction witnesses through readiness` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Bind a durable acknowledgment to a distinct operator session

Context surface: the plan's Correction row identity and Authorization witness terms.

Files:
- `scripts/session_channel.py`
- `scripts/corrections_record.py`
- `scripts/plan_delta_classifier.py`
- `agents/skills/maintenance/state-file.md`

- [ ] Row identity: given an operator-acked plan-family correction row, expects the producer to record a nonempty `author_session_id` from the shared helper; it resolves Claude, Cursor session, Cursor conversation, then `CODEX_SESSION_ID`, and an empty result refuses acknowledgment and retains fresh review. [class: REPOSITORY_TEST]
- [ ] Writer: given a correction row and explicit operator direction in a later interactive session, expects the production writer to derive its own `writer_session_id`, refuse when it matches `author_session_id` or is empty, bind the row digest and exact subject, and never accept a caller-supplied writer identity or path. [class: REPOSITORY_TEST]
- [ ] Mode boundary: given same-session authoring, expects the writer to refuse; given scheduled maintenance authoring without fresh interactive operator direction, expects the workflow not to invoke the writer, retain fresh review, and leave authorization absent; staging, direct readiness, and done readiness then refuse through the missing-witness leg. The writer does not claim a runtime mode check. [class: REPOSITORY_TEST]
- [ ] Durable lifecycle: given a valid distinct-session acknowledgment, expects the production writer to append idempotently by row digest, conflicting duplicates to refuse, the entry to survive a subsequent full scheduler-state rewrite, and the writer to read the primary state file back after its atomic replace and confirm the appended row digest is present, refusing with a named loss instead of reporting success; state loss remains fail-closed and requires a fresh operator direction. [class: REPOSITORY_TEST]
- [ ] State contract: given schema 4, expects `correction_authorizations` entries to carry the row digest, writer session identity, operator direction, timestamp, and exact row subject under the existing scheduler-turn writer class; Step 6 carries the array forward. Entries are append-only for the state-file lifetime; no sidecar-discovery or pruning job is added. [class: IMPLEMENTATION_REQUIRED]
- [ ] Write root: the writer resolves its write target through the same first-entry `git worktree list --porcelain` primary-checkout resolver and records into the primary checkout's `.ai-playbook/scheduler-state.json`, never a worktree-local copy. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run -> expect RED: exercise same-session refusal, empty-writer refusal, arbitrary writer/path refusal, and the missing production writer against the valid two-session fixture; every row-identity, writer, and mode-boundary fixture pins and clears the four session environment variables using the session-channel selftest save/restore pattern. [class: REPOSITORY_TEST]
- [ ] Implement the writer and state-field contract; extend `scripts/session_channel.py` with final fallback `CODEX_SESSION_ID`, preserve existing Claude/Cursor precedence, and test Codex-only exact derivation plus unset/empty fallback and mixed-source precedence in its embedded selftests, and update the existing scheduler-turn writer class. [class: IMPLEMENTATION_REQUIRED]
- [ ] Codex identity: given only `CODEX_SESSION_ID`, expects the helper to emit that exact value; with it unset or empty, expects empty output; with multiple supported sources set, expects the documented precedence. [class: REPOSITORY_TEST]
- [ ] Run -> expect GREEN: create the entry through the production writer in a second session, apply a full state rewrite, then run hard staging validation, direct readiness, and done readiness against rewritten primary state; from a secondary worktree, also run both primary/local-decoy directions. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: record distinct-session correction authorization` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Align the correction contract and close both origins

Context surface: the plan's Terms and Standing constraints.

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/state-file.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-staging/SKILL.md`
- `agents/hooks/skill-gate/README.md`
- `agents/hooks/lessons-recall/README.md`
- `agents/hooks/skill-gate/codex.sh`
- `agents/hooks/lessons-recall/codex.sh`
- `agents/hooks/lessons-recall/cursor.sh`
- `agents/hooks/skill-gate/claude.sh`
- `agents/hooks/skill-gate/cursor.sh`
- `agents/hooks/skill-gate/agy.sh`
- `agents/hooks/lessons-recall/claude.sh`
- `agents/hooks/lessons-recall/agy.sh`

- [ ] Contract: given a valid distinct-session operator-acked row, expects all three skills to describe the same row identity, durable authorization entry, receipt, classifier-gap, seal, and readiness conditions enforced by the code. [class: IMPLEMENTATION_REQUIRED]
- [ ] Mode boundary: given same-session or scheduled authoring, expects maintenance, plans, and review-staging to retain the fresh-review route and never imply that an acknowledgment can be self-issued; the live interactive workflow invokes the writer only after explicit operator direction, and the writer does not claim to detect invocation mode. [class: IMPLEMENTATION_REQUIRED]
- [ ] Anti-growth: given the changed operative paragraphs, expects each skill file's net byte growth measured across this plan's changes to be offset by equivalent deletion within this plan's changes. [class: IMPLEMENTATION_REQUIRED]
- [ ] Session-channel comments: given the helper's ordered sources, expects `agents/hooks/lessons-recall/README.md` to own the full precedence and all-source empty rule, the skill-gate README to refer to that contract, and all eight direct adapter comments to point to the shared contract and state runtime-specific empty/no-bridge behavior only when every supported source is unset or empty; Codex comments name `CODEX_SESSION_ID`, and all edits preserve hook behavior. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run -> expect RED: reproduce the documentation and executable-contract mismatch in the focused review checks. [class: REPOSITORY_TEST]
- [ ] Update the operator-acked contract; make the lessons-recall README the single prose owner of session precedence and have the skill-gate README refer to it; align the session-model comments in all eight direct adapters, keeping edits comment-only and removing duplicated precedence claims. Preserve the classifier taxonomy and code-family path. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run -> expect GREEN: run the validation commands, then run `python3 scripts/check_plan_origins_closed.py --plan docs/history/plans/2026-10-18-corrections-chain-operator-ack-end-to-end.md` after the origin-row deletions, and review the final text against the verifier behavior. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: align operator-acked correction contract` [class: IMPLEMENTATION_REQUIRED]

## Machinery admission

- Incident: the repeated staging and readiness refusals in `docs/history/backlog/2026-10-16-corrections-chain-unclassified-mechanical-hops.md` and the classifier exclusion witness in `docs/history/backlog/2026-10-10-plan-delta-classifier-excluded-region-gap.md`.
- Expected catch frequency: every declared operator-acked unclassified hop; two separate authoring contexts have already reproduced the refusal.
- Removes or simplifies: remove the caller-selected plan-family witness operand, the unusable ephemeral `last_turn.correction` assumption, and any sidecar-pruning lifecycle; reuse the existing scheduler-turn writer class and schema-4 carry-forward convention.
- False-positive cost: a stale or overbroad authorization could rebind a different hop; the canonical row digest, distinct session identities, exact subject, hunk, seal, commit, gap-record, and terminal-digest checks bind the accepted hop. The state entry is workflow evidence, not a cryptographic signature; session identity is environment-derived and forgeable by the invoking process, so the distinct-session refusal evidences workflow compliance only; lost or malformed state refuses and requires fresh operator direction.
- Sunset or review date: review by 2026-12-18; remove the unconditional classifier refusal only after production-shaped valid and refusal cases pass.

## Residual findings (cap closure)

- security#empty-writer-identity-minted: folded
- implementation#backward-compatibility: folded
- testing#red-validation-baseline-unsatisfiable: folded
- quality#environment-dependent-test: folded
- implementation#missing-wiring: folded
- testing#non-discriminating-pin: folded
- consistency#byte-budget-same-change-arithmetic: folded
- documentation#prose-terms-coverage-gap: folded
- security#automation-lane-witness-mint: folded
- security#spoofable-env-identity-underclaimed: folded
- security#ack-append-lost-update-window: folded
- simplification#yagni: folded
- architecture#dependency-direction: folded
