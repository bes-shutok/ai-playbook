# Plan: Authoring closeout follow-through: primary-checkout freeze placement and cross-turn closeout continuation

Authoring claim: docs/tmp/authoring-claims/authoring-closeout-follow-through.md (session interactive-maintenance-20261014)

Backlog origins (scope of record):
- docs/history/backlog/2026-10-14-plan-prompt-freeze-primary-checkout-placement.md
- docs/history/backlog/2026-10-14-authoring-closeout-follow-through-across-turns.md

Driving force: efficiency + code-quality
Plan review record: the staging series {reviews_dir}/2026-10-14-plan-review-authoring-closeout-follow-through-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 1.5h total, largest task 0.5h

## Terms

- Tracked freeze (prompt-log freeze): the `Frozen:` line recorded directly under a `PLAN-PROMPTS.md` entry heading in the tracked shared dispatch log, plus its commit.
- Primary checkout: the repository's default-branch working checkout (the checkout the runtime recipes address in explicit-rooted form), as opposed to an ad-hoc worktree.
- Authoring branch: the ad-hoc worktree's own branch per the Worktree-first standard.
- Entry-keyed authoring: an authoring run whose claim file is keyed to a `PLAN-PROMPTS.md` entry slug or to one of that entry's `Origins:` rows.
- Closeout phase: the span of an authoring session from the plan's ready review state through the Final Step's `done` handoff, landing riders, and worktree removal.
- Resumption boundary: a turn boundary at which an authoring session continues after an interruption: a new user message (including a bare status question), a continuation-summary resume, or an in-session task returning control.
- Explicit-rooted (explicit-rooted form): addressing a primary-checkout path by its recorded root or a git -C prefix, never relative to the session's current directory.
- Claim file: the AUTHORING CLAIM witness file under `docs/tmp/authoring-claims/` (four frontmatter lines); the slug-keyed claim file witnesses an entry-keyed run.
- Worktree-cwd: a session whose working directory is its ad-hoc worktree rather than the primary checkout.
- Done run manifest: the run-manifest record the done skill's setup step writes for the session; the closeout phase's durable record.
- Monitor: the maintenance skill's rolling prompt-log monitor step (the scheduler turn's log duties).
- Origin row: one bulleted origin path under the plan header's Backlog origins block.

## Why

The freeze rule says when an entry freezes, but no surface says which checkout owns the tracked freeze write, so a worktree-cwd authoring session recorded the freeze on its branch and the operator had to redirect it to the main checkout. The closeout duties all exist, yet nothing tells a resumed session to re-derive its remaining closeout scope from durable state, so finishing an authorized lifecycle took repeated operator prompts.

## Gist & Examples

TLDR: name the primary checkout as the tracked freeze's only authoritative placement and require closeout-scope re-derivation at every authoring-session resumption, so worktree authoring stops stranding the freeze on its branch and closeouts finish without repeated operator direction (driving force: efficiency).

**Before (today):** A session authors a plan in an ad-hoc worktree for a prompt-log entry and writes the entry's `Frozen:` line inside the worktree's copy of `docs/history/backlog/PLAN-PROMPTS.md`. The freeze rides the authoring branch, stays invisible to every log reader at the primary checkout until landing, and must be re-anchored before the landing is safe. Mid-closeout the operator asks whether the squash merge and artifact transfer reached the primary checkout, then directs the worktree and branch deletion; each answer restores the remaining scope only as far as the last operator message stated it.

**After (this plan):** The same session writes and commits the freeze at the primary checkout's tracked log before any plan work, explicit-rooted, witnessed by its slug-keyed claim file, exactly like the claim-file write it already performs there; the authoring branch never carries the freeze. At every resumption boundary in the closeout phase the session first re-derives the remaining Final Step obligations from durable state (task boxes, review-gate state, done run manifest, worktree existence, freeze placement, landing state), answers the status question briefly from that derivation, and continues the lifecycle; the completion report claims only verified completion and names remaining exceptions precisely.

**Edge cases:** the monitor's freeze-from-claim duty (the log's freeze rule) stays the backstop writer when an authoring session has not written the freeze itself; both writers act at the primary checkout. A freeze already present is verified, never rewritten. A landing that already carries a legacy branch-written freeze is re-anchored at closeout, not re-authored. A worktree death mid-run leaves the placed freeze standing; the entry reopens only per the log's existing abort rule.

## Outcome

An authoring session anchors its tracked freeze and its remaining closeout obligations to the primary checkout and re-derives them at every resumption, so an authorized plan lifecycle finishes without repeated operator direction.

- A worktree-cwd authoring run's freeze is present and committed at the primary checkout before plan work, without operator correction.
- A resumed authoring session answers a status question from a fresh derivation of its remaining closeout scope and continues to the next obligation without a further directive.
- Completion is reported only over verified state: landing confirmed, artifacts in their primary homes, worktree and branch removed through the existing gates.

Gate delta: no new refusal classes, hard gates, fences, protocol layers, or schema fields, and none removed; the additions are prose-only placement and continuation duties in existing skill text, priced by the two origin rows as completed-integrity-failure witnesses (the witnessed lifecycles completed only through operator rescue: the branch-only freeze needed pre-landing re-anchoring and the closeout needed repeated prompts; unrescued, the landing would have carried a misplaced freeze and the closeout would have stalled).

## Assumptions

- The freeze write at authoring start is one targeted section edit plus one commit at the primary checkout and costs no meaningful delay; basis: the AUTHORING CLAIM duty already writes at that boundary and the monitor already commits log writes at the primary checkout.
- The monitor's freeze-from-claim backstop (the log's freeze rule) remains the second writer; this plan adds placement wording, not a second mechanism.
- The closeout re-derivation reads only existing durable surfaces (plan file, review records, done run manifest, worktree list, landed refs); no new state file, ledger, or checklist artifact is introduced.

Decision points requiring a grill: none remain.

## Standing constraints

- Skill text anti-growth rules (repository guidelines): land the rule, not the story; operative text cites an origin row in at most one line, the witness narrative stays in the rows.
- Tool-agnostic wording: describe behaviors by intent (the primary checkout, an explicit-rooted write), never a tool name.
- No em-dashes in committed files; repo-relative paths only; no personal or machine-specific data in skill text.

## Evaluation Criteria

**Quality dimensions:**
- Consistency: the placement clause names the same checkout and the same owner in every edited surface (the log freeze rule, the plans Phase 0 duty, the maintenance duty wording), checked by reading all three in one pass.
- Single-homing: each rule lands once; sibling surfaces reference rather than restate, checked by grepping for duplicated placement sentences.
- Anti-growth compliance: operative text cites each origin at most once; net byte growth per edited file is named in the landing receipt, checked by the diff stat.

**Done when:**
- The freeze rule in `docs/history/backlog/PLAN-PROMPTS.md` names the primary checkout as the freeze write's authoritative placement and the branch-only shape as not placed.
- The plans Phase 0 duty instructs entry-keyed authoring runs to write the freeze at the primary checkout before plan work.
- The plans Final Step verifies freeze placement at the completion boundary and carries the resumption re-derivation discipline.
- The maintenance log-entry authoring duty names the primary checkout placement.
- `bash scripts/check_maintenance_pins.sh` exits 0; the hygiene scan exits 0; the em-dash sweep over added lines is clean.

**Ship when:**
- The next worktree-cwd authoring run freezes its entry at the primary checkout before plan work with no operator correction, and a resumed closeout continues from one status answer (human-owned condition, observed over subsequent runs).

## Review Scope

**Explicit must-fix:**
- `docs/history/backlog/PLAN-PROMPTS.md` (the freeze rule bullet)
- `agents/skills/plans/SKILL.md` (Phase 0 duty; Final Step recheck and continuation discipline)
- `agents/skills/maintenance/decisions.md` (the log-entry authoring duty's placement words)

**Plan-related extension:** pins-suite expectations and receipts when a pinned span's wording moves; the two origin rows' covered flips at landing; the Integration Points entries in `agents/skills/plans/SKILL.md` and `agents/skills/maintenance/SKILL.md` (conditional reconciliation only, when an edited duty made an existing entry's claim false).

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/template-authoring.md` payload paragraph edits; reason: the dispatched-child payload keeps its current shape, the monitor's freeze-from-claim duty remains the dispatched children's backstop writer.
- `agents/skills/done/SKILL.md`; reason: the done skill already owns the transfer, landing, and removal gates; the continuation gap lands in the plans Final Step, the authoring session's own owner.
- Any new script, validator, ledger, lock, or registry row; reason: the machinery admission protocol requires an incident a gate prevents, and the witnessed miss is follow-through, not a gate-preventable incident.

## Validation Commands

```bash
rg -n "tracked-log write performed and committed at the primary checkout" docs/history/backlog/PLAN-PROMPTS.md
rg -n "primary checkout's tracked log" agents/skills/maintenance/decisions.md
rg -n "beside the claim write and before plan work" agents/skills/plans/SKILL.md
rg -n "re-anchored onto the default branch" agents/skills/plans/SKILL.md
rg -n "resumption boundary" agents/skills/plans/SKILL.md
bash scripts/check_maintenance_pins.sh
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

### Task 1: Place the freeze rule's write in the primary checkout

Files:
- docs/history/backlog/PLAN-PROMPTS.md
- agents/skills/maintenance/decisions.md

Evidence: the `Freeze rule:` bullet in the log's standing rules; the in-session log-entry authoring duty's Self-freeze sentence set and the monitor's freeze leg in the maintenance decisions module.

- [x] In the `Freeze rule:` bullet of `docs/history/backlog/PLAN-PROMPTS.md`, extend the freeze-recording sentence with the placement clause: the `Frozen:` line is a tracked-log write performed and committed at the primary checkout (explicit-rooted form, mirroring the authoring claim file's placement) before plan work proceeds. [class: IMPLEMENTATION_REQUIRED]
- [x] In the same bullet, add the negative placement shape: a `Frozen:` line existing only on an authoring branch or worktree copy is not a placed freeze; it is re-anchored at the primary checkout before further log processing. At most one added line in the bullet cites an origin row. [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/maintenance/decisions.md`, the log-entry authoring duty's Self-freeze sentence folds the placement words in place, stating the freeze write lands at the primary checkout's tracked log, and the monitor's freeze leg names its write as occurring at the primary checkout; no other clause moves and no new clause is added. [class: IMPLEMENTATION_REQUIRED]
- [x] Read all edited surfaces in one pass and confirm each names the primary checkout as the write's placement and the authoring session (or the monitor as backstop) as the owner. [class: REPOSITORY_TEST]

### Task 2: Authoring-session freeze duty and closeout freeze recheck in the plans skill

Files:
- agents/skills/plans/SKILL.md

Evidence: Phase 0's Authoring claim paragraph and setup steps; the Final Step's completion-claims boundary paragraph.

- [x] In Phase 0, add one short duty paragraph beside the Authoring claim paragraph: entry-keyed authoring runs write the entry's `Frozen:` line at the primary checkout as part of Phase 0, beside the claim write and before plan work, witnessed by the slug-keyed claim file. [class: IMPLEMENTATION_REQUIRED]
- [x] The same paragraph takes the reference shape: placement, timing, and the negative branch shape are owned by the log's `Freeze rule:` placement clause, which the paragraph points at and does not restate; an already-present freeze is verified, never rewritten. [class: IMPLEMENTATION_REQUIRED]
- [x] In the Final Step's completion-claims boundary paragraph, add the freeze placement to the completion verification: the tracked freeze the run wrote reads on the default branch as a history read, not a working-copy read, since the landing rider prunes a matched entry's line. [class: IMPLEMENTATION_REQUIRED]
- [x] In the same verification, a freeze found only on the authoring branch, or on a peer branch checked out at the primary checkout, is re-anchored onto the default branch before completion is reported. [class: IMPLEMENTATION_REQUIRED]
- [x] In the same verification, a check that runs after the landing rider has pruned the entry is verification-only with no write target. [class: IMPLEMENTATION_REQUIRED]
- [x] Confirm the added text does not restate the log's freeze rule; the placement consequence lives in the log's rule and the Phase 0 duty names the write and points at it. [class: REPOSITORY_TEST]

### Task 3: Cross-turn continuation discipline in the plans Final Step

Files:
- agents/skills/plans/SKILL.md

Evidence: the Final Step section's closeout duties and completion-claims boundary.

- [x] Add one short paragraph to the Final Step, the continuation discipline: at every resumption boundary inside the closeout phase, the session first re-derives the remaining Final Step obligations from durable state (the plan's task boxes, the review-gate state, the done run manifest, the worktree's existence, the freeze placement, the landing state). [class: IMPLEMENTATION_REQUIRED]
- [x] In the same paragraph, add the question and report clauses: a status question during active work is answered briefly from that derivation and the lifecycle continues; the completion report claims verified completion and names remaining exceptions precisely. [class: IMPLEMENTATION_REQUIRED]
- [x] Confirm the paragraph introduces no new state surface, checklist artifact, or gate; it instructs derivation from existing surfaces only. [class: REPOSITORY_TEST]

### Task 4: Consistency sweep and suite gates

Files:
- none (verification only; a finding routes back to Tasks 1 through 3; the conditional Integration Points reconciliation may edit `agents/skills/plans/SKILL.md` or `agents/skills/maintenance/SKILL.md` per the Review Scope's plan-related extension line)

Evidence: the standing suite gates and the anti-growth review lens.

- [x] Run the Validation Commands block; every command exits 0 or matches. [class: REPOSITORY_TEST]
- [x] Sweep the added lines for em-dashes and absolute paths; sweep the operative text for origin-row citations beyond the one-line budget. [class: REPOSITORY_TEST]
- [x] Verify the maintenance skill's Integration Points entry for the plans skill and the plans skill's maintenance integration entry still state true claims after the edits; touch them only if a claim became false. [class: REPOSITORY_TEST]
