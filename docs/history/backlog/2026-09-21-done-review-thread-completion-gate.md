# Backlog: add a mechanical review-thread completion gate to done

Status: open
Priority: high
Workflow: backlog
Class: done and receiving-review completion integrity
Driving force: correctness

## Problem

The passive review workflow requires a reply to every tracked review thread, but
the done workflow has no mechanical way to prove that external review state was
closed before it reports completion. A session can commit and test the code while
leaving live threads without replies. The permission to reply is also distinct
from permission to push the branch, so treating push authorization as a blocker
can incorrectly suppress authorized review responses.

## Suggested fix

1. Have receiving-review write a small session marker containing the PR identity,
   branch head, and tracked thread IDs when it begins processing feedback.
2. Add a read-only validator that re-fetches the live thread inventory before
   done reports completion. It should require a verified agent reply or an
   explicit disposition for every tracked thread, distinguish human threads from
   automated threads, and reject resolved automated threads without a reply.
3. Make reply posting idempotent by checking for the exact existing response
   before creating a new one, then verify the response attachment by stable thread
   ID and parent metadata.
4. Make done fail closed when the marker exists and the validator cannot establish
   review closure. Report push authorization separately from review-response state.

## Acceptance criteria

- A passive review session cannot report done while a tracked thread lacks a
  verified reply or explicit disposition.
- The validator does not require a branch push merely to post an authorized reply.
- Human-authored threads are never auto-resolved.
- Retrying a timed-out reply operation does not create duplicate agent replies.
- A session with no passive-review marker is unaffected.

## Witness

During a review-fix session, the implementation commit and tests were complete,
but eight live automated threads were still unanswered because local finalization
was treated as sufficient. The threads were later replied to and verified manually.
