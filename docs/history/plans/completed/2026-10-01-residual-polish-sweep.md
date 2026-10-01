# Residual polish sweep (re-verify then fix)

Backlog origins (scope of record): `docs/history/backlog/2026-09-28-review-loop-exit-metrics-r1-nonblocking.md`, `docs/history/backlog/2026-09-28-execute-plan-vacated-step-numbers.md`, `docs/history/backlog/2026-09-28-invariants-referent-naming.md`, `docs/history/backlog/2026-09-28-lesson-147-stale-step-0-1a-citation.md`, `docs/history/backlog/2026-09-28-plan-g7-base-key-skip.md`, `docs/history/backlog/2026-09-28-plans-phase-0-restates-canonical-rationale.md`

Classification: [class: fix-class] recorded-review residuals, re-verify-then-fix; authoring only (this plan is not self-executing).

## Terminology and core concepts

- **Re-verify-then-fix**: every finding is adjudicated against current bytes before any edit; the entry's fixed/survivor expectations are 2026-09-29 facts, stale by four days of landings, and the Task 1 disposition log is the only authority for what Task 2 touches.
- **Disposition vocabulary**: `fixed-with-evidence` (the finding's demanded state exists on disk today; cite the file and line), `survivor` (still present; Task 2 fixes it with its named shape), `mooted-for-completed-history` (the demand lives in an executed plan's immutable bytes or a completed artifact; record the moot disposition in this sweep's surfaces, never edit the completed artifact).
- **Discriminating witness**: every code fix lands with a test or pin that fails without it; every prose fix lands with a grep pin in this plan's Validation block (added at execution time to the Validation Commands block below as part of the fix commit).

## Coverage dispositions (verified on disk 2026-10-01)

- The two cluster origins (phase3-r1, r3-overflow) are status-done: covered by the executed deferred-residual-dispositions plan (docs/history/plans/completed/2026-09-27-deferred-residual-dispositions.md), which owns their item-level disposition bookkeeping. The frozen p83 entry is the explicit revival decision for their FINDINGS as this sweep's scope of record (the coverage gate's supersede-or-explicit-revival arm): the earlier plan dispositioned the items without fixing the survivors this sweep verifies live (exit-metrics N2-N5 and the runtime-contract fragment are on disk today). The cluster files are cited here as scope provenance, deliberately NOT in the Backlog origins line, so the landing's covered-flip never touches their covered status; the six open origins carry the flip.
- Entry-time verified-fixed findings (phase3-r1 1, 6, 7; r3 themes 1, 3, 4) were re-spot-checked 2026-10-01: the usage long-form arm (line 17 of scripts/check-no-em-dash.sh) and the resume-same-claim contract pin still hold; the others re-verify in Task 1 like everything else.

## Tasks

### Task 1: per-finding disposition sweep

Files:
- none; verification-and-record task (dispositions recorded in the task log)

Evidence:
- the disposition log in the task log names all seventeen findings below (phase3-r1 1-8, r3 themes 1-4, exit-metrics N1-N5), each with one of the three dispositions and its file:line evidence

- [ ] Adjudicate every finding against current bytes, recording one line per finding in the task log: phase3-r1 findings 1-8 (1 typo'd-path fail-closed, 2 junk-state rejection witness, 3 parameterized blocked-persist tail, 4 shared task-heading predicate, 5 runtime-contract.md indentation, 6 usage long-form, 7 resume-same-claim contract pin, 8 bounded-read docstring fold-to-target); r3 themes 1-4 (1 payload-copy consume lifecycle, 2 appendix wording pair plus directive normalization, 3 attempt-bound named predicate, 4 loop-mode single statement); exit-metrics N1-N5 (1 grep -e pin in immutable plan bytes, 2 per-band float formatting, 3 legacy-counts report legend, 4 report-home definition plus parent mkdir, 5 strict-package wording placement); a finding the entry called fixed can be a survivor and vice versa - the log decides, never the entry [class: REPOSITORY_TEST]
- [ ] Commit: `chore: residual sweep disposition log (17 findings adjudicated)` (the log rides the plan's task log, not a repo file; the commit carries any no-op evidence notes) [class: IMPLEMENTATION_REQUIRED]

### Task 2: fix the survivors

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `scripts/summarize_review_stats.py`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/review-loop/SKILL.md`

Evidence:
- every Task 1 survivor fixed per its named shape below, each with its discriminating witness; findings Task 1 recorded fixed-with-evidence or mooted are untouched. A finding the entry called fixed that Task 1 adjudicates a survivor takes the origin's own candidate fix as its shape (each cluster origin states one), recorded in the log before the edit

- [ ] phase3-r1 2 (if surviving): add the junk-state rejection witness - a test that `validate_manifest` refuses an unknown claim state string with a named error, guarding the closed state set [class: REPOSITORY_TEST]
- [ ] phase3-r1 3 (if surviving): parameterize the shared blocked-persist tail of `_apply_blocked` and `_park_waiting_capacity_locked` (one helper carrying the task-persist block plus worker-blocked history append, claim state as the parameter) with the two call sites' behavior pinned unchanged by the existing suite [class: IMPLEMENTATION_REQUIRED]
- [ ] phase3-r1 4 (if surviving): collapse the duplicated at-least-one-task-heading predicate to one shared helper referenced by the terminal gate and the readiness plan-shape guard, preserving each site's evidence strings [class: IMPLEMENTATION_REQUIRED]
- [ ] phase3-r1 5 (if surviving): repair the structural wart at runtime-contract.md line 794 - the flush-left hard-wrap fragment beginning `The first` inside the r5-F3/r6-F1 prose block under Batch claim groups. The entry's original structure (a bullet list terminated mid-section) no longer exists: the region is plain prose, so the fix is a paragraph re-flow that joins the fragment to its sentence, never the entry's two-space list re-indent; the origin's candidate shape is the fallback the log derives from current bytes [class: IMPLEMENTATION_REQUIRED]
- [ ] r3 theme 2 (if surviving): reword the zcode.md mode-appendix content span to defer to the pinned literal and state the `<directive>` substitution normalization (trim, single line) beside it [class: IMPLEMENTATION_REQUIRED]
- [ ] exit-metrics N2 (if surviving): format the per-band ready-rate Markdown column through the same two-decimal helper as the overall table [class: IMPLEMENTATION_REQUIRED]
- [ ] exit-metrics N3 (if surviving): move the legacy-counts caveat from the docstring into the report legend text the generated Markdown carries [class: IMPLEMENTATION_REQUIRED]
- [ ] exit-metrics N4 (if surviving): define `<report-home>` in the maintenance skill's review-metrics rider (the resolved metrics report directory, named beside the rider's command) and give `_atomic_write_private` parent-directory creation so a fresh tmp does not fail the metrics write [class: IMPLEMENTATION_REQUIRED]
- [ ] exit-metrics N5 (if surviving): move or qualify the strict-package sentence so its mechanical force matches its surface (review-loop's advisory label vs review-plan's/execute-plan's mechanical rendering; the plans side already carries the personal-class qualification at the cap-closure item) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the full suite for every touched script plus the Validation block; every fix's witness fails when the fix is reverted (spot-check one revert) [class: REPOSITORY_TEST]
- [ ] Commit: `fix: residual sweep survivors (disposition-log driven)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: completed-history moot dispositions

Files:
- none; record-only task

Evidence:
- the disposition log carries the two moot records with their rationale

- [ ] Record the N1 moot: the `grep -qF --metrics-markdown` pin lives in the executed plan's immutable Validation bytes; the moot disposition cites the executed plan path and notes the `-e` form for any future author copying the shape [class: REPOSITORY_TEST]
- [ ] Adjudicate plan-g7-base-key-skip per its origin's own arm: completed-history moot (the owning plan executed and archived) unless a live consumer need proves a correction branch is warranted; record the adjudication and the rationale [class: REPOSITORY_TEST]

### Task 4: the amended residual docs items

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/maintenance/prompt-templates.md`
- `agents/skills/plans/SKILL.md`
- `projects/.ai-playbook/development_lessons.md`

The runtime-contract.md and prompt-templates.md entries are contingent: their diffs land only if the renumber arm wins (a Step 0.5 re-key site at runtime-contract.md line 1504; nine Phase 0 citation matches in prompt-templates.md). The lessons file is the lesson-147 correction target, resolved by the learn flow; its diff is unconditional.

Evidence:
- `bash scripts/check_maintenance_pins.sh` stays green; the learn-flow output records the lesson-147 correction

- [ ] Vacated Phase 0 numbering: renumber the execute-plan Phase 0 step headings gapless (0.1, 0.2, 0.3, ...) with the cross-skills citations and any keyed pins re-keyed in the same change, or add the one-line retirement note at the first gap - choose by counting the citation sites named in the origin (the fewer-sites arm wins); the Step 0.1 transfer-in obligation sentence points directly at the canonical Transfer-in implementation heading [class: IMPLEMENTATION_REQUIRED]
- [ ] Invariants referent: the Base-branch resolution rule's closing citation names the isolation bullets' owning file (`agents/skills/maintenance/SKILL.md`) so the referent resolves without a corpus search [class: IMPLEMENTATION_REQUIRED]
- [ ] Plans Phase 0 restatements: slim the plans skill's Step 0.1 rationale and Step 0.2 marker-keying restatements to reference-plus-literal form (point at the canonical section, keep only the payload-critical literal), never deleting a pinned span without re-keying its pin in the same change [class: IMPLEMENTATION_REQUIRED]
- [ ] Lesson 147: correct all three stale halves through the learn/lessons flows (never a hand edit of the lessons corpus), citing the plans consolidation as the driving incident: the See-also citation naming the deleted Step 0.1a, the stale rule-2 branch-match auto-continue arm (updated to the worktree-first reality or struck), and the citation's owning-file referent; the correction target is the corpus the learn flow resolves (lesson 147 lives in projects/.ai-playbook/development_lessons.md, not the project docs corpus), and that file's diff is the flow's output [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: residual sweep amended residuals (numbering, referents, restatements, lesson)` [class: IMPLEMENTATION_REQUIRED]

### Task 5: full-suite validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block; covers the disposition-driven fixes, the moot records, and the amended five

- [ ] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]

## Validation Commands

```bash
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base main
bash scripts/check_maintenance_pins.sh
PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime -q
python3 scripts/summarize_review_stats.py --help >/dev/null
grep -c "^The first$" agents/skills/execute-plan/runtime-contract.md
grep -c "report-home" agents/skills/maintenance/SKILL.md
# Task 2 witness lines (added at execution time, the Task 2 rule).
grep -c "^The first member is reached through" agents/skills/execute-plan/runtime-contract.md
grep -cF "Mechanical (not part of the advisory above" agents/skills/review-loop/SKILL.md
grep -c "the resolved metrics report directory" agents/skills/maintenance/SKILL.md
python3 scripts/summarize_review_stats.py --selftest --subset metrics
python3 scripts/summarize_review_stats.py --selftest --subset permissions
```

Floor-line conventions: the `^The first` count line is the phase3-r1 5 discriminator - it prints exactly 1 today (line 794 is a line consisting of exactly `The first`; the anchored dollar anchor excludes the legitimate line-564 wrapped sentence) and must print 0 after the re-flow, so it passes by printing 0 like the house print-0 convention (grep -c exits 1 at a zero count; the printed count is the assertion). The report-home count line is a presence floor (prints at least 1 today; the N4 fix adds the definition beside the rider, so the count never drops to zero). The block is extended at execution time with each survivor fix's discriminating witness (the Task 2 rule) and re-keyed whenever a fix changes a floor line's match count; the lines above are the standing floor.

## Assumptions

- The Task 1 disposition log is the sole driver of Task 2's edit set; the frozen entry's fixed/survivor expectations are advisory inputs re-verified like every other finding, and this plan never edits a finding Task 1 recorded as fixed-with-evidence or mooted.
- The bounded-read docstring item (phase3-r1 8) adjudicates by direct verification: its named fold target (2026-09-20-bounded-read-pin-hardening) sits in rejected/ and absorbed nothing, so no moot branch exists; the docstring's numbering note reads accurate today and the refusal-fragment suffix is test-pinned, so the expected disposition is fixed-with-evidence.
- Every fix keeps behavior identical except the named finding; no refactors beyond the named shapes; the pins suite's exactly-once spans are re-keyed in the same edit when a reworded span is pin-keyed.
- The lessons correction runs through the learn skill's flow so the corpus's own bookkeeping (numbering, cross-links) stays consistent; a direct hand edit is out of scope even though the lessons file is listed.

Decision points requiring a grill: Task 1 disposition authority (the task log over the entry's expectations); Task 2 survivor shapes (parameterization and shared-predicate forms exactly as named, no wider refactor, with the origin's candidate fix as the shape for entry-fixed findings that turn out to be survivors); Task 3 g7 adjudication (completed-history moot unless a live consumer need is demonstrated); Task 4 numbering arm (retirement note wins when its single line beats the renumber's citation-site count measured by the origin's grep, pins and citations re-keyed in the same change); Task 4 lesson shape (three named halves through the learn flow, never a hand edit); Task 2 phase3-r1 5 shape (paragraph re-flow of the flush-left fragment, never the entry's stale list re-indent).

## Review Scope

- `docs/history/plans/2026-10-01-residual-polish-sweep.md`
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `scripts/summarize_review_stats.py`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-loop/SKILL.md`
- `projects/.ai-playbook/development_lessons.md`
- `docs/history/backlog/completed/2026-09-20-phase3-r1-polish-residuals.md`
- `docs/history/backlog/completed/2026-09-21-r3-review-overflow-residuals.md`
- `docs/history/backlog/2026-09-28-review-loop-exit-metrics-r1-nonblocking.md`
- `docs/history/backlog/2026-09-28-execute-plan-vacated-step-numbers.md`
- `docs/history/backlog/2026-09-28-invariants-referent-naming.md`
- `docs/history/backlog/2026-09-28-lesson-147-stale-step-0-1a-citation.md`
- `docs/history/backlog/2026-09-28-plan-g7-base-key-skip.md`
- `docs/history/backlog/2026-09-28-plans-phase-0-restates-canonical-rationale.md`
