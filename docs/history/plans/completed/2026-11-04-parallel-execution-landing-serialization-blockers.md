# Plan: Raise execution parallelism past the landing-serialization blockers

Backlog origin: docs/history/backlog/2026-11-04-parallel-execution-landing-serialization-blockers.md
Driving force: efficiency
Plan review record: the staging series {reviews_dir}/2026-11-04-plan-review-parallel-execution-landing-serialization-blockers-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2h total, largest task 1h
Authoring claim: parallel-execution-landing-serialization-blockers.md (session sess_1586f3af-cc6c-4a18-87c9-ceb08cb97618)

## Terms

- owned-path set: the set of repository paths a run claims as its own edit surface, recorded per run in its done-setup manifest operands, and derived pre-run from the covering plan's Files: lists.
- dispatch admission: the check a deciding turn runs before creating a child, comparing the candidate's owned-path set against every outstanding run's recorded owned-path set.
- outstanding run: a recorded run sitting in the post-review, pre-landed state (its children[] entry outcome pending or progress past review, or a pending_landing record), plus any surviving repo-matching pending-landing note.
- merge landing lock: the lock family in scripts/done-lock.sh (merge-acquire, merge-status, merge-release) serializing landing critical sections on the default branch.
- ref-only landing class: the land_squash.sh land-worktree mode: composition happens in the source worktree and the primary checkout receives only a two-value compare-and-swap ref update.
- base pin: the recorded merge base a run captures at start and refreshes after a sanctioned rebase.

## Why

Three coupled rules serialize maintenance runs to one at a time. The dispatch gate requires zero outstanding unlanded runs, so one peer strand in post-review blocks every new dispatch even when targets are disjoint. The merge landing lock is exclusive for the whole landing, so landings queue behind the slowest. A base move mid-run triggers a stand-down instead of a bounded rebase. Witnessed cost: a 0/1 stand-down on 2026-11-04 and a 0/2 stand-down on 2026-11-01 while capacity sat free.

## Gist & Examples

TLDR: replaces the flat unlanded-run dispatch gate with target-disjointness admission, narrows the ref-only landing lock span to the swap critical section so composition no longer queues behind a lock holder, and makes base churn a bounded mechanical rebase, so three parallel sessions become reachable, for efficiency.

Today: five claim-free plans and multiple ready entries existed while one peer strand blocked dispatch (2026-11-04 witness). After: a disjoint candidate dispatches; two disjoint ref-only landings interleave their composition and serialize only their compare-and-swap moves on the narrowed lock; an intersecting landing waits only for the holder's swap critical section; a moved base triggers at most two mechanical rebases per convergence cycle before any stand-down.

## Outcome

Three parallel maintenance sessions are practically reachable without weakening the protections the landing machinery has actually witnessed needing.

- A dispatch proceeds when its owned-path set is disjoint from every outstanding run's recorded set.
- Two disjoint ref-only landings interleave their composition and serialize only their swap critical sections.
- A base move mid-run becomes a bounded mechanical rebase (at most two attempts per convergence cycle) instead of a stand-down trigger.
- The retired gate and the new check are registered in the machinery registry in the same change.

Gate delta: removes one dispatch refusal (the zero-outstanding-unlanded gate, maintenance SKILL.md Invariants; witnesses: stand-downs 2026-11-04 0/1 and 2026-11-01 0/2), replaced by a target-disjointness admission check (paying sibling: the removed gate itself); narrows the ref-only landing lock span from whole-landing exclusivity to the swap critical section (rebase, check-landing, the prompt-log prune audit, composition, tree-equality, and check-archive run pre-lock; primary land mode untouched, done-lock-before-merge-lock unchanged, no new lock-side check); adds a bounded rebase duty (procedural, no new refusal class; it retires the base-churn stand-down trigger); registry rows pre-registered for the removed gate, the new check, and the retired stand-down trigger; net: fewer refusal classes, one check added paying for one gate removed.

## Assumptions

- assume a run's owned paths are derivable at dispatch time from its done-setup manifest operands, and pre-run from the plan's Files: lists; basis: scripts/done_run.sh setup accepts --owned-path/--owned-plan operands and the manifest records them.
- assume the ref-only land-worktree class mutates only the base branch ref through a two-value compare-and-swap, so disjoint landings interleave safely; basis: scripts/land_squash.sh land-worktree contract and the P57 collision list naming shared-checkout and staging surfaces that ref-only landings never touch.
- assume two rebase attempts per convergence cycle bound the base-churn remedy before stand-down (the counter advances only on a failed convergence pass, so routine interleaved landings never exhaust it); basis: the probe-fail rebase arm exists and land-worktree accepts --expected-base.

Decision points requiring a grill: admission-record-source: recorded owned paths from the run's execution claim and done-setup manifest, plan Files lists before a run exists; source: repo evidence in scripts/done_run.sh and scripts/execution_claim.sh; date 2026-11-04; section Task 1; lock-narrowing-shape: overlap-conditional exclusivity for the ref-only class with the primary land mode untouched; source: scripts/land_squash.sh mode ownership plus the P57 collision list; date 2026-11-04; section Task 2; rebase-duty-owner: the Worktree-first standard lifecycle step 4 with the two maintenance blueprints referencing it; source: the standard's class-ownership paragraph; date 2026-11-04; section Task 3

## Standing constraints

- Do not edit the acquire-time export-capture arms; docs/history/backlog/2026-11-04-lock-acquire-export-capture-census.md and docs/history/backlog/2026-11-04-merge-lock-acquire-exports-lost-across-tool-call-shells.md own that surface (cluster fence from the dispatch entry).
- Every removed or narrowed guard names its witnessed incident in the same change; the P57 collision-list protections (branch switches sweeping peer files, staged-index races, done-lock and merge-order collisions) hold verbatim.
- Same-target claims and audit/re-triage lane exclusivity stay global across runtimes; the fleet cap number (3) does not change.
- Any new check carries the machinery admission fields (repository guidelines, Machinery admission protocol) and names what it retires.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the admission checker's intersect and disjoint verdicts are proven by tests, including the empty-set and missing-record degenerate cases.
- safety: the narrowed lock still serializes intersecting landings; the CAS old-value check is proven as the disjoint-case serialization point; P57 protection classes keep asserting tests.
- simplicity: net machinery removal is visible in one registry diff: one gate retired, one check added, one stand-down trigger retired.

**Done when:**
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_dispatch_admission.py scripts/test_land_squash.py -q` passes.
- `bash scripts/check_maintenance_pins.sh` exits 0.
- `bash scripts/check-no-em-dash.sh added-lines --base <branch point>` exits 0.
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` exits 0.

**Ship when:**
- none stated.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/dispatch_admission.py` (Task 1) *(new)*
- `agents/skills/maintenance/SKILL.md` (Task 1)
- `agents/skills/maintenance/decisions.md` (Task 1)
- `agents/skills/maintenance/guards.md` (Task 1)
- `agents/skills/maintenance/scheduling.md` (Task 1)
- `agents/skills/maintenance/survey-arms.md` (Task 1)
- `scripts/land_squash.sh` (Task 2)
- `agents/skills/execute-plan/worktree-first.md` (Task 2)
- `agents/skills/execute-plan/worktree-first.md` (Task 3)
- `agents/skills/maintenance/template-execution.md` (Task 3)
- `agents/skills/maintenance/template-authoring.md` (Task 3)
- `scripts/machinery_registry.json` (Task 4)
- `scripts/check_maintenance_pins.sh` (Task 1)

**Tests:**
- `scripts/test_dispatch_admission.py` (Task 1) *(new)*
- `scripts/test_land_squash.py` (Task 2)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/done_run.sh` export-capture arms; reason: owned by the sibling cluster rows named in Standing constraints.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_dispatch_admission.py scripts/test_land_squash.py -q
bash scripts/check_maintenance_pins.sh
bash scripts/check-no-em-dash.sh added-lines --base <branch point>
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

### Task 1: Target-disjointness dispatch admission

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/dispatch_admission.py` *(new)*
- `scripts/test_dispatch_admission.py` *(new)*
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/decisions.md`
- `agents/skills/maintenance/guards.md`
- `agents/skills/maintenance/scheduling.md`
- `agents/skills/maintenance/survey-arms.md`
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `check_admission` in `scripts/dispatch_admission.py`

- [x] `check_admission` computes the candidate's owned-path set and tests intersection against each outstanding run's recorded set: given one outstanding run whose owned paths intersect the candidate's, expects exit 1 naming both runs and the intersecting paths [class: IMPLEMENTATION_REQUIRED]
- [x] Disjoint candidate passes: given one outstanding run with disjoint owned paths, expects exit 0 with an `OUTCOME: pass` line recording the admission verdict [class: IMPLEMENTATION_REQUIRED]
- [x] Degenerate inputs hold: given an outstanding run with an empty recorded owned-path set, expects the conservative verdict (treat as intersecting) with the reason named [class: IMPLEMENTATION_REQUIRED]
- [x] Missing-record degenerate case: given an outstanding run carrying no done-setup manifest from which to derive owned paths, expects the conservative verdict (treat as intersecting) with the missing-source reason named [class: IMPLEMENTATION_REQUIRED]
- [x] Invariants paragraph replaced: the dispatch-gate clause reads target-disjointness admission, the post-review cap stays as a landing-queue depth bound with the one-per-turn drain duty, and the retired gate's registry-removal row is cited [class: IMPLEMENTATION_REQUIRED]
- [x] decisions.md gate references updated: the D1 dispatch gate sentence and the D2 authoring landing-mirror sentence read the new admission consult [class: IMPLEMENTATION_REQUIRED]
- [x] SKILL.md gate sites converted: the Invariants clause and the parked re-arm discharge precedence (SKILL.md lines 99 and 72) read the target-disjointness admission consult with the retired gate's registry-removal row cited [class: IMPLEMENTATION_REQUIRED]
- [x] decisions.md gate sites converted: the exec-mode selection rule and the in-session authoring chaining rule (decisions.md lines 28 and 35) read the admission consult with the retired gate cited [class: IMPLEMENTATION_REQUIRED]
- [x] Blueprint gate sites converted: the pre-dispatch landing gate with its final-slot D3 resolution (scheduling.md line 10) and the landing-gate mention in the override inventory (guards.md line 25) read the admission consult with the retired gate cited [class: IMPLEMENTATION_REQUIRED]
- [x] Survey-arms gate sites converted: the pending-dispatch validation and parked-intent discharge arms (survey-arms.md lines 43 and 46) read the admission consult with the retired gate cited, and an execution-time `rg -n 'outstanding unlanded|zero outstanding' agents/skills docs/maintenance` sweep over the touched files returns no unconverted operative hit [class: IMPLEMENTATION_REQUIRED]
- [x] Pins updated for the new wording: the pinned needle sets in `scripts/check_maintenance_pins.sh` (the `pre-dispatch landing gate` Step 5 needle, the Invariants region needles `post-review, pre-landed state` / `zero outstanding unlanded runs` / `no surviving repo-matching`, and the `pending-landing (outstanding unlanded run)` needle) read the admission consult's wording, and the pins suite passes against the rewritten sites [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the new tests fail against the absent checker (tests, fixtures, and commands are selected at execution from repository evidence) [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: replace zero-outstanding dispatch gate with target-disjointness admission` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Ref-only landing lock span narrowing

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/land_squash.sh`
- `agents/skills/execute-plan/worktree-first.md`
- `scripts/test_land_squash.py`

Primary class anchors:
- `land-worktree` in `scripts/land_squash.sh`

- [x] Lock span narrowed for the ref-only class: rebase, the wired check-landing gate, the prompt-log prune audit over the landing range, squash composition, tree-equality, and the check-archive gate over the built landing commit run pre-lock in the source worktree; the lock spans the parentage verification, the compare-and-swap, the post-landing gate, and the reconcile tail [class: IMPLEMENTATION_REQUIRED]
- [x] The pre-lock check-landing window stays closed: given a base move between any pre-lock gate pass (check-landing, prune audit, check-archive) and the compare-and-swap, expects the old-value check to refuse with the verified-base-tip evidence, and the Task 3 rebase duty to re-run the full pre-lock gate sequence on retry [class: IMPLEMENTATION_REQUIRED]
- [x] The primary land mode keeps full whole-landing exclusivity and its done-lock-before-merge-lock ownership unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given two concurrent ref-only landings on disjoint path sets, expects both compare-and-swap moves to serialize through the exclusive narrowed lock with exactly one retry cycle on the loser [class: REPOSITORY_TEST]
- [x] P57 protections asserted: given the shared-checkout and staging collision classes from the P57 list, expects the serialization tests to keep passing over the primary land mode [class: REPOSITORY_TEST]
- [x] Run → expect RED: the span-narrowing and serialization tests fail against the current whole-landing exclusivity [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: narrow ref-only landing lock span to the swap critical section` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Bounded mechanical rebase duty

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/worktree-first.md`
- `agents/skills/maintenance/template-execution.md`
- `agents/skills/maintenance/template-authoring.md`

Primary class anchors:
- `Post-landing reconciliation implementation (how step 4 finishes)` in `agents/skills/execute-plan/worktree-first.md`

- [x] Base-move duty: given a stale-base refusal or compare-and-swap old-value mismatch after landing composition, expects the run to rebase onto the moved tip inside its worktree, refresh the base pin, re-run the pre-lock gates, and retry, bounded at two failed passes per cycle [class: IMPLEMENTATION_REQUIRED]
- [x] Cycle accounting: a cycle is the attempts against one observed base tip; a peer landing between attempts starts a new cycle; the pass counter advances only on a base-move failure, never on other refusals [class: IMPLEMENTATION_REQUIRED]
- [x] Exhaustion arm: given a third consecutive failed convergence pass on base moves within one cycle, expects the run to stand down keeping the worktree and branch with the pending_landing record written [class: IMPLEMENTATION_REQUIRED]
- [x] Blueprint wiring: the execution and authoring blueprints reference the duty by name in their landing paragraphs instead of treating a base move as a stand-down trigger [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: bounded mechanical rebase duty for mid-run base churn` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Machinery registry rows

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/machinery_registry.json`

Primary class anchors:
- `entries` in `scripts/machinery_registry.json`
- `removals` in `scripts/machinery_registry.json`

- [x] Registry removal row for the retired zero-outstanding dispatch gate in `scripts/machinery_registry.json`: names the witnessed stand-downs (2026-11-04 0/1, 2026-11-01 0/2), the sunset (promotion is immediate: it replaces an existing blocker in the same change), and the review date [class: IMPLEMENTATION_REQUIRED]
- [x] Registry entry row for `dispatch_admission` carrying the four admission fields (incident links, catch frequency expectation, false-positive cost, review date) and naming the retired gate as its paying sibling [class: IMPLEMENTATION_REQUIRED]
- [x] Registry removal row for the retired base-churn stand-down trigger, so the one-registry-diff simplicity criterion shows all three movements [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full Validation Commands block → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `chore: register admission check and retired dispatch gate in machinery registry` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

Origin row `docs/history/backlog/2026-11-04-parallel-execution-landing-serialization-blockers.md` is covered by this plan's Tasks 1-4 (target-disjointness dispatch admission, ref-only landing lock span narrowing, bounded mechanical rebase duty, machinery registry rows) and is deleted in this archive commit per the AGENTS.md fold-then-delete rule. This section is the row's durable home; records citing the row as a witness cite this archived plan path.
