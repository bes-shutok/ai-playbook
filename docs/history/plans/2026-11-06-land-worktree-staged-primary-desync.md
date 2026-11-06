# Plan: land-worktree staged-primary desync guard and closeout census

Backlog origin: docs/history/backlog/2026-11-04-land-worktree-staged-primary-desync.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-06-plan-review-land-worktree-staged-primary-desync-p69b98331-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2.5h total, largest task 1.5h
Executed: no
Authoring claim: 2026-11-04-land-worktree-staged-primary-desync.md (session sess_c9ef3df7-5135-4a54-9a3b-5de61eb7b73e)

## Terms

- land-worktree: the `land-worktree` mode of `scripts/land_squash.sh`; rebase-and-squash in the source worktree, then move the default branch ref by compare-and-swap without touching the primary checkout's index or worktree.
- CAS (compare-and-swap): the two-value `git update-ref` ref move that is the landing's final write; it operates at the ref level only and cannot observe worktree or index state.
- primary checkout: the main working checkout of this repository, where rolling-log writes and shared index state live.
- changed-path set: the paths the landing changes, derived from the source branch delta against its base (`git diff --name-only <base>...<branch>`).
- intersecting staged state: a primary-checkout path that is staged (`git status --porcelain` index column non-blank, not `??`) or a locally modified tracked path, and that is a member of the changed-path set.
- staged-state census: the session-end read-only `git status --porcelain` sweep the closeout arms gain, with a commit-or-restore disposition over the full owned entries it finds, staged and unstaged-but-uncommitted alike.
- rider edits: the landing's own rider changes (freeze-line removals, origin flips, prune receipts) that a desynced checkout displays as staged re-applications of pre-landing content.
- PLAN-PROMPTS entry: a dispatch entry in the tracked rolling log `docs/history/backlog/PLAN-PROMPTS.md`.
- closeout arms: the closeout-phase duty paragraphs of the Worktree-first standard in `agents/skills/execute-plan/worktree-first.md`.
- modeled-refusal fail shape: a named, expected refusal reported through the outcome contract (`scripts/OUTCOME_CONTRACT.md`) as a final `OUTCOME: fail` line, distinct from a tool error.

## Why

`land-worktree` moves the default branch across a staged primary checkout with no landing-time signal: the checkout then silently desyncs from the new tip and displays the landing's own rider edits as a staged resurrection that invites the next session to commit pre-landing bytes over the landing. The guard class is witnessed three times (2026-10-28, 2026-11-04, 2026-11-05) and the omission is named verbatim in the tool's own usage text. The census arm answers the stranded-record half: owned unstaged-but-uncommitted primary state left at session boundaries twice posthumously (the 2026-11-04 gate-liveness-ledger append, the 2026-11-05 certification-diagnostics append), the evidence-decay cost the origin pins the census sweep to bound.

## Gist & Examples

TLDR: land-worktree gains an intersecting staged-state pre-refusal and the primary-checkout closeout gains a staged-state census, closing the silent CAS desync class, for code-quality.

Before: a session stages a PLAN-PROMPTS entry in the primary checkout and ends; 35 seconds later a landing CAS-moves main across that path; the checkout then shows the landing's rider edits as a staged re-application of pre-landing content, and a peer session must recover the stranded blob by hand (the 2026-11-04 14:38:55 witness).

After: the same landing refuses before any ref update, naming the intersecting path (`refuse: primary checkout staged state intersects the landing changed-path set: <path>; remedy: if the staged state is this session's, commit or restore it, then retry; a foreign staged path is never staged, discarded, or committed autonomously - route it per the operator-gated foreign-staged remedy, never by following the remedy line on a foreign path`); and the staging session's own closeout census would have committed or restored the entry at its boundary, so the landing never met the desync. A staged path the landing does not change still lands normally.

## Outcome

A landing can no longer silently desync a staged primary checkout, and a session can no longer strand staged state in the primary for the next session to trip over.

- The land-worktree landing refuses with a named-path report when the primary holds staged or locally-dirty tracked state on a changed path, before any ref update and pre-lock; the accepted residual is the narrow read-to-CAS window (a peer staging an intersecting path after the read), whose backstop is the reconcile tail's staged-peer-edit block row signaling the desync post-hoc.
- A staged or dirty path outside the changed-path set does not block the landing (no blanket refusal).
- The closeout arms carry a session-end staged-state census with a commit-or-restore disposition over the full owned entries the sweep finds, staged and unstaged-but-uncommitted alike; the stale-checkout discriminator's dispositions keep precedence on their overlap class, and foreign-owned state outside it is left untouched and reported.
- The usage text stops claiming that land-worktree omits the staged-state pre-refusal for the intersection class while still scoping the snapshot and restore machinery to `land`.

Gate delta: adds one refusal class, the intersecting staged-state pre-refusal in land-worktree, priced by the completed-integrity-failure witness route: the origin's Observed vs expected section plus three witnessed completed landings that desynced or stranded primary state (2026-10-28 teardown preservation, the 2026-11-04 14:39:30 CAS across a staged PLAN-PROMPTS entry, the 2026-11-05 16:35 landing's superseded-iteration residue) record the integrity failures the refusal prevents; the origin's Expected paragraph itself scopes the refusal to paths the landing changes, which rules out the class-default alternatives (add the sanctioned exit and remove the false positive: no false positive exists, the check is absent, not wrong; simplify the flow: the flow's correctness depends on the check, so removing flow steps cannot supply it). The no-exit justification above is recorded here; the origin carries the incident evidence, not the alternatives inventory. Review date for the added refusal class: 2026-12-06. Supporting measurement: gate liveness ledger at authoring time reads catches=30 incidents=48 (ratio 30:48, `scripts/gate_liveness_ledger.py show` 2026-11-06). The census arm is protocol text at an existing closeout boundary and adds no blocker. No gate, fence, protocol layer, or schema field is removed or added beyond the one refusal class; `none` otherwise.

## Assumptions

- The existing snapshot helper family (`parse_status_z`, `load_snapshot`, `snapshot_contains`, `snapshot_state_of`, `snapshot_has_dirty` in `scripts/land_squash.sh`) is reusable for the primary-checkout census read; basis: the helpers already parse `status --porcelain=v1 -z` for `land` mode's pre-refusals.
- The changed-path set input equals the source-branch delta the landing flow already computes for its other gates; basis: the origin's Suspected root area and the helper's existing branch-delta derivations.
- The guard runs inside the existing land-worktree flow before the compare-and-swap and needs no new lock; basis: the origin's evidence note that `git update-ref` cannot refuse on worktree state, so the check must be an explicit read-only step in the flow.
Decision points requiring a grill: none remain.

## Standing constraints

- This repository never runs its whole test suite at task boundaries; validation runs the focused suite file plus the named repository gates only.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the refusal fires on the intersection only, names the intersecting paths, and exits with the outcome contract's modeled-refusal fail shape before any ref update.
- maintainability: the guard reuses the existing snapshot helper family and the existing branch-delta derivation instead of adding a parallel parser.
- protocol fit: the census duty lives in the existing closeout arms and never autonomously touches foreign-owned staged state.

**Done when:**
- The three Task 1 suite cells pass: intersecting staged path expects the named fail; non-intersecting staged path expects the landing to proceed; the dirty-intersecting shape expects the same named fail.
- `bash -n scripts/land_squash.sh` passes and the focused suite file is green.
- The census duty and its commit-or-restore disposition are present in `agents/skills/execute-plan/worktree-first.md`.

**Ship when:**
- No external release condition; the plan is complete when the repository-verifiable checks pass.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/land_squash.sh` (Task 2)
- `scripts/OUTCOME_CONTRACT.md` (Task 2)
- `agents/skills/execute-plan/worktree-first.md` (Task 3)

**Tests:**
- `scripts/test_land_squash.py` (Tasks 1-2) *(new cells in existing file; Task 2 adds the omission-audit exception comment)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/done_run.sh`; reason: the runner transaction and its staged-delta checks are the closeout runner's own contract, untouched by this plan.
- `scripts/landing_parentage_gate.py`; reason: the parentage gates and the ref-lock span are owned by the landing-serialization plan (docs/history/plans/2026-11-04-parallel-execution-landing-serialization-blockers.md).

## Validation Commands

Validation preamble (authoring-time record, 2026-11-06): every pinned command below was executed over the plan bytes and the current tree before the first review round. Observed outcomes: command 1 passes today (existing suite green, 179 passed); command 2 passes today (`bash -n` clean); commands 3, 4, 5, and 6 fail today with exit 1 (the census duty, the guard function, and the updated usage text do not exist yet - the expected RED-today state, flipping GREEN exactly when Tasks 2 and 3 land; no vacuous pass, the first actually-failing gate is command 3). Em-dash added-lines scan over the plan bytes: pass. Public hygiene scan: pass. Readiness pre-round gate: pass (structural-clean, `OUTCOME: pass`). Rule 22 mechanical audit: every pinned span below occurs in exactly one prescribed location; `bash -n` over this block clean.

```bash
REPO="$(git rev-parse --show-toplevel)"; cd "$REPO" || exit 1
# 1. Focused suite: the guard's suite cells (canonical executable artifact)
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_land_squash.py -q || { echo "focused suite failed"; exit 1; }
# 2. Helper syntax after the guard edit
bash -n scripts/land_squash.sh || { echo "land_squash.sh syntax check failed"; exit 1; }
# 3. Census duty pinned in the closeout arms (distinctive spans, fail-closed)
grep -qF "session-end staged-state census" agents/skills/execute-plan/worktree-first.md || { echo "census duty missing from closeout arms"; exit 1; }
grep -qF "commit-or-restore disposition" agents/skills/execute-plan/worktree-first.md || { echo "census disposition missing"; exit 1; }
# 4. Guard function identifier exists (presence pin; the before-the-CAS ordering is pinned behaviorally by the Task 1 suite cell, which observes the refs unchanged at refusal)
grep -qF "refuse_intersecting_primary_state" scripts/land_squash.sh || { echo "guard function missing"; exit 1; }
# 5. Usage text carries the updated intersection pre-refusal claim
grep -qF "intersecting staged-state pre-refusal" scripts/land_squash.sh || { echo "usage text not updated for the intersection class"; exit 1; }
# 6. Contract row updated
grep -qF "intersecting staged-state pre-refusal" scripts/OUTCOME_CONTRACT.md || { echo "outcome contract row not updated"; exit 1; }
# 7. Text-policy scans over the scoped non-Markdown paths and the touched set (repository root anchored)
bash scripts/check-no-em-dash.sh touched || { echo "em-dash scan failed"; exit 1; }
bash scripts/scan-public-hygiene.sh || { echo "public hygiene scan failed"; exit 1; }
```

### Task 1: Suite cells for the intersecting staged-state refusal

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_land_squash.py`

Primary class anchors:
- `LandSquashHelperTest` in `scripts/test_land_squash.py`

- [ ] Cell 1: given a land-worktree fixture landing whose changed-path set contains a path staged in the primary checkout, expects the helper to refuse before any ref update, naming the staged path in the refusal output (the assertion anchors on the refusal's own prefix line, not bare path presence, which today's reconcile block row already prints) and ending with `OUTCOME: fail` [class: REPOSITORY_TEST]
- [ ] Cell 2: given a land-worktree fixture landing whose changed-path set contains no primary staged or locally-dirty tracked path while an unrelated staged path exists in the primary, expects the landing to proceed to `OUTCOME: pass` [class: REPOSITORY_TEST]
- [ ] Cell 3: given a land-worktree fixture landing whose changed-path set contains a locally modified tracked (unstaged) primary path, expects the same named refusal before any ref update and `OUTCOME: fail`, mirroring the land-mode precedent of separate staged and dirty cells [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the focused suite fails exactly on Cells 1 and 3 and stays green elsewhere; Cell 2 is a green-today safety witness whose discriminating value is realized when the Task 2 guard lands (it pins no blanket refusal against a future implementation) [class: REPOSITORY_TEST]
- [ ] Commit: `test: land-worktree intersecting staged-state refusal cells (RED)` [class: REPOSITORY_TEST]

### Task 2: Pre-CAS intersecting-path guard in land-worktree

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/land_squash.sh`
- `scripts/OUTCOME_CONTRACT.md`
- `scripts/test_land_squash.py`

Primary class anchors:
- `refuse_intersecting_primary_state` in `scripts/land_squash.sh`

- [ ] The guard delivers the intersecting staged-state refusal: given the primary checkout holding staged or locally-dirty tracked state on any member of the changed-path set, expects a read-only refusal before any ref update naming the intersecting paths and exiting the outcome contract's modeled-refusal fail shape [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness: given staged or dirty primary state on no changed path, expects the landing to proceed unchanged (the refusal is intersection-scoped, never a blanket staged-state refusal) [class: IMPLEMENTATION_REQUIRED]
- [ ] The guard reuses the snapshot helper family (`parse_status_z`, `load_snapshot`, `snapshot_contains`, `snapshot_state_of`, `snapshot_has_dirty`) and the existing branch-delta derivation; no parallel porcelain parser is added [class: IMPLEMENTATION_REQUIRED]
- [ ] The guard function is DEFINED in the shared helper region beside the snapshot family, outside the land-worktree mode section between its two mode markers, and invoked from the flow pre-lock (after base-tip resolution, beside the existing pre-lock gates), keeping the landed 2026-11-04 narrowed lock span intact [class: IMPLEMENTATION_REQUIRED]
- [ ] Audit-fit witness: given the passing omission-scope audit's banned tokens (`status --porcelain`, `load_snapshot`) scanned inside the mode section, expects the guard's in-section presence limited to the bare invocation and in-section prose free of those tokens, so the audit stays green [class: IMPLEMENTATION_REQUIRED]
- [ ] The omission-scope audit gains one comment line recording the sanctioned exception (a read-only primary porcelain read defined outside the section and invoked pre-lock, never restore or write), so the audit's stated intent matches the landed runtime semantics instead of drifting from them [class: IMPLEMENTATION_REQUIRED]
- [ ] The usage text's land-worktree paragraph is updated to declare the intersecting staged-state pre-refusal (a read-only porcelain read reusing land's snapshot helpers) while scoping the restore machinery, and land's full snapshot/refusal surface, to `land`; the mode's internal block comment and the usage text's land-worktree fail-class enumeration gain the new modeled refusal [class: IMPLEMENTATION_REQUIRED]
- [ ] The land_squash row of `scripts/OUTCOME_CONTRACT.md` is updated: the land-worktree clause declares the new intersecting staged-state pre-refusal (a read-only porcelain read reusing land's snapshot helpers that still never writes the primary index or worktree; the restore machinery and land's full snapshot pre-refusal surface stay scoped to `land`) and the new modeled fail class joins the row's fail enumeration [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the focused suite passes including the Task 1 cells and the helper passes a bash syntax check [class: REPOSITORY_TEST]
- [ ] Commit: `feat: land-worktree refuses landings intersecting staged primary state` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Session-end staged-state census duty in the closeout arms

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/worktree-first.md`

Primary class anchors:
- `Ad-hoc-worktree closeout migration` in `agents/skills/execute-plan/worktree-first.md`

- [ ] The closeout arms deliver the session-end staged-state census: given a session reaching its closeout boundary with uncommitted state it owns in the primary checkout, staged, unstaged-but-uncommitted, or owned untracked, expects a commit-or-restore disposition over the porcelain sweep's full owned entries (index and worktree columns, `??` included), recorded beside the closeout receipts in the run's session notes (the existing recording convention) before worktree removal [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit-vehicle witness: given owned state the census commits at the boundary, expects the commit leg to ride the closeout's own path-limited commit arm (the done closeout's owned-path commit vehicle), never a bare base-branch write, with the duty worded for both primary-placement and worktree-placed sessions [class: IMPLEMENTATION_REQUIRED]
- [ ] Ordering witness: given an owned staged entry whose bytes the stale-checkout discriminator classifies (an ancestor-blob match after a peer landing moved the base), expects the census to leave the discriminator's dispositions standing (restore for unclaimed matches, report-for-confirmation for session-owned matches) rather than auto-committing or auto-restoring through the census [class: IMPLEMENTATION_REQUIRED]
- [ ] Coalescence witness: given a session that runs the full done closeout, expects one sweep to serve both boundaries - the census's disposition governs the primary checkout and the done closeout's dangling-change stop keeps its own repositories - so no executor resolves two duties over one checkout with conflicting dispositions [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness: given uncommitted state in the primary checkout owned by another session and outside the discriminator's arms, expects the census to leave it untouched, report it, and proceed (never stage, discard, or commit a foreign path autonomously) [class: IMPLEMENTATION_REQUIRED]
- [ ] The census is a read-only porcelain sweep with a disposition; it adds no new gate, lock, or validator [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: command 3 of the Validation Commands block passes; the whole block exits 0 [class: REPOSITORY_TEST]
- [ ] Commit: `docs: session-end staged-state census duty in the worktree closeout arms` [class: IMPLEMENTATION_REQUIRED]
