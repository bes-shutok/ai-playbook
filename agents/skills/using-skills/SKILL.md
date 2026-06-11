---
name: using-skills
description: Skill usage guide - reminds available skills at the start of each session
user-invocable: false
---

# Skill Usage Guide

This skill is automatically triggered by the SessionStart hook, dynamically scanning all available skills under the `~/.agents/skills/` directory.

## Dynamic Scanning Mechanism

- Hook location: `~/.agents/hooks/session-start.sh`
- Scan directory: `~/.agents/skills/*/SKILL.md`
- Extracted information: name, description, user-invocable

## How to Add a New Skill

1. Create a new directory under `~/.agents/skills/`
2. Create a `SKILL.md` file with frontmatter:
   ```yaml
   ---
   name: skill-name
   description: Description of the skill
   user-invocable: true
   ---
   ```
3. It will be automatically detected at the start of the next session

## Proactive Usage Principles

The SessionStart hook injects the following principles into every session:

1. **Don't wait for user requests** - Proactively invoke relevant skills when the context matches
2. **Check guidelines before writing code** - Read `coding_guidelines.md` and stack-specific files (`jvm_guidelines.md`, `java_guidelines.md`, `kotlin_guidelines.md`, or `python_guidelines.md` as applicable) from `shared_docs_dir` in `~/.ai-playbook/facts.md`.
3. **Analyze before adding new components** - Read existing module patterns and align with those guideline files before introducing new types or packages
4. **Always run tests after writing code** - Use `unit-test-runner` (see language guidelines for runner commands)
5. **Always verify before claiming completion** - Re-run `unit-test-runner` (or project checks) with fresh output before claiming done; use `done` at session end
6. **Plan file reference** - A path under `docs/plans/` alone is not an execute-plan trigger. Route through the plan-path gate in the `execute-plan` skill (execute-plan / manual / read-only) before editing production code. See `execute-plan` skill "Implicit triggers and plan-path gate".
