# Backlog: normalize the blanket-add prohibition to one canonical phrasing

Captured: 2026-09-18 (code review r2 of the learn-done workflow updates plan; design-simplicity lens, non-blocking, backlogged)
Status: open
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; phrasing normalization. Revive on a witnessed misreading causes a wrong add, or a project-priority-profile change.)
Origin: simplification#shrink (staged finding F10, docs/reviews/2026-09-16-learn-done-workflow-updates-code-review-r2.md)

Workflow: backlog
Severity: low

## Finding

The blanket-add prohibition carries three phrasings across the touched skill set: "never a directory-wide add" (learn SKILL.md Step 1.8 commit rule, Step 4 bullet, and Step 5 commit workflow; done SKILL.md Rules), "never stage a whole tree with one command" (done SKILL.md Step 4 item 4), and "never use `git add -A` or `git add .`" (done SKILL.md Step 3 item 5, with a near-duplicate in the Step 2 pre-commit guard). Two of the three are plan-prescribed verbatim text from docs/plans/2026-09-16-learn-done-workflow-updates.md ("never a directory-wide add" and "never stage a whole tree with one command"; frozen scope of record for the run); one of those ("never a directory-wide add") is additionally pinned by the plan's G1 gate as a checker literal, so r2 could not normalize that phrasing without breaking the plan's Validation Commands pin.

## Suggested fix

A future plan should pick one canonical phrasing for the blanket-add prohibition and rewrite every occurrence across learn, done, and any other skill stating the rule, updating the corresponding validation pins in the same pass so the fail-closed gates keep matching.

## Why not fixed now

Two of the three phrasings are plan-prescribed verbatim (frozen scope of record for the 2026-09-16 learn-done workflow updates run); a sibling-doc restatement converts to backlog per the receiving-review Phase 3 default rather than editing pinned plan text mid-run.

## Closure (2026-09-19, P13 Task 7)

Canonical phrasing chosen: `never a directory-wide add`: it is the form the archived learn-done plan's G1 gate pins, so no needle flip was needed. Sites normalized in done SKILL.md: Step 4 item 4 (the superseded `never stage a whole tree with one command` replaced), Step 3 item 5, the Step 2 pre-commit guard, and the Rules line; each carries the contiguous canonical phrase (case-exact at the Step 3 item 5, Step 4 item 4, and Rules sites; sentence-initial capital at the Step 2 pre-commit guard) with the concrete `git add -A` / `git add .` enumeration as its example form, fail-closed structure kept. learn keeps its three canonical occurrences; the archived plan's G1 `expect_match "never a directory-wide add" agents/skills/learn/SKILL.md` runs rc 0. The superseded phrasing survives only in the archived plan's historical task text (frozen by design).
