#!/usr/bin/env python3
"""Run the repository's live required-test inventory with bounded children.

The runner owns the inventory and aggregate timers. A source suite is admitted
once, discovered in the configured test environment, and executed as complete
unittest classes or bounded pytest node groups. Unknown effects serialize.
"""
from __future__ import annotations

import argparse
import ast
import asyncio
import copy
import hashlib
import importlib.util
import inspect
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
import unittest
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


MARKER = "__AI_PLAYBOOK_REQUIRED_SUITE_JSON__="
DEFAULT_PER_SCRIPT_TIMEOUT = 60.0
DEFAULT_SUITE_TIMEOUT = 270.0
DEFAULT_CLEANUP_GRACE = 2.0
MAX_WORKERS = 8
PYTEST_BATCH_SIZE = 16
SAFE_METHOD_BATCHES_PER_WORKER = 1


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _inventory(root: Path) -> list[Path]:
    scripts = root / "scripts"
    paths = sorted(path for path in scripts.glob("test_*.py") if path.is_file())
    for path in paths:
        resolved = path.resolve()
        try:
            resolved.relative_to(root.resolve())
        except ValueError as exc:
            raise ValueError(f"test inventory path escapes repository: {path}") from exc
    return paths


def _inventory_digest(paths: Iterable[Path], root: Path) -> tuple[str, dict[str, str]]:
    file_digests = {path.relative_to(root).as_posix(): _sha256(path) for path in paths}
    canonical = "\n".join(f"{name} {file_digests[name]}" for name in sorted(file_digests))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest(), file_digests


def _module_name(path: Path) -> str:
    return path.stem


def _module_from_path(path: Path):
    module_name = _module_name(path)
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load test module {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _flatten(suite: unittest.TestSuite) -> list[unittest.TestCase]:
    tests: list[unittest.TestCase] = []
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            tests.extend(_flatten(item))
        else:
            tests.append(item)
    return tests


def _unittest_collection(path: Path) -> dict[str, Any]:
    module = _module_from_path(path)
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    tests = _flatten(suite)
    grouped: dict[str, list[str]] = defaultdict(list)
    safe_classes = {
        test.__class__ for test in tests
        if _class_method_shards_are_safe(test.__class__)
    }
    method_shardable: dict[str, bool] = {}
    for test in tests:
        class_name = f"{test.__class__.__module__}.{test.__class__.__qualname__}"
        grouped[class_name].append(test.id())
        method_shardable[class_name] = test.__class__ in safe_classes
    return {
        "ok": True,
        "runner": "unittest",
        "test_ids": [test.id() for test in tests],
        "groups": [
            {"shard_id": class_name, "test_ids": ids,
             "method_shardable": method_shardable[class_name]}
            for class_name, ids in grouped.items()
        ],
        "method_shards": bool(safe_classes),
    }


def _writes_from_temporary_fixture_parent(text: str) -> bool:
    """Detect writes that escape a per-test root into its shared parent."""
    import re

    fixture_root = r"(?:tmp_path(?:_factory)?|self\.\w+\.name|(?:tmp|temp|temporary|scratch)\w*\.name)"
    return bool(re.search(fixture_root + r"[^\n;]{0,120}\.parent\b", text.lower()))


def _writes_to_fixed_absolute_path(text: str) -> bool:
    """Detect literal absolute write targets that a temporary fixture cannot isolate."""
    import re

    absolute = r"(?:/|[a-z]:[\\/])[^'\"]*"
    target = r"(?:path|open)\(\s*['\"]" + absolute + r"['\"][^\n;]{0,180}"
    mutation = r"(?:\.(?:write_text|write_bytes|mkdir|touch|unlink|open)\(|,\s*['\"][wax])"
    return bool(re.search(target + mutation, text.lower()))


def _writes_to_environment_path(text: str) -> bool:
    """Detect mutations whose target aliases a shared environment value."""
    import textwrap

    try:
        tree = ast.parse(textwrap.dedent(text))
    except SyntaxError:
        return True

    def environment_lookup(node: ast.AST) -> bool:
        if isinstance(node, ast.Attribute) and node.attr == "environ" and isinstance(node.value, ast.Name):
            return node.value.id == "os"
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "getenv"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "os"
        )

    mutating_methods = {"write_text", "write_bytes", "mkdir", "touch", "unlink", "open"}

    def assigned_names(target: ast.AST):
        if isinstance(target, ast.Name):
            yield target.id
        elif isinstance(target, (ast.Tuple, ast.List)):
            for item in target.elts:
                yield from assigned_names(item)

    def environment_derived(node: ast.AST, names: set[str], functions: set[str]) -> bool:
        return any(
            environment_lookup(child)
            or isinstance(child, ast.Name) and child.id in names
            or isinstance(child, ast.Call)
            and isinstance(child.func, ast.Name) and child.func.id in functions
            for child in ast.walk(node)
        )

    tainted_names: set[str] = set()
    tainted_functions: set[str] = set()
    # Propagate environment provenance through local aliases and helpers that
    # return those aliases. Unresolved derived targets must serialize; a
    # temporary fixture cannot prove that a caller-provided environment path
    # is private.
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            value = None
            targets: list[ast.AST] = []
            if isinstance(node, ast.Assign):
                value, targets = node.value, node.targets
            elif isinstance(node, ast.AnnAssign):
                value, targets = node.value, [node.target]
            elif isinstance(node, ast.NamedExpr):
                value, targets = node.value, [node.target]
            if value is not None and environment_derived(value, tainted_names, tainted_functions):
                for target in targets:
                    for name in assigned_names(target):
                        if name not in tainted_names:
                            tainted_names.add(name)
                            changed = True
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name not in tainted_functions and any(
                    isinstance(child, ast.Return) and child.value is not None
                    and environment_derived(child.value, tainted_names, tainted_functions)
                    for child in ast.walk(node)
                ):
                    tainted_functions.add(node.name)
                    changed = True

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target: ast.AST | None = None
        if isinstance(node.func, ast.Attribute) and node.func.attr in mutating_methods:
            target = node.func.value
        elif isinstance(node.func, ast.Name) and node.func.id in {"open", "remove", "unlink", "mkdir"}:
            target = node.args[0] if node.args else None
        elif (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "os"
            and node.func.attr in {"open", "remove", "unlink", "mkdir"}
        ):
            target = node.args[0] if node.args else None
        if target is not None and environment_derived(target, tainted_names, tainted_functions):
            return True
    return False


def _class_method_shards_are_safe(test_class: type[unittest.TestCase]) -> bool:
    """Allow one method per process only with per-test fixture isolation.

    Runtime MRO inspection includes inherited fixtures such as the shared
    closeout TestCase mixin; class fixtures and unknown external bases fail
    closed. Each split method is still selected from the default loader's
    already-filtered IDs, preserving any module-level ``load_tests`` policy.
    """
    if any(name in base.__dict__ for base in test_class.__mro__ if base is not unittest.TestCase
           for name in ("setUpClass", "tearDownClass")):
        return False
    fixture_sources: list[str] = []
    for base in test_class.__mro__:
        if base is unittest.TestCase:
            break
        if base is object:
            continue
        for name in ("setUp", "tearDown"):
            method = base.__dict__.get(name)
            if method is not None:
                try:
                    fixture_sources.append(inspect.getsource(method).lower())
                except (OSError, TypeError):
                    return False
    method_sources: list[str] = []
    for name in unittest.defaultTestLoader.getTestCaseNames(test_class):
        method = getattr(test_class, name, None)
        if method is None:
            return False
        try:
            method_sources.append(inspect.getsource(method).lower())
        except (OSError, TypeError):
            return False
    fixture_text = "\n".join(fixture_sources)
    method_text = "\n".join(method_sources)
    all_text = fixture_text + "\n" + method_text
    external = ("subprocess", "os.environ", "path.write", ".write_text(", ".mkdir(",
                ".unlink(", "open(", "tempfile", "socket", "git ", "self.git(", "popen(", "lock")
    has_external_effect = any(token in all_text for token in external)
    import re
    has_per_test_isolation = bool(re.search(r"\btmp_path\b", fixture_text)) or any(
        token in fixture_text for token in ("temporarydirectory", "mkdtemp(", "self.tmp")
    )
    if has_external_effect and not has_per_test_isolation:
        return False
    if has_external_effect and _writes_from_temporary_fixture_parent(all_text):
        return False
    if has_external_effect and (
        _writes_to_fixed_absolute_path(all_text)
        # Locals are function-scoped. Inspect each fixture/test body separately
        # so an alias named ``env`` in setUp cannot taint an unrelated local
        # ``env`` in a test method. The source-level scheduler intentionally
        # keeps its broader whole-file check and may still classify the file
        # as unknown-serial.
        or any(_writes_to_environment_path(source)
               for source in fixture_sources + method_sources)
    ):
        return False
    if re.search(
        r"(?:path\.home\(\)|expanduser\(\))[^\n;]{0,120}\.(?:write_text|write_bytes|mkdir|touch|unlink|open)\(",
        all_text,
    ):
        return False
    # A fixture-free assertion class is method independent. Any mutating test
    # requires an explicit unique per-test fixture before it can overlap.
    return not has_external_effect or has_per_test_isolation


def _pytest_fixture_shards_are_safe(path: Path) -> bool:
    """Prove pytest functions use only function-scoped, fixture-local effects.

    Unknown or unsupported fixtures fail closed. Environment-derived write
    paths are safe only when a function-scoped fixture binds that exact
    variable to a temporary root.
    """
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError):
        return False
    functions = {
        node.name: node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    tests = [node for node in functions.values() if node.name.startswith("test_")]
    class_context: dict[int, list[ast.AST]] = {}
    for class_node in (node for node in tree.body if isinstance(node, ast.ClassDef)):
        methods = [
            node for node in class_node.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
        ]
        if methods and any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in {"setUpClass", "tearDownClass", "setup_class", "teardown_class"}
            for node in class_node.body
        ):
            return False
        class_fixtures = [
            node for node in class_node.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in {"setUp", "tearDown", "setup_method", "teardown_method"}
        ]
        for method in methods:
            class_context[id(method)] = class_fixtures
        tests.extend(methods)
    if not tests:
        return False

    fixtures: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    fixture_scopes: dict[str, str] = {}
    for name, node in functions.items():
        for decorator in node.decorator_list:
            call = decorator.func if isinstance(decorator, ast.Call) else decorator
            if not (
                isinstance(call, ast.Attribute) and call.attr == "fixture"
                or isinstance(call, ast.Name) and call.id == "fixture"
            ):
                continue
            fixtures[name] = node
            scope = "function"
            if isinstance(decorator, ast.Call):
                scope_kw = next((kw.value for kw in decorator.keywords if kw.arg == "scope"), None)
                if scope_kw is not None:
                    scope = (
                        scope_kw.value
                        if isinstance(scope_kw, ast.Constant) and isinstance(scope_kw.value, str)
                        else "dynamic"
                    )
                elif decorator.args:
                    positional_scope = decorator.args[0]
                    scope = (
                        positional_scope.value
                        if isinstance(positional_scope, ast.Constant)
                        and isinstance(positional_scope.value, str)
                        else "dynamic"
                    )
                elif any(keyword.arg is None for keyword in decorator.keywords):
                    # A **kwargs expansion may provide a non-function scope.
                    scope = "dynamic"
            fixture_scopes[name] = scope
            break

    builtins = {
        "tmp_path", "tmp_path_factory", "monkeypatch", "capsys", "capfd",
        "request", "pytestconfig", "caplog", "recwarn",
    }
    effects = (
        "subprocess.", "os.environ", "path.write", ".write_text(", ".write_bytes(",
        ".mkdir(", ".unlink(", "open(", "tempfile.", "socket.", "git ", "popen(",
    )

    def code_without_docstrings(node: ast.AST) -> str:
        copied = copy.deepcopy(node)

        def strip(current: ast.AST) -> None:
            body = getattr(current, "body", None)
            if isinstance(body, list):
                if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                    current.body = body[1:]
                for child in getattr(current, "body", []):
                    strip(child)

        strip(copied)
        return ast.unparse(copied).lower()

    def parameter_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
        return {arg.arg for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)} - {"self", "cls"}

    def parametrized_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
        names: set[str] = set()
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            if decorator.func.attr != "parametrize" or not decorator.args:
                continue
            value = decorator.args[0]
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                names.update(part.strip() for part in value.value.split(",") if part.strip())
            elif isinstance(value, (ast.Tuple, ast.List)):
                names.update(
                    item.value for item in value.elts
                    if isinstance(item, ast.Constant) and isinstance(item.value, str)
                )
        return names

    def fixture_dependencies(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[list[ast.AST], bool, bool]:
        pending = list(parameter_names(node) - parametrized_names(node))
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and decorator.func.attr == "usefixtures":
                pending.extend(arg.value for arg in decorator.args if isinstance(arg, ast.Constant) and isinstance(arg.value, str))
        seen: set[str] = set()
        fixture_nodes: list[ast.AST] = []
        has_temp_root = False
        unresolved = False
        non_function_scope = False
        while pending:
            name = pending.pop()
            if name in seen:
                continue
            seen.add(name)
            if name == "tmp_path":
                has_temp_root = True
                continue
            if name == "tmp_path_factory":
                # Factory calls can deliberately reuse one shared directory
                # (for example mktemp(..., numbered=False)); do not treat the
                # factory itself as proof of per-test isolation.
                unresolved = True
                continue
            if name in builtins:
                continue
            fixture = fixtures.get(name)
            if fixture is None:
                unresolved = True
                continue
            fixture_nodes.append(fixture)
            non_function_scope |= fixture_scopes[name] != "function"
            pending.extend(parameter_names(fixture))
        return fixture_nodes, has_temp_root, unresolved or non_function_scope

    def helper_nodes(roots: list[ast.AST]) -> list[ast.AST]:
        helpers: list[ast.AST] = []
        seen: set[str] = set()
        pending = [
            call.func.id for root in roots for call in ast.walk(root)
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
        ]
        while pending:
            name = pending.pop()
            node = functions.get(name)
            if node is None or name in seen or name in fixtures or name.startswith("test_"):
                continue
            seen.add(name)
            helpers.append(node)
            pending.extend(
                call.func.id for call in ast.walk(node)
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
            )
        return helpers

    def names_in_target(node: ast.AST, aliases: dict[str, set[str]], environment_maps: set[str]) -> set[str]:
        names: set[str] = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                names.update(aliases.get(child.id, set()))
            elif isinstance(child, ast.Subscript) and isinstance(child.value, ast.Name) and child.value.id in environment_maps:
                key = child.slice
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    names.add(key.value)
            elif isinstance(child, ast.Subscript) and isinstance(child.value, ast.Attribute):
                if isinstance(child.value.value, ast.Name) and child.value.value.id == "os" and child.value.attr == "environ":
                    key = child.slice
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        names.add(key.value)
            elif isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                value = child.func.value
                if child.func.attr == "get" and isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name) and value.value.id == "os" and value.attr == "environ" and child.args:
                    key = child.args[0]
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        names.add(key.value)
                elif child.func.attr == "getenv" and isinstance(value, ast.Name) and value.id == "os" and child.args:
                    key = child.args[0]
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        names.add(key.value)
        return names

    def temporary_environment_names(nodes: list[ast.AST]) -> set[str]:
        scoped: set[str] = set()
        for root in nodes:
            if not isinstance(root, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            temp_names = {name for name in parameter_names(root) if name == "tmp_path"}
            root_text = ast.get_source_segment(source, root) or ""
            if "temporarydirectory(" in root_text.lower() or "mkdtemp(" in root_text.lower():
                temp_names.add("self")
            assignments = [child for child in ast.walk(root) if isinstance(child, (ast.Assign, ast.AnnAssign))]
            environment_maps: set[str] = set()
            for assignment in assignments:
                value = assignment.value
                targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
                copies_environment = value is not None and any(
                    isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name)
                    and child.value.id == "os" and child.attr == "environ"
                    for child in ast.walk(value)
                )
                if copies_environment:
                    environment_maps.update(
                        child.id for target in targets for child in ast.walk(target)
                        if isinstance(child, ast.Name)
                    )
            for _ in range(len(assignments) + 1):
                changed = False
                for assignment in assignments:
                    value = assignment.value
                    if value is None or not any(isinstance(child, ast.Name) and child.id in temp_names for child in ast.walk(value)):
                        continue
                    targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
                    for target in targets:
                        for child in ast.walk(target):
                            if isinstance(child, ast.Name) and child.id not in temp_names:
                                temp_names.add(child.id)
                                changed = True
                if not changed:
                    break
            for call in (child for child in ast.walk(root) if isinstance(child, ast.Call)):
                if not isinstance(call.func, ast.Attribute):
                    continue
                env_name = None
                value = None
                if call.func.attr == "setenv" and len(call.args) >= 2:
                    key, value = call.args[:2]
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        env_name = key.value
                elif call.func.attr == "setitem" and len(call.args) >= 3:
                    mapping, key, value = call.args[:3]
                    if isinstance(mapping, ast.Attribute) and isinstance(mapping.value, ast.Name) and mapping.value.id == "os" and mapping.attr == "environ" and isinstance(key, ast.Constant) and isinstance(key.value, str):
                        env_name = key.value
                if env_name and value is not None and any(isinstance(child, ast.Name) and child.id in temp_names for child in ast.walk(value)):
                    scoped.add(env_name)
            for assignment in (child for child in ast.walk(root) if isinstance(child, ast.Assign)):
                target = assignment.targets[0] if assignment.targets else None
                if not isinstance(target, ast.Subscript):
                    continue
                direct_environment = isinstance(target.value, ast.Attribute) and isinstance(target.value.value, ast.Name) and target.value.value.id == "os" and target.value.attr == "environ"
                copied_environment = isinstance(target.value, ast.Name) and target.value.id in environment_maps
                if not (direct_environment or copied_environment):
                    continue
                key = target.slice
                if isinstance(key, ast.Constant) and isinstance(key.value, str) and any(isinstance(child, ast.Name) and child.id in temp_names for child in ast.walk(assignment.value)):
                    scoped.add(key.value)
        return scoped

    def environment_write_targets(nodes: list[ast.AST]) -> set[str]:
        targets: set[str] = set()
        mutators = {"write_text", "write_bytes", "mkdir", "touch", "unlink", "open", "remove"}
        for root in nodes:
            aliases: dict[str, set[str]] = {}
            assignments = [child for child in ast.walk(root) if isinstance(child, (ast.Assign, ast.AnnAssign))]
            environment_maps: set[str] = set()
            for assignment in assignments:
                value = assignment.value
                assignment_targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
                copies_environment = value is not None and any(
                    isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name)
                    and child.value.id == "os" and child.attr == "environ"
                    for child in ast.walk(value)
                )
                if copies_environment:
                    environment_maps.update(
                        child.id for target in assignment_targets for child in ast.walk(target)
                        if isinstance(child, ast.Name)
                    )
            for _ in range(len(assignments) + 1):
                changed = False
                for assignment in assignments:
                    value = assignment.value
                    if value is None:
                        continue
                    discovered = names_in_target(value, aliases, environment_maps)
                    targets_to_bind = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
                    for target in targets_to_bind:
                        for child in ast.walk(target):
                            if isinstance(child, ast.Name) and discovered - aliases.get(child.id, set()):
                                aliases.setdefault(child.id, set()).update(discovered)
                                changed = True
                if not changed:
                    break
            for call in (child for child in ast.walk(root) if isinstance(child, ast.Call)):
                target = None
                if isinstance(call.func, ast.Attribute) and call.func.attr in mutators:
                    target = call.func.value
                elif isinstance(call.func, ast.Name) and call.func.id in {"open", "remove", "unlink", "mkdir"} and call.args:
                    target = call.args[0]
                elif isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and call.func.value.id == "os" and call.func.attr in {"open", "remove", "unlink", "mkdir"} and call.args:
                    target = call.args[0]
                if target is not None:
                    targets.update(names_in_target(target, aliases, environment_maps))
                    for child in ast.walk(target):
                        if isinstance(child, ast.Subscript) and isinstance(child.value, ast.Name) and child.value.id in environment_maps:
                            key = child.slice
                            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                                targets.add(key.value)
        return targets

    for test in tests:
        fixture_nodes, has_temp_root, unresolved = fixture_dependencies(test)
        class_nodes = class_context.get(id(test), [])
        if class_nodes and any(
            "temporarydirectory(" in (ast.get_source_segment(source, node) or "").lower()
            or "mkdtemp(" in (ast.get_source_segment(source, node) or "").lower()
            for node in class_nodes
        ):
            has_temp_root = True
        roots: list[ast.AST] = [test, *fixture_nodes, *class_nodes]
        nodes = [*roots, *helper_nodes(roots)]
        text = "\n".join(code_without_docstrings(node) for node in nodes)
        if not any(token in text for token in effects):
            continue
        if not has_temp_root or unresolved:
            return False
        if _writes_from_temporary_fixture_parent(text) or _writes_to_fixed_absolute_path(text):
            return False
        if _writes_to_environment_path(text):
            targets = environment_write_targets(nodes)
            scoped_paths = temporary_environment_names(nodes)
            if targets and targets - scoped_paths or not targets and not scoped_paths:
                return False
        if re.search(
            r"(?:path\.home\(\)|expanduser\(\))[^\n;]{0,120}\.(?:write_text|write_bytes|mkdir|touch|unlink|open)\(",
            text,
        ):
            return False
    return True


class _PytestCollector:
    def __init__(self):
        self.test_ids: list[str] = []

    def pytest_collection_finish(self, session):
        self.test_ids = [item.nodeid for item in session.items]


class _PytestRecorder(_PytestCollector):
    def __init__(self):
        super().__init__()
        self.started: set[str] = set()
        self.outcomes: dict[str, str] = {}

    def pytest_runtest_logstart(self, nodeid, location):
        self.started.add(nodeid)

    def pytest_runtest_logreport(self, report):
        if report.when == "call" or report.skipped or report.failed:
            if report.skipped:
                self.outcomes[report.nodeid] = "skipped"
            elif report.failed:
                self.outcomes[report.nodeid] = "error" if report.when in {"setup", "teardown"} else "failed"
            else:
                self.outcomes.setdefault(report.nodeid, "passed")


def _pytest_main(path: Path, args: list[str], plugin: Any) -> tuple[int, dict[str, Any]]:
    import pytest

    rc = int(pytest.main(
        ["-q", "-o", "addopts=", "-p", "no:cacheprovider", *args],
        plugins=[plugin],
    ))
    return rc, {"test_ids": plugin.test_ids}


def _policy(path: Path) -> str:
    """Select pytest functions, TestCase classes, or unittest load_tests."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    if any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
           for node in tree.body):
        return "pytest"
    if any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "load_tests"
           for node in tree.body):
        return "unittest"
    bases: dict[str, set[str]] = {}
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    for node in classes:
        bases[node.name] = {
            base.id if isinstance(base, ast.Name) else base.attr if isinstance(base, ast.Attribute) else ""
            for base in node.bases
        }
    unittest_names = {"TestCase"}
    changed = True
    while changed:
        changed = False
        for name, parent_names in bases.items():
            if name not in unittest_names and parent_names & unittest_names:
                unittest_names.add(name)
                changed = True
    has_unittest_test = any(
        node.name in unittest_names and any(
            isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)) and member.name.startswith("test_")
            for member in node.body
        ) for node in classes
    )
    if has_unittest_test:
        return "unittest"
    return "pytest"


def _pytest_collection(path: Path) -> dict[str, Any]:
    collector = _PytestCollector()
    rc, result = _pytest_main(path, ["--collect-only", str(path)], collector)
    result.update({"ok": rc in (0, 5), "runner": "pytest", "collection_exit": rc})
    result["groups"] = [{"shard_id": test_id, "test_ids": [test_id]} for test_id in collector.test_ids]
    return result


def _load_unittest_tests(path: Path) -> list[unittest.TestCase]:
    module = _module_from_path(path)
    return _flatten(unittest.defaultTestLoader.loadTestsFromModule(module))


class _CountingResult(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.started_ids: list[str] = []
        self.outcomes: dict[str, str] = {}

    def startTest(self, test):
        self.started_ids.append(test.id())
        super().startTest(test)

    def addSuccess(self, test):
        self.outcomes[test.id()] = "passed"
        super().addSuccess(test)

    def addFailure(self, test, err):
        self.outcomes[test.id()] = "failed"
        super().addFailure(test, err)

    def addError(self, test, err):
        self.outcomes[test.id()] = "error"
        super().addError(test, err)

    def addSkip(self, test, reason):
        self.outcomes[test.id()] = "skipped"
        super().addSkip(test, reason)

    def addExpectedFailure(self, test, err):
        self.outcomes[test.id()] = "expected_failure"
        super().addExpectedFailure(test, err)

    def addUnexpectedSuccess(self, test):
        self.outcomes[test.id()] = "failed"
        super().addUnexpectedSuccess(test)

    def addSubTest(self, test, subtest, err):
        if err is not None:
            self.outcomes[test.id()] = "failed"
        else:
            self.outcomes.setdefault(test.id(), "passed")
        super().addSubTest(test, subtest, err)


def _run_unittest_shard(path: Path, shard_id: str,
                        expected_ids: list[str] | None = None) -> dict[str, Any]:
    tests = _load_unittest_tests(path)
    if expected_ids is not None:
        tests_by_id = {test.id(): test for test in tests}
        selected = [tests_by_id[test_id] for test_id in expected_ids if test_id in tests_by_id]
    else:
        selected = [test for test in tests if (
            test.id() == shard_id
            or f"{test.__class__.__module__}.{test.__class__.__qualname__}" == shard_id
        )]
    result = _CountingResult()
    suite = unittest.TestSuite(selected)
    class _ResultTextRunner(unittest.TextTestRunner):
        def _makeResult(self):
            return result

    _ResultTextRunner(stream=sys.stdout, verbosity=1).run(suite)
    failures = len(result.failures) + len(result.errors) + len(result.unexpectedSuccesses)
    return {
        "ok": bool(selected) and failures == 0,
        "runner": "unittest",
        "collected_ids": [test.id() for test in selected],
        "executed_ids": list(result.outcomes),
        "started_ids": result.started_ids,
        "outcomes": result.outcomes,
        "collected": len(selected),
        "executed": len(result.outcomes),
        "failures": failures,
        "errors": len(result.errors),
        "skipped": len(result.skipped),
    }


def _run_pytest_shard(path: Path, expected_ids: list[str]) -> dict[str, Any]:
    recorder = _PytestRecorder()
    rc, result = _pytest_main(path, expected_ids, recorder)
    collected = list(recorder.test_ids)
    exact_collection = sorted(collected) == sorted(expected_ids) and len(collected) == len(set(collected))
    executed_ids = [test_id for test_id in recorder.started if test_id in expected_ids]
    return {
        "ok": rc == 0 and exact_collection and len(executed_ids) == len(expected_ids),
        "runner": "pytest",
        "collected_ids": collected,
        "executed_ids": sorted(executed_ids),
        "started_ids": sorted(recorder.started),
        "outcomes": recorder.outcomes,
        "collected": len(collected),
        "executed": len(executed_ids),
        "failures": sum(value == "failed" for value in recorder.outcomes.values()),
        "errors": sum(value == "error" for value in recorder.outcomes.values()),
        "skipped": sum(value == "skipped" for value in recorder.outcomes.values()),
        "collection_exact": exact_collection,
    }


def _worker_process_groups(root_pid: int, *, timeout: float) -> tuple[set[int], str | None]:
    """Snapshot detached process groups that still descend from this worker."""
    env = dict(os.environ)
    env["PATH"] = os.defpath
    try:
        result = subprocess.run(
            ["ps", "-axo", "pid=,ppid=,pgid="], capture_output=True,
            text=True, timeout=max(0.01, timeout), env=env, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return set(), f"worker process-tree snapshot failed: {type(exc).__name__}: {exc}"
    if result.returncode != 0:
        detail = result.stderr.strip()
        return set(), "worker process-tree snapshot failed" + (f": {detail}" if detail else "")
    rows: dict[int, tuple[int, int]] = {}
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) != 3:
            continue
        try:
            pid, ppid, pgid = map(int, fields)
        except ValueError:
            continue
        rows[pid] = (ppid, pgid)
    if root_pid not in rows:
        return set(), "worker process missing from process-tree snapshot"
    descendants = {root_pid}
    while True:
        added = {pid for pid, (ppid, _) in rows.items() if ppid in descendants} - descendants
        if not added:
            break
        descendants.update(added)
    own_group = rows[root_pid][1]
    groups = {rows[pid][1] for pid in descendants} - {own_group}
    return groups, None


def _live_process_groups(groups: set[int], *, timeout: float) -> tuple[set[int], str | None]:
    if not groups:
        return set(), None
    env = dict(os.environ)
    env["PATH"] = os.defpath
    try:
        result = subprocess.run(
            ["ps", "-axo", "pgid=,state="], capture_output=True,
            text=True, timeout=max(0.01, timeout), env=env, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return set(), f"worker cleanup verification failed: {type(exc).__name__}: {exc}"
    if result.returncode != 0:
        detail = result.stderr.strip()
        return set(), "worker cleanup verification failed" + (f": {detail}" if detail else "")
    live: set[int] = set()
    observed: set[int] = set()
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) != 2:
            continue
        try:
            pgid = int(fields[0])
        except ValueError:
            continue
        if pgid in groups:
            observed.add(pgid)
            if not fields[1].startswith("Z"):
                live.add(pgid)
    # A successful but incomplete `ps` snapshot must not certify an omitted
    # process group as dead. Probe each omission directly; permission denied
    # proves that the group still exists, while other errors are uncertain.
    for pgid in groups - observed:
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            continue
        except PermissionError:
            live.add(pgid)
        except OSError as exc:
            return set(), f"worker cleanup verification failed: {type(exc).__name__}: {exc}"
        else:
            live.add(pgid)
    return live, None


def _cleanup_worker_descendants(grace: float) -> str | None:
    """Stop and verify detached descendants before the worker exits."""
    started = time.monotonic()
    deadline = started + max(0.05, grace)
    verify_reserve = min(0.15, max(0.01, grace / 4))
    snapshot_budget = min(0.5, max(0.1, grace / 4))
    groups, error = _worker_process_groups(
        os.getpid(), timeout=min(snapshot_budget, max(0.01, deadline - time.monotonic() - verify_reserve)),
    )
    if error:
        retry_budget = min(snapshot_budget, max(0.0, deadline - time.monotonic() - verify_reserve))
        if retry_budget > 0:
            groups, error = _worker_process_groups(os.getpid(), timeout=retry_budget)
    if error or not groups:
        return error
    for group in groups:
        try:
            os.killpg(group, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except OSError as exc:
            return f"worker could not terminate descendant group {group}: {type(exc).__name__}: {exc}"
    while time.monotonic() < deadline - verify_reserve:
        remaining = deadline - time.monotonic() - verify_reserve
        live, error = _live_process_groups(groups, timeout=min(0.2, max(0.01, remaining)))
        if error:
            return error
        if not live:
            return None
        time.sleep(min(0.025, max(0.0, remaining)))
    remaining, error = _live_process_groups(
        groups, timeout=min(verify_reserve, max(0.01, deadline - time.monotonic())),
    )
    if error:
        return error
    for group in remaining:
        try:
            os.killpg(group, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except OSError as exc:
            return f"worker could not kill descendant group {group}: {type(exc).__name__}: {exc}"
    remaining_time = max(0.01, deadline - time.monotonic())
    live, error = _live_process_groups(remaining, timeout=remaining_time)
    if error:
        return error
    if live:
        return f"detached descendant groups remain live after cleanup: {sorted(live)}"
    return None


def _worker_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--_worker", choices=("collect", "run"), required=True)
    parser.add_argument("--_repo-root", required=True)
    parser.add_argument("--_source", required=True)
    parser.add_argument("--_policy", choices=("unittest", "pytest"), required=True)
    parser.add_argument("--_shard", default="")
    parser.add_argument("--_test-ids", default="[]")
    parser.add_argument("--_cleanup-grace", type=float, default=DEFAULT_CLEANUP_GRACE)
    args = parser.parse_args(argv)
    path = Path(args._source)
    result: dict[str, Any] | None = None
    worker_error: str | None = None
    try:
        if args._worker == "collect":
            result = _unittest_collection(path) if args._policy == "unittest" else _pytest_collection(path)
        elif args._policy == "unittest":
            expected_ids = json.loads(args._test_ids)
            result = _run_unittest_shard(path, args._shard, expected_ids or None)
        else:
            result = _run_pytest_shard(path, json.loads(args._test_ids))
    except BaseException as exc:
        worker_error = f"{type(exc).__name__}: {exc}"
    try:
        cleanup_error = _cleanup_worker_descendants(args._cleanup_grace)
    except BaseException as exc:
        cleanup_error = f"worker descendant cleanup raised {type(exc).__name__}: {exc}"
    if worker_error is not None:
        failure: dict[str, Any] = {"ok": False, "error": worker_error}
        if cleanup_error:
            failure["cleanup_error"] = cleanup_error
        print(MARKER + json.dumps(failure, sort_keys=True, separators=(",", ":")))
        return 1
    if result is None:
        result = {"ok": False, "error": "worker produced no result"}
    if cleanup_error:
        result["ok"] = False
        result["cleanup_error"] = cleanup_error
    print(MARKER + json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("ok", False) else 1


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _scheduling_class(path: Path) -> tuple[str, dict[str, list[str]]]:
    """Conservatively identify read-only or per-test temporary work.

    Any file/environment/child effect without a discoverable isolated fixture
    remains exclusive. The process-group owner provides a known child effect.
    """
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    lower = text.lower()
    has_external_effect = any(token in lower for token in (
        "subprocess", "os.environ", "path.write", ".write_text(", ".write_bytes(",
        ".mkdir(", ".unlink(", "open(", "tempfile", "socket", "git ", "popen(",
        "lock", "worktree",
    ))
    import re
    has_isolation = bool(re.search(r"\btmp_path\b", lower)) or any(
        token in lower for token in ("temporarydirectory", "mkdtemp(", "self.tmp")
    )
    writes_home = bool(re.search(
        r"(?:path\.home\(\)|expanduser\(\))[^\n;]{0,120}\.(?:write_text|write_bytes|mkdir|touch|unlink|open)\(",
        lower,
    ))
    writes_outside_fixture = (
        _writes_from_temporary_fixture_parent(lower)
        or _writes_to_fixed_absolute_path(lower)
        or _writes_to_environment_path(lower)
    )
    if not has_external_effect:
        label = "read-only"
        mutable, locks, environment = ["none detected"], ["none detected"], ["process-local"]
    elif has_isolation and not writes_home and not writes_outside_fixture:
        label = "isolated-fixture"
        mutable, locks, environment = ["test temporary roots"], ["fixture-scoped; no shared lock path detected"], ["process-local"]
    else:
        label = "unknown-serial"
        mutable, locks, environment = ["unknown or shared path"], ["unknown or shared lock"], ["unknown process effects"]
        if _policy(path) == "pytest" and _pytest_fixture_shards_are_safe(path):
            label = "isolated-fixture"
            mutable = ["function-scoped test temporary roots"]
            locks = ["fixture-scoped; no shared lock path detected"]
            environment = ["function-scoped fixture values"]
    effects = ["child process groups are captured, terminated and reaped by the runner"]
    return label, {"mutable_paths": mutable, "locks": locks, "environment": environment, "child_effects": effects}


def _safe_first_schedule(
    paths: list[Path],
    classifications: dict[Path, tuple[str, dict[str, list[str]]]] | None = None,
) -> list[Path]:
    """Queue proven readers before unknown suites, keeping both groups stable.

    The admission gate gives an already-waiting serial suite priority. Queueing
    unknown suites first therefore prevents later safe readers from starting.
    Moving the proven-safe batch ahead of that serial queue avoids the convoy
    without changing any suite's safety classification or overlap rules.
    """
    return sorted(
        paths,
        key=lambda path: (
            classifications[path][0] if classifications is not None
            else _scheduling_class(path)[0]
        ) == "unknown-serial",
    )


def _source_shards(collection: dict[str, Any], policy: str,
                   workers: int = MAX_WORKERS) -> list[dict[str, Any]]:
    groups = list(collection.get("groups", []))
    if policy == "unittest":
        shards: list[dict[str, Any]] = []
        safe_groups: list[dict[str, Any]] = []
        independent_ids: list[str] = []
        for group in groups:
            if group.get("method_shardable"):
                safe_groups.append(group)
                independent_ids.extend(group["test_ids"])
            else:
                shards.append(group)
        if len(independent_ids) <= workers:
            return shards + safe_groups
        batch_count = min(
            max(1, workers * SAFE_METHOD_BATCHES_PER_WORKER),
            len(independent_ids),
        )
        batches = [[] for _ in range(batch_count)]
        for index, test_id in enumerate(independent_ids):
            batches[index % batch_count].append(test_id)
        for index, ids in enumerate(batches, start=1):
            shards.append({
                "shard_id": f"unittest-method-batch-{index}",
                "test_ids": ids,
                "method_shardable": True,
            })
        return shards
    # Preserve unittest class fixtures in mixed files; batch only top-level
    # pytest node IDs, while retaining one-to-one node accounting in reports.
    class_groups: dict[str, list[str]] = defaultdict(list)
    function_ids: list[str] = []
    for item in groups:
        nodeid = item["shard_id"]
        if "::" in nodeid:
            parts = nodeid.split("::")
            if len(parts) >= 3:
                class_groups["::".join(parts[:2])].append(nodeid)
            else:
                function_ids.append(nodeid)
        else:
            function_ids.append(nodeid)
    shards = [{"shard_id": key, "test_ids": ids} for key, ids in class_groups.items()]
    for offset in range(0, len(function_ids), PYTEST_BATCH_SIZE):
        ids = function_ids[offset:offset + PYTEST_BATCH_SIZE]
        shards.append({"shard_id": f"pytest-node-group-{offset // PYTEST_BATCH_SIZE + 1}", "test_ids": ids})
    return shards


class _SchedulingGate:
    def __init__(self):
        self.condition = asyncio.Condition()
        self.active_read = 0
        self.active_serial = False
        self.waiting_serial = 0

    async def acquire(self, serial: bool, cancelled: asyncio.Event) -> bool:
        async with self.condition:
            if serial:
                self.waiting_serial += 1
            try:
                while not cancelled.is_set():
                    allowed = (not self.active_serial and self.active_read == 0) if serial else (
                        not self.active_serial and self.waiting_serial == 0
                    )
                    if allowed:
                        if serial:
                            self.active_serial = True
                        else:
                            self.active_read += 1
                        return True
                    await self.condition.wait()
                return False
            finally:
                if serial:
                    self.waiting_serial -= 1

    async def release(self, serial: bool):
        async with self.condition:
            if serial:
                self.active_serial = False
            else:
                self.active_read -= 1
            self.condition.notify_all()

    async def wake(self):
        async with self.condition:
            self.condition.notify_all()


@dataclass
class _ProcessResult:
    outcome: str
    returncode: int | None
    stdout: str
    stderr: str
    started_at: float
    ended_at: float
    worker: dict[str, Any] | None


class RequiredTestSuiteRunner:
    """Inventory discovery, suite/shard scheduling, deadlines and accounting."""

    def __init__(self, repo_root: str | Path, *, workers: int = 1,
                 per_script_timeout: float = DEFAULT_PER_SCRIPT_TIMEOUT,
                 suite_timeout: float = DEFAULT_SUITE_TIMEOUT,
                 cleanup_grace: float = DEFAULT_CLEANUP_GRACE,
                 focused_suites: list[str] | None = None,
                 focused_test_ids: dict[str, list[str]] | None = None,
                 capture_process_context: bool = False,
                 json_report: str | Path | None = None):
        self.root = Path(repo_root).resolve()
        self.workers = workers
        self.per_script_timeout = per_script_timeout
        self.suite_timeout = suite_timeout
        self.cleanup_grace = cleanup_grace
        self.focused_test_ids = dict(focused_test_ids or {})
        self.focused_suites = list(focused_suites or list(self.focused_test_ids))
        self.capture_process_context = capture_process_context
        self.json_report = Path(json_report) if json_report else None
        self.cancelled = asyncio.Event()
        self.cancel_reason: str | None = None
        self.processes: dict[int, asyncio.subprocess.Process] = {}
        self.max_active_children = 0
        self.process_context_samples: list[dict[str, Any]] = []
        self.unassigned_controllers: dict[int, dict[str, Any]] = {}
        self.peak_owned_rss_kib = 0
        self.gate = _SchedulingGate()
        self.semaphore = asyncio.Semaphore(workers)
        self.suite_semaphore = asyncio.Semaphore(workers)
        self.start_monotonic = 0.0
        self.global_deadline = 0.0
        self.report_reserve = min(2.0, max(0.1, suite_timeout * 0.05))
        self.python_executable, self.venv_bin = self._configured_python()
        self.base_report: dict[str, Any] = {}

    @staticmethod
    def _configured_python() -> tuple[str, str]:
        active_venv = sys.prefix != sys.base_prefix
        inherited = os.environ.get("AI_PLAYBOOK_TEST_VENV", "")
        if active_venv:
            bin_dir = Path(sys.executable).parent
            executable = sys.executable
        else:
            bin_dir = Path(inherited) if inherited else Path()
            candidates = [bin_dir / "python3", bin_dir / "python"]
            executable_path = next((candidate for candidate in candidates if candidate.is_file()), None)
            if executable_path is None:
                raise RuntimeError("run the required-suite runner with the configured test virtual environment active")
            executable = str(executable_path)
        if not Path(executable).is_file():
            raise RuntimeError(f"configured test interpreter is missing: {executable}")
        return str(executable), str(bin_dir)

    def _child_env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["AI_PLAYBOOK_TEST_VENV"] = self.venv_bin
        env["PATH"] = self.venv_bin + (os.pathsep + env.get("PATH", "") if env.get("PATH") else "")
        env["PYTHONPATH"] = os.pathsep.join((str(self.root / "scripts"), str(self.root)))
        env.pop("PYTHONHOME", None)
        env["PYTHONNOUSERSITE"] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTEST_ADDOPTS"] = ""
        env.pop("PYTEST_PLUGINS", None)
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        return env

    def _inventory(self) -> tuple[list[Path], str, dict[str, str]]:
        paths = _inventory(self.root)
        digest, file_digests = _inventory_digest(paths, self.root)
        return paths, digest, file_digests

    def _selected(self, paths: list[Path]) -> list[Path]:
        if not self.focused_suites:
            return paths
        by_name = {_relative(self.root, path): path for path in paths}
        by_basename = {path.name: path for path in paths}
        selected: list[Path] = []
        seen: set[Path] = set()
        for selector in self.focused_suites:
            candidate = Path(selector)
            if candidate.is_absolute():
                resolved = candidate.resolve()
                match = next((path for path in paths if path.resolve() == resolved), None)
            else:
                normalized = selector.removeprefix("./")
                match = by_name.get(normalized) or by_basename.get(Path(normalized).name)
            if match is None:
                raise ValueError(f"focused suite is not in the live inventory: {selector}")
            if match in seen:
                raise ValueError(f"focused suite selected more than once: {selector}")
            selected.append(match)
            seen.add(match)
        return sorted(selected)

    def _git_revision(self) -> str | None:
        try:
            result = subprocess.run(
                ["git", "-C", str(self.root), "rev-parse", "--verify", "HEAD"],
                capture_output=True, text=True, timeout=1, env=self._child_env(), check=False,
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except (OSError, subprocess.TimeoutExpired):
            return None

    async def _signal_group(self, process: asyncio.subprocess.Process, signum: int) -> None:
        if process.returncode is not None:
            # The direct child may have exited while a descendant still owns
            # captured pipes; signal the original process group to reap it.
            pass
        try:
            os.killpg(process.pid, signum)
        except (ProcessLookupError, PermissionError, OSError):
            pass

    async def _descendant_groups(self, root_pid: int, *, timeout: float,
                                 search_path: str | None = None) -> tuple[set[int], str | None]:
        """Snapshot process groups owned by a worker before terminating it.

        A timed-out test may start a new session, escaping the worker's process
        group. Snapshotting the live parent tree before TERM lets timeout and
        cancellation cleanup terminate those groups too. This runs only on
        abnormal cleanup paths so normal shard completion pays no extra cost.
        """
        groups = {root_pid}
        try:
            snapshot_env = None
            if search_path is not None:
                snapshot_env = dict(os.environ)
                snapshot_env["PATH"] = search_path
            ps = await asyncio.create_subprocess_exec(
                "ps", "-axo", "pid=,ppid=,pgid=",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                env=snapshot_env,
            )
            try:
                stdout, stderr = await asyncio.wait_for(ps.communicate(), timeout=max(0.025, timeout))
            except asyncio.TimeoutError:
                ps.kill()
                await ps.wait()
                return groups, "process-tree snapshot timed out; detached descendants may remain"
            if ps.returncode != 0:
                detail = stderr.decode(errors="replace").strip()
                return groups, "process-tree snapshot failed" + (f": {detail}" if detail else "")
            rows: dict[int, tuple[int, int]] = {}
            for line in stdout.decode(errors="replace").splitlines():
                fields = line.split()
                if len(fields) != 3:
                    continue
                try:
                    pid, ppid, pgid = map(int, fields)
                except ValueError:
                    continue
                rows[pid] = (ppid, pgid)
            if root_pid not in rows:
                return groups, "worker missing from process-tree snapshot; detached descendants may remain"
            descendants = {root_pid}
            while True:
                added = {pid for pid, (ppid, _pgid) in rows.items() if ppid in descendants} - descendants
                if not added:
                    break
                descendants.update(added)
            groups.update(rows[pid][1] for pid in descendants)
            return groups, None
        except (OSError, asyncio.SubprocessError) as exc:
            return groups, f"process-tree snapshot failed: {type(exc).__name__}: {exc}"

    @staticmethod
    def _process_group_exists(pgid: int) -> bool:
        try:
            os.killpg(pgid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False

    async def _cleanup_process(self, process: asyncio.subprocess.Process,
                               communicate: asyncio.Task, *, grace: float,
                               capture_descendants: bool = False) -> tuple[str, str]:
        cleanup_deadline = time.monotonic() + max(0.01, grace)
        groups = {process.pid}
        cleanup_note = ""
        if capture_descendants:
            snapshot_budget = min(1.0, max(0.5, grace))
            snapshot_deadline = time.monotonic() + snapshot_budget
            fallback_reserve = min(0.15, snapshot_budget / 4)
            retry_budget = (snapshot_budget - fallback_reserve) / 2
            snapshot_error = None
            for attempt in range(2):
                remaining = snapshot_deadline - time.monotonic()
                if remaining <= fallback_reserve:
                    break
                groups, snapshot_error = await self._descendant_groups(
                    process.pid,
                    timeout=min(retry_budget, remaining - fallback_reserve),
                )
                if snapshot_error is None:
                    break
                if attempt == 0:
                    await asyncio.sleep(min(
                        0.025,
                        max(0.0, snapshot_deadline - time.monotonic() - fallback_reserve),
                    ))
            if snapshot_error and snapshot_deadline > time.monotonic():
                # Retry through the system path so a broken, shadowed, or
                # transient PATH-selected `ps` cannot make cleanup forget
                # descendants that detached into their own process groups.
                remaining = snapshot_deadline - time.monotonic()
                groups, snapshot_error = await self._descendant_groups(
                    process.pid, timeout=remaining, search_path=os.defpath,
                )
            if snapshot_error:
                cleanup_note = snapshot_error
        for group in groups:
            try:
                os.killpg(group, signal.SIGTERM)
            except (ProcessLookupError, PermissionError, OSError):
                pass
        # Pipe EOF is not a process-tree witness: test frameworks may redirect
        # a descendant's stdout, allowing communicate() to finish while that
        # descendant is still alive. Poll every captured descendant group.
        while any(self._process_group_exists(group) for group in groups) and time.monotonic() < cleanup_deadline:
            await asyncio.sleep(min(0.025, max(0.0, cleanup_deadline - time.monotonic())))
        for group in groups:
            if self._process_group_exists(group):
                try:
                    os.killpg(group, signal.SIGKILL)
                except (ProcessLookupError, PermissionError, OSError):
                    pass
        try:
            stdout, stderr = await asyncio.wait_for(
                asyncio.shield(communicate), timeout=max(0.2, grace),
            )
        except asyncio.TimeoutError:
            # The process group has already received KILL; make one bounded
            # final capture attempt, then let the caller record a capture error.
            await self._signal_group(process, signal.SIGKILL)
            try:
                stdout, stderr = await asyncio.wait_for(
                    asyncio.shield(communicate), timeout=max(0.2, grace),
                )
            except asyncio.TimeoutError:
                communicate.cancel()
                stdout, stderr = b"", b"runner could not capture output after process-tree kill"
        stderr_text = stderr.decode(errors="replace")
        if cleanup_note:
            stderr_text = (stderr_text + "\n" + cleanup_note).strip()
        return stdout.decode(errors="replace"), stderr_text

    async def _run_process(self, args: list[str], *, deadline: float) -> _ProcessResult:
        started = time.monotonic()
        if self.cancelled.is_set():
            return _ProcessResult(self.cancel_reason or "cancelled", None, "", "", started, time.monotonic(), None)
        if deadline - started <= 0:
            return _ProcessResult("timeout", None, "", "deadline expired before launch", started, time.monotonic(), None)
        async with self.semaphore:
            if self.cancelled.is_set():
                return _ProcessResult(self.cancel_reason or "cancelled", None, "", "", started, time.monotonic(), None)
            started = time.monotonic()
            if deadline - started <= 0:
                return _ProcessResult(
                    "timeout", None, "", "deadline expired while waiting for a worker slot",
                    started, time.monotonic(), None,
                )
            try:
                process = await asyncio.create_subprocess_exec(
                    self.python_executable, *args,
                    cwd=self.root,
                    env=self._child_env(),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    start_new_session=True,
                )
            except Exception as exc:
                return _ProcessResult("error", None, "", f"launch error: {type(exc).__name__}: {exc}", started, time.monotonic(), None)
            self.processes[process.pid] = process
            self.max_active_children = max(self.max_active_children, len(self.processes))
            communicate = asyncio.create_task(process.communicate())
            signal_wait = asyncio.create_task(self.cancelled.wait())
            usable = max(0.0, deadline - time.monotonic() - self.cleanup_grace)
            try:
                done, _ = await asyncio.wait(
                    (communicate, signal_wait), timeout=usable,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if communicate in done:
                    stdout_bytes, stderr_bytes = communicate.result()
                    # Closing the test child is also the point at which any
                    # leaked descendants are terminated and captured.
                    out, err = await self._cleanup_process(process, communicate, grace=self.cleanup_grace)
                    return _ProcessResult(
                        "completed", process.returncode,
                        out or stdout_bytes.decode(errors="replace"),
                        err or stderr_bytes.decode(errors="replace"), started, time.monotonic(), None,
                    )
                signalled = signal_wait in done and signal_wait.result()
                reason = (
                    "cancelled" if self.cancel_reason == "signal" else self.cancel_reason
                ) if signalled or self.cancelled.is_set() else "timeout"
                if reason == "signal":
                    reason = "cancelled"
                out, err = await self._cleanup_process(
                    process, communicate, grace=self.cleanup_grace, capture_descendants=True,
                )
                return _ProcessResult(reason, process.returncode, out, err, started, time.monotonic(), None)
            except asyncio.CancelledError:
                await self._cleanup_process(
                    process, communicate, grace=self.cleanup_grace, capture_descendants=True,
                )
                raise
            finally:
                signal_wait.cancel()
                self.processes.pop(process.pid, None)

    @staticmethod
    def _parse_marker(stdout: str) -> dict[str, Any] | None:
        for line in reversed(stdout.splitlines()):
            if line.startswith(MARKER):
                try:
                    return json.loads(line[len(MARKER):])
                except json.JSONDecodeError:
                    return None
        return None

    async def _worker(self, mode: str, path: Path, policy: str, deadline: float,
                      shard_id: str = "", test_ids: list[str] | None = None) -> _ProcessResult:
        args = [
            str(Path(__file__).resolve()), "--_worker", mode,
            "--_repo-root", str(self.root), "--_source", str(path), "--_policy", policy,
            "--_cleanup-grace", str(self.cleanup_grace),
        ]
        if shard_id:
            args.extend(("--_shard", shard_id))
        if test_ids is not None:
            args.extend(("--_test-ids", json.dumps(test_ids, separators=(",", ":"))))
        return await self._run_process(args, deadline=deadline)

    def _shard_record(self, path: Path, shard: dict[str, Any], classification: str,
                      evidence: dict[str, list[str]], queued_at: float,
                      process: _ProcessResult, worker: dict[str, Any] | None) -> dict[str, Any]:
        test_ids = list(shard.get("test_ids", []))
        expected = set(test_ids)
        actual_collected = set((worker or {}).get("collected_ids", []))
        actual_executed = set((worker or {}).get("executed_ids", []))
        exact = actual_collected == expected and len(actual_collected) == len(test_ids)
        executed_exact = actual_executed == expected and len(actual_executed) == len(test_ids)
        raw_collected = (worker or {}).get("collected")
        raw_executed = (worker or {}).get("executed")
        collected_count_valid = isinstance(raw_collected, int) and not isinstance(raw_collected, bool)
        executed_count_valid = isinstance(raw_executed, int) and not isinstance(raw_executed, bool)
        counts_exact = (
            collected_count_valid and executed_count_valid
            and raw_collected == len(test_ids) and raw_executed == len(test_ids)
        )
        outcome = process.outcome
        if outcome == "completed":
            if not worker or not worker.get("ok") or not exact or not executed_exact or not counts_exact:
                outcome = "accounting_error"
            elif worker.get("failures") or worker.get("errors"):
                outcome = "failed"
            elif worker.get("skipped") == worker.get("collected"):
                outcome = "skipped"
            else:
                outcome = "passed"
        started_at = process.started_at
        ended_at = process.ended_at
        return {
            "shard_id": shard["shard_id"],
            "source_suite": _relative(self.root, path),
            "scheduling_class": classification,
            "scheduling_evidence": evidence,
            "source_sha256": _sha256(path) if path.exists() else None,
            "test_ids": test_ids,
            "collected_ids": sorted(actual_collected),
            "executed_ids": sorted(actual_executed),
            "queued_at": queued_at,
            "started_at": started_at,
            "ended_at": ended_at,
            "duration": max(0.0, ended_at - started_at),
            "queue_wait": max(0.0, started_at - queued_at),
            "collected": raw_collected if collected_count_valid else 0,
            "executed": raw_executed if executed_count_valid else 0,
            "failures": int((worker or {}).get("failures", 0)),
            "errors": int((worker or {}).get("errors", 0)),
            "skipped": int((worker or {}).get("skipped", 0)),
            "outcome": outcome,
            "returncode": process.returncode,
            "collection_exact": exact,
            "execution_exact": executed_exact,
            "counts_exact": counts_exact,
            "stdout_sha256": hashlib.sha256(process.stdout.encode("utf-8", errors="replace")).hexdigest(),
            "stderr_sha256": hashlib.sha256(process.stderr.encode("utf-8", errors="replace")).hexdigest(),
            "output_tail": process.stderr[-2000:] or process.stdout[-2000:],
        }

    async def _run_shard(self, path: Path, policy: str, shard: dict[str, Any],
                         classification: str, evidence: dict[str, list[str]],
                         source_deadline: float, queued_at: float) -> dict[str, Any]:
        if self.cancelled.is_set():
            now = time.monotonic()
            return {
                "shard_id": shard["shard_id"], "source_suite": _relative(self.root, path),
                "scheduling_class": classification, "scheduling_evidence": evidence,
                "source_sha256": _sha256(path) if path.exists() else None,
                "test_ids": list(shard.get("test_ids", [])), "queued_at": queued_at,
                "started_at": None, "ended_at": now, "duration": 0.0,
                "queue_wait": max(0.0, now - queued_at), "collected": 0, "executed": 0,
                "failures": 0, "errors": 0, "skipped": 0, "outcome": "cancelled",
                "returncode": None, "collection_exact": False, "execution_exact": False,
                "stdout_sha256": hashlib.sha256(b"").hexdigest(), "stderr_sha256": hashlib.sha256(b"").hexdigest(),
                "output_tail": "",
            }
        ids = shard["test_ids"]
        try:
            if policy == "unittest":
                process = await self._worker(
                    "run", path, policy, source_deadline,
                    shard_id=shard["shard_id"], test_ids=ids,
                )
            else:
                process = await self._worker("run", path, policy, source_deadline, test_ids=ids)
            worker = self._parse_marker(process.stdout)
            return self._shard_record(path, shard, classification, evidence, queued_at, process, worker)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            return self._exception_shard_record(
                path, shard, classification, evidence, queued_at, exc,
            )

    def _exception_shard_record(self, path: Path, shard: dict[str, Any],
                                classification: str, evidence: dict[str, list[str]],
                                queued_at: float, exc: Exception) -> dict[str, Any]:
        ended_at = time.monotonic()
        message = f"shard execution error: {type(exc).__name__}: {exc}"
        process = _ProcessResult("error", None, "", message, ended_at, ended_at, None)
        record = self._shard_record(path, shard, classification, evidence, queued_at, process, None)
        record["errors"] = 1
        record["error"] = message
        return record

    async def _run_shard_queue(self, path: Path, policy: str,
                               shards: list[dict[str, Any]],
                               classification: str, evidence: dict[str, list[str]],
                               source_deadline: float, worker_count: int) -> list[dict[str, Any]]:
        """Run a bounded consumer pool over shards, pulling the next only when ready."""
        if not shards:
            return []
        results: list[dict[str, Any] | None] = [None] * len(shards)
        next_index = 0
        queued_at = time.monotonic()

        async def consume() -> None:
            nonlocal next_index
            while next_index < len(shards):
                index = next_index
                next_index += 1
                try:
                    results[index] = await self._run_shard(
                        path, policy, shards[index], classification, evidence,
                        source_deadline, queued_at,
                    )
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    results[index] = self._exception_shard_record(
                        path, shards[index], classification, evidence, queued_at, exc,
                    )

        concurrency = min(len(shards), max(1, worker_count))
        consumers = [asyncio.create_task(consume()) for _ in range(concurrency)]
        try:
            await asyncio.gather(*consumers)
        except BaseException:
            for consumer in consumers:
                if not consumer.done():
                    consumer.cancel()
            await asyncio.gather(*consumers, return_exceptions=True)
            raise
        if any(result is None for result in results):
            raise RuntimeError("bounded shard queue left an unaccounted shard")
        return [result for result in results if result is not None]

    async def _run_suite(self, path: Path, queued_at: float,
                         metadata: tuple[str, dict[str, list[str]]] | None = None) -> dict[str, Any]:
        relative = _relative(self.root, path)
        classification, evidence = metadata or _scheduling_class(path)
        serial = classification == "unknown-serial"
        # Waiting for an available source slot is global queue time. Start the
        # per-script deadline only after the scheduler admits this source.
        await self.suite_semaphore.acquire()
        if not await self.gate.acquire(serial, self.cancelled):
            self.suite_semaphore.release()
            return self._cancelled_suite(path, queued_at, classification, evidence)
        started_at = time.monotonic()
        source_deadline = min(started_at + self.per_script_timeout, self.global_deadline - self.report_reserve)
        suite: dict[str, Any] = {
            "source_suite": relative, "scheduling_class": classification,
            "scheduling_evidence": evidence, "source_sha256": _sha256(path),
            "queued_at": queued_at, "started_at": started_at, "queue_wait": max(0.0, started_at - queued_at),
            "shards": [], "collected": 0, "executed": 0, "failures": 0, "errors": 0,
            "skipped": 0, "outcome": "error", "report_complete": False,
            "worker_environment": {
                "python_executable": self.python_executable,
                "AI_PLAYBOOK_TEST_VENV": self.venv_bin,
                "PATH_first": self.venv_bin,
                "PYTHONPATH": os.pathsep.join((str(self.root / "scripts"), str(self.root))),
                "PYTHONHOME": "cleared",
                "PYTEST_ADDOPTS": "pinned-empty", "PYTEST_PLUGINS": "cleared",
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            },
        }
        try:
            if self.cancelled.is_set():
                suite["outcome"] = self.cancel_reason or "cancelled"
                return suite
            policy = _policy(path)
            collection_process = await self._worker("collect", path, policy, source_deadline)
            collection = self._parse_marker(collection_process.stdout)
            if collection_process.outcome != "completed" or not collection or not collection.get("ok"):
                suite["outcome"] = (
                    "cancelled" if collection_process.outcome == "signal" else
                    collection_process.outcome if collection_process.outcome != "completed" else "collection_error"
                )
                suite["collection_error"] = (collection or {}).get("error") or collection_process.stderr[-2000:]
                return suite
            test_ids = list(collection.get("test_ids", []))
            suite["runner"] = policy
            suite["discovered_count"] = len(test_ids)
            requested_ids = self.focused_test_ids.get(relative)
            if requested_ids:
                if len(requested_ids) != len(set(requested_ids)):
                    suite["outcome"] = "duplicate_selector"
                    return suite
                missing = sorted(set(requested_ids) - set(test_ids))
                if missing:
                    suite["outcome"] = "selector_missing"
                    suite["selector_missing_ids"] = missing
                    return suite
                if policy == "unittest":
                    selected_groups = []
                    for group in collection.get("groups", []):
                        selected_in_group = set(group["test_ids"]) & set(requested_ids)
                        if not selected_in_group:
                            continue
                        if selected_in_group != set(group["test_ids"]):
                            if not group.get("method_shardable", False):
                                suite["outcome"] = "partial_class_selector"
                                suite["selector_error"] = group["shard_id"]
                                return suite
                            selected_groups.extend(
                                {"shard_id": test_id, "test_ids": [test_id]}
                                for test_id in group["test_ids"] if test_id in selected_in_group
                            )
                        else:
                            selected_groups.append(group)
                    collection["groups"] = selected_groups
                selected = set(requested_ids)
                test_ids = [test_id for test_id in test_ids if test_id in selected]
                collection["test_ids"] = test_ids
                if policy != "unittest":
                    collection["groups"] = [
                        {"shard_id": group["shard_id"],
                         "test_ids": [test_id for test_id in group["test_ids"] if test_id in selected]}
                        for group in collection.get("groups", [])
                        if set(group["test_ids"]) & selected
                    ]
                suite["partial_test_selection"] = True
            suite["collected_ids"] = test_ids
            if not test_ids:
                suite["outcome"] = "zero_collection"
                return suite
            shard_workers = self.workers
            groups = collection.get("groups", [])
            has_safe_groups = any(group.get("method_shardable") for group in groups)
            has_serial_groups = any(not group.get("method_shardable") for group in groups)
            has_multi_id_serial_groups = any(
                not group.get("method_shardable") and len(group.get("test_ids", [])) > 1
                for group in groups
            )
            if classification == "unknown-serial" and has_safe_groups and has_multi_id_serial_groups:
                # Reserve one process slot for whole-class serial work while
                # isolated methods are sharded, avoiding an internal queue tail
                # behind a potentially long multi-test class. Singleton whole
                # classes remain intact and may use the spare time while those
                # batches run.
                shard_workers = max(1, self.workers - 1)
            shards = _source_shards(collection, policy, shard_workers)
            suite["shard_ids"] = [shard["shard_id"] for shard in shards]
            if len(test_ids) != len(set(test_ids)):
                suite["outcome"] = "duplicate_collection"
                return suite
            if len(shards) > 1 and classification != "unknown-serial":
                shard_results = await self._run_shard_queue(
                    path, policy, shards, classification, evidence,
                    source_deadline, self.workers,
                )
            elif len(shards) > 1 and policy == "unittest":
                safe_shards = [shard for shard in shards if shard.get("method_shardable", False)]
                serial_shards = [shard for shard in shards if not shard.get("method_shardable", False)]
                safe_task = asyncio.create_task(self._run_shard_queue(
                    path, policy, safe_shards, classification, evidence,
                    source_deadline, shard_workers,
                )) if safe_shards else None
                results_by_id: dict[str, dict[str, Any]] = {}
                # Keep each unsafe class intact and serialize unsafe classes
                # with each other. Proven fixture-isolated shards can occupy
                # other worker slots while those whole-class shards run.
                try:
                    for shard in serial_shards:
                        if self.cancelled.is_set():
                            break
                        results_by_id[shard["shard_id"]] = await self._run_shard(
                            path, policy, shard, classification, evidence,
                            source_deadline, time.monotonic(),
                        )
                    safe_results = await safe_task if safe_task is not None else []
                finally:
                    if safe_task is not None and not safe_task.done():
                        safe_task.cancel()
                    if safe_task is not None:
                        await asyncio.gather(safe_task, return_exceptions=True)
                results_by_id.update({result["shard_id"]: result for result in safe_results})
                for shard in serial_shards:
                    if shard["shard_id"] not in results_by_id:
                        results_by_id[shard["shard_id"]] = self._cancelled_shard(
                            path, shard, classification, evidence,
                        )
                shard_results = [results_by_id[shard["shard_id"]] for shard in shards]
            else:
                shard_results = []
                for shard in shards:
                    if self.cancelled.is_set():
                        break
                    shard_results.append(await self._run_shard(
                        path, policy, shard, classification, evidence,
                        source_deadline, time.monotonic(),
                    ))
                for shard in shards[len(shard_results):]:
                    shard_results.append(self._cancelled_shard(path, shard, classification, evidence))
            suite["shards"] = shard_results
            suite["collected"] = sum(shard["collected"] for shard in shard_results)
            suite["executed"] = sum(shard["executed"] for shard in shard_results)
            suite["failures"] = sum(shard["failures"] for shard in shard_results)
            suite["errors"] = sum(shard["errors"] for shard in shard_results)
            suite["skipped"] = sum(shard["skipped"] for shard in shard_results)
            collected_all = [test_id for shard in shard_results for test_id in shard["test_ids"]]
            executed_all = [test_id for shard in shard_results for test_id in shard.get("executed_ids", [])]
            suite["executed_ids"] = executed_all
            accounting_ok = (
                sorted(collected_all) == sorted(test_ids)
                and len(collected_all) == len(set(collected_all))
                and suite["executed"] == len(test_ids)
                and all(
                    shard["collection_exact"] and shard["execution_exact"] and shard["counts_exact"]
                    for shard in shard_results
                )
            )
            if path.exists() and _sha256(path) != suite["source_sha256"]:
                suite["outcome"] = "inventory_drift"
            elif self.cancelled.is_set() or any(shard["outcome"] in {"cancelled", "timeout"} for shard in shard_results):
                suite["outcome"] = (
                    "cancelled" if self.cancel_reason == "signal" or
                    any(shard["outcome"] == "cancelled" for shard in shard_results)
                    else "timeout"
                )
            elif time.monotonic() > source_deadline:
                suite["outcome"] = "timeout"
            elif not accounting_ok:
                suite["outcome"] = "accounting_error"
            elif suite["failures"] or suite["errors"] or any(shard["outcome"] not in {"passed", "skipped"} for shard in shard_results):
                suite["outcome"] = "failed"
            else:
                suite["outcome"] = "passed"
            suite["accounting_exact"] = accounting_ok
            return suite
        except Exception as exc:
            suite["outcome"] = "error"
            suite["error"] = f"{type(exc).__name__}: {exc}"
            return suite
        finally:
            suite["ended_at"] = time.monotonic()
            suite["duration"] = max(0.0, suite["ended_at"] - started_at)
            suite["report_complete"] = True
            await self.gate.release(serial)
            self.suite_semaphore.release()

    def _cancelled_shard(self, path: Path, shard: dict[str, Any], classification: str,
                         evidence: dict[str, list[str]]) -> dict[str, Any]:
        now = time.monotonic()
        return {
            "shard_id": shard["shard_id"], "source_suite": _relative(self.root, path),
            "scheduling_class": classification, "scheduling_evidence": evidence,
            "source_sha256": _sha256(path) if path.exists() else None,
            "test_ids": list(shard.get("test_ids", [])), "queued_at": now,
            "started_at": None, "ended_at": now, "duration": 0.0,
            "queue_wait": 0.0, "collected": 0, "executed": 0, "failures": 0,
            "errors": 0, "skipped": 0, "outcome": "cancelled", "returncode": None,
            "collection_exact": False, "execution_exact": False,
            "stdout_sha256": hashlib.sha256(b"").hexdigest(),
            "stderr_sha256": hashlib.sha256(b"").hexdigest(), "output_tail": "",
        }

    def _cancelled_suite(self, path: Path, queued_at: float, classification: str,
                         evidence: dict[str, list[str]]) -> dict[str, Any]:
        now = time.monotonic()
        return {
            "source_suite": _relative(self.root, path), "scheduling_class": classification,
            "scheduling_evidence": evidence, "source_sha256": _sha256(path),
            "queued_at": queued_at, "started_at": None, "ended_at": now,
            "queue_wait": max(0.0, now - queued_at), "duration": 0.0, "shards": [],
            "collected": 0, "executed": 0, "failures": 0, "errors": 0, "skipped": 0,
            "outcome": "cancelled", "report_complete": True,
        }

    @staticmethod
    def _elapsed_seconds(value: str) -> int:
        days = 0
        if "-" in value:
            day_part, value = value.split("-", 1)
            try:
                days = int(day_part)
            except ValueError:
                return 0
        try:
            parts = [int(part) for part in value.split(":")]
        except ValueError:
            return 0
        if len(parts) == 3:
            hours, minutes, seconds = parts
        elif len(parts) == 2:
            hours, minutes, seconds = 0, parts[0], parts[1]
        else:
            hours, minutes, seconds = 0, 0, parts[0]
        return days * 86400 + hours * 3600 + minutes * 60 + seconds

    def _process_snapshot(self) -> dict[str, Any]:
        ps = "/bin/ps" if Path("/bin/ps").is_file() else "ps"
        try:
            result = subprocess.run(
                [ps, "-axo", "pid=,ppid=,pgid=,etime=,rss=,command="],
                capture_output=True, text=True, timeout=0.5, check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return {"at": time.monotonic(), "snapshot_error": True,
                    "owned_processes": [], "unassigned_test_controllers": []}
        if result.returncode != 0:
            return {"at": time.monotonic(), "snapshot_error": True,
                    "owned_processes": [], "unassigned_test_controllers": []}
        records: dict[int, dict[str, Any]] = {}
        for line in result.stdout.splitlines():
            pieces = line.strip().split(None, 5)
            if len(pieces) < 6:
                continue
            try:
                pid, ppid, pgid, rss = int(pieces[0]), int(pieces[1]), int(pieces[2]), int(pieces[4])
            except ValueError:
                continue
            records[pid] = {
                "pid": pid, "ppid": ppid, "pgid": pgid,
                "elapsed_seconds": self._elapsed_seconds(pieces[3]),
                "rss_kib": rss, "command": pieces[5][:240],
            }
        if os.getpid() not in records:
            return {"at": time.monotonic(), "snapshot_error": True,
                    "owned_processes": [], "unassigned_test_controllers": []}
        active_groups = set(self.processes)
        owned = {os.getpid()}
        changed = True
        while changed:
            changed = False
            for pid, row in records.items():
                if pid not in owned and (row["ppid"] in owned or row["pgid"] in active_groups):
                    owned.add(pid)
                    changed = True
        owned_rows = [row for pid, row in records.items() if pid in owned and pid != os.getpid()]
        relevant_owned = [row for row in owned_rows if any(
            token in row["command"].lower() for token in ("python", "pytest", "unittest", "git", "bash", "zsh")
        )]
        unassigned = []
        for pid, row in records.items():
            if pid in owned:
                continue
            command = row["command"].lower()
            python_controller = "python" in command and any(token in command for token in (
                "pytest", "unittest", "run_required_test_suite.py", "scripts/test_", "test_*.py",
            ))
            long_unclassified = "python" in command and "-u -" in command and row["elapsed_seconds"] >= 120
            if python_controller or long_unclassified:
                unassigned.append(row)
                self.unassigned_controllers[pid] = row
        owned_rss = sum(row["rss_kib"] for row in owned_rows)
        self.peak_owned_rss_kib = max(self.peak_owned_rss_kib, owned_rss)
        try:
            load = list(os.getloadavg())
        except (AttributeError, OSError):
            load = None
        return {
            "at": time.monotonic(),
            "owned_process_count": len(owned_rows),
            "owned_processes": relevant_owned[:80],
            "owned_rss_kib": owned_rss,
            "unassigned_test_controllers": unassigned,
            "host_load": load,
        }

    async def _process_context_monitor(self):
        while True:
            self.process_context_samples.append(self._process_snapshot())
            await asyncio.sleep(0.5)

    async def _cancel_after_deadline(self):
        wait = max(0.0, self.global_deadline - self.report_reserve - time.monotonic())
        await asyncio.sleep(wait)
        if not self.cancelled.is_set():
            self.cancel_reason = "timeout"
            self.cancelled.set()
            await self.gate.wake()

    async def run_async(self) -> dict[str, Any]:
        paths, inventory_digest, digests = self._inventory()
        selected = self._selected(paths)
        self.start_monotonic = time.monotonic()
        self.global_deadline = self.start_monotonic + self.suite_timeout
        self.base_report = {
            "schema_version": 1,
            "source_revision": self._git_revision(),
            "repository_root": str(self.root),
            "inventory_digest": inventory_digest,
            "inventory": [{"source_suite": name, "sha256": digest} for name, digest in sorted(digests.items())],
            "selected_suites": [_relative(self.root, path) for path in selected],
            "partial": bool(self.focused_suites or self.focused_test_ids) or self.cancel_reason is not None,
            "focused_test_ids": self.focused_test_ids,
            "workers": self.workers,
            "max_active_children": self.max_active_children,
            "per_script_timeout": self.per_script_timeout,
            "suite_timeout": self.suite_timeout,
            "cleanup_grace": self.cleanup_grace,
            "python_executable": self.python_executable,
            "AI_PLAYBOOK_TEST_VENV": self.venv_bin,
            "pytest_environment": {"PYTEST_ADDOPTS": "", "PYTEST_PLUGINS": "cleared", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
            "pilot_substitutions": [],
            "started_at": time.time(),
        }
        loop = asyncio.get_running_loop()
        installed_signals: list[signal.Signals] = []
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self._receive_signal, sig)
                installed_signals.append(sig)
            except (NotImplementedError, RuntimeError):
                pass
        deadline_task = asyncio.create_task(self._cancel_after_deadline())
        monitor_task = asyncio.create_task(self._process_context_monitor()) if self.capture_process_context else None
        queued = time.monotonic()
        classifications = {path: _scheduling_class(path) for path in selected}
        execution_order = _safe_first_schedule(selected, classifications)
        tasks = [asyncio.create_task(
            self._run_suite(path, queued, classifications[path])
        ) for path in execution_order]
        try:
            execution_results = await asyncio.gather(*tasks)
            by_source = {suite["source_suite"]: suite for suite in execution_results}
            suites = [by_source[_relative(self.root, path)] for path in selected]
        finally:
            deadline_task.cancel()
            if monitor_task is not None:
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
            for sig in installed_signals:
                loop.remove_signal_handler(sig)
        try:
            current_paths, current_digest, current_digests = self._inventory()
            drift = current_digest != inventory_digest
        except Exception as exc:
            current_digest, current_digests, drift = None, {}, True
            self.base_report["inventory_error"] = f"{type(exc).__name__}: {exc}"
        if drift:
            for suite in suites:
                if suite.get("outcome") == "passed":
                    suite["outcome"] = "inventory_drift"
            self.base_report["inventory_drift"] = {
                "initial_digest": inventory_digest, "final_digest": current_digest,
                "initial_files": digests, "final_files": current_digests,
            }
        if self.cancel_reason == "signal":
            status = "cancelled"
        elif self.cancel_reason == "timeout":
            status = "timeout"
        elif any(suite.get("outcome") != "passed" for suite in suites):
            status = "failed"
        else:
            status = "passed"
        report = dict(self.base_report)
        report.update({
            "status": status,
            "suites": suites,
            "suite_count": len(suites),
            "collected": sum(suite.get("collected", 0) for suite in suites),
            "executed": sum(suite.get("executed", 0) for suite in suites),
            "failures": sum(suite.get("failures", 0) for suite in suites),
            "errors": sum(suite.get("errors", 0) for suite in suites),
            "skipped": sum(suite.get("skipped", 0) for suite in suites),
            "ended_at": time.time(),
            "duration": time.monotonic() - self.start_monotonic,
            "report_complete": True,
            "cancellation_reason": self.cancel_reason,
            "partial": bool(self.focused_suites or self.focused_test_ids) or self.cancel_reason is not None,
            "max_active_children": self.max_active_children,
            "process_context": ({
                "sample_count": len(self.process_context_samples),
                "sampling_interval_seconds": 0.5,
                "samples": self.process_context_samples,
                "unassigned_test_controllers": list(self.unassigned_controllers.values()),
                "peak_owned_rss_kib": self.peak_owned_rss_kib,
                "host_load_is_context_only": True,
            } if self.capture_process_context else None),
        })
        return report

    def _receive_signal(self, sig: signal.Signals):
        if not self.cancelled.is_set():
            self.cancel_reason = "signal"
            self.cancelled.set()
            asyncio.create_task(self.gate.wake())

    def write_report(self, report: dict[str, Any]) -> None:
        if self.json_report is None:
            return
        if str(self.json_report) == "-":
            sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
            return
        target = self.json_report if self.json_report.is_absolute() else self.root / self.json_report
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + f".tmp-{os.getpid()}")
        payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
        temporary.write_text(payload, encoding="utf-8")
        os.replace(temporary, target)

    def run(self) -> dict[str, Any]:
        return asyncio.run(self.run_async())


MATCHED_WORKER_ORDERS = ((1, 4, 8), (4, 8, 1), (8, 1, 4))


def _parse_test_id_selectors(values: list[str]) -> dict[str, list[str]]:
    selected: dict[str, list[str]] = defaultdict(list)
    for value in values:
        source, separator, test_id = value.partition("=")
        if not separator or not source or not test_id:
            raise ValueError("each --test-id must have the form SUITE=ID")
        source = source.removeprefix("./")
        if not source.startswith("scripts/"):
            source = "scripts/" + source
        selected[source].append(test_id)
    return dict(selected)


def _process_attribution_passed(process_context: dict[str, Any]) -> bool:
    samples = process_context.get("samples")
    if not isinstance(samples, list) or not samples:
        return False
    if any(not isinstance(sample, dict) or sample.get("snapshot_error") for sample in samples):
        return False
    return not process_context.get("unassigned_test_controllers")


def _campaign_qualification(runs: list[dict[str, Any]]) -> dict[str, Any]:
    expected_order = [
        {"round": round_number, "workers": worker_count}
        for round_number, order in enumerate(MATCHED_WORKER_ORDERS, start=1)
        for worker_count in order
    ]
    actual_order = [{"round": item["round"], "workers": item["workers"]} for item in runs]
    complete = actual_order == expected_order and len(runs) == 9
    same_inputs = bool(runs) and len({item.get("sample_fingerprint") for item in runs}) == 1
    same_inventory = bool(runs) and len({item.get("inventory_digest") for item in runs}) == 1
    environment_match = bool(runs) and len({item.get("environment_fingerprint") for item in runs}) == 1
    all_resource_checks = complete and all(item.get("resource_check_passed") for item in runs)
    metrics: dict[str, dict[str, Any]] = {}
    baseline = [item["wall_seconds"] for item in runs if item["workers"] == 1]
    if len(baseline) == 3:
        median_one = statistics.median(baseline)
        range_one = max(baseline) - min(baseline)
    else:
        median_one = None
        range_one = None
    qualifying: list[int] = []
    for worker_count in (4, 8):
        values = [item["wall_seconds"] for item in runs if item["workers"] == worker_count]
        if len(values) != 3 or median_one is None or range_one is None:
            metrics[str(worker_count)] = {
                "rounds": len(values), "median_seconds": None, "range_seconds": None,
                "gain_seconds": None, "resource_checks_passed": all_resource_checks,
                "qualifies": False,
            }
            continue
        median_candidate = statistics.median(values)
        candidate_range = max(values) - min(values)
        gain = median_one - median_candidate
        qualifies = (
            complete and same_inputs and same_inventory and environment_match
            and all_resource_checks and gain > max(range_one, candidate_range)
        )
        if qualifies:
            qualifying.append(worker_count)
        metrics[str(worker_count)] = {
            "rounds": 3,
            "median_seconds": median_candidate,
            "range_seconds": candidate_range,
            "gain_seconds": gain,
            "resource_checks_passed": all_resource_checks,
            "qualifies": qualifies,
        }
    return {
        "complete": complete,
        "same_sample": same_inputs,
        "same_inventory": same_inventory,
        "same_environment": environment_match,
        "baseline": {
            "rounds": len(baseline), "median_seconds": median_one,
            "range_seconds": range_one,
        },
        "candidates": metrics,
        "qualified_workers": sorted(qualifying),
        "selected_workers": max(qualifying) if qualifying else 1,
    }


def _write_json_atomic(target: Path, payload: dict[str, Any]) -> None:
    if str(target) == "-":
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + f".tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, target)


def _run_matched_campaign(args: argparse.Namespace, focused_ids: dict[str, list[str]]) -> dict[str, Any]:
    if args.campaign_timeout <= 0 or args.campaign_timeout > 300:
        raise ValueError("campaign-timeout must be greater than zero and no more than 300 seconds")
    if not args.suite:
        raise ValueError("matched-worker mode needs one or more explicit --suite samples")
    if not focused_ids:
        raise ValueError("matched-worker mode needs exact --test-id samples for matched inputs")
    started = time.monotonic()
    first = RequiredTestSuiteRunner(
        args.repo_root, workers=1, per_script_timeout=args.per_script_timeout,
        suite_timeout=min(args.suite_timeout, args.campaign_timeout),
        cleanup_grace=args.cleanup_grace, focused_suites=args.suite,
        focused_test_ids=focused_ids, json_report=None,
    )
    initial_paths, inventory_digest, all_digests = first._inventory()
    sample_paths = first._selected(initial_paths)
    selected_sources = set(focused_ids)
    selected_suite_sources = {_relative(first.root, path) for path in sample_paths}
    if not selected_sources.issubset(selected_suite_sources):
        raise ValueError("every --test-id sample source must also appear in --suite")
    sample = []
    for path in sample_paths:
        name = _relative(first.root, path)
        ids = focused_ids.get(name)
        if not ids:
            raise ValueError(f"matched sample requires exact test IDs for {name}")
        classification, evidence = _scheduling_class(path)
        sample.append({
            "source_suite": name,
            "source_sha256": all_digests[name],
            "scheduling_class": classification,
            "scheduling_evidence": evidence,
            "test_ids": ids,
        })
    inventory_classes = {_scheduling_class(path)[0] for path in initial_paths}
    sample_classes = [item["scheduling_class"] for item in sample]
    if set(sample_classes) != inventory_classes or len(sample_classes) != len(set(sample_classes)):
        raise ValueError(
            "matched sample must include exactly one highest-cost source or shard sample per live scheduling class; "
            f"inventory classes={sorted(inventory_classes)} sample classes={sorted(sample_classes)}"
        )
    sample_fingerprint = hashlib.sha256(json.dumps(sample, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    env_fingerprint = hashlib.sha256(json.dumps(first._child_env(), sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    witnesses = []
    for witness_value in args.profile_witness:
        witness_path = Path(witness_value)
        if not witness_path.is_absolute():
            witness_path = first.root / witness_path
        if not witness_path.is_file():
            raise ValueError(f"profile witness is missing: {witness_value}")
        witnesses.append({
            "path": _relative(first.root, witness_path) if witness_path.is_relative_to(first.root) else str(witness_path),
            "sha256": _sha256(witness_path),
        })
    rounds: list[dict[str, Any]] = []
    complete = True
    for round_number, order in enumerate(MATCHED_WORKER_ORDERS, start=1):
        for worker_count in order:
            elapsed = time.monotonic() - started
            remaining = args.campaign_timeout - elapsed
            if remaining <= max(1.0, args.cleanup_grace + 0.5):
                complete = False
                break
            run_timeout = min(args.suite_timeout, remaining - min(2.0, max(0.1, args.cleanup_grace)))
            runner = RequiredTestSuiteRunner(
                args.repo_root, workers=worker_count,
                per_script_timeout=args.per_script_timeout,
                suite_timeout=run_timeout,
                cleanup_grace=args.cleanup_grace,
                focused_suites=args.suite, focused_test_ids=focused_ids,
                capture_process_context=True,
                json_report=None,
            )
            report = runner.run()
            elapsed = time.monotonic() - started
            active_ok = report["max_active_children"] <= worker_count
            suites_ok = all(
                suite.get("outcome") == "passed"
                and suite.get("duration", args.per_script_timeout + 1) <= args.per_script_timeout
                and suite.get("accounting_exact", False)
                for suite in report["suites"]
            )
            inventory_ok = report["inventory_digest"] == inventory_digest
            process_context = report.get("process_context") or {}
            attribution_ok = _process_attribution_passed(process_context)
            resource_ok = active_ok and suites_ok and inventory_ok and attribution_ok and report["status"] == "passed"
            rounds.append({
                "round": round_number,
                "workers": worker_count,
                "order": list(order),
                "wall_seconds": report["duration"],
                "campaign_elapsed_seconds": elapsed,
                "status": report["status"],
                "inventory_digest": report["inventory_digest"],
                "sample_fingerprint": sample_fingerprint,
                "environment_fingerprint": env_fingerprint,
                "max_active_children": report["max_active_children"],
                "active_child_bound_passed": active_ok,
                "suite_accounting_passed": suites_ok,
                "process_attribution_passed": attribution_ok,
                "resource_check_passed": resource_ok,
                "process_context": process_context,
                "sample_suites": [{
                    "source_suite": suite["source_suite"],
                    "source_sha256": suite["source_sha256"],
                    "scheduling_class": suite["scheduling_class"],
                    "queue_wait": suite.get("queue_wait"),
                    "duration": suite.get("duration"),
                    "collected_ids": suite.get("collected_ids", []),
                    "executed_ids": suite.get("executed_ids", []),
                    "outcome": suite.get("outcome"),
                    "shards": [{
                        "shard_id": shard["shard_id"],
                        "test_ids": shard["test_ids"],
                        "source_sha256": shard["source_sha256"],
                        "duration": shard["duration"],
                        "outcome": shard["outcome"],
                        "collection_exact": shard["collection_exact"],
                        "execution_exact": shard["execution_exact"],
                    } for shard in suite.get("shards", [])],
                } for suite in report["suites"]],
            })
            if not resource_ok or elapsed >= args.campaign_timeout:
                complete = False
                break
        if not complete:
            break
    qualification = _campaign_qualification(rounds)
    if not complete:
        qualification["selected_workers"] = 1
        for candidate in qualification["candidates"].values():
            candidate["qualifies"] = False
    return {
        "schema_version": 1,
        "mode": "matched-worker-campaign",
        "status": "pass" if complete and qualification["complete"] else "incomplete",
        "campaign_limit_seconds": args.campaign_timeout,
        "campaign_elapsed_seconds": time.monotonic() - started,
        "per_script_limit_seconds": args.per_script_timeout,
        "round_orders": [list(order) for order in MATCHED_WORKER_ORDERS],
        "initial_inventory_digest": inventory_digest,
        "initial_inventory_count": len(initial_paths),
        "sample": sample,
        "profile_witnesses": witnesses,
        "sample_fingerprint": sample_fingerprint,
        "environment_fingerprint": env_fingerprint,
        "resource_check": "all selected suites pass exact accounting, all source durations are <= per-script limit, inventory is stable, and observed active children never exceed the requested worker count",
        "rounds": rounds,
        "qualification": qualification,
        "selected_workers": qualification["selected_workers"],
        "pilot_substitutions": [],
        "note": "Task 3 rejected the candidate pilots; every live source test ID remains in Python inventory.",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--suite", action="append", default=[], help="focused suite path or basename; repeatable")
    parser.add_argument("--test-id", action="append", default=[], metavar="SUITE=ID",
                        help="run a focused test ID from one suite; repeatable")
    parser.add_argument("--workers", type=int, default=1, choices=(1, 4, 8))
    parser.add_argument("--per-script-timeout", type=float, default=DEFAULT_PER_SCRIPT_TIMEOUT)
    parser.add_argument("--suite-timeout", type=float, default=DEFAULT_SUITE_TIMEOUT)
    parser.add_argument("--cleanup-grace", type=float, default=DEFAULT_CLEANUP_GRACE)
    parser.add_argument("--json-report", default="docs/tmp/required-test-suite.json")
    parser.add_argument("--matched-workers", action="store_true",
                        help="run the matched 1/4/8-worker qualification campaign")
    parser.add_argument("--campaign-timeout", type=float, default=300.0)
    parser.add_argument("--profile-witness", action="append", default=[],
                        help="profile artifact supporting highest-cost sample selection; repeatable")
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--_worker" in argv:
        return _worker_main(argv)
    args = _parser().parse_args(argv)
    if args.per_script_timeout <= 0 or args.per_script_timeout > DEFAULT_PER_SCRIPT_TIMEOUT:
        print("per-script-timeout must be greater than zero and no more than 60 seconds", file=sys.stderr)
        return 2
    if args.suite_timeout <= 0 or args.suite_timeout >= 300:
        print("suite-timeout must be greater than zero and less than 300 seconds", file=sys.stderr)
        return 2
    if args.cleanup_grace <= 0 or args.cleanup_grace >= args.per_script_timeout:
        print("cleanup-grace must be positive and less than per-script-timeout", file=sys.stderr)
        return 2
    try:
        focused_ids = _parse_test_id_selectors(args.test_id)
        if args.matched_workers:
            report = _run_matched_campaign(args, focused_ids)
            report_path = Path(args.json_report)
            if str(report_path) != "-" and not report_path.is_absolute():
                report_path = Path(args.repo_root).resolve() / report_path
            _write_json_atomic(report_path, report)
            if args.json_report != "-":
                print(json.dumps({
                    "status": report["status"], "report": str(args.json_report),
                    "selected_workers": report["selected_workers"],
                    "campaign_elapsed_seconds": report["campaign_elapsed_seconds"],
                }, sort_keys=True))
            return 0 if report["status"] == "pass" else 1
        runner = RequiredTestSuiteRunner(
            args.repo_root, workers=args.workers,
            per_script_timeout=args.per_script_timeout, suite_timeout=args.suite_timeout,
            cleanup_grace=args.cleanup_grace, focused_suites=args.suite,
            focused_test_ids=focused_ids,
            json_report=args.json_report,
        )
        report = runner.run()
        runner.write_report(report)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"required-suite runner error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    if args.json_report != "-":
        print(json.dumps({
            "status": report["status"], "report": str(args.json_report),
            "suite_count": report["suite_count"], "collected": report["collected"],
            "executed": report["executed"], "duration": report["duration"],
        }, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
