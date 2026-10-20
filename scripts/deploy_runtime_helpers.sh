#!/usr/bin/env bash
# deploy_runtime_helpers.sh: the one sanctioned stale-deployment remedy for the
# runtime home (default $HOME/.ai-playbook/scripts/).
#
# Contract:
# - Canonical repo resolution chain (ordered): the explicit --repo DIR flag,
#   then the invocation repo's toplevel when it is itself a skills-repo
#   checkout (its toplevel carries scripts/runtime-scripts.list), then the
#   user facts skills_repo_path key (resolved from the facts document at
#   $HOME/.ai-playbook/facts.md unless --facts PATH names another).
# - When no arm resolves, or the resolved canonical carries no
#   scripts/runtime-scripts.list: deploy mode ends OUTCOME: tool_error with
#   exit 3 and a named error; check mode prints one skipped-arms advisory
#   line and exits 0 with OUTCOME: pass.
# - The helper inventory is read at run time from the resolved canonical
#   repo's scripts/runtime-scripts.list (one manifest source, no second
#   resolution; '#' comments and blank lines are skipped).
# - A manifest entry carrying a scripts/ path prefix maps to the runtime-home
#   basename, because the runtime home is flat.
# - Per admitted name: the canonical file missing prints a skip line and
#   creates nothing; the runtime-home name absent is linked fresh to the
#   canonical file; a name already a symlink resolving to the canonical file
#   prints a current line (deploy mode) and is left untouched; a regular-file
#   copy or a symlink aimed elsewhere is moved aside to <name>.bak-<UTC date>
#   and replaced by a symlink to the canonical file (a pre-existing
#   .bak-<date> sibling is replaced by the newer sibling, never the live
#   entry). The conversion class the manifest's own header documents.
# - Modes: deploy is the default and ends OUTCOME: pass with exit 0 except
#   the refusals above; --check is report-only and runs the same walk without
#   writing: every anomaly prints one advisory line naming the deploy remedy,
#   and check mode always ends OUTCOME: pass and exits 0 (the drift advisory
#   never gates).
# - Post-walk verification: after the walk, the deployer runs
#   verify_runtime_deployment.py over the same canonical repo, runtime home,
#   and mode, resolved beside this script's own realpath, never from the
#   runtime home. The verifier scans the admitted entries' transitive
#   local-sibling closure over canonical bytes and probes every admitted
#   .py entry (shell entries are outside its domain): one -I -S -B child per
#   entry with a minimized environment (no PYTHONPATH), cwd and import root
#   a shared materialized probe root holding dereferenced copies of the
#   home's canonical-linked entries; the probe only executes bytes that are
#   symlinks dereferencing into the canonical scripts directory, and probing
#   those bytes executes module bodies, the residual trust extended to
#   admitted bytes. Deploy mode: any refusal (closure gap, canonical-missing,
#   home-absent, unreadable or unparseable bytes, not-canonical,
#   import-probe failure), or a verifier that cannot run at all, ends
#   OUTCOME: fail with exit 1, terminal in-run: every violation named in the
#   one run, never a retry or a skip-and-pass, and park-for-operator is the
#   bounded repair when no named remedy converges. Check mode: the same
#   findings are advisories, one converging remedy per class (closure gap:
#   the manifest edit; canonical-missing: restore the file or drop the
#   line; home-absent: the deploy run; unreadable or unparseable bytes:
#   restore the file, or drop the line for an admitted entry; not-canonical:
#   run the deploy run from the primary checkout or remove the foreign
#   file; probe failure: the named entry, a missing sibling the manifest
#   edit, otherwise park-for-operator), and an unresolvable or failed
#   verifier prints one
#   skipped-verification advisory; both keep the report-only contract
#   (OUTCOME: pass, exit 0). The verifier's own OUTCOME line is dropped so
#   the run carries exactly one final OUTCOME line.
# - Nothing is ever written under the canonical repo: the repo is the source,
#   the runtime home is the destination, never the reverse.
# - --home DIR names the runtime scripts directory (default
#   $HOME/.ai-playbook/scripts) so tests never touch the real home.
set -euo pipefail

usage_error() { # usage_error <message>: a usage violation is a tool error
  echo "error: $1" >&2
  echo "OUTCOME: tool_error"
  exit 3
}

MODE="deploy"
REPO_FLAG=""
HOME_DIR_FLAG=""
FACTS_FLAG=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --check)
      MODE="check"
      shift
      ;;
    --repo)
      [ "$#" -ge 2 ] || usage_error "--repo needs a directory value"
      REPO_FLAG="$2"
      shift 2
      ;;
    --home)
      [ "$#" -ge 2 ] || usage_error "--home needs a directory value"
      HOME_DIR_FLAG="$2"
      shift 2
      ;;
    --facts)
      [ "$#" -ge 2 ] || usage_error "--facts needs a path value"
      FACTS_FLAG="$2"
      shift 2
      ;;
    *)
      usage_error "unknown argument: $1"
      ;;
  esac
done

RUNTIME_HOME="${HOME_DIR_FLAG:-${HOME}/.ai-playbook/scripts}"
FACTS_FILE="${FACTS_FLAG:-${HOME}/.ai-playbook/facts.md}"
REMEDY="bash scripts/deploy_runtime_helpers.sh"

facts_value() { # facts_value <facts_file> <key>: print the first table cell
  #               after the cell equal to <key>, backticks stripped; the
  #               facts document is a Markdown table, one key per row
  awk -F'|' -v key="$2" '
    index($0, key) {
      for (i = 2; i <= NF; i++) {
        cell = $i
        gsub(/`/, "", cell)
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", cell)
        if (cell == key) { want = 1; continue }
        if (want && cell != "") { print cell; exit }
      }
    }' "$1" 2>/dev/null || true
}

# Canonical-repo resolution through the ordered chain.
canonical=""
detail=""
if [ -n "$REPO_FLAG" ]; then
  canonical="$REPO_FLAG"
else
  top="$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || true)"
  if [ -n "$top" ] && [ -f "$top/scripts/runtime-scripts.list" ]; then
    canonical="$top"
  elif [ -f "$FACTS_FILE" ]; then
    facts_dir="$(facts_value "$FACTS_FILE" "skills_repo_path")"
    if [ -n "$facts_dir" ]; then
      facts_dir="${facts_dir/#\~/${HOME}}"
      if [ -d "$facts_dir" ]; then
        canonical="$facts_dir"
      fi
    fi
  fi
fi

if [ -z "$canonical" ]; then
  detail="no canonical repo resolved through the chain (the --repo flag, the invocation repo's toplevel carrying scripts/runtime-scripts.list, the facts skills_repo_path key)"
elif [ ! -f "$canonical/scripts/runtime-scripts.list" ]; then
  detail="the resolved canonical repo carries no scripts/runtime-scripts.list: $canonical"
fi

if [ -n "$detail" ]; then
  if [ "$MODE" = "check" ]; then
    echo "advisory: runtime-helper drift check skipped: $detail; run $REMEDY once a canonical repo resolves"
    echo "OUTCOME: pass"
    exit 0
  fi
  echo "error: $detail"
  echo "OUTCOME: tool_error"
  exit 3
fi

if [ "$MODE" = "deploy" ]; then
  mkdir -p "$RUNTIME_HOME"
fi

manifest="$canonical/scripts/runtime-scripts.list"
bak_date="$(date -u +%Y%m%d)"

while IFS= read -r entry || [ -n "$entry" ]; do
  entry="${entry%$'\r'}"
  case "$entry" in
    "" | "#"*) continue ;;
  esac
  base="$(basename "$entry")"
  src="$canonical/scripts/$base"
  dst="$RUNTIME_HOME/$base"
  if [ ! -f "$src" ]; then
    echo "skip: $base (admitted by scripts/runtime-scripts.list but missing from the canonical repo at $src; nothing created)"
    continue
  fi
  if [ -L "$dst" ] && [ "$dst" -ef "$src" ]; then
    if [ "$MODE" = "deploy" ]; then
      echo "current: $base -> $src"
    fi
    continue
  fi
  if [ ! -e "$dst" ] && [ ! -L "$dst" ]; then
    if [ "$MODE" = "check" ]; then
      echo "missing: $base (deploy remedy: run $REMEDY to link it to the canonical file)"
    else
      ln -s "$src" "$dst"
      echo "linked: $base -> $src"
    fi
    continue
  fi
  bak="$dst.bak-$bak_date"
  if [ "$MODE" = "check" ]; then
    echo "stale: $base (deploy remedy: run $REMEDY from the primary checkout to move it aside to $bak and replace it with a symlink to the canonical file)"
  else
    rm -f "$bak"
    mv "$dst" "$bak"
    ln -s "$src" "$dst"
    echo "stale: $base moved aside to $bak and replaced by a symlink to $src"
  fi
done < "$manifest"

# The verifier resolves beside this script's own realpath, never from the
# runtime home: a deployed deployer copy is a symlink whose realpath lands in
# the canonical scripts directory, so the canonical twin is the one that runs.
verifier=""
self_real=""
if command -v python3 >/dev/null 2>&1; then
  self_real="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$0" 2>/dev/null)" || self_real=""
fi
if [ -n "$self_real" ]; then
  candidate="$(dirname "$self_real")/verify_runtime_deployment.py"
  if [ -f "$candidate" ]; then
    verifier="$candidate"
  fi
fi

if [ -z "$verifier" ]; then
  if [ "$MODE" = "check" ]; then
    echo "advisory: deployment verification skipped: no verify_runtime_deployment.py beside the deployer (resolved from $(dirname "$0")); run the deploy run once a canonical repo carries it"
    echo "OUTCOME: pass"
    exit 0
  fi
  echo "error: deployment verification could not run: no verify_runtime_deployment.py beside the deployer (resolved from $(dirname "$0"))"
  echo "OUTCOME: fail"
  exit 1
fi

verify_rc=0
verify_out="$(python3 "$verifier" --repo "$canonical" --home "$RUNTIME_HOME" --manifest "$manifest" --mode "$MODE" 2>&1)" || verify_rc=$?
verify_lines="$(printf '%s\n' "$verify_out" | grep -v '^OUTCOME:' || true)"

if [ "$verify_rc" -eq 0 ]; then
  if [ -n "$verify_lines" ]; then
    printf '%s\n' "$verify_lines"
  fi
  echo "OUTCOME: pass"
  exit 0
fi
if [ "$MODE" = "check" ]; then
  echo "advisory: deployment verification skipped: the verifier could not run (exit $verify_rc); run python3 $verifier --repo $canonical --home $RUNTIME_HOME --mode check for its evidence"
  echo "OUTCOME: pass"
  exit 0
fi
if [ "$verify_rc" -ne 1 ]; then
  echo "error: deployment verification could not run (verifier exit $verify_rc)"
fi
if [ -n "$verify_lines" ]; then
  printf '%s\n' "$verify_lines"
fi
echo "OUTCOME: fail"
exit 1
