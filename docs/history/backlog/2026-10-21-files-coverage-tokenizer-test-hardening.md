# Backlog: harden the FILES-COVERAGE tokenizer's unpinned surfaces and the pre-existing selftest failure

Status: open
Priority: low
Class: fix-class (test pins plus one pre-existing failure triage; no production change)
Origin class: review-residual (execute-plan Phase 3 r1 of plan docs/history/plans/2026-10-20-readiness-files-coverage-quote-prefix.md, findings T-2, T-3, T-4, CC-4)
Driving force: reliability

## Skill and step

`scripts/test_plan_readiness.py` (the PlanFilesCoverageTest class); `scripts/plan_readiness.py --selftest` (pre-existing failure, separate leg).

## Observed versus expected

Observed: the tokenizer's case sensitivity and its leading-whitespace `lstrip` are load-bearing but unpinned (a case-folding refactor or a dropped lstrip would widen or break the vocabulary with zero test failures: mutations M9 and M10 both survive the suite); the plan's Assumptions claim "a boundary test pins that" the composite collector keeps raw spans, and no such test exists; and `plan_readiness.py --selftest` exits 1 on a pre-existing counts-parity fixture failure (selftest#unresolved_blocking_finding) byte-identical on main, unrelated to this landing.

Expected: one subTest pinning `` Run `Bash scripts/foo.sh` `` still warns; one pinning `` ` bash scripts/foo.sh` `` (leading space) silent; either the one collector raw-span boundary test or a recorded note that the Assumptions' basis is inspection; and the selftest counts-parity failure triaged and repaired by its owning surface.

## Evidence

Phase 3 focused panel r1 (correctness-completeness + testing), 2026-10-21, branch 2026-10-21-readiness-files-coverage-quote-prefix; the testing lens's 11-mutation harness recorded M9/M10 as live survivors; CC-4 verified the selftest failure byte-identical on main 42a0a3b1f.
