# Backlog: the learn commit discipline has no same-file concurrency arm, so a peer's explicit-path commit absorbs a concurrent session's uncommitted corpus hunks

- **Filed:** 2026-11-01, learn Step 1.8 over the 11:00 auth carrier's learn+investigate turn
- **Status:** covered (docs/history/plans/2026-11-01-learn-corpus-commit-sweep-concurrent-session.md)
- **Workflow:** backlog
- **Priority:** medium
- **Cluster:** the learn skill's commit discipline (`agents/skills/learn/step-1-extract.md` Step 1.8 commit rule; the own-edit check per lesson 134 in `docs/maintenance/development_lessons.md`)
- **Skill/step:** `agents/skills/learn/step-1-extract.md`, Step 1.8 commit rule
- **Class:** fix-class
- **Origin class:** session witness (learn+investigate turn, 2026-11-01)

## Problem

Witnessed outcome (2026-11-01): two learn sessions authored the project lessons corpus concurrently; the faster session's explicit-path commit (eb77d5782) landed its own hunks together with the other session's uncommitted lesson 349 and its lesson 44 witness append. The absorbed content is durable and byte-correct on main, but it is attributed to a commit subject naming only the absorbing session's work, and no `committed:` receipt names it, so subject-based history and receipt-ledger consumers miss it.

Two discipline gaps surround the outcome:

- The stager-side own-edit check (lesson 134, codified in the Step 1.8 commit rule) tells a committing session to treat a pure-addition hunk it did not write as foreign and skip the path; the observed commit carried exactly such hunks, so either the check was not exercised on this path or its skip-and-report arm needs a mixed-author same-file clarification.
- The write-side parallel discipline (retry once on the re-read content) covers write-time conflicts only; nothing addresses commit-time absorption of a concurrent session's authored-but-uncommitted hunks, and nothing tells the authoring session to commit gated hunks promptly or record their blob ids in a shared checkout.

## Ask

One bounded skill-text arm in the Step 1.8 commit rule: in a checkout shared with live peers, commit learn-authored corpus hunks in the same bounded span as the gated write (marker, edit, scan, commit) or record their blob ids; after any parallel commit lands on an edited file, re-derive what actually landed (`git log -S` on an authored span) before reporting the receipt. Optionally make the own-edit skip arm's mixed-author case explicit. Lesson 351 in `docs/maintenance/development_lessons.md` is the corpus witness.
