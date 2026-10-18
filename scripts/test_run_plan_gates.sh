#!/usr/bin/env bash
# Selftest for scripts/run_plan_gates.sh, driven entirely through the
# documented RUN_PLAN_GATES_OVERRIDE seam so no real gate runs here.
# Hermetic: the fixture repository lives in one mktemp tree, git is isolated
# from host config, and the fake gates are throwaway scripts under tmp.
# Assertions:
#   1. Pass polarity: two passing fake gates (one with an OUTCOME line, one
#      without) both run; the bundle exits 0 and ends `OUTCOME: pass`.
#   2. Fail polarity: a passing gate followed by a failing gate; all gates
#      still run, the first failure is named, the bundle exits 1 and ends
#      `OUTCOME: fail`, and the kept log carries the failing gate's output.
#   3. First-failure naming: with two failing gates the bundle names the
#      first one, not the second.
#   4. Usage errors: an unknown argument, a RUN_PLAN_GATES_OVERRIDE
#      naming a missing file, and an override holding only blank or
#      comment lines (no runnable gate command) each exit 3 ending
#      `OUTCOME: tool_error`.
#   5. --help is a metadata exit: usage text, exit 0, no OUTCOME line.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE="${SCRIPT_DIR}/run_plan_gates.sh"

fail() {
  echo "selftest FAIL: $1" >&2
  exit 1
}

TMP="$(mktemp -d "${TMPDIR:-/tmp}/run-plan-gates-selftest.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

REPO="${TMP}/repo"
mkdir -p "$REPO"
(
  cd "$REPO"
  export GIT_CONFIG_GLOBAL="${TMP}/git-config"
  export GIT_CONFIG_SYSTEM="${TMP}/git-config"
  git init -q
  git -c user.email=t@t -c user.name=t commit --allow-empty -qm init
)

FAKES="${TMP}/fakes"
mkdir -p "$FAKES"
cat > "${FAKES}/pass_outcome.sh" <<'EOF'
#!/usr/bin/env bash
echo "fake gate with outcome: running"
echo "OUTCOME: pass"
exit 0
EOF
cat > "${FAKES}/pass_silent.sh" <<'EOF'
#!/usr/bin/env bash
echo "fake gate without outcome contract: running"
exit 0
EOF
cat > "${FAKES}/fail_gate.sh" <<'EOF'
#!/usr/bin/env bash
echo "fake gate boom: evidence line"
echo "OUTCOME: fail"
exit 1
EOF
chmod +x "${FAKES}/pass_outcome.sh" "${FAKES}/pass_silent.sh" "${FAKES}/fail_gate.sh"

run_bundle() {
  (
    cd "$REPO"
    export GIT_CONFIG_GLOBAL="${TMP}/git-config" GIT_CONFIG_SYSTEM="${TMP}/git-config"
    env RUN_PLAN_GATES_OVERRIDE="${1-}" bash "$BUNDLE" "${2-}"
  )
}

# ---- 1) pass polarity ----
cat > "${TMP}/override-pass.txt" <<EOF
${FAKES}/pass_outcome.sh
${FAKES}/pass_silent.sh
EOF

PASS_RC=0
run_bundle "${TMP}/override-pass.txt" >"${TMP}/pass.out" 2>"${TMP}/pass.err" || PASS_RC=$?
[[ "$PASS_RC" -eq 0 ]] || fail "pass polarity rc=${PASS_RC}, want 0"
[[ "$(tail -n1 "${TMP}/pass.out")" == "OUTCOME: pass" ]] || fail "pass polarity does not end with OUTCOME: pass"
grep -q "1/2: ${FAKES}/pass_outcome.sh" "${TMP}/pass.out" || fail "gate 1 did not run in pass polarity"
grep -q "2/2: ${FAKES}/pass_silent.sh" "${TMP}/pass.out" || fail "gate 2 did not run in pass polarity"
grep -q "^outcome: pass$" "${TMP}/pass.out" || fail "gate outcome line missing in pass polarity"
grep -q "^outcome: none$" "${TMP}/pass.out" || fail "gate without an OUTCOME line must report none"
grep -qF "2/2 gates green" "${TMP}/pass.out" || fail "pass polarity summary missing"

# ---- 2) fail polarity: all gates run, first failure named ----
cat > "${TMP}/override-fail.txt" <<EOF
${FAKES}/pass_outcome.sh
${FAKES}/fail_gate.sh
${FAKES}/pass_silent.sh
EOF

FAIL_RC=0
run_bundle "${TMP}/override-fail.txt" >"${TMP}/fail.out" 2>"${TMP}/fail.err" || FAIL_RC=$?
[[ "$FAIL_RC" -eq 1 ]] || fail "fail polarity rc=${FAIL_RC}, want 1"
[[ "$(tail -n1 "${TMP}/fail.out")" == "OUTCOME: fail" ]] || fail "fail polarity does not end with OUTCOME: fail"
grep -q "1/3: ${FAKES}/pass_outcome.sh" "${TMP}/fail.out" || fail "pre-failure gate did not run"
grep -q "3/3: ${FAKES}/pass_silent.sh" "${TMP}/fail.out" || fail "gate after the failure did not run (all gates must run)"
grep -qF "first failing gate: ${FAKES}/fail_gate.sh" "${TMP}/fail.out" || fail "first failing gate not named"
grep -qF "full gate output: " "${TMP}/fail.out" || fail "failure did not print the kept log path"
LOG_PATH="$(grep -F 'full gate output: ' "${TMP}/fail.out" | head -n1 | sed 's/^.*full gate output: //')"
[[ -f "$LOG_PATH" ]] || fail "the named log file does not exist: ${LOG_PATH}"
grep -qF "fake gate boom: evidence line" "$LOG_PATH" || fail "the log does not carry the failing gate's output"

# ---- 3) first-failure naming with two failures ----
cat > "${TMP}/override-two-fails.txt" <<EOF
${FAKES}/fail_gate.sh
${FAKES}/fail_gate.sh
EOF

TWO_RC=0
run_bundle "${TMP}/override-two-fails.txt" >"${TMP}/two.out" 2>&1 || TWO_RC=$?
[[ "$TWO_RC" -eq 1 ]] || fail "two-failures rc=${TWO_RC}, want 1"
[[ "$(grep -cF '=== gate ' "${TMP}/two.out")" -eq 2 ]] || fail "two-failures did not run exactly two gates"
[[ "$(tail -n1 "${TMP}/two.out")" == "OUTCOME: fail" ]] || fail "two-failures does not end with OUTCOME: fail"
grep -q "first failing gate: ${FAKES}/fail_gate.sh" "${TMP}/two.out" || fail "two-failures first gate not named"

# ---- 4) usage tool errors ----
USAGE_RC=0
run_bundle "" --bogus-flag >"${TMP}/usage.out" 2>&1 || USAGE_RC=$?
[[ "$USAGE_RC" -eq 3 ]] || fail "unknown argument rc=${USAGE_RC}, want 3"
[[ "$(tail -n1 "${TMP}/usage.out")" == "OUTCOME: tool_error" ]] || fail "unknown argument does not end with OUTCOME: tool_error"

MISSING_RC=0
run_bundle "${TMP}/no-such-override-file.txt" >"${TMP}/missing.out" 2>&1 || MISSING_RC=$?
[[ "$MISSING_RC" -eq 3 ]] || fail "missing override file rc=${MISSING_RC}, want 3"
[[ "$(tail -n1 "${TMP}/missing.out")" == "OUTCOME: tool_error" ]] || fail "missing override file does not end with OUTCOME: tool_error"
grep -qF "no-such-override-file.txt" "${TMP}/missing.out" || fail "missing override error does not name the file"

# ---- 4b) empty effective override (only blank/comment lines) is a ----
# ----    usage-class tool error, never an empty gates array      ----
printf '# only a comment\n\n   \n' > "${TMP}/override-empty.txt"
EMPTY_RC=0
run_bundle "${TMP}/override-empty.txt" >"${TMP}/empty.out" 2>&1 || EMPTY_RC=$?
[[ "$EMPTY_RC" -eq 3 ]] || fail "empty override rc=${EMPTY_RC}, want 3"
[[ "$(tail -n1 "${TMP}/empty.out")" == "OUTCOME: tool_error" ]] || fail "empty override does not end with OUTCOME: tool_error"
grep -qF "yields no runnable gate command" "${TMP}/empty.out" || fail "empty override error does not name the reason"
grep -qF "override-empty.txt" "${TMP}/empty.out" || fail "empty override error does not name the file"
if grep -qF "unbound variable" "${TMP}/empty.out"; then
  fail "empty override still crashes on an unbound variable"
fi

# ---- 5) --help is a metadata exit ----
HELP_RC=0
run_bundle "" --help >"${TMP}/help.out" 2>&1 || HELP_RC=$?
[[ "$HELP_RC" -eq 0 ]] || fail "--help rc=${HELP_RC}, want 0"
grep -qF "RUN_PLAN_GATES_OVERRIDE" "${TMP}/help.out" || fail "--help does not document the override"
grep -qF "Gates, in order" "${TMP}/help.out" || fail "--help does not document the gate list"
if grep -q '^OUTCOME:' "${TMP}/help.out"; then
  fail "--help must not emit an OUTCOME line (metadata exit)"
fi

echo "selftest OK: run_plan_gates bundle (pass, fail, first-failure, usage, empty-override, help)"
