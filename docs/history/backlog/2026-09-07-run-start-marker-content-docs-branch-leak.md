# Backlog: run-start marker content leaks absolute path + PID onto the docs branch

- **Origin:** wording-trio execute-plan Phase 3 review r1, finding F4 (risk worker, security#absolute-path-leakage-via-tmp-markers), 2026-09-07
- **File:** agents/skills/done/SKILL.md (Step 0 content-bearing marker line) interplaying with agents/skills/docs-branch/SKILL.md shadow sync
- **Status:** open
Priority: deferred (efficiency/token/simplicity triage 2026-09-11: process-cosmetic or archived-record value only; revisit only if it starts costing real review rounds or tokens)


The content-bearing run-start marker line records the absolute repo root and the writing shell PID. Live `run-start-*` markers survive the done Step 2.62 sweep (it never removes the newest previous-run marker), and docs-branch shadow-syncs `{tmp_dir}` onto the local `docs` branch (verified tracking markers on `refs/heads/docs`). The docs branch is local-only today, but the repo is public and its guidelines forbid machine-specific absolute paths; any future `git push docs` publishes `/Users/...` paths and PIDs.

Remedy options (from review r1 F4):
1. Record a non-reversible identity instead of the raw path (e.g. sha256 of `$REPO_TOP`) (content-match compares the hash of this repo's root against the recorded hash). Requires rewording the SKILL.md confirmation clauses and their validation pins.
2. Exclude `done-session/run-start-*` markers from the docs-branch shadow snapshot.

Either is a cross-skill change outside the wording-trio plan's Review Scope; deferred there per the backlog-deferral default.
