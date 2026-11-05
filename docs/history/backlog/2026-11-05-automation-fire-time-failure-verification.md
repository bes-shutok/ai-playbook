Status: covered-pending-execution (docs/history/plans/2026-11-05-automation-fire-time-failure-verification.md)
Priority: high
Class: fix-class
Origin class: witnessed defect (2026-11-05 cross-session learn+investigate harvest over the 24h runtime telemetry)
Cluster: docs/history/backlog/2026-11-04-clocked-order-fire-launch-leg-residual.md (same defect class: a fired carrier strands silently at the fire boundary; that row owns the chain fire path, this row owns the runtime scheduler carrier)

# A one-shot carrier that dies at fire time leaves no failed-fire record and no post-fire verification

## Problem

A scheduled one-shot maintenance carrier fired 2026-11-05 02:00 UTC and its first provider request failed with a non-retryable provider business error (quota exhausted); the turn died at 02:00:11Z and the session deactivated at 02:00:12Z. The payload never executed. Nothing recorded the death: no bounded repair, no park-for-operator surface, no post-fire liveness verification anywhere in the workflow. The armed record and the runtime memory index still carry the scheduled framing ("fires at 02:00") with no correction leg, so every later session reading them must re-derive from raw telemetry that the fire failed. Runtime telemetry for 2026-11-04/05 shows the same quota-at-fire failure shape recurring (a second carrier-class failure the same night), so this is a standing gap, not a one-off.

## Observed vs expected

Observed: fire-time death is invisible outside hand-reading runtime logs; armed records go stale while implying a pending execution; a same-mandate loop carrier that did execute is discoverable only by accident.
Expected: a fired carrier's outcome is recorded by a verification surface (a post-fire liveness read); a dead fire lands as an explicit failed-fire record with its error class; a stale armed record is corrected or reported instead of silently implying pending execution; a duplicate-carrier overlap is reported when detected post hoc, without reintroducing the operator-rejected pre-fire duplicate-lookup doctrine (operator standing doctrine: repeated ask = create fresh carrier, no deconfliction unless asked).

## Evidence (trimmed)

- 2026-11-05 02:00:09Z carrier session start; 02:00:10Z first provider request; 02:00:11Z request failed, provider reason invalid_request, statusMessage exceed quota limit, retryable false, attempt 1 of 11 never retried; 02:00:11Z turn.failed; 02:00:12Z session deactivated. The armed prompt payload (auth-mode maintenance mandate) never ran.
- The armed record and the memory index entry written at scheduling time (2026-11-04 21:24Z) still describe the carrier as scheduled-not-executed; no mechanism flags the outcome.
- Sibling class witnesses: `docs/history/backlog/completed/2026-10-18-clocked-order-discharged-order-silent-strand.md` (the silent-strand class home) and the open Cluster sibling (the chain fire path's discharge-without-launch-receipt shape).

## Suspected root area

The scheduling workflow's fire leg owns arming but nothing owns post-fire verification: `agents/skills/maintenance/scheduling.md` and the payload conventions the scheduling sessions follow. The verification surface is new machinery and enters warning-only per the repository guidelines' Machinery admission protocol: incident (this row), expected catch frequency (nightly carrier fires against a quota-walled provider account; two dead fires in the 24h window), false-positive cost (a liveness probe misreading a slow live run as dead, bounded by reading session lifecycle events rather than process state), sunset/review (review by 2026-12-05; promotes only on a true catch with a pre-registered registry-removal row).

## Ship when

A dead fire produces a durable failed-fire record (and a stale armed record is either corrected or reported by a later maintenance turn), demonstrated warning-only first; the fire path still never takes a pre-fire duplicate-lookup step; the pins suite and hygiene scan stay green.
