# Backlog: PLAN-PROMPTS carries a landed entry's headless body that now reads as the tail of the next-authored entry

- **Filed:** 2026-11-07, learn Step 1.9 over the closeout-migrate-stale-landing-sha-comment authoring session
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed defect (rolling log content, two landing riders and one bare index commit)
- **Class:** fix-class
- **Surface:** `docs/history/backlog/PLAN-PROMPTS.md` (the entry region between `## rolling-log-write-residue-recovery-recipe` and the next heading); the log's `Prune rule` range procedure
- **Dedup probe:** searched open backlog bodies for `headless`, `orphan`, `resurrect`, `receipt`, and `end anchor`; the completed `docs/history/backlog/completed/2026-10-15-plan-prompts-prune-end-anchor-overreach.md` owns the prune range procedure (its 2026-10-19 witness was a receipt line at the range tail; this witness is the next entry's heading line), `docs/history/backlog/2026-11-07-learn-commit-pathspec-ambiguity.md` owns the bare index commit that resurrected the entry, and `docs/history/backlog/2026-11-07-rolling-log-freeze-foreign-bytes-setaside-recipe.md` owns residue recovery before a log write; none owns cleaning this committed orphan or restoring its lost receipt
- **Cluster:** docs/history/backlog/2026-11-07-learn-commit-pathspec-ambiguity.md (same foreign-staged-sweep family; that row owns learn's commit wording, whose witnessed sweep resurrected this entry; this row owns the committed residue it left)

## Observed versus expected

Observed: the read-budget plan landing `347f835a2` pruned its own `operative-file-read-budget-gate` entry and wrote its `PLAN-PROMPTS-PRUNE:` receipt. The bare index commit `96b615c65` then recommitted the entry (heading and body) from a stale staged snapshot and dropped the receipt. The execute-plan-project-test-policy-scope landing `1f5123f6a` pruned its own entry and deleted the following `## operative-file-read-budget-gate` heading line as the tail of its range, leaving that entry's body headless; the `Prune rule` already requires reading through the actual next heading, so the procedure bounded the range but still consumed the anchor line. Consequences witnessed 2026-11-07: an authoring walk read the orphan body as the top entry and picked the already-landed plan (corrected before any claim); the investigate commit `dc812e6b9` inserted `## rolling-log-write-residue-recovery-recipe` directly above the orphan, so the orphan now reads as that entry's tail (a second `Added:`, `Origins:`, and `Prompt:` set) while a live authoring claim targets that entry; HEAD carries no receipt for `operative-file-read-budget-gate`.

Expected: the orphan body is gone and the lost receipt is restored, and a prune range ends before the next heading line, never on it.

## Evidence

- Per-commit trace of `docs/history/backlog/PLAN-PROMPTS.md` (heading, body, receipt counts for the read-budget entry): `347f835a2` 0/0/1; `96b615c65` 1/1/0; `72aa49465` and `5a1a9a69b` 1/1/0; `1f5123f6a` 0/1/0; every later commit through `073b2b23e` 0/1/0.
- `git show 1f5123f6a -- docs/history/backlog/PLAN-PROMPTS.md`: the removed span runs from `-## execute-plan-project-test-policy-scope` through `-## operative-file-read-budget-gate`, with the latter's body left in place.
- The lost receipt text survives at `git show 347f835a2:docs/history/backlog/PLAN-PROMPTS.md` (the `PLAN-PROMPTS-PRUNE: operative-file-read-budget-gate -> docs/history/plans/2026-11-07-operative-file-read-budget-gate.md ...` line).
- Related observation, same day (land-worktree working-tree composition, owned by the covered `docs/history/backlog/2026-11-04-land-worktree-staged-primary-desync.md`): the archive-rider landing `073b2b23e` committed a peer's uncommitted `## maintenance-d17-false-terminal-stop` emission with no blank line before its heading and left the primary index at the pre-landing snapshot.

## Suggested correction

One targeted log commit under the `Write boundary rule`: remove the orphan span (from the second `Added: 2026-11-07, investigate over the 2026-11-07 24h harvest's skills-corpus row` line through its `Prompt: Author a plan that lands the read-budget discipline ...` line) and restore the `347f835a2` receipt line in the receipt region. While `## rolling-log-write-residue-recovery-recipe` carries a live authoring claim, the `Freeze rule` holds that section: either wait for the claim to clear, or let that entry's own landing prune remove the orphan under the `Coverage and removal rule` (the orphan's origin is plan-covered) and restore only the receipt. No new gate; the prune-tail witness is recorded here for the completed end-anchor family, and a checker arm stays rejected until a further witness.
