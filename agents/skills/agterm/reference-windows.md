## window

- `window new [name] [--minimized]`, create and open a window; returns its id. It replies only once
  the on-screen window exists, so an immediate `window resize`/`move` on the returned id works.
  `--minimized` parks it in the Dock right after creating it, and leaves frontmost on a window you can
  still see, for building a set of project windows and ending up on one you are looking at. The window
  is presented briefly before it is parked, so expect it to appear and take focus on its way to the Dock.
- `window list`, `result.windows`, each with `id`, `name`, `open`, `active`, `autoFollowMs` (the
  window's Auto-follow timeout in milliseconds, omitted when the setting is Disabled), and
  `sidebarVisible` (whether that window's sidebar is shown, read from the open window's store, omitted
  for a closed window with no live store), and `geometry` (the open window's live frame `{x, y, width,
  height, display}` in the SAME units `window move`/`window resize` take, `x`/`y` top-left relative to
  `display`, y down, omitted for a closed window; the read side of `window move`/`window resize`, so
  record it, move/resize, then restore the exact frame), plus `fullscreen`, `zoomed` and `minimized`
  (whether the window is in native full screen / zoomed-to-screen / minimized to the Dock, the read side
  of `window fullscreen` / `window zoom` / `window minimize`, so a script can act idempotently; all omitted
  for a closed window). A MINIMIZED window still reports its `geometry`, the frame it comes back to, so a
  re-align script can include one. The `geometry`/`fullscreen`/`zoomed`/`minimized` fields stay current,
  the cache is refreshed when a window moves/resizes/zooms/enters or exits full screen/minimizes or
  restores, so a hand-drag or GUI toggle is reflected without needing another command. (`autoFollowMs`
  still reflects the last cache refresh, since a settings change is rare; and unlike `tree`, `window.list`
  does NOT carry `idleMs`, the live idle metric would freeze in the cache.)
- `window select <id>`, raise it if open, else open it.
- `window close <id>`, close the on-screen window (the bundle is kept; reopen with select).
- `window rename <id> <name>`.
- `window delete <id>`, keep-at-least-one; deleting the last errors.
- `window resize <id> --width W --height H`, frame size in points. The window must be open. The size is
  clamped into `[window min size, the display's visible frame]`, so an oversized or under-min request is
  bounded to fit rather than applied verbatim.
- `window move <id> --x X --y Y [--display N]`, top-left position in points, relative to display `N`
  (default the window's current display; y measured from the display top). The window must be open. The
  origin is clamped so an off-screen request keeps a grabbable strip of the window on the target display.
- `window zoom <id>`, toggle the window between its normal frame and a maximized (fill-screen, NOT
  native fullscreen) frame, via the standard `NSWindow.zoom`. A second call restores the prior frame.
  The window must be open. This is the control half of the double-click-on-header gesture (a plain green-button
  click does native full screen, not zoom, Option-click the green button to zoom); `resize`/`move` are
  control-native, but `zoom` mirrors a GUI action.
- `window fullscreen <id>`, toggle NATIVE macOS full screen (a separate Space, auto-hidden menu bar),
  via `NSWindow.toggleFullScreen`. A second call exits. The window must be open. This is the control half
  of ⌃⌘F (rebindable as `toggle_fullscreen`), View ▸ Enter/Exit Full Screen, and the green
  traffic-light button, distinct from `zoom`, which only maximizes the frame in the same Space.
- `window minimize <id> [on|off|toggle]`, minimize the window to the Dock, or restore it, via
  `NSWindow.miniaturize`/`deminiaturize`. The mode resolves against the window's current state, so `on` and
  `off` are idempotent and only `toggle` (the default) flips. Both positionals are optional and a window
  address is always a hex UUID prefix or `active`, so `window minimize on` is understood as the active
  window. The window must be open, and a window in NATIVE FULL SCREEN is rejected
  (`cannot minimize a full-screen window — window.fullscreen it first`) because AppKit no-ops miniaturize
  there. Restoring puts the window back on screen without making it key, use `window select` to restore
  and raise in one step. This
  is the control half of ⌘M, the yellow traffic-light button, and the Minimize title-bar double-click
  action. Read back as `minimized` on `window list`. The state is LIVE-ONLY: it is never persisted, so
  every window reopens un-minimized after a restart, and a Dock-icon click restores minimized windows.

`window resize`/`move` are control-native (no GUI equivalent, the title bar already drags-to-resize).

## surface

`agtermctl surface zoom [show|hide|toggle] [--target SURFACE_ID|active|quick] [--window W]`, zoom one
terminal surface to fill the window, hiding the sidebar (a slim title-bar strip with the traffic
lights and an exit button remains). `SURFACE_ID` comes from
`agtermctl tree --json` at `.result.tree.workspaces[].sessions[].surfaces[].id`, for example
`surface:<session-id>:right` for the split pane or `surface:<session-id>:overlay-right` for a pane
overlay covering it. Omit `--target` (or pass `active`) to act on the active surface in the
frontmost or `--window` window. `quick` is the one target that is not a window surface: it grows the
quick-terminal panel to fill its screen instead, takes no `--window`, is refused with `surface not
available: quick` while the panel is hidden, and is never what an omitted `--target` resolves to.
A HUD is not a zoom target: while one is up the
session lists no overlay surface and `surface:<session-id>:overlay` is refused with `surface not
available`, the same answer an empty slot gives.

`show` is idempotent; `hide` exits zoom and is idempotent too (when an explicit id is provided, it
only clears that same zoom target, and succeeds as a no-op even if that surface has since vanished);
`toggle` enters when unzoomed and exits when that surface is already zoomed. Read the current zoom
back from the tree's top-level `zoomedSurface` (the zoomed surface's control id, omitted when nothing
is zoomed). This is NOT
`window zoom`: it does not change the macOS window frame and it must not mutate split ratios, focus,
sidebar state, or split/scratch visibility. Entering zoom does close the window's transient chrome,
an open command palette and an active in-terminal search. The quick terminal is NOT closed: it is a panel
above every window rather than a surface inside one. While zoomed, the hidden deck keeps running: `session.split`/`session.scratch`/overlay
opens on the zoomed session still spawn their shells behind the zoom layer. A notification-banner
click exits zoom before revealing its session. Use `surface zoom` when the user/agent needs a pane
fullscreen inside agterm; use `window zoom` only to maximize the whole window on screen.

`agtermctl surface cursor [--target SURFACE_ID|active|quick] [--window W]`, the surface's zero-based
cursor column, counted from the left edge of the grid. Plain output is the bare number, so
`col=$(agtermctl surface cursor)` works; under `--json` it is `.result.cursor.column`. The target
vocabulary and its refusals are `surface zoom`'s, so an explicit `SURFACE_ID` reads a hidden pane or a
background session as readily as the visible one. It is a pure read: it neither selects nor realizes the
target, and it reports no field in `tree`, so poll it when you need it.

There is no row. The pinned libghostty exposes no cursor accessor and the vertical metrics it does export
cannot recover a row that survives a custom `adjust-font-baseline`; a `row` would join the same `cursor`
object if that ever changes. Treat the column as a one-way signal about the line: past the prompt it
proves the line is NOT empty, at the prompt it proves nothing, because the caret may have been moved back
over text that is still there. Never read "column equals the prompt" as "the composer is empty".

## dashboard

`agtermctl dashboard <ids…> [--font-size N | --auto-size] [--window W]` opens a per-window, view-only
grid of the named sessions' live panes; `agtermctl dashboard --mru [--font-size N | --auto-size]
[--window W]` opens the window's most-recently-used sessions instead of naming ids; `agtermctl dashboard
--close [--window W]` closes the open one. The cell unit is a session+pane: a non-split session is ONE
cell, and a SPLIT session shows as TWO cells, its left/primary pane and its right/split pane. The
positional ids are session addresses (id / unique prefix / `active`), each of which may carry a
`:left`/`:right` pane suffix to place THAT PANE ALONE, the same form `dashboardMembers` reports back, so
`dashboard <a>:left <b>:right` grids one pane per session while a bare id still takes every pane of its
session. The suffix composes with any head, so `active:left` and `<prefix>:right` both work, and it is
case-insensitive. `:primary`/`:top` alias `:left`, and `:split`/`:bottom` alias `:right`; readback remains
`:left`/`:right`. Other suffixes (`:scratch`, `:overlay`, a typo like `:lft`, or a pasted
`surface:<id>:left` zoom address) are rejected and fail the whole
command. Unresolved ids are dropped, including `:right` on a session with no split, which parses fine but
names no pane, and cells are deduped by session+pane, so a bare id beside a pane ref for the same session
collapses instead of double-hosting a surface. A grid that expands to no cells at all is an error and
leaves any open dashboard untouched. The 9-cell cap counts PANES (laid out `ceil(sqrt(n))`), applied after
each session expands into its pane cells: if the panes exceed 9 the first 9 are kept and the dropped-pane
count is reported in the response text (`dropped N pane(s) beyond the 9-cell limit`, appended to any
`unresolved:` note with `; `). `--window` targets a specific window's dashboard (default: the frontmost).
`--mru` draws its members from the window's recency (most-recent first); it is mutually exclusive with
explicit ids and `--close`, composes with the font flags and `--window`, and errors with `no recent
sessions` when the window has none.

A cell placed by a `:right` ref FOLLOWS its pane through promotion: when a split session's main shell
exits, agterm promotes the survivor into the primary slot, and the grid rewrites that cell to `<id>:left`
rather than dropping it, so a dashboard built to watch an agent in the split pane keeps watching it.

The most-recently-used grid also has a GUI opener: **⌘⇧G** (the `dashboard` built-in action, rebindable
in `keymap.conf`), **Navigate ▸ Dashboard**, and the command palette's **Dashboard** entry all TOGGLE the
frontmost window's dashboard: open it over the window's most-recently-used sessions auto-sized (identical to
`dashboard --mru --auto-size`) when closed, close it when open. It is a no-op while terminal zoom is active.
There is no new control command for it, the socket `dashboard` command is unchanged.

It is **view-only**: no cell takes keyboard or mouse input, the whole grid shows live output, and once
open the keyboard drives it. Arrow keys move a highlight between cells (2-D, no wrap; clamped into a
ragged last row), Enter jumps into the highlighted session AND focuses that exact pane (selecting the
session, focusing the primary pane for a `:left` cell or the split pane for a `:right` cell, then closing
the dashboard), and Esc closes it (leaving the selection as it was). Because a cell takes no input, a
program you dashboard keeps running but you cannot type into it from the grid, jump in with Enter first.

Font size is optional and mutually exclusive: `--font-size N` sets an absolute cell font in points
(must be finite and positive), while `--auto-size` sizes the cells relative to the Settings default font
size, shrinking as the grid grows so a dense 3×3 stays readable. Omit both to leave each pane's own
font untouched. The applied size and mode read back on the tree's top-level `dashboardFontSize` /
`dashboardFontMode`; the member pane refs and the highlighted cell read back on `dashboardMembers` /
`dashboardHighlighted` (each a `<session-id>:left`/`<session-id>:right` pane ref).

The dashboard and terminal zoom are **mutually exclusive**: opening a dashboard closes any active zoom,
and a zoom becoming active while the dashboard is open closes the dashboard. Opening (and closing) the
dashboard resizes each pane's pty to (and back from) its cell, so a running program receives a resize
event and may redraw, "view-only" means no input reaches the cell, not that the pane's process is
untouched.

Invalid invocations error (rejected at the CLI and re-checked server-side): `--font-size` with
`--auto-size`, a non-positive `--font-size`, `--close` combined with ids, `--mru`, or a font option,
`--mru` combined with explicit ids, and an open with neither ids nor `--mru`.

## pick

`agtermctl pick [--prompt TEXT] [--query TEXT] [--allow-custom] [--follow] [--window W] [--no-block]`
reads choices from stdin and opens a native fuzzy picker in the target window. `pick` defaults to the open
subcommand, so `agtermctl pick open` is not required. Stdin is read unconditionally, so a call that supplies
no items needs `< /dev/null` or it blocks.

The first non-whitespace input byte selects the format. `[` starts a JSON array of objects with required
`id` and `label` strings plus an optional `subtitle`; any other input is split into lines, blank and
whitespace-only lines are dropped, and each remaining line becomes both the id and label. Item ids must
be unique, labels must not be empty, labels and subtitles may not contain control characters, and a
picker accepts at most 1,000 items. An empty list is rejected with `pick.open requires at least one item`
unless `--allow-custom` is set, which accepts it and opens a plain text prompt. Omitting `items` altogether
is rejected with `pick.open requires items`, reachable only over the raw protocol: the CLI always sends the
list it parsed, empty or not.

The query matches item labels only; a subtitle is displayed but never searched, so consequence text on one
row cannot filter out its safer neighbour. An empty query lists the items in the order the caller supplied
them, so the first item is the one Return runs on open.

`--prompt` sets the query field's placeholder text. `--query` prefills it and filters on open, which ranks
by match score and so does not preserve the supplied order; the seeded text opens selected, so the first
keystroke replaces it rather than appending. `--allow-custom` adds a row for a nonmatching
query and returns it as a custom result; with an empty item list that row is the only possible one, and it
appears as soon as the query is nonblank, prefilled or typed; whitespace and newlines are trimmed first.
A background `--window` target is not raised by default; `--follow` raises it. Only one picker can be
pending in a window, and a second open fails with `pick already pending`.

The default call polls until the user answers and prints one bare JSON result:

```json
{"result":"picked","id":"production","label":"Production","index":1}
{"result":"custom","query":"new target"}
{"result":"cancelled"}
```

Picked and custom results exit 0. Cancellation exits 2. Protocol, validation, transport, and server
failures exit 1. The blocking client polls every 100 ms for the first second, then every 500 ms.

`--no-block` returns immediately with `{"id":"<pick-id>"}`. Use
`agtermctl pick result <pick-id> [--window W]` for a one-shot read; it prints the same bare result JSON,
including `{"result":"pending"}`, and exits 1 while pending. Use
`agtermctl pick cancel <pick-id> [--window W]` to cancel it. Result and cancel require the exact picker
id. Without `--window`, the globally unique id keeps result/cancel pinned to its owning window even if
the frontmost window changes. With `--window`, a live or close-retained result must belong to that
window. A wrong id returns `unknown pick: <id>`.

Read the live picker id from the tree's top-level `pickPending` field. It is omitted after selection,
custom input, cancellation, or window closure. Closing the picker, closing its window, and ⌘W resolve it
as cancelled. App termination cancels in-memory picker state before stopping the socket, but a client
whose next poll races process shutdown may observe a transport failure instead of the final cancellation.
A terminal result stays readable by its own id after the next picker opens in that window, and after the
window closes, including permanent window deletion, so a blocking caller always reads back the answer
it waited for. Results age out oldest-first: the 8 most recent per open window, and 32 across closed ones.

## quick

`agtermctl quick [show|hide|toggle]`, the app's one quick terminal (a single scratch terminal in a
floating panel at 90% of the focused screen up to 1100x700 unless Settings > Interface sets a share of its
own, not in the tree and owned by no window; its
shell stays alive across hides). Errors with `no open window` when none is open, and with `pick pending`
while a picker is up. Read its visibility back from the tree's top-level `quickVisible`.
A panel YOU open with `show` stays up when agterm loses focus, including when it was already visible
because the user had summoned it by hotkey, so a following `quick type` / `quick text` /
`surface zoom --target quick` still finds it. A window's terminal zoom is not a term either way: the panel
floats above every window, so `show` is never refused for it.

`agtermctl quick type TEXT` (or `--stdin`), inject `TEXT` as literal keystrokes into the frontmost
window's quick terminal, the quick-terminal twin of `session type`. There is no `--target`/`--window`
(always the frontmost window's quick terminal) and no `--pane` (a single surface). It polls briefly for
the surface to come up, so `quick show; quick type` back-to-back is reliable (the overlay mounts a beat
after `quick show` flips visibility). Errors with `quick terminal not open` when the overlay has never
been shown, `quick terminal not realized` if a shown surface never comes up in time, `no open window`
when none is open. Typing into a shown-then-hidden quick terminal still works (its shell stays alive).

`agtermctl quick text [--all] [--lines N]`, print the frontmost window's quick-terminal buffer as
plain text (the read-back for `quick type`; does not touch the system clipboard). `--all` reads the
full screen + scrollback, `--lines N` keeps only the last N (mutually exclusive). Polls for the surface
like `quick type`. Errors with `quick terminal not open` (never shown), `failed to read surface buffer`
(shown surface never realized in time), `no open window`.

