# Backlog: Bind the certified-final review record's status at execution landing

- **Cluster:** docs/history/backlog/2026-11-03-review-plan-cap-closure-seal-anchor-composition.md (same surface family: review-record lifecycle states versus what landing gates verify; that row owns the seal composition clause, this row owns the terminal-state binding)
- **Cluster:** docs/history/backlog/2026-11-04-execution-lane-authored-plans-misread-as-landed.md (same surface: the execution-lane landing/record lifecycle; that row owns the landed-versus-executed classification the exec lane's candidate selection reads, this row owns the certified-final record's terminal state)
- Status: open
- Priority: normal
- Age: new (2026-11-04)

## What is owed

Decide and pin the sanctioned terminal state of a plan's authoritative plan-review record at execution landing. Witnessed 2026-11-04 (exec takeover run over review-freshness-and-code-coverage-gaps, landing 7d4d3f7a2): the branch's highest plan-review record (r22) carried `Status: STAGED` with verdict `ready=yes` and zero findings, the landing's gates (probe containment, merge-tree trial, pins, hygiene, em-dash, focused runtime tests, full 3338-test suite) all passed, and the landing landed with the record still STAGED - no gate, validator, or landing-tail duty binds a certified-final record's status transition (staged -> posted/consumed) for the execution lane. The repair is either a landing-tail duty that marks the certified-final record's terminal state at landing (one status line, the existing record-selection helper's vocabulary), or an explicit recorded decision that STAGED is the sanctioned terminal state for execution-lane plan records, with the done finalize's record scans updated to expect it. Scope: the landing/validate machinery's record-status checks and the done finalize's missing-review-record scan; no record content changes.

Found by the 2026-11-04 exec takeover session's post-landing review of its own records (automation-18a7c17d carrier, session sess_1e4ddb48-a355-4508-9edc-e35bb76686b2); the landing itself is not blocked by this row and needs no rework.
