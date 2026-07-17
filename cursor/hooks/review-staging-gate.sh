#!/usr/bin/env bash
# Cursor hook adapter for review-staging validation.
#
# Modes (argv[1]):
#   edit   - postToolUse (Write): warn via additional_context (soft)
#   commit - beforeShellExecution: deny review-loop commits when staging invalid (hard)
#   stop   - stop: followup when newest round staging doc still invalid (hard)
#
# Core: ~/.ai-playbook/scripts/validate_review_staging.py
set -u

MODE="${1:-}"
VALIDATOR="${REVIEW_STAGING_VALIDATOR:-${HOME}/.ai-playbook/scripts/validate_review_staging.py}"
input="$(cat)"

if [[ ! -f "$VALIDATOR" ]]; then
  case "$MODE" in
    commit)
      printf '%s\n' '{"permission":"deny","user_message":"review-staging validator missing; install scripts/validate_review_staging.py to ~/.ai-playbook/scripts/ before review-loop commits"}'
      ;;
    stop)
      printf '%s\n' '{"followup_message":"review-staging validator missing at ~/.ai-playbook/scripts/validate_review_staging.py; install from repo scripts/ before ending the review-loop round."}'
      ;;
    *)
      printf '%s\n' '{"additional_context":"WARN: review-staging validator missing; stub staging docs will not be checked. Install scripts/validate_review_staging.py to ~/.ai-playbook/scripts/."}'
      ;;
  esac
  exit 0
fi

REVIEW_HOOK_INPUT="$input" python3 - "$MODE" "$VALIDATOR" <<'PY'
import json
import os
import re
import subprocess
import sys
from pathlib import Path

mode = sys.argv[1]
validator = Path(sys.argv[2])
raw = os.environ.get("REVIEW_HOOK_INPUT", "")

try:
    payload = json.loads(raw) if raw.strip() else {}
except Exception:
    payload = {}

cwd = payload.get("cwd")
if not isinstance(cwd, str) or not cwd:
    cwd = str(Path.cwd())

def resolve_path(file_path: str) -> str | None:
    if not file_path:
        return None
    p = Path(file_path)
    if not p.is_absolute():
        p = Path(cwd) / p
    return str(p.resolve())

def run_validate(path: str, *, hard: bool) -> dict:
    cmd = ["python3", str(validator), "--json"]
    if hard:
        cmd.append("--hard")
    cmd.append(path)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(proc.stdout or "{}")
    except Exception:
        return {
            "ok": proc.returncode == 0,
            "errors": [proc.stderr.strip() or "validation failed"],
            "path": path,
        }

def is_staging_name(name: str) -> bool:
    if not name.endswith(".md"):
        return False
    lowered = name.lower()
    # Align with validate_review_staging.STAGING_NAME_RE / gold-source kinds.
    if re.search(r"-pr-\d+", lowered) or re.search(r"^pr-\d+", lowered):
        return True
    if "review" not in lowered:
        return False
    return bool(
        re.search(r"-r\d+\.md$", name, re.IGNORECASE)
        or re.search(
            r"(branch-review|plan-review|rfc-review|confluence-review)",
            lowered,
        )
    )

def repo_root() -> Path | None:
    try:
        root = subprocess.check_output(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return Path(root)
    except (subprocess.CalledProcessError, OSError):
        return None

def current_branch() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, OSError):
        return None

def newest_staging(root: Path, branch: str | None) -> Path | None:
    reviews = root / "docs" / "history" / "reviews"
    facts = root / ".ai-playbook" / "facts.md"
    if facts.is_file():
        text = facts.read_text(encoding="utf-8", errors="replace")
        match = re.search(r'^reviews_dir\s*=\s*"([^"]+)"', text, re.MULTILINE)
        if match:
            reviews = (root / match.group(1)).resolve()
    if not reviews.is_dir():
        return None
    slug = (branch or "").lower().replace("/", "-")
    candidates = [p for p in reviews.glob("*.md") if is_staging_name(p.name)]
    if slug:
        scoped = [p for p in candidates if slug in p.name.lower()]
        if scoped:
            candidates = scoped
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)

def format_issues(result: dict) -> str:
    errors = result.get("errors") or []
    warnings = result.get("warnings") or []
    parts = []
    if errors:
        parts.append("errors: " + "; ".join(errors))
    if warnings:
        parts.append("warnings: " + "; ".join(warnings))
    return "; ".join(parts) if parts else "review-staging validation failed"

if mode == "edit":
    file_path = None
    top_level = payload.get("file_path")
    if isinstance(top_level, str):
        file_path = resolve_path(top_level)
    if not file_path:
        ti = payload.get("tool_input")
        if isinstance(ti, dict):
            for key in ("filePath", "file_path", "path"):
                value = ti.get(key)
                if isinstance(value, str):
                    file_path = resolve_path(value)
                    break
    if not file_path:
        print("{}")
        raise SystemExit(0)
    name = Path(file_path).name
    if not is_staging_name(name):
        print("{}")
        raise SystemExit(0)
    if not Path(file_path).is_file():
        print("{}")
        raise SystemExit(0)
    result = run_validate(file_path, hard=False)
    if result.get("ok"):
        print("{}")
        raise SystemExit(0)
    msg = (
        "Review staging doc incomplete after edit. "
        f"{format_issues(result)}. "
        "Complete per review-staging: Metadata, Review Statistics (Panel), "
        "Findings with #### Comment and #### Analysis for each Medium+ item."
    )
    print(json.dumps({"additional_context": msg}))
    raise SystemExit(0)

if mode == "commit":
    command = payload.get("command")
    if not isinstance(command, str):
        print(json.dumps({"permission": "allow"}))
        raise SystemExit(0)
    if not re.search(r"git\b", command) or not re.search(r"\bcommit\b", command):
        print(json.dumps({"permission": "allow"}))
        raise SystemExit(0)
    if not re.search(r"(?i)review-loop|review loop", command):
        print(json.dumps({"permission": "allow"}))
        raise SystemExit(0)
    root = repo_root()
    branch = current_branch()
    if root is None:
        print(json.dumps({"permission": "allow"}))
        raise SystemExit(0)
    target = newest_staging(root, branch)
    if target is None:
        print(json.dumps({"permission": "allow"}))
        raise SystemExit(0)
    result = run_validate(str(target), hard=True)
    if result.get("ok"):
        print(json.dumps({"permission": "allow"}))
        raise SystemExit(0)
    user_message = (
        f"Review-loop commit blocked: staging doc {target.name} fails review-staging validation."
    )
    agent_message = (
        f"Fix {target} before commit. {format_issues(result)}. "
        "Run: python3 ~/.ai-playbook/scripts/validate_review_staging.py --hard "
        f"\"{target}\""
    )
    print(
        json.dumps(
            {
                "permission": "deny",
                "user_message": user_message,
                "agent_message": agent_message,
            }
        )
    )
    raise SystemExit(0)

if mode == "stop":
    root = repo_root()
    branch = current_branch()
    if root is None or not branch:
        print("{}")
        raise SystemExit(0)
    target = newest_staging(root, branch)
    if target is None:
        print("{}")
        raise SystemExit(0)
    age_s = __import__("time").time() - target.stat().st_mtime
    if age_s > 7200:
        print("{}")
        raise SystemExit(0)
    result = run_validate(str(target), hard=True)
    if result.get("ok"):
        print("{}")
        raise SystemExit(0)
    followup = (
        f"Before ending: complete review staging doc {target.name}. "
        f"{format_issues(result)}. "
        "Required: full Review Statistics, per-finding Comment/Analysis, then re-run validator."
    )
    print(json.dumps({"followup_message": followup}))
    raise SystemExit(0)

print("{}")
PY

exit 0
