#!/usr/bin/env bash
# Selftest for the acquire-wait holder diagnostic in done-lock.sh
# (backlog docs/history/backlog/2026-10-05-merge-lock-holder-visibility.md).
# Hermetic: every fixture lives in one mktemp tree, the lock roots are
# overridden through their documented environment overrides
# (DONE_LOCK_ROOT / MERGE_LOCK_ROOT), git is isolated from host config, and
# no default-root lock is ever touched. Assertions:
#   1. merge-wait-acquire blocked on a live holder names it on stderr
#      (`merge lock held: token=... label=... repo=... age=...s`), keeps
#      stdout export-free, and still exits 1 with `OUTCOME: fail`.
#   2. done wait-acquire blocked likewise names the holder (`done lock held: ...`).
#   3. The no-contention wait prints no holder lines at all.
#   4. A meta-less lock record produces the one unreadable-record line and
#      the documented ambiguous timeout outcome (exit 2, indeterminate).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCK_SCRIPT="${SCRIPT_DIR}/done-lock.sh"

fail() {
  echo "selftest FAIL: $1" >&2
  exit 1
}

TMP="$(mktemp -d "${TMPDIR:-/tmp}/done-lock-holder-visibility.XXXXXX")"
HOLDER_PIDS=""
cleanup() {
  local pid
  for pid in $HOLDER_PIDS; do
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
  done
  rm -rf "$TMP"
}
trap cleanup EXIT

REPO="${TMP}/repo"
mkdir -p "$REPO"
(
  cd "$REPO"
  export GIT_CONFIG_GLOBAL="${TMP}/git-config"
  export GIT_CONFIG_SYSTEM="${TMP}/git-config"
  git init -q
  git -c user.email=t@t -c user.name=t commit --allow-empty -qm init
)

DONE_ROOT="${TMP}/locks/done"
MERGE_ROOT="${TMP}/locks/merge"
mkdir -p "$DONE_ROOT" "$MERGE_ROOT"

# Long-lived fake holder: a plain background sleep started in THIS shell so
# its pid stays killable from the EXIT trap (no command substitution).
start_holder() {
  sleep 120 &
  HOLDER_PID="$!"
  HOLDER_PIDS="$HOLDER_PIDS $HOLDER_PID"
}

# Hermetic runners: roots overridden, git config pointed at the fixture,
# every other lock variable pinned so ambient host state cannot leak in.
run_done() {
  (
    cd "$REPO"
    export GIT_CONFIG_GLOBAL="${TMP}/git-config" GIT_CONFIG_SYSTEM="${TMP}/git-config"
    DONE_LOCK_ROOT="$DONE_ROOT" \
      DONE_LOCK_POLL_SECS="${DONE_LOCK_POLL_SECS-}" \
      DONE_LOCK_STALE_SECS="${DONE_LOCK_STALE_SECS-}" \
      DONE_LOCK_DEAD_HOLDER_GRACE_SECS="${DONE_LOCK_DEAD_HOLDER_GRACE_SECS-}" \
      DONE_LOCK_HOLDER_PID="${DONE_LOCK_HOLDER_PID-}" \
      DONE_LOCK_DIR="${DONE_LOCK_DIR-}" \
      DONE_LOCK_TOKEN="${DONE_LOCK_TOKEN-}" \
      bash "$LOCK_SCRIPT" "$@"
  )
}

run_merge() {
  (
    cd "$REPO"
    export GIT_CONFIG_GLOBAL="${TMP}/git-config" GIT_CONFIG_SYSTEM="${TMP}/git-config"
    MERGE_LOCK_ROOT="$MERGE_ROOT" \
      MERGE_LOCK_POLL_SECS="${MERGE_LOCK_POLL_SECS-}" \
      MERGE_LOCK_STALE_SECS="${MERGE_LOCK_STALE_SECS-}" \
      MERGE_LOCK_DEAD_HOLDER_GRACE_SECS="${MERGE_LOCK_DEAD_HOLDER_GRACE_SECS-}" \
      MERGE_LOCK_HOLDER_PID="${MERGE_LOCK_HOLDER_PID-}" \
      MERGE_LOCK_DIR="${MERGE_LOCK_DIR-}" \
      MERGE_LOCK_TOKEN="${MERGE_LOCK_TOKEN-}" \
      bash "$LOCK_SCRIPT" "$@"
  )
}

EXPECTED_REPO_ROOT="$(cd "$REPO" && pwd -P)"

# ---- 1) merge-wait-acquire names the merge holder ----
start_holder
MERGE_HOLDER="$HOLDER_PID"
eval "$(MERGE_LOCK_HOLDER_PID="$MERGE_HOLDER" run_merge merge-acquire --label visible-holder)"
[[ -n "${MERGE_LOCK_TOKEN:-}" ]] || fail "merge-acquire produced no token export"
MERGE_TOKEN="$MERGE_LOCK_TOKEN"

MERGE_WAIT_RC=0
MERGE_LOCK_DIR= MERGE_LOCK_TOKEN= MERGE_LOCK_HOLDER_PID= \
  MERGE_LOCK_POLL_SECS=1 \
  run_merge merge-wait-acquire --label blocked-waiter --max-wait 2 \
  >"${TMP}/merge-wait.out" 2>"${TMP}/merge-wait.err" || MERGE_WAIT_RC=$?

[[ "$MERGE_WAIT_RC" -eq 1 ]] || fail "merge-wait-acquire rc=${MERGE_WAIT_RC}, want 1 (documented timeout outcome over a live holder)"
[[ "$(tail -n1 "${TMP}/merge-wait.err")" == "OUTCOME: fail" ]] || fail "merge-wait-acquire stderr does not end with OUTCOME: fail"
[[ ! -s "${TMP}/merge-wait.out" ]] || fail "blocked merge-wait-acquire wrote to stdout (must stay export-free)"

HOLDER_LINES="$(grep -cE '^merge lock held: token=' "${TMP}/merge-wait.err" || true)"
[[ "$HOLDER_LINES" -ge 1 ]] || fail "no 'merge lock held:' line on stderr while blocked"
[[ "$HOLDER_LINES" -le 4 ]] || fail "holder line emitted unbounded times (${HOLDER_LINES})"

HOLDER_LINE="$(grep -E '^merge lock held: token=' "${TMP}/merge-wait.err" | head -n1)"
[[ "$HOLDER_LINE" == "merge lock held: token=${MERGE_TOKEN} label=visible-holder repo=${EXPECTED_REPO_ROOT} age="* ]] \
  || fail "holder line mismatch: ${HOLDER_LINE}"
HOLDER_AGE="$(printf '%s' "$HOLDER_LINE" | sed -E 's/.*age=([0-9]+s|unknown)$/\1/')"
[[ "$HOLDER_AGE" =~ ^([0-9]+s|unknown)$ ]] || fail "holder line age field malformed: ${HOLDER_LINE}"

# Free the merge leg before the next fixture (kill, then token release).
kill "$MERGE_HOLDER" 2>/dev/null || true
wait "$MERGE_HOLDER" 2>/dev/null || true
run_merge merge-release-repo >/dev/null 2>&1 || fail "merge leg release failed"

# ---- 2) done wait-acquire names the done holder ----
start_holder
DONE_HOLDER="$HOLDER_PID"
eval "$(DONE_LOCK_HOLDER_PID="$DONE_HOLDER" run_done acquire --label done-visible)"
[[ -n "${DONE_LOCK_TOKEN:-}" ]] || fail "done acquire produced no token export"
DONE_TOKEN="$DONE_LOCK_TOKEN"

DONE_WAIT_RC=0
DONE_LOCK_DIR= DONE_LOCK_TOKEN= DONE_LOCK_HOLDER_PID= \
  DONE_LOCK_POLL_SECS=1 \
  run_done wait-acquire --label done-waiter --max-wait 2 \
  >"${TMP}/done-wait.out" 2>"${TMP}/done-wait.err" || DONE_WAIT_RC=$?

[[ "$DONE_WAIT_RC" -eq 1 ]] || fail "done wait-acquire rc=${DONE_WAIT_RC}, want 1"
[[ "$(tail -n1 "${TMP}/done-wait.err")" == "OUTCOME: fail" ]] || fail "done wait-acquire stderr does not end with OUTCOME: fail"
[[ ! -s "${TMP}/done-wait.out" ]] || fail "blocked done wait-acquire wrote to stdout"
grep -qE "^done lock held: token=${DONE_TOKEN} label=done-visible repo=" "${TMP}/done-wait.err" \
  || fail "no 'done lock held:' line naming the done holder on stderr"

# Free the done leg so the next fixture starts from no lock at all.
kill "$DONE_HOLDER" 2>/dev/null || true
wait "$DONE_HOLDER" 2>/dev/null || true
run_done release-repo >/dev/null 2>&1 || fail "done leg release failed"

# ---- 3) the no-contention wait prints no holder lines ----
NOCONF_RC=0
DONE_LOCK_DIR= DONE_LOCK_TOKEN= DONE_LOCK_HOLDER_PID= \
  run_done wait-acquire --label uncontended --max-wait 5 \
  >"${TMP}/noconf.out" 2>"${TMP}/noconf.err" || NOCONF_RC=$?
[[ "$NOCONF_RC" -eq 0 ]] || fail "uncontended wait-acquire rc=${NOCONF_RC}, want 0"
if grep -qE '(lock held:|record unreadable)' "${TMP}/noconf.err"; then
  fail "uncontended wait printed holder diagnostics: $(cat "${TMP}/noconf.err")"
fi
grep -q '^export DONE_LOCK_DIR=' "${TMP}/noconf.out" || fail "uncontended wait printed no exports"
# Adopt the fresh exports before releasing (the shell still carries the
# previous leg's stale generation, and a stale token must not release).
eval "$(cat "${TMP}/noconf.out")"
run_done release-repo >/dev/null 2>&1 || fail "release of the uncontended wait's lock failed"

# ---- 4) unreadable holder record: one line, then the ambiguous timeout ----
REPO_ID="$(cd "$REPO" && printf '%s' "$(git rev-parse --show-toplevel)" | shasum -a 256 | cut -c1-16)"
METALESS_DIR="${DONE_ROOT}/${REPO_ID}"
rm -rf "$METALESS_DIR"
mkdir -p "$METALESS_DIR"
touch -t 202001010000 "$METALESS_DIR" 2>/dev/null \
  || touch -d '2020-01-01' "$METALESS_DIR" 2>/dev/null \
  || fail "cannot age the meta-less lock fixture"

UNREADABLE_RC=0
DONE_LOCK_DIR= DONE_LOCK_TOKEN= DONE_LOCK_HOLDER_PID= \
  DONE_LOCK_POLL_SECS=1 \
  run_done wait-acquire --label unreadable-waiter --max-wait 2 \
  >"${TMP}/unreadable.out" 2>"${TMP}/unreadable.err" || UNREADABLE_RC=$?

[[ "$UNREADABLE_RC" -eq 2 ]] || fail "unreadable-record wait rc=${UNREADABLE_RC}, want 2 (documented ambiguous timeout outcome)"
[[ "$(tail -n1 "${TMP}/unreadable.err")" == "OUTCOME: indeterminate" ]] \
  || fail "unreadable-record wait stderr does not end with OUTCOME: indeterminate"
UNREADABLE_COUNT="$(grep -cF 'lock holder record unreadable' "${TMP}/unreadable.err" || true)"
[[ "$UNREADABLE_COUNT" -eq 1 ]] || fail "unreadable-record line emitted ${UNREADABLE_COUNT} times, want exactly 1"
grep -qF "$METALESS_DIR" "${TMP}/unreadable.err" || fail "unreadable-record line does not name the lock dir"
[[ ! -s "${TMP}/unreadable.out" ]] || fail "unreadable-record wait wrote to stdout"

rm -rf "$METALESS_DIR"

echo "selftest OK: acquire-wait holder visibility (merge, done, uncontended, unreadable)"
