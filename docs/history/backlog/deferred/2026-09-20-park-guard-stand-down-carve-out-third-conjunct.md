# Backlog: park-guard stand-down carve-out third machine conjunct

<<<<<<<< HEAD:docs/history/backlog/completed/2026-09-20-park-guard-stand-down-carve-out-third-conjunct.md
Status: done
========
Status: open
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; hardening against a hypothetically gaming failed child. Revive on a witnessed failed child claiming stand-down, or a project-priority-profile change.)
>>>>>>>> f8fbd660 (backlog: defer 72 formal items per project-priority full sweep):docs/history/backlog/deferred/2026-09-20-park-guard-stand-down-carve-out-third-conjunct.md
Origin: review r1 risk lens (deferred, design change beyond the certified park-guard plan)
Plan: docs/plans/completed/2026-09-19-maintenance-park-guard-externally-gated-plans.md (after archive)

The stand-down carve-out's machine test (json present naming the plan path + plan file unchanged vs dispatch_plan_sha) is child-asserted evidence: a json-writing failed child is indistinguishable from a legitimate stand-down, silently defeating the failure cap on exactly the zero-progress population the cap exists to catch. Hardening candidate: a third machine conjunct the checking turn evaluates itself: re-run the Gate satisfaction rule on the target plan (and/or grep the plan's first task for the stand-down prescription); a child claiming stand-down on a satisfied gate or an unprescribing plan accrues credit normally. Also echo the json contents in the turn output for triage.
