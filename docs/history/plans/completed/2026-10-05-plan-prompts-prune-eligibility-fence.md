# Plan: prompt-log prune-eligibility fence

Backlog origin: docs/history/backlog/2026-10-04-plan-prompts-prune-eligibility-fence.md
Driving force: code-quality
Plan review record: the staging series docs/reviews/2026-10-05-plan-review-plan-prompts-prune-eligibility-fence-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- Prompt log: the tracked rolling log `docs/history/backlog/PLAN-PROMPTS.md`; one `## <slug>` section per ready-to-dispatch authoring entry, most urgent first.
- Prune rule: the log's standing rule; an entry is removed when its plan file exists in the plans root (`docs/history/plans/` top level), evaluated at authoring closeout ("prune at authored").
- Prune-eligible: an entry whose plan-file witness exists, so removing it is sanctioned by the prune rule.
- Plan-file witness: a file under the plans root whose basename carries the removed entry's slug as a hyphen-bounded segment (for example slug `authoring-round-liveness-gap` matches basename `2026-10-04-authoring-round-liveness-gap.md`), or that file's twin under `docs/history/plans/completed/` when the removal rides the execution landing that archived the plan in the same landing.
- Prune receipt: the named `PLAN-PROMPTS-PRUNE:` output line a pruning pass prints per removed entry, carrying the entry slug and its plan-file witness path.
- Prune audit: the new removal-audit mode of `scripts/check_prompt_log_origins.py` (`--prune-audit --base <ref>`); it walks the commits that touched the prompt log in the base-to-HEAD range, parses each removal from the log diff, and classifies every removed entry against its plan-file witness at the removal commit.
- Removal commit: a commit in the audit range whose diff deletes one or more `## <slug>` entry headings from the prompt log.
- Landing closeout riders: the rider commits a plan landing or execution landing composes before its landing critical section (coverage flip bytes, prompt-log entry deletion, archive move, origin fold or deletion, ownership-registry row); the prune evaluation and the riders' bytes land on the landing branch so the squash commit carries them.
- Stale mode: the checker's existing behavior (`check_log`): flag an entry whose every origin is served; unchanged by this plan.
- Deferred-landing path: the execute-plan landing refusal route that keeps the branch and worktree, reports, and defers the landing to a later critical section instead of moving the ref.
- Outcome contract: the repo's four-outcome vocabulary (scripts/OUTCOME_CONTRACT.md): a gate exits 0 with a final `OUTCOME: pass` line, 1 with `OUTCOME: fail`, 2 with `OUTCOME: indeterminate`, 3 with `OUTCOME: tool_error`; a run ending without its final line reads as a tool error.
- Pins group: a named block of span assertions in `scripts/check_maintenance_pins.sh`; the pins suite is that script's full run.
- Maintenance survey: the maintenance skill's Step 1 read of the work surface (backlog, plans, log, consults) each scheduler turn; its consult family reports findings without blocking the turn.
- Standing authoring directive: the operator's standing instruction to author the most urgent uncovered issues one by one without stops (the directives home's D-4 record); it satisfies the plans skill's Phase 1 confirmation for unattended runs.
- SUPERSEDED-IN-COMMIT: the audit's third, report-only verdict for a removal in a commit that also adds a superseding entry (the sanctioned editorial merge shape); it is never a flag.

## Why

Two landing closeouts pruned the prompt log in bulk and removed live entries alongside their own dispatch entries: the codex-nonzero-exit-evidence landing `3032e750` deleted two entries in one edit while only one had a plan file at the plans root, and the review-cert-graded-binding prune `23349155` removed five entries of which four had no plan file, the nested-git-debris loss later misattributed by the re-emission commit `ee0492ac`; the lost prompts were recoverable only from git history. The prune rule states a per-entry condition but nothing binds a pruning pass to entries that satisfy it: there is no receipt naming each removal with its witness and no mechanical check detects a removed entry whose plan never landed.

## Outcome

Prompt-log pruning becomes per-entry witnessed and mechanically audited: a landing prunes only its own dispatch entry, every removal prints a receipt naming its plan-file witness, and the prune audit verifies removals at the landing closeout (fail-closed) and at the maintenance survey (consultative), so a removed-but-unlanded entry surfaces in the same turn or the next survey.

- A landing closeout that prunes prints one `PLAN-PROMPTS-PRUNE:` line per removed entry naming the slug and the witness path, and runs the prune audit before the rider commit; an audit refusal takes the landing's deferred-landing path.
- The prune audit classifies every removal in its range: `PRUNE-OK` when the plan-file witness exists at the removal commit (the clean self-prune `e81381d6` shape: the plan file landed in the same commit; the execution-rider shape with the `completed/` twin), `SUPERSEDED-IN-COMMIT` (report-only, never a flag) when the same commit also adds a superseding entry (the sanctioned merge `94e38903` shape), and `REMOVED-WITHOUT-WITNESS` (the flag) when neither holds (the witnessed `3032e750` and `23349155` shapes).
- The stale mode's verdicts, the log's targeted-section-edit discipline, and the freeze rule are untouched.

Gate delta: one new refusal class arrives, the landing-closeout prune-audit refusal (a log removal without its plan-file witness, exit 1, deferred-landing path), plus one consultative survey arm (report-only, never blocking). The machinery addition (one audit mode and its tests in an existing checker) is priced by the origin row's witnessed completed integrity failure (a bulk log edit removed a live dispatch entry; recoverable only from git history); the class-default alternatives are origin-adjudicated in the dispatch entry's rejected list (bulk side-effect pruning, fully manual pruning, and re-investigation recovery, each with its concrete reason). The duty-text changes are restrictions (scoping an existing duty), not additions, and remove nothing.

## Assumptions

- assume the entry's three-arm composed shape (landing-leg receipt duty, mechanical removal audit, standing-rule scoping) is the validated requirement set; basis: the harvest entry dispatched the origin row whose fix-shape analysis was complete at filing, with the rejected alternatives already adjudicated.
- assume the mechanical arm extends `scripts/check_prompt_log_origins.py` rather than `scripts/check_investigate_entries.py`; basis: the origins checker already owns prompt-log section parsing, origin resolution, archive-directory semantics, and the pins group, while the entries validator's documented scope is entry structure only and it carries no git-history machinery; the entry's "check_investigate_entries.py or the maintenance monitor's log duties" naming is an either/or surface list, and the plan records this selection here.
- assume removal detection is a git-history diff of the prompt log over an explicit base-to-HEAD range; basis: a removed entry is recoverable only from git history (the origin row's own recovery path used `git show 6cd1c966`).
- assume the witness match accepts the plans-root file or its `completed/` archive twin at the removal commit; basis: the prune rule keys the plans root, while an execution landing's tree carries the archived tree when the archive move and the entry deletion land as riders of the same landing.
- assume the landing-leg audit runs before the rider commit inside the closeout and its refusal takes the existing deferred-landing path; basis: the closeout riders' documented position in the landing closeout (agents/skills/plans/SKILL.md) and the execute-plan landing paragraph.
- assume the survey consult runs the audit consultatively over a bounded window and reports findings without blocking the turn; basis: the survey's consult family semantics (the machinery and reverse-squash consults are fail-open by design).
- assume authoring runs unattended under the standing authoring directive, so the Phase 1 confirmation is satisfied by the entry's validated record rather than a live interview; basis: the maintenance loop's authoring blueprint under the standing operator directive.
- assume removals in a commit that also adds a superseding entry are sanctioned editorial merges, classified `SUPERSEDED-IN-COMMIT` and reported without flagging; basis: the operator-directed merge commit `94e38903` (two removals, one grouped addition, no plan involved) is sanctioned history the audit must not false-flag, and it sits inside the default survey window.
- assume the audit classifies mechanically and the consultative survey leg adjudicates: ranges are expected to start after the pNNN-to-dispatch-log transition (the pre-plan-era wave landings `44eec2a7` and `61e86897` removed 20 pNNN entries sanctioned by the then-current task-log rule, outside any post-transition window), and the landing leg never spans those commits; basis: the removal shapes verified in git history and the survey consult's fail-open semantics.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: prompt-log pruning gains a per-entry receipt duty and a mechanical removal audit, so a landing can no longer delete a live dispatch entry as a bulk side effect; a code-quality fence against the witnessed over-prunes.

Before (today): a landing closeout evaluates the prune rule by hand and edits the log in the same commit as its other riders. The codex-nonzero-exit-evidence landing removed its own entry (correct, its plan file landed in that commit) and the authoring-round-liveness entry (not prune-eligible: no plan file existed anywhere) in one edit; the liveness origin row stayed open while its dispatch prompt vanished from the queue, and the loss surfaced only when a human compared git history.

After (this plan): the same closeout prunes only its own dispatch entry, prints `PLAN-PROMPTS-PRUNE: <slug> -> <witness path>` per removal, and runs `python3 scripts/check_prompt_log_origins.py --prune-audit --base <merge-base>` before the rider commit; a removal that lacks its witness refuses the landing and takes the deferred-landing path. At the survey, the monitor's log duties run the same audit over a bounded window and report any flagged removal consultatively. The checker's existing stale-entry mode is unchanged.

Edge cases pinned: a removal whose plan file lands in the same commit passes (the authoring-landing shape); a removal whose plan file is already at `completed/` at the removal commit passes (the execution-landing rider shape); a removal with no matching file at either path is flagged with the commit named; a removal in a commit that also adds a superseding entry is `SUPERSEDED-IN-COMMIT`, reported and never flagged (the sanctioned merge shape); an entry slug matching no segment of any same-tree basename is flagged even when a longer basename embeds the slug as a substring of one segment, and a slug longer than every basename's slug run never matches; the split-closeout shape (an entry removed in one commit, its plan landing in the next, the pre-rider `23349155`/`2c94d008` pair) is flagged by rule at the survey, and cannot occur on the landing leg because the rider model lands the plan file and the entry deletion in one squash commit; a range boundary can flag an already-healed removal (removed in one commit, restored later outside the range), which the consultative leg adjudicates and the landing leg never sees; the entry-template fence inside the log's standing rules never parses as an entry or a removal, and the diff-side fence tracker consumes context lines so fence state survives hunk boundaries; a log untouched in the range audits clean with zero removals.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the audit flags exactly the unwitnessed removal classes and passes exactly the witnessed clean shapes, with the sanctioned merge class reported as `SUPERSEDED-IN-COMMIT` without flagging; slug matching is segment-based, not substring-based, in both directions; the template fence is excluded; the stale mode's verdicts are byte-identical on the existing selftest fixture.
- fail-closed placement: the landing leg refuses (exit 1) and takes the deferred-landing path; the survey leg reports without blocking; the audit prints a final `OUTCOME:` line per the outcome contract and a run ending without one reads as a tool error at the call site.
- observability: every removal in the audited range produces exactly one classification line (`PRUNE-OK`, `SUPERSEDED-IN-COMMIT`, or `REMOVED-WITHOUT-WITNESS`) naming the commit; no silent path.
- maintainability: the audit lives in the existing checker as one new mode, stdlib only, run-from-anywhere against the script's own repo root; duty text changes are sentence-scoped edits, never a second copy of the rule.

**Done when:**
- all task boxes checked; the audit and regression suites pass under the venv pytest runner (`"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_check_prompt_log_origins.py scripts/test_check_investigate_entries.py -q` exits 0); the pins suite exits 0; `python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-plan-prompts-prune-eligibility-fence.md` exits 0 on the final bytes; the em-dash added-lines scan and the public hygiene scan exit 0.

**Ship when:**
- a real landing prunes its dispatch entry with the receipt printed and the audit passing, and a bulk removal of a live entry is refused at the landing closeout or named at the next survey.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_prompt_log_origins.py` (the `--prune-audit` mode)
- `docs/history/backlog/PLAN-PROMPTS.md` (the Prune rule bullet only)
- `agents/skills/plans/SKILL.md` (the landing closeout's prune-evaluation sentence only)
- `agents/skills/execute-plan/SKILL.md` (the landing paragraph's rider list parenthetical only)
- `agents/skills/maintenance/SKILL.md` (the log duties' prune clause only)
- `agents/skills/maintenance/prompt-templates.md` (the rider-tails preamble and the authoring blueprint's prune-evaluation sentence only)

**Tests:**
- `scripts/test_check_prompt_log_origins.py` (new audit-mode test classes)
- `scripts/check_maintenance_pins.sh` (new prune-audit pin group, same edit as any re-keyed span)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring implied by an explicit must-fix change, or contradicts a contract the plan changed.

**Out of scope; reject unless plan-related:**
- `scripts/check_investigate_entries.py`: the entries validator's structure checks stay untouched; the audit lives in the origins checker per the recorded assumption.
- The log's freeze rule and drift-check rule: their text and semantics are unchanged; this plan fences removals only.
- Prompt-log entry content and ordering: the queue's editorial surface is out of scope.

## Validation Commands

```bash
# Audit-mode suite and sibling validator regression (pytest tmp_path scratch repos;
# scratch-repo commits plumb git identity explicitly via -c user.name/-c user.email;
# the venv runner is the canonical invocation, bare python3 executes nothing here)
"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_check_prompt_log_origins.py scripts/test_check_investigate_entries.py -q
# Pins: the new prune-audit group lands in the same edit as any re-keyed span
bash scripts/check_maintenance_pins.sh
# Added-lines em-dash scan over the changed set (added-lines, never argless)
bash scripts/check-no-em-dash.sh added-lines --base main
# Public hygiene scan (fail-closed; outcome contract)
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
# Readiness (fail-closed; outcome contract)
python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-plan-prompts-prune-eligibility-fence.md
```

### Task 1: Prune-audit mode and its suite (TDD)

Files:
- `scripts/check_prompt_log_origins.py`
- `scripts/test_check_prompt_log_origins.py`

Evidence:
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_check_prompt_log_origins.py -q`; covers every criterion below at the task boundary (bare `python3` on this suite is a vacuous exit 0: the file has no runner)
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_check_investigate_entries.py -q`; covers the regression criterion that the sibling validator and the stale mode stay green (bare `python3` cannot import it: module-top pytest import)

- [x] `TestPromptLogPruneAudit#test_witnessed_bulk_removal_is_flagged` (re-derived 3032e750 shape); given a scratch repo whose log carries entries `self-own` and `live-entry`, a commit that removes both while adding a plans-root file matching only `self-own`, expects exit 1, a `REMOVED-WITHOUT-WITNESS: live-entry` line naming the commit, and a `PRUNE-OK: self-own` line naming the witness [class: REPOSITORY_TEST]
- [x] `TestPromptLogPruneAudit#test_clean_self_prune_passes` (re-derived e81381d6 shape); given a scratch repo whose removal commit both lands the plan file at the plans root and deletes the entry, expects exit 0 with the `PRUNE-OK` line naming the witness [class: REPOSITORY_TEST]
- [x] `TestPromptLogPruneAudit#test_archived_twin_witness_passes` (execution-rider shape); given a removal commit whose tree carries the plan at `docs/history/plans/completed/` and not at the plans root, expects exit 0 with the `PRUNE-OK` line naming the archive twin [class: REPOSITORY_TEST]
- [x] `TestPromptLogPruneAudit#test_superseding_merge_is_reported_not_flagged` (re-derived 94e38903 shape); given a removal commit that deletes two entries and adds one grouped entry in the same edit, expects exit 0, a `SUPERSEDED-IN-COMMIT` line per removed entry, and no `REMOVED-WITHOUT-WITNESS` line [class: REPOSITORY_TEST]
- [x] `TestPromptLogPruneAudit#test_segment_match_rejects_substring_slug`; given a removal whose only same-tree candidate basename embeds the slug inside a longer hyphen-bounded segment (slug appears only as a substring of one segment), expects the `REMOVED-WITHOUT-WITNESS` verdict, and given a true segment match it passes [class: REPOSITORY_TEST]
- [x] `TestPromptLogPruneAudit#test_slug_longer_than_basename_never_matches`; given a removal whose slug is longer than every same-tree basename's slug run (the origin-named-entry vs shorter-plan-file-name direction), expects the `REMOVED-WITHOUT-WITNESS` verdict, never a match [class: REPOSITORY_TEST]
- [x] `TestPromptLogPruneAudit#test_template_fence_never_parses_as_removal`; given a range commit that edits the log's standing-rules fence (the `## <short-slug>` placeholder lines inside the entry-template fence), expects zero parsed removals and exit 0 [class: REPOSITORY_TEST]
- [x] `TestPromptLogPruneAudit#test_untouched_log_audits_clean`; given a base-to-HEAD range where the log is untouched, expects exit 0 with a zero-removals summary line [class: REPOSITORY_TEST]
- [x] `TestPromptLogPruneAudit#test_outcome_line_present_on_both_verdicts`; given one flagged and one clean fixture, expects the final stdout line to be `OUTCOME: fail` and `OUTCOME: pass` respectively, and a missing final line to be absent in every green path [class: REPOSITORY_TEST]
- [x] `TestPromptLogPruneAudit#test_tool_error_paths`; given a missing log at the audit path, an unresolvable base ref, and a corrupted scratch repo, expects exit 3 with the final `OUTCOME: tool_error` line each time, never a silent pass [class: REPOSITORY_TEST]
- [x] `TestPromptLogPruneAudit#test_stale_mode_regression_fixture_unchanged`; given the existing selftest fixture, expects the stale mode's verdict lines byte-identical to the pre-plan behavior [class: REPOSITORY_TEST]
- [x] Run → RED confirmed under the venv runner (the audit flag does not exist; the new tests fail on a missing mode or miss every flagged shape) [class: REPOSITORY_TEST]
- [x] Implement `--prune-audit --base <ref>` in `scripts/check_prompt_log_origins.py` (one mode, stdlib only, resolved against the script's own repo root): resolve the log path from the script's own repo root as the existing mode does, but give the audit mode its own error paths per the outcome contract (a missing log at the audit path, an unresolvable base ref, or a git plumbing failure exits 3 with the final `OUTCOME: tool_error` line; the stale mode's `parser.error` behavior is untouched); enumerate the commits touching the log in `base..HEAD` oldest-first via git plumbing (`git rev-list`, `git diff-tree` over the log path), every subprocess call passing `cwd=REPO_ROOT` so the run-from-anywhere promise holds; parse removed entry headings from each diff (deleted lines whose content matches the existing `ENTRY_HEADING_RE`, fence state tracked through the added and removed sides consuming context lines so state survives hunk boundaries); for each removed slug classify at the removal commit's tree: a plans-root file whose basename minus `.md` carries the slug as a hyphen-bounded segment, or its `completed/` twin, is `PRUNE-OK`; a commit that also adds an entry heading superseding the removed one is `SUPERSEDED-IN-COMMIT` (report-only, never a flag); anything else is `REMOVED-WITHOUT-WITNESS`; print one classification line per removal (`PRUNE-OK: <slug> -> <witness>`, `SUPERSEDED-IN-COMMIT: <slug> (commit <short>)`, or `REMOVED-WITHOUT-WITNESS: <slug> (commit <short> <subject>)`); exit 1 when any removal lacks its witness, 0 otherwise; print the final `OUTCOME:` line per the outcome contract; the audit classifies mechanically and the consultative leg adjudicates: ranges are expected to start after the pNNN-to-dispatch-log transition, and the landing leg never spans the pre-plan-era wave commits [class: IMPLEMENTATION_REQUIRED]
- [x] Run → GREEN: full suite OK [class: REPOSITORY_TEST]
- [x] Run → GREEN (regression): the investigate-entries suite OK under the venv runner and the checker's `--selftest` OK [class: REPOSITORY_TEST]
- [x] Commit: `feat: prompt-log prune audit classifies removals against their plan-file witnesses` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Duty-text scoping, landing and survey wiring, receipt, pins

Files:
- `docs/history/backlog/PLAN-PROMPTS.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`
- `scripts/check_maintenance_pins.sh`

Evidence:
- `bash scripts/check_maintenance_pins.sh`; covers the companion-pin criterion
- `grep -c "PLAN-PROMPTS-PRUNE:" agents/skills/plans/SKILL.md` and `grep -c "PLAN-PROMPTS-PRUNE:" agents/skills/maintenance/prompt-templates.md`, run as two separate invocations so each file's receipt-duty presence gates on its own exit (a union grep passes when any single file matches); covers the receipt-duty presence (RED at authoring: zero hits in both)
- `grep -c "prune-audit" agents/skills/plans/SKILL.md`, `grep -c "prune-audit" agents/skills/maintenance/SKILL.md`, and `grep -c "prune-audit" docs/history/backlog/PLAN-PROMPTS.md`, run as three separate invocations for the same per-file gating; covers the wiring presence (RED at authoring: zero hits in all three)

- [x] Prune rule bullet scoped in `docs/history/backlog/PLAN-PROMPTS.md`: the standing rule gains the own-entry scope (a landing prunes only its own dispatch entry), the per-entry witness requirement (every removal carries its plan-file witness), and the monitor's-duties route for any other removal, keeping the drift-check and freeze bullets byte-untouched [class: IMPLEMENTATION_REQUIRED]
- [x] Landing closeout wired in `agents/skills/plans/SKILL.md`: the prune-evaluation sentence gains the own-entry scope, the `PLAN-PROMPTS-PRUNE:` receipt line per removal, the pre-rider prune-audit invocation (`python3 scripts/check_prompt_log_origins.py --prune-audit --base <merge-base>`, resolved repo-local then deployed home), and the refusal routing (exit 1 takes the deferred-landing path; exit 2, exit 3, and a run with no final `OUTCOME:` line stop the landing for re-derivation, never read as a pass), amending only that sentence's span [class: IMPLEMENTATION_REQUIRED]
- [x] Execution rider list qualified in `agents/skills/execute-plan/SKILL.md`: the `PLAN-PROMPTS entry deletion` rider names the receipt and the audit gate in one parenthetical, amending only that list item [class: IMPLEMENTATION_REQUIRED]
- [x] Monitor duty wired in `agents/skills/maintenance/SKILL.md`: the log duties' prune clause gains the own-entry scope for landing-leg prunes and the consultative audit arm (the survey runs the prune audit over a bounded window, the last 20 log-touching commits as the default window, and reports findings without blocking), amending only that clause [class: IMPLEMENTATION_REQUIRED]
- [x] Authoring blueprint sentence wired in `agents/skills/maintenance/prompt-templates.md`: the rider-tails preamble and the authoring blueprint's prune-evaluation sentence gain the receipt duty and the audit invocation, amending only those spans [class: IMPLEMENTATION_REQUIRED]
- [x] Companion pins group created (the `--prune-audit` invocation needle, the `PLAN-PROMPTS-PRUNE:` receipt needle in the plans skill and the blueprint, the scoped Prune-rule bullet needle in the log; no pre-existing span is re-keyed by this plan's edits, verified by the pins suite before and after) [class: IMPLEMENTATION_REQUIRED]
- [x] GREEN: full suite OK, pins suite exits 0, em-dash added-lines scan exits 0, hygiene scan exits 0 [class: REPOSITORY_TEST]
- [x] Commit: `feat: prompt-log pruning scoped to witnessed per-entry removals with landing and survey audit wiring` [class: IMPLEMENTATION_REQUIRED]
