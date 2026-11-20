# Backlog: backlog/completed regrows because the origins gate and doctrine text still license parking covered rows there

- **Filed:** 2026-11-08, operator-directed untracked-residue survey session
- **Status:** covered (docs/history/plans/2026-11-08-backlog-completed-dir-regrowth.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed defect (playbook repo, tracked corpus)
- **Class:** fix-class
- **Driving force:** correctness
- **Dedup probe:** searched open backlog bodies for `backlog/completed`, `regrow`, and `fold-then-delete` (rg over `docs/history/backlog/`); hits are cross-references only (`2026-10-04-main-rewind-consolidation-incident.md`, `PLAN-PROMPTS.md` scope arms). The nearest open row, `2026-10-13-covered-stub-rows-pending-disposal.md`, owns covered stubs left at the backlog top level, not the completed/ directory's regrowth or the gate's acceptance of it as a disposition home; the `completed/README.md` sweep record owns the 2026-10-02 one-time sweep only. No open row owns this defect.
- **Cluster:** docs/history/backlog/2026-10-13-covered-stub-rows-pending-disposal.md (same defect class: terminal-state backlog artifacts the closing boundary leaves behind; that row owns top-level stubs, this row owns the completed/ parking channel)

## Observed versus expected

Observed: `docs/history/backlog/completed/` holds 56 dated item files (2026-10-05 through 2026-11-02) although the directory's own README declares it "must stay empty of dated item files" and records the operator direction of 2026-10-01: "integrate into completed plans, do not keep completed backlog separately". The directory was fully swept on 2026-10-02 (126 candidates: 7 fold-and-delete, 116 delete-no-fold, 3 skip) and has regrown since through routine landing flows, not exotic repairs.

Expected: a covered backlog origin row's only terminal shape is the repository guidelines' fold-then-delete: disposition folded onto the archived covering plan, origin file deleted in the same change. `backlog_completed_dir` remains tooling-compatibility scaffolding and stays empty of dated item files.

## Evidence

- The regrowth is produced by the standard landing flows themselves, each commit ADDing rows into completed/ with folded dispositions: `058bbb7e0` (2026-10-26 done batch), `1633ed7ce`, `843cc9709`, `b5c3ad6ca` (2026-11-01 batches), `f0013ef57` and `8a0d939dd` (2026-11-08 15:06 UTC landings, two files each). The parked rows already carry the fold: for example `completed/2026-11-02-coverage-gate-checkpoint-twin-self-exemption.md` reads `Status: done (covered by docs/history/plans/completed/2026-11-02-coverage-gate-checkpoint-twin-self-exemption.md)`, so only the file's own persistence contradicts the rule; the disposition data already lives in the covering plan.
- The parking is licensed by four standing texts that contradict the fold-then-delete rule:
  - `docs/maintenance/development_lessons.md` #104 ("A Deleted Backlog Origin Row Fails the Origins Archive Gate; Archive It Covered"): its rule names "archived under `docs/history/backlog/completed/` with the covered flip" as a served disposition, born of the 2026-10-19 straggler refusal where a deleted row read as `missing` until it was restored under completed/.
  - `scripts/check_plan_origins_closed.py`: `DEFAULT_COMPLETED_DIR = "docs/history/backlog/completed"`; a row present under that directory classifies as state `completed` ("archived under the completed directory"), a pass state.
  - Root `AGENTS.md`, Commit & Pull Request Guidelines: the witness-precedence clause cites "the `docs/history/backlog/completed/` twin when one exists" ahead of the covering plan's completed twin, legitimizing future twins.
  - `agents/skills/doc-hierarchy/company-decisions.md` line 69: "move to `backlog/completed/` when the implementing plan completes", directly contradicting `doc-hierarchy/SKILL.md` line 82 ("Do not keep per-item files under `backlog/completed/`") and the plans skill's Backlog origin entry ("do not keep per-item archives under `{backlog_completed_dir}`").
- Why sessions prefer parking over the licensed deletion: once a plan is certified and landed, appending its `## Disposition of migrated backlog items` fold is a post-certification byte change routed through a delta round (development_lessons.md #102), so moving the row into completed/ is the cheap gate-accepted repair; the gate's acceptance converts fold-then-delete from the rule into an optional shape.
- The correct skill text exists and is contradicted, not absent: plans SKILL.md Backlog origin bullet and doc-hierarchy SKILL.md Backlog entry both prescribe fold-then-delete with completed/ empty, so text-only guidance has already proven insufficient against the gate-backed alternative.
- Standing citations that name completed/ twins as incident homes and need re-pointing at sweep time: development_lessons.md #111 (cites `completed/2026-10-15-plan-prompts-prune-end-anchor-overreach.md`) and #207 (cites `completed/2026-10-22-prune-audit-landing-token-never-resolves.md`); `agents/skills/maintenance/zcode.md` line 92 cites items "now closed in `docs/history/backlog/completed/`".
- Archaeology (git log -S, 2026-11-08): the gate's completed-directory default (`DEFAULT_COMPLETED_DIR`) dates to fe61c8471; lesson #104's "Archive It Covered" rule landed c71465ef1 (the 2026-10-26 exec batch); the first post-sweep regrowth is cb6adcb6f (2026-10-18, three rows added), sixteen days after the sweep.
- Fold verification (sampled): both 2026-11-08-parked rows' covering plans exist under `docs/history/plans/completed/` and carry the disposition spans (`2026-11-02-coverage-gate-checkpoint-twin-self-exemption.md` verified, `2026-11-02-rolling-log-write-foreign-staged-remedy.md` present), confirming the "fold exists, file persists" shape: the disposition data already lives in the archived plan, so deleting the parked file loses nothing. Both sampled files were themselves removed later the same day by the rewrite below; the covering plans remain (re-verified), so the conclusion carries to the remaining rows.
- Rewrite witness (2026-11-08 ~15:26 UTC): an operator-directed history rewrite (force-pushed tip `8fe42f5d6`, recorded by the same-day PLAN entry `release-publish-scope-hygiene-check`) removed exactly the four rows parked by the 15:06 UTC landings, taking the directory from 56 to 52 files; the parking commits `f0013ef57` and `8a0d939dd` are out of branch ancestry (reflog-only witnesses). The rewrite repairs the day's instances, not the channel: the gate's completed-directory pass state and the licensing texts stand unchanged, so the next landing can park again.

## Suggested correction

Three coordinated arms in one plan:

1. One-time sweep of the 56 files with the 2026-10-02 recipe (the `completed/README.md` sweep record is the canonical form): re-derive the census, probe claimed origins (`scripts/check_backlog_claimed.py`), fold onto the covering plan where the fold is missing and licensed, delete the file, re-point the standing citations listed above, and append the sweep receipt to the README record.
2. Align the four licensing texts with the fold-then-delete rule: #104's rule wording (the archive gate's sanctioned homes), the AGENTS.md witness-precedence clause (the covering plan's completed twin becomes the only named durable home), `company-decisions.md` line 69, and the maintenance overlay citation.
3. Machinery arm under the admission protocol: flip the origins gate's completed-directory pass state to warning-only first ("archived against the fold-then-delete rule"), promote to refusing only after a true catch, with the machinery registry row carrying this backlog row as its incident, a named sunset, and the promotion criteria. Expected catch: every parking attempt (the regrowth commits above are the rate evidence). False-positive cost: a legacy twin still awaiting sweep during the transition window, bounded by running arm 1 first.

This row proposes no change to the gate's `missing = straggler` fail-closed posture: with fold-then-delete as the only terminal shape, the 2026-10-19 refusal shape disappears because the fold lands in the same change as the deletion, before any gate reads the row as missing.
