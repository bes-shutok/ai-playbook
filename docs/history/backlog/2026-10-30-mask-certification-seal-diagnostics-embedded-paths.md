# Mask absolute home paths embedded in certification-seal landing diagnostics doc

Driving force: correctness + code-quality

`docs/history/certification-seal-landing-diagnostics.md` (landed in f50342158) embeds absolute home paths inside recorded validator stdout blocks. The release hygiene gate (`--files`) exits 1 on it today, and the widened default commit scan now reports it on every run (report-only since 2026-10-30-hygiene-scanner-default-scope-parity). Mask the embedded paths in that document per the current scanner masking policy so both scans run clean without touching deny patterns or exclusions. Witness: task-1 implement log and intermediate review, run hygiene-scanner-default-scope-parity 2026-10-30.

Re-witnessed 2026-10-31 (landing-diagnostic-own-plan-target exec run): the red persists at base (7 resolved-root receipt lines, identical count HEAD vs branch) and forced the run's plan validation command to report pre-existing failure; no delta contribution.
