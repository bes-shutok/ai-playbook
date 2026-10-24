# Plan: Keep done-run locks and guard records inside the closeout boundary
Backlog origins (scope of record):
- docs/history/backlog/2026-10-20-done-setup-classification-stop-holds-lock-blocks-retry.md
- docs/history/backlog/2026-10-20-finalize-ledger-append-after-landing-strands-dirt.md
- docs/history/backlog/2026-10-13-done-landing-commit-lock-span.md
Driving force: simplicity; secondary: reliability
Plan review record: the staging series .ai-playbook/reviews/YYYY-MM-DD-plan-review-done-run-lock-span-and-append-ordering-r*.md
Execution budget: 2.5h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-20-done-setup-classification-stop-holds-lock-blocks-retry.md (session d9260a1b-38f1-4cd6-ac50-aeb9b5b183c3)

## Terms

- **Classification stop:** setup's read-only, fail-closed exit when an interrupted run manifest needs an operator remedy or cannot be classified.
- **Guard firing:** a `--guard-firing NAME:KIND:EVIDENCE[:NOTE]` record appended to `scripts/gate_liveness_ledger.json`.
- **Landing commit:** the project commit produced by `done_run.sh commit` for the declared staged set.
- **No-prior-landing closeout:** finalize receives a guard firing when the run has no prior project landing commit; it must create a checked ledger commit before releasing the lock.

## Why

Two done-run paths leave follow-up work outside the lock or commit that produced it. Setup can exit after classifying an interrupted manifest while still holding the lock, so following a named remedy and retrying setup waits on the stopped session's own hold. Finalize appends guard-liveness rows after the landing and lock release, so a tracked ledger change can remain uncommitted. A separate witnessed row shows that one guard record included text caught by the public hygiene scan, so the ledger writer must screen candidate evidence and note fields before replacing the tracked ledger.

## Gist & Examples

Title: Keep done-run locks and guard records inside the closeout boundary.

TLDR: Release a lock after terminal setup stops and land clean guard-liveness rows through the checked closeout path.

Before (today): An operator runs setup for an interrupted manifest. The classifier names a terminal remedy and setup exits, but the process still owns the done lock; following the remedy and retrying setup can wait on that same hold. In a separate path, finalize appends a guard-liveness row after the landing sweep and lock release, leaving a tracked ledger edit outside the commit that just completed.

After (this plan): The same terminal setup outcome releases only the lock generation acquired by that invocation, so the operator can apply the named remedy and retry. A clean guard row is written before declared staging and the landing sweep. With no prior landing commit, finalize runs the checked commit subcommand as a child while the parent retains its lock, captures its result, then completes release and status verification.

Edge cases: A successful `--from-manifest` continuation keeps its lock. If the existing public-hygiene scan finds unsafe candidate text, the canonical ledger stays unchanged, the advisory row is skipped with a warning, and closeout continues. A child commit failure returns to finalize, which reports it and still releases and verifies the parent lock. A plain commit retains its bounded serialization window under the existing status and base-freshness checks.

## Outcome

The setup remedy-and-retry path does not wait on its own lock. A guard firing supplied for a landing is appended before declared-path staging and the landing sweep, then included in the staged set; after a successful landing it appears exactly once in committed ledger bytes. With no prior landing commit, finalize starts the checked commit subcommand as a child while its parent retains the lock, then captures the result and proceeds to release and verify the lock. Candidate ledger bytes are checked with the existing public hygiene scanner before they replace the canonical ledger. A hygiene hit leaves the ledger unchanged, reports the skipped row, and does not block the closeout. The done skill describes these call paths and their ordering.

- The `--from-manifest` success arm retains the lock and resumes the named boundary.
- A clean guard record is committed once through the chosen closeout path; finalize does not append it again after a landing. A child failure returns to the parent, which still releases and verifies the done lock.
- Neither a hygiene hit nor an advisory append failure strands tracked ledger dirt or refuses unrelated closeout work.
- The plain-commit serialization window is recorded as an accepted bound; this plan adds no merge-lock span.

Gate delta: no net new refusal classes, hard gates, fences, protocol layers, schema fields, or dispatch-pausing conditions; this plan reorders existing closeout work.

## Serialization decision

Accept the bounded window on `done_run.sh`'s plain landing commit. The 2026-10-13 origin records no witnessed lost update, and a session-held merge lock around the full commit stage self-collides with the docs-branch sync's own non-reentrant merge-lock acquisition. Keep the existing read-only merge-status consult and base-freshness checks as the compensating controls. Revisit this disposition after a witnessed stale-index revert or by 2027-01-24, whichever comes first; do not add a lock or another gate in this plan.

## Assumptions

- The current classifier remains the authority for interrupted-manifest state; this change alters lock cleanup around its terminal outcomes, not its verdicts or remedies.
- Guard-liveness rows remain advisory analysis records. The closeout continues if a firing is malformed, its writer is unavailable, or its candidate text is rejected by the hygiene scan.
- The scan uses the existing `scan-public-hygiene.sh` and its configured deny patterns; no second pattern list or validator is introduced.

Decision points requiring a grill: none remain. The maintenance-selected scope authorizes releasing only this run's acquired lock, moving its own ledger rows into the checked commit path, skipping hygiene-hit telemetry without blocking, and accepting the no-incident serialization window; date: 2026-10-24; affected plan sections: Serialization decision, Outcome, Tasks 1 and 2.

## Machinery admission

This plan adds no blocking gate, validator, lock, registry entry, or ceremony. It reuses the existing public-hygiene scanner to screen the candidate ledger row before the existing atomic ledger replacement. Incident: the 2026-10-20 ledger append contained a foreign ticket prefix and pre-landing SHA in its `evidence` text (`docs/history/backlog/2026-10-20-finalize-ledger-append-after-landing-strands-dirt.md`, witness section). Expected catch frequency: one observed catch; no broader frequency is claimed. False-positive cost: one advisory row is skipped and reported, while closeout continues; rewording the evidence permits a later record. Review date: 2027-01-24. This extends the existing scan's input timing and keeps its nonblocking telemetry posture; it creates no separate gate to retire.

## Decision points

- Prefer an explicit release on setup's terminal classification and fail-closed paths over treating the same holder PID as reentrant. The former removes the self-hold without changing the lock's ownership or ancestry checks.
- Move guard-firing appends into the commit path before declared staging and the landing sweep. For no-prior-landing closeouts, use a child process while the parent holds the lock. Never append twice after a successful landing.
- Accept the plain-commit serialization window as stated above; adding a merge-lock span would self-collide and has no witnessed-loss basis.
- Screen the candidate row before the canonical ledger write. On a hygiene hit, skip that advisory row with a warning rather than blocking the closeout or writing unsafe text.

## Evaluation Criteria

**Quality dimensions:**

- Correctness: the acquired lock is released on terminal setup stops, and the `--from-manifest` continuation remains protected by it.
- Reliability: a guard row either rides the checked project commit or is skipped without leaving tracked dirt; a successful commit is not followed by a duplicate finalize append.
- Privacy: evidence and note fields are scanned before canonical ledger replacement, using the existing patterns and scanner.
- Simplicity: no reentrant lock semantics, new validator, second pattern list, or merge-lock span is added.

**Done when:**

- Wrapper coverage proves terminal classification failures leave the lock status free, while explicit `--from-manifest` re-entry still holds and uses the lock.
- Wrapper coverage proves the ledger write precedes declared staging and sweep, and a no-prior-landing child commit lands while the parent lock is held before release.
- Ledger coverage proves a hygiene hit leaves canonical ledger bytes unchanged and emits a warning; clean input appends atomically.
- Existing done-run tests continue to cover staged-scope, reverse-squash, lock ownership, and finalize release behavior.

**Ship when:** both focused suites pass and the landing carries the three origin coverage flips and prompt-log disposition.

## Review Scope

**Explicit must-fix: findings on these paths are always in scope.**

**Production code:**
- `scripts/done_run.sh`
- `scripts/done-lock.sh`
- `scripts/gate_liveness_ledger.py`
- `scripts/gate_liveness_ledger.json`

**Documentation:**
- `agents/skills/done/SKILL.md` Steps 0, 3, and 6

**Tests:**
- `scripts/test_done_run_wrapper.py`
- `scripts/test_gate_liveness_ledger.py`

**Plan-related extension:** add or adjust focused fixtures in the named suites when required to prove terminal release, commit order, no-prior-landing outcomes, and pre-write hygiene.

**Out of scope; reject unless plan-related:**
- `scripts/done-lock.sh` ownership or reentrancy semantics.
- A new merge lock around the plain landing commit.
- New hygiene patterns, a second scanner, a registry row, or any lane-blocking gate.
- Changing the ledger schema or generalizing the scanner beyond the evidence and note fields this plan covers.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_done_run_wrapper.py'
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_gate_liveness_ledger.py'
```

### Task 1: Release the acquired lock on terminal setup stops

Context surface: the plan's Terms, Outcome, and the setup classification-stop origin.

Files:
- `scripts/done_run.sh`
- `scripts/test_done_run_wrapper.py`
- `agents/skills/done/SKILL.md`

Primary class anchors:
- `classify_partial` in `scripts/done_run.sh`
- `cmd_setup` in `scripts/done_run.sh`

- [ ] On every terminal classification and fail-closed exit after setup acquires the done lock, release only the generation acquired by this invocation before returning the original refusal outcome and remedy text. [class: IMPLEMENTATION_REQUIRED]
- [ ] Keep the successful `--from-manifest` arm unchanged: it re-enters the named boundary under the acquired lock. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add wrapper cases for terminal classification and tool failure; assert the original refusal outcome and remedy, a free lock, and held lock on explicit re-entry. [class: REPOSITORY_TEST]
- [ ] Update Step 0 to state the stop-release order and preserve the existing setup remedies and outcome classes. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `fix: release done lock on setup classification stop` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Land guard-firing rows through the checked commit path

Context surface: the plan's Outcome, Machinery admission, and the two ledger-related origin rows.

Files:
- `scripts/done_run.sh`
- `scripts/gate_liveness_ledger.py`
- `scripts/gate_liveness_ledger.json`
- `scripts/test_done_run_wrapper.py`
- `scripts/test_gate_liveness_ledger.py`
- `agents/skills/done/SKILL.md`

Primary class anchors:
- `cmd_commit` in `scripts/done_run.sh`
- `cmd_finalize` in `scripts/done_run.sh`
- `record` in `scripts/gate_liveness_ledger.py`
- `save_ledger` in `scripts/gate_liveness_ledger.py`

- [ ] Add repeated `--guard-firing` to `commit`; write accepted rows before declared-path staging and the landing sweep, then stage the ledger path so those bytes ride the commit. [class: IMPLEMENTATION_REQUIRED]
- [ ] Before replacing the canonical ledger, scan the serialized candidate using the existing public-hygiene scanner. On a hit, leave ledger bytes unchanged, warn that the advisory row was skipped, and continue the closeout without a new refusal class. [class: IMPLEMENTATION_REQUIRED]
- [ ] With no prior landing, run the checked commit subcommand as a child under the parent lock; capture output/status, warn on failure, continue finalize release/status checks, and never append twice. [class: IMPLEMENTATION_REQUIRED]
- [ ] Before the project commit, child failure restores prior ledger bytes/index; after it lands, preserve the committed row and report later failure without rollback. [class: IMPLEMENTATION_REQUIRED]
- [ ] Test the landing row is written before staging/sweep and committed exactly once; retain clean-append and hygiene-hit checks. [class: REPOSITORY_TEST]
- [ ] Test fallback success observes the committed row while locked, then asserts exactly one matching row after finalize and verifies release and free status. [class: REPOSITORY_TEST]
- [ ] Inject pre-commit failure: preserve prior bytes/index, warn, continue cleanup, and release the lock; inject post-commit failure: report it, preserve the committed row, and release the lock. [class: REPOSITORY_TEST]
- [ ] Update Steps 3 and 6 to describe the selected commit and fallback order, the pre-write scan, and the still-nonblocking advisory behavior. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `fix: land guard firing rows with done closeout` [class: IMPLEMENTATION_REQUIRED]
