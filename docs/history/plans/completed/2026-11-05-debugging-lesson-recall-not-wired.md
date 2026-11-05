# Plan: Wire lesson recall into systematic-debugging Phase 1

Backlog origin: docs/history/backlog/2026-11-05-debugging-lesson-recall-not-wired.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-05-plan-review-debugging-lesson-recall-not-wired-p5ac2ab0e-r*.md
Execution budget: 0.5h total, largest task 0.5h
Executed: yes (407785dd5c7e07e7bcd41c9e4dcd7cb769ac2f4e)
Authoring claim: 2026-11-05-debugging-lesson-recall-not-wired.md (session sess_0c64b583-40eb-470f-9713-f78af2218bad)

## Terms

- Recall before re-biting: the cross-project instruction (carried in the consuming project's agent instructions, for example `docs/AGENTS.md` in this repository) that directs a worker, before a bug fix, to scan the symptom against the root-cause families catalog and grep the tagged lesson corpora for a matching lesson, applying it before coding.
- Root-cause families catalog: the families index the recall instruction points at (the always-on table in the consuming project's agent instructions; in this repository `docs/AGENTS.md` "Root-cause families", with the full catalog in `projects/.ai-playbook/coding_guidelines.md` section 17, "Root-Cause Principle Catalog (Recall by Problem Shape)"); consumer projects carry their own equivalent.
- Lesson corpora: the tagged lesson files the recall instruction names (the user-level and repository-level development lessons documents).
- Public hygiene scan: the repository's public-hygiene pattern scan over changed files (`scan-public-hygiene.sh`); a task running it expects exit 0.
- Pins suite: `scripts/check_maintenance_pins.sh`, the maintenance pins regression suite; a task running it expects exit 0.
- Lesson-recall pointer: the single Phase 1 direction this plan inserts, pointing at the recall surfaces.
- Phase 1 span: the Phase 1 section's text in the skill, from its heading to the Phase 2 heading.

## Why

Workers using the debugging skill start root-cause analysis without ever seeing the existing lesson-recall practice, so a known lesson matching the symptom is missed exactly where it should guide the fix. A recent session needed an explicit request before prior issue patterns were analyzed. One pointer at Phase 1's start surfaces the existing convention without duplicating it.

## Gist & Examples

TLDR: Phase 1 of the systematic-debugging skill gains a lesson-recall pointer, because the skill's entry point never surfaces the existing recall practice and known lessons go unapplied (code-quality).

Today, Phase 1 ("Root Cause Investigation") lists evidence-gathering steps (read errors, reproduce, check recent changes, instrument boundaries) and then gates fix proposals, but says nothing about consulting prior lessons. A worker who hits a symptom already recorded in the lesson corpora proceeds to a fresh fix and can re-bite a documented mistake. After this change, the first instruction inside Phase 1 tells the worker to consult the applicable root-cause families catalog and lesson corpora (per the cross-project "Recall before re-biting" instruction) and to apply a matching lesson before proposing any fix. The instruction stays the single source of truth: the skill copies no taxonomy, adds no validator, and names no machine-specific paths.

## Outcome

Debugging sessions consult recorded lessons at the moment root-cause analysis begins.

- Phase 1 directs the worker to the root-cause families catalog and lesson corpora before any fix is proposed.
- A matching lesson is applied before the fix path starts, closing the miss the backlog item witnesses.
- The cross-project instruction remains the single source of truth; the skill adds one pointer and nothing else.

Gate delta: none (a prose-only pointer; no refusal class, hard gate, fence, protocol layer, or schema field is added, changed, or removed).

## Assumptions

- assume the pointer belongs at the start of Phase 1's "BEFORE attempting ANY fix" block, before the numbered evidence-gathering steps; basis: the backlog item's exact location names Phase 1, and recall logically precedes evidence gathering as the first consultation.
- assume the pointer references the recall instruction and its surfaces generically (families catalog, tagged lesson corpora) without hardcoding repository paths; basis: skills are vendored across consumer projects whose corpus locations differ, and the repository guidelines forbid personal or machine-specific paths in skill files.
- assume the sibling backlog row covering Phase 4 verification (CI-required checks) stays out of scope; basis: the item's dedup probe and the sibling row's Cluster header keep the two phases distinct.
- assume no skill-side validator or gate is wanted: the pointer stays prose-only, while a repository markdown-span verification asserting the added span is in scope (Task 1); basis: the item's expected fix says the skill "should not copy the root-cause taxonomy or add a new mandatory validator", which targets skill-side workflow machinery, not repository verification.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the pointer sits inside the Phase 1 span and names the recall instruction's surfaces (families catalog and lesson corpora) accurately.
- maintainability: the pointer is one directional reference; the instruction remains the only taxonomy and procedure owner; no duplicated guidance to drift.
- portability: the added text carries no absolute, tilde, or machine-specific paths.

**Done when:**
- Phase 1 contains the lesson-recall pointer and it precedes the evidence-gathering steps.
- The added span contains no `/Users/`, `~/.`, or other machine-specific path token.
- The public hygiene scan and the pins suite both exit 0.

**Ship when:**
- Consumer projects pick up the vendored skill text at their next sync; adoption there is external to this repository [class: EXTERNAL_RELEASE_GATE]; evidence owner: the vendored-sync pass in each consumer project; closure condition: the next consumer sync after this plan lands.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/systematic-debugging/SKILL.md` (Task 1)

**Tests:**
- `scripts/test_debugging_lesson_recall.py` (Task 1) *(new)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/systematic-debugging/SKILL.md` Phase 4 verification wording; reason: owned by the sibling backlog row (Phase 4 CI-check coverage), a distinct duty on the same shared skill surface.
- Any other skill file; reason: the fix is a single pointer on one Phase 1 span.

## Validation Commands

```bash
# Readiness over the plan's own bytes
python3 scripts/plan_readiness.py docs/history/plans/2026-11-05-debugging-lesson-recall-not-wired.md

# Public hygiene scan over changed files (root anchored to the invocation's repository)
REPO="$(git rev-parse --show-toplevel)"; ( cd "$REPO" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh )

# Pins suite
bash scripts/check_maintenance_pins.sh

# New Phase 1 span verification suite
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_debugging_lesson_recall.py -q
```

### Task 1: Add the Phase 1 lesson-recall pointer

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/systematic-debugging/SKILL.md`
- `scripts/test_debugging_lesson_recall.py` *(new)*

Primary class anchors:
- `Phase 1: Root Cause Investigation` in `agents/skills/systematic-debugging/SKILL.md`

- [x] Author the verification suite following `scripts/test_maintenance_runtime_scope.py`'s stated convention (a Markdown policy pinned by normative tokens inside the owning bullet's span) [class: REPOSITORY_TEST]
- [x] The suite asserts, inside the extracted Phase 1 span, the pointer's anchor tokens: the families catalog, the lesson corpora, and the "Recall before re-biting" instruction name [class: REPOSITORY_TEST]
- [x] The suite asserts the pointer's position ahead of the numbered evidence-gathering steps inside the Phase 1 span [class: REPOSITORY_TEST]
- [x] The suite asserts the portability guard: no `/Users/`, `~/.`, or other machine-specific path token, and no duplicated taxonomy text beyond the directional reference [class: REPOSITORY_TEST]
- [x] Run → expect RED: the verification suite fails against the unmodified Phase 1 span [class: REPOSITORY_TEST]
- [x] Insert the lesson-recall pointer as the first direction inside Phase 1's "BEFORE attempting ANY fix" block, ahead of the numbered evidence-gathering steps: consult the applicable root-cause families catalog and the tagged lesson corpora per the cross-project "Recall before re-biting" instruction, and apply a matching lesson before proposing any fix [class: IMPLEMENTATION_REQUIRED]
- [x] The added span cites the instruction by name and stays path-portable: no copy of the families taxonomy, no new validator or gate, and no absolute, tilde, or machine-specific path token [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the verification suite passes against the amended Phase 1 span [class: REPOSITORY_TEST]
- [x] Run the public hygiene scan and the pins suite; both exit 0 [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

Origin row `docs/history/backlog/2026-11-05-debugging-lesson-recall-not-wired.md` (Status: covered-pending-execution) is covered by this plan's execution landing and is deleted in the same completion pass; the Phase 4 CI-check verification duty stays with its sibling backlog row per the plan's scope assumption.
