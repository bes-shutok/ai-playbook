# gate-removal report-only notes join raw manifest destination strings
Cluster: docs/history/backlog/2026-11-01-gate-removal-formal-residues.md; docs/history/backlog/2026-11-01-gate-removal-multi-record-gate-report-conjunction-test.md; docs/history/backlog/2026-11-01-gate-removal-record-index-bool-stamp-exclusion-untested.md; docs/history/backlog/2026-11-01-gate-removal-resolver-verified-destinations-derivation.md (same-day review family)

Driving force: correctness

The unattributed/hold/expired note joins in `_gate_branch_closeout` embed raw `destination` strings from the manifest into agent-consumed gate output without stripping newlines or control characters. A destination containing `\n` (real filenames may; the manifest is hand-editable) can forge gate-shaped advisory lines (a fake authorization or note line) into the teardown report. The final `OUTCOME:` line cannot be forged, so this is output spoofing, not outcome flipping; the sink class pre-exists in the two sibling lines and this plan added a third instance. Reachability: plausible-edge; blast radius: local.

Fix: sanitize each destination before joining at all three sites in the attribution segment (escape `\x00-\x1f` as `\xNN`), with one test feeding a newline-bearing destination. Witness: Phase 3 r1 risk lens on gate-removal-inherited-manifest-rows (2026-11-01), F1.
