"""Focused contract tests for the bounded required-suite runner."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parent.parent
RUNNER = REPO_ROOT / "scripts" / "run_required_test_suite.py"


class RequiredTestSuiteRunnerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="required-suite-runner-")
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        (self.repo / "scripts").mkdir(parents=True)
        self.report = Path(self.tmp.name) / "report.json"

    def write_suite(self, name: str, source: str) -> Path:
        path = self.repo / "scripts" / name
        path.write_text(source, encoding="utf-8")
        return path

    def run_runner(self, *args: str, env: dict[str, str] | None = None,
                   timeout: float = 15) -> subprocess.CompletedProcess:
        child_env = dict(os.environ)
        child_env["AI_PLAYBOOK_TEST_VENV"] = str(Path(sys.executable).parent)
        child_env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + child_env.get("PATH", "")
        child_env.pop("PYTHONHOME", None)
        child_env.pop("PYTHONPATH", None)
        if env:
            child_env.update(env)
        command = [
            sys.executable, str(RUNNER), "--repo-root", str(self.repo),
            "--json-report", str(self.report), "--suite-timeout", "12",
            "--per-script-timeout", "5", "--cleanup-grace", "0.1",
            *args,
        ]
        return subprocess.run(command, capture_output=True, text=True,
                              env=child_env, timeout=timeout)

    def read_report(self) -> dict:
        self.assertTrue(self.report.is_file(), "runner must write a complete report")
        return json.loads(self.report.read_text(encoding="utf-8"))

    def test_mise_required_task_pins_venv_and_uses_single_bounded_command(self):
        import tomllib

        config = tomllib.loads((REPO_ROOT / "mise.toml").read_text(encoding="utf-8"))
        task = config["tasks"]["test:required"]
        env = config["env"]
        test_venv_bin = "{{ env.HOME }}/.agents/venvs/ai-playbook-test/bin"

        self.assertEqual(env["AI_PLAYBOOK_TEST_VENV"], test_venv_bin)
        self.assertEqual(env["_"]["path"], [test_venv_bin])
        self.assertEqual(env["PYTHONHOME"], "")
        self.assertEqual(env["PYTHONPATH"], "")
        self.assertTrue(task["raw_args"])
        self.assertEqual(task["timeout"], "295s")
        self.assertIsInstance(task["run"], str, "mise task must run one command")
        self.assertIn("--workers 8", task["run"])
        self.assertIn("--per-script-timeout 60", task["run"])
        self.assertIn("--suite-timeout 270", task["run"])
        self.assertIn("--json-report", task["run"])

    def test_matched_worker_campaign_uses_median_gain_range_and_resource_gates(self):
        import run_required_test_suite as runner_module

        runs = []
        times = {1: [100, 102, 101], 4: [70, 72, 71], 8: [65, 67, 66]}
        for round_number, order in enumerate(runner_module.MATCHED_WORKER_ORDERS, start=1):
            for workers in order:
                runs.append({
                    "round": round_number, "workers": workers,
                    "wall_seconds": times[workers][round_number - 1],
                    "sample_fingerprint": "same-sample",
                    "inventory_digest": "same-inventory",
                    "environment_fingerprint": "same-environment",
                    "resource_check_passed": True,
                })
        qualification = runner_module._campaign_qualification(runs)
        self.assertTrue(qualification["complete"])
        self.assertTrue(qualification["candidates"]["4"]["qualifies"])
        self.assertTrue(qualification["candidates"]["8"]["qualifies"])
        self.assertEqual(qualification["selected_workers"], 8)
        self.assertEqual(qualification["baseline"]["median_seconds"], 101)
        self.assertEqual(qualification["baseline"]["range_seconds"], 2)

        borderline = []
        times = {1: [100, 110, 105], 4: [95, 96, 97], 8: [90, 91, 92]}
        for round_number, order in enumerate(runner_module.MATCHED_WORKER_ORDERS, start=1):
            for workers in order:
                borderline.append({
                    "round": round_number, "workers": workers,
                    "wall_seconds": times[workers][round_number - 1],
                    "sample_fingerprint": "same-sample",
                    "inventory_digest": "same-inventory",
                    "environment_fingerprint": "same-environment",
                    "resource_check_passed": workers != 8,
                })
        qualification = runner_module._campaign_qualification(borderline)
        self.assertFalse(qualification["candidates"]["4"]["qualifies"])
        self.assertFalse(qualification["candidates"]["8"]["qualifies"])
        self.assertEqual(qualification["selected_workers"], 1)

        incomplete = runner_module._campaign_qualification(runs[:-1])
        self.assertFalse(incomplete["complete"])
        self.assertEqual(incomplete["selected_workers"], 1)

    def test_process_attribution_rejects_nonzero_ps_and_missing_snapshots(self):
        import run_required_test_suite as runner_module

        runner = runner_module.RequiredTestSuiteRunner(self.repo)
        for returncode, stderr in ((1, "ps unavailable"), (0, "")):
            with self.subTest(returncode=returncode):
                with patch(
                    "subprocess.run",
                    return_value=subprocess.CompletedProcess(
                        args=["ps"], returncode=returncode, stdout="", stderr=stderr,
                    ),
                ):
                    snapshot = runner._process_snapshot()
                self.assertTrue(snapshot["snapshot_error"])
                self.assertFalse(runner_module._process_attribution_passed({"samples": [snapshot]}))
        self.assertFalse(runner_module._process_attribution_passed({"samples": []}))

    def test_cleanup_snapshot_omission_checks_process_group_liveness(self):
        import run_required_test_suite as runner_module

        runner = runner_module.RequiredTestSuiteRunner(self.repo)
        empty_snapshot = subprocess.CompletedProcess(
            args=["ps"], returncode=0, stdout="", stderr="",
        )
        with patch("subprocess.run", return_value=empty_snapshot), patch(
            "os.killpg", side_effect=PermissionError("group exists but is not signalable"),
        ):
            live_groups, error = runner_module._live_process_groups({123}, timeout=0.2)

        self.assertEqual(live_groups, {123})
        self.assertIsNone(error)

    def test_process_reaping_assertion_ignores_permission_error_after_reaping(self):
        completed_snapshot = subprocess.CompletedProcess(
            args=["ps"], returncode=0, stdout="123 1 123 Z child\n", stderr="",
        )
        with patch("os.kill"), patch("subprocess.run", return_value=completed_snapshot), patch(
            "os.killpg", side_effect=PermissionError("process group is no longer signalable"),
        ):
            self.assert_process_group_reaped({"pid": 123, "pgid": 123})

    def test_matched_campaign_writes_relative_report_under_repo_root(self):
        import run_required_test_suite as runner_module

        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        report = self.repo / "reports" / "campaign.json"
        child_env = dict(os.environ)
        test_venv = str(Path(sys.executable).parent)
        child_env["AI_PLAYBOOK_TEST_VENV"] = test_venv
        child_env["PATH"] = test_venv + os.pathsep + child_env.get("PATH", "")
        child_env.pop("PYTHONHOME", None)
        child_env.pop("PYTHONPATH", None)
        with patch.object(
            runner_module, "_run_matched_campaign",
            return_value={"status": "pass", "selected_workers": 1,
                          "campaign_elapsed_seconds": 0.25},
        ):
            previous = Path.cwd()
            try:
                os.chdir(outside)
                with patch.dict(os.environ, child_env, clear=True):
                    result = runner_module.main([
                        "--repo-root", str(self.repo),
                        "--json-report", "reports/campaign.json",
                        "--matched-workers", "--suite", "scripts/test_alpha.py",
                        "--test-id", "scripts/test_alpha.py=scripts/test_alpha.py::test_one",
                    ])
            finally:
                os.chdir(previous)

        self.assertEqual(result, 0)
        self.assertTrue(report.is_file())
        self.assertFalse((outside / "reports" / "campaign.json").exists())
        self.assertEqual(json.loads(report.read_text())["status"], "pass")

    def test_matched_campaign_resolves_basename_suite_selectors(self):
        from types import SimpleNamespace
        import run_required_test_suite as runner_module

        self.write_suite("test_alpha.py", "def test_one():\n    assert True\n")
        original_runner = runner_module.RequiredTestSuiteRunner
        constructor_calls = 0

        class ReachedCampaignRounds(Exception):
            pass

        def stop_after_sample_resolution(*args, **kwargs):
            nonlocal constructor_calls
            constructor_calls += 1
            if constructor_calls == 1:
                return original_runner(*args, **kwargs)
            raise ReachedCampaignRounds()

        args = SimpleNamespace(
            repo_root=str(self.repo), suite=["test_alpha.py"],
            per_script_timeout=5, suite_timeout=12, cleanup_grace=0.1,
            campaign_timeout=30, profile_witness=[],
        )
        with patch.object(
            runner_module, "RequiredTestSuiteRunner", side_effect=stop_after_sample_resolution,
        ):
            with self.assertRaises(ReachedCampaignRounds):
                runner_module._run_matched_campaign(
                    args, {"scripts/test_alpha.py": ["test_alpha.py::test_one"]},
                )

    def test_focused_selection_is_partial_and_full_inventory_is_rederived(self):
        self.write_suite("test_alpha.py", "def test_alpha():\n    assert True\n")
        self.write_suite("test_beta.py", "def test_beta():\n    assert True\n")

        focused = self.run_runner("--suite", "scripts/test_alpha.py", "--workers", "1")
        self.assertEqual(focused.returncode, 0, focused.stderr)
        report = self.read_report()
        self.assertTrue(report["partial"])
        self.assertEqual([x["source_suite"] for x in report["suites"]], ["scripts/test_alpha.py"])
        self.assertEqual(report["suites"][0]["collected"], 1)
        self.assertEqual(report["suites"][0]["executed"], 1)

        focused_id = self.run_runner(
            "--suite", "scripts/test_alpha.py", "--workers", "1",
            "--test-id", "scripts/test_alpha.py=scripts/test_alpha.py::test_alpha",
        )
        self.assertEqual(focused_id.returncode, 0, focused_id.stderr)
        report = self.read_report()
        self.assertTrue(report["partial"])
        self.assertEqual(report["suites"][0]["collected_ids"], ["scripts/test_alpha.py::test_alpha"])
        self.assertEqual(report["suites"][0]["executed_ids"], ["scripts/test_alpha.py::test_alpha"])

        self.write_suite("test_gamma.py", "def test_gamma():\n    assert True\n")
        full = self.run_runner("--workers", "1")
        self.assertEqual(full.returncode, 0, full.stderr)
        report = self.read_report()
        self.assertFalse(report["partial"])
        self.assertEqual(report["pilot_substitutions"], [])
        self.assertEqual(
            {x["source_suite"] for x in report["suites"]},
            {"scripts/test_alpha.py", "scripts/test_beta.py", "scripts/test_gamma.py"},
        )

    def test_class_only_suite_shards_whole_classes_and_accounts_each_id_once(self):
        self.write_suite(
            "test_classes.py",
            "import unittest\n"
            "class First(unittest.TestCase):\n"
            "    @classmethod\n    def setUpClass(cls): cls.fixture = True\n"
            "    def test_one(self): self.assertTrue(self.fixture)\n"
            "class Second(unittest.TestCase):\n"
            "    @classmethod\n    def setUpClass(cls): cls.fixture = True\n"
            "    def test_two(self): self.assertTrue(self.fixture)\n",
        )
        result = self.run_runner("--suite", "test_classes.py", "--workers", "4")
        self.assertEqual(result.returncode, 0, result.stderr)
        suite = self.read_report()["suites"][0]
        self.assertEqual(suite["collected"], 2)
        self.assertEqual(suite["executed"], 2)
        ids = [test_id for shard in suite["shards"] for test_id in shard["test_ids"]]
        self.assertEqual(len(ids), 2)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(suite["shards"]), 2)
        self.assertTrue(all(shard["queue_wait"] >= 0 for shard in suite["shards"]))

    def test_load_tests_entrypoint_uses_unittest_protocol(self):
        import run_required_test_suite as runner_module

        self.write_suite(
            "support_cases.py",
            "import unittest\n"
            "class Selected(unittest.TestCase):\n"
            "    def test_selected(self): self.assertTrue(True)\n",
        )
        source = self.write_suite(
            "test_load_tests_entrypoint.py",
            "import unittest\n"
            "from support_cases import Selected\n"
            "def load_tests(loader, standard_tests, pattern):\n"
            "    return loader.loadTestsFromTestCase(Selected)\n",
        )

        self.assertEqual(runner_module._policy(source), "unittest")
        result = self.run_runner("--suite", source.name, "--workers", "1")

        self.assertEqual(result.returncode, 0, result.stderr)
        suite = self.read_report()["suites"][0]
        self.assertEqual(suite["collected"], 1)
        self.assertEqual(suite["executed"], 1)
        self.assertEqual(suite["collected_ids"], ["support_cases.Selected.test_selected"])

    def test_safe_unittest_methods_are_grouped_by_class_on_full_run(self):
        self.write_suite(
            "test_methods.py",
            "import unittest\n"
            "import tempfile\n"
            "class TestMethods(unittest.TestCase):\n"
            "    def setUp(self): self.tmp = tempfile.TemporaryDirectory()\n"
            "    def tearDown(self): self.tmp.cleanup()\n"
            "    def test_one(self): self.assertTrue(self.tmp.name)\n"
            "    def test_two(self): self.assertTrue(self.tmp.name)\n",
        )
        result = self.run_runner("--suite", "test_methods.py", "--workers", "4")
        self.assertEqual(result.returncode, 0, result.stderr)
        suite = self.read_report()["suites"][0]
        self.assertEqual(suite["collected"], 2)
        self.assertEqual(len(suite["shards"]), 1)
        self.assertEqual(suite["shards"][0]["shard_id"], "test_methods.TestMethods")
        self.assertEqual(len(suite["shards"][0]["test_ids"]), 2)

    def test_large_fixture_safe_unittest_methods_use_bounded_batches(self):
        methods = "".join(
            f"    def test_case_{index:02d}(self): self.assertTrue(self.tmp.name)\n"
            for index in range(23)
        )
        self.write_suite(
            "test_large_method_class.py",
            "import tempfile, unittest\n"
            "class TestMethods(unittest.TestCase):\n"
            "    def setUp(self): self.tmp = tempfile.TemporaryDirectory()\n"
            "    def tearDown(self): self.tmp.cleanup()\n"
            + methods,
        )

        result = self.run_runner("--suite", "test_large_method_class.py", "--workers", "4")

        self.assertEqual(result.returncode, 0, result.stderr)
        suite = self.read_report()["suites"][0]
        self.assertEqual(suite["executed"], 23)
        self.assertEqual(len(suite["shards"]), 4)
        self.assertEqual(sorted(len(shard["test_ids"]) for shard in suite["shards"]), [5, 6, 6, 6])
        self.assertTrue(all(shard["outcome"] == "passed" for shard in suite["shards"]))
        shard_ids = [test_id for shard in suite["shards"] for test_id in shard["test_ids"]]
        executed_ids = [test_id for shard in suite["shards"] for test_id in shard["executed_ids"]]
        self.assertEqual(len(shard_ids), len(set(shard_ids)))
        self.assertCountEqual(shard_ids, suite["collected_ids"])
        self.assertEqual(len(executed_ids), len(set(executed_ids)))
        self.assertCountEqual(executed_ids, suite["collected_ids"])

    def test_focused_safe_unittest_method_is_an_explicit_single_method_shard(self):
        self.write_suite(
            "test_methods.py",
            "import unittest\n"
            "import tempfile\n"
            "class TestMethods(unittest.TestCase):\n"
            "    def setUp(self): self.tmp = tempfile.TemporaryDirectory()\n"
            "    def tearDown(self): self.tmp.cleanup()\n"
            "    def test_one(self): self.assertTrue(self.tmp.name)\n"
            "    def test_two(self): self.assertTrue(self.tmp.name)\n",
        )
        result = self.run_runner(
            "--suite", "test_methods.py", "--workers", "4",
            "--test-id", "test_methods.py=test_methods.TestMethods.test_one",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        suite = self.read_report()["suites"][0]
        self.assertTrue(self.read_report()["partial"])
        self.assertEqual(suite["collected"], 1)
        self.assertEqual(suite["executed"], 1)
        self.assertEqual(
            suite["shards"][0]["shard_id"],
            "test_methods.TestMethods.test_one",
        )
        self.assertEqual(
            suite["shards"][0]["test_ids"],
            ["test_methods.TestMethods.test_one"],
        )

    def test_temporary_fixture_does_not_hide_writes_outside_its_unique_root(self):
        import run_required_test_suite as runner_module

        parent_write = (
            "        Path(self.tmp.name)" + chr(46) +
            "parent.joinpath('shared-marker').write_text('shared')\n"
        )
        absolute_write = (
            "        Path(" + repr(chr(47) + "tmp/shared-marker") +
            ").write_text('shared')\n"
        )
        source = self.write_suite(
            "test_fixture_scope.py",
            "import tempfile\n"
            "import unittest\n"
            "from pathlib import Path\n"
            "class TestFixtureScoped(unittest.TestCase):\n"
            "    def setUp(self): self.tmp = tempfile.TemporaryDirectory()\n"
            "    def tearDown(self): self.tmp.cleanup()\n"
            "    def test_write_inside_root(self):\n"
            "        Path(self.tmp.name, 'marker').write_text('private')\n"
            "class TestSharedParentWrite(unittest.TestCase):\n"
            "    def setUp(self): self.tmp = tempfile.TemporaryDirectory()\n"
            "    def tearDown(self): self.tmp.cleanup()\n"
            "    def test_write_outside_root(self):\n"
            + parent_write +
            "class TestFixedSharedPathWrite(unittest.TestCase):\n"
            "    def setUp(self): self.tmp = tempfile.TemporaryDirectory()\n"
            "    def tearDown(self): self.tmp.cleanup()\n"
            "    def test_write_outside_root(self):\n"
            + absolute_write,
        )
        module = runner_module._module_from_path(source)
        self.assertTrue(runner_module._class_method_shards_are_safe(module.TestFixtureScoped))
        self.assertFalse(runner_module._class_method_shards_are_safe(module.TestSharedParentWrite))
        self.assertFalse(runner_module._class_method_shards_are_safe(module.TestFixedSharedPathWrite))
        classification, _ = runner_module._scheduling_class(source)
        self.assertEqual(classification, "unknown-serial")

    def test_environment_backed_shared_write_is_not_isolated_by_a_temporary_fixture(self):
        import run_required_test_suite as runner_module

        source = self.write_suite(
            "test_env_fixture_scope.py",
            "import os\nimport tempfile\nimport unittest\nfrom pathlib import Path\n"
            "class TestSharedEnvironmentWrite(unittest.TestCase):\n"
            "    def setUp(self): self.tmp = tempfile.TemporaryDirectory()\n"
            "    def tearDown(self): self.tmp.cleanup()\n"
            "    def test_write_shared_path(self):\n"
            "        Path(os.environ['SHARED_MARKER']).write_text('shared')\n",
        )
        module = runner_module._module_from_path(source)
        self.assertFalse(runner_module._class_method_shards_are_safe(module.TestSharedEnvironmentWrite))
        classification, _ = runner_module._scheduling_class(source)
        self.assertEqual(classification, "unknown-serial")

    def test_environment_path_alias_is_not_isolated_by_a_temporary_fixture(self):
        import run_required_test_suite as runner_module

        source = self.write_suite(
            "test_env_alias_fixture_scope.py",
            "import os\nimport tempfile\nimport unittest\nfrom pathlib import Path\n"
            "class TestSharedEnvironmentAliasWrite(unittest.TestCase):\n"
            "    def setUp(self): self.tmp = tempfile.TemporaryDirectory()\n"
            "    def tearDown(self): self.tmp.cleanup()\n"
            "    def test_write_shared_path(self):\n"
            "        shared = os.environ['SHARED_MARKER']\n"
            "        target = Path(shared)\n"
            "        target.write_text('shared')\n",
        )
        module = runner_module._module_from_path(source)
        self.assertFalse(runner_module._class_method_shards_are_safe(
            module.TestSharedEnvironmentAliasWrite
        ))
        classification, _ = runner_module._scheduling_class(source)
        self.assertEqual(classification, "unknown-serial")

    def test_class_method_env_aliases_are_scoped_per_fixture_and_test_function(self):
        import run_required_test_suite as runner_module

        source = self.write_suite(
            "test_function_scoped_env_alias.py",
            "import os, tempfile, unittest\nfrom pathlib import Path\n"
            "class TestPrivateEnvironmentTarget(unittest.TestCase):\n"
            "    def setUp(self):\n"
            "        self.tmp = tempfile.TemporaryDirectory()\n"
            "        env = dict(os.environ)\n"
            "        self.base_env = env\n"
            "    def tearDown(self): self.tmp.cleanup()\n"
            "    def test_write_private_path(self):\n"
            "        env = dict(self.base_env)\n"
            "        env['SHARED_MARKER'] = str(Path(self.tmp.name) / 'marker')\n"
            "        Path(env['SHARED_MARKER']).write_text('private')\n",
        )
        module = runner_module._module_from_path(source)

        self.assertTrue(runner_module._class_method_shards_are_safe(
            module.TestPrivateEnvironmentTarget
        ))
        classification, _ = runner_module._scheduling_class(source)
        self.assertEqual(classification, "unknown-serial")

    def test_pytest_env_write_isolated_by_function_scoped_fixture_is_parallel_safe(self):
        import run_required_test_suite as runner_module

        source = self.write_suite(
            "test_pytest_fixture_scope.py",
            "import os\nfrom pathlib import Path\nimport pytest\n"
            "@pytest.fixture\n"
            "def scoped_marker(tmp_path, monkeypatch):\n"
            "    marker = tmp_path / 'marker'\n"
            "    monkeypatch.setenv('SHARED_MARKER', str(marker))\n"
            "    return marker\n"
            "def test_write_scoped_environment_path(scoped_marker):\n"
            "    Path(os.environ['SHARED_MARKER']).write_text('private')\n",
        )

        classification, _ = runner_module._scheduling_class(source)

        self.assertEqual(classification, "isolated-fixture")

    def test_pytest_env_write_with_unscoped_value_remains_serial(self):
        import run_required_test_suite as runner_module

        source = self.write_suite(
            "test_pytest_unscoped_env.py",
            "import os\nfrom pathlib import Path\n"
            "def test_write_inherited_environment_path(tmp_path):\n"
            "    Path(os.environ['SHARED_MARKER']).write_text('shared')\n",
        )

        classification, _ = runner_module._scheduling_class(source)

        self.assertEqual(classification, "unknown-serial")

    def test_pytest_dynamic_fixture_scope_write_remains_serial(self):
        import run_required_test_suite as runner_module

        source = self.write_suite(
            "test_pytest_dynamic_fixture_scope.py",
            "import os\nfrom pathlib import Path\nimport pytest\n"
            "def choose_scope(*, fixture_name, config): return 'session'\n"
            "@pytest.fixture(scope=choose_scope)\n"
            "def shared_root(tmp_path_factory): return tmp_path_factory.mktemp('shared')\n"
            "def test_write_shared_root(shared_root):\n"
            "    Path(os.environ['SHARED_MARKER']).write_text(str(shared_root))\n",
        )

        classification, _ = runner_module._scheduling_class(source)

        self.assertEqual(classification, "unknown-serial")

    def test_pytest_tmp_path_factory_shared_directory_remains_serial(self):
        import run_required_test_suite as runner_module

        source = self.write_suite(
            "test_pytest_shared_factory_path.py",
            "import pytest\nfrom pathlib import Path\n"
            "@pytest.fixture\n"
            "def shared_root(tmp_path_factory):\n"
            "    return tmp_path_factory.mktemp('shared', numbered=False)\n"
            "def test_write_shared_root(shared_root):\n"
            "    Path(shared_root / 'marker').write_text('shared')\n",
        )

        classification, _ = runner_module._scheduling_class(source)

        self.assertEqual(classification, "unknown-serial")

    def test_shard_exception_is_recorded_and_all_consumers_are_joined(self):
        import asyncio
        import run_required_test_suite as runner_module

        runner = runner_module.RequiredTestSuiteRunner(self.repo, workers=2)
        source = self.write_suite("test_shard_queue.py", "def test_placeholder(): pass\n")
        shards = [
            {"shard_id": f"shard-{index}", "test_ids": [f"case-{index}"]}
            for index in range(4)
        ]
        active = 0
        peak_active = 0

        async def run_shard(path, policy, shard, classification, evidence, deadline, queued_at):
            nonlocal active, peak_active
            active += 1
            peak_active = max(peak_active, active)
            try:
                await asyncio.sleep(0.01)
                if shard["shard_id"] == "shard-0":
                    raise RuntimeError("injected shard failure")
                return {"shard_id": shard["shard_id"], "outcome": "passed", "test_ids": shard["test_ids"]}
            finally:
                active -= 1

        runner._run_shard = run_shard
        results = asyncio.run(runner._run_shard_queue(
            source.resolve(), "unittest", shards, "unknown-serial", {},
            time.monotonic() + 5, 2,
        ))

        self.assertEqual(active, 0)
        self.assertLessEqual(peak_active, 2)
        self.assertEqual([result["shard_id"] for result in results], [f"shard-{index}" for index in range(4)])
        self.assertEqual(results[0]["outcome"], "error")
        self.assertEqual(results[0]["errors"], 1)
        self.assertEqual(results[0]["test_ids"], ["case-0"])
        self.assertTrue(all(result["outcome"] == "passed" for result in results[1:]))

    def test_process_waiting_for_worker_slot_does_not_launch_after_deadline(self):
        import asyncio
        import run_required_test_suite as runner_module

        runner = runner_module.RequiredTestSuiteRunner(self.repo, workers=1)
        attempted_launches = []

        async def forbid_launch(*args, **kwargs):
            attempted_launches.append(True)
            raise AssertionError("deadline must be checked before process creation")

        async def exercise():
            await runner.semaphore.acquire()
            with patch.object(asyncio, "create_subprocess_exec", new=forbid_launch):
                process_task = asyncio.create_task(runner._run_process([], deadline=time.monotonic() + 0.05))
                await asyncio.sleep(0.08)
                runner.semaphore.release()
                return await process_task

        result = asyncio.run(exercise())

        self.assertEqual(result.outcome, "timeout")
        self.assertEqual(attempted_launches, [])

    def test_zero_exit_cannot_hide_incomplete_or_duplicate_shard_accounting(self):
        from types import SimpleNamespace
        import run_required_test_suite as runner_module

        source = self.write_suite("test_accounting.py", "# synthetic shard source\n")
        runner = runner_module.RequiredTestSuiteRunner(self.repo, workers=1)
        expected = [
            "test_accounting.TestCase.test_one",
            "test_accounting.TestCase.test_two",
        ]
        shard = {"shard_id": "test_accounting.TestCase", "test_ids": expected}
        process = SimpleNamespace(
            outcome="completed", returncode=0, stdout="child exited zero\n", stderr="",
            started_at=1.0, ended_at=2.0,
        )
        complete = {
            "ok": True, "collected_ids": expected, "executed_ids": expected,
            "collected": 2, "executed": 2, "failures": 0, "errors": 0, "skipped": 0,
        }
        cases = {
            "omitted execution ID": {
                **complete, "executed_ids": expected[:1], "executed": 1,
            },
            "duplicated execution ID": {
                **complete, "executed_ids": [expected[0], expected[0]],
            },
            "duplicated collected ID": {
                **complete, "collected_ids": [expected[0], expected[0]],
            },
            "missing counts": {
                key: value for key, value in complete.items()
                if key not in {"collected", "executed"}
            },
        }
        for name, worker in cases.items():
            with self.subTest(name=name):
                record = runner._shard_record(
                    source.resolve(), shard, "read-only", {}, 0.9, process, worker,
                )
                self.assertEqual(record["returncode"], 0)
                self.assertEqual(record["outcome"], "accounting_error")

    def test_pytest_mixed_suite_reports_each_node_id_and_counts_failures_and_skips(self):
        self.write_suite(
            "test_mixed.py",
            "import unittest\nimport pytest\n"
            "class TestCase(unittest.TestCase):\n    def test_class_case(self): self.assertTrue(True)\n"
            "def test_function_case(): assert True\n"
            "def test_skipped_case(): pytest.skip('fixture skip')\n"
            "def test_failed_case(): assert False\n",
        )
        result = self.run_runner("--suite", "test_mixed.py", "--workers", "1")
        self.assertNotEqual(result.returncode, 0)
        suite = self.read_report()["suites"][0]
        self.assertEqual(suite["collected"], 4)
        self.assertEqual(suite["executed"], 4)
        self.assertEqual(suite["skipped"], 1)
        self.assertEqual(suite["failures"], 1)
        self.assertEqual(suite["outcome"], "failed")
        ids = [test_id for shard in suite["shards"] for test_id in shard["test_ids"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(shard["source_suite"] == "scripts/test_mixed.py" for shard in suite["shards"]))

    def test_hostile_python_and_pytest_environment_is_pinned_to_configured_venv(self):
        witness = Path(self.tmp.name) / "environment.json"
        hostile = Path(self.tmp.name) / "hostile"
        fake_bin = hostile / "bin"
        fake_py = hostile / "pythonpath"
        fake_bin.mkdir(parents=True)
        fake_py.mkdir(parents=True)
        (fake_bin / "python3").write_text("#!/bin/sh\nexit 97\n", encoding="utf-8")
        (fake_bin / "python3").chmod(0o755)
        (fake_py / "pytest.py").write_text("raise RuntimeError('hostile pytest imported')\n", encoding="utf-8")
        (fake_py / "runner_helper.py").write_text("VALUE = 'hostile'\n", encoding="utf-8")
        (self.repo / "scripts" / "runner_helper.py").write_text("VALUE = 'configured-helper'\n", encoding="utf-8")
        self.write_suite(
            "test_environment.py",
            "import json, os, sys\nimport pytest\nimport runner_helper\nfrom pathlib import Path\n"
            "def test_environment():\n"
            "    Path(os.environ['RUNNER_WITNESS']).write_text(json.dumps({"
            "'executable': sys.executable, 'pytest': pytest.__file__, 'helper': runner_helper.__file__,"
            "'helper_value': runner_helper.VALUE, 'venv': os.environ['AI_PLAYBOOK_TEST_VENV'],"
            "'path': os.environ['PATH'], 'pythonpath': os.environ.get('PYTHONPATH'),"
            "'pythonhome': os.environ.get('PYTHONHOME')}))\n",
        )
        env = {
            "AI_PLAYBOOK_TEST_VENV": str(hostile / "no-such-venv"),
            "PATH": str(fake_bin),
            "PYTHONPATH": str(fake_py),
            "PYTHONHOME": str(hostile / "not-a-python-home"),
            "PYTEST_ADDOPTS": "-k no_such_case",
            "PYTEST_PLUGINS": "missing_hostile_plugin",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "0",
            "RUNNER_WITNESS": str(witness),
        }
        import run_required_test_suite
        runner = run_required_test_suite.RequiredTestSuiteRunner(
            self.repo, workers=1, per_script_timeout=5, suite_timeout=12,
            cleanup_grace=.1, focused_suites=["test_environment.py"], json_report=self.report,
        )
        with patch.dict(os.environ, env, clear=False):
            report = runner.run()
            runner.write_report(report)
        self.assertEqual(report["status"], "passed", report)
        observed = json.loads(witness.read_text(encoding="utf-8"))
        venv = Path(sys.executable).parent
        self.assertEqual(Path(observed["executable"]).parent, venv)
        self.assertEqual(Path(observed["venv"]), venv)
        self.assertTrue(Path(observed["pytest"]).resolve().is_relative_to(venv.parent.resolve()))
        self.assertEqual(observed["helper_value"], "configured-helper")
        self.assertTrue(Path(observed["helper"]).resolve().is_relative_to((self.repo / "scripts").resolve()))
        self.assertEqual(observed["path"].split(os.pathsep)[0], str(venv))
        self.assertIsNone(observed["pythonhome"])
        suite = self.read_report()["suites"][0]
        self.assertEqual(suite["executed"], 1, "pytest deselection must not produce a false green")

    def test_child_timeout_kills_a_term_ignoring_descendant_and_writes_failure_report(self):
        pidfile = Path(self.tmp.name) / "descendant.pid"
        self.write_suite(
            "test_timeout.py",
            "import json, os, signal, subprocess, sys, time\nfrom pathlib import Path\n"
            "def test_slow():\n"
            "    child = subprocess.Popen([sys.executable, '-c', "
            "'import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(300)'])\n"
            f"    Path({str(pidfile)!r}).write_text(json.dumps({{'pid': child.pid, 'pgid': os.getpgid(child.pid), 'worker_pgid': os.getpgrp()}}))\n"
            "    time.sleep(30)\n",
        )
        result = self.run_runner(
            "--suite", "test_timeout.py", "--workers", "1", "--per-script-timeout", "1",
            "--suite-timeout", "5", "--cleanup-grace", "0.1", timeout=8,
        )
        self.assertNotEqual(result.returncode, 0)
        suite = self.read_report()["suites"][0]
        self.assertEqual(suite["outcome"], "timeout", suite)
        self.assertTrue(suite["report_complete"])
        self.assertTrue(pidfile.exists())
        process_identity = json.loads(pidfile.read_text())
        pid = process_identity["pid"]
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            pass
        else:
            state = subprocess.run(["ps", "-o", "pid=,ppid=,pgid=,state=,command=", "-p", str(pid)], capture_output=True, text=True)
            try:
                fields = state.stdout.strip().split()
                self.assertTrue(not fields or fields[3].startswith("Z"),
                                f"descendant is still live: {state.stdout.strip()} identity={process_identity}")
            finally:
                try:
                    os.killpg(process_identity["pgid"], signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_inventory_drift_and_zero_collection_fail_closed(self):
        source = self.write_suite(
            "test_drift.py",
            "from pathlib import Path\n"
            "def test_changes_inventory():\n"
            "    Path(__file__).write_text('def test_after_drift(): pass\\n')\n",
        )
        result = self.run_runner("--suite", "test_drift.py", "--workers", "1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.read_report()["suites"][0]["outcome"], "inventory_drift")

        source.write_text("# intentionally has no tests\n", encoding="utf-8")
        result = self.run_runner("--suite", "test_drift.py", "--workers", "1")
        self.assertNotEqual(result.returncode, 0)
        suite = self.read_report()["suites"][0]
        self.assertEqual(suite["collected"], 0)
        self.assertNotEqual(suite["outcome"], "passed")

    def test_unknown_suites_are_serial_and_queue_times_are_reported(self):
        active = Path(self.tmp.name) / "active"
        source = (
            "import os, time\nfrom pathlib import Path\n"
            "def test_shared_path():\n"
            "    marker = Path(os.environ['SHARED_MARKER'])\n"
            "    marker.mkdir()\n"
            "    time.sleep(.2)\n"
            "    marker.rmdir()\n"
        )
        self.write_suite("test_a.py", source)
        self.write_suite("test_b.py", source)
        result = self.run_runner(
            "--workers", "4", env={"SHARED_MARKER": str(active)}, timeout=8,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = self.read_report()
        self.assertEqual(len(report["suites"]), 2)
        for suite in report["suites"]:
            self.assertEqual(suite["scheduling_class"], "unknown-serial")
            self.assertGreaterEqual(suite["queue_wait"], 0)
            for shard in suite["shards"]:
                for field in ("queued_at", "started_at", "ended_at", "duration", "queue_wait", "collected", "executed", "outcome"):
                    self.assertIn(field, shard)

    def test_proven_safe_suite_runs_before_queued_unknown_serial_suite(self):
        marker = Path(self.tmp.name) / "unknown-started"
        self.write_suite(
            "test_a_unknown.py",
            "import time\nfrom pathlib import Path\n"
            f"def test_shared_path_write():\n    Path({str(marker)!r}).write_text('started')\n    time.sleep(.1)\n",
        )
        self.write_suite(
            "test_z_safe.py",
            "import time\n"
            "def test_read_only_work():\n    time.sleep(.2)\n",
        )

        result = self.run_runner("--workers", "4", timeout=8)

        self.assertEqual(result.returncode, 0, result.stderr)
        suites = {suite["source_suite"]: suite for suite in self.read_report()["suites"]}
        unknown = suites["scripts/test_a_unknown.py"]
        safe = suites["scripts/test_z_safe.py"]
        self.assertEqual(unknown["scheduling_class"], "unknown-serial")
        self.assertEqual(safe["scheduling_class"], "read-only")
        self.assertTrue(marker.is_file())
        self.assertLess(safe["started_at"], unknown["started_at"])
        self.assertLessEqual(safe["ended_at"], unknown["started_at"])

    def test_source_waiting_for_worker_slot_does_not_spend_its_script_budget(self):
        self.write_suite(
            "test_a_slow.py",
            "import time\n"
            "def test_slow(): time.sleep(2)\n",
        )
        self.write_suite(
            "test_b_fast.py",
            "def test_fast(): assert True\n",
        )

        result = self.run_runner(
            "--workers", "1", "--per-script-timeout", "1.0",
            "--suite-timeout", "5", "--cleanup-grace", "0.1", timeout=8,
        )

        self.assertNotEqual(result.returncode, 0, "the intentionally slow source must time out")
        suites = {suite["source_suite"]: suite for suite in self.read_report()["suites"]}
        self.assertEqual(suites["scripts/test_a_slow.py"]["outcome"], "timeout")
        self.assertEqual(suites["scripts/test_b_fast.py"]["outcome"], "passed")
        self.assertGreater(suites["scripts/test_b_fast.py"]["queue_wait"], 0.8)

    def test_unknown_suite_parallelizes_only_proven_independent_class_shards(self):
        marker = Path(self.tmp.name) / "unsafe-started"
        safe_methods = "".join(
            f"    def test_safe_{index:02d}(self): time.sleep(.2)\n"
            for index in range(7)
        )
        self.write_suite(
            "test_serial_batch.py",
            "import os, tempfile, time, unittest\nfrom pathlib import Path\n"
            "class TestAUnsafe(unittest.TestCase):\n"
            "    def test_shared_path_write(self):\n"
            "        Path(os.environ['SHARED_MARKER']).write_text('unsafe')\n"
            "        time.sleep(.2)\n"
            "    def test_shared_path_write_again(self):\n"
            "        Path(os.environ['SHARED_MARKER']).write_text('unsafe again')\n"
            "        time.sleep(.2)\n"
            "    def test_shared_path_write_last(self):\n"
            "        Path(os.environ['SHARED_MARKER']).write_text('unsafe last')\n"
            "        time.sleep(.2)\n"
            "class TestBSafe(unittest.TestCase):\n"
            "    def setUp(self): self.tmp = tempfile.TemporaryDirectory()\n"
            "    def tearDown(self): self.tmp.cleanup()\n"
            + safe_methods,
        )

        result = self.run_runner(
            "--suite", "test_serial_batch.py", "--workers", "4",
            env={"SHARED_MARKER": str(marker)}, timeout=8,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        report = self.read_report()
        suite = report["suites"][0]
        self.assertEqual(suite["scheduling_class"], "unknown-serial")
        shards = {shard["shard_id"]: shard for shard in suite["shards"]}
        unsafe = shards["test_serial_batch.TestAUnsafe"]
        safe = [shard for name, shard in shards.items()
                if name.startswith("unittest-method-batch-")]
        safe_ids = [test_id for shard in safe for test_id in shard["test_ids"]]
        self.assertEqual(len(unsafe["test_ids"]), 3, "unsafe methods must stay grouped")
        self.assertEqual(len(safe), 3, "safe methods should use one balanced batch per available worker")
        self.assertEqual(sorted(len(shard["test_ids"]) for shard in safe), [2, 2, 3])
        self.assertEqual(len(safe_ids), 7)
        self.assertEqual(len(safe_ids), len(set(safe_ids)))
        shard_ids = [test_id for shard in suite["shards"] for test_id in shard["test_ids"]]
        executed_ids = [test_id for shard in suite["shards"] for test_id in shard["executed_ids"]]
        self.assertEqual(len(shard_ids), len(set(shard_ids)))
        self.assertCountEqual(shard_ids, suite["collected_ids"])
        self.assertEqual(len(executed_ids), len(set(executed_ids)))
        self.assertCountEqual(executed_ids, suite["collected_ids"])
        self.assertLessEqual(report["max_active_children"], 4)
        self.assertTrue(marker.is_file())
        self.assertTrue(all(shard["outcome"] == "passed" for shard in shards.values()))
        self.assertTrue(any(
            shard["started_at"] < unsafe["ended_at"]
            and shard["ended_at"] > unsafe["started_at"]
            for shard in safe
        ), "a whole unsafe class may overlap proven-isolated class shards")

    def test_global_deadline_and_signal_cancellation_write_complete_partial_reports(self):
        marker = Path(self.tmp.name) / "started"
        pidfile = Path(self.tmp.name) / "signal-descendant.pid"
        self.write_suite(
            "test_slow.py",
            "import json, os, signal, subprocess, sys, time\nfrom pathlib import Path\n"
            "def test_slow():\n"
            "    child = subprocess.Popen([sys.executable, '-c', "
            "'import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(300)'])\n"
            f"    Path({str(pidfile)!r}).write_text(json.dumps({{'pid': child.pid, 'pgid': os.getpgid(child.pid)}}))\n"
            "    Path(os.environ['START_MARKER']).write_text('started')\n"
            "    time.sleep(20)\n",
        )
        result = self.run_runner(
            "--suite", "test_slow.py", "--workers", "1", "--per-script-timeout", "5",
            "--suite-timeout", "1", env={"START_MARKER": str(marker)}, timeout=5,
        )
        self.assertNotEqual(result.returncode, 0)
        report = self.read_report()
        self.assertTrue(report["report_complete"])
        self.assertIn(report["suites"][0]["outcome"], {"timeout", "cancelled"})
        deadline_child = json.loads(pidfile.read_text())
        self.assert_process_group_reaped(deadline_child)

        self.report.unlink(missing_ok=True)
        marker.unlink(missing_ok=True)
        pidfile.unlink(missing_ok=True)
        waiting_marker = Path(self.tmp.name) / "waiting-suite-ran"
        self.write_suite(
            "test_waiting.py",
            "from pathlib import Path\n"
            "def test_never_started():\n"
            f"    Path({str(waiting_marker)!r}).write_text('ran')\n",
        )
        env = dict(os.environ)
        env["AI_PLAYBOOK_TEST_VENV"] = str(Path(sys.executable).parent)
        env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
        env["START_MARKER"] = str(marker)
        for cancellation_signal in (signal.SIGTERM, signal.SIGINT):
            with self.subTest(signal=cancellation_signal.name):
                self.report.unlink(missing_ok=True)
                marker.unlink(missing_ok=True)
                pidfile.unlink(missing_ok=True)
                child = subprocess.Popen(
                    [sys.executable, str(RUNNER), "--repo-root", str(self.repo), "--json-report", str(self.report),
                     "--workers", "1", "--per-script-timeout", "10", "--suite-timeout", "15"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env,
                )
                deadline = time.monotonic() + 5
                while not marker.exists() and time.monotonic() < deadline and child.poll() is None:
                    time.sleep(.02)
                self.assertTrue(marker.exists(), "active suite should start before signal")
                child.send_signal(cancellation_signal)
                stdout, stderr = child.communicate(timeout=5)
                self.assertNotEqual(child.returncode, 0, (stdout, stderr))
                report = self.read_report()
                self.assertTrue(report["partial"])
                self.assertTrue(report["report_complete"])
                suite_outcomes = {
                    Path(suite["source_suite"]).name: suite["outcome"]
                    for suite in report["suites"]
                }
                self.assertEqual(
                    suite_outcomes,
                    {"test_slow.py": "cancelled", "test_waiting.py": "cancelled"},
                )
                self.assertFalse(waiting_marker.exists(), "the queued suite must not run after cancellation")
                signal_child = json.loads(pidfile.read_text())
                self.assert_process_group_reaped(signal_child)

    def assert_process_group_reaped(self, process_identity):
        pid = process_identity["pid"]
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        state = subprocess.run(
            ["ps", "-o", "pid=,ppid=,pgid=,state=,command=", "-p", str(pid)],
            capture_output=True, text=True,
        )
        try:
            self.assertEqual(state.returncode, 0, f"ps failed: {state.stderr.strip()}")
            fields = state.stdout.strip().split()
            if fields:
                self.assertEqual(fields[0], str(pid), state.stdout.strip())
                self.assertTrue(fields[3].startswith("Z"),
                                f"descendant is still live: {state.stdout.strip()} identity={process_identity}")
            else:
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    return
                self.fail(f"process snapshot omitted a live descendant: {process_identity}")
        finally:
            try:
                os.killpg(process_identity["pgid"], signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass

    def test_successful_child_exit_reaps_detached_descendant(self):
        pidfile = Path(self.tmp.name) / "successful-new-session-descendant.json"
        self.write_suite(
            "test_detached_success.py",
            "import json, os, subprocess, sys\nfrom pathlib import Path\n"
            "def test_ok():\n"
            "    child = subprocess.Popen([sys.executable, '-c', "
            "'import time; time.sleep(300)'], start_new_session=True, "
            "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
            f"    Path({str(pidfile)!r}).write_text(json.dumps("
            "{'pid': child.pid, 'pgid': os.getpgid(child.pid)}))\n",
        )
        result = self.run_runner(
            "--suite", "test_detached_success.py", "--workers", "1",
            "--per-script-timeout", "5", "--suite-timeout", "8",
            "--cleanup-grace", "0.5", timeout=12,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = self.read_report()
        self.assertEqual(report["suites"][0]["outcome"], "passed")
        self.assertTrue(pidfile.exists())
        self.assert_process_group_reaped(json.loads(pidfile.read_text()))

    def test_process_reaping_assertion_rejects_failed_ps_snapshot(self):
        child = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            start_new_session=True,
        )
        identity = {"pid": child.pid, "pgid": os.getpgid(child.pid)}
        try:
            with patch("subprocess.run", return_value=subprocess.CompletedProcess(
                args=["ps"], returncode=1, stdout="", stderr="ps unavailable",
            )):
                with self.assertRaises(AssertionError):
                    self.assert_process_group_reaped(identity)
        finally:
            child.wait(timeout=2)

    def test_worker_cleanup_retries_a_transient_process_snapshot_failure(self):
        import run_required_test_suite as runner_module

        child = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            start_new_session=True,
        )
        original_snapshot = runner_module._worker_process_groups
        calls = 0

        def fail_once(root_pid, *, timeout):
            nonlocal calls
            calls += 1
            if calls == 1:
                return set(), "worker process-tree snapshot failed: transient"
            return original_snapshot(root_pid, timeout=timeout)

        try:
            with patch.object(runner_module, "_worker_process_groups", side_effect=fail_once):
                result = runner_module._cleanup_worker_descendants(1.0)
            self.assertIsNone(result)
            self.assertEqual(calls, 2)
            self.assertIsNotNone(
                child.poll(), "cleanup retry returned while the detached child was still running",
            )
        finally:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=2)

    def test_worker_exception_still_cleans_detached_child(self):
        import io
        from contextlib import redirect_stdout
        import run_required_test_suite as runner_module

        source = self.write_suite("test_worker_exception.py", "def test_one():\n    assert True\n")
        child = None

        def fail_after_starting_child(*_args):
            nonlocal child
            child = subprocess.Popen(
                [sys.executable, "-c", "import time; time.sleep(30)"],
                start_new_session=True,
            )
            raise RuntimeError("worker operation failed")

        output = io.StringIO()
        try:
            with patch.object(runner_module, "_run_unittest_shard", side_effect=fail_after_starting_child):
                with redirect_stdout(output):
                    result = runner_module._worker_main([
                        "--_worker", "run", "--_repo-root", str(self.repo),
                        "--_source", str(source), "--_policy", "unittest",
                        "--_shard", "test_one", "--_test-ids", "[]",
                        "--_cleanup-grace", "1",
                    ])
            self.assertEqual(result, 1)
            payload = json.loads(output.getvalue().removeprefix(runner_module.MARKER))
            self.assertEqual(payload["error"], "RuntimeError: worker operation failed")
            self.assertIsNotNone(child.poll(), "exception path left a detached child running")
        finally:
            if child is not None and child.poll() is None:
                child.kill()
                child.wait(timeout=2)

    def test_worker_exception_preserves_cleanup_error_in_result(self):
        import io
        from contextlib import redirect_stdout
        import run_required_test_suite as runner_module

        source = self.write_suite("test_worker_cleanup_error.py", "def test_one():\n    assert True\n")
        output = io.StringIO()
        with patch.object(runner_module, "_run_unittest_shard", side_effect=RuntimeError("worker failed")), patch.object(
            runner_module, "_cleanup_worker_descendants", return_value="cleanup failed",
        ), redirect_stdout(output):
            result = runner_module._worker_main([
                "--_worker", "run", "--_repo-root", str(self.repo),
                "--_source", str(source), "--_policy", "unittest",
                "--_shard", "test_one", "--_test-ids", "[]",
                "--_cleanup-grace", "1",
            ])

        payload = json.loads(output.getvalue().removeprefix(runner_module.MARKER))
        self.assertEqual(result, 1)
        self.assertEqual(payload["error"], "RuntimeError: worker failed")
        self.assertEqual(payload["cleanup_error"], "cleanup failed")

    def test_child_timeout_kills_a_term_ignoring_new_session_descendant(self):
        pidfile = Path(self.tmp.name) / "new-session-descendant.json"
        fake_bin = Path(self.tmp.name) / "fake-bin"
        fake_bin.mkdir()
        ps_marker = Path(self.tmp.name) / "ps-failure-attempts"
        fake_ps = fake_bin / "ps"
        fake_ps.write_text(
            "#!/bin/sh\n"
            "printf 'failed\\n' >> \"$PS_FAILURE_LOG\"\n"
            "exit 1\n",
            encoding="utf-8",
        )
        fake_ps.chmod(0o755)
        self.write_suite(
            "test_detached_timeout.py",
            "import json, os, signal, subprocess, sys, time\nfrom pathlib import Path\n"
            "def test_slow():\n"
            "    child = subprocess.Popen([sys.executable, '-c', "
            "'import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(300)'], "
            "start_new_session=True)\n"
            f"    Path({str(pidfile)!r}).write_text(json.dumps({{'pid': child.pid, 'pgid': os.getpgid(child.pid)}}))\n"
            "    time.sleep(30)\n",
        )
        result = self.run_runner(
            "--suite", "test_detached_timeout.py", "--workers", "1",
            "--per-script-timeout", "2", "--suite-timeout", "6",
            "--cleanup-grace", "1", timeout=10,
            env={
                "PATH": str(fake_bin) + os.pathsep + os.environ.get("PATH", ""),
                "PS_FAILURE_LOG": str(ps_marker),
            },
        )
        self.assertNotEqual(result.returncode, 0)
        report = self.read_report()
        self.assertTrue(report["report_complete"])
        suite = report["suites"][0]
        self.assertEqual(suite["outcome"], "timeout", suite)
        self.assertTrue(suite["report_complete"])
        self.assertTrue(pidfile.exists())
        self.assertTrue(ps_marker.exists(), "the PATH-selected process-tree snapshot should fail")
        # The stub fails persistently. The runner may move to its independent
        # system-path fallback early when the cleanup deadline is tight.
        self.assertNotIn("process-tree snapshot", suite["shards"][0]["output_tail"])
        self.assert_process_group_reaped(json.loads(pidfile.read_text()))


if __name__ == "__main__":
    unittest.main()
