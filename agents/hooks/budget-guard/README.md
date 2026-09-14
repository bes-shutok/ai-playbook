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

Paths below use `<repo-root>` as a placeholder for this repository's checkout
root on your host: JSON config files do not expand `~`, so resolve repo-root
to an absolute path before pasting.

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
              "command": "<repo-root>/agents/hooks/budget-guard/zcode.sh",
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
`statusMessage`). The stored command is the repo-root-resolved absolute path;
JSON does not expand `~`:

```json
{
  "PreToolUse": [
    {
      "matcher": ".*",
      "hooks": [
        {
          "type": "command",
          "command": "<repo-root>/agents/hooks/budget-guard/codex.sh",
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

The registered commands execute this repository's live working tree, so hook
behavior tracks the checked-out branch: after any edit to
`budget_guard_core.py` or either adapter script, smoke-check the hooks with
`python3 -m unittest discover -s scripts -p 'test_budget_guard_hooks.py'`
from the repository root. A deployed-copy registration (pinned hook files
under `~/.ai-playbook/`) is tracked in
`docs/history/backlog/2026-09-14-budget-guard-deployed-hook-copies.md`.

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

The adapter emits the flat `{"permissionDecision": "deny", "reason": ...}`
envelope while the codex binary's own error strings name
`permissionDecisionReason`; live acceptance by the codex binary is unverified
until the first-start trust prompt is approved. The canonical open-question
statement, Ship-when drive procedure, and post-drive decision table live in
`docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md`; a
denial closes the question only when its reason embeds the armed flag's
`reset_at_iso`. This README keeps the registration schema, the trust-prompt
note, and exit conventions only.

## Exit conventions

- zcode block: exit 2, stdout `{"decision": "block", "reason": "..."}`
  (built via `json.dumps`, never string concatenation).
- codex block: exit 0, stdout `{"permissionDecision": "deny", "reason": "..."}`.
- pass: exit 0, empty stdout.

The core `budget_guard_core.py` is stdlib-only, imports no network modules,
and ignores stdin.

## Fixture test mode recipe

Hermetic tests live in `scripts/test_budget_guard_hooks.py`. They create a
synthetic flag file in a tmp directory (future `reset_at_epoch`, fixed
`reset_at_iso`), invoke the adapters as subprocesses with
`--flag-path`/`--fired-path` pointing into the tmp dir, and assert the exact
envelope, exit code, and cleanup semantics. No network access and no
credentials are involved; run with:

```bash
python3 -m unittest discover -s scripts -p 'test_budget_guard_hooks.py'
```
