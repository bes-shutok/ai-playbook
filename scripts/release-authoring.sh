#!/usr/bin/env bash
# release-authoring.sh - authoring mechanics of the release skill.
# Plan: docs/history/plans/2026-09-26-release-skill.md (Task 2).
#
# Usage (in the primary checkout, in the SAME shell invocation that later runs
# release-rewrite.sh):
#
#   eval "$(bash scripts/release-authoring.sh <drafted-section-file>)"
#   bash scripts/release-rewrite.sh "$GROUPS_FILE"
#
# The drafted section file carries the CHANGELOG markdown section first, then
# a single marker line "release-groups:", then alternating "group <count>" and
# "msg <subject>" lines (oldest group first). The counts tile the publish
# delta INCLUDING the notes commit this script creates: that commit is the
# newest one and folds into the last group.
#
# stdout: the acquired done-lock export lines (DONE_LOCK_DIR / DONE_LOCK_TOKEN)
# followed by a final "groups-file <path>" line naming the groups file written
# under the run temp dir. Every diagnostic goes to stderr. On any abort the
# CALLING shell releases the done lock with the exported values before exiting.
set -euo pipefail

lock_out=""
die() {
  # Any post-acquisition abort relays the acquired lock exports on stdout, so
  # the calling shell's eval captures them and can release the lock on every
  # exit path (the plan's SCRIPT I/O CONTRACT). Nothing else ever reaches
  # stdout, so the stream stays eval-able.
  if [ -n "$lock_out" ]; then
    printf '%s\n' "$lock_out"
  fi
  printf 'release-authoring: FATAL: %s\n' "$*" >&2
  exit 1
}

# Configuration keys (documented in agents/skills/release/SKILL.md):
#   DONE_LOCK_SCRIPT       done-lock implementation; default is the
#                          runtime-home deployment
#                          "${HOME}/.ai-playbook/scripts/done-lock.sh"
#   RELEASE_REMOTE         remote name (default: origin); every
#                          <remote>/main range expression below resolves
#                          through this key
#   RELEASE_LOCK_MAX_WAIT  seconds the short agent wait may poll (default: 60)
remote="${RELEASE_REMOTE:-origin}"
upstream="refs/remotes/${remote}/main"

[ "$#" -eq 1 ] || die "usage: release-authoring.sh <drafted-section-file>"
draft_in="$1"
draft_dir="$(dirname "$draft_in")"
draft="$(cd "$draft_dir" 2>/dev/null && pwd)/$(basename "$draft_in")"
[ -f "$draft" ] || die "drafted section file not found: $draft_in"

top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "not inside a git repository"
cd "$top"

today="$(date +%Y-%m-%d)"

# 1. Acquire the per-worktree done lock FIRST (label release-<date>), exactly
#    as done Step 0 does. Every later abort leaves the release to the calling
#    shell, which releases the lock with the exports this script prints.
lock_script="${DONE_LOCK_SCRIPT:-${HOME}/.ai-playbook/scripts/done-lock.sh}"
[ -f "$lock_script" ] || die "lock script not found (set DONE_LOCK_SCRIPT): $lock_script"
# Pin the lock holder to this script's INVOKING SHELL (the one-shot caller
# rule, done SKILL.md Step 0 Variant B): left unset, the lock script records
# its own PPID, which is this short-lived authoring process, so the real
# done-lock reads the hold as abandoned once its dead-holder grace period
# passes and a concurrent wait-acquire can steal it mid-run. The invoking
# shell lives through the rewrite and the publish step. An explicit caller
# pin to a longer-lived process wins.
export DONE_LOCK_HOLDER_PID="${DONE_LOCK_HOLDER_PID:-$PPID}"
lock_out="$("$lock_script" wait-acquire --label "release-$today" --max-wait "${RELEASE_LOCK_MAX_WAIT:-60}")" \
  || die "could not acquire the done lock"
case "$lock_out" in
  *"export DONE_LOCK_DIR="*) : ;;
  *) die "the lock script printed no DONE_LOCK exports" ;;
esac

# 2. Releases rewrite main only.
head_ref="$(git symbolic-ref HEAD 2>/dev/null)" || head_ref=""
[ "$head_ref" = "refs/heads/main" ] || die "refusing to release: HEAD is ${head_ref:-detached}, not refs/heads/main"

# 3. The user's uncommitted notes work is never committed by a release.
if [ -n "$(git status --porcelain -- CHANGELOG.md)" ]; then
  die "CHANGELOG.md carries uncommitted changes; commit or stash them first"
fi

# 4. Split the draft into the CHANGELOG section and the groups block.
#    The dash-separated template keeps the run dir inside the
#    release-authoring-* inventory pattern the rewrite step reports on.
run_tmp="$(mktemp -d "${TMPDIR:-/tmp}/release-authoring-XXXXXXXX")"
section_md="$run_tmp/section.md"
groups_md="$run_tmp/groups-block.txt"
awk '$0 == "release-groups:" { exit } { print }' "$draft" > "$section_md"
awk '$0 == "release-groups:" { seen = 1; next } seen { print }' "$draft" > "$groups_md"
[ -s "$section_md" ] || die "the draft carries no CHANGELOG section before the release-groups: marker"
[ -s "$groups_md" ] || die "the draft carries no release-groups: block"

counts_file="$run_tmp/counts.txt"
msgs_file="$run_tmp/msgs.txt"
: > "$counts_file"
: > "$msgs_file"
expect="group"
group_n=0
while IFS= read -r line || [ -n "$line" ]; do
  [ -n "$line" ] || continue
  case "$expect:$line" in
    group:group\ *)
      value="${line#group }"
      case "$value" in
        ''|*[!0-9]*) die "group count must be an integer, got: $value" ;;
      esac
      [ "$value" -ge 1 ] 2>/dev/null || die "group count must be at least 1, got: $value"
      printf '%s\n' "$value" >> "$counts_file"
      expect="msg"
      ;;
    msg:msg\ *)
      value="${line#msg }"
      [ -n "$value" ] || die "group message must not be empty"
      printf '%s\n' "$value" >> "$msgs_file"
      expect="group"
      group_n=$((group_n + 1))
      ;;
    *)
      die "groups block must alternate 'group <count>' and 'msg <subject>' lines; got: $line"
      ;;
  esac
done < "$groups_md"
[ "$expect" = "group" ] || die "the groups block ends with an unmatched 'group' line"
[ "$group_n" -ge 1 ] || die "the groups block carries no groups"

# 5. Em-dash ban on the drafted section BEFORE it touches CHANGELOG.md.
#    CHECK_NO_EM_DASH_ALL=1 scans the whole draft regardless of suffix, so a
#    draft saved without the .md suffix cannot bypass the pre-apply gate.
if ! CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file "$draft"; then
  die "the drafted section carries an em dash; fix the draft and re-run (CHANGELOG.md untouched)"
fi

# 6. Replace vs prepend by PUBLISH MEMBERSHIP: replace the today-section in
#    place only when its introducing notes commit lies inside the unpushed
#    range (this release lineage committed it, nothing was pushed); prepend
#    when the existing section is already reachable from the remote (or there
#    is none yet), so a same-day second release keeps its own notes.
changelog="$top/CHANGELOG.md"
mode="prepend"
if git rev-parse --verify --quiet "$upstream" >/dev/null 2>&1; then
  heading_line="+## $today"
  while IFS= read -r c; do
    [ -n "$c" ] || continue
    patch="$(git diff "${c}^" "$c" -- CHANGELOG.md 2>/dev/null)" || continue
    if printf '%s\n' "$patch" | grep -q "^+## ${today}\$"; then
      mode="replace"
      break
    fi
  done < <(git rev-list --reverse "$upstream..refs/heads/main" -- CHANGELOG.md)
fi

# A stale replace signal: detection saw a delta commit introduce the
# today-section, but a later delta commit removed or renamed that exact
# heading line, so the current CHANGELOG.md no longer carries it. The replace
# rewrite below would pass the file through unchanged and silently skip the
# notes commit; fall back to prepend mode instead, with a named note.
if [ "$mode" = "replace" ]; then
  if [ ! -f "$changelog" ] || ! grep -qxF "## $today" "$changelog"; then
    printf 'release-authoring: replace mode selected but the exact "## %s" heading is absent from CHANGELOG.md (a later delta commit removed or renamed it); falling back to prepend mode\n' "$today" >&2
    mode="prepend"
  fi
fi

new_changelog="$run_tmp/CHANGELOG.new"
if [ "$mode" = "replace" ]; then
  awk -v sec_file="$section_md" -v heading="## $today" '
    BEGIN { sec = ""; while ((getline l < sec_file) > 0) sec = sec l "\n" }
    !done && $0 == heading { printf "%s", sec; done = 1; insec = 1; next }
    insec && /^## / { insec = 0 }
    !insec { print }
  ' "$changelog" > "$new_changelog"
elif [ -f "$changelog" ]; then
  # Prepend above everything, but below a leading H1 title line when present.
  awk -v sec_file="$section_md" '
    BEGIN { sec = ""; while ((getline l < sec_file) > 0) sec = sec l "\n" }
    FNR == 1 {
      if ($0 ~ /^# /) { print; printf "%s", sec } else { printf "%s", sec; print }
      next
    }
    { print }
    END { if (NR == 0) printf "%s", sec }
  ' "$changelog" > "$new_changelog"
else
  cp "$section_md" "$new_changelog"
fi
mv "$new_changelog" "$changelog"

# 7. Whole-file em-dash scan, pass expected; restore the pre-run state and
#    abort otherwise (the file was clean at step 3, so this is lossless).
if ! bash scripts/check-no-em-dash.sh file "$changelog"; then
  if git cat-file -e "HEAD:CHANGELOG.md" 2>/dev/null; then
    git checkout -- CHANGELOG.md
  else
    rm -f "$changelog"
  fi
  die "CHANGELOG.md carries a pre-existing em dash outside the new section; file restored, nothing committed"
fi

# 8. Stage and commit ONLY the notes file (the pathspec commit leaves any
#    unrelated staged work staged); skip when the file equals HEAD.
git add -- CHANGELOG.md
if git diff --cached --quiet HEAD -- CHANGELOG.md; then
  printf 'release-authoring: CHANGELOG.md already matches HEAD; notes commit skipped\n' >&2
else
  git commit -q -m "changelog: release notes for $today" -- CHANGELOG.md
fi
base_tip="$(git rev-parse refs/heads/main)"

# 9. Write the groups file AFTER the notes commit; base is the post-notes tip
#    of main.
groups_out="$run_tmp/release-groups.txt"
{
  printf 'base %s\n' "$base_tip"
  awk 'NR == FNR { c[FNR] = $0; next } { printf "group %s\nmsg %s\n", c[FNR], $0 }' \
    "$counts_file" "$msgs_file"
} > "$groups_out"

# 10. Hand the lock exports and the groups file to the invoking shell. These
#     two stdout lines are the script's entire stdout contract.
printf '%s\n' "$lock_out"
printf 'groups-file %s\n' "$groups_out"
