#!/usr/bin/env bash
# One bundled runner for the repository's standing plan gate set
# (backlog docs/history/backlog/2026-10-05-plan-gate-bundle-script.md).
# Additive by design: every child gate keeps its own outcome contract, exit
# code, and output; the bundle only aggregates. All gates run to completion
# even after an earlier failure. Paths resolve relative to the repository
# root (git rev-parse --show-toplevel), so the bundle runs from anywhere
# inside the repo.
# Outcome contract (scripts/OUTCOME_CONTRACT.md): exit 0 with a final
# `OUTCOME: pass` when every gate is green; exit 1 with a final
# `OUTCOME: fail` naming the first failing gate when any gate fails; exit 3
# with a final `OUTCOME: tool_error` for usage and environment errors
# (unknown argument, not inside a git repository, a
# RUN_PLAN_GATES_OVERRIDE that names a missing or unreadable file, or an
# override that yields no runnable gate command). --help
# is a metadata exit without an OUTCOME line.
set -eu

prog=run_plan_gates

usage() {
  cat <<'EOF'
Usage: run_plan_gates.sh [--help]

Runs the standing plan gate set as one bundle, from the repository root
(git rev-parse --show-toplevel). Every gate runs even after an earlier
gate fails; the bundle then exits 1 naming the first failing gate.

Gates, in order:
  python3 scripts/test_corrections_record.py
  python3 scripts/test_plan_delta_classifier.py
  python3 scripts/test_code_delta_classifier.py
  python3 scripts/test_fix_plan_em_dashes.py
  python3 scripts/validate_review_staging.py --selftest
  python3 scripts/test_plan_readiness.py
  python3 scripts/plan_readiness.py --selftest
  bash scripts/check_maintenance_pins.sh
  python3 scripts/test_check_no_em_dash.py

Deliberately not in the bundle: the machine-specific hygiene scan
(`bash ~/.ai-playbook/scripts/scan-public-hygiene.sh`). It is bound to one
host's checkout path by design, so it stays a session-level gate run
manually before commit, not a bundled gate.

Per gate the bundle prints the gate command, its exit code, and its final
`OUTCOME:` line. A gate whose selftest reports no OUTCOME line of its own
reports `none`; its verdict rides the exit code. That none-class is the
unittest suites, and the staging validator selftest (its printed `OUTCOME:`
lines belong to the sub-runs it exercises, not to the selftest run itself).
Full gate output is appended to one temporary log file: removed when every
gate is green, kept and its path printed on failure.

Override (for tests and local variants): when the environment variable
RUN_PLAN_GATES_OVERRIDE names an existing readable file, its lines run
instead of the built-in list, one shell command per line, each run with the
repository root as the working directory. Blank lines and lines starting
with `#` are skipped. An override that yields no runnable gate command (it
holds only blank or comment lines) is a usage error: exit 3 with
`OUTCOME: tool_error`. The override changes the gate list only, never the
exit contract.

Exit contract: 0 all gates green (`OUTCOME: pass`); 1 any gate failed
(`OUTCOME: fail`, first failing gate named); 3 usage or environment tool
error (`OUTCOME: tool_error`: unknown argument, not inside a git
repository, an override naming a missing or unreadable file, or an
override yielding no runnable gate command). --help is a metadata exit (no
OUTCOME line).
EOF
}

tool_error() {
  echo "${prog}: $1" >&2
  echo "OUTCOME: tool_error"
  exit 3
}

case "${1:-}" in
  "") ;;
  -h|--help|help) usage; exit 0 ;;
  *) tool_error "unknown argument: $1 (see --help)" ;;
esac

repo="$(git rev-parse --show-toplevel 2>/dev/null)" \
  || tool_error "not inside a git repository"

if [[ -n "${RUN_PLAN_GATES_OVERRIDE:-}" ]]; then
  [[ -f "$RUN_PLAN_GATES_OVERRIDE" && -r "$RUN_PLAN_GATES_OVERRIDE" ]] \
    || tool_error "RUN_PLAN_GATES_OVERRIDE names a missing or unreadable file: ${RUN_PLAN_GATES_OVERRIDE}"
  gates=()
  while IFS= read -r override_line || [[ -n "$override_line" ]]; do
    override_line="$(printf '%s' "$override_line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
    if [[ -z "$override_line" || "$override_line" == \#* ]]; then
      continue
    fi
    gates+=("$override_line")
  done < "$RUN_PLAN_GATES_OVERRIDE"
  if [[ "${#gates[@]}" -eq 0 ]]; then
    tool_error "RUN_PLAN_GATES_OVERRIDE yields no runnable gate command (only blank or comment lines): ${RUN_PLAN_GATES_OVERRIDE}"
  fi
else
  gates=(
    "python3 scripts/test_corrections_record.py"
    "python3 scripts/test_plan_delta_classifier.py"
    "python3 scripts/test_code_delta_classifier.py"
    "python3 scripts/test_fix_plan_em_dashes.py"
    "python3 scripts/validate_review_staging.py --selftest"
    "python3 scripts/test_plan_readiness.py"
    "python3 scripts/plan_readiness.py --selftest"
    "bash scripts/check_maintenance_pins.sh"
    "python3 scripts/test_check_no_em_dash.py"
  )
fi

total="${#gates[@]}"
index=0
any_failed=0
first_failure=""
log_file="$(mktemp "${TMPDIR:-/tmp}/plan-gates-log.XXXXXX")"

for gate_cmd in "${gates[@]}"; do
  index=$((index + 1))
  echo "=== gate ${index}/${total}: ${gate_cmd}"
  gate_rc=0
  gate_out="$(cd "$repo" && bash -c "$gate_cmd" 2>&1)" || gate_rc=$?
  outcome_line="$(printf '%s\n' "$gate_out" | grep -E '^OUTCOME: ' | tail -n 1 || true)"
  if [[ -n "$outcome_line" ]]; then
    outcome_text="${outcome_line#OUTCOME: }"
  else
    outcome_text="none"
  fi
  {
    echo "=== gate ${index}/${total}: ${gate_cmd} (exit ${gate_rc})"
    printf '%s\n' "$gate_out"
    echo
  } >> "$log_file"
  echo "exit: ${gate_rc}"
  echo "outcome: ${outcome_text}"
  if [[ "$gate_rc" -ne 0 ]] && [[ "$any_failed" -eq 0 ]]; then
    any_failed=1
    first_failure="$gate_cmd"
  fi
done

if [[ "$any_failed" -eq 0 ]]; then
  echo "plan-gates: ${total}/${total} gates green"
  rm -f "$log_file"
  echo "OUTCOME: pass"
  exit 0
fi

echo "plan-gates: FAIL: first failing gate: ${first_failure}"
echo "plan-gates: full gate output: ${log_file}"
echo "OUTCOME: fail"
exit 1
