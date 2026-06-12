#!/usr/bin/env bash
# verify-doc-hierarchy.sh — migration gates for doc-hierarchy-migrate
# Usage: verify-doc-hierarchy.sh [step2|step3|step4|step5|step6|audit|full|self-test]
# Note: step6 and full are aliases (both run gate_step6); prefer full in skill docs.
# Env: REPO_ROOT (default .), REQUIRE_CALLER_CATALOG (0|1), CLASSIFIED_COMPANY_GUIDELINES (0|1)

set -uo pipefail

PHASE="${1:-full}"
REPO_ROOT="${REPO_ROOT:-.}"
cd "$REPO_ROOT" || exit 2
git rev-parse --git-dir >/dev/null 2>&1 || { echo 'FATAL: REPO_ROOT is not a git repository'; exit 2; }
REPO_TOP=$(git rev-parse --show-toplevel)
if [ "$(pwd -P)" != "$(cd "$REPO_TOP" && pwd -P)" ]; then
  echo "FATAL: REPO_ROOT must be the git repository root (toplevel: $REPO_TOP)" >&2
  exit 2
fi

FAILS=0
fail() { echo "FAIL: $1"; FAILS=$((FAILS + 1)); }
warn() { echo "WARN: $1"; }

gate_step2() {
  echo "=== Step 2 gate ==="
  local f
  for f in project-guidelines project-decisions glossary facts; do
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
  echo "=== Step 5 gate ==="
  test -f AGENTS.md || fail "AGENTS.md missing"
  head -1 AGENTS.md | grep -q '^# Instructions' || fail "AGENTS.md H1 must be '# Instructions'"
  grep -q 'Documentation Hierarchy' AGENTS.md || fail "AGENTS.md missing Documentation Hierarchy subsection"
  grep -q 'docs/maintenance/facts' AGENTS.md || fail "AGENTS.md missing docs/maintenance/facts path"
  grep -q 'docs/maintenance/project-guidelines' AGENTS.md || fail "AGENTS.md missing docs/maintenance/project-guidelines path"
  test -f docs/maintenance/project-guidelines.md || fail "docs/maintenance/project-guidelines.md missing"
  grep -q 'Documentation Hierarchy' docs/maintenance/project-guidelines.md || fail "project-guidelines missing Documentation Hierarchy section"
  grep -qE 'plans_dir|docs/history/plans/' docs/maintenance/project-guidelines.md || fail "project-guidelines missing resolved plans path"
  test -L CLAUDE.md && [ "$(readlink CLAUDE.md)" = "AGENTS.md" ] || warn "CLAUDE.md should symlink to AGENTS.md"
  if [ -f .cursor/rules/instructions.mdc ]; then
    grep -q '@AGENTS.md' .cursor/rules/instructions.mdc || warn "Cursor instructions.mdc should @-include AGENTS.md"
  fi
}

gate_step6_finish() {
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
      | rg -v "${EXTERNAL_DOCS_DOMAIN:-no-match-placeholder}/docs/" \
      | rg -v 'firebase\.google\.com/docs/' | rg -q .; then
      fail "rogue docs/<module>/ path in source or config"
    fi
  else
    fail "rg (ripgrep) required for step6 reference scans"
  fi

  local f
  for f in system-overview domain-model integrations api-contracts event-flows operational-guides troubleshooting; do
    test -f "docs/architecture/${f}.md" || fail "docs/architecture/${f}.md missing"
  done
  local arch_count
  arch_count=$(ls -1 docs/architecture/*.md 2>/dev/null | wc -l | tr -d ' ')
  [ "$arch_count" -eq 7 ] || fail "docs/architecture/ must have exactly 7 .md files (found $arch_count)"

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
  mkdir -p "$root/docs/maintenance" "$root/docs/architecture"
  cat > "$root/AGENTS.md" <<'EOF'
# Instructions

## Documentation Hierarchy

- **Start here:** `docs/README.md` (Layer 1).
- **Facts / guidelines:** `docs/maintenance/facts.md`; `docs/maintenance/project-guidelines.md`.
- **Shared knowledge:** `docs/architecture/`, `docs/maintenance/` (Layer 2).
- **Historical context:** `docs/history/` (Layer 3).
- **LLM-only:** `docs/tmp/`; gitignored `docs/history/reviews/`.
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
| reviews_dir | docs/history/reviews/ |
| tmp_dir | docs/tmp/ |
EOF
  for f in facts glossary project-decisions; do
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
docs/history/reviews/
docs/tmp/
EOF
  git -C "$dst" init -q || { fail "could not init git repo in $(basename "$dst") worktree"; return 1; }
  git -C "$dst" add -A 2>/dev/null
  git -C "$dst" commit -qm "self-test" >/dev/null 2>&1 \
    || { fail "could not commit $(basename "$dst") worktree"; return 1; }
}

commit_self_test_worktree() {
  local work="$1" msg="$2"
  git -C "$work" add -A 2>/dev/null
  git -C "$work" commit -qm "$msg" >/dev/null 2>&1 \
    || { fail "could not commit $(basename "$work") worktree: $msg"; return 1; }
}

cleanup_self_test_worktrees() {
  if [ -n "${SELF_TEST_TMP_ROOT:-}" ] && [ -d "$SELF_TEST_TMP_ROOT" ]; then
    rm -rf "$SELF_TEST_TMP_ROOT"
  fi
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
}

case "$PHASE" in
  step2) gate_step2 ;;
  step3) gate_step3 ;;
  step4) gate_step4 ;;
  step5) gate_step5 ;;
  step6|full) gate_step6 ;;  # aliases; prefer full in skill documentation
  audit) gate_audit ;;
  self-test) gate_self_test ;;
  *)
    echo "Unknown phase: $PHASE (use step2|step3|step4|step5|step6|audit|full|self-test)" >&2
    exit 2
    ;;
esac

if [ "$FAILS" -gt 0 ]; then
  echo "=== $FAILS gate failure(s) ==="
  exit 1
fi
echo "=== PASS ($PHASE) ==="
exit 0
