# Plan: Corrections chain recursion refusal and regression pins

Backlog origin: docs/history/backlog/2026-10-21-corrections-chain-recursion-refusal-and-pins.md
Driving force: code-quality
Plan review record: .ai-playbook/reviews/2026-10-29-plan-review-corrections-chain-recursion-refusal-and-pins-r*.md
Execution budget: 1.25h total, largest task 1.25h

## Terms

- **Authorization state**: the primary checkout's scheduler state JSON, which stores `correction_authorizations` entries used to verify operator-acked plan-family rows.
- **Operator-acked hop**: one correction hop whose unclassified plan-family changes have a separately verified authorization entry.
- **Mixed chain**: a sequence containing both a script-verified hop and an operator-acked hop.
- **Named refusal**: the existing receipt or append error returned by `corrections_record.py` instead of an uncaught exception.

## Why

Deeply nested scheduler state can currently escape the correction authorization checks as `RecursionError`, and the existing non-object and later-hop bypass behavior lacks regression tests. Returning the established named refusals keeps malformed state from authorizing a correction while preserving the existing state and review contracts.

## Gist & Examples

TLDR: contain recursion failures and pin state-shape and mixed-hop behavior, preserving fail-closed checks for code quality.

**Before:** Parsing the authorization state can raise an uncaught `RecursionError`; serialization can do the same outside a guard. The non-object state refusal and an operator-acked hop after an earlier hop are not covered by focused tests.

**After:** Parsing and serialization recursion return named receipt or append refusals, and focused tests pin both state rejection and the existing classification bypass for only the authorized later hop.

**Edge cases:** Deep nesting that crosses the interpreter recursion limit, a valid JSON value that is not an object, recursion during serialization, and a mixed chain whose authorized hop has index greater than zero.

## Outcome

Correction authorization state failures stay fail-closed and report through the existing named error legs, with the uncovered state-shape and mixed-hop behavior protected by regression tests.

- Deeply nested state cannot escape as a traceback or authorize a hop.
- A valid non-object state remains a named refusal in the verifier and writer paths.
- The classification bypass remains limited to the matching authorized hop in a mixed chain.

Gate delta: No gate, refusal class, fence, protocol layer, or state field is added or removed; existing receipt and append refusals gain handling for the witnessed recursion failures, and no dispatch or later work can pause because of this change.

## Assumptions

- Keep the existing receipt leg's not-decodable refusal for parse recursion and use the existing append leg for serialization recursion; basis: adjacent named malformed-state paths in `scripts/corrections_record.py` and the backlog origin.
- Keep the current mixed-hop index calculation unchanged; the origin records that a mixed-chain probe against HEAD verified it, and requests a regression pin.
- Prefer extending the current parse and append paths over adding parser infrastructure, state, or a separate validator; the origin's direct witness is an uncaught `RecursionError` at those exact paths.
- Map the origin's `security; secondary: testing` force to the plan taxonomy's `code-quality`: it best describes preserving authorization refusal semantics and the corresponding regression coverage.

Scope extensions (grilled): none proposed.
Sources inspected: `docs/history/backlog/2026-10-21-corrections-chain-recursion-refusal-and-pins.md`; `scripts/corrections_record.py`; `scripts/test_corrections_record.py`; `docs/maintenance/development_lessons.md` #142 and #289; `docs/history/plans/completed/2026-10-18-corrections-chain-operator-ack-end-to-end.md`.
Decision points requiring a grill: none remain.

## Standing constraints

- Invalid or malformed authorization state must never grant authority or bypass classification.
- A valid state authorization bypasses classification only for its matching operator-acked plan-family hop after all other verification legs pass.
- Do not change the correction authorization schema or its writer contract.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: every targeted recursion failure returns a named refusal and leaves the authorization state unchanged.
- Regression coverage: tests distinguish the verifier, writer pre-read, pre-replace reread unreadable-byte refusal, serialization, non-object, and mixed later-hop paths.
- Scope control: code-family behavior, schema, authorization matching, and caller contracts remain unchanged.

**Done when:**
- The focused corrections-record suite passes with the new failure and regression cases.
- Deep parse and serialization failures cannot escape as tracebacks, and the mixed-chain test proves only the authorized hop bypasses classification.

**Ship when:** No external release condition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/corrections_record.py` (Task 1)

**Tests:**
- `scripts/test_corrections_record.py` (Task 1)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

## Validation Commands

- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_corrections_record.py' -q`

## Tasks

### Task 1: Return named refusals for recursion and pin authorization boundaries

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/corrections_record.py`
- `scripts/test_corrections_record.py`

Primary class anchors:
- `load_correction_authorizations` in `scripts/corrections_record.py`
- `record_correction_authorization` in `scripts/corrections_record.py`
- `verify_corrections` in `scripts/corrections_record.py`

Evidence:
- The shared authorization-state loader and writer pre-read catch `ValueError` but not `RecursionError`; the writer's `json.dumps` call is outside a recursion guard. The writer pre-replace reread reads text and compares it with the pre-read bytes; it does not parse JSON.
- The verifier already has a named not-a-JSON-object receipt refusal, but the focused tests do not exercise a JSON non-object at this scheduler-state boundary.
- The current classification bypass adds the authorized row's index and compares it with zero-based hop indexes; the backlog's mixed-chain probe reports the behavior correct, but no test protects an operator-acked hop after an earlier hop.

Acceptance:
- [ ] Given authorization state nested deeply enough for `json.loads` to raise `RecursionError`, expects the verifier path through the shared loader and the writer pre-read to return the existing named receipt refusal with no traceback; no authorization is granted and no state bytes are written. [class: REPOSITORY_TEST]
- [ ] Given a valid JSON non-object authorization state, expects both the verifier and writer state path to return the existing not-a-JSON-object refusal without appending or changing the file; this regression case passes before implementation and remains green. [class: REPOSITORY_TEST]
- [ ] Given the writer's serialization step raises `RecursionError`, expects an existing append-leg named refusal, leaves the state file unchanged, and leaves no temporary acknowledgment file behind. [class: REPOSITORY_TEST]
- [ ] Given the writer's second `read_text` call is injected to raise `UnicodeDecodeError` while the on-disk authorization bytes remain valid and unchanged, expects the existing named receipt refusal, unchanged state bytes, and no temporary acknowledgment file left behind. [class: REPOSITORY_TEST]
- [ ] Given a mixed chain with a script-verified first hop and a valid operator-acked second hop, expects the chain to verify and classification to run for the first hop only; an absent or invalid authorization for the second hop still refuses; this regression case passes before implementation and remains green. [class: REPOSITORY_TEST]
- [ ] Add `RecursionError` handling at the shared loader and writer pre-read JSON parse sites and guard serialization in the writer, mapping failures to the existing named receipt or append leg without changing authorization selection, schema, or state write ordering. Preserve the pre-replace reread's existing unreadable-byte refusal behavior. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run -> expect RED: the deep-state and serialization `RecursionError` checks fail on current code. The non-object and mixed-hop regression checks pass on current code and remain green after implementation. [class: REPOSITORY_TEST]
- [ ] Run -> expect GREEN: the focused corrections-record suite listed in Validation Commands passes. [class: REPOSITORY_TEST]

