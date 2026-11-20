# Backlog: hook-timeout diagnostic plan carries fourteen non-blocking certification residuals

Status: open
Priority: low
Class: fix-class
Origin class: self-serving
Added: 2026-11-09, certification-round residuals of the hook-timeout diagnostic plan review
Driving force: efficiency

## Problem

The certified plan docs/history/plans/2026-11-09-hook-timeout-recurrence-diagnostic.md leaves refinements that its executor must apply, or its harness can misreport, abort spuriously, or touch live state:

- Safety witness: "one keying line per consult" fails on a resolver-failed consult, which appends the resolver's `no-anchor` line beside the core's own line. Count one core keying line (env-var or project-only) per consult.
- Timing emission: an unguarded write that fails after the decision makes the core exit nonzero, and the adapter's `|| core_out=""` then fail-opens a block into an allow. Make the write silent on failure, and add an unwritable-path witness arm.
- Dominance: the block class has one extra adapter stage, so per-class top stages can differ while both map to candidate (a). Let a candidate fire when both classes' dominants map to it.
- Hermeticity: `DEFAULT_RUNTIME_DIR` binds at import time, so in-process suite calls pass the runtime dir explicitly beside the HOME patch.
- Probe load: replication probes run alongside consults add load. Hold the probe protocol identical across baseline and narrowed runs, and record its cadence.
- Doctor token: the session-channel idiom token lives only in `claude.sh`'s header comment. Candidate (a) must keep a line that carries it.
- Low refinements: the regime claim names its timed-out count; the argv replica is updated before the efficacy re-run; environment-derived and flag-supplied keying branches are fixture-only labels; the note-arm byte check is relative to Task 2's end state; seed the sandbox with a facts file; loud-abort on an unmapped stage name; add Terms entries for narrow arm, note arm, and task log; a Task 1 item names the analyze mode; qualify the emission-off p95 as block-class; scope the floor phrase to the loaded repeats; spawn consults as their own process session and group; state the per-consult interpreter fan-out in the run context.

## Exact location

- `scripts/profile_skill_gate_consult.py` and `scripts/test_profile_skill_gate_consult.py`: the harness and suite the plan's Task 1 adds.
- `scripts/skill_gate.py`: the timing emission Task 1 adds.
- The plan's Terms and Tasks 1-3.

## Suggested fix

During the plan's execution, apply each bullet above at the task that owns it, before that task's RED step.

## Severity and source

Medium and Low, non-blocking: the r6 certification record `.ai-playbook/reviews/2026-11-09-plan-review-hook-timeout-recurrence-diagnostic-p7daeac52-r6.md`, findings F1-F14 and its five overflow items.

## Why not fixed now

Certification-round non-blocking findings never force a re-round or a plan fold (review-staging certification-residual routing); they belong to the plan's execution, which has not started.

Dedup probe: searched the open backlog corpus (filenames and bodies) for "hook-timeout", "skill-gate", "consult", and "profile_skill_gate_consult"; the only match is the plan's own origin row docs/history/backlog/2026-11-05-hook-timeout-recurrence-diagnostic.md, which owns the diagnostic's design, not these refinements. Distinct, so no merge.
