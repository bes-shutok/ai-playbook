# Run-start marker writer silently succeeds writing the marker outside docs/tmp/done-session

Captured: 2026-09-28 (source: release-skill-follow-ups done closeout, Step 0 run-start marker)
Status: done (2026-09-30; implemented by the executed p79 done-closeout plan's contract pass, squash main 89fa19b1 ('marker self-check'): the Step 0 recipe now re-parses tmp_dir independently after the write, resolves both the expected done-session root and the written marker's directory through cd-and-pwd (a resolved-path compare, not a match on the unexpanded variable), and on mismatch removes the stray marker and exits 1 naming the resolved path and the expected root. Verified against both Expected bullets on disk this date; closed as a landed-work straggler)
Priority: medium
Workflow: backlog
Class: correctness
Driving force: reliability
Origin class: self-serving
Consumer urgency: Run-start markers anchor the docs-branch sync window and the done session record; a marker written to the wrong directory breaks both silently and surfaces only as an unanchorable sync or a missing session record much later.

## Problem

The done Step 0 marker writer parses a temp-directory setting from the skill recipe and derives the marker path from it. During the release-skill-follow-ups closeout, a parsing typo in the derived path put the marker in the system temp directory (`/var/folders/...`) instead of `docs/tmp/done-session/`. The step exited 0, so the failure was invisible until the written path was inspected by hand; the marker had to be removed and rewritten.

Second instance (2026-09-28 evening, removed by hand): the misderived path was relative (`var/folders/.../T/done-session/`), so the recipe's relative-anchor branch wrote the marker inside the repository at `var/folders/bt/.../T/done-session/run-start-20260928T201221Z`, where it silently persisted after the writing run exited (writer PID verified dead before removal). A marker inside the repo is invisible to the docs-tmp-sweep gates, which glob `docs/tmp/done-session` only, so nothing prunes it and no gate notices; the relative form is strictly worse than the absolute form because the repo itself accumulates the stray directory tree.

## Exact location

`agents/skills/done/SKILL.md`, Step 0 run-start marker recipe (the temp-dir parsing lines and the final marker write).

## Expected

- After writing, the recipe verifies the marker path resolves under the expected `docs/tmp/done-session` root and fails loudly otherwise, rather than exiting 0 on a misderived path.
- The verification uses a prefix/pattern check on the resolved path, not a string match on the unexpanded variable.

## Severity and source reference

Severity: low-medium

Source: release-skill-follow-ups done closeout Step 0, 2026-09-28; capture hygiene: scan-public-hygiene --files pass.

## Why not fixed now

The closeout was running the skill as written, not editing it. Recorded for a skill-recipe hardening pass.

## Dedup probe

Search terms: `run-start marker location`, `marker path parse`. The registry lists `run-start-marker-content-docs-branch-leak` (completed) and the backlog family covers marker content/location conventions, but no item covers a post-write location self-check on the writer recipe.

## Suggested fix

Add a post-write assertion to the Step 0 recipe: resolve the written marker path and confirm it falls under the done-session root; on mismatch, remove the stray file, die with the resolved path in the message, and leave no marker behind.
