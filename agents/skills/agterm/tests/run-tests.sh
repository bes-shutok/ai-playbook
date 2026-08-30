#!/usr/bin/env bash
# agterm skill self-tests.
#
# Three layers, all local and read-only against the real app:
#   1. doc integrity of the skill directory (references resolve, no absolute paths)
#   2. bundled/guard paths of scripts/show-image.sh (no rendering)
#   3. the agent-status integration contract: the installer's wrappers and the shell
#      integration are exercised against a STUB agtermctl that records its argv, so
#      nothing here touches a live session. Live checks at the end are read-only
#      (version / tree / keymap list) and skip when no app is serving the socket.
#
# Usage: bash tests/run-tests.sh     (from anywhere; paths derive from this file)

set -u
SKILL_DIR=$(cd "$(dirname "$0")/.." && pwd)
REPO_ROOT=$(cd "$SKILL_DIR/../../.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

PASS=0; FAIL=0; SKIP=0
ok()   { PASS=$((PASS+1)); printf 'ok    %s\n' "$1"; }
fail() { FAIL=$((FAIL+1)); printf 'FAIL  %s\n' "$1"; }
skip() { SKIP=$((SKIP+1)); printf 'skip  %s\n' "$1"; }

assert_contains() { # desc haystack needle
  case "$2" in *"$3"*) ok "$1" ;; *) fail "$1 (missing: $3)" ;; esac
}
assert_not_contains() { # desc haystack needle
  case "$2" in *"$3"*) fail "$1 (unexpected: $3)" ;; *) ok "$1" ;; esac
}
assert_eq() { # desc expected actual
  [ "$2" = "$3" ] && ok "$1" || fail "$1 (expected [$2], got [$3])"
}
assert_token() { # desc haystack token  (whitespace-delimited, so --blink does not match --blink2)
  case " $(printf '%s' "$2" | tr '\n' ' ') " in *" $3 "*) ok "$1" ;; *) fail "$1 (missing token: $3)" ;; esac
}

# stub agtermctl: records its full argv as one line into $STUB_LOG, exits 0.
# STUB_LOG must be exported: the stub is spawned by wrappers we do not control.
export STUB_LOG="$TMP/stub.log"; : > "$STUB_LOG"
cat > "$TMP/stub-agtermctl" <<STUB
#!/usr/bin/env bash
printf '%s\n' "\$*" >> "\$STUB_LOG"
exit 0
STUB
chmod +x "$TMP/stub-agtermctl"
stub_log_grep() { grep -F -- "$1" "$STUB_LOG" 2>/dev/null; }

# pinned-PATH helper: a stub copy NAMED agtermctl, so tests that exercise a
# "find agtermctl on PATH" code path resolve the stub, never the real binary
mkdir -p "$TMP/bin" && cp "$TMP/stub-agtermctl" "$TMP/bin/agtermctl"

echo "== 1. doc integrity =="
for f in SKILL.md reference.md examples.md cookbook.md troubleshooting.md agent-runtimes.md \
         scripts/show-image.sh LICENSE.txt; do
  [ -f "$SKILL_DIR/$f" ] && ok "exists: $f" || fail "exists: $f"
done
grep -q '^name: *agterm' "$SKILL_DIR/SKILL.md" &&
  ok "frontmatter names the skill" || fail "frontmatter names the skill"
grep -q 'agent-runtimes\.md' "$SKILL_DIR/SKILL.md" &&
  ok "SKILL.md references agent-runtimes.md" || fail "SKILL.md references agent-runtimes.md"
# no machine-specific absolute home-path prefixes in any tracked skill file (repo
# rule); the prefix is built from parts so this scan does not flag its own pattern,
# and the tests directory is excluded — the check would otherwise match itself
home_prefix="/$(printf 'Users')"
leaks=$(grep -R "$home_prefix/" "$SKILL_DIR" --include='*.md' --include='*.sh' --exclude-dir=tests 2>/dev/null)
[ -z "$leaks" ] && ok "no absolute home-path prefixes in skill files" || fail "no absolute home-path prefixes in skill files"
grep -q '^| `agterm` | `agents/skills/agterm/SKILL.md`' "$REPO_ROOT/README.md" &&
  ok "README catalogs agterm (catalog row)" || fail "README catalogs agterm (catalog row)"

echo "== 2. show-image.sh guard paths =="
si="$SKILL_DIR/scripts/show-image.sh"
bash "$si" >/dev/null 2>&1; [ $? -eq 2 ] && ok "no args -> usage exit 2" || fail "no args -> usage exit 2"
bash "$si" "$TMP/nope.png" >/dev/null 2>&1; [ $? -eq 1 ] && ok "missing image -> exit 1" || fail "missing image -> exit 1"
# outside agterm (AGTERM_ENABLED unset) with the pinned stub as agtermctl: must refuse and suggest open
out=$(env -u AGTERM_ENABLED PATH="$TMP/bin:$PATH" bash "$si" "$SKILL_DIR/SKILL.md" 2>&1); rc=$?
[ $rc -eq 1 ] && assert_contains "outside agterm -> open fallback hint" "$out" 'open'
[ $rc -eq 1 ] || fail "outside agterm -> exit 1"
# inside agterm but agtermctl nowhere on PATH
out=$(env AGTERM_ENABLED=1 PATH="/usr/bin:/bin" bash "$si" "$SKILL_DIR/SKILL.md" 2>&1); rc=$?
[ $rc -eq 1 ] && assert_contains "no agtermctl on PATH -> says so" "$out" 'agtermctl not on PATH'
[ $rc -eq 1 ] || fail "no agtermctl on PATH -> exit 1"

echo "== 3. agent-status wrapper contract =="
WRAPPER=""
for c in "$HOME/.config/agterm/agent-status/agterm-agent-status.sh" \
         "/Applications/agterm.app/Contents/Resources/agent-status/agterm-agent-status.sh"; do
  [ -f "$c" ] && { WRAPPER="$c"; break; }
done
if [ -z "$WRAPPER" ]; then
  skip "wrapper contract (no agterm-agent-status.sh installed)"
else
  # full environment: state + pane + pane-id + socket + forwarded flags
  : > "$STUB_LOG"
  out=$(env AGTERM_SESSION_ID=sid-1 AGTERM_SOCKET=/tmp/agt.sock AGTERM_PANE=right AGTERM_PANE_ID=tok-9 \
    AGTERMCTL="$TMP/stub-agtermctl" bash "$WRAPPER" blocked --blink 2>&1); rc=$?
  line=$(stub_log_grep 'session status' | head -1)
  [ $rc -eq 0 ] && [ -z "$out" ] && ok "wrapper exits 0, output suppressed" || fail "wrapper exits 0, output suppressed (rc=$rc out=$out)"
  assert_contains "wrapper targets own session" "$line" '--target sid-1'
  assert_contains "wrapper passes explicit socket" "$line" '--socket /tmp/agt.sock'
  assert_contains "wrapper forwards pane role" "$line" '--pane right'
  assert_contains "wrapper forwards pane-id token" "$line" '--pane-id tok-9'
  assert_token "wrapper forwards extra flags" "$line" '--blink'
  # no socket env: no --socket argument
  : > "$STUB_LOG"
  env AGTERM_SESSION_ID=sid-1 AGTERMCTL="$TMP/stub-agtermctl" bash "$WRAPPER" active >/dev/null 2>&1
  assert_not_contains "no AGTERM_SOCKET -> no --socket arg" "$(stub_log_grep 'session status')" '--socket'
  # outside agterm: silent no-op, stub never called
  : > "$STUB_LOG"
  env -u AGTERM_SESSION_ID AGTERMCTL="$TMP/stub-agtermctl" bash "$WRAPPER" active >/dev/null 2>&1
  rc=$?; calls=$(wc -l < "$STUB_LOG" | tr -d ' ')
  [ $rc -eq 0 ] && [ "$calls" = "0" ] && ok "outside agterm -> no-op, no agtermctl call" || fail "outside agterm -> no-op, no agtermctl call"
  # resolution branch 3 (no AGTERMCTL override; find agtermctl on PATH): only safe to
  # pin against the APP-BUNDLE wrapper, whose default is bare `agtermctl`. The
  # installer-rewritten copy bakes the real app binary, which must never be invoked here.
  BUNDLE_WRAPPER="/Applications/agterm.app/Contents/Resources/agent-status/agterm-agent-status.sh"
  if [ -f "$BUNDLE_WRAPPER" ]; then
    : > "$STUB_LOG"
    env AGTERM_SESSION_ID=sid-1 PATH="$TMP/bin:$PATH" bash "$BUNDLE_WRAPPER" active >/dev/null 2>&1
    assert_token "wrapper resolves agtermctl from PATH" "$(stub_log_grep 'session status')" '--target sid-1'
  else
    skip "wrapper PATH-fallback branch (app bundle not present)"
  fi
fi

echo "== 4. codex lifecycle wrapper =="
CODEX_WRAPPER=""
for c in "$HOME/.config/agterm/agent-status/agterm-codex-status.sh" \
         "/Applications/agterm.app/Contents/Resources/agent-status/agterm-codex-status.sh"; do
  [ -f "$c" ] && { CODEX_WRAPPER="$c"; break; }
done
if [ -z "$CODEX_WRAPPER" ]; then
  skip "codex wrapper (agterm-codex-status.sh not installed)"
else
  codex_run() { # stdin JSON, action args...
    env AGTERM_SESSION_ID=sid-1 AGTERMCTL="$TMP/stub-agtermctl" \
        AGTERM_STATUS_WRAPPER="$TMP/stub-agtermctl" \
        AGTERM_CODEX_WATCH_FILE="$TMP/codex-watch-token" \
        AGTERM_CODEX_WATCH_MAX_CHECKS=1 AGTERM_CODEX_WATCH_INTERVAL=0 \
        bash "$CODEX_WRAPPER" "$@"
  }
  # AGTERM_STATUS_WRAPPER is the stub itself, so the log carries the bare state
  # word the wrapper would have forwarded, not a full `session status` argv.
  : > "$STUB_LOG"; codex_run session-start </dev/null >/dev/null 2>&1
  assert_eq "session-start -> idle" "idle" "$(cat "$STUB_LOG")"
  : > "$STUB_LOG"; printf '{"last_assistant_message":"shall we proceed?"}' | codex_run stop >/dev/null 2>&1
  assert_eq "stop + question mark -> blocked" "blocked" "$(cat "$STUB_LOG")"
  : > "$STUB_LOG"; printf '{"last_assistant_message":"all done"}' | codex_run stop >/dev/null 2>&1
  assert_eq "stop without question -> completed --auto-reset" "completed --auto-reset" "$(cat "$STUB_LOG")"
  : > "$STUB_LOG"; codex_run permission-request </dev/null >/dev/null 2>&1
  [ "$(grep -cE '^(idle|active|blocked|completed)' "$STUB_LOG")" = "0" ] &&
    ok "permission-request alone sets no status" || fail "permission-request alone sets no status"
  [ -f "$TMP/codex-watch-token" ] &&
    ok "watcher token file stays inside the sandbox" || fail "watcher token file stays inside the sandbox"
  # stop the pending watcher (removing its token breaks its poll loop) and give it
  # a beat to exit, so its async stub write cannot land after the next truncation
  rm -f "$TMP/codex-watch-token"; sleep 1
  : > "$STUB_LOG"
  env -u AGTERM_SESSION_ID AGTERMCTL="$TMP/stub-agtermctl" AGTERM_STATUS_WRAPPER="$TMP/stub-agtermctl" \
    bash "$CODEX_WRAPPER" session-start </dev/null >/dev/null 2>&1
  [ "$(wc -l < "$STUB_LOG" | tr -d ' ')" = "0" ] && ok "codex wrapper outside agterm -> no calls" || fail "codex wrapper outside agterm -> no calls"
fi

echo "== 5. shell integration =="
INTEG=""
for c in "$HOME/.config/agterm/agent-status/shell/integration.sh" \
         "/Applications/agterm.app/Contents/Resources/agent-status/shell/integration.sh"; do
  [ -f "$c" ] && { INTEG="$c"; break; }
done
if [ -z "$INTEG" ]; then
  skip "shell integration (integration.sh not installed)"
else
  # stub status binary the integration will call via AGTERM_AGENT_BIN
  cat > "$TMP/stub-status" <<STUB
#!/usr/bin/env bash
printf '%s\n' "\$*" >> "$STUB_LOG"
exit 0
STUB
  chmod +x "$TMP/stub-status"
  # bash: source with a stubbed status binary, default regex
  : > "$STUB_LOG"
  bash -c '
    export AGTERM_SESSION_ID=sid-1
    export AGTERM_AGENT_BIN="'"$TMP"'/stub-status"
    source "'"$INTEG"'"
    _ags_preexec "cursor-agent --resume" || true
    _ags_precmd || true
  ' >/dev/null 2>&1
  assert_eq "integration: matching command -> active --blink" "active --blink" "$(sed -n '1p' "$STUB_LOG")"
  assert_eq "integration: next prompt -> idle" "idle" "$(sed -n '2p' "$STUB_LOG")"
  # custom regex: copilot in, cursor-agent out
  : > "$STUB_LOG"
  bash -c '
    export AGTERM_SESSION_ID=sid-1
    export AGTERM_AGENT_BIN="'"$TMP"'/stub-status"
    export AGTERM_AGENT_RE="^(copilot)([[:space:]]|\$)"
    source "'"$INTEG"'"
    _ags_preexec "copilot" || true
    _ags_preexec "cursor-agent --resume" || true
  ' >/dev/null 2>&1
  assert_eq "custom regex: copilot matches and cursor-agent is excluded" "active --blink" "$(cat "$STUB_LOG")"
  # no AGTERM_SESSION_ID: sourcing is a clean no-op, no hooks installed
  bash -c 'unset AGTERM_SESSION_ID; source "'"$INTEG"'"; declare -F _ags_preexec >/dev/null && exit 1; exit 0' >/dev/null 2>&1 &&
    ok "outside agterm: no hooks installed" || fail "outside agterm: no hooks installed"
fi

echo "== 6. resume-pin hook pattern: run the DOCUMENTED snippet from examples.md =="
if command -v jq >/dev/null 2>&1; then
  # extract the fenced hook snippet out of examples.md and execute THAT, so the
  # test pins the published text rather than a hand-copied transcription of it
  awk '/^## Keep a forking agent session reattaching/{f=1; next}
       f && /^```bash$/{c=1; next}
       c && /^```$/{exit}
       c {print}' "$SKILL_DIR/examples.md" > "$TMP/hook-snippet.sh"
  [ -s "$TMP/hook-snippet.sh" ] &&
    ok "hook snippet extracted from examples.md" || fail "hook snippet extracted from examples.md"
  pin_run() { # stdin JSON -> the documented snippet, with the stub as agtermctl
    ( export PATH="$TMP/bin:$PATH" AGTERM_SESSION_ID=sid-1 AGTERM_PANE_ID=tok-9
      bash "$TMP/hook-snippet.sh" )
  }
  : > "$STUB_LOG"; printf '{"session_id":"abc-123"}' | pin_run >/dev/null 2>&1
  line=$(stub_log_grep 'session restore' | tr '\n' ' ')
  assert_contains "pin carries the live resume line" "$line" 'claude --resume abc-123'
  assert_token "pin targets own session" "$line" '--target'
  assert_token "pin targets sid-1" "$line" 'sid-1'
  assert_token "pin carries pane-id" "$line" '--pane-id'
  # the guard must refuse any unusable id: absent, whitespace-padded, or not id-shaped
  for bad in '{}' '{"session_id":"   "}'; do
    : > "$STUB_LOG"; printf '%s' "$bad" | pin_run >/dev/null 2>&1
    [ "$(wc -l < "$STUB_LOG" | tr -d ' ')" = "0" ] &&
      ok "unusable session_id (${bad}) -> guard leaves the pin alone" ||
      fail "unusable session_id (${bad}) -> guard leaves the pin alone"
  done
  : > "$STUB_LOG"; printf '{"session_id":"x;touch /tmp/pwned"}' | pin_run >/dev/null 2>&1
  [ "$(wc -l < "$STUB_LOG" | tr -d ' ')" = "0" ] &&
    ok "non-id-shaped session_id -> guard refuses to pin shell code" ||
    fail "non-id-shaped session_id -> guard refuses to pin shell code"
else
  skip "resume-pin pattern (jq not installed)"
fi

echo "== 7. live read-only smoke (skipped when no app serves the socket) =="
if command -v agtermctl >/dev/null 2>&1 && command -v jq >/dev/null 2>&1 && agtermctl version --json >/dev/null 2>&1; then
  v=$(agtermctl version --json 2>/dev/null | jq -r '.result.app.version // empty' 2>/dev/null)
  [ -n "$v" ] && ok "live: serving app reports version ($v)" || fail "live: serving app reports version"
  if [ -n "$v" ]; then
    agtermctl tree --json 2>/dev/null | jq -e '.result.tree.workspaces | type == "array"' >/dev/null 2>&1 &&
      ok "live: tree --json parses" || fail "live: tree --json parses"
    agtermctl keymap list --json 2>/dev/null | jq -e '.result.keymap.diagnostics' >/dev/null 2>&1 &&
      ok "live: keymap list --json parses" || fail "live: keymap list --json parses"
  fi
else
  skip "live smoke (agtermctl, jq, or serving app unavailable)"
fi

echo
echo "passed=$PASS failed=$FAIL skipped=$SKIP"
[ "$FAIL" -eq 0 ]
