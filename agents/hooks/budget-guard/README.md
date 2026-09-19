# budget-guard PreToolUse backstop hook

A last-resort PreToolUse hook that stops new tool work while a provider quota
window (GLM/Codex) is exhausted. The probe `scripts/quota_window_probe.py`
writes a guard flag when it decides to pause; this backstop enforces that
decision at the tool-call level so a session that missed the probe's report
still cannot silently burn a resume attempt or start new work mid-pause.

## What the gate protects

When the quota probe pauses a run, the intended behavior is: finish the
current sub-agent step, land the pending done commit, record the budget
pause, schedule the resume, and stop. An agent deep in a tool loop may not
see that instruction. The backstop turns the pause decision into a hard
block on the next tool call, with the recovery steps embedded in the block
reason.

## Flag-file contract

- Path: `~/.ai-playbook/runtime/budget-guard.flag` (written atomically,
  mode 0600, by `scripts/quota_window_probe.py`).
- Content lines:
  - `runtime=<zcode|codex>`: the runtime whose quota window closed. This line
    is forensics-only: the flag is host-global and gates every registered
    runtime regardless of which runtime's window expired.
  - `reset_at_epoch=<unix seconds>`: window reset; the flag is ignored and
    removed once this timestamp is in the past.
  - `reset_at_iso=<local ISO-8601>`: human-readable reset time, used
    verbatim in the block reason.
  - `plan=<slug>` (optional): the plan slug for forensics; names which
    plan run paused (an execute-plan implementation run or a plans
    authoring run).

Reset horizon: resets beyond `MAX_RESET_HORIZON_SECONDS` (40 days) are
clamped to that horizon at parse time (a clamped binding can still arm the
flag at the clamped epoch), and the flag writer additionally refuses any
binding still beyond the horizon (fail-open).

## Fired-marker anti-thrash rule

On the first block, the hook writes `budget-guard.fired` next to the flag
(default `<flag dir>/budget-guard.fired`, overridable with `--fired-path`).
While the fired marker exists, later invocations pass silently: the session
was already interrupted once and repeated blocks would spam the transcript.
The marker is host-global, so the single intervention is once per HOST per
window, not per session: the first blocked call anywhere on the host silences
the guard for every other session until the marker is removed at window
reset. The marker records the flag's `reset_at_epoch` and binds to that
window: a marker left over from an older window is stale, is removed, and
does not suppress the new window's single block. The marker write is
best-effort: if it fails, the block still fires (the block is the safety
effect; the marker is anti-thrash only). Only a regular file counts as a
marker.

## Fail-open rule

A missing, unreadable, or malformed flag fails open: exit 0, empty stdout.
The hook never blocks without a live, well-formed flag. An expired flag
(`reset_at_epoch` in the past) is ignored and removed, together with the
fired marker, so the guard self-cleans at window reset. Removal is guarded
by a re-read confirmation: a concurrent probe may have replaced the flag
with a newer live window between the hook's read and the removal, and in
that case removal is skipped so the newer window stays enforced.

## Shared guard lock and atomic cleanup contract

Every mutation and cleanup of the guard flag and fired marker serializes on
one shared `fcntl.flock` lock file next to the flag:
`~/.ai-playbook/runtime/budget-guard.lock`. Its participants are the probe
writer (`scripts/quota_window_probe.py`, whose final `os.replace` holds the
lock), both hook adapters through this core (expired-window flag-and-marker
cleanup, stale-marker removal, and the fired-marker write), and the standing
resume watcher's atomic compare-and-delete
(`scripts/execute_plan_resume_watcher.py`, which also clears the fired
marker). The read, the compare, and the unlink always happen while the lock
is held; the canonical contract lives in
`scripts/execute_plan_resume_watcher.py`, and this core holds the same file
by the same name because it is deployed as a standalone real-file copy that
cannot import that module.

Consequences:

- A cleanup that decided on an expired window can never interleave an
  unlink between the probe writer's decision and its replacement: the
  replacement happens under the lock, so the locked re-read sees the newer
  live window and skips the removal (the newer flag survives).
- A stale-marker removal re-checks the marker content under the lock: a
  marker re-written for the current window between the decision and the
  removal survives, and the block for the current window still fires.
- Lock-unavailability degrades fail-open: the cleanup skips removal quietly
  (the next hook invocation retries), and the writer skips arming rather
  than writing an unlocked replace (a later probe at the same boundary
  arms under the lock; not arming is the fail-open direction, r2 F16).

## Host-scope note

The guard flag and fired marker live under `~/.ai-playbook/runtime/` and are
host-global: on a shared host they gate every session's tool calls until
expiry or manual removal (`rm ~/.ai-playbook/runtime/budget-guard.flag
~/.ai-playbook/runtime/budget-guard.fired`). The flag content names the plan
slug for forensics.

One-shot semantics residual: after the single block fires and the marker is
written, a session that retries through the block runs unguarded for the rest
of the window (the marker suppresses further blocks). Treat the block as
authoritative: stop tool work and follow the embedded recovery steps instead
of retrying past it.

## Registration

Both runtimes register the deployed copies of the hook trio under
`~/.ai-playbook/hooks/budget-guard/` (real files, never symlinks), not this
repository's working tree. The schema below writes commands in the
`~/.ai-playbook/` form for readability; the values stored in the JSON config
files must be the `$HOME`-expanded absolute deployed paths, because JSON
config files do not expand `~`.

ZCode: `~/.zcode/cli/config.json` under `hooks.events.PreToolUse`:

```json
{
  "hooks": {
    "enabled": true,
    "events": {
      "PreToolUse": [
        {
          "hooks": [
            {
              "type": "command",
              "command": "~/.ai-playbook/hooks/budget-guard/zcode.sh",
              "timeout": 10
            }
          ]
        }
      ]
    }
  }
}
```

The matcher is omitted deliberately: this backstop gates every tool call, not
a tool-name subset. Config-file hooks are disabled unless `hooks.enabled` is
set to `true`.

Codex: registered in `~/.codex/hooks.json` under `hooks.PreToolUse` as a
`.*` matcher group (schema mirrors the live registered group's field set:
group-level `matcher`, hook fields `type`, `command`, `timeout`,
`statusMessage`):

```json
{
  "PreToolUse": [
    {
      "matcher": ".*",
      "hooks": [
        {
          "type": "command",
          "command": "~/.ai-playbook/hooks/budget-guard/codex.sh",
          "timeout": 10,
          "statusMessage": "Checking budget guard"
        }
      ]
    }
  ]
}
```

The `.*` matcher gates every tool call (the Codex schema requires a matcher;
`.*` is the whole-tool-set equivalent of the omitted ZCode matcher above).

Registration takes effect for sessions started after the config change; an
already-running session does not load the new hook.

### Deployed copies

The registered commands execute pinned real-file copies of the trio under
`~/.ai-playbook/hooks/budget-guard/`, so hook behavior does not track the
checked-out branch; refreshes are an explicit re-deploy. Refresh recipe:

1. Copy `zcode.sh`, `codex.sh`, and `budget_guard_core.py` from this
   repository's `agents/hooks/budget-guard/` into
   `~/.ai-playbook/hooks/budget-guard/`, preserving modes (the two adapter
   scripts stay executable); deploy real files, never symlinks.
2. Run the fixture probes against the deployed paths: in a temp directory,
   write a future-dated flag fixture (`runtime=codex`, `reset_at_epoch` one
   hour ahead, matching `reset_at_iso`) and invoke the deployed `codex.sh` and
   `zcode.sh` with `--flag-path`/`--fired-path` inside the temp directory;
   give each script its own fresh fixture files, because the fired marker
   one block probe writes makes the other script's block probe pass
   silently. All three fixture keys are required, and the
   `--flag-path`/`--fired-path` values must stay inside the temp directory,
   never the canonical `~/.ai-playbook/runtime/` paths: a fixture flag
   written there arms a host-wide lockout and suppresses the live guard's
   single block for the window. Expect the deny envelope with exit 0 (codex)
   and the block envelope with exit 2 (zcode), both embedding the fixture's
   `reset_at_iso`, then rerun both with no flag and expect exit 0 with
   empty stdout. Delete the temp fixture files afterward.
3. Repoint or verify the runtime configs: each budget-guard `command` value
   must equal the `$HOME`-expanded absolute deployed path
   (`$HOME/.ai-playbook/hooks/budget-guard/zcode.sh` and the `codex.sh`
   analogue); verify by parsing the JSON and comparing against the expanded
   path, since stored JSON values must be `$HOME`-expanded (JSON does not
   expand `~`).

PreToolUse-only: never register this hook on a Stop event. The block must
land before a tool runs; on Stop it would arrive after the work is done and
can wedge the session.

### First-start hook trust prompt (Ship-when)

The codex binary hash-gates hook trust (`trusted_hash` entries under
`[hooks.state]` in `~/.codex/config.toml`) and does not run a newly registered
hook until the user approves it at the next Codex session start. Until that
approval lands, the hook above is registered but inert. Ship-when
follow-through: after approving the prompt, run the single live drive
described in the open question below, then complete its post-drive cleanup.

### Open envelope question

The codex binary's own error strings name `permissionDecisionReason` for deny
decisions, while the adapter `agents/hooks/budget-guard/codex.sh` (via
`budget_guard_core.py`) emits the flat
`{"permissionDecision": "deny", "reason": ...}` envelope. Acceptance by the
live codex binary is unverified because the registered hook does not run until
the user approves the first-start hook trust prompt (a human step; the codex
binary hash-gates hooks via `trusted_hash` under `[hooks.state]` in
`~/.codex/config.toml`). This README is the canonical home of the open
question, the Ship-when drive procedure, and the post-drive decision table.

Adapter-level fixture probes verify the adapter's emission only, not Codex's
acceptance of the envelope: a deny probe (future-dated fixture flag, temp
dir) exits 0 with the deny envelope whose reason embeds the fixture's
`reset_at_iso`; a pass probe (no flag present) exits 0 with empty stdout.

## Ship-when live drive procedure

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
   unidentified-writer outcome before removing. A writer that cannot be
   identified while its epoch still matches an armed or pending window is an
   unidentified writer: an unidentified writer stops the drive and is
   investigated before any re-arm.
3. Arm the guard flag at the canonical `~/.ai-playbook/runtime/budget-guard.flag`
   path (the only path the registered command reads; it passes no arguments)
   with ALL THREE required keys: `runtime=codex`, `reset_at_epoch`, and
   `reset_at_iso` (a flag missing any required key makes `parse_flag` return
   an empty mapping and the hook fails open, faking decision-table state
   four - no denial, no fired marker: the hook never ran), plus `armed_by=manual` (the drive is a manual arming; the block
   reason attributes it). Keep the epoch horizon short: set `reset_at_epoch`
   to now + 10 minutes so an aborted drive cannot leave the host-global flag
   armed past the drive window. Abort clause: if the drive aborts after the
   flag is armed but before step 5, remove the canonical flag and the fired
   marker immediately (an abort during step 2's live-window path keeps the
   fired marker until that path's own abort-and-investigate protocol clears
   it); when the contingency was invoked, restore the hooks.json backup
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
| A denial is observed AND the denial reason embeds the armed flag's `reset_at_iso` (string check against the flag written at step 3) | Envelope accepted; question closed | Complete post-drive cleanup; record the closure; verdict trusted only when the attribution gate passes (co-registered hooks status recorded, marker baseline matched); when the contingency was invoked: contingency restore diff-verified, trust state confirmed |
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
modes are documented in
docs/plans/completed/2026-09-15-budget-gate-decision-table-attribution.md.
Warning: the PreToolUse model check is disabled host-wide during the window,
so bound the window to the single re-drive; a second consecutive foreign
denial is terminal for this question and is reported, not re-driven.

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
   reappear for the shifted groups, verify the `trusted_hash` entries for
   the restored groups under `[hooks.state]` in `~/.codex/config.toml`
   before any further drive: re-diff live `~/.codex/hooks.json` against
   both backups, and check each restored group's recorded hash against the
   live file. If the entries verify for the restored groups, trust is
   intact (the shift was already absorbed without a prompt): record the
   verification and proceed. Only a mismatch (the entries are neither valid
   for the restored groups nor explained by a recorded prompt approval)
   stops the drive: report the state for manual recovery. Do not edit
   `~/.codex/config.toml`.

Note: the step-4 marker removal is defense in depth, not a required step;
with a fresh flag armed the core auto-removes the stale marker, so no
anti-thrash suppression is possible.

## Abort and retirement protocol

(Backup existence is the arming state: the contingency is armed while either
fixed-name backup exists, and retired and disarmed once both are deleted.)

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
  recording their digests) so the pre-contingency restore point is not
  destroyed, or retire the contingency immediately by deleting both
  backups; record the superseding edit under either option. Retirement
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

The execute-plan second Ship-when condition (one real budget pause and
scheduled resume completing end-to-end on at least one runtime, at a live
window boundary) counts as verified only when the backstop block is observed
to have fired during that pause: the `budget-guard.fired` marker written at
block time (recording the pause's reset epoch) or the block reason observed
in the transcript. A completed pause record without an observed backstop
block proves the probe path only, not the enforcement path. The observed
backstop block counts as enforcement evidence only when the same attribution
gate passes, with the baseline conjunct disjunctive for the backstop's
primary scenario (a marker record already present at the boundary baseline
whose content matches the pause's reset epoch, OR the marker's mtime inside
the pause window with content matching that epoch) and the concurrent-writer
check at the pause boundary as the shared conjunct; the boundary check
requires an attended pause, and for an unattended pause the substitute
evidence is the blocked session's own transcript showing the block reason,
marker evidence alone being insufficient.

Canonical home since 2026-09-17 (plan 2026-09-17-budget-gate-pause-mechanics-drive); docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md is history-only after this fold.

## Exit conventions

- zcode block: exit 2, stdout `{"decision": "block", "reason": "..."}`
  (built via `json.dumps`, never string concatenation).
- codex block: exit 0, stdout `{"permissionDecision": "deny", "reason": "..."}`.
- pass: exit 0, empty stdout.
- Block reason text ends `... record the budget pause, and schedule the
  resume. Budget guard flag: <flag path> (armed by <armed_by>).` where
  `<armed_by>` is the flag's `armed_by` line (`probe` for probe-written
  flags, `manual` for a drive arming, `unknown` when the line is missing).

The core `budget_guard_core.py` is stdlib-only, imports no network modules,
and ignores stdin.

## Fixture test mode recipe

Hermetic tests live in `scripts/test_budget_guard_hooks.py`. They create a
synthetic flag file in a tmp directory (future `reset_at_epoch`, fixed
`reset_at_iso`, an `armed_by` line - `probe` by default, `manual` for the
drive fixture, omitted to pin the `unknown` fallback), invoke the adapters
as subprocesses with
`--flag-path`/`--fired-path` pointing into the tmp dir, and assert the exact
envelope, exit code, and cleanup semantics. No network access and no
credentials are involved; run with:

```bash
python3 -m unittest discover -s scripts -p 'test_budget_guard_hooks.py'
```
