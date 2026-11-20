#!/usr/bin/env python3
"""Tests for the consult-path profiling harness (plan 2026-11-09-hook-timeout-
recurrence-diagnostic, Task 1).

Covers the Task-1 REPOSITORY_TEST checklist: the core's opt-in timing
emission, the through-adapter witness, decision-byte identity (unset vs set
timing variable), the sandbox self-check abort arms, the degraded-path
classifier negative arms (one fixture per Terms disjunct), aggregation over
clean samples only, the dominance helper's negative cases, suite/run
hermeticity, matched-control load-mode retention, the clean-sample floor and
rerun budget, class forcing, the worker ceiling, and the analyze-mode record.

Fixtures are hermetic: every consult runs under a temporary HOME with
cleared session/GIT_* variables against a temp git fixture repo; the real
``~/.ai-playbook/logs/hooks.log`` is only READ (size snapshots) to witness
that no consult leaked into it. No absolute personal path is embedded.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import profile_skill_gate_consult as psgc  # noqa: E402
import skill_gate  # noqa: E402

BLOCK_MESSAGE = skill_gate.BLOCK_MESSAGE


def sha16(path) -> str:
    """The project key facts_paths.resolve_project_key derives for a git repo."""
    return hashlib.sha1(os.path.realpath(str(path)).encode()).hexdigest()[:16]


def make_profiler(tmp, **kw) -> "psgc.ConsultProfiler":
    out = Path(tmp) / "out"
    out.mkdir(parents=True, exist_ok=True)
    kw.setdefault("output_dir", out)
    kw.setdefault("worktree_root", psgc.REPO_ROOT)
    return psgc.ConsultProfiler(**kw)


def real_hooks_log_state():
    """(exists, size) of the REAL hooks log, for leak snapshots."""
    p = Path.home() / ".ai-playbook" / "logs" / "hooks.log"
    if p.is_file():
        return True, p.stat().st_size
    return False, 0


def assert_real_hooks_log_untouched(test, before):
    test.assertEqual(real_hooks_log_state(), before)


# --------------------------------------------------------------------------- #
# Timing emission (IMPLEMENTATION_REQUIRED checklist item).
# --------------------------------------------------------------------------- #
class TimingEmissionTests(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.tmp = Path(self._td.name)
        self.profiler = make_profiler(self.tmp)

    def tearDown(self):
        self._td.cleanup()

    def _core_run(self, sandbox, *, emission, class_name):
        timing_path = sandbox["timing_dir"] / "probe.json"
        if timing_path.exists():
            timing_path.unlink()
        nonce = "nonce-abc-123"
        env = self.profiler.worker_env(
            sandbox, emission=emission, timing_path=timing_path, nonce=nonce
        )
        argv = [
            sys.executable,
            str(sandbox["scripts_core"]),
            "--target", str(sandbox["target"]),
            "--cwd", str(sandbox["fixture"]),
        ]
        proc = subprocess.run(
            argv, capture_output=True, env=env,
            cwd=str(sandbox["fixture"]), timeout=30,
        )
        record = None
        if timing_path.is_file():
            record = json.loads(timing_path.read_text(encoding="utf-8"))
        return proc, record, nonce, timing_path

    def test_emission_on_writes_record_after_decision_with_nonce(self):
        for class_name, seed in (("allow", True), ("block", False)):
            with self.subTest(class_name=class_name):
                sandbox = self.profiler.build_sandbox(class_name, worker_id=0)
                if seed:
                    self.profiler.seed_allow_marker(sandbox)
                proc, record, nonce, timing_path = self._core_run(
                    sandbox, emission=True, class_name=class_name
                )
                self.assertEqual(proc.returncode, 0)
                self.assertIsNotNone(record, "timing record missing")
                self.assertEqual(record["nonce"], nonce)
                self.assertIsInstance(record["pid"], int)
                self.assertNotEqual(record["pid"], os.getpid())
                for stage in psgc.CORE_TIMING_STAGES:
                    self.assertIn(stage, record["stages"], stage)
                    self.assertIsInstance(record["stages"][stage], float)
                # stdout is EXACTLY the decision JSON - nothing of the record.
                decision = json.loads(proc.stdout.decode("utf-8"))
                self.assertEqual(decision["allow_tool"], class_name == "allow")

    def test_emission_off_writes_nothing(self):
        sandbox = self.profiler.build_sandbox("block", worker_id=0)
        proc, record, _nonce, timing_path = self._core_run(
            sandbox, emission=False, class_name="block"
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIsNone(record, "no timing file expected with the variable unset")
        self.assertFalse(timing_path.exists())

    def test_record_never_on_stdout_or_stderr(self):
        sandbox = self.profiler.build_sandbox("block", worker_id=0)
        proc, record, _nonce, _timing_path = self._core_run(
            sandbox, emission=True, class_name="block"
        )
        self.assertIsNotNone(record)
        stderr_text = proc.stderr.decode("utf-8")
        self.assertEqual(stderr_text, "")
        self.assertNotIn("nonce", proc.stdout.decode("utf-8"))
        self.assertNotIn('"stages"', proc.stdout.decode("utf-8"))


# --------------------------------------------------------------------------- #
# Decision-byte identity witness (REPOSITORY_TEST).
# --------------------------------------------------------------------------- #
class DecisionByteIdentityTests(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.tmp = Path(self._td.name)
        self.profiler = make_profiler(self.tmp)

    def tearDown(self):
        self._td.cleanup()

    def _identity(self, class_name, seed):
        sandbox = self.profiler.build_sandbox(class_name, worker_id=0)
        if seed:
            self.profiler.seed_allow_marker(sandbox)
        argv = [
            sys.executable,
            str(sandbox["scripts_core"]),
            "--target", str(sandbox["target"]),
            "--cwd", str(sandbox["fixture"]),
        ]
        runs = []
        for emission in (False, True):
            timing_path = sandbox["timing_dir"] / f"id-{int(emission)}.json"
            if timing_path.exists():
                timing_path.unlink()
            env = self.profiler.worker_env(
                sandbox, emission=emission, timing_path=timing_path, nonce="idn"
            )
            proc = subprocess.run(
                argv, capture_output=True, env=env,
                cwd=str(sandbox["fixture"]), timeout=30,
            )
            runs.append((proc.returncode, proc.stdout, proc.stderr, timing_path))
        (rc_off, out_off, err_off, t_off), (rc_on, out_on, err_on, t_on) = runs
        self.assertEqual(rc_off, rc_on, "exit code changed by the timing variable")
        self.assertEqual(out_off, out_on, "decision stdout bytes changed")
        self.assertEqual(err_off, err_on, "stderr changed")
        self.assertFalse(t_off.exists())
        self.assertTrue(t_on.exists(), "timing record expected only in the timed run")
        return json.loads(out_on.decode("utf-8"))

    def test_allow_shape_byte_identical(self):
        decision = self._identity("allow", seed=True)
        self.assertTrue(decision["allow_tool"])

    def test_block_shape_byte_identical(self):
        decision = self._identity("block", seed=False)
        self.assertFalse(decision["allow_tool"])
        self.assertEqual(decision["deny_reason"], BLOCK_MESSAGE)


# --------------------------------------------------------------------------- #
# Through-adapter witness (REPOSITORY_TEST).
# --------------------------------------------------------------------------- #
class ThroughAdapterWitnessTests(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.tmp = Path(self._td.name)
        self.profiler = make_profiler(self.tmp)

    def tearDown(self):
        self._td.cleanup()

    def test_adapter_chain_emits_timing_record_with_nonce(self):
        before = real_hooks_log_state()
        for class_name, seed, want_rc in (
            ("allow", True, 0),
            ("block", False, 2),
        ):
            with self.subTest(class_name=class_name):
                sandbox = self.profiler.build_sandbox(class_name, worker_id=0)
                if seed:
                    self.profiler.seed_allow_marker(sandbox)
                sample = self.profiler.measure_consult(
                    sandbox, class_name=class_name, worker_id=0,
                    iteration=0, probes={}, emission=True,
                    kind="witness", repeat=0, rerun=0,
                )
                self.assertTrue(sample["timing_nonce_ok"], "nonce not echoed")
                self.assertTrue(Path(sample["timing_path"]).is_file())
                record = json.loads(
                    Path(sample["timing_path"]).read_text(encoding="utf-8")
                )
                self.assertIn("nonce", record)
                # Keying line landed in the SANDBOX hooks log (project-only,
                # the empty branch), and the real hooks log was untouched.
                self.assertTrue(sample["keying_values"], "no keying line")
                self.assertEqual(sample["keying_values"][0], "project-only")
                self.assertEqual(sample["keying_branch"], "empty")
                self.assertEqual(sample["exit_code"], want_rc)
        assert_real_hooks_log_untouched(self, before)


# --------------------------------------------------------------------------- #
# ConsultProfiler single-consult measurement (IMPLEMENTATION_REQUIRED).
# --------------------------------------------------------------------------- #
class ConsultMeasurementTests(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.tmp = Path(self._td.name)
        self.profiler = make_profiler(self.tmp)

    def tearDown(self):
        self._td.cleanup()

    def test_sample_carries_stage_vocabulary_and_context(self):
        for class_name, seed in (("allow", True), ("block", False)):
            with self.subTest(class_name=class_name):
                sandbox = self.profiler.build_sandbox(class_name, worker_id=0)
                if seed:
                    self.profiler.seed_allow_marker(sandbox)
                probes = self.profiler.run_stage_probes(sandbox)
                sample = self.profiler.measure_consult(
                    sandbox, class_name=class_name, worker_id=0,
                    iteration=1, probes=probes, emission=True,
                    kind="probe", repeat=0, rerun=0,
                )
                self.assertEqual(sample["class"], class_name)
                self.assertEqual(sample["status"], "clean", sample)
                self.assertGreater(sample["e2e_s"], 0.0)
                for stage in psgc.CORE_TIMING_STAGES:
                    self.assertIn(stage, sample["stages"], stage)
                for stage in ("payload_extract", "session_channel",
                              "decision_parse", "interpreter_probe"):
                    self.assertIn(stage, sample["probe_stages"], stage)
                self.assertEqual(sample["outcome"], class_name)
                self.assertEqual(sample["keying_branch"], "empty")
                self.assertEqual(sample["project_key"], sha16(sandbox["fixture"]))
                self.assertEqual(sample["cwd"], str(sandbox["fixture"]))
                self.assertEqual(sample["target"], str(sandbox["target"]))

    def test_pre_run_class_check_aborts_on_contradiction(self):
        # A block-class sandbox that is (wrongly) seeded must abort loudly.
        sandbox = self.profiler.build_sandbox("block", worker_id=0)
        self.profiler.seed_allow_marker(sandbox)
        with self.assertRaises(psgc.SelfCheckError):
            self.profiler.pre_run_class_check(sandbox)


# --------------------------------------------------------------------------- #
# Sandbox startup self-check abort arms (REPOSITORY_TEST).
# --------------------------------------------------------------------------- #
class SelfCheckAbortTests(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.tmp = Path(self._td.name)
        self.profiler = make_profiler(self.tmp)
        # Control: an untouched sandbox passes every arm.
        self.sandbox = self.profiler.build_sandbox("block", worker_id=0)
        self.profiler.run_self_checks(self.sandbox)

    def tearDown(self):
        self._td.cleanup()

    def test_plain_file_sandbox_core_aborts(self):
        core = self.sandbox["scripts_core"]
        core.unlink()
        shutil.copyfile(psgc.REPO_ROOT / "scripts" / "skill_gate.py", core)
        with self.assertRaises(psgc.SelfCheckError) as ctx:
            self.profiler.run_self_checks(self.sandbox)
        self.assertIn("symlink", str(ctx.exception))

    def test_missing_gated_target_aborts(self):
        self.sandbox["target"].unlink()
        with self.assertRaises(psgc.SelfCheckError) as ctx:
            self.profiler.run_self_checks(self.sandbox)
        self.assertIn("target", str(ctx.exception))

    def test_non_git_fixture_aborts(self):
        shutil.rmtree(self.sandbox["fixture"] / ".git")
        with self.assertRaises(psgc.SelfCheckError) as ctx:
            self.profiler.run_self_checks(self.sandbox)
        self.assertIn("git", str(ctx.exception))

    def test_doctored_adapter_copy_aborts(self):
        replica = self.profiler.derive_adapter_stage_replica()
        self.assertIn("bodies", replica, "control derivation must pass")
        doctored = Path(self._td.name) / "doctored-claude.sh"
        text = psgc.ADAPTER_PATH.read_text(encoding="utf-8")
        # Plant an extra python3 subprocess stage into the adapter copy.
        text = text.replace(
            'payload="$(cat)"',
            'payload="$(cat)"\nDOCTOR="$(python3 -c \'print("x")\')"',
        )
        doctored.write_text(text, encoding="utf-8")
        profiler = make_profiler(self.tmp, adapter_path=doctored)
        with self.assertRaises(psgc.SelfCheckError):
            profiler.derive_adapter_stage_replica()


# --------------------------------------------------------------------------- #
# Degraded-path classifier negative arms (REPOSITORY_TEST).
# --------------------------------------------------------------------------- #
def base_sample(**overrides):
    class_name = overrides.pop("class_name", None)
    sample = {
        "class": "allow",
        "e2e_s": 0.3,
        "timed_out": False,
        "exit_code": 0,
        "stderr": "",
        "emission": True,
        "timing_nonce_ok": True,
        "keying_values": ["project-only"],
        "keying_branch": "empty",
        "decision_readable": True,
        "resolver_stage_s": 0.01,
        "resolver_probe_timed_out": False,
        "stages": {"marker_check": 0.01},
        "probe_stages": {"payload_extract": 0.02, "session_channel": 0.02,
                         "decision_parse": 0.02, "interpreter_probe": 0.02},
        "status": "clean",
        "degraded_label": "",
        "iteration": 0,
    }
    if class_name is not None:
        sample["class"] = class_name
    sample.update(overrides)
    return sample


class ClassifierNegativeArmTests(unittest.TestCase):
    def _classify(self, sample):
        return psgc.classify_sample(sample)

    def test_clean_sample_is_clean(self):
        status, label, _ = self._classify(base_sample())
        self.assertEqual((status, label), ("clean", ""))

    def test_per_consult_timeout_is_timed_out(self):
        sample = base_sample(timed_out=True, exit_code=None, timing_nonce_ok=False,
                             keying_values=[], decision_readable=False)
        status, label, _ = self._classify(sample)
        self.assertEqual((status, label), ("degraded", "timed-out"))

    def test_no_anchor_is_resolver_failed(self):
        sample = base_sample(keying_values=["project-only", "no-anchor"],
                             resolver_stage_s=0.02)
        status, label, _ = self._classify(sample)
        self.assertEqual((status, label), ("degraded", "resolver-failed"))

    def test_no_anchor_at_five_second_bound_is_resolver_timeout(self):
        sample = base_sample(keying_values=["project-only", "no-anchor"],
                             resolver_stage_s=psgc.RESOLVER_BOUND_S)
        status, label, _ = self._classify(sample)
        self.assertEqual((status, label), ("degraded", "resolver-timeout"))

    def test_no_anchor_probe_timeout_is_resolver_timeout(self):
        sample = base_sample(keying_values=["project-only", "no-anchor"],
                             resolver_stage_s=None, resolver_probe_timed_out=True)
        status, label, _ = self._classify(sample)
        self.assertEqual((status, label), ("degraded", "resolver-timeout"))

    def test_fail_open_keying_is_fail_open(self):
        sample = base_sample(keying_values=["project-only", "fail-open"])
        status, label, _ = self._classify(sample)
        self.assertEqual((status, label), ("degraded", "fail-open"))

    def test_error_keying_is_fail_open(self):
        sample = base_sample(keying_values=["project-only", "error"])
        status, label, _ = self._classify(sample)
        self.assertEqual((status, label), ("degraded", "fail-open"))

    def test_missing_keying_line_is_unreadable(self):
        sample = base_sample(keying_values=[])
        status, label, detail = self._classify(sample)
        self.assertEqual((status, label), ("degraded", "unreadable"))
        self.assertIn("keying", detail.get("reason", ""))

    def test_adapter_fail_open_unreadable_decision_is_unreadable(self):
        # Core never ran: allow-class adapter fail-open (exit 0) with no
        # keying line - the Terms "adapter-level fail-open" arm.
        sample = base_sample(keying_values=[], decision_readable=True)
        status, label, _ = self._classify(sample)
        self.assertEqual((status, label), ("degraded", "unreadable"))

    def test_block_contract_violation_is_unreadable(self):
        sample = base_sample(class_name="block", exit_code=0, stderr="")
        sample["decision_readable"] = psgc.adapter_decision_readable(
            "block", 0, ""
        )
        self.assertFalse(sample["decision_readable"])
        status, label, _ = self._classify(sample)
        self.assertEqual((status, label), ("degraded", "unreadable"))

    def test_missing_timing_witness_is_unreadable(self):
        sample = base_sample(timing_nonce_ok=False)
        status, label, detail = self._classify(sample)
        self.assertEqual((status, label), ("degraded", "unreadable"))
        self.assertIn("timing", detail.get("reason", ""))

    def test_emission_off_skips_timing_witness(self):
        sample = base_sample(emission=False, timing_nonce_ok=None)
        status, label, _ = self._classify(sample)
        self.assertEqual((status, label), ("clean", ""))


# --------------------------------------------------------------------------- #
# Aggregation over clean samples only (REPOSITORY_TEST).
# --------------------------------------------------------------------------- #
class AggregationTests(unittest.TestCase):
    def test_mixed_clean_and_degraded_aggregates_clean_only(self):
        clean_allow = [
            base_sample(iteration=i, e2e_s=1.0 + i * 0.1,
                        stages={"marker_check": 0.5},
                        probe_stages={"payload_extract": 0.05,
                                      "session_channel": 0.05,
                                      "decision_parse": 0.05,
                                      "interpreter_probe": 0.02})
            for i in range(4)
        ]
        clean_allow[0]["e2e_s"] = 2.0  # clean max
        clean_block = [
            base_sample(class_name="block", iteration=i, e2e_s=0.4,
                        stages={"marker_check": 0.01},
                        probe_stages={"payload_extract": 0.02,
                                      "session_channel": 0.02,
                                      "decision_parse": 0.02,
                                      "interpreter_probe": 0.02})
            for i in range(3)
        ]
        degraded = [
            base_sample(class_name="block", iteration=9, e2e_s=99.0,
                        status="degraded", degraded_label="timed-out"),
            base_sample(class_name="allow", iteration=10, e2e_s=98.0,
                        status="degraded", degraded_label="fail-open"),
        ]
        agg = psgc.aggregate_clean(clean_allow + clean_block + degraded)
        self.assertEqual(agg["by_class"]["allow"]["count"], 4)
        self.assertEqual(agg["by_class"]["block"]["count"], 3)
        allow = agg["by_class"]["allow"]
        self.assertAlmostEqual(allow["p50"], 1.25, places=6)
        self.assertAlmostEqual(allow["max"], 2.0, places=6)
        self.assertGreater(allow["p95"], allow["p50"])
        # Degraded 99.0/98.0 maxes must NOT leak into clean statistics.
        self.assertLess(agg["by_class"]["block"]["max"], 99.0)
        self.assertEqual(agg["degraded_counts"].get("timed-out"), 1)
        self.assertEqual(agg["degraded_counts"].get("fail-open"), 1)
        # Stage share uses clean samples' stage p95 over the class e2e p95.
        self.assertAlmostEqual(
            allow["stage_shares"]["marker_check"],
            psgc.percentile([0.5] * 4, 0.95) / psgc.percentile(
                [s["e2e_s"] for s in clean_allow], 0.95),
            places=6,
        )
        self.assertIn("residual", allow["stage_shares"])

    def test_percentile_endpoints(self):
        self.assertEqual(psgc.percentile([3.0], 0.95), 3.0)
        self.assertEqual(psgc.percentile([1.0, 2.0, 3.0, 4.0], 0.0), 1.0)
        self.assertEqual(psgc.percentile([1.0, 2.0, 3.0, 4.0], 1.0), 4.0)


# --------------------------------------------------------------------------- #
# Dominance helper (REPOSITORY_TEST).
# --------------------------------------------------------------------------- #
class DominanceTests(unittest.TestCase):
    def test_dominant_when_floor_and_ratio_met(self):
        shares = {"marker_check": 0.6, "payload_extract": 0.2, "residual": 0.2}
        stage, fields = psgc.stage_dominant_in_class(shares)
        self.assertEqual(stage, "marker_check")
        self.assertIsNone(fields["failing_bound"])
        self.assertEqual(fields["runner_up"], 0.2)

    def test_forty_percent_but_not_twice_is_no_dominant(self):
        shares = {"marker_check": 0.42, "payload_extract": 0.30, "residual": 0.28}
        stage, fields = psgc.stage_dominant_in_class(shares)
        self.assertIsNone(stage)
        self.assertEqual(fields["failing_bound"], "ratio")

    def test_twice_but_under_forty_is_no_dominant(self):
        # Top share is >= 2x the runner-up yet still under the 40% floor.
        shares = {"marker_check": 0.39, "session_channel": 0.19,
                  "payload_extract": 0.14, "decision_parse": 0.10,
                  "residual": 0.18}
        stage, fields = psgc.stage_dominant_in_class(shares)
        self.assertIsNone(stage)
        self.assertEqual(fields["failing_bound"], "floor")
        self.assertGreaterEqual(fields["share"], 2 * fields["runner_up"])

    def test_under_floor_altogether_is_no_dominant(self):
        shares = {"marker_check": 0.25, "session_channel": 0.25,
                  "payload_extract": 0.25, "decision_parse": 0.10,
                  "residual": 0.15}
        stage, fields = psgc.stage_dominant_in_class(shares)
        self.assertIsNone(stage)
        self.assertEqual(fields["failing_bound"], "floor")

    def test_dominant_in_both_classes_is_dominant(self):
        verdict = psgc.dominance_verdict({
            "allow": {"marker_check": 0.6, "payload_extract": 0.2, "residual": 0.2},
            "block": {"marker_check": 0.7, "payload_extract": 0.1, "residual": 0.2},
        })
        self.assertEqual(verdict["verdict"], "dominant")
        self.assertEqual(verdict["stage"], "marker_check")

    def test_dominant_in_one_class_only_is_no_dominant(self):
        verdict = psgc.dominance_verdict({
            "allow": {"marker_check": 0.6, "payload_extract": 0.2, "residual": 0.2},
            "block": {"marker_check": 0.3, "payload_extract": 0.3, "residual": 0.4},
        })
        self.assertEqual(verdict["verdict"], "no-dominant")
        self.assertEqual(verdict.get("reason"), "dominant-in-one-class-only")

    def test_no_dominant_when_neither_class_has_one(self):
        verdict = psgc.dominance_verdict({
            "allow": {"marker_check": 0.42, "payload_extract": 0.3, "residual": 0.28},
            "block": {"marker_check": 0.5, "session_channel": 0.3, "residual": 0.2},
        })
        self.assertEqual(verdict["verdict"], "no-dominant")
        self.assertEqual(verdict["per_class"]["allow"]["failing_bound"], "ratio")
        self.assertEqual(verdict["per_class"]["block"]["failing_bound"], "ratio")

    def test_single_class_input_is_degenerate_no_dominant(self):
        # One dominant class alone must NOT yield a dominant verdict: the
        # dominant stage is defined over BOTH decision-path classes (Terms).
        verdict = psgc.dominance_verdict({
            "allow": {"marker_check": 0.6, "payload_extract": 0.2, "residual": 0.2},
        })
        self.assertEqual(verdict["verdict"], "no-dominant")
        self.assertEqual(verdict["reason"], "degenerate-input-missing-class")
        self.assertEqual(verdict["missing_classes"], ["block"])

    def test_empty_shares_for_one_class_is_degenerate(self):
        verdict = psgc.dominance_verdict({
            "allow": {"marker_check": 0.6, "payload_extract": 0.2, "residual": 0.2},
            "block": {},
        })
        self.assertEqual(verdict["verdict"], "no-dominant")
        self.assertEqual(verdict["reason"], "degenerate-input-missing-class")
        self.assertEqual(verdict["missing_classes"], ["block"])

    def test_worse_run_governs_by_e2e_p95(self):
        worse = psgc.worse_run_select([
            {"class": "allow", "repeat": 0, "rerun": 0, "e2e_p95_s": 1.0},
            {"class": "allow", "repeat": 1, "rerun": 0, "e2e_p95_s": 1.5},
        ])
        self.assertEqual(worse["repeat"], 1)

    def test_session_channel_correction_kills_false_dominance(self):
        shares = {"session_channel": 0.5, "payload_extract": 0.2,
                  "decision_parse": 0.2, "interpreter_probe": 0.2,
                  "residual": 0.1}
        corrected = psgc.session_channel_corrected_shares(shares)
        self.assertAlmostEqual(corrected["session_channel"], 0.3, places=6)
        stage, _ = psgc.stage_dominant_in_class(corrected)
        self.assertIsNone(stage)
        self.assertEqual(
            psgc.stage_candidate("session_channel", "session_channel", shares),
            "no-candidate",
        )

    def test_session_channel_still_dominant_maps_to_b(self):
        shares = {"session_channel": 0.6, "payload_extract": 0.1,
                  "decision_parse": 0.1, "interpreter_probe": 0.05,
                  "residual": 0.15}
        corrected = psgc.session_channel_corrected_shares(shares)
        stage, _ = psgc.stage_dominant_in_class(corrected)
        self.assertEqual(stage, "session_channel")
        self.assertEqual(
            psgc.stage_candidate("session_channel", "session_channel", shares),
            "(b)",
        )

    def test_stage_candidate_closed_mapping(self):
        shares = {"marker_check": 0.6, "payload_extract": 0.1,
                  "decision_parse": 0.1, "residual": 0.2}
        expected = {
            "keying_log_append": "no-candidate",
            "plans_dir_resolve": "no-candidate",
            "project_key_resolve": "no-candidate",
            "git_resolver": "no-candidate",
            "classify_target": "(c)",
            "session_derive": "(c)",
            "marker_check": "(c)",
            "payload_extract": "(a)",
            "decision_parse": "(a)",
            "residual": "(a)",
        }
        for stage, candidate in expected.items():
            self.assertEqual(
                psgc.stage_candidate(stage, "marker_check", shares),
                candidate,
                stage,
            )


# --------------------------------------------------------------------------- #
# Clean-sample floor and rerun budget.
# --------------------------------------------------------------------------- #
class FloorTests(unittest.TestCase):
    @staticmethod
    def _both_classes(n, **kw):
        samples = []
        for class_name in ("allow", "block"):
            samples.extend(
                base_sample(class_name=class_name, iteration=i, **kw)
                for i in range(n)
            )
        return samples

    def test_floor_met(self):
        samples = self._both_classes(20)
        status = psgc.floor_status(samples)
        self.assertTrue(status["met"])
        self.assertFalse(status["incident_regime_reached"])

    def test_floor_missed(self):
        samples = self._both_classes(19)
        samples.append(base_sample(iteration=19, status="degraded",
                                   degraded_label="unreadable"))
        status = psgc.floor_status(samples)
        self.assertFalse(status["met"])
        self.assertEqual(status["degraded_label_breakdown"].get("unreadable"), 1)
        self.assertFalse(status["incident_regime_reached"])

    def test_timeout_dominated_degraded_share_is_incident_regime(self):
        samples = self._both_classes(19)
        for i in range(5):
            samples.append(base_sample(iteration=20 + i, status="degraded",
                                       degraded_label="timed-out"))
        status = psgc.floor_status(samples)
        self.assertFalse(status["met"])
        self.assertTrue(status["incident_regime_reached"])

    def test_rerun_budget_is_two(self):
        self.assertEqual(psgc.MAX_REPEAT_RERUNS, 2)

    def test_run_floor_arm_harness_incident_raises(self):
        # Still under floor after the budget and the degraded share is NOT
        # timeout-dominated: the harness-incident arm fails loud.
        with tempfile.TemporaryDirectory() as td:
            profiler = make_profiler(td)
            status = {
                "met": False,
                "incident_regime_reached": False,
                "per_class": {
                    "allow": {"clean": 12, "floor": 20, "met": False},
                    "block": {"clean": 14, "floor": 20, "met": False},
                },
                "degraded_label_breakdown": {"unreadable": 3},
            }
            with self.assertRaises(psgc.SelfCheckError) as ctx:
                profiler._enforce_floor_after_reruns(status, 2)
            self.assertIn("harness incident", str(ctx.exception))
            self.assertIn("unreadable", str(ctx.exception))

    def test_run_floor_arm_timeout_dominated_records_incident_regime(self):
        # Still under floor after the budget with timed-out labels dominating
        # the degraded share: the incident regime is RECORDED, not raised.
        with tempfile.TemporaryDirectory() as td:
            profiler = make_profiler(td)
            status = {
                "met": False,
                "incident_regime_reached": True,
                "per_class": {
                    "allow": {"clean": 5, "floor": 20, "met": False},
                    "block": {"clean": 7, "floor": 20, "met": False},
                },
                "degraded_label_breakdown": {"timed-out": 29},
            }
            recorded = profiler._enforce_floor_after_reruns(status, 2)
            self.assertTrue(recorded["incident_regime_recorded"])
            self.assertEqual(recorded["reruns_used"], 2)


# --------------------------------------------------------------------------- #
# Worker ceiling.
# --------------------------------------------------------------------------- #
class WorkerCeilingTests(unittest.TestCase):
    def test_ceiling_is_physical_cores_minus_one(self):
        ceiling, derivation = psgc.host_worker_ceiling()
        self.assertGreaterEqual(ceiling, 1)
        self.assertTrue(derivation, "ceiling derivation must be recorded")

    def test_requested_above_ceiling_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            profiler = make_profiler(td, workers=10 ** 6)
            with self.assertRaises(psgc.SelfCheckError):
                profiler.resolve_workers()


# --------------------------------------------------------------------------- #
# Hermeticity (REPOSITORY_TEST).
# --------------------------------------------------------------------------- #
class HermeticityTests(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.tmp = Path(self._td.name)
        self.profiler = make_profiler(self.tmp)
        self.sandbox = self.profiler.build_sandbox("block", worker_id=0)

    def tearDown(self):
        self._td.cleanup()

    def test_worker_env_pins_home_and_clears_ambient_variables(self):
        timing_path = self.sandbox["timing_dir"] / "h.json"
        env = self.profiler.worker_env(
            self.sandbox, emission=True, timing_path=timing_path, nonce="hn"
        )
        self.assertEqual(env["HOME"], str(self.sandbox["home"]))
        for var in psgc.SESSION_ENV_VARS + psgc.GIT_ISOLATION_VARS:
            self.assertNotIn(var, env, var)
        self.assertEqual(env["PYTHONDONTWRITEBYTECODE"], "1")
        self.assertEqual(env[psgc.TIMING_PATH_ENV], str(timing_path))
        self.assertEqual(env[psgc.TIMING_NONCE_ENV], "hn")
        env_off = self.profiler.worker_env(self.sandbox, emission=False)
        self.assertNotIn(psgc.TIMING_PATH_ENV, env_off)
        self.assertNotIn(psgc.TIMING_NONCE_ENV, env_off)

    def test_project_key_matches_fixture_repo(self):
        expected = sha16(self.sandbox["fixture"])
        marker = self.profiler.seed_allow_marker(self.sandbox)
        self.assertIn(expected, marker.name)
        sample = self.profiler.measure_consult(
            self.sandbox, class_name="allow", worker_id=0,
            iteration=0, probes={}, emission=True,
            kind="herm", repeat=0, rerun=0,
        )
        self.assertEqual(sample["project_key"], expected)

    def test_consult_cwd_and_explicit_target(self):
        sample = self.profiler.measure_consult(
            self.sandbox, class_name="block", worker_id=0,
            iteration=0, probes={}, emission=True,
            kind="herm", repeat=0, rerun=0,
        )
        self.assertEqual(sample["cwd"], str(self.sandbox["fixture"]))
        self.assertEqual(sample["target"], str(self.sandbox["target"]))


# --------------------------------------------------------------------------- #
# Matched-control load mode (REPOSITORY_TEST smoke: one worker, one class).
# --------------------------------------------------------------------------- #
class PerConsultTimeoutTests(unittest.TestCase):
    def test_hanging_consult_is_killed_and_labeled_timed_out(self):
        with tempfile.TemporaryDirectory() as td:
            stub = Path(td) / "stub-claude.sh"
            stub.write_text(
                "#!/usr/bin/env bash\nsleep 30\n", encoding="utf-8"
            )
            profiler = make_profiler(td, adapter_path=stub)
            sandbox = profiler.build_sandbox("block", worker_id=0)
            original = psgc.PER_CONSULT_TIMEOUT_S
            psgc.PER_CONSULT_TIMEOUT_S = 1.0
            try:
                sample = profiler.measure_consult(
                    sandbox, class_name="block", worker_id=0,
                    iteration=0, probes={}, emission=True,
                    kind="timeout", repeat=0, rerun=0,
                )
            finally:
                psgc.PER_CONSULT_TIMEOUT_S = original
            self.assertTrue(sample["timed_out"])
            self.assertEqual(sample["status"], "degraded")
            self.assertEqual(sample["degraded_label"], "timed-out")
            # The process group was killed and reaped, not left running.
            self.assertLess(sample["e2e_s"], 5.0)


class LoadModeTests(unittest.TestCase):
    def test_load_mode_retains_samples_failure_counts_and_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            profiler = make_profiler(
                td, workers=1, iterations=21, classes=("block",),
                kind="loaded", repeat=0,
            )
            summary = profiler.run()
            out = profiler.output_dir
            worker_files = sorted(out.glob("samples-loaded-r0-rr0-cblock-w*.json"))
            self.assertEqual(len(worker_files), 1)
            data = json.loads(worker_files[0].read_text(encoding="utf-8"))
            self.assertEqual(len(data["samples"]), 21)
            self.assertTrue(
                all(s["class"] == "block" for s in data["samples"])
            )
            self.assertIn("failure_counts", data)
            self.assertTrue(summary["floor_status"]["met"])
            manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
            invocation = manifest["loaded-r0-rr0"]
            self.assertEqual(invocation["workers"], 1)
            self.assertTrue(invocation["ceiling_derivation"])
            self.assertIn("ambient_load_before", invocation)
            self.assertIn("ambient_load_after", invocation)
            self.assertEqual(invocation["keying_branches"], ["empty"])

    def test_run_context_records_derivation(self):
        with tempfile.TemporaryDirectory() as td:
            profiler = make_profiler(td, workers=1, iterations=1,
                                     classes=("block",))
            self.assertEqual(profiler.resolve_workers(), 1)


# --------------------------------------------------------------------------- #
# Sandbox cleanup after a completed run (retained samples always stay).
# --------------------------------------------------------------------------- #
class SandboxCleanupTests(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.tmp = Path(self._td.name)

    def tearDown(self):
        self._td.cleanup()

    def _run_loaded_repeat(self, **kw):
        floor = psgc.CLEAN_SAMPLE_FLOOR
        psgc.CLEAN_SAMPLE_FLOOR = 1  # one clean consult meets this floor
        try:
            profiler = make_profiler(
                self.tmp, workers=1, iterations=1, classes=("block",),
                kind="loaded", repeat=0, **kw)
            summary = profiler.run()
        finally:
            psgc.CLEAN_SAMPLE_FLOOR = floor
        return profiler, summary

    def test_completed_run_removes_sandboxes_and_keeps_samples(self):
        profiler, summary = self._run_loaded_repeat()
        out = profiler.output_dir
        samples = sorted(out.glob("samples-loaded-r0-rr*-cblock-w*.json"))
        self.assertGreaterEqual(len(samples), 1, "retained samples must stay")
        self.assertFalse((out / "sandboxes").exists())
        self.assertFalse(summary["sandbox_cleanup"]["kept"])
        self.assertGreaterEqual(summary["sandbox_cleanup"]["removed"], 1)

    def test_keep_sandboxes_flag_retains_the_trees(self):
        profiler, summary = self._run_loaded_repeat(keep_sandboxes=True)
        sandboxes = profiler.output_dir / "sandboxes"
        self.assertTrue(sandboxes.is_dir())
        self.assertTrue(any(sandboxes.iterdir()))
        self.assertTrue(summary["sandbox_cleanup"]["kept"])
        self.assertEqual(summary["sandbox_cleanup"]["removed"], 0)

    def test_cleanup_sandboxes_sweeps_recorded_roots(self):
        profiler = make_profiler(self.tmp)
        sandbox = profiler.build_sandbox("block", worker_id=0)
        self.assertTrue(sandbox["root"].is_dir())
        removed = profiler._cleanup_sandboxes()
        self.assertEqual(removed, 1)
        self.assertFalse(sandbox["root"].exists())


# --------------------------------------------------------------------------- #
# Analyze mode (analysis record with Terms fields).
# --------------------------------------------------------------------------- #
def fabricated_sample(**kw):
    """A synthetic clean sample with a consistent stage vocabulary."""
    e2e = kw.pop("e2e_s", 1.0)
    class_name = kw.pop("class_name", "allow")
    stages = {
        "keying_log_append": 0.01,
        "plans_dir_resolve": 0.01,
        "classify_target": 0.01,
        "project_key_resolve": 0.01,
        "session_derive": 0.01,
        "marker_check": kw.pop("marker_check", 0.3),
    }
    probe_stages = {
        "payload_extract": 0.02,
        "session_channel": kw.pop("session_channel", 0.02),
        "decision_parse": 0.02,
        "interpreter_probe": kw.pop("interpreter_probe", 0.02),
    }
    sample = base_sample(
        class_name=class_name,
        e2e_s=e2e, stages=stages, probe_stages=probe_stages,
        status=kw.pop("status", "clean"),
        degraded_label=kw.pop("degraded_label", ""),
    )
    sample.update(kw)
    return sample


class AnalyzeModeTests(unittest.TestCase):
    def _write_set(self, out, kind, repeat, cls, samples, rerun=0, worker=0):
        psgc.write_samples_file(
            out, kind=kind, repeat=repeat, rerun=rerun, class_name=cls,
            worker=worker, samples=samples, failure_counts={},
        )

    def _prep_dir(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        return Path(td.name)

    def test_analysis_record_fields(self):
        out = self._prep_dir()
        allow = [fabricated_sample(class_name="allow", iteration=i, e2e_s=1.0,
                                   marker_check=0.6) for i in range(22)]
        block = [fabricated_sample(class_name="block", iteration=i, e2e_s=1.0,
                                   marker_check=0.6) for i in range(22)]
        self._write_set(out, "idle", 0, "allow", allow[:5])
        self._write_set(out, "idle", 0, "block", block[:5])
        self._write_set(out, "loaded", 0, "allow", allow)
        self._write_set(out, "loaded", 0, "block", block)
        off = [fabricated_sample(class_name="block", iteration=i, e2e_s=0.9,
                                 marker_check=0.2, emission=False,
                                 timing_nonce_ok=None) for i in range(22)]
        self._write_set(out, "emissionoff", 0, "block", off)
        record = psgc.analyze_sets(out)
        # All-sample max 1.0 is below the regime threshold: the incident
        # regime is NOT reached and NO stage verdict is drawn (Terms); the
        # suppression is recorded explicitly on the dominance record.
        self.assertFalse(record["regime"]["reached"])
        self.assertIsNone(record["dominance"]["verdict"])
        self.assertEqual(record["dominance"]["reason"], "regime-not-reached")
        self.assertLess(record["regime"]["threshold_s"], 6.0)
        self.assertEqual(record["resolver_counts"]["resolver-failed"], 0)
        self.assertEqual(record["resolver_counts"]["resolver-timeout"], 0)
        self.assertGreater(record["loaded_max"]["allow"]["clean_only_s"], 0.0)
        self.assertGreater(record["loaded_max"]["allow"]["all_samples_s"], 0.0)
        self.assertGreater(record["emission_off_p95_s"], 0.0)
        self.assertGreater(record["emission_on_block_p95_s"], 0.0)
        self.assertEqual(
            record["stage_candidates"]["marker_check"], "(c)")
        self.assertEqual(
            record["stage_candidates"]["session_channel"], "no-candidate")
        self.assertEqual(
            record["stage_provenance"]["marker_check"], "timing-record")
        self.assertEqual(
            record["stage_provenance"]["payload_extract"], "replicated-probe")
        self.assertEqual(record["stage_provenance"]["residual"], "derived")
        analysis_path = out / "analysis.json"
        self.assertTrue(analysis_path.is_file())

    def test_worse_run_governs_analysis(self):
        out = self._prep_dir()
        # e2e sits just above the stage sums so marker_check is the true
        # dominant component and residual stays tiny. A degraded timed-out
        # sample at 6.0s in the worse repeat pushes the all-sample max over
        # the regime threshold so a verdict is drawn at all (Terms).
        r0 = [fabricated_sample(class_name="allow", iteration=i, e2e_s=0.8,
                                marker_check=0.1) for i in range(22)]
        r1 = [fabricated_sample(class_name="allow", iteration=i, e2e_s=1.02,
                                marker_check=0.9) for i in range(22)]
        r1.append(fabricated_sample(
            class_name="allow", iteration=99, e2e_s=6.0, marker_check=0.9,
            status="degraded", degraded_label="timed-out", timed_out=True,
            exit_code=None, timing_nonce_ok=False, keying_values=[],
            decision_readable=False))
        block = [fabricated_sample(class_name="block", iteration=i, e2e_s=1.02,
                                   marker_check=0.9) for i in range(22)]
        self._write_set(out, "loaded", 0, "allow", r0)
        self._write_set(out, "loaded", 1, "allow", r1)
        self._write_set(out, "loaded", 0, "block", block)
        self._write_set(out, "loaded", 1, "block", block)
        record = psgc.analyze_sets(out)
        self.assertTrue(record["regime"]["reached"])
        self.assertEqual(record["worse_run"]["allow"]["repeat"], 1)
        self.assertGreater(
            record["per_class_stage_shares"]["allow"]["marker_check"], 0.5)
        # Same stage dominant in both classes via the worse runs.
        self.assertEqual(record["dominance"]["verdict"], "dominant")

    def test_regime_reached_with_degraded_sample_at_measured_duration(self):
        out = self._prep_dir()
        block = [fabricated_sample(class_name="block", iteration=i, e2e_s=1.0,
                                   marker_check=0.9) for i in range(22)]
        block.append(fabricated_sample(
            class_name="block", iteration=99, e2e_s=6.0,
            marker_check=0.9, status="degraded", degraded_label="timed-out",
            timed_out=True, exit_code=None, timing_nonce_ok=False,
            keying_values=[], decision_readable=False))
        allow = [fabricated_sample(class_name="allow", iteration=i, e2e_s=1.0,
                                   marker_check=0.9) for i in range(22)]
        self._write_set(out, "loaded", 0, "block", block)
        self._write_set(out, "loaded", 0, "allow", allow)
        record = psgc.analyze_sets(out)
        self.assertTrue(record["regime"]["reached"])
        self.assertGreaterEqual(
            record["regime"]["worse_run_all_sample_max_s"], 5.0)
        self.assertEqual(record["resolver_counts"]["resolver-failed"], 0)
        # Regime reached with the floor met: the stage verdict IS drawn
        # (the positive arm of the suppression gate).
        self.assertEqual(record["dominance"]["verdict"], "dominant")
        self.assertEqual(record["dominance"]["stage"], "marker_check")
        self.assertNotIn("reason", record["dominance"])

    def test_resolver_counts_count_degraded_samples(self):
        out = self._prep_dir()
        block = [fabricated_sample(class_name="block", iteration=i, e2e_s=1.0,
                                   marker_check=0.9) for i in range(22)]
        block.append(fabricated_sample(
            class_name="block", iteration=98, e2e_s=1.0,
            marker_check=0.9, status="degraded", degraded_label="resolver-failed",
            keying_values=["project-only", "no-anchor"], resolver_stage_s=0.02))
        allow = [fabricated_sample(class_name="allow", iteration=i, e2e_s=1.0,
                                   marker_check=0.9) for i in range(22)]
        self._write_set(out, "loaded", 0, "block", block)
        self._write_set(out, "loaded", 0, "allow", allow)
        record = psgc.analyze_sets(out)
        self.assertEqual(record["resolver_counts"]["resolver-failed"], 1)

    def test_floor_miss_flagged_when_repeat_below_floor(self):
        out = self._prep_dir()
        block = [fabricated_sample(class_name="block", iteration=i, e2e_s=1.0,
                                   marker_check=0.9) for i in range(10)]
        allow = [fabricated_sample(class_name="allow", iteration=i, e2e_s=1.0,
                                   marker_check=0.9) for i in range(22)]
        self._write_set(out, "loaded", 0, "block", block)
        self._write_set(out, "loaded", 0, "allow", allow)
        record = psgc.analyze_sets(out)
        self.assertTrue(record["floor_missed"]["block"])
        # A repeat under the clean-sample floor draws no stage verdict
        # (Terms); here the regime is not reached either, so both reasons
        # are recorded.
        self.assertIsNone(record["dominance"]["verdict"])
        self.assertEqual(record["dominance"]["reason"],
                         "floor-missed+regime-not-reached")

    def test_latest_rerun_replaces_its_repeat(self):
        out = self._prep_dir()
        r0 = [fabricated_sample(class_name="block", iteration=i, e2e_s=1.0,
                                marker_check=0.9) for i in range(22)]
        self._write_set(out, "loaded", 0, "block", r0, rerun=0)
        r0_rr1 = [fabricated_sample(class_name="block", iteration=i, e2e_s=2.0,
                                    marker_check=0.9) for i in range(22)]
        self._write_set(out, "loaded", 0, "block", r0_rr1, rerun=1)
        allow = [fabricated_sample(class_name="allow", iteration=i, e2e_s=1.0,
                                   marker_check=0.9) for i in range(22)]
        self._write_set(out, "loaded", 0, "allow", allow)
        self._write_set(out, "loaded", 1, "allow", allow)
        record = psgc.analyze_sets(out)
        self.assertEqual(record["worse_run"]["block"]["rerun"], 1)
        self.assertGreater(
            record["per_class_stage_shares"]["block"]["residual"], 0.0)

    # ---- multi-worker sample merge (retained-raw-samples contract) ---- #
    def test_load_sample_sets_merges_workers_and_keeps_highest_rerun(self):
        out = self._prep_dir()
        for worker, e2e in ((0, 1.0), (1, 1.1), (2, 1.2)):
            samples = [fabricated_sample(
                class_name="block", worker=worker, iteration=i, e2e_s=e2e,
                marker_check=0.9) for i in range(21)]
            self._write_set(out, "loaded", 0, "block", samples,
                            rerun=0, worker=worker)
        # Worker 1 re-run at rr1: its rr0 file is replaced, not merged in.
        rr1 = [fabricated_sample(
            class_name="block", worker=1, iteration=i, e2e_s=1.5,
            marker_check=0.9) for i in range(21)]
        self._write_set(out, "loaded", 0, "block", rr1, rerun=1, worker=1)
        sets = psgc.load_sample_sets(out)
        data = sets["loaded"][0]["block"]
        self.assertEqual(sorted(data["workers"]), [0, 1, 2])
        self.assertEqual(len(data["samples"]), 63)
        self.assertEqual(
            sorted({s["e2e_s"] for s in data["samples"]}), [1.0, 1.2, 1.5])
        self.assertEqual(data["rerun"], 1)
        # Through analyze: the merged clean count carries EVERY worker's
        # samples (the dropped-worker regression read 21 here).
        allow = [fabricated_sample(class_name="allow", iteration=i,
                                   e2e_s=1.0, marker_check=0.6)
                 for i in range(21)]
        self._write_set(out, "loaded", 0, "allow", allow)
        record = psgc.analyze_sets(out)
        self.assertEqual(record["worse_run"]["block"]["clean"], 63)

    # ---- interpreter-probe correction wired through analyze ---- #
    def _probe_correction_record(self, out, probe):
        def cls_samples(class_name):
            return [fabricated_sample(
                class_name=class_name, iteration=i, e2e_s=0.7,
                marker_check=0.01, session_channel=0.5,
                interpreter_probe=probe) for i in range(22)]

        block = cls_samples("block")
        block.append(fabricated_sample(
            class_name="block", iteration=99, e2e_s=6.0, marker_check=0.01,
            session_channel=0.5, interpreter_probe=probe,
            status="degraded", degraded_label="timed-out", timed_out=True,
            exit_code=None, timing_nonce_ok=False, keying_values=[],
            decision_readable=False))
        self._write_set(out, "loaded", 0, "block", block)
        self._write_set(out, "loaded", 0, "allow", cls_samples("allow"))
        return psgc.analyze_sets(out)

    def test_probe_correction_maps_over_threshold_channel_to_no_candidate(self):
        # session_channel share 0.5/0.7 dominates raw; minus the 0.25
        # interpreter-probe share it is under the floor -> no-candidate.
        out = self._prep_dir()
        record = self._probe_correction_record(out, probe=0.25)
        self.assertTrue(record["regime"]["reached"])
        self.assertEqual(record["dominance"]["verdict"], "dominant")
        self.assertEqual(record["dominance"]["stage"], "session_channel")
        self.assertAlmostEqual(
            record["interpreter_probe_shares"]["block"], 0.25 / 0.7, places=6)
        self.assertEqual(
            record["stage_candidates"]["session_channel"], "no-candidate")

    def test_probe_correction_still_dominant_channel_maps_to_b(self):
        out = self._prep_dir()
        record = self._probe_correction_record(out, probe=0.05)
        self.assertEqual(record["dominance"]["verdict"], "dominant")
        self.assertEqual(record["dominance"]["stage"], "session_channel")
        self.assertEqual(record["stage_candidates"]["session_channel"], "(b)")

    # ---- verdict suppression (regime / floor gates) ---- #
    def test_verdict_suppressed_when_floor_missed_but_regime_reached(self):
        out = self._prep_dir()
        block = [fabricated_sample(class_name="block", iteration=i,
                                   e2e_s=1.0, marker_check=0.6)
                 for i in range(10)]
        block.append(fabricated_sample(
            class_name="block", iteration=99, e2e_s=6.0, marker_check=0.6,
            status="degraded", degraded_label="timed-out", timed_out=True,
            exit_code=None, timing_nonce_ok=False, keying_values=[],
            decision_readable=False))
        allow = [fabricated_sample(class_name="allow", iteration=i,
                                   e2e_s=1.0, marker_check=0.6)
                 for i in range(22)]
        self._write_set(out, "loaded", 0, "block", block)
        self._write_set(out, "loaded", 0, "allow", allow)
        record = psgc.analyze_sets(out)
        self.assertTrue(record["regime"]["reached"])
        self.assertTrue(record["floor_missed"]["block"])
        self.assertIsNone(record["dominance"]["verdict"])
        self.assertEqual(record["dominance"]["reason"], "floor-missed")

    # ---- degenerate single-class input at the analyze level ---- #
    def test_analyze_single_class_input_records_no_dominant(self):
        out = self._prep_dir()
        allow = [fabricated_sample(class_name="allow", iteration=i,
                                   e2e_s=1.0, marker_check=0.6)
                 for i in range(22)]
        allow.append(fabricated_sample(
            class_name="allow", iteration=99, e2e_s=6.0, marker_check=0.6,
            status="degraded", degraded_label="timed-out", timed_out=True,
            exit_code=None, timing_nonce_ok=False, keying_values=[],
            decision_readable=False))
        self._write_set(out, "loaded", 0, "allow", allow)
        record = psgc.analyze_sets(out)
        self.assertTrue(record["regime"]["reached"])
        self.assertFalse(record["floor_missed"]["allow"])
        # The old wiring (dropping the empty class before the verdict)
        # returned "dominant" from the single class alone; the degenerate
        # guard records no-dominant with the missing class named.
        self.assertEqual(record["dominance"]["verdict"], "no-dominant")
        self.assertEqual(record["dominance"]["reason"],
                         "degenerate-input-missing-class")
        self.assertEqual(record["dominance"]["missing_classes"], ["block"])


if __name__ == "__main__":
    unittest.main()
