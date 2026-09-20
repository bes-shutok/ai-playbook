# Plan: Authoring-side discipline: anti-idle, payload contracts, park guard

Origins (scope of record, read in full from docs/history/backlog/):
- docs/history/backlog/2026-09-20-plans-review-subagent-anti-idle-discipline.md
- docs/history/backlog/2026-09-20-plans-watcher-schedule-payload-contract-ambiguity.md
- docs/history/backlog/2026-09-20-park-guard-stand-down-carve-out-third-conjunct.md
- docs/history/backlog/2026-09-20-park-proposal-note-type-convention.md
- docs/history/backlog/2026-09-20-park-guard-r3-residuals.md
- docs/history/backlog/2026-09-20-closeout-migration-robustness-residues.md

Review artifacts: docs/reviews/2026-09-20-plan-review-authoring-side-discipline-anti-idle-payload-contracts-park-guard-r<N>.md plus the same-basename `.stats.json` sidecars (prefix match, any N; the readiness gate derives the review slug from this plan's full stem, so review rounds from r3 on use this full-stem naming and `artifact_slug`; rounds r1 and r2 exist under the short slug authoring-side-discipline, an authoring-time naming mismatch corrected from r3 on and harmless to the gate, which binds only the latest round's sidecar).

## Terms

- **probe report**: the JSON document `scripts/quota_window_probe.py` prints on stdout; classifier-read fields are `status`, `binding`, `pause_decision`, and `limits[]` entries carrying `kind` and `reset_at_epoch`.
- **plans-watcher-schedule**: the manifest-free driver CLI operation (`scripts/execute_plan_runtime.py`) that records one authoring budget-boundary decision and runs the scheduler fallback chain over the authoring machine-state JSON.
- **stand-down carve-out**: the maintenance failure cap's rule that an evidence-backed edit-nothing outcome (the plan's own first task prescribed a stand-down) accrues no failure credit.
- **park proposal**: the D4 record set (state-file `park_proposals` entry, repo-keyed memory note, turn output) proposing an externally-gated plan for parking.
- **closeout migration**: `scripts/worktree_closeout_migrate.py` capture/migrate, which moves review artifacts from an ad-hoc worktree into the primary checkout by verified copy, never move.

## Assumptions

- assume the six origin texts are the complete scope of record; basis: the authoring dispatch prompt, 2026-09-20.
- assume origin 2 is a contract-ambiguity defect, not a driver behavior bug, so the driver's classification logic is unchanged and the fix is contract pinning plus witness tests; basis: the origin's own Environment section.
- assume `agents/skills/maintenance/prompt-templates.md` and `agents/skills/maintenance/zcode.md` carry no plans-watcher payload contract and are therefore non-surfaces for origin 2 (grep-verified 2026-09-20, zero hits); basis: repo grep evidence.
- assume the archived park-guard plan may be edited for the origin-5.1 wording mirror, the origin itself prescribing the edit "whenever the archived plan is next touched"; this plan is that touch; basis: origin text, docs/history/backlog/2026-09-20-park-guard-r3-residuals.md.

Decision points requiring a grill: origin-5.2 sweep disposition softened to the name-derivable scope with the plan-absent plus entry-gone combination named as the residual case (initial recommendation was extension; re-scoped after review r1 F3 proved extension undiscoverable under the no-listing convention, standing pre-authorization dispatch prompt 2026-09-20 plus review r1 F3 2026-09-20; affects Task 5); origin-4 note convention keeps per-plan deterministic note names and fixes only the body's type literal to `park-proposal` with `plan` and `repo` fields, legacy parameterized-type bodies cleared on sight (standing pre-authorization dispatch prompt 2026-09-20 plus review r1 F2 identity resolution 2026-09-20; affects Task 4); origin-3 third conjunct is the Gate satisfaction rule re-run only, no brittle first-task prose grep (standing pre-authorization, dispatch prompt 2026-09-20; affects Task 3); origin-2 pin home is the runtime contract CLI boundary plus the driver `--input` help plus the plans Budget gate restatement plus two witness tests (standing pre-authorization, dispatch prompt 2026-09-20; affects Task 2); origin-6 verify-error test tampering moves to the verify seam with unpatched source-survives and destination-bytes assertions (standing pre-authorization, dispatch prompt 2026-09-20; affects Task 6); origin-6 unused `check-restored --plans-dir` is removed with the docs-branch invocation updated in the same task (standing pre-authorization, dispatch prompt 2026-09-20; affects Task 6).

## Gist & Examples

Six origins, three clusters, one discipline: authoring-side machinery stops failing silently.

**Cluster 1, plans authoring boundary (origins 1, 2).** Review rounds launched as sub-agents died three ways before anti-idle prompt discipline existed: two 600-second inactivity kills during long quiet reads, one transient provider 429 with no retry. The discipline paragraph (short calls, chunked reads, bounded commands, one retry on rate-limited tool calls) exists only in session notes; Task 1 makes it required text in the plans skill's Plan Quality Gate sub-agent template and in review-plan's per-worker launch contract, without touching the orchestrator's own retry classification (usage-rate-limit still never triggers a worker retry; the paragraph governs the worker's own in-round tool-call behavior). Separately, an orchestrator following the plans skill's Budget gate mirror hand-assembled a `plans-watcher-schedule` payload whose `probe_report` was a subset (flat `reset_at_epoch`, no `limits[]`) and got `classification=unknown`, `boundary=supersede`, `scheduling=none`, reason `resume-watcher-superseded`: report-only, nothing armed, at a boundary the canonical contract calls a trusted-epoch continue. The runtime contract already pins the payload key set but not the classifier-read fields, and the plans skill names only `state_path`. Task 2 pins the full-probe-report rule in three mirrors (runtime contract CLI boundary, driver `--input` help, plans Budget gate restatement) and adds two witness tests plus mutation probes proving they discriminate.

**Cluster 2, park-guard skill (origins 3, 4, 5).** The stand-down carve-out's machine test (json naming the plan path, plus plan bytes unchanged since `dispatch_plan_sha`) is child-asserted evidence: a json-writing failed child is indistinguishable from a legitimate stand-down and silently defeats the failure cap. Task 3 adds a third conjunct the checking turn evaluates itself (re-run the Gate satisfaction rule on the target plan; a claim on a satisfied gate accrues credit normally) and an echo duty for triage. Task 4 unifies the park-proposal note convention: per-plan deterministic note names stay (they are what keeps concurrent proposals from overwriting each other and what makes the no-listing clear targeted), while the note body's type literal becomes the fixed `park-proposal` with `plan` and `repo` fields, matching the corpus's other scheduler notes (`successor-chain-failed` and friends); legacy parameterized-type bodies are cleared on sight under the same deterministic name. Task 5 closes the three r3 residual lows: the archived plan's superseded marker-attribution wording is mirrored to the corrected json-conjunct attribution, the "no orphaned note survives" claim is softened to the scope the name-derivable sweep actually covers (the one plan-absent plus entry-gone combination is named as the residual case, review r1 F3), and both header-block restatements in prompt-templates.md gain the no-`## `-heading clause (header block extends to end of file) the SKILL.md definition already carries.

**Cluster 3, closeout tooling (origin 6).** Four residues and three guard residues: `capture` crashes with a raw traceback on a dangling symlink; the migration manifest is written only after the full copy loop so a mid-loop exception orphans already-copied files from the audit record; the verify-error test patches `_copy_file`, bypassing production copy semantics; docs-branch and execute-plan prose is stale (the failure-semantics enumeration omits the certified-downgrade refusal, and the throwaway-script rationale still says docs-branch "never auto-prunes" though it prunes narrow ephemeral classes); the guard's `check-restored` accepts an unused `--plans-dir`, a missing dedupe script skips silently, and an unreadable plan file fails the guard closed by accident with a traceback. Task 6 hardens all of these with named skip-and-warn edges, a finally-scoped manifest write, a verify-seam test tamper, and the prose corrections.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every contract change carries a machine gate (grep pin for prose, pytest witness for behavior) that fails on today's tree and passes after its task lands; the whole Validation Commands block is executed at authoring time and the first failing gate recorded (rules 19 and 33 of the plans skill).
- consistency: every restated payload rule agrees with `classify_boundary` and `run_cli_watcher_operation` in `scripts/execute_plan_resume_watcher.py`; sibling restatements of the same contract are swept and updated in the same task (noun-phrase sweep, plans skill fold rule).
- regression safety: the driver, closeout, and guard test suites exit 0 on the final tree; no existing test regresses.
- hygiene: the no-em-dash scan and the public hygiene scan exit 0 over the plan and the changed tree.

**Done when:**
- `python3 scripts/plan_readiness.py docs/plans/2026-09-20-authoring-side-discipline-anti-idle-payload-contracts-park-guard.md` exits 0 against the certified review sidecar.
- All Validation Commands gates exit 0 on the final tree.
- `python3 scripts/test_execute_plan_runtime.py`, `python3 scripts/test_worktree_closeout_migrate.py`, and `python3 scripts/test_docs_branch_plan_guard.py` each exit 0.

**Ship when:**
- Nothing; this plan is fully repository-verifiable. [class: EXTERNAL_RELEASE_GATE] is intentionally absent; no external gates exist for this work.

## Review Scope

**Explicit must-fix; findings on these paths are always in scope (review and fix if valid):**

**Production code:**
- `scripts/execute_plan_runtime.py` (only the `--input` argparse help string; all other functions and the driver's classification logic are frozen)
- `scripts/worktree_closeout_migrate.py`
- `scripts/docs_branch_plan_guard.py`

**Tests:**
- `scripts/test_execute_plan_runtime.py` (only the new `PlansWatcherScheduleContractTest` class; all existing tests are frozen)
- `scripts/test_worktree_closeout_migrate.py`
- `scripts/test_docs_branch_plan_guard.py`

**Documentation:**
- `agents/skills/plans/SKILL.md` (Plan Quality Gate sub-agent prompt template; Budget gate Authoring watcher state paragraph)
- `agents/skills/review-plan/SKILL.md` (Step 2 worker-launch contract)
- `agents/skills/execute-plan/runtime-contract.md` (plans authoring watcher mirror paragraph in the CLI boundary section)
- `agents/skills/maintenance/SKILL.md` (Step 1 memory-index line, D4 line, stand-down carve-out block, carve-out witness line)
- `agents/skills/maintenance/prompt-templates.md` (the two header-block restatements only)
- `agents/skills/docs-branch/SKILL.md` (check-restored invocation, dedupe block, Failure semantics line)
- `agents/skills/execute-plan/SKILL.md` (exit-path throwaway-script cleanup rationale only)
- `docs/plans/completed/2026-09-19-maintenance-park-guard-externally-gated-plans.md` (the Task 3 Carve-out witness checkbox line only; historical checkbox state is preserved)

**Plan-related extension;** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/zcode.md`; grep-verified non-surface for every origin (2026-09-20), and the changelog-style entries there are historical.
- `scripts/quota_window_probe.py` and `agents/hooks/`; consumers of the probe report, never its definition.
- `scripts/execute_plan_resume_watcher.py`; the shared classifier is read as the source of truth, changed only if review proves a defect in it (any such change is a plan-related extension, not an explicit must-fix).
- All `## Change history` / changelog entries in any touched skill file; historical records are never rewritten.

## Validation Commands

```bash
#!/bin/bash
# Validation gates for the authoring-side discipline plan.
# Usage: bash gates.sh [task-number]   (no argument runs every gate)
# Each gate label names its task; gates are RED (fail) on today's tree and
# flip GREEN exactly when their task lands. Explicit abort on every miss.
set -u
cd "$(git rev-parse --show-toplevel)" || { echo "not inside a repository" >&2; exit 1; }
TASK="${1:-all}"
gate() { [ "$TASK" = "all" ] || [ "$TASK" = "$1" ]; }
fail() { echo "FAIL: $*" >&2; exit 1; }

# --- Task 1: anti-idle runtime discipline -------------------------------
gate 1 && {
  test -f agents/skills/plans/SKILL.md || fail "G1a target missing"
  grep -qF "Anti-idle runtime discipline (required in every review-round launch)" agents/skills/plans/SKILL.md || fail "G1a plans template carries the paragraph"
  grep -qF "retry that call once after a short pause" agents/skills/plans/SKILL.md || fail "G1b plans template carries the retry rule"
  test -f agents/skills/review-plan/SKILL.md || fail "G1c target missing"
  grep -qF "Anti-idle runtime discipline (required in every review-round launch)" agents/skills/review-plan/SKILL.md || fail "G1c review-plan worker contract carries the paragraph"
  grep -qF "leaves the orchestrator's retry classification" agents/skills/review-plan/SKILL.md || fail "G1d separation sentence present"
  echo "ok: task 1"
}

# --- Task 2: plans-watcher-schedule probe-report contract ---------------
gate 2 && {
  test -f agents/skills/execute-plan/runtime-contract.md || fail "G2a target missing"
  grep -qF "must be the FULL probe report, never a subset" agents/skills/execute-plan/runtime-contract.md || fail "G2a runtime contract pins the full-report rule"
  test -f scripts/execute_plan_runtime.py || fail "G2b target missing"
  grep -qF "a subset payload classifies unknown and degrades to the report-only supersede" scripts/execute_plan_runtime.py || fail "G2b driver help pins the degradation"
  test -f agents/skills/plans/SKILL.md || fail "G2c target missing"
  grep -qF "the classifier reads \`status\`, \`binding\`, \`pause_decision\`, and the binding limit's \`reset_at_epoch\` from \`limits[]\`" agents/skills/plans/SKILL.md || fail "G2c plans Budget gate restates the classifier fields"
  python3 scripts/test_execute_plan_runtime.py PlansWatcherScheduleContractTest || fail "G2d witness tests"
  echo "ok: task 2"
}

# --- Task 3: stand-down carve-out third conjunct -------------------------
gate 3 && {
  test -f agents/skills/maintenance/SKILL.md || fail "G3 target missing"
  grep -qF "three conjuncts, all required and named" agents/skills/maintenance/SKILL.md || fail "G3a machine test counts three conjuncts"
  grep -qF "re-runs the Gate satisfaction rule (Step 1) on the target plan's own current bytes" agents/skills/maintenance/SKILL.md || fail "G3b third conjunct named"
  grep -qF "echoes the consumed json's contents" agents/skills/maintenance/SKILL.md || fail "G3c echo duty present"
  grep -qF "while the plan's gate re-reads satisfied under conjunct 3" agents/skills/maintenance/SKILL.md || fail "G3d witness sentence present"
  echo "ok: task 3"
}

# --- Task 4: fixed park-proposal note type -------------------------------
gate 4 && {
  test -f agents/skills/maintenance/SKILL.md || fail "G4 target missing"
  grep -qF "fixed type literal \`park-proposal\` with \`plan\` and \`repo\` fields" agents/skills/maintenance/SKILL.md || fail "G4a fixed type convention present"
  grep -qF "matches the same clear by its name suffix alone and is deleted on sight" agents/skills/maintenance/SKILL.md || fail "G4b legacy transition matching present"
  if grep -qF "suffixed with the plan's basename so concurrent proposals never overwrite each other" agents/skills/maintenance/SKILL.md; then fail "G4c superseded D4 wording still present"; fi
  echo "ok: task 4"
}

# --- Task 5: park-guard r3 residual lows ---------------------------------
gate 5 && {
  test -f docs/plans/completed/2026-09-19-maintenance-park-guard-externally-gated-plans.md || fail "G5a target missing"
  if grep -qF "does not OPEN with the marker" docs/plans/completed/2026-09-19-maintenance-park-guard-externally-gated-plans.md; then fail "G5a superseded wording still in archived plan"; fi
  grep -qF "via the json conjunct, not marker matching" docs/plans/completed/2026-09-19-maintenance-park-guard-externally-gated-plans.md || fail "G5a corrected wording mirrored"
  test -f agents/skills/maintenance/SKILL.md || fail "G5b target missing"
  grep -qF "whose plan is absent from the survey AND whose state entry is gone" agents/skills/maintenance/SKILL.md || fail "G5b orphan combination covered"
  test -f agents/skills/maintenance/prompt-templates.md || fail "G5c target missing"
  test "$(grep -cF "header block extends to the end of the file" agents/skills/maintenance/prompt-templates.md)" -eq 2 || fail "G5c both payload restatements carry the no-heading clause"
  test "$(grep -cF "header block extends to the end of the file" agents/skills/maintenance/SKILL.md)" -eq 1 || fail "G5d canonical definition count changed"
  echo "ok: task 5"
}

# --- Task 6: closeout migration and guard hardening ----------------------
gate 6 && {
  test -f scripts/worktree_closeout_migrate.py || fail "G6 target missing"
  grep -qF "skipping unreadable path" scripts/worktree_closeout_migrate.py || fail "G6a capture named skip"
  grep -qF "finally:" scripts/worktree_closeout_migrate.py || fail "G6b manifest write in finally"
  grep -qF '"interrupted"' scripts/worktree_closeout_migrate.py || fail "G6b interrupted flag"
  test -f scripts/docs_branch_plan_guard.py || fail "G6c target missing"
  grep -qF "skipping unreadable plan pair" scripts/docs_branch_plan_guard.py || fail "G6c guard named skip"
  test -f agents/skills/docs-branch/SKILL.md || fail "G6e target missing"
  grep -qF "backlog dedupe script not found; sync proceeds without the duplicate sweep" agents/skills/docs-branch/SKILL.md || fail "G6e dedupe missing-script warn"
  grep -qF "certified-downgrade refusal" agents/skills/docs-branch/SKILL.md || fail "G6f failure semantics naming the refusal"
  grep -qF "check-restored" agents/skills/docs-branch/SKILL.md || fail "G6h anchor vanished"
  if sed -n '/check-restored/,+2p' agents/skills/docs-branch/SKILL.md | grep -F -- "--plans-dir"; then fail "G6h check-restored still passes --plans-dir"; fi
  test -f agents/skills/execute-plan/SKILL.md || fail "G6g target missing"
  if grep -qF "never auto-prunes" agents/skills/execute-plan/SKILL.md; then fail "G6g stale rationale still present"; fi
  grep -qF "prunes only narrow ephemeral classes" agents/skills/execute-plan/SKILL.md || fail "G6g corrected rationale present"
  python3 scripts/test_worktree_closeout_migrate.py || fail "G6i closeout suite"
  python3 scripts/test_docs_branch_plan_guard.py || fail "G6j guard suite"
  echo "ok: task 6"
}

# --- Task 7: whole-tree gates (run after review certification) -----------
gate 7 && {
  python3 scripts/test_execute_plan_runtime.py || fail "G7a full driver suite"
  python3 scripts/plan_readiness.py docs/plans/2026-09-20-authoring-side-discipline-anti-idle-payload-contracts-park-guard.md || fail "G7b readiness gate"
  bash scripts/check-no-em-dash.sh file docs/plans/2026-09-20-authoring-side-discipline-anti-idle-payload-contracts-park-guard.md || fail "G7c em-dash scan"
  bash scripts/scan-public-hygiene.sh || fail "G7d hygiene scan"
  echo "ok: task 7"
}

echo "all requested gates green"
```

Authoring-time execution record (tree before any task, 2026-09-20): `bash -n` clean; every task gate group fails at its first gate with the polarity above (G1a, G2a, G3a, G4a, G5a as a fired forbidden-match witness, G6a); G7a's full driver suite passed (269 tests OK) and G7b failed with "configured reviews_dir does not exist on disk" (the reviews dir does not exist before the review loop creates it; the first sidecar matching this plan's full-stem slug lands with round r3), the expected pre-certification state. No gate passed vacuously.

### Task 1: Anti-idle runtime discipline in every review-round launch

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-plan/SKILL.md`

- [ ] Insert into the plans skill's Plan Quality Gate sub-agent prompt template (agents/skills/plans/SKILL.md, the fenced template body, after the "Read the actual source files" paragraph) this paragraph verbatim: `Anti-idle runtime discipline (required in every review-round launch): emit a tool call or a progress message at least every 2-3 minutes; chunk file reads to at most 400 lines per read; never launch a single command expected to run longer than 60 seconds; on a rate-limit error from one of your own tool calls, retry that call once after a short pause before treating the round as failed.` [class: IMPLEMENTATION_REQUIRED]
- [ ] Add item 10 to review-plan Step 2's "Each worker receives" list (agents/skills/review-plan/SKILL.md): `Anti-idle runtime discipline: every worker prompt carries the anti-idle runtime discipline paragraph from the plans skill's Plan Quality Gate sub-agent template verbatim (the paragraph opening "Anti-idle runtime discipline (required in every review-round launch)"). It governs the worker's own in-round tool-call behavior, including the one retry on its own rate-limited tool call, and leaves the orchestrator's retry classification in "Bounded attempts and retry classification" unchanged: usage-rate-limit still never triggers a worker retry.` [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect RED today: `bash gates.sh 1` fails at G1a (the paragraph exists in neither file on the authoring-day tree; see the authoring-time execution record under Validation Commands). [class: REPOSITORY_TEST]
- [ ] Apply the two edits above; run → expect GREEN: `bash gates.sh 1` passes G1a through G1d. [class: REPOSITORY_TEST]
- [ ] Commit: `skills: require anti-idle runtime discipline in every plan-review round launch` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Pin the plans-watcher-schedule full-probe-report contract

Files:
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/execute_plan_runtime.py`
- `agents/skills/plans/SKILL.md`
- `scripts/test_execute_plan_runtime.py`

- [ ] In the runtime contract's CLI boundary section (agents/skills/execute-plan/runtime-contract.md), append to the END of the plans authoring watcher mirror paragraph, immediately after the mirror paragraph's final sentence, which ends with the plans-terminal entry "'kind' of 'complete', 'archived', or 'aborted')." (note the closing paren before the period; the closed end of the operation enumeration; never mid-enumeration), these sentences: "The schedule arm's probe report must be the FULL probe report, never a subset: the boundary classifier reads `status`, `binding`, `pause_decision`, and the binding window's `reset_at_epoch` from the matching `limits[]` entry, so a subset payload (for example one carrying a flat `reset_at_epoch` without `limits[]`) classifies `unknown` and degrades to the report-only supersede." [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend the driver's `--input` argparse help string in scripts/execute_plan_runtime.py (main, the `parser.add_argument("--input", ...)` call) from its current text to: `JSON object payload (create, checkpoint, done, interrupt, progress, terminal, and the watcher-* and plans-* operations; plans-watcher-schedule takes the FULL probe report as probe_report, or the payload itself, plus plan_path and state_path; the classifier reads status, binding, pause_decision, and the binding limit's reset_at_epoch from limits[], so a subset payload classifies unknown and degrades to the report-only supersede)`. No driver logic changes. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the plans skill's Budget gate Authoring watcher state paragraph (agents/skills/plans/SKILL.md), immediately after "each taking the payload `state_path` naming `{tmp_dir}/plan-requirements-<slug>.json`", insert the following text verbatim (real backticks; it must byte-match the G2c span below): " (plans-watcher-schedule additionally takes the FULL probe report JSON as probe_report, plus plan_path: never a subset, because the classifier reads `status`, `binding`, `pause_decision`, and the binding limit's `reset_at_epoch` from `limits[]`; a subset classifies unknown and the boundary degrades to the report-only supersede, so read the receipt's reason after every scheduling call)". [class: IMPLEMENTATION_REQUIRED]
- [ ] `PlansWatcherScheduleContractTest#test_trusted_epoch_continue_installs_watcher`; given a temp state_path, a readable temp plan file, and a full probe report payload (`status: "ok"`, `binding: "5h"`, `pause_decision: "continue"`, `limits: [{"kind": "5h", "reset_at_epoch": <integer epoch one hour in the future>}]`) passed with `plan_path` and `state_path` through the driver's plans-watcher-schedule entry (`_plans_watcher_operation`), expects status `success`, reason `resume-watcher-scheduled`, a non-null `resume_watcher` receipt, and non-null `scheduling`. Mirror the file's existing helper conventions for temp dirs and payload construction; the epoch must be an `int` (`trusted_binding_reset_epoch` rejects non-int values via its isinstance check). [class: REPOSITORY_TEST]
- [ ] `PlansWatcherScheduleContractTest#test_probe_subset_degrades_report_only`; given the same boundary but a subset probe report (flat `reset_at_epoch` at the payload top level, `status: "ok"`, `binding: "5h"`, no `limits` key), expects status `blocked`, reason `resume-watcher-superseded`, classification evidence naming `unknown`, and `scheduling` None (report-only, nothing armed). [class: REPOSITORY_TEST]
- [ ] Mutation probe both directions (rules 11 and 30): (a) invert the `limits[]` kind comparison in `trusted_binding_reset_epoch` (scripts/execute_plan_resume_watcher.py), run the new class, and observe exactly the install test fail; (b) instead simulate the plausible wrong fix (fall back to a flat `probe_report["reset_at_epoch"]` when no limits[] entry matches), run the class, and observe exactly the subset test fail. Revert both; run → expect GREEN. [class: REPOSITORY_TEST]
- [ ] Run → expect: G2d is GREEN as soon as the two tests land (they pin existing classifier behavior, RED-only via the mutation probes); G2a through G2c flip GREEN with the three prose edits; `bash gates.sh 2` passes. [class: REPOSITORY_TEST]
- [ ] Commit: `runtime: pin plans-watcher-schedule full-probe-report contract with witness tests` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Stand-down carve-out third conjunct and json echo

Files:
- `agents/skills/maintenance/SKILL.md`

- [ ] In the stand-down carve-out (agents/skills/maintenance/SKILL.md, the block opening "Stand-down carve-out (beside the evidenced provider-side stop exception"), change "Machine test, two conjuncts, both required and named:" to "Machine test, three conjuncts, all required and named:" and after conjunct (2) insert: `; (3) the checking turn re-runs the Gate satisfaction rule (Step 1) on the target plan's own current bytes and the gate reads unsatisfied: a child claiming stand-down on a plan whose gate now reads satisfied (a stale dispatch, the gate having satisfied between dispatch and check) or on a plan whose header block carries no External gate line accrues credit normally, the one conjunct the checking turn evaluates itself rather than trusting child-asserted evidence`. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the same block, after the sentence on consuming the checked json file, insert: `The turn output echoes the consumed json's contents (its plan, reason, and date values) for triage alongside the quoted marker witness.` [class: IMPLEMENTATION_REQUIRED]
- [ ] In the carve-out witness paragraph (the line opening "Carve-out witness: a stand-down outcome accrues nothing"), append: `; a child whose json satisfies conjuncts 1 and 2 while the plan's gate re-reads satisfied under conjunct 3 does not qualify and accrues credit normally`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect RED today at G3a, then GREEN after the three edits: `bash gates.sh 3` passes. [class: REPOSITORY_TEST]
- [ ] Commit: `skills: stand-down carve-out gains the gate-recheck third conjunct` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Fixed park-proposal note type with legacy transition matching

Files:
- `agents/skills/maintenance/SKILL.md`

- [ ] In D4 (agents/skills/maintenance/SKILL.md, the line opening "`D4 (propose park)`"), replace "a per-plan repo-keyed `park-proposal-<plan-basename>` memory note (repo-keyed like `loop-parent-missing`, suffixed with the plan's basename so concurrent proposals never overwrite each other; the note's body carries the plan path, the gate text, and the latest evidence, mirroring the state entry)" with "a per-plan repo-keyed memory note named `park-proposal-<plan-basename>` (repo-keyed like `loop-parent-missing`; the deterministic per-plan name is what keeps concurrent proposals from overwriting each other) whose body carries the fixed type literal `park-proposal` with `plan` and `repo` fields (the `plan` field naming the proposed plan's path, mirroring the state entry), plus the gate text and the latest evidence". The note identity scheme stays per-plan names; only the body's type literal unifies. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the Step 1 memory-index line's park-proposal lifecycle (the line opening "- Memory index:"), replace "deletes the repo-matching `park-proposal-<plan-basename>` note (the note's `repo` key must match the resolved repository root: one note read, no listing; the deterministic note name makes it a targeted clear, so a cross-repo name collision cannot be deleted)" with "deletes the repo-matching `park-proposal-<plan-basename>` note after its identity confirms the target (the note's `repo` key must match the resolved repository root, and the target is confirmed by the body's `plan` field for fixed-type bodies or by the name's own plan-basename suffix for legacy parameterized-type bodies: one note read, no listing; the deterministic name plus that confirmation makes the clear targeted, so a note naming a different plan is never deleted); a legacy note whose body carries the parameterized type literal (`park-proposal-<plan-basename>` as the type) matches the same clear by its name suffix alone and is deleted on sight, so notes written before the fixed body type self-migrate without a separate migration pass". [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect RED today at G4a, then GREEN after both edits (G4c confirms the superseded D4 wording is gone): `bash gates.sh 4` passes. [class: REPOSITORY_TEST]
- [ ] Commit: `skills: fixed park-proposal note type with legacy transition matching` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Park-guard r3 residual lows

Files:
- `docs/plans/completed/2026-09-19-maintenance-park-guard-externally-gated-plans.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`

- [ ] In the archived park-guard plan's Task 3 Carve-out witness checkbox (the `[x]` line containing "does not OPEN with the marker"), replace "; a child whose report contains the word stand-down anywhere but does not OPEN with the marker does not qualify." with "; a child whose report contains the word stand-down anywhere but wrote no json file does not qualify: via the json conjunct, not marker matching." Keep the checkbox checked; this is the paperkeeping wording mirror the origin prescribes, mirroring the r2-corrected skill text. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the Step 1 memory-index line's park-proposal lifecycle, replace "is deleted too, so no orphaned note survives." with "is deleted too. The sweep is name-derivable only: a note whose plan is absent from the survey AND whose state entry is gone has no derivable name under the one-note-read no-listing convention, so that combination is the one case that can leave an orphaned note until the plan revives (its reappearance makes the basename derivable and the surveyed-but-entry-gone rule deletes it) or a human clears it; the no-orphan property is claimed only for the name-derivable combinations." The authoring-time recommendation to extend the sweep was re-scoped to this softened claim after review r1 F3 proved extension undiscoverable for notes whose name cannot be derived. [class: IMPLEMENTATION_REQUIRED]
- [ ] In both prompt-templates.md header-block restatements (the successor external-gate skip entry and the SUCCESSOR DISPATCH payload body's D1-rule restatement), append the no-`## `-heading clause inside each restatement's existing header-block parenthesis (the two sites word the parenthesis slightly differently; do not expect one exact old string): the parenthesis gains "; when the plan carries no `## ` heading at all, the header block extends to the end of the file", mirroring the SKILL.md definition. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect RED today at G5a/G5b/G5c, then GREEN after the three edits: `bash gates.sh 5` passes. [class: REPOSITORY_TEST]
- [ ] Commit: `skills: park-guard r3 residual lows (witness wording, orphan sweep, header-block clause)` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Closeout migration and docs-branch guard hardening

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py`
- `scripts/docs_branch_plan_guard.py`
- `scripts/test_docs_branch_plan_guard.py`
- `agents/skills/docs-branch/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`

- [ ] `WorktreeCloseoutTest#test_capture_skips_dangling_symlink_with_named_warn`; given a captured tree containing a regular file and a dangling symlink under docs/reviews, expects capture to exit 0, print a stderr warn naming the unreadable path ("skipping unreadable path"), and record the path in a `skipped` list in the baseline JSON while the regular file still hashes normally. RED first. [class: REPOSITORY_TEST]
- [ ] Implement the capture edge in cmd_capture: per-file `_sha256` wrapped so an OSError prints `WARN: capture: skipping unreadable path <rel>: <reason>` to stderr and records the relative path in a `skipped` list written into the baseline JSON; exit stays 0. [class: IMPLEMENTATION_REQUIRED]
- [ ] `WorktreeCloseoutTest#test_manifest_written_on_midloop_crash`; given a two-file migration where the copy of the second file raises OSError (crash injected by patching `_copy_file` to raise for that one path; this is the crash-injection seam, distinct from the verify-error arm), expects the raised exception to propagate AND the manifest to already contain the first file's migrated entry plus an `"interrupted": true` marker. RED first. [class: REPOSITORY_TEST]
- [ ] Move the migration manifest append into a `finally:` block around the copy loop: the sections collected so far are appended even when an exception is in flight, with an `"interrupted": true` marker added only on that path, and the exception then propagates unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Rewrite `WorktreeCloseoutTest#test_migrate_fails_without_moving_on_verify_error` to tamper the verify seam instead of the copy seam: patch `MODULE._verify_copy` to return False, leaving production `_copy_file` unpatched; keep the source-survives assertion and add a destination-bytes assertion that the production copy ran (destination bytes equal source bytes even though verification failed). [class: IMPLEMENTATION_REQUIRED]
- [ ] `DocsBranchPlanGuardTest` unreadable-plan edge: given a shared plan file made unreadable (chmod 0o000, restored in a finally; skip the test when `os.geteuid() == 0` since root reads defeat the chmod), expects `guard` to exit NON-ZERO with a stderr warn naming the path ("skipping unreadable plan pair") and no traceback, keeping the guard subcommand's fail-closed posture on inputs it cannot verify, and expects `check-restored` to exit 0 with the same named warn (a witness leg, warn-and-continue). RED first: today the failure is a bare traceback with no named warn. [class: REPOSITORY_TEST]
- [ ] Implement the guard edge in cmd_guard and cmd_check_restored: wrap the `sha256_file` reads so an OSError prints a named warn (`WARN: guard: skipping unreadable plan pair for <path>: <reason>`, and the check-restored equivalent); cmd_guard then returns non-zero (the certified-downgrade boundary stays closed on unverifiable inputs), while cmd_check_restored continues and returns 0. Never a traceback. [class: IMPLEMENTATION_REQUIRED]
- [ ] `DocsBranchPlanGuardTest` flag-removal pin: given `check-restored` invoked with `--plans-dir`, expects argparse to reject it (SystemExit 2); given the invocation without it, expects normal warn-only behavior. RED first. [class: REPOSITORY_TEST]
- [ ] Remove the unused `--plans-dir` option from the check-restored subparser in scripts/docs_branch_plan_guard.py (the guard subparser keeps its own used `--plans-dir`). [class: IMPLEMENTATION_REQUIRED]
- [ ] In agents/skills/docs-branch/SKILL.md's restore-leg block, drop `--plans-dir "$_plans_dir_ord"` from the `check-restored` invocation (the guard invocation in the pre-staging block keeps its own --plans-dir; only the check-restored line changes). [class: IMPLEMENTATION_REQUIRED]
- [ ] In agents/skills/docs-branch/SKILL.md's backlog duplicate sweep block, restructure the single `if [ -f "$DEDUPE_SCRIPT" ] && [ -d ... ]` into a dir check with an inner script check whose else branch prints `WARN: backlog dedupe script not found; sync proceeds without the duplicate sweep` to stderr, matching the guard script's missing-script loudness. [class: IMPLEMENTATION_REQUIRED]
- [ ] In agents/skills/docs-branch/SKILL.md's Failure semantics line, extend the enumeration: after "or a failed commit each returns non-zero with a loud message", insert ", as does a certified-downgrade refusal (the plan guard's exit 1 before staging, naming every refused row)". [class: IMPLEMENTATION_REQUIRED]
- [ ] In agents/skills/execute-plan/SKILL.md's exit-path throwaway-script cleanup paragraph, replace "`docs-branch` is add-only and never auto-prunes" with "`docs-branch` is add-only and prunes only narrow ephemeral classes (stale cf-out snapshots, __pycache__, dirs orphaned by a completed doc-hierarchy migration)". [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect RED today at G6a/G6b/G6c and the new tests failing, then GREEN after the implementations; `bash gates.sh 6` passes. [class: REPOSITORY_TEST]
- [ ] Commit: `scripts: harden closeout migration and docs-branch plan guard edges` [class: IMPLEMENTATION_REQUIRED]

### Task 7: Whole-tree certification gates

Files:
- none (gates only)

- [ ] Run `bash gates.sh` with no argument → expect every gate GREEN on the final tree; G7a runs the full driver suite, G7b the readiness gate against the certified sidecar (runs only after the review loop completes; at authoring time it fails on the missing sidecar, the expected pre-certification state), G7c the em-dash scan over the plan, G7d the public hygiene scan over the tree. [class: REPOSITORY_TEST]
- [ ] Confirm no commit is needed; this task lands no bytes of its own. [class: REPOSITORY_TEST]
