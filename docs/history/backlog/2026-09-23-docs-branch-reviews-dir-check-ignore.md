# docs-branch: reviews_dir not added when check-ignore rejects the directory path

Status: open
Priority: high

## Skill / step

`docs-branch` Step 2 (`SHADOW_PATHS` build from `SHADOW_CANDIDATES`)

## Observed vs expected

- **Observed:** `git check-ignore -q docs/history/reviews` (and `reviews/`) returns non-zero when `.gitignore` lists `docs/history/reviews/` as a directory rule that matches descendants but not the directory path itself. The reviews root is therefore omitted from `SHADOW_PATHS`, so new staging docs under `{reviews_dir}` are never overlaid onto the orphan `docs` branch.
- **Expected:** `{reviews_dir}` from facts is always a shadow root when it exists on disk and its contents are gitignored; review staging files sync on every docs-branch run.

## Reproduction (scrubbed)

1. Repo with `.gitignore` rule `docs/history/reviews/` and live files under that tree.
2. Run docs-branch Step 2.
3. `git ls-tree -r refs/heads/docs -- docs/history/reviews/` lacks the session's new `*-rN.md` until a manual force-add worktree commit.

## Environment

- Date: 2026-09-23
- Runtime: agent done Step 2 after execute-plan review-iteration finalize
- Vendored skill: `~/.agents/skills/docs-branch/SKILL.md`

## Suspected root area

Shadow-candidate inclusion gates on `git check-ignore -q` of the **directory path**. Directory-only gitignore patterns that match children fail that probe. Fix: probe an ignored descendant, or treat facts `{reviews_dir}` as an explicit preservation root when any child is ignored.
