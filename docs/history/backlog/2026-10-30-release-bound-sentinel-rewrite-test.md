# Backlog: Add rewrite-level LOCATOR-BOUND-EXCEEDED branch test

Driving force: code-quality
Cluster: release privacy gate diagnostics

The bound tests drive only the helper directly; the rewrite-level sentinel branch in release-rewrite.sh invoke_scanner (crossed the 65536-byte locator parse bound message) has no test. Add a selftest case with an oversized-output fixture scanner driving the rewrite.
