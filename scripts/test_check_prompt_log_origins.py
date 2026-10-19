#!/usr/bin/env python3
"""Fixture suite for the prompt-log origin checker.

Every test drives the real script through subprocess against a fixture
log written into a temporary directory, never by importing the script's
helpers, so the CLI contract (report lines and exit codes) is the tested
surface. Fixtures mirror the tracked log's section shape: an entry-
template fence in the header, then one ``## <slug>`` section per entry
with its ``Origins:`` list. Origins are cited in the corpus style
(``docs/history/backlog/<name>.md``) while the fixture files sit beside
the fixture log, exercising the checker's basename resolution.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "check_prompt_log_origins.py"
LOG_REL = "docs/history/backlog/PLAN-PROMPTS.md"
EXEC_LOG_REL = "docs/history/backlog/EXEC-PROMPTS.md"

TEMPLATE_FENCE = """\
Entry template (one section per entry):

```
## <short-slug>

Added: <date and provenance>

Origins:
- docs/history/backlog/<origin>.md

Urgency: <judgment>

Prompt: <full ready-to-dispatch authoring prompt payload>

Rejected alternatives:
- <one line per rejected alternative, with the reason>
```
"""


def write_origin(tmp_path: Path, name: str, status_line: str | None) -> None:
    """A fixture origin file beside the fixture log; the status line is
    the file's first ``Status:`` line verbatim when given."""
    text = "# fixture origin\n"
    if status_line is not None:
        text += f"\n{status_line}\n"
    (tmp_path / name).write_text(text, encoding="utf-8")


def log_text(sections: list[str]) -> str:
    """The fixture log's full text: header, entry-template fence, then
    the sections verbatim."""
    return "Tracked rolling log fixture.\n\n" + TEMPLATE_FENCE + "\n".join(sections)


def log_text_with_ledger(sections: list[str], receipts: list[str]) -> str:
    """The fixture log's full text with a receipt ledger block in the
    header, mirroring the tracked log's shape (receipt lines before the
    entry-template fence)."""
    header = "".join(f"{line}\n" for line in receipts)
    return (
        "Tracked rolling log fixture.\n\n"
        + header
        + "\n"
        + TEMPLATE_FENCE
        + "\n".join(sections)
    )


def write_log(tmp_path: Path, sections: list[str]) -> Path:
    log = tmp_path / "PLAN-PROMPTS.md"
    log.write_text(log_text(sections), encoding="utf-8")
    return log


def entry(slug: str, origins: list[str], frozen_line: str | None = None) -> str:
    lines = [f"## {slug}", ""]
    if frozen_line is not None:
        lines += [frozen_line, ""]
    lines += [
        "Added: fixture provenance",
        "",
        "Origins:",
    ]
    lines += [f"- docs/history/backlog/{name}" for name in origins]
    lines += [
        "",
        "Urgency: fixture",
        "",
        "Prompt: fixture payload",
        "",
        "Rejected alternatives:",
        "- none",
        "",
    ]
    return "\n".join(lines)


def run_checker(log: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(log)],
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_prompt_log_origins_flags_done_origin(tmp_path):
    write_origin(tmp_path, "2026-10-01-done-origin.md", "Status: done")
    log = write_log(tmp_path, [entry("solo-entry", ["2026-10-01-done-origin.md"])])
    proc = run_checker(log)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "SERVED: solo-entry -> 2026-10-01-done-origin.md [done]" in proc.stdout
    assert "STALE: solo-entry" in proc.stdout
    assert "LIVE" not in proc.stdout


def test_prompt_log_origins_flags_covered_origin(tmp_path):
    write_origin(
        tmp_path,
        "2026-10-01-covered-origin.md",
        "- **Status:** covered (docs/history/plans/fixture-plan.md)",
    )
    log = write_log(
        tmp_path, [entry("solo-entry", ["2026-10-01-covered-origin.md"])]
    )
    proc = run_checker(log)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert (
        "SERVED: solo-entry -> 2026-10-01-covered-origin.md "
        "[covered (docs/history/plans/fixture-plan.md)]"
    ) in proc.stdout
    assert "STALE: solo-entry" in proc.stdout


def test_prompt_log_origins_flags_missing_origin(tmp_path):
    log = write_log(tmp_path, [entry("solo-entry", ["2026-10-01-nowhere.md"])])
    proc = run_checker(log)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "LIVE: solo-entry -> 2026-10-01-nowhere.md" in proc.stdout
    assert "SERVED" not in proc.stdout
    assert "STALE" not in proc.stdout


def test_prompt_log_origins_skips_template_block(tmp_path):
    write_origin(tmp_path, "2026-10-01-live-origin.md", "Status: open")
    log = write_log(tmp_path, [entry("real-entry", ["2026-10-01-live-origin.md"])])
    proc = run_checker(log)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    # The fenced template placeholders never parse as an entry.
    assert "<short-slug>" not in proc.stdout
    assert "<origin>.md" not in proc.stdout
    assert "LIVE: real-entry -> 2026-10-01-live-origin.md" in proc.stdout


def test_prompt_log_origins_clean_log_exits_zero(tmp_path):
    write_origin(tmp_path, "2026-10-01-live-origin.md", "Status: open")
    log = write_log(
        tmp_path,
        [
            entry("first-entry", ["2026-10-01-live-origin.md"]),
            entry("second-entry", ["2026-10-01-other-live.md"]),
        ],
    )
    write_origin(tmp_path, "2026-10-01-other-live.md", "Status: in review")
    proc = run_checker(log)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "STALE" not in proc.stdout
    assert "LIVE: first-entry -> 2026-10-01-live-origin.md" in proc.stdout
    assert "LIVE: second-entry -> 2026-10-01-other-live.md" in proc.stdout


def test_prompt_log_origins_frozen_entry_still_checked(tmp_path):
    write_origin(tmp_path, "2026-10-01-served-origin.md", "Status: done")
    log = write_log(
        tmp_path,
        [
            entry(
                "frozen-entry",
                ["2026-10-01-served-origin.md"],
                frozen_line=(
                    "- Frozen: fixture witness, 2026-10-01, authoring claim fixture"
                ),
            )
        ],
    )
    proc = run_checker(log)
    # A frozen entry whose origins are all served is exactly the wedge:
    # the freeze rule itself already orders its prune.
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "STALE: frozen-entry" in proc.stdout


def test_prompt_log_origins_mixed_entry_stays(tmp_path):
    write_origin(tmp_path, "2026-10-01-done-origin.md", "Status: done")
    archive = tmp_path / "completed"
    archive.mkdir()
    (archive / "2026-10-01-archived-origin.md").write_text(
        "# fixture origin moved to the archive\n", encoding="utf-8"
    )
    write_origin(tmp_path, "2026-10-01-live-origin.md", "Status: open")
    log = write_log(
        tmp_path,
        [
            entry(
                "mixed-entry",
                [
                    "2026-10-01-done-origin.md",
                    "2026-10-01-archived-origin.md",
                    "2026-10-01-live-origin.md",
                ],
            )
        ],
    )
    proc = run_checker(log)
    # A mixed entry is dispatchable and stays: exit 0, no STALE verdict.
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "SERVED: mixed-entry -> 2026-10-01-done-origin.md [done]" in proc.stdout
    assert (
        "SERVED: mixed-entry -> 2026-10-01-archived-origin.md "
        "[completed/2026-10-01-archived-origin.md]"
    ) in proc.stdout
    assert "LIVE: mixed-entry -> 2026-10-01-live-origin.md" in proc.stdout
    assert "STALE" not in proc.stdout


def test_prompt_log_origins_deferred_only_entry_stays_open(tmp_path):
    deferred_dir = tmp_path / "deferred"
    deferred_dir.mkdir()
    (deferred_dir / "2026-10-01-deferred-origin.md").write_text(
        "# fixture origin moved to the deferred archive\n", encoding="utf-8"
    )
    log = write_log(
        tmp_path, [entry("deferred-entry", ["2026-10-01-deferred-origin.md"])]
    )
    proc = run_checker(log)
    # A deferral is still-actionable work: the entry stays open, its only
    # origin prints as its own DEFERRED line class, never SERVED, and the
    # all-served staleness predicate never fires on it.
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (
        "DEFERRED: deferred-entry -> 2026-10-01-deferred-origin.md "
        "[deferred/2026-10-01-deferred-origin.md (still actionable:"
        " deferred is neither completed nor rejected)]"
    ) in proc.stdout
    assert "still actionable" in proc.stdout
    assert "SERVED" not in proc.stdout
    assert "STALE" not in proc.stdout


def test_prompt_log_origins_mixed_deferred_and_live_stays_open(tmp_path):
    deferred_dir = tmp_path / "deferred"
    deferred_dir.mkdir()
    (deferred_dir / "2026-10-01-deferred-origin.md").write_text(
        "# fixture origin moved to the deferred archive\n", encoding="utf-8"
    )
    write_origin(tmp_path, "2026-10-01-live-origin.md", "Status: open")
    log = write_log(
        tmp_path,
        [
            entry(
                "mixed-deferred",
                [
                    "2026-10-01-deferred-origin.md",
                    "2026-10-01-live-origin.md",
                ],
            )
        ],
    )
    proc = run_checker(log)
    # An entry split between a deferred and a live origin carries
    # unlanded work on both counts: it stays open with both lines.
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (
        "DEFERRED: mixed-deferred -> 2026-10-01-deferred-origin.md "
        "[deferred/2026-10-01-deferred-origin.md (still actionable:"
        " deferred is neither completed nor rejected)]"
    ) in proc.stdout
    assert "LIVE: mixed-deferred -> 2026-10-01-live-origin.md" in proc.stdout
    assert "STALE" not in proc.stdout


def test_prompt_log_origins_completed_hit_wins_over_deferred_twin(tmp_path):
    archive = tmp_path / "completed"
    archive.mkdir()
    (archive / "2026-10-01-twin-state-origin.md").write_text(
        "# fixture origin completed\n", encoding="utf-8"
    )
    deferred_dir = tmp_path / "deferred"
    deferred_dir.mkdir()
    (deferred_dir / "2026-10-01-twin-state-origin.md").write_text(
        "# fixture origin deferred twin\n", encoding="utf-8"
    )
    log = write_log(
        tmp_path, [entry("twin-entry", ["2026-10-01-twin-state-origin.md"])]
    )
    proc = run_checker(log)
    # The same basename present in both archive states classifies served
    # via the completed hit: the served pair keeps its precedence over the
    # deferred lookup (sorted first-match determinism included).
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert (
        "SERVED: twin-entry -> 2026-10-01-twin-state-origin.md "
        "[completed/2026-10-01-twin-state-origin.md]"
    ) in proc.stdout
    assert "DEFERRED" not in proc.stdout
    assert "STALE: twin-entry" in proc.stdout


class TestPromptLogPruneAudit:
    """The ``--prune-audit --base <ref>`` mode: every removal from the
    prompt log in base..HEAD is classified against its plan-file witness
    at the removal commit's tree.

    Each test drives the real script through subprocess against a scratch
    git repository (identity plumbed explicitly per commit) while the
    checker subprocess itself runs from the suite's own cwd, so the
    mode's run-from-anywhere promise is exercised: the audit must resolve
    the repository from the log path, never from the caller's working
    directory. The venv pytest runner is the canonical invocation; bare
    ``python3`` on this file executes nothing (no runner below).
    """

    def git(self, repo: Path, *args: str) -> str:
        proc = subprocess.run(
            ["git", *args], cwd=repo, capture_output=True, text=True, timeout=60
        )
        assert proc.returncode == 0, f"git {args}: {proc.stderr}"
        return proc.stdout

    def write(self, repo: Path, rel: str, text: str) -> None:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self, repo: Path, message: str) -> str:
        self.git(repo, "add", "-A")
        self.git(
            repo,
            "-c",
            "user.name=Prune Audit Fixture",
            "-c",
            "user.email=prune-audit-fixture@example.test",
            "commit",
            "-m",
            message,
        )
        return self.git(repo, "rev-parse", "HEAD").strip()

    def init_repo_with_log(
        self, repo: Path, sections: list[str], message: str
    ) -> str:
        self.git(repo, "-c", "init.defaultBranch=main", "init")
        self.write(repo, LOG_REL, log_text(sections))
        return self.commit(repo, message)

    def audit(self, log_path: Path, base: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--prune-audit",
                "--base",
                base,
                str(log_path),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

    def final_line(self, proc: subprocess.CompletedProcess) -> str:
        lines = proc.stdout.strip().splitlines()
        assert lines, proc.stdout + proc.stderr
        return lines[-1]

    def test_witnessed_bulk_removal_is_flagged(self, tmp_path):
        repo = tmp_path
        self.init_repo_with_log(
            repo,
            [
                entry("self-own", ["2026-10-01-self-origin.md"]),
                entry("live-entry", ["2026-10-01-live-origin.md"]),
            ],
            "seed the log with two entries",
        )
        base = self.git(repo, "rev-parse", "HEAD").strip()
        # The re-derived 3032e750 shape: one commit removes both entries
        # while landing a plan file whose basename witnesses self-own only.
        witness_name = "2026-10-05-self-own.md"
        self.write(repo, f"docs/history/plans/{witness_name}", "# fixture plan\n")
        self.write(repo, LOG_REL, log_text([]))
        self.commit(repo, "prune both entries, land the self-own plan")
        short = self.git(repo, "rev-parse", "--short", "HEAD").strip()
        proc = self.audit(repo / LOG_REL, base)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert (
            f"PRUNE-OK: self-own -> docs/history/plans/{witness_name}" in proc.stdout
        )
        assert (
            "REMOVED-WITHOUT-WITNESS: live-entry"
            f" (commit {short} prune both entries, land the self-own plan)"
            in proc.stdout
        )
        assert self.final_line(proc) == "OUTCOME: fail"

    def test_clean_self_prune_passes(self, tmp_path):
        repo = tmp_path
        self.init_repo_with_log(
            repo, [entry("solo-prune", ["2026-10-01-solo-origin.md"])], "seed the log"
        )
        base = self.git(repo, "rev-parse", "HEAD").strip()
        # The re-derived e81381d6 shape: the plan file lands in the same
        # commit that deletes the entry.
        witness_name = "2026-10-05-solo-prune.md"
        self.write(repo, f"docs/history/plans/{witness_name}", "# fixture plan\n")
        self.write(repo, LOG_REL, log_text([]))
        self.commit(repo, "land the solo-prune plan and prune its entry")
        proc = self.audit(repo / LOG_REL, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert (
            f"PRUNE-OK: solo-prune -> docs/history/plans/{witness_name}"
            in proc.stdout
        )
        assert "REMOVED-WITHOUT-WITNESS" not in proc.stdout
        assert self.final_line(proc) == "OUTCOME: pass"

    def test_archived_twin_witness_passes(self, tmp_path):
        repo = tmp_path
        witness_name = "2026-10-05-twin-prune.md"
        self.init_repo_with_log(
            repo, [entry("twin-prune", ["2026-10-01-twin-origin.md"])], "seed the log"
        )
        self.write(repo, f"docs/history/plans/{witness_name}", "# fixture plan\n")
        self.commit(repo, "land the twin-prune plan at the plans root")
        base = self.git(repo, "rev-parse", "HEAD").strip()
        # The execution-landing rider shape: the archive move and the entry
        # deletion land as riders of the same commit, so the removal
        # commit's tree carries the plan only under completed/.
        (repo / "docs/history/plans/completed").mkdir()
        self.git(
            repo,
            "mv",
            f"docs/history/plans/{witness_name}",
            f"docs/history/plans/completed/{witness_name}",
        )
        self.write(repo, LOG_REL, log_text([]))
        self.commit(repo, "execute twin-prune: archive the plan, prune its entry")
        proc = self.audit(repo / LOG_REL, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert (
            "PRUNE-OK: twin-prune -> "
            f"docs/history/plans/completed/{witness_name}" in proc.stdout
        )
        assert "REMOVED-WITHOUT-WITNESS" not in proc.stdout
        assert self.final_line(proc) == "OUTCOME: pass"

    def test_directory_charter_witness_passes_and_fails_closed(self, tmp_path):
        repo = tmp_path
        self.init_repo_with_log(
            repo,
            [
                entry("dir-prune", ["2026-10-01-dir-origin.md"]),
                entry("twin-dir", ["2026-10-01-twin-origin.md"]),
                entry("flagged-entry", ["2026-10-01-flagged-origin.md"]),
            ],
            "seed the log with three entries",
        )
        base = self.git(repo, "rev-parse", "HEAD").strip()
        # Removal one (the plan-directory-shape plan, Task 4): the landed
        # plan is a directory; the charter path
        # docs/history/plans/<slug>/PLAN.md witnesses at the plans-root
        # depth (5 path parts, keyed on the slug directory name).
        self.write(
            repo,
            "docs/history/plans/2026-10-05-dir-prune/PLAN.md",
            "# fixture charter\n",
        )
        self.write(
            repo,
            LOG_REL,
            log_text(
                [
                    entry("twin-dir", ["2026-10-01-twin-origin.md"]),
                    entry("flagged-entry", ["2026-10-01-flagged-origin.md"]),
                ]
            ),
        )
        self.commit(repo, "land the dir-prune directory plan, prune its entry")
        # Removal two: the completed/ archive twin is a directory; the
        # charter witnesses one part deeper (6 path parts).
        self.write(
            repo,
            "docs/history/plans/completed/2026-10-05-twin-dir/PLAN.md",
            "# fixture charter\n",
        )
        self.write(
            repo,
            LOG_REL,
            log_text([entry("flagged-entry", ["2026-10-01-flagged-origin.md"])]),
        )
        self.commit(repo, "archive the twin-dir directory plan, prune its entry")
        # Removal three: neither the file form nor the charter form at the
        # plans root -> the audit still fails closed.
        self.write(repo, LOG_REL, log_text([]))
        self.commit(repo, "prune flagged-entry without any witness")
        proc = self.audit(repo / LOG_REL, base)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert (
            "PRUNE-OK: dir-prune -> docs/history/plans/2026-10-05-dir-prune/PLAN.md"
            in proc.stdout
        )
        assert (
            "PRUNE-OK: twin-dir -> docs/history/plans/completed/2026-10-05-twin-dir/PLAN.md"
            in proc.stdout
        )
        assert "REMOVED-WITHOUT-WITNESS: flagged-entry" in proc.stdout
        assert self.final_line(proc) == "OUTCOME: fail"

    def test_superseding_merge_is_reported_not_flagged(self, tmp_path):
        repo = tmp_path
        self.init_repo_with_log(
            repo,
            [
                entry("merge-left", ["2026-10-01-left-origin.md"]),
                entry("merge-right", ["2026-10-01-right-origin.md"]),
            ],
            "seed the log with two entries",
        )
        base = self.git(repo, "rev-parse", "HEAD").strip()
        # The re-derived 94e38903 shape: two removals and one grouped
        # addition in the same edit, no plan file involved.
        self.write(
            repo,
            LOG_REL,
            log_text(
                [
                    entry(
                        "merge-grouped",
                        [
                            "2026-10-01-left-origin.md",
                            "2026-10-01-right-origin.md",
                        ],
                    )
                ]
            ),
        )
        head = self.commit(repo, "merge the two dispatch entries into one")
        short = self.git(repo, "rev-parse", "--short", head).strip()
        proc = self.audit(repo / LOG_REL, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert f"SUPERSEDED-IN-COMMIT: merge-left (commit {short})" in proc.stdout
        assert f"SUPERSEDED-IN-COMMIT: merge-right (commit {short})" in proc.stdout
        assert "REMOVED-WITHOUT-WITNESS" not in proc.stdout
        assert self.final_line(proc) == "OUTCOME: pass"

    def test_segment_match_rejects_substring_slug(self, tmp_path):
        repo = tmp_path
        self.init_repo_with_log(
            repo,
            [
                entry("gap", ["2026-10-01-gap-origin.md"]),
                entry("segment-ok", ["2026-10-01-segment-origin.md"]),
            ],
            "seed the log with two entries",
        )
        base = self.git(repo, "rev-parse", "HEAD").strip()
        # Removal one: the only same-tree candidate embeds the slug inside
        # a longer hyphen-bounded segment (livenessgap), so no segment of
        # the basename equals the slug.
        self.write(
            repo, "docs/history/plans/2026-10-04-livenessgap.md", "# fixture plan\n"
        )
        self.write(
            repo, LOG_REL, log_text([entry("segment-ok", ["2026-10-01-segment-origin.md"])])
        )
        self.commit(repo, "prune gap against a substring-only plan file")
        # Removal two: a true segment match passes.
        self.write(
            repo, "docs/history/plans/2026-10-05-segment-ok.md", "# fixture plan\n"
        )
        self.write(repo, LOG_REL, log_text([]))
        self.commit(repo, "prune segment-ok against a true segment match")
        proc = self.audit(repo / LOG_REL, base)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert "REMOVED-WITHOUT-WITNESS: gap (commit" in proc.stdout
        assert (
            "PRUNE-OK: segment-ok -> docs/history/plans/2026-10-05-segment-ok.md"
            in proc.stdout
        )
        assert self.final_line(proc) == "OUTCOME: fail"

    def test_slug_longer_than_basename_never_matches(self, tmp_path):
        repo = tmp_path
        slug = "authoring-round-liveness-gap-extra"
        self.init_repo_with_log(
            repo, [entry(slug, ["2026-10-01-extra-origin.md"])], "seed the log"
        )
        base = self.git(repo, "rev-parse", "HEAD").strip()
        # The origin-named-entry vs shorter-plan-file-name direction: the
        # slug's segment run (five) is longer than every basename's
        # segment run (four), so no window can match.
        self.write(repo, "docs/history/plans/2026-10-04-gap.md", "# fixture plan\n")
        self.write(repo, LOG_REL, log_text([]))
        self.commit(repo, "prune the long-slug entry against a shorter plan file")
        proc = self.audit(repo / LOG_REL, base)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert (
            f"REMOVED-WITHOUT-WITNESS: {slug} (commit" in proc.stdout
        )
        assert "PRUNE-OK" not in proc.stdout
        assert self.final_line(proc) == "OUTCOME: fail"

    def test_template_fence_never_parses_as_removal(self, tmp_path):
        repo = tmp_path
        seeded = log_text([entry("real-entry", ["2026-10-01-live-origin.md"])])
        self.init_repo_with_log(repo, [entry("real-entry", ["2026-10-01-live-origin.md"])], "seed the log")
        base = self.git(repo, "rev-parse", "HEAD").strip()
        # An edit strictly inside the entry-template fence: the deleted
        # ``## <short-slug>`` placeholder is a heading-shaped line, but it
        # sits inside the fence on both sides.
        renamed = seeded.replace("## <short-slug>", "## <renamed-placeholder>")
        assert renamed != seeded
        self.write(repo, LOG_REL, renamed)
        self.commit(repo, "rename the template placeholder inside the fence")
        proc = self.audit(repo / LOG_REL, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "REMOVED-WITHOUT-WITNESS" not in proc.stdout
        assert "SUPERSEDED-IN-COMMIT" not in proc.stdout
        assert "PRUNE-OK" not in proc.stdout
        assert (
            "0 removals (0 by log ledger) across 1 log-touching commit(s)"
            in proc.stdout
        )
        assert self.final_line(proc) == "OUTCOME: pass"

    def test_untouched_log_audits_clean(self, tmp_path):
        repo = tmp_path
        self.init_repo_with_log(
            repo, [entry("solo-entry", ["2026-10-01-solo-origin.md"])], "seed the log"
        )
        base = self.git(repo, "rev-parse", "HEAD").strip()
        self.write(
            repo, "docs/history/backlog/2026-10-01-solo-origin.md", "# fixture origin\n"
        )
        self.commit(repo, "touch only an origin file")
        proc = self.audit(repo / LOG_REL, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "0 removals (0 by log ledger) across 0 log-touching commit(s)" in proc.stdout
        assert "REMOVED-WITHOUT-WITNESS" not in proc.stdout
        assert self.final_line(proc) == "OUTCOME: pass"

    def test_outcome_line_present_on_both_verdicts(self, tmp_path):
        repo = tmp_path
        self.init_repo_with_log(
            repo, [entry("kept-entry", ["2026-10-01-kept-origin.md"])], "seed the log"
        )
        clean_base = self.git(repo, "rev-parse", "HEAD").strip()
        self.write(
            repo, "docs/history/backlog/2026-10-01-kept-origin.md", "# fixture origin\n"
        )
        self.commit(repo, "touch only an origin file")
        clean = self.audit(repo / LOG_REL, clean_base)
        assert clean.returncode == 0, clean.stdout + clean.stderr
        assert self.final_line(clean) == "OUTCOME: pass"
        self.write(repo, LOG_REL, log_text([]))
        self.commit(repo, "prune the kept entry without any witness")
        flagged = self.audit(repo / LOG_REL, clean_base)
        assert flagged.returncode == 1, flagged.stdout + flagged.stderr
        assert self.final_line(flagged) == "OUTCOME: fail"

    def test_ad_hoc_receipt_witness_accepts_removal(self, tmp_path):
        repo = tmp_path
        self.init_repo_with_log(
            repo, [entry("plan-entry", ["2026-10-01-plan-origin.md"])], "seed the plan log"
        )
        base = self.git(repo, "rev-parse", "HEAD").strip()
        # The positive probe (two-mode loop policy plan Task 3): an ad-hoc
        # landing commit exists first, and the monitor's prune lands strictly
        # after it carrying the EXEC-PROMPTS-PRUNE receipt naming the removed
        # slug and the landing commit; the landing commit digest substitutes
        # for the plans-root witness (no plan file carries the slug here).
        self.write(
            repo, "docs/history/plans/2026-10-06-unrelated-surface.md", "# unrelated surface\n"
        )
        landing = self.commit(repo, "land the ad-hoc surface change")
        self.write(
            repo,
            EXEC_LOG_REL,
            log_text([entry("adhoc-done", ["2026-10-01-done-origin.md"])]),
        )
        self.commit(repo, "append the adhoc-done entry to the exec log")
        self.write(repo, EXEC_LOG_REL, log_text([]))
        self.commit(
            repo,
            f"prune the completed ad-hoc entry\n\n"
            f"EXEC-PROMPTS-PRUNE: adhoc-done -> {landing}",
        )
        proc = self.audit(repo / LOG_REL, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert (
            f"PRUNE-OK: adhoc-done -> {landing} (EXEC-PROMPTS-PRUNE receipt)"
            in proc.stdout
        )
        assert "REMOVED-WITHOUT-WITNESS" not in proc.stdout
        assert self.final_line(proc) == "OUTCOME: pass"

    def test_ad_hoc_removal_without_matching_receipt_is_flagged(self, tmp_path):
        repo = tmp_path
        self.init_repo_with_log(
            repo, [entry("plan-entry", ["2026-10-01-plan-origin.md"])], "seed the plan log"
        )
        base = self.git(repo, "rev-parse", "HEAD").strip()
        landing = self.git(repo, "rev-parse", "HEAD").strip()
        self.write(
            repo, "docs/history/plans/2026-10-06-unrelated-surface.md", "# unrelated surface\n"
        )
        self.commit(repo, "land an unrelated surface change")
        # The negative probe (two-mode loop policy plan Task 3), three
        # fail-closed shapes: (a) no receipt at all, (b) a receipt naming a
        # different slug, (c) a receipt whose landing commit does not
        # resolve; each still exits 1 with REMOVED-WITHOUT-WITNESS.
        self.write(
            repo,
            EXEC_LOG_REL,
            log_text([entry("adhoc-lost", ["2026-10-01-lost-origin.md"])]),
        )
        self.commit(repo, "append the adhoc-lost entry to the exec log")
        self.write(repo, EXEC_LOG_REL, log_text([]))
        self.commit(repo, "prune the exec entry without any receipt")
        short_a = self.git(repo, "rev-parse", "--short", "HEAD").strip()
        flagged = self.audit(repo / LOG_REL, base)
        assert flagged.returncode == 1, flagged.stdout + flagged.stderr
        assert (
            "REMOVED-WITHOUT-WITNESS: adhoc-lost"
            f" (commit {short_a} prune the exec entry without any receipt)"
            in flagged.stdout
        )
        assert self.final_line(flagged) == "OUTCOME: fail"
        self.write(
            repo,
            EXEC_LOG_REL,
            log_text([entry("adhoc-other", ["2026-10-01-other-origin.md"])]),
        )
        self.commit(repo, "re-append an entry under a different slug")
        self.write(repo, EXEC_LOG_REL, log_text([]))
        self.commit(
            repo,
            f"prune the exec entry under a mismatched receipt\n\n"
            f"EXEC-PROMPTS-PRUNE: not-this-slug -> {landing}",
        )
        short_b = self.git(repo, "rev-parse", "--short", "HEAD").strip()
        mismatched = self.audit(repo / LOG_REL, base)
        assert mismatched.returncode == 1, mismatched.stdout + mismatched.stderr
        assert (
            "REMOVED-WITHOUT-WITNESS: adhoc-other"
            f" (commit {short_b} prune the exec entry under a mismatched receipt)"
            in mismatched.stdout
        )
        assert self.final_line(mismatched) == "OUTCOME: fail"
        self.write(
            repo,
            EXEC_LOG_REL,
            log_text([entry("adhoc-ghost", ["2026-10-01-ghost-origin.md"])]),
        )
        self.commit(repo, "re-append the ghost entry")
        self.write(repo, EXEC_LOG_REL, log_text([]))
        self.commit(
            repo,
            "prune the ghost entry with an unresolvable landing commit\n\n"
            "EXEC-PROMPTS-PRUNE: adhoc-ghost -> "
            "0000000000000000000000000000000000000000",
        )
        short_c = self.git(repo, "rev-parse", "--short", "HEAD").strip()
        ghost = self.audit(repo / LOG_REL, base)
        assert ghost.returncode == 1, ghost.stdout + ghost.stderr
        assert (
            "REMOVED-WITHOUT-WITNESS: adhoc-ghost"
            f" (commit {short_c} prune the ghost entry with an unresolvable"
            in ghost.stdout
        )
        assert self.final_line(ghost) == "OUTCOME: fail"

    def test_plan_log_ledger_receipt_witnesses_removal(self, tmp_path):
        repo = tmp_path
        self.init_repo_with_log(
            repo,
            [entry("ledger-prune", ["2026-10-01-ledger-origin.md"])],
            "seed the log",
        )
        base = self.git(repo, "rev-parse", "HEAD").strip()
        # The 04e505e4e shape: the removal commit's own post-image carries
        # the PLAN-PROMPTS-PRUNE ledger line naming the removed slug, with
        # the real trailing rationale prose after a resolving digest token
        # (three of the four incident lines carry such prose).
        self.write(
            repo,
            LOG_REL,
            log_text_with_ledger(
                [],
                [
                    f"PLAN-PROMPTS-PRUNE: ledger-prune -> {base}"
                    " (ad-hoc-superseded: fixture rationale prose after the token)"
                ],
            ),
        )
        self.commit(repo, "prune the ledger entry with the in-log receipt line")
        proc = self.audit(repo / LOG_REL, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert (
            f"PRUNE-OK: ledger-prune -> {base} (log ledger receipt)" in proc.stdout
        )
        assert "REMOVED-WITHOUT-WITNESS" not in proc.stdout
        assert (
            "1 removals (1 by log ledger) across 1 log-touching commit(s)"
            in proc.stdout
        )
        assert self.final_line(proc) == "OUTCOME: pass"

    def test_ledger_receipt_unresolvable_token_still_flags(self, tmp_path):
        repo = tmp_path
        self.init_repo_with_log(
            repo,
            [entry("ledger-ghost", ["2026-10-01-ghost-origin.md"])],
            "seed the log",
        )
        base = self.git(repo, "rev-parse", "HEAD").strip()
        # A ledger line whose token resolves to no commit and to no path
        # in the removal commit's tree never witnesses.
        self.write(
            repo,
            LOG_REL,
            log_text_with_ledger(
                [],
                [
                    "PLAN-PROMPTS-PRUNE: ledger-ghost -> "
                    "0000000000000000000000000000000000000000"
                ],
            ),
        )
        self.commit(repo, "prune the ghost ledger entry with a dead token")
        proc = self.audit(repo / LOG_REL, base)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert "REMOVED-WITHOUT-WITNESS: ledger-ghost (commit" in proc.stdout
        assert "(log ledger receipt)" not in proc.stdout
        assert "1 removals (0 by log ledger)" in proc.stdout
        assert self.final_line(proc) == "OUTCOME: fail"

    def test_ledger_receipt_mismatched_slug_never_witnesses(self, tmp_path):
        repo = tmp_path
        self.init_repo_with_log(
            repo,
            [entry("ledger-other", ["2026-10-01-other-origin.md"])],
            "seed the log",
        )
        base = self.git(repo, "rev-parse", "HEAD").strip()
        # The ledger line names a different slug: it never witnesses the
        # removed entry, even with a resolving token (the seed commit).
        self.write(
            repo,
            LOG_REL,
            log_text_with_ledger(
                [],
                [f"PLAN-PROMPTS-PRUNE: not-this-slug -> {base}"],
            ),
        )
        self.commit(repo, "prune the entry under a mismatched ledger line")
        proc = self.audit(repo / LOG_REL, base)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert "REMOVED-WITHOUT-WITNESS: ledger-other (commit" in proc.stdout
        assert "(log ledger receipt)" not in proc.stdout
        assert self.final_line(proc) == "OUTCOME: fail"

    def test_ledger_path_token_resolves_through_removal_tree(self, tmp_path):
        repo = tmp_path
        self.init_repo_with_log(
            repo,
            [entry("path-ledger", ["2026-10-01-path-origin.md"])],
            "seed the log",
        )
        base = self.git(repo, "rev-parse", "HEAD").strip()
        # Land a plans-root file whose basename does not carry the slug,
        # so the plan-file witness misses and the ledger path token is
        # what decides.
        self.write(
            repo, "docs/history/plans/2026-10-07-unrelated.md", "# unrelated plan\n"
        )
        self.commit(repo, "land an unrelated plan file")
        # Positive: the path token exists in the removal commit's tree.
        self.write(
            repo,
            LOG_REL,
            log_text_with_ledger(
                [],
                [
                    "PLAN-PROMPTS-PRUNE: path-ledger -> "
                    "docs/history/plans/2026-10-07-unrelated.md"
                ],
            ),
        )
        self.commit(repo, "prune path-ledger with an in-tree ledger path token")
        witnessed = self.audit(repo / LOG_REL, base)
        assert witnessed.returncode == 0, witnessed.stdout + witnessed.stderr
        assert (
            "PRUNE-OK: path-ledger -> "
            "docs/history/plans/2026-10-07-unrelated.md (log ledger receipt)"
            in witnessed.stdout
        )
        assert self.final_line(witnessed) == "OUTCOME: pass"
        # Negative: the path token is absent from the removal commit's
        # tree, so the removal still flags.
        self.write(
            repo,
            LOG_REL,
            log_text([entry("path-ledger-ghost", ["2026-10-01-ghost-origin.md"])]),
        )
        self.commit(repo, "re-append an entry under a fresh slug")
        self.write(
            repo,
            LOG_REL,
            log_text_with_ledger(
                [],
                [
                    "PLAN-PROMPTS-PRUNE: path-ledger-ghost -> "
                    "docs/history/plans/2026-10-07-absent.md"
                ],
            ),
        )
        self.commit(repo, "prune the ghost entry with an out-of-tree path token")
        flagged = self.audit(repo / LOG_REL, base)
        assert flagged.returncode == 1, flagged.stdout + flagged.stderr
        assert "REMOVED-WITHOUT-WITNESS: path-ledger-ghost (commit" in flagged.stdout
        assert self.final_line(flagged) == "OUTCOME: fail"

    def test_exec_removal_reads_own_log_post_image_not_sibling(self, tmp_path):
        repo = tmp_path
        self.init_repo_with_log(
            repo, [entry("plan-entry", ["2026-10-01-plan-origin.md"])], "seed the plan log"
        )
        seed = self.git(repo, "rev-parse", "HEAD").strip()
        # Negative: an exec-log removal whose EXEC-PROMPTS-PRUNE ledger
        # line lives only in the sibling plan log's post-image still
        # flags; each log's removals consult only that log's post-image.
        self.write(
            repo,
            EXEC_LOG_REL,
            log_text([entry("exec-sibling-only", ["2026-10-01-sibling-origin.md"])]),
        )
        self.commit(repo, "append the exec entry")
        self.write(
            repo,
            LOG_REL,
            log_text_with_ledger(
                [entry("plan-entry", ["2026-10-01-plan-origin.md"])],
                [f"EXEC-PROMPTS-PRUNE: exec-sibling-only -> {seed}"],
            ),
        )
        self.write(repo, EXEC_LOG_REL, log_text([]))
        self.commit(repo, "prune the exec entry, receipt only in the sibling log")
        short = self.git(repo, "rev-parse", "--short", "HEAD").strip()
        proc = self.audit(repo / LOG_REL, seed)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert (
            "REMOVED-WITHOUT-WITNESS: exec-sibling-only"
            f" (commit {short} prune the exec entry, receipt only in the sibling log)"
            in proc.stdout
        )
        assert "(log ledger receipt)" not in proc.stdout
        sibling_base = self.git(repo, "rev-parse", "HEAD").strip()
        # Positive: the same removal class receipted by the exec log's own
        # post-image is witnessed.
        self.write(
            repo,
            EXEC_LOG_REL,
            log_text([entry("exec-own-ledger", ["2026-10-01-own-origin.md"])]),
        )
        self.commit(repo, "re-append an exec entry")
        self.write(
            repo,
            EXEC_LOG_REL,
            log_text_with_ledger(
                [],
                [f"EXEC-PROMPTS-PRUNE: exec-own-ledger -> {seed}"],
            ),
        )
        self.commit(repo, "prune the exec entry with its own log receipt")
        own = self.audit(repo / LOG_REL, sibling_base)
        assert own.returncode == 0, own.stdout + own.stderr
        assert (
            f"PRUNE-OK: exec-own-ledger -> {seed} (log ledger receipt)"
            in own.stdout
        )
        assert self.final_line(own) == "OUTCOME: pass"

    def test_commit_message_receipt_wins_over_ledger_line(self, tmp_path):
        repo = tmp_path
        self.init_repo_with_log(
            repo, [entry("plan-entry", ["2026-10-01-plan-origin.md"])], "seed the plan log"
        )
        seed = self.git(repo, "rev-parse", "HEAD").strip()
        self.write(
            repo, "docs/history/plans/2026-10-06-unrelated-surface.md", "# unrelated surface\n"
        )
        landing = self.commit(repo, "land the ad-hoc surface change")
        self.write(
            repo,
            EXEC_LOG_REL,
            log_text([entry("adhoc-both", ["2026-10-01-both-origin.md"])]),
        )
        self.commit(repo, "append the both-receipt entry")
        # Both receipt classes present with different resolving tokens:
        # the ledger line names the seed commit, the commit message names
        # the landing. Precedence keeps the commit-message receipt first,
        # visible in the printed token and in the reconciliation count.
        self.write(
            repo,
            EXEC_LOG_REL,
            log_text_with_ledger(
                [],
                [f"EXEC-PROMPTS-PRUNE: adhoc-both -> {seed}"],
            ),
        )
        self.commit(
            repo,
            f"prune the completed ad-hoc entry\n\n"
            f"EXEC-PROMPTS-PRUNE: adhoc-both -> {landing}",
        )
        proc = self.audit(repo / LOG_REL, seed)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert (
            f"PRUNE-OK: adhoc-both -> {landing} (EXEC-PROMPTS-PRUNE receipt)"
            in proc.stdout
        )
        assert "(log ledger receipt)" not in proc.stdout
        assert "1 removals (0 by log ledger)" in proc.stdout
        assert self.final_line(proc) == "OUTCOME: pass"

    def test_tool_error_paths(self, tmp_path):
        repo = tmp_path
        self.init_repo_with_log(
            repo, [entry("solo-entry", ["2026-10-01-solo-origin.md"])], "seed the log"
        )
        log_path = repo / LOG_REL
        # (a) a missing log at the audit path
        missing = self.audit(tmp_path / "absent" / "PLAN-PROMPTS.md", "main")
        assert missing.returncode == 3, missing.stdout + missing.stderr
        assert "prune-audit: prompt log not found" in missing.stdout
        assert self.final_line(missing) == "OUTCOME: tool_error"
        # (b) an unresolvable base ref
        bad_base = self.audit(log_path, "no-such-ref")
        assert bad_base.returncode == 3, bad_base.stdout + bad_base.stderr
        assert "no-such-ref" in bad_base.stdout
        assert self.final_line(bad_base) == "OUTCOME: tool_error"
        # (c) a corrupted scratch repo: HEAD points at a phantom branch,
        # so the rev-list plumbing call fails over an already-resolved base
        (repo / ".git" / "HEAD").write_text(
            "ref: refs/heads/phantom\n", encoding="utf-8"
        )
        head_sha = self.git(repo, "rev-parse", "main").strip()
        corrupt = self.audit(log_path, head_sha)
        assert corrupt.returncode == 3, corrupt.stdout + corrupt.stderr
        assert self.final_line(corrupt) == "OUTCOME: tool_error"

    def test_stale_mode_regression_fixture_unchanged(self, tmp_path):
        # The checker's built-in selftest still holds (metadata mode).
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--selftest"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert proc.stdout.startswith("selftest ok:")
        # And the stale mode's verdict lines are byte-identical to the
        # pre-plan behavior on the driven fixture.
        write_origin(tmp_path, "2026-10-01-done-origin.md", "Status: done")
        log = write_log(tmp_path, [entry("solo-entry", ["2026-10-01-done-origin.md"])])
        stale = run_checker(log)
        assert stale.returncode == 1, stale.stdout + stale.stderr
        assert stale.stdout == (
            "SERVED: solo-entry -> 2026-10-01-done-origin.md [done]\n"
            "STALE: solo-entry: every origin served;"
            " prune per the log's prune rule\n"
        )

    def test_orphan_receipt_warns_without_failing(self, tmp_path):
        # The witnessed 2026-10-18 intermediate shape: a commit adds a
        # receipt line to a rolling log while removing no entry from that
        # same log. Warning-only: exit 0 with OUTCOME: pass unchanged.
        repo = tmp_path
        self.init_repo_with_log(
            repo, [entry("live-entry", ["2026-10-01-live-origin.md"])], "seed the log"
        )
        base = self.git(repo, "rev-parse", "HEAD").strip()
        self.write(
            repo,
            LOG_REL,
            log_text_with_ledger(
                [entry("live-entry", ["2026-10-01-live-origin.md"])],
                ["PLAN-PROMPTS-PRUNE: ghost-entry -> 0f39e725c"],
            ),
        )
        self.commit(repo, "add the receipt with no removal")
        short = self.git(repo, "rev-parse", "--short", "HEAD").strip()
        proc = self.audit(repo / LOG_REL, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert f"RECEIPT-WITHOUT-REMOVAL: {short} {LOG_REL}" in proc.stdout
        assert self.final_line(proc) == "OUTCOME: pass"

    def test_warning_count_appended_to_summary_line(self, tmp_path):
        repo = tmp_path
        self.init_repo_with_log(
            repo, [entry("live-entry", ["2026-10-01-live-origin.md"])], "seed the log"
        )
        base = self.git(repo, "rev-parse", "HEAD").strip()
        self.write(
            repo,
            LOG_REL,
            log_text_with_ledger(
                [entry("live-entry", ["2026-10-01-live-origin.md"])],
                ["PLAN-PROMPTS-PRUNE: ghost-entry -> 0f39e725c"],
            ),
        )
        self.commit(repo, "add the receipt with no removal")
        proc = self.audit(repo / LOG_REL, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        summary = next(
            line
            for line in proc.stdout.splitlines()
            if line.startswith("prune-audit summary:")
        )
        # Every existing summary substring stays contiguous; the count is
        # an append at line end only.
        assert (
            "prune-audit summary: 0 removals (0 by log ledger)"
            " across 1 log-touching commit(s)" in summary
        )
        assert summary.endswith("1 warning(s)")

    def test_normal_shape_receipt_with_removal_never_warns(self, tmp_path):
        repo = tmp_path
        self.init_repo_with_log(
            repo, [entry("solo-prune", ["2026-10-01-solo-origin.md"])], "seed the log"
        )
        base = self.git(repo, "rev-parse", "HEAD").strip()
        # The normal shape: one commit removes the entry and adds its own
        # ledger receipt line to the same log's post-image.
        self.write(
            repo,
            LOG_REL,
            log_text_with_ledger([], [f"PLAN-PROMPTS-PRUNE: solo-prune -> {base}"]),
        )
        self.commit(repo, "prune the entry with its receipt")
        proc = self.audit(repo / LOG_REL, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert (
            f"PRUNE-OK: solo-prune -> {base} (log ledger receipt)" in proc.stdout
        )
        assert "RECEIPT-WITHOUT-REMOVAL" not in proc.stdout
        summary = next(
            line
            for line in proc.stdout.splitlines()
            if line.startswith("prune-audit summary:")
        )
        assert summary.endswith(", 0 warning(s)")
        assert self.final_line(proc) == "OUTCOME: pass"

    def test_re_apply_repair_receipt_commits_warn_once(self, tmp_path):
        # The priced shape: the receipt commit warns once; the later
        # removal commit completing the receipt classifies PRUNE-OK via
        # the ledger lookup with no warning of its own.
        repo = tmp_path
        self.init_repo_with_log(
            repo, [entry("solo-prune", ["2026-10-01-solo-origin.md"])], "seed the log"
        )
        base = self.git(repo, "rev-parse", "HEAD").strip()
        self.write(
            repo,
            LOG_REL,
            log_text_with_ledger(
                [entry("solo-prune", ["2026-10-01-solo-origin.md"])],
                [f"PLAN-PROMPTS-PRUNE: solo-prune -> {base}"],
            ),
        )
        self.commit(repo, "add the receipt first (the orphan shape)")
        short_receipt = self.git(repo, "rev-parse", "--short", "HEAD").strip()
        # The ledger receipt line stays (append-only ledger); only the
        # entry section is removed, completing the earlier receipt.
        self.write(
            repo,
            LOG_REL,
            log_text_with_ledger(
                [], [f"PLAN-PROMPTS-PRUNE: solo-prune -> {base}"]
            ),
        )
        self.commit(repo, "complete the removal")
        proc = self.audit(repo / LOG_REL, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert proc.stdout.count("RECEIPT-WITHOUT-REMOVAL") == 1
        assert (
            f"RECEIPT-WITHOUT-REMOVAL: {short_receipt} {LOG_REL}" in proc.stdout
        )
        assert "PRUNE-OK: solo-prune" in proc.stdout
        assert "(log ledger receipt)" in proc.stdout
        assert self.final_line(proc) == "OUTCOME: pass"

    def test_removal_without_witness_fail_class_preserved(self, tmp_path):
        repo = tmp_path
        self.init_repo_with_log(
            repo, [entry("solo-entry", ["2026-10-01-solo-origin.md"])], "seed the log"
        )
        base = self.git(repo, "rev-parse", "HEAD").strip()
        self.write(repo, LOG_REL, log_text([]))
        self.commit(repo, "remove the entry with no witness")
        proc = self.audit(repo / LOG_REL, base)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert "REMOVED-WITHOUT-WITNESS: solo-entry" in proc.stdout
        assert self.final_line(proc) == "OUTCOME: fail"

    def test_per_log_scoping_one_warning_names_receipt_log(self, tmp_path):
        # A receipt added to one rolling log while the same commit removes
        # a sibling-log entry witnessed by that sibling's own ledger
        # receipt: exit 0, one warning naming the receipt's log only.
        repo = tmp_path
        self.git(repo, "-c", "init.defaultBranch=main", "init")
        self.write(repo, LOG_REL, log_text([entry("plan-live", ["2026-10-01-p.md"])]))
        # The exec log seeds with its ledger receipt for exec-entry
        # already in place (beside a completed sacrificial prune's
        # line), so the audited commit's removal of exec-entry is
        # witnessed by that surviving ledger line while the plan-log
        # receipt addition is the window's only orphan shape.
        self.write(
            repo,
            EXEC_LOG_REL,
            log_text_with_ledger(
                [entry("exec-entry", ["2026-10-01-e.md"])],
                [
                    "EXEC-PROMPTS-PRUNE: sacrificial -> 0f39e725c",
                    "EXEC-PROMPTS-PRUNE: exec-entry -> 0f39e725c",
                ],
            ),
        )
        self.commit(repo, "seed both logs")
        seed = self.git(repo, "rev-parse", "HEAD").strip()
        self.write(
            repo,
            EXEC_LOG_REL,
            log_text_with_ledger(
                [],
                [
                    f"EXEC-PROMPTS-PRUNE: sacrificial -> {seed}",
                    f"EXEC-PROMPTS-PRUNE: exec-entry -> {seed}",
                ],
            ),
        )
        self.write(
            repo,
            LOG_REL,
            log_text_with_ledger(
                [entry("plan-live", ["2026-10-01-p.md"])],
                ["PLAN-PROMPTS-PRUNE: ghost-entry -> 0f39e725c"],
            ),
        )
        self.commit(repo, "remove the exec entry, orphan-receipt the plan log")
        proc = self.audit(repo / LOG_REL, seed)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert proc.stdout.count("RECEIPT-WITHOUT-REMOVAL") == 1
        assert f"RECEIPT-WITHOUT-REMOVAL" in proc.stdout
        assert f"{LOG_REL}" in proc.stdout.split("RECEIPT-WITHOUT-REMOVAL")[1].splitlines()[0]
        assert "PRUNE-OK: exec-entry" in proc.stdout
        assert self.final_line(proc) == "OUTCOME: pass"


class TestCollateralServedDiscovery:
    """The ``--collateral-served --base <ref>`` read-only discovery mode:
    entries every origin of which is served at HEAD or was served at base
    and deleted in the base..HEAD range, with at least one range-produced
    origin, list one line each naming only the range-produced origins.

    Each test drives the real script through subprocess against a scratch
    git repository (identity plumbed explicitly per commit) so the
    base-side states are committed blobs, never working-tree-only files.
    """

    def git(self, repo: Path, *args: str) -> str:
        proc = subprocess.run(
            ["git", *args], cwd=repo, capture_output=True, text=True, timeout=60
        )
        assert proc.returncode == 0, f"git {args}: {proc.stderr}"
        return proc.stdout

    def write(self, repo: Path, rel: str, text: str) -> None:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self, repo: Path, message: str) -> str:
        self.git(repo, "add", "-A")
        self.git(
            repo,
            "-c",
            "user.name=Collateral Fixture",
            "-c",
            "user.email=collateral-fixture@example.test",
            "commit",
            "-m",
            message,
        )
        return self.git(repo, "rev-parse", "HEAD").strip()

    def discover(self, repo: Path, base: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--collateral-served",
                "--base",
                base,
                str(repo / LOG_REL),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

    def seed(
        self, repo: Path, log_sections: list[str], origins: dict[str, str]
    ) -> str:
        """Init the scratch repo, write the origin rows and the log, commit;
        returns the base commit."""
        self.git(repo, "-c", "init.defaultBranch=main", "init")
        for name, text in origins.items():
            self.write(repo, f"docs/history/backlog/{name}", text)
        self.write(repo, LOG_REL, log_text(log_sections))
        return self.commit(repo, "seed the log and origin rows")

    def test_status_flip_in_range_lists_with_range_origin_only(self, tmp_path):
        repo = tmp_path
        base = self.seed(
            repo,
            [
                entry(
                    "flip-entry",
                    ["2026-10-01-flip-origin.md", "2026-10-01-both-served.md"],
                )
            ],
            {
                "2026-10-01-flip-origin.md": "# fixture\n\n- **Status:** open\n",
                "2026-10-01-both-served.md": "# fixture\n\nStatus: done\n",
            },
        )
        self.write(
            repo,
            "docs/history/backlog/2026-10-01-flip-origin.md",
            "# fixture\n\nStatus: done\n",
        )
        self.commit(repo, "flip the origin to covered")
        proc = self.discover(repo, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        lines = [
            line
            for line in proc.stdout.splitlines()
            if line.startswith("COLLATERAL-SERVED:")
        ]
        assert lines == [
            "COLLATERAL-SERVED: flip-entry -> 2026-10-01-flip-origin.md"
        ], proc.stdout

    def test_archive_move_in_range_lists(self, tmp_path):
        repo = tmp_path
        base = self.seed(
            repo,
            [entry("move-entry", ["2026-10-01-move-origin.md"])],
            {"2026-10-01-move-origin.md": "# fixture\n\n- **Status:** open\n"},
        )
        (repo / "docs/history/backlog/2026-10-01-move-origin.md").unlink()
        self.write(
            repo,
            "docs/history/backlog/completed/2026-10-01-move-origin.md",
            "# fixture moved\n",
        )
        self.commit(repo, "archive the covered row")
        proc = self.discover(repo, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert (
            "COLLATERAL-SERVED: move-entry -> 2026-10-01-move-origin.md"
            in proc.stdout
        )

    def test_covered_row_deleted_in_range_lists(self, tmp_path):
        repo = tmp_path
        base = self.seed(
            repo,
            [entry("del-entry", ["2026-10-01-del-origin.md"])],
            {"2026-10-01-del-origin.md": "# fixture\n\nStatus: covered\n"},
        )
        (repo / "docs/history/backlog/2026-10-01-del-origin.md").unlink()
        self.commit(repo, "delete the covered row (delete-not-stub)")
        proc = self.discover(repo, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert (
            "COLLATERAL-SERVED: del-entry -> 2026-10-01-del-origin.md"
            in proc.stdout
        )

    def test_mixed_entry_with_one_live_origin_never_lists(self, tmp_path):
        repo = tmp_path
        base = self.seed(
            repo,
            [
                entry(
                    "mixed-entry",
                    ["2026-10-01-mx-served.md", "2026-10-01-mx-live.md"],
                )
            ],
            {
                "2026-10-01-mx-served.md": "# fixture\n\nStatus: done\n",
                "2026-10-01-mx-live.md": "# fixture\n\n- **Status:** open\n",
            },
        )
        self.write(
            repo,
            "docs/history/backlog/2026-10-01-mx-served.md",
            "# fixture\n\nStatus: covered\n",
        )
        self.commit(repo, "restate the served origin")
        proc = self.discover(repo, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "COLLATERAL-SERVED:" not in proc.stdout

    def test_all_served_already_at_base_never_lists(self, tmp_path):
        repo = tmp_path
        base = self.seed(
            repo,
            [entry("foreign-entry", ["2026-10-01-foreign-origin.md"])],
            {"2026-10-01-foreign-origin.md": "# fixture\n\nStatus: done\n"},
        )
        proc = self.discover(repo, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "COLLATERAL-SERVED:" not in proc.stdout

    def test_origin_absent_at_both_never_lists(self, tmp_path):
        repo = tmp_path
        base = self.seed(
            repo,
            [
                entry(
                    "absent-entry",
                    ["2026-10-01-absent-origin.md", "2026-10-01-abs-flip.md"],
                )
            ],
            {
                "2026-10-01-abs-flip.md": "# fixture\n\n- **Status:** open\n",
                # absent-origin.md is cited by the log but never written.
            },
        )
        self.write(
            repo,
            "docs/history/backlog/2026-10-01-abs-flip.md",
            "# fixture\n\nStatus: done\n",
        )
        self.commit(repo, "flip the second origin; the first stays absent")
        proc = self.discover(repo, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "COLLATERAL-SERVED:" not in proc.stdout

    def test_live_or_deferred_at_base_deleted_in_range_never_lists(self, tmp_path):
        repo = tmp_path
        base = self.seed(
            repo,
            [
                entry("nodel-entry", ["2026-10-01-nd-live.md", "2026-10-01-nd-def.md"]),
            ],
            {
                "2026-10-01-nd-live.md": "# fixture\n\n- **Status:** open\n",
                "2026-10-01-nd-def.md": "# fixture\n\n- **Status:** open\n",
            },
        )
        (repo / "docs/history/backlog/2026-10-01-nd-live.md").unlink()
        (repo / "docs/history/backlog/2026-10-01-nd-def.md").unlink()
        self.write(
            repo,
            "docs/history/backlog/deferred/2026-10-01-nd-def.md",
            "# fixture deferred\n",
        )
        self.commit(repo, "delete the live row and defer the other")
        proc = self.discover(repo, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "COLLATERAL-SERVED:" not in proc.stdout

    def test_reopened_covered_row_never_lists(self, tmp_path):
        repo = tmp_path
        base = self.seed(
            repo,
            [entry("reopen-entry", ["2026-10-01-reopen-origin.md"])],
            {"2026-10-01-reopen-origin.md": "# fixture\n\nStatus: done\n"},
        )
        self.write(
            repo,
            "docs/history/backlog/2026-10-01-reopen-origin.md",
            "# fixture\n\n- **Status:** open\n",
        )
        self.commit(repo, "reopen the covered row")
        proc = self.discover(repo, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "COLLATERAL-SERVED:" not in proc.stdout

    def test_deferred_at_base_and_head_never_lists(self, tmp_path):
        repo = tmp_path
        base = self.seed(
            repo,
            [entry("defstay-entry", ["2026-10-01-defstay-origin.md"])],
            {"2026-10-01-defstay-origin.md": "# fixture\n\n- **Status:** open\n"},
        )
        (repo / "docs/history/backlog/2026-10-01-defstay-origin.md").unlink()
        self.write(
            repo,
            "docs/history/backlog/deferred/2026-10-01-defstay-origin.md",
            "# fixture deferred\n",
        )
        self.commit(repo, "defer the origin (still actionable)")
        proc = self.discover(repo, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "COLLATERAL-SERVED:" not in proc.stdout

    def test_deferred_at_base_turned_served_lists_with_that_origin(self, tmp_path):
        repo = tmp_path
        base = self.seed(
            repo,
            [entry("defserved-entry", ["2026-10-01-ds-origin.md"])],
            {"2026-10-01-ds-origin.md": "# fixture\n\n- **Status:** open\n"},
        )
        self.write(
            repo,
            "docs/history/backlog/2026-10-01-ds-origin.md",
            "# fixture\n\nStatus: done\n",
        )
        self.commit(repo, "serve the deferred origin")
        proc = self.discover(repo, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert (
            "COLLATERAL-SERVED: defserved-entry -> 2026-10-01-ds-origin.md"
            in proc.stdout
        )

    def test_own_entry_removed_before_discovery_never_lists(self, tmp_path):
        repo = tmp_path
        base = self.seed(
            repo,
            [entry("own-entry", ["2026-10-01-own-origin.md"])],
            {"2026-10-01-own-origin.md": "# fixture\n\nStatus: done\n"},
        )
        # The landing pruned its own dispatch entry before discovery runs:
        # the log at HEAD no longer carries the entry.
        self.write(repo, LOG_REL, log_text([]))
        self.commit(repo, "prune the own entry with its receipt")
        proc = self.discover(repo, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "own-entry" not in proc.stdout

    def test_discovery_run_is_read_only(self, tmp_path):
        repo = tmp_path
        base = self.seed(
            repo,
            [entry("ro-entry", ["2026-10-01-ro-origin.md"])],
            {"2026-10-01-ro-origin.md": "# fixture\n\nStatus: done\n"},
        )
        self.write(
            repo,
            "docs/history/backlog/2026-10-01-ro-origin.md",
            "# fixture\n\nStatus: covered\n",
        )
        self.commit(repo, "restate the served origin")
        log_before = (repo / LOG_REL).read_text(encoding="utf-8")
        origin_before = {
            p.name: p.read_text(encoding="utf-8")
            for p in sorted((repo / "docs/history/backlog").rglob("*.md"))
        }
        proc = self.discover(repo, base)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert (repo / LOG_REL).read_text(encoding="utf-8") == log_before
        origin_after = {
            p.name: p.read_text(encoding="utf-8")
            for p in sorted((repo / "docs/history/backlog").rglob("*.md"))
        }
        assert origin_after == origin_before
        assert self.git(repo, "status", "--porcelain").strip() == ""

    def test_unresolvable_base_is_tool_error(self, tmp_path):
        repo = tmp_path
        self.seed(
            repo,
            [entry("te-entry", ["2026-10-01-te-origin.md"])],
            {"2026-10-01-te-origin.md": "# fixture\n\nStatus: done\n"},
        )
        proc = self.discover(repo, "no-such-ref")
        assert proc.returncode == 3, proc.stdout + proc.stderr
        assert self.final_line_is_tool_error(proc)

    def final_line_is_tool_error(self, proc: subprocess.CompletedProcess) -> bool:
        lines = proc.stdout.strip().splitlines()
        return bool(lines) and lines[-1] == "OUTCOME: tool_error"
