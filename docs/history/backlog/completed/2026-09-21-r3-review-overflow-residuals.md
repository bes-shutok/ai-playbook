# Backlog: state-durability r3 review overflow residuals (six candidates, four themes)

Status: done (2026-09-30; legacy origin fold completed post-execution: covered by docs/history/plans/completed/2026-09-27-deferred-residual-dispositions.md)
Priority: medium
Urgency remark: witnessed: payload-copy consume lifecycle gap on the live maintenance skill leaves stale copies
Promoted: 2026-09-26 from docs/history/backlog/deferred/ under the direction triage (source class: self-serving witnessed defect)
Origin: code review r3 of docs/plans/2026-09-21-scheduler-maintenance-state-durability.md, staging doc docs/reviews/2026-09-22-scheduler-maintenance-state-durability-code-review-r3.md, overflow manifest (per-worker non-blocking Low budget). All six are valid, verified, non-blocking.

## Theme 1: payload-copy consume lifecycle unbound (correctness-completeness, implementation#park-copy-identity)
The keyed-copy consume rule is bound to the Step 1 reader path only; every other clearer (writing duty same-session success, Step 0 recipe re-arm, memory-note path, watchdog recovery) clears the intent with no copy-deletion duty, and dispatched pending_dispatch copies have no consumer at all. Resolved intents leave stale keyed copies under docs/tmp. Candidate fix: extend the pairing rule with a copy-deletion duty for every clearer (same post-state-edit-survival ordering) and give dispatched parked targets a consume step in the Step 1 dispatch path.

## Theme 2: appendix wording residuals (correctness-completeness + risk, consistency#appendix-content-vs-literal + security#placeholder-normalization-unpinned)
The zcode recipe's r1 content span ("naming the lane the mode excludes") disagrees with the r2 pinned literal (names the lane the mode keeps): a builder following the prose produces an appendix the self-heal rewrites. Separately the literal pins the frame but not <directive> whitespace/newline normalization. Candidate fix: reword the content span to defer to the literal, and state the substitution normalization (trim, single line).

## Theme 3: attempt-bound predicate restated at four operative sites (design-simplicity, simplification#shrink)
The structured-first-line/defect-token/cadence predicate is spelled out in the Step 0 consultation clause, the structured-line sentence, the arm tail, and the rearm_note paragraph; a bound-semantics change edits four sites. Candidate fix: one named predicate (the live-bound condition) referenced by the other sites, on the file's named-condition precedent.

## Theme 4: loop-mode exclusion stated three times in one bullet (design-simplicity, simplification#shrink)
The Pending dispatch bullet states the exclusion in the gate, dispatch, and tail clauses; mode-semantics changes edit three clauses plus Step 3 plus the successor condition. Candidate fix: name the exclusion once (the Step 3 loop-mode exclusion) and reference it.
