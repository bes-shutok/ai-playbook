# Backlog: Codex deny-envelope live acceptance verification

Status: open
Origin: Task 6 of docs/plans/2026-09-13-budget-gate-quota-fixes.md (implementation pass, 2026-09-13); registered hook recorded in agents/hooks/budget-guard/README.md (`## Registration` section)
Date: 2026-09-13

Canonicality: this item is the canonical home of the open envelope question,
the Ship-when drive procedure, and the post-drive decision table (declared by
r1's overflow-manifest finding: simplification#duplicate-decision-table;
referenced as F12 in the r1 fix notes). agents/hooks/budget-guard/README.md
carries a two-line summary and points here; it keeps the registration schema,
the trust-prompt note, and exit conventions only.

## Open question

The codex binary's own error strings name `permissionDecisionReason` for deny
decisions, while the adapter `agents/hooks/budget-guard/codex.sh` (via
`budget_guard_core.py`) emits the flat
`{"permissionDecision": "deny", "reason": ...}` envelope. Acceptance by the
live codex binary is unverified because the registered hook does not run until
the user approves the first-start hook trust prompt (a human step; the codex
binary hash-gates hooks via `trusted_hash` under `[hooks.state]` in
`~/.codex/config.toml`).

Adapter-level fixture probes (Task 6, 2026-09-13) verify the adapter's
emission only, not Codex's acceptance of the envelope:

- Deny probe (future-dated fixture flag, temp dir): exit 0, stdout exactly
  `{"permissionDecision": "deny", "reason": "Provider quota window for runtime codex ends at <reset ISO>. Do not start new tool work. Finish the current sub-agent step, land the pending done commit if any, record the budget pause, and schedule the resume."}` (reason embeds the fixture's `reset_at_iso`).
- Pass probe (no flag present): exit 0, empty stdout (fail-open).

## Ship-when live check

Single drive, after the user approves the Codex hook trust prompt at the next
Codex session start:

1. Pre-drive: confirm the fired marker `~/.ai-playbook/runtime/budget-guard.fired`
   is ABSENT. A stale marker whose recorded epoch matches the drive window
   would suppress the block via the anti-thrash rule and fake an envelope
   rejection.
2. Arm the guard flag at the canonical `~/.ai-playbook/runtime/budget-guard.flag`
   path (the only path the registered command reads; it passes no arguments)
   with ALL THREE required keys: `runtime=codex`, `reset_at_epoch`, and
   `reset_at_iso` (a flag missing any required key makes `parse_flag` return
   an empty mapping and the hook fails open, faking decision-table state
   three). Keep the epoch horizon short: set `reset_at_epoch` to now + 10
   minutes so an aborted drive cannot leave the host-global flag armed past
   the drive window. If the drive aborts before step 4, remove the canonical
   flag and the fired marker immediately.
3. Drive one real tool call in a trusted Codex session and observe whether it
   is denied and, if so, whether the denial reason embeds the `reset_at_iso`
   value written at step 2 (co-registered matcher-`.*` hooks can produce a
   denial that says nothing about this adapter's envelope).
4. Post-drive cleanup: remove the canonical flag AND the fired marker.

## Decision table (post-drive states)

The no-denial states are discriminated by the core's own fired marker: the
core writes it (best-effort) whenever it runs and emits a block, independent
of whether Codex honors the envelope; a denial verdict additionally requires
the ISO string check.

| Post-drive observation | Verdict | Follow-through |
| --- | --- | --- |
| A denial is observed AND the denial reason embeds the armed flag's `reset_at_iso` (string check against the flag written at step 2) | Envelope accepted; question closed | Complete post-drive cleanup; record the closure in this item |
| A denial is observed but its reason does NOT embed the armed flag's `reset_at_iso` | Another hook denied the call (for example the co-registered matcher-`.*` hook); envelope attribution unknown; do NOT close the question | Isolate per the attribution caveat below, remove the co-registration interference, and re-run the drive |
| No denial; fired marker PRESENT after the drive | The hook ran and emitted a block Codex did not honor: the envelope was rejected | Write the RED pin of the probed-accepted shape against the pre-fix core first, then adapt `codex.sh`/`budget_guard_core.py`, flip GREEN, and re-verify live |
| No denial; fired marker still ABSENT after the drive (this reading assumes the marker write succeeded; re-run the drive once before concluding a trust/registration gap) | The hook never ran: a trust or registration gap, not an envelope defect | Fix trust approval / registration before re-testing the envelope |

Attribution caveat: docs/history/backlog/2026-09-13-budget-gate-decision-table-attribution.md
records how co-registered matcher-`.*` hooks and concurrent writers of the
host-global fired marker can distort these attributions; isolate before
trusting a verdict that contradicts the fixture probes.

## Real-pause Ship-when observation

The plan's second Ship-when condition (one real budget pause and scheduled
resume completing end-to-end on at least one runtime, at a live window
boundary) counts as verified only when the backstop block is observed to have
fired during that pause: the `budget-guard.fired` marker written at block
time (recording the pause's reset epoch) or the block reason observed in the
transcript. A completed pause record without an observed backstop block
proves the probe path only, not the enforcement path (review round r1,
finding F3).

Registered schema (README mirror): agents/hooks/budget-guard/README.md,
`## Registration` section; this item owns the question, the drive procedure,
and the decision table.
