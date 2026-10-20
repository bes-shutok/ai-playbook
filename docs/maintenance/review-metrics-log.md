# Review metrics log

Aggregates only; per-run reports live under ~/.ai-playbook/review-telemetry/reports/ (gitignored).

## ai-playbook 2026-10-12T132741 (weekly rider, sess_9f5841ba)

- Loops 1,977; legacy-bucket sidecars 2,519; malformed-finding skips 57.
- Ready rate per round: r1 0.16, r2 0.26, r3 0.24, r4 0.21, r5 0.17, then decaying (r8 0.04, r12 0.01, r16 0.00); findings per round decay 12,670 (r1) to 72 (r16).
- Cap-exhaustion share and complexity-band segmentation: not present in this run's report output; recorded as absent rather than synthesized.

## ai-playbook 2026-10-20T121209 (weekly rider)

- Loops 1,270; legacy-bucket sidecars 1,532; malformed-finding skips 41.
- Findings per round decay: 7,942 (r1), 4,263 (r2), 2,928 (r3), 2,022 (r4), 1,343 (r5), down to 58 (r16) and 15 (r20).
- Ready rate per round: r1 0.18, r2 0.25, r3 0.23, r4 0.21, r5 0.17, r6 0.10, then decaying (r8 0.04, r12 0.01, r20 0.00).
- Cap-exhaustion share: 34 of 1,270 loops (0.03).
- Complexity-band segmentation: small 50 loops (cap share 0.00, ready r1 0.50), medium 280 (0.02, ready r1 0.24), large 570 (0.05, ready r1 0.14), unknown 370 (0.00, ready r1 0.16; the legacy bucket counts in the unknown band).
