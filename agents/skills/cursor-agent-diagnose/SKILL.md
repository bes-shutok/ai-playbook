---
name: cursor-agent-diagnose
description: >
  Diagnose Cursor IDE agent runtime failures: dead shell, hook blocks, missing skills, done lock,
  wrong GitHub account, edit round-trip failures, MCP auth gaps. Use when the agent behaves
  strangely, /done fails, gh or GitHub PR commands fail, hooks block edits, simple file edits fail,
  or the user asks to diagnose Cursor agent config.
---

# Cursor agent diagnose

Run a **fast, ordered checklist** before blaming project config or proposing fixes. Distinguish Cursor IDE bugs (intermittent shell host), local hook amplification, `gh` account mismatch, and missing skill catalog.

**Boundary:** Runtime/environment diagnosis only. For application bugs, use `systematic-debugging`. For GitHub PR mechanics after auth is confirmed, use `github-pr-workflow`.

## When to use

- Agent cannot run shell commands (`no exit status`, empty output)
- `/done` or other shell-heavy skills fail mid-workflow
- `gh` / GitHub PR commands fail while manual terminal works
- Hooks block edits or MCP with "shell execution unavailable"
- Agent claims an edit succeeded but file content is unchanged
- User asks to diagnose Cursor, cursor-agent, hooks, or skills setup

## Configuration (from facts document)

| Key | Purpose | Fallback |
|-----|---------|----------|
| `done_lock_script` | Per-repo done lock | `~/.ai-playbook/scripts/done-lock.sh` |
| `public_hygiene_scan_script` | Hygiene gate used by done | `~/.ai-playbook/scripts/scan-public-hygiene.sh` |
| GitHub accounts table | Expected `gh` user per scope | Infer from `origin` remote (see Step 3) |

Optional env overrides for the bundled script (local testing):

```bash
export DONE_LOCK_SCRIPT="${DONE_LOCK_SCRIPT:-${HOME}/.ai-playbook/scripts/done-lock.sh}"
export CURSOR_HOOKS_DIR="${CURSOR_HOOKS_DIR:-${HOME}/.cursor/hooks}"
export GH_USER_EXPECTED="<gh user expected for this repo>"
```

Resolve `GH_USER_EXPECTED` from the user facts GitHub accounts table when the repo owner is not the default check.

## Workflow

Run all steps in order. Report **PASS / FAIL / SKIP** with raw output. Do not propose fixes until the verdict table is complete.

### Step 0: Load facts

Read `user_facts_path` when path-dependent keys are needed (GitHub accounts, script paths).

### Step 1: Automated checks (script)

From the project git root (or any cwd for shell/hook checks):

```bash
bash agents/skills/cursor-agent-diagnose/run.sh
```

When the project is not the skills repo (normal for company repos), use the installed skill copy:

```bash
bash "${HOME}/.cursor/skills/cursor-agent-diagnose/run.sh"
```

Or set `CURSOR_AGENT_DIAGNOSE_SCRIPT` to an absolute path under `skills_repo_path`.

Capture stdout. `SUMMARY: ALL_AUTOMATED_CHECKS_PASS` means checks 1-5 passed (and 7 is informational).

If **Step 1 shell commands fail before the script runs** (no exit status, hook denial, empty output), record **Step 1 FAIL** and skip to Step 6 (verdict). That result alone often means IDE shell host failure.

### Step 2: Manual shell probe (when script could not run)

Only when Step 1 did not execute:

```bash
echo "SHELL_OK"; date +%s; pwd; echo "exit=$?"
```

**PASS:** `SHELL_OK`, timestamp, cwd, `exit=0`.

### Step 3: Skills catalog (agent self-report)

Inspect the session's skill list (injected catalog or user-attached skills). Report:

- Total skill count visible to this session
- Whether `done` appears (by name or path)
- Whether the user manually attached the skill vs ambient discovery

**PASS:** `done` listed or explicitly attached for a `/done` diagnosis.

**FAIL:** Empty catalog or `done` missing when diagnosing done failures.

Known Cursor issue: catalog may be empty for the first turn after launch. Recovery: reload window, wait a few seconds, start a fresh agent chat.

### Step 4: Edit round-trip probe (agent)

Run only when Step 1 shell passed. Confirms this session can write and read a file, not just run shell.

1. Resolve probe path: `{tmp_dir}/cursor-agent-diagnose-probe.md` from `.ai-playbook/facts.md` TOML; fallback `docs/tmp/cursor-agent-diagnose-probe.md`.
2. Write one unique marker line (for example `PROBE_OK ts=<unix-epoch>`).
3. Read the file back and confirm the marker is present verbatim.
4. Delete the probe file (or remove the marker line) before finishing.

**PASS:** marker written, read back matches, cleanup done.

**FAIL:** write blocked, read mismatch, file unchanged after claimed edit, or cleanup left probe debris.

Use a direct file edit for the write. Do not use shell `sed`, `perl`, or piped rewrites for this probe.

### Step 5: IDE vs CLI versions (informational)

When accessible:

```bash
cursor-agent --version 2>/dev/null || true
```

IDE app version is separate from `cursor-agent` CLI. Record both when the user reports a specific build (for example `2026.07.09-a3815c0`).

### Step 6: Verdict table

Fill this table and pick **one primary root cause**:

```markdown
| Check | Result | Notes |
|-------|--------|-------|
| 1 Shell | PASS/FAIL | |
| 2 Hooks | PASS/FAIL | |
| 3 GitHub | PASS/FAIL | `gh repo view` works; for **User**-owned repos, active login must match owner; for **Organization** repos, active user may differ from org login |
| 4 done scripts/lock | PASS/FAIL | |
| 5 tmp writable | PASS/FAIL/SKIP | shell write under `{tmp_dir}` |
| 6 Skills catalog | PASS/FAIL/SKIP | |
| 7 Edit probe | PASS/FAIL/SKIP | agent round-trip |
| 8 MCP CLI | PASS/FAIL/SKIP/INFO | IDE MCP may still work |

**Primary root cause:** (pick one)
- IDE shell dead
- gh wrong account
- done lock held
- skills not loaded
- hooks amplifying shell failure
- edit tool or verification failure
- inconclusive (all pass; suspect network/model)
```

### Step 7: Recovery (minimal, ordered)

Apply **only** the fix matching the primary root cause. One recovery pass, then offer to re-run the diagnostic.

| Root cause | Recovery |
|------------|----------|
| IDE shell dead | Developer: Reload Window; new agent chat; optional Settings → Agents → Legacy Terminal Tool, then fully quit and reopen Cursor |
| gh wrong account | `gh auth switch --user <human-login>` from facts table when **User**-owned repo fails or `gh repo view` fails; never switch to an org login (for example `<org-login>`) |
| done lock held | `"${DONE_LOCK_SCRIPT:-${HOME}/.ai-playbook/scripts/done-lock.sh}" status`; `stale-clean` only if abandoned/stale |
| skills not loaded | Reload; wait; re-attach skill; fresh chat |
| hooks amplifying shell failure | Same as IDE shell dead; do not remove hooks as first response |
| edit tool or verification failure | Retry in a fresh chat; confirm Run Everything / file-edit permissions; avoid shell regex for markdown edits |
| inconclusive | New chat; check status.cursor.com; Network → HTTP Compatibility Mode → HTTP/1.1 |

## Pattern reference

| Pattern | Likely cause |
|---------|----------------|
| 1 FAIL, later checks untested | IDE shell host dead |
| 1 PASS, 2 FAIL | Hook runner / shell-exec race |
| 1-2 PASS, 3 FAIL on personal User-owned repo | Active `gh` user is company account |
| 1-2 PASS, 3 FAIL on org repo with company user active | False positive if script compares active user to org login; re-run with fixed diagnose script |
| 1-4 PASS, 5 FAIL | `{tmp_dir}` missing or not writable |
| 1-5 PASS, 6 FAIL | Skill catalog race or empty session |
| 1-5 PASS, 7 FAIL | Edit blocked or agent did not verify write |
| All PASS, user still blocked | Network/model slowness or wrong workspace root |
| All PASS incl edit, staging loops | Model tool choice / verification gap, not runtime config |

## Rules

- Run the diagnostic before editing hooks, rules, or MCP config.
- Do not treat a single failed session as proof of misconfiguration; check for intermittent shell failures.
- Do not remove `failClosed` hooks as the first fix; reload and retry first.
- Distinguish IDE chat MCP from `cursor-agent` CLI MCP auth.
- Keep output concise: verdict table + one recovery recommendation unless the user asks for detail.
