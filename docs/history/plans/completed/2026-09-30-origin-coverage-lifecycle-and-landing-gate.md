# Plan: Origin coverage lifecycle and duplicate-origin landing gate

Backlog origin: docs/history/backlog/2026-09-30-origin-coverage-lifecycle-and-landing-gate.md
Driving force: automation
Plan review record: the staging series docs/reviews/2026-09-30-plan-review-origin-coverage-lifecycle-and-landing-gate-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Landing a plan flips its open backlog origins to a covered state naming the covering plan, and a second plan citing the same origin is refused at landing and at execution readiness until the duplicate is reconciled to one plan.

- After this plan, a plan's landing closeout marks each named open backlog origin `Status: covered (<plan path>)` in the same landing commit, so any reader of the backlog (survey, human, re-triage) sees the covering plan without grepping the plans tree.
- A landing or execution readiness gate refuses when another plan already cites the same origin, naming the covering plan and the first-landed-wins remedy, so the 2026-09-30 collision class (two plans authored, landed, and executed for the scope-leak origin) is caught mechanically instead of by an accidental `git worktree list`.
- The maintenance survey stops offering covered origins as authoring targets while covered-not-yet-executed origins stay visible to execution selection and re-triage, because `covered` is a distinct classification, never a closed one.

Gate delta: adds one refusal class (duplicate-origin refusal at landing and at execution readiness, carried by two new origins-checker modes), one backlog status value (`covered`, with the covering-plan witness the value carries), and one corpus warn (a covered origin whose covering plan is no longer top-level); each addition is priced by the witnessed integrity failure - the 2026-09-30 duplicate execution of origin `2026-09-29-execute-plan-prior-invocation-scope-leak` by two independently authored plans (`0f4b7cf5`/`f97277f9` and the peer's `invocation-scope-revalidation`, both in `docs/history/plans/completed/`); removes nothing; the survey change is a reading clause on the existing plan-coverage read, not a new gate.

## Terms

- **Origin**: a backlog item file a plan names in its header scope (the `Backlog origins (scope of record):` block or the singular `Backlog origin:` line).
- **Covering plan**: a plan whose header scope names an origin; the covering plan named by a covered status is the first plan that landed citing it.
- **Covered**: an origin header `Status:` value of the form `covered (<plan path>)`, written at the covering plan's landing; distinct from `open` and from the execution-time fold.
- **Origins-closure checker**: `scripts/check_plan_origins_closed.py`.

## Assumptions

- assume the origins-closure checker parses the plural block and the `Backlog origin:` singular line but NOT the bare `Origin:` line the witnessed covering plan actually used (`docs/history/plans/completed/2026-09-30-execute-plan-prior-choice-scope-binding.md` line 2 carries a `[github: ...] Origin: docs/history/backlog/...` header); basis: probed current bytes on 2026-09-30 - the origin item's shape-normalization demand stands for the bare shape, so this plan's coverage extractor is a superset of `extract_origin_basenames` that additionally parses bare `Origin:` lines in the plan's header region (title line through the first `## ` heading), while the archive gate's existing grammar stays untouched.
- assume the covered flip rides the plan-file landing commit rather than a separate commit; basis: mirrors the execution-time fold-then-delete, which rides the archive commit (execute-plan SKILL.md closeout), keeping the plan and its origin witnesses atomic.
- assume `covered` never enters the checker's pass states (`completed`/`closed`/`rejected`); a covered-not-yet-executed origin still owes the execution-time fold, so pass semantics are unchanged.
- assume the maintenance blueprints in `agents/skills/maintenance/prompt-templates.md` stay byte-untouched; the landing duty rides the plans skill that every authoring session runs; basis: the pins suite pins those blueprints and the cycle-7 precedent of wiring by reference into the skills layer.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: Landing a plan now covers its backlog origins and a duplicate-origin plan is refused at landing or execution, so two lanes can no longer author, land, and execute plans for the same origin unnoticed - the automation force removes the manual reconcile-note routine the 2026-09-30 collision needed.

**Before (today):** On 2026-09-30, two lanes independently authored plans for `2026-09-29-execute-plan-prior-invocation-scope-leak`. The first landed (`0f4b7cf5`); the origin item stayed `Status: open` because nothing flips it at landing. A hand-written coverage note landed on main, but the peer's worktree pre-dated the note, so the peer reviewed, landed, and EXECUTED its duplicate (`docs/history/plans/completed/2026-09-30-execute-plan-invocation-scope-revalidation.md`) without ever seeing it. Reconciliation happened only because a session happened to run `git worktree list`.

**After (this plan):** The same first lane lands its plan and its landing closeout runs `python3 scripts/check_plan_origins_closed.py --mark-covered <plan>`, which rewrites the origin's header to `Status: covered (docs/history/plans/2026-09-30-execute-plan-prior-choice-scope-binding.md)` inside the landing commit. The peer's landing closeout first runs `--check-coverage <plan>`, sees the origin is covered by another plan, exits non-zero naming the covering plan, and the landing is refused with the remedy: first-landed wins - fold the later plan into the covering plan as an amendment, or reject the later plan as superseded. If the duplicate still slips through, the execution session's Step 0.5 gate runs the same check and stands the run down before any implement sub-agent launches.

## Evaluation Criteria

**Quality dimensions:**

- correctness (exit-code contract): each new checker mode returns 0 on success/no-op, 1 on a conflict (with the covering plan named on stdout/stderr), and 2 on tool error (unreadable tree, unresolvable scan root); a conflict never mutates bytes; a missing facts key resolves through the shared warn-and-default fallback (`resolve_dir`) exactly like the existing modes.
- fail-closed behavior: `--mark-covered` refuses (exit 1, bytes unchanged) when an origin is already covered by a different plan; it flips only header `Status:` lines of top-level items and only from `open`.
- compatibility: the existing unittest suite and the live corpus scan keep their current outcomes for every pre-existing input (no pass-state change; `covered` is a new classification, not a closed one).

**Done when:**

- `python3 -m unittest scripts.test_check_plan_origins_closed` exits 0 including the new coverage tests.
- The Validation Commands block below exits 0 end to end.
- `python3 scripts/check_plan_origins_closed.py` corpus mode exits 0 over the live tree with no new warnings attributable to this plan.

**Ship when:**

- None; repository machinery only.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `scripts/check_plan_origins_closed.py`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/maintenance/SKILL.md`

**Tests:**

- `scripts/test_check_plan_origins_closed.py`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `agents/skills/maintenance/prompt-templates.md`; byte-pinned child blueprints (pins suite) - the landing duty rides the plans skill instead.
- `scripts/plan_readiness.py`; the certification oracle stays a byte-property gate; corpus-state coverage wiring lives at its two consumers (landing closeout, execution Step 0.5).

## Validation Commands

```bash
# Task 1: checker unit suite (new coverage tests included)
python3 -m unittest scripts.test_check_plan_origins_closed || { echo "FAIL: unit suite"; exit 1; }

# Task 1: mode contracts on a throwaway repo-shaped fixture (fail-closed, three-way exit split; sequenced so each expectation matches the scan scope: plan B is written only after plan A's clean gate and covered flip)
WORK="$(mktemp -d)"
mkdir -p "$WORK/docs/history/backlog" "$WORK/docs/history/plans" "$WORK/docs/history/plans/completed"
printf 'Status: open\n' > "$WORK/docs/history/backlog/2026-01-01-widget.md"
printf '# Plan: A\n\nBacklog origin: docs/history/backlog/2026-01-01-widget.md\n' > "$WORK/docs/history/plans/2026-01-01-a.md"
python3 scripts/check_plan_origins_closed.py --check-coverage docs/history/plans/2026-01-01-a.md --repo-root "$WORK" --backlog-dir docs/history/backlog --active-plans-dir docs/history/plans --plans-dir docs/history/plans/completed > "$WORK/out1.txt" 2>&1
[ $? -eq 0 ] || { echo "FAIL: clean single-plan coverage must exit 0"; exit 1; }
python3 scripts/check_plan_origins_closed.py --mark-covered docs/history/plans/2026-01-01-a.md --repo-root "$WORK" --backlog-dir docs/history/backlog --active-plans-dir docs/history/plans --plans-dir docs/history/plans/completed || { echo "FAIL: mark-covered must exit 0"; exit 1; }
grep -qF 'Status: covered (docs/history/plans/2026-01-01-a.md)' "$WORK/docs/history/backlog/2026-01-01-widget.md" || { echo "FAIL: covered witness must record the repo-relative plan path"; exit 1; }
printf '# Plan: B\n\nBacklog origin: docs/history/backlog/2026-01-01-widget.md\n' > "$WORK/docs/history/plans/2026-01-01-b.md"
python3 scripts/check_plan_origins_closed.py --check-coverage docs/history/plans/2026-01-01-b.md --repo-root "$WORK" --backlog-dir docs/history/backlog --active-plans-dir docs/history/plans --plans-dir docs/history/plans/completed > "$WORK/out2.txt" 2>&1
[ $? -eq 1 ] || { echo "FAIL: duplicate-origin coverage must exit 1"; exit 1; }
grep -q "2026-01-01-a.md" "$WORK/out2.txt" || { echo "FAIL: conflict output must name the covering plan"; exit 1; }
python3 scripts/check_plan_origins_closed.py --mark-covered docs/history/plans/2026-01-01-b.md --repo-root "$WORK" --backlog-dir docs/history/backlog --active-plans-dir docs/history/plans --plans-dir docs/history/plans/completed > "$WORK/out3.txt" 2>&1
[ $? -eq 1 ] || { echo "FAIL: conflicting mark-covered must exit 1"; exit 1; }
rm -rf "$WORK"

# Tasks 2-4: per-file wiring obligations (each file's own gate, one invocation each; every token below is verified absent from its file at authoring time, so a skipped task fails its grep)
grep -q -- "--check-coverage" agents/skills/plans/SKILL.md || { echo "FAIL: plans skill landing duty missing"; exit 1; }
grep -q -- "--mark-covered" agents/skills/plans/SKILL.md || { echo "FAIL: plans skill covered-flip duty missing"; exit 1; }
grep -q "first-landed wins" agents/skills/plans/SKILL.md || { echo "FAIL: precedence rule missing"; exit 1; }
grep -q -- "--check-coverage" agents/skills/execute-plan/SKILL.md || { echo "FAIL: execution coverage gate missing"; exit 1; }
grep -q "value reads" agents/skills/maintenance/SKILL.md || { echo "FAIL: survey covered-awareness missing"; exit 1; }
grep -q "never reported as plan-uncovered-with-archived-coverage" agents/skills/maintenance/SKILL.md || { echo "FAIL: survey warn-arm awareness missing"; exit 1; }

# Corpus compatibility: the live scan passes unchanged
python3 scripts/check_plan_origins_closed.py || { echo "FAIL: corpus scan"; exit 1; }

# Negative control: the fixture obligations abort on failure by construction
# (every command is wrapped with an explicit exit-1 on miss). The per-file wiring
# greps use tokens that did not exist in their files at authoring time (verified
# absent 2026-09-30), so each grep is RED before its task edits the file and
# GREEN only after - a skipped task fails the block per development lesson #191.
```

### Task 1: Covered state and coverage modes in the origins checker

Files:

- `scripts/check_plan_origins_closed.py`
- `scripts/test_check_plan_origins_closed.py`

Evidence:

- `python3 -m unittest scripts.test_check_plan_origins_closed`; covers the classification, coverage-gate, mark-covered, and corpus-compat criteria below.
- `python3 scripts/check_plan_origins_closed.py --check-coverage <fixture-plan>`; covers the conflict exit-code contract on a two-plan fixture.

- [ ] `TestOriginCoverage#test_classify_covered_status`; given a top-level item whose header carries `Status: covered (docs/history/plans/2026-01-01-a.md)`, expects `classify_origin` returns state `covered` with detail naming that plan [class: REPOSITORY_TEST]
- [ ] `TestOriginCoverage#test_covered_is_not_closed`; given the same item, expects `covered` is not in the pass states and corpus mode does not report it as closed [class: REPOSITORY_TEST]
- [ ] `TestOriginCoverage#test_check_coverage_clean`; given exactly one plan citing an open origin, expects `--check-coverage` exits 0 with no conflict output [class: REPOSITORY_TEST]
- [ ] `TestOriginCoverage#test_check_coverage_conflict`; given a second plan citing the same origin basename, expects exit 1 and output naming the covering plan path and the first-landed-wins remedy [class: REPOSITORY_TEST]
- [ ] `TestOriginCoverage#test_check_coverage_excludes_self`; given the declaring plan as the only citer, expects no self-conflict (exit 0) [class: REPOSITORY_TEST]
- [ ] `TestOriginCoverage#test_check_coverage_scans_completed_and_rejected`; given the only other citer under the completed or rejected plans directories, expects exit 1 naming it [class: REPOSITORY_TEST]
- [ ] `TestOriginCoverage#test_check_coverage_scans_deferred`; given the only other citer under the deferred plans directory (`<active>/deferred`), expects exit 1 naming it and its parked state [class: REPOSITORY_TEST]
- [ ] `TestOriginCoverage#test_coverage_extractor_parses_bare_origin_header`; given a plan whose header region (title through the first `## ` heading) carries `[github: https://example.com/repo] Origin: docs/history/backlog/2026-01-01-widget.md`, expects the coverage extractor returns that basename (superset of `extract_origin_basenames`) [class: REPOSITORY_TEST]
- [ ] `TestOriginCoverage#test_coverage_extractor_ignores_bare_origin_in_body`; given a plan mentioning `Origin: docs/history/backlog/2026-01-01-widget.md` only below the first `## ` heading, expects the coverage extractor returns no basename from it [class: REPOSITORY_TEST]
- [ ] `TestOriginCoverage#test_active_and_rejected_dir_resolution`; given no explicit flag and no facts key, expects the coverage scan resolves the active plans directory from the new `--active-plans-dir` argument, then the facts key `plans_dir`, then the default `docs/history/plans`, derives the rejected plans archive as `<active>/rejected` and the deferred directory as `<active>/deferred` (warn-and-default fallback per the shared `resolve_dir`), and resolves the completed-plans conflict surface through the existing `--plans-dir` argument with facts key `plans_completed_dir` and default `docs/history/plans/completed` [class: REPOSITORY_TEST]
- [ ] `TestOriginCoverage#test_mark_covered_flips_open`; given an open top-level origin and a plan naming it, expects the header line becomes `Status: covered (<plan path>)` and exit 0 [class: REPOSITORY_TEST]
- [ ] `TestOriginCoverage#test_mark_covered_idempotent_same_plan`; given the origin already covered by the same plan, expects exit 0 and no byte change [class: REPOSITORY_TEST]
- [ ] `TestOriginCoverage#test_mark_covered_refuses_conflict`; given the origin covered by a different plan, expects exit 1, bytes unchanged, covering plan named [class: REPOSITORY_TEST]
- [ ] `TestOriginCoverage#test_mark_covered_skips_non_open`; given origins that are completed, rejected, closed, or folded (file absent), expects each skipped with a reported reason and exit 0 [class: REPOSITORY_TEST]
- [ ] `TestOriginCoverage#test_corpus_covered_with_live_plan_quiet`; given a covered item whose covering plan is top-level, expects corpus mode emits no warning for it [class: REPOSITORY_TEST]
- [ ] `TestOriginCoverage#test_corpus_covered_without_live_plan_warns`; given a covered item whose covering plan is gone from the top-level plans directory, expects one warning naming the covering plan [class: REPOSITORY_TEST]
- [ ] Run → expect RED: `python3 -m unittest scripts.test_check_plan_origins_closed -k TestOriginCoverage` [class: REPOSITORY_TEST]
- [ ] Implement the `covered` classification (`STATUS_COVERED_VALUE_RE` over the header status value, detail carrying the parenthesized plan path), the resolution surfaces the new modes need (a `--active-plans-dir` argument resolving through the shared `resolve_dir` with facts key `plans_dir` and default `docs/history/plans`; the rejected plans archive derived as `<active>/rejected` and the deferred directory as `<active>/deferred`; the completed-plans conflict surface reusing the existing `--plans-dir` argument with facts key `plans_completed_dir` and default `docs/history/plans/completed`), a coverage-scoped origin extractor that is a superset of `extract_origin_basenames` (it additionally parses bare `Origin:` lines - including a `[github: ...]` prefix - whose `.md` path is a backlog reference, scoped to the plan's header region so body prose never matches), the `--check-coverage <plan>` mode (scope-only extraction over the active + deferred + completed + rejected plans directories, self-excluded, conflicts listed with a per-citer-state remedy line: an active covering plan gets the first-landed-wins fold-or-reject remedy, a completed citer gets supersede-or-explicit-revival guidance, a rejected citer gets the revival-is-a-new-decision note, a deferred citer gets revive-or-explicitly-supersede guidance), and the `--mark-covered <plan>` writer mode (flip `open` top-level items only, preserve the line's non-status prefix, record the witness as the plan path repo-relative to the resolved repo root, idempotent for the same plan, refusal on a different-plan witness, skips reported for completed/rejected/closed/folded) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `python3 -m unittest scripts.test_check_plan_origins_closed` [class: REPOSITORY_TEST]
- [ ] Commit: `feat: origins checker covered state, coverage gate, mark-covered` [class: REPOSITORY_TEST]

### Task 2: Landing closeout duty in the plans skill

Files:

- `agents/skills/plans/SKILL.md`

Evidence:

- `grep -c "check-coverage" agents/skills/plans/SKILL.md`; covers the landing-duty wiring criterion.

- [ ] Add one bullet at the head of `## Plan Lifecycle`: when a newly authored plan lands, first run the coverage gate `python3 scripts/check_plan_origins_closed.py --check-coverage <repo-relative plan path>` (resolve the script repo-local first, then the deployed `~/.ai-playbook/scripts/` copy); a non-zero exit is a hard gate that refuses the landing, naming the covering plan and the remedy: first-landed wins - fold the later plan into the covering plan as an amendment, or reject the later plan as superseded through the rejected archive; after the gate passes, run `--mark-covered <repo-relative plan path>` so the covered flip of each named open origin rides the landing commit with the covering-plan witness recorded repo-relative [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the Validation Commands Task 2-4 grep block [class: REPOSITORY_TEST]
- [ ] Commit: `feat: plans skill landing closeout covers origins, refuses duplicates` [class: REPOSITORY_TEST]

### Task 3: Duplicate-origin gate at execution readiness

Files:

- `agents/skills/execute-plan/SKILL.md`

Evidence:

- `grep -c "check-coverage" agents/skills/execute-plan/SKILL.md`; covers the execution-gate wiring criterion.

- [ ] Add one paragraph to `### Step 0.5: Plan readiness gate (hard gate, before any task implementation)` in `agents/skills/execute-plan/SKILL.md`, immediately after the paragraph beginning `Exit 0 means`: run the same coverage gate (`python3 scripts/check_plan_origins_closed.py --check-coverage <repo-relative plan path>` with the same repo-local-then-deployed resolution); ANY non-zero exit is a hard gate that stops the run before any implement sub-agent launches - an exit 1 conflict names the covering plan and the remedy (first-landed wins - fold the later plan into the covering plan as an amendment, or reject the later plan as superseded), while any other non-zero exit (tool error, crash) carries the investigate-before-rerun rule like the readiness validator's narrow deployment-gap signature; the deployment-gap copy remedy is sibling-aware, mirroring the validator remedy the paragraph already cites: `cp scripts/check_plan_origins_closed.py scripts/facts_paths.py ~/.ai-playbook/scripts/` with `facts_paths.py` copied symlink-preserving (`cp -P`), never a bare single-file copy [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the Validation Commands Task 2-4 grep block [class: REPOSITORY_TEST]
- [ ] Commit: `feat: execution readiness refuses duplicate-origin plans` [class: REPOSITORY_TEST]

### Task 4: Maintenance survey covered-awareness

Files:

- `agents/skills/maintenance/SKILL.md`

Evidence:

- `grep -c "value reads" agents/skills/maintenance/SKILL.md`; covers the survey wiring criterion (the token pair exists only after the edit; verified absent at authoring time).

For Task 4:

- `grep -c "never reported as plan-uncovered-with-archived-coverage" agents/skills/maintenance/SKILL.md`; covers the warn-arm wiring criterion (verified absent at authoring time).

- [ ] Extend the `Plan coverage` survey bullet to carry the exact sentence: an item whose header `Status:` value reads `covered` is plan-covered regardless of the filename grep, with the covering plan named in the status value as the witness [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend the `Archived-coverage warn arm` survey bullet to carry the exact sentence: a covered item is never reported as plan-uncovered-with-archived-coverage (it carries its covering-plan witness in its own header); the corpus warn for a covered item fires only when its covering plan is no longer top-level [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the Validation Commands Task 2-4 grep block [class: REPOSITORY_TEST]
- [ ] Commit: `feat: maintenance survey reads covered origins` [class: REPOSITORY_TEST]

### Task 5: Corpus compatibility and reference closure

Files:

- None new; verification-only task over the live tree (any stale reference found is reported in the run log and filed as a follow-up, never edited here).

Evidence:

- `python3 scripts/check_plan_origins_closed.py`; covers the corpus-compat criterion.

- [ ] Run the corpus scan over the live tree and verify exit 0 with no new warnings attributable to this plan [class: REPOSITORY_TEST]
- [ ] Sweep the repository read-only for stale references to the origins checker's surface (`README.md`, `docs/` guides) naming only the archive-gate mode; report every hit in the run log with its path (zero edits in this task) [class: REPOSITORY_TEST]
