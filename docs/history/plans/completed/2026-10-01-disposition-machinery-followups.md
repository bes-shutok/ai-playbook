# Plan: Disposition-machinery follow-ups: stamp CAS, witness-arm documentation, proactive deployment probe

[github: https://github.com/admitriev/ai-playbook] Backlog origin: `docs/history/backlog/2026-09-30-disposition-machinery-followups.md`
Driving force: correctness; secondary documentation precision

## Gist TLDR

TLDR: close the disposition stamp's check-then-write window with a fresh-re-read CAS (an adopt/finalize/disposition racing the stamp refuses or degrades to the idempotent reprint instead of blurring the record), document the implemented third plan-arm (`HEAD:<recorded path>`) in the done skill's witness sentence, and give the survey's classification arm a proactive stale-deployment probe so a missing `disposition-manifest` sub-command fails fast in the survey instead of at the operator's closure attempt.

## Outcome + Gate delta

A concurrent adopt or finalize landing between the disposition checks and the stamp no longer produces a `dispositioned` record on an adopted or finalized manifest: the stamp re-reads the payload immediately before writing and refuses (naming the racing shape) unless the verified state still holds, with the already-dispositioned case degrading to the idempotent reprint. The done skill's witness sentence names all three implemented plan-resolution arms. The survey arm probes the sub-command before proposing dispositions and reports a stale-deployment line when the resolved lib predates it.

Gate delta: one re-read CAS inserted before the disposition stamp (no new lock primitive - the manifest write stays the existing atomic replace; the CAS is a fresh re-read plus state comparison, the item's own named alternative), one witness-sentence clause in the done skill, one probe sentence in the maintenance survey arm, one suite arm per behavior; no schema, gate, refusal class, or protocol change.

## Terms

- **Stamp CAS**: the fresh re-check immediately before `write_run_manifest` - two reads: this manifest's payload fresh from disk (racing shapes: `complete` flipped true, a `dispositioned` record appeared) and a fresh `_manifest_adopted_by_another` directory re-scan (racing shape: an `adopted_from` link appeared on any manifest in the session dir); each racing shape refuses, with the dispositioned shape degrading to the idempotent reprint (the racer's record).
- **Third plan arm**: the implemented resolution accepting an owned plan at `HEAD:<recorded path>` in addition to the recorded path and the `plans_completed` twin.

## Assumptions

- A CAS re-check is preferred over a lock: the manifest write is already an atomic replace, no other writer holds a lock the disposition could share, and the race window is single-check wide; the item names this alternative explicitly. The re-check is fail-closed: an absent or unparseable fresh payload refuses rather than stamping over an unknown state. The dispositioned-race reprint is understood to be the racer's record (its date/note), matching the existing idempotent arm.
- The survey probe is read-only (`--help` via the resolved lib) and never mutates; its failure output routes to the same stale-deployment remedy the done paragraph prescribes (redeploy the sweep-gates pair).

Decision points requiring a grill: none remain - the item's Expected behavior prescribes all three arms verbatim; the CAS-vs-lock choice is the item's own named alternative.

### Task 1 - The stamp CAS

- [x] In `scripts/done_sweep_gates_lib.py`, `_cmd_disposition_manifest`: after the witness verifies and immediately before `write_run_manifest`, re-check with TWO fresh reads: (a) re-read this manifest payload fresh from disk (an absent or unparseable re-read refuses fail-closed) - if `complete` is now true, refuse naming the post-check finalize; if a `dispositioned` record now exists, reprint the existing record (the racer's record: its date/note, not this call's) and exit 0 (the idempotent path); (b) re-run `_manifest_adopted_by_another` as a fresh directory re-scan (adoption writes `adopted_from` on the ADOPTER's manifest, so only a directory re-scan can see it) - if it now names the run, refuse naming the post-check adoption. Other field drift between the two reads does not block the stamp. [class: IMPLEMENTATION_REQUIRED]

### Task 2 - Witness-arm documentation and the proactive probe

- [x] In `agents/skills/done/SKILL.md`, the Manifest disposition paragraph: amend the witness sentence "The operation's deliverables witness verifies every owned deliverable through its set-specific resolution" to name the three plan arms - "its set-specific resolution (an owned plan passes at its recorded path, its `plans_completed` archive twin at HEAD, or `HEAD:<recorded path>`)". [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/maintenance/SKILL.md`, the Interrupted-manifest classification arm bullet: append one sentence - before proposing any dead-root disposition, the arm probes the resolved lib for the `disposition-manifest` sub-command (for example via its help output) and reports a stale-deployment line naming the redeploy remedy when the sub-command is absent, instead of proposing a closure the deployed lib cannot run. [class: IMPLEMENTATION_REQUIRED]

### Task 3 - Suite arms and validation

- [x] In `scripts/test_done_sweep_gates_lib.py`: two arms - (a) a race arm seeding a dead-root manifest, hooking the write path (or seeding a competing manifest) so `complete` flips true between the initial read and the stamp, asserting refusal with the post-check finalize named and no `dispositioned` record written; (b) the done-skill and maintenance-skill anchor greps from the Validation Commands. [class: IMPLEMENTATION_REQUIRED]
- [x] Run every Validation Command below from the worktree root; each must pass against the amended tree. [class: REPOSITORY_TEST]

## Evaluation Criteria

- A concurrent finalize/adoption between check and stamp refuses the stamp with the racing shape named; no `dispositioned` record lands on an adopted or finalized manifest.
- The done skill names all three plan arms; the survey arm reports stale deployment proactively.
- The full lib suite passes with the new arm.

## Review Scope

Editable regions: `scripts/done_sweep_gates_lib.py` (the `_cmd_disposition_manifest` stamp path only), `agents/skills/done/SKILL.md` (the Manifest disposition paragraph's witness sentence only), `agents/skills/maintenance/SKILL.md` (the Interrupted-manifest classification arm bullet only), `scripts/test_done_sweep_gates_lib.py` (the new arms). Read-only: the origin backlog item; every other file.

## Validation Commands

Run from the worktree root; every check fails closed (a miss or an error aborts non-zero).

1. `grep -qF 'post-check finalize' scripts/done_sweep_gates_lib.py || { echo FAIL: CAS refusal missing; exit 1; }` - the CAS refusal exists (absent on main).
2. `grep -qF 'HEAD:<recorded path>' agents/skills/done/SKILL.md || { echo FAIL: third arm undocumented; exit 1; }` - the witness sentence names all three arms.
3. `grep -qF 'stale-deployment' agents/skills/maintenance/SKILL.md || { echo FAIL: proactive probe missing; exit 1; }` - the survey arm's probe is pinned.
4. `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -q || { echo FAIL: suite; exit 1; }` - the full suite including the race arm.
5. `bash scripts/check-no-em-dash.sh added-lines --base main || { echo FAIL: em dash; exit 1; }` and `bash scripts/scan-public-hygiene.sh || { echo FAIL: hygiene; exit 1; }` - both exit 0.
