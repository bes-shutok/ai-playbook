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

Checkout-side sibling: this lesson owns peer safety at the ref move; live-checkout freshness after the move is owned by the post-landing reconciliation implementation and the stale-checkout discriminator in the Worktree-first standard (agents/skills/execute-plan/worktree-first.md). Witnessed 2026-10-24 (same repo, ad-hoc exec run): when the default branch moved mid-landing and the first squash rebuild rebased the DETACHED squash commit onto the new tip, tree-equality against the branch broke; the correct rebuild rebase is of the source branch itself (`checkout <branch> && rebase main`), and the squash is then recomposed from it - never rebase the detached squash.

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

Re-witnessed 2026-10-20 (playbook repo, execution run closeout): two code-review staging records drafted from memory were repaired against `validate_review_staging.py` one error class at a time (freshness Metadata lines, Record kind, usage mint pair, Panel and Counts grammar, per-finding sections with Pattern, the per-worker Low budget, lens-taxonomy coverage names, the producer-written sidecar the repair tool refuses to invent for non-zero findings) across roughly ten fix cycles; reading the validator's check families and fixture builders first would have been one draft. Re-witnessed 2026-10-22 (playbook repo, execute-plan Phase 3): the same one-error-class-at-a-time repair over an unstaged validator run (canonical headings, Metadata lines, a review-run-id rejected for non-hex shape until minted fresh, extension-nested self-heal block), resolved only after reading the validator's refusals as the schema of record. Re-witnessed 2026-10-25 (playbook repo, authoring run, plan-review r1 preflight): the same one-error-at-a-time repair over the record-selection staging pair (an admission-state vocabulary token, an exhaustion reason that must be exactly a retryable class token, a verdict enum limited to yes/no, a coverage key the pair rejects, plus local-fallback attempts counting toward coverage only with an existing artifact/sidecar pair on disk and a launched-worker count equal to the panel rows). Re-witnessed 2026-10-27 (playbook repo, ad-hoc exec run): two ad-hoc landing record pairs drafted and repaired against the validator's refusals (finding conservation demanding `#### F<N>` blocks for triaged-fixed findings too, the launched-worker count covering every confirm round's panel row, the mint pair bound across all rounds, and a BSD `date +%s%3N` printing a literal instead of epoch milliseconds until the milliseconds came from python). Re-witnessed 2026-10-28 (playbook repo, authoring run r2 certification preflight): a soften watchlist hand-drafted as Markdown bullets parsed as zero rows because the validator counts only pipe-delimited table rows, and a coverage-outcome value written outside the enum ('complete' for 'clean'); both cleared in one draft after reading the validator's check list.

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
immediately. Re-witnessed 2026-10-29 (playbook repo): a vacated-round
annotation appended inside an existing round block as prose made the parser
return None for the whole file, so every round's seal unresolved, and the
validator's degraded-grading warning read identically to a missing entry,
misdirecting the first repair toward appending the seal; annotations to an
existing block ride as extra `key: value` field lines. Third witness
2026-11-02 (playbook repo, an authoring closeout): the block shape was
correct but the commit fields carried a short 9-hex sha, and the entry again
read as unresolved (the same degraded-grading warning); rewriting the two
commit fields as full 40-char SHAs resolved the round with no other change,
so the resolvable-shape rule covers the field values too: record full
resolvable SHAs, never abbreviations.

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
can re-export, and never release a hold whose holder identity is not yours. 2026-11-01 re-witnesses (the 10:49 author carrier): the merge lock's exports were lost between tool calls mid-landing and re-exported from the acquire output (the recovery source working as designed), and the done-lock retry guessed the worktree's lock directory by listing the lock root and taking the first entry - which named a foreign run's hold; a lock directory is never derived by listing, only from the acquire echo or the hold's own meta.env.

**Principle:** Family D (a hold's own records are the single source for its
recovery; the env path and the metadata path must name the same token before
either is used).

**Why:** witnessed 2026-10-12 (playbook repo): a merge-lock release after a
multi-call landing window refused with the lost-exports error; the hold's
`meta.env` token matched the session's acquire output and the re-exported
release passed on the first retry.

Re-witnessed 2026-11-01 (exec run): the acquire output itself can be lost by
display filtering - a `tail -2` over `merge-wait-acquire` kept only the token
export, so the first `land-worktree` refused with `requires MERGE_LOCK_DIR
set`; the remedy was release-and-reacquire with the output captured whole to
a file. Capture an acquire's full output to a file, never tail-filter it:
every export line is load-bearing.

Re-witnessed 2026-11-01 (authoring run): the acquire exports were captured into plain shell variables in the same call but never exported, and the helper subprocess refused the identical `requires MERGE_LOCK_DIR set`; composing acquire and helper in one shell is necessary but not sufficient - the pair must be `export`ed (or prefixed on the helper invocation) so the child process inherits it.

Re-witnessed 2026-10-16 (playbook repo): the lock families also differ in
export names, so one shell is not enough by itself: the done lock's
`wait-acquire` prints the `DONE_LOCK_*` pair while the landing consumer
wants `MERGE_LOCK_*`; alias the pair in the same acquire shell
(`export MERGE_LOCK_DIR="$DONE_LOCK_DIR"
MERGE_LOCK_TOKEN="$DONE_LOCK_TOKEN"`) before `land-worktree`, and the
first landing attempt stops refusing with `requires MERGE_LOCK_DIR set`.

Re-witnessed 2026-10-29 (playbook repo, ad-hoc exec run): a post-landing
merge-lock release rebuilt its exports from the hold's `meta.env` and
refused twice before passing; the recovery translates names rather than
copying them, because `meta.env` stores bare field names (`lock_token=`)
while the release reads the prefixed `MERGE_LOCK_DIR`/`MERGE_LOCK_TOKEN`
exports. Build the recovery env by mapping each meta field to its export.
name, and reuse the acquire output's printed values where they survive
instead of re-deriving paths by glob.

Re-witnessed 2026-10-30 (playbook repo, execute-plan done closeout): a final
closeout's `finalize` refused with "done lock status is not free after the
release" while the lock root named a dead holder, and the from-holder release
arm refused in turn on its own gate (pin mismatch against the dead holder's
record). The sanctioned remedy stayed inside the lesson's rule: the stale
hold's own `meta.env` token was mapped onto the prefixed `DONE_LOCK_DIR`/
`DONE_LOCK_TOKEN` exports and passed to a direct `release-repo`, after which
status read free and `finalize` passed. A dead holder is the one case where
the direct release replaces the from-holder arm; confirm the holder is
actually dead (no live session owns the token) before reaching for it.

Second arm re-witnessed 2026-10-29 (playbook repo, the
primary-log-branch-drift-at-commit execution closeout): the same
stealable dead hold also yields to the plain `acquire` path itself (the
dead-holder grace reclaims it and prints fresh exports); releasing those
exports token-fenced and re-running `finalize` passed identically. Either
recovery arm works once the holder is verified dead; the acquire arm
avoids hand-mapping the meta fields.

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
caught, and the r15 sweep line repeated the shape. Re-witnessed 2026-10-29
(playbook repo): a closeout repaired the per-criterion caps but never re-ran
the gate, and the per-task aggregate breach stayed latent through three more
rounds, two of them blocking rounds that cannot reach the round-close gate,
until a certification panel measured it; the gate run belongs at every fold
commit (the pre-round invocation), not only before round one, because a fold
that edits criteria can create envelope debt the next close inherits.
Re-witnessed 2026-10-31 (playbook repo, an authoring closeout): an authored
plan accumulated em-dash policy violations that four review rounds never
flagged - the review lens catalogs own defect classes, not a repository's
text policy - and the em-dash added-lines gate refused at the closeout, after
certification, forcing a fix commit plus a fresh certification round. A
repository's mechanical text-policy gates (em-dash added-lines, public
hygiene, pins) belong in the same pre-round sweep over the authored bytes.
Re-witnessed 2026-11-02 (playbook repo, authoring run): the first review panel was launched before any pre-round gate run, and the panel spent three of its blocking findings on structural hard-refusals (classification tags, primary class anchors, off-taxonomy driving force) the pre-round gate refuses mechanically - a full-panel round spent on what one local gate invocation returns in seconds; the gate run now precedes every round launch.
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
Fourth witness 2026-10-24 (same repo, ad-hoc exec run): the pre-swap
parentage gate was piped through `tail -3` inside an `&&` chain, so the ref
update ran BEFORE the gate verdict; both gates were rerun immediately after
and the landing verified sound, but the composition was one refused gate
away from a clobber. Fifth witness 2026-11-01 (same repo, an authoring
run's freshened-base landing): a worktree rebase was piped through `tail`,
so a conflict stop reported the pipe tail's success and the chain read as
clean; the stop surfaced through the rebase output instead of the status
channel, and the union-of-intents resolution with post-resolution
re-verification preceded the landing.

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

Second witness 2026-11-01 (the same carrier's ad-hoc run): a validation
selftest composed without re-entry ran against the primary checkout and
reported every arm green - green because the primary still held the
pre-change script, not because the change passed. Validation commands are
writes-adjacent: the same re-entry and toplevel verification applies before
trusting any pass/fail verdict produced in a worktree phase.

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

**Why (second witness):** witnessed 2026-10-30 and 2026-11-01 (playbook repo): four ad-hoc landings deleted their learn-produced origin rows per the covered-row rule with no receipt on any surface (eebc930c0, c5c31e9d6, 830119aff, 66255a68d), and a ledger-section rewrite removed sixteen prior receipt lines in one commit (30fc2342b, plus two more at a5024b396); the consultative prune-audit holds twenty-three standing flags since the receipt convention landed, re-recorded report-only by consecutive survey turns with no owning row. The receipt-writing duty stays this lesson's rule; the routing gap that let the flags accumulate is lesson 349.

**Why (third witness):** witnessed 2026-11-02 (playbook repo, an authoring run's landing): the collateral prompt-log prune again wrote its receipt into the commit message only and the audit refused REMOVED-WITHOUT-WITNESS on the otherwise correct removal; reading the checker re-derived the in-log grammar (the receipt line inside the log post-image, its token resolving in the tree per the receipt-token rule), and the amended rider passed the identical audit unchanged. The miss recurs when the receipt is drafted from recipe memory instead of the checker read the rule requires; the checker read is the step that keeps being skipped.

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

**Extension (2026-10-24 witness, takeover landing):** the digest the egress gate
wants is the completed/ twin's bytes as they stand in the landing commit, so a
`## Disposition of migrated backlog items` fold appended at archive time changes
it: compute the exec receipt's `Egress plan bytes sha256` after the archive
commit, and take the expected value from the refusal line, which prints the
digest it computed.

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

**Witness (2026-10-23, dead-run-resume-claim-conversion landing):** the
worktree-class landing passed the target branch's tip as `--expected-tip`
and was refused naming the source worktree's HEAD; the arm wanted the
source branch tip (`land-worktree`), the exact split this lesson pins.

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

**Why (second witness):** witnessed 2026-10-27 (playbook repo): reading a lock gateway's argument shape by invoking an acquire subcommand directly acquired the merge lock as a side effect (`done-lock.sh merge-wait-acquire` with no arguments takes the lock and prints its exports immediately, because the acquire forms' stdout is export-only and their usage is not what they print); the usage text lives in the metadata-exempt no-argument invocation, and the accidental acquire was released at once with its exported token. Never probe a mutating subcommand to read its grammar.

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

**Extension (2026-10-23 witness, prune-range landing):** the continuity the
validator enforces is read from the prior record's sidecar, not its prose: a
successor round's run id is bound to the prior `.stats.json`'s
`extensions.convergence.self_heal_attempt.run_id` (a doc-line run id copied
from the prior record's metadata still refuses), the `Supersedes:` pointer
needs a matching `Superseded by:` line on the prior record, the doc's
`Coverage:` line must equal the sidecar's `coverage.outcome` string, and a
worker carries at most two non-blocking Low findings before the remainder
moves to overflow. A version-1 finding's pattern owner must be one of the
declared shared lens owners (`architecture`, `consistency`, `documentation`,
`implementation`, `quality`, `security`, `simplification`, `testing`,
`unknown`); and `scripts/produce_exec_review_record.py` is single-worker and
names its output by the plan-review series, so a multi-worker code-review record
(per-worker budgets, an overflow table) is composed by hand in the prior round's
exact shape and validated hard, never produced.

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
a plan-readiness gate refused with "plan file resolves outside plans_dir".
Fourth same-shape witness 2026-10-23 (playbook repo, exec closeout): full
`plan_readiness` run from a run worktree refused "no review artifact for
feature slug" because the plan-review r1/r2 records lived in the primary
checkout's reviews home only; the identical invocation from the primary
passed, so the checkout owning the review records runs the gate.
when run from the primary checkout for a worktree-owned plan. All three
resolved by following the tool's contract over the recipe wording.

Second witness (2026-10-21, execution run r2): the exec rounds' run-id continuity binds across the code-family chain too (an r2 minted fresh was refused); a code-family record validates only through `--source-code-repo <root> --source-code-plan <sidecar>` against a seal block whose `round_start_digest` equals sha256 of `git diff <reviewed_base>...<reviewed_head>` (`--source-plan` reads the plan family and refuses with `source_kind mismatch`); and the code-review name shape does not satisfy the plans-egress evidence leg, which greps `*-plan-review-<slug>-exec-r<N>.md` for the archived bytes' sha256, so the backfill completion record is written before `check-archive`.

Third witness (2026-10-22, execution run r2 landing): the egress record's anchored name grammar puts the `-plan-review-` segment BEFORE the slug (`<date>-plan-review-<slug>-exec-r<N>.md`, the slug occupying the whole hyphen-bounded tail); a record named `<date>-<slug>-plan-review-exec-r<N>.md` leaves an empty slug segment in the guard's anchored regex and silently fails the evidence leg even though the file carries the right digest. Derive the name from the guard's record grammar, not from the error message's shorthand.

Fourth witness (2026-10-22, execution run landing): the egress evidence record is two-sided - the archive gate demands its presence in the gitignored reviews home, while the landing's reviews-home egress fence refuses the branch that TRACKS it. A receipt staged with `git add` (needed for lesson 172's force-add in other gitignored homes) turns a green check-archive into a landing refusal; the record stays untracked (`git rm --cached`), verified by re-running both gates.

Fifth witness (2026-10-23, authoring run): rule (3)'s checkout-ownership anchor extends to the lane's own state artifacts. The authoring claim file lives at the primary checkout's claim home even while the run edits in its worktree, so a periodic claim refresh pointed at the worktree path aborts with FileNotFoundError; refresh from the owning checkout's path, not the session's current cwd - the same shape as rule (3), mirrored: the gate runs from the checkout that owns the plan, the state artifact refreshes from the checkout that owns the claim. The refresh site must also still hold a readable operand: when the run's own branch has already consumed the claim's origin row (deleted ahead of the landing), the worktree-side refresh refuses "plan operand not readable", and the refresh re-runs from a checkout whose tree still carries the row (the primary at base) - the same checkout-ownership anchor extended from the claim file to the row the refresh reads.

Sixth witness (2026-10-24, dual-mode scheduler session, exec Phase 3 and authoring cap round): the sidecar's declared `plan_identity` extension is itself the name trigger - a record whose sidecar declares the identity must carry the identity-qualified name (`...-p<identity>-r<N>.md`); the legacy-shaped name refused. Self-heal status `unknown` is reserved for a genuinely absent prior round record; when prior rounds exist and the arm went unused, the truthful status is `unused`, with the chain run id adopted from the surviving prior round's sidecar (a fresh mint was refused under run-id continuity). And a reconstructed historical record validates against the bytes it certified (the pre-archive plan bytes), never against the plan's current archived home: a post-archive re-validation fails on source_digest mismatch by construction - a validation-target error, not a record defect.

Seventh witness (2026-10-27, execution run landing): the backfill record's producer shares the naming trap: `scripts/produce_exec_review_record.py` derives its filename from `--artifact-slug`, whose default (the plan basename) carries no `-exec-` token, so a pair can validate clean at `--hard` and still miss the egress evidence leg's name scan. Pass `--artifact-slug <slug>-exec` explicitly when producing the plans-egress record.

Eighth witness (2026-10-30, self-heal-before-unknown-remedy execution run, three arms in one closeout): the checkout-ownership anchor extends to the closeout machinery's own inputs. The boundary-mirror manifest lives in the PRIMARY checkout's session dir even when the mirror subcommand runs from the worktree (a worktree path refused `manifest not found`); the continuity probe's baseline captured in the worktree session dir is COPIED to the primary session dir, never recaptured there; and the code-family chain's `round_start_digest` is the canonical `reviewed_scope_bytes` from `scripts/corrections_record.py` (the diff with bookkeeping-prefix pathspec exclusions), whose sha256 differs from a raw `git diff <base>...<head> | shasum` - derive the digest through the corrections-record reader, never the raw pipe.

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

Third witness (2026-10-31, playbook repo, session-channel-zcode-runtime-derivation-empty execution): the inverse citation form - the plan header carried a literal `-p*` infix segment, which the gate-removal series primitive does not parse (its recognized forms are a concrete `-p<8hex>` token or no infix segment at all, the tokenless form matching the optional infix), so the series reported zero members over records that existed. The remedy was again citation-only: reword the archived plan's citation to the tokenless series form (commit e160db2d6) and re-run the gate. When authoring a plan-header series citation, copy the form from a record pair that passes the gate, never from memory.

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

Teardown sibling (2026-10-23, authoring run closeout): the same consumed-branch fact puts the branch tip outside the landing commit's ancestry by construction, so `git branch -d` refuses with "not fully merged" on every cleanly squash-landed branch. The bounded delete is not a bypass: prove tree equality between the branch tip and the landing commit (`git rev-parse` both `^{tree}`), then `git branch -D`.

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
consulted is confirmed. The arm binds in both directions: a scan over a
canonical gitignored home (the reviews corpus, a shared ledger) must
resolve that home from the primary checkout, never from the invoking
worktree's transfer-in copy, whose partial population turns every absent
name into a false finding (an over-count, the mirror of the vacuous zero).

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
the worktree root, whose copy the relative name addressed, passed. Fourth witness 2026-10-29 (playbook repo, learn over the 2026-10-28 exec run): the done finalize report-only missing-review-record scan executed inside the ad-hoc worktree and rooted its checkout-relative `reviews_dir` facts value at the worktree, consulting the transfer-in partial reviews home and reporting 72 missing records; re-run verbatim at the primary checkout it reports 18, several of those fixture-shaped names embedded in the archived plans' text and missing by construction. The script already derives the primary checkout for its fallback branch, so the fix is rooting the facts branch there too; the fix is tracked in the backlog, this lesson records the operating rule.

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
gate unchanged in semantics. Re-witnessed 2026-11-01 (playbook repo, an
authoring run's round 1 preflight): the same probe refused a plan whose
checklist `Commit:` items carried no class tag; adding
`[class: IMPLEMENTATION_REQUIRED]` to every checklist anchor passed the
gate unchanged in semantics - the untagged-anchor variant of the same
grammar gap.

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

**Superseded (2026-10-29):** the landed workflow starts a worktree run
with its own Phase 0 setup and closeout-baseline capture, and done setup
now runs once at the final closeout. The ordering rule below is retained
as historical evidence of the start-dirt refusals it witnessed.

**Rule (historical):** a worktree run that will commit through the done boundary runs
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
receipt; the prune was redone as its own commit with the assertion passing.
Re-witnessed 2026-10-23 (playbook repo, exec run): a pre-landing prune-audit
joined to the landing with `;` failed, and the landing ran anyway; the
landing itself was sound and the breach was recorded as a deviation, but the
class repeated exactly as this rule predicts. Third witness (2026-10-31,
playbook repo, the stub-writer forensics run, hash-identity attributed in the
origin row disposition of plan 2026-10-28-plan-prompts-stub-writer-forensics):
the hazard reached live-path damage, not just a skipped gate - an ad-hoc
smoke command joined its fixture `cd` and a relative-path redirect with `;`;
the `cd` failed (`no matches found: /tmp/tmp.*`) and the write ran anyway in
the caller's default cwd, the primary checkout, wholesale replacing the
tracked prompt log. Probe commands that seed fixture paths must join with
`&&` and anchor their writes with an explicit path or a cd-success guard.

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

**Why:** During an authoring run, an em-dash gate was invoked as `check-no-em-dash.sh <plan.md>`, which printed the usage text and exited 0; the run recorded "em-dash clean" from a scan that never ran. The correct `file` subcommand form was recovered from the usage header only after a later gate failed for an unrelated reason. Second witness 2026-10-24 (exec run): a certified plan's own Validation Commands carried the bare `bash scripts/check-no-em-dash.sh || exit` form, so the declared gate was vacuous until the implement worker substituted the `added-lines` subcommand and reported the deviation. Third witness 2026-11-01 (exec-run review): even the right subcommand can scan nothing - the authored sweep prescribed bare `added-lines`, whose default diff window (working tree vs HEAD) was empty at the prescribed run time because the checkpoint-commit duty had already committed the plan bytes; the r1 panel caught the vacuous pass and the fold pinned an explicit `--base <branch point>`. Rule extension: a diff-window gate's window must be pinned to a base predating the bytes under test - an exit 0 from an empty window is the silent sibling of the usage-and-exit-0 pass.

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

**Why:** witnessed 2026-10-18 (playbook repo): a series carried the cap-closure certification at a round number below a pre-fold record that remained the highest; the landing sweep refused on that highest round's stale digest. Renumbering the certification record above it, with the digest re-bound to the folded plan bytes, let the same sweep pass without touching the validator. Second witness 2026-11-01 (playbook repo, execute-plan run): a canonical plan-review record was minted before the plan's bytes received their final edits (a scope-line fix and the archive-time disposition fold), so its digest no longer matched the bytes that landed; the repair was re-minting the record over the final on-disk plan bytes immediately before landing, not patching the digest by hand.

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

Extension witness 2026-10-31 (playbook repo, an execution run's pre-landing
rebase): a conflict resolved by a line-range deletion (`del lines[18:24]`)
that spanned the markers AND the merged content line between them silently
dropped the run's entire merged paragraph (the file shrank ~1% below the
base size); the post-rebase clause-presence grep plus a byte-size readback
against the base caught it before staging, and the paragraph was re-spliced
from the base's bytes. A marker-only scan cannot catch this class - the
markers are gone; the re-verify must assert the merged side's own clause is
present (grep a distinctive phrase from the content line) and the resolved
file's size sits within the expected union delta, per the diff-stat
readback arm of the conflict-extraction lesson.

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

A fresh execution worktree's wholesale reviews transfer-in (the Worktree-first standard's step 2 copy) seats thousands of foreign staging docs in the worktree, and the done setup's write-manifest claim-or-foreign gate then refuses them all as "neither owned nor foreign" (witnessed 2026-10-18, done-setup-task-owned-start-dirt-claims execution). The gate's own bulk answers are the remedy: pass `--claim-none` when the run owns no staging doc in the reviews home, and scope the transferred copy to the review series the run actually consumes so the readiness gate still resolves. The primary checkout's staging docs are never touched by the trim; they are copies. Second witness (2026-10-26, interactive exec mandate): the wholesale `cp -Rs` mirror of the reviews and seal homes also broke the commit run's docs-branch sync, which refuses any archive symlink escaping the checkout root: a primary-corpus entry that is itself a symlink is mirrored as a symlink naming the primary checkout's absolute path, and the sync refused the worktree-side copy twice in one run (the seal home first, then the reviews home). Remedy arm: a run that writes its review records directly to the primary corpus home needs no corpus mirror at all; skip the reviews and seal transfer-in entirely (the sync skips an absent home) and let the canonical home hold the records.

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

**Witness (2026-10-23, dead-run-resume-claim-conversion landing):** the
receipt was backfilled only at the first landing refusal, mid-critical-
section, merge lock held, recovered by re-exporting the lock env from the
acquire output file, the exact cost the production point below exists to
avoid; write the record before acquiring the lock.

**Rule:** before a plan execution's merge-locked landing, write the execution review record under `.ai-playbook/reviews/` named `*-plan-review-<plan-slug>-exec-r<N>.md` (hyphen-bounded) carrying the archived plan bytes' sha256; the egress guard reads it at the plans-root archive move and refuses the landing without it, and the worktree reviews home is where the record must already sit. Production point: the execute-plan flow writes the initial receipt at its Step 3.5 exit decision, when Step 3.5 selects Phase 4 (the blocking-clean exit and the satisfied residual-acceptance exit alike; a continue decision writes none); refresh point: Phase 4 refreshes the receipt's digest to the final archived plan bytes after the archive disposition section and before the archive commit and its `check-archive`; the landing call then only reads the record.

**Why:** witnessed 2026-10-18 (playbook repo, execution run): the first `land_squash.sh land-worktree` attempt refused at the plans-egress leg naming the missing record and the exact digest it must carry; writing the record and re-landing under the held lock passed. The record doubles as the migrated execution evidence. Second witness 2026-10-24 (playbook repo, two-pick exec carrier run, pick 2): the record existed but lacked the digest line, the landing refused at the same leg with the digest named in the refusal, and the digest backfill plus re-land under the still-held lock passed; the refusal message naming the exact expected sha256 is what keeps the mid-critical-section recovery bounded.

**See also:** #100 (landing helper contracts), #104 (archive gates fail closed).

Re-witnessed 2026-10-20 (playbook repo, execution run): the run's two `-code-review-r<N>` records carried the archived plan's sha256, yet the first landing attempt was refused because the guard matches the `-exec-r<N>` name grammar, not the digest alone; the receipt was written after the refusal and the second attempt landed. Fourth same-shape witness in a week: the receipt belongs to the Step 3.5 Phase 4 exit, not to the landing retry. Fifth witness 2026-10-31 (playbook repo, completion-pass run): the egress digest is **asymmetric by change shape** and the writer must derive it from the guard's own read rule, not from the file it hashed - for a rename egress the guard hashes the NEW-path bytes at the built commit (`rev:new`), for a deletion the parent-side bytes (`rev^:old`). A rename-of-unticked-bytes landing refused on the boxes leg (parent-side read), and after landing the ticks at the root first, the renamed-egress record still refused because it carried the pre-disposition digest while the guard wanted the disposition-appended archived bytes; re-producing the record against the archived path (round 2) landed it. Corollary: land every plans-root byte change (checkbox ticks included) at the root path BEFORE the archive move, so both read shapes see the same evidence.

## 108. An Evidence Digest Comes From the Bytes on Disk, Never From a Command's Fallback Output

**Rule:** when a gate or record requires a digest of specific bytes, compute it by hashing the artifact's bytes on disk (`shasum -a 256 <path>`) at claim time and confirm the path resolved; a string captured from a command that failed and fell back to echoing its argument (a failed rev-parse printing `main:<path>` verbatim) is not the digest. Before a digest enters a durable record, shape-check it (fixed-length lowercase hex) and re-derive it a second time.

**Why:** witnessed 2026-10-19 (playbook repo, execution run): while satisfying the plan-archive egress guard (lesson 107), the first digest capture took a literal `main:docs/...` string from a failed rev-parse fallback; a shape check caught it before any gate consumed the record, and re-hashing the worktree file produced the digest the guard accepted.

**See also:** #107 (the egress record that demanded the digest); #105 (measure a class by probing members, never by derivation); #78 (prove landedness from witnesses, not diff metrics).

## 109. A Lost Lock-Acquire Capture Orphans the Hold

**Rule:** parse the merge-lock acquire's stdout into its variables inside the same shell invocation that runs it (capture once, extract each field), and run the landing in that same shell; a capture construct that yields empty (quoting or subshell loss) leaves the hold acquired with no usable token record, and the exiting shell orphans it. Recovery for an orphaned hold: verify the hold record's holder pid is dead, run the orphaned-release subcommand (`merge-release-orphaned`), then redo acquire plus landing in one shell. Never leave an orphaned hold standing and never re-acquire over one.

**Principle:** Family D (a hold's own records are the recovery source; the orphaned-release arm exists for a hold whose owner output is gone).

**Why:** witnessed 2026-10-19 (playbook repo): the acquire's eval-style capture produced empty lock variables, the landing refused on the missing `--message`, and the exited shell left the hold orphaned; the orphaned-release subcommand passed after the holder-pid check, and the same-shell redo landed unchanged.

Second witness (2026-10-27, playbook repo, exec-mode ad-hoc run): the lock directory itself was externally deleted between the acquire and the landing helper's invocation (a peer's cleanup swept it), so the helper refused "merge lock directory does not exist" while this session's holder was alive. That state is not an orphaned hold - no hold record survives to recover - so the orphaned-release arm does not apply; verify the directory's absence on disk, then re-acquire and run the landing in one invocation, which also shrinks the window the two-step composition exposes to the next external sweep.

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

**Why:** witnessed 2026-10-19 (playbook repo): a plan's landing rider pruned its own dispatch entry with a heading-to-next-heading range delete and silently removed the neighboring landing's receipt line that sat at the range's tail; the execution review caught it, not the prune audit, which counts entry removals but not foreign receipt-line removals (the same audit gap the row docs/history/backlog/completed/2026-10-15-plan-prompts-prune-end-anchor-overreach.md records; the new witness is appended there). Witnessed again 2026-10-28: a landing's own-entry prune deleted heading-to-end-of-file and swept the log's five trailing foreign receipt lines; the deleted-receipt audit across the landing diff caught it in teardown and the receipts restored byte-exact from the pre-landing parent blob. See also #44.

## 112. After a Restore-Based Reconciliation, Verify the Index, Not Only the Worktree

**Principle:** Family D (state-first: a checkout's restore writes more surfaces than the one you read back; the index is the silent one).

**Trigger:** any post-landing reconciliation or stale-checkout restore that runs a wholesale or containment-delta restore arm over the primary checkout, before declaring the checkout clean.

**Rule:** after a restore-based reconciliation completes, read `git status --porcelain` (index plus worktree), never a working-tree diff alone: a restore arm can leave the pre-restoration bytes staged in the index while the worktree holds the fresh bytes, presenting later gates with unowned staged dirt that looks like a peer's staging violation. The remedy is a per-path `git restore --staged` after confirming the staged bytes equal an ancestor blob (the stale-checkout discriminator's half-synced arm), never a blanket reset.

**Why:** witnessed 2026-10-19 (playbook repo): a landing's reconciliation receipt reported a wholesale restore plus per-path containment-delta restores with exit 1; the working tree matched the new tip, but the index still held the pre-landing ancestor blob of the restored log file, and the checkout read as carrying a foreign staged reversal until the index entry was cleared. The receipt's exit code was the only surface that flagged the block; the index residue surfaced only through the porcelain read. Witnessed again 2026-10-28 (playbook repo): a primary checkout carried the pre-landing freeze blob staged on a log path the landing had touched; `git log --find-object` resolved the staged bytes to an ancestor commit before the path was cleared, preserved as a labeled stash per the foreign-dirt preserve precedent rather than discarded.

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

**Rule:** the recorded reset time is a claim by the runtime that refused the operation, not a measurement of the boundary. Before letting a timed resume carrier fire at the recorded time, run one cheap probe of the refused operation itself: a clean probe lifts the pause immediately (the pause's own carrier is deleted by its owner as the duplicate-in-waiting it has become, and the pause record gains a resolution line), a refused probe leaves the carrier standing unchanged. The discharge duty binds the pausing session itself, not just a later touching session: a session that resumes its own run manually after an early wall lift without discharging the resume carrier it armed fires that carrier into the now-live run, and the armed payload's session races the origin session over the same claim, worktree, and landing (witnessed 2026-10-31: a quota-paused exec run armed a 110-minute resume carrier, the origin session probed the wall open and resumed in-session, and the carrier fired mid-run; the collision resolved only because the origin session re-observed instead of racing and let the carrier-born session complete the landing; the run's own staged state was briefly double-written).

**Why:** witnessed twice in this repo's runtime (2026-10-17 and 2026-10-19): two usage-wall pauses idled their lanes toward the recorded reset, and a one-call probe ran clean about two hours early both times; the nominal-reset posture cost the idle hours and armed a second carrier over the live lane. Routed as the probe-first arm (the usage-wall-probe-before-timed-resume entry) with this lesson as the witness. Third witness 2026-10-20: a scheduler turn paused at 92 percent with the reset recorded for 16:39 and armed a 16:45 resume carrier; a probe at 13:44 read 1 percent with the live reset re-keyed to 18:37, so the recorded reset was replaced, not merely lifted early, and the carrier idled the lane about three hours. Fourth witness 2026-10-20: an execution run's probes read 63 and then 88 percent used against a reset recorded for 18:37 that evening with 165 minutes claimed remaining, and twenty-eight minutes after the second reading the window had already rolled over to 10 percent used with the reset re-keyed to 21:01, so a freshly reported reset was false within the half hour. Fifth witness 2026-11-01: an automation-born turn resumed from a context compaction held a planned resume carrier keyed to a 97-percent reading with the reset recorded for 18:47Z; a boundary probe 98 minutes later read 57 percent with the window already rolled (the reset re-keyed to 21:52Z), and the same fresh reads showed a parallel carrier had completed the turn's mandate, so the park-and-carrier plan died before writing anything (lesson 360 carries the full witness).

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

**See also:** `coding_guidelines.md` #24 (drop-side observability), AGENTS.md Machinery admission protocol (promotion after a true catch), `docs/maintenance/demoted-sweep-arms.md`, archived plan `docs/history/plans/completed/2026-10-24-description-length-gate-catch-promotion.md` (the origin row, covered and deleted by that plan).

## 136. A Shape Check Outlives the Convention It Encoded; Count the Compliant Population

**Principle:** Family H (verify the real thing: a validator pins a shape, and the shape is a proxy for a meaning that conventions can move away from without the check noticing).

**Trigger:** changing a corpus convention (what a served item looks like, when a token is written), or reading a validator's clean result as evidence that the meaning it was built for still holds.

**Rule:** when a convention changes, grep the validators that classify the old shape and re-baseline each default the change inverted; a fail-open default written for "unknown" becomes a permanent miss once the convention makes that case the common one. When a check can only test a shape (a prefix, a date, a presence), count the compliant population before trusting it: a confirmation token present on nearly every row is a drift signal, not health.

**Why:** witnessed twice 2026-10-20 (playbook repo). The prompt-log stale check (2026-10-01) classifies an absent origin that resolves nowhere as LIVE, a fail-open default for unknown moves; the covered-row rule (by 2026-10-13) made deletion the normal served shape, so a served entry sat dispatchable two days and a monitor sweep walked past it. The registry's `user-approved YYYY-MM-DD:` audit token means "the user confirmed this override" (ADR-0001); the validator checks only the prefix, and 579 of 659 completed rows carried the prefix on execution narration no user confirmed, while the five rows without it failed the moment they were parsed. Re-witnessed 2026-10-20 (seal census, playbook repo): the corrections gate's degrade-to-exact-match default, written for a certification predating the seal file, is the path most squash-landed plans take, because the squash orphans every resolvable seal's anchors; 7 of 37 seals anchored on main, and the two open plans refused that day were the two whose seals resolved (see #141).

**See also:** #130 (an absence signal needs an exact probe), #135 (a warning-posture catch must be ledgered), the completed plan `docs/history/plans/completed/2026-10-23-prompt-log-stale-check-deleted-origin-served.md` (the token-drift sibling row landed covered and its origin deleted per the covered-row rule; its writer-rule fix lives in the `doc-hierarchy` and `plans` skill text).

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

**Rule:** the gate seeds its owned set only from those header label lines plus `--claims`; with neither it refuses `empty owned set` by design, and the remedy is a claims file (one repo-relative record path per line, the plan's review records and sidecars) passed through `--claims`, never a header edit to the certified plan (that would stale the bound digest). After the pass, probe `git worktree list` and `git branch --list <branch>` before reporting teardown: the gate's pass may print the sanctioned removal step rather than perform it. Who runs the printed step follows the invocation shape: in a stand-alone gate invocation (no owning run around it) the printed step is the operator's to run, while in an orchestrated plans or execute-plan run cleanup ownership belongs to that run's owning orchestrator, which performs the printed step itself and executes the gate's exact disposition and the done skill's sanctioned branch-closeout sequence, per the Worktree-first standard's Terminal closeout ownership clause (`agents/skills/execute-plan/worktree-first.md`, lifecycle step 6), verifying the worktree and branch are gone where the disposition names removal and preserved-with-report otherwise.

**Why:** witnessed 2026-10-16, 2026-10-20, and again 2026-10-28 (playbook repo, scheduled authoring runs): the certified plans refused `empty owned set`, passed once a claims file named their records, and left the worktree and branch in place after the pass; teardown finished by hand. The printed-step behavior is an investigated origin (`docs/history/backlog/2026-10-11-ad-hoc-worktree-lifecycle-owner-gap.md`), so this lesson records the operating rule, not a fix.

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

Re-witnessed 2026-10-21 (playbook repo, corrections-chain operator-ack r1 review): one same-file residue and two cross-file ones (a helper docstring; a README pinned-idiom sentence whose consumer inventories missed the derivation's new third consumer class); the cross-file pair drove the extension above (`docs/history/backlog/2026-10-21-corrections-contract-doc-residues.md`).

Re-witnessed 2026-10-30 (playbook repo, agent-type-affinity plan Task 1 review): a new exemption token declared in decisions.md's fresh D1/D2 sentences was missing from the same bullet's closed sanctioned-reason enumeration and fall-through list; the plan review staged it blocking and the fix pass wove the token into both.

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

**Why:** witnessed 2026-10-21 (playbook repo, certification-seal-landing-survival execution, Phase 0): the orchestrator created the worktree, copied facts, then called `take`, which refused on the branch the call's own worktree half had just claimed and deleted its fresh claim; the retry after removing the manual worktree and branch passed on the first attempt. Second witness 2026-10-24 (playbook repo, two-pick exec carrier run, pick 1 Phase 0): the shape recurred from habit alone (the standard git workflow creates the worktree first); the refusal, rollback, manual worktree-plus-branch removal, and retry all repeated. Two recurrences of a purely procedural refusal price a remedy investigation; see backlog row `docs/history/backlog/2026-10-24-execution-claim-take-refusal-remedy-gap.md`.

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

**See also:** #146 (the refusal wording routes the diagnosis once it fires; quoting the enum keeps it from firing), the 2026-10-10 review-loop dispatch-closed-vocabulary origin row, folded into `docs/history/plans/completed/2026-10-23-review-loop-staging-vocabularies.md` (the adoption fix and the fourth-vocabulary witness), review-staging's closed-enums line (the doc-side statement this rule extends to the worker side).

## 165. Full-Mode Plan Readiness Stales on Progress Ticks; Run Pre-Round at Task Boundaries

**Principle:** Family B (ordering: a check that binds to byte identity runs after the last write that changes those bytes, never between writes).

**Trigger:** executing a certified plan whose Validation block or Done-when invokes full-mode `plan_readiness.py` while tasks remain; the first boundary's checkbox ticks have already changed the plan bytes the certification sidecar digests.

**Rule:** at task boundaries run only the `--pre-round` invocation (structural checks, review record not consulted); run the full-mode invocation once, at Phase 2, after the corrections chain's zero-round re-bind binds the certified record to the final ticked bytes. A full-mode exit 1 mid-run naming a stale sidecar digest is the boundary's own ticks, not a task defect: record it as a witnessed deferral naming Phase 2 on the boundary row and never edit the plan, the sidecar, or the validator to clear it; stash-prove the failure pre-exists the task's change before attributing it.

**Why:** witnessed 2026-10-21 (playbook repo, plan-validation-command-undefined-repo execution): Task 1's boundary commit ticked four checkboxes; Task 2's implement pass then inherited full-mode exit 1 on the r3 sidecar digest, stash-proved the failure present without its own change, and deferred the re-bind to Phase 2 instead of working around it, keeping the task's five gates green and the plan bytes untouched. Second witness (2026-10-31, playbook repo, a plan-execution Phase 2): the re-bind was a fresh focused plan-review round re-producing the record against the final ticked bytes (new round, run id carried from r1) - never an implement worker or a sidecar edit; the folded disposition section counts as a bytes change, so the re-bind round runs after it.

**See also:** the fold-side twin at the review-loop lesson on re-binding the closure certification's `source_digest` after a cap-round fold (the same digest-binding invariant at the review side), #43 (shell cwd resets between calls; re-derive at each boundary).
## 166. Transfer the Run Inputs In Before the Done Boundary Setup

**Principle:** Family B (ordering: a setup step that resolves project facts observes the transferred tree, so the transfer-in precedes it).

**Trigger:** entering a fresh ad-hoc worktree for a run that will commit through the done boundary.

**Rule:** run the Worktree-first transfer-in (the facts file and the reviews home) before `done_run.sh setup`, even though the boundary setup is the first edit-time action: the setup's run-manifest writer resolves the facts keys and refuses without them, and a refused attempt leaves the done lock held by the now-dead shell. A transferred-in reviews home also needs the setup's staging classification before the manifest write: enumerate unclaimed candidates with the sweep-gates lib's `--emit-foreign-candidates` invocation and re-run setup with `--foreign-review-from`. Release an abandoned hold only with the original token from the failed setup's own stdout, after corroborating the lock's meta.env repo_root against the checkout - never by stealing it from a fresh acquire path.

**Why:** witnessed 2026-10-21 (playbook repo, authoring-worktree-landing-shape execution): two setup attempts refused in one run (facts config error, then claim-or-foreign over 3264 transferred staging docs), each stranding its lock until the original-token release. Witnessed again 2026-10-23 (review-reconciliation-continuation-stop execution): the refused first attempt stranded the worktree lock under its printed token; the re-run with `--foreign-review-from` succeeded under a rotated token, so the operative token for the run's later boundary legs is the newest successful setup log's, never a refused attempt's. Witnessed a third way 2026-10-24 (playbook repo, a paused execution run's resume recipe): the recipe named the done-lock directory of the previous pick, copied from the session's earlier context, while the run's own setup log named a different directory; the resume session that trusted the recipe would have read the lock as abandoned and re-run setup over a live lock. The recipe may name the lock, but the resume re-derives the directory and token from the run's setup log before touching it. 2026-11-01 re-witness: a transfer list of bare basenames refused the claim-or-foreign gate (the classifier matches repo-relative paths); the list regenerated with repo-relative entries, and the same day's landed arrival-default arm retires the class for fresh provisioning (documents present before the run-start marker classify foreign without the flag).

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
deletion leg, so the producer is unattributed; the 2026-10-27 closeout enumeration left it unresolved and closed the row with the mirror-before-closeout preservation arm landed.

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
half of the same reviews-home discipline), the closed backlog row's
landing (producer unresolved after the 2026-10-22 enumeration; this
rule's second arm is the landed mirror-before-closeout preservation).

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

**Rule:** when `git add <path>` refuses with "the following paths are ignored", treat the refusal as information about the layout, not an obstacle: check that the directory already holds tracked content, and when the new file belongs in that tracked set, add it with `git add -f` deliberately. Afterwards confirm intent with `git ls-files -i -c --exclude-standard` (empty). Neither a silent plain-add drop nor a blanket force-add habit is acceptable. Within the `.ai-playbook/` audit home the never-force-add rule governs (the seal and every audit-home artifact stay untracked; an ignore refusal there ends the staging attempt; see agents/skills/plans/SKILL.md round-close and agents/skills/maintenance/template-authoring.md closeout).

**Why:** witnessed 2026-10-20 (playbook repo): adding a review-certification seal under `.ai-playbook/review-certs/` was refused because the directory is gitignored while its seal files are tracked; the forced add landed the seal. The lesson's tracked-seal premise was removed when landing plan ignored-audit-home-tracked-index-fence untracked the inventoried records.

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

**Why:** witnessed 2026-10-22 (playbook repo, execution landing): the first lessons conflict in a 12-commit rebase was resolved correctly (upstream corpus plus the branch's two lessons renumbered past upstream's max), but the second conflict at a later branch commit was resolved with `--theirs`, which took the branch's stale corpus (lessons to 159) and silently deleted upstream's lessons 160-172; the damage surfaced only because a heading census ran before landing, and the restore re-derived upstream's corpus verbatim and re-appended the branch's entries. Extension (2026-10-25 witness, execution landing): the conflict-block renumber covers only the entries inside the conflicted hunks; a branch lesson appended by a LATER commit that does not itself conflict (its insertion point had no upstream delta) keeps its stale number and collides after the landing, so the renumber pass must sweep the branch's every appended entry against upstream's max, not just the conflict blocks; a duplicated-heading grep is the cheap catcher. Extension (2026-10-27 witness, playbook repo, exec-run closeout rebase): the flag sides invert by operation - in a rebase conflict `--ours` is the upstream and `--theirs` is the commit being replayed, the mirror of merge semantics - so a merge-habit reach for `--theirs` resolved the whole log from the run's own stale bytes; the slip was caught by grepping the resolved bytes for an upstream-side landmark (a peer receipt line) before staging, so name the sides by role and grep before `git add`, never by merge muscle memory. Extension (2026-10-29/30 witness, playbook repo, exec-run closeout rebase): the branch's new lessons can also ride as UNCOMMITTED dirt while the rebase runs, where an EOF-append onto upstream's moved EOF is the conflict to avoid: save the dirt byte-exact, `git checkout --` the corpus file, rebase, then re-append the entries renumbered against upstream's fresh max with the corpus's two-blank-line separator restored, and census as above.

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

Re-witnessed and refined 2026-10-27 (playbook repo, exec-mode max-2 run): one landing bound the digest over the content head preceding the receipt and documented the receipt as bookkeeping outside the digest domain, and the focused panel challenged the carve-out as under-documented; the refinement avoids the fixed point entirely for log-embedded receipts - the receipt line the rolling log carries holds no digest at all (the log's standing digest-free receipt grammar), and the `Ad-hoc-panel-pass` digest over the full delta lives only in the landing commit message, where the three-way check (receipt == record `Source digest` == re-derived) holds exactly with no post-digest delta left to enumerate.

**See also:** #99 (the hand-composed landing form this digest shape rides on), #112 (verify the index, not only the worktree, after restore-based reconciliation).

## 183. A Scripted Structural Edit Is Claimed Only After a Tree Check of the Exact Intended Delta

**Rule:** any script-driven multi-line edit (python `str.replace`, section splice by `str.index` anchors, heredoc splice) that a follow-up claim will narrate (a review fold, a landing, a receipt) must verify the edit landed as intended before the claim: assert the replacement count or compare before/after bytes, anchor `index` calls on strings proven unique in the file (an anchor that occurs earlier splices the wrong region and can duplicate whole blocks), and after any conflict resolution grep the file for leftover conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) before committing. A `replace` that matches nothing is a silent no-op in every scripting language; the fold claim then over-delivers versus the tree and only an independent re-read catches it.

**Why:** witnessed 2026-10-22 (playbook repo, ad-hoc landing review r2): a fold script's `str.replace` no-op'd on a one-word byte difference ("same stranding class" vs "same defect class") and its `s.index` end-anchor matched a receipt line occurring earlier in the file than the entry being removed, duplicating a 14-line receipt block while leaving the target entry unremoved; the review panel's re-derivation from disk caught both, and the same run later landed a stray conflict-marker line that a post-resolution grep would have caught pre-commit.

**See also:** #74 (treat a zero-count success as unverified until the consulted tree is confirmed - this lesson extends it from read probes to write claims); #69 (derive the match pattern from on-disk names, not citation prose - the read-side sibling).

## 184. An Unquoted `=` Word in zsh Expands and Aborts the Chain Before the Next Command

**Rule:** in zsh command chains, never emit a bare separator argument whose text begins with `=` (for example `echo ===` or `echo ==-done`): zsh performs `=word` filename expansion (the PATH-command form) on it, fails with `=word not found`, and exits the `&&`-chained call before the subsequent steps (an amend, a gate, a release) run. Use `printf '%s\n' '...'`, quote the argument, or pick a marker without a leading `=`.

**Why:** witnessed 2026-10-22 (playbook repo, ad-hoc landing): a landing chain used `echo ===` as a visual separator between the file fix and the `git commit --amend`, zsh aborted on the expansion, and the amend and all downstream gates silently did not run in that call; the next call then operated on a half-landed state.

**Second witness (2026-10-23, learn turn):** two ad-hoc recon chains lost every step after an unquoted `===label===` echo separator (`zsh: ==WORKTREES=== not found`); with `&&` joins the pre-separator steps still ran, so the symptom reads as missing output rather than a dead call. Quote the marker or pick a leading-dash form.

**See also:** #181 (shell tool calls reset cwd between calls - the same class of chain-boundary assumption turning one call's failure into the next call's surprise).

## 185. A Re-Bind Round's Seal Binds round_close_commit to the Commit Where the Certified Bytes Landed

**Principle:** Family B (ordering and identity: a seal's close anchor is the commit whose tree carries the certified bytes, not whatever commit is HEAD when the seal is written).

**Trigger:** closing a Phase 2 progress-tick re-bind round (lesson 165) whose corrections chain terminates in a seal entry for a round certified before the plan's landing squashes moved the tip past the certified bytes.

**Rule:** set the re-bind seal's `round_close_commit` to the ancestor commit at which the certified round's bytes landed (the covering squash landing commit), never the current tip. The staging validator refuses the tip-bound shape ("hop commit dated before the seal entry's round-close commit") because every hop in the chain predates a tip anchor by construction. Derive the value from git history (the commit whose subject carries the covering landing), not from a predicted future sha.

**Why:** witnessed twice in one run (2026-10-22, playbook repo, exec-mode max-3 run, two plan executions): each Phase 2 re-bind round first drafted the seal with the then-current tip as `round_close_commit` and hit the same seal-integrity refusal; re-binding the close anchor to that plan's covering landing commit cleared both.

**Third witness (2026-10-23, authoring certification r2):** the identical refusal fires on a corrections row's `evidence_commit`, not only on a seal's close anchor: an initial anchor at the round-start commit refused with "hop commit dated before the seal entry's round-close commit", and re-pointing the hop at the commit whose tree carries the corrected bytes (here the round-close commit itself) cleared it. The general form covers both artifacts: every hop's commit anchor is the commit whose tree carries the bytes that hop claims, at or after the chain's close anchor.

**See also:** #165 (the re-bind duty this seal closes), #182 (the digest-binding invariant the same records carry), #32 (the machine-resolvable seal shape).

## 186. Execution Review Records Resolve Through the Canonical Artifact Slug, and a Certification Round Stages Blocking Findings Only

**Principle:** Family B (ordering and identity: a review series is keyed by the plan's canonical artifact slug, and the round verdict is a function of the staged-findings set).

**Trigger:** producing an execution-run review record pair with `scripts/produce_exec_review_record.py` during execute-plan Phase 3, then running the full readiness gate over the assembled series.

**Rule:** pass `--artifact-slug <print-artifact-slug output>` explicitly: the producer's default (the kebab-cased date-prefixed plan filename stem) names records the readiness gate's series resolution cannot see, so the gate keeps reading the authoring series' last round and reports a false stale-digest refusal ("plan bytes changed after review r5") even though a fresh certified round exists on disk. And stage blocking findings only at a certification round: the producer derives the sidecar verdict mechanically (any staged finding yields verdict `no`, an empty staged set yields `yes`), so deferred watchlist rows belong in the finding round's triage columns, never in the certification round's findings list (D-8 clause 2: non-blocking findings never force a re-round). Also match the small schema surfaces the hard validator enforces: `--round` takes the integer continuing the authoring series' numbering, and the metadata `Last fix commit:` line must equal the sidecar sha byte-for-byte.

**Why:** witnessed 2026-10-23 (playbook repo, maintenance-plan-authoring-authorization execution): four readiness-gate refusals in a row (stale r5 digest, verdict no, metadata disagreement, then resolution) collapsed once the pair was re-produced under the artifact slug with an empty certification findings list. Second witness 2026-11-02 (playbook repo, an exec run's archive-egress gate): the round number must stay OUT of `--artifact-slug` - passing `<slug>-exec-r1` made the producer emit `...-exec-r1-r1.md`, which the egress gate's `*-plan-review-<slug>-exec-r<N>.md` grammar cannot match; the record was deleted and re-produced with the bare `<slug>-exec` so the producer appends `-r1` itself. Third witness 2026-11-02 (playbook repo, an authoring run's name-shape probe): the plan-review series' optional identity token sits BETWEEN the artifact slug and the round number (`<date>-plan-review-<slug>-p<8hex>-r<N>.md`); renaming a pair to `<...>-r<N>-p<8hex>.md` fails the same probe even though every token is present, and the probe's refusal message prints the discovery glob - derive the rename from that glob, not from the token's order of mention in the template prose.

**See also:** #182 (the digest preimage the certification binds), #185 (the seal's close-anchor identity), and the series-token-infix lineage (per-worktree series tokens) for the sibling naming surface.

## 187. Gate a Shell Chain on the Scripted Resolver's Exit, and Anchor a Base-Line Lookup on the Line Start

**Principle:** Family A (verify scripted structural edits before the next mechanical step; #183 and #43 are the neighbors).

**Trigger:** resolving a rebase conflict, or any multi-step edit, where a scripted resolver precedes `git add` and `git rebase --continue` in one shell invocation.

**Rule:** join the resolver and every following mutating git step with `&&` (or run under `set -e`) and verify the resolved file carries zero conflict markers before staging; when a resolver locates a target line by content, anchor on `startswith` of the line's unique opening, never on a substring another line may also contain.

**Why:** witnessed 2026-10-23 (playbook repo, plan-prompts-prune-range-content-inventory landing rebase): a heredoc python resolver aborted on a bad anchor, but the newline-separated `git add && git rebase --continue` that followed still ran and committed a template-authoring.md carrying conflict markers (caught by a marker scan over the rebased commit, recovered with `git rebase --abort`); the bad anchor itself came from `next(l for l in base if phrase in l)` matching a 403-byte sibling line that also contained the phrase instead of the 26k-byte blueprint line. Both failures are silent without the exit gate and the marker scan. Second witness 2026-10-23 (update-stacked promoted-commit execution closeout): a newline-separated teardown chain ran `git worktree remove` and `git branch -D` after the claim release and the closeout gate-removal had both printed `OUTCOME: fail`; the artifacts had been migrated and verified beforehand, so nothing was lost, but the chain never read the refusals. Third witness 2026-10-24 (playbook repo, this exec run's EXEC-PROMPTS fold): the heredoc python fold script asserted the receipt label absent from the extracted entry body, the predicate tripped on the entry's own standing-rules text that legitimately mentions that label, and the newline-separated `git add && git commit` that followed landed the commit without the fold (caught on the immediate `--stat` re-read, repaired by amend); an entry-scoped assertion must anchor on the entry's slug heading or Frozen line, never on a label the entry's boilerplate itself carries. Fourth witness 2026-10-27 (playbook repo, 19:20 exec carrier's squash landing of the doc-hygiene plan): a reverse-replay rebase hit a shared-ledger conflict, the heredoc python union resolver aborted mid-block, and the newline-separated staging that followed committed replayed history carrying conflict markers into the lessons tail; the marker grep over the replay caught it post-commit, and because the base branch's landed commits are immutable the repair was a corrective commit (`cb885ba9a`) rather than an amend, so the guard arm applies to replayed landing history too: run the marker scan before the replay's staging step, not only after. Fifth witness 2026-10-28 (playbook repo, an execution run's pre-landing rebase): the conflict markers landed inside Python module docstrings, where they parse as string content, so an ast.parse check over the resolved file passed while the markers stood; the marker grep is the only check in the family that survives this shape, and it was the step skipped when the resolver errored mid-run and the staging still ran. Sixth witness 2026-10-30 (playbook repo, an execution run's pre-landing rebase after two earlier same-run failures): an earlier resolver script that died mid-assert had already been followed by unconditional `git add && rebase --continue`, committing markers twice before the abort; the rebuilt resolver gated on its own postconditions - assert exactly one marker set per conflict, assert zero markers remaining BEFORE staging, write the resolved file only after all assertions - and the retry then ran clean, so the durable shape is a resolver that asserts-before-staging inside itself, not a resolver plus a separately-remembered staging gate. Seventh witness 2026-11-01 (playbook repo, the 10:49 author carrier's close-as-covered commit): a heredoc python edit asserted an incidental vocabulary item that belonged to the sibling backlog row rather than the log entry, the assert fired as designed, and the newline-separated `git rm` that followed still staged the row deletion for a commit the runner then refused; the staged deletion had to be restored before the retry. The entry-scoped-assertion arm applies with a sharper edge here: the assert that fired was correct to fire, so the family's fix is not only assertion content but CHAIN SHAPE - the compound `cmd1 && cmd2 \` written across a heredoc-consuming command makes the following lines part of the same logical command in some shells, so the heredoc body's exit never gates them; a heredoc-consuming command stands alone as its own statement, and the next statement re-checks its exit. Eighth witness, same turn and same shape at the parse level: writing the continuation `&& \` on the heredoc opener's line made the shell read the body's first lines as commands (`command not found: import`) while the edit still ran - the parse split and the exit gate split are the same defect seen from both ends.

**See also:** #183 (verify scripted structural edits), #43 (worktree cwd resets between shell calls), and the conflict-content discipline in `agents/skills/execute-plan/worktree-first.md` (union of intents, then re-verify both sides present).

## 188. A Redirection Chain Is Processed Left to Right: `2>/dev/null >&2` Discards stdout

**Principle:** Family B (shell mechanics with a silent failure mode; #184's
neighbor).

**Trigger:** appending an error-suppression suffix to a command whose
output should reach stderr, e.g. `sed ... file 2>/dev/null >&2`.

**Rule:** order redirections by their dependency: `>&2` clones stdout to
whatever fd 2 is AT THAT MOMENT, so `cmd 2>/dev/null >&2` sends stdout to
/dev/null (fd 2 was already re-pointed); write `cmd >&2 2>/dev/null` when
the output must reach the real stderr and only the command's own
diagnostics belong in the bit bucket.

**Why:** witnessed 2026-10-23 (playbook repo, dead-run-resume-claim-
conversion execution): the claim gateway's refusal paths echoed captured
helper stderr through `sed 's/^/  /' "$err" 2>/dev/null >&2`, and every
echo silently vanished, six refusal arms carried no evidence lines, the
test suite asserted on strings that could never appear, and the debug cycle
cost a full instrument-and-rerun pass before a five-line isolation test
showed the ordering as the cause. The fix is mechanical and untestable by
reading: only a fixture that captures the chained form catches it.

## 189. A Nonzero Function Return Dispatched After a Semicolon Exits Under `set -e`

**Principle:** Family B (shell mechanics; #184, #187, and #188 are the
neighbors).

**Trigger:** capturing a function's verdict with `fn; rc=$?` inside a
`set -e` script, intending to branch on `rc`.

**Rule:** a bare simple command's nonzero status trips `set -e` before the
`rc=$?` assignment ever runs (the script exits with the function's status);
dispatch through a condition context, `if fn; then rc=0; else rc=$?; fi`,
or `fn || rc=$?`; the same applies to arithmetic and test builtins in
unprotected positions.

**Why:** witnessed 2026-10-23 (same execution): the claim gateway called
its conversion arm as `try_dead_run_conversion "$holder"; rc=$?` and the
arm's deliberate nonzero verdicts (2 = no context, 3 = lost race) became
silent whole-script exits carrying the function's own status, eight test
failures with exit code 2 and no message pointed at the call site only
after the if-context rewrite.

## 190. A Lock Helper's Caller-Pin Variables Are Mode-Prefixed, Not Shared

**Principle:** Family D (single source of truth: read the helper's per-mode
environment surface before composing an invocation; #54's generalization
guard, applied to env names).

**Trigger:** composing a script around a helper whose two modes share
semantics (done lock, merge lock) and setting one "holder" variable for
both.

**Rule:** grep the helper for the exact env names each mode reads before
the first invocation, this helper's pins are `DONE_LOCK_HOLDER_PID` /
`MERGE_LOCK_HOLDER_PID` (with `*_HOLD_PIN` siblings), and a mode-neutral
guess (`LOCK_HOLDER_PID`) is silently ignored: the acquire succeeds, the
meta records the fallback holder (a process that is not yours), and the
caller's own verify step then refuses what it just acquired.

**Why:** witnessed 2026-10-23 (same execution): the gateway set
`LOCK_HOLDER_PID=$$ LOCK_HOLD_PIN=1` for both modes; done-mode acquires
recorded the invoking subshell's PID instead, the gateway's
records-verification arm refused every acquire (`holder_pid record is
N, want the gateway pid`), and the cause surfaced only from a
done-lock.sh source read after two fixture debug cycles.

## 191. Fresh-mtime Residue Blocks Are Discharged by Blob Verification Against the Pre-tip Tree, Never by mtime Trust

**Rule:** when the post-landing reconcile or a staging gate names a `fresh-mtime` residue block on a primary-checkout path, classify the residue by content, not modification time: compare the index blob and the worktree blob against the pre-landing parent tree (`git rev-parse <pre-tip>:<path>` against `git ls-files -s` and `git hash-object`); when both are byte-identical to the parent the residue is dead and a targeted `git restore --staged [--worktree] -- <path>` fast-forwards it to HEAD; when a path's worktree blob differs from both the parent and HEAD the path is live dirt, so restore the index only and leave the worktree bytes alone.

**Principle:** Family A (verify scripted structural edits before acting; the block is a heuristic discriminator, not a verdict).

**Trigger:** a done closeout or landing whose `post-landing-staging` gate refuses on primary residue, or a `reconcile_post_landing` receipt whose block rows name `fresh-mtime`.

**Why:** witnessed twice in one session (2026-10-23, playbook repo): a peer landing (1763c1601) had left the primary index and worktree on two paths at the pre-landing parent bytes (its reconcile never completed), which blocked this session's done commit until the blobs were proven equal to the pre-tip tree and the gate's escape applied; the same discriminator then blocked this session's own landing on three paths whose blobs were provably the pre-landing parent, each fast-forwarded after verification. The fresh mtimes came from the reconciler's own earlier sync passes, not from any live writer.

**See also:** #43 (worktree cwd resets between shell calls), #183 (verify scripted structural edits), the post-landing reconciliation implementation in `agents/skills/execute-plan/worktree-first.md`.

## 192. An Un-Classifiable Landed Subject Repairs by Tree-Identical Message-Only Amend

**Principle:** Family D (recover and land through the owning machinery against current state).

**Trigger:** the just-landed base-branch tip carries a subject the post-landing verifier refuses to classify, found at the first post-landing audit, sha unconsumed.

**Rule:** prevention stays #50: compose the subject from the guard's recognized grammar before landing. Once the mis-subjected tip is already the base branch's head from your own landing, two repair arms exist. (a) Message-only amend: fix only the subject; tree and parent stay untouched, so the verifier classifies the new tip. The amend is a non-descendant ref pair and one permanent `backward-move:` row in the base reflog audit; the landing record names the deliberate, tree-identical deviation, and the row is never cleaned up later. (b) Leave the tip and hand-run the verification the guard can no longer anchor, losing guard coverage for every later walk over the range. Arm (a) trades one explained reflog row for restored coverage; arm (b) keeps a pristine reflog at the price of permanent lost coverage. Revert-and-re-land is out: it doubles the reflog churn and orphans the first landing. The amend arm is bounded to the just-landed, unconsumed tip of the same session; a sha with downstream consumers falls under #6's immutability note and only arm (b) applies. A content-empty landing is a different defect class: its repair is an additive corrective commit naming the content-bearing sha, never an amend.

**Why:** witnessed 2026-10-23 (playbook repo): a resume-carrier landing composed a free-form subject with no landing-claim prefix; the single-commit sweep refused the anchor (exit 2). A message-only amend re-titled the tip into the `plans: land <slug> (...)` grammar with the identical tree and parent, and the reflog-window audit flagged the amend as one backward-move row, named in the landing record and memory.

**See also:** #50 (the prevention rule this lesson assumes), #6 (the immutability boundary for consumed shas).

## 193. A Lock Status Read Resolves Its Repository by cwd

**Principle:** Family A (state facts are re-derived from the repository at the point of action, never carried from conversation).

**Trigger:** checking whether a per-checkout lock (a done lock, a merge lock) is held while the hold lives in an ad-hoc worktree of the same repository.

**Rule:** a lock helper whose status mode keys the repository from the shell's working directory reports on that checkout's lock root only; the primary checkout and its worktrees carry independent lock roots, so a status read from the primary answers "free" while the worktree's hold stands. Run the status read from the checkout whose hold the question is about (or resolve the lock root path explicitly) before any conclusion or follow-up action gates on the answer; a "free" that contradicts a recorded hold is resolved by re-reading from the hold's own checkout, never by treating it as license to re-acquire.

**Why:** witnessed 2026-10-23 (playbook repo): a paused run's intentionally held done lock read "free" from the primary checkout and "held" with the recorded token from the execution worktree, same repository, minutes apart; the release path then ran through the recorded exports as planned.

**See also:** #35 (lock exports die at the tool-call boundary; the hold record is the recovery source).

## 194. A Resume Recipe Pins Immutable Anchors Only

**Principle:** Family A (state facts are re-derived from the repository at the point of action, never carried from conversation).

**Trigger:** authoring a pause-handoff contract (a resume recipe, a checkpoint manifest) that a later session, often a different carrier, executes after an uncontrolled gap.

**Rule:** a resume recipe may pin what cannot move while paused: the worktree path, the run branch name, the checkpoint sha of the run's own branch, digests of owned files, and lock tokens and exports recorded at pause time. It must not pin what peers move during the gap: the base branch's tip, the merge-base, or gate operands derived from them. For those, the recipe instructs re-derivation at resume time (for example: pre-landing gates run over the fresh merge-base of the run branch and the base branch, not over a pinned landing base) and names the sanctioned remedy when re-derivation diverges (the pre-lock rebase in the execution worktree). A recipe-pinned base sha that a peer has passed becomes a stale operand that refuses the landing or audits the wrong range.

**Why:** witnessed 2026-10-23 (playbook repo): a paused run's resume recipe pinned the pre-pause base tip as both the landing base and the pre-landing gates' base; peers landed on the base branch during the pause, the landing probe refused the stale base, and the executing session re-derived the fresh merge-base from disk, rebased pre-lock over disjoint deltas, and ran the pre-landing gates over the re-derived base before landing.

**See also:** #128 (rebase discipline past a diverged fork), #129 (the executor-side re-derivation duty this recipe-authoring rule complements).

## 195. Twice-Refused Edits on a Shared Index Become One Atomic Line Rewrite

**Principle:** Family A (a repeated staleness refusal under concurrent writers is a race signal; switch mechanism, do not retry the loop).

**Trigger:** editing a shared, concurrently appended index file (the user-level memory index) while peer maintenance sessions are landing their own entries, and the editor refuses twice in a row with a modified-since-read staleness error.

**Rule:** after the second consecutive staleness refusal on the same file, stop the read-then-edit loop and perform one single-process read-modify-write that matches only the target entry keys, replaces those lines, and writes the file back whole; then verify the lines landed with a fresh grep. Never write from the stale read's full content, never reorder or drop sibling entries (the append-first convention still governs), and never delete an entry to make an edit apply.

**Why:** witnessed 2026-10-23 (playbook repo, learn turn): a peer session appended index entries between each read and edit, so two consecutive edits failed modified-since-read; one python read-modify-write of exactly the two target index lines landed cleanly and a follow-up grep verified both, while the peer's concurrent append survived untouched.

**See also:** #134 (own-edit commit check: never stage hunks this session did not write), #194 (the same family: re-derive shared mutable state at the point of action).

## 196. Re-Probe the Toolset at Each Session Instance Before Honoring a Recorded Absence

**Principle:** Family B (identity: an environment verdict binds the instance that wrote it, not the lineage; cap-blocked is not toolset-absent).

**Trigger:** resuming or continuing a session whose conversation or state records say the toolset lacks scheduling primitives (the reduced-toolset terminal park), before acting on that record.

**Rule:** re-probe with one real primitive attempt (an actual create, not another listing) at each new session instance before honoring a recorded toolset absence; a continuation can carry primitives its pre-continuation instances lacked. In the other direction, a refused create is not proof of absence: name which blocker fired (a lingered-spawner create cap lifts by deleting the own spawner; an absent primitive lifts by nothing), and record that distinction, never a bare "reduced toolset".

**Why:** witnessed 2026-10-23 (playbook repo): the pending_rearm park carried two recorded toolset-absent discharge failures (2026-10-22 23:05, 2026-10-23 04:08), and the resumed instance's first real create succeeded first try, arming the D-3 carrier; the same day a peer session corrected its own earlier "listing-only toolset" record to "the primitives were present, the cap was the blocker". Both misread directions landed in records within one day.

**See also:** #194 (re-derive mutable state at the point of action; this is its instance-scoped environment-fact arm), #160 (probe by attempting, not by listing).

## 197. Stranded Tracked Dirt on a Ledger-Class File Can Be a Row-Dropping Rewrite, Not an Append

**Principle:** Family A (pre-existing working-tree dirt inherited by a new session is unverified peer output; audit before landing, do not attribute blind).

**Trigger:** picking up stranded tracked dirt (a modified ledger, index, or registry file left by a prior session) and preparing to commit it as an attribution landing.

**Rule:** before committing stranded dirt on an append-surface file, run a whitespace-insensitive diff (`git diff -w`) and re-derive that no pre-existing row or entry was removed or replaced by the rewrite; a stale-snapshot whole-file write both adds the peer's row and silently drops rows another writer landed after the snapshot. Split the landing: the stranded append lands as one commit, any dropped rows are restored from the parent commit as a second commit, and both receipts are recorded.

**Why:** witnessed 2026-10-23 (playbook repo): the working-tree `gate_liveness_ledger.json` dirt looked like one appended incident row; the whitespace-insensitive audit showed the rewrite had also deleted the dead-run recovery pre-registration change row from HEAD, so the attribution commit landed the append (8a131767f) and a second commit restored the dropped row (8f967b726) - exactly the clobber shape an open PLAN-PROMPTS entry had witnessed hours earlier.

**See also:** #134 (own-edit commit check: never stage hunks this session did not write without auditing them), #195 (twice-refused shared-index edits become one atomic rewrite).

## 198. unittest discover Under-Collects Plain-Function Test Suites; Run scripts/ Suites With pytest

**Principle:** Family D (a documented verification command that silently runs a fraction of the suite is a false-green factory; the runner contract must match the suite style).

**Trigger:** running the repository's `scripts/` test suites via the documented `python3 -m unittest discover -s scripts -p 'test_<name>.py'` invocation and reading a tiny test count (one) as a pass.

**Rule:** when a suite file defines its tests as module-level pytest-style functions (fixtures by argument name), unittest discovery collects none of them; verify with pytest (`python3 -m pytest scripts/test_<name>. -q` style) and treat a suspiciously small collected-count as a runner mismatch, not a small suite. A landing that ran only the discovery-collectable subset has not run its suites.

**Why:** witnessed 2026-10-23 (playbook repo): `unittest discover` over `test_done_sweep_gates_lib.py` ran 1 test and passed, while the file holds 337 plain-function tests; `pytest` on the same file collected and ran 353 (plus subtests) and caught three real failures in freshly written fixtures that the discovery run had reported green.

**See also:** #74 (treat a zero-count success as unverified until the consulted tree is confirmed; #198 is its collection-count arm); the repository guidelines' unittest discover recipe needed a pytest arm for plain-function suites (landed in the guidelines' Testing Guidelines, witness the covering ad-hoc landing).

## 199. Check a Scope Arm's Reachability Through the Gate's Enumeration Universe Before Writing Its Fixture

**Principle:** Family C (a fixture for an unreachable input shape is dead weight and a false coverage claim; derive fixtures from the enumeration, not the prose).

**Trigger:** writing refusal-arm fixtures from an entry's scope-arm wording (for example "candidates outside the reviews home still refuse") without first reading the gate's candidate enumeration.

**Rule:** before writing a refuse-arm fixture, re-derive from the gate's enumeration code which on-disk shapes can actually enter the uncovered set; when the prose names a shape the universe cannot produce (a candidate class the enumerator filters out), write the nearest reachable refuse arm instead (the same refusal firing from a different qualifying condition) and record the unreachable shape as such, never as covered.

**Why:** witnessed 2026-10-23 (playbook repo): the foreign-by-default entry's "candidates outside the reviews home" refuse arm was unwritable because the claim-or-foreign universe enumerates only the reviews home; the reachable refuse arms proved to be the non-ignored candidate, the owned-arm parity, and the linked-worktree shape, and the worktree cell was written in the outside-home cell's place.

**See also:** #182 (probe the predicate with the real shape), #74 (treat a zero-count success as unverified until the consulted tree is confirmed).

## 200. Re-Derive Lane Liveness and Mirror Untracked Records Before a Worktree Teardown

**Principle:** Family A (state facts are re-derived from the repository at the point of action, never carried from conversation).

**Trigger:** an operator ask to remove a leftover authoring or execution branch and worktree, or any teardown justified by a merged-ness check.

**Rule:** before removal, re-derive liveness from the repository, not from git topology: under squash landing an authoring branch never advances, so an ancestor-of-main branch can be a live reserved surface and a non-ancestral branch can hold the only copy of certified work. Probe the open backlog rows and rolling-log entries citing the branch's plan slug, and check for a fresh authoring claim; inventory the worktree's gitignored homes (reviews home, authoring claims) for unlanded records and mirror them to the primary checkout; land unique durable artifacts (a plan file lands verbatim with the frozen-entry prune rider) before deleting. Removal then follows on a clean, re-derived-dead lane.

**Why:** witnessed 2026-10-23 (playbook repo, operator-directed cleanup): a fully-merged-looking branch was the reserved surface of a still-open high-priority plan, and a sibling non-ancestral branch held a five-round-certified plan plus its untracked review series; both were recoverable only because the teardown ran the probes and mirrors first, and the rescue landing is `88a718cf8`.

**See also:** #167 (mirror untracked run records before the closeout stages run), #46/#104 (landing-shape mechanics); the durability arm is owned by the plans skill's certification-time checkpoint duty in the authoring round-close (its origin row covered by the landing commit).

## 201. A Primary-Checkout docs/tmp Session Home Is Sweep-Eligible Mid-Run; Keep the Run's Logs Worktree-Side

Witnessed 2026-10-23 (done-dirt-regression-valid-correction-path execution): the run's `docs/tmp/execute-plan/<slug>/` home in the PRIMARY checkout, manifest, briefing, implement log, was found deleted twice within an hour while the run was live (unattributed sweeper; peer sessions run tmp sweeps and done closeouts concurrently on this checkout). The execution-claim files were untouched both times; only the execute-plan session home vanished. Rebuild cost: reconstructing logs from in-context records with provenance notes.

Rule: a live execute-plan run must treat the primary-checkout session home as volatile, not durable. Before every write to it, verify the directory still exists and re-create from the run's durable state on absence; keep the authoritative copies (manifest, briefing, implement/review logs) in the RUN WORKTREE's own `docs/tmp/` home, which no peer sweep reaches, and mirror to the primary only as a best-effort boundary record-mirror. Never treat a vanished session log as evidence that the step it recorded did not run, re-derive from the worktree, the commits, and the workers' returns.

Re-witnessed 2026-11-01/02 (done-setup-staging-doc-foreign-arrival-default execution, mirror-side gap): parent-side writers landed the run's briefing and the task review log in the PRIMARY home only while the implement log landed worktree-side, so the next leg's read of the named review log at the worktree home found nothing. On absence at the worktree home, check the primary mirror home before reporting the artifact missing, and copy the bytes back worktree-side to restore the authoritative home.

## 202. Grep the Pins and Frozen-Span Suites Before Condensing Skill Prose

**Principle:** Family C (shared-artifact coordination: operative prose and the mechanical pins that quote it must co-evolve).

**Trigger:** paying the anti-growth byte budget, or any condensation, by deleting or rewording sentences in a skill file that a pins suite or a byte-exact frozen-span test quotes.

**Rule:** before removing or rewording a sentence, grep the pins suite (`scripts/check_maintenance_pins.sh`) and the `scripts/test_*.py` frozen-span fixtures for distinctive substrings of that sentence; take the byte payment from unpinned prose only; run the pins check and the frozen-span suite on the condensed file before the review round, not after a blocking finding. A pinned carrier that must change is a pin update in the same change, never a silent reword.

**Why:** witnessed 2026-10-23 (playbook repo, semantic-naming plan execution): two consecutive blocking rounds on one file. Round 1 found the condensation had deleted the sentence the pins suite quotes; the round-1 fix restored it and paid the bytes by rewrapping the Boundary rule paragraph, which the frozen-span test pins byte-exact, so round 2 blocked again. Each grep takes seconds; each round cost a fold plus the digest re-bind (#165).

**See also:** #140 (a pin quotes the prescribed bytes, so a reword is a pin break), #151 (a contract edit sweeps the sibling surfaces that restate it), and the Skill text anti-growth rules in `AGENTS.md`.

## 203. A Worker's Mid-Flight Rate-Limit Error Is Not the Session's Quota Wall

**Principle:** Family H (verify the real thing: the failure's live boundary, not a pattern match on its error shape).

**Trigger:** a subagent worker (or any delegated unit) dies with a rate-limit-class error partway through its work, while the parent session holds a live mandate it could stand down or pause.

**Rule:** a rate-limit error surfaced inside a delegated worker is evidence about that one call, not about the parent session's quota window. Before pausing the run or arming a resume carrier, run one cheap quota probe from the parent session; a probe that reads the window open means the failure was transient, and the correct recovery is a fresh worker relaunch that reuses the dead worker's fixtures and baselines, not a lane pause. Standing down a whole mandate on a worker-shaped error costs the idle window the probe would have saved.

**Why:** witnessed 2026-10-23 (playbook repo, exec run): a pick's first implementation worker died with a `1302` rate-limit error after roughly twenty-five minutes with zero code edits; the error's shape invited the quota-wall pause posture, but the parent-session probe read the window open with over two hours remaining, and a fresh worker relaunch with the prior worker's fixtures reused completed the task unchanged. Re-witnessed 2026-10-23/24 (playbook repo, authoring run): four panel workers launched as one parallel background batch died with provider streaming-recovery interruptions; the probe read the window open, and relaunching the failed lenses one at a time in the foreground completed each within the two-attempt budget, so a repeated same-shape failure across a parallel batch changes the launch shape before it spends the retry budget.

**See also:** #127 (probe the live boundary before riding a recorded reset; this extends the probe duty from pause postures to worker-failure recovery).

## 204. Flush Worker Outputs to the Session Home Before Any Context-Compaction Risk

**Rule:** a review round's worker outputs are durable state, not transcript state: the orchestrator appends each lens verdict (verbatim, with finding blocks) to the session-home round log as it returns, before launching the next worker or doing any other work. A round record is never synthesized from a summary of lost outputs; when outputs are lost anyway, the affected lenses re-run fresh rather than staging reconstructed evidence.

**Why:** witnessed 2026-10-23 (playbook repo, exec run): three of five Phase 3 lens results survived only as condensed in-context summaries after a context compaction, unrecoverable for verbatim staging; the honest remedies cost three full re-runs over the post-fix HEAD. Two compounding gaps: outputs never written to the session home mid-round, and a compaction landing mid-round.

**How to apply:** at review orchestration time, treat "worker returned" as incomplete until its output is on disk in the session home; batch staging document writes only after every contributed output is durably logged. If staging from condensed summaries is ever tempted, re-run instead, reconstructed evidence lines are fabrication-adjacent and fail the record's purpose.

**See also:** #201 (session-home sweep eligibility mid-run; same durability theme on the storage side).

## 205. Validate an Earlier Round's Record Against Its Own Round-Close Bytes

**Principle:** Family A (precision-critical values are re-derived from disk at validation time: a record binds the plan bytes of its own round, so the validation target is those bytes, not the working tree).

**Trigger:** running the staging validator over a non-final round's record (r1, r2) after later folds changed the plan file, so the working-tree digest no longer matches that record's `source_digest`.

**Rule:** materialize the round's own bytes with `git show <round_close_commit>:<plan path>` into a scratch path and pass that path as `--source-plan`; take `round_close_commit` from the record's seal entry re-read from disk, never from a remembered sha. Rewriting an earlier record's digest to the current bytes falsifies that round's provenance, and validating it against the tree fails for a reason that is not a defect.

**Why:** witnessed 2026-10-23/24 (playbook repo, authoring run): two earlier-round records refused on `source_digest` against the folded working tree; the first retry used a remembered commit and still mismatched, while the re-read seal's close commit produced the recorded bytes and the validator passed with no record edit.

**See also:** #92 (the closure record's digest moves with the fold; this lesson covers the records that must not move), #185 (`round_close_commit` binds where the certified bytes landed).

## 206. The Delta Round's Blind Probe Is the Only Instrument Over the Fold's Own Coverage Claims

**Principle:** Family C (verify by execution: a focused review's scope excludes the very claims the fold added).

**Trigger:** closing a focused delta round over a fold diff whose text makes coverage claims (fixture modes, pinned assertions, reachability wording), with the mandatory blind correctness-completeness probe looking like ceremony on an already-clean diff.

**Rule:** run the blind probe on a delta round with full-panel rigor and aim it at the fold's own coverage claims first. The focused panel judges the diff's internal consistency, not whether the coverage the diff promises would actually hold, so a hole the fold itself introduced (a fixture pinned to one landing mode where the sibling mode is the operative one, an assertion that cannot fire in the mode its motivating witnesses used) is invisible to the panel and reachable only by tracing or executing the promised coverage. A non-blocking gap the probe surfaces defers under the minimal-fold doctrine with an execution-time fix note; it is a residual, never a reason to re-fold a diff whose findings are already zero blocking.

**Why:** witnessed 2026-10-23 (playbook repo, authoring run r2): the fold pinned the warning-line fixtures to one landing mode while the plan's own motivating witnesses landed through the sibling mode, leaving that mode's warning arm uncovered; the focused panel rated the gap Low and would have passed it, and the mandatory blind probe surfaced it as its own Medium risk. The probe is the round's only instrument whose scope covers the promise rather than the prose.

**See also:** #74 (treat a zero-count success as unverified until the consulted tree is confirmed; #198 is its collection-count arm), #30 (read the check families before authoring; the same read-the-contract instinct applied to the round's own probe duty).

## 207. Dry-Run a Receipt-Consuming Audit Against the Receipt Form Before the Act That Freezes It

**Principle:** Family H (verify the real thing: exercise the auditor and the receipt grammar against each other before an immutable commit locks both).

**Trigger:** a workflow emits a receipt (a log line, commit-message token, ledger entry) that a later audit judges, and the act that carries the receipt (a landing, a removal commit) is about to run without the two having met.

**Rule:** before the landing or removal, run the audit over a rehearsal range containing the exact receipt form the run plans to emit. If the audit cannot resolve the form post-act, the form is fixed at claim time, when it is still cheap to change; a receipt whose witness requires the act's own output (a landing sha inside the commit that creates the landing) is unresolvable by construction and needs a different grammar, not a post-hoc repair.

**Why:** witnessed 2026-10-23 (playbook repo, exec run): two ad-hoc prompt-log prunes with self-referential receipts (`landing in this commit`) flagged REMOVED-WITHOUT-WITNESS after landing; the removal commit was the squash itself, immutable once landed, so the only recognized repair shape (a message-cited landing sha) could not be applied without rewriting landed main. Incident dossier and disposition live in the completed sibling `docs/history/backlog/completed/2026-10-22-prune-audit-landing-token-never-resolves.md`; its covering arm (the in-commit receipt witness, landed 2026-10-24) resolved the standing flags this lesson's witnesses contributed.

**See also:** #84 (the chained guard that let the failing audit reach the landing at all), #82 (re-derive guard constants; the same from-disk discipline applied to the receipt grammar).

## 208. Verify a Rolling-Log Entry Removal Against the File Tail Before Committing

**Principle:** Family H (verify the real thing: the post-edit file shape, not the edit intent).

**Trigger:** a rolling prompt log entry is removed by a scripted slice or a bulk text replacement, and the commit is about to run without a structural check of the result.

**Rule:** after removing a `## `-headed entry, verify the file tail before staging: zero remaining `## ` entry headers for removed entries, every `EXEC-PROMPTS-PRUNE` receipt line byte-intact and in order, and no orphaned body fragments glued under neighboring receipts. When a follow-up targeted edit is applied to content the script just rewrote, the stale-read refusal is the drift guard working: re-read from disk and redo the edit against the fresh bytes, never re-derive the old_string from memory.

**Why:** witnessed 2026-10-24 (playbook repo, 05:46 exec run, pick 2): a python-slice entry removal followed by a memory-derived Edit spliced the removed entry's body text under the receipt block (origin row path glued mid-sentence into a neighboring entry's Origins lines); the error was caught by a tail inspection (`tail`, plus a `## `-header count) before the commit, and the fix was one deletion against the fresh read. The structural check is two commands; the residue class is invisible to `git diff --stat` counts.

**See also:** #134 (learn commit clobber; the same stale-write-vs-fresh-read family), #202 (grep the touched spans before condensing; the same verify-before-write discipline over log text).

## 209. Prove a Pure Move With a Line-Multiset Equality Check

**Principle:** Family H (verify the real thing: content identity, not symmetric counts).

**Trigger:** a skill-text change claims to be a pure relocation (block moved between sections, no rewording) and the landing evidence is a diffstat showing equal insertions and deletions.

**Rule:** prove the move mechanically: diff the old and new files as multisets of lines (for example Python `Counter(old_lines) - Counter(new_lines)` versus the reverse; an empty difference both ways is the pass), and state the check and its result in the landing receipt. Equal insert/delete counts do not prove zero rewording; the multiset check does, and it costs one short script against `git show <tip>:<path>` versus the working tree.

**Why:** witnessed 2026-10-24 (playbook repo, 05:46 exec run, pick 2): the update-stacked-branches finalize-block relocation was landed on the strength of a line-multiset equality check (`removed == added`, empty both directions) plus the diffstat 14/14; the check caught nothing because nothing was wrong, which is the point - it converts "looks like a pure move" into a checkable claim without a review round, fitting a move the dispatch entry's contract sizes below panel weight.

**See also:** #205 (validate a record against its own round-close bytes; the same content-identity evidence class), #207 (rehearse audits against the receipt form; the same land-the-proof-with-the-act discipline).

## 210. Parallel Review Workers Never Mutate the Shared Working Tree

**Principle:** Family A (review evidence integrity: one reviewer's transient experiment must never surface as another reviewer's red).

**Trigger:** a review worker (execute-plan Step 1.2b intermediate pass or a Phase 3 lens) proving test discrimination by applying and reverting mutations to files in the run worktree while sibling workers run the same suite against the same bytes.

**Rule:** review workers treat the checked-out working tree as read-only for the whole pass, temporary apply-and-revert experiments included; a mutation or discrimination check that needs an edited file runs on a scratch copy of the repository (a plain copy or a separate worktree), never in the shared tree, and a worker that cannot obtain a scratch copy reasons about the mutation instead of applying it.

**Why:** witnessed 2026-10-24 (playbook repo, exec run, Task 1 intermediate review): the testing worker's four apply-and-revert mutation checks overlapped the correctness worker's suite runs in one worktree; the sibling observed a transient `OUTCOME: fail` with an output shape no settled version of the script could produce, and only mtime forensics plus a re-run on the settled bytes cleared it. The settled diff digest never changed; the red was pure overlap, and a less careful reviewer would have failed the pass.

**See also:** #204 (worker outputs are durable state; the same discipline on the evidence side), #90 (verify the tool contract before reading its exit code).

## 211. Verify an Applied Fix Against the Behavior It Names, End to End

**Principle:** Family A (a fold recorded as fixed is evidence only when the behavior it names is witnessed, not when the diff that claims it exists).

**Trigger:** a review fold fixes a display/parity defect by adding a config pin, flag, or guard to one stage of a multi-stage pipeline, and the surrounding fixtures exercise only the trivial name class the defect never touched.

**Rule:** before recording a fold as fixed, run the defect's own repro end-to-end against the changed surface and add the fixture that fails without the fix; when a review record or commit message asserts a fold, a later round (or the landing checklist) re-witnesses it in the diff before trusting the record.

**Why:** witnessed 2026-10-24 (playbook repo, exec run): an r1 fold added core.quotePath=false to the diff stage of a diff|check-ignore pipeline to fix octal-escaped warning paths, but check-ignore unquotes its stdin itself and re-quotes its own stdout, so the pin was a verified no-op and the octal form survived; the fix passed the whole suite because every fixture used ASCII names. The same pass's record listed another fold (fixture append-form) as applied with no diff witness; the next round's design lens caught both, one by end-to-end experiment and one by reading the diff against the record.

**See also:** #210 (review workers read-only; the same round's process discipline), #90 (read the tool contract, not the assumed pipeline semantics).

## 212. Run done_run finalize From the Checkout Holding the Run's done-session Scratch

**Principle:** Family D (state-first: a composed script's directory resolution is part of its contract; anchor to the checkout that owns the state).

**Trigger:** closing out an execute-plan run whose done-session scratch (`docs/tmp/done-session/`) lives in the run worktree, while the shell's cwd has reset to the primary checkout.

**Rule:** run `done_run.sh finalize` from the checkout that holds the run's `docs/tmp/done-session/` scratch (the run worktree); the `--manifest <path>` alternative is dead guidance (finalize parses the flag but no arm reads it), so the owner-checkout rerun is the sole remedy; re-export the acquire-step lock tokens in the same command, since the release arms read them from env. The finalize's checkpoint-refresh arm resolves the done-session directory from cwd even when `DONE_RUN_MANIFEST` is exported, so a primary-checkout invocation refuses "no run manifest found for run_id" and degrades the closeout to warning-only skips that leave a resume-shaped checkpoint behind.

**Why:** witnessed 2026-10-23 (playbook repo, exec mandate pick 1 closeout): the first finalize ran from the primary checkout with `DONE_RUN_ID` and `DONE_RUN_MANIFEST` exported and still refused the checkpoint refresh, remove, and manifest finalize (all warning-only, nothing mutated); re-running the identical command from the run worktree resolved the manifest and finalized cleanly. The `DONE_RUN_MANIFEST` env path resolves from any checkout, but the checkpoint arm's session-dir scan is cwd-relative, so the env alone never completes the closeout.

**See also:** #65 (run a validator from the checkout owning its state; the same checkout-scoping family), the lock-export lesson at the env-per-shell rule (acquire exports are absent in later tool calls).

## 213. Re-derive a Parked Run's Disposition From Live State Before Discharging the Resume

**Principle:** Family D (state-first: a parked payload copy and its memory note are a snapshot from park time, not a liveness record; the durable state file is).

**Trigger:** resuming a parked or deferred run (a pending re-arm with a payload copy, a budget-pause park, an operator-paused lane) by executing the parked artifacts directly.

**Rule:** before executing any step of a parked resume, re-derive the run's current disposition from the live surfaces: the state file (is the park field still set? does a takeover or child entry name this run?), the landing surface (does the artifact already sit at its landed home? does a certification record or seal exist?), and the worktree/branch census (do the run's homes still exist?). Any discharged signal (cleared park field, takeover entry, landed artifact, removed worktree) stands the resume down before any worker dispatch: report the peer's completion and consume only the residue the peer left.

**Why:** witnessed 2026-10-24 (playbook repo): a paused authoring pick was resumed from its parked payload while the recurring loop carrier had already taken the same resume, certified the plan, and landed it. The resuming session read the payload and the memory note (both written at pause time) but not the state file's takeover entry or the landing surface, and spent a full certification worker (~2.2M subagent tokens) on the moot round before the worker's own environment report (worktree path gone, plan already on main) surfaced the takeover. Re-witnessed 2026-11-01 (playbook repo, an idle-queue dispatch): a queued payload's inline cold-start assertion was stale by fire time because sibling runs had already advanced the registry state; the fire-time session re-derived the disposition from the durable state record and the task file's own window rule and acted on those.

**See also:** #86 (list the live carriers before arming one; the arming-side twin), #77 (a claim file is not evidence of liveness), #13 (re-derive before the final write; this is the same discipline at the resume's first step).

## 214. On Provider Dispatch Refusals, Probe Cheap, Then Go Sequential With Backoff

**Principle:** Family A (a heavyweight request's failure is not evidence about the path; discriminate before standing down or retrying blind).

**Trigger:** subagent dispatches fail with a provider network error ("Network connection failed for the provider request"), especially parallel heavyweight dispatches.

**Rule:** treat one refusal as a request-level outcome until discriminated: dispatch a trivial probe to the same path (a probe success proves the path is alive and the failure is size- or concurrency-specific, not an outage); fall back from parallel to sequential single dispatches with a backoff wait (order of a minute) between attempts; only after probe, backoff, and sequential retries all fail, take the in-session deciding-turn execution and record the refusals in the round's durable record. Never conclude a total outage from parallel heavyweight failures alone, and never re-dispatch the full panel in a tight loop.

**Why:** witnessed 2026-10-24 (playbook repo), twice the same day in independent sessions: one session's two parallel review-worker dispatches plus one retry all refused while a trivial probe succeeded and a single dispatch after a 90-second backoff succeeded; a peer session hit two refusals the same way and fell back to in-session deciding-turn execution, recorded in its certification seal. Premature stand-down and blind parallel retry were both live failure modes; the probe was the one-command discriminator. Third witness 2026-10-24 (playbook repo, a resumed execution run's targeted review round): three parallel dispatches were interrupted, then nine of the next ten sequential single dispatches with backoffs of 45 seconds to 4 minutes refused with the same provider error while a cheap quota probe read the window open each time; the one dispatch that went through took 18 minutes and returned a verified finding, and the remaining lenses ran in-session with mutation checks on a scratch copy of the reviewed files, the fallback disclosed in the round's record. The backoff ladder is a bounded retry, not a guarantee: cap the sequential attempts (three or four) and take the in-session fallback rather than spending the lane's window on refusals. Fourth witness 2026-10-27 (playbook repo, an exec run's review panel): two heavyweight review-lens dispatches each died mid-run (13-16 minutes in) on the same provider error while the attempt that survived was the identical lens re-scoped to a handful of named reads with a bounded checklist, finishing in under five minutes; when a retry is owed after a mid-run death, narrow the prompt's scope (name the exact regions, bound the tool calls) instead of re-sending the identical heavyweight body - the tight retry shrinks the per-request exposure window the failure rides.

**See also:** #213 (the deciding-turn fallback inherits the full step order), #77 (corroborate liveness before acting on a refusal; the same discrimination duty aimed at the provider).

## 215. The Dispatch-Fallback Deciding Turn Still Walks the Full Step Order

**Principle:** Family D (a fallback changes who executes, never which steps run; durability checkpoints bind the deciding turn like any other executor).

**Trigger:** a review round executed in-session after dispatch refusals, followed by landing and teardown in the same deciding turn.

**Rule:** the in-session fallback path inherits the replaced path's full step order: the certification-time record-durability checkpoint (commit the artifact bytes to the primary checkout's canonical home; mirror owned review records and sidecars from the worktree's gitignored homes to the primary homes) precedes the worktree removal, and the removal preflight and gate-removal run before the removal regardless of who executed the round. A deciding turn that jumps from certification to teardown destroys exactly what the checkpoint exists to preserve.

**Why:** witnessed 2026-10-24 (playbook repo): a deciding-turn certification round landed its plan and recorded the seal, then removed the run worktree before the record-durability checkpoint ran; the r1-r3 review-record series staged only in the worktree's gitignored reviews home was destroyed, and the seal had to witness the series gap with the last round declared authoritative. The machinery was present and correct; the deciding turn skipped its ordering.

**See also:** #214 (the fallback's dispatch recipe), #139 (hand the removal gate the records and verify the removal).

## 216. A Bounded State-File Field Asserts Its Bound After the Write

**Principle:** Family D (state-first: a documented bound is part of the write's success condition; a write that succeeds byte-wise can still violate the field's invariant).

**Trigger:** any scripted append to a field with a documented cap (here: the scheduler state file's `children[]` keep-last-20).

**Rule:** slice the concatenated list, not the appended element - `(old + [new])[-20:]`, because `old + [new][-20:]` binds the slice to the one-element literal and caps nothing - and re-read the file after the atomic replace to assert the count. A plain append with no trim violates the same cap and is caught by the same post-write assert.

**Why:** witnessed 2026-10-24 (playbook repo), twice in one session: a Step 6 rewrite appended with the cap applied to the literal only, growing the field to 39 entries against the documented 20 until a separate fix pass noticed and trimmed; the closeout's later plain append pushed the field to 21 with no trim at all. Both writes reported success; only a post-write count catches the violation at the write site.

**See also:** #13 (re-derive before the write; this is its assert-after twin), the `children` field paragraph in `agents/skills/maintenance/state-file.md` (the cap of record).

## 217. A Shared-Index Squash Landing Commits the Whole Index: Verify the Staged Set Is the Run's Own Immediately Before the Landing Commit

**Principle:** Family B (shared-checkout assumption; the staged set you commit is whatever the shared index holds at commit time, not whatever you meant to stage).

**Trigger:** a squash landing built with `git merge --squash` (or any commit form that consumes the shared index) in a checkout other sessions share, especially one where you staged, stashed, or unstaged paths around a blocked merge.

**Required behavior:** immediately before the landing commit (not just before the merge), re-derive the staged set with `git diff --cached --name-only` and require every path to be one the run owns; a foreign staged path is parked for its owner, never swept into the landing. Stash/unstash cycles around a blocked merge make this check load-bearing: a stash restored with `--index` puts the peer's dirt back into the exact index the next commit consumes. This is the landing-commit sibling of the own-edit word-diff check on corpus commits (#134): that check guards authored record commits, this one guards the landing's mechanical index consumption.

**Why:** witnessed 2026-10-25 (playbook repo): a peer session's staged `document-registry.md` deletion blocked a squash merge; the landing session stashed the dirt, merged, restored it with `--index`, then ran the landing commit, and the peer's staged deletion landed inside the run's landing commit (caught in the post-landing self-audit; the diff sat recoverable in a stash). A pre-commit `--cached` cross-check would have refused it at the write site. Re-witnessed 2026-11-01 (playbook repo, an exec run's record commit): the sweep is not landing-only: a receipt commit made with a plain (non-pathspec) `git commit` in the shared primary consumed the shared index wholesale and landed a peer session's pre-staged deletions of three backlog rows alongside the receipt; base-branch immutability forced an additive restore commit for the repair, and the owning peer must re-stage if still intended. The `git diff --cached --name-only` ownership check applies to every commit in a shared checkout, record commits included, not only landing commits.

**See also:** #6 (build the squash from a tree merged with the current default branch), #134 (own-edit check for record commits; same foreign-content class, different commit surface), lesson 545 in the user corpus (derive a landing commit's pathspec from the branch delta).

## 218. Untracked Per-Worktree Runtime Config Silently Poisons Cross-Worktree Scans

**Principle:** Family H (verify the real thing, not the abstraction: a scan that resolves per-worktree config must treat missing config as data about the worktree, not as an inconclusive verdict about the target).

**Trigger:** any tool that iterates registered worktrees and resolves a path from each one's local facts document (the registered-manifest scan in `scripts/execution_claim.sh` is the witnessed instance); diagnosing an "inconclusive" scan refusal that names no offending worktree.

**Rule:** when a per-worktree config file is untracked (fresh `git worktree add` checkouts lack it), a cross-worktree scan must report WHICH worktree refused discovery, not collapse the whole scan into one inconclusive verdict. The landed verdict line carries the failure family (`facts` or `symlink`), the cause phrase or manifest path, and the registered worktree as tab-separated fields, so consumers print the attribution without re-scanning. On an older build, probe each worktree's config path individually (`ls <wt>/.ai-playbook/facts.md`) before concluding anything about the target. Separately, an identical record-mirror copy at the primary checkout makes single-target scans ambiguous by construction. The scan counts a byte-identical primary-side mirror as one identity (`cmp -s` strictly after the symlink gate), retaining the canonical non-primary worktree; differing bytes or a second non-primary manifest stay multiple. That diagnosis (diff mirror vs target; identical content, no information lost) applies only to those refusing shapes: pause the mirror for the gate call and restore it in the same command chain.

**Why:** witnessed 2026-10-25 (playbook repo, 03:00 exec carrier resuming a task-complete java run): the dead-run conversion arm refused "registered-manifest scan is inconclusive (facts refuse discovery, or a symlinked manifest path)" with no worktree named; two unrelated worktrees (one abandoned residue, one an active peer run) lacked the untracked `facts.md`. After additive copies fixed discovery, the scan refused "ambiguous" because the run's primary-side record mirror counted as a second manifest. Each refusal cost a diagnosis round; neither refusal named its cause. Repaired 2026-10-26 (playbook repo, the dead-run conversion plan's Task 2 boundary): the scan attributes both inconclusive legs and collapses the byte-identical primary mirror.

**See also:** #43 (re-derive from disk at each step boundary), #160 (the claim gateway's atomicity; the same surface).

## 219. A Heading-Sliced Section Parser Must Treat Slice End as a Terminator, Not a Failure

**Principle:** Family B (error-policy direction: the end of a data slice is valid input, so it routes to termination, not to an exception).

**Trigger:** scripting a mechanical resolution over a conflict or diff in a rolling log whose sections are delimited by headings (resolving a rebase conflict over `docs/history/backlog/PLAN-PROMPTS.md` is the witnessed instance), or writing any "take from here to the next `## ` heading" slice.

**Rule:** when a section is delimited by the NEXT heading, the last section in the slice has no delimiter: treat end-of-slice as the terminator in the same branch as a found heading. A `StopIteration` (or a not-found refusal) from the next-heading search on the final block is a parser bug, not data corruption; the bounded response is to add the end-of-slice arm and rerun, never to conclude the log is malformed.

**Why:** witnessed 2026-10-25 (playbook repo, rebase-conflict resolution over the plan-prompt log after a peer landing): the resolution script located each entry by the next `## ` heading; the pruned entry was the LAST block in the conflict slice, the search found no following heading, and the script died on StopIteration mid-resolution, costing one round before the terminator arm was added.

## 220. A Compact H-M Clock Token in a Scheduling Ask Is a Time, Not a Range: Confirm by Echoing the Concrete Clock Time

**Principle:** Family J (interpretation of an operator's compact notation: resolve a shorthand against its most local reading, and confirm by restating the resolved value, never by paraphrasing the shorthand back).

**Trigger:** a scheduling ask whose time token has the shape `H-M` or `HhMM` with an am/pm marker (witnessed: "schedule at 9-17 pm" / "9h17 pm").

**Rule:** read a compact hour-minute token as the single time `H:MM` (with the am/pm marker applied), never as a range or a pair of endpoints. When the resolved time still admits a second reading, ask one confirmation question whose options each name the CONCRETE resolved clock time (for example "21:17"), not a restatement of the shorthand; arming a carrier on an inferred reading is the failure shape.

**Why:** witnessed 2026-10-24/25 (playbook repo, one-shot exec carrier arm): "9-17 pm" was read twice wrongly (first collapsed to a single 21:00 fire, then re-read as an hourly 21:00-16:59 window), each misread patched in place after an operator correction; the intended reading was 21:17. Two avoidable correction rounds; both would have been prevented by echoing "21:17" before the first arm.

## 221. Amend an Armed One-Shot Carrier In Place: the Patch Preserves the Id the Records Already Name

**Principle:** Family I (mutation over recreation for stateful references: when durable records already name a resource id, correct the resource, never replace it).

**Trigger:** correcting a just-armed schedule carrier after an operator correction to its time, window, or payload.

**Rule:** patch the existing carrier's cron expression, title, and payload through the update primitive instead of deleting and recreating it; the automation id stays stable, so the memory note, the scheduler state references, and any receipts naming the old id stay valid across the correction. A delete-and-recreate mints a new id and strands every record that named the old one.

**Why:** witnessed 2026-10-24 (playbook repo, exec carrier automation-d04dd5bc corrected twice in place, from a single 21:00 one-shot to an hourly window and back to a 21:17 one-shot): each update primitive call changed cron, title, prompt, and recurrence in one step while preserving the id, so the one memory note tracked the carrier across both corrections with only its time line refreshed.

## 222. A Machine-Parsed Prose Line Is a Grammar Surface: Extend It Inside Its Grammar and Put Explanatory Prose in a Sibling Bullet

**Principle:** Family H (verify the real thing: the consuming script's self-test over the edited line, not the line read as prose).

**Trigger:** editing a skill-text line that a script locates by prefix or parses by grammar (the review-staging `- Closed enums:` line that `scripts/validate_review_staging.py --selftest` reads is the witnessed instance), or any bullet whose body a validator, hook, or pin suite tokenizes.

**Rule:** keep the parsed line's grammar exact: extend it only with segments the grammar admits, and put authority notes, rationale, or pointers in a new sibling bullet, never as a parenthetical on the parsed line. Run the consuming script's self-test in the same edit, before the commit; a green self-test is the only proof the line still parses, because the prose still reads fine to a human after the break.

**Why:** witnessed 2026-10-25 (playbook repo, plan review-loop-staging-vocabularies Task 1): an `(authority: ...)` parenthetical appended to the Closed enums line made the validator self-test report "no Closed enums line in the skill text" (rc 1) while the bullet read correctly; moving the sentence to its own `- Enum authority:` bullet restored rc 0. See also #219 (the parser side of the same contract).

## 223. A Migration Manifest Destination Is a Presence Contract Until the Teardown Gate Consumes It: Consolidate Migrated Artifacts After gate-removal, Not Before

**Principle:** Family D (recover and land through the owning machinery against current state: the teardown gate verifies the destinations the migration recorded, byte-presence only, so the recorded paths must still exist when it runs).

**Trigger:** a closeout migration collision-renamed a run artifact into a `.wt-` twin (a review seal, a manifest, a state file) and the run wants to merge the twin's content into its canonical sibling before tearing the worktree down.

**Rule:** run `worktree_closeout_migrate.py gate-removal` while every recorded destination is still on disk; merge or delete a collision twin only after the gate prints `OUTCOME: pass`. When the merge already happened, recreate the recorded destination path (the gate checks presence, not content) rather than editing the gate or the manifest. A twin merged elsewhere reads as `migrated artifact(s) missing under the target`, and a presence refusal is bounded-repair territory, never a reason to touch the validator.

**Why:** witnessed twice 2026-10-25 (playbook repo, both picks of the 01:18 exec carrier): the code-family seal block was merged from the `.wt-` seal copy into the primary seal file and the copy deleted; gate-removal then refused both teardowns naming the missing recorded destination, and recreating that path passed the gate. Third witness (2026-10-30, self-heal-before-unknown-remedy execution run): a merge-lock collision put the round's certification-seal block only in the `.wt-1` twin; after the block was installed at the canonical path, the gate still refused with the same missing-destination shape, and the clearing remedy was restoring the twin BYTE-IDENTICAL to its migrated bytes (not a presence-only stub) - when the twin's true bytes are known, recreate with content. The collision-rename itself is tracked in docs/history/backlog/2026-10-21-closeout-migration-collision-renames-run-mirrors.md. See also #177 (the gate's guard-propagation side).

## 224. Prove a Hold's Owner Dead from the Host Session Store Before a Takeover

**Principle:** Family D (state-first: the liveness verdict is read from a durable host record, never inferred from a stale claim stamp or a recent commit).

**Trigger:** deciding whether to reclaim a foreign execution claim or finish another session's paused execute-plan run (D-9 forbids reclaiming a live holder and requires a liveness proof for a dead one).

**Rule:** derive three facts from disk before the takeover: (1) the holder session's last activity from the host session store (`~/.zcode/cli/db/db.sqlite`, `session.time_updated`, the row matched by its title or slug); (2) that the silence spans the holder's own quota-window expiry (its recorded reset time plus the window) while sibling sessions in the same store are writing; (3) that the automation listing holds no armed successor carrier for that run. Only all three together are the proof. A stale `updated:` stamp on the claim is not death (a holder mid-round leaves its claim un-refreshed), and a recent commit on the run branch is not life (the witnessed holder committed four minutes before it died).

**Why:** witnessed 2026-10-24 (playbook repo, the 22:00 one-shot carrier): the stranded run had its r2 folds committed at 21:29 and its r3 record written, its claim still read `updated: 16:09`, and nothing on the run branch distinguished mid-closeout from dead; the session store showed the holder's last write at 21:33 against a window that expired about 21:52 while two sibling 22:00 sessions were active, and the listing held no successor, so the takeover landed the certified work (`2d592af72`) instead of opening a fresh plan beside stranded certified work.

**See also:** #110 (the resumed run re-binds the inherited claim before work); the directives home D-9 (bounded wait, then holder identity and a next action).

## 225. A Review Wave's Record Pair Is Written Before the Wave Boundary Pause, Because Worker Transcripts Die With the Session

**Principle:** Family D (state-first: the durable record of a completed round is the staging record pair on disk, never the orchestrator's context or the workers' returned text).

**Trigger:** a review round has completed (every worker returned, the address pass is committed) and the budget gate at the next wave boundary says pause; or any pause signal arrives between a round's close and its record write.

**Rule:** the wave boundary is reached only after the closing round's staging record and sidecar are written and validated; the gate is probed after that write, never before it. The round's inputs (each worker's returned findings, verbatim or near-verbatim) are appended to the round's session log as each worker returns, so a record that still has to be written at resume is composed from logged worker output rather than from a one-line manifest summary. A WIP checkpoint commit does not cover this: review records and session logs are gitignored, so the only durable copies are the ones the session writes to disk itself before it stops.

**Why:** witnessed 2026-10-24 (playbook repo, execute-plan Phase 3): a full five-worker round completed, its nine folds landed as the fix commit, the manifest took a four-line summary of the lenses, and the budget gate paused the run at the r2 wave boundary before the r1 record pair existed; the round's log held only its launch header. The resume session had to reconstruct nine findings, their anchors, and the panel counts from the summary and the fix commit's diff, disclose the reconstruction in the record's provenance, and still spend a validator repair cycle on the per-worker budget, all of which one record write at the round's close would have made unnecessary.

**See also:** #215 (the deciding-turn fallback still walks the record-durability checkpoint before teardown; this lesson is the same checkpoint at the pause boundary), #167 (mirror untracked run records out of the worktree before closeout stages run), #127 (probe the boundary before riding a recorded reset; the probe comes after the record write, not before).

## 226. A Claim Release Whose Operand Origin Was Deleted Rebuilds the Operand From the Landing's Parent, Not From Memory

**Principle:** Family D (state-first: re-derive the release operand from git object storage; the gateway validates the operand file, and a paraphrased copy risks failing that validation).

**Trigger:** releasing an execution claim after the claim's plan operand (a covered backlog row) has been deleted by its own landing - the sanctioned covered-row lifecycle leaves no on-disk operand, and the release refuses on an unreadable or basename-mismatched file.

**Rule:** restore the exact origin bytes from the landing's parent commit (`git show <landing>^:<origin-path>` written into a gitignored scratch directory under `docs/tmp/`), keep the original basename (the gateway derives the artifact slug from the FILENAME only), run the release against that restored path, then delete the scratch file in the same command chain. Never hand-retype the operand: the restored bytes are the record the claim was taken against.

**Why:** witnessed 2026-10-24 (playbook repo, ad-hoc exec run): all three entries' origin rows were deleted in their own landing commits, so every closeout's claim release refused "plan operand not readable"; the workaround (origin bytes via `git show <landing>^:<path>` into a gitignored scratch dir, release, remove scratch) worked first try for all three, and the slug-from-filename derivation is why the basename must survive the restore.

**See also:** #212 (run closeout tooling from the checkout holding its scratch), #218 (untracked per-worktree runtime config poisons cross-worktree scans; the gitignored facts copy is the same class of untracked dependency).

## 227. A Landing's Recorded Sha Comes From the Landing Receipt, Never From the Base Tip After Peers Land

**Principle:** Family D (state-first: the landing sha is a value the landing step produced and recorded; the base branch tip is a shared moving pointer that any peer landing advances).

**Trigger:** writing a record field that names "the commit this run landed" (a terminal receipt's `last_commit_sha`, a scheduler-state `landed_as`, a memory line, a closeout report) while other sessions land on the same base branch.

**Rule:** take the sha from the landing's own output (the `land-worktree` receipt, or `git log --format=%H -1 -- <archived plan path>` scoped to a file only this landing touched), then verify it with `git merge-base --is-ancestor <sha> <base>` and confirm `git show --stat <sha>` lists this run's files. Never resolve `<base>` or primary-checkout `HEAD` as the landing sha: a peer landing between the squash and the record write turns that value into the peer's commit.

**Why:** witnessed 2026-10-25 (playbook repo): a terminal receipt first recorded the base-branch tip, which was a peer's landing that had arrived minutes after this run's squash; the correction came only because the run's memory line already named the squash. The re-derive-from-disk rule was satisfied in letter (the value came from disk), but the wrong disk pointer was consulted.

**See also:** #132 (committed witness lines never cite branch-local shas; this lesson is the landed-side twin), #86 (peer carriers landing in the same window are the normal case, not an anomaly).

## 228. An Absence Conclusion Resolves on the Duty's Write Surface

**Principle:** Family D (state-first: an existence check is only as good as the read surface it resolves; a near-miss reconstructed path reads as a silent false absence, and a null recorded field silently redirects the read to a surface the run never wrote).

**Trigger:** concluding "no claim / no manifest / no progress" from a path reconstructed from memory, or through a recorded-field fallback, immediately before a dispatch-grade decision (lane release, failure marking, re-dispatch).

**Rule:** take the read path from the owning skill's pinned text at decision time, never from working memory; when a checker resolves through a record's additive field and the field is null, resolve the missing pointer through the record's surviving companions (the claim's `branch:` line plus a worktree listing) before reading "absent"; and an active-run cross-check (recent branch commits, dirty worktree) outranks a stale-or-absent pointer read, so when the two disagree, stop and re-derive instead of dispatching into the disagreement.

**Why:** witnessed 2026-10-25 (playbook repo, scheduler turn): three wrong-surface reads (a nonexistent claims directory taken from memory, a date-prefixed manifest glob, the primary checkout's plan file for a worktree-scoped run whose entry carried no worktree field) all agreed the run was dead; the turn deleted the armed carrier and created a re-dispatch, then the run's own worktree listing (a branch commit 75 minutes old, 21 checked boxes, a manifest written 2 hours prior) contradicted it, and the dispatch was withdrawn pre-fire.

**See also:** #27 (absence findings name their byte source; the vintage sibling), #15 (re-derive a memorized procedure's owning file at execution time), #226 (rebuild a deleted operand from the record, not memory).

## 229. Attribute a Run Worktree Through the Session Store's Message Payload

**Principle:** Family D (state-first: the attribution is only as good as the read surface it resolves; a UI task index answers "which session", never "which worktree").

**Trigger:** needing the owning session of a run worktree, branch husk, or detached checkout (an operator asks which live session to prompt for cleanup) and reaching for the task or UI index first.

**Rule:** the task index's `workspace_path` records only the primary workspace and never a run worktree, so it cannot bind a worktree to its session. Search the host session store's message payload for the worktree or branch name; the `message` table's payload column is `data` (there is no `message` column; check the schema before the first query of the day). Join `session` for the title, and bind subagent sessions to their carrier with a `session.parent_id` self-join. Treat a missing per-session model-io rollout file as rotation, not death: retention holds about three files and rotates mid-investigation; liveness comes from the session row's `time_updated` plus repo-side activity.

**Why:** witnessed 2026-10-25 (playbook repo, operator-asked stale-worktree sweep): the task-index query over worktree-shaped workspace paths returned zero rows for sessions that existed; a `m.message` column guess errored until the schema read showed `data`; and two live sessions' rollout files vanished between greps while their owners kept landing commits.

**See also:** #224 (prove a hold's owner dead from the same store before a takeover), #228 (absence resolves on the duty's write surface), #78 (prove branch landedness from witnesses).

## 230. Write the Pre-Restart Record and Execution Log Before the Long Run

**Principle:** Family A (a relaunched worker re-derives run state from disk records, never from the dead pass's lost context).

**Trigger:** a delegated execution worker with in-flight uncommitted work about to start a long, mostly silent validation span (a full test-suite run) that a worker death could interrupt.

**Rule:** before the long span, append a pre-restart record to the execution log: branch tip, in-flight dirty paths, and per-suite pass/fail state, each item checkable against disk (git status, a targeted rerun) so the next pass can verify it, adopt the in-flight diff wholesale, and skip re-derivation. Append a progress entry as each verification step completes, never only at pass end. Treat a long silent command as a death risk in itself: a run producing no output for longer than the worker runtime's inactivity window can kill the worker mid-validation, so prefer chunked or progress-emitting invocations, or at minimum make the span resumable before starting it.

**Why:** witnessed 2026-10-25 (playbook repo, exec run, Task 1): the first implement worker died inside a multi-minute full-suite run (inactivity cutoff) and the second on a provider network failure; the third pass resumed without loss because the pre-restart record had been written early and verified against disk, and the log carried each completed verification as it happened.

**See also:** #204 (flush worker outputs before compaction risk; the same write-early discipline on the review side), #203 (relaunch a dead worker with reused fixtures instead of pausing the lane), #201 (keep the run's logs worktree-side, where the sweep cannot eat them).

## 231. Classify Concurrent-Run Suite Failures by the Alone Re-Run

**Principle:** Family A (a transient failure while sibling agents are active is a contention signal; the alone re-run is the classifier, not regression triage).

**Trigger:** a test suite fails with transient low-level errors in temporary fixtures (for example git init or scratch-repo setup) while sibling workers or review agents are active on the same machine.

**Rule:** before triaging the failures as regressions, re-run the failing suite alone with no concurrent agents. Alone-clean plus dirty-under-concurrency is the contention verdict: record it as contention and spend no regression triage on it. Read-only siblings do not exempt a run: agents that never touch the shared tree can still contend at the machine level (concurrent temp-repo git operations), so keeping review workers read-only does not make concurrent suite runs contention-free.

**Why:** witnessed 2026-10-25 (playbook repo, exec run, Task 1): a combined two-suite validation run concurrent with two read-only review agents produced fifteen transient git init failures in temp fixtures; the failing suite re-ran alone clean, so the failures were contention, not regressions, and no triage of the code under test was spent on them.

**See also:** #210 (review workers never mutate the shared working tree; this is the residual contention shape that discipline does not remove), #195 (a repeated refusal under concurrent writers is a race signal; switch mechanism, not retry).

## 232. Capture Fixture Priors Before Any Test Poisons the Ambient Environment

**Principle:** Family E (temporal/ordering invariants: a state snapshot taken after a mutation is not a prior; capture order and cleanup-registration order decide who restores last).

**Trigger:** a combined multi-suite run fails with one fixed failure set while solo and order-flipped runs are clean; or writing a test that mutates ambient process state (environment variables, cwd) under a snapshot-and-restore fixture harness.

**Rule:** classify first, then order the restore. (1) The alone re-run (#218) separates contention only when the failure set drifts between runs; an identical failure set across repeated combined runs is deterministic, so the next probe is the order-flipped combination. Order-sensitivity plus clean solo runs is in-process state leakage, and the locator is a grep of the preceding suite for ambient-state mutation, not triage of the failing fixtures. (2) A harness that snapshots-and-restores ambient state must capture priors before any test body in the same process mutates that state. A test that must mutate earlier captures the real priors itself and registers its restore before the harness registers its own, so the LIFO cleanup order still leaves the harness's restore as the last write; alternatively the mutation moves after the capture point.

**Why:** witnessed 2026-10-25 (playbook repo, exec run, Task 2): a run-added environment-isolation test set a sentinel GIT_DIR in its setUp before the shared fixture mixin captured priors, so the mixin's teardown restored the poisoned value into the process and every later fixture's git subprocess failed, in wrapper-first combined runs only. Two combined runs produced identical failure sets; solo and reverse-order runs were clean, which ruled out contention and sent the grep to the poisoning setUp.

**See also:** #218 (the alone re-run as contention classifier; this is its deterministic-set sibling), #159 (hermetic fixture env is the inbound direction, host state leaking into fixtures; this is the outbound one, a test's mutation leaking to sibling tests).

## 233. A Detached Worktree Is Removed on a Liveness Conjunction

**Principle:** Family A (state facts are re-derived from the repository at the point of action); detachment is a HEAD state, not an activity state.

**Trigger:** a cleanup decision over detached-HEAD worktrees (peer scratch checkouts, pins or tool-home worktrees) that look maximally dead: clean, branchless, and sitting at an ancestor of the default branch.

**Rule:** removal safety is a three-conjunct test, and detachment is none of them. (1) Clean: `git status --short` is empty. (2) Zero-loss: the detached commit is an ancestor of the default branch (`git merge-base --is-ancestor HEAD <default>`), so removal strands no commit. (3) Liveness: a linked worktree's `.git` file (a file, per #39) carries the creation mtime. A HEAD commit dated at or after that mtime is the re-point witness: a worktree created or re-pointed inside the active window is live peer work and stays, however dead the topology makes it look. Detached means only that no branch pins the checkout. A worktree showing no re-point across the peer-activity horizon graduates to `git worktree remove`, which carries none of the branch reconciliation #79 owns.

**Why:** witnessed 2026-10-25 (playbook repo): an operator removal question over two detached worktrees, both clean and ancestral; the `.git` mtimes (18:02, 19:27) and detached commits (19:01, 19:27) showed one re-pointed after creation and one created minutes before the decision, so "detached therefore abandoned" was wrong for both.

**See also:** #200 (branch-bearing lane teardown re-derives liveness from probes and mirrors, not topology), #229 (owner attribution through the session store when one exists), #39 (the link file the mtime witness reads), #79 (tracked-file reconciliation before worktree removal).

## 234. A Prune Receipt Shares Its Commit With the Removal It Receipts

**Principle:** Family D (state-first: a receipt is a record-bearing claim about repository state; the state must hold in the commit the receipt names, and the prune auditor reads per commit, not per branch).

**Trigger:** closing an EXEC-PROMPTS or PLAN-PROMPTS entry: the prune receipt (`EXEC-PROMPTS-PRUNE: <slug> -> landing in this commit`) is being appended while the entry span or covered origin row is deleted.

**Rule:** the removal and its receipt share one commit. Delete the entry span (or origin row) and append the receipt in the same commit, then run `check_prompt_log_origins.py --prune-audit --base <merge-base>` before landing and require PRUNE-OK with zero warnings. On a pre-squash branch the two edits sit in separate commits, so squash them (soft-reset to the fix commit and recommit) until receipt and removal are one; `RECEIPT-WITHOUT-REMOVAL` is the receipt-without-removal half, `REMOVED-WITHOUT-WITNESS` the removal-without-receipt half.

**Why:** witnessed 2026-10-25 (playbook repo, interactive exec run): a receipt was appended while the entry stayed dispatchable at top of log with its orientation greps invalidated (panel-caught); the fold put the removal in a second commit and the audit refused `REMOVED-WITHOUT-WITNESS` until the two rider commits were squashed into one; the next pick read the same warning pre-emptively and pruned the span before the panel ran.

Second witness 2026-10-28 (playbook repo, interactive exec run): the receipt was planned as a separate pre-landing edit rather than riding the removal commit, and the rebuilt branch held the receipt unstaged; the focused review panel caught it by running the live audit at the branch tip (`REMOVED-WITHOUT-WITNESS`, exit 1) before any landing, and squashing receipt and removal into one commit turned the audit green. The same incident added a capture surprise: the rebuild's pathspec commit landed the whole staged index instead of its single named file, leaving the receipt behind (unreproducible in isolated vanilla-git and linked-worktree probes at the same version, so the operative defense is verification, not mechanism trust: re-derive what a commit captured with `git show --stat` before building on it, #227's verify arm).

Third witness 2026-11-02 (playbook repo, exec resume carrier run): the landing refused `RECEIPT-LINE-REMOVED-WITHOUT-WITNESS` because a later commit had rewritten the receipt line, and the first rebuild soft-reset to a point one commit ABOVE the removal commit, which recreated the rewrite pair (removal in one commit, receipt in the next) and refused the audit again; the reset point must precede the REMOVAL commit, not merely the receipt rewrite. The working rebuild used disjoint-path commits (a scripts-only fold commit, then one combined commit carrying the removal, the receipt, and the residual rows), leaving the certified tree bytes unchanged.

**See also:** #62 (re-derive the audit's flag grammar at invocation), #227 (a landing's recorded sha comes from the landing receipt).

## 235. A Dead Worker Channel Routes the Review Panel Through Nested Recovery

**Principle:** Family H (verify the real thing: separate channel outage from quota pressure with a probe, then route through the sanctioned recovery path instead of improvising or stalling).

**Trigger:** repeated subagent review-worker dispatches failing with provider transport errors while the driving session itself runs fine.

**Rule:** after two failures, probe quota once (healthy quota plus repeated transport errors is a channel outage, not pressure), back off boundedly, then run the focused panel as the doing-code-review nested-recovery path: the orchestrator runs the lens passes inline, the staging record discloses the recovery, `Review mode:` takes a declared enum value (`verification-only`; no nested-recovery value exists), `Last fix commit:` carries the bare full sha in both record and sidecar, and the r1 sidecar's `extensions.convergence.self_heal_attempt.status` is `unused` (`unknown` is only for later rounds reading a prior record). The landing receipt cites that record.

**Why:** witnessed 2026-10-25 (playbook repo, two ad-hoc landings in one exec run): seven dispatch failures over roughly eight minutes with the quota probe reading continue throughout, and a same-day peer landing recorded the same degradation with the same parent-inline recovery; the first recovery record failed validation three times, on the review-mode enum, the self-heal status, and a sha-with-prose metadata value.

**See also:** #62 (re-derive the validator's declared enums at record-write time, not from memory).

## 236. Digest-Verify Tool-Written Bytes in the Staging Shell Before the Commit

**Principle:** Family A (precision-critical values are re-derived at the moment of use: the bytes a commit will carry are digested by the staging shell itself, never trusted from the writing tool's success report).

**Trigger:** an agent-tool file edit (plan body, disposition section, lesson) followed in the same turn by a shell `git mv`/`git add`/`git commit` of that same path.

**Rule:** before staging, re-read the edited file inside the committing shell and compare its sha256 against the expected bytes (the receipt or pre-computed digest); on a mismatch, or on a pure-rename diff (`R100`) where an edit was expected, stop and re-stage from the verified bytes. Never diagnose staged content from the writing tool's success message.

**Why:** witnessed 2026-10-26 (playbook repo, execute-plan Phase 4 archive pass): the editor reported the disposition section written, but the same turn's `git mv` staged pre-edit bytes and the archive commit landed as a 100% rename without the fold; the amend re-staged the real bytes. The same session saw `ls` report a populated directory as empty minutes before listing it in full, so the stale view is real, not hypothetical.

**See also:** #108 (an evidence digest comes from the bytes on disk), #43 (per-call shell resets mask which checkout staged a write).

## 237. A Mandated Scan Is Green Only Over Its Own Roots

**Principle:** Family H (verify the real thing, not the abstraction: a gate's pass covers the paths that gate reads, and a publish-time gate over a wider set is the real check for everything outside those roots).

**Trigger:** a per-commit hygiene or lint mandate whose scanner reads a declared subset of the tree (roots or globs), beside a release or publish gate that scans the whole published result.

**Rule:** before trusting a commit-time pass for a file, check whether the file sits inside the scan's declared roots; when it does not, run the publish-scope mode (the explicit file list or the full tree) over that file before committing. Treat the scope gap itself as a backlog row; do not widen the exclusion list at release time to make the publish gate pass.

**Why:** witnessed 2026-10-26 (playbook repo, release of 620 commits): the default public hygiene scan reads `agents/skills` and `projects` only, so six tracked ledger receipts under `docs/history/` carrying absolute home paths passed seven mandated pre-commit scans across four days and surfaced only at the release privacy gate, which scans every published blob. The gate's failure line named all 1342 scanned paths, so the real two hits took a manual reproduction to find.

**See also:** #238 (the record contract that let the receipts leak), #178 (a pre-existing scan failure at the merge base reorders a run).

## 238. A Record Contract Masks Every Field, Not One Named Path

**Principle:** Family C (shared-artifact coordination: a tracked record's content contract is the producer's whole output surface, and a clause binding one field leaves every other field to the writer's habit).

**Trigger:** a tracked ledger or receipt whose header contract says one field is repo-relative (a plan path) while other fields carry command strings, captured stdout, or paths copied from the environment.

**Rule:** write the contract over the whole record: every embedded path, command string, and captured output uses the ledger's placeholder tokens (`<primary-checkout>`, `<source-worktree>`) or a repo-relative form, and the producer step says so. When some receipts already mask and others do not, fix the contract sentence, not only the receipts; the next writer reads the header, not the history.

**Why:** witnessed 2026-10-26 (playbook repo): the certification-seal landing diagnostic ledger's contract named only `plan_path` as repo-relative. Receipts written from the procedure's placeholder commands resolved `git -C <primary-checkout>` to real sibling-worktree paths in six of eleven receipts while five kept the token, and the release privacy gate refused the whole publish until the six were masked. Second witness 2026-11-01 (playbook repo, release of 656 commits): receipts minted after the masking contract landed still carried resolved sibling-worktree paths in seven entries; the header-contract fix bound writers who read the header, not the producer steps minting later legs, so the contract sentence alone did not stop recurrence and the publish gate remained the only working detector.

**See also:** #237 (the commit-time scan that never read the ledger), #148 (a stated shape contract binds the scan to the type level).

## 239. Recover a Mid-Run Branch From a Peer Base-Branch Rewrite With a Cherry-Pick of the Branch Range

**Principle:** Family D (state-first: the branch's commits survive in object storage even after the base rewrite unreachables them; recovery re-derives from git, not from rebase mechanics).

**Trigger:** mid-run, the base branch tip moves via a peer history rewrite (amend-style), so the run branch's old base is no longer reachable, its already-landed twin commits vanished from the base ancestry, and their content survived.

**Rule:** do not rebase the run branch onto the rewritten base: the merge-base predates the rewrite, so rebase replays the whole shared history (hundreds of commands) and must be aborted. Recover with `git cherry-pick <old-base>..<branch>` onto the rewritten base: the range resolves to the run's own commits regardless of the rewrite, applies cleanly when content was preserved, and yields a fast-forwardable chain. Verify preservation per file and keep the base's newer bytes for files the plan never touches (a tracked ledger is the witnessed instance). Re-derive the branch tip from the worktree's branch reflog before the CAS landing: `git rev-parse HEAD` lies after HEAD has been re-pointed at the base during recovery attempts, and a sha typed from session memory fails with `nonexistent object` (the cheap failure; a plausible-but-wrong sha that passes is the expensive one the two-value update-ref exists to catch).

**Why:** witnessed 2026-10-26 (playbook repo, exec run): a peer rewrote main mid-run, discarding the run's first-plan landing commit and turning `git rebase main` into a 619-command replay (aborted). The cherry-pick of the run range applied all five commits cleanly; the only delta was a ledger file the plan never touches, where the base's newer bytes were kept. A first CAS landing attempt failed on a memory-quoted sha, a second on `rev-parse HEAD` after HEAD had moved; the reflog-derived tip landed the two-value update-ref first try.

**See also:** #6 (base-branch immutability and the amend guard that names the rewrite), #227 (a landing's recorded sha comes from the landing receipt, never from the moving base tip).

## 240. A Lock Token Lost Across Shells Is Freed by a Fresh Acquire's Dead-Holder Auto-Clean, Then a Token-Fenced Release in the Same Shell

**Principle:** Family D (state-first: the lock's liveness is a property of its recorded holder, re-derived at acquire time; an exported token is shell state, not durable record).

**Trigger:** the landing-critical-section lock was acquired in one tool-call shell and the critical section runs in a later shell, so the token export is gone while the hold remains.

**Rule:** a hold whose recorded holder is dead and past the grace window is not stolen: a fresh `acquire` auto-removes it as an abandoned hold and prints the removal, after which an immediate token-fenced `release` in the SAME shell frees the lock cleanly. Never split the acquire and release across tool-call shells, and never release by deleting lock files by hand.

**Why:** witnessed twice 2026-10-26 (playbook repo, one exec run): the merge-landing-lock token exports died with their tool-call shells, leaving dead-holder holds that blocked the next landing; a fresh `merge-acquire` in each case printed `removed abandoned lock` and the same-shell fenced `merge-release` restored the free state, confirmed by `status`. Third witness 2026-11-02 (playbook repo, an exec run's squash landing): the hold can be even more fragile than the exports - the lock DIRECTORY itself vanished between two tool-call shells even though the earlier acquire had printed pass, so the later shell's release had nothing to release; the remedy is the same one-shell shape, acquire + land + release composed into a single command so no leg depends on state from a prior shell.

**See also:** #212 (run closeout tooling from the checkout holding its scratch - the same shell-lifetime boundary), the dead-holder grace contract in `scripts/done-lock.sh` usage text.

## 241. Plan-file checkbox writes can silently vanish before the boundary commit

**Rule:** a plan-file edit made inside a boundary shell call (checkbox marking, marker refresh, manifest append) is not done until the commit proves it: after `git add`, check `git diff --cached --stat` names the plan file, commit, then re-verify with `git show --stat HEAD` and `grep -c '\- \[ \]' <plan>` (expect the unchecked count to drop). If the plan file is missing from the staged set or the count did not drop, re-apply the edit as its own verified commit before any later phase reads the boxes; never batch the re-mark into a later commit and never trust the earlier write.

**Why:** witnessed three times in one execution run 2026-10-26 (playbook repo, plan `landing-subject-grammar-end-to-end`): python checkbox edits printed success inside the boundary call, but the boundary commits carried only the code files, the worktree read clean at HEAD, and a Phase 3 review lens later found all 22 boxes unchecked. Cause unresolved (suspect: a plan-protection hook or a racing peer process reverting unstaged plan bytes mid-call); the cheap per-boundary verification above catches the loss at the boundary where the rewrite is one command.

## 242. Size an Anti-Growth Byte Payment Before Drafting the Addition

**Principle:** Family D (state-first: the deletion budget is a disk-measurable quantity, derived before the addition is drafted, not discovered by iterating).

**Trigger:** a landing into text governed by a byte-neutral anti-growth rule (a change that grows a file must delete equivalent bytes in the same change), where the payable bytes are restated clauses in the target paragraphs.

**Rule:** first grep the target paragraphs for restated clauses (duplicated pointers, parentheticals restating a canonical section, recaps of rules owned elsewhere), sum their bytes with `wc -c` against the pre-change baseline, then draft the addition to fit the measured budget, and verify parity once. Never draft the addition first and discover parity through repeated measure-trim-measure loops.

**Why:** witnessed 2026-10-26 (playbook repo, ad-hoc exec landing): the byte payment was drafted first and took three successive measure-trim-measure `wc -c` iterations to reach parity; measuring the payable restated clauses up front sized the budget in one pass and the addition could have been written to it directly.

**See also:** #237 (a scan is green only over its own roots - the same derive-from-disk discipline applied to verification scopes).

## 243. A Branch Stranded by a Diverged Base Re-Lands by Cherry-Pick

**Principle:** Family D (recover and land through the owning machinery against current state).

**Trigger:** a rebase or landing against the base branch when the branch's fork point is no longer an ancestor of the base tip (the base was force-moved to a divergent line while work sat on the abandoned line).

**Rule:** when the fork point fails the ancestor check against the base tip, a plain rebase replays every unlanded commit since the true merge base - in a squash-landing repository, the whole abandoned line. Abort it, re-point the run branch to the current base tip (`git checkout -B <branch> <base-tip>`), and cherry-pick only the run's own commits, resolving shared rolling-log conflicts by union of intents (the run's removals and insertions apply onto the target's fresh layout; peer content stays byte-identical). At the retry the base pin and `--expected-base` must equal the newly computed merge base (#34), and the freshness gate re-refuses each tip race, so the retry-under-held-lock discipline (#128) applies. A panel digest over the merge-base-form diff survives the re-point while peer commits touch none of the run's paths, so the reviewed verdict and digest stay valid across replays.

**Why:** witnessed 2026-10-26 (playbook repo, ad-hoc exec landing): a branch forked hours before the base moved to a divergent line; the plain rebase computed a ~600-commit replay, the cherry-pick landed through one more tip race, and a stale base pin was refused once by the parentage gate before the refresh.

**See also:** #128 (rebase boundaries below an old fork; the plain form after a completed rebase), #34 (base-tip and base-pin argument semantics after a sanctioned replay).
## 244. Adding the Denied Class Falsifies the No-New-Class Sentence and Its Skill Twin

**Principle:** Family D (single source of truth: a footprint-denial sentence describes the change rather than the artifact, so the diff adding the denied class falsifies it, and the mirrored twin in the owning skill is the same claim's second copy).

**Trigger:** adding a refusal class, gate, or lock to a wrapper whose header contract sentence, or whose owning skill's mirrored prose, denies exactly that footprint ("adds no new refusal class").

**Rule:**
1. Treat the denial sentence as falsified by the same diff; rewrite it, in that diff, from denial to exact admission (the one class, its shapes, plus a one-line plan citation).
2. Rewrite the owning-skill twin to the same admission in the same change; grepping only the edited file never surfaces the twin.
3. Do not impose a same-length constraint on the rewrite: a sentence that denied a class must now admit one, so information strictly grows and length parity is unsatisfiable by construction.

**Why:** witnessed 2026-10-26 (playbook repo, execute-plan Phase 3 r1): `scripts/done_run.sh`'s header claimed the runner added no new refusal class while the same diff added the incompatible-transition-inputs class, and the twin in `agents/skills/done/SKILL.md` denied the same class; the blocking fix rewrote both to the one-class admission with the three shapes enumerated.

**See also:** #151 (the same-change sweep over disclaimers and case-space inventories; this is the behavior-edit variant, where the code, not a prose edit, is the source the prose must follow), #145 (a deliberate duplicate is one contract in two copies; a prose twin without a parity pin drifts silently).

## 245. A Preservation Assertion Needs the Fixture to Move the Preserved Value

**Principle:** Family H (verify the real thing, not the abstraction: while the seeded value and the current value are identical, an operation that preserves the seeded value and one that re-derives it fresh are observationally equivalent, so the assertion pins nothing).

**Trigger:** writing or reviewing a test that asserts an operation preserves an earlier-captured identity (a start commit, a digest, a record id) when the fixture performs no step between seeding that identity and running the operation.

**Rule:**
1. Make the fixture move the preserved value between seed and operation: commit new work so HEAD advances, or rewrite the bytes so a digest changes.
2. Assert the pair: the operation's output equals the seeded value and differs from the value's current form; the wrong implementation that re-derives the identity fresh at operation time then fails the second half instead of passing the whole suite.

**Why:** witnessed 2026-10-26 (playbook repo, execute-plan Phase 3 r1): both adoption tests asserted the adopted record preserved the interrupted boundary's start commit, but no fixture committed between seeding the boundary and adopting it, so the mutation "start commit = fresh HEAD" survived the entire suite while start-commit resolvability still passed; the fix commits post-boundary work in each fixture and asserts adopted equals prior and differs from new HEAD.

**See also:** lesson 79 in the user corpus (the guard-binding member of the family: neutralize the guard, confirm RED), lesson 80 in the user corpus (the restore member: assert the intermediate mutation, not the restored final state), lesson 330 in the user corpus (one mutation-killing witness per conjunct), #162 (grade pin claims with a mutation matrix; run the hypothesized wrong implementation rather than trusting the pins).

## 246. A Twin-Pinned Test Failing Only on a Branch Is Base Drift

**Principle:** Family H (verify the real thing, not the abstraction: a test comparing branch bytes against a vendored or deployed twin compares against a surface that tracks the default branch, so the failure can localize to the base rather than to the change).

**Trigger:** a receipt-pin or vendored-twin test fails on a run branch in an authoring worktree while the branch's own diff does not touch the pinned source.

**Rule:**
1. Run the same test on the default branch and again after rebasing the branch onto it.
2. Green on both localizes base drift: the twin holds default-branch bytes that the fork-point branch predates.
3. The remedy is the rebase, never an edit to the test, the pin, or the twin; record the drift in the round record as environment, not defect.

**Why:** witnessed 2026-10-26 (playbook repo, execute-plan Phase 3 r1): before the sanctioned rebase the lib suite showed one failure in the execute-plan skill receipt pins and vendored-twin test because main had advanced `agents/skills/execute-plan/SKILL.md` while the branch held fork-point bytes; the test passed on main and after the rebase, and the round record classifies it as base drift, not a defect of the change.

**See also:** lesson 476 in the user corpus (twin identity: a same-inode twin is one deployment surface, not a copy to synchronize), #6 (land a squash only from a tree merged with the current default branch; the same base-freshness discipline at the landing side).

## 247. A Closeout Helper's rc 0 Is Not a Landing Witness

**Principle:** Family H (verify the real thing, not the abstraction: a helper's exit status covers the legs it ran, and a deferred leg is still a success at the process level).

**Trigger:** a finalize-style closeout helper whose landing leg (a squash under the merge lock) can be deferred while the helper still exits 0, followed by any step that records terminal receipts or reports a landed hash.

**Rule:** after a closeout helper returns, re-derive the landing from the default branch itself (the squash subject naming the plan slug, or the archived destination's presence and bytes) before recording any terminal receipt or reporting a hash; never read the helper's landing summary line as the witness. When the landing was deferred behind a peer's held merge lock, complete it by hand under a fresh acquire, and note the egress gate's ack shape: `--ack-egress` must name the detected egress's old path (never the pointer record), and no ack is needed at all when the plans-egress pointer record already sits in the anchored reviews home the gate reads.

**Why:** witnessed 2026-10-26 (playbook repo, done closeout): finalize exited 0, marked the run manifest complete, released the done lock, and printed a landing summary naming the branch commit, while the squash itself had been skipped behind a live peer's merge lock; the default branch did not contain the archive until the landing was re-derived from main's history, confirmed absent, and completed by hand. Two landing retries then failed on the egress ack before the pointer record's evidence legs were recognized as already sufficient. Second witness 2026-11-02 (playbook repo, an exec run's plan landing): the converse arm is enforceable - once the evidence legs ARE satisfied, passing `--ack-egress` becomes a fatal `unused --ack-egress` refusal, so the ack is not a belt-and-suspenders flag but an exact-match argument; retry without it once the egress digest is already carried in the record pair.

**See also:** #240 (a lock token lost across shells; the token-fenced release arm), #243 (the cherry-pick re-land when the base was rewritten), #34 (base-tip and expected-tip argument semantics).

## 248. A Peer Plan's Byte Pin Colliding With Reworded Remedies Resolves to the New Canonical Text

**Principle:** Family D (single source of truth: union-of-intents merges keep both prose sides because prose describes; a byte pin is not prose - it asserts the artifact's current canonical bytes, so when two plans collide on those bytes the newer rewording wins and the older pin moves).

**Trigger:** a replayed or cherry-picked re-land where the run reworded a remedy or contract string that a peer plan's test pins byte-for-byte.

**Rule:** resolve the collision by updating the peer pin to the new canonical text (the pin's own witnessing intent - the behavior dimension it checks - is unchanged), and re-run the full suite after any replay whose peer commits touch the run's own paths: the re-land lesson's digest-survival condition (peer commits touching none of the run's paths) does not hold there, so the reviewed verdict does not carry across the replay.

**Why:** witnessed 2026-10-26 (playbook repo, done closeout): the re-land kept a peer plan's terminal-release test pinning the old orphan-classification remedy line while the run's plan had reworded that remedy into a multi-arm form; the focused adoption class stayed green and the full wrapper suite failed once post-merge. Updating the pin's expected bytes to the new canonical line and re-running the class and the suite closed it.

**See also:** #243 (the cherry-pick re-land and its digest-survival condition), #244 (the no-new-class sentence and its twin), #128 (rebase forms).

## 249. A Compare-and-Swap Squash Landing Can Leave the Primary Checkout's Index and Worktree Holding Stale Pre-Landing Bytes

**Principle:** Family A (state re-derivation at validation time: a ref-move landing advances the branch pointer only; every index and working-tree surface in the primary checkout is stale until a restore pass proves otherwise).

**Trigger:** a worktree-complete squash landing (the compare-and-swap ref update) just landed through the landing helper, and the primary checkout's status is about to be read to report cleanliness, to stage follow-up work, or to attribute dirt.

**Rule:** after every compare-and-swap squash landing, read `git status --porcelain` in the primary checkout before any staging, commit, or cleanliness claim; a staged or unstaged modification whose diff against HEAD is exactly the reverse of the just-landed change (the landed paths' pre-landing bytes) is the landing's stale-bytes phantom, not peer dirt: restore the named paths from HEAD after verifying the diff names nothing the landing did not touch, and never revert or re-land from the phantom. A phantom whose diff names paths the landing did not touch is peer state: touch nothing and report it.

**Why:** witnessed twice in this repo. 2026-10-22 (exec carrier closeout, state-file note): the primary index held a phantom after a landing, refreshed after exact parent-tree verification. 2026-10-26 (interactive exec mandate): after a three-commit branch squashed to one landing commit, the primary's index and working tree for the rolling prompt log held the pre-landing bytes (the newest prune receipt line missing), presenting as a staged modification whose diff removed exactly that line, while the landing's reconcile pass restore count had not covered the path; restoring from HEAD re-anchored the file with only the landed line added, and the final status ran clean. Third witness 2026-11-01 (two-pick exec carrier, both picks' landings): the shape hit three times in one session — pre-edit lesson bytes staged after the first landing, pre-edit skill-text bytes after the second, and a registry-row deletion presenting as staged after a reconcile pass that had already run; each cleared with a `git status --porcelain --untracked-files=no` read plus a restore from HEAD, and the run's final status was clean. One landing can seed several phantoms, and a phantom can reappear after an earlier reconcile pass, so the status read belongs after EVERY landing, not once per run.

**See also:** #100 (a ref-only landing into a peer-held checkout leaves reversal-shaped staged residue: the peer-held variant of reversal-shaped bytes), #89 (a value quoted from conversation context is not evidence).

## 250. Re-Derive Queue Coverage From Disk at Pick Time Under Parallel Lanes

**Principle:** Family A (state re-derivation at validation time: an observation made when work was selected is not the state at the moment work starts).

**Trigger:** any session about to start work on a queued item (a rolling-log entry, a backlog row, a plan) in a repository where parallel sessions dispatch from the same queue, after the session's own snapshot of the queue was taken earlier (at session start or an earlier survey).

**Rule:** immediately before starting work on the item, re-derive its coverage state from disk with fresh commands: the item still present and unfrozen in its log, no landing receipt for its origins in the default branch's history, no peer worktree, branch, or claim holding the item, and no live sibling run recorded against it. A peer-completed item is reported and skipped, never re-executed; a peer-in-flight item is stood down with the peer's commit or worktree named, never raced; and when the session already built partial work, the stand-down records the supersession (the surviving implementation identified) before its own worktree and branch are removed.

**Why:** witnessed 2026-10-26 (playbook repo, interactive exec mandate): three entries of one queue were concurrently covered by peer sessions; a session that planned from its session-start snapshot implemented one entry in full before discovering a peer's committed implementation of the same scope arms, stood the duplicate down (work committed for the record, then the worktree and branch removed), and executed the next uncovered entry instead. The same day's peer landings moved the default branch twice under in-flight work, forcing a rebase whose conflicts were tractable only because the duplicate had already been surrendered. The freeze marks and landing receipts exist as the disk-truth instruments; the cost lands entirely in sessions that skip the pick-time read. Second witness 2026-10-27 (the 02:00 exec carrier run): the session re-derived the queue's content and urgency but read the execution-claims directory and the worktree list only after authoring the full fix and its four regressions in the primary checkout, then reverted them byte-for-byte when the peer hold surfaced; the survey must precede the first edit, not precede the landing.

**See also:** #89 (re-run the origin's own probe before authoring its fix; the verification-at-action-time family), #249 (a CAS squash landing leaves the primary checkout stale; the same family at the landing boundary), #100 (a ref-only landing into a peer-held checkout; the peer-held variant).

## 251. A Mid-Turn Interrupt Cancels In-Flight Sub-Agent Launches

**Principle:** Family A (state re-derivation at validation time: after an interrupt, the fan-out's true state is what already returned, never what was launched).

**Trigger:** a parallel worker fan-out (a review panel, lens workers, helper agents) with launches still in flight when a new operator message interrupts the turn.

**Rule:** treat a cancelled launch as recoverable, never as a failed review: triage the surviving workers' returned output first and land the folds it ordered, then relaunch the cancelled worker one-for-one with the original prompt over the post-fold bytes, and record the relaunch in the panel row. Sequence deliberately: a fold landing while a worker still reads the diff shifts its line numbers, so the replacement launch should read the final bytes and its run becomes the record's review instead of a stale-byte pass.

**Why:** witnessed 2026-10-26 (playbook repo, ad-hoc exec run): the operator's stop-after-current-pick message arrived mid-panel and cancelled one of two parallel workers before it returned; the other worker's findings were triaged and folded first, the cancelled worker was relaunched over the folded head, and its run anchored the landing record.

**See also:** #250 (re-derive from disk at pick time; the same family under parallel lanes).

## 252. An Ancestry Check Never Sees a Squash Landing; Pair It With the Tree Proof

**Principle:** Family H (verify the real thing, not the abstraction: "reachable from the base branch" is the abstraction of landed, and a squash landing is the real shape the abstraction misses).

**Trigger:** code that classifies a commit as on or off the base branch (deferred-landing detection, completion gates, landing-witness checks) in a repository whose landings squash.

**Rule:** use merge-base ancestry as the first arm, never the only one: a squash landing composes a new commit on the base with a different sha, so the source branch's commit is never an ancestor of the base even after its work fully landed. Pair ancestry with a bounded tree-equality scan of recent base history (the commit's tree equal to some base commit's tree, the same squash proof the branch-deletion arm uses), and fail open with a warning when the base branch itself cannot be resolved.

**Why:** witnessed 2026-10-26 (playbook repo, the finalize deferred-squash honesty landing): the new landed/pending classification needed a test that recognizes direct and merge landings through ancestry and squash landings through the tree scan; ancestry alone would classify every legitimately squashed run as pending forever, so a re-run finalize could never complete the withheld state.

**See also:** #247 (a closeout helper's rc 0 is not a landing witness), #73 (post-squash follow-up deltas live on the default tip).

## 253. Re-Derive a Stale Classification at the Emission Point

**Principle:** Family A (state re-derivation at validation time: a classification is only as fresh as the point that emits it).

**Trigger:** a multi-step ceremony with an early check-then-act split whose later steps (a child commit, a rider append, a peer landing) can create or change the state the early check classified.

**Rule:** when an early classification gates an action, re-derive it fresh at every later point that emits user-visible output or a durable record, and word a late emission's duty clause for what the later position can actually know: the lock state, the marking outcome, and the ledger content may all have moved since the early check. An early check's duty wording repeated verbatim at a late emission point is a lie about the resumed state.

**Why:** witnessed 2026-10-26 (playbook repo, the finalize honesty landing's panel): the guard-firing child commit could create the ledger's first line after the marking decision, leaving the manifest complete while the summary said squash-pending with no deferral line; the fold re-derived the classification at the summary block and worded the late line's duty "the complete marking above predates this ledger line".

**See also:** #247 (rc 0 is not a landing witness), #252 (the landed classification's two arms).

## 254. The Shell's grep Is ugrep on This Host

**Principle:** Family H (verify the real thing, not the abstraction: the `grep` name on this host resolves to a different engine whose regex dialect differs).

**Trigger:** any locator pattern using GNU basic-regex escapes (a literal paren group like `name\)` in a grep argument) in this harness's shell.

**Rule:** on this host the shell's grep resolves to ugrep: patterns GNU grep accepts can error with shapes like "mismatched ( )". Prefer `-F` for fixed-string locators or restructure the pattern without escaped groups; read a ugrep error line as a dialect mismatch, never as evidence that the target text is absent.

**Why:** witnessed 2026-10-26 (playbook repo): a `grep -n "subcommand\)"` locator failed with a ugrep mismatched-parenthesis error while auditing a shell script, costing one retry round. Second witness 2026-10-27: a display-only `grep -E '^\+\+\+'` over a diff failed with the ugrep "invalid syntax" error at the `+++` quantifier, costing one retry round.


## 255. A Requested Clause Landed Inside an Existing Enumeration Must Clear That Enumeration's Governing Conditional

**Principle:** Family C (reachability: a rule is landed only where the surrounding structure lets its operative case reach it; verbatim fidelity to the request is not reachability).

**Trigger:** landing a sentence or clause "beside" or "inside" an existing list, enumeration, or parenthetical whose lead-in carries a `where`, `when`, or `for` conditional, especially when the wording came verbatim from a backlog row scoped to one named span.

**Rule:** before placing the clause, read the enumeration's lead-in conditional and ask whether the clause's operative case (the class of run or landing it governs) satisfies it; when it does not, widen the conditional in the same change (naming the new class and keeping per-item applicability explicit) or scope the clause to its class in its own words. A pre-existing item under the same misfit is evidence that the conditional, not the clause, is the thing to fix.

**Why:** witnessed 2026-10-26 (playbook repo): a receipt-paired-removal clause for the ad-hoc rolling log landed verbatim inside the worktree-first closeout-rider enumeration, whose lead-in named only plan and plan-execution landings; ad-hoc landings, the only class that appends the receipt, could never reach it. Both focused-panel workers staged it blocking; the fold widened the conditional to ad-hoc maintenance landings with a per-class qualifier, which also made the pre-existing origin-row-deletion rider coherent.

**See also:** #199 (a fixture for a shape the enumeration universe cannot produce is dead weight: the same reachability test applied to test fixtures).

## 256. A Pre-Landing Rebase Invalidates Every Landedness Proof Keyed on Recorded Branch Shas or Their Trees

**Principle:** Family D (state-first: a rebase rewrites the branch's commit and tree identities while leaving the content delta intact, so any sha or tree recorded before it names a commit that will never appear on the base branch).

**Trigger:** a closeout or honesty check that decides "landed" by asking whether a recorded branch commit (an owned-commits ledger line, a run manifest tip) is an ancestor of the base branch, or whether its tree appears among the base branch's recent trees, in a repository whose base-freshness gate forces a rebase whenever peers land first.

**Rule:** prove landedness from the content delta or the landing receipt, never from a pre-rebase identity: check `git diff <base> <branch>` for emptiness after the landing, or read the `land-worktree` receipt's new tip (#227); when a check must stay sha-keyed, refresh the recorded shas as part of the rebase step (rewrite the ledger lines with the post-rebase tips before finalize runs). Read a "landing deferred" verdict that follows a rebase as a candidate false negative and re-derive before acting on its resume duty.

**Why:** witnessed 2026-10-26 (playbook repo): an ad-hoc landing rebased twice while peers advanced the base, then squash-landed; the finalize leg's day-old deferred-squash honesty arm scanned the base for the ledger tip's tree, found the pre-rebase tree absent, printed LANDING DEFERRED, and withheld the manifest's complete marking although `git diff main <branch>` was empty and the landing receipt named the new tip. The resume duty it printed (re-run finalize) can never succeed on that ledger.

**See also:** #78 (prove landedness from witnesses, not diff metrics), #227 (the landing sha comes from the receipt, never the base tip), #123 and #128 (what a rebase does to a branch under squash landings).

## 257. A Dispatch Payload That Restates a Subset of a Standing Contract's Gates Silently De-Scope the Contract

**Principle:** Family C (reachability: a standing contract's machinery binds a run only where the payload the session actually follows lets it reach; an instruction that names fewer gates than the owning contract is read as the complete gate list, not as a subset).

**Trigger:** authoring or executing a dispatch payload (a log entry's prompt field, a task brief, a carrier instruction) for work whose surface already carries a standing contract (a mandatory panel, an isolation standard, a landing route), especially when the payload's gate list was written to be "helpfully concrete" for the specific pick.

**Rule:** a payload inherits its surface's standing contract by reference and may add specificity on top, never subtract beneath it: do not enumerate a gate list that shadows the owning contract's machinery; when a payload does restate gates, read the discrepancy as a defect in the payload (or in the emission contract that allowed it), not as permission. Symmetrically, when executing a payload, re-derive the full duty set from the owning contract before starting, and treat "the payload did not name it" as never a reason to skip a mandated step.

**Why:** witnessed 2026-10-26 (playbook repo, interactive exec mandate): the picked ad-hoc entry's prompt named exactly three gates (pins suite, em-dash gate, hygiene scan) while the owning ad-hoc arm mandated the focused review panel, the panel receipt, the ad-hoc worktree, and the squash-landing route; the run followed the prompt verbatim and landed with the arm's machinery absent, and the operator corrected it in-session. The fix is emission-side (the investigate contract forbidding shadowing gate lists in ad-hoc payloads) plus a mandate-wording clause; row and plan entry landed the same day.

**See also:** #255 (a landed clause is only operative where its governing conditional lets its class reach it: the same reachability test applied to payload text instead of placed clauses), #199.

## 258. A Scripted Section Splice With a Start Index Past Its End Index Silently Duplicates the Span Between Them

**Rule:** when a script rewrites a document by splicing (`text[:start] + segment + text[end:]`), an `end` index resolved independently of `start` can land before `start` (the end anchor matching an earlier occurrence), and the splice then silently duplicates everything between the two anchors instead of failing. Derive the end anchor by searching AFTER the start index (`text.index(anchor, start)`), assert `end > start` before splicing, and verify section-heading counts (or file size sanity) after any scripted structural edit before committing it. Witness: the 2026-10-27 ad-hoc-worktree-lifecycle-owner-gap exec run, where `t.index('## Assumptions')` matched an earlier section than `t.index('### Task 3:')` and the unchecked-box-marking splice doubled ~8KB of plan body; the corruption rode a boundary commit and was caught only by the Phase 3 adversarial panel.

**Principle:** Family Python/scripting

## 259. A Peer Strand-Drain of Your Branch Leaves the Run's Closeout Duties Unowned Until You Return

**Principle:** Family H (verify the real thing: a foreign squash landing of your branch is invisible to ancestry and to a whole-tree diff against your tip; your content's landedness is proven path-scoped, and the drained run still owns its release duties).

**Trigger:** returning to a run whose worktree and branch were removed by a peer strand-drain session that landed the branch's content on the base while the run sat between steps (no worktree, no branch, claim and panel record still standing).

**Rule:** the drained run's closeout is a verification-and-release set, never a redo: (1) prove the landing carried your reviewed bytes with a path-scoped diff of your changed files against your reviewed tip (empty output = byte-identical); a whole-tree diff between your old tip and the landing commit reads as a large mismatch because it includes every peer delta that landed between the bases and decides nothing; (2) re-run the affected test class at the new base tip (the drain session landed without your suite); (3) release your execution claim, which now outlives its worktree, through the claim gateway's operand-source arm reading the deleted origin row from the landing's parent (`<landing>^:<row-path>`); and (4) annotate your panel record with the landing witness so the reviewed digest and the landed commit stay linked. Never re-execute, re-land, or re-arm on the strength of a vanished worktree alone.

**Why:** witnessed 2026-10-26/27 (playbook repo, the 20:00 exec carrier run): between the run's review panel and its landing step, a peer session landed the completed branch as squash 9ef8ce21f ("strand drain: landed the 2026-10-26 finalize-honesty exec run's completed branch"), removed the worktree and branch, and left the execution claim standing; the returning session verified byte-identity (empty path-scoped diff of the two changed files vs the reviewed tip), re-ran the finalize test class 19/19 at the new main tip, released the stale claim through `--operand-source <landing>^:<row-path>`, and annotated the panel record with the landing witness.

**See also:** #256 (the rebased-branch landedness proof this run itself landed), #175 (the rebase conflict discipline the same run used mid-flight), #214 (the tight-scope dispatch retry the same run's panel needed).

## 260. Write the Round's Review Records to the Durable Home Before Any Interrupt-Prone Boundary; a Takeover Landing Inherits None

**Principle:** Family D (state-first: panel evidence that lives only in session context does not survive the session; the reviews home is the record of record).

**Trigger:** an execution run holds folded panel findings or a dispatched confirm round when it approaches a pause-shaped boundary (operator interrupt, budget pause, stand-down), or a second session considers adopting a branch another run left behind.

**Rule:** at every pause-shaped boundary the round's staged record pair goes to the primary reviews home before the pause stands, even mid-round (an r1 record naming the staged findings beats no record); an adopting session that lands an adopted branch cites the records it finds there, and when none exist it runs its own focused confirm round over the branch delta and cites that record in the landing message, never landing certified-only-in-session work without a citation.

**Why:** witnessed 2026-10-26/27 (playbook repo): an exec run's second pick was panel-certified in session (r1 findings folded, r2 confirm dispatched) when the session was interrupted before any record was written; a peer strand-drain landed the branch with no panel citation in its message, and the interrupted session reconstructed the r1/r2 records post-landing against the landed bytes - the review evidence survived only because the session resumed.

**See also:** #259 (the drained run's own closeout duties - this lesson is the write-side and adopter-side complement), #65 (the review machinery's validator is the contract over recipe prose).

## 261. A Dead Session's Per-Worktree Done Lock Recovers From meta.env Through the Orphaned Arm, Never From a Recaptured Export File

**Principle:** Family B (ordering/state: the lock's own on-disk record is the recovery source of truth; a captured shell transcript is not an export file).

**Trigger:** resuming work after a session died holding a per-worktree done lock (mid-run interrupt, quota wall, crash), with the acquiring shell's env exports lost.

**Rule:** recover the hold from the lock directory's own `meta.env` (token, label, holder pid, repo_root): verify the recorded holder pid is dead, then release via the lock script's orphaned arm with only the lock directory path in env - the verified-dead gate is the release's authority, not a re-supplied token. A `tee` capture of the setup banner is not a sourceable export file (interleaved status lines abort `source` mid-file), so "re-export from your acquire output" fails when the only capture is the banner; the env-less orphaned release keyed by the recorded directory is the working path, and it works even after the worktree the hold keyed on is gone.

**Why:** witnessed 2026-10-26/27 (playbook repo): an exec run interrupted between two worktree picks left both per-worktree done locks held by dead shells; sourcing the tee'd setup outputs failed on their non-export lines, and both holds released cleanly through the orphaned arm (holders verified dead, ages 8-9 hours) after their worktrees had been removed by other sessions.

**See also:** #166 (transfer the run inputs in before the done boundary setup - the same run's first refusal, whose failed setup releases its own hold), #43 (re-derive checkout state at every call).

## 262. Merge a Run Worktree's Telemetry Ledger Into the Primary Home With a Uniqueness Pass

**Principle:** Family B (ordering: the closeout append is a merge between two ledgers that may share history lines, not a union of disjoint ones).

**Trigger:** a worktree-scoped run's closeout copies or appends gitignored telemetry ledgers (landing-costs, invocation-costs) into the primary checkout's metrics home.

**Rule:** pass the merged ledger through an exact-duplicate filter (`sort | uniq` for line-structured jsonl) in the same change as the append, and sanity-check the merged unique-line count against the sources: a worktree-side ledger can carry lines the primary already holds, and a plain append silently multiplies them in a gitignored file nobody reads until its numbers matter.

**Why:** witnessed 2026-10-27 (playbook repo): the primary landing-costs ledger reached 545 lines carrying 114 unique across runs; a 1.5-hour-old worktree's own ledger held 109 lines for a one-landing run, so the naive append tripled several rows before both ledgers were deduped in the same change. The mechanism that seeds a fresh worktree's metrics home with primary history is identified (2026-10-27): the docs-branch sync's branch-only restore leg materializes docs-tracked ledgers into the run worktree whose closeout runs the sync there; removed by the restore-leg skip in linked worktrees (scripts/docs_branch_sync.sh).

**See also:** #167 (mirror untracked run records out of a worktree before the closeout stages run).

## 263. Precheck the Session's Primitives Before Planning a Duty Leg That Needs One

**Principle:** Family B (identity: a duty's primitive legs bind the executing session's actual toolset, not the duty text's assumption; a leg planned against an absent primitive surfaces only at emission time and drags the plan into a re-emission loop).

**Trigger:** an automation-born session reading a duty whose text orders a specific primitive emission (a delete-first ordering, a create, an update), before planning that leg.

**Rule:** precheck the executing session's toolset for the primitive a planned leg needs; when it is absent, record the proven-absent leg once beside the duty decision (naming the duty and the missing primitive) and proceed with the leg-free work. Never reach for the absent primitive mid-plan: the failed reach tends to re-emit the session's last successful read call, and a repeated-identical-call flag is the signature. When no create is owed, a lingered spawner ages out on its own, so the missing delete leg costs nothing once recorded.

**Why:** witnessed 2026-10-27 (playbook repo): a fired resume session planned the turn-start carrier re-arm duty's delete-own-spawner leg from the duty text alone, found its toolset listing-only at emission time, and re-emitted its verification listing three times (harness-flagged as repeated calls) before naming the leg proven-absent; no create was owed, so the delete was moot and every listing was pure waste.

**Distinguishing from #196:** #196 governs honoring an absence RECORDED by a prior instance (re-probe with one real attempt); this governs planning a leg against a live absence in the current instance (precheck before planning, record once, stop emitting).

**See also:** #196 (re-probe recorded absences at each session instance; cap-blocked is not toolset-absent).

## 264. Route a Worktree-Complete Landing Through land_squash.sh; a Hand-Composed Squash Detaches at the Base, Never at the Branch Tip

**Principle:** Family B (mechanics: `git merge --squash <branch>` produces the branch's delta only when HEAD is not already the branch tip; a squash of a branch into itself stages nothing - and the sanctioned landing path avoids the whole question).

**Trigger:** landing a run branch as a squash merge from an execution worktree, at the point of composing the landing critical section.

**Rule:** the worktree-complete class (plan landings, plan execution landings, ad-hoc maintenance landings) routes solely through `bash scripts/land_squash.sh land-worktree --branch <source-branch> --expected-tip <sha> --message <text>` under the acquired merge lock; the operative text (agents/skills/execute-plan/worktree-first.md, lifecycle step 4's class-ownership paragraph) never authorizes a hand-composed equivalent, and the helper owns the gate set (tree equality, base freshness, parentage gates, compare-and-swap) a hand sequence must otherwise re-derive line by line. When a hand-composed squash is nevertheless being diagnosed or repaired outside the class, detach at the base the landing builds onto (the current default-branch tip), never at the source branch's own tip: a detach at the branch tip makes the squash a silent no-op ("nothing to commit, working tree clean").

**Why:** witnessed 2026-10-27 (playbook repo): an ad-hoc landing session hand-composed the whole critical section (detach, merge --squash, commit, parentage gates, CAS) instead of the helper invocation; its first squash attempt detached at the branch tip and staged nothing, and the second attempt passed its re-derived gates but skipped the helper's own pre-refusals (lock-record verification, base-freshness check-landing, porcelain snapshot). The landing itself verified clean, and this correction is the additive record of the deviation (the base-branch immutability rule keeps the landed commit untouched).

**See also:** agents/skills/execute-plan/worktree-first.md lifecycle step 4 (the class-ownership paragraph is the operative source).

## 265. Derive a Reconciliation's Declared Values From the Live Artifact, Never From the Origin Row's Prose

**Principle:** Family B (identity: a change whose contract is "reconcile a declaration to observed state" copies values from the observed state itself; the origin row's description is a pointer, not the source).

**Trigger:** executing an entry whose fix is a declaration edit (a schema example, an enum, a field paragraph) that must match a live file, at the moment of writing the declared values.

**Rule:** read the live artifact (the state file, the module, the observed writes) and lift every literal - enum values, entry key spellings, entry shapes - from it directly before writing the declaration; when the live artifact carries more than one spelling of a key, the declaration admits both. Then check the delta the same way the reviewer will: diff the declared values against a fresh read of the live file, not against the origin row.

**Why:** witnessed 2026-10-27 (playbook repo): a schema-reconciliation edit declared the state notes array with the single key spelling the origin row described, while the live state file carried two spellings (nine `at`-keyed entries, four `ts`-keyed) - the review panel blocked r1 on the declaration reproducing the exact lag the entry existed to close. The same run's fold pass then re-committed the class in miniature: an explanatory date qualifier added during the fold was falsified by the live file (the "legacy" spelling was the newer one), and r2 blocked on the fold itself. Prescribed remedy both times: drop to what the live bytes show, word nothing the live artifact does not witness.

**See also:** the record re-derivation fence (investigate Stage 4) for the same class at record-write time.

## 266. Number Review Findings in Document Order, Not Discovery Order

**Principle:** Family B (mechanics: `validate_review_staging.py` checks that a staging record's finding blocks read in severity-major order with ascending finding ids across the whole document; ids are position stamps, not discovery stamps).

**Trigger:** staging a review round whose blocking or medium findings were discovered after lower-severity ones (the common worker-return order), at the point of assigning F-ids.

**Rule:** assign finding ids in the order the findings will appear in the staging document (severity groups first, ascending within each), and mirror that numbering in the sidecar's findings array; when a medium or blocking finding arrives after lows were numbered, renumber both halves before writing instead of reordering the document around the discovery sequence.

**Why:** witnessed 2026-10-27 (playbook repo): an r2 record staged four findings in discovery order (two lows, then a medium, then a low) and failed the ordering gate ("findings are not ordered by severity then ascending finding ID"); the repair renumbered the medium to the id its severity position implied in the markdown and the sidecar together, since fixing either half alone trips the finding-conservation gate.

**See also:** the staged-record repair discipline (read the validator's check families before drafting, not one error class at a time).

## 267. Drain an Exec Strand as Work-Plus-Riders: a Completed Branch Can Land Without Its Closeout Riders

**Principle:** Family B (ordering: a stranded run's branch carries the work but not necessarily the run's closeout paperwork; a drainer that lands the branch alone re-creates the strand at the record layer).

**Trigger:** an exec-mode survey finds a top pick whose work already sits committed-but-unlanded on a worktree branch (a prior session's strand), at pick-time freeze.

**Rule:** drain, never redo: re-run the branch's focused suite at its tip, rebase onto the moved base, land through the merge-locked worktree-complete helper, then diff the branch delta for the run's closeout riders (the covered origin-row deletion, the log entry prune with its receipt line, the panel-record annotation). A delta touching only the work files lacks them; supply the missing riders in a follow-up primary commit naming the landing commit as witness, because the riders-ride-the-branch rule is already spent once the branch landed. Converse duty on the execute side: land the riders on the branch before the landing boundary, since a later drainer will not know to recreate them (the drained run's own side is #259).

**Why:** witnessed 2026-10-27 (playbook repo, the 03:00 exec carrier run): both top EXEC-PROMPTS picks sat fully executed but unlanded on worktree branches from a prior interrupted run. Pick 1's branch carried its own origin-row deletion and entry prune, so its landing was self-contained; pick 2's delta touched only the two script files, so after its landing (3a089c866) the origin row and entry section stranded until follow-up 32a6ad90a supplied the prune, the receipt, and the row deletion.

**See also:** #259 (the drained run's closeout duties), #260 (records to the durable home before the boundary), #264 (the sanctioned helper landing).

## 268. Express a Whole-Section Deletion as a Boundary-Verified Line-Range Removal, Not an Edit Anchored on the Neighbor Heading

**Principle:** Family B (mechanics: a single replacement whose old text is the following section's heading inverts the intended direction when the replacement text re-includes the removed section, turning a deletion into a duplication).

**Trigger:** removing a whole multi-line section from a large tracked file (a consumed rolling-log entry, a long module) with one anchored replacement call.

**Rule:** before a whole-section removal, verify the section's boundary lines from disk, then delete by line range instead of anchoring a replacement on the neighbor heading; if a replacement is used at all, its replacement text must be derivable from the old text by pure subtraction. Re-read the working-tree diff for direction before staging: insertions where deletions were intended (the removed section's text reappearing at the anchor) are the inversion signature - stop, restore the file, and redo the removal; never commit past it.

**Why:** witnessed 2026-10-27 (playbook repo, the 5 am exec carrier run): deleting the consumed EXEC-PROMPTS entry section, the removal was drafted as a replacement anchored on the next section's heading with the old section text re-emitted inside the replacement, which duplicated the entry instead of deleting it. Caught at once by comparing intent to result, reverted with a checkout, and redone as a boundary-probed line-range deletion (boundaries confirmed by printing lines 3 and 29-31 first) whose result was read back before the receipt was appended.

**See also:** the log's standing write discipline (targeted section edit prepared from a fresh read; re-read and compare before every write).

## 269. A Swept Skip Record Downgrades a Closeout Retry to Capture

**Principle:** Family B (ordering: a multi-attempt ceremony's reuse arm is only as durable as the proof record it reads; a proof record under a swept scratch root survives until the next sweep pass, and the retry reads its absence as first-run state).

**Trigger:** a ceremony leg that reuses a baseline or honors a skip record living under a sweepable scratch root, at the retry after a failed attempt.

**Rule:** before retrying a failed closeout attempt, re-derive the predecessor attempt's proof state from the run's own records (the log lines naming the skip or bypass), not from the artifact paths alone; when a skip or baseline proof vanished between attempts, name the sweep as the consumer and restore or re-record the proof before the retry. A retry that silently changes arm (skip honored becomes capture performed) is a contract violation to stop on, never a fallback; never capture a late baseline to satisfy a retry.

**Why:** witnessed 2026-10-27 (playbook repo, a plan-execution closeout): the first commit attempt ran the valid-skip-record bypass arm (`closeout-baseline-skip.json` beside the absent Phase 0 baseline) and failed at a later leg; the docs/tmp sweep then consumed the skip record; the retry found neither the baseline nor the skip and captured a real baseline, where the closeout contract reuses the one pre-work Phase 0 baseline or its valid skip record, never capturing a late baseline (scripts/done_run.sh, the ad-hoc commit arm).

**See also:** #82 (ceremony-cited records re-derived from disk at the point of use), the record re-derivation fence (investigate Stage 4).

## 270. Copy Primary-Home Run Records Into the Run Home Before Verify-Records

**Principle:** Family B (identity: a containment check resolves its home from the closeout target, so a record written to a different home is foreign by construction no matter who wrote it).

**Trigger:** a run whose closeout records were written directly to the primary reviews home (the no-mirror remedy after the docs-branch sync's symlink-escape refusal), approaching the closeout leg whose citation check resolves the reviews home from the worktree target.

**Rule:** before the verify-records leg, copy each record the ceremony will cite from the primary reviews home into the run's reviews home; a citation outside the target-resolved reviews home is refused by design, and the copy is the working bridge, not a contract change. Do not answer the refusal by weakening containment to accept the primary home, and do not stop writing records to the primary home (the no-mirror remedy stands).

**Why:** witnessed 2026-10-27 (playbook repo, a plan-execution closeout): the exec-review record written to the primary reviews home was refused by the archive-ceremony's verify-records leg (the check keeps only citations resolving under the target's reviews home, scripts/worktree_closeout_migrate.py); copying the record into the run's reviews home cleared the leg.

**See also:** #96 extension (the no-mirror remedy this bridge serves), #260 (records to the durable home before interrupt-prone boundaries).

## 271. Fixture Facts Commit Pre-Branch and Path Assertions Share One Resolve

**Principle:** Family H (verify the real thing: a fixture's staged environment must exist as tracked history at the branch point, and a path assertion is only as sound as both sides' canonicalization).

**Trigger:** authoring a suite test whose fixture branches a worktree and stages environment facts, or asserting equality between a literal temp-dir path and a resolved path on this host.

**Rule:** two arms. (1) A fixture that stages tracked environment files for a worktree-branching test commits them on the fixture base before the test branches; dropping them into the worktree after the branch point leaves them untracked worktree-side, where the run's foreign-dirt gate reads them as foreign dirt and refuses. (2) When a test compares a path built from a literal temp directory against a path from `.resolve()`, derive both sides through the same resolve call; on this host macOS presents user-facing `/var/...` spellings while resolution yields `/private/var/...`, and a one-sided resolve fails every comparison.

**Why:** witnessed 2026-10-27 (playbook repo, the absolute-tmp regression for the migration-manifest destination): worktree-side facts.md tripped the foreign-dirt gate until committed fixture-side pre-branch, and the `/var` duality broke `relative_to` until both sides derived from the resolved worktree root. Second witness 2026-10-30 (playbook repo, an exec-run suite pin over the capture output): the pin first compared a literal temp-dir path inside a substring assertion and failed on the same duality; the fix derived both sides through `.resolve()` with a substring (`assertIn`) shape, which also survives emitted text whose sentence continues past the checked span (the output line's trailing period would have broken an `endswith` pin).

**See also:** #245 (a preservation assertion needs the fixture to move the preserved value).

## 272. Re-Derive a Cold-Start Premise From the Primary Checkout's Live Filesystem

**Principle:** Family A (state re-derivation at validation time: a dispatch premise is another actor's read, and a gitignored state home is invisible to any read keyed on the tracked tree).

**Trigger:** a dispatch payload or consult read asserts a task's state record is missing (a cold start) for a lane whose records live under a gitignored state home, before any action on that premise.

**Rule:** before acting on a cold-start premise, re-derive the record's existence at the task's `state_file` override (or default path) in the primary checkout's live filesystem with a direct probe; a gitignored home makes every record there invisible to a tracked-tree or worktree-side read, which manufactures a cold start whose sanctioned shape (seeding the authorization digest, re-stamping next_due) overwrites a verified record. A cross-check mismatch between the premise and disk stops the run with no sweep and no record write, and the mismatch is reported for the consult-side fix; the payload's own assertion is never the evidence.

**Why:** witnessed 2026-10-27 (playbook repo): the scheduler turn's registry consult recorded "4 registry records cold-missing" and dispatched the re-triage lane as a cold start, while two of the four records existed at their `state_file` overrides under the gitignored `.ai-playbook/friction-audit/` (next_due 2026-11-02 and 2026-11-09); the dispatched child's disk re-derivation caught the mismatch and stopped the run before the record-destroying write shape.

**See also:** #263 (precheck the session's primitives before planning a duty leg: the same before-the-leg precheck family), #172 (a gitignored directory can hold tracked files).

## 273. Rebuild a Conflict-Resolved Shared Log From the Fresh Base; Never Overwrite the File With a Hunk-Only Extraction

**Principle:** Family H (verify the real tree: a conflict resolution composed by extracting lines is only as complete as the extraction's span; a hunk-only extraction written over the file preserves the hunks and destroys everything around them).

**Trigger:** resolving a rebase conflict in a long shared file (a rolling log, a lessons corpus) by scripting a line-range extraction, then writing that extraction over the whole file.

**Rule:** two arms. (1) An extraction that replaces a file must span the whole file (head, hunks, and tail ranges together); a hunks-only selection is never a file body. When the branch's edits to the shared file are few and mechanical, skip conflict surgery entirely and rebuild deterministically from the fresh base: literal replacements with asserted occurrence counts, boundary-verified line-range removals for consumed sections, the receipt appended last, then re-verify the base-side additions are present in the rebuilt text. (2) Read back the diff stat after every conflict resolution and compare it to the expected edit shape before continuing; a delta an order of magnitude beyond the intended change is a destroyed file, and the recovery is a reset to the base plus the deterministic rebuild, never a repair of the truncated text.

**Why:** witnessed 2026-10-27 (playbook repo, exec-mode max-2 run): rebasing an ad-hoc worktree branch over a main that peers moved six times in a day, a conflict in the ad-hoc rolling log was resolved by extracting only the conflict hunks and copying them over the file, truncating it from about 400 lines to 35; the diff-stat readback (+3/-397 against an expected +3/-56) caught it before staging, the base branch was never touched, and the deterministic rebuild re-applied the branch's three log edits from the fresh base in one pass. The same rebuild also repaired quoting artifacts (printf-dropped apostrophes) that the earlier heredoc-composed edits had left in a receipt line.

**See also:** #93 (resolve a landing conflict by union of intents and re-verify every destructive intent), #268 (boundary-verified line-range removal for whole-section deletions), #94 (script a structural move from and against current bytes).

## 274. Never Pattern-Complete a Truncated Sha; Rev-Parse the Full Value at the Point of Use

**Principle:** Family A (state re-derivation: a full object name recalled from conversation context is a plausible-hex fabrication risk, and the tail of a sha is exactly the part memory and transcripts render unreliably).

**Trigger:** any precision step that takes a full sha as an argument (a landing helper's expected tip, a record sidecar's last-fix-commit field, a receipt's digest), when the value at hand is a short prefix seen earlier in the session.

**Rule:** the repo's standing precision rule (re-derive every digest, path, flag, or identifier from disk before a precision-critical step) applies here with a specific mechanism: a truncated sha must never be pattern-completed to full length from recall, because a plausible wrong tail passes every eyeball check and fails only at the consumer. Run `git rev-parse` (or the object form the consumer wants) immediately before the primitive call and paste its output; when a consumer refuses an expected value as unresolvable or mismatched, treat the refusal as the detection working, re-derive, and retry - never re-type the value by hand.

**Why:** witnessed three times in one session 2026-10-27 (playbook repo, exec-mode max-2 run): a review-record sidecar's last-fix-commit field, the same field in the record's Metadata block, and a landing call's expected-tip were each hand-completed from a prefix, and each was caught by its consumer (a staging-validator mismatch twice, the landing helper's unresolvable-tip refusal once, under a held merge lock); each fresh re-derivation produced a different tail than the fabricated one.

**See also:** #82 (ceremony-cited records carry the full digest re-derived from disk), #265 (reconciliation declared values derive from the live artifact, never from prose).

## 275. Re-Pin an Exact Catalog Pin From the On-Disk Union Under Parallel Sessions

**Principle:** Family A (state re-derivation: a pinned enumeration is a read of a shared surface that parallel sessions extend, so a pin failure under concurrency is a stale-read signal, never proof of which catalog is right).

**Trigger:** adding a member to a catalog whose exact-enumeration pin lives in the test suite (a helper's subcommand list, a CLI verb set, an exported-name list) while other sessions land additions to the same surface, and the suite run fails on the pinned list.

**Rule:** re-pin from the catalog as it exists on disk at fix time - the union of your addition and every peer addition already landed beside it - never from your own intended set; resolving the failure by dropping a peer's concurrent member breaks the peer's lane and the next suite run. Keep the pin exact rather than loosening it to containment: the exact enumeration is the mechanism that surfaces undeclared additions, so the fix for a concurrency failure is a fresh read, not a weaker assertion.

**Why:** witnessed 2026-10-27 (playbook repo, exec-mode ad-hoc run): adding a subcommand to scripts/worktree_closeout_migrate.py failed the suite's HelpCatalogTest exact command-list pin; a parallel session had landed its own boundary-mirror subcommand the same day, so the honest re-pin was the union catalog (both additions), and a re-pin to the first session's list alone would have silently deleted the peer's member from the pin.

**See also:** #66 (re-survey the filing destination at write time while a peer closeout is in flight), #163 (re-pin certified homes after a tip move).

## 276. A Per-Form Fixture Loop Accumulating History Pins Only Its First Form

**Trigger:** writing one subTest (or loop iteration) per recognized form where each iteration commits its witness into one shared per-method scratch fixture and the code under test scans the whole fixture history.

**Rule:** rewind the fixture to the pre-loop base at the top of every iteration (`git reset --hard <base>` in a scratch repo, or build a fresh fixture per form), so each iteration's history carries only its own witness; then prove the pins discriminate by mutating the subject away from one non-first form and expecting that form's pin to fail - a green suite under that mutation means the loop is order-masked and pins nothing past the first form.

**Why:** witnessed 2026-10-27 (playbook repo, ad-hoc landing): a per-prefix subTest loop committed each form's landing subject into the one scratch repo its setUp created while the sweep's landedness matcher scans the whole branch, so every later subTest was satisfied by the first form's commit; two panel workers independently verified that dropping any non-first prefix from the matcher left the suite green. The fold added the per-iteration reset, and the confirm round re-verified discrimination with a negative control (deleting the reset line returned the subtests to green).

## 277. A Conflict-Free Rebase Onto a Moved Base Still Stales the Delta Digest

**Rule:** a peer landing on the base branch mid-review invalidates the staged whole-delta digest even when the rebase applies with zero conflicts and both semantic deltas intact: the branch diff's hunk positions shift wherever the peer's landing touched a shared file above the delta's hunks, so `git diff <base>...<head>` re-hashes differently at the new head with no content change. Treat any base move during a review as a digest-invalidating event: after the rebase, re-derive the digest, and re-enter the panel as a rebuild confirm round certifying the new head instead of reusing the prior round's record; the re-entry is owed only when the re-derived digest differs, because peer commits disjoint from the delta's path set leave the three-dot diff byte-identical (blob hashes are content-addressed and no shared file shifts a hunk) and the staged record still names the delta exactly.

**Principle:** Family H (verify the real thing: a whole-delta digest is over diff bytes, and diff bytes carry hunk positions, not just content).

**Trigger:** staging a review record's `Source digest` (or any receipt digest over the branch delta) while the base branch is live under parallel sessions.

**Why:** witnessed 2026-10-27 (playbook repo, ad-hoc exec run): a mid-review peer landing (lesson rows plus a new log entry appended above the delta's hunks in the shared rolling log) rebased cleanly, yet the recomputed delta sha256 differed from the staged record's, forcing a rebuild confirm round before the landing; the same day, a second exec run's landing receipt recorded the identical rebuild-confirm shape after its own mid-review rebase, both conflict-free. Third witness 2026-10-28 (playbook repo, ad-hoc exec run): the post-rebase digest delta was context-only (every delta file but one byte-identical, the run's own hunks unchanged), proven with per-file hunk-equality evidence, so the rebuild confirm round certified the new head without a content re-review. Fourth witness 2026-10-28 (playbook repo, ad-hoc exec run): two mid-review rebases onto a twice-moved main left the whole-delta digest byte-identical both times, the intervening peer landings touching only paths outside the delta's file set, and the landing receipt cites the unchanged r1 digest, so the re-entry consequence keys on the re-derivation's outcome, not on the base move itself. Fifth witness 2026-11-02 (playbook repo, exec resume carrier run): a base that advanced twice while the run sat at a usage wall was rebased in the worktree BEFORE the certifying record was composed, so the round certified the actual post-rebase landing bytes, and a mid-panel peer plan landing left the re-derived digest byte-identical (no delta path touched), so the staged record carried the landing unchanged with no extra round.

**See also:** #182 (a receipt digest binds at the reviewed head, not inside its own preimage); #163 (re-pin every certified home after a tip move); #30 (the validator's checks are the record contract).
## 278. Provision the Gitignored Facts Block Into a Fresh Ad-Hoc Worktree Before Done Setup

**Principle:** Family B (ordering: a boundary script's facts-block resolution is a precondition the run provisions, not a failure the run diagnoses).

**Trigger:** starting an ad-hoc (no-plan) run in a freshly created worktree of a repo whose `.ai-playbook/facts.md` is gitignored, before running the done boundary setup.

**Rule:** copy the primary checkout's facts block into the worktree before the first done setup invocation - `mkdir -p .ai-playbook` first (a fresh worktree has no gitignored home at all, so a bare `cp` onto the worktree path fails), then copy the file - and re-run setup once. A setup failure whose output names facts-block resolution ("cannot resolve plans_dir from .ai-playbook/facts.md") in a fresh worktree is this exact shape, never a repo misconfiguration; the file is machine-local by design and never rides the branch.

**Why:** witnessed twice in one session 2026-10-27 (playbook repo, the 20:00 exec run's two ad-hoc picks): each fresh worktree's first setup emitted the facts-resolution tool error, and the first remedy attempt failed again because the copy skipped the missing parent directory; after `mkdir -p` plus copy, setup passed on both. The same gitignored-facts class already has a test-suite row and a done-setup surface; the suite row's scope is test-only, so the setup surface stays distinct. Third witness 2026-10-31 (playbook repo, an execute-plan worktree run): the plan-execution path hits the identical shape - the fresh claim worktree's first done setup refused the same facts resolution, and the same mkdir-plus-copy cleared it on retry.

**See also:** #270 (copy primary-home run records into the run home), the facts-hermeticity backlog row (the test-suite sibling).

## 279. Re-Derive a Plan's Authoring-Time Measured Set at Execution; the Count Is a Floor, Not the Batch

A plan that bounds its work by a measurement taken at authoring time ("the 21 em-dash hits") is naming a set that rots: the live corpus kept changing between authoring and execution, and the execution-time re-measure found 585 hits where the plan said 21. Treat the recorded count as evidence the class of defect exists, never as the batch to fix: re-run the measurement at execution start, fix the current set inside the plan's declared path scope, and capture the delta (measured-then vs measured-now, plus any residue outside the declared scope) as a durable backlog row instead of silently widening or silently ignoring it. **See also:** #7 (re-derive the plan's edit inventory from live bytes at execution start); this lesson adds the count-as-floor framing, the shrink-vs-grow direction, and the residue-outside-declared-scope capture that #7 does not name.

**Why:** witnessed 2026-10-27 (this repo, plan `2026-10-04-maintenance-doc-hygiene-review.md` Task 1): the vendored agterm skill alone had grown 477 new em-dashes after the plan's measure; an executor that fixed exactly 21 would have passed its own checkbox while leaving the done-when (zero live-corpus hits) permanently unreachable.

## 280. The Origins Gate Seeds From the Markdown Header, Not the Frontmatter Array

**Principle:** Family H (verify the real thing, not the abstraction: the parser's actual input surface, not the data being present somewhere in the file).

**Trigger:** authoring or repairing a plan that declares backlog origins, when the origins data exists in more than one surface form (a frontmatter array and a markdown header block).

**Rule:** a gate that parses the plan document reads only the surface its grammar names, never a semantically equivalent form elsewhere in the file. Declare backlog origins in the plain `Backlog origins (scope of record):` markdown header the origins checker parses; a frontmatter `backlog_origins` array does not seed it. When a coverage gate refuses with "no origins" over a file that visibly carries origins data, suspect a form mismatch before missing data, and re-derive the accepted shape from the checker's parser before editing.

**Why:** witnessed 2026-10-28 (playbook repo, authoring run): two plans carried only the TOML `backlog_origins` array; the coverage gate read "no origins"; adding the header post-certification changed the certified bytes and forced a delta certification round. See also #104 (the origins archive gate's row-disposition refusals); #179 (the disposition-heading grammar).

## 281. An In-Round Fix Re-Binds the Certification Seal's Start Anchor

**Principle:** Family A (precision-critical anchors: a seal binds the bytes its round certifies, so the start anchor moves with the bytes).

**Trigger:** an authoring certification round folds a disclosed fix mid-round, and the readiness gate then refuses the record pair as a bare rewrite.

**Rule:** re-anchor the in-progress seal round's `round_start_commit` and `round_start_digest` to the fixed bytes and add a disclosure note naming the fold. The refusal fires because the seal's start digest no longer equals the staged record's source digest; the corrections arm it names is scoped to post-certification rewrites, so an in-round disclosed fix answers the refusal by re-anchoring, not by opening a corrections row.

**Why:** witnessed 2026-10-28 (playbook repo, plan-review r2): a mid-round Low fold changed the plan bytes after the seal was drafted; re-anchoring the seal to the fix commit with a disclosure note cleared readiness.

**See also:** #185 (close anchors bind where the certified bytes landed), #205 (an earlier round validates against its own bytes), #32 (the machine-resolvable seal shape).

## 282. A Date Dispute May Be an Author-Committer Field Mismatch

**Principle:** Family A (precision-critical values re-derived from disk: a commit carries an author date and a committer date, and a citation must say which field it means).

**Trigger:** two review records, or a record and a plan text, cite different dates for the same change and one side is about to be discarded as a mismatch.

**Rule:** print both fields (`git log --date=iso --format='%h %ad %cd'`) and match each side's date to its field before discarding a finding or editing text; when writing a landing or drift date into a record, name the field.

**Why:** witnessed 2026-10-28 (playbook repo, plan-review r2): two workers disputed a drift date by days; the two git date fields showed each worker right about a different field, the plan text was correct, and the finding was discarded only after the field check.

**See also:** #274 (derive the value at the point of use, never from memory).

## 283. A Redirection Write Truncates Its Destination Even When the Producer Emits Nothing

**Principle:** Family D (state-first: the write surface commits before the producer's success is known).

**Trigger:** transforming a tracked file through a shell redirection (`sed ... <source> > <dest>`, or any `producer > existing-tracked-file`) where the producer's input is re-derived mid-flow and may be stale or absent.

**Rule:** a redirection opens and truncates the destination before the producer runs, so a producer that fails or emits nothing (a stale source path, a filter with no matches) silently reduces an existing tracked file to zero bytes; the command's non-zero exit does not undo the truncation. Before any in-place-by-redirect write to a tracked file, verify the producer's source exists and its output is non-empty: write to a temp file, check it, then move over the destination (or capture to a variable and test it first). A sudden zero-byte tracked file after a transform is this shape, and `git checkout -- <path>` restores it.

**Why:** witnessed 2026-10-28 (playbook repo, a backlog-row retirement pass): a `sed` transform over a living backlog row redirected into the row's completed/ twin, but the living origin row had already been archived by an earlier landing, so sed read nothing and truncated the existing twin to 0 bytes; the truncation was caught on the immediate post-write re-read and restored with `git checkout --`. The redirect was chosen over `sed -i` precisely to avoid the in-place self-overwrite class, trading it for this truncation class instead.

**See also:** #130 (an absence signal needs an untruncated or exact-match probe); the chained-command exit-gate family (a producer failure must stop the chain that consumes it).

## 284. A Mutation Check Must Not Restore From HEAD Inside a Worktree Holding Uncommitted Own Edits

**Principle:** Family B (ordering: the verification procedure runs after the work it must not destroy, and its cleanup step is scoped to what the check itself created).

**Trigger:** running an apply-and-revert mutation check (apply a candidate change, run the affected test, revert) in a worktree where the checked-out source file also carries the worker's own uncommitted edits for the pass in flight.

**Rule:** a mutation check's revert step that restores from `HEAD` (`git checkout HEAD -- <path>`) discards every uncommitted edit the same worktree holds for that file, including the worker's own in-flight pass edits, and the check still exits green - the destruction is silent. Snapshot the worker's own edits first (stash or copy), or run the mutation check on a scratch copy of the file (the in-session fallback's established shape), never a bare HEAD restore in a dirty worktree. After any mid-pass mutation check, re-verify the pass's edits are still present before continuing; a validation battery that suddenly reports the pre-edit baseline is the symptom.

**Why:** witnessed 2026-10-28 (playbook repo, an exec run's address pass over a review finding): the dispatched worker's own mutation check ran `git checkout HEAD` on the script under edit, wiping the pass's accumulated edits mid-flight; every edit had to be re-applied in full and the validation battery re-run. The cross-worker overlap sibling (a mutation check's transient red confusing a sibling) is separately witnessed; this is the self-destruction arm, which no existing lesson covered.

**See also:** the mutation-check overlap lesson (transient red from concurrent apply-and-revert cycles); the scratch-copy in-session fallback.

## 285. A Review Fold's Remediation Text Can Push a Plan Criterion Past the Readiness Byte Limit; Split the Criterion

**Principle:** Family F (bounded growth: a gate with a byte budget and a workflow that appends to the gated surface must check the budget at fold time).

**Trigger:** folding a review round's remediation or clarifying text into an existing plan evaluation criterion (an `[x]`/`[ ]` line) when the plan readiness gate enforces a per-criterion byte limit.

**Rule:** appending remediation prose to an existing criterion line is the fold shape most likely to breach a per-criterion byte limit, and the breach surfaces late - at the next readiness pass, potentially under the landing lock. When folding round findings into plan criteria, prefer splitting the grown criterion into two criteria (each carrying its own checkbox) over appending to one line, and re-check the byte budget immediately after the fold rather than at the next gate invocation. A readiness refusal naming a byte limit over a criterion the last fold grew is this exact shape, never a gate defect.

**Why:** witnessed 2026-10-28 (playbook repo, an exec run's r2 fold): the remediation text appended to Task 2's criterion grew it to 696 bytes against the readiness gate's 512-byte limit, and the mid-loop readiness pass refused; splitting the criterion into two checkbox lines resolved it. The gate's limit is by design; the lesson is the fold-time discipline, not a limit change.

**See also:** the plan-readiness certification family; the review-fold minimal-convergence doctrine.

## 286. A Subagent Inactivity Timeout Is Not a Termination Proof; Verify Liveness From Disk Before Relaunch

**Principle:** verify-before-relaunch. **Shape trigger:** a host harness reports a subagent "inactive for Nms" (or similar timeout error) mid-task.

A harness inactivity signal is not evidence the worker stopped: the witnessed run kept editing its owned files for roughly forty minutes after the timeout was reported, then went quiet without ever writing its required session log. Before relaunching a timed-out worker or taking over inline, verify termination from disk: re-stat the task's owned paths across a stability window (no mtime movement), check for the session log the worker was required to write before returning, and confirm the run branch tip is unchanged. Only a stable window with no log and no tip movement counts as verified terminal. Record the observed state as the relaunch's pre-restart record (branch tip, in-flight paths, lost-evidence inventory such as RED-pass evidence that died with the worker) so the resume verifies against disk instead of conversation memory, and reconstruct lost discipline evidence in a scratch copy rather than stashing or resetting the real worktree.

**See also:** the execute-plan timeout and recovery rules; the Worktree-first standard's Live-session discovery ladder. Re-witnessed 2026-10-31 (playbook repo, exec run): after two workers stalled at the inactivity wall in one task batch, the resume was addressed to the wrong stalled worker's agent id (the earlier task's, not the current one's), burning roughly half an hour of dispatch on a resume that could not advance the stalled task - liveness verification and address verification are separate checks, and the resume must be sent to the agent id that owns the stalled task.

## 287. The Archive-Egress Evidence Leg Reads the Resolving Checkout's Reviews Home; Mirror the Exec Receipt Into the Run Worktree Before the Retry

**Principle:** gates read the checkout they resolve, not the session's memory of where records live. **Shape trigger:** a `land-worktree` run whose `check-archive` leg refuses with "missing evidence leg: exec-review record ... under .ai-playbook/reviews/" while the named record verifiably exists in the primary checkout's reviews home.

The reverse-squash guard's archive-egress check resolves the reviews home inside the checkout it runs from, and a worktree-complete landing runs it inside the run worktree. When the run follows the transfer-in mirror-skip shape (the reviews home created empty in the worktree, records written directly to the primary home), the gate sees an empty home and refuses even though the receipt exists - the writer must mirror the exec receipt (and any cited review record) into the worktree-side home before the landing retry. A refusal that survives a receipt re-derivation from the primary home is this exact shape, never a missing record: re-check which home the resolving checkout holds before editing the receipt.

**Why:** witnessed 2026-10-27 (playbook repo, the run-tmp-evidence-loss-sweep-scope-out landing): the receipt was written to the primary reviews home; two consecutive landings refused with the identical missing-evidence message; mirroring the two records into the worktree's `.ai-playbook/reviews/` passed the gate on the next attempt unchanged. Second witness 2026-10-31 (corrections-chain-recursion-refusal-and-pins landing): the backfilled egress record sat only in the primary home and the refusal repeated byte-identically; copying the same file into the worktree-side home (no edits, no receipt rewrite) passed on the next land, confirming the record-copy remedy over any receipt edit. Third witness 2026-11-01 (plan-prompts-stub-writer-forensics landing): with the record mirrored into both homes the refusal persisted because the demanded egress digest was absent from the record's content - the backfill append was `&&`-chained after a failing sha probe (the archived file exists only in the worktree pre-landing) and was silently skipped, so the mirror shipped stale bytes; verify the demanded digest is actually present (`grep -c <digest> <record>` in both homes) before retrying the landing, and note the evidence-satisfied ack becomes an unused-ack refusal (the ack is an alternative exit, not an additive leg).

**See also:** the Worktree-first standard's Transfer-in mirror-skip paragraph; the resolve-at-use digest rule.

## 288. A Baseline-Relative Closeout Migrate Reports a Stale-Baseline Strand as a Clean Zero

**Principle:** a success-shaped empty result is distinguishable from a correct empty result only if the tool itself says which one happened; otherwise the reader supplies the optimistic reading. **Shape trigger:** a closeout migrate leg that copies "new or modified versus a baseline" reports `Migrated 0` while the run's owned paths visibly hold records.

**Rule:** when a baseline-relative closeout migrate completes with zero migrated entries, re-derive the zero against the run's own records before teardown: compare the run worktree's owned paths against the primary checkout directly and check the baseline capture's timestamp against the newest owned-path mtime. A baseline captured after the run's edits (the common shape: capture at closeout start, edits from the implement and review phases before it) diffs empty by construction, and the carry must then be done as a manual worktree-versus-primary delta; a shared telemetry ledger in both trees is append-merged, never replaced, or the primary's live rows are truncated. Never treat the clean `Migrated 0` line itself as the carry proof.

**Why:** witnessed 2026-10-28 (playbook repo, an execution closeout): the baseline-relative migrate reported `Migrated 0` for a run holding 35 run-era records and 221 scratch files; the records were recovered by a direct delta carry with an append-merge of the shared invocation ledger, and the silent-zero gap is tracked with a warning-only report arm in docs/history/backlog/2026-10-28-closeout-migrate-zero-delta-silence.md (entry closeout-migrate-zero-delta-silence in docs/history/backlog/EXEC-PROMPTS.md).

**Why:** witnessed 2026-10-28 (playbook repo, an execution closeout): the baseline-relative migrate reported `Migrated 0` for a run holding 35 run-era records and 221 scratch files; the records were recovered by a direct delta carry with an append-merge of the shared invocation ledger, and the silent-zero gap is tracked with a warning-only report arm in docs/history/backlog/2026-10-28-closeout-migrate-zero-delta-silence.md (entry closeout-migrate-zero-delta-silence in docs/history/backlog/EXEC-PROMPTS.md). Second witness 2026-10-31 (a resumed dead run's closeout): after a session-dir sweep ate the baseline and a late recapture was made mid-closeout, the re-run migrate's adjudication skipped the run's review records entirely (the fresh capture postdated them, so the empty diff read as already-carried); the carry was completed as a manual scoped copy of the skipped records into the staging set with digest verification of each copied file against its worktree original, and the manual-delta remedy extends to per-record copying, not just whole-tree deltas.

**See also:** the Worktree-first standard's closeout migration paragraphs; the same-run mirror replacement landing's receipt-gated transfer.

## 289. A Zero-Plan Closeout's Branch-Only Gate-Removal Needs the Migrate-Manifest Shape, Not the Scoped-Copy Record

**Principle:** Family D (state-first: a consumer's enforced input contract is the shape of record, not a producer-side record that merely describes the same artifacts). **Shape trigger:** a branch-only `gate-removal` (`--branch` without a worktree) after a zero-plan closeout refuses with "branch-only closeout produced no branch accounting" although the session manifest lists every transferred artifact with verified digests.

**Rule:** the branch-only adjudicator reads the migration manifest's shape, not the zero-plan scoped-copy record's: the manifest must carry a `branch` list whose latest record binds (`branch` naming the source branch, `source` the worktree) plus `migrated` entries (`destination`, `verified: true`, `sha256`) for the transferred gitignored artifacts. When no execute-plan transfer-out wrote one (the zero-plan fallback's session manifest deliberately adds no migration-manifest field), hand-build that shape and pass it at an explicit `--migration-manifest` path, deriving the fields from the adjudicator's reader in `scripts/worktree_closeout_migrate.py` (records[-1] is the authoritative binding; migrated entries need per-artifact digests), then re-run the gate: only a pass that adjudicates the branch (ancestry-accounted or exact-tree-accounted) authorizes its removal.

**Why:** witnessed 2026-10-28 (playbook repo, an ad-hoc EXEC run's post-landing teardown): pointing `--migration-manifest` at the zero-plan scoped-copy manifest found no branch record and the gate refused instead of adjudicating; reshaping the same file into the migrate shape (branch record plus digest-verified migrated entries) produced `exact-tree-accounted` and `OUTCOME: pass` on the next run unchanged.

**See also:** #65 (the validator as the contract over the recipe); the Worktree-first standard's Transfer-out-and-deletion baseline-less arm; the done skill's zero-plan skip-record paragraph.

## 290. A Pathspec Commit Lands the Named Paths' Worktree Content and Ignores Their Index Entries

**Principle:** Family H (verify the real thing: re-derive what a commit actually captured from the commit itself, never from the staging step that preceded it). **Shape trigger:** an index-blob construction (`git hash-object -w` + `git update-index --cacheinfo`) on a file whose worktree copy carries foreign dirt, followed by `git commit -- <path>`; or any commit whose `--stat` deletions exceed the author's own hunks.

**Rule:** the pathspec form of commit takes each named path's working-tree content and never reads that path's staged entry, so on a foreign-dirty file it transplants the worktree's foreign deletions or edits into history even though the constructed blob sits in the index. When the worktree holds exactly the intended content, commit the worktree content deliberately (`git add <path>` plus the pathspec commit, then verify); when the worktree carries foreign dirt that must not be committed, the constructed index entry is not enough: make the worktree file hold exactly HEAD plus own edits for the commit's duration and re-apply the foreign dirt afterward, or plan the corrective commit up front. Either way, verify the landed bytes before building on them: diff `git show HEAD:<path>` against the intended content and read the commit's `--stat` deletions against the author's own hunks.

**Why:** witnessed 2026-10-28 (playbook repo, a learn run over the shared primary checkout): the constructed blob carried HEAD plus the run's two lesson edits only, but the pathspec commit landed the worktree copy, transplanting a peer session's uncommitted deletions of two landed witness blocks into history (caught by the commit's `--stat` reading 4 deletions where the own hunks had 1); base-branch immutability made the repair a corrective restore commit (`f69f12577`) re-adding both blocks, and the intended corpus state was reached only across the two commits. Second witness 2026-10-31 (playbook repo): even the plain `git add <path>` plus pathspec commit arm carries the same hazard on a shared checkout - the index is shared, so the add swept a peer session's staged deletions of the same path into the commit; caught the same way (--stat deletions vs own hunks) and repaired with a corrective restore. Pre-commit mechanical check on a shared checkout: `git status --short` staged column and `git diff --cached -- <path>` before any add. Third witness 2026-10-31 (playbook repo, an exec carrier run's landing): even the staged-column check is insufficient when the sweep source is the WORKING TREE - a plain multi-path `git add` swept a peer session's uncommitted working-tree edits (an unlanded fix plus its fixtures and doc-registry rows) authored between the run's file reads and the add; the `--stat` read missed it because the swept paths were whole-file changes the run had legitimately touched, and the sweep surfaced only through a downstream test suite at the landed HEAD and the focused review panel. So the shared-checkout discipline is two checks, not one: immediately before the landing commit, re-derive the changed-file set (`git diff --cached --name-only`) and diff it against the hunks you authored (a foreign path or a foreign hunk inside a shared path goes back to its owner session before the commit); and after any landing on a shared checkout, run the touched surface's test suite at the new HEAD before declaring the landing done - the suite is the catcher when the diff read is not.

**See also:** #227 (a landing's recorded sha comes from the landing receipt: the verify arm); lesson 234's second witness (the sibling capture surprise: a pathspec commit landing the whole staged index); the index-blob construction practice for committing own hunks out of a foreign-dirty file.

## 291. A Record Field That Wants a Digest Is Authored Empty or With a Freshly Computed Value, Never With a Composed Plausible-Looking One

**Principle:** Family H (verify the real thing: re-derive from disk at the moment of use). **Shape trigger:** authoring a durable record (review record, receipt, manifest) whose template carries digest fields, while the derivation commands have not all been run yet.

**Rule:** when a record template's digest field cannot be filled from a command output already in hand, leave it empty (with an explicit `pending` note) or stop and run the derivation command before writing the record; never compose a value that merely looks like the right shape (a full-length hex string, a familiar commit prefix) to keep the record template complete. The composed value is worse than an empty field: it reads as evidence, passes format checks, and survives into history. The correction path is the same as the composition path - run the real command and replace the bytes before anything downstream reads the record.

**Why:** witnessed 2026-10-28 (playbook repo, an execution closeout backfilling an exec-review record): the authoring pass wrote a full-length `source_digest:` hex value into the record before any diff-digest command had been run, then self-audited the record, caught that the value was composed rather than derived, ran the real `git diff | shasum`, and corrected the line before the landing gate read it. Nothing downstream consumed the composed bytes, but the record was one gate failure away from citing a fabricated digest as review evidence.

**See also:** #89 (a value quoted from conversation context is not evidence - the transcription variant; this is the composition variant, where no source value ever existed).

**Distinguishing (range digests over a not-yet-existing range):** a real command can also produce a wrong digest when it runs before its input exists: witnessed 2026-10-28 (playbook repo, an exec-run code-family record): `git diff <base>...HEAD | shasum` was run before the staged work was committed, the range was empty, and the field filled with the empty-input digest; the fix is ordering, not composition - commit the range first, then derive the range digest, and re-check the field when the derivation order changes.

## 292. Prompt-Log Worktree Dirt Is Verified Against Its Own Description Before Any Commit Carries It

**Principle:** Family H (verify the real thing: read the diff, not the label). **Shape trigger:** a dirty or staged rolling prompt log described as a prune, cleanup, or residue to carry; any diff whose deletions exceed the described entries.

**Rule:** before a commit carries prompt-log changes, read the diff and check every removed entry or receipt-ledger line against its witness (a removal with its receipt in the same change, or the removal itself recorded in a landed commit); a rewrite that drops the header, whole entry sections, or receipt-ledger lines wholesale is corruption, not a prune - restore it from HEAD instead of carrying it, and record the refused carry. The description a carrier receives (operator wording, a note, a manifest row) is a claim to verify, not evidence; "surface instead of proceeding" applies exactly when the diff contradicts the description. Uncommitted ledger-corruption dirt left in a shared checkout is itself a hazard: unattended sessions commit dirt they did not author, so the restore-and-record is the safe terminal, never leave-and-report alone.

**Why:** witnessed 2026-10-28 (playbook repo, a closeout-completion session): the primary checkout carried uncommitted dirt rewriting PLAN-PROMPTS.md from its 407-line ledger (header, entry sections, and twenty receipt-ledger lines) to a three-line fixture-style stub, described to the session as "the PLAN-PROMPTS.md prune"; the session read the diff, refused the carry, restored the file from HEAD, and verified the full ledger intact. The sibling class is the 42610a0a2 freeze-revert repair (a stale-copy compose that silently restored pruned entries and dropped receipts - damage committed, then repaired by a corrective commit), and the land-worktree prompt-log audit wired 2026-10-28 (plan docs/history/plans/completed/2026-10-28-landing-gate-prune-audit-leg.md) now refuses the committed form; the uncommitted form has no gate, only this read-first rule.

**See also:** #44 (a receipt lives where its auditor parses - the receipted-removal grammar this rule verifies against), #290 (unattended commits sweep foreign staged bytes - the reason leave-and-report is not the terminal).

## 293. Primary-Checkout Dirt Byte-Equal to a Landing's Parent Is a Dead Peer Landing's Stale Snapshot; Restore From HEAD and Leave the Peer's Branch Alone

**Principle:** Family H (verify the real thing: re-derive from disk before acting on a hypothesis). **Shape trigger:** after a concurrent peer run dies mid-landing, uncommitted staged-plus-worktree edits appear in the shared primary checkout whose content looks like a revert of the just-landed work.

**Rule:** diagnose suspect primary-checkout dirt before draining it: byte-compare the dirt against the suspect landing's parent image (`git show <landing>^:<path>` against both the index and worktree bytes). Byte-equality proves the dirt is the dead run's stale pre-landing snapshot (its abandonment froze the primary mid-landing), not a live peer's work; the drain is `git restore --source=HEAD --staged --worktree <paths>` (HEAD already holds the landing, so the restore removes only the stale snapshot), followed by re-running the gates the touched paths feed. Never delete the dead run's branch or residue as part of the drain: a stale claim plus vanished state is not proof the run is dead, and its own closeout owns its artifacts.

**Why:** witnessed 2026-10-29 (playbook repo): right after a landing completed, the primary checkout held a staged revert of that landing's instruction wiring across three files; byte-equality against the landing parent's image proved it was a concurrently-dying peer landing's stale snapshot (its merge-lock hold was abandoned and self-reclaimed), and the restore-from-HEAD drain left the pins suite passing with no peer state touched.

**See also:** #292 (dirt is verified against its own description before any commit carries it - the same read-first discipline, carried shape), #290 (unattended commits sweep foreign staged bytes - the reason the drain cannot wait).

## 294. A Staging Record Writes All Four Severity Groups Even When Empty

**Principle:** Family A (make the contract machine-checkable: the record grammar is the validator's contract, and a soft exit code is not a clean record). **Shape trigger:** synthesizing a review-staging record for a round whose findings do not reach every severity tier.

**Rule:** a review-staging Markdown record carries the Critical, High, Medium, and Low group headings in every round, writing "None." under a group with no findings; the validator refuses a record missing any group, and preflight (soft mode) prints that refusal while still exiting 0, so a soft-mode pass is not evidence the record structure is complete - read the error lines, not the exit code.

**Why:** witnessed 2026-10-29 (playbook repo): a certifying round with no Medium findings omitted the Medium group; the preflight printed the missing-groups error beside the expected stale-digest error and exited 0, and the gap surfaced only because the run read the error lines.

## 295. Prove a Landing Delta by Owned-Path Byte-Identity Instead of a Doomed Replay

**Principle:** Family H (verify the real thing: the delta proof is about the end state, not the commit chain). **Shape trigger:** a landing step wants a rebase onto a moved base whose tip already carries the branch's certified content.

**Rule:** when the rebase exists only to prove the branch's delta and the branch's owned path set is small and closed, prove the delta directly: byte-identity or tree equality of every owned path between the branch tip and the base tip, then skip the replay and record the proof. A multi-commit replay onto a base carrying the branch's content conflicts at every replayed commit even when the end state is byte-identical, and each manual resolution is a fresh corruption surface.

**Why:** witnessed 2026-10-29 (playbook repo): an authoring closeout's branch held thirteen plan-edit commits while the base's certification checkpoint already carried the certified bytes; the replay conflicted at the first commit and would have conflicted at all thirteen, so it aborted and the landing recorded the zero-delta proof (one owned path, identical sha256 at branch tip and base tip), with the teardown sweeps running over the checkpoint commit.

**See also:** #123 (a squash landing absorbs the branch; post-landing branch work rebases as a reset - the refresh context this rule's proof-only context is distinct from), #277 (a conflict-free rebase onto a moved base still stales the delta digest - the digest-re-derivation this proof feeds), #73 (the consumed-branch fact behind the tree-equality deletion arm - the same proof at the teardown boundary).

## 296. A Corrective Closeout Migrate Cannot Unrecord a Prior Run's Manifest Entries

**Principle:** Family D (state-first: an append-merged record is durable by design, so a corrective re-run of the producing tool cannot retract what an earlier misconfigured run wrote; clearing requires deleting the record, never re-running). **Shape trigger:** a closeout migration re-run after hand-cleaning mis-migrated residue still fails the branch-accounting gate on entries naming paths that were just removed.

**Rule:** when a closeout migrate mis-fires (an over-broad `--dirs` override, a wrong baseline scope) and the residue is cleaned by hand, delete the migration manifest before the corrective re-run: the manifest writer append-merges each section into any existing file, so the corrective run's zero entries leave the prior run's renamed/migrated rows standing, and the gate-removal branch accounting reads them as artifacts that must exist under the target, retaining the branch for operator resolution. Verify the corrective manifest reads clean (empty migrated/renamed) before the gate-removal pass.

**Why:** witnessed 2026-10-29 (playbook repo, an execution closeout): a first migrate run with an over-broad `--dirs` override foreign-renamed tracked edits as `.wt-` residue in the primary checkout; after hand-cleaning the residue, the re-run over the same manifest path appended nothing and the gate-removal pass retained the branch on the phantom entries; deleting the manifest and re-running produced the clean empty manifest the gate needed.

**See also:** #288 (a stale-baseline migrate reports a clean zero - the zero-delta silence this rule's manifest-clearing complements), #289 (the branch-only gate-removal's manifest shape requirement - the same consumer reading these entries).

## 297. A Foreign Finalized Manifest Binds the Done Commit Gate Session-Wide

**Principle:** Family D (state-first: shared durable session state binds later operations, and the gate's refusal names the binding that actually fired, not the one you selected). **Shape trigger:** a done runner commit refuses with a manifest-not-bound error although this run's own manifest is present and freshly set up.

**Rule:** when a done runner commit refuses with "the selected run manifest is not bound to the newest root-confirmed marker" and the binding names another run's finalized manifest in the same shared done session, do not delete or edit the foreign manifest and do not retry through re-setup; a fresh setup and an explicit manifest selection re-refuse identically. The bounded remedy is a plain path-scoped commit of exactly this run's own files under the still-held done lock, with ref and OID re-verified. File a defect row for the binding gate. The refusal is per-session state, not persistent corruption.

**Why:** witnessed 2026-10-29 (playbook repo): after a peer run's finalized foreign-suffixed manifest landed in the shared done session, three commit attempts refused identically, fresh setup and explicit manifest selection included; the plain path-scoped commit landed cleanly and the next session's freeze committed normally. Defect row: docs/history/backlog/2026-10-29-done-run-commit-manifest-binding-refusal.md.

## 298. A Gate Refusal's Cleanup Can Revert Your Uncommitted Edits

**Principle:** Family H (disk truth: a failed command's cleanup path is part of its side effects, so the working tree is re-derived from disk after any refusal). **Shape trigger:** an edit applied before a refused guarded commit is reported absent by a follow-up grep, or the retry says "nothing to commit".

**Rule:** when a guarded commit tool refuses, assume its refusal path may run owned-delta cleanup over the working tree. Re-read the target files from disk before re-applying your edits. Do not trust a post-refusal grep that reports your edit absent: after a revert it faithfully reads HEAD, which is exactly what your edit's absence looks like. Re-apply mechanically (a scripted string replace, not a remembered patch) and re-verify before the next attempt.

**Why:** witnessed 2026-10-29 (playbook repo): a refused done commit's owned-delta cleanup reverted the session's uncommitted queue-freeze edit; the follow-up grep showed the frozen line still at HEAD and only the tool's "nothing to commit" error revealed the edit was gone; a scripted replace re-applied it and the commit landed.

**See also:** #284 (a mutation check's HEAD restore destroying uncommitted own edits - the sibling self-destruction arm, a cleanup step scoped to nothing it created).

## 299. An Exact-Ancestor Unfreeze Reads as a Leaked Revert

**Principle:** Family B (error-policy direction: a legitimate change that is evidence-indistinguishable from a violation class needs the gate's own authorization arm, not a reworded change or a bypass). **Shape trigger:** a guarded commit restoring a file to an earlier committed version is refused as a leaked revert.

**Rule:** restoring a file to an exact ancestor vintage (releasing a freeze by restoring pre-freeze bytes) is byte-indistinguishable from a revert leak, so a cached-diff guard correctly refuses it. Look inside the refusing gate for a purpose-built authorization (here `--authorize-ancestor-restoration <path> <staged-blob-id>` naming the restored blob id) instead of splitting the change, restaging around the guard, or editing the validator mid-lane.

**Why:** witnessed 2026-10-29 (playbook repo): the unfreeze of a queue entry restored pre-freeze bytes exactly matching the ancestor vintage; the cached-diff guard refused the commit as a leaked revert, and the authorize flag with the staged blob id landed it in one step.

## 300. An Exclusion Filter Keyed on the Audited Token Deletes the Match Class

**Principle:** Family H (verify the real thing: an audit's clean result is evidence only when the query could have surfaced the violation). **Shape trigger:** a defect-hunting grep reads suspiciously clean, and its pipeline carries an exclusion stage keyed on the token family the audit hunts.

**Rule:** an audit query that enumerates violations must not carry an exclusion stage keyed on the audited token family: the sought lines contain the token too, so the exclusion deletes exactly the match class and the audit reads clean over a standing defect. Run the hunt query unfiltered and read every line (or filter only after counting, for presentation), and treat a zero-hit result from a filtered pipeline as unproven rather than clean.

**Why:** witnessed 2026-10-29 (playbook repo, ad-hoc exec run): the pre-landing sweep for dangling reciprocal Cluster pointers piped through an exclusion naming the covered sibling's slug; the dangling pointer lines themselves quoted that slug, so both were filtered out and the sweep read clean until the review panel's Medium finding named both pointers, and the re-run without the exclusion listed them immediately.

## 301. Compose a Prompt-Log Branch So Each Receipt Line Lands Once

**Principle:** Family D (state-first: a per-commit gate reads the branch's intermediate states as history, so the commit sequence itself is part of the audited state, not only the net diff). **Shape trigger:** a landing gate that audits per-commit deltas flags a line the branch itself introduced earlier in the same branch.

**Rule:** the prompt-log prune audit walks per-commit deltas, so a receipt line an early branch commit adds and a later branch commit rewrites presents a removal in the rewriting commit's delta even though the net branch diff only ever adds it. Compose before landing: when a fold or rider pass must amend a receipt line, squash the composition onto the implementing commit (`git reset --soft` to it, re-commit once) so the line is added exactly once in its final form, and re-run the audit over the recomposed branch.

**Why:** witnessed 2026-10-29 (playbook repo, ad-hoc exec landing): the prune audit flagged RECEIPT-LINE-REMOVED-WITHOUT-WITNESS against the fold commit that reworded the receipt line an earlier branch commit had added; squashing riders and fold into the implementing commit left one adding commit and the re-run reported PRUNE-OK.


## 302. Byte-Payment Deletions in Skill Text Can Trip Count-Pins

**Principle:** Family C (mechanical safety: a text edit that reads as a clean dedupe can be a guarded span's only witness). **Shape trigger:** paying for added skill-text bytes by deleting "equivalent" same-file text, with the hygiene and anchor greps passing.

**Rule:** before paying for skill-text growth with same-file deletions, sweep the deleting target against the pins gate's count-gated spans (`scripts/check_maintenance_pins.sh`) and run that gate at the task boundary, beside the hygiene scan; a span the pins gate counts cannot be a byte-payment source, and the fix is restoring the pinned bytes verbatim and taking the payment from unpinned duplicate text, never editing the pin.

**Why:** witnessed 2026-10-29 (playbook repo, exec run plan-new-plan-seal-anchor): the implement worker paid its +bytes by deleting a rule-6 sentence the pins gate count-gates to exactly 1; the intermediate review caught the red pins gate the implement validation never ran, and the fix restored the span and paid from the Budget-gate stub tail duplication instead.


## 303. A Multi-Site Prose Fold Adds a Same-Scenario Agreement Check Across Its Touched Sites

**Principle:** Family H (verify the real thing, not the abstraction: each site's pin passing is not the agreement; the agreement is one concrete scenario producing one outcome at every site the change touched). **Shape trigger:** a change that lands one duty or classification as paying folds into several operative prose sites (sibling modules, or two clauses of one file), validated by per-site greps, absence pins, or a pins suite.

**Rule:** before calling such a change green, derive one concrete scenario through every touched site and compare the outcomes (for a deferral/override classification: an interactive session with a live directive, walked through each module's sentence; for an enumeration: one item, checked against both the enumeration that admits it and the clause that excludes it). Fix disagreements at the site the owning contract names, and keep the scenario as the check the next fold over the same sites re-runs. Per-site greps verify that literals are present or absent; they cannot see that two green sites give opposite answers for the same case.

**Why:** witnessed 2026-10-29 (playbook repo, an execute-plan Task 1 folding the stop-before-exhaustion park arm across seven maintenance modules): both round-1 blocking findings were self-contradictions inside the change's own hunks while every grep and the pins suite were green. The zcode.md deferral sentence classified three pauses as overridable where decisions.md's integrity-defer rule made two of them unconditional, and the state-file.md writer enumeration admitted a budget_pause record as a write mode the same edit's other paragraph forbade. The intermediate reviewer derived the scenario the validation set never ran.

**See also:** #291 (evidence is derived, never composed; the agreement derivation is the derived form a green grep set does not give you), #292 (read the changed text itself, not its description; the same read-first discipline applied across sites instead of within one).


## 304. A Needle-Restating Change Proves Its Validator Blast Radius by Running the Pre-Change Validator Against the New Tree

**Principle:** Family H (verify the real thing, not the abstraction: "the suite passes" does not say which pins the change touched, and a needle restated in the validator can silently vacate a second pin that still names the old wording's target). **Shape trigger:** a change that edits a pins-suite (or any validator's) needle, its region scoping, or the operative text a set of needles matches.

**Rule:** when a change restates a validator needle, run the PRE-change validator copy against the POST-change tree (process substitution or a scratch checkout; the validator must stay read-only on the tree) and read its failure list: exactly one failing entry, the intended restatement target, proves no other pin silently depended on the old wording; a longer list is the real blast radius and every extra entry needs a deliberate disposition before the suite is made green. Then run the post-change suite for the green. The pair of runs is the evidence; either alone hides the class - green-only hides the vacated twin, red-only hides which entry was the intended one.

**Why:** witnessed 2026-10-29 (playbook repo, an execute-plan Task 2 amending the maintenance pins suite's execution-lane stance span pin): the differential run (HEAD pins script vs current tree) returned exactly the one intended failing pin, proving no other pin carried a cap-wording literal that the five-site text sweep could have silently vacated, and the variant-grep sweep for evasive spellings came back clean beside it.

**See also:** #303 (same-scenario agreement across a fold's touched sites; this lesson is the validator-side twin: enumerate what the change touched in the validator, not only in the text), #227 (verify from the receipt/commit, not the staging step).


## 305. Digest Verification Binds to the Invoking Checkout's HEAD, and a Selection Record's Digest Is the Selection-Filtered Digest

**Principle:** Family H (verify the real thing, not the abstraction: the same digest function produces different true values depending on which repo HEAD and which byte scope it is pointed at, so a correct-looking verify can pass against nothing). **Shape trigger:** a workflow step that verifies a review or receipt record's source digest, or that records a digest for a diff-derived review record.

**Rule:** run a record's digest-verify subcommand from the checkout whose HEAD the digest was computed against (the run worktree during execution, not the primary checkout after a boundary), and take the recorded digest from the same selection machinery that defines the record's reviewed scope - the filtered digest, not the raw diff byte hash - unless the record's contract explicitly pins the raw form. An empty-input hash result is the tell that the verify ran against the wrong HEAD: it means the delta against that HEAD was empty, not that the record matches.

**Why:** witnessed 2026-10-30 (playbook repo, an execute-plan Phase 3 code-review closeout): verify-digest first ran from the primary checkout against an empty delta and reported a hash of empty input; and the record's source digest was initially drafted as the raw diff sha before the selection tool's own filter-scoped digest was used, which is what the staging validator actually compares.

**See also:** #227 (verify from the receipt/commit, not the staging step), #54 (helper argument contracts differ between landing modes; the same read-the-actual-contract discipline applied to digest scope).


## 306. A Dispatch-Blocked Review Panel Lands as an Inline Focused Record That Describes What Actually Ran

**Principle:** Family H (verify the real thing, not the abstraction: a review record is an execution claim, and a record claiming workers that never ran is a false claim even when the underlying review was real). **Shape trigger:** a review round whose worker dispatch channel fails outright (provider refuses every launch), forcing the round to run in the parent session.

**Rule:** when subagent dispatch is blocked and the round runs inline, record the round honestly in the review-record grammar: `panel_mode` "focused" with a `selection_reason` naming the dispatch block, `workers_launched` equal to the lenses actually executed, and `material_lens_set` scoped to exactly those lenses, so the "yes" verdict rests on clean coverage of the executed set rather than an unexecuted full roster. Never accept a producer template's full-panel default over what happened; reshape the sidecar and iterate on validator refusals (coverage vocabulary, lens coverage, exact coverage line) until the record validates while staying true. Pair the inline pass with mutation evidence: neuter each guarded mechanism, watch a named test fail, restore, and cite the pair in the record.

**Why:** witnessed 2026-10-29/30 (playbook repo, an execute-plan Phase 3 round): all dispatch attempts were provider-refused, the two-lens review ran inline in the parent session, and the producer's default sidecar claimed a five-worker full panel that never ran; the sidecar was reshaped to focused/2-lens with the block named in `selection_reason` and the material lens set scoped, hard validation then passed with zero degraded warnings, and the canonical identity-qualified round name was adopted via the selection oracle (which returned "reuse" on digest match, binding the record to the round).

**See also:** #286 (a subagent inactivity timeout is not a termination proof; the same verify-what-actually-happened discipline applied to worker liveness), lesson #65's chain-rule witness (a record's self-heal status is the truthful state, "unused" when the arm went unused; the honesty grammar is the same family).

## 307. A Stash Pop on a Shared Multi-Session Checkout Must Name Its Entry
**Principle:** Family A (verify the operand before consuming shared state: `git stash pop` without an argument takes `stash@{0}`, which in a checkout other sessions share may be a deliberately preserved foreign stash, not this session's entry). **Shape trigger:** any `git stash` cycle in a checkout where peer sessions park staged dirt as labeled stashes.

**Rule:** never pop a stash by position alone. Create stashes with a message naming the run, and pop by that resolved ref (`git stash pop stash@{n}` after confirming `git stash list` shows the labeled entry at that position); before popping, `git stash show --stat` the entry and refuse to apply a message this session did not write. A pop that conflicts kept the source entry in this session's witness, which is the only reason the preserved foreign dirt survived the accident; a clean apply would have silently consumed it.

**Why:** witnessed 2026-10-30 (playbook repo): a run-branch rebase used `git stash -q` on a clean tree (a no-op that creates nothing) followed by `git stash pop -q`, which applied `stash@{0}` - a peer session's labeled preservation of a pre-landing freeze blob - into the run worktree as an unresolved conflict, and only the conflict kept the entry in the stash list. The worktree was reset hard and the peer entry left untouched; the branch itself was unaffected because the run's real changes were already committed.

**See also:** #305 (digest verification binds to the invoking checkout; the same shared-checkout discipline at the digest layer).

## 308. Mirror the Run's Staged Review Records to the Primary Home Before Worktree Removal
**Principle:** Family G (durability before destruction: anything the closeout gates or later audits consume must exist in the primary home before the only other copy is deleted). **Shape trigger:** a worktree-complete teardown whose run produced gitignored staging artifacts (review records, sidecars, certification seal entries) under the run worktree's private home.

**Rule:** before `git worktree remove`, enumerate the run's new staging records (the Phase 3 record pair, exec/egress receipts, seal entries) and mirror each into the primary reviews home - by boundary-mirror `--mirror-path` or an explicit copy - verifying the primary copies read back. If the worktree is already gone, the records are recoverable only by re-deriving their exact inputs (findings JSON, run ids, and the reviewed bytes, which survive as git blobs even after the branch is deleted): re-produce, rename to the selector-emitted canonical names, and record the recovery in the manifest row. Recovery is possible only while the reviewed bytes still resolve as objects; after garbage collection it is not.

**Why:** witnessed 2026-10-30 (playbook repo): the Phase 3 clean round record and the plans-egress record were produced in the run worktree's gitignored reviews home; the worktree removal deleted both, and the primary home held neither. Recovery re-derived the reviewed plan bytes from the pre-squash branch commit (still present as a dangling object), re-produced both records byte-identically with the original run id, and re-pinned the certification seal's round-3 block onto the primary cert file.

**See also:** #8 (seal baselining and the hand-mirrored seal before teardown; this lesson extends the same duty to plan-family record pairs), #2581 area (post-squash review-series identity resolution).

## 309. A Vendored-Twin Byte-Pin Test Judges the Primary Checkout's Uncommitted State
**Principle:** Family H (verify the real thing, not the abstraction: a pin that reads a runtime-deployed twin compares against the deployed bytes, which track the primary working tree, not the committed tree). **Shape trigger:** a vendored-twin equality pin failing in a run worktree while the run's diff touches no twin file.

**Rule:** when a twin-equality pin fails and the run's changed-file set excludes the pinned file, diagnose the twin's sync source before rebasing: resolve whether the deployed twin tracks the primary checkout's committed blob or its uncommitted working tree. A peer session's in-flight uncommitted edit to the pinned file is mirrored into the twin on sync, and the pin fails in every worktree until that edit lands; the remedy is wait-for-landing (or landing first), never editing the twin, the validator, or the run's own copy.

**Why:** witnessed twice 2026-10-30 (playbook repo): a run worktree's vendored-twin pin failed twice; the first failure was real base staleness (the twin matched main, the worktree predated main's update) and a rebase fixed it; the second survived the rebase because a peer session held an uncommitted edit to the pinned skill file in the primary checkout and the twin had synced to those in-flight bytes. Byte-hash comparison of twin vs main blob vs primary working file separated the two cases in one step.

**See also:** #304 (validator blast radius; the same prove-it-before-you-blame-it discipline).


## 310. Repair a Legacy Review Record Only From Its Own Recorded Prose

**Principle:** Family H (verify the real thing, not the abstraction: a closeout gate reads the owned record set as it stands on disk, and a repaired record may attest only what its own bytes already say). **Shape trigger:** a landing or closeout sweep that validates every record a run owns (not only the round being landed), over a record family that spans an older grammar.

**Rule:** budget closeout time for the whole owned set: the review-staging gate reads every owned record, so a legacy-shaped sibling refuses the landing like the current round's record. Repair each legacy record by deriving every missing field from that record's own recorded prose (a finding's consequence, reachability, blast radius, and confidence from what its text already argues; its pattern owner from the lens it was written under; its triage outcome from its recorded disposition), never by composing plausible values. Where a field has no source (a usage mint pair), mint it and disclose the post-hoc mint in the record. Expect the retroactive couplings:

- finding ids are bare integers; a round-suffixed id parses as glued digits (`F1r4` reads as 14);
- per-worker budget excess moves to the record's overflow, with counts and triage outcomes restated;
- chain state is retroactive: once the chain start becomes valid, later rounds' self-heal state flips from `unknown` to `unused` (unknown is legal only while prior evidence is unavailable).

**Why:** witnessed 2026-10-29/30 (playbook repo, an execute-plan closeout): the done sweep's review-staging gate refused the landing on the run's owned prior records: the four code-review rounds at 116/116/92/32 errors, plus grammar gaps in the design review and the plan-review record. All were repaired to a hard-validator pass: fields derived from each record's own prose, overflow normalization, post-hoc mint pairs disclosed in usage notes, and later rounds' self-heal states flipped to `unused` once the chain start's repair made prior evidence valid.

**See also:** #30 (build a record from the validator's checks; the multi-record legacy-grammar variant), #291 (a field is derived or left empty, never composed; here extended to every per-finding field), #65 (run id immutable after r1; chain state is retroactive), #175 (census every appended entry; here census the whole owned set), #308 (mirror the owned set to the primary home before worktree removal; the durability half).
## 311. An Edit Anchor from a Rendered Read Is Not Disk Truth; Re-Derive from Raw Bytes on First Mismatch

**Principle:** Family A (state re-derivation: a rendering or transfer layer between the agent and the file can disagree with on-disk bytes, so an edit anchor built from a rendered read is a hypothesis, not evidence).

**Rule:** when a precise text-replacement anchor (or a copied pin literal) taken from a rendered file read fails to match the target file, stop re-trying near-identical anchors and re-derive every anchor from raw disk bytes (`cat -et` or equivalent byte-exact output) in the same pass; then re-run the precision-critical capture from raw output, never from the rendered view. Do not assume the file drifted or the tool is broken until the byte-level view is compared.

**Why:** witnessed 2026-10-29 (playbook repo, baseline-repair execution Task 1): the first Edit of a pinned stderr literal failed because the Read render of the pin region disagreed with the source's real line layout; re-deriving the anchor with `cat -et` resolved it immediately, and the same discipline was then applied to every byte-exact capture in the task. A rendered view silently reflowing or re-rendering byte-sensitive regions is exactly where a near-miss anchor would otherwise land as a corrupted pin.

**See also:** lesson 6-style peer-safety rules; the resolve-at-use digest rule (re-derive at the moment of use, never from carried context).

## 312. A Witness Citing a Living Record Path Dies When the Record Moves; Sweep Citations in the Same Change That Deletes the Path

**Principle:** Family A (dangling cross-reference: any durable record that cites another record by living path breaks silently when the cited path is fold-deleted, archived, or renamed).

**Rule:** any change that fold-deletes or archives a record (backlog row, plan, review record) sweeps the guard inventories that cite living paths - the machinery registry's witness refs foremost - and re-points each citation to the record's durable home before the deleting change lands, using the repo's citation precedence (the `completed/` twin when one exists, otherwise the covering plan's `completed/` twin). A baseline-repair run that meets a stale witness re-points it to the verified durable home only after confirming the twin's absence/presence (`git ls-tree` plus content head, never exit code alone).

**Why:** witnessed 2026-10-30 (playbook repo, baseline-repair execution Task 3): the machinery registry's `protocol:primary-log-ref-precondition` witness still cited the living backlog origin after peer landings fold-deleted the row and archived the covering plan, turning the check red as baseline drift; re-pointing required verifying the origin's `backlog/completed/` twin did NOT exist (a flawed `git ls-tree` probe exits 0 regardless of match) before selecting the covering plan's `plans/completed/` twin. The re-point was one of 25 standing-drift rows, none an actual defect.

**See also:** lesson 311 (re-derive byte evidence from disk, not from tool exit codes); the backlog covered-row citation precedence in AGENTS.md's Commit & Pull Request Guidelines.

## 313. A Receipt Runner Must Capture the Test Process's Exit Status, Not a Pipeline Tail's

**Principle:** Family A (state re-derivation: an rc recorded through a pipeline reflects the last pipeline stage, not the command whose result the receipt certifies).

**Rule:** a suite-inventory or receipt runner captures each command's exit status directly (`cmd > out.log 2>&1; rc=$?`), never through `| tail`/`| tee` whose exit status masks the child's; and before writing a green row it asserts the embedded output actually carries a passing summary (`OK` / `N passed`), refusing to emit `rc=0` over a contradictory body. The passing-summary assertion greps the FULL captured output, never just its tail (unittest's stderr `OK` block can flush before buffered stdout, so a tail-only grep under-audits and certifies an rc=0 row whose passing summary sits earlier in the capture), and the receipt records a per-row summary-witness (the matched passing-summary line) beside the rc so each row's green state is re-derivable from the receipt alone. A receipt whose rc column contradicts any embedded output tail invalidates every rc row in that receipt.

**Why:** witnessed 2026-10-30 (playbook repo, baseline-repair Phase 2): the full-inventory receipt recorded `rc=0` for a suite whose own embedded output two lines below read `FAILED (failures=1)` - the runner captured the pipeline tail's exit status - so a pre-existing red family (a stale done-skill anchor pin) was certified green and the review panel caught it, not the gate that exists to catch it.

**See also:** lesson 311 (re-derive evidence from raw bytes, not rendered views); docs/history/plans/completed/2026-10-30-machinery-witness-ref-validation.md (the machinery witness-ref validation plan, that origin row's durable home).

## 314. Manual Drains of Record-Backed Scratch Need Terminal Proof and Shape-Matched Vetoes

**Principle:** Family A (deletion safety: scratch files in a record-backed directory stay evidence until their producing record proves them consumable; recency alone proves nothing, and a veto that does not match the corpus's citation grammar passes cited files).

**Rule:** when manually draining a scratch directory whose files belong to run records, delete a file only after every applicable arm passes: (1) terminal-state proof from the producing record family, not mtime (a run-id group is consumable when any record in the group carries its terminal marker); (2) a recency gate (nothing newer than the chosen window is deletable, whatever its record says); (3) a reference veto over the durable corpora run with a tree search tool over a fixed-string candidate list, plus a prefix-form pass, because records cite files by glob-shaped prefixes (`name-<timestamp>-*`) that a literal full-path veto never matches; (4) a destination-resolution pass over the open closeout-record family: for every candidate path, also check whether an open run's closeout migration manifest (the recorded `closeout-migration.json` family beside the run records, and the run-ID `worktree-migrate-baseline-<id>-manifest.json` migrate-shape twins under the done-session record home) names that path as a verified destination of a run whose gate-removal has not completed, and retain the path until the owning run's gate passes (or mark the dead rows unverified in the manifest, with the drain's own sealed manifest as the marking witness), because terminal run ids prove the producing run's own files consumable, never the destinations a still-open closeout record claims. Extract embedded record ids with a mid-name match (`-<id-hex>` anywhere after the family prefix), never a stem-anchored one: per-worktree file variants (`name-...-<id>.wt-<slug>.txt`) silently fall into the id-less bucket otherwise. Seal the deletion list first (path, sha256, size, reason) into the record home the directory already owns, and keep one witness file per prefix any open record cites.

**Why:** witnessed 2026-10-30 (playbook repo, the operator-directed docs/tmp drain): the first veto pass (literal candidate paths over durable corpora) reported zero citations while open backlog rows cited three manifest witnesses by glob prefix, and only a follow-up prefix pass caught them before deletion; a stem-anchored id regex misclassified several hundred wt-variant files as id-less; and an in-process read of the whole reviews corpus hung past a tool timeout where the same corpus through the tree search completed in seconds. The destination gap is witnessed the same day from the consumer side (lesson 315): a drain whose terminal-run proof showed the producing run's ids consumable deleted gate-report destinations a parked run's migration manifest still carried as verified rows, stranding the closeout until a hand-run marking recovery.

**See also:** lesson 315 (the consumer-side recovery this destination-resolution arm prevents); lesson 312 (a witness citing a living record path dies when the record moves); lesson 311 (re-derive from raw bytes).

## 315. A Stale Closeout Manifest Blocks Teardown Until Its Dead Rows Are Marked, Not Deleted

**Principle:** Family A (deletion safety, consumer side: a recovery agent inheriting a record whose recorded destinations another sweep removed must repair the record in place with a dated witness, never delete rows or force the gate).

**Rule:** when a closeout gate refuses teardown because verified migration-manifest rows name destinations that no longer exist under the target, recover in this order: (1) prove the missing destinations belong to no live consumer: no live execution claim, no registered worktree, and zero citations of the producing run's ids in durable corpora and memory surfaces; (2) mark each dead row unverified with a dated note naming the removing sweep and the proof, in EVERY section the gate consults (both the migrated and the renamed/replaced sections; the per-worktree variant destinations live in the renamed section, so a fix that touches only the migrated section fails a second gate run); (3) re-run the gate unchanged. Never delete manifest rows (the manifest is an append-log), never edit the gate, never force worktree or branch removal before the gate passes; once the gate passes, delete the branch only at the exact OID the gate's disposition names.

**Why:** witnessed 2026-10-30 (playbook repo, the parked closeout of a landed run): a peer drain session removed gate-report destinations whose run ids the drain's own proof showed terminal, but the parked run's migration manifest still carried them as verified rows, so gate-removal refused and retained the worktree and branch. Marking the dead rows unverified (4 migrated plus 11 renamed rows) with a dated witness note let the unchanged gate pass with an exact-tree-accounted disposition, after which worktree and branch teardown landed cleanly.

**See also:** lesson 314 (the drain-side proof discipline whose gap produced the stale rows); lesson 312 (witness paths dying when records move). Second witness 2026-10-31 (playbook repo, completion-pass closeout, same day as the lesson): the same refusal shape was first resolved by operator-directed raw removal WITHOUT this remedy - the mark-then-rerun path was available and cheaper, and the operator escalation skipped it; the mark was applied retroactively and verified by re-running the unchanged gate, which progressed past the missing-destination leg (its only remaining failure is the post-removal exact-branch identity mismatch, the expected pre-removal-gate state once the worktree is gone). The ordering stands: exhaust the mark remedy BEFORE operator escalation; an operator direction substitutes for the gate pass only when the mark path is exhausted, and the retroactive mark keeps the shared manifest truthful for the next consumer.

## 316. Bash case patterns match slash-bearing tails

**Source:** release privacy diagnostics execution 2026-10-30 (worktree 2026-10-26-release-privacy-diag, commit 4974e1318).

In bash, a `case` glob like `"$root"/release-draft.*` matches paths with slashes in the `*` tail - case patterns treat `/` as an ordinary character, unlike pathname globbing. A guard `case $p in "$root"/name.*) [ -f "$p" ] && delete;; esac` therefore admits files NESTED inside a `name.*` directory. When a guard means "directly under", add an explicit dirname equality check beside the glob; and write the selftest for the nested case, not only outside-root and nonmatching names.

## 317. Egress the Closeout Migration Manifest Before Worktree Removal; Reconstruct With Re-verified Digests if Lost

**Principle:** Family D (state-first: a gate's required input must exist outside a surface the teardown itself deletes). **Shape trigger:** a closeout whose transfer-out writes `closeout-migration.json` inside the run worktree, followed by a landing that removes the worktree while gate-removal is still pending.

**Rule:** write or copy the closeout migration manifest to a surface that survives worktree removal (the primary session home or the run records home) BEFORE the worktree is deleted; gate-removal runs after teardown in the branch-only mode and needs `--migration-manifest`. When the manifest is lost with the worktree anyway, reconstruct it in the adjudicator's migrate shape (branch record plus per-artifact `migrated` entries with `destination`, `verified: true`, `sha256`), re-verify every digest against the PRIMARY checkout's surviving copies rather than trusting session notes, and disclose the reconstruction in a provenance note inside the manifest; the branch-only adjudicator reads the shape, not the writer, so a verified reconstruction passes unchanged.

**Why:** witnessed 2026-10-30 (playbook repo, an execution run's teardown): the transfer-out manifest lived only in the worktree and vanished with it; the branch-only gate-removal refused without `--migration-manifest`. A 17-entry manifest was reconstructed from the session records with each digest re-computed against the primary copies, carrying a `reconstructed` note, and the gate returned `exact-tree-accounted` on the next run.

**See also:** #289 (the migrate shape the branch-only adjudicator reads); #315 (marking dead rows, never deleting them).

## 318. A Repo-Wide Pins Failure From Stale Prompt-Log Entries Is Peer Residue; Repair as a Bounded Rider, Not a Block

**Principle:** Family B (scope discipline: a shared checkout's cross-session residue is not this run's defect, but a landing that consumes it must repair it within bounded authority). **Shape trigger:** `check_maintenance_pins` reports "prompt log has no all-served (stale) entry" at the primary checkout while the run's own changes never touched the prompt log.

**Rule:** verify each named entry is actually fully served (its landing exists on main) before touching it; prune only the provably served entries with the prompt log's own receipt form (`PLAN-PROMPTS-PRUNE: <slug> -> <landing receipt>`), landing the prune as a rider commit in the same run, and print the pins result in the run output. Never widen the prune to unserved or in-flight entries, never edit the pins gate, and never block the run's landing on a failure the run did not author.

**Why:** witnessed 2026-10-30 (playbook repo): a landing-window pins reproduction failed over three fully-served prompt-log entries left unpruned by peer sessions; all three were verified served against main, pruned with receipts in a rider commit, and the pins gate passed.

**See also:** #53's bounded-repair responses; the machinery admission protocol's bounded-repair clause.

## 319. Re-Derive a Sweep/Retention Refusal Before Blaming the Predicate; the Baseline May Be in the Wrong Checkout

**Trigger:** a worktree-migration leg refuses `closeout-baseline.json: baseline file not found` right after the landing sweep's docs-tmp-sweep reported the session dir removed as `(plan archived)`.

**Rule:** before filing a mechanism gap, re-derive both sides from disk: the sweep's retained proof-family list (`PLAN_SLUG_PROOF_FILES` in scripts/done_sweep_gates_lib.py: closeout-baseline.json, closeout-baseline-skip.json, closeout-migration.json) and the actual contents of the session dir the sweep removed. When the worktree session dir genuinely holds no baseline, the refusal is a placement defect, not a sweep defect: a Phase 0 capture executed after a shell cwd reset silently lands the baseline in the primary checkout while the run lives in an ad-hoc worktree. Remedy shape: the capture output names its placement, the migration refusal's remedy clause points at the primary checkout's same-slug session dir, and a late recapture is recorded as a deviation, never silent.

**Why:** witnessed 2026-10-30 (playbook repo, exec pick 1 closeout, landing 0a3c1ee34): the first write of this lesson blamed the retained-family list; archaeology for the follow-up backlog row showed the list already retained the baseline pair and the sweep kept its contract, so this lesson replaced its own wrong mechanism the same session.

**See also:** #43 (worktree cwd resets between shell calls), #317 (egress the migration manifest before worktree removal).

## 320. A Baseline-Red Gate's Red Set Is Window-Volatile; Adjudicate Base-Versus-Head in the Same Run

**Principle:** Family A (state re-derivation: a remembered inventory of known failures is a stale snapshot, not a baseline).

**Rule:** when a repo-wide gate (a pins sweep, an inventory check) fails and the failure looks like the recorded baseline red, classify it by re-deriving both sides in the same run - run the identical gate at the base commit and at the head and compare the failure sets - never from a remembered baseline list, however recent. Under concurrent landings the red set can change completely within one working session: an entry red cleared by a peer's prune and a new red introduced by a peer's landing are both normal, so "the baseline was red an hour ago" classifies nothing. A delta contributed by the reviewed branch is the only landing-blocking kind; a base-identical red is recorded with the base evidence beside it, not repaired in the reviewed change.

**Why:** witnessed 2026-10-30 (playbook repo, one interactive session, two ad-hoc landings an hour apart): pick 1 saw a three-entry stale-prompt-log pins red (base-identical, recorded); by pick 2 a peer prune had cleared it and a different peer landing had introduced a new review-plan pin red - the same run's pre-rebase "pins passed" note went stale mid-run, and only a fresh base comparison at each landing boundary classified the reds correctly.

**See also:** #318 (the stale-prompt-log red's repair route as a bounded rider); #319 (re-derive a refusal before blaming the predicate; wrong-checkout baselines).

## 321. Derive Validator-Gated Artifacts From the Owner's Scaffold, Never a Recent Record

**Principle:** Family A (state re-derivation: a gate's required shape is code-owned state that moves; a landed example is a snapshot of yesterday's shape).

**Rule:** when an artifact must pass a validating gate whose canonical shape lives in code (a staging record pair, a receipt, a manifest), derive the artifact from the owner skill's construction recipe or the validator's generated scaffold - never by imitating a recently landed record. Even a same-day record can predate the current gate set, because the validator's gate trio grows faster than records land; imitation then fails validation in several iterate-and-repair rounds, each one a re-derivation the scaffold would have made unnecessary. The owning skill's recipe is the source of record; reading it before the first write is the cheap pass.

**Why:** witnessed 2026-10-30 (playbook repo, one session, two ad-hoc landing records): both staging pairs were authored by imitating same-day records and each needed six-plus validator-refusal rounds to reach pass - missing severity groups, missing Comment/Analysis blocks, missing Review Statistics section, minted run-id pair, soften table, per-finding calibration fields - every one of them shapes the owner skill's scaffold-first recipe already prescribed, which the session read only after the refusals.

**See also:** the review-staging skill's Finding-construction recipe (scaffold before drafting), which owns this rule's mechanical home; #311 (re-derive from raw bytes on first mismatch). Fourth witness 2026-11-02 (playbook repo, an authoring run's r1 plan-review pair composed from the review-plan skill's prose stable-core summary instead of the scaffold): two validator rounds surfaced a distinct shape ladder the prior witnesses had not hit - the verdict sidecar field takes `yes`/`no` (not `ready=yes`), `panel_mode` is the closed enum `full|focused` (not a descriptive label), the coverage `outcome` enum is `clean|replacement-covered|degraded|failed`, `retry_budget` must be an object with positive `per_attempt_timeout_minutes`/`per_worker_max` and every attempt's elapsed must fit it (re-pinned 15 to 20 from measured completions), the Markdown `- Coverage:` line must equal the sidecar outcome, a `### Attempt ledger` section is required beside recorded attempts, and the per-worker non-blocking Low budget (2) moves extras to the `overflow` array with a Markdown manifest twin. The summary that misled is the skill's own "stable-core" copy, which declares it is not the contract; the recipe instruction to run `--scaffold` first is the repair that sticks.

## 322. Prove a Serializer-Owned File Round-Trips Before Hand-Editing It

**Principle:** Family H (verify the real thing, not the abstraction: the "machine-maintained" label is the abstraction; the round-trip diff is the real thing).

**Trigger:** about to hand-edit a data file whose canonical form a serializer defines (a registry, lockfile, or generated config with one canonical dump function).

**Rule:** first run the serializer over the current bytes and diff. A mismatch is pre-existing drift, not a property of your edit. Never re-serialize inside a semantic edit: the drift rewrites unrelated siblings' bytes and smears the diff. Never let textual insertion become the standing practice either: every future editor inherits the constraint. Land a normalize-only change first - serializer output over current content, nothing else - then edit on the round-tripping base. Shape validators do not see key order, so a green check proves nothing about the round-trip.

**Why:** witnessed 2026-10-30 (playbook repo, agent-type-affinity plan Task 2): registering a blocker in the machinery registry surfaced that the file no longer round-trips under its writer's sorted-keys dump - three removals rows carry unsorted keys. The entry went in as a textual tail insertion; the drift went to a backlog row (docs/history/backlog/2026-10-30-machinery-registry-canonical-serializer-non-round-trip.md).

**See also:** #320 (the same-run re-derivation discipline for machinery-gate state; there the red set, here the byte shape).

## 323. execution_claim take Creates Its Own Worktree; Never Pre-Create It

**Rule:** for an execute-plan run's claim (`scripts/execution_claim.sh take ... --worktree-parent ...`), let the gateway create the worktree and branch atomically. Pre-creating the worktree or branch with `git worktree add` first makes `take` refuse ("branch is held by an existing worktree"), and the remedy is a destructive bounded cleanup (`git worktree remove --force` + `git branch -D`) before re-taking.

**Why:** witnessed 2026-10-31 (machinery-witness-ref-validation execution): the run pre-created the worktree per the branch-naming convention, take refused, and the invocation's freshly written claim had to be cleaned up by the gateway itself before the retry.

**See also:** #321 (deriving validator-gated artifacts from the owner's scaffold rather than hand-provisioning).

## 324. A Second-Truncation Timing Test Needs a Crossed-Second Boundary to Discriminate

A timing-order test whose two sides are truncated to whole seconds (`timespec="seconds"`, floored) and whose marked operation is sub-second cannot discriminate: a capture recorded AFTER the walk truncates to the same second as one recorded before, so `assertLessEqual(captured, mark)` passes for both the correct and the regressed order (witnessed 2026-10-31, closeout-migrate-zero-delta-silence run: the mutation check moved `captured_at` after the walk and the test passed 10/10). Fix: make the marked walk deterministically cross a second boundary (`time.sleep(1.1)` after the mark) or drive the module clock through a seam. General rule: when an assertion compares truncated readings, prove the regression class truncates to a strictly different bucket before trusting the test; verify with a scratch-copy mutation, not reasoning alone.

## 325. Producer Findings JSON: Split Workers and Drop Out-of-Scope Residuals Before Staging

**Trigger:** building the findings JSON for `scripts/produce_exec_review_record.py` when the round's findings mix fixed, backlogged, and out-of-scope items across severities.

**Rule:** the per-worker non-blocking Low budget (max 2) keys on each finding's `workers` field, which defaults to one worker - attribute findings across the declared panel worker names explicitly, or Lows that belong to different lenses pile onto the default worker and the validator refuses the pair. Findings that are real but outside the reviewed plan's scope are not staged findings: give them `status: dropped` with `dropped_reason: out-of-scope` and a note pointing at the backlog row that records them, because a staged set yields sidecar verdict `no` and the certification round needs the empty set. Also note the two producer enums that refuse late: `triage` is one of pending/deferred/done/dropped/fixed (never prose), and the plan operand must byte-match the JSON's `plan` value.

**Why:** witnessed 2026-10-31 (execute-plan claim-procedure-pointer run): four refusal cycles (budget exceed on the default worker, unknown `overflow` key, triage prose, plan-path mismatch after archive) before the pair validated; splitting `workers` and dropping the out-of-scope set cleared it in one draft. Second witness 2026-11-02 (playbook repo, an exec run's Phase 3 pair): the same cycles repeated, plus `severity` must be capitalized (`Medium`, not `medium`) - a third producer enum refusing late; the per-worker Low cap has no producer-side overflow valve, so related Lows must be bundled into one finding (with an explicit `workers` list) before producing.

**See also:** the artifact-slug rule (L3346 block, "pass --artifact-slug") (the same producer's slug and verdict shapes).

## 326. Run the Done Finalize Before Worktree Removal; the Manifest Leg Binds the Worktree Root

**Principle:** Family B (ordering: a closeout leg whose input is bound to the run worktree runs before teardown, not after).

**Trigger:** sequencing a done-run closeout when worktree removal or branch deletion (gate-removal, closeout migration) is available before the finalize, and the finalize has not run yet.

**Rule:** run `done_run.sh finalize` from the run worktree BEFORE any worktree removal or branch deletion; the finalize's manifest leg re-verifies the session manifest's `repo_root` fingerprint against the checkout that must still be the run worktree. A post-removal finalize refuses with a fingerprint-shaped message ("manifest schema_version 1 repo_root fingerprint is not supported by this finalizer") even when the manifest bytes were copied out beforehand - the leg judges the root, not the bytes. Teardown ordering: finalize (this lesson) → record mirror and manifest egress (#308, #317) → worktree removal and gate-removal. When teardown already happened, report the failed leg honestly and release the locks; do not fabricate the leg or re-run it from a reconstructed directory.

**Why:** witnessed 2026-10-31 (playbook repo, an execute-plan run closeout): gate-removal passed and the worktree was removed first, then finalize ran from the primary checkout with the session manifest copied out; the manifest leg refused on the root-fingerprint check while the lock releases ran cleanly, degrading the closeout to a reported-failed leg with the session scratch preserved as evidence.

**See also:** #212 (finalize runs from the checkout holding the done-session scratch), #308 (mirror the owned record set before worktree removal), #317 (egress the migration manifest before worktree removal).

## 327. Hash the Ceremony Record's File Bytes, Never a git show of the Pre-Commit Head

**Principle:** Family D (digest binding: a ceremony record's sha256 is computed over the artifact's on-disk bytes at the verification point, not over a head-revision read that may not contain them yet).

**Trigger:** producing or re-pinning an archive-ceremony receipt (or any digest-bound record) while the record file is staged or written but the committing commit has not landed yet, and the digest command is assembled from a `git show` habit.

**Rule:** compute the record digest with `shasum -a 256 <path>` (or equivalent) over the file itself; a `git show HEAD:<path>` read at that moment exits quietly (or on an empty pipe) when the bytes are staged but not yet committed, and hashing the empty input silently produces the well-known null-string digest (e3b0c44…), which the ceremony then binds and the gate later refuses. If a head-revision read is used, assert it returned bytes before hashing; a null digest is always a bug, never evidence.

**Why:** witnessed 2026-10-31 (playbook repo, a done-run commit): the archive-ceremony gate required a `*-plan-review-<slug>-exec-r<N>.md` record carrying the archived plan's sha256; the first attempt read the plan via `git show HEAD:` while the archived bytes sat only in the index, hashed empty input, and bound the null digest before the gate refused.

**See also:** #10 (prove completion marks, not diff shape), #326 (closeout ordering binds the worktree root).

## 328. Closeout Mirror Operands Take the Manifest's Living Tuple, Never a Re-Derived Equivalent Path

**Principle:** Family B (ordering/identity: an operand that a verifier matches by tuple equality must come from the record that names it, not be re-derived from the tree's later state).

**Trigger:** running a worktree closeout mirror (e.g. `worktree_closeout_migrate.py boundary-mirror`) after the plan has already landed and archived, and supplying the plan's post-landing path (the `completed/` archive path) because that is where the file now lives.

**Rule:** take each path operand verbatim from the session manifest's recorded tuple - for the plan, its living `docs/history/plans/<file>` path - even when the file has since been archived or moved and the living path no longer resolves in the current checkout. A tuple-mismatch refusal naming the recorded vs supplied path is a wrong-operand refusal, not a gate defect: re-run with the manifest's value, never edit the mirror or the manifest. The same discipline covers the claim-release operand (`--operand-source <landing>^:<path>`) and the ack-egress path: each is anchored to a tuple some record already holds.

**Why:** witnessed 2026-10-31 (playbook repo, a plan-execution closeout): the boundary-mirror leg refused on a `plan_path` tuple mismatch after the run passed the plan's freshly archived path; re-running with the manifest's living path cleared it on the first retry.

**See also:** #43 (re-derive state at each boundary - derivation is for *state*, operands come from records), #323 (the same gateway's atomic-take contract).

## 329. Transfer Session Logs Into the Run Worktree Before Any Boundary Mirror

**Principle:** Family B (mechanics: `boundary-mirror` copies each `--mirror-path` source from the run worktree to the primary; a source that exists only at the primary is a missing file on the worktree side, so the leg exits 1 with per-path copy errors even though the data is safe).

**Trigger:** running a worktree-placed execute-plan run whose Phase 0 transfer-in did not bring the session directory (`{tmp_dir}/execute-plan/<PLAN_SLUG>/`) into the worktree, then invoking `boundary-mirror` with `manifest.md` or task logs among the mirror paths.

**Rule:** before the first boundary mirror, make every planned mirror source readable inside the run worktree: either complete Phase 0's transfer-in for the session directory, or copy the current primary session dir into the worktree before the leg (and re-sync after the primary-side manifest gains rows, so the next boundary's mirror source is current). A first-attempt failure listing every path as "copy error ... No such file or directory" against the worktree is this gap, not a mirror defect: repair by making the sources present, then re-run; receipts and the manifest row land on the retry.

**Why:** witnessed 2026-10-31 (playbook repo, a worktree-planned plan execution): every boundary mirror failed on the first attempt with all paths missing (session logs lived only at the primary because transfer-in was skipped), cleared on the first retry after the session dir was copied into the worktree; the pattern repeated at all three task boundaries.

**See also:** #328 (the same helper's operand-tuple rule), #326 (mirror the record set before worktree removal).

## 330. Quote `=`-Leading Tokens in zsh Compound Commands

**Principle:** Family B (mechanics: zsh performs equals expansion (`=cmd` expands to the command's path) on unquoted tokens beginning with `=`, and the resulting "word too long"-style `not found` error aborts the whole compound line, so a cosmetic echo label silently kills every command after it).

**Trigger:** composing a zsh compound command that includes a decorative separator such as `echo ===HEADING===` or `echo ===` mid-chain, before commands whose output is the actual decision input.

**Rule:** quote any token starting with `=` (`echo '=== heading ==='`) or drop decorative separators from compound commands entirely; never let a label abort the data-producing commands behind it. When a compound command exits nonzero, check whether anything after the offending token actually ran before trusting partial output.

**Why:** witnessed 2026-10-31 (playbook repo, a maintenance survey turn): `echo ===DIRECTIVES===` aborted the `;`-chain twice, once discarding the directives-heading grep behind it, and the failure was initially misread as a script error.

**See also:** #43 (re-derive state at each boundary), lesson on unquoted variables in zsh (no word splitting, in #132's corollary).

## 331. Register the Archived Plan in the Document Registry's FIRST Table Before the Landing Commit

**Principle:** Family B (mechanics: the doc-registry validator parses only the first markdown table in `docs/maintenance/document-registry.md`; a new row appended under a later section's table is present in the file bytes but invisible to the validator, so the archive gate classifies the archived plan path as an unregistered immutable write and refuses the landing).

**Trigger:** landing a plan archive (`done_run commit` with the `completed/` plan staged) when the plan path has no registry row yet, and the row is added by anchoring on a familiar late-file row instead of the first table.

**Rule:** before `done_run commit`, add the completed-plan registry row to the FIRST table of `docs/maintenance/document-registry.md` (insert after the last row of that table, not beside a matching-content row deeper in the file), then run `python3 scripts/doc_registry_validator.py validate` and confirm the new path resolves as registered before the landing attempt.

**Why:** witnessed 2026-10-31 (playbook repo, exec run automation-7bb77c96 landing `doctrine-text-precision-residuals`): the row was inserted beside the semantically nearest existing row (~line 904, a later table); `done_run commit` passed most gates and then refused at doc-registry with `HARD immutable path written without override` plus the note "registry row text naming ... is present in the registry file but outside the parsed first table", costing two extra landing attempts before the row was moved into the first table.

**See also:** lesson 323 (execution_claim take creates its own worktree - second witness same run: the first `take` invocation in this session also refused on a pre-created worktree), and the lock-export re-derivation lesson (meta.env recovery - re-witnessed twice in the same run's finalize).

## 332. Chain a Gate's Dependent Mutations with `&&`, Never Resume with `;`

**Principle:** Family B (mechanics: in a shell line `gate && echo ok; mutation`, the `;` separator runs `mutation` regardless of the gate's exit status - the `&&` binding ends at the `;` - so a failed validation gate does not stop the staging or commit placed after it).

**Trigger:** a compound command where a check-or-gate command is followed by mutating steps (a `git add`, a commit, a file write) in the same line with any `;` between the gate and the mutation, or a multi-command tool call whose later halves depend on an earlier half's success check.

**Rule:** every command whose correctness depends on a preceding gate must be reachable only through `&&` from that gate (or an explicit exit-status check between them); a `;` after a gate makes the gate decorative for everything after it, and a pipe does the same in a second way: `gate | tail` reports the filter's exit status and truncates the gate's verdict lines, so a refusal never reaches the chain and its prescription is cut off - check the gate's own status (`set -o pipefail`, or run the gate undecorated) whenever a later step depends on it, and never truncate a gate's output that carries its own failure report. When a gate fails mid-line, fix the cause and re-run the whole line; never let the tail of a `;`-chain land partial work behind a red gate.

**Why:** witnessed 2026-10-31 (playbook repo, an authoring closeout): a scripted multi-replace edit fixed two of three flagged lines; the em-dash gate re-run exited 1 on the third line, but the chain continued through a `;` into `git add` plus `git commit`, landing a partial fix as a commit; the miss was caught only by re-running the gate and cost a second fix commit. Re-witnessed the same day (the learn/investigate harvest closeout): a done_run commit refusal was masked by a `| tail` pipe so the finalize ran anyway, and two finalize runs' failure verdicts (a prescribed release-only retry with corrected env) were truncated away by `tail`, turning a self-diagnosing refusal into an hour-long silent-hold mystery.

**See also:** #330 (the sibling abort shape: a mid-chain expansion error kills the tail and is misread as a script error), #36 (the gate belongs in the pre-round sweep - this lesson is the command-shape rule that keeps a re-run's failure from being bypassed).

## 333. Deep-Copy Shared Structures When Authoring the Next Round's Sidecar From the Previous One

**Principle:** Family B (mechanics: a dict or list reused as the seed for a second artifact is aliased, not copied - in-place mutations made while filling the second artifact retroactively corrupt the first).

**Trigger:** authoring a multi-round record pair (an r2 `.stats.json` seeded from r1's, a template copied per finding) where the authoring script mutates shared containers in place.

**Rule:** when each round's sidecar is built by mutating a structure loaded from the previous round's sidecar, deep-copy the shared containers (per-round count dicts, staged-findings lists, coverage maps) before mutating; a shallow copy aliases nested dicts, so r1's counts silently absorb r2's numbers and the validator's parity check refuses the pair on a cross-round count mismatch that no single file explains.

**Why:** witnessed 2026-10-31 (playbook repo, an execution run's Phase 3 code-review pair): the r2 sidecar script copied the r1 sidecar at the top level and mutated nested `counts` in place; the validator refused with a staged-findings parity error only after r1's counts no longer matched r1's record, and the repair was a deep copy of the counts dict before the r2 mutations.

**See also:** #30 (derive the sidecar from the validator's checks, not by iteration - this lesson is the aliasing trap inside that authoring step), #65 (the honest state rule the counts must reflect).

## 334. Force Base-10 on Zero-Padded Version Components in Bash Arithmetic

`$(( ))` treats a leading-zero component as octal, so a zero-padded version component like `08` makes the arithmetic expression fail (or silently misbehave), and an unguarded `if (( ... ))` then falls through as false instead of comparing versions. Prefix every parsed version component with `10#` (`10#${BASH_REMATCH[1]} * 100 + 10#${BASH_REMATCH[2]}`) before arithmetic.

**Why:** witnessed 2026-10-31 (playbook repo, execute-plan r1 intermediate review over the docs-branch runner preflight): the new below-floor check computed `major*100+minor` from regex groups, and the reviewer proved a stub `Python 3.08` tripped the octal error, degrading to the old raw `tomllib` failure instead of the preflight diagnostic. Real CPython never zero-pads, so no test or run caught it - only the adversarial review did.

**See also:** #307 family (adversarial review catching unreachable-input defects); keep the guard when hand-parsing any dotted version in bash.

## 335. Author a Validator-Valid Review Pair From a Passing Twin, Never From Memory

The review-staging validator's date-conditioned required fields accumulate per date fence (freshness Metadata lines, `Coverage:`, mint pair, `extensions.convergence.self_heal_attempt`, sidecar `record_kind`/`review_mode`/`risk_signals`/`coverage`/`triage_outcomes`), and hand-recalling the set produces a predictable iterate-on-ERROR loop. Draft from the validator's `--scaffold`, then merge the extended sidecar fields from the newest passing pair of the same record family, and mint the run identity with `review_usage_capture.py mint` - the started-at key is `minted_at_ms`, not `review_started_at_ms`, and sidecar top-level keys outside the closed set are rejected (mint fields belong in `extensions`, and the two Metadata lines must carry the mint values verbatim).

**Why:** witnessed 2026-10-31 (playbook repo, execute-plan run): the archive-egress exec completion record took six validator round-trips to green because each fence surfaced one more missing field; the repair that stuck was copying a passing plan-review sidecar's extended fields and re-minting. Markdown/sidecar disagreement on `Last fix commit` (`none` vs a real sha) is its own named gate - keep the two surfaces byte-agreeing. Second witness 2026-10-31 (corrections-chain-recursion-refusal-and-pins r1, hand-authored without the scaffold): fifteen round-trips surfaced the same field ladder plus three silent-parse traps - metadata bullets parse only in bold form (`- **Pattern**:`; a plain `- Pattern:` reads as absent), sidecar finding ids are ints ordered by severity then id, and unattributed non-blocking Lows share one unnamed budget bucket that overflows into the sidecar `overflow` array with a Markdown Overflow manifest twin. Third witness 2026-11-02 (playbook repo, exec resume carrier run, two ad-hoc pick records): the sidecar `panel` array was omitted three separate times (the validator names it: `counts.workers_launched` does not match panel launches), the closed v1 pattern-owner set rejected `premortem#` and `concurrency#` prefixes (remap into the valid owner set), `#### F<N>.` heading prefixes are required (a `G` prefix reads as absent), and a Medium block under the `### Low` heading fails section placement.

**See also:** #333 (deep-copy shared structures when authoring the next round's sidecar - this lesson is the record-family authoring sibling), #35 (lock exports die at the tool-call boundary - re-witnessed by the same run's landing).

## 336. Price a Byte-Balance Criterion Against the Mandated Contract at Authoring Time

**Principle:** Family 1 (verification before commitment) - a plan whose done-when demands zero
net byte growth for a file while also mandating new contract content must be priced at authoring
time, not trusted to consolidation.

Shape trigger: a plan task pairs an additive contract change with a byte-neutrality criterion on
the same file.

Rule: before the plan leaves authoring, estimate the mandated addition's irreducible byte cost
(command literals, row enumerations, the contract's named members) against the demonstrably
removable redundant prose in the destination text. If the addition exceeds what consolidation
can free, scope the criterion in the plan itself (for example "no growth beyond the mandated
contract") or record the expected residual as a plan assumption. Discovering the infeasibility
at execution forces a choice between breaking the done-when and deleting carried-forward
operative behavior - and the executor should always take the second horn (record the honest
residual) rather than compress semantics to hit a number.

## 337. Derive Consumer-Side Test Fixtures From the Producer's Actual Write Path

**Principle:** Family 1 (verification before commitment) - a green suite proves only the
fixture shape it feeds, so hand-shaped fixtures must be derived from the producer, not from
the consumer's convenience.

Shape trigger: new consumer code that validates or binds records another component writes
(manifests, receipts, claim files, provisioned state).

Rule: before writing the consumer's tests, read the producer's actual write path (its writer
function, contract docstring, dispatch/cwd resolution) and mirror that exact shape - field
forms (digest vs raw path), storage location (which side of a worktree split), and the
provisioning side effects that precede the consumer's run (transfer-in copies, ignored-path
state). Witnessed twice in one task (2026-10-31, plan-authoring-stand-down-before-charter
Task 1): the manifest matcher passed 16 green tests against a legacy raw-path, primary-side
manifest shape no current producer writes (the real producer records a digest and resolves
its session dir from the dispatching worktree), and the zero-owned staging scan passed
against a provisioning shape that omitted the mandated transfer-in mirror copies. Both
defects were dead-on-arrival on the normal path despite a fully green suite; both were
caught only by adversarial review probes, not by the tests. When the producer is a script,
run it once in the fixture setup and assert against its real output instead of hand-writing
payloads.

Witness: 2026-10-31 (playbook repo, landing-diagnostic-own-plan-target exec run): the identity
binding plus outcome matrix added ~2100 irreducible bytes; narrative consolidation freed ~750;
the residual +1356 was recorded in the exec review and the implementation commit message.

**See also:** the skill-text anti-growth rules in the repository AGENTS.md (pay-for-growth
discipline; its review-time pricing is this lesson's authoring-time analogue).

## 337. Verify the Provenance of a Pre-Existing Session-Dir Baseline Before Capture-Once or Default-Lookup Adoption

**Principle:** Family H (mechanics: run-artifact paths keyed only by plan slug are shared across run kinds - the authoring closeout and a later execution run of the same plan resolve the same `{tmp_dir}/execute-plan/<slug>/` directory, so a capture-once guard ("skip if present") and a gate's default manifest lookup happily adopt the foreign run's bytes).

**Trigger:** starting an execution run whose plan-slug session directory already exists in the primary checkout with `closeout-baseline.json` / `closeout-migration.json` from a completed authoring run.

**Rule:** before the Phase 0 baseline capture or any closeout gate resolves a pre-existing artifact at the canonical session-dir path, verify provenance from the file itself: the baseline's captured checkout against this run's worktree, the migration manifest's recorded branch/worktree against this run's identity, and mtimes against the run start. Foreign-run residue is relocated to non-colliding names beside the canonical path (records preserved, never deleted; the default lookups then resolve only this run's artifacts) before the fresh capture runs.

**Why:** witnessed 2026-10-31 (playbook repo): a 2026-10-30 plan's primary session-slug dir carried the completed authoring run's baseline (1.6 MB, captured from a since-removed worktree) and its migration manifest (naming the removed authoring branch); the capture-once guard would have adopted the foreign baseline and the closeout gate's default `--migration-manifest` lookup would have read the foreign manifest at teardown. Both relocated to `*.authoring-<date>.bak` names; the run captured its own fresh baseline. Discovery itself rode a truncated `ls | head` survey that had first reported the slug dir absent - lesson 130's shape, caught before harm.

**See also:** 130 (absence signals need untruncated or exact-match probes), 269 (the one-baseline capture-once discipline this check protects), 315 (a stale closeout manifest blocks teardown; mark, never delete), 319 (a baseline can sit in the wrong checkout). Second witness 2026-10-31 (playbook repo, completion-pass execution run over an already-executed plan): the new run's Phase 0 bootstrap did not adopt-and-relocate but **overwrote** the prior run's session-dir `manifest.md`, `briefing.md`, and `closeout-baseline.json` outright (the fresh manifest was written before the pre-existing files were noticed), destroying the prior run's scratch state; the durable evidence survived only because it lives outside the session dir (the exec-review record and the landing commit). The check is therefore bidirectional: before ANY write into an existing plan-slug session dir, relocate the foreign bytes first - provenance verification protects adoption, and a write-path pre-check protects against clobbering.


## 338. A Helper That Takes Its Own Merge Lock Must Never Run Inside an Outer Merge-Lock Hold

**Principle:** Family G (a lock acquired around a helper whose body acquires the same lock deadlocks; the outer holder is a shell that cannot release on the helper's timeout, and killing it strands the hold).

**Trigger:** wrapping `scripts/worktree_closeout_migrate.py migrate` (or any helper documented as holding the repository's `worktree-closeout-migrate` merge lock across its transaction) inside a caller's own `done-lock.sh merge-acquire` for "extra safety".

**Rule:** check the helper's own lock contract before adding an outer hold: when the helper acquires the same lock family internally, the caller holds no lock and lets the helper manage its own; when an outer hold is genuinely required, use the wait-acquire form with a bounded wait in the same process that will release. If a deadlock is killed, the stranded outer hold is released by re-exporting the killed acquire's printed `MERGE_LOCK_DIR`/`MERGE_LOCK_TOKEN` and running the token-fenced release before any other lock user (including the retried helper) runs.

**Why:** witnessed 2026-10-31 (playbook repo, completion-pass closeout): the migrate invocation was wrapped in a fresh `merge-acquire`, the helper blocked forever acquiring its own internal hold of the same lock, the 120-second shell timeout moved the command to background, and the kill stranded the outer hold; recovery was the manual token-fenced release, then the bare helper run completed in under a second. The bare run also made the outer hold's purpose moot - the helper's internal lock already covers its whole transaction.


## 339. Discharge the Resume Carrier You Armed Before Resuming the Run In-Session

**Principle:** Family H (verify the real thing) applied to scheduling primitives: an armed automation is a live mutation waiting to fire, not a record.

**Trigger:** any session that armed a one-shot resume/pause carrier and then recovers the blocked work itself (manual resume, early wall lift, operator nudge).

**Rule:** before resuming the blocked run in-session, delete or disarm the carrier you armed for that resumption; an armed resume payload delivered into a second session while the origin session is live creates a two-owner race over the same execution claim, run worktree, and landing. When the delete primitive is absent from the session's toolset, record the armed id in the run manifest as a parked duplicate-in-waiting and let the carrier-born session's own re-observation (live-session discovery ladder) route it to re-observe rather than re-execute.

**Why:** witnessed 2026-10-31 (hard-mode-clause-pointer-residuals exec run): the origin session armed a 110-minute resume carrier at the quota wall, the wall lifted early, the origin session resumed and drove the run through review rounds in-session, and the carrier fired mid-run; the carrier-born session staged the archive/landing while the origin session was writing review records, and the race resolved benignly only because both sides re-observed from disk (the origin session stopped at the staged-archive discovery and handed off; the carrier-born session's working-tree squash absorbed the origin session's uncommitted completion-pass amendments). See also lesson 127 (probe-first) whose discharge clause this lesson extends to the origin-session resume path.

## 340. Durably Record a Review Round's Findings Before Any Fix or Pause Leg

**Principle:** Family H (verify the real thing) applied to review handoff: findings that exist only in conversation or as a summary line are not evidence a successor can fix against.

**Trigger:** any session that receives a review round's findings and then pauses, dies at a usage wall, or hands off to a fix worker.

**Rule:** before launching the fix leg or ending the session, write the round's findings to their durable record (the review record or the run manifest's full finding bodies, not titles alone); a successor that inherits only finding titles must re-derive them with a fresh verification pass and treat the re-derivation as the review of record, refuting as well as confirming each inherited title.

**Why:** witnessed 2026-10-31 (resume over a quota-dead execution run): the dead session's round-1 review returned four findings but recorded only their titles in the run manifest before dying at the fix-worker launch; the resume session could not fix against titles alone and had to re-run the review fresh, which confirmed three findings (each reworded to the actual on-disk defect) and refuted one - the lost record cost a full re-review and nearly let a refuted finding drive a code change. Duplicates the family of writing the landing receipt before the lock (see #100's receipt rule) at the review-handoff boundary.

## 341. Verify the Diff Surface After Any Delegated Reviewer Returns

**Principle:** Family H (verify the real thing) applied to worker delegation: a worker's brief is not an enforcement mechanism.

**Trigger:** any session that dispatches a delegated reviewer (or any read-only-briefed worker) over a working tree with uncommitted work.

**Rule:** after a delegated reviewer returns, inventory the working tree (`git status --porcelain` + diff) and classify every changed path as own-authored or worker-authored before staging anything; a read-only-briefed worker that nonetheless authored files leaves edits that would otherwise ride the next commit unacknowledged. Adjudicate each such edit explicitly: keep it with a recorded disclosure (and re-run the affected gates), or revert it - never fold it silently.

**Why:** witnessed 2026-10-31 (same run as #340): the reviewer subagent, briefed read-only, also authored a regression test and a fixture edit beyond its report; the overstep surfaced only when the orchestrator's post-fix `git status` showed a third modified file, and the test was kept with a disclosure and a full suite re-run. The defect class is silent co-authorship: the edits were on-topic and green, which is exactly why an unverified fold would have been invisible.


## 342. Treat an Errored Subagent Hand-Back as Liveness-Unknown, Never as Termination

**Principle:** Family 1 (verification before commitment) applied to delegation: a harness-side
error message is not a worker-termination proof.

**Trigger:** any dispatch whose result arrives as a host error (usage limit, timeout, stream
failure) rather than a worker return.

**Rule:** an errored hand-back verifies nothing about the worker's process state: the error may
have killed only result delivery while the worker keeps executing host-side. Treat the worker
as liveness-unknown and re-observe it (disk writes, log mtimes, branch state) before any
duplicate dispatch, state mutation, or parallel resumption of its task; the Live-session
discovery ladder's re-observe-before-edit rule applies with full force here.

**Why:** witnessed 2026-10-31 (plan-authoring-stand-down-before-charter run): a fix worker's
hand-back arrived as a usage-limit error, the parent recorded a usage-wall pause and armed a
timed resume, then a later in-session dispatch ran the same fix round in parallel - while the
"dead" worker had kept working, applied all fixes, committed the task, and landed the entire
plan. The two-owner race produced rewritten history on the run branch and only luck kept the
landings identical; lesson #339 records the carrier side of the same incident, and #340 the
findings-record side, but neither captures the root: an errored hand-back is not a death
certificate.

## 343. Grep Sibling Suites for Byte-Pinned Output Before Changing a Command's Output Format

**Principle:** Family 1 (verification before commitment) applied to output contracts: a summary
line is an interface, and some of its consumers are byte-exact test pins living outside the
changed file's declared scope.

**Trigger:** any edit that changes a script's stdout/stderr wording, order, or trailing format.

**Rule:** before committing an output-format change, grep the whole `scripts/` test corpus for
the exact output literal (and its stable prefix), not only the plan's declared `Files:` and
validation commands; a pin in an unrelated sibling suite (for example `_FINALIZE_SCAN_TAIL` in
`scripts/test_invocation_telemetry.py` pinning `done_run.sh` finalize output) fails after the
landing even when every declared validation command is green. When a pin must move, re-baseline
it fixture-stably (mask environment-varying spans the way the suite's normalizer already does),
name the re-baseline in the commit message, and add the pinned-file to the run's scope record.

**Why:** witnessed 2026-11-01 (done-finalize-missing-record-scan run): appending
` corpus_root=...` to the scan summary passed all three declared validation commands and the
full 195-test wrapper suite, yet broke 5 exact-equality tests in the telemetry suite; only the
Step 1.2b intermediate review caught it, because the pinned file was outside the plan's scope
and validation set. See also #341 (verify the diff surface after delegated reviewers).


## 344. Retry a Blocked Teardown After a Wait Before Parking; Complete It While Persisting the Disposition

**Principle:** Family 1 (verification before commitment) applied to closeout stands-down: "refused" is not yet "unresolvable".

**Trigger:** a closeout, teardown, or accounting gate (gate-removal, residue sweep, foreign-dirt ladder) refuses and the tempting next move is to park the worktree/branch for the operator.

**Rule:** before parking a blocked teardown: (1) wait and re-run the refusing gate — rule out transient causes and confirm the blocker is not an active peer; (2) when the refusal provably cites inactive material (a completed foreign run's gitignored scratch, a destination drained by the sanctioned sweep lifecycle, a source worktree already gone), find a way to complete the teardown anyway and persist the change durably — for example, prune the stale rows from the gitignored migration manifest — never by editing or bypassing the gate; (3) the durable disposition of record is a backlog row (or the covering log entry, cluster-joined, when an investigation already covers the defect class), not only the scratch-record note.

**Why:** witnessed 2026-10-31 (exec carrier run session-status-facts-parse-shape-gap): the session parked a landed branch plus worktree on a gate-removal refusal citing a foreign gate report pruned from primary; the operator corrected that a wait-and-retry plus a persisted-completion route existed, and the teardown then passed (branch exact-tree-accounted, worktree and ref removed at the proven OID) with the second-witness row `docs/history/backlog/2026-10-31-gate-removal-shared-slug-second-witness.md` as the record. Complements #213 (re-derive a parked run's disposition from live state): #213 governs discharging a parked resume; this lesson moves the boundary earlier — verify liveness of the blocker before the park is created at all.

## 345. A Mutating Command Is Never a Throwaway Probe

**Principle:** Family A (verify the tool contract before reading an exit code; a suppressed-error mutating call is an unverified write).

**Trigger:** the urge to append a quick "let's see if this flag works" command to a compound shell line - especially with `2>/dev/null` or `; true` swallowing the outcome.

**Rule:** a probe must be read-only. Any command that creates or mutates state (`git worktree add`, `git branch`, a lock acquire, a file write) is never run as an error-suppressed afterthought in a compound command: run it deliberately, unsuppressed, and consume its outcome. When a mutating command does slip through, discover and remove its residue in the same turn (worktree list, branch list) before any other work - suppressed-error residue is invisible exactly because nobody read the output.

**Why:** witnessed 2026-11-01 (exec run, learn pass): a leftover `git worktree add -b <branch> /tmp/nonexistent 2>/dev/null; true` tacked onto a commit command silently created a registered worktree at a junk path plus a branch; both were discovered only by the post-run `git worktree list` audit and removed in the same session. The suppression that hid the failure also hid the write.

**See also:** #34 (land_squash expected values re-derived from disk), #35 (lock exports re-exported from full captured output - the same never-filter-machine-output discipline).

## 346. Draft Structured Records From the Validator's Scaffold Mode, Never From an Exemplar Copy

**Principle:** Family X (tool-bounded artifact authoring).

**Why:** witnessed 2026-11-01 (playbook repo, the 10:49 author carrier's plan-review staging pair for docs-tmp-retention-redesign): the r1 record pair was composed by copying a recent passing exemplar, and the hard validator refused it six times over closed vocabularies the exemplar happened to satisfy by construction - the `blast_radius` enum (global|multi-service|single-service|local), the kebab-case risk-signal tag set, the attempt-ledger's ISO-string timestamps and per-worker attempt numbers, and the soften-watchlist row-parity table shape. The owning skill's recipe states the rule verbatim ("draft every staging pair from the validator's generated scaffold instead of from memory: run the optional scaffold mode, fill every placeholder, keep the generated structural shapes") and the scaffold prints every one of those shapes; the six refusals were all re-derivable from the scaffold's first output.

**Rule:** when a skill ships a generator, scaffold, or selector for a record's structural shape, run it first and compose into its output; an exemplar copy teaches voice, not schema, and every closed vocabulary the validator enforces must come from the generator (or the validator itself) rather than from a specimen that predates the current descriptor.

**See also:** lesson 187 (the same run's chain-shape failures - both arms of one discipline: verify what you emitted, generate what you must emit).

## 347. An Actionability Probe Traces the Expectation Chain, Not a String-Presence Grep

**Principle:** Family X (selection-time verification depth).

**Why:** witnessed 2026-11-01 (playbook repo, the 10:49 author carrier's first authoring pick): the pre-provision actionability probe for the gate-removal-drained-destination entry grepped for the refusal arm's string, found it live at HEAD, and proceeded to provision claim, freeze, and worktree; the full-depth probe run later inside authoring read the classification logic the arm had grown (the trio landing's swept-artifact demotion), found the origin's Expected disjunction already satisfied and the row's first consumer disposed, and the run stood down post-provision - the provisioning churn (worktree, done setup, freeze commit, close-as-covered commits) existed only because the probe verified a literal instead of the expectation chain. The deeper probe is cheap: the item's Expected section names the surfaces; reading those surfaces and the commits that touched them settles every expectation in minutes.

**Rule:** before provisioning work for an item whose satisfaction is the open question, evaluate every expectation the item states against current source - the named surfaces, the commits that touched them since the item was written, and each disjunctive route - rather than confirming one symptom string still exists; a symptom can persist while the item is already served (and a symptom can vanish while the item is not).

**See also:** lesson 345 (a mutating command is never a throwaway probe - the same verification-first posture on the execution side).

## 348. Repo-Local Scripts Run Without `python3 -I`

**Principle:** Family X (invocation-form verification; stack-canonical rule).

**Why:** witnessed 2026-11-01 (playbook repo, the 10:20 auth carrier's scheduler turn): a runtime script was invoked under `python3 -I` and died at import with `ModuleNotFoundError` on its sibling module before any of its own code ran; re-running without `-I` worked unchanged in the same shell. `-I` strips the script's own directory from `sys.path`, which is the load mechanism for flat sibling-import layouts.

**Rule:** apply `-I` only when executing untrusted content; run the repository's own trusted scripts with plain `python3`. Full rule: `projects/.ai-playbook/python_guidelines.md` #40.

## 349. A Recurring Report-Only Finding Owes an Owning Row, Not Another Recording

**Principle:** Family X (feedback-loop posture: the recording surface owes the routing, not just the record).

**Why:** witnessed 2026-11-01 (playbook repo, the 11:00 auth carrier's scheduler turn): the consultative prune-audit has held standing REMOVED-WITHOUT-WITNESS flags since the receipt convention landed (2026-10-28), twenty-three flags in three subclasses (covered-row deletions with no receipt on any surface, a ledger rewrite that ate sixteen prior receipt lines in one commit, and one receipt written but not resolving at its removal commit), yet consecutive survey turns each recorded only the subsets they happened to run, report-only, and no backlog row owned the class, so nothing routed the flags to repair and every turn re-paid the derivation.

**Rule:** when a report-only arm's finding class survives into a second run's output, the same turn files or extends the owning backlog row (full witness set, subclass split, and the named triage question); a report-only posture defers the fix, never the record's ownership, and a survey that re-records an unowned finding is spending the turn to preserve noise.

**See also:** lesson 44 (the receipt grammar the flagged removals skipped), lesson 62 (re-derive the flag grammar at invocation), lesson 171 (the audit base derivation), lesson 347 (verify the expectation chain, the same depth-over-literal posture on the provisioning side).

## 350. Land a Descendant Branch onto a Dirt-Carrying Primary by Ref Plumbing, Then Reconcile the Peer's Working Copy

**Principle:** Family X (shared-state non-interference; landing mechanics).

**Why:** witnessed 2026-10-31/11-01 (playbook repo, the 22:58 exec carrier's ad-hoc run): main held a live peer's uncommitted residue (staged row deletions plus an unstaged prune of the shared exec-records queue file) that overlapped a path the run's own landing touched, so a working-tree merge would have refused or folded foreign hunks into the landing commit. The run instead fast-forwarded the main ref to its own descendant tip with update-ref (no working-tree write), then repaired only the landing's own paths back to HEAD (targeted `git reset -q --` and `git checkout HEAD --`), leaving every foreign staged and unstaged entry byte-identical. A follow-up check caught the second-order hazard: the peer's working copy of the shared queue file still carried the run's two consumed entry sections, so the peer's pending commit would have resurrected landed-and-pruned entries; the run surgically removed exactly those sections from the working copy, re-verified the peer's unstaged diff equaled its own prune, and left the rest untouched.

**Rule:** when the primary checkout carries foreign uncommitted changes, land an own-descendant branch by ref plumbing (update-ref fast-forward plus targeted index and worktree repair of only the landing's paths), never a working-tree merge; after the ref move, re-derive the foreign working copy of any shared file the landing also touched and reconcile it to HEAD plus the peer's own delta, so the peer's pending commit cannot resurrect consumed state. Never stage, revert, or commit a foreign hunk.

## 351. An Uncommitted Authored Edit in a Shared Primary Rides a Peer's Whole-File Commit

**Principle:** Family H (attribution is written to be read by history; git commits by path, not by hunk ownership).

**Why:** witnessed 2026-11-01 (playbook repo): two learn sessions authored the project lessons corpus concurrently; the faster session's explicit-path commit landed its own hunks together with the other session's uncommitted lesson and witness append, so the absorbed lesson (349) is durable and byte-correct on main but attributed to a commit subject naming only the absorbing session's work, and no `committed:` receipt names it. The stager-side own-edit check (lesson 134) protects against staging foreign hunks; nothing protected the authored-but-uncommitted side.

**Rule:** in a checkout shared with live peers, commit authored corpus hunks in the same bounded span as the gated write (marker, edit, scan, commit), or record their blob ids (`git hash-object`) so swept content stays attributable; after any parallel commit lands on a file this session edited, re-derive what actually landed (`git log -S` on an authored span) before reporting the receipt.

**See also:** lesson 290 (a pathspec commit lands the path's working-tree bytes), lesson 134 (the stager-side own-edit check), lesson 349 (the recording surface owes the routing, the same session's other capture).

## 352. Derive an Interrupted-Manifest Census From the Full Listing Under the Classifier's Own Predicate

**Principle:** Family H (verify the real thing: a residue count is a measurement, and every shortcut view substitutes a different predicate for the classifier's own).

**Trigger:** a drain or survey turn censuses undisposed interrupted manifests from the boundary classifier's listing (one line per manifest: `root_matches_current_repo`, `lock`, `dispositioned`, `adopted`, `created`) instead of classifying per record.

**Rule:** (1) Derive every count from the FULL listing through an AND-chain over all three state fields (`root_matches_current_repo=no`, `dispositioned=no`, `adopted=no`); a tail window undercounts, a one-field or two-field grep overcounts. (2) `adopted=yes` lines are adoption-terminal, not residue: they never enter the drain census. (3) Live-root lines route to proposal-only resume or adopt, never into the dead-root count. (4) A growth alarm compares only predicate-stable numbers: recount under the current AND-chain before declaring growth against an older census. (5) Quote field names and separators from the listing's current bytes; a remembered grammar matches nothing and reads as a clean zero.

**Why:** witnessed 2026-11-01 in a scheduler-turn drain: a tail window showed 3 undisposed manifests where the full listing held 5 dead-root residue lines; the post-drain raw grep returned 7, 2 of them `adopted=yes` adoption-terminal lines; a same-day recount briefly returned 0 on comma separators the listing has never used. The census recorded only the AND-chain recount (pre-drain 5, post-drain 1, the persistent witness-refused head).

**See also:** lesson 45 (a boundary's live root is its checkout match), the user-level corpus's lesson 540 (why adopted lines exit the census), the user-level corpus's lesson 541 (a truncated listing is not an absence verdict: the presence/absence twin).

## 353. A Lock Acquire's Success Is Read From Its Captured Output, Not From a Wrapped Conditional's Exit Status

**Principle:** Family H (verify the real thing: an operation's effect is proven by inspecting its captured output, and a wrapper's exit status can pass while the effect never happened).

**Why:** witnessed 2026-11-01 (playbook repo, an exec-run landing): the landing chain ran `if eval "$(done-lock.sh merge-acquire ...)"` while another process already held the lock; the blocked acquire emitted no exports on stdout, the substitution expanded to an empty string, and `eval ""` succeeded vacuously, so the chain proceeded into merge, land, and release steps with no hold at all, and the release then refused for want of exports. The acquire had not failed; it had simply produced nothing, and the shell read that nothing as success. Second witness 2026-11-01 (playbook repo, an authoring run's plan-freeze write): the acquire was chained `eval "$(…)" || exit` before the guarded edit, the live foreign holder made it print its refusal verdict (holder pid and label) while the wrapper's exit status still passed, and the chain failed open into the edit and its commit; the write proved single-path and conflict-free after the fact, and the miss was recorded in the run record, not repaired by editing any gate.

**Rule:** capture an acquire command's stdout into a variable first, verify the lock directory and token fields are non-empty in that captured string, and only then evaluate it into the environment; never write a conditional that wraps `eval "$(cmd)"`, because an empty substitution is a silent pass, not a proof the hold was taken. The same discipline applies to any wrapper whose contract is "print export lines": emptiness of the captured output is the refusal signal, checked explicitly before the dependent steps run.

## 354. A Whole-File Baseline Migrate Can Clobber the Destination's Newer Tracked Files

**Principle:** Family H (verify the real thing: a baseline-relative carry moves whole-file bytes, not deltas, so it can silently revert destination-side content that is newer than the baseline).

**Why:** witnessed 2026-11-01 (playbook repo, an exec-run closeout): invoking the closeout migrate with a foreign worktree checkout as its baseline copied that worktree's stale copies of shared tracked corpus files (the project lessons corpus and the document registry) over the primary checkout's newer bytes and staged them, silently reverting peer content that had landed on the primary mid-run. The clobber was repaired by unstaging and restoring the affected tracked paths from HEAD, then re-validating the registry still held this run's landed rows.

**Rule:** before running a baseline-relative migrate from a foreign checkout, diff the baseline's versions of the destination's shared tracked files against the destination's HEAD and refuse (or re-capture the baseline) when the baseline is older; after any migrate run, inspect its staged set and revert every tracked-file hunk the migration did not author, treating any staged entry outside the migration manifest's own outputs as a clobber to undo before continuing. A clean exit from the migrate proves the carry ran, never that the destination was not rewound.

## 355. Post-Round Folds Certify Through Fresh Confirm Rounds, Not Corrections Rows

**Principle:** Family A (precision-critical anchors: a certification binds both the bytes and the corrections chain that authorizes rewriting them; neither can be borrowed).

**Trigger:** an authoring review folds findings after a round closed, and the runtime's session-identity derivation returns empty, so the corrections route cannot name the rewriting session.

**Rule:** when the corrections route is unavailable by construction, do not stage a certification record with a non-null `last_fix_commit` over the post-fold bytes - the hard gate's corrections anchor leg refuses it as a bare rewrite. Route the fold through the post-fix certification mode's own shape instead: restate every pre-fold round as an intermediate (verdict `ready=no`, the record's pre-review source digest, `last_fix_commit` none) and certify the new bytes with a fresh fresh-adversarial confirmation round that runs the hard source-plan validation and seals its own round entry (round start equal to round close when the plan did not change inside the round).

**Why:** witnessed 2026-11-01 (playbook repo, an authoring run's plan review): two finding rounds were folded after closing; the corrections-record emission refused on the empty session identity and offers no explicit-identity input (the session-channel helper gained exactly that input for the marker recipes; the classifier did not), a certification record staged with a non-null `last_fix_commit` over the folded bytes was refused as a bare rewrite, and the intermediates-plus-fresh-confirmation restage cleared the readiness gate without touching any refused gate. See also lesson 281 (the in-round arm: a disclosed fix inside a live round re-anchors the seal instead), lesson 277 (a mid-review base move stales the staged digest the same way), lesson 32 (the machine-resolvable seal shape).

## 356. Never Rebuild a Stale-Base Branch With `reset --soft`

**Principle:** Family H (verify the real thing: a rebuilt commit must be verified as a tree, and a soft reset's success says nothing about which tree the new commit carries).

**Trigger:** a landing refuses on a stale base while the run's own work sits in uncommitted edits or unrebased local commits, and the fix is rebuilding the branch onto the moved tip.

**Rule:** do not rebuild via `git reset --soft <tip>` plus a re-commit: soft reset moves the ref but keeps the pre-reset index, so the rebuild commit silently carries the stale fork tree, and the squash landing applies it as a diff that rewinds every peer landing the tip gained. Rebuild the tree instead: `git reset --hard <current tip>`, cherry-pick the run's own commits, then verify the candidate against the tip on foreign paths (only the run's own paths may differ) and re-run the pre-landing verifications before retrying.

**Why:** witnessed 2026-11-01 (playbook repo, an authoring run's landing): a stale-base refusal was "recovered" by a soft reset plus re-commit, producing a clean-looking commit whose tree was the old fork point; the rewind was caught by inspecting the candidate tree pre-landing, and the hard-reset-plus-cherry-pick rebuild passed the same checks first try. See also #243 (the cherry-pick re-land is the standing recovery shape), #354 (same family: whole-file carries revert newer destination content).

## 357. Gate a Covered-Flip on Its stdout Lines, Not Its Exit Status

**Principle:** Family H (verify the real thing: a partial flip reports itself on stdout while exiting zero, and a format-sensitive grep can confirm a flip that did not happen).

**Trigger:** a landing closeout flips backlog origins to covered with the origins checker's mark-covered mode, over a backlog that mixes row formats.

**Rule:** after a covered-flip, gate on the printed per-origin `covered:`/`skip:` lines and the final marked count, never the exit status alone (the mode's documented contract is exit 0 on no-op-with-skips). Pre-flight each origin for a `Status:` header before flipping: the hardening-note row format ships without one and must gain `Status: open` first. Verification greps over origins must match both field forms: plain `Status: covered` and the bold `- **Status:** covered` form the transfer-in mirror writes.

**Why:** witnessed 2026-11-01 (playbook repo, an authoring run's landing): one of two origins was skipped for a missing header and the skip surfaced only on reading stdout; the first verification grep false-negatived on the bold form. See also #353 (the same exit-status family on lock acquires).

## 358. Never Carry Line Numbers Across Calls on a Peer-Mutated Surface

**Principle:** Family A (state facts are re-derived from the repository at the point of action, never carried from conversation; a line number is derived addressing that decays between calls on a surface parallel sessions rewrite).

**Trigger:** locating an entry in a shared rolling log (headings via grep -n) in one shell call and reading its body with a line-range read (sed -n 'A,Bp') in a later call.

**Rule:** when the target file is a live surface peer sessions mutate (the prompt log, rolling logs, ledgers), do the locate and the read in one pass: a single awk (or grep) pipeline that matches the content anchor and prints the body. A locate-then-range-read split across calls fails silently after a peer prune or insert: the numbers still resolve, but to a neighboring entry's plausible text, not an error. Address by content anchor, never by a number carried from an earlier call. When a body is cross-checked, gate on the entry's own fields (the slug heading, the Frozen line) matching before use; a mismatch is a stop-and-reread, never a reconcile-by-eye.

**Why:** witnessed 2026-11-01 (playbook repo, a scheduler turn's backlog survey): a peer pruned a landed entry from the prompt log between the heading scan (three slugs at fixed lines) and the range reads, so the sed spans returned mismatched entry bodies and one slug's body was initially misattributed to a neighboring entry; the Frozen-line cross-check caught it, and one fresh awk pass over headings plus Frozen lines plus the target entry resolved the true positions.

**See also:** #13 (re-derive the work item's state before the final write), #15 (re-derive a memorized procedure's owning file when peers land on the same repo), #194 (the same family: state facts re-derived at the point of action).

## 359. A Cited Landing Sha Is Verified by Ancestry, Not Existence

**Principle:** Family H (verify the real thing: a landing citation is proven by reachability from the base branch, and object existence is not reachability).

**Trigger:** consuming a plan line, record, or code comment that cites the landing commit of a past change, when the cited sha was taken from run telemetry or a sibling record instead of derived from the base branch's own history.

**Rule:** a squash landing keeps the pre-rewrite objects in the object store, so `git cat-file -e <sha>` succeeds on a dangling pre-rewrite twin and an existence probe certifies a citation that never landed. Before repeating or building on a cited landing sha, run `git merge-base --is-ancestor <sha> <base-branch>`; derive the true landing sha from the base branch's history or the origin row's covering commit, never from a worktree record. A twin that fails the ancestry check is replaced by the ancestor whose subject matches, and every citing span is corrected in the same change.

**Why:** witnessed 2026-11-01 (playbook repo, an authoring run's confirm round): a plan's defect narrative cited the landing sha of the partial-arm incident it documented; `git cat-file -e` passed while `git merge-base --is-ancestor` failed, proving the citation a pre-rewrite twin of the live landing the origin row names; the plan folded the correction in three places before freeze, and the same dangling sha survives in a code comment the run flagged out of scope. Second witness 2026-11-02 (playbook repo, an execution run): a plan's seed shas came from a divergent peer execution lineage (neither an ancestor of the base branch), so the run could not anchor against them at all; the remedy generalized the twin-substitution arm to byte-identity: verify the peer-lineage object's blob equals a main-ancestry twin per record (`git show <sha>:<path>` compared byte-wise), substitute the ancestry-passing twin, and record the substitution at the constant and in the archived plan's disposition, never silently.

**See also:** #132 (committed text names paths and dates, never branch-local shas: the authoring-side twin), #169 (the row-citation rot this extends to commit identities).

## 360. Re-Run Pre-Compaction Decisions on Fresh Reads Before Executing Their Writes

**Principle:** Family H (verify the real thing: the decision inputs as they stand at execution time, not as a pre-compaction summary carried them).

**Trigger:** resuming from a context compaction with a queue of prepared writes (a park, a carrier arm, a state edit) whose decision inputs were read before the compaction.

**Rule:** a summary's queued decisions are conversation context, not disk evidence; the standing precision rule that governs quoted values governs the session's own pre-compaction conclusions too. Before executing any queued write, re-run that decision's own gates over fresh reads: the state file's current decision and pending_dispatch fields (a sibling carrier may have completed or re-shaped the mandate), the probe the decision cited (a provider window can roll mid-turn), and any lock the write contends. A gate result that flips kills the queued write; record the flip instead of writing the stale plan.

**Why:** witnessed 2026-11-01 (playbook repo, an automation-born author turn resumed from compaction): the pre-compaction plan queued a stop-before-exhaustion park plus a timed resume carrier, computed from a 97-percent probe and an unclaimed mandate read about 90 minutes earlier. At the write boundary a fresh state read showed a parallel carrier had already completed the mandate and landed it, so nothing remained to park, and a fresh probe showed the five-hour window had rolled mid-turn (57 percent used, the reset re-keyed about two hours later than the recorded one), so the resume carrier would have been a duplicate-in-waiting over a live loop. Both queued writes died to the two fresh reads; executing either would have polluted pending_dispatch and armed a pointless carrier.

**See also:** #127 (probe the live boundary before riding a recorded reset; the quota-axis remedy this lesson re-applies at compaction resume), #13 (re-derive the work item's unclaimed state before a long run's final write; the same discipline pointed at the session's own decision outputs), #7 (re-derive inventories from live bytes at execution start).

## 361. A Scripted Whole-File Transform Verifies Its Anchor Matches Before Writing

A checkbox-marking edit run as a python `str.partition` transform silently corrupted a plan file: the anchor substring failed to match (unstable on-disk state), `partition` returned empties, and the script still wrote `head + separators` over the file, truncating the Tasks section. `str.partition` never signals a missed match, so a whole-file rewrite built from partitioned parts must abort when any expected anchor is absent or any replacement count is zero, and the written result must be re-grepped for its expected markers before the step reports success. Prefer one deliberate file edit per checkbox over a scripted sweep; a scripted sweep that finds nothing to change must fail loudly, not pass through. (Witness: gate-removal-inherited-manifest-rows Task 1 checkbox marking, 2026-11-01, restored from HEAD.)

**Extension (2026-11-02 witness, an authoring run's plan-review fold script):** the count guard has an upper bound too: a global str.replace whose anchor also matched an unintended second location duplicated a companion checklist item (under the wrong sibling task's span name) into another task's body; a post-write grep caught it. A replacement that must land exactly once verifies its count equals the expected count, not merely nonzero, and a fold output is re-grepped for the inserted marker AND for the sibling spans it must not leak into before the step reports success.

## 362. A commit:path Existence Probe Exits 128 for a Missing Path, Not 1

**Principle:** Family H (verify the real thing: a subprocess probe's failure modes are enumerated from the tool's contract, not assumed two-valued).

**Trigger:** scripting a history walk that resolves `<commit>:<path>` blobs per commit (rev-list loop feeding `git cat-file -e` / `git show`) where some commits legitimately predate the path.

**Rule:** `git cat-file -e <sha>` is two-valued (0 exists, 1 missing), but the `<commit>:<path>` form is three-valued: a path absent from the commit's tree exits 128, and `subprocess.check=True` turns that ordinary shape into a crash mid-walk. Existence guards over commit:path operands must branch on returncode (`== 0` present; any nonzero for the expected-missing case) and skip the entry, and the guard belongs on parent-record lookups too, not just the head lookup, since older commits fail first. Verify the exit code against the tool, never against the surrounding test's expectations.

**Why:** witnessed 2026-11-02 (playbook repo, an execution run's test rework): a rev-list walk resolving per-commit record blobs crashed with returncode 128 on the first commit whose tree predated the record file; the fix guarded both the commit lookup and the parent-record lookup with returncode checks, after which an absent-blob entry was skipped instead of raising. Note the sibling trap: `cat-file -e` on a bare sha exits 1, so the same guard written for the sha form is wrong for the path form.

**See also:** #359 (existence is not ancestry for a bare sha; this lesson covers the exit-code axis of the same probe family).
## 363. A Target-Checkout Ownership Preflight Runs After the Landing That Moves the Ref

**Principle:** Family H (verify the real thing: the preflight reads the target checkout's working tree, and the target only holds landed bytes).

**Trigger:** composing an authoring run's closeout legs in one chain and running the worktree-removal preflight while the plan still lives only on the unlanded branch.

**Rule:** the removal preflight (`worktree_closeout_migrate.py owned-files-clean --expect-plan`) refuses when the owned plan's byte-identical copy is absent from the target checkout at the same repository-relative path. For a plan authored in the worktree, the primary checkout cannot hold that copy until the landing moves the ref and the checkout updates, so a pre-landing preflight run refuses by construction and no pre-landing retry can pass. Order the closeout land-first: land, then run the preflight, then remove the worktree. A pre-landing refusal naming the owned plan as missing from the target is an ordering signal, not a worktree defect to repair.

**Why:** witnessed 2026-11-01 (playbook repo, an authoring run's closeout): the preflight ran ahead of the landing leg and refused with the plan missing at the primary; the remedy was reordering the legs (land, then preflight), after which the identical preflight invocation passed unchanged.

**See also:** #359 (post-landing facts: a landing citation is certified by the landed history, not the worktree), #43 (the per-call shell that makes each closeout leg its own cwd context).

## 364. A Suite Measured Above the Shell Foreground Cap Runs in the Background From the First Attempt

**Principle:** Family H (verify the real thing: the command's actual runtime against the shell's hard foreground cap, before choosing the launch shape).

**Trigger:** about to run a repo validation command that is a full fixture-heavy suite (here: the done-gate pair `scripts/test_done_sweep_gates_lib.py` + `scripts/test_done_run_wrapper.py`) whose duration a prior run has already measured above the cap.

**Rule:** the shell's foreground timeout caps at 600 seconds and cannot be raised past that, so a suite measured above it is unrunnable in foreground by construction. Launch such a suite as a background shell on the first attempt and read the pass/fail counts from the output file the tool names; do not spend a foreground attempt discovering the cap, and do not treat the timeout event as evidence about the suite's outcome.

**Why:** witnessed 2026-11-01 (playbook repo, done-setup-staging-doc-foreign-arrival-default Task 1): the plan's full-suite validation command (633 tests plus subtests) ran 1838.66s (about 31 minutes); the foreground attempt hit the 600s cap and was moved to background mid-run, completing only on its own afterward.

**See also:** #338 (the same timeout-moved-to-background event strands a lock hold; background-first also keeps lock-holding helpers off the kill path), #286 (a harness timeout report is not a termination proof; read the result from the output file, not from the timeout event).

## 365. The Archive-Egress Receipt Carries the Archived Bytes' Digest, Which the Disposition Fold Changes

**Principle:** Family D (digest binding: a ceremony record's sha256 is computed over the artifact's on-disk bytes at the verification point, not over a head-revision read that may not contain them yet).

**Trigger:** about to satisfy the plan-archive egress gate for a plan whose archive commit folds the `## Disposition of migrated backlog items` section onto the archived copy.

**Rule:** the egress gate hashes the archived file's bytes as the landing sees them, which includes the disposition fold appended at the archive step — a different digest from the exec receipt's `source digest` of the reviewed pre-fold plan bytes. Compute the egress sha from the archived path's on-disk bytes in the worktree after the fold is written, and backfill BOTH digests into the receipt (source digest for review identity, archived-bytes digest for the gate) before the first landing attempt.

**Why:** witnessed 2026-11-02 (playbook repo, prune-audit-standing-flags landing): the receipt carried only the pre-fold plan-bytes digest (c573c90c…), the gate demanded the post-fold archived bytes' digest (aa95dcf8…), and the first landing refused with the missing-evidence leg; appending both digests to the receipt passed the identical invocation unchanged.

**See also:** #5007-family principle above (bytes at the verification point), lesson on the mirrored-evidence-leg homes (both `.ai-playbook/reviews/` copies), #363.

## 366. land-worktree's --expected-tip Is the Source Worktree Tip, the Opposite Referent of land's

The same flag changes referent between the squash-landing helper's modes: in
`land` mode `--expected-tip` is the base branch's expected tip (lesson 34),
while in `land-worktree` mode it is the SOURCE worktree's checked-out branch
tip, and the refusal names that ("source worktree's checked-out HEAD
<source-tip> does not equal --expected-tip <the value you passed>").
`--expected-base` carries the primary base pin in both modes.

Rule: never carry a flag mapping across modes of the same helper; re-derive
each mode's argument referent from that mode's own refusal text, and pass
both `--expected-tip` (source branch tip) and `--expected-base` (current
main tip) on every land-worktree retry.

**Principle:** Family D (a gate's refusal message is the authoritative
enumeration of the contract; the mapping is per-mode, not per-helper).

**Why:** witnessed 2026-11-02 (playbook repo): a strand-adoption landing
passed main's tip as `--expected-tip` following lesson 34's `land`-mode
rule and was refused by land-worktree with the source-tip message; the
re-derivation and retry landed. The first land attempt also failed the
archive-egress gate (missing exec receipt), which was minted and the
landing retried, so two fail-then-retry rounds mutated nothing.

## 367. A Stand-Down on Same-Runtime Stale-Claim Strands Starves the Queue; Adopt or Remove First

When every open plan's execution claim is stale but the owning sessions are
from the same runtime (the claims' session/runtime_id lines identify them),
the strands are adoptable work, not foreign work: check each strand's owning
session and worktree state, resume the run (take over the worktree, rebase,
continue execution), or remove it as leftover, and file backlog rows for
what cannot be adopted this turn. Only genuinely foreign or unknown-runtime
strands park untouchable. Standing down on them 0/N starves the plan queue
while dead worktrees accumulate, and peer sessions may land the strands
during the park anyway.

**Why:** witnessed 2026-11-02 (playbook repo): two exec carriers stood down
0/1 citing "all open plans same-target-held by peer pre-review strands";
the operator corrected the reading, and the same survey showed two of the
four strands had already been landed by peers while the third was fully
executed (23/23 tasks) and adoptable; the adopted strand landed the same
turn (137c50ebd). The correction's durable home is the operator feedback
memory; this lesson is the corpus witness.

## 368. A Posture Knob Shared by N Destructive Arms Needs the Off Pin on Every Arm

**Rule:** when one posture knob gates several destructive arms, the posture
matrix (on / report-only / off, at minimum off vs the default) is pinned per
arm, never once for the family: one arm's off pin proves nothing about its
siblings, and a fall-through where `off` behaves like `on` is exactly the
shape a single-arm matrix hides. Every new destructive arm inherits a
posture-pin checklist item in its own fixture set, and a review panel over
such a knob probes the off posture empirically (a real fixture invocation
per arm), not by reading one arm's branch.

**Why:** witnessed 2026-11-02 (playbook repo, the docs/tmp drain-arms run):
the docs_tmp_drain_arms knob landed with off honored in arm 1 only; arms 2
(dead-root marker drain) and 3 (proof-family drain) tested only the
report-only branch and fell through to quarantine-and-discard with the knob
at off. The full suite was green - only arm 1 had an off fixture - and
three r1 panel workers independently probe-verified the deletion (a
pre-window foreign marker and a whole terminal proof-family session
vanished with the knob off) before the fold gated both spans and added the
missing pins. The miss cost a blocking High finding and a fold round on a
surface whose entire safety story is that knob.

## 369. Sync the Vendored Skill Twin In the Landing Change, Never Mid-Run Before It

**Rule:** a same-change vendored-twin sync (repo skill file -> the runtime
skills home) happens in or after the change's own landing commit, never
mid-run while the bytes are unlanded: peer sessions run vendored syncs that
mirror the runtime home back into the primary checkout, so a mid-run twin
write lands the unlanded bytes into the primary working tree as modified
dirt that reads as foreign. When such dirt appears, compare digests against
the branch's copy before misreading it as foreign: byte-identical dirt
resolves itself at the landing (the landing makes it zero-delta).

**Why:** witnessed 2026-11-02 (playbook repo, the docs/tmp drain-arms run):
the done SKILL.md twin was synced mid-run right after the skill edit; a
peer session's vendored sync mirrored the unlanded paragraph into the
primary checkout, and the closeout's primary-status check showed
`M agents/skills/done/SKILL.md` with the branch's own not-yet-landed text.
A digest comparison against the run branch's copy (all three copies
byte-identical) resolved it in one step; had the bytes differed, the dirt
would have misread as a peer's edit or, worse, invited a checkout -- of
content the run owned. The twin was re-synced after the fold and matched
the landed bytes at landing time.

## 370. A Stage-0 Index Probe Reads an Unmerged Entry as Absent

**Principle:** Family H (verify the real thing: a probe's "absent" answer enumerates
the tool's state space, and a conflicted index holds states a stage-0 probe cannot see).

**Trigger:** scripting a staged-set audit or rewind preflight whose membership oracle is
a `git rev-parse :<path>` probe, on an index that can hold conflict stages.

**Rule:** `git rev-parse :<rel-path>` resolves stage-0 entries only: an unmerged
(conflicted) path exits 128 with "not at stage 0", so a probe keyed on the exit code
classifies a staged-but-conflicted file as absent from the staged set. The same entry IS
listed by `git diff --cached --name-only -z` and is repairable by
`git restore --source=HEAD --staged --worktree -- <path>`. Index-membership oracles for
audits use the diff-cached listing (NUL-delimited) or `git ls-files -u`; reserve the
stage-0 probe for checks that specifically mean "resolvable at stage 0", and settle a
disagreement on a live merge-conflict fixture before trusting either answer.

**Why:** witnessed 2026-11-02 (playbook repo, exec run): a closeout-migrate rewind
guard's staged-set read probed entries with `rev-parse :rel` and read rc 128 as absent
while the diff-cached listing showed the entry staged; verified with a live
merge-conflict fixture (probe 128, listing present, restore succeeds), which upgraded
the shape from a review hypothesis to a staged finding on first-hand evidence.

**See also:** #362 (the commit:path probe's exit-128 family; this lesson covers the
index-stage axis of the same probe shape), #112 (verify the index, not only the
worktree, after restore-based reconciliation).

## 371. A Shared JSON State File's Element Shapes Are the Last Writer's, Not Your Read's

**Principle:** Family D (state-first: the file's current bytes are the only shape of
record; a read is a snapshot of one writer's moment).

**Trigger:** a closeout, dispatch, or park write into a JSON state file that several
sanctioned writers rewrite whole (the scheduler state file's `children[]`, decision, and
queue fields), while peer carrier sessions are live.

**Rule:** when the write touches one entry inside an array, do not assume the element
shape the read showed: a peer rewrite between the read and the write can change a field's
JSON type or an entry's shape wholesale (entries from dicts to strings), so a prepared
write built on the stale shape crashes or clobbers. Shape-check every element the write
touches against the fresh bytes at the write boundary; on a shape mismatch, re-read the
file, write only this session's own entries adapted to the current shape, preserve every
peer entry unchanged, and record the drift. A lost race yields and retries on the fresh
shape; it never forces the stale read's shape back over the file.

**Why:** witnessed 2026-11-02 (playbook repo, an authoring run's final closeout write):
the turn's read showed `children[]` entries as dicts; concurrent peer sessions rewrote the
state file before the write (the children array shrank, several entries and the decision
fields were rewritten as strings), and the prepared full-structure write raised
`TypeError: string indices must be integers`. The drift-retry (fresh re-read, update only
the session's own dict-shaped entry, emit the decision fields in the current string shape,
preserve peer entries) landed the closeout without clobbering a peer.

**See also:** #195 (the memory-index variant: repeated staleness refusals are a race
signal resolved by one atomic rewrite of the target lines; the JSON shape-drift variant
here surfaces as a crash, not a refusal, because the stale shape still parses), #63 (key
ledger-edit predicates on stable identifiers, not human phrasing), #360 (re-run queued
decisions on fresh reads; the same fresh-read discipline pointed at the write's shape
assumptions).

## 372. A Path-Equality Gate Self-Exemption Needs the Primary-Path Declaring Operand After a Certification Checkpoint

**Rule:** a gate whose self-exemption compares the declaring artifact by resolved path alone cannot recognize the declaring artifact once a byte-identical twin exists elsewhere; the certification-time checkpoint that places certified plan bytes on the primary checkout creates exactly such a twin. When a coverage or duplicate gate is run from an authoring worktree after that checkpoint, resolve the declaring operand in the primary checkout (`--check-coverage <primary>/docs/history/plans/<plan>.md --repo-root <primary>`) so the path-equality exemption matches, and treat a worktree-relative declaring operand as suspect whenever a checkpoint twin exists. The general shape: an exemption keyed on identity must key on every identity the procedure can produce, or the caller must canonicalize the operand to the path the scan enumerates.

**Why:** witnessed 2026-11-02 (playbook repo, authoring run): after the certification checkpoint placed the plan bytes on main, the duplicate-origin coverage gate run with the worktree-relative declaring operand named the primary twin as the covering plan and failed `OUTCOME: fail` on a correct certification; re-running with the primary-path declaring operand passed. The twin-counts-as-citer behavior is correct for byte-different plans; only the identical-bytes case is the false conflict. See also #280 (the same gate's origins-form mismatch: frontmatter array versus markdown header; a form lesson, not an identity lesson), #365 (a landing's archived bytes' digest changes under a later fold; a digest-fidelity family neighbor).

## 373. Clear a Blocked Log Write With a Sha-Verified Unstage-Restage Window

**Principle:** Family D (recover and land through the owning machinery against current state: the refused gate reruns on genuinely clean state and is never edited, bypassed, or staged around).

**Trigger:** a mandated shared-primary transaction (the rolling-log write's `done_run.sh` class) refuses on a staged path outside the declared owned set, while the write's own bytes are checker-green and an explicit operator direction authorizes completing the interrupted write.

**Rule:** record the foreign path's staged blob sha and verify its worktree bytes hash to the same blob; `git restore --staged` only that path (the index entry drops, worktree bytes untouched); rerun the refused transaction; `git add` the path back; verify the staged blob sha is byte-identical before reporting success. The operator direction gates the window: a foreign staged entry is another session's in-flight state, so without direction the response stays stand-down and park. Calibrate any working-tree drift guard from the drafted artifact's actual line count before entering the window; a bound set from an estimate aborts mid-window and strands the hold abandoned.

**Why:** witnessed 2026-11-02 (playbook repo, operator-directed self-heal): a checker-green investigate entry landing refused three times over a peer's hours-old staged row; the window landed the entry (0ec10c5bd) with the peer's staged state restored byte-identical, and the same window landed the follow-up remedy entry (9c7fd1610). The one mid-window abort was self-inflicted: a numstat ride-along bound of 38-52 lines against an entry that is 34 lines; the bound, not the tree, was wrong.

**See also:** #344 (retry a blocked teardown after a wait before parking - the park-versus-retry split this rule's operator gate refines), #351 (an uncommitted authored edit rides a peer's whole-file commit - the ride-along hazard the worktree-untouched rule and the pre/post sha equality guard against), #243 (recover and land through the owning machinery - the family's cherry-pick sibling).

 Remedy arm re-witnessed 2026-11-02 (playbook repo, authoring run): when the blocked write's content is a non-time-critical mark (an entry freeze line) and the blocking bytes are a LIVE peer's unstaged edits to the same file (not the staged shape this lesson's window remedy clears), the sanctioned move is to defer the commit entirely - keep the mark in the working tree, proceed with placement, and let the peer's next whole-file log commit carry the mark durably; verify the mark landed on main before relying on it (the landing sweep's mixed-worktree-file refusal is the signal distinguishing this shape from the staged one).
## 374. Budget a Plan's Byte Balance Across All Its Tasks at Authoring

**Trigger:** an execution run reaches a later task whose standing constraint requires the edited file's operative-byte delta at or below zero, after an earlier task already spent the file's only retired-paragraph payment, and the new task adds genuinely new semantics with no dedup source left.

**Rule:** when a plan's standing constraint prices byte balance per file, the authoring pass must sum the constraint across ALL of the plan's tasks against the file's total available payment (retired paragraphs, in-file duplications), not validate Task 1 against its own retired bytes and leave later tasks unpaid. When a later task's required content structurally exceeds the remaining budget (this run measured the irreducible new content at ~800 bytes against a 212-byte remainder), the executor's sanctioned shape is: compress maximally, disclose the residual in the boundary commit and manifest, and file a byte-debt backlog row naming the payment path - never silently mark the GREEN checkbox, never stop to ask.

**Why:** witnessed 2026-11-02 (playbook repo, maintenance-self-heal-first-on-blocks execution): Task 1 paid its rewrite from the retired 448-byte Blocker recovery paragraph (net -52), leaving Task 2's stale-baseline + AI-owned arms (+610 own, +558 cumulative) with no payment source; three fix/compression passes proved the target infeasible and the disclosed-debt shape carried the landing (bb9908367).

**See also:** the repository guidelines' anti-growth rules (review-time pricing until the byte-budget gate lands), and #65's witness family for the landing-side disclosure discipline.

Sixth witness extension to #65 (2026-11-02, execution run landing, three-way landing): the two-sided egress record gains a third placement arm. The record committed ON the run branch refuses the landing ("reviews-home egress in the landing"), and the archive gate reads the record from the PRIMARY's reviews home - so when the branch cannot carry it and the worktree-side mirror was not used, the sanctioned shape is a pre-landing rider commit on main (pathspec-scoped when the primary holds foreign staged state), with the branch rebased onto the new tip before the squash. The sequence that stuck: land the record on main, rebase the branch, re-run probe + land-worktree with the updated --expected-tip/--expected-base.

## 375. A Stale-Base Authoring-Branch Rebase Conflicts at Every Plan-Touching wip Commit After the Certification Checkpoint

**Principle:** Family D (recover and land through the owning machinery against current state: the prescribed stale-base remedy rerun to completion, not aborted).

**Trigger:** an authoring self-landing refuses with "landing base stale" after peer landings moved the default branch, while the certification-time checkpoint has already placed the plan's final certified bytes on the default branch.

**Rule:** rebase the authoring branch onto the current default tip inside the worktree and expect every plan-touching `wip:`/fold checkpoint commit to conflict (both sides added or modified the same plan path); resolve each conflict to the default branch's certified checkpoint bytes (`git checkout main -- <plan>`), never to the worktree-side intermediate state. The wip and fold commits collapse against the already-final bytes (identical content drops them or leaves empty commits to skip), and only the branch-unique riders survive; verify the rebased tip's plan bytes hash to the certified digest, then re-run probe and landing with the updated tip.

**Why:** witnessed 2026-11-02 (playbook repo, an authoring closeout): the first landing refused over four peer commits; per-commit conflict resolution to the certified bytes collapsed seven checkpoint commits into the checkpoint and left the two rider commits (residual backlog rows, covered flip) as the branch's whole delta, and the retry landing passed on the first attempt. Attempting to preserve the worktree-side intermediate bytes would have reverted the certification checkpoint.

**See also:** #372 (the checkpoint-twin hazard for path-equality gates - the same checkpoint creating the collision surface this rule resolves), #65's sixth-witness extension (the sibling shape: pre-landing rider on main then branch rebase), #5/#6 (the stale-base landing family this remedy belongs to).

## 376. A Script Setup Entrypoint Does Not Subsume the Skill's Phase 0 Capture Duties

**Principle:** Family A (state re-derivation: an entrypoint's responsibilities are what its code does, not what the skill that usually wraps it would have done).

**Trigger:** an authoring or execution run routes through a bare script entrypoint (for example `done_run.sh setup`) instead of the owning skill's full phase walk, and the closeout's baseline-backed migration later refuses with "baseline file not found".

**Rule:** when a run skips the owning skill's phase walk and calls the script entrypoint directly, run the skill's Phase 0 capture duties explicitly before any plan-file write; a bare setup does not capture the closeout baseline. If the skip is discovered only at closeout, the sanctioned recovery is the late recapture (`capture --out <session-dir>/closeout-baseline.json` then migrate), recorded as a capture-failure deviation in the run record - never an implicit-empty-baseline migration, which the tool refuses by design.

**Why:** witnessed 2026-11-02 (playbook repo, an authoring self-landing run): the run invoked `done_run.sh setup` directly (which printed the done-lock env and ran the residue sweep but never wrote `closeout-baseline.json`), and the closeout `migrate` refused until a late capture ran; the migration then completed with 1 file moved and 0 collisions, but the deviation is a recorded capture-failure the next auditor must weigh. The cheap pass is capturing at Phase 0 alongside setup.

**See also:** #269 (the one-baseline capture-once discipline), #319 (a baseline can sit in the wrong checkout), the foreign-run-residue provenance check that governs recaptures into an existing session dir.
