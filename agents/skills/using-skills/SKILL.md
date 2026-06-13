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

## Step 0: Repo agent facts (every session)

Before path-dependent skill work in a target repository:

1. **Read** `.ai-playbook/facts.md` when it exists; parse only the **opening** fenced TOML block for path keys (`plans_dir`, `reviews_dir`, `tmp_dir`, `facts_path`, `bootstrap_version`, and optional keys).
2. **Check Terms triggers** from the `bootstrap-ai-playbook` skill: missing file, invalid TOML, incomplete required keys, `.ai-playbook/` or `.ai-playbook/facts.md` not gitignored, or cached path keys pointing at directories that no longer exist on disk.
3. **Invoke `bootstrap-ai-playbook` only when at least one trigger fires** — at most **once per session**, except a **recovery rerun** when post-write validation fails or a required path key cannot be resolved after a bootstrap run in the same session (see `bootstrap-ai-playbook`). When the file is fresh (valid TOML, required keys present, paths exist, gitignore passes), bootstrap is a **no-op**; use cached TOML values.
4. Other skills **read** TOML keys from `.ai-playbook/facts.md`; they do **not** invoke bootstrap each task.

## Proactive Usage Principles

The SessionStart hook injects the following principles into every session:

1. **Don't wait for user requests** - Proactively invoke relevant skills when the context matches
2. **Check guidelines before writing code** - Read `coding_guidelines.md` and stack-specific files (`jvm_guidelines.md`, `java_guidelines.md`, `kotlin_guidelines.md`, or `python_guidelines.md` as applicable) from `shared_docs_dir` in `~/.ai-playbook/facts.md`.
3. **Analyze before adding new components** - Read existing module patterns and align with those guideline files before introducing new types or packages
4. **Always run tests after writing code** - Use `unit-test-runner` (see language guidelines for runner commands)
5. **Always verify before claiming completion** - Re-run `unit-test-runner` (or project checks) with fresh output before claiming done; use `done` at session end
6. **Plan file reference** - A path under the project `{plans_dir}` alone is not an execute-plan trigger. Resolve `{plans_dir}` and related paths from `.ai-playbook/facts.md` (Step 0 above). Route through the plan-path gate in the `execute-plan` skill (execute-plan / manual / read-only) before editing production code.
7. **Documentation paths** - Skills that read/write repo docs resolve `{plans_dir}`, `{reviews_dir}`, `{tmp_dir}`, etc. from the opening TOML block in `.ai-playbook/facts.md` (Step 0). **`doc-hierarchy-migrate`** applies the three-layer schema when explicitly migrating a repo; **`doc-hierarchy-upkeep`** updates Layer 1/2 after migration; **`doc-hierarchy`** is schema reference only.
