# Plan: Record-commit preflight and branch-side certification checkpoint

Backlog origins (scope of record):
- docs/history/backlog/2026-11-19-stale-capture-record-commit-peer-clobber.md
- docs/history/backlog/2026-11-19-certification-checkpoint-main-placement-add-add-conflicts.md

Driving force: code-quality + simplicity
Plan review record: the staging series .ai-playbook/reviews/2026-11-19-plan-review-stale-capture-record-commit-peer-clobber-p*-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1.5h total, largest task 0.5h
Executed: yes (this landing 4b0e40d9d1899df1656c57ae07db4f571288e8e4)
Authoring claim: 2026-11-19-stale-capture-record-commit-peer-clobber.md (session sess_ea912330-5def-4fd4-a20a-41ab0e699907)

## Terms

- Certification-time checkpoint: the round-close duty committing certified plan bytes (the `Certification-time checkpoint (record durability)` clause in `agents/skills/plans/plan-quality-gate.md`); today one base-branch commit to the primary plans root, re-homed branch-side by Task 3.
- wip checkpoint: the existing duty committing the plan file on the authoring branch at every authored write (`agents/skills/plans/phase-0-placement.md`, Authoring checkpoint duty).
- Branch-side checkpoint: the re-homed certification-time checkpoint committing certified bytes on the run's authoring branch beside the wip checkpoints.
- Owned-staged-set preflight: the verified-index discipline binding before a record commit composes: enumerate the staged set, word-diff each staged entry against the writer's own intended hunks, stop on any foreign staged entry for reconciliation instead of riding it into history; primary-checkout record commits run it under the primary done lock with the Standing rules' ref/OID pair verification, and the branch-side checkpoint runs it over the composing worktree's own staged set.
- Standing rules' guard: the `Write boundary rule` in `docs/history/backlog/PLAN-PROMPTS.md` (ref/OID pair verification under the primary done lock, foreign staged delta refused), the log-write class's canonical guard home.
- Record-commit class: commits publishing record state (the certification checkpoint, seal-landing diagnostics appends, backlog-row flips) outside the rolling-log write and landing classes; after Task 3 the checkpoint composes on the authoring branch, and its remaining primary-checkout members (seal-landing diagnostics appends, backlog-row flips) stay outside this plan's preflight binding (see follow-up disposition).
- Receipt-bearing log path: `docs/history/backlog/PLAN-PROMPTS.md` and `docs/history/backlog/EXEC-PROMPTS.md`, whose prune receipts are durable landing witnesses.
- Union-of-intents: the landing conflict discipline resolving every conflict block by merging intents line-by-line, never taking one side (`agents/skills/execute-plan/worktree-first.md`, lifecycle step 4).
- Archive twin: `docs/history/plans/completed/2026-11-13-handoff-reconciler-dead-drift-mappings.md`, the executed record of landing `4f7a36be8` (canonical bytes blob `e1329819` in that tree).
- Open row: `docs/history/backlog/2026-11-18-completed-plan-evidence-series-criterion.md`, the executed landing's Phase 3 row.
- Dead-run residue: the stranded staged delta the dead manifest `20261119T004829Z` left in the shared primary checkout; disposed 2026-11-19 per the operator-reconciliation doctrine.
- Bounded mechanical rebase duty: the landing step's base-churn recovery (`agents/skills/execute-plan/worktree-first.md`), unchanged by this plan.
- Machinery admission protocol: the repository guidelines' admission procedure for gate-like machinery (warning-only first, promotion only after a second true catch, sunset review).
- Gate liveness ledger: `scripts/gate_liveness_ledger.json`, the per-gate incident and catch register.
- Pinned-resolution rule: the landing rebase pins plan-file conflict resolution to the certified checkpoint bytes; recorded in this plan as the priced fallback (Task 3), never landed skill text.

## Why

A shared-checkout record commit composed over an unverified index once published a dead peer run's half-done finalize as history (`e7c281cdf`), and the certification-time checkpoint's main-side placement structurally guarantees a landing-time add/add conflict against the branch's own draft, paid by three of three window landings with one near-clobber of a peer's landed prune receipt. The record-commit class lacks the verified-index discipline the neighboring classes already carry, and the checkpoint's durability does not need the conflict-prone placement.

## Gist & Examples

TLDR: the certification checkpoint gains an owned-staged-set preflight and moves branch-side, so its commits can no longer publish a dead peer's residue from a shared index and landings stop paying a structural add/add against their own checkpoint (code-quality + simplicity).

Before: the certification checkpoint commits certified plan bytes to the primary plans root on the base branch while the authoring branch continues from its pre-checkpoint base; every authoring landing then rebases into an add/add against the branch's own draft, resolved per session (one window landing ran an 8-iteration pinned-resolution loop, and one resolution nearly took a whole-file side on `PLAN-PROMPTS.md` that would have clobbered a peer's landed prune receipt). After: the checkpoint commits on the authoring branch, the landing carries no base-side copy of the plan bytes at a divergent base, and the structural conflict class is gone.

Before: a primary-checkout record commit composes over whatever the shared index holds; the corrupting commit `e7c281cdf` swept a dead peer's stranded staged delta into main's history, leaving the executed plan's record wrong for hours (living path `Executed: no`, twin and row untracked, three diagnostic appends stranded). After: the checkpoint runs the owned-staged-set preflight (word-diffing the composing checkout's staged set against its own hunks) and stops on foreign state for reconciliation; the repaired record state (operator migration `9d098910c`, repair commit `c17e44b55`) stays verified by the Task 1 probes.

Edge cases: the preflight is warning-only first (report and park for reconciliation, never autonomous unstage or discard of foreign bytes; D-19 keeps owning log-path residue direction); a checkout whose staged set holds only the writer's own hunks composes normally; the exclusion clause never weakens the union-of-intents discipline for ordinary paths.

## Outcome

The certification checkpoint composes only from a verified index, and landings stop paying the checkpoint-imposed conflict cost.

- The certification checkpoint's certified bytes live on the authoring branch, equally durable against worktree loss, with no main-side duplicate at a divergent base.
- The checkpoint commit carries the owned-staged-set preflight by reference to the Standing rules' guard, warning-only first with its admission fields pinned.
- The executed handoff-reconciler record state stays verified repaired; the Task 1 probes double as the regression guard.
- Receipt-bearing log paths are excluded from whole-file conflict resolutions during landings, removing the near-clobber judgment class.

Gate delta: adds one warning-only prose duty, the owned-staged-set preflight bound to the certification checkpoint (the record-commit class's remaining primary-checkout members stay an explicit follow-up below; priced by the completed-integrity-failure witness `e7c281cdf` and the admission fields in `docs/history/backlog/2026-11-19-stale-capture-record-commit-peer-clobber.md`, sunset 2026-12-19; the gate liveness ledger at authoring shows no row yet for this class and `archive-ceremony catches=1 incidents=2`); adds one whole-file-resolution exclusion for receipt-bearing log paths (priced by the witnessed near-clobber in `docs/history/backlog/2026-11-19-certification-checkpoint-main-placement-add-add-conflicts.md`); removes one refusal class, the authoring landing's checkpoint-imposed stale-base reconciliation with its plan-file resolution pin, obsolete under the branch-side checkpoint; no new gate, validator, lock, ledger, or script.

Follow-up disposition: preflight promotion from warning-only to blocking routes through the Machinery admission protocol after a second true catch, reviewed at the pinned sunset 2026-11-19 plus one month (2026-12-19), no new row; a Task 1 probe leg that regresses and cannot be repaired in-run files a durable backlog row naming the leg; the three-surface single-homing of the existing check-carriers' texts is priced here and deliberately scoped out, landing only with its own witnessed trigger; the record-commit class's remaining primary-checkout members (seal-landing diagnostics appends, backlog-row flips) stay unpreflighted here because their owning texts sit outside the two named files, and binding them is the recorded follow-up on the same Machinery admission protocol path when their witness arrives; each rejected disposition carries its ruling evidence in this section.

## Assumptions

- assume the repair arm (origin row 1 scope arm 1) is already executed and stays verification-only in this plan; basis: the origin row's 2026-11-19 ~15:20Z repair-progress witness (commit `c17e44b55`), the operator-directed migration `9d098910c`, and the authoring-time probes (living path absent from main's tree, completed twin tracked with `Executed: yes (0f19aee5feda647db428d9efd0910cf9a5832913)`, open row tracked open, diagnostics committed, `git status --porcelain -- docs/history` empty); simpler-design comparison recorded: re-executing the repair legs was rejected because the record state is already correct on main and a second repair pass risks the exact peer-clobber class the row names.
- assume the preflight lands as duty text by reference to the Standing rules' guard, never as a script or blocking gate; basis: origin row 1 Suggested direction ("by reference to the Standing rules' existing log-write guard rather than a new mechanism"), the Machinery admission protocol (warning-only first, no second true catch), and the repository's skill-text anti-growth rules; simpler-design comparison recorded: a scripts/ helper was rejected as a new mechanism the row does not ask for.
- assume the landed placement arm is the branch-side checkpoint and the pinned-resolution rule stays the recorded fallback rather than landed skill text; basis: the dispatch entry's Prompt ("the placement decision with the pinned-resolution rule as the priced fallback") and scope arm ("land the smallest arm that removes the structural add/add cost"), and origin row 2's Expected (branch-side equally durable against worktree loss, no main-side duplicate at a divergent base); simpler-design comparison recorded: the pinned-resolution rule bounds per-conflict resolution cost but leaves the structural conflict and its stale-base reconciliation in place, which the entry's wording does not accept as done.
- assume the receipt-bearing-path exclusion lands alongside the re-home because the near-clobber class is placement-independent (peer prune receipts land on the base branch under every lane); basis: origin row 2's Expected second clause and the entry's requirement that the placement arm name what it removes (the per-session judgment that nearly clobbered a peer prune receipt).
- assume the three existing check-carriers (the Standing rules' log-write guard, the learn commit rule's own-edit word-diff check, the landing machinery's staged-state snapshot refusal) stay byte-intact; basis: origin row 1 Expected final clause ("name one shared preflight rather than three private copies") read against the anti-growth rules; the new clause satisfies the naming intent by referencing the shared guard, and a three-surface text consolidation needs its own witnessed trigger.
- assume D-19 (`docs/maintenance/operator-directives.md`) and the sibling row `docs/history/backlog/2026-11-19-authoring-freeze-checkout-state-refusal-no-decay-arm.md` stay untouched; basis: origin row 1's group roster ("this prompt consumes them as context, not as origins").
Decision points requiring a grill: none remain.

## Standing constraints

- Pinned spans verified by `scripts/check_maintenance_pins.sh` stay byte-intact; no pin row over the changed files may regress, and the suite's single baseline-listed pre-existing red (`PIN FAIL: FINAL STEP prefix count`) is recorded in the Validation preamble and stays outside this plan's scope.
- No script, gate, validator, lock, or ledger is added; the preflight is duty text with warning-only semantics: report and park for reconciliation, never autonomously unstage or discard foreign bytes.
- D-19's operator-direction pre-give for log-path residue stays the sanctioned remedy on log paths; the preflight never invents a decay or self-repair arm for foreign state.
- The checkpoint's record-durability purpose stands: certified bytes survive worktree loss; a branch ref survives worktree removal, satisfying that purpose.
- Skill-text and record-file changes only; no production code and no test suites are touched; the facts policy `test_suite_policy = "focused-never-full"` applies and no suite run is required by this plan.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every Task 1 probe matches its expected repaired state; any mismatch repairs in-run with canonical bytes or files the residual row.
- guard fidelity: the preflight text names the shared guard vocabulary (ref/OID pair under the done lock for primary-checkout record commits, word-diff against own hunks in the composing checkout, foreign-entry stop) without introducing a new mechanism; the placement rewrite preserves the durability purpose.
- text integrity: the pins suite, the byte-budget gate, the em-dash gate, and the hygiene scan pass over the changed files.
- regression: no skill text outside the two named files changes; the union-of-intents discipline's clauses outside step 4's receipt-path exclusion amendment stay byte-intact (the Primary-checkout landing restatement inherits the exclusion through its own the-same-discipline lead-in and is not edited).

**Done when:**
- The Task 1 probes are recorded green in the task log (or the regressed leg is repaired in-run or filed as a residual row).
- `agents/skills/plans/plan-quality-gate.md` carries the amended checkpoint clause: the owned-staged-set preflight bound before composition and the checkpoint committed on the authoring branch, with the base-branch commit placement and the stale-base reconciliation sentence removed.
- `agents/skills/execute-plan/worktree-first.md` step 4 carries the receipt-bearing-path whole-file-resolution exclusion.
- The Validation Commands block passes from the placement root.

**Ship when:**
- No external release conditions: nothing in this plan ships outside the repository; the preflight's promotion decision is the Machinery admission protocol's operator-gated review at sunset 2026-12-19 (operations follow-up, evidence owner: the maintenance survey's admission review; closure: a second true catch recorded in the gate liveness ledger).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Skill text:**
- `agents/skills/plans/plan-quality-gate.md` (Task 2)
- `agents/skills/plans/plan-quality-gate.md` (Task 3)
- `agents/skills/execute-plan/worktree-first.md` (Task 3)

**Records (conditional regression-repair targets only; each repaired only when its Task 1 probe regresses):**
- `docs/history/plans/completed/2026-11-13-handoff-reconciler-dead-drift-mappings.md` (Task 1)
- `docs/history/plans/2026-11-13-handoff-reconciler-dead-drift-mappings.md` (Task 1)
- `docs/history/backlog/2026-11-18-completed-plan-evidence-series-criterion.md` (Task 1)
- `docs/history/certification-seal-landing-diagnostics.md` (Task 1)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Documentation:** production code and tests use the explicit list. Docs may also be in scope under plan-related extension when a change is substantively required to keep docs aligned with the feature; not every path needs listing upfront. A doc-closure task should include search/grep for stale references, not only pre-listed paths.

**Out of scope; reject unless plan-related:**
- `docs/maintenance/operator-directives.md` (D-19); reason: the sibling row's surface, untouched by this plan
- the Standing rules block of `docs/history/backlog/PLAN-PROMPTS.md`, `agents/skills/learn/`, `scripts/land_squash.sh`, `scripts/done_run.sh`; reason: existing check-carriers stay byte-intact (reference-only)
- `scripts/check_maintenance_pins.sh`, `scripts/skill_text_budget.py`; reason: gates read, never edited, by this plan
- PLAN-PROMPTS.md and EXEC-PROMPTS.md entry bodies; reason: the rolling logs' own write machinery owns them

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1
git cat-file -e "refs/heads/main:docs/history/plans/2026-11-13-handoff-reconciler-dead-drift-mappings.md" 2>/dev/null && { echo "REGRESSION: living path reappeared on main"; exit 1; }
git show "refs/heads/main:docs/history/plans/completed/2026-11-13-handoff-reconciler-dead-drift-mappings.md" | grep -q 'Executed: yes (0f19aee5feda647db428d9efd0910cf9a5832913)' || { echo "REGRESSION: twin Executed line"; exit 1; }
git show "refs/heads/main:docs/history/backlog/2026-11-18-completed-plan-evidence-series-criterion.md" | grep -q 'Status:\*\* open' || { echo "REGRESSION: open row status"; exit 1; }
PRIMARY="$(git worktree list --porcelain | sed -n 's/^worktree //p' | head -1)" || exit 1
[ -n "$PRIMARY" ] || { echo "primary checkout not resolved"; exit 1; }
[ -z "$(git -C "$PRIMARY" status --porcelain -- docs/history/certification-seal-landing-diagnostics.md)" ] || { echo "REGRESSION: diagnostics dirt"; exit 1; }
[ -z "$(git -C "$PRIMARY" status --porcelain -- docs/history)" ] || { echo "REGRESSION: stranded record deltas under docs/history"; exit 1; }
for c in e7c281cdf 4f7a36be8 0c0080b10 9d098910c c17e44b55 54e4e53b7; do git rev-parse -q --verify "$c^{commit}" >/dev/null || { echo "REGRESSION: witness commit $c unreachable"; exit 1; }; done
grep -qF 'Certification-time checkpoint (record durability)' agents/skills/plans/plan-quality-gate.md || { echo "checkpoint clause missing"; exit 1; }
grep -qF 'owned-staged-set preflight' agents/skills/plans/plan-quality-gate.md || { echo "preflight clause missing"; exit 1; }
grep -qF 'receipt-bearing' agents/skills/execute-plan/worktree-first.md || { echo "exclusion clause missing"; exit 1; }
bash scripts/check_maintenance_pins.sh > "${TMPDIR:-/tmp}/pins-scan-stale-capture.out" 2>&1 || true
NEW_PINS="$(grep -E 'PIN FAIL|PIN RECORDED RED EXPIRED|PIN RECORDED RED MALFORMED' "${TMPDIR:-/tmp}/pins-scan-stale-capture.out" | grep -vxF 'PIN FAIL: FINAL STEP prefix count' || true)"
[ -z "$NEW_PINS" ] || { echo "NEW pin failure: $NEW_PINS"; exit 1; }
rm -f "${TMPDIR:-/tmp}/pins-scan-stale-capture.out"
python3 scripts/skill_text_budget.py --check || exit 1
bash scripts/check-no-em-dash.sh added-lines --base main || exit 1
bash scripts/scan-public-hygiene.sh || exit 1
```

Validation preamble (authoring-time preflight record, 2026-11-19):

- Record-state probes: all five legs measured green at authoring from the primary checkout at main tip lineage `0e523a714` (living path absent, twin `Executed: yes (0f19aee5...)`, open row open, diagnostics clean, `docs/history` clean); witness commits `e7c281cdf`, `4f7a36be8`, `0c0080b10`, `9d098910c`, `c17e44b55`, `54e4e53b7` all reachable. The two status legs resolve the primary checkout explicitly (`git worktree list`'s main worktree) because plan execution runs from the placement worktree, whose `docs/history` is clean by construction.
- Clause greps: `Certification-time checkpoint (record durability)` is GREEN today (the clause exists); `owned-staged-set preflight` and the worktree-first `receipt-bearing` exclusion are RED today and turn GREEN exactly when Tasks 2 and 3 land; the base-branch placement vocabulary check is owned by Task 3's own checklist items (the stale-reference sweep and the re-home item), not by this block.
- Pins suite: `bash scripts/check_maintenance_pins.sh` carries one pre-existing, baseline-listed, register-unrecorded red at authoring, the escalated line `PIN FAIL: FINAL STEP prefix count` (`agents/skills/maintenance/template-authoring.md` holds 0 of the expected comma'd `FINAL STEP, after the report:` prefix; witnessed unchanged through peer landings `6217512b0` and `51d5e3e29`, the latter recording the red in its own landing message; captured in the primary checkout's `.ai-playbook/maintenance/baseline-known-red-gates.json`). That line is actionable for its owning lane and stays outside this plan's scope (omit-extension); the block's pins line therefore fails only on pin reds beyond that single recorded line, and no pin row over the two changed files may regress.
- Byte-budget gate: `python3 scripts/skill_text_budget.py --check` measured `0 ceiling breach(es)` (blocking posture) at authoring; neither target file carried a cap or ratchet breach.
- Em-dash authoring-time self-check: the write-time fixer (`scripts/fix_plan_em_dashes.py`) runs in full mode over the new plan bytes before the first review round and in `--preserve-tasks` mode after every later write.
- Hygiene scan: `bash scripts/scan-public-hygiene.sh` measured pass at authoring over the worktree base.
- Block shape: the Validation Commands block passes `bash -n`; every fallible line carries `|| exit 1`, an explicit `&& { ...; exit 1; }` refusal, or a guarded `for` loop exit.

### Task 1: Executed-record state verification (regression guard)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/history/plans/completed/2026-11-13-handoff-reconciler-dead-drift-mappings.md` (conditional repair target)
- `docs/history/plans/2026-11-13-handoff-reconciler-dead-drift-mappings.md` *(deleted)* (conditional repair target; absent from the tree today because the archive rename stands; the repair arm deletes it again if a probe ever finds it restored)
- `docs/history/backlog/2026-11-18-completed-plan-evidence-series-criterion.md` (conditional repair target)
- `docs/history/certification-seal-landing-diagnostics.md` (conditional repair target)

- [x] Probe the five repaired record legs with the Validation Commands block's probe commands (living path absent from main's tree, twin `Executed: yes (0f19aee5...)`, open row open, diagnostics clean and committed, `docs/history` free of stranded deltas) and record each raw probe output in the task log [class: REPOSITORY_TEST]
- [x] Residue witness: given the dead manifest `20261119T004829Z`'s residue, expects no stranded staged or untracked record delta under `docs/history` in the primary checkout, and the corrections-writer tick mirror resolved by its landing `54e4e53b7` [class: REPOSITORY_TEST]
- [x] Conditional repair arm, canonical restore: given a probe naming a regressed leg, expects the repair to restore canonical bytes (the archive twin from `4f7a36be8`'s tree blob `e1329819`; the open row's bytes as filed at `4f7a36be8`; the diagnostics appends verbatim in append order), recorded with the probe evidence [class: IMPLEMENTATION_REQUIRED]
- [x] Conditional repair arm, composing discipline: given any repair commit in this task, expects it composed under this plan's own owned-staged-set discipline (verified staged set in the composing checkout; the done-lock and ref/OID legs when composing in the primary checkout) [class: IMPLEMENTATION_REQUIRED]
- [x] Conditional repair arm, unrepairable leg: given a leg that cannot be repaired in-run, expects a durable backlog row naming the leg filed instead of forcing the repair [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness (shared checkout): given any repair or probe in this task, expects no foreign staged delta staged, unstaged, or discarded, and no commit composed over an unverified index [class: REPOSITORY_TEST]
- [x] Run the record-state probe lines of the Validation Commands block expecting GREEN; when the repair arm fired, Commit: `docs: restore <regressed leg> record state (regression repair)`; when it did not fire, no commit is owed [class: IMPLEMENTATION_REQUIRED]

### Task 2: Owned-staged-set preflight duty text

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/plans/plan-quality-gate.md`

- [x] Preflight clause, verified-index steps: amend the checkpoint clause to bind, before composing the checkpoint commit: verify the ref/OID pair per the Standing rules' `Write boundary rule` under the primary done lock, enumerate the staged set (`git status --porcelain` plus `git diff --cached --name-status`), and word-diff each staged entry against the writer's own intended hunks [class: IMPLEMENTATION_REQUIRED]
- [x] Preflight clause, foreign-entry stop: given any foreign staged entry (including a dead peer's stranded D/R state) at composition time, expects the amended clause to stop the commit: report the entry and park for reconciliation, never ride it into history [class: IMPLEMENTATION_REQUIRED]
- [x] Warning-only posture and admission fields: the clause states the preflight's warning-first semantics (report and park, never autonomous unstage or discard of foreign bytes; D-19 keeps owning log-path residue direction) and its admission fields (incident `e7c281cdf`; rare-per-commit catch with high harm; false-positive cost one re-derivation turn; sunset 2026-12-19; promotion per the Machinery admission protocol after a second true catch) [class: IMPLEMENTATION_REQUIRED]
- [x] Single-home naming: the clause names the Standing rules' `Write boundary rule` as the shared verified-index guard and notes the classes already carrying legs of it (rolling-log writes, learn commits, landing snapshot refusals) without rewriting those texts [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness (foreign bytes): given a clause draft that would unstage, discard, or auto-resolve foreign staged bytes, expects the draft rejected; the sanctioned remedy is report, park, and the operator-reconciliation doctrine, matching the origin row's Expected [class: REPOSITORY_TEST]
- [x] Durability invariant preserved: given the clause as amended, expects the checkpoint's record-durability purpose (certified bytes survive worktree loss) still stated verbatim in intent [class: REPOSITORY_TEST]
- [x] Run the Validation Commands block expecting the `owned-staged-set preflight` grep GREEN and the gates green; Commit: `docs: bind the owned-staged-set preflight to the checkpoint commit (warning-only)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Branch-side certification checkpoint and receipt-path resolution exclusion

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/plans/plan-quality-gate.md`
- `agents/skills/execute-plan/worktree-first.md`

- [x] Branch-side re-home: rewrite the checkpoint clause's placement so the certified plan bytes commit on the run's authoring branch beside the wip checkpoints instead of one base-branch commit to the primary plans root; the durability statement reads: certified bytes survive worktree loss through the branch ref, remain readable from the primary repo (`git show authoring/<branch>:<plan path>`), and reach the plans root at the authoring landing [class: IMPLEMENTATION_REQUIRED]
- [x] Preflight re-scope, branch-side composition: given the clause as re-homed, expects a re-scope sentence stating that with the checkpoint commit composed on the authoring branch from the worktree's own index, the clause's preflight steps run in the composing checkout's context, and the primary done lock and Standing rules' ref/OID pair legs apply only to record commits that still compose in the primary checkout [class: IMPLEMENTATION_REQUIRED]
- [x] Reconciliation rewrite, removal: remove the checkpoint clause's structural landing reconciliation (the deferred-landing stale-base refusal met by the checkpoint's own main-side bytes and the plan-file-conflicts-resolve-to-certified-bytes pin) [class: IMPLEMENTATION_REQUIRED]
- [x] Reconciliation rewrite, replacement text: state instead that with no base-side copy at a divergent base the landing carries no checkpoint-imposed add/add, peer base churn follows the bounded mechanical rebase duty, and the deciding-turn absence arm commits on the run branch under the same byte-identity rule [class: IMPLEMENTATION_REQUIRED]
- [x] Receipt-path exclusion clause: extend `agents/skills/execute-plan/worktree-first.md` step 4's conflict-content discipline: conflicts on receipt-bearing log paths (`docs/history/backlog/PLAN-PROMPTS.md`, `docs/history/backlog/EXEC-PROMPTS.md`) never resolve by a whole-file strategy (union, theirs, or ours); they resolve line-level with the receipts inventoried, and the post-resolution re-verification duty's receipt audits re-run over those paths [class: IMPLEMENTATION_REQUIRED]
- [x] Exclusion single-home: given the amended discipline, expects the clause to state that step 4's block is the canonical home for the exclusion and the Primary-checkout landing class paragraph inherits it through its own the-same-conflict-content-discipline lead-in (one shared rule, no second living copy edited) [class: IMPLEMENTATION_REQUIRED]
- [x] Fallback disposition: the pinned-resolution rule (landing rebase pins plan-file resolution to the certified checkpoint bytes) stays recorded in this plan as the priced fallback, never landed skill text; given the clause as rewritten, expects no plan-file pin vocabulary remains in the checkpoint clause (its premise is gone) [class: REPOSITORY_TEST]
- [x] Stale-reference sweep: grep the skill tree for the removed placement's vocabulary (a certification-time base-branch commit to the plans root, plan-file conflicts resolving to the certified checkpoint bytes); expects no `base-branch commit` vocabulary remains in the checkpoint clause, and update or record every other hit; pinned spans and every other clause of the two files stay byte-intact [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Validation Commands block expecting GREEN (the clause greps GREEN, the pins scan failing only on pin reds beyond the one recorded pre-existing line, the byte-budget gate, the em-dash gate, and the hygiene scan); Commit: `docs: move the certification checkpoint branch-side and exclude receipt paths from whole-file resolution` [class: IMPLEMENTATION_REQUIRED]
