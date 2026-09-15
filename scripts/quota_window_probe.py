#!/usr/bin/env python3
"""Quota window probe pure core.

Parses Z.ai/ZCode limit responses and Codex rollout rate-limit records into a
uniform limit contract, selects the binding (earliest resetting) window, and
evaluates pause thresholds. Pure stdlib, no network; Task 2 adds transports
behind injectable interfaces on top of this module.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from datetime import datetime
import pathlib
import sys
import time
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence
import urllib.error
import urllib.request

# Z.ai limit entry type -> window kind. Kind calibration (do not skip
# silently): cross-check each type's nextResetTime against the observed
# exhaustion line in the local ZCode log; TOKENS_LIMIT is the 5-hour window
# that reports the reset (primary), TIME_LIMIT the weekly secondary window.
# When no local exhaustion line is observable (fresh host, rotated or cleaned
# logs, never-exhausted window), calibrate against a live nextResetTime
# progression observed across two probe calls spaced apart (the moving window
# is primary), or record the mapping as provisionally documented with the
# fixture carrying the documented mapping and an explicit note in the run
# log. Never skip the calibration silently; timezone encoding lives in the
# user facts document only.
ZCODE_KIND_MAP = {
    "TOKENS_LIMIT": "primary",
    "TIME_LIMIT": "secondary",
}

DEFAULT_MINUTES_THRESHOLD = 20
DEFAULT_PERCENT_THRESHOLD = 90

# Provider-reported resets beyond this horizon are clamped (review r1 F2):
# the widest legitimate window observed is the monthly-scale secondary reset
# in the captured live payload (about 26 days out), so the horizon covers a
# full billing cycle plus margin while still bounding a hostile or buggy
# epoch to weeks instead of an unbounded host-global lockout. The same bound
# is enforced again at flag-write time as defense in depth.
MAX_RESET_HORIZON_SECONDS = 40 * 86400


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


def _validated_limit(kind: str, raw_percent: Any, raw_reset: Any, now: float,
                     reset_is_ms: bool = False) -> Optional[dict]:
    """Shared per-entry guard for both parse loops (review r3 F4).

    Absorbs convert -> validate -> clamp -> construct -> marker so a guard
    edit cannot land in one runtime's parser and miss the other's (a drift
    that already materialized once on this branch). Returns None when the
    entry must drop alone; a malformed entry never aborts the parse.

    - Conversion and limit construction sit inside per-entry guards
      (review r2 F3): a non-numeric value, an epoch datetime cannot
      represent, or a platform localtime failure (``OSError`` band,
      review r3 F2) drops only its own entry.
    - Non-finite or out-of-range percentages drop the entry (review r1 F2).
    - Implausibly far horizons clamp to now + MAX_RESET_HORIZON_SECONDS,
      and an engaged clamp is observable via a ``reset_clamped`` marker
      (review r1 F2, r2 F7).
    """
    try:
        used_percent = float(raw_percent)
        reset_at_epoch = int(raw_reset)
        if reset_is_ms:
            reset_at_epoch //= 1000
    except (TypeError, ValueError, OverflowError, OSError):
        return None
    # Reject non-finite or out-of-range percentages per entry (review
    # r1 F2): a fabricated inf/NaN/100+ percent must neither force a
    # false pause nor abort the whole report.
    if not (math.isfinite(used_percent) and 0.0 <= used_percent <= 100.0):
        return None
    # Clamp implausibly far horizons: a provider-chosen epoch must not
    # arm a months-or-years-long host-global lockout (review r1 F2).
    # An engaged clamp is observable (review r2 F7): the limit carries
    # a reset_clamped marker that build_report turns into a reason.
    clamped = min(reset_at_epoch, int(now) + MAX_RESET_HORIZON_SECONDS)
    try:
        entry_limit = make_limit(
            kind=kind,
            used_percent=used_percent,
            reset_at_epoch=clamped,
            now=now,
        )
    except (TypeError, ValueError, OverflowError, OSError):
        # Limit construction stays inside the guard (review r2 F3): an
        # epoch datetime cannot represent (for example a negative value,
        # a year outside 1..9999, or the OSError localtime band) drops
        # its entry alone.
        return None
    if clamped < reset_at_epoch:
        entry_limit["reset_clamped"] = True
    return entry_limit


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
        # Symmetric entry guard (review r1 F6, extended r2 F3): a
        # non-mapping element, a missing epoch OR a missing percentage
        # drops only this entry, so one malformed limit cannot blind the
        # whole gate (both windows).
        if not isinstance(entry, Mapping):
            continue
        # Review r3 F2: the kind lookup needs a hashable key. A list- or
        # dict-typed ``type`` would raise TypeError (unhashable) outside
        # any guard and abort the whole parse, so validate the shape
        # before the map lookup.
        entry_type = entry.get("type")
        if not isinstance(entry_type, str):
            continue
        kind = ZCODE_KIND_MAP.get(entry_type)
        if kind is None or "nextResetTime" not in entry or "percentage" not in entry:
            continue
        entry_limit = _validated_limit(
            kind, entry["percentage"], entry["nextResetTime"], now, reset_is_ms=True
        )
        if entry_limit is not None:
            limits.append(entry_limit)
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
        # Same per-entry isolation and validation shape as the zcode path
        # (review r2 F3 + r2 F5), shared via _validated_limit since r3 F4:
        # a non-mapping window, a non-numeric value, a non-finite or
        # out-of-range percent (JSON Infinity/NaN literals parse), an
        # epoch datetime cannot represent, or an OSError-band epoch drops
        # ONLY this window; resets_at is clamped to the same horizon.
        window = latest.get(kind)
        if not isinstance(window, Mapping) or "resets_at" not in window:
            continue
        entry_limit = _validated_limit(
            kind, window.get("used_percent"), window["resets_at"], now
        )
        if entry_limit is not None:
            limits.append(entry_limit)
    return limits


def rollout_carries_rate_limits(lines: Iterable[str]) -> bool:
    """True when any rollout line parses to a record carrying rate_limits.

    Mirrors parse_codex_rollout's own scan (strip per line, skip blanks and
    unparseable lines, json.loads per record); unlike the parser, which
    lets the last record win, this predicate returns on the first record
    carrying rate_limits, so probe_codex can distinguish a record whose
    windows all dropped from a record-less rollout at fail-open time
    without touching the parser's list[dict] return contract.
    """
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if _find_rate_limits(record) is not None:
            return True
    return False


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
    # An engaged horizon clamp is observable (review r2 F7): a clamped
    # limit's reset time is a bound, not the provider's real reset.
    if any(limit.get("reset_clamped") for limit in live):
        # Review r3 F6: the day figure derives from the constant so a
        # retune cannot leave this reason lying.
        reasons.append(
            "reset clamped to {}-day horizon".format(
                MAX_RESET_HORIZON_SECONDS // 86400
            )
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

# Live Z.ai monitor endpoint (extracted from the ZCode desktop app bundle, 2026-09-13); the legacy https://api.z.ai/api/quota/limit answers 404-NOT_FOUND inside HTTP 200, which read as a permanent status: unknown; do not revert.
ZCODE_QUOTA_URL = "https://api.z.ai/api/monitor/usage/quota/limit"
DEFAULT_ZCODE_CONFIG = pathlib.Path("~/.zcode/cli/config.json").expanduser()
DEFAULT_CODEX_SESSIONS = pathlib.Path("~/.codex/sessions").expanduser()

Transport = Callable[[str, Mapping[str, str]], str]


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    # Documented replacement idiom (review r2 F9): a redirect handler whose
    # redirect_request returns None makes the opener treat any 3xx as an
    # error instead of following it. The transport's URL is the fixed
    # https ZCODE_QUOTA_URL constant, so the handler-set difference versus
    # the previously hand-assembled opener (which omitted the FTP/File/Data
    # handlers) is moot for scheme coverage; build_opener() drops its
    # default HTTPRedirectHandler in favor of this subclass automatically.
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _build_no_redirect_opener() -> "urllib.request.OpenerDirector":
    # urllib's default opener follows redirects and replays every request
    # header (including Authorization) verbatim to the redirect target, so a
    # 3xx from the trusted endpoint could leak the provider API key to an
    # arbitrary cross-host or cleartext downgrade. With _NoRedirectHandler
    # installed, a 3xx surfaces as an HTTPError
    # (HTTPErrorProcessor -> HTTPDefaultErrorHandler) and probe_zcode fails
    # open to status: unknown with that reason. Filtering the handler list
    # of a build_opener() result would NOT unregister the redirect methods,
    # so the subclass replaces the default handler instead.
    return urllib.request.build_opener(_NoRedirectHandler())


_OPENER_NO_REDIRECTS = _build_no_redirect_opener()


def urllib_transport(url: str, headers: Mapping[str, str]) -> str:
    """Default HTTPS transport (stdlib urllib; redirects never followed)."""
    request = urllib.request.Request(url, headers=dict(headers))
    try:
        with _OPENER_NO_REDIRECTS.open(request, timeout=10) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        # Review r3 F9: the fail-open 3xx path surfaces as an HTTPError
        # that carries the open response body; close it deterministically
        # before the error propagates to the guard's unknown report, so
        # the body is never left to the garbage collector's implicit
        # cleanup (witnessed by test_zcode_transport_never_follows_
        # redirects, which escalates ResourceWarning and records
        # sys.unraisablehook unraisables across a forced collection pass;
        # escalation alone is vacuous on py3.14, see python guidelines
        # rule 33; review r4 F2).
        exc.close()
        raise


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
        # Parse stays inside the guard: a read or unexpected parse failure
        # must fail open like every other transport/parse failure, never
        # escape as a traceback (per-entry malformed windows now drop
        # inside parse_codex_rollout itself, review r2 F3/F5).
        limits = parse_codex_rollout(text.splitlines(), now=now)
    except Exception as exc:  # fail open: any read/parse failure
        return _unknown_report("codex", ["codex rollout parse failed: {}".format(exc)])
    if not limits:
        # Split fail-open reason (review r2 F5 follow-up): a rollout that
        # carried a rate_limits record whose windows all dropped at
        # per-entry validation is a different diagnostic shape from a
        # rollout with no rate_limits record at all.
        if rollout_carries_rate_limits(text.splitlines()):
            return _unknown_report(
                "codex", ["rollout rate_limits record carried no usable windows"]
            )
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
    if binding_limit["reset_at_epoch"] > time.time() + MAX_RESET_HORIZON_SECONDS:
        # Defense in depth (review r1 F2): a direct build_report caller can
        # hand the writer an unclamped limit; never arm the host-global flag
        # with an epoch beyond the clamp horizon. Not arming is the
        # fail-open direction.
        return False
    lines = [
        "runtime={}".format(runtime),
        "reset_at_epoch={}".format(binding_limit["reset_at_epoch"]),
        "reset_at_iso={}".format(binding_limit["reset_at_iso"]),
    ]
    if plan:
        # Review r4 F1: the plan slug is forensic metadata, never trusted
        # key material. parse_flag keeps the LAST occurrence of each key,
        # so a newline-bearing --plan value would inject forged runtime/
        # reset_at_epoch lines into the host-global flag. Keep only the
        # first line (splitlines() also strips a trailing CR) and omit the
        # plan line entirely when nothing remains.
        first_line = plan.splitlines()[0] if plan.splitlines() else ""
        if first_line:
            lines.append("plan={}".format(first_line))
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
            "from the stdout JSON report, not from the exit code. Resets "
            "beyond MAX_RESET_HORIZON_SECONDS ({} days) are clamped to that "
            "horizon at parse time (a clamped binding can still arm the flag "
            "at the clamped epoch); the flag writer additionally refuses any "
            "binding still beyond the horizon.".format(
                MAX_RESET_HORIZON_SECONDS // 86400
            )
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
            # Review r4 F4: the boolean return is deliberately not relayed
            # into reasons here. Every main()-reachable False arm is
            # excluded by construction (both parsers clamp every limit to
            # the horizon before main() sees it, and an empty limit set
            # cannot carry a pause decision); the writer-level horizon
            # check stays as genuine defense in depth for direct callers.
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
