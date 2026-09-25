# Plan: Harden passive review thread handling and contract terminology

Backlog origin: `docs/history/backlog/2026-08-17-review-reply-verification-and-contract-terminology.md`

## Terms

- **Target-thread verification**: re-checking, from live GitHub API data, that the selected reply target is the intended parent comment (author, path, line, distinctive body fragment) before posting, and that the posted reply attached to that parent after posting.
- **Durable replay safety**: protection against duplicate creates from persisted natural keys, unique constraints, and insert-if-absent behavior. Exists without any header protocol.
- **`Idempotency-Key` protocol**: an explicit header-based replay protocol (key storage, request replay, response replay, mismatch handling). The profile/consent contracts intentionally do not use it.
- **Reviewer-facing reply**: a PR thread reply that is a closed technical statement for the reviewer; internal session context (tickets, PR scope chat, partner questions) stays in chat or planning artifacts.

## Assumptions

- assume the backlog's `receiving-code-review` skill is the on-disk `agents/skills/receiving-review/`; basis: the repo tree has no `receiving-code-review` directory, and `receiving-review` carries the passive-review reply rules the backlog cites.
- assume the mechanical before/after reply verification primitive lives in `github-pr-workflow` "Shared GitHub PR Operations" (its documented role as shared primitives owner), while the behavioral gates (terminology, roadmap, hygiene, architectural boundary, correction protocol) live in `receiving-review`; basis: both skills' routing boundaries.
- assume no new test harness: validation is fail-closed grep probes over the edited skill files plus the repo hygiene scan; basis: backlog "Validation artifacts" note and the repo has no skill-content test suite.

Decision points requiring a grill: none remain.

## Gist & Examples

A passive review session posted a reply to the wrong thread, used ticket-scope language, called durable natural-key replay safety "idempotency" narrowly, and promised future `Idempotency-Key` support nobody had decided. The skills already contain most rules but nothing mechanical stops a wrong-thread reply or terminology drift.

What changes:

1. `github-pr-workflow` gains a shared **verify thread attachment** operation: after `addPullRequestReviewThreadReply`, query the target thread directly and confirm the new reply is attached to the intended parent thread with the expected author, file path, and line; a mismatch is reported as an error, not smoothed over.
2. `receiving-review` gains a **target-thread verification gate**: select the target by stable thread ID, verify parent author/path/line/body fragment before every reply, stop on mismatch, and never post a second reply until the target is re-resolved.
3. `receiving-review` gains a **contract terminology gate**: before replying about idempotency, retries, dedup, replay, or conflict behavior, check the active contract/glossary, name the actual mechanism, and keep durable replay safety distinct from `Idempotency-Key` semantics.
4. `receiving-review` forbids **unsupported roadmap language** ("future", "planned", "will be added") unless an authoritative source records the plan; state current behavior and current scope instead.
5. `receiving-review` tightens **reviewer-reply hygiene**: no ticket/PR/task/internal-session meta-commentary, no partner-only questions, no invented status labels, in addition to the existing no-gratitude rules.
6. `receiving-review` defines the **architectural-question boundary**: a reviewer question about whether a new capability should exist is a design decision; if the contract and authoritative guidelines do not settle it, stop and ask the partner before posting.
7. `receiving-review` defines a **correction protocol** for a misplaced reply: identify by API ID, delete, verify deletion, re-resolve the correct parent, post one replacement, verify it, and report briefly in chat. Never leave both replies.
8. `agent_workflow_guidelines.md` gains one numbered rule beside §37.4 making the roadmap-language and terminology-classification rules cross-cutting for PR thread replies.

Example: reviewer asks "why no `Idempotency-Key` on POST /profile? will it come later?" Today's failure mode answers "not in this story's scope, planned for a future capability". After this plan: the reply states the contract's actual mechanism (natural-key + DB-constraint replay safety where applicable), explicitly says header-based idempotency is not used today, and does not forecast a roadmap; the "will it come later" part is a design decision that pauses for the partner unless the contract already settles it.

## Evaluation Criteria

**Quality dimensions:**

- Correctness: every backlog "Proposed changes" item 1-6 has a corresponding enforceable rule in the right skill; every backlog acceptance criterion is covered by a probe in Validation Commands.
- Mechanical protection: the thread gate is stated as a stop-and-report gate (fail-closed), not advice; deleting a primary gate sentence (pre-reply verification, post-reply attachment check, stop-on-mismatch, terminology distinction, roadmap prohibition, correction chain) breaks its dedicated probe; secondary clauses within a gate are covered by the gate's primary pin.
- Maintainability: rules live in their owning skill; the cross-cutting guideline is a single numbered rule, not a full restatement in every peer (consolidation rule in `receiving-review` "Documentation and Comment Findings").
- Hygiene: `scan-public-hygiene.sh` exits 0; no absolute paths or sensitive strings introduced.

**Done when:**

- Both SKILL.md files and the guidelines file carry the new rules with the exact anchor phrases the Validation Commands pin.
- All validation commands pass on the edited tree.
- Hygiene scan exits 0.

**Ship when:**

- Runtime skill copies (`~/.agents/skills` and other agent runtime directories) are redeployed (pending user go-ahead; tracked separately from this repo).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code (skill corpus):**
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/github-pr-workflow/SKILL.md`
- `projects/.ai-playbook/agent_workflow_guidelines.md`

**Tests:** none; the repo has no skill-content test suite (see Assumptions).

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py`; reason: foreign in-flight edit from a peer session on this branch, untouched by this plan.
- Product service code (profile/consent APIs); reason: backlog Non-goals: no `Idempotency-Key` support or contract changes in any product repo.
- `README.md`; reason: skill catalog names and paths are unchanged.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"

fail() { echo "FAIL: $1" >&2; exit 1; }

for f in \
  "$REPO/agents/skills/receiving-review/SKILL.md" \
  "$REPO/agents/skills/github-pr-workflow/SKILL.md" \
  "$REPO/projects/.ai-playbook/agent_workflow_guidelines.md"; do
  test -f "$f" || fail "missing must-fix file: $f"
done

# Task 1: target-thread verification gate, distinctive span verbatim
grep -q "verify the parent comment author, file path, line, and a distinctive body fragment" \
  "$REPO/agents/skills/receiving-review/SKILL.md" \
  || fail "target-thread verification gate missing"
# Task 1: post-reply verification obligation
grep -q "re-fetch the thread and verify that the new reply is attached to the intended parent" \
  "$REPO/agents/skills/receiving-review/SKILL.md" \
  || fail "post-reply verification missing"
# Task 1: stop-on-mismatch wording (polarity: positive obligation verbs)
grep -q "stop and report the state" "$REPO/agents/skills/receiving-review/SKILL.md" \
  || fail "stop-on-mismatch gate missing"
grep -q "verify_thread_attachment" "$REPO/agents/skills/github-pr-workflow/SKILL.md" \
  || fail "shared verify-thread-attachment operation missing"
# Task 2: terminology gate pins both sides of the distinction
grep -q "durable replay safety" "$REPO/agents/skills/receiving-review/SKILL.md" \
  || fail "durable replay safety term missing"
grep -q "Idempotency-Key" "$REPO/agents/skills/receiving-review/SKILL.md" \
  || fail "Idempotency-Key distinction missing"
# Task 3: roadmap prohibition, canonical home is guideline 37.5 (skill carries the operational gate)
grep -qiE "roadmap language" "$REPO/agents/skills/receiving-review/SKILL.md" \
  || fail "roadmap language prohibition missing"
grep -q "state current behavior and current scope without forecasting" \
  "$REPO/agents/skills/receiving-review/SKILL.md" \
  || fail "roadmap current-scope phrasing missing"
grep -q "separate capability" "$REPO/agents/skills/receiving-review/SKILL.md" \
  || fail "separate capability example missing"
# Task 4: hygiene pins partner-only questions and status labels (distinctive fragments)
grep -q "internal-session meta-commentary" "$REPO/agents/skills/receiving-review/SKILL.md" \
  || fail "reviewer-reply hygiene rule missing"
grep -q "omit partner-only questions" "$REPO/agents/skills/receiving-review/SKILL.md" \
  || fail "partner-only question rule missing"
grep -q "inventing a status label" "$REPO/agents/skills/receiving-review/SKILL.md" \
  || fail "status-label rule missing"
# Task 2: terminology gate generality clause
grep -qi "not only idempotency" "$REPO/agents/skills/receiving-review/SKILL.md" \
  || fail "terminology gate generality clause missing"
# Task 5: architectural-question boundary
grep -q "classify the thread as a design decision" \
  "$REPO/agents/skills/receiving-review/SKILL.md" \
  || fail "architectural-question boundary missing"
# Task 6: correction protocol ordered chain (delete -> verify -> re-resolve -> one replacement)
tr '\n' ' ' < "$REPO/agents/skills/receiving-review/SKILL.md" \
  | grep -q "identify the misplaced comment.*delete it.*verify the deletion.*resolve the correct parent again.*one replacement reply" \
  || fail "correction protocol chain missing"
# Task 6: never leave both replies
grep -qi "do not leave both" "$REPO/agents/skills/receiving-review/SKILL.md" \
  || fail "both-replies prohibition missing"
# Task 3: cross-cutting guideline rule pinned beside the 37.4 family (escaped dots intentional)
grep -q "37\.5\." "$REPO/projects/.ai-playbook/agent_workflow_guidelines.md" \
  || fail "cross-cutting guideline rule missing"
# Task 1: replies stay in the review thread (backlog acceptance) and no-second-reply rule
grep -qi "do not attempt a second reply" "$REPO/agents/skills/receiving-review/SKILL.md" \
  || fail "no-second-reply rule missing"
grep -q "Reply in the thread, not as a top-level PR comment" \
  "$REPO/agents/skills/github-pr-workflow/SKILL.md" \
  || fail "reply-in-thread rule regressed"
# Task 6: both deletion rules name the misplaced-reply exception (distinctive fragments)
grep -q "Misplaced reply correction" "$REPO/agents/skills/receiving-review/SKILL.md" \
  || fail "receiving-review deletion-rule exception missing"
grep -q "Misplaced reply correction" "$REPO/agents/skills/github-pr-workflow/SKILL.md" \
  || fail "github-pr-workflow deletion-rule exception missing"
grep -q "sanctioned deletion exception" "$REPO/agents/skills/receiving-review/SKILL.md" \
  || fail "receiving-review sanctioned-exception wording missing"
# Existing rules stay intact (backlog acceptance: no regression on prior rules)
grep -q "Never resolve threads opened by human reviewers" \
  "$REPO/agents/skills/github-pr-workflow/SKILL.md" \
  || fail "human-thread resolution rule regressed"
grep -q "every resolved bot thread must have a reply first" \
  "$REPO/agents/skills/github-pr-workflow/SKILL.md" \
  || fail "bot-thread reply-before-resolution rule regressed"
# Hygiene gate (repo rule: exit 0 required before commit)
( cd "$REPO" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh ) \
  || fail "public hygiene scan failed"
```

### Task 1: Target-thread verification gate in `receiving-review`

Files:
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/github-pr-workflow/SKILL.md`

- [x] In `github-pr-workflow` "Shared GitHub PR Operations", add a `verify_thread_attachment` operation: input is the reply's GraphQL comment ID plus the intended parent thread ID; query the target thread by its `PRRT_` ID directly (a single-thread node query, not the `reviewThreads(first: 100)` inventory, so pagination cannot produce a false mismatch), locate the reply among the thread's comments, and fail loudly when the reply is not attached to the intended parent thread or the thread's parent comment author, file path, or line does not match the intended target (reply comments carry no path or line of their own; those attributes live on the parent comment). Reference it from the "Reply to review threads" guidelines as the mandatory post-reply check.
- [x] In `receiving-review` "Feedback-source Workflow", extend step 13 (the reply step) with the target-thread verification gate: resolve the PR and fetch the complete thread inventory; select the target by stable thread ID; verify the parent comment author, file path, line, and a distinctive body fragment; post through the source adapter; re-fetch the thread and verify that the new reply is attached to the intended parent.
- [x] State the failure semantics: if the pre-check mismatches or the post-check shows a mismatch, stop and report the state; do not attempt a second reply until the target is re-resolved from current API data.
- [x] Commit: `skills: add target-thread verification gate to receiving-review and github-pr-workflow`

### Task 2: Contract terminology gate in `receiving-review`

Files:
- `agents/skills/receiving-review/SKILL.md`

- [x] Add a "Contract terminology gate" section: before replying about idempotency, retries, deduplication, replay, or conflict behavior, inspect the active API contract and the repository glossary or guidelines; name the actual mechanism in the reply; distinguish durable replay safety (natural keys, unique constraints, insert-if-absent) from `Idempotency-Key` header semantics (key storage, request replay, response replay, mismatch handling); do not replace the repository's chosen term with a stronger or narrower term without evidence.
- [x] State that the gate applies to any contract term with the same ambiguity, not only idempotency.
- [x] Commit: `skills: add contract terminology gate for review replies`

### Task 3: Prohibit unsupported roadmap statements

Files:
- `agents/skills/receiving-review/SKILL.md`
- `projects/.ai-playbook/agent_workflow_guidelines.md`

- [x] In `receiving-review` "Source Thread Replies" rules, add: do not say "future", "planned", "will be added", "separate capability", or similar roadmap language unless an authoritative project source records that plan; when only current scope is known, state current behavior and current scope without forecasting.
- [x] In `agent_workflow_guidelines.md`, add rule 37.5 beside 37.4 as the canonical home of the cross-cutting prohibition: a PR thread reply states current behavior and current scope; it implies a planned follow-up only when an authoritative project source records that plan. The `receiving-review` wording is the operational gate and points to guideline 37.5 rather than restating it as a second canonical rule.
- [x] Commit: `skills+guidelines: forbid unsupported roadmap language in review replies`

### Task 4: Reviewer-reply hygiene checks

Files:
- `agents/skills/receiving-review/SKILL.md`

- [x] Extend "Source Thread Replies" rules (and cross-reference "Forbidden Responses"): reviewer replies contain the technical answer, evidence, and current behavior; omit ticket, PR, task, or internal-session meta-commentary unless needed to identify a code change; omit partner-only questions and decision prompts (aligns with `agent_workflow_guidelines.md` §37.4); avoid performative agreement and gratitude (existing rules stay); use the repository's terminology rather than inventing a status label.
- [x] Commit: `skills: add reviewer-reply hygiene rules to receiving-review`

### Task 5: Architectural-question boundary

Files:
- `agents/skills/receiving-review/SKILL.md`

- [x] Add to "Feedback-source Workflow" (after the classification step): when a reviewer asks whether a new capability should exist, classify the thread as a design decision; if the current contract and authoritative guidelines do not settle it, stop and ask the human partner before posting any substantive accept/reject reply; if the contract does settle it, reply with the contract evidence and no roadmap implication. Reference the existing "Handling Unclear Feedback" stop rule as the enforcement pattern.
- [x] Commit: `skills: add architectural-question boundary for review threads`

### Task 6: Correction protocol for a misplaced reply

Files:
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/github-pr-workflow/SKILL.md`

- [x] Add a "Misplaced reply correction" section to `receiving-review` with the ordered protocol: identify the misplaced comment by API ID; delete it when GitHub permits deletion; verify the deletion; resolve the correct parent again; post one replacement reply; verify the replacement's parent and body (via the Task 1 post-reply check); report the correction briefly in chat.
- [x] Add the hard rule: do not leave both the misplaced and corrected replies in the PR.
- [x] Scope note: the protocol covers inline review threads. A misplaced reply to a top-level PR Conversation comment follows the existing conversation-comment rules (`github-pr-workflow` "Reply to top-level PR Conversation comments"): no delete-and-repost simulation; report the placement error to the human partner in chat and let them decide.
- [x] Amend the surviving deletion rules so the protocol is not contradicted, scoped to inline review threads: in `receiving-review` "Source Thread Replies", amend the "Do not delete or replace reviewer feedback" bullet to name the agent's own misplaced inline-thread reply under the Misplaced reply correction protocol as the sanctioned deletion exception; in `github-pr-workflow`, amend the sentence "Deleting the agent's own response is allowed only when the user explicitly requests comment cleanup and the exact comment IDs have been verified" the same way. The top-level Conversation-comment no-delete-and-repost rule is unchanged in both. Deleting reviewer comments remains forbidden in both.
- [x] Commit: `skills: add misplaced-reply correction protocol to receiving-review and github-pr-workflow`

### Task 7: Final validation

Files: none (validation only)

- [x] Run the full `## Validation Commands` block; every probe passes on the edited tree.
- [x] Run `bash scripts/check-instruction-size.sh` (or the repo's equivalent gate) if it covers the edited skill files; resolve any size-gate finding by consolidation, not by weakening rules.
- [x] On the completion pass (all tasks `[x]`), move the backlog origin file to `docs/history/backlog/completed/` and mark it `Status: done`, per the backlog header's workflow line and the plans Plan Lifecycle.
- [x] Commit (only if the prior items produced no changes; otherwise fold into the fix commit): `chore: validate review-reply gates`

## Disposition of migrated backlog items
- docs/history/backlog/completed/2026-09-16-review-record-kinds-and-sidecar-contract.md: disposition folded into 2026-09-04-review-reply-verification-contract-terminology.md (2026-09-25); per-item file deleted.

- docs/history/backlog/completed/2026-08-17-review-reply-verification-and-contract-terminology.md: disposition folded into 2026-09-04-review-reply-verification-contract-terminology.md (2026-09-25); per-item file deleted.
