# Backlog: the final terminal stage proves the commit identity exists but not that it is the run's closeout commit

- **Filed:** 2026-10-05
- **Status:** deferred (2026-10-06, operator adjudication: witnessed once, self-inflicted, caught immediately by the existing cross-check; cheap workaround discipline; a seconds-wide window does not justify a receipt-gate change)
- **Priority:** high
- **Workflow:** backlog
- **Origin class:** witnessed terminal-gate refusal with a surviving silent sibling
- **Class:** fix-class
- **Skill/step:** `scripts/execute_plan_runtime.py` `_final_terminal_stage` commit check, and `agents/skills/execute-plan/SKILL.md` final terminal stage step text

## Problem

The final terminal stage validates the supplied last_commit_sha with commit existence only (commit_lookup), while the pre-archive stage validates its identity through the stronger ancestor-or-self freshness seam (commit_ancestry) in the same file. A well-formed but fabricated identity passes every visual check and fails only existence, which is the witnessed catch; but a stale yet real identity, such as the pre-archive tip resupplied after the closeout commit, passes existence and binds a commit that is not the run's closeout commit into the permanent terminal receipt. Nothing mechanically ties the receipt's commit identity to the closeout window the archive gate opened, and no derive-at-compose duty exists at the boundary where the parent composes the driver payload.

## Evidence

- `scripts/execute_plan_runtime.py`, final stage: the commit check is `self.commit_lookup(last_commit_sha.strip())` refusing "commit identity is not provable"; the pre-archive gate runs the injectable `commit_ancestry` seam ("The staged terminal gate's freshness seam: True only when a commit is proven ancestor-or-self of HEAD"), and the same seam serves a recovery fix check.
- Witnessed 2026-10-05 in a consumer closeout: the session supplied `8cb690d55ec0b2ab3a3c90a52f3ecbc6540c11d7` (verified absent from the object store) while HEAD was `8cb690d5d98dbae698f4c95ccd9d2377ba1f68de` (the real closeout commit); the shared 8-hex prefix shows the value was reconstructed rather than derived from disk; the existence check caught it and the run completed through a manual retry with a properly derived value.
- The repository guideline that owns this class ("a value quoted from conversation context is not evidence: before any precision-critical step re-derive every digest, path, flag, or identifier from disk") is prose with no mechanical surface at this boundary; the execute-plan skill's final terminal stage step says "the last commit sha" without a derive-at-compose duty.
- The staged terminal operation landed in the integrity-quad consolidation 7baa8ce1 (staged archive gate, phase3 reconciliation trigger, orchestration authority validators); the ancestry seam exists beside the final stage's check unused by it.

## Expected

The terminal receipt's commit identity gets at least the pre-archive gate's freshness rigor plus a closeout-window bound. Candidate predicates to adjudicate at authoring: (a) the final stage runs the supplied identity through commit_ancestry (ancestor-or-self of HEAD) and verifies it is a strict descendant of the archive_gate receipt's recorded pre-archive identity, so the identity must lie inside the closeout window the receipt opened; (b) tip-equality: the supplied identity must equal the resolved HEAD at check time, the narrower contract that no commit may land between the closeout commit and the final call; (c) a derive-at-compose duty in the execute-plan skill's final-stage step text: the parent derives the identity inside the composing step (the same command that composes the payload), never resupplies a captured value, mirroring the repository re-derivation guideline as a skill-level duty with a stop-on-mismatch guard.

## Why not fixed now

The witnessed run completed through a manual retry with a properly derived identity. The change touches the staged terminal predicate, its fixtures, and the skill step text, and needs its own reviewed landing.

## Source

- Witnessed 2026-10-05 during the STORY-KEY closeout (the same execution that filed the telemetry-capture row).
- Capture hygiene: public-hygiene and em-dash scans pass.
