#!/usr/bin/env python3
"""Fixture-only activation help probe."""

from __future__ import annotations

import sys
import importlib.util
from pathlib import Path


if len(sys.argv) != 3 or not Path(sys.argv[2]).is_file():
    raise SystemExit(2)
if sys.argv[1] == "driver":
    spec = importlib.util.spec_from_file_location("loaded_execute_plan_runtime", sys.argv[2])
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if not hasattr(module, "RuntimeDriver"):
        raise SystemExit(3)
print(f"{sys.argv[1]}-help-ok")
