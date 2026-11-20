## tree

`agtermctl tree [--json] [--window W]`, the workspace/session tree. Each session node:
`id`, `name`, `cwd`, `title` (the raw OSC terminal title, e.g. a remote host over SSH, omitted
when none reported; distinct from `name`, the derived sidebar label), `active` (selected),
`split` (split SHOWN side by side, the read side of `session split on|off`),
`realized` (whether the session's MAIN pane has a live terminal, `false` means no shell was spawned and a
`--command` has not run. `session text` then answers `session not realized` without realizing anything;
`session type` brings up a restored main pane still waiting its turn in a launch that replays commands,
while any other unrealized cause can still exhaust its poll and fail the same way; `session search`
expedites such a pane too.
`session new` returns `ok` for a session that exists in the model, which is not the same thing: libghostty
refuses to create a surface while the DISPLAY is asleep, so a session a scheduled job creates overnight
stays unrealized until the displays wake, at which point it recovers on its own. A queued right pane shows
nothing here. Poll this after creating a session unattended; `agtermctl tree` also tags the row
`(not realized)`),
`backedByZmx` (true only when every existing primary/split pane is currently zmx-backed; older servers omit
it),
`remoteHost` (the machine an attached session came from, the read side of `zmx attach`; omitted for a
local session, and never present after a relaunch because a remote session is never written to disk),
`hasSplit` (whether a second pane exists at all, shown or hidden with ⌘D; omitted when there is none,
read THIS to decide whether a session has a split, because a hidden split reports `split: false` while
its pane stays alive, and it is present exactly when `splitRatio`/`splitFocused` can be),
`splitAxis` (`vertical` for left/right or `horizontal` for top/bottom; omitted when there is no split),
`splitRatio` (the primary-pane fraction 0.05-0.95 of the area below the titlebar, left or top, of a
session that HAS a split,
shown or hidden; omitted when there's no split, or while the split has never been shown, a shown split
always reports a value, 0.5 when nothing set one), the read side
of `session resize`, record it to restore the exact divider position),
`splitFocused` (which pane holds focus in a session that HAS a split: `true` = the split/right/bottom pane,
`false` = the primary/left/top pane; omitted when there's no split; the read side of `session focus`, record it
to restore focus via `session focus left|right`),
`commandWait`/`splitCommandWait` (whether either pane's `--command` was created with `--wait` to hold open
after exit, the read side of `session new --wait`; each omitted for a plain or non-holding pane),
`overlay` (overlay shown),
`overlaySizePercent` (an open overlay's size, the
floating panel's percent of the pane, 1–100; omitted = a full-pane overlay or no overlay, so gate on
`overlay` first; the read side of `session overlay resize`, e.g. record it before switching to `--full`
to restore the exact size),
`paneOverlays` (the panes covered by their own pane-scoped overlay, `["left"]`, `["right"]` or
`["left","right"]`, omitted when neither is; the read side of `session overlay open --pane`, reported
independently of the session-wide `overlay` flag, which a pane overlay never sets),
`hud` (the message panel occupying the session-wide overlay slot, the read side of `session hud`; omitted
when none is up. A
`{message, detail?, spinner, backgroundColor?, textColor?, sizePercent?, heightPercent?, position, pane?}`
object: `detail`, `backgroundColor` and `textColor` are omitted when the caller set none, `sizePercent` is the EFFECTIVE
10–80 share of the pane's WIDTH the panel takes (the app's measurement of the message, or the caller's
`--size-percent` override, either way bounded so a message never covers the session; always present for a
live HUD), `heightPercent` is the effective share of its HEIGHT, always measured from the message's rows
and never set by a caller, and `position` and `spinner`
always report the effective value, `center` and a static panel's `none` included, so a caller who omitted
them never has to know the defaults. `position` always names one of the nine CANONICAL anchors, so a caller
who sent the `top`/`bottom` alias reads `top-center`/`bottom-center` back. The two colors differ in
lifetime: `backgroundColor` is what the panel was CREATED with and survives every update, while `textColor`
tracks the latest update. `spinner` names the STYLE, a string, so a static panel reads back as
`"none"` rather than `false`. A pane-scoped HUD also reports its target identity's current role as `pane`;
session-wide placement omits it. `hud` and `overlay` are mutually exclusive because they share one slot, and a HUD reports `overlay`
FALSE with `overlaySizePercent` omitted, so a poll for "is a program covering this session" cannot mistake
a message for one. No event announces a HUD; poll `tree` for it),
`scratch` (scratch shown), `flagged` (in the
flagged working-set), `context` (what the session is about, the `session context` value, persisted and
omitted when unset), `status` (the agent-status, `active`|`completed`|`blocked`, omitted when
idle), `statusPane` (which pane set that status, `left` (main) | `right` (split) | `scratch`, the
`--pane` value from `session status`, omitted when unset or idle; gated on the same non-idle condition
as `status`, so it is never reported without a `status`), `statusBlink` (`true` when the status glyph is
set to blink, the `--blink` value; omitted when idle or not blinking), `statusColor` (the `#rrggbb`
glyph-tint override, the `--color` value; omitted when idle or using the configured color) and
`statusShape` (the glyph silhouette override, the `--shape` value, one of
`circle`|`square`|`triangle`|`diamond`|`capsule`|`star`; omitted when idle or using the configured shape.
Like `statusColor` it reports the PER-CALL override only, so a shape picked in Settings reads back as
absent), `statusChangedAt` (when the status was last SET, in epoch seconds, the same clock an event's
`ts` carries, so the two compare directly; omitted when idle. It is stamped on every ACCEPTED non-idle
`session status`, a call refused by the pane-precedence rule below stamps nothing, not only on a
change of state, so a hook re-pushing `active` refreshes it and
`now - statusChangedAt` reads as how long ago the status was last WRITTEN, the age of the glyph.
Normally that write is the agent's own push; a pane promotion re-tags the indicator and also counts.
Ephemeral like `unseen`: never persisted, so it is absent after a restart even for a restored session),
`foreground`/`splitForeground` (the live argv of each pane's foreground
process, what it is running, omitted when the pane sits at its shell prompt, and also for a
setuid/setgid foreground process like `top` or `sudo`, whose argv macOS refuses to expose),
`foregroundShell`/`splitForegroundShell` (the shell HOLDING each pane's foreground as a basename, `zsh`,
`fish`, present exactly when that pane's `foreground` is omitted because a shell holds it. For a pane that
EXISTS, both omitted together means agterm could not read the process, which is how you tell "a shell has it"
from "cannot tell"; check `hasSplit` before reading the split pair, since a session with no split omits both
simply because there is no pane. It is NOT a claim the pane is at a prompt and NEVER permission to type: a
builtin like `read` runs inside the shell, so a pane blocked on input is indistinguishable from an idle one.
A shell agterm does not recognize, outside its known set and your `$SHELL`, reports in `foreground` like any
other program),
`restoreCommand`/`splitRestoreCommand` (each pane's persisted restore-command override, the read side of
`session restore`: omitted = no override (auto-capture), `""` = pinned to nothing (a plain shell), a
command string = the shell line that runs on the next launch; reported from persisted state, so a read
after the override already fired still reports what is pinned), `background` (the
background spec set via `session background`, a `{kind, text?, imagePath?, colorHex?, opacity?, fit?,
position?, repeats?}` object; `kind` is `image`/`text`/`color`, omitted when none is set), `unseen`
(the unseen-notification badge count, raised by `notify`/OSC 9/777, cleared by `session seen`, omitted
when zero), `fontSize`/`splitFontSize`/`scratchFontSize` (the LIVE font size in points of each pane,
the read side of `font --pane`; each omitted when that pane isn't realized. `fontSize` tracks the
default/left target (the main pane, or the promoted split survivor once the primary exits, the same pane
`font --pane left` writes); only the main pane's size survives a relaunch, so the split/scratch sizes and a
promoted survivor are live-only, read them back here rather than from the snapshot), and `surfaces` (array
of `{id, kind, active, visible, backedByZmx?}` where `kind` is
`left`|`right`|`scratch`|`overlay`|`overlay-left`|`overlay-right`).
Primary/split surfaces report `backedByZmx`; scratch and overlays omit it.
The surface `id` is the address for `surface zoom`; hidden-but-alive split/scratch surfaces are included
so a script can zoom them without changing split/scratch visibility first. Caveat: `active`/`visible`
derive from the session's own flags, not from zoom, and `visible` reads false for a pane behind a
FLOATING overlay even though it is visually on screen; address by `id`/`kind`, and read the zoom state
from the top-level `zoomedSurface`. Workspace nodes carry
`id`, `name`, `active`, `sessions`, `focused` (whether this workspace is a MEMBER of the sidebar's focus
set, the read side of `workspace focus`, distinct from `active` the SELECTED workspace; omitted on
non-members, and absent entirely when nothing is marked. Membership is reported INDEPENDENTLY of whether
the filter is applied, so a marked-but-not-filtering set reads back too; a workspace ROW RENDERS in the
sidebar iff `sidebarVisible && sidebarMode == "tree" && (!workspaceFilter || focused)`, every term on the
same tree response, the sidebar hidden renders nothing, `flagged` mode renders a flat flagged-session
list with NO workspace rows whatever the filter says, `tree` mode with the filter OFF renders the whole
tree regardless of membership, and only `tree` mode with the filter ON narrows visibility to the
members), and `collapsed` (whether this workspace is COLLAPSED in the sidebar tree, the read side of
`workspace collapse`/`workspace expand` and `workspace new --collapsed`; `true` when collapsed, omitted
when expanded, so an all-expanded tree carries no `collapsed` keys).

The tree object itself carries fourteen top-level read-only fields: `idleMs` (milliseconds since the last
user input in the window, omitted before any activity), `autoFollowMs` (the window's Auto-follow
timeout in milliseconds, omitted when the setting is Disabled), `sidebarVisible` (whether the
window's sidebar is currently shown, the read side of the write-only `sidebar` command, so a script
can restore it, e.g. a tmux-style zoom that hides the sidebar and must re-show it only when it was
visible before), `sidebarMode` (`tree` or `flagged`, the sidebar view mode, the read side of
`sidebar mode`), `sidebarWidth` (the sidebar divider position in points, the read side of
`sidebar width`, reported here and nowhere else), `workspaceFilter` (whether the window's workspace focus filter is currently APPLIED,
the flag half of the focus set, whose member half is each workspace node's `focused`; the read side of
`workspace filter`, so a script can record the filter state, restore it, or make the toggle idempotent),
`quickVisible` (whether the quick terminal is currently shown, the read
side of the write-only `quick` command, so a script can make the toggle idempotent; it is app-level, so
every window reports the same value), `zoomedSurface`
(the control id of the surface terminal zoom currently fills the window with,
`surface:<session-id>:<kind>` or `quick`; omitted when nothing is zoomed, the read side of the
write-only `surface zoom` command, so a script can check "is it already zoomed" and
record-then-restore. `quick` is app-level and independent of any window's zoom, and it WINS: with the
panel zoomed this reports `quick` even while that window's own session zoom is armed and rendering, so
record-then-restore must read it BEFORE zooming the panel, not after), and the four read sides of the write-only `dashboard` command (all omitted when
no dashboard is open): `dashboardMembers` (the pane refs the open dashboard shows, in grid order,
`<session-id>:left` for a primary pane, `<session-id>:right` for a split pane, so a split session appears
as both), `dashboardHighlighted` (the highlighted cell's pane ref, the one Enter jumps into, focusing
that exact pane), `dashboardFontSize` (the absolute font size in points applied to the cells, omitted when
the mode is `untouched`), and `dashboardFontMode` (`auto` for `--auto-size`, `fixed` for `--font-size`, or
`untouched`), plus `pickPending` (the id of the native picker currently awaiting an answer in this
window, omitted when none is pending), and `app` (which agterm is serving this socket: `version`, plus
`commit` when the build recorded one, the same value `agtermctl version` returns, so an agent already
reading the tree gets its version floor without a second round-trip; it is not duplicated onto
`window.list`, where a caller uses `version` instead). `idleMs` is live
and grows while the window is idle, so it is on `tree` only, never `window.list`; `sidebarVisible` is on
both; `sidebarMode`, `sidebarWidth`, `workspaceFilter`, `quickVisible`, `zoomedSurface`, the four
`dashboard*` fields, and `pickPending`
are `tree`-only (a GUI/keyboard change would leave a cached copy stale). All of those are read-only
projections of live GUI state. `app` is the one CONSTANT among them, and is absent from `window.list`
for a different reason: it describes the serving app rather than a window, so repeating it on every row
buys nothing. A caller with no tree uses `version`.

## workspace

- `workspace new [name] [--collapsed] [--window W]`, create a workspace; returns its id. Name defaults
  to an auto-generated one. `--collapsed` creates it CLOSED in the sidebar tree so a script can build a
  workspace and fill it with `session new --no-select` without it ever opening (a fresh workspace is
  expanded by default), and for the same reason a `--collapsed` create is kept OUT of the workspace focus
  set, it never widens a marked working set. A PLAIN `workspace new` while the filter is applied JOINS
  the marked set instead, so a foreground create is visible rather than hidden behind the filter (the
  same auto-reveal the GUI's New Workspace button has). Read the state back from the tree workspace
  node's `collapsed` flag, and the membership from its `focused` flag.
- `workspace rename <name> [--target] [--window W]`.
- `workspace delete [--target] [--window W]`, keep-at-least-one; deleting the last workspace errors.
- `workspace select [--target] [--window W]`.
- `workspace go --to next|prev [--window W]`, step the CURRENT workspace one place through the
  sidebar's visible order, wrapping at both ends, and select the workspace it lands on. Relative, so it
  takes NO `--target`; `workspace move` is the neighbouring verb that REORDERS a workspace instead.
  Landing selects that workspace's FIRST session, exactly as `workspace select` does. Returns the
  workspace id. A workspace's COLLAPSED state does not affect it, a folded workspace is stepped into
  like any other. While the focus filter is applied, stepping is confined to the marked workspaces, the
  same scoping `session go` gets. Errors with `no other workspace to navigate to` when there is nowhere
  to step: the flagged flat list (which renders no workspace rows), or a single visible workspace.
- `workspace move --to up|down|top|bottom [--target] [--window W]`, reorder among siblings. Missing
  or invalid `--to` errors. Note: `--target active` resolves to the current workspace, a
  foreground-created workspace that still holds the target, else the selected session's, else
  the last one; address a specific workspace by id to step the same one.
- `workspace focus [on|off|toggle|add] [--target] [--window W]`, mark or unmark ONE workspace in the
  sidebar's focus SET; returns the workspace id. The sidebar renders the marked workspaces when the
  filter is applied, all of them when it is not. `on` sets the marked set to just this workspace and
  APPLIES the filter (the single-workspace zoom); `off` removes it, and the filter switches off once the
  set empties; `toggle` (the default) replace-toggles, it clears when the set is exactly this workspace
  and the filter is applied, else sets the set to just this workspace and applies it; `add` inserts it
  into the set leaving the filter flag EXACTLY as it was. `add` never switches the filter on: that is
  what makes a multi-workspace set buildable, since a mark that narrowed the tree would hide the rows
  still to be marked, so mark several and apply once with `workspace filter on`.
  Per-window and persisted; orthogonal to `sidebar mode` (the flagged flat list ignores the filter).
  While the filter is applied, `session go` navigation is scoped to the marked workspaces' sessions (and
  to the flagged set in flagged mode); an explicit `session select` of a session outside the set switches
  the filter OFF while KEEPING the set, so re-applying it costs one `workspace filter on`.
  That reveal is TREE-MODE ONLY: the flagged list is cross-workspace and ignores the marked set, so
  selecting an off-set session there leaves the filter applied.
  The converse also holds for the commands listed below, and it MOVES THE SELECTION: when one of them
  leaves the selected session invisible, the most recently used session still visible is selected instead,
  read back as `active` on `tree`. The transitions that do it: `workspace focus on` and a narrowing `toggle`; a
  `workspace focus off` that drops the selected session's workspace while the remaining members keep the
  filter applied; `workspace filter on`; both `sidebar mode` flips; and `session flag off` on the selected
  session while the flagged view is up and other flagged sessions remain.
  A visible set with NO sessions is the one exception, nothing to move to, so the selection stays. The
  same commands repair it, so `session flag on` into an empty flagged view and `workspace focus add` of a
  populated workspace while the marked set holds only empty ones both move the selection despite widening,
  provided something was selected at all; a window restored with no selection stays unselected.
  `session flag clear` never does (it empties the list), and neither does `session new --no-select`, so
  the view can hold a row with nothing selected until one of the listed commands runs.
  Nor does a plain `session new` or a `session select` in FLAGGED mode: both make the fresh or chosen
  session active while the flagged view renders no row for it, leaving the sidebar unselected.
  A script that changes what is visible should re-read `tree` before using the default `active` target.
  A workspace
  created while the filter is applied joins the set, so it is visible without breaking the filter, except
  a `workspace new --collapsed` (or a `session new --no-select --create-workspace`), whose whole point is a
  quiet background build.
  Read membership back from the tree workspace node's `focused` flag. An unknown mode errors.
- `workspace filter [on|off|toggle] [--window W]`, apply or suspend the whole window's workspace focus
  filter WITHOUT touching the marked set, so peeking at the full tree and coming back costs one call each
  way. Window-scoped: it takes NO `--target` (it flips the window's filter, not one workspace's
  membership), and `--window` picks the window like `sidebar expand`/`sidebar collapse`, defaulting to
  the frontmost. `toggle` is the default; idempotent (delta-computed); an unknown mode errors, and
  `no open window` when none is open. `on` with an EMPTY marked set is REFUSED, it returns ok having
  changed nothing, which is what keeps the filter term of the row-visibility contract exact:
  `workspaceFilter == true` with nothing marked cannot occur, so an applied filter always has at least one
  visible member (the full predicate, including the sidebar-mode term, is on the `focused` field above).
  Read it
  back from the tree top-level `workspaceFilter`. The GUI half is the sidebar's bottom-bar grid button
  (filled while applied, disabled with nothing marked), View ▸ Toggle Workspace Filter, the ⌃⇧P palette
  entry, and the `toggle_workspace_filter` keymap action.
- `workspace collapse [--target] [--window W]`, collapse ONE workspace's subtree in the sidebar tree
  (hide its sessions); returns the workspace id. The per-workspace counterpart of `sidebar collapse`
  (which collapses ALL but the active workspace), this targets exactly the addressed workspace and does
  not depend on which one is active. Idempotent. Persisted. Read back from the tree workspace node's
  `collapsed` flag.
- `workspace expand [--target] [--window W]`, expand ONE workspace's subtree (show its sessions);
  returns the workspace id. The inverse of `workspace collapse`, and the per-workspace counterpart of
  `sidebar expand`. Idempotent. To TOGGLE a workspace, read its `collapsed` flag off `tree` first, then
  call `expand` or `collapse`.

