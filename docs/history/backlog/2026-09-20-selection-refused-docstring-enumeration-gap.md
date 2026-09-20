# Backlog: SelectionRefused exit-taxonomy docstring omits the different-successor refusal shape

Status: open
Workflow: backlog
Class: docstring completeness (comment-only, no behavior change)
Discovered: 2026-09-20, review r1 of `docs/plans/2026-09-19-scheduler-ops-contract-fix.md` (five-lens panel, documentation lens, deferred as Low)

## Finding

The `SelectionUsageError` docstring in `scripts/review_record_selection.py` (the "exit taxonomy, stated once" paragraph, around lines 106-110) enumerates the environmental `SelectionRefused` cases as "a missing or damaged record target, an orphaned half, and a differing digest without a decision", but `mark_superseded` also raises `SelectionRefused` for two shapes the enumeration omits: the different-successor re-mark refusal (the already-marked prior record re-marked for a different successor, the raise inside `mark_superseded`, previously around line 450) and the duplicate-marker / missing-Metadata-section record-repair refusals. The taxonomy paragraph claims to be exhaustive ("stated once") while listing only the `select` subcommand's refusal shapes.

## Driving force

The taxonomy paragraph exists so a reader can predict the exit code of every refusal from one place; an enumeration that silently covers one subcommand trains the reader to mistrust the paragraph (documentation accuracy at zero runtime cost).

## Fix shape

Extend the taxonomy paragraph's `SelectionRefused` list with the supersession-side shapes: the different-successor re-mark refusal, the duplicate-marker refusal, and the missing-Metadata refusal (one clause each, or reword to "covering the select-side overwrite-guard refusals and the mark-superseded-side repair refusals" plus the named shapes).

## Trigger

Next edit of `scripts/review_record_selection.py` for any reason (docstring-adjacent change, new refusal shape, or the next review-address pass that touches the helper).
