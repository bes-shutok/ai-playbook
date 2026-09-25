# Backlog: empty-digest exit-2 refusal is preempted by the orphan exit-1 refusal, making the exit code corpus-state-dependent

Status: open
Priority: medium
Urgency remark: witnessed: exit-code nondeterminism on live select_record, real caller-facing ordering bug
Promoted: 2026-09-26 from docs/history/backlog/deferred/ under the direction triage (source class: self-serving witnessed defect)
Workflow: backlog
Class: error-taxonomy determinism (both paths fail closed; only the exit code and message vary with unrelated corpus state)
Discovered: 2026-09-20, review r1 of `docs/plans/2026-09-19-scheduler-ops-contract-fix.md` (five-lens panel, robustness lens, deferred as Low)

## Finding

In `scripts/review_record_selection.py`, `select_record` runs the enumeration and the orphan-half refusal (previously around lines 257-265) BEFORE the empty-digest and malformed-digest usage checks (previously around lines 266-281). When the corpus holds an orphan half matching the slug, an invocation that also supplies an empty or malformed `--source-digest` exits 1 with the orphan message instead of exiting 2 with the digest message: the same caller mistake surfaces with a different exit code and a different diagnosis depending on unrelated corpus state. Both orders fail closed (no record is ever read or replaced on either path), so this is taxonomy determinism only, not a guard hole.

## Driving force

An exit taxonomy exists so callers can branch mechanically; a code that flips with corpus state forces callers to handle both codes for the same bug. Usage errors (invalid invocation input) are knowable before any filesystem state is consulted and are cheap to check first (simplicity and code quality at zero risk; both arms are pure string checks).

## Fix shape

Move the empty-digest and `SOURCE_DIGEST_PATTERN` usage checks (and, for symmetry, the slug grammar/length/backup-infix checks' relative position stays as is) above the enumeration/orphan refusal in `select_record`, so every exit-2 usage error is decided before any exit-1 environmental refusal; adjust the orphan test order expectation if any test pins the current precedence.

## Trigger

Next behavior-relevant edit of `select_record` in `scripts/review_record_selection.py`, or the next review-address pass that touches the helper's refusal arms (fold with the accompanying test-order tweak in `scripts/test_review_record_selection.py`).
