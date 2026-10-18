# Plan: post-landing origin-only ancestry divergence is informational

Backlog origin: docs/history/backlog/2026-10-15-post-landing-origin-ancestry-check-refusal.md
Driving force: simplicity + code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-15-plan-review-post-landing-origin-ancestry-diagnostic-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 1.5h total, largest task 0.75h

## Terms

- origin-tracking ref: the remote-tracking ref `refs/remotes/origin/<default branch>` that `land_squash.sh` passes to every landing's post-landing check.
- origin-only divergence: the post-landing state where the default branch descends from the captured pre-landing tip but not from the origin-tracking ref.
- pre-tip leg: the post-landing ancestry check that the default branch still descends from the captured pre-landing tip; the landing-caused severance protection.
- informational note: a `note:` line reporting a condition without affecting the gate's exit code and without demanding operator action.
- origin-leg-only keep-arm: the `land_squash.sh` branch (both landing modes) that kept the landing while forwarding the gate's origin refusal and instructing origin-ref reconciliation.
- compare-and-swap (CAS): the two-value `git update-ref` that moves the default branch ref to the landing commit only while it still reads the expected base tip.
- interleaved-tip arm: the helper's post-landing recovery that rolls the default branch back to the verified base tip when a peer move interleaved with the landing.
- POST_RC: the exit code of the helper's post-landing parentage-gate invocation, routed to the pass, interleaved-tip, or tool-error arms.
- descent fact: the landing-verified proposition that the divergence predates the landing (the landing commit descends from the checked pre-landing tip, so the landing cannot have changed the origin ref's ancestry relationship).

## Why

The post-landing origin check turns a pre-existing local-versus-remote-tracking divergence into a refusal-shaped line and an operator reconciliation instruction, so every landing in a repo whose origin ref is stale looks partially failed. The landing itself is always intact in that state: the verified landing commit descends from the checked pre-landing tip, so the origin ref's ancestry relationship cannot have been changed by the landing.

## Gist & Examples

TLDR: origin-only ancestry divergence becomes a labeled informational note with exit 0 and no required follow-up, because the landing provably cannot cause it.

Before: a landing in this repository today emits `refuse: default branch no longer descends from refs/remotes/origin/main` plus "operator reconciliation: reconcile the origin ref with the landed tip before the next landing", even though the landing commit is verified to parent onto the pre-landing tip and `OUTCOME: pass` is emitted; the refusal-shaped lines read as a failed landing. The state is live: `refs/remotes/origin/main` (7c293e7be) is not an ancestor of `main`, so every landing takes this arm.

After: the same landing reports one informational note, exits 0 with no refusal-shaped text, and the helper's unreachable keep-arms are deleted. A genuinely severed default branch still refuses with exit 1 exactly as before.

## Outcome

The post-landing output unambiguously distinguishes a landing-caused severance (exit 1, pre-tip refuse line) from a pre-existing origin-tracking divergence (exit 0, informational note), and the landing tail carries no operator follow-up duty for the latter.

- The origin-only refusal class and its exit-code contribution are removed from `landing_parentage_gate.py post-landing`; the pre-tip refusal path is byte-for-byte unchanged in wording and exit code.
- The two unreachable origin-leg-only keep-arms and their reconciliation instruction are removed from both `land_squash.sh` landing modes; the pass and interleaved-tip paths keep their current routing.
- The three consumer blueprints (authoring, execution, unblock) cease prescribing the removed operator-reconciliation routing, and the deviation ledger records the blueprint change.
- The pins baseline is restored: two Mode-binding pin spans re-aimed to their current carriers and one all-served log entry pruned, so the pins suite is green again.

Gate delta: removals: the origin-only refusal class and its exit-code contribution in `cmd_post_landing`, the two origin-leg-only keep-arm branches in `land_squash.sh` (land and land-worktree modes), and the operator reconciliation instruction in the keep-arm note and the three consumer blueprints. Additions: one informational note output line in `cmd_post_landing`, a replacement informational-routing sentence in the authoring and execution blueprints, a clause deletion in the unblock blueprint, one appended deviation entry in `templates-CHANGELOG.md`, and two re-aimed pin rows in `check_maintenance_pins.sh` (no new gate, check, field, or seam; net operative text shrinks).

## Assumptions

- The origin-tracking ref can never be invalidated by a landing: the pre-swap gate verifies the landing commit's parent is the expected base tip before the CAS, so the landing commit descends from the pre-landing tip; the landing commit descends from the origin ref if and only if the pre-landing tip descends from it (the landing adds exactly one commit, itself, to the ancestor set, and nothing writes the origin-tracking ref), so the post-landing origin leg's outcome is fully determined before the landing. Basis: the parentage verification in `scripts/landing_parentage_gate.py` (pre-swap `ok: landing commit parentage verified`) and `scripts/land_squash.sh` invocation order.
- What the origin leg still detects beyond the preserved checks: only a pre-existing divergence between local main and the remote-tracking ref (in this local-only repository, an expected steady state); it detects no landing defect, which is why it survives as a note rather than a refusal. The touched scripts are deployed to other repositories through the `~/.ai-playbook/scripts` symlinks, so the note wording states the universally true descent fact and leaves the action judgment to the consuming repository instead of asserting that no action is ever required. Basis: the ancestry argument above, p66's recorded intent that the origin leg distinguish a pre-existing divergence from a landing-caused severance, and the deployed-home symlinks on this host.
- The operator-reported run's exact exit code is not re-derivable: no retained landing receipt or session artifact naming that run was found (search over docs/tmp and the gitignored .ai-playbook homes, 2026-10-15); the live ref state reproduces the arm deterministically, and the current fixtures pin the emitted lines, so the plan changes behavior against those pins without inferring the witnessed run's exit code. Basis: the origin row's evidence section and the absent receipt search.
- Task 4 is a review-staged scope addition: the r2 certification panel found the pins suite red on this repository's baseline (two Mode-binding pins stale since the fa22ac133 rewording landed without re-aims, plus one all-served log entry whose origin row a peer landing covered), which starves this plan's own validation chain; the repair restores the baseline without touching any pinned skill text. Basis: the r2 staged record and the pins-suite run reproduced on 2026-10-15.

Decision points requiring a grill: none remain.

## Standing constraints

- This repository is local-only: no step fetches, pushes, or mutates remote state; the origin-tracking ref is read-only input.
- Shell recipes in Validation Commands abort on miss and on forbidden match (fail-closed), never relying on bare grep exit status: forbidden-match sweeps capture the grep exit status and fail on rc 0 (forbidden match found) and on rc >= 2 (tool error), passing only on rc 1.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every changed post-landing shape has a failing-before, passing-after fixture (origin-only divergence exits 0 with the note; severed branch still exits 1; severed branch with diverged origin still exits 1 with one refuse line only), and each green path still passes.
- output clarity: no post-landing success path emits a `refuse:` line or an operator action requirement; the note names the origin ref and states the descent fact the landing verified.
- scope fidelity: the pre-tip refusal wording, the CAS, the interleaved-tip recovery, the absent-origin skip note, and the POST_RC 2/3 tool-error routing are unchanged; no live surface outside the changed files still names the removed routing.

**Done when:**
- `python3 scripts/test_landing_parentage_gate.py` passes including the rewritten origin cases.
- `python3 scripts/test_land_squash.py` passes with the diverge-origin tests asserting the informational output and the removed keep-arms' invariants.
- `bash scripts/check_maintenance_pins.sh` exits 0.
- The Validation Commands block passes end to end, including the per-surface negated sweeps over the three consumer blueprints.

**Ship when:**
- None; the change is fully local and verifiable in-repository.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/landing_parentage_gate.py`
- `scripts/land_squash.sh`
- `agents/skills/maintenance/template-authoring.md` *(one sentence in the landing paragraph)*
- `agents/skills/maintenance/template-execution.md` *(one parenthetical in the landing pass-arm)*
- `agents/skills/maintenance/template-unblock.md` *(one enumeration clause in the landing routing paragraph)*
- `agents/skills/maintenance/templates-CHANGELOG.md` *(one appended deviation entry)*
- `scripts/check_maintenance_pins.sh` *(two pin rows re-aimed, provenance beside each)*

**Tests:**
- `scripts/test_landing_parentage_gate.py`
- `scripts/test_land_squash.py`

**Log surfaces:**
- `docs/history/backlog/PLAN-PROMPTS.md` *(one all-served entry pruned with its receipt)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/reconcile_post_landing.py`; separate landed post-landing reconciliation contract, untouched by this change.
- `agents/skills/maintenance/SKILL.md`; the Mode-binding text stays byte-identical (the pins re-aim points at its existing spans).
- `docs/history/plans/completed/2026-09-27-p66-orphan-squash-landing-gates.md` and `docs/history/plans/completed/2026-10-03-squash-landing-failure-path-guard.md`; completed history is immutable context cited as rationale, never edited.

## Validation Commands

```bash
# Full suite for both touched test files (abort on any failure).
python3 scripts/test_landing_parentage_gate.py || { echo 'FAIL: gate suite'; exit 1; }
python3 scripts/test_land_squash.py || { echo 'FAIL: land_squash suite'; exit 1; }
# Pins suite: green only after Task 4 restores the baseline.
bash scripts/check_maintenance_pins.sh || { echo 'FAIL: pins suite'; exit 1; }
# Negated sweeps: each removed routing echo has its own fail-closed three-way
# probe. The [x] bracket escapes are intentional (self-match immunity): each
# escaped pattern cannot match its own command line, while genuine stale
# echoes still match. The Gist's historical Before quote does contain the
# plain phrase, which is why every sweep targets only live surfaces and none
# targets the plans directory.
sweep() { rc=0; grep -rn "$1" $2 || rc=$?; [ "$rc" -eq 1 ] || { echo "FAIL: sweep '$1' rc=$rc (0 = stale echo remains, >=2 = tool error)"; exit 1; }; }
sweep "reconcile the origin ref with the landed ti[p]" "scripts/land_squash.sh"
sweep "naming the origin le[g] alone" "agents/skills/maintenance/template-authoring.md"
sweep "operator reconciliation: fetch, the[n]" "agents/skills/maintenance/template-execution.md"
sweep "origin-leg kee[p]" "agents/skills/maintenance/template-unblock.md"
sweep "diverge-origin keep ar[m]" "scripts/test_land_squash.py"
sweep "origin-leg-only divergence note ar[m]" "scripts/test_land_squash.py"
sweep "takes the origin-leg-onl[y]" "scripts/test_land_squash.py"
# The informational note exists in the gate and carries the descent fact.
grep -q "predates the landing" scripts/landing_parentage_gate.py || { echo 'FAIL: informational note missing'; exit 1; }
# The blueprint replacements are present (positive pins, one per file).
grep -q "informational" agents/skills/maintenance/template-authoring.md || { echo 'FAIL: authoring blueprint replacement missing'; exit 1; }
grep -q "informational" agents/skills/maintenance/template-execution.md || { echo 'FAIL: execution blueprint replacement missing'; exit 1; }
# The deviation entry exists (fails today, flips when Task 2 lands).
grep -q "2026-10-15-post-landing-origin-ancestry-diagnostic" agents/skills/maintenance/templates-CHANGELOG.md || { echo 'FAIL: deviation entry missing'; exit 1; }
```

### Task 1: Reclassify the gate's origin-only divergence as informational

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/landing_parentage_gate.py`
- `scripts/test_landing_parentage_gate.py`

Primary class anchors:
- `cmd_post_landing` in `scripts/landing_parentage_gate.py`

- [x] `cmd_post_landing` reports origin-only divergence informationally: given a default branch that descends from the pre-landing tip while `--origin-ref` resolves to a non-ancestor, expects exit 0, no `refuse:` line, exactly one note line naming the origin ref and stating the descent fact (the divergence predates the landing). [class: IMPLEMENTATION_REQUIRED]
- [x] Pre-tip protection unchanged: given a severed default branch, expects exit 1 with the pre-landing-tip refuse line; given a severed branch plus a diverged origin ref, expects exit 1 whose output contains exactly one refuse line (the pre-tip one) and the origin divergence as a note. [class: IMPLEMENTATION_REQUIRED]
- [x] Absent-origin and origin-ancestor behaviors unchanged: given an unresolvable origin ref, expects exit 0 with the existing skip note; given an origin ref that is an ancestor, expects exit 0 with the existing ok line and no note. [class: REPOSITORY_TEST]
- [x] The two existing tests pinning the removed refusal are rewritten in this task: `test_post_landing_origin_ref_passes_and_refuses` (its refuse leg folds into the new origin-only informational case, its green half stays) and `test_post_landing_both_legs_drop_prints_both_refuse_lines` (becomes the severed-branch-plus-diverged-origin fixture of the second item). [class: REPOSITORY_TEST]
- [x] Run the new origin-only case and the rewritten both-legs assertion first and record the failing output, then implement: replace the origin refusal path with the note print, remove the `origin_refusal` exit contribution, and update the usage docstring's origin-leg wording. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN on the full gate suite; note for the executor: the land_squash suite is red at this point (its current diverge-origin assertions still demand the removed reconciliation text) and turns green in Task 2. [class: REPOSITORY_TEST]
- [x] Commit: `gate: report origin-only ancestry divergence informationally` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Remove the helper's unreachable origin-only keep-arms and update every consumer

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/land_squash.sh`
- `scripts/test_land_squash.py`
- `agents/skills/maintenance/template-authoring.md`
- `agents/skills/maintenance/template-execution.md`
- `agents/skills/maintenance/template-unblock.md`
- `agents/skills/maintenance/templates-CHANGELOG.md`

Primary class anchors:
- `print_gate_evidence` in `scripts/land_squash.sh`, the evidence printer whose POST_RC routing the changed arms feed in both landing modes
- `test_land_origin_leg_divergence_note` in `scripts/test_land_squash.py`
- `test_land_worktree_diverge_origin_keeps_landing` in `scripts/test_land_squash.py`

- [x] Reachability witness recorded in the task log: with the pre-swap parentage verification, `POST_RC` is 1 only when the pre-tip leg refused, and the base ref then cannot equal the landing commit, so both keep-arm branches are dead code after Task 1. [class: REPOSITORY_TEST]
- [x] RED witness at this task's start: run the unmodified diverge-origin tests against the Task 1 tree and record their failing output (their current assertions demand the removed `operator reconciliation` text); the updated assertions written here cannot be shown failing against the dead keep-arm, so the removal itself is pinned by the negated sweep and the structural check, not by a RED run. [class: REPOSITORY_TEST]
- [x] Both diverge-origin tests updated: assert the pass outcome with the gate's informational note in evidence, assert no `operator reconciliation` text, and keep the kept-landing invariants (landing kept, parent is the base tip, clean checkout). [class: REPOSITORY_TEST]
- [x] The test file's stale arm prose is rewritten to the informational-note routing in the same edit: the module docstring's arm enumeration, the section banner above `test_land_origin_leg_divergence_note`, and the behavior comment atop `test_land_worktree_diverge_origin_keeps_landing`. [class: REPOSITORY_TEST]
- [x] Keep-arms removed in both landing modes: the `POST_RC` 1 routing goes directly to the interleaved-tip arm; the keep-arm note lines and the reconciliation instruction are deleted; the POST_RC 2 and tool-error routing is unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] The authoring blueprint's landing paragraph replaces the origin-leg reconciliation routing sentence (the one naming the origin leg alone) with the informational routing. [class: IMPLEMENTATION_REQUIRED]
- [x] The execution blueprint's landing pass-arm parenthetical (the one naming the operator reconciliation: fetch, then rebase or the push decision) is replaced with the informational routing. [class: IMPLEMENTATION_REQUIRED]
- [x] The unblock blueprint's landing routing enumeration drops the origin-leg keep clause and keeps the inverse compare-and-swap clause. [class: IMPLEMENTATION_REQUIRED]
- [x] One deviation entry is appended to templates-CHANGELOG.md citing this plan, the retired origin-leg reconciliation routing, and the replacement informational routing. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN on the full land_squash suite including the interleaved-tip and fault-seam tests. [class: REPOSITORY_TEST]
- [x] Commit: `landing: drop unreachable origin-only keep-arms and update consumers` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Full validation sweep

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_landing_parentage_gate.py` *(existing)*
- `scripts/test_land_squash.py` *(existing)*

Primary class anchors:
- `cmd_post_landing` in `scripts/landing_parentage_gate.py`, whose informational note the Validation Commands pin.

- [x] Run the whole Validation Commands block and record each result; every negated sweep uses the fail-closed three-way split, and each removed routing echo has its own dedicated per-surface probe. [class: REPOSITORY_TEST]
- [x] Confirm the changed surfaces carry no echo of the removed routing and the gate carries the informational note; record the sweep outputs in the task log. [class: REPOSITORY_TEST]
- [x] Commit any validation-forced corrections under `test: pin origin-only informational landing output`; on an all-green first pass no commit arises and this item records that outcome. [class: REPOSITORY_TEST]

### Task 4: Restore the pins baseline

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/check_maintenance_pins.sh`
- `docs/history/backlog/PLAN-PROMPTS.md`

Primary class anchors:
- `pin` in `scripts/check_maintenance_pins.sh`, whose Mode-binding rows (the dual-default and binding-postfix rows) this task re-aims

- [x] The dual-default pin row is re-aimed to the current carrier span (`When no keyword or manual ruling classifies the run, default to dual` in the Mode binding paragraph) with a provenance comment naming the fa22ac133 rewording and the unchanged semantics. [class: IMPLEMENTATION_REQUIRED]
- [x] The binding-postfix pin row is re-aimed to the current carrier span (`classifies auth, author, authoring wording as author mode`) with the same provenance form. [class: IMPLEMENTATION_REQUIRED]
- [x] The all-served PLAN-PROMPTS entry (`post-implementation-review-invariant-coverage`, whose origin row a peer landing covered) is pruned with the receipt `PLAN-PROMPTS-PRUNE: post-implementation-review-invariant-coverage -> docs/history/plans/2026-10-15-post-implementation-review-invariant-coverage.md`, per the prune scan's own direction. [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh` first and record the three failing pins, then re-run after the repairs and record `OUTCOME: pass`. [class: REPOSITORY_TEST]
- [x] Commit: `pins: re-aim mode-binding spans and prune the all-served log entry` [class: IMPLEMENTATION_REQUIRED]
