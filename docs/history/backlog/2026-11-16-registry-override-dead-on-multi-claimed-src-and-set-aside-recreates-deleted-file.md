# Backlog: the registry audit-note override cannot license a path that two rows claim, and the rolling-log set-aside recreates a peer's staged-deleted file on disk

- **Filed:** 2026-11-16, user-requested capture after a self-heal recovery of a refused rolling-log commit
- **Status:** open
- **Priority:** medium
- **Origin class:** session-witnessed gate behaviour (two defects met in one recovery; both reproduced from disk)
- **Workflow:** backlog
- **Class:** fix-class (a documented override that is structurally unusable for a common registry shape; a cleanup arm that reverses a peer's pending deletion)
- **Skill and step:** `scripts/doc_registry_validator.py` (`check-writes`, the multiply-claimed-src handling and the audit-note override); `scripts/done_run.sh` commit with the rolling-log pre-stage guard and the set-aside arm described in the Write boundary rule of `docs/history/backlog/PLAN-PROMPTS.md`

## Observed vs expected

Defect 1 (override unusable). Observed: an investigate entry commit through the runner was refused by the landing sweep's doc-registry arm because a peer's uncommitted body edit sat on an archived plan under `docs/history/plans/completed/`. The validator documents an audit note on the path's registry row as the override. With the note added, `check-writes` still printed `HARD immutable path written without override`: the plan's path is claimed by two identities (the plan row and its `-origin` row), and the multi-claim branch skips both the lifecycle exemption and the override (`doc_registry_validator.py`, the `src in multi_claimed` continue). A dry run over a copy of the registry showed 21 paths in that state. Only blanking the `src` of the second row, besides the note, produced `override: ... has an audit-noted registry row` and a clean `validate`. Expected: the documented override either works for the common plan-plus-origin pairing or its docs say it needs the pairing removed first, and the refusal names that step.

Defect 2 (set-aside recreates a deleted file). Observed: after the operator-gated remedy set aside a peer's staged deletion of a tracked backlog row (`git restore --staged` on that path, the recorded delta `:100644 000000 <blob> 000000000 D`), the runner's commit landed and the deleted file was back in the working tree, byte-equal to HEAD, so the peer's pending deletion no longer existed in either index or worktree. The runner's arm that installs a saved blob worktree-only for an undeclared path treats the deletion's saved blob as content to put back. Repair needed `git rm` on the path and a verified match of the recorded delta. Expected: a set-aside undeclared path that was staged as a deletion is re-applied as a deletion (or left untouched), never recreated.

## Reproduction evidence (trimmed)

1. Defect 1: stdin ` M docs/history/plans/completed/<plan>.md` into `python3 scripts/doc_registry_validator.py check-writes --stdin` over a registry whose plan row carries a valid `user-approved YYYY-MM-DD:` note and whose `-origin` row shares the `src`: HARD, plus `warn: src ... is registered by multiple identities`. Blank the second row's `src`: override printed, 0 unprotected writes.
2. Defect 2: with a peer's staged deletion present, `scripts/done_run.sh commit --stage docs/history/backlog/EXEC-PROMPTS.md ...` refuses before staging (the pre-stage guard names a staged path outside the declared set). After the operator-gated restore of that one path and a successful commit, `ls` shows the file again and `git status` shows nothing for it.

## Environment

- Playbook repo, primary checkout shared with a peer session, 2026-11-16; both defects hit while landing one `EXEC-PROMPTS.md` entry commit.

## Suspected root area

Defect 1: the multi-claim guard was written for a registry defect (two identities for one artifact) and the override branch sits behind it; the plan-plus-origin pairing is a deliberate registry convention, so the guard fires on valid rows. Fix options to price: let the override apply when all claiming rows are completed-history rows; or document and refuse with the exact dedupe step; or fold the origin row's coverage into one row.

Defect 2: the set-aside arm saves "the staged blob" per path and reapplies it worktree-only; a staged deletion has no new blob, so the saved value is the old blob and the reapply recreates the file. A deletion needs its own class in the journal (class field already recorded per path) and a deletion-shaped reapply.
