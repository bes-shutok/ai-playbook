# clocked-order-discharge-on-fire consumes the order without launching the payload session

- Cluster: coordination-single-writer-ttl
- Cluster: docs/history/backlog/2026-10-16-loop-child-dispatch-launchd-collapse.md (the same launchd dispatch surface; the collapse row's default-form promotion is gated on this row's discharge-verification gap)
- Priority: normal
- Status: covered (docs/history/plans/2026-10-17-rearm-dispatch-ladder-incident-guards.md)

Witnessed 2026-10-10 11:00:07 WEST: order co-ea9763321390435782e5a292b01f2a25 (requested 11:00, armed 07:40
through the watcher chain) fired its launchd one-shot; the job log shows only the discharge JSON
(`"discharged": true`, sentinel consumed) and the worktree held by the order's payload showed zero progress
afterwards, with no headless session process and an empty err log. The order ledger marks the order
`discharged`, so the missed-order detector (`clocked-order due`) never fires and the ordered work is stranded
silently - the exact instant-death class the launchd resume-carrier bullet's env-complete form was written
for, one layer up. Expected: a discharge whose payload session does not verifiably launch (no session receipt,
no worktree progress) records a discharge failure on the order instead of a clean discharge, so the survey's
clocked-order consult turns it into a turn error and the payload re-parks. Adjacent witness: the older order
co-7a5e12e9's resume automation (automation-6b4af1e7) fired 11:00:12 the same morning and its worktree also
showed no progress at 11:06.
