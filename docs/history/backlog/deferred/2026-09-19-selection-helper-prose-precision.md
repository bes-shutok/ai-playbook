# Backlog: selection-helper prose and message precision (small polish batch)

Status: closed (2026-10-01 triage, operator adjudication "follow row contracts"; completed by other work, completion receipts below)
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; docstring/message/exit-taxonomy precision. Revive on a witnessed operator misdirection by one of the messages, or a project-priority-profile change.)
Severity: Low
Origin: r4 code-review round of the review-records-contract execution (2026-09-19), staged finding F5 and overflow items (design-simplicity, risk); staging doc `docs/reviews/2026-09-16-review-records-contract-code-review-r4.md` (gitignored); capture hygiene: scan-public-hygiene --files pass (2026-09-19)

## Problem

Small precision items in `scripts/review_record_selection.py` and one backlog note: (a) `SelectionUsageError` docstring says "invalid argument (exit 2)" but three non-argument uses exist (symlinked prior, unclosed fence, backup-name collision); (b) the F9 backlog note (`2026-09-19-scanner-allowlist-glob-single-source.md` line ~12) overstates the absolute-spelling shape: absolute spellings of root LICENSE.txt are EXCLUDED in files mode (the `*/LICENSE.txt` case pattern matches across slashes); only the bare root-level relative spelling is scanned; (c) an empty/whitespace `--source-digest` exits 1 while every other malformed digest exits 2 (taxonomy inconsistent; both fail closed); (d) the slug error message claims "no '..'" while `a..b` is accepted (no separator possible in the grammar).

## Fix shape

Broaden the docstring; drop the parenthetical in the F9 note; raise the empty-digest refusal as a usage error (exit 2) or document the split; reword the slug message to "no path separators". All fail-closed today; polish only.

## Trigger

The next edit to the helper's error paths or the allowlist backlog item's consumption.

## Completion receipts (2026-10-01)

All four sub-items are landed by other work, verified on the current tree: (a) the SelectionUsageError docstring now reads "An invalid invocation, or an unusable target/state that is the caller's to repair (exit 2)" and enumerates the environmental raise sites (scripts/review_record_selection.py around lines 95-110); (b) the F9 backlog note's overstated absolute-spelling parenthetical is gone, the note states the corrected bare root-level shape; (c) an empty --source-digest raises SelectionUsageError (exit 2) with the overwrite-guard rationale comment (scripts/review_record_selection.py around line 311); (d) the slug message now says "no path separators" (line 283; landed in the ee85cebc wave per git log -S).
