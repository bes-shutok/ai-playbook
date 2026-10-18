# Plan: the plan template's Standing constraints section and the worker read surface

Backlog origin: docs/history/backlog/2026-10-05-plan-worker-read-contract.md
Driving force: code-quality
Plan review record: the staging series docs/reviews/2026-10-05-plan-review-plan-worker-read-contract-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- Standing constraints: the plan template's new optional `## Standing constraints` section, stated once per plan: the repo-wide rules, conventions, and invariants every task must respect, referenced by every task instead of restated per task.
- Read surface: what a task's prompt declares as its context: the plan's Terms, the task's own body, and the Standing constraints section when present; the unit's contract shape ("each task declares its context surface as Terms plus the task plus Standing constraints").
- Unit identifiers: the frozen rolling-log entry `execution-pipeline-friction` (docs/history/backlog/PLAN-PROMPTS.md) numbers this plan's sibling units; the standing D-4 authoring directive (docs/maintenance/operator-directives.md) orders continuous authoring.
- Span extractor: scripts/plan_task_span.py, the landed interim single-file extractor (explicitly disposable, superseded by the plan-directory shape) that emits byte-verified Terms and task spans; this plan extends its grammar with the constraints span.
- Constraints span: the extractor's new header line for the section from the line `## Standing constraints` through the line before the next `## ` heading, shaped exactly like the existing terms span (start and end byte offsets plus a sha256 digest over the span bytes; no raw bytes in either mode, the full-mode marker and payload layout untouched); emitted when the section exists, omitted when it does not; the consumer reads the slice's bytes at the cited offsets from the plan file, exactly as Terms consumers already do.
- Declared-not-wired surface: the citation wiring that hands workers the three-slice read surface is deliberately not part of this plan: no consumer cites the extractor's spans today (the extractor arms the interim grammar and the plan-directory shape that supersedes it, with ad-hoc orchestrator use), and the dispatch-side citation lands with the directory-shape unit that owns the worker-read machinery.
- Template arm: the changes to agents/skills/plans/SKILL.md's template block and rules (the new section in the template, the per-task reference line, the read-surface sentence in the rules), all additive and optional-declared: an existing plan without the section remains valid, curation stays an optimization never a restriction, and quoted landing text is never deduplicated.

## Why

Every worker today re-derives the run's standing rules from whatever slice its prompt cites, and plans restate the same constraints per task or lose them between tasks: the witnessed runs spent worker context re-reading plan-level rules the task never needed to repeat. One section stated once and referenced per task gives the author one place to declare the constraints and the worker one declared read surface, on the extractor's existing verified-span machinery.

## Outcome

Plans declare a Standing constraints section when they have plan-wide rules; every task's declared read surface is Terms plus the task plus that section; and the span extractor emits the constraints span alongside the terms and task spans, so a worker's declared surface is three whole verified slices read from the plan at cited offsets.

- The plans template block gains the `## Standing constraints` section (optional, declared-when-needed, placed after `## Assumptions` and before `## Gist & Examples`), and the rules gain the read-surface sentence: each task's context surface is Terms plus the task plus Standing constraints, stated once and referenced, never restated per task; curation stays an optimization never a restriction, a worker that finds its slice insufficient reads the whole plan and reports it, the done and review gates keep reading everything, and quoted landing text is never deduplicated.
- scripts/plan_task_span.py emits a `constraints-span` header line (start and end offsets plus the span digest, shaped like the existing terms span, no raw bytes, the full-mode layout untouched) when the section exists and omits the line when it does not; the outcome contract is unchanged.
- The extractor's docstring names the three-slice read surface; fixtures pin the present, absent, first-match, and termination shapes.

Gate delta: one new optional template section, one rules sentence, one new span header in an existing extractor, and its fixtures. No readiness gate change, no state field, no runtime driver change, no dispatch wiring (declared-not-wired, see Terms).

## Assumptions

- assume the section is optional-declared and never gated: an existing plan without it stays valid, and no plan_readiness check requires it; basis: the unit's own wording ("curation stays an optimization, never a restriction") and the migrate-on-touch convention for template shape changes.
- assume the extractor extension is the interim grammar's (the plan-directory shape supersedes it by design), so the constraints span rides the same disposable vocabulary instead of new machinery; basis: the extractor's own docstring and the unit text ("the interim span extractor ... needs no authoring work" refers to its existence, while the read surface its grammar hands workers must learn the new section).
- assume the citation wiring is deliberately deferred: no consumer cites the extractor's spans today, so this plan delivers the grammar and the template declaration while the dispatch-side citation lands with the directory-shape unit that owns the worker-read machinery; basis: the repo-wide reference scan (the extractor's only references are its own selftest and the backlog and plans prose) and the frozen entry's unit seams.
- assume the section's placement after `## Assumptions` and before `## Gist & Examples`; basis: the template's section order (Terms, Why, Outcome, Assumptions, Gist & Examples, Evaluation Criteria, Review Scope, Validation Commands, Tasks) places plan-wide reference material beside the assumption record and before the reader-facing summary sections, and no existing span shifts for a plan with the section (the terms span ends at `## Why`, the task spans start at `### Task N:`).
- assume the adjacency holds unchanged: the other frozen-entry units own different files (the early-lens template beside the subagent-prompts lenses is a later unit; sizing and directory shape follow), so anchors re-derive from live bytes at execution and a moved anchor re-keys its pin in the same edit; basis: the frozen entry's seam rule.
- assume authoring runs under the standing D-4 authoring directive plus the live operator order to continue authoring without stops, so the plans skill's Phase 1 confirmation is satisfied by the frozen entry's validated record; basis: the maintenance loop's authoring blueprint under the standing operator directive.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: plans gain one optional Standing constraints section and workers read exactly three verified slices (Terms, the task, the constraints), a code-quality contract that stops per-task constraint restatement and worker context waste.

Before (today): a task's worker sees Terms plus the task span; plan-wide rules live wherever the author remembered to put them, restated in some tasks and missing in others.

After (this plan): the author declares `## Standing constraints` once; the declared read surface is the three slices; a plan without the section behaves byte-identically to today; the dispatch-side citation of the three slices lands with the directory-shape unit.

Edge cases pinned: a plan with no Standing constraints section emits no constraints-span line (byte-compatible with today); a duplicated section at `## ` level resolves to the first match's span; the section's span runs to the next `## ` heading exactly as the Terms span does; the extractor's outcome contract and its declared stderr placement deviation are unchanged; the full-mode marker and single-payload layout are untouched.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the constraints span's offsets and digest follow the extractor's existing byte-span rules; the present, absent, first-match, and termination shapes behave as pinned.
- additive placement: the template arm is optional-declared and ungated; existing plans stay valid; no existing extractor consumer breaks; the full-mode layout is untouched.
- observability: the header line names the constraints span's offsets and digest exactly as the terms line does.
- maintainability: one template section, one rules sentence, one span header with fixtures; no new tool, no driver change, no dispatch wiring.

**Done when:**
- all task boxes checked; the extractor suite passes under the venv pytest runner (`"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_plan_task_span.py -q` exits 0, bare `python3` off-venv fails rc 1 with a pytest import error, fail-closed); the pins suite exits 0 (OUTCOME: pass); the em-dash added-lines scan and the public hygiene scan exit 0; `python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-plan-worker-read-contract.md` exits 0 on the final bytes.

**Ship when:**
- the extractor emits the three-slice header grammar for a plan declaring `## Standing constraints`, the template declares the read surface, and a plan without the section behaves byte-identically to today.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/plan_task_span.py` (the constraints span and its docstring sentence only)
- `agents/skills/plans/SKILL.md` (the template block's new section, the per-task reference line, and the rules' read-surface sentence only)

**Tests:**
- `scripts/test_plan_task_span.py` (new constraints-span test items)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring implied by an explicit must-fix change, or contradicts a contract the plan changed.

**Out of scope; reject unless plan-related:**
- the runtime driver and the subagent prompt templates: the citation wiring is the declared-not-wired surface, landing with the directory-shape unit.
- the other execution-pipeline-friction units (early lens, done batching, continuity probe, sizing, directory shape): separate plans under the frozen entry's seam rule.
- plan_readiness.py: no gate requires the new section.
- the state schema and every other production script: no field grows, no tool changes beyond the named files.

## Validation Commands

```bash
# Extractor suite (new constraints-span items; the venv runner is the
# canonical invocation; bare python3 off-venv fails rc 1 with a pytest
# import error, fail-closed)
"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_plan_task_span.py -q
# Pins: verify no pin keys a span this edit touches; a moved anchor
# re-keys its pin in the same edit
bash scripts/check_maintenance_pins.sh
# Added-lines em-dash scan over the changed set (added-lines, never
# argless; it witnesses committed bytes, so the GREEN checkpoints run it
# after the task's commit)
bash scripts/check-no-em-dash.sh added-lines --base main
# Public hygiene scan (fail-closed; outcome contract)
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
# Readiness (fail-closed; outcome contract); RED at authoring until the
# staging review series lands under docs/reviews, green from r1 on
python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-plan-worker-read-contract.md
```

### Task 1: The constraints span in the extractor and its suite (TDD)

Files:
- `scripts/plan_task_span.py`
- `scripts/test_plan_task_span.py`

Evidence:
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_plan_task_span.py -q`; covers every criterion below at the task boundary (bare `python3` off-venv fails rc 1 with a pytest import error)
- `grep -c "constraints-span" scripts/plan_task_span.py`; covers the span presence (RED at authoring: zero hits)
- `grep -c "Standing constraints" scripts/plan_task_span.py`; covers the section-key presence (RED at authoring: zero hits)

- [x] Re-derive the anchors from live bytes: the extractor's span rules and stdout grammar (the terms and task span definitions, the byte-offset and digest shapes, the full-mode marker and single-payload layout, the outcome contract and its stderr placement deviation), the plans template block's section order, and the pins suite's plans-skill surfaces (verify no pin keys a span this edit touches); if any anchor moved from the bytes this plan quotes, update the owning pin in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] Pin the fixtures in scripts/test_plan_task_span.py as a second module-level fixture list with local span recomputation (the suite's existing helpers are hard-bound to its module globals; the subprocess invocation helper reuses cleanly), given/expects form: `test_constraints_span_present`; given a plan with the section, expects a `constraints-span` header line with correct offsets and digest shaped like the terms line and no raw bytes in either mode; `test_constraints_span_absent_byte_compatible`; given a plan without the section, expects no constraints-span line and output byte-identical to the pre-plan grammar; `test_constraints_span_first_match_wins`; given a plan with two `## `-level `## Standing constraints` sections, expects the first one's span; `test_constraints_span_runs_to_next_heading`; given a section followed by `## Gist & Examples`, expects the span to end before that heading [class: REPOSITORY_TEST]
- [x] Run → RED confirmed under the venv runner (the constraints span does not exist; the new tests fail on the missing header line) [class: REPOSITORY_TEST]
- [x] Implement the constraints span in scripts/plan_task_span.py: a header line `constraints-span: start=<int> end=<int> sha256=<hex>` for the section from the line `## Standing constraints` through the line before the next `## ` heading (the Terms span's rule, first match wins), emitted in the header block between the terms and task lines, shaped exactly like the terms span (offsets and digest only, no raw bytes in either mode, the full-mode marker and payload layout untouched), present only when the section exists (absent tolerated, the outcome contract and the stderr placement deviation unchanged), and the docstring names the three-slice read surface (Terms plus task plus Standing constraints) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → GREEN: full suite OK [class: REPOSITORY_TEST]
- [x] Commit: `feat: plan task span extractor emits the standing-constraints span` [class: IMPLEMENTATION_REQUIRED]

### Task 2: The template arm and the read-surface rules sentence

Files:
- `agents/skills/plans/SKILL.md`

Evidence:
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_execute_plan_runtime.py -q -k shared_skill_bodies`; covers the shared-body gate criterion (the plans skill is a gate-covered shared-body file)
- `bash scripts/check_maintenance_pins.sh`; covers the pins criterion (verify no pin keys a span this edit touches; a moved anchor re-keys its pin in the same edit)
- `grep -c "Standing constraints" agents/skills/plans/SKILL.md`; covers the template arm presence (RED at authoring: zero hits)

- [x] Add the `## Standing constraints` section to the template block after `## Assumptions` and before `## Gist & Examples`, with a one-line body comment naming its declared-when-needed optionality, and add the per-task reference line to the task template immediately after the `### Task N:` heading and before the `Files:` list (the slot that respects the Evidence-after-Files rule and the runtime Files parser's exact opener grammar): the line names the task's context surface as Terms plus the task plus Standing constraints, referenced, never restated [class: IMPLEMENTATION_REQUIRED]
- [x] Add the read-surface sentence to the template's rules: the section is optional-declared and ungated, stated once and referenced per task; curation stays an optimization never a restriction, a worker that finds its slice insufficient reads the whole plan and reports it, the done and review gates keep reading everything, and quoted landing text is never deduplicated; verify no pin keys a span this edit touches and re-key any moved pin in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] Run the shared-body gate and the standing gates: the shared-body runtime test OK, the extractor suite OK, the pins suite exits 0 with OUTCOME: pass, the public hygiene scan exits 0, and `python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-plan-worker-read-contract.md` exits 0 on the final bytes; the em-dash added-lines scan runs after the task's commit so it witnesses the committed bytes [class: REPOSITORY_TEST]
- [x] Commit: `feat: plans template gains the standing-constraints section and the three-slice read surface` [class: IMPLEMENTATION_REQUIRED]

## Disposition

Executed 2026-10-06 in worktree ai-playbook-wt-pwr (branch plan-plan-worker-read-contract-exec) by the standing maintenance execution lane. Task 1 (065c9d48): scripts/plan_task_span.py emits the constraints-span header line shaped exactly like the terms span (offsets and digest only, first match wins, absent tolerated, full-mode marker and payload untouched), with the docstring naming the three-slice read surface; the four named fixtures land with genuine local recomputation; byte-identical output on section-less plans was verified empirically during review against four plans including the tool_error path. Task 2 (1ea04458): the plans template gains the optional Standing constraints section after Assumptions, the per-task context-surface reference line in the slot before Files (verified inert to the live Files parser), and the read-surface rules sentence carrying all five clauses.

Validation: extractor suite 13 passed under the venv runner; pins suite exit 0; hygiene scan exit 0; plan_readiness exit 0; em-dash added-lines scan exit 0 post-rebase (the pre-rebase exit 1 was a base-drift artifact, r4 F1). The shared-body runtime gate is green again on the landed tip (the pre-existing forbidden-term regression was repaired and its row covered by a peer lane while this plan ran). Exec review r4 (fresh-adversarial, one worker) found zero blocking findings with one Low accepted (the base-drift em-dash artifact) and two informational notes; records at docs/reviews/2026-10-05-plan-review-plan-worker-read-contract-r4.{md,stats.json} plus the r5 certification probe.

Deferred residuals: the r4 Low above. Origin row docs/history/backlog/2026-10-05-plan-worker-read-contract.md is covered by this execution and folded in the landing.
