# Backlog: (covered)

Covered by plan 2026-10-23-ignored-audit-home-tracked-index-fence (executed 2026-10-24; landing the witness).

# Backlog: ignored audit-home paths can be force-tracked and ride both landing paths onto main

- **Filed:** 2026-10-20, interactive session, after the operator saw a tracked `.ai-playbook/review-certs/` modification in `git status`
- **Status:** covered (docs/history/plans/2026-10-23-ignored-audit-home-tracked-index-fence.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** operator-witnessed
- **Class:** defect (a repo-wide exclusion policy has no complement at the commit and landing boundary)
- **Driving force:** correctness
- **Skill/step:** `agents/skills/plans/SKILL.md` round-close seal duty (the "local seal file" sentence); the maintenance authoring closeout's residue-landing step (`agents/skills/maintenance/template-authoring.md`); `scripts/land_squash.sh` `land-worktree` composition (line 739, `update-index --add --remove`); `scripts/done_sweep_gates_lib.py` `_ignored_paths` and `scripts/done_run.sh` line 697 (untracked-only ignored arms)
- **Severity/source:** two force-tracked seals reached `main` in f5a8142ed and 4399aee99 (the 2026-10-20 01:34 user-directed authoring carrier, picks 1 and 2 of the same fire); detected manually about eleven hours later; untracked by 839984ac2 with the disk copies kept
- **Capture hygiene:** repo-relative paths only; no personal or machine-specific data.
- **Dedup probe:** searched open backlog filenames and text for `gitignore`, `ignored`, `force-add`, `add -f`, `exclude-standard`, `docs branch`, `retention`. Nearest rows: the docs-branch runner test rows (`docs/history/backlog/2026-10-09-docs-branch-step2-selector-test.md`, `docs/history/backlog/2026-10-09-docs-branch-witness-contract-and-recovery-test.md`) and the missing-records row (`docs/history/backlog/2026-10-07-archived-plan-review-records-missing.md`); none covers the tracked-index pollution class, so this row is a single-origin group.

## Problem

`/.ai-playbook/` is wholesale-ignored (`.gitignore`, since b5f1185c8 on 2026-06-13); the ignore comment and the hard rule "Skill audit artifacts" in `docs/AGENTS.md` make it the one canonical, already-ignored home for review records, certification seals, and metrics, with the retention copy on the docs branch, and `agents/skills/plans/SKILL.md` calls the seal a "local seal file". On disk 138 seal files live there; before the fix exactly two were tracked, both landed by one carrier fire:

- pick 1 (f5a8142ed) committed `.ai-playbook/review-certs/done-cached-diff-authorized-reversal.md` directly on `main` beside its PLAN-PROMPTS prune receipt. An ignored untracked path enters the index only through a forcing step (`git add -f`, or an `update-index --add` that never consults ignore rules), so the residue-landing step forced it, most plausibly by answering git's "use -f if you really want to add them" refusal hint literally.
- pick 2 (4399aee99) tracked `.ai-playbook/review-certs/gate-removal-closeout-accounting.md` on the authoring worktree branch, and `scripts/land_squash.sh` `land-worktree` reproduced the branch tree on `main`: its composition seeds a temp index from the base tip and indexes the branch's changed paths with `git update-index --add --remove --stdin` (line 739), a primitive that ignores `.gitignore` by design, then proves tree equality against the branch tip, which faithfully preserves the defect.

Nothing detects a tracked ignored path on either path. `scripts/done_sweep_gates_lib.py` `_ignored_paths` and `scripts/done_run.sh` line 697 enumerate untracked ignored files (`ls-files --others --ignored --exclude-standard`), never tracked ones (`git ls-files -i -c --exclude-standard`); `land_squash.sh` `probe` checks containment and a merge-tree conflict trial, not ignore status. Detection was manual, from `git status` showing an `M` row inside a directory every skill treats as local scratch.

Consequences: the ignore rule and the index disagreed about the same fact (root-cause family D, single source of truth), so `git status` and the dirt gates started reporting modifications under the audit home, and the live execution session appending its exec-r1 seal line to that file saw the append become tracked dirt in the primary checkout. Propagation witnessed and closed: the execution branch `2026-10-20-done-cached-diff-authorized-reversal` was cut after f5a8142ed, inherited the tracked seal, and modified it in its own round-close commit; after 839984ac2 the peer session rebased onto `main` and its branch tree carries no `.ai-playbook/` path (verified at filing), so that instance is closed, but every branch cut from a polluted base inherits the pollution the same way and nothing would report it.

## Expected

An ignored path never enters the index on any landing path. An ignore refusal is a stop for the staging attempt, never an instruction to add `-f`; the sanctioned durable copies of audit artifacts are the docs branch retention and the backlog rows. The predicate `git ls-files -i -c --exclude-standard` prints nothing on `main`, on every landing branch before its squash, and in every done commit's index.

## Suggested fix

Complete the missing complement in the smallest form, per the repository guidelines' Machinery admission protocol (warning-only first):

1. Skill text, no machinery: one sentence each in the plans round-close seal duty and the maintenance authoring closeout residue step: the seal and every `.ai-playbook/` artifact are local and stay untracked; an ignore refusal ends the staging attempt.
2. Warning-only predicate at the two existing landing surfaces: `land_squash.sh` `probe` reports any branch-changed path that `git check-ignore --no-index` matches, and the done landing sweep's ignored arm gains a tracked (`--cached`) sibling reporting `git ls-files -i -c --exclude-standard` output. Admission: incident f5a8142ed and 4399aee99; expected catch frequency about two per 138 seals in the home's history; false-positive cost zero on a clean index (no legitimate tracked path matches an ignore rule today, and the `/docs/facts.md` legacy deny lines in `.gitignore` exist for exactly this shape); review 2027-01-20, promotion only after a true catch with the registry-removal row pre-registered.
3. Already done, recorded here so the plan does not redo it: the two instances were untracked by 839984ac2 with the disk copies kept and the docs branch retention intact, and the inheriting execution branch dropped the path on its rebase.

Rejected: tracking seals on `main` (widens the policy against its selection record, `docs/history/plans/completed/2026-10-13-skill-audit-artifact-ignore-default.md`), and a git `pre-commit` hook (the `commit-tree` plus `update-ref` landing path never runs it, and hooks are installed per agent, not per repository).
