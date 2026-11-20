# Backlog: eight Python-mkdtemp strays accumulate in the wholesale-ignored audit home with no cleanup owner

- **Filed:** 2026-11-08, operator-directed untracked-residue survey session
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** witnessed defect (playbook repo, primary checkout audit home)
- **Class:** fix-class
- **Driving force:** simplicity
- **Dedup probe:** searched open backlog bodies for `ai-playbook/tmp` (rg over `docs/history/backlog/`); no row owns audit-home scratch residue. The docs/tmp retention family and the drained `2026-10-30-remaining-run-era-tmp-dirs-drain.md` row (deleted per the covered-row rule at landing, prune receipt in EXEC-PROMPTS.md) own(ed) `docs/tmp/` surfaces only; `2026-10-18-runtime-scripts-home-residue.md` owns the deployed scripts home, a different surface.
- **Cluster:** the EXEC-PROMPTS-PRUNE receipt remaining-run-era-tmp-dirs-drain (docs/history/backlog/EXEC-PROMPTS.md; same defect class: run-era scratch the closing boundary leaves behind; the drained row was deleted per the covered-row rule at landing)

## Observed versus expected

Observed: the wholesale-ignored `/.ai-playbook/` audit home carries eight strays: seven empty mode-700 directories named `tmp` plus exactly 8 random characters (`.ai-playbook/tmp0dwh7kiz`, `tmp46dk44d4`, `tmp4y7ntcl0`, `tmpfa5ljgc6`, `tmpjm2bzj5l`, `tmpped3e2sv`, `tmpx5s44_nj`; directory mtimes 2026-11-05 15:54 through 2026-11-07 04:07, the overnight ladder windows) and one 76 KB regular file `.ai-playbook/tmpsubzgkmn` (2026-10-30 19:48). The naming (no separator between `tmp` and the random part) and the mode-700 empty directories are the `tempfile.mkdtemp()` signature with default naming, so a Python runtime step creates scratch under the audit home and its cleanup does not fire on every exit path.

Expected: runtime scratch lives in `{tmp_dir}` (`docs/tmp/`) where the sweep gates can see and drain it, and a mkdtemp caller removes its directory on every exit path; the audit home holds only its named record families (reviews, done-session, metrics, review-certs, friction-audit, maintenance).

## Evidence

- The `/.ai-playbook/` wholesale ignore makes the strays invisible to `git status`, so no baseline, closeout, or survey arm surfaces them; this survey found them by directory listing only.
- Candidate Python callers importing `tempfile` in `scripts/`: `maintenance_fire_outcomes.py` (ladder-adjacent, matching the mtimes' windows; imports tempfile but shows no literal `mkdtemp(` line, so it may call it indirectly or use `mkstemp`), `hooks_probe.py`, `summarize_review_stats.py` (its `mkdtemp` calls all carry explicit `review-metrics-*` prefixes, so it is not the bare-naming caller). The caller whose temp directory resolves under `.ai-playbook/` (direct `dir=` argument, a `TMPDIR` export in a ladder payload, or a cwd-relative default) is identified as the fix's first step, not asserted here.
- The one non-empty stray (76 KB, 2026-10-30 19:48) predates the empty dirs by six days and needs content classification before deletion; if it holds a run record, the recover-manifest recipe applies before removal.
- Creator elimination sweep (2026-11-08 investigation): no bare `mkdtemp()` or `mkstemp()` call exists anywhere in `scripts/`, `agents/`, `projects/`, the deployed `~/.ai-playbook/scripts`, or `~/.ai-playbook/hooks` (every production call carries an explicit prefix or directory; only tests create bare temp roots, under explicit paths); no script or clocked-order payload exports `TMPDIR` pointing at the audit home. The repository-side candidate list in the bullet above resolves to empty: the creator is external to this repository (the runtime layer, Python `tempfile` default naming under a `TMPDIR` resolving at the audit home, unproven).
- Stray-file classification (2026-11-08): `.ai-playbook/tmpsubzgkmn` is JSON - a maintenance-lane authoring-cycle gate state snapshot (`authoring_cycle_gate`, content dated 2026-09-30T19:05+01:00, born 2026-10-30 19:48), stale runtime state, not a run record; the recover-manifest recipe does not apply. Directory birth times: 2026-11-05 15:54:18, 16:28:00, 16:28:53, 16:45:04, 18:10:30, 18:10:46, and 2026-11-07 04:07:02 - the 04:07 birth sits in the 04:00 WET scheduled-carrier window of 2026-11-07.
- Investigation resolution: the row's identification step resolves to "not repo-side", so the fix arm below is the bounded sweep plus an operator-facing runtime-layer report, with the caller search closed at this row's Evidence rather than left open.

## Suggested correction

The identification step is resolved (creator external to the repository, see Evidence): a bounded fix-class arm that classifies (done), deletes the eight strays, appends the census-and-classification receipt to this row, and reports the runtime-layer creator suspicion to the operator for a runtime-side watch. No tracked surface changes; no gate; the audit home gains no new standing sweep surface from this row (if such an arm is wanted, it goes through the machinery admission protocol with its own incident).
