# Plan: investigate Stage 3 continuity lens

Authoring claim: docs/tmp/authoring-claims/2026-10-08-investigate-blocker-continuity-signal.md (session sess_17e58dd5-8e5f-4d81-bec6-330c62ac65e0)

Backlog origins (scope of record):
- docs/history/backlog/2026-10-08-investigate-blocker-continuity-signal.md
- docs/history/backlog/2026-10-10-standalone-work-branch-closeout.md

Driving force: simplicity
Plan review record: the staging series .ai-playbook/reviews/*-plan-review-investigate-blocker-continuity-signal-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 0.5h total, largest task 0.5h

## Terms

- Continuity lens: the Stage 3 consideration this plan adds: when the investigated evidence shows a blocker interrupting otherwise authorized work, the investigation names the signal and prices removing, narrowing, replacing, or simplifying the blocker through the existing remove-or-keep and cost-pricing duties, preserving protections tied to witnessed harms.
- Blocker: a refusal, gate, or recovery path in the investigated surface that interrupted otherwise authorized work.
- Otherwise authorized work: work a lane or the operator is already entitled to perform, which the blocker interrupted.
- Protective value: the harm a standing blocker prevents, evidenced by a witnessed incident, a red test, or an explicit user decision.
- remove-or-keep axis: the existing Stage 3 axis (remove, keep, keep and narrow, keep and widen); extended by this plan, never restated.
- missing-complement axis: the existing Stage 3 axis (a correct mechanism with a missing complement is completed, not removed); unchanged.
- cost-pricing duty: the existing Stage 3 duty to price the witnessed cost from records before pricing urgency; the lens routes through it.
- Pins suite: scripts/check_maintenance_pins.sh, whose investigate section pins presence spans and three anti-pattern absence literals in the skill this plan edits.
- Pins failing set: the suite's set of failing pin lines on a given tree; the plan requires byte-identical failing sets before and after each task.
- Vendored twin: the runtime-side copy of the skill outside this repository's tracked tree, synced per the repository guidelines' Vendored Asset Sync Rules.
- Lens bullet: the single Stage 3 bullet Task 1 prescribes; the plan's only operative deliverable.
- Stage 3: the investigate skill's possibility-space stage (agents/skills/investigate/SKILL.md, "Stage 3: possibility space") this plan extends.
- Possibility space: Stage 3's enumerated alternative-resolution set (the two standing axes, the witnessed-cost pricing, and the admission step); the lens bullet joins this set.
- Rolling logs: the tracked prompt logs docs/history/backlog/PLAN-PROMPTS.md and docs/history/backlog/EXEC-PROMPTS.md that Stage 4 writes; unchanged by this plan.

## Why

The investigate skill's Stage 3 already prices removing or keeping mechanisms and their witnessed costs, but it never names continuity: an investigation can preserve a blocker that protects a real harm while missing a narrower shape that keeps the protection and lets authorized work proceed. The operator asked whether recent blocker cases signal removing or simplifying blockers to allow uninterrupted work (the origin row, 2026-10-08); without a named lens, that question is re-decided ad hoc per investigation or missed entirely.

## Gist & Examples

TLDR: adds one continuity-lens bullet to the investigate skill's Stage 3 possibility space, so every investigation prices unblocking interrupted authorized work through the existing remove-or-keep and cost-pricing duties; declared force simplicity, motivated by reliability (interrupted authorized work is the cost this closes).

Before: an investigation of a terminal-worker reclaim refusal records the false multi-hour refusal of an authorized next claim and preserves the live-worker fences; whether the fence could be narrowed to release the false refusal without weakening the liveness protection is considered only if the investigator thinks of it unprompted.
After: the same investigation must consider the continuity question explicitly, name the signal, and price the unblocking arms through the existing duties; the disposition lands in the existing recommendation text; the live-worker protection itself stays because its protective value is witnessed.
Edge cases: a safety or integrity blocker with demonstrated independent value remains, with its value and any viable narrower recovery path stated; an investigation with no relevant blocker signal manufactures none and adds no analysis step; the lens adds no gate, validator, ledger, review round, or user question.

Origin-directed authoring walkthrough, the four focused sample contexts (recorded here as design evidence for the lens wording; not execution tasks):

1. Terminal-worker reclaim refusal (docs/history/backlog/2026-10-08-execute-plan-reclaim-after-terminal-worker.md): the witnessed false refusal of an authorized next claim is the blocker signal; the lens prices a narrowed fence shape through the remove-or-keep axis while the live-worker and identity protections stay (their protective value is witnessed).
2. Bounded review self-heal (the origin row covered by commit 9b73528ab): the pause after the one failed self-heal attempt is the signal; the lens prices whether a bounded continuation or a reported handoff restores progress; the never-loop safety condition is the preserved protection.
3. Missing worktree-closeout baseline (docs/history/backlog/2026-10-08-worktree-closeout-baseline-fallback.md): the missing-baseline refusal with an existing safe manual fallback is the signal; the existing cost-pricing duty already orders recurrence pricing before an automation recommendation, and the lens names the continuity frame for that same pricing.
4. Standalone work branch (docs/history/backlog/2026-10-10-standalone-work-branch-closeout.md): the real blocker was the isolated commit having no pull request while pushing the divergent local main would have published unrelated commits; the branch was resolved by the PR merge (7c293e7be, remote branch deleted); the lens records that resolution and prices whether any investigation of the branch-only exclusion is warranted, without broadening the closeout policy: the manual-disposition hold on unmerged work stays, and this plan recommends no exclusion change.

## Outcome

Investigations notice continuity signals and price unblocking through the duties they already run.
- Every Stage 3 possibility-space pass considers whether the evidence shows a blocker interrupting otherwise authorized work.
- The continuity disposition rides the existing recommendation and rejected-alternative text; no new entry field, gate, validator, ledger, review round, or mandatory user question exists.
- A blocker with demonstrated independent protective value stays, with its value and any viable narrower recovery path stated; no signal means no manufactured analysis.
- The change is one prose bullet in one skill file plus its vendored twin; the pins suite's failing set is byte-identical across the change.

Gate delta: no refusal class, hard gate, fence, protocol layer, schema field, validator code path, or ceremony is added or removed; one prose-only duty bullet is added inside the existing Stage 3 possibility-space bullet set (the section's own predicate absorbs the case; the entry's first rejected alternative records why the bare remove-or-keep axis could not); the prose addition is priced by the operator-directed origin row (the 2026-10-08 recorded operator direction is the witnessed gap); explicit none for machinery.

## Assumptions

- assume the lens lands as one bullet inside the existing Stage 3 possibility-space bullet set rather than a new stage or subsection; basis: the origin row's "Integrate this consideration into the existing Stage 3 possibility-space and cost-pricing duties rather than creating a separate gate or ceremony" and the repository guidelines' Skill text anti-growth rules (the named section's predicate absorbs the case).
- assume the continuity disposition rides the existing recommendation text and rejected-alternative dispositions, adding no required entry field; basis: the origin prompt's "Decide whether the continuity reasoning belongs in the existing recommendation text or merits a small explicit disposition in each entry" resolved by the entry's own rejected alternative barring ceremony and by Stage 4's unchanged emission contract.
- assume the four sample contexts are authoring-time walkthroughs recorded in Gist & Examples, not execution tasks; basis: the origin prompt's "Use four focused sample contexts" asks the plan to demonstrate the lens, and this plan's execution is a prose edit whose validation is structural.
- assume interruption pricing uses available evidence only; basis: the origin prompt's "Price interruption from available evidence only; do not invent durations or recurrence".
- assume the branch case's recorded resolution (the PR merge 7c293e7be, the remote branch deletion) and the staying manual-disposition hold are facts of record; basis: the origin row's Evidence and Expected sections.
- assume origin 2's regression-evidence acceptance clause ("adds regression evidence ... if behavior changes") reads as vacuous under this plan because the plan recommends no behavior change in the closeout policy; basis: the clause's own conditionality and the origin prompt's "without broadening the underlying closeout policy".
- assume the pins suite's currently failing set (the documented baseline failures recorded at execution baseline capture) is unchanged by this plan; basis: the pinned investigate sentences live in the corpus bullet, Stage 0, Stage 1, and Stage 4 spans this plan does not touch, and the inserted text avoids the three anti-pattern literals; Task 1 verifies the failing set is byte-identical.
- assume no Primary class anchors blocks are declared because no task owns production behavior (prose-only skill text); basis: the plans skill's anchors requirement is scoped to production-behavior tasks.

Decision points requiring a grill: lens placement read as one Stage 3 bullet inside the existing possibility-space bullet set rather than a new subsection or stage: resolved by the origin row's integrate-into-Stage-3 direction and the repository guidelines' Skill text anti-growth rules, 2026-10-14, affected sections: Terms, Task 1, Gate delta; disposition home read as the existing recommendation text rather than a new per-entry field: resolved by the origin prompt's own decision point and its rejected alternative barring ceremony, 2026-10-14, affected sections: Assumptions, Task 1.

## Standing constraints

- Prose-only: no validator, gate, ledger, hook, review round, or mandatory user question is added; Stage 4's emission contract and both rolling logs' entry shape are unchanged.
- Existing-duty reuse: the lens routes through the remove-or-keep, missing-complement, and cost-pricing duties by reference; it never restates them.
- Anti-pattern literals: the inserted text must not contain the literals 'foreign-origin', 'ownership skip', or 'never grouped, investigated, or dispatched' (the pins suite's absence pins).
- Pins invariance: each task touching the skill verifies the pins suite's failing set is byte-identical to the base state's (the documented baseline failures are pre-existing and out of scope).
- Vendored sync: the skill edit lands in the vendored twin in the same run, or the change leaves the tracked vendored-sync landing path naming the changed files.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the lens bullet sits in Stage 3's possibility-space bullet set, references the existing duties without restating them, and carries the keep-justified-blockers and no-manufacture arms.
- behavior preservation: the pins suite's failing set is byte-identical before and after; no validator, entry contract, or emission shape changes.
- anti-growth: one bullet added; no incident narrative in operative text (the witnessed cases stay in the backlog rows and this plan's Gist); existing duties referenced by name only.

**Done when:**
- agents/skills/investigate/SKILL.md Stage 3 carries the lens bullet with both boundary arms.
- The vendored twin carries the same change, or the tracked vendored-sync landing path names the changed files.
- The pins suite's failing set is byte-identical to the pre-change state's, and no validation gate other than the em-dash gate this plan intentionally flips changes its outcome.

**Ship when:**
- none; this plan is repository-internal with no external release surface.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/investigate/SKILL.md` (Stage 3 possibility-space bullet set)

**Tests:**
- none; the change is prose-only and the validation battery is structural.

**Backlog rows (disposition):**
- `docs/history/backlog/2026-10-08-investigate-blocker-continuity-signal.md` *(deleted at execution completion; covered flip at landing)*
- `docs/history/backlog/2026-10-10-standalone-work-branch-closeout.md` *(deleted at execution completion; covered flip at landing)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, or reconciles a pins row the plan's insertion moved. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the underlying worker, review, and closeout policies (the terminal-worker fence, the self-heal policy, the closeout sweep and its branch-only exclusion); reason: the origin bounds this plan to the investigation contract.
- Stage 4's entry emission contract and the rolling logs' entry shape; reason: the disposition rides existing recommendation text, and a new entry field is the entry's rejected ceremony arm.
- any validator or script change; reason: the plan is prose-only by its Gate delta.
- promoting or rewording the existing remove-or-keep, missing-complement, or cost-pricing duties; reason: they are referenced, never restated.

## Validation Commands

```bash
( cd "$(git rev-parse --show-toplevel)" && bash scripts/check_maintenance_pins.sh )
( cd "$(git rev-parse --show-toplevel)" && bash scripts/check-no-em-dash.sh file agents/skills/investigate/SKILL.md )
( cd "$(git rev-parse --show-toplevel)" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh )
```

Validation preamble (rule 29 record): recorded at authoring and re-verified at execution baseline capture; the pins suite's failing set is captured at execution start and required byte-identical after each task; the em-dash scan over the touched skill file is RED at the authoring baseline (two pre-existing em-dashes in the Stage 3 Admission-step bullet, agents/skills/investigate/SKILL.md:52) and flips GREEN exactly when Task 1's typography fix lands, which is why Task 1 carries that fix (rule 19 RED-today record); the public-hygiene scan passes. The structural checks this plan pins are the two Task 1 grep deliverable gates; no literal-count pins exist, so no rule 22 audit set applies beyond the Task 1 greps themselves.

The pins suite is the behavior-preservation witness (the pinned investigate sentences must survive byte-identical) and each Task 1 grep is the deliverable witness.

### Task 1: the Stage 3 continuity-lens bullet

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/investigate/SKILL.md`

- [x] Stage 3's possibility-space bullet set gains one lens bullet positioned after the two standing-axis bullets, reading: when the investigated evidence shows a blocker (a refusal, gate, or recovery path) interrupting otherwise authorized work, name that signal in the possibility space and price removing, narrowing, replacing, or simplifying the blocker through the remove-or-keep and cost-pricing duties above, preserving protections tied to witnessed harms [class: IMPLEMENTATION_REQUIRED]
- [x] The same bullet carries the keep-justified-blockers arm: a blocker with demonstrated independent protective value (a witnessed incident, a red test, or an explicit user decision) stays, with its value and any viable narrower recovery path stated [class: IMPLEMENTATION_REQUIRED]
- [x] The same bullet carries the no-manufacture arm: an investigation whose evidence shows no relevant blocker signal manufactures none and adds no analysis step [class: IMPLEMENTATION_REQUIRED]
- [x] The same bullet routes the disposition into the existing recommendation and rejected-alternative dispositions and names no new entry field, gate, validator, ledger, review round, or mandatory user question [class: IMPLEMENTATION_REQUIRED]
- [x] The inserted text contains none of the three anti-pattern literals the pins suite excludes, and every existing pinned investigate sentence survives byte-identical [class: IMPLEMENTATION_REQUIRED]
- [x] The skill's vendored twin carries the same change in the same run, or the change leaves the tracked vendored-sync landing path naming the changed file [class: IMPLEMENTATION_REQUIRED]
- [x] The Stage 3 Admission-step bullet's two pre-existing em-dashes are substituted typography-only (wording otherwise unchanged), so the whole-file em-dash gate flips GREEN when this task lands [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect one grep hit per deliverable: the lens bullet's opening span and each boundary arm's span in agents/skills/investigate/SKILL.md, at the spans this task prescribes [class: REPOSITORY_TEST]
- [x] Run → expect the pins suite's failing set byte-identical to the execution baseline capture's, with no new failure naming agents/skills/investigate/SKILL.md [class: REPOSITORY_TEST]
- [x] Commit: `docs: investigate Stage 3 continuity lens` [class: IMPLEMENTATION_REQUIRED]
