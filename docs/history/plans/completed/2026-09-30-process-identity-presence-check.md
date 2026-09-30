# Plan: Worker process-identity presence check

Backlog origin: docs/history/backlog/2026-09-22-execute-plan-empty-process-identity.md
Driving force: code-quality
Plan review record: the staging series docs/reviews/2026-09-30-plan-review-process-identity-presence-check-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

`RuntimeDriver._record_worker_launch` distinguishes an omitted `process_identity` from an explicitly supplied invalid one: synthesis of the documented compatibility identity happens only for a true omission, and an explicitly supplied empty, null, or malformed value is refused by name before persistence.

- An adapter contract violation (the adapter promised an identity and supplied none of substance) surfaces as a named refusal (`process-identity-invalid`) instead of being silently papered over by a synthesized identity.
- The receipt faithfully distinguishes omitted from invalid, so capacity stays conservative without hiding contract violations.

Gate delta: one named refusal return (`process-identity-invalid`) added beside the sibling `provider-session-identity-mismatch` refusal in the same function, plus a presence-key narrowing of the existing synthesis branch. The refusal addition is a fix-class sanctioned exit the origin prescribes directly (its Suggested fix names the presence split and the refusal), removing a false-target synthesis rather than adding machinery; the origin's witnessed defect (a receipt that cannot distinguish omitted from invalid) is the paying witness.

## Terms

- **Omitted**: the receipt carries no `process_identity` key; the documented compatibility identity (`{"provider": ..., "session_id": ...}` synthesized from the adapter and session) is the sanctioned fallback.
- **Explicitly invalid**: the key is present with a falsy value (empty string, empty mapping, null), or a non-mapping value, or a mapping without both a non-empty `provider` and a non-empty `session_id`; refused before persistence.

## Assumptions

- assume the refusal shape matches the function's sibling: `{"status": "refused", "reason": "process-identity-invalid"}`, returned before `registry.register_launch` so nothing persists; basis: the adjacent `provider-session-identity-mismatch` refusal in the same block and the origin's refuse-before-persistence requirement.
- assume a valid supplied identity is a mapping with both keys non-empty after string-stripping; a supplied mapping lacking either key is malformed, not partially acceptable; basis: the documented compatibility shape `{"provider": ..., "session_id": ...}` the synthesis branch builds, and the origin's malformed-value clause.
- assume the origin's classification is fix-class; basis: the header carries no bare `Class:` line and the body records a correctness note from a Task 2 intermediate review with a prescribed narrowing remedy; the judgment is recorded here per the filing-class rule.
- assume the narrowing is deliberate and recorded: supplied identities persisted under today's lenient branch that lack the provider/session_id keys (for example pid-shaped values) will refuse after this plan; the r1 review census found no in-repo caller or test supplying such values, and the named refusal makes the contract visible to any future adapter.
- assume the repository's pytest-runner contract applies (venv interpreter first, ambient fallback with a version guard); basis: plan `docs/history/plans/completed/2026-09-30-done-sweep-closeout-baseline-exemption.md` Task 3 (Validation).
- assume the behavioral probe ran at authoring time: the current code synthesizes for an explicitly supplied empty mapping (the defect live on this tree); basis: read of the block at scripts/execute_plan_runtime.py `if not process_identity:` and the probe simulation in the plan's Gist.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the worker launch recorder refuses an explicitly invalid process identity instead of synthesizing over it, so adapter contract violations stop disappearing into compatibility identities; the driving force is code-quality (the receipt must distinguish omitted from invalid).

Before (today): an adapter supplies `"process_identity": ""` (or `{}`, or null). The `if not process_identity:` branch treats it as omitted and synthesizes `{"provider": <adapter-name>, "session_id": <session>}`. The persisted launch receipt looks like a healthy compatibility identity; the contract violation is invisible. An authoring-time trace of this exact block on the current tree confirms the behavior.

After (this plan): the same receipt hits the presence check first: the key present with an empty, null, non-mapping, or key-incomplete mapping value returns `{"status": "refused", "reason": "process-identity-invalid"}` before anything persists. A true omission keeps today's synthesized compatibility identity, unchanged.

## Evaluation Criteria

**Quality dimensions:**
- correctness: omitted synthesizes (characterization); each explicitly invalid shape (null, empty string, empty mapping, non-mapping, mapping missing `provider`, mapping missing `session_id`) refuses with the named reason before persistence; a fully valid supplied mapping passes through unchanged.
- regression safety: the sibling `provider-session-identity-mismatch` refusal and the launch path are untouched; the existing suite stays green.
- maintainability: the refusal reason is named and testable; the presence/validity split is one guard block.

**Done when:**
- The guard block implements the presence split with the named refusal; the new tests cover omitted versus each invalid shape; all Validation Commands exit 0.

**Ship when:**
- Consumer runtimes pick the runtime up through their normal vendored-asset sync; no further release action belongs to this plan.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_runtime.py`

**Tests:**
- `scripts/test_execute_plan_runtime.py`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- The adapter-side identity production; reason: the defect is the recorder's omitted-versus-invalid conflation, not the adapters' contracts.

## Validation Commands

```bash
TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"
"$TEST_PY" -m pytest --version || { echo "no pytest-capable interpreter" >&2; exit 1; }

# 1. The runtime suite passes with the new tests.
"$TEST_PY" -m pytest scripts/test_execute_plan_runtime.py -q || { echo "FAIL: runtime suite" >&2; exit 1; }

# 2. The new refusal is named in the source (dedicated pin).
grep -qF '"process-identity-invalid"' scripts/execute_plan_runtime.py || { echo "FAIL: named refusal missing" >&2; exit 1; }

# 3. Em-dash gate over the branch's added lines.
bash scripts/check-no-em-dash.sh added-lines --base main || { echo "FAIL: em-dash gate" >&2; exit 1; }
```

Authoring-time gate record (rule 29/19/22): the defect was traced live on this tree at authoring time (the `if not process_identity:` synthesis branch at `_record_worker_launch`, scripts/execute_plan_runtime.py ~2850). RED-today evidence, rule 19: Command 1's new tests do not exist (RED until Task 1); Command 2's refusal reason is absent from the source today (verified zero hits). Rule 22 mechanical audit: Command 2's pin occurs once in Task 2's prescription beside its Command occurrence; `bash -n` over this block passed.

### Task 1: Pin the presence split (RED)

Files:
- `scripts/test_execute_plan_runtime.py`

Evidence:
- `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_execute_plan_runtime.py -k process_identity_presence -q`; covers: the new tests exist and fail against the current synthesizing branch.

- [ ] Add tests named with the `process_identity_presence` substring, patterned on the existing `_record_worker_launch`/launch-path tests: omitted key synthesizes the compatibility identity (characterization, GREEN by construction); each explicitly invalid shape refuses `{"status": "refused", "reason": "process-identity-invalid"}` with nothing persisted (null, empty string, empty mapping, a non-mapping value, a mapping missing `provider`, a mapping missing `session_id`); a fully valid supplied mapping passes through unchanged. [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the invalid-shape tests fail (the current code synthesizes over them); the omitted characterization passes. [class: REPOSITORY_TEST]
- [ ] Commit: `test: pin process-identity presence split (RED)` [class: REPOSITORY_TEST]

### Task 2: Implement the guard (GREEN)

Files:
- `scripts/execute_plan_runtime.py`

Evidence:
- `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_execute_plan_runtime.py -q`; covers: the whole suite green including the new tests.

- [ ] In `_record_worker_launch`, replace the `if not process_identity:` branch with a presence split: `"process_identity" not in receipt` synthesizes the documented compatibility identity exactly as today; a present value that is falsy, not a Mapping, or a Mapping without both a non-empty (string-stripped) `provider` and a non-empty `session_id` returns `{"status": "refused", "reason": "process-identity-invalid"}` before `registry.register_launch`; the sibling session-mismatch elif keeps its place and semantics for a present valid mapping. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the runtime suite exits 0. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: refuse explicitly invalid worker process identities instead of synthesizing` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Whole-plan validation gate

Files:
- `scripts/execute_plan_runtime.py`

Evidence:
- `awk '/^```bash$/{f=1;next}/^```$/{f=0}f' docs/history/plans/2026-09-30-process-identity-presence-check.md > "$TMPDIR/whole-plan-validation.sh" && bash "$TMPDIR/whole-plan-validation.sh"` (the block's own commands extracted and executed; the awk expression is described because the literal sequence cannot appear inside this fenced block); covers: every criterion in Done when.

- [ ] Run the extracted Validation Commands block from the worktree root; every command exits 0. [class: REPOSITORY_TEST]
- [ ] Commit: `test: whole-plan validation for the process-identity presence check` [class: REPOSITORY_TEST]
