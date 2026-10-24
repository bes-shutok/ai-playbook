# Repository Guidelines

## Project Structure & Module Organization
This repository is a skill library. Each skill under `agents/skills/` is an executable prompt/instruction set packaged as a `SKILL.md`.

- `agents/skills/`: first-party and vendored skills; the canonical skill layer for this repository.
- `projects/.ai-playbook/`: shared cross-project guidelines and agent runtime folder mapping (`agent-runtime-layout.md`).
- `README.md`: source-of-truth index for the skill catalog and usage.
- `.opencode/command/`: local registration target used at runtime; create it locally as needed and avoid committing generated copies.

## Build, Test, and Development Commands
There is no compile/build pipeline. Main workflows are registration and execution.

- Commands live as skills under `agents/skills/`. Each agent loads them from its skill registry or symlink; register or alias them per agent as needed.
- Run a skill in direct mode (Codex example):
```bash
codex exec "$(cat agents/skills/tdd-design/SKILL.md)

Context:
$(cat ./context/tdd-input.md)"
```
- Audit files quickly:
```bash
rg --files
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh   # from instructions repo root; see public_hygiene_scan_script in user facts
```

## Coding Style & Naming Conventions
- Use Markdown with clear section headings and concise, enforceable instructions.
- Prefer imperative language for rules (for example, “Do X”, “Do not Y”).
- Keep skill names kebab-case and descriptive (for example, `tdd-design`).
- For non-trivial specs, include a terminology/core-concepts section near the top.
- Keep examples, Markdown links, and documented repo paths repository-relative; do not commit machine-specific absolute filesystem paths such as `/Users/...`.
- Verify actual on-disk runtime source folders before documenting which agent uses which commands or skills; do not guess from folder names alone.
- Keep detailed agent runtime folder mappings in `projects/.ai-playbook/agent-runtime-layout.md` and let `README.md` summarize and link instead of duplicating the full mapping.

## Skill Design Guidelines
- A skill must provide unique workflow logic or domain knowledge; do not create skills for behavior any competent agent should exhibit by default (for example, "look at existing code before implementing" or "run tests before claiming done").
- Keep the main `SKILL.md` language-agnostic. Extract language-specific details (test runners, framework idioms, CLI commands) into separate files within the skill directory (for example, `java-kotlin.md`, `python.md`).
- **Tool-agnostic design**: Write skills to work across multiple agents (Claude, Cursor, Codex, etc.). Avoid tool-specific references such as `AskUserQuestion`, specific tool names (`Write`, `Edit`, `Bash`), or agent type names (`general-purpose`, `claude-code-guide`). Describe behaviors by intent rather than implementation; for example, use "ask the user" instead of "use AskUserQuestion", "write to a file" instead of "use the Write tool", "launch a sub-agent" instead of "via the task tool". This allows each agent to use its own capabilities while following the same workflow.
- When two skills overlap significantly, merge them; prefer one skill with sections over two skills with duplicated concepts.
- When a skill is only useful in a specific project (not cross-project), it belongs in that project's repo, not in the shared skill registry.
- When a skill is consumed by multiple other skills (cross-cutting), document the integration in both directions: the provider skill lists an "Integration Points" section describing each consumer and how it integrates; each consumer skill adds a specific step in its workflow referencing the provider. This prevents drift and keeps each skill self-contained. When an Integration Points entry describes the peer skill's behavior, verify the claim against that skill's actual steps (read its `SKILL.md`) so the entry cannot over-claim or misattribute the peer's role.
- When a skill produces substantial structured output (multi-section feedback, tables, formatted analysis), write to a temporary Markdown file and print only a summary + file path to the console. Console is not suitable for large text blocks; the file is the primary artifact for reading.
- Never hardcode personal paths, org-specific domains, project names, ticket prefixes, or team identifiers in skill files. Externalize environment-specific values to a user facts document (e.g., `facts.md`) and reference them by key. Skills in this repository are public; they must not contain any personal or sensitive information.
- When a connected integration appears to lack an operation, inspect its capability-discovery surface before declaring it unavailable (see `docs/maintenance/development_lessons.md` #53).
- When a skill needs environment-specific configuration (paths, domains, credentials), add a "Configuration (from facts document)" section listing required keys, their purpose, and fallback defaults.
- Every new skill directory must include `LICENSE.txt` (MIT; copy from `agents/skills/plans/LICENSE.txt`). Personal email belongs only in the LICENSE copyright line, not in `SKILL.md`.

## Skill text anti-growth rules
These rules bind every session editing skill text, guidelines, or plans in this repository, and every review panel over such edits; they supersede directive D-12's meanwhile bind, docs/maintenance/operator-directives.md. No existing section absorbs them: the Skill Design Guidelines merge rule prices cross-skill duplication and its other bullets govern authoring and structuring skills, not the growth balance of existing operative text, and the Coding Style single-homing bullets fix documentation-mapping cases, not incident-dossier citation caps or per-file byte budgets, so the absence of a section whose predicate absorbs the case, named with those reasons, is the design input per the admission rule's own second sentence.
- Land the rule, not the story: the incident dossier, with its witness narrative, rejected alternatives, and dates, lives in the backlog row, the analysis document, or a changelog file; operative skill text cites it in at most one line.
- Name the home or the absence: a new top-level arm, section, or field names the existing section it extends and why that section's predicate cannot absorb the case; when no such section exists, that absence, named, is the design input.
- Pay for growth: once the repo-wide byte-budget gate lands, a change that grows a skill file past its cap deletes equivalent bytes in the same change, the gate's own breach report being the record, and no separate growth-debt note surface is added; until that landing, the same discipline applies at review time only.
- Price unbalanced growth: treat operative text that grew without a deletion as a finding class, recorded as one line in the review panels' existing finding-class documentation, never a new panel duty.

## Testing Guidelines
- Validate skill changes by running the skill with realistic sample context.
- Confirm expected hard gates and required output structure still trigger.
- Ensure README skill names and paths match actual files.
- For `learn` flows, confirm lessons are placed in the correct scope and do not duplicate guidance.
- When reviewing uncommitted changes for confidential data, path leakage, or naming issues, inspect the actual changed file set from `git status --short`, including untracked files, before narrowing the review to a subset of files.
- Before committing skill or instruction changes, run the hygiene scan from `public_hygiene_scan_script` in user facts (exit 0 required). Deny patterns: `public_hygiene_patterns_file` (template: `docs/scan-public-hygiene.patterns.example`). Personal contact email is allowed only in `LICENSE.txt` copyright lines.
- Whenever a change touches `agents/skills/review-agents/`, run `python3 scripts/check_review_agent_portability.py` (exit 0 required) to keep the shared catalogs free of stack-specific tokens (mirrors the hygiene-scan mandate), and run `python3 scripts/test_review_agent_doors.py` (exit 0 required) so the door-pattern registry (typed-catalog enumeration, helper-retarget-after-door, delivery-slice-meta) keeps its required actions.
- Run the `scripts/` test suites as `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_<name>.py -q`; this is the collector for plain-function suites, which unittest discovery silently collects none of. Keep the unittest form `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_<name>.py'` only for class-style suites; `scripts/` is not an importable package, so `python3 -m unittest scripts.test_<name>` fails at import. A collected count far below the suite file's test-definition count is a runner mismatch, not a small suite.

## Agent-Specific Runtime Safety
- Before host-level changes (package installs, shell profile edits), state execution context (host vs sandbox), expected impact, and rollback plan.
- Prefer isolated environments for Python dependencies used by commands or skills (for example, `$HOME/.agents/venvs/codex-tools`) before system-level overrides.
- Verify package availability in the selected package manager before proposing an install path.
- If a command is interrupted or aborted, verify partial side effects first, report the current state, then continue.
- A value quoted from conversation context is not evidence: before any precision-critical step (commit, landing, lock handling, digest verification), re-derive every digest, path, flag, or identifier from disk, and stop on a cross-check mismatch until it is resolved.
- When a public site's search requires an interactive challenge and the user offers to solve it, open the supplied link in the live browser and resume the lookup afterward (see `projects/.ai-playbook/development_lessons.md` #465).
- Run the done boundary setup as the first worktree action before editing any owned file; registry-row shape and ceremony-record digest requirements are pinned in docs/maintenance/development_lessons.md #80-#82.
- Shell tool calls reset cwd to the primary checkout between calls: in ad-hoc-worktree phases re-enter the worktree in every command and verify toplevel before writes or commits (see docs/maintenance/development_lessons.md #43).

## Machinery admission protocol

- Any addition that can block a lane names the incident it prevents (with a link), expected catch frequency, false-positive cost, and sunset or review date. No incident, no blocking gate.
- New machinery lands warning-only or read-only. Promote it only after a true catch and with a pre-registered registry-removal row naming its sunset and promotion criteria.
- Default to fewer blockers: every machinery plan names what it removes or simplifies, and a promoted blocker retires or demotes an existing blocker in the same change. Otherwise keep it non-blocking unless the operator explicitly approves net growth after a true catch.
- Bounded repair: when a gate blocks a lane, the allowed responses are a bounded retry, skip-with-report, or park-for-operator. Editing a gate or validator mid-lane to unblock oneself is forbidden without a plan. Additionally, an explicit operator direction to investigate and recover the blocked lane, issued in the blocked lane's session while the block stands, authorizes diagnosing the refusal, applying a safe workaround within existing authority, rerunning the refused gate, and continuing the interrupted work up to the lane's existing completion boundary; it never authorizes editing or bypassing the refused gate or validator, new machinery, or work beyond that boundary, and a block that remains unresolved falls back to the allowed responses above.

## Vendored Asset Sync Rules
- When syncing vendored agent assets (`agents/skills/`), apply full bidirectional sync: add new items, update changed items, and remove items that no longer exist in the source. Use `rsync --delete` semantics.
- Before syncing, diff source vs repo to identify additions, updates, and deletions explicitly.
- When a runtime source directory is itself a symlink (e.g. `~/.claude/skills → ../.agents/skills`), mirror this with a symlink in the repo (e.g. `claude/skills → ../agents/skills`) rather than a separate copy.
- After every sync or import of external files, scan all changed files for absolute paths and sensitive information (company domains, employee names, internal service names, environment names, internal URLs, credentials). Run the hygiene scan from user facts before commit. Mask sensitive content in both the repo copy and the origin source before committing.
- Do not vendor skills that are managed autonomously by an agent (e.g. `~/.codex/skills`). Only vendor skills from registries you manage directly (e.g. `~/.agents/skills`).
- A runtime-side catalog edit (per review-plan Iteration Discipline rule 5) must either land the vendored copy in the same run when the file is in the plan's scope, or leave a tracked landing path (a vendored-sync backlog item naming the changed files); never strand the vendored twin as orphan dirt.
- A run that files durable records lands them in the same run or leaves a tracked landing path; never strand them as untracked residue.
- Do not add a parallel command-file layer that duplicates a skill in `agents/skills/`; the skill is the canonical form. Remove the duplicate command copy and update all doc references to point to the skill.
- When removing or replacing a cross-cutting skill module (for example deleting a shared file under `agents/skills/_shared/` in favor of an on-demand skill), complete the migration in one pass: update every consumer skill reference, README and `agent-runtime-layout.md` catalog entries, migration templates, verify-script repo fingerprints, and bidirectional Integration Points before merge. Run `rg` for the deleted path after edits.
- `agents/skills/grilling/` and `agents/skills/grill-with-docs/` carry a deliberate local fork of their upstream sources (answer-state rule family, opt-in phrase, decision receipts, question economy, cadence rewrite, integration points; see each file's Local fork notice). An upstream sync of these directories must re-apply the fork from git history of these paths or consciously drop it with the decision recorded; never overwrite the fork silently. `agents/skills/i-have-adhd/` carries the same class of deliberate local fork (the portable `when_to_use` slash-only gate beside `disable-model-invocation`; see its Local fork notice), and the same re-apply-or-drop rule applies to an upstream sync of that directory. `agents/skills/handoff/` carries the same class of deliberate local fork (the portable `when_to_use` slash-only gate beside `disable-model-invocation`; see its Local fork notice), and the same re-apply-or-drop rule applies to an upstream sync of that directory.

## Workflow verb routing

Workflow verbs resolve to their owning skill under `agents/skills/` before improvised work: read its `SKILL.md` and follow its stages, gates, and artifact contract. Verbs without an owner use ordinary context gathering. Release-summary claims follow lesson #85 in `docs/maintenance/development_lessons.md`.

## Scheduling asks (verb contract)
- A "schedule at ..." ask schedules: list existing automations first, then create or patch one carrier (a live carrier already covering the ask's window and mandate is patched or reported, never stacked; see docs/maintenance/development_lessons.md #86), then report the automation id and its next fire time; it never executes the payload in the same turn.
- Satisfaction is session-owned: an ask is satisfied only by an automation record the asking session itself created, or its own record that it patched, whose id and next fire time the report carries; an automation record from another session (or any other carrier, such as a launchd job) is deconfliction context, never satisfaction.
- Deconfliction rides the created payload (re-derive from disk; skip-if-done, and report, when a parallel carrier already did the work; when the payload's work is not re-derivable from disk, the report names the overlapping carrier and the shared fire time), never a create refusal, and a session that cannot create after exhausting the scheduling fallback its runtime overlay sanctions reports the ask as unscheduled, never satisfied by reference.
- In a cap-refused bound session, the ask's fallback requires the delete-own-spawner leg exhausted first, per the operator-ordered schedule surface paragraph in agents/skills/maintenance/zcode.md, which owns this clause's ordering; a fallback armed without that leg's recorded deletion attempt or a proven-absent deletion primitive is an unscheduled ask, never satisfaction. (This clause supersedes, for exactly this clause, this section's standing sibling-span fence against delete-own-spawner and cap-refusal vocabulary; the fence still governs the section's other text.)
- A standing pending re-arm (a parked carrier-restoration record plus payload) takes precedence over a new one-shot execution ask: a user-started session holding the pending re-arm with one automation creation available restores the maintenance carrier first and spends the sole creation on it, then reports the execution ask as unscheduled, never satisfied by reference.
- An automation-born reduced-toolset session keeps session-owned satisfaction semantics: it preserves the pending record and payload for the next capable session and never treats another session's or another carrier's record as satisfaction of the ask.

## Commit & Pull Request Guidelines
Use short, clear subjects and keep each commit scoped to one logical change.

- Preferred commit style: `<area>: <concise summary>`.
- When a change completes a backlog row: an ad-hoc landing deletes the row from `docs/history/backlog/` in the same change rather than leaving a `Status: covered` stub; a landed plan instead flips its origin rows `Status: covered (<plan path>)` in place and, in its completion pass, folds a `## Disposition of migrated backlog items` section onto the archived plan and deletes the origin file, the shape the origins gate accepts (a bare deletion without the fold fails closed; `docs/history/backlog/completed/` stays empty; see the plans skill's Plan Lifecycle and `docs/maintenance/development_lessons.md` #104). Name the covering commit or completed plan as the witness in the commit message, and tidy other rows' `Cluster:` pointers at removed rows in the same commit.
- PRs should include changed skill files and rationale.
- PRs should call out behavior changes in skill gates/output.
- PRs should update `README.md` when skill names, paths, or usage changes.
