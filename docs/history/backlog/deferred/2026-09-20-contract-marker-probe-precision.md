# Backlog: contract marker-probe precision (task 7 residuals)

- **Status:** open
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; probe precision (gates auditing gates). Revive on a witnessed deletion staying green, or a project-priority-profile change.)
- **Origin:** execute-plan task 7 intermediate review (Step 1.2b, testing lens, 2026-09-20)

## Findings

1. The Task 7 contract probe as operationalized (whole-file `grep -cF` for backticked `* [ ]` / `+ [ ]`, threshold >= 2) is not fail-closed for the terminal-predicate paragraph's marker naming: deleting that paragraph's markers (runtime-contract.md:158) leaves 3 hits and stays green. Paragraph-scoped checks (the sed-range technique the condition-4 probe uses) or per-paragraph counts are needed.
2. The heading-refusal clause of the empty-plan probe ("zero recognizable `### Task <N>:` task headings is refused naming the missing task sections") is line-wrapped across contract :152-155, so a naive single-line grep returns 0; a wrap-tolerant (whitespace-normalized) pattern is needed for the Task 10 sweep.
3. Info: the agreement witness's `assertFalse(any("line " in item ...))` no-line-fragment pin could false-fail on an unrelated rewording containing "line " (e.g. "deadline "); safe direction today.
4. Witness (task 10 sweep): a deletion-simulation negation arm must remove ALL occurrences of the target literal inside the scoped paragraph, not only the first: the terminal-predicate paragraph legitimately names the dash marker twice (predicate clause plus the fence-blind sentence), so a replace-first deletion left one mention and the three-marker check stayed green, silently voiding the arm; corrected to replace-all before the arm passed.

## Driving force

The plan's dedicated probes are contracted to fail when their obligation is deleted; a probe that stays green after deletion silently voids the fail-closed sweep Task 10 relies on.

## Note

The Task 10 sweep in this execution run applies the paragraph-scoped and wrap-tolerant forms directly; this backlog item records the durable lesson for future sweep authors.
