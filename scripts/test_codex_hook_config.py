from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import codex_hook_config as config


class CodexHookConfigTest(unittest.TestCase):
    def test_renderer_preserves_unrelated_registrations(self):
        existing = {"hooks": {"SessionStart": [{"command": "unrelated"}], "Custom": [{"command": "kept"}]}, "other": 1}
        definitions = {"schema_version": 1, "hooks": {event: [{"command": "execute-plan"}] for event in config.SUPPORTED_EVENTS}}
        rendered = config.render(existing, definitions)
        self.assertEqual(rendered["hooks"]["SessionStart"][0], {"command": "unrelated"})
        self.assertEqual(rendered["hooks"]["Custom"], [{"command": "kept"}])
        self.assertEqual(rendered["other"], 1)
        self.assertEqual(len(rendered["hooks"]["SessionStart"]), 2)

    def test_checker_reads_selected_policy_from_explicit_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            existing = root / "existing.json"
            definitions = root / "definitions.json"
            policy = root / "config.toml"
            existing.write_text(json.dumps({"hooks": {"Unrelated": [{"command": "keep"}]}}), encoding="utf-8")
            definitions.write_text(json.dumps({"schema_version": 1, "hooks": {event: [{"command": "hook"}] for event in config.SUPPORTED_EVENTS}}), encoding="utf-8")
            policy.write_text('[agents]\ndefault_subagent_model = "selected-model"\n', encoding="utf-8")
            result = config.validate_fixture(existing, definitions, policy)
            self.assertEqual(result["selected_subagent_model"], "selected-model")
            self.assertEqual(result["rendered"]["hooks"]["Unrelated"], [{"command": "keep"}])


if __name__ == "__main__":
    unittest.main()
