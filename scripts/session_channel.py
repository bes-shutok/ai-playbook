#!/usr/bin/env python3
"""Session-channel helper leaf (r10-B1 Decision 1).

Stdlib-only ``scripts/`` leaf (same tier as ``facts_paths.py`` /
``lessons_corpus.py``). It is the SINGLE source of the per-session channel value
across BOTH hooks' adapters AND the plans-skill marker recipe. Each consumer
invokes it as a SUBPROCESS:

    SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"

and OMITS ``--session-id`` when ``SID`` is empty. The cores
(``lessons_recall.py``, ``skill_gate.py``) NEVER import this module - they
accept ``--session-id`` as OPAQUE data, so the agent-agnostic-core invariant
holds and "cores depend only downward" stays true (Family D single source
enforced by a real shared artifact, NOT an import; Family F avoided).

The helper prints ``_derive()`` via ``sys.stdout.write`` with NO trailing
newline, so the captured value is independent of the shell's newline-stripping
(r11-L9).

v9: ``CLAUDE_CODE_SESSION_ID`` only (Claude). v2 adds optional
``CURSOR_SESSION_ID`` (Cursor session bridge) with **Claude-first precedence**
when both are set in the same subprocess. When the Cursor env is unset, stdout
is byte-identical to v9. v3 adds ``CURSOR_CONVERSATION_ID`` as a Cursor agent-shell
fallback: Cursor injects that into the agent process but only injects
``CURSOR_SESSION_ID`` into hook subprocesses (via ``cursor-session-bridge.sh``).
The conversation id matches the bridged session id for the same composer tab, so
marker writers (learn/plans skills in the agent shell) and gate readers (hooks)
agree. Each agent normally sets only its own var; see
``agents/hooks/lessons-recall/README.md`` (Session channel precedence).
"""

from __future__ import annotations

import os
import sys

CLAUDE_SESSION_ENV = "CLAUDE_CODE_SESSION_ID"
CURSOR_SESSION_ENV = "CURSOR_SESSION_ID"
CURSOR_CONVERSATION_ENV = "CURSOR_CONVERSATION_ID"


def _derive() -> str:
    """Return the per-session channel value (Claude, then Cursor hook, then Cursor agent)."""
    return (
        os.environ.get(CLAUDE_SESSION_ENV)
        or os.environ.get(CURSOR_SESSION_ENV)
        or os.environ.get(CURSOR_CONVERSATION_ENV)
        or ""
    )


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if "--selftest" in args or any(a.startswith("--selftest#") for a in args):
        return selftest(args)
    # NO trailing newline (r11-L9): the $(...) capture is independent of the
    # shell's newline-stripping.
    sys.stdout.write(_derive())
    return 0


def _selftest_check(label: str, condition: bool, detail: str = "") -> bool:
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}" + (f" - {detail}" if detail else ""))
    return condition


def _capture_main() -> tuple[int, str]:
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main([])
    return rc, buf.getvalue()


def _save_env(*names: str) -> dict[str, str | None]:
    return {name: os.environ.get(name) for name in names}


def _restore_env(saved: dict[str, str | None]) -> None:
    for name, value in saved.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


def selftest(argv: list[str] | None = None) -> int:
    """In-memory selftests for session channel derivation."""
    args = sys.argv[1:] if argv is None else argv
    filter_name: str | None = None
    for a in args:
        if a.startswith("--selftest#"):
            filter_name = a[len("--selftest#") :]
            break

    all_ok = True

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal all_ok
        if filter_name is not None and filter_name not in label:
            return
        all_ok = _selftest_check(label, condition, detail) and all_ok

    env_names = (CLAUDE_SESSION_ENV, CURSOR_SESSION_ENV, CURSOR_CONVERSATION_ENV)

    # ------------------------------------------------------------------ #
    # v1 arms (derive_session_channel_env_var): Claude env only.
    # ------------------------------------------------------------------ #
    saved = _save_env(*env_names)
    try:
        os.environ.pop(CURSOR_SESSION_ENV, None)
        os.environ.pop(CURSOR_CONVERSATION_ENV, None)
        os.environ[CLAUDE_SESSION_ENV] = "abc-123"
        rc, out = _capture_main()
        check(
            "derive_session_channel_env_var: SET -> stdout is that value",
            rc == 0 and out == "abc-123",
            repr(out),
        )
    finally:
        _restore_env(saved)

    saved = _save_env(*env_names)
    try:
        os.environ.pop(CLAUDE_SESSION_ENV, None)
        os.environ.pop(CURSOR_SESSION_ENV, None)
        os.environ.pop(CURSOR_CONVERSATION_ENV, None)
        rc, out = _capture_main()
        check(
            "derive_session_channel_env_var: UNSET -> stdout empty",
            rc == 0 and out == "",
            repr(out),
        )
    finally:
        _restore_env(saved)

    saved = _save_env(*env_names)
    try:
        os.environ.pop(CURSOR_SESSION_ENV, None)
        os.environ.pop(CURSOR_CONVERSATION_ENV, None)
        os.environ[CLAUDE_SESSION_ENV] = ""
        rc, out = _capture_main()
        check(
            "derive_session_channel_env_var: empty-string env -> stdout empty",
            rc == 0 and out == "",
            repr(out),
        )
    finally:
        _restore_env(saved)

    # ------------------------------------------------------------------ #
    # v2 arms: optional Cursor env (bridge).
    # ------------------------------------------------------------------ #
    saved = _save_env(*env_names)
    try:
        os.environ.pop(CLAUDE_SESSION_ENV, None)
        os.environ.pop(CURSOR_CONVERSATION_ENV, None)
        os.environ[CURSOR_SESSION_ENV] = "abc-123"
        rc, out = _capture_main()
        check(
            "cursor_session_id_from_env: Cursor set, Claude unset -> Cursor value",
            rc == 0 and out == "abc-123",
            repr(out),
        )
    finally:
        _restore_env(saved)

    saved = _save_env(*env_names)
    try:
        os.environ[CLAUDE_SESSION_ENV] = "claude-sess"
        os.environ[CURSOR_SESSION_ENV] = "cursor-sess"
        os.environ.pop(CURSOR_CONVERSATION_ENV, None)
        rc, out = _capture_main()
        check(
            "precedence_claude_over_cursor: both set -> Claude value",
            rc == 0 and out == "claude-sess",
            repr(out),
        )
    finally:
        _restore_env(saved)

    # v1_fallback_unchanged: pre-v2 arms with Cursor env unset.
    for label_suffix, claude_value, expected in (
        ("SET", "abc-123", "abc-123"),
        ("UNSET", None, ""),
        ("empty-string", "", ""),
    ):
        saved = _save_env(*env_names)
        try:
            os.environ.pop(CURSOR_SESSION_ENV, None)
            os.environ.pop(CURSOR_CONVERSATION_ENV, None)
            if claude_value is None:
                os.environ.pop(CLAUDE_SESSION_ENV, None)
            else:
                os.environ[CLAUDE_SESSION_ENV] = claude_value
            rc, out = _capture_main()
            check(
                f"v1_fallback_unchanged: Claude {label_suffix} with Cursor unset -> v1 stdout",
                rc == 0 and out == expected,
                repr(out),
            )
        finally:
            _restore_env(saved)

    saved = _save_env(*env_names)
    try:
        os.environ.pop(CLAUDE_SESSION_ENV, None)
        os.environ.pop(CURSOR_CONVERSATION_ENV, None)
        os.environ[CURSOR_SESSION_ENV] = ""
        rc, out = _capture_main()
        check(
            "cursor_empty_string_env: Cursor empty, Claude unset -> stdout empty",
            rc == 0 and out == "",
            repr(out),
        )
    finally:
        _restore_env(saved)

    saved = _save_env(*env_names)
    try:
        os.environ[CLAUDE_SESSION_ENV] = "claude-only"
        os.environ[CURSOR_SESSION_ENV] = ""
        os.environ.pop(CURSOR_CONVERSATION_ENV, None)
        rc, out = _capture_main()
        check(
            "cursor_empty_string_env: Cursor empty, Claude set -> Claude value",
            rc == 0 and out == "claude-only",
            repr(out),
        )
    finally:
        _restore_env(saved)

    # ------------------------------------------------------------------ #
    # v3 arms: CURSOR_CONVERSATION_ID (agent-shell fallback).
    # ------------------------------------------------------------------ #
    saved = _save_env(*env_names)
    try:
        os.environ.pop(CLAUDE_SESSION_ENV, None)
        os.environ.pop(CURSOR_SESSION_ENV, None)
        os.environ[CURSOR_CONVERSATION_ENV] = "conv-123"
        rc, out = _capture_main()
        check(
            "cursor_conversation_id_fallback: conversation set, session unset -> conversation value",
            rc == 0 and out == "conv-123",
            repr(out),
        )
    finally:
        _restore_env(saved)

    saved = _save_env(*env_names)
    try:
        os.environ.pop(CLAUDE_SESSION_ENV, None)
        os.environ[CURSOR_SESSION_ENV] = "cursor-sess"
        os.environ[CURSOR_CONVERSATION_ENV] = "conv-123"
        rc, out = _capture_main()
        check(
            "precedence_cursor_session_over_conversation: both set -> session value",
            rc == 0 and out == "cursor-sess",
            repr(out),
        )
    finally:
        _restore_env(saved)

    saved = _save_env(*env_names)
    try:
        os.environ[CLAUDE_SESSION_ENV] = "claude-sess"
        os.environ.pop(CURSOR_SESSION_ENV, None)
        os.environ[CURSOR_CONVERSATION_ENV] = "conv-123"
        rc, out = _capture_main()
        check(
            "precedence_claude_over_conversation: Claude + conversation -> Claude value",
            rc == 0 and out == "claude-sess",
            repr(out),
        )
    finally:
        _restore_env(saved)

    saved = _save_env(*env_names)
    try:
        os.environ.pop(CLAUDE_SESSION_ENV, None)
        os.environ.pop(CURSOR_SESSION_ENV, None)
        os.environ[CURSOR_CONVERSATION_ENV] = ""
        rc, out = _capture_main()
        check(
            "cursor_conversation_empty_string: empty conversation, others unset -> stdout empty",
            rc == 0 and out == "",
            repr(out),
        )
    finally:
        _restore_env(saved)

    print()
    if filter_name is not None and all_ok:
        print(f"ALL PASS (filter: {filter_name})")
    elif all_ok:
        print("ALL PASS")
    else:
        print("SOME FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
