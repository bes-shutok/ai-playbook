# Backlog: turn_usage Variant B sentence precision and proxy-bullet comma splice

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-23
Origin: P37 execution code review r1 findings F3/F4 (docs/reviews/2026-09-23-code-review-p37-context-budget-probes-and-runtime-state-r1.md)

## Driving force

The landed Variant B sentence in agents/skills/maintenance/zcode.md says turn_usage "carries per-turn token columns but none tracks context size", while the verification notes' negative is sums-based ("none tracks context size via per-session sums") and a per-row input_tokens value approximately tracks that request's context (87-97% cache-inflated). A future reader attempting a per-row read could cite the notes against the unqualified prose. The rewritten Proxy ratio bullet also carries a plan-authored comma splice.

## Expected

- Narrow the Variant B claim to the sums-based form (or add the per-row caveat) without breaking the `turn_usage` pin.
- Fix the comma splice in the Proxy ratio bullet.
