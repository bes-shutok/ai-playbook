# Backlog: budget-gate plan review r1 exit residue (git stdout helper, witness block shape)

Captured: 2026-09-15
Status: open
Priority: low
Origin: code review r1 of `docs/plans/2026-09-14-budget-gate-family-residuals.md`
(staging doc
`docs/reviews/2026-09-15-2026-09-14-budget-gate-family-residuals-code-review-r1.md`,
findings F7 and F8, both Low, both deferred at the r1 address pass; durable
capture per receiving-review backlog rules before the review loop continues
with round 2).

## Finding F7: nineteen identical `_git(...).stdout.strip()` chains

`simplification#git-stdout-strip-chains` (Low).

Evidence: `scripts/test_execute_plan_runtime.py` carries exactly 19 call
sites of the shape `self._git(...).stdout.strip()` against the test-double
repo fixture's `_git` helper (lines 310, 311, 501, 517, 613, 614, 669,
1049, 1122, 1521, 1536, 1808, 2942, 2945, 2946, 2957, 2964, 2978, 2984 at
capture time). The repeated strip-out-of-subprocess idiom suggests a
`_git_stdout(*args) -> str` fixture helper returning the stripped stdout
directly.

Suggested fix: one mechanical follow-up tidy commit introducing the helper
and migrating the 19 chains; test-only file, no production behavior change.

Open decisions: none. Pure tidy; do not mix into a functional commit.

## Finding F8: witness block nesting depth and distant assertion

`simplification#witness-block-nesting-depth` (Low).

Evidence: `scripts/test_quota_window_probe.py`,
`test_zcode_transport_never_follows_redirects`: the ResourceWarning witness
block (escalation filter plus `sys.unraisablehook` recorder swap plus forced
`gc.collect()`, with the restore in a `finally`) sits several context levels
deep inside the server/patch scaffolding, and the trailing
`assertFalse(any(u.exc_type is ResourceWarning ...))` is far from the block
whose window it checks. Correct but hard to read.

Suggested fix: extract a `recorded_unraisables()` contextmanager
(simplefilter + hook swap + restore + window yield) when a second witness
test appears; do not extract preemptively while only one witness test
exists.

Open decisions: the extraction trigger is conditional on a second witness
test landing; revisit at that point rather than on a schedule.

## Why not fixed in the r1 address pass

F7 is a 19-site mechanical migration sized as a follow-up tidy commit, not
a Phase 3 fix; F8's extraction is deliberately conditional (single witness
test today). Deferred by the r1 address worker per the staging triage;
neither finding was dropped, both remain valid work.

3. **Stale mechanism comment in test_cli_zcode_default_url_reaches_transport** (r2 F1, correctness-completeness, Low): the comment claims the fixture epochs fail open to unknown/continue, but the secondary epoch (1791551411) stays live until 2026-10-10, so the report is ok/report-only today and only degrades to unknown after both epochs age out. The pinned exit-1 assertion is correct in every phase; reword the comment to the phase-robust truth before anyone strengthens the pin into a date-dependent flake.
