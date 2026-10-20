# Backlog: a served origin deleted under the covered-row rule reads LIVE to the stale check, so its prompt entry never prunes

- **Filed:** 2026-10-20, operator-directed investigate pass over the served-out-of-band EXEC-PROMPTS entry `done-valid-document-removal-row-coverage` (pruned this pass)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** session-witnessed validator/convention mismatch (the 2026-10-13 covered-row deletion rule inverted the checker's absent-file design premise)
- **Class:** fix-class
- **Driving force:** correctness (a served entry stays dispatchable for days and invites a duplicate run)
- **Skill/step:** `scripts/check_prompt_log_origins.py` stale check (`LIVE` classification for "an absent file that resolves nowhere", the module docstring's fail-open line); the `--collateral-served` discovery mode (does not enumerate the sibling log the way `--prune-audit` does); the rolling logs' prune rule in `docs/history/backlog/PLAN-PROMPTS.md` line 8 and its EXEC-PROMPTS delta
- **Cluster:** docs/history/backlog/2026-10-13-covered-stub-rows-pending-disposal.md (the deletion rule's hygiene side; this row is its checker counterpart)
- **Cluster:** docs/history/backlog/2026-10-16-collateral-mixed-fixture-composition-pin.md (same checker surface, a collateral-mode fixture residual)
- **Capture hygiene:** repo-relative paths only; no personal or machine-specific data.
- **Dedup probe:** searched open backlog filenames and text for `prune`, `collateral`, `served`, `covered-row`, `prompt log`; nearest: `docs/history/backlog/2026-10-13-covered-stub-rows-pending-disposal.md` (the deletion rule's hygiene side; this row is its checker counterpart), `docs/history/backlog/2026-10-16-collateral-mixed-fixture-composition-pin.md` (same checker surface, a fixture residual), `docs/history/backlog/2026-10-15-plan-prompts-prune-end-anchor-overreach.md` (removals audit, covered by the `plan-prompts-prune-range-content-inventory` entry). No open row owns the deleted-origin classification.

## Problem

The repository guidelines' covered-row rule (in force by 2026-10-13, quoted by `docs/history/backlog/2026-10-13-covered-stub-rows-pending-disposal.md`; wording last touched in `cb6adcb6f`) requires a completing change to delete the backlog row outright instead of leaving a `Status: covered` stub. The stale check in `scripts/check_prompt_log_origins.py` predates that convention (2026-10-01, `44eec2a73`): it classifies an origin SERVED only when its first `Status:` line reads done/covered or when the absent file resolves by basename into the `completed/` or `rejected/` archive directories, and classifies an absent file that resolves nowhere LIVE by design ("fail-open for novel statuses and fail-closed only for the witnessed drift classes"). Under the deletion rule, the common case of a served origin is now an absent path with no archive twin, so the checker's most common real input inverted from "moved somewhere unknown" to "served by deletion", and every such entry reads LIVE forever.

Witnessed (one entry, two independent misses): the EXEC-PROMPTS entry `done-valid-document-removal-row-coverage` stayed live two days after the plan landing `887d890b8` (2026-10-18, "fix: prevent false dirt-regression refusals") deleted its origin `2026-10-14-done-dirt-gate-valid-doc-removal.md`; `python3 scripts/check_prompt_log_origins.py docs/history/backlog/EXEC-PROMPTS.md` returned exit 0 with the entry listed LIVE, while `--collateral-served --base 887d890b8~1` over the same log listed it correctly. The 2026-10-20 11:00 monitor turn's prune sweep (`93fff300b`, three served entries pruned) passed over it the same morning. The collateral mode does recognise deletion, but only inside a landing's own `base..HEAD` window, and the closeout rider that runs it (`agents/skills/maintenance/template-authoring.md`) sweeps `PLAN-PROMPTS.md` by default, not the EXEC log; `--prune-audit` enumerates both logs, `--collateral-served` does not.

The checker's own precedent is the guide: `--prune-audit` already accepts deletion-shaped evidence (receipt witnesses), and `--collateral-served` already classifies deletion-in-window as served; the stale check's absent-file arm just never learned the deletion convention.

## Expected

An entry whose every origin was deleted on the base branch (a deletion commit reachable from HEAD) classifies SERVED with the deletion commit named, so the monitor survey's stale read and the landing closeout's fail-closed check see it, and the entry gets its receipted prune instead of sitting dispatchable. A path that never existed at all (a typo) stays LIVE, keeping the checker's fail-closed protection against fabricated origins.

## Suggested fix

Smallest form first, no new gate (the change narrows an existing report-only finding class):

1. `scripts/check_prompt_log_origins.py` stale check: add a served class - origin absent at HEAD, the path absent from the backlog top level, and `git log --diff-filter=D -1 --format=%H -- <path>` resolves a deletion commit that is an ancestor of HEAD - reported as SERVED with the deletion commit as witness. A path with no history at all stays LIVE (typo protection unchanged); `deferred/` resolution keeps its own never-serves class; fixtures in `scripts/test_check_prompt_log_origins.py` for the deleted-served case, the never-existed LIVE case, and the unchanged archive-dir and status cases.
2. `--collateral-served` enumerates the sibling log exactly as `--prune-audit` does, so a landing's collateral sweep covers both rolling logs; one sentence in `agents/skills/maintenance/template-authoring.md`'s rider sentence to say the sweep covers both logs.

Rejected: classifying every absent origin as served (it deletes the typo protection the 2026-10-01 design names as its fail-closed line); returning to `Status: covered` stubs (the operator-set deletion rule exists precisely to stop stubs re-presenting done work as open, witnessed by the covered-stub-rows census); a hand-prune doctrine with no checker change (the recurrence is every covered-row deletion landing that names an open entry's origin, already two witnesses).
