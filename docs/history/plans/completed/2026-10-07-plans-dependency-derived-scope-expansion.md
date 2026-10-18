# Plan: dependency-derived deliverable reconciliation in plans authoring

Backlog origin: docs/history/backlog/2026-10-06-plans-dependency-derived-scope-expansion.md
Driving force: code-quality (the origin declares `reliability`, which is not in the closed taxonomy; code-quality is the mapping tag, justified per the template: the plan hardens a workflow decision boundary whose miss shipped an out-of-scope deliverable, a correctness property of the workflow's outputs)
Plan review record: the staging series docs/history/reviews/2026-10-07-plan-review-plans-dependency-derived-scope-expansion-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 1.5h total, largest task 0.75h
Authoring claim: docs/tmp/authoring-claims/2026-10-06-plans-dependency-derived-scope-expansion.md (session sess_1e13991c-8e25-4535-9a7e-ae31500fc603)

## Terms

- dependency-derived deliverable: a deliverable suggested to the author by a dependency edge (a linked or dependent ticket in the tracker context) rather than by the requested item's own goal and authoritative acceptance criteria.
- reconciliation: the Phase 1 enumeration and classification of every dependency-derived deliverable candidate, routing each non-clearly-required candidate through the existing scope-extension hard gate and recording the user's include, split, or defer decision in the Step 1.4 confirmation block's Scope extensions entry.
- scope-extension hard gate: the plans skill's existing Phase 1 gate that bars any work not required by the stated primary goal from entering the plan without an explicit user decision.
- review witness: the review-plan Step 1 audit item that detects a dependency-derived deliverable entering a plan without its recorded reconciliation decision.
- closure matrix: the review-plan Step 1 item 6 backstop pattern (task artifacts verified against Files, Review Scope, and gates); the new audit item follows its placement precedent.

## Why

A company consumer project received a plan whose tasks included a deliverable owned by a dependent ticket, admitted because the dependency graph connected the tickets; the existing Phase 1 scope-extension hard gate was simply overlooked, and nothing in the authoring flow or the review flow asked the dependency question. Dependency edges are sequencing context, never authorization, and an unimplemented dependent behavior must not be specified as current-task work. The fix is a named reconciliation step beside the existing gate plus one review audit that catches the miss, not a second general scope policy.

## Outcome

A ticket-linked plan cannot admit a dependency-derived deliverable without an explicit recorded user decision, and a reviewer catches the miss when it happens.

- Phase 1 gains the dependency-derived deliverable reconciliation: enumerate candidates from the dependency context, classify each non-clearly-required candidate as a scope extension through the existing grill, record the decision in the confirmation block, and keep split and deferred candidates outside the plan with their later verification owner recorded as prose.
- review-plan gains a Step 1 dependency-derived scope audit that flags a dependency-derived deliverable with no recorded decision as a blocking correctness-completeness finding.
- Ordinary dependencies that transfer no deliverable trigger nothing: no enumeration receipt, no decision, no finding.

Gate delta: one fence-class addition priced by the origin's cited completed failure (the witnessed 2026-10-06 consumer incident: a dependent ticket's deliverable entered a plan through the dependency edge with no user decision): the plans Phase 1 grows its checked-condition set (the reconciliation enumeration beside the existing scope-extension hard gate, which stays the governing mechanism and is referenced, not duplicated), and a review-layer duty whose violation blocks is declared separately (the review-plan Step 1 audit item, witnessed in its own text: item 10 records the operator's 2026-10-06 clarification, the origin's cited completed failure, as the duty's witness); the guard liveness ledger's catch-to-incident ratio is 12:14 at authoring time (`python3 scripts/gate_liveness_ledger.py show`, re-derived 2026-10-07 at the r2 fold, superseding the 11:14 figure this line carried at r1 before the tally landing moved it); no refusal class, hard gate, protocol layer, or schema state field is added, and nothing is removed.

## Assumptions

- assume the reconciliation records its decisions in the existing Step 1.4 Scope extensions block rather than a new confirmation block: the origin's Expected paragraph says "Record the answer in the Phase 1 confirmation block", the dispatch entry's prompt paragraph carries the adjudicated dispatch wording of the same duty, the block already exists with the always-renders contract and the grilled-outcome shape, and a second block would duplicate it; basis: docs/history/backlog/2026-10-06-plans-dependency-derived-scope-expansion.md Expected, the dispatch entry's prompt paragraph in docs/history/backlog/PLAN-PROMPTS.md, and the plans skill's Step 1.2 item 6 and Step 1.4 block text.
- assume the origin's declared driving force `reliability` maps to the taxonomy tag `code-quality` with the justification carried on the header line: the closed taxonomy has no reliability tag; basis: the plans template's Driving force annotation.
- assume the review witness lands as a review-plan Step 1 audit item beside the closure-matrix precedent rather than a new lens: the origin's Expected paragraph asks to "Strengthen the plans workflow or its review gate", the dispatch entry's prompt paragraph prices that strengthening as a small witness, the Step 1 checklist is where plan-closure duties live, and the audit needs no new pattern catalog; basis: docs/history/backlog/2026-10-06-plans-dependency-derived-scope-expansion.md Expected, the dispatch entry's prompt paragraph, review-plan Step 1 items 6 through 9, and the plans skill's review-side backstop precedent for the origins-block shape.
- assume the mechanical fixture is a pins-suite row pair (one literal per skill) plus the shared-body runtime-neutrality gate over the edited plans skill: the workflow is prose, so the executable witness is span-presence and forbidden-term gating, not a unit test; basis: the origin's Expected paragraph and the dispatch entry's prompt paragraph (the directly required pin or fixture), and the plans skill's Shared-body forbidden-term precheck rule.
- assume the four validation properties (ordering alone cannot admit; an accepted extension can enter; split and defer stay out; ordinary dependencies do not false-positive) are gated as dedicated span checks over the prescribed prose: each property is a normative sentence the tasks prescribe, so rule 7's dedicated-grep form proves presence and the review rounds prove sufficiency; basis: the plans Validation authoring rules.

Decision points requiring a grill: none remain.

## Standing constraints

- The existing Phase 1 scope-extension hard gate stays the governing mechanism: the reconciliation references it and never restates or weakens it.
- No second general scope policy: the new prose is scoped to the dependency-derived case, and the review audit is scoped to tracker-linked plans whose context names linked or dependent tickets.

## Gist & Examples

TLDR: Phase 1 enumerates what the dependency graph suggests, asks before admitting any of it, records the answer, and a review audit catches the miss (code-quality, mapping the origin's reliability).

**Before (today):** A ticket-linked plan's author reads the tracker's dependency edges and, because the graph connects a dependent ticket, adds that ticket's snapshot-related deliverable to the plan's tasks. The scope-extension hard gate exists but nothing asks the dependency question, so the gate is overlooked; the user must clarify after the fact that the deliverable belongs to the dependent ticket. A reviewer has no named duty to check dependency-derived work against a recorded decision either, so the miss survives review.

**After (this plan):** The same author, in Phase 1, enumerates the candidates the dependency context suggests, classifies each non-clearly-required one as a scope extension, routes it through the existing grill, and records include, split, or defer in the confirmation block's Scope extensions entry; a deferred dependent behavior records its later verification owner and trigger as prose instead of becoming hypothetical tasks. The reviewer runs the new Step 1 audit: a deliverable traceable to a linked ticket with no recorded decision is a blocking finding; a recorded include admits it; split and defer keep it out. A plan whose dependency edges suggest no transferred work triggers nothing at all.

Edge cases: a candidate the requested item clearly requires is ordinary scope and needs no decision; a dependency edge pointing at a ticket whose work never enters this plan leaves no receipt and no finding; an unimplemented dependent behavior is deferred with its verification owner and trigger recorded, never specified as current-task work.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the four normative properties are each stated once in the prescribed prose (ordering alone cannot admit; an accepted extension enters through its recorded decision; split and defer keep the candidate out; ordinary dependencies trigger nothing) and each carries its dedicated validation span.
- regression safety: the pins suite passes; the shared-body runtime-neutrality test passes over the edited plans skill; the em-dash touched scan and the public hygiene scan pass.
- scope discipline: the changes touch only the two skill insertions with their Integration Points lines, the pins rows, and the validation block; the existing hard gate's bytes are untouched (the gate-anchor count gates own this verification) and the Integration Points lines are counted once per file (the per-file span gates own them).

**Done when:**
- Every span check in `## Validation Commands` holds on the executed tree (the property spans present exactly once at their sites, the shared-body gate green, the pins suite green).
- `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )` exits 0.

**Ship when:**
- The next ticket-linked authoring session enumerates its dependency candidates and records decisions for every non-clearly-required one, and the next plan review of such a plan runs the dependency-derived scope audit; they follow from the executed tree.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/plans/SKILL.md` (one paragraph inserted after the Scope-extension hard gate paragraph and one Integration Points line in the With review-plan subsection; all other spans frozen)
- `agents/skills/review-plan/SKILL.md` (one Step 1 audit item appended after item 9 and one Integration Points line in the With plans subsection; all other spans frozen)
- `scripts/check_maintenance_pins.sh` (two pin rows appended beside the existing plans-skill pins)

**Tests:**
- none *(the workflow is prose; the mechanical witness is the pins rows and the shared-body gate, both running existing suites)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py` and the review-staging validator; reason: the origin scopes the witness to the review flow's plan-closure duties, not the readiness gate.
- `agents/skills/execute-plan/SKILL.md`; reason: the witnessed miss is an authoring-time decision, and the origin scopes the fix to plans authoring and its review witness.
- Any new review lens file under `agents/skills/review-agents/`; reason: the audit needs no new pattern catalog (Assumptions above).

## Validation Commands

Authoring-time evidence (rule 29 pre-round): the plan bytes passed the pre-round gate with exit 0 and `OUTCOME: pass`; the em-dash fixer reported 0 substitutions and the touched scan exited 0; the hygiene scan answered `OUTCOME: pass`; the shared-body forbidden-term precheck ran the prescribed insertion text against the gate's term tuple with zero hits; the rule 19 RED-today probes ran all seven property spans against the two skill files at the base tip with 0 matches each (heading to 1 at their sites post-edit); `bash -n` accepted the extracted Validation Commands block. Round-start state for r1: authoring worktree ai-playbook-wt-pdse, branch 2026-10-07-plans-dependency-scope, base main bb2dee78.

```bash
set -euo pipefail
REPO="$(git rev-parse --show-toplevel)"
TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"
[ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"
( cd "$REPO" && test "$(grep -cF 'Dependency edges inform ordering only and never authorize inclusion' agents/skills/plans/SKILL.md)" -eq 1 )
( cd "$REPO" && test "$(grep -cF 'an explicitly accepted extension enters only through that recorded decision' agents/skills/plans/SKILL.md)" -eq 1 )
( cd "$REPO" && test "$(grep -cF 'split and defer keep the candidate outside the current plan' agents/skills/plans/SKILL.md)" -eq 1 )
( cd "$REPO" && test "$(grep -cF 'leaves no decision, no receipt, and no review finding' agents/skills/plans/SKILL.md)" -eq 1 )
( cd "$REPO" && test "$(grep -cF 'Dependency-derived deliverable reconciliation' agents/skills/plans/SKILL.md)" -eq 1 )
( cd "$REPO" && test "$(grep -cF 'A dependency-derived deliverable with no recorded decision is a blocking correctness-completeness finding' agents/skills/review-plan/SKILL.md)" -eq 1 )
( cd "$REPO" && test "$(grep -cF 'recorded Phase 1 reconciliation decision' agents/skills/review-plan/SKILL.md)" -eq 1 )
( cd "$REPO" && test "$(grep -cF 'Scope-extension hard gate (independent of the confidence tiers)' agents/skills/plans/SKILL.md)" -eq 1 )
( cd "$REPO" && test "$(grep -cF 'grill it or remove the implementing tasks before the plan file is written.' agents/skills/plans/SKILL.md)" -eq 1 )
( cd "$REPO" && test "$(awk '/independent of the confidence tiers/{f=1;next} f && /^## /{exit} f' agents/skills/plans/SKILL.md | grep -cF 'Dependency edges inform ordering only')" -eq 1 )
( cd "$REPO" && test "$(awk '/^## Step 1/{f=1} f && /^## Step 2/{exit} f' agents/skills/review-plan/SKILL.md | grep -cF 'A dependency-derived deliverable with no recorded decision is a blocking correctness-completeness finding')" -eq 1 )
( cd "$REPO" && awk '/^## Step 1/{f=1} f && /^## Step 2/{exit} f' agents/skills/review-plan/SKILL.md | grep -qF '10. **Dependency-derived scope audit**' )
( cd "$REPO" && test "$(grep -cF 'dependency-derived scope audit (item 10) consumes the reconciliation decisions' agents/skills/plans/SKILL.md)" -eq 1 )
( cd "$REPO" && test "$(grep -cF 'dependency-derived scope audit (item 10) consumes the reconciliation decisions' agents/skills/review-plan/SKILL.md)" -eq 1 )
( cd "$REPO" && "$TEST_PY" -m pytest scripts/test_execute_plan_runtime.py -k test_shared_skill_bodies_remain_runtime_neutral -q )
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )
( cd "$REPO" && bash scripts/check-no-em-dash.sh touched )
( cd "$REPO" && bash "${PUBLIC_HYGIENE_SCAN:-$HOME/.ai-playbook/scripts/scan-public-hygiene.sh}" )
```

### Task 1: Pin the normative spans (RED probes)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- none (probe-only task)

Evidence:
- the span greps of `## Validation Commands` run against the current bytes; covers the RED-today criterion (every property span absent before the edits)

- [x] Run → expect RED: each of the first seven span checks of `## Validation Commands` fails against the current bytes (counts 0 today), and the shared-body gate, pins suite, and scans pass unchanged [class: REPOSITORY_TEST]

### Task 2: Apply the two prose insertions

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/plans/SKILL.md` (one paragraph after the Scope-extension hard gate paragraph)
- `agents/skills/review-plan/SKILL.md` (one Step 1 item after item 9)

Evidence:
- the span greps of `## Validation Commands`; covers the four property spans, the reconciliation anchor, and the two review-witness spans turning GREEN

- [x] Insert after the Scope-extension hard gate paragraph (which ends `grill it or remove the implementing tasks before the plan file is written.`), as its own paragraph: `**Dependency-derived deliverable reconciliation (tracker-linked requests):** when the request's dependency context (the linked or related issues the Tracker and linked-contract sources step reads, or any named dependent ticket) suggests deliverables beyond the requested item's own goal and authoritative acceptance criteria, enumerate each such candidate in the requirements buffer before any task is written, and classify it: a candidate the requested item clearly requires is ordinary scope; every other candidate is a scope extension and routes through the scope-extension hard gate above (the existing grill; include, split, or defer), with the user's decision recorded in the Step 1.4 confirmation block's Scope extensions entry. Dependency edges inform ordering only and never authorize inclusion: a dependency relationship alone cannot admit a deliverable, an explicitly accepted extension enters only through that recorded decision, and split and defer keep the candidate outside the current plan (a deferred candidate records its later verification owner and trigger as prose beside the decision, never as tasks specifying the unimplemented dependent behavior). Ordinary dependencies whose edges suggest no deliverable transfer trigger nothing: the reconciliation enumerates only candidates, and a linked ticket that adds none of its work to this plan leaves no decision, no receipt, and no review finding.` [class: IMPLEMENTATION_REQUIRED]
- [x] Append as Step 1 item 10 in review-plan, after item 9 (the Tracker-source audit): `10. **Dependency-derived scope audit**: for a tracker-linked plan whose Sources inspected record, origin row, or task prose names a linked or dependent ticket beyond the requested item, verify every deliverable in the Tasks or Files lists that is traceable to a linked or dependent ticket carries a recorded Phase 1 reconciliation decision (a Scope extensions entry naming it with its grill outcome). A dependency-derived deliverable with no recorded decision is a blocking correctness-completeness finding: dependency ordering alone does not authorize inclusion. A recorded include decision admits the deliverable; split and defer decisions must leave it out of the current plan's tasks and files. A plan whose linked tickets contribute no deliverable passes vacuously with no finding. The witness for this duty is the operator's 2026-10-06 clarification that a dependency-owned deliverable was out of scope (the origin row's cited completed failure).` [class: IMPLEMENTATION_REQUIRED]
- [x] Append one line to the plans skill's `### With \`review-plan\` skill` Integration Points subsection: `Plan review's Step 1 dependency-derived scope audit (item 10) consumes the reconciliation decisions this skill's Phase 1 dependency-derived deliverable reconciliation records in the confirmation block's Scope extensions entry (provider: plans; consumer: review-plan).` and one line to review-plan's `### With \`plans\` skill` subsection after the item-9 sentence: `Plan review's Step 1 dependency-derived scope audit (item 10) consumes the reconciliation decisions plans' Phase 1 dependency-derived deliverable reconciliation records in the confirmation block's Scope extensions entry (provider: plans; consumer: review-plan).` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the first seven span checks of `## Validation Commands` [class: REPOSITORY_TEST]
- [x] Commit: `feat: dependency-derived deliverable reconciliation in phase 1 with its review audit` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Pins rows and full validation

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/check_maintenance_pins.sh` (two pin rows beside the existing plans-skill pins)

Evidence:
- `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )`; covers the pins criterion with the two new rows green
- the shared-body gate line of `## Validation Commands`; covers the forbidden-term criterion over the edited plans skill

- [x] Append two pin rows beside the existing plans-skill pins (the `$PL` block): `pin "plans dependency-derived reconciliation gate present" grep -qF 'Dependency edges inform ordering only and never authorize inclusion' "$PL"` and `pin "review-plan dependency-derived scope audit present" grep -qF 'A dependency-derived deliverable with no recorded decision is a blocking correctness-completeness finding' "$repo/agents/skills/review-plan/SKILL.md"` [class: IMPLEMENTATION_REQUIRED]
- [x] Run the complete `## Validation Commands` block → expect exit 0 on the executed tree [class: REPOSITORY_TEST]
- [x] Commit: `test: pin the dependency-derived reconciliation spans` [class: IMPLEMENTATION_REQUIRED]
