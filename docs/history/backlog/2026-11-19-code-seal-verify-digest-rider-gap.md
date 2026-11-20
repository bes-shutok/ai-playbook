# Backlog: code-family seal-correction riders invalidate verify-digest freshness and re-bind refuses seal-path deltas

Cluster: declared-log-path-foreign-unstaged-byte-carry
Cluster: docs/history/backlog/2026-11-20-execute-plan-phase3-digest-scope-description.md
Status: open
Priority: low

Witnessed 2026-11-19 (execute-plan run declared-log-path-foreign-unstaged-byte-carry, landing 30ea172f0): a code-family certification is valid over base...landing, but two post-landing seal-correction riders (re-binding the seal head to the landed commit, then correcting the round-start digest) each moved the reviewed-scope digest, so `review_record_selection.py verify-digest` at the post-rider tip reads the record stale; the sanctioned `re-bind` remedy refuses fail-closed because its record-scope derivation counts the seal file itself as a touched record-scope path (the seal path's "excluded from diff classification" carve-out in the Phase 3 seal duty is not reflected in the re-bind scope derivation).

Trigger: any future run whose landing needs a post-landing seal rider hits the same stale-at-tip reading; the fix is a scope carve-out for the review-certs seal path in the re-bind/verify-digest scope derivation, or a documented stable ordering (all seal edits pre-landing) pinned in the Phase 4 re-pin text.
