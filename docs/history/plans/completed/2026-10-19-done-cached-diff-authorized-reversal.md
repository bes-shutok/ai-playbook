# Plan: Permit an explicitly authorized ancestor restoration

Backlog origin: docs/history/backlog/2026-10-19-done-cached-diff-authorized-reversal.md
Driving force: code-quality (carries the closeout reliability concern through explicit run, path, blob, and landing-tree contracts; this plan adds implementation machinery, so simplicity is not its force)
Plan review record: the staging series .ai-playbook/reviews/2026-10-19-plan-review-done-cached-diff-authorized-reversal-p59f84205-r*.md
Authoring claim: docs/tmp/authoring-claims/2026-10-19-done-cached-diff-authorized-reversal.md (session 01a15484-176a-70a1-814d-785fd68e1975)
Execution budget: 2.0h total, largest task 1.5h

## Terms

- Ancestor restoration: a staged file whose bytes equal a version reachable from the current commit history.
- Cached-diff guard: the commit-stage check that classifies staged declared paths and refuses ancestor-matching content reversals, with a separate passage for declared deletions.
- Declared-deletion passage: the existing cached-diff guard behavior that permits a declared path absent from the staged index as the set's own removal.
- Declared-set tree: the Git tree made from the complete staged set accepted by the existing staged-scope guard for the declared commit paths.
- Authorization argument: an explicit commit option binding the operator's authorization to one repo-relative path and expected Git blob id for the current commit invocation.
- Current done run: the newest root-confirmed marker and its nonterminal manifest classified by the existing run loader, with the live done lock owned by this active run.
- Compare-and-swap update: atomically verify captured `HEAD` identity and update its branch ref, or direct `HEAD` in detached mode, only if the captured OID still matches.
- Captured `HEAD` identity: symbolic target plus target OID, or detached state plus direct `HEAD` OID, captured before hooks run.
- Current-run tuple: the newest root-confirmed marker, its selected manifest and run id, and the live token-owned done-lock directory/token pair.
- Staged-scope guard: the existing commit check that limits accepted staged entries to declared paths while preserving its rename/copy membership behavior.
- Stale-checkout classification: the existing decision that identifies ancestor-blob debris outside the declared set.
- Revert-set classifier: the read-only classifier that identifies restores to ancestor versions and stale-checkout debris.

## Why

The cached-diff guard stops accidental restorations to old file contents, but it also stops an explicitly authorized restoration. The existing workaround adds an unrelated edit, and the declared-deletion passage covers absent paths only.

## Gist & Examples

TLDR: accept an explicit per-invocation authorization for one exact staged path while keeping unrelated reversals blocked, for code-quality.

Before (today): when a user directs restoration of a file to exact ancestor bytes, the classifier reports a reversal and the done commit stops. Adding an incidental edit lets the commit proceed but leaves unrelated churn.

After (this plan): the operator supplies an explicit authorization option with an expected blob id to the existing done commit command. The current run confirms its marker and manifest, and the landing commit uses the validated declared-set tree; every other ancestor-matching path still refuses.

Edge cases: a missing option, stale or unbound run, different or undeclared path, absent staged file, or unrelated ancestor-matching path still refuses; declared deletions continue through their existing arm.

## Outcome

The done closeout can commit one explicitly authorized exact-content restoration without weakening its protection against unrelated accidental reversals.

- The operator authorizes one repo-relative path for the current commit invocation.
- The guard requires that path's staged blob to equal the operator-supplied expected blob and confirms the exact declared-set tree after pre-update commit hooks before updating the captured ref.
- The landing preserves every other accepted staged entry, has exactly one parent at captured `HEAD`, compare-and-swaps the captured ref (branch ref or direct `HEAD` when detached), and keeps unrelated ancestor-matching paths refused.

Gate delta: add one commit protocol layer and grow the existing commit step's checked-condition/refusal surface to bind authorized path/blob to the active run, reject a pre-update hook's staged-tree change, and transactionally verify/update the captured ref; add no manifest field or dispatch pause. This is priced by the completed wrong landing reproduced in [r3 F1](.ai-playbook/reviews/2026-10-19-plan-review-done-cached-diff-authorized-reversal-p59f84205-r3.md#f1-git-can-land-a-different-blob-than-the-authorized-staged-blob): path-limited commit landed a blob different from the staged blob. The backlog origin records why the existing false positive cannot be removed globally and why current commit forms do not meet the scoped-tree contract; it is alternatives analysis, not a Rule 42 no-exit claim. Current guard-liveness ratio: total 27:39 catches:incidents; cached-diff 0:1. Catch frequency is low, limited to an authorized restoration with stale run, hook index mutation, or branch/run ownership movement; false-positive cost is to inspect, restage, and rerun; review by 2027-01-19. Run `pre-commit`, `prepare-commit-msg`, and `commit-msg` in order; preserve trusted `reference-transaction` hook phases and veto behavior during the ref transaction; run `post-commit` after success.

## Assumptions

- The commit command can select a manifest and run id independently, while setup or `--from-manifest` re-entry exports the marker, manifest, and run id. Resolve the newest root-confirmed marker and its manifest through the existing loader/classifier; require selected exports to match, reject stale or terminal runs, and verify live done-lock ownership. Require the manifest root to equal the current root. Revalidate this exact tuple and token-fenced lock after pre-update commit hooks, immediately before starting the ref transaction; trusted reference-transaction hook side effects are outside this wrapper guarantee. Basis: setup exports, `marker_confirms`, `load_run_manifest`, `classify_run_boundary`, lock status, and manifest writer.
- A Git blob id derived from the staged index is an observation, not authorization. The operator supplies the expected blob id; check it after declared staging. Capture the tree accepted by existing guards, run pre-update commit hooks in normal order, refuse if one changes the index tree, and construct one commit from that same tree with sole parent at captured `HEAD`. In one Git ref transaction, verify symbolic `HEAD` and compare-and-swap its captured branch ref; in detached mode, verify and compare-and-swap direct `HEAD` without creating a branch. Configured `reference-transaction` hooks are trusted transaction participants: preserve their standard phases and veto behavior, but the wrapper's mutation-refusal guarantee does not cover side effects performed by those hooks. Basis: current path-limited `git commit` can reread worktree bytes after the staged-blob check; a no-pathspec commit can include unrelated staged entries.
- Intent comes only from the explicit authorization argument, not from a path declaration, commit message, or classifier result. Basis: the backlog origin's Expected and rejected alternatives.
- The existing Step 3 cached-diff guard paragraph is the home for the invocation-scoped behavior; a new section would duplicate the guard decision.

Decision points requiring a grill: none remain.

## Standing constraints

- Keep unapproved content reversals refusing.
- Do not add a generic force option or a broad user-directed bypass.
- Preserve declared-deletion passage, stale-checkout classification, and unrelated-path behavior.
- Do not change the revert-set classifier's general classification contract.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: only the explicitly authorized current-run path and expected blob pass; the post-pre-update-commit-hook declared-set tree lands in a commit whose sole parent is captured `HEAD`.
- Safety: missing or mismatched authorization/run identity, changed authorized content, unrelated reversals, pre-update commit-hook scope changes, changed `HEAD` identity/OID, or stale/released/replaced run lock detected at final pre-transaction validation refuse without ref update; declared deletions remain absent. Trusted reference-transaction hooks may veto; their side effects are outside the wrapper guarantee.
- Maintainability: keep authorization invocation-local, reuse the existing staged-scope guard and normal hook configuration, and preserve the staged set it already admits.

**Done when:** exact authorized blob, run boundary, post-pre-update-hook tree and sole-parent-at-captured-HEAD, atomic symbolic/detached `HEAD` and OID verification, pre-transaction run/lock revalidation, ref-hook veto, metadata/ledger preservation, unrelated reversal, and deletion witnesses pass.

**Ship when:** none; repository-only behavior.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope.

**Production code:**
- `scripts/done_run.sh` - explicit commit authorization argument and cached-diff guard decision.
- `agents/skills/done/SKILL.md` - the Step 3 cached-diff explanation and the direct-landing advisory.

**Tests:**
- `scripts/test_done_run_wrapper.py` *(edited)*

**Plan-related extension:** change another file only when it implements a task, repairs a regression caused by plan work, or completes wiring required by an explicit must-fix. The backlog origin may be amended to record the complete fix-class no-exit alternatives required by Rule 42; that source row is removed when this plan completes. Record the reason in the review report.

**Out of scope; reject unless plan-related:**
- `scripts/revert_set_classifier.py` - its read-only ancestor classification stays unchanged.
- General done-run authorization, arbitrary content replacement, and declared-deletion behavior.
- New receipt stores, generic force flags, or unrelated closeout gates.

## Validation Commands

```bash
python3 scripts/test_done_run_wrapper.py
```

### Task 1: Bind one authorized restoration to its current-run commit tree

Context surface: this task, `## Terms`, `## Standing constraints`, and the active run marker and manifest checks.

Files:
- `scripts/done_run.sh` *(edited)*
- `agents/skills/done/SKILL.md` *(edited)*
- `scripts/test_done_run_wrapper.py` *(edited)*

Primary class anchors:
- `commit` in `scripts/done_run.sh`
- `resolve_manifest_path` in `scripts/done_run.sh`

- [x] [class: IMPLEMENTATION_REQUIRED] Add invocation-local `--authorize-ancestor-restoration <repo-relative-path> <expected-blob-id>`; intent comes only from the operator passing this option for this commit.
- [x] [class: IMPLEMENTATION_REQUIRED] Resolve run identity through the existing loader/classifier: require the newest root-confirmed marker, matching selected exports, a nonterminal manifest, and live done-lock ownership; reject stale/terminal tuples and root mismatch.
- [x] [class: IMPLEMENTATION_REQUIRED] Given a valid current run and one declared ancestor-restoration path, accept `--authorize-ancestor-restoration <repo-relative-path> <expected-blob-id>` only when its staged blob equals the operator-supplied expected blob; refuse wrong blob ids before ref update.
- [x] [class: IMPLEMENTATION_REQUIRED] Refuse without ref update on stale/terminal run, unowned lock, or mismatched marker, manifest, run id, root, or override.
- [x] [class: IMPLEMENTATION_REQUIRED] After existing content guards pass, record the accepted staged tree; invoke `pre-commit`, `prepare-commit-msg`, and `commit-msg` in Git order with normal arguments/environment/message handling. A hook failure or any index-tree change refuses before ref or ledger update.
- [x] [class: IMPLEMENTATION_REQUIRED] Capture symbolic `HEAD` target and OID, or detached state and direct `HEAD` OID, before hooks. In one Git ref transaction atomically verify identity and compare-and-swap the captured branch ref or direct `HEAD`; detached mode creates no branch.
- [x] [class: IMPLEMENTATION_REQUIRED] After pre-update commit hooks and immediately before ref transaction, revalidate the exact current-run tuple and same live token-owned lock directory/token; refuse if marker, manifest, run id, lock owner/token changed, disappeared, or became terminal. Configured reference-transaction hooks are trusted; preserve their standard phases/veto behavior, with no wrapper guarantee for their side effects.
- [x] [class: IMPLEMENTATION_REQUIRED] Build one commit from the unchanged tree with sole parent at captured `HEAD`, without rereading worktree bytes or persisting/reinferring authorization from manifest, `--stage`, message, or classifier. Preserve hook args/order, message, identities, signing, and owned-commit ledger; after success invoke `post-commit` on new HEAD, whose failure cannot undo the commit.
- [x] [class: IMPLEMENTATION_REQUIRED] Refuse without captured-ref change if expected blob, accepted tree, staged scope, `HEAD` identity/OID, or current-run lock/tuple mismatch is detected before the ref transaction; trusted ref-hook side effects are excluded.
- [x] [class: IMPLEMENTATION_REQUIRED] Update the Step 3 cached-diff paragraph with the exact argument/path/blob binding.
- [x] [class: IMPLEMENTATION_REQUIRED] Remove the direct-landing advisory's incident parenthetical to pay for the Step 3 text growth; preserve its warning behavior and measurement rule.
- [x] [class: REPOSITORY_TEST] Matching run/path/blob lands exactly; mismatched marker, manifest, run ID, root, or overrides; invalid authorization; stale/terminal/unowned run; or unrelated reversal refuses before ref/ledger update.
- [x] [class: REPOSITORY_TEST] Hook tree/scope changes refuse; worktree edits do not substitute staged bytes. After pre-hooks, same-OID HEAD switch, tip move, lock replacement, or run-tuple change refuses; transaction verifies symbolic HEAD and ref OID.
- [x] [class: REPOSITORY_TEST] Attached and detached commits have sole parent at prior HEAD; detached CAS updates direct HEAD without a branch. Probes assert commit-hook arguments/environment/message and reference-transaction phases; post-commit gets no args and sees new HEAD. Ref veto blocks landing; refusals skip post-commit; trusted ref-hook side effects are out of scope.
- [x] [class: REPOSITORY_TEST] Landing preserves message and configured identity/signing, records its OID once in the active ledger, and keeps declared deletions/entries scoped; the listed wrapper suite passes.
- [x] [class: IMPLEMENTATION_REQUIRED] Commit: `feat: authorize one exact restoration per done commit`
