```toml
id = "weekly-skill-review"
cadence_days = 7
kind = "audit"
```

# Recurring task: weekly skill-review lane

You are running the `recurring task weekly-skill-review lane` in the repository at <REPO_ROOT> (the resolved repository root; this body runs verbatim in a fresh session with only that root). The registry consult owns this task's due-read and dispatch; this file is the run's procedure of record. The state record's additive `rotation_cursor` field carries the next batch start (cold start: cursor 0).

## Corpus and batch

The corpus is the top-level skill directories under `agents/skills/`, in lexicographic order of skill directory name (the stable recorded rotation order). Per run, the batch is the next `ceil(corpus_size / 6)` skills from the `rotation_cursor`, wrapping to the corpus start, so every skill is covered at least every six runs (about every six weeks at cadence 7).

## Defect classes

Review each batched skill for the three defect classes (overcomplication, repetition, internal controversy):

- Overcomplication: rules and guard ladders for problems never observed again, always-one-way branches, speculative generality.
- Repetition: the same rule or contract stated in multiple homes, including vendored-copy drift against the canonical files.
- Internal controversy: contradictory instructions within or across files, including superseded-but-undeleted text.

Per finding, record the evidence shape: file, line-precise span, defect class, and proposed remediation.

## Output discipline

One aggregates-only record is appended to `docs/maintenance/skill-review-log.md` (create-if-absent); no per-skill rows beyond batch membership. One backlog origin per actionable finding, or one batched origin per cluster, each origin passing the audit lane's dedupe-and-fold exists-check (open plus completed plus deferred) before filing, shaped per receiving-review's Backlog capture required content with the `Origin class:` line set per its rule (self-serving unless consumer-witnessed). The run record and filed origins commit under the tracked-artifact commit discipline: merge landing lock with bounded wait, default-branch re-verification at commit time, check-writes and em-dash gates over the changed paths, commit-before-stamp ordering, and the timeout's pending-artifact stranding record.

## Caps

At most 2 sub-agents and the recorded token budget; idle/off-peak preferred; the consult's one-day failure advance applies on a failed run (the recorded supersession of the origin's no-advance fail-open wording).

## State advance

State advance: advance `rotation_cursor` by the batch size modulo the corpus size only when the batch completed end to end; stamp `next_due` at completion plus the task's `cadence_days`, set `last_run_at` and a one-line `last_result`, and reset `consecutive_failures`, through the record's atomic-replace rules.
