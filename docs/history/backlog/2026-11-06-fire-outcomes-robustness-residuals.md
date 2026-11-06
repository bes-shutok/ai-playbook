# Backlog: maintenance_fire_outcomes.py robustness residuals

Driving force: reliability (residual code-quality findings from the 2026-11-06 automation-fire-time-failure-verification Task 1 intermediate review; all low, non-blocking, warning-only surface, so they do not block that plan's landing).

Cluster: closeout-recovery

Findings captured (evidence in the run's implement-task-1.log.md and review round records):

1. Unescaped splice: the error class (`exceptionKind`/`reason`) is spliced into the pipe-delimited note/correction grammar unescaped in `scripts/maintenance_fire_outcomes.py` (record/append paths); a reason containing `|` or `=` corrupts the grammar (`parse_outcome_note` keeps the last duplicate key). Data comes from structured runtime attribution, limiting exposure.
2. Retention skip: `update_correction_status` rewrites an outcome note without re-applying the newest-30 retention, so an array already over cap stays over cap through status flips (out-of-band writers only).
3. Idempotency edge: after a `correction=done` flip, re-recording the identical terminal outcome returns unknown/conflicting instead of idempotent reuse (writer-managed status differs, outcome data identical); benign re-observations get a spurious conflict report.
4. Whole-document re-serialization: the "targeted" state edit re-serializes the whole state document with canonical formatting; byte-safe today, but a live file with divergent formatting would be reformatted wholesale.
5. Test naming accuracy: the state-side drift-retry coalesce leg is unwitnessed (index twin is exercised) while the module docstring claims both; the aged-out test name overclaims ("reports unknown" vs asserts empty report).

Accept when: escaping/normalization lands for grammar-bound fields, retention re-applies on every outcome-note write, the done-flip re-observation reuses idempotently, and the docstring/test names match witnessed behavior.

Phase 3 round additions (2026-11-06, correctness lens probe-verified, all low non-blocking):

6. Prefix-key match: the index "exact key" read is a startswith prefix match, so epoch-ms values of differing digit lengths can collide (practically unreachable pre-2001/post-2286).
7. Armed-target uniqueness is a bare substring test (`automation_id in line`), so any index line mentioning the id satisfies the append precondition.
8. Retention can prune a just-appended older outcome note while reporting "recorded (with retention prune)".
9. Atomic write leaves the target at 0600 (precedent: gate_liveness_ledger.py restores the target's mode).
10. Corrupt or missing state file escapes as a raw exception instead of a structured unknown report.
11. Status-flip rebuild drops note chunks without `=` (a value containing `|` truncates).
12. Informational: ATTRIBUTION_ALLOWLIST is documentation-only; find_armed_target unused; CLI exit codes asymmetric (read-outcome 0 on unknown vs record/append 1); append-only memory corrections unbounded (sanctioned by plan).
13. Contract residuals: new pin family is lane-blocking (PIN FAIL) where sibling families landed PIN-WARN warning-only (machinery-admission differential for the operator); sanctioned-writer enumeration at state-file.md line 13 lacks a clause for the outcome-note write and its prune; idempotency/retention parentheticals restated near-verbatim in survey-arms and state-file (drift held only by pins); drift-retry rule carries a third name variant.
14. Test residuals: live-digest guard order-dependent and three of four memory-index legs vacuous on this host; several negative arms untested (missing-event append no-write, update_correction_status ambiguous/absent/already arms, zero-armed-match, state drift-retry success path, retention tie/unparseable-key edges); unused LATE_FIRE_MS constant.
