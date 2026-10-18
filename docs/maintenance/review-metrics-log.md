# Review metrics log

Aggregates only; per-run reports live under ~/.ai-playbook/review-telemetry/reports/ (gitignored).

## ai-playbook 2026-10-12T132741 (weekly rider, sess_9f5841ba)

- Loops 1,977; legacy-bucket sidecars 2,519; malformed-finding skips 57.
- Ready rate per round: r1 0.16, r2 0.26, r3 0.24, r4 0.21, r5 0.17, then decaying (r8 0.04, r12 0.01, r16 0.00); findings per round decay 12,670 (r1) to 72 (r16).
- Cap-exhaustion share and complexity-band segmentation: not present in this run's report output; recorded as absent rather than synthesized.
