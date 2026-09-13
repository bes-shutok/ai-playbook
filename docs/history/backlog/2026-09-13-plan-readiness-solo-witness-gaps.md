# Backlog: plan_readiness selftest solo-witness gaps (r1 testing lens)

Status: open
Origin: execution review r1 (2026-09-13) of docs/plans/2026-09-09-plan-readiness-trailer-tail.md, findings F7-F11

Witness-coverage gaps left deferred (duplicate-witness class, backlog-by-default):
- F7 `second_files_block_latched` has no solo witness for a latch-only
  regression (the path-shape filter masks it; post-r1-fix the latch is gone
  entirely, so the residual gap is an echo-shape witness whose token is
  non-path-shaped by construction).
- Post-r1-fix: the F1 fix (re-open semantics) means the positive red
  direction — a second real block listing an unlisted real path must fail —
  is proven only by ephemeral /tmp probes, not by a committed arm; consider
  promoting it.
- F8 "payload-bearing `files:` line must NOT latch/open" has no fixture
  combining a payload line with a later real opener.
- F9 ticked-branch separator normalization unwitnessed (only fall-through
  branch covered by `windows_separator_coverage_ok`).
- F10 meta rows probe `_validate_arm` directly; removing the loop's call to it
  flips nothing.
- F11 heading-boundary split widening (`\n#{2,4} `) has no discriminating arm
  (defense-in-depth post-fix).

Any fix should add arms WITHOUT removing existing arm names (segment [B]
preservation).
- r1 F12 deferred half: the path-shape predicate stays inline at the collection
  site (broader suffix-predicate dedup to a shared helper deliberately
  deferred with this item as its committed record).
- r3 testing lens additions (2026-09-13): doubled-backtick acceptance in the
  leading-span match has zero committed witness (revert flips 0 arms); `- [`
  checkbox-close, non-item-line close, indented sub-bullet skip, and `./`-strip
  are shape-filter-masked (each removal flips 0 arms). Cheapest first
  promotion: a doubled-backtick arm.
- Docstring precision nit (r3 correctness lens): the record says "a
  doubled-backtick fence is accepted" but the pattern accepts any backtick-run
  length; behaviorally equivalent to main's rule.
