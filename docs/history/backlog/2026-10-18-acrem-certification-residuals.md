# Backlog: acrem certification residuals (2026-10-18)

- **Filed:** 2026-10-18, certification closeout (r11) of docs/history/plans/2026-10-17-archive-ceremony-review-evidence-mismatch.md
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** certification residual
- **Class:** fix-class
- **Driving force:** simplicity (five residuals routed to one durable row: the two Low residuals priced out of the certified bytes, plus three Medium residuals captured from the redundant parallel panel's stand-down report)
- **Cluster:** docs/history/plans/completed/2026-10-18-closeout-gate-series-token-infix.md (same class: certification residuals routed to a durable row)
- **Cluster:** docs/history/backlog/2026-10-17-archive-ceremony-writer-side-binding-text.md (same surface: residuals tracked against the landed archive-ceremony plan)

## Residuals

1. O1 (correctness-completeness, quality#test-implementation-alignment, Low): the Task 4 screening witness states its boundary on the raw basename length ("exceeds 64 characters"); state it on the screened length, or pin the fixture comfortably above the boundary (for example at least 70 raw characters with one control character), so the full-screened-basename assertion can only hold under the no-truncation variant and a boundary-exact fixture cannot pass the truncating default.
2. O2 (correctness-completeness, implementation#requirement-coverage, Low): the Terms `reviewed revision` definition still enumerates two unrecoverable shapes and its recovery recipe points at the parent-state blob, which reads as sanctioning the forbidden base-blob approximation for the degenerate delete-then-add rename; extend the enumeration with that shape (raw bytes None, archived-bytes binding alone) when a later round touches Terms or Task 1.
3. O3 (testing, testing#needle-unreachable-from-prescribed-text, Medium): the Task 1 recipe "the plan bytes amended between the boundary and the archive add by a small edit above the rename-detection threshold" is not self-executing and reads inverted (similarity must stay above the threshold, so the edit must be small). Measured in scratch repositories at the test suite's house fixture scale: two-line plan bodies emit D+A for any amendment; pairing holds from about four content lines up (R081 at 4 lines, R086 at 6, R089 at 8, R074 at 10 with one edited line). Fix: pin a sizing rule (the fixture plan carries at least four checked task lines; the amendment appends or edits one short line so the pair stays above git's rename-detection threshold) and the base-blob-distinct property the refuse arm needs.
4. O4 (testing, testing#hermeticity-gap, Medium): the Task 3 pin "core.autocrlf=false with no text or eol attributes" covers only repo-local configuration; a global core.attributesFile declaring text normalization for the fixture's file kind normalizes the committed blob to LF and the expected-GREEN arms refuse (measured end-to-end; this host's global core.autocrlf=input is defeated by the repo pin, so the attributes path is the gap). Fix: pin the mechanism - repo-local core.attributesFile set to an empty fixture file, or GIT_CONFIG_GLOBAL/GIT_ATTR_NOSYSTEM in the sweep env.
5. O5 (testing, testing#missing-test, Medium): Task 1 threads the staged-addition shape but no witness covers it: the Task 3 else-form witness pins only untracked and committed additions, and the existing staged fixture is a rename (git mv), so the index branch ships unwitnessed. Fix: extend the else-form witness (or Task 4) with a staged-addition arm: a staged-addition archive whose record carries the archive-state identity with the staged bytes' digest and a yes verdict expects the pass.

Both are certification-round overflow residuals per the certification-residual routing (never a re-round, never a fold); none blocks execution or landing. Items 3 through 5 were filed 2026-10-19 from the redundant parallel session's r11 panel stand-down report (development-lessons #87); its panel independently converged on the row's screening-length residual O1, which strengthens it.
