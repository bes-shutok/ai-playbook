# Plan: Concurrent-landing and archive-routing hygiene gates

Backlog origins (scope of record):
- `docs/history/backlog/2026-09-27-concurrent-landing-foreign-staging-sweep.md`
- `docs/history/backlog/2026-09-27-plans-archive-move-only-gate.md`
- `docs/history/backlog/2026-09-27-registry-concurrent-landing-lost-update.md`
- `docs/history/backlog/2026-09-27-backlog-filing-dedup-probe.md`

Driving force: code-quality + efficiency
Plan review record: the staging series docs/reviews/2026-09-27-plan-review-concurrent-landing-archive-routing-gates-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Turn the four witnessed landing-interference and archive-routing defects into named gates: a landing closeout refuses to stage work it does not own, the shared document registry detects a concurrent writer before committing, plans archive routing gains a landing-time twin gate on top of the corpus-wide pins owner, and every backlog filing carries a dedup probe.

- A landing closeout can no longer sweep a concurrent session's uncommitted files into its commit at the whole-file level: the foreign-dirt judgment arm in the done skill is the pre-staging net, and the done sweep's `foreign-staging` gate re-runs at the commit boundary over the final staged set, failing any staged path that is both recorded as start-dirt and outside the run's owned paths (content-level co-editing inside a session-owned path stays a recorded residual).
- The document registry read-modify-write detects a concurrent same-checkout writer before it commits: a capture-and-verify digest arm (record the registry digest when the edit is computed, re-verify at staging, and on a mismatch re-apply the session's rows onto the freshly read bytes) plus an own-rows re-grep arm catch the clobber class that silently dropped two audit rows on 2026-09-27 (cross-worktree composition losses stay a recorded residual; see Assumptions).
- Plans archive routing gains a landing-time net that closes the release-skill twin class end to end: a completed-home protocol README plus a `plans-archive-twin` done-sweep gate fail any landing while a dated plan basename sits both at the plans root and in an archive state directory (the maintenance pins suite hard-failed that class on every run, but nothing gated it at landing time until the twin was removed by a manual dedup pass), and the release-skill live-twin backlog item is dispositioned as a duplicate of the move-only origin with the resolved baseline re-verified.
- Every backlog filing records the corpus search it ran and the nearest items found, so topic twins like the compact-mechanism pair surface at filing time instead of two days later.

## Terms

- **Landing (closeout):** the commit sequence that finalizes a session's work into the default branch's history: the done skill's Step 3 in place, or the execute-plan/driver squash closeout for an executed plan.
- **Foreign dirt:** uncommitted work in the checkout that the current session does not own: another live session's edits, staged entries, or untracked files.
- **Done sweep gates:** the deterministic gate runner `scripts/done_sweep_gates.sh` plus `scripts/done_sweep_gates_lib.py`, one gate function per absorbed done step, run in `pre-docs` and `pre-commit` phases.
- **Run manifest (start-dirt record):** the Step 0 JSON record under the done-session directory; its `start_porcelain` list is the verbatim `git status --porcelain` snapshot (rows with status letters intact) taken before this session staged anything, and its owned-path lists record what this run may stage.
- **Move-only archive routing:** an archive transition is a rename (`git mv`) of the live path; the open home never retains an archived basename; a plan or item exists in exactly one lifecycle state (open, completed, deferred, rejected) at a time.
- **Dedup probe:** the required record in a newly filed backlog item of the keyword search run over the open backlog corpus, the nearest item(s) found, and the distinction from each or a merge recommendation.

## Assumptions

- assume the dedup-probe requirement lands in the `receiving-review` skill's Backlog capture required-content list rather than in a backlog README; basis: no `docs/history/backlog/README.md` exists on disk, and the filing checklist of record is the Backlog capture required-content list (the origin item's "backlog README protocol" wording is rewritten to the current SOT placement per the plans skill's origin-acceptance rewrite rule).
- assume the `2026-09-27-release-skill-plan-live-twin` backlog item closes as a duplicate of origin 2 rather than being subsumed as additional scope; basis: verified 2026-09-27 at main ad1337fd that the live copy `docs/history/plans/2026-09-26-release-skill.md` is absent, only `docs/history/plans/completed/2026-09-26-release-skill.md` remains, and `bash scripts/check_maintenance_pins.sh` exits 0, so the item's fix scope is already discharged by the 2026-09-27 dedup pass; the authoring task pre-authorizes close-as-duplicate.
- assume the plan adds a second mechanical scanner over the basename-collision class beside the existing `check_maintenance_pins.sh` live-vs-archive gate, with a recorded ownership split; basis: the pins suite (hard-failing this class since 2026-09-25, over plans AND backlog roots, non-dated names included, filesystem-scanned) runs only in the maintenance suite, so the real gap is timing: nothing fails at landing time. The done-sweep `plans-archive-twin` gate is the landing-time net over the plans home (facts-key-driven, dated plan shape, per origin 2's prescribed fix shape); the pins section stays the corpus-wide scheduled owner. Neither scanner may be removed as the duplicate of the other: the pins gate covers the backlog root and non-dated names that the done-sweep gate deliberately does not, and the done-sweep gate runs at a cadence the pins suite does not. The doc-registry validator's unregistered-completed-history warn is a different class (registry completeness, the lost-row net) and stays warn-level: the lost-row net this plan adds is the Task 2 digest capture-and-verify arms, deliberately fail-open so routine row appends stay lock-free and lightweight.
- assume the run manifest grows one owned-paths list for the staging gate (`owned_paths`, recorded at Step 0 via repeatable `--owned-path <path>` claims beside the existing `--owned-review`/`--foreign-review` flags), while registry detection grows no manifest field; basis: the staging gate's discriminator must be ownership, and the run's own record of what it may stage is exactly that data (mirroring the existing owned-plan/owned-review lists); the registry detection arms are in-skill judgment and need no schema.
- assume registry-mutation serialization stays declined for routine appends; basis: the done lock serializes one checkout's done run end to end (sweep gates through project commits), and the merge lock covers the Step 2 worktree migration and docs-branch sync and is released before Step 3, so landing-time registry writes run unserialized against a peer's routine appends; that residual is exactly why the Task 2 detection arms exist. A lock requirement for routine non-landing appends would serialize unrelated capture flows that do not touch the landing path, so the detection arms are the accepted mechanism. Recorded residuals: even with the Task 2 arms, a peer registry write landing inside any armed-check-to-next-check window remains unserializable without the lock, including the final re-hash-to-commit window (a pathspec commit serializes working-tree bytes, so a write after the last re-hash lands unverified bytes with every arm green); the arms are same-checkout arms, and a cross-worktree composition loss (two linked worktrees landing concurrently, each commit's tree replacing the registry wholesale) is structurally invisible to every arm because neither worktree's bytes ever contain the peer's rows: that class is accepted as a recorded residual rather than gated, because landing commits already serialize through the repository-keyed merge lock at the orchestration layer and a registry-specific lock routing was declined to keep the arms judgment-level. The foreign-staging arms are path-granular, so peer hunks edited inside a path this session owns stay sweepable (content-level co-editing has no provenance signal; the registry got row-level arms because it is the one shared file with row identity). Gitignored paths sit outside the start-dirt record by porcelain semantics; the done skill's never-stage-gitignored rule owns that class, and the bound is accepted.
- assume the execute-plan skill needs no new archive-rule text of its own; basis: its Phase 4 already carries the move-only discipline (the Move-with-mutation discipline paragraph and the UL#193 completeness gate, verified on disk), so the execute-plan-side change is limited to naming the foreign-staging landing gate in its Hard Gates list.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: landing closeouts refuse foreign work and archive routing gains a landing-time twin gate, because silent lost updates and copy-not-move twins keep converting concurrent work into rework (code-quality, with efficiency second: every incident today costs a cleanup pass).

On 2026-09-27 two sessions shared one checkout: the dedup pass held five uncommitted changes while the done-gate execution landing ran its closeout in the same tree. The landing's staging swept all five of the dedup pass's paths into its staged set (twelve staged paths, seven of them foreign), its registry read-modify-write was computed from a pre-edit read and silently dropped the dedup pass's two new audit rows, and nothing flagged either: only the landing's explicit per-path commit pathspec kept foreign work out of the squash. The same day, the release-skill execution landing had left a byte-identical plan twin at the plans root and under `completed/`; the maintenance pins suite hard-fails exactly that class and did so at every run, but nothing at landing time caught it, so the twin sat at the plans root until a manual dedup pass removed it later that day. And two backlog items filed two days apart covered the same compaction mechanism without ever being reconciled, because filing requires no corpus consult.

This plan adds the missing named gates at each layer:

- before staging, the landing compares uncommitted paths against its own owned list and refuses foreign paths (judgment arm in the done skill), and the `foreign-staging` done-sweep gate, re-run at the commit boundary over the final staged set, mechanically fails any staged path that is both recorded as start-dirt at Step 0 and outside the run's owned paths;
- the done skill arms that touch the document registry record the file's digest when the edit is computed, re-verify it at staging (on a mismatch: re-read and re-apply the session's rows onto the freshly read bytes, never a pre-computed block), and re-grep that the session's own rows are still present before committing;
- the plans completed home gets the written move-only protocol no plans-tree home carries today (the backlog counterpart's written-home role is the model, not its content), and the `plans-archive-twin` gate fails any landing while a dated plan basename sits at the plans root and in `completed/`, `deferred/`, or `rejected/` at the same time (the maintenance pins suite keeps owning the corpus-wide post-hoc check);
- the backlog filing checklist requires a `Dedup probe:` line, and plan-review panels treat a missing probe line as a Low finding.

## Evaluation Criteria

**Quality dimensions:**

- correctness: the `foreign-staging` gate fails on a staged path that is in the normalized start-dirt record and not in the run's owned paths (both sides compared over the same C-unquoted raw-path space, renames exposed on both sides), and passes the owned staged set, the union-exemption shape, the re-run-after-staging and adopted-run shapes; the `plans-archive-twin` gate fails on a root-plus-archive basename pair (byte-identical or different, in any state directory) and passes the current tree; all behaviors pinned by hermetic fixtures.
- fail-closed degradation: with no resolvable run manifest the `foreign-staging` gate reports a warning skip, never a silent pass and never a crash; with a non-default `plans_completed_dir` facts key the twin gate scans the configured home, never the hardcoded default; with an unresolvable key or an absent state directory the twin gate emits a named warning, never a silent green.
- simplicity: each new mechanical check has exactly one home (the done sweep runner); skill text names gates and states obligations, it does not re-implement them; the two basename-collision scanners (done-sweep gate, pins suite) carry a recorded ownership split instead of a silent duplicate.
- maintainability: gate ids appear consistently in the lib registry, the phase lists, the runner usage text, `list-gates`, the done skill's phase inventories and fix guidance, and the test count expectations.

**Done when:**

- `scripts/test_done_sweep_gates_lib.py` and `scripts/test_done_sweep_gates_wrapper.py` pass, including the new gate fixtures and the updated phase-count and phase-membership expectations (pre-docs emits 8 gate lines, pre-commit emits 5, `list-gates` prints twelve distinct ids, and plans-archive-twin sits in both phase lists while foreign-staging sits in pre-commit).
- The obligation sentences listed in Tasks 2, 3, and 5 are present verbatim in the four skill files, and `docs/history/plans/completed/README.md` exists with the move-only protocol.
- The live-twin item sits under `docs/history/backlog/rejected/` with a `Status: rejected` duplicate disposition, its registry row exists, `scripts/doc_registry_validator.py validate` exits 0, and `bash scripts/check_maintenance_pins.sh` exits 0 with the live twin still absent.
- The shared-skill-body runtime-neutrality test passes (execute-plan SKILL.md is a gated shared body).

**Ship when:**

- Nothing ships outside this repository; no external gate applies.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py`
- `scripts/done_sweep_gates.sh`
- `agents/skills/done/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `scripts/check_maintenance_pins.sh` *(comment-only touch: the ownership-split pointer above `check_live_vs_archive_duplicates`)*
- `docs/history/plans/completed/README.md` *(new)*
- `docs/maintenance/document-registry.md` *(Task 4 protocol-README row + Task 6 rejected-routing row)*
- `docs/history/backlog/rejected/2026-09-27-release-skill-plan-live-twin.md` *(new at this destination; `git mv` from `docs/history/backlog/`, body byte-intact apart from the replaced Status line)*

**Tests:**
- `scripts/test_done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_wrapper.py`

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/doc_registry_validator.py`; reason: the warn-promotion arm is declined with a recorded class split (see Assumptions).
- `docs/history/plans/2026-09-27-deferred-residual-dispositions.md`; reason: a live peer plan in execution; its live-twin exemption arm retires at that plan's next natural edit per its own text, not in this plan.
- `README.md` (repository root); reason: the runner's README row describes phases, not gate ids, and stays accurate; the lib row's "one gate function per absorbed done step" phrasing becomes accepted drift under this plan's gate-shaped registry and retires with that file's next natural edit (recorded deliberately instead of widening this plan's scope).

## Validation Commands

Authoring record 2026-09-27 (worktree at main ad1337fd): the rule-29 pre-round gates were run over the plan bytes before round 1 and re-run after each fold (`check-no-em-dash.sh file`, the public-hygiene scan, `plan_readiness.py --pre-round`, all clean); the skill-text pins in checks 4 to 6 and the check 8 status and registry pins fired RED against the current target bytes, re-proven after each fold for reworded spans (the check 8 negative pin is a regression guard over the replaced Status line, dual-polarity by construction); check 7's pins target plan-created files, so they pass only once Task 4 exists (the expected vacuous-until-created class, first real failure surfacing at execution); every pinned span occurs in its task's prescribed text (rule-22 audit re-run after each fold); check 9 is the shared-body suite, not a text pin; the baseline guards in check 2 passed as regression guards (live twin already absent, pins already green); `bash -n` over this block passes.

```bash
#!/usr/bin/env bash
# Run from any working tree of this repository. Fail-closed throughout;
# every repo-root-sensitive invocation is anchored.
set -u
fail() { echo "VALIDATION FAIL: $*" >&2; exit 1; }
REPO="$(git rev-parse --show-toplevel 2>/dev/null)" || fail "run inside a checkout of the repository"
TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"
"$TEST_PY" -m pytest --version >/dev/null 2>&1 || TEST_PY=python3

# 1. Done sweep gate suites, including the new gate fixtures and the updated
#    phase-count and phase-membership expectations (Task 1).
( cd "$REPO" && "$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py scripts/test_done_sweep_gates_wrapper.py -q ) || fail "done sweep gate suites"

# 2. Baseline regression guards (Task 6): the release-skill live twin stays
#    absent and the pins suite stays green.
test ! -e "$REPO/docs/history/plans/2026-09-26-release-skill.md" || fail "live twin reappeared at the plans root"
( cd "$REPO" && bash scripts/check_maintenance_pins.sh >/dev/null ) || fail "maintenance pins"

# 3. The two new gates are implemented and registered (Task 1).
grep -qF "gate_foreign_staging" "$REPO/scripts/done_sweep_gates_lib.py" || fail "foreign-staging gate not implemented"
grep -qF "gate_plans_archive_twin" "$REPO/scripts/done_sweep_gates_lib.py" || fail "plans-archive-twin gate not implemented"
DONE_SWEEP_REPO_ROOT="$REPO" bash "$REPO/scripts/done_sweep_gates.sh" list-gates | grep -qF "foreign-staging" || fail "list-gates missing foreign-staging"
DONE_SWEEP_REPO_ROOT="$REPO" bash "$REPO/scripts/done_sweep_gates.sh" list-gates | grep -qF "plans-archive-twin" || fail "list-gates missing plans-archive-twin"

# 4. Done skill obligation sentences (Task 2), one dedicated check per obligation.
grep -qF -- "--owned-path" "$REPO/agents/skills/done/SKILL.md" || fail "done skill: owned-path manifest claim missing"
grep -qF "re-run the pre-commit phase so the" "$REPO/agents/skills/done/SKILL.md" || fail "done skill: commit-time re-run duty missing"
grep -qF "foreign-dirt gate" "$REPO/agents/skills/done/SKILL.md" || fail "done skill: foreign-dirt gate not named"
grep -qF "outside the list and not attributable to this session's recorded work" "$REPO/agents/skills/done/SKILL.md" || fail "done skill: foreign-dirt attribution clause missing"
grep -qF "Landing commits use explicit pathspecs only" "$REPO/agents/skills/done/SKILL.md" || fail "done skill: pathspec-only rule missing"
grep -qF "registry digest alongside the edit" "$REPO/agents/skills/done/SKILL.md" || fail "done skill: registry digest capture arm missing"
grep -qF "re-apply the session's rows onto the freshly read bytes" "$REPO/agents/skills/done/SKILL.md" || fail "done skill: registry mismatch remedy missing"
grep -qF "confirm the written bytes by re-reading" "$REPO/agents/skills/done/SKILL.md" || fail "done skill: remedy loop closure missing"
grep -qF "re-grep that every registry row this session added" "$REPO/agents/skills/done/SKILL.md" || fail "done skill: own-rows re-grep arm missing"
grep -qF "re-hash the working-tree registry bytes against the staged blob" "$REPO/agents/skills/done/SKILL.md" || fail "done skill: staged-blob arm missing"
grep -qF "a move, never an add-plus-keep" "$REPO/agents/skills/done/SKILL.md" || fail "done skill: archive move rule missing"
grep -qF "fails any landing while a twin from an earlier run sits unresolved" "$REPO/agents/skills/done/SKILL.md" || fail "done skill: twin-gate guarantee missing"
grep -qF "staged paths recorded as start-dirt but not owned" "$REPO/agents/skills/done/SKILL.md" || fail "done skill: foreign-staging fix guidance missing"
grep -qF "unstaged removal of the plans-root side, never the archive side" "$REPO/agents/skills/done/SKILL.md" || fail "done skill: plans-archive-twin fix guidance missing"
grep -qF "docs-tmp-sweep, plans-archive-twin" "$REPO/agents/skills/done/SKILL.md" || fail "done skill: pre-docs enumeration missing plans-archive-twin"
( sed -n '/^## Pre-commit sweep gates/,/^## Step 3:/p' "$REPO/agents/skills/done/SKILL.md" | grep "^Gates run in this order:" | grep -qF "foreign-staging" ) || fail "done skill: pre-commit enumeration missing foreign-staging"
( sed -n '/^## Pre-commit sweep gates/,/^## Step 3:/p' "$REPO/agents/skills/done/SKILL.md" | grep "^Gates run in this order:" | grep -qF "plans-archive-twin" ) || fail "done skill: pre-commit enumeration missing plans-archive-twin"
for f in "$REPO/scripts/done_sweep_gates.sh" "$REPO/scripts/done_sweep_gates_lib.py" "$REPO/scripts/test_done_sweep_gates_lib.py" "$REPO/scripts/test_done_sweep_gates_wrapper.py"; do
  grep -q "ten absorbed" "$f"; rc=$?
  [ "$rc" -eq 0 ] && fail "stale ten-absorbed text survives in $f"
  [ "$rc" -eq 1 ] || fail "grep error rc=$rc sweeping $f"
done

# 5. Execute-plan hard gate (Task 3).
grep -qF "No foreign staging at landing" "$REPO/agents/skills/execute-plan/SKILL.md" || fail "execute-plan: foreign-staging hard gate missing"

# 6. Dedup probe wiring (Task 5).
grep -qF "Dedup probe:" "$REPO/agents/skills/receiving-review/SKILL.md" || fail "receiving-review: dedup probe field missing"
grep -qF "missing Dedup probe line" "$REPO/agents/skills/review-plan/SKILL.md" || fail "review-plan: probe lens missing"

# 7. Plans completed-home protocol (Task 4), licensed against the doc-registry write gate.
grep -qF "exactly one lifecycle state" "$REPO/docs/history/plans/completed/README.md" || fail "plans completed README: move-only protocol missing"
grep -qF "never an add-plus-keep copy" "$REPO/docs/history/plans/completed/README.md" || fail "plans completed README: move-only rule fragment missing"
( cd "$REPO" && python3 scripts/doc_registry_validator.py check-writes docs/history/plans/completed/README.md >/dev/null ) || fail "doc registry write licensing (the completed-home README must carry its registry row)"

# 8. Live-twin disposition landed (Task 6).
grep -q "^Status: rejected" "$REPO/docs/history/backlog/rejected/2026-09-27-release-skill-plan-live-twin.md" || fail "live-twin item not routed rejected"
if grep -q "^Status: open" "$REPO/docs/history/backlog/rejected/2026-09-27-release-skill-plan-live-twin.md"; then fail "live-twin item carries a twin Status: open line (the Status line must be replaced, not added)"; fi
grep -qF "release-skill-plan-live-twin" "$REPO/docs/maintenance/document-registry.md" || fail "registry row for the rejected routing missing"
( cd "$REPO" && python3 scripts/doc_registry_validator.py validate >/dev/null ) || fail "doc registry validator"

# 9. Shared-body runtime neutrality (Task 3 edits a gated shared skill body).
( cd "$REPO" && "$TEST_PY" -m pytest scripts/test_execute_plan_runtime.py -k shared_skill_bodies -q ) || fail "shared skill bodies no longer runtime neutral"

echo "ALL VALIDATION CHECKS PASS"
```

### Task 1: Done-sweep gates `foreign-staging` and `plans-archive-twin`

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/done_sweep_gates.sh`
- `scripts/check_maintenance_pins.sh` *(comment-only)*
- `scripts/test_done_sweep_gates_lib.py` *(test additions plus retarget of the ten-gate registry fixture and the report-shape fixture (pre-docs count to 8, new pre-commit leg asserting 5 lines))*
- `scripts/test_done_sweep_gates_wrapper.py` *(test updates if its assertions reference gate counts)*

Gate semantics (normative):

- `foreign-staging` (pre-commit phase): load the current run's manifest; if no manifest resolves, return a warning-skip result naming the reason (conservative degradation, mirroring the runner's other session-scoped gates). If a manifest resolves, build two sets: the start-dirt set, computed by a dedicated row normalizer keyed on the status letters (a row whose FIRST status letter (the index column) is `R` or `C`, or whose second (worktree) letter is `R` on runtimes that emit worktree-column rename rows, registers BOTH sides of the ` -> ` separator, each C-unquoted; any other row registers its body verbatim, C-unquoted; a path containing the literal separator is therefore parsed by letters, never by substring). This normalizer is new code beside `_unquote_porcelain_path`; it must NOT call `_porcelain_paths`, which keeps only the new side of a rename and detects renames by substring. The owned set is the union of the manifest's `owned_paths`, `owned_plan_paths`, and `owned_review_paths`. Take the staged path set as `git diff --cached --name-only --no-renames` (exposing both sides of staged renames) and C-unquote each line through `_unquote_porcelain_path`, so both representations compare over the same raw-path space. Every staged path that is in the start-dirt set and NOT in the owned set is a failure naming those paths with the message that landing must never stage foreign start-dirt. A staged path in the start-dirt set that IS in the owned set passes, and the pass result names every exempted owned path so a wrong claim is auditable at landing time; a staged path outside the start-dirt set passes (mid-session own staging; mid-session foreign writers are the judgment gate's concern in Task 2, whose pathspec-only rule is the commit-time net for them). The gate covers the mid-work staging window; the commit-time observation point is the Task 2 re-run duty.
- `plans-archive-twin` (pre-docs AND pre-commit phases): register the gate in both phase lists. Pre-docs catches a lingering twin before the docs work; the pre-commit run (observed by the Task 2 Step 3 re-run duty at the commit boundary) catches the creating landing itself, which was already past pre-docs when its own copy-not-move staging appeared. Scan the plans home from the `plans_dir` facts key; resolve the completed home from the existing `plans_completed_dir` facts resolution (the context's field, never a hardcoded default path), and `deferred/` and `rejected/` as `plans_dir` children (`ctx.plans_dir / "deferred"`, `ctx.plans_dir / "rejected"`, matching the existing rejected-dir precedent in the lib's readiness-candidate derivation). Never scan nothing silently: emit a named warning when a resolved state directory does not exist on disk, and a named warning when a facts key does not resolve and the default fell back. Scan the filesystem (covering untracked twins). For every file whose basename matches the dated plan shape `YYYY-MM-DD-*.md` and appears both at the plans root and inside any of the resolved state directories, fail naming both paths, whether the copies are byte-identical or different. A basename present in exactly one location passes; non-dated files (for example the new README) never trigger the gate.
- Ownership split with the existing pins suite (retention note, recorded at the code home too): `scripts/check_maintenance_pins.sh` `check_live_vs_archive_duplicates` stays the corpus-wide scheduled owner of the basename-collision class (plans AND backlog roots, non-dated names included); the new gate is the landing-time net over the plans home only, facts-key-driven, per origin 2's prescribed fix shape. Neither scanner may be removed as the duplicate of the other; the implementation carries this split as a comment on `gate_plans_archive_twin`, which also records the deliberate scope edge that a basename in two state directories with no root copy (completed plus rejected, say) is owned by neither scanner today and is the corpus-wide owner's candidate to absorb; a matching one-line comment above `check_live_vs_archive_duplicates` in `scripts/check_maintenance_pins.sh` names `gate_plans_archive_twin` as the landing-time plans-home net, this section as the corpus-wide owner, and this section as the designated absorber of that edge (comment-only touch, no behavior change).

- [ ] `test_done_sweep_gates_lib.py` foreign-staging fixtures: given a hermetic repo whose run manifest is seeded via the same production-shape helper the writer uses, with `start_porcelain` rows in verbatim porcelain form including the rename row `R  docs/tmp/foreign-note.md -> docs/tmp/renamed-note.md` and the quoted row `?? "docs/tmp/foreign note.md"`, where the staged foreign path is the rename's OLD side (`docs/tmp/foreign-note.md`, so a new-side-only normalizer stays GREEN and this fixture kills it), the quoted row's spaced path is staged bare and named unquoted in the expected message, a control-character start-dirt row is staged through its quoted `--name-only` emission and named unquoted, and a delete+add staged pair exposes the old side of a start-dirt row (the `--no-renames` staged set), expects `gate_foreign_staging` to fail naming the paths (stage via `git add -f`; the suite's repo fixture gitignores `/docs/`) [class: REPOSITORY_TEST]
- [ ] foreign-staging owned case: given the same start-dirt rows with `docs/tmp/foreign-note.md` present in the manifest's `owned_paths`, expects the gate to pass and the pass result to name the exempted owned path (the session's own Step-0 dirt, deliberately staged, auditable) [class: REPOSITORY_TEST]
- [ ] foreign-staging union case: given a start-dirt path exempted only via `owned_plan_paths`, expects the gate to pass (the owned set is the union of all three lists) [class: REPOSITORY_TEST]
- [ ] foreign-staging re-run case: given own mid-session staged paths that appear in no start-dirt row, expects the gate to pass [class: REPOSITORY_TEST]
- [ ] foreign-staging adopted-run case: given an adopted manifest whose `owned_paths` already carries `docs/tmp/foreign-note.md` and that path staged bare, expects the gate to pass [class: REPOSITORY_TEST]
- [ ] foreign-staging adopted-run unclaimed-creation case: given an adopted manifest whose predecessor created a mid-session file (now a start-dirt row of the retry via the unioned start-dirt record) that the adopting Step 0 claimed via `owned_paths`, expects the gate to pass; given the same shape unclaimed, expects a failure [class: REPOSITORY_TEST]
- [ ] foreign-staging writer-side wiring: run the write-manifest command with `--owned-path docs/tmp/foreign-note.md` and assert the written payload's `owned_paths` equals that list, mirroring the existing atomic-record flag-to-JSON test [class: REPOSITORY_TEST]
- [ ] foreign-staging writer-side warning: given a `--owned-path` claim matching no normalized start-dirt row, expects the writer to emit its named warning [class: REPOSITORY_TEST]
- [ ] foreign-staging writer-side adoption composition: given a write-manifest `--adopt` invocation with fresh claims over an adopted manifest carrying `owned_paths`, expects the written `owned_paths` to equal fresh claims plus adopted claims deduped [class: REPOSITORY_TEST]
- [ ] foreign-staging degradation: given no resolvable run manifest, expects a warning-skip result, never a crash and never a failure [class: REPOSITORY_TEST]
- [ ] `test_done_sweep_gates_lib.py` twin-gate fixtures: given a dated plan basename at the plans root and a byte-identical copy under the resolved completed home, expects `gate_plans_archive_twin` to fail naming both paths; given a byte-different copy, the same failure; given the root basename paired into `deferred/` and into `rejected/`, the same failure for each; given each basename present in exactly one state directory, expects a pass; given a non-dated root file, expects no finding; given a non-default `plans_completed_dir` facts key, expects the scan to read the configured home; given the key unresolvable, expects the named fallback warning, a scan of the default home, and a passing (warning-skip) result, never a failure; given a resolved state directory absent on disk, expects a named warning line and a pass, never a silent green and never a failure [class: REPOSITORY_TEST]
- [ ] `test_done_sweep_gates_lib.py` registry expectations updated, naming the two pre-existing tests that hard-code the old shape: `test_gate_registry_matches_absorbed_steps` retargets its phase-list slices, `GATES` key-set, and list-gates-output assertions (pre-docs 8, pre-commit 5, twelve distinct ids, the twin printed once at its first phase), and `test_report_shape_and_order` retargets the pre-docs line count to 8 and the pre-commit line count to 5 [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the two new gate names resolve to no implementation and the count and membership fixtures fail [class: REPOSITORY_TEST]
- [ ] Implement `gate_foreign_staging` and `gate_plans_archive_twin` per the normative semantics above, including: the `owned_paths` manifest list recorded at Step 0 via repeatable `--owned-path <path>` write-manifest claims (tolerant `from_dict` default like the existing owned lists); the write-manifest adoption branch composing `owned_paths` as the fresh claims plus the adopted manifest's `owned_paths` through the same dedup path as the existing lists, and composing the start-dirt record as the adopted manifest's `start_porcelain` unioned with the fresh snapshot so the predecessor's uncommitted output stays gate-visible; the writer-side cross-check that warns by name when an `--owned-path` claim matches no normalized start-dirt row; the ownership-split comment on `gate_plans_archive_twin`; the matching one-line comment above `check_live_vs_archive_duplicates` in `scripts/check_maintenance_pins.sh`; and the `list-gates` sub-command change to print each gate id once, deduped at its first phase (today it prints the PRE_DOCS+PRE_COMMIT concatenation); register foreign-staging in the pre-commit phase list and plans-archive-twin in BOTH the pre-docs and pre-commit phase lists, both in the `GATES` mapping, and in the runner usage plus header comments (twelve distinct gate ids, the twin running in both phases) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: both suites pass [class: REPOSITORY_TEST]
- [ ] Commit: `feat: done-sweep foreign-staging and plans-archive-twin gates` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Done skill landing-closeout arms

Files:
- `agents/skills/done/SKILL.md`

Insertions, all inside `agents/skills/done/SKILL.md`:

1. Step 0 (manifest write): add the repeatable `--owned-path <path>` claim to the write-manifest flag enumeration beside `--owned-review`/`--foreign-review`, with the duty to record every start-dirt path this run may stage (the session's own baseline dirt, and for an adopting run also the adopted run's uncommitted output per the adoption re-derivation record, after re-reviewing the adopted manifest's inherited `owned_paths` claims: an inherited claim the re-derivation does not support is never exercised (leave its path unstaged and record the disowned claim in the session notes; the writer unions inherited `owned_paths` verbatim and there is no drop flag)); claims are load-bearing only against Step-0-recorded rows (mid-session creations pass the gate without claims), and the gate-side pass result naming exempted owned paths is the audit of record for baseline-dirt claims. Also add `--owned-path` to the stale-deployment signature enumeration's recognized-flags list.
2. Step 3 (Commit Uncommitted Changes), beside the existing pre-commit guard bullet: a named foreign-dirt gate paragraph that explicitly supersedes Step 3 item 0's baseline arm for landing staging, with one disposition ladder: the owned list derives from the run manifest's owned claims plus the paths this session created or modified during the run, attributed from the session's own records (the session-notes baseline record, the session's in-session edit records, and for adopted runs the adoption re-derivation record); unclaimed start-dirt is foreign here too: the item-0 ask for user-owned baseline dirt happens at Step 0, where an approval is recorded as an `--owned-path` claim before staging, and baseline dirt discovered unclaimed at landing is reported and left unstaged (it stays for the next run); a live peer session's uncommitted work is reported by path and the landing aborts (waiting is futile while this run holds the done lock the peer's own landing would need); a foreign path is never staged.
3. Step 3: the commit-time observation duty: after staging and before committing, re-run the pre-commit phase so the `foreign-staging` and `plans-archive-twin` gates observe the final staged set and the plans tree at the commit boundary, and record the re-run's exit line in the session notes beside the registry digest record.
4. Step 3: the registry detection arms (below).
5. Item 0 gains the landing-supersession sentence; item 5's directory-wide-add carve-out ("unless the user explicitly requests it") is scoped to exclude landing closeouts; Step 4 item 3's cross-reference to Step 3 item 0's discipline is updated to name the non-landing fallback scope.
6. The pre-docs and pre-commit "Gates run in this order" enumeration paragraphs: the pre-docs enumeration reads `docs-tmp-sweep, plans-archive-twin` at the insertion point, and the pre-commit enumeration's `Gates run in this order:` line names both new gate ids as entries in the paragraph's existing entry shape (the Validation block witnesses both ids on that line by region); the same bullet carries the archive-move obligation sentence as its closing sentence; one fix-guidance bullet per new gate is added, mirroring the existing per-gate guidance shape; the foreign-staging guidance carries the fragment "staged paths recorded as start-dirt but not owned" and the plans-archive-twin guidance carries the ownership-and-tracking-scoped remedy: "a twin this session created resolves by true rename in-landing; for a byte-different pair, diff the two sides first and reconcile the root side's extra content into the archive side (or ask the user) before any removal; an untracked unclaimed start-dirt twin resolves by unstaged removal of the plans-root side, never the archive side; a tracked plans-root side that is dirty at Step 0 resolves at the next Step 0 via an `--owned-path` claim followed by a staged deletion committed in that landing's pathspec (unstaged removal of a tracked side leaves the twin committed); a clean tracked side may resolve in-landing by a staged deletion without a claim (its path is not start-dirt), re-verifying the side is clean against HEAD immediately before the deletion (if it went dirty mid-window, route to the tracked-dirty arm; never delete with force); a run deferring resolution to the next Step 0 records a recorded stop".

The insertions must carry, verbatim, these obligation sentences (the Validation Commands pin each):

- "Before staging, run the foreign-dirt gate: list uncommitted paths (staged, unstaged, untracked) and compare them against this session's owned path list, which comprises the run manifest's owned claims and every path this session created or modified during the run, attributed from the session's own records; every uncommitted path outside the list and not attributable to this session's recorded work is foreign: report it by path; unclaimed baseline dirt is reported and left unstaged for the next run, and a foreign path attributable to a live peer session aborts the landing (waiting is futile while this run holds the done lock the peer's own landing would need); never stage a foreign path."
- "Landing commits use explicit pathspecs only; a directory-wide add in a landing closeout is a gate violation."
- "After staging and before committing, re-run the pre-commit phase so the foreign-staging and plans-archive-twin gates observe the final staged set and the plans tree at the commit boundary, and record the re-run's exit line in the session notes beside the registry digest record."
- "When computing a document-registry edit, record the file's sha256 as the registry digest alongside the edit (in the session notes) before further edits."
- "Before staging a landing commit that includes the document registry, verify the file's working-tree bytes still hash to the recorded registry digest; on a mismatch a concurrent writer intervened: stop, re-read the file, re-apply the session's rows onto the freshly read bytes (never write a pre-computed block; re-apply only rows not already present, matched byte-exact as full registry lines, not by row token), then confirm the written bytes by re-reading, recapture the registry digest, re-run the re-grep arm, re-stage, and re-run the pre-commit phase and the staged-blob check before committing."
- "Before committing, re-grep that every registry row this session added is still present in the file being staged; a missing row means a concurrent write clobbered it: abort and reconcile instead of committing the loss."
- "Immediately before committing, re-hash the working-tree registry bytes against the staged blob (`git ls-files -s`); on divergence a write landed after staging: re-run the verify arm (re-read, re-apply the session's rows not already present, matched byte-exact as full registry lines, onto the fresh bytes, confirm by re-reading, recapture the digest, re-run the re-grep arm, re-add) or abort."
- "Archiving a plan is a move, never an add-plus-keep; the plans-archive-twin gate fails any landing while a twin from an earlier run sits unresolved at the plans root."

- [ ] Insert the Step 0 `--owned-path` claim and duty into the manifest-write flag enumeration, and add `--owned-path` to the stale-deployment signature enumeration's recognized-flags list [class: IMPLEMENTATION_REQUIRED]
- [ ] Insert the foreign-dirt gate paragraph (with the item 0 supersession and disposition ladder) and the Step 3 re-run duty at the Step 3 anchor, carrying the obligation sentences verbatim [class: IMPLEMENTATION_REQUIRED]
- [ ] Insert the registry capture, verify, re-grep, and staged-blob arms carrying their obligation sentences verbatim [class: IMPLEMENTATION_REQUIRED]
- [ ] Reconcile the superseded item 0 text, item 5's carve-out scope, and the Step 4 item 3 cross-reference [class: IMPLEMENTATION_REQUIRED]
- [ ] Update the pre-docs and pre-commit gate enumerations and add the two fix-guidance bullets carrying their prescribed fragments verbatim [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the Validation Commands check 4 (all check-4 done-skill pins go GREEN); confirm the pins are absent before the edits (authoring record shows RED) [class: REPOSITORY_TEST]
- [ ] Commit: `feat: done skill foreign-dirt gate and registry detection arms` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Execute-plan hard gate entry

Files:
- `agents/skills/execute-plan/SKILL.md`

Add one bullet to the Hard Gates list naming the landing-side contract, bound through the done run that every closeout commit lands through; wording must stay runtime-neutral (the shared-body forbidden-term gate covers this file):

- "No foreign staging at landing: each closeout commit lands through a done run whose foreign-staging gate observes the staged set at the commit boundary, with only this run's owned paths staged by explicit pathspec."

- [ ] Add the Hard Gates bullet carrying the sentence "No foreign staging at landing" verbatim [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the shared-body runtime-neutrality test and Validation Commands check 5 and 9 [class: REPOSITORY_TEST]
- [ ] Commit: `feat: execute-plan names the foreign-staging landing gate` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Plans completed-home move-only protocol

Files:
- `docs/history/plans/completed/README.md` *(new)*

Write the protocol README for the plans tree: the written-home role is modeled on the backlog counterpart, but the content is this plan's own (the backlog counterpart carries an empty-inbox protocol, not a move-only one). Scope the normative rule to the completed home itself and reference the `deferred/` and `rejected/` home READMEs as their homes' own carriers of their arrival disciplines (pointers, not restatements). Required content: this directory holds completed plans; an archive transition is a rename of the live path (`git mv`), never an add-plus-keep copy; a plan exists in exactly one lifecycle state at a time, and the plans root must not retain an archived basename; the done sweep's `plans-archive-twin` gate fails a closeout that leaves a dated plan basename at the plans root and in an archive state at the same time, and the pins suite owns the corpus-wide post-hoc check (one line; scanner-absorption policy stays at the code homes). Because the README lands under the immutable completed-history home, the same commit appends its ownership-registry row (mirroring the backlog counterpart's completed-inbox README row) so the doc-registry write gate licenses it.

- [ ] Create `docs/history/plans/completed/README.md` with the required content, carrying the fragments "exactly one lifecycle state" and "never an add-plus-keep copy" verbatim [class: IMPLEMENTATION_REQUIRED]
- [ ] Append the ownership-registry row for the new README in `docs/maintenance/document-registry.md` in the same commit, and run `python3 scripts/doc_registry_validator.py check-writes docs/history/plans/completed/README.md` to prove the write is licensed [class: IMPLEMENTATION_REQUIRED]
- [ ] Run Validation Commands check 7 [class: REPOSITORY_TEST]
- [ ] Commit: `docs: plans completed-home move-only protocol README` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Backlog filing dedup probe

Files:
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/review-plan/SKILL.md`

In the receiving-review Backlog capture required-content list, add one required bullet: "`Dedup probe:` the keyword search run over the open backlog corpus (item filenames plus Problem bodies), the nearest item(s) found, and either the distinction from each or an explicit merge recommendation." In the review-plan skill's finding-synthesis guidance, add the panel lens: "When a reviewed plan promotes or files backlog items, check each newly filed item carries its Dedup probe line; a missing Dedup probe line is a Low finding, not a gate."

- [ ] Add the `Dedup probe:` required-content bullet to the Backlog capture list, carrying the field label verbatim [class: IMPLEMENTATION_REQUIRED]
- [ ] Add the review-plan panel lens sentence carrying "missing Dedup probe line" verbatim [class: IMPLEMENTATION_REQUIRED]
- [ ] Run Validation Commands check 6 [class: REPOSITORY_TEST]
- [ ] Commit: `feat: backlog filing dedup probe required and review-checked` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Disposition the release-skill live-twin item (duplicate of origin 2)

Files:
- `docs/history/backlog/rejected/2026-09-27-release-skill-plan-live-twin.md` *(new at this destination; `git mv` from `docs/history/backlog/`)*
- `docs/maintenance/document-registry.md` *(one row append)*

The item witnessed the same release-skill live-vs-archive twin as origin 2, and its fix scope is already discharged: the dedup pass removed the live copy and the registry row `release-skill` records the removal. Close it as a duplicate with the baseline re-verified, so the corpus keeps the witness without keeping an open duplicate.

- [ ] Verify baseline: `test ! -e docs/history/plans/2026-09-26-release-skill.md` and `bash scripts/check_maintenance_pins.sh` exits 0 [class: REPOSITORY_TEST]
- [ ] Replace the existing `Status: open` line with `Status: rejected (<execution date>; duplicate of docs/history/backlog/2026-09-27-plans-archive-move-only-gate.md: same witnessed live-vs-archive twin, removed by the 2026-09-27 dedup pass, pins exit 0 re-verified at disposition)`; the body apart from that one replaced line stays byte-intact; then `git mv` the file to `docs/history/backlog/rejected/` [class: IMPLEMENTATION_REQUIRED]
- [ ] Append the ownership-registry row for the rejected item (state: rejected, duplicate reason) and run `python3 scripts/doc_registry_validator.py validate` [class: IMPLEMENTATION_REQUIRED]
- [ ] Run Validation Commands checks 2 and 8 [class: REPOSITORY_TEST]
- [ ] Commit: `docs: close release-skill live-twin item as duplicate of the move-only origin` [class: IMPLEMENTATION_REQUIRED]

## Origins dispositions

All four origins executed in full by this plan's execution (2026-09-28, exec review r2 ready=yes zero blocking); each item file is fold-then-deleted, its scope of record preserved by this archived plan:

- `docs/history/backlog/2026-09-27-concurrent-landing-foreign-staging-sweep.md`: folded - foreign-staging done-sweep gate plus the done skill foreign-dirt judgment gate (Tasks 1-2) and the execute-plan Hard Gates entry (Task 3).
- `docs/history/backlog/2026-09-27-plans-archive-move-only-gate.md`: folded - plans-archive-twin gate plus the completed-home move-only protocol README (Tasks 1 and 4).
- `docs/history/backlog/2026-09-27-registry-concurrent-landing-lost-update.md`: folded - registry digest capture-and-verify, re-grep, and staged-blob arms in the done skill (Task 2).
- `docs/history/backlog/2026-09-27-backlog-filing-dedup-probe.md`: folded - Dedup probe required-content bullet and review-plan panel lens (Task 5).

## Disposition of migrated backlog items

Fold-then-delete consult (execution 2026-09-28): the origin item files below were deleted from the open backlog top level after their scope landed; dispositions recorded in the Origins dispositions section above.

- docs/history/backlog/2026-09-27-concurrent-landing-foreign-staging-sweep.md
- docs/history/backlog/2026-09-27-plans-archive-move-only-gate.md
- docs/history/backlog/2026-09-27-registry-concurrent-landing-lost-update.md
- docs/history/backlog/2026-09-27-backlog-filing-dedup-probe.md
