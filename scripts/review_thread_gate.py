#!/usr/bin/env python3
"""Read-only review-thread closure gate over a review-thread marker.

Consumes the marker a passive-review session writes when it begins
processing external PR feedback (duty owned by the receiving-review
skill, ``docs/tmp/review-threads/<session-slug>.json``) and classifies
every tracked thread against an inventory of the PR's review threads.
Exit 0 only on closure: each tracked thread carries a verified agent
reply or an explicit disposition. Exit 1 otherwise, listing every
unclosed thread, one line per thread.

Inventory source, exactly one of:

- ``--inventory PATH``  canned JSON: a file path, or ``-`` to read the
  pipe/stdin. Accepted shapes: the full ``gh api graphql`` envelope
  (``{"data": ...}``), the inner ``{"repository": ...}`` body, a bare
  ``{"reviewThreads": ...}`` object, or a bare list of thread nodes.
- ``--live``            fetch the inventory through ``gh`` (GraphQL,
  reviewThreads). Network access happens ONLY behind this explicit
  flag; tests stay on canned fixtures.

Missing marker file exits 0 with nothing to check: the documented
no-marker non-condition, so a session that never processed external
feedback is unaffected by the gate.

Per-thread classification, in order:

1. explicit disposition recorded on the marker entry (non-empty
   ``disposition``) -> closed;
2. a comment on the tracked thread whose body exactly matches the
   entry's ``reply_body`` -> verified agent reply (already posted; the
   thread is closed and the session must not re-post). A second exact
   match is reported as a duplicate-reply warning on stderr. When the
   entry carries ``parent_id``, the thread's parent comment id must
   match it (attachment verification by stable thread ID plus parent
   metadata); a mismatch fails the thread;
3. otherwise unclosed, split by the parent comment author:
   - human author -> human thread (never auto-resolved; inventory
     resolution alone never closes it);
   - bot author -> automated thread; ``isResolved`` without a reply is
     the witnessed failure shape (resolved without reply).

Marker schema (writer duty: receiving-review; the session identity
staleness match belongs to the done step, not here):
``{"pr": "owner/repo#N", "branch_head": "<sha>", "session_identity":
"<slug>", "threads": [{"id": "<stable thread id>", "parent_id"?,
"disposition"?, "reply_body"?}]}``. The ``pr`` field carries either the canonical ``owner/repo#N`` string, or the session shape, numeric ``pr`` plus ``repo`` (as ``owner/name``) or ``url`` (a GitHub pull-request URL);
``--live`` resolves both behind one pure resolver. The gate is read-only:
it never writes, resolves, or replies to anything.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

GRAPHQL_QUERY = (
    "query($owner:String!,$name:String!,$number:Int!){"
    "repository(owner:$owner,name:$name){"
    "pullRequest(number:$number){"
    "reviewThreads(first:100){nodes{id,isResolved,"
    "comments(first:50){nodes{id,author{login,__typename},body}}}}}}}"
)


def parse_inventory(text: str) -> list[dict]:
    """Parse canned or live gh output into a list of thread nodes.

    Tolerates the full GraphQL envelope and its inner bodies so a
    piped ``--jq`` projection and the raw response use one parser.
    """
    payload = json.loads(text)
    if isinstance(payload, list):
        return [n for n in payload if isinstance(n, dict)]
    if not isinstance(payload, dict):
        raise ValueError("inventory root must be an object or a list")
    node = payload.get("data", payload)
    if not isinstance(node, dict):
        raise ValueError("inventory 'data' is not an object")
    repo = node.get("repository", node)
    pr = repo.get("pullRequest", repo) if isinstance(repo, dict) else None
    threads = pr.get("reviewThreads", pr) if isinstance(pr, dict) else None
    nodes = (
        threads.get("nodes", threads)
        if isinstance(threads, dict)
        else threads
    )
    if not isinstance(nodes, list):
        raise ValueError("cannot locate reviewThreads nodes in inventory")
    return [n for n in nodes if isinstance(n, dict)]


def _comments(node: dict) -> list[dict]:
    comments = node.get("comments") or {}
    nodes = comments.get("nodes") or []
    return [c for c in nodes if isinstance(c, dict)]


def _parent_comment(node: dict) -> dict | None:
    comments = _comments(node)
    return comments[0] if comments else None


def _exact_body_matches(node: dict, body: str) -> list[dict]:
    return [c for c in _comments(node) if c.get("body") == body]


def classify_thread(entry: dict, node: dict | None) -> tuple[bool, str, int]:
    """Classify one tracked thread.

    Returns ``(closed, report_line, exact_body_match_count)``. The
    count exceeds 1 only when the recorded reply body is already
    posted more than once (duplicate-reply detection).
    """
    tid = entry.get("id", "<missing-id>")
    if node is None:
        return False, f"{tid}: tracked thread not found in inventory", 0
    disposition = str(entry.get("disposition") or "").strip()
    if disposition:
        return True, f"{tid}: explicit disposition recorded", 0
    reply_body = entry.get("reply_body")
    if reply_body:
        matches = _exact_body_matches(node, reply_body)
        if matches:
            parent_id = entry.get("parent_id")
            parent = _parent_comment(node)
            if parent_id and (parent is None or parent.get("id") != parent_id):
                line = (
                    f"{tid}: attachment verification failed "
                    "(parent metadata mismatch)"
                )
                return False, line, len(matches)
            return True, f"{tid}: verified agent reply (already posted)", len(matches)
        line = f"{tid}: recorded reply not found on thread (not posted or not visible)"
        return False, line, 0
    resolved = bool(node.get("isResolved"))
    author = (_parent_comment(node) or {}).get("author") or {}
    if author.get("__typename") != "Bot":
        # Missing or non-Bot author reads as human: the conservative arm.
        line = f"{tid}: human thread (never auto-resolved)"
        if resolved:
            line += "; inventory reports resolution without a reply or disposition"
        return False, line, 0
    if resolved:
        return False, f"{tid}: automated thread resolved without reply", 0
    return False, f"{tid}: unanswered automated thread (no verified reply or disposition)", 0


def _resolve_live_target(marker: dict) -> tuple[str, str, int, str]:
    """Resolve the marker's ``pr`` field to (owner, name, number, error).

    Pure: no network access, no process spawns. Accepted shapes,
    first match wins:

    (a) canonical: ``pr`` is a string containing ``#`` whose base
        contains ``/`` and whose number part is all digits;
    (b) session shape with ``repo``: ``pr`` is all digits and ``repo``
        is ``owner/name`` containing exactly one ``/``;
    (c) session shape with ``url``: ``pr`` is all digits and ``url`` is
        a GitHub pull URL whose path after ``github.com/`` is exactly
        ``<owner>/<name>/pull/<digits>`` with non-empty owner and name
        and no extra segments.

    On no match returns a nonempty error message and empty identity
    fields.
    """
    pr = marker.get("pr")

    # (a) canonical owner/repo#N string
    if isinstance(pr, str) and "#" in pr:
        base, _, number = pr.partition("#")
        if "/" in base and number.isdigit() and base:
            owner, _, name = base.partition("/")
            if owner and name:
                return owner, name, int(number), ""
    # (b) numeric pr plus repo
    repo = marker.get("repo")
    if isinstance(pr, int) or (isinstance(pr, str) and pr.isdigit()):
        number = int(pr)
        if isinstance(repo, str) and repo.count("/") == 1:
            owner, _, name = repo.partition("/")
            if owner and name:
                return owner, name, number, ""
        # (c) numeric pr plus GitHub pull URL
        url = marker.get("url")
        if isinstance(url, str) and url.startswith("https://github.com/"):
            path = url[len("https://github.com/"):].strip("/")
            segments = path.split("/")
            if (
                len(segments) == 4
                and segments[2] == "pull"
                and segments[0] and segments[1] and segments[3].isdigit()
            ):
                return segments[0], segments[1], int(segments[3]), ""
    return "", "", 0, f"marker pr {pr!r} is not resolvable to owner/repo#N; cannot fetch live"


def fetch_live(marker: dict) -> str:
    """Fetch the reviewThreads inventory through gh (explicit --live)."""
    owner, name, number, error = _resolve_live_target(marker)
    if error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
    cmd = [
        "gh", "api", "graphql",
        "-f", f"query={GRAPHQL_QUERY}",
        "-f", f"owner={owner}",
        "-f", f"name={name}",
        "-F", f"number={int(number)}",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(
            f"error: gh inventory fetch failed: {proc.stderr.strip()}",
            file=sys.stderr,
        )
        sys.exit(1)
    return proc.stdout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only closure gate over a review-thread marker"
    )
    parser.add_argument(
        "--marker", required=True,
        help="Path to the review-thread marker JSON (missing file exits 0)",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--inventory",
        help="Canned inventory JSON: file path, or - for stdin/pipe",
    )
    source.add_argument(
        "--live", action="store_true",
        help="Fetch the inventory through gh (network; explicit opt-in)",
    )
    args = parser.parse_args(argv)

    marker_path = Path(args.marker)
    if not marker_path.exists():
        print(
            f"review_thread_gate: no review-thread marker at {marker_path}; "
            "nothing to check"
        )
        return 0
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(
            f"error: cannot read review-thread marker {marker_path}: {exc}",
            file=sys.stderr,
        )
        return 1
    if not isinstance(marker, dict):
        print(
            f"error: review-thread marker {marker_path} is not an object",
            file=sys.stderr,
        )
        return 1
    tracked = marker.get("threads")
    if not isinstance(tracked, list):
        print(
            f"error: review-thread marker {marker_path} carries no thread list",
            file=sys.stderr,
        )
        return 1

    if args.live:
        inventory_text = fetch_live(marker)
    elif args.inventory == "-":
        inventory_text = sys.stdin.read()
    else:
        try:
            inventory_text = Path(args.inventory).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"error: cannot read inventory: {exc}", file=sys.stderr)
            return 1
    try:
        nodes = parse_inventory(inventory_text)
    except ValueError as exc:
        print(f"error: cannot parse inventory: {exc}", file=sys.stderr)
        return 1
    by_id = {node.get("id"): node for node in nodes}

    unclosed = 0
    for entry in tracked:
        if not isinstance(entry, dict) or not entry.get("id"):
            print("error: marker thread entry without id", file=sys.stderr)
            unclosed += 1
            continue
        closed, line, dup = classify_thread(entry, by_id.get(entry.get("id")))
        print(line)
        if dup > 1:
            print(
                f"warning: duplicate reply detected on thread {entry.get('id')} "
                f"(exact-body match x{dup}); do not re-post",
                file=sys.stderr,
            )
        if not closed:
            unclosed += 1
    if unclosed:
        print(
            f"review_thread_gate: {unclosed} unclosed thread(s)",
            file=sys.stderr,
        )
        return 1
    print(f"review_thread_gate: all {len(tracked)} tracked thread(s) closed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
