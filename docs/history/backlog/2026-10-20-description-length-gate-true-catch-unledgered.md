# Backlog: the description-length sweep gate caught a dropped skill and warning posture discarded the catch

- **Filed:** 2026-10-20, ad-hoc fix of the missing execute-plan skill in ZCode (learn Step 1.8 capture)
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** session-witnessed true catch of a warning-posture gate, unledgered
- **Class:** fix-class
- **Driving force:** reliability (a skill silently absent from an agent runtime for a day while the gate built for that class fired unread at every landing)
- **Skill/step:** `agents/skills/done/SKILL.md` Step 3 landing sweep (`description-length` in `LANDING_WARNING_GATES`, `scripts/done_sweep_gates_lib.py`); `scripts/check_skill_description_length.py`; registry entry `script:check_skill_description_length.py` in `scripts/machinery_registry.json`; AGENTS.md Machinery admission protocol (promotion criteria)
- **Capture hygiene:** repo-relative paths only; no personal or machine-specific data.
- **Dedup probe:** searched open backlog filenames and text for `description-length`, `1024`, `warning posture`, `guard-liveness`, `promot`; nearest rows are `2026-10-10-promotion-threshold-activation-contract.md` (maintenance pre-review stops, a different gate family) and `2026-10-17-memory-index-over-budget-compress-and-index.md` (a byte budget on the memory index, not a sweep gate); no open row owns this gate's posture.

- **Cluster:** (the shared-mechanism row docs/history/backlog/2026-10-20-description-length-checker-scans-gitignored-synced-cache.md was deleted 2026-10-22 by its covering plan's execution; the description-length family link now lives in that plan's disposition record)
- **Cluster:** docs/history/backlog/2026-10-18-done-plan-readiness-child-tool-error.md (shared mechanism: same runner or gate family; investigate 2026-10-20 roster)
## Problem

`agents/skills/execute-plan/SKILL.md` carried a frontmatter description of 1159 characters from a 2026-10-19 wording edit (988 before it). The ZCode skill loader drops any skill whose description exceeds 1024 characters (its `diagnosing-skills` guide, pitfall 8), so the skill was absent from that runtime's skill list until a user asked why on 2026-10-20 and the description was trimmed to 852 characters.

The sweep's checker names this exact class: `python3 scripts/check_skill_description_length.py` on the pre-fix bytes prints `folded description 1159 > 1024` and exits 1 (reproduced 2026-10-20). The gate rides in warning posture (`LANDING_WARNING_GATES`, demoted because it had "no ledger catches"), so every landing between the 2026-10-19 edit and the fix printed the failure as a warning and proceeded. No landing recorded the firing in the guard-liveness ledger, so the promotion criterion the admission protocol names (a true catch) was met and invisible at the same time.

The gate was built for this class: the same file crossed the cap on 2026-09-27 (1167 characters), was trimmed on 2026-09-28, and the checker landed on 2026-09-30 (`docs/history/plans/completed/2026-09-30-skill-description-length-gate.md`). Two over-cap events on one file in three weeks; the second one slipped through the gate meant to stop it.

## Expected

A skill description over the loader cap never lands: the `description-length` gate refuses the landing commit, naming the file and the folded length, and the run fixes the description before landing. Until promotion, every firing of the warning-posture gate reaches the guard-liveness ledger so the evidence stream the protocol reads is complete.

## Suggested fix

Smallest form first, under the Machinery admission protocol:

1. Ledger the catch: this run records `--guard-firing description-length:catch:...` at its finalize (done Step 6), so the ledger carries the 2026-10-20 witness.
2. Promotion plan (plan-worthy, not an in-lane edit): move `description-length` out of `LANDING_WARNING_GATES` so a non-zero checker child refuses the landing. The plan names this row as the incident, the expected catch frequency (two over-cap events on one file in three weeks; every description grows incrementally across edits), the false-positive cost (none when the cap matches the consuming loader; the checker already carries a 950-character warning band for approach), and a sunset or review date. Per the protocol a promoted blocker retires or demotes an existing blocker in the same change, or the operator explicitly approves net growth after this true catch; the plan names its candidate.
3. Pre-register the registry-removal row for the promoted gate (sunset and promotion criteria) in `scripts/machinery_registry.json` in the same plan.

Rejected: editing `LANDING_WARNING_GATES` inside the learn or done run that witnessed the incident (a mid-lane gate edit to unblock or harden oneself is forbidden without a plan); a runtime-specific hook that re-checks descriptions on ZCode only (skills are tool-agnostic and the cap is already the checker's constant); lowering the checker's cap below 1024 (the threshold is right; the posture discarded the catch).
