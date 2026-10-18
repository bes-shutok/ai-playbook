# Plan: done closeout cost and skill scope reduction

Backlog origin: docs/history/backlog/2026-10-06-done-closeout-cost-and-skill-scope.md
Driving force: simplicity + efficiency
Plan review record: the staging series docs/history/reviews/2026-10-07-plan-review-done-closeout-cost-and-skill-scope-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 3.0h total, largest task 1.0h
Authoring claim: docs/tmp/authoring-claims/2026-10-06-done-closeout-cost-and-skill-scope.md (session sess_1e13991c-8e25-4535-9a7e-ae31500fc603)

## Terms

- runtime home: the deployed `$HOME/.ai-playbook/scripts/` directory the done flow's resolution convention falls back to (repo-local `scripts/` copy first, deployed copy second).
- canonical repo: the skills repository checkout the carrier treats as the deployment source, resolved through the chain: explicit `--repo` flag, then the invocation repo's toplevel when it is itself a skills-repo checkout (its toplevel carries `scripts/runtime-scripts.list`; a worktree and the primary checkout qualify equally), then the user facts `skills_repo_path` key (the same key the done skill's Configuration table resolves); when no arm resolves, or the resolved canonical carries no `scripts/runtime-scripts.list`, deploy mode refuses with `OUTCOME: tool_error` and check mode reports the skipped arms. The carrier reads its inventory manifest only from the resolved canonical repo. The repo is the source and the runtime home is the destination, never the reverse.
- stale deployment: a runtime-home name that no longer matches its canonical counterpart (a regular-file copy lagging the source, or a symlink aimed at a moved target), or a name the done flow needs that is missing from the runtime home; the class behind the witnessed 2026-10-06 dirt-regression block and the ledger's revert-set-classifier incident row.
- drift advisory: the report-only freshness check (`deploy_runtime_helpers.sh --check`) that names stale or missing helpers and always exits 0; posture matches the rearm-on-touch posture (echo-and-continue, never blocks).
- rearm-on-touch posture: the advisory echo-and-continue contract the done skill already applies to its maintenance rearm check; a failed or skipped advisory is reported in the run record and never blocks the boundary.
- helper inventory: every name admitted by `scripts/runtime-scripts.list` (the repo's deployed-home manifest, one name per line with `#` comments), which the carrier reads at run time; the manifest's own admission criterion is a name the maintenance, execute-plan, or done skills resolve from the deployed home copy.
- carrier script: `scripts/deploy_runtime_helpers.sh`, the runnable stale-deployment remedy; a verbatim multi-line bash recipe inside the skill is a design smell, so the remedy becomes a real script the prose invokes.
- guard liveness ledger: the tracked recorder at `scripts/gate_liveness_ledger.py` plus `scripts/gate_liveness_ledger.json` holding per-guard catch, incident, and basis rows; this plan reads it as input and writes nothing to it.
- dirt-regression gate: the Step 3 working-tree guard (`scripts/dirt_regression_gate.py`) whose stale deployed copy produced the witnessed 2026-10-06 false block.
- pins suite: `scripts/check_maintenance_pins.sh`, the literal-span guard over the maintenance-family skill bodies.

## Why

A stale runtime-home helper blocked a valid consumer closeout on 2026-10-06 and recovery took multiple manual rounds, because the skill's stale-deployment recognition is scattered across four sites, each carrying its own inline remedy recipe, and nothing checks helper freshness before the gates run. The guard liveness ledger records the same class independently (the revert-set-classifier incident: an absent deployed copy produced a false missing-dependency block while the canonical copy existed). The evidenced fix is one sanctioned recovery path plus drift visibility at the boundary start, not more per-gate prose.

## Outcome

A done closeout that hits the stale-deployment class recovers with one command, and helper drift is visible before the gates that depend on it run.

- The four scattered stale-deployment recognition sites keep telling the reader how to recognize the class but share one canonical remedy paragraph naming the carrier script, so the per-gate cp recipes and the seven-copy manual list disappear from the skill.
- Step 0 runs the advisory drift check once after the lock; stale or missing helpers print as advisory lines with the same one-command remedy, and the closeout continues.
- Removing the guard stack as a whole was evaluated against the guard liveness ledger and rejected with cited catches (see Gist & Examples); the selection adds no refusal class, gate, fence, protocol layer, or schema field.

Gate delta: no refusal class, hard gate, fence, protocol layer, or schema state field is added or removed; the simplification removes the duplicated stale-deployment remedy prose (the Step 0 lib inline recipe, the doc-registry single-file cp recipe, the plan-readiness seven-copy manual list, the Step 6 stale-finalizer inline refresh) in favor of one canonical paragraph plus the runnable carrier, and the drift advisory is a report-only surface priced by the origin-cited witnessed block (a stale deployed dirt-regression gate copy blocked valid work across multiple recovery rounds, 2026-10-06) and the ledger's same-class revert-set-classifier incident row (scripts/gate_liveness_ledger.json; the ledger's gate-addition citation duty does not apply because this plan adds no gate or fence).

## Assumptions

- assume the selection implements the drift-recovery path and the prose consolidation and nothing else, because the ledger's other evidenced delay classes already received their remedies: the 25-minute post-landing-staging incident's class got the indeterminate-under-lock arm plus the operator tally landing, and all four run-manifest-writer incidents landed their fixes (checkpoint writer, bulk affordances, recovery and disposition subcommands); basis: scripts/gate_liveness_ledger.json rows dated 2026-10-05/06 re-derived at authoring time.
- assume removing the done guard stack as a whole is rejected on recorded catches, not inertia: the ledger records 11 catches against 14 incidents, and the catch rows name harms that would reopen (the stale-base landing refusal of commit d41bf3e5, the fabricated-digest refusal, the corrupted-supersession-link refusal, the foreign peer stub preservation); basis: `python3 scripts/gate_liveness_ledger.py show` at authoring time.
- assume the drift advisory never becomes a gate: a blocking freshness check would add a refusal class with no witness that drift ever went undetected (both witnessed drift incidents were caught at gate time; the cost was recovery, not detection), and the origin forbids adding a gate unless existing evidence cannot answer a necessary question; basis: the origin's Expected paragraph plus the ledger's dirt-regression gate and revert-set-classifier rows.
- assume Step 2.5 (formatting-only rollback) keeps its explicit all-files scope: its cost is bounded (only files whose every hunk is formatting-only are reverted) and no ledger row or origin evidence names it as a closeout delay; basis: the skill's Step 2.5 text and the absence of a Step 2.5 row in scripts/gate_liveness_ledger.json.
- assume the pytest suite runs through the venv interpreter with the bare python3 fallback; basis: the execution precedent in docs/history/plans/2026-10-07-done-readiness-closeout-boundary.md (184 passed through $HOME/.agents/venvs/ai-playbook-test/bin/python3).
- assume the helper inventory is exactly the name set `scripts/runtime-scripts.list` admits, because that manifest is the repo's own deployed-home record and its admission criterion (a name the maintenance, execute-plan, or done skills resolve from the deployed home copy) is the done-flow boundary this plan prices; the carrier reads the manifest at run time, so inventory completeness is structural rather than an enumeration that can go stale; the manifest's content lags its own criterion today, so the plan joins the missing done-flow names through the manifest header's documented one-line mechanism rather than embedding a competing list in the carrier; basis: scripts/runtime-scripts.list header, the r2 review findings F13/F21, and the reconciliation record.

Decision points requiring a grill: none remain.

## Standing constraints

- The runtime home is the deployment destination only: no task or script mode copies anything from the runtime home into the canonical repo.
- The drift advisory never gates: the check mode prints findings and always exits 0; deploy mode's only non-zero exits are the named no-canonical-repo and no-manifest refusals, which no closeout boundary treats as a gate finding (the skill's remedy posture points at the refusal as the recovery instruction).

## Gist & Examples

TLDR: One sanctioned recovery command and a boundary-start drift advisory replace the done skill's scattered stale-deployment recipes, cutting the witnessed multi-round drift recovery to one step (simplicity + efficiency).

**Before (today):** A consumer closeout hits a stale deployed dirt-regression gate copy that flags a valid edit as a dirt regression. The skill recognizes this class at four places (the Step 0 lib signature, the doc-registry gate bullet, the plan-readiness deployment-gap remedy, the Step 6 stale-finalizer triage), each carrying its own inline remedy: a prose redeploy recipe here, a single-file cp there, a seven-file copy list with a symlink warning elsewhere. Recovery means working out which recipe applies to the failure at hand, hand-running it, and re-deriving which of the possibly-stale helpers the failed gate actually used; the witnessed incident took multiple recovery rounds. Nothing checks helper freshness before the gates run, so drift is discovered mid-closeout at maximum cost.

**After (this plan):** The same failure names one remedy: run `bash scripts/deploy_runtime_helpers.sh` (the carrier resolves the canonical repo through its chain: explicit `--repo`, or the invocation repo itself when it carries `scripts/runtime-scripts.list`, or the facts `skills_repo_path` key for consumer closeouts). For every name the deployed-home manifest (`scripts/runtime-scripts.list`) admits, the carrier verifies the runtime-home entry against the canonical counterpart: a missing entry is linked fresh, a lagging regular-file copy is moved aside to a `.bak-<date>` sibling and replaced by a symlink to the canonical file, and a correctly linked entry is reported current. Because the deployed name becomes a symlink to the canonical file, the deployed resolution stops lagging its source for every name the manifest admits, which closes the witnessed drift class structurally rather than by repeated manual repair. Step 0 also runs the `--check` mode once after the lock: stale or missing helpers print as advisory lines naming the same remedy, and the closeout continues; a stale helper named before its gate runs costs one command instead of a mid-closeout recovery round. The four recognition sites keep their recognition value and point at the one canonical remedy.

**Evaluated and rejected (the removal candidate the origin requires on the record):** removing the done-specific gate and recovery mechanics as a whole was priced against the guard liveness ledger and rejected: the stack holds 11 recorded catches against 14 incidents, and the catch rows name harms that would reopen with the stack gone (a stale-base branch whose landing would have deleted four peer paths; a hand-expanded fabricated digest; a corrupted inherited supersession link; foreign peer stubs preserved uncompleted). The incident rows concentrate in mechanisms whose fixes already landed (run-manifest-writer: four incidents, each remediated by a landed fix; post-landing-staging: the residue classes now carry the indeterminate-under-lock and owned-path arms). Per-mechanism narrowing candidates were evaluated the same way: the revert-set three-arm resolution, the claim-or-foreign preflight, and the two-phase sweep-gate pair keep their current shapes; Step 2.5 keeps its explicit all-files scope (Assumptions above). The one unpriced duplication the evidence does pay for is the remedy-prose sprawl this plan consolidates.

Edge cases: a runtime where no canonical arm resolves (no `--repo`, no resolvable `skills_repo_path`, and the invocation repo is not the skills repo) makes check mode print its skipped-arms advisory line and deploy mode refuse with `OUTCOME: tool_error` and exit 3; a canonical repo that resolves but carries no `scripts/runtime-scripts.list` takes the same refusal posture (no inventory source, no sync); a manifest name missing from the canonical repo is skipped with a skip line, never fabricated; a manifest entry carrying a `scripts/` path prefix maps to the runtime-home basename, because the runtime home is flat; a `.bak-<date>` sibling from an earlier sync is replaced by the newer sibling, never the live entry.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the carrier's deploy mode converts a lagging regular-file copy with a `.bak-<date>` aside into a symlink to the canonical file, links a missing name fresh, leaves a correct symlink current, and refuses with `OUTCOME: tool_error` when no canonical arm resolves or the resolved canonical carries no manifest; the check mode reports stale, missing, and skipped-arms anomalies and stays silent on current entries, always exiting 0.
- regression safety: the pins suite passes; the em-dash touched scan and the public hygiene scan pass; the removed inline recipes read zero and the canonical paragraph's anchors read exactly once (the eq-0 and eq-N span gates prove precisely this and nothing more).
- scope discipline: no gate, ledger, protocol, or review step is added; the advisory never influences an exit code; the four recognition sites keep their recognition sentences.

**Done when:**
- `( cd "$REPO" && "$TEST_PY" -m pytest scripts/test_deploy_runtime_helpers.py -q )` exits 0.
- `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )` exits 0.
- Every span check in `## Validation Commands` holds on the executed tree.

**Ship when:**
- The next closeout that hits the stale-deployment class recovers through the carrier script in one step, and a pre-closeout check names drifted helpers before their gates run; the plan's own execution deploys the carrier and its joined names (Task 2's deployment step), so both conditions follow from the executed tree.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/deploy_runtime_helpers.sh` *(new)*
- `scripts/runtime-scripts.list` (one-line additions only: the manifest join below; every other edit out of scope)
- `agents/skills/done/SKILL.md` (only the four stale-deployment remedy sites and the advisory duty inside the Step 0 canonical paragraph; all other spans frozen)

**Tests:**
- `scripts/test_deploy_runtime_helpers.py` *(new)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/done_sweep_gates.sh` and `scripts/done_sweep_gates_lib.py`; reason: the advisory rides the skill's Step 0 prose and the carrier script, not the sweep runner, and the entry prices no runner change.
- `agents/skills/execute-plan/SKILL.md` and every other skill's deployment conventions; reason: the origin scopes the review to the done closeout.
- `scripts/gate_liveness_ledger.py` and its JSON; reason: the read side and candidate machinery are the completed guard-liveness plan's deliverables and this plan only reads them as input.

## Validation Commands

Authoring-time evidence (rule 29 pre-round): the plan bytes passed the pre-round gate with exit 0 and `OUTCOME: pass` (one pre-round failure fixed before round 1: four Commit checklist lines lacked their classification tags; the tagged bytes re-ran clean); the em-dash fixer reported 0 substitutions and the touched scan exited 0; the hygiene scan answered `OUTCOME: pass`; the rule 19 RED-today probes ran each pinned span with grep against agents/skills/done/SKILL.md at the base tip: the five new-duty spans returned 0 (heading to 4 carrier mentions, 1 canonical-remedy anchor, 1 advisory anchor, 3 recipe pointers, 1 posture anchor), the three removed-literal spans returned 1 each (heading to 0), and the preserved bak-aside span returned exactly 1; the rule 22 mechanical audit verified every pinned span occurs in its owning prescribed snippet in this plan and `bash -n` accepted the extracted Validation Commands block. Round-start state for r1: authoring worktree ai-playbook-wt-dccs, branch 2026-10-07-done-closeout-cost-scope, base main 9df16f4b, plan bytes committed at 54cfb2dc (digest e2060a8e6a32a15f4b6834d63ff1e4128e5b2aa204a694953a7050123ff51789). Post-fold state (r1 fold, five blocking plus accepted non-blocking findings): the canonical-root chain, the manifest-derived inventory with symlink conversion, the Evidence blocks, the `set -euo pipefail` line, the recipe self-declaration, the Terms entries, and the criterion reword below are the folded bytes; the fold commit re-derived every count surface listed in this preamble and the r2 round-start line records its digest. Round-start state for r2: plan bytes at commit fffa1b40 (digest 0e310ea0ed4aaf7ea76641effde3b164a7f09c9577c853b4a25638924cb404c6); r2 staged 14 findings (6 blocking), all routed through the rule 13 reconciliation (docs/history/reviews/2026-10-07-plan-review-done-closeout-cost-and-skill-scope-reconciliation.md). Round-start state for r3: plan bytes at commit ede721f6 (digest 1daa2aa0a89a0e1b1e21487e3bad8e3f45f24572b5c5f30428274d918ff59cd4); r3 staged 6 findings (2 blocking), whose design-reflection fold (the resolution-chain reorder and the canonical-only manifest source, adopted under the reconciliation skill's gate) produced the bytes this preamble's r4 line anchors.

```bash
set -euo pipefail
REPO="$(git rev-parse --show-toplevel)"
TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"
[ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"
( cd "$REPO" && bash -n scripts/deploy_runtime_helpers.sh )
( cd "$REPO" && "$TEST_PY" -m pytest scripts/test_deploy_runtime_helpers.py -q )
( cd "$REPO" && grep -qF 'runtime-scripts.list' scripts/deploy_runtime_helpers.sh )
( cd "$REPO" && for name in dirt_regression_gate.py doc_registry_validator.py revert_set_classifier.py validate_review_staging.py facts_paths.py corrections_record.py plan_delta_classifier.py code_delta_classifier.py fix_plan_em_dashes.py scan-public-hygiene.sh check_backlog_inbox_location.py check_cleanup_scope_baseline.py deploy_runtime_helpers.sh test_deploy_runtime_helpers.py; do grep -qxF "$name" scripts/runtime-scripts.list || { echo "manifest misses joined helper: $name"; exit 1; } done )
( cd "$REPO" && test "$(grep -oF 'scripts/deploy_runtime_helpers.sh' agents/skills/done/SKILL.md | wc -l | tr -d ' ')" -eq 4 )
( cd "$REPO" && test "$(grep -cF 'The Step 0 stale-deployment recipe' agents/skills/done/SKILL.md)" -eq 1 )
( cd "$REPO" && test "$(grep -cF 'Runtime-helper drift advisory' agents/skills/done/SKILL.md)" -eq 1 )
( cd "$REPO" && test "$(grep -cF 'via the Step 0 stale-deployment recipe' agents/skills/done/SKILL.md)" -eq 3 )
( cd "$REPO" && test "$(grep -cF 'moving each live copy aside to a `.bak-<date>` sibling' agents/skills/done/SKILL.md)" -eq 1 )
( cd "$REPO" && test "$(grep -cF 'the rearm-on-touch posture' agents/skills/done/SKILL.md)" -eq 1 )
( cd "$REPO" && test "$(grep -cF 'cp scripts/doc_registry_validator.py' agents/skills/done/SKILL.md)" -eq 0 )
( cd "$REPO" && test "$(grep -cF 'copy all seven' agents/skills/done/SKILL.md)" -eq 0 )
( cd "$REPO" && test "$(grep -cF 'refresh the deployed `done_sweep_gates_lib.py`' agents/skills/done/SKILL.md)" -eq 0 )
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )
( cd "$REPO" && bash scripts/check-no-em-dash.sh touched )
( cd "$REPO" && bash "${PUBLIC_HYGIENE_SCAN:-$HOME/.ai-playbook/scripts/scan-public-hygiene.sh}" )
( cd "$REPO" && bash scripts/check-instruction-size.sh gate )
```

### Task 1: Pin the carrier contract (RED fixtures)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_deploy_runtime_helpers.py` *(new)*

Evidence:
- `( cd "$REPO" && "$TEST_PY" -m pytest scripts/test_deploy_runtime_helpers.py -q )`; covers the carrier-contract criteria (manifest-driven inventory, deploy conversion with bak-aside and symlink placement, facts-arm canonical resolution, the no-canonical and no-manifest refusal arms, prefixed-entry mapping, check-mode report and exit 0, destination discipline, missing-canonical skip)

- [x] `DeployRuntimeHelpersTest#test_deploy_syncs_manifest_names_with_bak_aside_and_symlink`; given a temp canonical repo holding current bytes for names admitted by a temp manifest and a temp runtime home holding an outdated regular-file copy of one admitted name, expects deploy mode to move the outdated copy aside to a `.bak-<date>` sibling, place a symlink to the canonical file at the runtime-home name, print a final `OUTCOME: pass` line, and exit 0 [class: REPOSITORY_TEST]
- [x] `DeployRuntimeHelpersTest#test_deploy_links_missing_name_and_leaves_correct_symlink_current`; given an admitted name absent from the runtime home and another already symlinked to its canonical file, expects deploy mode to link the first and report the second current without touching it [class: REPOSITORY_TEST]
- [x] `DeployRuntimeHelpersTest#test_check_reports_stale_missing_current_and_exits_zero`; given a runtime home with one lagging regular-file copy, one missing name, and one correct symlink against a canonical repo admitting all three, expects check mode to print exactly one stale line and one missing line (each naming the name and the deploy remedy), no line for the current entry, a final `OUTCOME: pass` line, and exit 0 [class: REPOSITORY_TEST]
- [x] `DeployRuntimeHelpersTest#test_consumer_environment_resolves_canonical_from_facts`; given a stub user facts document carrying `skills_repo_path` pointed at the temp canonical repo, no `--repo` flag, and a non-skills working directory, expects both modes to resolve the canonical repo through the facts arm and sync or report against it [class: REPOSITORY_TEST]
- [x] `DeployRuntimeHelpersTest#test_skills_repo_invocation_resolves_canonical_to_invocation_repo`; given a working directory inside a temp skills-repo-shaped checkout whose toplevel carries `scripts/runtime-scripts.list`, no `--repo`, and a facts document that misses or points elsewhere, expects both modes to resolve the canonical repo to the invocation checkout and sync or report against it (the pre-landing worktree self-deployment case) [class: REPOSITORY_TEST]
- [x] `DeployRuntimeHelpersTest#test_unresolvable_canonical_refuses_deploy_and_reports_check`; given no `--repo`, an unresolvable facts document, and a non-skills working directory (and, as a second arm, a canonical repo that resolves but carries no `scripts/runtime-scripts.list`), expects deploy mode to end `OUTCOME: tool_error` with exit 3 and a named error in both arms, and check mode to print a skipped-arms advisory line and exit 0 [class: REPOSITORY_TEST]
- [x] `DeployRuntimeHelpersTest#test_prefixed_manifest_entry_maps_to_basename_and_stale_variants_flip`; given a temp manifest admitting one `scripts/`-prefixed name, one name whose runtime-home symlink aims elsewhere, and one with a pre-existing colliding `.bak-<date>` sibling, expects deploy mode to link the prefixed name at its runtime-home basename, move the aimed-elsewhere symlink aside, and replace the colliding sibling with the newer one [class: REPOSITORY_TEST]
- [x] `DeployRuntimeHelpersTest#test_never_writes_into_the_canonical_repo`; given a canonical repo and a runtime home in either mode, expects every canonical-repo path to stay byte-identical after the run (destination discipline) [class: REPOSITORY_TEST]
- [x] `DeployRuntimeHelpersTest#test_missing_canonical_name_is_skipped_not_fabricated`; given a manifest-admitted name absent from the canonical repo, expects check mode to print a skip line and deploy mode to skip the entry without creating any file for it, still exiting 0 with `OUTCOME: pass` [class: REPOSITORY_TEST]
- [x] Run → expect RED: `( cd "$REPO" && "$TEST_PY" -m pytest scripts/test_deploy_runtime_helpers.py -q )` (every test fails: the carrier script does not exist yet, so each subprocess invocation errors) [class: REPOSITORY_TEST]
- [x] Commit: `test: pin the runtime-helper deployment carrier contract` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Implement the carrier script (GREEN)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/deploy_runtime_helpers.sh` *(new)*
- `scripts/runtime-scripts.list` (one-line additions only)

Evidence:
- `( cd "$REPO" && "$TEST_PY" -m pytest scripts/test_deploy_runtime_helpers.py -q )`; covers every Task 1 fixture turning GREEN against the implemented contract
- `( cd "$REPO" && bash -n scripts/deploy_runtime_helpers.sh )`; covers the script-syntax criterion
- the manifest-completeness loop of `## Validation Commands`; covers the join criterion (every joined name admitted)

- [x] Write `scripts/deploy_runtime_helpers.sh`: `--check` (report-only) and deploy (default) modes; canonical-repo resolution through the ordered chain `--repo DIR`, then the invocation repo's toplevel when it carries `scripts/runtime-scripts.list`, then the user facts `skills_repo_path` key (resolved from the facts document at `$HOME/.ai-playbook/facts.md` unless the `--facts PATH` override names another); when no arm resolves, or the resolved canonical carries no `scripts/runtime-scripts.list`, deploy mode ends `OUTCOME: tool_error` with exit 3 and a named error while check mode prints a skipped-arms advisory line and exits 0; `--home DIR` (runtime scripts directory, default `$HOME/.ai-playbook/scripts`) so tests never touch the real home; the helper inventory read at run time from the resolved canonical repo's `scripts/runtime-scripts.list` (one manifest source, no second resolution); a manifest entry carrying a `scripts/` path prefix maps to the runtime-home basename (the runtime home is flat); per admitted name: canonical missing prints a skip line and creates nothing; the runtime-home name absent is linked fresh to the canonical file; the name already a symlink resolving to the canonical file prints a current line and is left untouched; a regular-file copy or a symlink aimed elsewhere is moved aside to `.bak-<UTC date>` and replaced by a symlink to the canonical file (the conversion class the manifest's own header documents); check mode runs the same walk report-only: every anomaly prints one advisory line naming the deploy remedy; check mode always ends `OUTCOME: pass` and exit 0; deploy mode ends `OUTCOME: pass` and exit 0 except the refusals above; nothing ever writes under the canonical repo [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `( cd "$REPO" && "$TEST_PY" -m pytest scripts/test_deploy_runtime_helpers.py -q )` [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `( cd "$REPO" && bash -n scripts/deploy_runtime_helpers.sh )` [class: REPOSITORY_TEST]
- [x] Join the missing done-flow names to `scripts/runtime-scripts.list`, one line per name per the manifest header's documented mechanism: at minimum every name in the Validation block's manifest-completeness loop (`dirt_regression_gate.py`, `doc_registry_validator.py`, `revert_set_classifier.py`, `validate_review_staging.py`, `facts_paths.py`, `corrections_record.py`, `plan_delta_classifier.py`, `code_delta_classifier.py`, `fix_plan_em_dashes.py`, `scan-public-hygiene.sh`, `check_backlog_inbox_location.py`, `check_cleanup_scope_baseline.py`, `deploy_runtime_helpers.sh`, `test_deploy_runtime_helpers.py`), plus every other name the done skill's resolution conventions name that a `grep -qxF` over the manifest shows missing; names already admitted are skipped [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the manifest-completeness loop line of `## Validation Commands` (every joined name now admitted) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `( cd "$REPO" && bash scripts/deploy_runtime_helpers.sh )` against the real runtime home with no flags (the invocation-repo arm resolves this checkout: its toplevel carries the joined manifest and the new carrier), then `( cd "$REPO" && bash scripts/deploy_runtime_helpers.sh --check )`, recording the observed lines in the task log, so the carrier and its joined names are deployed by this plan's own execution [class: REPOSITORY_TEST]
- [x] Commit: `feat: one sanctioned runtime-helper deployment carrier` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Consolidate the stale-deployment remedies in the done skill

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/done/SKILL.md` (four sites; every other span frozen)

Evidence:
- `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )`; covers the pins-unchanged criterion
- the span-count lines of `## Validation Commands`; covers the consolidation criteria (4 carrier mentions, 1 recipe self-declaration, 1 advisory anchor, 3 recipe pointers, 1 preserved bak-aside span, 1 posture anchor, 0 removed literals)

Apply four byte-precise replacements. Site 1, the Step 0 paragraph titled `**Stale-deployment signature (Step 0 lib):**`: keep the opening recognition sentence through `not a lib defect to investigate`, then replace everything after it with: `; never route this signature to the investigate path or the recorded-stop exception. The Step 0 stale-deployment recipe (the canonical remedy for every stale deployment in this skill: this signature, the doc-registry and plan-readiness gate signatures below, the manifest disposition and recovery stale signatures, and the Step 6 stale-finalizer triage) is one command: run `bash scripts/deploy_runtime_helpers.sh` (resolve the script repo-local first, then the deployed home copy), which syncs every name the deployed-home manifest (`scripts/runtime-scripts.list`) admits against the resolved canonical repo, moving each live copy aside to a `.bak-<date>` sibling and replacing it with a symlink to the canonical file so the deployed resolution can no longer lag its source, then re-run the failed boundary; the runtime home stays the deployment destination, never the source. **Runtime-helper drift advisory:** once per run after the lock, run the same script in check mode (`--check`): each stale or missing helper prints one advisory line naming the same remedy; the advisory is echo-and-continue (the rearm-on-touch posture), never gates, and never blocks the closeout.` Site 2, the pre-docs doc-registry bullet: replace the sentence from `**Stale-deployment signature:**` through `until redeploy);` with: `**Stale-deployment signature:** a doc-registry failure printing `invalid state value` on a state value the repo-copy validator accepts is a stale runtime-home validator, not a registry defect: redeploy via the Step 0 stale-deployment recipe (`scripts/deploy_runtime_helpers.sh`; the manifest-derived inventory includes `doc_registry_validator.py`, and the redeploy also covers the silent direction, a pre-fix deployed copy lacking the rejected-archive immutability and licensed-transition coverage) and re-run the gate;` Site 3, the pre-docs plan-readiness bullet's manual-remedy sentence: replace from `Manual remedy:` through `is NOT covered by that copy remedy: investigate the validator before re-running the gate.` with: `Manual remedy: redeploy via the Step 0 stale-deployment recipe (`scripts/deploy_runtime_helpers.sh`); the manifest-derived inventory carries the validator and its six sibling modules (`plan_readiness.py`, `validate_review_staging.py`, `facts_paths.py`, `corrections_record.py`, `plan_delta_classifier.py`, `code_delta_classifier.py`, `fix_plan_em_dashes.py`), and a deployed `facts_paths.py` symlink stays a symlink under the carrier's sync; any other non-zero exit that prints no `readiness FAILED:` line is not covered by that remedy: investigate the validator before re-running the gate.` Site 4, the Step 6 stale-finalizer triage paragraph: replace the parenthetical `(refresh the deployed `done_sweep_gates_lib.py` from the repo-local `scripts/` copy, the copy the Step 0 `$LIB` resolution prefers)` with: `(via the Step 0 stale-deployment recipe, `scripts/deploy_runtime_helpers.sh`)`.

- [x] Apply the four site replacements byte-precisely per the prescription above [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )` (no pinned literal sits inside the four edited spans; verified by grep at authoring time) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the span-count lines of `## Validation Commands` (4 carrier mentions, 1 recipe self-declaration, 1 advisory anchor, 3 recipe pointers, 1 preserved bak-aside span, 1 posture anchor, 0 removed literals) [class: REPOSITORY_TEST]
- [x] Commit: `docs: consolidate stale-deployment remedies onto one carrier` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Full validation and drift-advisory proof

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- none (validation-only task)

- [x] Run the complete `## Validation Commands` block → expect exit 0 on the executed tree [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `( cd "$REPO" && bash scripts/deploy_runtime_helpers.sh --check )` against the real runtime home with no flags (the canonical arm resolves through the invocation checkout, which carries the manifest pre-landing and post-landing alike), recording the observed advisory lines (empty or not) in the task log; then rebuild the check-mode fixture from Task 1 and confirm a deliberately lagged regular-file copy flips a stale line, proving the advisory reports drift today [class: REPOSITORY_TEST]
- [x] Commit: `test: full validation for the done closeout drift carrier` [class: IMPLEMENTATION_REQUIRED]
