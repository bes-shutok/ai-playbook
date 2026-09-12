# Backlog: token-usage-telemetry r5 residuals

Status: open
Priority: deferred (efficiency/token/simplicity triage 2026-09-11: process-cosmetic or archived-record value only; revisit only if it starts costing real review rounds or tokens)

Workflow: backlog
Source: docs/reviews/2026-09-07-2026-09-06-token-usage-telemetry-code-review-r5.md (three Low, non-blocking findings; deferred at the 5-round cap per the backlog-deferral default; folding them would mutate the digest past the round budget)
Severity: Low
Scope: scripts/review_usage_capture.py, scripts/summarize_review_stats.py

## Items

1. `review_usage_capture#cwd_less_first_meta_silent_drop`: a rollout file whose FIRST parseable `session_meta` carries no `cwd` is silently dropped (cwd_ok False → break) even when a later meta names the matching repo cwd; the drop is invisible (no stderr diagnostic, unlike other adapter failure paths) and undocumented (the docstring covers missing-`session_id` but not missing-`cwd`). Fix: either treat a cwd-less first meta as identity-undecided (scan later metas for cwd only, keeping the first meta's sid) or document the accepted drop in the accepted-limitations paragraph plus a pinning selftest witness.

2. `summarize_review_stats#garbage_string_totals_counts_in_numerator`: a `usage.totals` dict whose values are garbage strings passes the `isinstance(totals, dict)` gate and `_coerce_int` maps them to 0, so the sidecar counts in the coverage numerator ("has usage") while contributing zero tokens, contradicting the "malformed → treated as absent" seam claim. Fix: require all six keys to coerce to non-None ints, else return None (treated absent).

3. `review_usage_capture#abbreviate_home_sibling_prefix`: `_abbreviate_home_str` uses plain `s.replace(str(home), "~")`, so a sibling path like `/Users/<name>2/...` appearing in an exception message mangles to `~/2/...`. Cosmetic diagnostic-only mangling, no leakage. Fix: match the home path only at string start or after a path separator.

## Dismissed at triage (record only)

- SKILL.md "available once the repo commit lands" phrasing: operationally true on this host (symlink wired 2026-09-07); a fresh machine needs runtime bootstrap; acceptable for this repo's single-operator model.
