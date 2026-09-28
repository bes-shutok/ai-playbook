Status: open
Priority: high
Workflow: backlog
Class: automation
Driving force: reliability
Origin class: witnessed-incident (the 2026-09-29 interrupted closeout 20260929T023532Z-3fb1c11bb98b, the stranded-captures landing ee0b2e15, and the same-run lock recovery; user direction: collect ideas on how to avoid such things)

# Interrupted-run and stranded-work prevention: idea set

## Problem

Three failure classes were witnessed within one day, each leaving work stranded or noisy for later sessions:

1. Teardown before closeout: an execution run deleted its worktree before its closeout done finalized, so the run manifest stayed complete=false while bound to a root digest that no longer exists. The signal is permanently unadoptable and every later Step 0 re-reports it as an interrupted run that no tooling may resolve.
2. Killed sessions strand finished work: an app restart killed a session with two finished, uncommitted backlog captures; they waited 13 hours for a human to notice, verify, and land them.
3. One-shot shell lock handling: an acquire's token exports died with the acquiring shell call, the release failed, and the subsequent stale-clean removed the caller's own still-live run lock (its holder PID was unpinned, so the run looked like a dead holder) before the correct namespace-scoped clean ran.

A related class, the maintenance loop staying dark for roughly half a day after a parked-primitive re-arm, is already owned by the landed maintenance-autonomous-pipeline plan's stall-recovery tasks and is not duplicated here.

## Observed versus expected

- Observed: closeout ordering is convention, not gate; orphaned manifests have no disposition path, so the advisory repeats forever; finished captures live only in a dead session's working tree until a human triages them; lock-token durability depends on the caller remembering two disciplines (pin the holder PID, retain the exports) with no mechanical guard.
- Expected: each failure gets a mechanical prevention or a self-recovery path, so a killed or interrupted session leaves either nothing stranded or a machine-actionable resume record.

## Prevention ideas

- A. Closeout-before-teardown gate: the worktree closeout duty refuses worktree and branch removal while any run manifest with complete=false binds the worktree's root digest; the worktree-first standard's transfer-out step gains the ordering explicitly (verify manifests, finalize or adopt first, then remove). Extends the worktree-closeout-baseline-capture item's surface.
- B. Disposition record for orphaned manifests: a sanctioned way to close an unadoptable manifest, a finalize variant accepting a verified-deliverables witness (each owned plan, review, and owned path checked landed), or a disposition sidecar the Step 0 reader honors. The report then reads "dispositioned: work verified landed, owner root gone" instead of re-reporting an interruption forever.
- C. Done-tail resume carrier: extend the standing budget-gate resume watcher to the done workflow's critical tail (the span between write-manifest and finalize), so an interrupted closeout relaunches itself at the next quota window instead of waiting for a human.
- D. Survey arm for unfinished manifests: the maintenance loop's Step 1 classifies complete=false manifests by root liveness; a live root proposes a resume dispatch (parked like other intents), a dead root proposes the B disposition once. This replaces the perpetual advisory with a machine-actionable record.
- E. Same-turn commit duty for backlog captures: generalize the rolling prompt log's rule (every write is committed in the same turn that performs it) to all backlog-file writes; a capture left uncommitted at turn end records a parked recovery note naming the file, so nothing finished sits silently in a working tree.
- F. Lock-token durability: one-shot shell callers pin the holder PID env to a long-lived process so dead-holder recovery cannot eat a live run's lock (the acquire command could detect the one-shot context and warn or refuse without the pin), and the acquire exports are recorded in the run manifest or session notes as a release backup. Extends the done-lock-one-shot-reclaim-releases-documentation item.

## Suggested fix

One plan, or folded tasks riding the maintenance-autonomous-pipeline plan's execution, in value order: B plus D first (cheap, kills the perpetual advisory and closes the witnessed incident class), then E (prevents the stranding at the source), then A (the gate), then C (self-recovery), then F (mechanical pin enforcement). Each idea cites its witness above; keep the additions witness-gated per the active-elimination doctrine, and delete this item's ideas that the pipeline plan's stall-recovery tasks already absorb when it executes.

## Environment

Witnesses: interrupted manifest 20260929T023532Z-3fb1c11bb98b (repo_root digest of a deleted worktree; refused by both adopt and finalize on 2026-09-29, disposition recorded in memory); stranded captures landed main ee0b2e15 after runtime verification; the lock recovery sequence (token loss, wrong-lock stale-clean, namespace-scoped merge clean) in the same session. Family: extends docs/history/backlog/2026-09-28-worktree-closeout-baseline-capture.md (facet A), docs/history/backlog/2026-09-28-done-manifest-root-identity-contract.md (facet B), docs/history/backlog/2026-09-28-done-lock-one-shot-reclaim-releases-documentation.md (facet F); loop darkness belongs to the landed maintenance-autonomous-pipeline plan.
