# Backlog: dfm r2 F1 successor comment lands split across its two pin sites

- Priority: low
- Status: open
- Workflow: backlog
- Scope: `scripts/check_maintenance_pins.sh` (dfm successor pin comments)
- Owner: playbook maintenance
- Source: P56 execution review r1 F2 (non-blocking Low; consistency#successor-comment-placement-drift)
- Driving force: code-quality
- capture hygiene: pending scan

## Problem

Task 4 prescribed one shared comment `dfm r2 F1 successor (the archived gates left these producer steps ungated)` above the pin group; the landed suite carries the full comment only above the `$RP` pin, while the `$PL` pin pair carries the tag only in pin names under the F8 comment block.

## Expected

Comment text unified at the next natural touch of the pins suite: either one shared comment block spanning both sites or matching per-site comments; all consumer gates already pass, comment-text drift only.
