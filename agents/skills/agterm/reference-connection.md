## Connection and output

- **Socket resolution** (when `--socket` is omitted): `AGTERM_SOCKET` is the path the running app
  bound; agtermctl resolves the same rendezvous: `<AGTERM_STATE_DIR>/agterm.sock`, else
  `<$HOME>/Library/Application Support/agterm/agterm.sock`. Passing `--socket "$AGTERM_SOCKET"` is the
  safe explicit form.
- **`--json`**: prints the raw response object. Without it, ordinary mutations print `ok`, batch
  close/move prints the affected session count, and `tree`/`window list` print a human listing. Use
  `--json` when you need to read ids or values back.
- **Response shape**: `{"ok": true, "result": {…}}` or `{"ok": false, "error": "<message>"}`.
  `result` carries one of: `id` (affected/new session/workspace/window), `text` (session copy/text),
  `exitCode` (overlay result), `count` (diagnostics/search), `restore` (the restore-mode policy),
  `zmx` (the daemon inventory), `remote` (another Mac's attachable sessions, for `zmx tree`),
  `affected` (things actually changed: sessions
  for a batch close/move, daemons killed for `zmx prune`), `tree` (the tree), `windows` (window list), `app` (the serving app's identity, for
  `version`). The process exit code is non-zero when
  `ok` is false.
- **Options go after the subcommand**: `agtermctl session type "ls" --target active`, never before it.

## events

`agtermctl events [--json] [--kind KIND ...] [--run UUID --after SEQ] [--limit N]` continuously
prints control events. Each poll is one ordinary socket connection and one `events.read` response.
The CLI immediately reads again after a non-empty page and waits 250 ms only after an empty page.

With no cursor, the first read subscribes from now: it returns an empty batch anchored at the current
tail, and the CLI prints only later events. The app keeps a non-destructive ring of the latest 4,096
events for its current process run. Independent readers do not consume one another's events.

The five event kinds and payloads are:

- `status`: `name`, normalized `status` (`idle`|`active`|`blocked`|`completed`), a `blink` boolean,
  and optional `pane`, `color` and `shape` (the last two being the per-call `--color`/`--shape`
  overrides). An event fires whenever the whole indicator changes, not just the state name, so a
  change to `blink`, `pane`, `color` or `shape` alone is a real event you can watch, while re-asserting
  an identical indicator emits nothing. Clearing emits `idle`.
- `notify`: `name`, effective `title`, and `body`. It is emitted after target and foreground-focus
  suppression checks, including when desktop banners are disabled.
- `session.created` / `session.closed`: session `name`, emitted when the session enters or leaves a
  visible window tree. Undo emits a new `session.created`; grace-period finalization does not emit a
  second close.
- `tree.changed`: an empty payload and the affected window id. Name, membership, and ordering changes
  are coalesced for 100 ms per window, as is a `session context` set or clear that changes the value.
  Read `tree --json` for the current snapshot.

Every event has `seq` (app-wide sequence), `ts` (Unix timestamp), `kind`, optional
`window`/`workspace`/`session` ids, and `payload`. Human mode prints one compact line. `--json` emits
one bare `ControlEvent` JSON object per line and flushes promptly.

`--kind` may be repeated or comma-separated. Unknown kinds are errors. Filtering advances the global
cursor across nonmatching events, so changing a filter does not replay skipped history. `--limit`
defaults to 100 and accepts 1 through 1,000.

The raw `events.read` response stores the batch under `result.events`:

```json
{"ok":true,"result":{"events":{"run":"01234567-89AB-CDEF-0123-456789ABCDEF","next":42,"items":[]}}}
```

A no-cursor response supplies the `run` and `next` anchor. Resume with both values:
`agtermctl events --run RUN --after NEXT`. The options must appear together. The streaming `--json`
format contains bare events rather than this batch envelope, so a restart-safe client must retain the
cursor from raw `events.read` responses.

Cursor failures return `ok: false`, one of `event run changed`, `event cursor expired`, or
`event cursor is ahead of the current sequence`, plus the current empty anchor under
`result.events`. Treat them as data-loss boundaries. Do not silently use the supplied anchor unless
the caller explicitly accepts dropping the missing interval. `agtermctl events` exits non-zero on a
cursor, transport, or server error and does not retry forever while the app is absent. SIGINT and
SIGTERM use normal process behavior.

## Addressing

- `--target` defaults to `active` (the selected session / current workspace). Accepts a full UUID
  (case-insensitive) or a unique prefix. Zero matches → `notFound`; ambiguous prefix → `ambiguous`
  (the error lists candidates).
- For a WORKSPACE, `active` is where a new session lands: one created in the foreground (the GUI's New
  Workspace, or `workspace new` without `--collapsed`) until the selection CHANGES, to a different
  session or to none at all, as when you close the last one, or `workspace select` names another, it is
  deleted, or the workspace filter hides it. Hiding drops it for good, so turning the filter off does not
  restore it. Reselecting the already-selected session does not count: `session select`,
  `session overlay open --follow` and single-session `session go` leave it in place. `workspace select` on an EMPTY
  workspace has no session to select, so it takes the target instead (and is revealed if the filter was
  hiding it). Else the selected session's workspace, else the last one. A background create (`workspace new --collapsed`,
  `session new --create-workspace --no-select`) never takes it. The tree workspace node's `active` flag
  reads the SELECTED session's workspace only, so right after a foreground create it can name a
  different workspace than `--target active` resolves to; address by id when the two must agree.
- **For an agent, `active` is the USER's GUI-selected session, not yours.** Your shell is
  `$AGTERM_SESSION_ID`; the user is usually on a different session while you work. Pass
  `--target "$AGTERM_SESSION_ID"` on any session-scoped command (`session overlay open`, `session scratch`,
  `session type`, `session text`, `session background`, `session status`, `session copy`, …) that must act
  on the session you run in, otherwise it hits
  whatever the user has selected. `session overlay open` opens in the background without switching the user
  (both full and floating); pass `--follow` to additionally SELECT the target, switching the user to it.
- `--window <id|prefix|active>` (on session/workspace/tree/font/notify/pick commands) picks which window's
  tree to act on; default is the frontmost. With `--window` set, that window must be open. Without it,
  an id/prefix session target is matched across all open windows.
- `window.*` commands take the window selector as a positional argument, default `active` (frontmost).
- A window need not be open to be a `window.*` target (e.g. `window select` opens a closed one).

