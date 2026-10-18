# Backlog: porcelain unquote does not decode git octal escapes

Origin: done-sweep residuals execution review r1 finding 1, 2026-09-25
Status: rejected (2026-10-10; standing 2026-09-26 direction-triage rubric class 2: unwitnessed validator hardening, a fail-closed decoding fix with no corruption witness; adjudicated with agreement to .ai-playbook/friction-audit/retriage-proposal-2026-09-27.md; revival only by a new owner decision)

`_unquote_porcelain_path` (scripts/done_sweep_gates_lib.py) strips git's C-style quote wrapping but does not decode the octal `\NNN` escapes git emits for non-ASCII bytes under the default `core.quotePath=true`. A staged rename of a staging doc whose destination name carries non-ASCII bytes is unquoted of its wrapper quotes but left with literal `\320\...` sequences, so it still misses the claim-or-foreign universe. Fail-closed direction (named claim-or-foreign abort, never silent suppression); pre-F9 behavior was equally broken for such names, so this is residual scope, not a regression.

Suggested remedy: decode `\NNN` byte escapes (UTF-8 reassembly) in the unquote helper, or parse the rename row via `git status --porcelain -z` (NUL-delimited, no quoting) in `_porcelain_paths`, mirroring the F9 plan discussion. Pin with a non-ASCII rename fixture.
