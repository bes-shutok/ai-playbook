# Backlog: claim-fence test coverage gaps (from Step 1.2b, live-claim-plan-deletion-fence)

- **Filed:** 2026-10-06, the Step 1.2b intermediate review of the live-claim-plan-deletion-fence execution
- **Status:** open
- **Workflow:** backlog
- **Priority:** low

Driving force: reliability (the guard's central resolution rules ship correct but unpinned; a future refactor could silently break the witnessed topology the fence exists to protect, and the suite would stay green).

- F1: add a fixture creating a linked worktree, writing the claim only under the primary checkout, scanning with --repo = the linked worktree, expecting the refusal (kills the `return root` mutant in claim_fence_primary_checkout).
- F2: one fixture seeding a facts file resolving a non-default plans home/tmp dir, expecting the fence to key on the resolved paths (kills the delete-the-facts-arm mutant).
- F3: one test invoking check-claim-fence with no --base, expecting exit 3 and OUTCOME: tool_error.
- F4: sharpen test_claim_fence_ack_wrong_path_refuses to an ack value embedding the deleted path as a strict superstring so exact-equality and substring matching diverge.
- CF2: dedupe refusal blocks by deleted path (or skip first-parent re-attribution for merges whose second-parent side owns the deletion) for merge-containing ranges.

- CF2-CANDIDATE (re-review pass 2): harden the absolute-value containment check against mixed symlink flavors (facts value unresolved /var flavor vs resolved /private/var toplevel) by containment-checking realpath'd pairs on both sides.

Task 2 captures (Step 1.2b):
- F1/T2-5: add REVERSE_SQUASH_GUARD_SCRIPT to sweep_env's delenv list (fixture hermeticity parity with the seven sibling overrides).
- F2: converge the battery's absent-script posture (review-staging rc 1 named deployment gap vs this gate's rc 3) or name the rc-3 arm in the done enumeration prose.
- **Cluster:** docs/history/backlog/2026-10-07-claim-fence-stem-case-drift.md; docs/history/plans/completed/2026-10-10-coordination-single-writer-ttl.md; docs/history/backlog/2026-10-07-execution-claims-dir-resolution-drift.md
- F3: append the scanned range target to the contradiction arm's message, matching the sibling indeterminate arm's "target {base}..HEAD" shape.
- T2-1: fixture with the plans tree gone at HEAD and base (and one with the dir absent pre-run), asserting the named warning skip; also assert the keep-scan nuance (own commit emptied the plans root keeps its scan).
- T2-2: fixture for the no-manifest skip arm asserting the named reason.
- T2-3: parametrized test over stub guard scripts covering gate-level child exit 2, exit 3, missing final OUTCOME line, label/exit contradiction (rc 2), and script-absent routing.
- T2-4: parser edge test with a two-block child stdout (multi-block claim-to-header association, header-without-claim-line, zero-parsable-blocks fail-closed), direct unit call on _claim_fence_refusal_blocks.

Review r1 backlog-routed Lows (staging doc docs/reviews/2026-10-05-live-claim-plan-deletion-fence-code-review-r1.md):

- correctness#plans-home-skip-masks-unreadable-window: a range-enumeration (rev-list) failure combined with an absent plans home collapses into the absent-home warning skip; remedy: make the skip arm consume the range-read result so an unreadable window classifies tool error or indeterminate, never the skip.
- correctness#facts-resolved-home-drops-backlog-root (merged with risk#facts-resolution-narrows-protected-roots): a facts-resolved plans_dir replaces the guard's dual hard-coded roots, dropping the backlog root from the fence; remedy: keep the backlog root fenced when facts resolve a single plans home (union with the hard-coded backlog root) and pin with a fixture.
- risk#conservative-fallback-misroutes-foreign-as-own: an unreadable owned-commits ledger over-includes rows as own deletions; remedy: name the conservative over-inclusion posture in the gate docstring (reported, never silently owned).
- risk#ack-sanction-lost-at-squash-aggregation: a Plans-Deletion-Ack trailer on a rider is lost when the landing squashes the branch; remedy: add a landing-sentence clause requiring the ack trailer restated on the landing (squash) commit.
- risk#non-ascii-path-owned-row-mismatch: text-mode diff-tree quoting mismatches owned rows for non-ASCII paths; remedy: make the owned-row comparison quoting-safe (byte-mode or quote-normalized) in the foreign-commit classifier.
- testing#gate-pass-arm-undrilled: remedy: fixture drilling the gate pass arm (child exit 0) asserting the sanction lines reach the gate message.
- testing#archive-twin-add-shape-unpinned: remedy: fixture pinning the same-commit archive-twin sanction (A/R/C record whose post-side path sits under a completed archive with the deleted basename).
- testing#ack-position-grammar-unpinned: remedy: fixture pinning the ack-trailer match grammar (any message line carrying the exact-path trailer matches; a different-path trailer never sanctions).
- testing#backlog-root-fence-unpinned: remedy: fixture pinning a backlog-root deletion refusing while a live claim names it.
- testing#facts-escape-fallback-unpinned: remedy: fixture pinning the facts-value fallback (a value degenerating to or escaping the scanned root falls back to the hard-coded defaults).
- testing#primary-checkout-toolerror-unpinned: remedy: fixture pinning the primary-checkout resolution failure class (failed or empty worktree listing classifies tool error).
- testing#guard-multiblock-emission-unpinned: remedy: fixture pinning the guard's multi-block emission (two protected deletions in one range, both refusal blocks printed).

Note: risk#stem-grammar-cross-date-collision was staged informational (deliberate tradeoff with a recorded basis), not backlog-routed.
- **Cluster:** docs/history/backlog/2026-10-07-execution-claims-dir-resolution-drift.md; docs/history/backlog/landing 5865a50a5, carried into current history by rewrite commit f3894756d
