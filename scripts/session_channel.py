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
agree. v4 adds ``CODEX_SESSION_ID`` as the FINAL fallback (the Codex source is
not a generic ``SESSION_ID`` fallback); the Claude/Cursor precedence is
unchanged. Each agent normally sets only its own var; see
``agents/hooks/lessons-recall/README.md`` (Session channel precedence).
v5 adds an explicit ``--session-id <value>`` identity input that outranks
ALL environment sources (the ZCode marker source: a runtime whose session
identity lives in runtime context, not the subprocess environment, passes
it here); an EMPTY explicit value is a fail-loud caller error (nonzero
exit, empty stdout) that never falls back to env and never keys the shared
``no-session``. Callers without the flag keep the env precedence unchanged.
"""

from __future__ import annotations

import os
import sys

CLAUDE_SESSION_ENV = "CLAUDE_CODE_SESSION_ID"
CURSOR_SESSION_ENV = "CURSOR_SESSION_ID"
CURSOR_CONVERSATION_ENV = "CURSOR_CONVERSATION_ID"
CODEX_SESSION_ENV = "CODEX_SESSION_ID"


def _derive() -> str:
    """Return the per-session channel value (Claude, then Cursor hook, then
    Cursor agent, then Codex)."""
    return (
        os.environ.get(CLAUDE_SESSION_ENV)
        or os.environ.get(CURSOR_SESSION_ENV)
        or os.environ.get(CURSOR_CONVERSATION_ENV)
        or os.environ.get(CODEX_SESSION_ENV)
        or ""
    )


def _explicit_session_id(args: list[str]) -> tuple[bool, str]:
    """Return ``(present, value)`` for the explicit ``--session-id`` input.

    The explicit identity outranks EVERY environment source (v5, the ZCode
    marker source: a runtime whose session identity lives in runtime
    context, not the subprocess environment, passes it here). A missing
    value is an EMPTY explicit identity, so a bare flag fails loud instead
    of silently falling back."""
    for i, a in enumerate(args):
        if a == "--session-id":
            return True, args[i + 1] if i + 1 < len(args) else ""
        if a.startswith("--session-id="):
            return True, a[len("--session-id="):]
    return False, ""


def _empty_explicit_identity_error() -> int:
    """Fail loud BEFORE any stdout byte: an empty explicit identity must
    never fall back to the environment and must never key the shared
    ``no-session`` marker namespace."""
    sys.stderr.write(
        "session_channel.py: explicit --session-id is empty; refusing to "
        "derive a value (an empty explicit identity never falls back to the "
        "environment or the no-session key)\n")
    return 2


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    # The explicit-identity parse runs BEFORE the selftest dispatch (r1-F10):
    # an explicit --session-id value (space or equals form) is OPAQUE DATA, so
    # a mode-token-shaped value (e.g. ``--session-id --selftest``) must print
    # verbatim, never route to selftest mode. With BOTH tokens the order is
    # position-independent: the explicit --session-id token always takes the
    # explicit branch (e.g. ``--selftest --session-id=x`` prints x, rc 0).
    # With NO --session-id token present, the dispatch below behaves exactly
    # as before.
    explicit_present, explicit_value = _explicit_session_id(args)
    if explicit_present:
        if explicit_value.strip() == "":
            return _empty_explicit_identity_error()
        # NO trailing newline (r11-L9): the $(...) capture is independent of
        # the shell's newline-stripping. The explicit value is printed
        # VERBATIM (no strip): the core hashes exactly what it receives.
        sys.stdout.write(explicit_value)
        return 0
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


def _capture_main(argv: list[str] | None = None) -> tuple[int, str]:
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main([] if argv is None else argv)
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
    """Selftests for session channel derivation: in-memory derivation arms
    plus v5 subprocess marker arms (explicit identity, injected runtime
    dir)."""
    args = sys.argv[1:] if argv is None else argv
    filter_name: str | None = None
    for a in args:
        if a.startswith("--selftest#"):
            filter_name = a[len("--selftest#") :]
            break

    all_ok = True
    arms_run = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal all_ok, arms_run
        if filter_name is not None and filter_name not in label:
            return
        arms_run += 1
        all_ok = _selftest_check(label, condition, detail) and all_ok

    env_names = (CLAUDE_SESSION_ENV, CURSOR_SESSION_ENV,
                 CURSOR_CONVERSATION_ENV, CODEX_SESSION_ENV)

    # ------------------------------------------------------------------ #
    # v1 arms (derive_session_channel_env_var): Claude env only.
    # ------------------------------------------------------------------ #
    saved = _save_env(*env_names)
    try:
        os.environ.pop(CURSOR_SESSION_ENV, None)
        os.environ.pop(CURSOR_CONVERSATION_ENV, None)
        os.environ.pop(CODEX_SESSION_ENV, None)
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
        os.environ.pop(CODEX_SESSION_ENV, None)
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
        os.environ.pop(CODEX_SESSION_ENV, None)
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
        os.environ.pop(CODEX_SESSION_ENV, None)
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
        os.environ.pop(CODEX_SESSION_ENV, None)
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
            os.environ.pop(CODEX_SESSION_ENV, None)
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
        os.environ.pop(CODEX_SESSION_ENV, None)
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
        os.environ.pop(CODEX_SESSION_ENV, None)
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
        os.environ.pop(CODEX_SESSION_ENV, None)
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
        os.environ.pop(CODEX_SESSION_ENV, None)
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
        os.environ.pop(CODEX_SESSION_ENV, None)
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
        os.environ.pop(CODEX_SESSION_ENV, None)
        os.environ[CURSOR_CONVERSATION_ENV] = ""
        rc, out = _capture_main()
        check(
            "cursor_conversation_empty_string: empty conversation, others unset -> stdout empty",
            rc == 0 and out == "",
            repr(out),
        )
    finally:
        _restore_env(saved)

    saved = _save_env(*env_names, "SESSION_ID")
    try:
        os.environ.pop(CLAUDE_SESSION_ENV, None)
        os.environ.pop(CURSOR_SESSION_ENV, None)
        os.environ.pop(CURSOR_CONVERSATION_ENV, None)
        os.environ.pop(CODEX_SESSION_ENV, None)
        os.environ["SESSION_ID"] = "generic-sess"
        rc, out = _capture_main()
        generic_ignored = rc == 0 and out == ""
        rc2, out2 = _capture_main(["--session-id", "zcode-sess-A"])
        check(
            "generic_session_id_never_fallback_and_explicit_beats_it: SESSION_ID set, recognized vars unset -> empty stdout; explicit input -> explicit value",
            generic_ignored and rc2 == 0 and out2 == "zcode-sess-A",
            f"generic={rc},{out!r} explicit={rc2},{out2!r}",
        )
    finally:
        _restore_env(saved)

    # ------------------------------------------------------------------ #
    # v4 arms: CODEX_SESSION_ID (final fallback).
    # ------------------------------------------------------------------ #
    saved = _save_env(*env_names)
    try:
        os.environ.pop(CLAUDE_SESSION_ENV, None)
        os.environ.pop(CURSOR_SESSION_ENV, None)
        os.environ.pop(CURSOR_CONVERSATION_ENV, None)
        os.environ[CODEX_SESSION_ENV] = "codex-sess-9"
        rc, out = _capture_main()
        check(
            "codex_session_id_fallback: Codex set, others unset -> Codex value",
            rc == 0 and out == "codex-sess-9",
            repr(out),
        )
    finally:
        _restore_env(saved)

    saved = _save_env(*env_names)
    try:
        os.environ.pop(CLAUDE_SESSION_ENV, None)
        os.environ.pop(CURSOR_SESSION_ENV, None)
        os.environ.pop(CURSOR_CONVERSATION_ENV, None)
        os.environ[CODEX_SESSION_ENV] = ""
        rc, out = _capture_main()
        check(
            "codex_empty_string_env: Codex empty, others unset -> stdout empty",
            rc == 0 and out == "",
            repr(out),
        )
    finally:
        _restore_env(saved)

    saved = _save_env(*env_names)
    try:
        os.environ[CLAUDE_SESSION_ENV] = "claude-sess"
        os.environ.pop(CURSOR_SESSION_ENV, None)
        os.environ.pop(CURSOR_CONVERSATION_ENV, None)
        os.environ[CODEX_SESSION_ENV] = "codex-sess-9"
        rc, out = _capture_main()
        check(
            "precedence_claude_over_codex: Claude + Codex -> Claude value",
            rc == 0 and out == "claude-sess",
            repr(out),
        )
    finally:
        _restore_env(saved)

    saved = _save_env(*env_names)
    try:
        os.environ.pop(CLAUDE_SESSION_ENV, None)
        os.environ[CURSOR_SESSION_ENV] = "cursor-sess"
        os.environ.pop(CURSOR_CONVERSATION_ENV, None)
        os.environ[CODEX_SESSION_ENV] = "codex-sess-9"
        rc, out = _capture_main()
        check(
            "precedence_cursor_session_over_codex: session + Codex -> session value",
            rc == 0 and out == "cursor-sess",
            repr(out),
        )
    finally:
        _restore_env(saved)

    saved = _save_env(*env_names)
    try:
        os.environ.pop(CLAUDE_SESSION_ENV, None)
        os.environ.pop(CURSOR_SESSION_ENV, None)
        os.environ[CURSOR_CONVERSATION_ENV] = "conv-123"
        os.environ[CODEX_SESSION_ENV] = "codex-sess-9"
        rc, out = _capture_main()
        check(
            "precedence_cursor_conversation_over_codex: conversation + Codex -> conversation value",
            rc == 0 and out == "conv-123",
            repr(out),
        )
    finally:
        _restore_env(saved)

    saved = _save_env(*env_names)
    try:
        os.environ[CLAUDE_SESSION_ENV] = "claude-sess"
        os.environ[CURSOR_SESSION_ENV] = "cursor-sess"
        os.environ[CURSOR_CONVERSATION_ENV] = "conv-123"
        os.environ[CODEX_SESSION_ENV] = "codex-sess-9"
        rc, out = _capture_main()
        check(
            "precedence_full_chain: all four sources set -> Claude value",
            rc == 0 and out == "claude-sess",
            repr(out),
        )
    finally:
        _restore_env(saved)

    # ------------------------------------------------------------------ #
    # v5 arms: explicit --session-id identity input (the ZCode marker
    # source). The explicit identity outranks EVERY environment source; an
    # EMPTY explicit identity is the caller's fail-loud error (nonzero exit,
    # empty stdout) that never falls back to env and never keys the shared
    # ``no-session``. The marker arms simulate the marker recipe chain
    # against an INJECTED temporary runtime directory (HOME override in the
    # subprocess env) and an explicit project root (--cwd), invoking the
    # marker core (skill_gate.py) the way the production recipes do: as a
    # SUBPROCESS, never an import (the cores never import this module).
    # ------------------------------------------------------------------ #
    import io
    import subprocess
    import tempfile
    from contextlib import redirect_stderr, redirect_stdout
    from pathlib import Path

    helper_path = Path(__file__).resolve()
    core_path = helper_path.parent / "skill_gate.py"

    def _v5_capture_main(argv: list[str]) -> tuple[int, str, str]:
        out_buf, err_buf = io.StringIO(), io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = main(list(argv))
        return rc, out_buf.getvalue(), err_buf.getvalue()

    def _v5_env(home: Path, code_value: str | None) -> dict[str, str]:
        env = dict(os.environ)
        env["HOME"] = str(home)
        for name in env_names:
            env.pop(name, None)
        if code_value is not None:
            env[CODEX_SESSION_ENV] = code_value
        return env

    def _v5_run_helper(args: list[str], env: dict[str, str]) -> tuple[int, str, str]:
        proc = subprocess.run(
            [sys.executable, str(helper_path), *args],
            capture_output=True, text=True, env=env, timeout=60)
        return proc.returncode, proc.stdout, proc.stderr

    def _v5_run_core(sid: str | None, project_root: Path, home: Path) -> tuple[int, str]:
        cmd = [sys.executable, str(core_path), "--write-marker", "learn",
               "--cwd", str(project_root)]
        if sid is not None:
            cmd += ["--session-id", sid]
        proc = subprocess.run(
            cmd, capture_output=True, text=True, env=_v5_env(home, None),
            timeout=60)
        return proc.returncode, proc.stderr

    def _v5_recipe_write(
        *, explicit: str | None, code_value: str | None,
        home: Path, project_root: Path,
    ) -> tuple[bool, int, str, str, str]:
        """One marker-recipe pass: derive SID via the helper subprocess,
        then apply the recipe's fail-loud discipline (abort BEFORE the
        marker core on a nonzero helper exit); an env-only empty SID omits
        ``--session-id`` (existing adapter behavior). Returns (core invoked,
        core rc when invoked else helper rc, core stderr span when invoked
        else "", helper stdout, helper stderr)."""
        args = [] if explicit is None else ["--session-id", explicit]
        rc, out, err = _v5_run_helper(args, _v5_env(home, code_value))
        if rc != 0:
            return False, rc, "", out, err
        core_rc, core_err = _v5_run_core(out or None, project_root, home)
        return True, core_rc, core_err, out, err

    def _v5_marker_names(runtime: Path) -> list[str]:
        return sorted(p.name for p in runtime.glob("learn.*.marker"))

    saved = _save_env(*env_names)
    try:
        os.environ[CLAUDE_SESSION_ENV] = "claude-sess"
        os.environ[CURSOR_SESSION_ENV] = "cursor-sess"
        os.environ[CURSOR_CONVERSATION_ENV] = "conv-123"
        os.environ[CODEX_SESSION_ENV] = "codex-sess-9"
        rc, out = _capture_main(["--session-id", "zcode-sess-A"])
        check(
            "explicit_session_id_wins_over_full_env_chain: explicit + all four env -> explicit value",
            rc == 0 and out == "zcode-sess-A",
            repr((rc, out)),
        )
    finally:
        _restore_env(saved)

    saved = _save_env(*env_names)
    try:
        os.environ[CODEX_SESSION_ENV] = "codex-sess-9"
        rc1, out1 = _capture_main(["--session-id", "zcode-sess-A"])
        rc2, out2 = _capture_main(["--session-id", "zcode-sess-B"])
        check(
            "explicit_session_id_two_identities_win_unchanged: each explicit value wins over Codex env",
            rc1 == 0 and out1 == "zcode-sess-A" and rc2 == 0 and out2 == "zcode-sess-B",
            repr((rc1, out1, rc2, out2)),
        )
    finally:
        _restore_env(saved)

    saved = _save_env(*env_names)
    try:
        os.environ[CODEX_SESSION_ENV] = "codex-sess-9"
        rc, out, err = _v5_capture_main(["--session-id", ""])
        check(
            "explicit_empty_identity_fails_loud: empty explicit + Codex env -> nonzero rc, empty stdout, no env fallback",
            rc != 0 and out == "" and err != "",
            repr((rc, out, err)),
        )
        rc, out, err = _v5_capture_main(["--session-id"])
        check(
            "explicit_missing_value_fails_loud: bare --session-id -> nonzero rc, empty stdout",
            rc != 0 and out == "" and err != "",
            repr((rc, out, err)),
        )
        rc, out, err = _v5_capture_main(["--session-id", "   "])
        check(
            "explicit_whitespace_identity_fails_loud: whitespace-only explicit -> nonzero rc, empty stdout",
            rc != 0 and out == "" and err != "",
            repr((rc, out, err)),
        )
    finally:
        _restore_env(saved)

    saved = _save_env(*env_names)
    try:
        os.environ[CODEX_SESSION_ENV] = "codex-sess-9"
        rc, out = _capture_main(["--session-id=abc"])
        check(
            "explicit_session_id_equals_form_wins: equals-form value -> verbatim stdout, rc 0",
            rc == 0 and out == "abc",
            repr((rc, out)),
        )
        rc, out, err = _v5_capture_main(["--session-id="])
        check(
            "explicit_equals_empty_identity_fails_loud: equals-form empty -> rc 2, empty stdout",
            rc == 2 and out == "" and err != "",
            repr((rc, out, err)),
        )
        rc, out = _capture_main(["--session-id", "  padded-sess  "])
        check(
            "explicit_identity_printed_verbatim_no_strip: whitespace-padded value -> byte-exact stdout",
            rc == 0 and out == "  padded-sess  ",
            repr((rc, out)),
        )
        rc, out = _capture_main(["--session-id", "--selftest"])
        check(
            "explicit_mode_token_value_not_routed_to_selftest: --session-id --selftest -> verbatim value, rc 0, no PASS lines",
            rc == 0 and out == "--selftest" and "PASS" not in out,
            repr((rc, out)),
        )
        rc, out = _capture_main(["--selftest", "--session-id=x"])
        check(
            "explicit_session_id_token_any_position_takes_explicit_branch_suppresses_selftest: --selftest --session-id=x -> explicit branch wins in ANY position, prints x rc 0, no PASS lines",
            rc == 0 and out == "x" and "PASS" not in out,
            repr((rc, out)),
        )
    finally:
        _restore_env(saved)

    with tempfile.TemporaryDirectory(prefix="session-channel-v5-a") as td:
        root = Path(td)
        home_a, project_a = root / "home-a", root / "project-a"
        home_a.mkdir()
        project_a.mkdir()
        runtime_a = home_a / ".ai-playbook" / "runtime" / "skill-invoked"
        invoked, rc, core_err, out, _err = _v5_recipe_write(
            explicit="zcode-sess-A", code_value="codex-sess-9",
            home=home_a, project_root=project_a)
        check(
            "marker_recipe_session_a: explicit ZCode identity writes its own marker key",
            invoked and rc == 0 and out == "zcode-sess-A",
            repr((invoked, rc, out, core_err)),
        )
        _v5_recipe_write(explicit="zcode-sess-B", code_value="codex-sess-9",
                         home=home_a, project_root=project_a)
        names = _v5_marker_names(runtime_a)
        components = {name.split(".")[2] for name in names}
        check(
            "marker_two_zcode_sessions_distinct_keys: two distinct sessions -> two distinct keys, no no-session key",
            len(names) == 2 and len(components) == 2
            and all("no-session" not in name for name in names),
            repr(names),
        )
        invoked3, rc3, core_err3, _out3, _err3 = _v5_recipe_write(
            explicit="zcode-sess-A", code_value="codex-sess-9",
            home=home_a, project_root=project_a)
        names_again = _v5_marker_names(runtime_a)
        check(
            "marker_repeated_write_same_session_same_key: repeated session-A write -> core invoked rc 0, same keys",
            invoked3 and rc3 == 0 and names_again == names,
            repr((invoked3, rc3, core_err3, names, names_again)),
        )

    with tempfile.TemporaryDirectory(prefix="session-channel-v5-b") as td:
        root = Path(td)
        home_b, project_b = root / "home-b", root / "project-b"
        home_b.mkdir()
        project_b.mkdir()
        runtime_b = home_b / ".ai-playbook" / "runtime" / "skill-invoked"
        invoked, rc, _core_err, out, err = _v5_recipe_write(
            explicit="", code_value="codex-sess-9",
            home=home_b, project_root=project_b)
        check(
            "marker_empty_explicit_identity_fails_before_core: helper nonzero + empty stdout, core NOT invoked",
            (not invoked) and rc != 0 and out == "" and err != "",
            repr((invoked, rc, out, err)),
        )
        leftovers = _v5_marker_names(runtime_b)
        check(
            "marker_empty_explicit_identity_no_no_session_marker: injected runtime dir holds no shared-key marker",
            not leftovers,
            repr(leftovers),
        )

    with tempfile.TemporaryDirectory(prefix="session-channel-v5-c") as td:
        root = Path(td)
        home_c, project_c = root / "home-c", root / "project-c"
        home_c.mkdir()
        project_c.mkdir()
        runtime_c = home_c / ".ai-playbook" / "runtime" / "skill-invoked"
        invoked, rc, core_err, out, _err = _v5_recipe_write(
            explicit=None, code_value=None,
            home=home_c, project_root=project_c)
        names_c = _v5_marker_names(runtime_c)
        check(
            "marker_env_only_caller_keeps_no_session: no explicit, env unset -> core invoked, no-session key preserved",
            invoked and rc == 0 and out == ""
            and len(names_c) == 1 and "no-session" in names_c[0],
            repr((invoked, rc, out, core_err, names_c)),
        )

    print()
    if filter_name is not None and arms_run == 0:
        print(f"NO ARMS MATCHED (filter: {filter_name})")
        return 1
    if filter_name is not None and all_ok:
        print(f"ALL PASS ({arms_run} arms; filter: {filter_name})")
    elif all_ok:
        print("ALL PASS")
    else:
        print("SOME FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
