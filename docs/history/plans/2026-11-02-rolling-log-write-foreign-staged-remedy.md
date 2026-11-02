# Plan: documented foreign-staged recovery for the rolling-log Write boundary rule

Backlog origin: docs/history/backlog/2026-11-02-rolling-log-write-foreign-staged-refusal.md
Driving force: automation
Execution budget: 1.5h total, largest task 0.5h
Plan review record: the staging series .ai-playbook/reviews/2026-11-02-plan-review-rolling-log-write-foreign-staged-remedy-r*.md (the highest rN for this source-plan path is authoritative)
Authoring claim: rolling-log-write-foreign-staged-remedy.md (session sess_3b4230c6-7949-4640-9f49-7d31db509d47)

## Terms

- Write boundary rule: the rules block at the top of `docs/history/backlog/PLAN-PROMPTS.md` that governs primary-checkout rolling-log writes (lock order, owned-path staging, ref-bound captured-tree transaction, recovery).
- Pre-stage guard (staged-set enumeration): the `scripts/done_run.sh` leg that enumerates every path staged against HEAD and refuses the transaction when any lies outside the declared owned set.
- Foreign staged path: a path staged in the shared primary index by a session other than the log writer, outside the writer's declared owned set.
- Blob-preserving remedy: the documented recovery that records the foreign path's staged blob sha, unstages only that path, reruns the refused transaction, re-adds the path, and verifies the re-staged blob sha is byte-identical.
- Ride-along precondition: the requirement to re-verify, immediately before and immediately after the unstage and re-add window, that the foreign path's worktree bytes still equal its staged blob.
- Acknowledgment arm: the rejected-in-scope runner extension that would let a commit proceed while naming an acknowledged foreign path; this plan pre-registers it as admission text only.
- Admission text: a pre-registered machinery admission record (incident, catch frequency, false-positive cost, review date) kept as text so a future promotion has its registration; it ships no code.
- Monitor-class log write: a rolling-log write performed by the maintenance monitor's log duties (prune, freeze, investigate append), the writer class the Write boundary rule governs.
- Log checker: `scripts/check_prompt_log_origins.py`, the log's own origin and removal-audit script; its `--prune-audit` mode is the audit this plan's validation runs.
- Primary checkout: the repository's main working copy whose index the pre-stage guard reads; shared by parallel sessions.
- Scratch clone: a temporary standalone clone of the repository, outside every registered worktree, used for fixture verification so the shared primary index is never touched.

## Why

The rolling-log pre-stage guard correctly refuses a primary log write when an unrelated staged path sits in the shared index, but the only sanctioned responses were stand down or park for the operator, and the verified recovery recipe lived only in a backlog row that no blocked writer reads at refusal time. One witnessed session hit the same refusal three times and its composed entry survived only as a conversational record, which the log's artifact rule does not recognize as durable.

## Gist & Examples

TLDR: the Write boundary rule gains the operator-gated, blob-preserving unstage/restage remedy plus the acknowledgment arm's pre-registered admission text, so a blocked monitor log write recovers without stranding, keeping the unattended loop continuous (automation).

Before (today): a peer session's unrelated backlog row sits staged in the shared primary index (its author session quota-dead, the staged blob unchanged for hours). A monitor-class log write declares only the log path, the pre-stage guard refuses naming the foreign path, and the writer has no readable remedy: it re-runs into the same refusal, stands the write down, and the composed entry survives only in conversation.

After (this plan): the same writer reads the Write boundary rule, and with the operator's explicit direction for that foreign path it records the path's staged blob sha, unstages only that path with the worktree bytes untouched, reruns the refused transaction to landing, re-adds the path, verifies the re-staged blob sha byte-identical, and releases the lock with the peer's staged work preserved. Without operator direction the writer stands down or parks exactly as today, and the rule text says so.

Edge cases:
- The foreign path's worktree bytes drift from its staged blob inside the window: the ride-along precondition fails, the writer stops before the transaction rerun and parks for the operator, never committing or discarding the peer's bytes.
- No operator direction: no remedy; the existing stand-down and park-for-operator responses stand unchanged.
- The foreign path turns out to be a live peer's in-flight edit: the same ride-along verification stops the remedy; ownership never transfers to the blocked writer.

## Outcome

A blocked primary rolling-log write has a documented, operator-gated recovery that preserves the peer's staged bytes, and the acknowledgment arm's admission registration exists as text for a future second-catch promotion.

- The next monitor-class write that meets unrelated staged dirt follows a readable remedy instead of a repeated-refusal stand-down.
- The peer's staged blob survives the window byte-identical or the remedy stops before the transaction rerun.
- The guard's staged-set enumeration and refusal behavior stay byte-for-byte unchanged.

Gate delta: no new gate, fence, refusal class, protocol layer, or schema field; the rules text gains an operator-gated prose-only recovery procedure and an admission-text pre-registration, both priced by the dispatching entry's recorded no-exit justification (the PLAN-PROMPTS entry rolling-log-write-foreign-staged-remedy's Rejected alternatives enumerate the alternatives, waiting for the peer, committing the foreign row, row-only documentation, bypassing the transaction, and show each fails the write contract, ownership boundary, durability rule, or incident the transaction closed, so no smaller priced option exists; the origin row is the incident witness); nothing removed.

## Assumptions

- assume the remedy is operator-gated, never autonomous; basis: the origin's verified recovery ran under explicit operator direction and the dispatching entry's scope arm 1 names the gate.
- assume the guard's staged-set enumeration bytes stay unchanged; basis: the entry's keep-and-narrow scope arm and the continuity disposition.
- assume the acknowledgment arm ships as pre-registered admission text with its fields stated (one witnessed incident, unknown catch frequency, operator-gated false-positive cost, review date 2026-12-02) and its incident link (the origin row's three-refusal transcript, recovery witness landing 0ec10c5bd), promoted only on a second true catch; the false-positive cost is concrete: an operator-gated acknowledgment can admit a foreign path whose worktree bytes then drift mid-window, a cost bounded by the ride-along precondition's sha verification that stops before any peer byte is committed; basis: the entry's arm 2 pricing and the repository guidelines' machinery admission protocol, which lands pre-registrations as text and promotes only on a true catch. Simpler-design comparison recorded at selection: dropping the arm with the missing-incident absence named saves three text lines but discards a free pre-registration, so a second catch would restart pricing from zero; pre-registration as text costs no code and no gate, and was selected.
- assume fixture verification runs in a scratch clone so the shared primary index is never touched; basis: a foreign staged entry in the shared index is exactly the incident class this plan documents.

Decision points requiring a grill: acknowledgment-arm disposition: pre-registered as admission text, not implemented, review 2026-12-02; basis: maintenance-selected standing authorization receipt, 2026-11-02, affected sections Assumptions and Task 2.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the Write boundary rule names every remedy step in the entry's wording (staged blob sha recorded, restore of the single named path only, transaction rerun, re-add, byte-identical sha verification), the operator-direction gate, and the ride-along precondition; a grep sweep over the rule span finds each.
- guard preservation: `scripts/done_run.sh` bytes are unchanged in the branch diff.
- loop continuity: `scripts/check_prompt_log_origins.py` (the log checker, prune-audit mode) stays green after the edits.

**Done when:**
- The Write boundary rule carries the remedy, the operator gate, the ride-along precondition, and the acknowledgment arm's admission text.
- The origin row's disposition records the deliberate decision with a dated line.
- The scratch-clone fixture verification shows sha preservation end to end and the guard refusal reproduced.
- `git diff <merge-base>..HEAD -- scripts/done_run.sh` is empty.

**Ship when:**
- Consumer repositories running the shared log machinery pick up the amended rules text at their next skills sync (external sync; no checklist item).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- none; this plan changes documentation text only

**Documentation:**
- `docs/history/backlog/PLAN-PROMPTS.md` (Task 1): the Write boundary rule remedy text; the rest of the log, including every entry section, is frozen for this plan
- `docs/history/backlog/PLAN-PROMPTS.md` (Task 2): the acknowledgment arm's pre-registration admission text
- `docs/history/backlog/2026-11-02-rolling-log-write-foreign-staged-refusal.md` (Task 2): the origin row's disposition section only

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/done_run.sh`; reason: the guard's bytes are frozen by the continuity disposition (keep-and-narrow), any change is a plan defect
- `agents/skills/**`; reason: no skill-text surface is in this plan's scope, the remedy lives in the log's own rules text

## Validation Commands

```bash
git diff $(git merge-base main HEAD)..HEAD --stat -- scripts/done_run.sh
grep -n "restore --staged" docs/history/backlog/PLAN-PROMPTS.md
python3 scripts/check_prompt_log_origins.py --prune-audit --base $(git merge-base main HEAD)
```

### Task 1: Write boundary rule carries the operator-gated remedy

Context surface: the plan's Terms, this task, and the Gist's remedy steps.

Files:
- `docs/history/backlog/PLAN-PROMPTS.md`

- [ ] The Write boundary rule text gains the remedy in the entry's wording, all five steps named: record the foreign path's staged blob sha, restore only that named path (worktree bytes untouched), rerun the refused transaction, re-add the path, verify the re-staged blob sha byte-identical [class: IMPLEMENTATION_REQUIRED]
- [ ] The remedy text states its gate: it runs only on the operator's explicit direction for that foreign path, and without direction the writer stands down or parks as today [class: IMPLEMENTATION_REQUIRED]
- [ ] The remedy text names the ride-along precondition: re-verify the foreign path's worktree blob equals its staged blob immediately before and immediately after the window; when it fails mid-window, the text names the abort residue: stop before the transaction rerun, re-add the path only when its worktree bytes still equal the recorded staged blob sha, otherwise leave the path unstaged and park for the operator with the recorded sha in the report [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect pass: within the Write boundary rule span of `docs/history/backlog/PLAN-PROMPTS.md` (the Standing rules block at the top of the file, above the entry sections), grep finds the sha record step, the restore step for the single named path, the rerun, the re-add, and the byte-identical verification; the entry sections below the rules block do not satisfy this check [class: REPOSITORY_TEST]
- [ ] Run → expect pass: `git diff $(git merge-base main HEAD)..HEAD --stat -- scripts/done_run.sh` prints nothing [class: REPOSITORY_TEST]
- Commit: `docs: add operator-gated foreign-staged recovery to the log Write boundary rule`

### Task 2: acknowledgment arm pre-registration and origin row disposition

Context surface: the plan's Terms and Assumptions decision receipt.

Files:
- `docs/history/backlog/PLAN-PROMPTS.md`
- `docs/history/backlog/2026-11-02-rolling-log-write-foreign-staged-refusal.md`

- [ ] The rules text pre-registers the acknowledgment arm as admission-only text naming: one witnessed incident linked to the origin row's three-refusal transcript and its recovery witness landing 0ec10c5bd, unknown catch frequency, and review date 2026-12-02 [class: IMPLEMENTATION_REQUIRED]
- [ ] The admission text states a concrete operator-gated false-positive cost: an acknowledgment can admit a foreign path whose worktree bytes then drift mid-window; the ride-along precondition's sha verification bounds it and stops before any peer byte is committed [class: IMPLEMENTATION_REQUIRED]
- [ ] The admission text states the arm ships no code and promotes only on a second true catch [class: IMPLEMENTATION_REQUIRED]
- [ ] The origin row gains a dated disposition line recording the deliberate decision: pre-registered admission text, implementation only on a second true catch [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect pass: `python3 scripts/check_prompt_log_origins.py --prune-audit --base $(git merge-base main HEAD)` exits 0 with no REMOVED-WITHOUT-WITNESS flag [class: REPOSITORY_TEST]
- Commit: `docs: pre-register acknowledgment arm and record origin row disposition`

### Task 3: fixture verification of sha preservation end to end

Context surface: the plan's Terms (scratch clone, blob-preserving remedy, ride-along precondition).

Files:
- none; verification only, artifacts recorded in the session notes

- [ ] Run → expect pass: in a scratch clone, stage a fixture file at an unrelated path and attempt a log transaction declaring only the log path; the pre-stage guard refuses naming the foreign path [class: REPOSITORY_TEST]
- [ ] Run → expect pass: record the fixture's staged blob sha, restore only the fixture path from the index, and rerun the transaction with the same declared paths; the pre-stage guard passes with no foreign-path refusal [class: REPOSITORY_TEST]
- [ ] Run → expect pass: re-add the fixture and verify the re-staged blob sha equals the recorded sha; a full landing inside the scratch clone is not required (landing-grade inputs stay execution-selected and out of scope here) [class: REPOSITORY_TEST]
- [ ] Run → expect pass: the fixture's worktree bytes equal its staged blob immediately before and immediately after the window (the ride-along precondition holds in the clean fixture); the shared primary checkout's index is never touched by this task [class: REPOSITORY_TEST]
- Commit: none; verification task, evidence recorded in the session notes
