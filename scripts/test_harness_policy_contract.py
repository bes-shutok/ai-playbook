#!/usr/bin/env python3
"""Harness policy contract tests (Task 3, 2026-09-23 harness friction audit plan).

These tests pin the harness policy contract that survived the evidence-backed
simplification pass:

1. No active shared rule or configured adapter carries a control whose only
   purpose is malicious co-user defense (single-operator host).
2. Unapproved Slack outbound stays draft-only.
3. Every externally visible write class stays gated behind explicit user
   authorization.
4. Rewritten policy text stays agent-agnostic (intent-level wording, adapter
   mapping only where a host needs it).
5. The removed co-user threat-model wording has no operational reference left
   in the repo policy, skill, and hook adapter corpus.
6. The configured active entrypoints (instruction entrypoints and registered
   hook configs on this host) carry no reintroduction of the removed control.

The inventory constants below record the surfaces mapped during the Task 3
inventory step. Repo paths are repository-relative. Home entrypoints resolve
through Path.home() and are swept only when present, so the suite stays
runnable on a fresh checkout while still guarding this operator's wiring.
The home surface lists are externalizable per host via the optional
`home_entrypoint_files` / `home_hook_config_files` TOML-array keys in the
repo-scoped gitignored `.ai-playbook/facts.md` fence; the in-script lists
(DEFAULT_HOME_*) are the fallback default when the file, the fence, or a key
is absent (or a present value is malformed, with a stderr warning naming the
key). The exists-then-skip design with its recorded skip message is unchanged.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Canonical shared rules (repo side).
REPO_SHARED_RULES = [
    "AGENTS.md",
    "docs/AGENTS.md",
]

# Skill surfaces changed or verified by this plan's Task 3.
REPO_SKILL_SURFACES = [
    "agents/skills/slack-message/SKILL.md",
    "agents/skills/done/SKILL.md",
    "agents/skills/execute-plan/SKILL.md",
    "agents/skills/review-plan/SKILL.md",
    "agents/skills/review-agents/review-panel-selection.md",
    "agents/skills/review-staging/SKILL.md",
]

# Hook adapter corpus root; every non-cache file under it is an inventoried
# adapter surface (READMEs are the policy carriers, scripts the enforcement).
HOOK_ADAPTER_ROOT = REPO_ROOT / "agents" / "hooks"

# Active shared instruction entrypoints on this single-operator host. Each is
# a thin import of or symlink to the canonical docs/AGENTS.md (verified during
# the Task 3 inventory; see the gitignored surface-inventory working notes).
# FALLBACK DEFAULT: externalizable per host via the optional
# `home_entrypoint_files` TOML-array key in the repo-scoped gitignored
# `.ai-playbook/facts.md` fence (see _load_home_surface_lists); the
# exists-then-skip sweep design with its recorded skip message is unchanged.
DEFAULT_HOME_ENTRYPOINT_FILES = [
    "~/.zcode/AGENTS.md",
    "~/.claude/CLAUDE.md",
    "~/.codex/AGENTS.md",
    "~/.gemini/GEMINI.md",
    "~/.copilot/copilot-instructions.md",
]

# Registered hook configuration files per host agent (registered adapters).
# FALLBACK DEFAULT: externalizable per host via the optional
# `home_hook_config_files` TOML-array key in the repo-scoped gitignored
# `.ai-playbook/facts.md` fence (see _load_home_surface_lists).
DEFAULT_HOME_HOOK_CONFIG_FILES = [
    "~/.zcode/cli/config.json",
    "~/.claude/settings.json",
    "~/.codex/hooks.json",
    "~/.cursor/hooks.json",
    "~/.gemini/antigravity-cli/hooks.json",
]


def _load_home_surface_lists(facts_path=None):
    """Load the home-surface sweep lists from the repo-scoped gitignored
    facts fence, falling back to the in-script DEFAULT_* lists.

    Reads the FIRST ```toml-fenced block in `.ai-playbook/facts.md` (repo
    default: REPO_ROOT/.ai-playbook/facts.md; the parameter exists for the
    unit tests) and consumes the optional TOML-array keys
    `home_entrypoint_files` / `home_hook_config_files`. A missing file,
    missing fence, or missing key falls back to the corresponding DEFAULT_*
    list; a PRESENT but malformed value (not a non-empty list of non-empty
    strings) is also ignored with a one-line stderr warning naming the key
    and the fallback, so a typo'd override cannot silently no-op. Never
    raises. Mirrors facts_paths.py's first-fence walk; it deliberately does
    NOT import or widen facts_paths.resolve_toml_key_raw (scalar-only,
    docstring-pinned single source).
    """
    import sys
    entrypoints = list(DEFAULT_HOME_ENTRYPOINT_FILES)
    hook_configs = list(DEFAULT_HOME_HOOK_CONFIG_FILES)
    path = Path(facts_path) if facts_path is not None else REPO_ROOT / ".ai-playbook" / "facts.md"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, ValueError):  # ValueError: invalid-encoding facts bytes
        return entrypoints, hook_configs
    lines = text.splitlines()
    try:
        start = next(i for i, ln in enumerate(lines) if ln.strip() == "```toml")
        end = next(i for i, ln in enumerate(lines[start + 1:], start + 1) if ln.strip() == "```")
        block = "\n".join(lines[start + 1:end])
    except StopIteration:
        return entrypoints, hook_configs
    try:
        import tomllib
        data = tomllib.loads(block)
    except Exception:
        return entrypoints, hook_configs
    for key, target in (
        ("home_entrypoint_files", entrypoints),
        ("home_hook_config_files", hook_configs),
    ):
        if key not in data:
            continue
        value = data[key]
        if (
            isinstance(value, list)
            and bool(value)
            and all(isinstance(item, str) and item for item in value)
        ):
            target[:] = value
        else:
            sys.stderr.write(
                f"harness policy contract: ignoring malformed {key!r} in {path}; "
                f"falling back to the in-script default list\n"
            )
    return entrypoints, hook_configs


HOME_ENTRYPOINT_FILES, HOME_HOOK_CONFIG_FILES = _load_home_surface_lists()

# Patterns whose ONLY purpose is hostile-co-user threat framing. Chosen to
# never match accidental-data-loss wording (accident, unintended, peer
# staging refusals), external-action authorization gates, or product-security
# catalogs, which must all stay.
CO_USER_THREAT_PATTERNS = [
    (r"hostile\s+(?:co-?user|agent|peer|user|actor|local\s+user)", "hostile-actor framing"),
    (r"malicious\s+(?:co-?user|user|agent|peer|actor)", "malicious-actor framing"),
    (r"\bco-?user\b", "co-user threat model"),
    (r"\bforgeable\b", "forgeability framing"),
    (r"another\s+local\s+user", "another-local-user framing"),
]

# Exact wordings removed by this task (the skill-gate THREAT-MODEL note's
# hostile-co-user defense framing). Their return anywhere active would
# reintroduce the removed control.
REMOVED_CONTROL_SIGNATURES = [
    "forgeable by any process",
    "not to defend against a hostile",
    "THREAT-MODEL note",
]

# Slack draft-only contract fragments that must stay present.
SLACK_DRAFT_ONLY_REQUIRED_IN_SKILL = [
    "Draft first, always",
    "Never use immediate/direct send",
    "Immediate/direct send is forbidden",
    "Slack Drafts",
]
SLACK_DRAFT_ONLY_REQUIRED_IN_RULES = [
    "draft-only",
    "Never send, post, schedule, edit, delete, or react in Slack",
]
# Instructions that would allow the agent itself to send. Tight shapes only,
# so "let the user send from Slack" and "do not call a direct-send tool" stay
# legal.
SLACK_SEND_ALLOW_PATTERNS = [
    r"(?i)\b(?:you may|you can|agent may|is allowed to|are permitted to|feel free to)\b[^.]*\b(?:send|post|schedule|edit|delete|react)\b",
    r"(?i)\bdirect[- ]send\s+(?:is\s+)?(?:allowed|permitted|enabled|supported)\b",
]

# Externally visible write classes and the explicit-authorization gate each
# must keep in the shared contract (docs/AGENTS.md, lowercased match).
EXTERNAL_WRITE_GATES = [
    ("git push", "never push without explicit user instruction"),
    ("git force-push", "never force-push without approval"),
    ("slack outbound", "never send, post, schedule, edit, delete, or react in slack"),
    ("confluence pages owned by someone else", "never update confluence pages created by someone else"),
    ("personal projects remote actions", "local git only unless user asks"),
]

# Agent or tool-specific bindings that must not appear inside the rewritten
# policy paragraphs (adapter wiring sections elsewhere legitimately name
# hosts; the policy paragraphs themselves must stay intent-level).
AGENT_OR_TOOL_TOKENS = [
    "Claude", "Codex", "Cursor", "Gemini", "Antigravity", "agy", "ZCode",
    "Copilot", "Write", "Edit", "Bash", "jq", "python3", "json.dumps",
]


def _repo_file(rel: str) -> Path:
    return REPO_ROOT / rel


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _hook_adapter_files() -> list[Path]:
    files = [
        p
        for p in sorted(HOOK_ADAPTER_ROOT.rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts
    ]
    if not files:
        raise AssertionError(f"hook adapter inventory is empty: {HOOK_ADAPTER_ROOT}")
    return files


def _repo_inventory_files() -> list[tuple[str, Path]]:
    """The inventoried shared-rule and adapter file set (repo side)."""
    named = [
        ("shared-rule", rel, _repo_file(rel)) for rel in REPO_SHARED_RULES
    ] + [
        ("skill", rel, _repo_file(rel)) for rel in REPO_SKILL_SURFACES
    ]
    missing = [path for _, _, path in named if not path.is_file()]
    if missing:
        raise AssertionError(
            "inventory file(s) missing: " + ", ".join(str(p) for p in missing)
        )
    return [(kind, path) for kind, _, path in named] + [
        ("hook-adapter", path) for path in _hook_adapter_files()
    ]


def _home_files(rel_or_tilde: str) -> Path:
    return Path(rel_or_tilde).expanduser()


class HarnessPolicyContractTest(unittest.TestCase):
    """Contract tests for the simplified harness policy (Task 3)."""

    def test_co_user_threat_controls_absent(self):
        """No inventoried shared rule or adapter carries co-user-only threat framing."""
        hits = []
        for kind, path in _repo_inventory_files():
            text = _read(path)
            for lineno, line in enumerate(text.splitlines(), start=1):
                for pattern, label in CO_USER_THREAT_PATTERNS:
                    if re.search(pattern, line):
                        hits.append(
                            f"{path.relative_to(REPO_ROOT)}:{lineno}: {label} "
                            f"({pattern}): {line.strip()}"
                        )
        self.assertEqual(
            hits,
            [],
            "co-user-only threat framing found in active policy surfaces:\n"
            + "\n".join(hits),
        )

    def test_unapproved_slack_send_remains_draft_only(self):
        """Without explicit send authorization, Slack stays draft-only everywhere."""
        skill = _read(_repo_file("agents/skills/slack-message/SKILL.md"))
        rules = _read(_repo_file("docs/AGENTS.md"))
        for fragment in SLACK_DRAFT_ONLY_REQUIRED_IN_SKILL:
            self.assertIn(fragment, skill, "slack skill lost draft-only rule")
        for fragment in SLACK_DRAFT_ONLY_REQUIRED_IN_RULES:
            self.assertIn(fragment, rules, "shared rule lost Slack draft-only gate")
        for name, text in (("slack-message/SKILL.md", skill), ("docs/AGENTS.md", rules)):
            for lineno, line in enumerate(text.splitlines(), start=1):
                for pattern in SLACK_SEND_ALLOW_PATTERNS:
                    self.assertIsNone(
                        re.search(pattern, line),
                        f"{name}:{lineno} allows an unapproved Slack send: {line.strip()}",
                    )

    def test_unapproved_external_writes_remain_authorization_gated(self):
        """Every external-write class keeps its explicit-authorization gate."""
        rules = _read(_repo_file("docs/AGENTS.md")).lower()
        for action, gate in EXTERNAL_WRITE_GATES:
            self.assertIn(
                gate,
                rules,
                f"shared contract lost the authorization gate for {action}",
            )
        # The active execute-plan adapter restates the push boundary.
        execute_plan = _read(_repo_file("agents/skills/execute-plan/SKILL.md"))
        self.assertIn(
            "still requires explicit user instruction",
            execute_plan,
            "execute-plan adapter lost the push authorization gate",
        )

    def test_shared_policy_is_agent_agnostic(self):
        """Rewritten policy paragraphs stay agent-agnostic and intent-level."""
        readme = _read(_repo_file("agents/hooks/skill-gate/README.md"))
        section = re.split(r"^## What the gate does\s*$", readme, maxsplit=1, flags=re.M)
        self.assertEqual(len(section), 2, "skill-gate README lost 'What the gate does'")
        body = section[1].split("\n## ", 1)[0]
        paragraphs = [p for p in body.split("\n\n") if "consent reminder" in p]
        self.assertEqual(
            len(paragraphs), 1, "expected exactly one consent-reminder paragraph"
        )
        paragraph = " ".join(paragraphs[0].split())
        for token in AGENT_OR_TOOL_TOKENS:
            self.assertNotIn(
                token, paragraph,
                f"rewritten consent-reminder paragraph binds policy to '{token}'",
            )
        # The shared contract's external-write bullets stay agent-agnostic too.
        rules = _read(_repo_file("docs/AGENTS.md"))
        for bullet_marker in ("Git push:", "Slack outbound:", "Confluence ownership:"):
            line = next(
                (l for l in rules.splitlines() if l.strip().startswith(f"- **{bullet_marker}")),
                None,
            )
            self.assertIsNotNone(line, f"docs/AGENTS.md lost the {bullet_marker} bullet")
            for token in AGENT_OR_TOOL_TOKENS[:8]:
                self.assertNotIn(
                    token, line,
                    f"{bullet_marker} bullet binds policy to '{token}'",
                )

    def test_removed_controls_have_no_operational_reference(self):
        """No repo policy, skill, or hook adapter file reintroduces the removed control."""
        leftovers = []
        for kind, path in _repo_inventory_files():
            text = _read(path)
            for signature in REMOVED_CONTROL_SIGNATURES:
                if signature in text:
                    leftovers.append(f"{path.relative_to(REPO_ROOT)}: {signature!r}")
        self.assertEqual(
            leftovers,
            [],
            "removed co-user control is still operationally referenced:\n"
            + "\n".join(leftovers),
        )

    def test_home_surface_lists_override_from_facts_keys(self):
        """A facts fence with both optional keys overrides the defaults exactly."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            facts = Path(td) / "facts.md"
            facts.write_text(
                "# notes\n```toml\n"
                'home_entrypoint_files = ["~/zcode/AGENTS.example.md"]\n'
                'home_hook_config_files = ["~/agents/hooks.example.json"]\n'
                "```\n",
                encoding="utf-8",
            )
            ep, hc = _load_home_surface_lists(facts_path=facts)
        self.assertEqual(ep, ["~/zcode/AGENTS.example.md"])
        self.assertEqual(hc, ["~/agents/hooks.example.json"])

    def test_home_surface_lists_fallback_defaults(self):
        """Missing file, no fence, or fence without the keys all fall back."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "absent.md"
            no_fence = Path(td) / "nofence.md"
            no_fence.write_text("plain markdown, no fence\n", encoding="utf-8")
            no_keys = Path(td) / "nokeys.md"
            no_keys.write_text(
                "```toml\nother_key = \"value\"\n```\n", encoding="utf-8"
            )
            for facts in (missing, no_fence, no_keys):
                ep, hc = _load_home_surface_lists(facts_path=facts)
                self.assertEqual(ep, DEFAULT_HOME_ENTRYPOINT_FILES)
                self.assertEqual(hc, DEFAULT_HOME_HOOK_CONFIG_FILES)

    def test_home_surface_lists_rejects_malformed_values(self):
        """A bare string or a list with a non-string element falls back + warns."""
        import contextlib
        import io
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            bare = Path(td) / "bare.md"
            bare.write_text(
                "```toml\n"
                'home_entrypoint_files = "~/oops.md"\n'
                "```\n",
                encoding="utf-8",
            )
            badlist = Path(td) / "badlist.md"
            badlist.write_text(
                "```toml\n"
                "home_hook_config_files = [\"~/ok.json\", 42]\n"
                "```\n",
                encoding="utf-8",
            )
            for facts, key in ((bare, "home_entrypoint_files"), (badlist, "home_hook_config_files")):
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    ep, hc = _load_home_surface_lists(facts_path=facts)
                self.assertIn(key, stderr.getvalue())
                self.assertIn("falling back", stderr.getvalue())
                self.assertEqual(ep, DEFAULT_HOME_ENTRYPOINT_FILES)
                self.assertEqual(hc, DEFAULT_HOME_HOOK_CONFIG_FILES)

    def test_removed_controls_absent_from_active_entrypoints(self):
        """No configured surface (entrypoint or registered hook config) reintroduces it."""
        missing = []
        for tilde in HOME_ENTRYPOINT_FILES + HOME_HOOK_CONFIG_FILES:
            path = _home_files(tilde)
            if not path.exists():
                missing.append(tilde)
                continue
            text = _read(path)
            for signature in REMOVED_CONTROL_SIGNATURES:
                self.assertNotIn(
                    signature, text,
                    f"active surface {tilde} reintroduces the removed control: {signature!r}",
                )
        if missing:
            self.skipTest(
                "optional host surfaces absent on this machine (repo surfaces are "
                "covered by test_removed_controls_have_no_operational_reference): "
                + ", ".join(missing)
            )


if __name__ == "__main__":
    unittest.main()
