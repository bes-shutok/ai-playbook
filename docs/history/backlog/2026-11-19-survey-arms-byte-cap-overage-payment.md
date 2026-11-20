# survey-arms.md byte-cap overage payment

Status: open
Priority: medium
Class: skill-text-budget
Origin class: inherited-pre-existing-red
Cluster: docs/history/backlog/2026-11-20-known-red-baseline-stales-under-landing-traffic.md (the stale budget section is the pre-classification side of the same advisory red this row pays down)
Driving force: the pinned 85706-byte cap on agents/skills/maintenance/survey-arms.md is crossed at main: the file measured 88502 bytes at commit 322e1c07c before the post-fire-verification plan's Task 3 ran (plan authoring measured 84023 on 2026-11-14; landings c4dc2798f and c7fd7a251 grew the file past the cap afterwards). The executing plan's Task 3 applied its same-change payment duty to its own addition (739 added / 522 deleted, net +217) but the ~2796-byte pre-existing breach (88502 - 85706) needs a dedicated payment pass.

## Acceptance
- A payment pass cuts >= 3013 bytes of story/witness-class text from survey-arms.md without removing any exactly-once pinned needle or required-battery-covered operative text, bringing the file to <= 85706 bytes (3329 from the post-fire-outcome-execution 89035-byte tree, measured 2026-11-20 after that run's net +316; 3013 from the 88719-byte post-task tree).
- The plan-validation needle `test "$(wc -c < agents/skills/maintenance/survey-arms.md)" -le 85706` goes green on main.
- The overage sources are named in the pass record (c4dc2798f drain-arms arm growth, c7fd7a251 lane-state sharing growth).
