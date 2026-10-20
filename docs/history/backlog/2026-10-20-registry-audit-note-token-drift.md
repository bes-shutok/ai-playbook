# Backlog: the registry audit cell carries execution narration stamped `user-approved`, not user confirmations

- **Filed:** 2026-10-20, operator-directed registry relocation pass (the stranded-rows data repair)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** session-witnessed contract drift (writer skills versus the registry's audit-note contract)
- **Class:** fix-class
- **Driving force:** correctness (an approval token that no user minted licenses nothing, yet 579 rows carry one)
- **Skill/step:** `agents/skills/plans/SKILL.md` completion transition (the "append exactly one ownership-registry row" sentence names the minimum cells and says nothing about `audit`); `agents/skills/doc-hierarchy/SKILL.md` registry column table (`audit` row) and its Corruption override paragraph; consumer `scripts/doc_registry_validator.py` `audit_note_valid` / `audit_note_defects`
- **Capture hygiene:** repo-relative paths only; no personal or machine-specific data.
- **Dedup probe:** searched open backlog filenames and text for `audit note`, `user-approved`, `registry row`, `ADR-0001`; nearest rows are `docs/history/backlog/2026-10-19-dated-record-stamp-audit-arm.md` (dated stamps on records, not the approval token) and the relocation row this pass deleted (`2026-10-19-doc-registry-stranded-rows-relocation`, landed per the covered-row rule); no open row owns the token's meaning drift.

## Problem

The registry contract (`agents/skills/doc-hierarchy/SKILL.md`, `audit` column row and the Corruption override paragraph; ADR-0001 in `docs/history/plans/completed/2026-09-08-doc-ownership-lifecycle.md`) defines the `audit` cell as the sole override licensing an edit to a frozen completed-history body, written only after explicit user confirmation, beginning with the dated token `user-approved YYYY-MM-DD:` and recording "what the user confirmed". The validator enforces the shape only: any non-empty note on a completed, superseded, or rejected row must begin with a real, non-future token (`audit_note_valid`), and it has no way to know whether a user confirmed anything.

Measured on `docs/maintenance/document-registry.md` at the 2026-10-20 relocation pass: of the completed rows, 75 have an empty `audit` cell, 579 carry `user-approved <date>:` followed by execution narration ("execute-plan run in worktree ...; Tasks 1-2 implemented, Task 3 rider ...", "migration audit - received ... disposition"), and 5 (the stranded rows this pass relocated) carried the same narration without the token and failed the validator the moment they were parsed. The token-bearing rows date from the registry's introduction (2026-09-10, `7dcdf6c5b`): writers have used the cell as an execution summary from day one and prefixed the token because the validator demands it, so the field's meaning has drifted from "the user confirmed this override" to boilerplate. ADR-0001's own rule, "a self-minted token licenses nothing", is unenforceable once every row carries a minted token.

The writer side has no rule either way: the plans completion transition names the minimum cells (`identity`, `sot`, `state`, `archived`, `src`) and is silent on `audit`, and the doc-hierarchy column row says only what a non-empty note must look like, not when the cell stays empty.

## Expected

A routine completion leaves the `audit` cell empty; the execution summary lives in the landing commit message and the archived plan's disposition section (the committed-witness rule already says those carry paths and dates). A non-empty `audit` note appears only when a user actually confirmed an override, and then names what was confirmed, so the token keeps the meaning ADR-0001 gave it.

## Suggested fix

Smallest form first, skill text only, no validator change:

1. One sentence in the plans completion transition sentence (`agents/skills/plans/SKILL.md`): the row's `audit` cell stays empty on a routine completion; the execution summary belongs in the commit message, never in the registry row.
2. One clause in the doc-hierarchy `audit` column row (`agents/skills/doc-hierarchy/SKILL.md`): empty on every row except an ADR-0001 override the user confirmed; narration is never an audit note.
3. Existing 579 notes: leave them (a retroactive scrub of committed registry rows is a separate operator decision over an immutability-adjacent surface and is not part of this fix); the five relocated rows already have empty cells.

Rejected: a validator arm that refuses token notes lacking confirmation vocabulary (machinery over a wording heuristic, no witnessed incident of a false override, high false-positive cost on 579 rows); widening the contract so narration is a sanctioned note class (it would legitimize the drift and leave ADR-0001 with no distinguishable confirmation token).
