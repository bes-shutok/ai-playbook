# Backlog: coverage-gate self-exemption misses byte-identical checkpoint twins

- **Filed:** 2026-11-02, learn capture over the maintenance-self-heal-first-on-blocks authoring run
- **Status:** open
- **Priority:** high
- **Origin class:** observed gate false conflict (safe invocation-shape workaround applied, no gate edit)
- **Class:** fix-class
- **Driving force:** correctness
- **Skill/step:** `scripts/check_plan_origins_closed.py` `_find_covering_citers` self-exemption; the plans skill's certification-time checkpoint (which places certified plan bytes on main while the authoring worktree still declares)
- **Catch frequency:** expected once per authoring run with backlog origins that runs the duplicate-origin coverage gate from the authoring worktree after its certification checkpoint; witnessed once
- **False-positive cost:** the gate fails `OUTCOME: fail` on a correct certification, and the working remedy (re-running with the declaring operand resolved in the primary checkout) is undocumented folklore a future session must rediscover under review-budget pressure
- **Review date:** 2026-12-02
- **Dedup probe:** searched open backlog filenames and bodies for coverage gate, checkpoint twin, self-exemption, and declaring operand; no existing row covers path-equality self-exemption versus a byte-identical twin. `docs/maintenance/development_lessons.md` #280 covers an origins-form mismatch (frontmatter array versus markdown header), a different failure mode on the same gate.

## Problem

`_find_covering_citers` skips the declaring plan with a pure path comparison (`plan.resolve() == declaring.resolve()`). When the certification-time checkpoint has placed the plan's certified bytes on main, a second plan file with byte-identical content exists at a different path (the primary checkout), and the gate names that twin as the covering plan: the coverage check reports the declaring plan as already covered and fails, even though no other plan covers the origin. Witnessed 2026-11-02 in the maintenance-self-heal-first-on-blocks authoring run: after checkpoint `d75130dcd` landed the plan bytes on main, the gate run from the authoring worktree reported the main twin as the covering plan (`OUTCOME: fail`).

The workaround used was an invocation shape, not a gate edit: re-run the gate with `--check-coverage <primary>/docs/history/plans/<plan>.md --repo-root <primary>`, so the declaring operand resolves to the same path the scan enumerates and the path-equality exemption matches. That works but is undiscovered and easy to misread as a certification defect.

## Expected

The self-exemption should not depend on the declaring operand's path alone. Either the exemption also treats a byte-identical plan as the declaring artifact (content-equality alongside path equality), or the gate canonicalizes the declaring operand to the primary checkout's plan path when the bytes match. A twin that differs in bytes from the declaring plan must still count as a citer.

## Suggested direction

Compare the current path-only exemption with a content-hash exemption (hash the declaring plan's bytes, exempt a scanned plan whose bytes hash equal) and with a documented primary-path canonicalization at the gate entry. State which shape keeps a genuinely distinct same-origin plan flagged as a citer. This narrows an existing guard's predicate rather than adding machinery; no new admission surface is needed, and the machinery admission protocol's retire-or-simplify duty is met by removing the false-conflict refusal class the workaround currently absorbs.

## Evidence

- `scripts/check_plan_origins_closed.py` `_find_covering_citers`: the declaring-plan skip is `plan.resolve() == declaring.resolve()` and nothing else.
- Certification checkpoint `d75130dcd` and landing `e79617d9` (plan `docs/history/plans/2026-11-02-maintenance-self-heal-first-on-blocks.md`): the checkpoint put identical plan bytes on main before the worktree's gate run.
- Remedy invocation recorded in the run: `python3 scripts/check_plan_origins_closed.py --check-coverage docs/history/plans/2026-11-02-maintenance-self-heal-first-on-blocks.md --repo-root <primary>` returned pass while the worktree-relative invocation returned `OUTCOME: fail`.
