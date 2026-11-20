# Plan: stack-review-fix-round-ownership

Backlog origins (scope of record):
- docs/history/backlog/2026-11-09-stack-post-publish-review-fix-round-procedure.md
- docs/history/backlog/2026-11-09-pr-description-and-verification-claims-go-stale.md
- docs/history/backlog/2026-11-09-receiving-review-round-authorization-single-ask.md

Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/2026-11-14-plan-review-stack-review-fix-round-ownership-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 2.5h total, largest task 1h
Executed: yes (f24f0ad13)
Authoring claim: 2026-11-09-stack-post-publish-review-fix-round-procedure.md (session sess_a18daf46-38cd-474c-9025-08e7721e0fd4)

## Terms

- Published stack: a sequence of stacked task branches, each with a draft PR whose base is the predecessor branch, already pushed to the remote.
- Review-fix round: the loop after an external reviewer's finding lands on a branch inside a published stack: edit the lowest affected branch, restack descendants, retest affected branches, push, reply, resolve, refresh descriptions.
- Affected branches: the lowest branch carrying an edit plus all its descendants in the stack.
- Old tip: the branch head captured before an amend or fix commit; the restack range base whose ancestry into each descendant branch's tip anchors the replay range and prevents replaying the whole stack.
- Method C: the explicit-rebase restack method in `agents/skills/update-stacked-branches/SKILL.md`; the helper wraps its mechanical shape (backup refs before any tip rewrite, per-link `git rebase --onto` in stack order, per-link parentage verification) and observes its hard rules, never bypassing them.
- Lease push: `git push --force-with-lease=<branch>:<remote-tip>` with the remote tip read from `ls-remote` immediately before the push; protected branch names (trunk, default, main, master) refuse a force push.
- Head-bound line: a PR description sentence or plan checkbox verification line that names the head commit it applies to, or states only what was run, or is omitted.
- Enumerated ask: one authorization prompt per review-fix round listing the exact set: branches with lease SHAs, reply count and target threads, bot threads to resolve, description refreshes.
- Retest set: the project test policy's commands scoped to affected branches only.
- Description refresh: re-deriving each pushed PR's description after the push so it matches the new head.
- Bot thread: a review thread authored by an automated reviewer; resolvable after a reply per the source adapter's rules.

## Why

A review-fix round on a published stack is rebuilt by hand every time, and the rebuilds fail mechanically: one session ran about six rounds with 17 zsh-shaped transcript errors, two failed force-push attempts, and one wrong-range restack that replayed the whole stack into conflicts (docs/history/backlog/2026-11-09-stack-post-publish-review-fix-round-procedure.md). Descriptions and checkbox verification claims went stale after every push until the operator noticed (docs/history/backlog/2026-11-09-pr-description-and-verification-claims-go-stale.md), and the round cost nine separate approval-only operator turns across five rounds (docs/history/backlog/2026-11-09-receiving-review-round-authorization-single-ask.md).

## Gist & Examples

TLDR: one owner for the post-publish review-fix round on a published stack (round section, bash helper, head-bound wording, one enumerated ask), because every round was rebuilt by hand with mechanical push and restack failures.

Before: the agent improvises each step: captures the restack range from memory (one wrong range replayed the whole stack into conflicts), pushes with a stale lease (two failed attempts before any ref moved), retypes the same summary nine times for approval, and leaves PR descriptions claiming results from heads that no longer exist.

After: `bash scripts/stack_review_round.sh affected|restack|retest-set|push-leases|verify-heads` performs the mechanical steps with verified outcomes; the execute-plan-stack round section names one owner per step and declares bash the required shell; PR description and checkbox verification lines are head-bound and every push ends with a description refresh; receiving-review asks once per round with the enumerated set.

## Outcome

After execution, a review-fix round on a published stack has one documented owner per step and mechanical helpers for the failure-prone steps.

- Restack uses the pre-captured old tip, so a wrong range cannot replay the whole stack.
- Every push is a lease push built from fresh remote tips, and heads and bases verify after the push.
- PR descriptions and checkbox verification lines carry the head they describe or state only what was run.
- One enumerated ask per round authorizes the listed set; replies still post only after the push verifies.

Gate delta: none (no gate, validator, lock, ledger, or required ceremony is added; the helper wraps existing commands and verifies their outcomes; the skill edits are prose rules; no refusal class is added or removed).

Follow-up disposition: gaps discovered while using the round procedure route as backlog rows with ready-to-dispatch prompts; helper subcommand gaps discovered in the first uses are backlog rows naming the missing subcommand and the witnessed invocation, never silent helper edits outside a plan.

## Assumptions

- assume the helper is a bash script invoked as `bash scripts/stack_review_round.sh <subcommand> ...`; basis: the witnessed zsh word-splitting failures (17 transcript events, origin row one) and the repository's existing bash helpers (scripts/done-lock.sh, scripts/land_squash.sh).
- assume Method C stays the restack method of record and the helper wraps its ordering instead of re-deriving it; basis: origin row one rejects folding the round into update-stacked-branches while requiring reuse of Method C.
- assume the retest set is derived for affected branches only and the project test policy (facts: focused-never-full) stays the owner of what runs; basis: origin row one's retest arm.
- assume the enumerated ask authorizes exactly its listed set and any new action needs a new ask; basis: origin row three's recommended arm and the standing hard rule that approval does not carry across actions or contexts.
- assume replies post only after the push verifies, unchanged; basis: origin row three's preserved ordering and the receiving-review skill's existing rules.
- assume description generation from the run record stays rejected; basis: origin row two's recorded rejection (prose carries design rationale; no second witness).

Decision points requiring a grill: none remain.

## Standing constraints

- The repository's hygiene gates bind every inserted skill byte: the public hygiene scan and the no-em-dash gate run over prescribed insertions before each review round.
- Skill text growth is budgeted: files under a byte cap grow only within the cap (scripts/skill_text_budget.py, blocking posture); the touched files are within caps or uncapped at authoring time.
- Bash is the required shell for the skills' shell snippets touched by this plan; snippets avoid zsh-only expansions.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each helper subcommand's outcome is verified by the focused suite against real git fixtures (scratch repos under mktemp -d with teardown), including the wrong-range and stale-lease refusals.
- reliability: lease tips are read from ls-remote immediately before each push and remote heads verify after; the restack ordering pins old-tip capture before the amend.
- maintainability: each round step names one owner; Method C stays the restack method of record and the helper wraps its mechanical shape while observing its hard rules; no gate or validator is added.
- usability: the enumerated ask lists every authorization the round needs; bash is declared as the required shell where snippets are prescribed.

**Done when:**
- `bash -n scripts/stack_review_round.sh` exits zero.
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_stack_review_round.py -q` passes.
- Every Validation Commands gate exits zero over the executed tree.

**Ship when:**
- None: the change is complete when the repository checks above pass; the round procedure's first live use on a real stack is operational use, not a release condition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/stack_review_round.sh` (Task 1) *(new)*

**Skills (workflow docs):**
- `agents/skills/execute-plan-stack/SKILL.md` (Task 2)
- `agents/skills/github-pr-workflow/SKILL.md` (Task 3)
- `agents/skills/execute-plan/implementation-loop.md` (Task 3)
- `agents/skills/receiving-review/SKILL.md` (Task 4)

**Tests:**
- `scripts/test_stack_review_round.py` (Task 1) *(new)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/update-stacked-branches/SKILL.md`; reason: Method C is reused by reference and this plan must not edit it (origin row one's scope).
- `agents/skills/done/SKILL.md`; reason: the push and reply separation is preserved as written; no edit.
- `docs/AGENTS.md`; reason: the push hard rule is context, not a surface this plan edits.

## Validation Commands

Pinned-command record (authoring time, over the plan bytes): the whole block below was executed today against the current tree; the first actually-failing gate is the Task 1 `bash -n` check (file absent, fail-closed exit), the Task 1 pytest gate is unreachable behind it (helper and suite absent), and every per-file grep gate was executed individually and is RED today (its phrase absent in every touched skill file, including the Task 4 preserved-ordering phrase "after the push verifies"). All gates are expected to flip GREEN exactly when their task lands; none passes vacuously today.

```bash
REPO="$(git rev-parse --show-toplevel)"; cd "$REPO" || exit 1
fail() { echo "VALIDATION FAIL: $1"; exit 1; }

bash -n scripts/stack_review_round.sh || fail "helper syntax (Task 1)"
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_stack_review_round.py -q || fail "helper focused suite (Task 1)"

grep -qF "### Post-publish review-fix round" agents/skills/execute-plan-stack/SKILL.md || fail "round section heading (Task 2)"
grep -qF "bash is the required shell" agents/skills/execute-plan-stack/SKILL.md || fail "bash declaration (Task 2)"
grep -qF "scripts/stack_review_round.sh" agents/skills/execute-plan-stack/SKILL.md || fail "helper wired in round (Task 2)"
grep -qF "refresh-descriptions" agents/skills/execute-plan-stack/SKILL.md || fail "refresh step in round (Task 2)"

grep -qF "names the head" agents/skills/github-pr-workflow/SKILL.md || fail "head-bound description rule (Task 3)"
grep -qF "last run on" agents/skills/github-pr-workflow/SKILL.md || fail "ran-on form (Task 3)"
grep -qF "command plus head" agents/skills/execute-plan/implementation-loop.md || fail "tick receipt rule (Task 3)"

grep -qF "one enumerated ask per round" agents/skills/receiving-review/SKILL.md || fail "enumerated ask (Task 4)"
grep -qF "after the push verifies" agents/skills/receiving-review/SKILL.md || fail "reply-after-push preserved (Task 4)"

echo "VALIDATION OK"
```

### Task 1: Round helper with focused suite

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/stack_review_round.sh` *(new)*
- `scripts/test_stack_review_round.py` *(new)*

Primary class anchors:
- `cmd_affected` in `scripts/stack_review_round.sh`
- `cmd_restack` in `scripts/stack_review_round.sh`
- `cmd_push_leases` in `scripts/stack_review_round.sh`
- `cmd_verify_heads` in `scripts/stack_review_round.sh`
- `cmd_retest_set` in `scripts/stack_review_round.sh`

- [x] `cmd_affected` delivers affected-set derivation: given a stack base, the stack's ordered branch chain lowest-first as recorded in the stack run record, and the edited branch names, expects the lowest edited branch plus its chain descendants in chain order [class: IMPLEMENTATION_REQUIRED]
- [x] `cmd_restack` delivers ordered restack wrapping Method C's shape: given the pre-captured old tip of the amended branch and its new tip, expects a backup ref for every rewritten tip before any rewrite, then per descendant in chain order `git checkout <descendant>` plus `git rebase --onto <amended-new-tip> <old-tip> <descendant>`, and given a missing old-tip argument, expects refusal naming the old tip before any rebase runs [class: IMPLEMENTATION_REQUIRED]
- [x] `cmd_restack` delivers per-link parentage verification: after each link, expects the descendant's base verified against its predecessor's new tip and, on a parent reversal or conflict, expects `git rebase --abort` plus restore from the backup refs and a nonzero exit [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a recorded old tip that is not an ancestor of a descendant branch's tip, `cmd_restack` expects refusal before replaying that descendant [class: IMPLEMENTATION_REQUIRED]
- [x] `cmd_push_leases` delivers lease push: given branches with remote tips, expects one `git push --force-with-lease=<branch>:<remote-tip-read-from-ls-remote>` per branch, given a protected branch name (trunk, default, main, master) expects force-push refusal before any remote call, and given a remote tip that moved between read and push, expects the push refusal reported per branch [class: IMPLEMENTATION_REQUIRED]
- [x] `cmd_verify_heads` delivers head and base verification: given expected base and head per branch, expects one `ls-remote` comparison per branch reporting equality or the observed mismatch [class: IMPLEMENTATION_REQUIRED]
- [x] `cmd_retest_set` delivers the retest set: given the affected branches and the policy-derived command set passed by the caller, expects the command set scoped to the affected branches printed for the caller; the project test policy stays the owner of what runs and the helper never encodes project commands [class: IMPLEMENTATION_REQUIRED]
- [x] The helper emits the final `OUTCOME: <pass|fail|indeterminate|tool_error>` line per run matched to its exit code per `scripts/OUTCOME_CONTRACT.md`, declaring conformance in its header like `scripts/done-lock.sh` [class: IMPLEMENTATION_REQUIRED]
- [x] The helper reads remote tips through an overridable ls-remote command (environment override) so the focused suite can interpose a stale tip between read and push deterministically [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the focused suite fails before the helper exists (missing module), then each fixture turns its case green; RED fixtures build scratch git repos under `mktemp -d` with explicit teardown [class: REPOSITORY_TEST]
  receipt: ModuleNotFoundError collection error witnessed pre-creation, then `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_stack_review_round.py -q` 20 passed, last run on bd0f6e6a3
- [x] Commit: `feat: round helper for published-stack review fixes` [class: IMPLEMENTATION_REQUIRED]
  receipt: git log shows 33eb4f1fb with exactly that message, last run on bd0f6e6a3

### Task 2: Round section in execute-plan-stack

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan-stack/SKILL.md`

Primary class anchors:
- `## Workflow` in `agents/skills/execute-plan-stack/SKILL.md`

- [x] The `### Post-publish review-fix round` section exists directly after the Workflow list [class: IMPLEMENTATION_REQUIRED]
- [x] The section names one owner per step: affected and restack via `bash scripts/stack_review_round.sh` with Method C as the restack method of record (reused by reference from `agents/skills/update-stacked-branches/SKILL.md`), retest via the helper's retest set under the project test policy, push via the helper's lease push [class: IMPLEMENTATION_REQUIRED]
- [x] The section routes replies and resolution to `receiving-review` and the description refresh to `github-pr-workflow` [class: IMPLEMENTATION_REQUIRED]
- [x] The section states the precedence rule against workflow step 8: while an execute-plan-stack run is still active, step 8's `update-stacked-branches` hand-off governs fixes on that run's own tasks; the post-publish round section governs review-fix rounds on the published stack after the claim release [class: IMPLEMENTATION_REQUIRED]
- [x] The section states "bash is the required shell" for the snippets it prescribes and carries the refresh-descriptions step as the round's closing step after every push [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Task 2 grep gates pass over the executed tree [class: REPOSITORY_TEST]
  receipt: grep -qF "### Post-publish review-fix round" agents/skills/execute-plan-stack/SKILL.md && grep -qF "bash is the required shell" agents/skills/execute-plan-stack/SKILL.md && grep -qF "scripts/stack_review_round.sh" agents/skills/execute-plan-stack/SKILL.md && grep -qF "refresh-descriptions" agents/skills/execute-plan-stack/SKILL.md, last run on a4e29e655
- [x] Commit: `docs: post-publish review-fix round section in execute-plan-stack` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Head-bound wording and tick receipts

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/github-pr-workflow/SKILL.md`
- `agents/skills/execute-plan/implementation-loop.md`

Primary class anchors:
- `## PR Descriptions and Stats` in `agents/skills/github-pr-workflow/SKILL.md`
- `Plan-file edits (skill-gate)` in `agents/skills/execute-plan/implementation-loop.md`

- [x] `github-pr-workflow` gains the head-bound description rule: a verification claim names the head it applies to, or states only what was run in the form "last run on `<short sha>`", or is omitted [class: IMPLEMENTATION_REQUIRED]
- [x] `github-pr-workflow` gains the description-refresh rule: after every push of a PR, refresh its description so claims match the new head before reporting the push done [class: IMPLEMENTATION_REQUIRED]
- [x] `agents/skills/execute-plan/implementation-loop.md` gains the tick receipt rule: a verification checkbox is ticked only with its receipt recorded (command plus head) beside the tick, matching how stack evidence already binds task evidence to a commit SHA [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Task 3 grep gates pass over the executed tree [class: REPOSITORY_TEST]
  receipt: grep -qF "names the head" agents/skills/github-pr-workflow/SKILL.md && grep -qF "last run on" agents/skills/github-pr-workflow/SKILL.md && grep -qF "command plus head" agents/skills/execute-plan/implementation-loop.md, last run on a4e29e655
- [x] Commit: `docs: head-bound verification wording and tick receipts` [class: IMPLEMENTATION_REQUIRED]

### Task 4: One enumerated ask per round

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/receiving-review/SKILL.md`

Primary class anchors:
- `Feedback-source Workflow` in `agents/skills/receiving-review/SKILL.md`
- `## Source Thread Replies` in `agents/skills/receiving-review/SKILL.md`

- [x] The workflow gains the enumerated ask rule at the end of the fix phase: one enumerated ask per round presenting exactly the branches to force-push with their lease SHAs, the reply count and target threads, the bot threads to resolve, and the description refreshes; one answer authorizes that listed set and nothing else, a new action needs a new ask, and the inserted rule states that replies post only after the push verifies [class: IMPLEMENTATION_REQUIRED]
- [x] The inserted enumerated-ask rule carries the preserved ordering phrase "after the push verifies" so the Task 4 gate binds to prescribed bytes [class: REPOSITORY_TEST]
  receipt: grep -qF "after the push verifies" agents/skills/receiving-review/SKILL.md, last run on bd0f6e6a3
- [x] Run → expect GREEN: the Task 4 grep gates pass over the executed tree [class: REPOSITORY_TEST]
  receipt: grep -qF "one enumerated ask per round" agents/skills/receiving-review/SKILL.md && grep -qF "after the push verifies" agents/skills/receiving-review/SKILL.md, last run on a4e29e655
- [x] Commit: `docs: one enumerated authorization ask per review-fix round` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-11-09-stack-post-publish-review-fix-round-procedure.md: covered by this plan (Task 1 helper, Task 2 round section).
- docs/history/backlog/2026-11-09-pr-description-and-verification-claims-go-stale.md: covered by this plan (Task 3 head-bound wording and description-refresh rule).
- docs/history/backlog/2026-11-09-receiving-review-round-authorization-single-ask.md: covered by this plan (Task 4 one enumerated ask per round).
