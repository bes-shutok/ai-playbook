# Backlog: check_backlog_claimed resolver docstring over-claims the missing-key warning; resolver pair warn semantics drifted

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-24
Class: non-blocking review Low (contract-docs drift between twin resolvers)
Source: P51 plans/authoring surface hygiene code review r1 F8
Driving force: code-quality

## Observed

`scripts/check_backlog_claimed.py` `resolve_plans_dir`'s docstring says "A missing facts key warns on stderr (exit code unaffected)", but the code warns only when the key is present but blank (`raw is not None` guards the warning inside the `not raw or not raw.strip()` branch); a truly absent `plans_dir` key falls back to the conventional default silently. The sibling resolver in `scripts/check_plan_origins_closed.py` warns on the missing key (`<facts_key> missing from facts; falling back to <default>`), so the two near-duplicate resolvers have drifted warn semantics while presenting the same documented contract.

## Expected

The two resolvers agree on one warn semantics and the docstring matches the code: either both warn on a missing facts key (aligning `check_backlog_claimed.py` to the sibling's behavior and keeping the docstring), or both stay silent on a missing key and only warn on present-but-blank (fixing the docstring instead). The choice must not change any exit code: warnings stay exit-code-neutral in both scripts.

## Direction

Consolidate the resolution logic into one shared helper (or mechanically mirror the chosen semantics into both scripts) so the warn behavior cannot drift again; add unit coverage asserting the exact warning behavior for the missing-key, blank-value, and absent-facts-file cases in both scripts.

## Evidence

- Code review r1 F8 (docs/reviews/2026-09-24-p51-plans-authoring-surface-hygiene-code-review-r1.md), lens: design; triaged valid non-blocking, routed to backlog per the r1 triage.
- `scripts/check_backlog_claimed.py` `resolve_plans_dir` docstring vs the `if not raw or not raw.strip(): if raw is not None:` warning guard (observed 2026-09-24).
- `scripts/check_plan_origins_closed.py` warns on the missing key via its `_warn` helper (observed 2026-09-24).
