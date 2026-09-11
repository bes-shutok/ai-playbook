# Scope-control family r6 non-blocking residuals

- **Date:** 2026-09-05
- **Status:** open
Priority: deferred (efficiency/token/simplicity triage 2026-09-11: process-cosmetic or archived-record value only; revisit only if it starts costing real review rounds or tokens)

- **Origin:** code review round 6 (fresh full panel on 4d2656e) of the scope-control family plan (docs/plans/completed/2026-09-05-scope-control-family.md after archive). Zero blocking findings; these valid non-blocking findings were deferred unfixed to avoid mutating the clean digest (a fix would require a round-7 review beyond the authorized budget). Full detail: docs/reviews/2026-09-05-scope-control-family-code-review-r6.md (gitignored).

## Findings (12; 3 Medium, 9 Low)

### Medium

1. **done Step 3 item 0 is a ~250-word six-rule paragraph with checker documentation duplicated three times** (done, plans ledger paragraph, checker docstring). Fix: keep the behavioral rule in done; point to the checker for exit codes/limitations; keep limitation text in exactly one place.
2. **grilling trigger condition is one ~80-word sentence with three nested "or" groups**; r4/r5 catch-alls make the word enumeration partially redundant and "or whose" lacks a clean antecedent. Fix: restructure as short lead + two-bullet trigger list (wording limb; tree limb), preserving pinned spans.
3. **plans ledger paragraph over-claims what the checker mechanically enforces**: the allow-list is byte-exact file paths only; classes/methods/hunks/frozen areas inside an allow-listed file are not mechanically checked. Fix: append a granularity-limitation sentence to the ledger paragraph; mirror one clause in done item 0.

### Low

4. plans Step 1.4 template meta-rule HTML comment sits inside the copyable template fence (would render or leak into plans on verbatim copy); also the always-renders rule now lives three times in plans/SKILL.md, and the "none proposed." literal cannot survive the template's bold rendering byte-exactly (element 6 vs template should prescribe the exact rendered form `**Scope extensions (grilled):** none proposed.`).
5. plans necessity tie-breaker largely restates the goal-source parenthetical in the same paragraph; compress.
6. plans ledger "committed changes relative to the base" never defines which base; grilling "or whose natural fulfillment" grammar is garbled ("or a request whose...").
7. done item 0 "after commits exist, only deletions remain checkable" is ambiguous: uncommitted dirty paths are still classified from git status; only committed non-deletion changes become invisible.
8. done item 0 ignored-set capture has no stated timing (must be the same pre-edit moment; `--porcelain --ignored` collapses directories - prefer `--ignored=matching` or per-file listing).
9. checker selftest `subprocess.run` calls omit `encoding="utf-8", errors="replace"`, so selftest decoding is locale-dependent (crashes, fail-closed, on non-UTF-8 locales); production `_git()` pins it correctly.
10. checker docstring "fails closed" non-UTF-8 claim has no selftest arm (add one writing a `b"bad\xffname.txt"` fixture).
11. checker config-independence claim (`diff.renames=true`/`status.renames=true` hostile config) untested: set both configs in the arm-9 fixture before `git mv`.
12. checker nits: `_run_checker` argv built via `sum()` of lists; docstring says "eleven fixture repos" twice in one sentence; Task 4 in the plan has no amendment note for the 4-to-11 arm expansion.

## Disposition

Backlogged 2026-09-05 by the execute-plan run after clean round 6; candidate for a small follow-up hardening pass (items 1-3 first).
