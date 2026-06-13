# Repository Guidelines

## Project Structure & Module Organization
This repository is a command-spec library. Each Markdown file is an executable prompt/instruction set.

- `create-documentation/`: commands for RFCs, bug tickets, TDD docs, and documentation-learning workflows.
- `projects/.ai-playbook/`: shared cross-project guidelines and agent runtime folder mapping (`agent-runtime-layout.md`).
- `README.md`: source-of-truth index for command catalog, usage, and registration examples.
- `.opencode/command/`: local registration target used at runtime; create it locally as needed and avoid committing generated copies.

## Build, Test, and Development Commands
There is no compile/build pipeline. Main workflows are registration and execution.

- Register commands locally:
```bash
mkdir -p .opencode/command
cp create-documentation/create-design-rfc.md .opencode/command/create-design-rfc.md
cp create-documentation/create-tdd.md .opencode/command/create-tdd.md
cp create-documentation/create-bug-ticket.md .opencode/command/create-bug-ticket.md
```
- Run a command in direct mode (Codex example):
```bash
codex exec "$(cat create-documentation/create-design-rfc.md)

Context:
$(cat ./context/rfc-input.md)"
```
- Audit files quickly:
```bash
rg --files
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh   # from instructions repo root; see public_hygiene_scan_script in user facts
```

## Coding Style & Naming Conventions
- Use Markdown with clear section headings and concise, enforceable instructions.
- Prefer imperative language for rules (for example, “Do X”, “Do not Y”).
- Keep command filenames kebab-case and descriptive (for example, `create-design-rfc.md`).
- For non-trivial specs, include a terminology/core-concepts section near the top.
- Keep examples, Markdown links, and documented repo paths repository-relative; do not commit machine-specific absolute filesystem paths such as `/Users/...`.
- Verify actual on-disk runtime source folders before documenting which agent uses which commands or skills; do not guess from folder names alone.
- Keep detailed agent runtime folder mappings in `projects/.ai-playbook/agent-runtime-layout.md` and let `README.md` summarize and link instead of duplicating the full mapping.

## Skill Design Guidelines
- A skill must provide unique workflow logic or domain knowledge; do not create skills for behavior any competent agent should exhibit by default (for example, "look at existing code before implementing" or "run tests before claiming done").
- Keep the main `SKILL.md` language-agnostic. Extract language-specific details (test runners, framework idioms, CLI commands) into separate files within the skill directory (for example, `java-kotlin.md`, `python.md`).
- When two skills overlap significantly, merge them — prefer one skill with sections over two skills with duplicated concepts.
- When a skill is only useful in a specific project (not cross-project), it belongs in that project's repo, not in the shared skill registry.
- When a skill is consumed by multiple other skills (cross-cutting), document the integration in both directions: the provider skill lists an "Integration Points" section describing each consumer and how it integrates; each consumer skill adds a specific step in its workflow referencing the provider. This prevents drift and keeps each skill self-contained.
- When a skill produces substantial structured output (multi-section feedback, tables, formatted analysis), write to a temporary Markdown file and print only a summary + file path to the console. Console is not suitable for large text blocks; the file is the primary artifact for reading.
- Never hardcode personal paths, org-specific domains, project names, ticket prefixes, or team identifiers in skill files. Externalize environment-specific values to a user facts document (e.g., `facts.md`) and reference them by key. Skills in this repository are public — they must not contain any personal or sensitive information.
- When a skill needs environment-specific configuration (paths, domains, credentials), add a "Configuration (from facts document)" section listing required keys, their purpose, and fallback defaults.
- Every new skill directory must include `LICENSE.txt` (MIT; copy from `agents/skills/plans/LICENSE.txt`). Personal email belongs only in the LICENSE copyright line, not in `SKILL.md`.

## Testing Guidelines
- Validate command changes by running the command with realistic sample context.
- Confirm expected hard gates and required output structure still trigger.
- Ensure README command names, aliases, and paths match actual files.
- For `learn` flows, confirm lessons are placed in the correct scope and do not duplicate guidance.
- When reviewing uncommitted changes for confidential data, path leakage, or naming issues, inspect the actual changed file set from `git status --short`, including untracked files, before narrowing the review to a subset of files.
- Before committing skill or instruction changes, run the hygiene scan from `public_hygiene_scan_script` in user facts (exit 0 required). Deny patterns: `public_hygiene_patterns_file` (template: `docs/scan-public-hygiene.patterns.example`). Personal contact email is allowed only in `LICENSE.txt` copyright lines.

## Agent-Specific Runtime Safety
- Before host-level changes (package installs, shell profile edits), state execution context (host vs sandbox), expected impact, and rollback plan.
- Prefer isolated environments for Python dependencies used by commands or skills (for example, `$HOME/.agents/venvs/codex-tools`) before system-level overrides.
- Verify package availability in the selected package manager before proposing an install path.
- If a command is interrupted or aborted, verify partial side effects first, report the current state, then continue.

## Vendored Asset Sync Rules
- When syncing vendored agent assets (`agents/skills/`), apply full bidirectional sync: add new items, update changed items, and remove items that no longer exist in the source. Use `rsync --delete` semantics.
- Before syncing, diff source vs repo to identify additions, updates, and deletions explicitly.
- When a runtime source directory is itself a symlink (e.g. `~/.claude/skills → ../.agents/skills`), mirror this with a symlink in the repo (e.g. `claude/skills → ../agents/skills`) rather than a separate copy.
- After every sync or import of external files, scan all changed files for absolute paths and sensitive information (company domains, employee names, internal service names, environment names, internal URLs, credentials). Run the hygiene scan from user facts before commit. Mask sensitive content in both the repo copy and the origin source before committing.
- Do not vendor skills that are managed autonomously by an agent (e.g. `~/.codex/skills`). Only vendor skills from registries you manage directly (e.g. `~/.agents/skills`).
- Do not maintain a `create-documentation/` command that duplicates an existing skill in `agents/skills/`. The skill is the canonical form; remove the command copy and update all doc references to point to the skill.

## Commit & Pull Request Guidelines
Git history is currently minimal (`init`, `Readme added`), so use short, clear subjects and keep each commit scoped to one logical change.

- Preferred commit style: `<area>: <concise summary>` (example: `create-documentation: tighten create-tdd completeness rules`).
- PRs should include changed command files and rationale.
- PRs should call out behavior changes in command gates/output.
- PRs should update `README.md` when command names, paths, or usage changes.
