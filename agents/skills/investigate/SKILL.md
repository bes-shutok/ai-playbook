---
name: investigate
description: "Pre-authoring investigation for a backlog item or a small set of related items: group discovery, issue archaeology, and possibility-space analysis, ending in one entry in the tracked rolling prompt log that carries a ready-to-dispatch plan-creation prompt plus rejected-alternative dispositions. Runs autonomously with no user interview and never executes or dispatches anything. Trigger phrases; \"investigate this backlog item\", \"run pre-authoring investigation\", \"archaeology on this guard\", \"prepare a plan-creation prompt\"."
---

# Investigate

**Purpose:** pre-authoring investigation for one open backlog item or a small set of related items, producing a plan-creation prompt. The skill runs autonomously, asks the user nothing, and produces exactly one artifact: a single entry in the tracked rolling prompt log (`docs/history/backlog/PLAN-PROMPTS.md`, ordered most urgent first).

**Boundary:** investigate runs autonomously with no user interview and stops at the log entry, while plans Phase 1 owns user-facing requirements discovery and consumes the log entry as design input.

Run the four stages in order; the skill ends when Stage 4's write is committed.

## Configuration (from facts document)

Read these keys from the opening TOML block of `.ai-playbook/facts.md`. Fall back to the defaults when a key is missing.

| Key | Purpose | Fallback |
|-----|---------|----------|
| `plans_dir` | Plans root consulted when checking whether a covering plan already exists for the item's origins | `docs/history/plans/` |
| `backlog_dir` | Open-backlog directory scanned for the input item and for similar or grouped siblings | `docs/history/backlog/` |

### Stage 1: group discovery

- Check the open backlog (the resolved `backlog_dir`) for items similar to or grouped with the input: shared mechanism, shared surfaces, or the same defect class.
- When a group exists, investigate the group as one unit and record the roster (each member's repo-relative path) in the log entry, so a parallel session (an ownership survey, a parallel triage) sees the grouping instead of rejecting grouped origins as unrelated (the witnessed 2026-09-27 mass-rejection cause).
- When no siblings exist, proceed with single-origin scope and record the roster as the one origin.

### Stage 2: issue archaeology

- For each guard, contract, or mechanism the item touches, establish when and why it was introduced before judging it: history search such as `git log -S` over the mechanism's distinctive spans, the motivating plan or incident that introduced it, and its current dependents.
- Read the motivating record itself rather than inferring intent from the current text alone; a decision whose framing inverts its own original fix is the failure this stage prevents.
- Judge the mechanism only after its introduction story is established.

### Stage 3: possibility space

- Enumerate the alternative resolutions before recommending one, including two standing axes:
  - the remove-or-keep axis: remove, keep, keep and narrow, or keep and widen the mechanism;
  - the missing-complement axis: a correct mechanism with a missing complement is completed, not removed (witnessed case: a seed gate whose recovery path was missing; the correct scope was both arms, not removal and not the one-arm fix).
- The recommendation must name what was rejected and why; these one-line dispositions carry into the log entry.

### Stage 4: log entry emission

- Write one entry into the rolling prompt log (`docs/history/backlog/PLAN-PROMPTS.md`) at the urgency position the entry merits (the log is ordered most urgent first; the position is judged when the entry is written).
- The entry carries: origins (repo-relative backlog paths, including the Stage 1 roster when a group was investigated), scope arms, orientation, the full ready-to-dispatch prompt payload, and one-line dispositions for each rejected alternative (Stage 3).
- The entry is the artifact: no side record under the gitignored scratch directory (`docs/tmp/`).
- The write follows the log's standing rules: a targeted section edit (the entry's own section) prepared from a fresh read; re-read and compare before every write, and any difference is drift: retry once from the fresh read, then attempt a pure append of the entry at the end of the file; only when that append also fails the drift check, abort and report the full intended entry text in the turn output as the fallback record; the entry carries repo-relative paths only and no personal or machine-specific data; the write is committed in the same turn that performs it.

## Hard gates

- Never execute or dispatch anything: the skill ends at the log entry; the prompt payload is work for a later authoring turn, never for the turn that writes it.
- Never cite the log as a plan's Backlog origin: the log is not a backlog item; a plan produced from a log entry cites it as design input in prose.
- Keep every path repo-relative: no absolute or machine-specific paths in the skill's edits or emitted entry.

## Integration Points

### With `maintenance` skill
Consumer. The maintenance scheduler turn's monitor step invokes this skill, at most one investigation per turn, on the highest-priority remaining ungrouped open backlog item when the log has no ready entry (it first skips any ungrouped item whose origins intersect an existing log entry's `Origins:` line or a plans-root plan file, recording the skip reason), and it reads the emitted entries for its read, prune, and dispatch duties.

### With `plans` skill
Downstream consumer of the emitted prompt: a later plans session authors from the log entry as design input, per the Boundary line above. Investigate never authors the plan file itself.
