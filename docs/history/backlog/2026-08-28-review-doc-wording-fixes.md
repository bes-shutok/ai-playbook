# Review-doc wording fixes: Confluence scratch-file child-page scope, stale fence-blindness claim

Status: open (F11 fixed 2026-08-29 by docs/plans/2026-08-28-fence-scanner-consolidation.md; F6 remains open)
Workflow: backlog
Source: docs/reviews/2026-08-28-review-artifact-contracts-code-review-r6.md, round r6, findings F6 + F11 (validated as wording/contract ambiguities; deliberately deferred)

## Problem

1. **F6 (`consistency#producer-contract-scope-gap`, Medium)**: the r5-added scratch-file recipe in `agents/skills/review-confluence-doc/SKILL.md` names one scratch file per page title and hashes only that file, while "reviewed content" is defined as the parent page plus child pages. On multi-page documents both producer readings (parent-only vs parent+children) pass the digest gate, so the documented no-misattribution guarantee over-claims (~line 183).
2. **F11 (`documentation#stale-validator-claim`, Low)**: the snippet-format rule in `agents/skills/review-staging/SKILL.md` still says the hard validator walks headings line-by-line without fence tracking; after the r5 fence-aware two-pass scan that claim is stale for block splitting and finding parsing (the severity-group heading scan is still fence-blind) (~line 245). FIXED 2026-08-29 by docs/plans/2026-08-28-fence-scanner-consolidation.md (Task 4): paragraph reworded to fence-aware splitting/parsing with the partial unclosed-fence fallback caveat and the severity-group heading-scan caveat.

## Location

- `agents/skills/review-confluence-doc/SKILL.md`, scratch-file recipe (~line 183).
- `agents/skills/review-staging/SKILL.md`, snippet-format paragraph (~line 245).

## Suggested fix

F6: either make the scratch file the concatenation of every fetched page in review order (digest covers full reviewed content) or keep per-page files and soften the guarantee to parent-page bytes only. F11: reword to say finding-block splitting and metadata parsing are fence-aware (with the unclosed-fence caveat) while the severity-group heading scan is not, so the stated reason matches the code.

## Severity

Medium (F6), Low (F11). Doc-only; following either rule as written stays safe.

## Why not fixed now

User policy 2026-08-28: low-risk findings backlogged; the fix-fix cycle was producing more issues than it closed. Both are one-paragraph skill edits; F11's wording should be settled together with the fence-scanner backlog item so the caveat text matches the consolidated scanner behavior. Decision made by the user (orchestrator scoped-fix instruction, 2026-08-28).
