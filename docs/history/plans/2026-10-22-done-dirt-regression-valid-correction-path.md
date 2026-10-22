# Plan: Done dirt-regression gate supports necessary corrections

Backlog origin: `docs/history/backlog/2026-10-20-done-dirt-regression-correction-block.md`
Driving force: code-quality
Plan review record: `.ai-playbook/reviews/2026-10-22-plan-review-done-dirt-regression-valid-correction-path-p16b9dca3-r*.md`
Execution budget: 2.5h total, largest task 1.0h
Authoring claim: `docs/tmp/authoring-claims/2026-10-20-done-dirt-regression-correction-block.md` (session `01a1638f-189d-7b02-9cf8-0990eb6f3dfd`)

## Terms

- **Dirt-regression gate**: the done closeout check that refuses restored base-era text over content added after the merge base.
- **Base-era text**: file content present at the merge base.
- **HEAD-gained content**: file content added after the merge base and present at HEAD.
- **Staged blob**: the exact Git object for a path in the index that the commit would record.
- **Captured commit tree**: the immutable Git tree object the done runner builds and lands as the commit's content.
- **Live run tuple**: the current done run's root-confirmed marker, selected exports, run identifier, nonterminal manifest, and owned done-lock token.
- **Correction set**: the finite mapping from each path in one user-directed correction to that path's expected staged blob.
- **Invocation authorization**: one explicit authorization for a correction set and its live run tuple, used only in the current done invocation.

## Why

The dirt-regression gate correctly caught accidental merge-lock restoration, but it also refused a necessary user-directed contract correction spanning several files. The done flow needs a narrow recovery path that preserves the accidental-reversion catch and lets that complete correction land together.

## Gist & Examples

TLDR: Allow one exact, invocation-scoped correction set through the dirt-regression gate while preserving its accidental-reversion protection.

**Before (today):** the gate refuses both accidental restoration and necessary corrections that restore exact base text. The observed identifier-contract correction touched an API schema, a migration, tests, and an RFC; a one-file fixture cannot complete it. Arbitrary same-hunk prose adds unrelated churn, while history editing cannot reliably correct shared or already-landed changes.

**After (planned):** primary-repository commits share one captured-tree gate. A live-run path/blob set authorizes only exact correction regressions; the runner verifies each blob and reports the captured branch if checkout races after its final check.

**Example:** the identifier-prefix correction spans schema, migration, tests, and RFC. The run authorizes those exact staged blobs; stale, changed, malformed, or unrelated regressions still refuse.

## Outcome

The primary-repository closeout can land a necessary multi-file base-text correction while retaining the dirt-regression gate's accidental-reversion protection.

- The witnessed merge-lock and reverse-squash regressions remain refused unless their exact paths and staged blobs are explicitly included in the user-directed correction set.
- A user-directed multi-file correction can pass only for its finite exact path/blob mapping bound to the live run.
- Unmatched regressions, changed blobs, stale or malformed authorizations, and every other closeout guard retain their refusing behavior.
- Attached `HEAD` pins the branch/OID captured at tree creation. An observed switch refuses; a later checkout cannot retarget the commit. Report the captured destination and ledger entry.

Gate delta: permit exact invocation-bound correction blobs in primary-repository dirt classification; retain the gate for unmatched paths. Removal loses independent merge-lock and reverse-squash protection; text heuristics cannot distinguish valid corrections from accidental restoration. Reshaping adds churn; persistent exceptions or general skips add state. The runner binds the finite path/blob set to the live run and captured tree; the classifier returns per-path outcomes. Ordinary and authorized primary-repository commits share one captured-tree gate. Capture branch/OID, recheck before update, then CAS only that branch. A later checkout may leave `HEAD` elsewhere but cannot redirect the commit; report the destination. Run post-commit after success against actual `HEAD`. Preserve hook order, arguments, and message edits; detected pre-update index changes refuse. Side-repository commits are out of scope. Cached-diff authorization stays separate.

## Assumptions

- assume the authorization is supplied only for the current done invocation and covers the complete user-directed correction set as exact path/blob pairs; basis: user selected an invocation-bound path/blob authorization, and the backlog requires a multi-file correction.
- assume every authorized path still passes the other closeout guards and is revalidated against the captured commit tree; basis: the origin's integrity requirement and the existing run-bound authorization pattern.

Decision receipt: the user replied "sure" to the recommendation for a one-invocation authorization bound to an exact path and staged blob while keeping the dirt gate active, 2026-10-22. The correction set extends that exact binding to each path because the origin documents one correction across several contract-bearing files; no user-intent inference or broad allowlist is part of the choice.

Decision points requiring a grill: none remain.

## Standing constraints

- Keep existing guards active; authorize exact paths/blobs only for primary-repository landing. Side-repository commits are out of scope.
- Do not add a persistent allowlist, general skip, second gate, or standing approval ceremony.
- Keep cached-diff authorization separate; neither authorization can satisfy or bypass the other guard.
- Revalidate the live run tuple and each exact staged blob in the captured commit tree before the landing commit.
- Preserve the dirt gate's existing `--base <commit> -- <paths...>` worktree invocation for maintenance merge callers; done commits pass their captured tree explicitly without changing the existing CLI mode.
- In attached mode, pin captured branch/OID, recheck before CAS, and report that destination; a moved branch refuses before ledger update.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the original accidental reversion still refuses, while the complete precisely authorized correction set passes.
- Isolation: wrong or undeclared path, wrong or changed blob, stale run, duplicate entry, malformed set, and any unrelated regression refuse without committing.
- Simplicity: one finite mapping uses a shared captured-tree landing flow for authorized and ordinary commits, removes the false-positive refusal for explicitly directed corrections, and adds no persistent authorization state or separate gate.

**Done when:**
- The dirt-gate and done-runner test suites cover the original reversion, every path in a valid multi-file correction set, every authorization mismatch, and an unrelated regressive path.
- Ordinary primary-repository commits run the gate once on the captured tree; unauthorized reversion refuses and a clean commit lands from it.
- If the primary worktree changes after capture, the gate still classifies the captured tree; its regression refuses even if the worktree appears clean.
- Primary-repository hooks retain Git order/arguments; composed messages and commit-msg edits land. Hook failures or detected index edits refuse before ref/ledger update. Post-commit runs after success and sees actual `HEAD`, including after a checkout race.
- An authorized-path mutation after initial authorization binding but before tree capture refuses, with the wrapper recording the captured tree and exactly one dirt-gate invocation.
- Authorized indeterminate and tool-error classifier outcomes refuse without a landing commit.
- Tests prove dirt-correction authorization cannot satisfy the cached-diff guard and cached-diff authorization cannot satisfy the dirt-regression gate.
- Wrapper fixtures clear Git repository and index selectors so tests operate only on their temporary repositories.
- Wrapper setup, helper Git calls, and runner calls use fixture-scoped config with system config disabled and ambient Git config overrides cleared.
- The machinery inventory check, landing sweep, and plan readiness check pass.
- The done procedure separates authorizations and documents primary-repo tree, branch-race, and hook behavior.

**Ship when:** No external release or operations prerequisite is identified; the observable repository closure evidence is the landed commit on the repository base branch.

## Review Scope

**Explicit must-fix:**

**Production code:**
- `scripts/done_run.sh`
- `scripts/dirt_regression_gate.py`

**Tests:**
- `scripts/test_dirt_regression_gate.py`
- `scripts/test_done_run_wrapper.py`
- `scripts/test_machinery_inventory.py`

**Operator procedure and machinery record:**
- `agents/skills/done/SKILL.md`
- `scripts/machinery_registry.json`

**Plan-related extension:** Include a finding on another path only when it is causally required to implement or validate the exact correction-set authorization, preserve a changed closeout invariant, or repair a regression introduced by this work.

**Out of scope; reject unless plan-related:**
- `scripts/staged_scope_guard.py`; its existing guard contract is preserved and not redesigned.
- `scripts/cached_diff_guard.py`; its authorization belongs to a separate earlier stage and is not reused for the dirt-regression gate.
- Historical incident and completed-plan records; read-only evidence for this change.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_dirt_regression_gate.py'
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_done_run_wrapper.py'
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_machinery_inventory.py'
python3 scripts/machinery_inventory.py --check
bash scripts/done_sweep_gates.sh landing
python3 scripts/doc_registry_validator.py validate
python3 scripts/plan_readiness.py docs/history/plans/2026-10-22-done-dirt-regression-valid-correction-path.md
```

### Task 1: Add the narrowly bound correction-set path

Context surface: the plan's Terms and `## Standing constraints`; read the source procedure and current guard ladder before editing.

Files:
- `scripts/done_run.sh`
- `scripts/dirt_regression_gate.py`
- `scripts/test_dirt_regression_gate.py`
- `scripts/test_done_run_wrapper.py`

Primary class anchors:
- `cmd_commit` in `scripts/done_run.sh`
- `classify_path` in `scripts/dirt_regression_gate.py`

- [ ] `cmd_commit` accepts one explicit finite mapping of unique declared paths to expected staged blobs, bound to operator direction and the live run tuple; given an undeclared path or any other run, expects refusal before commit [class: IMPLEMENTATION_REQUIRED]
- [ ] `classify_path` reads the immutable captured tree and reports a pure per-path result; given any indeterminate or tool-error outcome, expects the runner to refuse [class: IMPLEMENTATION_REQUIRED]
- [ ] Keep the worktree-based `--base <commit> -- <paths...>` CLI for other callers; done passes its captured tree [class: IMPLEMENTATION_REQUIRED]
- [ ] Capture attached branch/OID, recheck before update, CAS only that branch, and report its destination [class: IMPLEMENTATION_REQUIRED]
- [ ] Route primary-repository commits through one captured-tree boundary; preserve hooks/message/ledger and refuse detected pre-update index-tree mutations [class: IMPLEMENTATION_REQUIRED]
- [ ] Exact live correction blobs authorize only matching path regressions; other guards remain active [class: REPOSITORY_TEST]
- [ ] Given a mismatched or changed blob, stale run tuple, duplicate or undeclared path, malformed mapping, or missing authorization, expects a named refusal and no landing commit [class: REPOSITORY_TEST]
- [ ] Given the witnessed accidental merge-lock restoration without a matching correction-set authorization, expects the original dirt-regression refusal [class: REPOSITORY_TEST]
- [ ] Given dirt-only authorization for a cached-diff regression, and cached-diff-only authorization for a dirt regression, expects each owning guard to refuse with no commit [class: REPOSITORY_TEST]
- [ ] Capture the final primary-repository tree before dirt classification; refuse unrelated regressions or mismatched authorized blobs in it [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the existing gate once at the shared primary-repository tree boundary; regressions refuse before ref update [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a captured-tree regression followed by a worktree-only cleanup before classification, expect the gate to refuse based on the captured tree [class: REPOSITORY_TEST]
- [ ] Given an unrelated-path mutation before capture or during a pre-update hook, expect refusal; after the final tree check, expect later mutations to remain staged and excluded [class: REPOSITORY_TEST]
- [ ] Given an authorized-path mutation after binding but before capture, expect one gate call on the captured tree and refusal with HEAD and ledger unchanged [class: REPOSITORY_TEST]
- [ ] Given an authorized classifier result of indeterminate or tool-error, expect a wrapper witness to refuse without a landing commit [class: REPOSITORY_TEST]
- [ ] Given the legacy worktree CLI call, expect maintenance merge classification to remain available [class: REPOSITORY_TEST]
- [ ] Given checkout switches A to B after final check, expect only A to advance, B/`HEAD` unchanged, output and ledger naming A, and post-commit observing B [class: REPOSITORY_TEST]
- [ ] Given captured branch A moves, expect CAS refusal without ledger append; a switch observed before final check also refuses [class: REPOSITORY_TEST]
- [ ] Given fixture setup, helper, and runner Git calls, expect system/global host config and Git config overrides to be isolated to fixture config [class: REPOSITORY_TEST]
- [ ] Verify hook order/arguments/message edits; failures or index mutations leave ref/ledger unchanged; post-commit runs after landing and race fixture records its `HEAD` [class: REPOSITORY_TEST]
- [ ] Show the regression witness fail before implementation and pass before Task 1's commit [class: REPOSITORY_TEST]
- [ ] Keep live-run tuple and correction-set enforcement in `cmd_commit`; given any classifier result other than a path regression, expect no authorization to suppress it [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a host Git selector in the wrapper-test environment, expect the fixture harness to clear it and operate only on its temporary repository [class: REPOSITORY_TEST]
- [ ] Commit: `fix: authorize a necessary dirt correction set per done run` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Document and register the authorization limits

Context surface: the plan's Terms and `## Standing constraints`; the authorization must remain distinct from the cached-diff exception.

Files:
- `agents/skills/done/SKILL.md`
- `scripts/machinery_registry.json`
- `scripts/test_machinery_inventory.py`

- [ ] The done procedure explains one explicit finite path/blob mapping, live-run binding, captured-tree validation, and that all unmatched regressions still refuse [class: IMPLEMENTATION_REQUIRED]
- [ ] Update Step 3 for primary-repository tree gating, captured-branch reporting, post-commit's actual `HEAD`, hook-index refusal, and side-repo exclusion [class: IMPLEMENTATION_REQUIRED]
- [ ] The done procedure states that cached-diff authorization is separate and neither authorization lifts the other guard [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the operator-procedure edit, expect equivalent bytes of duplicated operative wording to be removed from `agents/skills/done/SKILL.md` in the same change [class: IMPLEMENTATION_REQUIRED]
- [ ] The existing dirt-regression machinery record cites the valid-correction incident, one confirmed valid correction with catch frequency still unknown, the false-positive cost of blocked closeout and recovery work, review date 2027-01-20, and retirement only of the invocation-authorization path if no further valid-correction refusal occurs while retaining the gate's independent accidental-reversion protection [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the updated machinery record, expect the machinery inventory check to pass without adding another gate or persistent authorization record [class: REPOSITORY_TEST]
- [ ] Commit: `docs: define the done dirt correction authorization` [class: IMPLEMENTATION_REQUIRED]
