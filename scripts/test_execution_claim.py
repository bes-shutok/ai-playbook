"""Selftest for the execution-claim gateway (scripts/execution_claim.sh).

Covers the gateway contract: the cold-start take creating both claim and
worktree, the fresh-foreign refusal naming holder, age, occupying worktree,
and override route, the stale takeover, the takeover with an occupied
branch, the own-claim existing-worktree refusal keeping the claim, the
failed-create cleanup, the release ownership fence, refresh re-stamping /
recreating / fencing, the claim-only mode, the recorded branch and
start-commit lines (written when passed, the unresolvable start-commit
usage refusal writing nothing, refresh and the takeover and recreate
rebuild paths carrying them), slug derivation through the
python SOT, the missing-primary-checkout tool error, and the exit-path
cleanup (the trap removing a fresh claim, and any worktree the in-flight
add brought into existence, on a failure or signal after the claim was
created, disarmed on the success path; the cleanup's owner check leaves a
claim naming a foreign session untouched; the signal tests deliver their
signal to the process group while the PATH-shimmed worktree add is parked,
so the parked git child dies too and the outcome is deterministic), and
the race-retry witnesses (plan 2026-10-13-machinery-script-refactor-program,
Task 3): a permanently contended claims directory, built by a dangling
symlink at the claim path which the noclobber create refuses
deterministically and root-proofly, fails both retry loops after the third
attempt with the racing tool error, and a lost-then-won contender, a date
shim planting that link once and releasing on every later call, is won on
attempt 2 with the state flags exactly as a cold start sets them.
The sweep arm is covered over the same scratch repositories: it deletes
exactly the spent claims (the plan landed through the plans root's
completed/ archive or through a main-history landing subject naming the
claim's slug, the recorded branch resolving to no worktree) and skips
every other claim untouched with a one-line reason (a plan parked under
the plans root outside completed/ included, landing subject or not).

Hermetic by construction: every fixture builds its own scratch git
repository under a mktemp parent, and that scratch repository is its own
primary checkout (the first `git worktree list --porcelain` entry), so the
real repository's claims directory is never touched. The script resolves
its repository anchor from the process working directory, so each run
invokes the script with the scratch repository as cwd; no override seam and
no checkouts of this repository are involved.

Run from the repository root:

    python3 scripts/test_execution_claim.py
"""

import os
import shutil
import signal
import subprocess
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "execution_claim.sh"

PLAN_NAME = "2026-09-01-exec-claim-fixture-story.md"
SLUG = "exec-claim-fixture-story"
UPPER_PLAN_NAME = "2026-09-01-EXEC-CLAIM-Fixture-Story.md"
CANONICAL_SLUG = "exec-claim-fixture-story"

FRESH_AGE = timedelta(minutes=5)
STALE_AGE = timedelta(hours=3)


def iso_stamp(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class TestExecutionClaim(unittest.TestCase):
    """The execution-claim gateway script's behavior over scratch repos."""

    def setUp(self):
        self.scratch = Path(tempfile.mkdtemp(prefix="exec-claim-fixture-"))
        self.addCleanup(shutil.rmtree, self.scratch, True)
        self.repo = self.scratch / "primary"
        self.repo.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "fixture@example.invalid")
        self._git("config", "user.name", "Fixture")
        self._git("commit", "--allow-empty", "-q", "-m", "init")
        self.plan = self.scratch / PLAN_NAME
        self.plan.write_text("# Fixture plan\n", encoding="utf-8")
        self.claims_dir = self.repo / "docs" / "tmp" / "execution-claims"
        self.claim = self.claims_dir / f"{SLUG}.md"
        self.wt_parent = self.scratch / "wt"
        self.branch = "fixture/feature-branch"
        # Hermetic by construction (the review r1 B1 fold): the trusted
        # lock-root seam points every test's gateway invocations at a
        # scratch lock home, and the scratch primary carries the facts
        # document the preservation scan and provider resolution read.
        lock_home = self.scratch / "lock-home"
        lock_home.mkdir()
        os.environ["EXECUTION_CLAIM_LOCK_HOME"] = str(lock_home)
        self.addCleanup(os.environ.pop, "EXECUTION_CLAIM_LOCK_HOME", None)
        facts_dir = self.repo / ".ai-playbook"
        facts_dir.mkdir(exist_ok=True)
        (facts_dir / "facts.md").write_text(
            'tmp_dir = "docs/tmp"\n', encoding="utf-8"
        )

    # -- helpers -------------------------------------------------------- #

    def _git(self, *args):
        subprocess.run(
            ["git", "-C", str(self.repo), *args],
            check=True,
            capture_output=True,
            timeout=60,
        )

    def _run(self, *args, cwd=None, path_prepend=None, extra_env=None):
        env = os.environ.copy()
        if path_prepend is not None:
            env["PATH"] = str(path_prepend) + os.pathsep + env["PATH"]
        if extra_env:
            env.update({k: str(v) for k, v in extra_env.items()})
        return subprocess.run(
            ["bash", str(SCRIPT), *args],
            cwd=str(cwd or self.repo),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

    def _git_out(self, *args) -> str:
        return subprocess.run(
            ["git", "-C", str(self.repo), *args],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        ).stdout.strip()

    def _git_ok(self, *args) -> bool:
        return (
            subprocess.run(
                ["git", "-C", str(self.repo), *args],
                capture_output=True,
                timeout=60,
            ).returncode
            == 0
        )

    def _registered_worktree_paths(self):
        # The registered worktree paths, physical-normalized (git stores
        # symlink-resolved forms, the macOS /private variants of the fixture
        # paths the tests hand out), so membership checks cannot miss on a
        # path-form technicality.
        out = self._git_out("worktree", "list", "--porcelain")
        return [
            os.path.realpath(line[len("worktree "):])
            for line in out.splitlines()
            if line.startswith("worktree ")
        ]

    def _date_shim(self, fixed_epoch: int) -> Path:
        """A PATH shim answering `date -u +%s` with a fixed epoch while
        passing every other date form through to the real binary: pins the
        script's freshness clock so a boundary test cannot flake on the
        wall-clock delta between seeding the claim and the script's read
        (no sleeps; bounded runtime by construction)."""
        real_date = shutil.which("date")
        self.assertIsNotNone(real_date, "date not found on PATH")
        bin_dir = self.scratch / "date-shim-bin"
        bin_dir.mkdir(exist_ok=True)
        shim = bin_dir / "date"
        shim.write_text(
            "#!/bin/sh\n"
            'if [ "$1" = "-u" ] && [ "$2" = "+%s" ]; then\n'
            f"  printf '%s\\n' {fixed_epoch}\n"
            "  exit 0\n"
            "fi\n"
            f'exec "{real_date}" "$@"\n',
            encoding="utf-8",
        )
        shim.chmod(0o755)
        return bin_dir

    def _plant_dangling_symlink_at_claim(self):
        """The permanently contended claims directory fixture: a dangling
        symlink at the claim path. The noclobber create refuses it
        deterministically (the exclusive create behind `set -o noclobber`
        fails on any existing directory entry, a dangling symlink included)
        and root-proofly (a shell-level existence check, no permission bits
        involved), so neither a PATH shim (it cannot fail the builtin's own
        redirect) nor a chmod (root ignores permission bits) can build this
        fixture. `[[ -e ]]` follows the symlink and reads absent, so every
        retry re-enters the create branch and loses again until the
        ceiling fires."""
        self.claims_dir.mkdir(parents=True, exist_ok=True)
        os.symlink(str(self.claim) + ".planted-target", str(self.claim))

    def _physical_claim(self):
        """The claim path in the physical form the script prints and errors
        with: PRIMARY resolves through `git worktree list` to git's stored
        physical path, so on macOS the /var prefix of the fixture's logical
        path reads /private/var in every CLAIM_PATH-bearing line."""
        return (
            Path(os.path.realpath(self.repo))
            / "docs" / "tmp" / "execution-claims" / f"{SLUG}.md"
        )

    def _lost_then_won_date_shim(self):
        """The lost-then-won contender stub: a date shim, never a timed
        contender file. The racing create's stamp read (`iso_now` inside
        create_claim_noclobber) is the script's first date invocation, so
        the shim's first invocation plants a dangling symlink at the claim
        path and exits nonzero: the failed stamp is absorbed in the
        create's condition context (the create runs under `if !`, where
        errexit is ignored) and the noclobber create then refuses the
        planted link, losing attempt one. Every later invocation removes
        the planted link and delegates to the real date, so attempt two's
        create wins. The marker records that the plant happened exactly
        once; the returned bin dir goes on PATH ahead of the system
        paths."""
        real_date = shutil.which("date")
        self.assertIsNotNone(real_date, "date not found on PATH")
        bin_dir = self.scratch / "lost-then-won-bin"
        bin_dir.mkdir(exist_ok=True)
        marker = self.scratch / "lost-then-won-planted"
        shim = bin_dir / "date"
        # The plant keys on the STAMP-FORM date calls (the ISO stamp the
        # claim writer and the lock meta both draw), not the global call
        # index: the merge-lock discipline added stamp-form consumers, and
        # the contender's contract is "the first stamp consumer loses, the
        # rest release", whatever command issues them.
        shim.write_text(
            "#!/bin/sh\n"
            'case "$* " in\n'
            '  *" +%Y-%m-%dT%H:%M:%SZ "*)\n'
            "    n=0\n"
            f'    [ -f "{marker}.count" ] && n=$(cat "{marker}.count")\n'
            "    n=$((n + 1))\n"
            f'    printf %s "$n" > "{marker}.count"\n'
            '    if [ "$n" -eq 1 ]; then\n'
            f'      : > "{marker}"\n'
            f'      ln -s "{self.claim}.planted-target" "{self.claim}"\n'
            "      exit 1\n"
            "    fi\n"
            '    if [ "$n" -eq 2 ]; then\n'
            f'      rm -f "{self.claim}"\n'
            "    fi\n"
            "    ;;\n"
            "esac\n"
            f'exec "{real_date}" "$@"\n',
            encoding="utf-8",
        )
        shim.chmod(0o755)
        return bin_dir, marker

    def _take(self, session, branch=None, plan=None, parent=None, cwd=None, base=None, path_prepend=None):
        args = [
            "take",
            str(plan or self.plan),
            "--session", session,
            "--branch", branch or self.branch,
            "--worktree-parent", str(parent or self.wt_parent),
        ]
        if base is not None:
            args += ["--base", base]
        return self._run(*args, cwd=cwd, path_prepend=path_prepend)

    def _git_worktree_add_parker(self, registered: Path, unblock: Path) -> Path:
        """A PATH shim making `git ... worktree add` two-phase: it first
        runs the real add with --no-checkout (so the worktree IS registered,
        the exact strand state a killed add leaves behind), writes the
        registered marker, then parks until the unblock file appears. The
        script therefore sits inside an in-flight add over an
        already-registered worktree when the test signals the process group,
        which deterministically reproduces the strand window (a signal that
        kills only the bash pid, or lands before registration, does not).
        A bounded park keeps a broken run failing instead of hanging."""
        real_git = shutil.which("git")
        self.assertIsNotNone(real_git, "git not found on PATH")
        budget_ticks = 300  # 300 * 0.05s = 15s, then proceed anyway
        bin_dir = self.scratch / "parker-bin"
        bin_dir.mkdir()
        shim = bin_dir / "git"
        shim.write_text(
            "#!/bin/sh\n"
            'if [ "$3" = "worktree" ] && [ "$4" = "add" ]; then\n'
            "  shift 4\n"
            f'  if ! "{real_git}" worktree add --no-checkout "$@"; then\n'
            "    exit 1\n"
            "  fi\n"
            f'  : > "{registered}"\n'
            "  i=0\n"
            f'  while [ ! -f "{unblock}" ] && [ "$i" -lt {budget_ticks} ]; do\n'
            '    sleep 0.05\n'
            '    i=$((i + 1))\n'
            "  done\n"
            "  exit 0\n"
            "fi\n"
            f'exec "{real_git}" "$@"\n',
            encoding="utf-8",
        )
        shim.chmod(0o755)
        return bin_dir

    def _take_popen(self, session, unblock: Path) -> subprocess.Popen:
        env = os.environ.copy()
        registered = self.scratch / "git-add-registered"
        env["PATH"] = str(self._git_worktree_add_parker(registered, unblock)) + os.pathsep + env["PATH"]
        # start_new_session puts the script and its in-flight git child in
        # one fresh process group, so the test can signal the group and both
        # die together (signalling only the bash pid leaves the parked git
        # child alive and the outcome racy).
        return subprocess.Popen(
            [
                "bash", str(SCRIPT), "take", str(self.plan),
                "--session", session,
                "--branch", self.branch,
                "--worktree-parent", str(self.wt_parent),
            ],
            cwd=str(self.repo),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )

    def _take_signalled_at_fresh_claim(self, sig, expected_code):
        """Start a take, signal the process group once the PATH-shimmed
        worktree add is IN FLIGHT over an already-registered worktree (the
        shim's registered marker is out), then let it finish; the ordering
        invariant must hold end to end: the signal's 128+N exit status, the
        fresh claim gone, and no worktree left behind or registered (any
        non-zero exit implies neither survives; rc 0 implies both exist,
        pinned by the cold-start test)."""
        unblock = self.scratch / "unblock-git-add"
        registered = self.scratch / "git-add-registered"
        proc = self._take_popen("session-b", unblock)
        try:
            deadline = time.monotonic() + 30
            while not self.claim.exists():
                if proc.poll() is not None or time.monotonic() > deadline:
                    self.fail(
                        "the claim never appeared; the script exited or "
                        f"stalled before parking (rc={proc.poll()})"
                    )
                time.sleep(0.01)
            while not registered.exists():
                if proc.poll() is not None or time.monotonic() > deadline:
                    self.fail(
                        "the worktree add never went in flight over a "
                        "registered worktree; the script exited or stalled "
                        f"after the claim (rc={proc.poll()})"
                    )
                time.sleep(0.01)
            os.killpg(proc.pid, sig)
            unblock.write_text("go", encoding="utf-8")
            proc.communicate(timeout=60)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.communicate()
        self.assertEqual(proc.returncode, expected_code)
        self.assertFalse(
            self.claim.exists(), "the fresh claim survived the signal"
        )
        self.assertFalse(
            (self.wt_parent / self.branch).exists(),
            "a half-created worktree survived the signal",
        )
        registered_list = subprocess.run(
            ["git", "-C", str(self.repo), "worktree", "list", "--porcelain"],
            check=True, capture_output=True, text=True, timeout=60,
        ).stdout
        self.assertNotIn(
            str(self.wt_parent / self.branch), registered_list,
            "the worktree stayed registered after the signal",
        )
        # The take leaves no half-created state at all: the branch the
        # in-flight add created (the add creates the branch before the
        # worktree exists) is rolled back by the cleanup too, so a retry
        # take of the same branch name is not blocked by a stranded ref.
        self.assertFalse(
            self._git_ok("rev-parse", "--verify", "-q", "refs/heads/" + self.branch),
            "the branch the in-flight add created survived the signal",
        )

    def _claim_args(self, session, plan=None):
        return (
            "claim",
            str(plan or self.plan),
            "--session", session,
            "--branch", self.branch,
            "--worktree-parent", str(self.wt_parent),
        )

    def _outcome_line(self, proc):
        lines = [line for line in proc.stdout.splitlines() if line.strip()]
        self.assertTrue(
            lines, f"no stdout lines: stdout={proc.stdout!r} stderr={proc.stderr!r}"
        )
        return lines[-1]

    def _seed_claim(self, session, age, plan_path=None, now=None, branch=None):
        self.claims_dir.mkdir(parents=True, exist_ok=True)
        now = now or datetime.now(timezone.utc)
        created = iso_stamp(now - age - timedelta(minutes=1))
        updated = iso_stamp(now - age)
        text = (
            f"session: {session}\n"
            f"plan: {plan_path or self.plan}\n"
            f"created: {created}\n"
            f"updated: {updated}\n"
        )
        if branch is not None:
            text += f"branch: {branch}\n"
        self.claim.write_text(text, encoding="utf-8")

    def _seed_worktree(self, branch, name, parent=None):
        path = (parent or self.scratch) / name
        self._git("worktree", "add", "-b", branch, str(path))
        # Registered worktrees carry a facts document: the preservation
        # scan refuses discovery (and preserves every claim) when any
        # registered worktree's facts are unreadable, so the fixtures that
        # mean to exercise the deletion/takeover legs write the file.
        (path / ".ai-playbook").mkdir(exist_ok=True)
        (path / ".ai-playbook" / "facts.md").write_text(
            'tmp_dir = "docs/tmp"\n', encoding="utf-8"
        )
        return path

    def _claim_session(self):
        for line in self.claim.read_text(encoding="utf-8").splitlines():
            if line.startswith("session: "):
                return line[len("session: "):]
        self.fail("claim carries no session: line")

    def _release(self, session):
        return self._run("release", str(self.plan), "--session", session)

    def _updated_stamp(self):
        for line in self.claim.read_text(encoding="utf-8").splitlines():
            if line.startswith("updated: "):
                return line[len("updated: "):]
        self.fail("claim carries no updated: line")

    def _hash_file(self, path) -> str:
        import hashlib
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    # -- take ----------------------------------------------------------- #

    def test_take_cold_start_creates_both(self):
        proc = self._take("session-a")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: pass")
        # Also proves the exit-path cleanup disarmed on the success path:
        # an armed trap would have deleted the claim at script exit.
        self.assertTrue(self.claim.is_file(), "claim missing after cold start")
        claim_text = self.claim.read_text(encoding="utf-8")
        self.assertIn("session: session-a", claim_text)
        # The take requires --branch, so the claim records the branch line
        # beside the four frontmatter lines (the recorded identity the
        # takeover and recreate paths must carry).
        self.assertIn(f"branch: {self.branch}", claim_text)
        self.assertTrue(
            (self.wt_parent / self.branch).is_dir(), "worktree missing after take"
        )

    def test_take_with_base_seeds_worktree_head_and_claim_base_line(self):
        # --base start point: the created worktree's HEAD equals the seeded
        # ref AND differs from the branch tip (the fixture commits once
        # more after capturing the base, so base != HEAD and the assertion
        # discriminates: a take ignoring --base would start at the tip and
        # fail here), and the claim carries the base line (the base line is
        # written after the worktree exists, on the take's success path).
        self._git("commit", "--allow-empty", "-q", "-m", "base commit")
        base_sha = self._git_out("rev-parse", "HEAD")
        self._git("commit", "--allow-empty", "-q", "-m", "ahead of base")
        tip_sha = self._git_out("rev-parse", "HEAD")
        self.assertNotEqual(base_sha, tip_sha)
        proc = self._take("session-b", base=base_sha)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: pass")
        head = self._git_out(
            "-C", str(self.wt_parent / self.branch), "rev-parse", "HEAD"
        )
        self.assertEqual(head, base_sha, "worktree HEAD is not the --base ref")
        self.assertNotEqual(
            head,
            tip_sha,
            "worktree HEAD equals the branch tip; the base ref is not discriminated",
        )
        claim_text = self.claim.read_text(encoding="utf-8")
        self.assertIn(f"base: {base_sha}", claim_text, "claim carries no base line")
        self.assertIn(f"base: {base_sha}", proc.stdout)

    def test_take_fresh_foreign_refusal(self):
        holder_wt = self._seed_worktree(self.branch, "holder-wt")
        self._seed_claim("session-holder", FRESH_AGE)
        before = self.claim.read_text(encoding="utf-8")
        proc = self._take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
        combined = proc.stdout + proc.stderr
        self.assertIn("session-holder", combined)
        # The age assertion is discriminating: the literal "claim age:"
        # followed by a numeric second count ("age" alone matches
        # unrelated words like "agents").
        self.assertRegex(combined, r"claim age: \d+s \(updated: ")
        self.assertIn(str(holder_wt), combined)
        self.assertIn("override", combined)
        self.assertFalse(
            (self.wt_parent / self.branch).exists(), "worktree created despite refusal"
        )
        self.assertEqual(self.claim.read_text(encoding="utf-8"), before)

    # -- dead-run conversion (plan 2026-10-21-dead-run-resume-claim-
    # conversion; the restored-worktree recognition arm's successor) --------

    def _conversion_fixture(self, holder="session-holder", status="terminal",
                            form="canonical"):
        """The full dead-run conversion fixture: a registered worktree at
        the take target carrying a facts-resolved run manifest (the chosen
        identity form), a terminal-shaped runtime state with a well-formed
        pre_archive_receipt whose plan_digest hashes the plan bytes, the
        task implement log at its contract path, a fixture provider
        executable answering the chosen status, and the primary facts file
        naming the provider. Returns (worktree_path, manifest_path)."""
        import hashlib
        import json

        wt = self._seed_worktree(self.branch, os.path.join("wt", self.branch))
        (wt / ".ai-playbook").mkdir(exist_ok=True)
        (wt / ".ai-playbook" / "facts.md").write_text(
            'tmp_dir = "run-tmp"\n', encoding="utf-8"
        )
        run_dir = wt / "run-tmp" / "execute-plan" / SLUG
        run_dir.mkdir(parents=True)
        manifest = run_dir / "manifest.md"
        if form == "canonical":
            manifest.write_text(
                "# Execute-plan session: " + SLUG + "\n"
                "\n"
                "workflow_state: terminal\n"
                f"session_id: {holder}\n"
                f"plan_path: {self.plan}\n"
                f"run_worktree: {wt}\n"
                f"run_branch: {self.branch}\n"
                "\n"
                "task_boundary: task=1 commit=fixture validation=pass\n",
                encoding="utf-8",
            )
        elif form == "legacy-full":
            manifest.write_text(
                "# Execute-plan session: " + SLUG + "\n"
                "\n"
                "workflow_state: terminal\n"
                f"Session: {holder}\n"
                f"Plan: {self.plan}\n"
                "\n"
                "task_boundary: task=1 commit=fixture validation=pass\n",
                encoding="utf-8",
            )
        elif form == "legacy-session":
            manifest.write_text(
                "# Execute-plan session: " + SLUG + "\n"
                "\n"
                "workflow_state: terminal\n"
                f"session_id: {holder}\n"
                "\n"
                "task_boundary: task=1 commit=fixture validation=pass\n",
                encoding="utf-8",
            )
        evidence_file = self.scratch / "phase3-exit-record.md"
        evidence_file.write_text("phase 3 exit: zero blocking\n", encoding="utf-8")
        digest = hashlib.sha256(self.plan.read_bytes()).hexdigest()
        (run_dir / "task-1-implement.log.md").write_text(
            "task 1 implement log\n", encoding="utf-8"
        )
        (run_dir / "runtime_state.json").write_text(
            json.dumps({
                "plan_slug": SLUG,
                "workflow_state": "terminal",
                "tasks": {"1": "complete"},
                "pre_archive_receipt": {
                    "declared_paths": [str(self.plan)],
                    "archived_plan_path": str(
                        self.repo / "docs" / "history" / "plans" / "completed" / PLAN_NAME
                    ),
                    "plan_digest": digest,
                    "evidence": [str(evidence_file)],
                    "recorded_at": "2026-10-23T00:00:00Z",
                },
                "terminal_receipt": {
                    "exit": "phase3-zero-blocking",
                    "recorded_at": "2026-10-23T00:10:00Z",
                },
            }),
            encoding="utf-8",
        )
        provider = self.scratch / "status-provider.sh"
        if status == "terminal":
            body = 'printf \'{"session_id": "%s", "status": "terminal"}\\n\' "$1"\n'
        elif status in ("live", "paused", "unresolved"):
            body = (
                "printf '{\"session_id\": \"%s\", \"status\": \"" + status + "\"}\\n' \"$1\"\n"
            )
        elif status == "slow":
            body = "sleep 12\nprintf '{\"session_id\": \"%s\", \"status\": \"terminal\"}\\n' \"$1\"\n"
        elif status == "malformed":
            body = "printf 'not-json-at-all\\n'\n"
        elif status == "overflow":
            body = (
                "printf '{\"session_id\": \"%s\", \"status\": \"terminal\"}' \"$1\"\n"
                "i=0\nwhile [ \"$i\" -lt 70000 ]; do printf 'x'; i=$((i + 1)); done\n"
                "printf '\\n'\n"
            )
        elif status == "mismatched-id":
            body = 'printf \'{"session_id": "someone-else", "status": "terminal"}\\n\' "$1"\n'
        else:
            body = 'printf \'{"session_id": "%s", "status": "bogus"}\\n\' "$1"\n'
        provider.write_text("#!/bin/sh\n" + body, encoding="utf-8")
        provider.chmod(0o755)
        facts_dir = self.repo / ".ai-playbook"
        facts_dir.mkdir(exist_ok=True)
        with open(facts_dir / "facts.md", "a", encoding="utf-8") as fh:
            fh.write(f'session_status_command = "{provider}"\n')
        return wt, manifest

    def _conversion_take(self, session, branch=None, plan=None, parent=None):
        return self._run(
            "take",
            str(plan or self.plan),
            "--session", session,
            "--branch", branch or self.branch,
            "--worktree-parent", str(parent or self.wt_parent),
            extra_env={
                "CLAUDE_CODE_SESSION_ID": session,
                "EXECUTION_CLAIM_LOCK_HOME": str(self.scratch / "lock-home"),
            },
        )

    def test_restored_worktree_takeover_on_verifiable_same_run_state(self):
        # The registered worktree at the take path carries the canonical
        # run manifest naming the foreign claim's holder and this exact
        # plan, the provider answers the prior owner terminal, and the
        # completed-run boundary holds: the claim converts to the resumer
        # (atomic replacement, no worktree add, no occupant refusal), and
        # the manifest canonicalizes to the resumer's identity.
        wt, manifest = self._conversion_fixture()
        self._seed_claim("session-holder", FRESH_AGE, branch=self.branch)
        prior_created = next(
            line for line in self.claim.read_text(encoding="utf-8").splitlines()
            if line.startswith("created: ")
        )
        proc = self._conversion_take("session-b")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: pass")
        self.assertIn("conversion: claim", proc.stdout)
        self.assertEqual(self._claim_session(), "session-b")
        claim_text = self.claim.read_text(encoding="utf-8")
        # The replacement shape: prior created preserved, branch preserved,
        # updated refreshed; nothing synthesized.
        self.assertIn(prior_created, claim_text)
        self.assertIn(f"branch: {self.branch}", claim_text)
        self.assertIn("session: session-b", claim_text)
        self.assertTrue(
            (self.wt_parent / self.branch).is_dir(), "worktree must be adopted, not recreated"
        )
        # Manifest canonicalized: resumer identity, legacy aliases gone,
        # unrelated content preserved.
        canonical = manifest.read_text(encoding="utf-8")
        self.assertIn("session_id: session-b", canonical)
        self.assertIn(f"plan_path: {self.plan}", canonical)
        self.assertIn(f"run_worktree: {wt}", canonical)
        self.assertIn(f"run_branch: {self.branch}", canonical)
        self.assertNotIn("Session:", canonical)
        self.assertNotIn("Plan:", canonical)
        self.assertIn("workflow_state: terminal", canonical)
        self.assertIn("task_boundary:", canonical)
        # The converted claim survives the exit path (TAKE_OK disarmed the
        # cleanup): a second read after the process exited is the proof.
        self.assertEqual(self._claim_session(), "session-b")

    def test_restored_worktree_refusal_on_unprovable_state(self):
        # No run manifest at the take target (the seeded worktree sits at a
        # different path, so the target is not even registered): the
        # conversion has no context and the historical fresh-foreign
        # refusal judges.
        self._seed_worktree(self.branch, "restored-wt-none")
        (self.wt_parent / self.branch / "docs" / "tmp" / "execute-plan" / SLUG).mkdir(parents=True)
        self._seed_claim("session-holder", FRESH_AGE)
        before = self.claim.read_text(encoding="utf-8")
        proc = self._take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
        self.assertIn("fresh foreign claim", proc.stdout + proc.stderr)
        self.assertEqual(self.claim.read_text(encoding="utf-8"), before)

    def test_conversion_refuses_nonterminal_provider_status(self):
        # The provider answers live: only a terminal prior owner proceeds;
        # the claim is preserved byte-identically.
        self._conversion_fixture(status="live")
        self._seed_claim("session-holder", FRESH_AGE, branch=self.branch)
        before = self.claim.read_text(encoding="utf-8")
        proc = self._conversion_take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
        self.assertIn("prior owner session-holder is live, not terminal", proc.stdout + proc.stderr)
        self.assertIn("live", proc.stdout + proc.stderr)
        self.assertEqual(self.claim.read_text(encoding="utf-8"), before)

    def test_conversion_refuses_without_provider_configuration(self):
        # No session_status_command in the primary facts: the provider
        # refuses and the conversion refuses unchanged (the Ship gate's
        # default: the existing refusal remains active without valid
        # configuration and verified evidence).
        self._conversion_fixture()
        (self.repo / ".ai-playbook" / "facts.md").write_text(
            'tmp_dir = "docs/tmp"\nother_key = "x"\n', encoding="utf-8"
        )
        self._seed_claim("session-holder", FRESH_AGE, branch=self.branch)
        before = self.claim.read_text(encoding="utf-8")
        proc = self._conversion_take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
        self.assertIn("did not return prior owner", proc.stdout + proc.stderr)
        self.assertEqual(self.claim.read_text(encoding="utf-8"), before)

    def test_conversion_refuses_incomplete_run_boundary(self):
        # The runtime state names task 2 in progress: the completed-run
        # boundary refuses and the claim is preserved.
        import json
        wt, manifest = self._conversion_fixture()
        state_path = wt / "run-tmp" / "execute-plan" / SLUG / "runtime_state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["tasks"] = {"1": "complete", "2": "in-progress"}
        state_path.write_text(json.dumps(state), encoding="utf-8")
        self._seed_claim("session-holder", FRESH_AGE, branch=self.branch)
        before = self.claim.read_text(encoding="utf-8")
        proc = self._conversion_take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
        self.assertIn("not in a sanctioned terminal state", proc.stdout + proc.stderr)
        self.assertEqual(self.claim.read_text(encoding="utf-8"), before)

    def test_conversion_refuses_mismatched_plan_digest(self):
        # The receipt's plan_digest does not hash the active plan bytes:
        # refuse unchanged.
        import json
        wt, manifest = self._conversion_fixture()
        state_path = wt / "run-tmp" / "execute-plan" / SLUG / "runtime_state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["pre_archive_receipt"]["plan_digest"] = "0" * 64
        state_path.write_text(json.dumps(state), encoding="utf-8")
        self._seed_claim("session-holder", FRESH_AGE, branch=self.branch)
        proc = self._conversion_take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("does not hash the active plan bytes", proc.stdout + proc.stderr)

    def test_conversion_legacy_full_and_session_forms_convert(self):
        # The two legacy identity forms convert identically: the manifest's
        # legacy aliases are removed on canonicalization and the canonical
        # identity fields are written.
        for form in ("legacy-full", "legacy-session"):
            with self.subTest(form=form):
                wt, manifest = self._conversion_fixture(form=form)
                self._seed_claim("session-holder", FRESH_AGE, branch=self.branch)
                proc = self._conversion_take("session-b")
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                canonical = manifest.read_text(encoding="utf-8")
                self.assertIn("session_id: session-b", canonical)
                self.assertIn(f"plan_path: {self.plan}", canonical)
                self.assertNotIn("Session:", canonical)
                self.assertNotIn("Plan:", canonical)
                # Reset the fixture state the next iteration rebuilds.
                self._git("worktree", "remove", "--force", str(wt))
                self._git("worktree", "prune")
                self._git("branch", "-D", self.branch)
                if self.claim.exists():
                    self.claim.unlink()
                # Restore the facts baseline: the fixture appends the
                # provider line, so a stale duplicate key would refuse the
                # next iteration's provider resolution.
                (self.repo / ".ai-playbook" / "facts.md").write_text(
                    'tmp_dir = "docs/tmp"\n', encoding="utf-8"
                )

    def test_conversion_session_channel_mismatch_refuses(self):
        # The session channel derives a different active id than --session:
        # the trusted-channel boundary refuses before any mutation.
        self._conversion_fixture()
        self._seed_claim("session-holder", FRESH_AGE, branch=self.branch)
        before = self.claim.read_text(encoding="utf-8")
        proc = self._run(
            "take", str(self.plan),
            "--session", "session-b",
            "--branch", self.branch,
            "--worktree-parent", str(self.wt_parent),
            extra_env={
                "CLAUDE_CODE_SESSION_ID": "session-someone-else",
                "EXECUTION_CLAIM_LOCK_HOME": str(self.scratch / "lock-home"),
            },
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("does not equal --session session-b", proc.stdout + proc.stderr)
        self.assertEqual(self.claim.read_text(encoding="utf-8"), before)

    def test_conversion_stale_claim_at_registered_manifest_preserved(self):
        # Stale take preservation: the manifest remains at its registered
        # worktree, but the boundary fails (provider live), so the stale
        # claim is preserved — never taken over by the historical unlink.
        self._conversion_fixture(status="live")
        self._seed_claim("session-holder", STALE_AGE, branch=self.branch)
        before = self.claim.read_text(encoding="utf-8")
        proc = self._conversion_take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
        self.assertEqual(self.claim.read_text(encoding="utf-8"), before)

    def test_sweep_preserves_claim_with_registered_manifest(self):
        # Sweep-side preservation: a spent-looking claim (landed plan, no
        # branch occupant) whose run manifest remains at its registered
        # worktree is skipped untouched, naming the registered worktree.
        wt, manifest = self._conversion_fixture()
        completed = self.repo / "docs" / "history" / "plans" / "completed"
        completed.mkdir(parents=True)
        shutil.copy(self.plan, completed / PLAN_NAME)
        self._seed_claim("session-holder", STALE_AGE, branch="fixture/gone-branch")
        proc = self._run("sweep", "--session", "session-sweeper")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: pass")
        self.assertTrue(self.claim.exists(), "preserved claim was deleted by sweep")
        combined = proc.stdout + proc.stderr
        self.assertIn("run manifest remains at its registered worktree", combined)
        self.assertIn("deleted 0", combined)

    def test_conversion_refuses_symlinked_manifest(self):
        # A symlinked run manifest is never followed: the conversion
        # refuses unchanged, naming the registered worktree and the
        # symlinked manifest path; the claim, the link itself, and the
        # link target's bytes stay untouched.
        wt, manifest = self._conversion_fixture()
        target = self.scratch / "elsewhere-manifest.md"
        target.write_text("not the manifest\n", encoding="utf-8")
        manifest.unlink()
        os.symlink(str(target), str(manifest))
        self._seed_claim("session-holder", STALE_AGE, branch=self.branch)
        before = self.claim.read_text(encoding="utf-8")
        target_before = self._hash_file(target)
        proc = self._conversion_take("session-b")
        self.assertEqual(proc.returncode, 1)
        combined = proc.stdout + proc.stderr
        self.assertIn("registered-manifest scan is inconclusive", combined)
        self.assertIn("symlink", combined)
        # The refusal names the registered worktree and the manifest path
        # in git's stored physical form (the porcelain entry the scan read).
        physical_wt = os.path.realpath(str(wt))
        self.assertIn(physical_wt, combined)
        self.assertIn(
            os.path.join(physical_wt, "run-tmp", "execute-plan", SLUG, "manifest.md"),
            combined,
        )
        self.assertEqual(self.claim.read_text(encoding="utf-8"), before)
        self.assertTrue(manifest.is_symlink())
        self.assertEqual(self._hash_file(target), target_before)

    def test_conversion_refuses_ambiguous_manifests(self):
        # The manifest exists at the take target AND at another registered
        # worktree (two worktrees ran the same slug): the ambiguity
        # preserves the claim for operator reconciliation.
        wt, manifest = self._conversion_fixture()
        other_branch = "fixture/other-branch"
        other = self._seed_worktree(other_branch, os.path.join("wt", other_branch))
        (other / ".ai-playbook").mkdir(exist_ok=True)
        (other / ".ai-playbook" / "facts.md").write_text(
            'tmp_dir = "run-tmp"\n', encoding="utf-8"
        )
        other_run = other / "run-tmp" / "execute-plan" / SLUG
        other_run.mkdir(parents=True)
        (other_run / "manifest.md").write_text(
            f"# Execute-plan session: {SLUG}\n\nSession: session-holder\nPlan: {self.plan}\n",
            encoding="utf-8",
        )
        self._seed_claim("session-holder", STALE_AGE, branch=self.branch)
        before = self.claim.read_text(encoding="utf-8")
        proc = self._conversion_take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("more than one registered worktree", proc.stdout + proc.stderr)
        self.assertEqual(self.claim.read_text(encoding="utf-8"), before)

    def test_conversion_refuses_unusable_worktree_facts_names_cause(self):
        # Registered-worktree facts that are missing, unreadable, or lack
        # the tmp_dir key each make the scan inconclusive naming the
        # worktree and the specific discovery failure, with no guessed
        # manifest path; the claim and manifest bytes stay unchanged.
        def _unlink(path):
            path.unlink()

        def _chmod_zero(path):
            os.chmod(path, 0)

        def _drop_tmp_dir(path):
            path.write_text('other_key = "x"\n', encoding="utf-8")

        for shape, corrupt in (
            ("missing facts", _unlink),
            ("unreadable facts", _chmod_zero),
            ("no tmp_dir", _drop_tmp_dir),
        ):
            with self.subTest(shape=shape):
                if shape == "unreadable facts" and os.geteuid() == 0:
                    self.skipTest("root reads anything")
                wt, manifest = self._conversion_fixture()
                facts = wt / ".ai-playbook" / "facts.md"
                corrupt(facts)
                self._seed_claim("session-holder", FRESH_AGE, branch=self.branch)
                claim_before = self._hash_file(self.claim)
                manifest_before = self._hash_file(manifest)
                proc = self._conversion_take("session-b")
                self.assertEqual(proc.returncode, 1)
                self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
                combined = proc.stdout + proc.stderr
                self.assertIn("registered-manifest scan is inconclusive", combined)
                self.assertIn(shape, combined)
                self.assertIn(os.path.realpath(str(wt)), combined)
                # No guessed fallback path: the worktree's facts-resolved
                # run path is never printed when discovery refused.
                self.assertNotIn(
                    os.path.join(os.path.realpath(str(wt)), "run-tmp"), combined
                )
                self.assertEqual(self._hash_file(self.claim), claim_before)
                self.assertEqual(self._hash_file(manifest), manifest_before)
                # Reset the fixture state the next iteration rebuilds.
                if facts.exists():
                    os.chmod(facts, 0o644)
                self._git("worktree", "remove", "--force", str(wt))
                self._git("worktree", "prune")
                self._git("branch", "-D", self.branch)
                if self.claim.exists():
                    self.claim.unlink()
                # Restore the facts baseline: the fixture appends the
                # provider line, so a stale duplicate key would refuse the
                # next iteration's provider resolution.
                (self.repo / ".ai-playbook" / "facts.md").write_text(
                    'tmp_dir = "docs/tmp"\n', encoding="utf-8"
                )

    def _plant_primary_mirror(self, manifest, *, differing=False):
        """The primary-side mirror: a copy of the canonical registered
        manifest under the primary checkout's matching run path (the
        primary facts resolve tmp_dir to docs/tmp)."""
        mirror_dir = self.repo / "docs" / "tmp" / "execute-plan" / SLUG
        mirror_dir.mkdir(parents=True, exist_ok=True)
        mirror = mirror_dir / "manifest.md"
        if differing:
            mirror.write_text(
                "# Execute-plan session: " + SLUG + "\n\na differing copy\n",
                encoding="utf-8",
            )
        else:
            shutil.copy(manifest, mirror)
        return mirror

    def test_conversion_accepts_byte_identical_primary_mirror(self):
        # A byte-identical copy under the primary checkout's matching run
        # path is the same manifest identity: the scan reports one identity
        # retained at the canonical registered worktree, so the conversion
        # proceeds through it (the mirror copy itself is never rewritten).
        wt, manifest = self._conversion_fixture()
        mirror = self._plant_primary_mirror(manifest)
        self._seed_claim("session-holder", FRESH_AGE, branch=self.branch)
        mirror_before = self._hash_file(mirror)
        proc = self._conversion_take("session-b")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: pass")
        self.assertEqual(self._claim_session(), "session-b")
        self.assertIn("session_id: session-b", manifest.read_text(encoding="utf-8"))
        self.assertEqual(self._hash_file(mirror), mirror_before)

    def test_conversion_refuses_differing_primary_mirror(self):
        # A primary-side copy whose bytes differ from the canonical
        # registered manifest stays ambiguous: the multiple-manifest
        # refusal keeps the claim and all three records byte-for-byte.
        wt, manifest = self._conversion_fixture()
        mirror = self._plant_primary_mirror(manifest, differing=True)
        self._seed_claim("session-holder", FRESH_AGE, branch=self.branch)
        claim_before = self._hash_file(self.claim)
        manifest_before = self._hash_file(manifest)
        mirror_before = self._hash_file(mirror)
        proc = self._conversion_take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("more than one registered worktree", proc.stdout + proc.stderr)
        self.assertEqual(self._hash_file(self.claim), claim_before)
        self.assertEqual(self._hash_file(manifest), manifest_before)
        self.assertEqual(self._hash_file(mirror), mirror_before)

    def test_conversion_refuses_mirror_plus_second_worktree_manifest(self):
        # The mirror collapse admits one primary-side copy beside the
        # canonical manifest, never a third identity: an additional
        # non-primary worktree manifest keeps the multiple refusal and
        # the claim preserved.
        wt, manifest = self._conversion_fixture()
        mirror = self._plant_primary_mirror(manifest)
        other_branch = "fixture/other-branch"
        other = self._seed_worktree(other_branch, os.path.join("wt", other_branch))
        other_run = other / "docs" / "tmp" / "execute-plan" / SLUG
        other_run.mkdir(parents=True)
        (other_run / "manifest.md").write_text("a third identity\n", encoding="utf-8")
        self._seed_claim("session-holder", FRESH_AGE, branch=self.branch)
        claim_before = self._hash_file(self.claim)
        manifest_before = self._hash_file(manifest)
        mirror_before = self._hash_file(mirror)
        proc = self._conversion_take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("more than one registered worktree", proc.stdout + proc.stderr)
        self.assertEqual(self._hash_file(self.claim), claim_before)
        self.assertEqual(self._hash_file(manifest), manifest_before)
        self.assertEqual(self._hash_file(mirror), mirror_before)

    def test_conversion_refuses_two_nonprimary_byte_identical_manifests(self):
        # Two non-primary registered worktrees carrying byte-identical
        # manifests stay multiple: the one admitted collapse requires a
        # primary-side copy (either the current or the retained find at
        # the primary checkout), so with no primary-side manifest the
        # refusal holds and the claim plus both manifests keep their
        # bytes.
        wt, manifest = self._conversion_fixture()
        other_branch = "fixture/other-branch"
        other = self._seed_worktree(other_branch, os.path.join("wt", other_branch))
        other_run = other / "docs" / "tmp" / "execute-plan" / SLUG
        other_run.mkdir(parents=True)
        other_manifest = other_run / "manifest.md"
        shutil.copy(manifest, other_manifest)
        self._seed_claim("session-holder", FRESH_AGE, branch=self.branch)
        claim_before = self._hash_file(self.claim)
        manifest_before = self._hash_file(manifest)
        other_manifest_before = self._hash_file(other_manifest)
        proc = self._conversion_take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("more than one registered worktree", proc.stdout + proc.stderr)
        self.assertEqual(self._hash_file(self.claim), claim_before)
        self.assertEqual(self._hash_file(manifest), manifest_before)
        self.assertEqual(self._hash_file(other_manifest), other_manifest_before)

    def test_sweep_inconclusive_scan_names_worktree_and_cause(self):
        # The stale-sweep skip reason carries the same attribution as the
        # take refusal: a spendable claim (landed plan, branch gone) whose
        # scan is inconclusive is skipped untouched, naming the registered
        # worktree and the discovery cause; the claim bytes stay unchanged.
        for shape in ("missing facts", "unreadable facts", "no tmp_dir", "symlink"):
            with self.subTest(shape=shape):
                if shape == "unreadable facts" and os.geteuid() == 0:
                    self.skipTest("root reads anything")
                wt, manifest = self._conversion_fixture()
                facts = wt / ".ai-playbook" / "facts.md"
                if shape == "missing facts":
                    facts.unlink()
                elif shape == "unreadable facts":
                    os.chmod(facts, 0)
                elif shape == "no tmp_dir":
                    facts.write_text('other_key = "x"\n', encoding="utf-8")
                else:
                    target = self.scratch / "elsewhere-sweep-manifest.md"
                    target.write_text("not the manifest\n", encoding="utf-8")
                    manifest.unlink()
                    os.symlink(str(target), str(manifest))
                completed = self.repo / "docs" / "history" / "plans" / "completed"
                completed.mkdir(parents=True, exist_ok=True)
                shutil.copy(self.plan, completed / PLAN_NAME)
                self._seed_claim("session-holder", STALE_AGE, branch="fixture/gone-branch")
                claim_before = self._hash_file(self.claim)
                manifest_before = self._hash_file(manifest)
                proc = self._run("sweep", "--session", "session-sweeper")
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                combined = proc.stdout + proc.stderr
                self.assertIn("preservation scan inconclusive", combined)
                self.assertIn(shape, combined)
                self.assertIn(os.path.realpath(str(wt)), combined)
                if shape == "symlink":
                    # The symlinked manifest path is named in the reason,
                    # in git's stored physical form (the take-side twin
                    # asserts the same attribution on its refusal).
                    self.assertIn(
                        os.path.join(
                            os.path.realpath(str(wt)),
                            "run-tmp", "execute-plan", SLUG, "manifest.md",
                        ),
                        combined,
                    )
                self.assertTrue(
                    self.claim.exists(), "inconclusive scan let sweep delete the claim"
                )
                self.assertEqual(self._hash_file(self.claim), claim_before)
                self.assertEqual(self._hash_file(manifest), manifest_before)
                # Reset the fixture state the next iteration rebuilds.
                if facts.exists():
                    os.chmod(facts, 0o644)
                self._git("worktree", "remove", "--force", str(wt))
                self._git("worktree", "prune")
                self._git("branch", "-D", self.branch)
                if self.claim.exists():
                    self.claim.unlink()
                (self.repo / ".ai-playbook" / "facts.md").write_text(
                    'tmp_dir = "docs/tmp"\n', encoding="utf-8"
                )

    def test_conversion_refuses_run_base_conflict(self):
        # The manifest's run_base branch token disagrees with the claim's
        # base line: refuse before the replacement.
        wt, manifest = self._conversion_fixture()
        mtext = manifest.read_text(encoding="utf-8")
        manifest.write_text(
            mtext + "run_base: some-other-branch @ 0123456789abcdef\n",
            encoding="utf-8",
        )
        self._seed_claim("session-holder", STALE_AGE, branch=self.branch)
        claim_text = self.claim.read_text(encoding="utf-8")
        self.claim.write_text(claim_text + "base: main\n", encoding="utf-8")
        proc = self._conversion_take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("conflicts with the claim's base", proc.stdout + proc.stderr)

    def test_conversion_refuses_split_owner_state(self):
        # H-claim/R-manifest split owners: the manifest names a different
        # owner than the claim (the interrupted-replacement shape) — the
        # conversion refuses byte-identically without inferring lineage.
        wt, manifest = self._conversion_fixture(holder="session-first")
        self._seed_claim("session-second", STALE_AGE, branch=self.branch)
        before = self.claim.read_text(encoding="utf-8")
        manifest_before = manifest.read_text(encoding="utf-8")
        proc = self._conversion_take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("does not verify against the claim", proc.stdout + proc.stderr)
        self.assertEqual(self.claim.read_text(encoding="utf-8"), before)
        self.assertEqual(manifest.read_text(encoding="utf-8"), manifest_before)

    def test_conversion_refuses_claim_manifest_branch_conflict(self):
        # The manifest's run_branch disagrees with the claim's recorded
        # branch: refuse before the replacement; nothing mutates.
        wt, manifest = self._conversion_fixture()
        self._seed_claim("session-holder", STALE_AGE, branch="fixture/other-branch")
        before = self.claim.read_text(encoding="utf-8")
        proc = self._conversion_take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("conflicts with the claim's branch", proc.stdout + proc.stderr)
        self.assertEqual(self.claim.read_text(encoding="utf-8"), before)

    def test_conversion_refuses_on_slow_provider_timeout(self):
        # A provider exceeding the 10-second bound refuses the conversion
        # unchanged, and both gateway-owned locks are released (a later
        # command's merge-acquire must not see a stranded hold).
        wt, manifest = self._conversion_fixture(status="slow")
        self._seed_claim("session-holder", FRESH_AGE, branch=self.branch)
        before = self.claim.read_text(encoding="utf-8")
        proc = self._conversion_take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
        self.assertIn("did not return prior owner", proc.stdout + proc.stderr)
        self.assertEqual(self.claim.read_text(encoding="utf-8"), before)

    def test_conversion_refuses_malformed_overflow_and_mismatched_provider(self):
        # Malformed JSON, a 64 KiB stream overflow, and a mismatched
        # session id each refuse the conversion unchanged (the provider
        # contract's closed vocabulary; the gateway never proceeds on a
        # response outside the exact shape).
        for status, needle in (
            ("malformed", "not valid JSON"),
            ("overflow", "byte cap"),
            ("mismatched-id", "did not return prior owner"),
        ):
            with self.subTest(status=status):
                wt, manifest = self._conversion_fixture(status=status)
                self._seed_claim("session-holder", FRESH_AGE, branch=self.branch)
                before = self.claim.read_text(encoding="utf-8")
                proc = self._conversion_take("session-b")
                self.assertEqual(proc.returncode, 1)
                self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
                self.assertIn(needle, proc.stdout + proc.stderr)
                self.assertEqual(self.claim.read_text(encoding="utf-8"), before)
                # Reset the fixture state the next iteration rebuilds.
                self._git("worktree", "remove", "--force", str(wt))
                self._git("worktree", "prune")
                self._git("branch", "-D", self.branch)
                if self.claim.exists():
                    self.claim.unlink()
                # Restore the facts baseline: the fixture appends the
                # provider line, so a stale duplicate key would refuse the
                # next iteration's provider resolution.
                (self.repo / ".ai-playbook" / "facts.md").write_text(
                    'tmp_dir = "docs/tmp"\n', encoding="utf-8"
                )

    def test_conversion_r_then_s_second_conversion_succeeds(self):
        # R-to-S: a second conversion on the already-converted run transfers
        # the claim again; the artifacts the first conversion wrote (the
        # manifest's canonical identity block, the old logs) keep their
        # bytes apart from the ownership fields.
        wt, manifest = self._conversion_fixture()
        self._seed_claim("session-holder", FRESH_AGE, branch=self.branch)
        first = self._conversion_take("session-b")
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        manifest_after_first = manifest.read_text(encoding="utf-8")
        run_log = wt / "run-tmp" / "execute-plan" / SLUG / "task-1-implement.log.md"
        log_before = run_log.read_bytes()
        # The claim now names session-b with a fresh updated stamp; make it
        # stale so the second conversion takes the same gated path.
        self._seed_claim("session-b", STALE_AGE, branch=self.branch)
        second = self._conversion_take("session-c")
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual(self._claim_session(), "session-c")
        canonical = manifest.read_text(encoding="utf-8")
        self.assertIn("session_id: session-c", canonical)
        self.assertIn("run_session_id: session-holder", canonical)
        self.assertEqual(run_log.read_bytes(), log_before)

    def test_conversion_same_owner_resumes_through_own_claim_arm(self):
        # The claim and manifest name the invoking session: the verified
        # live same-session resume hands back to the own-claim arm (the
        # adopt-instead-of-recreate refusal keeping the claim), never the
        # conversion.
        wt, manifest = self._conversion_fixture()
        self._seed_claim("session-holder", FRESH_AGE, branch=self.branch)
        proc = self._run(
            "take", str(self.plan),
            "--session", "session-holder",
            "--branch", self.branch,
            "--worktree-parent", str(self.wt_parent),
            extra_env={
                "CLAUDE_CODE_SESSION_ID": "session-holder",
                "EXECUTION_CLAIM_LOCK_HOME": str(self.scratch / "lock-home"),
            },
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("already exists", proc.stdout + proc.stderr)
        self.assertEqual(self._claim_session(), "session-holder")

    def test_conversion_preserves_all_optional_claim_lines(self):
        # The replacement shape: created, branch, start-commit, and base
        # survive; updated refreshes; a later take on another branch still
        # sees the saved branch occupancy.
        wt, manifest = self._conversion_fixture()
        self._seed_claim("session-holder", FRESH_AGE, branch=self.branch)
        text = self.claim.read_text(encoding="utf-8")
        text += "start-commit: 0123456789abcdef0123456789abcdef01234567\nbase: main\n"
        self.claim.write_text(text, encoding="utf-8")
        updated_before = self._updated_stamp()
        proc = self._conversion_take("session-b")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        claim_text = self.claim.read_text(encoding="utf-8")
        self.assertIn("start-commit: 0123456789abcdef0123456789abcdef01234567", claim_text)
        self.assertIn("base: main", claim_text)
        self.assertNotEqual(self._updated_stamp(), updated_before)
        # The saved branch occupancy: the sweep's branch leg still sees the
        # saved branch held by the registered worktree, so the spent-looking
        # claim is skipped whatever the plan's state.
        proc = self._run("sweep", "--session", "session-z")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(self.claim.exists(), "the converted claim was swept")
        combined = proc.stdout + proc.stderr
        self.assertTrue(
            "run manifest remains at its registered worktree" in combined
            or f"branch {self.branch} is held by worktree" in combined,
            f"neither preservation witness fired: {combined}",
        )

    def test_conversion_poisoned_lock_environment_cannot_redirect_roots(self):
        # Poisoned caller HOME and lock-root variables cannot change the
        # roots: the conversion succeeds with decoys set and the decoy
        # directories stay empty (the OS-account/seam derivation wins).
        wt, manifest = self._conversion_fixture()
        decoy = self.scratch / "decoy-home"
        decoy.mkdir()
        self._seed_claim("session-holder", FRESH_AGE, branch=self.branch)
        proc = self._run(
            "take", str(self.plan),
            "--session", "session-b",
            "--branch", self.branch,
            "--worktree-parent", str(self.wt_parent),
            extra_env={
                "CLAUDE_CODE_SESSION_ID": "session-b",
                "EXECUTION_CLAIM_LOCK_HOME": str(self.scratch / "lock-home"),
                "HOME": str(decoy),
                "DONE_LOCK_ROOT": str(decoy / "done-redirect"),
                "MERGE_LOCK_ROOT": str(decoy / "merge-redirect"),
            },
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self._claim_session(), "session-b")
        self.assertFalse(
            (decoy / "done-redirect").exists(), "caller DONE_LOCK_ROOT was honored"
        )
        self.assertFalse(
            (decoy / "merge-redirect").exists(), "caller MERGE_LOCK_ROOT was honored"
        )
        self.assertEqual(list(decoy.iterdir()), [], "caller HOME was used as the lock root")

    def test_merge_lock_contention_refuses_claim_commands_once(self):
        # With a live merge-lock held by another session, each claim
        # command refuses once naming the holder and preserves the claim
        # (the one-shot contention refusal; no second acquire attempt).
        wt = self._seed_worktree(self.branch, os.path.join("wt", self.branch))
        lock_home = self.scratch / "lock-home"
        holder_dir = lock_home / ".ai-playbook" / "locks" / "merge"
        acq = subprocess.run(
            ["env", f"MERGE_LOCK_ROOT={holder_dir}", "bash",
             str(SCRIPT.parent / "done-lock.sh"), "merge-acquire", "--label", "external-holder"],
            cwd=str(self.repo), capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(acq.returncode, 0, acq.stderr)
        lock_dir = ""
        token = ""
        for line in acq.stdout.splitlines():
            if line.startswith("export MERGE_LOCK_DIR="):
                lock_dir = line.split("=", 1)[1]
            if line.startswith("export MERGE_LOCK_TOKEN="):
                token = line.split("=", 1)[1]
        self.assertTrue(lock_dir and token)
        try:
            self._seed_claim("session-a", FRESH_AGE)
            before = self.claim.read_text(encoding="utf-8")
            for mode_args in (
                ("claim", str(self.plan), "--session", "session-b"),
                ("release", str(self.plan), "--session", "session-a"),
                ("sweep", "--session", "session-b"),
                ("refresh", str(self.plan), "--session", "session-a"),
                ("take", str(self.plan), "--session", "session-b",
                 "--branch", "fixture/contended", "--worktree-parent", str(self.scratch / "wt-c")),
            ):
                with self.subTest(mode=mode_args[0]):
                    proc = self._run(
                        *mode_args,
                        extra_env={"EXECUTION_CLAIM_LOCK_HOME": str(lock_home)},
                    )
                    self.assertEqual(proc.returncode, 1)
                    self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
                    self.assertIn("merge-lock is held", proc.stdout + proc.stderr)
            self.assertEqual(self.claim.read_text(encoding="utf-8"), before)
        finally:
            subprocess.run(
                ["env", f"MERGE_LOCK_ROOT={holder_dir}",
                 f"MERGE_LOCK_DIR={lock_dir}", f"MERGE_LOCK_TOKEN={token}",
                 "bash", str(SCRIPT.parent / "done-lock.sh"), "merge-release"],
                cwd=str(self.repo), capture_output=True, text=True, timeout=60,
            )

    def test_restored_worktree_claim_mutation_serialized(self):
        # The compare-and-delete seam: the takeover and release mutations
        # re-verify the claim row's session as the unlink's immediately
        # preceding operation. The fixture states the seam (the grep-plus-rm
        # pair inside takeover_stale_claim and cmd_release): when the claim
        # no longer names the expected holder at that last instant, the
        # mutation aborts and the claim is left untouched.
        self._seed_claim("session-holder", STALE_AGE)
        # race the takeover: rewrite the claim to a third session after the
        # takeover's freshness read but before its compare-and-delete by
        # making the claim file read as session-c at the last instant
        holder_wt = None
        proc = self._take("session-b")
        # the stale claim of session-holder is taken over; the mutation's
        # compare-and-delete passed because the row still named session-holder
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self._claim_session(), "session-b")
        # release's compare-and-delete: a foreign session refuses untouched
        self._seed_claim("session-other", FRESH_AGE)
        proc = self._release("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("names session session-other", proc.stdout + proc.stderr)
        self.assertEqual(self._claim_session(), "session-other")
        del holder_wt

    def test_freshness_boundary_7199s_refuses(self):
        # FRESHNESS_SECS=7200 boundary, refuse side: one second inside the
        # cadence window still refuses (the pinned constant's refuse arm).
        # The freshness clock is pinned through a date shim answering
        # `date -u +%s` with the seed epoch itself, so the boundary is
        # exact: a wall-clock delta between seeding and the script's read
        # cannot push the age over the boundary (the flake this removes).
        # The 7200 twin below is shimmed the same way: its takeover arm
        # reads the identical clock, so its boundary is exact too.
        seed_epoch = 1_700_000_000
        seed_now = datetime.fromtimestamp(seed_epoch, timezone.utc)
        self._seed_claim("session-holder", timedelta(seconds=7199), now=seed_now)
        proc = self._take("session-b", path_prepend=self._date_shim(seed_epoch))
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
        self.assertIn("session-holder", proc.stdout + proc.stderr)
        self.assertFalse((self.wt_parent / self.branch).exists())

    def test_freshness_boundary_7200s_takes_over(self):
        # FRESHNESS_SECS=7200 boundary, takeover side: exactly one cadence
        # period of age is stale and taken over. The same date shim pins
        # the freshness clock at the seed epoch, so the read age is
        # exactly 7200s: the boundary is exact, not merely skew-immune,
        # matching the 7199 refuse side's exactness (the seeded stamp and
        # the script's read are the same pinned instant, so any wall-clock
        # behavior is out of the loop).
        seed_epoch = 1_700_000_000
        seed_now = datetime.fromtimestamp(seed_epoch, timezone.utc)
        self._seed_claim("session-dead", timedelta(seconds=7200), now=seed_now)
        proc = self._take("session-b", path_prepend=self._date_shim(seed_epoch))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: pass")
        self.assertIn("takeover", proc.stdout)
        self.assertIn("session: session-b", self.claim.read_text(encoding="utf-8"))

    def test_take_stale_takeover(self):
        self._seed_claim("session-dead", STALE_AGE)
        proc = self._take("session-b")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: pass")
        self.assertIn("takeover", proc.stdout)
        self.assertIn("session-dead", proc.stdout)
        self.assertIn("session: session-b", self.claim.read_text(encoding="utf-8"))
        self.assertTrue((self.wt_parent / self.branch).is_dir())

    def test_take_stale_claim_with_occupied_worktree(self):
        occupied = self._seed_worktree(self.branch, "dead-wt")
        self._seed_claim("session-dead", STALE_AGE)
        before = self.claim.read_text(encoding="utf-8")
        proc = self._take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
        combined = proc.stdout + proc.stderr
        self.assertIn(str(occupied), combined)
        self.assertIn("adopt", combined)
        self.assertIn("remove", combined)
        # The bounded removal remedy names both removal commands in order
        # (worktree removal, then branch deletion) before the take re-run.
        self.assertIn("git worktree remove --force", combined)
        self.assertIn("git branch -D", combined)
        self.assertLess(
            combined.index("git worktree remove --force"),
            combined.index("git branch -D"),
            "the removal remedy does not order worktree removal before branch deletion",
        )
        self.assertIn("re-run take", combined)
        # The occupant check runs before the takeover arm: the refusal
        # preserves the dead session's claim (destroying it would erase the
        # registry entry the next reader needs) and creates no fresh claim.
        self.assertEqual(
            self.claim.read_text(encoding="utf-8"),
            before,
            "the stale foreign claim was not preserved by the occupant refusal",
        )
        self.assertFalse((self.wt_parent / self.branch).exists())

    def test_take_own_claim_existing_worktree_fails_keeping_claim(self):
        self._seed_claim("session-b", FRESH_AGE)
        target = self.wt_parent / self.branch
        self._git("worktree", "add", "-b", self.branch, str(target))
        before = self.claim.read_text(encoding="utf-8")
        proc = self._take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
        combined = proc.stdout + proc.stderr
        self.assertIn(str(target), combined)
        self.assertEqual(
            self.claim.read_text(encoding="utf-8"), before, "claim was not kept"
        )

    def test_pre_registered_occupant_worktree_survives_failed_take(self):
        # Exit-path probe, different-branch variant: a registered worktree
        # already at the take path whose HEAD is on another branch passes
        # both pre-add guards (the branch-scoped occupant check matches by
        # branch, the own-claim check only runs for own claims), the add
        # fails over the occupied path, and the cleanup's removal arm must
        # not fire: the occupant's registration, directory, and uncommitted
        # changes all survive the failed take.
        self.wt_parent.mkdir()
        occupant = self._seed_worktree(
            "other/holder-branch", self.branch, parent=self.wt_parent
        )
        marker = occupant / "occupant-uncommitted.txt"
        marker.write_text("occupant work in progress", encoding="utf-8")
        proc = self._take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
        combined = proc.stdout + proc.stderr
        self.assertIn("worktree add failed", combined)
        self.assertTrue(
            occupant.is_dir(), "the pre-registered occupant worktree was removed"
        )
        self.assertTrue(
            marker.is_file(), "the occupant's uncommitted changes were destroyed"
        )
        self.assertIn(
            os.path.realpath(occupant),
            self._registered_worktree_paths(),
            "the pre-registered occupant worktree was unregistered",
        )
        self.assertNotIn(
            "cleanup: removed this invocation's half-created worktree", combined
        )
        self.assertFalse(
            self._git_ok("rev-parse", "--verify", "-q", "refs/heads/" + self.branch),
            "the failed add's collateral branch was not rolled back",
        )
        self.assertFalse(self.claim.exists(), "fresh claim not deleted after failure")

    def test_pre_registered_detached_worktree_survives_failed_take(self):
        # Exit-path probe, detached variant: the same survival contract over
        # an occupant registered detached (no branch entry at all in the
        # porcelain listing, so no branch-scoped guard can see it either).
        self.wt_parent.mkdir()
        occupant = self.wt_parent / self.branch
        self._git("worktree", "add", "--detach", str(occupant))
        marker = occupant / "occupant-uncommitted.txt"
        marker.write_text("occupant work in progress", encoding="utf-8")
        proc = self._take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
        combined = proc.stdout + proc.stderr
        self.assertIn("worktree add failed", combined)
        self.assertTrue(
            occupant.is_dir(), "the pre-registered detached worktree was removed"
        )
        self.assertTrue(
            marker.is_file(), "the occupant's uncommitted changes were destroyed"
        )
        self.assertIn(
            os.path.realpath(occupant),
            self._registered_worktree_paths(),
            "the pre-registered detached worktree was unregistered",
        )
        self.assertNotIn(
            "cleanup: removed this invocation's half-created worktree", combined
        )
        self.assertFalse(
            self._git_ok("rev-parse", "--verify", "-q", "refs/heads/" + self.branch),
            "the failed add's collateral branch was not rolled back",
        )
        self.assertFalse(self.claim.exists(), "fresh claim not deleted after failure")

    def test_failed_create_cleans_fresh_claim(self):
        self._git("branch", self.branch)
        proc = self._take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
        combined = proc.stdout + proc.stderr
        self.assertIn("already exists", combined)
        self.assertFalse(self.claim.exists(), "fresh claim not deleted after failure")
        self.assertFalse((self.wt_parent / self.branch).exists())
        # The rollback never touches a branch that pre-existed the add: the
        # seeded branch (not this add's creation) must survive the failure.
        self.assertTrue(
            self._git_ok("rev-parse", "--verify", "-q", "refs/heads/" + self.branch),
            "a pre-existing branch was deleted by the failed take",
        )

    def test_failed_add_rolls_back_stranded_branch_and_retry_succeeds(self):
        # `git worktree add -b` creates the branch before validating the
        # path: a path-collision failure strands the freshly created branch,
        # and every later take of that branch name would fail until a manual
        # delete. The add-failure arm rolls the stranded branch back (only
        # when it did not exist before this add), so the retry succeeds once
        # the path collision is freed.
        target = self.wt_parent / self.branch
        target.mkdir(parents=True)
        (target / "collision").write_text("not a worktree", encoding="utf-8")
        proc = self._take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
        combined = proc.stdout + proc.stderr
        self.assertIn("worktree add failed", combined)
        self.assertIn(
            "cleanup: removed this invocation's stranded branch", combined
        )
        self.assertFalse(
            self._git_ok("rev-parse", "--verify", "-q", "refs/heads/" + self.branch),
            "the stranded branch was not rolled back",
        )
        self.assertFalse(self.claim.exists(), "fresh claim not deleted after failure")
        # The unregistered collision directory is not the cleanup's to
        # remove (its worktree arm only ever removes registered worktrees).
        self.assertTrue(target.is_dir(), "the collision directory was removed")
        # Retry with the collision freed: the take now succeeds.
        shutil.rmtree(target)
        proc = self._take("session-b")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: pass")
        self.assertTrue(target.is_dir(), "worktree missing after the retry take")
        self.assertTrue(self.claim.is_file(), "claim missing after the retry take")

    # -- exit-path cleanup (the trap) ------------------------------------- #

    def test_take_uncreatable_worktree_parent_cleans_fresh_claim(self):
        # The worktree parent path is an existing regular file, so the
        # parent creation fails after the claim was created; the take must
        # still leave no claim behind (tool_error, claim absent).
        blocker = self.scratch / "wt-parent-blocker"
        blocker.write_text("a file, not a directory", encoding="utf-8")
        proc = self._take("session-b", parent=blocker)
        self.assertEqual(proc.returncode, 3)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: tool_error")
        combined = proc.stdout + proc.stderr
        self.assertIn("worktree parent not creatable", combined)
        self.assertIn("cleanup: removed this invocation's fresh claim", combined)
        self.assertFalse(
            self.claim.exists(),
            "fresh claim stranded by the worktree-parent failure",
        )

    def test_take_sigint_after_claim_creation_cleans_fresh_claim(self):
        self._take_signalled_at_fresh_claim(signal.SIGINT, 130)

    def test_take_sigterm_after_claim_creation_cleans_fresh_claim(self):
        self._take_signalled_at_fresh_claim(signal.SIGTERM, 143)

    def test_signal_with_foreign_session_claim_keeps_claim_cleans_worktree(self):
        # Owner-check witness on the exit-path cleanup: the claim file is
        # tampered to name a FOREIGN session after this invocation created
        # it, then the parked add is signalled. The cleanup's owner check
        # must leave the foreign-named claim untouched (the owner check
        # keeps a claim naming another session from being deleted), while
        # the worktree arm still cleans the half-created worktree and the
        # stranded branch (its witness gates read the pre-add witnesses,
        # not the claim's owner field).
        unblock = self.scratch / "unblock-git-add"
        registered = self.scratch / "git-add-registered"
        proc = self._take_popen("session-b", unblock)
        try:
            deadline = time.monotonic() + 30
            while not self.claim.exists():
                if proc.poll() is not None or time.monotonic() > deadline:
                    self.fail(
                        "the claim never appeared; the script exited or "
                        f"stalled before parking (rc={proc.poll()})"
                    )
                time.sleep(0.01)
            while not registered.exists():
                if proc.poll() is not None or time.monotonic() > deadline:
                    self.fail(
                        "the worktree add never went in flight over a "
                        "registered worktree; the script exited or stalled "
                        f"after the claim (rc={proc.poll()})"
                    )
                time.sleep(0.01)
            before = self.claim.read_text(encoding="utf-8")
            tampered = before.replace(
                "session: session-b", "session: session-foreign", 1
            )
            self.assertNotEqual(tampered, before, "the session tamper was a no-op")
            self.claim.write_text(tampered, encoding="utf-8")
            os.killpg(proc.pid, signal.SIGINT)
            unblock.write_text("go", encoding="utf-8")
            out, err = proc.communicate(timeout=60)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.communicate()
        self.assertEqual(proc.returncode, 130)
        combined = out + err
        # The foreign-named claim survives byte-identical: the owner check
        # kept the cleanup's rm off it.
        self.assertTrue(
            self.claim.exists(),
            "the cleanup deleted a claim naming a foreign session",
        )
        self.assertEqual(
            self.claim.read_text(encoding="utf-8"),
            tampered,
            "the foreign-named claim was modified by the cleanup",
        )
        self.assertNotIn(
            "cleanup: removed this invocation's fresh claim", combined,
            "the cleanup claimed ownership of a foreign-named claim",
        )
        # The worktree arm still cleans, independent of the claim's owner.
        self.assertIn(
            "cleanup: removed this invocation's half-created worktree", combined,
            "the worktree arm did not clean although no occupant shields the path",
        )
        self.assertFalse(
            (self.wt_parent / self.branch).exists(),
            "a half-created worktree survived the signal",
        )
        registered_list = subprocess.run(
            ["git", "-C", str(self.repo), "worktree", "list", "--porcelain"],
            check=True, capture_output=True, text=True, timeout=60,
        ).stdout
        self.assertNotIn(
            str(self.wt_parent / self.branch), registered_list,
            "the worktree stayed registered after the signal",
        )
        self.assertFalse(
            self._git_ok("rev-parse", "--verify", "-q", "refs/heads/" + self.branch),
            "the branch the in-flight add created survived the signal",
        )

    def test_post_acquire_occupant_refusal_over_empty_claims_dir(self):
        # The post-acquire arm of the branch-occupant refusal over an empty
        # claims directory: no claim anywhere, a registered worktree holding
        # the requested branch. The fresh claim this invocation created is
        # cleaned up by the refusal itself, named by the same cleanup line
        # the exit-path trap prints, and no worktree is created.
        self.wt_parent.mkdir()
        occupied = self._seed_worktree(self.branch, "occupied-wt", parent=self.wt_parent)
        proc = self._take("session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
        combined = proc.stdout + proc.stderr
        self.assertIn(str(occupied), combined)
        self.assertIn("cleanup: removed this invocation's fresh claim", combined)
        # The post-acquire arm prints the same bounded removal remedy; pin
        # its copy so the twin refusal sites cannot silently diverge.
        self.assertIn("bounded removal remedy", combined)
        self.assertIn("git worktree remove --force", combined)
        self.assertIn("git branch -D", combined)
        self.assertIn("re-run take", combined)
        self.assertFalse(
            self.claim.exists(), "fresh claim survived the occupant refusal"
        )
        self.assertFalse((self.wt_parent / self.branch).exists())

    # -- release -------------------------------------------------------- #

    def test_release_ownership_fence(self):
        self._seed_claim("session-holder", FRESH_AGE)
        before = self.claim.read_text(encoding="utf-8")
        proc = self._run("release", str(self.plan), "--session", "session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
        self.assertEqual(self.claim.read_text(encoding="utf-8"), before)

        proc = self._run("release", str(self.plan), "--session", "session-holder")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: pass")
        self.assertFalse(self.claim.exists())

        proc = self._run("release", str(self.plan), "--session", "session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
        combined = proc.stdout + proc.stderr
        self.assertIn(str(self.claim), combined)

    # -- sweep ------------------------------------------------------------ #

    def _sweep(self, session="session-sweeper"):
        return self._run("sweep", "--session", session)

    def test_sweep_deletes_landed_plan_claim_without_worktree(self):
        # The completed-archive landing leg: the plan file exists under the
        # plans root's completed/ archive and the recorded branch resolves
        # to no worktree, so the claim cannot be a live peer and the sweep
        # deletes it; the scan itself ends pass.
        completed = self.repo / "docs" / "history" / "plans" / "completed"
        completed.mkdir(parents=True)
        (completed / PLAN_NAME).write_text("# archived plan\n", encoding="utf-8")
        self._seed_claim("session-dead", STALE_AGE, branch=self.branch)
        proc = self._sweep()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: pass")
        self.assertIn(f"sweep: deleted {self._physical_claim()}", proc.stdout)
        self.assertIn(f"branch {self.branch} holds no worktree", proc.stdout)
        self.assertFalse(self.claim.exists(), "the spent claim survived the sweep")

    def test_sweep_skips_live_claim_with_resolving_worktree(self):
        # The fail-closed leg: the plan is unlanded (absent from the plans
        # root, no landing commit names the slug) and the recorded branch is
        # held by a registered worktree; the claim is skipped untouched with
        # a one-line reason naming the occupying worktree.
        live_wt = self._seed_worktree(self.branch, "live-wt")
        self._seed_claim("session-live", FRESH_AGE, branch=self.branch)
        before = self.claim.read_text(encoding="utf-8")
        proc = self._sweep()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: pass")
        self.assertIn(f"sweep: skipped {self._physical_claim()}:", proc.stdout)
        self.assertIn(os.path.realpath(live_wt), proc.stdout)
        self.assertEqual(
            self.claim.read_text(encoding="utf-8"),
            before,
            "the live claim was modified by the sweep",
        )

    def test_sweep_deletes_gone_worktree_claim_landed_via_main_history(self):
        # The main-history landing leg: the plan is absent from the plans
        # root, a landing-shaped commit subject ("check: land ...") on the
        # primary checkout's current branch (the sweep's main-history
        # resolution when no facts key or origin HEAD exists) names the
        # claim's slug as a hyphen-bounded segment, and the branch holds no
        # worktree: the claim is deleted.
        self._git(
            "commit", "--allow-empty", "-q", "-m",
            f"check: land {SLUG} (sweep witness landing)",
        )
        self._seed_claim("session-dead", STALE_AGE, branch=self.branch)
        proc = self._sweep()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: pass")
        self.assertIn(f"sweep: deleted {self._physical_claim()}", proc.stdout)
        self.assertFalse(self.claim.exists(), "the spent claim survived the sweep")

    def test_sweep_skips_plan_parked_under_plans_root_despite_landing_subject(self):
        # The parked-plan guard: the plan's file sits under the plans root
        # outside completed/ (the deferred/ park) while a landing subject on
        # the main-history branch names the slug. A parked plan is not a
        # landing, so the claim is skipped untouched even though the branch
        # holds no worktree (the regression the history leg's earlier reach
        # allowed: a parked plan read as landed through its slug's subject).
        deferred = self.repo / "docs" / "history" / "plans" / "deferred"
        deferred.mkdir(parents=True)
        (deferred / PLAN_NAME).write_text("# deferred plan\n", encoding="utf-8")
        self._git(
            "commit", "--allow-empty", "-q", "-m",
            f"check: land {SLUG} (sweep witness landing)",
        )
        self._seed_claim("session-dead", STALE_AGE, branch=self.branch)
        before = self.claim.read_text(encoding="utf-8")
        proc = self._sweep()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: pass")
        self.assertIn(f"sweep: skipped {self._physical_claim()}:", proc.stdout)
        self.assertIn("not in the completed/ archive", proc.stdout)
        self.assertEqual(
            self.claim.read_text(encoding="utf-8"),
            before,
            "the parked-plan claim was modified by the sweep",
        )

    def test_sweep_absolute_plans_dir_fact_is_not_double_prefixed(self):
        # The plans-dir fact guard: an absolute plans_dir value in the
        # scratch facts document is used as the plans root itself, never
        # joined onto the primary checkout root (the double prefix would
        # miss the completed/ archive and misjudge the landedness leg into
        # a skip on a landed claim).
        plans_root = self.repo / "docs" / "history" / "plans"
        completed = plans_root / "completed"
        completed.mkdir(parents=True)
        (completed / PLAN_NAME).write_text("# archived plan\n", encoding="utf-8")
        facts_dir = self.repo / ".ai-playbook"
        facts_dir.mkdir(exist_ok=True)
        (facts_dir / "facts.md").write_text(
            "```toml\n"
            f'plans_dir = "{plans_root}"\n'
            'tmp_dir = "docs/tmp"\n'
            "```\n",
            encoding="utf-8",
        )
        self._seed_claim("session-dead", STALE_AGE, branch=self.branch)
        proc = self._sweep()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: pass")
        self.assertIn(f"sweep: deleted {self._physical_claim()}", proc.stdout)
        self.assertFalse(self.claim.exists(), "the spent claim survived the sweep")

    # -- refresh -------------------------------------------------------- #

    def test_refresh_restamps_recreates_and_fences(self):
        self._seed_claim("session-b", STALE_AGE)
        before = self.claim.read_text(encoding="utf-8")
        created_before = [
            line for line in before.splitlines() if line.startswith("created: ")
        ][0]
        proc = self._run(
            "refresh", str(self.plan), "--session", "session-b", "--base", "main"
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: pass")
        after = self.claim.read_text(encoding="utf-8")
        self.assertNotEqual(after, before)
        self.assertIn("base: main", after)
        self.assertIn(created_before, after)
        stamp = self._updated_stamp()
        parsed = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        age = (datetime.now(timezone.utc) - parsed).total_seconds()
        self.assertLess(age, 300, "refresh did not re-stamp updated: to now")

        self.claim.unlink()
        proc = self._run("refresh", str(self.plan), "--session", "session-b")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(self.claim.is_file(), "refresh did not recreate the claim")
        recreated = self.claim.read_text(encoding="utf-8")
        self.assertIn("session: session-b", recreated)
        self.assertNotIn("base:", recreated)

        self._seed_claim("session-holder", FRESH_AGE)
        before = self.claim.read_text(encoding="utf-8")
        proc = self._run("refresh", str(self.plan), "--session", "session-b")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
        self.assertEqual(self.claim.read_text(encoding="utf-8"), before)

    # -- race-retry witnesses (the shared claim retry gate, plan
    # 2026-10-13-machinery-script-refactor-program, Task 3) ---------------- #

    def test_take_permanently_contended_claims_dir_fails_after_third_attempt(self):
        # Witness A, acquire_claim's loop: a permanently contended claims
        # directory (the dangling symlink at the claim path) makes every
        # noclobber create lose deterministically and root-proofly, so the
        # loop burns attempts one through three and the ceiling fires with
        # the racing tool error and the tool-error exit; the take creates
        # nothing and the contender survives untouched.
        self._plant_dangling_symlink_at_claim()
        proc = self._take("session-b")
        self.assertEqual(proc.returncode, 3)
        self.assertEqual(
            proc.stdout.strip().splitlines()[-1], "OUTCOME: tool_error"
        )
        combined = proc.stdout + proc.stderr
        self.assertIn(
            f"error: claims directory kept racing at {self._physical_claim()}; "
            "re-derive the state from disk",
            combined,
        )
        self.assertNotIn("cleanup:", combined)
        self.assertTrue(
            os.path.islink(str(self.claim)), "the planted contender did not survive"
        )
        self.assertFalse((self.wt_parent / self.branch).exists())
        self.assertFalse(
            self._git_ok("rev-parse", "--verify", "-q", "refs/heads/" + self.branch),
            "the contended take stranded a branch",
        )

    def test_refresh_permanently_contended_claims_dir_fails_after_third_attempt(self):
        # Witness A, cmd_refresh's loop: the same contended fixture against
        # the recreate loop; the ceiling fires with the identical error
        # text and exit class, and the contender survives untouched.
        self._plant_dangling_symlink_at_claim()
        proc = self._run("refresh", str(self.plan), "--session", "session-b")
        self.assertEqual(proc.returncode, 3)
        self.assertEqual(
            proc.stdout.strip().splitlines()[-1], "OUTCOME: tool_error"
        )
        self.assertIn(
            f"error: claims directory kept racing at {self._physical_claim()}; "
            "re-derive the state from disk",
            proc.stdout + proc.stderr,
        )
        self.assertTrue(
            os.path.islink(str(self.claim)), "the planted contender did not survive"
        )

    def test_take_lost_then_won_succeeds_on_attempt_two_cold_start_shape(self):
        # Witness B, acquire_claim's loop: the contender (the date shim)
        # loses the first create and releases before the second, so the
        # take wins on attempt 2. The evidence is the cold-start shape:
        # the same claim and worktree lines, no takeover, no cleanup, no
        # arm-3 markers, the winning create carrying a delegated real
        # stamp, and the plant recorded exactly once.
        shim_bin, marker = self._lost_then_won_date_shim()
        proc = self._take("session-b", path_prepend=shim_bin)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: pass")
        self.assertTrue(marker.is_file(), "the contender never planted its loss")
        combined = proc.stdout + proc.stderr
        self.assertNotIn("kept racing", combined)
        self.assertNotIn("takeover", combined)
        self.assertNotIn("cleanup:", combined)
        self.assertNotIn("arm-3", combined)
        self.assertIn(
            f"claim: {self._physical_claim()} (session: session-b, slug: {SLUG})",
            proc.stdout,
        )
        self.assertIn(
            f"worktree: {self.wt_parent / self.branch} (branch: {self.branch})",
            proc.stdout,
        )
        self.assertTrue(self.claim.is_file())
        self.assertEqual(self._claim_session(), "session-b")
        self.assertRegex(
            self.claim.read_text(encoding="utf-8"),
            r"created: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",
        )
        self.assertTrue((self.wt_parent / self.branch).is_dir())

    def test_take_lost_then_won_sets_cold_start_cleanup_flags(self):
        # Witness B's flag half: the attempt-2 win must leave the state the
        # cleanup and exit traps consume exactly as a cold start sets it
        # (the claim is this invocation's own fresh claim, no arm-3
        # resume). A take whose worktree add fails after the attempt-2
        # create refuses with the cold-start fresh-claim cleanup line,
        # never the arm-3 keep line, and leaves no claim behind.
        shim_bin, _marker = self._lost_then_won_date_shim()
        target = self.wt_parent / self.branch
        target.mkdir(parents=True)
        (target / "collision").write_text("not a worktree", encoding="utf-8")
        proc = self._take("session-b", path_prepend=shim_bin)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
        combined = proc.stdout + proc.stderr
        self.assertIn("worktree add failed", combined)
        self.assertIn("cleanup: removed this invocation's fresh claim", combined)
        self.assertNotIn("arm-3", combined)
        self.assertFalse(self.claim.exists(), "the attempt-2 claim was not cleaned")

    def test_refresh_lost_then_won_succeeds_on_attempt_two(self):
        # Witness B, cmd_refresh's loop: the recreate loses the first
        # create to the planted link and wins the second after the shim
        # releases; the recreate evidence line is the cold recreate shape
        # and the claim names this session.
        shim_bin, marker = self._lost_then_won_date_shim()
        proc = self._run(
            "refresh", str(self.plan), "--session", "session-b",
            path_prepend=shim_bin,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: pass")
        self.assertTrue(marker.is_file(), "the contender never planted its loss")
        self.assertIn("recreated:", proc.stdout)
        self.assertNotIn("kept racing", proc.stdout + proc.stderr)
        self.assertNotIn("refresh refused", proc.stdout + proc.stderr)
        self.assertEqual(self._claim_session(), "session-b")

    # -- claim mode ------------------------------------------------------ #

    def test_claim_mode_creates_without_worktree(self):
        proc = self._run(*self._claim_args("session-b"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: pass")
        self.assertTrue(self.claim.is_file())
        self.assertFalse(
            (self.wt_parent / self.branch).exists(),
            "claim mode created a worktree directory",
        )

        self.claim.unlink()
        self._seed_claim("session-holder", FRESH_AGE)
        proc = self._run(*self._claim_args("session-b"))
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: fail")
        combined = proc.stdout + proc.stderr
        self.assertIn("session-holder", combined)
        self.assertRegex(combined, r"claim age: \d+s \(updated: ")
        self.assertIn("override", combined)

    # -- recorded branch and start commit (plan
    # 2026-10-13-execute-plan-company-task-branch, Task 2) ---------------- #
    # Script tests cover the claim file only: the branch-mismatch
    # stand-down is placement-arm behavior with no script witness.

    def _start_commit_sha(self) -> str:
        self._git("commit", "--allow-empty", "-q", "-m", "start commit")
        return self._git_out("rev-parse", "HEAD")

    def test_claim_records_branch_and_start_commit_lines(self):
        expected_sha = self._start_commit_sha()
        # The operand is HEAD, not the sha: resolution is discriminated by
        # requiring the recorded value to be the full 40-hex sha HEAD
        # resolves to, never the operand form or an abbreviation.
        self.assertRegex(expected_sha, r"^[0-9a-f]{40}$")
        proc = self._run(
            "claim", str(self.plan),
            "--session", "session-b",
            "--branch", self.branch,
            "--start-commit", "HEAD",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: pass")
        claim_text = self.claim.read_text(encoding="utf-8")
        self.assertIn(f"branch: {self.branch}", claim_text)
        # The recorded value is the resolved sha, not the operand form.
        self.assertIn(f"start-commit: {expected_sha}", claim_text)

    def test_claim_unresolvable_start_commit_is_usage_refusal_writing_nothing(self):
        proc = self._run(
            "claim", str(self.plan),
            "--session", "session-b",
            "--branch", self.branch,
            "--start-commit", "not-a-commit",
        )
        # Usage violations are tool errors per the argparse-override
        # precedent: exit 3, usage text, error, and the final OUTCOME line
        # all on stderr, stdout empty, and no claim written anywhere.
        self.assertEqual(proc.returncode, 3)
        self.assertEqual(proc.stdout, "")
        self.assertEqual(proc.stderr.strip().splitlines()[-1], "OUTCOME: tool_error")
        self.assertIn("Usage: execution_claim.sh", proc.stderr)
        self.assertIn("start-commit", proc.stderr)
        self.assertFalse(
            self.claim.exists(),
            "a claim was written despite the unresolvable start commit",
        )

    def test_refresh_preserves_branch_and_start_commit(self):
        # Refresh carries neither --branch nor --start-commit: the recorded
        # identity lines survive the re-stamp untouched.
        start_sha = self._start_commit_sha()
        proc = self._run(
            "claim", str(self.plan),
            "--session", "session-b",
            "--branch", self.branch,
            "--start-commit", start_sha,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        before = self.claim.read_text(encoding="utf-8")
        self.assertIn(f"branch: {self.branch}", before)
        self.assertIn(f"start-commit: {start_sha}", before)
        proc = self._run("refresh", str(self.plan), "--session", "session-b")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        after = self.claim.read_text(encoding="utf-8")
        self.assertIn(f"branch: {self.branch}", after)
        self.assertIn(f"start-commit: {start_sha}", after)

    def test_claim_takeover_rebuild_carries_branch_and_start_commit(self):
        # The takeover rebuild path (create_claim_noclobber) must carry the
        # recorded identity: a takeover never silently drops it.
        start_sha = self._start_commit_sha()
        self._seed_claim("session-dead", STALE_AGE)
        proc = self._run(
            "claim", str(self.plan),
            "--session", "session-b",
            "--branch", self.branch,
            "--start-commit", start_sha,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("takeover", proc.stdout)
        claim_text = self.claim.read_text(encoding="utf-8")
        self.assertIn("session: session-b", claim_text)
        self.assertIn(f"branch: {self.branch}", claim_text)
        self.assertIn(f"start-commit: {start_sha}", claim_text)

    def test_refresh_recreate_carries_branch_and_start_commit(self):
        # The refresh recreate path (the same create_claim_noclobber write)
        # carries both lines from the recreating invocation's values.
        start_sha = self._start_commit_sha()
        proc = self._run(
            "claim", str(self.plan),
            "--session", "session-b",
            "--branch", self.branch,
            "--start-commit", start_sha,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.claim.unlink()
        proc = self._run(
            "refresh", str(self.plan), "--session", "session-b",
            "--branch", self.branch,
            "--start-commit", start_sha,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        recreated = self.claim.read_text(encoding="utf-8")
        self.assertIn(f"branch: {self.branch}", recreated)
        self.assertIn(f"start-commit: {start_sha}", recreated)

    # -- slug derivation -------------------------------------------------- #

    def test_slug_derived_through_sot(self):
        upper_plan = self.scratch / UPPER_PLAN_NAME
        upper_plan.write_text("# Fixture\n", encoding="utf-8")
        proc = self._run(*self._claim_args("session-b", plan=upper_plan))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        expected = self.claims_dir / f"{CANONICAL_SLUG}.md"
        self.assertTrue(
            expected.is_file(),
            f"claim filename is not the canonical artifact slug: "
            f"expected {expected.name} at {expected}",
        )

    # -- tool error -------------------------------------------------------- #

    def test_missing_primary_checkout_tool_error(self):
        nonrepo = self.scratch / "not-a-repo"
        nonrepo.mkdir()
        proc = self._take("session-b", cwd=nonrepo)
        self.assertEqual(proc.returncode, 3)
        self.assertEqual(self._outcome_line(proc), "OUTCOME: tool_error")

    def test_slug_refusal_dies_in_parent_shell_with_tool_error(self):
        # A plan whose canonical slug derivation refuses dies in the parent
        # shell: exit 3 with the final OUTCOME line on stdout (the
        # environment-failure routing), and no claim written anywhere.
        bad_plan = self.scratch / "2026-09-01-Underscore_story.md"
        bad_plan.write_text("# Fixture\n", encoding="utf-8")
        proc = self._take("session-b", plan=bad_plan)
        self.assertEqual(proc.returncode, 3)
        self.assertEqual(
            proc.stdout.strip().splitlines()[-1], "OUTCOME: tool_error"
        )
        self.assertIn("artifact slug derivation failed", proc.stderr)
        self.assertFalse(
            self.claim.exists(), "a claim was written despite the slug refusal"
        )

    def test_claim_missing_session_line_dies_with_tool_error_in_all_modes(self):
        # A readable claim carrying no session: line is an unsupported
        # record shape: take, refresh, and release all die in the parent
        # shell with exit 3 and a final OUTCOME line on stdout, and the
        # malformed claim is left untouched throughout.
        self.claims_dir.mkdir(parents=True, exist_ok=True)
        self.claim.write_text(
            f"plan: {self.plan}\ncreated: 2026-10-07T00:00:00Z\n",
            encoding="utf-8",
        )
        before = self.claim.read_text(encoding="utf-8")

        proc = self._take("session-b")
        self.assertEqual(proc.returncode, 3)
        self.assertEqual(
            proc.stdout.strip().splitlines()[-1], "OUTCOME: tool_error"
        )
        self.assertIn("no session: line", proc.stdout + proc.stderr)
        self.assertFalse((self.wt_parent / self.branch).exists())

        proc = self._run("refresh", str(self.plan), "--session", "session-b")
        self.assertEqual(proc.returncode, 3)
        self.assertEqual(
            proc.stdout.strip().splitlines()[-1], "OUTCOME: tool_error"
        )

        proc = self._run("release", str(self.plan), "--session", "session-b")
        self.assertEqual(proc.returncode, 3)
        self.assertEqual(
            proc.stdout.strip().splitlines()[-1], "OUTCOME: tool_error"
        )
        self.assertEqual(
            self.claim.read_text(encoding="utf-8"),
            before,
            "the malformed claim was modified",
        )

    # -- usage contract -------------------------------------------------- #

    def test_usage_violation_exits_3_with_usage_text_on_stderr(self):
        # Usage violations are tool errors per the argparse-override
        # precedent: exit 3, the usage text, the error, and the final
        # OUTCOME line all on stderr (stdout stays empty so a classified
        # consumer never reads a stdout OUTCOME line twice).
        proc = self._run("take")  # no plan operand
        self.assertEqual(proc.returncode, 3)
        self.assertEqual(proc.stdout, "")
        self.assertEqual(proc.stderr.strip().splitlines()[-1], "OUTCOME: tool_error")
        self.assertIn("Usage: execution_claim.sh", proc.stderr)
        self.assertIn("error:", proc.stderr)

        proc = self._run("bogus", str(self.plan))  # unknown mode
        self.assertEqual(proc.returncode, 3)
        self.assertEqual(proc.stdout, "")
        self.assertEqual(proc.stderr.strip().splitlines()[-1], "OUTCOME: tool_error")
        self.assertIn("Usage: execution_claim.sh", proc.stderr)

    def test_help_is_metadata_exit_without_outcome_line(self):
        proc = self._run("--help")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Usage: execution_claim.sh", proc.stdout)
        self.assertNotIn("OUTCOME:", proc.stdout)
        self.assertNotIn("OUTCOME:", proc.stderr)


if __name__ == "__main__":
    unittest.main()
