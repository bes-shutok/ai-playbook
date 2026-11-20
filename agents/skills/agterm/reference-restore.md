## restore modes

**Settings ▸ General ▸ Restore sessions** chooses one global launch mode. The process keeps the mode it
started with, so a change applies after restarting agterm.

- **Fresh shells** restores the structural snapshot with new shells.
- **Re-run commands** starts captured commands again. The old processes are not attached.
- **Live sessions** wraps primary and split panes with zmx and reattaches to their running processes. Zsh
  must be the macOS login shell. Scratch, overlay, and quick terminals remain temporary.

Closing agterm or sending it SIGTERM ends the attach clients and leaves live daemons running. A clean quit
also captures each live pane's foreground command, so a daemon missing after an orderly machine restart is
recreated under the same name running that command. Four cases still come back as a
fresh shell: a pane in a window closed before the quit, a hard power loss or force quit that never reached
capture, a command refused by `restore-denylist.conf` or carrying control bytes, and SIGTERM, which leaves
the daemons running but skips the clean-quit capture. A session or split that is explicitly deleted has its
daemon killed after the undo grace period.
Switching to Fresh shells or Re-run commands and restarting ends every detached live process in the state
directory. A launch that still requests Live sessions but cannot use it preserves those processes.

The tree exposes actual backing without adding sidebar UI. Primary and split surface entries carry
`backedByZmx`; the session-level field is true only when every existing primary or split pane is backed.
Reattach keeps usable text, TUI state, and normal colors. It does not retain inline images, earlier OSC 133
prompt markers, program-changed palette entries, or existing cell hyperlink metadata. New terminal output
after reattach behaves normally.

## restore

`agtermctl restore capture`, capture every open pane's live foreground command NOW, into the same slot the
quit-time capture fills, and persist it. For the exit that never reaches `applicationWillTerminate`: a force
quit, a crash, a hard reset, a power loss, all of which today leave every pane restoring a plain shell. (A
shutdown, restart or logout is not one of them: that path quits the app normally and captures by itself.)
Run it from a scheduled job or bind it, and an exit nobody was there for restores like a deliberate
quit. Consumption is unchanged, the next launch arms each captured command once and clears it. App-global
(no `--window`), prints `count`, the number of panes it captured a command for (main and shown split count
one each). It runs only when `rerun` is configured for the next launch. Configured fresh-shell and live
modes return `restore.capture requires rerun mode; configured restore mode is MODE`. A capture is only as
fresh as its last run: a pager or a build that has finished since still re-runs after a crash, which
`restore clear` drops wholesale and `restore-denylist.conf` prevents per program. Typed at a prompt the
command records ITSELF, since while it runs it is that pane's foreground process and the pane comes back
running `agtermctl restore capture` (which
prints its count and captures itself again). Bind it or schedule it rather than running it by hand:
`restore clear` is app-global, so it is no per-pane undo.

`agtermctl restore clear`, clear every session's saved CAPTURED foreground command and persist, so the
next restart restores plain shells for those panes (not whatever each pane was running). It does NOT clear
a `session.new --command` session's own command (`initialCommand`, the durable creation identity), which
still re-runs in `rerun` mode. This command works in every mode. `rerun` captures each pane's foreground
command at a clean quit and starts it again on relaunch; `restore clear` wipes those saved commands now
(also closing the force-quit re-fire window). App-global (no `--window`), prints `ok`. Like `restore capture`
it acknowledges only a save that landed: if any window's write fails it reports that at least one window
failed to save, since those captures are still on disk and nothing reads those slots back.

`agtermctl restore mode [none|rerun|live]`, read the restore policy, or write it for the NEXT launch.
Bare, it reports five things: `configured` (what settings hold, so what the next launch asks for),
`requestedAtLaunch` and `active` (what THIS launch asked for and what it got), `restartRequired`, and
`unavailableReason` when live was requested and refused. The two requested values differ once the mode has
changed since this instance started, which is exactly when a caller wonders why nothing happened.

Setting it changes nothing in the running app, and no flag makes it: a pane is wrapped in a zmx daemon or
not at the moment it is created, so a running shell cannot be retrofitted either way. A failed write is
reported as a failure rather than acknowledged.

`agtermctl zmx list`, every daemon and every pane expecting one, joined, under the restore status as a
header. `state` is `claimed`, `orphan`, `unknown`, `conflicted`, `pendingClose` or `foreign`;
`observation` is `running`, `unreadable` or `absent`, separate from the client count because a daemon that
is gone and one zmx could not read are different answers. A CLOSED window's panes are `claimed` with zero
clients. That is the resting state after you close a window, not a leak, which is why the owner's window
state is its own column. `unknown` means the pane inventory was incomplete, so no row can be called an orphan.
The header also carries `endpoint.executable` and `endpoint.socketDirectory`, which is what another machine
needs to reach these daemons; a server older than remote sessions omits the key.

`agtermctl zmx prune`, kill the daemons no pane claims and nothing is attached to. It refuses outright on
an incomplete or conflicted inventory. The gate is checked and revalidated rather than atomic: zmx has no
kill-if-detached, so prune re-lists immediately before killing and drops anything that gained a client,
but a client attaching from outside agterm in the remaining gap can still be terminated. It reports each
daemon separately, and a "cleaned up a stale socket" line is NOT a kill: zmx unlinked a socket it could
not reach, and that daemon may still be running.

`agtermctl zmx kill --target ID --pane left|right --force`, destroy one pane's daemon and the process in
it. All three are required: this kills a backend process, reaches a pane no window is showing, and takes
down every client attached to that daemon, so there is no sensible default for who is affected. Killing a
shown split closes that split; killing a primary promotes its split survivor, or closes the session when
there is none; a pane whose window is closed simply comes back as a fresh shell. None of these gets the
three-second undo. It refuses a daemon already gone, one zmx could not read (forcing that can unlink a
live daemon's socket and leave it running unreachable), and a session inside its undo window. Killing the
daemon of the pane you are typing in can kill the calling `agtermctl` before it reads the reply.

`--window ID` scopes the search to one window's claims, for a session prefix claimed in more than one.
Omit it to search every window, closed and unindexed ones included; `active` is not accepted, and neither
is it for `--target`. Without it an ambiguous prefix reports `no left pane daemon for session ID`, the
same answer a target that does not exist gets.

`agtermctl zmx tree [HOST]`, attachable sessions across EVERY open window. With a `HOST` it reads another
Mac over ssh; with none it reports this app's own, which is exactly the form the remote call runs on the
far side, so it is also how to see what another machine would answer without sshing anywhere.
`result.remote` carries `endpoint` (the zmx `executable` and `socketDirectory`), `host` when one was given,
and `sessions`, each with `id`, `name`, `windowID`/`windowName` and `workspaceID`/`workspaceName` (show the
names, group by the ids, neither is unique, so two windows called `main` merge if you group by name),
`context` when its owner set one, `cwd`, `splitAxis` when it has a split, and `panes`
(`{pane, daemon, foreground}`, the last being the argv that pane is running and omitted when none is
reported). `host` is the ssh destination the REQUESTING app was given, stamped on after decoding: the far
side has no idea which name reached it.

Only a session whose every pane still has a live daemon is listed: attaching to a name that no longer
exists would CREATE a daemon and hand back a fresh shell wearing it, so an incomplete one is omitted
rather than offered half. An empty list is a successful answer and does NOT diagnose the restore mode,
`zmx list` does that. The far side must be running in `live` mode, which is what puts a daemon behind each
pane, and be new enough to answer `zmx tree` at all; an older one is refused by name rather than
half-attached. It also needs `agtermctl` installed by the cask or the Help action: a machine merely
running agterm has no CLI an ssh command can find, and the read fails with exit 127.

`agtermctl zmx attach HOST SESSION`, open one of those sessions here, marked remote, in the current
window's current workspace, selected, with the remote session's split when it has one. `SESSION` is the
`id` from `zmx tree`, never the name: remote names are editable and repeat across workspaces. Returns the
new local session's `id`; read `remoteHost` on its tree node. The remote is resolved AGAIN before anything
is created, so a session that has gone since the listing fails and creates nothing. Everything reported
here is a failure found before that point, a connection that starts and later drops is an ordinary pane
exit, which holds on Ghostty's press-any-key prompt under one line naming the host, the session, the pane
and the exit status.

Closing a remote session here ends only this side's connection: the far-side processes keep running and
nothing agterm does from this end can kill them. It is never written to disk, so it does not come back
after a relaunch whatever the restore mode is.

Both commands run ssh non-interactively (`BatchMode`), so key-based auth must already work for the host,
a password or host-key prompt is a failure, not a question. An attach joins as a follower and pinned zmx
keeps one leader per pane, so the pane arrives at the OTHER machine's window size and drops input until
the first CLASSIFIED key (a printable character, Return, Tab or Backspace) takes the lead and reflows
it. Until then the mouse, focus reporting and Ctrl-L do not reach the far side, so a mouse-driven TUI looks
dead, and an ordinary control key may not wake it. Because the lead is per pane, typing in one half of a split leaves the other at the
remote's geometry, and after the session closes the far side keeps that size until something there resizes
it.

Every zmx command needs a running agterm: only the app can join its live windows, its pending closes and
its persisted snapshots against what zmx reports. With agterm stopped there is nothing to ask.

Which programs are NOT re-run is controlled by `restore-denylist.conf` in the config directory (one
command name per line, seeded with the terminal multiplexers `tmux`/`screen`/`zellij`). It is a plain
user-edited file read at launch, there is no control command for it. Two more things are skipped
whatever the denylist says, and the pane starts a plain shell. A control character in the command's
name or any argument: the restored line is typed, so the line editor reads that byte as an editing key
rather than as text. A byte sequence that was not valid UTF-8: it is captured lossily, so replaying it
would run an argument the process never had.

For a PER-SESSION, per-pane override that pins (or suppresses) what a pane restores, use
`session restore` (in the session section above): it wins over the captured foreground, bypasses the
denylist, and is what a `SessionStart` hook rewrites to reattach a non-idempotent command. `restore clear`
here is app-global and touches only the captured commands, not those overrides.

## version

`agtermctl version`, which agterm is serving this socket. App-global: no target, no `--window`, and no
window need be open, so it works as a preflight from a keymap-launched script. Returns `result.app`:

- `version`, the app's version, the number a cookbook recipe's minimum is compared against.
- `commit`, the build's git commit, omitted when the build recorded none. Diagnostics only; never part
  of a version comparison.

Human output is `version` alone, or `version (commit)`, followed by a `client:` line naming the resolved
path of the `agtermctl` that ran, a diagnostic for a stale CLI earlier on `PATH` than the app's bundled
helper. That line is human output only: `--json` stays the raw server response, and a caller that needs
the client path resolves the binary it invoked itself.

Address the socket explicitly when the answer must be about THIS session's app: `agtermctl` never reads
`AGTERM_SOCKET`, so a bare call resolves the default path and may report a different instance. Use
`--socket "$AGTERM_SOCKET"` from a session shell and `--socket "$AGT_SOCKET"` from a keymap- or
palette-launched child.

The same identity is on the `tree` top level as `app`, so an agent already reading the tree needs no
second call. In a session shell `$TERM_PROGRAM_VERSION` carries the same number, but it is ABSENT in a
process launched from the keymap or the palette, which inherits the app's launch environment rather than
a terminal surface's.

## Errors you may see

`notFound` / `ambiguous` (target resolution), `no such session`, `invalid split mode` /
`invalid scratch mode`, `session has no split` (focus, restore, or HUD update), `no selection` (copy),
`overlay already open` /
`no overlay` / `overlay still running` / `no overlay result` / `pane overlay already open` /
`pane not visible` (pane overlay or HUD open),
`no hud` (session hud update/close with none up) /
`hud pane must be left or right` (a HUD pane ID resolved to scratch) /
`no overlay result: the slot holds a hud` (session overlay result over a HUD) /
`a hud is always floating: pass --size-percent, not --full` (session overlay resize over a HUD) /
`session.hud.open requires a message` (also for a blank one) / `session.hud.update requires a message` /
`hud text must not contain control characters` /
`hud message too long (max 256 characters)` / `hud detail too long (max 256 characters)` /
`session.overlay.open: --size-percent must be 1...100` /
`session.overlay.resize: --size-percent must be 1...100` /
`session.hud.open: --size-percent must be 1...100` /
`hud helper is not bundled in this build` / `could not write the hud message` /
`invalid position: <value> (top-left|top-center|top-right|center-left|center|center-right|bottom-left|bottom-center|bottom-right|top|bottom)`
(session hud over the raw socket; the `agtermctl` CLI rejects the same value locally with
`position must be one of: top-left, top-center, top-right, center-left, center, center-right, bottom-left, bottom-center, bottom-right, top, bottom`),
`invalid text color: <value> (#rrggbb)` (session hud; the CLI rejects it locally with
`text-color must be a #rrggbb hex value`),
`invalid spinner: <value> (bar|braille|circle|blocks|dot|none)` (same split: the CLI rejects it locally with
`spinner style must be one of: bar, braille, circle, blocks, dot, none`),
`invalid flag mode` (session flag),
`invalid fit` / `invalid position` / `invalid opacity` / `invalid color` / `text too long` /
`unsupported image (PNG or JPEG only)` / `no such image file` / `image path must not contain control characters` / `invalid background mode` (session background),
`invalid sidebar mode` (sidebar),
`invalid focus mode: <value> (on|off|toggle|add)` (workspace focus over the raw socket; the `agtermctl`
CLI rejects the same value locally with `mode must be one of: on, off, toggle, add`),
`invalid workspace filter mode: <value>` (workspace filter over the raw socket; the CLI rejects it
locally with `mode must be on, off, or toggle`),
`no open window` (quick/sidebar/workspace filter), `quick terminal not open` / `quick terminal not realized` (quick type) /
`failed to read surface buffer` (quick text / session text),
`text must not contain a NUL byte` (session type / quick type),
`invalid restore mode` / `session.restore set requires a command` / `command must not contain control characters` /
`command too long (max 1024 bytes)` / `the scratch terminal is never restored` /
`unknown pane id: <token>` (restore or HUD) /
`failed to save the restore override, the previous value is still in effect` (session
restore; a `session restore --pane right` on a session with no split also returns `session has no split`),
`window not open`
(resize/move/`--window`), `unknown theme: <name>` (theme set), `unknown sound: <name>` (session status --sound),
`invalid color (expected #rrggbb)` (session status --color),
`invalid shape: <value> (circle|square|triangle|diamond|capsule|star)` (session status --shape over the
raw socket; the `agtermctl` CLI rejects the same value locally with
`shape must be one of: circle, square, triangle, diamond, capsule, star`),
`--pane must be left, right, or scratch` (the `--pane` value check; the message intentionally lists the
canonical read-back names while the role and position aliases documented above are accepted. The
`agtermctl` CLI rejects a bad pane with this for session status/type/text/paste, and over the raw socket
`session.status`, `session.restore` and `session.paste` return this same string;
`session.type`, `session.text` and `font.*` over the raw socket instead return `invalid pane: <value>`),
`blocked status owned by pane <pane> (write from that pane to change it)` (session status,
the pane-precedence refusal, the one `session status` error a well-formed call can hit, so retry from the
owning pane rather than treating it as a bad argument). Unknown commands fail to decode and return a structured error, never a crash.
