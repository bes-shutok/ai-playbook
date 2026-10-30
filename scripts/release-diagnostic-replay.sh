#!/usr/bin/env bash
# release-diagnostic-replay.sh - opt-in exact replay of a failed release
# privacy scan.
# Plan: docs/history/plans/2026-10-26-release-privacy-gate-diagnostics-and-replay.md
# (Task 2).
#
# Usage (the one-command invocation the rewrite's PRIVACY GATE DIAGNOSTICS
# block prints; run it from inside the release checkout):
#
#   bash scripts/release-diagnostic-replay.sh \
#     --source-tip <oid> \
#     --scanner <path> --scanner-sha256 <hex> \
#     --patterns <path> --patterns-sha256 <hex> \
#     --groups-sha256 <hex> \
#     --draft <path>
#
# Every check runs BEFORE any scanning: HEAD must equal the recorded source
# tip, the tracked worktree must be clean, the scanner and effective-pattern
# sources must match their recorded sha256 digests, and the release-group
# input serialized from the retained draft must match the recorded digest.
# Any mismatch refuses (exit 2, REPLAY REFUSED) without scanning. On valid
# inputs the helper scans the tracked regular blobs of the source tip plus
# the reconstructed release-groups file against the verified sources, saves
# the scanner's raw stdout to one mode-0600 file, and prints only the
# raw-output paths and the scanner outcome: matched content reaches only the
# 0600 file, never this transcript. The exit code is the scanner's own exit
# code (0 pass, 1 findings, 3 tool error); 2 is reserved for replay refusals.
set -euo pipefail

refuse() {
  printf 'release-diagnostic-replay: REPLAY REFUSED: %s\n' "$*" >&2
  exit 2
}

sha256_of() {
  shasum -a 256 < "$1" | cut -d' ' -f1
}

require_digest() {
  # $1 = flag name, $2 = recorded value.
  printf '%s' "$2" | grep -Eq '^[0-9a-f]{64}$' \
    || refuse "$1 is not a 64-character sha256 hex digest: $2"
}

# Argument parsing: the seven flags, each exactly once, each with a value.
source_tip=""
scanner=""
scanner_sha256=""
patterns=""
patterns_sha256=""
groups_sha256=""
draft=""
while [ "$#" -gt 0 ]; do
  flag="${1:-}"
  case "$flag" in
    --source-tip|--scanner|--scanner-sha256|--patterns|--patterns-sha256|--groups-sha256|--draft)
      [ "$#" -ge 2 ] || refuse "flag $flag requires a value"
      value="$2"
      case "$flag" in
        --source-tip)
          [ -z "$source_tip" ] || refuse "--source-tip is given more than once"
          source_tip="$value"
          ;;
        --scanner)
          [ -z "$scanner" ] || refuse "--scanner is given more than once"
          scanner="$value"
          ;;
        --scanner-sha256)
          [ -z "$scanner_sha256" ] || refuse "--scanner-sha256 is given more than once"
          scanner_sha256="$value"
          ;;
        --patterns)
          [ -z "$patterns" ] || refuse "--patterns is given more than once"
          patterns="$value"
          ;;
        --patterns-sha256)
          [ -z "$patterns_sha256" ] || refuse "--patterns-sha256 is given more than once"
          patterns_sha256="$value"
          ;;
        --groups-sha256)
          [ -z "$groups_sha256" ] || refuse "--groups-sha256 is given more than once"
          groups_sha256="$value"
          ;;
        --draft)
          [ -z "$draft" ] || refuse "--draft is given more than once"
          draft="$value"
          ;;
      esac
      shift 2
      ;;
    *)
      refuse "unknown argument: $flag"
      ;;
  esac
done
[ -n "$source_tip" ] || refuse "missing --source-tip"
[ -n "$scanner" ] || refuse "missing --scanner"
[ -n "$scanner_sha256" ] || refuse "missing --scanner-sha256"
[ -n "$patterns" ] || refuse "missing --patterns"
[ -n "$patterns_sha256" ] || refuse "missing --patterns-sha256"
[ -n "$groups_sha256" ] || refuse "missing --groups-sha256"
[ -n "$draft" ] || refuse "missing --draft"
require_digest "--scanner-sha256" "$scanner_sha256"
require_digest "--patterns-sha256" "$patterns_sha256"
require_digest "--groups-sha256" "$groups_sha256"

# The replay targets the checkout it runs inside: the tree identity gate
# proved the rewritten tip equals the source tip, so a clean tracked checkout
# at the source tip carries the exact scanned bytes without materializing the
# rewritten tree.
top="$(git rev-parse --show-toplevel 2>/dev/null)" \
  || refuse "not inside a git repository; run the replay from the release checkout"

# 1. HEAD equals the recorded source tip.
head_oid="$(git rev-parse HEAD 2>/dev/null)" || refuse "git rev-parse HEAD failed"
[ "$head_oid" = "$source_tip" ] \
  || refuse "HEAD ($head_oid) does not equal the recorded source tip ($source_tip); the scan inputs would not match the failed run"

# 2. The tracked worktree is clean (untracked scratch does not change any
#    tracked blob the scan reads).
dirty="$(git status --porcelain --untracked-files=no 2>/dev/null)" || refuse "git status failed"
[ -z "$dirty" ] \
  || refuse "the tracked worktree is not clean; the scan would read different bytes than the failed run"

# 3. The scanner source matches the recorded digest.
[ -f "$scanner" ] || refuse "the recorded scanner source is not a regular file: $scanner"
[ "$(sha256_of "$scanner")" = "$scanner_sha256" ] \
  || refuse "the scanner source does not match the recorded digest ($scanner_sha256): $scanner"

# 4. The effective-pattern source matches the recorded digest.
[ -f "$patterns" ] || refuse "the recorded effective-pattern source is not a regular file: $patterns"
[ "$(sha256_of "$patterns")" = "$patterns_sha256" ] \
  || refuse "the effective-pattern source does not match the recorded digest ($patterns_sha256): $patterns"

# 5. The retained draft still serializes to the recorded release-group
#    digest. The block is parsed exactly as release-authoring.sh parses it,
#    and the bytes are rebuilt exactly as release-authoring.sh writes the
#    groups file: the recorded source tip as the base line, then alternating
#    group/msg lines.
[ -f "$draft" ] || refuse "the retained draft is not a regular file: $draft"
block_seen=0
expect="group"
counts=()
msgs=()
while IFS= read -r line || [ -n "$line" ]; do
  if [ "$block_seen" -eq 0 ]; then
    if [ "$line" = "release-groups:" ]; then
      block_seen=1
    fi
    continue
  fi
  [ -n "$line" ] || continue
  case "$expect:$line" in
    group:group\ *)
      value="${line#group }"
      case "$value" in
        ''|*[!0-9]*) refuse "the draft's release-groups block carries a non-integer group count: $value" ;;
      esac
      [ "$value" -ge 1 ] 2>/dev/null || refuse "the draft's release-groups block carries a group count below 1: $value"
      counts+=("$value")
      expect="msg"
      ;;
    msg:msg\ *)
      value="${line#msg }"
      [ -n "$value" ] || refuse "the draft's release-groups block carries an empty group message"
      msgs+=("$value")
      expect="group"
      ;;
    *)
      refuse "the draft's release-groups block must alternate 'group <count>' and 'msg <subject>' lines; got: $line"
      ;;
  esac
done < "$draft"
[ "$block_seen" -eq 1 ] || refuse "the retained draft carries no release-groups: marker: $draft"
[ "$expect" = "group" ] || refuse "the draft's release-groups block ends with an unmatched 'group' line"
[ "${#counts[@]}" -ge 1 ] || refuse "the draft's release-groups block carries no groups"
[ "${#counts[@]}" -eq "${#msgs[@]}" ] || refuse "the draft's release-groups block group/msg pairs do not alternate"

replay_tmp="$(mktemp -d "${TMPDIR:-/tmp}/release-replay-XXXXXXXX")"
groups_installed=0
cleanup_replay() {
  # The reconstructed groups file is this helper's only working-tree
  # footprint; the raw output files live outside this dir and persist by
  # design (they are the requested artifact).
  if [ "$groups_installed" -eq 1 ]; then
    rm -f -- "$top/release-groups.txt" 2>/dev/null || true
  fi
  rm -rf -- "$replay_tmp" 2>/dev/null || true
  return 0
}
trap cleanup_replay EXIT

groups_serialized="$replay_tmp/release-groups.txt"
{
  printf 'base %s\n' "$source_tip"
  i=0
  while [ "$i" -lt "${#counts[@]}" ]; do
    printf 'group %s\n' "${counts[$i]}"
    printf 'msg %s\n' "${msgs[$i]}"
    i=$((i + 1))
  done
} > "$groups_serialized"
[ "$(sha256_of "$groups_serialized")" = "$groups_sha256" ] \
  || refuse "the release-group input serialized from the retained draft ($draft) does not match the recorded digest ($groups_sha256); the draft drifted from the failed run"

# Reconstruct the scanned groups file at the checkout root under the exact
# relative path the failed scan named; never overwrite an occupied path.
groups_target="$top/release-groups.txt"
if [ -e "$groups_target" ] || [ -L "$groups_target" ]; then
  refuse "the reconstruction path is occupied; remove it or move it aside first: $groups_target"
fi
cp "$groups_serialized" "$groups_target"
groups_installed=1

# Tracked regular blobs only, exactly as the failed scan enumerated them:
# symlinks (120000) and gitlinks (160000) carry no scannable blob content.
scan_call_paths=()
while IFS= read -r -d '' entry; do
  meta="${entry%%$'\t'*}"
  p="${entry#*$'\t'}"
  case "$meta" in
    100644*|100755*) ;;
    *) continue ;;
  esac
  [ -n "$p" ] || continue
  scan_call_paths+=("$p")
done < <(git ls-tree -r -z HEAD)
[ "${#scan_call_paths[@]}" -ge 1 ] || refuse "the source tip tree carries no tracked regular blobs; nothing to scan"
scan_call_paths+=("release-groups.txt")

# The replayed scan: raw stdout to a persisted mode-0600 file (mktemp creates
# 0600; the explicit chmod keeps the mode pinned), stderr to its own 0600
# copy so tool-error diagnostics survive without entering the transcript.
raw_out="$(mktemp "${TMPDIR:-/tmp}/release-replay-stdout-XXXXXXXX")"
raw_err="$(mktemp "${TMPDIR:-/tmp}/release-replay-stderr-XXXXXXXX")"
chmod 600 "$raw_out" "$raw_err"
scan_rc=0
PUBLIC_HYGIENE_REPO_ROOT="$top" PUBLIC_HYGIENE_PATTERNS_FILE="$patterns" \
  bash "$scanner" --files "${scan_call_paths[@]}" >"$raw_out" 2>"$raw_err" || scan_rc=$?
chmod 600 "$raw_out" "$raw_err"
outcome_row="$(grep '^OUTCOME: ' "$raw_out" | tail -n 1 || true)"
printf 'release-diagnostic-replay: raw scanner stdout: %s (mode 0600)\n' "$raw_out"
printf 'release-diagnostic-replay: scanner stderr copy: %s (mode 0600)\n' "$raw_err"
if [ -n "$outcome_row" ]; then
  printf 'release-diagnostic-replay: scanner outcome: %s (exit %s)\n' "${outcome_row#OUTCOME: }" "$scan_rc"
else
  printf 'release-diagnostic-replay: scanner outcome: none (exit %s)\n' "$scan_rc"
fi
exit "$scan_rc"
