from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import codex_model_guard_probe as probe

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "agents/hooks/codex-model-guard/require-luna.py"


class CodexModelGuardProbeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source" / "require-luna.py"
        self.source.parent.mkdir()
        self.source.write_bytes(b"guard\x00bytes")
        self.installed = self.root / "installed" / "require-luna.py"
        self.installed.parent.mkdir()
        self.installed.write_bytes(b"guard\x00bytes")
        self.other = self.root / "installed" / "other.py"
        self.other.write_bytes(b"other executable")
        self.config = self.root / "config.toml"
        self.config.write_text('[agents]\ndefault_subagent_model = "chosen-model"\n', encoding="utf-8")
        self.registration = self.root / "hooks.json"

    def set_registration(self, *, event="PreToolUse", matcher="Agent", command=None):
        command = command or str(self.installed)
        document = {"hooks": {event: [{"matcher": matcher, "hooks": [
            {"type": "command", "command": command}
        ]}]}}
        self.registration.write_text(json.dumps(document), encoding="utf-8")

    def run_probe(self, *, config=None, env=None, cwd=None, default_config=None):
        return probe.probe(self.registration, self.source, config, env=env, cwd=cwd,
                           default_config=default_config)

    def test_aligned_runtime_passes(self):
        self.set_registration(command=f"python3 {self.installed}")
        before = self._snapshot(self.registration, self.installed, self.source, self.config)
        outcome = self.run_probe(config=self.config)
        self.assertEqual(outcome["status"], "ok")
        self.assertEqual(outcome["hook_path"], str(self.installed.resolve()))
        self.assertEqual(outcome["selected_model"], "chosen-model")
        self.assertEqual(self._snapshot(self.registration, self.installed, self.source, self.config), before)

    def test_cli_reports_bounded_json_and_exit_status_for_aligned_and_drifted_policy(self):
        self.set_registration(command=f"python3 {self.installed}")
        self.config.write_text(
            '[agents]\ndefault_subagent_model = "chosen-model"\n'
            '[unrelated]\nsecret = "do-not-report"\ntranscript = "private conversation"\n', encoding="utf-8")
        before = self._snapshot(self.registration, self.installed, self.source, self.config)
        child_env = {
            "PATH": os.defpath,
            "HOME": str(self.root / "isolated-home"),
            "LANG": "C",
            "LC_ALL": "C",
        }

        aligned = subprocess.run(
            [sys.executable, str(ROOT / "scripts/codex_model_guard_probe.py"),
             "--registration", str(self.registration), "--source", str(self.source),
             "--config", str(self.config)],
            text=True, capture_output=True, check=False, timeout=5, env=child_env,
        )

        self.assertEqual(aligned.returncode, 0, aligned.stderr)
        result = json.loads(aligned.stdout)
        self.assertEqual(result["status"], "ok", result)
        self.assertEqual(result["config_path"], str(self.config.resolve()))
        self.assertEqual(set(result), {"status", "hook_path", "config_path", "selected_model", "failed_check", "error", "recovery"})
        self.assertNotIn("do-not-report", aligned.stdout)
        self.assertNotIn("private conversation", aligned.stdout)
        self.assertEqual(self._snapshot(self.registration, self.installed, self.source, self.config), before)

        self.installed.write_bytes(b"drifted guard")
        drift_before = self._snapshot(self.registration, self.installed, self.source, self.config)
        drifted = subprocess.run(
            [sys.executable, str(ROOT / "scripts/codex_model_guard_probe.py"),
             "--registration", str(self.registration), "--source", str(self.source),
             "--config", str(self.config)],
            text=True, capture_output=True, check=False, timeout=5, env=child_env,
        )

        self.assertEqual(drifted.returncode, 1, drifted.stderr)
        result = json.loads(drifted.stdout)
        self.assertEqual(result["status"], "runtime-policy-unavailable", result)
        self.assertEqual(result["failed_check"], "guard_alignment", result)
        self.assertEqual(set(result), {"status", "failed_check", "error", "recovery"})
        self.assertNotIn("config_path", result)
        self.assertNotIn("do-not-report", drifted.stdout)
        self.assertNotIn("private conversation", drifted.stdout)
        self.assertEqual(self._snapshot(self.registration, self.installed, self.source, self.config), drift_before)

    def test_wrong_target_or_guard_drift_fails_closed(self):
        self.set_registration()
        original = self.installed.read_bytes()
        self.installed.unlink()
        before = self._snapshot(self.registration, self.source, self.config)
        outcome = self.run_probe(config=self.config)
        self.assertEqual(outcome["status"], "runtime-policy-unavailable")
        self.assertEqual(outcome["failed_check"], "installed_guard")
        self.assertNotIn(str(self.root), json.dumps(outcome))
        self.assertEqual(self._snapshot(self.registration, self.source, self.config), before)

        self.installed.write_bytes(original)
        self.installed.write_bytes(b"different bytes")
        before = self._snapshot(self.registration, self.installed, self.source, self.config)
        outcome = self.run_probe(config=self.config)
        self.assertEqual(outcome["status"], "runtime-policy-unavailable")
        self.assertEqual(outcome["failed_check"], "guard_alignment")
        self.assertEqual(self._snapshot(self.registration, self.installed, self.source, self.config), before)

        self.set_registration(command=str(self.other))
        outcome = self.run_probe(config=self.config)
        self.assertEqual(outcome["status"], "runtime-policy-unavailable")
        self.assertEqual(outcome["failed_check"], "registration")

    def test_registration_must_match_worker_launch(self):
        cases = [
            ({"hooks": {}}, "missing PreToolUse"),
            ({"hooks": {"UserPromptSubmit": [{"matcher": "Agent", "hooks": [
                {"type": "command", "command": str(self.installed)}]}]}}, "wrong event"),
            ({"hooks": {"PreToolUse": [{"matcher": "Other", "hooks": [
                {"type": "command", "command": str(self.installed)}]}]}}, "nonmatching matcher"),
        ]
        for document, label in cases:
            self.registration.write_text(json.dumps(document), encoding="utf-8")
            self.assertEqual(self.run_probe(config=self.config)["status"], "runtime-policy-unavailable", label)

        for command in (str(self.other), f"sh -c 'python3 {self.installed}'",
                        f"{self.installed} && true", f"python3 {self.installed} ; true"):
            self.set_registration(command=command)
            self.assertEqual(self.run_probe(config=self.config)["status"], "runtime-policy-unavailable", command)

        self.set_registration(matcher=".*", command=str(self.installed))
        self.assertEqual(self.run_probe(config=self.config)["status"], "ok")

    def test_relative_hook_target_resolves_from_runtime_working_directory(self):
        caller = self.root / "caller"
        runtime = self.root / "runtime"
        for directory in (caller, runtime):
            (directory / "hooks").mkdir(parents=True)
        relative_target = Path("hooks/require-luna.py")
        (caller / relative_target).write_bytes(b"drifted guard")
        (runtime / relative_target).write_bytes(self.source.read_bytes())
        self.set_registration(command=str(relative_target))

        with mock.patch.object(Path, "cwd", return_value=caller):
            outcome = self.run_probe(config=self.config, cwd=runtime)

        self.assertEqual(outcome["status"], "ok")
        self.assertEqual(outcome["hook_path"], str((runtime / relative_target).resolve()))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO fixtures are not available")
    def test_special_file_hook_target_refuses_without_blocking(self):
        fifo = self.root / "installed" / "require-luna.py"
        fifo.unlink()
        os.mkfifo(fifo)
        self.set_registration(command=str(fifo))

        outcome = self.run_probe(config=self.config)

        self.assertEqual(outcome["status"], "runtime-policy-unavailable")
        self.assertEqual(outcome["failed_check"], "installed_guard")

    def test_effective_config_path_matches_guard(self):
        self.set_registration()
        caller_cwd = self.root / "caller"
        caller_cwd.mkdir()
        configurations = (
            ("absolute", "absolute-model", self.config),
            ("relative", "relative-model", self.config),
            ("default", "default-model", self.root / "home" / ".codex" / "config.toml"),
        )
        default_config = configurations[2][2]
        for name, model, config_path in configurations:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(f'[agents]\ndefault_subagent_model = "{model}"\n', encoding="utf-8")
            effective_path = config_path
            if name == "relative":
                effective_path = caller_cwd / "config.toml"
                effective_path.write_bytes(config_path.read_bytes())
                self.assertEqual(probe.effective_config({"CODEX_CONFIG": "config.toml"}, caller_cwd), effective_path.resolve())
            normalized = effective_path.resolve()
            worker_env = {"PATH": os.environ.get("PATH", ""), "HOME": str(self.root / "home")}
            if name != "default":
                worker_env["CODEX_CONFIG"] = "config.toml" if name == "relative" else str(normalized)
            result = self.run_probe(env=worker_env,
                                    cwd=caller_cwd, default_config=default_config)
            self.assertEqual(result["status"], "ok", name)
            self.assertEqual(Path(result["config_path"]), normalized, name)
            self.assertEqual(result["selected_model"], model, name)

            accepted = self._run_guard(model, worker_env, caller_cwd)
            denied = self._run_guard(f"wrong-{model}", worker_env, caller_cwd)
            self.assertEqual(accepted.returncode, 0, (name, accepted.stdout, accepted.stderr))
            self.assertEqual(json.loads(denied.stdout)["hookSpecificOutput"]["permissionDecision"], "deny", name)

    def test_missing_or_malformed_selected_model_fails_closed(self):
        self.set_registration()
        cases = [
            ("not TOML", "invalid TOML"),
            ("[other]\nkey = 'value'\n", "absent agents"),
            ("[agents]\n", "missing model"),
            ("[agents]\ndefault_subagent_model = 3\n", "non-string model"),
            ('[agents]\ndefault_subagent_model = " "\n', "blank model"),
        ]
        for contents, label in cases:
            bad_config = self.root / "bad.toml"
            bad_config.write_text(contents, encoding="utf-8")
            result = self.run_probe(config=bad_config)
            self.assertEqual(result["status"], "runtime-policy-unavailable", label)
            self.assertEqual(result["failed_check"], "selected_config", label)

        arbitrary = self.root / "arbitrary.toml"
        arbitrary.write_text('[agents]\ndefault_subagent_model = "future-model-99"\n', encoding="utf-8")
        self.assertEqual(self.run_probe(config=arbitrary)["selected_model"], "future-model-99")

    def test_output_excludes_transcript_and_unrelated_config(self):
        self.set_registration()
        self.config.write_text(
            '[agents]\ndefault_subagent_model = "chosen-model"\n'
            '[unrelated]\nsecret = "do-not-report"\n'
            'transcript = "private conversation"\n', encoding="utf-8")
        output = json.dumps(self.run_probe(config=self.config))
        self.assertNotIn("do-not-report", output)
        self.assertNotIn("private conversation", output)
        self.assertNotIn("transcript", output)
        self.assertIn("chosen-model", output)

    def test_unreadable_policy_output_is_bounded_and_read_only(self):
        self.set_registration()
        missing = self.root / "private-secret-config.toml"
        registration_before = self.registration.read_bytes()
        outcome = self.run_probe(config=missing)
        self.assertEqual(outcome["status"], "runtime-policy-unavailable")
        self.assertEqual(outcome["failed_check"], "selected_config")
        self.assertEqual(outcome["error"], "Selected model config is unreadable.")
        self.assertIn("recovery", outcome)
        self.assertNotIn("private-secret", json.dumps(outcome))
        self.assertEqual(self.registration.read_bytes(), registration_before)
        self.assertFalse(missing.exists())

    def test_each_unreadable_stage_is_named_without_disclosing_paths(self):
        self.registration.write_text("{", encoding="utf-8")
        outcome = self.run_probe(config=self.config)
        self.assertEqual(outcome["failed_check"], "registration")
        self.assertNotIn(str(self.root), json.dumps(outcome))

        self.set_registration()
        missing_registration = self.root / "missing-hooks.json"
        outcome = probe.probe(missing_registration, self.source, self.config)
        self.assertEqual(outcome["failed_check"], "registration")
        self.assertNotIn(str(self.root), json.dumps(outcome))

        self.set_registration()
        installed_bytes = self.installed.read_bytes()
        self.installed.unlink()
        outcome = self.run_probe(config=self.config)
        self.assertEqual(outcome["failed_check"], "installed_guard")
        self.assertNotIn(str(self.root), json.dumps(outcome))
        self.installed.write_bytes(installed_bytes)

        missing_source = self.root / "missing-source.py"
        outcome = probe.probe(self.registration, missing_source, self.config)
        self.assertEqual(outcome["failed_check"], "versioned_source")
        self.assertNotIn(str(self.root), json.dumps(outcome))

    def test_symlink_loop_paths_fail_closed_without_disclosure(self):
        loop_target = self.root / "require-luna.py"
        loop_target.symlink_to(loop_target)
        self.set_registration(command=str(loop_target))
        outcome = self.run_probe(config=self.config)
        self.assertEqual(outcome["status"], "runtime-policy-unavailable")
        self.assertEqual(outcome["failed_check"], "registration")
        self.assertEqual(outcome["error"], "Registered model guard target cannot be canonicalized.")
        self.assertNotIn(str(self.root), json.dumps(outcome))

        self.set_registration()
        config_loop = self.root / "config-loop.toml"
        config_loop.symlink_to(config_loop)
        outcome = self.run_probe(config=config_loop)
        self.assertEqual(outcome["status"], "runtime-policy-unavailable")
        self.assertEqual(outcome["failed_check"], "selected_config")
        self.assertEqual(outcome["error"], "Effective Codex config path cannot be resolved.")
        self.assertNotIn(str(self.root), json.dumps(outcome))

    def _snapshot(self, *paths: Path):
        return {path: (path.exists(), path.read_bytes() if path.exists() else None) for path in paths}

    def _run_guard(self, requested_model: str, environment: dict[str, str], cwd: Path):
        event = {"hook_event_name": "PreToolUse", "tool_name": "Agent",
                 "tool_input": {"model": requested_model}}
        return subprocess.run([sys.executable, str(GUARD)], input=json.dumps(event), text=True,
                              capture_output=True, check=False, timeout=3,
                              cwd=cwd, env=environment)


if __name__ == "__main__":
    unittest.main()
