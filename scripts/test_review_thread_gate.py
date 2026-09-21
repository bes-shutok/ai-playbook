#!/usr/bin/env python3
"""Tests for the review-thread closure gate (review_thread_gate.py).

Canned fixtures only: the inventory is a written JSON file in the gh
GraphQL reviewThreads shape and the network path (--live) is never
exercised. Each test builds a scratch directory with tempfile.mkdtemp
and tears it down via addCleanup.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent / "review_thread_gate.py"

REPLY_BODY = "Fixed in abc1234: the gate now fails closed on unanswered threads."
REPLY_BODY_TWO = "Fixed in abc5678: the teardown now removes every scratch file."

BOT_AUTHOR = {"login": "coderabbitai", "__typename": "Bot"}
HUMAN_AUTHOR = {"login": "alice", "__typename": "User"}
AGENT_AUTHOR = {"login": "review-adapter", "__typename": "Bot"}


def review_thread(tid, parent_id, author, body, is_resolved=False, replies=()):
    """One reviewThreads node: parent comment first, replies after."""
    comments = [{"id": parent_id, "author": author, "body": body}]
    comments.extend(replies)
    return {"id": tid, "isResolved": is_resolved, "comments": {"nodes": comments}}


def agent_reply(comment_id, body):
    return {"id": comment_id, "author": AGENT_AUTHOR, "body": body}


def envelope(nodes):
    return {
        "data": {
            "repository": {
                "pullRequest": {"reviewThreads": {"nodes": nodes}}
            }
        }
    }


class ReviewThreadGateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="review-thread-gate-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def write_marker(self, threads, name="marker.json"):
        path = self.tmp / name
        marker = {
            "pr": "octo/hello#7",
            "branch_head": "abc1234",
            "session_identity": "sess-fixture-1",
            "threads": threads,
        }
        path.write_text(json.dumps(marker, indent=2) + "\n", encoding="utf-8")
        return path

    def write_inventory(self, nodes, name="inventory.json"):
        path = self.tmp / name
        path.write_text(
            json.dumps(envelope(nodes), indent=2) + "\n", encoding="utf-8"
        )
        return path

    def run_gate(self, marker, inventory):
        proc = subprocess.run(
            [
                sys.executable, str(SCRIPT_PATH),
                "--marker", str(marker),
                "--inventory", str(inventory),
            ],
            capture_output=True,
            text=True,
        )
        return proc.returncode, proc.stdout, proc.stderr

    def test_all_replied_passes(self):
        t1 = review_thread(
            "PRRT_1", "IC_1", BOT_AUTHOR, "Flag: unused import.",
            replies=[agent_reply("IC_2", REPLY_BODY)],
        )
        t2 = review_thread(
            "PRRT_2", "IC_3", BOT_AUTHOR, "Flag: missing teardown.",
            replies=[agent_reply("IC_4", REPLY_BODY_TWO)],
        )
        marker = self.write_marker([
            {"id": "PRRT_1", "parent_id": "IC_1", "reply_body": REPLY_BODY},
            {"id": "PRRT_2", "parent_id": "IC_3", "reply_body": REPLY_BODY_TWO},
        ])
        inventory = self.write_inventory([t1, t2])
        code, out, err = self.run_gate(marker, inventory)
        self.assertEqual(code, 0, f"expected exit 0, stderr: {err}")
        self.assertIn("all 2 tracked thread(s) closed", out)
        self.assertIn("verified agent reply (already posted)", out)

    def test_unanswered_automated_fails(self):
        t1 = review_thread(
            "PRRT_1", "IC_1", BOT_AUTHOR, "Flag: unbounded retry loop.",
            is_resolved=True,
        )
        marker = self.write_marker([{"id": "PRRT_1", "parent_id": "IC_1"}])
        inventory = self.write_inventory([t1])
        code, out, err = self.run_gate(marker, inventory)
        self.assertEqual(code, 1, f"expected exit 1, stdout: {out}")
        self.assertIn("PRRT_1", out)
        self.assertIn("resolved without reply", out)
        self.assertIn("1 unclosed thread(s)", err)

    def test_disposition_passes(self):
        t1 = review_thread(
            "PRRT_1", "IC_1", BOT_AUTHOR, "Flag: naming style on the helper.",
        )
        marker = self.write_marker([
            {
                "id": "PRRT_1",
                "parent_id": "IC_1",
                "disposition": "deferred: pointer-cleanup backlog item filed",
            },
        ])
        inventory = self.write_inventory([t1])
        code, out, err = self.run_gate(marker, inventory)
        self.assertEqual(code, 0, f"expected exit 0, stderr: {err}")
        self.assertIn("explicit disposition recorded", out)
        self.assertIn("all 1 tracked thread(s) closed", out)

    def test_human_thread_never_autoresolved(self):
        t1 = review_thread(
            "PRRT_1", "IC_1", HUMAN_AUTHOR, "Why does this skip Windows?",
            is_resolved=True,
        )
        marker = self.write_marker([{"id": "PRRT_1", "parent_id": "IC_1"}])
        inventory = self.write_inventory([t1])
        code, out, err = self.run_gate(marker, inventory)
        self.assertEqual(code, 1, f"expected exit 1, stdout: {out}")
        self.assertIn("human thread (never auto-resolved)", out)
        # Inventory resolution alone never closes the thread.
        self.assertIn("resolution without a reply or disposition", out)
        self.assertIn("1 unclosed thread(s)", err)

    def test_duplicate_reply_detected(self):
        # The exact reply body is already posted twice (a retry raced a
        # slow post): the exact-body match marks the reply already
        # posted, so the thread counts verified and the duplicate is
        # reported instead of a third post being suggested.
        t1 = review_thread(
            "PRRT_1", "IC_1", BOT_AUTHOR, "Flag: unused import.",
            replies=[
                agent_reply("IC_2", REPLY_BODY),
                agent_reply("IC_3", REPLY_BODY),
            ],
        )
        marker = self.write_marker([
            {"id": "PRRT_1", "parent_id": "IC_1", "reply_body": REPLY_BODY},
        ])
        inventory = self.write_inventory([t1])
        code, out, err = self.run_gate(marker, inventory)
        self.assertEqual(code, 0, f"expected exit 0, stderr: {err}")
        self.assertIn("already posted", out)
        self.assertIn("duplicate reply detected", err)
        self.assertIn("all 1 tracked thread(s) closed", out)

    def test_missing_marker_passes(self):
        t1 = review_thread(
            "PRRT_1", "IC_1", BOT_AUTHOR, "Flag: unused import.",
        )
        inventory = self.write_inventory([t1])
        marker = self.tmp / "absent" / "marker.json"
        code, out, err = self.run_gate(marker, inventory)
        self.assertEqual(code, 0, f"expected exit 0, stderr: {err}")
        self.assertIn("nothing to check", out)
        self.assertEqual(err, "")


if __name__ == "__main__":
    unittest.main()
