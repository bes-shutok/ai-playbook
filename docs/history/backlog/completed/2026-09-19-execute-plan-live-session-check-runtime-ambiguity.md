# Backlog: execute-plan live-session check has no runtime-defined mechanism (process-table scan confusion)

Status: done 2026-09-21 (fixed by docs/plans/completed/2026-09-19-scheduler-ops-lanes-durability.md; executed clean: 7 tasks, phase 3 r1-r3 clean exit)
Priority: medium
Origin: 2026-09-19 maintenance turn (user directive: run execute-plan for urgent plans one by one). While resuming `docs/plans/2026-09-16-review-records-contract.md`, the orchestrator had to answer "is a peer session live?" and found no defined mechanism, so it scanned the host process table (`ps aux | grep codex|claude`) and found a live Codex session — the user then asked why a ZCode session was grepping for Codex.

## Problem

The execute-plan skill and the maintenance skill both require a **live-session / discovery check** before taking over or duplicating in-flight work:

- execute-plan Step 3.1 timeout and the maintenance G1e "Discovery arm" both name "the execute-plan claim check via the mechanism named in the runtime overlay, or active child session traces on the checkout" — but for the ZCode runtime the overlay names no concrete mechanism, and runs that deliberately skip the machine manifest (`runtime_state.json`) in favor of manifest.md-only orchestration (recorded deviation in this very run) have **no claim check at all**.
- The durable signals that actually exist are runtime-neutral: the session manifest heartbeat (`docs/tmp/execute-plan/<slug>/manifest.md` `updated:` and `review-r<N>.log.md` mtime), the presence/absence of the expected staging doc, and the git reflog of the run branch. A process-table scan is a proxy: ambiguous (a Codex *app* running says nothing about a session working this repo), host-wide rather than repo-scoped, and confusing to the user (a ZCode agent apparently "checking Codex").

## Requested change

1. Define, in `agents/skills/execute-plan/` (and mirrored in the maintenance skill's Discovery arm), a repo-scoped liveness ladder that needs no process scan:
   - first: driver claim check (`runtime_state.json`) when a machine manifest exists;
   - second: session-manifest heartbeat freshness (manifest.md / review log mtime within the Step 3.1 20-minute window) plus staging-doc presence;
   - last: only if those are absent, the process scan — and when it is used, the skill should instruct the agent to *state the reason* ("no repo-scoped liveness signal exists for a manifest-only run") so the check is self-explaining.
2. In `agents/skills/execute-plan/zcode.md` (runtime overlay) pin the ZCode discovery mechanism explicitly, the same way the maintenance overlay pins scheduling primitives.
3. Consider recording in the manifest-only deviation note that it costs the run its claim check, so future runs weigh that tradeoff explicitly.

## Why not fixed now

Maintenance turn was instructed to run executions only; authoring the skill/overlay change needs its own certified plan. The live-session confusion was resolved conservatively this turn (stand down from the peer-owned run and monitor its heartbeat) without the fix.
