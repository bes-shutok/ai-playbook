# Hyphen-bounded slug non-match unpinned across the execution-claim gateway suite

- **Status:** open
- **Priority:** medium
- **Origin class:** learn Step 1.9 project issue (witnessed 2026-10-27, learn+investigate over the interactive exec max-2 run that landed the sweep landedness matcher widening)
- **Skill/step:** `scripts/execution_claim.sh` `sweep_landing_subject_names_slug` (the hyphen-bounded-segment guarantee) and `scripts/test_execution_claim.py` (the gateway suite's sweep landedness pins)
- **Driving force:** correctness; secondary: test-debt
- **Cluster:** the sweep landedness leg's subject-grammar defect is covered (matcher widened to the recognized LANDING_CLAIM_PREFIXES forms, EXEC-PROMPTS entry claim-sweep-landing-subject-grammar-mismatch); this row owns the boundary behavior that widening's panel recorded on its watchlist as pre-existing debt
- **Dedupe probe:** searched open backlog filenames and text for `hyphen-bounded`, `longer token`, and `prefix or suffix`; the only hits are the consumed EXEC-PROMPTS entry's receipt lines; no open row owns the boundary behavior.
- **Problem:** the matcher's docstring guarantees a subject witnesses a landing only when the slug appears as a hyphen-bounded segment, never as the prefix or suffix of a longer token (the regex `(^|[^a-z0-9-])<slug>([^a-z0-9-]|$)`), but no test in the gateway suite pins that non-match: every sweep subject in the suite uses the claim slug verbatim, so a future edit that loosens the segment boundary (for example, dropping the boundary classes from the regex) keeps the suite green while a longer slug silently vouches for its prefix.
- **Observed versus expected:** observed: a landing subject naming a longer slug that contains the claim slug as a prefix or suffix is not covered by any pin; expected: one sweep test committing such a longer-token subject asserts the skip (the fail-closed skip reason and unchanged claim bytes), so the boundary guarantee is regression-locked like the grammar forms are.
- **Reproduction evidence:** grep of `scripts/test_execution_claim.py` at the landing head 580fb9d52: every landing-subject literal embeds the bare SLUG constant; no longer-token subject exists; the watchlist Low is recorded in the landing commit message and the EXEC-PROMPTS-PRUNE receipt.
- **Environment context:** playbook repo, 2026-10-27, the gateway suite's scratch-repo pattern (per-method repo, `EXECUTION_CLAIM_LOCK_HOME` pinned).
- **Suspected root area:** the boundary guarantee predates the grammar widening; the widening's scope arms named one pin per grammar form plus the unrecognized-prefix pin, so the boundary case was never in any entry's scope.
- **Class:** fix-class (one sweep test pinning the non-match; no behavior change).
