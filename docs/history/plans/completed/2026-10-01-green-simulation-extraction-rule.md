# GREEN-simulation insertions must be extracted from the plan's prescribed spans, never re-typed

[github: https://github.com/admitriev/ai-playbook] Backlog origin: `docs/history/backlog/2026-09-30-plans-green-simulation-must-extract-prescribed-spans.md`
Driving force: code-quality; secondary simplicity

## Gist TLDR

TLDR: add one authoring rule (rule 44) to the plans skill's Validation Commands authoring rules: a GREEN-polarity simulation's inserted bytes are extracted mechanically from the plan's own prescribed spans, never re-typed from recall, and any count or content expectation derived from a simulation whose insertions are not byte-identical to a prescribed span is unpinnable - closing the simulation-vs-prescription divergence class at authoring time instead of at a review round.

Witnessed 2026-09-30: an authoring-time count gate pinned the simulated 6 where a faithful landing reads 5, because one unprescribed summary sentence crept into a hand-rebuilt scratch tree; five review workers re-derived the 5, costing a blocking review round, a re-pin, and a re-simulation. The existing rules govern the simulation's polarities (rule 41), its duplicate direction (rule 36), and hand-written transform expectations (rule 24), but none pins the fidelity of the simulation's input bytes.

## Outcome + Gate delta

Count and content expectations derived from authoring-time simulations stand on prescribed bytes: the derivation chain (prescribed span -> extracted insertion -> simulated tree -> expectation) is mechanical and re-runnable, and a divergent simulation is void before it can pin a wrong number. The recert round this defect class costs disappears.

Gate delta: one numbered authoring rule added to `agents/skills/plans/SKILL.md`'s Validation Commands rules list (rule 44, after rule 43); no script, hook, validator, catalog change, refusal class, hard gate, fence, or protocol layer is added.

## Terms

- **GREEN-polarity simulation**: an authoring-time execution of a plan's gate against a scratch tree carrying the plan's prescribed insertions (rule 41's pass-state run; rule 36's temp copy).
- **Prescribed span**: insertion text a plan task quotes as the bytes to insert (the quoted literal inside a task's checklist item or its named insertion block).
- **Extraction**: copying a prescribed span into the scratch tree programmatically from the plan file's own text (a grep/sed/python one-liner over the plan), so the inserted bytes are byte-identical to the prescription by construction.

## Assumptions

- assume the rule lands as prose in the existing numbered list (the origin's recommended shape), not as a bundled extraction script; basis: the origin's possibility space rejects the script with its own reason (machinery needing maintenance against plan-format drift) and rejects a total ban on hand-built simulations because ad-hoc behavioral probes stay legitimate (rule 27); only gate expectation derivation binds to prescribed bytes.
- assume no review-panel catalog change is needed; basis: the defect class is authoring-side and reviewers catch it through the plan's own rule text (the rule a plan's Validation preamble must record), the same path the executed SUT-naming rule 43 took beside its catalog addition - this origin prescribes no catalog arm.
- assume rule numbering continues at 44; basis: rule 43 (the executed SUT-naming rule) is the list's current tail, immediately before the `## Budget gate` heading, re-derived from the worktree at authoring time.
- assume the origin's `Class:` line (fix-class) holds: the body records the block that disappears (the recert round) and the arms remove the defect class at authoring time without adding a refusal path to any runtime or review flow; basis: the origin's Acceptance section, read per rule 42.

- assume the rule intentionally covers insertions only: rule 36's prescribed removals and rule 41's RED-polarity scratch runs are adjacent divergence vectors the origin does not scope (its Expected behavior names "inserted bytes"), recorded here as the boundary instead of widening beyond the origin; a future origin may govern them. Basis: the origin's Expected behavior section, read per rule 42.

Decision points requiring a grill: none remain.

### Task 1 - Rule 44: extraction duty in the Validation Commands authoring rules

- [x] In `agents/skills/plans/SKILL.md`, the Validation Commands authoring rules list: insert rule 44 between rule 43's paragraph and the `## Budget gate` heading (insertion anchor: the rule 43 paragraph tail and the heading literal `## Budget gate (plan-authoring pause and resume)`, both present on main at authoring time; re-derive exact bytes from the worktree before the edit). Rule text: `44. **Extract GREEN-simulation insertions from the plan's prescribed spans, never re-type them:** when a count or content expectation derives from a GREEN-polarity simulation (rule 36's temp-copy insertions, any hand-run insertion probe), the simulation's inserted bytes are extracted mechanically from the plan's own prescribed spans - programmatically copying each task's quoted insertion text from the plan file into the scratch tree - never re-typed from recall of the fold; a simulation whose inserted bytes are not byte-identical to a span the plan prescribes is void and every expectation derived from it is unpinnable, because a hand-rebuilt insertion diverges from the prescription silently and the gate then reads the divergence, not the plan (witnessed 2026-09-30: an authoring-time count gate pinned the simulated 6 where a faithful landing reads 5, one unprescribed summary sentence having crept into the hand-rebuilt scratch tree; five review workers re-derived the 5, costing a blocking round, a re-pin, and a re-simulation). A plan whose count or content pins derive from a simulation records the extraction beside it: the command or one-liner that copied the prescribed spans into the scratch tree, so the derivation chain (prescribed span, extracted insertion, simulated tree, expectation) is re-runnable at review time.` [class: IMPLEMENTATION_REQUIRED]

### Task 2 - Validation

- [x] Run every Validation Command below from the worktree root; each must pass against the amended tree. [class: REPOSITORY_TEST]
- [x] Run the rule 22 mechanical audit over this plan: extract each pinned span below and verify it occurs exactly once in the task text that prescribes it; run `bash -n` over the extracted Validation Commands block (span-joined extraction of the numbered command lines); fix both sides of any mismatch in the same edit. [class: REPOSITORY_TEST]

## Evaluation Criteria

- A count or content expectation whose derivation chain runs through a GREEN-polarity simulation stands on byte-identical prescribed spans, and a divergent simulation is void before it can pin a number.
- The derivation chain is recorded and re-runnable: a reviewer can re-extract the prescribed spans, re-run the simulation, and re-derive the pinned expectation without trusting the author's recall.
- No script, catalog, refusal path, or gate machinery ships: the only touched file is `agents/skills/plans/SKILL.md`, and the rule joins the numbered list as prose.

## Review Scope

Editable regions: `agents/skills/plans/SKILL.md` (the Validation Commands authoring rules list, the region between rule 43's paragraph and the `## Budget gate` heading).

Read-only: `agents/skills/review-agents/` (all catalogs); `agents/skills/review-plan/SKILL.md`; `agents/skills/plans/SKILL.md`'s Budget gate section; `scripts/`; every other file.

## Origins dispositions

The origin stays in place at the backlog top level while this plan is open; execution folds it per the Plan Lifecycle.

## Validation Commands

Run from the worktree root; every check fails closed (a miss or an error aborts non-zero). Baselines derived from main at authoring time 2026-10-01 (commit 5138a9fc); re-derive any drifted baseline at execution per the provenance rule before trusting a pass. Authoring-time record (rule 29): the em-dash `touched` scan over the plan bytes passed, the public-hygiene scan passed, and `plan_readiness.py --pre-round` passed (structural checks clean), and the shared-body runtime-neutrality gate (command 11's invocation) passed over the prescribed rule text. Rule 19 RED-today evidence, verified 2026-10-01 against the worktree's main bytes: commands 1, 2, 3, 4, 5, 7's pins are absent from the skill file (command 3's awk region matches nothing on main), command 6's number 44 has zero occurrences (grep rc 1), and command 12's extraction-mechanism pin is absent (grep rc 1); the insertion anchors (rule 43's paragraph opening and the `## Budget gate` heading) each occur exactly once. Rule 22 authoring-time mechanical audit: each pinned span occurs in Task 1's prescribing text exactly once (the rule-name literal, the void condition, the recording duty, the witness numbers, and the extraction-mechanism literal).

1. `grep -q "44. \*\*Extract GREEN-simulation insertions" agents/skills/plans/SKILL.md || { echo FAIL: rule missing; exit 1; }` - rule 44 exists (zero hits on main at authoring time).
2. `test "$(grep -oF "Extract GREEN-simulation insertions from the plan's prescribed spans" agents/skills/plans/SKILL.md | wc -l)" -eq 1 || { echo FAIL: rule duplicated; exit 1; }` - exactly-once at its site (occurrence form per rule 33).
3. `awk '/^43\. \*\*System-under-test naming/{f=1} f && /^## Budget gate/{f=0} f' agents/skills/plans/SKILL.md | grep -q "Extract GREEN-simulation insertions" || { echo FAIL: rule outside the list tail; exit 1; }` - the rule lands between rule 43 and the Budget gate heading, region-scoped.
4. `grep -q "byte-identical to a span the plan prescribes" agents/skills/plans/SKILL.md || { echo FAIL: void condition missing; exit 1; }` - the void/unpinnable clause is pinned in the rule text.
5. `grep -q "records the extraction beside it" agents/skills/plans/SKILL.md || { echo FAIL: recording duty missing; exit 1; }` - the acceptance's record-beside-the-simulation duty is pinned in the rule text.
6. `grep -qE '^44\. ' agents/skills/plans/SKILL.md || { echo FAIL: numbering broken; exit 1; }` and `test "$(grep -cE '^44\. ' agents/skills/plans/SKILL.md)" -eq 1 || { echo FAIL: number duplicated; exit 1; }` - the list's numbering stays contiguous with a single rule 44 (the authoring-rules list sits at column 0, so the anchored regex carries no portability variable per rule 26).
7. `grep -q "simulated 6" agents/skills/plans/SKILL.md && grep -q "reads 5" agents/skills/plans/SKILL.md || { echo FAIL: witness missing; exit 1; }` - the rule carries its witness numbers (the witnessed 6-vs-5 divergence).
8. `grep -n "Extract GREEN-simulation" agents/skills/review-agents/*.md; st=$?; test "$st" -eq 1 || { echo "FAIL: catalog touched (rc=$st)"; exit 1; }` - three-way split: no review-agents catalog carries the rule (the assumption's no-catalog-change shape stays true).
9. `bash scripts/check-no-em-dash.sh added-lines --base main agents/skills/plans/SKILL.md || { echo FAIL: em dash in added lines; exit 1; }` - the added-lines gate passes over the edited file against the committed baseline.
10. Run the public-hygiene scan from the user facts document's `public_hygiene_scan_script` key over the repository; exit 0 required.
11. `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_execute_plan_runtime.py -k shared_skill_bodies -q >/dev/null 2>&1 || { echo FAIL: shared-body neutrality; exit 1; }` - rule 37's mandated runtime-neutrality gate runs over the amended shared skill body (plans/SKILL.md is in the gate's shared_files tuple); invocation shape per the executed SUT-naming plan into the same list.
12. `grep -q "programmatically copying each task's quoted insertion text" agents/skills/plans/SKILL.md || { echo FAIL: extraction mechanism missing; exit 1; }` - the extraction-mechanism clause (the rule's only in-skill definition of "mechanically") is pinned, so its deletion breaks a command per the list's own rule 7/18 dedicated-grep standard.
