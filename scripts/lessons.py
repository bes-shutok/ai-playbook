#!/usr/bin/env python3
"""Single CLI entry point for the lessons tool family (harness triage plan,
Task 7; origin 2026-09-18-harness-paperkeeping-triage-dismantle direction 4:
"Consolidate the lessons scripts behind one entry point with subcommands").

This hub owns ALL lessons CLI dispatch. The five modules stay in place as
importable libraries and keep their ``main(argv)`` and ``selftest()``
functions; each lost only its standalone ``if __name__ == "__main__"``
dispatch block, which moved here. ``lessons_corpus`` remains the
shared-primitives module and gains no CLI duty.

Subcommands (each delegates to the named module's ``main``):

  index <user_corpus>              validate the user-level lessons corpus
                                   (read-only; the learn Step 6.6 gate)
  adopt --tag-unclassified <file>  backfill untagged lessons with
                                   'Family unclassified' (manual tool, never
                                   invoked automatically)
  classify --selftest              prompt-classifier fixtures (selftest only)
  migrate <project_lessons> [--dry-run]
                                   cross-project lesson migration (the module
                                   accepts --dry-run anywhere among its args)
  recall [--prompt P] [--session-id S] [--state-dir D] [--budget N]
         [--no-dedup] [--classifier C] [--selftest]
                                   the agent-agnostic recall core (the
                                   lessons-recall hooks call this subcommand)
  selftest [--all | MODULE]        run one module's selftest, or all five

Exit codes follow the delegated module: 0 ok, 1 failure, 2 usage error.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lessons_adopt  # noqa: E402
import lessons_classify  # noqa: E402
import lessons_index  # noqa: E402
import lessons_migrate  # noqa: E402
import lessons_recall  # noqa: E402

#: Subcommand -> module owning that subcommand's dispatch. The module keeps
#: ``main(argv)`` and ``selftest()``; the hub adds nothing per-subcommand.
_MODULES = {
    "index": lessons_index,
    "adopt": lessons_adopt,
    "classify": lessons_classify,
    "migrate": lessons_migrate,
    "recall": lessons_recall,
}

#: Stable module order for the aggregate selftest report.
_MODULE_ORDER = ("index", "adopt", "classify", "migrate", "recall")

_HUB = Path(__file__).name

_USAGE = f"""usage: {_HUB} <subcommand> [args]

subcommands:
  index <user_corpus>               validate the user-level lessons corpus
  adopt --tag-unclassified <file>   backfill untagged lessons (manual tool)
  classify --selftest               classifier fixtures (selftest only)
  migrate <project_lessons> [--dry-run]
                                    cross-project lesson migration
  recall [--prompt P] [--session-id S] [flags]
                                    agent-agnostic recall core
  selftest [--all | MODULE]         one module's selftest, or all five
                                    (MODULE: {" | ".join(_MODULE_ORDER)})
"""


def _run_selftest_all() -> int:
    """Run every module's selftest in stable order; report one line per
    module plus an aggregate verdict. Return 0 only when all pass."""
    results: list[tuple[str, int]] = []
    for name in _MODULE_ORDER:
        rc = _MODULES[name].selftest()
        results.append((name, rc))
        print(f"{_HUB} selftest: {name} {'OK' if rc == 0 else 'FAILED'}")
    failed = [name for name, rc in results if rc != 0]
    passed = len(results) - len(failed)
    if not failed:
        print(f"{_HUB} selftest --all: OK ({passed}/{len(results)} modules)")
        return 0
    print(
        f"{_HUB} selftest --all: FAILED ({passed}/{len(results)} passed; "
        f"failing: {', '.join(failed)})"
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        sys.stderr.write(_USAGE)
        return 2
    cmd, rest = args[0], args[1:]
    if cmd == "selftest":
        if not rest or rest == ["--all"]:
            return _run_selftest_all()
        if len(rest) == 1 and rest[0] in _MODULES:
            return _MODULES[rest[0]].selftest()
        sys.stderr.write(
            f"{_HUB}: selftest takes --all or one of: "
            f"{', '.join(_MODULE_ORDER)}\n"
        )
        return 2
    module = _MODULES.get(cmd)
    if module is None:
        sys.stderr.write(f"{_HUB}: unknown subcommand {cmd!r}\n{_USAGE}")
        return 2
    return module.main(rest)


if __name__ == "__main__":
    raise SystemExit(main())
