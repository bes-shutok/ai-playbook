# Development lessons

Project lessons corpus for this repository's agent runtime, plan workflows, and
operational tooling. Lessons retain incident evidence; current workflow rules
belong in their owning skills and contracts.

## Core Concepts

- **Sequential execute-plan run:** the parent launches one native worker per
  task, verifies its result, runs the parent-owned done boundary, and only then
  starts the next task. The execute-plan skill is the operative workflow.
- **Parent-inline fallback:** the parent may perform the task when native
  delegation is unavailable before launch or after a worker is verified
  terminal. Unknown worker liveness means no edit and no duplicate launch.
- **Run-level claim and task record:** the execution claim prevents conflicting
  runs; the session manifest and task logs record progress and evidence. They
  do not represent a machine worker manifest or adapter contract.
- **Landing boundary:** the parent owns validation, review, and commit duties
  under the current `done` workflow.
- **Plans-authoring watcher:** authoring state and its watcher remain separate
  from execute-plan task execution.

## Historical execute-plan driver incidents (non-operative)

The following incident notes describe the retired adapter-backed worker driver
and its machine manifest. They preserve why earlier protections were added;
they are historical evidence only and do not prescribe current execute-plan
operations. Use the current execute-plan skill and runtime contract for runs.

1. A diagnostic launch under a live claim consumed a launch slot and then
   blocked relaunches until a dedicated recovery operation was added. The
   incident established the cost of using a mutating transition as a probe.
2. Two capacity-wedge recoveries used manifest backups, independent worker
   evidence, locked recovery operations, and readiness checks to leave an
   auditable record. Those driver-specific steps are retired.
3. A self-hosted driver plan landed stricter launch fields and evidence maps
   after its run had been seeded, requiring repeated seed reconciliation at
   contract boundaries. That manifest lifecycle no longer applies.
4. One driver run settled separate worker task commits and parent bookkeeping
   commits, then reused that composition for later tasks. Current execute-plan
   instead assigns the task landing boundary to the parent-owned done workflow.
5. A done worker could not hold the host lock or write the linked-worktree Git
   index; an implement worker hit the same index limit. The run moved lock and
   commit duties to the parent/host-capable runtime. Current execute-plan keeps
   those parent-owned duties directly.

## 6. Land a Squash Only From a Tree Merged With the Current Default Branch

**Principle:** Family D (recover and land through the owning machinery against current state;
a stale-base tree transplanted onto an advanced default branch silently reverts peers).

**Trigger:** a temp-index or worktree squash landing where the branch base predates the
default branch's current tip, and the squash commit is built from the branch tree directly
(`read-tree <branch-tip>` then `commit-tree -p main`).

**Required behavior:** before building the squash commit, integrate the current default-branch
tip into the run branch (merge or rebase; resolve conflicts faithfully) and build the squash
from the merged tree. Then diff the squash against the old default tip and require every
changed path to be attributable to the run: peer-added paths appearing as deletions (or peer
edits appearing as reversals) are the clobber signature - undo the ref move
(`update-ref` with both old and new), merge, and re-land. Tree-identity of the squash against
its source tree proves nothing about peer safety; that gate must be paired with the
run-scope diff check.

**Why this matters:** The worker-lifecycle landing built the squash from the branch tree while
peers had landed about fourteen commits after the branch base; the first diff-vs-old-main
check showed peer backlog files as deletions and peer edits as reversals. The ref move was
undone in one command, the merge integrated the peer landings (the driver file auto-merged;
three closed-origin conflicts resolved as deletions), the merged tree re-validated green, and
the re-land produced a 23-path run-scoped diff. Catching it at the diff check cost one redo;
landing it would have silently reverted every peer change.

Checkout-side sibling: this lesson owns peer safety at the ref move; live-checkout freshness after the move is owned by the post-landing reconciliation implementation and the stale-checkout discriminator in the Worktree-first standard section of agents/skills/execute-plan/SKILL.md.

Amend-side sibling: **base-branch immutability** - once a commit is reachable from the base branch it is never amended; corrections land as additive follow-up commits; amend is legal only inside a session's own unlanded branch before the landing critical section (origin docs/history/backlog/2026-10-02-base-branch-commit-immutability.md; witness: the 2026-10-02 18:09 amend of a peer's landed tip, folded in four minutes after another session landed it). The same expectation covers every record citing a landed sha: a cited sha is expected to stay reachable and immutable, so an amend of the cited commit surfaces as a cross-check mismatch in each record holding the old sha; the guard (`scripts/base_branch_amend_guard.py`: `check-head` refuses an amend with HEAD on the base branch, `reflog-scan` reports foreign `commit (amend)` entries) stops the commit path or names the rewrite instead of letting it pass silently.

Commit-form sibling: the landing commit itself is built from the staged index inside the worktree, the staged set derived mechanically from the branch delta (`git diff --name-only <old-base>...<branch>`) - a pathspec commit silently skips worktree-absent (deleted) paths, and a hand-built list rots at the first fold; tree equality against the branch tip is the gate that catches every commit-form drift (full rule: user-corpus lesson 545, derive a landing commit's pathspec from the branch delta).

## 7. Re-Derive a Plan's Edit Inventory From Live Bytes at Execution Start

**Principle:** Family H (verify the real thing, not the abstraction: a plan's edit inventory
is a claim about the base commit it was authored against, not a spec to reproduce).

**Trigger:** executing a plan task whose edit inventory was enumerated against a recorded
authoring baseline, while the base branch has moved between plan authoring and execution.

**Required behavior:** Before the first planned replacement, recount the live inventory
(byte-exact search for the target pattern) and diff the target file against the recorded
authoring baseline. Apply only the occurrences still present; record the already-satisfied
ones as inventory drift in the task log. Never re-apply an edit whose post-state already
matches: a duplicate application either no-ops silently or corrupts the byte-exact span the
plan prescribed. Treat an occurrence count in the plan as of authoring time; the executable
spec is the live file.

**Why this matters:** An em-dash removal task inventoried six occurrences against its
authoring baseline; by execution, the base branch had already applied four of them. The
recount found exactly the two surviving occurrences, and the task landed with only those two
edits plus a drift note. Blind execution of the six-item list would have failed the task's
own byte-exact assertions on the four stale entries.

**See also:** Lesson 6 (the stale-base sibling for landing machinery); Lesson 5 (verify the
real thing, not the abstraction).

## 8. Pass a Single-String Space-Split Tool Option as One Quoted Argument

**Principle:** Family D (single source of truth: the script's own argument contract, what its
parser declares and what its consuming helper accepts, is the invocation spec, not the
calling recipe's quoting).

**Trigger:** invoking a capture or migration script whose option is declared as one string
value that the script splits on whitespace (here `worktree_closeout_migrate.py capture
--dirs`), when a skill recipe shows the values as separate quoted arguments.

**Required behavior:** Before invoking, read the script's parser declaration and the helper
that consumes the value: an option consumed by a string-splitting helper takes ONE argument,
so the working form is `--dirs "<dir-a> <dir-b>"`; two separate quoted values make the
parser reject the second as unrecognized. When a skill recipe and the script contract
disagree, the script contract wins for the immediate call, and the recipe is a defect to fix
at its owning skill (record it; do not silently work around it forever).

**Why this matters:** The execute-plan capture recipe shows `--dirs "{reviews_dir}"
"{tmp_dir}"` (two arguments), but the script's dirs helper splits one raw string, so the
recipe's shape is rejected at parse time and the closeout baseline never gets captured that
way. This run's baseline capture succeeded only with the single quoted space-separated form.

**See also:** Lesson 4 (skill prose versus machine contract precedence);
`agents/skills/execute-plan/SKILL.md` (capture recipe carrying the two-argument shape).

## 10. Prove the Landing Base and the Completion Marks, Not the Diff Shape

**Principle:** Family H (verify the real thing, not the abstraction: a tree-identical gate
compares trees, never ancestries, and an archive rename moves bytes, never proof of work).

**Trigger:** landing a squash built from a run branch while the base branch may have moved
(peer sessions active), and archiving a plan whose executing session skipped the completion
ceremony.

**Required behavior:** Before any CAS ref move, assert the source tree's merge-base with the
base branch equals the base branch's current tip; a tree-identical check against the moved
ref passes vacuously on a stale base and the landing silently reverts every peer commit
(witnessed 2026-09-30: squash 2bcc562d reverted four peer landings, repaired by CAS delta
re-land 455ed9ec). An archived plan must carry its completion marks (checkboxes and a
review record binding the final bytes); an archive landing with unchecked task boxes and no
staged review record presents unverified work as done (witnessed twice 2026-09-30, landings
21178a3f and 66b91d23; backfilled a38ff7de after re-running each plan's Validation
Commands). Prevention items: docs/history/backlog/2026-09-30-execution-ceremony-prevention-witnesses.md.

**See also:** Lesson 6 (integrate the current default tip before building the squash);
Lesson 7 (re-derive inventories from live bytes at execution start).

## 11. Resolve a Disposition From Every Shape Its Machinery Writes

**Principle:** Family H (verify the real thing, not the abstraction: a disposition is a
state the lifecycle machinery writes in several shapes, and a probe keyed to one shape
classifies every other shape as open).

**Trigger:** sweeping a queue or registry for stale or undispositioned items when the
lifecycle's fold can be either an in-place status flip or a directory move into an
archive subdirectory.

**Required behavior:** Before classifying an item open, resolve every disposition shape
the machinery writes: the top-level file carrying a done or covered status line, the move
into an archive directory (completed/, rejected/), and a covering plan or log record.
Probe archive destinations by basename, not only the top-level path, and when a sweep
cuts entries, verify each cut against every shape first and print one receipt per cut.

**Why this matters:** a log-prune sweep's first pass classified every folded origin open
because it checked only top-level existence and status lines; origins moved into
completed/ by their executing sessions read as missing-and-open and the sweep cut nothing.
The corrected criterion (archive-directory membership counts as dispositioned) cut eight
genuinely landed entries; the naive criterion would have reported the whole registry
stale.

**See also:** Lesson 7 (re-derive the live inventory from disk at execution start);
Lesson 10 (prove the landing base and the completion marks).

## 12. A Ref-Level Landing Is Not Done Until the Post-Landing Reconciliation Runs

**Principle:** Family D (recover and land through the owning machinery against current
state; a ref advance moves the branch without refreshing any other checkout).

**Trigger:** landing by a ref-level move (compare-and-swap `update-ref`, push, or any
tail that does not merge inside each live checkout) while any checkout holds the base
branch, then reporting done without a reconciliation pass.

**Rule:** After the ref move, run the post-landing reconciliation over every live
checkout of the base branch before reporting done (`python3 scripts/reconcile_post_landing.py
--base <branch> --pre-tip <old> --post-tip <new>`); its exit-1 block rows are named work,
never a silent pass. A skip re-flares the stale-index class in that checkout: the stale
index materializes a staged reversal of exactly the landed paths.

**Why:** witnessed 2026-10-02 (playbook repo): two compare-and-swap landings advanced
the default branch while the primary checkout sat on it, each leaving staged deletions of
the just-landed files until the reconciliation restored them; an earlier peer landing's
skip left the same flare for a later session to adjudicate.

**See also:** Lesson 6 (land from a tree merged with the current tip - the pre-move half
of the same fence); Lesson 10 (prove the base and the completion marks); the
`check-landing` refusal mode of `scripts/reverse_squash_guard.py` (the stale-base half).

## 13. Re-derive the Work Item's Unclaimed State Before a Long Run's Final Write

**Principle:** Family D (recover and land through the owning machinery against current
state; a shared work queue's membership is state, not a snapshot).

**Trigger:** an execution (or any finalizing run) over a shared queue whose setup read -
target selection, claim, certification - happened at run start, followed by a long
in-run review loop before the final write (landing, closeout, or archive).

**Rule:** Immediately before the final write, re-derive the target's still-valid state
from the shared source of truth: the work item still exists where the queue keeps
unclaimed work (not archived or completed by a peer), the run's claim still names this
session, and no peer record (landing commit, archive move, receipt) now covers the same
unit. A peer completing the same item mid-run makes this run a superseded duplicate:
stand down without the final write, tear down the run's branches/worktrees/claims, and
record the supersession - never land a second copy of landed work.

**Why:** witnessed 2026-10-07 (playbook repo): an execution run selected a landed plan,
executed all tasks, and folded a zero-blocking review round while a parallel peer
execution of the same plan landed its own copy on the default branch and archived the
plan mid-run; the duplicate was caught only by the r2 verification worker's diff-base
observation, not by any mechanical gate, because every gate re-ran inside the run's own
worktree over the run's own branch bytes. The run stood down before landing; the
branch, worktree, and claim were torn down; the only unique deltas were wording-level
comment sweeps already tracked as the peer's residual rows.

**See also:** Lesson 12 (the post-landing reconciliation - the after-the-write half of
the same prove-current-state family); Lesson 6 (land from a tree merged with the
current tip); the execution blueprint's state-first successor-dispatch park (the same
re-derive-before-primitive discipline at dispatch time).

## 14. Capture Every Export an Acquire Prints; Release Locks Inside Their Freshness Window

**Principle:** Family D (a multi-field env contract is part of the lock's state; the
acquire output is the only complete copy of it).

**Trigger:** any script whose acquire prints several `export VAR=...` lines (done locks,
merge locks) while the matching release runs later in the session, and whose locks decay
by a staleness window.

**Rule:** export every variable the acquire prints, in the acquiring shell, immediately,
and keep them beside the run record - never just the token. Release inside the stated
staleness window. A release rebuilt from memory (one variable of several, or after the
window) is refused with a tool error, and a lock past its window decays by freshness on
its own: verify with the status subcommand instead of retrying the refused release.

**Why:** witnessed 2026-10-07 (playbook repo): an authoring self-landing captured only
`MERGE_LOCK_TOKEN` from `merge-wait-acquire`, which prints `MERGE_LOCK_DIR` and
`MERGE_LOCK_TOKEN`; both post-landing release attempts refused (`refusing shared session
load`, then `lock directory missing metadata`), and by then the 10-minute staleness
window had elapsed, so the lock had decayed (`merge-status: free`). The landing itself
was safe inside the window; only the release path was dead. The machinery-side release
gap is owned by the done-lock-release-mode-dispatch backlog row.

**See also:** Lesson 13 (re-derive state before the write); Lesson 15 (the peer-landing
twin of this rule).

## 15. Re-derive a Memorized Procedure's Owning File at Execution Time When Peers Land on the Same Repo

**Principle:** Family D (a procedure's source of truth is the file at the current tip;
a session-start read is a snapshot).

**Trigger:** a long session that read a workflow's procedure early, then executes a later
step of that workflow after peers have landed commits on the same repository.

**Rule:** before executing any step whose procedure came from an earlier read, re-read
the owning skill or script from the current tip. A peer landing can move a subcommand
between scripts, retire a flag, or reshape a step between your read and your execution;
the fail-loud aborts in the step (unknown command, empty echo) are the designed catch,
not a bug to work around.

**Why:** witnessed 2026-10-07 (playbook repo): this session's done closeout invoked
`done-lock.sh write-manifest` from its session-start skill read; a peer execution landing
earlier the same day (cf43eec4) had moved the manifest writer into the sweep-gates lib
(`done_sweep_gates_lib.py write-manifest`), so the call returned `unknown command` with
`OUTCOME: tool_error`, the empty-echo abort fired as designed, and the step was re-derived
from the current skill bytes before continuing.

**See also:** Lesson 13 (the work-item twin of this rule); Lesson 14 (capture the full
env contract when you do re-derive at acquire time).

## 16. An Operator Stop Order Suspends the Stage It Names, Not Finished Stages' Bookkeeping

**Principle:** Family A (a hold directive scopes to the stage it names; completed
stages still owe their recorded closeout).

**Trigger:** an operator order like "stop when X is ready" arrives mid-workflow, and
the workflow's doctrine makes post-X bookkeeping (landing, artifact transfer, teardown)
an automated no-ask step.

**Rule:** before ending a run on a stop order, re-read the governing doctrine and
separate the named stage from the finished stages' bookkeeping. Landing a plan is not
executing it; transfer-out and claim closure are not new work. Run the recorded
closeout mechanics, leave only the named stage unstarted, and report the split
explicitly.

**Why:** witnessed 2026-10-07: a certify-before-execute stop left a certified plan,
its seal, and eleven review records stranded in the ad-hoc worktree with a live
authoring claim; the operator had to ask why the lifecycle was not followed. The
landing doctrine already said landings are automated lifecycle steps with zero asks.

## 17. Record a Helper's Flag Gotcha in the Recall Corpus, Not Only Session Memory

**Principle:** Family D (a session-side note is a snapshot for one session; the
corpus is the recall surface).

**Trigger:** a helper refuses with a semantic you have seen before, and the earlier
note lives in chat memory rather than the lessons corpus.

**Rule:** when a helper's flag semantics bite and you recognize the bite from your own
history, capture the gotcha in the project corpus before the run ends, with the flag's
actual contract in one line. A memory line does not surface through recall hooks; the
corpus does.

**Why:** witnessed 2026-10-07: a squash-landing helper's `--expected-tip` is the base
branch's expected tip, not the source branch's; the gotcha was recorded in session
memory from a prior cycle, was not in this corpus, and re-bit the same day, costing a
refused landing and a retry.

## 18. Supply the Boundary-Claims File and Take the Foreign Set From the Gate's Own Refusal

**Principle:** Family D (a gate's refusal message is the authoritative enumeration of
what it actually checked).

**Trigger:** a closeout gate aborts with a claim-or-foreign violation, or a verify
subcommand fails on paths that are clearly evidence quotes, not records.

**Rule:** pass the boundary-claims file explicitly when the run claimed records;
without it the derivation scrapes the plan body and noise-fails on bare `.md` quotes.
When a pre-run emit preview disagrees with the writer's candidate set (different tree,
truncated count), take the foreign list from the refusal message's own named paths,
merging rounds until the write passes. When the run owns any staging doc, pre-build
the foreign list before the first write as the emission complement (re-run the emit
flag with the owned claims attached) and pass it up front.

**Why:** witnessed 2026-10-07: the emit preview wrote 2198 of 4506 candidates and
walked only the nested legacy reviews tree; three write-manifest rounds each named a
different slice before the merged list passed, and verify-records noise-failed on 107
quoted source paths until the claims file was supplied. Witnessed 2026-10-15:
skipping the pre-build refused the first manifest write on 2700 unpartitioned
candidates, costing a lock release and a full setup retry.

## 19. Thread a Boundary's Entry-Time Resolved Override Into Every Helper It Calls

**Principle:** Family H (verify the real thing: an override's reach is the call chain
it actually travels, not the boundary signature that accepts it).

**Trigger:** a transition resolves a per-call dependency override at entry (a test
seam, an injection point), then delegates through helper layers before the dependency
is consulted.

**Rule:** pass the resolved value down as a parameter through every layer; a helper
that re-reads the instance default compiles green, passes the default-path tests, and
silently ignores the override one link deep. Prove the reach with a two-sided witness:
make the constructor's dependency refuse every call, make the per-call override
accept, and assert the acceptance governs end to end.

**Why:** witnessed 2026-10-09: the startup reconciliation's digest route resolved a
per-call commit lookup at entry, but a link verifier two layers down still consulted
the constructor's lookup, so a refusing default blocked only one link of the chain;
the gap took a tri-lens review to surface.

## 20. Rewind Every Queued Side Effect in a Between-Runs Fixture, Not Only the Records

**Principle:** Family H (a fixture simulating "another run happened" models the real
persisting surface, or the next boundary adopts the leftover).

**Trigger:** a test drives two runtime generations in one process (done flow, then a
reconciliation or claim against the seeded after-state) and the second boundary
refuses, adopts, or observes bytes that moved.

**Rule:** enumerate every durable side effect the inter-run boundaries write (a
prepared handoff intent awaiting the next claim, a persisted stamp, a generation bump)
and unwind all of them in the fixture's between-runs step; rebuilding the manifest
records alone leaves the queue state live, so a plain claim adopts the stale intent.
Take byte snapshots from the already-held driver/adapter instead of constructing a
second one, whose construction persists its own stamp.

**Why:** witnessed 2026-10-09: three of four green-iteration failures in one task
were fixture realism gaps of this class (an adopted handoff intent, a stamp persisted
by a second driver construction, a scope token attached at launch not claim), each
indistinguishable from a production defect until the fixture was rewound.

## 21. A Mandated Durable Record Owes a Mandated Landing Path

**Principle:** Family H (a workflow that orders an artifact into existence also owns the
artifact's commit; a landing that stages only pre-declared paths strands the run's own
output).

**Trigger:** a gated workflow requires filing durable records (backlog rows, review
records, receipts) mid-run, and the run later closes through a bounded transition that
authorizes only pre-declared archive paths, or through a recovery landing composed after
the deadlock.

**Rule:** every artifact a workflow's contract mandates must have a mandated commit
route: either the run commits it before its terminal boundary, or the bounded
transition's authorized path set includes the run's own filings, or the run records a
tracked landing path. A recovery landing must reconcile the run's recorded filings
against `git status --short` so an untracked owned filing fails closeout instead of
becoming orphan dirt discovered only by a later provenance investigation.

**Why:** witnessed 2026-10-10: a plan run whose archive commit was gate-refused landed
through a targeted recovery that staged only plan files; the six backlog rows the run
had filed during execution and review stayed untracked with no owner until a
provenance investigation attributed them. Filed as backlog row
`docs/history/backlog/2026-10-10-execute-plan-run-filed-backlog-rows-stranded.md`.

## 22. Hold the Merge Lock Across a Landing Commit; a Free-Lock Check Is Not a Hold

**Principle:** Family E (temporal and ordering invariants: the serialization of a
shared-checkout critical section comes from holding the lock across it, not from
checking it beforehand).

**Trigger:** any landing commit that touches a shared-checkout surface (the docs
orphan branch, directives homes, completed-history paths) whose workflow prescribes a
lock acquire before the commit.

**Rule:** acquire the merge lock before the landing commit, in the same ordered span,
even when a status check immediately beforehand shows the lock free. The check answers
a question about the past; only the hold serializes the section against a peer landing
that starts between the check and the commit. A release attempted after an
unserialized landing refuses with no hold to release: the tool error is the witness
that the section ran exposed.

**Why:** witnessed 2026-10-10: a directives-home landing committed first, then
acquired the merge lock; the release refused (no hold), and the free-lock check before
the commit had been treated as satisfying the ordering. No contention occurred, but
the ordering miss was recorded in the run record as the thing to not repeat.

**See also:** Lesson 14 (capture every acquire export; release inside the freshness
window); Lesson 15 (the peer-landing twin of this rule).

## 23. A Governance Protocol Without an Operative Home Binds Nobody

**Principle:** Family D (single source of truth: a rule's enforcement surface is
the operative contract that references it, not the analysis prose that proposed it).

**Trigger:** executing a program whose governing protocol lives only in an audit
or analysis document, while the skills, guidelines, and validators that will do
the work carry no reference to it.

**Rule:** before routing work that a governance protocol governs, land the
protocol's operative home first (the guideline section, the skill's stage arm,
the validator check), and route the protocol-carrying item before the work that
depends on it. A protocol only an analysis document states is invisible to every
contract that acts; its violations surface only through the operator reading the
output.

**Why:** witnessed 2026-10-10: an admission protocol prescribed by an audit
(warning-only until first true catch, stated sunset, pre-registered removals
row) was skipped by three same-day plan routings that added a hard-exit gate and
tracking surfaces, because no skill contract or guideline referenced the
protocol; the operator caught the violations, and the reconciliation plus the
protocol's durable-landing routing followed.

**See also:** Lesson 21 (a mandated durable record owes a mandated landing path).

## 24. A Standing Automation's Prompt Is Its Identity; Do Not Share the Parent's Recognition Span

**Principle:** Family H (the workflow that orders a record into existence owns
that record's identity distinctness from every recognition span the machinery
matches).

**Trigger:** arming or restoring a recurring cadence automation in a repository
whose loop recognizes its own records by prompt-span shape (an opening line plus
a repository-root containment).

**Rule:** word a standing cadence's payload so it neither begins with the loop
template's opening line nor lacks its lane's classification marker: a
scheduler-shaped prompt beside the armed parent is exactly the extra ENABLED
span match a duplicate-parent tripwire flags (and its human-clear deletes), and
a fired marker-less record inside the listing's freshness window classifies as a
both-lane occupant. A distinct opening line plus the lane's child marker keeps
the record invisible to the parent tripwire and an occupant of only its own lane.

**Why:** witnessed 2026-10-10: a 05:49 authoring cadence disappeared four times
in as many days while armed with a scheduler-shaped payload; the fifth
restoration used a non-span-matching, marker-carrying wording, with the tripwire
hypothesis recorded as the first lead if the record disappears again.

**See also:** Lesson 23 (route the protocol home before its dependents).

## 25. A Test Harness Main Block Belongs at File End; Classes After It Never Run

**Principle:** Family H (the workflow that appends test classes to a shared
runtime file owns the file's execution-order integrity, not only its syntax).

**Trigger:** appending a new test class to an existing test module that may
already carry an `if __name__ == "__main__": unittest.main()` block somewhere
mid-file.

**Rule:** before adding a test class to a shared test module, locate the main
block; it must sit after the last class definition, and an append must re-check
that invariant afterwards (an append lands textually after the block,
re-orphaning every class defined before the append). A "NO TESTS RAN" or a
suspiciously small collected-test count under direct execution is the symptom;
a green suite that silently excludes the new class is the danger.

**Why:** witnessed 2026-10-10: a plan task's new test class was verified green,
then discovered dead under direct execution because a mid-file main block
predated it; the fix (moving the block to file end) was itself re-broken by the
next append and had to be moved again.

Companion discipline: verify a new test actually collects (the runner's own
test listing), not only that the file executes.

## 26. A Fold Must Re-Sweep Every Scope-Declaring Surface, Not Only the Task Text

A review fold that enlarges a plan's operative span set (an edit area, a
predicate, a scope enumeration) must re-sweep every surface that restates the
scope, Terms, Gist & Examples, Outcome bullets, Assumptions, Review Scope,
Standing constraints, in the same fold, not only the task text it amends.
Task text is the instruction of record, but executors, later folds, and
auditors reconcile against the summaries, and a summary left behind re-creates
the exact defect the fold closed at the summary layer. Two rounds of the same
authoring cycle staged the identical finding class (`fold-incomplete-summary-surfaces`)
against two different folds before the pointer-form fix landed ("the span set
Task 3 names"), which makes the summaries structurally unable to lag.

**Why:** witnessed 2026-10-10 in the machinery-admission-protocol plan's review
series: the r1 fold's ad-hoc-span enlargement and the r3 fold's log-mediated
enlargement each left Gist/Outcome (and the r3 fold left Terms) stating the
narrower enumeration; r2 F1 and r4 F1 staged the same class both times.

Companion discipline: prefer the pointer form in summaries ("the span set
Task N names") over restating enumerations; a pointer cannot drift.

## 27. Absence Findings Name Their Byte Source; Re-Grep at the Current Tip

A review finding that asserts something is missing (a marker line, a freeze
entry, a queue row) is only as good as the copy it was read from. When the
target file lives on a moving branch, a worker reading a checkout copy whose
vintage predates the last landing reports the pre-landing world as fact, and
the false absence rides into staging as a finding that costs a full
adjudication round to discard.

Rule: an absence finding on a fast-moving file names its byte source (path
plus commit or digest), and a blocking absence claim is re-derived at the
current reference tip (`git show <tip>:<path>`) before it is staged; an
adjudicator discards an absence finding whose vintage cannot be produced.

**Why:** witnessed 2026-10-10 in an authoring cycle's r1: a worker staged the
queue entry "carries no Frozen line" as a finding, but the freeze had landed
on main before the round; the worker's copy of the queue file predated it,
and the finding folded as a discarded false positive.

## 28. Routing State Sweeps the Composed Duty Chain, Not Only Its Declaration

A plan that introduces routing state (a mark, flag, or precedence promise) into a composed instruction set must, at authoring and again at review, enumerate every consumer that reads the routing predicate - including the duties and stages the plan does not edit - and pin enforcement at the site where the routing decision is made. Routing prose where the state is declared ("routes as the highest-precedence candidate", "clears only by X") enforces nothing: a consumer with a fixed duty order that reads only its own ready-predicate still treats the marked item as an ordinary candidate, and the state's own sanctioned clearing event (a prune by a landing born of that dispatch) then launders the leak. The authoring-side check is one sweep: list the consumers, name the comparison each makes, and add the hold where the ordering lives.

**Why:** witnessed 2026-10-10 in the renewal-trigger plan's certification: the Renewal-pending mark carried precedence and clearing prose, but the monitor's fixed duty order ran dispatch before the renewal duty and read only "top surviving unfrozen entry", so a freeze-cleared marked entry stayed a dispatch candidate; the cross-session finding staged the gap post-certification and the next version folded the bounded dispatch hold into both composed surfaces, certified in the final round (seal: docs/history/review-certs/investigate-renewal-trigger.md).

Companion discipline: when adjudicating a deliberate enforcement absence, record it in Assumptions with the rejected alternative, so the Terms' liveness promise cannot over-claim the drafted enforcement.

## 29. A Script That Spawns Child Interpreters Inherits Your PATH Problem

Invoking a repo script with one interpreter does not fix the interpreter its
own subprocesses spawn. A wrapper shelling a bare `python3` resolves whatever
`PATH` holds at run time, so a script fine on its own fails under an agent
session whose `PATH` lacks the project's tooling venv, and a "nested" call
(`python3 <venv-python> script.py`) fails differently again (the outer
interpreter parses the venv binary as source). The failure surfaces far from
the cause, as a parse error or a slug-derivation abort inside the child.

Rule: when a repo documents a tooling venv, prepend its bin directory to
`PATH` for the whole session before the first script invocation, and invoke
the venv binary directly, never as an argument to another interpreter; a
script that shells child interpreters is validated in the same environment
its children will see.

**Why:** witnessed 2026-10-11 (playbook repo): an execution-claim helper
aborted with "artifact slug derivation failed" because its own `python3`
subprocess was the system 3.9 (no `tomllib`), while the invoked venv binary
was fine; the same session also hit the nested-invocation SyntaxError shape.

## 30. Build a Schema-Gated Sidecar From the Validator's Checks, Not by Iteration

A review-staging sidecar and its Markdown record form one validated pair, and
the validator couples the surfaces: enum spellings, a commit field's canonical
"none" on both sides, worker counts equal to panel rows, required severity
groups even when empty, and a section heading whose exact shape a regex
anchors. Drafting the sidecar from memory and fixing validator errors one at
a time burns a round per mismatch, because each fix can trip the next coupled
invariant.

Rule: before authoring a schema-gated artifact by hand, read the validator's
check list and satisfy every coupling in one draft; treat any validator error
as a prompt to re-read the full check family, not a single predicate, and
prefer producing the artifact with the schema's own tooling over hand-writing
it when one exists. The derivation discipline covers the artifact's name too:
take the sidecar path the machinery emits or names in its own refusal (the
validator derives the sidecar name from the record's name by replacing its
`.md` suffix), never a hand-composed double extension.

**Why:** witnessed 2026-10-11 (playbook repo): a hand-built delta-certification
sidecar needed five validator rounds (review_mode enum, last_fix_commit
disagreement, counts parity, missing severity groups, soften heading
parenthetical breaking the section regex) that a single read of
validate_review_staging.py's checks would have prevented.

**Why (second witness):** the 2026-10-13/14 authoring cycles passed the
tool-minted halves and still lost repeated preflight rounds to the
hand-filled sections (the coverage list's shape, a per-panel-row launch
field, an empty-array edge, an extension-nested usage block, and
inherited-coverage rows required by a yes verdict): the residual schema
surface lives exactly in the sections no tool writes, so a scaffold mode or
schema reference has to cover those too.

## 31. Worktree Recreation Is Not Recovery for Untracked Run Artifacts

A worktree deleted and re-added from its branch tip restores only tracked
content. Every untracked run artifact it held (review records, worker
reports, a gitignored facts copy) is silently gone, and the loss surfaces
later as a missing file a gate or a reader expected to exist. Local APFS
snapshots can recover the corpus, but mounting one requires root.

Rule: before any delete or restore of a worktree, inventory its untracked
corpus and copy owned artifacts to the primary checkout; treat
`git worktree add` as provisioning, never as recovery; attempt snapshot
recovery only when the root password is available, and otherwise document the
loss in the surviving record that replaces the lost chain.

**Why:** witnessed 2026-10-11 (playbook repo): the authoring worktree was
externally deleted mid-review-round and restored from the unchanged branch
tip; the three prior review records, their worker reports, and the gitignored
facts copy were lost (snapshots existed, mount refused without sudo); the
certifying round's record carries the continuity note.

Re-witnessed 2026-10-12 from the recovery side (playbook repo): the removed
worktree's seven review-record markdowns were lost, but their validated
`.stats.json` sidecars had already reached the primary reviews home, and the
records were rebuilt byte-faithfully from the sidecars plus the session's
generator state, cross-checked by sidecar digests and a fresh validator run
over the landed bytes.

## 32. Write Certification Seals in the Machine-Resolvable Shape

The seal parser resolves only `## round N` headers carrying snake_case fields
(artifact, round_start_commit, round_start_digest, round_close_commit). Both
legacy corpus shapes (human-labeled "## Round N" sections and flat
"- Artifact:" bullet lists) parse as zero entries, so a seal written in the
corpus's visible style silently fails every consumer while looking correct.

Rule: append new certification seals as `## round N` blocks with the four
snake_case fields; keep prose in the preamble above the first header (only
lines before the first header are free-form); verify with the parser before
relying on resolution.

**Why:** witnessed 2026-10-11 (playbook repo): a seal draft copied the
corpus's "## Round 7" exemplar shape and the validator still reported no
resolvable entry; rewriting in the machine shape resolved the round
immediately.

## 33. Index-Only Deletions Silently Re-Sync From the Working Tree

`git update-index --remove <path>` is a no-op when the path still exists in
the working tree: instead of removing the entry, the command re-syncs it from
the file on disk. An index-composition flow (temp index, `write-tree`,
`commit-tree`) that "removes" paths this way commits those paths untouched,
and the landing silently loses every deletion it announces.

Rule: in any index-composition flow, remove tracked paths with
`git update-index --force-remove <path>` (or delete the working-tree file
first), and verify the composed tree before committing it: the temp-index
diff against the base tip must show exactly the announced deletions. A
landing whose announced deletions are absent from the composed tree is a
defect, not a success.

**Principle:** Family H (the workflow that composes a tree into existence
owns verifying the composed bytes, not the intent it issued).

**Why:** witnessed 2026-10-11 (playbook repo): a merge-locked plan landing
built with temp-index plumbing carried only the added plan file; its three
announced backlog-row deletions never staged because `--remove` re-synced
the entries from the working tree, and the gap surfaced only in the
post-landing commit census; a second lock-hold repaired the landing with
`--force-remove` (100 deletions).


## 34. land_squash --expected-tip Is the Expected Base Tip, Not the Source Tip

The squash-landing helper's `--expected-tip` names the tip the BASE branch is
expected to sit at during the landing, not the source branch's tip; the
naturally-planned first invocation (passing the branch you just rebased) is
refused with "base branch tip moved: refs/heads/main is at <base> but
--expected-tip is <the value you passed>". `--expected-base` carries the
recorded base pin for the parentage gate; after a sanctioned rebase both
values are the current base tip.

Rule: before any landing-helper invocation, re-derive each flag's referent
from the helper's refusal messages or usage text (run `probe` first), never
from the flag name's most familiar reading; a refused landing mutates
nothing, so the correct response is re-derive and retry, not force.

**Principle:** Family D (a gate's refusal message is the authoritative
enumeration of the contract; read it before re-deriving the argument
mapping).

**Why:** witnessed 2026-10-12 (playbook repo): the first `land` of a clean
r1-ready branch passed the source tip as `--expected-tip` and was refused;
the refusal text alone disambiguated the mapping and the retry passed.

## 35. Lock Exports Die at the Tool-Call Boundary; the Hold Record Is the Recovery Source

An agent session's shell invocations are separate processes: the `MERGE_LOCK_DIR`/`MERGE_LOCK_TOKEN` (or `DONE_LOCK_*`) exports from an acquire step are absent in a later tool call, and a release run there reports `tool_error` ("re-export them from your acquire Step 0 output"). The hold's own metadata record (the lock root's `meta.env`) carries the same token and holder identity, so the owner can recover the exports without any bypass arm.

Rule: run every mutating step of a lock lifecycle that must share the lock
context (land, release, finalize) in the SAME shell invocation as the
acquire when possible; when a later call is unavoidable, re-export from the
recorded hold metadata only after confirming the recorded token matches your
own acquire output; never use `--from-holder` for a hold you still own and
can re-export, and never release a hold whose holder identity is not yours.

**Principle:** Family D (a hold's own records are the single source for its
recovery; the env path and the metadata path must name the same token before
either is used).

**Why:** witnessed 2026-10-12 (playbook repo): a merge-lock release after a
multi-call landing window refused with the lost-exports error; the hold's
`meta.env` token matched the session's acquire output and the re-exported
release passed on the first retry.

Re-witnessed 2026-10-16 (playbook repo): the lock families also differ in
export names, so one shell is not enough by itself: the done lock's
`wait-acquire` prints the `DONE_LOCK_*` pair while the landing consumer
wants `MERGE_LOCK_*`; alias the pair in the same acquire shell
(`export MERGE_LOCK_DIR="$DONE_LOCK_DIR"
MERGE_LOCK_TOKEN="$DONE_LOCK_TOKEN"`) before `land-worktree`, and the
first landing attempt stops refusing with `requires MERGE_LOCK_DIR set`.

## 36. Measure the Full Gate's Private Dimensions Before Round One

A readiness validator can carry checks its pre-round invocation never runs: the
evidence-envelope limits (per-criterion and per-task byte caps) lived only in
the full gate, so a plan sailed through four review rounds and a certification
before the done-boundary gate refused on a 597-byte criterion, then again on a
4096-byte aggregate, each refusal costing a fold and a fresh round. A second
copy of the same shape: fold text adopted from a review finding verbatim
(without re-grounding it in the code it names) reintroduced a defect as a
blocking finding one round later.

Rule: before the first review round, run the plan through every gate dimension
the eventual done or execution boundary will enforce, not only the structural
pre-round subset; and fold every review fix by re-deriving its claim against
the artifact it names (the function, the routing arms, the live pins file),
never by transcribing the finding's prose.

**Why:** witnessed 2026-10-12 (playbook repo): the boundary-reliability plan
certified at r10, then failed the full gate on evidence-byte limits it had
carried since v1, and burned r11 through r13 re-shaping criteria; the r9 fold
of the r8 fix text produced an unsatisfiable witness that r9's own panel
caught, and the r15 sweep line repeated the shape.
## 37. Detached-HEAD Done Setup Needs an Explicit Lock Label

`done_run.sh setup` derives its done-lock label from
`git branch --show-current` with an `|| echo unknown-branch` fallback, but that
command exits 0 with empty output on a detached HEAD, so the label composes
empty, and `done-lock.sh wait-acquire` refuses with `--label requires a value`
(`OUTCOME: tool_error`) on every retry, a reproducible setup failure that
looks like a lock-backend fault. Pass setup's own `--label TEXT` explicitly
whenever the closeout runs in a detached continuation checkout (the recorded
workaround for the dispositioned-manifest classifier blocker lands in exactly
that shape).

**Why:** witnessed 2026-10-12 (playbook repo): two setup attempts in a fresh
detached continuation worktree failed with the lock tool_error while a manual
`wait-acquire` in the same checkout passed; the only delta was the empty
label.

## 38. A Gate's Refusal Cannot Ride a Pipeline Tail or Discarded Stderr

A verdict-bearing command gates control flow through its exit status, and a
pipeline returns the LAST command's status: `gate ... | tail -n 3` turns a
refused gate into a passing composition and the run continues past the
refusal. The same masking family discards a producer step's stderr and
swallows its status, so its output never lands and the consumer step operates
on a missing input without noticing.

Rule: run a gate whose verdict controls the next step with its status observed
directly (`if ! gate ...; then ...`), never as a non-final pipeline element;
when a step produces input a later step consumes, verify the artifact landed
(path probe, digest match when precision matters) before consuming it; never
append `2>/dev/null` to a step whose failure changes what the next step
should do.

**Why:** witnessed 2026-10-12 (playbook repo): a temp-index landing piped the
base-freshness probe and the pre-swap parentage gate through `tail`, landed
past two refusals, and CAS'd a stale-base commit that clobbered a peer commit
(repaired additively the same day); in the same session a record-migration
`cp` built from an unset variable with discarded stderr copied nothing, and
the later worktree removal destroyed the only markdown copies. Re-witnessed
the same day by an independent session: the same landing pipeline piped the
pre-swap parentage gate through `tail`, so the refusal did not stop the run
and the landed diff had to be verified sound only after the fact. Re-witnessed
2026-10-14 (same repo) in the measurement variant: a timing batch wrapped each
run as `{ /usr/bin/time -p cmd; } 2>/dev/null`, discarding the timing report
itself (`/usr/bin/time` writes its report to stderr), so every measurement
came back empty and the batch had to rerun with the stderr forwarded to the
consumer (`2>&1 >/dev/null | awk`).

## 39. A Linked Worktree's .git Is a File, Not a Directory

Inside a linked worktree `.git` is a file holding a `gitdir:` pointer, so any
hand-run composing repo-internal paths from `$PWD/.git/...` (a temporary
`GIT_INDEX_FILE`, a lock path) targets a non-directory and fails. Resolve the
real git dir first (`git rev-parse --git-dir`) and derive index and lock paths
from it. In the primary checkout the two agree, which is why the assumption
survives until the first worktree run.

**Why:** witnessed 2026-10-12 (playbook repo): a temp-index landing attempt in
an ad-hoc authoring worktree failed on `GIT_INDEX_FILE="$PWD/.git/..."` and
unblocked only after re-deriving the path from `git rev-parse --git-dir`.

## 40. A Ref-Only Landing Moves the Branch, Not the Checkout

A temporary-index landing updates the default-branch ref without touching any
checkout's index or working tree. The primary checkout afterward reads its
pre-landing bytes as if current. Its status can show the just-landed files as
staged deletions, and `git merge --ff-only` reports "Already up to date"
because only the ref moved. The next pathspec commit there stages those stale
bytes, silently reverting what the landing (or a peer landing rider) put on
the branch.

Rule: after any landing that moved a ref without a checkout (CAS, temp-index,
commit-tree), classify the primary checkout's paths against the landed tree
before composing any commit there. A path byte-current against the tip blob
stays. A stale ancestor of the tip blob is restored from the tip. Uncommitted
local work stays as a named block and is never staged. Rebuild shared-log
edits from the tip's bytes (`git show <branch>:<file>`), never from disk
bytes. Treat a ref-only advance as invalidating every derived read (status,
diff, log spans) until each is re-derived from the ref.

**Principle:** Family D (state-first: after a ref-only landing the branch ref
is the only truth; a checkout's on-disk bytes are not evidence of the
branch's content).

**Why:** witnessed 2026-10-12 (playbook repo, three independent sessions in
one afternoon): two pathspec commits from stale primary bytes resurrected a
peer's pruned dispatch entry and deleted its prune receipt, and a third
session's post-landing primary showed its own just-landed plan file as a
staged deletion; each repair rebuilt the file from the landed tip's bytes
with per-path classification, leaving uncommitted peer dirt untouched.

## 41. A Runtime's Own Lifecycle Is Investigable Only From That Runtime

A plan whose subject is another agent runtime's internal behavior (its
teardown, its session lifecycle, its resource handling) cannot be root-caused
from a foreign harness: the foreign session sees only the subject's on-disk
residue, so it can hypothesize about the mechanism but never observe it. The
symptom-level fix a foreign session authors (a sweep that cleans the residue)
treats the wound, not the cause, and the root-cause question survives every
landing of the symptom fix.

Rule: at queue intake, classify the entry's main idea before claiming it.
When that idea is another runtime's own lifecycle, do not author the plan in
this harness; hand off instead: restate the main idea as the root cause on the
queue entry and lift the freeze, write an evidence dossier holding everything
the foreign investigation established, and demote the foreign-authored
symptom fix to a backstop arm that revives only after the root cause lands.

**Principle:** Family H (verify the real thing, not the abstraction: the
producing runtime's own lifecycle is observable only from that runtime;
on-disk residue is an abstraction of the failure, never the mechanism).

**Why:** witnessed 2026-10-13 (playbook repo): a worktree-residue sweep plan
reached round 2 in this harness before the operator redirected it; the
residue's producing teardown was observable only from a session of the runtime
that leaves it, that runtime's binary carried no greppable marker string, and
the receiving runtime's author session had its worktree open within minutes of
the handoff.

## 42. A Scratch Worktree Checks Out a Commit, Not Your Working Tree

`git worktree add --detach <path>` (and any worktree add without a branch
carrying the edits) materializes the named commit only. Uncommitted rewiring
in the authoring checkout - a mid-refactor script, an unwired helper, a
half-converted call site - does not exist in the scratch checkout, so a probe
suite run there exercises the pre-edit bytes and reports against the very
defects under repair. Several green or red probe results in a row can be
statements about two different trees.

Rule: before probing repair work from a scratch worktree, commit the work
under test to a branch first and add the scratch checkout at that branch tip;
never at the authoring HEAD while edits are uncommitted. When a probe result
contradicts the expected post-repair behavior, verify the bytes the probe
actually read (`git -C <scratch> rev-parse HEAD`, `git -C <scratch> diff HEAD
-- <probed-path>` empty) before debugging the probe logic or the repair.

**Principle:** Family D (state-first: a worktree's checkout is a snapshot of
one commit; on-disk edits elsewhere are not part of what a probe there reads).

**Why:** witnessed 2026-10-14 (playbook repo): a 14-arm probe battery against
a heredoc-router rewiring kept failing on the old wiring because the scratch
worktree was detached at the pre-edit HEAD; the fix was committing the rewire
first and re-adding the scratch checkout at the new tip, after which the same
probes passed unchanged.

## 43. A Per-Call Shell Resets cwd to the Primary Checkout

A shell tool that starts every call in the session's default checkout does not
persist `cd` across calls. A multi-call sequence inside an ad-hoc worktree
silently returns to the primary checkout after every call, so the next command
composed without an explicit re-entry runs against the base branch's checkout.
A landing rider executed there commits to the base branch ahead of its witness
and outside the merge lock, the exact violation the worktree-complete landing
class prevents, and the repair needs an additive restore because a
base-reachable commit is never amended.

Rule: in any worktree-scoped phase, begin EVERY shell call with an explicit
re-entry (`cd <worktree> &&` as the first compound) and verify placement
before any write, stage, or commit (`pwd`, `git rev-parse --show-toplevel`,
current branch). Address artifacts in another checkout by rooted paths
(`git -C <root>` or absolute), never cwd-relative; the reverse slip (a
cwd-relative refresh of a primary-resident artifact from the worktree) misses
it the same way.

**Principle:** Family D (state-first: the checkout a command runs in is part
of the command's state; verify it at every call, never assume it persisted
from the previous one).

**Why:** witnessed 2026-10-14 (playbook repo): an authoring landing's
prompt-log prune and its rider commit ran in the primary checkout because the
shell cwd reset between calls, pruning the dispatch entry on main before the
landing carried its plans-root witness; the repair took an additive
byte-identical restore (9c1721098, 6ea0cc270) plus a worktree re-run of the
landing tail. Same run, second slip: a claim heartbeat refresh read from the
worktree against the primary-resident claim file and missed it. Siblings:
#39, #40, #42.

Runtime variant, witnessed 2026-10-16 (ZCode Bash): that runtime's shell
PERSISTS cwd across calls and across summarization gaps, so the slip arrives
inverted - a stale unexpected directory (here a reviews-home subdirectory)
survived a compaction, and `git status` run from it still answered correctly
because git walks up to the repo root, hiding the misplacement until a
repo-relative probe or write resolved against the wrong base. Same rule,
plus one addition: after resuming a session, run `pwd` before the first
relative-path operation.

## 44. A Machine Receipt Lives Where Its Auditor Parses

A removal that a mechanical audit validates needs its receipt in the grammar
and surface the auditor's parser actually reads. The prompt-log prune audit
reads its receipt ledger from content lines inside the rolling log itself
(`PLAN-PROMPTS-PRUNE: <slug> -> <witness>`), while its commit-message scan is
a different, stricter surface with its own anchored shape. A receipt written
only into the landing commit's message is invisible to the ledger scan: the
audit flags the entry REMOVED-WITHOUT-WITNESS and the removal reads as
uncovered even though the witness exists one surface away.

Rule: before satisfying any receipt, ledger, or provenance requirement, derive
the required location and line grammar from the auditor's parser (read the
checker first), write the receipt there in the same change as the removal, and
re-run the audit before landing; a receipt in an adjacent surface the checker
does not parse (a commit message, session notes, a sibling log) reads as
absent.

**Principle:** Family H (the consumer of a record is its parser; provenance
is written to be read by the check that enforces it).

**Why:** witnessed 2026-10-14 (playbook repo): a landing pruned a prompt-log
entry with the receipt only in the commit message; the prune hunk was also
lost in a rebase, and the re-apply still flagged REMOVED-WITHOUT-WITNESS
because the in-log receipt line was missing - the audit's own docstring
documents the in-log grammar, and the repair added the line as log content
(57eeb4326). Siblings: #11, #21.

## 45. A Boundary's Live Root Is Its Checkout Match, Not Its Holder Process

**Principle:** Family H (verify the real thing, not the abstraction: "live root"
classifies where the record's repo_root resolves, not whether the process that
wrote the record still exists).

**Trigger:** adjudicating an interrupted closeout boundary whose recorded
holder pid is dead, choosing among the recovery subcommands the refusal names.

**Rule:** select the interrupted-run remedy from the record's root state, never
from holder liveness: a manifest whose recorded repo_root matches the current
repository is a live root even when its holder pid is gone, and the remedies
are recover-manifest (verify the landed work against git, then close),
write-manifest --adopt, or finalize-manifest; disposition-manifest is only for
a record whose root no longer resolves. Before recovering, prove the run's work
landed: its landing commit reachable from the base branch carrying the owned
paths is the witness.

**Why:** witnessed 2026-10-14: a peer session's run manifest sat unfinalized
with a dead holder pid while its work was already landed by its own landing
commit on main; disposition-manifest refused because the recorded repo_root
matched the repository (a live root), and recover-manifest verified the landed
commit and closed the boundary in one step.

**See also:** Lesson 11 (resolve a disposition from every shape its machinery
writes); Lesson 44 (a machine receipt lives where its auditor parses).

## 46. A Guard's Evidence Home Resolves Under the Root the Guard Is Invoked With

**Principle:** Family H (verify the real thing, not the abstraction: an
evidence-lookup gate reads the homes its own invocation root resolves, not the
primary checkout's homes).

**Trigger:** satisfying a named-evidence refusal (an exec-review record for an
archived plan) during a landing that runs from an ad-hoc worktree.

**Rule:** when a gate resolves evidence paths under its `--repo`-style root, an
evidence record written only into the primary checkout's home does not satisfy
the gate invoked from a run worktree: copy the record (and its sidecar) into
the worktree's own home before retrying, and keep the primary-home copy for
the durable corpus. Diagnose the mismatch by reading the guard's lookup
function, not by re-adding the record to the same home that already failed.

**Why:** witnessed 2026-10-13/14 (playbook repo): the plans-egress refusal
"missing evidence leg: exec-review record" persisted after the record was
written into the primary reviews home, because `find_evidence_record` reads
the reviews home under the root the guard was invoked with (the run
worktree); copying both files into the worktree's `.ai-playbook/reviews/`
cleared the refusal on the first retry.

**See also:** Lesson 44 (a machine receipt lives where its auditor parses);
Lesson 45 (a boundary's live root is its checkout match).

## 47. A Structured-Line Transform Replaces Tokens, Never Whole Lines

**Principle:** Family E (make the mechanical check run: a targeted text
transform on structured lines preserves every field of the line it edits).

**Trigger:** flipping task checkboxes (or any status marker) in a structured
record such as a plan file before an archive gate.

**Rule:** flipping a structured line's marker is a substring replace of the
marker token (`- [ ]` to `- [x]`), never a replacement of the whole line with
a bare marker: line-level replacement silently destroys the line's text, and
a checkbox-counting gate passes on the wreckage because the count is
unchanged. Verify the transform with a diff that shows only the marker token
changing per line.

**Why:** witnessed 2026-10-14 (playbook repo): a scripted tick replaced whole
checkbox lines with bare `- [x]`, destroying 8 of 9 checkbox texts in a plan
record; the egress gate passed on box count alone and the destruction was
caught only by the Phase 3 review round, costing a fold round to restore the
texts from the certified bytes.

**See also:** Lesson 42 (a scratch worktree checks out a commit, not your
working tree); Lesson 38 (a gate's refusal cannot ride a pipeline tail).

## 48. A Claim Line in a Frozen Artifact Is Provenance, Never Cleanup Debt

**Principle:** Family D (single source of truth: a claim's live state has one
mutable home, the registry file; copies of the claim inside artifacts that
left digest-integrity review are provenance snapshots, not state).

**Trigger:** teardown of a run whose reviewed artifact carries a header line
pointing at the run's registry entry (claim, lease, lock) that teardown
deletes.

**Rule:** teardown cleans the registry surface it owns, never the reviewed
artifact: a line citing a registry entry inside an artifact that exited
digest-integrity review is permanent provenance, and removing it after the
terminal review round is an out-of-process delta the integrity rule reverts.
Delete the registry file; leave the line.

**Why:** witnessed 2026-10-14 (playbook repo): an authoring teardown removed
the plan header's authoring-claim line after the final review round; the
post-round digest-integrity rule classified the removal as an unclassified
delta and the removal was reverted, and the landed plan keeps the line by
convention (archived plans carry it as provenance) while no skill text
documents the line's persistence.

## 49. Draft Inside the Byte Cap When the Gate Measures Bytes

**Principle:** Family D (single source of truth: the cap's authoritative
measure belongs at composition time, the same place the text is written, not
at a downstream gate).

**Trigger:** authoring structured items (checklist entries, table rows,
record fields) whose acceptance gate enforces a per-item byte budget.

**Rule:** when a downstream gate enforces a per-item byte budget, measure the
budget while drafting each item (a one-line shell probe over the drafted
item), not at gate time: a gate-time miss forces splitting complete,
already-reviewed items, and every split risks dropping acceptance coverage
that the original item carried.

**Why:** witnessed 2026-10-13/14 (playbook repo): two authoring cycles needed
seven gate-time checklist-item splits in total across the plan readiness
gate's per-item cap; each split was a rework pass over items that were
complete at first draft. Recurred 2026-10-17: a third cycle spent five more
gate-time splits across three commits with this rule already in the corpus;
the durable fix is an authoring-side operative duty, not another corpus note.

## 50. Compose the Landing Subject From the Verifier Recognized Grammar

**Principle:** Family D (recover and land through the owning machinery against current state; a landing the verifier cannot classify loses its mechanical verification even when the bytes are perfect).

**Trigger:** composing a squash-landing commit message when a post-landing guard classifies landings by subject prefix.

**Rule:** derive the landing subject prefix from the verification machinery recognized landing-claim grammar (read the guard constant) before landing, not from the lane vocabulary. An unrecognized prefix forces hand-run verification (rev-list) and loses the guard coverage for every later walk that anchors on subject classes.

**Example:** an authoring landing used `author: land ...`; the single-commit sweep refused the anchor (not a landing-claiming commit) and the run fell back to a manual rev-list count. A same-day landing using the guard own `plans: land ` prefix classified cleanly.

## 51. Anchor a Scoped Range Edit on a Boundary Proven Unique

**Principle:** Family E (make the mechanical check run: a scripted range
transform is only as safe as its anchor; verify the anchor's uniqueness and
the transform's size signature before committing).

**Trigger:** a script that splices or rewrites a byte range of a structured
document by locating two anchor strings (for example, marking task checkboxes
in a section located via a heading string).

**Rule:** before a scripted range edit, prove each anchor matches exactly one
location (count occurrences first) and prefer task-item boundaries over
section headings, which recur across front matter and body. Then check the
transform's size signature before committing: a splice whose output is much
larger than its input (or whose commit stat reads as pure insertion on an
existing file) is duplication corruption, not an edit; rebuild from the last
good bytes and re-apply with bounded per-task ranges.

**Why:** witnessed 2026-10-15 (playbook repo): a checkbox-mark script took
`index` of `## Evaluation Criteria`, which occurs twice in the plan (criteria
section and a later occurrence), so the computed range was empty and the
script duplicated the file's tail (140 to 210 lines); the corruption was
committed and caught only by the implausible commit stat, then repaired by
rebuilding from the pre-edit commit and flipping boxes in per-task ranges.
Sibling: #47 (line-replacement destroys text; this one is its range-splice
analogue).

## 52. A File-Creation Tool Writes Where the Path Says, Not Where the Shell Stands

**Principle:** Family D (state-first: the checkout a write lands in is part
of the write's state; a file-creation tool resolves absolute paths, so a
habitual repo-root path bypasses worktree placement that shell discipline
would have caught).

**Trigger:** creating a new run artifact (backlog row, note, record) with a
file-creation/edit tool while the run executes in an ad-hoc worktree.

**Rule:** when a run executes in a worktree, compose every new-file path
under the worktree root explicitly, even for paths that "obviously" belong to
the repo layout: a Write/Edit call given the primary checkout's absolute path
creates the file there directly, outside the worktree's branch, and a later
stage-by-path fails with a pathspec miss. Detect the slip as an untracked
file appearing in the primary checkout's status; repair by moving the file
into the worktree, not by staging from the primary.

**Why:** witnessed 2026-10-15 (playbook repo): an execution run in a worktree
created a new backlog row via its habitual primary-checkout absolute path;
`git add` in the worktree failed with `pathspec did not match`, and the file
had to be moved into the worktree before staging. Sibling: #43 (the shell
cwd reset; this is its file-tool analogue).

## 53. Discover Integration Capabilities Before Declaring an Operation Missing

**Principle:** Family H (verify the real thing, not the abstraction: an initial
tool list is only one view of a connected integration's supported operations).

**Shape trigger:** A connected integration appears to lack a required action
because no standalone operation is visible in its initial inventory.

**General form:** Before declaring an operation unavailable, inspect the
integration's supported capability-discovery surface and identify any mediated
flow it exposes. Probe that supported path end to end with its returned inputs
and identifiers. Do not substitute an unapproved credentialed request or
conclude that the capability is absent from one incomplete list.

**Why this matters:** A publishing workflow was about to stop because its
initial action list showed no attachment upload. Capability discovery exposed
an integration-managed upload path, which returned the identifiers needed to
embed and verify the image.

**See also:** User-level lesson UL#315 (probe interface surfaces before
declaring a capability inaccessible); `agents/skills/confluence-page-sync/SKILL.md`.

## 54. land and land-worktree Carry Opposite --expected-tip Contracts

**Principle:** Family D (single source of truth: read the helper's own usage
per subcommand; never generalize one subcommand's flag contract to its
siblings).

**Trigger:** a `scripts/land_squash.sh` landing is refused on the expected
tip, or a corpus lesson about the landing helper's flags is about to be
applied to the other subcommand than the one it was witnessed on.

**Rule:** derive `--expected-tip` per subcommand from the helper usage at
call time: `land` verifies the BASE branch tip (main must still be there);
`land-worktree` verifies the SOURCE branch tip (the worktree branch being
landed). The same flag name carries opposite contracts; re-derive the value
with `git rev-parse` in the landing shell and never reuse the other
subcommand's value.

**Why:** witnessed 2026-10-15: a `land-worktree` landing passed main's tip
under the blanket base-tip rule, was refused, and landed on the retry with
the source branch tip; the helper usage names both contracts explicitly.

**See also:** #34 (the `land` side of the same flag).

## 55. Compose the Plan-Archive Rider Before the Landing Critical Section

**Principle:** Family B (ordering: a gate that classifies by diff shape only
sees what the landing range carries; a missing rider is not an error, it is a
silently absent side effect).

**Trigger:** a plan-execution landing is about to run, and the plan file is
still at the plans root with no archive rider commit composed on the run
branch.

**Rule:** the archive egress gate fires only when the landing range itself
moves a plan out of a plans root; a landing built without the archive rider
passes every gate and lands the ticked plan unarchived at the plans root.
Compose the archive move (and the completion-pass disposition section) as a
rider commit BEFORE the landing critical section. Recovery after such a
landing is a second mini-landing: fresh branch off the moved base tip,
cherry-pick only the archive rider commit, probe, lock, land; do not rebase
the original run branch, whose content commits already live in the base tip
through the squash and conflict against themselves.

**Why:** witnessed 2026-10-15 on two same-day execution landings: the first
run composed the rider pre-landing and the egress gate verified its review
evidence; the second run landed without the rider, the gate stayed silent
(no egress in range), and the repair needed the recomposed-branch
mini-landing above plus an orphan staged-copy cleanup in the primary
checkout (staged ancestor-blob bytes of the plans-root path the rename
deleted).

**See also:** #54 (the landing helper's flag contracts), #51 (scoped range
edit anchoring).


## 56. Assert a Span Edit's Internal Inventory, Not Only Its Anchors

**Principle:** Family E (make the mechanical check run: a scripted range
transform is only as safe as its knowledge of what lies between the
anchors; enumerate and assert that interior, not just the boundary
matches).

**Trigger:** a script that deletes or replaces a byte range of a fenced
index document between two heading anchors (for example, pruning one
entry from an instruction-queue file by slicing from its heading to the
next entry's heading).

**Rule:** before replacing the span, derive the expected interior from
the live bytes (list the headings or entries the region should contain)
and assert the extracted span matches that expectation exactly. Unique
anchors (#51) do not bound the interior: an unexpected sibling between
two proven boundaries dies with the span, and on a large file the
few-hundred-byte overshoot hides from any size-signature check.

**Why:** witnessed 2026-10-16 (playbook repo): a prune rider anchored on
the target entry's heading and the next heading, but an intervening
entry sat between them and was deleted with the span; the landing
sweep's prune audit caught the unwitnessed removal and refused the
landing.

**See also:** #51 (anchor uniqueness plus the size signature), #57 (the
audit that caught it and its history-level remedy).


## 57. A Per-Commit Gate Reads History, Not the Tip

**Principle:** Family B (ordering: a gate that classifies each commit's
diff in the unlanded range keeps judging that history no matter what
the tip's bytes say afterwards).

**Trigger:** a pre-landing audit refuses a range-carried change (an
unwitnessed index-entry removal, an egress move), and the tempting fix
is to restore the expected bytes at the tip.

**Rule:** byte-level repair cannot clear a per-commit gate: the
offending commit still rides the branch and every re-run re-reads it.
While the branch is unlanded, rewrite the history instead - `git reset
--soft` onto the base, then re-commit the work in clean layers so every
removal carries its own witness. Once landed, the gate's record is
history and the remedy is an additive follow-up, never an amend.

**Why:** witnessed 2026-10-16 (playbook repo): after an over-pruned
entry was restored byte-identically from the base, the prune audit
still refused with the same unwitnessed-removal finding because the
rider commit still carried the deletion; the same audit passed after
the soft-reset re-commit showed exactly one witnessed removal.

**See also:** #55 (same gate family: the landing range decides), #56
(the interior-inventory assertion that prevents the over-prune).


## 58. Reproduce the Live Failure Shape Before Re-Keying a Spec

**Principle:** Family H (verify the real thing, not the abstraction: a
revised threat model is only as good as the reproduced mechanism it is
keyed to).

**Trigger:** review refuses a plan's topology (its Why, fixtures, or
validation criteria keyed to a failure shape), and the fold must
re-key the spec onto a corrected one.

**Rule:** do not re-key from the finding's wording alone. Reproduce the
live failure end-to-end with probes, name the exact stage or gate that
actually fires, and re-anchor the Why, the fixtures, and the evaluation
criteria onto that observed mechanism. A fixture that dies at a
different gate than the spec cites refutes the topology, not the
reviewer; shipping it fences the wrong component.

**Why:** witnessed 2026-10-16 (playbook repo): a closeout-guard plan's
refusal fixture failed two stages before its cited guard, and its Why
assumed a retired closeout shape; live probes showed the only reachable
swallow path resolved a foreign staged set at a later stage, and the v3
re-key moved the fixture and the cited line onto that observed path
before certification passed. Recurred 2026-10-17: a review fold prescribed
a permutation fixture that was never run against the live gate; the
classifier's diff alignment turned the prescribed two-line shape into a
mixed-restoration hunk no correct implementation could fail, and the re-key
held only after the replacement fixture was measured against the live
classifier.

**See also:** #36 (measure the full gate's private dimensions before
round one).


## 59. When a Tool Call Loops, Switch Channels Instead of Retrying

A tool-emission loop is selection failure, not tool failure: the same
read-only call materializes twice in a row while a decided mutating
call stays unsent. Stop emitting that tool family immediately. Record
the decided action through a channel that still works (a file write, a
state edit), let that durable artifact carry the decision to its
executor, and close the looped surface for the rest of the session. A
refusal on the first real attempt breaks the loop, where a retried
listing cannot: listings are free and self-reinforcing, while a
mutating call always returns new information.

**Principle:** Family D (state-first: when one output channel degrades,
the durable record is the decision, and the degraded surface is stood
down, not retried).

**Why:** witnessed 2026-10-16 (playbook repo): a scheduler session
decided one automation create and then emitted seven consecutive
listing calls instead of it; the recorded remedy, standing down through
a state write and installing the fallback carrier with shell commands,
cost one carrier and zero further loops, and the session's other tools
(shell, file writes, state edits) never misfired during the episode.
Recurred 2026-10-17 at about fifteen collapses: switching tool families and
mixed parallel blocks did not break the loop, and delegation could not carry
the decided call because the delegate lacked the looped tool family; the
durable state write plus a shell-installed fallback carrier still landed it.

**See also:** #43 (the checkout a command runs in is state; this is
its emission-surface analogue).

## 60. A Dispatch Text's Coverage Claim Is Not Evidence About the Disk

A rolling-log entry's own prompt encodes facts as of its writing
(a row "is covered" by a plan, a defect "is live"); those claims age
against the moving tip like any other quoted value. Before executing an
entry's destructive or fixing instruction, re-derive the claim's
predicate against current disk bytes with a probe (read the named code
paths, run the classifier or gate on a rebuilt witness shape), and let
the probe's outcome pick the branch - execute, stand down, or record
already-fixed - never the prompt's assertion.

**Principle:** Family D (state-first: the artifact on disk is the
source of record; a written instruction's description of that artifact
is a stale read).

**Why:** witnessed twice 2026-10-16 (playbook repo, one resume run):
the valid-document-removal entry ordered row deletion on a coverage
claim the disk refuted (the origin's removal shape was within-file,
still refusing; the run stood down at its own stop condition), and the
gate-removal glob entry ordered a regex repair that had already landed
upstream (probes showed both citation forms matching; the real residue
was only the parked teardown, which then completed).

**See also:** the repository guidelines' precision-critical rule
(a value quoted from conversation context is not evidence); this is its
dispatch-text analogue.

## 61. Acquire the Merge Lock at the Primary Checkout, Not Inside the Worktree

**Rule:** when a `land_squash.sh land-worktree` landing runs from an ad-hoc
worktree, run the merge-lock acquire with the shell cwd at the primary
checkout, then `cd` to the worktree for the landing itself and release
after, all in one shell call. The lock record binds `repo_root` to the
checkout the acquire ran in, and the landing refuses a record whose root is
the worktree (`merge lock record repo_root ... does not equal this
repository's primary checkout root`).

**Principle:** Family D (state-first: the lock record is keyed state; write
it from the checkout every consumer validates against).

**Trigger:** a merge-locked landing staged inside an ad-hoc worktree, where
the natural habit is to acquire the lock where you land.

**Why:** witnessed 2026-10-16 (playbook repo): the acquire ran inside the
authoring worktree and the landing refused on the root mismatch; the retry
acquired at the primary checkout and landed the same bytes unchanged.

**See also:** #35 (lock exports die at the tool-call boundary; the hold
record is the recovery source); #43 (a per-call shell resets cwd to the
primary checkout); #54 (land and land-worktree carry opposite
--expected-tip contracts).

## 62. Re-Derive a Script's Flag Grammar at Invocation, Not from Memory

**Rule:** before a precision-critical helper invocation, read the script's
usage text and take every flag and positional from it; a remembered grammar
(`--head <rev>`) the script never had is refused loudly (`unrecognized
arguments`), and a commit-ish passed in a path position is refused as a
missing file (`prompt log not found`). Capture the script's own exit code
directly; `$?` after a pipeline is the last command's.

**Principle:** Family H (verify the real thing, not the abstraction: the
usage text is the contract; memory of a sibling tool's grammar is not).

**Trigger:** invoking a repo maintenance script (for example
`check_prompt_log_origins.py --prune-audit`) whose siblings share flag
vocabulary.

**Why:** witnessed 2026-10-16 (playbook repo): a prune-audit run passed the
landing commit as `--head` and then as the positional, refused both times,
and the first retry read `$?` after a `tail` pipe and took the wrong exit
code; the `--base <merge-base> <log-path>` form from the usage text passed
on the first correct invocation.

**See also:** #15 (re-derive a memorized procedure's owning file at
execution time); #60 (a dispatch text's coverage claim is not evidence
about the disk).

## 63. Key Ledger-Edit Predicates on Stable Identifiers, Not Human Phrasing

**Rule:** when a script asserts on or edits an append-only ledger whose
records share phrasing across days (for example the scheduler state file's
per-fire children entries), key the match predicate on the record's stable
identity fields (target slug plus session or automation id), never on a
human-phrased date or title prefix; scheduled fires reuse the same phrases,
and a loose prefix matches a different day's record.

**Principle:** Family D (state-first: match the record by its identity
fields; prose inside the record is description, not a key).

**Trigger:** editing or asserting on a state file or ledger that several
scheduled fires append to with near-identical wording.

**Why:** witnessed 2026-10-16 (playbook repo): a state-file edit keyed on
the loose prefix naming "cycle 2" matched the previous night's fire entry
with the same phrase; the assertion failed loudly, and re-keying the
predicate on the entry slug plus session id edited only the intended record.

**See also:** #15 (re-derive a memorized procedure's owning file at
execution time); #60 (a dispatch text's coverage claim is not evidence
about the disk).

## 64. Never Probe Pin Mutations with sed -i.bak

**Rule:** a pin mutation probe (mutate a pinned substring, assert the test
suite fails, restore) must not run through `sed -i.bak` in a repeated
loop: each pass replaces the pinned substring with the marker AND
overwrites the same `.bak` file, so after two probes the backup is
mutated bytes too and the "pristine" restore target is corrupt. Do the
mutate-assert-restore cycle in one Python script with a `finally` block
that rewrites the original content it read at start, or restore with
`git checkout -- <path>` from a verified-clean HEAD before each probe.

**Principle:** Family D (state-first: capture the pristine bytes once at
run start and restore from that capture, never from a derived backup
that earlier iterations have already touched).

**Trigger:** any change that runs more than one in-place mutation probe
against the same file in one validation battery.

**Why:** witnessed 2026-10-16 (playbook repo): two successive
`sed -i.bak` probes against `agents/skills/execute-plan/SKILL.md` left
both the file and its `.bak` carrying "MUTATED" where pinned text
belonged; the follow-up "pin not found" assertion fired on already
mutated bytes and looked like a pin bug rather than probe corruption.
Restored from `git checkout --` (HEAD held the landed state) and re-ran
the probes in pure Python.

**See also:** #15 (re-derive a memorized procedure's owning file at
execution time); #62 (re-derive a script's flag grammar at invocation).

## 65. Take the Review Machinery's Validator as the Contract Over the Recipe

**Rule:** the review-round machinery's durable invocation contracts live in
its validator and selector, not in a run's recipe text: (1) a series'
review-run-id is minted at r1 and immutable across its rounds, so a recipe
that says "fresh mint per round" is wrong by the validator's grammar
("run_id cannot change after r1 in the same artifact chain"); (2) the
selector allocates the next round number from staged records only, so
stage the prior round's record before requesting the next round, or the
selector re-allocates a round that already ran; (3) plan-level gates anchor
path resolution to the checkout they run from (plan_readiness anchors
plans_dir to the cwd repo), so run them from the checkout that owns the
plan. When a validator refusal contradicts recipe wording, the validator
wins: fix the artifact, never the gate.

**Principle:** Family D (state-first: a tool's enforced invariant is the
contract of record over any prose describing it).

**Trigger:** staging, validating, or gating review rounds from a resume
recipe, checkpoint note, or dispatch text.

**Why:** witnessed 2026-10-16 (playbook repo): an r2 record staged with a
fresh mint was refused for run-id continuity; a later round was allocated
past an unstaged r2 because the selector counts staged records only; and
a plan-readiness gate refused with "plan file resolves outside plans_dir"
when run from the primary checkout for a worktree-owned plan. All three
resolved by following the tool's contract over the recipe wording.

**See also:** #62 (re-derive a script's flag grammar at invocation); #60
(a dispatch text's coverage claim is not evidence about the disk).

## 66. Re-Survey the Filing Destination at Write Time While a Peer Closeout Is in Flight

A shared state note that names a filing duty ambiguously (for example
"filed, or left to the maintenance survey") authorizes a re-derivation,
not the write itself. Immediately before creating a derived record
(backlog row, residual-ledger entry, receipt), list the destination
directory again, and treat a peer session whose landing or closeout is
seconds to minutes old as a filing owner-in-waiting: its closeout may
contain the same filing, richer than the one about to be written. When
the peer's record already exists, fold instead of writing: stand down,
keep the peer's version, and witness the reconciliation. A duplicate
caught only after the write costs a removal commit on top of the filing.

**Principle:** Family D (state-first: the destination listing at write
time is the only current evidence about what a live peer has already
filed; a state note is a stale read the moment its writer moves on).

**Trigger:** filing a derived record whose duty was learned from a
shared state file or session note, while the peer that produced the
underlying work is still live or has landed within the hour.

**Why:** witnessed 2026-10-16 (playbook repo): a shepherd session
derived a residual-ledger row duty from a state entry that left the
filing ambiguous, wrote its own row while the delegated session was
still closing out, and the delegated session filed its richer row less
than two minutes after its landing; the duplicate was caught on the
next read and removed in its own corrective commit, keeping the peer's
record.

**See also:** #13 (re-derive the work item's unclaimed state before a
long run's final write: the queue-work execution shape of the same
write-time discipline); #60 (a dispatch text's coverage claim is not
evidence about the disk: the read-time half of the state-first family).
## 67. Sweep Every Text-Assertion Layer When Retiring Operative Text

**Rule:** when a change retires or rewords a named span of operative
corpus text (a policy value, a doctrine sentence, an enum literal), sweep
every layer that asserts on that text in the same change: the pin and
checker suites AND the test fixtures and golden files. Grep the whole test
surface for the removed literal, not only the owning files and the one
enforcement layer the change already names; a removal validated against
the owning files and its pins alone can strand another layer's pinning
assertion and turn a standing gate bundle red.

**Principle:** Family D (single source of truth: retired text surviving
in a fixture is a stale copy; a removal checklist is a consumer
inventory, and test fixtures asserting corpus text are consumers).

**Trigger:** a task whose acceptance is a zero-match grep over skill or
corpus files, or any retirement of a named text span from operative
files.

**Why:** witnessed 2026-10-16 (playbook repo): a policy consolidation
retired a policy value from two skill files and re-keyed the four pins
targeting the removed arm, but a standing test fixture's profile-by-policy
matrix asserted the removed authorization span verbatim; the plan-gate
bundle regressed, caught only by the task's intermediate review. The
change's consumer inventory had enumerated pins and docs but not the test
suite.

**See also:** #60 (a dispatch text's coverage claim is not evidence about
the disk); #63 (key predicates on stable identifiers, not human phrasing).

## 68. Relay the Fetched Listing Whole and Rerun a Zero-Recognition Verdict

**Rule:** when a tool's fetched output (an automation listing, a query
result, an inventory dump) is passed on as decision input to a mechanical
checker that keys recognition predicates on fields beyond the summary
lines, the input must be the faithful full record set, never a
hand-trimmed transcription. A verdict computed with recognition
zero-matches against an input the checker reports as used may have booked
wrong durable state as a side effect; re-run the check with the faithful
listing before echoing any verdict as decided, and expect the rerun to
correct the checker's own bookkeeping rather than hand-editing the state
file.

**Principle:** Family D (single source of truth: the fetched tool output
is the source of record; a hand-trimmed transcription is a divergent copy
that silently fails every predicate reading the dropped spans).

**Trigger:** relaying a tool listing to a second checker under
output-size pressure, when the relay drops fields the checker's
recognition literals live in (prompt bodies, embedded payloads), and the
checker both decides and books.

**Why:** witnessed 2026-10-17 (playbook repo): a done closeout's
rearm-on-touch check ran against a hand-trimmed scheduler listing with
prompt bodies dropped; the recognizer matched zero automations,
classified the armed recurring parent fresh-absent, and booked a
parent-absent-since fact into the scheduler state file. The rerun with
the full listing recognized the parent, flipped the verdict to parent-ok
with no re-arm owed, and cleared the wrongly-booked absence itself.

**See also:** #24 (a standing automation's prompt is its identity: the
dropped spans were exactly the identity carrier); #60 (a dispatch text's
coverage claim is not evidence about the disk: the same read-fidelity
family on the human side).


## 69. Derive a Downstream Match Pattern from the On-Disk Names, Not from a Citation's Prose

**Rule:** when a mechanical check derives the record names it expects to
exist from a durable document's citation line (a plan's review-series
citation, a changelog reference), re-derive the actual record names from
the directory at check time and reconcile the citation to disk before
enforcing the match; prose citations lag on-disk naming (an infix present
on the records but absent from the citation line), and a glob built from
the citation false-refuses on records that exist.

**Principle:** Family D (disk-first: the on-disk names are the source of
record; a citation's prose is a lossy copy of them).

**Trigger:** writing or enforcing a gate whose expected-file set comes
from a document's citation of record names rather than from a directory
listing.

**Why:** witnessed twice (playbook repo, 2026-10-16 and 2026-10-17): two
archived plans' review-series citations lacked the `-p<hash>` infix the
on-disk series records carried; the archive gate-removal glob built from
the citations reported the series missing and refused the landing, and
the bounded remedy each time was a citation-only commit, a re-land, and a
re-run of the gate.

**See also:** #62 (re-derive a script's contract at invocation, not from
memory); #63 (key predicates on stable identifiers, not human phrasing).


## 70. Hold a Count-Exact Text Pin's Anchored Phrase to One Line

**Rule:** a text pin that counts exact occurrences of a phrase (a
fixed-string grep piped to a hit counter) breaks silently when the source
reflows the phrase across a line wrap; when a pin requires a sentence or
clause to survive, hold the phrase to one line in the source (or make the
pin line-join-insensitive), and treat a pin that drops from one hit to
zero after an unrelated wording edit as a wrap, not as a removal.

**Principle:** Family E (make the mechanical check run: a check that
cannot see a legal formatting state is a false-alarm generator).

**Trigger:** writing or repairing an occurrence-exact pin whose anchored
phrase can be re-wrapped by documentation formatting.

**Why:** witnessed 2026-10-17 (playbook repo): a docstring sentence was
reflowed during an edit and its pinned phrase wrapped across two lines;
the count-exact pin found zero hits and failed the validation battery
although the sentence itself survived intact, and reflowing to keep the
phrase on one line restored the expected single hit.

**See also:** #67 (sweep every text-assertion layer when retiring
operative text); #64 (never probe pin mutations with an in-place sed).

## 71. Identify the Pinned Gate Invocation Before Repairing a Validator Refusal

**Rule:** when a hard gate refuses and repair looks necessary, first confirm
the exact invocation the owning workflow pins as the gate. A validator that
exposes several modes (a strict full consult, a structural pre-round probe)
can refuse in the stricter mode while the pinned gate invocation passes; the
stricter consult's refusal is not the gate's refusal, and repairing the
artifact the stricter mode trips over (record surgery, metadata backfill) is
unrequested work on a surface the gate never consults.

**Principle:** Family D (state-first: the gate's own invocation form is part
of the gate's state; run the pinned form, never a re-derived variant).

**Trigger:** a readiness, validation, or boundary gate refuses and the next
instinct is to edit records, sidecars, or metadata to unblock it.

**Why:** witnessed 2026-10-17 (playbook repo): a dispatch run executed the
readiness validator's strict consult, hit an ambiguous-series refusal rooted
in a legacy review record, briefly added an identity line to the record, and
only then found the pinned Step 0.5 invocation (`--pre-round`) passes because
it never consults review records; the record edit was reverted. The refusal
class itself is real and was routed to the authoring lane (origin row
`docs/history/backlog/2026-10-17-review-record-legacy-identity-blocks-readiness.md`).

**See also:** #36 (measure the full gate's private dimensions before round
one - the authoring-side inverse: pre-round passing while the full gate
refuses).

## 72. An Authoring Landing's Commit Message Can Read Like an Execution Landing

**Rule:** a landing commit whose subject says it "lands" a plan may be the
authoring landing (plan file, origin-row dispositions, prompt-log prune) with
none of the plan's operative files; before inferring executed status from the
subject, check the commit's diffstat for the plan's operative paths. Memory
notes saying "certified-unexecuted" stay true across such a landing.

**Principle:** Family E (make the mechanical check run: re-derive status from
the diff, never from a summary phrase).

**Trigger:** deciding whether a certified plan still needs an execution
dispatch, from history or memory alone.

**Why:** witnessed 2026-10-17 (playbook repo): a commit subject read
"skills: land <plan> (r3-certified ...)" while the diff added the plan file
and six origin-row updates and zero files under the skills tree; the plan's
operative edits were absent from the default branch, and the survey first
misread the plan as already executed before the diffstat corrected it.

**See also:** #43 (a per-call shell resets cwd to the primary checkout, with
the persisted-cwd runtime variant - re-derive from git before judging
drift).


## 73. Re-Apply Post-Squash Follow-Up Deltas From the Default Tip

**Rule:** once a squash landing has consumed a run branch, that branch is
dead for follow-up work: its commits already live in the default branch as
one squash commit, so rebasing the branch onto the moved tip replays each
original commit onto content that already contains it and self-conflicts.
For a follow-up delta (a citation fix, a wording correction), start from the
default branch state: reset the touched file to HEAD (`git restore
--source=HEAD --staged --worktree <path>`; a bare `git restore <path>` reads
the index and can silently restore a stale staged version), apply only the
delta, commit fresh, and land the result as its own small corrective commit
through the same landing machinery.

**Why:** witnessed 2026-10-17 (playbook repo): a citation-only follow-up to
a freshly squash-landed plan was attempted as a rebase of the landed
authoring branch and conflicted against the squash's own plan file on the
default tip; the working route was abort, hard-reset to the default tip,
re-apply the one-line citation delta from the HEAD version, and land the
one-line corrective. During that repair a bare `git restore` silently
restored the stale staged pre-landing version because the index still held
it.

**See also:** #6 (integrate the current default tip before building a
squash), #10 (prove the landing base and the completion marks).


## 74. Explicit-Root Every Validator Invocation That Audits Another Tree

**Rule:** a tool that resolves its anchor (the repository root, a log path,
a reviews home) from its own location or from the invoking shell's cwd can
audit a different tree than the one under review and report a vacuous
success, a zero-count pass, or a refusal about the wrong precondition. When
the state under audit lives in an ad-hoc worktree and the shell cwd resets
to the primary checkout between calls, pass explicit worktree-rooted paths
for every path argument, and treat a zero-count success (zero removals,
zero matches, an empty listing) as unverified until the tree the tool
consulted is confirmed.

**Why:** witnessed 2026-10-17 (playbook repo): a prune audit invoked with a
relative log path reported zero removals across zero log-touching commits
against the primary checkout's prompt log while the audited prune receipts
lived in the worktree's copy; re-running with the explicit worktree log
path printed the clean verdict. In the same run, the review-record selector
refused with a wrong-precondition message (a missing reviews home read as
"not inside a git repository") because the script derives its repository
root from that directory. Third witness, same day: a worktree-closeout gate
invocation mixed path bases within one command - the worktree and target
arguments rooted absolute, the plan argument repo-relative - and ran from
the primary checkout, so the one relative argument resolved against the
wrong tree and refused with a plan-file-not-found error; re-running from
the worktree root, whose copy the relative name addressed, passed.

**See also:** #43 (a per-call shell resets cwd to the primary checkout),
#68 (relay the fetched listing whole and rerun a zero-recognition verdict),
#71 (identify the pinned gate invocation before repairing a refusal - the
mode-variant sibling of this root-variant).


## 75. A Review Certification Covers the Panel's Checks, Not the Authoring Gates

**Rule:** a review record's ready verdict is evidence about the panel's own
findings only; it never re-runs the authoring-side mechanical gates (the
pre-round readiness probe among them). When an execution-start structural
gate refuses a freshly certified plan, treat the refusal as a plan defect
whose authoring-time gate run was skipped: re-derive the gate's current
grammar from disk, apply the minimal semantics-preserving plan-maintenance
remedy (canonical-form rewrite, its own commit), re-run the gate, and
continue. Never edit the gate mid-lane and never read the certification as
an override; the review side's scope audit is a subset of the pre-round
probe, so a skipped authoring run leaves exactly this gap.

**Principle:** Family D (the gate on disk is the contract of record; a
certification's prose is a snapshot of one panel's coverage).

**Trigger:** an executor's structural gate refuses a plan whose review
series ends in a ready verdict.

**Why:** witnessed 2026-10-17 (playbook repo): a r4-certified plan failed
`plan_readiness.py --pre-round` at execution start on prose-form class
anchors, a form the anchors-grammar probe refuses; no review round had run
the pre-round probe and the authoring session had skipped the plans-skill
mandate to run it before round 1; the canonical-anchor rewrite passed the
gate unchanged in semantics.

**See also:** #65 (take the validator as the contract over the recipe),
#60 (a dispatch text's coverage claim is not evidence about the disk).


## 76. Prove Past-a-Checkpoint Suite Sections in a Sandbox with a Negative Control

**Rule:** a validation suite that hard-exits at an early failing checkpoint
never executes sections ordered after the blocker, so a newly added section
cannot prove green in-place while a known pre-existing failure stands. Prove
the new section in a throwaway clone of the tree with only the blocker
neutralized, run the suite there for the green outcome, and run a negative
control in the same sandbox (delete the pinned spans, expect exactly the new
pins' failure lines). Record that the in-repo green becomes observable only
after the blocker's sanctioned resolution, and never neutralize the blocker
in the real tree to get the pass.

**Principle:** Family E (make the mechanical check run: a checkpointed suite
is ordered evidence, and proof for a later section needs an isolated run,
not an edit to the failing earlier section).

**Trigger:** a suite exits at checkpoint N and your additions live after N.

**Why:** witnessed 2026-10-17 (playbook repo): a pins-suite addition sat
after a hard-exit checkpoint whose failure was a stale prompt-log entry due
to be pruned at landing; the pins passed via a /tmp sandbox clone with the
stale checker no-op'd, and the negative control failed with exactly the
three new pin names, proving both directions without touching the blocker.

**See also:** #70 (hold a count-exact pin's anchored phrase to one line),
#64 (never probe pin mutations in place).

## 77. A Claim File Is Not Evidence of a Live Session

**Rule:** a freshness-dated claim, lock, or manifest written by one session
is a statement about when that session last wrote, not about whether it is
still running. Before any decision that treats it as a live peer (a
stand-down, a queue skip, a dispatch refusal), corroborate liveness with the
record's own named resources: does the recorded worktree or branch still
resolve, has any progress artifact (a checkpoint commit, a record
heartbeat) moved since the claim, and - for execution claims - has the
claimed plan already landed? A claim whose plan is landed and whose worktree
is gone is stranded residue, whatever its timestamp says.

**Why:** witnessed 2026-10-17 (playbook repo): an exec survey stood down
twice on execution claims whose owning sessions had finished - one plan had
already landed and its worktree torn down, and three more orphaned claims
pointed at plans landed days earlier; the runs (manual ad-hoc sessions) had
taken claims through the gateway but never loaded the execute-plan closeout
that releases them. The stranded files read as live peers under the
freshness rule and starved the queue against nobody.

**See also:** #71 (identify the pinned gate invocation before repairing a
refusal - the release contract existed; the manual runs never ran it),
#43 (re-derive checkout state at every call).

## 78. Prove Branch Landedness From Witnesses, Not From Diff Metrics

**Rule:** under squash landings, `git cherry` and any branch-vs-main diff
statistic are the wrong instruments: patch-ids never match a squash, and
`git diff main <branch>` mostly measures how far main has moved past the
branch. To decide whether a branch's work already landed, use witnesses: the
branch's unique commit subjects (`git log main..<branch>`) matched against
landing commits on main ("check: land <plan>", "plans: land <plan>",
subject-identical squash twins), the plan file's presence under the plans
root's `completed/` archive, and the memory or receipt lines naming the
landing digest. Delete a branch only when a witness names its content or a
recorded disposition covers it; a unique commit with no witness is unlanded
work, whatever the diff says.

**Why:** witnessed 2026-10-17 (playbook repo): a residue sweep first ran
`git cherry main <branch>` over fourteen branches and counted 1-19
"unlanded" changesets everywhere, then a `diff --shortstat` that showed
tens of thousands of phantom insertions; both metrics inverted (landed
branches read unlanded). The witness route - unique-commit subjects against
main's landing commits plus the `completed/` archive - classified every
branch correctly, and one branch the metrics flagged as residue turned out
to hold a parked certified landing whose tip is its only copy.

**See also:** #73 (re-apply post-squash follow-up deltas from the default
tip), #72 (a landing's commit message can read like an execution landing).

## 79. Reconcile Tracked-File Deltas Before Worktree Removal

**Rule:** a run's teardown step that removes its worktree runs into
`git worktree remove`'s clean-tree gate over TRACKED files: ceremony steps
that append to tracked files (a finalize writing telemetry rows into a
tracked ledger) leave the worktree dirty and the removal refuses. Land the
tracked delta as an additive primary-checkout commit first, after verifying
the diff is exactly the ceremony's appended lines; gitignored residue never
blocks the gate, so after tracked reconciliation a forced removal is safe
for gitignored artifacts already migrated out.

**Principle:** Family B (ordering: a clean-tree gate sees the tree as the
run's own preceding steps left it; reconcile the run's tracked mutations
before the step that demands cleanliness).

**Trigger:** a worktree-bound run whose closeout ceremony writes into
tracked files, followed by worktree and branch teardown.

**Why:** witnessed 2026-10-16 (playbook repo): a plan run's finalize
appended three override rows to the tracked gate liveness ledger inside the
run worktree; the subsequent removal refused on the modified tracked file.
The delta was verified as exactly the appended lines, landed as an additive
primary commit, and the forced removal cleared the worktree.

**See also:** #55 (compose landing-critical artifacts before the critical
section: the same ordering family at the landing boundary); #73 (re-apply
post-squash follow-up deltas from the default tip).

## 80. A Doc-Registry Row Only Parses Inside the Main Table With Its Transition Licensed

**Rule:** an executing session adding its row to the document registry
places the row inside the main parsed table, never after a bullet list or
other non-table block: the gate parses contiguous table rows only, and a
row outside them surfaces as a row-count mismatch that does not name the
parse boundary. The row's `src` column carries the plans-root destination
path (the completed-plan path is what licenses the add/rename transition),
and the `audit` note begins `user-approved <date>:` followed by the
authorization reason.

**Principle:** Family A (validator contract: write the artifact in the
exact shape the validator parses, and derive that shape from the
validator's own parser, not from neighboring prose).

**Trigger:** a landing rider that archives a plan and adds its registry
row in the same change.

**Why:** witnessed 2026-10-17 (playbook repo): two executing-session rows
were first placed after a bullet list (unparsed; the gate reported a
row-count delta on both sides without locating the stray row), then
rejected for a `src` value that named the plan's origin instead of its
destination. The passing shape was re-derived from the gate's checks, not
from documentation.

**See also:** #78 (prove landedness from witnesses: the same re-derive
from the mechanism, not the summary, discipline).

## 81. Run the Done Boundary Setup Before Any Production Edit

**Rule:** a worktree run that will commit through the done boundary runs
the boundary setup (marker, manifest, owned-set registration) as its first
worktree action, before editing any file the run will own. Edits made
before setup are read as start-dirt by the foreign-staging gate and the
commit refuses; recovery costs a stash, a lock release, a stale
run-start marker and manifest cleanup, and a fresh setup.

**Principle:** Family B (ordering: a gate that classifies the tree at
setup time must observe the tree before the run mutates it).

**Trigger:** entering a worktree for a run whose commits go through the
done boundary.

**Why:** witnessed twice (2026-10-16 and again 2026-10-17, playbook
repo): both times skill files were edited before setup, both times the
commit refused with the start-dirt classification, and the second
occurrence shows a conversational memory note is not load-bearing
enforcement; the ordering rule is the fix, not another note.

**See also:** #79 (reconcile tracked deltas before worktree removal: the
same family, cleanliness gates observing the tree at a boundary).

## 82. Ceremony-Cited Review Records Carry the Full Digest, Re-Derived From Disk

**Rule:** a review record cited by an archive or landing ceremony contains
the FULL sha256 of the archived artifact's bytes, and the digest is
re-derived from the file on disk immediately before the write. A truncated
digest fails the ceremony's cross-check, and a digest quoted from session
context is not evidence.

**Principle:** Family A (precision-critical values are re-derived from
disk at the point of use, never carried from conversation).

**Trigger:** writing or backfilling a record whose consumer verifies a
hash against file bytes.

**Why:** witnessed 2026-10-17 (playbook repo): an exec-review record was
first written with a 20-character digest prefix and failed the
archive-ceremony check; backfilling the full on-disk sha256 cleared it.

**See also:** #78 (prove landedness from witnesses, not diff metrics).

## 83. A Failed Chain Probe Censors the Remaining Verification Probes

**Rule:** a conjunction-chained verification sequence is one aggregate
verdict, not a checklist: when an early probe fails, the later probes never
run, so their results are unknown, not negative. On a mid-chain failure,
split the remaining probes into separate commands and run each to its own
verdict before reporting; when the failed probe keyed on an identifier
captured earlier in the session, re-derive it from disk first, because a
peer's landing can rename or re-date the artifact - a plan file lands under
its landing date, not its authoring date - so the stale name, not the
audited state, is what failed.

**Principle:** Family A (a value quoted from session context is not
evidence: every identifier a check consumes is re-derived from disk at the
point of use).

**Trigger:** a multi-probe verification chain gates a report, and an early
probe fails on a path, digest, or name the session did not re-derive.

**Why:** witnessed 2026-10-17 (playbook repo): a residue-teardown
verification chain keyed its first probe on an authoring-dated plan
filename; the landing peer had re-dated the file, the chain exited on that
probe, and the seal, record, and claim checks behind it never ran. Re-run
as separate commands against disk-derived names, they all passed.

**See also:** #74 (explicit-root every validator invocation that audits
another tree: the same incident's resolution-base half), #43 (a per-call
shell resets cwd to the primary checkout), #62 (re-derive a script's flag
grammar at invocation, not from memory).

## 84. Chain a Guard to the Action It Gates With &&

**Principle:** Family A (a chained sequence's links authorize each other
explicitly: a guard whose failure must stop the tail is joined to the tail
by `&&`, never by a newline or semicolon).

**Trigger:** one shell call runs a verification probe (an assertion, a gate,
a size check) and then the write or commit that probe protects.

**Rule:** join a guard and the action it authorizes with `&&` so the guard's
failure aborts the tail; a newline- or `;`-joined sequence runs the action
whatever the guard's verdict. Keep independent verification probes as
separate commands so each result is individually known (#83's censoring
direction); the `&&` chain is for the guard-to-action dependency.

**Why:** witnessed 2026-10-17 (playbook repo): a landing rider's prune
assertion failed on a misremembered byte cap, but the newline-joined commit
after it ran anyway, landing the covered-flip edits without the prune
receipt; the prune was redone as its own commit with the assertion passing
first.

**See also:** #83 (the inverse chaining failure: an early probe exit censors
the remaining probes), #82 (re-derive the guard's own constants from disk).
