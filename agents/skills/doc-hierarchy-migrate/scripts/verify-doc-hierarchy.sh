#!/usr/bin/env bash
# verify-doc-hierarchy.sh — migration gates for doc-hierarchy-migrate
# Usage: verify-doc-hierarchy.sh [step2|step3|step4|step5|step6|audit|full|self-test|stale-bootstrap-test]
# Note: step6 and full are aliases (both run gate_step6); prefer full in skill docs.
# Env: REPO_ROOT (default .), REQUIRE_CALLER_CATALOG (0|1), CLASSIFIED_COMPANY_GUIDELINES (0|1)

set -uo pipefail

PHASE="${1:-full}"
REPO_ROOT="${REPO_ROOT:-.}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_INSTALL="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT" || exit 2
git rev-parse --git-dir >/dev/null 2>&1 || { echo 'FATAL: REPO_ROOT is not a git repository'; exit 2; }
REPO_TOP=$(git rev-parse --show-toplevel)
if [ "$(pwd -P)" != "$(cd "$REPO_TOP" && pwd -P)" ]; then
  echo "FATAL: REPO_ROOT must be the git repository root (toplevel: $REPO_TOP)" >&2
  exit 2
fi

echo "verify-doc-hierarchy: REPO_ROOT=$REPO_TOP phase=$PHASE" >&2

if [ -n "${EXPECTED_REPO_ROOT:-}" ]; then
  expected_abs=$(cd "$EXPECTED_REPO_ROOT" 2>/dev/null && pwd -P) || expected_abs=""
  if [ -z "$expected_abs" ] || [ "$expected_abs" != "$(pwd -P)" ]; then
    echo "FATAL: REPO_ROOT ($REPO_TOP) does not match EXPECTED_REPO_ROOT ($EXPECTED_REPO_ROOT)" >&2
    exit 2
  fi
fi

if [ "$PHASE" != self-test ] && [ "$PHASE" != stale-bootstrap-test ] && [ "${VERIFY_ALLOW_SKILL_INSTALL:-0}" != 1 ]; then
  repo_top_p=$(cd "$REPO_TOP" && pwd -P)
  skill_install_p=$(cd "$SKILL_INSTALL" && pwd -P)
  if [ "$repo_top_p" = "$skill_install_p" ]; then
    echo "FATAL: REPO_ROOT is the skill install directory ($REPO_TOP). Set REPO_ROOT to the service repo root." >&2
    exit 2
  fi
  if [ -f "$REPO_TOP/agents/skills/doc-hierarchy-migrate/SKILL.md" ] && \
     [ -f "$REPO_TOP/agents/skills/bootstrap-ai-playbook/SKILL.md" ]; then
    echo "FATAL: REPO_ROOT appears to be the instructions/skills repository ($REPO_TOP), not a service repo. Set REPO_ROOT to the service repo root." >&2
    exit 2
  fi
fi

if [ "$PHASE" != self-test ] && [ "$PHASE" != stale-bootstrap-test ] && [ ! -d docs ]; then
  echo "FATAL: REPO_ROOT has no docs/ directory — likely not a service repo ($REPO_TOP)" >&2
  exit 2
fi

validate_external_docs_domain() {
  local d="${EXTERNAL_DOCS_DOMAIN:-}"
  [ -z "$d" ] && return 0
  if command -v rg >/dev/null 2>&1; then
    if ! printf '%s' "$d" | rg -q '^[a-zA-Z0-9.-]+$'; then
      echo "FATAL: EXTERNAL_DOCS_DOMAIN contains invalid characters: $d" >&2
      exit 2
    fi
  elif ! printf '%s' "$d" | grep -Eq '^[a-zA-Z0-9.-]+$'; then
    echo "FATAL: EXTERNAL_DOCS_DOMAIN contains invalid characters: $d" >&2
    exit 2
  fi
}

FAILS=0
fail() { echo "FAIL: $1"; FAILS=$((FAILS + 1)); }
warn() { echo "WARN: $1"; }

gate_step2() {
  echo "=== Step 2 gate ==="
  local f
  for f in project-guidelines project-decisions glossary; do
    test ! -f "docs/${f}.md" || fail "docs/${f}.md still at root"
    test -f "docs/maintenance/${f}.md" || fail "docs/maintenance/${f}.md missing"
  done
  test ! -f "docs/company-guidelines.md" || fail "docs/company-guidelines.md still at root"
  if [ "${CLASSIFIED_COMPANY_GUIDELINES:-0}" -eq 1 ]; then
    test -f docs/maintenance/company-guidelines.md || fail "docs/maintenance/company-guidelines.md missing (mirror classified)"
  fi
  test ! -e docs/reviews || fail "docs/reviews still at root"
  test ! -d docs/history/reviews/reviews || fail "docs/history/reviews/reviews nested (bad mv)"
  test -e docs/history/reviews || fail "docs/history/reviews missing"
  git check-ignore -q docs/history/reviews/ 2>/dev/null || fail "docs/history/reviews/ not gitignored"
  git check-ignore -q docs/tmp/ 2>/dev/null || fail "docs/tmp/ not gitignored"
  shopt -s nullglob
  for f in docs/api-for-*.md docs/*-sync*.md; do
    fail "wire contract still at docs root: $f"
  done
  shopt -u nullglob
  test ! -d docs/plans || fail "docs/plans still at root"
  test -d docs/history/plans || warn "docs/history/plans/ missing (plans_dir target)"
  test ! -d docs/context || fail "docs/context still at root"
  test ! -d docs/history/investigations/context || fail "docs/history/investigations/context present (use docs/history/context/)"
  test ! -d docs/proposals || fail "docs/proposals still at root"
  test ! -f docs/api-reference.md || fail "docs/api-reference.md still at root"
  test ! -d docs/examples || fail "docs/examples still at root"
  test ! -d docs/rfcs || fail "docs/rfcs/ still at root (RFCs belong in docs/history/feature-notes/)"
  test ! -d docs/history/examples || fail "docs/history/examples still present"
  test ! -d docs/dashboards || fail "docs/dashboards still at root (use docs/maintenance/dashboards/)"
  test ! -f scripts/verify-doc-hierarchy.sh || fail "scripts/verify-doc-hierarchy.sh vendored in service repo (run gates from doc-hierarchy-migrate skill only)"
  if [ "${REQUIRE_CALLER_CATALOG:-0}" -eq 1 ]; then
    test -f docs/maintenance/api-reference.md || fail "docs/maintenance/api-reference.md missing (required)"
  fi
}

gate_step3() {
  echo "=== Step 3 gate ==="
  local d base
  for d in docs/*/; do
    [ -d "$d" ] || continue
    base=$(basename "$d")
    case "$base" in architecture|maintenance|history|tmp) continue ;; esac
    fail "module-split docs dir still present: docs/$base/"
  done
}

gate_step4() {
  echo "=== Step 4 gate ==="
  local d
  if [ -d docs/history/feature-notes ]; then
    while IFS= read -r d; do
      fail "nested feature-notes dir: $d"
    done < <(find docs/history/feature-notes -mindepth 1 -maxdepth 1 -type d ! -name proposals 2>/dev/null)
    while IFS= read -r d; do
      fail "deep nested feature-notes dir: $d"
    done < <(find docs/history/feature-notes -mindepth 2 -type d ! -path '*/proposals/*' 2>/dev/null)
  fi
}

gate_step5() {
  gate_step5_committed
  gate_step5_runtime
}

gate_step5_committed() {
  echo "=== Step 5 gate (committed artifacts) ==="
  test -f AGENTS.md || fail "AGENTS.md missing"
  head -1 AGENTS.md | grep -q '^# Instructions' || fail "AGENTS.md H1 must be '# Instructions'"
  grep -q 'Documentation Hierarchy' AGENTS.md || fail "AGENTS.md missing Documentation Hierarchy subsection"
  grep -qE '\.ai-playbook/facts' AGENTS.md || fail "AGENTS.md missing .ai-playbook/facts path"
  grep -q 'docs/maintenance/project-guidelines' AGENTS.md || fail "AGENTS.md missing docs/maintenance/project-guidelines path"
  grep -qE '^/\.ai-playbook/' .gitignore 2>/dev/null || fail ".gitignore missing /.ai-playbook/ rule (repo root only)"
  if git ls-files --error-unmatch docs/maintenance/facts.md >/dev/null 2>&1; then
    fail "docs/maintenance/facts.md still committed (complete Step 5b: promote FACTs, git rm legacy facts)"
  fi
  if git ls-files --error-unmatch docs/facts.md >/dev/null 2>&1; then
    fail "docs/facts.md still committed (complete Step 5b: git rm legacy root facts)"
  fi
  test -f docs/maintenance/project-guidelines.md || fail "docs/maintenance/project-guidelines.md missing"
  grep -q 'Documentation Hierarchy' docs/maintenance/project-guidelines.md || fail "project-guidelines missing Documentation Hierarchy section"
  grep -qE 'plans_dir|docs/history/plans/' docs/maintenance/project-guidelines.md || fail "project-guidelines missing resolved plans path"
  test -L CLAUDE.md && [ "$(readlink CLAUDE.md)" = "AGENTS.md" ] || warn "CLAUDE.md should symlink to AGENTS.md"
  if [ -f .cursor/rules/instructions.mdc ]; then
    grep -q '@AGENTS.md' .cursor/rules/instructions.mdc || warn "Cursor instructions.mdc should @-include AGENTS.md"
  fi
}

toml_value_for_key() {
  local file="$1" key="$2"
  extract_opening_toml_body "$file" | sed -n "s/^${key}[[:space:]]*=[[:space:]]*\"\\([^\"]*\\)\".*/\\1/p" | head -1
}

validate_opening_toml_facts() {
  local file="$1"
  local key dir
  head -20 "$file" | grep -q '^```toml' || fail ".ai-playbook/facts.md missing opening TOML fence"
  for key in plans_dir reviews_dir tmp_dir facts_path bootstrap_version; do
    toml_value_for_key "$file" "$key" | grep -q . \
      || fail ".ai-playbook/facts.md missing required TOML key: $key"
  done
  for key in plans_dir reviews_dir tmp_dir; do
    dir=$(toml_value_for_key "$file" "$key")
    dir="${dir%/}/"
    [ -d "$dir" ] || fail ".ai-playbook/facts.md stale or missing directory for $key: $dir"
  done
}

gate_step5_runtime() {
  echo "=== Step 5 gate (local runtime — run bootstrap after Step 5b) ==="
  test -f .ai-playbook/facts.md || fail ".ai-playbook/facts.md missing (complete Step 5b + bootstrap-ai-playbook)"
  git check-ignore -q .ai-playbook/ 2>/dev/null || fail ".ai-playbook/ not gitignored"
  git check-ignore -q .ai-playbook/facts.md 2>/dev/null || fail ".ai-playbook/facts.md not gitignored"
  if git ls-files --error-unmatch .ai-playbook/ >/dev/null 2>&1; then
    fail ".ai-playbook/ has tracked files (git rm --cached before bootstrap)"
  fi
  validate_opening_toml_facts ".ai-playbook/facts.md"
}

gate_step6_content_hygiene() {
  if ! command -v rg >/dev/null 2>&1; then
    return
  fi
  local scan_roots=(docs/maintenance docs/architecture)
  rg -q -i '(AKIA[0-9A-Z]{16}|sk_live_[0-9a-zA-Z]{20,}|-----BEGIN (RSA |EC )?PRIVATE KEY-----|Bearer [a-zA-Z0-9._-]{20,})' \
    "${scan_roots[@]}" 2>/dev/null && \
    fail "possible live credential pattern in Layer 2 docs (use placeholders)"
}

gate_step6_finish() {
  validate_external_docs_domain
  if command -v rg >/dev/null 2>&1; then
    local canon_roots=(AGENTS.md README.md docs/architecture docs/maintenance docs/README.md)
    rg -q 'docs/(project-guidelines|project-decisions|glossary|facts|company-guidelines)\.md' \
      "${canon_roots[@]}" 2>/dev/null && \
      fail "legacy root guideline paths still referenced in canonical docs"
    rg -q 'docs/reviews/' "${canon_roots[@]}" 2>/dev/null && \
      fail "docs/reviews/ still referenced (use docs/history/reviews/)"
    rg -q 'docs/examples/|docs/history/examples/' "${canon_roots[@]}" docs/maintenance/project-guidelines.md 2>/dev/null && \
      fail "docs/examples/ or docs/history/examples/ still referenced"
    rg -q 'docs/dashboards/' "${canon_roots[@]}" docs/maintenance/project-guidelines.md 2>/dev/null && \
      fail "docs/dashboards/ still referenced (use docs/maintenance/dashboards/)"
    rg -q 'docs/rfcs/' "${canon_roots[@]}" docs/maintenance/project-guidelines.md 2>/dev/null && \
      fail "docs/rfcs/ still referenced (use docs/history/feature-notes/)"
    rg -q 'docs/context/|docs/plans/|docs/proposals/' "${canon_roots[@]}" 2>/dev/null && \
      fail "legacy docs/context, docs/plans, or docs/proposals still referenced in canonical docs"
    rg -q 'docs/history/investigations/context' "${canon_roots[@]}" 2>/dev/null && \
      fail "docs/history/investigations/context referenced (canonical path is docs/history/context/)"
    rg -q '^# Moved to|^This document moved to' docs/ --glob '!docs/history/**' --glob '!docs/tmp/**' 2>/dev/null && \
      fail "stub redirect still present under docs/"
    rg 'docs/history/feature-notes/[a-zA-Z0-9_-]+/' docs/architecture docs/maintenance AGENTS.md 2>/dev/null \
      | grep -v 'feature-notes/proposals/' | rg -q . && \
      fail "nested history/feature-notes path referenced in canonical docs"
    rg -q 'docs/(context|plans|proposals)/' --glob '*.java' --glob '*.kt' --glob '*.{yml,yaml,sh,md}' . \
      --glob '!docs/history/**' --glob '!docs/tmp/**' --glob '!docs/history/reviews/**' 2>/dev/null && \
      fail "legacy docs/context, docs/plans, or docs/proposals referenced outside history/"
    if rg 'docs/[a-z][a-z0-9-]+/' --glob '*.java' --glob '*.kt' --glob '*.py' --glob '*.{yml,yaml,sh,md}' . 2>/dev/null \
      | rg -v 'docs/(architecture|maintenance|history|tmp)/' \
      | rg -v 'https?://[^/]*/docs/' \
      | rg -v '[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/docs/' \
      | rg -Fv "${EXTERNAL_DOCS_DOMAIN:-no-match-placeholder}/docs/" \
      | rg -v 'firebase\.google\.com/docs/' | rg -q .; then
      fail "rogue docs/<module>/ path in source or config"
    fi
  else
    fail "rg (ripgrep) required for step6 reference scans"
  fi

  gate_step6_content_hygiene

  local f
  for f in system-overview domain-model integrations api-contracts event-flows operational-guides troubleshooting; do
    test -f "docs/architecture/${f}.md" || fail "docs/architecture/${f}.md missing"
  done
  local arch_count
  arch_count=$(ls -1 docs/architecture/*.md 2>/dev/null | wc -l | tr -d ' ')
  [ "$arch_count" -ge 7 ] || fail "docs/architecture/ must have at least 7 .md files (found $arch_count)"

  test ! -d docs/examples || fail "docs/examples at root"
  test ! -d docs/history/examples || fail "docs/history/examples present"
  test ! -e docs/reviews || fail "docs/reviews at root"
  test ! -f docs/history/doc-migration.md || fail "doc-migration.md metainfo present"

  test -d docs/history/plans || fail "docs/history/plans/ missing (plans_dir target)"
  test -d docs/history/context || fail "docs/history/context/ missing"
  test -d docs/history/investigations || fail "docs/history/investigations/ missing"
  test -d docs/history/migrations || fail "docs/history/migrations/ missing"
  test -d docs/history/feature-notes || fail "docs/history/feature-notes/ missing"

  if [ -f docs/README.md ]; then
    rg -q '^\| \[architecture/|^\| \[maintenance/' docs/README.md 2>/dev/null && fail "README has per-file catalog tables"
    rg -q '^\| Document \| Purpose \|' docs/README.md 2>/dev/null && fail "README has doc inventory table"
    grep -q '## What this service does' docs/README.md || fail "README missing Layer 1 section"
    grep -q '## Main responsibilities' docs/README.md || fail "README missing Layer 1 section"
  else
    fail "docs/README.md missing"
  fi
}

gate_step6() {
  echo "=== Step 6 gate ==="
  gate_step2
  gate_step3
  gate_step4
  gate_step5
  gate_step6_finish
}

gate_audit() {
  echo "=== Repair audit (all phases) ==="
  gate_step2
  gate_step3
  gate_step4
  gate_step5
  echo "=== Step 6 reference and layout checks (audit) ==="
  gate_step6_finish
  echo "Audit complete. Map each FAIL line to the owning step in doc-hierarchy-migrate SKILL.md."
}

bootstrap_fixture_legacy_mini() {
  local root="$1"
  mkdir -p "$root/docs/plans"
  cat > "$root/docs/project-guidelines.md" <<'EOF'
# Legacy root guidelines (fixture)
EOF
  cat > "$root/docs/plans/sample-plan.md" <<'EOF'
# Sample plan (fixture)
EOF
}

bootstrap_fixture_expected_mini() {
  local root="$1" topic f
  mkdir -p "$root/docs/maintenance" "$root/docs/architecture" "$root/.ai-playbook" "$root/docs/tmp"
  cat > "$root/AGENTS.md" <<'EOF'
# Instructions

## Documentation Hierarchy

- **Start here:** `docs/README.md` (Layer 1 — concise service overview; not a file catalog).
- **Facts / guidelines:** `repo_facts_rel` → `.ai-playbook/facts.md` (gitignored repo agent runtime); `project_guidelines_rel` → `docs/maintenance/project-guidelines.md`.
- **Shared knowledge:** `docs/architecture/`, `docs/maintenance/` (Layer 2) — update in the same PR/session when behavior, contracts, integrations, or ops change; see `docs/maintenance/project-guidelines.md` Documentation Hierarchy section.
- **Historical context:** `docs/history/` (Layer 3) — reference only; active plans under `docs/history/plans/`, archives under `docs/history/plans/completed/`.
- **LLM-only:** `docs/tmp/` at root; gitignored `docs/history/reviews/` — not canonical human Layer 2.
- **Wire catalogs (Layer 2):** `docs/maintenance/api-reference.md` when the service exposes HTTP APIs; other wire contracts under `docs/maintenance/` (BFF, sync, admin FE shapes). Do not recreate a separate examples tree or per-endpoint files under `maintenance/`; use `maintenance/api-reference.md` for caller samples.
- **Doc path resolution:** Other skills resolve `{plans_dir}`, `{reviews_dir}`, `{tmp_dir}`, `{proposals_dir}`, `{rfcs_dir}`, `{caller_catalog}` from `.ai-playbook/facts.md` TOML (via `using-skills` Step 0) and project guidelines — not from hardcoded skill defaults.
- Use `doc-hierarchy-migrate` to relocate flat or module-split docs; use `doc-hierarchy-upkeep` for Layer 1/2 after migration; merge durable knowledge into topic-based `architecture/`, not `docs/<module>/` trees.
EOF
  cat > "$root/.ai-playbook/facts.md" <<'EOF'
```toml
plans_dir = "docs/history/plans/"
reviews_dir = "docs/history/reviews/"
tmp_dir = "docs/tmp/"
facts_path = ".ai-playbook/facts.md"
bootstrap_version = "1"
```

## Related Jira tasks

- FIXTURE-1 — self-test fixture ledger entry
EOF
  cat > "$root/docs/README.md" <<'EOF'
# fixture-service

## What this service does

Minimal fixture service for verify-doc-hierarchy self-test.

## Main responsibilities

- Exercise migration gates in CI-free local verify.

## Key integrations and dependencies

- None (fixture only).

## APIs and events (high level)

- N/A for fixture.

## High-level flows

1. Self-test runs `full` gate against this layout.

## Operations

- See `architecture/operational-guides.md`.

## Where to read next

| Layer | Folder | Use for |
|-------|--------|---------|
| 2 | `architecture/` | Domain and integration topics |
| 2 | `maintenance/` | Guidelines and facts |
| 3 | `history/` | Plans and feature notes |
EOF
  cat > "$root/docs/maintenance/project-guidelines.md" <<'EOF'
# Project guidelines (fixture)

## Documentation Hierarchy

Follow the company service layout under `docs/`. Resolved paths for other skills:

| Key | Path |
|-----|------|
| plans_dir | docs/history/plans/ |
| plans_completed_dir | docs/history/plans/completed/ |
| reviews_dir | docs/history/reviews/ |
| tmp_dir | docs/tmp/ |
| proposals_dir | docs/history/feature-notes/proposals/ |
| rfcs_dir | docs/history/feature-notes/ |
| caller_catalog | docs/maintenance/api-reference.md |
EOF
  for f in glossary project-decisions; do
    cat > "$root/docs/maintenance/${f}.md" <<EOF
# ${f} (fixture)
EOF
  done
  for topic in system-overview domain-model integrations api-contracts event-flows operational-guides troubleshooting; do
    cat > "$root/docs/architecture/${topic}.md" <<EOF
# ${topic}

Fixture placeholder.
EOF
  done
}

prepare_self_test_worktree() {
  local dst="$1" kind="$2"
  rm -rf "$dst"
  mkdir -p "$dst"
  case "$kind" in
    legacy) bootstrap_fixture_legacy_mini "$dst" ;;
    expected) bootstrap_fixture_expected_mini "$dst" ;;
    *) fail "unknown self-test kind: $kind"; return 1 ;;
  esac
  mkdir -p "$dst/docs/history/plans" \
           "$dst/docs/history/context" \
           "$dst/docs/history/investigations" \
           "$dst/docs/history/migrations" \
           "$dst/docs/history/feature-notes" \
           "$dst/docs/history/reviews"
  cat > "$dst/.gitignore" <<'EOF'
/.ai-playbook/
/docs/facts.md
/docs/maintenance/facts.md
docs/history/reviews/
docs/tmp/
EOF
  git -C "$dst" init -q || { fail "could not init git repo in $(basename "$dst") worktree"; return 1; }
  git -C "$dst" add -A 2>/dev/null
  git -C "$dst" rm -r --cached .ai-playbook 2>/dev/null || true
  git -C "$dst" -c user.name=fixture -c user.email=fixture@example.com commit -qm "self-test" >/dev/null 2>&1 \
    || { fail "could not commit $(basename "$dst") worktree"; return 1; }
}

commit_self_test_worktree() {
  local work="$1" msg="$2"
  git -C "$work" add -A 2>/dev/null
  git -C "$work" -c user.name=fixture -c user.email=fixture@example.com commit -qm "$msg" >/dev/null 2>&1 \
    || { fail "could not commit $(basename "$work") worktree: $msg"; return 1; }
}

cleanup_self_test_worktrees() {
  if [ -n "${SELF_TEST_TMP_ROOT:-}" ] && [ -d "$SELF_TEST_TMP_ROOT" ]; then
    rm -rf "$SELF_TEST_TMP_ROOT"
  fi
}

extract_opening_toml_body() {
  local file="$1"
  awk '
    BEGIN { in_block=0; found=0 }
    /^```toml[[:space:]]*$/ && !found { in_block=1; found=1; next }
    in_block && /^```[[:space:]]*$/ { exit }
    in_block { print }
  ' "$file"
}

extract_prose_after_opening_toml() {
  local file="$1"
  awk '
    BEGIN { in_block=0; past_block=0; found=0 }
    /^```toml[[:space:]]*$/ && !found { in_block=1; found=1; next }
    in_block && /^```[[:space:]]*$/ { in_block=0; past_block=1; next }
    past_block { print }
  ' "$file"
}

refresh_opening_toml_preserve_prose() {
  local file="$1" new_toml="$2" prose tmp
  prose=$(extract_prose_after_opening_toml "$file")
  tmp="${file}.refresh.$$"
  {
    printf '```toml\n'
    printf '%s' "$new_toml"
    if [ -n "$new_toml" ] && [ "${new_toml: -1}" != $'\n' ]; then
      printf '\n'
    fi
    printf '```\n'
    if [ -n "$prose" ]; then
      printf '%s' "$prose"
    fi
  } > "$tmp"
  mv "$tmp" "$file"
}

gate_stale_bootstrap_test() {
  echo "=== Stale bootstrap test ==="
  local work toml_before toml_after prose_before prose_after expected_toml
  SELF_TEST_TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/verify-doc-hierarchy-stale-bootstrap.XXXXXX") \
    || { fail "could not create stale-bootstrap temp dir"; return 1; }
  trap cleanup_self_test_worktrees EXIT INT TERM

  work="$SELF_TEST_TMP_ROOT/stale-bootstrap"
  prepare_self_test_worktree "$work" expected || return 1

  cat > "$work/.ai-playbook/facts.md" <<'EOF'
```toml
plans_dir = "docs/plans/"
reviews_dir = "docs/reviews/"
tmp_dir = "docs/tmp/"
facts_path = ".ai-playbook/facts.md"
bootstrap_version = "1"
```

## Related Jira tasks

- STALE-1 — prose below opening fence must survive refresh

## Inline code fence edge case

Do not parse the following as TOML (prose-only example):

```toml
plans_dir = "docs/legacy-inline/"
reviews_dir = "docs/legacy-reviews/"
```

End of edge-case section.
EOF

  prose_before=$(extract_prose_after_opening_toml "$work/.ai-playbook/facts.md")
  toml_before=$(extract_opening_toml_body "$work/.ai-playbook/facts.md")

  echo "$toml_before" | grep -q 'plans_dir = "docs/plans/"' \
    || { fail "stale-bootstrap fixture missing stale plans_dir"; return 1; }

  expected_toml='plans_dir = "docs/history/plans/"
reviews_dir = "docs/history/reviews/"
tmp_dir = "docs/tmp/"
facts_path = ".ai-playbook/facts.md"
bootstrap_version = "1"
'
  refresh_opening_toml_preserve_prose "$work/.ai-playbook/facts.md" "$expected_toml"

  toml_after=$(extract_opening_toml_body "$work/.ai-playbook/facts.md")
  prose_after=$(extract_prose_after_opening_toml "$work/.ai-playbook/facts.md")

  echo "$toml_after" | grep -q 'plans_dir = "docs/history/plans/"' \
    || { fail "stale-bootstrap refresh did not update plans_dir"; return 1; }
  echo "$toml_after" | grep -q 'docs/legacy-inline/' \
    && { fail "stale-bootstrap refresh merged inline prose fence into opening TOML"; return 1; }
  [ "$prose_before" = "$prose_after" ] \
    || { fail "stale-bootstrap refresh changed prose below opening fence"; return 1; }
  echo "$prose_after" | grep -q 'docs/legacy-inline/' \
    || { fail "stale-bootstrap prose lost inline code fence edge-case content"; return 1; }

  echo "OK: stale TOML refresh preserves prose and ignores inline code fences"
}

gate_self_test() {
  echo "=== Self-test ==="
  local script_dir legacy_work expected_work out
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  if ! command -v rg >/dev/null 2>&1; then
    fail "rg (ripgrep) required for self-test assertions"
    return 1
  fi

  SELF_TEST_TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/verify-doc-hierarchy-self-test.XXXXXX") \
    || { fail "could not create self-test temp dir"; return 1; }
  trap cleanup_self_test_worktrees EXIT INT TERM

  legacy_work="$SELF_TEST_TMP_ROOT/legacy"
  expected_work="$SELF_TEST_TMP_ROOT/expected"
  prepare_self_test_worktree "$legacy_work" legacy || return 1
  prepare_self_test_worktree "$expected_work" expected || return 1

  if out=$(REPO_ROOT="$legacy_work" "$script_dir/verify-doc-hierarchy.sh" step2 2>&1); then
    fail "legacy layout step2 should fail but passed"
  else
    echo "$out" | rg -q 'docs/plans still at root' \
      || fail "legacy layout step2 failed for unexpected reason: $out"
    echo "OK: legacy layout fails step2 as expected"
  fi
  if ! out=$(REPO_ROOT="$expected_work" "$script_dir/verify-doc-hierarchy.sh" step2 2>&1); then
    fail "migrated layout step2 should pass but failed: $out"
  else
    echo "OK: migrated layout passes step2 as expected"
  fi
  if ! out=$(REPO_ROOT="$expected_work" "$script_dir/verify-doc-hierarchy.sh" full 2>&1); then
    fail "migrated layout full should pass but failed: $out"
  else
    echo "OK: migrated layout passes full as expected"
  fi

  local module_work nested_work legacy_ref_work
  module_work="$SELF_TEST_TMP_ROOT/module-split"
  prepare_self_test_worktree "$module_work" expected || return 1
  mkdir -p "$module_work/docs/foo"
  echo 'fixture' > "$module_work/docs/foo/.gitkeep"
  commit_self_test_worktree "$module_work" "add module-split dir" || return 1
  if out=$(REPO_ROOT="$module_work" "$script_dir/verify-doc-hierarchy.sh" step3 2>&1); then
    fail "module-split layout step3 should fail but passed"
  else
    echo "$out" | rg -q 'module-split docs dir still present' \
      || fail "module-split step3 failed for unexpected reason: $out"
    echo "OK: module-split layout fails step3 as expected"
  fi

  nested_work="$SELF_TEST_TMP_ROOT/nested-fn"
  prepare_self_test_worktree "$nested_work" expected || return 1
  mkdir -p "$nested_work/docs/history/feature-notes/badsubdir"
  echo 'fixture' > "$nested_work/docs/history/feature-notes/badsubdir/.gitkeep"
  commit_self_test_worktree "$nested_work" "add nested feature-notes dir" || return 1
  if out=$(REPO_ROOT="$nested_work" "$script_dir/verify-doc-hierarchy.sh" step4 2>&1); then
    fail "nested feature-notes step4 should fail but passed"
  else
    echo "$out" | rg -q 'nested feature-notes dir' \
      || fail "nested feature-notes step4 failed for unexpected reason: $out"
    echo "OK: nested feature-notes fails step4 as expected"
  fi

  legacy_ref_work="$SELF_TEST_TMP_ROOT/legacy-ref"
  prepare_self_test_worktree "$legacy_ref_work" expected || return 1
  echo 'Do not recreate docs/plans/ at root.' >> "$legacy_ref_work/docs/architecture/api-contracts.md"
  commit_self_test_worktree "$legacy_ref_work" "add legacy path string" || return 1
  if out=$(REPO_ROOT="$legacy_ref_work" "$script_dir/verify-doc-hierarchy.sh" full 2>&1); then
    fail "legacy path string in canonical doc should fail full but passed"
  else
    echo "$out" | rg -q 'legacy docs/context, docs/plans, or docs/proposals still referenced in canonical docs' \
      || fail "legacy-ref full failed for unexpected reason: $out"
    echo "OK: legacy path string in canonical doc fails full as expected"
  fi

  local catalog_work catalog_ok_work guidelines_work vendored_work audit_work
  catalog_work="$SELF_TEST_TMP_ROOT/caller-catalog-missing"
  prepare_self_test_worktree "$catalog_work" expected || return 1
  if out=$(REPO_ROOT="$catalog_work" REQUIRE_CALLER_CATALOG=1 "$script_dir/verify-doc-hierarchy.sh" step2 2>&1); then
    fail "REQUIRE_CALLER_CATALOG=1 without api-reference should fail step2 but passed"
  else
    echo "$out" | rg -q 'api-reference.md missing' \
      || fail "caller-catalog-missing step2 failed for unexpected reason: $out"
    echo "OK: REQUIRE_CALLER_CATALOG=1 fails without api-reference as expected"
  fi

  catalog_ok_work="$SELF_TEST_TMP_ROOT/caller-catalog-present"
  prepare_self_test_worktree "$catalog_ok_work" expected || return 1
  echo 'caller samples (fixture)' > "$catalog_ok_work/docs/maintenance/api-reference.md"
  commit_self_test_worktree "$catalog_ok_work" "add api-reference" || return 1
  if ! out=$(REPO_ROOT="$catalog_ok_work" REQUIRE_CALLER_CATALOG=1 "$script_dir/verify-doc-hierarchy.sh" step2 2>&1); then
    fail "REQUIRE_CALLER_CATALOG=1 with api-reference should pass step2 but failed: $out"
  else
    echo "OK: REQUIRE_CALLER_CATALOG=1 passes with api-reference as expected"
  fi

  guidelines_work="$SELF_TEST_TMP_ROOT/company-guidelines-missing"
  prepare_self_test_worktree "$guidelines_work" expected || return 1
  if out=$(REPO_ROOT="$guidelines_work" CLASSIFIED_COMPANY_GUIDELINES=1 "$script_dir/verify-doc-hierarchy.sh" step2 2>&1); then
    fail "CLASSIFIED_COMPANY_GUIDELINES=1 without mirror should fail step2 but passed"
  else
    echo "$out" | rg -q 'company-guidelines.md missing' \
      || fail "company-guidelines-missing step2 failed for unexpected reason: $out"
    echo "OK: CLASSIFIED_COMPANY_GUIDELINES=1 fails without mirror as expected"
  fi

  guidelines_work="$SELF_TEST_TMP_ROOT/company-guidelines-present"
  prepare_self_test_worktree "$guidelines_work" expected || return 1
  echo 'mirror (fixture)' > "$guidelines_work/docs/maintenance/company-guidelines.md"
  commit_self_test_worktree "$guidelines_work" "add company-guidelines mirror" || return 1
  if ! out=$(REPO_ROOT="$guidelines_work" CLASSIFIED_COMPANY_GUIDELINES=1 "$script_dir/verify-doc-hierarchy.sh" step2 2>&1); then
    fail "CLASSIFIED_COMPANY_GUIDELINES=1 with mirror should pass step2 but failed: $out"
  else
    echo "OK: CLASSIFIED_COMPANY_GUIDELINES=1 passes with mirror as expected"
  fi

  vendored_work="$SELF_TEST_TMP_ROOT/vendored-verify"
  prepare_self_test_worktree "$vendored_work" expected || return 1
  mkdir -p "$vendored_work/scripts"
  cp "$script_dir/verify-doc-hierarchy.sh" "$vendored_work/scripts/verify-doc-hierarchy.sh"
  commit_self_test_worktree "$vendored_work" "vendor verify script" || return 1
  if out=$(REPO_ROOT="$vendored_work" "$script_dir/verify-doc-hierarchy.sh" step2 2>&1); then
    fail "vendored verify script should fail step2 but passed"
  else
    echo "$out" | rg -q 'verify-doc-hierarchy.sh vendored' \
      || fail "vendored-verify step2 failed for unexpected reason: $out"
    echo "OK: vendored verify script fails step2 as expected"
  fi

  if ! out=$(REPO_ROOT="$expected_work" "$script_dir/verify-doc-hierarchy.sh" audit 2>&1); then
    fail "audit on migrated layout should pass but failed: $out"
  else
    echo "$out" | rg -q 'PASS \(audit\)' \
      || fail "audit missing PASS banner: $out"
    echo "OK: audit passes on migrated layout as expected"
  fi

  local reviews_ref_work stub_work rogue_work bare_host_work
  reviews_ref_work="$SELF_TEST_TMP_ROOT/reviews-ref"
  prepare_self_test_worktree "$reviews_ref_work" expected || return 1
  echo 'See docs/reviews/ for staging.' >> "$reviews_ref_work/docs/architecture/system-overview.md"
  commit_self_test_worktree "$reviews_ref_work" "add docs/reviews reference" || return 1
  if out=$(REPO_ROOT="$reviews_ref_work" "$script_dir/verify-doc-hierarchy.sh" full 2>&1); then
    fail "docs/reviews/ reference should fail full but passed"
  else
    echo "$out" | rg -q 'docs/reviews/ still referenced' \
      || fail "reviews-ref full failed for unexpected reason: $out"
    echo "OK: docs/reviews/ reference fails full as expected"
  fi

  stub_work="$SELF_TEST_TMP_ROOT/stub-redirect"
  prepare_self_test_worktree "$stub_work" expected || return 1
  echo '# Moved to docs/architecture/domain-model.md' > "$stub_work/docs/stub-redirect.md"
  commit_self_test_worktree "$stub_work" "add stub redirect" || return 1
  if out=$(REPO_ROOT="$stub_work" "$script_dir/verify-doc-hierarchy.sh" full 2>&1); then
    fail "stub redirect should fail full but passed"
  else
    echo "$out" | rg -q 'stub redirect still present' \
      || fail "stub-redirect full failed for unexpected reason: $out"
    echo "OK: stub redirect fails full as expected"
  fi

  rogue_work="$SELF_TEST_TMP_ROOT/rogue-module-path"
  prepare_self_test_worktree "$rogue_work" expected || return 1
  mkdir -p "$rogue_work/src/main/java/com/example"
  echo '// see docs/foo/bar for details' > "$rogue_work/src/main/java/com/example/App.java"
  commit_self_test_worktree "$rogue_work" "add rogue docs path in source" || return 1
  if out=$(REPO_ROOT="$rogue_work" "$script_dir/verify-doc-hierarchy.sh" full 2>&1); then
    fail "rogue docs/<module>/ path should fail full but passed"
  else
    echo "$out" | rg -q 'rogue docs/<module>/ path in source or config' \
      || fail "rogue-module-path full failed for unexpected reason: $out"
    echo "OK: rogue docs/<module>/ path fails full as expected"
  fi

  bare_host_work="$SELF_TEST_TMP_ROOT/bare-host-exclusion"
  prepare_self_test_worktree "$bare_host_work" expected || return 1
  mkdir -p "$bare_host_work/src/main/java/com/example"
  echo '// see kubernetes.io/docs/concepts/pods for vendor docs' > "$bare_host_work/src/main/java/com/example/App.java"
  commit_self_test_worktree "$bare_host_work" "add bare hostname vendor doc reference" || return 1
  if ! out=$(REPO_ROOT="$bare_host_work" "$script_dir/verify-doc-hierarchy.sh" full 2>&1); then
    fail "bare hostname vendor doc reference should pass full but failed: $out"
  else
    echo "OK: bare hostname vendor doc reference passes full as expected"
  fi

  local committed_facts_work instructions_repo out_guard
  committed_facts_work="$SELF_TEST_TMP_ROOT/committed-maintenance-facts"
  prepare_self_test_worktree "$committed_facts_work" expected || return 1
  echo '# Legacy committed facts (fixture — should fail step5)' > "$committed_facts_work/docs/maintenance/facts.md"
  git -C "$committed_facts_work" add -f docs/maintenance/facts.md 2>/dev/null
  commit_self_test_worktree "$committed_facts_work" "add committed docs/maintenance/facts.md" || return 1
  if out=$(REPO_ROOT="$committed_facts_work" "$script_dir/verify-doc-hierarchy.sh" step5 2>&1); then
    fail "committed docs/maintenance/facts.md should fail step5 but passed"
  else
    echo "$out" | rg -q 'docs/maintenance/facts.md still committed' \
      || fail "committed-maintenance-facts step5 failed for unexpected reason: $out"
    echo "OK: committed docs/maintenance/facts.md fails step5 as expected"
  fi

  root_facts_work="$SELF_TEST_TMP_ROOT/committed-root-facts"
  prepare_self_test_worktree "$root_facts_work" expected || return 1
  echo '# Legacy root facts (fixture — should fail step5-committed)' > "$root_facts_work/docs/facts.md"
  git -C "$root_facts_work" add -f docs/facts.md 2>/dev/null
  commit_self_test_worktree "$root_facts_work" "add committed docs/facts.md" || return 1
  if out=$(REPO_ROOT="$root_facts_work" "$script_dir/verify-doc-hierarchy.sh" step5-committed 2>&1); then
    fail "committed docs/facts.md should fail step5-committed but passed"
  else
    echo "$out" | rg -q 'docs/facts.md still committed' \
      || fail "committed-root-facts step5-committed failed for unexpected reason: $out"
    echo "OK: committed docs/facts.md fails step5-committed as expected"
  fi

  instructions_repo=$(cd "$script_dir/../../../.." && pwd -P)
  if out=$(REPO_ROOT="$instructions_repo" "$script_dir/verify-doc-hierarchy.sh" step2 2>&1); then
    fail "instructions repo as REPO_ROOT should fatal but passed"
  else
    echo "$out" | rg -q 'instructions/skills repository' \
      || fail "instructions-repo guard failed for unexpected reason: $out"
    echo "OK: instructions repo guard fatals as expected"
  fi

  skill_install_dir=$(cd "$script_dir/.." && pwd -P)
  if out=$(REPO_ROOT="$skill_install_dir" "$script_dir/verify-doc-hierarchy.sh" step2 2>&1); then
    fail "skill install directory as REPO_ROOT should fatal but passed"
  else
    echo "$out" | rg -q 'skill install directory|must be the git repository root' \
      || fail "skill-install guard failed for unexpected reason: $out"
    echo "OK: skill install directory guard fatals as expected"
  fi
}

case "$PHASE" in
  step2) gate_step2 ;;
  step3) gate_step3 ;;
  step4) gate_step4 ;;
  step5-committed) gate_step5_committed ;;
  step5) gate_step5 ;;
  step6|full) gate_step6 ;;  # aliases; prefer full in skill documentation
  audit) gate_audit ;;
  self-test) gate_self_test ;;
  stale-bootstrap-test) gate_stale_bootstrap_test ;;
  *)
    echo "Unknown phase: $PHASE (use step2|step3|step4|step5|step5-committed|step6|audit|full|self-test|stale-bootstrap-test)" >&2
    exit 2
    ;;
esac

if [ "$FAILS" -gt 0 ]; then
  echo "=== $FAILS gate failure(s) ==="
  exit 1
fi
echo "=== PASS ($PHASE) ==="
exit 0
