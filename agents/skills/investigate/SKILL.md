---
name: investigate
description: "Pre-authoring investigation for a backlog item or a small set of related items: group discovery, issue archaeology, and possibility-space analysis, ending in one entry in the tracked rolling prompt log that carries a ready-to-dispatch plan-creation prompt plus rejected-alternative dispositions. Runs autonomously with no user interview and never executes or dispatches anything. Trigger phrases; \"investigate this backlog item\", \"run pre-authoring investigation\", \"archaeology on this guard\", \"prepare a plan-creation prompt\"."
---

# Investigate

**Purpose:** pre-authoring investigation for one open backlog item or a small set of related items, producing a plan-creation prompt. The skill runs autonomously, asks the user nothing, and produces exactly one artifact: a single entry in the tracked rolling prompt log (`docs/history/backlog/PLAN-PROMPTS.md`, ordered most urgent first).

**Boundary:** investigate runs autonomously with no user interview and stops at the log entry, or earlier on the Stage 1 ownership skip, while plans Phase 1 owns user-facing requirements discovery and consumes the log entry as design input.

Run the four stages in order; the skill ends when Stage 4's write is committed, or earlier when Stage 1's ownership skip ends the pass with no entry.

## Configuration (from facts document)

Read these keys from the opening TOML block of `.ai-playbook/facts.md`. Fall back to the defaults when a key is missing.

| Key | Purpose | Fallback |
|-----|---------|----------|
| `plans_dir` | Plans root consulted when checking whether a covering plan already exists for the item's origins | `docs/history/plans/` |
| `backlog_dir` | Open-backlog directory scanned for the input item and for similar or grouped siblings | `docs/history/backlog/` |

### Stage 0: backlog-wide cluster survey (runs on every anchored invocation)

- Before the anchored pass, sweep every open top-level backlog item in the resolved `backlog_dir` and group items sharing a mechanism, surface, or defect class (the Stage 1 grouping criteria), skipping origins that are not investigable here (the monitor's skip rule: no intersection with an existing log entry's `Origins:` line, no plans-root plan file, plus the Stage 0 ownership skip: a foreign-origin item, one whose subject code, documentation, ticket context, or module paths identify a different owning repository, is skipped with that reason recorded in the turn output and is never grouped, investigated, or dispatched from this backlog).
- For each computed roster of two or more, write one additive `Cluster:` line per sibling into each member's header region (repo-relative paths, the member itself excluded). Idempotent: an unchanged roster never rewrites, and an item with no cluster is never touched. The sweep emits no log entries and changes no status: the roster lines are advisory input for Stage 1, never dispositions.

### Stage 1: group discovery

- Read the input item's `Cluster:` lines (the Stage 0 sweep's rosters) as discovered-sibling input before the similarity search.
- Check the open backlog (the resolved `backlog_dir`) for items similar to or grouped with the input: shared mechanism, shared surfaces, or the same defect class.
- Apply the Stage 0 ownership skip to the anchored search as well: a foreign-origin sibling is never grouped into this investigation, and when the input item itself is foreign-origin, the pass ends before Stage 2 with the reason recorded in the turn output (no log entry; ownership is a boundary this skill never crosses).
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
- Every rejected-alternative disposition cites its evidence basis: a disk witness (a repo-relative path), a landed mechanism (a file or section that exists), a commit, or a witnessed incident - never a bare assertion.
- The enumeration includes at least one alternative from outside the recommended mechanism's family (a pins-suite change versus a skill-text change are different families); the two standing axes are the minimum, not the whole space.
- An entry whose alternatives were contested on evidence (an operator or peer correction, recorded in the entry or its origin, arguing against a disposition with evidence) carries no `Standing pre-authorization` line, or scopes it to the non-contested arms, so a contested recommendation gets a genuine authoring-side look.
- The recommendation must name what was rejected and why; these one-line dispositions carry into the log entry.

### Stage 4: log entry emission

- The entry passes `python3 scripts/check_investigate_entries.py` (the structural minimum the script owns: non-empty rejected alternatives, evidence-cited dispositions) before the write is committed; the script's module docstring owns the marker semantics (the file-precision marker floor included), and the phrasing here is only the summary.
- Write one entry into the rolling prompt log (`docs/history/backlog/PLAN-PROMPTS.md`) at the urgency position the entry merits (the log is ordered most urgent first; the position is judged when the entry is written).
- The entry carries: origins (repo-relative backlog paths, including the Stage 1 roster when a group was investigated), scope arms, orientation, the full ready-to-dispatch prompt payload, and one-line dispositions for each rejected alternative (Stage 3).
- The entry is the artifact: no side record under the gitignored scratch directory (`docs/tmp/`).
- The write follows the log's standing rules: a targeted section edit (the entry's own section) prepared from a fresh read; re-read and compare before every write, and any difference is drift: retry once from the fresh read, then attempt a pure append of the entry at the end of the file; only when that append also fails the drift check, abort and report the full intended entry text in the turn output as the fallback record; the entry carries repo-relative paths only and no personal, machine-specific, or foreign-project data (no ticket prefixes, organization, service, or module names, and no internal document titles of a repository this one does not own); the write is committed in the same turn that performs it.

## Hard gates

- Never execute or dispatch anything: the skill ends at the log entry, when one is emitted (the Stage 1 ownership skip ends a foreign-origin pass earlier with no entry); the prompt payload is work for a later authoring turn, never for the turn that writes it.
- Never cite the log as a plan's Backlog origin: the log is not a backlog item; a plan produced from a log entry cites it as design input in prose.
- Keep every path repo-relative: no absolute or machine-specific paths in the skill's edits or emitted entry.

## Integration Points

### With `maintenance` skill
Consumer. The maintenance scheduler turn's monitor step invokes this skill, at most one investigation per turn, on the highest-priority remaining ungrouped open backlog item when the log has no ready entry (it first skips any ungrouped item whose origins intersect an existing log entry's `Origins:` line or a plans-root plan file, or are foreign-origin (the Stage 0 ownership skip), recording the skip reason), and it reads the emitted entries for its read, prune, freeze, and dispatch duties. The maintenance loop's per-cycle harvest duty (maintenance SKILL.md Step 3) is the second consumer form: it runs one investigate pass per completed cycle under a live standing directive, taking the highest-priority ungrouped open item among the findings the cycle witnessed (the same selection rule this entry prescribes), while the scheduler turn's monitor step remains the first form. The anchored invocation opens with the Stage 0 survey sweep, whose `Cluster:` annotation writes the scheduler turn commits and reads around exactly as before.

### With `plans` skill
Downstream consumer of the emitted prompt: a later plans session authors from the log entry as design input, per the Boundary line above. Investigate never authors the plan file itself.
