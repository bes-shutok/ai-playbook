# Plan: Corpus-level investigation runs as resumable bounded units

Backlog origin: docs/history/backlog/2026-10-15-investigate-corpus-pass-stopped-before-emission.md
Driving force: efficiency + code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-15-plan-review-investigate-corpus-pass-resumability-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 1h total, largest task 0.5h

## Terms

- corpus pass: an investigate invocation whose object is the whole backlog corpus rather than one anchored item.
- census: the Stage 0 cluster survey re-run as the pass's roster and completeness read; the word names the survey when a corpus pass runs it.
- roster: the set of eligible groups the census computes for the pass; an ungrouped open item is its own single-origin group.
- unit: one group carried through Stages 1-4 to a validated, same-turn-committed log entry, or to a recorded skip disposition.
- completion recognition: deciding a unit is done from repository truth only: the group's members are represented by an existing entry's `Origins:` lines in either rolling log or a plans-root plan file; conversational memory is never the progress record.
- completeness check: a fresh Stage 0 census re-run that finds zero eligible groups lacking both an entry and a recorded skip disposition; the only completion signal a pass reports.
- skip disposition: a recorded one-line disposition for an eligible group the pass does not emit an entry for (for example the machinery-quarantine skip), written as a targeted header-line edit on the group's origin rows (the `Quarantine:` line precedent), so a later census reads it; never a silent drop.

## Why

A corpus-level investigate pass stopped four consecutive times after the census with zero entries, and the operator had to reissue the request each time; the fourth attempt succeeded only by working one group per turn to a committed entry. The contract said what the pass emits but not how it continues, so partial progress was invisible and a yield looked like completion.

## Gist & Examples

TLDR: A corpus pass runs as bounded units with repository-truth completion recognition and a census completeness check, because a pass that cannot name its own progress yields half-done and costs an operator reissue (declared force efficiency; the reliability harm lands as the code-quality duty wording).

Before: the pass is one undivided emission obligation; a session that stops after the census leaves no durable trace of which groups remain, and the next turn cannot tell resumption from restart.
After: each unit ends at a committed entry or a skip recorded as a header-line edit on the origins; a resumed pass re-runs the census, subtracts completed units by their committed entries, and continues at the next uncovered group in the logs' urgency order, yielding only at a real gate; the pass reports complete only when a fresh census finds nothing eligible uncovered.
Edge: a group quarantined by the survey's machinery-quarantine skip is recorded as a skip disposition, never silently dropped; a group whose members gained a covering plan mid-pass is complete by the same recognition rule.

## Outcome

A corpus pass survives interruption without operator reissue.

- Each investigated group reaches a validated, committed entry or a recorded skip before the next unit starts.
- A resumed pass finds its remaining work in the repository, not in session memory, and never redoes or silently drops a group.
- The pass's completion claim is a census result, so partial progress cannot masquerade as completion.

Gate delta: prose-only continuation-contract clarification inside the existing Corpus-level invocation paragraph and one pointer sentence in the existing maintenance integration paragraph; no refusal class, hard gate, fence, protocol layer, or schema field is added or removed, no new artifact, cursor, validator, or ledger exists, and no checked set grows; priced by the origin row's own recorded incident, catch frequency, false-positive cost, review date, and rejected alternatives (docs/history/backlog/2026-10-15-investigate-corpus-pass-stopped-before-emission.md), which reject the mandatory cursor, validator, and continuation-gate shapes.

## Assumptions

- assume the rolling-log entries and the existing `Cluster:` graph are sufficient durable state; basis: the origin's Suggested direction ("Reuse the existing logs and current `Cluster:` graph where possible") and its alternative rejecting a mandatory cursor.
- assume the deterministic next-unit rule reuses the logs' standing most-urgent-first ordering, judged as the entry position rule already is; basis: the rolling logs' standing ordering and the existing Corpus-level invocation paragraph.
- assume the per-turn single-investigation bound stays the scheduler's binding; a pass turn may run multiple units only while its window and that binding allow; basis: the existing Corpus-level invocation paragraph and the origin's bounded-group recovery that worked.
- assume the skip-recording surface already exists: a targeted header-line edit on the group's origin rows, the `Quarantine:` line precedent the maintenance survey already writes; basis: the origin's Expected paragraph, the machinery-quarantine precedent, and the targeted-row-edit write discipline.

Decision points requiring a grill: none remain.

## Standing constraints

- Skill-text edits follow the repository guidelines' Skill text anti-growth rules: land the rule; the incident stays in the origin row.
- An edit never rewrites prose outside the lines the task touches, and never reorders existing sections.
- No new gate, validator, ledger, cursor file, or required ceremony: the origin's alternatives reject them and the machinery admission protocol requires a witnessed recurring catch.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the contract reproduces the observed recovery (bounded groups, committed receipts, resume without redo) and closes the witnessed stop shape (census-only yields).
- maintainability: the edit lives in one paragraph plus one pointer sentence; no duty restated, no new surface.

**Done when:**
- the edited skill passes the validation sweep (entry checker, hygiene, portability, doors) with exit 0 each.
- the worked example (a pass interrupted after two of five groups, resumed) classifies correctly under the edited text.

**Ship when:**
- prose-only repository work; no external conditions.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/investigate/SKILL.md`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- any new cursor file, validator, continuation gate, ledger, or required ceremony; reason: the origin row's alternatives reject them and the machinery admission protocol requires a witnessed recurring catch.

## Validation Commands

```bash
python3 scripts/check_investigate_entries.py --log docs/history/backlog/PLAN-PROMPTS.md
bash scripts/scan-public-hygiene.sh
python3 scripts/check_review_agent_portability.py
python3 scripts/test_review_agent_doors.py
```

### Task 1: the Corpus-level invocation paragraph carries the resumable bounded-unit contract

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/investigate/SKILL.md`

Primary class anchors:
- `Corpus-level invocation:` in `agents/skills/investigate/SKILL.md`

- [x] The paragraph carries the unit contract: the census doubles as the roster, and the pass runs one group per unit through the existing stages to a validated same-turn-committed entry or a recorded skip disposition [class: IMPLEMENTATION_REQUIRED]
- [x] The paragraph carries completion recognition from repository truth: a unit is complete when its group's members are represented by an existing entry's `Origins:` lines, a plans-root plan, or a recorded skip disposition's header line on the origins; conversational memory is never the progress record [class: IMPLEMENTATION_REQUIRED]
- [x] The paragraph carries the continuation rule: the next unit is the next uncovered group in the logs' urgency order, a resumed pass re-runs the census and continues without redoing or dropping a group, and a pass yields only at a real gate [class: IMPLEMENTATION_REQUIRED]
- [x] The paragraph carries the completeness check: the pass reports complete only when a fresh census finds zero eligible groups lacking an entry, a covering plan, and a recorded skip disposition; the census reads the origins' own header lines, so the check needs no new surface [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given the witnessed shape (a pass that stopped after the census with zero entries and no durable trace), expects the edited contract to classify that yield incomplete and to make the next turn's resume continue at the first uncovered group rather than restart [class: REPOSITORY_TEST]
- [x] Run → expect RED: the paragraph before the edit names neither the unit contract nor the completeness check (grep probe for "completeness" and "resume", execution-selected) [class: REPOSITORY_TEST]
- [x] Apply the edit inside the existing paragraph, preserving its non-continuation sentences [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the paragraph names the unit contract, repository-truth recognition, the next-unit ordering, the resume rule, and the completeness check [class: REPOSITORY_TEST]
- [x] Commit: `skills: run corpus-level investigation as resumable bounded units` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the maintenance integration scopes the pass continuation truthfully

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/investigate/SKILL.md`

Primary class anchors:
- `The maintenance scheduler turn's monitor step invokes this skill` in `agents/skills/investigate/SKILL.md`

- [x] One sentence in the maintenance integration paragraph, scoped to the monitor's actual trigger: a corpus pass continues under the standing directive that opened it, each turn taking the next uncovered unit while its window allows, and the monitor's investigate leg stays scoped to its own ready-entry trigger [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a pass interrupted mid-corpus with two committed entries, expects the edited text to route continuation to the directive-holding session, not to a monitor leg whose trigger the ready entries suppress [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the integration paragraph names the directive-carried continuation (anchor grep, execution-selected) [class: REPOSITORY_TEST]
- [x] Commit: `skills: scope the resumed corpus pass continuation to its standing directive` [class: IMPLEMENTATION_REQUIRED]

### Task 3: validation sweep, checker, and the interrupted-pass worked example

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/investigate/SKILL.md`

Primary class anchors:
- `Corpus-level invocation:` in `agents/skills/investigate/SKILL.md`

- [x] Run the four Validation Commands; exit 0 each [class: REPOSITORY_TEST]
- [x] Worked example: compose the interrupted-pass case (five roster groups, two committed entries, session dies, a fresh turn resumes) and record in the task log how the edited text recognizes the two completed units, selects group three, and reports incomplete until the fresh census passes [class: REPOSITORY_TEST]
- [x] Corpus duplication audit: search investigate, maintenance, and the rolling-log rules for existing resume or roster duties that overlap the new contract; consolidate or point, none duplicated [class: REPOSITORY_TEST]
- [x] No branch commit (verification task) [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

The origin row was deleted by the authoring landing 1673f0a3c with this plan as the per-row commit-message witness, and the frozen PLAN-PROMPTS entry was pruned with its receipt in the same change. This plan is the covering disposition.
