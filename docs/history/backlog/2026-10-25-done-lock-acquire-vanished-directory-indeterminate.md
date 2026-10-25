# Backlog: done-lock acquire reports indeterminate when the lock directory disappears after contention

- **Filed:** 2026-10-25, observed during a closeout setup
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** user-witnessed execution friction
- **Class:** fix-class
- **Driving force:** efficiency + simplicity
- **Skill/step:** `scripts/done-lock.sh` `acquire` and `wait-acquire` refusal classification

## Problem

An acquire attempt can lose `mkdir "$lock_dir"` while a peer still owns the lock, then reach `classify_held_outcome` after the peer has removed the directory. The classifier treats the absent directory as ambiguous and emits `OUTCOME: indeterminate`. An immediate `status` can then report the lock free. The closeout stops even though the existing atomic acquire operation can safely arbitrate a retry.

## Expected

When a failed atomic acquire is followed by an absent lock directory, retry the same atomic acquisition path within the existing wait attempt. If a peer recreated the directory, the existing held or ambiguous classification still decides the outcome; unreadable metadata and genuinely unadjudicable holder state remain `indeterminate`.

## Evidence

- `scripts/done-lock.sh` `try_acquire` uses `mkdir "$lock_dir"` as its atomic acquisition operation.
- `scripts/done-lock.sh` `classify_held_outcome` currently maps a missing directory to `ambiguous`.
- Observed 2026-10-25: a closeout setup returned an ambiguous-holder outcome, and a subsequent lock status read returned free.

## Suggested direction

Add one bounded retry through the existing atomic acquisition path when the failed attempt is followed by no lock directory. Keep all existing ambiguous-record refusals. Cover the race deterministically in the focused lock test.

## Source

- Current-session observation and the acquisition/classification code cited above.
