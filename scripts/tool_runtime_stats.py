#!/usr/bin/env python3
"""Tool and script runtime statistics: offline miner over the host session store.

Reads the runtime's local SQLite session database READ-ONLY and aggregates
per-local-day, per-tool wall-clock rows. Emits aggregates only: counts,
durations, tool and script names, token sums. Command strings are read solely
to derive script slugs and are never emitted.

Fail-open contract: a missing store, missing tables, or an empty window produce
a one-line report on stdout and exit 0. Only the pinned absent-data arms are
swallowed; genuine defects still raise.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sqlite3
import subprocess
import sys
import tomllib
from pathlib import Path

DEFAULT_STORE = Path.home() / ".zcode" / "cli" / "db" / "db.sqlite"
DEFAULT_FACTS = Path.home() / ".ai-playbook" / "facts.md"
REPO_FACTS_REL = Path(".ai-playbook") / "facts.md"
REPORT_HOME_NAME = "tool-runtime-stats"

# Terms-pinned store shapes; a drifted column set takes the fail-open arm
PINNED_COLUMNS = {
    "tool_usage": ("tool_name", "status", "started_at", "completed_at", "duration_ms", "tool_call_id"),
    "turn_usage": ("session_id", "turn_id", "tool_call_count", "input_tokens", "output_tokens", "computed_total_tokens"),
    "part": ("id", "message_id", "session_id", "data"),
}

# filing threshold: total >= 300 s/day, or mean >= 10 s at >= 50 calls/day.
# Under total = count x mean the second arm is strictly subsumed by the first;
# both arms are implemented as written so the contract stays faithful.
FILING_TOTAL_SECONDS = 300.0
FILING_MEAN_SECONDS = 10.0
FILING_MIN_CALLS = 50
ERROR_RANKING_MIN_CALLS = 50
JUDGMENT_FREE_MIN_RATIO = 0.8
DEFAULT_TOP_N = 5
RETENTION_KEEP = 8


# ---------------------------------------------------------------------------
# facts resolution


def load_facts(facts_path: Path) -> dict:
    """Parse the opening TOML fence of the gitignored facts document.

    A missing file resolves to no facts (the miner falls back to defaults).
    A malformed TOML block is a genuine configuration defect and raises:
    the plan's fail-open arms cover absent data only, never a wrong store.
    """
    try:
        text = facts_path.read_text(encoding="utf-8")
    except OSError:
        return {}
    match = re.search(r"```toml\s*\n(.*?)```", text, re.DOTALL)
    if not match:
        return {}
    return tomllib.loads(match.group(1))


def resolve_store_path(args: argparse.Namespace, facts: dict) -> Path:
    """--store override wins; then the facts key; then the adapter default."""
    if getattr(args, "store", None):
        return Path(args.store).expanduser()
    from_facts = facts.get("session_store_path")
    if from_facts:
        return Path(str(from_facts)).expanduser()
    return DEFAULT_STORE


def resolve_facts_path(args: argparse.Namespace) -> Path:
    if getattr(args, "facts", None):
        return Path(args.facts).expanduser()
    repo_candidate = Path(__file__).resolve().parent.parent / REPO_FACTS_REL
    if repo_candidate.exists():
        return repo_candidate
    return DEFAULT_FACTS


def resolve_out_root(args: argparse.Namespace, facts: dict) -> Path:
    if getattr(args, "out_root", None):
        return Path(args.out_root).expanduser()
    tmp_dir = facts.get("tmp_dir")
    if tmp_dir:
        return Path(str(tmp_dir)).expanduser()
    return Path("docs") / "tmp"


def resolve_repo_root(args: argparse.Namespace) -> Path:
    if getattr(args, "repo_root", None):
        return Path(args.repo_root).expanduser().resolve()
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        ).stdout.strip()
        if out:
            return Path(out).resolve()
    except OSError:
        pass
    return Path.cwd().resolve()


# ---------------------------------------------------------------------------
# store access (read-only)


def connect_read_only(store: Path) -> sqlite3.Connection:
    uri = f"file:{store}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


class SchemaDriftError(Exception):
    """A present table lacks a Terms-pinned column (genuine defect: raises)."""


def require_tables(conn: sqlite3.Connection, tables: tuple[str, ...], columns: dict[str, tuple[str, ...]] | None = None) -> None:
    """Absent tables raise StoreShapeError (the pinned fail-open arm).

    A present table missing a pinned column raises SchemaDriftError: the plan
    distinguishes a drifted schema (load-bearing, must not be silently
    swallowed) from the absent-data arms.
    """
    missing = [t for t in tables if not table_exists(conn, t)]
    if missing:
        raise StoreShapeError(f"missing tables: {', '.join(missing)}")
    for table, needed in (columns or {}).items():
        if not table_exists(conn, table):
            continue
        present = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        absent = [name for name in needed if name not in present]
        if absent:
            raise SchemaDriftError(f"missing columns in {table}: {', '.join(absent)}")


class StoreShapeError(Exception):
    """The store lacks a table this miner reads (fail-open arm)."""


# ---------------------------------------------------------------------------
# bash script attribution (repo-anchored)


RUNTIME_PLAYBOOK_PREFIX = (Path.home() / ".ai-playbook").resolve()


def _sanctioned_prefixes(repo_root: Path) -> tuple[Path, ...]:
    prefixes = [repo_root.resolve()]
    try:
        prefixes.append(RUNTIME_PLAYBOOK_PREFIX)
    except OSError:
        pass
    return tuple(prefixes)


_TOKEN_EDGE_CHARS = ";},\"')]&"
# a slugable basename carries an extension and no shell or regex metacharacters,
# so grep/sed/find pattern arguments never become script names
_SLUG_METACHARS = set('*?[](|){}$~^!,;=')

def _clean_token(token: str) -> str:
    """Strip redirection prefixes and shell punctuation glued to a token."""
    if ">" in token:
        token = token.rsplit(">", 1)[-1]
    elif "<" in token:
        token = token.rsplit("<", 1)[-1]
    return token.strip(_TOKEN_EDGE_CHARS)


def _token_script_slug(token: str, prefixes: tuple[Path, ...]) -> str | None:
    """Return the script basename when the token is a path under a prefix.

    The resolved file must exist under the prefix: a relative command from a
    foreign project must never attribute to this repo merely because its
    relative shape would fit (repo-anchor invariant).
    """
    token = _clean_token(token)
    if "/" not in token or not token:
        return None
    basename = token.rsplit("/", 1)[-1]
    if "." not in basename or any(ch in basename for ch in _SLUG_METACHARS):
        return None
    expanded = Path(os.path.expandvars(os.path.expanduser(str(token))))
    tries = [expanded] if expanded.is_absolute() else [prefix / expanded for prefix in prefixes]
    for try_path in tries:
        try:
            resolved = try_path.resolve()
        except OSError:
            continue
        if any(resolved.is_relative_to(prefix) for prefix in prefixes) and resolved.is_file():
            return resolved.name
    return None


def bash_command_slugs(conn: sqlite3.Connection, prefixes: tuple[Path, ...]) -> tuple[dict[str, str], int]:
    """Map tool_usage.id to a script slug for Bash rows; count degradations.

    The command string is read from the joined tool-call part solely to derive
    the slug and is never emitted. Bash rows with no matching part row degrade
    to the other bucket; the caller reports the degradation count. Malformed
    part JSON makes the store unreadable for this query and raises: only the
    pinned absent-data arms are swallowed, and the rider's fail-open wrapping
    reports the error without failing the maintenance turn.
    """
    rows = conn.execute(
        "SELECT tu.id, p.data FROM tool_usage tu LEFT JOIN part p"
        " ON p.session_id = tu.session_id"
        " AND json_extract(p.data, '$.type') = 'tool'"
        " AND json_extract(p.data, '$.callID') = tu.tool_call_id"
        " WHERE tu.tool_name = 'Bash'"
    ).fetchall()
    slugs: dict[str, str] = {}
    degraded = 0
    for row_id, part_data in rows:
        command = None
        if part_data:
            try:
                state = json.loads(part_data).get("state") or {}
                command = (state.get("input") or {}).get("command")
            except (ValueError, AttributeError):
                command = None
        slug = None
        if command:
            for token in str(command).split():
                slug = _token_script_slug(token, prefixes)
                if slug:
                    break
        if slug:
            slugs[row_id] = slug
        else:
            slugs[row_id] = "other"
            if command is None:
                degraded += 1
    return slugs, degraded


# ---------------------------------------------------------------------------
# collection


def local_date_from_ms(epoch_ms: int) -> str:
    return datetime.datetime.fromtimestamp(epoch_ms / 1000).date().isoformat()


def _p95_nearest_rank(sorted_values: list[float]) -> float:
    if not sorted_values:
        return 0.0
    import math

    rank = max(1, math.ceil(0.95 * len(sorted_values)))
    return sorted_values[rank - 1]


def collect_day_summaries(conn: sqlite3.Connection, report_dates: set[str] | None = None) -> list[dict]:
    """Per-day token summaries over turns that joined at least one tool row.

    A turn's tokens are allocated evenly across its joined tool rows for the
    per-tool rows; the day summary carries the turn-level sums. Days that
    have tool rows but no joined turns emit a zero summary (the plan pins a
    zero share, not an absent row); days with no tool rows at all produce no
    summary.
    """
    require_tables(conn, ("turn_usage",))
    joined_counts = {
        (session_id, turn_id): count
        for session_id, turn_id, count in conn.execute(
            "SELECT session_id, turn_id, COUNT(*) FROM tool_usage"
            " WHERE session_id IS NOT NULL AND turn_id IS NOT NULL"
            " GROUP BY session_id, turn_id"
        )
    }
    days: dict[str, dict] = {
        date: {"tokens_in": 0, "tokens_out": 0, "total": 0, "single": 0}
        for date in (report_dates or ())
    }
    turns = conn.execute(
        "SELECT session_id, turn_id, started_at, input_tokens, output_tokens FROM turn_usage"
    ).fetchall()
    for session_id, turn_id, started_at, input_tokens, output_tokens in turns:
        if started_at is None:
            continue
        joined = joined_counts.get((session_id, turn_id), 0)
        if not joined:
            continue
        date = local_date_from_ms(started_at)
        day = days.setdefault(date, {"tokens_in": 0, "tokens_out": 0, "total": 0, "single": 0})
        tokens_in = input_tokens or 0
        tokens_out = output_tokens or 0
        day["tokens_in"] += tokens_in
        day["tokens_out"] += tokens_out
        day["total"] += tokens_in + tokens_out
        if joined == 1:
            day["single"] += tokens_in + tokens_out
    summaries = []
    for date in sorted(days):
        day = days[date]
        share = day["single"] / day["total"] if day["total"] else 0.0
        summaries.append(
            {
                "date": date,
                "tokens_in": day["tokens_in"],
                "tokens_out": day["tokens_out"],
                "est_no_judgment_token_share": round(share, 4),
            }
        )
    return summaries


def collect_day_rows(conn: sqlite3.Connection, repo_root: Path) -> tuple[list[dict], int]:
    """Aggregate tool_usage into one row per (local date, tool, script slug).

    Durations come from the store column when positive; otherwise from the
    completed_at - started_at wall-clock delta when both bounds exist. Bash
    rows carry an attributed slug (sanctioned script basename or the other
    bucket); non-Bash rows carry a null slug. Turn tokens are allocated
    evenly across each turn's joined tool rows; the share of a row's calls
    inside single-row turns feeds the judgment-free predicate.
    """
    require_tables(conn, ("part", "turn_usage"))
    prefixes = _sanctioned_prefixes(repo_root)
    slugs, degraded = bash_command_slugs(conn, prefixes)
    turn_tokens: dict[tuple[str, str], tuple[int, int]] = {}
    for session_id, turn_id, input_tokens, output_tokens in conn.execute(
        "SELECT session_id, turn_id, input_tokens, output_tokens FROM turn_usage"
    ):
        if session_id is None or turn_id is None:
            continue
        turn_tokens[(session_id, turn_id)] = (input_tokens or 0, output_tokens or 0)
    joined_counts = {
        (session_id, turn_id): count
        for session_id, turn_id, count in conn.execute(
            "SELECT session_id, turn_id, COUNT(*) FROM tool_usage"
            " WHERE session_id IS NOT NULL AND turn_id IS NOT NULL"
            " GROUP BY session_id, turn_id"
        )
    }
    rows = conn.execute(
        "SELECT id, session_id, turn_id, started_at, completed_at, duration_ms,"
        " tool_name, status FROM tool_usage"
    ).fetchall()
    buckets: dict[tuple[str, str, str | None], dict] = {}
    for row_id, session_id, turn_id, started_at, completed_at, duration_ms, tool_name, status in rows:
        if started_at is None:
            continue
        date = local_date_from_ms(started_at)
        tool_name = tool_name or "unknown"
        if tool_name == "Bash":
            slug = slugs.get(row_id, "other")
        else:
            slug = None
        key = (date, tool_name, slug)
        bucket = buckets.setdefault(
            key, {"calls": 0, "errors": 0, "durations_ms": [], "tokens": 0.0, "single_calls": 0}
        )
        bucket["calls"] += 1
        if status == "error":
            bucket["errors"] += 1
        joined = joined_counts.get((session_id, turn_id), 0) if session_id and turn_id else 0
        if joined:
            tokens_in, tokens_out = turn_tokens.get((session_id, turn_id), (0, 0))
            bucket["tokens"] += (tokens_in + tokens_out) / joined
        if joined == 1:
            bucket["single_calls"] += 1
        if duration_ms is not None and duration_ms > 0:
            resolved = duration_ms
        elif completed_at is not None and completed_at >= started_at:
            resolved = completed_at - started_at
        else:
            resolved = None
        if resolved is not None:
            bucket["durations_ms"].append(resolved)

    day_rows: list[dict] = []
    for key in sorted(buckets, key=lambda k: (k[0], k[1], k[2] or "")):
        date, tool, slug = key
        bucket = buckets[key]
        durations = bucket["durations_ms"]
        total_s = sum(durations) / 1000 if durations else 0.0
        mean_s = total_s / len(durations) if durations else 0.0
        p95_s = _p95_nearest_rank(sorted(d / 1000 for d in durations)) if durations else 0.0
        day_rows.append(
            {
                "date": date,
                "tool": tool,
                "calls": bucket["calls"],
                "errors": bucket["errors"],
                "mean_seconds": round(mean_s, 3),
                "p95_seconds": round(p95_s, 3),
                "total_seconds": round(total_s, 3),
                "script_slug": slug,
                # unrounded float: even allocation stays reconciliation-exact
                # at full precision; rounding here would lose remainders
                "tokens": bucket["tokens"],
                "single_calls": bucket["single_calls"],
                "trend_total_seconds_delta": None,
            }
        )
    return day_rows, degraded


# ---------------------------------------------------------------------------
# ranking report: time, tokens, errors, scriptable candidates, trend


def _row_label(tool: str, slug: str | None) -> str:
    return f"{tool}/{slug}" if slug else tool


def _slug_suffix(slug: str | None) -> str:
    return f" script_slug={slug}" if slug else ""


def window_rows(day_rows: list[dict]) -> tuple[dict, int]:
    """Aggregate per-day rows into one entry per (tool, script slug)."""
    days_count = max(1, len({row["date"] for row in day_rows}))
    window: dict[tuple[str, str | None], dict] = {}
    for row in day_rows:
        key = (row["tool"], row["script_slug"])
        entry = window.setdefault(
            key,
            {"calls": 0, "errors": 0, "seconds": 0.0, "tokens": 0.0,
             "single_calls": 0, "day_rows": [], "days": set()},
        )
        entry["calls"] += row["calls"]
        entry["errors"] += row["errors"]
        entry["seconds"] += row["total_seconds"]
        entry["tokens"] += row["tokens"]
        entry["single_calls"] += row["single_calls"]
        entry["day_rows"].append(row)
        entry["days"].add(row["date"])
    return window, days_count


def _predicates(tool: str, entry: dict, days_count: int) -> dict:
    """Mechanical scriptable predicates for one window row.

    deterministic: attributed script slug, or a non-Bash runtime tool whose
    invocation shape is fixed by the tool schema itself; free-form commands
    (the other bucket) are never deterministic.
    frequent: calls/day at or above the 50-call floor.
    judgment-free: at least 80 percent of the row's calls ran alone in their
    turn (single joined tool row).
    threshold: any single day at or above the filing threshold.
    """
    slug = entry.get("slug")
    deterministic = (tool != "Bash") or (slug not in (None, "other"))
    # calls/day on the entry's own active days, consistent with the per-day
    # ranking basis (R6-4): a row measured on few days is judged on those days
    frequent = entry["calls"] / max(1, len(entry["days"])) >= FILING_MIN_CALLS
    judgment_free = entry["calls"] > 0 and (
        entry["single_calls"] / entry["calls"] >= JUDGMENT_FREE_MIN_RATIO
    )
    threshold = any(
        day["total_seconds"] >= FILING_TOTAL_SECONDS
        or (day["mean_seconds"] >= FILING_MEAN_SECONDS and day["calls"] >= FILING_MIN_CALLS)
        for day in entry["day_rows"]
    )
    return {
        "deterministic": deterministic,
        "frequent": frequent,
        "judgment_free": judgment_free,
        "threshold": threshold,
    }


def _replacement_shape(tool: str, slug: str | None, mean_seconds: float) -> str:
    """Mechanical disposition across the plan's four replacement shapes.

    Attributed script rows become direct script invocations; unattributed
    Bash volume is skipped (free-form commands are not mechanically
    replaceable); expensive fixed-schema tool calls batch; cheap fixed-schema
    tool calls cache.
    """
    if slug and slug != "other":
        return "script"
    if tool != "Bash":
        return "batch" if mean_seconds >= FILING_MEAN_SECONDS else "cache"
    return "skip"


def build_rankings(day_rows: list[dict], top_n: int) -> dict:
    window, days_count = window_rows(day_rows)
    ranked = []
    for (tool, slug), entry in window.items():
        entry = dict(entry)
        entry["tool"] = tool
        entry["slug"] = slug
        entry["predicates"] = _predicates(tool, entry, days_count)
        entry["scriptable"] = all(
            entry["predicates"][name]
            for name in ("deterministic", "frequent", "judgment_free")
        )
        ranked.append(entry)

    # per-day rates use each entry's own active days: a row present on many
    # days must not outrank a costlier row present on few
    for entry in ranked:
        entry["active_days"] = max(1, len(entry["days"]))
        entry["seconds_per_day"] = entry["seconds"] / entry["active_days"]
        entry["tokens_per_day"] = entry["tokens"] / entry["active_days"]
    by_time = sorted(ranked, key=lambda e: e["seconds_per_day"], reverse=True)[:top_n]
    by_tokens = sorted(ranked, key=lambda e: e["tokens_per_day"], reverse=True)[:top_n]
    error_eligible = [e for e in ranked if e["calls"] >= ERROR_RANKING_MIN_CALLS]
    by_errors = sorted(
        error_eligible,
        key=lambda e: (e["errors"] / e["calls"] if e["calls"] else 0.0),
        reverse=True,
    )[:top_n]
    candidates = [e for e in ranked if e["scriptable"]]
    candidates.sort(key=lambda e: e["seconds"], reverse=True)
    return {
        "window": window,
        "days_count": days_count,
        "by_time": by_time,
        "by_tokens": by_tokens,
        "by_errors": by_errors,
        "candidates": candidates,
    }


def load_prior_report(out_root: Path) -> tuple[dict | None, str | None]:
    """Newest prior run in the report home (lexicographically greatest name)."""
    out_dir = out_root / REPORT_HOME_NAME
    if not out_dir.is_dir():
        return None, None
    json_files = sorted(p for p in out_dir.iterdir() if p.name.endswith(".json") and p.is_file())
    if not json_files:
        return None, None
    newest = json_files[-1]
    try:
        return json.loads(newest.read_text(encoding="utf-8")), newest.name
    except (ValueError, OSError):
        return None, None


def _apply_trend(day_rows: list[dict], prior: dict | None) -> None:
    """Per-day delta against the prior report's same (date, tool, slug) row."""
    if not prior:
        return
    prior_map = {
        (row["date"], row["tool"], row["script_slug"]): row["total_seconds"]
        for row in prior.get("days", [])
    }
    for row in day_rows:
        key = (row["date"], row["tool"], row["script_slug"])
        if key in prior_map:
            row["trend_total_seconds_delta"] = round(row["total_seconds"] - prior_map[key], 3)


def _render_trend(rankings: dict, prior_name: str | None) -> list[str]:
    lines: list[str] = ["## Weekly trend", ""]
    if prior_name is None:
        lines.append("no prior report in the report home; baseline starts with this run")
        return lines
    # comparable deltas: per-day totals summed over the dates BOTH reports
    # carry, so a growing full-history window cannot fake an improvement
    added = 0
    for entry in rankings["by_time"]:
        key = (entry["tool"], entry["slug"])
        prior_days = rankings.get("prior_per_day", {}).get(key, {})
        current_days = {row["date"]: row["total_seconds"] for row in entry["day_rows"]}
        common = sorted(set(prior_days) & set(current_days))
        if not common:
            continue
        current = sum(current_days[date] for date in common)
        prior = sum(prior_days[date] for date in common)
        delta = current - prior
        lines.append(
            f"- {_row_label(entry['tool'], entry['slug'])}:{_slug_suffix(entry['slug'])}"
            f" total {entry['seconds']:.1f} s in window (delta {delta:+.1f} s over"
            f" {len(common)} common day(s) vs run {prior_name})"
        )
        added += 1
    if not added:
        lines.append(f"no comparable rows against prior run {prior_name}")
    return lines


def _render_digest(report: dict, stamp: str, rankings: dict, prior_name: str | None) -> str:
    """Aggregates-only Markdown digest for one run, assembled per section."""
    lines = [f"# Tool runtime stats run {stamp}", ""]
    lines.append(
        "retention: this folder keeps the newest 8 runs; older run-stamped"
        " artifacts are pruned automatically on each run."
    )
    lines.append("")
    lines.extend(_render_day_table(report))
    lines.extend(_render_time_ranking(rankings))
    lines.extend(_render_token_ranking(rankings))
    lines.extend(_render_error_ranking(rankings))
    lines.extend(_render_candidates(rankings))
    lines.extend(_render_token_summaries(report))
    lines.extend(_render_trend(rankings, prior_name))
    lines.append("")
    return "\n".join(lines)


def _render_day_table(report: dict) -> list[str]:
    lines = ["## Per-day tool rows", ""]
    lines.append("| date | tool | script_slug | calls | errors | mean_s | p95_s | total_s |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|")
    for row in report["days"]:
        lines.append(
            "| {date} | {tool} | {slug} | {calls} | {errors} | {mean} | {p95} | {total} |".format(
                date=row["date"], tool=row["tool"], slug=row["script_slug"] or "",
                calls=row["calls"], errors=row["errors"], mean=row["mean_seconds"],
                p95=row["p95_seconds"], total=row["total_seconds"],
            )
        )
    lines.append("")
    return lines


def _render_time_ranking(rankings: dict) -> list[str]:
    lines = [
        f"## Time ranking (top {len(rankings['by_time'])} by total seconds per active day,"
        f" {rankings['days_count']} day(s) in window)",
        "",
    ]
    for i, entry in enumerate(rankings["by_time"], 1):
        rate = entry["errors"] / entry["calls"] * 100 if entry["calls"] else 0.0
        lines.append(
            "{i}. {label}{slug} total={total} s (calls={calls}, calls/day={per_day:.1f},"
            " s/day={spd:.1f} over {days} active day(s),"
            " error rate {rate:.1f} percent; scriptable candidate: {verdict})".format(
                i=i, label=_row_label(entry["tool"], entry["slug"]),
                slug=_slug_suffix(entry["slug"]), total=int(round(entry["seconds"])),
                calls=entry["calls"], per_day=entry["calls"] / rankings["days_count"],
                spd=entry["seconds_per_day"], days=entry["active_days"],
                rate=rate, verdict=_candidate_verdict(entry),
            )
        )
    lines.append("")
    return lines


def _render_token_ranking(rankings: dict) -> list[str]:
    lines = [f"## Token ranking (top {len(rankings['by_tokens'])} by tokens in window)", ""]
    for i, entry in enumerate(rankings["by_tokens"], 1):
        lines.append(
            "{i}. {label}{slug} tokens={tokens} (estimated no-judgment share sourced from"
            " day summaries)".format(
                i=i, label=_row_label(entry["tool"], entry["slug"]),
                slug=_slug_suffix(entry["slug"]), tokens=int(round(entry["tokens"])),
            )
        )
    lines.append("")
    return lines


def _render_error_ranking(rankings: dict) -> list[str]:
    lines = [f"## Error ranking (calls >= {ERROR_RANKING_MIN_CALLS} in window)", ""]
    if not rankings["by_errors"]:
        lines.append(f"no row reached the {ERROR_RANKING_MIN_CALLS}-call floor")
        lines.append("")
        return lines
    for i, entry in enumerate(rankings["by_errors"], 1):
        rate = entry["errors"] / entry["calls"] * 100 if entry["calls"] else 0.0
        lines.append(
            "{i}. {label}{slug} calls={calls} errors={errors} error rate={rate:.1f} percent".format(
                i=i, label=_row_label(entry["tool"], entry["slug"]),
                slug=_slug_suffix(entry["slug"]), calls=entry["calls"],
                errors=entry["errors"], rate=rate,
            )
        )
    lines.append("")
    return lines


def _render_candidates(rankings: dict) -> list[str]:
    lines = ["## Scriptable candidates", ""]
    filed = [e for e in rankings["candidates"] if e["predicates"]["threshold"]]
    if not filed:
        lines.append(
            "no candidate cleared the filing threshold"
            f" (total >= {FILING_TOTAL_SECONDS:.0f} s/day, or mean >= {FILING_MEAN_SECONDS:.0f} s"
            f" at >= {FILING_MIN_CALLS} calls/day)"
        )
    for entry in rankings["candidates"]:
        predicate = entry["predicates"]
        lines.append(
            "- {label}{slug}: measured cost {cost} s in window; replacement shape: {shape};"
            " estimated saving: {saving} s/window; filed: {filed}".format(
                label=_row_label(entry["tool"], entry["slug"]),
                slug=_slug_suffix(entry["slug"]),
                cost=f"{entry['seconds']:.1f}",
                shape=_replacement_shape(
                    entry["tool"], entry["slug"],
                    entry["seconds"] / entry["calls"] if entry["calls"] else 0.0,
                ),
                saving=f"{entry['seconds']:.1f}",
                filed="yes" if predicate["threshold"] else "no (below threshold)",
            )
        )
    lines.append("")
    return lines


def _render_token_summaries(report: dict) -> list[str]:
    lines = ["## Day token summaries", ""]
    if not report["day_summaries"]:
        lines.append("no joined turns; no token summaries")
        lines.append("")
        return lines
    lines.append("| date | tokens_in | tokens_out | est_no_judgment_token_share |")
    lines.append("|---|---:|---:|---:|")
    for summary in report["day_summaries"]:
        lines.append(
            "| {date} | {tin} | {tout} | {share} |".format(
                date=summary["date"], tin=summary["tokens_in"],
                tout=summary["tokens_out"],
                share=summary["est_no_judgment_token_share"],
            )
        )
    lines.append("")
    return lines


def _candidate_verdict(entry: dict) -> str:
    if entry["scriptable"] and entry["predicates"]["threshold"]:
        return "yes (filed)"
    if not entry["predicates"]["deterministic"]:
        return "no (unattributed free-form command)"
    if not entry["predicates"]["judgment_free"]:
        return "no (judgment required)"
    if not entry["predicates"]["frequent"]:
        return "no (below the call floor)"
    return "no (below threshold)"


# ---------------------------------------------------------------------------
# report


def _run_stamp(out_dir: Path) -> str:
    """Local run stamp, lexicographically sortable; bump seconds on collision."""
    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    while (
        (out_dir / f"{REPORT_HOME_NAME}-{stamp}.json").exists()
        or (out_dir / f"{REPORT_HOME_NAME}-{stamp}.md").exists()
    ):
        stamp = (datetime.datetime.strptime(stamp, "%Y%m%dT%H%M%S") + datetime.timedelta(seconds=1)).strftime("%Y%m%dT%H%M%S")
    return stamp


def write_artifacts(report: dict, render_digest, out_root: Path) -> Path:
    """Write the stamped JSON table and Markdown digest; prune to newest 8.

    render_digest is a callable (stamp -> digest text) so a stamp collision
    with a concurrent rider re-renders the header under the bumped stamp.
    Both files are created exclusively (O_CREAT|O_EXCL), so same-second
    concurrent runs never overwrite each other's artifacts.
    """
    out_dir = out_root / REPORT_HOME_NAME
    out_dir.mkdir(parents=True, exist_ok=True)
    while True:
        stamp = _run_stamp(out_dir)
        json_path = out_dir / f"{REPORT_HOME_NAME}-{stamp}.json"
        md_path = out_dir / f"{REPORT_HOME_NAME}-{stamp}.md"
        # the digest is written first and the JSON table last: the JSON is the
        # run's completion marker, so a crash mid-write never leaves a partial
        # run that load_prior_report or retention would treat as complete
        try:
            fd_md = os.open(md_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            continue
        try:
            with os.fdopen(fd_md, "w", encoding="utf-8") as stream:
                stream.write(render_digest(stamp))
            try:
                fd = os.open(json_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                md_path.unlink(missing_ok=True)
                continue
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as stream:
                    stream.write(json.dumps(report, indent=2))
            except OSError:
                json_path.unlink(missing_ok=True)
                raise
        except OSError:
            md_path.unlink(missing_ok=True)
            raise
        _apply_retention(out_dir, keep=RETENTION_KEEP)
        return json_path


def _apply_retention(out_dir: Path, keep: int) -> None:
    """Keep-newest pruning: resolve runs by lexicographic run-stamped filename.

    A run is a JSON table (the authoritative artifact); its Markdown digest is
    pruned with it, and orphan digests whose JSON is gone are pruned too. The
    only exemption from keep-newest-eight is a fresh PARTIAL pair (one file
    missing): that is a concurrent rider mid-write, and pruning it would split
    the pair. Complete pairs are always pruned on the contract.
    """
    import time

    fresh_cutoff = time.time() - 600
    files_by_stamp: dict[str, list[Path]] = {}
    for path in out_dir.iterdir():
        name = path.name
        prefix = f"{REPORT_HOME_NAME}-"
        if path.is_file() and name.startswith(prefix) and (
            name.endswith(".json") or name.endswith(".md")
        ):
            stamp = name[len(prefix):].rsplit(".", 1)[0]
            files_by_stamp.setdefault(stamp, []).append(path)
    json_stamps = {
        stamp for stamp, paths in files_by_stamp.items() if any(p.suffix == ".json" for p in paths)
    }
    ordered = sorted(json_stamps)
    prune = set(ordered[:-keep] if len(ordered) > keep else [])
    # orphan digests whose JSON table is gone are always pruned
    prune |= set(files_by_stamp) - json_stamps
    for stamp in prune:
        paths = files_by_stamp[stamp]
        complete = any(p.suffix == ".json" for p in paths) and any(p.suffix == ".md" for p in paths)
        if not complete and any(p.stat().st_mtime > fresh_cutoff for p in paths):
            continue  # a concurrent rider is mid-write on this partial pair
        for path in paths:
            path.unlink(missing_ok=True)


def run_collection(args: argparse.Namespace) -> int:
    facts = load_facts(resolve_facts_path(args))
    store = resolve_store_path(args, facts)
    out_root = resolve_out_root(args, facts)
    repo_root = resolve_repo_root(args)

    if not store.exists():
        print(f"tool runtime stats: no session store at {store}; nothing collected")
        return 0
    conn = connect_read_only(store)
    try:
        require_tables(conn, ("tool_usage", "turn_usage", "part"), columns=PINNED_COLUMNS)
        day_rows, degraded = collect_day_rows(conn, repo_root)
        day_summaries = collect_day_summaries(conn, report_dates={row["date"] for row in day_rows})
    except StoreShapeError as exc:
        print(f"tool runtime stats: store at {store} is not a session store ({exc}); nothing collected")
        return 0
    finally:
        conn.close()
    if not day_rows:
        print(f"tool runtime stats: no tool rows in store at {store}; nothing collected")
        return 0
    if degraded:
        print(
            f"tool runtime stats: {degraded} bash rows had no matching part row;"
            " degraded to the other bucket",
            file=sys.stderr,
        )

    report = {"days": day_rows, "day_summaries": day_summaries}
    prior, prior_name = load_prior_report(out_root)
    _apply_trend(day_rows, prior)
    rankings = build_rankings(day_rows, top_n=args.top)
    rankings["prior_per_day"] = {}
    if prior:
        for row in prior.get("days", []):
            key = (row["tool"], row["script_slug"])
            rankings["prior_per_day"].setdefault(key, {})[row["date"]] = row["total_seconds"]

    def render(stamp: str) -> str:
        return _render_digest(report, stamp=stamp, rankings=rankings, prior_name=prior_name)

    write_artifacts(report, render, out_root)
    print(json.dumps(report, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--store", default=None, help="session store path override")
    common.add_argument("--facts", default=None, help="facts document path override")
    common.add_argument("--out-root", default=None, dest="out_root", help="output root override")
    common.add_argument("--repo-root", default=None, dest="repo_root", help="repo root override")
    common.add_argument("--top", type=int, default=DEFAULT_TOP_N, help="top-N ranking size")
    parser = argparse.ArgumentParser(prog="tool_runtime_stats", description=__doc__, parents=[common])
    sub = parser.add_subparsers(dest="command", required=False)
    parser.set_defaults(command="run")
    run = sub.add_parser("run", parents=[common], help="collect and report in one pass (default)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_collection(args)


if __name__ == "__main__":
    sys.exit(main())
