# Plan: Review-loop exit condition and metrics

Backlog origin: docs/history/backlog/2026-09-28-review-loop-exit-condition-and-metrics.md
Driving force: simplicity + new-capability
Plan review record: the staging series docs/reviews/2026-09-28-plan-review-review-loop-exit-condition-metrics-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Review loops stop by convergence instead of chasing unattainable zero-finding rounds, and their cost is measured instead of guessed.

- Every review-loop surface states the blocking-only exit as the mechanical rule and carries advisory stop-and-escalate guidance, so ordinary (non-blocking) findings are recorded once and never chased with new rounds.
- Projects resolving `personal` get the strict package mechanically: default two review rounds, hard cap of three, simplify-or-rewrite at the cap, and no cap-closure terminal shape.
- Projects resolving `standard` keep today's round budgets unchanged, with the explicit recorded decision point that their caps move only after their own measured data justifies it.
- The maintenance loop's weekly rider publishes review-corpus metrics (findings-per-round decay, ready-rate per round, cap-exhaustion share) segmented by plan-complexity band, from data the corpus already stages.

## Terms

- Strictness class: the per-project loop policy class, `personal` or `standard`, resolved once at loop start from the project facts document (canonical resolution procedure lives in `review-plan`, Project strictness classes).
- `personal_projects_root`: the facts TOML key naming the operator's personal repositories root; a repository inside it resolves `personal`; every other case resolves `standard`. Never hardcoded in shared prose.
- Blocking-only exit: readiness means zero unresolved findings with `blocking: true` on a fresh review of the current digest; non-blocking findings are recorded, never gating.
- Cap-closure terminal shape: the operator-authorized loop closure recorded in `extensions.cap_closure` with the plan section `## Residual findings (cap closure)`; unavailable to `personal`-class plans under this plan.
- Complexity band: the plan-size segment a metrics row reports, derived from the plan file's task-checkbox count: small (5 or fewer), medium (6 to 15), large (16 or more), unknown (plan file not found or count ambiguous).
- Metrics pass: the read-only aggregation over a repository's staged review sidecars that computes findings-per-round decay, ready-rate per round index, and cap-exhaustion share, per complexity band.

## Assumptions

- assume the four named loop surfaces already carry blocking-only exit conditions in their current bytes (review-plan Iteration Discipline rule 1: "zero unresolved blocking findings and no unresolved reconciliation trigger"; review-loop Exit criteria item 1: "Zero unresolved findings with `blocking: true`"; plans Plan Quality Gate rule 6 and the Ready-for-execution definition; execute-plan Review end condition Blocking row: "Zero unresolved findings with `blocking: true` after triage"); basis: disk reads of all four files, 2026-09-28; Task 2 therefore pins the existing wording as regression guards and adds guidance, it does not rewrite any exit condition.
- assume the legacy "zero Blockers AND zero Medium" wording in projects/.ai-playbook/development_lessons.md (the Planning-Mode stop lesson and the convergence lesson's historical loop name) is historical corpus, not a live gate; basis: the lessons corpus is append-mostly history, the origin names skill surfaces only, and the file is listed out of scope below.
- assume the metrics pass runs read-only over the staged sidecar corpus with no side effects on review artifacts; basis: the script's existing discovery and conservation layers are read-only by design and its privacy invariant (no path-level data outside the private telemetry home) is preserved by aggregate-only output.
- assume `.ai-playbook/facts.md` is the correct local home for `personal_projects_root` (per-project, gitignored local configuration); basis: the facts TOML block convention every skill already resolves; this repository's own file gains the key in Task 1 as a local, commit-free configuration item.
- assume extending `scripts/summarize_review_stats.py` in place is the right carrier for the metrics pass; basis: the origin names the script as the extension target ("or its successor"), the script exists with the discovery, validation-delegation, and selftest layers the pass reuses, and no successor exists.
- assume per-project segmentation is satisfied by one metrics report per repository (each report names its resolved project key, and each repository's `docs/maintenance/review-metrics-log.md` accumulates its own per-project sections the operator compares across repos); basis: corpus discovery is facts-driven per repository, a multi-repo walker would re-implement per-repo facts resolution for no measured need, and the per-repo log shape already yields per-project sections.

Decision points requiring a grill: strict package mechanical for personal projects, metrics-first advisory elsewhere, instrumentation global (user direction recorded in the origin's per-project split, 2026-09-28; Tasks 1 through 4); blocking-only exit as the mechanical rule with ordinary findings recorded not chased (user direction recorded in the origin's Expected section, 2026-09-28; Tasks 1 and 2); existing five-round budgets stay until a project's own data justifies a change (user direction recorded in the origin's Expected section, 2026-09-28; Task 1 standard branch); class resolution via the facts key, never a hardcoded directory (user direction recorded in the origin's split paragraph, 2026-09-28; Task 1); extend summarize_review_stats.py in place as the metrics carrier (origin Suggested fix item 2 with the author's on-disk confirmation of the script's layers, 2026-09-28; Task 3); one metrics report per repository as the per-project segmentation shape (author recommendation accepted under the origin prompt's standing pre-authorization, 2026-09-28; Tasks 3 and 4).

## Gist & Examples

TLDR: review loops exit on zero blocking findings with stop-and-escalate guidance instead of unattainable zero-finding rounds, personal projects get the strict two-round/three-cap package, and a new metrics pass measures decay, ready-rate, and cap exhaustion per complexity band, for simplicity (active elimination of fix-on-fix churn) plus new-capability (the measurement layer).

The corpus measurement in the origin (22 percent of plans stopping at exactly the five-round cap, docs still reporting ready=No at r14-r15, the historical Blocker=0 AND Medium=0 exit unsatisfiable by construction) shows loops terminating by cap, not convergence. This plan makes the already-blocking-only exit the stated mechanical rule everywhere, tells the operator when to stop (no new blocking findings in the latest round) and when to escalate (blockers surviving a verification round mean simplify or rewrite, not another patch round), and instruments the corpus so a later caps decision is made from data.

Examples:

- A personal-class plan under plan review reaches round 3 with one blocking finding left. Today the loop would close through cap closure. After this plan the loop stops, and the operator simplifies the mechanism or rewrites the plan section; no `extensions.cap_closure` is recorded for personal-class plans.
- A standard-class plan reaches round 2 whose round reports no new blocking findings against the prior round. The advisory guidance says stop: record the ordinary findings in the staging record or backlog and exit on the blocking-clean round.
- The weekly maintenance rider runs the metrics pass: the report shows plans in the large band averaging 4.2 findings at r1 decaying to 1.1 by r3 with a 22 percent cap-closure share, which is the evidence a later caps decision cites.

## Evaluation Criteria

**Quality dimensions:**

- correctness: the strictness class resolution is stated once (canonical home in `review-plan`) and every amended surface derives its branch from that resolution, not from a second copy of the rule.
- consistency: every cap-closure surface (plans rule 16, review-plan rule 8, review-staging record contract, execute-plan end-condition) carries the personal-class unavailability with the same class vocabulary.
- observability: the metrics pass exits 0 on the live corpus, emits aggregate-only documents, and never crashes on a legacy or unparseable sidecar (legacy rows land in an unknown bucket).
- minimality: no new mechanical gate is added for the advisory guidance; no validator script changes; the standard-class round budgets stay byte-identical.

**Done when:**

- `review-plan` carries the canonical Project strictness classes subsection resolving the class from `personal_projects_root`, and plans rule 16, review-plan rule 8, review-staging, and execute-plan each carry their personal-class branch.
- review-loop, plans, and receiving-review carry the advisory stop-and-escalate or record-not-chase guidance.
- `scripts/summarize_review_stats.py` grows the `--metrics` mode with `--metrics-json` and `--metrics-markdown` outputs, and its built-in selftest covers decay, ready-rate, cap-exhaustion share, band segmentation, legacy tolerance, and aggregate-only output.
- the maintenance skill's Step 7 weekly rider runs the metrics pass and appends an aggregates-only section to `docs/maintenance/review-metrics-log.md` under the same fail-open guard as the tool-runtime-stats rider.
- this repository's local facts document carries `personal_projects_root` (local configuration; no commit).
- the Validation Commands block passes end to end.

**Ship when:**

- other repositories adopt the class resolution by adding the facts key in their own local facts documents (per-project configuration; human-owned).
- a standard-class project's caps decision (lowering or retiring its round cap and cap-closure protocol) is made from that project's accumulated metrics log in a later plan; deferred, not cancelled.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `agents/skills/review-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/review-loop/SKILL.md`
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/maintenance/SKILL.md`
- `scripts/summarize_review_stats.py`
- `.ai-playbook/facts.md` *(local configuration only; gitignored, so Task 1's edit of it commits nothing)*

**Tests:**

- none as separate files; the metrics behavior is witnessed by the script's built-in `--selftest` suite (extended in Task 3), and the shared-skill runtime-neutrality gate in `scripts/test_execute_plan_runtime.py` is executed unchanged (rule 37) because Task 1 edits two of its covered files.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `projects/.ai-playbook/development_lessons.md`; historical lessons corpus, append-mostly; the origin names skill surfaces only and the legacy exit wording there is descriptive history (see Assumptions).
- `scripts/plan_readiness.py` and `scripts/validate_review_staging.py`; the readiness and staging gates stay untouched: cap-closure acceptance remains valid for standard-class plans, and class-awareness in a validator would re-implement facts resolution the canonical prose section owns.
- `README.md`; no skill name, path, or catalog entry changes.
- runtime copies of the skills outside this repository (deployed home mirrors); they follow the standing vendored-sync flow, not this plan.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"

# 1. Metrics selftest: synthetic-corpus coverage of the new pass (Task 3).
( cd "$REPO" && python3 scripts/summarize_review_stats.py --selftest ) || { echo "FAIL: selftest failed"; exit 1; }

# 2. Shared-skill runtime neutrality (Tasks 1 and 2 edit two covered files).
( cd "$REPO" && python3 -m unittest discover -s scripts -p "test_execute_plan_runtime.py" -k shared_skill_bodies ) || { echo "FAIL: shared-body gate failed"; exit 1; }

# 3. Em-dash cleanliness, scoped to what this plan creates and adds (rule 28: edited
# files carry legacy content no task touches, so whole-file sweeps are out of scope).
# BASE is recorded by Task 1's first item before any task commit; the unset guard
# keeps a missing base from silently scanning nothing.
bash scripts/check-no-em-dash.sh file "$REPO/docs/history/plans/2026-09-28-review-loop-exit-condition-metrics.md" || { echo "FAIL: em-dash in plan file"; exit 1; }
test -n "$BASE" || { echo "FAIL: BASE not recorded (Task 1 first item)"; exit 1; }
bash scripts/check-no-em-dash.sh added-lines --base "$BASE" || { echo "FAIL: em-dash in added lines"; exit 1; }

# 4. Canonical strictness home landed with the strict package (Task 1).
test -f "$REPO/agents/skills/review-plan/SKILL.md" || { echo "FAIL: review-plan missing"; exit 1; }
grep -qF "## Project strictness classes" "$REPO/agents/skills/review-plan/SKILL.md" || { echo "FAIL: strictness subsection missing"; exit 1; }
grep -qF "personal_projects_root" "$REPO/agents/skills/review-plan/SKILL.md" || { echo "FAIL: facts key unresolved"; exit 1; }
grep -qF "default is two review rounds" "$REPO/agents/skills/review-plan/SKILL.md" || { echo "FAIL: personal default missing"; exit 1; }
grep -qF "hard cap of three" "$REPO/agents/skills/review-plan/SKILL.md" || { echo "FAIL: personal cap missing"; exit 1; }
grep -qF "is a certification defect" "$REPO/agents/skills/review-plan/SKILL.md" || { echo "FAIL: cap-closure prohibition missing"; exit 1; }

# 5. Personal-class branch present on every cap-closure surface (Task 1).
grep -qF "escalates to simplify-or-rewrite instead" "$REPO/agents/skills/plans/SKILL.md" || { echo "FAIL: plans pet branch missing"; exit 1; }
grep -qF "never close a loop through this shape" "$REPO/agents/skills/review-staging/SKILL.md" || { echo "FAIL: staging pet note missing"; exit 1; }
grep -qF "not available to personal-class plans" "$REPO/agents/skills/execute-plan/SKILL.md" || { echo "FAIL: execute-plan pet branch missing"; exit 1; }

# 6. Advisory stop-and-escalate and record-not-chase guidance landed (Task 2).
grep -qF "escalate to simplifying or rewriting the change instead of another patch round" "$REPO/agents/skills/review-loop/SKILL.md" || { echo "FAIL: review-loop advisory missing"; exit 1; }
grep -qF "stop when the latest round produced no new blocking findings" "$REPO/agents/skills/plans/SKILL.md" || { echo "FAIL: plans advisory missing"; exit 1; }
grep -qF "never launches additional rounds to chase them to zero" "$REPO/agents/skills/receiving-review/SKILL.md" || { echo "FAIL: receiving-review note missing"; exit 1; }

# 7. Blocking-only exit regression pins (already true today; guards against reintroduction).
grep -qF "zero unresolved blocking findings and no unresolved reconciliation trigger" "$REPO/agents/skills/review-plan/SKILL.md" || { echo "FAIL: review-plan exit pin lost"; exit 1; }
grep -qF 'Zero unresolved findings with `blocking: true`' "$REPO/agents/skills/review-loop/SKILL.md" || { echo "FAIL: review-loop exit pin lost"; exit 1; }
grep -qF "reports zero unresolved blocking findings" "$REPO/agents/skills/plans/SKILL.md" || { echo "FAIL: plans exit pin lost"; exit 1; }
grep -qF 'Zero unresolved findings with `blocking: true` after triage' "$REPO/agents/skills/execute-plan/SKILL.md" || { echo "FAIL: execute-plan exit pin lost"; exit 1; }

# 8. Maintenance wiring landed (Task 4).
grep -qF "review-metrics-log.md" "$REPO/agents/skills/maintenance/SKILL.md" || { echo "FAIL: metrics log home missing"; exit 1; }
grep -qF "--metrics-markdown" "$REPO/agents/skills/maintenance/SKILL.md" || { echo "FAIL: metrics invocation missing"; exit 1; }

# 9. Metrics mode runs on the live corpus and stays aggregate-only (Task 3).
tmp="$(mktemp -d)"
( cd "$REPO" && python3 scripts/summarize_review_stats.py --metrics --metrics-json "$tmp/metrics.json" --metrics-markdown "$tmp/metrics.md" ) || { echo "FAIL: metrics run failed"; rm -rf "$tmp"; exit 1; }
test -s "$tmp/metrics.json" || { echo "FAIL: empty metrics output"; rm -rf "$tmp"; exit 1; }
test -s "$tmp/metrics.md" || { echo "FAIL: empty metrics markdown"; rm -rf "$tmp"; exit 1; }
if grep -qF ".stats.json" "$tmp/metrics.json" "$tmp/metrics.md"; then echo "FAIL: per-file rows leaked into metrics output"; rm -rf "$tmp"; exit 1; fi
rm -rf "$tmp"

# 10. Local class resolution configured for this repository (Task 1 local config item; gitignored, no commit).
grep -qF "personal_projects_root" "$REPO/.ai-playbook/facts.md" || { echo "FAIL: facts key missing (local configuration)"; exit 1; }
```

### Task 1: Project strictness classes and the personal strict package

Files:

- `agents/skills/review-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `.ai-playbook/facts.md` *(local configuration, gitignored; no commit)*

- [x] Record the base revision for validation command 3 in the run notes: `BASE="$(git rev-parse HEAD)"`, executed before any task commit of this run. [class: REPOSITORY_TEST]
- [x] In `agents/skills/review-plan/SKILL.md`, insert a new `## Project strictness classes` subsection immediately before the `## Iteration Discipline (plans skill gate)` heading, with exactly this body: the class-resolution rule (read `personal_projects_root` from the opening TOML block of the project facts document; class is `personal` when the key is present and the repository root lies inside the directory it names, comparing realpaths; every other case, including a missing key or an unresolvable facts document, resolves `standard`; never hardcode the directory in shared prose); the personal strict package (default is two review rounds, hard cap of three, blocking-only exit, ordinary findings recorded in the staging record or backlog and never chased with new rounds, and at the cap without a clean round stop and simplify the plan or rewrite the affected mechanism instead of patching again; the cap-closure terminal shape is NOT available, and a sidecar declaring `extensions.cap_closure` for a personal-class plan is a certification defect); the standard branch (existing round budgets stay unchanged, no new mechanical cap, and a later plan may lower or retire a standard project's round cap and cap-closure protocol only after that project's aggregated review metrics confirm the direction; deferred, not cancelled); and the advisory stop-and-escalate bullet for every class (stop when the latest round produced no new blocking findings; when blocking findings survive a verification round, escalate to simplifying or rewriting the plan instead of patching again). [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/plans/SKILL.md`, append one sentence to the end of Plan Quality Gate rule 16 (after its final words "when no blocking finding stays unresolved"): "In a `personal`-class project (class resolution and strict package per `review-plan`, Project strictness classes) the cap-closure terminal shape is not available: the loop stops at the personal cap of three and escalates to simplify-or-rewrite instead." [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/review-plan/SKILL.md`, append the same sentence with "above" instead of the cross-reference to the end of Iteration Discipline rule 8 (after "a declaration at an earlier round is a falsified certification"): "In a `personal`-class project (Project strictness classes above) the cap-closure terminal shape is not available: the loop stops at the personal cap of three and escalates to simplify-or-rewrite instead." [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/review-staging/SKILL.md`, insert one paragraph immediately after the `### Cap-closure sidecar extension` heading and before the "When a plan loop closes" paragraph: "`personal`-class projects never close a loop through this shape (the strict package escalates to simplify-or-rewrite at their cap of three); a sidecar declaring `extensions.cap_closure` for a plan whose project resolves `personal` is a certification defect (class resolution: `review-plan`, Project strictness classes)." [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/execute-plan/SKILL.md`, insert one paragraph immediately after the Review end condition table and before the "Track in `manifest.md`:" line: "In a `personal`-class project (class resolution and strict package per `review-plan`, Project strictness classes) these review budgets tighten mechanically: the default is two review rounds with a hard cap of three, and at the cap without a clean round the orchestrator stops and puts simplify-or-rewrite to the user; the cap-closure terminal shape is not available to personal-class plans." [class: IMPLEMENTATION_REQUIRED]
- [x] Add `personal_projects_root` to this repository's `.ai-playbook/facts.md` TOML block, set to the local directory that contains this repository among the operator's personal repositories (value recorded only in the local facts file, never in repository bytes; gitignored file, so this item commits nothing). [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED before the edits, GREEN after: validation command 4 (`grep -qF "## Project strictness classes" ...` block) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: validation commands 5 (personal-class branch pins) and 2 (shared-body gate, because plans and execute-plan bodies changed) [class: REPOSITORY_TEST]
- [x] Commit: `skills: project strictness classes with the personal strict package` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Advisory stop-and-escalate guidance and blocking-only regression pins

Files:

- `agents/skills/review-loop/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/receiving-review/SKILL.md`

- [x] In `agents/skills/review-loop/SKILL.md`, insert one paragraph between Exit criteria item 6 and the `| Signal | Valid exit? |` table: "Advisory (no new mechanical gate, every strictness class; class resolution per `review-plan`, Project strictness classes): stop when the latest round produced no new blocking findings, recording ordinary findings instead of chasing them with new rounds; when blocking findings survive a verification round, escalate to simplifying or rewriting the change instead of another patch round. In a `personal`-class project the default is two review rounds with a hard cap of three, and at the cap without a clean round the loop stops for simplify-or-rewrite; `max_full_panel_rounds` keeps its default for standard-class projects." [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/plans/SKILL.md`, insert one paragraph immediately before the "**Ready for execution** means" paragraph: "Advisory stop-and-escalate guidance (no new mechanical gate; full form in `review-plan`, Project strictness classes): stop when the latest round produced no new blocking findings; when blocking findings survive a verification round, escalate to simplifying or rewriting the plan instead of patching again." [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/receiving-review/SKILL.md`, insert one sentence immediately before the line beginning "Do **not** drop a finding that asks to strengthen": "Ordinary (non-blocking) findings are recorded in the staging record or captured as backlog; a review loop never launches additional rounds to chase them to zero (advisory guidance; class resolution per `review-plan`, Project strictness classes)." [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: validation command 6 (advisory pins) and command 7 (blocking-only regression pins, which must stay green through this task; a red pin here means a task edit clobbered an exit condition and blocks the task) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: validation command 2 (shared-body gate; the plans body changed again) [class: REPOSITORY_TEST]
- [x] Commit: `skills: advisory stop-and-escalate guidance with blocking-only exit pins` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Metrics mode in the review-stats script

Files:

- `scripts/summarize_review_stats.py`

- [x] Add a `--metrics` mode with `--metrics-json PATH` and `--metrics-markdown PATH` outputs (at least one required when `--metrics` is given), reusing the existing facts-driven discovery and sidecar parsing; group the discovered sidecars by `artifact_slug` into loops, and per round record the round number, verdict, staged findings total, blocking count, and whether `extensions.cap_closure` is present. [class: IMPLEMENTATION_REQUIRED]
- [x] Compute, per complexity band and per round index: findings totals (the decay series), ready-rate (share of loops whose round verdict is ready), and per loop the cap-exhaustion share (loops closed through `extensions.cap_closure`) plus the latest-round distribution; derive each loop's band from its plan file's task-checkbox count (`plans_dir` and its completed subdirectory globbed by the artifact slug; small 5 or fewer, medium 6 to 15, large 16 or more, unknown when the plan file is absent or the match is ambiguous); classify a sidecar that fails validation into an unknown-band legacy bucket instead of failing the pass; emit aggregates only (no per-file path rows) in both output forms, preserving the script's privacy invariant. [class: IMPLEMENTATION_REQUIRED]
- [x] `summarize_review_stats.py --selftest`; given a synthetic corpus of three loops in a temp directory (loop A: three rounds with findings totals 6, 4, 2 and verdicts no, no, yes; loop B: two rounds with totals 3, 3 and `extensions.cap_closure` on the last round; loop C: one round, verdict no; plans sized into different bands; a fourth loop whose plan file is absent from the plans directories, carrying one round with two findings and verdict no; a fifth loop whose artifact slug matches plan files under both the plans directory and its completed subdirectory, carrying one round with one finding and verdict no), expects the metrics result to report the per-round findings series 14, 7, 2 across round indexes, ready-rate one of five at the final index, cap-exhaustion share one of five, three loops in their derived bands with the plan-less fourth loop and the ambiguous-slug fifth loop both in the unknown band, and a JSON document with zero per-file path rows; ends with explicit temp-directory teardown. [class: REPOSITORY_TEST]
- [x] `summarize_review_stats.py --selftest`; given a synthetic corpus containing one sidecar that fails version-1 validation beside valid loops, expects the metrics pass to count it into the legacy bucket and still exit 0. [class: REPOSITORY_TEST]
- [x] Run → expect RED before implementation: validation command 9 (the `--metrics` flag does not exist today, so the smoke run fails non-zero); expect GREEN after (the live-corpus run exits 0 with aggregate-only output). [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: validation command 1 (selftest) [class: REPOSITORY_TEST]
- [x] Commit: `stats: review-corpus metrics mode with decay, ready-rate, and cap-exhaustion segmentation` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Maintenance weekly rider wiring

Files:

- `agents/skills/maintenance/SKILL.md`

- [x] In `agents/skills/maintenance/SKILL.md` Step 7 (weekly measurement rider), insert one bullet between the "On success:" bullet and the "Fail open:" bullet: "- Review-metrics pass (same weekly gate): run `python3 scripts/summarize_review_stats.py --metrics --metrics-markdown <report-home>/review-metrics-<run-stamp>.md` and append one aggregates-only section to `docs/maintenance/review-metrics-log.md` (create-if-absent; findings-per-round decay, ready-rate per round, cap-exhaustion share, segmented by complexity band, the resolved project key riding the section header), sharing the tool-runtime-stats rider's guard, cadence, and fail-open semantics." [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: validation command 8 (maintenance wiring pins) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the full Validation Commands block, tasks 1 through 3 artifacts in place (rule 21 interim expectation: at this point every command in the block passes) [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: weekly review-metrics rider on the measurement leg` [class: IMPLEMENTATION_REQUIRED]
