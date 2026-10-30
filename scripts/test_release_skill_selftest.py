#!/usr/bin/env python3
"""Hermetic scratch-repository selftest for the release skill scripts.

Plan: docs/history/plans/2026-09-26-release-skill.md, Task 1 (RED harness). The
two release scripts start as ``exit 1`` stubs, so every case that needs working
behavior fails; Task 2 implements the scripts against this harness.

Harness-pinned seams (Task 2 implements against these):

- Invocation: ``bash scripts/release-authoring.sh <drafted-section-file>``
  runs in the primary checkout; then ``bash scripts/release-rewrite.sh
  <groups-file>`` runs with the authoring lock exports in the environment.
  The groups file path (the authoring stdout's final ``groups-file <path>``
  line) is passed to the rewrite script as its single argv argument.
- Drafted section file format: the CHANGELOG markdown section, then a line
  ``release-groups:``, then alternating ``group <count>`` / ``msg <subject>``
  lines, oldest group first. Counts must tile the publish delta INCLUDING the
  notes commit the authoring script is about to create; that commit is the
  newest one, so it belongs to the last group.
- The drafted section file carries a ``.md`` suffix so the em-dash checker's
  plain ``file`` mode scans the whole file.
- Lock stub contract (DONE_LOCK_SCRIPT): verbs ``acquire``/``wait-acquire``
  print ``export DONE_LOCK_DIR=...`` / ``export DONE_LOCK_TOKEN=...`` lines on
  success; ``status`` exits 0 with a ``held`` line when the env token matches a
  live lock and exits 1 with ``free`` otherwise; ``release``/``release-repo``
  are token-fenced from the environment and log a ``RELEASE`` witness line
  either way. Every invocation appends an ``ACQUIRE``/``RELEASE`` witness line
  to the harness lock log.
- Scanner modes copied into the scratch repo at
  ``scripts/scan-public-hygiene.sh``: ``real`` (this repo's scanner, probed in
  BOTH directions before use: exit 0 plus the PASS marker on clean content,
  exit 1 plus FAIL naming the path on a hit), ``noop`` (exit 0), ``exit2``
  (exit 2), ``exit3`` (exit 3), ``lognoop`` (exit 0 plus an argv witness log,
  used by the tree-materialization-failure case to prove no materialized file
  reaches the scanner), and ``envlog`` (exit 0 plus an environment and argv
  witness log, used to pin the release remote and the helper-script
  environment settings at the scanner invocation).
- The rewrite runs its scanner through the locator helper
  ``scripts/release-privacy-locators.py``; the helper-level contract cases
  (row acceptance, the 65,536-byte bound, escaping, exit passthrough) drive
  the helper directly against a fixture scanner stub that replays fixed
  stdout bytes and a chosen exit code (plan
  docs/history/plans/2026-10-26-release-privacy-gate-diagnostics-and-replay.md,
  Task 1).
- Fixture layout per case: temp dir holding a bare ``origin``, a clone whose
  ``main`` carries 6 commits in 3 contiguous feature groups (distinct author
  names and dates per source commit, one group deleting a file, one
  rename-with-scrub pair whose old blob was added in an earlier group), a
  pinned per-case ``TMPDIR`` (push scripts and materialization roots land
  there), a lock root plus witness log, a fixture patterns file carrying one
  deterministic deny line, and a per-case git shim directory pinned on PATH.
  Every artifact lives under one ``mktemp -d``-style directory torn down on
  every exit path; the harness never deletes a persisted push script itself.

  Pinned seams documented by review r1 (Task 1 intermediate review): the
  groups file is passed to the rewrite script as argv; the drafted section
  carries a ``release-groups:`` marker; the merge-commit case pins the FULL
  40-character offending SHA in the abort output; the tree-tamper shim fires
  on porcelain ``git commit`` and the CAS shim on porcelain ``git worktree
  add`` (plumbing implementations must keep those firing points).
"""

from __future__ import annotations

import datetime
import hashlib
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORING_SCRIPT = ROOT / "scripts" / "release-authoring.sh"
REWRITE_SCRIPT = ROOT / "scripts" / "release-rewrite.sh"
LOCATOR_HELPER = ROOT / "scripts" / "release-privacy-locators.py"
REAL_SCANNER = ROOT / "scripts" / "scan-public-hygiene.sh"
REAL_EM_DASH_CHECK = ROOT / "scripts" / "check-no-em-dash.sh"

DENY_TOKEN = "RELEASE-SELFTEST-SECRET-TOKEN"
GROUPS_MARKER = "release-groups:"
EM_DASH = "\u2014"

MSG_G1 = "alpha feature work"
MSG_G2 = "docs and shared scaffolding"
MSG_G3 = "docs rework and cleanup"
DEFAULT_MSGS = [MSG_G1, MSG_G2, MSG_G3]
# Tiles the 6 source commits plus the authoring script's own notes commit
# (newest, so it folds into the last group).
DEFAULT_COUNTS = [2, 2, 3]
COMMITTER = ("Release Selftest", "selftest@example.invalid")

# (subject, author name, author email, author ISO date); distinct per commit.
# The offsets are non-UTC on purpose: git renders a zero UTC offset as "Z" in
# strict ISO (%aI), so a "+00:00" fixture string could never equal %aI output
# and the author-preservation assertion would be unsatisfiable regardless of
# the implementation. Non-zero offsets round-trip %aI verbatim on every git.
SOURCE_COMMITS = [
    ("feat: alpha one", "Author One", "one@example.invalid", "2026-09-20T10:01:00+02:00"),
    ("feat: alpha two", "Author Two", "two@example.invalid", "2026-09-20T10:02:00+02:00"),
    ("docs: guide draft", "Author Three", "three@example.invalid", "2026-09-20T10:03:00+02:00"),
    ("chore: shared placeholder", "Author Four", "four@example.invalid", "2026-09-20T10:04:00+02:00"),
    ("docs: rename guide with scrub", "Author Five", "five@example.invalid", "2026-09-20T10:05:00+02:00"),
    ("chore: drop placeholder", "Author Six", "six@example.invalid", "2026-09-20T10:06:00+02:00"),
]
# Oldest source commit of each group of the default [2, 2, 3] tiling.
DEFAULT_EXPECTED_AUTHORS = [
    (SOURCE_COMMITS[0][1], SOURCE_COMMITS[0][3]),
    (SOURCE_COMMITS[2][1], SOURCE_COMMITS[2][3]),
    (SOURCE_COMMITS[4][1], SOURCE_COMMITS[4][3]),
]

UNTRACKED_HELPERS = ("scan-public-hygiene.sh", "check-no-em-dash.sh")

GIT_CONFIG_GLOBAL_TEXT = """[user]
	name = Release Selftest
	email = selftest@example.invalid
[commit]
	gpgsign = false
[init]
	defaultBranch = main
[core]
	hooksPath =
"""

PATTERNS_TEXT = "# selftest fixture deny patterns\n" + DENY_TOKEN + "\n"

LOCK_STUB_TEMPLATE = """#!/usr/bin/env bash
# selftest done-lock stub: acquire/status/release env-token contract witness.
set -euo pipefail
LOG="@LOG@"
ROOT_DIR="@ROOT@"
log() { printf '%s\\n' "$*" >> "$LOG"; }
cmd="${1:-}"
shift || true
case "$cmd" in
  acquire|wait-acquire|merge-acquire|merge-wait-acquire)
    label=""
    while [ "$#" -gt 0 ]; do
      case "$1" in
        --label) label="${2:-}"; shift 2 ;;
        --max-wait) shift 2 ;;
        *) shift ;;
      esac
    done
    dir="$(mktemp -d "$ROOT_DIR/lock.XXXXXX")"
    token="tok-$$-$RANDOM-$(date +%s)"
    printf '%s' "$token" > "$dir/token"
    log "ACQUIRE token=$token label=$label dir=$dir"
    printf 'export DONE_LOCK_DIR=%q\\n' "$dir"
    printf 'export DONE_LOCK_TOKEN=%q\\n' "$token"
    ;;
  status|merge-status)
    if [ -n "${DONE_LOCK_DIR:-}" ] && [ -f "${DONE_LOCK_DIR}/token" ] \\
       && [ "$(cat "${DONE_LOCK_DIR}/token")" = "${DONE_LOCK_TOKEN:-}" ]; then
      echo "done-lock: held (${DONE_LOCK_DIR})"
      exit 0
    fi
    echo "done-lock: free"
    exit 1
    ;;
  release|release-repo|merge-release|merge-release-repo)
    log "RELEASE token=${DONE_LOCK_TOKEN:-} dir=${DONE_LOCK_DIR:-}"
    if [ -n "${DONE_LOCK_DIR:-}" ] && [ -d "$DONE_LOCK_DIR" ] \\
       && [ -f "${DONE_LOCK_DIR}/token" ] \\
       && [ "$(cat "${DONE_LOCK_DIR}/token")" = "${DONE_LOCK_TOKEN:-}" ]; then
      rm -rf "$DONE_LOCK_DIR"
      echo "done-lock: released"
    else
      echo "done-lock: lock already released"
    fi
    ;;
  *)
    echo "selftest lock stub: unknown command: $cmd" >&2
    exit 1
    ;;
esac
"""


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


class ReleaseSkillSelftest(unittest.TestCase):
    """Every prescribed Task 1 case against the real scripts, hermetically."""

    def setUp(self) -> None:
        self.base = Path(tempfile.mkdtemp(prefix="release-selftest-"))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.tmpdir = self.base / "tmpdir"
        self.tmpdir.mkdir()
        self.origin = self.base / "origin.git"
        self.clone = self.base / "clone"
        self.shim_dir = self.base / "shim"
        self.shim_dir.mkdir()
        self.lock_root = self.base / "lock-root"
        self.lock_root.mkdir()
        self.lock_log = self.base / "lock.log"
        self.lock_log.touch()
        self.scanner_log = self.base / "scanner.log"
        self.cas_record = self.base / "cas-main.txt"
        self.patterns = self.base / "hygiene.patterns"
        self.patterns.write_text(PATTERNS_TEXT, encoding="utf-8")
        # Pinned HOME carrying the scanner's default patterns file, so the
        # default-patterns branch of the privacy gate is hermetic (it never
        # reads the host's own ~/.ai-playbook file).
        self.home = self.base / "home"
        (self.home / ".ai-playbook").mkdir(parents=True)
        self.default_patterns = self.home / ".ai-playbook" / "public-hygiene.patterns"
        self.default_patterns.write_text(PATTERNS_TEXT, encoding="utf-8")
        self.empty_home = self.base / "empty-home"
        self.empty_home.mkdir()
        self.git_global = self.base / "git-config-global"
        self.git_global.write_text(GIT_CONFIG_GLOBAL_TEXT, encoding="utf-8")
        self.section_path = self.base / "drafted-section.md"
        self.real_git = shutil.which("git")
        self.assertIsNotNone(self.real_git, "git must be on PATH")
        self._write_lock_stub()
        self._write_shim("pass")

    # ------------------------------------------------------------------
    # Environment and fixture helpers
    # ------------------------------------------------------------------

    def _git_env_overrides(self) -> dict:
        return {
            "GIT_CONFIG_GLOBAL": str(self.git_global),
            "GIT_CONFIG_SYSTEM": os.devnull,
        }

    def _gitx(self, *args, cwd=None, env_extra=None, check=True):
        """Hermetic git subprocess for fixture build and assertions."""
        env = dict(os.environ)
        env.update(self._git_env_overrides())
        if env_extra:
            env.update(env_extra)
        proc = subprocess.run(
            ["git", *args], cwd=str(cwd or self.clone), env=env,
            capture_output=True, text=True,
        )
        if check and proc.returncode != 0:
            self.fail(
                "fixture git %s failed rc=%s\nstderr: %s\nstdout: %s"
                % (" ".join(args), proc.returncode, proc.stderr, proc.stdout)
            )
        return proc

    def _run_env(self, lock_exports=None, env_extra=None) -> dict:
        """Environment for invoking the real scripts: pinned TMPDIR, lock stub,
        fixture patterns file, hermetic git config, and the per-case shim dir
        prepended to PATH. TZ is pinned to UTC, RELEASE_REMOTE is pinned to
        origin, and ambient git-context and author/committer variables are
        stripped, so a midnight rollover in the local zone, a leaked
        GIT_DIR/GIT_CONFIG_COUNT/GIT_*_DATE, or an ambient remote name from
        the calling session cannot flip date-dependent, identity-dependent,
        or remote-dependent behavior under test."""
        env = dict(os.environ)
        env.update(self._git_env_overrides())
        env["TMPDIR"] = str(self.tmpdir)
        env["DONE_LOCK_SCRIPT"] = str(self.lock_stub)
        env["SELFTEST_LOCK_LOG"] = str(self.lock_log)
        env["SELFTEST_SCANNER_LOG"] = str(self.scanner_log)
        env["PUBLIC_HYGIENE_PATTERNS_FILE"] = str(self.patterns)
        env["RELEASE_REMOTE"] = "origin"
        env["TZ"] = "UTC"
        for leak in (
            "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_CONFIG_COUNT",
            "GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_AUTHOR_DATE",
            "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL", "GIT_COMMITTER_DATE",
        ):
            env.pop(leak, None)
        env.pop("DONE_LOCK_DIR", None)
        env.pop("DONE_LOCK_TOKEN", None)
        env["PATH"] = str(self.shim_dir) + os.pathsep + os.environ.get("PATH", "")
        if lock_exports:
            env.update(lock_exports)
        if env_extra:
            env.update(env_extra)
        return env

    def _write_lock_stub(self) -> None:
        path = self.base / "lock-stub.sh"
        path.write_text(
            LOCK_STUB_TEMPLATE.replace("@LOG@", str(self.lock_log)).replace("@ROOT@", str(self.lock_root)),
            encoding="utf-8",
        )
        path.chmod(0o755)
        self.lock_stub = path

    def _write_shim(self, name: str) -> None:
        """(Re)write the per-case git wrapper in the shim directory."""
        real = self.real_git
        if name == "pass":
            body = (
                "#!/usr/bin/env bash\n"
                "# selftest pass-through git shim\n"
                'exec "%s" "$@"\n' % real
            )
        elif name == "archive-fail":
            body = (
                "#!/usr/bin/env bash\n"
                "# selftest git shim: git archive fails (result materialization must abort)\n"
                'if [ "${1:-}" = "archive" ]; then\n'
                '  echo "selftest shim: git archive forced to fail" >&2\n'
                "  exit 42\n"
                "fi\n"
                'exec "%s" "$@"\n' % real
            )
        elif name == "tree-tamper":
            body = (
                "#!/usr/bin/env bash\n"
                "# selftest git shim: corrupt the rewritten tip tree after each rewrite commit\n"
                'if [ "${1:-}" = "commit" ] && [ -z "${SELFTEST_TAMPER_GUARD:-}" ]; then\n'
                "  export SELFTEST_TAMPER_GUARD=1\n"
                '  "%s" "$@" || exit $?\n' % real
                + "  printf 'selftest tamper line\\n' >> README.md\n"
                '  "%s" add -- README.md || exit $?\n' % real
                + '  exec "%s" commit --amend --no-edit\n' % real
                + "fi\n"
                'exec "%s" "$@"\n' % real
            )
        elif name == "cas-tamper":
            body = (
                "#!/usr/bin/env bash\n"
                "# selftest git shim: advance main once the rewrite worktree materializes\n"
                'if [ "${1:-}" = "worktree" ] && [ "${2:-}" = "add" ] && [ -z "${SELFTEST_TAMPER_GUARD:-}" ]; then\n'
                '  "%s" "$@" || exit $?\n' % real
                + "  export SELFTEST_TAMPER_GUARD=1\n"
                "  (\n"
                '    cd "%s" || exit 1\n' % self.clone
                + '    "%s" commit --allow-empty -q -m "concurrent commit during release" || exit 1\n' % real
                + '    "%s" rev-parse HEAD > "%s"\n' % (real, self.cas_record)
                + "  )\n"
                "  exit 0\n"
                "fi\n"
                'exec "%s" "$@"\n' % real
            )
        elif name == "commit-fail":
            body = (
                "#!/usr/bin/env bash\n"
                "# selftest git shim: every git commit fails, so the authoring\n"
                "# step's unguarded step-8 commit exits under set -e and only the\n"
                "# global EXIT trap can relay the lock exports.\n"
                'if [ "${1:-}" = "commit" ]; then\n'
                '  echo "selftest shim: git commit forced to fail" >&2\n'
                "  exit 7\n"
                "fi\n"
                'exec "%s" "$@"\n' % real
            )
        else:
            self.fail("unknown shim name: %s" % name)
        path = self.shim_dir / "git"
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def _today(self) -> str:
        """Date-dependent fixture values come from the scripts' own ``date``,
        under the same UTC pin the scripts run with (see ``_run_env``), so a
        local-zone midnight rollover cannot split the harness clock from the
        scripts' clock."""
        env = dict(os.environ)
        env["TZ"] = "UTC"
        out = subprocess.run(["date", "+%Y-%m-%d"], capture_output=True, text=True, check=True, env=env)
        return out.stdout.strip()

    def _yesterday(self) -> str:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        return (now_utc - datetime.timedelta(days=1)).date().isoformat()

    def _today_section(self, marker: str) -> str:
        return "## %s\n\n%s\n" % (self._today(), marker)

    def _build_fixture(self, variant: str = "clean") -> None:
        """Bare origin plus a clone carrying the 6 source commits in 3
        contiguous feature groups, shaped per variant."""
        self.assertFalse(self.clone.exists(), "fixture must be built once per case")
        # Bare origin via a seed repo (avoids empty-clone branch quirks).
        self._gitx("init", "--bare", "-q", str(self.origin), cwd=self.base)
        seed = self.base / "seed"
        seed.mkdir()
        self._gitx("init", "-q", cwd=seed)
        (seed / "README.md").write_bytes(b"scratch repository\n")
        adds = ["README.md"]
        if variant == "published_changelog":
            (seed / "CHANGELOG.md").write_text(self._today_section("published section marker"), encoding="utf-8")
            adds.append("CHANGELOG.md")
        if variant == "changelog_em_dash":
            (seed / "CHANGELOG.md").write_text(
                "# Changelog\n\n## 2026-01-01\n\nOlder section carrying " + EM_DASH + " an em dash\n",
                encoding="utf-8",
            )
            adds.append("CHANGELOG.md")
        self._gitx("add", "--", *adds, cwd=seed)
        self._gitx("commit", "-q", "-m", "initial commit", cwd=seed)
        self._gitx("push", "-q", str(self.origin), "main", cwd=seed)
        self._gitx("clone", "-q", str(self.origin), str(self.clone), cwd=self.base)

        # 6 source commits, 3 contiguous feature groups, distinct authors/dates.
        one = "alpha line one\n"
        if variant == "dirty_cleaned":
            one = "alpha line one carrying " + DENY_TOKEN + "\n"
        guide = "guide content v1\n"
        if variant == "rename_scrub":
            guide = "guide v1 carrying " + DENY_TOKEN + "\n"

        self._commit_actions(0, [("write", "feature-alpha/one.txt", one)])
        self._commit_actions(1, [("write", "feature-alpha/two.txt", "alpha line two\n")])
        c3 = [("write", "docs/guide.md", guide)]
        if variant == "dirty_cleaned":
            c3.append(("write", "feature-alpha/one.txt", "alpha line one cleaned\n"))
        self._commit_actions(2, c3)
        c4 = [("write", "shared/placeholder.txt", "shared placeholder\n")]
        if variant == "added_deleted":
            c4 = [("write", "shared/placeholder.txt", "placeholder carrying " + DENY_TOKEN + "\n")]
        if variant == "outside_scope":
            c4.append(("write", "scripts/tool.sh", "#!/bin/sh\nprintf '%s\\n' " + DENY_TOKEN + "\n"))
        if variant == "excluded_license":
            c4.append(("write", "pkg/LICENSE.txt", "fixture license text\n" + DENY_TOKEN + "\n"))
        if variant == "typechange":
            c4.append(("symlink", "link/alias", "docs/guide.md"))
        self._commit_actions(3, c4)
        self._commit_actions(4, [("rename", "docs/guide.md", "docs/manual.md", "manual content scrubbed v2\n")])
        c6 = [("delete", "shared/placeholder.txt")]
        if variant == "typechange":
            c6.append(("write-over", "link/alias", "regular file carrying " + DENY_TOKEN + "\n"))
        self._commit_actions(5, c6)

        # Variant extras layered after the 6 source commits.
        if variant == "merge":
            self._gitx("checkout", "-q", "-b", "side")
            (self.clone / "side").mkdir()
            (self.clone / "side" / "extra.txt").write_text("side work\n", encoding="utf-8")
            self._gitx("add", "--", "side/extra.txt")
            self._gitx("commit", "-q", "-m", "side work")
            self._gitx("checkout", "-q", "main")
            self._gitx("merge", "--no-ff", "-m", "merge side work", "side")
        if variant == "changelog_delta":
            (self.clone / "CHANGELOG.md").write_text(self._today_section("delta section marker"), encoding="utf-8")
            self._gitx("add", "--", "CHANGELOG.md")
            self._gitx("commit", "-q", "-m", "changelog: today section in delta")

        # Helper script copies stay UNTRACKED in the scratch repo working tree,
        # so they never become publish-delta blobs the privacy gate would scan.
        helper_dir = self.clone / "scripts"
        helper_dir.mkdir(exist_ok=True)
        shutil.copyfile(REAL_SCANNER, helper_dir / "scan-public-hygiene.sh")
        shutil.copyfile(REAL_EM_DASH_CHECK, helper_dir / "check-no-em-dash.sh")

    def _commit_actions(self, index: int, actions) -> None:
        for action in actions:
            op = action[0]
            if op == "write":
                _, rel, content = action
                path = self.clone / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                self._gitx("add", "--", rel)
            elif op == "delete":
                (self.clone / action[1]).unlink()
                self._gitx("add", "--", action[1])
            elif op == "symlink":
                _, rel, target = action
                path = self.clone / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                os.symlink(target, path)
                self._gitx("add", "--", rel)
            elif op == "write-over":
                _, rel, content = action
                path = self.clone / rel
                if path.is_symlink() or path.exists():
                    path.unlink()
                path.write_text(content, encoding="utf-8")
                self._gitx("add", "--", rel)
            elif op == "rename":
                _, old, new, content = action
                self._gitx("mv", "--", old, new)
                (self.clone / new).write_text(content, encoding="utf-8")
                self._gitx("add", "--", new)
            else:
                self.fail("unknown fixture action: %s" % op)
        subject, name, email, date = SOURCE_COMMITS[index]
        self._gitx(
            "commit", "-q", "-m", subject,
            env_extra={
                "GIT_AUTHOR_NAME": name,
                "GIT_AUTHOR_EMAIL": email,
                "GIT_AUTHOR_DATE": date,
                "GIT_COMMITTER_NAME": COMMITTER[0],
                "GIT_COMMITTER_EMAIL": COMMITTER[1],
                "GIT_COMMITTER_DATE": date,
            },
        )

    def _advance_origin(self) -> None:
        """Create a commit on origin that local main does not have."""
        diverger = self.base / "diverger"
        self._gitx("clone", "-q", str(self.origin), str(diverger), cwd=self.base)
        self._gitx("commit", "-q", "--allow-empty", "-m", "divergent origin commit", cwd=diverger)
        self._gitx("push", "-q", str(self.origin), "main", cwd=diverger)

    # ------------------------------------------------------------------
    # Scanner / lock stub installation
    # ------------------------------------------------------------------

    def _install_scanner(self, mode: str) -> None:
        """Install the per-case scanner at scripts/scan-public-hygiene.sh in the
        scratch repo. ``real`` is probed in BOTH directions so an exit-2 crash
        can never masquerade as a pass or as a pattern hit."""
        self.assertTrue(self.clone.exists(), "build the fixture before installing the scanner")
        target = self.clone / "scripts" / "scan-public-hygiene.sh"
        if mode == "real":
            shutil.copyfile(REAL_SCANNER, target)
        elif mode == "noop":
            target.write_text("#!/usr/bin/env bash\n# selftest no-op scanner stub\nexit 0\n", encoding="utf-8")
        elif mode == "exit2":
            target.write_text(
                "#!/usr/bin/env bash\n"
                "# selftest scanner stub: environment error\n"
                'echo "selftest scanner stub: environment error" >&2\n'
                "exit 2\n",
                encoding="utf-8",
            )
        elif mode == "exit3":
            target.write_text(
                "#!/usr/bin/env bash\n"
                "# selftest scanner stub: tool error under the outcome contract\n"
                'echo "selftest scanner stub: tool error" >&2\n'
                "exit 3\n",
                encoding="utf-8",
            )
        elif mode == "envlog":
            target.write_text(
                "#!/usr/bin/env bash\n"
                "# selftest env-logging scanner stub: witness the invocation\n"
                "# environment, argv, and the effective patterns bytes, then pass.\n"
                'log="${SELFTEST_SCANNER_LOG:?}"\n'
                "{\n"
                '  printf \'RELEASE_REMOTE=%s\\n\' "${RELEASE_REMOTE-}"\n'
                '  printf \'PUBLIC_HYGIENE_REPO_ROOT=%s\\n\' "${PUBLIC_HYGIENE_REPO_ROOT-}"\n'
                '  printf \'PUBLIC_HYGIENE_PATTERNS_FILE=%s\\n\' "${PUBLIC_HYGIENE_PATTERNS_FILE-}"\n'
                '  printf \'SELF=%s\\n\' "$0"\n'
                '  printf \'PATTERNS-BYTES>\\n\'\n'
                '  cat "${PUBLIC_HYGIENE_PATTERNS_FILE-}" 2>/dev/null\n'
                '  printf \'END-PATTERNS-BYTES\\n\'\n'
                "  printf 'ARGV'\n"
                '  for arg in "$@"; do printf \' %s\' "$arg"; done\n'
                "  printf '\\n'\n"
                '} >> "$log"\n'
                "exit 0\n",
                encoding="utf-8",
            )
        elif mode == "hitlog":
            target.write_text(
                "#!/usr/bin/env bash\n"
                "# selftest hit-logging scanner stub: witness the invocation and\n"
                "# the scanned groups bytes, then emit one fixed FAIL row carrying\n"
                "# the deny token and exit 1 (a privacy hit).\n"
                'log="${SELFTEST_SCANNER_LOG:?}"\n'
                "{\n"
                '  printf \'RELEASE_REMOTE=%s\\n\' "${RELEASE_REMOTE-}"\n'
                '  printf \'PUBLIC_HYGIENE_REPO_ROOT=%s\\n\' "${PUBLIC_HYGIENE_REPO_ROOT-}"\n'
                '  printf \'PUBLIC_HYGIENE_PATTERNS_FILE=%s\\n\' "${PUBLIC_HYGIENE_PATTERNS_FILE-}"\n'
                '  printf \'GROUPS-BYTES>\\n\'\n'
                '  cat "${PUBLIC_HYGIENE_REPO_ROOT:-}/release-groups.txt" 2>/dev/null\n'
                '  printf \'END-GROUPS-BYTES\\n\'\n'
                "  printf 'ARGV'\n"
                '  for arg in "$@"; do printf \' %s\' "$arg"; done\n'
                "  printf '\\n'\n"
                '} >> "$log"\n'
                "printf 'FAIL: files\\n'\n"
                'printf \'docs/manual.md:2:%s\\n\' "' + DENY_TOKEN + '"\n'
                "printf '\\n'\n"
                "printf '=== 1 public-hygiene failure(s) ===\\n'\n"
                "printf 'OUTCOME: fail\\n'\n"
                "exit 1\n",
                encoding="utf-8",
            )
        elif mode == "lognoop":
            target.write_text(
                "#!/usr/bin/env bash\n"
                "# selftest logging no-op scanner stub\n"
                'log="${SELFTEST_SCANNER_LOG:?}"\n'
                "{\n"
                "  printf 'SCAN'\n"
                '  for arg in "$@"; do printf \' %s\' "$arg"; done\n'
                "  printf '\\n'\n"
                "} >> \"$log\"\n"
                "exit 0\n",
                encoding="utf-8",
            )
        else:
            self.fail("unknown scanner mode: %s" % mode)
        target.chmod(0o755)
        if mode == "real":
            self._probe_real_scanner(target)

    def _probe_real_scanner(self, target: Path) -> None:
        probe = self.base / "scanner-probe"
        probe.mkdir(exist_ok=True)
        (probe / "clean-sample.md").write_text("clean sample content\n", encoding="utf-8")
        (probe / "hit-sample.md").write_text("dirty sample carrying " + DENY_TOKEN + "\n", encoding="utf-8")
        env = dict(os.environ)
        env.update(self._git_env_overrides())
        env["PUBLIC_HYGIENE_REPO_ROOT"] = str(probe)
        env["PUBLIC_HYGIENE_PATTERNS_FILE"] = str(self.patterns)
        clean = subprocess.run(
            ["bash", str(target), "--files", "clean-sample.md"],
            cwd=str(probe), env=env, capture_output=True, text=True,
        )
        self.assertEqual(
            clean.returncode, 0,
            "copied real scanner must pass clean content (exit 0), got rc=%s:\n%s\n%s"
            % (clean.returncode, clean.stdout, clean.stderr),
        )
        self.assertIn("PASS (public hygiene", clean.stdout, "clean probe must print the PASS marker")
        # Two named files: rg prints paths in the FAIL block for a multi-file
        # invocation, so the probe can assert the hit is named by its path.
        hit = subprocess.run(
            ["bash", str(target), "--files", "clean-sample.md", "hit-sample.md"],
            cwd=str(probe), env=env, capture_output=True, text=True,
        )
        self.assertEqual(
            hit.returncode, 1,
            "copied real scanner must fail a hit (exit 1), got rc=%s:\n%s\n%s"
            % (hit.returncode, hit.stdout, hit.stderr),
        )
        self.assertIn("FAIL:", hit.stdout, "hit probe must print a FAIL block")
        self.assertIn("hit-sample.md", hit.stdout, "hit probe must name the offending path")
        self.assertNotIn("clean-sample.md", hit.stdout, "the clean file must produce no hit")

    # ------------------------------------------------------------------
    # Script invocation steps
    # ------------------------------------------------------------------

    def _draft_section(self, counts, msgs, marker: str, extra_line: str = None) -> Path:
        lines = ["## %s" % self._today(), "", marker, ""]
        if extra_line:
            lines += [extra_line, ""]
        lines.append(GROUPS_MARKER)
        for count, msg in zip(counts, msgs):
            lines.append("group %d" % count)
            lines.append("msg %s" % msg)
        self.section_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return self.section_path

    def _authoring_step(self):
        return subprocess.run(
            ["bash", str(AUTHORING_SCRIPT), str(self.section_path)],
            cwd=str(self.clone), env=self._run_env(), capture_output=True, text=True,
        )

    def _parse_authoring(self, proc):
        exports = {}
        groups_path = None
        for line in proc.stdout.splitlines():
            if line.startswith("export DONE_LOCK_DIR="):
                exports["DONE_LOCK_DIR"] = _unquote(line.split("=", 1)[1])
            elif line.startswith("export DONE_LOCK_TOKEN="):
                exports["DONE_LOCK_TOKEN"] = _unquote(line.split("=", 1)[1])
            elif line.startswith("groups-file "):
                groups_path = line[len("groups-file "):].strip()
        return exports, groups_path

    def _require_authoring_contract(self, proc):
        self.assertEqual(
            proc.returncode, 0,
            "authoring script failed rc=%s\nstdout:\n%s\nstderr:\n%s"
            % (proc.returncode, proc.stdout, proc.stderr),
        )
        exports, groups_path = self._parse_authoring(proc)
        self.assertTrue(
            exports.get("DONE_LOCK_DIR") and exports.get("DONE_LOCK_TOKEN"),
            "authoring stdout carried no DONE_LOCK exports:\n%s" % proc.stdout,
        )
        self.assertTrue(
            groups_path,
            "authoring stdout carried no final groups-file line:\n%s" % proc.stdout,
        )
        return exports, groups_path

    def _rewrite_step(self, groups_path, exports, shim: str = "pass",
                      recovery_base: str = None, expect_remote_oid: str = None,
                      draft=None, extra_env: dict = None):
        self._write_shim(shim)
        args = ["bash", str(REWRITE_SCRIPT), str(groups_path)]
        if recovery_base is not None or expect_remote_oid is not None:
            self.assertTrue(
                recovery_base is not None and expect_remote_oid is not None,
                "recovery flags are paired or absent",
            )
            args += ["--recovery-base", recovery_base, "--expect-remote-oid", expect_remote_oid]
        if draft is None:
            # The rewrite requires a regular file at RELEASE_DRAFT_PATH; cases
            # that hand-write the groups file without a drafted section get a
            # placeholder draft (never parsed by the rewrite itself).
            if self.section_path.exists():
                draft = self.section_path
            else:
                draft = self.base / "recovery-draft.txt"
                if not draft.exists():
                    draft.write_text("release-groups:\n", encoding="utf-8")
        env_extra = {"RELEASE_DRAFT_PATH": str(draft)}
        if extra_env:
            env_extra.update(extra_env)
        return subprocess.run(
            args,
            cwd=str(self.clone), env=self._run_env(lock_exports=exports, env_extra=env_extra),
            capture_output=True, text=True,
        )

    def _acquire_lock_exports(self) -> dict:
        """A direct lock-stub acquisition for recovery runs that hand-write
        the groups file (the recovery tiling is not the authoring tiling)."""
        proc = subprocess.run(
            ["bash", str(self.lock_stub), "acquire", "--label", "recovery"],
            cwd=str(self.clone), env=self._run_env(),
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        exports = {}
        for line in proc.stdout.splitlines():
            if line.startswith("export DONE_LOCK_DIR="):
                exports["DONE_LOCK_DIR"] = _unquote(line.split("=", 1)[1])
            elif line.startswith("export DONE_LOCK_TOKEN="):
                exports["DONE_LOCK_TOKEN"] = _unquote(line.split("=", 1)[1])
        self.assertTrue(exports.get("DONE_LOCK_DIR") and exports.get("DONE_LOCK_TOKEN"))
        return exports

    def _hand_groups(self, base_tip: str, counts, msgs) -> Path:
        groups = self.base / "recovery-groups.txt"
        lines = ["base %s" % base_tip]
        for count, msg in zip(counts, msgs):
            lines.append("group %d" % count)
            lines.append("msg %s" % msg)
        groups.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return groups

    def _recovery_fixture(self):
        """Merge fixture plus a direct lock acquisition: main carries the
        merge above the six source commits; main~5 (the fixture has no notes commit)
        is the pre-merge first-parent commit usable as the selected base."""
        self._build_fixture("merge")
        self._install_scanner("noop")
        return self._acquire_lock_exports()

    # Recovery-mode witnesses (plan 2026-10-18-release-merge-history-recovery,
    # Task 1): the selected base is main~4 (source commit three; the
    # fixture carries no notes commit, and the merge is main~1), the first-parent segment base..main
    # carries four commits (four, five, six, the merge), and the counts
    # tile it as [2, 2].

    RECOVERY_COUNTS = [2, 2]
    RECOVERY_MSGS = ["recovered feature tail", "merge and notes work"]

    def test_recovery_rewrite_happy_path(self):
        exports = self._recovery_fixture()
        origin_tip = self._rev_parse("origin/main")
        base = self._rev_parse("main~4")
        main_tip = self._rev_parse("main")
        groups = self._hand_groups(main_tip, self.RECOVERY_COUNTS, self.RECOVERY_MSGS)
        rewrite = self._rewrite_step(
            groups, exports, recovery_base=base, expect_remote_oid=origin_tip,
        )
        combined = rewrite.stdout + rewrite.stderr
        self.assertEqual(rewrite.returncode, 0, "recovery rewrite must pass:\n%s" % combined)
        rebuilt = self._rev_parse("main")
        self.assertNotEqual(rebuilt, main_tip, "main must sit at the rebuilt tip")
        # The rebuilt subjects equal the groups-file msg lines in order, over
        # the first-parent segment only (the merged side branch stays below
        # the selected base's reach through the first-parent walk).
        subjects = self._gitx(
            "log", "--reverse", "--first-parent", "--format=%s",
            "%s..main" % base,
        ).stdout.splitlines()
        self.assertEqual(subjects, self.RECOVERY_MSGS)
        # Tree and backup witness: the rebuilt tip is byte-identical to the
        # original main tip; the backup ref holds the merge-containing state.
        backup_refs = self._backup_refs()
        self.assertEqual(len(backup_refs), 1, "exactly one backup ref")
        backup_ref = sorted(backup_refs)[0]
        self.assertEqual(backup_refs[backup_ref], main_tip)
        self._assert_tree_identical_to(backup_ref)
        # Publish witness: the remote is untouched until the push script runs.
        self.assertEqual(self._rev_parse("origin/main"), origin_tip)
        push_script = self._find_push_script()
        executed = self._execute_push_script(push_script)
        self.assertEqual(
            executed.returncode, 0,
            "recovery push script must publish:\n%s\n%s" % (executed.stdout, executed.stderr),
        )
        self.assertEqual(self._rev_parse("origin/main"), rebuilt)

    def test_recovery_diverged_delta_admitted(self):
        exports = self._recovery_fixture()
        base = self._rev_parse("main~4")
        main_tip = self._rev_parse("main")
        self._advance_origin()
        self._gitx("fetch", "-q", "origin")
        expect_oid = self._rev_parse("origin/main")
        groups = self._hand_groups(main_tip, self.RECOVERY_COUNTS, self.RECOVERY_MSGS)
        rewrite = self._rewrite_step(
            groups, exports, recovery_base=base, expect_remote_oid=expect_oid,
        )
        combined = rewrite.stdout + rewrite.stderr
        self.assertEqual(
            rewrite.returncode, 0,
            "recovery must admit a diverged delta:\n%s" % combined,
        )
        self.assertNotIn("not a descendant", combined, "the ordinary divergence refusal must not fire")
        push_script = self._find_push_script()
        executed = self._execute_push_script(push_script)
        self.assertEqual(executed.returncode, 0, executed.stdout + executed.stderr)
        self.assertEqual(self._rev_parse("origin/main"), self._rev_parse("main"))

    def test_recovery_usage_refusals(self):
        exports = self._recovery_fixture()
        main_tip = self._rev_parse("main")
        groups = self._hand_groups(main_tip, self.RECOVERY_COUNTS, self.RECOVERY_MSGS)
        # Unpaired: only --recovery-base.
        unpaired = subprocess.run(
            ["bash", str(REWRITE_SCRIPT), str(groups),
             "--recovery-base", self._rev_parse("main~4")],
            cwd=str(self.clone), env=self._run_env(lock_exports=exports),
            capture_output=True, text=True,
        )
        combined = unpaired.stdout + unpaired.stderr
        self.assertNotEqual(unpaired.returncode, 0)
        self.assertIn("FATAL", combined, "a usage refusal is a FATAL:\n%s" % combined)
        self.assertIn("--expect-remote-oid", combined, "usage refusal names the paired flag")
        # Unknown flag.
        unknown = subprocess.run(
            ["bash", str(REWRITE_SCRIPT), str(groups),
             "--recovery-base", self._rev_parse("main~4"),
             "--expect-remote-oid", "x", "--unknown-flag"],
            cwd=str(self.clone), env=self._run_env(lock_exports=exports),
            capture_output=True, text=True,
        )
        self.assertNotEqual(unknown.returncode, 0)
        self.assertIn("FATAL", unknown.stdout + unknown.stderr)
        self.assertEqual(self._rev_parse("main"), main_tip, "main unchanged on usage refusal")
        self.assertEqual(self._backup_refs(), {}, "no backup ref on usage refusal")

    def test_recovery_base_refusals(self):
        exports = self._recovery_fixture()
        main_tip = self._rev_parse("main")
        origin_tip = self._rev_parse("origin/main")
        groups = self._hand_groups(main_tip, self.RECOVERY_COUNTS, self.RECOVERY_MSGS)
        absent = "0000000000000000000000000000000000000009"
        off_line = self._rev_parse("main^2")  # the merged side commit: ancestor, off the first-parent line
        cases = [
            ("does not resolve", absent),
            ("first-parent", off_line),
            ("equals the current main tip", main_tip),
        ]
        for label, bad_base in cases:
            rewrite = self._rewrite_step(
                groups, exports, recovery_base=bad_base, expect_remote_oid=origin_tip,
            )
            combined = rewrite.stdout + rewrite.stderr
            self.assertNotEqual(rewrite.returncode, 0, "%s base must be refused:\n%s" % (label, combined))
            self.assertIn("RECOVERY REFUSED:", combined, "the sentinel names the reason: %s" % combined)
            self.assertIn(label, combined)
            self.assertEqual(self._rev_parse("main"), main_tip, "main unchanged")
            self.assertEqual(self._backup_refs(), {}, "no backup ref on a base refusal")

    def test_recovery_delta_refusal_names_ordinary_flow(self):
        # A recovery invocation whose delta carries no merge and no divergence
        # is refused naming the ordinary flow.
        self._build_fixture()
        self._install_scanner("noop")
        exports = self._acquire_lock_exports()
        main_tip = self._rev_parse("main")
        origin_tip = self._rev_parse("origin/main")
        groups = self._hand_groups(main_tip, [2, 2, 3], DEFAULT_MSGS)
        rewrite = self._rewrite_step(
            groups, exports, recovery_base=self._rev_parse("main~3"),
            expect_remote_oid=origin_tip,
        )
        combined = rewrite.stdout + rewrite.stderr
        self.assertNotEqual(rewrite.returncode, 0)
        self.assertIn("RECOVERY REFUSED:", combined)
        self.assertIn("ordinary", combined, "the refusal names the ordinary flow")
        self.assertEqual(self._backup_refs(), {})

    def test_recovery_remote_oid_mismatch_refused_before_backup(self):
        # An expected remote OID differing from the fetched remote tip is
        # refused before the backup ref.
        self._build_fixture("merge")
        self._install_scanner("noop")
        exports = self._acquire_lock_exports()
        main_tip = self._rev_parse("main")
        groups = self._hand_groups(main_tip, self.RECOVERY_COUNTS, self.RECOVERY_MSGS)
        rewrite = self._rewrite_step(
            groups, exports, recovery_base=self._rev_parse("main~4"),
            expect_remote_oid="0000000000000000000000000000000000000001",
        )
        combined = rewrite.stdout + rewrite.stderr
        self.assertNotEqual(rewrite.returncode, 0)
        self.assertIn("RECOVERY REFUSED:", combined)
        self.assertEqual(self._backup_refs(), {}, "refusal precedes the backup ref")

    def test_recovery_push_remote_rail(self):
        exports = self._recovery_fixture()
        origin_tip = self._rev_parse("origin/main")
        base = self._rev_parse("main~4")
        main_tip = self._rev_parse("main")
        groups = self._hand_groups(main_tip, self.RECOVERY_COUNTS, self.RECOVERY_MSGS)
        rewrite = self._rewrite_step(
            groups, exports, recovery_base=base, expect_remote_oid=origin_tip,
        )
        self.assertEqual(rewrite.returncode, 0, rewrite.stdout + rewrite.stderr)
        push_script = self._find_push_script()
        # The remote moves after the swap: the expected OID no longer holds.
        self._advance_origin()
        self._gitx("fetch", "-q", "origin")
        moved_tip = self._rev_parse("origin/main")
        executed = self._execute_push_script(push_script)
        combined = executed.stdout + executed.stderr
        self.assertNotEqual(executed.returncode, 0, "a moved remote must abort:\n%s" % combined)
        self.assertIn("re-observ", combined, "the abort names re-observation and re-authorization")
        self.assertIn("Restore path", combined, "the abort carries the recovery restore path")
        self.assertEqual(self._rev_parse("origin/main"), moved_tip, "nothing published")
        self.assertFalse(push_script.exists(), "the push script removes itself on abort")

    def test_recovery_push_correction_rail(self):
        exports = self._recovery_fixture()
        origin_tip = self._rev_parse("origin/main")
        base = self._rev_parse("main~4")
        main_tip = self._rev_parse("main")
        groups = self._hand_groups(main_tip, self.RECOVERY_COUNTS, self.RECOVERY_MSGS)
        rewrite = self._rewrite_step(
            groups, exports, recovery_base=base, expect_remote_oid=origin_tip,
        )
        self.assertEqual(rewrite.returncode, 0, rewrite.stdout + rewrite.stderr)
        push_script = self._find_push_script()
        # The witnessed CHANGELOG correction shape: a tracked-file correction
        # committed after the swap, before the push script executes.
        (self.clone / "CHANGELOG.md").write_text(
            self._today_section("post-swap correction marker"), encoding="utf-8"
        )
        self._gitx("add", "--", "CHANGELOG.md")
        self._gitx("commit", "-q", "-m", "chore: post-swap correction")
        executed = self._execute_push_script(push_script)
        combined = executed.stdout + executed.stderr
        self.assertNotEqual(executed.returncode, 0, "a correction after the swap must abort:\n%s" % combined)
        self.assertIn("no longer equals the rewritten tip", combined, "the first failing re-assertion is tip equality")
        self.assertIn("re-run", combined, "the abort names the re-run remedy")
        self.assertEqual(self._rev_parse("origin/main"), origin_tip, "nothing published")
        self.assertFalse(push_script.exists(), "the push script removes itself on abort")

    def test_recovery_push_script_shape(self):
        exports = self._recovery_fixture()
        origin_tip = self._rev_parse("origin/main")
        base = self._rev_parse("main~4")
        main_tip = self._rev_parse("main")
        groups = self._hand_groups(main_tip, self.RECOVERY_COUNTS, self.RECOVERY_MSGS)
        rewrite = self._rewrite_step(
            groups, exports, recovery_base=base, expect_remote_oid=origin_tip,
        )
        self.assertEqual(rewrite.returncode, 0, rewrite.stdout + rewrite.stderr)
        push_script = self._find_push_script()
        text = push_script.read_text(encoding="utf-8")
        lease_lines = [line for line in text.splitlines() if "--force-with-lease=refs/heads/main:" in line]
        self.assertEqual(len(lease_lines), 1, "exactly one lease-bound push line:\n%s" % text)
        self.assertIn(origin_tip, lease_lines[0], "the lease binds the expected remote OID")
        self.assertIn("FINAL_TREE", text, "the script carries the final-tree re-verification")
        self.assertIn("scan-public-hygiene", text, "the script carries the privacy re-scan invocation")

    def _run_release(self, variant: str = "clean", scanner: str = "noop",
                     counts=None, msgs=None, marker: str = "selftest section marker",
                     rewrite_shim: str = "pass", draft=None, extra_env: dict = None):
        """Authoring plus rewrite plus the lock release, returning the rewrite
        result, the exports, the groups file path, and the pre-rewrite tip."""
        self._build_fixture(variant)
        self._install_scanner(scanner)
        self._draft_section(counts or DEFAULT_COUNTS, msgs or DEFAULT_MSGS, marker)
        authoring = self._authoring_step()
        exports, groups_path = self._require_authoring_contract(authoring)
        pre_tip = self._rev_parse("main")
        rewrite = self._rewrite_step(groups_path, exports, shim=rewrite_shim,
                                     draft=draft, extra_env=extra_env)
        self._release_lock(exports)
        self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        return rewrite, exports, groups_path, pre_tip

    def _release_lock(self, exports) -> None:
        if not exports.get("DONE_LOCK_DIR"):
            return
        subprocess.run(
            ["bash", str(self.lock_stub), "release-repo"],
            cwd=str(self.clone), env=self._run_env(lock_exports=exports),
            capture_output=True, text=True,
        )

    def _release_last_acquisition(self) -> dict:
        """Release whatever the aborting authoring script acquired (per the
        contract the calling shell releases on every abort path)."""
        exports = self._last_acquire_exports()
        if exports:
            self._release_lock(exports)
            self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        return exports

    def _last_acquire_exports(self):
        if not self.lock_log.exists():
            return None
        for line in reversed(self.lock_log.read_text().splitlines()):
            if line.startswith("ACQUIRE"):
                fields = dict(part.split("=", 1) for part in line.split()[1:] if "=" in part)
                if fields.get("token") and fields.get("dir"):
                    return {"DONE_LOCK_DIR": fields["dir"], "DONE_LOCK_TOKEN": fields["token"]}
        return None

    def _assert_release_logged(self, token: str) -> None:
        log = self.lock_log.read_text()
        self.assertTrue(
            any(line.startswith("RELEASE") and token in line for line in log.splitlines()),
            "lock log lacks a RELEASE invocation carrying the acquired token:\n%s" % log,
        )

    def _assert_lock_was_acquired(self) -> None:
        log = self.lock_log.read_text()
        self.assertTrue(
            any(line.startswith("ACQUIRE") for line in log.splitlines()),
            "authoring never reached lock acquisition (contract: the lock is "
            "acquired before the abort checks):\n%s" % log,
        )

    def _find_push_script(self) -> Path:
        found = sorted(self.tmpdir.glob("release-push-*"))
        self.assertEqual(len(found), 1, "expected one persisted push script under the pinned TMPDIR, got %s" % found)
        return found[0]

    def _execute_push_script(self, path: Path):
        return subprocess.run(
            ["bash", str(path)],
            cwd=str(self.clone), env=self._run_env(), capture_output=True, text=True,
        )

    # ------------------------------------------------------------------
    # Assertion helpers
    # ------------------------------------------------------------------

    def _rev_parse(self, ref: str) -> str:
        return self._gitx("rev-parse", ref).stdout.strip()

    def _rev_list_count(self, rng: str) -> int:
        return int(self._gitx("rev-list", "--count", rng).stdout.strip())

    def _subjects(self, rng: str):
        return self._gitx("log", "--reverse", "--format=%s", rng).stdout.splitlines()

    def _rewritten_authors(self, rng: str):
        out = self._gitx("log", "--reverse", "--format=%an%x1f%aI", rng).stdout
        return [tuple(line.split("\x1f")) for line in out.splitlines() if line.strip()]

    def _backup_refs(self) -> dict:
        out = self._gitx("for-each-ref", "--format=%(refname) %(objectname)", "refs/release-backup/").stdout
        return {
            parts[0]: parts[1]
            for parts in (line.split() for line in out.splitlines() if line.strip())
        }

    def _worktree_count(self) -> int:
        out = self._gitx("worktree", "list", "--porcelain").stdout
        return sum(1 for line in out.splitlines() if line.startswith("worktree "))

    def _branches(self) -> set:
        return set(self._gitx("for-each-ref", "--format=%(refname:short)", "refs/heads/").stdout.split())

    def _porcelain(self) -> str:
        return self._gitx("status", "--porcelain").stdout

    def _head_files(self):
        out = self._gitx("show", "--name-only", "--format=", "HEAD").stdout
        return [line for line in out.splitlines() if line.strip()]

    def _assert_tree_identical_to(self, ref: str) -> None:
        diff = self._gitx("diff", "main", ref, check=False)
        self.assertEqual(
            diff.returncode, 0,
            "diff against %s must resolve (rc=0); an unresolvable ref must fail "
            "the case, not read as an empty diff: %s" % (ref, diff.stderr),
        )
        self.assertEqual(diff.stdout, "", "main tree must be byte-identical to %s" % ref)

    def _assert_torn_down(self) -> None:
        self.assertEqual(self._worktree_count(), 1, "the rewrite worktree must be removed")
        self.assertEqual(self._branches(), {"main"}, "the temp branch must be removed")

    def _assert_abort_shape(self, proc, pre_tip: str, token_absent: str = None, path_expected: str = None):
        combined = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0, "run must abort; output:\n%s" % combined)
        self.assertEqual(self._rev_parse("main"), pre_tip, "main must be unchanged (abort before the swap)")
        if path_expected is not None:
            self.assertIn(path_expected, combined, "abort output must carry the offending PATH")
        if token_absent is not None:
            self.assertNotIn(token_absent, combined, "the deny token itself must never reach the output")

    def _assert_backup_ref_recovery(self, combined: str, backup_ref: str) -> None:
        """Push-abort recovery pin: the output must name the backup ref AND
        carry the restore path (the word restore or reset) TOGETHER, on the
        same line, so neither half of the recovery message can drift away."""
        self.assertIn(backup_ref, combined, "the abort message must name the backup ref:\n%s" % combined)
        named_lines = [line for line in combined.splitlines() if backup_ref in line]
        self.assertTrue(
            any(("restore" in line.lower() or "reset" in line.lower()) for line in named_lines),
            "the recovery steps must pair the backup ref name with restore/reset:\n%s" % combined,
        )

    # ------------------------------------------------------------------
    # Task 2 witnesses (plan 2026-10-26-release-privacy-gate-diagnostics-
    # and-replay): pattern copies, draft lifecycle, diagnostic replay
    # ------------------------------------------------------------------

    def _sha256_of(self, path) -> str:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    def _scanner_log_blocks(self) -> list:
        """Split the scanner witness log into per-invocation blocks; each
        invocation opens with a RELEASE_REMOTE= line."""
        text = self.scanner_log.read_text(encoding="utf-8")
        blocks = []
        current = None
        for line in text.splitlines(keepends=True):
            if line.startswith("RELEASE_REMOTE="):
                current = []
                blocks.append(current)
            if current is not None:
                current.append(line)
        return ["".join(block) for block in blocks]

    def _log_payload(self, block: str, name: str) -> str:
        """Bytes between a ``NAME>`` marker and its ``END-NAME`` sentinel in
        one witness-log block."""
        marker = name + ">\n"
        start = block.index(marker) + len(marker)
        end = block.index("END-%s\n" % name, start)
        return block[start:end]

    def _replay_command(self, combined: str) -> str:
        lines = [
            line.strip() for line in combined.splitlines()
            if line.strip().startswith("bash ") and "release-diagnostic-replay.sh" in line
        ]
        self.assertEqual(
            len(lines), 1,
            "exactly one shell-safe replay command line expected:\n%s" % combined,
        )
        return lines[0]

    def _run_replay(self, command: str):
        return subprocess.run(
            ["bash", "-c", command],
            cwd=str(self.clone), env=self._run_env(), capture_output=True, text=True,
        )

    # ------------------------------------------------------------------
    # Rewrite cases
    # ------------------------------------------------------------------

    def test_squash_contiguous_groups(self):
        # The passing clean-content case runs the REAL scanner end to end.
        rewrite, _, _, _ = self._run_release(scanner="real")
        self.assertEqual(
            rewrite.returncode, 0,
            "rewrite failed rc=%s\nstdout:\n%s\nstderr:\n%s" % (rewrite.returncode, rewrite.stdout, rewrite.stderr),
        )
        self.assertEqual(self._rev_list_count("origin/main..main"), 3)
        self.assertEqual(self._subjects("origin/main..main"), DEFAULT_MSGS)
        self.assertEqual(self._rewritten_authors("origin/main..main"), DEFAULT_EXPECTED_AUTHORS)
        refs = self._backup_refs()
        self.assertEqual(len(refs), 1, "exactly one backup ref expected, got %s" % refs)
        self._assert_tree_identical_to(next(iter(refs)))

    def test_uncommitted_changes_survive(self):
        self._build_fixture()
        self._install_scanner("noop")
        manual = self.clone / "docs" / "manual.md"
        dirty_bytes = manual.read_bytes() + b"uncommitted local edit\n"
        manual.write_bytes(dirty_bytes)
        scratch = self.clone / "untracked-note.txt"
        scratch.write_text("untracked scratch\n", encoding="utf-8")
        snapshot = self._porcelain()
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "survival marker")
        authoring = self._authoring_step()
        exports, groups_path = self._require_authoring_contract(authoring)
        rewrite = self._rewrite_step(groups_path, exports)
        self._release_lock(exports)
        self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        self.assertEqual(
            rewrite.returncode, 0,
            "rewrite failed rc=%s\nstdout:\n%s\nstderr:\n%s" % (rewrite.returncode, rewrite.stdout, rewrite.stderr),
        )
        # The squashed count holds BEFORE the survival assertions.
        self.assertEqual(self._rev_list_count("origin/main..main"), 3)
        self.assertEqual(manual.read_bytes(), dirty_bytes, "modified tracked file must survive byte-identical")
        self.assertEqual(scratch.read_text(), "untracked scratch\n", "untracked file must survive")
        self.assertEqual(self._porcelain(), snapshot, "post-swap status must equal the pre-run snapshot")

    def test_base_tip_mismatch_aborts(self):
        self._build_fixture()
        self._install_scanner("noop")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "base mismatch marker")
        authoring = self._authoring_step()
        exports, groups_path = self._require_authoring_contract(authoring)
        pre_tip = self._rev_parse("main")
        parent = self._rev_parse("main~1")
        lines = Path(groups_path).read_text(encoding="utf-8").splitlines(keepends=True)
        self.assertTrue(lines[0].startswith("base "), "groups file must open with a base line")
        lines[0] = "base %s\n" % parent
        Path(groups_path).write_text("".join(lines), encoding="utf-8")
        rewrite = self._rewrite_step(groups_path, exports)
        self._release_lock(exports)
        self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        self._assert_abort_shape(rewrite, pre_tip)
        self.assertIn("REGROUP REQUIRED", rewrite.stderr, "base mismatch must demand a regroup on stderr")

    def test_not_descendant_of_origin_aborts(self):
        self._build_fixture()
        self._install_scanner("noop")
        self._advance_origin()
        self._gitx("fetch", "-q", "origin")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "divergence marker")
        authoring = self._authoring_step()
        exports, groups_path = self._require_authoring_contract(authoring)
        pre_tip = self._rev_parse("main")
        rewrite = self._rewrite_step(groups_path, exports)
        self._release_lock(exports)
        self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        self._assert_abort_shape(rewrite, pre_tip)
        self.assertNotEqual(self._rev_parse("origin/main"), pre_tip, "origin must have advanced past the local range")

    def test_coverage_gap_aborts(self):
        self._build_fixture()
        self._install_scanner("noop")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "coverage marker")
        authoring = self._authoring_step()
        exports, groups_path = self._require_authoring_contract(authoring)
        pre_tip = self._rev_parse("main")
        lines = Path(groups_path).read_text(encoding="utf-8").splitlines(keepends=True)
        group_slots = [i for i, line in enumerate(lines) if line.startswith("group ")]
        self.assertTrue(group_slots, "groups file must carry group lines")
        last = lines[group_slots[-1]]
        count = int(last.split()[1])
        lines[group_slots[-1]] = "group %d\n" % (count - 1)
        Path(groups_path).write_text("".join(lines), encoding="utf-8")
        rewrite = self._rewrite_step(groups_path, exports)
        self._release_lock(exports)
        self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        self._assert_abort_shape(rewrite, pre_tip)

    def test_merge_commit_in_range_aborts(self):
        self._build_fixture("merge")
        self._install_scanner("noop")
        merge_tip = self._rev_parse("main")
        self._draft_section(
            [2, 2, 2, 3],
            [MSG_G1, MSG_G2, MSG_G3, "side and merge work"],
            "merge marker",
        )
        authoring = self._authoring_step()
        exports, groups_path = self._require_authoring_contract(authoring)
        pre_tip = self._rev_parse("main")
        rewrite = self._rewrite_step(groups_path, exports)
        self._release_lock(exports)
        self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        combined = rewrite.stdout + rewrite.stderr
        self.assertNotEqual(rewrite.returncode, 0, "merge in range must abort:\n%s" % combined)
        self.assertIn(merge_tip, combined, "the offending merge commit must be named")
        self.assertEqual(self._rev_parse("main"), pre_tip, "main must be unchanged")

    def test_lock_stolen_between_scripts_aborts(self):
        self._build_fixture()
        self._install_scanner("noop")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "stolen lock marker")
        authoring = self._authoring_step()
        exports, groups_path = self._require_authoring_contract(authoring)
        lock_dir = Path(exports["DONE_LOCK_DIR"])
        self.assertTrue(lock_dir.exists(), "the acquired lock dir must exist")
        shutil.rmtree(lock_dir)  # flip the stub lock to not-held
        pre_tip = self._rev_parse("main")
        rewrite = self._rewrite_step(groups_path, exports)
        self._release_lock(exports)
        self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        self._assert_abort_shape(rewrite, pre_tip)
        self.assertEqual(self._backup_refs(), {}, "no backup ref may be created without a held lock")

    def test_lock_not_held_aborts(self):
        self._build_fixture()
        self._install_scanner("noop")
        tip = self._rev_parse("main")
        groups_file = self.base / "manual-groups"
        groups_file.write_text(
            "base %s\ngroup 2\nmsg %s\ngroup 2\nmsg %s\ngroup 2\nmsg %s\n"
            % (tip, MSG_G1, MSG_G2, MSG_G3),
            encoding="utf-8",
        )
        rewrite = self._rewrite_step(groups_file, exports={})
        self._assert_abort_shape(rewrite, tip)
        self.assertEqual(self._backup_refs(), {}, "no backup ref may be created without a held lock")

    def test_not_on_main_aborts(self):
        self._build_fixture()
        self._install_scanner("noop")
        self._gitx("checkout", "-q", "-b", "feature-side")
        main_tip = self._rev_parse("main")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "side branch marker")
        authoring = self._authoring_step()
        self._release_last_acquisition()
        self.assertNotEqual(
            authoring.returncode, 0,
            "authoring must refuse a non-main checkout:\n%s\n%s" % (authoring.stdout, authoring.stderr),
        )
        self.assertEqual(self._backup_refs(), {}, "no backup ref may exist")
        self.assertEqual(self._rev_parse("main"), main_tip, "main must be unchanged")
        self.assertEqual(self._gitx("branch", "--show-current").stdout.strip(), "feature-side")
        self._assert_lock_was_acquired()

    def test_privacy_hit_outside_strict_scope_aborts(self):
        rewrite, _, _, pre_tip = self._run_release(variant="outside_scope", scanner="real")
        self._assert_abort_shape(rewrite, pre_tip, token_absent=DENY_TOKEN, path_expected="scripts/tool.sh")

    def test_added_then_deleted_secret_proceeds(self):
        # Result-only scanning (operator directive 2026-09-27): a secret added
        # and later deleted inside the pile never reaches the published result,
        # so the release proceeds and the final tree carries no deny token.
        rewrite, _, _, pre_tip = self._run_release(variant="added_deleted", scanner="real")
        self.assertEqual(
            rewrite.returncode, 0,
            "release must proceed when the dirt never reaches the result "
            "(rc=%s)\nstdout:\n%s\nstderr:\n%s" % (rewrite.returncode, rewrite.stdout, rewrite.stderr),
        )
        self.assertEqual(
            self._gitx("grep", "-F", DENY_TOKEN, "main", check=False).stdout, "",
            "the published result must carry no deny token",
        )
        self._assert_tree_identical_to(pre_tip)

    def test_rename_with_scrub_old_blob_proceeds(self):
        # The dirty pre-rename blob stays inside pile history but never
        # reaches the published result; only the scrubbed renamed file does.
        rewrite, _, _, pre_tip = self._run_release(variant="rename_scrub", scanner="real")
        self.assertEqual(
            rewrite.returncode, 0,
            "release must proceed when the scrubbed rename keeps the token out "
            "of the result (rc=%s)\nstdout:\n%s\nstderr:\n%s"
            % (rewrite.returncode, rewrite.stdout, rewrite.stderr),
        )
        self.assertEqual(
            self._gitx("grep", "-F", DENY_TOKEN, "main", check=False).stdout, "",
            "the published result must carry no deny token",
        )
        self._assert_tree_identical_to(pre_tip)

    def test_typechange_blob_aborts(self):
        rewrite, _, _, pre_tip = self._run_release(variant="typechange", scanner="real")
        self._assert_abort_shape(rewrite, pre_tip, token_absent=DENY_TOKEN, path_expected="link/alias")

    def test_dirty_then_cleaned_same_path_proceeds(self):
        # Cleaned within the pile before the result is cut: the published
        # tree carries only the cleaned content, so the gate passes it.
        rewrite, _, _, pre_tip = self._run_release(variant="dirty_cleaned", scanner="real")
        self.assertEqual(
            rewrite.returncode, 0,
            "release must proceed when the in-pile clean keeps the token out "
            "of the result (rc=%s)\nstdout:\n%s\nstderr:\n%s"
            % (rewrite.returncode, rewrite.stdout, rewrite.stderr),
        )
        self.assertEqual(
            self._gitx("grep", "-F", DENY_TOKEN, "main", check=False).stdout, "",
            "the published result must carry no deny token",
        )
        self._assert_tree_identical_to(pre_tip)

    def test_deletion_only_group_proceeds(self):
        # A group whose net change deletes files still proceeds: the gate
        # scans the published result once, so per-group path sets no longer
        # exist and no per-group skip note is printed.
        rewrite, _, _, _ = self._run_release(
            counts=[2, 2, 1, 1, 1],
            msgs=[MSG_G1, MSG_G2, "docs rework", "cleanup", "release notes"],
            marker="deletion-only marker",
            scanner="real",
        )
        self.assertEqual(
            rewrite.returncode, 0,
            "a deletion-only group must proceed (rc=%s)\nstdout:\n%s\nstderr:\n%s"
            % (rewrite.returncode, rewrite.stdout, rewrite.stderr),
        )
        self.assertEqual(self._rev_list_count("origin/main..main"), 5)

    def test_excluded_shape_blob_reports_skip(self):
        rewrite, _, _, _ = self._run_release(variant="excluded_license", scanner="real")
        self.assertEqual(
            rewrite.returncode, 0,
            "an excluded-shape blob proceeds as the scanner exit dictates (rc=%s)\nstdout:\n%s\nstderr:\n%s"
            % (rewrite.returncode, rewrite.stdout, rewrite.stderr),
        )
        combined = rewrite.stdout + rewrite.stderr
        self.assertIn("skipped excluded path", combined, "the scanner skip note must be surfaced, never silent")

    def test_scanner_exit_two_aborts(self):
        rewrite, _, _, pre_tip = self._run_release(scanner="exit2")
        self._assert_abort_shape(rewrite, pre_tip)
        # Exit 2 of the rewrite script is exclusive to REGROUP REQUIRED; a
        # scanner environment failure must surface as exit 3.
        self.assertEqual(
            rewrite.returncode, 3,
            "a scanner environment failure must exit 3 (2 is REGROUP REQUIRED "
            "only), got rc=%s\nstderr:\n%s" % (rewrite.returncode, rewrite.stderr),
        )
        self._assert_torn_down()

    def test_privacy_hit_reports_locators_only(self):
        # The refusal message carries only safe path:line locators derived
        # from the scanner's FAIL rows: no matched content, no scanned-path
        # list.
        rewrite, _, _, pre_tip = self._run_release(variant="outside_scope", scanner="real")
        combined = rewrite.stdout + rewrite.stderr
        self._assert_abort_shape(rewrite, pre_tip, token_absent=DENY_TOKEN, path_expected="scripts/tool.sh:2")
        self.assertEqual(
            rewrite.returncode, 1,
            "a privacy hit must keep the scanner's exit 1, got rc=%s\nstderr:\n%s"
            % (rewrite.returncode, rewrite.stderr),
        )
        self.assertIn("PRIVACY GATE FAILED (scanner exit 1)", combined)
        self.assertIn("offending locators (path:line):", combined)
        # No full path list: clean scanned paths must stay out of the refusal.
        self.assertNotIn("feature-alpha/one.txt", combined, "clean scanned paths must not be listed")
        self.assertNotIn("docs/manual.md", combined, "clean scanned paths must not be listed")
        self.assertNotIn("release-groups.txt", combined, "clean scanned paths must not be listed")

    def test_scanner_exit_three_maps_to_rewrite_exit_three(self):
        rewrite, _, _, pre_tip = self._run_release(scanner="exit3")
        combined = rewrite.stdout + rewrite.stderr
        self._assert_abort_shape(rewrite, pre_tip)
        self.assertEqual(
            rewrite.returncode, 3,
            "a scanner tool error must exit 3, got rc=%s\nstderr:\n%s"
            % (rewrite.returncode, rewrite.stderr),
        )
        self.assertIn("PRIVACY GATE FAILED (scanner exit 3)", combined)
        self.assertNotIn("feature-alpha/one.txt", combined, "a tool error must not list scanned paths")
        self._assert_torn_down()

    def test_clean_scan_prints_no_failure_message(self):
        rewrite, _, _, _ = self._run_release(scanner="real")
        combined = rewrite.stdout + rewrite.stderr
        self.assertEqual(
            rewrite.returncode, 0,
            "rewrite failed rc=%s\nstdout:\n%s\nstderr:\n%s" % (rewrite.returncode, rewrite.stdout, rewrite.stderr),
        )
        self.assertNotIn("PRIVACY GATE FAILED", combined, "a passing gate must print no failure message")
        self.assertNotIn("offending locators", combined)

    def test_scanner_invocation_env_pinned(self):
        # The privacy gate must run the fixture scanner under the release
        # run's pinned settings: the pinned release remote, the
        # materialization root, the patterns copy, the immutable scanner
        # copy, and the explicit-paths argv including the groups file.
        self._build_fixture()
        self._install_scanner("envlog")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "env pin marker")
        authoring = self._authoring_step()
        exports, groups_path = self._require_authoring_contract(authoring)
        rewrite = self._rewrite_step(groups_path, exports)
        self._release_lock(exports)
        self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        self.assertEqual(
            rewrite.returncode, 0,
            "rewrite failed rc=%s\nstdout:\n%s\nstderr:\n%s" % (rewrite.returncode, rewrite.stdout, rewrite.stderr),
        )
        log = self.scanner_log.read_text(encoding="utf-8")

        def field(name: str) -> str:
            prefix = name + "="
            for line in log.splitlines():
                if line.startswith(prefix):
                    return line[len(prefix):]
            return ""

        self.assertEqual(log.count("RELEASE_REMOTE="), 1, "exactly one gate invocation:\n%s" % log)
        self.assertEqual(
            field("RELEASE_REMOTE"), "origin",
            "the scanner must run under the pinned release remote:\n%s" % log,
        )
        self.assertTrue(
            field("PUBLIC_HYGIENE_REPO_ROOT").startswith(str(self.tmpdir)),
            "the gate must set PUBLIC_HYGIENE_REPO_ROOT under the pinned TMPDIR:\n%s" % log,
        )
        patterns = field("PUBLIC_HYGIENE_PATTERNS_FILE")
        self.assertTrue(
            patterns.startswith(str(self.tmpdir)) and patterns.endswith("hygiene.patterns"),
            "the gate must scan with the run-dir patterns copy:\n%s" % log,
        )
        self.assertTrue(
            field("SELF").startswith(str(self.tmpdir)),
            "the scanner must run from the immutable run-dir copy, not the checkout:\n%s" % log,
        )
        argv_line = next((line for line in log.splitlines() if line.startswith("ARGV")), "")
        self.assertTrue(
            argv_line.startswith("ARGV --files ") and " release-groups.txt" in argv_line,
            "the scanner must be invoked in explicit-paths mode including the groups file:\n%s" % log,
        )

    def test_tree_materialization_failure_is_fatal(self):
        rewrite, _, _, pre_tip = self._run_release(scanner="lognoop", rewrite_shim="archive-fail")
        self._assert_abort_shape(rewrite, pre_tip)
        scanned = self.scanner_log.exists() and self.scanner_log.read_text().strip()
        self.assertFalse(scanned, "no materialized file may reach the scanner:\n%s" % (scanned or ""))
        self._assert_torn_down()

    def test_swap_cas_mismatch_aborts(self):
        self._build_fixture()
        self._install_scanner("noop")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "cas marker")
        authoring = self._authoring_step()
        exports, groups_path = self._require_authoring_contract(authoring)
        pre_tip = self._rev_parse("main")
        rewrite = self._rewrite_step(groups_path, exports, shim="cas-tamper")
        self._release_lock(exports)
        self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        self.assertNotEqual(rewrite.returncode, 0, "CAS mismatch must abort:\n%s" % (rewrite.stdout + rewrite.stderr))
        self.assertIn("REGROUP REQUIRED", rewrite.stderr, "a concurrent commit routes into the regroup loop")
        new_main = self._rev_parse("main")
        self.assertTrue(
            self.cas_record.exists() and new_main == self.cas_record.read_text().strip(),
            "main must still sit at the concurrent commit",
        )
        self.assertNotEqual(new_main, pre_tip)
        refs = self._backup_refs()
        self.assertEqual(len(refs), 1, "the backup ref must stay intact")
        self.assertEqual(list(refs.values())[0], pre_tip, "the backup ref stays at the pre-rewrite tip")
        self._assert_torn_down()

    def test_tree_identity_gate_aborts(self):
        rewrite, _, _, pre_tip = self._run_release(rewrite_shim="tree-tamper")
        combined = rewrite.stdout + rewrite.stderr
        self.assertNotEqual(rewrite.returncode, 0, "a diverging rewritten tree must abort:\n%s" % combined)
        self.assertEqual(self._rev_parse("main"), pre_tip, "main stays at the base tip")
        refs = self._backup_refs()
        self.assertEqual(len(refs), 1, "the backup ref must be present")
        self.assertEqual(list(refs.values())[0], pre_tip, "the backup ref sits at the pre-rewrite tip")
        self._assert_torn_down()

    def test_post_swap_snapshot_mismatch_aborts(self):
        rewrite, _, _, pre_tip = self._run_release()
        self.assertEqual(
            rewrite.returncode, 0,
            "rewrite failed rc=%s\nstdout:\n%s\nstderr:\n%s" % (rewrite.returncode, rewrite.stdout, rewrite.stderr),
        )
        push_script = self._find_push_script()
        rewritten_tip = self._rev_parse("main")
        self.assertNotEqual(rewritten_tip, pre_tip)
        base_tip = self._rev_parse("origin/main")
        readme = self.clone / "README.md"
        readme.write_bytes(readme.read_bytes() + b"post-swap local dirt\n")
        pushed = self._execute_push_script(push_script)
        combined = pushed.stdout + pushed.stderr
        self.assertNotEqual(pushed.returncode, 0, "post-swap dirt must abort the push:\n%s" % combined)
        refs = self._backup_refs()
        self.assertEqual(len(refs), 1, "the backup ref must be named")
        self._assert_backup_ref_recovery(combined, next(iter(refs)))
        self.assertEqual(self._rev_parse("origin/main"), base_tip, "nothing may be pushed")
        self.assertEqual(self._rev_parse("main"), rewritten_tip, "main stays at the rewritten tip")
        self.assertFalse(push_script.exists(), "the push script removes itself")

    def test_push_script_reassertion_aborts(self):
        rewrite, _, _, _ = self._run_release()
        self.assertEqual(
            rewrite.returncode, 0,
            "rewrite failed rc=%s\nstdout:\n%s\nstderr:\n%s" % (rewrite.returncode, rewrite.stdout, rewrite.stderr),
        )
        push_script = self._find_push_script()
        rewritten_tip = self._rev_parse("main")
        text = push_script.read_text(encoding="utf-8")
        self.assertRegex(
            text, re.escape(rewritten_tip) + r":(main|refs/heads/main)",
            "the push command must reference the recorded tip value, not the bare branch name",
        )
        self.assertNotIn("--force", text, "the push script must be free of force flags")
        self.assertIsNone(re.search(r"push\s+-f(\s|$)", text), "no short force flag")
        # The leading-plus refspec force forms are equally banned: '+<tip>:'
        # and 'push ... +<40-hex>:'.
        self.assertIsNone(
            re.search(r"\+\s*" + re.escape(rewritten_tip) + r":", text),
            "no leading-plus force refspec on the recorded tip:\n%s" % text,
        )
        self.assertIsNone(
            re.search(r"push\s+.*\s\+[0-9a-f]{40}:", text),
            "no leading-plus force refspec on any 40-hex tip:\n%s" % text,
        )
        base_tip = self._rev_parse("origin/main")
        self._gitx("commit", "-q", "--allow-empty", "-m", "local commit past the rewritten tip")
        moved_tip = self._rev_parse("main")
        pushed = self._execute_push_script(push_script)
        combined = pushed.stdout + pushed.stderr
        self.assertNotEqual(pushed.returncode, 0, "the re-assertion must abort:\n%s" % combined)
        refs = self._backup_refs()
        self.assertEqual(len(refs), 1, "the backup ref must be named")
        self._assert_backup_ref_recovery(combined, next(iter(refs)))
        self.assertEqual(self._rev_parse("origin/main"), base_tip, "the bare remote stays unchanged")
        self.assertEqual(self._rev_parse("main"), moved_tip, "main stays at the new commit")
        self.assertFalse(push_script.exists(), "the script is removed afterward")

    def test_push_script_remote_divergence_aborts(self):
        rewrite, _, _, _ = self._run_release()
        self.assertEqual(
            rewrite.returncode, 0,
            "rewrite failed rc=%s\nstdout:\n%s\nstderr:\n%s" % (rewrite.returncode, rewrite.stdout, rewrite.stderr),
        )
        push_script = self._find_push_script()
        rewritten_tip = self._rev_parse("main")
        self._advance_origin()
        self._gitx("fetch", "-q", "origin")
        divergent = self._rev_parse("origin/main")
        pushed = self._execute_push_script(push_script)
        combined = pushed.stdout + pushed.stderr
        self.assertNotEqual(pushed.returncode, 0, "remote divergence must abort before the push:\n%s" % combined)
        refs = self._backup_refs()
        self.assertEqual(len(refs), 1, "the backup ref must be named")
        self._assert_backup_ref_recovery(combined, next(iter(refs)))
        self.assertEqual(
            self._gitx("--git-dir", str(self.origin), "rev-parse", "main").stdout.strip(),
            divergent, "the bare remote stays unchanged at the divergent commit",
        )
        self.assertNotEqual(self._rev_parse("origin/main"), rewritten_tip, "nothing may be pushed")
        self.assertFalse(push_script.exists(), "the script removes itself")

    def test_push_is_plain_fast_forward(self):
        rewrite, _, _, _ = self._run_release()
        self.assertEqual(
            rewrite.returncode, 0,
            "rewrite failed rc=%s\nstdout:\n%s\nstderr:\n%s" % (rewrite.returncode, rewrite.stdout, rewrite.stderr),
        )
        push_script = self._find_push_script()
        mode = stat.S_IMODE(push_script.stat().st_mode)
        self.assertEqual(mode & 0o777, 0o700, "the persisted push script is created 0700")
        base_tip = self._rev_parse("origin/main")
        rewritten_tip = self._rev_parse("main")
        pushed = self._execute_push_script(push_script)
        self.assertEqual(
            pushed.returncode, 0,
            "the fast-forward push must succeed\nstdout:\n%s\nstderr:\n%s" % (pushed.stdout, pushed.stderr),
        )
        self.assertEqual(self._rev_parse("origin/main"), rewritten_tip, "origin/main must equal the verified value")
        rng = "%s..origin/main" % base_tip
        self.assertEqual(self._rev_list_count(rng), 3, "the pushed history is the squashed one")
        self.assertEqual(self._subjects(rng), DEFAULT_MSGS, "pushed subjects carry the groups-file msg lines")
        self.assertFalse(push_script.exists(), "the script removes itself after execution")

    # ------------------------------------------------------------------
    # Backup ref cases
    # ------------------------------------------------------------------

    def test_backup_ref_created(self):
        rewrite, _, _, pre_tip = self._run_release()
        self.assertEqual(
            rewrite.returncode, 0,
            "rewrite failed rc=%s\nstdout:\n%s\nstderr:\n%s" % (rewrite.returncode, rewrite.stdout, rewrite.stderr),
        )
        refs = self._backup_refs()
        self.assertEqual(len(refs), 1, "exactly one backup ref expected, got %s" % refs)
        name = next(iter(refs))
        self.assertRegex(name, r"^refs/release-backup/pre-release-\d{4}-\d{2}-\d{2}$")
        self.assertEqual(refs[name], pre_tip, "the backup ref sits at the pre-rewrite tip")
        self._assert_tree_identical_to(name)
        self._assert_torn_down()
        self.assertEqual(
            list(self.tmpdir.glob("release-hygiene-*")), [],
            "no materialization root may remain",
        )

    def test_backup_ref_collision_creates_suffix(self):
        self._build_fixture()
        self._install_scanner("noop")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "collision marker")
        authoring = self._authoring_step()
        exports, groups_path = self._require_authoring_contract(authoring)
        pre_tip = self._rev_parse("main")
        today = self._today()
        yesterday = self._yesterday()
        # Pre-create collision candidates for today AND yesterday at the
        # pre-rewrite tip.
        self._gitx("update-ref", "refs/release-backup/pre-release-%s" % today, pre_tip)
        self._gitx("update-ref", "refs/release-backup/pre-release-%s" % yesterday, pre_tip)
        rewrite = self._rewrite_step(groups_path, exports)
        self._release_lock(exports)
        self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        self.assertEqual(
            rewrite.returncode, 0,
            "the run must survive the same-day collision (rc=%s)\nstdout:\n%s\nstderr:\n%s"
            % (rewrite.returncode, rewrite.stdout, rewrite.stderr),
        )
        refs = self._backup_refs()
        self.assertEqual(refs.get("refs/release-backup/pre-release-%s" % today), pre_tip,
                         "today's pre-existing ref must stay unchanged")
        self.assertEqual(refs.get("refs/release-backup/pre-release-%s-2" % today), pre_tip,
                         "the collision must create the -2 suffixed ref at the pre-rewrite tip")
        self.assertEqual(refs.get("refs/release-backup/pre-release-%s" % yesterday), pre_tip,
                         "yesterday's candidate must stay unchanged")
        self._assert_tree_identical_to("refs/release-backup/pre-release-%s-2" % today)

    # ------------------------------------------------------------------
    # Task 2: effective-pattern copies, draft lifecycle, diagnostic replay
    # (plan 2026-10-26-release-privacy-gate-diagnostics-and-replay)
    # ------------------------------------------------------------------

    def test_patterns_default_copy_scanned(self):
        # With no PUBLIC_HYGIENE_PATTERNS_FILE override the gate still scans
        # an immutable run-dir copy of the EFFECTIVE default patterns file,
        # resolved from the pinned HOME (never the host's own default file).
        self._build_fixture()
        self._install_scanner("envlog")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "default patterns marker")
        authoring = self._authoring_step()
        exports, groups_path = self._require_authoring_contract(authoring)
        rewrite = self._rewrite_step(groups_path, exports, extra_env={
            "HOME": str(self.home),
            "PUBLIC_HYGIENE_PATTERNS_FILE": "",
        })
        self._release_lock(exports)
        self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        combined = rewrite.stdout + rewrite.stderr
        self.assertEqual(
            rewrite.returncode, 0,
            "rewrite failed rc=%s\nstdout:\n%s\nstderr:\n%s" % (rewrite.returncode, rewrite.stdout, rewrite.stderr),
        )
        self.assertIn(
            "privacy gate patterns: %s" % self.default_patterns, combined,
            "the default patterns resolution is printed alongside its scan copy",
        )
        blocks = self._scanner_log_blocks()
        self.assertEqual(len(blocks), 1, "exactly one gate invocation:\n%s" % self.scanner_log.read_text())
        patterns_env = ""
        for line in blocks[0].splitlines():
            if line.startswith("PUBLIC_HYGIENE_PATTERNS_FILE="):
                patterns_env = line[len("PUBLIC_HYGIENE_PATTERNS_FILE="):]
        self.assertTrue(
            patterns_env.startswith(str(self.tmpdir)) and patterns_env.endswith("hygiene.patterns"),
            "the gate must scan the run-dir patterns copy of the default file:\n%s" % blocks[0],
        )
        self.assertEqual(
            self._log_payload(blocks[0], "PATTERNS-BYTES"), PATTERNS_TEXT,
            "the scanned copy must carry the effective default patterns bytes",
        )

    def test_patterns_default_missing_maps_to_tool_error(self):
        # A missing effective default patterns file keeps the scanner's own
        # tool-error class: the copy-time refusal exits 3 (never a usage
        # exit 1), matching the scanner's missing-patterns exit mapping.
        self._build_fixture()
        self._install_scanner("noop")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "missing default marker")
        authoring = self._authoring_step()
        exports, groups_path = self._require_authoring_contract(authoring)
        pre_tip = self._rev_parse("main")
        rewrite = self._rewrite_step(groups_path, exports, extra_env={
            "HOME": str(self.empty_home),
            "PUBLIC_HYGIENE_PATTERNS_FILE": "",
        })
        self._release_lock(exports)
        self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        combined = rewrite.stdout + rewrite.stderr
        self.assertEqual(
            rewrite.returncode, 3,
            "a missing default patterns file must keep the tool-error exit 3, "
            "got rc=%s\n%s" % (rewrite.returncode, combined),
        )
        self.assertIn("PRIVACY GATE FAILED (scanner exit 3)", combined)
        self.assertIn(
            str(self.empty_home / ".ai-playbook" / "public-hygiene.patterns"), combined,
            "the refusal names the missing effective default path",
        )
        self.assertEqual(self._rev_parse("main"), pre_tip, "main must be unchanged")

    def test_patterns_override_missing_refused(self):
        # A set-but-missing override keeps the existing fail-closed FATAL.
        missing = self.base / "no-such.patterns"
        self._build_fixture()
        self._install_scanner("noop")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "missing override marker")
        authoring = self._authoring_step()
        exports, groups_path = self._require_authoring_contract(authoring)
        pre_tip = self._rev_parse("main")
        rewrite = self._rewrite_step(groups_path, exports, extra_env={
            "PUBLIC_HYGIENE_PATTERNS_FILE": str(missing),
        })
        self._release_lock(exports)
        self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        combined = rewrite.stdout + rewrite.stderr
        self.assertEqual(rewrite.returncode, 1, combined)
        self.assertIn("FATAL", combined)
        self.assertIn(str(missing), combined, "the refusal names the missing override")
        self.assertEqual(self._rev_parse("main"), pre_tip, "main must be unchanged")

    def test_draft_removed_after_successful_rewrite(self):
        # A regular release-draft.* file parked directly under the
        # canonicalized temp root is removed by the exit trap on success.
        draft = self.tmpdir / "release-draft.case"
        draft.write_text("release draft scratch\n", encoding="utf-8")
        rewrite, _, _, _ = self._run_release(draft=draft)
        self.assertEqual(
            rewrite.returncode, 0,
            "rewrite failed rc=%s\nstdout:\n%s\nstderr:\n%s" % (rewrite.returncode, rewrite.stdout, rewrite.stderr),
        )
        self.assertFalse(draft.exists(), "a successful rewrite removes the temp-root draft")

    def test_draft_outside_temp_root_survives_cleanup(self):
        # The removal guard only ever deletes a release-draft.* file DIRECTLY
        # under the canonicalized temp root: a regular-file draft parked
        # outside the temp root survives a successful rewrite.
        draft = self.base / "release-draft.outside"
        draft.write_text("keep me\n", encoding="utf-8")
        rewrite, _, _, _ = self._run_release(draft=draft)
        self.assertEqual(
            rewrite.returncode, 0,
            "rewrite failed rc=%s\n%s" % (rewrite.returncode, rewrite.stdout + rewrite.stderr),
        )
        self.assertTrue(draft.exists(), "a draft outside the temp root must survive the cleanup guard")

    def test_draft_nonmatching_name_survives_cleanup(self):
        # A regular-file draft under the temp root whose name does not match
        # release-draft.* survives a successful rewrite.
        draft = self.tmpdir / "scratch-draft.txt"
        draft.write_text("keep me\n", encoding="utf-8")
        rewrite, _, _, _ = self._run_release(draft=draft)
        self.assertEqual(
            rewrite.returncode, 0,
            "rewrite failed rc=%s\n%s" % (rewrite.returncode, rewrite.stdout + rewrite.stderr),
        )
        self.assertTrue(draft.exists(), "a nonmatching draft name must survive the cleanup guard")

    def test_draft_symlink_survives_cleanup(self):
        # A matching name under the temp root that is a symlink, not a regular
        # file, must survive together with its target.
        target = self.tmpdir / "draft-target.txt"
        target.write_text("target\n", encoding="utf-8")
        link = self.tmpdir / "release-draft.link"
        os.symlink(target, link)
        rewrite, _, _, _ = self._run_release(draft=link)
        self.assertEqual(
            rewrite.returncode, 0,
            "rewrite failed rc=%s\n%s" % (rewrite.returncode, rewrite.stdout + rewrite.stderr),
        )
        self.assertTrue(link.is_symlink(), "the symlink draft must survive the cleanup guard")
        self.assertTrue(target.exists(), "the symlink target must survive the cleanup guard")

    def test_draft_nested_in_release_draft_dir_survives_cleanup(self):
        # A regular file nested inside a release-draft.* directory under the
        # temp root is NOT directly under it: the case glob's slash-bearing
        # tail must not satisfy the removal guard, so the nested file and its
        # directory survive a successful rewrite.
        nested_dir = self.tmpdir / "release-draft.dir"
        nested_dir.mkdir()
        draft = nested_dir / "inner.txt"
        draft.write_text("keep me\n", encoding="utf-8")
        rewrite, _, _, _ = self._run_release(draft=draft)
        self.assertEqual(
            rewrite.returncode, 0,
            "rewrite failed rc=%s\n%s" % (rewrite.returncode, rewrite.stdout + rewrite.stderr),
        )
        self.assertTrue(
            draft.exists(),
            "a draft nested inside a release-draft.* directory must survive the cleanup guard",
        )
        self.assertTrue(
            nested_dir.exists(),
            "the release-draft.* directory itself must survive the cleanup guard",
        )

    def test_privacy_hit_retains_draft_and_prints_replay_diagnostics(self):
        # A privacy hit retains the draft, persists no raw output, and names
        # every replay input plus one shell-safe replay command.
        rewrite, _, _, pre_tip = self._run_release(variant="outside_scope", scanner="real")
        combined = rewrite.stdout + rewrite.stderr
        self._assert_abort_shape(rewrite, pre_tip, token_absent=DENY_TOKEN, path_expected="scripts/tool.sh:2")
        self.assertEqual(rewrite.returncode, 1, combined)
        self.assertTrue(self.section_path.exists(), "a failed rewrite retains the Release draft")
        self.assertIn("PRIVACY GATE DIAGNOSTICS", combined)
        self.assertIn("source tip: %s" % pre_tip, combined)
        self.assertIn(
            "retained release draft: %s" % self.section_path, combined,
            "the diagnostics name the retained draft path",
        )
        self.assertIn("scanner source sha256: %s" % self._sha256_of(REAL_SCANNER), combined)
        self.assertIn("effective patterns source: %s" % self.patterns, combined)
        self.assertIn("effective patterns source sha256: %s" % self._sha256_of(self.patterns), combined)
        expected_groups = "base %s\n" % pre_tip + "".join(
            "group %d\nmsg %s\n" % (count, msg) for count, msg in zip(DEFAULT_COUNTS, DEFAULT_MSGS)
        )
        self.assertIn(
            "serialized release-group input sha256: %s" % hashlib.sha256(expected_groups.encode()).hexdigest(),
            combined,
        )
        command = self._replay_command(combined)
        for flag in ("--source-tip", "--scanner", "--scanner-sha256", "--patterns",
                     "--patterns-sha256", "--groups-sha256", "--draft"):
            self.assertIn(flag, command)
        self.assertEqual(
            list(self.tmpdir.glob("release-replay-*")), [],
            "a privacy hit must persist no raw-output file",
        )

    def test_diagnostic_replay_reproduces_scan_and_refuses_drift(self):
        # The one-command replay reproduces the failed scan exactly: same
        # tracked blobs, byte-identical reconstructed groups file, raw stdout
        # in a 0600 file, transcript carrying only paths and the outcome. Any
        # drifted input refuses (exit 2) BEFORE scanning.
        self._build_fixture()
        self._install_scanner("hitlog")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "replay marker")
        authoring = self._authoring_step()
        exports, groups_path = self._require_authoring_contract(authoring)
        groups_bytes = Path(groups_path).read_bytes()
        pre_tip = self._rev_parse("main")
        rewrite = self._rewrite_step(groups_path, exports)
        self._release_lock(exports)
        self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        combined = rewrite.stdout + rewrite.stderr
        self.assertEqual(rewrite.returncode, 1, "the stub hit must fail the gate:\n%s" % combined)
        self.assertNotIn(DENY_TOKEN, combined, "the rewrite transcript must not carry matched content")
        self.assertEqual(self._rev_parse("main"), pre_tip, "main must be unchanged")
        self.assertTrue(self.section_path.exists(), "the failed run retains the draft")
        command = self._replay_command(combined)

        def assert_refused(label: str, proc, groups_absent: bool = True) -> None:
            out = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 2, "%s must refuse with exit 2:\n%s" % (label, out))
            self.assertIn("REPLAY REFUSED:", out, label)
            self.assertEqual(
                sorted(p.name for p in self.tmpdir.glob("release-replay-*")), raw_snapshot,
                "%s: the refusal must persist no new artifact" % label,
            )
            if groups_absent:
                self.assertFalse(
                    (self.clone / "release-groups.txt").exists(),
                    "%s: no reconstructed groups file may survive" % label,
                )

        # Valid replay: reproduces the hit with the verified sources.
        replay = self._run_replay(command)
        replay_out = replay.stdout + replay.stderr
        self.assertEqual(replay.returncode, 1, "the replay must reproduce the privacy hit:\n%s" % replay_out)
        self.assertNotIn(DENY_TOKEN, replay_out, "matched content must stay out of the replay transcript")
        out_prefix = "release-diagnostic-replay: raw scanner stdout: "
        out_lines = [ln for ln in replay.stdout.splitlines() if ln.startswith(out_prefix)]
        self.assertEqual(len(out_lines), 1, replay.stdout)
        raw_path = Path(out_lines[0][len(out_prefix):].rsplit(" (mode", 1)[0])
        raw_text = raw_path.read_text(encoding="utf-8")
        self.assertIn(DENY_TOKEN, raw_text, "the raw file carries the scanner's own output")
        self.assertIn("docs/manual.md:2", raw_text, "the raw output reproduces the failed scan")
        self.assertEqual(stat.S_IMODE(raw_path.stat().st_mode) & 0o777, 0o600, "raw stdout is 0600")
        err_prefix = "release-diagnostic-replay: scanner stderr copy: "
        err_lines = [ln for ln in replay.stdout.splitlines() if ln.startswith(err_prefix)]
        self.assertEqual(len(err_lines), 1, replay.stdout)
        err_path = Path(err_lines[0][len(err_prefix):].rsplit(" (mode", 1)[0])
        self.assertEqual(stat.S_IMODE(err_path.stat().st_mode) & 0o777, 0o600, "the stderr copy is 0600")
        self.assertIn("scanner outcome: fail (exit 1)", replay.stdout)
        self.assertFalse(
            (self.clone / "release-groups.txt").exists(),
            "the replay removes the reconstructed groups file after the scan",
        )
        # Group reconstruction witness: the replay-time invocation read a
        # groups file byte-identical to the one the failed scan consumed.
        clone_real = os.path.realpath(str(self.clone))
        replay_blocks = [
            block for block in self._scanner_log_blocks()
            if ("PUBLIC_HYGIENE_REPO_ROOT=%s\n" % clone_real) in block
        ]
        self.assertEqual(
            len(replay_blocks), 1,
            "exactly one replay-time invocation expected:\n%s" % self.scanner_log.read_text(),
        )
        self.assertEqual(
            self._log_payload(replay_blocks[0], "GROUPS-BYTES").encode(), groups_bytes,
            "the replay reconstructs the groups file byte-identically",
        )
        # The valid replay persists exactly its two raw-output files; every
        # later refusal must add none.
        raw_snapshot = sorted(p.name for p in self.tmpdir.glob("release-replay-*"))
        self.assertEqual(len(raw_snapshot), 2, "the valid replay persists exactly two raw files")
        # Drift refusals, each BEFORE any scan.
        # (a) HEAD moved off the recorded source tip.
        self._gitx("commit", "-q", "--allow-empty", "-m", "post-failure drift commit")
        assert_refused("moved tip", self._run_replay(command))
        self._gitx("reset", "-q", "--hard", pre_tip)
        # (b) dirty tracked worktree.
        readme = self.clone / "README.md"
        saved_readme = readme.read_bytes()
        readme.write_bytes(saved_readme + b"local dirt\n")
        assert_refused("dirty tree", self._run_replay(command))
        readme.write_bytes(saved_readme)
        # (c) corrupted scanner digest argument.
        scanner_digest = re.search(r"--scanner-sha256 ([0-9a-f]{64})", command).group(1)
        corrupted = command.replace(
            scanner_digest, ("0" if scanner_digest[0] != "0" else "1") + scanner_digest[1:], 1,
        )
        assert_refused("scanner digest argument", self._run_replay(corrupted))
        # (d) drifted scanner source (an untracked helper copy in the clone).
        scanner_copy = self.clone / "scripts" / "scan-public-hygiene.sh"
        saved_scanner = scanner_copy.read_bytes()
        scanner_copy.write_bytes(saved_scanner + b"# drifted\n")
        assert_refused("scanner source drift", self._run_replay(command))
        scanner_copy.write_bytes(saved_scanner)
        # (e) corrupted patterns digest argument.
        patterns_digest = re.search(r"--patterns-sha256 ([0-9a-f]{64})", command).group(1)
        corrupted = command.replace(
            patterns_digest, ("0" if patterns_digest[0] != "0" else "1") + patterns_digest[1:], 1,
        )
        assert_refused("patterns digest argument", self._run_replay(corrupted))
        # (f) drifted effective-pattern source.
        saved_patterns = self.patterns.read_bytes()
        self.patterns.write_bytes(saved_patterns + b"extra-deny-line\n")
        assert_refused("patterns source drift", self._run_replay(command))
        self.patterns.write_bytes(saved_patterns)
        # (g) drifted draft: the serialized group input no longer matches.
        draft_text = self.section_path.read_text(encoding="utf-8")
        self.section_path.write_text(
            draft_text.replace("msg %s" % MSG_G1, "msg edited drift subject"), encoding="utf-8",
        )
        assert_refused("draft drift", self._run_replay(command))
        self.section_path.write_text(draft_text, encoding="utf-8")
        # (h) occupied reconstruction path: the replay never overwrites.
        occupied = self.clone / "release-groups.txt"
        occupied.write_text("occupied\n", encoding="utf-8")
        assert_refused("occupied groups path", self._run_replay(command), groups_absent=False)
        self.assertEqual(
            occupied.read_text(encoding="utf-8"), "occupied\n",
            "the replay must never overwrite an occupied reconstruction path",
        )
        occupied.unlink()

    # ------------------------------------------------------------------
    # Authoring cases
    # ------------------------------------------------------------------

    def test_authoring_replace_inside_delta(self):
        self._build_fixture("changelog_delta")
        self._install_scanner("noop")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "replacement section marker")
        authoring = self._authoring_step()
        exports, _ = self._require_authoring_contract(authoring)
        self._release_lock(exports)
        self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        text = (self.clone / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertNotIn("delta section marker", text, "the delta section must be replaced in place")
        self.assertIn("replacement section marker", text)
        self.assertEqual(text.count("## %s" % self._today()), 1, "exactly one today-section remains")
        self.assertEqual(self._head_files(), ["CHANGELOG.md"], "HEAD must be a notes commit touching only CHANGELOG.md")

    def test_authoring_prepend_when_published(self):
        self._build_fixture("published_changelog")
        self._install_scanner("noop")
        origin_tip = self._rev_parse("origin/main")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "second release marker")
        authoring = self._authoring_step()
        exports, _ = self._require_authoring_contract(authoring)
        self._release_lock(exports)
        self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        text = (self.clone / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("published section marker", text, "the published section stays untouched")
        self.assertIn("second release marker", text, "a new section is prepended")
        self.assertLess(
            text.index("second release marker"), text.index("published section marker"),
            "the new section must sit above the published one",
        )
        self.assertEqual(text.count("## %s" % self._today()), 2, "same-day second release keeps its own section")
        self.assertEqual(self._rev_parse("origin/main"), origin_tip, "authoring never pushes")
        self.assertEqual(self._head_files(), ["CHANGELOG.md"], "HEAD must be a notes commit touching only CHANGELOG.md")

    def test_authoring_staging_isolation(self):
        self._build_fixture()
        self._install_scanner("noop")
        (self.clone / "unrelated.txt").write_text("unrelated staged work\n", encoding="utf-8")
        self._gitx("add", "--", "unrelated.txt")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "staging isolation marker")
        authoring = self._authoring_step()
        exports, _ = self._require_authoring_contract(authoring)
        self._release_lock(exports)
        self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        # FIRST: HEAD is a notes commit touching only CHANGELOG.md with the
        # section content present.
        self.assertEqual(self._head_files(), ["CHANGELOG.md"])
        self.assertIn("staging isolation marker", (self.clone / "CHANGELOG.md").read_text(encoding="utf-8"))
        # THEN: the pre-staged unrelated file stays staged and untouched.
        self.assertIn("A  unrelated.txt", self._porcelain(), "the pre-staged file must remain staged")

    def test_authoring_skip_identical(self):
        self._build_fixture()
        self._install_scanner("noop")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "identical section marker")
        first = self._authoring_step()
        exports, _ = self._require_authoring_contract(first)
        self._release_lock(exports)
        self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        # FIRST: the rerun baseline is a notes commit touching only CHANGELOG.md.
        head_after_first = self._rev_parse("HEAD")
        self.assertEqual(self._head_files(), ["CHANGELOG.md"])
        self.assertIn("identical section marker", (self.clone / "CHANGELOG.md").read_text(encoding="utf-8"))
        # Rerun with a byte-identical section.
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "identical section marker")
        second = self._authoring_step()
        exports2, _ = self._require_authoring_contract(second)
        self._release_lock(exports2)
        self._assert_release_logged(exports2["DONE_LOCK_TOKEN"])
        # THEN: no second notes commit was created.
        self.assertEqual(self._rev_parse("HEAD"), head_after_first, "an identical rerun must skip the notes commit")

    def test_authoring_changelog_dirty_aborts(self):
        self._build_fixture()
        self._install_scanner("noop")
        (self.clone / "CHANGELOG.md").write_text("# Changelog\n\nhistory section\n", encoding="utf-8")
        self._gitx("add", "--", "CHANGELOG.md")
        self._gitx("commit", "-q", "-m", "changelog baseline")
        dirty = "# Changelog\n\nhistory section\n\nuser dirt line\n"
        (self.clone / "CHANGELOG.md").write_text(dirty, encoding="utf-8")
        head_before = self._rev_parse("HEAD")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "dirty changelog marker")
        authoring = self._authoring_step()
        self._release_last_acquisition()
        self.assertNotEqual(
            authoring.returncode, 0,
            "a dirty CHANGELOG must abort:\n%s\n%s" % (authoring.stdout, authoring.stderr),
        )
        self.assertEqual(self._rev_parse("HEAD"), head_before, "no notes commit may be created")
        self.assertEqual(
            (self.clone / "CHANGELOG.md").read_text(encoding="utf-8"), dirty,
            "the user's dirty content must stay byte-identical",
        )
        self._assert_lock_was_acquired()

    def test_authoring_em_dash_note_aborts(self):
        self._build_fixture()
        self._install_scanner("noop")
        self._draft_section(
            DEFAULT_COUNTS, DEFAULT_MSGS, "em dash marker",
            extra_line="prose carrying an em dash " + EM_DASH + " here",
        )
        head_before = self._rev_parse("HEAD")
        authoring = self._authoring_step()
        self._release_last_acquisition()
        self.assertNotEqual(
            authoring.returncode, 0,
            "an em dash in the drafted section must abort:\n%s\n%s" % (authoring.stdout, authoring.stderr),
        )
        self.assertEqual(self._rev_parse("HEAD"), head_before, "no notes commit may be created")
        porcelain = self._porcelain()
        self.assertNotIn("CHANGELOG", porcelain, "CHANGELOG.md must stay untouched")
        for line in porcelain.splitlines():
            self.assertTrue(
                line.startswith("??"),
                "the abort must happen before staging; unexpected non-untracked entry: %s" % line,
            )
        self._assert_lock_was_acquired()

    # ------------------------------------------------------------------
    # Follow-up plan cases (run-dir teardown, snapshot scope, relay,
    # checker resolution, step-7 restore)
    # ------------------------------------------------------------------

    def test_authoring_whole_file_em_dash_restores_and_cleans_run_dir(self):
        self._build_fixture("changelog_em_dash")
        self._install_scanner("noop")
        changelog = self.clone / "CHANGELOG.md"
        before = changelog.read_bytes()
        head_before = self._rev_parse("HEAD")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "whole-file em dash marker")
        authoring = self._authoring_step()
        self._release_last_acquisition()
        self.assertNotEqual(
            authoring.returncode, 0,
            "a pre-existing em dash in CHANGELOG.md must abort the whole-file scan:\n%s\n%s"
            % (authoring.stdout, authoring.stderr),
        )
        self.assertIn("pre-existing em dash", authoring.stderr, "the abort must name the whole-file scan failure")
        self.assertEqual(authoring.stdout.count("export DONE_LOCK_DIR="), 1,
                         "the die() relay must reach stdout exactly once:\n%s" % authoring.stdout)
        self.assertEqual(authoring.stdout.count("export DONE_LOCK_TOKEN="), 1)
        self.assertEqual(changelog.read_bytes(), before, "the pre-run CHANGELOG.md must be restored byte-identical")
        self.assertEqual(self._rev_parse("HEAD"), head_before, "no notes commit may be created")
        self._assert_lock_was_acquired()
        self.assertEqual(
            list(self.tmpdir.glob("release-authoring-*")), [],
            "the authoring failure exit must remove the run dir",
        )

    def test_push_reassertion_ignores_untracked_stray_file(self):
        rewrite, _, _, _ = self._run_release()
        self.assertEqual(
            rewrite.returncode, 0,
            "rewrite failed rc=%s\nstdout:\n%s\nstderr:\n%s" % (rewrite.returncode, rewrite.stdout, rewrite.stderr),
        )
        push_script = self._find_push_script()
        rewritten_tip = self._rev_parse("main")
        base_tip = self._rev_parse("origin/main")
        (self.clone / "stray-untracked.txt").write_text("stray file between swap and push\n", encoding="utf-8")
        pushed = self._execute_push_script(push_script)
        self.assertEqual(
            pushed.returncode, 0,
            "a stray untracked file must not abort the push re-assertion:\n%s" % (pushed.stdout + pushed.stderr),
        )
        self.assertEqual(self._rev_parse("origin/main"), rewritten_tip, "the push publishes the verified tip")
        self.assertNotEqual(self._rev_parse("origin/main"), base_tip)
        # The tracked-modification polarity stays covered by
        # test_post_swap_snapshot_mismatch_aborts (an uncommitted tracked edit
        # still fails the snapshot re-assertion).

    def test_rewrite_trap_removes_authoring_run_dir(self):
        self._build_fixture()
        self._install_scanner("noop")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "run dir teardown marker")
        authoring = self._authoring_step()
        exports, groups_path = self._require_authoring_contract(authoring)
        run_dir = Path(groups_path).parent
        self.assertIn("release-authoring-", run_dir.name, "the groups file lives in the authoring run dir")
        self.assertTrue(run_dir.exists(), "the run dir must exist while the run is in flight")
        rewrite = self._rewrite_step(groups_path, exports)
        self._release_lock(exports)
        self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        self.assertEqual(
            rewrite.returncode, 0,
            "rewrite failed rc=%s\nstdout:\n%s\nstderr:\n%s" % (rewrite.returncode, rewrite.stdout, rewrite.stderr),
        )
        self.assertFalse(run_dir.exists(), "the rewrite EXIT trap removes the authoring run dir")
        self.assertEqual(
            list(self.tmpdir.glob("release-authoring-*")), [],
            "no authoring run dir may survive the rewrite",
        )

    def test_rewrite_trap_leaves_non_authoring_dirs_alone(self):
        self._build_fixture()
        self._install_scanner("noop")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "guard marker")
        authoring = self._authoring_step()
        exports, groups_path = self._require_authoring_contract(authoring)
        relocated_parent = self.tmpdir / "relocated-groups-parent"
        relocated_parent.mkdir()
        relocated = relocated_parent / "groups.txt"
        shutil.copyfile(groups_path, relocated)
        rewrite = self._rewrite_step(str(relocated), exports)
        self._release_lock(exports)
        self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        self.assertEqual(
            rewrite.returncode, 0,
            "rewrite failed rc=%s\nstdout:\n%s\nstderr:\n%s" % (rewrite.returncode, rewrite.stdout, rewrite.stderr),
        )
        self.assertTrue(relocated.exists(), "a directory outside the release-authoring-* mktemp shape must survive the trap")
        self.assertEqual((relocated_parent / "groups.txt").read_bytes(), Path(groups_path).read_bytes())

    def test_lock_relay_set_e_fault_exactly_once(self):
        self._build_fixture()
        self._install_scanner("noop")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "relay fault marker")
        self._write_shim("commit-fail")
        authoring = self._authoring_step()
        self._release_last_acquisition()
        self.assertNotEqual(
            authoring.returncode, 0,
            "a set -e exit on the step-8 commit must abort:\n%s\n%s" % (authoring.stdout, authoring.stderr),
        )
        self._assert_lock_was_acquired()
        self.assertEqual(authoring.stdout.count("export DONE_LOCK_DIR="), 1,
                         "the EXIT-trap relay must reach stdout exactly once (no double relay):\n%s" % authoring.stdout)
        self.assertEqual(authoring.stdout.count("export DONE_LOCK_TOKEN="), 1)
        # The relayed values must be well-formed, not merely present once: a
        # corrupted relay (a broken trap quoting would leave a stray suffix on
        # the token) would make the calling shell's release mismatch.
        relay, _ = self._parse_authoring(authoring)
        acquired = self._last_acquire_exports()
        self.assertTrue(acquired, "the faulted run must have acquired the lock first")
        self.assertEqual(relay.get("DONE_LOCK_DIR"), acquired["DONE_LOCK_DIR"],
                         "the relayed DONE_LOCK_DIR must equal the acquired value:\n%s" % authoring.stdout)
        self.assertEqual(relay.get("DONE_LOCK_TOKEN"), acquired["DONE_LOCK_TOKEN"],
                         "the relayed DONE_LOCK_TOKEN must equal the acquired value:\n%s" % authoring.stdout)
        self.assertNotIn("groups-file ", authoring.stdout, "a faulted run never reaches the success-path data line")
        self.assertEqual(
            list(self.tmpdir.glob("release-authoring-*")), [],
            "the non-zero EXIT-trap path removes the run dir",
        )

    def test_lock_relay_success_exactly_once(self):
        self._build_fixture()
        self._install_scanner("noop")
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "relay success marker")
        authoring = self._authoring_step()
        exports, groups_path = self._require_authoring_contract(authoring)
        self._release_lock(exports)
        self._assert_release_logged(exports["DONE_LOCK_TOKEN"])
        self.assertEqual(authoring.stdout.count("export DONE_LOCK_DIR="), 1,
                         "the success path relays the exports exactly once:\n%s" % authoring.stdout)
        self.assertEqual(authoring.stdout.count("export DONE_LOCK_TOKEN="), 1)
        self.assertEqual(authoring.stdout.count("groups-file "), 1)

    def test_missing_em_dash_checker_dies_and_cleans_run_dir(self):
        self._build_fixture()
        self._install_scanner("noop")
        missing = self.tmpdir / "no-such-checker.sh"
        self._draft_section(DEFAULT_COUNTS, DEFAULT_MSGS, "missing checker marker")
        head_before = self._rev_parse("HEAD")
        authoring = subprocess.run(
            ["bash", str(AUTHORING_SCRIPT), str(self.section_path)],
            cwd=str(self.clone), env=self._run_env(env_extra={"CHECK_NO_EM_DASH_SCRIPT": str(missing)}),
            capture_output=True, text=True,
        )
        self._release_last_acquisition()
        self.assertNotEqual(
            authoring.returncode, 0,
            "a missing checker must abort:\n%s\n%s" % (authoring.stdout, authoring.stderr),
        )
        self.assertIn("em-dash checker not found", authoring.stderr, "the abort names the environment failure")
        self.assertIn(str(missing), authoring.stderr, "the abort names the missing path")
        self.assertNotIn("carries an em dash", authoring.stderr, "a missing checker must never be reported as a policy hit")
        self.assertEqual(authoring.stdout.count("export DONE_LOCK_DIR="), 1,
                         "the die() relay must reach stdout exactly once:\n%s" % authoring.stdout)
        self.assertEqual(authoring.stdout.count("export DONE_LOCK_TOKEN="), 1)
        relay, _ = self._parse_authoring(authoring)
        acquired = self._last_acquire_exports()
        self.assertTrue(acquired, "the aborting run must have acquired the lock first")
        self.assertEqual(relay.get("DONE_LOCK_DIR"), acquired["DONE_LOCK_DIR"])
        self.assertEqual(relay.get("DONE_LOCK_TOKEN"), acquired["DONE_LOCK_TOKEN"])
        self._assert_lock_was_acquired()
        self.assertEqual(self._rev_parse("HEAD"), head_before, "no notes commit may be created")
        self.assertEqual(
            list(self.tmpdir.glob("release-authoring-*")), [],
            "the abort also witnesses the authoring failure-exit run-dir removal",
        )


class ReleasePrivacyLocatorsHelperTest(unittest.TestCase):
    """Direct locator-helper contract cases (plan Task 1): row acceptance,
    the 65,536-byte bound, control-byte escaping, dedup, and exit
    passthrough, each against a fixture scanner stub replaying fixed stdout
    bytes and a chosen exit code."""

    def setUp(self) -> None:
        self.base = Path(tempfile.mkdtemp(prefix="release-locators-"))
        self.addCleanup(shutil.rmtree, self.base, True)

    def _write_row_stub(self, payload: bytes, rc: int) -> Path:
        fixture = self.base / "scanner-stdout.bin"
        fixture.write_bytes(payload)
        stub = self.base / "fixture-scanner.sh"
        stub.write_text(
            "#!/usr/bin/env bash\n"
            "# selftest locator fixture scanner: replay the fixture bytes, exit rc.\n"
            'cat "%s"\n'
            "exit %d\n" % (fixture, rc),
            encoding="utf-8",
        )
        stub.chmod(0o755)
        return stub

    def _run_helper(self, stub: Path, paths):
        return subprocess.run(
            [sys.executable, str(LOCATOR_HELPER), "--scanner", str(stub), "--", "--files", *paths],
            capture_output=True,
        )

    def test_multiple_hits_and_dedup(self):
        payload = (
            b"FAIL: files\n"
            b"docs/x.md:3:SECRETCONTENT\n"
            b"docs/x.md:3:SECRETCONTENT\n"
            b"release-groups.txt:5:OTHERSECRET\n"
            b"\n"
            b"FAIL: files\n"
            b"docs/x.md:7:MORESECRET\n"
            b"\n"
            b"=== 2 public-hygiene failure(s) ===\n"
            b"OUTCOME: fail\n"
        )
        proc = self._run_helper(self._write_row_stub(payload, 1), ["docs/x.md", "release-groups.txt"])
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(
            proc.stdout,
            b"docs/x.md:3\nrelease-groups.txt:5\ndocs/x.md:7\n",
            "each distinct locator once, first-seen order",
        )
        self.assertNotIn(b"SECRETCONTENT", proc.stdout, "matched content must never be emitted")

    def test_malformed_and_absent_rows_rejected(self):
        payload = (
            b"FAIL: files\n"
            b"no-colon-at-all\n"
            b"docs/x.md:notdigits:hit\n"
            b":5:empty-path\n"
            b"docs/x.md\n"
            b"\n"
            b"OUTCOME: fail\n"
        )
        proc = self._run_helper(self._write_row_stub(payload, 1), ["docs/x.md", "release-groups.txt"])
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(proc.stdout, b"", "malformed and rowless paths yield no locator")

    def test_unrequested_path_yields_no_locator(self):
        payload = b"FAIL: files\nsecret.md:5:SECRETCONTENT\n\n"
        proc = self._run_helper(self._write_row_stub(payload, 1), ["docs/x.md"])
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(proc.stdout, b"", "an unrequested path yields no locator")
        self.assertNotIn(b"secret.md", proc.stdout)
        self.assertNotIn(b"SECRETCONTENT", proc.stdout)

    def test_single_file_line_content_hit(self):
        # One scanned path: ripgrep's line:content form assigns the sole path.
        payload = b"FAIL: files\n12:SECRETCONTENT\n\n"
        proc = self._run_helper(self._write_row_stub(payload, 1), ["only.md"])
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(proc.stdout, b"only.md:12\n")

    def test_multi_path_line_only_row_rejected(self):
        # Several scanned paths: a pathless row names no requested path.
        payload = b"FAIL: files\n12:SECRETCONTENT\n\n"
        proc = self._run_helper(self._write_row_stub(payload, 1), ["only.md", "two.md"])
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(proc.stdout, b"")

    def test_overlapping_colon_paths_resolve(self):
        payload = b"FAIL: files\na:b.txt:4:SECRETCONTENT\n\n"
        proc = self._run_helper(self._write_row_stub(payload, 1), ["a", "a:b.txt"])
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(proc.stdout, b"a:b.txt:4\n", "the exact requested prefix wins")

    def test_ambiguous_prefix_yields_no_locator(self):
        payload = b"FAIL: files\none:2:3:SECRETCONTENT\n\n"
        proc = self._run_helper(self._write_row_stub(payload, 1), ["one", "one:2"])
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(proc.stdout, b"", "an ambiguous prefix yields no locator")

    def test_digit_prefixed_content_keeps_first_split(self):
        payload = b"FAIL: files\ndocs/x.md:3:12:SECRETCONTENT\n\n"
        proc = self._run_helper(self._write_row_stub(payload, 1), ["docs/x.md"])
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(proc.stdout, b"docs/x.md:3\n", "digits-and-colon content must not remap the locator")

    def test_exact_bound_parses(self):
        row = b"docs/x.md:9:SECRETCONTENT\n"
        payload = b"z" * (65536 - len(row) - 4) + b"pad\n" + row
        self.assertEqual(len(payload), 65536, "the fixture must sit exactly at the parse bound")
        proc = self._run_helper(self._write_row_stub(payload, 1), ["docs/x.md"])
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(proc.stdout, b"docs/x.md:9\n", "exactly 65,536 bytes still parse")

    def test_bound_exceeded_discards_and_reports(self):
        row = b"docs/x.md:9:SECRETCONTENT\n"
        payload = b"z" * (65536 - len(row) - 4) + b"pad\n" + row + b"q"
        self.assertEqual(len(payload), 65537, "the fixture must cross the parse bound by one byte")
        proc = self._run_helper(self._write_row_stub(payload, 1), ["docs/x.md"])
        self.assertEqual(proc.returncode, 1, "the bound fallback must not change the scanner exit class")
        self.assertEqual(proc.stdout, b"LOCATOR-BOUND-EXCEEDED\n", "the bounded-output fallback is reported")
        self.assertNotIn(b"docs/x.md", proc.stdout, "an over-bound run emits no locators")
        self.assertNotIn(b"SECRETCONTENT", proc.stdout)

    def test_control_bytes_escaped(self):
        payload = b"dirty\x07:1:SECRETCONTENT\n"
        proc = self._run_helper(self._write_row_stub(payload, 1), ["dirty\x07"])
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(proc.stdout, b"dirty\\x07:1\n", "the control byte must be escaped")
        self.assertNotIn(b"\x07", proc.stdout, "no raw control byte may reach the output")
        self.assertNotIn(b"SECRETCONTENT", proc.stdout)

    def test_undecodable_path_bytes_escaped(self):
        payload = b"caf\xff:2:SECRETCONTENT\n"
        proc = self._run_helper(self._write_row_stub(payload, 1), ["caf\udcff"])
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(proc.stdout, b"caf\\xff:2\n", "an undecodable byte must be escaped")
        self.assertNotIn(b"\xff", proc.stdout)
        self.assertNotIn(b"SECRETCONTENT", proc.stdout)

    def test_clean_output_and_exit_passthrough(self):
        payload = b"=== PASS (public hygiene) ===\nOUTCOME: pass\n"
        clean = self._run_helper(self._write_row_stub(payload, 0), ["a.md"])
        self.assertEqual(clean.returncode, 0, clean.stderr)
        self.assertEqual(clean.stdout, b"", "a no-hit run emits no locators")
        tool_error = self._run_helper(self._write_row_stub(b"", 3), ["a.md"])
        self.assertEqual(tool_error.returncode, 3, "the scanner exit class must pass through")
        self.assertEqual(tool_error.stdout, b"")


if __name__ == "__main__":
    unittest.main()
