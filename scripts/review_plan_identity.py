"""Shared source-plan identity helpers for plan-review record pairs."""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path


IDENTITY_FIELD = "plan_identity"


def repository_root(path: Path) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    return Path(result.stdout.strip()).resolve() if result.returncode == 0 else None


def normalize_plan_path(path: Path, repo_root: Path) -> str | None:
    try:
        return path.expanduser().resolve().relative_to(repo_root.resolve()).as_posix()
    except (OSError, ValueError):
        return None


def identity_token(identity: str) -> str:
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:8]


def markdown_identity(text: str) -> str | None:
    # Section-scoped: only the actual ``## Metadata`` section binds
    # identity; the same line in body or fenced content never does.
    for section in re.split(r"^## ", text, flags=re.MULTILINE):
        if not section.startswith("Metadata"):
            continue
        section = re.sub(r"```.*?```", "", section, flags=re.DOTALL)
        match = re.search(r"^- URL or Artifact: (.+?)\s*$", section, re.MULTILINE)
        break
    else:
        return None
    if match is None:
        return None
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] == "`":
        value = value[1:-1].strip()
    return Path(value).as_posix()


def record_identity(markdown: Path, payload: object) -> str | None:
    if isinstance(payload, dict):
        extensions = payload.get("extensions")
        if isinstance(extensions, dict) and IDENTITY_FIELD in extensions:
            identity = extensions[IDENTITY_FIELD]
            if isinstance(identity, str) and identity.strip():
                return Path(identity).as_posix()
            return None
    try:
        return markdown_identity(markdown.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return None
