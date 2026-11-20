# Plan: Step-anchored lesson recall pointers at three intra-run boundaries

Backlog origin: docs/history/backlog/2026-11-13-step-boundary-lesson-recall-residual.md
Driving force: efficiency
Authoring claim: 2026-11-13-step-boundary-lesson-recall-residual.md (session sess_4c5ad3e9-3aa2-4996-a665-ddc263d3dca)
Plan review record: the staging series .ai-playbook/reviews/2026-11-13-plan-review-step-boundary-lesson-recall-residual-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1h total, largest task 0.5h
Executed: yes (816712a3b5ea2616c5cf905d3906ddefb833ea7f)
Language guidelines: projects/.ai-playbook/python_guidelines.md (the validation battery runs repository python scripts)

## Terms

- Recall surface: the lessons-recall hook under `agents/hooks/lessons-recall/`; its adapters fire on operator prompt submit only, so intra-run step boundaries never consult the corpus.
- Family pointer: the one-line advisory sentence this plan adds to operative skill text at a step boundary, naming by number or by named duty the lesson family a session standing at that step should read before acting.
- Evidence-home family: corpus lessons #46, #287, and #402 in `docs/maintenance/development_lessons.md` (a guard's evidence leg resolves under the root it is invoked with; mirror gate-required records into the source worktree before the retry).
- Scaffold lesson: corpus lesson #346 in `docs/maintenance/development_lessons.md` (draft structured records from the validator's scaffold mode, never from an exemplar copy).
- Self-heal contract: `agents/skills/self-heal/SKILL.md` (the consult-once-per-non-user-only-blocker contract).
- Reset-anchored successor duty: the Reset-anchored successor bullet in `agents/skills/maintenance/zcode-scheduling-primitives.md` (arm the resume carrier at the probe's `reset_at_epoch` plus the arming margin).
- Byte-budget gate: `python3 scripts/skill_text_budget.py --check` (blocking single-read ceiling, advisory ratchet; a change that grows a skill file past its cap deletes equivalent bytes in the same change).
- Pins suite: `bash scripts/check_maintenance_pins.sh` over the guarded spans.
- Em-dash scan: `bash scripts/check-no-em-dash.sh added-lines --base <merge-base>`.

## Why

The lessons-recall hook fires only when the operator submits a prompt, so the three witnessed failures in one window all sat at intra-run step boundaries no prompt event reaches: at two quota walls the session did not consult the self-heal contract or the reset-anchored-successor duty until ordered; a landing was refused on an unused egress acknowledgment although lesson #46's evidence-home family covered the mechanism, with recall happening only during learn, after the refusal; and review records were hand-authored against the canonical-record lesson and refused line-by-line. Skill steps that predictably need a specific lesson family carry no pointer, so the corpus's recall value decays into post-hoc diagnosis. Three one-line pointers at exactly those steps restore the recall without any new hook or machinery.

## Gist & Examples

TLDR: three one-line lesson-family pointers land at the quota-wall pause path, the landing/egress prep step, and the backlog-capture record-authoring duty, so a session standing at those boundaries reads the applicable lesson before acting instead of after, for efficiency.

Before (today): a session hitting a primary-window quota pause schedules its resume carrier and stops, with nothing in the pause text telling it to consult the self-heal contract or the reset-anchored-successor duty; the two witnessed walls needed an operator order before both were consulted. A session preparing a landing composes its egress evidence against whatever home it happens to be in; the witnessed landing was refused on the unused acknowledgment before lesson #46 was recalled. A session composing a captured backlog item or review record drafts the record by hand; the witnessed session rewrote its records after validation refusals.

After (this plan): the same pause bullet carries one advisory line naming the self-heal contract and the reset-anchored-successor duty, so the session reads both at the pause boundary itself. The landing step carries one advisory line naming the evidence-home family (lessons #46, #287, #402), so the session resolves each guard's evidence home under the root that guard is invoked with before the landing call. The backlog-capture composition carries one advisory line naming the scaffold lesson #346, so structured records are drafted from the validator's scaffold mode before any refusal cycle.

Edge cases: the pointers are advisory recall text; every existing refusal, gate, and guard semantics stays unchanged. Each pointer is one line and is priced against its touched file's byte budget; a file the budget gate caps pays equivalent bytes in the same change rather than shipping over cap.

## Outcome

A session standing at a quota pause, a landing/egress preparation, or a record-authoring step consults the applicable corpus lesson at that step, because the step's own text names the family.

- The three witnessed recall failures do not re-pay their post-hoc diagnosis: the pointer is read at the boundary, not recalled after the refusal.
- No new hook, gate, validator, lock, ledger, or schema field exists after this plan; the recall surface stays the existing submit hook.
- Each touched skill file stays within its byte-budget posture, with any cap-crossing growth paid by equivalent deletion in the same change.

Gate delta: none (no gate, validator, lock, ledger, schema field, refusal class, or dispatch-pausing condition is added or removed; three advisory recall pointer lines land in existing operative text).

Follow-up disposition declaration: a witness replay after landing that still shows a boundary consulting a lesson only post-hoc is captured per the maintenance survey's existing learn Step 1.9 project-issue capture (a new backlog row, never a silent residual); no other follow-up lead is anticipated by this plan.

## Assumptions

- assume Task 1's insertion home is `agents/skills/maintenance/zcode-quota-effort.md` (the extracted Quota leg module), not `agents/skills/maintenance/zcode.md` as the origin row's Skill/step line names; basis: `grep -c -i "paus" agents/skills/maintenance/zcode.md` returns 0, the pause path ("when pausing, schedule after `reset_at_epoch`") lives in the extracted module `zcode-quota-effort.md`, and the current-ownership rule puts new work in the final owner, not the pre-split location.
- assume the exemplar-copy lesson the origin names is corpus lesson #346 ("Draft Structured Records From the Validator's Scaffold Mode, Never From an Exemplar Copy"); basis: the corpus heading at `docs/maintenance/development_lessons.md` line 5376 and the origin's Witness 3 wording (records hand-authored against the canonical-record lesson).
- assume the evidence-home family is lessons #46, #287, and #402; basis: the corpus headings (a guard's evidence home resolves under the invoking root; the archive-egress evidence leg mirrors gate-required records into the run worktree; a landing gate's evidence leg resolves only the homes it names), which together cover the witnessed egress-acknowledgment refusal mechanism.
- assume the pointers are advisory text only; no behavioral change to any gate or refusal; basis: the origin row's expected shape ("No new hook and no new machinery").

Decision points requiring a grill: none remain.

## Standing constraints

- Skill text anti-growth rules (repository AGENTS.md): operative text that grows pays for growth; the byte-budget gate (`scripts/skill_text_budget.py`, blocking) is the enforcing instrument, and its advisory ratchet rows are growth-watch signals, never a review-time blocking input.
- Land the rule, not the story: a pointer line cites the lesson family in at most one line; no witness narrative moves into the skill files.
- Tool-agnostic design: pointer lines describe behaviors and name lesson families; they never name agent-specific tool surfaces.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each pointer names lesson families or named duties that exist on disk (numbers and paths re-verified from the corpus and the skill tree at execution, never quoted from memory); a pointer paraphrasing a nonexistent lesson is a defect.
- minimality: each task adds exactly one line at the named boundary; no section is restructured, no adjacent bullet is rewritten.
- growth discipline: the byte-budget gate reports `OUTCOME: pass` after all three edits; any touched file the gate caps pays equivalent bytes in the same change, with the payment named in that task's commit.
- hygiene: the em-dash added-lines scan and the public-hygiene scan exit 0 over the touched set; the pins suite stays green over the guarded spans.

**Done when:**
- the three touched skill files carry their one-line pointers at the named boundaries (Task 1 pause bullet in `zcode-quota-effort.md`, Task 2 landing step in `worktree-first.md`, Task 3 backlog-capture composition in `receiving-review/SKILL.md`).
- the Validation Commands battery passes over the final bytes.

**Ship when:**
- none stated (repository-internal skill text; no external release condition).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/zcode-quota-effort.md` (Task 1)
- `agents/skills/execute-plan/worktree-first.md` (Task 2)
- `agents/skills/receiving-review/SKILL.md` (Task 3)

**Tests:**
- none; the plan adds no test files (the changed surfaces are skill-text pointers verified by the Validation Commands battery).

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work (for example a byte-budget payment deletion in the same touched file), closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/hooks/lessons-recall/` (the recall surface itself); reason: the origin explicitly rejects extending the hook to new events, and this plan's shape is skill-text pointers only.
- `docs/maintenance/development_lessons.md`; reason: the corpus is read, never edited, by this plan; lesson extensions belong to their own learn runs.

## Validation Commands

```bash
python3 scripts/skill_text_budget.py --check
bash scripts/check-no-em-dash.sh added-lines --base <merge-base>
bash scripts/scan-public-hygiene.sh
bash scripts/check_maintenance_pins.sh
```

### Task 1: quota-wall pause path pointer

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/zcode-quota-effort.md`

Primary class anchors:
- `Usable output (pause decision bullet)` in `agents/skills/maintenance/zcode-quota-effort.md`

- [x] The "Usable output" bullet in the Quota leg carries one advisory line, immediately usable at the pause decision: given a session standing at a primary-window pause decision (the "when pausing, schedule after `reset_at_epoch`" step), expects the session to read, before ending the turn, the self-heal contract (`agents/skills/self-heal/SKILL.md`) and the Reset-anchored successor duty (`agents/skills/maintenance/zcode-scheduling-primitives.md`) named by the added line [class: IMPLEMENTATION_REQUIRED]
- [x] The added line names both families by their durable homes (the self-heal contract path and the Reset-anchored successor duty's owning file), staying one line, tool-agnostic, and witness-free [class: IMPLEMENTATION_REQUIRED]
- [x] Run the byte-budget gate; if this file lands over its cap, the same change deletes equivalent bytes elsewhere in this file and the commit message names the payment [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `skill-text: quota pause bullet names the self-heal contract and reset-anchored successor duty` [class: IMPLEMENTATION_REQUIRED]

### Task 2: landing and egress prep pointer

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/worktree-first.md`

Primary class anchors:
- `Land under the lock (lifecycle step 4)` in `agents/skills/execute-plan/worktree-first.md`

- [x] Lifecycle step 4 ("Land under the lock") carries one advisory line at the pre-landing evidence-composition point: given a session composing the egress and review evidence a landing gate will read, expects the session to resolve each guard's evidence home under the root that guard is invoked with and to mirror gate-required records into the source worktree before the landing call, per the evidence-home family named by the added line (corpus lessons #46, #287, #402) [class: IMPLEMENTATION_REQUIRED]
- [x] The added line stays one line, tool-agnostic, and witness-free, naming the family by lesson numbers [class: IMPLEMENTATION_REQUIRED]
- [x] Run the byte-budget gate; if this file lands over its cap, the same change deletes equivalent bytes elsewhere in this file and the commit message names the payment [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `skill-text: landing prep names the evidence-home lesson family` [class: IMPLEMENTATION_REQUIRED]

### Task 3: backlog-capture record-authoring pointer

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/receiving-review/SKILL.md`

Primary class anchors:
- `Backlog capture for valid findings not fixed in scope (item composition)` in `agents/skills/receiving-review/SKILL.md`

- [x] The Backlog capture section carries one advisory line at the item-composition point (before the capture hygiene check): given a session composing a captured backlog item or another structured review record, expects the record to be drafted from the validator's scaffold mode rather than hand-built, per scaffold lesson #346 named by the added line [class: IMPLEMENTATION_REQUIRED]
- [x] The added line stays one line, tool-agnostic, and witness-free, naming the lesson by number [class: IMPLEMENTATION_REQUIRED]
- [x] Run the byte-budget gate; if this file lands over its cap, the same change deletes equivalent bytes elsewhere in this file and the commit message names the payment [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `skill-text: backlog capture names the scaffold-mode record lesson` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-11-13-step-boundary-lesson-recall-residual.md: covered and executed by this plan (three advisory lesson-family recall pointers landed at the quota-pause bullet, the pre-landing evidence-composition point, and the backlog-capture item-composition point; execution commit series 46b116deb, 238eada06, b24015e3f; Phase 3 review r1 ready=yes). Row deleted in this completion pass per the origins-closure completion shape.
