# lessons-recall adapters

Per-agent adapters around the agent-agnostic `lessons_recall.py` core. Each
adapter reads the agent's hook payload on stdin, extracts the prompt with
python3, pipes it to the core, derives the session id via the shared
`session_channel.py` subprocess, and builds the agent's specific envelope via
`json.dumps` dict construction.

## Boundary vs pr-skill-reminder.sh

These are INDEPENDENT hooks:
- `pr-skill-reminder.sh` injects the PR-skill reminder (a workflow nudge).
- `lessons-recall` injects family-tagged lessons from the development-lessons
  corpus (proactive recall keyed on prompt INTENT).

Neither subsumes the other.

## jq-free / python-parse convention

All four adapters parse the stdin JSON payload with **python3, not jq** (see the
plan Design Invariant). Rationale: agy hosts may not have jq, and python3 is
already required by the core, so python3 is the single robust extraction path
across all four agents.

## json.dumps-envelope invariant

Each adapter builds its envelope ONLY via `json.dumps(<dict>)` construction,
never via f-string or string concatenation. This prevents corpus text containing
`"`, `}`, or newlines from breaking the envelope or injecting sibling keys. The
core emits a single `json.dumps(text)` string value; the adapter wraps it.

Each agent's envelope shape is DISTINCT:
- **Claude** wraps context as
  `{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext": ...}}`.
- **Codex** emits a flat `{"additionalContext": ...}`.
- **agy** emits a TOP-LEVEL `{"additionalContext": ...}` with NO
  `hookSpecificOutput` wrapper (the nested shape fails agy schema validation).
- **Cursor** emits a flat `{"additionalContext": <family-index>}` (best-effort
  one-shot; see below).

## Session channel derivation (subprocess, not import)

The session id is derived VERBATIM via the shared helper subprocess:

```bash
SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"
```

This idiom is PINNED here so the plans-skill marker recipe and every adapter
use the SAME artifact (Family D single source). The helper prints
``CLAUDE_CODE_SESSION_ID or CURSOR_SESSION_ID or ""`` with NO
trailing newline (Claude at v9; Cursor optional at v2 via the session bridge).
When `SID` is empty the adapter OMITS `--session-id`, so the core keys the
literal `no-session` and uses the FULL window. Per-session isolation is
Claude-only at v9 and Cursor-without-bridge at v9; optional Cursor bridge
install (v2) supplies `CURSOR_SESSION_ID` per composer tab.

The cores NEVER import `session_channel.py`; they accept `--session-id` as
opaque data, so the agent-agnostic-core invariant holds.

### Session channel precedence (read this before multi-agent use)

`session_channel.py` evaluates **one subprocess environment** per hook invocation:

```text
CLAUDE_CODE_SESSION_ID  →  if set and non-empty, use it
else CURSOR_SESSION_ID  →  if set and non-empty, use it
else ""                 →  adapter omits --session-id (no-session key)
```

**Claude wins when both vars are set in the same process.** Cursor does not override
Claude. The precedence rule exists for the rare case where both env vars leak into
one hook subprocess (for example `CLAUDE_CODE_SESSION_ID` exported in your shell
while Cursor hooks also set `CURSOR_SESSION_ID`). In that edge case, hooks use the
Claude session id, not Cursor's.

**Normal case (Claude + Cursor on the same repo):** each agent runs hooks in its
own subprocess tree with its own env. Claude Code sets `CLAUDE_CODE_SESSION_ID`
only in Claude hooks. Cursor sets `CURSOR_SESSION_ID` only in Cursor hooks (when
the session bridge is registered). They do not share one hook process, so precedence
almost never applies. Claude hooks work fully in Claude; Cursor hooks work fully in
Cursor. Markers and dedup state are keyed by `(project_hash, session_component)`;
different session ids produce different filenames, so Claude and Cursor sessions on
the same repo do not clobber each other's markers.

**What v2 changed:** only Cursor gained an optional way to populate
`CURSOR_SESSION_ID` (the session bridge). Claude, Codex, and agy env and adapter
logic are unchanged.

## Agent differences (v2 at a glance)

Shared cores (`lessons_recall.py`, `skill_gate.py`, `session_channel.py`) serve
all agents. Per-agent **adapters** and **host config** differ. v2 production
changes are **Cursor-only** (optional session bridge + docs); frozen adapter
scripts for Claude, Codex, and agy were not rewritten.

| Agent | Recall hook event | Recall tier | Session env (steady state) | Session bridge | Skill-gate |
|-------|-------------------|-------------|----------------------------|----------------|------------|
| Claude | `UserPromptSubmit` (every prompt) | FULL | `CLAUDE_CODE_SESSION_ID` (product) | N/A | `PreToolUse` block, live |
| Codex | `SessionStart` one-shot | DEGRADED | none (`no-session`) | N/A | adapter exists; config often unwired |
| agy | `PreInvocation` | DEGRADED | none (`no-session`) | N/A | `PreToolUse` block, live |
| Cursor | `sessionStart` one-shot | DEGRADED | none without bridge; `CURSOR_SESSION_ID` with bridge | **optional** `cursor-session-bridge.sh` | `PreToolUse` block, live |

**Classifier:** core default remains `--classifier v1` for all agents. v2 phrase+verb
classifier is opt-in CLI only until a follow-on plan wires adapters.

**Frozen adapters (v2):** `claude.sh`, `codex.sh`, `agy.sh`, and all three
non-Cursor `skill-gate` adapters. Do not edit their stdin parsing, envelopes, or
exit codes without a regression-driven unfreeze.

## Same repository, multiple agents

Using Claude Code, Cursor, Codex CLI, and agy on **one git repo** is supported.

- **Hooks are per agent, not per repo.** Installing Cursor hooks does not change
  Claude's `~/.claude/settings.json`. Installing Claude hooks does not change
  Cursor's `~/.cursor/hooks.json`.
- **Runtime state is partitioned by session id.** Example marker:
  `plans.<project>.<session_hash>.marker`. Claude's session hash comes from
  `CLAUDE_CODE_SESSION_ID`. Cursor's comes from `CURSOR_SESSION_ID` when the
  bridge is installed. Same repo, different agents → different session components
  → no cross-agent marker admission unless you reuse the same session id on purpose.
- **Shared symlinked cores** under `~/.ai-playbook/scripts/` are updated once and
  used by every agent's adapters. Backward compat: when `CURSOR_SESSION_ID` is unset,
  `session_channel.py` output matches v1 (Claude var or empty).

Per-prompt recall quality remains agent-specific (Claude FULL; others degraded as in
the table above). That is a product wiring limitation, not a v2 regression.

## Install (step-by-step)

Host-level install: symlinks under `~/` agent dirs plus JSON registration in each
agent's config. Rollback: remove symlinks and config entries.

**0. Resolve repo path** from `user_facts_path` (`instructions_repo`).

**1. Symlink shared scripts** (all agents that use hooks):

```bash
INSTRUCTIONS_REPO=~/path/to/ai-playbook   # edit
mkdir -p ~/.ai-playbook/scripts ~/.ai-playbook/runtime ~/.ai-playbook/logs
ln -sf "$INSTRUCTIONS_REPO/scripts/session_channel.py"  ~/.ai-playbook/scripts/session_channel.py
ln -sf "$INSTRUCTIONS_REPO/scripts/lessons_recall.py"   ~/.ai-playbook/scripts/lessons_recall.py
ln -sf "$INSTRUCTIONS_REPO/scripts/skill_gate.py"       ~/.ai-playbook/scripts/skill_gate.py
ln -sf "$INSTRUCTIONS_REPO/scripts/facts_paths.py"      ~/.ai-playbook/scripts/facts_paths.py
ln -sf "$INSTRUCTIONS_REPO/scripts/lessons_classify.py" ~/.ai-playbook/scripts/lessons_classify.py
ln -sf "$INSTRUCTIONS_REPO/scripts/hooks_probe.py"       ~/.ai-playbook/scripts/hooks_probe.py
ln -sf "$INSTRUCTIONS_REPO/scripts/hooks_log_summary.py" ~/.ai-playbook/scripts/hooks_log_summary.py
```

**2. Per-agent adapter symlinks** (install only the agents you use):

| Agent | Recall adapter symlink | Skill-gate adapter (see skill-gate README) |
|-------|------------------------|--------------------------------------------|
| Claude | `.../lessons-recall/claude.sh` → `~/.claude/hooks/lessons-recall.sh` | `.../skill-gate/claude.sh` → `~/.claude/hooks/skill-gate.sh` |
| Codex | `.../codex.sh` → `~/.codex/hooks/lessons-recall.sh` | `.../skill-gate/codex.sh` → `~/.codex/hooks/skill-gate.sh` |
| Cursor | `.../cursor.sh` → `~/.cursor/hooks/lessons-recall.sh` | `.../skill-gate/cursor.sh` → `~/.cursor/hooks/skill-gate.sh` |
| agy | `.../agy.sh` → `~/.gemini/antigravity-cli/hooks/lessons-recall.sh` | `.../skill-gate/agy.sh` → `~/.gemini/antigravity-cli/hooks/skill-gate.sh` |

**3. Register hooks in agent config** (required for hooks to fire):

- Claude: `UserPromptSubmit` → lessons-recall; `PreToolUse` → skill-gate (see recipes below).
- Codex: `SessionStart` → lessons-recall (degraded); skill-gate when wired.
- Cursor: `sessionStart` → lessons-recall; `preToolUse` → skill-gate (see Cursor section).
- agy: `PreInvocation` → lessons-recall (see agy section).

**4. Cursor session bridge (optional, Cursor only):**

The bridge is **not** required for hooks to run. Without it, Cursor behaves as v1
(`no-session`, all composer tabs on a repo share dedup/marker session key).

To install per-tab session isolation:

```bash
ln -sf "$INSTRUCTIONS_REPO/agents/hooks/lessons-recall/cursor-session-bridge.sh" \
  ~/.cursor/hooks/cursor-session-bridge.sh
```

Register it **first** in `~/.cursor/hooks.json` `sessionStart` (before
`lessons-recall.sh`). On each new composer tab, Cursor calls the bridge with
`{"session_id":"..."}`; the bridge returns `{"env":{"CURSOR_SESSION_ID":"..."}}`;
later hooks in that tab inherit the var. See **Cursor (sessionStart one-shot)** below.

**5. Verify:**

```bash
python3 ~/.ai-playbook/scripts/hooks_probe.py --all
```

See **Capability probe** for expected PASS / DEGRADED / FAIL per agent.

**6. After repo updates:** symlinks point at `$INSTRUCTIONS_REPO`; `git pull` in
the clone updates behavior on next hook run. Re-open Cursor composer tabs after
bridge or env renames so new sessions pick up current env keys.

## Window and budget

- `RECALL_DEDUP_WINDOW` default 86400s (24h). ALL agents use the FULL window
  unconditionally; omitting `--session-id` does NOT halve the window.
- `--budget` default 1500 chars (HEAD-truncated, measured on the injected body
  before `json.dumps` wrapping). FLAGGED threshold; user-tunable.

## Observability

`~/.ai-playbook/logs/hooks.log` records one JSON line per consultation.

### Recall JSONL (v2, every consultation)

On every `_consult` call the core appends one recall observability line:

```json
{"ts":"<iso8601-utc>","event":"recall","outcome":"fire","family":"G"}
```

| Field | Required | Values |
|-------|----------|--------|
| `ts` | yes | ISO8601 UTC timestamp |
| `event` | yes | always `"recall"` |
| `outcome` | yes | `fire` (injected), `suppress-dedup` (matched, all deduped), `suppress-empty-corpus` (matched, no corpus content), `suppress-classify` (no family match) |
| `family` | optional | Present on match arms (`fire`, `suppress-dedup`, `suppress-empty-corpus`); absent on `suppress-classify` |

Summarize fire vs suppress ratio over the last N days:

```bash
python3 scripts/hooks_log_summary.py --days 7
# or after symlink install:
python3 ~/.ai-playbook/scripts/hooks_log_summary.py --days 7
```

### Legacy keying lines (coexist in the same file)

Legacy LOUD keying metadata is separate JSONL lines (no `event` field):

- The CORE emits `keying=env-var` (Claude steady state: a session id was
  supplied; Cursor with optional session bridge installed) or
  `keying=project-only` (Codex steady state; Cursor/agy without bridge at v9:
  no session id). `keying` is PURE LOG METADATA and drives NO core branch.
- The RESOLVER `facts_paths.resolve_project_key` emits `keying=no-anchor` to the
  SAME file on its git-failure branch (a non-git dir; in a non-git tree the
  `project` component is cwd-derived and unstable across `cd`).
- `keying=error` = an unexpected exception escaped `_consult` to `main`'s
  generic `except Exception` backstop; recall stayed silent and returned no
  reminder (the never-blocking Family-G arm). The recall core has NO
  `keying=fail-open` analogue (it has no `OSError`-specific arm; any exception
  including `OSError` falls through to the generic arm -> `keying=error`).
- The Claude adapter additionally warns on stderr `CLAUDE_CODE_SESSION_ID
  absent; running in no-session mode` when SID is empty-after-strip (only the
  Claude adapter does this; for the others empty is documented steady state).

`hooks_log_summary.py` counts both recall outcomes and `keying=*` lines
(including `no-anchor`) in the same pass.

The runtime paths (`~/.ai-playbook/runtime/lessons-recall/`,
`~/.ai-playbook/logs/hooks.log`) are disposable; safe to delete.

## Capability probe (steady state)

Run `python3 scripts/hooks_probe.py --all` from the instructions repo (or
`python3 ~/.ai-playbook/scripts/hooks_probe.py --all` after the core symlink
exists). Exit 0 when no cell is FAIL; DEGRADED is honest steady state for
several agents. Weekly cron (Mondays 09:00 local):

```cron
0 9 * * 1 python3 "$HOME/.ai-playbook/scripts/hooks_probe.py" --all >> "$HOME/.ai-playbook/logs/hooks-probe.log" 2>&1
```

| Agent | Probe tier | Wiring | Notes |
|-------|------------|--------|-------|
| Claude | FULL | `UserPromptSubmit` + adapter symlink | Per-prompt recall; `CLAUDE_CODE_SESSION_ID` session channel |
| Codex | DEGRADED | `SessionStart` one-shot + adapter symlink | No per-prompt hook in this install; adapter ready for future `user_prompt_submit` |
| agy | DEGRADED | `PreInvocation` + adapter symlink | Best-effort injection; not Claude-grade per-prompt |
| Cursor | DEGRADED | `sessionStart` one-shot + adapter symlink | Optional `cursor-session-bridge.sh` adds per-tab session env (v2); per-prompt recall blocked on product schema |

Classifier: `lessons_recall.py` core default remains `--classifier v1`; v2 is
opt-in CLI only until a follow-on plan wires adapters.

## Dedup behavior

Append-only, home-anchored, PATH-ISOLATED per (project, session) state file at
`~/.ai-playbook/runtime/lessons-recall/<project>.<session>.state`. The
membership key is the lesson number `N`; the file grows within a session and is
safe to delete per-session. The `<project>` component is derived via the shared
`facts_paths.resolve_project_key` (the one function both cores import; not
re-implemented here).

## Cursor limitation

Cursor cannot silently inject context on every prompt the way Claude
UserPromptSubmit does; it fires a `sessionStart` hook ONCE per session. So
`cursor.sh` is a best-effort one-shot that emits a COMPACT FAMILY INDEX built
directly from the corpus (lowest-numbered lesson per present family) at session
start, rather than per-prompt recall. The selection happens inline in the
adapter (no shared helper). The existing
`grep -nE '^\*\*Principle:\*\* Family' <corpus>` recall command (documented in
user AGENTS.md) still covers on-demand recall.

## Build-time verifications (outcomes)

### Codex prompt-event

Probed `~/.codex/config.toml` and `~/.codex/hooks.json`. Codex does NOT expose a
prompt-equivalent hook event in this install:
- `~/.codex/hooks.json` carries a `SessionStart` array only (one-shot).
- `~/.codex/config.toml` `[hooks]` carries `post_tool_use = "~/.agents/scripts/learn-counter-codex.sh"`.

Neither delivers the user prompt per turn, and neither exposes `user_prompt_submit`
or `pre_tool_use`. `codex --help` shows no hook subcommand.

OUTCOME: `codex.sh` is documented as a DEGRADED one-shot. The CLI is identical
to the Claude adapter's prompt-extraction path, so a future Codex
`user_prompt_submit` event can be wired by changing only the Codex config entry
(no adapter rewrite). Preferred event when available: `user_prompt_submit`; the
degraded fallback is `SessionStart` (no per-turn prompt).

### agy PreInvocation field

DEFERRED to first real agy session (fix-on-first-use). The cited article
describes the PreInvocation event but does not show the context-injection field
in a concrete example. The adapter ships LIVE wired assuming the field is
`additionalContext`; on the first real agy session confirm the injected text
surfaces in the agent's next turn and correct the field name if it does not.

## Per-agent wiring recipes

### Claude (UserPromptSubmit)

Register in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "*",
        "hooks": [{"type": "command", "command": "~/.claude/hooks/lessons-recall.sh", "timeout": 10}]
      }
    ]
  }
}
```

Pin a per-hook `timeout` (seconds) so a stuck core degrades to a missed recall
(recall is non-blocking in intent, but a hang wedges the prompt until the harness
intervenes; r2-M4). The canonical home for the timeout table, field name, and
threshold rationale is the skill-gate README's "Host hook timeout" section
(`>= 2 * RESOLVER_GIT_TIMEOUT_S` = 10 seconds, field `timeout` lowercase
seconds); see that section rather than duplicating it here.

### Codex (degraded SessionStart one-shot)

Codex has no per-prompt hook in this install. To wire the degraded one-shot, add
to `~/.codex/hooks.json` under `hooks.SessionStart` (alongside any existing
entry):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {"type": "command", "command": "bash ~/.codex/hooks/lessons-recall.sh", "timeout": 10}
        ]
      }
    ]
  }
}
```

(Outcome: the adapter extracts `.prompt` from a SessionStart payload if present;
in practice SessionStart does not carry the prompt, so this is best-effort. When
Codex ships `user_prompt_submit`, re-point this entry at it.)

### Cursor (sessionStart one-shot)

**Optional session bridge (v2):** Cursor does not expose a per-session env var
natively. Without the bridge, `session_channel.py` returns empty and adapters
key `no-session` (v1 steady state). To isolate markers and dedup state per
composer tab, register `cursor-session-bridge.sh` **FIRST** in the
`sessionStart` array so it exports `CURSOR_SESSION_ID` before
other hooks run in the same tab:

```json
{
  "hooks": {
    "sessionStart": [
      {"type": "command", "command": "bash ~/.cursor/hooks/cursor-session-bridge.sh", "timeout": 10},
      {"type": "command", "command": "bash ~/.cursor/hooks/lessons-recall.sh", "timeout": 10}
    ]
  }
}
```

The bridge reads `sessionStart` JSON on stdin, extracts `.session_id`, and
emits `{"env":{"CURSOR_SESSION_ID":"<id>"}}` via `json.dumps`.
Missing `session_id` emits `{}`. Exit 0 always. Later hooks in the same
composer session inherit the env var; `session_channel.py` reads
`CURSOR_SESSION_ID` only when `CLAUDE_CODE_SESSION_ID` is unset (Claude wins if
both are present in the same subprocess; see **Session channel precedence**).

Without the bridge installed, Cursor behavior is unchanged from v1 (`no-session`).

#### Live verification (optional)

With the bridge installed, open two Cursor composer tabs on the same repo and
trigger skill-gate marker writes; each tab should get a different `session`
component in marker filenames. If live two-tab smoke is not feasible, the
required backstop is:

```bash
python3 scripts/skill_gate.py --selftest#distinct_cursor_session_components
```

### Agent parity (v2)

v2 hook changes are **Cursor-only** (optional session bridge + docs). Claude
(`UserPromptSubmit`), Codex (`SessionStart` one-shot), and agy (`PreInvocation`)
adapters and steady-state recall/gate behavior are unchanged.

### agy (PreInvocation)

Register in `~/.gemini/antigravity-cli/hooks.json`. The `command` MUST be an
ABSOLUTE path (relative paths resolve against the launch cwd and fail with exit
127, silently bypassing the guardrail):

```json
{
  "PreInvocation": [
    {"type": "command", "command": "/home/you/.gemini/antigravity-cli/hooks/lessons-recall.sh", "timeout": 10}
  ]
}
```

(The `command` MUST be the absolute path to the symlink under your home
directory; JSON does not expand `~` or `$HOME`. Replace `/home/you` with your
real home directory, for example via `echo ~/.gemini/antigravity-cli/hooks/lessons-recall.sh`.)

## Install (symlink block)

Copy-paste symlink block for hosts that already followed **Install (step-by-step)**.
Prefer the step-by-step section above for first-time setup (includes skill-gate
symlinks, config registration, and bridge ordering).

This is a HOST-LEVEL change: it creates symlinks under the `~/` agent config
dirs. These are NEW filenames (`lessons-recall.sh`, `session_channel.py`,
`lessons_recall.py`), so `ln -sf` will not clobber existing hooks. Execution
context: host. Impact: new symlinks in `~/` agent dirs. Rollback: `rm` the
symlink paths.

```bash
# Resolve clone path from user facts (key: instructions_repo); edit before running.
INSTRUCTIONS_REPO=~/path/to/ai-playbook
# r12-M2: create target parent dirs that do not always exist on a default install.
# r13-M3: ~/.ai-playbook/scripts/ is the symlink TARGET dir for the cores + helper.
mkdir -p ~/.ai-playbook/scripts ~/.codex/hooks ~/.gemini/antigravity-cli/hooks ~/.claude/hooks ~/.cursor/hooks
# Helper + core + 2 leaves symlinked to ~/.ai-playbook/scripts/. The cores reach
# the leaves at runtime via Path(__file__).resolve().parent (following their own
# symlink to the repo dir), but the leaves ALSO need their own symlinks for
# DIRECT invocation (the plan's Validation Commands block invokes every script
# in ~/.ai-playbook/scripts/) and for single-source-model consistency.
ln -sf "$INSTRUCTIONS_REPO/scripts/session_channel.py"  ~/.ai-playbook/scripts/session_channel.py
ln -sf "$INSTRUCTIONS_REPO/scripts/lessons_recall.py"   ~/.ai-playbook/scripts/lessons_recall.py
ln -sf "$INSTRUCTIONS_REPO/scripts/facts_paths.py"      ~/.ai-playbook/scripts/facts_paths.py
ln -sf "$INSTRUCTIONS_REPO/scripts/lessons_classify.py" ~/.ai-playbook/scripts/lessons_classify.py
ln -sf "$INSTRUCTIONS_REPO/scripts/hooks_probe.py"       ~/.ai-playbook/scripts/hooks_probe.py
ln -sf "$INSTRUCTIONS_REPO/scripts/hooks_log_summary.py" ~/.ai-playbook/scripts/hooks_log_summary.py
# Four lessons-recall adapter symlinks (absolute targets)
ln -sf "$INSTRUCTIONS_REPO/agents/hooks/lessons-recall/claude.sh" ~/.claude/hooks/lessons-recall.sh
ln -sf "$INSTRUCTIONS_REPO/agents/hooks/lessons-recall/codex.sh"  ~/.codex/hooks/lessons-recall.sh
ln -sf "$INSTRUCTIONS_REPO/agents/hooks/lessons-recall/cursor.sh" ~/.cursor/hooks/lessons-recall.sh
ln -sf "$INSTRUCTIONS_REPO/agents/hooks/lessons-recall/cursor-session-bridge.sh" ~/.cursor/hooks/cursor-session-bridge.sh
ln -sf "$INSTRUCTIONS_REPO/agents/hooks/lessons-recall/agy.sh"    ~/.gemini/antigravity-cli/hooks/lessons-recall.sh
```

After symlinks, register Cursor hooks in `~/.cursor/hooks.json` with the
bridge **first** in `sessionStart` (see the ordered example under **Cursor
(sessionStart one-shot)** above).

The cores + helper are SYMLINKED to `~/.ai-playbook/scripts/` (the new
single-source model; a deviation from the four existing copy-synced lessons
scripts `lessons_index.py`/`lessons_adopt.py`/`lessons_migrate.py`/
`lessons_corpus.py`, whose cleanup is out of scope).
