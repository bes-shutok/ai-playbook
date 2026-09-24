# Verify inline review comments after submission

Status: closed

Disposition: 2026-09-25 (routed via docs/plans/2026-09-25-done-sweep-residuals-and-stale-origin-dispositions.md, Task 5): Discharged by executed docs/plans/completed/2026-09-22-review-post-landing-verification.md: the mandatory post-submission landing-verification step is live in agents/skills/doing-code-review/SKILL.md (verified live this run).
Priority: high

## Skill and step

- Skill: `doing-code-review`
- Step: Posting staged findings to a GitHub pull request

## Observed behavior

An active review submission was reported as containing four inline findings because the submission call returned an approved review. The returned review object only contained the top-level approval text, and the pull request had no comments associated with that review. The inline findings became visible only after posting each comment separately through the pull-request comments endpoint.

## Expected behavior

After posting a review, the workflow should verify that every intended finding exists as a GitHub inline comment with the expected path, line, commit, and distinctive body fragment before marking the staging record `POSTED` or reporting completion. If the batch endpoint silently drops comments, the workflow should post them individually or report the review as incomplete.

## Reproduction evidence

1. Submit a review containing a top-level approval body and inline comment payloads.
2. Inspect the returned review object and query the pull request's review comments filtered by the returned review ID.
3. The review is `APPROVED`, but the filtered comment set is empty.
4. Post each inline comment through the pull-request comments endpoint and verify the returned comment IDs, paths, lines, commit SHA, and URLs.

## Suspected root area

The active-review posting protocol treats a successful review-submission response as proof that inline comments were attached. It lacks a postcondition check over the GitHub comment collection and does not define recovery when the batch submission accepts the review but drops file comments.

## Desired fix shape

Add a mandatory post-submission verification step to the active review workflow. The check should compare the intended finding count and anchors with the live pull request comments, then use individually posted comments as the recovery path when the batch review contains fewer inline comments than intended.
