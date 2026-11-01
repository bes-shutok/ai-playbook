# Backlog: read maintenance quota from the active agent's native source

- **Filed:** 2026-11-01, Codex maintenance quota attribution investigation
- **Status:** covered (docs/history/plans/2026-11-01-maintenance-runtime-native-quota-sources.md)
- **Workflow:** backlog
- **Priority:** high
- **Required agent type:** codex
- **Origin class:** runtime-specific quota-source correction
- **Class:** fix-class
- **Driving force:** automation
- **Cluster:** docs/history/backlog/2026-11-01-codex-maintenance-quota-reset-wake.md (same Codex primary-window decision path; this row owns native evidence, the sibling owns the reset wake)

## Observed versus expected

Observed: the account governor's prior 97% five-hour reading came from shared cached evidence carrying ZCode log-mined exhaustion events, not from this Codex session. A fresh Codex `account/rateLimits/read` returned a Codex primary window at 41% of 300 minutes and a separate weekly secondary window. The current Codex probe still selects the newest `rollout-*.jsonl` anywhere under `~/.codex/sessions`, so it can read another session's record and does not prove the active account's current five-hour usage. Codex's documented app-server method returns `rateLimitsByLimitId.codex.primary` and `secondary`, including `usedPercent`, `windowDurationMins`, and `resetsAt` ([Codex App Server rate limits](https://learn.chatgpt.com/docs/app-server#rate-limits-chatgpt)). ZCode already has its own live quota probe and its CLI log belongs only to ZCode.

Expected: every maintenance quota decision first binds to the active agent runtime, then reads quota from that runtime's native source. Codex reads the Codex account rate limits and identifies the short primary window from the returned duration; ZCode reads its existing Z.ai quota endpoint and may use only ZCode-owned supporting evidence. An unknown or unsupported runtime, missing native primary window, stale session record, or failed probe cannot inherit another runtime's cached percentage or be reported as abundant. The report names runtime, source, observation time, window kind and duration, usage, and reset; secondary windows remain distinct from the primary stop threshold.

## Work scope

Investigate the source-selection contract across the maintenance quota policy, runtime detection, window probe, account governor state, and Codex/ZCode runtime guidance. Implement explicit runtime-to-native-source routing for Codex and ZCode, reject cross-runtime cached evidence, and leave a narrow extension seam for additional runtimes without claiming unsupported adapters. Keep the existing threshold and lane policy unless evidence shows the current unknown behavior must change to prevent false attribution. Keep the Codex quota-reset wake capability in `2026-11-01-codex-maintenance-quota-reset-wake.md` separate; this item establishes trustworthy inputs for that workflow.

## Acceptance criteria

- A Codex maintenance turn reads its current Codex account rate-limit data; the primary and secondary windows are preserved separately with their returned durations and reset times.
- A Codex five-hour pause can be based only on the Codex primary window, never a ZCode log/cache entry or a rollout from an unrelated session.
- A ZCode turn continues to use its existing ZCode quota source and cannot feed its usage or exhaustion records into Codex decisions.
- Unknown runtime or unusable native evidence is reported as unknown with runtime/source/timestamp provenance; it never silently becomes abundant or adopts another runtime's last value.
- Maintenance instructions and quota reports make runtime detection and source selection explicit, with Codex and ZCode procedures and a documented unknown-runtime fallback.
- Focused regression coverage demonstrates both runtime paths, native Codex primary/secondary parsing, cross-runtime isolation, and unknown/unusable evidence.
- The Codex reset-wake backlog remains a separate follow-up and consumes only the native Codex primary reset.
