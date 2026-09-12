# Backlog: company master ownership-scoping loop residuals (r3 deferrals)

- Date: 2026-09-12
- Status: open
- Origin: review-loop r3 on the dedicated ownership-scoping fix (branch 2026-09-11-execute-plan-runtime-residuals, commits eb32be3/52f60ae/fc4ca8c); staged in docs/reviews/2026-09-12-branch-review-2026-09-11-execute-plan-runtime-residuals-r3.md
- Disposition: r3 fix-risk triage deferrals plus r5 cap deferrals (5 of 5 full-panel rounds used; exit round blocking-clean with no fixes)

## Item 1: durable audit trail for lesson-scope skip decisions

- Lens/Pattern: risk / security#ephemeral-skip-witness-no-durable-audit-trail
- Anchor: agents/skills/done/SKILL.md (Step 3 item 4a, witness-echo line after the validator invocation)
- Observation: the out-of-scope note, drift WARNING, and cold-start message are echoed into the Step 7 outcome report, and learn 5c receipts are explicitly temporary run output; an auditor working from repository history alone cannot reconstruct a skip decision.
- Candidate directions: append the drift witness line to the corpus commit message body on the drift path; or accept the transcript-only reconstruction and document it in done 4a.
- Why deferred: committing witness lines to commit messages is a behavior change beyond the wording scope of the ownership-scoping fix; the transcript normally retained by the orchestrator covers the immediate need.

## Item 2: promote the ownership-scoping resolution test to its own numbered item

- Lens/Pattern: design-simplicity / architecture#misplaced-canonical-definition
- Anchor: agents/skills/learn/SKILL.md (Step 1.2 item 5c carries both receipt mechanics and the canonical test; five surfaces cite "item 5c")
- Observation: the canonical definition of a cross-cutting path-resolution algorithm lives mid-paragraph inside the placement-receipt item; five surfaces (item 2b, item 4c, the Step 6 checklist, done Step 3 item 4a, facts `Guideline canonical homes`) cite it there.
- Candidate direction: promote the test to its own numbered item (for example 5d) immediately before 5c and update every citing surface plus the 5b living-surfaces inventory in one change set.
- Why deferred: renumbering at round 3 of a review loop regenerates cross-reference churn across all five surfaces; all current citations resolve correctly.

## Item 3: disambiguate "item 2b" references to fork (2b)

- Lens/Pattern: correctness-completeness / documentation#prose-ambiguous-item-2b-reference (r5, Medium, non-blocking)
- Anchor: agents/skills/learn/SKILL.md lines 100 (5b inventory), 101 (5c routing boundary), 548 (Completion Checklist line)
- Observation: Step 1.2 has a literal item 2b (line 87, the Principle-based Template formatting item), unrelated to fork (2b), the item 4 sub-bullet the ownership-scoping change modified. Three added phrases cite bare "item 2b"; a fan-out executor or checklist verifier can resolve them against the formatting item and leave fork (2b) unmirrored.
- Candidate direction: replace each bare "item 2b" with "fork (2b) (item 4 sub-bullet)" or equivalent, matching the section's existing naming.
- Why deferred: the 5-round full-panel budget was exhausted at the exit round (round 5, blocking-clean, no fixes); a fold would have changed the digest past the last reviewable state.

## Item 4: orphaned "for the lock generation" phrase in the Abandoned-lock definition

- Lens/Pattern: design-simplicity / simplification#delete (r5, Low, non-blocking; peer-owned surface)
- Anchor: agents/skills/done/SKILL.md line 93 ("Abandoned:" definition, trailing qualifier)
- Observation: the peer's lock-generation removal (branch commit 74f9203) stripped `DONE_LOCK_GENERATION` from every acquire/trap/release instruction and the lock script selftest asserts the meta file carries no `generation=` key, but the Abandoned definition still says "there is no matching `<repo>/.ai-playbook/done-lock.session` for the lock generation".
- Candidate direction: drop the qualifier ("...no matching `<repo>/.ai-playbook/done-lock.session` for the lock") or restate in token terms.
- Why deferred: the phrase was introduced by the peer's runtime-residuals change set in the same file; folding it here risks colliding with the peer's in-flight loop.
