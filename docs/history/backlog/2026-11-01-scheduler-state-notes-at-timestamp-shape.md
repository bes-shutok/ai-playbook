Status: open
Priority: low
Class: fix-class
Origin class: learn Step 1.9 session witness (2026-11-01 automation-born author turn, parallel-carrier cycle)

## Observed

The scheduler state file's structured `notes` array carried, within one hour of this filing, two wrong-shaped `at` stamps written by peer maintenance sessions: a placeholder hybrid `"2026-11-01T18:5x:00+00:00"` (a minute digit replaced by `x`; ISO-shaped, so ISO-parsing consumers reject it while label-reading consumers must special-case it) and a future stamp `"2026-11-01T18:35:00+00:00"` observed on a state write whose file mtime was about 18:12Z. The schema line tolerates `"<iso or dated label>"`, and the placeholder hybrid is neither allowed shape: not parseable ISO-8601, and not an explicitly human-readable dated label. Observation site: `.ai-playbook/scheduler-state.json` `notes` array, 2026-11-01; the file is a gitignored runtime surface, so the quoted values are the durable evidence, not the volatile file.

## Expected

Every structured `at` value is exactly one of the two allowed shapes: an exact parseable ISO-8601 timestamp (the canonical spelling the decision-shape-drift contract pins) or an explicitly human-readable dated label (prose, no ISO punctuation, no placeholder characters). A stamp derived at write time from the current operation's clock never lands future-dated or placeholder-shaped.

## Suspected root area

`agents/skills/maintenance/state-file.md` notes field line: the `"<iso or dated label>"` tolerance names the two allowed shapes but does not exclude the ISO-shaped hybrid, and no write-side sentence ties the stamp to the write clock (the wrong-stamp discipline lives in the lessons corpus, not in the contract text the state writers read at the boundary).

## Environment

ZCode runtime, automation-born maintenance sessions, 2026-11-01, repo copy is the runtime copy. Witnesses: two peer-written stamps plus one live state write observed during this session's own targeted state edit.
