from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import hooks_probe

ROOT = Path(__file__).resolve().parents[1]

PR_SKILL_REMINDER_ADAPTER = "~/.claude/scripts/pr-skill-reminder.sh"


class HooksProbeTest(unittest.TestCase):
    def test_plan_readiness_docs_no_longer_claim_codex_lacks_blocking_stop(self):
        text = (ROOT / "agents/hooks/plan-readiness/README.md").read_text(encoding="utf-8")
        self.assertNotIn("current Codex host cannot block the final response", text)
        self.assertIn("`Stop` and `SubagentStop` hooks can return a blocking decision", text)


class PrSkillReminderWiringTest(unittest.TestCase):
    """Claude pr-skill-reminder wiring verdicts: wired, unwired, miswired."""

    def _fixture_home(self) -> tempfile.TemporaryDirectory:
        return tempfile.TemporaryDirectory()

    def _install_adapter(self, home: Path) -> None:
        adapter = hooks_probe._expand(PR_SKILL_REMINDER_ADAPTER, home)
        adapter.parent.mkdir(parents=True, exist_ok=True)
        target = home / "adapter-pr-skill-reminder.sh"
        target.write_text("# probe fixture\n", encoding="utf-8")
        adapter.symlink_to(target)

    def _write_user_prompt_submit(self, home: Path, command: str) -> None:
        path = home / ".claude" / "settings.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        hooks = {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": command}]}]}
        path.write_text(json.dumps({"hooks": hooks}), encoding="utf-8")

    def test_wired_reports_full_and_cell_passes(self):
        with self._fixture_home() as td:
            home = Path(td)
            self._install_adapter(home)
            self._write_user_prompt_submit(
                home, f"bash {PR_SKILL_REMINDER_ADAPTER}"
            )
            self.assertEqual(
                hooks_probe._assess_wiring("Claude", "pr-skill-reminder", home), "FULL"
            )
            cell = hooks_probe._probe_one("Claude", "pr-skill-reminder", "FULL", home=home)
            self.assertEqual(cell.status, "PASS")

    def test_unwired_reports_none_and_cell_fails_registration(self):
        with self._fixture_home() as td:
            home = Path(td)
            self._install_adapter(home)
            self.assertEqual(
                hooks_probe._assess_wiring("Claude", "pr-skill-reminder", home), "NONE"
            )
            cell = hooks_probe._probe_one("Claude", "pr-skill-reminder", "FULL", home=home)
            self.assertEqual(cell.status, "FAIL")
            self.assertIn("config registration missing", cell.detail)

    def test_command_without_adapter_path_reports_none(self):
        with self._fixture_home() as td:
            home = Path(td)
            self._install_adapter(home)
            self._write_user_prompt_submit(
                home, "bash ~/.claude/scripts/other-hook.sh pr-skill-reminder"
            )
            self.assertEqual(
                hooks_probe._assess_wiring("Claude", "pr-skill-reminder", home), "NONE"
            )


class SkillNameExtractionTest(unittest.TestCase):
    """Backtick-quoted skill-name extraction over versioned hook text."""

    def test_real_pr_skill_reminder_text_extracts_both_review_skills(self):
        text = (ROOT / "agents/hooks/pr-skill-reminder/pr-skill-reminder.sh").read_text(
            encoding="utf-8"
        )
        self.assertEqual(
            hooks_probe.skill_name_references(text),
            ["doing-code-review", "receiving-review"],
        )

    def test_ignores_backticks_on_lines_without_skill_mention(self):
        text = "# uses `jq` and `grep` here\ninvoke the `no-such-skill` skill\n"
        self.assertEqual(hooks_probe.skill_name_references(text), ["no-such-skill"])

    def test_ignores_non_identifier_spans_and_dedupes(self):
        text = "skill line: `set -u` then `doing-code-review` and `doing-code-review` again\n"
        self.assertEqual(hooks_probe.skill_name_references(text), ["doing-code-review"])


class SkillNameReferenceVerdictTest(unittest.TestCase):
    """probe_skill_name_references verdicts: missing name, resolving name."""

    def _write_hook_script(self, repo: Path, text: str) -> Path:
        script = repo / "agents" / "hooks" / "fixture-hook" / "fixture-hook.sh"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text(text, encoding="utf-8")
        return script

    def _seed_skill(self, home: Path, root: str, name: str) -> None:
        (home / root.replace("~/", "") / name).mkdir(parents=True)

    def test_missing_name_fails_naming_hook_and_missing_name(self):
        with tempfile.TemporaryDirectory() as repo_td, tempfile.TemporaryDirectory() as home_td:
            repo = Path(repo_td)
            self._write_hook_script(repo, "invoke the `ghost-skill` skill\n")
            checks = hooks_probe.probe_skill_name_references(
                repo_root=repo, home=Path(home_td)
            )
            self.assertEqual(len(checks), 1)
            check = checks[0]
            self.assertEqual(check.status, "FAIL")
            self.assertEqual(check.hook, "fixture-hook/fixture-hook.sh")
            self.assertIn("missing skill name(s)", check.detail)
            self.assertIn("`ghost-skill`", check.detail)

    def test_name_under_agents_root_passes(self):
        with tempfile.TemporaryDirectory() as repo_td, tempfile.TemporaryDirectory() as home_td:
            repo = Path(repo_td)
            home = Path(home_td)
            self._write_hook_script(repo, "invoke the `ghost-skill` skill\n")
            self._seed_skill(home, "~/.agents/skills", "ghost-skill")
            checks = hooks_probe.probe_skill_name_references(repo_root=repo, home=home)
            self.assertEqual([c.status for c in checks], ["PASS"])
            self.assertIn("`ghost-skill`", checks[0].detail)

    def test_name_under_claude_root_passes(self):
        with tempfile.TemporaryDirectory() as repo_td, tempfile.TemporaryDirectory() as home_td:
            repo = Path(repo_td)
            home = Path(home_td)
            self._write_hook_script(repo, "invoke the `ghost-skill` skill\n")
            self._seed_skill(home, "~/.claude/skills", "ghost-skill")
            checks = hooks_probe.probe_skill_name_references(repo_root=repo, home=home)
            self.assertEqual([c.status for c in checks], ["PASS"])

    def test_script_without_skill_references_gets_pass_row(self):
        with tempfile.TemporaryDirectory() as repo_td, tempfile.TemporaryDirectory() as home_td:
            repo = Path(repo_td)
            self._write_hook_script(repo, "echo no skills here\n")
            checks = hooks_probe.probe_skill_name_references(
                repo_root=repo, home=Path(home_td)
            )
            self.assertEqual(len(checks), 1)
            self.assertEqual(checks[0].status, "PASS")
            self.assertIn("no skill-name references", checks[0].detail)

    def test_real_versioned_hooks_pass_with_every_referenced_name_resolving(self):
        referenced: set[str] = set()
        for script in sorted((ROOT / "agents" / "hooks").glob("*/*")):
            if script.is_file() and script.suffix in (".sh", ".py"):
                referenced.update(
                    hooks_probe.skill_name_references(script.read_text(encoding="utf-8"))
                )
        self.assertEqual(referenced, {"doing-code-review", "receiving-review"})
        with tempfile.TemporaryDirectory() as home_td:
            home = Path(home_td)
            for name in referenced:
                self._seed_skill(home, "~/.agents/skills", name)
            checks = hooks_probe.probe_skill_name_references(repo_root=ROOT, home=home)
            self.assertTrue(checks)
            self.assertEqual([c.status for c in checks], ["PASS"] * len(checks))


if __name__ == "__main__":
    unittest.main()
