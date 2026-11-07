Status: covered-pending-execution (docs/history/plans/2026-11-07-operative-file-read-budget-gate.md)
Priority: high
Class: fix-class
Origin class: skills-corpus defect (2026-11-07 cross-session 24h harvest over the prior day's maintenance fleet)
Cluster: docs/history/backlog/2026-11-05-plan-prompts-shared-rules-pruned.md (same dispatch-and-corpus legibility family; that row owns the rolling logs' shared contract block, this row owns the operative files' read-budget ceiling)

# Core operative skill files exceed the harness Read tool's single-read cap, and the refusal ignores the supplied window

## Problem

The maintenance fleet's operative files have grown past the Read tool's single-read token budget (25000 tokens), and the tool refuses the whole file even when the caller supplies `offset`/`limit`, contradicting the refusal's own remedy advice. Fourteen refused reads were witnessed across the 2026-11-06 10:00 to 2026-11-07 02:00 sessions, every one with a window supplied: `agents/skills/maintenance/zcode.md` (119033 bytes, about 27.6K tokens; refused at offset 56 limit 93, repeatedly across four sessions), the vendored `agents/skills/plans/SKILL.md` twin (201859 bytes, up to 36.1K tokens; refused five times at various offsets), and `agents/skills/maintenance/decisions.md` (about 27.4K tokens; refused four times across the primary checkout and two run worktrees). A 354240-byte rolling log additionally hit the tool's 256KB hard size cap once. Each session recovered only by falling back to shell text tools, so skill instructions that direct a whole-file read ("load the runtime overlay", "read its SKILL.md", the authoring walk over the plans skill) silently degrade to partial or skipped context on exactly the files every unattended session must load. The corpus owns both halves of the remedy and applies neither to these files: the learn skill's own load-on-dispatch module split is the in-repo precedent for an over-cap file (the learn router plus per-step modules), and the repository guidelines' Skill text anti-growth rules sanction a repo-wide byte-budget gate whose landing is still pending ("until that landing, the same discipline applies at review time only"). The witnessed cost is that pending landing's price, now measured.

## Observed vs expected

Observed: sessions loading the runtime overlay, the plans skill, or the decisions file hit a hard refusal mid-walk, re-issue the same windowed read, then fall back to grep and sed; the walk continues with degraded context and wasted turns.
Expected: every file a skill instruction directs a session to read loads whole through the Read tool, or the owning skill names its own module or windowed read path so the load never depends on whole-file single reads.

## Evidence (trimmed)

- Byte sizes at HEAD: agents/skills/maintenance/zcode.md 119033; agents/skills/plans/SKILL.md 201859; agents/skills/maintenance/decisions.md 111845; docs/history/backlog/EXEC-PROMPTS.md 354240. Token counts from the tool's own refusal lines (27632, 36124, 33699, 29382, 27237, 27432 across instances).
- The refusal fires with the window supplied: the same call carried `"offset": 56, "limit": 93` and was refused with "File content (27632 tokens) exceeds maximum allowed tokens (25000)" while the error text advises "Use offset and limit parameters".
- Learn's module-split precedent: agents/skills/learn/SKILL.md routes each step to step-1-extract.md, step-2-placement.md, step-6-instruction-updates.md, step-completion.md, with the router text declaring the read set "this router plus the in-flight step modules, never the full pre-split body" (plan docs/history/plans/2026-10-10-done-closeout-lock-span-and-output-cost.md Task 5).

## Suspected root area

Skill file growth without a read-budget constraint. The anti-growth rules name the missing gate; the gate's caps must be calibrated against the harness single-read budget (or the files it measures split load-on-dispatch), otherwise a fully compliant corpus can still be unreadable by the runtime that must load it.

## Ship when

The byte-budget gate lands with caps that keep operative skill files single-read-loadable, and every file still over the cap splits load-on-dispatch after the learn precedent; a fresh unattended session loads the overlay, the plans skill, and the decisions file through the Read tool without a fallback; hygiene scan exit 0; the gate is the only machinery added, pre-sanctioned by the guidelines' anti-growth rules, with its registry row naming this row's witness as the admission incident.

Capture hygiene: `bash scripts/scan-public-hygiene.sh --files` pass and `bash scripts/check-no-em-dash.sh file` pass over this row and the sibling cluster edits (2026-11-07)
