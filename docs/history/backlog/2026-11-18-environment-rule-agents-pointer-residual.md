# Backlog: the environment-contract rule landed without its repo AGENTS.md pointer line

- **Filed:** 2026-11-18, residue of the raced twin exec session over the environment-contract-extraction-and-rule change-set (the twin's focused r1 panel found the line load-bearing before the race was discovered)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Class:** fix-class
- **Origin class:** landing residue of a raced twin (duplicate change-set discarded unlanded; remainder row-scoped)
- **Skill/step:** repo root `AGENTS.md` (Agent-Specific Runtime Safety section)
- **Cluster:** landing d18d5bd4a (adhoc: land environment-contract-extraction-and-rule; rule #45 at `projects/.ai-playbook/coding_guidelines.md`, extraction arm 1d at `agents/skills/learn/step-1-extract.md`) + prune 5beb40b47

## Observed versus expected

**Observed:** the landing covers both origin surfaces (learn extraction arm 1d, guideline rule #45) but not the third placement surface origin 2's row named: the one-line cross-reference in the repo root `AGENTS.md` runtime-safety section. `grep -c "environment fact" AGENTS.md` returns 0 at the landing commit.

**Expected:** one pointer bullet in Agent-Specific Runtime Safety, sibling-shaped to the existing `python_guidelines.md #40` line: imperative restatement of the rule (never assume an environment fact - binary on PATH, file at a path, tool version, reachable service, permissions - in anything a generated or scheduled artifact will later run; verify in the actual execution context and check the payload's own start signal before reporting done), closing with `(see projects/.ai-playbook/coding_guidelines.md #45)`. learn Step 1 item 6 mandates exactly this instruction-file cross-reference for discoverability; AGENTS.md is the always-loaded surface while coding_guidelines.md is a referenced corpus.

## Reproduction evidence (trimmed)

Focused r1 consistency lens over the twin branch delta: "the AGENTS.md pointer line is the one branch-unique piece main never landed"; correctness/design lenses independently confirmed the pointer pattern matches the section's established compact-restatement-plus-numbered-pointer convention.

## Environment context

Single-line edit to a tracked repo surface; no skill text, no machinery.
