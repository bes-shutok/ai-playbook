# Archive-gate boundary for receipt-closed checklist lines

Backlog origins (scope of record): `docs/history/backlog/2026-10-02-receipt-closed-lines-vs-archive-gate.md`

Classification: [class: fix-class] docs boundary record (no behavior change); authoring only (this plan is not self-executing).

## Terminology and core concepts

- **Receipt-closed lines**: Commit, verification, and bounded-RED-disposition checklist lines that the execute-plan preflight's receipt-backed reconciliation deliberately leaves UNCHECKED in the plan bytes (the reconciliation accepts the run on receipt evidence, not checkbox bytes).
- **Archive-ceremony checkbox arm**: the done boundary's gate that refuses any archive whose plan bytes still carry an unchecked `- [ ]` task box, with two sanctioned exits (check the boxes after verified work, or a marked backfill completion record).

## Coverage dispositions (verified on disk 2026-10-01, at HEAD)

- The archive-ceremony gate's checkbox-failure sentence (done SKILL.md, the gates paragraph: "the two sanctioned exits: check the boxes after verified work, or land a marked backfill completion record per the plans skill's archive-correction exception") is landed and is the single insertion anchor; no gate code changes (the doc arm alone closes the confusion, per the origin's own alternative).

## Tasks

### Task 1: the boundary sentence in the archive-ceremony gate's sanctioned exits

Files:
- `agents/skills/done/SKILL.md`

Evidence:
- `grep -c "receipt-closed" agents/skills/done/SKILL.md` returns at least 1

- [ ] Run → expect RED: the Evidence grep returns 0 [class: REPOSITORY_TEST]
- [ ] In the gates paragraph's archive-ceremony checkbox-failure sentence, AFTER the complete existing sentence (its tail ends ...archive-correction exception), append the boundary as a follow-on sentence: A receipt-closed plan - one whose Commit, verification, and bounded-RED lines the execute-plan preflight's receipt-backed reconciliation deliberately leaves unchecked in the plan bytes - still has its boxes flipped, or lands a marked backfill, before archiving; the reconciliation's acceptance is verification evidence for the check-the-boxes exit, never license to archive unchecked bytes [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the Evidence grep [class: REPOSITORY_TEST]
- [ ] Commit: `skills: archive-gate boundary names the receipt-backed reconciliation` [class: IMPLEMENTATION_REQUIRED]

### Task 2: full-suite validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block

- [ ] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]

## Validation Commands

```bash
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base main
bash scripts/check_maintenance_pins.sh
grep -c "receipt-closed" agents/skills/done/SKILL.md
```

## Assumptions

- Only `agents/skills/done/SKILL.md` changes; the doc arm alone closes the confusion per the origin's own alternative, and no gate message or code changes. The reconciliation arm the clause names is documented today in the driver source and the completed overlay plan; its execute-plan skill-layer doc sync is tracked residue outside this plan's doc-arm scope. The origin's Filed date (2026-10-02, the filer's clock) postdates this plan's date by a day - provenance noted, content matches.
- The insertion extends one existing sentence without touching any pinned span (the gates paragraph's presence pins key on intact openers).

Decision points requiring a grill: Task 1 boundary form (a clause inside the sanctioned-exits sentence naming the reconciliation as evidence source, never a behavior change or a second exit).

## Review Scope

- `docs/history/plans/2026-10-01-archive-gate-receipt-closed-boundary.md`
- `agents/skills/done/SKILL.md`
- `docs/history/backlog/2026-10-02-receipt-closed-lines-vs-archive-gate.md`
