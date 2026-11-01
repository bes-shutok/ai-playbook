# seal-landing diagnostic ledger: producer steps mint post-contract receipts with resolved paths

- Filed: 2026-11-01
- Status: open
- Priority: high
- Class: fix-class
- Origin class: learn Step 1.9 (project issue; second witness to lesson 238)
- Cluster: lesson 238 (docs/maintenance/development_lessons.md #238); the one-shot mask remedy for this ledger landed 2026-11-01 as commit e65a1be0b (covering the 2026-10-30-mask-certification-seal-diagnostics-embedded-paths origin row); this row owns the producer-side arm the mask arm does not reach

## Observed

The certification-seal landing diagnostics ledger's masking contract landed
2026-10-26 (every embedded path uses placeholder tokens or a repo-relative
form). Receipts minted after that landing (2026-10-28 through 2026-10-30) still
carried resolved sibling-worktree absolute paths in seven entries; the release
privacy gate refused the publish until they were masked by hand. The header
contract sentence did not reach the producer steps that mint the receipts; the
publish gate remained the only working detector.

## Expected

Either the producer steps mask at mint time (mask-before-append duty, the
shape the 2026-10-26 r1 fold already named for the append-failure leg), or a
cheap pre-append scan over the receipt body catches resolved filesystem roots
before the ledger accepts the entry; recurrence should not depend on the
release gate.

## Reproduction

Grep the ledger's history for receipts dated after the contract landing whose
captured command outputs contain resolved worktree roots; the seven 2026-11-01
masked entries are the witness set.

## Environment

ZCode runtime, ai-playbook repo, ledger at
docs/history/certification-seal-landing-diagnostics.md, 2026-11-01.

## Suspected root area

The masking contract lives in the ledger header prose; the minting producers
(landing diagnostic capture steps across execute-plan/done flows) never gained
the mask-before-append step, so compliance stays writer-habit-dependent.
