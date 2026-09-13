# Backlog: plan_readiness path-shape and markup accepted-tail extensions

Status: open
Origin: execution review r1 (2026-09-13) of docs/plans/2026-09-09-plan-readiness-trailer-tail.md, findings F2 and F4

- The r4-F2 path-shape predicate (`/` in token or known suffix) drops real
  slash-less, unlisted-suffix paths (`Makefile`, `Dockerfile`, `README`,
  `.gitignore`, `site.yaml`) from task-Files collection; consider extending
  REVIEW_SCOPE_DOC_SUFFIXES/IMPLEMENTATION_SUFFIXES or a root-file allowlist.
- The leading-span rule regresses bold-wrapped backticked paths
  (``- **`src/a.py`**``) in both directions (phantom false-reject; check-(a)
  escape in category blocks); consider stripping surrounding emphasis markup
  before span extraction.

Both are recorded as accepted tails in the plan's Design Invariants; fix only
if a real authoring shape hits them.
