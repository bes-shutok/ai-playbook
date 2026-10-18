# Plan: the docs-branch primary-mode selector stops warning on empty arrays and never silently degrades the declared no-worktree mode

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-05-docs-branch-empty-array-test-warning.md`
- `docs/history/backlog/2026-10-05-docs-branch-no-worktree-helper-deployment.md`

Driving force: simplicity (outside the five driving principles justification: both defects are consumer-facing reliability wounds on one shared selector block, witnessed the same day in consumer runs; the empty-array warning makes a healthy sync look broken and the silent degrade quietly discards the consumer's declared execution mode, so the pair lands together under simplicity's user-economy lens; park-triage would take neither: both are small, both are witnessed, and they share the file seam)
Plan review record: the staging series docs/history/reviews/2026-10-06-plan-review-docs-branch-primary-sync-selector-fixes-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 1h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-06-docs-branch-primary-sync-selector-fixes.md (session sess_72b1f155-dee1-439a-916f-fcc26d801c74)

## Terms

- Step 2 selector: the docs-branch skill's Step 2 `case` block that reads `worktree_policy` from the project facts and routes the sync to the worktree path or the no-worktree plumbing mode.
- Primary declaration: a project facts block carrying `worktree_policy = "primary"`, the declared no-worktree exception.
- Plumbing mode: the no-worktree sync through `scripts/docs_branch_sync_noworktree.sh` (temporary index, `commit-tree`, compare-and-swap `update-ref`), which keeps the live checkout's HEAD, index, and shadow-path bytes byte-identical.
- Silent degrade: today's behavior when the plumbing helper resolves to no existing file: a `WARN: no-worktree plumbing script not found; falling back to the worktree path` line to stderr and the sync proceeds on the worktree path, discarding the declared mode.
- Canonical skills root: an optional caller-provided root directory (`DOCS_BRANCH_SKILLS_ROOT`) naming the checkout whose `scripts/` carries the helper, probed after the deployed home and before any refusal.
- Bash 3.2 empty-array expansion: the witnessed behavior that `"${a[@]+x}"` inside a POSIX `[` test with an empty declared array makes the left operand disappear and the shell print `[: =: unary operator expected` while the test still fails.
- Extraction test: a test that extracts the live selector lines from the skill bytes by pinned anchors and executes them under the host bash, so the suite tests the shipped text rather than a copy.

## Why

Two witnessed consumer defects share the Step 2 selector block. First, the optional `EXTRA_SHADOW_DIRS` export is gated by `if [ "${EXTRA_SHADOW_DIRS[@]+x}" = "x" ]`; under the supported Bash 3.2 an empty declared array makes the left operand vanish, the shell prints `[: =: unary operator expected`, and a healthy empty configuration reads as a shell failure (witnessed 2026-10-05, exit 0 but stderr reporting an invalid conditional). Second, when the plumbing helper is absent from the project and the deployed runtime paths, the selector prints the WARN line and falls back to the worktree path, so a consumer's declared `worktree_policy = "primary"` silently degrades to the mode it explicitly refused (witnessed 2026-10-05; the run completed only through the documented `DOCS_BRANCH_SYNC_NOWORKTREE_SCRIPT` override). Both behaviors tax every consumer closeout that runs the docs sync, and the repair is two small edits to one shared block, so one plan fixes both.

## Outcome

- An empty `EXTRA_SHADOW_DIRS` under any supported bash emits no warning and exports nothing; a non-empty array exports `DOCS_SYNC_EXTRA_SHADOW_DIRS` exactly as today; the selector's export gate no longer uses the bare-array POSIX test form anywhere in the skill.
- A primary declaration with the helper resolvable from the override, the project, the deployed home, or the canonical skills root runs plumbing mode with the selected path echoed; a primary declaration with the helper absent everywhere stops with a named refusal carrying the deployment instruction, never the worktree fallback and never a silent degrade.
- The worktree path for undeclared or `worktrees` facts is untouched; the plumbing mode's own safety model is untouched; no facts key, gate, or outcome contract changes.

Gate delta: one warn-and-continue path replaced by a refusal (the primary-arm silent WARN fallback becomes a loud named refusal; priced by the witnessed 2026-10-05 silent degrade, origin row 2) and one optional environment knob added (`DOCS_BRANCH_SKILLS_ROOT`, paying sibling the existing `DOCS_BRANCH_SYNC_NOWORKTREE_SCRIPT` override whose style it copies); no new hard gate, no schema field, no removed refusal class beyond the replaced one.

## Assumptions

- assume authoring runs unattended under the standing operator directive, so the Step 1.4 confirmation is satisfied by the rows' validated records rather than a live interview; basis: the maintenance loop's authoring blueprint and both rows' consumer-urgency headers.
- assume the origin rows' declared class fix-class governs both remedies (witnessed consumer defects whose fixes are selector edits plus regression tests, not new capability); basis: each row's `Class:` line.
- assume the length test `[ "${#EXTRA_SHADOW_DIRS[@]}" -gt 0 ]` is the replacement form, safe under Bash 3.2 because the skill declares `EXTRA_SHADOW_DIRS=()` unconditionally before the selector; basis: the skill's own initialization line and the empty-array semantics of `${#a[@]}` under 3.2.
- assume the extraction test runs under the host bash, which on the maintenance host is Bash 3.2, so the witnessed environment is the test environment; basis: the origin row's reproduction on GNU Bash 3.2.57 and the macOS host shell.
- assume the new refusal exits non-zero after the WARN replacement, because a declared mode that cannot run must stop the sync rather than pick a mode the facts refused; basis: the no-worktree mode paragraph's declaration-gated contract and the row's refusing-fallback Expected.
- assume tests extend the existing docs-branch test style (python unittest wrappers driving bash) beside scripts/test_docs_branch_sync_noworktree.py; basis: the file's existing suite and the fixture-placement rule (fixtures carry placement plus teardown).

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the primary-mode selector's empty-array gate stops emitting bash 3.2 warnings, and a declared primary sync that cannot find its helper refuses loudly with deployment instructions instead of silently degrading to the worktree path.

Before (today): a consumer with no extra shadow dirs sees `[: =: unary operator expected` on every sync; a consumer with `worktree_policy = "primary"` and no deployed helper sees `WARN: no-worktree plumbing script not found; falling back to the worktree path` and gets the worktree mode it refused, unless it discovers the undocumented-in-the-moment override.

After (this plan): the export gate uses the array length form that is defined for empty arrays under every supported bash; the selector probes the override, the project scripts, the deployed home, then an optional `DOCS_BRANCH_SKILLS_ROOT` before declaring the helper missing; a missing helper under a primary declaration is a named refusal naming the override and the deployment path, and the sync stops instead of degrading.

Edge cases pinned: empty declared array emits no warning and exports nothing; non-empty array exports the space-joined value exactly as today; the array is always declared before the selector so the length form never trips `set -u`; an unset `worktree_policy` and a `worktrees` value keep today's worktree path with no new output; an unknown policy value keeps today's named report; the override wins over every probe when it names an existing file, and a set-but-missing override falls straight to the deployed-home probe (the project slot applies only when the override is unset); the canonical skills root is probed only when set; the refusal fires only under a primary declaration, and no other arm's messages change.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the replacement check is defined for empty arrays under Bash 3.2 and preserves the export-iff-non-empty semantics; the resolution order is override, project, deployed home, optional canonical root, refusal, each probe a plain file test; the refusal fires only in the primary arm.
- fail-closed shape: a declared mode that cannot run stops with a named message carrying the override knob and the deployment path; no arm silently changes the execution mode the facts declared.
- no scope creep: the worktree arm, the unknown-policy report, and the plumbing script's internals are untouched; no facts key or gate registry change.
- testability: the extraction test executes the shipped selector lines under the host bash and pins both array states; the resolution test pins precedence and the refusal, never a copy of the logic.

**Validation focus:**
- the new selector suite passes with empty and non-empty array cases;
- the resolution/refusal tests pass;
- the pins suite passes unchanged;
- the added-lines em-dash gate passes over the branch diff;
- the hygiene scan passes;
- `plan_readiness.py --pre-round` passes on the drafted plan bytes.

## Goal

A consumer's declared primary sync either runs the plumbing mode through a helper that was verifiably found, or stops with a named deployment refusal; and a normal empty configuration never prints a shell error again.

## Test Pins

- Pin A (Task 1): the literal `[ "${EXTRA_SHADOW_DIRS[@]+x}" = "x" ]` is absent from the post-change bytes of agents/skills/docs-branch/SKILL.md and the replacement length-test literal appears exactly once in the primary arm (zero-hit check scoped to the pre-change bytes of that file).
- Pin B (Task 2): the refusal message literal `docs-branch: worktree_policy = primary but no plumbing helper found` appears in the post-change bytes of agents/skills/docs-branch/SKILL.md, zero-hit in the pre-change bytes of that file, and the WARN fallback literal is absent from the post-change primary arm.
- Pin C (Task 1): the extraction test's assertion for the empty-array case (empty stderr, nothing exported) is new text in Task 1's own diff.

## Validation Commands

- python3 scripts/test_docs_branch_step2_selector.py
- python3 scripts/test_docs_branch_sync_noworktree.py
- bash scripts/check_maintenance_pins.sh
- bash scripts/check-no-em-dash.sh added-lines --base main
- bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
- python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-06-docs-branch-primary-sync-selector-fixes.md

### Task 1: empty-array-safe export gate and its extraction test

Files: `agents/skills/docs-branch/SKILL.md`, `scripts/test_docs_branch_step2_selector.py`

Evidence: `python3 scripts/test_docs_branch_step2_selector.py` green with the empty and non-empty cases, and the Pin A verification recorded in the task log in both directions: the unsafe literal present exactly once pre-change and absent post-change, and the replacement length literal zero-hit pre-change and appearing exactly once in the primary arm post-change.

- Replace the primary arm's export gate `if [ "${EXTRA_SHADOW_DIRS[@]+x}" = "x" ]; then` with the length form `if [ "${#EXTRA_SHADOW_DIRS[@]}" -gt 0 ]; then`, sentence-scoped to that line; the array's unconditional initialization earlier in the assembled invocation (the Documentation paths fence, extracted together with the sync fence) is frozen.
- Add scripts/test_docs_branch_step2_selector.py: extract from the skill bytes, by pinned anchors, the selector line and the export line it gates, write them to a temp script that initializes `EXTRA_SHADOW_DIRS=()`, sources the extracted lines, and prints the export decision; run it under bash with an empty array (assert empty stderr, nothing exported) and a two-entry array (assert empty stderr, the space-joined export), with per-fixture teardown; also assert the skill bytes no longer contain the bare-array POSIX test literal (Pin A's mechanical sweep).
- Freeze every other line of the `case` block.

### Task 2: canonical-source probe and the loud refusal (strictly after Task 1)

Files: `agents/skills/docs-branch/SKILL.md`, `scripts/test_docs_branch_step2_selector.py`

Evidence: the resolution and refusal assertions in scripts/test_docs_branch_step2_selector.py green (selected-path precedence with a fake root layout, and the primary-arm refusal with the helper absent everywhere), plus the Pin B zero-hit verification recorded in the task log.

- Extend the primary arm's resolution: after the deployed-home probe add the guarded fall-through `if [ ! -f "$NOWORKTREE_SCRIPT" ] && [ -n "${DOCS_BRANCH_SKILLS_ROOT:-}" ] && [ -f "${DOCS_BRANCH_SKILLS_ROOT}/scripts/docs_branch_sync_noworktree.sh" ]; then NOWORKTREE_SCRIPT="${DOCS_BRANCH_SKILLS_ROOT}/scripts/docs_branch_sync_noworktree.sh"; fi`, so the knob is probed only when every earlier resolution missed and can never clobber the override or an existing selection, and echo the selected helper path when plumbing mode starts.
- Replace the else arm's WARN fallback with the named refusal `docs-branch: worktree_policy = primary but no plumbing helper found (set DOCS_BRANCH_SYNC_NOWORKTREE_SCRIPT or deploy scripts/docs_branch_sync_noworktree.sh; see the no-worktree mode paragraph)` followed by `exit 1`, so the sync stops instead of degrading.
- Amend the no-worktree plumbing mode paragraph (the declaration-gated mode description) sentence-scoped: the resolution names the four probes in order and states that a primary declaration with no resolvable helper is a named refusal, never a fallback.
- Extend scripts/test_docs_branch_step2_selector.py, with the harness environment neutralized so the fixtures are host-independent (the override and the knob unset, HOME scrubbed to the temp layout, since the existing selector harness force-feeds the override), with the extraction-based resolution cases: precedence (override beats project beats deployed beats skills root, executed with a fake root layout in a temp dir, including the set-but-missing override fall-through case, whose landing is the deployed home) and the refusal case (primary declaration, no helper anywhere, assert the refusal literal on stderr and a non-zero exit, and assert the WARN fallback literal never appears), with per-fixture teardown.

- Amend the skill's Failure-semantics paragraph (the sync block's failure-classification paragraph) sentence-scoped: the primary-arm helper refusal joins the enumerated exit-1 abort paths, so the taxonomy that claims to classify every failure path of the block names the new refusal.
- After the edits run the pins suite and record its exit, and Task 2's own cases cover the refusal's appearance in the taxonomy (the refusal literal asserted in both the selector bytes and the Failure-semantics span).
Rider: both tasks edit one shared block and are strictly sequenced; Task 2 re-runs the Task 1 suite before its own cases, and any pin these edits reword is re-derived in the same task.
