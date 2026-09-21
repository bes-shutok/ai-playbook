#!/usr/bin/env bash
# Deploy runtime scripts to a target directory with committed provenance.
#
# Usage: deploy_runtime_scripts.sh <target-dir> <script-name> [<script-name>...]
#
# Copies each named script from this repository's scripts/ directory into the
# target directory, then writes a .source-commit file beside the copies
# containing the current HEAD sha. Refuses to run when the working tree is
# dirty (including untracked files): stamped provenance must be committed
# provenance. Stamping is manual-only by design; this helper is the
# sanctioned manual path.
#
# Exit codes: 0 on success; 1 on refusal (dirty tree, missing source file);
# 2 on usage error.
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "usage: deploy_runtime_scripts.sh <target-dir> <script-name> [<script-name>...]" >&2
  exit 2
fi

target_dir="$1"
shift

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

dirty="$(git -C "$repo_root" status --porcelain)"
if [ -n "$dirty" ]; then
  echo "REFUSED: working tree is dirty; stamped provenance must be committed provenance" >&2
  exit 1
fi

head_sha="$(git -C "$repo_root" rev-parse HEAD)"

for name in "$@"; do
  if [ ! -f "$repo_root/scripts/$name" ]; then
    echo "REFUSED: not a file under scripts/: $name" >&2
    exit 1
  fi
done

mkdir -p "$target_dir"
for name in "$@"; do
  cp "$repo_root/scripts/$name" "$target_dir/$name"
done

printf '%s\n' "$head_sha" > "$target_dir/.source-commit"
echo "deployed $# script(s) to $target_dir from commit $head_sha"
