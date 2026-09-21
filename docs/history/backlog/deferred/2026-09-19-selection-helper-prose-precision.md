# Backlog: selection-helper prose and message precision (small polish batch)

Status: open
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; docstring/message/exit-taxonomy precision. Revive on a witnessed operator misdirection by one of the messages, or a project-priority-profile change.)
Severity: Low
Origin: r4 code-review round of the review-records-contract execution (2026-09-19), staged finding F5 and overflow items (design-simplicity, risk); staging doc `docs/reviews/2026-09-16-review-records-contract-code-review-r4.md` (gitignored); capture hygiene: scan-public-hygiene --files pass (2026-09-19)

## Problem

Small precision items in `scripts/review_record_selection.py` and one backlog note: (a) `SelectionUsageError` docstring says "invalid argument (exit 2)" but three non-argument uses exist (symlinked prior, unclosed fence, backup-name collision); (b) the F9 backlog note (`2026-09-19-scanner-allowlist-glob-single-source.md` line ~12) overstates the absolute-spelling shape: absolute spellings of root LICENSE.txt are EXCLUDED in files mode (the `*/LICENSE.txt` case pattern matches across slashes); only the bare root-level relative spelling is scanned; (c) an empty/whitespace `--source-digest` exits 1 while every other malformed digest exits 2 (taxonomy inconsistent; both fail closed); (d) the slug error message claims "no '..'" while `a..b` is accepted (no separator possible in the grammar).

## Fix shape

Broaden the docstring; drop the parenthetical in the F9 note; raise the empty-digest refusal as a usage error (exit 2) or document the split; reword the slug message to "no path separators". All fail-closed today; polish only.

## Trigger

The next edit to the helper's error paths or the allowlist backlog item's consumption.
