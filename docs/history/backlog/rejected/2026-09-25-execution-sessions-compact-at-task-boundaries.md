# Execution sessions compact at task boundaries before context exhaustion

Status: rejected (2026-09-27; duplicate mechanism — superseded by the live 2026-09-27-compact-between-execution-runs-mechanism.md, whose 2026-09-26 witness established that no agent-invokable compaction primitive exists, refuting this item's "runtime session-compact" fix premise; this item's implementable residue — green commit plus manifest update at every task boundary so an auto-compaction lands on durable checkpoint state — is folded into that item's fix shape)

Priority: medium, class real.

On 2026-09-25 an interactive execution session ran its context to exhaustion
mid-turn and was continued by a machine summary; the continuation re-read files
and re-derived state that a durable checkpoint would have preserved, and the
summarized transcript briefly lost fine-grained execution state (validation
script paths, lock token handling). Related but distinct from
`2026-09-25-authoring-cycle-gate-auto-resume.md` (that item covers the
authoring-cycle pacing gate; this one covers execution-lane context hygiene).

Fix: teach the execute-plan skill (and the execution blueprint) a proactive
compaction duty: at each task boundary with a green commit, when remaining plan
work is non-trivial, the session compacts (runtime session-compact) after the
commit and the manifest update, so compaction happens at a durable checkpoint
instead of mid-task or at exhaustion; the manifest (workflow_state, task
checkboxes, execution record) is the resume source of truth, never the
transcript summary. Mirrors the execution blueprint's FINAL STEP compaction
duty but fires mid-run at boundaries, not only at end.

Non-goals: no change to review rounds or landing discipline; no automatic
compaction while a merge lock or landing critical section is held.
