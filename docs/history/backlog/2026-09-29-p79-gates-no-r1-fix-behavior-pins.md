# Backlog: p79 validation gates tolerate silent revert of r1-fix behaviors

Driving force: code-quality

p79 r2 finding N3 (docs/reviews/2026-09-29-p79-code-review-r2-verification.md): the plan's Validation Commands pins are green with live content today, but no gate pins the r1-fix behaviors (schema bool/float rejection, roundtrip rendering sanitization, ledger guard placement, receipt scoping, emit echo-capture guidance, `_repo_root_matches_value` sharing) - a silent revert of any of them passes all gates. G8+G9 also tolerate stubbed test bodies. Candidate remedy: extend the selftest suite with assertions over the fix behaviors (suite-level pins are stronger than grep pins for behavior).
