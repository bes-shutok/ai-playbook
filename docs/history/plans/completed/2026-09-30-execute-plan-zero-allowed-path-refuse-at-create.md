# Create must refuse a zero-allowed-path task before seeding the launch wedge

[github: https://github.com/admitriev/ai-playbook] Origin: docs/history/backlog/2026-09-30-execute-plan-zero-allowed-path-task-launch-wedge.md

Plan review: docs/reviews/2026-09-30-plan-review-execute-plan-zero-allowed-path-refuse-at-create-r3.md (the highest round of the r1-r3 staging series; r3 verdict ready=yes, zero blocking)

## Gist TLDR

The driver's `create` operation seeds a task with an empty `allowed_paths` list as launchable state, but the launch envelope's worker-role contract (`_worker_role_contract`) returns `None` for such a task whenever evidence enforcement is on - and `create` always turns enforcement on. Every `continue` for that task then refuses with "canonical single-task worker role is missing or mismatched", the refusal is read-only, and no driver operation replaces the immutable contract on an unlaunched claim: the run wedges. Two same-day executions in this repository hit exactly this with verification-only tasks whose plan section declared no `Files:`. Fix: `create`'s pre-seed task validation refuses an empty allowed-paths list with an actionable error naming the task and the sanctioned verification-only remedy (declare the file the task's verification commands execute; it is read by gates, never edited). The two boundaries align at seed time instead of diverging at the first launch.

## Outcome + Gate delta

Witnessed 2026-09-30 twice (residual-exit same-day ordering execution, landed 10dd0ec9, Task 3 "Files: - none (verification only)"; em-dash residuals canary execution, superseded by peer landing abe72523, Task 4 with no Files section). Both runs wedged at the first `continue` after a `create` that reported success, and both had to exit through the outside-the-driver path: a non-semantic plan correction giving the task a real `Files:` entry, a focused re-cert review, and a fresh session re-seed replaying done receipts - three manual disciplines per occurrence.

The mechanical shape after this plan: the `create` operation's pre-seed validation loop (which today already requires non-empty `required_criteria` and `verification_commands` per task, and resolves every declared allowed path through the fail-closed path policy) gains one more conjunct: a task whose `allowed_paths`/`Files:` derivation is absent or empty raises `ValueError` before any manifest bytes are written. The error names the task id and the remedy verbatim so the plan author can fix the plan section and re-run create without consulting the runtime source. No launch-path behavior changes: `_worker_role_contract` stays exactly as it is, because after this plan the driver never holds a seeded claim whose task could make it return `None` for the empty-paths reason.

Out of scope: admitting a verification-only contract shape at the launch envelope (the origin item's acceptable alternative - it loosens the worker-role contract for a shape the repository's own plan discipline can express as a declared read path), recovery operations for already-seeded zero-path claims (the wedge leaves the manifest recoverable today via the documented re-seed path, and after this plan new occurrences do not arise), and any change to plan-parsing defaults.

## Terms

- **Zero-allowed-path task**: a task whose `allowed_paths` (canonical) derivation from the plan section is absent or resolves to an empty sequence.
- **Verification-only task**: a task whose section declares commands and criteria but no `Files:`; historically written as "Files: - none (verification only)" or by omitting the list.
- **Launch wedge**: the state where `claim_next_task` succeeds but every `launch`/`continue` refuses with "canonical single-task worker role is missing or mismatched"; the claim never reaches the launched hold that `recover-evidence-contract` requires.
- **Pre-seed validation loop**: the per-task validation inside the `create` operation before `create_manifest` is called, inside the manifest lock.

## Assumptions

- The refusal belongs in `create` (the origin item's preferred remedy) because `create` unconditionally sets `evidence_enforcement: True` on the manifest it seeds, so the launch envelope's non-empty-allowed-paths conjunct is always live for driver-created manifests; accepting the seed is what manufactures the wedge.
- The error message carries the remedy because both witnessed recoveries required the plan author to invent the classification ("the added path is never exercised") that the driver can state mechanically: the verification commands execute some file in the repository; that file is the task's declared allowed path, and declaring it grants no write authorization the gates do not already exercise.
- A task may still legitimately declare paths that fail `_safe_relative_path` resolution - that existing refusal is unchanged; this plan only closes the empty-list case the existing loop never inspects.

Decision points requiring a grill: none - the origin item's Expected section prescribes the preferred remedy verbatim; the validation-loop placement and the error-message contract were fixed by reading the create operation's existing conjunct structure so the new check is one more line in an established fail-closed sequence.

### Task 1 - Create refuses a zero-allowed-path task before seeding

- [ ] In `scripts/execute_plan_runtime.py`, the `create` operation's pre-seed per-task validation loop (the loop that today runs `_safe_relative_path` over each declared entry and then requires non-empty `required_criteria` and `verification_commands`): after the existing entry-resolution loop, add an empty-list check - when `task.get("allowed_paths", task.get("files", ()))` is absent or empty, raise `ValueError` with a message that names the task id, states that the launch envelope's worker-role contract refuses an empty allowed-paths list under evidence enforcement, and names the remedy (declare the file the task's verification commands execute as its allowed path; the gates read it, no one edits it). No other validation conjunct changes. [class: IMPLEMENTATION_REQUIRED]

### Task 2 - Regression coverage

- [ ] In `scripts/test_execute_plan_runtime.py`, add a RED-today test that calls the create operation (the suite's established create-manifest helper path) with a task dict carrying non-empty `required_criteria` and `verification_commands` but an empty `allowed_paths` list, and asserts the refusal: `ValueError` raised, message contains the task id, and no manifest file exists afterwards. Add a second test asserting a task with a real (resolvable) allowed path still creates successfully, so the new conjunct is proven not to over-refuse. Run both against the unmodified runtime first and verify the first fails before applying Task 1. [class: REPOSITORY_TEST]
- [ ] In the same file, update the two existing create-seeding fixtures whose task dicts carry no `allowed_paths`/`files` key, so the new conjunct does not break them: `test_create_operation_seeds_manifest` (its `task-1`) and `test_create_operation_fails_closed_under_concurrent_create` (whose task must keep reaching the manifest lock so the "held by another owner" assertion still fires - the new conjunct runs in the pre-seed loop before the lock). Give each fixture task a resolvable allowed path (the suite's established `allowed_paths: ["task-1.txt"]` pattern; path policy validates shape, not file existence). No assertion of either test changes. [class: REPOSITORY_TEST]

### Task 3 - Validation

- [ ] All checks in Validation Commands pass from the worktree root with the runtime suite runner (`TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"` if present, else ambient `python3 -m unittest`). [class: REPOSITORY_TEST]

## Evaluation Criteria

- `create` refuses a task with an empty allowed-paths list before any manifest is written, with an error naming the task id and the verification-only remedy.
- A task with a resolvable non-empty allowed path still creates successfully; the existing criteria/commands/path-resolution refusals are unchanged.
- The full `scripts/test_execute_plan_runtime.py` suite passes with a checked exit code.

## Review Scope

Files: `scripts/execute_plan_runtime.py` (the `create` operation's pre-seed validation loop only), `scripts/test_execute_plan_runtime.py` (the new tests and the two create-seeding fixture re-paths named in Task 2 only). Contract files referenced read-only: origin backlog item, `_worker_role_contract` (launch envelope, unchanged), the completed residual-exit ordering plan (witness one).

## Validation Commands

Run from the worktree root:

1. `grep -n "empty allowed-paths" scripts/execute_plan_runtime.py` - the refusal exists in the create validation region.
2. `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_execute_plan_runtime.py -q` - full runtime suite green with a live exit code.
3. `git diff main --stat -- scripts/execute_plan_runtime.py scripts/test_execute_plan_runtime.py` - only the two in-scope files changed.
