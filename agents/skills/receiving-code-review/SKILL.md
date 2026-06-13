---
name: receiving-code-review
description: Use when receiving or addressing existing code review feedback, before implementing suggestions, especially if feedback seems unclear or technically questionable. Trigger phrases — "address comments", "address PR comments", "process PR comments", "reviewer comments", "copilot comments", "fix review feedback", "respond to review feedback", "address comments in <GitHub PR URL>". Requires technical rigor and verification, not performative agreement or blind implementation. Do not use for fresh PR review; use doing-code-review instead.
---

# Code Review Reception

## Boundary

Use this skill for **passive review**: evaluating, triaging, implementing, and replying to existing review feedback.

Do not use this skill to produce a fresh review of a PR or diff. Use `doing-code-review` for active review. For GitHub PR operations such as fetching review threads, replying to threads, and resolving bot threads, use the shared primitives in `github-pr-workflow`.

## Overview

Code review requires technical evaluation, not emotional performance.

**Core principle:** Verify before implementing. Ask before assuming. Technical correctness over social comfort.

## The Response Pattern

```
WHEN receiving code review feedback:

1. READ: Complete feedback without reacting
2. UNDERSTAND: Restate requirement in own words (or ask)
3. VERIFY: Check against codebase reality
4. EVALUATE: Technically sound for THIS codebase?
5. RESPOND: Technical acknowledgment or reasoned pushback
6. IMPLEMENT: One item at a time, test each
```

## GitHub PR Feedback Workflow

Use this workflow when the user asks to process, triage, plan, address, or reply to existing PR review comments.

1. Use `github-pr-workflow` to resolve the PR context and fetch all review threads.
2. Read all unresolved thread bodies before deciding what to implement.
3. Spot-check resolved or outdated threads against current code before skipping them.
4. Verify each live comment against the referenced file and line.
5. **Check branch scope**: before staging any fix, confirm the file belongs to this branch's scope. If a comment touches a file outside the branch's folder (e.g., `individual/<name>/` while on a team branch), plan that fix as a separate commit to the appropriate branch — do not include it in the PR's branch commit.
6. Classify each live comment as correctness bug, test quality, cleanup, docs, false positive, or needs clarification.
7. When a bot cites a guideline to justify a flag, look up the guideline and confirm it applies to this specific file type before implementing. Standard license copyright headers, for example, are not subject to PII redaction rules even if the guideline covers the same keyword (see `coding_guidelines.md §12`).
8. Deduplicate comments by root cause. Multiple threads about the same root cause become one task.
9. If any item is unclear, stop and ask before implementing.
10. Implement one root-cause task at a time and verify after each fix.
11. Use `github-pr-workflow` to reply to each thread after implementation or after deciding no code change is needed.
12. Resolve bot or automated threads only after replying. Never resolve human reviewer threads.

Every CR comment thread must get a reply before it is resolved. For fixes, reference the commit SHA when available and describe what changed. For false positives, explain why no change was made.

When a plan is needed, save grouped tasks to `{plans_dir}/<BRANCH-KEY>-<short-title>.md` (read `{plans_dir}` from `.ai-playbook/facts.md` TOML per `using-skills` Step 0) using the repository plan format. Do not start implementing the plan unless the user explicitly says to start.

## Forbidden Responses

**NEVER:**
- "You're absolutely right!" (explicit CLAUDE.md violation)
- "Great point!" / "Excellent feedback!" (performative)
- "Let me implement that now" (before verification)

**INSTEAD:**
- Restate the technical requirement
- Ask clarifying questions
- Push back with technical reasoning if wrong
- Just start working (actions > words)

## Handling Unclear Feedback

```
IF any item is unclear:
  STOP - do not implement anything yet
  ASK for clarification on unclear items

WHY: Items may be related. Partial understanding = wrong implementation.
```

**Example:**
```
your human partner: "Fix 1-6"
You understand 1,2,3,6. Unclear on 4,5.

❌ WRONG: Implement 1,2,3,6 now, ask about 4,5 later
✅ RIGHT: "I understand items 1,2,3,6. Need clarification on 4 and 5 before proceeding."
```

## Source-Specific Handling

### From your human partner
- **Trusted** - implement after understanding
- **Still ask** if scope unclear
- **No performative agreement**
- **Skip to action** or technical acknowledgment

### From External Reviewers
```
BEFORE implementing:
  1. Check: Technically correct for THIS codebase?
  2. Check: Breaks existing functionality?
  3. Check: Reason for current implementation?
  4. Check: Works on all platforms/versions?
  5. Check: Does reviewer understand full context?

IF suggestion seems wrong:
  Push back with technical reasoning

IF can't easily verify:
  Say so: "I can't verify this without [X]. Should I [investigate/ask/proceed]?"

IF conflicts with your human partner's prior decisions:
  Stop and discuss with your human partner first
```

**your human partner's rule:** "External feedback - be skeptical, but check carefully"

## YAGNI Check for "Professional" Features

```
IF reviewer suggests "implementing properly":
  grep codebase for actual usage

  IF unused: "This endpoint isn't called. Remove it (YAGNI)?"
  IF used: Then implement properly
```

**your human partner's rule:** "You and reviewer both report to me. If we don't need this feature, don't add it."

## Implementation Order

```
FOR multi-item feedback:
  1. Clarify anything unclear FIRST
  2. Then implement in this order:
     - Blocking issues (breaks, security)
     - Simple fixes (typos, imports)
     - Complex fixes (refactoring, logic)
  3. Test each fix individually
  4. Verify no regressions
```

## Same-change-set scope for optional Low findings

When a review finding is marked optional/Low but references files or classes already modified in the active branch or session, list the in-scope Low findings you plan to implement and ask the user for confirmation before acting.

```
IF finding severity is Low AND reviewer labels it "optional":
  IF finding touches files already changed on this branch/session:
    REPORT to user: list each in-scope Low finding and the proposed fix
    WAIT for user confirmation before implementing
  ELSE IF finding is cross-cutting or new subsystem:
    PRESENT to user before deferring
```

"Optional" means lower delivery priority, not permission to skip when the diff is already open on those paths. But it also does not mean silent auto-implementation: report what you plan to fix and get a brief confirmation first.

## Triage Decision Rule

When classifying findings for user questions (design decisions, architectural changes, refactors):

**Never unilaterally classify a Medium/High finding as "skip"** — always present it as an explicit question to the user. Only the user can decide to defer or reject a non-trivial architectural decision.

```
❌ WRONG: Present findings #28 and #29 as "Skip — architectural change not needed now"
✅ RIGHT: Ask user: "Finding #28 proposes moving TaxJurisdictionConfig to domain/. Should I do this?"
```

The only findings that may be silently skipped without asking are:
- Findings already confirmed as `done` by prior code inspection
- Findings the user explicitly declined in an earlier question in the same session

All others — regardless of your assessment of their complexity or risk — must be presented to the user.

## When To Push Back

Push back when:
- Suggestion breaks existing functionality
- Reviewer lacks full context
- Violates YAGNI (unused feature)
- Technically incorrect for this stack
- Legacy/compatibility reasons exist
- Conflicts with your human partner's architectural decisions

**How to push back:**
- Use technical reasoning, not defensiveness
- Ask specific questions
- Reference working tests/code
- Involve your human partner if architectural

**Signal if uncomfortable pushing back out loud:** "Strange things are afoot at the Circle K"

## Acknowledging Correct Feedback

When feedback IS correct:
```
✅ "Fixed. [Brief description of what changed]"
✅ "Good catch - [specific issue]. Fixed in [location]."
✅ [Just fix it and show in the code]

❌ "You're absolutely right!"
❌ "Great point!"
❌ "Thanks for catching that!"
❌ "Thanks for [anything]"
❌ ANY gratitude expression
```

**Why no thanks:** Actions speak. Just fix it. The code itself shows you heard the feedback.

**If you catch yourself about to write "Thanks":** DELETE IT. State the fix instead.

## Gracefully Correcting Your Pushback

If you pushed back and were wrong:
```
✅ "You were right - I checked [X] and it does [Y]. Implementing now."
✅ "Verified this and you're correct. My initial understanding was wrong because [reason]. Fixing."

❌ Long apology
❌ Defending why you pushed back
❌ Over-explaining
```

State the correction factually and move on.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Performative agreement | State requirement or just act |
| Blind implementation | Verify against codebase first |
| Batch without testing | One at a time, test each |
| Assuming reviewer is right | Check if breaks things |
| Avoiding pushback | Technical correctness > comfort |
| Partial implementation | Clarify all items first |
| Can't verify, proceed anyway | State limitation, ask for direction |

## Real Examples

**Performative Agreement (Bad):**
```
Reviewer: "Remove legacy code"
❌ "You're absolutely right! Let me remove that..."
```

**Technical Verification (Good):**
```
Reviewer: "Remove legacy code"
✅ "Checking... build target is 10.15+, this API needs 13+. Need legacy for backward compat. Current impl has wrong bundle ID - fix it or drop pre-13 support?"
```

**YAGNI (Good):**
```
Reviewer: "Implement proper metrics tracking with database, date filters, CSV export"
✅ "Grepped codebase - nothing calls this endpoint. Remove it (YAGNI)? Or is there usage I'm missing?"
```

**Unclear Item (Good):**
```
your human partner: "Fix items 1-6"
You understand 1,2,3,6. Unclear on 4,5.
✅ "Understand 1,2,3,6. Need clarification on 4 and 5 before implementing."
```

## GitHub Thread Replies

Use `github-pr-workflow` for the exact GitHub GraphQL commands.

Rules:
- Reply in the review thread, not as a top-level PR comment.
- Do not reply "Fixed" or cite a follow-up branch until the change exists in the working tree or a pushed commit on that branch.
- Bot or automated threads: reply, then resolve in the same step.
- Human reviewer threads: reply only. Never resolve them.
- Never silently resolve any thread.

## Integration Points

### With `bootstrap-ai-playbook` skill
Provider for `{plans_dir}` when saving grouped fix tasks from review feedback. Read path keys from `.ai-playbook/facts.md` (see `using-skills` Step 0).

### With `execute-plan` skill
Invoked as a sub-agent between review rounds. Input is the staging doc from `doing-code-review` (`pending` Critical/High/Medium findings). Honors the plan's `## Review Scope`. Triage is authoritative for Phase 3 exit: implements fixes, marks `drop`/`done`, leaves only validated issues at `pending`. The orchestrator counts **remaining Medium+** after this step — not provisional `doing-code-review` counts. Does not commit — the orchestrator runs streak evaluation and `done`, then may start the next review round.

## The Bottom Line

**External feedback = suggestions to evaluate, not orders to follow.**

Verify. Question. Then implement.

No performative agreement. Technical rigor always.
