# Plan-delta classifier refuses content-shaped plan edits (excluded-region + non-exempt classes)

Origin class: consumer-pet
Driving force: automation
Cluster: docs/history/backlog/2026-10-16-corrections-chain-unclassified-mechanical-hops.md (same surface: the plan-delta classifier's class taxonomy refusing legitimate hop shapes)
Status: open
Priority: low

The plan-delta classifier (`scripts/plan_delta_classifier.py`) only script-verifies
edits whose hunks fall in the exempt classes (checkbox marker flips, whitespace,
typography) and whose changed bytes lie outside excluded regions (fences, inline
code spans, link destinations). A mechanical acceptance-criterion split required
by the execute-plan seeding boundary's evidence limits (a non-blank line replaced
by several, containing inline code spans such as `pre_restart:`) is therefore
never script-exempt and always takes the operator-acked path with a classifier-gap
backlog row, even when the edit is behavior-preserving.

Witness: 2026-10-10 execution of docs/history/plans/2026-10-08-quota-wall-dispatch-doctrine.md,
Phase 0 seeding refusal (task-1 criterion 828 UTF-8 bytes over the 512 limit);
classifier refusal "hunk(s) not exempt: the changed bytes lie inside an excluded
region".

Suggested direction: consider a dedicated exempt or classified class for
evidence-limit-driven criterion splits verified by a coverage checker (before
criteria are a subset of after criteria modulo sentence boundaries), so the
common re-seed loop stops consuming an operator ack per run.
