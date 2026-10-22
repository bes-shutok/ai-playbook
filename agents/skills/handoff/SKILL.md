---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up. Use when the user asks for a handoff, session handoff, or to continue work in a fresh session.
disable-model-invocation: true
when_to_use: Use only when the user explicitly invokes this skill by name (/handoff); never invoke it on the model's own judgment.
argument-hint: "What will the next session be used for?"
metadata:
  upstream: "https://github.com/mattpocock/skills/tree/main/skills/productivity/handoff"
---

# Session Handoff

> **Local fork notice:** this file carries a deliberate local fork of the upstream `handoff` skill (`metadata.upstream`). Deliberate divergence: the `when_to_use` frontmatter line stating the skill is used only when the user explicitly invokes it by name and never on the model's own judgment, kept beside the upstream's `disable-model-invocation: true` because some loaders ignore unknown top-level keys and present `when_to_use` beside the description as the only portable gate there. A future upstream sync of this directory must re-apply this fork (recovery source: git history of this path) or consciously drop it with the decision recorded; see the Vendored Asset Sync Rules in the repository AGENTS.md.

Write a handoff document summarising the current conversation so a fresh agent can continue the work.

## Output location

1. When working in a repo with `.ai-playbook/facts.md`, read `{tmp_dir}` from the opening TOML block (`using-skills` Step 0) and save to `{tmp_dir}/handoff/<slug>-handoff.md`. Derive `<slug>` from the active branch, plan name, or date.
2. When no repo agent facts exist, save to the OS temporary directory (not the current workspace).

Print only a short summary and the file path to the console. The file is the primary artifact for reading.

## Content rules

- Do not duplicate content already captured in other artifacts (specs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.
- Redact sensitive information (API keys, passwords, personally identifiable information).
- If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.

## Document structure

Use this template (aligned with `agents-best-practices/references/context-memory-compaction.md` Handoff summary format):

```markdown
# Session Handoff

## Next session focus
...

## Current objective
...

## Completed
- ...

## In progress
- ...

## Key decisions
- ...

## Artifacts
| Artifact | Path or URL |
|----------|-------------|
| ... | ... |

## Open questions
- ...

## Suggested skills
- `skill-name`: one-line rationale

## Next recommended step
...
```

## Integration Points

### With `agents-best-practices` skill
Harness-level auto-compaction uses a similar handoff format in `references/context-memory-compaction.md`. This skill is for **explicit user-requested** session handoffs; compaction is operational and automatic inside long runs.

### With `execute-plan` skill
When handing off mid-plan execution, reference the execute-plan manifest under `{tmp_dir}/execute-plan/<slug>/manifest.md` and the plan file path under `{plans_dir}`.

### With `handoff` consumers
The suggested skills section should name skills from the shared registry (`~/.agents/skills/`) that match the next session's work (for example `execute-plan`, `doing-code-review`, `systematic-debugging`).
