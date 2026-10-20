# Backlog: pins re-aim hardening and style follow-ups (smme execution r1 residuals)

Status: open
Priority: low
Class: pins-script hardening and provenance style
Origin class: execution review r1 of docs/history/plans/2026-10-14-skill-monolith-module-extraction.md (findings F8, F9)
Driving force: code-quality

- Split-count per-leg hardening (r1 F8, correctness#split-count-distribution-blind + design#split-count-blind-leg): the re-aimed split-count row (scripts/check_maintenance_pins.sh ~line 2950) gates the total as one arithmetic sum, so a (2,0)/(0,2) redistribution passes where the pre-extraction gate would have caught a single-site loss. The plan's edge-case text sanctioned the total-preserving form, so this is hardening, not a violation: split into two per-leg count rows, each -eq 1, preserving the no-third-copy property.
- Re-aim provenance style (r1 F9, design#inline-module-path-x30 + design#verbatim-comment-copies): the re-aimed rows inline the module path literals with no variable binding (the file's convention binds section paths once, e.g. E= at ~line 312); bind WF= and VA= beside the existing bindings and use them in the re-aimed rows. Optionally shorten the 18 byte-identical provenance comment bodies to their varying part, one line per contiguous run.
