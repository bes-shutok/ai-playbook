## sidebar

`agtermctl sidebar [show|hide|toggle]`, show/hide the frontmost window's workspace/session sidebar
(the custom split has no system toggle). `toggle` is the default; an unknown mode is an error, and
`no open window` when none is open. The GUI half is the title-bar button, View ▸ Show/Hide Sidebar,
the ⌃⇧P palette "Toggle Sidebar", and the ⌃⌘S keymap action (`toggle_sidebar`).

`agtermctl sidebar mode [tree|flagged|toggle]`, flip the frontmost window's sidebar VIEW between the
workspace tree and the flat flagged working-set list (the durable per-session `flag`; each flagged row
is labeled `session : workspace`, even across workspaces). `toggle` is the default; idempotent
(delta-computed); an unknown mode is an error, and `no open window` when none is open. Persisted
per-window. While in `flagged` mode, `session go` navigation (and the Ctrl-Tab MRU switcher) is scoped
to the flagged sessions only; back in `tree` it spans the marked workspaces' sessions (while the focus
filter is applied) or all sessions. The GUI half is the bottom-bar flag button, View ▸ Show Flagged / Show All, and the
⌃⇧P palette. Use with `session flag` to build and view a cross-workspace working set.

`agtermctl sidebar expand [--window W]`, expand every workspace row in a window's sidebar tree.
Defaults to the frontmost window; `--window` (id / prefix / `active`) targets any OPEN window, so a
script can expand a background window's tree. Idempotent (a clean no-op when all are already expanded);
a graceful no-op in `flagged` mode (no workspace rows); a named-but-closed window errors, and `no open
window` when none is open. The GUI half (frontmost only) is View ▸ Expand Workspaces and the ⌃⇧P palette
"Expand Workspaces".

`agtermctl sidebar collapse [--window W]`, collapse every workspace EXCEPT the current one (the same
resolution as `--target active`), which stays expanded and is scrolled into view. Same `--window`
selector and defaults as `expand`. Idempotent; a graceful no-op in `flagged` mode; a named-but-closed
window errors, and `no open window` when none is open. The GUI half (frontmost only) is View ▸ Collapse
Workspaces and the ⌃⇧P palette "Collapse Workspaces".

`agtermctl sidebar width <points> [--window W]` sets the sidebar divider position in points, the one
thing the divider drag does that had no command. Clamped server-side to the same 160...560pt range the
drag enforces, persisted through the window snapshot, and ECHOED: the command prints the STORED width,
so an out-of-range request reads back as the bound it landed on rather than as what was asked for. The
echo is the stored value, not a measured on-screen width. Same `--window` selector and defaults as
`expand`. Fractional points are accepted and preserved without rounding, which is why the value is not an
integer: the drag itself writes a fractional cursor x. Compare request against echo NUMERICALLY rather than
as strings - the echo is a Double, so `300` comes back `300.0`. Read back from the tree's top-level `sidebarWidth`;
`window list` does NOT carry it. There is no GUI half beyond dragging the divider.

Terminal width is the window width minus the sidebar width minus a 1pt divider, so widening the sidebar
is how a caller shrinks the terminal below what the window's own minimum width allows. agterm reports no
column count, so a caller fitting an exact number of columns measures its own grid and corrects; do not
expect points to convert to columns without one.

## notify

`agtermctl notify <body> [--title T] [--target] [--window W]`, post a macOS desktop notification
attributed to a session (default: the active session of the frontmost window). `--title` defaults to
the session name. Clicking the banner reveals that session. This is the only app-level way to post a
banner (the terminal's own OSC 9/777 is the other source). Control-native (no GUI/menu equivalent).

The banner is gated by **Settings ▸ Notifications ▸ Show notification banners**; the unseen badge is
not. With banners off the command still succeeds and still raises the badge, but nothing reaches macOS,
so it answers `ok` with an advisory `result.text` (`badge updated, but "Show notification banners" is
off, so no banner was posted`) instead of a bare `ok`. Treat the presence of `result.text` as "no banner
appeared"; a delivered notification carries none. The badge itself reads back on `tree` as `unseen`.

For agentic attention (waiting on input, or a finished result), prefer `session status` over `notify`
and OSC 9/777. The two overlap, either can raise an "I need you" signal, but a notification is a
one-shot banner and badge with no lasting state, while `session status` is a typed, persistent state
(`active`/`blocked`/`completed`) that stays on the row until acted on, is more precise, and drives the
attention list, the title-bar bell, and attention navigation (`session go --to next-attention`). Keep
`notify` for a one-off nudge that needs no follow-up.

## font

`agtermctl font inc|dec|reset [--pane left|right|scratch] [--target] [--window W]`, increase / decrease /
reset the font size of a session pane. `--pane` picks which surface's font to change, like `session type`
and `session text`: omitted or `left` is the main pane, `right` the split pane (errors with `session has
no split pane` when the session has no split), `scratch` the session's scratch terminal (settable even
while hidden). The role and position aliases (`primary`/`top`, `split`/`bottom`) resolve to the same panes.
No `other` value. Only the MAIN pane's size is persisted across relaunch; a split/scratch
pane's font change is live-only, matching a GUI cmd +/- on those panes. Read the resulting size back from
`tree`, `fontSize` (main), `splitFontSize`, `scratchFontSize`, each in points and omitted when that pane
isn't realized.

## keymap

`agtermctl keymap reload`, re-read and apply `keymap.conf`; returns `result.count` = the number of
parse diagnostics (0 = clean). App-global (no `--window`).

`agtermctl keymap list`, the read side of `keymap.reload`. App-global, no target and no args. Returns
`result.keymap`:

- `path`, the `keymap.conf` this came from.
- `actions[]`, every rebindable built-in: `action` (its `keymap.conf` name), `chord` (the resolved menu
  chord in the same kitty syntax the file uses, omitted when the action is keyless or a `map` line left it
  with no menu chord), `alternates[]` (its other binds, the ones a key monitor delivers, omitted when it
  has none), and `overridden: true` when a `map` line moved it off its shipped default. Every action is
  listed, bound or not, so you can also see which chords are free.
- `commands[]`, the custom commands: `name`, and `shortcut` omitted for a palette-only one. A shortcut
  holding alternatives is one `|`-joined string, in the file's own spelling.
- `diagnostics[]`, `line` + `message` per parse problem (`keymap.reload` returns only the count).
- `menu[]`, the key equivalents the menu bar carries: `chord`, the owning `menu`, the item `title`, its
  `selector`, and `enabled: false` when the item is disabled. agterm's own items report `menuAction:`;
  anything else is an AppKit-supplied item. Nested submenus are included, attributed to their top-level
  menu. A disabled item's chord is INERT, AppKit consumes the key and fires nothing, including a
  same-chord sibling, so an entry marked `enabled: false` explains a dead binding by itself.

**`actions` and `menu` can disagree, and that is what this command is for.** SwiftUI rebuilds the menu
only on the next app activation, so right after `keymap reload` a chord can be correct in `actions` and
stale in `menu`. It also resolves a chord collision by unbinding agterm's own item, so a stock item can
end up holding a chord an action claims. If a keybinding "does not work" while `actions` looks right,
compare the two lists: find the action's `chord`, then look for that chord in `menu` and check which
item carries it.

Two built-ins are legitimately absent from `menu`, both delivered by a key monitor rather than a menu
item: `undo_close` (⌘Z by default), so native text undo keeps working in the rename, palette and Settings
fields, and `toggle_fullscreen` (⌃⌘F by default), because agterm ships no full screen menu item, macOS
adds its own, carrying `fn+f`. Their missing menu entries are expected and not a fault. So is an
`alternates` entry: only an action's `chord` can reach the menu bar.

Menu chords use the same vocabulary as the file (`cmd+opt+up`, `cmd+shift+return`), so the two lists
compare as plain strings. One exception: the globe/fn modifier prints as `fn+`, which no `keymap.conf`
line can express, such an item is AppKit's own and never matches an action.

### keymap.conf format

The file lives at `<config dir>/keymap.conf` (default `~/.config/agterm`; the dir is set in Settings ▸
Key Mapping). Three verbs, line-based; blank lines and `#` comments ignored:

- `map <chord> <action>`, rebind a built-in menu action.
- `command "<name>" [chord] <shell...>`, define a custom shell command, listed in the action palette
  marked `custom`. The quoted name may contain spaces. The post-name token is the chord only if it
  parses AND carries a modifier (a bare modifier-less key is rejected). A custom chord may be a leader
  sequence (chords joined by `>`, e.g. `ctrl+a>g`). No chord → palette-only.
- `global-hotkey <chord>`, bind ONE system-wide chord that summons the quick terminal while any
  application is frontmost. Unset unless the line is present. Exactly one chord: no alternatives, no
  leader sequence, and it must carry a modifier. A second line replaces the first. macOS registers it
  by physical key position, so it survives a layout switch. It is registered with the OS rather than
  agterm's own monitor, so it takes NO part in the collision rules below, it may share a chord with a
  menu item, and whichever application is frontmost decides who gets the key.

Either verb's chord token may hold **alternatives** joined by `|`, with no spaces around it (everything
after the first token is the shell line): `map cmd+t|ctrl+space>s toggle_split` fires the action from
either. A built-in's first single-chord alternative the menu can carry becomes its menu shortcut (one that
names a reserved chord or a bare arrow is diagnosed and dropped, and the next single chord takes the slot);
every other alternative, and every alternative of a `command`, is delivered by a key monitor and so must
carry a modifier on its first chord. `global-hotkey` is outside all of this: the OS owns it, and it WINS,
agterm frontmost included, so a chord it shares with a menu action fires the panel and the menu binding
never sees it. A `map` line with no single-chord alternative
(`map ctrl+a>s toggle_split`) leaves the action with NO menu shortcut, its shipped default is gone, not
kept. A malformed alternative rejects the whole line; one that merely breaks a rule or collides with
another binding drops by itself and its siblings keep working. A line left binding nothing at all leaves
the action on the shortcut it shipped with.

A **chord** is modifier words joined by `+` then a base key: modifiers `ctrl`, `cmd`, `opt`, `shift`;
base key is a single character or `tab`/`space`/`return`/`delete`/`left`/`right`/`up`/`down`. A key typed
with Shift is written `shift+<base>` (`shift+/` = `?`, `shift+=` = `+`, `shift+5` = `%`), the base key,
not the shifted glyph. `+`/`>` can't be a bare key token (they are the separators), though those keys are
bindable via `shift+=`/`shift+.`. A `map` line may not bind a bare, modifier-less arrow (`map left …`),
a built-in rides an always-on menu key-equivalent, so a bare arrow would swallow the key everywhere;
any modifier makes it bindable. Some chords are reserved (the Ctrl-Tab switcher, Ctrl-1/2 pane focus)
and cannot be bound.

Custom-command tokens (expanded into the `/bin/sh -c` line, raw, prefer the quoted `$AGT_*` env form
for untrusted content). A remote host can set the session title (OSC) and working directory (OSC 7),
so `{AGT_SESSION_NAME}` and `{AGT_SESSION_PWD}` are as untrusted as `{AGT_SELECTION}`; use the quoted
`$AGT_*` form for any of them:

- `{AGT_SESSION_NAME}` / `$AGT_SESSION_NAME`, the session's display name (the focused pane's terminal title, remote-settable via OSC).
- `{AGT_SESSION_PWD}` / `$AGT_SESSION_PWD`, the working directory of the pane the command fired from;
  the scratch terminal reports the main pane's, since it tracks no cwd of its own.
- `{AGT_SELECTION}` / `$AGT_SELECTION`, the current selection.
- `{AGT_PANE}` / `$AGT_PANE`, the pane the command fired from: `left` (main), `right` (split), or
  `scratch` (the session's scratch terminal). Feed it back as `session type --pane "$AGT_PANE"` to type
  into the very pane the shortcut was pressed in.
- Plus the other `$AGT_*` context vars the runner exports.

Built-in action names for `map` include: `new_window`, `new_workspace`, `new_session`,
`open_directory`, `rename_session`, `duplicate_session`, `close_session`, `reopen_recent`, `undo_close`, `clear_status`, `increase_font_size`,
`decrease_font_size`, `reset_font_size`, `toggle_split`, `toggle_horizontal_split`, `toggle_scratch`, `toggle_sidebar`,
`focus_workspace`, `toggle_workspace_filter`, `quick_terminal`,
`session_palette`, `command_palette`, `custom_command_palette`, `dashboard`, and the navigation actions (`previous_session`, `next_session`,
`first_session`, `last_session`, `previous_attention_session`, `next_attention_session`,
`focus_left_pane`, `focus_right_pane`, `select_theme`). Editing the keymap from a terminal: open
`keymap.conf` in `$EDITOR`, then `agtermctl keymap reload`.

## config

`agtermctl config reload` - re-read and apply the ghostty config; returns `result.count` = the ghostty
config-diagnostic count (0 = clean), counted across ALL config sources, not just the agterm-scoped
`ghostty.conf` (libghostty diagnostics do not record which file they came from), so do not read a
non-zero count as proof `ghostty.conf` is the culprit. App-global (no `--window`). It runs the same path
as the GUI's File ▸ Reload Config menu/palette item, which posts a warning banner on diagnostics.

### ghostty.conf

`<config dir>/ghostty.conf` (default `~/.config/agterm`, next to `keymap.conf`) is the agterm-scoped
ghostty config and the place to put agterm overrides/customizations. It is ALWAYS loaded. The app builds
its terminal config in order, each source overriding the one before: ghostty's bundled defaults, then
your global `~/.config/ghostty/config` (OFF by default, opt in with Settings ▸ General ▸ Use my global
Ghostty config), then `<config dir>/ghostty.conf`, then the values agterm emits from Settings, which
load last and win over matching values in `ghostty.conf`. The current list of those keys is at
https://agterm.com/docs#ghostty. The scoped file is
agterm-only; the standalone Ghostty.app never reads it. agterm is self-contained by default, so a config
written for Ghostty.app does not silently change agterm, put agterm overrides in `ghostty.conf` (e.g.
`macos-option-as-alt = true`); the full reference is at https://ghostty.org/docs/config. Editing it from
a terminal: open `ghostty.conf` in `$EDITOR`, then `agtermctl config reload`.

## theme

The app's out-of-the-box default theme is the bundled **agterm** theme (a fresh install opens on it).
A separate **default ghostty** entry means "no theme", ghostty's own built-in colors (`theme` absent).

`agtermctl theme list`, list the bundled theme names; returns `result.themes` (the names),
`result.theme` (the current plain theme, absent = ghostty's built-in / "default ghostty"), and
`result.sync` with `result.light`/`result.dark` (the per-appearance themes). While syncing,
`result.theme` is absent, the state rides the three sync fields. Human output prints one name per
line with a leading "default ghostty" row, the active one(s) marked `* `; when syncing, a header notes
the light/dark pair and both sides are marked.

`agtermctl theme set [name]`, set and persist the terminal theme app-wide (the same change as Settings
▸ Appearance), per slot:
- `theme set <name>` sets the light/single theme; a dark theme, if set, is KEPT (syncing stays on).
  Omit the name for ghostty's built-in default ("default ghostty"), with a dark theme set, that
  clears BOTH (an unnamed side can't be part of a pair).
- `theme set --dark <name>` sets the dark theme, the terminal then tracks the macOS Light/Dark
  appearance, applying the matching side automatically as the OS switches (the light side seeds from
  the current theme, else `Builtin Light`). `--light <name>` is an alias for the positional name.
- `theme set --dark none` clears the dark theme, tracking stops, the light theme stays as the single
  theme.
The response always echoes the full state (`result.theme`/`sync`/`light`/`dark`). An unknown name
returns `unknown theme: <name>`; a positional name combined with `--light` is a usage error. Human
output prints `ok`. App-global (no `--window`). The GUI's live-preview picker (View ▸ Select Theme…)
is keyboard-only, committing it replaces the CURRENT appearance's side when syncing (the pair is
kept); over the socket `theme set` is the commit, with no preview.

