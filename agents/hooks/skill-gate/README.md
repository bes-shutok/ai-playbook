# skill-gate adapters

Per-agent PreToolUse adapters around the agent-agnostic `skill_gate.py` core.
Each adapter reads the agent's hook payload on stdin, extracts the target write
path with python3 (NOT jq), pipes it to the core, derives the session id via the
shared `session_channel.py` subprocess, and builds the agent's specific decision
envelope via `json.dumps` dict construction.

The core is agent-agnostic: it ALWAYS exits 0 and emits one JSON line on stdout:

```json
{"allow_tool": true}
{"allow_tool": false, "deny_reason": "Invoke the plans skill before authoring a plan file."}
{"allow_tool": false, "deny_reason": "Invoke the learn skill before editing the project lessons corpus."}
```

Each adapter translates that decision into its agent's contract (Claude:
stderr + exit 2 on block; agy/Cursor/Codex: top-level JSON, exit 0 always).

## What the gate does

The skill-gate gates writes to gated artifact classes (v2: `docs/plans/` and the
project lessons corpus `docs/maintenance/development_lessons.md`). Before a
gated Write/Edit/MultiEdit is allowed, the gate requires a fresh per-(project,
session) marker at
`~/.ai-playbook/runtime/skill-invoked/<class>.<project>.<session>.marker`
(written/refreshed by the owning skill on EVERY gated-file write; see the
marker WRITE RECIPE sections below). An ABSENT marker ALWAYS blocks; the gate
consults NO second signal. Recovery from a transient/unwritable/divergently-resolved store
is via `skill_gate --doctor` (Mon1), NOT a gate-side bypass.

The marker is a **consent reminder, NOT a security boundary** (THREAT-MODEL
note, r6-L2): it is forgeable by any process with write access to the runtime
dir. This is accepted because the protected files (plan files) are already
fully writable by the same user; the gate exists to make the "did the plans
skill run?" question loud, not to defend against a hostile agent.

## jq-free / python-parse convention

All four adapters parse the stdin JSON payload with **python3, not jq** (see the
plan Design Invariant). Rationale: agy hosts may not have jq (the cited article
requires a grep/cut fallback), and python3 is already required by the core, so
python3 is the single robust extraction path across all four agents.

## json.dumps-envelope invariant

Each adapter builds its envelope ONLY via `json.dumps(<dict>)` construction,
never via f-string or string concatenation. The block message
`deny_reason` is data-influenced (it transits the adapter), so it is always
re-emitted via `json.dumps`, never written raw to stderr. This prevents the
reason string (or a future data-influenced field) from breaking the envelope or
injecting sibling keys (M3; Family H, Family C, Family G).

Each agent's envelope shape is DISTINCT:
- **Claude** translates block into stderr-reason + `exit 2`; allow is `exit 0`
  (matches the only wired precedent, `check-plan-review-gate.sh`).
- **agy** emits a TOP-LEVEL `{"allow_tool": true}` / `{"allow_tool": false,
  "deny_reason": ...}` and exits 0 ALWAYS (a non-zero exit is a hook FAILURE on
  agy, not a block). NO `hookSpecificOutput` wrapper (the nested shape fails
  agy schema validation).
- **Codex** emits a flat top-level `{"allow_tool": ...}` (no
  hookSpecificOutput wrapper).
- **Cursor** emits a flat top-level `{"allow_tool": ...}` (same shape as Codex;
  full-fidelity blocking, unlike the lessons-recall one-shot).

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
install (v2) supplies `CURSOR_SESSION_ID` per composer tab. The
cores NEVER import `session_channel.py`; they accept `--session-id` as opaque
data.

**Precedence and multi-agent use:** see `agents/hooks/lessons-recall/README.md`
(**Session channel precedence**, **Same repository, multiple agents**). Summary:
Claude wins if both `CLAUDE_CODE_SESSION_ID` and `CURSOR_SESSION_ID` are set in
the same hook subprocess; normally each agent only sets its own var, so Claude
and Cursor hooks on the same repo do not interfere.

Only the Claude adapter warns on empty SID (`CLAUDE_CODE_SESSION_ID absent;
running in no-session mode`, BEFORE invoking the core); for Codex/Cursor/agy
empty is documented steady state (r12-M4 relocated alarm).

## Marker WRITE RECIPE (plans class)

This README is the SINGLE SOURCE for the byte-identical marker WRITE RECIPE
(M7/r7-L2). The `plans` SKILL.md step REFERENCES it (does not restate the
constants - r3-M7). The plans skill writes/REFRESHES the marker on EVERY
plan-file write it performs (create AND update, NOT only Phase 0 - M2) BEFORE
the gated tool call, and the marker write is FAIL-LOUD in the skill (abort with
a clear error if unwritable - M2).

Local elements of the recipe (per Terms "Skill-gate marker"; the constants live
there and in `skill_gate.py`):

1. `os.makedirs(~/.ai-playbook/runtime/skill-invoked/, exist_ok=True, mode=0o700)`
   (r8-M4; the gate ALSO does this benign makedirs before its `os.stat`, so a
   missing dir on a fresh install cannot fail-OPEN via `FileNotFoundError`).
2. ATOMICALLY write via `lessons_corpus.atomic_write_text` at mode `0o600`
   (`O_EXCL|O_NOFOLLOW` + `os.replace`, r8-L3; torn-read-safe under concurrent
   skill-refresh).
3. `--write-marker` CATCHES `FileExistsError` at the call site and treats it as
   BENIGN (r10-L1: a concurrent skill-refresh racing on the same marker; the
   loser's abort is harmless - no retry, no `os.replace`, no deletion of a
   pre-existing `.tmp`).
4. Marker filename: `plans.<project>.<session>.marker`, where `project` derives
   via the shared `facts_paths.resolve_project_key` (the ONE function both cores
   import; do NOT re-implement) and `session` derives per Terms "Session key"
   (emptiness check FIRST; empty-after-strip -> literal `no-session`; otherwise
   `sha1(value)[:16]` hex).
5. CLI: `python3 ~/.ai-playbook/scripts/skill_gate.py --write-marker [--session-id "$SID"]`
   (bare `--write-marker` defaults to the plans class).
6. Acceptance: the marker EXISTS AND `0 <= (now - mtime) <= SKILL_GATE_WINDOW`
   (default 4h, FLAGGED; future-dated/negative delta or `mtime == 0` is STALE ->
   block, M4). ALL agents use the FULL window (r10-M10).

The marker BODY stores the writer's `realpath(cwd)` and the resolved repo-anchor
path as FORENSIC/debug metadata ONLY (it is NOT a checked guard - r7-M4).

The `plans` skill invokes `--write-marker` with the SAME `--session-id "$SID"`
the Claude adapter supplies (so a marker written in session A does NOT admit
session B's writes in the same repo - r6/r9/r10).

## Marker WRITE RECIPE (learn class)

The `learn` skill REFERENCES this section (does not restate constants). It
writes/refreshes the learn marker on EVERY Write/Edit to the project lessons
corpus (`docs/maintenance/development_lessons.md`, the path constant
`PROJECT_CORPUS_REL` in `lessons_recall.py`) BEFORE the gated tool call. The
marker write is FAIL-LOUD in the skill (abort with a clear error if unwritable).

Steps 1-3, 5, and 6 are IDENTICAL to the plans recipe above (same runtime dir,
same atomic write, same `FileExistsError` benign catch, same window). Only step
4 (marker filename) and the CLI class differ:

4. Marker filename: `learn.<project>.<session>.marker` (same `project`/`session`
   derivation as plans).
5. CLI: `python3 ~/.ai-playbook/scripts/skill_gate.py --write-marker learn [--session-id "$SID"]`.
6. Acceptance: the marker EXISTS AND `0 <= (now - mtime) <= SKILL_GATE_WINDOW`
   (same rule as plans step 6).

The learn skill invokes `--write-marker learn` with the SAME `--session-id "$SID"`
idiom as plans (Family D single source via `session_channel.py` subprocess).

## Adding a third gated class

v2 has TWO gated classes (`plans`, `learn`). To add a third (e.g. `rfcs`), extend
the module-level `GATED_CLASS_REGISTRY` in `skill_gate.py` IN THAT CHANGE (L3).
The core, the owning skill, and the doctor checks must move together; do not leave
a new class half-wired.

## Build-time verifications (outcomes)

### Codex blocking-event probe (r12-M5 / r13-M8)

Probed `~/.codex/config.toml` and `~/.codex/hooks.json` with the literal
`grep -nE 'pre_tool_use|PreToolUse' ~/.codex/config.toml ~/.codex/hooks.json`.
OUTCOME: EMPTY in BOTH files.
- `~/.codex/config.toml` `[hooks]` carries only `post_tool_use`
  (`"~/.agents/scripts/learn-counter-codex.sh"`), which CANNOT block.
- `~/.codex/hooks.json` carries a `SessionStart` array only (one-shot).

Codex has NO BLOCKING `pre_tool_use` event in this install. Per the Task 5 GATE,
`codex.sh` is NOT wired into any Codex config file (no config entry references
it). The symlink at `~/.codex/hooks/skill-gate.sh` IS created (so the doctor's
11-path check resolves and a future blocking event can be wired by adding ONLY
the config entry), but it is a NO-OP until Codex ships a blocking
`pre_tool_use`. The adapter is authored in full so no rewrite is needed when
that event lands.

INSTALL GATE preserved: the existing `post_tool_use` line in `~/.codex/config.toml`
is UNTOUCHED (Family G; do not regress an existing wired hook).

### agy file-tool path field

DEFERRED to first real agy session (fix-on-first-use, r6). The cited article
describes the PreToolUse event but is not concrete for file tools. The adapter
ships LIVE wired assuming the path field inside `.toolCall.args` is `path`; on
the first real agy session confirm a `write_to_file` of a plan file is gated -
if it is not, correct the field name and re-test. Also verify the
`~/.gemini/antigravity-cli/hooks.json` `timeout` field path and the matcher
tool names at that session.

### Host hook timeout (all agents; r2-M3/M4)

`RESOLVER_GIT_TIMEOUT_S = 5` (`facts_paths.py`). The resolver bounds its internal
`git rev-parse` to that value, but the rest of `_consult` (`os.lstat`, makedirs,
corpus read, atomic write) is unbounded inside the core. A stuck I/O op on, for
example, an NFS-mounted `~/.ai-playbook/runtime/` would wedge the hook until the
agent harness kills it. EVERY adapter's host-config entry MUST therefore carry a
host-level hook timeout, so a hung core degrades to a missed consult (the
fail-open aperture already covers an exit/crash) rather than wedging the user's
session:

| Agent | host field | required bound | recipe |
|-------|-----------|----------------|--------|
| agy | `timeout` (in `~/.gemini/antigravity-cli/hooks.json`) | `>= 2 * RESOLVER_GIT_TIMEOUT_S` (= 10) | MUST exceed the resolver's git timeout so a hung git makes agy kill the hook AFTER the resolver's `TimeoutExpired` catch fires (else agy treats hook-kill as failure, not block, silently disabling the gate - r15-M4) |
| Claude | `timeout` (in `~/.claude/settings.json`, seconds) | `>= 2 * RESOLVER_GIT_TIMEOUT_S` (= 10) | Claude's default hook timeout is much larger than 10s; pin it tight so a stuck core does not block Write/Edit for ~60s+. Per-hook field is `timeout` (lowercase, seconds); the camelCase `T`-capitalized variant is NOT a recognized field and is silently ignored (verified against the plugin-dev `validate-hook-schema.sh` schema validator, which reads `.hooks[].timeout` as an integer in seconds with thresholds 5..600). |
| Cursor | `timeout` (in `~/.cursor/hooks.json`) | `>= 2 * RESOLVER_GIT_TIMEOUT_S` (= 10) | same tight bound |
| Codex | (set when the blocking `pre_tool_use` ships) | `>= 2 * RESOLVER_GIT_TIMEOUT_S` (= 10) | same tight bound |

The agy host `~/.gemini/antigravity-cli/hooks.json` ships `timeout: 10`; the
`#doctor_agy_timeout` selftest pins it. Claude/Cursor/Codex do NOT currently
have a wired doctor check for the host timeout field, so the value is
HAND-SYNCED at install time against this recipe.

## Per-agent wiring recipes

### Claude (PreToolUse, exit-2 + stderr contract)

Register in `~/.claude/settings.json` under `hooks.PreToolUse` (alongside the
existing `Bash` entry for `check-plan-review-gate.sh`, which MUST be preserved):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "~/.claude/hooks/check-plan-review-gate.sh"}]
      },
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [{"type": "command", "command": "~/.claude/hooks/skill-gate.sh"}]
      }
    ]
  }
}
```

The skill-gate entry's matcher MUST be `Write|Edit|MultiEdit` (r8-M6). The doctor
asserts BOTH the `Bash` entry AND the `Write|Edit|MultiEdit` entry survive. Pin a
per-hook `timeout` (seconds) so a stuck core degrades to a miss instead of
wedging Write/Edit for the Claude default (~60s+); see "Host hook timeout" above
(r2-M3):

```json
{
  "matcher": "Write|Edit|MultiEdit",
  "hooks": [{"type": "command", "command": "~/.claude/hooks/skill-gate.sh", "timeout": 10}]
}
```

### Codex (no-op until blocking pre_tool_use ships)

NOT WIRED. Codex has no blocking `pre_tool_use` event in this install (see the
build-time probe above). When Codex ships one, add to whichever config file the
event consults (verified at that time), WITHOUT removing the existing
`post_tool_use` line. The adapter CLI extracts `.tool_input.file_path`.

### Cursor (preToolUse, full-fidelity blocking)

Register in `~/.cursor/hooks.json` under `hooks.preToolUse` with matcher
`Write|EditNotebook` (the Cursor file tools; full-fidelity blocking, unlike the
lessons-recall one-shot):

```json
{
  "hooks": {
    "preToolUse": [
      {"matcher": "Write|EditNotebook", "hooks": [{"type": "command", "command": "bash ~/.cursor/hooks/skill-gate.sh", "timeout": 10}]}
    ]
  }
}
```

The adapter tolerates `.tool_input.filePath` (camelCase) and `.tool_input.file_path`.
Pin a per-hook `timeout` so a stuck core degrades to a miss (see "Host hook
timeout" above; r2-M3).

### agy (PreToolUse)

Register in `~/.gemini/antigravity-cli/hooks.json`. The `command` MUST be an
ABSOLUTE path (relative paths resolve against the launch cwd and fail with exit
127, silently bypassing the gate). The matcher is the agy file-management tool
names. `timeout` MUST be `>= 2 * RESOLVER_GIT_TIMEOUT_S` (= 10):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "write_to_file|replace_file_content|multi_replace_file_content",
        "timeout": 10,
        "hooks": [
          {"type": "command", "command": "/home/you/.gemini/antigravity-cli/hooks/skill-gate.sh"}
        ]
      }
    ]
  }
}
```

agy constraints (r15-M4/r16-L5):
- ABSOLUTE `command` path (JSON does not expand `~` or `$HOME`; replace
  `/home/you` with your real home directory).
- ALWAYS exit 0 (non-zero = hook FAILURE, not a block).
- jq may be ABSENT on agy hosts; the adapter parses with python3.

## Install (HOST-LEVEL)

This is a HOST-LEVEL change: it creates symlinks under the `~/` agent config
dirs. These are NEW filenames (`skill-gate.sh`, `skill_gate.py`), so `ln -sf`
will not clobber existing hooks. Execution context: host. Impact: new symlinks
in `~/` agent dirs + the new core symlink in `~/.ai-playbook/scripts/`. Rollback:
`rm` the symlink paths.

```bash
# Resolve clone path from user facts (key: instructions_repo); edit before running.
INSTRUCTIONS_REPO=~/path/to/ai-playbook
# r12-M2: create target parent dirs that do not always exist on a default install
# (the Task 3 INSTALL already mkdir'd these once; re-running is idempotent).
# r13-M3: ~/.ai-playbook/scripts/ is the symlink TARGET dir for the cores + helper.
mkdir -p ~/.ai-playbook/scripts ~/.codex/hooks ~/.gemini/antigravity-cli/hooks ~/.claude/hooks ~/.cursor/hooks
# Core + 2 leaves symlinked to ~/.ai-playbook/scripts/ (the core is
# subprocess-invoked by every adapter; the leaves are NOT directly invoked by
# the adapters but are symlinked alongside for single-source-model consistency
# and so a partial install is caught loudly; see the lessons-recall README's
# install block for the shared leaf rationale).
ln -sf "$INSTRUCTIONS_REPO/scripts/skill_gate.py"      ~/.ai-playbook/scripts/skill_gate.py
ln -sf "$INSTRUCTIONS_REPO/scripts/facts_paths.py"     ~/.ai-playbook/scripts/facts_paths.py
ln -sf "$INSTRUCTIONS_REPO/scripts/lessons_classify.py" ~/.ai-playbook/scripts/lessons_classify.py
ln -sf "$INSTRUCTIONS_REPO/scripts/hooks_probe.py"       ~/.ai-playbook/scripts/hooks_probe.py
ln -sf "$INSTRUCTIONS_REPO/scripts/hooks_log_summary.py" ~/.ai-playbook/scripts/hooks_log_summary.py
# Four skill-gate adapter symlinks (absolute targets)
ln -sf "$INSTRUCTIONS_REPO/agents/hooks/skill-gate/claude.sh" ~/.claude/hooks/skill-gate.sh
ln -sf "$INSTRUCTIONS_REPO/agents/hooks/skill-gate/codex.sh"  ~/.codex/hooks/skill-gate.sh
ln -sf "$INSTRUCTIONS_REPO/agents/hooks/skill-gate/cursor.sh" ~/.cursor/hooks/skill-gate.sh
ln -sf "$INSTRUCTIONS_REPO/agents/hooks/skill-gate/agy.sh"    ~/.gemini/antigravity-cli/hooks/skill-gate.sh
```

(The Task 3 INSTALL step covers the helper + four lessons-recall adapter
symlinks. The Codex symlink above is created for doctor path-resolution but is
NOT wired into any Codex config until Codex ships a blocking `pre_tool_use`.)

The cores + helper are SYMLINKED to `~/.ai-playbook/scripts/` (the
single-source model; a deviation from the four existing copy-synced lessons
scripts, whose cleanup is out of scope).

## Doctor

`python3 ~/.ai-playbook/scripts/skill_gate.py --doctor` runs FIVE checks (see
the Task 4 Doctor spec for the full algorithm):

1. **PreToolUse array** (`~/.claude/settings.json`): an entry whose matcher
   `|`-split alternation is a SUPERSET of `{Write,Edit,MultiEdit}` is present,
   AND a SEPARATE `Bash` entry is preserved (no regression of
   `check-plan-review-gate.sh`).
2. **11 paths live + parent dirs exist**: the helper + 2 cores + 8 adapter
   symlinks all resolve (no dangling links); the parent dirs
   (`~/.ai-playbook/scripts/`, `~/.codex/hooks/`,
   `~/.gemini/antigravity-cli/hooks/`, `~/.claude/hooks/`, `~/.cursor/hooks/`)
   exist.
3. **Subprocess idiom**: each adapter greps clean for the literal
   `python3 ~/.ai-playbook/scripts/session_channel.py` invocation and does NOT
   read `CLAUDE_CODE_SESSION_ID` directly. (KNOWN LIMITATION: the predicate
   flags the literal env-var name anywhere in the file, including the required
   Claude empty-SID warning string; both `claude.sh` adapters emit that warning
   per the r12-M4 plan obligation. This is a Task 4 core predicate issue, not
   an adapter defect.)
4. **Core-symbol + writable runtime**: the installed core resolves
   `classify_path`/`check_marker`, creates `~/.ai-playbook/runtime/skill-invoked/`
   if absent, and confirms that dir is writable by the skill uid.
5. **agy hook timeout**: the `~/.gemini/antigravity-cli/hooks.json` PreToolUse
   entry carrying the skill-gate matcher has `timeout > RESOLVER_GIT_TIMEOUT_S`
   (r15-M4/r17-M4). (KNOWN LIMITATION: the predicate looks for a
   `Write|Edit|MultiEdit` matcher token, but the real agy matcher is the agy
   tool-name vocabulary `write_to_file|replace_file_content|multi_replace_file_content`
   per the cited article. The host hooks.json ships the REAL agy matcher so the
   gate actually fires; this doctor check is a Task 4 core predicate issue.)

## Block message + observability

**Block message** (EXACT text, per class):
- Plans: `Invoke the plans skill before authoring a plan file.`
- Learn: `Invoke the learn skill before editing the project lessons corpus.`

(emitted as `deny_reason`).
- Claude surfaces it on stderr + exit 2.
- Codex, Cursor, and agy all surface it as a flat top-level
  `{"allow_tool": false, "deny_reason": ...}` envelope, exit 0 (see the
  json.dumps-envelope shapes above).

**Observability** (LOUD keying mode, r11-M2): `~/.ai-playbook/logs/hooks.log`
records one JSON line per consultation.
- The CORE emits `keying=env-var` (a session id was supplied - Claude steady
  state; Cursor with optional session bridge installed) / `keying=project-only`
  (no session id - Codex steady state; Cursor/agy without bridge at v9). `keying`
  is PURE LOG METADATA and drives NO core branch.
- The RESOLVER `facts_paths.resolve_project_key` emits `keying=no-anchor` on its
  git-failure branch (a non-git dir; treat any `keying=no-anchor` line as a real
  signal, not steady state - r12-L4: in a non-git tree, `project` is
  cwd-derived and UNSTABLE across `cd`).
- `keying=fail-open` = a marker-store `OSError` (EROFS/EIO/ELOOP/ENOSPC, or a
  `realpath` `OSError` in resolve/classify) was caught by `_consult`'s
  `except OSError` arm; the gate ALLOWED the write with a stderr warning (the
  LOUD fail-open aperture). The gate failed OPEN, not OFF.
- `keying=error` = an unexpected non-`OSError` exception escaped `_consult` to
  `main`'s generic `except Exception` backstop; the gate ALLOWED the write
  (Family-G backstop, also with a stderr warning). Both labels mean the gate
  failed OPEN; investigate either.

The three runtime paths are DISPOSABLE (safe to delete):
- `~/.ai-playbook/runtime/skill-invoked/` (markers)
- `~/.ai-playbook/runtime/lessons-recall/` (dedup state, owned by Task 3)
- `~/.ai-playbook/logs/hooks.log` (one JSON line per consultation)

## Capability probe (steady state)

Run `python3 scripts/hooks_probe.py --all` from the instructions repo (or
`python3 ~/.ai-playbook/scripts/hooks_probe.py --all` after the core symlink
exists). Exit 0 when no cell is FAIL; DEGRADED is honest steady state for Codex.
Weekly cron (Mondays 09:00 local):

```cron
0 9 * * 1 python3 "$HOME/.ai-playbook/scripts/hooks_probe.py" --all >> "$HOME/.ai-playbook/logs/hooks-probe.log" 2>&1
```

| Agent | Probe tier | Wiring | Notes |
|-------|------------|--------|-------|
| Claude | FULL | `PreToolUse` `Write\|Edit\|MultiEdit` + adapter symlink | stderr + exit 2 on block |
| Codex | DEGRADED | Adapter symlink only | No blocking `pre_tool_use` in this install; symlink for doctor/future wiring |
| agy | FULL | `PreToolUse` file-tool matcher + adapter symlink | Top-level JSON block; exit 0 always |
| Cursor | FULL | `preToolUse` `Write\|EditNotebook` + adapter symlink | Full-fidelity blocking |

The probe never PASSes when the adapter symlink or required config registration
is missing for a FULL-tier cell.
