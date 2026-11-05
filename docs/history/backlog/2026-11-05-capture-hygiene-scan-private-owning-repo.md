# Backlog: capture hygiene check cannot pass for items kept in a private owning repository

- **Filed:** 2026-11-05, witnessed while capturing review findings in a company repository
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** Company projects that run review-fix cycles file backlog items in their own private repositories; a mandatory scan that always fails there forces either a false pass claim or a silent exception.
- **Origin class:** consumer-feedback (company)
- **Class:** fix-class
- **Driving force:** clarity + reliability
- **Skill/step:** `agents/skills/receiving-review/SKILL.md` "Backlog capture for valid findings not fixed in scope", capture hygiene check steps 1 to 5; `scripts/scan-public-hygiene.sh`
- **Catch frequency:** witnessed once; an already-committed item in the same company repository fails the scan the same way.
- **False-positive cost:** exempting the scan too broadly would let identifiers reach a public repository; any exemption must key off the destination repository's visibility, not the item's content.
- **Review date:** 2026-12-05
- **Dedup probe:** searched open backlog names and bodies for the hygiene scanner and capture hygiene wording; the nearest item concerns stub-row disposal and does not touch this check.

## Problem

The capture hygiene check says to run the public-hygiene scanner over the draft and, on a findings verdict, fix the draft until it passes, never widening the deny patterns. Step 5 separately says scrubbing identifiers applies to a foreign-origin item recorded in a shared or public repository. For an item recorded in the finding's own private company repository, the scanner flags the ticket prefix and the company package paths, which are exactly the actionable locations the item needs. Following step 2 literally would strip those and make the item useless; following step 5 says the scrub is not required. The two steps do not say which wins, and the scanner has no mode keyed to destination visibility.

## Observed versus expected

Observed: scan exits 1 with `OUTCOME: fail` on a draft whose only hits are the ticket prefix and package paths; a previously committed item in the same repository fails identically. The author had to decide alone to record the real scan result and keep the identifiers. Expected: the check states that the scan gates only items destined for a public or shared repository, or the scanner accepts a destination-visibility input, and says what verdict to record for a private owning repository.

## Suggested fix

In the capture hygiene check, branch on the destination repository's visibility (the repository facts already carry an artifact visibility value): public or shared destination runs the scan and scrub as written; a private owning repository records "scan not applicable (private owning repository)" or runs the scanner in an informational mode, and never claims a pass.

## Evidence

Environment: shared skills at the repository copy, 2026-11-05, company repository with private visibility. Scan outcome fail on two lines of the draft (ticket prefix, package path); same outcome on a committed item from a prior boundary.
