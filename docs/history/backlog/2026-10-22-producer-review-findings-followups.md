# Producer review follow-ups from the exec-review-records-at-round-close r1 panel

Added: 2026-10-22, execute-plan Phase 3 r1 fresh-adversarial panel over the branch delta (plan exec-review-records-at-round-close); valid non-blocking findings folded forward as durable backlog capture.

Driving force: maintainability and test-surface completeness for `scripts/produce_exec_review_record.py` and its skill-text consumers; none of these block the plan's Outcome (all fail safe at the validator's hard-mode arbitration).

Findings carried (each with its r1 pattern id):
- testing#self-heal-fallback-arms-untested: the round >= 2 no-valid-prior `unknown` fallback and the ambiguous-prior refusal have no test arms; one test per arm locks the fallback grammar.
- simplification#lens-table-literal-duplication: the five worker/lens literals are hardcoded in two parallel tables (Markdown panel rows and sidecar panel rows) while `vrs.REQUIRED_PANEL_LENSES` is already imported three lines away; single-home the association in one producer constant.
- simplification#validator-gate-preflight-duplication: the small pre-write pre-flights (identity-qualified slug tail, kebab shape, clean+last-fix freshness precondition, and the clean+prior-filter-yes inconsistency) re-encode validator gates locally; they buy earlier errors and fail safe, and should ride the same seam work as `docs/history/backlog/2026-10-22-producer-self-heal-chain-grammar-dedup.md`.
- simplification#flag-surface-wider-than-truth: `--review-mode` accepts all three validator modes and a free `--review-type`, but the builder renders exactly one panel truth (full five-worker, `Plan Review` title); narrow the modes to what the fixed shape truthfully renders or refuse non-full-panel modes with a named tool error, and drop `--review-type`.
- simplification#verdict-field-ordering-coupling: `ctx["verdict_field"]` is set as a side effect of `build_markdown` and read by `build_payload`; compute it in `build_context` so both builders are pure readers.

Suggested fix: one test-only change (first bullet) and one small refactor change (remaining bullets) when the producer is next touched; the pre-flight bullets fold into the chain-grammar seam row's scope.

Rejected: folding in-run (the r1 fix batch was already scoped to the blocking finding plus cheap hardening; these are non-blocking and the plan's anti-growth constraints favor landing the plan without scope creep); suppressing the lens findings instead of filing (the staging record is gitignored, so an uncaptured valid finding is lost work).

## r2 additions

Added: 2026-10-22, the r2 focused post-fix panel over the fix commit 30bdcada8f (the four workers owning accepted r1 findings re-probed the folded tree; design-simplicity was skipped because its r1 findings all ride backlog rows). All findings non-blocking; carried here as durable capture, same rationale as the r1 list.

Findings carried (each with its r2 pattern id):
- implementation#plan-repo-test-claims: three Task 3 REPOSITORY_TEST rows in `docs/history/plans/2026-10-20-exec-review-records-at-round-close.md` name workflow-test evidence that pre-existing guard suites (the receipt digest arms of `scripts/test_reverse_squash_guard.py`, and `scripts/test_land_squash.py`) plus agent-behavior prose duties already satisfy; no new tests exist for those rows and none are possible for the prose duties. When the plan is next touched, re-scope those rows' evidence claims to the actual carriers.
- documentation#minter-example-selector: the Step 3.5 minter example names the Phase 2 progress-tick re-bind round, whose records are selector-emitted rather than minted on demand; add a selector-precedence qualifier when the seam row is next touched.
- security#exec-token-naming: the Step 3.5 family contrast keys on the `-code-review` token, but the sharper differentiator is the `-exec` token the producer can never emit; name it in the same seam touch as the selector qualifier.
- security#item8-no-outcome-line: the Step 3.1 item 8 carve-out names `tool_error` and `indeterminate` outcomes but not a validator crash that prints no final `OUTCOME` line at all; extend the carve-out with the no-final-line shape (the producer's `final_outcome` already models it as None).
- testing#usage-arm-untested: the argparse override's usage arm (exit 3 with a final `OUTCOME: tool_error` line on stderr, `--help` excepted) has no test pin; pin one usage-error invocation end to end.
- testing#tool-error-arms-not-exhaustive: the r1 pins cover three tool_error arms (malformed findings JSON, missing plan file, clean round with a last-fix commit); the remaining `ProducerToolError` raise sites (plan mismatch, review mode and round checks, date validation, write failures) are unpinned.
- quality#validator-toolerror-conflation: the producer maps a validator run that ends `OUTCOME: tool_error` to its own fail refusal (exit 1), one disposition class off; map that final line to the producer's exit-3 arm in `validate_generated_pair`.

Correction to the r1 capture above (testing#backlog-row-accuracy): the r1 pre-flight bullet lists a "clean+prior-filter-yes inconsistency" among the small pre-write pre-flights in `build_context`. No such pre-write check exists in `build_context`: it validates `--prior-findings-filter` for the yes/no vocabulary only, and the clean+prior-filter-yes contradiction is gated only downstream, by the validator on the generated pair (which deletes both halves on refusal). Executors should not hunt for a pre-write check; treat that one clause of the bullet as validator-owned grammar, and fold it into `docs/history/backlog/2026-10-22-producer-self-heal-chain-grammar-dedup.md`'s seam scope as validator-side. The clean+last-fix precondition named by the same bullet is real and does refuse pre-write.
