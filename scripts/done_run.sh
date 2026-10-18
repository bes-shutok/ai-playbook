#!/usr/bin/env bash
# done_run.sh - thin orchestrator composing the done closeout's mechanical
# steps. Subcommands: setup, commit, finalize. The runner adds no gate, no
# ledger, and no new refusal class: every
# refusal it prints is one of the composed commands' own named errors, or the
# relocated one-for-one setup refusals below (the empty-echo abort and the
# partial-setup classification stop), each moved verbatim from the done
# skill's Step 0 text.
#
# Usage:
#   done_run.sh setup [--label TEXT] [--from-manifest RUN_ID]
#        [--owned-plan PATH]... [--owned-review PATH]... [--owned-path PATH]...
#        [--foreign-review PATH]... [--foreign-review-from FILE] [--claim-none]
#   done_run.sh commit --stage PATH... --subject TEXT
#        [--learn-receipts-from FILE] [--revert-formatting PATH]...
#        [--side-commit REPO_PATH]... [--manifest PATH] [--run-id RUN_ID]
#   done_run.sh finalize [--manifest PATH] [--run-id RUN_ID]
#        [--from-holder] [--session IDENTITY] [--no-landing-cost]
#        [--guard-firing NAME:KIND:EVIDENCE[:NOTE]]...
#
# finalize composes the closeout's release ceremony: the resumable-closeout
# checkpoint refresh (a no-checkpoint refusal falls back to create-then-
# refresh; an already-finalized manifest skips the refresh arm), the run
# manifest finalize (a missing manifest is a one-line note; any other
# non-zero exit aborts after the releases, never masking the error), the
# checkpoint remove, the done-lock release (env-token path by default; with
# --from-holder, or when the exports are lost, the lock script's
# metadata-sourced release arm under its own recorded guards: the hold was
# pinned at acquire, the recorded hostname matches this host, the recorded
# holder is verifiably alive with exact identity, is not pid 1, and this
# shell descends from it - every refusal names the failed gate), the
# merge-lock release when a hold survives (exports when present, else the
# same from-holder arm), and the status-free verification. It then assembles
# the report inputs: the landing summary from the run's owned-commits ledger
# and the report-only missing-review-record scan over the archived plans
# (missing review records are reported, never blocking, never fabricated).
# The advisory appends run last, never blocking: one landing-cost telemetry
# line when this run landed work in the project repo (skip with --no-
# landing-cost or when nothing landed; a failed append is a warning line),
# and one guard-liveness ledger row per --guard-firing (a failed append is a
# warning line).
#
# setup composes, in order: the rearm-on-touch echo (advisory), the done-lock
# wait-acquire with the short agent wait (DONE_LOCK_AGENT_MAX_WAIT_SECS,
# default 90), the runtime-helper drift advisory (echo-and-continue), the
# worktree residue sweep (fail-open), the partial-setup classification (the
# sweep-gates lib's classify-run-boundary verdict at run identity: a terminal
# boundary continues to the fresh marker and manifest behind a one-line note,
# an unresolved orphan takes the verbatim refusal remedies, an unreadable
# record fails closed), the run-start marker write, and the run
# manifest write bound to that marker via --run-marker. On success it prints
# one status line on stdout followed by eval-able export lines for the
# downstream consumers: DONE_LOCK_DIR, DONE_LOCK_TOKEN, DONE_RUN_MARKER,
# DONE_RUN_MANIFEST, DONE_RUN_ID.
#
# commit owns the collapsed Step 3 (the plan's authoritative composed order):
# stage by explicit pathspec from the run's owned set (--stage, gitignored
# paths reported and never staged), append staged plans-root paths to the
# deliverables file, the stale-checkout adjudication (revert_set_classifier
# classify restores ancestor-blob debris outside the declared set, never
# staging it), the cached-diff guard (a declared staged path whose content
# equals an ancestor vintage is the relocated leaked-revert stop), the dirt
# regression gate, the staged-scope guard, the foreign-dirt disposition
# ladder (a manifest foreign claim aborts the landing; other unclaimed dirt
# is reported and left), the formatting-only candidate list (no revert
# without --revert-formatting), the unused-import pass (skip-note when no
# linter resolves; findings report-only), the lesson-scope audit when the
# lessons corpus is touched, the --learn-receipts-from ledger appends
# (post-hoc-from-receipt, before the sweep), the landing sweep over the
# final staged set, the docs-branch sync (the worktree migration precedes it
# in an ad-hoc worktree; the sync holds its own runner-owned merge-lock
# span; --boundary-class per-task skips the sync as a final-closeout leg and
# forwards the class to the landing sweep, whose per-task roster drops the
# primary-checkout inspection; the default final-closeout keeps today's
# behavior byte-identically; the sweep-gates runner's usage text is the
# canonical roster split), the registry digest arm, the reverse-squash
# check-staged, and
# exactly one landing commit with the owned-commits ledger append fused to
# it (git commit ... && git rev-parse HEAD >> ledger). That landing commit
# refuses an empty declared set over a non-empty staged index, naming every
# staged path as the foreign set, and keeps the clean-index skip (no staged
# changes; landing commit skipped). The base-branch
# immutability rule is reported as a warning line, never a refusal. The
# subcommand then walks the facts-resolved side repos (user-facts keys
# skills_repo_path and shared_docs_dir), reports dirty paths per repo, and
# executes one confirmed commit action per repo named by --side-commit,
# re-running the public-hygiene scan over each staged side-repo set before
# that repo's commit. When DONE_RUN_TRACE_FILE is set the subcommand appends
# one `stage <name>` line per composed stage, so a run's trace shows the
# order the plan fixes.
#
# Env: DONE_LOCK_SCRIPT overrides the lock script (default: this repo's
# scripts/done-lock.sh, then the deployed home copy); the sweep-gates lib is
# resolved from this repo's scripts/ then the deployed home copy. All other
# DONE_LOCK_* / MERGE_LOCK_* / DONE_SWEEP_* variables pass through to the
# composed commands unchanged; the one exception the runner composes itself
# is DONE_SWEEP_DECLARED_STAGE_PATHS, written by the commit subcommand for
# its own landing-sweep invocation only (the final declared set, one path
# per line; actively unset for the sweep subprocess when the declared set is
# empty), never passed through. DONE_RUN_LINTER overrides the unused-import
# linter (default: ruff resolved from PATH).
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_SCRIPTS="${HOME}/.ai-playbook/scripts"

resolve_helper() { # name -> prints path or nothing
  if [ -f "$SCRIPT_DIR/$1" ]; then printf '%s\n' "$SCRIPT_DIR/$1"
  elif [ -f "$HOME_SCRIPTS/$1" ]; then printf '%s\n' "$HOME_SCRIPTS/$1"; fi
}

fail_partial() { # step evidence
  echo "done Step 0 partial-setup: $1; $2; no manifest bound" >&2
  exit 1
}

# Compose the CWD repo's facts-resolved done-session directory; print nothing.
session_dir() {
  local repo_top tmp_dir
  repo_top="$(git rev-parse --show-toplevel 2>/dev/null)" || return 1
  tmp_dir="$(sed -n 's/^tmp_dir = ["'\'']\(.*\)["'\'']$/\1/p' \
    "$repo_top/.ai-playbook/facts.md" 2>/dev/null | head -n 1)"
  tmp_dir="${tmp_dir:-$repo_top/docs/tmp/}"
  case "$tmp_dir" in /*) ;; *) tmp_dir="$repo_top/$tmp_dir";; esac
  printf '%s\n' "${tmp_dir%/}/done-session"
}

# Content-confirm a marker against the CWD repo root (digest middle field).
marker_confirms() { # marker-path -> rc
  local repo_top digest recorded
  repo_top="$(git rev-parse --show-toplevel 2>/dev/null)" || return 1
  digest="$(printf '%s' "${repo_top%/}" | (shasum -a 256 2>/dev/null || sha256sum) | awk '{print $1}')"
  recorded="$(awk '{print $2}' "$1" 2>/dev/null)"
  [ -n "$digest" ] && [ "$recorded" = "$digest" ]
}

# Classify a found partial setup; print the remedy lines on stderr and, for
# an explicit --from-manifest re-entry, the audit exports on stdout.
# Read-only: writes nothing. The state verdict comes from the repo-local
# sweep-gates lib's classify-run-boundary subcommand (the canonical
# RunManifest parse plus the adopted-set orphan filter, read at run identity
# over every run-manifest-*.json record sharing the newest file's payload run
# id); bash holds no manifest state predicate of its own: a terminal verdict
# (finalized | adopted | dispositioned | shadow-closed) continues to the
# fresh boundary behind a one-line note, an orphan verdict takes the verbatim
# remedy refusals, and an unreadable record fails closed naming the file.
classify_partial() { # from_manifest(empty allowed)
  local session from_manifest newest_marker newest_manifest mid marker_name verdict
  session="$(session_dir)" || return 1
  from_manifest="$1"
  newest_marker=""
  for f in "$session"/run-start-*; do
    [ -f "$f" ] || continue
    if marker_confirms "$f"; then
      if [ -z "$newest_marker" ] || [ "$f" \> "$newest_marker" ]; then newest_marker="$f"; fi
    fi
  done
  newest_manifest=""
  for f in "$session"/run-manifest-*.json; do
    [ -f "$f" ] || continue
    if [ -z "$newest_manifest" ] || [ "$f" \> "$newest_manifest" ]; then newest_manifest="$f"; fi
  done
  if [ -z "$newest_marker" ] && [ -z "$newest_manifest" ]; then
    return 1  # fresh setup
  fi
  if [ -n "$newest_manifest" ]; then
    # The canonical classification owner: the verdict is read at run identity
    # through the lib's RunManifest parse and the adopted-set orphan filter.
    local lib class_out
    lib="$(resolve_helper done_sweep_gates_lib.py)"
    if [ -z "$lib" ]; then
      echo "done_run setup: no done_sweep_gates_lib.py resolved (repo-local scripts/ or deployed home); cannot classify: $(basename "$newest_manifest")" >&2
      exit 3
    fi
    class_out="$(python3 "$lib" classify-run-boundary --session-dir "$session" --manifest "$newest_manifest" 2>&1)" || {
      printf '%s\n' "$class_out" >&2
      echo "done_run setup: the manifest-state classifier failed; no new boundary written (fail-closed)" >&2
      exit 3
    }
    verdict="$(printf '%s\n' "$class_out" | sed -n 's/^verdict: //p')"
    mid="$(printf '%s\n' "$class_out" | sed -n 's/^run_id: //p')"
    marker_name="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("marker",""))' "$newest_manifest" 2>/dev/null)"
    if [ "$verdict" = "unreadable" ]; then
      echo "done_run setup: found an unparseable run manifest record: $(basename "$newest_manifest") (corrupt or schema-invalid; run_id unreadable)" >&2
      echo "done_run setup: no new boundary written (fail-closed; repair or remove the named record explicitly)" >&2
      exit 2
    fi
    case "$verdict" in
      finalized|adopted|dispositioned|shadow-closed)
        if [ -z "$from_manifest" ]; then
          echo "done_run setup: newest manifest run_id=$mid is $verdict (closed boundary); continuing with a fresh marker and manifest"
          return 1
        fi
        ;;
      orphan)
        ;;  # the unadopted-boundary remedies below, verbatim
      *)
        echo "done_run setup: unknown boundary verdict from the classifier: $verdict" >&2
        exit 3
        ;;
    esac
    if [ -n "$newest_marker" ] && [ "$marker_name" = "$(basename "$newest_marker")" ]; then
      echo "done_run setup: found an unadopted current-boundary manifest run_id=$mid bound to the newest content-confirmed marker" >&2
      echo "done_run setup: remedies: python3 scripts/done_sweep_gates_lib.py recover-manifest --run-id $mid | re-enter with --from-manifest $mid (adopt) | python3 scripts/done_sweep_gates_lib.py finalize-manifest --run-id $mid" >&2
    else
      echo "done_run setup: found a stale-marker or markerless interrupted manifest run_id=${mid:-unknown}" >&2
      echo "done_run setup: remedies: python3 scripts/done_sweep_gates_lib.py recover-manifest --run-id ${mid:-<id>} | adopt via --from-manifest ${mid:-<id>} | python3 scripts/done_sweep_gates_lib.py finalize-manifest --run-id ${mid:-<id>} | python3 scripts/done_sweep_gates_lib.py disposition-manifest --run-id ${mid:-<id>} (dead root only)" >&2
    fi
    if [ -n "$from_manifest" ]; then
      if [ "$from_manifest" != "$mid" ]; then
        echo "done_run setup: --from-manifest $from_manifest names no found boundary (found: ${mid:-none})" >&2
        exit 1
      fi
      RUN_MARKER_PATH=""
      [ -n "$newest_marker" ] && [ "$marker_name" = "$(basename "$newest_marker")" ] && RUN_MARKER_PATH="$newest_marker"
      echo "done_run setup: re-entering boundary run_id=$mid (explicit --from-manifest)"
      echo "export DONE_RUN_MANIFEST=$(printf '%q' "$newest_manifest")"
      echo "export DONE_RUN_ID=$mid"
      echo "export DONE_RUN_MARKER=$(printf '%q' "$RUN_MARKER_PATH")"
      return 0
    fi
    echo "done_run setup: no new boundary written (read-only classification; pass --from-manifest to re-enter explicitly)" >&2
    exit 2
  fi
  # Marker without manifest: the interrupted attempt died inside the marker
  # recipe or before the writer; the marker-boundary remedy is a fresh write
  # (the writer's --run-marker binding governs identity), so report and stop.
  echo "done_run setup: found a content-confirmed marker with no manifest (partial marker write)" >&2
  echo "done_run setup: remedy: re-run setup to write the manifest bound to that marker, or remove the marker to discard the attempt" >&2
  echo "done_run setup: no new boundary written" >&2
  exit 2
}

cmd_setup() {
  local label="" from_manifest=""
  shift # subcommand
  while [ $# -gt 0 ]; do
    case "$1" in
      --label) label="$2"; shift 2;;
      --from-manifest) from_manifest="$2"; shift 2;;
      --owned-plan|--owned-review|--owned-path|--foreign-review)
        WM_ARGS+=("$1" "$2"); shift 2;;
      --foreign-review-from|--adopt)
        WM_ARGS+=("$1" "$2"); shift 2;;
      --claim-none) WM_ARGS+=("$1"); shift;;
      *) echo "done_run setup: unknown argument: $1" >&2; exit 3;;
    esac
  done

  # 1. Rearm-on-touch echo (advisory, echo-and-continue).
  REARM="$(resolve_helper rearm_on_touch.py)"
  if [ -n "$REARM" ]; then
    REARM_OUT="$(python3 "$REARM" 2>&1 || true)"
    echo "done_run setup: rearm-on-touch (advisory): $(printf '%s' "$REARM_OUT" | head -n 1)"
  else
    echo "done_run setup: rearm-on-touch (advisory): helper not deployed; skipped"
  fi

  # 2. Done-lock wait-acquire with the short agent wait.
  LOCK_SCRIPT="${DONE_LOCK_SCRIPT:-$(resolve_helper done-lock.sh)}"
  if [ -z "$LOCK_SCRIPT" ]; then
    echo "done-lock: no lock script resolved (set DONE_LOCK_SCRIPT)" >&2
    exit 3
  fi
  LABEL="${label:-$(git branch --show-current 2>/dev/null || echo unknown-branch)}"
  MAX_WAIT="${DONE_LOCK_AGENT_MAX_WAIT_SECS:-90}"
  LOCK_ERR="$(mktemp)"
  if ! LOCK_EXPORTS="$(bash "$LOCK_SCRIPT" wait-acquire --label "$LABEL" --max-wait "$MAX_WAIT" 2>"$LOCK_ERR")"; then
    bash "$LOCK_SCRIPT" status >&2 || true
    echo "done-lock: acquire outcome: $(grep -E '^OUTCOME: ' "$LOCK_ERR" | tail -n1)" >&2
    case "$(grep -E '^OUTCOME: ' "$LOCK_ERR" | tail -n1)" in
      "OUTCOME: fail")
        echo "done-lock: blocked after ${MAX_WAIT}s; another done holds the lock" >&2
        echo "done-lock: if holder PID is dead or lock is stale, run: $LOCK_SCRIPT stale-clean" >&2 ;;
      "OUTCOME: indeterminate")
        echo "done-lock: holder state ambiguous; the hold cannot be adjudicated: report and stop (stale-clean stays the explicit operator escape only)" >&2 ;;
      *)
        echo "done-lock: lock tool error (outcome: $(grep -E '^OUTCOME: ' "$LOCK_ERR" | tail -n1)); fix the invocation or environment and re-derive from disk with status" >&2 ;;
    esac
    rm -f "$LOCK_ERR"
    exit 2
  fi
  grep -qx 'OUTCOME: pass' "$LOCK_ERR" || {
    echo "done-lock: acquire emitted no final OUTCOME: pass on stderr; treating as tool error" >&2
    rm -f "$LOCK_ERR"
    exit 2
  }
  rm -f "$LOCK_ERR"
  eval "$LOCK_EXPORTS"
  printf '%s\n' "$LOCK_EXPORTS"
  if [ -z "${DONE_LOCK_DIR:-}" ] || [ -z "${DONE_LOCK_TOKEN:-}" ]; then
    echo "done-lock: acquire succeeded without lock exports" >&2
    exit 1
  fi

  # 3. Runtime-helper drift advisory (echo-and-continue, once per run).
  DEPLOY="$(resolve_helper deploy_runtime_helpers.sh)"
  if [ -n "$DEPLOY" ]; then
    DRIFT_OUT="$(bash "$DEPLOY" --check 2>&1 || true)"
    if [ -n "$DRIFT_OUT" ]; then
      printf 'done_run setup: runtime-helper drift advisory (echo-and-continue):\n%s\n' "$DRIFT_OUT"
    else
      echo "done_run setup: runtime-helper drift advisory: no drift"
    fi
  fi

  # 4. Worktree residue sweep (fail-open, report-and-continue).
  SWEEP="$(resolve_helper worktree_closeout_migrate.py)"
  if [ -n "$SWEEP" ]; then
    PRIMARY="$(git worktree list --porcelain | sed -n 's/^worktree //p' | head -1)"
    SWEEP_OUT="$(python3 "$SWEEP" sweep --target "$PRIMARY" --apply 2>&1 || true)"
    printf 'done_run setup: residue sweep (fail-open): %s\n' "$(printf '%s' "$SWEEP_OUT" | grep -E '^(OUTCOME|verdict|sweep):' | tail -n 3)"
  fi

  # 5. Partial-setup classification (read-only unless --from-manifest).
  classify_partial "$from_manifest" && return 0

  # 6. Run-start marker (content-bearing recipe, moved verbatim).
  session="$(session_dir)" || { echo "done-run: cannot resolve the repo root" >&2; exit 3; }
  mkdir -p "$session"
  REPO_TOP="$(git rev-parse --show-toplevel)"
  MARKER="$session/run-start-$(date -u +%Y%m%dT%H%M%SZ)"
  REPO_HASH="$(printf '%s' "${REPO_TOP%/}" | (shasum -a 256 2>/dev/null || sha256sum) | awk '{print $1}')"
  printf '%s' "$REPO_HASH" | grep -qE '^[0-9a-f]{64}$' || \
    fail_partial "run-start marker" "sha256 tool missing or malformed digest"
  printf '%s\n' "$(date -u +%s) $REPO_HASH $$" > "$MARKER" || \
    fail_partial "run-start marker" "marker write failed"
  # Post-write location self-check (independent fresh parse).
  session_fresh="$(session_dir)" || session_fresh=""
  if [ "$session_fresh" != "$session" ]; then
    rm -f "$MARKER"
    fail_partial "run-start marker" "resolved path is not the expected done-session root; stray marker removed"
  fi

  # 7. Run manifest write bound to the marker (fail-atomic block).
  LIB="$(resolve_helper done_sweep_gates_lib.py)"
  if [ -z "$LIB" ]; then
    rm -f "$MARKER"
    fail_partial "run manifest" "no sweep-gates lib resolved (repo-local scripts/ or deployed home)"
  fi
  WM_OUT="$(python3 "$LIB" write-manifest --run-marker "$MARKER" ${WM_ARGS+"${WM_ARGS[@]}"} 2>&1)" || {
    rm -f "$MARKER"
    fail_partial "run manifest" "the writer refused: $(printf '%s' "$WM_OUT" | tail -n 3)"
  }
  printf '%s\n' "$WM_OUT"
  MANIFEST="$(printf '%s\n' "$WM_OUT" | sed -n 's/^manifest: //p')"
  RUN_ID="$(printf '%s\n' "$WM_OUT" | sed -n 's/^run_id: //p')"
  if [ -z "$MANIFEST" ] || [ -z "$RUN_ID" ]; then
    rm -f "$MARKER"
    fail_partial "run manifest" "writer left no manifest/run_id echo to capture"
  fi

  echo "done_run setup: ok run_id=$RUN_ID"
  echo "export DONE_LOCK_DIR=$(printf '%q' "$DONE_LOCK_DIR")"
  echo "export DONE_LOCK_TOKEN=$(printf '%q' "$DONE_LOCK_TOKEN")"
  echo "export DONE_RUN_MARKER=$(printf '%q' "$MARKER")"
  echo "export DONE_RUN_MANIFEST=$(printf '%q' "$MANIFEST")"
  echo "export DONE_RUN_ID=$RUN_ID"
}

# --- commit subcommand ------------------------------------------------------

trace_stage() { # name: one `stage <name>` line when DONE_RUN_TRACE_FILE is set
  if [ -n "${DONE_RUN_TRACE_FILE:-}" ]; then
    printf 'stage %s\n' "$1" >> "$DONE_RUN_TRACE_FILE"
  fi
  return 0
}

commit_die() { # rc message...: fail loud with the named evidence
  local rc="$1"
  shift
  echo "done_run commit: $*" >&2
  exit "$rc"
}

facts_toml_value() { # key -> value from the repo facts TOML block
  local repo_top key="$1"
  repo_top="$(git rev-parse --show-toplevel 2>/dev/null)" || return 1
  sed -En "/^${key} = [\"']/{s/^${key} = [\"'](.*)[\"']$/\\1/p;}" \
    "$repo_top/.ai-playbook/facts.md" 2>/dev/null | head -n 1
}

manifest_field() { # manifest field -> one value per line (list field)
  python3 -c 'import json,sys
values = json.load(open(sys.argv[1])).get(sys.argv[2]) or []
for value in values:
    print(value)' "$1" "$2" 2>/dev/null
}

manifest_scalar() { # manifest field -> the scalar value or empty
  python3 -c 'import json,sys
print(json.load(open(sys.argv[1])).get(sys.argv[2]) or "")' "$1" "$2" 2>/dev/null
}

resolve_manifest_path() { # explicit arg, then the setup export, then newest
  if [ -n "${COMMIT_MANIFEST:-}" ] && [ -f "$COMMIT_MANIFEST" ]; then
    printf '%s\n' "$COMMIT_MANIFEST"
    return 0
  fi
  if [ -n "${DONE_RUN_MANIFEST:-}" ] && [ -f "$DONE_RUN_MANIFEST" ]; then
    printf '%s\n' "$DONE_RUN_MANIFEST"
    return 0
  fi
  local session newest=""
  session="$(session_dir)" || return 1
  for f in "$session"/run-manifest-*.json; do
    [ -f "$f" ] || continue
    if [ -z "$newest" ] || [ "$f" \> "$newest" ]; then newest="$f"; fi
  done
  [ -n "$newest" ] && printf '%s\n' "$newest"
  return 0
}

resolve_run_id() { # --run-id arg, then the manifest, then the setup export
  local manifest
  if [ -n "${RUN_ID_ARG:-}" ]; then printf '%s\n' "$RUN_ID_ARG"; return 0; fi
  manifest="$(resolve_manifest_path)" || return 1
  if [ -n "$manifest" ] && [ -f "$manifest" ]; then
    manifest_scalar "$manifest" run_id
    return 0
  fi
  printf '%s\n' "${DONE_RUN_ID:-}"
}

remove_from_declared() { # path: drop one reverted path from DECLARED
  local path="$1" kept=()
  for p in ${DECLARED+"${DECLARED[@]}"}; do
    [ "$p" = "$path" ] || kept+=("$p")
  done
  DECLARED=()
  for p in ${kept+"${kept[@]}"}; do DECLARED+=("$p"); done
}

# Compose the declared-stage channel bytes from the current DECLARED set:
# one path per line, newline-terminated, on stdout. A DECLARED path
# containing a newline is excluded from the channel with the one warning
# line here (the sweep gate keeps its strict behavior for it); any non-zero
# exit is the caller's composition-failure arm (one warning line, then
# continue with the channel unset). Bookkeeping only: this never gates and
# never refuses.
compose_declared_channel() {
  local row
  for row in ${DECLARED+"${DECLARED[@]}"}; do
    case "$row" in
      *$'\n'*)
        echo "done_run commit: declared-stage channel: declared path containing a newline excluded (the sweep gate keeps its strict behavior for it): $row" >&2
        ;;
      *)
        printf '%s\n' "$row"
        ;;
    esac
  done
}

side_facts_value() { # key -> value from the user facts markdown table
  local user_facts="${DONE_SWEEP_USER_FACTS:-${HOME}/.ai-playbook/facts.md}"
  [ -f "$user_facts" ] || return 0
  awk -v key="$1" '
    $0 ~ ("^[|][ \t]*`" key "`[ \t]*[|]") {
      line = $0
      sub(/^[^|]*[|][^|]*[|]/, "", line)
      gsub(/`/, "", line)
      sub(/[|].*$/, "", line)
      gsub(/^[ \t]+|[ \t]+$/, "", line)
      print line
      exit
    }' "$user_facts"
}

cmd_commit() {
  local subject="" receipts_file="" path row
  STAGE_ARGS=(); REVERT_FMT_ARGS=(); SIDE_COMMIT_ARGS=()
  COMMIT_MANIFEST=""; RUN_ID_ARG=""; BOUNDARY_CLASS="final-closeout"
  shift # subcommand
  while [ $# -gt 0 ]; do
    case "$1" in
      --boundary-class) BOUNDARY_CLASS="$2"; shift 2;;
      --stage) STAGE_ARGS+=("$2"); shift 2;;
      --revert-formatting) REVERT_FMT_ARGS+=("$2"); shift 2;;
      --side-commit) SIDE_COMMIT_ARGS+=("$2"); shift 2;;
      --subject) subject="$2"; shift 2;;
      --learn-receipts-from) receipts_file="$2"; shift 2;;
      --manifest) COMMIT_MANIFEST="$2"; shift 2;;
      --run-id) RUN_ID_ARG="$2"; shift 2;;
      *) echo "done_run commit: unknown argument: $1" >&2; exit 3;;
    esac
  done
  [ -n "$subject" ] || commit_die 3 "a --subject is required (the why-first landing message)"

  local repo_top session plans_dir deliverables
  repo_top="$(git rev-parse --show-toplevel 2>/dev/null)" || \
    commit_die 3 "not inside a git repository"
  cd "$repo_top" || commit_die 3 "cannot enter the repository root"
  session="$(session_dir)" || commit_die 3 "cannot resolve the repo root"

  # 1. Stage by explicit pathspec from the run's owned set (the declared
  #    --stage paths). Gitignored paths are reported and never staged.
  #    The declared set partitions into three arms: worktree-existing or
  #    index-tracked paths ride the git add below; an already-staged
  #    deletion (worktree-absent, index-absent, HEAD-tracked) needs no
  #    staging operation; a path tracked nowhere refuses so a typo never
  #    silently vanishes from the declared set.
  trace_stage staging
  DECLARED=()
  STAGE_LIST=()
  for path in ${STAGE_ARGS+"${STAGE_ARGS[@]}"}; do
    if git check-ignore -q "$path"; then
      echo "done_run commit: gitignored path not staged (previously force-tracked; untrack it instead, never commit it here): $path" >&2
    elif [ ! -e "$path" ] && ! git ls-files -- "$path" | grep -qxF -- "$path"; then
      if git cat-file -e "HEAD:$path" 2>/dev/null; then
        echo "done_run commit: already-staged deletion, no staging operation needed: $path" >&2
        DECLARED+=("$path")
      else
        commit_die 3 "declared path is absent and not tracked: $path"
      fi
    else
      DECLARED+=("$path")
      STAGE_LIST+=("$path")
    fi
  done
  if [ "${#STAGE_LIST[@]}" -gt 0 ]; then
    git add -- ${STAGE_LIST+"${STAGE_LIST[@]}"} || \
      commit_die 3 "git add refused the declared pathspec; stage the surviving paths in their own invocation and re-run"
  fi

  # 2. Append staged plans-root paths to the deliverables file.
  trace_stage deliverables
  plans_dir="$(facts_toml_value plans_dir)"
  plans_dir="${plans_dir:-docs/history/plans/}"
  deliverables="$session/plan-deliverables.txt"
  for path in ${DECLARED+"${DECLARED[@]}"}; do
    # a worktree-absent declared path is a deletion, not a deliverable
    [ -e "$path" ] || continue
    case "$path" in
      "$plans_dir"*)
        case "$path" in
          "$plans_dir"completed/*) continue;;
        esac
        mkdir -p "$session"
        grep -qxF "$path" "$deliverables" 2>/dev/null || \
          printf '%s\n' "$path" >> "$deliverables"
        ;;
    esac
  done

  # 3. Stale-checkout adjudication over the non-declared tracked dirty set:
  #    ancestor-blob debris is restored from HEAD and reported, never staged.
  trace_stage stale-checkout-adjudication
  CLASSIFIER="$(resolve_helper revert_set_classifier.py)"
  [ -n "$CLASSIFIER" ] || commit_die 3 "no revert_set_classifier.py resolved (repo-local scripts/ or deployed home)"
  local tmpd
  tmpd="$(mktemp -d)" || commit_die 3 "no scratch directory available"
  if [ "${#DECLARED[@]}" -gt 0 ]; then
    printf '%s\n' ${DECLARED+"${DECLARED[@]}"} | sort > "$tmpd/declared"
  else
    : > "$tmpd/declared"
  fi
  git diff --name-only HEAD | sort > "$tmpd/dirty"
  comm -13 "$tmpd/declared" "$tmpd/dirty" > "$tmpd/nondecl"
  if [ -s "$tmpd/nondecl" ]; then
    CL_PATHS=()
    while IFS= read -r row; do
      [ -n "$row" ] && CL_PATHS+=(--path "$row")
    done < "$tmpd/nondecl"
    CL_RC=0
    CL_OUT="$(python3 "$CLASSIFIER" classify --repo "$repo_top" ${CL_PATHS+"${CL_PATHS[@]}"} 2>&1)" || CL_RC=$?
    case "$CL_RC" in
      0) ;;
      1)
        printf '%s\n' "$CL_OUT" | while IFS= read -r row; do
          case "$row" in
            "reversal: "*)
              rpath="$(printf '%s' "$row" | awk '{print $2}')"
              if git diff --cached --name-only HEAD | grep -qxF "$rpath"; then
                echo "done_run commit: stale-checkout adjudication: reversal path left (index state differs from HEAD; the staged-scope guard owns it when a declared set is present, and an empty declared set refuses before any landing commit): $rpath" >&2
              elif git checkout -- "$rpath" 2>/dev/null; then
                echo "done_run commit: stale-checkout adjudication: restored from HEAD, never staged: $rpath" >&2
              else
                echo "done_run commit: stale-checkout adjudication: reversal path reported (restore failed): $rpath" >&2
              fi
              ;;
          esac
        done
        ;;
      *)
        printf '%s\n' "$CL_OUT" >&2
        rm -rf "$tmpd"
        commit_die 2 "stale-checkout adjudication could not classify the non-declared dirty set (rc=$CL_RC)"
        ;;
    esac
  fi

  # 4. Cached-diff guard over the declared staged paths: a declared path
  #    whose staged content equals an ancestor vintage is a leaked revert
  #    (the relocated stop). Declared deletions are the set's own removals.
  trace_stage cached-diff-guard
  if [ "${#DECLARED[@]}" -gt 0 ]; then
    CD_PATHS=()
    for path in ${DECLARED+"${DECLARED[@]}"}; do CD_PATHS+=(--path "$path"); done
    CD_RC=0
    CD_OUT="$(python3 "$CLASSIFIER" classify --repo "$repo_top" ${CD_PATHS+"${CD_PATHS[@]}"} 2>&1)" || CD_RC=$?
    case "$CD_RC" in
      0) ;;
      1)
        LEAKED="$(printf '%s\n' "$CD_OUT" | grep '^reversal: ' | grep ' dirty state equals ancestor ' | awk '{print $2}')"
        if [ -n "$LEAKED" ]; then
          echo "done_run commit: cached-diff guard: a leaked revert is staged across: $(printf '%s' "$LEAKED" | tr '\n' ' ')" >&2
          echo "done_run commit: cached-diff guard: reset the leaked paths and restage only the intended edits, then re-run; nothing committed" >&2
          rm -rf "$tmpd"
          exit 1
        fi
        # Deliberate pass-through: a reversal naming a declared path whose
        # index entry is absent is the declared deletion itself, the set's
        # own removal, not a leaked revert; pin the passage so it does not
        # depend on the classifier's message wording.
        for path in ${DECLARED+"${DECLARED[@]}"}; do
          if ! git ls-files -- "$path" | grep -qxF -- "$path" && \
             printf '%s\n' "$CD_OUT" | grep '^reversal: ' | awk '{print $2}' | grep -qxF -- "$path"; then
            echo "done_run commit: cached-diff guard: declared deletion is the set's own removal: $path" >&2
          fi
        done
        ;;
      *)
        printf '%s\n' "$CD_OUT" >&2
        rm -rf "$tmpd"
        commit_die "$CD_RC" "cached-diff guard: the revert-set classifier could not answer (rc=$CD_RC)"
        ;;
    esac
  fi

  # 5. Dirt regression gate over the declared HEAD-tracked paths. A
  #    worktree-absent declared path (the set's own removal) is skipped:
  #    the declaration discharges the accidental-reversion hypothesis for
  #    it; existing paths gate exactly as before.
  trace_stage dirt-regression-guard
  DIRT_GATE="$(resolve_helper dirt_regression_gate.py)"
  BASE_REF=""
  BASE_REF="$(facts_toml_value base_branch)"
  if [ -z "$BASE_REF" ]; then
    BASE_REF="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || true)"
  fi
  DIRT_PATHS=()
  for path in ${DECLARED+"${DECLARED[@]}"}; do
    [ -e "$path" ] || continue
    git cat-file -e "HEAD:$path" 2>/dev/null && DIRT_PATHS+=("$path")
  done
  if [ "${#DIRT_PATHS[@]}" -gt 0 ]; then
    if [ -z "$BASE_REF" ]; then
      echo "done_run commit: dirt regression gate: no default branch resolved; skipped"
    elif [ -z "$DIRT_GATE" ]; then
      echo "done_run commit: dirt regression gate: no dirt_regression_gate.py resolved; skipped" >&2
    else
      BASE_SHA="$(git merge-base HEAD "$BASE_REF" 2>/dev/null || true)"
      if [ -z "$BASE_SHA" ]; then
        echo "done_run commit: dirt regression gate: base $BASE_REF does not merge-base against HEAD; skipped" >&2
      else
        DG_RC=0
        DG_OUT="$(python3 "$DIRT_GATE" --base "$BASE_SHA" -- ${DIRT_PATHS+"${DIRT_PATHS[@]}"} 2>&1)" || DG_RC=$?
        printf '%s\n' "$DG_OUT"
        if [ "$DG_RC" -ne 0 ]; then
          rm -rf "$tmpd"
          commit_die "$DG_RC" "dirt regression guard refused the staging pass (rc=$DG_RC); nothing committed"
        fi
      fi
    fi
  fi

  # 6. Staged-scope guard over the declared set before the commit.
  trace_stage staged-scope-guard
  SCOPE_GUARD="$(resolve_helper staged_scope_guard.py)"
  if [ "${#DECLARED[@]}" -gt 0 ]; then
    if [ -z "$SCOPE_GUARD" ]; then
      rm -rf "$tmpd"
      commit_die 2 "staged-scope guard: no resolvable copy (repo-local scripts/ and the deployed runtime home were both searched); the commit path stops until a resolvable copy exists"
    fi
    SG_ARGS=()
    for path in ${DECLARED+"${DECLARED[@]}"}; do SG_ARGS+=(--include "$path"); done
    SG_RC=0
    SG_OUT="$(python3 "$SCOPE_GUARD" ${SG_ARGS+"${SG_ARGS[@]}"} 2>&1)" || SG_RC=$?
    printf '%s\n' "$SG_OUT"
    if [ "$SG_RC" -ne 0 ]; then
      rm -rf "$tmpd"
      commit_die "$SG_RC" "staged-scope guard refused the declared set (rc=$SG_RC); unstage the named entries or widen the declared set deliberately; nothing committed"
    fi
  fi

  # 7. Foreign-dirt disposition ladder over the remaining dirty paths: a
  #    manifest foreign claim is a live peer's work and aborts the landing;
  #    other unclaimed dirt is reported and left unstaged.
  trace_stage foreign-dirt-ladder
  FOREIGN_CLAIMS="$(mktemp)" || commit_die 3 "no scratch file available"
  RUN_MANIFEST="$(resolve_manifest_path)" || RUN_MANIFEST=""
  if [ -n "$RUN_MANIFEST" ] && [ -f "$RUN_MANIFEST" ]; then
    manifest_field "$RUN_MANIFEST" foreign_review_paths >> "$FOREIGN_CLAIMS"
  fi
  git ls-files --others --exclude-standard | sort > "$tmpd/untracked"
  comm -13 "$tmpd/declared" "$tmpd/untracked" > "$tmpd/untracked-foreign"
  sort -u "$tmpd/nondecl" "$tmpd/untracked-foreign" | comm -13 "$tmpd/declared" - > "$tmpd/remaining"
  PEER_ABORT=""; REPORTED=""
  while IFS= read -r row; do
    [ -n "$row" ] || continue
    if grep -qxF "$row" "$FOREIGN_CLAIMS"; then
      PEER_ABORT="$PEER_ABORT $row"
    else
      REPORTED="$REPORTED $row"
    fi
  done < "$tmpd/remaining"
  rm -f "$FOREIGN_CLAIMS"
  if [ -n "$PEER_ABORT" ]; then
    rm -rf "$tmpd"
    commit_die 1 "foreign-dirt gate: uncommitted work attributable to a live peer session; the landing aborts:$PEER_ABORT (waiting is futile while this run holds the done lock the peer's own landing would need)"
  fi
  if [ -n "$REPORTED" ]; then
    echo "done_run commit: foreign-dirt gate: unclaimed baseline dirt reported and left unstaged:$REPORTED" >&2
  fi

  # 8. Formatting-only diff candidates: listed for one-line confirmation;
  #    no revert without the --revert-formatting flag.
  trace_stage formatting-candidates
  FMT_CANDIDATES=()
  for path in ${DECLARED+"${DECLARED[@]}"}; do
    [ -f "$path" ] || continue
    FULL_DIFF="$(git diff HEAD -- "$path")"
    [ -n "$FULL_DIFF" ] || continue
    CORE_DIFF="$(git diff HEAD --ignore-all-space --ignore-blank-lines -- "$path")"
    if [ -z "$CORE_DIFF" ]; then FMT_CANDIDATES+=("$path"); fi
  done
  if [ "${#FMT_CANDIDATES[@]}" -gt 0 ]; then
    echo "done_run commit: formatting-only diff candidate(s), revert list needs one-line confirmation via --revert-formatting (no revert without it): ${FMT_CANDIDATES[*]}"
  fi
  for path in ${REVERT_FMT_ARGS+"${REVERT_FMT_ARGS[@]}"}; do
    IS_CANDIDATE=""
    for candidate in ${FMT_CANDIDATES+"${FMT_CANDIDATES[@]}"}; do
      [ "$candidate" = "$path" ] && IS_CANDIDATE=1
    done
    if [ -z "$IS_CANDIDATE" ]; then
      rm -rf "$tmpd"
      commit_die 3 "--revert-formatting names a path that is not a formatting-only candidate: $path"
    fi
    git checkout HEAD -- "$path" || { rm -rf "$tmpd"; commit_die 3 "revert failed for $path"; }
    remove_from_declared "$path"
    echo "done_run commit: formatting-only diff reverted after confirmation: $path"
  done

  # 9. Unused-import pass over touched lintable paths (report-only).
  trace_stage unused-import-pass
  LINTER="${DONE_RUN_LINTER:-ruff}"
  if ! command -v "$LINTER" >/dev/null 2>&1; then
    echo "done_run commit: unused-import pass: no linter resolved; skipped"
  else
    LINT_PATHS=()
    for path in ${DECLARED+"${DECLARED[@]}"}; do
      case "$path" in
        *.py) [ -f "$path" ] && LINT_PATHS+=("$path");;
      esac
    done
    if [ "${#LINT_PATHS[@]}" -eq 0 ]; then
      echo "done_run commit: unused-import pass: no lintable touched paths; skipped"
    else
      LINT_OUT="$("$LINTER" check --no-fix --select F401 -- ${LINT_PATHS+"${LINT_PATHS[@]}"} 2>&1 || true)"
      if [ -n "$LINT_OUT" ]; then
        printf 'done_run commit: unused-import pass findings (report-only; fix before staging):\n%s\n' "$LINT_OUT" >&2
      else
        echo "done_run commit: unused-import pass: clean"
      fi
    fi
  fi

  # 10. Lesson-scope audit when the lessons corpus is touched.
  trace_stage lesson-scope-audit
  CORPUS_REL="docs/maintenance/development_lessons.md"
  DRIFT_WITNESS=""
  STAGED_NOW="$(git diff --cached --name-only HEAD)"
  if printf '%s\n' "$STAGED_NOW" | grep -qxF "$CORPUS_REL"; then
    CPR="$(facts_toml_value company_projects_root)"
    CGM="$(facts_toml_value company_guidelines_master)"
    if [ -z "$CPR" ] || [ -z "$CGM" ]; then
      echo "done_run commit: lesson-scope audit: company master out of scope for this repo; duplicate check skipped"
    else
      UNDER_ROOT=""
      case "$repo_top" in
        "$CPR"|"$CPR"/*) UNDER_ROOT=1;;
      esac
      if [ -z "$UNDER_ROOT" ]; then
        echo "done_run commit: lesson-scope audit: company master out of scope for this repo; duplicate check skipped"
      elif [ ! -f "$CGM" ]; then
        echo "done_run commit: lesson-scope audit: WARNING: config drift: company guidelines master not found; company duplicate audit not run" >&2
        DRIFT_WITNESS="lesson-scope-audit: config drift: company guidelines master not found; company duplicate audit not run"
      else
        VALIDATOR="${LESSON_SCOPE_SCRIPT:-$(resolve_helper check_lesson_scope.py)}"
        if [ -z "$VALIDATOR" ] || [ ! -f "$VALIDATOR" ]; then
          echo "done_run commit: lesson-scope audit: lesson scope validator absent; mechanical duplicate check skipped (cold-start)" >&2
        else
          LS_RC=0
          LS_OUT="$(python3 "$VALIDATOR" "$repo_top/$CORPUS_REL" "$CGM" 2>&1)" || LS_RC=$?
          printf '%s\n' "$LS_OUT"
          if [ "$LS_RC" -eq 1 ] && printf '%s' "$LS_OUT" | grep -q '^DUPLICATE:'; then
            rm -rf "$tmpd"
            commit_die 1 "lesson-scope audit: a full rule is duplicated across the project corpus and the company master; stop before commit and ask the user to classify the lesson"
          elif [ "$LS_RC" -ne 0 ]; then
            rm -rf "$tmpd"
            commit_die 2 "lesson-scope audit: validator tool failure (rc=$LS_RC); do not stage the corpus"
          fi
        fi
      fi
    fi
    echo "done_run commit: lesson-scope audit: placement receipts remain the agent confirmation duty (owned by the learn skill placement receipts duty)"
  fi

  # 11. Learn receipts: post-hoc-from-receipt ledger appends, before the
  #     in-script landing re-run, so the sweep's doc-registry gate sees them.
  if [ -n "$receipts_file" ]; then
    trace_stage learn-receipts
    [ -f "$receipts_file" ] || { rm -rf "$tmpd"; commit_die 3 "learn receipts file not readable: $receipts_file"; }
    RUN_ID="$(resolve_run_id)"
    if [ -z "$RUN_ID" ]; then
      echo "done_run commit: learn receipts skipped (no run manifest from Step 0; no ledger path)"
    else
      LEDGER_PATH="$session/owned-commits-$RUN_ID.txt"
      mkdir -p "$session"
      while IFS= read -r row; do
        sha="$(printf '%s' "$row" | grep -oE '[0-9a-fA-F]{40}' | head -n 1)"
        [ -n "$sha" ] || continue
        if git rev-parse -q --verify "$sha^{commit}" >/dev/null 2>&1; then
          printf '%s\n' "$sha" >> "$LEDGER_PATH"
        else
          echo "done_run commit: learn receipt skip (not resolvable in this repository): $sha"
        fi
      done < "$receipts_file"
    fi
  fi

  # 12. The landing sweep over the final staged set: the closeout's one
  #     run. Immediately before the invocation, the declared-stage channel
  #     is composed from the final DECLARED set (the step-8 formatting
  #     revert has resolved it) and rides this one sweep invocation only.
  trace_stage landing-sweep
  SWEEP="$(resolve_helper done_sweep_gates.sh)"
  [ -n "$SWEEP" ] || { rm -rf "$tmpd"; commit_die 3 "no done_sweep_gates.sh resolved (repo-local scripts/ or deployed home)"; }
  # Declared-stage channel composition (bookkeeping in the commit flow,
  # never gates and never refuses): one final DECLARED path per line,
  # newline-terminated, handed to the sweep subprocess below and to nothing
  # else. A declared path containing a newline is excluded from the channel
  # with the composer's one warning line (the gate keeps its strict
  # behavior for it); a composition failure prints the one warning line
  # here and continues with the channel unset.
  SWEEP_CHANNEL="$(compose_declared_channel)" || {
    echo "done_run commit: declared-stage channel composition failed; continuing with the channel unset" >&2
    SWEEP_CHANNEL=""
  }
  SWEEP_RC=0
  if [ -n "$SWEEP_CHANNEL" ]; then
    SWEEP_OUT="$(DONE_SWEEP_DECLARED_STAGE_PATHS="$SWEEP_CHANNEL" bash "$SWEEP" landing --boundary-class "$BOUNDARY_CLASS" 2>&1)" || SWEEP_RC=$?
  else
    # empty declared set: actively unset the variable for the sweep
    # subprocess rather than skipping the assignment, so no ambient export
    # can leak into a channel-free sweep
    SWEEP_OUT="$(env -u DONE_SWEEP_DECLARED_STAGE_PATHS bash "$SWEEP" landing --boundary-class "$BOUNDARY_CLASS" 2>&1)" || SWEEP_RC=$?
  fi
  printf '%s\n' "$SWEEP_OUT"
  if [ "$SWEEP_RC" -ne 0 ]; then
    rm -rf "$tmpd"
    commit_die "$SWEEP_RC" "the landing sweep refused the staged set (rc=$SWEEP_RC); nothing committed"
  fi

  # 13. The docs-branch sync at its today position; the migration precedes it
  #     when this session runs in an ad-hoc worktree. Both mutating runners
  #     hold their own repository-keyed merge lock inside their own process.
  trace_stage docs-sync
  PRIMARY="$(git worktree list --porcelain | sed -n 's/^worktree //p' | head -n 1)"
  if [ -n "$PRIMARY" ] && [ "$repo_top" != "$PRIMARY" ]; then
    MIGRATE="$(resolve_helper worktree_closeout_migrate.py)"
    if [ -n "$MIGRATE" ]; then
      echo "done_run commit: ad-hoc worktree: migrating review staging docs and session logs to the main checkout before the sync"
      RUN_ID_MIG="$(resolve_run_id)"
      MIG_MANIFEST="$session/worktree-migrate-manifest-${RUN_ID_MIG:-adhoc}.json"
      MIG_BASELINE="$session/worktree-migrate-baseline-${RUN_ID_MIG:-adhoc}.json"
      mkdir -p "$session"
      MG_RC=0
      MG_OUT="$(python3 "$MIGRATE" capture --out "$MIG_BASELINE" 2>&1)" || MG_RC=$?
      if [ "$MG_RC" -eq 0 ]; then
        MG_OUT="$(python3 "$MIGRATE" migrate --baseline "$MIG_BASELINE" --source "$repo_top" --target "$PRIMARY" --manifest "$MIG_MANIFEST" 2>&1)" || MG_RC=$?
      fi
      printf '%s\n' "$MG_OUT"
      if [ "$MG_RC" -ne 0 ]; then
        rm -rf "$tmpd"
        commit_die 2 "the worktree migration refused (rc=$MG_RC); resolve what it named before the sync; nothing committed"
      fi
    fi
  fi
  if [ "$BOUNDARY_CLASS" = "per-task" ]; then
    # per-task boundary: the docs-branch sync is a final-closeout leg (the
    # boundary-class split, plan worktree-done-boundary-gate-roster-split);
    # the review-artifact migration above kept its position, and one trace
    # line names the skipped leg so the skip stays visible in the run record
    trace_stage docs-sync-skip
    echo "done_run commit: per-task boundary: skipping the docs-branch sync (a final-closeout leg; the run's final closeout owns the publication)"
  else
    SYNC="$(resolve_helper docs_branch_sync.sh)"
    [ -n "$SYNC" ] || { rm -rf "$tmpd"; commit_die 3 "no docs_branch_sync.sh resolved (repo-local scripts/ or deployed home)"; }
    SYNC_RC=0
    SYNC_OUT="$(bash "$SYNC" 2>&1)" || SYNC_RC=$?
    printf '%s\n' "$SYNC_OUT"
    if [ "$SYNC_RC" -ne 0 ]; then
      rm -rf "$tmpd"
      commit_die "$SYNC_RC" "the docs-branch sync refused (rc=$SYNC_RC); nothing committed"
    fi
  fi

  # 14. Registry digest-capture arm: the working-tree registry bytes must
  #     still hash to the staged blob immediately before the commit.
  trace_stage registry-digest-arms
  REGISTRY_REL="docs/maintenance/document-registry.md"
  if printf '%s\n' "$STAGED_NOW" | grep -qxF "$REGISTRY_REL"; then
    STAGED_BLOB="$(git ls-files -s -- "$REGISTRY_REL" | awk '{print $2}')"
    WORK_BLOB="$(git hash-object "$REGISTRY_REL")"
    if [ "$STAGED_BLOB" != "$WORK_BLOB" ]; then
      rm -rf "$tmpd"
      commit_die 1 "registry digest arm: working-tree bytes diverge from the staged blob; a write landed after staging: re-read the file, re-apply this session's rows, re-stage, and re-run the commit"
    fi
    echo "done_run commit: registry digest arm: staged blob matches the working-tree bytes"
  fi

  # 15. Reverse-squash check-staged: its today observation point, immediately
  #     before the landing commit.
  trace_stage reverse-squash-check-staged
  RS_GUARD="$(resolve_helper reverse_squash_guard.py)"
  if [ -n "$RS_GUARD" ]; then
    RS_RC=0
    RS_OUT="$(python3 "$RS_GUARD" check-staged --repo "$repo_top" 2>&1)" || RS_RC=$?
    printf '%s\n' "$RS_OUT"
    case "$RS_RC" in
      0) ;;
      1) rm -rf "$tmpd"; commit_die 1 "reverse-squash guard refused the staged set; unstage the refused set and rebuild it from the intended edits; nothing committed" ;;
      *) rm -rf "$tmpd"; commit_die "$RS_RC" "reverse-squash guard tool failure (rc=$RS_RC)" ;;
    esac
  else
    echo "done_run commit: reverse-squash guard absent; check skipped"
  fi

  # 16. Exactly one landing commit carrying work plus lessons, with the
  #     owned-commits ledger append fused to it; base-branch immutability is
  #     a warning line, never a refusal. An empty declared set over a
  #     non-empty staged index refuses before the construction: with no
  #     trailing pathspec Git reads `git commit --` as commit-the-whole-
  #     index, so every staged path is foreign and nothing may land.
  trace_stage landing-commit
  STAGED_NOW="$(git diff --cached --name-only HEAD)"
  if [ -z "$STAGED_NOW" ]; then
    echo "done_run commit: no staged changes; landing commit skipped"
  elif [ "${#DECLARED[@]}" -eq 0 ]; then
    FOREIGN_SET="$(printf '%s\n' "$STAGED_NOW" | tr '\n' ' ')"
    rm -rf "$tmpd"
    commit_die 1 "landing commit refuses an empty declared set over a non-empty staged index; every staged path is foreign: $FOREIGN_SET; re-run with the set declared via --stage or unstage the foreign entries; nothing committed"
  else
    BRANCH="$(git branch --show-current)"
    STORY_KEY="$(printf '%s' "$BRANCH" | grep -oE '[A-Z][A-Z0-9]*-[0-9][0-9]*' | head -n 1)"
    FULL_SUBJECT="$subject"
    if [ -n "$STORY_KEY" ]; then FULL_SUBJECT="[$STORY_KEY] $subject"; fi
    echo "done_run commit: base-branch immutability: a commit reachable from the base branch is never amended; corrections land as additive follow-up commits (warning line, never a refusal)" >&2
    LEDGER_PATH=""
    RUN_ID="$(resolve_run_id)"
    if [ -n "$RUN_ID" ]; then
      LEDGER_PATH="$session/owned-commits-$RUN_ID.txt"
      mkdir -p "$session"
    else
      echo "done_run commit: owned-commits ledger skipped (no run manifest from Step 0)"
    fi
    COMMIT_ARGS=(-m "$FULL_SUBJECT")
    if [ -n "$DRIFT_WITNESS" ]; then COMMIT_ARGS+=(-m "$DRIFT_WITNESS"); fi
    COMMIT_ARGS+=(-- ${DECLARED+"${DECLARED[@]}"})
    COMMIT_OK=0
    if [ -n "$LEDGER_PATH" ]; then
      git commit "${COMMIT_ARGS[@]}" && git rev-parse HEAD >> "$LEDGER_PATH" || COMMIT_OK=1
    else
      git commit "${COMMIT_ARGS[@]}" || COMMIT_OK=1
    fi
    if [ "$COMMIT_OK" -ne 0 ]; then
      rm -rf "$tmpd"
      commit_die 1 "the landing commit refused; nothing appended to the owned-commits ledger"
    fi
    echo "done_run commit: landed $(git rev-parse HEAD)"
  fi

  # 17. The facts-resolved side repos: dirty paths reported per repo; one
  #     confirmed commit action each, the sensitive-data scan re-run over the
  #     staged side-repo set before that repo's commit.
  trace_stage side-repo-walk
  SIDE_REPOS=""
  for key in skills_repo_path shared_docs_dir; do
    value="$(side_facts_value "$key")"
    case "$value" in ""|/*) ;; *) continue;; esac
    [ -e "$value/.git" ] || continue
    case "$SIDE_REPOS" in *" $value "*) ;; *) SIDE_REPOS="$SIDE_REPOS $value ";; esac
  done
  if [ -z "$(printf '%s' "$SIDE_REPOS" | tr -d ' ')" ]; then
    echo "done_run commit: side-repo walk: no facts-resolved side repos resolved; walk skipped"
  fi
  for repo in $SIDE_REPOS; do
    DIRTY="$(git -C "$repo" status --porcelain --no-renames)"
    if [ -z "$DIRTY" ]; then
      echo "done_run commit: side-repo walk: $repo: clean"
      continue
    fi
    echo "done_run commit: side-repo walk: $repo: dirty paths:"
    printf '%s\n' "$DIRTY" | sed 's/^/  /'
    CONFIRMED=""
    for confirmed in ${SIDE_COMMIT_ARGS+"${SIDE_COMMIT_ARGS[@]}"}; do
      [ "$confirmed" = "$repo" ] && CONFIRMED=1
    done
    if [ -z "$CONFIRMED" ]; then
      echo "done_run commit: side-repo walk: $repo: left uncommitted (no confirmation for this repo)"
      continue
    fi
    SIDE_PATHS=()
    while IFS= read -r row; do
      [ -n "$row" ] && SIDE_PATHS+=("$(printf '%s' "$row" | cut -c4-)")
    done < <(printf '%s\n' "$DIRTY")
    git -C "$repo" add -- ${SIDE_PATHS+"${SIDE_PATHS[@]}"} || { rm -rf "$tmpd"; commit_die 3 "side-repo walk: git add refused in $repo"; }
    SCAN="$(resolve_helper scan-public-hygiene.sh)"
    if [ -n "$SCAN" ]; then
      SCAN_RC=0
      SCAN_OUT="$(cd "$repo" && PUBLIC_HYGIENE_REPO_ROOT="$repo" bash "$SCAN" --files ${SIDE_PATHS+"${SIDE_PATHS[@]}"} 2>&1)" || SCAN_RC=$?
      printf '%s\n' "$SCAN_OUT"
      if [ "$SCAN_RC" -ne 0 ]; then
        rm -rf "$tmpd"
        commit_die "$SCAN_RC" "side-repo walk: the sensitive-data scan refused $repo's staged set (rc=$SCAN_RC); that repo's commit did not happen"
      fi
    fi
    if ! git -C "$repo" commit -m "docs: done closeout side-repo landing" -- ${SIDE_PATHS+"${SIDE_PATHS[@]}"}; then
      rm -rf "$tmpd"
      commit_die 1 "side-repo walk: the commit refused in $repo"
    fi
    echo "done_run commit: side-repo walk: $repo: landed $(git -C "$repo" rev-parse HEAD)"
  done
  rm -rf "$tmpd"
}

# --- finalize subcommand ----------------------------------------------------

finalize_die() { # rc message...: fail loud with the named evidence
  local rc="$1"
  shift
  echo "done_run finalize: $*" >&2
  exit "$rc"
}

cmd_finalize() {
  # Invocation telemetry start stamp (plan
  # docs/history/plans/2026-10-14-script-runtime-cost-telemetry.md, Task 3):
  # one python3-derived epoch captured at the function's entry so the
  # exit-side append below spans the whole finalize; fail-open and silent
  # (a missing python3 leaves the variable empty and the closeout unchanged).
  FINALIZE_START_EPOCH="$(python3 -c 'import time; print(repr(time.time()))' 2>/dev/null || :)"
  local from_holder=0 no_landing_cost=0 session_id="" path
  FINALIZE_MANIFEST=""; RUN_ID_ARG=""; GUARD_FIRINGS=()
  shift # subcommand
  while [ $# -gt 0 ]; do
    case "$1" in
      --manifest) FINALIZE_MANIFEST="$2"; shift 2;;
      --run-id) RUN_ID_ARG="$2"; shift 2;;
      --from-holder) from_holder=1; shift;;
      --session) session_id="$2"; shift 2;;
      --no-landing-cost) no_landing_cost=1; shift;;
      --guard-firing) GUARD_FIRINGS+=("$2"); shift 2;;
      *) echo "done_run finalize: unknown argument: $1" >&2; exit 3;;
    esac
  done

  local repo_top session lib
  repo_top="$(git rev-parse --show-toplevel 2>/dev/null)" || \
    finalize_die 3 "not inside a git repository"
  cd "$repo_top" || finalize_die 3 "cannot enter the repository root"
  session="$(session_dir)" || finalize_die 3 "cannot resolve the repo root"

  LOCK_SCRIPT="${DONE_LOCK_SCRIPT:-$(resolve_helper done-lock.sh)}"
  [ -n "$LOCK_SCRIPT" ] || finalize_die 3 "no lock script resolved (set DONE_LOCK_SCRIPT)"
  LIB="$(resolve_helper done_sweep_gates_lib.py)"
  [ -n "$LIB" ] || finalize_die 3 "no done_sweep_gates_lib.py resolved (repo-local scripts/ or deployed home)"

  RUN_MANIFEST="$(resolve_manifest_path)" || RUN_MANIFEST=""
  RUN_ID="$(resolve_run_id)"
  local finalize_rc=0 release_rc=0

  # 1. Checkpoint refresh at the finalize preamble: a no-checkpoint refusal
  #    falls back to create-then-refresh; an already-finalized manifest is
  #    the skip-the-refresh arm. A missing manifest is a one-line note.
  if [ -z "$RUN_ID" ] || [ ! -f "$RUN_MANIFEST" ]; then
    echo "done_run finalize: no run manifest from setup; nothing to finalize or checkpoint; the release still runs"
  else
    SESSION_ID="${session_id:-${DONE_RUN_SESSION:-done_run_finalize}}"
    CK_OUT="$(python3 "$LIB" checkpoint-manifest --run-id "$RUN_ID" --mode refresh --session "$SESSION_ID" --gates landing 2>&1)"
    if [ $? -ne 0 ]; then
      case "$CK_OUT" in
        *"already finalized"*|"already complete"*)
          echo "done_run finalize: checkpoint refresh skipped (the manifest already finalized; nothing to refresh)";;
        *"no checkpoint present"*|*"create it first"*)
          python3 "$LIB" checkpoint-manifest --run-id "$RUN_ID" --mode create --session "$SESSION_ID" --gates landing >&2 \
            && python3 "$LIB" checkpoint-manifest --run-id "$RUN_ID" --mode refresh --session "$SESSION_ID" --gates landing >/dev/null \
            || { printf '%s\n' "$CK_OUT" >&2; echo "done_run finalize: WARNING: checkpoint create-then-refresh refused (mutated nothing); continuing" >&2; };;
        *)
          printf '%s\n' "$CK_OUT" >&2
          echo "done_run finalize: WARNING: checkpoint refresh refused (mutated nothing); continuing" >&2;;
      esac
    else
      printf '%s\n' "$CK_OUT"
    fi

    # 2. Manifest finalize: a missing manifest answers exit 0 with the lib's
    #    own note; any other non-zero exit is a real failure recorded for the
    #    final exit (the releases below still run; never stranded).
    FM_OUT="$(python3 "$LIB" finalize-manifest --run-id "$RUN_ID" 2>&1)" || finalize_rc=$?
    printf '%s\n' "$FM_OUT"
    if [ "$finalize_rc" -ne 0 ]; then
      echo "done_run finalize: FAILED (exit $finalize_rc); the run manifest finalize did not complete; running the releases so no lock strands" >&2
    else
      # 3. Checkpoint remove (only after the successful finalize).
      CR_OUT="$(python3 "$LIB" checkpoint-manifest --run-id "$RUN_ID" --mode remove 2>&1)"
      if [ $? -ne 0 ]; then
        printf '%s\n' "$CR_OUT" >&2
        echo "done_run finalize: WARNING: checkpoint remove refused; the sibling stays for a resume continuation" >&2
      else
        printf '%s\n' "$CR_OUT"
      fi
    fi
  fi

  # 4. Done-lock release: the env-token path by default; --from-holder (or
  #    lost exports) takes the lock script's metadata-sourced arm under its
  #    own recorded guards (pinned hold, same host, holder verifiably alive
  #    with exact identity, not pid 1, this shell descends from it).
  if [ "$from_holder" -eq 1 ] || [ -z "${DONE_LOCK_DIR:-}" ] || [ -z "${DONE_LOCK_TOKEN:-}" ]; then
    echo "done_run finalize: releasing the done lock via the from-holder arm (the hold's own acquire-time records gate it)"
    REL_OUT="$(bash "$LOCK_SCRIPT" release-repo --from-holder 2>&1)" || release_rc=$?
  else
    REL_OUT="$(DONE_LOCK_DIR="$DONE_LOCK_DIR" DONE_LOCK_TOKEN="$DONE_LOCK_TOKEN" bash "$LOCK_SCRIPT" release-repo 2>&1)" || release_rc=$?
  fi
  printf '%s\n' "$REL_OUT"
  if [ "$release_rc" -ne 0 ]; then
    echo "done_run finalize: done-lock release refused (rc=$release_rc); read the OUTCOME line above through the outcome contract, then run status" >&2
    [ "$finalize_rc" -eq 0 ] && finalize_rc="$release_rc"
  fi

  # 5. Merge-lock release when a hold survives (the sync and migration
  #    runners release their own spans in finally blocks; a surviving hold is
  #    a stranded span: exports when present, else the same from-holder arm).
  MS_OUT="$(bash "$LOCK_SCRIPT" merge-status 2>&1)" || MS_OUT=""
  if printf '%s\n' "$MS_OUT" | grep -qE ': free( |$)'; then
    echo "done_run finalize: merge lock free"
  else
    echo "done_run finalize: merge lock held; releasing the surviving span"
    if [ -n "${MERGE_LOCK_DIR:-}" ] && [ -n "${MERGE_LOCK_TOKEN:-}" ]; then
      MREL_OUT="$(MERGE_LOCK_DIR="$MERGE_LOCK_DIR" MERGE_LOCK_TOKEN="$MERGE_LOCK_TOKEN" bash "$LOCK_SCRIPT" merge-release-repo 2>&1)" || release_rc=$?
    else
      MREL_OUT="$(bash "$LOCK_SCRIPT" merge-release-repo --from-holder 2>&1)" || release_rc=$?
    fi
    printf '%s\n' "$MREL_OUT"
    if printf '%s\n' "$MREL_OUT" | grep -q '^OUTCOME: pass'; then
      echo "done_run finalize: surviving merge-lock span released"
    else
      echo "done_run finalize: WARNING: the merge-lock hold did not release under this shell (a foreign or ambiguous holder; every refusal names its failed gate); report and leave it" >&2
    fi
  fi

  # 6. Status-free verification.
  ST_OUT="$(bash "$LOCK_SCRIPT" status 2>&1)" || ST_OUT=""
  printf '%s\n' "$ST_OUT"
  if printf '%s\n' "$ST_OUT" | grep -qE ': free( |$)'; then
    echo "done_run finalize: done lock status: free"
  else
    echo "done_run finalize: FAILED: done lock status is not free after the release; do not report completion while a hold survives" >&2
    [ "$finalize_rc" -eq 0 ] && finalize_rc=1
  fi

  # 7. Report-input assembly: the landing summary plus the report-only
  #    missing-review-record scan (never blocking, never fabricating).
  local ledger landing_commit
  ledger=""
  if [ -n "$RUN_ID" ] && [ -f "$session/owned-commits-$RUN_ID.txt" ]; then
    ledger="$session/owned-commits-$RUN_ID.txt"
  fi
  landing_commit=""
  if [ -n "$ledger" ]; then
    landing_commit="$(tail -n 1 "$ledger")"
    echo "done_run finalize: landing summary: run_id=$RUN_ID ledger=$ledger commits=$(wc -l < "$ledger" | tr -d ' ') landing_commit=$landing_commit"
  else
    echo "done_run finalize: landing summary: no owned-commits ledger for this run; nothing landed in the project repo through the commit subcommand"
  fi
  trace_stage missing-review-record-scan
  python3 - "$repo_top" <<'PYEOF' || echo "done_run finalize: WARNING: the missing-review-record scan could not run (report-only; the closeout continues)" >&2
import os
import re
import subprocess
import sys

repo_top = sys.argv[1]


def facts_toml_value(key):
    try:
        text = open(os.path.join(repo_top, ".ai-playbook", "facts.md"), encoding="utf-8").read()
    except OSError:
        return ""
    import re as _re
    m = _re.search(r'^%s = ["\'](.*)["\']$' % key, text, _re.M)
    return m.group(1) if m else ""


primary = subprocess.run(
    ["git", "-C", repo_top, "worktree", "list", "--porcelain"],
    capture_output=True, text=True,
).stdout
primary = next((line[len("worktree "):] for line in primary.splitlines()
                if line.startswith("worktree ")), repo_top)


def facts_rooted(value):
    if not value:
        return ""
    return value if os.path.isabs(value) else os.path.join(repo_top, value)


plans_completed = facts_rooted(facts_toml_value("plans_completed_dir")) \
    or os.path.join(repo_top, "docs/history/plans/completed")
reviews_dir = facts_rooted(facts_toml_value("reviews_dir")) \
    or os.path.join(primary, ".ai-playbook/reviews")

record_re = re.compile(r"[A-Za-z0-9._/-]*(?:plan-review|code-review)[A-Za-z0-9._/-]*-r\d+\.md")
reviewed = {}
for base, _dirs, files in os.walk(reviews_dir):
    for name in files:
        reviewed[name] = True

missing = []
try:
    plan_files = sorted(os.listdir(plans_completed))
except OSError:
    plan_files = []
for name in plan_files:
    if not name.endswith(".md"):
        continue
    try:
        text = open(os.path.join(plans_completed, name), encoding="utf-8", errors="replace").read()
    except OSError:
        continue
    for record in sorted(set(record_re.findall(text))):
        if os.path.basename(record) not in reviewed:
            missing.append((name, record))

for citing, record in missing:
    print(f"missing-review-record: {record} cited by {citing} (reconstruction duty: report with a witness note; never fabricate, never block, never delete)")
print(f"missing-review-record scan: {len(missing)} missing record(s)")
PYEOF

  # 8. Advisory appends: guard-liveness ledger rows and the landing-cost
  #    telemetry line. Echo-and-continue: a failed append is a warning line
  #    and never blocks the closeout.
  trace_stage advisory-appends
  local firing ledger_script GL_OUT=""
  if [ "${#GUARD_FIRINGS[@]}" -gt 0 ]; then
    ledger_script="$(resolve_helper gate_liveness_ledger.py)"
    if [ -z "$ledger_script" ]; then
      echo "done_run finalize: WARNING: no gate_liveness_ledger.py resolved; guard-liveness appends skipped (advisory)" >&2
    fi
    for firing in ${GUARD_FIRINGS+"${GUARD_FIRINGS[@]}"}; do
      local gname gkind gevidence gnote
      gname="$(printf '%s' "$firing" | cut -d: -f1)"
      gkind="$(printf '%s' "$firing" | cut -d: -f2)"
      gevidence="$(printf '%s' "$firing" | cut -d: -f3)"
      gnote="$(printf '%s' "$firing" | cut -d: -f4-)"
      if [ -z "$gname" ] || [ -z "$gkind" ] || [ -z "$gevidence" ]; then
        echo "done_run finalize: WARNING: malformed --guard-firing (want NAME:KIND:EVIDENCE[:NOTE]): $firing" >&2
        continue
      fi
      GL_ARGS=(record --guard "$gname" --kind "$gkind" --date "$(date -u +%F)" --evidence "$gevidence")
      [ -n "$gnote" ] && GL_ARGS+=(--note "$gnote")
      if [ -n "$ledger_script" ]; then
        GL_OUT="$(python3 "$ledger_script" ${GL_ARGS+"${GL_ARGS[@]}"} 2>&1)" \
          || echo "done_run finalize: WARNING: guard-liveness append failed for $gname (advisory; the closeout continues)" >&2
        [ -n "$GL_OUT" ] && printf '%s\n' "$GL_OUT"
      fi
    done
  fi
  if [ "$no_landing_cost" -eq 0 ] && [ -n "$landing_commit" ] && [ -n "$RUN_MANIFEST" ] && [ -f "$RUN_MANIFEST" ]; then
    metrics_dir="$(facts_toml_value metrics_dir)"
    metrics_dir="${metrics_dir:-.ai-playbook/metrics}"
    case "$metrics_dir" in /*) ;; *) metrics_dir="$repo_top/$metrics_dir";; esac
    mkdir -p "$metrics_dir" 2>/dev/null || true
    LC_RC=0
    LC_OUT="$(python3 - "$RUN_MANIFEST" "$landing_commit" "$metrics_dir/landing-costs.jsonl" "$session" <<'PYEOF' 2>&1
import datetime
import json
import os
import sys

manifest_path, landing_commit, costs_path, session = sys.argv[1:5]
plan_slug = None
note = "no owned plan recorded for this run"
try:
    record = json.load(open(manifest_path, encoding="utf-8"))
    owned = record.get("owned_plan_paths") or []
    if owned:
        plan_slug = owned[0]
        note = None
except (OSError, ValueError):
    pass
wall_hours = None
try:
    markers = sorted(
        (os.path.join(session, name) for name in os.listdir(session)
         if name.startswith("run-start-")),
        key=lambda p: os.path.getmtime(p),
    )
    if markers:
        start_epoch = int(open(markers[-1]).read().split()[0])
        wall_hours = round((datetime.datetime.now().timestamp() - start_epoch) / 3600.0, 4)
except (OSError, ValueError, IndexError):
    pass
line = {
    "plan_slug": plan_slug,
    "landing_commit": landing_commit,
    "wall_hours": wall_hours,
    "review_rounds": None,
    "gate_refusals": None,
    "operator_interventions": None,
    "tokens_est": None,
    "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
}
if plan_slug is None:
    line["note"] = note
with open(costs_path, "a", encoding="utf-8") as handle:
    handle.write(json.dumps(line, sort_keys=True) + "\n")
print(f"landing-cost telemetry appended: {costs_path}")
PYEOF
    )" || LC_RC=$?
    printf '%s\n' "$LC_OUT"
    if [ "$LC_RC" -ne 0 ]; then
      echo "done_run finalize: WARNING: the landing-cost telemetry append failed (advisory; the closeout continues)" >&2
    fi
  fi

  # 9. Invocation telemetry: one invocation_kind closeout-battery line
  #    spanning the whole finalize (plan
  #    docs/history/plans/2026-10-14-script-runtime-cost-telemetry.md,
  #    Task 3). Unconditional and outside the landing-cost guard above:
  #    every real finalize arm (no-ledger, --no-landing-cost, no-manifest)
  #    records exactly one line; the usage-error and early-refusal arms
  #    exit before this block and record none. Same facts-resolved metrics
  #    home shape as the landing-cost writer, via the telemetry library
  #    beside this script. Fail-open and stdout-silent: the one python3
  #    call is fully silenced and `|| :`-guarded, so telemetry success or
  #    failure never changes the closeout's exit status, stdout, or stderr
  #    contract (diagnostics stderr-only at most, none by default).
  if [ -n "$FINALIZE_START_EPOCH" ]; then
    python3 -c '
import sys, time
from pathlib import Path
script_path = sys.argv[1]
try:
    lib_dir = str(Path(script_path).resolve().parent)
    if lib_dir not in sys.path:
        sys.path.insert(0, lib_dir)
    import invocation_telemetry as telemetry
    wall_ms = max(0.0, (time.time() - float(sys.argv[2])) * 1000.0)
    telemetry.record_invocation(script_path, "closeout-battery", wall_ms)
except Exception:
    pass
' "${BASH_SOURCE[0]}" "$FINALIZE_START_EPOCH" >/dev/null 2>&1 || :
  fi

  exit "$finalize_rc"
}

main() {
  if [ $# -lt 1 ]; then
    sed -n '2,85p' "${BASH_SOURCE[0]}" >&2
    exit 3
  fi
  case "$1" in
    setup) cmd_setup "$@";;
    commit) cmd_commit "$@";;
    finalize) cmd_finalize "$@";;
    *) echo "done_run: unknown subcommand: $1" >&2; exit 3;;
  esac
}

main "$@"
