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
tip into the run branch (merge or rebase; resolve conflicts faithfully, the clause now pinned
by the operative conflict-content discipline: each conflict block resolves by union of
intents with its post-resolution re-verification duty, lesson 93 below and the landing
critical section in agents/skills/execute-plan/SKILL.md) and build the squash
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

Amend-side sibling: **base-branch immutability** - once a commit is reachable from the base branch it is never amended; corrections land as additive follow-up commits; amend is legal only inside a session's own unlanded branch before the landing critical section (origin docs/history/backlog/2026-10-02-base-branch-commit-immutability.md; witness: the 2026-10-02 18:09 amend of a peer's landed tip, folded in four minutes after another session landed it). The same expectation covers every record citing a landed sha: a cited sha is expected to stay reachable and immutable, so an amend of the cited commit surfaces as a cross-check mismatch in each record holding the old sha; the guard (`scripts/base_branch_amend_guard.py`: `check-head` refuses an amend with HEAD on the base branch, `reflog-scan` reports foreign `commit (amend)` entries) stops the commit path or names the rewrite instead of letting it pass silently. Second witness 2026-10-22: a peer session amended the landed main tip mid-run and a concurrent lander's reflog-window audit surfaced it as a backward-move FAIL; the reconciliation (verify the peer's tree delta is its own additive change, record the finding in the landing record) needed no operator stop, and the guard's true catch stands.

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
`agents/skills/execute-plan/SKILL.md` (capture recipe; since the 2026-10-22 landing it passes no `--dirs` and resolves all four dirs from facts).

**Second witness (2026-10-21, execution closeout):** the same `--dirs` operand is also a hand-maintained twin of the script's facts-resolved family: the recipe pins three dirs while `FACTS_DIR_KEYS` resolves four (`review_certs_dir` joined on 2026-10-18), so the run's code-family seal was never baselined and had to be mirrored by hand before teardown; when the script can resolve the list from facts, pass no operand (the 2026-10-22 landing removed the operand from the recipe; the origin row is deleted per the covered-row rule). Shell corollary from the same closeout: zsh does not word-split an unquoted variable, so `--files $LIST` with a newline-joined list arrives as one path (`path must not contain a newline`); pipe through `xargs` or use `${=LIST}`.

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
skip left the same flare for a later session to adjudicate. Re-witnessed 2026-10-22
(playbook repo, exec-mode ad-hoc run): two more ref-move landings left the primary's
staged index and working tree holding the landed paths' pre-landing bytes; the run
repaired by hand (index reset, then checkout of the three landed paths) instead of
running this lesson's reconciliation helper, which itself traces to the hand-composed
landing form of lesson 99.

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
gap is owned by the done-lock-release-mode-dispatch backlog row. Re-witnessed
2026-10-19 (same repo) at acquire time: the landing was attempted under the
done lock (`wait-acquire`'s `DONE_LOCK_*` exports) and `land-worktree`
refused for `MERGE_LOCK_DIR`; the landing acquire is the merge namespace's
`merge-wait-acquire`, a separate lock from the done lock even though one
holder may hold both.

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

Re-witnessed 2026-10-18 (playbook repo): a "stop when finish authoring" instruction
again gated the closeout after certification, leaving the certified plan unlanded on
its worktree branch. This rule had been in this corpus since 2026-10-07 and was not
recalled at the stop, and the stop report's pending-closeout note still cost an
operator ask ("why is the plan not in the main checkout?") before the closeout ran.

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

Re-witnessed 2026-10-20 (playbook repo, execution-run closeout): a pre-built foreign
list excluded the run's two owned staging records by a shape suffix
(`-code-review-r[12].md$`), which also dropped every peer record of that shape and
inverted them into the owned set; setup refused with the claim-or-foreign violation
naming them and exited holding the lock. Anchor an exclusion to the artifact's full
identity (the slug-qualified path), never to a shape its peers share; the
slug-anchored list passed on the retry after a hand release.

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

Re-witnessed 2026-10-20 (playbook repo, execution run closeout): two code-review staging records drafted from memory were repaired against `validate_review_staging.py` one error class at a time (freshness Metadata lines, Record kind, usage mint pair, Panel and Counts grammar, per-finding sections with Pattern, the per-worker Low budget, lens-taxonomy coverage names, the producer-written sidecar the repair tool refuses to invent for non-zero findings) across roughly ten fix cycles; reading the validator's check families and fixture builders first would have been one draft. Re-witnessed 2026-10-22 (playbook repo, execute-plan Phase 3): the same one-error-class-at-a-time repair over an unstaged validator run (canonical headings, Metadata lines, a review-run-id rejected for non-hex shape until minted fresh, extension-nested self-heal block), resolved only after reading the validator's refusals as the schema of record.

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
the refusal text alone disambiguated the mapping and the retry passed. Re-witnessed
2026-10-22 (exec-mode ad-hoc run): the first `land` invocation passed the
source branch tip again and was refused by the same mapping; the re-derivation
and retry passed, the refusal mutating nothing.

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
consumer (`2>&1 >/dev/null | awk`). Re-witnessed
2026-10-19 (same repo): a readiness gate piped through `tail -2` inside an
`&&` chain let the commit step key off the pipe tail's exit, so the commit
landed on a FAILED gate; the next gate run caught it one step later.

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
Re-witnessed 2026-10-20 (scheduled execution run): a `land-worktree` landing
again passed the base tip; the refusal left its merge hold orphaned across the
shell boundary (recovered per #109, the retry redone in one shell with the
source tip). Re-witnessed 2026-10-21 (scheduled execution run): the probe was
first invoked with the worktree's path form and refused `source branch
unresolvable`; the helper takes the branch NAME (`adhoc/<slug>`), never the
worktree path.

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

Second witness (2026-10-21, execution run r2): the exec rounds' run-id continuity binds across the code-family chain too (an r2 minted fresh was refused); a code-family record validates only through `--source-code-repo <root> --source-code-plan <sidecar>` against a seal block whose `round_start_digest` equals sha256 of `git diff <reviewed_base>...<reviewed_head>` (`--source-plan` reads the plan family and refuses with `source_kind mismatch`); and the code-review name shape does not satisfy the plans-egress evidence leg, which greps `*-plan-review-<slug>-exec-r<N>.md` for the archived bytes' sha256, so the backfill completion record is written before `check-archive`.

Third witness (2026-10-22, execution run r2 landing): the egress record's anchored name grammar puts the `-plan-review-` segment BEFORE the slug (`<date>-plan-review-<slug>-exec-r<N>.md`, the slug occupying the whole hyphen-bounded tail); a record named `<date>-<slug>-plan-review-exec-r<N>.md` leaves an empty slug segment in the guard's anchored regex and silently fails the evidence leg even though the file carries the right digest. Derive the name from the guard's record grammar, not from the error message's shorthand.

Fourth witness (2026-10-22, execution run landing): the egress evidence record is two-sided - the archive gate demands its presence in the gitignored reviews home, while the landing's reviews-home egress fence refuses the branch that TRACKS it. A receipt staged with `git add` (needed for lesson 172's force-add in other gitignored homes) turns a green check-archive into a landing refusal; the record stays untracked (`git rm --cached`), verified by re-running both gates.

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

## 85. Release Claims Match the Direction of Change

**Principle:** Family H (verify the real effect, not an inferred label: a summary follows the source changes' direction, not the repository's reputation).

**Trigger:** writing a release summary from grouped commits, especially when controls or workflows are removed or simplified.

**Rule:** Check the overall claim and every bullet against the source diff. Describe additions, removals, and simplifications accurately; call a release "hardening" only when changes add or strengthen controls. Do not infer direction from the project's purpose or safety vocabulary.

**Why:** During a release, the initial summary called broad workflow changes "hardening" even though the published commits removed guardrails and blockers. The operator corrected the label; the source diff supported a neutral description of clearer workflows and less repeated work.

**See also:** #25 (verify the real effect, not the abstraction: the grouped source diff is evidence for a release claim).

## 86. List the Live Carriers Before Arming a Scheduled One-Shot

**Principle:** Family D (state-first: the automation listing at arming time is the only evidence about coverage already standing; the ask's own wording is a stale read the moment an earlier ask armed).

**Trigger:** any scheduling ask on a repository that already runs scheduled carriers, especially a resume ask following an operator pause, which may itself have armed one.

**Rule:** Before creating a scheduled carrier, list the existing automations. A live one-shot (enabled, unfired) already covering the ask's window and mandate is patched or reported, never stacked: aligned carriers fire together, and every copy but the claim winner becomes a redundant session racing the same lane.

**Why:** witnessed 2026-10-18 (playbook repo): three one-shot carriers covering the same wall-clock window fired together, and two sessions executed the same authoring resume in parallel. The collision resolved cleanly because the coordination surfaces held: the second reader adopted the stale claim through its own takeover rules, detected the winner's staged record diverging from its own panel returns at the staging surface, and stood down before any mutating write (#13's discipline at the staging boundary). Both sessions had still spent full review panels, and the redundant session's findings survived only in its conversation. The duplicate-parent tripwire covers the recurring loop carrier; nothing gated stacking ad-hoc one-shots.

**See also:** #13 (the run-side stand-down when a peer lands the same unit mid-run), #66 (the write-time destination re-survey while a peer closeout is in flight).

## 87. A Stand-Down Routes Its Uniquely-Held Evidence Before Ending

**Principle:** Family D (state-first: once the winning session owns the lane, its records are the only capture surface; evidence held only in the stood-down session's conversation has no disk existence after that session ends).

**Trigger:** standing down on a collision (a peer took the claim, landed the unit, or owns the staging surface) while holding review-panel returns, measurements, or witness notes the winner's records do not carry.

**Rule:** Before ending, route every uniquely-held item of evidence durably: name it in the stand-down report with its full substance (measurement, anchor, concrete fix), or file it beside the winner's record once the lane settles. A report is durable; a conversation transcript is not.

**Why:** witnessed 2026-10-18 (playbook repo): a redundant session's two-worker review panel returned three measured residuals the winning session's certified record and residuals row do not carry; they survived only because the stand-down report named each with its measurement and concrete fix, which is what let the follow-up pass route them beside the winner's row. The #86 rule prevents the collision; this one contains its cost when a collision happens anyway.

**See also:** #86 (the prevention side of the same collision), #13 (the stand-down discipline whose report carries the evidence), #66 (fold into the winner's record instead of writing a duplicate).

## 88. Re-Derive Prepared Edit Spans After a Branch Switch

**Principle:** Family A (precision-critical values are re-derived from the state that will be edited, at edit time; a span prepared from one tree's bytes is a quoted value the moment that tree changes).

**Trigger:** a multi-step turn that switches branches or checkouts between reading a file's structure and editing it: a line-range edit prepared on one branch's bytes, executed after a later switch lands different bytes.

**Rule:** Line numbers and spans prepared for a targeted edit are valid only for the bytes they were read from. After any branch switch, checkout, or landing reconcile changes the working tree, re-derive the span from the current tree before the cut. The same re-derivation covers audit-gated lines written in the same pass: a receipt whose target token is prose fails the audit: the token must resolve to a commit digest or a path present in the edited tree.

**Why:** witnessed 2026-10-18 (playbook repo): a rolling-log entry prune prepared by line numbers on an authoring branch (whose bytes carried a branch-only freeze line) was executed after switching to a fresh branch off the base; the shifted lines deleted the neighboring entry's heading, and the prune audit flagged the removal without witness. The redo cost an extra commit cycle; the audit caught it, not the editor.

**See also:** #82 (ceremony-cited values re-derived from disk), #7 (re-derive an edit inventory from live bytes at execution start).

## 89. Re-Run the Origin's Own Probe Before Authoring Its Fix

**Principle:** Family H (verify the real thing, not the record of it: an evidence section records when its witness was taken, not whether the defect still holds).

**Trigger:** authoring a plan, or scoping any fix, from a backlog row or log entry whose Evidence section describes a reproduced blocker.

**Rule:** Before drafting, re-run the origin's own probe against the current tip: the scan, command, or check that produced the witnessed failure. A green or empty result is a scope-changing discovery: the disposition becomes close-as-covered, naming the commit that landed the fix, not a plan. The entry's keep-open condition (a chosen contract and a discriminating witness landed) may already be satisfied, and the cheaper catch matters: a full authoring cycle plus review panel spent on a stale premise is the wasted cost.

**Why:** witnessed 2026-10-18 (playbook repo): a release-privacy cleanup was authored from an entry whose blocker evidence was three hours old; the covering redaction had landed in between, and the affected set re-derived empty only at the r1 five-worker review: four workers independently measured the scan green on the current tip. The round folded into a closure landing instead of a plan.

**See also:** #58 (reproduce the live failure shape before re-keying a spec), #85 (claims follow the source changes' direction).

## 90. Gate Scripts With Subcommands Refuse Bare-Path Invocations Loudly, Not Silently

**Principle:** Family A (verify the tool contract before reading an exit code: a usage message with exit 0 is not a clean scan).

**Trigger:** invoking a repository check script with a bare file path when its CLI requires a subcommand (for example `check-no-em-dash.sh <path>` instead of `check-no-em-dash.sh file <path>`).

**Rule:** Before treating a check script's exit 0 as a pass, confirm the invocation matches the script's usage header; a subcommand-taking script called with a bare path prints its usage and exits 0 without scanning anything. Call the documented subcommand form, and when composing gate chains, let the script's own usage text resolve the form rather than assuming a positional contract.

**Why:** During an authoring run, an em-dash gate was invoked as `check-no-em-dash.sh <plan.md>`, which printed the usage text and exited 0; the run recorded "em-dash clean" from a scan that never ran. The correct `file` subcommand form was recovered from the usage header only after a later gate failed for an unrelated reason.

**See also:** #68 (verify the executing context's primitives before dispatch: the same verify-the-contract discipline at the CLI boundary).

## 91. Ceiling a Computed Schedule Time to the Whole Minute the Chain Arms

**Principle:** Family A (verify the tool contract before invoking: a schedule surface arms whole-minute fire times, so a computed sub-minute time is a refusal, and flooring it would silently shrink the margin the schedule exists to preserve).

**Trigger:** deriving a clocked-order (or any wall-clock carrier) fire time from a probe reading or reset timestamp plus a margin.

**Rule:** After computing fire = anchor + margin, ceiling to the next whole minute before invoking the schedule surface; never truncate. Rounding down can land the fire inside the walled window the margin was measured to avoid.

**Why:** witnessed 2026-10-18 (playbook repo): a re-arm computed reset 11:53:21 plus a 10-minute margin as 12:03:21; the clocked-order chain refused the sub-minute request, and the retry at 12:04:00 armed cleanly. The chain's own helpers round reset times up to the whole minute; a caller-computed time must do the same.

**See also:** #86 (list the live carriers before arming a scheduled one-shot).

## 92. The Cap-Closure Certification Record Rides the Series' Highest Round

**Principle:** Family A (precision-critical values are re-derived at validation time: the landing sweep hard-validates the series' highest round against the current plan bytes, so a closure record numbered below a pre-fold round leaves stale bytes as the validation target).

**Trigger:** closing a plan loop at its round cap with the cap-closure terminal shape, where the folding round produced the final plan bytes but an earlier-numbered record carries the closure extension.

**Rule:** After folding the cap round's findings, make the closure certification record the series' highest round and re-bind its sidecar `source_digest` to the folded bytes; the extension's `round` value moves with the renumber. A highest round whose digest predates the fold refuses the landing sweep on a stale digest.

**Why:** witnessed 2026-10-18 (playbook repo): a series carried the cap-closure certification at a round number below a pre-fold record that remained the highest; the landing sweep refused on that highest round's stale digest. Renumbering the certification record above it, with the digest re-bound to the folded plan bytes, let the same sweep pass without touching the validator.

**See also:** the review-staging skill's cap-closure extension keys (the sidecar contract this numbering duty completes).

## 93. Resolve a Landing Conflict by Union of Intents

A merge or rebase inside a landing critical section resolves each conflict
block by union of the two sides' intents, never by taking one side of the
hunk: a side-pick silently drops the other side's intent. A branch-side pick
reverts a peer's landed lines; a base-side pick resurrects hunks the branch
removed, so the landing carries a removal it claims but did not perform.

Rule: keep each side's stated intent (a branch removal stays removed, a base
addition stays added; overlapping edits merge line-by-line keeping foreign
lines). Then re-verify every destructive intent on the post-merge tree: the
duty's scope is any merge or rebase whose result feeds the landing's gates,
whether composed before lock acquisition or inside the critical section, and
its timing is always before the landing gates next run - re-grep each pruned
heading or removed span absent, and re-run the landing's receipt audits
against the post-merge bytes (the audit's receipt-without-removal warning
class is the mechanical backstop on that re-run).

**Principle:** Family H (verify the real tree after a conflict resolution,
not the resolution's intended shape; the merged bytes are the record).

**Why:** witnessed 2026-10-18 (playbook repo): a stale-base re-land merged
main under the held merge lock, the conflict juxtaposed the branch's pruned
dispatch entry against main's new entry in the same region, the resolution
took main's side, and the pruned entry returned with its Frozen line; the
landing carried only the +1 prune receipt and the removal completed as a
post-landing repair commit. A post-merge re-grep of the pruned heading would
have caught it inside the lock for one command.

Mirror witness 2026-10-09 (playbook repo): a branch-side pick inside a kept
shared file reverted a peer's landed line, caught only by a manual
post-rebase diff; the landing-text fix routes through
docs/history/plans/completed/2026-10-18-landing-conflict-intent-union.md.

**See also:** #6 (the merge-and-re-land flow whose "resolve conflicts
faithfully" clause this lesson pins down); #44 (the receipt surface the
repair had to satisfy).

## 94. Script a Structural Move From and Against Current Bytes

**Principle:** Family H (verify the real thing: a scripted restructure's document model is an abstraction; both its regions and its result must be derived from and checked against the current bytes).

**Trigger:** a review fold or correction that restructures a structured document (moving a section, reordering checklist items, folding one block into another) via a scripted splice whose source and destination regions were worked out from an earlier read or from a summary of the file.

**Rule:** derive the move's source and destination from a fresh read of the current bytes immediately before scripting, and pin every region with an exact-match assertion. After the mutation, assert the membership invariants an anchor check cannot see: per-section item counts match the pre-mutation inventory, each per-section anchor (a task's `Files:` list, a section heading) occurs exactly as many times as intended, and the origin region holds what the move intends it to hold. Anchor uniqueness and output-size signature (#51) pass on well-formed misplacement; only membership checks catch content that landed in the wrong section.

**Why:** witnessed 2026-10-18 (playbook repo): during one plan's certification folds, three scripted restructures ran with valid anchors and plausible sizes while wrong. A reorder dropped 10 checklist items; a splice nested one task's body inside a sibling task (duplicate `Files:` block); a relocation authored against a misread premise left a drifted task copy inside the plan's review-scope section. The plan's own structural gates caught the first two; the next review round caught the third. Each recovery was a full-file rewrite from a fresh read plus a re-run script carrying exact-match assertions.

**See also:** #51 (anchor uniqueness and size signature), #88 (re-derive prepared spans after a branch switch), #64 (never probe pin mutations with sed).

## 95. Report Workflow State as Gates Passed, Not Artifact Existence

**Principle:** Family H (verify the real thing: what a staged workflow reports is the state of its stage contract, of which the artifact is only one input).

**Trigger:** a status report or completion claim for a multi-stage skill run (authoring, review, execution) where the artifact exists but later stages (validation, review, certification) have not run, or an operator question asking whether a workflow was followed or finished.

**Rule:** when reporting a staged workflow's status, name each stage of the owning skill's contract and mark it executed or pending; never let "the artifact is written" stand in for "the workflow is done". Treat an operator's "is it finished / did you follow the skill" as an audit prompt: re-derive the stage state from the gates actually run (readiness output, certification records, commits), answer stage by stage, and if a mandatory stage was skipped, say so before anything else.

**Why:** witnessed 2026-10-18 (playbook repo): a plan was reported ready for handoff after drafting while the plans skill's review-and-certification phases had not run. The operator had to ask twice ("did you follow the plans skill and did the review?") before the skipped review surfaced, and the plan only then reached its certified state through five review rounds.

**See also:** #77 (a claim file is not evidence of a live session), #78 (prove landedness from witnesses, not metrics), #16 (a stop order suspends the named stage, not finished stages' bookkeeping: the stop-scope sibling of this reporting rule).

## 96. Scope Worktree Reviews Transfer-In To The Consumed Series

A fresh execution worktree's wholesale reviews transfer-in (the Worktree-first standard's step 2 copy) seats thousands of foreign staging docs in the worktree, and the done setup's write-manifest claim-or-foreign gate then refuses them all as "neither owned nor foreign" (witnessed 2026-10-18, done-setup-task-owned-start-dirt-claims execution). The gate's own bulk answers are the remedy: pass `--claim-none` when the run owns no staging doc in the reviews home, and scope the transferred copy to the review series the run actually consumes so the readiness gate still resolves. The primary checkout's staging docs are never touched by the trim; they are copies.

## 97. Compose an Exact-Match Edit Anchor From a Fresh Read, Never From an Earlier View

**Principle:** Family D (state-first: the bytes on disk at edit time are the only anchor of record; a remembered span is a stale read).

**Rule:** when drafting an exact-match replacement, read the target span immediately before composing the anchor, and after any multi-line edit to a syntax-bearing file run that file's parser (or at minimum a diff review of the single edit) before anything else consumes the file.

**Why:** witnessed 2026-10-19 (playbook repo): a help-text edit was anchored from a `sed` view read several operations earlier; the reconstructed anchor differed from disk by one punctuation character and the edit landed at a shifted boundary, turning a closing paren into a tuple and breaking the module's syntax. The corruption surfaced only in a later diff review; a parser run immediately after the edit would have named it in one line. Same family as #94's fresh-bytes rule, narrower shape: per-edit anchors, not scripted structural moves.

**Shape trigger:** any exact-match edit whose old text is quoted from memory, from an earlier read, or from a command output rather than re-read at edit time.

## 98. Verify a Scripted Plan-File Edit by Count Invariants Before Commit

**Rule:** any scripted edit to a plan file (checkbox ticks, box rewrites, batch replacements) verifies mechanical count invariants before the commit: line count within an expected delta, checked/unchecked box counts before versus after, and exactly one title heading. A tick script that only mutates the first checkbox before each pattern can silently duplicate the whole document or splice lines; the duplication is invisible to the script and to a casual diff.

**Why:** witnessed 2026-10-19 (playbook repo): a takeover session's Python box-ticking edit grew the plan file from 250 to 499 lines (a full body duplicate plus a mangled splice line) and committed it; the corruption was caught only by an independent execution reviewer, not by the edit script, the committer, or any gate.

**See also:** #94 (script structural moves against current bytes), #97 (compose edit anchors from a fresh read).

## 99. Route the Landing Critical Section Through the Landed Helper, Never a Hand-Composed Squash

**Rule:** when the Worktree-first standard's landing bullet names a helper invocation (`scripts/land_squash.sh land-worktree`) as the class's mechanical operation, the landing runs through that helper; a hand-composed rebase-plus-squash-plus-compare-and-swap sequence reproduces the shape but silently skips the gates the helper owns: base freshness (`reverse_squash_guard.py check-landing`), the plans-egress archive gate (`check-archive`) on any landing that moves plan files into an archive directory, and the helper's outcome-contract routing.

**Why:** witnessed 2026-10-19 (playbook repo): two plan-execution landings were hand-composed (manual rebase, manual squash commit, manual `git update-ref` with the parentage gate run by hand) and moved executed plans into `completed/` without the archive-egress gate the doctrine requires at that checkpoint; the landings were correct by luck, not by gate. Re-witnessed 2026-10-22 (exec-mode ad-hoc run): the run's first ad-hoc landing was again hand-composed (`git merge --squash` plus a hand commit in the primary checkout) before the run noticed this lesson and routed its second landing through `scripts/land_squash.sh land`; the composed landing skipped the helper's gates and was accepted as landed history under the base-branch immutability rule. Re-witnessed again 2026-10-22 (parallel exec-mode run, max 3): both of that run's worktree landings were hand-composed (manual rebase, `git commit-tree` squash plus two-value `git update-ref`), each skipping the helper's parentage and tree-equality gates; the ad-hoc arm's landing sentence never names the helper, which is the suspected reason the form keeps recurring.

**See also:** #34 (`--expected-tip` is the base tip), and the landing bullet in `agents/skills/execute-plan/SKILL.md` (the worktree-complete class's helper invocation is the operation of record).

## 100. A Ref-Only Landing Into a Peer-Held Primary Checkout Leaves Reversal-Shaped Staged Residue at Switch-Back

**Rule:** when a landing moves the base-branch ref while the primary checkout is held by a peer session on its own branch, the primary's index cannot be reconciled in-turn; record it and expect reversal-shaped staged residue (the landed archives un-archived, deleted rows re-added, landed edits stripped) to appear when the peer switches back to the base branch. Any working-tree reader after the switch-back (a plans-root census, a survey, the operator's `ls`) sees the reversal until it is cleared; verify the index against `HEAD` before treating working-tree state as landed truth, and clear reversal residue only after confirming the staged bytes are pre-landing snapshots.

**Why:** witnessed 2026-10-19 (playbook repo): three squash landings moved `main` while a peer landing held the primary checkout on a non-base branch; the peer's staged snapshot became a byte-level reversal of all three landings at switch-back, and the operator read the plans as "still on main".

**See also:** #77 (a claim file is not evidence of a live session).

## 101. Disk-Verify Adopted Reviewer Phrasing Before a Fold Lands It

**Rule:** when a review fold adopts a reviewer's suggested replacement text verbatim, every referent the adopted phrasing names gets the same on-disk verification a finding gets before the fold commits; adoption is not triage.

**Why:** witnessed 2026-10-18/19 (playbook repo): the r2 fold adopted "the recipe's existing escalation paths and attempt bound" verbatim; "attempt bound" had zero occurrences in the cited recipe (the named surface lives one file up in the maintenance SKILL.md), the defect survived four delta-focused rounds that never re-read folded text, and the plan's span needle would have frozen the dangling citation permanently; the r7 contract-docs worker caught it only by chasing the citation.

**See also:** #96 (scoped reviews transfer-in), #89 (a value quoted from conversation context is not evidence).

## 102. Post-Certification Plan Byte Changes Route Through a Delta Round

**Rule:** the readiness gate binds the latest review sidecar's source digest to the landing bytes, so any post-certification plan edit (a gate-prescribed re-chunk included) is followed by a focused delta verification round over exactly that diff; the executability contracts (512 UTF-8 bytes per criterion, 4096 per task aggregate, canonical anchors-entry shape) bite plans whose criteria grow across review folds, and re-chunking is the gate's own prescribed remedy.

**Why:** witnessed 2026-10-19 (playbook repo): a plan certified at r8 grew to 2178-byte criteria and a 6357-byte task aggregate across nine rounds of folds; the landing-time gate refused, the split re-chunk restored the limits, and the r9 delta round (zero findings, clause-by-clause coverage check) restored the gate to pass.

**See also:** #99 (route the landing critical section through the landed helper).

## 103. Reconcile a Plan Whose Precondition a Peer Completed During Review

**Rule:** when a rebase onto the moved main reveals a peer landing already performed one of the plan's steps (with its covering row deleted), replace the stale steps with completed-precondition verification items that name the peer's covering witness commit and carry a fallback arm to the filed prescription, then run a focused delta round over the reconciliation diff; never land a plan whose steps contradict the tree an executor will meet.

**Why:** witnessed 2026-10-19 (playbook repo): peer commit 6f6082dd8 re-keyed the stale schedule-ask pin to the exact short needle the plan prescribed and deleted the covering fix row while the plan sat in review; the reconciliation (verify items + fallback) passed the r10 delta round and the pinned baseline stayed green.

**See also:** #100 (peer-held primary checkout landings), #85 (release-summary claims follow the witness).

## 104. A Deleted Backlog Origin Row Fails the Origins Archive Gate; Archive It Covered

**Rule:** the origins gate's served dispositions for a landed plan's backlog origin row are archived under `docs/history/backlog/completed/` with the covered flip, archived under `rejected/`, or a closed-status header at the top level; a filesystem `rm` reads as `missing` and fails closed as a straggler, so removal from the top level means move-plus-flip, not deletion.

**Why:** witnessed 2026-10-19 (playbook repo): the silent-strand row was `git rm`-ed as the covering witness and the archive gate refused twice (missing = straggler) until the row was restored under the backlog completed archive with `- **Status:** covered (<plan path>)`; the default completed directory is `docs/history/backlog/completed`, not the plans completed dir.

Re-witnessed 2026-10-20 (playbook repo, execution run): the plan's origin row was deleted by following the repository guidelines' covered-row bullet literally; the closeout's origins gate refused the done commit until the row was restored under the backlog completed archive with a done status naming the covering plan, costing a repair commit before the landing. The guideline bullet now names the archive disposition for a landed plan's origin rows, so the two no longer disagree.

**See also:** #100 (landing helper contracts), #80 (done boundary setup).

## 105. Count Each Partition Class per Member, Never by Subtraction

**Principle:** Family D (disk-first: a class membership is a property of the member, established by testing the member; a complement count derived from an unverified total is a guess carrying a measurement's label).

**Trigger:** an inventory or audit that splits a population into classes (resolving vs dangling links, tracked vs stray files, matching vs non-matching records) and reports per-class counts into a durable artifact.

**Rule:** count every class by probing each member directly (resolve the link, stat the file, run the predicate), and reconcile the measured classes' sum against the population total. Never derive a class count by subtracting another class's count from the total, and never classify a member by pattern-matching its target text or name: the pattern proves the text's shape, not the property. A count not obtained by direct per-member measurement must not be labeled as measured or verified on disk.

**Why:** witnessed 2026-10-18 (playbook repo): a runtime-home inventory classified the home's symlinks by target-text glob and derived the resolving class as the complement of the backup-link count (73 of 126). Per-link resolution showed 66 resolving and 60 dangling, because 7 live-named links whose target text named the primary checkout pointed at files retired from the repository. The subtraction-derived partition passed as a disk measurement into a filed backlog row until the review panel probed per link.

**See also:** #69 (derive a match pattern from on-disk names, not from a citation's prose - the false-refuse sibling of this false-pass shape); #78 (prove landedness from witnesses, not diff metrics); #74 (treat a zero-count success as unverified until the consulted tree is confirmed).

## 106. Run-Tmp Evidence Needs a Durable Copy Before Any Done Boundary Step

**Rule:** evidence a later phase must consult (the pins-suite baseline, the session manifest) is kept outside the run's gitignored `docs/tmp/` scratch as well as in it; after any `done_run.sh` step, re-verify the scratch copies still exist before relying on them, and re-derive from the base commit when a scratch file is gone.

**Why:** witnessed 2026-10-18 (playbook repo, execution run): the run's own tmp directory was emptied twice across done boundary steps, taking the recorded pins baseline with it; the baseline was recovered by re-running the suite at the merge base in a scratch checkout and byte-comparing the tail. The sweep treats untracked tmp as residue, so anything only in tmp is one boundary step from loss.

**See also:** #74 (treat a zero-count success as unverified); #80 (done boundary setup).

## 107. The Plan-Egress Guard Wants Its Exec-Review Record Written Before the Landing Call

**Rule:** before a plan execution's merge-locked landing, write the execution review record under `.ai-playbook/reviews/` named `*-plan-review-<plan-slug>-exec-r<N>.md` (hyphen-bounded) carrying the archived plan bytes' sha256; the egress guard reads it at the plans-root archive move and refuses the landing without it, and the worktree reviews home is where the record must already sit. Production point: the execute-plan flow writes the initial receipt at its Step 3.5 exit decision, when Step 3.5 selects Phase 4 (the blocking-clean exit and the satisfied residual-acceptance exit alike; a continue decision writes none); refresh point: Phase 4 refreshes the receipt's digest to the final archived plan bytes after the archive disposition section and before the archive commit and its `check-archive`; the landing call then only reads the record.

**Why:** witnessed 2026-10-18 (playbook repo, execution run): the first `land_squash.sh land-worktree` attempt refused at the plans-egress leg naming the missing record and the exact digest it must carry; writing the record and re-landing under the held lock passed. The record doubles as the migrated execution evidence.

**See also:** #100 (landing helper contracts), #104 (archive gates fail closed).

Re-witnessed 2026-10-20 (playbook repo, execution run): the run's two `-code-review-r<N>` records carried the archived plan's sha256, yet the first landing attempt was refused because the guard matches the `-exec-r<N>` name grammar, not the digest alone; the receipt was written after the refusal and the second attempt landed. Fourth same-shape witness in a week: the receipt belongs to the Step 3.5 Phase 4 exit, not to the landing retry.

## 108. An Evidence Digest Comes From the Bytes on Disk, Never From a Command's Fallback Output

**Rule:** when a gate or record requires a digest of specific bytes, compute it by hashing the artifact's bytes on disk (`shasum -a 256 <path>`) at claim time and confirm the path resolved; a string captured from a command that failed and fell back to echoing its argument (a failed rev-parse printing `main:<path>` verbatim) is not the digest. Before a digest enters a durable record, shape-check it (fixed-length lowercase hex) and re-derive it a second time.

**Why:** witnessed 2026-10-19 (playbook repo, execution run): while satisfying the plan-archive egress guard (lesson 107), the first digest capture took a literal `main:docs/...` string from a failed rev-parse fallback; a shape check caught it before any gate consumed the record, and re-hashing the worktree file produced the digest the guard accepted.

**See also:** #107 (the egress record that demanded the digest); #105 (measure a class by probing members, never by derivation); #78 (prove landedness from witnesses, not diff metrics).

## 109. A Lost Lock-Acquire Capture Orphans the Hold

**Rule:** parse the merge-lock acquire's stdout into its variables inside the same shell invocation that runs it (capture once, extract each field), and run the landing in that same shell; a capture construct that yields empty (quoting or subshell loss) leaves the hold acquired with no usable token record, and the exiting shell orphans it. Recovery for an orphaned hold: verify the hold record's holder pid is dead, run the orphaned-release subcommand (`merge-release-orphaned`), then redo acquire plus landing in one shell. Never leave an orphaned hold standing and never re-acquire over one.

**Principle:** Family D (a hold's own records are the recovery source; the orphaned-release arm exists for a hold whose owner output is gone).

**Why:** witnessed 2026-10-19 (playbook repo): the acquire's eval-style capture produced empty lock variables, the landing refused on the missing `--message`, and the exited shell left the hold orphaned; the orphaned-release subcommand passed after the holder-pid check, and the same-shell redo landed unchanged.

**See also:** #35 (lock exports die at the tool-call boundary; the hold record is the recovery source), #34 (re-derive landing-helper flags from refusal messages).

## 110. A Resumed Run Takes Over the Inherited Execution Claim Before Work

**Rule:** a session resuming another session's execute-plan run re-binds the inherited claim at start per the claim gateway's stale-foreign-takeover arm (re-read, unlink while it still names the foreign session with a stale `updated:`, recreate under this session's id); a claim refreshed inside the cadence window is a fresh foreign claim and refuses the start instead. A continuation that skips the takeover cannot release at closeout (release is owner-bound and refuses a foreign session id); after the worktree is removed, its discharge is the claim gateway's sweep arm, which deletes claims whose plan is landed and whose branch holds no worktree.

**Principle:** Family D (the claim's session line is keyed state; rebind it where the release will read it).

**Why:** witnessed 2026-10-19 (playbook repo): a resumed run inherited the original session's claim and skipped the takeover, so closeout `release` refused on a session-id requirement; the sweep after worktree removal deleted the run's own claim (plus one already-spent peer claim) and the closeout completed.

**See also:** #35 (the same one-shell discipline for lock context), #96 (the same closeout's bulk answers for transferred reviews).

## 111. A Structural Range Delete Still Owes Its Contents an Ownership Inventory

**Principle:** Family A (bounded deletion: an anchor pair locates a region; it never vouches for every line inside it).

**Trigger:** pruning a rolling-log entry, removing a config block, or deleting any section found by heading or delimiter match, when foreign records accumulate between the same anchors.

**Rule:** before deleting a section selected by structural anchors (heading to next heading), inventory the range's contents and classify each foreign record (a receipt line, an annotation, a trailing note) for preservation; delete only the lines the operation owns. Re-read the fresh bytes before the deletion and never trust a remembered layout: receipts and notes migrate between entries as peers land.

**Why:** witnessed 2026-10-19 (playbook repo): a plan's landing rider pruned its own dispatch entry with a heading-to-next-heading range delete and silently removed the neighboring landing's receipt line that sat at the range's tail; the execution review caught it, not the prune audit, which counts entry removals but not foreign receipt-line removals (the same audit gap the open row docs/history/backlog/2026-10-15-plan-prompts-prune-end-anchor-overreach.md records; the new witness is appended there). See also #44.

## 112. After a Restore-Based Reconciliation, Verify the Index, Not Only the Worktree

**Principle:** Family D (state-first: a checkout's restore writes more surfaces than the one you read back; the index is the silent one).

**Trigger:** any post-landing reconciliation or stale-checkout restore that runs a wholesale or containment-delta restore arm over the primary checkout, before declaring the checkout clean.

**Rule:** after a restore-based reconciliation completes, read `git status --porcelain` (index plus worktree), never a working-tree diff alone: a restore arm can leave the pre-restoration bytes staged in the index while the worktree holds the fresh bytes, presenting later gates with unowned staged dirt that looks like a peer's staging violation. The remedy is a per-path `git restore --staged` after confirming the staged bytes equal an ancestor blob (the stale-checkout discriminator's half-synced arm), never a blanket reset.

**Why:** witnessed 2026-10-19 (playbook repo): a landing's reconciliation receipt reported a wholesale restore plus per-path containment-delta restores with exit 1; the working tree matched the new tip, but the index still held the pre-landing ancestor blob of the restored log file, and the checkout read as carrying a foreign staged reversal until the index entry was cleared. The receipt's exit code was the only surface that flagged the block; the index residue surfaced only through the porcelain read.

## 113. Wire the Guard to the Channel Where the Verdict Rides

**Principle:** Family H (verify the real thing, not the abstraction: the verdict itself, not a command's success).

**Trigger:** composing an `&&` / `if` guard over a probe command, when the probe is known to speak through output rather than exit status.

**Rule:** an exit-status guard only gates when the verdict rides the exit channel; some verdict-bearing tools exit 0 unconditionally and report only on stdout, so a guard over them fires identically on clean and dirty input. Before trusting such a guard, check which channel carries the verdict: `grep -q`-style checkers carry it in the exit status; listers and dedupers (`uniq -d` among them) carry it in stdout. When the verdict is stdout, test the output explicitly (`[ -n "$(cmd)" ]` or a verdict-carrying consumer) and let that test be the guard.

**Why:** witnessed 2026-10-19 (playbook repo): a duplicate-check over a registry's item list used `uniq -d && echo "DUP FOUND"`, which exited 0 on every run; the alarm was reported as a false positive and the corrected duplicate count came from counting the stdout, which was zero. See also #38 (the composition-masking sibling: the verdict exists in the exit channel and is lost in a pipeline tail; here it never enters that channel).

## 114. A Failed Lookup Is First Evidence About the Lookup String

**Principle:** Family H (verify the real thing, not the abstraction: the identifier's source bytes, not the recollection of them).

**Trigger:** any existence or lookup probe over a path or identifier transcribed by hand from an earlier tool output, before reporting the target as missing.

**Rule:** a failed lookup over a hand-copied identifier fails in two distinct worlds: the target is absent, or the transcription dropped or altered a component. Re-copy the identifier verbatim from the listing that produced it (or re-run that listing and match) before concluding the target is missing; when the identifier is quoted from conversation memory instead of a fresh read, the re-derive-from-disk rule applies first. Consume a negative lookup result only after the probe's input is verified against its source.

**Why:** witnessed 2026-10-19 (playbook repo): an ad-hoc worktree was briefly concluded missing because its absolute path was retyped with the repo-root components dropped between the listing and the probe; the verbatim re-copy against the same worktree listing restored the target on the first try and every follow-up check passed against the real path. See also #42 (a contradictory probe result indicts what the probe read; this extends the indictment to what the probe was handed).

## 115. Registrations Above Their Helper's Definition Never Run

**Principle:** Family H (verify the real thing, not the abstraction: the registration executed, not the file edited).

**Trigger:** adding check registrations (pin-style or check-style calls) to a script whose registration helper is defined partway down the file.

**Rule:** place a registration only after the line where its helper is defined; a call above it runs nothing while the shell still prints a tolerated "command not found" naming the helper, so the check is inert and the suite looks green. Before inserting, locate the definition (`grep -n` the helper name); when a new check "passes" without ever exercising anything, suspect this first. See also #25 (the same silent-dead-shape in test modules: classes appended after the main guard never collect).

**Why:** witnessed 2026-10-19 (playbook repo): two pins registered above the pins suite's `pin()` definition executed nothing; the suite printed `pin: command not found` on every run and still passed, and the intended RED state did not fire until the registrations were relocated into the pins region.

## 116. A Strict Read Wired Beside a Lenient Accessor Keeps the Lenient Channel Live

**Principle:** Family H (verify the real thing, not the abstraction: the value the handler consumes, not the strict call it makes).

**Trigger:** introducing a strict (fail-closed) reader to replace a fail-open accessor in a module with existing consumers.

**Rule:** after wiring a strict reader, grep the module for remaining call sites of the old accessor; every consumer must iterate the strict call's return value, because a strict call whose result is discarded leaves the fail-open path as the operative channel and the failure mode the reader was added to prevent survives the migration untouched.

**Why:** witnessed 2026-10-19 (playbook repo, execution review r1): a ledger handler called the new lock-held strict read but iterated the old fail-open order list, so malformed entries still flowed into the handler; the fix iterated the strict read's return. The blocking finding came from review, not from the change's own tests.

## 117. A Dispatch Layer That Normalizes Names Silences Full-Name Matchers

**Principle:** Family H (verify the real thing, not the abstraction: the name as dispatched, not the name as declared).

**Trigger:** adding a handler branch to a dispatcher that rewrites operation names before routing (stripping a prefix, lowercasing, aliasing).

**Rule:** a matcher keyed on the un-normalized name never fires under such a dispatcher, and the symptom is a silently unmatched operation, not an error. Match the normalized form, or both spellings when callers legitimately use either, and exercise the branch through the dispatcher's own entry path (CLI or payload), not by calling the handler directly.

**Why:** witnessed 2026-10-19 (playbook repo): the plan-execution runtime strips a `clocked-order-` prefix from operation names before dispatch, so a new handler branch keyed on the full operation name would never fire; the branch matched both spellings and the CLI-path test exercised the stripped form the dispatcher actually delivers.

## 118. A Short-Circuit Matcher in a Pipefeed Kills the Producer Under pipefail

**Principle:** Family H (verify the real thing, not the abstraction: the pipeline's verdict, not a member's early exit).

**Trigger:** writing `producer | grep -q pattern` (or any `-q` matcher that exits on first hit) inside a script running `set -o pipefail`, before treating pipeline failure as a miss.

**Rule:** a first-hit matcher closes the read end as soon as it matches, so a long producer can die on SIGPIPE (exit 141); with `pipefail` the pipeline then reports failure on a successful match, and a membership check reads a hit as a miss (a guard then refuses something that satisfies it). Feed a matched consumer from a captured value instead: capture the producer's full output into a variable or file, then run the matcher on the capture with an `if`/`case`, so no live pipe connects a SIGPIPE-able producer to an early-exiting consumer.

**Why:** witnessed 2026-10-19 (playbook repo): a release-recovery precondition piped `git rev-list --first-parent` into `grep -q` to prove the base commit was first-parent-reachable; grep matched early, rev-list died with 141, `pipefail` surfaced it as a miss, and the recovery was spuriously refused with a "not first-parent" message. The capture-then-case rewrite never reproduced it. See also #38 (the sibling where the verdict exists in the exit channel but is lost in the pipeline tail; here the verdict enters the channel and the producer's death fakes a miss) and #113 (a verdict that never enters the exit channel at all).

## 119. A Range Enumeration Cannot Be Trusted to Exclude Its Own Anchor

**Principle:** Family H (verify the real thing, not the abstraction: the enumerated set, not the range expression's promised semantics).

**Trigger:** enumerating commits with a range (`base..tip`, first-parent tiling, chained exclusions) and then slicing, counting, or rewriting the result on the assumption the lower anchor is absent.

**Rule:** after enumerating a range for a positional operation, filter the anchor commit explicitly and derive every count and index from the filtered set; the range operator's exclusion of the lower bound is a convention of some invocation shapes, not an invariant of the output, and an unfiltered anchor shifts every position, count, and rewrite seed built on the list. A cheap assertion (anchor not a member of the filtered set) converts the silent shift into a loud refusal.

**Why:** witnessed 2026-10-19 (playbook repo): the release-recovery rewrite enumerated the recoverable tail with a first-parent walk and the lower base commit appeared among the members in one invocation shape; seeding the rewrite's predecessor pointer from the selected base then had to be paired with an explicit filter of the base and a `range_count` derived from the filtered array, and the tests pinned the count against a fixture where the merge and notes commits sat at different first-parent depths. See also #105 (measure by probing members, never by derivation).

## 120. Count the Escape Layers When a Script Generates Shell Text

**Principle:** Family H (verify the real thing, not the abstraction: the bytes the generated file carries, not the source line that produced them).

**Trigger:** a generator script emits shell code containing runtime-expansion literals (`$0`, `"$@"`, `$(...)`) that must evaluate only when the generated file runs.

**Rule:** decide, per token, whether the generator should expand it now (single `\`) or emit it inert for the consumer (double the backslash: the generator source writes `\\$0` so the file carries `\$0`); a miscount produces either a literal backslash plus an expansion in the generated file or an empty expansion at generation time. After generating, read the emitted bytes (or run the generated file's syntax check) before executing it, and fix the generator, never the generated artifact by hand.

**Why:** witnessed 2026-10-19 (playbook repo): a release push-script generator emitted its self-delete trap twice with a doubled backslash, so the persisted script carried a literal `\` before an expanding `$0`; both the ordinary trap line and the recovery cleanup trap were corrected in the generator with the single-escape form and verified by reading the emitted bytes, not by trusting the source line. See also #108 (a digest from a fallback output: the same verify-the-emitted-bytes discipline).

## 121. A Directory-Contract Helper Fails a File Operand Silently

**Principle:** Family H (verify the real thing, not the abstraction: the operand the helper actually accepts, not the one the caller holds).

**Trigger:** passing a file path to a helper whose contract is a directory (`git -C <path>`, a chdir-based probe, a root resolver) and treating the failure result as "not derivable" rather than "wrong operand shape".

**Rule:** a directory-contract helper fails a file operand (`git -C <file> rev-parse` exits 128 with "not a directory"), so a caller holding a file path passes `path.parent` and the wrapped failure surfaces as an ordinary None/empty result - the caller then silently degrades to its no-value fallback while the real cause is the operand shape. Before wiring a resolver into a new caller, check the operand contract at the helper, and make a None result distinguishable (or assert the input kind) when the fallback changes behavior downstream.

**Why:** witnessed 2026-10-19 (playbook repo, execution run): the plan-identity derivation passed the plan file to a `repository_root` helper that shells `git -C <path> rev-parse --show-toplevel`; every derivation returned None, the identity diagnostics never fired, and seven new tests failed before the parent-directory fix. See also #42 (a contradictory probe result indicts what the probe read; here the probe was handed a file where it required a directory) and #114 (a failed lookup is first evidence about the lookup string).

## 122. The Execution Landing Does Not Archive the Plan; the Archive Move Is Its Own Landing

**Principle:** Family D (state-first: what the landing tool actually mutates, not what the ceremony implies).

**Trigger:** a plan execution's merge-locked landing, when concluding the executed plan is archived by that landing itself.

**Rule:** the squash landing lands branch content only; the executed plan's move from the plans root to the completed archive is a branch commit the executor composes and lands through a second landing call (the egress backfill record carrying the archived bytes' sha256 gates it). After the implementation landing passes, verify the plan's archive location on disk before teardown; a missing move means the archive landing is still owed.

**Why:** witnessed 2026-10-19 (playbook repo, execution run): the first landing passed with the egress record present, but the plan stayed at the plans root; the move was composed as a branch commit and landed as a second squash. The same shape repeated the prior day's run, and the gate-removal squash-accounting row records the accounting twin of it. Third witness (2026-10-21, certification-seal-landing-survival landing): when the archive move rides the same squash, any post-squash step that resolves the plan's review series by identity (the readiness oracle keys `plan_identity` to the pre-archive active path) finds nothing at the completed path; run such a step against the pre-archive identity or order it before the move (residual L1 in `docs/history/backlog/2026-10-21-seal-landing-survival-review-residuals.md`). See also #104 (the origins archive gate's covered-row arm) and #107 (the egress record the archive move wants).

## 123. A Squash Landing Absorbs the Branch; Post-Landing Branch Work Rebases as a Reset

**Principle:** Family D (state-first: the branch no longer contains unique history once its squash landed).

**Trigger:** rebasing a branch onto a moved main after the branch's content already landed as a squash commit.

**Rule:** once a branch's content landed as a squash, every branch commit conflicts against its own landed copy at rebase - the rebase replays identical changes onto text that already contains them. The remedy is not conflict resolution but a reset: point the branch at the new main and re-apply only the genuinely residual commits (a post-landing archive move, a late rider) as fresh commits, then land that. Detect the shape by the conflict appearing in the branch's own hunks, and confirm with a grep of main for the branch's distinctive added lines before touching the rebase.

**Why:** witnessed 2026-10-19 (playbook repo, execution run): after the implementation landing passed, main moved; rebasing the branch for the archive-move landing conflicted inside the branch's own test file, with the HEAD side already carrying the corrected lines; the branch was reset to main and the archive move recommitted, landing cleanly. See also #112 (the staged residue the same landing left in the primary index) and #101-family (landing critical sections serialize under the merge lock; peers move main between a certification and its landing).

## 124. Stamp a Record From the Operation's Own Clock, Never a Carried One

**Principle:** Family H (verify the real thing, not the abstraction: the timestamp that names this write, not one inherited from context).

**Trigger:** writing any dated field (Filed, Updated, section stamps, heartbeat lines) in a session that spans resumes, superseded turns, or quoted context.

**Rule:** a record's timestamp is derived from the current operation's clock at write time. A date quoted from an earlier turn's output, a carried variable, or a superseded turn's context lands as a wrong stamp that reads as the record's truth until a corrective pass finds it. When the only visible clock is a superseded turn's output, re-read the current time before writing the stamp; when auditing a landed stamp, cross-check it against the date of the commit that carried it, which is ground truth.

**Why:** witnessed 2026-10-19 (playbook repo): a resumed session landed its resume-state section with the correct content but a section stamp two days stale, inherited from a superseded same-session turn's clock; the repair was a follow-up citation-only corrective commit whose message names the mechanism (e418023c2). Re-witnessed 2026-10-19 (same repo, hours after this lesson landed): a backlog row's Filed header and its commit message carried the operator-direction date quoted from an earlier conversation turn's context instead of the write-time date; the misstamp was removed with the row itself when the row was deleted as superseded (517c4e4d7). Re-witnessed 2026-10-19 (same repo, execution lane): an implement worker stamped both of its pins re-aim provenance comments with the plan slug's filename date instead of the write-time date; the Step 1.2b intermediate review caught it and the fix folded before the task 1 boundary commit of the skill-monolith-module-extraction execution run (2026-10-19).

## 125. The Learn Marker Recipe Binds Every Project-Corpus Write

**Principle:** Family D (the write gate is part of the corpus's state, not part of the learn invocation).

**Trigger:** appending to `docs/maintenance/development_lessons.md` from any flow - a harvest duty, a closeout, an ad-hoc fix - where the session does not think of itself as running learn.

**Rule:** refresh the skill-gate learn marker per the skill-gate README (the `session_channel.py` subprocess verbatim, then `skill_gate.py --write-marker learn`) before EVERY write to the project lessons corpus, whoever owns the surrounding flow; a write without its marker is silent missing telemetry, and skipping it because the write is not a learn run is the failure.

**Why:** witnessed 2026-10-19 (playbook repo): a maintenance closeout's harvest appended four lessons straight to the corpus without the marker; the gate is edit-time and no validator caught the miss; only a later learn run's corpus-gate re-read surfaced it.

**See also:** #38 (a verdict-bearing command's status must be observed directly).

## 126. Verify a Folded Artifact by Running the Committed Bytes, Not a Transcription

**Principle:** Family H (verify the real thing, not the abstraction: the bytes as committed, not a hand-typed equivalent of them).

**Trigger:** any fold or edit whose new machinery (a command block, loop, gate, or witness) claims a mechanical property, before citing the fold-time verification as evidence.

**Rule:** two failure shapes hide behind a passing fold-time check. First, the edit itself can silently no-op: a string substitution that matches nothing succeeds as a no-op, so assert the replacement changed the bytes. Second, the verification can run a hand-typed equivalent instead of the artifact's committed bytes, and the transcription drifts exactly where the fix was. Extract the artifact from the committed (or staged) file and run those exact bytes. Companion signature: a locator-class witness whose dry run classifies everything as the benign arm is reporting the tool's brokenness, not the tree's cleanliness; near-total benign classification means investigate the tool before believing the tree.

**Why:** witnessed 2026-10-19 (playbook repo): a review-record fold's quote-strip fix no-op'd through a substitution-escaping mismatch while the fold-time dry run executed a hand-typed loop that passed; the next round's panel isolated the defect in minutes, and the recorded "zero misses" was the vacuity signature rather than coverage. See also #114 (indict the transcription first; this extends the indictment to the verification's input bytes) and the fold-commit-staged-record precondition (the record-staging half of the same fold discipline).

## 127. Probe the Live Boundary Before Riding a Recorded Reset

**Principle:** Family H (verify the real thing: the boundary's live state, not the same runtime's recorded claim about it).

**Trigger:** any pause posture that schedules resumption at a recorded timestamp (a quota reset, a lock expiry, a rate-limit window) when the blocked operation is cheaply probeable.

**Rule:** the recorded reset time is a claim by the runtime that refused the operation, not a measurement of the boundary. Before letting a timed resume carrier fire at the recorded time, run one cheap probe of the refused operation itself: a clean probe lifts the pause immediately (the pause's own carrier is deleted by its owner as the duplicate-in-waiting it has become, and the pause record gains a resolution line), a refused probe leaves the carrier standing unchanged.

**Why:** witnessed twice in this repo's runtime (2026-10-17 and 2026-10-19): two usage-wall pauses idled their lanes toward the recorded reset, and a one-call probe ran clean about two hours early both times; the nominal-reset posture cost the idle hours and armed a second carrier over the live lane. Routed as the probe-first arm (the usage-wall-probe-before-timed-resume entry) with this lesson as the witness. Third witness 2026-10-20: a scheduler turn paused at 92 percent with the reset recorded for 16:39 and armed a 16:45 resume carrier; a probe at 13:44 read 1 percent with the live reset re-keyed to 18:37, so the recorded reset was replaced, not merely lifted early, and the carrier idled the lane about three hours. Fourth witness 2026-10-20: an execution run's probes read 63 and then 88 percent used against a reset recorded for 18:37 that evening with 165 minutes claimed remaining, and twenty-eight minutes after the second reading the window had already rolled over to 10 percent used with the reset re-keyed to 21:01, so a freshly reported reset was false within the half hour.

## 128. After a Completed Rebase the Next Rebase Is the Plain Form; Past a Diverged Fork Rebase Only the Owned Range

**Principle:** Family D (recover and land through the owning machinery against current state).

**Trigger:** a landing refused as stale-base while the merge lock is held, on a branch that may carry commits older than the current work.

**Rule:** two disciplines. First, once a branch has been rebased onto a base, the next refresh is the plain form (rebase onto the new tip); re-using an earlier onto-boundary after the branch moved replays the entire main line into conflicts. Second, when the branch forked long ago, inspect the range between the fork and the owned work: stray commits below the owned range stay behind (rebase with the owned base as the boundary), hunks in shared rolling logs resolve to the target side when the target already carries the re-witnessed line, and the landing retry runs immediately under the still-held lock because the base races peers; re-verify the certified digest after every replay.

**Why:** witnessed 2026-10-19 (playbook repo): an authoring branch forked before a main rewind carried era-stray commits that surfaced only as landing conflicts; the landing refused stale twice as peers landed through the window, a mis-boundary second rebase replayed the main line, and the plain form then landed all nine owned commits cleanly with the certified digest unchanged while the strays stayed behind for their own disposition.

## 129. Re-Derive Repository State at Each Acting Turn of a Session

**Principle:** Family A (state facts are re-derived from the repository at the point of action, never carried from conversation).

**Trigger:** an interactive session whose turns span idle gaps (hours to days), about to file a record or start work based on a prior turn's repository-state conclusions.

**Rule:** an earlier turn's repository-state observations (worktree and branch existence, run manifests, plan location, review-series contents) were true when made, not when reused. Peer sessions may complete, archive, or rebuild the work between turns. Before any write or plan step in a later turn depends on those claims, re-derive them with the turn's first probes: the worktree list, the branch table, the plans root, the review-series listing, and the freshness of any claim or manifest the work keys on.

**Why:** witnessed 2026-10-19 (playbook repo): a conversation resumed two days after its opening turns and filed a row directing work on run state read from the earlier turns; peers had meanwhile revived, executed, and archived the run and removed its worktree and branch, so the row was stale on arrival and was deleted the hour it landed (7249dbacc, deleted 517c4e4d7). The same resume found the plan's review series carried eleven rounds the earlier turns never saw. Re-witnessed 2026-10-20: a session relayed a two-day-old stand-down record's conclusion ("the exit is an operator machinery decision") to the operator as still owed; a peer landing had already made that decision and deleted the record's origin row, which one `ls` plus one `git log` on the origin path would have shown.

**See also:** #82 (precision values re-derived from disk at point of use), #124 (dated fields from the operation's own clock).

## 130. An Absence Signal Needs an Untruncated or Exact-Match Probe

**Principle:** Family A (the probe's verdict comes from the complete output, not a visible prefix of it).

**Trigger:** reading membership or containment listings (branch --contains, log --grep, directory globs) where the next decision keys on an expected entry's absence.

**Rule:** when absence of an expected entry is the signal, the probe is either untruncated or an exact targeted match (grep for the one expected value and check its result), never an enumeration piped through `head` or `tail` with the visible portion read as the whole answer; a truncation artifact and a true absence are indistinguishable in a shortened listing.

**Why:** witnessed 2026-10-19 (playbook repo): `git branch --contains <sha> | head -3` listed three authoring worktree branches and cut main from the output; the truncated listing was read as proof the landing was absent from main and that a peer had advanced the branch under review, and the false alarm stood until the probe was re-run untruncated.

**See also:** #38 (status and stderr masking: the same genus of a wrapper corrupting a probe's verdict).

## 131. A Claim Is a Heartbeat Its Owner Keeps; a Refresh Lapse Surrenders the Lane

**Principle:** Family H (verify the real thing, not the abstraction: the lane guard is the claim's current `updated:` line, not the session's belief that it still holds the lane).

**Trigger:** any run longer than one refresh cadence (phase boundaries hours apart, a quota wall, an operator pause) that holds an execution or authoring claim.

**Rule:** refresh the claim's `updated:` line at every phase boundary and immediately after any pause resumes, and treat its absence on return as a fact to re-derive, not a glitch to patch: before recreating it, check for a peer claim, a peer worktree, and the plan's state on the base branch (a sweeper may have read the stale claim as dead and a peer may have taken the lane); recreate only when no peer holds it, and record the gap. When a peer does hold it, touch none of its claim, branch, or worktree; hand unlanded findings over through a durable backlog row its review loop folds. The consumer rule (#77) corroborates liveness before sweeping; the owner's heartbeat is what makes that corroboration cheap, and a lapsed heartbeat is an invitation to be swept.

**Why:** witnessed 2026-10-20 (playbook repo): an interactive execution run took its claim at the start of a multi-hour session and never refreshed it across three task boundaries, a review loop, and a quota-wall pause; a peer's stale-sweep deleted the file mid-run. No peer took the plan (verified by claim, worktree, and base-branch probes before the claim was recreated for the landing window), but the lane ran unguarded for hours while a scheduled exec automation fired. Re-witnessed 2026-10-20 from the surrendered side: a scheduled exec run paused on a usage wall without refreshing; a live peer took the lane (claim rewritten, branch rebased, plan archived), and the run backed off, filing its blocking finding as a backlog row the peer folded.

**See also:** #77 (a claim file is not evidence of a live session: the consumer side of the same contract), #129 (re-derive repository state at each acting turn).

## 132. Committed Witness Lines Name Paths and Dates, Never Branch-Local Shas

**Principle:** Family D (single source of truth: a committed record cites identities that survive the landing, and a pre-landing commit sha is not one of them).

**Trigger:** writing a registry audit note, a lesson witness, a backlog row, or any other tracked text that cites the run's own commits while the run's branch has not yet landed.

**Rule:** a squash landing erases every pre-landing sha, so a committed witness that cites task-boundary or address-pass commits dangles on the base branch the moment it lands; name the artifact paths, the dates, and the record files instead, and keep shas in the gitignored run records (manifest, sidecars, receipts) where they are telemetry. Sweep the branch's tracked diff for seven-plus-hex sha literals before the landing call. The done skill's rule names only the landing digest; this is its general form.

**Why:** witnessed 2026-10-20 (playbook repo): a registry audit note cited three task commits and two address commits, and a lesson witness cited a boundary commit; a pre-landing rebase renumbered all of them and the squash would have left six dangling references on main. Caught by a pre-landing sweep and rewritten as paths and dates in one additive commit.

**See also:** #82 (ceremony-cited review records carry the full digest re-derived from disk: the digest a record MAY carry is the artifact's content hash, never a commit identity).
## 133. update-ref --stdin CASes One Ref with a Single update Line, Never verify Plus update

**Rule:** a `git update-ref --stdin` transaction that compare-and-swaps one ref expresses the swap as a single `update <ref> <new> <old>` line (the old-value check is built into the update); adding a `verify <ref> <old>` line for the same ref before the update makes git reject the whole transaction as multiple updates to that ref, so the composed CAS never lands. A detached-HEAD swap is the same single `update HEAD <new> <old>` preceded by `option no-deref`.

**Why:** witnessed 2026-10-20 (playbook repo, authorized-restoration landing in `scripts/done_run.sh`): the first composed transaction input paired `verify` and `update` on the same ref and git refused it; the landed form is the single `update` old-value check per ref, probed against attached and detached HEADs.

**See also:** #100 (ref-only landings), #123 (post-landing branch work rebases as a reset).

## 134. A Direct Commit's Pure-Reversal Hunk Is a Peer Clobber, Not an Edit

**Principle:** Family D (single source of truth: every staged hunk is attributable to the session's own edit; a hunk that only removes text a newer landing added is the stale-read clobber signature, whatever the landing path).

**Trigger:** committing by explicit path in a shared checkout (a learn, investigate, or backlog commit on the base branch) while peers land, when a staged path's hunk is pure deletion, is a pure addition of text you did not write, or the path is outside the commit's declared edit set.

**Rule:** lesson 6's run-scope diff check applies to direct commits as much as to squashes. Before `git commit`, word-diff each staged path against HEAD. A hunk that only removes text is foreign unless you deleted it on purpose; `git log -1 --format=%cd -- <path>` newer than your last read of that file proves it reverses a peer landing. Then re-read the file from HEAD, re-apply your edit, and never stage a path the commit's purpose does not name. A pure-addition hunk you did not write is the same signature in the resurrection direction (a peer's just-pruned span re-added by a stale-read write), so the path-age test runs on every staged path whatever its hunks' direction. When the path sits under a pinned surface (`agents/skills/maintenance/`), run the pins suite before committing; a red pin on the base branch stays red until some later run happens to execute the suite.

**Why:** witnessed 2026-10-19 (playbook repo): a learn commit (ce3a984b8) nine minutes after a peer landing (19866b067) staged `agents/skills/maintenance/survey-arms.md` with a pure deletion of the sentence that landing had added. The commit's subject named lessons and a backlog witness, not that file. The pins suite went red on main and stayed red for a day, until an unrelated ad-hoc run's suite reconciliation traced it with `git log -S` and restored the sentence byte-verbatim (a42e0e1d4). Re-witnessed the same day in the resurrection direction: an investigate entry commit (563d2e2e, 15:39) written from a read taken before a peer's direct commit seventeen seconds earlier (0c6a66f3f) had pruned a dispatch entry re-added that entry as a pure-addition hunk inside the commit's own declared rolling log; neither the pure-deletion signature nor the declared-path test fires on that shape, the path-age test does, and the resurrected entry stayed dispatchable for about twenty hours until the next monitor prune (93fff300b).

**See also:** #6 (the squash-landing form of the same signature), #129 (re-derive state at each acting turn), learn Step 1.8's own-edit staging check.

## 135. A Warning-Posture Gate's True Catch Must Be Ledgered or It Never Promotes

**Principle:** Family G (data-loss observability: a warning gate's firing is a record that real harm was detected; left in sweep stdout it is silently discarded from the only evidence stream that can promote the gate).

**Trigger:** a landing sweep prints `<gate> ... failed` under a warning-posture gate; or a consumer-side breakage (a skill missing from an agent runtime, a dropped artifact) turns out to have been named by a warning gate at an earlier landing.

**Rule:** treat a warning-posture gate's non-zero child as a catch, never as noise. (1) Fix the named file in the same run when it is yours. (2) Record the firing at finalize as `--guard-firing <gate>:catch:<evidence>:<note>` so the guard-liveness ledger carries it. (3) File the promotion row naming the harm the posture let through. A gate demoted for "no ledger catches" can re-earn blocking posture only through that ledger; a warning nobody reads is the same as no gate.

**Why:** witnessed 2026-10-20 (playbook repo): a 2026-10-19 wording edit grew the frontmatter description of `agents/skills/execute-plan/SKILL.md` from 988 to 1159 characters. The ZCode skill loader drops any skill whose description exceeds 1024 characters, so the skill vanished from that runtime until a user asked why. The sweep's description-length checker exits 1 naming the file (reproduced on the old bytes), but the gate rides in warning posture, so every landing in between went through with the firing unledgered. The gate had been built for this exact class after the same file crossed the cap on 2026-09-27, and the authoring rule already existed (`how-to-write-skills`, frontmatter requirements); the gap was the discarded catch.

**See also:** `coding_guidelines.md` #24 (drop-side observability), AGENTS.md Machinery admission protocol (promotion after a true catch), `docs/maintenance/demoted-sweep-arms.md`, backlog row `docs/history/backlog/2026-10-20-description-length-gate-true-catch-unledgered.md`.

## 136. A Shape Check Outlives the Convention It Encoded; Count the Compliant Population

**Principle:** Family H (verify the real thing: a validator pins a shape, and the shape is a proxy for a meaning that conventions can move away from without the check noticing).

**Trigger:** changing a corpus convention (what a served item looks like, when a token is written), or reading a validator's clean result as evidence that the meaning it was built for still holds.

**Rule:** when a convention changes, grep the validators that classify the old shape and re-baseline each default the change inverted; a fail-open default written for "unknown" becomes a permanent miss once the convention makes that case the common one. When a check can only test a shape (a prefix, a date, a presence), count the compliant population before trusting it: a confirmation token present on nearly every row is a drift signal, not health.

**Why:** witnessed twice 2026-10-20 (playbook repo). The prompt-log stale check (2026-10-01) classifies an absent origin that resolves nowhere as LIVE, a fail-open default for unknown moves; the covered-row rule (by 2026-10-13) made deletion the normal served shape, so a served entry sat dispatchable two days and a monitor sweep walked past it. The registry's `user-approved YYYY-MM-DD:` audit token means "the user confirmed this override" (ADR-0001); the validator checks only the prefix, and 579 of 659 completed rows carried the prefix on execution narration no user confirmed, while the five rows without it failed the moment they were parsed. Re-witnessed 2026-10-20 (seal census, playbook repo): the corrections gate's degrade-to-exact-match default, written for a certification predating the seal file, is the path most squash-landed plans take, because the squash orphans every resolvable seal's anchors; 7 of 37 seals anchored on main, and the two open plans refused that day were the two whose seals resolved (see #141).

**See also:** #130 (an absence signal needs an exact probe), #135 (a warning-posture catch must be ledgered), backlog row `docs/history/backlog/2026-10-20-served-origin-deletion-leaves-prompt-entries-live.md` (the token-drift sibling row landed covered; its writer-rule fix lives in the `doc-hierarchy` and `plans` skill text).

## 137. A Readiness Verdict Is the Oracle's Exit, Never a Reading of Its Inputs

**Principle:** Family H (verify the real thing: the certification oracle is `scripts/plan_readiness.py`; the seal file and the review sidecars are its inputs).

**Trigger:** an exec-mode selection deciding whether an open plan is dispatchable, or any report calling a plan "not ready" or "no ready verdict".

**Rule:** run the oracle once per open plan and branch on its outcome line; never infer readiness from the presence or absence of a `ready=yes` span in the seal file, whose entries are anchors and digests, not verdicts. A failing oracle names its failing leg: record that leg verbatim (a stale digest is needs-recert and stays dispatchable; an anchor-leg refusal over unchanged bytes is a filed gap, not a silent skip).

**Why:** witnessed 2026-10-20 (playbook repo): the 06:35 scheduled exec run skipped two certified plans as "certs carry no ready=yes verdict"; rerun, the oracle passed one outright and failed the other only on a squash-orphaned seal anchor over byte-identical bytes. Both were dispatchable within the run's unused mandate.

**See also:** the maintenance survey's Certification bullet (`agents/skills/maintenance/survey-arms.md`), #129 (re-derive state at each acting turn), #141 (the producer side: the landing ends when the oracle passes on the base), backlog row `docs/history/backlog/2026-10-07-corrections-graded-freshness-post-squash.md` (the anchor-leg gap).

## 138. A Skill Root's Authored Set Is Its Tracked Top-Level Directories

**Principle:** Family D (single source of truth: the repo-authored skill set is the tracked, one-level-deep tree under the skills root; a runtime cache nested beneath it is neither loaded by the runtime nor owned by the repo, so a checker that scans it reports on files nobody here authors).

**Trigger:** a skill tree under a discovery root holds a nested or gitignored subtree (a vendor sync cache, a runtime's own synced-skills directory); a sweep checker warns about a path under it; or a nested skill fails to appear in a runtime's skill list.

**Rule:** scope skill-tree checkers to the tracked set (`git ls-files` under the root, or depth one), never a bare recursive glob. Diagnose a missing skill by depth before frontmatter: the runtime discovers skills directly under each root, so a `SKILL.md` two levels down is not found however valid it is. Never hand-edit a nested externally managed cache to silence a checker; the next sync overwrites the edit.

**Why:** witnessed 2026-10-20 (playbook repo): the description-length checker (`rglob("SKILL.md")`) warned at every landing about two files under the gitignored `agents/skills/synced/` cache written by an external skills sync; neither appears in the runtime's loaded skill list, while all 47 top-level skills do.

**See also:** #135 (a warning nobody reads is no gate), AGENTS.md Vendored Asset Sync Rules (autonomously managed trees are never vendored or hand-edited), `how-to-write-skills` frontmatter requirements (the authoring cap).

## 139. The Removal Gate's Owned Set Seeds From Header Citations; Hand It the Records and Verify the Removal

**Principle:** Family H (verify the real thing: a passing removal gate is a verdict about record migration, not evidence that the worktree and branch are gone).

**Trigger:** running `scripts/worktree_closeout_migrate.py gate-removal` at an authoring or execution closeout whose plan file carries no `Plan review record:` or `Plan review:` header citation (the review records sit in the primary reviews home, but the plan names none of them), or reading the gate's pass as the end of teardown.

**Rule:** the gate seeds its owned set only from those header label lines plus `--claims`; with neither it refuses `empty owned set` by design, and the remedy is a claims file (one repo-relative record path per line, the plan's review records and sidecars) passed through `--claims`, never a header edit to the certified plan (that would stale the bound digest). After the pass, probe `git worktree list` and `git branch --list <branch>` before reporting teardown: the gate's pass may print the sanctioned removal step rather than perform it, and the printed step is the operator's to run.

**Why:** witnessed 2026-10-16 and again 2026-10-20 (playbook repo, scheduled authoring runs): both certified plans refused `empty owned set`, passed once a claims file named their records, and left the worktree and branch in place after the pass; teardown finished by hand. The printed-step behavior is an investigated origin (`docs/history/backlog/2026-10-11-ad-hoc-worktree-lifecycle-owner-gap.md`), so this lesson records the operating rule, not a fix.

**See also:** #61 (acquire the merge lock at the primary checkout), #104 (the archive gate's covered-row arm), the execute-plan skill's worktree-first module (`agents/skills/execute-plan/worktree-first.md`).

## 140. A Validation Pin Quotes the Prescribed Bytes, and an Absence Arm Carries a Positive Control

**Principle:** Family H (verify the real thing: a plan's validation command is an oracle over the task's own prescribed text and the witnessed failure's exact shape; a paraphrase of either tests nothing the executor will produce).

**Trigger:** authoring a plan's Validation Commands or acceptance criteria for a text edit or a matcher fix; a review round asks what the pin would catch, or whether a passing count could pass on unchanged bytes.

**Rule:** derive each pin from the phrase a task checkbox prescribes, byte-exact, one pin per prescribing checkbox; a vacuity or absence pin (`expect: 0`, "the file is unchanged") pairs with a positive control that fails on the pre-change bytes, or it proves nothing. When the fix targets a witnessed warning or error string, copy the string from the witness record, suffix included, and match the shape the real emitter produces (a leading-token match when the witness carried a trailing redirection, never the whole span), so the regression arm reproduces the witness rather than a tidied paraphrase. Authoring these first costs one pass; a panel that catches them costs a round per defect plus the digest re-bind each fold forces.

**Why:** witnessed 2026-10-20 (playbook repo, two authoring picks in one scheduled run): the first plan's pins paraphrased the prescribed sentences and its vacuity arm had no control, the second plan's regression arm matched a cleaned-up copy of the readiness warning while the witnessed line carried a redirection suffix only a leading-path-token match closes; the panels caught both, at six and five rounds. Plans: `docs/history/plans/2026-10-20-fold-verification-runs-committed-bytes.md`, `docs/history/plans/2026-10-20-readiness-files-coverage-quote-prefix.md`.

**See also:** #7 (re-derive a plan's edit inventory from live bytes), #130 (an absence signal needs an exact probe), the plans skill's validation authoring rules (`agents/skills/plans/validation-authoring-rules.md`).

## 141. Seal Anchors Die in the Squash: Re-Run the Oracle on the Base

**Principle:** Family D (single source of truth: a record field a gate resolves through git must name an identity that exists on the base branch after the landing; #132's run-record carve-out holds only while no verifier consumes the sha).

**Trigger:** closing a plan review round in an authoring worktree writes the seal's `round_start_commit` and `round_close_commit`; a rebase or squash landing follows; or a landing report declares the plan execution-ready without an oracle run on the landed base.

**Rule:** both history rewrites the workflow prescribes orphan the commits a seal names. The pre-landing rebase makes the validator refuse in-branch until the anchors move to the replayed tip; the squash landing removes every branch commit from the base's ancestry. So the landing is complete only when `scripts/plan_readiness.py <plan>` passes on the base branch. On an anchor-leg refusal over byte-identical bytes, re-anchor both commit fields to the landing commit, whose plan blob re-hashes to the sealed digest. Record the move in a `landing_note:` line and leave the gate alone. Expect the refusal when the seal is correct: a seal that resolves for the record's round is verified, while one that fails to resolve (short shas, a round mismatch) degrades to the exact-match rule and passes with a warning.

**Why:** witnessed 2026-10-20 (playbook repo): an authoring landing (`docs/history/plans/2026-10-20-usage-wall-probe-before-timed-resume.md`) reported complete with teardown done, and the oracle on main refused its lesson-#32-compliant seal on the anchor leg; the pre-landing rebase had already forced one in-branch re-anchor of the same fields. A seal census found 7 of 37 seals anchored on main; of twelve open plans, the two refused were the two whose seals resolved for their latest round, and the rest passed through the degradation warning or on re-anchored seals. The re-anchor passed the oracle without touching the bytes or the gate.

**See also:** #137 (the consumer side: an anchor-leg refusal over unchanged bytes is a filed gap, never a silent skip), #132 (committed witness lines never cite branch-local shas), #136 (a fail-open default for the unknown case becomes the common path), #32 (the machine-resolvable seal shape), backlog row `docs/history/backlog/2026-10-07-corrections-graded-freshness-post-squash.md` (fix of record: an unorphaning anchor leg or a landing-written `landed_as` witness).
## 142. A Fail-Closed State Reader Catches Decode Errors With I/O Errors

**Principle:** Family G (guard fail-closed: a verifier's contract is that every bad-input mode resolves to a named refusal, never an exception, so the catch tuple must cover the read's full raise surface, not the failure shapes its happy path suggests).

**Trigger:** wrapping a text-mode read of operator-editable or untrusted state (a state file, a witness record, a copied authorization) in a fail-closed refusal path, and writing the except tuple from the I/O failure shape alone.

**Rule:** derive the tuple from the call's full raise surface: reading bytes that are invalid in the expected encoding raises `UnicodeDecodeError`, a `ValueError` subclass that no `except OSError` catches, so a decode failure escapes the guard and crashes the verifier instead of producing the refusal the caller's gate matches on. Guard such reads with `except (OSError, ValueError)`, and pin the mode with a test that feeds undecodable bytes and asserts the named unreadable-state refusal comes back (no exception). A fail-closed verifier that crashes on malformed input is open, not closed.

**Why:** witnessed 2026-10-20 (playbook repo, corrections-chain Task 1 review): the corrections-record authorization loader (`scripts/corrections_record.py`) guarded its state read with `except OSError` only; undecodable state bytes crashed the verifier with `UnicodeDecodeError` instead of the unreadable-witness refusal. The fix widened the guard to `(OSError, ValueError)` and added an undecodable-bytes refusal test.

Re-witnessed 2026-10-20 (playbook repo, corrections-chain Task 3 review): the same module's writer drift-guard re-read still caught only `OSError` after the pre-read had been widened, so a decode failure at the re-read would have escaped the retry guard; the re-read now routes through the pre-read's exact `(OSError, ValueError)` leg, probe-witnessed by feeding undecodable bytes at the re-read and observing the named refusal. The read-site form of the rule: every read of the same protected file converts the same error set to the same named refusal; widen per file, not per incident.

**See also:** user-level UL#335 (the seam-parity facet: a test seam's broader except tuple enumerates the natural path's gap).

## 143. Serialize Mutation-Probe Workers Against Peer Review Workers Sharing One Worktree

**Principle:** Family D (single source of truth: a reviewer's reviewed-files-unchanged guard reads the shared tree as evidence, and a peer's sanctioned temporary mutation makes that evidence lie).

**Trigger:** an orchestration that runs several review workers concurrently against one worktree, when any worker validates tests by temporary mutation (mutate the code or a fixture, run the suite, revert).

**Rule:** a testing worker's temporary mutation probes are writes to the reviewed tree, so every other worker's unchanged-files check observes them and can raise a false external-writer alarm against the author under review. Either serialize the probe-mutating worker against peer workers, or have each worker pin before and after digests of the files it reviews and attribute a digest change to its own disclosed probes before raising the alarm. A probe-mutating worker must disclose its plan to the orchestrator up front so the serialization decision can be made before the round starts.

**Why:** witnessed 2026-10-20 (playbook repo, corrections-chain Task 1 review): a correctness worker's reviewed-files guard fired mid-round while a concurrent testing worker ran disclosed, fully reverted mutation probes; the tree re-verified byte-identical and the alarm was attributed to the probes. Without the disclosure the signal would have stood as an unexplained integrity failure.

**See also:** #64 (probe mechanics: never probe pin mutations with an in-place editor that leaves residue), #31 (a worktree's untracked run artifacts are the run's own estate to protect).

## 144. A Conditionally Refused Flag's Help States the Exact Trigger Condition

**Principle:** Family C (shared-artifact coordination: the flag's help text is the operator-facing contract and must co-evolve with the refusal condition the same change wires).

**Trigger:** rewiring a CLI flag or source selector so it refuses only when a specific state is in play (for example, when the chain declares an operator-acked row), while it stays legal and inert otherwise.

**Rule:** the help text states the exact condition under which the refusal fires and that the flag is inert otherwise; scope any "absent keeps the default" sentence to the behavior family where it holds, and check the drafted help against the same diff's new pass paths so it cannot contradict them. An unconditional-refusal claim over a conditional refusal reads as a broken flag, not a scoped one.

**Why:** witnessed 2026-10-20 (playbook repo, corrections-chain Task 2 review): the rewritten flag help claimed an unconditional refusal beside the plan-source selector, and its trailing default sentence contradicted the pass path the same diff added; three of the four review workers flagged the same over-claim, and the fix scoped the refusal sentence and family-scoped the default sentence.

**See also:** #142 (the fail-closed refusal family the help describes), #18 (a gate's refusal message as the authoritative enumeration).

## 145. A Deliberate Duplicate Is Pinned by a Same-Fixture Parity Test

**Principle:** Family D (single source of truth: a deliberately duplicated recipe is one contract in two copies; the parity pin is what makes the second copy a view of the first).

**Trigger:** adding or reviewing a helper copied between modules instead of imported (to preserve a dependency direction or keep a leaf dependency-free), and any later edit to either copy.

**Rule:** when duplication is deliberate, pin both copies with one parity test over the same fixture (a real end-to-end leg plus a synthetic-input leg where the contract has edge shapes); without the pin, drift between the copies is silent, because no import failure or suite asymmetry can surface it. Name the owning original in the copy's docstring so the pin's intent is discoverable.

**Why:** witnessed 2026-10-20 (playbook repo, corrections-chain Task 2 review): the staging validator grew its own copy of the primary-checkout resolver the done-sweep gates library owns (docstring names the owner; no import, preserving dependency direction); the review flagged the missing parity pin, and one same-fixture parity test (a real two-worktree leg, a fabricated porcelain-list leg) closed it.

**See also:** #143 (the same task's serialization rule for review workers sharing one worktree).

## 146. A Fail-Closed Refusal Names an Absent Input Absent, Not Only Unreadable

**Principle:** Family B (error-policy propagation: absent and unreadable are distinct unsuitability causes of a guard, and the refusal message routes the operator's first diagnosis).

**Trigger:** writing or widening a fail-closed refusal message for input that may simply not exist yet (a record never written) alongside genuinely corrupt or undecodable input.

**Rule:** the refusal distinguishes an absent input from an unreadable one, or names both worlds ("absent or unreadable"), so a never-recorded input does not read as corruption; widen the message rather than replace it, preserving the refusal tokens callers and tests match on.

**Why:** witnessed 2026-10-20 (playbook repo, corrections-chain Task 2 review): an absent state file refused with "is unreadable", reading as corruption rather than never-recorded; the message widened to "absent or unreadable" with the docstring and comment naming both, and every existing token assertion held unchanged.

**See also:** #142 (the catch tuple behind the same refusal).

## 147. A Precedence-Chain Fixture Clears the Full Source Set Before Pinning

**Principle:** Family A (equivalence-class coverage: a fixture's meaning is fixed by every input that participates in the decision it asserts, not only the member it pins).

**Trigger:** writing or reviewing a test fixture that sets one environment source of a multi-source precedence chain (session identity, config resolution, credential selection) while the other sources are left inherited from the ambient shell.

**Rule:** the fixture deletes every higher-precedence source in the chain before pinning the members the assertion is about (save for restore, clear the full set, pin, assert). An inherited source is an unpinned class: the assertion's meaning then depends on the ambient environment, and agent shells carry session-identity variables ambiently, so a pin-only fixture false-reds a correct implementation exactly in the deployment environment the code targets.

**Why:** witnessed 2026-10-20 (playbook repo, corrections-chain Task 3 fold): a classifier stimuli arm set only the lowest-precedence session source and passed in a clean shell, but failed as `ambient decoy value != expected derived value` under an ambient higher-precedence variable; the red was reproduced first, then the arm cleared all four sources and verified green under all three ambient decoys.

**See also:** user-level UL#200 (env control inside a fixture suite: a requested fixture runs after a same-scope autouse fixture).

## 148. A Stated Shape Contract Binds the Scan Down to the Type Level

**Principle:** Family G (guard fail-closed: a scan's stated contract, malformed state resolves to a named refusal and never to a silent non-match, binds its shape enumeration; a skipped deviation is the silent twin of #142's escaping exception).

**Trigger:** writing or reviewing a validator that iterates an array or map whose members are expected to be objects, where the loop body's member access implies the type check and the enumeration stops at field-level shapes.

**Rule:** the shape enumeration includes the type-level deviation: a non-object member hits the named malformed refusal, never the filter. When a helper's docstring states the contract ("a shape-malformed entry is malformed state, never a silent non-match"), read the scan against the sentence clause by clause; a contract the code does not enforce is a live contradiction, and the fix enforces the scan rather than weakening the sentence.

**Why:** witnessed 2026-10-20 (playbook repo, corrections-chain Task 3 review): the row-digest shape gate skipped non-dict array members while its helper's stated intent covered every shape-malformed entry; the scan now refuses with the malformed-family leg ("an array member is not a JSON object") and the docstring names both refusal shapes.

**See also:** #142 (the exception-surface twin in the same family), #146 (the refusal wording the named leg reuses).

## 149. Check Paren Balance at an Insertion Point Before Adding a Clause

**Principle:** Family C (shared-artifact coordination: an enumeration's paren nesting is part of the operative contract, and an inserted clause inherits the structure at its insertion point, not the level its author intends).

**Trigger:** appending a clause or list item to an existing enumeration in operative prose (skill text, contract docs), where an earlier edit may have left a parenthetical unclosed.

**Rule:** before inserting, walk the target enumeration and verify paren (and bracket) balance up to the insertion line; a pre-existing unclosed parenthetical re-levels the inserted clause into a nested position and mis-attributes it to the wrong enumeration member. Verify end-of-line paren depth is zero at the insertion point, and close a pre-existing imbalance as its own minimal edit in the same change.

**Why:** witnessed 2026-10-20 (playbook repo, corrections-chain Task 3 review): a new write-mode clause landed inside a parenthetical an earlier change had left unclosed at HEAD, nesting the clause one level deep in the write-mode enumeration; one byte closed the imbalance and the clause moved to the enumeration's top level.

**See also:** #144 (the same family's co-evolution rule for a refusal's help text).

## 150. An Owed Offset Survives Only on a Tracked Path with an Owner

**Principle:** Family D (single source of truth: a disclosed obligation is authoritative where it is tracked; a run log's disclosure is a witness, never an owner).

**Trigger:** landing a change that grows skill text past its byte budget while the repo's offset discipline still runs at review time, and recording the owed offset in the implement log.

**Rule:** carry the owed byte offset onto a tracked surface a later run actually reads (a named later task's existing item in the same plan, or an open backlog row naming the file and the owed size). A disclosure that lives only in the run's log leaks when the log is archived, because nothing later reads it back; the tracked row, not the log line, is the record the pricing obligation consumes.

**Why:** witnessed 2026-10-20 (playbook repo, corrections-chain Task 3): a skill-file byte growth was priced at review time and carried explicitly onto the plan's existing later-task anti-growth item, updating the owed total in the same change; the carry, not the log disclosure, is what keeps the debt collectable.

Re-witnessed 2026-10-20 (playbook repo, corrections-chain Task 4): the carried debt was paid by exactly the route the rule predicts. The targeted later task read the owed total and landed it as deletions-only trims of superseded enumeration text (1978 bytes from the same file against the owed 1959), leaving the file net-negative for the plan; the tracked item was read back and collected, not rediscovered.

**See also:** the skill-text anti-growth rules in this repository's AGENTS.md (review-time pricing pending the byte-budget gate).

## 151. A Contract Edit Sweeps Its File's Disclaimers and Case-Space Inventories

**Principle:** Family D (single source of truth: a contract's same-file mirrors and case-space inventories are derived views; updating the source without the views leaves the file contradicting itself).

**Trigger:** rewriting a contract sentence or adding a case to its case space in a shared doc that also carries a single-homing disclaimer or an inventory enumerating that case space.

**Rule:** in the same change, sweep the file's sibling prose surfaces that scope against or enumerate the edited contract. A "does not restate it" disclaimer must carve out mirrored pinned sentences that legitimately restate part of the contract; every enumeration of the contract's case space gains the new case. The sweep crosses the file boundary when the enumeration lives on another file's owned surface (a helper's docstring, a README's pinned-idiom sentence): grep the repo for the contract's artifact names, not just the edited file. An unscoped disclaimer over-claims, a stale inventory under-claims, and both read as the file disagreeing with itself.

**Why:** witnessed 2026-10-20 (playbook repo, corrections-chain Task 4 review): the skill-gate README's "does not restate it" disclaimer was contradicted by its own pinned idiom sentence, and the lessons-recall README (the contract's designated owner) gained a new precedence source while its own per-session isolation inventory still stopped at the earlier cases. Two one-line folds closed both (the disclaimer scoped to the pinned sentence; the inventory gained the clause).

Re-witnessed 2026-10-21 (playbook repo, corrections-chain operator-ack r1 review): one same-file residue (an unscoped empty-state sentence below the all-source empty rule it defers to) and two cross-file ones (a helper docstring and a README pinned-idiom sentence, consumer inventories missing the derivation's new third consumer class); the cross-file pair was invisible to the then same-file sweep, which is the extension above (`docs/history/backlog/2026-10-21-corrections-contract-doc-residues.md`).

**See also:** #26 (the fold-time re-sweep of scope-declaring plan surfaces), #67 (the retirement-direction sweep over pin and fixture layers), #144 (executable-prose co-evolution for a refusal's help), #145 (the pinned mirror a disclaimer must carve out).

## 152. A Depth Fault Escapes a Decode-Widened Catch Tuple

**Principle:** Family G (guard fail-closed: the raise-surface derivation behind the catch tuple continues past the decode leg; a parser's raise set over unbounded input outruns any named enumeration).

**Trigger:** wrapping a JSON parse of operator-editable or machine-written input in a tuple widened for decode errors, and leaving a same-guard dump or re-serialization outside the guard.

**Rule:** input nested past the interpreter recursion limit raises `RecursionError` from the parser, and `json.dumps` raises it the same way; neither is an `OSError` or a `ValueError`, so a decode-widened tuple still leaks a bare traceback where the named refusal belongs. Add `RecursionError` to the tuple, bring the dump inside a guard, and pin the leg with a deeply nested fixture.

**Why:** witnessed 2026-10-21 (playbook repo, corrections-chain operator-ack r1 review): all three state-read sites of `scripts/corrections_record.py` correctly carried the `(OSError, ValueError)` widening and still escaped. A risk-lens probe of scheduler-state JSON nested to extreme depth raised uncaught `RecursionError` at each, with the writer's re-serialization outside any try. Fail-closed in direction (a crash grants no authority; the input is unreachable from sanctioned writers); the fix, tuple widening plus a dumps guard, is tracked in `docs/history/backlog/2026-10-21-corrections-chain-recursion-refusal-and-pins.md`.

**See also:** #142 (the raise-surface derivation this extends), #148 (the type-level twin in the same family), #146 (the refusal wording the leaked traceback replaces).

## 153. A Shared Kind's Definition Scopes Its Route Requirements Per Family

**Principle:** Family C (shared-artifact coordination: a multi-family kind's definition is the operator-facing contract and must co-evolve with the per-family routing the executable wires; one family's route requirements stated as the kind's requirements strand the sibling route).

**Trigger:** adding a family to a shared kind or mode whose executable resolves each family through a different route (a primary state resolution for one, a turn record or witness flag for the other), and writing the definition paragraph with the new family's requirements stated family-blind.

**Rule:** a definition paragraph over a multi-family kind scopes each requirement to the family whose route carries it, or enumerates every family's route and defers each to its owning contract; when a family is added, re-read the definition against the executable's per-family branches so a requirement only the new family's route holds is not left reading as the kind's requirement. A family-blind definition makes the sibling route undiscoverable: following the text for the sibling family walks into a fail-closed refusal the text never mentions.

**Why:** witnessed 2026-10-21 (playbook repo, corrections-chain operator-ack r1 review): the `operator-acked` row kind's definition in the review-staging contract gained the plan family's state-route requirements (a fixed state selector, a nonempty author session, primary-state resolution) stated family-blind, while the verifier routes only plan-family acked rows to the state route and keeps the code family's turn-record resolution, so following the text for a code-family row walks into a fail-closed refusal with the route undiscoverable, even though the executable gates stayed self-consistent. The family-scoping fix is tracked in `docs/history/backlog/2026-10-21-corrections-contract-doc-residues.md`.

**See also:** #144 (the same family's conditional-refusal help rule), #151 (the sibling-surface sweep this complements), #146 (the refusal wording a stranded route ends in).

## 154. A Refusal's Remedy Points at the Surface the Flagged Defect Lives On

**Principle:** Family B (error-policy propagation: the remedy line routes the operator's first repair the way the refusal wording routes the first diagnosis; a remedy naming one canonical surface strands the class members whose defect lives elsewhere).

**Trigger:** writing or widening a gate refusal's remedy text for a refusal class whose flagged items can live on more than one input surface, or aggregating several refusal classes behind one shared remedy arm.

**Rule:** the remedy directs the repair to the surface where the flagged defect actually lives, derived per flagged instance; a class-aggregate arm prints each refusal class its own remedy rather than one shared line, and a remedy that cannot close the class it prints for (a migrate re-run for a citation refusal) is never printed for that class.

**Why:** witnessed 2026-10-21 (playbook repo, plan gate-removal-closeout-accounting Task 1 and its review): the closeout gate's aggregate refusal arm printed the migrate remedy for every class, including citation refusals no migrate run can satisfy; the class split fixed that, and the review then caught the new citation remedy naming the plan header for claims-file refusals - the fold directs the repair to the surface where the citation lives.

**See also:** #139 (which artifact closes the empty-owned-set refusal), #144 (the help text a conditional refusal co-evolves), #146 (the refusal wording routing the first diagnosis), #71 (identify the pinned invocation before repairing).

## 155. An Agreement Test Pins the Cross-Reference, Not Only the Shared Vocabulary

**Principle:** Family D (single source of truth: a consumer surface's restatement of a canonical rule is bound to it by the reference, not by the vocabulary; a vocabulary-only pin passes on an unbound restatement that then drifts into an independent rule).

**Trigger:** writing or reviewing a text-contract test that asserts a producer doc and a consumer doc agree on a canonical rule (skill text, contract docs), or folding a review finding into one.

**Rule:** the agreement test asserts the cross-reference itself - the consumer-side phrase tying the surface to the canonical definition, byte-exact per #140 - alongside the shared vocabulary and operand shapes. Vocabulary presence holds whether or not the binding pointer exists, so a vocabulary-only agreement test cannot catch a consumer silently becoming an independent statement of the rule.

**Why:** witnessed 2026-10-21 (playbook repo, plan gate-removal-closeout-accounting Task 1 review): the skill-text agreement class pinned the producer's canonical rule arms and the consumer's prescribed invocation operand shape, and both held while nothing bound the consumer text to the producer's rule; the fold asserted the consumer-side cross-reference phrase, making the binding itself the pinned contract.

**See also:** #140 (the byte-exact quoting the phrase assertion inherits), #145 (the parity pin for deliberately duplicated logic - a distinct shape from a referenced restatement), #151 (the edit-time sweep over sibling surfaces that restate a contract).

## 156. A Log's Test Counts and RED Inventories Are Counted, Not Recalled

**Principle:** Family H (verify the real thing: a boundary log's numeric claims are themselves checkable claims, and the check runs against the suite and the run output, not the writer's recall).

**Trigger:** writing a boundary or implement log's test-identity summary (how many tests a new class holds, which failures a RED run printed), especially while the run's details are still in memory.

**Rule:** derive each reported count by counting the named source at write time (the test class's methods, the run output's failure list), and let a RED inventory enumerate every failure the run printed - never a hand-picked subset. A reconciling summary total can carry a miscounted composition: omitted rows and inflated counts cancel, and only a per-source recount exposes it.

**Why:** witnessed 2026-10-21 (playbook repo, plan gate-removal-closeout-accounting Task 1): the implement log reported the two new classes one member high each (12/15 against actual 11/14) and its RED inventory omitted two printed gate-side failures, while the summary totals reconciled; the parent's testing-review correction caught both, and nothing in the log's own arithmetic flagged them.

**See also:** #105 (count each class per member on disk - the inventory sibling), user-level UL#337 (record the first actually-failing gate the executed block shows - the authoring-time anchor sibling).

## 157. A Mode Created to Adjudicate One Thing Cannot Pass on a Skip

**Principle:** Family B (fail closed where the surface owns the decision: an outcome verdict is machine-readable authorization, and a skip that leaves the mode's only question unanswered is a refusal, not a pass).

**Trigger:** adding or reviewing an epilogue that maps internal skip/early-return shapes onto an OUTCOME line, in a mode (or flag combination) whose sole purpose is producing that verdict.

**Rule:** in a mode whose only authority is the verdict it prints, a missing disposition (any skip shape) maps to fail with the skip reason echoed; the worktree-mode skip-then-pass stays defensible only where an independent gate owns the underlying decision. Enumerate every reachable skip shape and give the fail arm a probe, not just the pass arm.

**Why:** witnessed 2026-10-21 (playbook repo, plan gate-removal-closeout-accounting Task 2 review): the branch-only gate failed only on an explicit retained status, so a missing manifest, a manifest with no branch record, an unresolved branch, or a non-git target all fell through to OUTCOME: pass, exit 0, with zero branch accounting; OUTCOME: pass is what the done operator sequence keys on, and the probe proved each shape live.

**See also:** #154 (the refusal names the surface the defect lives on - the skip line the fail arm echoes), #131 (fail-open report shapes).

## 158. A Doc That Names a Command Names the Executable Form

**Principle:** Family D (single source of truth: prose that restates a command the code prints is a consumer restatement, bound to the executable form, not to an idealized one).

**Trigger:** writing or reviewing operator documentation that paraphrases a command a script prints or runs.

**Rule:** settle the documented form by running the surrounding procedure, not by what the procedure should require: a live probe showed plain `git worktree remove` refuses on any untracked file while the gate does not promise a porcelain-clean tree, so the documented command is the forced form plus its verification precondition, verbatim with the script's printed line.

**Why:** witnessed 2026-10-21 (playbook repo, plan gate-removal-closeout-accounting Task 2 review): done SKILL.md step 5 said "without force, using the sanctioned command the pass printed" while the pass printed `git worktree remove --force`; the operator following the doc verbatim hits exit 128 on the first untracked file.

**See also:** #155 (the agreement pin that holds such a restatement to the canonical form), #149 (doc/code drift as a review finding class).

## 159. Fixture Git Runs Under a Pinned Identity, Home, and Clock

**Principle:** Family H (verify the real thing: a fixture's git subprocesses are part of the host environment surface, and inherited environment is uncontrolled input).

**Trigger:** writing or extending test fixtures that create git repositories or launch the CLI under test.

**Rule:** every git and CLI subprocess a fixture launches takes one shared hermetic env: inherited `GIT_*` cleared, HOME pointed at a fixture-local directory, locale and timezone pinned (LC_ALL/LANG=C, TZ=UTC). A helper that only pins the lock variables still leaks host git config and clock zone into every child it spawns.

**Why:** witnessed 2026-10-21 (playbook repo, plan gate-removal-closeout-accounting Task 2): the lock-env helper pinned lock roots but copied the full host environment, so commit dates, message rendering, and identity in fixtures depended on the host's git config and timezone; the fix routed every subprocess through one `_hermetic_git_env` helper.

**See also:** #105 (count the source, not the recall - the same derivation-over-recall discipline for fixture claims).

## 160. The Claim Gateway Is Atomic: Never Pre-Create the Run Worktree

**Principle:** Family A (sequence discipline: a gateway that bundles two steps refuses when one step's effect already exists, so the bundling is the interface, not an optimization).

**Trigger:** starting an execute-plan run: creating the ad-hoc worktree manually before (or instead of) the execution-claim `take` call.

**Rule:** obtain the run worktree only through the claim gateway's `take` mode (claim create-or-refuse immediately followed by worktree creation); never `git worktree add` the run branch by hand first. A pre-existing worktree on the branch makes `take` refuse with `branch ... is held by an existing worktree` and rolls back its own fresh claim; the remedy is to remove the manual worktree and branch, then re-run `take` so it creates both atomically.

**Why:** witnessed 2026-10-21 (playbook repo, certification-seal-landing-survival execution, Phase 0): the orchestrator created the worktree, copied facts, then called `take`, which refused on the branch the call's own worktree half had just claimed and deleted its fresh claim; the retry after removing the manual worktree and branch passed on the first attempt.

**See also:** #43 (shell cwd resets between calls; the same re-derive-from-disk discipline at each step boundary).

## 161. stdlib Exclusion in Import Probes Needs a Directory-Provenance Leg

**Principle:** Family H (verify the real thing, not the abstraction: the real stdlib is the running interpreter's stdlib directory, not a declared module-name set).

**Trigger:** writing or reviewing any tool that classifies imported modules as stdlib versus third-party to gate a probe, allowlist, or scan: import probes, dependency audits, module enumeration, import-linter configuration.

**Rule:** treat a module as stdlib only when at least one of three legs holds: the name is in `sys.stdlib_module_names`, the name is in `sys.builtin_module_names`, or the module's `__file__` resolves under `dirname(realpath(os.__file__))` of the running interpreter. Never ship the name-set legs alone: distribution builds of CPython ship real stdlib-directory modules that `sys.stdlib_module_names` omits. Before trusting a green probe, preview it on every interpreter the tool will run under, in a clean environment, not only the authoring virtualenv.

**Why:** witnessed 2026-10-21 (playbook repo): the new deployment verifier's import probe (`scripts/verify_runtime_deployment.py`) keyed its provenance assertion on the name-set legs alone. Under Homebrew CPython 3.15, `unittest` imports `_missing_stdlib_info`, a genuine stdlib-directory module absent from `sys.stdlib_module_names`, so a clean home produced 10 probe failures; adding the directory-provenance leg probed all 55 real manifest entries clean under both 3.14 and 3.15 (verified empirically on both interpreters before implementation). The gap is environment-silent: it never reproduces in the authoring virtualenv, only on machines with that distribution.

**See also:** backlog row `docs/history/backlog/2026-10-21-runtime-verifier-naming-and-remedy-gaps.md` (the verifier's open review findings); backlog row `docs/history/backlog/2026-10-21-learn-captures-shared-corpus-promotion.md` (landing the Python-ecosystem restatement in `python_guidelines.md`).

## 162. Grade a Review's Pin Claims With a Mutation Matrix

**Principle:** Family H (credit comes from a killed mutation, not from reasoning that a pin would kill one).

**Trigger:** reviewing a diff whose tests pin behavior; the reviewer can name several "most likely wrong implementations" but has only read the pins, not run them.

**Rule:** turn each hypothesized wrong implementation into a planted mutant: copy the implementation to a scratch location, apply one wrong implementation, re-run the targeted tests, record caught or passed, restore. A caught mutant is evidence the pin holds; a passing mutant is a real pin-gap finding to file, never an argument to have. Report the tally (caught/total) in the review record so the pin set's strength is measured, and let the passing mutants, not the reviewer's confidence, name the gaps.

**Why:** witnessed 2026-10-21 (playbook repo, execute-plan Task 2 review): the panel planted five wrong implementations against the new deployment-verification suite; four flipped a test, and one (removing the probe child's `-S` hardening flag) passed the whole suite, naming an unpinned flag that reading had scored as pinned. The matrix converted five hypotheses into 4 verified catches plus 1 filed gap.

**See also:** #64 (run each mutate-assert-restore cycle from a pristine capture, never an in-place backup), #140 (a validation pin quotes the prescribed bytes, and an absence arm carries a positive control), User-level lesson UL#330 (the fixture-authoring sibling: one mutation-killing witness per guard conjunct), backlog row `docs/history/backlog/2026-10-21-runtime-deployer-test-pin-gaps.md` (the filed gap this matrix found).

## 163. Re-Pin Every Certified Code-Family Home After a Tip Move

**Principle:** Family D (single source of truth: the certified range is one fact recorded in four homes, and a tip move invalidates all four together).

**Trigger:** a clean code-family review round has been certified (seal block, sidecar, record, plans-egress backfill record) and the branch tip then moves: a bookkeeping boundary commit (the residual row the round itself backlogs), a pre-landing rebase onto an advanced base, or a merge-base change that alters the branch delta.

**Rule:** treat the four homes as one record keyed on `reviewed_base...reviewed_head`: after any tip move, recompute the delta digest at the new merge-base, rewrite the seal block's anchors and range, the sidecar's `certified_range` and `source_digest`, the record's Round and Source digest lines, and the backfill record's range and digest, then re-run the staging validator through the code-source context before the lock. A home left at the old tip refuses later with `the round-start bytes do not re-hash` or `is not an ancestor of HEAD`, and the plan-family landed-anchor recovery does not apply to the code family.

**Why:** witnessed 2026-10-21 (playbook repo, certification-seal-landing-survival execution): r2 was certified at the fold tip, then the residual-row append, the rebase onto the advanced main, and the base re-pin each required a hand re-pin of all four homes (three re-pins, each re-validated green). The Step 3.4 sentence already calls backlog rows bookkeeping outside the digest, while the code-family digest hashes the whole branch diff; that seam is the open row `docs/history/backlog/2026-10-21-code-family-certification-stale-after-tip-moves.md`.

**See also:** #65 (the validator is the contract over the recipe); #123 (post-landing rebase semantics); #128 (rebase range after a completed rebase).

## 164. Quote a Closed Vocabulary From Its Validator at Every Producer Surface

**Principle:** Family D (single source of truth: a validator's closed enum owns the field's vocabulary; a producer-facing surface that mandates the field without quoting the owner's values invents a scale that refuses at validation time).

**Trigger:** assembling worker prompts, shared catalogs, or sidecar instructions for a pipeline whose downstream validator enforces closed vocabularies; or writing a catalog line that mandates a field by name without stating its allowed values.

**Rule:** before dispatch, extract each closed set from its validator and paste it verbatim into every producer-facing surface that mandates the field. Parent-side mapping of a near-miss value onto the closed enum at synthesis is recovery, not prevention: it costs a refused record and a revalidation pass every time the invented scale diverges.

**Why:** witnessed 2026-10-10 (playbook repo: three vocabularies refused across one authoring session's review rounds) and re-witnessed 2026-10-21 (plan-validation-command-undefined-repo review r1): the lens-worker return schema offered `verified|likely|speculative`, the staging validator's closed enum is `hypothesis|strong-evidence|verified`, and synthesis mapped the finding to `strong-evidence` before the re-run passed. The worker-facing catalog (`agents/skills/review-agents/severity-calibration.md`, "Required on every finding") mandates `confidence` without enumerating it, so every assembled prompt reinvents a scale.

**See also:** #146 (the refusal wording routes the diagnosis once it fires; quoting the enum keeps it from firing), backlog row `docs/history/backlog/2026-10-10-review-loop-dispatch-closed-vocabulary.md` (the adoption fix and the fourth-vocabulary witness), review-staging's closed-enums line (the doc-side statement this rule extends to the worker side).

## 165. Full-Mode Plan Readiness Stales on Progress Ticks; Run Pre-Round at Task Boundaries

**Principle:** Family B (ordering: a check that binds to byte identity runs after the last write that changes those bytes, never between writes).

**Trigger:** executing a certified plan whose Validation block or Done-when invokes full-mode `plan_readiness.py` while tasks remain; the first boundary's checkbox ticks have already changed the plan bytes the certification sidecar digests.

**Rule:** at task boundaries run only the `--pre-round` invocation (structural checks, review record not consulted); run the full-mode invocation once, at Phase 2, after the corrections chain's zero-round re-bind binds the certified record to the final ticked bytes. A full-mode exit 1 mid-run naming a stale sidecar digest is the boundary's own ticks, not a task defect: record it as a witnessed deferral naming Phase 2 on the boundary row and never edit the plan, the sidecar, or the validator to clear it; stash-prove the failure pre-exists the task's change before attributing it.

**Why:** witnessed 2026-10-21 (playbook repo, plan-validation-command-undefined-repo execution): Task 1's boundary commit ticked four checkboxes; Task 2's implement pass then inherited full-mode exit 1 on the r3 sidecar digest, stash-proved the failure present without its own change, and deferred the re-bind to Phase 2 instead of working around it, keeping the task's five gates green and the plan bytes untouched.

**See also:** the fold-side twin at the review-loop lesson on re-binding the closure certification's `source_digest` after a cap-round fold (the same digest-binding invariant at the review side), #43 (shell cwd resets between calls; re-derive at each boundary).
## 166. Transfer the Run Inputs In Before the Done Boundary Setup

**Principle:** Family B (ordering: a setup step that resolves project facts observes the transferred tree, so the transfer-in precedes it).

**Trigger:** entering a fresh ad-hoc worktree for a run that will commit through the done boundary.

**Rule:** run the Worktree-first transfer-in (the facts file and the reviews home) before `done_run.sh setup`, even though the boundary setup is the first edit-time action: the setup's run-manifest writer resolves the facts keys and refuses without them, and a refused attempt leaves the done lock held by the now-dead shell. A transferred-in reviews home also needs the setup's staging classification before the manifest write: enumerate unclaimed candidates with the sweep-gates lib's `--emit-foreign-candidates` invocation and re-run setup with `--foreign-review-from`. Release an abandoned hold only with the original token from the failed setup's own stdout, after corroborating the lock's meta.env repo_root against the checkout - never by stealing it from a fresh acquire path.

**Why:** witnessed 2026-10-21 (playbook repo, authoring-worktree-landing-shape execution): two setup attempts refused in one run (facts config error, then claim-or-foreign over 3264 transferred staging docs), each stranding its lock until the original-token release.

**See also:** #81 (the boundary setup precedes every owned edit; the transfer-in is not an edit and precedes the setup), #104 (archive origin rows covered, never rm).

## 167. Mirror Untracked Run Records Out of a Worktree Before the Closeout Stages Run

**Principle:** Family D (state-first: the only copy of a gate-required run
record must never live in a directory whose contents the closeout stages
rewrite, and a record-bearing claim about a deletion names its producer).

**Trigger:** a done-run closeout executes from an execution worktree whose
reviews home still holds untracked records (review records, exec backfills,
seal witnesses) not yet copied to the primary checkout's home, or a
mid-run gate reports a previously present record missing.

**Rule:** before the closeout stages run, copy every untracked record from
the worktree's homes to the primary checkout's homes; and when a record is
nonetheless lost mid-run, recreate it from the run's session logs, re-mirror
it, and file the unknown producer as an open issue rather than naming a
mechanism the code does not show. The witness below initially misattributed
the deletion to the docs-branch sync's restore pass; reading the code before
writing the rule shows that pass is create-only (`O_EXCL`, skips existing)
and neither the sync nor the done commit stage carries an untracked-file
deletion leg, so the producer is unattributed and under investigation.

**Why:** witnessed 2026-10-21 (playbook repo, scheduled execution run): a
gate-required exec backfill record vanished from the worktree reviews home
after the commit stage's docs-branch sync pass, and the landing gate flagged
it missing; the record was recreated from session state and re-mirrored, but
the run's closeout record blamed the sync pass, an attribution the
archaeology (2026-10-22, learn capture) could not confirm - the lesson text
was rewritten from the misattributed to the open-attribution form rather
than letting a wrong mechanism stand in the corpus.

**See also:** #31 (worktree recreation is not recovery for untracked run
artifacts - a witnessed deletion class with a known producer), #166
(transfer the run inputs in before the done boundary setup - the inbound
half of the same reviews-home discipline), the backlog row
`docs/history/backlog/2026-10-22-done-docs-restore-untracked-record-loss.md`
(the open producer investigation this rule's second arm files).

## 168. An Absence Probe Pins the Token Boundary, Not a Bare Substring

**Principle:** Family H (verify the real thing: the probe's pattern must match the shape of the token the claim is about, not a substring that longer sibling tokens share).

**Trigger:** verifying an absence claim (a record-name shape, a flag, an identifier) with grep before writing it into a durable record, where the searched stem is also a prefix of a longer common sibling.

**Rule:** anchor the pattern to the characters that distinguish the token from its longer siblings (a digit or delimiter class after the stem) and run the same pinned pattern against both the working tree and the tip; a bare-substring hit is not presence of the claimed token until the matched lines are read and reconciled against the claim.

**Why:** witnessed 2026-10-21 (playbook repo): an exec-r record-absence check over the execute-plan skill nearly recorded "the skill mentions the shape" because `grep exec-r` matched the "exec-review" receipt paragraph; the pinned form `exec-r[0-9<]` returned no match at the working tree and the tip, which the two-command re-derivation needed for the entry write.

**See also:** #27 (absence findings name their byte source; re-grep at the current tip), #130 (an absence signal needs an untruncated or exact-match probe).

## 169. A Backlog-Row Citation in Durable Text Rots at the Covering Landing

**Principle:** Family D (single source of truth: once a covering landing deletes its row, the row's durable fact lives in the landing commit's receipt line, not in a path that no longer exists).

**Trigger:** writing or reusing a rejected-alternative, cluster, or witness citation that names a `docs/history/backlog/*.md` path, especially one copied from an older entry's citation line.

**Rule:** re-derive every backlog-row citation from disk (existence probe plus `git cat-file` at the tip) immediately before reuse; when the covering landing deletes the row (the covered-row rule; ad-hoc landings print `EXEC-PROMPTS-PRUNE` receipts), cite the covering landing commit or the `completed/` twin instead of the row path; the entry checker accepts a `.md` span without resolving it, so the author owns the resolution.

**Why:** witnessed 2026-10-21 (playbook repo): a live EXEC-PROMPTS entry's rejected-alternative still cites a row its own ad-hoc landing deleted the day it landed (6b7c41018); the next entry's draft nearly copied that citation and the existence probe caught it before the write.

**See also:** #69 (derive downstream match patterns from on-disk names, not citation prose), #130 (an absence signal needs an untruncated or exact-match probe).

## 170. Multi-Path Commands Take Separate Arguments; Options Precede the `--` Separator

**Principle:** Family D (the consumer's grammar is the invocation spec: git treats everything after `--` as a pathspec and each argument as exactly one path).

**Trigger:** composing hygiene scans, add, or commit commands over a list of paths held in a shell variable.

**Rule:** pass each path as its own argument (individual variables or an array expansion); one quoted space-joined scalar collapses into a single pathspec and fails with "did not match any files", and an option placed after `--` (including `-m`) is read as a pathspec too. Either failure prints a pathspec error, so stop and rebuild the invocation rather than quoting the list harder.

**Why:** witnessed 2026-10-21 (playbook repo): one investigate Stage 0 commit failed twice in a single invocation, first from a hygiene scan handed one quoted path-list scalar (`OUTCOME: tool_error`) and then from the commit's `-m` sitting after the `--` separator; the commit landed only with per-path arguments and the message before `--`.

**See also:** #8 (the inverse contract: a single-string space-split tool option as one quoted argument), #43 (a per-call shell resets cwd to the primary checkout).

## 171. A Log-Audit Base Is the True Merge-Base, Not a Remote Ref

**Principle:** Family D (derive audit inputs from ref state at run time; a remote-tracking ref is a cached claim, not evidence).

**Trigger:** running a history-audit script (a prune-audit, an origins check) with `--base` pointing at a remote-tracking ref.

**Rule:** compute the audit window's base with `git merge-base HEAD <remote>` (or the landing's recorded parent) in the same invocation. A remote-tracking ref can trail main, and auditing against it reports already-covered history as violations. A violation produced against a stale base is re-derived against the merge-base before it is believed, and a pass on a stale base is not a pass either.

**Why:** witnessed 2026-10-20 (playbook repo): a prune-audit with `--base origin/main` reported a REMOVED-WITHOUT-WITNESS for a commit main had already covered; the rerun against the true merge-base passed on the first invocation.

**See also:** #62 (the same script's flag vocabulary), #6 (the stale-base sibling for landing machinery).

## 172. A Gitignored Directory Can Hold Tracked Files; New Files There Need a Forced Add

**Principle:** Family D (state-first: ignore rules govern untracked candidates only; the tracked set is independent state).

**Trigger:** adding a new file under a gitignored path (for example a runtime state directory) whose sibling files are already tracked.

**Rule:** when `git add <path>` refuses with "the following paths are ignored", treat the refusal as information about the layout, not an obstacle: check that the directory already holds tracked content, and when the new file belongs in that tracked set, add it with `git add -f` deliberately. Afterwards confirm intent with `git ls-files -i -c --exclude-standard` (empty). Neither a silent plain-add drop nor a blanket force-add habit is acceptable.

**Why:** witnessed 2026-10-20 (playbook repo): adding a review-certification seal under `.ai-playbook/review-certs/` was refused because the directory is gitignored while its seal files are tracked; the forced add landed the seal.

**See also:** #43 (per-call shell resets), #171 (derive audit inputs from current state).
## 173. A Descriptor Field Is a Claim Until the Gate Loop Reads It

**Principle:** Family H (verify the real thing: a declarative spec's self-description is not behavior; consumption is proven at the read site, never inferred from a green battery or from the spec's own legend).

**Trigger:** consolidating procedural validation gates into a declarative descriptor (per-field specs, message-override slots, a gate-routing legend), or reviewing that consolidation.

**Rule:** trace every declared key to the gate loop that reads it, and prove each consumed override slot with a flip pin (mutate the override, watch the emitted message change, restore). A legend may name as descriptor-consumed only consumers that read the descriptor at call time; gates that keep procedural bodies are named as procedural owners. Consumption pins on the descriptor object are not consumption pins on its fields: a dead key passes every behavioral test because no test exercises it. A consolidation also keeps the consumed slots byte-identical to the procedural messages they replace.

**Why:** witnessed 2026-10-21 (playbook repo, plan review-staging-schema-scaffold-and-validation-reuse Task 1 review): the consolidated sidecar descriptor carried a `message` override key no gate loop read (the loop consumes `type_error`; moving the extensions override there restored the pinned refusal bytes exactly). The gate legend claimed classifier and current consumption that stayed procedural. Both fixes landed while the 718-check selftest battery stayed green, and a sibling finding recorded a declared `schema_version` type a mutation probe showed had zero effect.

**See also:** #143 (the mutation matrix: one killed mutant per claimed pin; the per-key flip pin aims that discipline at the descriptor itself), #140 (the byte-exact quoting the restored override satisfies), #30 (build schema-gated artifacts from the validator's own tooling, which the descriptor and its scaffold builder now are).

## 174. A Mode Guard Lives for One Entry Call, Not for the Process

**Principle:** Family H (verify the real thing: a module-global flag set by one CLI mode is process state, and every in-process reuse of the entry point, the embedded selftest first of all, inherits it unless the entry call scopes it).

**Trigger:** adding a module-level suppression or mode flag that an entry point's `finally` consults (telemetry, record writes, outcome lines), or writing the selftest witness that proves the flag's scope.

**Rule:** the entry function saves the flag at entry, resets it, and restores it in its own `finally` after the consulting decision, so the flag describes exactly one call. The witness captures its baseline before the first in-process call of the mode, never after a sibling check has already run it, and pins the positive control on both sides of the mode call (a validation call after the mode call still records). "The process exits right after" is not a scope argument once the selftest reuses `main()` in-process.

**Why:** witnessed 2026-10-21 (playbook repo, plan review-staging-schema-scaffold-and-validation-reuse Task 2 review): the scaffold mode's telemetry guard was raised in the dispatch and never cleared, so `--selftest`, which calls the scaffold in-process four times before its telemetry witness, silently stopped recording its own invocation row while the 747-check battery stayed green; the witness passed because it captured the already-raised guard as its "prior" value. Scoping the guard in `main()` and pinning the post-scaffold validation call restored the row.

**See also:** #173 (a declared slot is a claim until the read site proves it; here the restore pin's baseline was the unproven claim), #159 (fixture isolation of ambient state), #38 (observe the verdict directly, not the green battery).

## 175. Resolve an Append-Only Corpus Conflict by Regenerating, Then Census Every Resolution

**Principle:** Family H (verify the real thing: a conflict resolution that takes one side of a whole-file conflict in an append-only numbered corpus silently discards the other side's later entries; integrity is proven by a census after EVERY resolution, not just the first).

**Trigger:** rebasing a branch whose commits append to an append-only numbered corpus (numbered lessons, changelogs, registries) where every branch commit conflicts against the corpus file, or reaching for `git checkout --ours/--theirs` on such a file.

**Rule:** resolve the first corpus conflict by regenerating (take the upstream tip's corpus and re-append your entries under their re-derived numbers), and re-run the same regeneration discipline at every later commit's corpus conflict in the same rebase - a `--theirs` pick on a later commit takes that commit's whole stale file and silently clobbers everything the upstream added in between. After the rebase, census the corpus: heading numbers strictly increasing, no duplicates, count equals upstream's plus yours. A whole-file side pick is only safe when the file has no upstream-side delta since your fork.

**Why:** witnessed 2026-10-22 (playbook repo, execution landing): the first lessons conflict in a 12-commit rebase was resolved correctly (upstream corpus plus the branch's two lessons renumbered past upstream's max), but the second conflict at a later branch commit was resolved with `--theirs`, which took the branch's stale corpus (lessons to 159) and silently deleted upstream's lessons 160-172; the damage surfaced only because a heading census ran before landing, and the restore re-derived upstream's corpus verbatim and re-appended the branch's entries.

**See also:** #123 (the own-landed-squash conflict shape; distinct: there the remedy is a reset, here the branch's commits are genuinely new), #143 (one killed mutant per claimed pin; the census is the corpus's pin).

## 176. A Runtime-Attributed Capture Is Checkout-Sensitive and an Honest Empty Is Sanctioned

**Principle:** Family H (verify the real thing: a capture tool that attributes runtime store data by checkout context returns different results from different checkouts of the same repository, and an empty result is a modeled outcome, not a failure to retry).

**Trigger:** invoking a runtime-store capture or attribution CLI from an execution worktree whose records a staging pair needs, or seeing an empty capture where a sibling round captured fine.

**Rule:** generate the capture from the checkout context the store attributes (the primary checkout) and merge the JSON into the sidecar from a temp file; do not assume a same-repo worktree shares the attribution context. An empty capture (exit 0, no stdout) is the tool's sanctioned missing-data outcome - the sidecar legitimately omits the field ("missing stays missing"); retrying the identical invocation does not fill it, and a brand-new mint's window can be honestly empty until attributed turns reach the store.

**Why:** witnessed 2026-10-22 (playbook repo, execution run): the same capture invocation returned a full record from the primary checkout and zero bytes when run inside the execution worktree, and a freshly minted round identity captured empty twice before the run wrote the sidecar without the usage field per the tool's contract.

**See also:** #65 (the capture module's mint/capture contract and its sidecar field ownership), #60 (a dispatch text's coverage claim is not evidence about the disk).

## 177. An Authorization Decision Must Consume the Guard's Failure Signal, Not Print Beside Its Report

**Principle:** Family D (state-first: a decision line is evidence only when the signals it depends on flow into the decision, not merely into the same output).

**Trigger:** writing or reviewing a guard whose failure reasons are computed into a report, disposition, or finding list while the gated action's authorization line and exit code are produced by a separate code path.

**Rule:** an authorization decision (a removal command line, an action-allowed verdict, an exit code) must take the guard's failure signal as an input: compute the signal once, propagate it into the decision branch, and let a failed guard hold the action and fail the outcome. A guard whose evidence reaches only the printed report is inert; the gated action prints as authorized beside a report that names the failure.

**Why:** witnessed 2026-10-21 (playbook repo, plan gate-removal-closeout-accounting Phase 3 risk lens): worktree-mode gate-removal computed a retained disposition whose reasons carried failed guards (linked sibling worktree, missing migrated artifact, unreadable ref) yet still printed the `removal: git worktree remove --force` authorization line and ended `OUTCOME: pass`; fix 1af769c59 propagates a `removal_blocked` flag from the guard computation into the removal decision and the sweep verdict, so a failed guard holds the on-disk worktree and fails the outcome.

**See also:** #167 (a record-bearing deletion claim names its producer; the same report-vs-decision split hides the producer), #165 (a stale readiness digest certifies bytes no round produced - the sibling shape of evidence computed but not consumed).

## 178. A Pre-Existing Scan Failure at the Merge Base Reorders the Run Before Its Own Picks

**Principle:** Family B (ordering: a blocked gate is the run's highest-urgency item, ahead of the work the run was picked for).

**Trigger:** an ad-hoc or plan run whose required validation suite (pins, hygiene, readiness) fails at the run's own merge base, with the failing span owned by an already-queued item rather than by the run's delta.

**Rule:** when a landing-required suite fails at the merge base, re-derive from disk that the failure pre-exists the branch (run the suite at the base tip), then treat the failing span's reconciliation as the run's first landing: if its owner entry's timing gate has lifted, execute that entry inside the run, consuming one of the run's slots, before landing the picked work; never land around a red suite and never record the failure as the run's own defect. A suite failure that only the base shares is a queue-ordering fact, not a landing blocker for the span's fix.

**Why:** witnessed 2026-10-22 (playbook repo, exec-mode run, max 3): the pins suite failed at the merge base on a live-vs-archive backlog twin owned by an EXEC-PROMPTS dedupe entry whose freeze had just lifted; executing that entry as slot one unblocked both remaining landings, and the originally-planned third pick (medium urgency) dropped off instead.

**See also:** #99 (the landing runs through the landed helper), #34 (the landing helper's flag contracts), and the ad-hoc backlog arm's broken-span reconciliation clause (`agents/skills/maintenance/decisions.md`).
## 179. The Origins Consult Reads the Disposition-of-Migrated-Items Heading, Not Origins Dispositions

**Rule:** when a plan must document the disposition of a deleted backlog origin so `scripts/check_plan_origins_closed.py` passes at archive, write the section under the literal heading `## Disposition of migrated backlog items`; a `## Origins dispositions` heading does not satisfy the consult and the gate still refuses.

**Why:** witnessed 2026-10-22 (playbook repo): an execution deleted its covered backlog origin rows outright per a plan's no-archive-copy disposition; the archive-ceremony origins gate classified the deleted row as a missing straggler and refused. Adding the dispositions under the consult's canonical heading (used by six archived precedent plans) resolved it; the literal-heading variant returned False from the consult and still exited 1.

## 180. A Subagent Without Fan-Out Runs the Review Panel Inline and Records the Mechanism

**Rule:** when an execution runs inside a subagent whose runtime exposes no sub-agent fan-out, the doing-code-review panel runs as sequential fresh-adversarial lens passes over the same delta, and the review record's Metadata carries a Panel mechanism note naming the inline shape and the repo precedent; the run never fabricates worker rows, skips the review, or defers the panel to a later turn.

**Why:** witnessed 2026-10-22 (playbook repo, exec-mode max-3 run): all three ad-hoc landing records carry the same deviation ("panel executed inline; this runtime exposes no sub-agent fan-out"), each validated by the review-staging validator with verdict ready=yes zero blocking; the recorded mechanism is what keeps the records mutually consistent for a later audit.

**See also:** #178 (the same run family), `agents/skills/review-agents/review-panel-selection.md` (the focused-panel recording shape the note borrows).

## 181. A Stale cwd Turns Path Operations into Primary-Tree Edits

**Rule:** shell tool calls reset cwd to the primary checkout between calls, so every destructive or path-sensitive command (rm, mv, git checkout/restore, absolute-path redirects) must run inside the same call chain that cd's into the run worktree AND verifies `git rev-parse --show-toplevel` first; on a suspected stray write to the primary tree, `git status --porcelain` plus `git checkout -- <path>` recovers, and the run reports the near-miss even when no landing byte was affected.

**Why:** witnessed 2026-10-22 (playbook repo, pick 2 of the max-3 run): the execution subagent twice deleted the covered origin backlog row in the PRIMARY working tree from a stale cwd before landing; both restores succeeded pre-landing and no landed byte was affected, but each incident only surfaced because the subagent happened to re-check `git status`.

**See also:** #43 (re-enter the worktree in every command - this lesson extends it from working-directory hygiene to destructive-operation gating).


## 182. A Receipt Digest Cannot Sit Inside Its Own Preimage; Bind It at the Reviewed Head

**Rule:** when a landing commit must carry a receipt line containing a content digest (for example the ad-hoc arm's `Ad-hoc-panel-pass: <record path> <digest>`), the digest's preimage is the branch diff at the reviewed head, not the landing commit's own diff: the receipt line is a post-review rider that necessarily changes the bytes, so demanding the digest cover the final landed diff is an unsatisfiable fixed point. Derive and three-way-check the digest (receipt == staging record `Source digest` == re-derived) over the reviewed head's diff, verify the only post-digest delta is the receipt line itself, and route that rider bytes back through the panel as a fresh confirmation pass so no byte lands unreviewed.

**Why:** witnessed twice 2026-10-22 (playbook repo, exec-mode max-3 run): both worktree landings via `commit-tree` squash plus compare-and-swap `update-ref` hit the same shape - a digest computed over the landing diff can never appear inside that diff, so each run bound the digest at the reviewed head (payload bytes), documented the binding in the staging record, and re-entered the receipt insertion through a confirmation panel pass; both validators accepted the record and the three-way equality held at the recorded head.

**See also:** #99 (the hand-composed landing form this digest shape rides on), #112 (verify the index, not only the worktree, after restore-based reconciliation).

## 183. A Scripted Structural Edit Is Claimed Only After a Tree Check of the Exact Intended Delta

**Rule:** any script-driven multi-line edit (python `str.replace`, section splice by `str.index` anchors, heredoc splice) that a follow-up claim will narrate (a review fold, a landing, a receipt) must verify the edit landed as intended before the claim: assert the replacement count or compare before/after bytes, anchor `index` calls on strings proven unique in the file (an anchor that occurs earlier splices the wrong region and can duplicate whole blocks), and after any conflict resolution grep the file for leftover conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) before committing. A `replace` that matches nothing is a silent no-op in every scripting language; the fold claim then over-delivers versus the tree and only an independent re-read catches it.

**Why:** witnessed 2026-10-22 (playbook repo, ad-hoc landing review r2): a fold script's `str.replace` no-op'd on a one-word byte difference ("same stranding class" vs "same defect class") and its `s.index` end-anchor matched a receipt line occurring earlier in the file than the entry being removed, duplicating a 14-line receipt block while leaving the target entry unremoved; the review panel's re-derivation from disk caught both, and the same run later landed a stray conflict-marker line that a post-resolution grep would have caught pre-commit.

**See also:** #74 (treat a zero-count success as unverified until the consulted tree is confirmed - this lesson extends it from read probes to write claims); #69 (derive the match pattern from on-disk names, not citation prose - the read-side sibling).

## 184. An Unquoted `=` Word in zsh Expands and Aborts the Chain Before the Next Command

**Rule:** in zsh command chains, never emit a bare separator argument whose text begins with `=` (for example `echo ===` or `echo ==-done`): zsh performs `=word` filename expansion (the PATH-command form) on it, fails with `=word not found`, and exits the `&&`-chained call before the subsequent steps (an amend, a gate, a release) run. Use `printf '%s\n' '...'`, quote the argument, or pick a marker without a leading `=`.

**Why:** witnessed 2026-10-22 (playbook repo, ad-hoc landing): a landing chain used `echo ===` as a visual separator between the file fix and the `git commit --amend`, zsh aborted on the expansion, and the amend and all downstream gates silently did not run in that call; the next call then operated on a half-landed state.

**See also:** #181 (shell tool calls reset cwd between calls - the same class of chain-boundary assumption turning one call's failure into the next call's surprise).

## 185. A Re-Bind Round's Seal Binds round_close_commit to the Commit Where the Certified Bytes Landed

**Principle:** Family B (ordering and identity: a seal's close anchor is the commit whose tree carries the certified bytes, not whatever commit is HEAD when the seal is written).

**Trigger:** closing a Phase 2 progress-tick re-bind round (lesson 165) whose corrections chain terminates in a seal entry for a round certified before the plan's landing squashes moved the tip past the certified bytes.

**Rule:** set the re-bind seal's `round_close_commit` to the ancestor commit at which the certified round's bytes landed (the covering squash landing commit), never the current tip. The staging validator refuses the tip-bound shape ("hop commit dated before the seal entry's round-close commit") because every hop in the chain predates a tip anchor by construction. Derive the value from git history (the commit whose subject carries the covering landing), not from a predicted future sha.

**Why:** witnessed twice in one run (2026-10-22, playbook repo, exec-mode max-3 run, two plan executions): each Phase 2 re-bind round first drafted the seal with the then-current tip as `round_close_commit` and hit the same seal-integrity refusal; re-binding the close anchor to that plan's covering landing commit cleared both.

**See also:** #165 (the re-bind duty this seal closes), #182 (the digest-binding invariant the same records carry), #32 (the machine-resolvable seal shape).
