# Plan: Reconcile the Authoring Claim Marker and Closeout Lifecycle

Backlog origin: docs/history/backlog/2026-10-21-plans-authoring-claim-marker-contract.md
Driving force: reliability (justification: reliability is implemented because conflicting instructions can strand digest-bound plans and leave fresh claims blocking the same target; park-triage would not take it because the contract conflict recurs at every plan-authoring closeout until one canonical rule replaces it)
Authoring claim: docs/tmp/authoring-claims/2026-10-21-plans-authoring-claim-marker-contract.md (session 01a15484-176a-70a1-814d-785fd68e1975)
Plan review record: .ai-playbook/reviews/YYYY-MM-DD-plan-review-authoring-claim-marker-and-closeout-lifecycle-p<id>-r*.md
Execution budget: 1.0h total, largest task 0.5h

## Terms

- Plan header marker: the `Authoring claim:` line copied into a plan header to identify the authoring session that produced it.
- Mutable claim file: the primary-checkout file under `docs/tmp/authoring-claims/` whose `updated:` timestamp is the live authoring heartbeat.
- Liveness probe: `scripts/check_authoring_plans_liveness.py`, the consumer that classifies untracked plans using a fresh claim file.
- Certification: the review boundary after which the plan bytes are digest-bound.
- Review digest binding: a review record's hash reference to the exact plan bytes it assessed.
- Worktree placement: authoring the plan in a dedicated Git worktree and branch, then landing that branch during closeout.
- Primary-checkout placement: authoring the plan directly in the primary checkout, without a separate worktree, landing, or branch-removal step.
- Cadence period: the claim-freshness interval, 120 minutes by default. Maintenance survey and D2 treat age at or beyond the cadence as stale; the liveness probe treats age at or below the cadence as fresh, so exactly 120 minutes is stale to the readers but fresh to the probe.
- Stale takeover: allowing a new authoring session to select a target after its prior claim becomes stale; the stale claim remains input to the existing claim procedure.
- `owned-files-clean`: the removal preflight that refuses to remove a worktree while session-owned changes remain uncommitted.
- `gate-removal`: the closeout check that must pass before an authoring worktree is removed.
- Completion-claims boundary: the evidence required before reporting plan-creation work complete; it must match the placement used.
- Duplicate-origin refusal: the modeled coverage-gate conflict where an already-landed plan covers one of this plan's backlog origins.

## Why

The plan-authoring instructions say to remove the plan header marker at certification, while the maintenance template and lesson 48 say the marker is permanent provenance. The closeout instructions also assign deletion of the mutable claim file without placing an explicit, ownership-checked delete in the actual plans closeout sequence. These conflicts leave two different marker lifetimes in force and allow completed sessions to leave stale claim files behind.

## Gist & Examples

TLDR: make the plan header marker permanent and make claim-file deletion an explicit ownership-checked closeout action, for reliability.

Before: an author begins a plan with an `Authoring claim:` line, then reaches certification. The plans skill says to remove the line, while the maintenance template says it is permanent. The author may create a post-review digest delta by following the plans skill, and may leave the mutable claim file behind because the final closeout sequence does not name the delete operation.

After: the authoring template owns the marker's permanent-provenance rule and defines claim deletion at both placement-specific closeout boundaries. The plans skill invokes that procedure without prescribing certification-time marker removal. Worktree placement reaches deletion after migration, squash landing, the owned-files-clean and gate-removal checks, and authoring-branch removal are verified. Primary-checkout placement reaches it after `done` verifies the plan, review, and closeout commits; that placement has no worktree, landing, or removal gates. A foreign or unreadable identity observed by the procedure's final check is preserved and reported.

Edge cases: the liveness probe continues to use a fresh claim file to identify an untracked plan; an archived plan keeps its header marker after the live claim file is deleted. Ordinary worktree landing or migration refusals keep the owned claim beside the preserved branch and worktree; the template's specific duplicate-origin procedure deletes the owned claim while preserving the branch and worktree; the plans-skill handoff points to that procedure without repeating its claim policy. A refused primary-placement closeout keeps the claim until the commit and artifact state can be verified. The existing final-read-then-unlink procedure is not atomic with stale takeover; no ownership guarantee extends past the identity observed at the read.

## Outcome

One authoring lifecycle contract distinguishes the permanent marker snapshot in the plan from the mutable claim heartbeat file.

- Certification preserves the marker bytes used by review digest binding and later archival.
- The template defines the claim deletion boundary for both supported placements, and the plans Final Step invokes the applicable procedure after successful closeout.
- The liveness probe and stale-heartbeat behavior remain unchanged.
- The maintenance survey and D2 consult continue to treat only fresh foreign claims as occupied; the existing cadence is 120 minutes.

Gate delta: none new; the read-only sample-context check applies AGENTS.md's existing skill-change validation rule, and this plan adds no runtime refusal class, gate, fence, protocol layer, state field, or dispatch pause.

## Design Invariants

- The template's authoring-claim procedure is the single source for claim lifetime, placement-specific deletion boundaries, and ownership checks; plans skill steps point to it.
- A plan header marker is permanent provenance once written and remains in certified, landed, and archived plan bytes.
- The claim file is mutable live state and remains in the primary checkout. Delete it after successful placement-specific closeout or an owned refusal stand-down when the immediate final identity read names this session. The template's claim procedure owns the generic retention rule and its duplicate-origin exception: delete the claim while keeping the branch and worktree for that modeled refusal, and retain it for ordinary closeout refusals. The plans skill points to this disposition and owns its landing order and branch/worktree state without restating claim policy. The check-then-unlink is best-effort and not atomic with stale takeover: a replacement claim may be unlinked after the read, and the procedure makes no ownership guarantee after that read.
- The deletion procedure preserves and reports a missing, unreadable, or foreign `session:` value observed by its final identity read. A stale takeover can replace the claim after that read and before unlink; the procedure does not claim atomicity or protection of the replacement.
- The existing duplicate-origin landing coverage gate remains unchanged and applies to newly landed plans. The template's generic refusal rule explicitly carves out its modeled conflict: keep the branch and worktree, delete this session's claim, and retain the claim for ordinary landing or migration refusals. The plans skill points to the template for claim disposition and states only its own landing order and branch/worktree closeout state.
- The liveness probe and maintenance reader semantics remain unchanged; no new gate, validator, registry field, lock, or recurring cleanup is introduced.

## Assumptions

- Lesson 48 and the maintenance template establish permanent plan-header marker provenance. The liveness probe classifies untracked plans from claim freshness and matching claim-file text; it does not inspect the plan-header marker.
- The maintenance survey and D2 treat claims at or beyond 120 minutes as stale; the liveness probe includes exactly 120 minutes in its fresh range and treats only greater ages as stale. This plan changes neither reader behavior nor the probe.
- If the closeout ownership re-check finds a different or unparseable session id, the safe result is to preserve the file and report the unresolved claim rather than overwrite or delete it.
- The template's existing check-then-unlink ownership and stale-takeover procedures remain the claim mutation contract. No ownership-loss incident is recorded in the supporting backlog evidence; introducing a lock or atomic-claim protocol here would add machinery beyond the evidence and scope. The plan records the race limit rather than claiming atomic protection.
- The 2026-10-19 closeout-delete item has a covered archive copy at `docs/history/backlog/completed/2026-10-19-authoring-claim-closeout-delete-duty.md`, witnessed by `docs/history/plans/completed/2026-10-20-authoring-worktree-landing-shape.md` for the worktree-placement arm. That plan left primary-placement claim deletion unchanged. Commit `f48799e02` restored the top-level row as open for that remaining boundary, and the corresponding `PLAN-PROMPTS.md` entry grouped it with this marker-contract investigation. Because the completed plan already cites the same origin path, this plan keeps only the marker-contract item in its header and carries the reopened primary-placement gap as related scope. At plan landing, mark both the header-origin row and the related closeout row covered by this plan, prune the prompt entry, and keep both backlog files at their current paths; do not move or copy either row to a per-item archive. At implementation completion, disposition and delete both top-level rows. Update the related closeout row's existing archive copy to name this plan as the witness for the reopened primary-placement gap while preserving the prior worktree-placement witness, then retarget or remove remaining cluster pointers to the deleted paths. This is the frozen prompt's two-stage disposition. The plan clarifies primary-placement closeout while preserving existing survey, D2, and liveness-probe behavior. The survey and D2 use one cadence period; the probe defaults to 120 minutes and includes the equality case as fresh.

Decision points requiring a grill: none remain.

## Disposition of migrated backlog items

This plan's two backlog origins were dispositioned at implementation completion per the frozen two-stage disposition in Assumptions.

- docs/history/backlog/2026-10-21-plans-authoring-claim-marker-contract.md: header origin, covered by this plan, deleted at implementation completion; landing coverage flip witness: commit 7711ab7f9.
- docs/history/backlog/2026-10-19-authoring-claim-closeout-delete-duty.md: related-scope row, covered by this plan for the reopened primary-placement gap, deleted at implementation completion; surviving disposition record: docs/history/backlog/completed/2026-10-19-authoring-claim-closeout-delete-duty.md.

## Evaluation Criteria

**Done when:**
- The plans skill and maintenance authoring template agree that certification and teardown preserve the header marker.
- The plans Final Step invokes the template-owned claim deletion procedure after the verified successful closeout boundary for each supported placement, and the template explicitly defines both boundaries. The plans skill Completion claims boundary applies the worktree-only removal checks only to worktree placement, retains tracked-freeze verification, and defines the corresponding primary-placement evidence.
- The maintenance survey and D2 consult treat a foreign claim updated within 120 minutes as fresh and occupied, and one at or beyond 120 minutes as stale and non-blocking. The liveness probe treats age exactly equal to 120 minutes as fresh and only greater ages as stale; the read-only walkthrough verifies that inclusive comparator in source, while the listed runtime fixtures make no equality-coverage claim. All existing reader and probe behavior remains unchanged.
- Existing liveness behavior and stale-heartbeat semantics remain intact, including the probe's inclusive freshness comparison. The source-level liveness test checks the plans-skill marker rule, not marker observation by the probe. The exact 120-minute probe boundary is verified by read-only source inspection of the inclusive comparator; the listed runtime fixtures do not claim equality coverage.
- No new gate, validator, lock, state field, or recurring sweep is added.

**Ship when:**
- [class: EXTERNAL_RELEASE_GATE] The instruction and test changes are reviewed and committed by the repository maintainer; evidence owner: the repository review and closeout records; closure condition: a canonical review record reports readiness and names the commit containing the changed instruction and test files.

**Done when:**
- Repository-verifiable checks pass: the liveness test and maintenance pins suite, public hygiene on changed files, and a read-only source walkthrough of both placement successes, each refusal branch, owned stand-down, foreign or unreadable identity, and the maintenance survey/D2 freshness rule.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope.

**Production code:**
- none; the liveness reader behavior is unchanged.

**Tests:**
- `scripts/test_authoring_plans_liveness.py` (update the contract assertion from certification-time removal to permanent provenance; preserve the existing live-claim and stale-claim probes).

**Documentation:**
- `agents/skills/plans/SKILL.md` (Phase 0 marker rule, Final Step closeout sequence, claim-lifecycle integration text, and placement-specific Completion claims boundary)
- `agents/skills/maintenance/template-authoring.md` (canonical marker lifetime and claim-file deletion procedure)
- `docs/history/backlog/PLAN-PROMPTS.md` (keep the frozen entry's Origins list aligned with this plan's sole header origin; identify the closeout row as related scope)
- `docs/history/backlog/completed/2026-10-19-authoring-claim-closeout-delete-duty.md` (related-row disposition and cluster-pointer cleanup at implementation completion)
- `docs/history/backlog/completed/2026-10-14-authoring-worktree-create-path.md` (cluster pointer cleanup)
- `docs/history/backlog/completed/2026-10-19-authoring-claim-closeout-delete-duty.md` (preserve the prior worktree-placement witness; at implementation completion add this plan as the reopened-gap coverage witness and retarget its marker-origin pointer)
- `docs/history/backlog/completed/2026-10-20-authoring-worktree-landing-shape.md` (cluster pointer cleanup)

**Read-only contract evidence (no edits planned):**
- `agents/skills/maintenance/survey-arms.md` (survey claim-freshness consult)
- `agents/skills/maintenance/decisions.md` (D2 fresh-foreign-claim consult)
- `agents/skills/maintenance/guards.md` (existing two-hour freshness definition)
- `scripts/check_authoring_plans_liveness.py` (default cadence and inclusive `age <= cadence` freshness boundary)

**Plan-related extension:** the authoring closeout aligns this plan's `PLAN-PROMPTS.md` origin list with the unique header origin and records the closeout row as related scope; plan landing marks that related row covered without removing it; implementation completion dispositions and deletes the top-level row, updating its existing archive copy with this plan as the reopened-gap witness while preserving the prior witness. Edits to directly adjacent integration pointers are in scope only when needed to remove a contradiction with these owners. Keep the liveness probe implementation and its reader-side cadence unchanged. The reopened row's known cluster-pointer files are listed in Task 2 so its removal leaves no stale links.

**Out of scope:**
- Changes to claim freshness, claim schema, authoring concurrency, the liveness script's classification behavior, or maintenance lane selection.
- New cleanup machinery, a validator, a registry field, a lock, or a recurring sweep.
- Changes to lesson 48, which already states the permanent-provenance rule and remains the evidence source.

## Validation Commands

```bash
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-22-authoring-claim-marker-and-closeout-lifecycle.md
python3 scripts/plan_readiness.py docs/history/plans/2026-10-22-authoring-claim-marker-and-closeout-lifecycle.md
python3 scripts/test_authoring_plans_liveness.py
bash scripts/check_maintenance_pins.sh
bash scripts/scan-public-hygiene.sh --files agents/skills/plans/SKILL.md agents/skills/maintenance/template-authoring.md scripts/test_authoring_plans_liveness.py
git diff --check
bash scripts/check-no-em-dash.sh touched
```

Perform a read-only walkthrough of the plans skill and the scheduled authoring payload using these realistic sample contexts. For each, cite the instructions that determine the expected claim state and closeout order. This checks consistency of the written contract; it does not execute the mutating lifecycle or demonstrate runtime deletion behavior.

- Worktree placement: migration, landing, removal checks, and branch removal are verified before the template-owned delete procedure is invoked.
- Primary-checkout placement: the verified `done` commit and artifact state reaches the template-owned delete procedure without worktree-only gates; the Completion claims boundary uses the primary placement's verified commit, artifact, and tracked-freeze evidence.
- Ordinary worktree landing refusal: the branch, worktree, and owned claim stay available for recovery.
- Duplicate-origin coverage refusal: the branch and worktree stay available for recovery, while the template deletes the owned claim; distinguish this modeled conflict from other landing refusals.
- Artifact-migration refusal: the branch, worktree, and owned claim stay available for recovery.
- Primary closeout or completion-commit verification refusal: the owned claim stays available for recovery.
- Owned stand-down: the template's final identity read and conditional delete are followed; a missing, unreadable, or foreign identity observed at that read is preserved and reported. The walkthrough must state that the check-then-unlink sequence is not atomic with stale takeover and does not prove the path still names the session after the read.
- Maintenance reader disposition: cite `survey-arms.md`, `decisions.md`, `guards.md`, and the liveness probe. A claim at exactly 120 minutes is stale to the survey/D2 readers but remains fresh to the probe; one older than 120 minutes is stale to both. Do not duplicate reader rules.
- Landing origin guard: the existing duplicate-origin coverage gate remains in place. Its modeled conflict keeps the branch and worktree but deletes the claim under the template's specific procedure; both generic refusal rules must state that exception while preserving claims for ordinary landing refusals.

### Task 1: Align marker lifetime at the shared authoring boundary

**Files:** `agents/skills/plans/SKILL.md`, `agents/skills/maintenance/template-authoring.md`, `scripts/test_authoring_plans_liveness.py`

- [x] **Given** a plan whose header has an `Authoring claim:` line before review certification, **expects** the line remains unchanged through certification, landing, and archival as provenance. [class: IMPLEMENTATION_REQUIRED]
- [x] **Given** the plans skill's Phase 0 and maintenance template are read together, **expects** one canonical marker-lifetime rule in the template and a plans-skill pointer with no certification-time removal. [class: IMPLEMENTATION_REQUIRED]
- [x] **Given** the plans skill describes the maintenance liveness probe, **expects** it says the probe matches a candidate's slug or identity against fresh claim-file text and does not read the plan header; the marker is provenance only. The source-text contract assertion covers this wording. [class: IMPLEMENTATION_REQUIRED]
- [x] **Given** the existing liveness test checks the plans-skill text contract, **expects** it to reject certification-time marker removal and the false claim that the probe reads the plan header, while probe fixtures continue to cover fresh-claim text classification and stale-claim behavior. The probe never inspects the header; fixtures do not claim marker persistence through certification or archival. [class: REPOSITORY_TEST]
- [x] **Given** review digest binding begins at certification, **expects** no post-certification plan-byte change is needed to remove mutable claim state. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Make claim-file deletion executable at plan closeout

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/maintenance/template-authoring.md`
- `scripts/test_authoring_plans_liveness.py`
- `docs/history/backlog/PLAN-PROMPTS.md`
- `docs/history/backlog/completed/2026-10-19-authoring-claim-closeout-delete-duty.md`
- `docs/history/backlog/completed/2026-10-14-authoring-worktree-create-path.md`
- `docs/history/backlog/completed/2026-10-19-authoring-claim-closeout-delete-duty.md`
- `docs/history/backlog/completed/2026-10-20-authoring-worktree-landing-shape.md`

(Related-row disposition and pointer cleanup at implementation completion.)

- [x] **Given** the template's AUTHORING CLAIM procedure is read by itself, **expects** it defines the primary-placement success boundary separately from worktree landing and removal, with the ownership-check and refusal procedure still owned there. [class: IMPLEMENTATION_REQUIRED]
- [x] **Given** worktree placement reaches completion, **expects** the Completion claims boundary requires verified `done` migration, owned-files-clean, a passing gate-removal result, authoring-branch removal, and the tracked-freeze evidence before the template-owned deletion procedure runs. [class: IMPLEMENTATION_REQUIRED]
- [x] **Given** primary-checkout placement reaches completion, **expects** the Completion claims boundary requires verified `done` commits, plan/review artifact state, and tracked-freeze evidence, then invokes the template's primary-placement deletion procedure without worktree-only landing or removal gates. [class: IMPLEMENTATION_REQUIRED]
- [x] **Given** the scheduled payload runs under either resolved Worktree-first placement, **expects** worktree placement uses its existing worktree and closeout, while primary placement stays in the primary checkout without worktree, landing, or removal steps; both use the template-owned claim procedure and matching closeout boundary. [class: IMPLEMENTATION_REQUIRED]
- [x] **Given** ordinary worktree refusal, **expects** branch, worktree, and claim retained; duplicate-origin refusal retains branch/worktree but deletes the owned claim; unverifiable primary closeout retains the claim. [class: IMPLEMENTATION_REQUIRED]
- [x] **Given** plan landing, **expects** both backlog rows to be marked covered, the prompt entry pruned, and both files to remain at their current paths without per-item archive copies. [class: IMPLEMENTATION_REQUIRED]
- [x] **Given** implementation completion, **expects** the archived plan to disposition and delete both top-level rows, update the related row's existing archive twin to cite this plan for the reopened primary-placement gap while retaining its prior witness, and retarget or remove remaining links to the deleted paths. [class: IMPLEMENTATION_REQUIRED]
- [x] **Given** `LivenessDeclarationTest` reads canonical closeout prose, **expects** assertions pin separate worktree and primary success boundaries, ordinary refusal retention, and duplicate-origin claim deletion with the branch/worktree preserved. These are text-contract checks, not runtime deletion proof. [class: REPOSITORY_TEST]
- [x] **Given** the owned stand-down procedure is read, **expects** assertions pin the current-session identity check, preservation of foreign, missing, or unreadable identities, and the required check/delete order. These are text-contract checks, not runtime deletion proof. [class: REPOSITORY_TEST]
- [x] **Given** the plans skill Completion claims boundary, **expects** tracked-freeze and placement-specific evidence, with owned-files-clean/gate-removal required only for worktree placement. [class: IMPLEMENTATION_REQUIRED]
- [x] **Given** an owned stand-down, **expects** the template to perform its final identity read and attempt unlink only when that read names the current session; a foreign, missing, or unreadable identity observed at that read is preserved and reported. State that stale takeover can replace the claim between read and unlink, so this best-effort check is not atomic and gives no ownership guarantee after the read. [class: IMPLEMENTATION_REQUIRED]
- [x] **Given** the maintenance survey and D2 consult read a foreign claim, **expects** a claim younger than 120 minutes to remain occupied and one exactly 120 minutes old or older not to block selection. Given the liveness probe, expects exactly 120 minutes to remain fresh and older ages to be stale. Audit each source separately; change no reader or probe behavior. [class: IMPLEMENTATION_REQUIRED]
- [x] **Given** a completed plan retains its `Authoring claim:` line after its mutable claim file is deleted, **expects** the liveness and provenance rules remain consistent without changing the probe or adding cleanup machinery. [class: IMPLEMENTATION_REQUIRED]
