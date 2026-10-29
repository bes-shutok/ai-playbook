# Backlog: done sweep deletes gate reports still cited by closeout migration

- **Filed:** 2026-10-29 during final-closeout recovery
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Consumer urgency:** Consumer repositories that use this shared closeout workflow need the retention fix; the skills-repository personal priority profile must not park it as formal-hardening for this repository alone.
- **Skill-step:** `agents/skills/done/SKILL.md` Steps 2-3; `scripts/done_sweep_gates_lib.py` `gate_docs_tmp_sweep` and `_prune_done_session_markers`
- **Class:** fence-class
- **Origin class:** self-serving
- **Driving force:** reliability
- **Severity:** high; a later worktree-removal gate could not complete until missing report bytes were recovered.
- **Dedup probe:** searched open backlog filenames and Problem bodies for `gate-reports`, `done-session`, `docs-tmp-sweep`, `closeout-migration`, and retention. The closest open items are `2026-10-27-closeout-mirror-residuals.md` (migration replacement, digest, and identity residuals) and `2026-10-28-closeout-migrate-zero-delta-silence.md` (a zero-result migration report); neither covers later pruning of a verified destination still cited by a retained manifest. The closed `closeout-proof-record-retention` receipt (`docs/history/backlog/EXEC-PROMPTS.md`, landing commit `cf2341ebf`) preserves the plan-slug proof family but not gate reports. `2026-10-09-done-recursive-tmp-sweep-safety.md` is already covered and concerns recursive deletion safety, not this bounded gate-report home.
- **Source:** interactive Codex recovery on 2026-10-29; repository-owned skill and script copies, not vendored copies; capture hygiene: public-hygiene explicit-path scan passed and em-dash file scan passed.

## Problem

A closeout migration manifest can record a gate report under `{tmp_dir}/done-session/gate-reports/` as `verified: true`. For entries in the `migrated` or `renamed` sections, `gate-removal` checks that the recorded destination still exists. A later `docs-tmp-sweep` pass can prune an older report by its mtime relative to the session-window anchor without checking whether a retained `closeout-migration.json` still cites that destination. A later `gate-removal` then refuses worktree teardown, although the manifest still claims the transfer was verified.

In this run, repository history and both checkouts lacked the report bytes. The first response asked the operator for originals before checking local backup snapshots. The reports were recovered from those snapshots, and the same gate passed afterward. A future run should not require an operator to supply bytes that the cleanup policy could have retained while they were still referenced.

## Expected

Preserve each verified gate-report destination in the `migrated` or `renamed` sections of a closeout migration manifest while its registered worktree closeout can still consume that record. Use existing manifest and worktree state as the source of truth, and let the existing session-window pruning resume after closeout has completed. Retrying a recoverable teardown should not depend on an operator locating a backup. Branch-only unknown-ref recovery and its post-success pruning signal are tracked separately in `2026-10-29-branch-only-closeout-terminal-state.md` because the current manifest has no durable branch-only completion state.

## Suspected root area

`scripts/done_sweep_gates_lib.py`, `gate_docs_tmp_sweep` and `_prune_done_session_markers`; the sweep applies only the session-window mtime rule to the bounded gate-reports home and does not consult live closeout-migration references.

## Suggested direction

Trace the current `closeout-migration.json` consumer and its registered-worktree completion signal. Extend the existing sweep retention decision to keep only verified report destinations in the `migrated` and `renamed` sections while the registered worktree closeout remains live. Keep the existing age-window rule for other reports. Do not add a separate registry or ledger. Branch-only lifecycle design is out of this item and remains open in `2026-10-29-branch-only-closeout-terminal-state.md`.

## Why not fixed now

This turn is completing the approved plan-authoring closeout and worktree teardown. Changing shared retention behavior is outside that plan and needs a focused implementation decision.
