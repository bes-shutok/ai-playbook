# Review-staging scaffold: simplification residuals from the execution review

- Date: 2026-10-22
- Driving force: simplification
- Status: open
- Source: execution review r1 of the plan `docs/history/plans/2026-10-19-review-staging-schema-scaffold-and-validation-reuse.md` (overflow findings 7, 9, 10 of `.ai-playbook/reviews/2026-10-22-review-staging-schema-scaffold-and-validation-reuse-code-review-r1.md`)
- Files: `scripts/validate_review_staging.py`

## Observed

Three behavior-neutral shrink candidates on the just-landed descriptor and scaffold surface, deferred from the landing run because each touches a surface the same run introduced and they are better taken together:

1. The per-field `gate` legend in `V1_SCHEMA_DESCRIPTOR` is a dispatch dimension where only `"v1"` is read by code (the two `gate == "v1"` loops); the container guard keys on `type is dict`, and the other six values name owners already stated in the legend prose. Keep the dispatched marker only and name owners once.
2. The second module-global telemetry guard (`_scaffold_telemetry_suppressed`) plus its save/reset/restore in `main()` and the selftest's prior-flag bookkeeping could be a `_main` return marker, removing the process-global state lesson 174 polices (tradeoff: a scaffold that dies mid-print would then record telemetry).
3. The two embedded selftest families (`_selftest_schema_descriptor_scaffold`, `_selftest_scaffold_mode`) duplicate five builder-output pin groups (extensions shape, soften present, coverage keys, source_digest non-hex, triage label); single-home them.

Related: the convergence example and its `extensions` label hand-copy the self-heal gate's key path and status vocabulary (three unsynchronized copies in one file; the strict direction is battery-caught, the relax direction is not) -- extract a shared `SELF_HEAL_STATE_STATUSES` constant or fold the coupling into this row's fix.
Related: the descriptor's `conditional` section declares per-field specs (`coverage`, `record_kind`) that no gate reads -- the section is consumed only as a key set; mutating their `enum`/`type` values changes no output (staged finding r3, the dead-key trap lesson 173 names) -- fold into item 1's legend shrink or strip the unread spec values.
Related: the `_scaffold_telemetry_suppressed` save/clear/restore protocol is a read-modify-write on a module global, lossy under two in-process `main()` calls on different threads (no current caller does; telemetry accuracy only) -- the call-scoped rewrite in item 2 or a module lock closes it.
Related: the builder walks only the required and extended descriptor sections and hand-wires `record_kind`, `extensions`, and `coverage`, and the `date_conditioned` label hardcodes the extended field list; deriving both from the descriptor closes a drift class (staged finding 8 of the same record, deferred here).

## Expected

One change that lands all four, keeps the 751-check battery green and the `--scaffold` envelope byte-stable except where the legend prose moves, and deletes more bytes than it adds (the review estimated roughly 65 lines net).
