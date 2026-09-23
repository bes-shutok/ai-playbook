# Plan: P52 script/harness small real tail

Backlog origins (scope of record; items stay in place until plan completion):

- `docs/history/backlog/2026-09-19-bootstrap-doc-hierarchy-greenfield-path-ordering.md`
- `docs/history/backlog/2026-09-19-cache-breakpoint-overflow-token-cost.md`
- `docs/history/backlog/2026-09-19-edit-failure-churn-read-discipline.md`
- `docs/history/backlog/2026-09-22-dirt-gate-staged-deletion-edge.md`

## Terms

- **Facts file**: `.ai-playbook/facts.md` in a consumer repo; Markdown with a single opening TOML fence carrying the path keys (`plans_dir`, `reviews_dir`, `backlog_dir`, and siblings) that every downstream skill reads.
- **Canonical map**: the post-migration doc-hierarchy layout: `docs/history/plans/`, `docs/history/plans/completed/`, `docs/history/reviews/` (gitignored), `docs/history/backlog/`, `docs/history/backlog/completed/`, `docs/tmp/`.
- **Greenfield fallback**: bootstrap path discovery on a consumer repo with no `docs/` tree at all, where no existing home can be discovered on disk.
- **Read-before-edit pin**: the behavioral rule that a file must be Read in the current session before its first Edit, and re-Read after any external-change signal.
- **Staged deletion**: a whole-file deletion recorded in the git index (`git rm`, or a post-deletion `git add` sweep) while HEAD still tracks the path.
- **Dirt regression gate**: `scripts/dirt_regression_gate.py`, which classifies working-tree changes that restore base-era text over lines HEAD gained.

## Assumptions

- assume one batch plan for all four origins, not four split plans; basis: the maintenance batch P52 defines them as one small real tail and the four tasks have pairwise-disjoint `Files:` sets.
- assume the full bootstrap remedy (explicit greenfield ask plus canonical seeding) with the warning retained for the residual legacy shape where top-level `docs/plans/` and `docs/reviews/` keys are persisted anyway (a caller-directed legacy layout or an older runtime default), while an unanswered ask persists no invented keys; basis: the origin's Expected section lists the full remedy first and the standing pre-authorization accepts recommended options.
- assume the dirt-gate staged-deletion remedy has already landed in `scripts/dirt_regression_gate.py`; basis: code probe 2026-09-23 shows the HEAD-tracking classification with its explanatory comment, and a scratch-repo probe (`git rm` of a regressive shape) returns rc 1 with `dirt REGRESSION` today; this plan only adds witness tests and folds the duplicate.
- assume the cache-breakpoint repo-side remedy is a documentation amendment; basis: the origin disposition of 2026-09-23 records that the overflowing context assembler is outside this repository and the reference doc is its sole living-surface match.
- assume task order 1 through 4 below; basis: backlog listing order, and no ordering dependency exists between the tasks.

Decision points requiring a grill: none remain.

## Gist & Examples

Four small origins, one task each. Example for Task 1: on a consumer repo with no `docs/` tree, bootstrap today falls back to seeding `plans_dir = "docs/plans/"` and `reviews_dir = "docs/reviews/"` (the example-template values) when the interactive ask goes unanswered. A later doc-hierarchy-migrate on that repo then fails its step2 gate because plans and reviews sit at the `docs/` root, and the facts keys must be rewritten after the migration. After Task 1, greenfield bootstrap asks whether the doc-hierarchy schema is the target and, when it is, seeds the canonical map directly, so the two skills compose in either order. Example for Task 2: every request of the mined week emitted `Maximum 4 cache breakpoints exceeded (found 5)`; the reference doc currently carries only the generic line `respect provider limits on cache breakpoints`. Task 2 replaces it with the concrete budget rule (at most 4 breakpoints, deterministic merge-or-drop of the lowest-value candidates, alert on overflow). Example for Task 3: 6.3 percent of edits fail, the largest single class being `File has not been read yet` (408 of 820 errors over 30 days); Task 3 pins read-before-edit discipline into the implement worker templates and the done skill so fresh subagent contexts stop inheriting stale already-read beliefs. Example for Task 4: a staged deletion (`git rm app.txt`) was once misreported as a git-environment error (rc 2) instead of being classified; the classification fix has already landed in `scripts/dirt_regression_gate.py`, but no test pins the staged shape and a strict-duplicate rc test remains; Task 4 adds both staged-deletion witnesses and deletes the duplicate.

## Evaluation Criteria

**Quality dimensions:**

- correctness: every pinned span in Validation Commands matches its prescribed insertion verbatim; the dirt-gate suite passes with both new staged-deletion witnesses and the folded duplicate absent.
- completeness: all four origins carry a repo-verifiable remedy; Integration Points rows are updated in both directions (bootstrap-ai-playbook and doc-hierarchy-migrate).
- maintainability: pin spans are distinctive multi-word strings, unique within their evaluated scope (file-wide where the pin is file-wide; inside the extracted Discovery-rules region where the pin is region-scoped, which is why the `tmp_dir` seed literal is pinned only in-region, since it pre-exists in the Facts File Shape example block); no new scripts and no hooks (the read-discipline remedy is skill-level text only).
- simplicity: each task is the smallest repo-side remedy that closes its origin; Task 4 changes no production code.

**Done when:**

- All four tasks are implemented and the `## Validation Commands` block exits 0 on the post-task tree.
- `python3 scripts/test_dirt_regression_gate.py` passes, `test_untracked_missing_path_fails_closed` is gone, and both staged-deletion witness tests exist.
- `bash scripts/scan-public-hygiene.sh` exits 0 from the repo root.

**Ship when:**

- (origin 2, out-of-repo runtime condition) A 24-hour log window on a runtime that adopted the breakpoint budget shows zero breakpoint-overflow warnings and no cache-hit regression on long sessions. Evidence owner: the harness runtime operator, not this repository.
- (origin 3, operations condition) A 7-day log window shows the edit error rate below 2 percent and zero `File has not been read yet` failures inside single-owner runs. Evidence owner: the cross-session friction audit that mined the original numbers.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `agents/skills/bootstrap-ai-playbook/SKILL.md`
- `agents/skills/doc-hierarchy-migrate/SKILL.md`
- `agents/skills/agents-best-practices/references/prompt-caching-and-cost.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/done/SKILL.md`

**Tests:**

- `scripts/test_dirt_regression_gate.py`

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `scripts/dirt_regression_gate.py`; the staged-deletion fix already landed there (probe 2026-09-23); changing it is not this plan's work.
- `scripts/verify-doc-hierarchy.sh` and the doc-hierarchy-migrate gates; the migration gates are correct as-is, the remedy is bootstrap-side.
- `docs/maintenance/development_lessons.md`; lessons land via learn during execution, never as a plan task.

## Validation Commands

```bash
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1
fail() { echo "VALIDATION FAIL: $1"; exit 1; }
expect_present() { grep -qF "$1" "$2" || fail "missing in $2: $1"; }
expect_absent() {
  grep -qF "$1" "$2"; rc=$?
  if [ "$rc" -eq 0 ]; then fail "forbidden match in $2: $1"; fi
  if [ "$rc" -ge 2 ]; then fail "grep error rc=$rc on $2"; fi
}

# Task 1 pins: bootstrap greenfield canonical seeding (seed obligations region-scoped to the greenfield rule; warning and integration pins file-wide)
REGION="$(awk '/^### Discovery rules$/{f=1;next} /^### Exploration commands$/{f=0} f' agents/skills/bootstrap-ai-playbook/SKILL.md)"
test -n "$REGION" || fail "Discovery rules region not found in bootstrap skill"
for span in \
  'ask explicitly whether the doc-hierarchy schema is the target layout' \
  'plans_dir = "docs/history/plans/"' \
  'plans_completed_dir = "docs/history/plans/completed/"' \
  'reviews_dir = "docs/history/reviews/"' \
  'backlog_dir = "docs/history/backlog/"' \
  'backlog_completed_dir = "docs/history/backlog/completed/"' \
  'tmp_dir = "docs/tmp/"' \
  'create every seeded directory' \
  'when no existing rule ignores it' \
  'compose in either order'; do
  printf '%s' "$REGION" | grep -qF "$span" || fail "greenfield rule missing: $span"
done
expect_present 'conflict with the doc-hierarchy-migrate step2 gate' agents/skills/bootstrap-ai-playbook/SKILL.md
expect_present 'legacy-layout examples, not greenfield defaults' agents/skills/bootstrap-ai-playbook/SKILL.md
expect_present 'seeds the canonical history map when it is' agents/skills/bootstrap-ai-playbook/SKILL.md
expect_present 'canonical map directly when the schema is confirmed' agents/skills/doc-hierarchy-migrate/SKILL.md

# Task 2 pins: cache breakpoint budget rule (new rule present, generic line gone)
expect_present 'budget at most 4 cache breakpoints per request' agents/skills/agents-best-practices/references/prompt-caching-and-cost.md
expect_present 'Maximum 4 cache breakpoints exceeded (found 5)' agents/skills/agents-best-practices/references/prompt-caching-and-cost.md
expect_present 'merge or drop the lowest-value candidates by one deterministic rule' agents/skills/agents-best-practices/references/prompt-caching-and-cost.md
expect_present 'treat a breakpoint-overflow warning as a budget bug in the assembler' agents/skills/agents-best-practices/references/prompt-caching-and-cost.md
expect_absent 'respect provider limits on cache breakpoints' agents/skills/agents-best-practices/references/prompt-caching-and-cost.md

# Task 3 pins: read-before-edit discipline (exactly one occurrence per region, two in the templates file)
test "$(grep -cF 'read-before-edit is mandatory per file per session' agents/skills/execute-plan/subagent-prompts.md)" -eq 2 || fail "implement/batch pin count is not 2"
test "$(grep -cF 'read-before-edit is mandatory per file per session' agents/skills/done/SKILL.md)" -eq 1 || fail "done pin count is not 1"
expect_present 'A fresh subagent context inherits no read state from the parent' agents/skills/execute-plan/subagent-prompts.md
expect_present 're-Read the file before retrying the edit' agents/skills/done/SKILL.md

# Task 4 pins: dirt-gate suite green, witnesses present, duplicate folded
python3 scripts/test_dirt_regression_gate.py || fail "dirt-gate suite failed"
expect_absent 'test_untracked_missing_path_fails_closed' scripts/test_dirt_regression_gate.py
expect_present 'def test_staged_regressive_whole_file_deletion_is_regression' scripts/test_dirt_regression_gate.py
expect_present 'def test_staged_neutral_whole_file_deletion_passes' scripts/test_dirt_regression_gate.py

# Mechanical gates over the plan artifact itself (run from the repo root)
bash scripts/check-no-em-dash.sh file docs/plans/2026-09-23-p52-script-harness-tail.md || fail "em dash in plan file"
bash scripts/scan-public-hygiene.sh || fail "public hygiene scan failed"
```

### Task 1: Bootstrap greenfield seeds the canonical doc-hierarchy map

Files:

- `agents/skills/bootstrap-ai-playbook/SKILL.md`
- `agents/skills/doc-hierarchy-migrate/SKILL.md`

- [ ] In `### Discovery rules` of bootstrap-ai-playbook, add a greenfield rule that does all of the following and contains the span `ask explicitly whether the doc-hierarchy schema is the target layout`: when the repo has no `docs/` tree at all, ask that question first; when confirmed, skip discovery for the doc keys and seed `plans_dir = "docs/history/plans/"`, `plans_completed_dir = "docs/history/plans/completed/"`, `reviews_dir = "docs/history/reviews/"`, `backlog_dir = "docs/history/backlog/"`, `backlog_completed_dir = "docs/history/backlog/completed/"`, and `tmp_dir = "docs/tmp/"`; create every seeded directory; add `docs/history/reviews/` to `.gitignore` when no existing rule ignores it; state that bootstrap and doc-hierarchy-migrate then compose in either order because a later migration finds the layout already canonical. [class: IMPLEMENTATION_REQUIRED]
- [ ] Make the no-home policy coherent and define the non-interactive case: amend the existing final Discovery-rule bullet (`If no home exists, follow project_guidelines_rel if documented; else ask the user before creating new top-level docs/ trees.`) so it defers to the greenfield ask on a repo with no `docs/` tree and states that no path keys are persisted silently on an unanswered ask; and extend the greenfield rule so that when the ask goes unanswered in a non-interactive run, bootstrap records the open ask (per the Recovery rerun rule) and persists no invented doc keys. Extend the Recovery rerun exception clause (the paragraph beginning `**Recovery rerun (same session):**`) so a greenfield doc ask awaiting the user is named alongside the backlog-ask exception as not a validation failure (re-ask once per session instead of rerunning bootstrap), so the persist-no-keys behavior cannot compose with the missing-required-key trigger into an unbounded non-interactive rerun loop. The fallback-warning obligation (span `conflict with the doc-hierarchy-migrate step2 gate`) then applies to the residual legacy shape where top-level `docs/plans/` and `docs/reviews/` keys get persisted anyway (a caller-directed legacy layout or an older runtime default), naming that conflict and the re-pointing obligation. [class: IMPLEMENTATION_REQUIRED]
- [ ] In `## Facts File Shape` of bootstrap-ai-playbook, directly below the example TOML block, add one sentence containing the span `legacy-layout examples, not greenfield defaults`, saying the example `docs/plans/` and `docs/reviews/` values are exactly that and pointing at the greenfield rule in Path Discovery for the canonical history map. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the bootstrap Integration Points table, extend the `doc-hierarchy`, `doc-hierarchy-migrate`, `doc-hierarchy-upkeep` row so its cell also contains the span `seeds the canonical history map when it is`, describing the greenfield ask. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the doc-hierarchy-migrate Integration Points table, extend the `bootstrap-ai-playbook` row so its cell also contains the span `canonical map directly when the schema is confirmed`, so the peer-side row encodes the same contract (bidirectional integration). [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `feat: bootstrap greenfield seeds the canonical doc-hierarchy map` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Cache breakpoint budget rule in the prompt-caching reference

Files:

- `agents/skills/agents-best-practices/references/prompt-caching-and-cost.md`

- [ ] In the `### Anthropic` implementation notes text block, replace the single generic line `respect provider limits on cache breakpoints` with three concrete lines that together contain these exact spans: `budget at most 4 cache breakpoints per request`; the overflow warning literal `Maximum 4 cache breakpoints exceeded (found 5)` (named as the signature the provider emits when breakpoint 5 is silently dropped and the uncovered segment pays full token cost on every call); `merge or drop the lowest-value candidates by one deterministic rule` (same choice for the same context shape, never emit 5); and `treat a breakpoint-overflow warning as a budget bug in the assembler` with the guidance to alert on it rather than tolerate it as log noise. Keep the surrounding lines of the text block unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: concrete cache breakpoint budget rule in prompt-caching reference` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Read-before-edit pins in the implement, batch, and done contracts

Files:

- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/done/SKILL.md`

- [ ] Append a new rule 10 to the `## Rules` list of the Implement Task template containing the span `read-before-edit is mandatory per file per session`, the re-Read rule after any external-change signal (peer commit, plan fold, formatter run, or a `modified since read` failure), and the sentence `A fresh subagent context inherits no read state from the parent`. Appending keeps the existing rule numbering stable. [class: IMPLEMENTATION_REQUIRED]
- [ ] Append a new rule 9 to the `## Rules` list of the Implement Task Batch template containing the same span `read-before-edit is mandatory per file per session`, phrased for the single batch session: member boundaries are external-change signals, so the next member's files are re-Read in this session before the first edit to them. Appending keeps the existing rule numbering stable. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the done skill's `## Invocation (read first)` block, add one bullet named Edit discipline containing the span `read-before-edit is mandatory per file per session`, the same external-change-signal re-Read rule naming docs-branch and sweep-gate operations among the signals, and the span `re-Read the file before retrying the edit`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `feat: read-before-edit pins in implement, batch, and done contracts` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Dirt-gate staged-deletion witnesses and duplicate fold

Files:

- `scripts/test_dirt_regression_gate.py`

- [ ] Delete the test method `test_untracked_missing_path_fails_closed`; it is a strict duplicate of `test_missing_path_fails_closed` (same ghost fixture and rc 2 assertion, minus the stderr message assertion the survivor already makes). [class: REPOSITORY_TEST]
- [ ] Add `test_staged_regressive_whole_file_deletion_is_regression` next to the existing whole-file-deletion tests: seed with the existing `_seed_head_gained_lines()` helper, stage the deletion of `app.txt` with `git rm` through the fixture's git helper (index removal, not a bare unlink), run the gate against the returned base sha; given this staged regressive shape, expects rc 1 and stdout naming `app.txt` with `dirt REGRESSION`. Probe 2026-09-23 confirmed today's code returns exactly that on this shape. [class: REPOSITORY_TEST]
- [ ] Add `test_staged_neutral_whole_file_deletion_passes`, a mirror of `test_neutral_whole_file_deletion_passes` that stages the deletion with `git rm` instead of unlinking; given a staged deletion restoring base content, expects rc 0. [class: REPOSITORY_TEST]
- [ ] Run `python3 scripts/test_dirt_regression_gate.py`; expect GREEN with no RED phase because the classification fix pre-lands and these tests pin existing behavior plus the fold. [class: REPOSITORY_TEST]
- [ ] Commit: `test: staged-deletion witnesses and duplicate fold for the dirt gate` [class: REPOSITORY_TEST]
