```toml
id = "weekly-skill-review"
cadence_days = 7
kind = "audit"
```

# Recurring task: weekly skill-review lane

You are running the `recurring task weekly-skill-review lane` in the repository at <REPO_ROOT> (the resolved repository root; this body runs verbatim in a fresh session with only that root). The registry consult owns this task's due-read and dispatch; this file is the run's procedure of record. The state record's additive `rotation_cursor` field carries the next batch start (cold start: cursor 0).

## Corpus and batch

The review units are one ordered list built from three segments, derived from the tracked tree at run time:

1. Skill segment: the top-level skill directories under `agents/skills/`, in lexicographic order of skill directory name (the stable recorded rotation order). Vendored `synced/` copies stay outside the rotation.
2. Maintenance segment: the Markdown files under `docs/maintenance/` (recursively), in path order.
3. Backlog segment: the open top-level backlog Markdown files (`docs/history/backlog/*.md`; the `completed/`, `deferred/`, and `rejected/` subdirectories are archived trees and stay outside), in basename order. A row is open when its status line (a leading `Status:` line or a bold list-item `**Status:**` form) does not mark it covered (including completed), rejected, or deferred; a row with no status line is open. The rolling prompt logs `PLAN-PROMPTS.md` and `EXEC-PROMPTS.md` are not review units; the maintenance router processes them separately.

The tracked skill Markdown (excluding `synced/`), the maintenance segment, and the open backlog segment together form the run's live prose corpus; the same file set feeds the per-run em-dash diagnostic below.

Per run, the batch is the next `ceil(total_units / 6)` units of the combined ordered list, starting at `rotation_cursor` and wrapping to the list start, so every review unit is covered at least every six successful runs (about every six weeks at cadence 7). `total_units` is the combined list size counted at run time. The cursor is a plain index into the combined list: because the skill segment is the list's first segment and keeps its current size and order, an existing cursor value that points into the skill list names the same next skill unit as before the corpus expansion. A start index at or beyond the current `total_units` (the corpus shrank between runs) wraps modulo `total_units` before the batch is read.

## Defect classes

Review each batched unit (a skill directory, a maintenance Markdown file, or an open backlog row) for the five defect classes:

- Overcomplication: rules and guard ladders for problems never observed again, always-one-way branches, speculative generality.
- Repetition: the same rule or contract stated in multiple homes, including vendored-copy drift against the canonical files.
- Internal controversy: contradictory instructions within or across files, including superseded-but-undeleted text.
- Source-of-truth placement: content restating a topic owned by a canonical file, checked against `agents/skills/doc-hierarchy/content-ownership.md` (by reference; do not restate its table).
- Standing prose rules: section 39 of the repository's configured agent workflow guidelines (`projects/.ai-playbook/agent_workflow_guidelines.md`), expressly including the globish rule (39.2) beside the no-em-dash rule (39.1).

Per finding, record the evidence shape: file, line-precise span, defect class, and proposed remediation. The semantic review is bounded to the selected rotation batch and stays read-only and advisory: findings are review suggestions only; the audit never edits source files, moves, or reclassifies documents.

## Per-run read-only diagnostics

Each run additionally executes three read-only diagnostics and records their summaries in the run's aggregates record (Output discipline). None of them changes the audit outcome, the lane dispatch, or the state advance; a diagnostic that cannot execute is recorded in `last_result` and does not by itself constitute a failed run; the failure advance stays bound to the run's own end-to-end completion condition, and a nonzero exit carrying findings is an executed diagnostic (findings are classified, not a failure advance).

- Em dash scan over the full live prose corpus: build the corpus file list (one path per line) and run `bash scripts/check-no-em-dash.sh stdin` with that list on stdin. Known residual: an em dash inside the backticked quoted app refusal message in `agents/skills/agterm/reference.md` (line 868 as of 2026-10-27) is a KNOWN literal-data residual, deliberately kept because the dash is part of the documented output, not prose punctuation; the residual row `docs/history/backlog/2026-10-27-emdash-residuals-open-rows-and-literal.md` owns the live location, and the classification matches on the quoted string, never on the line number. Every other hit reports as new with its `path:line` evidence.
- Duplication report over the skills and the live maintenance docs: `python3 scripts/skill_text_duplication.py agents/skills/ docs/maintenance/`. The script excludes `docs/history/` and `synced/` subtrees itself, always reports `OUTCOME: pass`, and its per-file repeated-span percentages, duplicated sentences, and cross-file intersections are data, never failures.
- Byte-budget report over the skill corpus: `python3 scripts/skill_text_budget.py --check`. Warning-only: advisory BREACH, CAPS GAP, STALE CAP, and PILOT lines that never move the exit; the report always ends `OUTCOME: pass`.

## Quarantine batch presentation

Before the aggregates record is written, the run reads the open top-level backlog rows carrying a `Quarantine:` header line and records one batch presentation (the row list plus one-line value summaries) as an operator-facing quarantine section appended to `docs/maintenance/skill-review-log.md` beside the run's aggregates record. The body runs verbatim in a fresh unattended session, so the run stages proposed dispositions marked as proposals, never final: a row's quarantine disposition (cover by a named plan, reject, or keep open) is recorded in the row only by an operator-driven turn acting on the presented batch. A reject proposal acted on by the operator-driven turn prunes any held PLAN-PROMPTS.md entry whose origins are exclusively that row, under the log's write discipline (the dispatch duty's quarantine hold).

## Output discipline

One aggregates-only record is appended to `docs/maintenance/skill-review-log.md` (create-if-absent); no per-unit rows beyond batch membership, the operator-facing quarantine section above being the one named exception (its presentation section, not per-unit rows). The aggregates record additionally carries, compactly: the combined corpus size (the three segment counts and their total), the selected batch (the cursor range and its unit names), the three diagnostic summaries (em dash hits split into known and new with `path:line` evidence, the duplication report's headline numbers, the byte-budget report's breach and gap counts), and path-and-line evidence for every surfaced semantic finding. One backlog origin per actionable finding, or one batched origin per cluster, each origin passing the audit lane's dedupe-and-fold exists-check (open plus completed plus deferred) before filing, shaped per receiving-review's Backlog capture required content with the `Origin class:` line set per its rule (self-serving unless consumer-witnessed). The run record and filed origins commit under the tracked-artifact commit discipline: merge landing lock with bounded wait, default-branch re-verification at commit time, check-writes and em-dash gates over the changed paths, commit-before-stamp ordering, and the timeout's pending-artifact stranding record. The audit never edits source files and never finalizes a quarantine disposition (the quarantine section above owns that boundary).

## Caps

At most 2 sub-agents and the recorded token budget; idle/off-peak preferred; the consult's one-day failure advance applies on a failed run (the recorded supersession of the origin's no-advance fail-open wording).

## State advance

State advance: advance `rotation_cursor` by the batch size modulo `total_units` only when the batch completed end to end; stamp `next_due` at completion plus the task's `cadence_days`, set `last_run_at` and a one-line `last_result`, and reset `consecutive_failures`, through the record's atomic-replace rules.
