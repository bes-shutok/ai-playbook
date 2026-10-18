# Backlog: name the missing reviews home in the review-record selector's refusal

- **Filed:** 2026-10-17, learn Step 1.8 capture from the 2026-10-17 authoring session
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** observed selector-family misattributed refusal
- **Class:** fix-class
- **Driving force:** operability (primary); reliability (secondary)
- **Skill/step:** `scripts/review_record_selection.py`, `_repository_root` use in the `select` usage-error path
- **Severity:** low; the wrong message costs a re-derivation detour on each fresh-worktree selection
- **Cluster:** docs/history/backlog/2026-10-10-review-selector-kind-suffix-alias.md (same surface: `scripts/review_record_selection.py` selection refusals)

**Observed:** in a fresh linked worktree whose `reviews_dir` (facts key) does not exist yet, running the selector's `select` with `--source-plan <worktree plan path>` refuses with "--source-plan requires a path inside a git repository". The actual state is that the reviews directory named by the facts key is missing: `_repository_root` derives the repository root from the reviews directory (git toplevel anchored there) and returns `None` when that directory does not exist, and the usage error reports that `None` as a repository problem.

**Expected:** the refusal names the directory it could not resolve (for example "reviews directory <path> does not exist; create or transfer it in before selection"), or falls back to deriving the repository root from the source plan's git directory, so the operator reads the missing-provisioning remedy instead of hunting a git problem.

**Reproduction:** create a fresh linked worktree; skip the worktree standard's transfer-in step (which `mkdir -p`s the reviews directory); run the selector `select` with `--source-plan` pointing at a plan file in the worktree; the misattributed refusal reproduces.

**Environment:** playbook repository, 2026-10-17 authoring session, worktree execution, repo copy of the script. Witnessed once; the 2026-10-08 authoring cycle hit the adjacent missing-provisioning state and hand-created the directory after the same detour.

**Suspected root area:** `_repository_root` conflates "path is not inside a git repository" with "path does not exist"; the error message is built for the first case only.
