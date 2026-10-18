# Backlog: advisory guard-ledger appends repeatedly block done closeout

- **Filed:** 2026-10-08, operator-directed
- **Status:** deferred (2026-10-09, operator routing: disposition rides the closeout-gate demotion program in docs/history/backlog/2026-10-08-done-closeout-ceremony-friction.md; warning-only conversion of post-landing-staging (2 catches / 5 incidents in scripts/gate_liveness_ledger.json) removes the blocking shape; advisory-append classification re-judged after conversion)
- **Workflow:** backlog
- **Priority:** high
- **Cluster:** docs/history/backlog/2026-10-08-done-closeout-ceremony-friction.md
- **Origin class:** witnessed recurring closeout friction
- **Class:** fix-class
- **Skill/step:** `agents/skills/done/SKILL.md`, Step 7 ledger duty and pre-commit `post-landing-staging`; `scripts/gate_liveness_ledger.py`
- **Driving force:** simplicity + reliability
- **Related work:** `docs/history/backlog/2026-10-08-done-closeout-ceremony-friction.md`; `docs/history/backlog/2026-10-06-done-closeout-cost-and-skill-scope.md`

## Problem

The Step 7 guard-liveness duty appends advisory records to one shared tracked JSON file after closeout work. A later or concurrent run sees that file as baseline dirt. The post-landing staging gate refuses closeout while any such path is peer-live, and the shared JSON cannot be staged by row. Records then accumulate across sessions, repeatedly blocking otherwise unrelated local commits. This occurred across multiple October 8 closeouts; the current worktree carries additional ledger rows from the same pattern.

The refusal preserves peer data while its owner may still be writing. Its cost is that completed advisory records remain coupled to every later closeout until an operator can safely land the whole file. The broad closeout-friction entry records other ceremony costs but does not decide whether this specific shared-file coupling and blocker should remain.

## Evidence

- `scripts/gate_liveness_ledger.json` contains dated incident rows for the repeated ledger-residue refusals and the recovery cost. The broader closeout-cost backlog already prices one ledger-related closeout delay at 25 minutes (`docs/history/backlog/2026-10-06-done-closeout-cost-and-skill-scope.md`).
- The October 8 closeout record re-derived for this entry reports the `post-landing-staging` refusal, explains why the dead-residue escape and probe-then-reland did not apply, and confirms row-level pathspec separation is impossible because all rows share one JSON file.

## Expected

Choose the smallest policy that prevents data loss while letting completed advisory records stop blocking unrelated commits. Evaluate all of these arms:

- Remove the post-landing blocker for the advisory ledger path; preserve the recorder's evidence, but allow its tracked edit to ride a later commit.
- Narrow the gate so it refuses only when the path is demonstrably being written by a live peer, then provide a recovery arm for completed rows after that writer closes.
- Keep the blocker and change the write/landing shape so independent session records do not share one path that must be claimed as a unit.
- Remove or narrow the Step 7 tracked-file append if the current prove-first decision process does not need a durable row for every firing.

Price each arm against actual catches, incidents, known time lost, and the concrete data-loss harm the gate prevents. Do not preserve the blocker only because it exists, and do not add another gate, ledger, or recovery ceremony to administer the choice.

## Immediate workaround

After re-deriving that the writer session is complete, no process still owns the append, and the merge lock is free, land the entire JSON as one focused local commit. Do not split or restore rows. Then rerun the blocked closeout's gates against the new tip and its own manifest before resuming that closeout.

## Deduplication

The existing closeout-ceremony friction entry covers manifest recovery, archive checks, and docs-branch dependencies. The completed closeout-cost plan evaluates general guard-stack value and records one 25-minute ledger-related refusal, but neither chooses a policy for this repeated advisory-append versus shared-file blocker interaction. This entry owns that narrower decision.
