# Backlog: r2 code-review residuals (merge-landing-lock-grouping)

Priority: medium
Urgency remark: witnessed: classification and labeling edges in live merge-lock code
Promoted: 2026-09-26 from docs/history/backlog/deferred/ under the direction triage (source class: self-serving witnessed defect)

- Status: rejected (2026-09-27; review-round polish: hypothetical misclassification windows, cosmetic labels, speculative watchdog edges; no witnessed failure)
- Origin: Phase 3 r2 focused review; verdict blocking on two findings (both fixed in 567451c1); these residuals valid-but-deferred
- Driving force: each item is a small semantic refinement whose absence does not break the landed guarantees but leaves a wrong-in-principle classification or an untested regression path.

## Items

1. (risk F5) Meta-less lock dirs younger than MERGE_LOCK_INCOMPLETE_SECS are misclassified as stale crash evidence by G3b during the ms-wide mid-acquire window; have merge-status print the lock dir's mtime age when meta is missing and classify young meta-less holds as fresh defers.
2. (correctness F2) separate-git-dir repos whose gitdir is literally named `.git` key the merge lock to the gitdir parent (cosmetic labeling; keying stays exclusive); document or scope the `*/.git` strip.
3. (correctness F4) In the authoring temp-index arm, a last-instant re-check mismatch strands even though update-ref is checkout-independent; consider re-running the arm decision instead of stranding.
4. (testing F15b) M9 has no watchdog: a wait loop that ignores --max-wait hangs the selftest instead of failing; add a sleep-based watchdog around the M9 waiter.
