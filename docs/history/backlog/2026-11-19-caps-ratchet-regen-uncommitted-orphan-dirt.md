# Backlog: a wholesale caps-table ratchet regeneration sat uncommitted on the primary working tree through four landings, invisible to every gate because stale and regenerated states both pass

- **Filed:** 2026-11-19, operator ask (analyze why the caps changes are not committed; create backlog; investigate; fix)
- **Status:** open (repair landed in-repo same turn; writer-ownership and detection decisions pending)
- **Workflow:** backlog
- **Priority:** low
- **Class:** fix-class
- **Origin class:** witnessed orphan-dirt incident (one incident; an uncommitted working-tree mutation survived four subsequent landings because no gate, test, or closeout step compares the committed caps table against what the ratchet would produce)
- **Skill/step:** the byte-budget gate's ratchet surface (`scripts/skill_text_budget.py --ratchet`) and the primary-checkout write boundary (sessions that mutate tracked files outside their landing scope)
- **Cluster:** docs/history/backlog/2026-10-23-dirt-gate-head-pinned-after-classification-window.md, docs/history/backlog/2026-10-23-dirt-gate-tree-mode-contract-surface-stale.md (same uncommitted-drift defect family; those rows own the run-worktree closeout dirt gate, this row owns the primary working tree, which no closeout ceremony inspects between runs)
- **Cluster:** docs/history/backlog/2026-11-20-learn-corpus-writes-stranded-uncommitted-primary.md (same uncommitted-primary-write family; that row owns the learn-corpus surface, where the writer skipped both sanctioned commit-rule arms, and holds the write-time durability floor arm)

## Problem

Witnessed sequence, all legs on disk:

1. `scripts/skill_text_budget_caps.json` last landed 2026-11-11 (3f8dc5d1f). Ten capped skill files were created or last changed after that date (the learn router split into step files, the self-heal and plan-stack skills, the read-only verification lane, the execute-plan splits, and others), so the committed table carried stale-high caps and 10 caps gaps.
2. On 2026-11-19 at 18:28:53 local (UTC), a wholesale `--ratchet` regeneration was written to the primary working tree: 12 caps lowered onto shrunken files and 10 new entries seeded, every value matching the ratchet formula (current bytes plus the larger of 25% or 8192, clamped to the ceiling, never raised). A fresh `--ratchet` run over the current tree reproduces the file byte-identically ("0 cap(s) lowered, 0 seeded"; the one post-write growth, `agents/skills/self-heal/SKILL.md` +568 bytes at 21:20, stays inside its seeded cap and the ratchet never raises), so the mutation is the ratchet's own faithful output, not hand-editing.
3. The write was never committed. The writing session's window brackets the mtime exactly: commits 0e523a714 and 1c0c9c3b4 at 18:21, then 7a4dd1ae7 and 709cc2cce at 18:40-18:41, all backlog and prompt-log writes from the primary checkout. No captured transcript located (agent sub-transcripts, codex rollout logs) records an actual `--ratchet` invocation in that window (all hits are CLI help-text echoes or advisory-row reports from `--check`); the interactive main-session transcript was not retrievable, so the exact invocation and its intent are not recoverable. The session's committed scope never included the caps file.
4. Four subsequent landings (875e5aaca, 8c5e4590b, da4d9329f, 37fe34ebe, 19:48 through 21:40, all from run worktrees) correctly declined to commit foreign unscoped primary dirt per the unowned-post-boundary rule and each landed around it. The mutation sat until the operator asked about it the same evening.
5. Structural reason nothing detected it: the gate passes with BOTH states. `--check` against the committed stale-high table exits 0 (0 blocking; 10 advisory gap lines, 5 advisory ratchet rows), and `--check` against the regenerated table also exits 0 (0 blocking, 0 gaps). A stale-high table only produces advisory rows, never a blocking failure; the test suite exercises the ratchet on tmp fixtures only; and the run-worktree dirt gate never sees the primary working tree between runs. The drift is benign by construction and therefore untraceable by machinery.

## Suggested direction

- Repair arm (landed with this row): commit the regenerated table as-is after re-verification; it is the ratchet's own current output and the gate passes with it.
- Writer-ownership arm (process, no machinery): a session that runs `--ratchet` commits the regenerated table in the same turn; status or inspection runs use `--check` or `--suite` (both read-only), never `--ratchet`. One-line home: the gate's operational documentation where its modes are described.
- Detection arm (machinery decision, pending): a warning-only drift line comparing the committed caps table against a fresh ratchet run. Admission fields per the machinery admission protocol: the incident is this row; expected catch frequency is low (fires only when a wholesale regen is left uncommitted; first witness 2026-11-19); false-positive cost is an in-flight landing whose commit legitimately includes a fresh regen (the line must be clearable by that landing itself); sunset/review 2027-02-07 aligned with the budget gate's own review date. Keep warning-only; do not promote without a true catch after landing.

## Evidence

- Working-tree mtime of `scripts/skill_text_budget_caps.json` 2026-11-19 18:28:53 local; `git status` showed it as the only modified tracked file through the investigation.
- Caps table's last commit 3f8dc5d1f (2026-11-11 00:34 UTC, "plans: land operative-file-read-budget-gate").
- Fresh-ratchet identity check (2026-11-19): a copy of the dirty table re-run through `--ratchet` against a scratch caps path reports "0 cap(s) lowered, 0 seeded; no cap raised" and diffs identical to the working-tree file.
- `--check` exits 0 with the committed table (10 caps gap lines) and with the regenerated table (0 gap lines), same 0 blocking count in both.
- Session window: reflog commits 0e523a714, 1c0c9c3b4, 7a4dd1ae7, 709cc2cce (18:21:54 through 18:41:45 UTC).
- Landing runs' worktrees kept their own caps copies clean (the day's run worktree caps mtime equals its checkout time), so the write did not come from a landing run; no test writes the real caps path (the suite passes `--caps` tmp fixtures only; the script's only write site is the `--ratchet` branch).
