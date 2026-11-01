# Plan: Restore the Intentional-Deletion Carve-Out

Backlog origin: docs/history/backlog/2026-10-21-own-edit-check-pure-deletion-carve-out.md
Driving force: code-quality
Authoring claim: docs/tmp/authoring-claims/2026-10-21-own-edit-check-pure-deletion-carve-out.md (session 01a17c5b-bdc9-7781-86f5-38e0cd2c16dd)
Plan review record: .ai-playbook/reviews/2026-10-29-plan-review-own-edit-intentional-deletion-carve-out-r*.md
Execution budget: 0.5h total, largest task 0.5h

## Terms

- **Own-edit check:** the procedure that decides whether a changed path contains only this session's work before staging it.
- **Pure-deletion hunk:** a diff hunk that removes text and adds none.
- **Pure-addition hunk:** a diff hunk that adds text and removes none.
- **Intentional deletion:** a removal explicitly included in the current task's scope before the path is staged.
- **Stale-read clobber:** a change from an old file read that would remove or restore text written by a newer landing.
- **Last-landing check:** a path is foreign when its most recent landing is newer than the session's read of it.
- **`learn` and `investigate`:** the two workflow skills whose commit rules use the own-edit check.

## Why

The `learn` and `investigate` own-edit checks classify every pure-deletion hunk as foreign, even when the current task deliberately removed that text. This can make either workflow skip a path the session intentionally changed. Restore the existing intentional-deletion carve-out while preserving protection against stale-read clobbers.

## Gist & Examples

TLDR: Restore the intentional-deletion exception in both own-edit rules, protecting code quality by keeping explicitly owned deletions eligible while peer changes stay protected.

Before, a deliberately deleted text hunk is always treated as foreign and skipped. After, a pure deletion is owned only when the current task explicitly includes that deletion; an unclear deletion or one from a newer landing remains foreign and is skipped.

**Gate delta:** remove the false foreign classification for an explicitly owned deletion only; no other refusal or check changes, and no new gate, approval, ledger, or pause condition is added. Existing plan review and readiness remain unchanged.

## Outcome

Keep the `learn` and `investigate` own-edit rules aligned with the intentional-deletion exception already stated in Lesson 134.

- A session can retain a pure deletion that its current task explicitly owns.
- A deletion without that scope evidence remains foreign and is skipped.
- The pure-addition check and the check that treats a path as foreign when its last landing is newer than the session's read stay unchanged in both procedures.

## Assumptions

- Lesson 134 records the intended exception; the backlog row identifies its omission from both consuming rules.
- Intent is established by the current task's declared scope, not by a new record or approval step.

Decision points requiring a grill: none remain.

## Evaluation Criteria

- **Correctness:** a pure deletion explicitly owned by the current task is not classified as foreign; an unclaimed deletion or one superseded by a newer landing remains foreign and is skipped.
- **Consistency:** the two skill clauses state the same exception and preserve the pure-addition and last-landing checks.
- **Scope:** only the two owner procedures change; no test framework, gate, validator, or intent ledger is added.

**Quality dimensions:**
- Correctness: intentional deletes and stale-read deletions receive their established distinct dispositions.
- Simplicity: restore the omitted clause without adding machinery or a human approval step.

**Done when:** both procedures contain the same intentional-deletion exception and the remaining foreign-hunk rules are unchanged.

**Ship when:** both skill edits and the covered-origin disposition land through the existing plan closeout.

## Review Scope

**Explicit must-fix:**

**Production code:** none.

**Tests:** none; validate the two existing procedures with the scenarios in Task 1 without adding a new test gate.

**Documentation:**
- `agents/skills/learn/step-1-extract.md` (Task 1)
- `agents/skills/investigate/SKILL.md` (Task 1)
- `docs/maintenance/development_lessons.md` (review-only) read-only witness: Lesson 134
- `docs/history/backlog/2026-10-21-own-edit-check-pure-deletion-carve-out.md` (review-only) read-only scope

**Plan-related extension:** none; repository search found these two operational consumers.

**Out of scope; reject unless plan-related:**
- New ownership ledgers, validators, or approval steps; the current task scope is sufficient to identify an intentional deletion.
- Unrelated staging rules, pure-addition behavior, and last-landing behavior; the origin does not ask to change them.

## Validation Commands

```bash
rg -n -F 'unless the current task explicitly included that deletion' agents/skills/learn/step-1-extract.md agents/skills/investigate/SKILL.md
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" --files agents/skills/learn/step-1-extract.md agents/skills/investigate/SKILL.md
git diff --check
```

### Task 1: Restore the intentional-deletion exception

Context surface: Terms and this task.

Files:
- `agents/skills/learn/step-1-extract.md`
- `agents/skills/investigate/SKILL.md`

**Evidence:** the origin records both missing qualifiers; Lesson 134 states that a pure-deletion hunk is foreign unless the session deleted it on purpose.

- [x] [class: IMPLEMENTATION_REQUIRED] Rephrase only the existing own-edit rule in each file to include the same exception: a pure deletion is foreign unless the current task explicitly included that deletion. Achieve byte neutrality by removing equivalent text only within that same own-edit rule; preserve its meaning apart from this exception and leave every other instruction unchanged.
- [x] [class: REPOSITORY_TEST] In both skills, verify three cases: a task-owned deletion on an unchanged path remains eligible; an unclaimed deletion on that path remains foreign and skipped; a task-owned deletion on a newer path remains foreign and skipped.
- [x] [class: REPOSITORY_TEST] In both skills, verify two cases: an addition this session did not write on an unchanged path remains foreign and skipped; a session-written addition on a newer path remains foreign and skipped. Confirm no new approval, refusal, tracking step, or gate appears.

**Acceptance:** the two clauses match on the exception, and the existing pure-addition and newer-path protections still produce their current foreign-skip outcome.
