# Backlog: doc-registry validator CLI declared-delta registry precision

Status: open
Origin: code review r6 of 2026-09-09-doc-registry-freeze-move-licensing-fold (docs/reviews/2026-09-13-2026-09-09-doc-registry-freeze-move-licensing-fold-code-review-r6.md, findings F1-F3, all Low non-blocking)

- scripts/doc_registry_validator.py `_build_parser` docstring: declare the empty `--root=` value delta (behaves as no `--root`, repo-root search fallback; fail-neutral) or reject empty values with the flag-like check.
- Same docstring: make explicit that `--stdin` before `--selftest` suppresses the selftest short-circuit (exit 0 -> exit 2 consequence of the left-to-right pre-scan).
- `_run_selftest_checks` CLI fixture block NOTE: soften the "failures are loud" claim (a reorder can silently rebind `root` to another valid fixture dir; bind a local fixture root if a root-sensitive pin is ever added).
