# Plan: Outcome contract migration, batch 2: the review and maintenance advisory tier

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-03-outcome-contract-migration-validate-review-staging.md`
- `docs/history/backlog/2026-10-03-outcome-contract-migration-plan-readiness.md`
- `docs/history/backlog/2026-10-03-outcome-contract-migration-review-thread-gate.md`
- `docs/history/backlog/2026-10-03-outcome-contract-migration-revert-set-classifier.md`
- `docs/history/backlog/2026-10-03-outcome-contract-migration-check-maintenance-pins.md`
- `docs/history/backlog/2026-10-03-outcome-contract-migration-rearm-on-touch.md`
- `docs/history/backlog/2026-10-03-outcome-contract-migration-check-cleanup-scope-baseline.md`
- `docs/history/backlog/2026-10-03-outcome-contract-migration-scan-public-hygiene.md`

Driving force: automation + code-quality
Plan review record: the staging series docs/reviews/2026-10-03-plan-review-outcome-contract-migration-batch-2-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Family template: docs/history/plans/completed/2026-10-03-outcome-contract-migration-batch-1.md (the landing and closeout gates; this batch is the register's tracked successor pass that plan's assumptions name)

## Outcome

The eight remaining queued rows of scripts/OUTCOME_CONTRACT.md's migration register (the review and maintenance advisory tier) report the contract's four outcomes, completing the register: every decision script with a row answers in the pass/fail/indeterminate/tool-error vocabulary, ends non-metadata runs with a final `OUTCOME:` line, and leaves its agent-facing callers branching explicitly instead of guessing from legacy exit codes.

- scripts/validate_review_staging.py: `--hard` invalid stays fail (exit 1), soft-mode warnings stay inside a pass, and the failure classes that today borrow unrelated codes move to their contract homes: argparse usage violations (exit 2 today, verified at authoring) become tool error (exit 3, argparse overridden), and an unreadable input file becomes tool error instead of straggling at exit 1. The embedded `--selftest` gains the outcome arms; `--json` runs carry the outcome as a JSON field and are exempt from the stdout line (a declared placement deviation, the done-lock stderr precedent's shape). The done-sweep lib consumes this validator as a CLI subprocess child in its review-staging gate, and that child arm is rewired in Task 1 alongside the CLI migration; the library surfaces (the sweep lib's `is_staging_review_path` scope helper and scripts/summarize_review_stats.py's import) sit outside the CLI contract and are recorded, not rewired.
- scripts/plan_readiness.py: readiness verdicts keep 0 pass and 1 fail; the sibling-compatibility failure (a `return 1` today, misfiled as a readiness fail when it is evidence about the environment pairing, not the plan) becomes tool error; parse-time usage and mutual-exclusion violations (parser.error, exit 2 today) become tool error with the argparse override; the `--sweep` drift mode rides the same vocabulary. The done-sweep lib's readiness child arm (scripts/done_sweep_gates_lib.py `gate_plan_readiness`) branches on all four child outcomes instead of routing everything above 1 into an indeterminate bucket, applies the missing-OUTCOME-line rule with the no-line rule winning over the exit code, and the batch-1 register row's child-vocabulary assumption text ("answers in the 0/1 vocabulary") is rewritten to the migrated reality.
- scripts/review_thread_gate.py: closure keeps 0 pass and 1 fail; the missing-marker skip (exit 0, "nothing to check") is preserved as a modeled pass naming its reason; six arms that today exit 1 while reporting tool-shaped failures become tool error: an unresolvable marker PR target, a failed gh inventory fetch, an unreadable marker file, a marker that is not a JSON object, a marker without a thread list, and an unreadable `--inventory` file; a malformed inventory JSON becomes tool error (unsupported data, the done-lock precedent).
- scripts/revert_set_classifier.py: retires the guard-family vocabulary exactly as batch 1 retired it on the guard trio: clean and reversal keep 0 and 1, plumbing failures over resolved inputs become indeterminate (exit 2) under the answer-vocabulary criterion, unresolvable inputs (a bad `--repo` today exits 2 with the "revert-set-classifier tool failure:" prefix) and usage become tool error (exit 3), and the tool-failure stderr prefix retires.
- scripts/check_maintenance_pins.sh: all-pins-hold keeps exit 0 and a pin failure keeps exit 1, and every run ends with exactly one final `OUTCOME:` line: the suite fails at 38 separate mid-suite `[ "$fail" -eq 1 ] && exit 1` checkpoints (count on the authored bytes; re-derived at execution), so the emission funnels every exit site through one emit helper rather than decorating two ends; the not-inside-a-git-repo arm (exit 1 today, masquerading as a findings-class failure) becomes tool error (exit 3).
- scripts/rearm_on_touch.py: every classified verdict keeps exit 0 (bare invocation today is a classified `no-scheduler-state-file` skipped verdict at exit 0, not a usage error; the verdict JSON is the decision payload and the exit code never carried a domain fail class), the malformed-state arm (RearmError, exit 2 today) and the unexpected-exception arm (exit 2 today) become tool error, and argparse usage violations (an unknown flag, exit 2 today) become tool error.
- scripts/check_cleanup_scope_baseline.py: accounted and violation verdicts keep 0 and 1; the internal-error class splits per the answer-vocabulary criterion: an unresolvable base ref or a non-repo root (exit 2 today with "cleanup-scope: internal error") becomes tool error, a git plumbing failure over resolved inputs becomes indeterminate, usage becomes tool error; the eleven-fixture `--selftest` arms that assert the old exit-2 shapes are renewed.
- scripts/scan-public-hygiene.sh: clean stays 0 and findings stay 1; the script's own-error class (exit 2 today: an invalid regex line in the shared patterns file, unreadable scan inputs, the fail-closed guards) becomes tool error (exit 3), with the `--selftest` gaining the outcome arms; the runtime-home twin is a symlink into this repository's canonical copy (verified at authoring), so it inherits the migrated vocabulary at landing, and the task verifies the symlink parity rather than re-deploying; the done-sweep lib's skills-repo hygiene arm branches on the child's outcomes instead of collapsing any nonzero into a finding.
- The eight register rows record each script's declared operating-context assumptions and flip to migrated; the batch-1 sweep-pair row's child-vocabulary and inheritance sentences are rewritten to the migrated three-child-arm reality; the compatibility note gains the batch-2 entry; the primary caller recipes branch on every outcome plus the missing-OUTCOME-line rule.

Gate delta (machinery priced additions): +0 net-new counted classes (refusal classes, hard gates, fences, protocol layers, schema state fields), the batch-1 rationale carried over: the exit-vocabulary remaps, the per-script arms, and the three sweep-lib child-arm rewires replace legacy semantics under the landed contract document scripts/OUTCOME_CONTRACT.md, which is the doctrine receipt pricing this migration; the final `OUTCOME:` line is an output convention, not a counted class.

## Terms

- **outcome contract**, **answer-vocabulary criterion**, **migration register**, **caller obligation**: batch 1's definitions (docs/history/plans/completed/2026-10-03-outcome-contract-migration-batch-1.md, Terms), carried unchanged.
- **sweep child arm**: a done-sweep gate that invokes one of the migrated scripts as a CLI subprocess and must branch on the child's four outcomes; this batch rewires three (gate_review_staging in Task 1, gate_plan_readiness in Task 2, the skills-repo hygiene arm in Task 5) and the partial-scope freeze protects every other gate.
- **library surface**: a consumer that imports a validator as a module and calls its functions directly, outside the CLI contract: the sweep lib's `is_staging_review_path` scope helper and scripts/summarize_review_stats.py's import of validate_review_staging; exit-code remaps do not touch these, and the register row records them.
- **runtime-home twin**: the deployed copy of a script that the facts document's keys resolve to at runtime (public_hygiene_scan_script); the deployed scan twin is a symlink into this repository's canonical scripts directory, so it tracks the canonical bytes and carries a migration at landing, and the manifest-managed scripts (scripts/runtime-scripts.list) are the only copies scripts/sync_runtime_scripts.sh deploys.

## Assumptions

- assume batch 2 is all eight remaining queued register rows, completing the register; basis: batch 1's assumption 2 ("the remaining eight register rows stay queued with their backlog origins open, and the register table itself is the tracked successor path") and the contract's ranking note leaving no ninth row.
- assume this batch sequences after batch 1 (landed and executed 2026-10-03) and composes with the live sibling work on shared skill and script surfaces: the archive-ceremony execution is live on the execute-plan, plans, and maintenance landing text (worktree wt-acgu2), and the recurring-task-registry execution landed on main mid-authoring (cb10de83, re-keying check_maintenance_pins.sh's pin targets) after this plan's first review round witnessed it in flight: each caller-surface and script-byte step therefore re-reads its anchor immediately before editing and stops on drift, and no task assumes a sibling surface's bytes; basis: the landing-tail coordination rule and the witnessed parallel-execution fleet.
- assume validate_review_staging gains no indeterminate class: its inputs are staging markdown bytes that are readable or not, and a schema-violating record is the modeled violation the validator exists to report, never uncertainty; basis: the `--hard` contract (exit 1 invalid is the tool's purpose, witnessed across the staging rounds) and the absence of any partially-parsed arm in its selftest suite.
- assume the plan_readiness sibling-compatibility `return 1` is a remapped arm, not a preservation exception: compatibility evidence is about the environment pairing (the sibling module's shape), so the contract places it at tool error; the readiness verdicts themselves (digest, schema, sidecar, verdict, cap closure) are untouched; basis: the contract's tool-error definition and the docstring's own separation of the compat check from the readiness conditions.
- assume review_thread_gate's missing-marker exit 0 is a modeled skip preserved verbatim (the help text already declares "missing file exits 0": nothing to close is not a violation), and its read and fetch arms move from fail to tool error because a dead gh authentication, an unreadable file, or a shape-violating JSON is unsupported data or an unheld environment assumption, never a review finding; basis: the marker contract in the receiving-review skill and the contract's tool-error definition.
- assume rearm_on_touch keeps exit 0 for every classified verdict, including verdicts the calling session will act on (a dark-loop classification is a successful classification; bare invocation with no state file is the modeled `no-scheduler-state-file` skipped verdict at exit 0, verified at authoring): the exit channel reports whether classification ran, the verdict JSON carries the state; only the malformed-state and unexpected-exception arms (exit 2 today) move, to tool error (unsupported data and internal failure); basis: the script's boundary docstring ("classifies, books, and decides", never acts) and the done-lock unsupported-lock-data precedent.
- assume check_cleanup_scope_baseline's git-failure indeterminate arm is witnessed, not invented: its documented internal-error class lumps usage, unresolvable base ref, non-repo root, and git failures at exit 2 today; the answer-vocabulary criterion splits them (inputs that never resolved are tool error; plumbing failures over resolved inputs are indeterminate); basis: batch 1's identical split on the guard trio.
- assume check_maintenance_pins and scan-public-hygiene gain no indeterminate class: the pins suite's inputs are the repository's own tracked files (readable or the run is a tool error) and the scan's fail-closed guards already separate its own errors from findings; basis: the exit-2 fail-closed sites in scan-public-hygiene.sh and the pins script's two-arm shape.
- assume the scan-public-hygiene clean-tree contract is preserved: exit 0 on a clean tree, the standing pre-commit mandate, so the migration changes no pre-commit flow; the runtime-home twin is the verified symlink into the canonical scripts directory and needs a parity check at execution, not a re-deploy; basis: the repo guidelines' hygiene-scan mandate, the readlink verification at authoring, and the manifest gap (scan-public-hygiene.sh is absent from scripts/runtime-scripts.list, so the sync script is a no-op for this twin).
- assume none of the eight has eval-consumed stdout (no caller evals their output as exports, unlike done-lock's acquire subcommands), so every `OUTCOME:` line emits on stdout, with the single declared deviation that validate_review_staging's `--json` runs carry the outcome as a JSON field and emit no stdout line; basis: the caller census below shows recipe-style invocation with exit-code and line greps only, and the batch-1 declared-deviation precedent for output-shaped conflicts.
- assume `--selftest` runs of the three embedded harnesses are metadata-mode diagnostics outside the contract (no `OUTCOME:` line), like `--help`; the harnesses' pass and fail verdicts ride their own assertions and exit codes; basis: the contract's exemption naming only help and version metadata, closed here as a declared reading, with batch 1's done-lock selftest mapping noted as the alternative shape this batch does not need (its harnesses are fixture runners, not gated flows).
- assume the caller census known at authoring is: exit-sensitive surfaces are the review-staging skill's staging-validation recipes (validate_review_staging), the done skill's review-thread closure recipe (review_thread_gate, the actual runner; receiving-review writes the marker and holds one prose mention) and its revert-adjudication recipes (revert_set_classifier), the maintenance skill's revert-set step (revert_set_classifier), its Step 0 rearm bullet (rearm_on_touch) and its deferred-corpus census probe consuming `plan_readiness --sweep`, the done skill's Step 0 rearm recipe (its "rc 2 malformed-or-failed" sentence, invalidated by the rearm remap), the receiving-review skill's capture-hygiene recipe (scan-public-hygiene, whose nonzero-stops-capture wording misroutes a tool error into draft-fixing after the remap), the plans skill's readiness gate and cleanup-scope step (plan_readiness, check_cleanup_scope_baseline), the execute-plan skill's Step 0.5 readiness gate (plan_readiness), the maintenance prompt-templates' readiness and landing recipes (plan_readiness), the three done-sweep child arms (validate_review_staging, plan_readiness, scan-public-hygiene), and scripts/release-rewrite.sh (its `invoke_scanner` branches on the scanner's exit 2 today, a live branch the hygiene remap re-keys); each migration task's probe re-derives the enumeration live and records the receipt rather than trusting this list; basis: the authoring census (grep per script across agents/ and scripts/, 2026-10-03, re-verified against main cb10de83) and batch 1's identical probe discipline.
- assume the exit-agnostic callers stay untouched unless a probe witnesses exit-code branching: docs-branch, lessons-migrate, release, cursor-agent-diagnose (skill and run.sh), rfc-design, review-confluence-doc, review-plan, review-loop, doing-code-review, the plan-readiness hook README, scripts/review_record_selection.py, scripts/execute_plan_runtime.py, scripts/docs_branch_plan_guard.py, scripts/summarize_review_stats.py (a library surface), the pins script's prose references (agents/skills/execute-plan/SKILL.md's telemetry note, agents/skills/maintenance/SKILL.md's change-log mentions, agents/skills/maintenance/zcode.md's title-pin note; no agent-facing recipe invokes the pins suite, so it has no caller-text update in this batch), and execute-plan's readiness-gate deployment note naming validate_review_staging as a copy-sibling; basis: their references are presence checks, prose citations, library imports, or exit-agnostic dies, the batch-1 out-of-scope shape, each re-verified live by the owning task's probe.
- assume check_maintenance_pins gains no new suite-wide harness in this batch: the suite has no `--selftest` CLI mode, but it is not fixtureless, and the plan's first review round wrongly called it zero-fixture: the live-vs-archive section has carried a per-section fixture seam since 2026-09-25 (a callable check function taking the root as its argument, the PINS_DUPLICATE_ROOT override, and a built-in synthetic-fixture selftest asserting the refusal names the fixture pair); its outcome coverage is pinned by that seam's extended refusal arm plus direct validation commands (in-repo run, run from a non-repo directory, and the OUTCOME-line census); a suite-wide fixture harness is new machinery outside a vocabulary remap's price class; basis: the machinery delta doctrine, the 38 exit checkpoints, and the live-vs-archive section's existing seam (check_maintenance_pins.sh's fixture comments and built-in selftest, present in cb10de83^ and verified in this plan's second review round).
- assume the register's `| migrated` count moves from 6 (the dirt-gate precedent row plus batch 1's five) to 14, with the register then holding fifteen rows total (the fourteenth migrated row plus base_reflog_audit's conformant-at-birth row); basis: the authoring-time grep, verified 2026-10-03 on main cb10de83 bytes.
Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: completes the script outcome contract migration by moving the eight remaining register rows (the review and maintenance advisory tier) to the four-outcome vocabulary with declared assumptions, caller branching, and three done-sweep child-arm rewires, so an agent gating on any decision script in this repository can finally branch on what actually happened instead of guessing from three different legacy exit dialects.

Today `python3 scripts/plan_readiness.py` exits 2 for a usage mistake and so does a sibling-compatibility mismatch, which a landing recipe cannot tell from the guard family's old exit-2 tool failure; `review_thread_gate.py` reports a dead gh authentication as exit 1, the same code as an unclosed review thread; the pins suite reports "not inside a git repository" as exit 1, the same code as a failing pin, and fails mid-suite at 38 checkpoints so a tail-only line would never fire; and none of the eight prints a final machine-readable outcome. After this batch every run of every registered decision script ends with exactly one `OUTCOME:` line, uncertainty is exit 2 and never masquerades as a verdict, broken invocations are exit 3 and never masquerade as findings, and the sweep pair's three child arms stop collapsing the distinction.

## Evaluation Criteria

**Quality dimensions:**
- contract conformance: every migrated script emits exactly one final `OUTCOME:` line per non-metadata run on stdout, with exit codes matching the contract including the argparse override; `--help`, the successful `--selftest` diagnostics, and validate_review_staging's `--json` runs (the declared JSON-field deviation) sit outside the stdout-line rule per the exemptions and declared readings above.
- behavior preservation for modeled cases: every pre-migration pass and fail case keeps its verdict and exit; the declared remapped arms are exactly the error-class arms named in the Outcome section (usage violations, unresolvable and unreadable inputs, shape-violating JSON, environment and internal failures, the sibling-compatibility mismatch, the not-in-repo pins arm, the review-thread gate's six read and fetch arms, the rearm malformed-state arm, the hygiene own-error class), each individually named in the tasks; no modeled refusal or findings class changes its code.
- caller explicitness: each exit-sensitive caller recipe branches on all four outcomes and on the missing-OUTCOME-line rule (treat as tool error, stop, re-derive from disk) for the scripts it invokes, and no caller collapses indeterminate or tool error into a fail or a findings row; the three sweep child arms branch instead of collapsing, and the no-line rule wins over the child's exit code when both could classify.
- regression net: the four migrated scripts' existing test files, the three embedded selftest harnesses, the two done-sweep suites, the rejected-archive lifecycle suite, and the runtime-twin sync suite stay green after each task, with legacy exit-shape arms renewed per the checklist items.

**Done when:**
- The eight scripts' outcome fixtures pass under the test venv or their selftest harnesses (pass, fail where the script has a fail class, tool error, plus the witnessed indeterminate cases for the classifier pair), with the renewed legacy arms.
- scripts/OUTCOME_CONTRACT.md shows all fifteen rows accounted for: fourteen migrated (the six pre-existing plus batch 2's eight) and one conformant-at-birth (base_reflog_audit.py), with batch 2's declared assumptions filled and the compatibility note extended.
- The exit-sensitive caller surfaces (agents/skills/review-staging/SKILL.md, agents/skills/plans/SKILL.md, agents/skills/execute-plan/SKILL.md, agents/skills/maintenance/SKILL.md, agents/skills/maintenance/prompt-templates.md, agents/skills/receiving-review/SKILL.md, agents/skills/done/SKILL.md) branch on every outcome where they gate on these scripts, and the probe receipts for the exit-agnostic callers are recorded in the session record.

**Ship when:**
- Nothing; the work is repository-internal.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/validate_review_staging.py`
- `scripts/plan_readiness.py`
- `scripts/review_thread_gate.py`
- `scripts/revert_set_classifier.py`
- `scripts/check_maintenance_pins.sh`
- `scripts/rearm_on_touch.py`
- `scripts/check_cleanup_scope_baseline.py`
- `scripts/scan-public-hygiene.sh`
- `scripts/done_sweep_gates_lib.py` (the review-staging, plan-readiness, and skills-repo hygiene child arms only)
- `scripts/release-rewrite.sh` (the `invoke_scanner` exit-code branch only)
- `scripts/OUTCOME_CONTRACT.md`

**Tests:**
- `scripts/test_plan_readiness.py`
- `scripts/test_rearm_on_touch.py`
- `scripts/test_revert_set_classifier.py`
- `scripts/test_review_thread_gate.py`
- `scripts/test_done_sweep_gates_lib.py` (the three child-arm fixtures)
- `scripts/test_done_sweep_gates_wrapper.py` (the child-stub fixtures)
- `scripts/test_rejected_archive_lifecycle.py` (the readiness-stub fixture)
- the three embedded selftest harnesses (`validate_review_staging.py --selftest`, `check_cleanup_scope_baseline.py --selftest`, `scan-public-hygiene.sh --selftest`)

**Skills and recipes:**
- `agents/skills/review-staging/SKILL.md` (the staging-validation recipes)
- `agents/skills/plans/SKILL.md` (the readiness and cleanup-scope steps)
- `agents/skills/execute-plan/SKILL.md` (the Step 0.5 readiness gate)
- `agents/skills/maintenance/SKILL.md` (the certification bullet, the rearm bullet, the revert-set step, the census probe)
- `agents/skills/maintenance/prompt-templates.md` (the readiness and landing recipes)
- `agents/skills/receiving-review/SKILL.md` (the capture-hygiene scan steps)
- `agents/skills/done/SKILL.md` (the review-thread closure recipe, the revert-adjudication recipes, the Step 0 rearm recipe, the cleanup-scope steps, and the hygiene-scan steps: the doc-registry bullet's prose-scan duty and the sensitive-data-scan fix guidance)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Partially-in-scope files:** in the eight scripts, only the exit-code vocabulary, the result-emission paths, the new tool-error and indeterminate arms, their docstrings, and their usage texts are in scope; each script's classification logic for existing pass, fail, and findings cases is frozen (findings there are pre-existing defects, filed separately, not fixed here), with the three named exceptions the sweep-lib tasks rewire. In done_sweep_gates_lib.py, only the review-staging, plan-readiness, and skills-repo-hygiene child arms' outcome branching is in scope; every other gate is frozen. In scripts/release-rewrite.sh, only the `invoke_scanner` exit-code branch and its comment are in scope. In scripts/OUTCOME_CONTRACT.md, only the eight batch rows, the batch-1 sweep-pair row's child-vocabulary and inheritance sentences, and the compatibility note are in scope. In the seven skill files, only the recipe steps that invoke the eight scripts and their outcome-handling text are in scope; everything else is frozen.

**Out of scope; reject unless plan-related:**
- `scripts/reverse_squash_guard.py`: no register row exists for it today (the archive-ceremony plan's "pending the family's queued outcome-contract migration row" sentence points at a row that is not in the table); filing that row is a separate backlog act, and this migration completes the existing register, it does not grow it.
- `scripts/base_reflog_audit.py` (conformant at birth), `scripts/read_freshness_probe.py`, and `scripts/base_branch_amend_guard.py` (absent from the register; the evidence-integrity plan's helpers): their rows, if ever filed, are their own migration acts.
- The exit-agnostic caller set named in the assumptions, unless a probe witnesses exit-code branching live.
- The runtime-home copies themselves (outside the repository): the scan twin is a verified symlink tracking the canonical bytes; the manifest-managed copies deploy through scripts/sync_runtime_scripts.sh, which this plan never edits.
- The queued-row backlog origin files beyond the `--mark-covered` flip at landing: their fold-and-delete belongs to this plan's own completion pass, not to a task.

## Validation Commands

```bash
PY=$HOME/.agents/venvs/ai-playbook-test/bin/python3
$PY scripts/test_plan_readiness.py
$PY scripts/test_rearm_on_touch.py
$PY scripts/test_revert_set_classifier.py
$PY scripts/test_review_thread_gate.py
$PY scripts/test_done_sweep_gates_lib.py
$PY scripts/test_done_sweep_gates_wrapper.py
$PY scripts/test_rejected_archive_lifecycle.py
$PY scripts/validate_review_staging.py --selftest
$PY scripts/check_cleanup_scope_baseline.py --selftest
bash scripts/scan-public-hygiene.sh --selftest
$PY scripts/test_sync_runtime_scripts.py
for s in scripts/plan_readiness.py scripts/validate_review_staging.py scripts/review_thread_gate.py scripts/revert_set_classifier.py scripts/check_cleanup_scope_baseline.py; do python3 "$s" >/dev/null 2>&1; test "$?" -eq 3 || { echo "usage error is not exit 3 for $s"; exit 1; }; done
python3 scripts/rearm_on_touch.py --no-such-flag >/dev/null 2>&1; test "$?" -eq 3 || { echo "rearm usage error is not exit 3"; exit 1; }
DIR="$(pwd)"; (cd /tmp && bash "$DIR/scripts/check_maintenance_pins.sh" >/dev/null 2>&1); test "$?" -eq 3 || { echo "pins not-in-repo is not exit 3"; exit 1; }
for s in scripts/plan_readiness.py scripts/validate_review_staging.py scripts/review_thread_gate.py scripts/revert_set_classifier.py scripts/check_cleanup_scope_baseline.py scripts/rearm_on_touch.py scripts/check_maintenance_pins.sh scripts/scan-public-hygiene.sh; do grep -q 'OUTCOME:' "$s" || { echo "no OUTCOME emission in $s"; exit 1; }; done
bash scripts/scan-public-hygiene.sh >/dev/null 2>&1; test "$?" -eq 0 || { echo "clean-tree hygiene scan no longer exits 0"; exit 1; }
test "$(readlink -f "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh")" = "$(git rev-parse --path-format=absolute --git-common-dir | sed -e 's,/.git$,,')/scripts/scan-public-hygiene.sh" || { echo "hygiene runtime twin is not a symlink into the canonical checkout"; exit 1; }
test "$(grep -c '| migrated' scripts/OUTCOME_CONTRACT.md)" -eq 14 || { echo "register rows not all flipped (want 14)"; exit 1; }
```

Authoring-time gate evidence, all verified 2026-10-03 in the authoring worktree, re-verified against main cb10de83 after the recurring-task-registry landing: the eleven suite commands are GREEN today (the four migrated scripts' test files, the three done-sweep and lifecycle suites, the three selftests, the sync suite) and must stay green through every task boundary; the usage probes are RED today (the five python CLIs with required operands exit 2 on no arguments, argparse's default) and flip GREEN at exit 3; rearm_on_touch exits 0 on bare invocation (the classified `no-scheduler-state-file` skipped verdict, its modeled state) and 2 on an unknown flag, so its probe is the unknown-flag shape; the pins probe is RED today (running the suite from a non-repo directory exits 1) and flips GREEN at 3; the OUTCOME-line census is RED today (zero matches in all eight scripts) and flips GREEN per task; the clean-tree hygiene scan exits 0 today and must never leave 0; the runtime-twin parity probe is GREEN today (the facts-key copy is the verified symlink into the canonical checkout) and must stay GREEN, and it is checkout-independent, resolving the canonical checkout through the git common dir so it reads identically from any linked worktree; the register count is 6 today and flips GREEN at 14; the origins-closed gate on this plan's own bytes is RED today by design (the eight origins sit open at the backlog top level while the plan is open) and flips GREEN only at the landing pass after Task 6, so it gates the completion pass, not a task.

### Task 1: Migrate validate-review-staging and branch its sweep child arm

Files:
- `scripts/validate_review_staging.py`
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`
- `agents/skills/review-staging/SKILL.md`

Evidence:
- `$PY scripts/validate_review_staging.py --selftest`; covers the outcome arms, the renewed legacy arms, and every pre-existing fixture group
- `$PY scripts/test_done_sweep_gates_lib.py`; covers the rewired review-staging child arm and every pre-existing arm

- [x] RED: add outcome arms to the embedded selftest harness: a `--hard` invalid record emits exit 1 with a final `OUTCOME: fail` line after the human-readable finding lines; a valid record emits exit 0 with `OUTCOME: pass` (a soft-mode warning run still exits 0, the warning line inside the evidence, and the OUTCOME line still last); a usage violation (a missing positional operand, a flag-combination violation) exits 3 with `OUTCOME: tool_error` (the argparse override), while `--help` stays metadata-exempt with no OUTCOME line; an unreadable input file (a path that cannot be opened) exits 3 with `OUTCOME: tool_error` naming the path; a `--json` run emits no stdout OUTCOME line and carries the outcome as a JSON field; run the selftest → expect RED: today invalid is exit 1 with no OUTCOME line, usage is argparse's exit 2, and an unreadable input straggles at exit 1 [class: REPOSITORY_TEST]
- [x] Remap the CLI vocabulary site by site: argparse errors override to exit 3 with the OUTCOME line on stderr before exit; the unreadable-input arm becomes exit 3; `--hard` invalid stays exit 1; valid stays exit 0; every non-metadata run ends with exactly one final `OUTCOME:` line on stdout after the human-readable evidence, `--json` runs excepted per the declared deviation (the outcome rides the JSON field, no stdout line); the module's importable functions are untouched [class: IMPLEMENTATION_REQUIRED]
- [x] Update the module docstring's exit-code line to the four-outcome vocabulary (the metadata exemption, the `--json` deviation, and the library surfaces named), and draft the register row's operating-context assumptions: readable input paths (an unreadable path is tool error); invocation with at most one staging record per run; the library surfaces recorded (the sweep lib's `is_staging_review_path` scope helper and scripts/summarize_review_stats.py's import sit outside the CLI contract) [class: IMPLEMENTATION_REQUIRED]
- [x] Re-wire the sweep lib's review-staging child arm (`gate_review_staging`, which today collapses every nonzero `--hard` child exit into a failed bucket): a child exit 0 passes, exit 1 lands in the failed bucket with the validator's finding tail, exit 2 lands in an indeterminate bucket naming the target, exit 3 lands in a tool-error bucket naming the target, and a child run with no final OUTCOME line classifies tool error per the contract's no-line rule winning over the exit code; renew the lib suite's review-staging child fixtures to cover all four outcomes and the no-line shape [class: IMPLEMENTATION_REQUIRED]
- [x] Probe the CLI callers for exit-code branching, verifying the enumerated assumption live and recording the receipt (known exit-sensitive members: the review-staging skill's validation recipes and the sweep lib's review-staging child arm; probe receiving-review, review-plan, review-loop, doing-code-review, done, review-confluence-doc, rfc-design, and execute-plan's deployment note for the exit-agnostic claim, plus the library surfaces summarize_review_stats.py and the sweep lib's scope helper); update the review-staging skill's recipe steps that run this script so they branch on the four outcomes and the missing-OUTCOME-line rule, and re-verify the exit-agnostic claim for scripts/review_record_selection.py and scripts/execute_plan_runtime.py [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the selftest under `$PY` and the lib suite [class: REPOSITORY_TEST]
- [x] Commit: `feat: migrate validate-review-staging and branch its sweep child arm` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Migrate plan-readiness and re-wire the readiness sweep child arm

Files:
- `scripts/plan_readiness.py`
- `scripts/test_plan_readiness.py`
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_wrapper.py`
- `scripts/test_rejected_archive_lifecycle.py`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`

Evidence:
- `$PY scripts/test_plan_readiness.py`; covers the outcome fixtures, the renewed legacy arms, and every pre-existing arm
- `$PY scripts/test_done_sweep_gates_lib.py` and `$PY scripts/test_done_sweep_gates_wrapper.py`; cover the rewired readiness child arm and the renewed child stubs
- `$PY scripts/test_rejected_archive_lifecycle.py`; covers the renewed readiness stub

- [x] RED: add outcome fixtures to the test file: a ready plan emits exit 0 with a final `OUTCOME: pass`; a failed condition emits exit 1 with `OUTCOME: fail` and the named first-failed condition; a parse-time usage violation (no operands, or a forbidden mode combination such as `--pre-round` with `--selftest`) exits 3 with `OUTCOME: tool_error` (the argparse override; today parser.error exits 2), while `--help` stays metadata-exempt; a sibling-compatibility failure exits 3 with `OUTCOME: tool_error` (today a `return 1`, misfiled as a readiness fail); build the compat seam by monkeypatching the sibling compatibility constant the way plan_readiness.py's own selftest fixtures do (no compat seam exists in the test file today); run → expect RED [class: REPOSITORY_TEST]
- [x] Remap the exit vocabulary site by site: readiness verdicts keep 0 and 1; the sibling-compat arm moves from `return 1` to exit 3; parse-time usage and mutual-exclusion violations override argparse to exit 3; the `--sweep` drift mode keeps its modeled verdicts and gains the same final-line and usage rules; every non-metadata run ends with exactly one final `OUTCOME:` line on stdout; update the docstring exit-code line and draft the register assumptions (a readable repository with resolvable facts keys for plans_dir and reviews_dir, a readable plan operand, the sibling modules importable and shape-compatible; a compat mismatch is tool error, never a readiness fail) [class: IMPLEMENTATION_REQUIRED]
- [x] Re-wire the sweep child arm in scripts/done_sweep_gates_lib.py `gate_plan_readiness`: a child exit 0 passes, exit 1 lands in the failed bucket with the first-failure line, exit 2 (which the migrated child never models; a crash or legacy shape) keeps an indeterminate bucket naming the child, exit 3 lands in a tool-error bucket reported as the gate's tool-error evidence (a child that could not run reliably is never a readiness fail), and a child run with no final OUTCOME line classifies tool error per the contract's no-line rule winning over the exit code; renew the lib suite's readiness child fixtures for all four outcomes and the no-line shape; renew the wrapper suite's validator stubs (today a stub exits 1 with no OUTCOME line and asserts a failed-bucket aggregation: after the rewire that stub must emit `OUTCOME: fail` to stay a fail, or the assertions move to the tool-error expectation) and the rejected-archive lifecycle suite's readiness stub (same renewal) [class: IMPLEMENTATION_REQUIRED]
- [x] Rewrite the batch-1 register row's child-vocabulary assumption (the "plan-readiness child validator answers in the 0/1 vocabulary" sentence and its "exit outside it classifies indeterminate" clause) to the migrated four-outcome reality, and extend the sweep-pair row's inheritance note to name the review-staging child as a CLI-contract caller rewired in Task 1 (the full row text edit lands in Task 6; this task records the drafted wording in the session record) [class: IMPLEMENTATION_REQUIRED]
- [x] Probe the callers for exit-code branching, verifying the enumerated assumption live and recording the receipt (known exit-sensitive members: the plans skill's readiness gate and certification flow, the execute-plan skill's Step 0.5 readiness gate, the maintenance skill's certification bullet and its deferred-corpus census probe consuming `--sweep`, the prompt-templates readiness and landing recipes, the done-sweep readiness gate); update those recipe texts to branch on the four outcomes and the missing-OUTCOME-line rule, re-reading each anchor immediately before editing and stopping on drift (the sibling-execution coordination rule); re-verify the exit-agnostic claim for agents/hooks/plan-readiness/README.md, agents/skills/review-plan/SKILL.md, agents/skills/review-loop/SKILL.md, and scripts/docs_branch_plan_guard.py [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the three test files and both sweep suites under `$PY` [class: REPOSITORY_TEST]
- [x] Commit: `feat: migrate plan-readiness and branch the readiness sweep child arm` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Migrate the review-lane pair (review-thread-gate, revert-set-classifier)

Files:
- `scripts/review_thread_gate.py`
- `scripts/revert_set_classifier.py`
- `scripts/test_review_thread_gate.py`
- `scripts/test_revert_set_classifier.py`
- `agents/skills/done/SKILL.md`
- `agents/skills/maintenance/SKILL.md`

Evidence:
- `$PY scripts/test_review_thread_gate.py`; covers the outcome fixtures and every pre-existing arm
- `$PY scripts/test_revert_set_classifier.py`; covers the outcome fixtures, the renewed legacy arms, and every pre-existing arm

- [x] RED: add outcome fixtures to both test files. review_thread_gate: closure emits exit 0 with `OUTCOME: pass`; unclosed threads emit exit 1 with `OUTCOME: fail` listing them; a missing marker file emits exit 0 with `OUTCOME: pass` and the nothing-to-check reason line (the preserved modeled skip); the six tool-shaped arms (an unresolvable marker PR target, a failed gh inventory fetch, an unreadable marker file, a marker that is not a JSON object, a marker without a thread list, an unreadable `--inventory` file) exit 3 with `OUTCOME: tool_error` (all exit 1 today); a malformed inventory JSON exits 3 with `OUTCOME: tool_error`; a usage violation exits 3 (today argparse exit 2). revert_set_classifier: a clean tree emits exit 0 with `OUTCOME: pass`; a reversal emits exit 1 with `OUTCOME: fail` and the pure-or-partial summary; a bad `--repo` (an unresolvable input) exits 3 with `OUTCOME: tool_error` (today exit 2 with the tool-failure prefix); a usage violation exits 3; run → expect RED on every new arm [class: REPOSITORY_TEST]
- [x] Remap review_thread_gate's vocabulary site by site: the six read and fetch arms and the malformed-inventory arm move from exit 1 to exit 3; the closure and unclosed verdicts keep 0 and 1; the missing-marker skip keeps 0 and gains the OUTCOME line; usage overrides argparse to exit 3; every non-metadata run ends with exactly one final `OUTCOME:` line on stdout; update the docstring exit-code line [class: IMPLEMENTATION_REQUIRED]
- [x] Remap revert_set_classifier's vocabulary under the answer-vocabulary criterion, the batch-1 guard-trio shape: plumbing failures over resolved inputs become indeterminate (exit 2, the answer-vocabulary reading of a git call that answered outside 0/1); unresolvable inputs (repo, ref) and usage become tool error (exit 3); the "revert-set-classifier tool failure:" stderr prefix retires; clean and reversal keep 0 and 1; every non-metadata run ends with exactly one final `OUTCOME:` line on stdout; update the docstring exit-code line [class: IMPLEMENTATION_REQUIRED]
- [x] Draft both register rows' operating-context assumptions: review_thread_gate (a readable, shape-conforming marker when present; a gh installation authenticated for `--live`; an unreadable or shape-violating marker or inventory is tool error); revert_set_classifier (invocation inside a git repository with a resolvable `--repo` and resolvable revs; git answering outside its 0/1 vocabulary is indeterminate) [class: IMPLEMENTATION_REQUIRED]
- [x] Probe the callers for exit-code branching, verifying the enumerated assumption live and recording the receipt (known exit-sensitive members: the done skill's review-thread closure recipe, the done skill's revert-adjudication recipes, the maintenance skill's revert-set step); update those recipe texts to branch on the four outcomes and the missing-OUTCOME-line rule (the closure recipe keeps the missing-marker skip reading as a pass), re-reading each anchor before editing and stopping on drift; re-verify the exit-agnostic claim for receiving-review's prose mention of the marker duty and for scripts/check_maintenance_pins.sh's textual references [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the two test files under `$PY` [class: REPOSITORY_TEST]
- [x] Commit: `feat: migrate the review-lane pair to the outcome contract` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Migrate the maintenance-loop pair (check-maintenance-pins, rearm-on-touch)

Files:
- `scripts/check_maintenance_pins.sh`
- `scripts/rearm_on_touch.py`
- `scripts/test_rearm_on_touch.py`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/done/SKILL.md`

Evidence:
- `$PY scripts/test_rearm_on_touch.py`; covers the outcome fixtures and every pre-existing arm
- `bash scripts/check_maintenance_pins.sh`; the in-repo run is the pass arm (exit 0, final `OUTCOME: pass`), the live-vs-archive section's built-in synthetic-fixture selftest is the witnessed fail arm (extended per the RED item), and the Validation Commands' non-repo probe is the tool-error arm; the suite's fixture seam is per-section, not suite-wide (the declared scoping in Assumptions)

- [x] Re-derive the pins script's bytes against the current tree before editing and stop on drift: the recurring-task-registry landing (cb10de83) re-keyed this script's pin targets mid-authoring, so the checkpoint count and the pass-arm evidence are re-derived from the checked-out bytes, never quoted from this plan (witnessed-drift duty) [class: IMPLEMENTATION_REQUIRED]
- [x] RED: add outcome arms to the rearm test file: a classified verdict (any class, including a skip) emits exit 0 with the verdict JSON and a final `OUTCOME: pass` line (today exit 0 with no OUTCOME line); a malformed state file emits exit 3 with `OUTCOME: tool_error` (today exit 2 via RearmError); an unexpected-exception arm emits exit 3 with `OUTCOME: tool_error`; an unknown-flag usage violation exits 3 (today argparse exit 2; bare invocation is the modeled skipped verdict at exit 0 and is not a usage shape); run → expect RED on the new arms [class: REPOSITORY_TEST]
- [x] Remap rearm_on_touch's vocabulary: the RearmError arm and the unexpected-exception arm move from exit 2 to exit 3 with the OUTCOME line on stdout after the verdict JSON (the verdict JSON stays the machine-readable payload and stays parseable; the OUTCOME line follows it); every classified-verdict run keeps exit 0; usage overrides argparse to exit 3; update the docstring [class: IMPLEMENTATION_REQUIRED]
- [x] Migrate check_maintenance_pins.sh: RED first, extend the live-vs-archive section's built-in synthetic-fixture selftest to assert the refusal run ends with the final `OUTCOME: fail` line and run it → expect RED (the refusal emits no line today); then funnel every exit site through one emit helper so each run ends with exactly one final `OUTCOME:` line on stdout: the all-pins-hold exit 0 (`OUTCOME: pass`), every mid-suite `[ "$fail" -eq 1 ]` checkpoint exit 1 (`OUTCOME: fail` after the failing pin lines; 38 checkpoints on the authored bytes, re-derived per the drift duty), and the not-inside-a-git-repo arm moved from exit 1 to exit 3 (`OUTCOME: tool_error`); record the per-section-seam evidence shape in the script's header comment (no suite-wide harness; the declared scoping in Assumptions); the suite's per-pin output format is frozen [class: IMPLEMENTATION_REQUIRED]
- [x] Draft both register rows' operating-context assumptions: check_maintenance_pins (invocation inside the target git repository; the suite reads the repository's own tracked files; a non-repo invocation is tool error); rearm_on_touch (a readable scheduler state file at the resolved path; an unparseable state file is tool error; the verdict JSON is the decision payload and every classified verdict passes on the exit channel) [class: IMPLEMENTATION_REQUIRED]
- [x] Probe the callers for exit-code branching, verifying the enumerated assumption live and recording the receipt (known exit-sensitive members: the maintenance skill's Step 0 rearm bullet and the done skill's Step 0 rearm recipe, whose "rc 2 malformed-or-failed" sentence the remap invalidates; the pins suite has no agent-facing invocation, only prose references in execute-plan, the maintenance skill, and zcode.md, re-verified exit-agnostic); update the two rearm recipe texts to branch on the four outcomes and the missing-OUTCOME-line rule, re-reading each anchor immediately before editing and stopping on drift; the pins suite must stay green after every edit in this task [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the rearm test file under `$PY`, and the pins suite in-repo (exit 0 with the final `OUTCOME: pass` line) [class: REPOSITORY_TEST]
- [x] Commit: `feat: migrate the maintenance-loop pair to the outcome contract` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Migrate the cleanup and hygiene pair, branch the hygiene sweep arm, and re-key the release caller

Files:
- `scripts/check_cleanup_scope_baseline.py`
- `scripts/scan-public-hygiene.sh`
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`
- `scripts/release-rewrite.sh`
- `agents/skills/plans/SKILL.md`
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/done/SKILL.md`

Evidence:
- `$PY scripts/check_cleanup_scope_baseline.py --selftest`; covers the renewed arms, the new indeterminate arm, and every pre-existing fixture repo
- `bash scripts/scan-public-hygiene.sh --selftest`; covers the outcome arms and every pre-existing hermetic fixture
- `$PY scripts/test_done_sweep_gates_lib.py`; covers the rewired hygiene child arm

- [x] RED: renew the cleanup-scope selftest's internal-error arms and add outcome arms: the nonexistent-base-ref arm, the missing-`--base` arm, and the non-repo-root arm now want exit 3 with `OUTCOME: tool_error` (they want exit 2 today); a new arm drives a git plumbing failure over resolved inputs (a corrupted object or an equivalent injected failure through the test's existing fixture seams) and wants exit 2 with `OUTCOME: indeterminate` naming what could not be determined (today that shape exits 2 as internal error, indistinguishable from usage); clean and violation arms keep their codes and gain the final OUTCOME line expectations. scan-public-hygiene: add selftest arms for the outcome emission (clean run exit 0 `OUTCOME: pass`, findings run exit 1 `OUTCOME: fail`, an own-error shape exit 3 `OUTCOME: tool_error`, today exit 2); run both → expect RED on the new and renewed arms [class: REPOSITORY_TEST]
- [x] Remap check_cleanup_scope_baseline's vocabulary per the answer-vocabulary criterion: unresolvable base ref, non-repo root, and usage become tool error (exit 3); git plumbing failures over resolved inputs become indeterminate (exit 2) with the observed/could-not-determine evidence; accounted and violation verdicts keep 0 and 1; every non-metadata run ends with exactly one final `OUTCOME:` line on stdout; the "cleanup-scope: internal error" prefix retires into the split arms; update the docstring exit-code line [class: IMPLEMENTATION_REQUIRED]
- [x] Remap scan-public-hygiene's vocabulary: the own-error class (the invalid-regex-in-patterns-file arm, the unreadable-input fail-closed guards, the environment failures) moves from exit 2 to exit 3 with `OUTCOME: tool_error`; clean stays 0 (`OUTCOME: pass`) and findings stay 1 (`OUTCOME: fail` after the hit lines); `--help` stays metadata-exempt and the successful `--selftest` run stays a no-line metadata-mode diagnostic; every non-metadata run ends with exactly one final `OUTCOME:` line on stdout; update the usage text's exit-code lines [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the runtime-home twin parity: `readlink -f` on the facts-key copy (public_hygiene_scan_script) resolves into this repository's canonical scripts directory, so the twin carries the migrated vocabulary at landing (the twin is a symlink by deployment, verified at authoring; the sync script's manifest does not manage this name, so no sync run is prescribed); record the parity receipt [class: IMPLEMENTATION_REQUIRED]
- [x] Re-wire the sweep lib's skills-repo hygiene arm (the block that runs the scan when the repository is the skills repo): a child exit 1 keeps landing in findings with the tail rows; a child exit 2 becomes an indeterminate gate result naming the child; a child exit 3 becomes a tool-error gate result naming the child; a child run with no final OUTCOME line classifies tool error per the no-line rule; renew the suite's arm fixtures [class: IMPLEMENTATION_REQUIRED]
- [x] Re-key scripts/release-rewrite.sh's `invoke_scanner` exit-code branch: the scanner's own-error class is exit 3 now, so the branch keys on 3 (today it keys on 2), the dead exit-2 arm and its reserved-code comment retire, and the findings fall-through keeps its mapping; the caller discards scanner stdout, so the OUTCOME-line check is inapplicable there and the receipt records that reading [class: IMPLEMENTATION_REQUIRED]
- [x] Probe the callers for exit-code branching, verifying the enumerated assumption live and recording the receipt (known exit-sensitive members: the plans skill's cleanup-scope step and its pre-round hygiene invocation, the done skill's cleanup and hygiene steps (the doc-registry bullet's prose-scan duty and the sensitive-data-scan fix-guidance wording the remap invalidates), the receiving-review skill's capture-hygiene recipe whose nonzero-stops-capture wording must learn the pass/findings/tool-error split, the sweep lib's hygiene arm, and the release-rewrite branch); update those recipe texts to branch on the four outcomes and the missing-OUTCOME-line rule (a tool error or a missing OUTCOME line records failed-resolution evidence and stops, never "fix the draft in place"), re-reading each anchor before editing and stopping on drift; re-verify the exit-agnostic claim for agents/skills/docs-branch/SKILL.md, agents/skills/lessons-migrate/SKILL.md, agents/skills/release/SKILL.md, and agents/skills/cursor-agent-diagnose/ (skill and run.sh) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: both selftests, the done-sweep lib suite, and the clean-tree hygiene scan still exiting 0 [class: REPOSITORY_TEST]
- [x] Commit: `feat: migrate the cleanup and hygiene gates and re-key the release caller` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Record the batch in the migration register and the compatibility note

Files:
- `scripts/OUTCOME_CONTRACT.md`

Evidence:
- `test "$(grep -c '| migrated' scripts/OUTCOME_CONTRACT.md)" -eq 14`; covers the eight batch rows plus the six previously migrated rows
- `$PY scripts/plan_readiness.py docs/history/plans/2026-10-03-outcome-contract-migration-batch-2.md`; covers the certification gate on the final bytes

- [x] Flip the eight batch rows' Status from queued to migrated, fill each row's Assumptions column with the per-script text drafted in Tasks 1 through 5, rewrite the batch-1 sweep-pair row's child-vocabulary and inheritance sentences to the migrated three-child-arm reality (the Task 1 and Task 2 drafted wording), and extend the compatibility note with the batch-2 entry: the guard-family "tool failure" prefix retires on the revert-set classifier; the former exit-2 readings are gone on the five python CLIs whose usage errors were argparse exits; the named remapped arms (the sibling-compat mismatch, the not-in-repo pins arm, the review-thread gate's six read and fetch arms, the rearm malformed-state arm, the hygiene own-error class, the release scanner branch re-key) are tool error now; the witnessed indeterminate classes are the classifier pair's plumbing-failure arms; the declared deviations are validate_review_staging's JSON-field outcome and the three selftest harnesses' metadata exemption; no modeled refusal or findings class changed its code [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect exit 0: the full Validation Commands block [class: REPOSITORY_TEST]
- [x] Commit: `docs: record outcome-contract batch 2 in the migration register` [class: IMPLEMENTATION_REQUIRED]
