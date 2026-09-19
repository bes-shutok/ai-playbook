# Backlog: ZCode memory files get rewritten externally, breaking Edit state

Status: done
Priority: low
Workflow: backlog
Date: 2026-09-16

Privacy boundary: this item is sanitized. It contains no personal names,
email addresses, policy numbers, or private message text.

## Symptom

In a long-running ZCode session (2026-09-16, medical-data project), two `Edit`
calls against files under `~/.zcode/cli/memories/projects/<project>/memory/`
failed with "File has been modified since read" even though the same agent had
written the file earlier in the session and no other agent turn had touched it
in between. Re-`Read` immediately before the retry succeeded, and the content
showed changes the agent had not made in that turn (apparently host-side
folding/normalization of memory content between turns).

## Impact

Any multi-step memory update (two+ Edits to the same memory file across turns)
risks a failed Edit and a wasted round trip; worst case an agent may assume
its earlier edit was lost and duplicate content.

## Candidate rules

1. Treat memory files as externally mutable: `Read` immediately before every
   `Edit` on a memory file; never rely on read-state from earlier in the
   session.
2. Prefer one `Write` per memory file per turn (full-file rewrite) over
   successive `Edit`s when several sections must change.
3. If an Edit fails with modified-since-read, Read, diff against intent, then
   retry once — do not rewrite blind.
