# Plan: delete legacy Summary verdict grammar from plan_readiness

Backlog origin: `docs/history/backlog/2026-09-05-plan-readiness-legacy-verdict-grammar-deletion.md` (scope of record)
Origin source: `docs/history/backlog/completed/2026-09-04-plan-readiness-sidecar-verdict-field.md` (acceptance criterion 3)
Language guidelines: `projects/.ai-playbook/python_guidelines.md`

## Terms

- **sidecar verdict field**: the `verdict` key (`"yes"`/`"no"`) in a review round's `.stats.json`, written by review-plan; conforming membership is owned by `sidecar_verdict()` in `scripts/plan_readiness.py`.
- **Summary token grammar** (formerly the "total rule"): any `## Summary` line containing a word-bounded `ready=yes` / `ready=no` token is a verdict line; the last occurrence in the section wins; implemented by `VERDICT_TOKEN_RE` plus `verdict_tokens()`.
- **verdict-source drift**: a covered artifact whose conforming sidecar verdict contradicts its Summary's last verdict token.
- **eligibility gate**: `--sweep` coverage with total positive and covered equal to total over the live plan-review corpus; the blocking precondition for the deletion.
- **mention detector**: the existing sweep anomaly that fires when a Summary mentions `ready=` but yields no verdict token (`SWEEP_MENTION_RE`).
- **Skill-gate marker**: the per-(project, session) consent marker at `~/.ai-playbook/runtime/skill-invoked/plans.<project>.<session>.marker`, refreshed before every gated plan-file write per `agents/hooks/skill-gate/README.md` ("Marker WRITE RECIPE (plans class)"); the session key is the literal `no-session` when the session id is empty after stripping, otherwise `sha1(value)[:16]` hex.

## Design Invariants (CR Guard)

1. Sidecar verdict field primacy (2026-09-05 plan-readiness-migration): this deletion completes that consumer precedence decision; no prose-derived verdict may re-enter the gate.
2. Fail-closed gate convention: an unverifiable verdict fails with a named reason, never passes silently; the r2 F1 versionless tolerance was a bridge for the pre-convergence window only, and this deletion deliberately ends it.
3. The sweep stays the drift detector (origin acceptance criterion 3): deleting the gate fallback must not end drift detection; the sweep drift anomaly carries it.
4. Single-owner predicates: the yes/no membership test stays inside `sidecar_verdict()`; token extraction stays inside `verdict_tokens()`; no new copies of either.

## Assumptions

- assume the drift disposition is the sweep-side anomaly (option a, first-listed in the item); basis: origin acceptance criterion 3 suggested fix "keep --sweep as the drift detector", accepted under standing pre-authorization to take recommended options.
- assume fail-closed semantics for a missing or non-conforming verdict field after the deletion; basis: the item's eligibility rationale ("deleting it early would newly fail readiness for every pre-adoption artifact") and the repo's fail-closed convention.
- assume corpus convergence (backfilling or archiving the legacy artifacts) is a separate effort outside this plan; basis: the item's Scope line names `scripts/plan_readiness.py` only.
- assume `VERDICT_TOKEN_RE` and `verdict_tokens()` survive with sweep-side-only consumers; basis: the suggested fix keeps the sweep's mention detector and the drift anomaly needs token extraction; the item's "remove the now-dead VERDICT_TOKEN_RE machinery" is implemented as "remove the gate-side fallback machinery and rewrite the comment block", stated here so the deviation is explicit.
- assume the authoring-time measurements recorded 2026-09-15: sweep coverage 235/478 (ineligible today), verdict drift 0 across covered artifacts, selftest exit 0; basis: probes in `docs/tmp/plan-requirements-plan-readiness-legacy-verdict-grammar-deletion.md`; Task 1 re-measures at execution.

Decision points requiring a grill: drift disposition = sweep-side anomaly (option a); source: origin acceptance criterion 3 suggested fix plus the first-listed disposition in the spin-off item, accepted under standing pre-authorization; 2026-09-15; affects Gist, Tasks 1 to 4, Evaluation Criteria.

## Gist & Examples

What changes: today the readiness gate accepts a review round whose sidecar lacks a conforming verdict field by reading the review's `## Summary` for `ready=yes` / `ready=no` tokens. This plan deletes that fallback so the sidecar verdict field is the only verdict source in the gate. A missing or non-conforming field becomes a named fail-closed failure. Because the fallback was also the only place comparing the sidecar against the prose, the sweep gains a drift anomaly that flags a conforming sidecar verdict contradicting the Summary's last token, keeping the signal the origin item told us to keep.

Why gated: the fallback exists for pre-adoption artifacts. The eligibility gate (positive total, covered equal to total) proves every live plan-review artifact carries a conforming sidecar verdict, so deleting the fallback breaks nobody. Measured 2026-09-15 the corpus is 235/478, so Task 1 stands execution down until convergence; this plan is authored now and executes when eligible, exactly as the time-gated item prescribes.

Before (today): a plan's latest round has Summary line `- ready=yes` but its sidecar has no verdict field (a pre-adoption artifact): the gate falls back to the Summary token, reads yes, and passes. A sidecar `verdict: "maybe"` with Summary `- ready=no`: the fallback reads no and the gate fails with "does not report a ready=yes verdict line in its ## Summary".

After (this plan): the same missing-field artifact fails with "sidecar has no conforming verdict field"; the "maybe" artifact fails with the same named reason and the Summary is never consulted. Conforming yes/no artifacts gate exactly as today. Meanwhile `--sweep` on an artifact whose sidecar says yes but whose Summary's last token is no exits 1 listing the drift anomaly; an artifact with no sidecar verdict stays invisible to the drift check (nothing to compare) and keeps failing readiness fail-closed.

Edge cases that shaped the design: a Summary with no tokens (or no Summary section) cannot contradict anything, so no drift anomaly fires for it; the mention detector keeps covering malformed mentions. Boundary tokens like `Notready=yes` are not word-bounded and stay outside the grammar (the `\b` anchors live on, sweep-side).

## Evaluation Criteria

**Quality dimensions:**
- correctness: `python3 scripts/plan_readiness.py --selftest` exits 0 after every commit; the rewritten fixtures fail first (RED) naming exactly the claimed failing set (Task 2: the 6 ids its RED bullet enumerates; Task 3: the rc-1-asserting drift and migration ids).
- behavioral parity: the sidecar yes/no precedence fixtures are untouched and green across every commit; conforming artifacts gate identically to today (same pass/fail outcomes and the same reason strings).
- fail-closed behavior: the new reason string is grep-pinned in the source; the `evaluate_readiness` region contains zero `verdict_tokens` references after Task 2.
- documentation consistency: the three live docs carry no fallback clause (negated, rc-aware grep set) while unrelated content stays untouched.
- corpus safety: the live sweep exits 0 after Task 3 (drift measured 0 on 2026-09-15; Task 1 re-verifies at execution).

**Done when:**
- every task checkbox is checked and the full Validation Commands block exits 0 end to end, including the live gate run on this plan.

**Ship when:**
- corpus eligibility convergence (sweep coverage total positive and covered equal to total, zero drift, zero sweep anomalies) is an external prerequisite; until then Task 1 stands the execution down and this plan stays open by design (the item is time-gated). No deployed-environment or cross-team condition applies; the validator is repo-local.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/plan_readiness.py` (the built-in selftest suite lives inside this same file: `_selftest_verdict_grammar`, `_selftest_sweep`, and the fixture builders; there is no separate test file)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Documentation:** the precedence clauses Task 4 edits live in `agents/hooks/plan-readiness/README.md`, `agents/skills/review-plan/SKILL.md`, and `agents/skills/review-loop/SKILL.md`; doc findings on those three files are in scope when causally related to the verdict-source change.

**Out of scope; reject unless plan-related:**
- `scripts/validate_review_staging.py`; reason: sibling shared-rule module, no contract change in this plan
- `docs/history/` and the legacy artifacts under `docs/reviews/`; reason: immutable history; corpus convergence is an external prerequisite
- deployed runtime copies of the validator outside the repo; reason: the repo copy is canonical; redeployment is ops, not this plan

## Validation Commands

```bash
set -u
fail() { echo "VALIDATION FAIL: $1"; exit 1; }

python3 scripts/plan_readiness.py --selftest || fail "selftest"
python3 scripts/plan_readiness.py --sweep || fail "live sweep reported anomalies"
python3 scripts/plan_readiness.py docs/plans/2026-09-15-plan-readiness-legacy-verdict-grammar-deletion.md || fail "live gate on this plan"

grep -q "no conforming verdict field" scripts/plan_readiness.py || fail "fail-closed reason string missing"

# the fallback branch is really gone from the gate function (region-scoped
# count with fail-closed extractor assertions: an empty or over-long
# extraction is a broken anchor, never a passing count)
REGION=$(sed -n '/^def evaluate_readiness/,/^# Raw "ready=" mention/p' scripts/plan_readiness.py)
printf '%s\n' "$REGION" | grep -q "^def evaluate_readiness" || fail "region extractor lost its start anchor"
printf '%s\n' "$REGION" | grep -q 'Raw "ready=" mention' || fail "region extractor lost its end anchor"
COUNT=$(printf '%s\n' "$REGION" | grep -c "verdict_tokens")
[ "$COUNT" -eq 0 ] || fail "evaluate_readiness still calls verdict_tokens ($COUNT)"

# stale fallback clauses gone from the three live docs (grep rc captured:
# only rc 1 is a clean no-match; rc >= 2 is a tool error and fails)
for f in agents/hooks/plan-readiness/README.md agents/skills/review-plan/SKILL.md agents/skills/review-loop/SKILL.md; do
  test -f "$f" || fail "missing doc $f"
  for pat in "legacy Summary" "Summary total rule" "consumer rule for the verdict is a TOTAL rule" "falls back to Summary parsing" "fall back to that rule" "still predates the sidecar verdict field"; do
    RC=0
    grep -q "$pat" "$f" || RC=$?
    if [ "$RC" -eq 0 ]; then fail "stale fallback clause '$pat' in $f"; fi
    if [ "$RC" -ge 2 ]; then fail "grep tool error (rc $RC) for '$pat' in $f"; fi
  done
done

echo "VALIDATION OK"
```

### Task 1: eligibility precondition (read-only stand-down gate)

Files: none (probes only; no edits, no commit)

- [ ] Run `python3 scripts/plan_readiness.py --sweep`; parse the coverage line; require total positive and covered equal to total; record the numbers in the execution log.
- [ ] Run the drift probe with the module's own functions (self-contained recipe): import `scripts/plan_readiness.py` with the repo `scripts/` directory on `sys.path`; iterate the sorted `*-plan-review-*.md` glob hits under `{reviews_dir}`; read each sidecar via the sibling module's `stats_sidecar_path`; for dict payloads take `sidecar_verdict(payload)`; read the artifact and compute `verdict_tokens(summary_section(content))`; count covered artifacts whose tokens are non-empty and whose last token (lowercased) differs from the sidecar verdict; require the count to be zero and record it. Authoring measurement 2026-09-15: total 478, covered 235, contradictions 0.
- [ ] Transient-failure tolerance, both shapes: a sweep exit 1 from a torn mid-round write by a parallel session (a partial Summary mentioning `ready=` with no complete token yet) is retried once after a short wait (seconds) before being attributed to real anomalies; the same tolerance applies to the coverage half (a torn sidecar write yields exit 0 with covered<total, so an ineligible-looking coverage line is retried once before the stand-down fires); an `unreadable` anomaly caused by an artifact vanishing mid-sweep (parallel archival) is retried once like the other transient shapes. The drift check itself is torn-read-safe (an artifact without a conforming sidecar verdict is not covered and not an anomaly); an artifact whose file disappears between the probe's glob and its read is skipped and noted, retried once. The post-retry reading governs; persistent ineligibility or persistent anomalies after the one retry mandate STOP exactly like the primary stand-down rule.
- [ ] If either required check fails: STOP. Edit nothing, commit nothing; report the stand-down with the measured numbers and leave the plan open (time-gated item; convergence is the Ship-when prerequisite).

### Task 2: sole-source verdict step and the fixture migration it forces (RED then GREEN)

Files:
- `scripts/plan_readiness.py`

- [ ] RED: in `_selftest_verdict_grammar`, rewrite the three fallback characterizations to fail-closed expectations under renamed check ids: `selftest#verdict_field/legacy_verdict_junk_falls_back/string_arm` becomes `selftest#verdict_field/legacy_verdict_junk_rejected/string_arm` (sidecar `verdict: "maybe"`, expect not ok with reason containing "no conforming verdict field"); the dict arm becomes `selftest#verdict_field/legacy_verdict_junk_rejected/dict_arm` (dict-valued verdict, same new reason); `selftest#verdict_field/absent_falls_back_to_summary` becomes `selftest#verdict_field/absent_verdict_rejected` (`sidecar_verdict_value=None`, no verdict field, same new reason).
- [ ] RED: repoint the fixtures that assert Summary-grammar reasons, each with an explicit input (the builder default would otherwise make them pass): `selftest#verdict_outside_summary_rejects` and `selftest#boundary_violating_mention_rejects` take `sidecar_verdict_value=None` (verdict-less sidecar) and expect not ok with "no conforming verdict field" in the reason; `selftest#ready_no_verdict` takes `sidecar_verdict_value="no"` and expects not ok with the existing "sidecar verdict field reports 'no'" reason (green in both worlds; it pins the decisive "no" arm's text); `selftest#stale_digest_after_plan_edit/review_markdown_edited` keeps the conforming default sidecar and edits the Markdown to add an unresolved blocking finding, mirroring it into the sidecar (a `findings` entry plus `counts.staged_findings = 1`, exactly what the builder's `blocking=True` writes; without the mirror the generic finding-conservation schema gate fails the arm before the verdict step), expecting not ok with the unresolved-blocking reason (this preserves a Markdown-only re-read discriminator); refresh each migrated or renamed fixture's adjacent comment with the new expectation (the "fallback must survive unchanged" lead comment and the per-fixture characterization comments still describe the deleted behavior).
- [ ] RED: replace the gate-side `verdict_line_shapes` family, including its `last_line_wins_no` and `last_line_wins_yes` arms (keeping them would add an unnamed RED failure under the builder default), with one representative fixture `selftest#verdict_field/absent_verdict_rejects_regardless_of_summary` (a corpus-shaped Summary verdict line with no sidecar verdict field, expect not ok with the new reason); the full corpus shape list (yes and no shapes) migrates sweep-side in Task 3.
- [ ] Migrate the fixture builders (this is what makes the GREEN gate reachable): today `_write_clean_state` and `_clear_sidecar` write no `verdict` key, so every default clean-state fixture passes gate step 4 only through the Summary fallback (bare-deletion baseline, worker-verified: 114 checks fail). Add a NEW parameter `sidecar_verdict_value: str | None = "yes"` to `_write_clean_state` (the written sidecar carries `verdict: "yes"` unless the caller passes another value; `None` omits the key for verdict-less states); the existing Summary-side `verdict` parameter is untouched and keeps feeding `_review_markdown` only; `_clear_sidecar` itself stays verdict-less; the `latest_round_selection_tie_break` family's `inverted_polarity_ok` arm builds its own sidecar via `_clear_sidecar` and sets its verdict explicitly.
- [ ] Apply the collateral fixture reworks the builder default forces, reworking exactly what the GREEN run shows needs it (at RED the collateral families are green by design; family names, not hard counts, since families grow): the `decision_marker` family, the `review_scope` family, the `cli` family (`accepted_state`, `rejected_state`, `nested_cwd`, `cwd_relative_dotdot`, `tilde_facts`), `stale_digest_after_plan_edit`, `unresolved_blocking_finding`, `ready_no_verdict`, `uppercase_round_suffix_ignored`, the `latest_round_selection_tie_break` arms, `glob_metachar_slug`, and `accepted_state`; most pass unchanged once the builder feeds conforming verdicts, and polarity or reason-asserting arms set explicit `sidecar_verdict_value` values or repoint at the reasons as above.
- [ ] Rework the two sweep coverage-count fixtures for the new default: `selftest#sweep/coverage_mixed_corpus` (covered count becomes 2/3) and `selftest#sweep/coverage_malformed_sidecar_uncovered` (1/2), or construct their verdict-less states explicitly so the pinned counts stay honest; update each fixture's adjacent comment to describe the new default (the r1-era comment above `coverage_mixed_corpus` pins the old 1/3 count).
- [ ] Run → expect RED: `python3 scripts/plan_readiness.py --selftest` exits nonzero naming exactly 6 failing ids: the three renamed `verdict_field` ids, the replacement fixture (`absent_verdict_rejects_regardless_of_summary`), and the two verdict-less repointed arms (`verdict_outside_summary_rejects`, `boundary_violating_mention_rejects`). The `ready_no_verdict` arm and the repointed `review_markdown_edited` arm pass in both worlds by design (the "reports 'no'" branch predates this plan; the blocking-finding expectation is outcome-based), and the collateral families stay green at RED because the builder migration precedes this run (the 114-check figure is the bare-deletion baseline without the builder migration, recorded as context). Record the failing set in the execution log.
- [ ] GREEN: in `evaluate_readiness` step 4, delete the Summary fallback branch; after the existing "no" arm, any value that is not "yes" returns False with the f-string reason `latest review r{round_no} sidecar has no conforming verdict field (expected "verdict": "yes" or "no" written by review-plan)`. Rewrite the WHOLE `VERDICT_TOKEN_RE` comment block for sweep-side-only consumers (the gate-flavored rationale lines included), dropping the PRECEDENCE paragraph and the time-gate sentence; the step comment states the r2 F1 versionless tolerance is deliberately reversed by this deletion. Reword the sweep coverage line in the same commit (drop the eligibility sentence; state that artifacts without a conforming sidecar verdict fail readiness fail-closed); the rewritten `VERDICT_TOKEN_RE` comment block names the sweep mention detector as its only consumer until Task 3. Update the `sidecar_verdict` docstring (readiness callers fail closed on None; the sweep counts None as not covered).
- [ ] Run → expect GREEN: `python3 scripts/plan_readiness.py --selftest` exits 0.
- [ ] Commit: `plan-readiness: sidecar verdict field becomes the sole verdict source`

### Task 3: sweep drift anomaly and sweep-side grammar home (RED then GREEN)

Files:
- `scripts/plan_readiness.py`

- [ ] RED: in `_selftest_sweep`, add drift fixtures that set the sidecar verdict via the Task 2 builder parameter where the fixture uses `_write_clean_state` (pass `sidecar_verdict_value="yes"` / `sidecar_verdict_value="no"`), or read-modify-write the sidecar JSON where a fixture builds its own (the `_write_clean_state` `verdict` parameter feeds only the Summary Markdown): contradiction (sidecar `verdict: "yes"`, Summary `- ready=no` → `run_sweep` rc 1, output names the artifact and both values); agreement as a covered state (sidecar `verdict: "yes"`, Summary `- ready=yes` → rc 0); no-token Summary (sidecar `verdict: "yes"`, Summary `- verdict deferred` → rc 0, nothing to contradict); last-occurrence-wins (Summary with a `ready=no` line followed by a `ready=yes` line: sidecar `verdict: "no"` → rc 1 drift, sidecar `verdict: "yes"` → rc 0).
- [ ] RED: migrate the corpus-derived verdict-line shape list into a sweep-side loop over `run_sweep`, both polarities: each yes-shaped Summary with sidecar `verdict: "no"` → rc 1 drift; with sidecar `verdict: "yes"` → rc 0; each of the 8 corpus-derived no-shaped Summaries with sidecar `verdict: "yes"` → rc 1 drift; with sidecar `verdict: "no"` → rc 0 (the no shapes keep a direct witness for the `(yes|no)` no-alternation).
- [ ] Run → expect RED: `python3 scripts/plan_readiness.py --selftest` exits nonzero naming exactly the rc-1-asserting drift and migration check ids (the contradiction fixture, both last-occurrence-wins rc-1 arms, and the shape-migration checks that assert rc 1; the rc-0 checks pass in both worlds and are not part of the RED set). Record the failing set in the execution log; if any rc-0-asserting id or any unrelated family appears in it, STOP and reconcile before proceeding (a shortened shape migration shows up as missing rc-1 ids here).
- [ ] GREEN: in `run_sweep`, after the summary read, when the sidecar payload dict carries a conforming verdict and `verdict_tokens(summary)` is non-empty and its last token differs from the sidecar verdict, append the anomaly `{name}: sidecar verdict '<v>' contradicts the ## Summary's last verdict token '<t>' (verdict-source drift)`. Reword the `run_sweep` docstring, the mention-detector anomaly message, and the `--sweep` argparse help to match, and extend the `VERDICT_TOKEN_RE` comment block's consumer list with the drift anomaly (Task 2 rewrote the block before the anomaly existed). Preserve the `# Raw "ready=" mention` comment line verbatim (the Validation Commands region extractor anchors on it).
- [ ] Run → expect GREEN: selftest exits 0; `python3 scripts/plan_readiness.py --sweep` exits 0 on the live corpus (Task 1 recorded drift 0).
- [ ] Commit: `plan-readiness: sweep owns verdict drift detection after fallback deletion`

### Task 4: documentation precedence clauses

Files:
- `agents/hooks/plan-readiness/README.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/review-loop/SKILL.md`

- [ ] README "## Verdict representation" section, the whole section: the section's opening paragraph (the consumer rule and the precedence sentence share it) and the legacy-artifacts paragraph state that the sidecar verdict field is the sole verdict source with fail-closed behavior on a missing or non-conforming field; the TIME-GATED sentence and the open-item pointer are dropped (replaced with a pointer to the backlog item, whose completed/ location is settled by this workflow's completion pass).
- [ ] README gate summary (top of file): the fail-reason enumeration gains the new "no conforming verdict field" failure.
- [ ] README "## Drift check: --sweep" section: the anomaly list is the mention detector plus the new drift anomaly; ALL FOUR sweep-limits bullets are rewritten for the drift anomaly, including "Verdicts without `=`" (its claim that the readiness gate itself rejects prose-verdict Summaries fail-closed is false once the gate consults only the sidecar) and the "Negated mentions" bullet; the trailing future-option sentence about flagging multi-token Summaries is refreshed (the drift anomaly auto-flags the contradicted-last-token case; only same-verdict supersession remains human-eyes); the coverage-line wording is quoted in its new form.
- [ ] review-plan SKILL.md, both surfaces: the "Canonical verdict line" paragraph (which says the validator "falls back to Summary parsing") and the readiness-gate integration paragraph (sidecar field first, Summary total rule as the legacy fallback) state sidecar-only verdict semantics; that integration paragraph's fail-reason enumeration ("A missing or malformed sidecar, a `ready=no` verdict, or an unresolved blocking finding") gains the new "no conforming verdict field" failure; the stale-digest and Summary-no-longer-consulted clauses stay accurate.
- [ ] review-loop SKILL.md sweep paragraph: the failure-cause enumeration gains verdict-source drift; the coverage-line sentence is refreshed.
- [ ] Run → expect GREEN: the Validation Commands doc greps exit clean on all three files.
- [ ] Commit: `docs: plan-readiness precedence drops the legacy Summary fallback`

### Task 5: final validation and closure

Files: none beyond prior tasks (validation only)

- [ ] Run the full Validation Commands block; every gate exits 0; record the output in the execution log. The transient-failure tolerance applies here too: a live-sweep exit 1 from a torn mid-round write by a parallel session is retried once after a short wait before being attributed to real anomalies.
- [ ] Re-parse the live sweep coverage line and require total positive and covered equal to total (eligibility re-check at closure; a legacy-format artifact landing mid-execution regresses coverage and must stand the closure down per Task 1's rule, with the same retry tolerances; the post-retry reading governs and persistent ineligibility after the one retry mandates STOP). On a genuine regression: leave the commits in place, name every regressed artifact in the stand-down report, and note that backfilling its sidecar verdict (the corpus-convergence effort) restores it; if a revert is ever required, revert the Task 2 and Task 3 commits together in reverse order (reverting only Task 3 would leave deletion without the drift detector).
- [ ] Commit (only if review fixes left residue) or close with the clean-exit report.
