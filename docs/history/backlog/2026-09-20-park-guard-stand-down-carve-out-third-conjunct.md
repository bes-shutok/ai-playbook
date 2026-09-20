# Backlog: park-guard stand-down carve-out third machine conjunct

Status: open
Origin: review r1 risk lens (deferred, design change beyond the certified park-guard plan)
Plan: docs/plans/completed/2026-09-19-maintenance-park-guard-externally-gated-plans.md (after archive)

The stand-down carve-out's machine test (json present naming the plan path + plan file unchanged vs dispatch_plan_sha) is child-asserted evidence: a json-writing failed child is indistinguishable from a legitimate stand-down, silently defeating the failure cap on exactly the zero-progress population the cap exists to catch. Hardening candidate: a third machine conjunct the checking turn evaluates itself — re-run the Gate satisfaction rule on the target plan (and/or grep the plan's first task for the stand-down prescription); a child claiming stand-down on a satisfied gate or an unprescribing plan accrues credit normally. Also echo the json contents in the turn output for triage.
