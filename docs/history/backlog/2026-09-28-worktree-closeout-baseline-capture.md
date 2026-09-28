# Backlog: ad-hoc worktree runs must capture the closeout baseline at Phase 0

Captured: 2026-09-28 (source: codex-worker-terminal-recovery exec landing)
Status: open
Priority: low

Workflow: backlog

## What was witnessed

The execute-plan skill's Phase 0 recipe captures a closeout baseline (`worktree_closeout_migrate.py capture`) so the end-of-run migration can move exactly what the run added. The 2026-09-28 codex-worker-terminal-recovery exec run skipped that capture; at closeout `migrate` refused to run without a baseline (implicit-empty-baseline guard), and the run fell back to an explicitly scoped staging-doc copy per the operator payload - workable but unverified against the full artifact set, and a full-dir sweep would have wrongly carried done-session markers into the primary checkout's session window.

## Suggested fix

Enforce the baseline capture in the ad-hoc-worktree path (execute-plan Phase 0 or the worktree bootstrap recipe): a run that cannot produce `closeout-baseline.json` records the skip and the closeout degrades to scoped copies with an explicit artifact list recorded in the session manifest.

## Acceptance

- An ad-hoc worktree run either has the baseline file at closeout or a recorded skip note naming the scoped-copy fallback and its artifact list.

## Witness append (2026-09-29, em-dash gate mode-selection run)

Same skill and step family (execute-plan Phase 0 capture recipe), second failure mode: the recipe at `agents/skills/execute-plan/SKILL.md` shows the capture as `--dirs "{reviews_dir}" "{tmp_dir}"` (two separate quoted arguments), but `worktree_closeout_migrate.py` declares `--dirs` as a single string consumed by a whitespace-splitting helper (`_configured_dirs` does `raw.split()`), so the recipe's two-argument shape is rejected at parse time and the baseline capture cannot succeed with it. The single quoted space-separated form `--dirs "<dir-a> <dir-b>"` works and is what this run used. Remediation should fix the recipe text (or widen the parser) together with this item's Phase 0 enforcement; recorded as project lesson 8 in `docs/maintenance/development_lessons.md`.
