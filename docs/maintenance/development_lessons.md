# Development lessons

Project lessons corpus for this repository's agent-runtime engineering: running plans on the
execute-plan driver, hardening that driver, and operating multi-worker execution in linked
worktrees. Lessons are convention-tagged (`**Principle:** Family X`) per the shared lesson
template; incident witnesses reference this repository's own public artifacts.

## Core Concepts

- **Machine manifest:** the driver's persisted run state (`runtime_state.json`), the single
  source of truth for a run. Its only sanctioned write path is the driver's own locked,
  receipt-recording methods; manual edits stay prohibited.
- **Serialized task contract:** the driver-built worker prompt. The driver validates the
  orchestrator prose, then sends only the serialized contract, which carries the plan task
  section including the parent-owned `Commit:` line.
- **Launch reservation:** the durable capacity hold a claim carries while a worker is launched;
  released at the terminal boundary by the done/recovery transitions.
- **Self-hosted runtime plan:** a plan executed by the execute-plan runtime while its tasks
  modify that same runtime. The run's seed state predates every contract change the run lands.

## 1. Probe a Lifecycle Driver Through Its Read-Only Surface; a Mutating Method Is Never a Diagnostic

**Principle:** Family H (verify the real thing, not the abstraction: observing driver state
means reading it; exercising a transition to "see what happens" performs the transition).

**Trigger:** a launch, resume, or checkpoint operation refuses with a state-dependent reason,
and the next step under time pressure is calling the underlying mutation method in-process
(here, the claim launch method) to locate the wedge.

**Required behavior:** Diagnose driver state only through read-only operations (status,
readiness, inspect, inventory consults). Never invoke a state-mutating lifecycle method as a
diagnostic: a mutating call performs the real transition, consumes real lifecycle slots (a
launch reservation, a handoff intent slot, a worker row), and can strand the claim in a shape
no recovery operation reaches. If a behavioral probe is genuinely unavoidable, run it against a
throwaway manifest, and still assume the probe consumes the slot it takes.

**Why this matters:** A relaunch refused for capacity was "diagnosed" with an in-process launch
under the live claim. The call started a real no-op probe worker, consumed the handoff intent's
launch slot, and the launched-intent fence then blocked every relaunch until a dedicated
recovery operation existed. The diagnostic cost a full recovery cycle on top of the original gap.

**Shape trigger (when to suspect this family):** any claim, lease, or queue lifecycle with
fenced transitions and durable persisted state, operated by an agent that also holds the
implementation import.

**See also:** Lesson 2 (recover stranded state only through the driver's own locked methods);
`agents/skills/execute-plan/runtime-contract.md` (handoff and recovery fences).

## 2. Recover Stranded Run State Only Through the Driver's Own Locked Methods

**Principle:** Family D (single source of truth: the machine manifest is authoritative, and its
only sanctioned write path is the driver's locked, receipt-recording mutation methods).

**Trigger:** a run wedges on state the current CLI cannot fix through a documented operation: a
stale launch reservation left behind by a skipped success-path release, or a claim whose closing
operation does not exist yet, while the run must continue.

**Required behavior:** Drive the driver's own locked internal methods in-process (the exact
methods the CLI transitions call), never raw edits to the persisted manifest. Pair every
recovery with all four anchors: a pre-recovery backup of the manifest stored beside the
recovery script; an adapter or provider record consulted as independent evidence for each
identity decision (this worker is terminal, this claim is closed); a re-run of the driver's
readiness validation afterward; and a session-manifest entry recording the recovery plus the
boundary procedure that substitutes for the missing operation (for example, release the
completed claim's reservation after record_done) so later tasks repeat it until the runtime
lands the closing operation.

**Why this matters:** Two capacity-wedge recoveries in one run followed this pattern and left
the manifest auditable (backups, witnesses, re-validation). A raw edit would have broken the
receipt, generation, and digest fences that make the manifest a crash-recovery record.

**See also:** Lesson 1 (read-only diagnostics); Lesson 3 (the seed-completion sibling for
contract evolution); `agents/skills/execute-plan/runtime-contract.md` ("Manual manifest edits
stay prohibited").

## 3. A Self-Hosted Runtime Plan Strands Its Own Seed; Complete the Seed at Each Contract Boundary

**Principle:** Family E (temporal and ordering invariants: persisted run state created before a
landed contract change is stale under the new contract until it is reconciled, at every
boundary the change touches).

**Trigger:** a plan whose tasks tighten the executor's own launch or evidence contract (new
mandatory launch fields, a new capture path that requires new manifest metadata) while the run
itself was seeded before those fields existed.

**Required behavior:** After each task that lands a contract-tightening change, compare the
run's seed against the new contract before the next launch, and complete missing metadata
through the runtime's own helper methods (the same helpers the CLI operations use), with a
pre-edit backup, then let the driver re-validate readiness before launching. Budget this as a
recurring boundary duty in the run bookkeeping: for a self-hosted runtime plan, seed completion
repeats at every contract boundary, it is not a one-off fix.

**Why this matters:** One run landed a contract that made four task fields mandatory at launch,
then landed an evidence-capture path that required the per-task criteria map; the run's create
predated both. Completing each through driver helpers kept the seeded manifest launchable
without ever editing it by hand.

**See also:** Lesson 2 (locked-methods-only mutation, with backups and re-validation);
`agents/skills/execute-plan/runtime-contract.md` (seeding boundary and resume reconciliation).

## 4. Commit Ownership Follows the Serialized Worker Contract

**Principle:** Family D (single source of truth: the serialized task contract the driver
validates and sends is the worker's authoritative instruction surface; commit ownership and
bookkeeping granularity follow it, not the surrounding prose).

**Trigger:** composing worker prompts and bookkeeping commits in a driver-executed run, where
skill prose and the driver's manifest boundary describe different commit compositions.

**Required behavior:** In a driver-executed run, the worker prompt is the serialized task
contract including the parent-owned `Commit:` line, so the worker creates its own task-scope
commit, validated against the task's path allowlist at the done boundary. Orchestrator
bookkeeping (plan checkbox flips, intermediate-review backlog captures) rides a separate
bookkeeping commit immediately after record_done, never inside the task commit. When skill
prose and the driver's boundary disagree, the machine manifest is authoritative: record the
deviation once in the run manifest and apply the settled pattern to the remaining tasks instead
of re-litigating the composition per task.

**Why this matters:** One run settled this pattern at its second task and applied it through
the eighth: task commits stayed exactly task-scoped, bookkeeping stayed reviewable on its own,
and the single recorded deviation note replaced per-task argument. When the driver later began
sending only the serialized contract as the worker prompt, the pattern already matched it.

**See also:** Lesson 5 (which runtime may perform the commit); `agents/skills/execute-plan/SKILL.md` (commit authorization and the done boundary).

## 5. Route Lock-Holding and Commit Duties to a Runtime That Can Hold Them

**Principle:** Family H (verify the real thing, not the abstraction: a worker's sandbox
boundary is whatever its host actually permits, learned from its failed operations, not from
its job description).

**Trigger:** dispatching the done boundary of a driver-executed run (acquire the host done
lock, run gates, create the commit) to a worker, in a repository checked out as linked git
worktrees.

**Required behavior:** Before dispatch, verify the target runtime can hold the lock and create
the commit where the repository actually lives. A sandboxed worker cannot do either here:
writes outside its workspace are denied, so it cannot hold the host done lock, and a linked
worktree's git index lives under the primary checkout's `.git/worktrees/` metadata directory,
which the sandbox cannot write, so it cannot commit even inside its workspace. Route the duty
to the dispatching orchestrator (acquire the lock, perform the commit inline after gates pass)
or to a sub-agent on the host runtime, which can do both. Keep the worker's failed attempts in
the task log; they are the evidence for the routing decision.

**Why this matters:** A done worker's first two attempts failed on exactly these two walls
before the run rerouted the duty; a later implement worker independently hit the same index
wall. Recording the failures once turned an undocumented sandbox limit into a settled dispatch
rule for every later task.

**See also:** Lesson 4 (commit ownership between worker and orchestrator); Lesson 2 (locked
in-process recovery when no operation exists).

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
