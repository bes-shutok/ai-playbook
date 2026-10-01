# Done-tail closeout resume checkpoint

Backlog origins (scope of record): `docs/history/backlog/2026-10-01-done-tail-resume-after-session-interruption.md`

Classification: [class: fix-class] automation (evidence-fenced continuation for recoverable closeout interruptions); authoring only (this plan is not self-executing).

## Terminology and core concepts

- **Closeout checkpoint**: a durable record written when a done run reaches its finalizer span (write-manifest complete through Step 6's finalize), naming the run_id, the manifest path, the session identity, and the verified state at interruption - the artifact a resume continuation reads.
- **Resume continuation**: a bounded recovery that re-verifies the run identity, the claimed deliverables, and commit ownership, then runs only the remaining gates and the finalizer - never adopting or staging another run's work implicitly.
- **Done-tail resume watcher**: the standing resume watcher machinery (`scripts/execute_plan_runtime.py` watcher family and the maintenance skill's resume carrier) that currently carries budget-gated work; this plan extends its reach to the closeout boundary.

## Coverage dispositions (re-verified against disk 2026-10-01)

- The interrupted-record visibility and manual-close layers are LANDED: the Step 0 survey reports complete:false manifests, the finalizer (`finalize-manifest --run-id`) closes them, and disposition-manifest closes dead-root records. The deliverables witness's BASE arms (recorded path, archive twin, HEAD) are landed; the landed-deletion and note-backed arms are AUTHORED by the sibling plan `2026-10-01-deliverables-witness-resolution-arms.md` (landed as a document, not yet executed - zero arm code on disk). Task 2 orders after that plan's execution and references the arms as the ones it lands; until then the continuation's witness re-run uses whichever arms are on disk at execution time and refuses unverifiable entries fail-closed. This plan adds only the automatic, evidence-fenced continuation between the visibility and close ends.

## Tasks

### Task 1: the resumable-closeout checkpoint in the done skill

Files:
- `agents/skills/done/SKILL.md`

Evidence:
- `grep -c "resumable-closeout checkpoint" agents/skills/done/SKILL.md` returns at least 2

- [x] Run → expect RED: the Evidence grep misses (count before editing) [class: REPOSITORY_TEST]
- [x] In Step 0's write-manifest block (after the echo-capture duty - the same paragraph whose sentence carries the `write-manifest: undisposed-interrupted:` literal) and in Step 6's finalize preamble, add the checkpoint duty with create-then-refresh semantics: Step 0 creates the resumable-closeout checkpoint in the run's manifest directory when the run enters the finalizer span (a sibling JSON naming run_id, the manifest path, the session identity, the manifest's sha256, and the gates already green at write time), and Step 6 REFRESHES it at the finalize preamble (same filename, updated manifest sha and gate set) rather than writing a second copy; a successful finalize removes the checkpoint sibling; on an interruption the checkpoint is what a resume continuation reads, and staleness is the recomputed-manifest-sha mismatch [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Evidence grep [class: REPOSITORY_TEST]
- [x] Commit: `skills: resumable-closeout checkpoint at the finalizer span` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the evidence-fenced resume continuation

Files:
- `agents/skills/done/SKILL.md`

Evidence:
- `grep -q "resume continuation" agents/skills/done/SKILL.md`
- `grep -q "refuses automatic continuation" agents/skills/done/SKILL.md`

- [x] Run → expect RED: both Evidence greps miss [class: REPOSITORY_TEST]
- [x] In the write-manifest paragraph's sentence carrying the `write-manifest: undisposed-interrupted:` literal, add the resume continuation arm: a later session that finds a resumable-closeout checkpoint verifies the run identity (the checkpoint's run_id and session identity against the done-session directory's records), re-runs the deliverables witness (every owned deliverable resolves per the witness arms on disk at execution time, including the landed-deletion and note-backed arms once the deliverables-witness plan executes - it orders before this plan's Task 2), and verifies commit ownership (the owned-commits ledger's commits reachable from the landing destination); only then does it run the remaining gates and the finalizer, recording the continuation as a session-notes receipt (the precedent home the skill's own receipts use; the manifest's disposition record is a dead-root-only mechanism and is never hand-edited); it refuses automatic continuation - leaving the record for explicit `--adopt`, finalize, or disposition - when the checkpoint is stale (the recomputed manifest sha256 differs from the checkpoint's recorded sha), the identity differs, any claimed deliverable is unverifiable, or the owned commits are not verifiably landed; it never adopts or stages another run's work implicitly [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: both Evidence greps [class: REPOSITORY_TEST]
- [x] Commit: `skills: evidence-fenced resume continuation for interrupted closeouts` [class: IMPLEMENTATION_REQUIRED]

### Task 3: the watcher's reach extends to the closeout boundary

Files:
- `agents/skills/maintenance/SKILL.md`

Evidence:
- `grep -c "closeout boundary" agents/skills/maintenance/SKILL.md` returns at least 1

- [x] Run → expect RED: the Evidence grep misses [class: REPOSITORY_TEST]
- [x] In the Step 1 interrupted-manifest classification arm (the survey bullet whose list-interrupted-manifests output reports each manifest's complete=false state and proposes resuming or adopting live-root runs), extend the proposal sentence to the closeout boundary: a live-root run interrupted inside its finalizer span with a resumable-closeout checkpoint proposes the resume continuation (the Task 2 arm) instead of only the adoption boundary, and the arm's adoption-owns-continuation cross-reference names the resume continuation as the second sanctioned continuation; the discovery surface is this skill-level arm (the driver's watcher receipts carry a closed plan-centric schema a done-run checkpoint does not ride), so no driver code changes [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Evidence grep [class: REPOSITORY_TEST]
- [x] Commit: `skills: resume watcher reaches the closeout boundary` [class: IMPLEMENTATION_REQUIRED]

### Task 4: full-suite validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block; covers the checkpoint, the continuation, and the watcher reach

- [x] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]

## Validation Commands

```bash
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base main
bash scripts/check_maintenance_pins.sh
grep -c "resumable-closeout checkpoint" agents/skills/done/SKILL.md
grep -q "resume continuation" agents/skills/done/SKILL.md
grep -q "refuses automatic continuation" agents/skills/done/SKILL.md
grep -c "closeout boundary" agents/skills/maintenance/SKILL.md
```

## Assumptions

- Only the two skill files change: the continuation's discovery surface is the maintenance survey's Step 1 interrupted-manifest arm (the driver watcher's receipts are plan-centric and closed, so the checkpoint never rides that path), and the closeout checkpoint needs no driver code change.
- The checkpoint is additive to the manifest directory (a sibling JSON), never a manifest-schema edit; the existing reader contracts are untouched.
- The refusal arms are the design's core: an automatic continuation runs only on a verified checkpoint, and every unverifiable shape keeps today's explicit-disposition exits.

Decision points requiring a grill: Task 1 checkpoint home (a sibling JSON in the manifest directory, never a manifest-schema edit); Task 2 verification order (identity, deliverables witness, commit ownership - each refusing to explicit disposition before any gate reruns); Task 2 non-adoption rule (continuation resumes only its own boundary, never staging another run's work); Task 3 reach arm (the Step 1 classification arm is the discovery surface; the plan-centric watcher receipts stay untouched); checkpoint lifecycle (create at Step 0, refresh at Step 6, remove at successful finalize, staleness by sha mismatch).

## Review Scope

- `docs/history/plans/2026-10-01-done-tail-closeout-resume-checkpoint.md`
- `agents/skills/done/SKILL.md`
- `agents/skills/maintenance/SKILL.md`
- `docs/history/backlog/2026-10-01-done-tail-resume-after-session-interruption.md`
