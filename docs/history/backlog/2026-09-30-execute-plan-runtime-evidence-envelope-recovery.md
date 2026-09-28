# Backlog: Align execute-plan evidence envelope limits and recovery

- **Filed:** 2026-09-30
- **Status:** done (2026-09-30; executed+landed via docs/history/plans/completed/2026-09-30-execute-plan-runtime-evidence-envelope-recovery.md, exec review r1 ready=yes zero blocking)
- **Workflow:** backlog
- **Priority:** high
- **Class:** fix-class
- **Origin class:** consumer-feedback (company)
- **Driving force:** reliability; secondary simplicity
- **Consumer urgency:** Company projects running execute-plan need a supported way to validate and recover oversized evidence envelopes; the skills-repo personal priority profile must not park or defer this shared-skill fix as formal-hardening for the skills repo alone.
- **Source:** A consumer execute-plan run, 2026-09-30. After task-local contract recovery, the registered verifier could not complete its evidence checkpoint under the active runtime envelope limit. A temporary project-local driver copy with a larger bounded envelope was used to finish validation. No shared skill or driver source was changed. Capture hygiene: `scan-public-hygiene.sh --files` pass.
- **Dedup probe:** Searched open backlog filenames and problem bodies for `evidence envelope limit`, `runtime criterion bytes`, `oversized evidence recovery`, and `driver copy`. The nearest items concern prelaunch contract validation and driver path ownership; neither defines runtime envelope-size parity and a sanctioned recovery for an already-launched verifier. Keep this as a separate runtime-contract issue.

## Problem

A task's registered verification command and required criteria may fit the plan and recovery authoring paths but exceed a downstream runtime evidence envelope limit. The driver then rejects the worker checkpoint after implementation or verification has run. When the contract recovery path does not permit correcting that launched state, execution can require an ad hoc local copy of the driver, risking divergent runtime behavior and leaving no reusable, supported recovery procedure.

## Expected behavior

- Define one bounded evidence-envelope contract across plan parsing, manifest creation, worker checkpoint serialization, verification, and recovery.
- Validate the complete envelope before launching a worker, with task and field details plus a supported correction path.
- When a verifier has already launched, provide a receipt-fenced recovery transition for a corrected envelope that preserves claim identity, generation, audit history, and replay protection.
- Keep limits bounded and prove every consumer supports them. Do not require project-local copies or unreviewed limit changes to finish a valid task.
- Add regression coverage for exact-boundary and over-boundary envelopes, including UTF-8 byte counting, multi-item aggregate size, verifier output, recovery after launch, stale identity, replay, and refusal without state mutation.

## Evidence

The run completed documentation assertions and the registered plan verifier after a local driver-copy workaround, but the normal runtime rejected the evidence envelope. This demonstrates a gap between an accepted or recovered task contract and the downstream checkpoint boundary; it does not establish that globally raising the limit is safe.
