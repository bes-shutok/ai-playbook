# Plan: Maintenance skill size refactor (changelog extraction, byte-budget gate, module split)

Backlog origin: docs/history/backlog/2026-10-10-maintenance-skill-size-refactor.md (the PLAN-PROMPTS entry `maintenance-skill-size-refactor` carries the operator-ordered prompt; the operator's 2026-10-10 go covers authoring dispatch)
Driving force: token-usage
Design input: docs/maintenance/maintenance-skill-refactor-analysis-2026-10-09.md (the measured analysis; its Part 4 table is the split architecture, its Part 5 item 2 the admission protocol this plan obeys)
Plan review record: the staging series docs/history/reviews/2026-10-10-plan-review-maintenance-skill-size-refactor-r*.md (created by this plan's review loop, r1 onward; the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 3h total, largest task 1h
Authoring claim: docs/tmp/authoring-claims/2026-10-10-maintenance-skill-size-refactor.md (session sess_5c51c846-299a-4dfe-a00c-4238d7883663)

## Terms

- Change ledger: history text living inside an operative skill file: the `## Revisions` section of `agents/skills/maintenance/SKILL.md` (75,756 bytes at lines 371-426, re-derived 2026-10-10) and the deviation-list preamble of `agents/skills/maintenance/prompt-templates.md` (78,059 bytes at lines 3-75, the deviation-intro paragraph through the last deviation entry, re-derived 2026-10-10; the file's first two lines are the title the split keeps). Verbatim moves only; no entry is rewritten, dropped, or summarized.
- Router: the post-split `SKILL.md` entry file that keeps frontmatter, configuration, loop-mode summaries, the Step 0-7 skeleton as one-paragraph dispatch entries with module pointers, invariants, and integration points, and names the module each step must load.
- Module: a file beside the router holding one concern's operative text with every section heading verbatim (`survey-arms.md`, `guards.md`, `decisions.md`, `quota-policy.md`, `scheduling.md`, `failure-cap.md`, `state-file.md`).
- Byte-budget gate: `scripts/skill_text_budget.py`, an outcome-contract checker over every `agents/skills/` skill file; per-file caps enforced advisory at landing (warning-only), per-section caps advisory as the pilot, a `--ratchet` mode that only lowers caps, and the admission test, promotion criteria, and sunset stated in the script header.
- Ratchet: the caps-table update mode that lowers a file's cap when a landing shrinks the file below it, and never raises any cap.
- Vendored twin: `~/.agents/skills` is a symlink to this repository's PRIMARY checkout's `agents/skills` directory (re-derived 2026-10-10), so skill-file edits reach the runtime registry when this plan's branch lands in that checkout: the merge-locked landing is the deploy, and until it lands the live loop keeps loading the pre-split files (old behavior, no breakage). The only out-of-band deploy in this plan is the new script: its filename joins `scripts/runtime-scripts.list` and its copy lands at the runtime scripts home in the same run; that deployed copy is machine-local, survives a git revert, and its rollback is the hand-removal named in Standing constraints.

## Why

The maintenance corpus is 626,902 bytes (~157K tokens) across three files; `SKILL.md` alone is 357,411 bytes and grew 18KB to 357KB in 24 days with exactly one 64-byte shrink across 35 commits. Every scheduler turn and child dispatch loads this doctrine before working. About 24% of the corpus is change ledger, not rules, and no surface anywhere measures size, so the loop that causes the growth cannot see it. The operator ordered the analysis's most effective suggestion executed first (the extraction, ~154KB out at near-zero semantic risk), then the standing counter-pressure (the budget gate), then the split that makes the entry file loadable again. Full measurements: docs/maintenance/maintenance-skill-refactor-analysis-2026-10-09.md.

## Gist & Examples

TLDR: move both change ledgers out to changelog files, land a fleet-wide warning-only byte-budget gate with a ratchet, split `SKILL.md` into a router plus per-concern modules with headings verbatim, and split `prompt-templates.md` into per-kind blueprints plus a shared duties-core file.

Before: a scheduler turn loads a 357KB `SKILL.md` whose tail 21% is the Revisions ledger; a landed plan appends to that ledger and the file ratchets forever; no consumer notices.

After: the same turn loads a router in the 25-40KB class plus only the modules its steps name; landed plan receipts append to `CHANGELOG.md`, which no operative turn loads; a pins-suite step reports any file over its cap as an advisory line, the ratchet lowers caps on shrink, and the machinery registry carries the gate's removals row, sunset, and promotion criteria.

Edge cases: the region-scoped pins checks that split `SKILL.md` on `## Revisions` (the python `s.split("## Revisions", 1)[0]` operative-region cut and the awk `/^## Revisions/{exit}` scan) lose their anchor when the heading moves; each is re-aimed in the same change to the post-extraction shape with its comment telling the truth; whole-file grep checks whose pass relied on the ledger's in-file copy are re-aimed at the changelog files beside their provenance; deviation-paraphrase must-not-carry surfaces are re-aimed at `templates-CHANGELOG.md` so the paraphrase protection survives the move; the count-gated checks that read exactly two occurrences across blueprint-plus-deviation (the pins script names this shape) are re-derived against the post-move tree.

## Outcome

The operative maintenance corpus drops from 626,902 bytes to roughly 160KB, no operative turn loads change history, growth is measured on every pins-suite run, and the entry file is loadable again.

- Both ledgers live in `agents/skills/maintenance/CHANGELOG.md` and `agents/skills/maintenance/templates-CHANGELOG.md`, byte-verbatim; every cross-reference resolves; the pins suite is green before and after each move.
- The budget gate reports per-file breaches over every `agents/skills/` skill file as advisory lines on every pins-suite run, carries per-section advisory caps for the maintenance corpus as the pilot, never loosens a cap, and states its admission test (the 35-commit one-shrink ratchet and the ~89K-token per-turn doctrine load), its promotion criteria (blocking exit 1 only after its first true catch), and its sunset (two-phase per Task 2: no removal path until the growth-telemetry consumer lands, then the six-window breach-and-fleet-total arm the pre-registered removals row names) in the script header beside that pre-registered machinery-registry removals row.
- `SKILL.md` reads as a router; every section heading lives verbatim in exactly one file; the directives-home citations, the D-series records, and the peer skills' anchor navigation keep resolving; machinery registry rows name the post-split files.
- `prompt-templates.md` becomes per-kind blueprint files plus `duties-core.md` for the byte-identical duty sets the pins suite already holds identical.

Gate delta: packaging only, no rule semantics change, no refusal class or hard gate added or removed, no new schema state field; the budget gate lands warning-only per the admission protocol (docs/maintenance/machinery-blocker-audit-2026-10-09.md Part 5 item 2) with its admission test, promotion criteria, sunset, and pre-registered removals row; new files are new homes for existing text (the ledgers), registered new machinery (the gate, warning-only with its admission fields and removals row), or read-only additions to the existing enforcement fabric (the router-integrity pin row and the gate's fixture suite); the machinery registry rows land in the same landings as the files they name.

## Assumptions

- The extraction is a pure move: the Revisions region (from the `## Revisions` heading through end of file) and the deviation preamble (from the deviation-intro paragraph through the last deviation entry, ending before `## Authoring child`) move byte-verbatim; `SKILL.md` keeps a title-level file but its tail becomes a two-line change-log pointer, and `prompt-templates.md` keeps its title plus a one-paragraph source-of-record pointer naming the changelog file. Basis: the analysis Part 4 execution order ("pure moves, no semantics"), the origin row's ship-when, and the re-derived byte counts in Terms.
- The in-corpus citation set is small and enumerable, and the plan verifies rather than assumes it: `SKILL.md` carries exactly two `Revisions` mentions at HEAD (the heading itself and the Step 5 five-minute-floor citation at line 193 naming "the Revisions ledger's 2026-09-15 floor-revision entry"); `prompt-templates.md` carries the line-3 deviation pointer; the corpus-wide grep task re-points any further reference that names the old locations. Basis: re-derived 2026-10-10 by grep at HEAD (the origin row's "18 mentions" figure is superseded by this re-derivation and is not reproduced in any task).
- Skill-file edits reach the runtime registry at landing, not at branch commit: the twin symlink resolves to the primary checkout's `agents/skills`, so each task's branch commit goes live only when the plan's squash lands there; the executor plans no separate skill deploy and claims no same-commit runtime visibility, and between landings the live loop runs the pre-split files (no breakage). The budget script is the exception: its deployed copy at the runtime scripts home is a same-run, machine-local deploy whose rollback is a hand-removal. Basis: the symlink read (re-derived 2026-10-10) and the repository's runtime deploy mechanism.
- The budget gate lands warning-only and stays warning-only within this plan: the pins-suite wiring invokes the checker in advisory mode whose findings never move the suite's exit code; the blocking promotion (exit 1) is a later, evidence-gated change per the admission protocol, and this plan lands only the promotion criteria text and the removals row. Basis: the origin row's fix shape, the machinery admission protocol Part 5 item 2, and directive D-12's admission subordination.
- Per-file caps seed at each file's current byte size plus a fixed headroom margin (25% or 8KB, whichever is larger, stated in the caps table header); for the three maintenance files the seeding happens after Task 1's extraction (caps seeded at post-extraction sizes), so the gate never reports the extraction's own removal as a breach and bites at growth, not at day one (this seeding rule deliberately restates the analysis Part 5 item 1's "current minus the changelog extraction" shorthand as the equivalent executable form: post-extraction-plus-margin is bite-at-growth by construction). Per-section caps for the maintenance corpus come from the analysis Part 4 table and stay advisory (the pilot diagnostic); only the per-file gate is the promoted-on-catch surface. Basis: the analysis Part 5 item 1 ("caps are set generously at first... so the gate bites at growth") and the entry's warning-only posture.
- The split keeps every `### `/`## ` heading byte-verbatim and moves each heading's section body whole; text that spans two concerns stays in the module of its primary heading, and the router's dispatch entry may summarize in one line plus pointer but never restate a rule. The `zcode.md` overlay stays one file (budgeted, not split). Basis: the analysis Part 4 architecture table and the origin row's heading-verbatim requirement.
- The blueprint split extracts only the byte-identical shared duty sets the pins suite already holds identical into `duties-core.md`; the blueprints name those spans by reference and stay self-contained for everything else, because a dispatched child must be able to load its blueprint without resolving repository-relative references beyond the named core file. Restatement folding beyond that (the analysis Part 2 items 1, 3, 4) is out of scope. Basis: the origin row's Task 4 wording and the analysis's "not deletion of payload self-containment" reading.
- Residual accepted: pins re-pointing is mechanical but wide (the suite carries 515 pins over these files), so each task's landing runs the suite green-before-green-after and re-keys only the pins whose anchors the task moved; a pin whose anchor survives unchanged is never touched. If a task cannot reach green within its own landing, it takes the deferred-landing path and reports, never a weakened check. Basis: the pins suite's green-before-green-after discipline and the origin row's constraint block.

Decision points requiring a grill: none remain (the operator ordered the program and its order on 2026-10-10; the entry records the operator go for each of the four tasks; the open questions this plan could have grilled (cap margin size, module granularity, duties-core boundary) are all named in the analysis and carried as stated assumptions above).

## Standing constraints

- Packaging only: no rule's semantics change; no operative sentence is rewritten except the citation re-points this plan names; the ledgers move byte-verbatim.
- Every intermediate landing keeps the pins suite, the public hygiene scan, the parallel-work regressions suite (`python3 scripts/test_plan_review_boundary_examples.py`), the authoring-plans liveness test (`python3 scripts/test_authoring_plans_liveness.py`), and, from Task 2's landing onward, the budget-gate fixture suite (`python3 scripts/test_skill_text_budget.py`) green; a red suite at a task boundary stops the task for reconciliation, never a weakened check.
- Landings of the pins-script edits serialize under the merge landing lock against the plans/execute-plan extraction plan (the `skill-monolith-module-extraction` entry), which re-aims the same script; the maintenance corpus stays the split pilot while the budget gate is fleet-wide from its first landing.
- Restatement folding and the growth-telemetry rider wiring are out of scope (the doc-hygiene row owns the standing review arm; folding follows in a later cycle once this packaging lands).
- No machine-specific absolute paths in any edited file; the hygiene scan passes before each commit; nothing is pushed to origin.
- Rollback arm: revert the offending task's commit (the ledgers and splits are byte-verbatim moves, so a revert restores the prior tree exactly); hand-remove the deployed budget-script copy from the runtime scripts home (machine-local, survives a revert); re-reconcile the machinery registry rows if reverting after Task 3's registry rename. The router stays sufficient as the dispatch root for a dispatched child: it carries the Step 0-7 skeleton and invariants inline, and each step's dispatch entry names the module whose text the child loads before executing the step (the router never restates a rule, so a step's operative text lives in its module).
- Execution runs on a branch kept rebased onto current main at each fold. At each task start the executor re-verifies currency (pins suite exit 0 and no commit in `git log HEAD..main` touching this plan's anchor files or the pins script) and stops and reports on a red baseline, a vanished anchor, or a stale rebase; hand-reconciling PLAN-PROMPTS.md is never the repair.

## Evaluation Criteria

**Quality dimensions:**
- correctness: both ledgers are byte-verbatim in their changelog files (`cmp` against the pre-move extraction), every cross-reference resolves, and the router's dispatch table names a real module for every step.
- regression safety: the pins suite passes before and after every landing; the parallel-work regressions suite and the em-dash scan pass over the touched paths; the machinery inventory check reports the new script as registered, not regrown.
- scope discipline: the changes touch only the maintenance skill directory, the pins script, the budget script plus its caps table, the machinery registry, `scripts/runtime-scripts.list`, and the rider-doc lines this plan names; no validator bytes change (`scripts/plan_readiness.py`, `scripts/validate_review_staging.py` untouched).

**Done when:**
- Every span check in `## Validation Commands` holds on the executed tree.
- `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )` exits 0.

**Ship when:**
- The next scheduler turn loads a router plus named modules instead of a 357KB monolith, landed receipts append to the changelog files, and the pins suite prints the budget report on every run; they follow from the executed tree.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/SKILL.md` (Task 1 tail extraction + citation re-point; Task 3 router conversion)
- `agents/skills/maintenance/CHANGELOG.md`, `agents/skills/maintenance/templates-CHANGELOG.md` (Task 1, created)
- `agents/skills/maintenance/prompt-templates.md` (Task 1 preamble extraction; Task 4 split)
- `agents/skills/maintenance/survey-arms.md` (Task 3, created)
- `agents/skills/maintenance/guards.md` (Task 3, created)
- `agents/skills/maintenance/decisions.md` (Task 3, created)
- `agents/skills/maintenance/quota-policy.md` (Task 3, created)
- `agents/skills/maintenance/scheduling.md` (Task 3, created)
- `agents/skills/maintenance/failure-cap.md` (Task 3, created)
- `agents/skills/maintenance/state-file.md` (Task 3, created)
- `agents/skills/maintenance/template-authoring.md` (Task 4, created)
- `agents/skills/maintenance/template-execution.md` (Task 4, created)
- `agents/skills/maintenance/template-unblock.md` (Task 4, created)
- `agents/skills/maintenance/duties-core.md` (Task 4, created)
- `scripts/skill_text_budget.py` (Task 2, created) and its caps table `scripts/skill_text_budget_caps.json`
- `scripts/machinery_inventory.py` (Task 3: the state-field read re-pointed to `state-file.md`; its check logic otherwise untouched)

**Tests:**
- `scripts/check_maintenance_pins.sh` (the mechanical fixture for every prescribed span and the budget-gate wiring)
- `scripts/test_skill_text_budget.py` (Task 2, created: the gate's hermetic fixture suite)
- `scripts/test_authoring_plans_liveness.py` (Tasks 3-4: span assertions re-keyed to the post-split files)

**Docs:**
- `scripts/machinery_registry.json` (Task 2: the gate's registration, admission fields, sunset, and pre-registered removals row; Tasks 3-4: rows re-named to the post-split files)
- `scripts/runtime-scripts.list` (Task 2: the budget script's deploy entry)
- `docs/history/backlog/2026-10-10-maintenance-skill-size-refactor.md` (read-only this plan; flipped covered by the landing rider, not by a task)

**Read-only (referenced, never edited):**
- `docs/maintenance/maintenance-skill-refactor-analysis-2026-10-09.md` (the design input; its Part 4 table and Part 5 item 2)
- `docs/maintenance/machinery-blocker-audit-2026-10-09.md` (the admission protocol)
- `docs/maintenance/operator-directives.md` (D-12; cited, not edited by a task)
- `scripts/plan_readiness.py`, `scripts/validate_review_staging.py` (validators; bytes unchanged)

**Receipts:**
- Origin row: docs/history/backlog/2026-10-10-maintenance-skill-size-refactor.md (Status: open; the landing rider flips it covered naming this plan)
- Prompt entry: docs/history/backlog/PLAN-PROMPTS.md `## maintenance-skill-size-refactor` (frozen under docs/tmp/authoring-claims/2026-10-10-maintenance-skill-size-refactor.md; pruned by the landing rider with the prune receipt)

## Validation Commands

**Production:**
```bash
grep -c "^## Revisions" agents/skills/maintenance/SKILL.md   # expect 0 (extracted)
grep -c "Revisions ledger" agents/skills/maintenance/CHANGELOG.md   # expect >=1 (ledger body intact)
head -3 agents/skills/maintenance/CHANGELOG.md   # the three-line extracted-ledger header Task 1 prescribes
grep -c "deviation" agents/skills/maintenance/prompt-templates.md   # expect <=3 (pointer only)
test -x scripts/skill_text_budget.py && python3 scripts/skill_text_budget.py --check   # exit 0, final line OUTCOME: pass (breach lines print advisory, never move the exit)
grep -c "skill_text_budget" scripts/check_maintenance_pins.sh   # expect >=1 (suite wiring)
grep -c "skill_text_budget" scripts/runtime-scripts.list   # expect 1
python3 scripts/test_skill_text_budget.py   # exit 0 (hermetic fixtures)
grep -c "skill_text_budget" scripts/machinery_registry.json   # expect >=1 (registered, warning-only)
grep -c "duties-core" agents/skills/maintenance/template-authoring.md   # expect >=1
grep -cE "^### Step 1: survey" agents/skills/maintenance/survey-arms.md   # expect 1 (heading verbatim)
wc -c agents/skills/maintenance/SKILL.md   # expect < 40001 (the 40KB class top of the 25-40KB router class the Gist claims)
```

**Tests:**
```bash
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )   # exit 0
python3 scripts/test_plan_review_boundary_examples.py   # exit 0
python3 scripts/machinery_inventory.py --check   # exit 1 at HEAD is the expected baseline (16 pre-existing findings at authoring time); the gate adds NO finding naming skill_text_budget.py
bash scripts/check-no-em-dash.sh file agents/skills/maintenance/SKILL.md   # exit 0
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file scripts/skill_text_budget.py   # exit 0 (prose filter skips .py unless the env flag is set)
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh   # exit 0 from the repo root
```

### Task 1: changelog extraction (both ledgers, cross-references, pins re-aims)

Files:
- agents/skills/maintenance/SKILL.md
- agents/skills/maintenance/CHANGELOG.md *(new)*
- agents/skills/maintenance/prompt-templates.md
- agents/skills/maintenance/templates-CHANGELOG.md *(new)*
- scripts/check_maintenance_pins.sh

- [x] Extract `SKILL.md`'s `## Revisions` region (the heading line through end of file, 75,756 bytes at HEAD, re-derive at execution) byte-verbatim into `agents/skills/maintenance/CHANGELOG.md` prefixed by a three-line header naming the file as the extracted Revisions ledger of `SKILL.md` and its extraction witness (this plan); replace the extracted region in `SKILL.md` with a two-line change-log pointer naming `CHANGELOG.md`. [class: IMPLEMENTATION_REQUIRED]
- [x] Re-point the in-file citation: the Step 5 five-minute-floor sentence keeps its "Revisions ledger" phrase and gains the changelog file name so the reference resolves post-move ("see agents/skills/maintenance/CHANGELOG.md, the Revisions ledger's 2026-09-15 floor-revision entry"); the citation's pin, if the suite pins that sentence, re-keys to the reworded span in the same change. [class: IMPLEMENTATION_REQUIRED]
- [x] Extract `prompt-templates.md`'s deviation preamble (the deviation-intro paragraph through the last deviation entry, ending before `## Authoring child`, 78,059 bytes at HEAD, re-derive at execution) byte-verbatim into `agents/skills/maintenance/templates-CHANGELOG.md` with the same header shape; replace the preamble with the title, a one-paragraph source-of-record pointer naming `templates-CHANGELOG.md` and the deviations' new home, and nothing else. [class: IMPLEMENTATION_REQUIRED]
- [x] Re-aim the pins script beside provenance: every whole-file grep whose pass relied on the ledger's in-file copy re-aims at the changelog files (the comment at the whole-file-grep note naming the Revisions-ledger copy, the deviation-paraphrase must-not-carry surfaces, and the exactly-two-occurrences blueprint-plus-deviation count checks are re-derived against the post-move tree with the surviving copy's home named in each comment); the region-scoped checks that split on `## Revisions` (the python operative-region cut and the awk exit-anchor scan) are re-aimed to the post-extraction shape and their comments tell the truth about what the operative region now is; no check is deleted and no count is loosened. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the corpus-wide resolution sweep: `grep -rn "Revisions\|deviation list" agents/ docs/maintenance/ README.md scripts/ --include=*.md --include=*.sh --include=*.json` and re-point every hit that names the old in-file locations to the changelog files; the task's end state is zero references to the old in-file locations outside the changelog files themselves and git history, verified by a final grep whose only remaining hits are the changelog files' self-references; record that final grep's output in the session log. [class: REPOSITORY_TEST]
- [x] Verify the moves byte-verbatim by mechanism, not claim: before editing, write each region to a gitignored scratch path in this worktree (`docs/tmp/pre-move-extraction/skill-revisions.txt` and `prompt-templates-preamble.txt`, captured with `sed -n` over the exact line ranges); after the move, `cmp` each scratch copy against the corresponding changelog-file region; record both cmp receipts in the session log; delete the scratch files after this task's landing. Then run the pins suite, the parallel-work regressions suite, and the hygiene scan green, and land this task as its own commit on the authoring branch. [class: REPOSITORY_TEST]

### Task 2: byte-budget gate (fleet-wide, warning-only, ratchet, admission fields)

Files:
- scripts/skill_text_budget.py *(new)*
- scripts/skill_text_budget_caps.json *(new)*
- scripts/test_skill_text_budget.py *(new)*
- scripts/check_maintenance_pins.sh
- scripts/machinery_registry.json
- scripts/runtime-scripts.list

- [x] Land `scripts/skill_text_budget.py`: outcome-contract style (`OUTCOME: pass`/`fail` vocabulary per scripts/OUTCOME_CONTRACT.md), `--check` mode walking every `agents/skills/*/[A-Za-z]*.md` skill file reporting per-file bytes versus cap, per-section advisory caps for the maintenance corpus from the analysis Part 4 table as the pilot, and `--ratchet` mode lowering caps on shrink and never raising; the script header states the admission test (the 35-commit one-shrink ratchet, the ~89K-token per-turn doctrine load, docs/maintenance/maintenance-skill-refactor-analysis-2026-10-09.md), the expected catch frequency and false-positive cost (a breach line on any landing that grows a file past its cap; false positives bounded by the seeded margin, the caps table being the tuning surface), the promotion criteria (blocking exit 1 only after its first true catch, promoted by a later change), and the sunset (two-phase, so no weekly measurement is owed that no consumer owns: until the growth-telemetry consumer lands - the doc-hygiene row owns that rider wiring and it stays out of this plan's scope - the gate runs warning-only with NO removal path; when the consumer lands, its first six consecutive weekly windows with zero reported breaches AND non-increasing fleet byte totals arm the removal the pre-registered removals row names; a dormant gate over a still-growing corpus is never the removal case). [class: IMPLEMENTATION_REQUIRED]
- [x] Seed `scripts/skill_text_budget_caps.json` at the post-Task-1 tree: per-file cap = current bytes plus the larger of 25% or 8KB, the margin rule stated in the table header; the maintenance per-section pilot caps carried as advisory members from the Part 4 table; a skill file with no caps entry is a reported gap line in the `--check` output, never a silent skip, and files a later task creates seed their caps in that task's own landing (cap = post-creation bytes plus the same margin, via `--ratchet`). [class: IMPLEMENTATION_REQUIRED]
- [x] Land `scripts/test_skill_text_budget.py` *(new)*: a hermetic fixture suite over a temp skill tree proving (a) a file over its cap produces a breach line while `--check` still exits 0 with a final `OUTCOME: pass` line (advisory), (b) `--ratchet` lowers a cap when the file shrank and a second `--ratchet` run never raises any cap, (c) the four-outcome vocabulary holds (`OUTCOME: fail` only on a modeled violation; usage and context failures map to `tool_error`, and a breach never maps to `fail`). [class: REPOSITORY_TEST]
- [x] Wire the gate into the pins suite as an advisory step after the existing checks: the step runs `--check` and prints its report; a breach line never moves the suite's exit code at this landing (warning-only); the step's comment names the admission fields and the promotion path. [class: IMPLEMENTATION_REQUIRED]
- [x] Register the gate in `scripts/machinery_registry.json` (the registry's fixed schema carries the warning-only posture, the admission test citation, and the sunset in the entry `note`, and the removals row in the `removals` array with disposition `delete`; no invented fields) and append the script to `scripts/runtime-scripts.list`; deploy the copy to `~/.ai-playbook/scripts/` in the same run; `python3 scripts/machinery_inventory.py --check` reports no unregistered-script finding for it afterward. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the pins suite, the machinery inventory check, the budget gate's own `--check` (expect `OUTCOME: pass` with zero breach lines on the seeded caps), `python3 scripts/test_skill_text_budget.py`, and the hygiene scan green, and land this task as its own commit. [class: REPOSITORY_TEST]

### Task 3: SKILL.md module split (router plus seven modules, headings verbatim)

Files:
- agents/skills/maintenance/SKILL.md
- scripts/machinery_inventory.py
- scripts/test_authoring_plans_liveness.py
- agents/skills/maintenance/survey-arms.md *(new)*
- agents/skills/maintenance/guards.md *(new)*
- agents/skills/maintenance/decisions.md *(new)*
- agents/skills/maintenance/quota-policy.md *(new)*
- agents/skills/maintenance/scheduling.md *(new)*
- agents/skills/maintenance/failure-cap.md *(new)*
- agents/skills/maintenance/state-file.md *(new)*
- scripts/check_maintenance_pins.sh
- scripts/machinery_registry.json

- [x] Split `SKILL.md` into the router plus the seven module files per the analysis Part 4 architecture: each module keeps its section headings byte-verbatim and moves each heading's section body whole; the router keeps frontmatter, configuration, loop-mode and cycle-gate summaries, the Step 0-7 skeleton as one-paragraph dispatch entries naming the module each step loads, invariants, integration points, and the router contract; the two headings the seven-module set does not obviously own are named to their home here: `### Trigger verbs (schedule vs execute vs resume)` and `### Blocker recovery` both move whole into `decisions.md`, beside the lane decisions they govern; no rule is restated in the router and no rule's semantics change; `zcode.md` stays one file. [class: IMPLEMENTATION_REQUIRED]
- [x] Re-point pins per module in the same landing: every pin whose anchor text moved re-keys to the module file that now carries it, keyed beside its provenance; pins whose anchors survive in the router are never touched; the suite is green before and after the move and its pin count never decreases across it (count with `grep -c '^pin ' scripts/check_maintenance_pins.sh`, 523 at authoring time, re-derive at execution; the Assumptions' 515 figure is the analysis's `pin()`-occurrence count, not this grep's; record the before and after counts in the session log); a pin that cannot re-key green takes the deferred-landing path and reports. [class: IMPLEMENTATION_REQUIRED]
- [x] Re-aim the split's coded consumers in the same landing: `scripts/machinery_inventory.py`'s state-field read (its hardcoded skill path and `## State file` heading anchor) re-points to `state-file.md` so the unregistered-state-field guard survives the move; `scripts/test_authoring_plans_liveness.py`'s span assertions against `SKILL.md` and `prompt-templates.md` re-key to the module files that now carry the spans; both run green in this task's battery. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the standing router-integrity pin row to the pins suite: every router dispatch pointer names an existing module file, each named module carries its step heading verbatim, and `SKILL.md`'s frontmatter `name:` and `description:` lines are byte-unchanged; a later edit that renames or drops a module fails the suite instead of stranding a pointer. [class: REPOSITORY_TEST]
- [x] Update the machinery registry rows naming the maintenance files to the post-split file set; run the corpus-wide navigation sweep (`grep -rn "SKILL.md Step\|SKILL.md's Step\|maintenance/SKILL.md" agents/ docs/maintenance/ scripts/*.py README.md` ) and verify every section-name citation still resolves to a file carrying that heading verbatim; record the sweep disposition in the session log. [class: REPOSITORY_TEST]
- [x] Run the pins suite, the parallel-work regressions suite, the budget gate `--check` (advisory), and the hygiene scan green, run `--ratchet` so the router's cap tightens to the post-split size plus margin and every newly created module file's cap seeds at its post-split bytes plus the same margin, and land this task as its own commit. [class: REPOSITORY_TEST]

### Task 4: template split (per-kind blueprints plus duties-core) and final verification

Files:
- agents/skills/maintenance/prompt-templates.md
- scripts/test_authoring_plans_liveness.py
- agents/skills/maintenance/template-authoring.md *(new)*
- agents/skills/maintenance/template-execution.md *(new)*
- agents/skills/maintenance/template-unblock.md *(new)*
- agents/skills/maintenance/duties-core.md *(new)*
- scripts/check_maintenance_pins.sh
- scripts/machinery_registry.json

- [x] Split `prompt-templates.md` into `template-authoring.md`, `template-execution.md`, and `template-unblock.md` (the two blueprints plus the parked-dependency unblock template; the pointer stubs stay with their kind or become one-line pointers, stated in each file's header) plus `duties-core.md` holding exactly the byte-identical shared duty sets the pins suite already holds identical; each blueprint names its core spans by reference and stays self-contained for everything else; no duty text is rewritten. [class: IMPLEMENTATION_REQUIRED]
- [x] Re-point the pins script's blueprint pins to the new files beside provenance: the byte-identical duty-set pins re-key to `duties-core.md` plus the naming references, the count-gated checks re-point their path variables (each per-kind file carries its counts individually after the split) and re-derive their counts against the post-split tree, and the body-identification spans re-key to the per-kind files; `scripts/test_authoring_plans_liveness.py`'s prompt-templates spans re-key to the per-kind files; the suite is green before and after and its pin count never decreases; update the machinery registry rows naming prompt-templates.md to the post-split file set. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full verification battery on the executed tree: the pins suite, both validation-command blocks, the parallel-work regressions suite, the machinery inventory check, the budget gate `--check` and `--ratchet`, the em-dash scan over the touched paths, and the hygiene scan; record each exit code in the session log and fix any red span before reporting the task done; this task's landing also seeds the created template files' caps via `--ratchet`. [class: REPOSITORY_TEST]
