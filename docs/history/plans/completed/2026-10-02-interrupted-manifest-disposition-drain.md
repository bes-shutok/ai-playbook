# Interrupted-manifest disposition drain in the maintenance turn

Origin (scope of record): `docs/history/backlog/2026-10-01-interrupted-manifest-disposition-drain.md`

Classification: [class: fix-class] skill prompt change (two skills' procedure text; no script code change).

## Terminology and core concepts

- **Dead-root manifest**: an interrupted run manifest whose recorded root digest names a checkout that no longer exists on disk; unadoptable by construction, closed only by the done skill's `disposition-manifest` procedure.
- **Executing arm**: the upgrade of the maintenance survey's interrupted-manifest classification from propose-only to propose-plus-execute for dead-root manifests in the same turn; live-root manifests stay proposal-only.
- **Bounded census**: a count assertion on the dead-root classification output that turns an unbounded pile into a visible failure instead of a silent backlog.

## Evaluation Criteria

- The maintenance survey arm's dead-root clause directs executing the disposition closure in the same turn for each dead-root manifest whose deliverables witness passes, recording receipts, and reporting (never forcing) a witness failure.
- Live-root proposals are unchanged in kind: adoption, finalize, and the resume continuation remain explicit continuations, never executed by the survey arm.
- The bounded census gives the dead-root pile a visible ceiling; crossing it is reported as a turn-blocking error naming the census, not silently absorbed.
- The done skill's disposition paragraph names the maintenance arm as the executing consumer while keeping operator-directed closure as the procedure of record.

## Review Scope

- `docs/history/plans/2026-10-02-interrupted-manifest-disposition-drain.md`
- `agents/skills/maintenance/SKILL.md` (the interrupted-manifest classification arm; the execution-discipline text that consumes survey output)
- `agents/skills/done/SKILL.md` (the Manifest disposition paragraph's cross-reference sentence)
- `docs/history/backlog/2026-10-01-interrupted-manifest-disposition-drain.md`

## Validation Commands

```bash
grep -c "executes the disposition closure" agents/skills/maintenance/SKILL.md
grep -q "bounded census" agents/skills/maintenance/SKILL.md
grep -q "witness failure leaves that manifest" agents/skills/maintenance/SKILL.md
grep -q "executing consumer" agents/skills/done/SKILL.md
grep -q "the same turn executes the disposition closure" agents/skills/maintenance/SKILL.md
bash scripts/check_maintenance_pins.sh
bash scripts/check-no-em-dash.sh added-lines --base main
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

## Tasks

### Task 1: the executing arm in the dead-root clause

Files:
- `agents/skills/maintenance/SKILL.md`

Evidence:
- `grep -c "executes the disposition closure" agents/skills/maintenance/SKILL.md` returns at least 1
- `grep -q "witness failure leaves that manifest" agents/skills/maintenance/SKILL.md`

- [x] Run -> expect RED: both Evidence greps miss (count before editing) [class: REPOSITORY_TEST]
- [x] In the survey's interrupted-manifest classification arm, extend the dead-root sentence: after the existing proposal of the disposition closure, the same turn executes the disposition closure for each listed dead-root manifest by following the done skill's disposition paragraph as the procedure of record (resolve the lib exactly as that paragraph directs, run the `disposition-manifest` invocation for the manifest's run id, and record each printed `dispositioned` receipt in the session notes beside the manifest reference); a witness failure leaves that manifest untouched for operator direction and is reported in the turn output naming the manifest and the failing deliverable, never forced; a live-root manifest stays proposal-only (adoption, finalize, and the resume continuation remain explicit continuations the survey arm proposes but never executes); the arm's read-only character is narrowed to exactly this executing exception: it mutates nothing but the dead-root dispositions it executes through the sanctioned procedure; the arm's existing stale-deployment probe sentence is reworded in the same edit so its tail reads "instead of executing or proposing a closure the deployed lib cannot run" (the propose-only tail goes stale once the arm executes) [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect GREEN: both Evidence greps [class: REPOSITORY_TEST]
- [x] Commit: `skills: maintenance executes dead-root manifest dispositions` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the bounded census on the dead-root pile

Files:
- `agents/skills/maintenance/SKILL.md`

Evidence:
- `grep -q "bounded census" agents/skills/maintenance/SKILL.md`

- [x] Run -> expect RED: the Evidence grep misses [class: REPOSITORY_TEST]
- [x] In the same classification arm, after the executing-arm sentence, add the bounded census: the arm counts the dead-root manifests it classified, and when the count exceeds ten the turn reports the dead-root census as a blocking condition through the survey's existing `turn_error:` escalation channel, naming the count, the oldest manifest's age, and the drain instruction, instead of proceeding to execute an unbounded pile silently (ten is the ceiling the origin's witnessed 44-manifest pile shows a queue can reach when the drain is absent; a census at or under ten proceeds with the same-turn drain normally); the census is a report over the classification output the arm already has, so no new discovery surface and no driver change [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect GREEN: the Evidence grep [class: REPOSITORY_TEST]
- [x] Commit: `skills: bounded census gates the dead-root manifest drain` [class: IMPLEMENTATION_REQUIRED]

### Task 3: the done skill's cross-reference names the executing consumer

Files:
- `agents/skills/done/SKILL.md`

Evidence:
- `grep -q "executing consumer" agents/skills/done/SKILL.md`

- [x] Run -> expect RED: the Evidence grep misses [class: REPOSITORY_TEST]
- [x] In the Manifest disposition paragraph, update the cross-reference sentence near the paragraph's end: the maintenance survey's interrupted-manifest classification arm is the executing consumer of this paragraph for dead-root manifests (it runs this procedure in the same turn it proposes the closure, per its bounded-census gate), while operator-directed closure remains available at any time through this paragraph's own invocation; the sentence keeps naming this paragraph as the procedure of record so the maintenance arm and an operator direction resolve to the identical steps [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect GREEN: the Evidence grep [class: REPOSITORY_TEST]
- [x] Commit: `skills: disposition paragraph names the maintenance executing consumer` [class: IMPLEMENTATION_REQUIRED]

### Task 4: full-suite validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block; covers the executing arm, the census, the cross-reference, and the untouched pins baseline

- [x] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]

## Assumptions

- Only the two skill files change; the disposition operation itself (`done_sweep_gates_lib.py disposition-manifest`) and the survey's discovery surface (`list-interrupted-manifests`) already exist and are exercised as-is.
- The ten-manifest census ceiling is a prompt-level constant, not a script flag; a future drift files a backlog item rather than re-parameterizing the lib.
- The pins suite pins no literal inside the edited sentences (verified at authoring time against `scripts/check_maintenance_pins.sh`); any pin collision surfaces at Task 4 and is resolved by rewording, never by editing the pin.
