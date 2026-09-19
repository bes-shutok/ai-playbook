# Backlog: Finder AppleScript folder-reference assignment fails with -10006

Status: done
Priority: low
Workflow: backlog
Date: 2026-09-16

Privacy boundary: this item is sanitized. It contains no personal names,
email addresses, or private paths beyond generic folder examples.

## Symptom

On macOS (2026-09-16, plain `~/Desktop`, not CloudStorage), an AppleScript
that (1) `make new folder`ed, then (2) assigned the folder to a variable by
re-resolving its name — `set target to folder "X" of folder "Desktop" of home`
— failed with error -10006 ("Can't set target to folder … Access not
allowed"). The `whose name is X` filter + `item 1` assignment pattern failed
the same way on retry, while a plain `exists folder X of …` check returned
`true`. The folder itself was created fine by the first run; only the
variable assignment/re-resolve broke.

## Working recipe (verified 2026-09-16)

- Never assign Finder folder references to variables via name re-resolution;
  use the fully inline reference at each use site, e.g.
  `duplicate (file n of src) to folder "X" of folder "Desktop" of home`.
- Split create and copy into separate `osascript` invocations, checking
  `exists` first; a failed mid-script run still persists created folders.
- Same remedy applies to the previously documented CloudStorage Finder
  wedges: `killall Finder` clears a wedged Finder, but was not needed here.

## Candidate rule

In shared recipes (project guidelines, memory), write Finder AppleScript with
inline element references and per-step invocations; ban `set v to folder …`
re-resolution by name.
