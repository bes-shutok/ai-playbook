# flat-pin normalization misses a hyphen-split line wrap

Driving force: correctness
Date filed: 2026-10-07
Origin: Task 1 intermediate review (investigate-origin-independent-eligibility) backlog capture

## Finding

The pins suite's wrap-tolerant flat scan normalizes newlines to single spaces (`tr '\n' ' ' | tr -s ' '`), so a banned literal wrapped at a hyphen (for example `foreign-` + newline + `origin`) normalizes to `foreign- origin` and evades every flat pin suite-wide, not only the origin-eligibility section. The property is shared by every pre-existing `expect_absent_flat` consumer; the plan mandated exactly this doctrine, so this is a doctrine-level residual, not a task deviation. A hyphen-split reintroduction also renders differently in Markdown, bounding practical reach.

## Suggested direction

A doctrine-level normalization pass (for example also collapsing `- ` at wrap joins, or a second hyphen-stripped comparison) inside `expect_absent_flat`, with the suite's fixture fail-arm extended to cover the hyphen-split case.

R1 F5 addition (2026-10-07, investigate-origin-independent-eligibility code review): also rewrite the origin-eligibility section's two inline flat-scan loops (the `check_origin_independent_eligibility` copies of `expect_absent_flat`'s core) onto a shared rc-returning helper (for example `absent_flat_rc <file> <pattern>` carrying the same three-way polarity), so a doctrine-level normalization fix lands in one place and covers the whole suite (three copies of the core today: the helper, plus the two inline loops).

## Evidence

- Task 1+2 review pass, 2026-10-07, wt-ioie-exec (live probe: `foreign-\norigin` undetected; word-boundary wraps detected)
- scripts/check_maintenance_pins.sh flat-scan normalization (line ~78 doctrine, ~2498/~2515 consumers)
