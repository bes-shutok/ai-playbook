# Plan: Done final-only; learn capture at intermediate boundaries

Backlog origin: docs/history/backlog/2026-10-17-execute-plan-step-3-4-iteration-done-scoping.md
Driving force: efficiency + token-usage
Plan review record: the staging series {reviews_dir}/2026-10-18-plan-review-done-final-only-learn-intermediate[-p<identity-token>]-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 4h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-18-done-final-only-learn-intermediate.md (session sess_1b0f1009-f577-46d2-b73f-08f889226ad2)

Design input in prose: the open PLAN-PROMPTS.md entry `execute-plan-step-3-4-primary-cadence` (added 2026-10-17) asked for Step 3.4 to mirror Step 1.4's primary-placement cadence while preserving worktree per-iteration behavior; this plan's scope subsumes that entry and supersedes its worktree-preservation arm by operator decision (see Assumptions). Task 5 prunes the entry with receipt and deletes the origin row per the covered-row rule, this plan being the witness.

## Terms

- Intermediate boundary: a per-task (execute-plan Step 1.4), per-review-fix-iteration (execute-plan Step 3.4), or per-round (review-loop step 4) work boundary inside a live run.
- Light boundary: the intermediate boundary procedure this plan lands: the parent makes the plain path-limited task commit, then runs learn, then mirrors new records; no done runner, no lock, no landing sweep, no docs-branch sync, no finalize.
- Full done closeout: the done skill's complete sequence (setup, learn, commit run with the one landing sweep and the docs-branch sync, side-repo walk, finalize, report), run once per run at the final closeout, before the squash landing.
- Landing sweep: the single `done_sweep_gates.sh landing` run that gates the staged set before the closeout's landing commit.
- Docs-branch sync: the orphan-branch publication of gitignored review and metrics docs (`docs_branch_sync.sh`), run inside the closeout's commit stage.
- Squash landing: the transfer-out of a run worktree's branch onto the base branch as one squash commit, gated by the closeout migration checks.
- Side-repo walk: the closeout's per-repository commit pass over the skills and shared-docs repositories.
- Phase 5: execute-plan's closeout phase (archive verification, closeout gate, transfer-out, session tmp cleanup).
- Session logs: a run's session directory under `{tmp_dir}/execute-plan/<plan-slug>/`: the manifest, task implement and review logs, and telemetry.
- Review-record mirror: the boundary's plain file copy of new review staging docs, their .stats.json sidecars, and new session logs from the run worktree to the primary checkout's reviews and tmp homes; not a gate, never blocking.
- Project-backlog capture arm: the new learn step that reviews the session for project issues worth fixing and files backlog rows routed by related project.
- Related project: the repository a captured issue belongs to; the routing home for its backlog row (see Step 1.9).
- Investigate anchoring: invoking the investigate skill with the just-created backlog row(s) as its input item, inside the same learn run.
- Boundary manifest row: the session-manifest line recording one boundary's completion, renamed from `done_fast_path:` to `task_boundary:`.
- skills_repo_path: the user facts key that resolves the skills repository checkout; script invocations resolve through it.
- Primary resolution, worktrees resolution: the two placements of the project worktree policy owned by the Worktree-first standard's policy paragraph in agents/skills/execute-plan/SKILL.md.
- Backlog capture: the item shape owned by receiving-review's "Backlog capture for valid findings not fixed in scope" section.
- done runner: scripts/done_run.sh (setup, commit, finalize subcommands) in the skills repository.
- done ceremony: the done skill's full sequence; this plan removes its intermediate-boundary invocations and keeps the final closeout's.

## Design Invariants (CR Guard)

- The final-closeout target state landed by docs/history/plans/completed/2026-10-11-done-target-state-learn-commit-closeout.md (commit 04bd9c80a) is preserved: one landing sweep, the docs-branch sync, the single landing commit, the side-repo walk, and finalize all stay in the done sequence. This plan removes only intermediate invocations of that sequence; the validation block's preservation greps pin the frozen roster.
- The review-iteration boundary keeps its commit and verification duties (the origin entry's rejected alternative "remove Step 3.4's done invocation and batch review fixes until loop exit" stays rejected; only the done ceremony around the commit is removed).
- No new gate, validator, lock, or refusal class at intermediate boundaries (repository Machinery admission protocol): the boundary adds a plain commit, a learn invocation, and a plain file copy, and removes machinery.
- Workers and subagents still never commit; the parent owns every boundary commit (execute-plan worker contract, unchanged).

## Why

The done ceremony (lock acquire, run marker and manifest, landing sweep, docs-branch deferral machinery, finalize) runs at every intermediate boundary of an execute-plan or review-loop run, several times per run, while its gates pay off once per landing. The operator set the target state directly on 2026-10-18: done runs once at the final closeout before the squash landing; intermediate boundaries commit plainly and capture through learn. The primary-checkout placement already runs this shape (the placement doctrine landed at commit 0e8815007); this plan makes it the only cadence and moves the boundary's capture duties into learn, which gains related-project backlog filing and investigate routing.

## Gist & Examples

TLDR: intermediate boundaries commit plainly and capture through an enhanced learn while done becomes the once-per-run final closeout, cutting per-task ceremony cost for efficiency and token usage.

Before: after each task, the execute-plan parent runs the full done ceremony in the run worktree: `done_run.sh setup` (done lock, run marker, manifest, residue sweep), learn, `done_run.sh commit` (the landing sweep over the staged set, the review-and-session-log migration), `done_run.sh finalize` (manifest, checkpoint, lock release). The same sequence repeats after every review-fix iteration and every review-loop round, and the whole closeout runs again at Phase 5.

After: the parent creates the plan's specified task commit by explicit pathspec over the task's accepted paths, the captured backlog items, and the previous boundary's learn-authored corpus paths. It then runs learn, which captures lessons, files related-project backlog rows for issues worth fixing, and calls investigate over the rows it created. It copies the boundary's new review staging docs and session logs to the primary checkout homes and records one `task_boundary:` manifest row. At Phase 5 the full done closeout runs once: the landing sweep gates the whole branch delta, the docs-branch sync publishes the run's review docs, and the run lands through the squash-landing path unchanged.

## Outcome

A plan run's intermediate boundaries stop invoking the done ceremony; capture moves to an enhanced learn; the final closeout is unchanged.

- Per task and per review iteration, the parent commits plainly and runs learn; no lock, sweep, manifest, or finalize runs mid-run, under either placement.
- learn files related-project backlog rows for issues worth fixing and routes them through investigate in the same boundary, so follow-up work survives the run without a done run per task.
- Review staging docs and session logs survive a mid-run worktree loss through the per-boundary mirror to the primary checkout homes (the 2026-10-11 teardown incidents lost such records twice).
- The final closeout keeps the full done ceremony: one landing sweep, the docs-branch sync, the side-repo walk, finalize, and the report.

Gate delta: net removal, no addition. Removed from the intermediate-boundary surface, each with its new home: the per-task done lock acquire and release (nothing; worktrees are per-run isolated, and the skills-repo index race keeps learn's own retry), the run-marker and run-manifest writes (the boundary manifest row), the intermediate landing-sweep run (the final closeout's one sweep over the whole branch delta), the per-round docs-branch sync (the exit closeout's sync), the per-boundary review-artifact migration (split: review docs and session logs move to the review-record mirror), the review-candidate classification, worktree residue sweep, stale-checkout adjudication, cached-diff, staged-scope and foreign-dirt guards, dangling-change stop, review-thread closure, plans-root liveness, and checkpoint refresh (all deferred to the final closeout, which keeps them unchanged), the per-landing owned-commits ledger append for learn receipts (the `task_boundary:` row records the receipts), and the `--boundary-class per-task` routing in skill text (the runner keeps the option with no skill-text callers; its retirement rides the Task 5 residue row). Added: none. The review-record mirror is a plain file copy, not a gate, priced by the witnessed 2026-10-11 worktree-teardown record losses it prevents; the learn backlog arm and the investigate invocation reuse existing machinery (receiving-review's Backlog capture shape, the investigate skill's own contract) and add no refusal class, no pause condition, and no checked set. Accepted residual risks, named: mid-run staging, revert, and dangling-dirt defect classes now surface once at the final closeout instead of per boundary (report-only residue notes on the boundary row keep attribution); the removed cross-session serialization leaves the project lessons corpus with a lost-update window at overlapping learn runs, mitigated by a learn re-read-before-write guidance sentence, not a gate; the per-boundary lesson-scope audit is accepted as lost for intermediate corpus deltas (learn's placement-time duplicate checks remain the first layer, and the final closeout's audit is unchanged).

## Assumptions

- assume the boundary's plain commit keeps the plan's per-task commit convention (explicit pathspec, why-first message, plan-specified pre-commit checks); basis: operator boundary-shape decision 2026-10-18, and the commit lines already present in plan task checklists.
- assume learn's project-backlog arm routes each row to the related project: when the related project is the current run checkout's repository (or is otherwise present in the current worktree), the row lands in that checkout's resolved backlog directory; otherwise learn files the row on the current branch of the corresponding project's own checkout, in its resolved backlog directory; dedupe runs against the destination home; basis: operator correction 2026-10-18 (mid-round chat receipt), refining the same-day direction to create backlogs "on the same worktree".
- assume investigate runs unchanged whenever the learn run created new rows (its Stage 0 survey, verdict routing, entry emission, and its own entry commit all apply as written); basis: explicit operator direction 2026-10-18.
- assume execute-plan Step 3.4 and review-loop per-round boundaries get the same light shape as Step 1.4; basis: the operator's "all intermediate steps and subagent runs", 2026-10-18.
- assume the final closeout sequence is byte-preserved in its gate roster; basis: the operator's "only as the last step" plus the landed 2026-10-11 closeout target state.
- assume the capture arms live in learn (consumer-agnostic), so standalone learn and the maintenance harvest duty gain them too; basis: skill layering, the router keeps step text in modules.
- assume the enhanced learn run at every boundary does not defer to end-of-run under either placement (it replaces the per-task learn the done boundary used to run); basis: operator decision 2026-10-18.
- assume the investigate entry commit is a sanctioned second commit at a boundary (alongside learn's own skills-repo commits), recorded on the boundary manifest row; basis: investigate's unchanged same-turn commit contract.
- Origin rewrite: the origin row asks Step 3.4 to preserve the documented per-iteration worktree behavior; the operator's 2026-10-18 boundary-shape decision supersedes that acceptance, and this plan rewrites it to the light-boundary form before authoring tasks (recorded here per the plans skill's origin-acceptance rewrite rule).
Decision points requiring a grill: Boundary shape is learn capture plus a plain parent commit at every intermediate boundary with the full done sequence once at the final closeout; user decision 2026-10-18 structured-question receipt; affects execute-plan Step 1.4 and Step 3.4, review-loop round cadence, and done integration text; Mid-run review-record protection is a plain per-boundary copy to the primary reviews home; user decision 2026-10-18 structured-question receipt; affects the boundary procedure and review-loop round steps; Script relocation is scoped to resolution text plus one follow-up backlog row after the repo-first discovery; operator decision 2026-10-18 chat confirmation; affects Task 4; Backlog rows route to the related project's repository, kept in the current worktree when the project is present there and otherwise filed on the current branch of the corresponding project's checkout; operator correction 2026-10-18 mid-round chat receipt; affects learn Step 1.9 and the Terms entry.

## Standing constraints

- Tool-agnostic wording: describe behaviors by intent; no tool names, no agent-type names (repository Skill Design Guidelines).
- Anti-growth: operative text cites incidents in at most one line; the boundary procedure is stated once in execute-plan and referenced, never restated, by review-loop (repository anti-growth rules).
- Machinery admission: removals need no admission pricing; the two additions (mirror copy, learn arm) are non-gating and witness-priced in the Gate delta line.
- Every consumer edit updates its Integration Points in both directions (repository Skill Design Guidelines); where a peer's own text keeps a stale back-reference (receiving-review's learn Step 1.8 mentions), the plan records it as an accepted stale reference rather than expanding scope.

## Evaluation Criteria

**Quality dimensions:**
- consistency: every touched skill describes the same light boundary; review-loop references the execute-plan procedure instead of restating it; the final-closeout roster text in done/SKILL.md is unchanged (the validation block's preservation greps pin Steps 2, 3, and 4 headings and the landing-sweep invocation).
- completeness: no stale per-task done routing remains in the spans the tasks and sweeps inventory (the case-insensitive sweeps pass and every named span's reword has a pin or an owned task item); every removed duty has a named new home (the Gate delta roster).
- portability: no tool-specific or agent-type-specific wording enters the edited text (repository hygiene scan passes).

**Done when:**
- all files in the Review Scope explicit list carry the new contract spans the validation block greps for.
- the validation block exits 0 in the run checkout.
- the public hygiene scan and the no-em-dash gate pass over the changed set.

**Ship when:**
- none; everything is repository-verifiable.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code (skill text):**
- `agents/skills/execute-plan/SKILL.md` (edited spans: the frontmatter description; the run-contract blockquote and summary line; Commit authorization; the anti-pattern table, all rows; the three-way gate row; Hard Gates 4, 5, 10, 17, 20, 25, and 26; the Worktree-first standard's policy paragraph's learn-once clause; the Recovery path's done launch and done-commits lines; Steps 1.2b through 1.4 including the follow-up-dispatch paragraph; Step 3.4 including its heading, its verification-gate block, and the Step 3.5 return line; the exit-criteria items; the Sub-agent execution logs duty list and log-reading sentence; the manifest-freshness and briefing-refresh clauses; the worker-loop sentence; the Intermediate-reviews paragraph; the Orchestrator Responsibilities done-boundary item; the review-iteration formula line; the staging-doc citation rule; the launch-wait line; the upkeep-edits line; the off-plan findings paragraph; the summary line's placement phrase; the Step 1.2b gate sentence; the resume line; the shared-worker contract lines; the last-done handoff; the Recovery path's per-task done launch; the Phase 5 success checklist; the Sub-Agent Launch Rules Done-boundary row; the resume and closeout-gate boundary references; the Integration Points section. All remaining sections are frozen; reject any review finding that touches them)
- `agents/skills/execute-plan/agent-logs.md` (the manifest-row paragraph and the done-anchored log-handoff sentences)
- `agents/skills/execute-plan/subagent-prompts.md` (the worker no-commit line, the done sub-agent prompt template, and the Address Review template's done handoff line)
- `agents/skills/execute-plan/runtime-contract.md` (the boundary rows of the normative sequential contract)
- `agents/skills/learn/SKILL.md` (the commit-boundary paragraph, the Step 1 dispatch range, and Integration Points)
- `agents/skills/learn/step-1-extract.md` (Step 1.8's receipt-consumer sentence, its failure-semantics sentence, and the new Step 1.9)
- `agents/skills/learn/step-2-placement.md` (the done-boundary anchor sentence only)
- `agents/skills/review-loop/SKILL.md` (the frontmatter description, the Goal cadence line, the round table and its step 4 row, the docs-branch sync step, Continuous iterations, Commits, the mutator parenthetical, the Consumes done entry, and the new Consumes `learn` entry in Integration Points)


- `agents/skills/done/SKILL.md` (the frontmatter ownership sentence, the Run placement paragraph, the boundary-class sentence, Step 1 and its notes, and Integration Points only; Steps 2 through 7 are frozen and preservation-pinned)
- `agents/skills/investigate/SKILL.md` (Integration Points only)

**Tests:**
- none; this is a prose-only change. The validation block is the check.

**New files:**
- `docs/history/backlog/2026-10-18-runtime-scripts-home-residue.md` *(new)*

**Landing bookkeeping (deletions):**
- `docs/history/backlog/2026-10-17-execute-plan-step-3-4-iteration-done-scoping.md` (origin row deleted per the covered-row rule)
- `docs/history/backlog/PLAN-PROMPTS.md` (the `execute-plan-step-3-4-primary-cadence` entry pruned with receipt)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it removes a stale per-task-done reference the sweeps missed under agents/skills/, closes an Integration Point this contract change invalidates in a touched skill's sibling, or contradicts a contract this plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/` (the done runner, sweep gates, and every validator: unchanged; the runner's per-task class loses its skill-text callers, and its retirement is tracked on the Task 5 residue row)
- `agents/skills/receiving-review/SKILL.md` (the Backlog capture shape provider: consumed as-is; its learn Step 1.8 mentions are accepted stale references recorded here, re-routed by a later receiving-review pass)
- `agents/skills/plans/SKILL.md` (its done invocation is already the authoring closeout's last step; unchanged)
- any path outside the repository, including the deployed runtime homes (the follow-up backlog row owns both surfaces: the runtime scripts home and the vendored skill-text twins)

## Validation Commands

RED-today record (measured 2026-10-18 against the pre-change tree): every sweep below fired (boundary-class: 4 matches across 2 skills; done sub-agent: 5 lines including the capitalized verification-gate heading; done_fast_path: 1; parent-executed done: 2; via done: 1; after done succeeds: 1; done commit: 8 lines) and every new-contract pin returned 0 hits; the preservation pins were green; the unscoped em-dash gate measured red today on one pre-existing landed line, so the block scopes it to the Review Scope paths (scoped added-lines measured 0 hits and exit 0 today on the five skill paths; the new row is gated by the script's path-independent file mode because added-lines aborts on untracked pathspecs). The gates flip green exactly when the tasks land. The sweeps target paths under `agents/skills/` plus the two landing-bookkeeping paths only; the plan file lives under `docs/history/plans/` and is never in a sweep surface, so its embedded pattern literals cannot self-match.

```bash
cd "$(git rev-parse --show-toplevel)" || exit 1
fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }

# Positive spans: one dedicated grep per guarded obligation, pinned to its owning file.
grep -Fq 'Light boundary (every task and review iteration)' agents/skills/execute-plan/SKILL.md || fail 'Step 1.4 retitle'
grep -Fq 'task_boundary:' agents/skills/execute-plan/agent-logs.md || fail 'manifest row rename'
grep -Fq 'orchestrator runs the boundary after verification' agents/skills/execute-plan/subagent-prompts.md || fail 'worker contract span'
grep -Fq 'parent-owned light boundary' agents/skills/execute-plan/runtime-contract.md || fail 'runtime contract boundary row'
grep -Fq '## Step 1.9: Project issue backlog capture' agents/skills/learn/step-1-extract.md || fail 'learn capture arm'
grep -Fq '### With `investigate` skill' agents/skills/learn/SKILL.md || fail 'learn investigate integration'
grep -Fq '(with Steps 1.5 through 1.9)' agents/skills/learn/SKILL.md || fail 'learn router range'
grep -Fq 'plain commit, then learn, then the record mirror' agents/skills/review-loop/SKILL.md || fail 'review-loop round row'
grep -Fq 'runs once per run at the final closeout' agents/skills/done/SKILL.md || fail 'done universal cadence span'
grep -Fq '### With `learn` skill' agents/skills/investigate/SKILL.md || fail 'investigate learn consumer'
test -f docs/history/backlog/2026-10-18-runtime-scripts-home-residue.md || fail 'follow-up backlog row'

# Landing bookkeeping: the subsumed entry is pruned and the origin row deleted.
if grep -Fq '2026-10-17-execute-plan-step-3-4-iteration-done-scoping' docs/history/backlog/PLAN-PROMPTS.md; then fail 'origin entry not pruned'; fi
if [ -f docs/history/backlog/2026-10-17-execute-plan-step-3-4-iteration-done-scoping.md ]; then fail 'origin row not deleted'; fi

# Preservation pins over the frozen closeout roster (green before and after; damage flips them red).
grep -Fq '## Step 2: Preserve Gitignored Docs and Instructions' agents/skills/done/SKILL.md || fail 'closeout Step 2 missing'
grep -Fq '## Step 3: Commit Uncommitted Changes' agents/skills/done/SKILL.md || fail 'closeout Step 3 missing'
grep -Fq '## Step 4: Skills repo walk' agents/skills/done/SKILL.md || fail 'closeout Step 4 missing'
grep -Fq 'done_sweep_gates.sh landing' agents/skills/done/SKILL.md || fail 'closeout landing sweep missing'
grep -Fq 'done_run.sh setup' agents/skills/done/SKILL.md || fail 'closeout runner sequence missing'

# Forbidden stale routing: case-insensitive, three-way exit split (0 forbidden, 1 clean, >=2 tool error).
sweep() {
  pattern="$1"; shift
  out="$(grep -rniE "$pattern" "$@" 2>/dev/null)"; rc=$?
  if [ "$rc" -eq 0 ]; then printf 'FORBIDDEN MATCH (%s):\n%s\n' "$pattern" "$out" >&2; exit 1; fi
  if [ "$rc" -ge 2 ]; then printf 'SWEEP ERROR rc=%s (%s)\n' "$rc" "$pattern" >&2; exit 1; fi
}
sweep 'boundary-class per-tas[k]' agents/skills/execute-plan agents/skills/review-loop agents/skills/done
sweep 'done_fast_pat[h]' agents/skills/execute-plan
sweep '[d]one sub-agent' agents/skills/execute-plan agents/skills/review-loop
sweep 'parent-executed done' agents/skills/execute-plan agents/skills/done
sweep 'via .done.' agents/skills/review-loop
sweep 'after .done. succeeds' agents/skills/review-loop
sweep 'done commi[t]' agents/skills/execute-plan

# Gates over the changed set (branch-based, run before the landing).
bash scripts/check-no-em-dash.sh added-lines --base origin/main -- agents/skills/execute-plan agents/skills/learn agents/skills/review-loop agents/skills/done agents/skills/investigate || fail 'em-dash gate'
bash scripts/check-no-em-dash.sh file docs/history/backlog/2026-10-18-runtime-scripts-home-residue.md || fail 'em-dash gate (new row)'
bash scripts/scan-public-hygiene.sh --changed-from origin/main || fail 'hygiene scan'
echo 'VALIDATION PASS'
```

### Task 1: execute-plan light boundary

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/agent-logs.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/runtime-contract.md`

- [ ] Step 1.4 is retitled "Light boundary (every task and review iteration)" and its body states the four legs in order: plain commit, learn, record mirror, manifest row. [class: IMPLEMENTATION_REQUIRED]
- [ ] Boundary leg 1 witness: given a completed task whose accepted paths are known, expects one commit by explicit pathspec carrying exactly those paths, the captured backlog items, and the previous boundary's learn-authored corpus paths, with the why-first message; a gitignored path among the candidates is reported and never staged; no done runner, no lock, no sweep, no finalize. [class: IMPLEMENTATION_REQUIRED]
- [ ] Boundary leg 2 witness: given the boundary's implement and review logs, expects a learn run that captures lessons, files related-project backlog rows per its Step 1.9, and invokes investigate over the rows it created. [class: IMPLEMENTATION_REQUIRED]
- [ ] Boundary leg 3 witness: given new review staging docs, .stats.json sidecars, and new session logs at the boundary, expects copies under the primary checkout's reviews and tmp homes; a copy error is reported and never blocks the boundary. [class: IMPLEMENTATION_REQUIRED]
- [ ] Boundary leg 4 witness: given the completed boundary, expects exactly one `task_boundary:` manifest row naming the commit sha, the verification results, the created backlog paths, the learn and investigate commit receipts, and any changed paths outside the task's Files list (report-only). [class: IMPLEMENTATION_REQUIRED]
- [ ] The placement-conditional sentence (primary resolution defers learn to end-of-run) is deleted from Step 1.4, and the policy paragraph's learn-once clause plus the verification gate's deferred-learn parenthetical are reworded: learn runs at every boundary under both placements. [class: IMPLEMENTATION_REQUIRED]
- [ ] Step 3.4 keeps its commit and verification duties and runs the same light boundary; the done sub-agent spawn and its `--boundary-class per-task` declaration are removed from the step text and from the subagent prompt template; the review-round log handoff (agent-logs.md) is unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Update the Commit authorization paragraph: the Step 1.4 and Step 3.4 light boundaries commit without a separate commit prompt; the sentence naming the done sub-agent is deleted. [class: IMPLEMENTATION_REQUIRED]
- [ ] Reword Hard Gate 25: the light boundary's commit does not run while blocking findings are unresolved or the off-plan backlog items are uncaptured; title "Intermediate review before the boundary commit". [class: IMPLEMENTATION_REQUIRED]
- [ ] The exit-criteria item is reworded to the boundary commit, and its re-run-or-fix and do-not-open guards survive with boundary wording; the accounting item's "re-runs the done boundary" remedy is reworded to the light boundary. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run this task's pin grep and the execute-plan-span checks; expect the retitle pin green and remaining sweep matches to belong only to Task 2 and Task 4 spans (interim scoping per the plans skill's stage-scoped rule). [class: REPOSITORY_TEST]
- [ ] Commit: `skills: execute-plan intermediate boundaries commit plainly and capture through learn` [class: IMPLEMENTATION_REQUIRED]


### Task 2: execute-plan stale-span sweep and siblings

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/agent-logs.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/runtime-contract.md`

- [ ] Update the three named anti-pattern rows ("Skip Step 1.4 because code already works"; "Parent runs git commit or learn between tasks outside the boundary"; "Address review fixes then start next review round without done") to the light-boundary equivalents. [class: IMPLEMENTATION_REQUIRED]
- [ ] Catch-all, part 1: reword every remaining anti-pattern table row that names mid-run done (the delegation row, the checkbox-and-archive row, the every-iteration row, the Hard Gate 25 row, the widen-the-done-commit row, the two log-handoff rows, the worker-checkpoint row, the replace-all row, the Recovery row, and the skip-Phase-3 iteration row) to the light boundary. [class: IMPLEMENTATION_REQUIRED]
- [ ] Catch-all, part 2: reword the remaining done-routing spans to the light boundary, done at the final closeout only: the frontmatter description, the run-contract blockquote (keeping the one-line demotion program change 9 citation), the three-way gate row, and Hard Gates 4, 5, 10, 17, and 26. [class: IMPLEMENTATION_REQUIRED]
- [ ] Catch-all, part 3: reword the Sub-agent execution logs duty 4 and the log-reading sentence, the manifest-freshness and briefing-refresh clauses, the worker-loop sentence, Step 1.2b's launch sentence, and Step 1.3b's gate tail. [class: IMPLEMENTATION_REQUIRED]
- [ ] Catch-all, part 5: reword the Intermediate-reviews paragraph's done-commit clause, the Orchestrator Responsibilities done-boundary item, the review-iteration formula line, the staging-doc citation rule's done-prompts mention, the launch-wait line, the upkeep-edits line, and the off-plan findings paragraph's done-commit mentions. [class: IMPLEMENTATION_REQUIRED]
- [ ] Catch-all, part 4: reword or delete the follow-up-dispatch paragraph for the no-done-worker world, reword the Step 3.4 heading, its verification-gate block, and the Step 3.5 return line, the Phase 5 success checklist item, the Sub-Agent Launch Rules Done-boundary row, and the resume and closeout-gate references (the closeout gate verifies the boundary rows), and agent-logs' done-anchored log-handoff sentences. [class: IMPLEMENTATION_REQUIRED]
- [ ] Recovery path: reword the done launch and done-commits lines, and Hard Gate 20's Recovery done clause, to the light boundary (the gate joins the edited roster). [class: IMPLEMENTATION_REQUIRED]
- [ ] subagent-prompts.md Address Review template: the done handoff line becomes the boundary handoff (exits on a fresh blocking-clean digest unchanged). [class: IMPLEMENTATION_REQUIRED]
- [ ] Integration Points: rewrite the "Consumes `done` skill" entry to final-closeout-only with parent-owned plain boundary commits, reword that entry's "captured before that task's done commit" mention to the boundary commit, and add a "Consumes `learn` skill" entry mirroring learn's boundary-consumer entry. [class: IMPLEMENTATION_REQUIRED]
- [ ] agent-logs.md: rename the `done_fast_path:` manifest row to `task_boundary:` and rewrite its definition sentence (the parent's record that the task boundary completed). [class: IMPLEMENTATION_REQUIRED]
- [ ] subagent-prompts.md: the implement worker contract line becomes "Do NOT commit; the orchestrator runs the boundary after verification"; the done sub-agent prompt template is replaced by a light-boundary prompt stub or deleted with a pointer to the parent-executed procedure. [class: IMPLEMENTATION_REQUIRED]
- [ ] runtime-contract.md: the normative sequential contract's boundary rows describe the parent-owned light boundary; done appears only as the final closeout. [class: IMPLEMENTATION_REQUIRED]
- [ ] Catch-all, part 6: reword the summary line's per-task-done-boundary phrase, the Step 1.2b gate's done-boundary sentence, the resume line's per-task-done-commit phrase, the subagent shared contract's done-workflow and done-worker lines, the address-review done handoffs, and agent-logs' last-done handoff to the light boundary. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the validation block scoped to this task's files; expect this task's pins green and the execute-plan-side sweeps clean. [class: REPOSITORY_TEST]
- [ ] Commit: `skills: execute-plan stale done routing replaced by the light boundary` [class: IMPLEMENTATION_REQUIRED]

### Task 3: learn enhancement (related-project backlog arm and investigate invocation)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/learn/step-1-extract.md`
- `agents/skills/learn/SKILL.md`
- `agents/skills/learn/step-2-placement.md`

- [ ] Add `## Step 1.9: Project issue backlog capture` to step-1-extract.md after Step 1.8: while classifying session findings, also identify project issues worth fixing outside the current task's scope (defects, gaps, follow-ups the session witnessed but did not own), grouped into families by shared root area, surface, and step. [class: IMPLEMENTATION_REQUIRED]
- [ ] Step 1.9 routing: each row routes to the related project's repo; when that project is present in the current worktree the row lands in that checkout's resolved backlog directory, otherwise learn files it on the current branch of the corresponding project's own checkout; dedupe runs against the destination home. [class: IMPLEMENTATION_REQUIRED]
- [ ] Step 1.9 dedupe and create: for each family, dedupe against open items in the destination home (append new witness details and re-affirm priority on a match; re-survey immediately before create); create `YYYY-MM-DD-<slug>.md` rows with `Status: open`, a priority, and the Backlog capture shape including the `Class:` and `Origin class:` lines. [class: IMPLEMENTATION_REQUIRED]
- [ ] Step 1.9 hygiene: run the hygiene and em-dash scans over the drafted row text and apply the Step 1.7 proper-noun review before writing. [class: IMPLEMENTATION_REQUIRED]
- [ ] Investigate invocation and failure semantics: when the step created rows, invoke investigate anchored on them in the same learn run, its own contract applying unchanged (survey, routing, emission, entry commit); capture and investigate never block the enclosing boundary; failures report as a manual follow-up. [class: IMPLEMENTATION_REQUIRED]
- [ ] Off-tree rows are committed at create time: learn commits each off-tree row in its destination checkout by explicit path per its own commit discipline, records the sha on the boundary manifest row, and never leaves the row untracked residue. [class: IMPLEMENTATION_REQUIRED]
- [ ] Off-tree investigate anchoring: for off-tree rows, learn invokes investigate from the destination checkout, anchoring the row there, so the entry and its commit land in that project's own logs (foreign-data redaction applies). [class: IMPLEMENTATION_REQUIRED]
- [ ] learn/SKILL.md: rewrite the commit-boundary paragraph's ownership clause (learn commits its own skills-repo artifacts; the parent owns boundary commits; done owns the closeout) with a re-read-before-write drift-retry sentence, extend the adjacent scope sentence to the Step 1.9 arm, and update the invocation sentence (learn is invoked outside done at intermediate boundaries; done Step 1 invokes learn only at the final closeout). [class: IMPLEMENTATION_REQUIRED]
- [ ] learn/SKILL.md router and provider entries: the Step 1 dispatch range becomes "(with Steps 1.5 through 1.9)"; update "With `done` skill" and "With `receiving-review` skill" (Step 1.9 joins Step 1.8 as a Backlog-capture consumer, project-side). [class: IMPLEMENTATION_REQUIRED]
- [ ] learn/SKILL.md consumer entries: add "### With `investigate` skill" (learn is the consumer; investigate's Boundary and Hard gates are unchanged); add boundary-consumer entries for execute-plan and review-loop. [class: IMPLEMENTATION_REQUIRED]
- [ ] learn/step-1-extract.md Step 1.8: the receipt-consumer sentence names the boundary manifest row as the intermediate consumer of `committed:` receipts (the done run's ledger consumes them at the final closeout), and the failure-semantics sentence names the boundary manifest row and the closeout's Step 7 report instead of the enclosing done run. [class: IMPLEMENTATION_REQUIRED]
- [ ] learn/step-2-placement.md: reword the placement-timing clause's "before the done boundary" anchor to the owning boundary's capture (the cross-reference wiring rule itself is unchanged). [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the validation block scoped to the learn files; expect the Step 1.9, integration, and router pins green. [class: REPOSITORY_TEST]
- [ ] Commit: `skills: learn gains related-project backlog capture and investigate routing` [class: IMPLEMENTATION_REQUIRED]

### Task 4: review-loop reroute and done integration text (universal cadence)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/review-loop/SKILL.md`
- `agents/skills/done/SKILL.md`

- [ ] review-loop: the frontmatter description and the Goal cadence line become the light-boundary cycle (fresh review, fix if needed, light boundary, repeat; done at the exit closeout); the description's done mention drops with the rewrite. [class: IMPLEMENTATION_REQUIRED]
- [ ] review-loop: the round table's step 4 row becomes "light boundary (plain commit, then learn, then the record mirror; the procedure is execute-plan's Light boundary section, referenced not restated)"; "Continuous iterations" reads "after the boundary succeeds, increment review_round". [class: IMPLEMENTATION_REQUIRED]
- [ ] review-loop: the round-mutator parenthetical's "files added by learn/done" becomes the boundary mutators (learn and investigate at the boundary). [class: IMPLEMENTATION_REQUIRED]
- [ ] review-loop: "Commits" reads the boundary commits, one iteration one commit when fixes ran, with learn's skills-repo commits and the investigate entry commit as sanctioned rider commits recorded on the boundary row; the "Sync gitignored staging to docs branch via done" step becomes the per-boundary record mirror with the docs-branch sync deferred to the loop's exit closeout; "Consumes `done` skill" becomes "Consumed at the exit closeout only". [class: IMPLEMENTATION_REQUIRED]
- [ ] done/SKILL.md Run placement paragraph: state the universal cadence for all placements: intermediate boundaries commit plainly and capture through learn; the done skill runs once per run at the final closeout, before the squash landing; the primary-resolution special case dissolves into this rule; the plan-lane sentence reads: per-task plain commits and boundary learn under both placements, the full closeout once at the run's end. [class: IMPLEMENTATION_REQUIRED]
- [ ] done/SKILL.md boundary-class sentence: narrow to the final closeout (the runner's default class); the per-task class loses its skill-text callers, noted in one line without runner documentation. [class: IMPLEMENTATION_REQUIRED]
- [ ] done/SKILL.md frontmatter ownership sentence: the light boundary's parent-owned plain commit joins the exception list (learn's artifacts, docs-branch commits, release notes; now boundary commits), stated in one clause. [class: IMPLEMENTATION_REQUIRED]
- [ ] done/SKILL.md Step 1 note: the "Invoked after each review/fix iteration and parent-executed per task" contract is replaced by "invoked once per run at the final closeout"; the execute-plan entry describes the boundary-invoked learn (learn reads the preceding-step logs under the consumer's session directory; the capture contract is unchanged). [class: IMPLEMENTATION_REQUIRED]
- [ ] done/SKILL.md Integration Points and invocation form: the Run placement paragraph's touched text gains one sentence resolving the script invocations through skills_repo_path's scripts directory; no frozen invocation block is edited (the preservation pin's literal survives in the frozen intro). [class: IMPLEMENTATION_REQUIRED]
- [ ] review-loop Integration Points: add a "Consumes `learn` skill (via the boundary procedure)" entry mirroring learn's boundary-consumer entry. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the validation block scoped to this task's files; expect this task's pins green, the review-loop and done sweeps clean, and the preservation pins still green (the Task 5 row gate may still be red until the row exists). [class: REPOSITORY_TEST]
- [ ] Commit: `skills: done moves to the once-per-run final closeout` [class: IMPLEMENTATION_REQUIRED]

### Task 5: investigate integration point, landing bookkeeping, and follow-up backlog row

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/investigate/SKILL.md`
- `docs/history/backlog/2026-10-18-runtime-scripts-home-residue.md` *(new)*
- `docs/history/backlog/PLAN-PROMPTS.md`
- `docs/history/backlog/2026-10-17-execute-plan-step-3-4-iteration-done-scoping.md` *(deleted)*

- [ ] investigate/SKILL.md Integration Points: add "### With `learn` skill": learn's Step 1.9 is a consumer that invokes investigate anchored on the backlog rows it just created, within the same learn run; investigate's stages, verdict routing, boundary, and hard gates are unchanged, and its same-turn entry commit lands in the boundary's checkout (inside a run worktree it lands with the run's squash landing). [class: IMPLEMENTATION_REQUIRED]
- [ ] Create the follow-up backlog row `docs/history/backlog/2026-10-18-runtime-scripts-home-residue.md` (Status: open, a priority, Class: fix-class) inventorying the deployed runtime scripts home's 25 real files beside the repo-symlinked majority. [class: IMPLEMENTATION_REQUIRED]
- [ ] The row's inventory classes: dated backup files and backup symlinks pointing at a removed worktree; live real files diverged from their repo twins (reconcile_post_landing.py, review_record_selection.py, skill_text_budget_caps.json, gate_liveness_ledger.json); identical duplicates (quota_governor.py, quota_pressure_stats.py); one live helper with no repo twin (sync-mcp-credentials.sh); the runner entry missing from home while skill text once invoked it bare. [class: IMPLEMENTATION_REQUIRED]
- [ ] The row's disposition: reconcile every diverged file against its repo twin (repo authoritative, recovering any home-only delta first), then retire the home copies in favor of skills-repo-path resolution; the done runner's callerless per-task class and the vendored skill-text twins of the five edited skills (and their three execute-plan sibling files) are named as tracked retirement and sync surfaces; a recovered delta files its own row. [class: IMPLEMENTATION_REQUIRED]
- [ ] Landing bookkeeping: delete the origin row `2026-10-17-execute-plan-step-3-4-iteration-done-scoping.md` per the covered-row rule (this plan is the witness) and prune the `execute-plan-step-3-4-primary-cadence` entry from PLAN-PROMPTS.md with a one-line receipt in the commit message. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the full validation block and the hygiene gates; expect exit 0. [class: REPOSITORY_TEST]
- [ ] Commit: `skills: investigate gains learn consumer; land bookkeeping and residue row` [class: IMPLEMENTATION_REQUIRED]
