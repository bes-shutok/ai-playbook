#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
Usage: test_framework_callback_readability_session.sh \
  --manifest PATH [--run-base COMMIT] [--execution-log PATH]
USAGE
}

manifest=
run_base_override=
execution_log_override=
while (($#)); do
  case "$1" in
    --manifest)
      (($# >= 2)) || { usage; exit 2; }
      manifest=$2
      shift 2
      ;;
    --run-base)
      (($# >= 2)) || { usage; exit 2; }
      run_base_override=$2
      shift 2
      ;;
    --execution-log)
      (($# >= 2)) || { usage; exit 2; }
      execution_log_override=$2
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

[[ -n "$manifest" ]] || { usage; exit 2; }

validate_session_evidence() {
  [[ -f "$manifest" ]] || exit 1

  repo_root=$(git rev-parse --show-toplevel)
  manifest_base=$(sed -nE 's/^run_base: .*([0-9a-f]{40}).*/\1/p' "$manifest")
  manifest_log=$(sed -nE 's/^\| Phase 1 task 3 \| ([^|]+) \|.*/\1/p' "$manifest" | sed 's/^ *//;s/ *$//')
  run_base=${run_base_override:-$manifest_base}
  execution_log=${execution_log_override:-$manifest_log}
  [[ -n "$run_base" && -n "$execution_log" ]] || exit 1
  [[ -s "$execution_log" ]] || exit 1
  expected_header='# Execute-plan session: framework-callback-readability-and-review-scope'
  [[ $(head -n 1 "$manifest") == "$expected_header" ]] || exit 1
  manifest_branch=$(sed -n 's/^run_branch: //p' "$manifest")
  [[ -n "$manifest_branch" && "$manifest_branch" == "$(git branch --show-current)" ]] || exit 1
  [[ "$manifest_base" == "$run_base" ]] || exit 1
  [[ "$manifest_log" == "$execution_log" ]] || exit 1
  [[ $(git rev-parse --verify "$run_base^{commit}") == "$run_base" ]] || exit 1
  git merge-base --is-ancestor "$run_base" HEAD || exit 1

  bash "$repo_root/scripts/check-no-em-dash.sh" added-lines --base "$run_base" -- \
    projects/.ai-playbook/jvm_guidelines.md \
    projects/.ai-playbook/java_guidelines.md \
    projects/.ai-playbook/kotlin_guidelines.md \
    agents/skills/review-agents/quality.md \
    agents/skills/review-agents/review-panel-selection.md \
    scripts/machinery_registry.json
  bash "$repo_root/scripts/check-no-em-dash.sh" file "$manifest" "$execution_log"
  printf '%s\n' 'session evidence checks: ok'
}

validate_session_evidence
