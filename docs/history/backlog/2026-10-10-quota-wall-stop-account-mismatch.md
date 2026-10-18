# Backlog: record the account-mismatch quota-wall stop as a false stop signal

- **Filed:** 2026-10-10, operator correction on resume
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** operator-caught misattribution in an exec lane stop record
- **Class:** record-class

## Observed vs expected

Observed: the review-loop-round-budget exec lane (sess_2ab595f1) stopped 2026-10-10 at a worker dispatch refusal reading "Usage limit reached for 5 hour. Your limit will reset at 2026-10-11 03:25:11", and the stop state (session manifest progress record + memory index entry rlrb-exec-cycle-inflight-quota-wall-20261010) recorded it as a genuine quota wall. The operator corrected on resume: the limit belonged to a DIFFERENT account than the one this session runs on, so the refusal was not a stop signal for this session at all.

Expected: durable stop records should not carry a misattributed cause uncorrected. The manifest progress record and the memory entry should be annotated (not rewritten) to note the account mismatch, and the quota-wall-dispatch-doctrine threshold ("hour-or-more usage wall") should note that a wall message must be attributed to the session's own account before it counts as a stop trigger.

## Suggested direction

Fold the attribution check into the quota-wall dispatch doctrine's stop-handling arm: on a usage-limit refusal, verify the limit belongs to the dispatching account before recording a quota-wall stop or arming a timed resume; if attribution cannot be established, record the stop as "cause unverified" rather than "quota wall". Annotate the 2026-10-10 rlrb stop records with the mismatch.
