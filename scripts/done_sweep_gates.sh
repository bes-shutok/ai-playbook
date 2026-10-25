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
#   done_sweep_gates.sh landing [--boundary-class per-task|final-closeout]
#                  # the closeout's one landing sweep run (the retained roster; warning-posture gates report, never block); the boundary class defaults to final-closeout and per-task runs the roster minus the primary-checkout inspection
#   done_sweep_gates.sh list-gates [phase]  # print the landing roster, one gate per line (warning-posture gates suffixed " (warning)")
#   done_sweep_gates.sh write-manifest [flags...]   # done Step 0 manifest write (full flag vector forwarded)
#
# Run from the project git root (or set DONE_SWEEP_REPO_ROOT). Path resolution
# anchors at the repo root via scripts/facts_paths.py helpers; validator
# scripts resolve env override, then repo-local scripts/, then the deployed
# runtime home copy. Syncs nothing. Outcome contract
# (scripts/OUTCOME_CONTRACT.md): phase runs exit 0 pass, 1 fail,
# 2 indeterminate, 3 tool error, ending stdout with exactly one final
# `OUTCOME:` line; a usage error or a lib missing next to the runner is a
# tool error (exit 3 with an OUTCOME line); --help is a metadata exit with
# no OUTCOME line.

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: done_sweep_gates.sh <landing|list-gates|write-manifest>

Phases:
  landing      the closeout's one landing sweep run: the retained roster with
               instruction-size in warning posture (it reports, never blocks)
               and description-length blocking (a measured over-cap result
               refuses, and the commit path records the catch pre-refusal;
               deployment gaps and operational-exception exits answer tool
               error); backlog-inbox and vim-swap-sweep
               are not on the roster (receiving-review capture step and the
               periodic survey advisory own their duties); accepts
               --boundary-class per-task|final-closeout (default final-
               closeout): per-task runs the roster minus the primary-
               checkout inspection (post-landing-staging), which only the
               final closeout, the landing owner, keeps
  list-gates [phase]
               print the landing roster one gate per line with warning-
               posture gates suffixed " (warning)"
  write-manifest
               done Step 0 run manifest write; the FULL argument vector is
               forwarded to the lib (e.g. --adopt, --owned-review,
               --foreign-review, --claim-none, --foreign-review-from)

Environment:
  DONE_SWEEP_REPO_ROOT     repo anchor override (default: git toplevel of cwd)
  DONE_SWEEP_RUNTIME_HOME  runtime home override (default: ~/.ai-playbook)
  DONE_SWEEP_USER_FACTS    user facts document override (default: <runtime_home>/facts.md)
  DONE_SWEEP_DECLARED_STAGE_PATHS
                           newline-separated declared-stage paths unioned into
                           the post-landing-staging gate's owned set behind the
                           primary-checkout shape guard (a direct landing
                           invocation inherits ambient values; the production
                           writer is the done_run.sh cmd_commit composition,
                           which sets this variable only for its own landing
                           sweep subprocess and actively unsets it when the
                           declared set is empty)
EOF
}

main() {
  local phase_arg="${1:-}"
  case "$phase_arg" in
    landing|list-gates|write-manifest) ;;
    -h|--help) usage; return 0 ;;
    "")
      usage >&2
      echo "OUTCOME: tool_error"
      return 3
      ;;
    *)
      echo "done_sweep_gates: unknown phase '$phase_arg'" >&2
      usage >&2
      echo "OUTCOME: tool_error"
      return 3
      ;;
  esac

  local script_dir lib
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  lib="$script_dir/done_sweep_gates_lib.py"
  if [[ ! -f "$lib" ]]; then
    echo "done_sweep_gates: lib not found next to the runner: $lib" >&2
    echo "OUTCOME: tool_error"
    return 3
  fi
  # F2: forward the FULL argument vector so flags survive the wrapper (a
  # phase-only forward would silently drop --adopt and the F13 bulk flags on
  # exactly the interrupted-run flow they serve).
  exec python3 "$lib" "$@"
}

main "$@"
