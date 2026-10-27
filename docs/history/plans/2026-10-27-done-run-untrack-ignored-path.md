# Plan: Add an explicit untrack path to the done runner

Backlog origin: docs/history/backlog/2026-10-27-done-run-untrack-ignored-path.md
Driving force: efficiency + code-quality
Plan review record: .ai-playbook/reviews/2026-10-27-plan-review-done-run-untrack-ignored-path-r*.md
Execution budget: 2h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-27-done-run-untrack-ignored-path.md (session 01a17c5c-b1b6-7c02-8203-5bc9bf7f9ab3)

## Terms

- **Index-only deletion:** a path tracked by `HEAD` that has been removed from the index but remains in the working tree.
- **Untrack declaration:** the new `--untrack <path>` operand that declares a verified index-only deletion for the done runner's landing.

## Why

The done runner checks whether a declared path is ignored before it recognizes an already-staged deletion. A consumer can use `git rm --cached` to preserve a local-only file, but `--stage <path>` reports it as ignored and omits the deletion from the declared set, so the closeout cannot land the intended tree.

## Gist & Examples

TLDR: Add a narrow untrack declaration for ignored-path index deletions, improving closeout efficiency and staging safety.

Before: `git rm --cached -- local.properties` removes the tracked entry from the index while retaining the local file, but `done_run.sh commit --stage local.properties` rejects the ignored path and cannot land the deletion.

After: `done_run.sh commit --untrack local.properties` accepts the path only after checking the `HEAD` entry, absent index entry, retained ignored worktree file, and staged-index safety; it lands the deletion without adding ignored contents.

Edge cases: An untracked path, a still-indexed path, a missing local copy, a path that is not ignored, or any changed staged ignored blob is refused; ordinary `--stage` behavior remains unchanged.

## Outcome

Consumers can remove a tracked local-only file from the repository while keeping its ignored working copy. The operator stages the index-only deletion with `git rm --cached`, declares that intent with `--untrack`, and the runner verifies the deletion before including it in the landing set.

- The declared path must exist in `HEAD`, be absent from the index, remain present in the working tree, and match an ignore rule.
- A run using `--untrack` refuses if an index entry changed from `HEAD` carries an ignored blob, including a force-added ignored file; unchanged tracked entries are outside the staged delta.
- The runner never force-adds an ignored file and never deletes the working-tree copy or changes ignore rules.
- Read-only preflight runs before runner-owned index changes, ledger appends, or other staging. A preflight refusal preserves `HEAD`, the index, and relevant working-tree bytes.
- Ignore matching is index-independent and scoped to index entries changed relative to `HEAD` that carry blobs; the intended deletion entries are allowed. Unchanged tracked files do not trigger refusal.
- After `git write-tree`, the runner verifies the captured tree still omits every untrack target and has no ignored blob among entries changed from `HEAD`; it commits only that validated tree. A late captured-tree refusal creates no commit or ref update, but does not undo caller or runner staging already performed.
- `--stage` continues to report and skip ignored paths as it does now.

The option-specific refusal protects against accidentally landing ignored file contents during the untrack operation. Its incident is [the originating backlog item](../backlog/2026-10-27-done-run-untrack-ignored-path.md), which records that ignored files must not be force-added as part of this repair. Expected catch frequency is rare: only when an invocation with `--untrack` has a changed ignored blob staged, or a target fails its exact-path checks. The false-positive cost is that the caller must remove staged ignored content and retry. Review this refusal boundary by 2027-01-27.

The refusal cannot offer a sanctioned exit that accepts the ignored blob without violating the origin's no-ignored-content constraint. Automatically unstaging or deleting content would mutate caller-owned index or worktree state, and removing the check would permit ignored contents into the commit; neither is a safe simpler flow. The origin offers a narrow explicit declaration, not an exception for ignored blobs.

Gate delta: add only the option-specific refusal required to protect this explicit `--untrack` operation; no scheduler or repository-wide gate is added. Existing landing and staged-scope guards remain in force.

## Assumptions

- The caller runs `git rm --cached -- <path>` before invoking `--untrack`; basis: the origin describes this as the current recovery action, and the narrow declaration avoids moving Git index mutation into the runner.
- `--untrack` is repeatable for individual file paths; basis: the runner already accepts repeated path operands, while the origin asks for an exact-path operation and does not request recursive directory handling.
- Preflight examines index entries changed from `HEAD` that carry blobs when `--untrack` is present; basis: the origin forbids landing ignored contents, while unchanged tracked files are outside the landing delta. Use index-independent ignore matching (for example, `git check-ignore --no-index`) because ordinary matching omits indexed paths. Revalidate changed entries in the exact tree returned by `git write-tree` to close the direct-index-mutation race; do not add another lock.
- Maintenance-selected decision receipt: use a separate `--untrack` declaration for pre-staged index-only deletions; source: the backlog's Suggested fix, current staging loop, and existing ignored-path regression; date: 2026-10-27; affected sections: Outcome, Evaluation Criteria, Tasks, Validation Commands.
- Sources inspected: `docs/history/backlog/2026-10-27-done-run-untrack-ignored-path.md`; `scripts/done_run.sh`; `scripts/test_done_run_wrapper.py`; `agents/skills/done/SKILL.md`.
Decision points requiring a grill: Use a separate `--untrack` declaration while keeping `--stage` refusal unchanged; source: origin Suggested fix and staging-loop behavior; date: 2026-10-27; affected sections: Outcome, Assumptions, Tasks.

## Evaluation Criteria

- **Safe deletion:** a valid declaration lands the index deletion and leaves the ignored working-tree copy and ignore rule intact.
- **No ignored content:** index-independent checks refuse changed ignored blobs, including concurrent additions visible in the captured tree, while unchanged ignored tracked files do not block the operation.
- **Boundary:** invalid `--untrack` paths are refused, while existing `--stage` ignored-path behavior and ordinary declared-path handling remain unchanged.
- **Documentation:** the done skill explains the `git rm --cached` plus `--untrack` sequence and its constraints.

**Done when:** focused wrapper regressions cover successful untracking, the exact resulting tree, retained local copy and ignore status, invalid declarations, preflight refusal-state preservation, unchanged ignored tracked files, and a late captured-tree refusal with no commit or ref update; the documented wrapper suite, no-em-dash scan, and public-hygiene scan pass for changed files.

**Ship when:** this plan lands and its backlog origin is marked covered with the required disposition during plan completion.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope.

**Production code:**
- `scripts/done_run.sh` (the explicit untrack operand, usage text, validation, and declared-set integration only) (Task 1)

**Tests:**
- `scripts/test_done_run_wrapper.py` (focused wrapper behavior and safety cases only) (Task 1)

**Documentation:**
- `agents/skills/done/SKILL.md` (the commit invocation and ignored-path staging guidance only) (Task 2)

**Plan-related extension:** other changes are in scope only when required to preserve the explicit untrack contract, existing `--stage` behavior, or the exact landing tree.

**Out of scope:**
- General changes to `--stage`, force-add behavior, ignore rules, or working-tree cleanup.
- Changes to the done lock, landing sweep, staged-scope guard, or other closeout gates.
- Directory-recursive untracking, new configuration, metrics, or a scheduler/maintenance gate.

## Validation Commands

Run from the repository root:

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_done_run_wrapper.py'
bash scripts/check-no-em-dash.sh touched
bash scripts/scan-public-hygiene.sh --files scripts/done_run.sh scripts/test_done_run_wrapper.py agents/skills/done/SKILL.md
```

The regression matrix must verify that `git rm --cached` followed by `--untrack` lands only the index deletion and preserves the local ignored file; reject a path absent from `HEAD`, a path still in the index, a missing worktree copy, and a path that does not match ignore rules; refuse changed index entries relative to `HEAD` that carry ignored blobs using index-independent matching, while allowing unchanged ignored tracked files; and confirm that an ignored path passed through `--stage` is still reported and never staged. Include a force-added ignored blob already in the index but declared through `--stage`. Snapshot `HEAD`, index tree/entries, and relevant working-tree bytes for preflight refusals and assert they are unchanged. Use separate late-race cases for the two captured-tree invariants: re-add an `--untrack` target after preflight to exercise target absence; then force-add an ignored non-target path passed via `--stage` after preflight but before stage-operand processing and tree capture, so the runner declares it and the changed-blob check, not the target or foreign-path check, refuses. Assert no commit or ref update, retain the injected caller index state and ordinary explicit staging, and preserve the working-tree copy.

### Task 1: Add the explicit untrack declaration and safety checks

Context surface: Terms, Outcome, Assumptions, Evaluation Criteria; the origin's Problem, Evidence, and Suggested fix; the existing ignored-path staging loop and wrapper regression.

Files:
- `scripts/done_run.sh`
- `scripts/test_done_run_wrapper.py`

Primary class anchors:
- `cmd_commit` in `scripts/done_run.sh`
- `DoneRunDeclaredStageChannelTest` in `scripts/test_done_run_wrapper.py`

- [ ] Parse repeatable `--untrack <path>` operands as a separate explicit declaration and update the runner `Usage` block to document it; leave `--stage` semantics unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run read-only preflight before any runner-owned index mutation, ledger append, or staging. Accept only paths tracked by `HEAD`, absent from the index, present in the working tree, and matched by an index-independent ignore check; include accepted deletion paths in the declared set without adding their contents. [class: IMPLEMENTATION_REQUIRED]
- [ ] When `--untrack` is present, refuse if any index entry changed relative to `HEAD` that carries a blob matches an ignore rule under index-independent matching; allow intended deletions and unchanged ignored tracked files, and report the offending path. [class: IMPLEMENTATION_REQUIRED]
- [ ] After `git write-tree`, validate the exact captured tree: all untrack targets remain absent and no changed entry carrying a blob matches an ignore rule. Refuse any mismatch before commit or ref update; do not undo concurrent caller mutation or ordinary staging already performed. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add wrapper coverage for valid deletion, retained ignored file and rule, exact committed tree, invalid path conditions, unchanged ignored tracked files, and force-added ignored blobs passed through `--stage`. [class: REPOSITORY_TEST]
- [ ] Snapshot state around preflight refusals; separately reinsert an `--untrack` target after preflight and force-add an ignored non-target `--stage` path after preflight but before stage-operand processing and tree capture. Verify the target check and changed-blob scan refuse their respective cases without commit or ref update, preserving the injected index state and worktree copy. [class: REPOSITORY_TEST]
- [ ] Preserve the existing `--stage` ignored-path regression and all ordinary staging behavior. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: support explicit ignored-path untracking` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Document the untrack sequence

Context surface: Terms, Outcome, Evaluation Criteria; the done skill's commit invocation and ignored-path staging guidance.

Files:
- `agents/skills/done/SKILL.md`

- [ ] Document the `git rm --cached` then explicit untrack sequence, including the path checks, changed staged ignored-blob refusal, and retained working-tree file. [class: IMPLEMENTATION_REQUIRED]
- [ ] Keep the documented `--stage` ignored-path behavior explicit and unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: document done-run untrack path` [class: IMPLEMENTATION_REQUIRED]
