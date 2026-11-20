## session

- `session new [--cwd DIR] [--workspace W] [--workspace-name NAME] [--create-workspace] [--command CMD] [--wait] [--name NAME] [--after SID | --before SID] [--no-select] [--window W]`,
  create a session and focus it; returns the new id. `--cwd` sets the start directory (default
  `$HOME`). The destination workspace is addressed one of two mutually-exclusive ways: `--workspace`
  (id / unique prefix / `active`, the default) or `--workspace-name` (the sidebar label), the latter
  errors if no workspace has that name unless `--create-workspace` is also passed, which reuses an
  existing one or creates it when absent (idempotent). `--command` runs that command as the session's
  process instead of the login shell (no echoed command line; the session closes when the command
  exits). It runs argv-style (tokenized, quotes respected, but NO shell), so shell operators (`;`,
  `&&`, `$VAR`, redirects, globs) are not interpreted, and it inherits the app's GUI `PATH` (the launchd
  default, no `/opt/homebrew/bin`), so a bare Homebrew or other non-default binary fails with exit 127.
  Wrap in a login shell for both, `--command "zsh -lc 'htop'"`, or give an absolute path
  (`/opt/homebrew/bin/htop`). All of that describes Fresh shells and Re-run commands. In Live sessions
  mode the command is instead a create-only zmx payload the persistent shell runs as a login shell, so
  shell operators are interpreted, the `PATH` is that shell's rather than the launchd default, and the
  session stays open after the command exits.
  `--wait` (only with `--command`, else an error) HOLDS the session open after the command exits,
  showing libghostty's press-any-key prompt with the final output intact instead of closing immediately,
  so you can read a build/test/deploy's final output or an early failure that would otherwise flash and
  vanish. In Re-run commands mode it persists across restart (unlike an overlay's live-only `--wait`),
  so a restored command session that starts its command again also holds; read it back on `tree`'s
  `commandWait`. Live sessions mode passes the command as a create-only zmx payload, which bypasses the
  1,024-byte PTY input cap. A surviving daemon ignores the payload; a new daemon runs it, then starts the persistent
  shell. The shell stays open when it exits, and `--wait` adds no hold prompt. After a clean quit, a missing daemon
  is recreated running whatever that pane's foreground command was; if the command had already exited, or the
  quit never happened, the pane comes back as a fresh shell.
  The command is persisted (`SessionSnapshot.initialCommand`) and starts again on restore in Re-run commands
  mode; a captured foreground takes precedence over it. Fresh shells mode restores a plain shell. `--name`
  seeds the session's custom name (the sidebar label; blank/omitted leaves the auto basename),
  equivalent to a `session rename` right after create. `--after SID` / `--before SID` place the new
  session directly after / before an anchor session instead of appending at the end (the anchor is a
  session address, id / unique prefix / `active`). The anchor CARRIES ITS OWN WORKSPACE (resolved
  across all workspaces), so it names the destination workspace itself, `--after`/`--before` are
  therefore mutually exclusive with each other and with `--workspace`/`--workspace-name` (the anchor
  already picks the workspace). `agtermctl session new --after active` is the headline case: create
  right after the current session in one round-trip. `--no-select` creates the session in the BACKGROUND:
  it is added to the sidebar but NOT selected or focused, so the current selection and focus are left
  untouched (the new node is not `active` in `tree`, that flag is the read-back); omit it for the default
  select-and-focus behavior. Every other addressing/placement option composes with it, and a background
  `--create-workspace` create does not widen the workspace focus set either (the new workspace stays
  unmarked, so the filtered sidebar view is left put instead of revealing it).
- `session duplicate [--target] [--window W]`, create a fresh session in the SAME workspace as the
  target, inserted directly AFTER it, rooted at the target's focused-pane working directory (the live
  OSC 7 cwd the sidebar row shows and `session reveal` opens); selects + focuses the new session and
  returns its id. There are NO other options, the target session names both the destination workspace
  and the cwd, and `--target` defaults to `active`. It is equivalent to
  `session new --cwd <source cwd> --after <source>` in ONE atomic round-trip.
  ONLY the directory carries over: the duplicate is a plain login shell with the auto basename, and it
  does NOT inherit the source's custom name, `--command`, split, scratch, status, flag, font size, or
  background, it is "new session seeded with the source's cwd", not a clone of state. Errors: the usual
  resolver errors for an unresolvable / ambiguous target, and `could not duplicate session` when creation
  fails. READ-BACK: no new tree field, `tree` itself is the read-back, since the new session node appears
  directly after its source, carrying the source's focused-pane cwd. That equals the source node's
  `tree.cwd` for a non-split session (and a split focused on its primary pane); for a split focused off its
  primary the source node's `tree.cwd` reports the primary pane while the duplicate carries the focused
  pane's directory. It is the control half of the sidebar row's **Duplicate Session** context-menu item
  (single-selection only).
- `session close [--target T ...] [--window W]`, close one session, or repeat `--target` to close
  several sessions in the same window/store. Batch close honors the GUI grace-undo setting: one grouped
  undo/reopen record when enabled, immediate close when disabled. Returns `result.affected`.
- `session select [--target] [--window W]`.
- `session rename <name> [--target] [--window W]`.
- `session reveal [--target] [--window W]`, select the target session's focused-pane working
  directory in Finder. Errors when that directory no longer exists.
- `session go --to next|prev|first|last|next-attention|prev-attention [--window W]`, move the
  selection relative to the CURRENT one (no `--target`). Operates over the VISIBLE/FILTERED set: the
  flagged sessions in flagged mode, the marked workspaces' sessions while the focus filter is applied,
  else all sessions (clearing the flag / suspending the filter restores the full set). next/prev wrap around at the ends (last→first,
  first→last); first/last jump to the ends of that set; next-attention/prev-attention step only through the filtered
  sessions needing attention (status blocked/completed), wrapping. Returns the newly selected id.
- `session move <workspace> [--target] [--window W]`, relocate the session to another workspace
  (appends). OR `session move --to up|down|top|bottom [--target]`, reorder within its workspace. OR
  `session move --after SID | --before SID [--target]`, place the session directly after / before an
  anchor session (id / unique prefix / `active`). The anchor CARRIES ITS OWN WORKSPACE (resolved across
  all workspaces), so it relocates + positions in one shot, wherever the anchor lives, cross-workspace
  placement falls out for free. Exactly one placement intent is required among {positional workspace,
  `--to`, `--after`/`--before`}; `--after`/`--before` are mutually exclusive with each other, with `--to`,
  and with a destination workspace (the anchor already names the workspace).
  Repeat `--target` for a batch move with the workspace and after/before placement forms; the sessions
  move as one ordered block after all sources are removed. Repeated `--target` is rejected with
  `--to up|down|top|bottom` because relative reorder is per-session. Batch moves return `result.affected`,
  counting only sessions whose position/workspace changed.

Shared pane selectors accept `primary`/`left`/`top` for the primary pane and
`split`/`right`/`bottom` for the split pane. Commands supporting scratch also accept `scratch`.
The signatures and read-back below use canonical `left`/`right`/`scratch`; the stable invalid-value
error keeps those names for compatibility.

- `session type <text> [--stdin] [--select] [--pane left|right|scratch] [--target] [--window W]`, inject text
  as real keystrokes (printable runs plus Return for each newline; no bracketed-paste markers).
  `--stdin` reads the text from stdin instead of the argument. Any session is typable without `--select`,
  including a background one and one created moments ago: the main pane bounded-polls (12 × 30ms) for the
  surface, so `session new --no-select` followed straight away by `session type` does not race the mount.
  `--select` selects the session first, and only when its surface is not ready, a realized session is typed
  into without moving the user's selection. A surface that never comes up → `session not realized`.
  Text carrying a NUL is rejected with `text must not contain a NUL byte`, since libghostty's key-text
  field is NUL-terminated and could only deliver the run up to it.
  `--pane left` types into the main pane (the default when omitted), `--pane right` into the split pane
  (errors with `session has no split pane` when the session has no split), `--pane scratch` into the
  session's scratch terminal even while it is hidden (`session has no scratch terminal` when none opened);
  the role and position aliases (`primary`/`top`, `split`/`bottom`) resolve to the same panes; like
  `session text`, no `other` value. `--select` realizes the MAIN pane only, a split pane must
  already exist. Also like `session text`, there is no overlay value: every `--pane` types into the surface
  UNDER a covering overlay, so the keystrokes reach the hidden shell and run there unseen until the overlay
  closes, the call still answers `ok`. That is deliberate: the panes stay drivable whatever is drawn over
  them, so an overlay never has to be closed to keep automation running. It has no read-back twin either,
  `session overlay text` exists because an overlay's output is otherwise unobservable, while its program is
  the caller's own, so there is no way and no need to type into one.
- `session copy [--target] [--window W]`, returns `result.text` with the session's current selection.
  Does NOT touch the system clipboard (pipe the returned text into another `session type`). No/empty
  selection → `no selection` error. Selection is readable on any realized session regardless of focus, but
  always from the main PANE, a selection made in a covering overlay is `session overlay copy`'s, not this
  command's. A never-shown session → `session not realized`, as with `session select-all`.
- `session paste [--pane left|right|scratch] [--target] [--window W]`, paste the system clipboard
  (`NSPasteboard.general`) into a pane of the session, the socket analogue of ⌘V / Edit ▸ Paste. Runs
  libghostty's `paste_from_clipboard` (bracketed paste, no prompt), so the text lands at the prompt without
  auto-submitting. `--pane` (canonical `left`|`right`|`scratch`; role and position aliases above are also
  accepted) picks the pane: `right` is the split pane (`session has no split pane` when there is none),
  `scratch` the scratch terminal even while hidden (`session has no scratch terminal` when none opened);
  omitted and `left` are the main pane, which still reaches a promoted split survivor. An unparseable value
  is `--pane must be left, right, or scratch`, rejected in the dispatcher so a raw socket client gets it too.
  Read it back with `session text --pane` naming the same pane. A never-shown session →
  `session not realized`.
- `session select-all [--target] [--window W]`, select the session's entire terminal buffer (main pane),
  the socket analogue of ⌘A / Edit ▸ Select All (libghostty `select_all`). Read the resulting selection
  back with `session copy`. A never-shown session → `session not realized`.
- `session text [--all] [--lines N] [--pane left|right|scratch] [--pane-id TOKEN] [--target] [--window W]`: returns `result.text`
  with the session's terminal buffer as PLAIN TEXT (no ANSI/color). By default it reads the VISIBLE
  SCREEN of the on-screen pane. `--all` reads the whole buffer including scrollback; `--lines N` reads the
  full buffer and keeps only the last N CONTENT lines (trailing blank rows trimmed; `--all` and `--lines`
  are mutually exclusive and `--lines` must be > 0, enforced server-side too). `--pane left` reads the
  main pane, `--pane right` the split pane (errors if the session has no split), `--pane scratch` the
  session's scratch terminal even while it is hidden (its buffer is kept alive; `session has no scratch
  terminal` when none opened); the role and position aliases (`primary`/`top`, `split`/`bottom`) resolve to
  the same panes; omit `--pane` for the visible pane (the scratch terminal when it covers the
  session, else the focused pane). `--pane-id` accepts the shell's stable `$AGTERM_PANE_ID`, resolves its
  current live slot and overrides `--pane` when found. An absent or unknown token falls back to `--pane`,
  then to the visible pane. Use it for a long-running watcher because `$AGTERM_PANE` is a spawn role and can
  become stale after promotion or `session swap`. NOTE: unlike
  `session focus`, `--pane` here has NO `other` value, only `left`/`right`/`scratch`, and no overlay value:
  every one of them reads the surface UNDER a covering overlay, whose buffer is `session overlay text`'s.
  A genuinely BLANK screen is
  NOT an error (returns `ok` with an empty string, unlike `session copy`'s `no selection`), but a failed
  read IS an error (`failed to read surface buffer`). Pipe the text into `grep`/`fzf` to extract URLs,
  paths, etc.
- `session search [needle] [--next|--prev|--close] [--target] [--window W]`, search the target
  session's live terminal scrollback. Selects the target first (so the search bar and match highlights
  render). With a `needle` it sets the query (opening the bar if needed) and highlights matches; with no
  needle and no flag it just opens the empty bar. `--next`/`--prev` step the selected match;
  `--close` closes the bar (the three flags are mutually exclusive). Returns `result.count` (total
  matches) and `result.text` (the counter string: "N of M", "M matches", or "no matches"); the count
  settles asynchronously, so the command waits briefly for it. Without `--json` it prints `result.text`
  (or `ok` on close / an empty bar).
- `session split [on|off|toggle] [--axis vertical|horizontal] [--target] [--window W]` - second shell.
  `vertical` means left/right and `horizontal` means top/bottom. Omitting `--axis` preserves the current
  axis and keeps the legacy left/right default for a new split. `off` hides but keeps the shell alive;
  tearing it down takes `session split close` or the shell's own exit. Unknown modes and axes error.
- `session split close [--target] [--window W]`, tear the split pane down: the surface dies, whatever it
  runs dies with it, and `hasSplit`/`splitRatio`/`splitFocused` drop out of `tree`. Reaches a HIDDEN pane
  too, which is what `session type --pane right $'exit\n'` cannot do once the pane is past a prompt
  (nested shell, ssh, an agent). Answers ok on a session with no split.
- `session swap [--target] [--window W]`: exchange both terminals' physical positions and primary/split
  roles without restarting either process. Focus follows its terminal; split axis and ratio stay fixed.
  Works when the split is shown or hidden and under zoom/dashboard. Errors when there is no split or a
  surface is not ready. The new primary supplies `tree`'s `cwd`/`title`/`foreground`/`restoreCommand`/
  `commandWait`; the other side supplies `splitForeground`/`splitRestoreCommand`/`splitCommandWait`.
- `session scratch [on|off|toggle] [--command CMD] [--target] [--window W]`, a third, full-coverage
  shell that renders like a full overlay but behaves like the split. `off` hides it keep-alive; typing
  `exit` in it closes it and the next `on` spawns a fresh shell. `on` selects the target first (the
  scratch is full-coverage and owns focus). `--command` (only when showing) runs that program as the
  scratch's process instead of a login shell, argv-style (no shell, and inheriting the app's GUI
  `PATH`, so the same exit-127 caveat as `session new --command`: wrap in `"zsh -lc '…'"` or use an
  absolute path) and RUN-ONCE like `session new --command` (after it exits, the next `on` is a plain
  shell). A scratch is expendable, so passing `--command` while one is already open respawns it. Not
  persisted. Unknown mode errors. The tree's `scratch` flag tracks visibility.
- `session focus [primary|split|left|right|top|bottom|other] [--target] [--window W]` - move keyboard focus between the two
  split panes (`other` toggles, the default). Errors when the session has no split. Works whether the
  split is shown in either orientation or hidden (maximized). When hidden, focusing a pane swaps which one shows.
- `session resize (--split-ratio R | --grow-left D | --grow-right D | --grow-primary D | --grow-split D | --grow-top D | --grow-bottom D) [--target] [--window W]` - move the
  split DIVIDER (the divider is otherwise mouse-only: drag it, or double-click it for an even split. No
  GUI/menu/keymap action reaches any other fraction, so bind a key by mapping a
  `command "agtermctl session resize …"` custom action). Provide exactly one form:
  `--split-ratio` sets the absolute primary-pane fraction of the area below the titlebar (`0..1`, left
  or top). The grow options are
  equivalent role/position aliases: primary/left/top versus split/right/bottom. The result is clamped to
  `0.05..0.95` and persisted, and the applied (clamped) fraction is printed (and returned as `result.ratio`
  under `--json`). Errors when the session has no split. Resizing a hidden split updates the stored
  fraction; it takes effect when the split is next shown.
- `session status <idle|active|completed|blocked> [--blink] [--auto-reset] [--sound NAME] [--color #rrggbb] [--shape circle|square|triangle|diamond|capsule|star] [--pane left|right|scratch] [--pane-id TOKEN] [--target] [--window W]`,
  set the sidebar agent-status glyph. Every ACCEPTED non-idle call stamps the session node's
  `statusChangedAt`, including one that re-pushes the status already showing, so a poller can tell a fresh
  glyph from a stale one without keeping state of its own; a call refused by the pane-precedence rule
  changes nothing, the stamp included. `--blink` requests an attention pulse; macOS Reduce Motion
  suppresses the repeating sidebar and dashboard animation while keeping the status visible, and the
  pulse resumes when Reduce Motion is disabled. `--auto-reset` clears it back to idle once the session
  is visited (use for a one-shot completion flash). `--sound` plays a
  one-shot sound when the status is set: `default` (the system alert sound) or a system sound name
  (`Basso`, `Blow`, `Bottle`, `Frog`, `Funk`, `Glass`, `Hero`, `Morse`, `Ping`, `Pop`, `Purr`,
  `Sosumi`, `Submarine`, `Tink`; also any custom sound in `~/Library/Sounds`), an unknown name errors.
  Without `--sound`, a `blocked` status plays the user's Settings "Blocked sound" if they configured one
  (Appearance ▸ Agent Status; off by default); an explicit `--sound` always overrides it.
  `--color` (`#rrggbb`) overrides the glyph tint for THIS call only, it rides the status, so the next
  `session status` without `--color` reverts to the Settings-configured color (a malformed hex errors).
  Use it to distinguish states beyond the fixed palette (e.g. a caller-specific blocked color).
  `--shape` (`circle`, `square`, `triangle`, `diamond`, `capsule`, `star`) overrides the glyph SILHOUETTE
  the same way, it rides the status, so the next `session status` without `--shape` reverts to the
  Settings-configured shape, else the built-in plain circle (an unknown name errors, listing the six).
  Shape is a second channel alongside the tint, so a session stays distinguishable at a glance and for a
  color-blind user; use it to mark one session for the length of a run.
  The value is read back on `tree` as the session node's `statusShape` (the per-call override only, like
  `statusColor`), and rides the `status` control event's `shape` payload field so an `events` consumer can
  explain a shape-only change.
  A `--shape` on `idle` is accepted and ignored, since an idle session draws no glyph.
  `--pane` (canonical `left`|`right`|`scratch`; role and position aliases above are also accepted) records
  which pane set the status. It has three effects: (1) keystroke-clear becomes pane-scoped, a status set
  from a background pane survives typing in a DIFFERENT pane (so a `right`- or `scratch`-tagged block is
  no longer wiped by foreground typing in the main pane, and only input in the OWNING pane clears it,
  whether typed by hand or sent with `session type`), (2) while the session is `blocked`, a status from
  another pane that is not itself `blocked` is REFUSED with `blocked status owned by pane <pane>`,
  it changes nothing and plays no sound, so an agent working in one pane cannot erase the other pane's
  request for input; a second pane may still report its own `blocked`, `idle` is NOT exempt (Codex's
  `session-start` hook and the shell integration's post-command hook both send it from their own pane),
  and the owning
  pane writes freely, and (3) when the status needs attention (`blocked`/`completed`), any user-initiated GUI selection of
  the session lands on the tagged pane, auto-follow,
  the attention-nav (⌃⌥↑/⌃⌥↓, the Navigate menu), plain session nav (⌥⌘↑/↓/first/last),
  the command palettes, a sidebar row click, and a Dock-menu session row all reveal and focus it, flipping to the split or
  showing a hidden scratch instead of the main pane. An `active` status keeps the existing pane selection.
  (The socket `session go next-attention|prev-attention`
  only STEPS the selection to attention sessions; it does not itself move focus into the tagged pane, the
  reveal is a GUI/auto-follow concern.) An agent that runs in a split or scratch should set its own pane so
  the user lands on it. The value is read back on `tree` as the session node's `statusPane`. An invalid
  value errors with the stable canonical-name message (`--pane must be left, right, or scratch`).
  `--pane-id` is the surface's stable spawn token (the shell's `$AGTERM_PANE_ID`), the agent-status hook
  forwards it automatically. When it resolves against the session's LIVE surfaces it OVERRIDES `--pane`, so
  a status from a pane whose baked role went stale (a split survivor promoted into the main pane, then a
  re-split) lands on the pane's CURRENT slot instead of the stale role; an absent/unknown token falls back
  to `--pane`. Scripts normally set `--pane` directly and leave `--pane-id` to the hook.
  An unknown state errors. Setting non-idle is for agents/hooks; `idle` clears it (also available in the GUI).
- `session flag [on|off|toggle|clear] [--target] [--window W]`, flag/unflag a session for the flagged
  working-set view (a durable, persisted membership). `on`/`off`/`toggle` act on `--target` (default
  `active`) and are idempotent; `clear` ignores the target and unflags every session in the window.
  Pair with `sidebar mode flagged` to see just the flagged sessions as a flat `session : workspace`
  list. Unknown mode errors. The tree's `flagged` flag tracks membership.
- `session context <TEXT|--clear> [--target] [--window W]`, set or clear what the session is ABOUT, shown
  in the title bar, a PR number, an issue, the task in hand. It is set from OUTSIDE the session, so a
  hook or an orchestrator can say what a session it just created is for. Exactly one of TEXT or `--clear`, enforced at parse time and again server-side: a blank
  TEXT is rejected, not treated as a second clear, so `--clear` is the only route to unset. The value is
  trimmed of outer spaces and rejected if empty, over 256 UTF-8 bytes, or carrying any control character or
  line/paragraph separator; a rejected call leaves the previous context standing. It states durable purpose,
  not current activity: it persists across quit, relaunch and restore, and nothing expires it. A duplicated
  session starts without one. A set or clear that CHANGES the value emits `tree.changed`; re-setting the
  same value emits nothing. The tree's `context` field is the read side, omitted when unset. In the title
  bar it takes line two in normal mode (replacing the cwd/terminal-title detail) and follows the session and
  window names on line one in compact mode, where a long value tail-truncates before the names do. Settings
  ▸ Interface ▸ Title Bar ▸ "Session context" hides it without clearing it.
- `session seen [--target] [--window W]`, clear the session's unseen-notification badge without changing
  the selection, focus, or agent status. It is the focus-free counterpart to `notify`: `notify` (and a
  terminal's own OSC 9/777) raise the red badge, and until now the only way to clear it was visiting the
  session. Idempotent, a no-op when the badge is already zero. Read the current count from the tree node's
  `unseen` field. This lets an orchestrator acknowledge a driven session's notifications over the socket
  while keeping the badge a real attention signal on the sessions a human tends.
- `session restore (<command> | --none | --clear) [--pane left|right] [--pane-id TOKEN] [--target] [--window W]`,
  pin the command a pane re-runs on the NEXT launch, overriding the captured foreground. Provide exactly
  one of: a `<command>` shell line to pin, `--none` to pin nothing (the pane restores a plain shell,
  suppressing the captured command), or `--clear` to drop the override and fall back to auto-capture.
  Tri-state, read back on the tree node as `restoreCommand` (main pane) / `splitRestoreCommand` (split
  pane): omitted = auto-capture, `""` = pinned to nothing, a command = the pinned line.
  The override is written NOW and consumed on the next launch, it never touches the running session, and
  it is STICKY: it fires again on every restart until cleared. It wins over EVERYTHING else the pane could
  restore: the captured foreground AND the session's own `session new --command`, which a pinned line (or
  `--none`) suppresses, so a restored `--command` session runs the pinned line instead, as typed input
  rather than the exec path, and its `--wait` close-on-exit behavior no longer applies.
  It runs only in `rerun` mode. In fresh-shell or live mode, a command or `--none` still saves policy for a
  future rerun launch and returns a note in `result.text` naming the active mode; `--clear` works in every
  mode. A pin never opts one session out of live mode. Deliberate pins bypass `restore-denylist.conf`
  (it names its command deliberately, so the denylist is never the reason it does not fire). It is typed
  verbatim as a shell line, so `cd x && claude --resume y` works as written.
  A split hidden at quit keeps its identity and pin; showing it after restart creates the pane and applies
  the saved rerun policy.
  It exists for NON-IDEMPOTENT commands, `claude --resume <id> --fork-session` mints a NEW session on every
  restart, so restoring it verbatim never reattaches the session the user was in. A Claude Code
  `SessionStart` hook that rewrites the override to the live session id on every start makes the next
  restart reattach instead of fork (see examples.md). Ownership flips to whoever sets it: write once and
  forget, and it stays pinned to a stale id, that is the deliberate hook-driven tradeoff.
  `--pane` (default `left`) picks the pane; `--pane right` errors when the session has no split, and
  `scratch` is rejected (`the scratch terminal is never restored`). `--pane-id` (the shell's
  `$AGTERM_PANE_ID`) resolves the pane's LIVE slot, so a hook in a promoted-then-re-split pane still pins
  the right one; UNLIKE `session status`, a token that does not resolve is an error unless `--pane` is also
  given as the fallback (a silent main-pane default here would overwrite the wrong pane).
  Every success names the pane it wrote in `result.pane` (`left`/`right`), which is the read-back for
  `--pane-id`: a token names a surface rather than a role, so without it the caller has to re-read the tree
  and diff `restoreCommand` against `splitRestoreCommand` to find out where the pin landed. Only an app
  predating the field omits it from a successful `session.restore`; treat absence as UNKNOWN, never as the
  default `left` pane.
  The pinned value is SHELL CODE: it persists in the window's state file (`windows/<id>.json`), is readable
  via `tree`, and may enter shell history when it runs, so it must not carry secrets, and only
  safely-interpolated values (a UUID-shaped session id) belong in it. It persists immediately, so a
  force-quit does not lose a hook's write; if that write fails the command answers with an ERROR rather
  than `ok` (the previous override is still in effect and still fires, so re-issue the same request to
  retry). Not to be confused with the app-global `restore clear`, which
  clears every session's CAPTURED foreground command; this is per-session and clears only the override.
- `session background image <path> [--opacity F] [--fit contain|cover|stretch|none] [--position P] [--repeat] [--target] [--window W]`,
  composite the image at `path` (PNG or JPEG only) behind the terminal as a watermark. libghostty
  auto-fits it to the surface and re-fits on every window resize. `--opacity` is 0.0–1.0 (default 1.0);
  `--fit` defaults to `contain`; `--position` is `center` (default) or an edge/corner anchor
  (`top-left`, `top-center`, `top-right`, `center-left`, `center-right`, `bottom-left`, `bottom-center`,
  `bottom-right`); `--repeat` tiles to fill blank space. Errors on a bad fit/position, an out-of-range
  `--opacity` (must be 0.0–1.0), an unsupported format, a missing file, or a path containing control
  characters (the path reaches a ghostty config line, so a newline could inject other keys).
- `session background text <text> [--color #rrggbb] [--opacity F] [--fit ...] [--position ...] [--target] [--window W]`,
  rasterize `text` to a watermark behind the terminal. `--color` defaults to the terminal foreground
  (must be a `#rrggbb` hex value); `--opacity`/`--fit`/`--position` as above. `text` is capped at 256
  characters (a watermark is a word or two).
- `session background color <#rrggbb> [--target] [--window W]`, set a SOLID terminal background color
  (the `background` key, not an image). Takes no opacity: the color is drawn at the Settings window
  translucency (solid when translucency is off; blurred/translucent when on), so it honors your
  opacity/blur instead of forcing the pane opaque like the image/text watermark. macOS Reduce
  Transparency temporarily presents it as opaque and unblurred without changing the saved opacity/blur;
  the requested presentation returns when Reduce Transparency is disabled. Errors on a malformed color
  (must be a `#rrggbb` hex value).
- `session background clear [--target] [--window W]`, remove the session's background.
  Per session (applies to the session's pane(s)); persisted, so it survives a relaunch. An image/text
  watermark makes the pane render OPAQUE, overriding window translucency (an image is invisible at 0
  background-opacity); a `color` instead honors the Settings window translucency. Read the current
  background back from a session's `background` field in `tree --json` (a `{kind, colorHex, …}` object,
  omitted when none).
- `session overlay open <command> [--cwd DIR] [--wait] [--block] [--size-percent N] [--background-color #rrggbb] [--follow] [--pane left|right] [--target] [--window W]`,
  run `command` in an ephemeral terminal on top of the session; it closes when the command exits.
  `command` runs through `sh -c` (so shell operators DO work here) but with the app's GUI `PATH` (no
  `/opt/homebrew/bin`), so a bare Homebrew or other non-default binary fails with exit 127, the overlay
  flashes open then vanishes and `session overlay result` reports 127; give an absolute path or wrap in
  `"zsh -lc '…'"`.
  Full-size by default (hides the session); `--size-percent N` (1–100) makes it a floating framed panel
  with the session visible behind, and a percent outside that range is an error. **By default the
  overlay does NOT switch the active session**, full and floating both open on `--target` and run
  their program in the background, appearing when the user visits that session. **Pass `--follow` to
  select the target after opening** (a no-op if it is already
  active); use it when you want the user pulled to the overlay, omit it to open quietly. `--background-color #rrggbb` gives the overlay pane its own solid
  background color, independent of the session's own `session background color` (nil = the default theme
  background); it honors the Settings window translucency, captured when the overlay opens. `--wait` keeps the overlay open after the command exits (press a key
  to close). `--block` waits for the command to exit and makes agtermctl exit with the command's status
  (cannot combine with `--wait`); the program renders normally, capture its OUTPUT via the program's
  own output file, not the control channel. Returns the overlay's session id. `--target` defaults to
  `active`, so an automated caller should pass `--target "$AGTERM_SESSION_ID"`, otherwise a (usually
  blocking, full-pane) overlay lands on whatever session is currently active, not the calling one.
  `--pane left|right` scopes the overlay to ONE split pane rather than the whole session: it covers
  exactly that pane and leaves the sibling pane visible and interactive. The two panes are independent
  and may both hold an overlay at once, each with its own `--background-color` and `--cwd`. A pane
  overlay is ALWAYS full-pane, there is no floating variant, so `--pane` with `--size-percent` is a
  usage error and `session overlay resize` takes no `--pane`. Everything else matches the session-wide
  overlay: it closes when the program exits, `--wait` holds it open on the press-any-key prompt,
  `--block` blocks and exits with the program's status, and `--follow` selects the target. A NON-SPLIT
  session accepts `--pane left`. `AGTERM_PANE` is the shell's spawn role and may be stale after promotion
  or `session swap`, so a long-running shell must not assume `--pane "$AGTERM_PANE"` still names its slot.
  A pane that is not
  currently rendered is refused with `pane not visible`: a SHOWN split renders both panes, a HIDDEN one
  renders only the FOCUSED pane, so the refused one is the pane without focus, `--pane left` on a
  session whose hidden split holds it, `--pane right` when the main pane does; hiding the split AFTER
  opening is fine, the program keeps running and reappears when the split is shown again. Opening a
  second overlay on the same pane errors `pane overlay already open`. A full session-wide overlay and
  the scratch terminal both cover a pane overlay, and ⌘W dismisses the FOCUSED pane's overlay before it
  would close the session, an overlay on the other pane is not in front of the user, so ⌘W keeps its
  ordinary meaning there. Read the open panes back from `paneOverlays` in `tree --json`.
- `session overlay resize (--size-percent N | --full) [--target] [--window W]`, resize an ALREADY-OPEN
  overlay in place. Exactly one of `--size-percent N` (1–100, makes it a floating framed panel) or
  `--full` (switches it back to the full-pane overlay that hides the session) is required; passing both
  or neither, or a percent outside 1–100, is an error. The overlay program keeps running across the
  resize, it is a layout re-flow, never a re-spawn. Errors `no overlay` when none is open. Returns the
  session id. It has no `--pane`: pane overlays are always full-pane, and passing one errors. Against a
  HUD a percent is accepted and re-flows its WIDTH (the panel re-flows and its `hud.sizePercent` reports the
  new value; `hud.heightPercent` does not move, the text wrapping at a fixed 60 columns rather than at the
  panel) but `--full` is refused with `a hud is always floating: pass --size-percent, not --full`, full size
  would cover the session the message is about. The resize rewrites the body header itself, so the panel
  re-centres on its new grid within a tick, no `session hud update` is needed to correct the placement.
- `session overlay close [--pane left|right] [--target] [--window W]`, close (destroy) the overlay.
  `--pane` closes that split pane's overlay; omit it for the session-wide one. It also takes a HUD down,
  as a courtesy, the slot is the same one.
- `session overlay result [--pane left|right] [--target] [--window W]`, returns `result.exitCode` once
  the overlay has closed. Errors `overlay still running` while up, `no overlay result` if none ran.
  `--pane` reads that pane's overlay; omit it for the session-wide one. A HUD runs the app's own painter,
  not a caller's program, so there is no status to report and the session-wide arm errors
  `no overlay result: the slot holds a hud`; the `--pane` arm still reads the separate pane-overlay slot,
  since HUD pane scope changes placement without changing slot ownership.
- `session overlay copy [--pane left|right] [--target] [--window W]`, returns `result.text` with the
  selection made INSIDE the overlay. `session copy` cannot reach it: that one addresses the pane the overlay
  covers, so a selection the user made in the overlay reads as `no selection` there. Does NOT touch the
  system clipboard. `--pane` reads that pane's overlay; omit it for the session-wide one. Errors
  `no overlay` with nothing in the slot, `overlay not realized` in the moment after `open` before its
  terminal is up, `no selection` when nothing is selected, and
  `no overlay to read: the slot holds a hud` for a HUD, whose text is agterm's own.
- `session overlay text [--all] [--lines N] [--pane left|right] [--target] [--window W]`, returns
  `result.text` with the overlay's terminal buffer. `session text` reads the surface UNDERNEATH, its
  `--pane right` returns the shell, not the program drawn over it. `--all` and `--lines N` mean what they do
  on `session text` and are mutually exclusive. What comes back is a TUI's DRAWN screen, wrapped as
  rendered, not the output the program would have printed, for output, prefer the program's own output
  file. Errors `no overlay`, `overlay not realized` and `no overlay to read: the slot holds a hud` as
  `session overlay copy` does, plus `failed to read surface buffer` on a real read failure. It has no
  `no selection`: a blank realized screen is `ok` with an empty string.
- `session hud [open] <message> [--detail T] [--spinner] [--spinner-style S] [--position P] [--background-color #rrggbb] [--text-color #rrggbb] [--size-percent N] [--pane P] [--pane-id ID] [--target] [--window W]`,
  post a PASSIVE message panel over the session and return its id. It occupies the same session-wide slot
  as `session overlay open`, but carries a message rather than a program: it takes no input, the session
  keeps first responder and stays typable, and the terminal behind it is neither dimmed nor click-blocked.
  Meant for the seconds before an agent can show anything, computing the items for `pick`, waiting on a
  slow command, so the user reads what is happening in the session he is about to be pulled into.
  `open` is the group's default subcommand (`session hud "gathering options…"`); a message that is
  literally `update` or `close` needs the explicit `session hud open` verb. `--detail` adds a dim second line,
  `--spinner` animates a glyph beside the message in the default `bar` style, `--spinner-style` picks
  another from `bar|braille|circle|blocks|dot` and turns the spinner on by itself, `dot` blinks rather than
  animating, for a panel that sits up for minutes. `--spinner-style none` is accepted too and leaves the
  panel static, so the `none` a read-back reports can be echoed straight back; an unknown name is refused
  `invalid spinner: <value> (bar|braille|circle|blocks|dot|none)`. `--position` anchors the panel to one of
  the nine `top-left|top-center|top-right|center-left|center|center-right|bottom-left|bottom-center|bottom-right`
  (default `center`), the same anchors `session background` takes; every anchor off center holds a fixed
  margin off that pane edge on each axis it names, so a panel at the largest allowed size never overhangs.
  `--pane primary|left|top|split|right|bottom` makes the selected pane the bounds for measurement, explicit
  size, anchor, and margin. `--pane-id` takes the shell's stable `$AGTERM_PANE_ID`; a live token overrides
  `--pane`, while an unknown token uses that role as fallback or errors without one. The stored identity follows
  pane swap and promotion. Open refuses a pane that is not rendered. Hiding the target suppresses the panel
  without stopping its helper, and showing it restores the panel. Destroying the target closes the HUD.
  A corner is what keeps a long-lived panel out of the text the user is reading. The bare `top`/`bottom`
  this argument shipped with are still accepted for `top-center`/`bottom-center`, and `hud.position` reports
  the canonical anchor whichever spelling was sent. The panel is measured from the message against the session's terminal font on BOTH
  axes separately, width from the longest wrapped line, height from the number of them, so a title and a
  subtitle give a wide, short panel rather than a square one. `--size-percent N` (1–100) overrides the WIDTH
  only; the height always follows the message, since a caller-set height could only strand it in an empty
  box. The effective width is bounded to 10–80% of the pane, the same invariant that makes
  `session overlay resize --full` a refusal, so a requested 100 reads back as 80. Both effective shares read
  back, as `hud.sizePercent` and `hud.heightPercent`. `--background-color #rrggbb` gives the panel its own solid
  background, read once when the panel is created; `--text-color #rrggbb` colors the TEXT and, unlike the
  background, rides the panel's body file, so an update can change it. Both read back, as
  `hud.backgroundColor` and `hud.textColor`. Message and detail are capped at 256 characters and
  reject control characters, newline included, since the panel prints straight into a live terminal and
  `--detail` is the second line on offer. Errors `session.hud.open requires a message` on a missing or
  empty message, `hud text must not contain control characters`, `hud message too long (max 256
  characters)` / `hud detail too long (max 256 characters)`, `invalid color: <value> (#rrggbb)`,
  `invalid text color: <value> (#rrggbb)`,
  `invalid position: <value> (top-left|top-center|top-right|center-left|center|center-right|bottom-left|bottom-center|bottom-right|top|bottom)`,
  `invalid spinner: <value> (bar|braille|circle|blocks|dot|none)`,
  `--pane must be left or right`, `hud pane must be left or right` when a pane ID resolves to scratch,
  `pane not visible`, `unknown pane id: <token>`,
  and `session.hud.open: --size-percent must be 1...100`.
  A second `hud` replaces the first; a `session overlay open` replaces a HUD, while a HUD over a RUNNING
  program is refused with `overlay already open`, a message is replaceable, a program is not.
- `session hud update <message> [--detail T] [--spinner] [--spinner-style S] [--position P] [--text-color #rrggbb] [--size-percent N] [--pane P] [--pane-id ID] [--target] [--window W]`,
  repaint the live panel in place: no re-spawn, no blink, the panel does not flicker. It REPLACES the
  whole spec rather than patching it, so `--detail`, the spinner, `--position`, `--text-color`, and pane selectors must be
  repeated to survive and an omitted one drops. `--spinner-style` may name a DIFFERENT style than the panel
  opened with, and `--text-color` a different color; both ride the message file, so the look changes on the
  next tick with no re-spawn. It shares `open`'s message, text, color, position, spinner, and pane-spelling
  validation. Pane lifecycle differs: update accepts a hidden target, while a missing split errors
  `session has no split` instead of `pane not visible`. There is no `--background-color`: the surface reads
  that once at creation, so only a fresh `session hud` can change it, and `tree` keeps reporting the creation
  color across updates. Errors `no hud` when none is up.
- `session hud close [--target] [--window W]`, take the panel down and delete its message file. Errors
  `no hud` when none is up, so it is not idempotent. A program overlay in the same slot is left alone;
  `session overlay close`, ⌘W, and closing the session or its window also tear a HUD down and delete that
  file.

**Displaying an image inline.** This skill bundles `scripts/show-image.sh`. It opens an overlay (a
real terminal surface) and renders the image there via the kitty graphics protocol, which ghostty,
agterm's engine, draws natively. No kitty binary and no external image viewer are used; the encoder
is plain `base64` + `printf`. Run it as `bash <skill-dir>/scripts/show-image.sh <image> [size-percent]`,
resolving `<skill-dir>` as the directory `SKILL.md` was loaded from rather than a fixed path, the skill
ships both as a plugin (`~/.claude/plugins/cache/…`, `~/.codex/plugins/cache/…`) and as the app's own
copy (`~/.claude/skills/agterm/`, `~/.codex/skills/agterm/`), and the script sits beside `SKILL.md` in
every one of them.
The image is scaled to fit the overlay and centered in it (uniform, aspect preserved, up or down): the
script asks the terminal for its pixel and cell geometry over `/dev/tty`, reads the image dimensions
with `sips`, and gives the graphics command an explicit cell box. If the terminal does not answer the
geometry query it falls back to drawing at native pixel size in the top-left corner.
Two simpler routes fail and are why the overlay is needed: emitting graphics escapes to the agent's own
tool stdout (the harness escapes the control bytes) and running an image viewer in the agent's tool
shell (no controlling terminal, `/dev/tty` errors). See examples.md for usage.

