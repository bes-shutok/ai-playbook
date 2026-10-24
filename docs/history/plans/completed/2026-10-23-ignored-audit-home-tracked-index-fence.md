# Plan: Complement the Audit-Home Ignore Policy at the Commit and Landing Boundary

Backlog origin: docs/history/backlog/2026-10-20-ignored-audit-home-paths-force-tracked.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-24-plan-review-ignored-audit-home-tracked-index-fence-r*.md
Execution budget: 1.5h total, largest task 1h
Classification: [class: fix-class] warning-only observability complement with skill-text and fixtures
Authoring claim: docs/tmp/authoring-claims/2026-10-20-ignored-audit-home-paths-force-tracked.md (session zcode-automation-1f6ae856-1944)

## Terms

- **Audit home:** The gitignored `/.ai-playbook/` directory holding local run artifacts such as certification seals and review records; retention rides the docs branch, never the tracked tree.
- **Force-tracked:** A path inside an ignored directory that git nonetheless tracks because it was added with a forced add; git consults no ignore rule for tracked paths.
- **Probe:** The pre-lock, read-only mode of `scripts/land_squash.sh` that gates a landing on containment and conflict checks before the lock is acquired.
- **Done landing sweep:** The done closeout's gate family in `scripts/done_sweep_gates_lib.py` that classifies leftover paths; its ignored arm enumerates untracked ignored files only.
- **Warning-only:** A report that prints evidence and never changes an exit code, per the machinery admission protocol until a true catch and a pre-registered registry-removal row.
- **Tracked-ignored warning:** Reports landing-boundary paths an ignore rule matches even though git tracks them: branch-changed paths via `git check-ignore --no-index` (the probe arm), index-tracked ones via `git ls-files -i -c --exclude-standard` (the sweep's tracked sibling).
- **Seal:** The local certification record a round-close writes under the audit home (for example `.ai-playbook/review-certs/`).
- **Pre-landed:** The two witnessed seals, already untracked at `839984ac2`, plus three tracked-ignored review records main already carries (added by landing `9e703d600`); the records' untracking is plan scope, the seals' cleanup is recorded history.
- **Carrier fire:** One execution of the scheduled authoring carrier.

## Why

Two force-tracked seals reached main in one carrier fire through two different landing paths, and nothing on either path reports the class, so detection stays manual.

## Gist & Examples

TLDR: Both landing paths gain a warning-only tracked-ignored report and the closeout text forbids the forced add, so the next force-tracked audit-home artifact is named by machinery instead of found by eye, for code-quality.

**Before:** A session hit the ignore refusal hint and answered it with a forced add; commit `f5a8142ed` landed a seal directly on main and `4399aee99` landed one through the worktree squash; detection came eleven hours later by eye, and one untrack commit (`839984ac2`) cleaned up.

**After:** A branch carrying a force-tracked ignored path prints the path list from the probe and from the done sweep while both still succeed; a clean branch prints nothing; the plans round-close seal duty and the maintenance authoring closeout residue step each carry one sentence that the seal and every `.ai-playbook/` artifact stay untracked and an ignore refusal ends the staging attempt, never prompting a forced add.

**Example:** `git ls-files -i -c --exclude-standard` listing `.ai-playbook/review-certs/example.md` makes the sweep surface print a warning naming that path, and the probe surface does too when the path is on the branch delta; exit codes and verdicts stay unchanged.

**Edge cases:** A clean index reports nothing from either surface. The instances witnessed are already untracked, so the plan records them as pre-landed in its Terms and no task redoes that cleanup. A deliberate non-audit-home tracked-ignored path elsewhere in the repository would also warn; the warning's disposition rule is that a reported path is either untracked on sight or recorded as deliberate. The repository's tracked-ignored population at authoring time is the three review records inventoried under Pre-landed, all in the plan's scope; once they are untracked, the false-positive cost is zero on a clean index.

## Outcome

The ignore policy gains its complement at the two commit and landing boundaries, so the force-tracked class is reported by machinery on both landing paths.

- The probe reports any branch-changed path matched by an ignore rule, warning-only.
- The done landing sweep's ignored arm gains the tracked sibling reporting `git ls-files -i -c --exclude-standard` output, warning-only.
- The two closeout text homes carry the untracked-seal sentence and the never-force-add rule.

Gate delta: No new refusal class, hard gate, fence, protocol layer, schema field, flag, mode, or dispatch pause; both additions are warning-only reports in two existing surfaces, paid for by the witnessed double landing (incident `f5a8142ed` and `4399aee99`, catch frequency about two per 138 seals in the audit home's history plus the three live records the first closeout reports, false-positive cost zero on a clean index once the inventoried records are untracked, review 2027-01-20 with promotion only after a true catch and a pre-registered registry-removal row). No blocking review-layer duty is added.

## Assumptions

- assume the probe's predicate runs over the branch delta paths (`git diff --name-only <base tip> <source tip>` piped through `git check-ignore --no-index --stdin`); basis: the probe already resolves both tips for its containment check, and `--no-index` matches would-be-ignored paths that are tracked, which the plain check-ignore mode never reports.
- assume the done sweep's sibling uses `git ls-files -i -c --exclude-standard` with no pathspec restriction beyond the sweep's existing scope; basis: the existing `_ignored_paths` helper in `scripts/done_sweep_gates_lib.py` is the untracked counterpart and the flagged design names that exact command.
- assume the two text homes are the plans skill's round-close seal duty and the maintenance authoring blueprint's closeout residue sentence; basis: the origin row names both and the witnessed session had the local-seal sentence in front of it and still forced the add, so both homes get the explicit never-force-add rule.
- assume the two witnessed instances stay out of task scope (already untracked at `839984ac2`; the inheriting branch dropped the path on its rebase); basis: the origin row records both as pre-landed.
- assume the simplest alternative, skill text alone, is rejected as the whole fix; basis: the witnessed session had the sentence and the ignore refusal hint still won, and one fire produced two instances through two paths within eight minutes.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: each surface's fixture shows the warning with the paths named on a force-tracked branch and silence on a clean branch, and both still exit in their existing verdicts.
- Safety: no exit code, refusal class, or gate verdict changes; the additions are report-only.

**Done when:**
- Both witnesses per home pass: a branch carrying a force-tracked ignored path probes with the warning and still exits 0 with its pass verdict and no mutation, and a clean branch probes without the warning.
- The two text sentences sit in their named homes inside existing steps, one sentence each.
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_land_squash.py scripts/test_done_sweep_gates_lib.py` passes with the new fixtures present.

**Ship when:**
- None; the repository change is the complete deliverable.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid).

**Production code:**
- `scripts/land_squash.sh`
- `scripts/done_sweep_gates_lib.py`

**Tests:**
- `scripts/test_land_squash.py`
- `scripts/test_done_sweep_gates_lib.py`

**Documentation:**
- `agents/skills/plans/SKILL.md` (the round-close seal duty sentence only)
- `agents/skills/maintenance/template-authoring.md` (the closeout residue sentence only)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `.gitignore` and the ignore-policy selection record (`docs/history/plans/completed/2026-10-13-skill-audit-artifact-ignore-default.md`); reason: the policy is correct and selected on record; this plan lands its complement, not a policy change.
- `docs/history/backlog/2026-10-22-adhoc-landing-sentence-omits-land-squash-helper.md`; reason: a sibling row about the arm's landing sentence discoverability, a different mechanism.

## Validation Commands

```bash
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-23-ignored-audit-home-tracked-index-fence.md
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_land_squash.py scripts/test_done_sweep_gates_lib.py || exit
git ls-files -i -c --exclude-standard | grep -q . && echo 'tracked ignored paths remain' && exit 1 || echo 'real index clean'
bash scripts/check-no-em-dash.sh || exit
REPO_ROOT="$(git rev-parse --show-toplevel)" || exit
(cd "$REPO_ROOT" && bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh") || exit
```

### Task 1: The probe's tracked-ignored warning and the plans seal-duty sentence

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/land_squash.sh`
- `scripts/test_land_squash.py`
- `agents/skills/plans/SKILL.md`

Primary class anchors:
- `emit_outcome` in `scripts/land_squash.sh`

- [x] The probe delivers the tracked-ignored warning: given a source branch whose delta from the base tip changes a path matching an ignore rule, expects the probe to print one warning line per matched path and still exit with its existing pass verdict; given a clean branch, expects no warning. [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given any probe input, expects no exit code or verdict change from the warning arm; the warning is report-only. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the plans skill's round-close seal duty, expects one added sentence stating the seal and every audit-home artifact stay untracked and an ignore refusal ends the staging attempt, never prompting a forced add, inside the existing step. [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect RED: a scratch-repository fixture that seeds its own ignore rule and force-tracks two ignored paths on the source branch with `git add -f` and commits them (the done-sweep suite's force-add precedent) shows the probe printing no warning today; follow the existing land-squash suite fixture shape, whose helpers need the seeding added. [class: REPOSITORY_TEST]
- [x] Write minimal implementation: the branch-delta check-ignore pass guarded for the none-matched exit (the script's `|| true` pipeline style, so a clean branch reaches OUTCOME: pass unchanged) and the one sentence. [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect GREEN: the land_squash suite passes with the warning fixture (each forced path named on its own warning line) and the clean-branch fixture. [class: REPOSITORY_TEST]
- [x] Commit: `feat: warn on force-tracked paths at the landing probe` [class: IMPLEMENTATION_REQUIRED]

### Task 2: The done sweep's tracked sibling and the authoring closeout sentence

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`
- `agents/skills/maintenance/template-authoring.md`

Primary class anchors:
- `_ignored_paths` in `scripts/done_sweep_gates_lib.py`

- [x] The done landing sweep delivers the tracked sibling: given a closeout scope holding an index-tracked path matching an ignore rule, expects the sweep to report the path repo-wide (no pathspec, not session-window-filtered, so an inherited tracked-ignored path from a polluted base is still reported) from `git ls-files -i -c --exclude-standard` warning-only, beside the existing untracked ignored arm. [class: IMPLEMENTATION_REQUIRED]
- [x] A comment beside the tracked sibling carries the admission fields (incident, catch frequency, review 2027-01-20) as the recording destination for a true catch. [class: IMPLEMENTATION_REQUIRED]
- [x] Untrack the three inventoried tracked-ignored review records in the same change (`git rm --cached` on the Pre-landed list), so the first closeout's report starts from a clean index. [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a clean scope, expects the tracked sibling to report nothing and every gate verdict to stay unchanged; given an old-mtime inherited tracked-ignored path, expects it still reported (the no-session-filter clause is pinned). [class: IMPLEMENTATION_REQUIRED]
- [x] Given the authoring blueprint's closeout step, expects one added sentence with the same untracked-seal and never-force-add rule inserted beside its existing review-artifacts-never-ride-commits sentence. [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect RED: a fixture that seeds its own audit-home ignore rule and force-tracks a path under it with `git add -f` (staging suffices; the tracked sibling reads the index) outside any single gate's narrow pathspec (for example under review-certs, mirroring the witnessed shape) shows no report today, following the existing done-sweep suite fixture shape. [class: REPOSITORY_TEST]
- [x] Write minimal implementation: the tracked sibling helper beside `_ignored_paths` and the one sentence. [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect GREEN: the done-sweep suite passes; the em-dash and public hygiene scans stay clean. [class: REPOSITORY_TEST]
- [x] Commit: `feat: report tracked ignored paths in the done sweep` [class: IMPLEMENTATION_REQUIRED]
