# Plan: Wire the Prompt-Log Prune Audit Into Landing

Backlog origin: docs/history/backlog/2026-10-28-landing-gate-prune-audit-wiring.md
Driving force: correctness; secondary: code-quality
Execution budget: 1h total, largest task 0.75h
Authoring claim: docs/tmp/authoring-claims/2026-10-28-landing-gate-prune-audit-wiring.md (session 01a17c5b-bdc9-7781-86f5-38e0cd2c16dd)

## Terms

- **Prompt log:** either `docs/history/backlog/PLAN-PROMPTS.md` or `docs/history/backlog/EXEC-PROMPTS.md`.
- **Prune audit:** the existing `scripts/check_prompt_log_origins.py --prune-audit` check that verifies each removed entry has a valid witness in the commit that removed it.
- **Landing receipt:** the `land-worktree` helper's stdout record of each gate result, including the audit output.
- **Landing range:** every commit after the source branch's merge base with the current base tip through the verified source tip; a later revert does not erase an earlier touch from this range.

## Why

The landing helper checks base freshness, archive egress, tree equality, and commit parentage, but it does not run the existing prompt-log prune audit. A prompt-log removal without its same-commit receipt can therefore land when a session or review panel misses the documented manual check. The checker already identifies the exact removal and commit, so the smallest fix is to wire it into the affected landing path.

## Gist & Examples

Wire the existing prune audit into prompt-log-changing landings so receipt-less removals are caught before the landing ref moves.

Before, `land-worktree` could land a branch that changed a prompt log without running the check. After, it runs the audit only when a commit in the landing range touched either prompt log, and reports the audit result with the landing gates. For example, a code-only branch follows the current path without invoking the audit; a branch removing an entry without its receipt is refused with the slug and commit printed, followed by the existing same-commit receipt repair and retry steps.

## Outcome

A worktree landing that changes either prompt log cannot land a receipt-less removal.

- Prompt-log changes are checked before commit composition and before the base ref moves.
- Code-only landings retain their current checks and outcomes.
- A failed audit identifies the entry and commit and gives the bounded repair needed to continue.

Gate delta: wire the existing audit into `land-worktree` for ranges that touched either prompt log and add an optional explicit upper endpoint to the existing checker; no audit classification or refusal class changes. The current guard-liveness ledger is 29 catches to 48 incidents (29:48). The user authorized this narrow, witnessed growth with the condition that unrelated landings gain no blocking behavior; the invocation is skipped when neither log appears in the landing range.

## Assumptions

- The audit runs against the computed merge base and the exact verified source-tip commit. Pass that commit through a new optional checker `--head <commit>` argument; callers that omit it retain the existing `HEAD` behavior. Pass an existing rolling prompt-log path as the worktree anchor; when one log was deleted, pass its existing sibling because the checker audits both logs from either anchor. Basis: `prune_audit_cli` requires an existing explicit path and resolves that path's worktree, while the checker can enumerate the explicit `base..head` range and add the sibling log.
- If either prompt log was touched in the landing range, one audit invocation is sufficient because the checker automatically includes the sibling rolling log. Basis: the checker CLI contract.
- Audit exit 1 is the modeled finding refusal; exit 3 or an unclassified tool result is a named tool error. Preserve both streams and keep the landing ref unchanged. The invoking workflow routes a tool error through the existing `self-heal` recovery once: diagnose the reported cause, apply only an already-authorized correction, rerun the audit, and continue only on exit 0; if it persists, park with the exact evidence and next action. Never bypass the audit. Basis: the checker CLI contract, the helper's fail-closed tool-error convention, and the existing `self-heal` recovery contract.
- The helper does not edit prompt logs. For a receipt-less removal, the single repair is to add its receipt in the removal commit, squash or recommit that pair as required by lesson 234, and retry. Existing workflow recovery invokes `self-heal` for this recoverable refusal, so the routine repair does not require a user decision. Basis: lesson 234 and the standing recovery contract.
- The user's net-growth approval is limited to the witnessed prune-audit failure class and to the path-scoped invocation described here. It does not authorize new refusal classes or changes to other landing modes.

Decision points requiring a grill: none remain.

## Standing constraints

- Add the audit call only to the `land-worktree` critical section and only when any commit in the landing range touched either rolling prompt log. Detect commit history with rename detection disabled, so deletion, rename, and a later revert cannot hide a touch; do not rely only on the endpoint tree diff. Pass the already verified source-tip commit as the checker upper endpoint so a concurrent worktree `HEAD` move cannot change the audited history.
- Run the audit after `check-landing` passes and before the landing commit is composed; use the actual merge base, verified source-tip commit, and source worktree. Pass the verified tip with `--head`; pass an existing rolling log as the checker anchor, selecting the sibling when the touched log was deleted.
- Invoke the checker once when either or both logs were touched. Preserve its stdout and stderr in the landing receipt; retain each `PRUNE-OK` line the checker emits, and accept its passing summary when the range has no removal and therefore emits no `PRUNE-OK` line.
- On audit exit 1, refuse before any landing ref update and print one direct repair: put the receipt in the removal commit, squash or recommit per lesson 234, then retry. On exit 3 or an unrecognized result, preserve diagnostics, return the named tool error without moving refs, and let the invoking workflow run the single existing `self-heal` recovery and retry the audit; if it still fails, park with the exact error and repair action.
- Add only an optional `--head <commit>` range endpoint to `check_prompt_log_origins.py`, keeping `HEAD` as the default for existing callers and leaving audit classifications unchanged. Do not mutate either prompt log from the helper or change `land` mode, other gates, surveys, or unrelated landings.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: every prompt-log-changing landing runs the audit over its own commit range before the ref move.
- Scope: no prompt-log path in the landing range means no new audit invocation or refusal class.
- Recovery: a missing receipt refusal names the exact finding and one direct repair; ordinary repair proceeds without asking the user.

**Done when:** `scripts/test_check_prompt_log_origins.py` proves `--head` audits the pinned commit when current `HEAD` has moved, while omitted `--head` retains existing behavior; `scripts/test_land_squash.py` covers commit-history touch detection including a changed-then-reverted log and a log rename, one audit call for one or both logs, use of the surviving sibling when one touched log is deleted, passing summary output with `PRUNE-OK` retained when emitted, exit-1 refusal before the ref move with one actionable repair, exit-3 and unclassified tool-error output preservation with refs unchanged, a pinned-tip argument, updated helper and checker help/summary text, and unchanged code-only landing behavior. The landing tests do not require `PRUNE-OK` when the checker reports no removals.

**Ship when:** the plan is reviewed and certified ready for execution.

## Documentation Impact Assessment

The backlog origin and lesson 234 already hold the incident and repair procedure. No separate incident dossier or new audit mode is needed; the checker module documentation, CLI help, and summary document the optional endpoint, while existing callers keep the `HEAD` default; the helper's landing receipt is the operational output for this gate.

## Review Scope

**Explicit must-fix:**

**Production code:**
- `scripts/land_squash.sh` (Task 1)
- `scripts/check_prompt_log_origins.py` (Task 1)

**Tests:**
- `scripts/test_land_squash.py` (Task 1)
- `scripts/test_check_prompt_log_origins.py` (Task 1)

**Review-only dependency:**
- `docs/maintenance/development_lessons.md` (review-only)

**Plan-related extension:** implementation and review may change files not listed above only when a finding is causally required by the scoped gate, fixes a regression it introduces, or closes wiring explicitly required by this plan. If the link is weak or speculative, report it out of scope.

**Out of scope; reject unless plan-related:**
- Changes to the prune audit's classifications or removal-witness rules.
- Changes to `land` mode, maintenance survey behavior, or other landing guards.
- New standalone validators, hooks, registries, or receipt-repair mechanisms.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_land_squash.py'
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_check_prompt_log_origins.py -q
bash scripts/check-no-em-dash.sh touched
bash scripts/scan-public-hygiene.sh
```

### Task 1: Run the existing prune audit for prompt-log-changing worktree landings

Context surface: this task, `## Terms`, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/land_squash.sh`
- `scripts/check_prompt_log_origins.py`
- `scripts/test_land_squash.py`
- `scripts/test_check_prompt_log_origins.py`
- `docs/maintenance/development_lessons.md` (review-only)

Primary class anchors:
- `MODE` in `scripts/land_squash.sh`
- `prune_audit_cli` in `scripts/check_prompt_log_origins.py`
- `LandSquashHelperTest` in `scripts/test_land_squash.py`
- `TestPromptLogPruneAudit` in `scripts/test_check_prompt_log_origins.py`

- [x] Determine whether either rolling prompt log was touched by any commit after the merge base through the verified source tip, including deletion, rename, or a touch later reverted; inspect commit history with rename detection disabled. When neither was touched, do not invoke the prune audit and keep the existing code-only landing path unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Add optional `--head <commit>` to the prune-audit CLI, defaulting to `HEAD` for existing callers, and use the supplied commit for both the audited `base..head` range and its reported tip identity. [class: IMPLEMENTATION_REQUIRED]
- [x] Update the checker module documentation, `--prune-audit` CLI help, and audit summary to describe the optional pinned upper endpoint and report the actual `base..head` range. [class: IMPLEMENTATION_REQUIRED]
- [x] When one or both prompt logs were touched, run `python3 scripts/check_prompt_log_origins.py --prune-audit --base <merge-base> --head <verified-source-tip> <existing-source-worktree-log>` exactly once after `check-landing` passes and before commit composition; use either existing rolling log as the checker anchor, choosing the sibling if the touched log was deleted, and verify both paths from the current repository layout. [class: IMPLEMENTATION_REQUIRED]
- [x] Preserve the checker's stdout and stderr in the landing receipt. On exit 0, continue, retaining any `PRUNE-OK` lines and accepting the passing summary when there were no removals. [class: IMPLEMENTATION_REQUIRED]
- [x] On exit 1, return `OUTCOME: fail` before the ref update with the exact finding and same-commit receipt repair. [class: IMPLEMENTATION_REQUIRED]
- [x] On exit 3 or an unclassified result, return a named tool error with refs unchanged. The invoking workflow runs one existing `self-heal` diagnosis/correction/retry; if it fails again, park with the exact evidence and next action. Never bypass the audit. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a code-only source range, expect no audit call and unchanged landing output and ref behavior. [class: REPOSITORY_TEST]
- [x] Given commit history that touches either log, including a change later reverted or a rename, expect one audit call; given a valid receipt, expect a passing summary in the receipt and normal landing, with `PRUNE-OK` retained when emitted. Given changes to both logs, expect one invocation to audit both; given deletion of one log, expect the surviving sibling to anchor the audit. [class: REPOSITORY_TEST]
- [x] Given a prompt-log removal without its receipt, expect the audit to name the removed slug and commit, `OUTCOME: fail`, the single direct repair, and no landing ref update. [class: REPOSITORY_TEST]
- [x] Given checker exit 3 or an unclassified exit, expect a named tool-error outcome, preserved stdout and stderr, and no landing ref update or fallback. [class: REPOSITORY_TEST]
- [x] Given the worktree `HEAD` moves to a same-tree commit with different removal-receipt history after the source tip was verified, expect the checker to audit the pinned source-tip commit, so its result still governs the exact tree the helper will land. [class: REPOSITORY_TEST]
- [x] Update `land-worktree --help` to name the prompt-log audit, its scoped trigger, and the direct recovery for a missing receipt or persistent tool error. [class: IMPLEMENTATION_REQUIRED]
- [x] Verify `scripts/test_check_prompt_log_origins.py` covers the updated checker help and pinned-tip summary. [class: REPOSITORY_TEST]
- [x] Run the focused helper suite and the plan's validation commands. [class: REPOSITORY_TEST]
- [x] Commit: `fix: gate prompt-log landings on prune audit` [class: IMPLEMENTATION_REQUIRED]
