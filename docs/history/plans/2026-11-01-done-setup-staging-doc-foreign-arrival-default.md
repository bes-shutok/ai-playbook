# Plan: done setup classifies transferred staging docs foreign-by-arrival

Backlog origin: docs/history/backlog/2026-11-01-authoring-transfer-in-reviews-home-strands-done-setup.md
Backlog origin: docs/history/backlog/2026-10-31-no-charter-staging-scan-facts-anchor.md
Driving force: automation + simplicity
Plan review record: the staging series .ai-playbook/reviews/2026-11-01-plan-review-done-setup-staging-doc-foreign-arrival-default-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1.5h total, largest task 0.5h

## Terms

- foreign-by-arrival: the classification a staging candidate receives when it predates the run-start marker's recorded epoch in a run-owned linked worktree: present before the run's first owned record, therefore not this run's write, therefore foreign.
- run-start marker epoch: the integer Unix timestamp on the first content line of the run-start marker file (written by `scripts/done_run.sh` `cmd_setup` and bound to the manifest via `--run-marker`).
- staging candidate: a gitignored review-staging record (`.md` plus its `.stats.json` sibling) under the resolved reviews directory that the write-manifest claim-or-foreign gate classifies as owned, foreign, or refused.
- transferred reviews home: the `.ai-playbook/reviews/` copy a worktree-placement run receives from the primary checkout during the Worktree-first standard's transfer-in step.
- uncovered set: the staging candidates the write-manifest classification finds neither owned nor foreign before the split arms run.
- claim-or-foreign gate: the write-manifest classification that requires every staging candidate to be either owned by the run (claimed) or recorded foreign; a candidate that is neither refuses the manifest write.
- refuse arm: the claim-or-foreign outcome that refuses the uncovered candidate (prints it and fails the write), as opposed to classifying it.
- owned arm: the claim-or-foreign outcome for candidates the run itself staged: they stay owned claims and the foreign-by-default arms disengage for the run.
- adopted manifest: a prior interrupted run's boundary carried verbatim (start commit, owned paths, foreign markings) into a new write by `setup --adopt` or re-entered with `--from-manifest`.
- fresh boundary: a write-manifest invocation that writes a new boundary with no adopted manifest carried; the only shape the foreign-by-arrival arm engages.

## Why

Authoring provisioning copies the whole reviews home into a fresh worktree, and every copied staging doc then hits the done setup's claim-or-foreign gate as unclassifiable because the linked-worktree shape keeps the refuse arm that the primary-checkout shape already retired (b3025de59). The run must hand-carry a foreign list whose natural sources both fail: a snapshot list misses docs written after capture, and the transfer carries the session's own prior-run records forward. Each refusal costs a full setup re-run plus a manual list append, per worktree, per pick; witnessed twice in one session on 2026-11-01.

## Gist & Examples

TLDR: the done setup classifies transferred staging docs foreign-by-arrival, so authoring provisioning stops stranding on unclassifiable reviews-home copies; automation retires the hand-carried list and its re-run loop.

Before (today): an authoring session provisions its worktree per the standard (the transfer copies 9533 files, 4195 staging docs at the witnessed run), then runs `bash scripts/done_run.sh setup --owned-plan <plan>` with no foreign list. The write-manifest refuses naming every pre-existing staging doc. The run captures a list from a prior snapshot; the setup refuses again naming whatever landed after the snapshot, and names the session's own prior-run records the transfer carried forward. Fixing it costs a full setup re-run per refusal, per worktree, per pick.

After (this plan): the same provisioning and setup run with no list at all. The classifier splits the uncovered set in the linked-worktree shape: candidates whose file mtime predates the bound run-start marker's recorded epoch classify foreign-by-arrival, merge into the manifest's foreign paths, and the write-manifest output names the count and a sample. A staging doc written after the marker (mid-run, unclaimed) still refuses, keeping the silent-claiming protection. The hand-carried list and its stale-snapshot failure mode disappear for fresh provisioning.

Edge cases: a run-start marker whose epoch cannot be parsed fails closed to refuse (no silent auto-foreign); a tracked-but-unclaimed candidate refuses as today; a run that staged its own review records keeps the owned arm exactly as before; an adopted manifest's carried foreign markings are untouched; a candidate newer than the marker refuses regardless of shape; an adopted boundary (a resumed interrupted run) never engages the arrival arm, so its uncovered mid-run docs keep their adjudication refusal instead of being silently classified foreign by the resume's fresh marker.

## Outcome

The done setup classifies the transferred reviews home's pre-run docs foreign-by-arrival, so authoring provisioning completes without hand-carried foreign lists.

- Provisioning an authoring worktree with the standard's full reviews-home copy and running setup with no foreign list succeeds on the first pass.
- Mid-run staging writes keep their refusal, so the classifier's visibility protection is unchanged where it matters.
- The standard's transfer-in text documents the mechanized default and the fresh-enumeration recipe for deployments without it, and records the no-charter scan's facts anchor as a hardening note.

Gate delta: removes the claim-or-foreign refusal subclass for pre-marker transferred staging docs in run-owned linked worktrees (a narrowing of an existing refusal class; witnessed catch twice on 2026-11-01, the two origin rows are the incident links); adds no gate, ledger, registry, fence, protocol layer, or schema field; expected catch frequency is every authoring provisioning over a transferred reviews home; false-positive cost is a peer staging doc written between transfer-in and marker write, which classifies foreign at the run's own setup and whose owner's manifest still protects it at drain; review at the next authoring-flow maintenance pass. Admission shape: completion of the existing classifier's foreign-by-default arm (the protocol's completion shape), not a new mechanism.

## Assumptions

- assume the arrival boundary is the bound run-start marker's recorded epoch; basis: the marker is the run's first owned record, its epoch rides the existing content-confirmed first line, and `--run-marker` already binds it, so no new record surface or mtime-only fragility is introduced.
- assume the worktree arm is default-on with no opt-out flag; basis: pre-marker docs in a run-owned worktree are definitionally not this run's writes (transfer-in precedes setup), the post-marker refusal keeps the visibility protection, and an opt-out knob has no witnessed need.
- assume arrival-classified paths merge into the existing `foreign_review_paths` manifest field; basis: they are semantically foreign, the schema stays unchanged, and provenance rides the write-manifest report line.
- assume the no-charter sibling row lands as the doc-level hardening note its own text prescribes; basis: the row states an out-of-band worktree facts edit has no in-contract writer, self-identifies as a hardening note, and forbids a facts byte-equality check as new machinery.

Decision points requiring a grill: arrival-boundary-source: run-start marker epoch (standing authorization receipt; 2026-11-01; Task 2); activation-shape: default-on without opt-out (standing authorization receipt; 2026-11-01; Task 2, Standing constraints); manifest-representation: merge into foreign_review_paths (standing authorization receipt; 2026-11-01; Task 2); sibling-row-disposition: doc-level hardening note per the row's own text (standing authorization receipt; 2026-11-01; Task 3)

## Standing constraints

- Machinery admission (repository guidelines): this plan adds no gate, lock, validator, ledger, or required ceremony; the worktree arm completes an existing classifier arm and every fail-closed refusal arm is preserved. A facts byte-equality check for the no-charter anchor is out of scope by the sibling row's own boundary.
- The primary-checkout foreign-by-default arm's qualifying conjuncts and behavior stay byte-for-byte unchanged; only the linked-worktree shape gains the arrival arm.

## Evaluation Criteria

**Quality dimensions:**
- correctness: both witnessed refusal shapes are pinned by tests at the lib level (a transferred home with pre-marker docs classifies foreign; a post-marker candidate refuses), and the primary arm's regression pins stay green unchanged.
- safety: every fail-closed arm keeps its refusal and has a test: unparseable marker epoch, tracked-but-unclaimed candidate, post-marker candidate, run-staged own records, adopted-manifest markings untouched.
- observability: the write-manifest output names the arrival-classified count with a bounded sample, bounded per the existing report-emission limit.

**Done when:**
- `scripts/done_sweep_gates_lib.py` classifies pre-marker transferred staging docs foreign-by-arrival in the linked-worktree shape, with the report line, and all fail-closed arms hold.
- `agents/skills/execute-plan/worktree-first.md`'s Transfer-in implementation carries the mechanized-default line, the fresh-enumeration interim recipe, and the no-charter hardening note.
- The lib and wrapper test suites pass: `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py scripts/test_done_run_wrapper.py -q`.

**Ship when:**
- none (repository-internal change; no deployed or human-owned condition).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py` (Task 2)
- `agents/skills/execute-plan/worktree-first.md` (Task 3)

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` (Task 1) *(new tests added to the existing suite)*
- `scripts/test_done_run_wrapper.py` (Task 1) *(new test added to the existing suite)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/worktree_closeout_migrate.py`; reason: the no-charter scan's anchor behavior is recorded as a hardening note only (Task 3), and its code changes nothing in this plan.
- transfer-in scoping (entry arm (b)); reason: explicitly priced separately by the origin entry and deferred.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py scripts/test_done_run_wrapper.py -q
bash scripts/check-no-em-dash.sh added-lines --base main
bash scripts/scan-public-hygiene.sh
```

### Task 1: Pin the worktree foreign-by-arrival arms in tests

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_done_sweep_gates_lib.py`
- `scripts/test_done_run_wrapper.py`

Primary class anchors:
- `_foreign_by_default_split` in `scripts/done_sweep_gates_lib.py`

- [ ] Given the suite's existing linked-worktree refuse-arm pins, expects each pin updated to the arrival-arm expectations with the flip owned by this task's checkboxes (no orphaned pin asserts the old universal worktree refusal) [class: REPOSITORY_TEST]
- [ ] Given the wrapper-level setup over a provisioned worktree with a transferred reviews home and no foreign list, expects setup to succeed with the pre-marker docs classified foreign-by-arrival (owns the wrapper-suite test) [class: REPOSITORY_TEST]
- [ ] Given a run-owned linked-worktree context with a bound run-start marker whose recorded epoch precedes a set of gitignored staging candidates under the resolved reviews dir, expects those candidates classified into the auto-foreign set (foreign-by-arrival), not the refuse set [class: REPOSITORY_TEST]
- [ ] Given the same shape with one candidate whose mtime postdates the marker epoch, expects that candidate in the refuse set while its pre-marker siblings stay auto-foreign [class: REPOSITORY_TEST]
- [ ] Given a candidate with an mtime equal to the marker epoch, expects it in the refuse set (boundary: only strictly-older candidates classify foreign) [class: REPOSITORY_TEST]
- [ ] Given an unparseable or missing marker epoch in the linked-worktree shape, expects the whole uncovered set refused (fail closed, no auto-foreign) [class: REPOSITORY_TEST]
- [ ] Given a tracked-but-unclaimed candidate in the linked-worktree shape, expects it refused exactly as today [class: REPOSITORY_TEST]
- [ ] Given a linked-worktree run that staged its own review records in the home, expects the owned arm kept and no auto-foreign classification [class: REPOSITORY_TEST]
- [ ] Given the primary-checkout shape (repo root is the primary checkout), expects the existing foreign-by-default behavior byte-for-byte (regression pins stay green unchanged) [class: REPOSITORY_TEST]
- [ ] Given an adopted manifest carrying foreign markings, expects them untouched by the arrival arm [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the new worktree-arm behaviors fail against today's classifier (the linked-worktree shape refuses everything uncovered) [class: REPOSITORY_TEST]
- [ ] Write minimal implementation (Task 2) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN [class: REPOSITORY_TEST]
- [ ] Commit: `feat: pin worktree foreign-by-arrival classification arms` [class: REPOSITORY_TEST]

### Task 2: Extend the classifier with the linked-worktree arrival arm

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/done_sweep_gates_lib.py`

Primary class anchors:
- `_foreign_by_default_split` in `scripts/done_sweep_gates_lib.py`

- [ ] `_foreign_by_default_split` gains the linked-worktree arm: when the gate context's repo root is a run-owned linked worktree (not the primary checkout), candidates in the refuse path classify into the auto-foreign set when all hold: gitignored, under the resolved reviews dir, and mtime strictly older than the bound run-start marker's recorded epoch [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the witnessed provisioning shape (a linked worktree whose transferred reviews home carries pre-marker staging docs), expects the witnessed refusal to disappear and the manifest's foreign paths to carry the arrival-classified set [class: IMPLEMENTATION_REQUIRED]
- [ ] The arrival arm engages only on a fresh boundary: given an adopted manifest (a `setup --adopt` resume or a `--from-manifest` re-entry), expects the refuse arm unchanged for the uncovered set, so the resume's fresh marker never silently classifies the adopted run's mid-run staging docs foreign [class: IMPLEMENTATION_REQUIRED]
- [ ] The marker epoch is read from the bound run-start marker's first content line via the existing `--run-marker` binding; given a missing, unreadable, or unparseable epoch, expects fail-closed refusal of the whole uncovered set with a named reason line [class: IMPLEMENTATION_REQUIRED]
- [ ] The write-manifest output names the arrival-classified classification: a line with the count and a bounded sample (the existing report-emission limit), so the classification is visible per run [class: IMPLEMENTATION_REQUIRED]
- [ ] Arrival-classified paths merge into the existing `foreign_review_paths` manifest field; given a completed write, expects the schema unchanged and the paths present in the field [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness: given a mid-run staging doc written after the marker epoch and left unclaimed, expects the claim-or-foreign refusal to fire with its current named shape (the silent-claiming protection holds) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN (Task 1's suite) [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `feat: classify transferred staging docs foreign-by-arrival in worktree setup` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Document the mechanized default and the hardening anchor in the standard

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/worktree-first.md`

- [ ] The Transfer-in implementation text gains one line naming the mechanized default: the done setup classifies pre-marker staging docs foreign-by-arrival in run-owned worktrees, so hand-carried `--foreign-review-from` snapshot lists are retired for fresh provisioning [class: IMPLEMENTATION_REQUIRED]
- [ ] The same section's interim line names the fresh-enumeration recipe for deployments without the default: enumerate the worktree's reviews dir fresh at setup time and declare everything present pre-setup foreign, never carry a snapshot [class: IMPLEMENTATION_REQUIRED]
- [ ] The section records the no-charter hardening note: the staging scan resolves its reviews and review-certs homes from the worktree's facts copy; no in-contract writer edits worktree facts post-provisioning (transfer-in is noclobber), and an out-of-band facts edit would redirect the scan and strand run-created records; a facts byte-equality check is new machinery and stays out of scope [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: document foreign-by-arrival default and staging-scan anchor in transfer-in` [class: IMPLEMENTATION_REQUIRED]
