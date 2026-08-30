---
name: receiving-review
description: "Use when receiving or addressing existing review feedback from a pull request, RFC, document, or other review system, before implementing suggestions, especially if feedback seems unclear or technically questionable. Trigger phrases: \"address comments\", \"process review feedback\", \"reviewer comments\", \"fix review feedback\", \"respond to review feedback\". Requires technical rigor and verification, not performative agreement or blind implementation. Do not use for a fresh review; use the source's active-review skill instead."
---

# Review Reception

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

## Feedback-source Workflow

Use this workflow when the user asks to process, triage, plan, address, or reply to existing PR review comments.

1. Use the applicable source-specific workflow skill to resolve the feedback context and fetch all live comments or threads.
2. Read all unresolved thread bodies before deciding what to implement.
3. Spot-check resolved or outdated threads against current code before skipping them.
4. Verify each live comment against the referenced file and line.
5. Identify the feedback source and load its source-specific workflow skill before replying or mutating feedback. The source adapter owns comment or thread retrieval, reply mechanics, resolution, and cleanup.
6. **Check branch scope**: before staging any fix, confirm the file belongs to this branch's scope. If a comment touches a file outside the branch's folder (e.g., `individual/<name>/` while on a team branch), plan that fix as a separate commit to the appropriate branch; do not include it in the PR's branch commit.
7. Map each live comment's problem shape to the root-cause families and search the applicable project and user-level lesson corpora for relevant learnings. Apply repository-specific facts from those learnings when evaluating the feedback.
8. Classify each live comment as correctness bug, test quality, cleanup, docs, false positive, or needs clarification.
9. When a bot cites a guideline to justify a flag, look up the guideline and confirm it applies to this specific file type before implementing. Standard license copyright headers, for example, are not subject to PII redaction rules even if the guideline covers the same keyword (see `coding_guidelines.md §12`).
10. Deduplicate comments by root cause. Multiple threads about the same root cause become one task.
11. If any item is unclear, stop and ask before implementing.
12. Implement one root-cause task at a time and verify after each fix.
13. Use the source adapter to reply to each comment after implementation or after deciding no code change is needed.
14. Follow the source adapter's rules for resolution. Never silently delete, resolve, or replace feedback or responses.

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

## Documentation and Comment Findings

When a finding or feedback item targets documentation or comments (outdated doc, verbose or duplicated comment, missing doc), evaluate the artifact itself before editing it. A reviewer asking to "fix the documentation" may be pointing at text that should not survive the fix.

1. **Needed at all?** Keep only documentation that preserves reasons, constraints, conclusions, or requirements not fully clear from the code. A comment or doc section that restates what the code already expresses is a deletion candidate, not a rewording task.
2. **Duplication.** When the comment duplicates the code, or a second doc duplicates a rule another doc owns, prefer delete or a code refactor (rename, extract) over wording changes. Consolidate to the single owning document.
3. **Outdated (contradicts current code).** Decide the disposition explicitly:
   - Remove as obsolete when nothing depends on it.
   - Move to frozen docs as historical context when it records past decisions worth keeping (Layer 3 history per `doc-hierarchy` for company repos; the docs branch for gitignored agent docs). Leave a pointer when readers may search for it.
   - Do not rewrite active documentation to describe old behavior as current.
4. Run the evaluation with the documentation agent's phase 2 gates (`review-agents/documentation.md`); they apply ad hoc to the documents and comments named by the feedback, not only to diff prose.
5. Reply in the thread with the chosen disposition (kept with reason, removed, or frozen) so the decision is auditable.

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

## Default: address all findings regardless of severity

Address every review finding by default, including Low and optional ones, whether the file is in the active change set or a cross-cutting/new subsystem path. Do not ask for confirmation before implementing Low findings; just verify, implement, test, and report. In a regenerating review-fix loop this default is bounded by **Fix-risk triage when fixes regenerate findings** below.

```
DEFAULT: address every finding (Critical/High/Medium/Low, in-scope or cross-cutting).
SKIP only when one of these conditions holds:
  - User explicitly asked to skip, defer, or "no Lows" / "Medium+ only" earlier in the session
  - YAGNI applies (unused feature) -> push back per the YAGNI Check section
  - Suggestion is technically incorrect for this codebase -> push back per the When To Push Back section
  - Finding was already confirmed as `done` by prior code inspection
```

Do **not** drop a finding that asks to strengthen `## Validation Commands` solely because the skill or implementation prose already states the obligation. Skill correctness and validation-gate coverage are separate surfaces (see `development_lessons.md` #186).

"Optional" or "Low" severity signals lower priority for the reviewer, not permission to defer action. If the fix is large or opens a new subsystem, say so briefly in the report but proceed unless a push-back condition above triggers. The Triage Decision Rule below still gates design-decision findings (architectural moves, refactors) - those remain ask-first regardless of severity.

Findings excluded under a SKIP condition or deferred by the user remain valid work unless the exclusion reason is invalidity (YAGNI, technically incorrect, false positive); capture those as backlog items per **Backlog capture for valid findings not fixed in scope** below.

## Triage Decision Rule

When classifying findings for user questions (design decisions, architectural changes, refactors):

**Never unilaterally classify a Medium/High finding as "skip"**: always present it as an explicit question to the user. Only the user can decide to defer or reject a non-trivial architectural decision.

```
❌ WRONG: Present findings #28 and #29 as "Skip: architectural change not needed now"
✅ RIGHT: Ask user: "Finding #28 proposes moving TaxJurisdictionConfig to domain/. Should I do this?"
```

The only findings that may be silently skipped without asking are:
- Findings already confirmed as `done` by prior code inspection
- Findings the user explicitly declined in an earlier question in the same session

All others, regardless of your assessment of their complexity or risk, must be presented to the user. In a regenerating loop this rule is bounded by **Fix-risk triage when fixes regenerate findings** below.

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

## Source Thread Replies

Use the source-specific workflow skill for exact reply, resolution, and cleanup mechanics.

Rules:

- Reply in the existing source thread or comment when the source supports it.
- Do not reply "Fixed" or cite a follow-up branch until the change exists in the working tree or a published commit on that branch.
- Keep replies addressed to the reviewer or document participant, not the human partner directing the work.
- Do not delete or replace reviewer feedback. Do not delete and repost your own response merely to change its location unless the user explicitly requests comment cleanup.

## Soften / intentional revert tracking

When addressing review findings (staging triage or ad-hoc partner feedback):

1. If a finding was already `fixed` / `done` and a later change **restores the prior behavior**, or the partner asks to **soften / undo** that fix, do **not** silently leave triage as `fixed`.
2. Mark the finding triage appropriately (`dropped` or `deferred` with reason) and append a row to `### Soften watchlist` in the current (or newest) staging doc with status `open`.
3. Tell the partner the item is on the soften watchlist so the next `review-loop` / `doing-code-review` round must reaffirm or restage it.
4. Commit messages that undo a review fix should say so explicitly (for example `Soften rN F12: …`) so later rounds can discover the revert from git history if the watchlist was missed.

## Staging doc triage outcomes

When triaging findings from a `doing-code-review` staging doc (execute-plan Phase 3, review-loop step 3):

1. Update each finding **Status** (`done`, `drop`, `pending`, `deferred`) and matching **Triage** field per `review-staging` (`fixed`, `dropped`, `pending`, `deferred`).
2. Recompute `## Review Statistics` → **Triage outcomes** per agent (Staged, Fixed, Dropped, Deferred, Pending). Do not rewrite synthesis tables (Panel, Discarded, Severity calibration).
3. Update the matching `.stats.json` sidecar when present (required artifact per `review-staging`).
4. When an authorizing rule directs a Blocking re-evaluation (see **Fix-risk triage when fixes regenerate findings**), rewrite the finding's **Blocking** bullet in place, record the rationale on its Analysis section, and mirror the flip in the sidecar `findings[].blocking` per review-staging **Severity and ordering** (Triage presentation freeze).
5. When a soften/revert applies, update `### Soften watchlist` in the same pass (status `open` until a later review reaffirms or restages).
6. **Mechanical gate (after the triage update):** re-run the review-staging validator on the staging path so a malformed triage update (broken Triage outcomes, drifted sidecar) cannot be handed back to the orchestrator:
   ```bash
   VALIDATOR="${REVIEW_STAGING_VALIDATOR:-$HOME/.ai-playbook/scripts/validate_review_staging.py}"
   python3 "$VALIDATOR" --hard "$STAGING_PATH"
   ```

This gives downstream analysis a ground-truth signal for which agents produce fix-worthy findings.

## Backlog capture for valid findings not fixed in scope

Review-fix cycles exit on zero unresolved **blocking** findings, not zero findings. Every finding assessed **valid (worth fixing)** that is not fixed in the current work must leave a durable backlog item with all known details before the cycle is reported complete. Gitignored staging docs and chat reports are never the only record. Exception: a must-stay-blocking finding held for the fix-risk user decision (**Fix-risk triage when fixes regenerate findings**) stays `pending` and is recorded as returned-for-ask, not backlogged; once the user decides, apply this section to it (backlog if deferred, fix if directed).

Capture an item when a valid finding ends triage as:

- `deferred`: any severity, any deferral reason (scope, size, risk, user instruction such as "Medium+ only" or "no Lows")
- `dropped` for **scope**: wrong branch for the fix, unrelated to the reviewed change, or excluded from the current work (but not drops for invalidity: false positive, YAGNI, technically incorrect)

Partner-declined fixes and softened reverts stay on the soften watchlist; do not duplicate them as backlog items unless the partner asks for a durable record.

Resolve destination 1 before consulting any later destination; a failed resolution never falls through. A missing `{backlog_dir}` key or missing directory is a bootstrap trigger: run a `bootstrap-ai-playbook` recovery pass to resolve or create the backlog home, and if it still does not resolve, stop and ask the user before recording anywhere else. In a non-interactive run, return that ask to the orchestrator per **Fix-risk triage when fixes regenerate findings**; do not resolve it by choosing a later destination.

Destination, in order:

1. `{backlog_dir}` pre-plan file (key from `.ai-playbook/facts.md`; promote via the `plans` skill when scheduled, move to `backlog_completed_dir` on completion per `doc-hierarchy` and `plans`)
2. Module high-level tasks doc on module-split repos (per `doing-code-review` Step 5.1), only when project guidelines name an existing doc for that module; never create a new doc to hold backlog items.
3. Project issue tracker via its workflow skill (for example `jira-workflow`) when the project tracks backlog there; external write, so create tickets only on explicit user request or standing pre-authorization
4. No destination resolves: ask the user where to record; never silently fall back to chat, the staging doc, `docs/tmp/` (ephemeral), or a newly invented location such as `docs/maintenance/` (Layer 2 living ops, not a backlog inbox).

Required content per item (`{backlog_dir}/YYYY-MM-DD-<slug>.md`; one finding or shared root cause per file; keep the Status/Workflow header lines so `plans`-skill promotion applies):

- Problem statement with evidence: what is wrong and the observed or realistic consequence
- Exact location: file path with line or anchor, or contract/doc section
- Suggested fix, or the options considered when the fix is a design choice
- Severity and source reference: staging doc path, round, finding id
- Why not fixed now: the scope boundary or decision, and who made it

Record the backlog item path on the finding (Analysis section or triage log) so later rounds and downstream analysis can find it.

## Agent corpus feedback (accepted human findings)

When accepted external or human-partner review findings reveal a defect shape the active review panel missed:

1. Map each accepted finding to an **abstract** pattern family (language/project-agnostic), not to a project-specific class or suffix name.
2. Propose the smallest corpus update:
   - New/extended pattern in `review-agents/<lens>.md` when the shape is universal
   - Stack trigger in `doing-code-review/<overlay>.md` when the shape needs framework APIs
   - **Company** guideline note (`company_guidelines_master` under `company_ownership_docs_dir`) when the convention is shared across company repos
   - **Project** guideline note (`project_guidelines_rel`) when the convention is repo-local
   - When both apply, update company for the shared rule and project for the delta; do not duplicate the full company rule only in the project file
3. Do **not** hardcode one repo's test-class suffix or runner name into shared agent catalogs.
4. Offer to apply the skill/guideline patch in the same session when the partner wants it; otherwise record the proposal in chat (or `learn` when they ask to capture the lesson).

## Generalize-on-fix

After a finding is accepted **and** its fix lands (staging triage or ad-hoc partner feedback), prompt a `generalize` pass on the incident: map the instance fix to its root-cause principle family and propose the smallest corpus/catalog update. Follow the `generalize` skill for the pass itself; do not re-implement its extraction here. Narrow instance fixes (that path, that glob) let sibling defects survive later rounds.

**Class-exhaustive fixes for recurring classes.** When accepted findings are new instances of a class an earlier round of the same loop already fixed (more aliased probes, more unpinned obligations, more understated records), fix the class, not the instances: enumerate the full membership mechanically (per-probe match counts in each target file, obligation inventory rebuilt from fix-commit history, per-record diff audit over every record), fix every member in one pass, and record members verified clean as evidence for the next round. A finding list is a sample of the class, not the census; instance-scoped fixes to a class-level defect guarantee the next fresh round re-finds the surviving members.

This is the sibling rule to **Agent corpus feedback** above: that section generalizes findings the panel missed; this step applies the same abstraction to every accepted fix. Do not duplicate its corpus-update placement steps here.

## Fix-risk triage when fixes regenerate findings

When a review-fix cycle keeps regenerating findings, stop folding mechanically and audit the findings before the next fix pass. The trigger is operational: two consecutive rounds in which at least one new finding lands on files modified by the prior round's fixes. Before applying the classifications below, invoke `review-reconciliation` when the recurrence, ownership, or evidence cannot be explained from the current round alone. Pass the chronological review artifacts and sidecars, triage and fix history, current source digest, and permitted mutation scope. Record the per-family regression chain on the affected findings' Analysis sections so a rule 2 refusal stays auditable. This bounds the **Default: address all findings** rule (which back-references this section): an unbounded fold loop can damage more than the findings it resolves.

Classify each remaining finding and record the class next to it:

- **Live-reproduced**: the defect reproduces against current code (command, test, or executed path). These stay fix material.
- **Code-traced**: traced by reading code but not reproduced. Reproduce where cheap; otherwise weigh fix risk before touching the code.
- **Test-gap-only**: the observation is real but the behavior is correct; the gap is missing coverage. Prefer adding the test over changing working code.

Then decide fix vs backlog per finding:

1. **Prefer additive fail-closed fixes.** A guard that rejects previously mishandled input has a near-zero regression surface. A structural rework of the same site has a larger one; do not choose it late in a regenerating loop.
2. **Refuse further surgery on a regressing component family.** Once fixes to one component family have themselves regressed in consecutive rounds, do not attempt another structural change there in this run. Fix a live blocking defect only with the minimal additive change; backlog the rest with the regression chain recorded.
3. **Fail-closed defects on rule-violating input are backlog material**, not fix material: when a validator or tool correctly rejects input that violates its documented contract, the residual defect is hardening, not a live bug.
4. **Flag the fix scope for the orchestrator's focused targeted review**: record which findings were fixed and which workers' domains the fixes touched, so the orchestrator can compose the focused round per `review-panel-selection.md` (Review-loop follow-ups); the triage agent does not launch review rounds.

Report the classification and the fix-vs-backlog decision per finding. Findings backlogged under rules 2-3 are valid unfixed work and get durable backlog items per **Backlog capture**.

This section also bounds the **Triage Decision Rule**: a Critical, High, or Medium finding moved to backlog under rules 2-3 is presented to the user when the session is interactive; in a non-interactive run, record the fix-risk rationale on the affected findings' Analysis sections and surface the backlog path in the loop exit report. When the executing agent lacks direct user access, it does not perform the ask itself: it returns the presentation or stop-for-direction question to its orchestrator, or, when it is the top-level loop agent of a non-interactive run, it applies the stop below; until answered, the finding stays `pending`. A finding with `blocking: true` that triage moves to backlog under rules 2-3 has blocking re-evaluated per review-staging **Severity and ordering** (Triage presentation freeze): apply the severity-calibration **Blocking decision procedure** to the current digest, and flip to `blocking: false` only when leaving the finding unresolved no longer creates concrete risk; a finding that still meets a blocking condition must stay blocking and takes the path below. The Triage outcomes counts change only through the finding's disposition (deferred when backlogged), never through the blocking flag itself. A blocking finding that must stay blocking, including a rule-3 hardening defect, is fix material via the minimal additive change or a user decision, never silent backlog; with neither path available in a non-interactive run, the loop stops for user direction rather than exiting or silently backlogging.

## Integration Points

### With `bootstrap-ai-playbook` skill
Provider for `{plans_dir}` when saving grouped fix tasks and for `{backlog_dir}` / `{backlog_completed_dir}` during **Backlog capture**; the recovery rerun resolves or creates the backlog home when the keys are missing. Read path keys from `.ai-playbook/facts.md` (see `using-skills` Step 0).

### With `review-staging` skill
Triage updates **Triage outcomes** and finding **Triage** fields; preserves immutable synthesis statistics from the review pass. The triage update ends with a `--hard` validator gate (final step of **Staging doc triage outcomes**) before the staging doc is handed back to the orchestrator.

### With `doc-hierarchy` + `plans` skills (backlog lifecycle)
**Backlog capture** items written under `{backlog_dir}` use the `doc-hierarchy` pre-plan backlog format; promotion to a plan and archival to `backlog_completed_dir` follow those skills, not this one.

### With `execute-plan` skill
Invoked as a sub-agent between review rounds. Input is the staging doc from `doing-code-review`. Triage is authoritative for exit: implement valid fixes, mark `drop` or `done`, and leave only validated unresolved issues at `pending`. The orchestrator counts unresolved findings with `blocking: true`, not severity alone. Accepted fixes identify every owning or affected worker for the targeted follow-up. Phase 3 Hard Gate 23 applies **Fix-risk triage when fixes regenerate findings** before further folding; the focused verification round's worker composition follows `review-panel-selection.md`.

### With `review-loop` skill
Orchestration rule 4 applies **Fix-risk triage when fixes regenerate findings** in a regenerating loop; the triage classes and fix-vs-backlog decisions feed its exit report and **Backlog capture** tally.

### With `review-reconciliation` skill
Use reconciliation for recurring-root, contradictory-artifact, or evidence-ownership analysis. This skill retains fix-vs-backlog triage and does not treat reconciliation's artifact changes as independently reviewed; the original review orchestrator must run the next fresh round.

### With `doing-code-review` / `review-agents`
Accepted human findings that the panel missed feed Step 2.5 Guideline Pack awareness and optional catalog/overlay patches (see **Agent corpus feedback** above). Pattern IDs stay abstract; overlays and guidelines carry stack/project detail. Documentation and comment findings are evaluated with `review-agents/documentation.md` phase 2 gates, including the remove-or-freeze disposition for outdated docs (see **Documentation and Comment Findings** above).

## The Bottom Line

**External feedback = suggestions to evaluate, not orders to follow.**

Verify. Question. Then implement.

No performative agreement. Technical rigor always.
