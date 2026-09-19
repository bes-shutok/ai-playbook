# Codex token-budget reset guard

This hook denies the AI's `mcp__codex_app__consume_usage_reset` tool call.
The manual reset action in the Codex UI does not pass through the agentic
`PreToolUse` loop, so a person can still reset the budget there.

## Registration

Add this matcher group to `~/.codex/hooks.json`. Replace `<repo-root>` with the
absolute path to this repository because Codex does not expand `~` in JSON
command strings:

```json
{
  "PreToolUse": [
    {
      "matcher": "^mcp__codex_app__consume_usage_reset$",
      "hooks": [
        {
          "type": "command",
          "command": "<repo-root>/agents/hooks/codex-budget-reset-guard/codex.sh",
          "timeout": 3,
          "statusMessage": "Checking token-budget reset policy"
        }
      ]
    }
  ]
}
```

Merge the group into the existing `hooks.PreToolUse` array; do not replace
other groups. The hook must remain synchronous because background hooks cannot
block a tool call.

Codex must review and trust the new hook definition before it runs. After
registration, open `/hooks` in Codex, trust the hook, and start a new session
if the current session does not reload the configuration.

## Enforcement boundary

The guard is intentionally narrow: it blocks the current canonical reset-tool
name and allows all other tool calls. A future Codex release that renames or
adds another reset path needs a corresponding matcher and test update. This
hook does not protect against changing or disabling the local hook
configuration, using an alternate unrecognized backend path, or a specialized
tool path that opts out of Codex's local hook system.

## Test

From the repository root:

```bash
python3 -m unittest discover -s scripts -p 'test_codex_budget_reset_guard.py'
```
