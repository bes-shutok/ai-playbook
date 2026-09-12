#!/usr/bin/env python3
"""Quota window probe pure core.

Parses Z.ai/ZCode limit responses and Codex rollout rate-limit records into a
uniform limit contract, selects the binding (earliest resetting) window, and
evaluates pause thresholds. Pure stdlib, no network; Task 2 adds transports
behind injectable interfaces on top of this module.
"""

from __future__ import annotations

import argparse
import io
import json
import os
from datetime import datetime
import pathlib
import sys
import time
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence
import urllib.request

# Z.ai limit entry type -> window kind. Calibrated against the documented
# semantics (TOKENS_LIMIT carries the 5-hour token window that reports the
# reset; TIME_LIMIT is the secondary time window). See the task log for the
# calibration note; timezone encoding lives in the user facts document only.
ZCODE_KIND_MAP = {
    "TOKENS_LIMIT": "primary",
    "TIME_LIMIT": "secondary",
}

DEFAULT_MINUTES_THRESHOLD = 20
DEFAULT_PERCENT_THRESHOLD = 90


def make_limit(kind: str, used_percent: float, reset_at_epoch: int, now: float,
               window_minutes: Optional[int] = None) -> dict:
    # ``window_minutes`` stays in the signature for compatibility and is
    # deliberately not carried in the contract: nothing downstream consumes
    # window length, only reset times and usage.
    return {
        "kind": kind,
        "used_percent": used_percent,
        "reset_at_epoch": reset_at_epoch,
        # Local timezone of the host; never a hardcoded zone.
        "reset_at_iso": datetime.fromtimestamp(reset_at_epoch).astimezone().isoformat(),
        "minutes_remaining": int((reset_at_epoch - now) // 60),
    }


def _find_first(obj: Any, predicate: Callable[[Any], bool]) -> Any:
    """Depth-first search for the first value satisfying ``predicate``."""
    if predicate(obj):
        return obj
    if isinstance(obj, Mapping):
        children: Iterable[Any] = obj.values()
    elif isinstance(obj, Sequence) and not isinstance(obj, (str, bytes)):
        children = obj
    else:
        return None
    for child in children:
        found = _find_first(child, predicate)
        if found is not None:
            return found
    return None


def _has_limits_array(node: Any) -> bool:
    limits = node.get("limits") if isinstance(node, Mapping) else None
    return isinstance(limits, Sequence) and not isinstance(limits, (str, bytes))


def _find_limits_array(payload: Any) -> Optional[Sequence[Mapping]]:
    holder = _find_first(payload, _has_limits_array)
    return holder["limits"] if holder is not None else None


def parse_zcode_limits(payload: Mapping, now: Optional[float] = None) -> list[dict]:
    """Parse a Z.ai quota/limit response into the limit contract.

    ``nextResetTime`` is epoch milliseconds in the source payload; the contract
    carries epoch seconds. Kind mapping per ZCODE_KIND_MAP.
    """
    if now is None:
        now = time.time()
    entries = _find_limits_array(payload) or []
    limits = []
    for entry in entries:
        kind = ZCODE_KIND_MAP.get(entry.get("type"))
        if kind is None or "nextResetTime" not in entry:
            continue
        limits.append(make_limit(
            kind=kind,
            used_percent=float(entry["percentage"]),
            reset_at_epoch=int(entry["nextResetTime"]) // 1000,
            now=now,
        ))
    return limits


def _find_rate_limits(obj: Any) -> Optional[Mapping]:
    def has_rate_limits(node: Any) -> bool:
        return isinstance(node, Mapping) and isinstance(node.get("rate_limits"), Mapping)

    holder = _find_first(obj, has_rate_limits)
    return holder["rate_limits"] if holder is not None else None


def parse_codex_rollout(lines: Iterable[str], now: Optional[float] = None) -> list[dict]:
    """Parse rollout JSONL lines; the last record carrying rate_limits wins."""
    if now is None:
        now = time.time()
    latest: Optional[Mapping] = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        found = _find_rate_limits(record)
        if found is not None:
            latest = found
    if latest is None:
        return []
    limits = []
    for kind in ("primary", "secondary"):
        window = latest.get(kind)
        if not isinstance(window, Mapping) or "resets_at" not in window:
            continue
        limits.append(make_limit(
            kind=kind,
            used_percent=float(window["used_percent"]),
            reset_at_epoch=int(window["resets_at"]),
            now=now,
        ))
    return limits


def select_binding(limits: Sequence[Mapping]) -> Optional[str]:
    """The binding window is the limit whose reset_at_epoch is earliest."""
    if not limits:
        return None
    return min(limits, key=lambda limit: limit["reset_at_epoch"])["kind"]


def evaluate_pause(limits: Sequence[Mapping], binding: Optional[str],
                   minutes_threshold: int = DEFAULT_MINUTES_THRESHOLD,
                   percent_threshold: float = DEFAULT_PERCENT_THRESHOLD) -> tuple[str, list[str]]:
    binding_limit = next((limit for limit in limits if limit["kind"] == binding), None)
    if binding_limit is None:
        return "continue", []
    reasons = []
    if binding_limit["minutes_remaining"] < minutes_threshold:
        reasons.append(
            "minutes_remaining {} below {}".format(
                binding_limit["minutes_remaining"], minutes_threshold
            )
        )
    if binding_limit["used_percent"] >= percent_threshold:
        reasons.append(
            "used_percent {} at or above {}".format(
                binding_limit["used_percent"], percent_threshold
            )
        )
    return ("pause" if reasons else "continue"), reasons


def build_report(runtime: str, limits: Sequence[Mapping],
                 minutes_threshold: int = DEFAULT_MINUTES_THRESHOLD,
                 percent_threshold: float = DEFAULT_PERCENT_THRESHOLD,
                 now: Optional[float] = None) -> dict:
    """Evaluate only live windows; an all-expired limit set fails open.

    A limit whose ``reset_at_epoch`` is at or before ``now`` describes a
    window that already closed: the data is stale and must never win the
    binding selection (an expired earliest reset would force a pause that
    immediately thrashes into a resume). If there were limits but none are
    live, the report degrades to status ``unknown`` (fail open). An empty
    ``limits`` sequence is also reported as ``unknown`` ("no limits
    supplied"): pure-core direct callers pass no windows, and no data must
    never be treated as an all-clear.
    """
    if now is None:
        now = time.time()
    if not limits:
        return _unknown_report(runtime, ["no limits supplied"])
    live = [limit for limit in limits if limit["reset_at_epoch"] > now]
    if not live:
        return _unknown_report(runtime, ["all quota windows already reset; data stale"])
    binding = select_binding(live)
    decision, reasons = evaluate_pause(
        live, binding,
        minutes_threshold=minutes_threshold,
        percent_threshold=percent_threshold,
    )
    return {
        "runtime": runtime,
        "limits": list(live),
        "binding": binding,
        "pause_decision": decision,
        "reasons": reasons,
        "status": "ok",
    }


# --- Task 2: transports, runtime discovery, fail-open, flag write ---

ZCODE_QUOTA_URL = "https://api.z.ai/api/quota/limit"
DEFAULT_ZCODE_CONFIG = pathlib.Path("~/.zcode/cli/config.json").expanduser()
DEFAULT_CODEX_SESSIONS = pathlib.Path("~/.codex/sessions").expanduser()

Transport = Callable[[str, Mapping[str, str]], str]


def urllib_transport(url: str, headers: Mapping[str, str]) -> str:
    """Default HTTPS transport (stdlib urllib). Host context only."""
    request = urllib.request.Request(url, headers=dict(headers))
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.read().decode("utf-8")


def load_api_key(config_path: os.PathLike | str) -> Optional[str]:
    """Read provider.zai.options.apiKey from the ZCode CLI config (nested JSON)."""
    try:
        payload = json.loads(pathlib.Path(config_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    node = payload
    for key in ("provider", "zai", "options"):
        if not isinstance(node, Mapping):
            return None
        node = node.get(key)
    if isinstance(node, Mapping) and isinstance(node.get("apiKey"), str):
        return node["apiKey"]
    return None


def probe_zcode(config_path: os.PathLike | str = DEFAULT_ZCODE_CONFIG,
                url: str = ZCODE_QUOTA_URL,
                transport: Optional[Transport] = None,
                now: Optional[float] = None,
                minutes_threshold: int = DEFAULT_MINUTES_THRESHOLD,
                percent_threshold: float = DEFAULT_PERCENT_THRESHOLD) -> dict:
    """Fetch Z.ai limits via the transport; fail open on any failure."""
    if transport is None:
        transport = urllib_transport
    api_key = load_api_key(config_path)
    if not api_key:
        return _unknown_report("zcode", ["zcode config missing provider.zai.options.apiKey"])
    try:
        body = transport(url, {"Authorization": api_key})
        payload = json.loads(body)
        limits = parse_zcode_limits(payload, now=now)
    except Exception as exc:  # fail open: any transport/parse failure
        return _unknown_report("zcode", ["zcode quota fetch failed: {}".format(exc)])
    if not limits:
        return _unknown_report("zcode", ["zcode quota response carried no usable limits"])
    return build_report("zcode", limits,
                        minutes_threshold=minutes_threshold,
                        percent_threshold=percent_threshold, now=now)


def discover_codex_rollout(sessions_dir: os.PathLike | str) -> Optional[pathlib.Path]:
    """Newest rollout-*.jsonl under the sessions tree, by name sort."""
    root = pathlib.Path(sessions_dir)
    if not root.is_dir():
        return None
    candidates = sorted(root.rglob("rollout-*.jsonl"))
    return candidates[-1] if candidates else None


def probe_codex(sessions_dir: os.PathLike | str = DEFAULT_CODEX_SESSIONS,
                now: Optional[float] = None,
                minutes_threshold: int = DEFAULT_MINUTES_THRESHOLD,
                percent_threshold: float = DEFAULT_PERCENT_THRESHOLD) -> dict:
    """Parse the newest Codex rollout tail; fail open on absence."""
    rollout = discover_codex_rollout(sessions_dir)
    if rollout is None:
        return _unknown_report(
            "codex", ["no rollout-*.jsonl found under sessions dir {}".format(sessions_dir)]
        )
    try:
        text = rollout.read_text(encoding="utf-8")
        # Parse stays inside the guard: a malformed rollout record (for
        # example a non-numeric used_percent) must fail open like every
        # other transport/parse failure, never escape as a traceback.
        limits = parse_codex_rollout(text.splitlines(), now=now)
    except Exception as exc:  # fail open: any read/parse failure
        return _unknown_report("codex", ["codex rollout parse failed: {}".format(exc)])
    if not limits:
        return _unknown_report("codex", ["rollout carried no rate_limits record"])
    return build_report("codex", limits,
                        minutes_threshold=minutes_threshold,
                        percent_threshold=percent_threshold, now=now)


def detect_runtime(explicit: Optional[str] = None,
                   zcode_config: os.PathLike | str = DEFAULT_ZCODE_CONFIG,
                   codex_sessions: os.PathLike | str = DEFAULT_CODEX_SESSIONS) -> Optional[str]:
    """Explicit override wins; documented autodetect precedence is zcode then codex."""
    if explicit in ("zcode", "codex"):
        return explicit
    if pathlib.Path(zcode_config).exists():
        return "zcode"
    if pathlib.Path(codex_sessions).is_dir():
        return "codex"
    return None


def add_secondary_report_only_reason(report: dict) -> dict:
    """When the binding window is the secondary one, mark it report-only."""
    if report.get("binding") == "secondary":
        report["reasons"].append(
            "binding window is the weekly secondary window; report-only, do not schedule a same-day resume"
        )
    return report


def write_flag_if_paused(flag_path: os.PathLike | str, runtime: str,
                         limits: Sequence[Mapping], decision: str,
                         plan: Optional[str] = None) -> bool:
    """Atomically write the guard flag (mode 0o600) only on a pause decision."""
    if decision != "pause":
        return False
    binding = select_binding(limits)
    if binding == "secondary":
        # Report-only: a weekly secondary window must not arm the host-global
        # guard flag, which gates every registered runtime.
        return False
    binding_limit = next((l for l in limits if l["kind"] == binding), None)
    if binding_limit is None:
        return False
    lines = [
        "runtime={}".format(runtime),
        "reset_at_epoch={}".format(binding_limit["reset_at_epoch"]),
        "reset_at_iso={}".format(binding_limit["reset_at_iso"]),
    ]
    if plan:
        lines.append("plan={}".format(plan))
    path = pathlib.Path(flag_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    return True


def _unknown_report(runtime: str, reasons: list[str]) -> dict:
    return {
        "runtime": runtime,
        "limits": [],
        "binding": None,
        "pause_decision": "continue",
        "reasons": reasons,
        "status": "unknown",
    }


def run_probe(runtime: str,
              config_path: os.PathLike | str = DEFAULT_ZCODE_CONFIG,
              sessions_dir: os.PathLike | str = DEFAULT_CODEX_SESSIONS,
              url: str = ZCODE_QUOTA_URL,
              transport: Optional[Transport] = None,
              now: Optional[float] = None,
              minutes_threshold: int = DEFAULT_MINUTES_THRESHOLD,
              percent_threshold: float = DEFAULT_PERCENT_THRESHOLD) -> dict:
    if runtime == "zcode":
        report = probe_zcode(config_path=config_path, url=url, transport=transport, now=now,
                             minutes_threshold=minutes_threshold,
                             percent_threshold=percent_threshold)
    else:
        report = probe_codex(sessions_dir=sessions_dir, now=now,
                             minutes_threshold=minutes_threshold,
                             percent_threshold=percent_threshold)
    return add_secondary_report_only_reason(report)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Quota window probe (stdlib only). Exit codes: 0 = pause decision, "
            "1 = continue (including status unknown). Parse pause_decision "
            "from the stdout JSON report, not from the exit code."
        )
    )
    parser.add_argument("--runtime", choices=("zcode", "codex"))
    parser.add_argument("--minutes-before", type=int, default=DEFAULT_MINUTES_THRESHOLD)
    parser.add_argument("--max-percent", type=float, default=DEFAULT_PERCENT_THRESHOLD)
    parser.add_argument("--write-flag")
    parser.add_argument("--config", default=str(DEFAULT_ZCODE_CONFIG))
    parser.add_argument("--sessions-dir", default=str(DEFAULT_CODEX_SESSIONS))
    parser.add_argument("--url", default=ZCODE_QUOTA_URL)
    parser.add_argument("--plan")
    args = parser.parse_args(argv)
    try:
        runtime = detect_runtime(
            args.runtime, zcode_config=args.config, codex_sessions=args.sessions_dir
        )
    except Exception as exc:
        # Fail open: runtime detection itself must never escape as a traceback
        # (for example an embedded NUL byte in a --config path raises before
        # any filesystem check); degrade to an unknown JSON report.
        report = _unknown_report("none", ["runtime detection failed: {}".format(exc)])
    else:
        if runtime is None:
            report = _unknown_report("none", ["no agent runtime detected; pass --runtime explicitly"])
        else:
            report = run_probe(runtime, config_path=args.config, sessions_dir=args.sessions_dir,
                               url=args.url, minutes_threshold=args.minutes_before,
                               percent_threshold=args.max_percent)
    if args.write_flag:
        try:
            write_flag_if_paused(args.write_flag, report["runtime"], report["limits"],
                                 report["pause_decision"], plan=args.plan)
        except OSError as exc:
            # Fail-open: a failed flag write never masks the JSON report.
            report = dict(report)
            report["reasons"] = list(report["reasons"]) + ["flag write failed: {}".format(exc)]
    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if report["pause_decision"] == "pause" else 1


if __name__ == "__main__":
    sys.exit(main())
