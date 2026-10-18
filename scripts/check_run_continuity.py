#!/usr/bin/env python3
"""Per-boundary run-continuity probe (plan 2026-10-06-worktree-continuity-probe).

At every task boundary the orchestrator runs the ``check`` subcommand over
the run's recorded identity (the Phase 0 worktree root and run branch) and
reads the outcome contract. A fail stops the boundary into the existing
repair arms (re-transfer inputs from the primary checkout, re-capture or
skip-record the baseline) instead of letting mid-run state loss surface at
closeout.

Six checks, one line each (``<name>: pass <evidence>`` /
``<name>: fail <observed evidence>`` / ``<name>: skipped``):

- linked      The repo at --repo is a linked worktree: ``git rev-parse
              --git-dir`` and ``git rev-parse --git-common-dir`` resolve to
              different paths; equal paths fail.
- registered  The worktree's realpath appears in ``git worktree list
              --porcelain`` output, enumerated from the resolved common dir.
              Git always lists the probed repository itself as the main
              (first) entry, so the main entry never counts as a
              registration: only a linked (non-main) entry witnesses a
              registration, which is what makes a standalone clone - a valid
              repository linked nowhere - fail here too.
- branch      The worktree's current branch equals the recorded --branch; a
              mismatch fails naming the observed branch.
- facts       The facts file exists (--facts; default
              .ai-playbook/facts.md under --repo).
- reviews     The reviews directory exists (--reviews; default resolved from
              the facts file's TOML-fenced ``reviews_dir`` key via
              facts_paths.resolve_toml_key_raw, the single TOML-fence
              parser, anchored at the facts file's grandparent so the
              default <repo>/.ai-playbook/facts.md layout reads exactly the
              probed file; relative values anchor at --repo).
- baseline    In --manifest-dir (default docs/tmp under --repo),
              closeout-baseline.json exists, or closeout-baseline-skip.json
              exists (the baseline-less closeout arm's skip sibling passes
              the check); neither fails.

Outcome contract (scripts/OUTCOME_CONTRACT.md):

- any check fail -> exit 1, ``OUTCOME: fail``, all six check lines reported;
- a git plumbing failure over an EXISTING checkout (a worktree whose
  registration was pruned while its ``.git`` gitfile remains, a corrupt
  gitfile) -> exit 2, ``OUTCOME: indeterminate``, evidence naming the
  invalid gitfile; per-check lines are suppressed there (uncertainty
  dominates). A plumbing failure over a path that is not a checkout at all
  (no ``.git`` entry) is not this class: that is a tool error;
- usage errors (missing --branch, a nonexistent --repo path) -> exit 3,
  ``OUTCOME: tool_error``;
- --skip-worktree-checks (primary placement) reports linked, registered, and
  branch as ``skipped``; the facts, reviews, and baseline checks stay
  enforced.

Stdlib only.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import facts_paths

CHECK_NAMES = ("linked", "registered", "branch", "facts", "reviews", "baseline")
WORKTREE_CHECK_NAMES = ("linked", "registered", "branch")
BASELINE_FILENAME = "closeout-baseline.json"
BASELINE_SKIP_FILENAME = "closeout-baseline-skip.json"
DEFAULT_FACTS_RELPATH = Path(".ai-playbook") / "facts.md"
DEFAULT_MANIFEST_RELPATH = Path("docs") / "tmp"
REVIEWS_FACTS_KEY = "reviews_dir"


class ToolError(Exception):
    """Usage, environment, or not-a-checkout failure: exit 3, tool_error."""


class Indeterminate(Exception):
    """Git plumbing failure over an existing checkout: exit 2 with evidence."""

    def __init__(self, evidence: list[str]):
        super().__init__("; ".join(evidence))
        self.evidence = evidence


class OutcomeArgumentParser(argparse.ArgumentParser):
    """argparse override per the outcome contract's usage rule: a usage
    violation is a tool error, so ``error()`` prints the message on stderr
    plus a final ``OUTCOME: tool_error`` row on stdout and exits 3;
    ``--help`` stays a metadata exit (usage text only, no OUTCOME row)."""

    def error(self, message: str) -> None:  # type: ignore[override]
        print(f"check_run_continuity: {message}", file=sys.stderr)
        print("OUTCOME: tool_error")
        raise SystemExit(3)


def _plumbing_failure(repo: Path, args: list[str] | tuple, stderr: str) -> Indeterminate:
    """Classify a git plumbing failure over the probed path.

    A path carrying no ``.git`` entry at all is not a checkout: that is the
    tool-error class (the probe's unheld operating-context assumption),
    raised here so the failure is never read as a domain finding. An
    EXISTING checkout whose plumbing still fails (a worktree whose
    registration was pruned while its ``.git`` gitfile remains, a corrupt
    gitfile) is indeterminate, and the evidence names the invalid gitfile:
    git's own stderr (whose not-a-repository message carries the resolved
    gitdir path) plus, when the checkout carries a ``.git`` gitfile, the
    gitdir pointer it holds.
    """
    git_entry = repo / ".git"
    if not (git_entry.exists() or git_entry.is_symlink()):
        raise ToolError(f"--repo is not a git checkout (no .git entry): {repo}")
    first = stderr.strip().splitlines()[0] if stderr.strip() else "git exited nonzero"
    evidence = [
        f"indeterminate: git plumbing failed over an existing checkout at {repo} "
        f"(git {' '.join(args)}): {first}"
    ]
    if git_entry.is_file():
        target = ""
        try:
            for line in git_entry.read_text(encoding="utf-8").splitlines():
                if line.startswith("gitdir:"):
                    target = line[len("gitdir:"):].strip()
                    break
        except OSError:
            target = ""
        if target:
            evidence.append(
                f"indeterminate: worktree gitfile {git_entry} points to invalid or "
                f"missing gitdir {target}"
            )
        else:
            evidence.append(
                f"indeterminate: worktree gitfile {git_entry} carries no gitdir pointer"
            )
    return Indeterminate(evidence)


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise _plumbing_failure(repo, args, proc.stderr)
    return proc.stdout


def _resolve_under(repo: Path, value: str) -> Path:
    """Resolve a git path output (possibly relative to the repo) to a realpath."""
    path = Path(value.strip())
    if not path.is_absolute():
        path = repo / path
    return path.resolve()


def _linked_line(repo: Path) -> str:
    git_dir = _resolve_under(repo, _git(repo, "rev-parse", "--git-dir"))
    common_dir = _resolve_under(repo, _git(repo, "rev-parse", "--git-common-dir"))
    if git_dir == common_dir:
        return f"linked: fail git-dir equals common-dir ({git_dir})"
    return f"linked: pass git-dir {git_dir} differs from common-dir {common_dir}"


def _registered_line(repo: Path) -> str:
    listing = _git(repo, "worktree", "list", "--porcelain")
    entries = [
        Path(line[len("worktree "):].strip())
        for line in listing.splitlines()
        if line.startswith("worktree ")
    ]
    repo_real = repo.resolve()
    # The first entry is always the main worktree: every repository lists
    # itself, so only non-main entries witness a linked registration.
    linked_entries = entries[1:]
    if any(entry.resolve() == repo_real for entry in linked_entries):
        return f"registered: pass {repo_real} registered in the worktree list"
    main = entries[0].resolve() if entries else None
    return (
        f"registered: fail {repo_real} absent as a linked worktree "
        f"(main worktree: {main})"
    )


def _branch_line(repo: Path, recorded: str) -> str:
    observed = _git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip()
    if observed == recorded:
        return f"branch: pass observed {observed} matches recorded {recorded}"
    return f"branch: fail observed {observed} does not match recorded {recorded}"


def _facts_path(repo: Path, facts_arg: str | None) -> Path:
    if facts_arg:
        return Path(facts_arg)
    return repo / DEFAULT_FACTS_RELPATH


def _facts_line(facts_path: Path) -> str:
    if facts_path.is_file():
        return f"facts: pass {facts_path}"
    return f"facts: fail missing facts file {facts_path}"


def _reviews_line(repo: Path, reviews_arg: str | None, facts_path: Path) -> str:
    if reviews_arg:
        reviews = Path(reviews_arg)
    else:
        # facts_paths.resolve_toml_key_raw is the SINGLE parser for the
        # TOML-fence format (its own declaration): it anchors at a directory
        # and reads that directory's .ai-playbook/facts.md, scoped to the
        # FIRST ```toml fence. Anchoring at the facts file's grandparent
        # reads exactly the probed facts file under the default
        # <repo>/.ai-playbook/facts.md layout; a --facts path outside that
        # layout falls back to the grandparent's own facts file and fails
        # closed when the key is unresolvable there.
        raw = facts_paths.resolve_toml_key_raw(
            facts_path.parent.parent, REVIEWS_FACTS_KEY
        )
        if raw is None or not raw.strip():
            return (
                f"reviews: fail cannot resolve {REVIEWS_FACTS_KEY} from {facts_path}"
            )
        reviews = Path(raw).expanduser()
        if not reviews.is_absolute():
            reviews = repo / reviews
    if reviews.is_dir():
        return f"reviews: pass {reviews}"
    return f"reviews: fail missing reviews directory {reviews}"


def _manifest_dir(repo: Path, manifest_arg: str | None) -> Path:
    if manifest_arg:
        return Path(manifest_arg)
    return repo / DEFAULT_MANIFEST_RELPATH


def _baseline_line(manifest_dir: Path) -> str:
    baseline = manifest_dir / BASELINE_FILENAME
    skip = manifest_dir / BASELINE_SKIP_FILENAME
    if baseline.is_file():
        return f"baseline: pass {baseline}"
    if skip.is_file():
        return f"baseline: pass skip sibling {skip}"
    return (
        f"baseline: fail neither {BASELINE_FILENAME} nor {BASELINE_SKIP_FILENAME} "
        f"present in {manifest_dir}"
    )


def cmd_check(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    if not repo.is_dir():
        raise ToolError(f"--repo path does not exist: {repo}")
    try:
        lines: list[str] = []
        if args.skip_worktree_checks:
            lines.extend(f"{name}: skipped" for name in WORKTREE_CHECK_NAMES)
        else:
            lines.append(_linked_line(repo))
            lines.append(_registered_line(repo))
            lines.append(_branch_line(repo, args.branch))
        facts_path = _facts_path(repo, args.facts)
        lines.append(_facts_line(facts_path))
        lines.append(_reviews_line(repo, args.reviews, facts_path))
        lines.append(_baseline_line(_manifest_dir(repo, args.manifest_dir)))
    except Indeterminate as exc:
        for line in exc.evidence:
            print(line)
        print("OUTCOME: indeterminate")
        return 2
    for line in lines:
        print(line)
    failed = any(": fail" in line for line in lines)
    print("OUTCOME: fail" if failed else "OUTCOME: pass")
    return 1 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = OutcomeArgumentParser(
        description="Per-boundary run-continuity probe over a run's recorded identity."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser(
        "check", help="Probe the run worktree, branch, inputs, and baseline."
    )
    check.add_argument("--repo", required=True, help="The run worktree root (an existing checkout).")
    check.add_argument("--branch", required=True, help="The recorded run branch.")
    check.add_argument(
        "--facts",
        default=None,
        help="Facts file path (default .ai-playbook/facts.md under --repo).",
    )
    check.add_argument(
        "--reviews",
        default=None,
        help="Reviews directory path (default resolved from the facts file's reviews_dir).",
    )
    check.add_argument(
        "--manifest-dir",
        default=None,
        help="Directory holding the closeout baseline (default docs/tmp under --repo).",
    )
    check.add_argument(
        "--skip-worktree-checks",
        action="store_true",
        help="Primary placement: report the three worktree checks as skipped.",
    )
    check.set_defaults(func=cmd_check)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ToolError as exc:
        print(f"check_run_continuity: {exc}", file=sys.stderr)
        print("OUTCOME: tool_error")
        return 3
    except Exception as exc:  # an unexpected internal failure is a tool error, never a silent pass
        print(
            f"check_run_continuity: unexpected failure: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        print("OUTCOME: tool_error")
        return 3


if __name__ == "__main__":
    sys.exit(main())
