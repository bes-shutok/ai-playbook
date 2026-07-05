# Plan: Agent Hooks Workflow v2 (Parity, Precision, Gates)

Created with the **plans** skill. Phase 0 branch: `2026-07-04-agent-hooks-workflow-v2`. Phase 1 requirements: `docs/tmp/plan-requirements-agent-hooks-v2.md`.

Follow-up to `docs/plans/2026-07-01-lessons-recall-hook.md` (r20 READY, all tasks complete).

Plan review: `docs/reviews/2026-07-04-plan-review-agent-hooks-workflow-v2-r4.md` (r4: READY - 0 Blocker / 0 Medium / 2 Low / 2 Monitor)
Plan review: `docs/reviews/2026-07-04-plan-review-agent-hooks-workflow-v2-r3.md` (r3: Not ready - 0 Blocker / 1 Medium; r2 closed)
Plan review: `docs/reviews/2026-07-04-plan-review-agent-hooks-workflow-v2-r2.md` (r2: Not ready - 0 Blocker / 2 Medium; r1 closed)
Plan review: `docs/reviews/2026-07-04-plan-review-agent-hooks-workflow-v2-r1.md` (r1: Not ready - 1 Blocker / 5 Medium)

## Terms

- **Predecessor plan**: `2026-07-01-lessons-recall-hook.md`; cores in `scripts/`, adapters in `agents/hooks/`.
- **Frozen adapters**: `claude.sh`, `codex.sh`, `agy.sh`, and all three non-Cursor `skill-gate` adapters. v2 MUST NOT edit their stdin parsing, envelope shapes, exit codes, or session-arg glue unless a Task explicitly unfreezes them after a regression failure (none planned).
- **Cursor-only surface**: `cursor-session-bridge.sh` and Cursor sections of README/install docs. Shared cores may gain backward-compatible extensions only.
- **Capability probe**: stdlib leaf `hooks_probe.py`; PASS / DEGRADED / UNSUPPORTED per (agent, hook).
- **Session channel**: `session_channel.py` subprocess output; hashed to marker/state `session` component. v1: Claude-only. v2 adds optional Cursor env **without changing output when that env is unset**.
- **Cursor session env bridge**: `sessionStart` hook emits `{"env":{"CURSOR_SESSION_ID":"<session_id>"}}`; Cursor passes env to later hooks in the same composer session.
- **Classifier v2**: `classify_prompt_v2` (phrase + task verb within proximity window). **Default remains v1** (`--classifier v1`) for all agents until operator opts in.
- **Gated class registry**: promoted table in `skill_gate.py` mapping path suffixes to `(skill_name, marker_prefix, deny_message)`.
- **Family D single source**: shared artifacts (`session_channel.py`, `resolve_project_key`, marker WRITE RECIPE) not duplicated in adapters/skills.

## Gist & Examples

v1 hooks work. Monitor items and user constraint ("other agent types must not be affected") drive a **Cursor-first, additive** v2.

**What changes for Cursor only:** a new `sessionStart` bridge exports Cursor's `session_id` into `CURSOR_SESSION_ID`. Subsequent hooks in that composer tab derive a per-tab `session` hash (skill-gate markers and recall dedup state no longer alias across tabs). The existing `cursor.sh` family index one-shot stays; per-prompt recall remains blocked on Cursor product schema (`beforeSubmitPrompt` has no `additional_context`).

Example: two Cursor tabs on the same repo today share `plans.<project>.no-session.marker`. After bridge install, tab A and tab B get different marker filenames; a plans-marker in tab A does not admit tab B's plan Write.

**What stays the same for Claude, Codex, agy:**

| Agent | lessons-recall steady state | skill-gate steady state | Adapter files touched in v2 |
|-------|----------------------------|-------------------------|----------------------------|
| Claude | Per-prompt UserPromptSubmit, `CLAUDE_CODE_SESSION_ID` | PreToolUse block, env-var session | **None (frozen)** |
| Codex | SessionStart one-shot (degraded) | Adapter exists; config unwired (degraded) | **None (frozen)** |
| agy | PreInvocation (best-effort) | PreToolUse block (live) | **None (frozen)** |
| Cursor | SessionStart index + optional bridge | PreToolUse block (live) | bridge + README only |

**Shared-core changes (backward compatible):**

- `session_channel.py`: if `CURSOR_SESSION_ID` unset, stdout is **byte-identical to v1** (Claude var or empty). Claude precedence when both set.
- `lessons_classify.py` / `lessons_recall.py`: add v2 classifier behind `--classifier v2`; **default v1** so Claude recall behavior unchanged.
- `skill_gate.py`: registry + `learn` gated class; existing `plans` class behavior unchanged; non-lessons paths still ungated.
- New read-only leaves: `hooks_probe.py`, `hooks_log_summary.py` (no runtime effect on agents).

**Problem: recall precision (opt-in).** v1 incidental matches (e.g. "dropped" in a comment) inject noise. v2 adds phrase+verb proximity but ships as opt-in because the v1 flagship prompt "the report dropped a row" has no task verb and must keep working on default v1.

**Problem: learn skill not gated.** v2 adds `learn.*.marker` for project corpus path only (`done` deferred).

**Problem: silent degradation.** `hooks_probe --all` reports wiring state; `hooks_log_summary` surfaces recall suppress ratio from `hooks.log`.

**Deferred (OUT):** Cursor per-prompt recall until product adds injection; Codex `pre_tool_use` wiring; `done` gating; copy-sync lessons script migration.

## Evaluation Criteria

**Quality dimensions:**
- **Agent non-regression (hard):** Claude, Codex, agy adapter echo-pipes from predecessor Validation Commands produce the same allow/block/inject/empty outcomes as v1; frozen adapter files have zero diff unless Task 7 documents an emergency unfreeze.
- **Session channel backward compat:** with `CURSOR_SESSION_ID` unset and Claude var unset, `session_channel.py` stdout is empty; with only `CLAUDE_CODE_SESSION_ID` set, behavior unchanged from v1 selftests.
- **Parity (Cursor, optional install):** with bridge installed, two distinct Cursor `session_id` values produce two distinct marker filename `session` components for the same `project`.
- **Classifier v2 isolation:** `--classifier v2` selftests pass; default `--classifier v1` (or omitted flag) passes all existing v1 `#prompt_*` selftests unchanged.
- **Probe honesty:** `hooks_probe.py` never PASS when adapter symlink or config registration is missing.
- **Learn gate:** blocks project lessons path without fresh marker; allows with marker; fail-open unchanged.

**Release gates:**
- All `--selftest` targets exit 0 (including new leaves).
- Task 7 four-agent echo-pipe matrix GREEN (repo-relative paths under `agents/hooks/`).
- `python3 scripts/skill_gate.py --selftest` and `python3 scripts/lessons_recall.py --selftest` green with default classifier v1.
- `check-no-em-dash.sh` clean on changed files.
- Predecessor hooks (`pr-skill-reminder.sh`, `learn-counter`, plan review gates) still independent.

## Review Scope

**Explicit must-fix:**

**Production code (new):**
- `scripts/hooks_probe.py` *(new)*
- `scripts/hooks_log_summary.py` *(new)*
- `agents/hooks/lessons-recall/cursor-session-bridge.sh` *(new)*

**Production code (modified):**
- `scripts/session_channel.py` *(modify; optional Cursor env only)*
- `scripts/lessons_classify.py` *(modify; add v2, default v1)*
- `scripts/lessons_recall.py` *(modify; `--classifier` flag, default v1)*
- `scripts/skill_gate.py` *(modify; registry + learn class)*

**Production code (modified, Cursor-only):**
- `agents/hooks/lessons-recall/cursor.sh` *(modify; comments + session-bridge dependency note ONLY; no envelope or extraction logic change)*

**Docs / skills (modified):**
- `agents/hooks/lessons-recall/README.md`
- `agents/hooks/skill-gate/README.md`
- `agents/skills/learn/SKILL.md`
- `docs/AGENTS.md`

**Frozen (reject findings unless plan-related regression fix):**
- `agents/hooks/lessons-recall/claude.sh`
- `agents/hooks/lessons-recall/codex.sh`
- `agents/hooks/lessons-recall/agy.sh`
- `agents/hooks/skill-gate/claude.sh`
- `agents/hooks/skill-gate/codex.sh`
- `agents/hooks/skill-gate/agy.sh`
- `agents/hooks/skill-gate/cursor.sh` *(logic frozen; picks up new session via subprocess automatically)*

**Out of scope:**
- Host `~/.cursor/hooks.json`, `~/.claude/settings.json`, etc. (documented install only).
- `done` skill gating.
- Codex/Cursor `beforeSubmitPrompt` injection.

**Plan-related extension:** Cursor live smoke and probe output may require README-only corrections.

## Design Invariants (CR Guard)

**From predecessor (unchanged):**

1. Agent-agnostic cores never import `session_channel.py`.
2. Adapters/skills derive session via `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"` verbatim (bridge writes env; does not change this idiom).
3. `facts_paths.resolve_project_key` is the sole project hash source.
4. json.dumps envelopes; python3 stdin parse (not jq).
5. Skill-gate fail-open on store errors; absent marker blocks.
6. Recall adapters always exit 0.
7. Symlink install model.
8. FULL dedup/gate windows for project-only agents.

**v2 agent non-regression (new):**

9. **Frozen adapter policy:** Tasks 1-6 MUST NOT edit frozen adapter files. Cursor bridge is a NEW file; `cursor.sh` changes limited to comments unless echo-pipe proves regression.
10. **session_channel v1 fallback:** When `CURSOR_SESSION_ID` is unset, `_derive()` output MUST match v1 for all v1 selftest arms (empty and Claude-set cases).
11. **Claude precedence:** If both `CLAUDE_CODE_SESSION_ID` and `CURSOR_SESSION_ID` are set, Claude wins (Claude hooks never inherit Cursor env accidentally).
12. **Classifier default v1:** `lessons_recall` CLI default `--classifier v1`; v2 only via explicit flag. v1 `#prompt_realistic` selftests MUST pass without flag changes.
13. **Codex/agy steady state preserved:** With bridge env unset, Codex/agy adapters still omit `--session-id` and key `no-session` (adapter-glue selftest from v1 still passes).
14. **Learn gate additive:** New gated class MUST NOT change `classify_path` outcome for plan files or non-lessons paths.

## Validation Commands

```bash
# Cores and leaves
python3 scripts/session_channel.py --selftest
python3 scripts/lessons_classify.py --selftest
python3 scripts/lessons_recall.py --selftest
python3 scripts/skill_gate.py --selftest
python3 scripts/hooks_probe.py --selftest
python3 scripts/hooks_log_summary.py --selftest

# Classifier default is v1 (non-regression)
python3 scripts/lessons_recall.py --prompt "the report dropped a row" | test -n "$(cat)"

# Optional v2
python3 scripts/lessons_recall.py --classifier v2 --prompt "debug why the report dropped a row" | test -n "$(cat)"

# Probe (host)
python3 scripts/hooks_probe.py --all

# Four-agent echo-pipe matrix (repo adapters; same contracts as predecessor plan)
echo '{"prompt":"the report dropped a row"}' | bash agents/hooks/lessons-recall/claude.sh
echo '{"prompt":"fix the typo"}' | bash agents/hooks/lessons-recall/claude.sh | test -z "$(cat)"
echo '{"tool_name":"Write","tool_input":{"file_path":"docs/plans/x.md"}}' | bash agents/hooks/skill-gate/claude.sh

echo '{"prompt":"the report dropped a row"}' | bash agents/hooks/lessons-recall/codex.sh
echo '{"tool_input":{"filePath":"docs/plans/x.md"}}' | bash agents/hooks/skill-gate/codex.sh

echo '{"prompt":"the report dropped a row"}' | bash agents/hooks/lessons-recall/agy.sh
echo '{"toolCall":{"args":{"path":"docs/plans/x.md"}}}' | bash agents/hooks/skill-gate/agy.sh

bash agents/hooks/lessons-recall/cursor.sh <<< '{}' | python3 -c 'import json,sys; json.loads(sys.stdin.read() or "{}")'
echo '{"session_id":"cursor-tab-test-1"}' | bash agents/hooks/lessons-recall/cursor-session-bridge.sh | python3 -c 'import json,sys; o=json.loads(sys.stdin.read() or "{}"); assert "env" in o'

# Adapter glue: empty session channel -> no --session-id in argv (codex representative)
env -u CLAUDE_CODE_SESSION_ID -u CURSOR_SESSION_ID bash -c '
  SID="$(python3 scripts/session_channel.py)"
  test -z "$SID"
'

# Hygiene
bash ~/.ai-playbook/scripts/check-no-em-dash.sh \
  agents/hooks/ scripts/hooks_probe.py scripts/hooks_log_summary.py \
  docs/plans/2026-07-04-agent-hooks-workflow-v2.md
```

## Monitor

- Cursor `beforeSubmitPrompt`: re-check on upgrade; fast-follow when `additional_context` lands.
- Codex `pre_tool_use`: probe should flip from DEGRADED to PASS; wire config only.
- Classifier v2: opt-in until corpus tuning; promote to default only in a follow-on plan after v1 realistic set is re-seeded with task verbs.
- Learn gate: project corpus only; user-level corpus deferred.
- **Frozen adapter diff gate:** Task 7 MUST include `git diff --name-only` asserting zero changes under frozen paths (or explain emergency unfreeze in commit message).
- **Cursor two-tab smoke (owner: Task 6):** optional live smoke; `skill_gate --selftest#distinct_cursor_session_components` is the required backstop when live smoke skipped.
- **Classifier v2 opt-in (owner: Task 3/README):** frozen adapters never pass `--classifier v2`; production recall stays v1 until a follow-on plan wires adapter opt-in; `hooks_probe` notes core default v1.

---

### Task 1: Cursor session channel bridge (Cursor-only install surface)

Files:
- `agents/hooks/lessons-recall/cursor-session-bridge.sh` *(new)*
- `scripts/session_channel.py` *(modify)*
- `scripts/skill_gate.py` *(modify: add `#distinct_cursor_session_components` selftest arm only)*
- `agents/hooks/lessons-recall/README.md` *(modify)*

- [x] `session_channel --selftest#cursor_session_id_from_env`; given `CURSOR_SESSION_ID=abc-123` and Claude var UNSET, expects stdout `abc-123`
- [x] `session_channel --selftest#precedence_claude_over_cursor`; given BOTH env vars set, expects Claude value
- [x] `session_channel --selftest#v1_fallback_unchanged`; with `CURSOR_SESSION_ID` UNSET, ALL pre-v2 selftest arms still pass (SET, UNSET, empty-string Claude env; Cursor env ignored)
- [x] `session_channel --selftest#cursor_empty_string_env`; `CURSOR_SESSION_ID=""` with Claude unset -> stdout empty; with Claude set -> Claude value
- [x] Implement `cursor-session-bridge.sh`: read `sessionStart` JSON, extract `.session_id`, emit `{"env":{"CURSOR_SESSION_ID":"<id>"}}` via json.dumps; missing id -> `{}`; exit 0 always
- [x] Extend `_derive()`: `CLAUDE_CODE_SESSION_ID or CURSOR_SESSION_ID or ""`
- [x] README: bridge FIRST in `sessionStart` array; document optional install (without bridge, Cursor stays v1 `no-session`); INSTALL adds `ln -sf` for `cursor-session-bridge.sh` -> `~/.cursor/hooks/` (new filename; does not clobber existing hooks)
- [x] Run -> expect GREEN: `python3 scripts/session_channel.py --selftest`
- [x] `skill_gate --selftest#distinct_cursor_session_components`; two distinct raw session channel values produce two distinct `_derive_session_component()` hashes (marker filename isolation backstop; NOT session_channel leaf)
- [x] Commit: `feat(hooks): Cursor session id bridge (optional, backward compatible)`

### Task 2: Capability probe

Files:
- `scripts/hooks_probe.py` *(new)*
- `agents/hooks/lessons-recall/README.md` *(modify)*
- `agents/hooks/skill-gate/README.md` *(modify)*

- [x] `hooks_probe --selftest#frozen_agents_listed`; PROBE_MATRIX includes Claude/Codex/agy/Cursor rows with expected tier (Claude FULL, Codex lessons DEGRADED, etc.)
- [x] `hooks_probe --selftest#detects_symlink_dangle`; dangling symlink -> FAIL
- [x] Implement stdlib probe; `--all` human table; exit 1 on FAIL only
- [x] README: weekly probe cron one-liner; honest steady-state table per agent
- [x] Run -> expect GREEN: selftest
- [x] Commit: `feat(hooks): agent capability probe`

### Task 3: Classifier v2 (opt-in; default v1)

Files:
- `scripts/lessons_classify.py` *(modify)*
- `scripts/lessons_recall.py` *(modify)*

- [x] Pin classifier v2 spec: `TASK_VERBS` list (minimum: debug, fix, investigate, trace, verify, explain, check, review); proximity window (FLAGGED: 80 chars); new `classify_prompt_v2(prompt)` (phrase match AND task verb within window; same `PROMPT_FAMILY_ORDER` as v1)
- [x] `lessons_classify --selftest#v2_false_positive_comment`; "the typo fix dropped a word in the comment" -> None under v2
- [x] `lessons_classify --selftest#v2_flagship_no_verb`; "the report dropped a row" -> None under v2 (confirms v2 is opt-in only; v1 flagship stays on default v1)
- [x] `lessons_classify --selftest#v2_true_positive`; "debug why the report dropped a row" -> family G under v2
- [x] `lessons_classify --selftest#v1_default_unchanged`; ALL existing v1 `#prompt_*` selftests pass with default classifier (no flag)
- [x] `lessons_recall --selftest#default_classifier_v1`; core default `--classifier v1`; v1 recall selftests unchanged
- [x] Thread `--classifier` through `_consult(..., classifier=...)` dispatch (`classify_prompt` vs `classify_prompt_v2`); default v1 when omitted
- [x] Append recall observability to `hooks.log` on EVERY consultation (match or no-match): JSONL with `event=recall`, `outcome=fire|suppress-dedup|suppress-classify` (`suppress-classify` = no family match; `suppress-dedup` = matched but deduped); schema pinned in Task 4
- [x] `lessons_recall --selftest#recall_log_fire_and_suppress`; isolated temp `hooks.log`, live `_consult` calls assert JSONL lines match pinned schema (fire on match+inject; suppress-classify on no-match; suppress-dedup on repeat)
- [x] Run -> expect GREEN: classify + recall selftests
- [x] Commit: `feat(lessons-recall): opt-in classifier v2`

### Task 4: Hooks log observability

Files:
- `scripts/hooks_log_summary.py` *(new)*
- `agents/hooks/lessons-recall/README.md` *(modify: Observability section)*

- [x] `hooks_log_summary --selftest#empty_log`; missing log -> exit 0, zero counts
- [x] `hooks_log_summary --selftest#suppress_ratio`; fixture log with Task 3 `event=recall` lines -> correct fire/suppress counts
- [x] Implement read-only JSONL parser for Task 3 recall schema (`event=recall`, `outcome=fire|suppress-dedup|suppress-classify`); `--days N`; also report `keying=*` and `no-anchor` counts
- [x] README Observability: document recall JSONL schema (`event`, `outcome`, optional `family`); coexistence with legacy `keying` lines; pointer to `hooks_log_summary.py`
- [x] Run -> expect GREEN: selftest
- [x] Commit: `feat(hooks): hooks.log summary tool`

### Task 5: Skill-gate learn class + registry

Files:
- `scripts/skill_gate.py` *(modify)*
- `agents/hooks/skill-gate/README.md` *(modify)*
- `agents/skills/learn/SKILL.md` *(modify)*

- [x] `skill_gate --selftest#block_learn_without_marker`; `docs/maintenance/development_lessons.md` path, no marker -> block with learn deny message
- [x] `skill_gate --selftest#allow_learn_with_fresh_marker`; fresh `learn.*.marker` -> allow
- [x] `skill_gate --selftest#plans_class_unchanged`; plan path allow/block byte-identical to pre-refactor v1 (registry must not alter plans arm)
- [x] `skill_gate --selftest#learn_path_non_lessons`; other paths under `docs/maintenance/` NOT gated
- [x] `skill_gate --selftest#learn_cross_tree_absolute_target`; gate cwd in worktree, absolute target to main repo `docs/maintenance/development_lessons.md` -> BLOCK without marker; fresh `learn.*.marker` -> ALLOW (mirrors plans `#cross_tree_absolute_target_classified`)
- [x] Promote registry tuple `(path_matcher, marker_prefix, deny_message)`; refactor `_consult` to resolve class, `check_marker(..., marker_prefix=...)`, per-class deny message; learn matcher: structural suffix `docs/maintenance/development_lessons.md` on `realpath(target)` (Arm 2 discipline, not cwd-only join); import/reference `lessons_recall.PROJECT_CORPUS_REL` as Family D constant check
- [x] Refactor `_marker_path` and `_write_marker` to accept registry-resolved `marker_prefix` (default `plans`)
- [x] Extend CLI: `--write-marker [class]` default `plans` when flag present without value (bare `--write-marker` unchanged for plans skill); `--write-marker learn` writes `learn.<project>.<session>.marker`
- [x] `skill_gate --selftest#write_marker_learn_cli`; public CLI `skill_gate.py --write-marker learn --session-id ...` creates `learn.<project>.<session>.marker`
- [x] Pin learn block message (EXACT): `Invoke the learn skill before editing the project lessons corpus.`
- [x] skill-gate README: learn marker WRITE RECIPE section (reference plans recipe; learn class only)
- [x] learn SKILL.md: marker refresh before EVERY project-corpus Write/Edit (mirror plans skill); rewrite Step 6.6 project-tier text (project corpus IS skill-gate gated; user corpus remains Step 6.6 script gate only)
- [x] Run -> expect GREEN: `python3 scripts/skill_gate.py --selftest`
- [x] Commit: `feat(skill-gate): learn class (additive)`

### Task 6: Cursor docs + optional live smoke

Files:
- `agents/hooks/lessons-recall/cursor.sh` *(comments only)*
- `agents/hooks/lessons-recall/README.md` *(modify)*
- `docs/AGENTS.md` *(modify)*

- [x] `cursor.sh`: update header comments only (bridge dependency, v1 behavior without bridge)
- [x] INSTALL: `cursor-session-bridge.sh` symlink + ordered `sessionStart` example
- [x] Live (Cursor, optional): two tabs -> different marker `session` component when bridge installed
- [x] AGENTS.md: one-line probe pointer; note other agents unchanged
- [x] Commit: `docs(hooks): Cursor bridge install + agent parity notes`

### Task 7: Four-agent regression + frozen diff gate

Files:
- (verification only)

- [x] Run full Validation Commands block; all GREEN
- [x] Echo-pipe matrix: Claude, Codex, agy, Cursor (all arms in Validation Commands)
- [x] `git diff --name-only "$(git merge-base HEAD main 2>/dev/null || git merge-base HEAD master)"...HEAD`: assert NO changes to frozen adapter paths (`claude.sh`, `codex.sh`, `agy.sh`, `skill-gate/claude.sh`, `skill-gate/codex.sh`, `skill-gate/agy.sh`, `skill-gate/cursor.sh`)
- [x] `hooks_probe --all` snapshot in commit message or `docs/tmp/` note (machine-specific)
- [x] `check-no-em-dash.sh` clean
- [x] Commit: `test(hooks): four-agent regression + frozen adapter gate`
