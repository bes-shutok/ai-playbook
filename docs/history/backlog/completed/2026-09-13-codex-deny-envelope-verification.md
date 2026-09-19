# Backlog: Codex deny-envelope live acceptance verification

Status: done (executed 2026-09-18 via docs/plans/completed/2026-09-17-budget-gate-pause-mechanics-drive.md)
Origin: Task 6 of docs/plans/2026-09-13-budget-gate-quota-fixes.md (implementation pass, 2026-09-13); registered hook recorded in agents/hooks/budget-guard/README.md (`## Registration` section)
Date: 2026-09-13

Canonicality: the canonical home of the open envelope question, the
Ship-when drive procedure, and the post-drive decision table is
agents/hooks/budget-guard/README.md ("Open envelope question") since
2026-09-17 (plan 2026-09-17-budget-gate-pause-mechanics-drive); this item is
history-only from that date and moves to completed at plan completion.
Previously this item was the canonical home (declared by r1's
overflow-manifest finding: simplification#duplicate-decision-table;
referenced as F12 in the r1 fix notes).

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

1. Pre-drive session check (fail-closed order: it precedes any state change):
   - Baseline sets: The operator records the drive session's own PID at
     baseline, expands it into its recorded descendant set with a recursive
     pgrep -P pass, and records the host's ChatGPT/Codex desktop-app helper
     processes into an explicit exclusion list (executable paths recorded at
     baseline, not judged ad hoc at check time).
   - Matching pass: The check then runs the anchored pattern
     pgrep -fl '(^|/)(codex|zcode)([[:space:]]|$)' (executable-token
     anchored, so a bare -f substring match - for example an editor holding
     a file whose path contains codex - does not fire) followed by one ps
     pass over the matched PIDs to classify each line against the recorded
     PID, its recorded descendants, and the recorded helper list.
   - Contamination stop: Any matched line outside those three recorded sets
     is contamination, stopping before the flag is armed.
   - Re-checks: The same check is re-checked at the drive boundary and after
     the drive. At the boundary re-check the operator also records the
     wall-clock timestamp of the drive tool call, which the row-3 mtime
     comparison uses.
2. Pre-drive evidence: fired-marker baseline and hooks-trust status. The
   operator first confirms the fired marker
   `~/.ai-playbook/runtime/budget-guard.fired` is ABSENT, then records the
   fired marker's baseline stat (presence, mtime, content epoch) and the
   co-registered matcher-`.*` hooks and their trust status from the trusted
   session. A stale marker whose recorded epoch matches the drive window
   would suppress the block via the anti-thrash rule and fake an envelope
   rejection. A marker already PRESENT at baseline whose content matches no
   live window is removed before the drive, and a marker matching a live
   window is an abort-and-investigate condition (its writer is unknown). A
   live window here means the marker's content epoch equals the
   `reset_at_epoch` of a flag currently armed at the canonical flag path, or
   of a budget pause whose window has not yet elapsed. The investigation
   runs before any state change: record the marker's full stat and content;
   re-run the step-1 session check plus one ps pass over its matches to
   identify the writer, where the identification evidence is concrete: the
   epoch matching an armed window plus the pause/probe records naming that
   window as this host's own; wait out the armed epoch (the horizon of
   whichever window the epoch matches: 10 minutes for a drive-armed flag,
   the pause window's own reset for a probe-armed one) and re-stat the
   marker; treat the marker as removable once its epoch matches no armed or
   pending window, and if writer identification failed, record the
   unidentified-writer outcome in this item before removing. A writer that
   cannot be identified while its epoch still matches an armed or pending
   window is an unidentified writer: an unidentified writer stops the drive
   and is investigated before any re-arm.
3. Arm the guard flag at the canonical `~/.ai-playbook/runtime/budget-guard.flag`
   path (the only path the registered command reads; it passes no arguments)
   with ALL THREE required keys: `runtime=codex`, `reset_at_epoch`, and
   `reset_at_iso` (a flag missing any required key makes `parse_flag` return
   an empty mapping and the hook fails open, faking decision-table state
   three). Keep the epoch horizon short: set `reset_at_epoch` to now + 10
   minutes so an aborted drive cannot leave the host-global flag armed past
   the drive window. Abort clause: if the drive aborts after the flag is
   armed but before step 5, remove the canonical flag and the fired marker
   immediately (an abort during step 2's live-window path keeps the fired
   marker until that path's own abort-and-investigate protocol clears it);
   when the contingency was invoked, restore the hooks.json backup
   (diff-verified) in addition to removing the flag and the fired marker,
   per the pre-restore live snapshot, the registration-level merge
   granularity, the restore-source order, and retirement in the abort and
   retirement protocol below.
4. Drive one real tool call in a trusted Codex session and observe whether it
   is denied and, if so, whether the denial reason embeds the `reset_at_iso`
   value written at step 3 (co-registered matcher-`.*` hooks can produce a
   denial that says nothing about this adapter's envelope).
5. Post-drive cleanup: remove the canonical flag AND the fired marker.

## Decision table (post-drive states)

The no-denial states are discriminated by the core's own fired marker: the
core writes it (best-effort) whenever it runs and emits a block, independent
of whether Codex honors the envelope; a denial verdict additionally requires
the ISO string check.

| Post-drive observation | Verdict | Follow-through |
| --- | --- | --- |
| A denial is observed AND the denial reason embeds the armed flag's `reset_at_iso` (string check against the flag written at step 3) | Envelope accepted; question closed | Complete post-drive cleanup; record the closure in this item; verdict trusted only when the attribution gate passes (co-registered hooks status recorded, marker baseline matched); when the contingency was invoked: contingency restore diff-verified, trust state confirmed |
| A denial is observed but its reason does NOT embed the armed flag's `reset_at_iso` | Another hook denied the call (for example the co-registered matcher-`.*` hook); envelope attribution unknown; do NOT close the question | Invoke the row-2 contingency below (numbered steps); verdict trusted only when the attribution gate passes (marker baseline re-taken after the first drive) |
| No denial; fired marker PRESENT after the drive | The hook ran and emitted a block Codex did not honor: the envelope was rejected | Write the RED pin of the probed-accepted shape against the pre-fix core first, then adapt `codex.sh`/`budget_guard_core.py`, flip GREEN, and re-verify live; verdict trusted only when the attribution gate passes (marker mtime within 60 seconds of the drive call timestamp, no concurrent codex or zcode process at any check) |
| No denial; fired marker still ABSENT after the drive (this reading assumes the marker write succeeded; re-run the drive once before concluding a trust/registration gap) | The hook never ran: a trust or registration gap, not an envelope defect | Fix trust approval / registration before re-testing the envelope; verdict trusted only when the attribution gate passes (baseline hooks trust status recorded and unchanged, marker baseline matched; when the contingency was invoked: contingency restore diff-verified, trust state confirmed) |

A verdict whose gate evidence is missing or unverifiable is contaminated.
'marker baseline matched' means the post-drive marker state is consistent
with the recorded baseline transition: a marker absent at baseline appears
only in-window with the armed epoch, or is absent at both points for rows
without a block. The session checks are point-in-time bounds and do not
prove window exclusivity; a verdict is re-opened if later evidence
contradicts it; a marker mtime not within 60 seconds of the drive call
timestamp counts as unverifiable gate evidence, and a verdict relying on
it alone is contaminated.

Row-2 contingency (invoked only by the foreign-denial row): the contamination
modes are documented in docs/history/backlog/2026-09-13-budget-gate-decision-table-attribution.md.
Warning: the PreToolUse model check is disabled host-wide during the window,
so bound the window to the single re-drive; a second consecutive foreign
denial is terminal for this item's question and is reported, not re-driven.

1. On a foreign denial, copy `~/.codex/hooks.json` to
   `~/.codex/hooks.json.budget-drive-backup` AND to
   `~/.ai-playbook/runtime/hooks.json.budget-drive-backup`, recording a
   checksum of each and verifying with `diff` before any edit.
2. Disable the co-registered matcher-`.*` hooks other than the budget-guard
   hook by DELETING the require-luna PreToolUse group object from
   `~/.codex/hooks.json` (delete the whole group object; do not comment out a
   line, blank its command, or edit the hook in place, so the recorded
   positional trust keys shift exactly as step 5 describes).
3. Start a FRESH trusted Codex session and re-approve the hook trust prompt
   (the edit invalidates `trusted_hash` for the affected groups).
4. Quiesce the first drive session (close it, or record its PID for
   exclusion), re-arm the guard flag at the canonical flag path with a FRESH
   `reset_at_epoch` (now + 10 minutes) and a matching `reset_at_iso`, remove
   the fired marker, re-take the marker baseline and re-run the step-1
   session check at the re-drive boundary, and re-drive; the re-drive's
   denial ISO check compares against the fresh `reset_at_iso`, not the
   first window's.
5. Before restoring, snapshot live `~/.codex/hooks.json` to a distinct
   timestamped file (for example `~/.codex/hooks.json.pre-restore.<epoch>`)
   and diff it against the expected mid-contingency shape (the backup minus
   the require-luna group); record any unexpected divergence and route it
   through the superseded-edit decision in the abort and retirement
   protocol below before overwriting. One restore granularity applies
   everywhere: a registration-level merge of the require-luna group back
   into live `~/.codex/hooks.json`, never a wholesale file overwrite;
   restore `~/.codex/hooks.json` from the backup (diff-verified) at that
   granularity. Because the recorded trust keys are positional (group
   index and content), the hook trust prompt is EXPECTED to reappear for
   the shifted groups after the restore - approving it in the next fresh
   session, with the diff against the runtime backup clean, is the correct
   terminal action; record the extra approval. If the trust prompt does NOT
   reappear for the shifted
   groups, verify the `trusted_hash` entries for the restored groups under
   `[hooks.state]` in `~/.codex/config.toml` before any further drive:
   re-diff live `~/.codex/hooks.json` against both backups, and check each
   restored group's recorded hash against the live file. If the entries
   verify for the restored groups, trust is intact (the shift was already
   absorbed without a prompt): record the verification and proceed. Only a
   mismatch (the entries are neither valid for the restored groups nor
   explained by a recorded prompt approval) stops the drive: report the
   state for manual recovery. Do not edit `~/.codex/config.toml`.

Note: the step-4 marker removal is defense in depth, not a required step;
with a fresh flag armed the core auto-removes the stale marker, so no
anti-thrash suppression is possible.

Abort and retirement protocol (backup existence is the arming state: the
contingency is armed while either fixed-name backup exists, and retired and
disarmed once both are deleted):

- Stop trigger: if at any point a backup file is missing, a checksum or
  diff mismatches, or the session dies mid-contingency, stop and do not
  re-drive.
- Skip-restore branch (the failure happened at contingency step 1 before
  any hooks.json edit): skip the restore entirely - live
  `~/.codex/hooks.json` is still unmodified, so there is nothing to restore
  - and retire immediately by deleting both fixed-name backups.
- Single-source restore branch: otherwise, when at least one copy verifies
  good against its step-1 checksum, first snapshot live
  `~/.codex/hooks.json` to a distinct timestamped file and diff it against
  the expected mid-contingency shape (the backup minus the require-luna
  group), routing any unexpected divergence through the superseded-edit
  branch before overwriting; then restore require-luna's registration from
  the runtime backup
  `~/.ai-playbook/runtime/hooks.json.budget-drive-backup` (diff-verified),
  falling back to `~/.codex/hooks.json.budget-drive-backup` when the
  runtime copy is the missing or mismatched one (registration-level merge
  of the require-luna group back into live, never a wholesale file
  overwrite).
- Both-bad branch (BOTH copies are missing or mismatched, so no restore
  source exists): change nothing further in `~/.codex/hooks.json`, retire
  by deleting both fixed-name backups (whichever exist) so the standing
  order below cannot later revert the manual recovery against a stale
  backup, and report the state for manual recovery.
- Superseded-edit branch: if the standing order's check confirms an
  intentional edit, do not restore; either refresh both fixed-name backups
  to the current live content with new checksums (diff-verified), first
  preserving the old backup copies under distinct timestamped names (or
  recording their digests in this item) so the pre-contingency restore
  point is not destroyed, or retire the contingency immediately by deleting
  both backups; record the superseding edit under either option. Retirement
  timing: the refresh option retires at the next clean fresh-session diff
  per normal-path retirement below; the retire option retires immediately.
- Normal-path retirement: after a completed restore or a confirmed
  superseding edit whose next fresh-session diff is clean, retire both
  fixed-name backups by deleting them, so the standing order cannot later
  revert a legitimate hooks.json edit against a stale backup.
- Standing order (keyed to backup existence): until both backups are
  retired, at the next Codex session start after any contingency, first
  confirm no intentional edit since the contingency (a hooks.json change
  made on purpose after the restore), then diff live `~/.codex/hooks.json`
  against the runtime backup (or against
  `~/.codex/hooks.json.budget-drive-backup` when the runtime copy is the
  missing or mismatched one) and restore diff-verified on mismatch from
  the same source, taking the same pre-restore live snapshot (distinct
  timestamped file; unexpected divergence routed through the superseded-edit
  decision before overwriting) and the same registration-level merge
  granularity (the require-luna group merged back into live, never a
  wholesale file overwrite).

## Real-pause Ship-when observation

The plan's second Ship-when condition (one real budget pause and scheduled
resume completing end-to-end on at least one runtime, at a live window
boundary) counts as verified only when the backstop block is observed to have
fired during that pause: the `budget-guard.fired` marker written at block
time (recording the pause's reset epoch) or the block reason observed in the
transcript. A completed pause record without an observed backstop block
proves the probe path only, not the enforcement path (review round r1,
finding F3). The observed backstop block counts as enforcement evidence
only when the same attribution gate passes, with the baseline conjunct
disjunctive for the backstop's primary scenario (a marker record already
present at the boundary baseline whose content matches the pause's reset
epoch, OR the marker's mtime inside the pause window with content matching
that epoch) and the concurrent-writer
check at the pause boundary as the shared conjunct; the boundary check
requires an attended pause, and for an unattended pause the substitute
evidence is the blocked session's own transcript showing the block reason,
marker evidence alone being insufficient.

Registered schema (README mirror): agents/hooks/budget-guard/README.md,
`## Registration` section; this item owns the question, the drive procedure,
and the decision table.
