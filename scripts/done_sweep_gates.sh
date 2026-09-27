#!/usr/bin/env bash
# done_sweep_gates.sh - done sweep gate runner (one call per phase).
#
# Runs the done skill's deterministic gates in SKILL.md order and emits one
# machine-readable report (one JSON line per gate: gate, rc, message) plus a
# human summary. Judgment steps (lock and run-start marker, learn, docs-branch,
# formatting rollback, cross-references, unused-import scan, commit staging
# decisions, lock release, outcome report) stay in the done skill.
#
# Usage:
#   done_sweep_gates.sh pre-docs     # done Steps 1.5, 2.65, 2.648, 2.645, 2.64, 2.63, 2.62 gates
#   done_sweep_gates.sh pre-commit   # done Steps 2.7 (mechanical half), 2.76, 2.8 gates
#   done_sweep_gates.sh list-gates   # print the twelve absorbed gate ids, deduped at first phase
#   done_sweep_gates.sh write-manifest [flags...]   # done Step 0 manifest write (full flag vector forwarded)
#
# Run from the project git root (or set DONE_SWEEP_REPO_ROOT). Path resolution
# anchors at the repo root via scripts/facts_paths.py helpers; validator
# scripts resolve env override, then repo-local scripts/, then the deployed
# runtime home copy. Syncs nothing. Exit code: 0 when every gate passed, else
# non-zero (the highest gate rc).

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: done_sweep_gates.sh <pre-docs|pre-commit|list-gates|write-manifest>

Phases:
  pre-docs     plan-readiness, confluence-hygiene, doc-registry, backlog-inbox,
               review-staging, vim-swap-sweep, docs-tmp-sweep, plans-archive-twin
               (done Steps 1.5, 2.65, 2.648, 2.645, 2.64, 2.63, 2.62)
  pre-commit   sensitive-data-scan, em-dash-scan, instruction-size,
               foreign-staging, plans-archive-twin
               (done Steps 2.7 mechanical half, 2.76, 2.8)
  list-gates   print the twelve absorbed gate ids, deduped at first phase
  write-manifest
               done Step 0 run manifest write; the FULL argument vector is
               forwarded to the lib (e.g. --adopt, --owned-review,
               --foreign-review, --claim-none, --foreign-review-from)

Environment:
  DONE_SWEEP_REPO_ROOT     repo anchor override (default: git toplevel of cwd)
  DONE_SWEEP_RUNTIME_HOME  runtime home override (default: ~/.ai-playbook)
  DONE_SWEEP_USER_FACTS    user facts document override (default: <runtime_home>/facts.md)
EOF
}

main() {
  local phase_arg="${1:-}"
  case "$phase_arg" in
    pre-docs|pre-commit|list-gates|write-manifest) ;;
    -h|--help) usage; return 0 ;;
    "")
      usage >&2
      return 2
      ;;
    *)
      echo "done_sweep_gates: unknown phase '$phase_arg'" >&2
      usage >&2
      return 2
      ;;
  esac

  local script_dir lib
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  lib="$script_dir/done_sweep_gates_lib.py"
  if [[ ! -f "$lib" ]]; then
    echo "done_sweep_gates: lib not found next to the runner: $lib" >&2
    return 2
  fi
  # F2: forward the FULL argument vector so flags survive the wrapper (a
  # phase-only forward would silently drop --adopt and the F13 bulk flags on
  # exactly the interrupted-run flow they serve).
  exec python3 "$lib" "$@"
}

main "$@"
