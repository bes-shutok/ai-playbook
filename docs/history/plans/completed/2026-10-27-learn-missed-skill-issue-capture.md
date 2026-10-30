# Plan: learn candidate separation for missed skill invocations

Backlog origin: docs/history/backlog/2026-10-27-learn-missed-skill-issue.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-27-plan-review-learn-missed-skill-issue-capture-p5ee5f2bc-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/learn-missed-skill-issue-capture.md (session zcode-auth-fc20a852-202015Z)

## Terms

- skill-usage issue: a skills-corpus defect identified under Step 1.8 of the learn skill (a skill or script bug, a wrong or ambiguous instruction, a missing runtime deployment, or a trigger failure).
- co-occurring dual failure: one incident that shows both an underlying workflow defect and a missed-invocation.
- workflow-defect candidate: the candidate covering the incident's underlying workflow defect, deduped against the backlog row that covers it.
- missed-invocation candidate: the candidate formed from the agent's own failure to invoke or follow an applicable skill during the witnessed work.
- capture-pass omission candidate: the skills-corpus candidate formed when the capture pass itself omits a candidate its review should have formed, or dismisses one against a different failure mode's coverage.
- candidate-separation text: the two sentences Task 1 appends to the Step 1.8 opening paragraph.
- premature-dismissal anti-pattern: the learn Step 1 block "Anti-pattern: premature dismissal as already covered" in `agents/skills/learn/step-1-extract.md`.
- Step 1.8: the "Skill-usage issue capture" step in `agents/skills/learn/step-1-extract.md`.

## Why

A learn pass reviewed the session where the operator had to invoke `self-heal` manually and reported nothing to capture, because the incident's workflow defect already had a backlog row and a plan; the distinct failure, learn's own missed capture of that skill-usage issue, was never extracted as a candidate, and the operator had to prompt again. Step 1.8's family dedupe and the premature-dismissal anti-pattern both guard the treatment of a candidate that was already formed; neither instructs the formation of the second candidate when one incident carries two failures, and neither treats the capture pass's own omission as a candidate in its own right. A two-sentence addition to the Step 1.8 opening paragraph makes both the dual-failure split and the capture-pass omission candidate operational.

## Gist & Examples

TLDR: Step 1.8 gains the candidate-separation text, so a missed skill invocation is extracted as its own candidate even when the incident's workflow defect is already covered, and the capture pass's own omission is tracked as a skills-corpus defect on the capturing skill's family (driving force: code-quality).

Today, a reviewer applying Step 1.8's dedupe rule can stop at the first matching family: the incident's workflow defect has a backlog row, so the pass concludes "already covered" and never asks whether the agent's own missed skill invocation is a second, separate candidate. The witnessed result: learn reported "no new lessons" for a session whose skill-usage failure the operator then had to point out by hand. After the change, the same input produces candidates with independent dedupe:

- workflow-defect candidate: deduped against the row covering the workflow's underlying defect, including rows already covered by a plan;
- missed-invocation candidate: deduped against items on the same skill and step whose failure mode is the missed or wrong invocation itself;
- capture-pass omission candidate: when the pass omits or wrongly dismisses one of the above, that omission is its own candidate on the capturing skill's family, so learn's own review misses are tracked like any other skills-corpus defect.

Coverage of the workflow defect never dismisses the missed-invocation candidate, and the reverse.

## Outcome

Learn reliably extracts and tracks an agent's missed skill invocation, and its own capture misses, as skills-corpus defects, even when the same incident's workflow defect is already covered elsewhere.

- A co-occurring dual failure yields candidates with independent dedupe targets, surveyed across open and covered items alike.
- A capture pass that omits or wrongly dismisses a candidate produces its own skills-corpus candidate on the capturing skill's family.
- The operator no longer needs to prompt a second time for learn to capture its own workflow's skill-usage failure.
- The capture duty stays two sentences inside the existing Step 1.8 flow, with no new section, validator, gate, or ceremony.

Gate delta: none (no gate, validator, fence, protocol layer, or schema field added or removed; prose-only instruction clarification inside an existing skill section).

## Assumptions

- assume the witnessed incident carries two distinct failures: the workflow's missed self-heal invocation, and learn's own missed capture of that skill-usage issue; basis: the origin row docs/history/backlog/2026-10-27-learn-missed-skill-issue.md, and the covering plan docs/history/plans/2026-10-27-self-heal-before-workflow-stop.md whose scope is the workflow defect only.
- assume the primary gap sits at candidate formation, not dismissal: the premature-dismissal anti-pattern verifies a formed candidate before discarding it, and the witnessed pass never formed the missed-invocation candidate; the appended text also arms the adjacent dismissal-shaped guard (a dismissal citing a different failure mode's coverage), priced by the same witness; basis: the origin row's Problem section read against the Step 1.8 and anti-pattern text at authoring time.
- assume the remedy is two sentences inside the existing Step 1.8 opening paragraph, with no new section, validator, gate, or required ceremony; basis: the dispatch entry's scope arms (PLAN-PROMPTS entry learn-missed-skill-issue-capture) and the repository skill anti-growth rules; the second sentence is required by the origin row's own expected behavior ("Step 1.8 should capture a distinct learn issue when learn's candidate review omits one"), which the first sentence alone does not produce for the witnessed incident.
- assume the one-sentence-ask of the dispatch entry resolves to this two-sentence minimum: the no-change disposition was rejected because the existing rules were in force and the pass still missed, the single dual-failure sentence alone re-derives the covering row's subject instead of the learn-family omission the row demands, and the two-sentence text is the smallest operative change that prices the witnessed recurrence; this line is the maintenance-selected decision receipt for the dispatch entry learn-missed-skill-issue-capture (2026-10-27), recorded here in full.
- assume no test suite pins the Step 1.8 opening paragraph's prose, while scripts/test_learn_router_dispatch.py does pin the edited file's module headings byte-identically and is red on main for a pre-existing drift (the file carries "## Step 1.9: Project issue backlog capture", added 2026-10-19, absent from the test's expected table, last updated 2026-10-18); the prescribed append introduces no heading and cannot trip that pin, so the expectation is no NEW failures beyond the pre-existing Step 1.9 heading-table drift, and the table's repair is a separate tracked change outside this plan's scope; the skill text byte cap (scripts/skill_text_budget_caps.json) caps agents/skills/learn/SKILL.md, not step-1-extract.md; basis: the suite's frozen heading contract read and run against the plan branch at review time.
Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: reading the edited Step 1.8 against the origin row's incident names which candidate is which, and the capture-pass omission candidate lands on the capturing skill's own family.
- simplicity: exactly two sentences added; the section's existing enumeration, dedupe rule, and backlog-home text unchanged.
- maintainability: the appended text reads as part of the existing identify-then-dedupe flow and does not duplicate the premature-dismissal anti-pattern.

**Done when:**
- the Step 1.8 opening paragraph carries the candidate-separation text from Task 1 and no other section of the file changed.
- `bash scripts/check-no-em-dash.sh file agents/skills/learn/step-1-extract.md` exits 0.
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` exits 0.
- the learn router-dispatch suite reports no NEW failures beyond the pre-existing Step 1.9 heading-table drift recorded in Assumptions.

**Ship when:**
- none; the change is repository-internal with no external release condition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/learn/step-1-extract.md` (Task 1) (Step 1.8 opening paragraph only; all other sections and steps in this file are frozen; reject any review finding that touches them)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/test_learn_router_dispatch.py`; reason: the heading table's pre-existing Step 1.9 drift predates this plan and its repair is a separate tracked change on a file this plan does not own.
- `docs/history/backlog/2026-10-27-self-heal-before-workflow-stop.md`; reason: that row and its covering plan own the workflow-defect failure, a distinct candidate this plan deliberately does not rework.
- `docs/history/backlog/2026-10-27-learn-missed-skill-issue.md`; reason: the origin row is this plan's scope-of-record input; its covered flip rides the landing lifecycle, not this plan's tasks.

## Validation Commands

```bash
bash scripts/check-no-em-dash.sh file agents/skills/learn/step-1-extract.md
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_learn_router_dispatch.py -q
python3 scripts/plan_readiness.py docs/history/plans/2026-10-27-learn-missed-skill-issue-capture.md
```

(The readiness command is the plan-lifecycle certification gate: it passes once this plan's authoritative review record pair exists in the resolved reviews home; it is not an edit gate.)

### Task 1: Append the candidate-separation text to Step 1.8

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/learn/step-1-extract.md`

Primary class anchors:
- `Step 1.8` in `agents/skills/learn/step-1-extract.md`

Exact text to append (verbatim, at the end of the Step 1.8 opening paragraph, after its final sentence and before the "**Backlog home**" paragraph):

```text
When one incident shows both an underlying workflow defect and the agent's own missed or wrong invocation of an applicable skill, these are two separate candidates: extract and dedupe each against its own failure mode, surveying covered items as well as open ones. When the capture pass itself omits a candidate its review should have formed, or dismisses one as covered by an item that covers a different failure mode, that omission or dismissal is its own skills-corpus candidate on the capturing skill's family.
```

- [x] The Step 1.8 opening paragraph ends with the candidate-separation text, appended after its final sentence and before the "**Backlog home**" paragraph [class: IMPLEMENTATION_REQUIRED]
- [x] The appended text is verbatim the exact text quoted in this task's Context block above [class: IMPLEMENTATION_REQUIRED]
- [x] No other section or step of the file changed: given `git diff main -- agents/skills/learn/step-1-extract.md`, expects exactly one paragraph gaining the two sentences [class: REPOSITORY_TEST]
- [x] The edited wording routes the witnessed incident to named, separately deduped candidates: the workflow-defect candidate dedupes against the covering row, the missed-invocation candidate dedupes on its own failure mode across open and covered items, and the capture-pass omission candidate lands on the capturing skill's own family [class: REPOSITORY_TEST]
- [x] Run `bash scripts/check-no-em-dash.sh file agents/skills/learn/step-1-extract.md`, expect exit 0 [class: REPOSITORY_TEST]
- [x] Run `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh`, expect exit 0 [class: REPOSITORY_TEST]
- [x] Run the learn router-dispatch suite per Validation Commands, expect no NEW failures beyond the pre-existing Step 1.9 heading-table drift [class: REPOSITORY_TEST]
- [x] Commit: `learn: separate co-occurring missed-skill-invocation candidates in Step 1.8` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-10-27-learn-missed-skill-issue.md (this plan's origin row, Status: covered by this plan): deleted from the living backlog in the landing change; this archived plan is its durable home. The change landed as Task 1 (commit 392f864cd on the run branch, squash-landed to main); execution review record: .ai-playbook/reviews/2026-10-29-plan-review-learn-missed-skill-issue-capture-r3.md (plus the r1/r2 series) and the Phase 3 code review .ai-playbook/reviews/2026-10-29-learn-missed-skill-issue-capture-code-review-r1.md.
- docs/history/backlog/2026-10-27-self-heal-before-workflow-stop.md: out of scope by this plan's Review Scope (owns the distinct workflow-defect candidate); dispositioned by its own covering plan.
