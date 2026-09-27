- Status: open
Priority: medium
Urgency remark: six valid non-blocking findings from the release-skill Phase 3 review r2 (fresh blocking-clean round deferred under the review-convergence directive); findings 1-2 are Medium
- Workflow: backlog
- Priority: Medium
- Created: 2026-09-27

# Release skill: deferred code-review findings (r2, 2026-09-27)

Source: docs/reviews/2026-09-27-release-skill-code-review-r2.md over scripts/release-rewrite.sh, scripts/release-authoring.sh, agents/skills/release/SKILL.md, scripts/test_release_skill_selftest.py.

1. (Medium) Authoring run dir is never torn down and is reported as a leftover by the rewrite inventory of the very same run; SKILL.md summary item 6 over-claims cleanup. Fix: tear the authoring dir down in the rewrite trap (the groups file is consumed at startup) or have the authoring step clean it via the Step 3 wrapper.
2. (Medium, dormant on this repo) Legal delta shapes hard-abort: tracked `*.lock` paths hit an unconditional die arm in release-rewrite.sh materialization (no functional need; write target is outside the repo), and gitlink/submodule paths fail `git show` (128) instead of a mode-160000 skip note. Zero such paths in the current delta; landmine for other repos.
3. (Low) Post-swap snapshot hash covers untracked entries, so a stray untracked file between Steps 2 and 3 fails the push re-assertion and forces a full re-release. Consider hashing tracked+untracked-modified only (prescribed design today).
4. (Low) A missing check-no-em-dash.sh is misdiagnosed as an em-dash policy hit (exit 127 swallowed by the `if !` gate); the checker path is hardcoded while scanner/lock have Configuration keys.
5. (Low) Replace-mode detection keys on any delta commit adding the exact `## <today>` line, not just release-lineage notes commits; a user-authored same-day section is replaced in place (recoverable via the backup ref).
6. (Low) Selftest lacks a case for the authoring step-7 whole-file-rescan restore branch (the script's only destructive restore).

Origin: docs/history/plans/2026-09-26-release-skill.md execution run 2026-09-27.
