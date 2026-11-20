# Plan: PR-reference prompt hook skill-name ownership

Backlog origin: docs/history/backlog/2026-11-09-pr-review-reminder-hook-names-nonexistent-skill.md
Driving force: reliability
Plan review record: the staging series .ai-playbook/reviews/2026-11-15-plan-review-pr-review-hook-skill-name-ownership-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically; `pr-review-hook-skill-name-ownership` is the canonical artifact slug, the plan's feature slug lowercased)
Execution budget: 2h total, largest task 1h
Executed: yes (ddfb9cbfac417a17710dbfcb7972e093910b47eb)
Authoring claim: 2026-11-09-pr-review-reminder-hook-names-nonexistent-skill.md (session sess_32f7c1b6-2eb3-4361-9e49-750630a18a77)

Driving-force justification: `reliability` is outside the closed taxonomy's five principles; it is implemented anyway because a prompt hook pointing at a retired skill name silently misroutes review work on every pull-request prompt (19 witnessed injections in one session), and park-triage would not take it: the fix is small, witnessed, and removes a recurring dead-name lookup rather than adding machinery.

## Terms

- pr-skill-reminder: the Claude `UserPromptSubmit` hook (today `~/.claude/scripts/pr-skill-reminder.sh`) that injects a code-review-skill reminder when a prompt references a pull request.
- receiving-review: the live passive-review skill (`agents/skills/receiving-review/`); `receiving-code-review` is its retired name.
- hooks probe: `scripts/hooks_probe.py`, the read-only install diagnostic whose matrix comes from the `[[hook_profiles]]` rows in `projects/.ai-playbook/execute-plan-runtime-inventory.toml`.
- installed skills roots: `~/.claude/skills/` and `~/.agents/skills/`, the directories a skill name must resolve under on this host.

## Why

A user-level prompt hook tells the agent to invoke a skill name that no longer exists, and the hook is not versioned with the repository's other hooks, so skill renames never reach it. Versioning the hook beside its siblings and probing the skill names it emits makes the next rename observable instead of silently dead.

## Gist & Examples

TLDR: the PR-reference hook moves into `agents/hooks/` with its skill name fixed and a probe assertion over emitted skill names, so a skill rename cannot leave the hook pointing at a dead name.

- Before: a prompt like "look at github.com/o/r/pull/12" injects a reminder naming `receiving-code-review`, which resolves to no installed skill; the agent recovers only because the user typed the right slash command. The hook lives only at `~/.claude/scripts/pr-skill-reminder.sh`, so the repository's rename fan-out never touches it.
- After: the same prompt injects a reminder naming `receiving-review`; a prompt already beginning with a slash command that names an installed skill (`/receiving-review ...`) injects nothing; the hook's source of record is `agents/hooks/pr-skill-reminder/` with install and probe wiring documented like its siblings; and `python3 scripts/hooks_probe.py --all` both reports the hook's wiring and asserts that every skill name a versioned hook emits resolves under the installed skills roots.

## Outcome

Give the PR-reference prompt hook a tracked, probed home so its skill references stay live across renames.

- A pull-request prompt injects a reminder naming the real passive-review skill (`receiving-review`), so the agent stops looking for an uninstalled skill.
- An explicit slash-command prompt no longer receives a redundant injection.
- The next skill rename that affects a versioned hook is caught by the hooks probe instead of being discovered at prompt time.

Gate delta: adds one read-only assertion to the existing hooks probe and one `[[hook_profiles]]` registry row; no refusal path, fence, protocol layer, schema field, or dispatch-pausing condition is added, and none is removed (the probe stays advisory diagnostics; the assertion is a probe check, not a gate).

## Assumptions

- assume the hook stays Claude-only (one script, no per-agent adapters); basis: the witnessed hook is wired only in `~/.claude/settings.json`, and the four-adapter convention belongs to the lessons-recall and skill-gate corpus hooks.
- assume the versioned script keeps its jq-based stdin extraction; basis: Claude hosts ship `jq`, and the jq-free python-parse convention in `agents/hooks/lessons-recall/README.md` is scoped to the four corpus adapters.
- assume the slash-command skip resolves to a leading-`/`-token check whose token names an installed skill (the leading token matches a directory under one of the installed skills roots); basis: the origin's wording "already begins with a slash command that names a skill", so a non-skill slash command carrying a PR reference keeps the reminder.
- assume the probe assertion resolves skill names against both installed skills roots; basis: `~/.claude/skills/` and `~/.agents/skills/` verified present on this host, both serving the same skill catalog.
- Sources inspected: not a tracker-linked request.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the versioned script injects the reminder with the live skill name and skips injection for slash-command prompts; verified by running the script against representative stdin payloads.
- maintainability: the hook is versioned under `agents/hooks/pr-skill-reminder/` with install and probe wiring documented like its siblings, and `python3 scripts/hooks_probe.py --all` reports it.
- regression safety: the existing hooks probe suite passes apart from the added rows and assertions.

**Done when:**
- `agents/hooks/pr-skill-reminder/pr-skill-reminder.sh` exists, is executable, and contains no `receiving-code-review` string.
- Feeding the script a prompt containing `github.com/o/r/pull/12` emits the reminder naming `receiving-review`; feeding a prompt beginning with `/receiving-review` that also carries a PR reference (`/receiving-review check github.com/o/r/pull/12`) emits nothing; feeding a prompt beginning with a slash token naming no installed skill that carries a PR reference (`/deploy-feature check github.com/o/r/pull/12`) keeps the reminder; feeding a prompt with no pull-request reference emits nothing.
- The inventory carries a `Claude` / `pr-skill-reminder` profile row and the probe reports the hook's wiring.
- The probe's skill-name assertion reports a failure for a fixture hook referencing a nonexistent skill and passes for the repository-versioned hooks under `agents/hooks/*/`.
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_hooks_probe.py -q` passes.

**Ship when:**
- The deployed hook on the operator's host resolves to the versioned copy: the user-level script replaced by a symlink into the repository checkout, the `~/.claude/settings.json` registration unchanged. [class: OPERATIONS_FOLLOW_UP] Owner: the operator session applying the install step at execution closeout. Closure condition: `readlink ~/.claude/scripts/pr-skill-reminder.sh` resolves into the repository checkout.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/hooks/pr-skill-reminder/pr-skill-reminder.sh` (Task 1) *(new)*
- `agents/hooks/pr-skill-reminder/README.md` (Task 1) *(new)*
- `agents/hooks/lessons-recall/README.md` (Task 1)
- `projects/.ai-playbook/execute-plan-runtime-inventory.toml` (Task 2)
- `scripts/hooks_probe.py` (Task 2)
- `scripts/hooks_probe.py` (Task 3)

**Tests:**
- `scripts/test_hooks_probe.py` (Task 2)
- `scripts/test_hooks_probe.py` (Task 3)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Documentation:** production code and tests use the explicit list. Docs may also be in scope under plan-related extension when a change is substantively required to keep docs aligned with the feature; not every path needs listing upfront. A doc-closure task should include search/grep for stale references, not only pre-listed paths.

**Out of scope; reject unless plan-related:**
- `~/.claude/settings.json` and any other path under `~/.claude/` or `~/.codex/`; host-level deployment is the Ship-when operations follow-up, not repository work.
- `docs/history/backlog/PLAN-PROMPTS.md`; the rolling log is governed by its own write discipline, not this plan.

## Validation Commands

```bash
python3 scripts/hooks_probe.py --all
python3 scripts/hooks_probe.py --selftest
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_hooks_probe.py -q
bash -n agents/hooks/pr-skill-reminder/pr-skill-reminder.sh
```

### Task 1: Version the hook with the corrected skill name and slash-command skip

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/hooks/pr-skill-reminder/pr-skill-reminder.sh` *(new)*
- `agents/hooks/pr-skill-reminder/README.md` *(new)*
- `agents/hooks/lessons-recall/README.md`

Primary class anchors:
- `emit_reminder` in `agents/hooks/pr-skill-reminder/pr-skill-reminder.sh`

- [x] Corrected injection: given stdin `{"prompt": "look at github.com/o/r/pull/12"}`, the script's reminder output names `receiving-review` and contains no `receiving-code-review` string [class: IMPLEMENTATION_REQUIRED]
- [x] Slash-command skip: given stdin `{"prompt": "/receiving-review check github.com/o/r/pull/12"}` (slash command plus a PR reference, the input the unmodified hook injects for), the script emits nothing on stdout [class: IMPLEMENTATION_REQUIRED]
- [x] Slash-command passthrough: given stdin `{"prompt": "/receiving-review check the PR comments"}` (slash command, no PR reference), the script also emits nothing on stdout [class: IMPLEMENTATION_REQUIRED]
- [x] Non-skill slash keep-branch: given stdin `{"prompt": "/deploy-feature check github.com/o/r/pull/12"}` (a leading slash token naming no installed skill, plus a PR reference, the input class the narrowed rule protects), the script emits the reminder naming `receiving-review` [class: IMPLEMENTATION_REQUIRED]
- [x] Syntax gate: `bash -n agents/hooks/pr-skill-reminder/pr-skill-reminder.sh` exits 0 [class: IMPLEMENTATION_REQUIRED]
- [x] Non-PR passthrough: given stdin `{"prompt": "hello"}`, the script emits nothing on stdout and exits 0 [class: IMPLEMENTATION_REQUIRED]
- [x] README documents the hook's purpose, the independent-hooks boundary versus lessons-recall (pointer, not a restatement), the install pattern (the user-level script path becomes a symlink to the repository copy; the settings registration is unchanged), and the jq dependency [class: IMPLEMENTATION_REQUIRED]
- [x] The lessons-recall README's boundary note points at the versioned home instead of the bare user-level script name [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: version pr-skill-reminder hook with corrected skill name` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Register the hook with the hooks probe

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `projects/.ai-playbook/execute-plan-runtime-inventory.toml`
- `scripts/hooks_probe.py`
- `scripts/test_hooks_probe.py`

Primary class anchors:
- `probe_matrix` in `scripts/hooks_probe.py`
- `_assess_wiring` in `scripts/hooks_probe.py`

- [x] Inventory row: a `[[hook_profiles]]` row with agent `Claude`, hook `pr-skill-reminder`, expected `FULL`, runtime id `claude`, adapter `~/.claude/scripts/pr-skill-reminder.sh`, event `UserPromptSubmit` (the row's `event` key is read unconditionally by the probe's wiring check) [class: IMPLEMENTATION_REQUIRED]
- [x] Probe selftest pin: update the probe's `frozen_agents_listed` cell-count pin to the new cell count (13) and re-run `python3 scripts/hooks_probe.py --selftest` [class: IMPLEMENTATION_REQUIRED]
- [x] Wiring verdict: for Claude, the probe reports `FULL` when the registered hook commands reference the `pr-skill-reminder` hook name and the adapter path, and `NONE` otherwise; no other agent gains a row [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: `python3 scripts/hooks_probe.py --all` before the row exists reports no `pr-skill-reminder` row (tests, fixtures, and commands are selected at execution from repository evidence) [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the `pr-skill-reminder` cell appears in `python3 scripts/hooks_probe.py --all` output reporting FAIL with the `malformed adapter` diagnostic while the deployed adapter is a regular file [class: REPOSITORY_TEST]
- [x] Pass signal: the cell-level verdict, never the `--all` exit code, which is 1 on this host from pre-existing ambient FAIL cells unrelated to this plan [class: REPOSITORY_TEST]
- [x] Probe suite covers the new wiring verdict for both the wired and unwired shapes [class: REPOSITORY_TEST]
- [x] Commit: `feat: register pr-skill-reminder in the hooks probe` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Skill-name existence assertion in the probe

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/hooks_probe.py`
- `scripts/test_hooks_probe.py`

Primary class anchors:
- `probe_skill_name_references` in `scripts/hooks_probe.py`

- [x] Assertion behavior: for each repository-versioned hook script under `agents/hooks/*/`, the probe extracts skill-name references (backtick-quoted identifiers on a line that also mentions a skill) and asserts each resolves under an installed skills root [class: IMPLEMENTATION_REQUIRED]
- [x] Assertion population: the versioned hooks under `agents/hooks/*/` are the input population (the rename-fan-out surface the probe guards); the exact extraction pattern is selected at execution from the real hook scripts' text so every real versioned hook passes [class: IMPLEMENTATION_REQUIRED]
- [x] Missing-name failure: given a fixture hook script referencing a skill name that resolves under no installed skills root, the probe reports the failure naming the hook and the missing name [class: IMPLEMENTATION_REQUIRED]
- [x] Real-hook pass: given the repository's real versioned hook scripts, the assertion passes with every referenced name resolving [class: IMPLEMENTATION_REQUIRED]
- [x] Probe suite covers the extraction and both the failure and pass verdicts [class: REPOSITORY_TEST]
- [x] Commit: `feat: assert emitted skill names exist in the probe` [class: IMPLEMENTATION_REQUIRED]
