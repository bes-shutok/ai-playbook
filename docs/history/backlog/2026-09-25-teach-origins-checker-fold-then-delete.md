# Teach check_plan_origins_closed.py the fold-then-delete disposition

Priority: low, class real.

The 2026-09-25 backlog-completed-archive-policy execution (plan
`docs/plans/completed/2026-09-25-backlog-completed-archive-policy.md`) deleted
318 dated per-item files from `docs/history/backlog/completed/` after folding
their dispositions into completed plans and registry audit notes. The corpus
origins scan now warns on 116 migrated origins whose per-item files no longer
resolve under the backlog directory (expected warn noise; the audit trail lives
in the disposition bullets and the `user-approved` registry audit notes).

Fix: extend `scripts/check_plan_origins_closed.py` so an unresolved origin is
not warned when the origin's basename appears in the plan's own disposition
section (`## Disposition of migrated backlog items`) or when a
`document-registry.md` audit cell names the former item path with the
`user-approved ...: migration audit` token. Keep the warn arm for genuinely
unresolved origins; retire the migrated-origin warn noise with this script's
own surface.

Non-goals: no change to the plan-mode gate behavior beyond the disposition
consult; no registry format change.
