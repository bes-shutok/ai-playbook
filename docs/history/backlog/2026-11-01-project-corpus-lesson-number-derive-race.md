# Project corpus lesson-number derivation races under parallel learn sessions

Status: open
Workflow: backlog
Priority: medium
Class: fix-class
Origin class: learn Step 1.9 project issue capture (2026-11-01 interactive learn run over the same day's authoring session)
Cluster: docs/history/backlog/2026-11-01-learn-corpus-commit-sweep-concurrent-session.md (same surface - parallel learn sessions authoring the project lessons corpus in one shared checkout; that row's landed plan covers the commit-span attribution arm, this row the write-time number-derivation arm)

## Problem

Two learn sessions authoring `docs/maintenance/development_lessons.md` concurrently in one shared checkout each derived the next lesson number from the same pre-write read: both computed maximum existing heading plus one and both wrote a `## 337.` heading, so the corpus carries two distinct lessons numbered 337. The number-derivation rule (learn SKILL.md: derive from a fresh read as the maximum existing `## N.` heading number plus one; retry once on re-read when a parallel run wrote first) closes the sequential-write window only: when both sessions read before either writes, each session's retry re-read finds its own heading present and proceeds. The Step 6.6 project-tier duplicate check is warn-only and runs at learn finish, after both writes have already landed.

## Evidence

- `grep -n '^## 337.' docs/maintenance/development_lessons.md` returns two headings with different titles ("Derive Consumer-Side Test Fixtures From the Producer's Actual Write Path"; "Verify the Provenance of a Pre-Existing Session-Dir Baseline Before Capture-Once or Default-Lookup Adoption").
- `git log -S '## 337.' -- docs/maintenance/development_lessons.md` names the two landing commits: `721e6cc21` (execute-plan: land plan-authoring-stand-down-before-charter) and `b7e89b33d` (execute-plan: land session-channel-zcode-runtime-derivation-empty).
- The only check that catches the shape today is Step 6.6's project-tier duplicate check (optional grep, warn-only), run after the fact at learn finish.

## Suspected root area

`agents/skills/learn/SKILL.md` number-derivation rule (the fresh-read window has no pre-write collision probe), plus the project corpus carrying the live collision to repair.

## Fix shape (body-named, single bounded change-set, no open design choice)

(1) Repair the live collision: renumber the second `## 337.` heading to the next free number and update same-corpus references to either numbered lesson by hand (grep for citations first). (2) Close the window in skill text: the derivation rule gains a pre-write collision probe - immediately before the corpus write, re-grep the derived number; on a hit, re-derive from a fresh read and retry once before reporting the drift as a manual follow-up. No validator, hook, or lock: the sibling landed plan's machinery admission rejected runtime machinery for the adjacent commit-span arm on the same shared-checkout economics (false-positive cost: a blocked legitimate landing whenever peers share a checkout).
