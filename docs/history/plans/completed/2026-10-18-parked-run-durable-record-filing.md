# Plan: parked-run durable record filing

Authoring claim: docs/tmp/authoring-claims/parked-run-durable-record-filing.md (session sess_ba9e0356-44b4-4f13-a29d-a18cdfbc7c15)

Backlog origins (scope of record):
- docs/history/backlog/2026-10-17-parked-run-durable-record-residue.md

Driving force: automation, efficiency
(ranked compound; the run files its own durable records at park time instead of stranding them for a later session or the operator to notice and land, removing the recurring rescue direction and its operator-time cost)

Plan review record: the staging series .ai-playbook/reviews/2026-10-18-plan-review-parked-run-durable-record-filing-p63e62431-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)

Execution budget: 1h total, largest task 0.5h

## Terms

- Park disposition: the lifecycle's response when a run pauses or stands down (quota pause, budget pause, input stop, lane hold); today it records the pause and leaves owned filings where they lie.
- Durable record: a tracked repository filing a run produces beside its plan work (a backlog row, a residual note, a follow-up filing its dispositions call for).
- Tracked landing path: the recorded disposition naming where and when a filing lands (the branch and tip carrying its commit, and the vehicle: the run's own closeout landing, or a repository-tracked follow-up vehicle); the Filed-row reconciliation's sanctioned alternative to landing in the archive transition. The recorded form's definition home is this plan's new filing paragraph; the reconciliation paragraph remains the disposition-semantics home, byte-unchanged.
- Filed-row reconciliation: the fail-closed closeout check at execute-plan's Filed-row reconciliation paragraph, comparing the pre-archive receipt's `filed_row_paths` against the tree and the recorded landing paths; unchanged by this plan.
- Run branch: the execution run's worktree branch under a worktree placement; the primary-placement lane records no run worktree, and this plan's park-time commit applies only to worktree placements.
- Claimed task path: a path a run's per-task done commits are scoped to; the filing step is not a claimed-path commit.
- Closeout rider: a landing-time step (origin-row disposition, entry prune) that fires only when a run reaches its closeout; dormant for a parked run.
- Pre-archive receipt: the `pre_archive_receipt` record the run writes into its session state file before the archive commit is requested, carrying `filed_row_paths` among its fields.
- Checkpoint commit-marker convention: the `wip:` subject prefix convention of the WIP checkpoint duty, the mechanical commit class this plan's filing step reuses.
- Session manifest: execute-plan's named per-run record surface (manifest.md), the home of the tracked-landing-path records.
- Vendored twin: the runtime-side copy under ~/.agents/skills/ of each touched agents/skills/ file, synced byte-equal in the same change per the repository guidelines' Vendored Asset Sync Rules.

## Why

A parked run that files a durable record strands it: per-task commits are scoped to claimed task paths, closeout riders never fire while parked, and the primary checkout's staging gates refuse unclaimed paths, so the first parked filer left an untracked draft that an unrelated turn landed a day later. The durable-records rule requires a run to land its filings or leave a tracked landing path; the pause machinery owns the commit convention but no arm records a parked filing's landing path today, and the step must live beside that machinery because input-stop and lane-hold parks never consult the quota section.

## Gist & Examples

TLDR: execute-plan's park disposition gains a record-filing step (commit the filing on the run branch and record its tracked landing path in the session manifest) and the pre-archive receipt reads that bookkeeping, so a parked run's durable records are tracked instead of stranded; automation, because the run completes its own filing duty at the moment it pauses.

Before: a parked run writes a follow-up backlog row, cannot commit it (claimed-path scoping, dormant riders, primary staging refusals), and parks; the draft survives untracked until an unrelated session notices and lands it.

After: the same run commits the row on its run branch before pausing and records the tracked landing path in the session manifest; if the run resumes, the closeout lands it exactly as the Filed-row reconciliation already requires; if it never resumes, the record is a tracked, resumable landing path instead of untracked residue.

Edge cases: a filing with no recorded landing path still fails the Filed-row reconciliation (the check is unchanged and stays fail-closed); the step authorizes no primary-checkout staging and no claimed-path commit; a filing whose landing vehicle is a follow-up actor must name a repository-tracked durable vehicle created in the same step (a backlog row naming the landing owner and time), the Filed-row reconciliation's sanctioned alternative disposition, never a second untracked terminal state; the park-time commit never carries plan bytes or semantically classified paths, so the checkpoint convention's non-semantic invariant holds; the parked run's evidence contract and park-time state mirror belong to the summary-handoff entry and are not touched here.

## Outcome

A parked run that files a durable record on a worktree placement leaves it committed on its run branch with a recorded tracked landing path, instead of stranding it untracked; on a primary placement the run records the filing need for the lane's durable-vehicle arm.

- The witnessed stranding class closes at the moment it is created, with no new gate, validator, or ledger.
- The Filed-row reconciliation keeps its fail-closed strength and gains the bookkeeping it was always meant to read.
- The pre-archive receipt's `filed_row_paths` reflects the run's real filing state at pre-archive.

Gate delta: none counted; the change adds one park-disposition step and one enumeration read, both inside the existing checkpoint-commit and reconciliation machinery (the step reuses the sanctioned checkpoint commit class bounded to manifest-named record files that never carry plan bytes or semantically classified paths, and records the landing-path disposition the Filed-row reconciliation already sanctions; nothing new refuses, pauses, or checks beyond the standing closeout), and no gate, fence, refusal surface, protocol layer, schema field, or pausing condition is added or removed (admission: the origin row records the rejected second-checker and primary-staging arms with the missing-incident absence named).

## Assumptions

- assume the vehicle is the bounded composition: commit on the run branch at park time plus the tracked landing path recorded now, with the closeout reconciliation unchanged; basis: the origin row's Suggested direction, the AGENTS.md durable-records sentence (land in the same run or leave a tracked landing path), and the reconciliation's own sanctioned-alternative wording.
- assume the filing commit rides the checkpoint commit-marker convention (mechanical, branch-scoped, never primary staging); basis: the WIP checkpoint duty's existing sanctioned class and the origin's foreign-staging witness.
- assume this plan owns only the record-filing vehicle and its bookkeeping; the parked run's evidence contract and the park-time state mirror belong to the post-implementation-review-summary-handoff entry, and neither plan rewrites the other's span; basis: the dispatch entry's Orientation span split.
- assume the byte growth is priced: the delta is the dispatch entry's anti-growth allowance (one park-disposition step plus one enumeration read); the same-file cut surface was surveyed and the only candidate cuts sit inside the pinned WIP-checkpoint spans whose re-key would widen this change's surface, so the unbalanced growth stands as the reportable finding class the anti-growth rules name; basis: the dispatch entry's Anti-growth line and the repository skill text anti-growth rules.
- assume the never-resume durability of the tracked-landing-path record is bounded by this plan: the park-time commit message itself carries the landing-path content (the branch name and the vehicle, with the tip read from the branch ref rather than embedded) so the branch stays self-describing if the gitignored manifest is lost; the manifest mirror question belongs to the summary-handoff entry's undecided arm; basis: the dispatch entry's span split.
- assume vendored twins sync byte-equal in the same change; basis: the repository guidelines' Vendored Asset Sync Rules.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: on a worktree placement a parked filing is always either landed by the closeout or carried by a recorded tracked landing path naming a repository-tracked vehicle, and on a primary placement the filing need is recorded for the lane's durable-vehicle arm; the Filed-row reconciliation's fail-closed behavior is byte-unchanged, verified by the hunk and standing-surface checks, with the refusal and vehicle behaviors exercised by the sample-context exercise
- anti-growth: the landed delta is one paragraph and three clause extensions, with no gate, validator, ledger, or new commit class, verified by the hunk-count check; the byte growth is priced in Assumptions
- maintainability: the tracked-landing-path recorded form has one operative definition home (the new filing paragraph) and the Filed-row reconciliation paragraph remains the byte-unchanged disposition-semantics home; the step references the reconciliation by name

**Done when:**
- the two insertions land with byte-equal vendored twins and the pins suite failing set matches the recorded baseline
- the validation battery is green, the sample-context exercise records every context outcome, and the landing diff carries exactly the hunks the task lists prescribe

**Ship when:**
- the landed tree's validation battery passes and the closeout report records the boundary, span, and sample-context witnesses

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- agents/skills/execute-plan/SKILL.md
- scripts/check_maintenance_pins.sh *(conditional: only the boundary-pin re-key arm; byte-unchanged when the suite reports no new delta)*
- docs/history/backlog/2026-10-17-parked-run-durable-record-residue.md *(landing rider: deletion)*
- docs/history/backlog/PLAN-PROMPTS.md *(landing rider: own-entry prune with receipt)*

**Tests:**
- none new; the validation battery below is the verification surface

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, or contradicts a contract the plan changed. A pins-suite delta caused by an insertion boundary is in scope only as the pin re-key named in Task 1. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the summary-handoff entry's span (the parked run's evidence contract and the park-time state mirror); reason: the dispatch entry's span split assigns it to its own entry
- the Filed-row reconciliation paragraph's check semantics; reason: the check stays fail-closed and byte-unchanged
- review-loop machinery and any validator or gate script; reason: no gate or panel change is in scope

## Validation Commands

```bash
bash scripts/check_maintenance_pins.sh
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 scripts/plan_readiness.py docs/history/plans/2026-10-18-parked-run-durable-record-filing.md --pre-round
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh file agents/skills/execute-plan/SKILL.md
diff agents/skills/execute-plan/SKILL.md "$HOME/.agents/skills/execute-plan/SKILL.md"
```

### Task 1: the park-time record-filing step and the receipt enumeration read

Context surface: the plan's Terms and this task.

Files:
- agents/skills/execute-plan/SKILL.md
- scripts/check_maintenance_pins.sh *(conditional: only the boundary-pin re-key arm below; byte-unchanged when the suite reports no new delta)*

- [x] Run the pins suite at the pre-change HEAD and record its full tail (the OUTCOME line plus every PIN FAIL and suppressed-recorded-reds line) in the session manifest as the recorded baseline. [class: REPOSITORY_TEST]
- [x] Run → expect RED: the literals `tracked landing path for it in the session manifest` and `tracked-landing-path records when the manifest carries them` are absent from the skill and its twin before the edit. [class: REPOSITORY_TEST]
- [x] Insert one paragraph immediately after the Task-boundary checkpoint duty paragraph (the paragraph carrying the WIP checkpoint commits duty, inside the Context budget checkpoints section, whose pause signals the step shares). [class: IMPLEMENTATION_REQUIRED]
- [x] The paragraph states the filing step: at every pause signal, including input stop and lane hold beside the duty's existing enumeration, when a parked or paused run files a durable repository record, the run commits the record files on the run branch under the checkpoint commit-marker convention and records a tracked landing path for it in the session manifest (the branch and tip carrying the commit, and the landing vehicle), before the pause takes effect. [class: IMPLEMENTATION_REQUIRED]
- [x] The paragraph bounds the commit content: the commit carries only the record files the manifest record names, written before the commit; a durable record is a repository filing the run's own tasks or dispositions call for (a backlog row, a residual note, a follow-up filing), and the commit never carries plan bytes or semantically classified paths, so the checkpoint convention's non-semantic invariant holds. [class: IMPLEMENTATION_REQUIRED]
- [x] The paragraph bounds the follow-up vehicle: a filing whose landing vehicle is a follow-up actor must name a repository-tracked durable vehicle created in the same step (a backlog row naming the landing owner and time), and the record names where and when the filing lands. [class: IMPLEMENTATION_REQUIRED]
- [x] The paragraph states the placement arm: the step applies to worktree placements; on a recorded primary placement the run performs no park-time commit (that lane has no run worktree branch and no closeout landing) and records the filing need in the session manifest as a parked-run filing note naming the record and its intended vehicle. [class: IMPLEMENTATION_REQUIRED]
- [x] The paragraph scopes the plan's Outcome and correctness claims to worktree placements, the primary lane's durable vehicle being the summary-handoff entry's undecided mirror arm. [class: IMPLEMENTATION_REQUIRED]
- [x] The paragraph states the authority boundary: the step authorizes no primary-checkout staging and no claimed-path commit. [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the WIP checkpoint duty's pause-signal enumeration with input stop and lane hold (input stop being the stop-for-operator class of the Only-stop-between-tasks list), re-keying the pause-signals pin under this task's conditional pins arm in the same change. [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the pre-archive receipt sentence's `filed_row_paths` clause to read: the run's filed-row paths as `filed_row_paths`, taken from the tree and from the session manifest's tracked-landing-path records when the manifest carries them, and the receipt unions the two sources; at closeout the run retires or re-vehicles each tracked-landing-path record its own landing satisfies. [class: IMPLEMENTATION_REQUIRED]
- [x] Sync the vendored twin byte-equal in the same change. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the literals `tracked landing path for it in the session manifest`, `tracked-landing-path records when the manifest carries them`, and `filed_row_paths` verify in the skill and its twin after the edit, and diff against the twin exits 0. [class: REPOSITORY_TEST]
- [x] Boundary witness: given the pins suite run after the change, its delta is exactly the pause-signals pin re-key; any other new failure caused by an insertion boundary is re-keyed inside this change as the only other sanctioned pins-suite edit, with the re-keys recorded in the session manifest. [class: REPOSITORY_TEST]
- [x] Commit: `feat: park-time record filing with tracked landing paths` [class: IMPLEMENTATION_REQUIRED]

### Task 2: boundary, span, and validation battery

Context surface: the plan's Terms and this task.

Files:
- agents/skills/execute-plan/SKILL.md (read-only verification)

- [x] Verify the landing diff carries exactly the hunks the task lists prescribe, nothing else in the skill. [class: REPOSITORY_TEST]
- [x] Verify the sibling and standing surfaces are untouched: the Filed-row reconciliation paragraph, the summary-handoff entry's span surfaces, and the primary-checkout staging gates carry no changes from this plan. [class: REPOSITORY_TEST]
- [x] Exercise context 1 and record the outcome in the session manifest: a parked run filing a follow-up row with a follow-up vehicle (expect the record files committed on the run branch, the manifest record naming the tracked vehicle row and the branch tip, and the Filed-row reconciliation reading the record). [class: REPOSITORY_TEST]
- [x] Exercise context 2 and record the outcome in the session manifest: a run pausing with no durable filing (expect no tracked-landing-path record in the simulated manifest and no filing commit in the simulated branch log). [class: REPOSITORY_TEST]
- [x] Exercise context 3 and record the outcome in the session manifest: a never-resumed run's follow-up-vehicle record (expect the Filed-row reconciliation accepting it without landing, the vehicle being a repository-tracked row). [class: REPOSITORY_TEST]
- [x] Exercise context 4 and record the outcome in the session manifest: a filed record with no recorded landing path at closeout (expect the Filed-row reconciliation refusing it, fail-closed unchanged). [class: REPOSITORY_TEST]
- [x] Exercise context 5 and record the outcome in the session manifest: a filing on a recorded primary placement (expect the parked-run filing note in the session manifest and no park-time commit in the log). [class: REPOSITORY_TEST]
- [x] Run the full validation battery: the pins suite failing set equals the recorded baseline (after Task 1's sanctioned re-key if it fired), the hygiene scan exits 0, the em-dash file-mode scan on the touched skill is clean, and the readiness pre-round reports no blocking problem. [class: REPOSITORY_TEST]
- [x] Record the task's verification-only closure in the session manifest (this task stages nothing; the recorded baseline and every recorded sample-context outcome are its evidence). [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- docs/history/backlog/2026-10-17-parked-run-durable-record-residue.md: the landing closeout (the authoring session's landing commit, outside task scope) deletes this row per the repository guidelines' backlog-completion rule, naming this landed plan as the witness, and tidies the removed row's Cluster back-references in the rows that carry them in the same change, and prunes this plan's own dispatch entry from PLAN-PROMPTS.md with the `PLAN-PROMPTS-PRUNE: parked-run-durable-record-filing -> docs/history/plans/2026-10-18-parked-run-durable-record-filing.md` receipt line and a prune-audit pass; the row's problem, expected, and suggested-direction substance is folded into this plan's Why, Gist, and Tasks.
