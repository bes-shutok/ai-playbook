# Backlog: clause-pointer r2 residual improvements

Driving force: code-quality
Created: 2026-10-31 (hard-mode-clause-pointer-residuals r2 review; all findings non-blocking, deferred at the clean exit)
Cluster: docs/history/backlog/2026-10-31-witness-ledger-pointer-marker-case-dead.md
Cluster: docs/history/backlog/2026-10-31-clause-pointer-residual-under-routing-families.md

Residuals from the r2 fresh-adversarial panel over the hard-mode clause-pointer landing, each probe-verified by its reporting lens:

- source_digest family under-fire: `version-1 sidecar missing required top-level field 'source_digest'` and its JSON-null twin contain the marker only inside template quotes, so the quote-position anchor skips the sole occurrence and both route bare while six sibling source_digest emits carry the pointer. Candidate fix: leader row `("required top-level field", "Version-1 sidecar contract")` ahead of the `source_digest` row plus a byte-real pin (covers the whole missing/null family without reopening the C3 window).
- The residual under-routing row's capture-all sweep missed the required-top-level-field family and the full-panel composition siblings (`full panel: missing required base worker`, `missing required lenses`, `appears 2 times`); extend that row or drop its capture-all framing.
- Set-equality failure diagnostic is one-directional: `unpinned table markers: []` renders while failing on a stale pin, duplicate pin, or duplicate table row; render both set differences plus the counts pair.
- The severity/blocking/triage bullet-parity sub-family has no routing pin; a synced re-widening of a leader row would reintroduce the r1 F3 misroute class green. Candidate: routing-neutral `("severity disagrees", "Staged Markdown hierarchy (required)")` row plus pin.
- `_skill_clause_pointer` docstring's exemption clause reads naturally as "exempt markers are skipped" (inverted); the side comment omits the message-start (idx == 0) case.
- Plan prose (Gist After, Task 2 bullet) records the per-marker-shape mechanism that did not land; reword to the quote-position contract in the completion pass.
- Task 2's demonstration bullet (C3 refused, wrong-section remap failing, demonstrated-red guard) needs its evidence filed beside the ticked bullet before landing.
- The new import-based live-count herestring in check_maintenance_pins.sh runs `python3 -` from the invocation cwd, so stdlib-named modules planted in cwd shadow the validator import chain; harden with `-P`/`-I` or spec_from_file_location.

Source: 2026-10-31 r2 review panel (correctness-completeness, testing, design-simplicity, contract-docs, risk).
