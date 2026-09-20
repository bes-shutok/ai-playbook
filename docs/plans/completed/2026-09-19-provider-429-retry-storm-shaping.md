# Plan: Provider 429 rate-limit retry storm shaping

Backlog origin: docs/history/backlog/2026-09-19-provider-429-retry-storm-shaping.md (stays in place while this plan is open).

## Terms

- **Rate pressure**: the rolling count of `rate_limited` events recorded for this repository within the last 24 hours (state-file `rate_limited_events` array; the count is `rate_pressure`).
- **Fan-out cap**: the maximum number of concurrent subagent launches one orchestrator keeps in flight; default 3, halved to a floor of 1 for the rest of a run after the run observes a rate-limited launch.
- **Throttle window**: the period after a rate-limited launch during which relaunch is barred; it ends when a launch attempt after the backoff succeeds, or at the next defined run boundary, whichever comes first, so "does not relaunch into the same throttle window" is checkable by reading the run's recorded stop-line timestamps against the relaunch time.
- **Re-queue**: the scheduler behavior for rate-limited work: the decided dispatch (or child target) is retained in `pending_dispatch` with reason `rate_limited` and retried next turn, instead of being lost or retried in-place.
- **`1302`**: the provider's retryable per-request rate-limit error (`Rate limit reached for requests`), distinct from the `[1308]` 5-hour usage quota already covered by the quota leg.

## Assumptions

- assume the repo-owned levers only: the runtime's retry attempt count (max 11) and its backoff policy are host-side and OUT of scope; this plan shapes fan-out, lane decisions, and re-queue telemetry, which this repository owns; basis: backlog item's suggested fix, items 1 and 3 (item 2's attempt-count half is host-side, its fail-fast-with-reason half is taken as the reporting contract below).
- assume the fan-out cap default is 3 concurrent subagent launches (the backlog's "modest static cap"), adaptive only downward (halve on observed rate-limited launch, floor 1); basis: backlog item's shaping option.
- assume the rate-pressure deferral threshold is 3 events in 24h; basis: the same "modest" principle applied to the lane decision.
- assume the run's existing gitignored context.jsonl telemetry (docs/plans/2026-09-19-context-budget-and-telemetry-long-running-skills.md, not yet executed) is NOT a dependency: rate-limited events are recorded in the scheduler state file and the execute-plan session manifest's free-text lines (the budget_skip precedent), which exist today; basis: keeps this plan independent of an unexecuted plan.
- assume `rate_pressure` is a this-repo-only lower bound on account-wide pressure (peer sessions' 1302 events are invisible to this state file); the fan-out cap still bounds this repository's own contribution, the dominant term on the witnessed spike; under-firing on peer-driven days is measured by the Ship-when friction-audit window; basis: review r1 residual acceptance.
- assume launch-kind ingestion can miss a run shorter than one read interval that completes successfully and deletes its session manifest before any turn reads it; the Task 2 structured `rate_limited` end-of-run report is the durable ingestion trigger for runs that end unarchived (the scheduler reads the report on the next turn); basis: review r2 residual acceptance.
Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the scheduler and the execute-plan orchestrator shape their fan-out and defer work on a measured rate-pressure signal, so the `external`-forced 1302 retry storms (2,473 events in 7 days, a 5,704-event spike on Sep 17) stop converting plan-tier throttling into 14-minute stalls and dead turns.

What changes: the scheduler state file gains a rolling `rate_limited_events` record and a `rate_pressure` count; the execution lane consults it before dispatching and defers at 3 events/24h (a sanctioned deferral, not a dispatch defect); execute-plan caps concurrent subagent launches at 3 (halving to 1 after a rate-limited launch) and reports a structured `rate_limited` reason on exhaustion; the Step 1 reader re-queues a rate-limited retained dispatch instead of losing it.

Example: Sep-17-style spike day: three children and a review panel collide, three launches return 1302; each is ingested as `{ts, kind: launch, target: <launch>}` into `rate_limited_events`, the run's fan-out cap halves to 1, and the turn ends with the decided dispatch retained in `pending_dispatch` and the `rate_limited` reason in `decision_reason`; the next turn's reader finds rate_pressure at 3, defers dispatch, and the queue drains after the spike passes instead of burning 11 retry attempts per request.

## Evaluation Criteria

**Quality dimensions:**
- correctness: a turn with rate_pressure at or above 3 defers execution dispatch with a recorded rate-pressure reason and no dispatch-defect `turn_error`; a turn below the threshold dispatches normally.
- correctness: a run observing a rate-limited launch halves its fan-out cap (floor 1) and does not relaunch into the same throttle window.
- observability: every rate-limited event lands in the state file with a timestamp; the re-queue is visible in `pending_dispatch` and `decision_reason`.
- independence: no runtime or host-side retry policy change is assumed.

**Done when:**
- All Task greps pass (fail-closed, per Validation Commands).
- Each task commit touches exactly its declared Files list plus this plan's checkbox marks (witnessed by the commit-scope gates); concurrent peer commits on the shared branch are outside this plan's Done-when by construction.

**Ship when:**
- [class: OPERATIONS_FOLLOW_UP] A 7-day post-deployment log window shows the backlog acceptance profile (no queryId burned to the attempt tail attributable to this repo's fan-out; spike days without multi-minute stalls); evidence owner: Andrey via the friction-audit lane; closure: the next cross-session friction audit records the improvement or the residual.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/SKILL.md` (state-file schema: `rate_limited_events`; Step 1 pending-dispatch reader: rate-limited re-queue; Step 3 D1: rate-pressure deferral; Step 6 writer classes)
- `agents/skills/execute-plan/SKILL.md` (fan-out cap section and structured rate-limited reporting)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed.

**Out of scope; reject unless plan-related:**
- `scripts/quota_window_probe.py` and the quota leg; reason: `[1308]` usage-quota shaping is a separate, already-covered axis.
- The host runtime's retry policy and attempt counts; reason: host-side, not repo-owned.
- `agents/skills/maintenance/zcode.md`; reason: no new runtime primitive is required (the state file and skill text carry the whole mechanism).

## Validation Commands

```bash
set -u
cd "$(git rev-parse --show-toplevel)"
MAINT=agents/skills/maintenance/SKILL.md
EXEC=agents/skills/execute-plan/SKILL.md
PLAN=docs/plans/2026-09-19-provider-429-retry-storm-shaping.md
fail() { echo "GATE FAIL: $1" >&2; exit 1; }

# Task 1 gates: state schema, D1 deferral, reader re-queue, writer classes.
grep -q "rate_limited_events" "$MAINT" || fail "state schema field missing"
grep -q "rate_pressure" "$MAINT" || fail "rate-pressure count missing"
grep -q "defers execution dispatch" "$MAINT" || fail "D1 deferral missing"
grep -q "rate-pressure reason" "$MAINT" || fail "sanctioned deferral reason missing"
grep -q "retained in .pending_dispatch. with reason .rate_limited." "$MAINT" || fail "reader re-queue missing"

# Task 2 gates: fan-out cap, adaptive halving, structured reporting.
grep -q "concurrent subagent launches" "$EXEC" || fail "fan-out cap missing"
grep -q "halves its fan-out cap" "$EXEC" || fail "adaptive halving missing"
grep -q "does not relaunch into the same throttle window" "$EXEC" || fail "no-relaunch clause missing"
grep -q "structured .rate_limited. reason" "$EXEC" || fail "structured reporting missing"

# Keep-green regression witness: the maintenance pins suite stays green over the schema addition.
bash scripts/check_maintenance_pins.sh || fail "pins suite drifted"

# Commit-scope witness (BASE recorded before the first commit; declared lists include this plan).
BASE="$(cat docs/tmp/r429-base-sha.txt)"
commit_scope_ok() {
  subj="$1"; shift
  c="$(git log -F --grep="$subj" --format=%H "$BASE"..HEAD | tail -1)"
  test -n "$c" || fail "task commit missing: $subj"
  for f in "$@"; do
    git show --name-only --format= "$c" | grep -qxF "$f" || fail "commit $c missing declared file $f"
  done
  EXTRA="$(git show --name-only --format= "$c" | grep -v '^$' | grep -vxF -f <(printf '%s\n' "$@") || true)"
  test -z "$EXTRA" || fail "commit $c touches undeclared files: $EXTRA"
}
commit_scope_ok "maintenance: rate-pressure signal and deferral" "$MAINT" "$PLAN"
commit_scope_ok "execute-plan: fan-out cap and rate-limited reporting" "$EXEC" "$PLAN"
```

Gate provenance: every new-string gate is RED today (none of the strings exist in the two target files; first gate measured firing with exit 1 at authoring) and flips GREEN exactly when the tasks land; each gate needle is a contiguous span of its task bullet's prescribed text; the pins-suite invocation is a keep-green witness, GREEN today and required to stay GREEN (the schema addition moves no pinned literal); the commit-scope gates run last, require BASE (recorded before Task 1's commit) plus the two landed commits, and measure committed history by subject, never working-tree state.

### Task 1: Scheduler rate-pressure signal, deferral, and re-queue

Files:
- `agents/skills/maintenance/SKILL.md`

- [x] Before the first commit, record the current HEAD sha to `docs/tmp/r429-base-sha.txt` (one line, `git rev-parse HEAD`); the commit-scope gates read it as BASE. [class: IMPLEMENTATION_REQUIRED]
- [x] Add `rate_limited_events` to the state-file schema documentation block (top-level array, each entry `{ts, kind, target}`, `kind` one of `turn` or `launch`, capped at 20 entries oldest-evicted) and the derived `rate_pressure` count (entries within the last 24 hours); note it is additive under schema 3; add the append to the sanctioned writer-classes list AND to the Step 6 whole-document-rewrite carry-forward list so the rewrite cannot drop it. [class: IMPLEMENTATION_REQUIRED]
- [x] Name the writers and triggers: the Step 1 child-outcome check appends a `turn`-kind entry when it observes a surfaced 429 rate-limited stop on a child (the failure-detection section already reads exactly this stop evidence), and, on the same read-back, appends `launch`-kind entries for rate-limited stop lines found in the pending child's execute-plan session manifest's free-text lines (the budget_skip precedent for session-manifest free-text), so every scheduler turn while the child is pending ingests them. [class: IMPLEMENTATION_REQUIRED]
- [x] Extend Step 3's `D1 (execute)` bullet with the rate-pressure deferral: when `rate_pressure` is at or above 3, the turn defers execution dispatch, writes the decided dispatch to `pending_dispatch` (`kind`, `target`, `payload_slug`, `decided_at` per the existing field paragraph, mirroring the decided-but-could-not-schedule writer semantics), and records the deferral with a rate-pressure reason in `decision_reason`; the deferral is a sanctioned reason in the must-dispatch exemption list (no dispatch-defect `turn_error`), alongside the existing guard, quota, and dependency reasons (the external-gate reason joins this list when the park-guard plan lands). [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the Step 1 pending-dispatch reader: a target retained from a turn that ended rate-limited is re-dispatched when valid (the existing validation applies) and, when the deferral condition still holds, is retained in `pending_dispatch` with reason `rate_limited`, so the decided work is never lost to a throttle window. [class: IMPLEMENTATION_REQUIRED]
- [x] Witness: the deferral fires at exactly the threshold (a state with 3 events in 24h defers; with 2 it dispatches; this threshold semantics is a prose obligation verified by review reading, not by a grep) and the exemption list sentence names the rate-pressure reason; the text-presence obligations each have their own Validation Commands needle. [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: rate-pressure signal and deferral` [class: IMPLEMENTATION_REQUIRED]

### Task 2: execute-plan fan-out cap and structured reporting

Files:
- `agents/skills/execute-plan/SKILL.md`

- [x] Add a fan-out shaping rule to the orchestration guidance: the parent keeps at most 3 concurrent subagent launches in flight (review panels and batch implement launches included); after a launch fails with a retryable rate-limit error, the run halves its fan-out cap for the rest of the run (floor 1) and does not relaunch into the same throttle window: the launch is recorded as a rate-limited stop line in the execute-plan session manifest's free-text lines (the budget_skip convention, not the driver-owned runtime_state.json), and the run resumes the launch after a backoff or at the next defined boundary. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the structured reporting contract: when a run cannot proceed because of rate limiting, it ends with the plan unarchived, the machine manifest left active, and the report naming a structured `rate_limited` reason (so the scheduler's re-queue semantics and post-mortems see it), never with a generic failure. [class: IMPLEMENTATION_REQUIRED]
- [x] Witness: the cap default (3), the halving (floor 1), and the structured reason each have a dedicated needle, and the no-relaunch clause has its own dedicated needle. [class: REPOSITORY_TEST]
- [x] Commit: `execute-plan: fan-out cap and rate-limited reporting` [class: IMPLEMENTATION_REQUIRED]
