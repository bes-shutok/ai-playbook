# Done manifest writer and finalizer disagree on repository identity

Captured: 2026-09-28 (source: consumer done closeout, manifest finalization)
Status: done (2026-09-30; implemented by the executed p79 done-closeout plan's contract pass, squash main 89fa19b1: versioned manifest identity with repo_root as the 64-hex digest plus two-arm legacy-path matcher, single-source writer/finalizer contract (_repo_root_matches_value), named schema/identity finalize abort leaving the manifest unchanged (_finalize_identity_mismatch), producer-to-finalizer round-trip coverage (test_round_trip_writer_to_finalizer), and the manual completion-flag repair prohibition in done Step 6 triage; deployed twins verified in sync 2026-09-30. Verified against every Expected bullet on disk this date; closed as a landed-work straggler, no plan needed)
Priority: high
Workflow: backlog
Class: correctness
Driving force: reliability
Origin class: consumer-feedback (company)
Consumer urgency: Consumer projects using done need writer/finalizer identity agreement to avoid manual manifest repair; the skills-repo personal priority profile must not defer this shared-skill fix as formal-hardening for the skills repo alone.

## Problem

In a consumer project closeout, the run manifest stored `repo_root` as the SHA-256 fingerprint recorded by the run-start marker. The deployed `finalize-manifest` helper compared that field as a filesystem path and reported that no matching manifest existed. The closeout could not complete through its normal finalizer; after verifying the run ID, fingerprint, owned commit, and gates, the completion flag was set manually.

This is a contract mismatch between manifest producer and consumer, possibly caused by runtime deployment drift. A missing-manifest response obscures that mismatch and invites unsafe manual edits to the run record.

## Exact location

`agents/skills/done/SKILL.md`, Step 0 run-manifest writer contract and Step 6 finalizer; `scripts/done_sweep_gates_lib.py` writer/finalizer implementations and deployed runtime copies.

## Expected

- Define repository identity in the manifest schema as an explicit typed field, distinguishing a canonical path from a content fingerprint.
- Ensure the writer and finalizer use the same identity contract and schema version, including when invoked from deployed runtime copies.
- Add a round-trip test that writes a manifest using the production writer and successfully finalizes it using the deployed/runtime finalizer.
- On incompatible schema or identity, fail with a specific version/identity mismatch and leave the manifest unchanged; do not report a generic missing manifest.
- Remove manual completion-flag repair from the supported closeout path.

## Severity and source reference

Severity: medium

Source: consumer done closeout, finalizer reported no matching manifest after the writer recorded a root fingerprint; capture hygiene: scan-public-hygiene --files pass.

## Why not fixed now

The user asked for session learning and backlog capture, not a change to done runtime or manifest schema.

## Dedup probe

Search terms: `run manifest`, `repo_root fingerprint`, `finalize-manifest identity`. Nearest: `docs/history/backlog/2026-09-22-execute-plan-empty-process-identity.md`, which concerns the meaning and validation of a worker process identity, not repository identity agreement between done's manifest producer and finalizer. No open item covers this round-trip mismatch.

## Evidence

The done-session notes record the fingerprint-versus-path mismatch and manual completion after independent verification. No repository path, project name, or fingerprint is included here.

## Suggested fix

Trace the runtime deployment path for both manifest operations, establish one versioned identity contract, and add the producer-to-finalizer round-trip coverage before changing the closeout's failure handling.
