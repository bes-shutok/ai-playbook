#!/usr/bin/env python3
"""Machinery inventory: registry-backed keep-or-delete inventory of every
guard script, hook, review-round mechanism, protocol layer, and scheduler
state field (2026-09-28 machinery-elimination-pass plan).

Modes:
  --scaffold  generate candidate registry rows (disposition "pending") from
              tracked sources only and merge them into the registry file.
  --check     validate the registry against the tracked tree; exit non-zero
              on regrowth, unresolved witnesses, bad rows, or pending rows
              (skipped only under --allow-pending).

All check inputs come from the committed tree (git ls-tree HEAD, never the index), so the guard is
worktree-independent. The gitignored observed scheduler state file, when
present, is a scaffold cross-check that only adds rows, never a check input.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REGISTRY_PATH = "scripts/machinery_registry.json"
SKILL_PATH = "agents/skills/maintenance/SKILL.md"
WITNESS_CLASSES = ("none", "origin-kept-set", "red-test", "incident",
                   "user-decision", "sibling-boundary")
DISPOSITIONS = ("pending", "keep", "delete")
KINDS = ("script", "hook", "state-field", "protocol")
STATE_FIELD_HEADING = "## State file"

# The plan's named-protocol universe (Task 2 seed rows). Refs resolve at
# execution; the scaffold emits them with disposition pending.
SEED_PROTOCOLS = [
    ("five-round-review-cap", "agents/skills/review-loop/SKILL.md"),
    ("review-staging-governance", None),
    ("plan-readiness-gate", None),
    ("digest-recert-fencing", None),
    ("merge-landing-lock", None),
    ("budget-pause-protocol", None),
    ("done-sweep-gates", None),
    ("reverse-squash-dirt-gates", None),
    ("skills-gate-markers", None),
    ("quota-probing-budget-guard", "docs/history/plans/completed/2026-09-28-account-quota-governor.md"),
    ("worktree-recipe", "docs/history/plans/completed/2026-09-28-worktree-first-standard-only-mode.md"),
    ("residual-acceptance-exit", "docs/history/plans/completed/2026-09-28-residual-exit-same-day-ordering-gates.md"),
]


def _git(repo, *args):
    out = subprocess.run(["git", "-C", str(repo)] + list(args),
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit("machinery_inventory: git {} failed: {}".format(
            " ".join(args), out.stderr.strip()))
    return out.stdout


def tracked_files(repo):
    """The committed tree (HEAD), never the index: staged-but-uncommitted
    entries (for example a peer's staged adds of deleted paths) must not read
    as tracked machinery."""
    return set(_git(repo, "ls-tree", "-r", "--name-only", "HEAD").splitlines())


def is_test_path(path):
    name = os.path.basename(path)
    return name.startswith("test_") or "/test_" in path


def script_paths(tracked):
    out = []
    for path in sorted(tracked):
        if path.startswith("scripts/") and path.endswith((".py", ".sh")) \
                and not is_test_path(path):
            out.append(path)
    return out


def hook_dirs(tracked):
    dirs = set()
    for path in tracked:
        if path.startswith("agents/hooks/"):
            parts = path.split("/")
            if len(parts) >= 3:
                dirs.add("agents/hooks/{}/".format(parts[2]))
    return sorted(dirs)


def parse_state_fields(skill_text):
    """Field names parsed from the tracked State file schema section: a
    paragraph whose first token is a backticked snake_case name followed by
    ' is '."""
    fields = []
    in_section = False
    for line in skill_text.splitlines():
        if line.startswith("#"):
            in_section = line.strip().lower() == state_heading_lower()
            continue
        if not in_section:
            continue
        match = re.match(r"^`([a-z_0-9]+)` is ", line.strip())
        if match and len(match.group(1)) > 3:
            fields.append(match.group(1))
    return sorted(set(fields))


def state_heading_lower():
    return STATE_FIELD_HEADING.lower()


def load_registry(repo):
    path = Path(repo) / REGISTRY_PATH
    if not path.exists():
        return {"schema_version": 1, "entries": [], "removals": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_registry(repo, registry):
    path = Path(repo) / REGISTRY_PATH
    path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def scaffold_rows(repo, tracked, observed_state=None, skill_path=SKILL_PATH):
    rows = []
    for path in script_paths(tracked):
        rows.append({
            "id": "script:" + os.path.basename(path),
            "kind": "script",
            "paths": [path],
            "tests": [],
            "witness": {"class": "none", "ref": None},
            "disposition": "pending",
            "note": "",
        })
    for hook_dir in hook_dirs(tracked):
        rows.append({
            "id": "hook:" + hook_dir.rstrip("/").split("/")[-1],
            "kind": "hook",
            "paths": [hook_dir],
            "tests": [],
            "witness": {"class": "none", "ref": None},
            "disposition": "pending",
            "note": "",
        })
    skill = (Path(repo) / skill_path).read_text(encoding="utf-8")
    for field in parse_state_fields(skill):
        rows.append({
            "id": "state-field:" + field,
            "kind": "state-field",
            "paths": [],
            "tests": [],
            "witness": {"class": "none", "ref": None},
            "disposition": "pending",
            "note": "",
        })
    for name, _ref in SEED_PROTOCOLS:
        rows.append({
            "id": "protocol:" + name,
            "kind": "protocol",
            "paths": [],
            "tests": [],
            "witness": {"class": "none", "ref": None},
            "disposition": "pending",
            "note": "",
        })
    # Cross-check only: the gitignored observed state file can add field rows
    # for names the tracked section does not define yet; it is never a check
    # input.
    if observed_state and Path(observed_state).exists():
        try:
            data = json.loads(Path(observed_state).read_text(encoding="utf-8"))
            known = {r["id"] for r in rows}
            for key in sorted(data):
                if isinstance(key, str) and re.fullmatch(r"[a-z_0-9]+", key) \
                        and len(key) > 3:
                    rid = "state-field:" + key
                    if rid not in known:
                        rows.append({
                            "id": rid, "kind": "state-field", "paths": [],
                            "tests": [], "witness": {"class": "none", "ref": None},
                            "disposition": "pending", "note": "observed state key",
                        })
        except (ValueError, OSError):
            pass
    return rows


def cmd_scaffold(repo, observed_state, skill_path=SKILL_PATH):
    tracked = tracked_files(repo)
    registry = load_registry(repo)
    known = {e["id"] for e in registry.get("entries", [])}
    added = 0
    for row in scaffold_rows(repo, tracked, observed_state, skill_path):
        if row["id"] not in known:
            registry.setdefault("entries", []).append(row)
            known.add(row["id"])
            added += 1
    save_registry(repo, registry)
    print("scaffold: {} new row(s), {} total".format(
        added, len(registry["entries"])))
    return 0


def check_failures(repo, registry, allow_pending, skill_path=SKILL_PATH):
    tracked = tracked_files(repo)
    failures = []
    entries = registry.get("entries", [])
    seen_ids = {}
    path_owner = {}
    for entry in entries:
        rid = entry.get("id", "<missing>")
        if rid in seen_ids:
            failures.append("duplicate id: {}".format(rid))
        seen_ids[rid] = True
        kind = entry.get("kind")
        if kind not in KINDS:
            failures.append("{}: bad kind {}".format(rid, kind))
        disposition = entry.get("disposition")
        if disposition not in DISPOSITIONS:
            failures.append("{}: bad disposition {}".format(rid, disposition))
            continue
        if disposition == "pending" and not allow_pending:
            failures.append("{}: row still pending".format(rid))
        for path in entry.get("paths", []):
            if path in path_owner and path_owner[path] != rid:
                failures.append("{}: path {} already owned by {}".format(
                    rid, path, path_owner[path]))
            path_owner[path] = rid
        witness = entry.get("witness", {})
        wclass = witness.get("class")
        if wclass not in WITNESS_CLASSES:
            failures.append("{}: bad witness class {}".format(rid, wclass))
        if disposition == "keep":
            if wclass == "none":
                failures.append("{}: keep with witness class none".format(rid))
            ref = witness.get("ref")
            if wclass != "none":
                if not ref or ref not in tracked:
                    failures.append("{}: witness ref does not resolve to a tracked path: {}".format(rid, ref))
            for path in entry.get("paths", []):
                if path.endswith("/"):
                    if not any(t.startswith(path) for t in tracked):
                        failures.append("{}: keep path does not exist: {}".format(rid, path))
                elif path not in tracked:
                    failures.append("{}: keep path does not exist: {}".format(rid, path))
        if disposition == "delete" and not (entry.get("note") or "").strip():
            failures.append("{}: delete row without a note naming its spent event or unwitnessed basis".format(rid))

    # Regrowth: tracked machinery with no registry row.
    registered_paths = set()
    for entry in entries:
        registered_paths.update(entry.get("paths", []))
    for path in script_paths(tracked):
        if path not in registered_paths:
            failures.append("regrowth: unregistered script file {}".format(path))
    for hook_dir in hook_dirs(tracked):
        if hook_dir not in registered_paths:
            failures.append("regrowth: unregistered hook directory {}".format(hook_dir))
    skill = (Path(repo) / skill_path).read_text(encoding="utf-8")
    registered_fields = {e["id"] for e in entries
                         if e.get("kind") == "state-field"}
    for field in parse_state_fields(skill):
        rid = "state-field:" + field
        if rid not in registered_fields:
            failures.append("regrowth: unregistered state field {}".format(rid))

    # Removals: a removals-list row whose paths still exist fails.
    for removal in registry.get("removals", []):
        for path in removal.get("paths", []):
            if path.endswith("/"):
                if any(t.startswith(path) for t in tracked):
                    failures.append("removals {}: path still exists {}".format(removal.get("id"), path))
            elif path in tracked:
                failures.append("removals {}: path still exists {}".format(removal.get("id"), path))
    return failures


def cmd_check(repo, allow_pending, skill_path=SKILL_PATH):
    registry = load_registry(repo)
    failures = check_failures(repo, registry, allow_pending, skill_path)
    if failures:
        for failure in failures:
            print("FAIL: " + failure)
        print("machinery inventory check: {} failure(s)".format(len(failures)))
        return 1
    print("machinery inventory check: ok ({} entries, {} removals)".format(
        len(registry.get("entries", [])), len(registry.get("removals", []))))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scaffold", action="store_true")
    group.add_argument("--check", action="store_true")
    parser.add_argument("--allow-pending", action="store_true")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--observed-state", default=None,
                        help="gitignored observed state file (scaffold cross-check only)")
    parser.add_argument("--skill-path", default=SKILL_PATH,
                        help="tracked skill file carrying the State file schema section")
    args = parser.parse_args(argv)
    repo = args.repo_root or subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True,
        text=True).stdout.strip()
    if not repo:
        raise SystemExit("machinery_inventory: not inside a git repository")
    if args.scaffold:
        return cmd_scaffold(repo, args.observed_state, skill_path=args.skill_path)
    return cmd_check(repo, args.allow_pending, args.skill_path)


if __name__ == "__main__":
    sys.exit(main())
