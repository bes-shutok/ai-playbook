#!/usr/bin/env python3
"""Machinery inventory: registry-backed keep-or-delete inventory of every
guard script, hook, review-round mechanism, protocol layer, and scheduler
state field (2026-09-28 machinery-elimination-pass plan).

Modes:
  --scaffold  generate candidate registry rows (disposition "pending") from
              tracked sources only and merge them into the registry file.
  --check     validate the registry against the tracked tree; exit non-zero
              on regrowth, unresolved or non-exercising red-test witnesses,
              bad rows, or pending rows (skipped only under --allow-pending).
  --render-baseline <path>
              run the three known-red gate producer surfaces (this script's
              --check, scripts/check_maintenance_pins.sh, and
              scripts/skill_text_budget.py --check) against the primary
              checkout (the first `git worktree list --porcelain` entry) and
              write the known-red gate baseline JSON to <path>; a relative
              path resolves against the primary checkout. Exits per
              scripts/OUTCOME_CONTRACT.md (the render mode's register row
              there declares the producer-subprocess operating-context
              assumptions; the legacy --check/--scaffold exits stay outside
              the contract).

Tracked-tree and witness check inputs come from the committed tree (git
ls-tree HEAD and git show HEAD:, never the index), so those checks are
worktree-independent; the registry JSON and the State-file skill text are
read from the worktree. The gitignored observed scheduler state file, when
present, is a scaffold cross-check that only adds rows, never a check input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REGISTRY_PATH = "scripts/machinery_registry.json"
# re-pointed to the state-file module by the maintenance-skill-size-refactor
# split (Task 3): the State file schema section lives there now
SKILL_PATH = "agents/skills/maintenance/state-file.md"
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


def is_test_source_path(path):
    """A Python or shell test-source path: `.py`/`.sh` extension and a
    basename beginning `test_` (witness-ref-validation plan 2026-10-30)."""
    return path.endswith((".py", ".sh")) \
        and os.path.basename(path).startswith("test_")


def resolved_script_stems(entry):
    """Script stems a red-test witness must name for a `kind: script` row:
    the row's non-test `.py`/`.sh` file paths; when `paths` is empty, a
    `.py`/`.sh` filename in the row id, then explicit non-test
    `scripts/<file>` paths in its note; when neither resolves there is no
    stem to check and only the tracked-test-source check applies."""
    if entry.get("paths"):
        sources = [p for p in entry["paths"]
                   if p.endswith((".py", ".sh")) and not is_test_source_path(p)]
    else:
        id_match = re.fullmatch(r"script:([A-Za-z0-9._-]+\.(?:py|sh))",
                                entry.get("id") or "")
        if id_match:
            sources = [id_match.group(1)]
        else:
            sources = [p for p in re.findall(
                r"scripts/[A-Za-z0-9._/-]+\.(?:py|sh)", entry.get("note") or "")
                if not is_test_source_path(p)]
    return sorted({os.path.splitext(os.path.basename(s))[0] for s in sources})


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
                elif wclass == "red-test" and not is_test_source_path(ref):
                    failures.append("{}: red-test witness ref is not a tracked test-source path (test_*.py or test_*.sh): {}".format(rid, ref))
                elif wclass == "red-test" and kind == "script":
                    # Reached only for a script row whose ref resolved to a
                    # tracked test source (the two fences above), so those
                    # conditions are not re-tested here. Witness test content
                    # comes from the committed tree (git show HEAD:), never
                    # the index or worktree copies.
                    missing = [stem for stem in resolved_script_stems(entry)
                               if stem not in _git(repo, "show",
                                                   "HEAD:{}".format(ref))]
                    if missing:
                        failures.append("{}: red-test witness {} omits resolved script stem(s): {}".format(
                            rid, ref, ", ".join(missing)))
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


# --- Known-red gate baseline rendering (plan
# 2026-11-13-known-red-gates-consumed-baseline, Task 1): the render mode is
# this script's OUTCOME_CONTRACT surface; the legacy --check/--scaffold exits
# stay outside the contract. ---

RENDER_SCHEMA = "known-red-gates-baseline"
RENDER_SCHEMA_VERSION = 1
# per-producer capture timeout; the MACHINERY_RENDER_TIMEOUT_SECS override is
# a declared test-only seam (render fixtures shrink the wait), never set in
# production
RENDER_PRODUCER_TIMEOUT_SECS = 300

RENDER_PRODUCER_ORDER = ("machinery_inventory", "maintenance_pins",
                         "skill_text_budget")
RENDER_PRODUCER_SCRIPTS = {
    "machinery_inventory": "machinery_inventory.py",
    "maintenance_pins": "check_maintenance_pins.sh",
    "skill_text_budget": "skill_text_budget.py",
}
# the expected terminal marker each producer must emit for its capture to
# count; the inventory's legacy exit shape (no OUTCOME: line) is normal
# output, so its marker is its own summary line
RENDER_EXPECTED_MARKERS = {
    "machinery_inventory": "machinery inventory check: ",
    "maintenance_pins": "OUTCOME: ",
    "skill_text_budget": "OUTCOME: ",
}
# capture vocabulary (the plan's Terms entry): line-prefix classes recorded
# verbatim, longest prefix first so compound classes are not shadowed
RENDER_CAPTURE_CLASSES = (
    ("maintenance_pins", "PIN RECORDED RED EXPIRED"),
    ("maintenance_pins", "PIN RECORDED RED MALFORMED"),
    ("maintenance_pins", "PIN RECORDED RED"),
    ("maintenance_pins", "PIN FAIL"),
    ("maintenance_pins", "PIN WARN"),
    ("maintenance_pins", "pin fail:"),
    ("skill_text_budget", "CEILING BREACH"),
    ("skill_text_budget", "BREACH"),
    ("skill_text_budget", "PILOT OVER"),
    ("skill_text_budget", "PILOT PENDING"),
    ("machinery_inventory", "FAIL:"),
)
# excluded from capture: the pins suite's run-summary lines and the pre-pin
# checkpoint's missing <path> arm, so a broken checkout's checkpoint failure
# never baseline-classifies; those lines stay unknown actionable everywhere
RENDER_EXCLUDED_PREFIXES = (
    "PIN RECORDED REDS SUPPRESSED THIS RUN:",
    "prune-range pins: first missing clause:",
    "placement pins: first missing span:",
    "missing ",
)
# controlling tracked inputs per producer section (the plan's staleness
# entry); the budget section additionally covers the capped-file set the
# scan reads (every agents/skills/*/[A-Za-z]*.md file), appended at capture
RENDER_CONTROLLING_INPUTS = {
    "machinery_inventory": (
        "scripts/machinery_inventory.py",
        "scripts/machinery_registry.json",
        "agents/skills/maintenance/state-file.md",
    ),
    "maintenance_pins": (
        "scripts/check_maintenance_pins.sh",
        "scripts/gate_liveness_ledger.json",
    ),
    "skill_text_budget": (
        "scripts/skill_text_budget.py",
        "scripts/skill_text_budget_caps.json",
    ),
}


def _git_probe(cwd, *args):
    out = subprocess.run(["git", "-C", str(cwd)] + list(args),
                         capture_output=True, text=True)
    return out.returncode, out.stdout


def resolve_primary_checkout(repo):
    """The primary checkout: the first `git worktree list --porcelain`
    entry (the home authority mechanism's resolution)."""
    rc, out = _git_probe(repo, "worktree", "list", "--porcelain")
    if rc != 0:
        return None
    for line in out.splitlines():
        if line.startswith("worktree "):
            return line[len("worktree "):].strip()
    return None


def resolve_base_tip(primary):
    """Base-tip provenance metadata: the primary checkout's default-branch
    tip, resolved as origin/HEAD when resolvable, else the primary checkout's
    own checked-out branch tip, else its detached HEAD."""
    rc, ref = _git_probe(primary, "symbolic-ref", "--quiet",
                         "refs/remotes/origin/HEAD")
    if rc == 0:
        rc2, commit = _git_probe(primary, "rev-parse", "--verify",
                                 ref.strip() + "^{commit}")
        if rc2 == 0:
            return {"ref": ref.strip(), "commit": commit.strip(),
                    "source": "origin-head"}
    rc, branch = _git_probe(primary, "symbolic-ref", "--quiet", "HEAD")
    if rc == 0:
        rc2, commit = _git_probe(primary, "rev-parse", "--verify",
                                 branch.strip() + "^{commit}")
        if rc2 == 0:
            return {"ref": branch.strip(), "commit": commit.strip(),
                    "source": "primary-branch"}
    rc, commit = _git_probe(primary, "rev-parse", "--verify", "HEAD^{commit}")
    if rc == 0:
        return {"ref": None, "commit": commit.strip(),
                "source": "detached-head"}
    return None


def _file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_controlling_inputs(primary, producer):
    """Per-section controlling-input digests over the primary checkout's
    working-tree bytes (the consumer re-derives them at read time)."""
    rels = list(RENDER_CONTROLLING_INPUTS[producer])
    if producer == "skill_text_budget":
        skills = Path(primary) / "agents" / "skills"
        if skills.is_dir():
            rels.extend(sorted(
                path.relative_to(primary).as_posix()
                for path in skills.glob("*/[A-Za-z]*.md") if path.is_file()))
    files = {}
    absent = []
    for rel in rels:
        path = Path(primary) / rel
        if path.is_file():
            files[rel] = _file_sha256(path)
        else:
            absent.append(rel)
    blob = json.dumps(files, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")
    return {"algorithm": "sha256", "files": files, "absent": absent,
            "digest": hashlib.sha256(blob).hexdigest()}


def classify_render_line(line):
    """Classify one producer output line into its owning producer section and
    captured class per the Terms capture vocabulary; None for excluded and
    out-of-vocabulary lines."""
    for prefix in RENDER_EXCLUDED_PREFIXES:
        if line.startswith(prefix):
            return None
    for producer, prefix in RENDER_CAPTURE_CLASSES:
        if line.startswith(prefix):
            return producer, prefix
    return None


def render_producer_command(producer, primary):
    """The producer subprocess command against the primary checkout; every
    producer runs with cwd inside the primary checkout (the pins suite's
    register default resolves the primary's tracked ledger through it)."""
    script = Path(primary) / "scripts" / RENDER_PRODUCER_SCRIPTS[producer]
    if producer == "maintenance_pins":
        return ["bash", str(script)]
    cmd = [sys.executable, str(script)]
    if producer == "machinery_inventory":
        cmd += ["--check", "--repo-root", str(primary)]
    elif producer == "skill_text_budget":
        cmd += ["--check"]
    return cmd


def _render_timeout():
    timeout = RENDER_PRODUCER_TIMEOUT_SECS
    override = os.environ.get("MACHINERY_RENDER_TIMEOUT_SECS")
    if override and override.isdigit() and int(override) > 0:
        timeout = int(override)
    return timeout


def capture_render_producer(producer, primary):
    """Run one producer surface and return its capture record: status
    (captured/unavailable), exit code, expected-output marker, and the
    classified lines from both streams. A producer that fails to launch,
    times out, or terminates without its expected marker is recorded
    unavailable; a modeled fail exit carrying the marker is capture-success."""
    record = {"status": "captured", "exit_code": None,
              "unavailable_reason": None, "expected_output": False,
              "captured_lines": []}
    cmd = render_producer_command(producer, primary)
    if not Path(cmd[1]).is_file():
        record["status"] = "unavailable"
        record["unavailable_reason"] = \
            "producer script not found: {}".format(cmd[1])
        return record
    try:
        proc = subprocess.run(cmd, cwd=str(primary), capture_output=True,
                              text=True, errors="replace",
                              timeout=_render_timeout())
    except subprocess.TimeoutExpired:
        record["status"] = "unavailable"
        record["unavailable_reason"] = \
            "timed out after {}s".format(_render_timeout())
        return record
    except OSError as exc:
        record["status"] = "unavailable"
        record["unavailable_reason"] = "failed to launch: {}".format(exc)
        return record
    record["exit_code"] = proc.returncode
    stdout_lines = proc.stdout.splitlines()
    stderr_lines = proc.stderr.splitlines()
    marker = RENDER_EXPECTED_MARKERS[producer]
    record["expected_output"] = any(
        line.startswith(marker) for line in stdout_lines)
    for stream, lines in (("stdout", stdout_lines), ("stderr", stderr_lines)):
        for line in lines:
            hit = classify_render_line(line)
            if hit:
                owner, klass = hit
                record["captured_lines"].append(
                    {"class": klass, "line": line, "stream": stream,
                     "section": owner})
    if not record["expected_output"]:
        record["status"] = "unavailable"
        record["unavailable_reason"] = (
            "terminated without its expected output (exit {}, no {} line)"
            .format(proc.returncode, marker.strip()))
    return record


def probe_output_writable(path):
    """Writability probe refusing before any producer runs: an existing
    baseline is append-opened (never truncated), a new path probes its
    parent directory with a created-and-removed temp file. Returns the
    observed error text, or None when writable."""
    try:
        if path.exists():
            with open(path, "a"):
                pass
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            handle, probe = tempfile.mkstemp(dir=str(path.parent),
                                             prefix=".render-probe-")
            os.close(handle)
            os.unlink(probe)
        return None
    except OSError as exc:
        return str(exc)


def render_baseline_payload(primary, out_path):
    sections = {}
    for producer in RENDER_PRODUCER_ORDER:
        section = render_controlling_inputs(primary, producer)
        capture = capture_render_producer(producer, primary)
        lines = []
        for entry in capture.pop("captured_lines"):
            entry["emitted_by"] = producer
            lines.append(entry)
        section["captured_lines"] = lines
        section.update(capture)
        sections[producer] = section
    base_tip = resolve_base_tip(primary)
    return {
        "schema": RENDER_SCHEMA,
        "schema_version": RENDER_SCHEMA_VERSION,
        "generated_at":
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "base_tip": base_tip if base_tip else
            {"ref": None, "commit": None, "source": "unresolvable"},
        "primary_checkout": str(primary),
        "write_home": str(out_path),
        "producers": sections,
    }


def write_render_baseline(out_path, payload):
    """Atomic write through a temp file in the output's directory, so a
    failed write leaves any existing baseline byte-untouched."""
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    handle, tmp = tempfile.mkstemp(dir=str(out_path.parent),
                                   prefix=".baseline-write-")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, str(out_path))
    except OSError:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def cmd_render_baseline(repo, out_arg):
    primary = resolve_primary_checkout(repo)
    if not primary:
        print("render: cannot resolve the primary checkout (the first "
              "`git worktree list --porcelain` entry)")
        print("OUTCOME: tool_error")
        return 3
    out_path = Path(out_arg)
    if not out_path.is_absolute():
        out_path = Path(primary) / out_path
    out_path = Path(os.path.abspath(str(out_path)))
    error = probe_output_writable(out_path)
    if error:
        print("render: refusing to write baseline: {}: {}".format(
            out_path, error))
        print("OUTCOME: tool_error")
        return 3
    try:
        payload = render_baseline_payload(primary, out_path)
        write_render_baseline(out_path, payload)
    except OSError as exc:
        print("render: refusing to write baseline: {}: {}".format(
            out_path, exc))
        print("OUTCOME: tool_error")
        return 3
    unavailable = [producer for producer in RENDER_PRODUCER_ORDER
                   if payload["producers"][producer]["status"] != "captured"]
    for producer in unavailable:
        print("render: producer unavailable: {}: {}".format(
            producer, payload["producers"][producer]["unavailable_reason"]))
    captured = sum(len(section["captured_lines"])
                   for section in payload["producers"].values())
    print("render: baseline written to {} (producers captured {}/{}, "
          "{} red line(s) captured)".format(
              out_path, len(RENDER_PRODUCER_ORDER) - len(unavailable),
              len(RENDER_PRODUCER_ORDER), captured))
    if unavailable:
        print("OUTCOME: indeterminate")
        return 2
    print("OUTCOME: pass")
    return 0


class _RenderUsageParser(argparse.ArgumentParser):
    # usage violations keep argparse's legacy exit shape for the legacy
    # --check/--scaffold modes; a --render-baseline invocation is the
    # contract-conformant surface, so its usage error is tool error (exit 3)
    # with the final OUTCOME line on stdout
    render_invocation = False

    def error(self, message):
        if self.render_invocation:
            print("usage error: {}".format(message))
            print("OUTCOME: tool_error")
            sys.exit(3)
        super().error(message)


def main(argv=None):
    parser = _RenderUsageParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scaffold", action="store_true")
    group.add_argument("--check", action="store_true")
    group.add_argument("--render-baseline", metavar="PATH", default=None,
                       help="render the known-red gate baseline JSON to PATH")
    parser.add_argument("--allow-pending", action="store_true")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--observed-state", default=None,
                        help="gitignored observed state file (scaffold cross-check only)")
    parser.add_argument("--skill-path", default=SKILL_PATH,
                        help="tracked skill file carrying the State file schema section")
    parser.render_invocation = "--render-baseline" in (
        sys.argv[1:] if argv is None else list(argv))
    args = parser.parse_args(argv)
    repo = args.repo_root or subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True,
        text=True).stdout.strip()
    if not repo:
        raise SystemExit("machinery_inventory: not inside a git repository")
    if args.render_baseline:
        return cmd_render_baseline(repo, args.render_baseline)
    if args.scaffold:
        return cmd_scaffold(repo, args.observed_state, skill_path=args.skill_path)
    return cmd_check(repo, args.allow_pending, args.skill_path)


if __name__ == "__main__":
    sys.exit(main())
