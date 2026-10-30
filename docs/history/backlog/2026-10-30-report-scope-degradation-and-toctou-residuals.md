# Backlog: report-scope degradation and TOCTOU residuals (hygiene scanner r2)

Driving force: reliability (primary), simplicity (secondary)

Origin: Phase 3 review round 2 on plan docs/history/plans/2026-10-26-hygiene-scanner-default-scope-parity (worktree 2026-10-30-hygiene-scanner-scope-parity, 2026-10-30). Deliberate non-fixes: each residual verified true by the panel and judged not to block the landing. Witness: Phase 3 r2 panel.

Named residuals:

1. (design-simplicity c1) `scripts/scan-public-hygiene.sh` `run_report_scan` duplicates the rg invocation loop for the builtin patterns and the shared patterns file (one rg per pattern over the same scope); consolidating into a single rg pass with repeated `-e` flags would remove the duplication and the per-pattern process churn without changing the record grammar.

2. (risk F2) TOCTOU windows stand by design: a tracked path can enter or leave the scope between the git enumeration and the rg open, and the shared patterns file can change between the `-f`/`-r` gate and the read inside the process substitution; both windows fail visible (the failed rg pass or read gates the scope) rather than fail open, and closing them needs an atomic snapshot the scan sizes do not justify.

3. (risk F4a/F4b) Whole-scope degradation in `run_report_scan` reports `enumeration-unavailable` even when enumeration succeeded and the rg scan itself failed (a mislabeled fixed record), and the production `mktemp` files (changed-mode scratch, enumeration list, report matches) are not trap-cleaned when a run is interrupted, unlike the selftest's trapped temp dir; residue lands in `$TMPDIR` outside the repository.

Status: open. Any landing must keep the `PUBLIC_HYGIENE_REPORT:` prefix grammar and the fixed-record set the done gate forwards, and must not change `--files`/`--changed-from` semantics.

Fourth residual (review r3 F1): the gate's split-debris filter drops a genuine report record when the tracked path contains `:<digits>:` (unescaped by the quote helper); debris and genuine records are textually indistinguishable, so the rare false negative on the advisory warnings channel is accepted rather than coded around.

Fifth residual (review r2 testing lens): the gate-level pin asserts the ordinary stub row never becomes a warning but not that it stays out of the finding message, so the "ignore unrelated successful scanner output" clause is half-pinned at the message channel.

Cluster: docs/history/backlog/2026-10-30-frozen-full-tree-rg-fail-closed-arm.md (same surface: scripts/scan-public-hygiene.sh rg invocation shapes; same review origin)
