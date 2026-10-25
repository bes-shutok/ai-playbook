# Template: execution child (execute-plan skill)

Extracted module of the maintenance prompt-templates file (agents/skills/maintenance/prompt-templates.md); moved 2026-10-10 by plan docs/history/plans/2026-10-10-maintenance-skill-size-refactor.md Task 4; the dispatched child loads this file plus agents/skills/maintenance/duties-core.md, nothing else.
## Execution child (execute-plan skill)

Distinguishable by the span "You are the SCHEDULER, not the executor". This blueprint keeps its own fill-in field lines at the end of the fenced body; the SCHEDULER-voice opening and the `{execution_time}: at` field line are deciding-turn instructions, and `{execution_time}` is an input to the scheduling call, never part of the payload. What enters the scheduled payload follows the SKILL.md Step 5 dispatch slice. The fenced body:

```
Schedule at {execution_time} the following. You are the SCHEDULER, not the executor:
your ONLY job in this turn is to create the one-shot automation below and confirm it.
Do NOT start Phase 0, do NOT create branches or session dirs, do NOT run the plan,
readiness gate, or any plan work yourself. Everything else in this message is for the
scheduled session, not for you.

<prompt for the scheduled session>
You are an unattended scheduled session in the repository at {REPO_ROOT}; do not create
or schedule further automations beyond the re-arm duty below and the single successor-dispatch duty below. The user has pre-authorized
everything below: never block on questions, decide and proceed; never push to origin.

EXECUTION CLAIM, the claim file this session writes before any plan work, in gate-before-write order: before any plan work the claim file docs/tmp/execution-claims/<plan-slug>.md is created in the primary checkout (explicit-rooted form) by scripts/execution_claim.sh, the creation procedure of record (the atomic take invocation the PER-EXECUTION WORKTREE paragraph below pins creates the claim create-or-refuse as its first half; the same script's claim mode serves the authorized primary-placement lane; the file carries exactly four frontmatter lines at creation, session: <this session's id>, plan: <the target plan path>, created: <iso timestamp at creation>, updated: <iso timestamp at the latest refresh>, plus the line branch: <the run's recorded branch, written when the invocation passes --branch> and the line start-commit: <the run's start commit, written when the invocation passes --start-commit and recorded as resolved through `git rev-parse --verify`>, and gains the base line, base: <the run_base value recorded at worktree creation, verified at swap time by the parentage gate's `--expected-base` leg when the caller passes it>, at the take itself when the take passes --base, otherwise at the first refresh that passes it); a fresh foreign claim (a claim naming a session id other than this session's whose updated: is fresher than one cadence period, 2 hours) refuses the start: stand down writing nothing; a stale foreign claim is taken over (re-read the file immediately before the unlink and unlink it only while it still names the same foreign session id with a stale updated: line, recording the takeover, then create this session's claim); refresh updated: at every phase boundary, at every task completion inside the implementation loop, and at every review-round iteration (a refresh recreates the claim file when a takeover unlinked it); delete the claim at closeout and on an owned stand-down; a claim left behind by a session that died decays by freshness, never by trust.

PER-EXECUTION WORKTREE, created before any plan work: this run creates its
own ad-hoc worktree on its own branch per the Worktree-first standard
section in agents/skills/execute-plan/SKILL.md, the worktree's branch name
deriving per the execute-plan Phase 0 branch-naming convention, and all plan work, task
commits, the archive commit, and the review loop run inside that worktree on
the worktree's own branch. The creation itself runs through the single pinned take invocation, the procedure of record:
`bash scripts/execution_claim.sh take <plan-path> --session <id> --branch <name> --worktree-parent <dir> [--base <ref>]`,
which takes the execution claim create-or-refuse (the EXECUTION CLAIM duty above) and creates this worktree in one atomic step, a refusal leaving no worktree; complete the standard's full Transfer-in implementation in the
worktree before the PRE-STEP readiness gate, and capture the closeout baseline (the
execute-plan session bootstrap's closeout-baseline capture) as part of the
run's setup so the closeout migration never refuses on a missing baseline;
if the worktree cannot be created, delete this session's claim
file per the EXECUTION CLAIM duty's delete arm and stand down writing
nothing.

Before any plan work (in the run's worktree, after the standard's transfer-in
step): verify no merge or rebase is in progress in the run's own worktree and
the run's own per-worktree done lock is free; if either fails, stand down and
write nothing.

PRE-STEP (mandatory before Phase 1): run the Step 0.5 readiness gate
(python3 scripts/plan_readiness.py <plan-path>) and branch on its four
outcomes (scripts/OUTCOME_CONTRACT.md): exit 0 with the final `OUTCOME: pass`
line proceeds; exit 1 (`OUTCOME: fail`, the first failed readiness condition
on stderr) is handled below for the stale-digest class; exit 2
(`OUTCOME: indeterminate`) or exit 3 (`OUTCOME: tool_error`, including the
sibling-compatibility mismatch and usage violations) is never a readiness
fail: record the validator's error evidence and stop the run without writing
(a validator that could not run reliably is never a recert trigger); and a
run with no final `OUTCOME:` line is tool error per the contract's no-line
rule: stop and re-derive the state from disk. If the gate fails with a stale
source_digest, or with an anchor-leg refusal over plan bytes that re-hash to
the latest ready sidecar's digest, the repo moved under the plan: run a fresh focused review-plan
re-cert round over the current bytes, fold all blocking findings into the plan
(re-baseline stale probes/edit targets against the current tree), write the new
review round r<N> staging doc + .stats.json sidecar (digest = sha256 of folded
plan, ready=yes, zero unresolved blocking), and re-run the gate. Only start
Phase 1 once the gate exits 0.

Recovery procedure (the sole home for H/claim-H → R resumption; the other run documents link here): when the target plan already carries checked checkboxes or a saved run manifest exists, this is a resume run, resolved through the claim gateway's `take` in Phase 0 before the saved-manifest refresh, any other run mutation, work, or closeout, with `--session` equal to the active ID returned by the shared session-channel helper (scripts/session_channel.py). Recovery applies to a SURVIVING foreign claim — a missing claim is the fresh-create path, not a conversion input — and a runtime may advertise conversion only after its configuration owner has run the exact-ID terminal smoke check against the configured provider and completed the provider smoke evidence record at `docs/history/release-evidence/session-status-provider/<runtime-id>.md`; without that verified evidence the existing refusals stay active. The gateway routes three shapes. (a) Verified live same-session resume: the claim and manifest name this session; the gateway hands back to the own-claim arm and the saved manifest's `updated:` refreshes first — behavior unchanged. (b) Dead-run conversion: a foreign claim whose run manifest remains at its exact registered-worktree path; the gateway verifies the manifest identity (canonical `session_id:`/`plan_path:`, legacy `Session:`/`Plan:`, or legacy `session_id:` with the claim supplying the exact plan), queries the runtime-configured session status provider (`session_status_command` in the primary checkout's facts file; an absolute executable invoked in a controlled environment; exactly one JSON object with the string fields `session_id` and `status`; only `terminal` proceeds, and a 10-second bound with 64 KiB stream caps refuse everything else), validates the completed-run boundary over the stable tuple (`run_session_id`, exact plan path, registered worktree, bound through the runtime state, every `task_boundary:` row, the Phase 2/3 records, each task's contract-path log, and the `pre_archive_receipt`, with a bounded legacy binding for pre-tuple artifacts whose bytes are never rewritten), takes the target worktree's done-lock then the repository merge-lock (roots derived from the OS account record, caller lock variables cleared, records verified against the gateway's own PID and tokens), atomically replaces the claim beside the old one in one rename (the prior `created:`, `branch:`, `start-commit:`, and `base:` preserved; a recorded manifest conflict refuses first), canonicalizes the manifest (`session_id:`, `plan_path:`, `run_worktree:`, `run_branch:` written to the resumer and the attached target; legacy aliases removed; unrelated content preserved), releases only its own lock tokens in reverse acquisition order, and returns success before the occupant refusal and the worktree add — the run adopts the exact registered worktree and continues from the first unchecked task without re-running completed ones. (c) Refusal, unchanged bytes: a live, paused, or unresolved prior owner; an incomplete or ambiguous run boundary; a missing, relative, or unconfigured provider; mismatched claim and manifest owners (the interrupted-replacement shape — no lineage is inferred and no automatic recovery runs); symlinked or ambiguous manifests; or any lock record that will not verify as the gateway's own refuses the conversion for operator reconciliation, and the resumer falls back to the claim duty's stale-takeover arm only when the conversion context is absent AND the registered-manifest scan finds no manifest anywhere (every registered worktree's facts resolved, none present) — an unreadable facts document or any surviving manifest preserves the claim instead. Manifest discovery resolves the run tmp directory from the specific registered worktree's facts document's `tmp_dir` key — missing or unreadable facts refuse discovery, and the docs/tmp path is never substituted. Phase 0 of every new run initializes the canonical identity block (`run_session_id` as the immutable origin identity, the mutable current `session_id`, the exact repository-relative `plan_path:`, and `run_worktree:`) before any log or runtime state exists, and new `task_boundary:` rows, logs, runtime-state writes, and the receipt carry the stable tuple; verified legacy artifacts migrate through the bounded legacy binding only after all its checks pass, branch fields retained. The PRE-STEP re-certification covers the digest drift the checkbox marks cause.

Stand-down report duty: when the target plan's own first task prescribes an
edit-nothing stand-down (its external gate is unsatisfied), you execute that
stand-down and nothing beyond it: write .ai-playbook/last-stand-down.json with
exactly the keys {"plan": "<plan path>", "reason": "<gate-unsatisfied-reason>",
"date": "<iso date>"} as your LAST action before reporting, and your final
report opens with the literal marker line STAND-DOWN: <plan-path>
<gate-unsatisfied-reason>; if this session runs in an ad-hoc worktree, write
that json into the primary checkout's .ai-playbook/last-stand-down.json
(.ai-playbook/ is gitignored, so a worktree copy never reaches the checking
scheduler turn, which reads only the primary checkout) and verify it present
there; on any other outcome the marker must not appear anywhere in the report
and the file must not be written, so an ordinary failure report can never fake
a stand-down.

CONTEXT CHECKPOINTS, a standing duty for every step block of this run: after each blueprint step block, at a boundary only, never mid-task, log one telemetry record (skill: execute-plan) to docs/tmp/execute-plan/<plan-slug>/context.jsonl, creating the run's telemetry directory if needed; at that same boundary measure context size per the overlay's measurement primitive (agents/skills/maintenance/zcode.md "Context measurement primitive"; a char-count proxy fallback result is labeled an estimate in the record) and act per the threshold ladder of the execute-plan `Context budget checkpoints` policy.

TASK-BOUNDARY CHECKPOINT, a standing duty at every green task boundary of this run: the duty at every green task boundary is the durable checkpoint state (the task's plain boundary commit landed with its `task_boundary:` manifest row written, the session manifest updated, the execute-plan Step 1.4 verification gate passed), so an automatic harness compaction can only land on resumable state; the session never invokes compaction itself; the manifest (workflow_state, task checkboxes, execution record) is the resume source of truth, never the transcript summary; the boundary telemetry record duty is unchanged.

Execute {some_plan} via the execute-plan skill: inside the run's own ad-hoc
worktree that the PER-EXECUTION WORKTREE duty created before any plan work,
on the worktree's own branch (the worktree's own branch already satisfies
the Phase 0 worktree setup; run the remaining run-setup steps inside it),
one task at a time with
tests green, plan checkboxes marked, plain boundary commits
per task (each boundary writes its `task_boundary:` manifest row; done runs once
per run at the final closeout), then Phase 3 review/fix loop until one fresh review of the current
digest reports zero unresolved blocking findings (cap 5 total rounds; defer the
two regenerating classes to backlog per ADR-0002). Accept all review suggestions;
choose the backlog-deferral default when the flow would stop to ask. Discharge
non-blocking fix-risk asks by recording per review-staging's receiving-review
consumer row and surface them in the exit report. Archive the plan per the plans
skill, move backlog origins to completed/ with Status: done, and after any git-mv
verify the committed destination carries its content edits (rename-commit trap);
before the archive commit run the origins-closure check (`python3
scripts/check_plan_origins_closed.py --plan <archived-plan>`; read through the
outcome contract's final `OUTCOME:` line: exit 0 (`OUTCOME: pass`) proceeds;
exit 1 (`OUTCOME: fail`) names the stragglers; exit 2 (`OUTCOME:
indeterminate`), exit 3 (`OUTCOME: tool_error`), and a run with no final
`OUTCOME:` line (tool error under the contract) stop the archive step for
re-derivation from disk, never read as closed) and disposition
or record why open every straggler it names for that plan;
the archive commit is a per-run worktree commit: the archive move, the
document-registry row append, the origins-closure check, and the archive
commit run inside this run's worktree on the run's branch and ride the final
squash merge, never as a primary-checkout commit. That branch-riding shape is
the only rider surface: the origin fold or deletion and the ownership-registry
row append ride the same run branch as rider commits before the landing
critical section, never as main follow-up commits after the landing.
Then run the done skill ONLY on clean exit; it runs in this worktree; done
locks are keyed per-worktree on --show-toplevel,
so the run's done lock is its own (stand down if a peer holds that worktree's
done lock); commit only this session's files (leave foreign staged files and
peer changes alone); the merge landing lock stays repo-keyed and is acquired
at the landing critical section as prescribed. Finally squash merge to the repository's default branch (the canonical Base-branch resolution rule resolves the per-project base for worktree creation and the execute-plan and plans landings; the default branch is this payload's landing target, and equals the resolved base in a default-branch-integration project; a
checkout-flow project's resolved base differs from this landing target, and
the mismatch guard in the landing critical section fails the landing closed
naming both refs):
first acquire the merge landing
lock (bash scripts/done-lock.sh merge-wait-acquire --label execution-final-merge
--max-wait 300; on timeout (the outcome contract's `OUTCOME: fail`) take the
lock-acquire timeout path: stand down
keeping the branch and, before any report, write the deferred-landing record
and note per the deferred-landing record duty below; an `OUTCOME:
indeterminate` (ambiguous holder) or `OUTCOME: tool_error` result, including
a run with no final `OUTCOME:` line, takes the same stand-down path and is
reported, never read as acquired) and hold
the acquired MERGE_LOCK_DIR/MERGE_LOCK_TOKEN exports across the whole landing:
inside the critical section the landing is worktree-complete, the rebase onto the current default tip inside the run worktree and
the squash merge there build the landing, the primary checkout receives only
the final squash commit through one compare-and-swap ref update, the landing
never writes the primary checkout's index or working tree, and staging
(git add) in the primary checkout is a landing-gate violation. Before the
squash, compare the run worktree's
creation base (the base branch the worktree was created from, per the
canonical Base-branch resolution rule) with the landing target (the
repository's default branch); when they name different branches - a
checkout-flow project's divergence - the mismatch fails the landing closed
before any ref move: write the deferred-landing record and note per the
deferred-landing record duty naming BOTH refs (the creation base and the
default branch), keep the branch and worktree, and end the landing; never
sweep operator-branch commits onto the default branch. Dependency-branch
landing-race discipline (added
2026-09-25, parked-dependency visibility): a dependency-branch landing verifies
its squash against the actual pre-landing main, meaning the merge base re-read
from the default-branch ref at the commit moment, never the branch lineage;
when a parallel landing is detected between lock acquisition and commit (the
default-branch ref moved), the landing gate set re-runs against the moved main
before the landed-bytes verification: the PII and hygiene gates, the peer-byte
guard with its merge base recomputed from the moved default-branch ref, the
gmail-author check, the dirt regression gate against the new merge base, and
the landed-commit test probing the dependency-landing record identity's
landed_path. `Severed-ancestry landing rule (diff-based landing):` prescribing, when `git merge-base refs/heads/<default> <branch>` prints nothing, a diff-based landing only, in the arm context the landing runs in, and stopping fail-closed (keep the branch and worktree, report for operator reconciliation) when neither fork-point source yields the fork point nor a landing context is available; the single run-worktree context: apply the branch's cumulative diff against its fork-point commit (the branch creation start point recovered mechanically as the object value of the oldest `git reflog show --format='%H %gs' <branch>` entry whose message starts with `branch: Created from` - the message may carry a name such as main or HEAD instead of a sha; the entry's object value is the fork point in every form - or from the run's worktree-creation record (the session manifest's run_base field, recorded at Step 0.4 as the base branch ref and commit captured at creation - the branch start point for a fresh run worktree); the cumulative diff is `git diff <fork-point> <branch-tip>`) with `git apply --index` inside the run worktree against the detached default-tip state (staging exactly the diff's paths; a non-zero apply exit stops the landing: keep the branch, take the recipe's deferred-landing path, and report the conflict for operator reconciliation), before committing the applied diff, the cumulative diff passes through the guard's check-diff --against <fork-point> --repo <run-worktree> (the cumulative diff git diff <fork-point> <branch-tip> piped to the mode's stdin; probe the repo-local scripts/reverse_squash_guard.py, then the deployed $HOME/.ai-playbook/scripts/ copy; a guard copy absent from every resolved path is a rc 1 deployment gap, never a skip; exit 1 takes the deferred-landing path naming the findings; exit 2 is a tool failure: stop and report), commit there scoped to the diff's changed paths (`git commit -- <the diff's changed paths>`), run the pre-swap invocation with `--new-commit` pinned to the built commit sha (never `refs/heads/<default>`, which the detached commit does not move), land through the compare-and-swap ref update, run the post-landing invocation, and route refusals per the worktree arm's mechanics including its inverse-compare-and-swap rollback; include the prohibition sentence `never merge, rebase, branch -f, or ref-update the default branch to any commit of the severed chain` with the witnessed rationale (the 2026-09-27 racorpus and grillfork landings; a rebase onto the rebuilt main finds no common ancestor and explodes) Base-branch ref-move integrity receipts (the worktree-arm landing and the severed-ancestry diff-based landing, per the execute-plan landing critical section and the closeout audit duty, which own the semantics): the fast-forward verification before the ref move, the two-value CAS form, the pre-swap empty-diff refusal as a stop-for-adjudication refusal (excluded from the arm's generic exit-1 deferred-landing routing and from the parked-dependency unblock recipe's every-refusal blanket, since a restart reproduces the same tree-identical commit), and the post-landing completion duty's two `scripts/base_reflog_audit.py` subcommands (`reflog-window --since-sha <pre-tip>`, `landed-receipt`) with the landed commit's first-parent diffstat recorded beside the tree-equality receipt. Worktree arm (the only arm; the whole landing machinery runs inside the run
worktree): the helper invocation is the only sanctioned composition, and the failure-path prose below never authorizes a hand-composed equivalent; when the repository-local helper is absent, record a deployment gap naming the probed paths and defer the landing (no alternate helper copy or hand-composed substitute is authorized). The landing is one mechanical operation, the helper invocation
`bash scripts/land_squash.sh land-worktree --branch <branch> --expected-tip <sha>
--message <text>` (plus `--expected-base <sha>` whenever the run records a base
pin) run under the acquired merge lock; the helper owns the class's gates (tree
equality between the squashed branch tip and the landing commit, base freshness
(the reverse-squash guard's check-landing), the parentage pre-swap and
post-landing invocations, and the two-value compare-and-swap ref update of the
default branch), and the primary checkout receives only the final squash commit,
its index and working tree never written, staging (git add) in the primary
checkout staying a landing-gate violation. Before the invocation the run's own
duties hold as policy: the pre-landing gate set (the PII check + hygiene scan
(exit 0 required), the peer-byte guard, and the gmail-author check) and any
rebase onto a moved default tip run per the landing step's implementations in
the Worktree-first standard section of agents/skills/execute-plan/SKILL.md, and
a sanctioned rebase ends by refreshing the recorded base pin per the standard's
refresh duty (the manifest's run_base and the claim's `base:` line) so the
helper's parentage base arguments find no mismatch; every landing shell pipeline
checks and propagates rebase and merge exit codes, and a masked failure aborts
the landing before any staging or ref move. The landing routes solely on the
helper's outcome contract (the final `OUTCOME:` line per
scripts/OUTCOME_CONTRACT.md): `OUTCOME: pass` keeps the landing (a kept
post-landing origin divergence carries only the gate's informational note:
the divergence predates the landing, with no operator follow-up); `OUTCOME: fail` takes the deferred-landing path
keeping the branch and worktree, writing the deferred-landing record and note
per the deferred-landing record duty below; `OUTCOME: indeterminate` and
`OUTCOME: tool_error` stop and report, never read as pass or refusal, and a run
with no final `OUTCOME:` line is tool error under the contract and stops and
reports the same way; the rollback-by-inverse-compare-and-swap posture stays the
recorded operation's sanctioned shape per the execute-plan skill's landing
critical section, never an improvised ref edit. The landing never copies bytes
into, stages into, or commits in the primary checkout; a landing of the
primary-checkout class (the squash executing in the base branch's primary
checkout: archive riders, ad-hoc maintenance landings, manual recoveries) is
never a hand-composed sequence; under the acquired merge lock it runs
`scripts/land_squash.sh land --branch <branch> --expected-tip <sha> --message <text>`
(the lock-bound helper owning that class per the execute-plan skill's
primary-checkout landing duty; the optional `--expected-base <sha>` passthrough
carries the recorded base pin to the pre-swap leg), and the pre-lock
`scripts/land_squash.sh probe --branch <branch>` duty gates lock acquisition.
The `--message` text's subject line follows the landing-claim grammar pinned
by the Worktree-first standard's landing step, in both landing modes' helper
invocations. On a landing kept after the helper's outcome contract, the post-landing sweep
runs per the landing closeout's post-landing sweep implementation in the
Worktree-first standard section of agents/skills/execute-plan/SKILL.md; on the
rollback arm the sweep does not run and the deferred-landing record carries the
finding duty. On the deferred-landing path
the run worktree stays on the run branch and both branch and worktree are kept;
on the pass path the branch deletion follows the closeout's deletion gating (a
branch checked out in the run worktree cannot be deleted, so the worktree leaves
the branch or is removed first) as critical-section-exit cleanup. A residual lane that must stage paths in the
primary checkout first runs the pre-stage freshness gate
(`python3 scripts/prestage_freshness_gate.py check --repo <primary-checkout> --fresh-list <the session's fresh-write list> -- <candidate paths>`)
verifying each candidate path's disk bytes equal HEAD or are session-owned
fresh writes; read through the outcome contract's final `OUTCOME:` line:
exit 1 (`OUTCOME: fail`) refuses the staging naming the paths and takes
the deferred-landing path, never stages; exit 2 (`OUTCOME: indeterminate`)
and exit 3 (`OUTCOME: tool_error`) stop and report, never read as pass or
refusal, and stage nothing; exit 0 (`OUTCOME: pass`)
stages only the verified paths; a run with no final `OUTCOME:` line is tool
error under the contract and stages nothing. Then (after the landing and before the branch deletion)
run the dirt regression gate against the run's merge base over the arm's own
working tree (the run worktree's own working tree)
(`python3 scripts/dirt_regression_gate.py --base <merge-base-sha> -- "${DIRT_PATHS[@]}"`;
the `<merge-base-sha>` placeholder is replaced with the run's actual merge
base before execution; `DIRT_PATHS` is safely populated as a Bash array with
one element per working-tree modified file plus every file the dirt
backup/restore touched when a restore ran; the `"${DIRT_PATHS[@]}"` expansion
passes each path as one literal quoted argument and constructing or
evaluating shell command text from raw path bytes is prohibited;
`--base` without path operands is a command-construction usage error): a dirt regression finding is remedied in place (the
regressed file is restored from HEAD and the merge summary carries one line
per restored file naming the regression); it is NOT a gate failure and does
not trigger the release/keep-branch abort; the gate reports the outcome contract's four outcomes (scripts/OUTCOME_CONTRACT.md, final `OUTCOME:` line): a finding is fail (remedy in place as above); an indeterminate or tool-error result stops the merge step (do not delete the branch, do not report the merge complete; take the gate-failure release arm: release via merge-release-repo with the acquired exports, keep the branch, and report): report the gate's lines and re-derive the landed tree from disk outside the held critical section before retrying; only a determinate pass or fail verdict proceeds to branch deletion; a run that emits no final `OUTCOME:` line is tool error under the contract and stops the merge step the same way; then verify the landed commit on the repository's default branch:
run the landed-commit test for the run's archived plan path
(`git cat-file -e refs/heads/<default>:<archived-plan-path>`); when it passes,
the landing is confirmed and the critical section continues to the branch
deletion and release; when it fails (a deferred, refused, or silently dropped
squash), clean any conflicted squash state with `git reset --merge` first, then
write the deferred-landing record and note (the deferred-landing record duty
below) before releasing the lock via `merge-release-repo` with the acquired
exports, keep the branch and any worktree, and end the session chaining
nothing; on the pass path, the branch deletion; any gate failure releases via
merge-release-repo with the acquired exports, keeps the branch, and reports;
release the lock only after the branch is deleted. After the release, reconcile live checkouts of the base branch per the post-landing reconciliation implementation in the Worktree-first standard section of agents/skills/execute-plan/SKILL.md (fast-forward plus verified completion, named-block refusal, stale-witness restore-and-record); the landing closeout ends only when that reconciliation is verified or a named block is recorded. The closeout records the reconcile receipt (the invocation's exit code and its row summary in the run's session notes); a skipped or failed reconcile fails the closeout. If any release
attempt itself fails (the gate-failure release included, not only the final
post-deletion release; read through the outcome contract: `OUTCOME: fail` and
`OUTCOME: tool_error` both take this fallback, and a release run with no
final `OUTCOME:` line is tool error under it), re-export the lock variables
from your acquire output
and retry that release once, then explicitly report the stranded lock label
(execution-final-merge) and MERGE_LOCK_DIR. If the
execution ran in an ad-hoc worktree, then before removing that worktree, move
every review staging doc and .stats.json sidecar the run wrote under the
worktree's .ai-playbook/reviews/ into the primary checkout's .ai-playbook/reviews/ (.ai-playbook/reviews/
is gitignored, so reviews never ride the squash merge) and verify them present in
the primary checkout; remove the worktree only after that verification, keeping
it and reporting if any file cannot be moved or verified. Once the
worktree is removed and the landing is visible at the primary checkout,
the run releases its own execution claim through the EXECUTION CLAIM
duty's delete arm, and may then run the claim gateway's sweep arm
(`bash scripts/execution_claim.sh sweep --session <id>`) to clear peer
claims the same closeout shape has already spent. Deferred-landing
record duty (applying on the gate-failure path, the verification-failure path,
and the lock-acquire timeout path alike): write `pending_landing` with
"lane": "execute" filled from the run's own facts (the plan path, the branch
name, the branch tip sha, the worktree path when one exists, the archived plan
path as landed_path, the recorded-at timestamp, and the deferral reason in
note) as one targeted state edit addressed to the primary checkout's
`.ai-playbook/scheduler-state.json` (the recorded primary checkout root in an
explicit-rooted form, the claim duty's precedent; a cwd-relative edit from an
ad-hoc worktree would write a per-worktree gitignored file no reader reads)
immediately when the deferral is known, before releasing the lock and before
any report; the occupied-field rule applies: a write finding the field already set
never overwrites an existing record (it writes the per-run note only and reports the collision), and a
record-write loss or undetermined outcome still writes the per-run note (the
note is the recovery input, its write is unconditional on the record write's
outcome); then write the per-run repo-keyed memory note named
`pending-landing-<plan-slug>` with body {"lane": "execute",
"repo": "<repository root>", "plan": "<plan path>", "branch": "<branch name>",
"branch_tip": "<tip sha or null>", "worktree": "<worktree path or null>",
"landed_path": "<archived plan path>", "attempts": 0} in the agent's persistent
memory index (state-first ordering: the state write precedes the note). Never
push.

SUCCESSOR DISPATCH, after the final squash merge passes and before ending the session: chain the next execution child by recycling your own spawner record. Read the primary checkout's `.ai-playbook/scheduler-state.json` (explicit-rooted form per the claim duty's precedent; a cwd-relative edit from the ad-hoc worktree would write a per-worktree gitignored file no reader reads) and the open top-level plans. Chain nothing, and end, when any of these holds: no open plan remains, or open plans remain but the D1-rule selection, after the dependency-blocked and external-gate skips, yields no target; the state file's rolling rate pressure (the count of `rate_limited_events` entries within the last 24 hours, the field the scheduler's D1 deferral reads), computed from the state file already read, is at or above 3, so the successor target waits for the next scheduler turn's pressure-gated reader/D1 path; the state file it already read carries a standing `survey_only` flag (the Mode enforcement paragraph's operator lane stop binds this successor duty beside its per-lane reads), so the successor target waits for the next scheduler turn's reader path, which consults the same flag; any other children[] entry whose lane hold is still active under the scheduler's release rules (outcome not `failed` and completion evidence absent within the outcome horizon, with the Step 2 evidenced-stopped early release applying: another actor holds or awaits the record); the automation listing shows an armed child payload for this repository; or this run did not end in a clean closeout; or its own landing is not verified on the default branch (the same landed-commit test the final-merge paragraph runs; under this conjunct the child records the deferred-landing record and note per the final-merge paragraph's duty and ends); or an outstanding pending_landing record sits in the state file or any surviving repo-matching per-run landing note for any lane survives, so the fleet gate holds at the child-side chain site too (the note half is worded as a paraphrase on purpose so the per-run note literal stays counted at exactly its two duty sites). Otherwise select the successor target by the D1 rule: memory dependency-chain order when available; otherwise the oldest open plan that passes the certification oracle, run once per open top-level plan as Step 1 does; otherwise the oldest open plan, whose re-certification the PRE-STEP performs; skip plans the memory index marks dependency-blocked whose blocker is still an open plan or a deferred plan anywhere under the resolved plans directory; also skip a plan named by a live `parked_dependencies` entry (any entry not yet cleared by the State file field paragraph's clear arms; a finishing child's successor selection never chains a plan a live ledger entry blocks); when the successor duty prepends the next target to `execution_queue` in the same targeted edit family as its successor dispatch, it prepends only when the target is not already queued; also skip open top-level plans whose header block (the title line through the first `## ` heading, nothing beyond it; when the plan carries no `## ` heading at all, the header block extends to the end of the file) carries an `External gate:` line that is unsatisfied per the same rule: a gate is satisfied when its value's first whitespace-delimited token is a `YYYY-MM-DD` date that has passed (date form), or when some open top-level plan or open backlog item other than the declaring plan carries the slug (the value's first token, kebab-case) in its file basename as a hyphen-bounded segment (slug form; the match set is the open top-level plans, never the completed/ or deferred/ subdirectories, and the open backlog items at the backlog top level, never its parked/completed subdirectories; basename matching only, no body-text matching), a first token that is neither form (like the empty value) reads as unsatisfied, and a plan whose gate has become satisfied is selected again by the normal rules without human action. Fix the fire time per the quota leg (run scripts/quota_window_probe.py, using its --fire-at mode with --need-minutes set to this lane's estimate and --straddle-minutes 60 for this execution lane; the runtime-fit, deferred-window, peak-pricing, and floor rules all apply; at least 5 minutes out; the overlay's starvation exception beats pricing, never fit). Primitive precheck before leg selection (the child-side twin of the overlay's ladder precheck): before either mutating leg, assert the session actually owns the primitive that leg needs (the update primitive for the reshape leg; the delete plus create primitives for the delete-plus-create fallback leg); on absence route to the next leg or the park path (the both-legs-fail branch below) WITHOUT burning listings on statically absent primitives. Park-first chaining (added 2026-09-24, P54): before the reshape/create attempt, record the park decision-first: set "pending_dispatch" (kind execute, the selected successor target, filled per the pending_dispatch field's shape) plus the assembled successor payload copy under the dispatch kind's identity-bound payload filename (derived per the pending_rearm field paragraph) in one targeted state edit (the park-path pairing rule), so the primitive phase is a purely mechanical emission of an already-recorded decision; when the dispatch then succeeds, consume the park by clearing "pending_dispatch" in the same targeted edit family as the children[] record write; on the failure branches the park stays standing and the existing both-legs-fail write below becomes its consume-or-keep tail (the state already carries the park; the branch's write finds the field set and keeps it, writing the memory note as before). Then reshape your own spawner record into the successor one-shot with one update-primitive call: recurring false, the successor fire time, this payload's body with {some_plan} filled with the successor plan path and {REPO_ROOT} filled, enabled true. HOST CAVEAT: any recycling update whose echoed record is not verifiably the intended form (enabled true, recurring false, a future nextRunAt matching the successor fire time, confirmed by a listing) is treated as a refusal; when that update is refused, or its echoed record is unverifiable, fall back to deleting your own spawner record whatever its current form (child one-shot, lingered completed, or the re-armed parent this session created) and creating the successor one-shot per the overlay's clocked child shape (agents/skills/maintenance/zcode.md "Scheduling primitives": one-shot delayMinutes schedule, recurring false), carrying the same payload and fire time; this fallback leg is part of the single successor-dispatch duty the opening guard authorizes; when both legs fail, list at most once before the re-create: when an ENABLED automation with the recognition title and prompt opening (the literals defined in agents/skills/maintenance/zcode.md "Recurring automation recipe") whose prompt also contains the resolved repository root is present, adopt its id into "parent_automation_id" (targeted field edit) and end without creating; only when the listing shows no such match, re-create the parent per the recipe in agents/skills/maintenance/zcode.md "Recurring automation recipe" and update "parent_automation_id" (targeted field edit) so the loop stays armed; only when that re-create is also refused, write "pending_dispatch" (kind execute, the D1-selected successor target this paragraph selected, filled per the pending_dispatch field's shape) plus the assembled successor payload copy under the dispatch kind's identity-bound payload filename (derived per the pending_rearm field paragraph) in the same targeted state edit (the park-path pairing rule: intent record and payload copy are one paired write, always before the memory note), then write a memory note {"type": "successor-chain-failed", "repo": "<repository root>", "target": "<successor plan path>"} in the agent's persistent memory index and end; the memory note no longer stands alone: on this path the loop may still stay dark until an outside actor re-arms it and no watchdog covers it, but the parked "pending_dispatch" keeps the target mechanically dispatchable (the next scheduler turn's Step 1 reader dispatches it per its kind, the tmp file being the payload's human-readable copy, and the dispatched child's re-arm duty restores the parent as its FIRST ACTION); the note is still surfaced by a human read-back of the memory index, and by the next scheduler turn's Step 1 survey read-back when the loop has been re-armed by some actor. Loop guard: if you have listed twice without a mutating step between listings, stop touching automation primitives and end; the next scheduler turn re-decides the target. On success, record the successor in the state file children[] as kind execute, pending, the same automation id when the reshape leg ran, otherwise the fresh id of the created successor, with the new target, requested_at carrying the originally requested fire time, fire_at, and dispatch_plan_sha (the successor plan file's sha256 recorded at dispatch time, so the stand-down carve-out can qualify a successor-dispatched child), all as one targeted field edit, recording quota_status deferred-peak when a pricing deferral moved the fire time. Dispatch exactly one successor per completed child (a failed chain counts as the one attempt); never chain after a stood-down or failed run. Never push.

CLOSING PARK DISCHARGE DUTY, before ending: read the primary checkout's `.ai-playbook/scheduler-state.json` (explicit-rooted form per the claim duty's precedent); when pending_rearm or pending_dispatch is set and this session passes the able-session precheck (the child-side primitive precheck discipline the re-arm duty above applies), discharge the parked intents in this same session before ending, guard-bound: re-arm per the recipe from the paired payload copy (consuming it after the state edit survives) and/or dispatch the retained target per its kind through the normal path (the reader's validation arms and gates apply), then clear the discharged field in one targeted state edit; on primitive absence, leave the park standing (the existing park-and-stop behavior) and end.

FINAL STEP, after the report: end this run after the report; the next scheduled payload
starts in a fresh, compacted context, because the dispatch boundary is the compaction boundary
and compaction itself is operator-only.
</prompt>

{execution_time}: at
{some_plan}: <plan-path-under-docs/history/plans>
```

RE-ARM FIRST ACTION: the paragraph's canonical copy lives in agents/skills/maintenance/duties-core.md (the byte-identical shared duty set); load that file and execute its FIRST ACTION paragraph as the blueprint's first action, before any gate or phase.
