#!/usr/bin/env bash
# Confluence mirror validation and ephemeral docs/tmp cleanup.
# Used by done Step 2.65 and docs-branch Step 2 (worktree pass).
set -euo pipefail

MANIFEST_DEFAULT="docs/maintenance/confluence-sync-manifest.json"
MIRROR_DIR_DEFAULT="docs/history/context/confluence"

usage() {
  cat <<'EOF'
Usage: confluence-mirror-hygiene.sh <command> [args...]

Commands:
  audit-cf-out [root]      Classify each docs/tmp/*-cf-out.md before deletion:
                           STALE (safe to remove), NEEDS_UPGRADE (promote to hierarchy
                           first), or UNMAPPED (manual routing). Exit 1 when upgrade
                           or mapping is required.
  cleanup [root]           Remove __pycache__ always; remove *-cf-out.md only when
                           audit-cf-out marks them STALE. Exit 1 if promotion pending.
  validate [root]          Validate confluence-sync-manifest.json and mirror frontmatter.
  docs-worktree-prune <wt> Prune stale ephemeral tmp from docs-branch worktree when absent
                           from live checkout (only STALE-classified cf-out per live audit).
  --selftest               Run fixture checks for audit-cf-out classification (exit 0/1).

Promotion targets (docs hierarchy, in order):
  1. docs/history/context/confluence/{page_id}-{slug}.md (verbatim wiki mirror + frontmatter)
  2. layer2_targets from confluence-sync-manifest.json for that page
  3. Engineering spike sync ledgers (for example ADR-46 Confluence sync ledger)

Never delete *-cf-out.md until audit says STALE or content was promoted.
EOF
}

repo_root() {
  local root="${1:-.}"
  (cd "$root" && git rev-parse --show-toplevel 2>/dev/null) || echo "$root"
}

is_ephemeral_tmp_rel() {
  local rel="$1"
  case "$rel" in
    docs/tmp/*-cf-out.md) return 0 ;;
    docs/tmp/*/__pycache__/*) return 0 ;;
    docs/tmp/__pycache__/*) return 0 ;;
    *) return 1 ;;
  esac
}

cmd_audit_cf_out() {
  local root
  root="$(repo_root "${1:-.}")"
  python3 - "$root" <<'PY'
import json, re, sys
from pathlib import Path

root = Path(sys.argv[1])
tmp_dir = root / "docs/tmp"
manifest_path = root / "docs/maintenance/confluence-sync-manifest.json"

cf_files = sorted(tmp_dir.glob("*-cf-out.md")) if tmp_dir.is_dir() else []
if not cf_files:
    print("confluence-mirror-hygiene: audit-cf-out ok (no *-cf-out.md files)")
    sys.exit(0)

pages = []
if manifest_path.is_file():
    pages = json.loads(manifest_path.read_text()).get("pages") or []

PREFIX_ALIASES = {
    "adr46": "4554523700",
    "phase1": "4553638457",
}

def norm(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    return text

def body_without_frontmatter(text: str) -> str:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].lstrip()
    return text

def headings(text: str) -> set[str]:
    return {m.group(1).strip().lower() for m in re.finditer(r"^##+ (.+)$", text, re.M)}

def map_page(prefix: str):
    pid = PREFIX_ALIASES.get(prefix)
    if pid:
        for page in pages:
            if str(page.get("page_id")) == pid:
                return page
    prefix_l = prefix.lower()
    for page in pages:
        slug = (page.get("slug") or "").lower()
        title = (page.get("title") or "").lower()
        if prefix_l in slug or prefix_l in re.sub(r"[^a-z0-9]+", "", title):
            return page
    return None

def mirror_body(page) -> tuple[str | None, str | None]:
    local_path = page.get("local_path")
    if not local_path:
        return None, None
    full = root / local_path
    if not full.is_file():
        return None, local_path
    return body_without_frontmatter(full.read_text(encoding="utf-8", errors="replace")), local_path

def layer2_paths(page) -> list[str]:
    return list(page.get("layer2_targets") or [])

blocked = False
for cf in cf_files:
    prefix = cf.stem.replace("-cf-out", "")
    cf_text = cf.read_text(encoding="utf-8", errors="replace")
    cf_body = body_without_frontmatter(cf_text)
    cf_norm = norm(cf_body)

    page = map_page(prefix)
    if not page:
        print(f"{cf.relative_to(root)}: UNMAPPED (no manifest page for prefix '{prefix}'; route to docs hierarchy manually)")
        blocked = True
        continue

    page_id = str(page.get("page_id", ""))
    mirror_text, mirror_path = mirror_body(page)
    targets = layer2_paths(page)
    target_hint = mirror_path or (targets[0] if targets else f"docs/history/context/confluence/{page_id}-<slug>.md")

    if mirror_text is None:
        print(f"{cf.relative_to(root)}: NEEDS_UPGRADE -> create or refresh mirror {target_hint} (manifest page {page_id})")
        blocked = True
        continue

    mirror_norm = norm(mirror_text)
    cf_heads = headings(cf_body)
    mirror_heads = headings(mirror_text)
    missing_heads = sorted(h for h in cf_heads if h not in mirror_heads)

    stale_markers = ("~1m", "nigeria", "not nigeria", "1m users")
    cf_lower = cf_body.lower()
    mirror_lower = mirror_text.lower()
    cf_has_stale = any(m in cf_lower for m in stale_markers)
    mirror_fixed = any(m not in mirror_lower for m in stale_markers if m in cf_lower)

    if cf_norm == mirror_norm:
        print(f"{cf.relative_to(root)}: STALE (matches mirror {mirror_path})")
        continue

    if cf_norm and cf_norm in mirror_norm and len(mirror_norm) > len(cf_norm) * 1.05:
        print(f"{cf.relative_to(root)}: STALE (mirror {mirror_path} is superset)")
        continue

    if cf_has_stale and mirror_fixed:
        print(f"{cf.relative_to(root)}: STALE (mirror {mirror_path} supersedes outdated scale/pilot wording)")
        continue

    if missing_heads:
        print(f"{cf.relative_to(root)}: NEEDS_UPGRADE -> merge sections {missing_heads!r} into {target_hint} before delete")
        blocked = True
        continue

    if len(cf_norm) > len(mirror_norm) * 1.1:
        print(f"{cf.relative_to(root)}: NEEDS_UPGRADE -> mirror {mirror_path} shorter; promote newer cf-out body first")
        blocked = True
        continue

    # Fail closed: similar-length same-heading rewrites are not proven STALE.
    print(f"{cf.relative_to(root)}: NEEDS_UPGRADE -> body differs from {mirror_path}; promote or confirm before delete")
    blocked = True
    continue

if blocked:
    print("confluence-mirror-hygiene: audit-cf-out BLOCKED (promote to docs hierarchy before cleanup)")
    sys.exit(1)

print("confluence-mirror-hygiene: audit-cf-out ok (all cf-out files safe to remove)")
PY
}

cmd_cleanup() {
  local root
  root="$(repo_root "${1:-.}")"

  if ! cmd_audit_cf_out "$root"; then
    echo "confluence-mirror-hygiene: cleanup aborted (run audit-cf-out, promote content, re-run)" >&2
    exit 1
  fi

  local removed=0
  while IFS= read -r -d '' path; do
    rm -rf -- "$path"
    echo "confluence-mirror-hygiene: removed $path"
    removed=$((removed + 1))
  done < <(find "$root/docs/tmp" \( -name '*-cf-out.md' -o -path '*/__pycache__/*' \) -print0 2>/dev/null || true)

  if [ "$removed" -eq 0 ]; then
    echo "confluence-mirror-hygiene: cleanup ok (no ephemeral tmp files)"
  fi
}

cmd_validate() {
  local root
  root="$(repo_root "${1:-.}")"
  local manifest="${root}/${MANIFEST_DEFAULT}"
  local fail=0

  if [ ! -f "$manifest" ]; then
    echo "confluence-mirror-hygiene: no manifest (skip validate)"
    exit 0
  fi

  python3 - "$manifest" "$root" <<'PY' || fail=1
import json, re, sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
root = Path(sys.argv[2])
data = json.loads(manifest_path.read_text())
pages = data.get("pages") or []
errors = []

required = {
    "confluence_page_id", "confluence_title", "confluence_version",
    "confluence_url", "space_key", "synced_at", "sync_status", "layer2_targets",
}

for page in pages:
    page_id = str(page.get("page_id", ""))
    local_path = page.get("local_path")
    if not local_path:
        errors.append(f"manifest page {page_id}: missing local_path")
        continue
    full = root / local_path
    if not full.is_file():
        errors.append(f"manifest page {page_id}: missing mirror file {local_path}")
        continue
    if "docs/history/context/confluence/" not in local_path.replace("\\", "/"):
        continue
    text = full.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        errors.append(f"{local_path}: missing YAML frontmatter")
        continue
    parts = text.split("---", 2)
    if len(parts) < 3:
        errors.append(f"{local_path}: truncated frontmatter")
        continue
    fm = parts[1]
    if re.search(r"^path:", fm, re.M):
        errors.append(f"{local_path}: non-standard frontmatter key 'path' (use confluence_page_id)")
    for key in required:
        if not re.search(rf"^{re.escape(key)}:", fm, re.M):
            errors.append(f"{local_path}: missing frontmatter key {key}")
    basename = full.name
    if page_id and not basename.startswith(f"{page_id}-"):
        errors.append(f"{local_path}: filename should start with {page_id}-")

readme = root / "docs/history/context/confluence/README.md"
if readme.is_file() and pages:
    body = readme.read_text(encoding="utf-8", errors="replace")
    for page in pages:
        pid = str(page.get("page_id", ""))
        if pid and pid not in body:
            errors.append(f"confluence README missing page id {pid}")

if errors:
    print("confluence-mirror-hygiene: validate FAILED")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print(f"confluence-mirror-hygiene: validate ok ({len(pages)} manifest pages)")
PY

  exit "$fail"
}

cmd_docs_worktree_prune() {
  local worktree="${1:?worktree path required}"
  local live_root
  live_root="$(repo_root ".")"
  local pruned=0

  if [ ! -d "${worktree}/docs/tmp" ]; then
    exit 0
  fi

  # Only prune cf-out on worktree when live checkout audit would allow cleanup.
  local cf_audit_ok=0
  if (cd "$live_root" && "${CONFLUENCE_MIRROR_HYGIENE_SCRIPT:-${HOME}/.ai-playbook/scripts/confluence-mirror-hygiene.sh}" audit-cf-out) >/dev/null 2>&1; then
    cf_audit_ok=1
  elif [ ! -d "${live_root}/docs/tmp" ] || ! find "${live_root}/docs/tmp" -maxdepth 1 -name '*-cf-out.md' -print -quit 2>/dev/null | grep -q .; then
    cf_audit_ok=1
  fi

  while IFS= read -r -d '' wt_file; do
    rel="${wt_file#"${worktree}/"}"
    is_ephemeral_tmp_rel "$rel" || continue
    live_file="${live_root}/${rel}"
    if [ -e "$live_file" ]; then
      continue
    fi
    case "$rel" in
      docs/tmp/*-cf-out.md)
        [ "$cf_audit_ok" -eq 1 ] || continue
        ;;
    esac
    rm -rf -- "$wt_file"
    echo "docs-branch: pruned stale ephemeral tmp ${rel}"
    pruned=$((pruned + 1))
    (
      cd "$worktree"
      git add -f "$rel" 2>/dev/null || true
    )
  done < <(find "${worktree}/docs/tmp" \( -name '*-cf-out.md' -o -path '*/__pycache__/*' \) -print0 2>/dev/null || true)

  if [ "$pruned" -eq 0 ]; then
    echo "docs-branch: ephemeral tmp prune ok (nothing stale)"
  fi
}

cmd_selftest() {
  local script_dir tmp fail=0
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  tmp="$(mktemp -d)"
  cleanup_tmp() { rm -rf "$tmp"; }
  trap cleanup_tmp EXIT

  mkdir -p "$tmp/docs/tmp" "$tmp/docs/history/context/confluence" "$tmp/docs/maintenance"
  cat >"$tmp/docs/maintenance/confluence-sync-manifest.json" <<'JSON'
{
  "pages": [
    {
      "page_id": "1001",
      "slug": "demo-page",
      "title": "Demo Page",
      "local_path": "docs/history/context/confluence/1001-demo-page.md",
      "layer2_targets": []
    }
  ]
}
JSON

  # Case 1: exact match -> STALE, audit exit 0
  printf '%s\n' '# Same' >"$tmp/docs/history/context/confluence/1001-demo-page.md"
  printf '%s\n' '# Same' >"$tmp/docs/tmp/demo-page-cf-out.md"
  if ! out="$("$script_dir/confluence-mirror-hygiene.sh" audit-cf-out "$tmp" 2>&1)"; then
    echo "selftest FAIL: exact match should be STALE/exit 0" >&2
    echo "$out" >&2
    fail=1
  elif ! printf '%s\n' "$out" | grep -q 'STALE (matches mirror'; then
    echo "selftest FAIL: exact match missing STALE label" >&2
    echo "$out" >&2
    fail=1
  fi

  # Case 2: cf-out has extra heading -> NEEDS_UPGRADE, exit 1
  rm -f "$tmp/docs/tmp/"*-cf-out.md
  printf '%s\n' '# Title' >"$tmp/docs/history/context/confluence/1001-demo-page.md"
  printf '%s\n' '# Title' '' '## Extra' 'body' >"$tmp/docs/tmp/demo-page-cf-out.md"
  if out="$("$script_dir/confluence-mirror-hygiene.sh" audit-cf-out "$tmp" 2>&1)"; then
    echo "selftest FAIL: extra heading should NEEDS_UPGRADE/exit 1" >&2
    echo "$out" >&2
    fail=1
  elif ! printf '%s\n' "$out" | grep -q 'NEEDS_UPGRADE'; then
    echo "selftest FAIL: extra heading missing NEEDS_UPGRADE" >&2
    echo "$out" >&2
    fail=1
  fi

  # Case 3: same headings, similar length, different body -> NEEDS_UPGRADE (fail-closed fallthrough)
  rm -f "$tmp/docs/tmp/"*-cf-out.md
  printf '%s\n' '# Title' 'mirror body aaa' >"$tmp/docs/history/context/confluence/1001-demo-page.md"
  printf '%s\n' '# Title' 'cf-out body bbb' >"$tmp/docs/tmp/demo-page-cf-out.md"
  if out="$("$script_dir/confluence-mirror-hygiene.sh" audit-cf-out "$tmp" 2>&1)"; then
    echo "selftest FAIL: body diff should NEEDS_UPGRADE/exit 1" >&2
    echo "$out" >&2
    fail=1
  elif ! printf '%s\n' "$out" | grep -q 'NEEDS_UPGRADE'; then
    echo "selftest FAIL: body diff missing NEEDS_UPGRADE" >&2
    echo "$out" >&2
    fail=1
  fi

  # Case 4: unmapped prefix with no matching mirror -> UNMAPPED
  rm -f "$tmp/docs/tmp/"*-cf-out.md
  printf '%s\n' '# Orphan' >"$tmp/docs/tmp/orphan-cf-out.md"
  if out="$("$script_dir/confluence-mirror-hygiene.sh" audit-cf-out "$tmp" 2>&1)"; then
    echo "selftest FAIL: orphan cf-out should not exit 0" >&2
    echo "$out" >&2
    fail=1
  elif ! printf '%s\n' "$out" | grep -q 'UNMAPPED'; then
    echo "selftest FAIL: orphan cf-out missing UNMAPPED" >&2
    echo "$out" >&2
    fail=1
  fi

  if [ "$fail" -eq 0 ]; then
    echo "confluence-mirror-hygiene: --selftest ok"
    exit 0
  fi
  echo "confluence-mirror-hygiene: --selftest FAILED" >&2
  exit 1
}

main() {
  local cmd="${1:-}"
  shift || true
  case "$cmd" in
    audit-cf-out) cmd_audit_cf_out "$@" ;;
    cleanup) cmd_cleanup "$@" ;;
    validate) cmd_validate "$@" ;;
    docs-worktree-prune) cmd_docs_worktree_prune "$@" ;;
    --selftest|selftest) cmd_selftest ;;
    -h|--help|help|"") usage ;;
    *) echo "Unknown command: $cmd" >&2; usage >&2; exit 2 ;;
  esac
}

main "$@"
