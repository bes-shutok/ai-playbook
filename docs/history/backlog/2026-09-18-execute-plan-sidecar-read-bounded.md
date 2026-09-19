# Clean-round sidecar read is unbounded in the staged terminal gate (r5 CC5-3, deferred at round cap)

Evidence: scripts/execute_plan_runtime.py ~:3835 reads the review sidecar with read_text() fully into memory under the held manifest lock; every other read in the gate (plan text, digests) uses the 1,000,000-byte bounded policy. The plan specified only path-policy resolution for the sidecar, so this matches the plan's letter; runtime-contract.md documents the sidecar read as terminal-gate-only without a bound.

Direction: cap the sidecar read with the LIMIT+1 byte pattern (read binary, refuse over-limit as clean-round evidence failure, then decode/parse), mirroring the plan-read policy; document the bound in runtime-contract.md.
