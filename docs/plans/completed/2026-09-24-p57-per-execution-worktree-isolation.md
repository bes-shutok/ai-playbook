# Plan: P57 per-execution ad-hoc worktree isolation for dispatched execution children

Backlog origin: docs/history/backlog/2026-09-24-reinstate-per-execution-adhoc-worktree-isolation.md
Driving force: efficiency + code-quality (primary + secondary; the backlog item's secondary force is named "reliability", which is outside the closed taxonomy, so it is mapped to code-quality, the closest member: the reliability half is the elimination of the shared-checkout stranding classes, and park-triage would not take it because the primary efficiency half is user-directed fleet utilization)

## Terms

- Per-execution worktree: the linked git worktree the execution blueprint creates before any plan work, one per dispatched execution child, branched off the default-branch snapshot.
- Snapshot: the default branch's current commit (`refs/heads/<default>`), never the primary checkout's working tree or its current branch.
- Merge landing lock: the repo-keyed lock family in `scripts/done-lock.sh` (`merge-*` commands); any linked worktree of one repository observes the same lock, so landing critical sections serialize across all worktrees.
- Done lock: the done-mode lock family in the same script; keyed per-worktree on `--show-toplevel`, so each per-execution worktree holds its own.
- Execution claim: the claim file at the primary checkout's `docs/tmp/execution-claims/<plan-slug>.md` the execution payload writes; it stays primary-rooted by design because the guards read it there.
- `pending_landing`: the scheduler state's deferred-landing intent record plus its per-run memory note; the drain cursor that serializes landing recovery.
- Fleet cap: the 2026-09-24 (P54) repo-wide cap of 4 concurrent children across mixed kinds; `children[]` entries are the state-file arm's in-flight records.
- `progress_mark`: the per-entry checkbox count the scheduler's child-outcome check stores; today it reads the primary checkout's plan file.

## Assumptions

- assume main `df664ad5` (P54 landed) is the authoring baseline and the surveyed prose of SKILL.md, zcode.md, prompt-templates.md, and the pins suite is current; basis: git survey 2026-09-24 of this plan's surfaces.
- assume `scripts/execute_plan_worker_registry.py` (named in the dispatch surfaces list) is out of scope: it does not exist on main; it lives only on the unlanded peer branch `2026-09-22-codex-execute-plan-runtime-reconciliation`. Per-child fleet semantics on main live in SKILL.md's guards. If that branch lands later, a follow-up fold owns reconciling it with this plan's per-run reads; basis: `ls scripts/` and `git log --all --follow` on main bytes, 2026-09-24.
- assume done-session-isolation (mid-execution on a branch, not landed) is not a dependency of this plan; basis: the backlog item's "what already exists" list marks it "(executing)".
- assume P53a's `recover-done-pending` driver transition (main `7f708429`) is landed and is the liveness reference for a wedged run; basis: `git show 7f708429` (SKILL.md, runtime-contract.md, execute_plan_runtime.py, DonePendingRecoveryTest).
- assume the done lock already scopes per run once runs are per-worktree, because done-mode locks are keyed per-worktree on `--show-toplevel` while merge locks are keyed per-repository; basis: `scripts/done-lock.sh` usage text, read 2026-09-24.
- assume the execute-plan skill already supports linked worktrees end to end (Linked-worktree bootstrap recipe, closeout-baseline capture, ad-hoc-worktree closeout migration, unlanded-plan cherry-pick remedy) and its bytes stay untouched here; basis: agents/skills/execute-plan/SKILL.md read 2026-09-24; recipe pinned by scripts/test_execute_plan_worktree_bootstrap.py.
- assume this is a prose-only plan: the runtime driver (`scripts/execute_plan_runtime.py`) operates relative to its invoking checkout and needs no change for per-execution worktrees; basis: driver survey 2026-09-24 (per-checkout git usage, existing worktree scope witnesses).
- assume execution children dispatched under the ZCode runtime follow the SKILL.md orchestrator path, so the blueprint paragraphs are the operative surface; the Codex driver path consumes the same SKILL.md contract; basis: maintenance SKILL.md Step 5 and the runtime contract's adapter boundary.
Decision points requiring a grill: parallelism degree: executions are fleet members counted toward the repo-wide cap of four, with the per-turn dispatch limits (at most one execution and one authoring per scheduler turn) and the post-review pre-landed single-run cap standing; recommended shape accepted under the dispatch task's standing pre-authorization; source: dispatch prompt standing pre-authorization plus the backlog item's decide item; 2026-09-24; affected: Gist & Examples, Evaluation Criteria, Task 2; merge-order policy: landings serialize under the repo-keyed merge landing lock in arrival order, the squash's own merge machinery polices main movement, and the existing `pending_landing` recovery is the only landing queue; recommended shape accepted under the same standing pre-authorization; source: dispatch prompt standing pre-authorization plus the backlog item's decide item; 2026-09-24; affected: Gist & Examples, Evaluation Criteria, Task 5.

## Gist & Examples

TLDR: dispatched execution children move into their own per-execution ad-hoc worktrees off the default-branch snapshot, retiring the execution lane's one-in-flight hold so the fleet cap becomes meaningful for executions (efficiency), and the shared-checkout stranding classes disappear (code-quality).

**Before (today):** the execution blueprint runs branch-based Phase 0 in the shared primary checkout. A second execution cannot start (the P54 interim constraint holds the lane at one) because a second branch-based execution would reproduce the documented collision list: Phase 0 branch switches sweeping a peer's uncommitted files, staged-index races during per-task commits, done-lock contention, document-registry archive-commit races, and final-merge interference. The witnessed costs: landing-completion work defers with `pending-landing (primary occupied by peer session)`; a done-pending wedge strands the checkout for days (the 2026-09-24 deadlock); a stalled lane holds the checkout with no reclaim surface; and the fleet cap of four degrades to one execution plus authoring children.

**After (this plan):** the execution blueprint creates a per-execution worktree before any plan work (`git worktree add -b <execution-branch> <sibling-path> <default-branch>`), runs the execute-plan Linked-worktree bootstrap recipe (facts, reviews, tmp), and does all plan work, task commits, the archive commit, and the review loop inside that worktree on the run's own branch. Two dispatched executions now overlap: each checks boxes in its own tree, each holds its own done lock (done locks are keyed per-worktree), each commits in its own index. Landings still serialize: the merge landing lock is repo-keyed, so the two runs' squash merges arrive in lock order; a conflicted or refused squash takes the existing `pending_landing` deferred-landing path. The scheduler's reads follow the run: the `children[]` entry gains an additive `worktree` field the child records once its worktree exists, and the failure cap's manifest reads and progress-mark counts resolve per-run locations through it (claims stay primary-rooted; they are the guards' witness by design).

The seven rework-list items from the backlog item and the stance, each with its owning task:

1. Per-execution worktree off a snapshot via the linked-worktree bootstrap recipe: Task 4 (blueprint worktree paragraph).
2. Phase 0 branch setup per worktree: Task 4 (the worktree's `-b` branch is the Phase 0 branch; execute-plan Step 0.3 verifies, nothing is created).
3. Done-lock scope per run: Tasks 4 and 5 (pre-Phase-0 gate and done-skill scoping; the per-worktree keying already in `scripts/done-lock.sh` is the mechanism, the prose pins it).
4. Document-registry archive commit per worktree: Task 5 (archive move, registry row, origins-closure check, and archive commit run in the run's worktree and ride the squash).
5. The lane guards' discovery arm per worktree: Task 1 (claims stay primary-rooted by design; the manifest-based arms and the progress-mark read resolve per-run locations through the entry's `worktree` field).
6. The state schema's per-child progress marks: Task 1 (additive `worktree` field under schema 4, no version bump; per-run reads at the three manifest/progress sites).
7. Parallelism degree and merge-order policy, then flip the rejection paragraph: Tasks 2 and 3 (the constraint flip: SKILL.md's operative surfaces, then the runtime overlay's two clauses) and Task 5 (the blueprint's landing and archive half of the flip).

Non-goals, unchanged and verified by the existing pins: the merge landing lock, the landing gate (zero outstanding unlanded runs plus the per-run note conjunct), the post-review pre-landed single-run cap, and every landing re-run stay; the state schema stays at 4 (additive field only); interactive operator sessions keep today's "operator or plan prescribes" allowance; the execute-plan skill's own bytes (bootstrap recipe, closeout migration) are consumed by reference, never edited.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every one of the seven rework-list items maps to an owning task section (the Gist mapping table is greppable per item), and no operative surface still carries the interim constraint after execution (region-scoped negation in Validation Commands; the P54 Revisions ledger entry keeps its dated wording).
- maintainability: the blueprint edits reference existing mechanisms by name (Linked-worktree bootstrap recipe, closeout-baseline capture, ad-hoc-worktree closeout, `pending_landing` duty, merge landing lock) instead of restating them; new prose carries dated attribution (P57) the way P54's edits do.
- validation: the pins suite exits 0 with the companion pins registered (blueprint byte-parity and deviations-list protocol), `scripts/plan_readiness.py` exits 0 on the final bytes, and the hygiene scan exits 0.

**Done when:**
- All tasks checked; the pins suite, the bootstrap-recipe smoke suite, and the readiness gate exit 0 on the final tree.
- `grep -c "INTERIM EXECUTION CONSTRAINT" agents/skills/maintenance/SKILL.md` returns 0 (case-sensitive; the historical lowercase ledger wording is untouched), and the five flip spans (S7, S8, S9, S11, S12 in Validation Commands) each verify.
- The `children[]` schema block still parses as JSON with `schema: 4` and carries `"worktree": null` in the entry shape.
- No runtime script changed: `git diff --name-only` over the branch lists only the four prose/pins files this plan declares plus this plan file (the five-file set Task 6's verify item names).

**Ship when:**
- The next dispatched execution child runs end to end in its own per-execution worktree, records its `worktree` field, and lands through the merge-landing-lock-serialized squash; observed by a scheduler turn's `children[]` record and the run's own landing verification. Operational adoption evidence; prose only, no checklist item.

## Review Scope

**Explicit must-fix; findings on these paths are always in scope (review and fix if valid):**

**Production code:**
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/prompt-templates.md`
- `scripts/check_maintenance_pins.sh`

**Tests:**
- (none; the pins suite is itself the mechanical gate and is listed above)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/execute_plan_runtime.py`; reason: the driver operates per-invoking-checkout and its existing worktree scope witnesses already tolerate linked worktrees; this plan changes no driver code (Assumption).
- `scripts/execute_plan_runtime_codex.py`; reason: same per-checkout operation; no code path of this plan touches it.
- `scripts/worktree_closeout_migrate.py`; reason: consumed by reference from the existing execute-plan closeout step; no change prescribed.
- `agents/skills/execute-plan/SKILL.md`; reason: its Linked-worktree bootstrap recipe and closeout steps are consumed by reference and are byte-pinned by `scripts/test_execute_plan_worktree_bootstrap.py`; editing them is this plan's non-goal.
- `scripts/execute_plan_worker_registry.py`; reason: does not exist on main; peer-branch-only surface recorded in Assumptions.
- `docs/history/backlog/2026-09-24-reinstate-per-execution-adhoc-worktree-isolation.md`; reason: origin of record stays open under `docs/history/backlog/` until this plan's completion pass moves it per the plans skill's Plan Lifecycle.

## Design Invariants (CR Guard)

- The merge landing lock stays repo-keyed and mutually exclusive for all landing critical sections (2026-09-20 merge-landing-lock grouping; P54 Invariants): isolation replaces shared-checkout cohabitation, not the lock. No task may move landing serialization into the state file or per-run locks.
- The landing gate stands: zero outstanding unlanded runs and no surviving repo-matching `pending-landing-<plan-slug>` note gates both lanes' dispatches, and the post-review pre-landed state stays capped at one recorded run (sequential landing discipline, landed 2026-09-23). Parallel executions overlap only in the tasks/review phase, never in the landing pipeline.
- The state schema stays at 4: the `worktree` field is additive with no version bump (the schema-4 additive-no-bump precedent; the pins suite's schema-block parse check must keep passing).
- Done-mode lock keying (per-worktree on `--show-toplevel`) and merge-mode keying (per-repository common dir) are load-bearing facts this plan documents, never changes.
- The execution claim file stays primary-rooted with its four frontmatter lines; a per-worktree claim would be invisible to the `G1e` discovery arm and would regress the P54 Task 4 design.
- The execute-plan skill's Linked-worktree bootstrap recipe bytes are pinned by `scripts/test_execute_plan_worktree_bootstrap.py`; this plan consumes the recipe by name and must not restate or edit it.
- Historical prose keeps its bytes: the P54 Revisions ledger entry and the dated supersession chain links before P57 are history and are never edited; only new dated links and the operative flip sentences change.
- Blueprint byte-parity protocol: every execution-blueprint edit is registered in prompt-templates.md's deviation list (dated entry, paraphrased, never quoting the pinned literals), and companion pins are registered in the same task so the suite stays green per commit.

## Validation Commands

```bash
set -u
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1
fail() { echo "VALIDATION FAIL: $1"; exit 1; }
# Three-way absence check (forbidden-match polarity): rc 0 = forbidden match (fail),
# rc 1 = clean no-match (pass), rc >= 2 = tool error (fail). A plain
# `if grep; then fail` would read a tool error as clean.
expect_absent() {
  grep -qF "$1" "$2" 2>/dev/null
  rc=$?
  if [ "$rc" -eq 0 ]; then fail "forbidden pattern present in $2: $1"; fi
  if [ "$rc" -ge 2 ]; then fail "grep tool error rc=$rc on $2"; fi
}
# Wrap-tolerant variant (flattened before matching): a multi-word phrase can be
# line-wrapped in the target, so the line-oriented check above never matches it.
expect_absent_flat() {
  [ -f "$2" ] || fail "missing absence-check target: $2"
  tr '\n' ' ' < "$2" | tr -s ' ' | grep -qF "$1" 2>/dev/null
  rc=$?
  if [ "$rc" -eq 0 ]; then fail "forbidden pattern present (flat) in $2: $1"; fi
  if [ "$rc" -ge 2 ]; then fail "grep tool error rc=$rc on $2"; fi
}

# 1. Pins suite: every companion pin this plan registered (blueprint byte-parity).
bash scripts/check_maintenance_pins.sh || fail "pins suite"

# 2. The consumed bootstrap recipe bytes did not move (non-regression witness).
python3 scripts/test_execute_plan_worktree_bootstrap.py || fail "bootstrap recipe smoke suite"

# 3. Interim constraint retired from operative surfaces. Region discipline: the
#    case-sensitive caps phrase occurs only in operative sites (the Step 2 bullet and
#    the supersession chain); the P54 Revisions ledger entry carries the lowercase
#    historical wording and is never swept.
expect_absent "INTERIM EXECUTION CONSTRAINT" agents/skills/maintenance/SKILL.md
expect_absent "Until P57, the sanctioned overlap shapes" agents/skills/maintenance/SKILL.md
expect_absent "stays single until P57" agents/skills/maintenance/zcode.md
expect_absent "holds at one in-flight child until P57" agents/skills/maintenance/zcode.md

# 4. The flip landed: one dedicated positive grep per flipped surface.
grep -qF "EXECUTION ISOLATION (landed 2026-09-24, P57" agents/skills/maintenance/SKILL.md \
  || fail "S7 fleet-cap isolation sentence missing"
grep -qF "execution children run in per-execution ad-hoc worktrees off the default-branch snapshot" \
  agents/skills/maintenance/SKILL.md || fail "S8 Invariants flip missing"
awk '/^### Execution-lane concurrency stance/{f=1; next} /^## Revisions/{f=0} f' \
  agents/skills/maintenance/SKILL.md | grep -qF "REWORK EXECUTED (landed 2026-09-24, P57" \
  || fail "S9 supersession chain P57 link missing"
test "$(grep -cF "2026-09-24 (P57 per-execution worktree isolation" agents/skills/maintenance/SKILL.md)" -eq 1 \
  || fail "S10 Revisions ledger P57 entry missing or duplicated"
grep -qF "execution children in their per-execution worktrees, P57" agents/skills/maintenance/zcode.md \
  || fail "S11 zcode markers flip missing"
grep -qF "retired 2026-09-24 by P57" agents/skills/maintenance/zcode.md \
  || fail "S12 zcode ladder flip missing"

# 5. Per-run reads: the additive schema field and each read site's own clause.
#    The json fence literal is built at run time (a literal fence sequence here
#    would close this plan's own Validation Commands block; intentional).
BT="$(printf '\140\140\140')"
awk -v bt="$BT" '$0 == bt "json" {f=1; next} $0 == bt {f=0} f' agents/skills/maintenance/SKILL.md \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); c=d["children"][0]; sys.exit(0 if d.get("schema")==4 and "worktree" in c and c["worktree"] is None else 1)' \
  || fail "state schema block lost the worktree field or schema 4"
grep -qF "once its blueprint-created per-execution worktree exists" agents/skills/maintenance/SKILL.md \
  || fail "S1 worktree field paragraph missing"
grep -qF "resolved inside the entry's recorded \`worktree\` when that additive field is set" \
  agents/skills/maintenance/SKILL.md || fail "S2 progress-mark per-run clause missing"
grep -qF "the same repository-relative manifest path inside the recorded worktree" \
  agents/skills/maintenance/SKILL.md || fail "S3 ingestion per-run clause missing"
grep -qF "the same per-run resolution the rate-limited ingestion bullet applies" \
  agents/skills/maintenance/SKILL.md || fail "S4 fast re-dispatch per-run clause missing"
grep -qF "own-record per-run worktree recording" agents/skills/maintenance/SKILL.md \
  || fail "S5 sanctioned-writer addition missing"
grep -qF "the archival arm is read ref-based" agents/skills/maintenance/SKILL.md \
  || fail "S21 ref-based archival read missing"

# 6. Blueprint Phase 0 per worktree (unique-literal counts keep the checks body-scoped).
test "$(grep -oF "git worktree add -b <execution-branch> <sibling-path> <default-branch>" agents/skills/maintenance/prompt-templates.md | wc -l | tr -d ' ')" -eq 1 \
  || fail "S13 execution worktree literal missing or duplicated"
grep -qF "Linked-worktree bootstrap recipe" agents/skills/maintenance/prompt-templates.md \
  || fail "S14 bootstrap reference missing from the blueprint edits"
grep -qF "the run's own done lock is free (done locks are keyed per-worktree" \
  agents/skills/maintenance/prompt-templates.md || fail "S15 per-run pre-Phase-0 gate missing"
expect_absent_flat "Phase 0 dedicated branch from main" agents/skills/maintenance/prompt-templates.md

# 7. Blueprint landing and archive per worktree.
grep -qF "merge --squash <branch>" agents/skills/maintenance/prompt-templates.md \
  || fail "S16 squash arm missing"
grep -qF "git worktree add --detach <temp-path> refs/heads/<default>" agents/skills/maintenance/prompt-templates.md \
  || fail "S17 temp-worktree arm missing"
grep -qF "git update-ref refs/heads/<default> <new-tip> <old-tip>" agents/skills/maintenance/prompt-templates.md \
  || fail "S18 compare-and-swap landing missing"
grep -qF "the archive commit is a per-run worktree commit" agents/skills/maintenance/prompt-templates.md \
  || fail "S19 archive scoping missing"
grep -qF "so the run's done lock is its own" agents/skills/maintenance/prompt-templates.md \
  || fail "S20 done-lock per-run scoping missing"
test "$(grep -oF "merge-wait-acquire" agents/skills/maintenance/prompt-templates.md | wc -l | tr -d ' ')" -eq 2 \
  || fail "merge landing lock acquire count moved (must stay once per blueprint)"
test "$(grep -oF "YYYY-MM-DD-authoring-<slug>" agents/skills/maintenance/prompt-templates.md | wc -l | tr -d ' ')" -eq 1 \
  || fail "authoring worktree literal uniqueness broken (auth_bodies pin would degenerate)"

# 8. Deviation-list registration (blueprint byte-parity protocol).
test "$(grep -oF "plan \`docs/plans/2026-09-24-p57-per-execution-worktree-isolation.md\`" agents/skills/maintenance/prompt-templates.md | wc -l | tr -d ' ')" -ge 2 \
  || fail "P57 deviation-list entries missing (Phase 0 and landing registrations)"

# 9. Authoring-side mechanical gates on the final tree.
python3 scripts/plan_readiness.py docs/plans/2026-09-24-p57-per-execution-worktree-isolation.md \
  || fail "readiness gate"
( cd "$REPO" && bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" ) || fail "hygiene scan"

echo "P57 validation: all gates passed"
```

### Task 1: Per-run locations in the scheduler state schema and failure-cap reads (SKILL.md)

Files:
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [x] In the State file section's `children[]` schema block, extend the entry shape from `"outcome_reason": null, "dispatch_plan_sha": null, "quota_signal": null` to `"outcome_reason": null, "dispatch_plan_sha": null, "quota_signal": null, "worktree": null` (the block must stay parseable JSON at `schema: 4`; the pins suite's superset check tolerates the added key). [class: IMPLEMENTATION_REQUIRED]
- [x] Add the `worktree` field paragraph to the State file section, after the `quota_signal` paragraph, carrying span S1 ("an execution child records on its own pending children[] entry once its blueprint-created per-execution worktree exists") and stating: the field carries the worktree path the child recorded, `null` for authoring and audit children, for execution entries whose child has not yet recorded the path, and for legacy entries predating the field; additive under schema 4 with no version bump; the writer is the dispatched execution child itself (one targeted field edit addressed to the primary checkout's `.ai-playbook/scheduler-state.json` in the explicit-rooted form, the claim duty's precedent), joining the child re-arm FIRST ACTION sanctioned-writer class; the Step 6 rewrite carries entries whole, so the field rides the existing carry-forward clause; the readers are the failure cap's manifest reads and the progress-mark count, resolved per the sites below. [class: IMPLEMENTATION_REQUIRED]
- [x] Progress predicate (Failure detection and the failure cap, the execution-child progress bullet): append span S2 after the existing checkbox-grep parenthetical, quoting it verbatim so the task text and its pin cannot drift: `resolved inside the entry's recorded \`worktree\` when that additive field is set, else the primary checkout's file`, and extend it with the same degraded fallback S3 already prescribes (when the entry's `worktree` field is set but the recorded path no longer exists, the read falls back to the primary checkout's file); and append one sentence scoping the bullet's archival arm to a ref-based read (span S21: `the archival arm is read ref-based`, using the `git cat-file -e refs/heads/<default>:<archived-plan-path>` landed-commit-test form) so a compare-and-swap landing is visible from any checkout, because a worktree-isolated child checks boxes in its own tree and a CAS landing never updates the checking turn's working tree. [class: IMPLEMENTATION_REQUIRED]
- [x] Rate-limited event ingestion bullet: extend the manifest locator with span S3 (the same repository-relative manifest path inside the recorded worktree when the entry's `worktree` field is set; the primary checkout's resolved tmp directory stays the fallback when the field is null or the per-run file is absent). [class: IMPLEMENTATION_REQUIRED]
- [x] Fast re-dispatch bullet: extend its manifest locator with span S4 (the same per-run resolution the rate-limited ingestion bullet applies). [class: IMPLEMENTATION_REQUIRED]
- [x] Sanctioned-writer enumeration (State file section, the child re-arm FIRST ACTION class): add span S5, the dispatched execution child's own-record per-run worktree recording (one targeted field edit setting the additive `worktree` field on its own pending entry, explicit-rooted to the primary checkout's state file, written once when the blueprint-created worktree exists; a lost or undetermined write degrades to the null-field fallback reads, which the field paragraph already covers). [class: IMPLEMENTATION_REQUIRED]
- [x] Companion pins in scripts/check_maintenance_pins.sh, each a dedicated grep that fails when its span is deleted: S1, S2, S3, S4, S5, S21 against `agents/skills/maintenance/SKILL.md`, plus a schema-block assertion that the parsed `children[0]` carries a `worktree` key with value `null` and `schema == 4` (mirroring the existing block-parse pin's mechanism). [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` (all existing pins still pass; the schema block still parses; the new spans verify). [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the Task 1 subset of the Validation Commands block (checks 1 and 5 only; later tasks' spans do not exist yet, so the full block stays RED until Task 5 lands). [class: REPOSITORY_TEST]
- [x] Commit: `feat: P57 per-run worktree field and per-run reads in the scheduler state schema` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Retire the interim constraint; record the parallelism and merge-order policy (SKILL.md)

Files:
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [x] Step 2 Fleet cap bullet: replace the sentence from `INTERIM EXECUTION CONSTRAINT (review r1 F1):` through the end of that sentence with span S7: `EXECUTION ISOLATION (landed 2026-09-24, P57, retiring the review r1 F1 interim constraint): execution children run in per-execution ad-hoc worktrees created off the default-branch snapshot per the execution blueprint, so executions are fleet members counted toward the cap of four like the authoring and audit kinds; the per-turn dispatch limits (at most one execution and one authoring per turn) and the audit-lane occupancy rules stand unchanged.` Keep the bullet's fleet-counting text (arms, strongest-arm order, below-the-cap dispatch) byte-identical. [class: IMPLEMENTATION_REQUIRED]
- [x] Invariants Fleet cap bullet: replace the clause `the execution lane holds at one in-flight child until P57's isolation lands, then worktree-isolated executions fill their slots` with span S8's operative form so the bullet reads: executions are fleet members, execution children run in per-execution ad-hoc worktrees off the default-branch snapshot (span S8), merge-lock landings stay serialized under the merge landing lock, and the per-turn dispatch limits sentence stands unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Supersession chain (Execution-lane concurrency stance): append the dated P57 link after the existing 2026-09-24 backlog-item link and replace the `INTERIM EXECUTION CONSTRAINT (landed 2026-09-24, P54, review r1 F1)` sentence and the `Until P57, the sanctioned overlap shapes` sentence with span S9 (`REWORK EXECUTED (landed 2026-09-24, P57,` naming this plan file): the rework executed per the seven-item list (worktree off snapshot, Phase 0 per worktree, done-lock scope per run via the per-worktree keying, archive commit per worktree, per-run discovery reads, the additive `worktree` field, the decided parallelism degree and merge-order policy restated in one sentence each), the interim constraint retired, the collision list standing as historical rationale, and the sanctioned overlap shapes now reading: up to four concurrent children across mixed kinds with executions worktree-isolated, and mutually exclusive landing critical sections under the merge landing lock. Historical chain links before P57 keep their bytes. [class: IMPLEMENTATION_REQUIRED]
- [x] Revisions ledger: add one entry at the top dated `2026-09-24 (P57 per-execution worktree isolation, docs/plans/2026-09-24-p57-per-execution-worktree-isolation.md)` summarizing this task's and Task 1's SKILL.md changes, the blueprint edits' registration in prompt-templates.md's deviation list, and the companion pins. [class: IMPLEMENTATION_REQUIRED]
- [x] Companion pins: presence pins for S7 and S8 (file-scoped: they live in the Step 2 fleet-cap bullet and the Invariants bullet, outside the stance section), S9 region-scoped to the stance section, the case-sensitive absence check for `INTERIM EXECUTION CONSTRAINT` in SKILL.md (rc 1 required, so the historical lowercase ledger wording cannot satisfy or break it), the absence check for `Until P57, the sanctioned overlap shapes`, and the exactly-once count for the Revisions entry date string. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh`. [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the SKILL.md halves of the Validation Commands block's checks 3 and 4 (the zcode.md halves of both checks stay RED until Task 3 flips zcode.md; this task's gate covers only the SKILL.md surfaces it edits). [class: REPOSITORY_TEST]
- [x] Commit: `feat: P57 retire the interim execution constraint; record fleet and merge-order policy` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Flip the runtime overlay's execution-lane clauses (zcode.md)

Files:
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`

- [x] Child classification markers bullet: replace the clause `authoring and audit children are fleet members counted toward the cap, and the execution lane stays single until P57's isolation lands` so the markers note reads that authoring, audit, and execution children are fleet members counted toward the cap, with execution children running in their per-execution worktrees (span S11: `execution children in their per-execution worktrees, P57`); keep the `G3b` merge-lock defer sentence byte-identical. [class: IMPLEMENTATION_REQUIRED]
- [x] Dispatch ladder second-lane bullet: replace the clause `the execution lane holds at one in-flight child until P57's isolation lands` inside the never-routed-in-session parenthetical with span S12's operative form (the strictly sequential wording superseded 2026-09-24 by the fleet cap, P54, and the single-child hold retired 2026-09-24 by P57's per-execution worktree isolation: the guards count, not exclude, and executions fill their fleet slots from per-execution worktrees; the never-routed-in-session carrier-class rule stands unchanged). [class: IMPLEMENTATION_REQUIRED]
- [x] Companion pins: the two absence checks (`stays single until P57`, `holds at one in-flight child until P57`) and the presence pins for S11 and S12 against `agents/skills/maintenance/zcode.md`. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh`. [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the Task 3 subset of the Validation Commands block (the zcode.md halves of checks 3 and 4). [class: REPOSITORY_TEST]
- [x] Commit: `feat: P57 flip the runtime overlay's execution-lane clauses` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Execution blueprint Phase 0 per worktree (prompt-templates.md)

Files:
- `agents/skills/maintenance/prompt-templates.md`
- `scripts/check_maintenance_pins.sh`

- [x] In the execution blueprint's fenced body, insert a new paragraph immediately after the EXECUTION CLAIM paragraph and before the pre-Phase-0 gate paragraph, headed `PER-EXECUTION WORKTREE, created before any plan work:` and carrying, in order: the creation command literal S13 (`git worktree add -b <execution-branch> <sibling-path> <default-branch>`, where `<execution-branch>` is the branch name the execute-plan Phase 0 convention derives and `<default-branch>` is the repository default branch), the snapshot rule (off the default branch ref, never off the primary checkout's working tree or current branch), the facts copy duty (copy the primary checkout's gitignored `.ai-playbook/facts.md` into the worktree first), the failure path (if the worktree cannot be created, delete this session's claim file per the EXECUTION CLAIM duty's delete arm and stand down writing nothing), the bootstrap duty (span S14: run the execute-plan skill's Linked-worktree bootstrap recipe in the worktree, its gitignored inputs being facts, reviews directory, and tmp directory, plus its closeout-baseline capture, before the PRE-STEP readiness gate), the Phase 0 resolution (the worktree's own `-b` branch is the Phase 0 dedicated branch: execute-plan Step 0.3 verifies branch state, nothing is created), and the scope sentence (all plan work, task commits, the archive commit, and the review loop run inside this worktree on the run's branch). [class: IMPLEMENTATION_REQUIRED]
- [x] Reword the pre-Phase-0 gate paragraph's opening sentence to per-run scope (span S15): `Before Phase 0 (in the worktree, after the bootstrap): verify no merge or rebase is in progress in the run's own worktree and the run's own done lock is free (done locks are keyed per-worktree on --show-toplevel); if either fails, stand down and write nothing.` [class: IMPLEMENTATION_REQUIRED]
- [x] Reword the Execute paragraph's opening sentence (the sentence opening `Execute {some_plan} via the execute-plan skill` and containing the clause `Phase 0 dedicated branch from` / `main`, which is line-wrapped in the file exactly that way) to the per-worktree form naming the worktree paragraph and the already-satisfied Phase 0 branch, keeping the rest of that paragraph (one task at a time, review loop, archive duties, done skill, landing) intact for Task 5. [class: IMPLEMENTATION_REQUIRED]
- [x] Register the deviation-list entry for this task's blueprint edits at the top of prompt-templates.md's deviations list, dated (2026-09-24, plan `docs/plans/2026-09-24-p57-per-execution-worktree-isolation.md`), paraphrasing the Phase 0 worktree paragraph, the gate rewording, and the Execute-paragraph rewording, with the not-part-of-the-backlog-source-text formula; and append to the older fire-time-gate deviation entry (the one quoting the superseded checkout-gate sentence in the present tense) a dated reconciliation clause noting that the 2026-09-24 P57 per-worktree rewording supersedes its quoted sentence, so the header list does not contradict the reworked body. [class: IMPLEMENTATION_REQUIRED]
- [x] Companion pins: the exactly-once count for S13 across prompt-templates.md (body-scoped by uniqueness; the authoring literal `YYYY-MM-DD-authoring-<slug>` must stay exactly-once so the suite's `auth_bodies` identification does not degenerate), the absence check that the execution body never carries the authoring worktree literal, presence pins for S14 and S15, and the existing execution-body absence pin for the authoring-claims literal continues to pass unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` and `python3 scripts/test_execute_plan_worktree_bootstrap.py` (the consumed recipe bytes untouched). [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the Task 4 subset of the Validation Commands block (check 6). [class: REPOSITORY_TEST]
- [x] Commit: `feat: P57 execution blueprint Phase 0 per-execution worktree` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Execution blueprint landing and archive per worktree (prompt-templates.md)

Files:
- `agents/skills/maintenance/prompt-templates.md`
- `scripts/check_maintenance_pins.sh`

- [x] Rework the execution blueprint's final-merge paragraph into the dual-arm landing, keeping the paragraph's `Finally squash merge to main` opening literal byte-identical (the pins suite's ordering pin anchors on it and requires it to precede `SUCCESSOR DISPATCH` and `FINAL STEP`), and keeping the acquire literal, the bounded-wait-then-defer behavior, the deferred-landing record duty, the release and release-failure fallback sentences, the dirt regression gate step, the landed-commit verification, the review-migration sentence, and the successor chain-nothing conjuncts byte-identical in meaning and position: inside the critical section, first re-verify which checkout holds the default branch (discover it by listing `git worktree list --porcelain` and checking each worktree's HEAD) and take the matching arm. Primary arm (a checkout holds the default branch): run the gate set there (the PII check + hygiene scan exit 0 required, the peer-byte guard unchanged, the gmail-author check), then squash there with span S16 (`git -C <default-checkout> merge --squash <branch>` followed by the commit; a conflicted squash is cleaned with `git reset --merge` and takes the deferred-landing path, keeping the branch and worktree). Temp-worktree arm (no checkout holds the default branch): create a uniquely named temporary worktree detached at the default branch tip (span S17: `git worktree add --detach <temp-path> refs/heads/<default>`), run the same gate set there, squash there (`git merge --squash <branch>`; the merge machinery polices main movement exactly as the primary arm's squash does), commit, land through the compare-and-swap ref update (span S18: `git update-ref refs/heads/<default> <new-tip> <old-tip>`, the old tip captured before the merge, refusing on any tip movement), and remove the temporary worktree on every exit path; a refusal or failure takes the deferred-landing path. The dirt regression gate runs over the arm's own working tree (the primary arm's checkout, the temp arm's temporary worktree). [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the Execute paragraph's archive sentence with span S19 (`the archive commit is a per-run worktree commit`): the archive move, the document-registry row append, the origins-closure check, and the archive commit run inside this run's worktree on the run's branch and ride the final squash merge; never as a primary-checkout commit. [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the done-skill sentence with span S20 (`so the run's done lock is its own`): the done skill runs in this worktree; done locks are keyed per-worktree on `--show-toplevel`, so the run's done lock is its own (stand down if a peer holds that worktree's done lock); the merge landing lock stays repo-keyed and is acquired at the landing critical section as prescribed. [class: IMPLEMENTATION_REQUIRED]
- [x] Register the second deviation-list entry for this task's edits, dated (2026-09-24, plan `docs/plans/2026-09-24-p57-per-execution-worktree-isolation.md`), paraphrasing the dual-arm landing, the archive scoping, and the done-lock scoping (paraphrase only, so the pins suite's exactly-once counts on the blueprint literals hold). [class: IMPLEMENTATION_REQUIRED]
- [x] Companion pins: presence pins for S16, S17, S18, S19, S20 against prompt-templates.md; the existing `merge-wait-acquire` exactly-2 count pin continues to pass (each blueprint acquires once); and the wrap-tolerant absence check for the superseded sentence (the flattened `Phase 0 dedicated branch from main` must have zero matches in prompt-templates.md; the plain line-oriented form is a no-op against the file's wrapped bytes and must not be used). [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh`. [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the full Validation Commands block (checks 1 through 9 all pass for the first time at this task). [class: REPOSITORY_TEST]
- [x] Commit: `feat: P57 execution blueprint dual-arm landing and per-worktree archive` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Final validation and closeout gates

Files:
- (none; this task runs the block)

- [x] Run → expect GREEN: the full Validation Commands block against the final tree (the pins suite, the bootstrap smoke suite, both absence groups, all positive spans, the schema-block parse, the count gates, the readiness gate, the hygiene scan). [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `python3 scripts/plan_readiness.py docs/plans/2026-09-24-p57-per-execution-worktree-isolation.md` (already inside the block; the standalone run is the certification oracle the done handoff records). [class: REPOSITORY_TEST]
- [x] Verify the Review Scope's out-of-scope set is untouched: `git diff --name-only` over the branch lists exactly `agents/skills/maintenance/SKILL.md`, `agents/skills/maintenance/zcode.md`, `agents/skills/maintenance/prompt-templates.md`, `scripts/check_maintenance_pins.sh`, and this plan file. [class: REPOSITORY_TEST]
- [x] Commit (if any gate fix produced bytes): `fix: P57 validation closeout` [class: IMPLEMENTATION_REQUIRED]
