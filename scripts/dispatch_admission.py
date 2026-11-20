#!/usr/bin/env python3
"""Target-disjointness dispatch admission (plan
2026-11-04-parallel-execution-landing-serialization-blockers, Task 1).

The dispatch admission check a maintenance deciding turn runs before
creating a child: compute the candidate's owned-path set (the repository
paths the run claims as its own edit surface) and test intersection
against each outstanding run's recorded owned-path set. A disjoint
candidate is admitted; an intersecting outstanding run refuses the
dispatch naming both runs and the intersecting paths. Degenerate inputs
hold conservatively: an outstanding run with an empty recorded owned-path
set, or one with no done-setup manifest from which to derive owned paths,
is treated as intersecting with the reason named.

Candidate owned-path sources (first given wins the union):
  --owned-path PATH          explicit path, repeatable
  --candidate-manifest PATH  a done-setup run manifest (the union of its
                             owned_paths, owned_plan_paths, and
                             owned_review_paths list fields)
  --plan PATH                derive pre-run from the covering plan's
                             `Files:` lists (backticked repo paths)

Outstanding-run inputs, repeatable and order-preserving: the runs reach
check_admission in the interleaved argv order of the two options (the
first blocker decides, so order is verdict-relevant):
  --outstanding-with-manifest ID PATH     a recorded run and its
                                          done-setup manifest
  --outstanding-without-manifest ID       a recorded run carrying no
                                          done-setup manifest (the
                                          missing-source conservative
                                          case)

Outcome contract (scripts/OUTCOME_CONTRACT.md): exit 0 with a final
`OUTCOME: pass` line admits the dispatch; exit 1 with `OUTCOME: fail`
refuses it (intersection or a conservative verdict, the offending
evidence named); exit 3 with `OUTCOME: tool_error` covers missing or
unparseable inputs and usage violations (argparse usage errors are
routed through the ToolError path by the parser's error override, so
they exit 3 with the OUTCOME line instead of argparse's bare exit 2
with none). No indeterminate outcome is modeled: every observed input
either parses or is a tool error.
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from typing import List, Optional

PROG = "dispatch_admission"


@dataclass
class Candidate:
    """The dispatch candidate: a run id plus its owned-path set."""
    run_id: str
    owned_paths: List[str]


@dataclass
class OutstandingRun:
    """A recorded outstanding run. ``owned_paths`` is None when the run
    carries no done-setup manifest from which to derive owned paths (the
    missing-source conservative case); an empty list is a manifest that
    records an empty owned-path set (the empty-set conservative case)."""
    run_id: str
    owned_paths: Optional[List[str]]
    source: str = ""


@dataclass
class AdmissionVerdict:
    """One admission verdict: admit, or refuse with the blocking run and
    the intersecting paths named."""
    admitted: bool
    reason: str
    blocking_run_id: Optional[str] = None
    intersecting_paths: List[str] = field(default_factory=list)


def check_admission(candidate: Candidate,
                    outstanding_runs: List[OutstandingRun]) -> AdmissionVerdict:
    """Test the candidate's owned-path set against each outstanding run's
    recorded set in argument order; the first blocker decides. A run with
    no manifest source or an empty recorded set takes the conservative
    verdict (treated as intersecting) with the reason named."""
    candidate_set = set(candidate.owned_paths)
    for run in outstanding_runs:
        if run.owned_paths is None:
            return AdmissionVerdict(
                admitted=False,
                reason=("outstanding run %s carries no done-setup manifest "
                        "from which to derive owned paths; treated as "
                        "intersecting (conservative verdict)" % run.run_id),
                blocking_run_id=run.run_id,
            )
        if not run.owned_paths:
            return AdmissionVerdict(
                admitted=False,
                reason=("outstanding run %s records an empty owned-path "
                        "set; treated as intersecting (conservative "
                        "verdict)" % run.run_id),
                blocking_run_id=run.run_id,
            )
        intersecting = sorted(candidate_set.intersection(run.owned_paths))
        if intersecting:
            return AdmissionVerdict(
                admitted=False,
                reason=("candidate owned paths intersect outstanding run "
                        "%s" % run.run_id),
                blocking_run_id=run.run_id,
                intersecting_paths=intersecting,
            )
    return AdmissionVerdict(
        admitted=True,
        reason=("candidate owned paths are disjoint from every "
                "outstanding run's recorded owned-path set"),
    )


def owned_paths_from_manifest(path: str) -> List[str]:
    """Read a done-setup run manifest and return the union of its owned
    path list fields. An unreadable or unparseable manifest is a tool
    error (the check cannot run reliably over a missing input)."""
    try:
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError) as exc:
        raise ToolError("outstanding manifest %s is unreadable or "
                        "unparseable: %s" % (path, exc))
    if not isinstance(payload, dict):
        raise ToolError("outstanding manifest %s is not a JSON object" % path)
    paths: List[str] = []
    for key in ("owned_paths", "owned_plan_paths", "owned_review_paths"):
        value = payload.get(key)
        if isinstance(value, list):
            paths.extend(item for item in value if isinstance(item, str))
    return paths


_FILES_HEADING = re.compile(r"^Files:\s*$")
_LIST_ITEM = re.compile(r"^- `([^`]+)`")
_PATH_SPAN = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_./-]*$")


def owned_paths_from_plan(path: str) -> List[str]:
    """Derive the candidate's owned-path set pre-run from the covering
    plan's `Files:` lists: the backticked repo-path spans of the `- `
    list items directly following each `Files:` line, unioned in file
    order, deduplicated. A span outside a Files: list (a class anchor, a
    command) never contributes."""
    try:
        with open(path, encoding="utf-8") as handle:
            lines = handle.read().splitlines()
    except OSError as exc:
        raise ToolError("plan %s is unreadable: %s" % (path, exc))
    paths: List[str] = []
    seen = set()
    in_files_block = False
    for line in lines:
        if _FILES_HEADING.match(line):
            in_files_block = True
            continue
        if in_files_block:
            match = _LIST_ITEM.match(line)
            if not match:
                in_files_block = False
                continue
            span = match.group(1)
            if ("/" in span or "." in span) and _PATH_SPAN.match(span):
                if span not in seen:
                    seen.add(span)
                    paths.append(span)
    if not paths:
        raise ToolError("derived no owned paths from the plan's Files: "
                        "lists in %s" % path)
    return paths


class ToolError(Exception):
    """The script cannot perform its check reliably (missing inputs,
    unsupported data, usage violation)."""


class _UsageToolErrorParser(argparse.ArgumentParser):
    """Route usage violations (missing required options, malformed or
    mutually exclusive values) through the ToolError path: the script
    exits 3 with a final ``OUTCOME: tool_error`` line instead of
    argparse's bare exit 2 with no OUTCOME line."""

    def error(self, message):
        raise ToolError("usage: %s" % message)


class _OutstandingRunAction(argparse.Action):
    """Collect outstanding runs in argv order across both outstanding-run
    options. argparse's plain append action fills one list per option,
    which drops the interleaving of --outstanding-with-manifest and
    --outstanding-without-manifest occurrences that check_admission's
    first-blocker rule reads; this action appends each occurrence to the
    shared ``outstanding_runs`` list while parse_args walks argv, so the
    runs reach check_admission in the order the caller wrote them."""

    def __call__(self, parser, namespace, values, option_string=None):
        runs = list(getattr(namespace, "outstanding_runs", None) or [])
        if self.dest == "outstanding_with_manifest":
            run_id, manifest_path = values
            runs.append(("with-manifest", run_id, manifest_path))
        else:
            runs.append(("without-manifest", values, None))
        setattr(namespace, "outstanding_runs", runs)


def build_parser():
    parser = _UsageToolErrorParser(
        prog=PROG,
        description="Target-disjointness dispatch admission: refuse a "
                    "candidate whose owned-path set intersects an "
                    "outstanding run's recorded set.")
    parser.add_argument("--candidate-run", required=True,
                        help="the candidate run id named in the verdict")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--owned-path", action="append", default=[],
                        help="candidate owned path, repeatable")
    source.add_argument("--candidate-manifest",
                        help="candidate done-setup run manifest")
    source.add_argument("--plan",
                        help="derive candidate owned paths from the "
                             "plan's Files: lists")
    parser.add_argument("--outstanding-with-manifest",
                        action=_OutstandingRunAction,
                        nargs=2, metavar=("RUN_ID", "MANIFEST"),
                        help="outstanding run with its done-setup "
                             "manifest, repeatable")
    parser.add_argument("--outstanding-without-manifest",
                        action=_OutstandingRunAction, metavar="RUN_ID",
                        help="outstanding run carrying no done-setup "
                             "manifest, repeatable")
    parser.set_defaults(outstanding_runs=[])
    return parser


def main(argv=None):
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        if args.candidate_manifest:
            candidate_paths = owned_paths_from_manifest(args.candidate_manifest)
        elif args.plan:
            candidate_paths = owned_paths_from_plan(args.plan)
        elif args.owned_path:
            candidate_paths = list(args.owned_path)
        else:
            raise ToolError("no candidate owned-path source given: one of "
                            "--owned-path, --candidate-manifest, or --plan "
                            "is required")

        outstanding_runs: List[OutstandingRun] = []
        for kind, run_id, manifest in args.outstanding_runs:
            if kind == "with-manifest":
                outstanding_runs.append(OutstandingRun(
                    run_id=run_id,
                    owned_paths=owned_paths_from_manifest(manifest),
                    source="done-setup manifest %s" % manifest,
                ))
            else:
                outstanding_runs.append(OutstandingRun(
                    run_id=run_id,
                    owned_paths=None,
                    source="no done-setup manifest recorded",
                ))

        candidate = Candidate(args.candidate_run, candidate_paths)
        verdict = check_admission(candidate, outstanding_runs)

        print("dispatch admission: %s" % ("ADMITTED" if verdict.admitted
                                          else "REFUSED"))
        print("candidate run: %s" % candidate.run_id)
        print("candidate owned paths: %d" % len(candidate.owned_paths))
        for run in outstanding_runs:
            print("outstanding run: %s (%s)" % (run.run_id, run.source))
        if verdict.admitted:
            print("verdict: %s" % verdict.reason)
            print("OUTCOME: pass")
            return 0
        print("blocking outstanding run: %s" % verdict.blocking_run_id)
        print("reason: %s" % verdict.reason)
        if verdict.intersecting_paths:
            print("intersecting paths: %s" % ", ".join(verdict.intersecting_paths))
        print("OUTCOME: fail")
        return 1
    except ToolError as exc:
        print("%s: %s" % (PROG, exc))
        print("OUTCOME: tool_error")
        return 3


if __name__ == "__main__":
    sys.exit(main())
