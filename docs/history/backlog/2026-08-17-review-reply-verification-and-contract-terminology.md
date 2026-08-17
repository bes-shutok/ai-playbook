# Backlog: Harden passive review thread handling and contract terminology

Status: backlog idea (pre-plan; promote via the `plans` skill when scheduled).
Workflow: when implementation is scheduled, create a plan in `{plans_dir}` and move this file to `docs/history/backlog/completed/` when the work is complete.

## Problem

A passive code-review session addressed a GitHub pull request with several avoidable process errors:

1. A reply was posted to the wrong review thread because the target thread identifier was copied manually from a large API response without a final parent-comment check.
2. The reply used task and ticket scope language that was not useful to the reviewer.
3. The term `idempotency` was interpreted too narrowly as `Idempotency-Key` response replay. The repository already provides durable replay safety for identity-keyed creates through persisted natural-key uniqueness and database constraints.
4. The reply introduced a future roadmap statement that was not supported by an authoritative source. The current contract says that header-based idempotency is not used; it does not establish a future delivery commitment.
5. The reviewer’s architectural question was answered before separating the documented current behavior from a product decision about adding a new header protocol.

The existing `receiving-code-review` and `github-pr-workflow` skills contain most of the behavioral rules, but they do not provide enough mechanical protection against a wrong-thread reply or terminology drift.

## Root causes

### A. Review-thread identity was treated as text, not as a verified relation

The workflow fetches thread IDs and comments, but it does not require a final check that the reply target contains the intended author, path, line, and comment body. A wrong identifier can therefore produce a syntactically valid reply in a semantically wrong thread.

### B. Contract terms were not classified before writing the response

The response should distinguish:

- durable replay safety from persisted natural identities, unique constraints, and upsert or insert-if-absent behavior;
- `Idempotency-Key` protocol support, including key storage, request replay, response replay, and mismatch handling.

The first can exist without the second. The service contract currently uses the first where applicable and intentionally does not expose the second.

### C. Unsupported roadmap language was inferred from scope language

“Not part of the current story” was incorrectly expanded into “future capability”. A backlog or review reply may state current scope and current non-support, but must not imply a planned follow-up unless a source explicitly records that plan.

### D. Reviewer-facing and partner-facing communication were mixed

GitHub replies should contain a closed technical answer for the reviewer. Internal context such as a ticket identifier, PR scope discussion, or a decision prompt for the partner belongs in the chat or a planning artifact, not in the review thread.

## Proposed changes

### 1. Add a target-thread verification gate to `receiving-code-review`

Before every reply:

- resolve the PR and fetch the complete thread inventory;
- select the target by stable thread ID, then verify the parent comment author, path, line, and a distinctive body fragment;
- post the reply through the shared GitHub workflow;
- re-fetch the thread and verify that the new reply is attached to the intended parent.

If the post fails or the verification shows a mismatch, stop and report the state. Do not attempt a second reply until the target is re-resolved.

### 2. Add a terminology gate for contract-sensitive replies

Before replying about idempotency, retries, deduplication, replay, or conflict behavior:

- inspect the active API contract and the repository glossary or guidelines;
- name the actual mechanism in the reply;
- distinguish durable natural-key replay safety from `Idempotency-Key` header semantics;
- avoid replacing the repository’s chosen term with a stronger or narrower term without evidence.

The gate should apply to other contract terms when the same ambiguity exists, not only to idempotency.

### 3. Prohibit unsupported roadmap statements in review replies

Extend reviewer-reply guidance with an explicit rule:

- do not say “future”, “planned”, “will be added”, “separate capability”, or similar roadmap language unless an authoritative project source says so;
- when only current scope is known, state current behavior and current scope without forecasting.

### 4. Add reviewer-reply hygiene checks

Reviewer replies must:

- contain the technical answer, evidence, and current behavior;
- omit ticket, PR, task, or internal-session meta-commentary unless it is directly needed to identify a code change;
- omit partner-only questions and decision prompts;
- avoid performative agreement and gratitude language;
- use the repository’s terminology rather than inventing a status label.

### 5. Define the architectural-question boundary

When a reviewer asks whether a new capability should exist, classify the thread as a design decision. If the current contract and authoritative guidelines do not settle it, stop and ask the partner before posting a substantive accept or reject reply. If the current contract does settle it, reply with the contract evidence and do not imply a roadmap.

### 6. Add a correction protocol for a misplaced reply

If a reply was posted to the wrong thread:

- identify the misplaced comment by API ID;
- delete it when GitHub permits deletion;
- verify deletion;
- resolve the correct parent again;
- post one replacement reply;
- verify the replacement’s parent and body;
- report the correction briefly in chat.

Do not leave both the misplaced and corrected replies in the PR.

## Candidate files

**Primary implementation:**

- `agents/skills/receiving-code-review/SKILL.md`
- `agents/skills/github-pr-workflow/SKILL.md`

**Guideline alignment if the wording is cross-cutting:**

- `projects/.ai-playbook/agent_workflow_guidelines.md`

**Validation artifacts:**

- Add focused self-checks or fixtures only where the existing skill validation structure supports them. Do not add a tool-specific integration test solely to exercise a GitHub API call.

## Acceptance criteria

- A passive-review workflow cannot post a reply until the intended parent comment has been re-verified from current API data.
- After posting, the workflow verifies the reply’s actual parent and reports a mismatch as an error.
- Guidance explicitly distinguishes natural-key durable replay safety from `Idempotency-Key` semantics.
- Guidance forbids unsupported roadmap language in reviewer replies.
- Guidance forbids PR, ticket, and internal-session meta-commentary in reviewer-facing replies.
- Architectural questions that are not settled by current authoritative sources pause for partner clarification.
- The correction protocol removes a misplaced reply before posting its replacement.
- Existing rules remain intact: human threads are not resolved by the assistant, bot threads are replied to before resolution, and replies stay in the review thread.

## Non-goals

- Adding `Idempotency-Key` support to any product service.
- Changing the current profile or consent API contracts.
- Declaring a roadmap for durable client-key replay.
- Automatically resolving human review threads.
- Replacing the shared GitHub workflow with a provider-specific implementation.

## Evidence and source decisions

- `agents/skills/receiving-code-review/SKILL.md`: verify feedback, stop on unclear items, treat architectural changes as user decisions, and keep replies reviewer-facing.
- `agents/skills/github-pr-workflow/SKILL.md`: fetch review threads, reply in-thread, and keep replies technical and reviewer-facing.
- `projects/.ai-playbook/agent_workflow_guidelines.md` §37.4: partner-only questions and decision prompts do not belong in PR thread replies.
- The profile repository’s active API reference and project guideline #73: profile and consent writes do not use `Idempotency-Key`; replay safety comes from natural keys and database constraints where applicable.
