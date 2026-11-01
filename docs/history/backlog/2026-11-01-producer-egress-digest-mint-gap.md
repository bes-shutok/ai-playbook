# Exec-review producer cannot carry the archive-egress digest at mint time; hand backfill is the only route

Status: open
Priority: medium
Class: tooling-gap
Origin class: learn Step 1.9 project issue capture (2026-11-01 plan-prompts-stub-writer-forensics closeout witness)

Cluster: docs/history/backlog/2026-10-22-producer-review-findings-followups.md (same script: `scripts/produce_exec_review_record.py` follow-up family)
Cluster: docs/history/backlog/2026-10-31-review-record-producer-clean-round-constraints.md (same script: undiscoverable producer contract family)

## Observed versus expected

`scripts/produce_exec_review_record.py` is creation-only (it never repairs an
existing pair), and a run mints its exec-review record pair before the
completion pass moves the plan to `completed/`. The reverse-squash guard's
archive-egress evidence leg (`scripts/reverse_squash_guard.py`,
`find_evidence_record`) then demands an exec-review record whose content
carries the sha256 of the ARCHIVED bytes - a value that cannot exist in the
record at mint time, because the archived file only comes into being with the
completion pass. Expected: the producer supports supplying the egress digest
at mint time (digesting the archive-destination path) or a sanctioned,
validator-checked backfill subcommand; observed: the only route is a hand
`cat >>` edit into both reviews homes, with no mechanical check that the
digest landed (and the landing retry as the only verifier).

## Witnessed cost (2026-11-01, plan-prompts-stub-writer-forensics landing)

The hand backfill append was `&&`-chained after a failing sha probe (the
archived path exists only in the run worktree pre-landing), so the append
silently never ran; the mirror copied stale bytes into both homes; two
landing attempts were refused before the digest was verified present with
`grep -c`. A second shape in the same pass: once the evidence leg is
satisfied, a `--ack-egress` passed alongside it becomes an unused-ack refusal
(the ack is an alternative exit, not an additive leg), costing another
refusal round-trip. Lesson 287 (third witness) records the mechanics.

## Work needed

One bounded producer change: add an option (for example
`--egress-digest <sha256>` or `--egress-path <path>` digested at mint time)
that places the archive-egress digest into the record pair at mint, plus one
fixture pin proving the minted pair satisfies the guard's
`find_evidence_record` leg unchanged. Alternatively (smaller): teach the
guard's refusal text to name the digest-presence check
(`grep -c <digest> <record>` in both homes) as the retry pre-check, leaving
the producer untouched. No new gate; this removes a hand-edit family that has
now cost refusals in three consecutive landings (lesson 287 witnesses).
