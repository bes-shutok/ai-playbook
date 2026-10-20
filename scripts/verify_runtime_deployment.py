#!/usr/bin/env python3
"""verify_runtime_deployment.py: post-walk deployment verification for the
runtime helper home (the closure diff plus the no-PYTHONPATH import probe).

The deployer calls this script after its walk with the resolved canonical
repo, runtime home, and mode; it also runs standalone. Two checks over one
runtime home against one canonical repo's runtime manifest:

- closure scan: the transitive plain-import closure of the manifest's admitted
  .py entries, over the canonical bytes (imports matched at any indentation,
  the basename mapping applied to scripts/-prefixed manifest lines, a visited
  set carried across the walk). A local sibling module
  (<repo>/scripts/<name>.py) the entries require but the manifest does not
  admit is a closure-gap violation; sibling existence alone gates the scan,
  so a local sibling shadowing a stdlib name is a gap too;
  canonical bytes that cannot be read or cannot parse are named violations
  (an unadmitted sibling has no manifest line to drop, so its remedy is
  restore-only). An import of a module that is not a local sibling
  (out-of-root) is not a gap: the import probe's provenance assertion owns
  out-of-root imports.
- import probe: one child per admitted .py entry (shell entries are outside
  the probe's domain), run from a fresh private per-run probe root (mode 0700,
  removed on exit regardless of outcome) holding dereferenced copies of the
  admitted entries the home legitimately deploys, laid out under a scripts/
  subdirectory. The child is
    python3 -I -S -B -c "<pinned core + provenance assertion>" <module> <probe-root>/scripts
  with the module name passed as argv (never interpolated into code text), its
  cwd set to that scripts/ directory, the repo's pinned validator interpreter
  preferred, and a minimized environment (no PYTHONPATH). After the import,
  every newly imported non-stdlib module's __file__ must resolve under the
  probe root; a violation names the entry and the offending module path.
  Classification is canonical-first, before any home byte is touched: an
  admitted name whose canonical file is missing is a canonical-missing
  violation (the walk's skip created nothing, so no deploy rerun can converge)
  and its home bytes are never copied or probed, whatever the home holds; an
  admitted entry absent from the home is a home-absent violation and is not
  copied; an admitted entry whose home bytes are not a symlink dereferencing
  into the canonical scripts directory is a not-canonical violation (remedy:
  run the deploy run from the primary checkout, or remove the foreign file)
  and is not copied or probed. The probe consumes deployed bytes only through
  symlinks that dereference into the canonical scripts directory, and copies
  read the verified realpath: it never reads or executes bytes whose
  provenance is not the canonical repo.

Output: one evidence line per violation, one summary line, then exactly one
final OUTCOME: line.

Exit codes: 0 pass (in check mode its findings never gate: they are
advisories), 1 deploy-mode violations, 3 tool error (usage violation, a
missing manifest, a repo path that is not a directory, an interpreter
without sys.stdlib_module_names, an unexpected internal failure).
"""

import argparse
import ast
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = "verify_runtime_deployment.py"

# The pinned probe core opens the child program; the provenance assertion
# appends to the same program with the module name still riding argv.
PROBE_CHILD_CODE = (
    "import importlib, sys\n"
    "sys.path.insert(0, sys.argv[2])\n"
    "seen = set(sys.modules)\n"
    "importlib.import_module(sys.argv[1])\n"
    "import os\n"
    "root = os.path.dirname(os.path.realpath(sys.argv[2]))\n"
    "stdlib_dir = os.path.dirname(os.path.realpath(os.__file__))\n"
    "escaped = []\n"
    "for name, module in sorted(sys.modules.items()):\n"
    "    if name in seen:\n"
    "        continue\n"
    "    top = name.split('.')[0]\n"
    "    if top in sys.stdlib_module_names or top in sys.builtin_module_names:\n"
    "        continue\n"
    "    path = getattr(module, '__file__', None)\n"
    "    if not path:\n"
    "        continue\n"
    "    real = os.path.realpath(path)\n"
    "    if real.startswith(stdlib_dir + os.sep):\n"
    "        continue\n"
    "    if real != root and not real.startswith(root + os.sep):\n"
    "        escaped.append(name + ' -> ' + real)\n"
    "if escaped:\n"
    "    sys.stderr.write('import left the probe root: ' + '; '.join(escaped) + '\\n')\n"
    "    raise SystemExit(7)\n"
)

REMEDY_GAP = "admit it in scripts/runtime-scripts.list and redeploy"
REMEDY_CANONICAL_MISSING = "restore the canonical file or drop the manifest line"
REMEDY_HOME_ABSENT = "run the deploy run (bash scripts/deploy_runtime_helpers.sh) to link it"
REMEDY_NOT_CANONICAL = (
    "run the deploy run from the primary checkout or remove the foreign file"
)
REMEDY_PROBE = (
    "inspect the named entry and module; a missing sibling is a manifest edit,"
    " otherwise park for the operator"
)
REMEDY_BYTES = "restore the canonical file or drop its manifest line"
REMEDY_BYTES_RESTORE_ONLY = "restore the canonical file"

PROBE_TIMEOUT_SECS = 120


class ToolError(Exception):
    pass


class UsageError(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(message)


def build_parser():
    parser = Parser(prog=TOOL)
    parser.add_argument("--repo", required=True, help="the canonical repo toplevel")
    parser.add_argument("--home", required=True, help="the runtime scripts directory")
    parser.add_argument(
        "--manifest",
        default=None,
        help="default: <repo>/scripts/runtime-scripts.list",
    )
    parser.add_argument("--mode", choices=("deploy", "check"), default="deploy")
    return parser


def manifest_entries(manifest):
    """Admitted basenames, comments and blanks skipped, scripts/ prefixes
    mapped to the flat runtime-home name; repeated lines are deduplicated
    with an order-preserving seen-set, so a duplicated admission line neither
    double-probes nor inflates the entry count."""
    entries = []
    seen = set()
    for raw in manifest.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name = Path(line).name
        if name in seen:
            continue
        seen.add(name)
        entries.append(name)
    return entries


def imported_tops(node):
    """Top-level module names of a plain import statement (relative imports
    are not local sibling imports in the flat layout)."""
    tops = []
    if isinstance(node, ast.Import):
        tops = [alias.name.split(".")[0] for alias in node.names]
    elif isinstance(node, ast.ImportFrom):
        if node.level == 0 and node.module:
            tops = [node.module.split(".")[0]]
    return [top for top in tops if top]


def remember(named, violations, klass, name, detail, remedy):
    if name in named:
        return
    named.add(name)
    violations.append((klass, name, detail, remedy))


def closure_scan(scripts_dir, entries, violations):
    """The transitive plain-import scan over admitted .py entries' canonical
    bytes; discovered unadmitted siblings are traversed too, so gaps are
    found at any depth. Sibling existence alone gates the scan: every
    existing local sibling shadows whatever shares its name, stdlib modules
    included, and is a gap when the manifest does not admit it."""
    admitted = set(entries)
    visited = set()
    named = set()
    queue = [name for name in entries if name.endswith(".py")]
    while queue:
        filename = queue.pop(0)
        if filename in visited:
            continue
        visited.add(filename)
        path = scripts_dir / filename
        if not path.is_file():
            continue  # a missing admitted entry is named by the probe side
        bytes_remedy = (
            REMEDY_BYTES if filename in admitted else REMEDY_BYTES_RESTORE_ONLY
        )
        try:
            source = path.read_bytes()
        except OSError as exc:
            remember(
                named, violations, "unreadable", "scripts/%s" % filename,
                "canonical bytes cannot be read: %s" % exc, bytes_remedy,
            )
            continue
        try:
            tree = ast.parse(source, filename=str(path))
        except (SyntaxError, ValueError):
            remember(
                named, violations, "unparseable", "scripts/%s" % filename,
                "canonical bytes do not parse", bytes_remedy,
            )
            continue
        for node in ast.walk(tree):
            for top in imported_tops(node):
                sibling = top + ".py"
                # Existence alone gates: an existing local sibling shadows
                # any stdlib module sharing its name and must be admitted.
                if not (scripts_dir / sibling).is_file():
                    continue
                if sibling not in admitted:
                    remember(
                        named, violations, "closure-gap", sibling,
                        "a local sibling the admitted entries import is not admitted",
                        REMEDY_GAP,
                    )
                queue.append(sibling)


def minimal_env():
    """A minimized child environment; PYTHONPATH is absent by construction."""
    env = {}
    for key in ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR"):
        value = os.environ.get(key)
        if value is not None:
            env[key] = value
    return env


def resolve_interpreter():
    """The repo's pinned validator interpreter when it answers, else this
    interpreter; returns (path, version) or (None, None)."""
    pinned = Path.home() / ".agents" / "venvs" / "ai-playbook-test" / "bin" / "python3"
    candidates = []
    if pinned.is_file():
        candidates.append(str(pinned))
    candidates.append(sys.executable)
    for candidate in candidates:
        try:
            proc = subprocess.run(
                [candidate, "-c", "import sys; print(sys.version.split()[0])"],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if proc.returncode == 0 and proc.stdout.strip():
            return candidate, proc.stdout.strip()
    return None, None


def probe_one(interpreter, probe_scripts, filename):
    """Run one probe child; None on success, else the named reason."""
    module = filename[:-3]
    try:
        proc = subprocess.run(
            [
                interpreter, "-I", "-S", "-B", "-c", PROBE_CHILD_CODE,
                module, str(probe_scripts),
            ],
            cwd=str(probe_scripts),
            env=minimal_env(),
            capture_output=True,
            text=True,
            timeout=PROBE_TIMEOUT_SECS,
        )
    except subprocess.TimeoutExpired:
        return "the import did not finish within %ds" % PROBE_TIMEOUT_SECS
    if proc.returncode == 0:
        return None
    detail = ""
    for line in reversed((proc.stderr or "").splitlines()):
        if line.strip():
            detail = line.strip()
            break
    return detail or "the probe child exited %d" % proc.returncode


def canonical_link_realpath(path, canonical_real):
    """The verified realpath when path is a symlink whose realpath resolves
    inside the canonical scripts directory, else None; the caller copies from
    the returned path, so the checked path is the read path."""
    if not path.is_symlink():
        return None
    real = Path(os.path.realpath(path))
    if str(real).startswith(str(canonical_real) + os.sep):
        return real
    return None


def run_probe(scripts_dir, home, entries, violations, interpreter):
    """Materialize the probe root from the home's canonical-linked entries and
    probe each admitted .py entry; returns the number of entrypoints probed.
    Classification is canonical-first: an admitted name missing from the
    canonical scripts directory is canonical-missing and its home bytes are
    never executed; only home entries that are symlinks dereferencing into
    the canonical scripts directory are copied, and copied from the verified
    realpath, so the probe never reads or executes bytes whose provenance is
    not the canonical repo."""
    root = Path(tempfile.mkdtemp(prefix="verify-runtime-deployment-"))
    try:
        os.chmod(root, 0o700)
        probe_scripts = root / "scripts"
        probe_scripts.mkdir()
        canonical_real = scripts_dir.resolve()
        named = set()
        probed = []
        for filename in entries:
            src = home / filename
            if not (scripts_dir / filename).is_file():
                remember(
                    named, violations, "canonical-missing", filename,
                    "admitted but missing from the canonical repo, so the walk"
                    " created nothing and the entry cannot be imported from the"
                    " home",
                    REMEDY_CANONICAL_MISSING,
                )
                continue
            if not src.is_file():  # follows symlinks; a dangling link is absent
                remember(
                    named, violations, "home-absent", filename,
                    "admitted but absent from the runtime home",
                    REMEDY_HOME_ABSENT,
                )
                continue
            verified = canonical_link_realpath(src, canonical_real)
            if verified is None:
                remember(
                    named, violations, "not-canonical", filename,
                    "the home's entry is not a symlink into the canonical"
                    " scripts directory; its bytes are not executed",
                    REMEDY_NOT_CANONICAL,
                )
                continue
            try:
                shutil.copyfile(verified, probe_scripts / filename)
            except OSError as exc:
                remember(
                    named, violations, "unreadable", filename,
                    "the entry's canonical bytes cannot be read: %s" % exc,
                    REMEDY_BYTES,
                )
                continue
            if filename.endswith(".py"):
                probed.append(filename)
        for filename in probed:
            reason = probe_one(interpreter, probe_scripts, filename)
            if reason is not None:
                violations.append(("probe-fail", filename, reason, REMEDY_PROBE))
        return len(probed)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def tool_error(message):
    print("error: %s" % message, file=sys.stderr)
    print("OUTCOME: tool_error")
    return 3


def run(args):
    if not hasattr(sys, "stdlib_module_names"):
        raise ToolError(
            "the verifier needs a python with sys.stdlib_module_names (3.10+)"
        )
    repo = Path(args.repo).resolve()
    home = Path(args.home).resolve()
    manifest = (
        Path(args.manifest).resolve()
        if args.manifest
        else repo / "scripts" / "runtime-scripts.list"
    )
    if not repo.is_dir():
        raise ToolError("the repo path is not a directory: %s" % args.repo)
    if not manifest.is_file():
        raise ToolError("the manifest is missing: %s" % manifest)
    entries = manifest_entries(manifest)
    violations = []
    closure_scan(repo / "scripts", entries, violations)
    interpreter, version = resolve_interpreter()
    if interpreter is None:
        raise ToolError(
            "no probe interpreter answered the version query (the pinned"
            " $HOME/.agents/venvs/ai-playbook-test/bin/python3 and"
            " the running interpreter both failed)"
        )
    probed = run_probe(repo / "scripts", home, entries, violations, interpreter)
    for klass, name, detail, remedy in violations:
        print("verify-%s: %s: %s (remedy: %s)" % (klass, name, detail, remedy))
    print(
        "verification: %d manifest entries, %d entrypoints probed with %s"
        " (python %s), %d violation(s)"
        % (len(entries), probed, interpreter, version, len(violations))
    )
    if args.mode == "deploy" and violations:
        print("OUTCOME: fail")
        return 1
    print("OUTCOME: pass")
    return 0


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
    except UsageError as exc:
        return tool_error(str(exc))
    try:
        return run(args)
    except ToolError as exc:
        return tool_error(str(exc))
    except Exception as exc:  # an unexpected failure is never a silent pass
        return tool_error("internal failure: %s: %s" % (type(exc).__name__, exc))


if __name__ == "__main__":
    sys.exit(main())
