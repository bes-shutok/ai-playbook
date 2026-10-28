# PLAN-PROMPTS.md wholesale stub rewrite: identify the writer channel

Status: open
Priority: medium
Class: corpus-integrity
Origin class: learn Step 1.9 project issue capture (2026-10-28 closeout-completion session witness)

## Observed versus expected

The primary checkout carried uncommitted dirt rewriting
`docs/history/backlog/PLAN-PROMPTS.md` from its full 407-line ledger (header,
entry sections, and twenty receipt-ledger lines) to a three-line fixture-style
stub (`# PLAN prompts` / `- entry one`), first observed 2026-10-28 19:07Z in the
dirty state and repaired the same day by restore from HEAD (lesson 292, the
refused-carry rule). Expected: every write to a tracked rolling prompt log is
either a landed commit with receipts or an owned session edit with a durable
record; an unexplained wholesale rewrite with no owning session, receipt, or
commit is a gap in that contract.

## Work needed

One bounded forensics pass: identify the writer channel that produced the stub
bytes. Sweep the durable channels (session logs and ZCode session store over
2026-10-28 roughly 16:30Z-19:10Z, git reflog and stash over the window, the
repo's test fixtures for the stub's literal text `# PLAN prompts` / `- entry
one`, and any script that writes a prompt-log fixture to a real path) and
record the finding beside this row's covered disposition. The stub's literal
text is the primary fingerprint: a fixture string points at a test or script
writing to the live path (a path-resolution defect class); no match points at a
session or tool write.

If the writer is a test or script fixture leaking onto the live path, the
follow-up is the smallest path-resolution fix plus a fixture-path pin; if it is
a session, the follow-up is the session's owner recording the write. Either
way the pass ends in one disposition commit; no new machinery is proposed
(the read-first carry rule in lesson 292 and the wired prompt-log landing
audit own the prevention sides they cover).
