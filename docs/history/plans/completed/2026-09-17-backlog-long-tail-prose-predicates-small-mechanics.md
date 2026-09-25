# Plan: Backlog Long Tail: Prose, Predicates, and Small Mechanics

Closes the eight unclaimed origins of the live P7 backlog group (queue:
`docs/tmp/future-plan-prompts-2026-09-16.md`, section P7). Origin items, the
scope of record, all under `docs/history/backlog/`:

- `2026-09-13-doc-registry-r5-prose-residuals.md`
- `2026-09-13-plan-readiness-path-shape-suffix-and-markup-tails.md`
- `2026-09-13-plan-readiness-solo-witness-gaps.md`
- `2026-09-14-runtime-r5-trim-review-exit-residuals.md`
- `2026-09-16-cross-surface-globish-brevity-policy.md`
- `2026-09-16-graphify-skill-package-version-drift.md`
- `2026-09-16-finder-applescript-folder-reference-10006.md`
- `2026-09-16-zcode-memory-files-external-rewrites.md`

Guidelines reference: `projects/.ai-playbook/agent_workflow_guidelines.md`
(especially sections 1, 39, 45, 64).

## Terms

- **Selftest arm**: one named fixture-plus-assertion row inside a validator's
  `--selftest` run (for example `selftest#review_scope/<name>` in
  `scripts/plan_readiness.py`). Arms are added, never removed or renamed.
- **Leading-span rule**: `_review_scope_path_token` extracts a backticked span
  from a Review Scope or Files list item before the fall-through first-token
  branch; both branches share one backslash-to-slash normalization exit.
- **Accepted tail**: a recorded, deliberately unfixed defect class in a plan's
  invariants, to be fixed only when a real authoring shape hits it.
- **Canonical writing contract**: the single shared statement of writing
  priorities living in guidelines section 45; skills point at it and keep only
  surface-specific rules.
- **Human-finalization boundary**: Slack messages are drafted by the agent,
  reviewed and edited by the user, and sent only by the user.
- **Vendored skill sync**: this repo's `agents/skills/` copy is the canonical
  skill layer; refreshes follow the full bidirectional sync and hygiene rules.

## Assumptions

- assume the live queue file outranks the scheduling prompt's 10-origin enumeration: `learn-capture` and `drift-witness-docs-branch-sync` moved to the P0 group and are out of scope here; basis: the P7 slimming note in `docs/tmp/future-plan-prompts-2026-09-16.md` and a stand-down probe (plans dirs, deferred dirs, git log) that found no covering plan for any origin, 2026-09-17.
- assume the path-shape and markup accepted tails stay unfixed and their origin closes by verification; basis: a corpus sweep over `docs/plans/**` on 2026-09-17 found zero slash-less suffix-less path tokens in task Files lists and zero bold-wrapped backticked paths in Review Scope blocks, and the origin's own condition is fix only if a real authoring shape hits.
- assume the Globish origin's numbered fix candidates 1 through 7 are adopted as the contract design, with code comments staying delegated to the documentation review lens and Atlassian scope meaning this repo's existing jira and Confluence skills; basis: the origin's fix-candidate preference order and its current-state list, under standing pre-authorization.
- assume new guidelines rules append after section 64 (the last existing number) as sections 65 and 66, and the canonical writing contract expands section 45 in place so existing external references to it stay valid; basis: file tail inspection 2026-09-17; the plans skill and `jira-workflow` already cite section 45.
- assume the r5-trim F2 lesson records live-measured suite counts, not the origin's stale 136; basis: `scripts/test_execute_plan_runtime.py` holds 137 `def test_` definitions at authoring time, 2026-09-17.
- assume the graphify mismatch warning probed live on 2026-09-17 (`warning: skill is from graphify 0.9.25, package is 0.9.51. Run 'graphify install' to update.`) is the preflight trigger shape; basis: `graphify --version` run on this host.

Decision points requiring a grill: p7-scope-slim: follow the live queue's 8-origin P7, learn-capture and drift-witness belong to the P0 group; source: queue slimming note plus stand-down probe, 2026-09-17; affects Scope and Gist; path-shape-disposition: close by verification with no predicate change; source: corpus sweep 2026-09-17 found zero real shapes and the origin's fix-only-if-hit condition; affects Task 2; globish-design: adopt the origin's numbered fix candidates 1-7 as the contract design, with the candidate-6 example set narrowed to Slack-like and review-comment pairs plus normative decision-table rows for the remaining surface classes; source: origin preference order plus standing pre-authorization, 2026-09-17; affects Task 5; f10-coupling-deferred: keep the meta-row loop-call coupling deferred with recorded rationale; source: a flipping witness would require an invalid arm-table row, which the table must never carry, 2026-09-17; affects Task 2.

## Gist & Examples

This plan is a batch of small, independent repairs across validators, skill
prose, and shared guidelines. Each origin gets one owning task with executable
gates; nothing here needs new infrastructure.

**Before (today):** an agent running `graphify --version` sees
`warning: skill is from graphify 0.9.25, package is 0.9.51. Run 'graphify install' to update.` and may still follow the query workflow from stale 0.9.25
guidance against a 0.9.51 package. A worker filename carrying a byte invalid in
the locale encoding makes `reconcile_startup` raise `UnicodeDecodeError` out of
the runtime library instead of returning the fail-closed
`worktree-witness-unavailable` outcome its sibling failure shapes return. The
plan-readiness selftest proves the windows-separator normalization only for the
fall-through token branch: a backticked item like `- `scripts\service.py`` in a
Files list exercises the leading-span branch with zero committed arms, so a
regression there flips nothing. `doc-hierarchy` says "except for three bounded
warn tiers" where the validator docstring says three further warn tiers beyond
the legacy ones. Nothing in the shared guidelines states one writing contract,
so each human-facing skill carries its own partial prose rules, and nothing
pins the Finder AppleScript `-10006` failure or the externally-mutable memory
file behavior that burned real sessions this week.

**After (this plan):** the graphify skill carries a version preflight keyed on
that exact warning shape plus one supported update path and an offline
fallback. The runtime catches `UnicodeDecodeError` on both natural-path
witness sites, pinned by two RED-first arms. Six new committed arms pin the
leading-span, payload-reopen, heading-boundary, and echo shapes, and the
path-shape accepted tails close with recorded corpus evidence instead of code
churn. `doc-hierarchy` reads "three further bounded warn tiers". Guidelines
section 45 becomes the canonical writing contract (with the session-language
invariant), sections 65 and 66 add the Finder AppleScript and memory-file
rules, and six skill surfaces point at the contract keeping only their
surface-specific constraints. The eight origin items archive with registry
rows.

Happy path walk, one origin end to end (graphify): an agent invokes the skill;
Step 1 now runs the version probe first; on the warning it stops the workflow,
runs `graphify install --platform agents`, verifies the repo diff is confined
to `agents/skills/graphify/`, hygiene-scans, commits the refresh, re-probes
clean, and only then continues. Offline, it prints the mismatch, falls back to
`--help`-derived flag guidance, and says so.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every code defect pinned by a named RED arm or a live probe quoted verbatim in this plan; prose fixes quote the exact before and after sentences
- simplicity: witness arms over new frameworks; no predicate changes on the accepted tails; no new scripts, hooks, or config
- maintainability: skills point at the canonical contract instead of restating policy; arm names are self-describing
- hygiene: public-hygiene scan exit 0 on all changed files; no em dash (U+2014) in any content this plan introduces

**Done when:**
- `python3 -m unittest test_execute_plan_runtime` (from `scripts/`) passes with the two new UnicodeDecodeError arms
- `python3 scripts/plan_readiness.py --selftest` passes with the six new review_scope arms
- `python3 scripts/doc_registry_validator.py --selftest` passes
- the Validation Commands block exits 0 end to end
- the eight origin items sit under `docs/history/backlog/completed/` with `Status: done` and one document-registry row each

**Ship when:**
Nothing ships; all evidence is repository-local. Landing follows the normal
execute-plan merge flow.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_runtime.py` (only the two natural-path except clauses in `_reconcile_startup_locked`; all other methods in this file are frozen; reject any finding that touches them)
- `scripts/plan_readiness.py` (only the new selftest arms, the `_review_scope_path_token` docstring sentence, and nothing else; the path-shape and leading-span predicates are frozen per the accepted-tail disposition)
- `scripts/doc_registry_validator.py` (only the one duplicated-word comment deletion)
- `agents/skills/doc-hierarchy/SKILL.md` (only the warn-tier sentence)
- `docs/history/backlog/completed/` *(archive destinations for the Task 9 moves; one directory entry covers all eight)*
- `agents/skills/graphify/SKILL.md`
- `projects/.ai-playbook/agent_workflow_guidelines.md` (sections 45, 65, 66 only)
- `agents/skills/slack-message/SKILL.md`, `agents/skills/jira-workflow/SKILL.md`, `agents/skills/review-confluence-doc/SKILL.md`, `agents/skills/doing-code-review/SKILL.md`, `agents/skills/github-pr-workflow/SKILL.md`, `agents/skills/review-agents/documentation.md` (canonical-contract pointer reconciliation only)
- `projects/.ai-playbook/development_lessons.md` (test-count drift lesson append only; 352 pre-existed, landed as 371)
- `docs/maintenance/document-registry.md` (eight appended rows only)

**Tests:**
- `scripts/test_execute_plan_runtime.py` (two new arms appended)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. `agents/skills/graphify/references/` may be refreshed by the Task 4 install step; such refreshes are plan-related. Backlog moves under `docs/history/backlog/completed/` are plan-related. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/hooks/budget-guard/*`, `scripts/quota_window_probe.py`, `scripts/execute_plan_resume_watcher.py`, `agents/skills/execute-plan/SKILL.md` working-tree changes; reason: peer-session joint state, not this plan's work
- `docs/history/backlog/2026-09-16-learn-skill-usage-issue-backlog-capture.md`, `docs/history/backlog/2026-09-15-drift-witness-docs-branch-sync-fallback.md`; reason: claimed by the P0 queue group, excluded by the p7-scope-slim receipt
- `docs/plans/completed/2026-09-13-doc-registry-validator-residuals.md`, `docs/plans/completed/2026-09-13-execute-plan-runtime-r5-residuals-yagni-trim.md` (archived bodies); reason: frozen history per doc-hierarchy; both dispositions are record-only

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"
cd "$REPO" || exit 1

# Task 1: runtime suite including the two new UnicodeDecodeError arms
( cd scripts && python3 -m unittest test_execute_plan_runtime -q ) || { echo "FAIL: runtime suite"; exit 1; }

# Task 2: plan_readiness selftest including the six new arms
python3 scripts/plan_readiness.py --selftest || { echo "FAIL: plan_readiness selftest"; exit 1; }

# Task 3: doc-registry selftest plus prose gates
python3 scripts/doc_registry_validator.py --selftest || { echo "FAIL: doc-registry selftest"; exit 1; }
grep -qF "three further bounded warn tiers" agents/skills/doc-hierarchy/SKILL.md || { echo "FAIL: warn-tier scoping missing"; exit 1; }
# Wrap-tolerant duplication gate: the two words sit on different comment lines,
# so newlines and '#' map to spaces before matching. The plan's own mention uses
# a slash between the words and cannot self-match.
tr '\n#' '  ' < scripts/doc_registry_validator.py | grep -qE "argparse +argparse"
rc=$?
if [ "$rc" -eq 0 ]; then echo "FAIL: duplicated argparse word still present"; exit 1
elif [ "$rc" -ge 2 ]; then echo "ERROR: grep failed on validator"; exit 1; fi

# Task 4: graphify preflight anchor (the step quotes the probed warning verbatim)
grep -qF "skill is from graphify" agents/skills/graphify/SKILL.md || { echo "FAIL: version preflight missing"; exit 1; }
grep -qF "graphify install --platform agents" agents/skills/graphify/SKILL.md || { echo "FAIL: supported update path missing"; exit 1; }

# Task 5: canonical contract anchors, one pointer per reconciled surface
grep -qF "canonical writing contract" projects/.ai-playbook/agent_workflow_guidelines.md || { echo "FAIL: canonical contract missing"; exit 1; }
for f in slack-message jira-workflow review-confluence-doc doing-code-review github-pr-workflow; do
  grep -qF "agent_workflow_guidelines.md" "agents/skills/$f/SKILL.md" || { echo "FAIL: $f missing canonical pointer"; exit 1; }
done
grep -qF "agent_workflow_guidelines.md" agents/skills/review-agents/documentation.md || { echo "FAIL: documentation lens missing canonical pointer"; exit 1; }
# No-duplication tripwire: the final-pass checklist phrasing lives only in the
# guidelines section 45; no reconciled surface restates it.
grep -lF "final-pass checklist" agents/skills/slack-message/SKILL.md agents/skills/jira-workflow/SKILL.md agents/skills/review-confluence-doc/SKILL.md agents/skills/doing-code-review/SKILL.md agents/skills/github-pr-workflow/SKILL.md agents/skills/review-agents/documentation.md
rc=$?
if [ "$rc" -eq 0 ]; then echo "FAIL: a reconciled surface restates the canonical checklist"; exit 1
elif [ "$rc" -ge 2 ]; then echo "ERROR: grep failed on surfaces"; exit 1; fi

# Tasks 6 and 7: new guidelines rules
grep -qF "## 65. Finder AppleScript" projects/.ai-playbook/agent_workflow_guidelines.md || { echo "FAIL: rule 65 missing"; exit 1; }
grep -qF "## 66. Agent Memory Files Are Externally Mutable" projects/.ai-playbook/agent_workflow_guidelines.md || { echo "FAIL: rule 66 missing"; exit 1; }

# Task 8: the test-count drift lesson landed (352 pre-existed; landed as 371)
grep -qF "## 371." projects/.ai-playbook/development_lessons.md || { echo "FAIL: lesson 371 missing"; exit 1; }

# Task 9: all eight origins archived with registry rows (iterate full basenames;
# the registry identity strips the date prefix)
for f in 2026-09-13-doc-registry-r5-prose-residuals 2026-09-13-plan-readiness-path-shape-suffix-and-markup-tails 2026-09-13-plan-readiness-solo-witness-gaps 2026-09-14-runtime-r5-trim-review-exit-residuals 2026-09-16-cross-surface-globish-brevity-policy 2026-09-16-graphify-skill-package-version-drift 2026-09-16-finder-applescript-folder-reference-10006 2026-09-16-zcode-memory-files-external-rewrites; do
  if [ -e "docs/history/backlog/$f.md" ]; then echo "FAIL: $f still open"; exit 1; fi
  test -f "docs/history/backlog/completed/$f.md" || { echo "FAIL: $f not archived"; exit 1; }
  grep -q "^Status: done" "docs/history/backlog/completed/$f.md" || { echo "FAIL: $f not marked done"; exit 1; }
  s="${f#*-}"; s="${s#*-}"; s="${s#*-}"
  grep -qF "$s" docs/maintenance/document-registry.md || { echo "FAIL: $s missing registry row"; exit 1; }
done

# Hygiene over the repo (scan root anchored to the repo)
( cd "$REPO" && bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" ) || { echo "FAIL: hygiene scan"; exit 1; }
```

### Task 1: Runtime worktree witness survives undecodable filenames (r5-trim F1)

Files:
- `scripts/test_execute_plan_runtime.py`
- `scripts/execute_plan_runtime.py`

- [x] `test_execute_plan_runtime` RED arm `test_reconcile_startup_survives_unicode_decode_on_dirty_probe`; given a driver whose `_git_worktree_dirty` is patched to raise `UnicodeDecodeError`, `driver.reconcile_startup()` expects `status == "blocked"`, `reason_code == "worktree-witness-unavailable"`, `resume_allowed` false, and no exception escaping (follow the patch-and-assert shape of the existing `worktree-witness-unavailable` arms near lines 552 and 1069)
- [x] RED arm `test_reconcile_startup_survives_unicode_decode_on_ambient_enumeration`; given `_git_worktree_dirty` patched to return True and `_git_worktree_entries` patched to raise `UnicodeDecodeError`, `driver.reconcile_startup()` expects the same blocked outcome (this pins the ambient classification call, the second natural-path site)
- [x] Run → expect RED: `( cd scripts && python3 -m unittest test_execute_plan_runtime -k unicode_decode -q )` fails with `UnicodeDecodeError` escaping both new arms (137 existing tests stay green)
- [x] Write minimal implementation: in `_reconcile_startup_locked`, add `UnicodeDecodeError` to the two natural-path except clauses (the `_git_worktree_dirty` call and the ambient `_git_worktree_entries` call), matching the catch already present on the injected-dirty fill-in path
- [x] Run → expect GREEN: the two new arms pass and the full suite (139 tests at authoring; live count recorded in the task log) reports OK
- [x] Commit: `fix: runtime worktree witness survives undecodable filenames`

### Task 2: plan_readiness solo-witness arms and path-shape disposition (solo-witness-gaps origin, r3 additions, path-shape closure)

Files:
- `scripts/plan_readiness.py`

Characterization arms are GREEN on arrival; each names the revert that must flip it. Add arms without removing or renaming any existing arm name. Place review-scope arms in `_selftest_review_scope` following its `rs_plan` fixture helper and `check("selftest#review_scope/<name>", ...)` pattern.

- [x] Arm `backticked_windows_separator_ok`; given a task Files item `` - `scripts\service.py` `` (backtick-quoted backslash path, leading-span branch) and scope entry `- scripts/`, expects ok (probed 2026-09-17: the shared normalization exit covers both branches; only the fall-through branch had an arm); flip probe: make the shared exit normalize only the fall-through branch
- [x] Arm `doubled_backtick_span_extracted`; given a task Files item `` - ``src/service.py`` *(new)* `` (doubled backticks plus a trailing annotation) with `- src/service.py` listed in scope, expects ok (probed live: the leading-span pattern accepts any backtick-run length and the annotation never enters the span; today zero committed arms cover a doubled-backtick item); flip probe: narrow the leading-span pattern to exactly one backtick per side so the item falls through to the raw first-token branch (measured 2026-09-17: the fall-through token retains the backtick run and fails containment, flipping the arm)
- [x] Arm `payload_files_line_then_reopen_collects`; given a task whose Files block first opens with a payload line `Files: none new (validation only)` and later re-opens with a bare `Files:` listing `- src/unlisted.py` absent from scope, expects failure with reason naming `src/unlisted.py` (stated as expects-failure because an ok-arm with an in-scope path cannot detect under-collection; current re-open semantics collect the path and fail); flip probe: revert the opener branch to the pre-r1-F1 form where a bare Files: line does not open collection after a payload line closed it (measured: the unlisted path is then never collected and this arm goes green, flipping it)
- [x] Arm `second_real_files_block_unlisted_fails`; given a task with two real Files blocks where the second lists `- src/unlisted2.py` absent from scope, expects failure with reason naming `src/unlisted2.py` (promotes the post-r1 positive red direction from ephemeral /tmp probes into a committed arm); flip probe: the same pre-r1-F1 re-open revert named for `payload_files_line_then_reopen_collects` (the two arms flip together under the shared revert, from the payload-first and two-real-blocks directions)
- [x] Arm `heading_boundary_files_after_subheading_ignored`; given Task 1 carrying a valid Files block whose path is listed in scope, followed inside the same Task 1 region by a `### Notes: boundary probe` subheading with its own Files block listing `- src/unlisted.py` (absent from scope), expects ok (the subheading must not start with Task or Step: `### Step note:` was measured to match the `#{3,4} (Task|Step)` scan and open its own collected region; `### Notes:` does not match, so the `\n#{2,4} ` boundary cut ends Task 1's tail at the subheading and the block is never collected; reverting the widening to `\n## ` makes Task 1's tail swallow the unlisted block and flips this arm to a containment failure)
- [x] Arm `echo_section_non_path_token_ignored`; given a valid first Review Scope block plus a second `## Review Scope` echo block carrying a stray `Files:` line with `- src/phantom.md`, and a task Files list whose real path is listed in the first block, expects ok (probed live: `md_section` returns only the first block; this witnesses the no-second-block-latch and no-fabrication property); flip probe: collect `Files:` lines from any section instead of only `#{3,4} (Task|Step)` headings
- [x] Docstring precision (r3 correctness lens): in `_review_scope_path_token`, replace the sentence stating a doubled-backtick fence is accepted with: a backtick-run opener of any length is accepted (behaviorally equivalent to the pattern; no behavior change)
- [x] Mutation probes: for each new arm, apply its named flip probe, confirm the matching arm flips while the others keep their verdicts (arms `payload_files_line_then_reopen_collects` and `second_real_files_block_unlisted_fails` flip together under the shared pre-r1-F1 revert; record any additional sibling arms that flip with it), then revert the probe
- [x] Corpus shape probe (path-shape origin disposition): sweep `docs/plans/**/*.md` task Files lists and Review Scope category blocks for slash-less suffix-less path tokens and for bold-wrapped backticked paths; record the zero-hit counts in the commit message; leave `REVIEW_SCOPE_DOC_SUFFIXES`, `REVIEW_SCOPE_IMPLEMENTATION_SUFFIXES`, and the leading-span markup handling byte-unchanged (accepted tails; condition not met)
- [x] Run → expect GREEN: `python3 scripts/plan_readiness.py --selftest` passes with all new arm names present and every pre-existing arm name still present
- [x] Note in the commit message: the F10 coupling gap (meta rows probe `_validate_arm` directly, so removing the arm loop's call flips nothing) stays deferred because a flipping witness would require an invalid arm-table row, which the table must never carry
- [x] Commit: `test: plan_readiness solo-witness arms for backtick, payload, boundary, and echo shapes`

### Task 3: doc-registry r5 prose residuals (items 1 and 2; item 3 record-only)

Files:
- `agents/skills/doc-hierarchy/SKILL.md`
- `scripts/doc_registry_validator.py`

- [x] In `agents/skills/doc-hierarchy/SKILL.md` line 124, replace "except for three bounded warn tiers" with "except for three further bounded warn tiers" (matching the validator module docstring's "Three further warn tiers"; the sentence already lists the three warn paths, so no listing change)
- [x] In `scripts/doc_registry_validator.py` near lines 1751-1752, delete the duplicated word in the selftest comment so "(argparse / argparse independently rejects" reads "(argparse independently rejects" (the duplication wraps across a comment-line break, which is why the validation gate below is wrap-tolerant)
- [x] Item 3 disposition (no edit): the duty-wording nit lives in the archived plan `docs/plans/completed/2026-09-13-doc-registry-validator-residuals.md`, which is frozen history; this checklist item is the disposition of record and requires no file change
- [x] Run → expect GREEN: `python3 scripts/doc_registry_validator.py --selftest` (148 checks) passes
- [x] Commit: `docs: doc-registry r5 prose residuals (warn-tier scoping, selftest comment)`

### Task 4: graphify skill and package version-drift guard

Files:
- `agents/skills/graphify/SKILL.md`
- `agents/skills/graphify/references/` *(refreshed only if the update path runs)*

- [x] Add a version-compat preflight at the top of "Step 1 - Ensure graphify is installed": run the version probe (`graphify --version`) and treat the warning shape `warning: skill is from graphify <skill-version>, package is <package-version>. Run 'graphify install' to update.` (quoted verbatim from the live probe of 2026-09-17) as a blocking preflight result: do not run build, query, path, or explain steps on mismatched guidance
- [x] Prescribe the one supported update path in the skill: `graphify install --platform agents` (the agents platform maps to this repo's `agents/skills/` runtime layout), then verify `git status` in the repo shows changes confined to `agents/skills/graphify/`, diff-review the refreshed files and carry forward any repo-local edits per the vendored-sync rules, run the public-hygiene scan, and commit the refresh as its own commit `feat: refresh vendored graphify skill to match package`; then re-run the version probe and expect the warning gone
- [x] Prescribe the fallback: when the refresh cannot run (offline host, hostile diff, unsupported platform), the skill prints the actionable mismatch with both versions and continues only with flag guidance derived from `--help` output of the installed package for steps whose flags may have drifted; the existing host-neutral subagent fallback paragraph (near line 164) stays byte-unchanged
- [x] Regression check: this plan's Validation Commands gate both anchors (preflight warning shape and update path) in the committed skill file; record the live probe output for the record
- [x] Run → expect: both Task 4 validation greps pass; `graphify --version` output recorded in the task log
- [x] Commit: `feat: graphify version-drift preflight and supported update path`

### Task 5: canonical writing contract (Globish origin)

Files:
- `projects/.ai-playbook/agent_workflow_guidelines.md`
- `agents/skills/slack-message/SKILL.md`
- `agents/skills/jira-workflow/SKILL.md`
- `agents/skills/review-confluence-doc/SKILL.md`
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/github-pr-workflow/SKILL.md`
- `agents/skills/review-agents/documentation.md`

- [x] Expand guidelines section 45 in place into the canonical writing contract, keeping its number and title stem so external references stay valid: ordered priorities (1 preserve meaning and accuracy, 2 be concise, 3 use plain Globish, 4 keep only audience-relevant jargon, 5 define uncommon terms on first use or add a Terms section, 6 verify the final text before saving); a decision table by audience and artifact (Slack messages and comments: short, outcome-first; Jira business text: compact and business-facing; contracts, plans, and review findings: complete but compressed; code comments: excluded, delegated to the documentation review lens); the jargon threshold (widely shared technical vocabulary such as API or JSON stays when the audience needs it; team-local abbreviations and unexplained metaphors are replaced or defined); and a final-pass checklist (remove duplicated context, generic introductions, stale drafting history, unnecessary headings, unexplained abbreviations, and sentences that do not change the reader's next action)
- [x] Add the compression invariant to the contract: shorter text must not drop uncertainty, acceptance criteria, safety constraints, or the author's actual decision
- [x] Add the session-language invariant to the contract: an explicit user-selected conversation language is a session invariant inherited by resumed turns, compacted context, delegated review updates, and final responses; English is the default when none was selected; the consistency check preserves code, quoted source text, and user-requested translations
- [x] Add the human-finalization boundary to the contract: the agent may prepare a draft; the user reviews, edits, and verifies meaning; only the user sends; improving writing quality never authorizes direct posting or skipping review
- [x] Add one compressed before/after example pair for a Slack-like message and one for a review comment inside section 45, and give the decision table a row for each origin surface class (Slack-like message, Jira item, Atlassian comment, PR/review comment, code comment), with the two worked pairs as anchors; the table rows are normative for classes without a worked pair
- [x] Reconcile `slack-message`: point to the canonical contract; keep only surface-specific rules; verify the existing draft-only and user-sends wording already states the finalization sequence and strengthen it only if a step is ambiguous
- [x] Reconcile `jira-workflow`, `review-confluence-doc`, `doing-code-review`, `github-pr-workflow`: each points to the canonical contract and keeps only surface-specific constraints (jira's size limits, first-use expansion, and em-dash scan stay)
- [x] Reconcile `review-agents/documentation.md`: point to the canonical contract as the owner of comment prose rules; the shared plain-language section's code-comment exclusion stays, now with the explicit delegation named
- [x] No-duplication witness: each reconciled surface loses its restated policy prose and keeps only the pointer plus surface-specific constraints; the final-pass checklist phrasing lives only in guidelines section 45 (gated below)
- [x] Run → expect: the Task 5 validation greps pass, including the duplication tripwire
- [x] Commit: `docs: canonical writing contract in guidelines 45 with skill reconciliation`

### Task 6: Finder AppleScript inline-reference rule

Files:
- `projects/.ai-playbook/agent_workflow_guidelines.md`

- [x] Append section 65 titled "Finder AppleScript: Inline References and Per-Step Invocations" with the rule: write Finder AppleScript with fully inline element references at each use site (for example `duplicate (file n of src) to folder "X" of folder "Desktop" of home`); never assign a folder reference to a variable by re-resolving its name, because `set target to folder "X" of folder "Desktop" of home` fails with error -10006 (access not allowed) even when `exists folder "X" of ...` returns true and the folder was created fine; split create and copy into separate `osascript` invocations with an `exists` check between them, since a failed mid-script run still persists created folders; `killall Finder` clears a wedged Finder (the documented CloudStorage wedges) but is not required for the -10006 shape
- [x] Run → expect: the Task 6 validation grep passes
- [x] Commit: `docs: Finder AppleScript inline-reference rule (guidelines 65)`

### Task 7: externally-mutable agent memory files rule

Files:
- `projects/.ai-playbook/agent_workflow_guidelines.md`

- [x] Append section 66 titled "Agent Memory Files Are Externally Mutable" with the rules: re-read a memory file immediately before every edit to it and never rely on read-state from earlier in the session (the host may normalize or fold memory content between turns); prefer one full-file write per turn over successive edits when several sections must change; on a modified-since-read failure, re-read, diff the fresh content against the intended change, and retry once; never rewrite blind and never assume the earlier edit was lost and duplicate it
- [x] Run → expect: the Task 7 validation grep passes
- [x] Commit: `docs: externally-mutable agent memory files rule (guidelines 66)`

### Task 8: done-record test-count drift lesson (r5-trim F2)

Files:
- `projects/.ai-playbook/development_lessons.md`

- [x] Run the live suite and record actual counts in the task log: `( cd scripts && python3 -m unittest test_execute_plan_runtime -q )` (authoring baseline 2026-09-17: 137 tests, all green; the origin's recorded 136 is already stale, which is the lesson's point; execution-time counts are recorded live and are expected to have drifted)
- [x] Append the test-count drift lesson as the next free number (authored as 352; 352 was already taken, landed as 371): completion records that state test counts drift whenever a late witness lands; the corrected arithmetic belongs in the fix commit message and the lessons corpus; an archived plan body is frozen history and is never edited to chase the number (doc-hierarchy); carry the origin's corrected arithmetic as the witness: the r5-trim record said 135 total with seventeen witnesses while the final tree ran 136 with nineteen added definitions, and the count has drifted again since
- [x] Refresh the learn-class skill-gate marker per `agents/hooks/skill-gate/README.md` before writing to the lessons corpus
- [x] Run → expect: the Task 8 validation grep passes
- [x] Commit: `docs: lesson 371 done-record test-count drift (plan's 352 already taken; next free number used)`

### Task 9: archive the eight origins with registry rows

Files:
- `docs/history/backlog/completed/2026-09-13-doc-registry-r5-prose-residuals.md` *(moved)*
- `docs/history/backlog/completed/2026-09-13-plan-readiness-path-shape-suffix-and-markup-tails.md` *(moved)*
- `docs/history/backlog/completed/2026-09-13-plan-readiness-solo-witness-gaps.md` *(moved)*
- `docs/history/backlog/completed/2026-09-14-runtime-r5-trim-review-exit-residuals.md` *(moved)*
- `docs/history/backlog/completed/2026-09-16-cross-surface-globish-brevity-policy.md` *(moved)*
- `docs/history/backlog/completed/2026-09-16-graphify-skill-package-version-drift.md` *(moved)*
- `docs/history/backlog/completed/2026-09-16-finder-applescript-folder-reference-10006.md` *(moved)*
- `docs/history/backlog/completed/2026-09-16-zcode-memory-files-external-rewrites.md` *(moved)*
- `docs/maintenance/document-registry.md`

- [x] Move each of the eight origin files to `docs/history/backlog/completed/` marking `Status: done` in the same edit, as a plain line-start literal: the graphify origin carries a bold-wrapped `**Status:** open`, so replace that whole status line with the plain `Status: done` form (the loop's `grep -q "^Status: done"` witness fails loudly on any bold-wrapped variant)
- [x] Append exactly one ownership-registry row per moved item in registry column order (identity, sot: no, state: completed, archived: today, src), identity = filename minus the date prefix and extension
- [x] Run → expect: the Task 9 validation loop passes for all eight archived basenames and their registry identities
- [x] Commit: `backlog: archive long-tail origins closed by the long-tail plan`
