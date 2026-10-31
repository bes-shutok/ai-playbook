# Refresh lesson 139's empty-owned-set remedy sentence

Driving force: correctness

Origin: intermediate task review Low finding (execute-plan run gate-removal-empty-owned-set-remedy, 2026-10-31).

`docs/maintenance/development_lessons.md` lesson #139 says the empty-owned-set remedy is a claims file, "never a header edit to the certified plan (that would stale the bound digest)". The gate's remedy line now (landed with the 2026-10-27-gate-removal-empty-owned-set-remedy plan) names two attainable inputs: a `Plan review record:`/`Plan review:` header citation, or a `--claims` file with record paths. Refresh the lesson's remedy sentence to match the gate's two-input line and re-anchor the certified-plan caveat (claims path is the digest-safe option for digest-bound certified plans) so the corpus does not contradict the printed remedy.
