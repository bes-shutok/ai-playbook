"""Region-scoped regression pins for maintenance D-17 continuation scenarios."""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import dispatch_admission
import quota_window_probe
import rearm_on_touch

DECISIONS = (ROOT / "agents/skills/maintenance/decisions.md").read_text(encoding="utf-8")
MAINTENANCE = (ROOT / "agents/skills/maintenance/SKILL.md").read_text(encoding="utf-8")
DIRECTIVES = (ROOT / "docs/maintenance/operator-directives.md").read_text(encoding="utf-8")
AUTHORING = (ROOT / "agents/skills/maintenance/template-authoring.md").read_text(encoding="utf-8")


def heading_section(text: str, heading: str) -> str:
    """Return a Markdown heading's region through the next same-or-higher heading."""
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line == heading)
    level = len(heading) - len(heading.lstrip("#"))
    end = next(
        (i for i in range(start + 1, len(lines))
         if lines[i].startswith("#") and len(lines[i]) - len(lines[i].lstrip("#")) <= level),
        len(lines),
    )
    return "\n".join(lines[start:end])


def paragraph(text: str, prefix: str) -> str:
    """Return the complete blank-line-delimited paragraph beginning with prefix."""
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(prefix))
    end = next((i for i in range(start + 1, len(lines)) if not lines[i].strip()), len(lines))
    return "\n".join(lines[start:end])


def bullet(text: str, prefix: str) -> str:
    """Return the line-prefix-scoped bullet, following the established test precedent."""
    return next(line for line in text.splitlines() if line.startswith(prefix))


BLOCKER_RECOVERY = heading_section(DECISIONS, "### Blocker recovery")
CONTINUE_LOOP = paragraph(DECISIONS, "The continue-loop condition ")
CYCLE_GATE = heading_section(MAINTENANCE, "## Cycle gate (durable pacing between cycles)")
SELF_HEAL_INTEGRATION = bullet(
    heading_section(MAINTENANCE, "## Integration Points"), "- `self-heal` skill"
)
D17 = bullet(heading_section(DIRECTIVES, "## D-17: maintenance autopilot continues across picks without user turns"), "- directive:")
D6 = bullet(heading_section(DIRECTIVES, "## D-6: executing and authoring lanes continue unless the 5h limit is low"), "- directive:")
FINAL_STEP = paragraph(AUTHORING, "FINAL STEP, after the report:")
D1_EXECUTE = bullet(heading_section(DECISIONS, "### Step 3: decision"), "- `D1 (execute)`")
ADMISSION_CONTRACT = bullet(MAINTENANCE, "- The fleet caps the landing queue at one recorded run:")
LOOP_LIVENESS = bullet(MAINTENANCE, "- User-directed maintenance payload duties")

SITES = {
    "blocker_recovery": BLOCKER_RECOVERY,
    "continue_loop": CONTINUE_LOOP,
    "cycle_gate": CYCLE_GATE,
    "self_heal_integration": SELF_HEAL_INTEGRATION,
    "d17": D17,
    "d6": D6,
    "final_step": FINAL_STEP,
}

# Each row states only the clauses that own that scenario; keys make the
# scenario-to-sites agreement explicit and prevent a whole-file match from
# satisfying a missing site.
SCENARIOS = {
    "routine_blocker_with_another_pick": {
        "sites": {
            "blocker_recovery": ("non-user-only blocker", "one `self-heal` consultation", "before the stop is judged unrecoverable"),
            "self_heal_integration": ("consults self-heal once per non-user-only blocker", "before a stop or operator ask"),
            "continue_loop": ("continues into the next lane decision instead of ending at a landing boundary while all four legs hold", "a dispatchable target exists", "a full lane decision through the normal machinery, never a shortcut past a guard"),
        },
        "fixture": "routine blocker; another eligible pick remains; consult once, then resume guarded lane selection",
    },
    "context_management_gate": {
        "sites": {
            "continue_loop": ("context management is cleared with the existing dated trace", "explicit user-paced gate still stops"),
            "cycle_gate": ("context-management stop is not user-paced", "records the D-17 disposition", "without a prompt"),
            "d17": ("context-management stop", "clear it with the existing dated clear trace", "continue without a prompt"),
            "final_step": ("context-management stops do not hold the cycle gate", "continue eligible work without a user turn"),
        },
        "fixture": "autopilot; gate armed only for context management; dated trace; record disposition; continue without prompt",
    },
    "explicit_user_paced_gate": {
        "sites": {
            "continue_loop": ("explicit user-paced gate still stops",),
            "cycle_gate": ("explicit user-paced directive", "reports readiness and stops until a real user directive clears it"),
            "d17": ("requires user action before the next cycle", "still arms the gate and stops"),
            "final_step": ("explicit user-paced directive does",),
        },
        "fixture": "explicit user-paced directive; report readiness; hold until a real user directive clears gate",
    },
    "empty_eligible_queue": {
        "sites": {
            "continue_loop": ("a dispatchable target exists", "turn stops at that boundary"),
            "cycle_gate": ("empty eligible queue still end the loop",),
            "d17": ("empty-queue stop",),
            "final_step": ("while a target remains",),
        },
        "fixture": "no eligible targets remain; stop at the empty-queue boundary",
    },
    "primary_quota_pause": {
        "sites": {
            "d17": ("primary five-hour quota pause",),
            "d6": ("primary-window probe reading at its pause thresholds", "records the resume point in the state file and stops", "weekly-secondary binding window's pause stays report-only"),
        },
        "fixture": "primary five-hour quota pause stops; weekly-secondary pause remains report-only",
    },
    "explicit_stop_request": {
        "sites": {
            "cycle_gate": ("Explicit current stop requests", "still end the loop"),
            "d17": ("an explicit current stop or pause request",),
        },
        "fixture": "operator explicitly requests stop; preserve stop request",
    },
    "user_only_blocker": {
        "sites": {
            "blocker_recovery": ("A user-only decision", "stay blocking outside this consultation", "explicit operator stop"),
        },
        "fixture": "missing authority or explicit operator stop; remain held without self-heal bypass",
    },
}


def active_deny_patterns(patterns_path: Path) -> list[re.Pattern[str]]:
    active = []
    for raw in patterns_path.read_text(encoding="utf-8").splitlines():
        expression = raw.split("#", 1)[0].strip()
        if expression:
            active.append(re.compile(expression))
    return active


class MaintenanceD17ScenarioAgreementTest(unittest.TestCase):
    """Keep continuation outcomes aligned only at their owning prose spans."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._patterns_dir = tempfile.TemporaryDirectory()
        cls.patterns_path = Path(cls._patterns_dir.name) / "public-hygiene.patterns"
        cls.patterns_path.write_text(
            "/" + "Users/" + "|/home/[a-zA-Z0-9._-]+/\n"
            + r"Co-[Aa]uthored-[Bb]y:\s+.+<[^>]+@[^>]+>" + "\n",
            encoding="utf-8",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._patterns_dir.cleanup()

    def setUp(self) -> None:
        # Hygiene is checked before any scenario token is pinned. This protects
        # both extracted policy text and the scenario fixtures themselves.
        patterns = active_deny_patterns(self.patterns_path)
        for label, value in [*SITES.items(), *((key, row["fixture"]) for key, row in SCENARIOS.items())]:
            for pattern in patterns:
                self.assertIsNone(pattern.search(value), f"deny pattern {pattern.pattern!r} matched {label}")

    def _assert_scenario(self, name: str) -> None:
        scenario = SCENARIOS[name]
        self.assertTrue(scenario["sites"], f"{name} must own at least one site")
        for site, tokens in scenario["sites"].items():
            self.assertIn(site, SITES, f"{name} maps an unknown site")
            span = SITES[site]
            for token in tokens:
                self.assertIn(token, span, f"{name}: {token!r} missing from owning span {site}")

    def test_blocker_leg_resumes_after_single_self_heal_consult(self) -> None:
        self._assert_scenario("routine_blocker_with_another_pick")

    def test_context_gate_clears_and_continues_without_prompt(self) -> None:
        self._assert_scenario("context_management_gate")

    def test_user_paced_gate_reports_readiness_and_holds(self) -> None:
        self._assert_scenario("explicit_user_paced_gate")

    def test_preserved_terminals_have_owning_clause_pins(self) -> None:
        for name in ("explicit_stop_request", "empty_eligible_queue", "primary_quota_pause", "user_only_blocker"):
            with self.subTest(terminal=name):
                self._assert_scenario(name)

    def test_site_mapping_is_explicit_and_region_scoped(self) -> None:
        expected_sites = {
            "routine_blocker_with_another_pick": {"blocker_recovery", "self_heal_integration", "continue_loop"},
            "context_management_gate": {"continue_loop", "cycle_gate", "d17", "final_step"},
            "explicit_user_paced_gate": {"continue_loop", "cycle_gate", "d17", "final_step"},
            "empty_eligible_queue": {"continue_loop", "cycle_gate", "d17", "final_step"},
            "primary_quota_pause": {"d17", "d6"},
            "explicit_stop_request": {"cycle_gate", "d17"},
            "user_only_blocker": {"blocker_recovery"},
        }
        self.assertEqual({name: set(row["sites"]) for name, row in SCENARIOS.items()}, expected_sites)
        for name in SCENARIOS:
            with self.subTest(scenario=name):
                self._assert_scenario(name)

    def test_hygiene_scan_reports_no_hit_for_this_file(self) -> None:
        executable_dirs = [
            str(Path(path).parent)
            for path in (shutil.which("git"), shutil.which("rg"))
            if path
        ]
        environment = {
            "HOME": str(self.patterns_path.parent),
            "LC_ALL": "C",
            "PATH": os.pathsep.join(dict.fromkeys([*executable_dirs, *os.defpath.split(os.pathsep)])),
            "PUBLIC_HYGIENE_PATTERNS_FILE": str(self.patterns_path),
            "PUBLIC_HYGIENE_REPO_ROOT": str(ROOT),
        }
        command = [shutil.which("bash") or "/bin/bash", "scripts/scan-public-hygiene.sh", "--files", "scripts/test_maintenance_d17_continuation_scenarios.py"]
        result = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("OUTCOME: pass", output)
        self.assertNotIn("PUBLIC_HYGIENE_REPORT: path=scripts/test_maintenance_d17_continuation_scenarios.py", output)
        self.assertNotIn("note: skipped excluded path:", output)
        self.assertNotIn("HIT:", output)


class MaintenanceD17GuardCompositionTest(unittest.TestCase):
    """Compose real quota, admission, and rearm verdicts as D-17 inputs."""

    def test_quota_headroom_and_wall_verdicts_feed_the_d17_loop(self) -> None:
        now = 1_000
        headroom = quota_window_probe.make_limit(
            "primary", 40.0, now + 150 * 60, now=now
        )
        quota_wall = quota_window_probe.make_limit(
            "primary", 95.0, now + 150 * 60, now=now
        )

        headroom_verdict, headroom_reasons = quota_window_probe.evaluate_pause(
            [headroom], "primary"
        )
        self.assertEqual((headroom_verdict, headroom_reasons), ("continue", []))
        quota_clause_by_verdict = {
            "continue": ("abundant and tightening continue the loop", CONTINUE_LOOP),
            "pause": ("primary five-hour quota pause", D17),
        }
        self.assertIn(*quota_clause_by_verdict[headroom_verdict])
        pause, reasons = quota_window_probe.evaluate_pause([quota_wall], "primary")
        self.assertEqual(pause, "pause")
        self.assertTrue(any("used_percent" in reason for reason in reasons), reasons)
        self.assertIn(*quota_clause_by_verdict[pause])

    def test_quota_core_forbids_host_reads_writes_and_transports(self) -> None:
        now = 1_000
        fixture = quota_window_probe.make_limit(
            "primary", 40.0, now + 150 * 60, now=now
        )
        forbidden = AssertionError("pure evaluate_pause crossed a host-touching surface")
        with ExitStack() as stack:
            for name in (
                "run_probe", "probe_zcode", "probe_codex", "load_api_key",
                "urllib_transport", "_codex_app_server_request",
                "write_flag_if_paused", "_shared_guard_lock",
            ):
                stack.enter_context(mock.patch.object(quota_window_probe, name, side_effect=forbidden))
            for name in ("open",):
                stack.enter_context(mock.patch("builtins." + name, side_effect=forbidden))
            for method in ("read_text", "write_text", "mkdir", "unlink"):
                stack.enter_context(mock.patch.object(Path, method, side_effect=forbidden))
            stack.enter_context(mock.patch.object(quota_window_probe.os, "replace", side_effect=forbidden))
            stack.enter_context(mock.patch.object(quota_window_probe.fcntl, "flock", side_effect=forbidden))
            stack.enter_context(mock.patch.object(quota_window_probe.urllib.request, "urlopen", side_effect=forbidden))
            stack.enter_context(mock.patch.object(quota_window_probe.subprocess, "Popen", side_effect=forbidden))
            decision, reasons = quota_window_probe.evaluate_pause([fixture], "primary")

        self.assertEqual(decision, "continue")
        self.assertEqual(reasons, [])

    def test_admission_verdicts_bind_disjoint_and_intersecting_picks(self) -> None:
        disjoint = dispatch_admission.check_admission(
            dispatch_admission.Candidate("plan-disjoint", ["docs/next.md"]),
            [dispatch_admission.OutstandingRun("run-active", ["scripts/owned.py"])],
        )
        self.assertTrue(disjoint.admitted, disjoint.reason)
        self.assertIsNone(disjoint.blocking_run_id)
        admission_clause_by_verdict = {
            True: ("Step 2 guards pass in their fixed order", CONTINUE_LOOP),
            False: (
                "When any leg does not hold, the turn stops at that boundary",
                CONTINUE_LOOP,
            ),
        }
        self.assertIn(*admission_clause_by_verdict[disjoint.admitted])

        intersecting = dispatch_admission.check_admission(
            dispatch_admission.Candidate("plan-overlap", ["docs/next.md", "scripts/owned.py"]),
            [dispatch_admission.OutstandingRun("run-active", ["scripts/owned.py"])],
        )
        self.assertFalse(intersecting.admitted, intersecting.reason)
        self.assertEqual(intersecting.blocking_run_id, "run-active")
        self.assertEqual(intersecting.intersecting_paths, ["scripts/owned.py"])
        self.assertIn(*admission_clause_by_verdict[intersecting.admitted])

        conservative = dispatch_admission.check_admission(
            dispatch_admission.Candidate("plan-underivable", ["docs/next.md"]),
            [dispatch_admission.OutstandingRun("run-without-manifest", None)],
        )
        self.assertIs(conservative.admitted, False)
        self.assertEqual(conservative.blocking_run_id, "run-without-manifest")
        self.assertEqual(
            conservative.reason,
            "outstanding run run-without-manifest carries no done-setup manifest "
            "from which to derive owned paths; treated as intersecting "
            "(conservative verdict)",
        )
        self.assertIn(*admission_clause_by_verdict[conservative.admitted])

        self.assertIn("check_admission", ADMISSION_CONTRACT)
        self.assertIn("must be disjoint from every outstanding run's recorded owned-path set", ADMISSION_CONTRACT)
        self.assertIn("with an empty recorded set or a run with no done-setup manifest from which to derive owned paths taking the conservative verdict", ADMISSION_CONTRACT)
        self.assertIn("conservative verdict (treated as intersecting", ADMISSION_CONTRACT)
        self.assertIn("Step 2 guards pass in their fixed order", CONTINUE_LOOP)
        self.assertIn("When any leg does not hold, the turn stops at that boundary and records the failing leg", CONTINUE_LOOP)
        self.assertIn("the execution lane (`G1e`) is free, and an open plan exists", D1_EXECUTE)

    def assert_rearm_parent_ok_fixture_is_loop_liveness_input(self, tmp_path) -> None:
        repo_root = tmp_path / "fixture-repository"
        repo_root.mkdir()
        state_path = tmp_path / "scheduler-state.fixture.json"
        listing_path = tmp_path / "automation-listing.fixture.json"
        state = {
            "parent_automation_id": "fixture-parent-enabled",
            "parent_absent_since": None,
            "children": [],
            "rearm_note": None,
        }
        state_path.write_text(json.dumps(state) + "\n", encoding="utf-8")
        listing = [{
            "automationId": "fixture-parent-enabled",
            "title": rearm_on_touch.RECOGNITION_TITLE,
            "prompt": rearm_on_touch.RECOGNITION_PROMPT_OPENING + " " + str(repo_root),
            "enabled": True,
            "lifecycleStatus": "active",
        }]
        listing_path.write_text(json.dumps(listing) + "\n", encoding="utf-8")

        stdout, stderr = io.StringIO(), io.StringIO()
        args = [
            "--repo-root", str(repo_root),
            "--state-path", str(state_path),
            "--listing-json", str(listing_path),
        ]
        with mock.patch.dict(os.environ, {}, clear=True), redirect_stdout(stdout), redirect_stderr(stderr), mock.patch.object(
            rearm_on_touch.subprocess, "run", side_effect=AssertionError("explicit fixture root must avoid git lookup")
        ):
            result = rearm_on_touch.main(args)

        output_lines = stdout.getvalue().splitlines()
        verdict = json.loads(output_lines[0])
        self.assertEqual(output_lines[-1], "OUTCOME: pass")
        self.assertEqual(result, 0)
        self.assertEqual(verdict["class"], "parent-ok")
        self.assertTrue(verdict["listing_used"])
        self.assertEqual(verdict["recognition_matches"], 1)
        self.assertFalse(verdict["rearm_required"])
        self.assertEqual(json.loads(state_path.read_text(encoding="utf-8")), state)
        liveness_clause_by_verdict = {
            "parent-ok": (
                LOOP_LIVENESS,
                "ENABLED recognition match exists",
                "reports `loop-liveness:`",
            ),
        }
        for clause in liveness_clause_by_verdict[verdict["class"]][1:]:
            self.assertIn(clause, liveness_clause_by_verdict[verdict["class"]][0])
        self.assertIn("a dispatchable target exists", CONTINUE_LOOP)


def test_rearm_parent_ok_fixture_is_loop_liveness_input(tmp_path) -> None:
    MaintenanceD17GuardCompositionTest().assert_rearm_parent_ok_fixture_is_loop_liveness_input(tmp_path)


if __name__ == "__main__":
    unittest.main()
