# agterm control reference

Full detail for every `agtermctl` command. See `SKILL.md` for the model and addressing overview,
`examples.md` for worked examples, and `cookbook.md` for the repository's installable recipes.

## Module dispatch (the router contract)

The reference's operative text lives in per-command-family modules beside this router. Each dispatch entry below contains a short contract and a module pointer. When a lookup needs a module, load its full text (load-on-dispatch). The read set is this router plus the module needed for the current lookup. Do not load the full pre-split body. This router does not restate rules. Each module keeps the original headings and bodies, byte-verbatim.

- **Connection, events, and addressing** - load `agents/skills/agterm/reference-connection.md` (the `## Connection and output`, `## events`, and `## Addressing` headings: socket resolution, the `--json` response shape, the events poll loop, and the target-addressing grammar) for any flag, option-ordering, or return-shape question about connecting to the socket, reading control events, or addressing targets.
- **Tree and workspaces** - load `agents/skills/agterm/reference-layout.md` (the `## tree` and `## workspace` headings: the full state tree with its per-node fields and the workspace lifecycle) when reading or mutating the window and workspace hierarchy.
- **Sessions** - load `agents/skills/agterm/reference-session.md` (the `## session` heading: the session subcommands' flags, return shapes, restore and state semantics, and the overlay and HUD pane machinery) for any per-session operation.
- **Windows, surfaces, dashboard, pick, and quick** - load `agents/skills/agterm/reference-windows.md` (the `## window`, `## surface`, `## dashboard`, `## pick`, and `## quick` headings: window creation and focus, split surfaces, the dashboard, the picker, and the quick palette) for windowing and on-screen surface operations.
- **Appearance and configuration** - load `agents/skills/agterm/reference-appearance.md` (the `## sidebar`, `## notify`, `## font`, `## keymap`, `## config`, and `## theme` headings: the sidebar, notifications, fonts, the keymap with its keymap.conf format, the ghostty.conf config file, and theme control) for appearance and configuration work.
- **Restore, version, and errors** - load `agents/skills/agterm/reference-restore.md` (the `## restore modes`, `## restore`, `## version`, and `## Errors you may see` headings: the restore-mode policy, session and workspace restore, the version identity, and the structured error vocabulary) when restoring state, checking the serving app, or decoding a refusal.
