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
  (exit 2), ``lognoop`` (exit 0 plus an argv witness log, used by the
  tree-materialization-failure case to prove no materialized file reaches the
  scanner).
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
import os
import re
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORING_SCRIPT = ROOT / "scripts" / "release-authoring.sh"
REWRITE_SCRIPT = ROOT / "scripts" / "release-rewrite.sh"
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
        prepended to PATH. TZ is pinned to UTC and ambient git-context and
        author/committer variables are stripped, so a midnight rollover in the
        local zone or a leaked GIT_DIR/GIT_CONFIG_COUNT/GIT_*_DATE from the
        calling session cannot flip date-dependent or identity-dependent
        behavior under test."""
        env = dict(os.environ)
        env.update(self._git_env_overrides())
        env["TMPDIR"] = str(self.tmpdir)
        env["DONE_LOCK_SCRIPT"] = str(self.lock_stub)
        env["SELFTEST_LOCK_LOG"] = str(self.lock_log)
        env["SELFTEST_SCANNER_LOG"] = str(self.scanner_log)
        env["PUBLIC_HYGIENE_PATTERNS_FILE"] = str(self.patterns)
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

    def _rewrite_step(self, groups_path, exports, shim: str = "pass"):
        self._write_shim(shim)
        return subprocess.run(
            ["bash", str(REWRITE_SCRIPT), str(groups_path)],
            cwd=str(self.clone), env=self._run_env(lock_exports=exports),
            capture_output=True, text=True,
        )

    def _run_release(self, variant: str = "clean", scanner: str = "noop",
                     counts=None, msgs=None, marker: str = "selftest section marker",
                     rewrite_shim: str = "pass"):
        """Authoring plus rewrite plus the lock release, returning the rewrite
        result, the exports, the groups file path, and the pre-rewrite tip."""
        self._build_fixture(variant)
        self._install_scanner(scanner)
        self._draft_section(counts or DEFAULT_COUNTS, msgs or DEFAULT_MSGS, marker)
        authoring = self._authoring_step()
        exports, groups_path = self._require_authoring_contract(authoring)
        pre_tip = self._rev_parse("main")
        rewrite = self._rewrite_step(groups_path, exports, shim=rewrite_shim)
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


if __name__ == "__main__":
    unittest.main()
