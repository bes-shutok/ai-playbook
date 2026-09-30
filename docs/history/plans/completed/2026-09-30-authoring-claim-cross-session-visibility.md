# Interactive authoring must run the existing authoring-claim duty so cross-session collisions refuse at start

[github: https://github.com/admitriev/ai-playbook] Origin: docs/history/backlog/2026-09-30-authoring-claim-cross-session-visibility.md
Driving force: reliability

## Gist TLDR

TLDR: wire the existing AUTHORING CLAIM duty into the plans skill's Phase 0 setup and give selection the same origin-level consult execution selection already has, so interactive authoring refuses same-origin collisions at start instead of after two review rounds.

The authoring-claim machinery already exists - but its audience excludes sessions that run only the plans skill's Phase 0 setup. The writer (the AUTHORING CLAIM duty: noclobber create of `docs/tmp/authoring-claims/<backlog-item-basename>.md` in the primary checkout, refreshes, closeout delete, foreign-claim refusal, stale takeover) is the AUTHORING CLAIM paragraph in `agents/skills/maintenance/prompt-templates.md`, executed by payload-born authoring sessions (and mapped onto in-session scheduler authoring by the rolling-log duties); the reader (the G1a discovery arm) lives in the scheduler turn's lane-occupancy evaluation. A session that runs only the plans skill's Phase 0 worktree-first setup never sees the duty: it writes no claim, and nothing consults the surface when that session selects its target. Witnessed 2026-09-30: two such lanes ran full authoring-plus-review passes on the same open backlog origin (landing `0f4b7cf5` raced peer commits `a7b470e3`/`f18d818c`). Fix: wire the existing duty into the plans skill's Phase 0 by reference (prompt-templates.md stays the procedure of record, byte-for-byte), and give the maintenance Step 1 survey and D2 selection the same origin-level consult the D1 execution selection already has for fresh execution claims.

## Outcome + Gate delta

Gate delta: one duty's refusal audience extended to interactive sessions (by reference, no recipe copied), one selection checked-condition added per lane decision site, one sanctioned-reason addition, and two Integration Points attestations.

After this plan:

- Any authoring session - interactive or payload-born - announces itself at start: the plans skill's Phase 0 Authoring Worktree Setup runs the AUTHORING CLAIM duty before any plan work. That paragraph owns the four frontmatter lines, the create-if-absent noclobber create keyed on the target backlog item's basename, the refresh cadence, the fresh-foreign-claim refusal and stale-foreign-claim takeover, and the deletes at closeout (the done handoff) and on a refusal stand-down this session already owned - the witnessed collision now fails fast at Phase 0 instead of after two review rounds.
- Selection consults the surface: the Step 1 survey and the D2 authoring selection skip a backlog item whose fresh foreign claim sits in the resolved tmp directory's `authoring-claims/` at the primary checkout, with the skip recorded in `decision_reason` and admitted to the sanctioned must-dispatch exemption list - mirroring D1's fresh-execution-claim skip in shape and vocabulary, and carrying the same facts-`tmp_dir`-override caveat the G1a discovery arm already documents for its own readers.
- The G1a discovery arm, the execution-claim surface, and the rolling prompt log's freeze rule are untouched: the freeze rule already keys on "a live authoring claim file keyed to the entry slug or one of its origins", and it starts seeing Phase-0-only claims for free once those sessions write them.

Out of scope: the AUTHORING CLAIM paragraph's own text (prompt-templates.md stays byte-frozen), the payload templates, the G1a discovery arm's lane-occupancy semantics, the execution-claim surface, and the duplicate-origin coverage gate (the sibling origin item `2026-09-30-origin-coverage-lifecycle-and-landing-gate.md`).

## Terms

- **AUTHORING CLAIM duty**: the procedure of record in `agents/skills/maintenance/prompt-templates.md` (four-line frontmatter `session:`/`item:`/`created:`/`updated:`, create-if-absent noclobber create, refresh cadence, ownership re-checks, deletes at closeout and on an owned stand-down, fresh-foreign-claim refusal, stale-foreign-claim takeover).
- **Claim surface**: the resolved tmp directory's `authoring-claims/` at the primary checkout (`docs/tmp/` default), keyed by the target backlog item's file basename.
- **Interactive authoring session**: a session running the plans skill's Phase 0 worktree-first setup that was not dispatched from a payload template carrying the duty and is not an in-session scheduler authoring run.
- **Fresh foreign claim**: a claim file foreign per the AUTHORING CLAIM gate - its `session:` line names a different session id, including the gate's rule that a claim with no parseable `session:` line is foreign - whose `updated:` is fresher than one cadence period (2 hours).

## Assumptions

- Wiring by reference, not restatement: the plans skill's Phase 0 section names the AUTHORING CLAIM duty and its procedure-of-record home instead of copying the recipe (the by-reference precedent is execute-plan SKILL.md's Phase 0 "Execution claim registration" step, which names the EXECUTION CLAIM paragraph as its procedure of record); one owner, no drift.
- The selection-time consult is admission control, not a new guard: the skipped target stays dispatchable for the next turn (the claim decays or its owner finishes), and the skip joins the existing sanctioned-reason list so no dispatch-defect `turn_error` fires in the check-then-select race window - the same treatment D1's fresh-execution-claim skip already has.
- An interactive session with no backlog origin (a direct user request) extends the duty's `item:`-line semantics to carry the plan slug when no backlog item exists - a sanctioned extension, not a match of the item-line's backlog-path semantics; plan-slug claims never match backlog-item targets, so the consult never skips on them, and the G1a arm stands aside from them whenever the target-distinctness sanction is recorded (conservatively occupying the lane otherwise, as any unexplained foreign claim).

Decision points requiring a grill: none - the mechanism, surface, keying, freshness, and refusal semantics all already exist in the AUTHORING CLAIM duty; this plan only extends their audience to Phase-0-only sessions and adds the selection-time consult mirroring an existing D1 skip.

### Task 1 - Plans skill: Phase 0 runs the AUTHORING CLAIM duty

- [ ] In `agents/skills/plans/SKILL.md`, the "Phase 0: Authoring Worktree Setup" section: add the claim duty wiring - before any plan work, run the AUTHORING CLAIM duty (procedure of record: the AUTHORING CLAIM paragraph in `agents/skills/maintenance/prompt-templates.md`, which owns the frontmatter lines, the noclobber create, the refresh cadence, the refusal and stale takeover, and the closeout/owned-stand-down deletes); an interactive session with no backlog origin extends the `item:` line to carry the plan slug per the Assumptions. Do not restate the recipe's operational steps in this file. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the same file, the Integration Points section: add the maintenance-skill consumer entry (the Step 1 survey and D2 selection consult this surface per Task 2); the bidirectional attestation follows the repository's Integration Points rule with maintenance's investigate entry as the working exemplar, not the execution-claim wiring (whose precedent is the one-directional Phase 0 step). [class: IMPLEMENTATION_REQUIRED]

### Task 2 - Maintenance skill: selection skips origins holding a fresh foreign claim

- [ ] In `agents/skills/maintenance/SKILL.md`, the Step 1 survey and the D2 authoring selection: add the claim consult - before selecting an authoring target, read the resolved tmp directory's `authoring-claims/` at the primary checkout; a target whose fresh foreign claim sits there (foreign per the AUTHORING CLAIM gate, including the no-parseable-session-line rule) is skipped as occupied, the skip recorded in `decision_reason`, and the reason added to the sanctioned must-dispatch exemption list; a stale claim does not block selection and remains the payload takeover path's input. Keep the payload's literal `docs/tmp/authoring-claims/` caveat discipline: the consult reads where the duty writes, and the G1a arm's existing facts-`tmp_dir`-override caveat extends to this third reader. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the same file, the Integration Points section: add the plans-skill producer entry attesting the same contract from the reader side. [class: IMPLEMENTATION_REQUIRED]

### Task 3 - Validation

- [ ] All checks in Validation Commands pass from the worktree root. [class: REPOSITORY_TEST]

Files: `agents/skills/plans/SKILL.md` (the "Phase 0: Authoring Worktree Setup" section and Integration Points only), `agents/skills/maintenance/SKILL.md` (Step 1 survey, D2 selection, and Integration Points only).
Evidence: the grep literals below verified absent from both files on main before authoring; `prompt-templates.md` byte-unchanged baseline verified (`git diff --quiet main` empty).

## Evaluation Criteria

- The plans skill's Phase 0 section runs the AUTHORING CLAIM duty by reference (procedure of record named with its home, recipe not restated - no duty-distinctive recipe literal such as the noclobber `set -C` step appears in plans SKILL.md).
- The Step 1 survey and D2 selection skip fresh foreign claims with a recorded reason and a sanctioned exemption; stale claims do not block.
- Both Integration Points sections attest the contract bidirectionally.
- `agents/skills/maintenance/prompt-templates.md` is byte-unchanged.

## Review Scope

Files: `agents/skills/plans/SKILL.md` (the "Phase 0: Authoring Worktree Setup" section and Integration Points only), `agents/skills/maintenance/SKILL.md` (Step 1 survey, D2 selection, and Integration Points only). Contract files referenced read-only: `agents/skills/maintenance/prompt-templates.md` (the AUTHORING CLAIM paragraph, the procedure of record), `agents/skills/execute-plan/SKILL.md` (the Phase 0 execution-claim wiring as the by-reference precedent), origin backlog item, sibling origin item `2026-09-30-origin-coverage-lifecycle-and-landing-gate.md`.

## Validation Commands

Run from the worktree root; every check fails closed (a miss or an error aborts non-zero):

1. `grep -q "AUTHORING CLAIM" agents/skills/plans/SKILL.md || { echo FAIL: duty unwired; exit 1; }` - Phase 0 names the duty (zero hits on main today, so this flips on the change).
2. `grep -q "prompt-templates.md" agents/skills/plans/SKILL.md || { echo FAIL: home pointer missing; exit 1; }; grep -q "set -C" agents/skills/plans/SKILL.md; st=$?; [ "$st" -eq 1 ] || { echo "FAIL: recipe restated (rc=$st) or grep tool error"; exit 1; }` - the wiring references the procedure of record, and the recipe's distinctive noclobber literal is absent (the three-way status split passes only grep rc 1, failing both rc 0 and tool errors per the plans skill's validation rule).
3. `grep -q "fresh foreign claim" agents/skills/maintenance/SKILL.md || { echo FAIL: consult missing; exit 1; }` - the selection consult exists (zero hits on main today).
4. `git diff --quiet main -- agents/skills/maintenance/prompt-templates.md || { echo FAIL: procedure of record modified; exit 1; }` - the duty text is byte-unchanged (git's own exit status is the boolean, no pipe to swallow it).
5. `test "$(grep -c "^## Integration Points" agents/skills/plans/SKILL.md)" = "$(git show main:agents/skills/plans/SKILL.md | grep -c "^## Integration Points")" || { echo FAIL: section structure changed; exit 1; }` - both baseline legs explicit, anchored to section headings so entry-prose mentions of the phrase cannot bump the count; the attestation lands inside existing sections.
