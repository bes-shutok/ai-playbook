# Plan: plan_readiness migration (tie-break fixture, sidecar verdict field, sibling compat backstop)

Backlog origins (scope of record):
- `docs/history/backlog/2026-09-03-plan-readiness-same-n-tie-break-fixture.md`
- `docs/history/backlog/2026-09-04-plan-readiness-sidecar-verdict-field.md`
- `docs/history/backlog/2026-09-04-validator-sibling-version-check.md`

Plan review: `docs/reviews/2026-09-05-plan-review-plan-readiness-migration-r6.md` (7 non-blocking findings folded; round r7 certifies the folded bytes)

## Terms

- **Readiness validator**: `scripts/plan_readiness.py`; the fail-closed gate called by `execute-plan` Step 0.5 and `done` Step 1.5. Answers: does the latest review of these exact plan bytes report ready with zero blocking findings and a valid sidecar?
- **Shared staging validator (vrs)**: `scripts/validate_review_staging.py`; owns digest, schema, sidecar-path, and review-parsing rules. The readiness validator imports it as `vrs`.
- **Stats sidecar**: the `.stats.json` JSON record written next to every review artifact by the review orchestrators (schema gold source: `agents/skills/review-staging/SKILL.md`).
- **Verdict field**: new optional version-1 sidecar top-level field `verdict`, string `yes` or `no`, written by `review-plan` alongside the `## Summary` it matches.
- **Feature slug**: plan filename stem minus its leading `YYYY-MM-DD-` prefix; drives the review-artifact glob `*-plan-review-<slug>-r<N>.md`.
- **Sweep**: `plan_readiness.py --sweep`; corpus drift check over `{reviews_dir}` plan-review artifacts, plus (after this plan) the coverage counter that gates the legacy-grammar deletion.
- **Pre-adoption artifact**: a live review artifact whose sidecar lacks the `verdict` field (produced before this plan's producer contract).
- **Compat handshake**: `validate_review_staging.py` declares `COMPAT_VERSION` (int); the readiness validator declares the value it shipped against (`EXPECTED_SIBLING_COMPAT_VERSION`) and checks the sibling at launch, failing loudly on missing or mismatched value.
- **Skill-gate marker**: per-(project, session) consent file at `~/.ai-playbook/runtime/skill-invoked/plans.<project>.<session>.marker`; `<project>` derives via the shared `facts_paths.resolve_project_key` (the ONE function both cores import; never re-implemented), `<session>` per Session key; refreshed by `python3 ~/.ai-playbook/scripts/skill_gate.py --write-marker [--session-id "$SID"]` BEFORE every plan-file write (create, update, and completion), fail-LOUD: abort with a clear error if the write fails. Active during execution too: every plan-file edit this plan's own lifecycle makes (task-checkbox updates, completion moves) refreshes the marker per this recipe.
- **Session key**: `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"` invoked VERBATIM (shared subprocess, Family D); empty-after-strip becomes the literal `no-session`; otherwise `sha1(value)[:16]` hex.

## Assumptions

- assume the compat check lives in the readiness validator's launch path only, and vrs never imports the readiness validator; basis: the import direction (plan_readiness.py:35 imports vrs; the reverse is a cycle) and the recorded queue decision from the readiness-gate plan ("version-check backstop on plan_readiness.py launch path only, never shared vrs").
- assume the legacy Summary verdict-grammar deletion is NOT executed by this plan; basis: the origin item's own time gate and the corpus state (zero artifacts carry a conforming string `verdict` today; the live corpus carries legacy non-conforming `verdict` keys, two plan-review sidecars dict-valued, that the consumer must keep tolerating via fallback, probe- and r2-verified), so the plan adds the mechanical eligibility counter and spins off a dedicated backlog item instead.
- assume only `review-plan` is taught to WRITE the verdict field; basis: the origin item's producer scope ("producer: review-plan writes it"); the schema change permits the field for every producer without mandating it.
- assume the review-loop sweep wiring is fail-loud before every round; basis: the origin item's rationale ("caught before a round starts rather than at gate time") and the sweep's sub-second cost over the corpus.
- assume this standalone plan supersedes the origin items' "belongs to the validator-pass plan" lines; basis: the scheduling instruction names this trio explicitly, and the 2026-09-04 refreshed backlog priority deliberately split it out as new-plan group 3 (time-gated/mooted) instead of folding it into validator-pass.
- assume execution order relative to the certified (unexecuted) validator-pass plan is interchangeable; basis: this plan's vrs edits (module constant region, optional-field tuple, v1 field-gate region) are disjoint from validator-pass's known task regions, and its plan_readiness edits are disjoint from validator-pass (which does not touch that file).

## Gist & Examples

Three workstreams, all in the readiness-validator family, one plan.

**1. Sidecar verdict field (producer + schema + consumer precedence).** Today a round's verdict lives only in review prose: the validator's total rule scans the `## Summary` for word-bounded `ready=yes`/`ready=no` tokens, last occurrence wins. That is robust over old artifacts but unstructured. After this plan, `review-plan` writes `"verdict": "yes"` (or `"no"`) into each round's sidecar in the same pass as the Summary, the version-1 schema allows and type-checks the field, and the readiness validator PREFERS the sidecar field, falling back to the prose rule only when the field is absent. Example: a sidecar says `verdict: "no"` while a stray `ready=yes` sits in the Summary; readiness must FAIL with `latest review r2 sidecar verdict field reports 'no'` instead of passing on the prose token. Artifacts keep working through the prose rule whenever their sidecar lacks a CONFORMING field: only an exact `yes`/`no` string decides, while legacy non-conforming `verdict` keys (dicts and other shapes exist in the live corpus, r2-verified) fall back to the prose rule exactly as today, and a non-conforming value on a version-1 record is rejected earlier by the schema gate. The legacy prose grammar itself is NOT deleted here: no live artifact carries a conforming field yet. Instead `--sweep` learns to print coverage (`sweep coverage: 3/7 plan-review artifacts carry a sidecar verdict field; ...`), and a new backlog item holds the deletion, eligible only when coverage reaches N==M.

**2. Sibling compat backstop.** The readiness validator imports digest, schema, and parsing rules from vrs in its own directory. A partially updated deployment (one file refreshed, sibling stale) currently imports cleanly and drifts silently. After this plan, vrs declares `COMPAT_VERSION = 1` and the readiness validator declares the value it shipped against; every launch (gate, sweep, and selftest modes) checks the sibling first and fails loudly: `compatibility FAILED: sibling validate_review_staging.py COMPAT_VERSION 999 != expected 1; ...`. A pre-handshake copy that lacks the constant gets its own named error. The check is consumer-side only: vrs never imports the readiness validator (the import direction makes that a cycle). Since the runtime scripts dir is fully symlinked to the repo, the handshake covers the historical "repo-local shadows deployed" hazard too: replacing a symlink with a stale snapshot copy trips the handshake unless the whole pair was replaced together; that both-stale-consistent case stays invisible and is documented as the accepted Low-severity residual.

**3. Same-N tie-break fixture.** `latest_review_round` picks the highest `r<N>` and breaks same-round ties by filename order (date prefix included), never mtime. No fixture pinned that tie-break: deleting it would leave the selftest green. The new fixture builds two `r1` artifacts for one slug with different date prefixes, gives the EARLIER-dated file a year-2100 mtime (so any mtime participation would flip the winner), and pins both polarities: later-dated `ready=no` fails readiness, later-dated `ready=yes` passes. Characterization GREEN on arrival (behavior probe-verified correct at authoring with both polarities under adversarial mtimes).

Plus one small wiring task: `review-loop` runs the sweep before every round so verdict-shape drift in the plan-review corpus surfaces at round start instead of at a finalization gate.

## Evaluation Criteria

**Quality dimensions:**
- correctness: `plan_readiness.py --selftest` and `validate_review_staging.py --selftest` pass including every new fixture; each new failure mode has a named reason string pinned by a fixture (sidecar-verdict-no, version-1 schema rejection of a non-conforming verdict value, compat missing constant, compat mismatch).
- compatibility: a stale or foreign sibling fails at launch in all three CLI modes; the both-stale-consistent limit is documented in the hook README rather than claimed solved.
- docs consistency: `review-staging` (gold), the `review-plan` inlined schema copy, and `agents/hooks/plan-readiness/README.md` agree on the verdict field, precedence, sweep wiring, and handshake (grep-pinned spans).
- minimality: no producer other than `review-plan` is required to write the field; no schema-version bump (optional field addition to version-1).

**Done when:**
- Both selftests pass with the new fixtures; `--sweep` exits 0 over the live corpus and prints the coverage line.
- The plan survives review with `ready=yes` and zero unresolved blocking findings on a fresh post-fold digest.
- The spin-off deletion backlog item exists; all three origin items are moved to `{backlog_completed_dir}` with `Status: done` and disposition lines, each move committed together with its content edit.

**Ship when:**
- Runtime propagation needs no deploy step: `~/.ai-playbook/scripts/` copies are symlinks into the repo, so the landed behavior is live on commit.
- The legacy grammar deletion executes via the spin-off backlog item once the sweep reports full coverage (time-gated, external to this plan).

## Design Invariants (CR Guard)

- The consumer's Summary total rule stays TOTAL and unchanged for artifacts whose sidecar lacks the verdict field (r4 reconciliation directive); precedence ADDS a preferred source, it never narrows the legacy rule while pre-adoption artifacts live, and a non-conforming `verdict` value on a versionless record falls back to the Summary rule and must NEVER newly fail readiness (the legacy corpus carries such keys, r2-verified).
- `latest_review_round` never resolves by mtime; the new fixture strengthens this existing invariant, it does not change selection behavior.
- The compat check never enters vrs's own launch path and vrs never imports `plan_readiness` (single-direction dependency; recorded queue decision).
- `--sweep` exit semantics stay anomaly-driven (exit 1 only for Summary parse anomalies and missing `reviews_dir`); the coverage counter is informational and must not change any exit code, because the review-loop wiring keys on the exit code.
- Review Scope freeze: all other functions in `scripts/plan_readiness.py` and `scripts/validate_review_staging.py` beyond the named regions are frozen; reject findings touching them as out of scope (track separately if real).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/plan_readiness.py` (regions only: module constants, `_check_sibling_compat` + `main()` launch gate, `evaluate_readiness` verdict step, `run_sweep`, `run_selftest` fixture additions; all other functions frozen)
- `scripts/validate_review_staging.py` (regions only: `COMPAT_VERSION` constant near `SUPPORTED_SIDECAR_SCHEMA_VERSIONS`, `V1_OPTIONAL_TOP_LEVEL_FIELDS` + its comment, the version-1 optional-field type-gate region, one selftest smoke check + verdict-field checks; all 5600+ other lines frozen)

**Tests:**
- selftest harnesses live inside the two scripts above (no separate test files)

**Docs:**
- `agents/skills/review-staging/SKILL.md` (optional-fields sentence, one line)
- `agents/skills/review-plan/SKILL.md` (inlined schema Optional segment, canonical-verdict-line paragraph, Integration Points validator paragraph)
- `agents/skills/review-loop/SKILL.md` (one new pre-round paragraph at the tail of the Resolve scope (Step 0) section)
- `agents/hooks/plan-readiness/README.md` (verdict representation section, sweep section, deployment note)
- `docs/history/backlog/2026-09-05-plan-readiness-legacy-verdict-grammar-deletion.md` *(new)*
- the three origin backlog files (Status line + disposition edits ride their `git mv` to `{backlog_completed_dir}`)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/summarize_review_stats.py`; reason: consumes `classify_sidecar_schema` labels, which this plan does not change (an optional field addition alters no label or adapter routing)
- `docs/plans/2026-09-02-validator-pass.md` and every other certified plan; reason: certified artifacts with digest-bound reviews on other branches; amending them breaks their certification binding
- `scripts/check_backlog_inbox_location.py`, `scripts/hooks_probe.py`; reason: unrelated gates, untouched by this plan
- `.ai-playbook/facts.md`; reason: no new facts keys introduced

## Validation Commands

```bash
cd "$(git rev-parse --show-toplevel)" || exit 1
python3 scripts/plan_readiness.py --selftest || { echo "FAIL: plan_readiness selftest"; exit 1; }
python3 scripts/validate_review_staging.py --selftest || { echo "FAIL: vrs selftest"; exit 1; }
python3 scripts/plan_readiness.py --sweep || { echo "FAIL: sweep"; exit 1; }
# Docs obligations: one dedicated flatten-grep per obligation (newline-tolerant:
# prose rewrapping replaces a space with a newline and tr restores exactly one
# space, so each pin matches wherever its sentence is wrapped). Each fails when
# ITS obligation is absent.
doc_has() { tr '\n' ' ' < "$2" | grep -qF "$1" || { echo "FAIL: missing in $2: $1"; exit 1; }; }
doc_has '`domains` (list), `verdict` (string `yes` or `no`; the plan-review producer' agents/skills/review-staging/SKILL.md
doc_has '`domains` (list), `verdict` (string `yes` or `no`; this skill writes it' agents/skills/review-plan/SKILL.md
doc_has 'The same verdict is recorded in the sidecar `verdict` field' agents/skills/review-plan/SKILL.md
doc_has 'the verdict is established from the sidecar `verdict` field first' agents/skills/review-plan/SKILL.md
doc_has 'Summary-only edits no longer flip readiness' agents/skills/review-plan/SKILL.md
doc_has 'Verdict-shape drift check (every round, before launching the review)' agents/skills/review-loop/SKILL.md
doc_has 'Consumer precedence is sidecar verdict field > Summary total rule' agents/hooks/plan-readiness/README.md
doc_has 'The check lives ONLY in the plan_readiness launch path' agents/hooks/plan-readiness/README.md
doc_has 'sidecar verdict field; legacy Summary grammar deletion is' scripts/plan_readiness.py
# Forbidden: the superseded backlogged-wiring sentence must be gone from the
# hook README. Flattened sweep: the phrase is line-wrapped in the file today,
# so a bare line-based grep would never fire (verified at authoring).
if tr '\n' ' ' < agents/hooks/plan-readiness/README.md | grep -qF 'as a pre-round check is backlogged'; then echo "FAIL: stale backlogged-sweep sentence"; exit 1; fi
# Forbidden: no em-dashes in the plan file, the four edited docs, and the new
# backlog item. Scope note (r1 F1 fold): the two validators' frozen regions
# already contain em-dashes (15 + 23 lines today); this plan introduces none
# because every prescribed artifact is fenced verbatim in this plan, and the
# plan file itself is checked here.
for f in docs/plans/2026-09-05-plan-readiness-migration.md agents/skills/review-staging/SKILL.md agents/skills/review-plan/SKILL.md agents/skills/review-loop/SKILL.md agents/hooks/plan-readiness/README.md docs/history/backlog/2026-09-05-plan-readiness-legacy-verdict-grammar-deletion.md; do
  test -f "$f" || { echo "FAIL: missing must-fix file $f"; exit 1; }
  if grep -qF $'\xe2\x80\x94' "$f"; then echo "FAIL: em-dash in $f"; exit 1; fi
done
bash scripts/scan-public-hygiene.sh || { echo "FAIL: hygiene scan"; exit 1; }
```

The em-dash loop pre-checks every swept path (fail-closed on a missing file), and the hygiene scan runs from the repo root by design (anchor preserved by the leading `cd`). The grep patterns above carry no self-match risk: every pattern is swept against target files that do NOT embed this plan, and the one forbidden-pattern phrase appears only in this plan file and in the hook README sentence being DELETED, never in the other swept targets. The `sweep coverage` pin deliberately uses the in-part fragment `sidecar verdict field; legacy Summary grammar deletion is` because Task 4 prescribes the print as an exact wrapped f-string and that fragment must sit inside ONE string part (the plain-text pin text greps scripts/plan_readiness.py where the phrases `sidecar verdict field reports` (Task 3 reason) and the fixture prose also live, so the semicolon continuation is what makes it unique).

### Task 1: Sibling compat handshake (backlog: validator-sibling-version-check, detection/backstop half)

Files:
- `scripts/validate_review_staging.py`
- `scripts/plan_readiness.py`

- [x] vrs: declare `COMPAT_VERSION = 1` (plain int) directly above `SUPPORTED_SIDECAR_SCHEMA_VERSIONS`, with a comment stating the contract: consumers pair against the value they shipped with; bump ONLY together with every consumer's expected constant
- [x] `plan_readiness.py`: declare `EXPECTED_SIBLING_COMPAT_VERSION = 1` after the imports; add `_check_sibling_compat() -> str | None` returning a named error when `getattr(vrs, "COMPAT_VERSION", None)` is missing (`sibling validate_review_staging.py does not declare COMPAT_VERSION; the deployment is a partial update`) or mismatched (`sibling validate_review_staging.py COMPAT_VERSION {declared!r} != expected {EXPECTED_SIBLING_COMPAT_VERSION!r}; the deployment is a partial update with divergent shared-rule semantics`); call it in `main()` immediately after `args = parser.parse_args(argv)` and before the `--selftest` dispatch, printing `compatibility FAILED: <error>` to stderr and returning 1
- [x] `selftest#sibling_compat/real_pair_match`; given the unpatched in-process pair, expects `vrs.COMPAT_VERSION` to equal `EXPECTED_SIBLING_COMPAT_VERSION` (uses `getattr(..., None)` so the check reads False, not crashes, while the constant is missing)
- [x] `selftest#sibling_compat/mismatch_fails_loud`; given `vrs.COMPAT_VERSION` set to `999` (try/finally restore; at RED time vrs does not yet declare the constant, so the finally-restore must handle absence via `delattr`, never reassignment of a saved value), expects `run_main(["--sweep"])` to return 1 with `compatibility FAILED` and `999` on stderr and no `sweep` output line on stdout. Run → expect RED: today the sweep runs normally (rc 0, `sweep OK`) because no check exists; verified RED at authoring. Place this fixture and `missing_constant` inside the `try:` block that follows `os.chdir(root)` in `run_selftest` (immediately before the `# accepted:` CLI fixture), where the `run_main` helper is in scope and `--sweep` resolves the temp tree's facts rather than the live repo
- [x] `selftest#sibling_compat/missing_constant`; given the `COMPAT_VERSION` attribute deleted from vrs via `delattr` guarded by `hasattr` (try/finally restore; while the attribute is absent the check asserts False with detail `vrs does not declare COMPAT_VERSION (handshake not implemented)` so the RED state is an explicit FAIL, never an AttributeError), expects `run_main(["--sweep"])` to return 1 with the missing-constant named error. Run → expect RED: explicit FAIL today for the same missing-constant reason
- [x] vrs selftest: alongside the `v1 contract: schema classifier` checks, add `check("compat handshake: COMPAT_VERSION declared (int >= 1)", isinstance(globals().get("COMPAT_VERSION"), int) and globals().get("COMPAT_VERSION") >= 1)`. Run → expect RED: explicit FAIL today (constant missing), GREEN after the declaration lands
- [x] Run → expect GREEN: `python3 scripts/validate_review_staging.py --selftest` passes (new smoke check + untouched existing checks); `python3 scripts/plan_readiness.py --selftest` passes with all three new `sibling_compat` fixtures; at this task point the verdict, sweep-coverage, and tie-break fixtures do not exist yet
- [x] Commit: `feat: sibling compat handshake for plan_readiness (COMPAT_VERSION)`

### Task 2: Sidecar verdict field, schema + producer contract (backlog: sidecar-verdict-field, producer half)

Files:
- `scripts/validate_review_staging.py`
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/review-plan/SKILL.md`

- [x] vrs: extend `V1_OPTIONAL_TOP_LEVEL_FIELDS` to `("depth", "domains", "verdict", "extensions")` and its comment to document the new documented type (`verdict` string `yes`/`no`)
- [x] vrs: after the existing `depth`/`domains` type-gate loop, add the verdict gate: `if "verdict" in payload and payload["verdict"] not in ("yes", "no")` then `result.add_error("version-1 sidecar field 'verdict' must be 'yes' or 'no'")` (explicit null is REJECTED: a round always has a verdict, and null would blur absent-fallback semantics)
- [x] vrs selftest, inside `_selftest_versioned_schema_and_patterns`, alongside its existing `v1 contract:` checks (r6 F5 fold, r7 F2 reword: the earlier `v1 contract: schema classifier` anchor string exists only at the schema-classification check; the new anchor names the function explicitly to remove placement ambiguity): (a) the valid base payload with `"verdict": "yes"` passes `validate_staging_file(..., hard=True)`; (b) with `"verdict": "maybe"` fails hard with an error containing `field 'verdict' must be 'yes' or 'no'`; (c) with `"verdict": None` fails with the same named error; (d) with `"verdict": True` fails with the same named error. Run → expect RED: today (a) dies on the unknown-top-level-field rejection and (b)-(d) report the WRONG error text; verified RED at authoring (the unknown-field gate exists, the named verdict gate does not)
- [x] `review-staging/SKILL.md` line with anchor `Optional top-level fields:`: replace that one-line sentence with exactly this one line (the example JSON stays untouched: producers other than review-plan are permitted, not required, to write the field):

```text
Optional top-level fields: `depth` (string), `domains` (list), `verdict` (string `yes` or `no`; the plan-review producer writes it alongside the `## Summary`), `extensions` (object). Any other top-level field is rejected; future extensions belong inside the object-valued `extensions` (a non-object `extensions` value is rejected).
```
- [x] `review-plan/SKILL.md` inlined schema bullet: rewrite its `Optional:` segment (same line, up to and including `any other top-level field is rejected).`) to exactly:

```text
Optional: `depth` (string), `domains` (list), `verdict` (string `yes` or `no`; this skill writes it in the same pass as the `## Summary`, matching the round's final verdict), `extensions` (object; all future extra data belongs inside it; any other top-level field is rejected).
```
- [x] `review-plan/SKILL.md` canonical-verdict-line paragraph (anchor `Canonical verdict line`): append this sentence verbatim:

```text
The same verdict is recorded in the sidecar `verdict` field in the same pass; the readiness validator prefers the sidecar field and falls back to Summary parsing only for artifacts whose sidecar lacks it.
```
- [x] `review-plan/SKILL.md` Integration Points validator paragraph (r4 F2 fold; r6 F1+F3 refold): in the paragraph's final sentence, replace the ENTIRE final sentence, which wraps `ready=yes` and `## Summary` in backticks, from `and the review Markdown reports` through the closing paren of `(`is_review_ready`)`, as a full-sentence replacement block with exactly:

```text
and reports zero unresolved blocking findings (`is_review_ready`); the verdict is established from the sidecar `verdict` field first, with the Summary total rule over the review Markdown as the legacy fallback.
```
(r4 F4 fold: the shipped sentence keeps the blocking-findings clause earlier, joined by a semicolon with `and reports zero unresolved blocking findings`; the fence records the prescription, not the final bytes.)
(r5 executed-shape note: the shipped sentence carries further wording from the later r7 F1 fold about Summary-only edits; the fence records the prescription, not the final bytes.)

Then, in the SAME paragraph, replace the clause beginning `while a post-round edit of the review Markdown itself is caught` through the end of the paragraph with exactly (r7 F1 fold: replace the CLAUSE, never the whole sentence; the preceding `The sidecar digest covers the PLAN bytes only:` statement is load-bearing and must stay intact):

```text
while a post-round edit of the review Markdown is still caught when it breaks the blocking consistency the validator recomputes over the current review text; once the sidecar carries a conforming `verdict` field, the Summary verdict token is no longer consulted, so Summary-only edits no longer flip readiness.
```
- [x] Run → expect GREEN: `python3 scripts/validate_review_staging.py --selftest` passes with the four new checks; `python3 scripts/plan_readiness.py --selftest` still passes (its selftest sidecars do not carry the field yet; the version-1 path change is additive)
- [x] Commit: `feat: sidecar verdict field (v1 schema + review-plan producer contract)`

### Task 3: Consumer precedence, sidecar verdict over Summary grammar (backlog: sidecar-verdict-field, consumer half)

Files:
- `scripts/plan_readiness.py`

- [x] Replace the verdict step (step 4) of `evaluate_readiness` with the precedence rule: read `verdict_field = sidecar_verdict(payload)` via the new module-level helper (next bullet; r6 F6 fold: single owner of the conforming-verdict predicate); when it equals `"yes"` or `"no"` the field is DECISIVE: on `"no"` return False with `latest review r{N} sidecar verdict field reports 'no'`, on `"yes"` proceed to condition 5. For ANY other value (absent, or a non-conforming legacy value such as a dict or a non-yes/no string) run the existing Summary total rule unchanged (same reason text): version-1 records with non-conforming values never reach this step because the Task 2 schema gate rejects them earlier, while versionless legacy records keep today's tolerance (r2 F1 fold: the live corpus carries legacy `verdict` keys including two dict-valued plan-review sidecars, so a rejecting consumer would newly fail artifacts that pass today, contradicting the fallback invariant). A probe at authoring confirmed a versionless sidecar with a `verdict` key is silently tolerated today; this rule keeps that behavior
- [x] Add the module-level helper in the verdict-step region's neighborhood (r6 F6 fold, in-scope region): `def sidecar_verdict(payload: dict) -> str | None:` returning `payload.get("verdict")` when that value is `"yes"` or `"no"`, else `None`; the Task 4 coverage counter routes through this same helper so the conforming-verdict predicate has ONE owner
- [x] Extend the `VERDICT_TOKEN_RE` comment block with the precedence note: sidecar verdict field preferred; the per-line total rule is the legacy fallback for pre-adoption artifacts; deletion is time-gated and tracked in the spin-off backlog item
- [x] `selftest#verdict_field/sidecar_yes_summary_silent_passes`; given a clean sidecar carrying `"verdict": "yes"` and a review whose Summary contains NO `ready=` token (`_review_markdown(verdict_line="Counts confirmed in Review Statistics; the verdict lives in the sidecar verdict field.")`), expects `evaluate_readiness` to return ok. Run → expect RED: today the missing Summary token fails readiness with the legacy reason; probe-verified RED at authoring
- [x] `selftest#verdict_field/sidecar_no_overrides_summary_yes`; given a clean sidecar carrying `"verdict": "no"` and `_review_markdown(verdict="yes")`, expects not-ok with a reason containing `sidecar verdict field reports`. Run → expect RED: today the prose token passes readiness; probe-verified RED at authoring
- [x] `selftest#verdict_field/sidecar_yes_overrides_summary_no`; given a clean sidecar carrying `"verdict": "yes"` and `_review_markdown(verdict="no")`, expects ok. Run → expect RED: today the prose `ready=no` token fails readiness
- [x] `selftest#verdict_field/legacy_verdict_junk_falls_back`; given (arm a) a clean sidecar carrying `"verdict": "maybe"` and `_review_markdown(verdict="yes")`, expects ok; and given (arm b) a clean sidecar carrying a dict-valued `"verdict": {"ready": false}` and `_review_markdown(verdict="no")`, expects not-ok with the LEGACY reason containing `does not report a ready=yes verdict` (the junk field neither decides nor fails readiness). Run → expect GREEN (characterization: pins the r2 F1 fold semantics, which today's code already exhibits since the key is ignored; the corpus carries real dict-valued keys)
- [x] `selftest#verdict_field/absent_falls_back_to_summary`; given a clean sidecar WITHOUT the field and `_review_markdown(verdict="no")`, expects not-ok with the existing legacy reason containing `does not report a ready=yes verdict`. Run → expect GREEN (characterization: the fallback path must survive Task 3 unchanged)
- [x] Run → expect GREEN: `python3 scripts/plan_readiness.py --selftest` passes with the five new fixtures plus Tasks 1's; `python3 scripts/validate_review_staging.py --selftest` still passes; at this task point the sweep prints no coverage line yet
- [x] Commit: `feat: readiness consumer prefers sidecar verdict over Summary grammar`

### Task 4: Sweep coverage counter (backlog: sidecar-verdict-field, deletion-gate enabler)

Files:
- `scripts/plan_readiness.py`

- [x] Extend `run_sweep`: over the same `*-plan-review-*.md` glob, count `total` artifacts and `covered` artifacts whose `vrs.stats_sidecar_path(path)` sidecar exists, parses as JSON, and carries a conforming `verdict` per the Task 3 `sidecar_verdict` helper (r6 F6 fold: no second yes/no membership test); unreadable or malformed sidecars count as NOT covered and are NOT anomalies. After the anomaly list, print exactly this statement on exactly the TWO exits that follow the glob (the anomaly-failure return and the clean return); the missing-`reviews_dir` early return prints only its own error and NO coverage line (r1 F3 fold: this reading is pinned by a fixture below). The statement, wrapping as shown so the validation pin `sidecar verdict field; legacy Summary grammar deletion is` sits inside ONE string part:

```python
    print(
        f"sweep coverage: {covered}/{total} plan-review artifacts carry a "
        "sidecar verdict field; legacy Summary grammar deletion is "
        "eligible only when covered equals total"
    )
```

Exit codes unchanged: anomalies and a missing `reviews_dir` still decide
- [x] `selftest#sweep/coverage_mixed_corpus`; clean the reviews dir before building the corpus and after (as the neighboring sweep fixtures do; r6 F2 fold: the preceding `sweep/plan_path_rejected` fixture leaves one artifact behind); given two clean artifacts built at DISTINCT paths (arm 1 via `write_clean_state()` defaults; arm 2 via `write_clean_state(date="2026-09-02")` with `"verdict": "yes"` added to its sidecar, so arm 2's plan and review filenames do not collide with arm 1's, r4 F1 fold), expects `run_main(["--sweep"])` rc 0 with `sweep coverage: 1/2` on stdout. Run → expect RED: today no coverage line is printed
- [x] `selftest#sweep/coverage_malformed_sidecar_uncovered`; clean the reviews dir before building the corpus and after (same r6 F2 fold reason); given one clean artifact via `write_clean_state()` defaults plus one artifact written at the distinct path `2026-09-02-plan-review-fixture-feature-r1.md` whose sidecar is the string `not json` (r4 F1 fold: distinct paths), expects rc 0, coverage `0/2`, and no crash. Run → expect RED: no coverage line today. The coverage counter tests sidecars through the Task 3 `sidecar_verdict` helper, not a re-stated yes/no test
- [x] `selftest#sweep/coverage_absent_on_missing_reviews_dir`; given a facts file whose `reviews_dir` points at a missing directory, expects `run_main(["--sweep"])` rc 1 with `sweep FAILED` on stderr and NO `sweep coverage:` line on stdout. Run → expect GREEN (characterization: pins the decided early-return reading, which today's code already exhibits since no coverage line exists yet); clean the reviews dir between fixtures as the neighboring sweep fixtures do
- [x] Run → expect GREEN: `python3 scripts/plan_readiness.py --selftest` passes with the new fixtures AND the pre-existing `sweep/*` fixtures (their `sweep OK` / rc pins are untouched; the coverage line is additive); `python3 scripts/plan_readiness.py --sweep` over the live corpus exits 0 and prints a real N/M line. At this task point the review-loop wiring and the tie-break fixture do not exist yet
- [x] Commit: `feat: sweep reports sidecar-verdict corpus coverage`

### Task 5: Review-loop pre-round wiring + hook README docs (backlog: sidecar-verdict-field related follow-up; version-check documentation)

Files:
- `agents/skills/review-loop/SKILL.md`
- `agents/hooks/plan-readiness/README.md`

- [x] `review-loop/SKILL.md`, immediately AFTER the paragraph containing the anchor `Do not cache the file set from round 1` (the tail of the "Resolve scope (Step 0)" section, r3 F1 fold), insert this paragraph verbatim:

```text
**Verdict-shape drift check (every round, before launching the review):** run `python3 scripts/plan_readiness.py --sweep`, resolving the script via the env-override, repo-local, then deployed-runtime fallback documented in `agents/hooks/plan-readiness/README.md`. A non-zero exit means the plan-review corpus carries verdict-parse anomalies; stop before launching this round's workers and resolve the listed anomalies first. The sweep's coverage line is informational: it tracks how much of the corpus still predates the sidecar verdict field.
```
(r3 review-fix note: the shipped paragraph broadens the non-zero-exit meaning to name a missing or misconfigured reviews_dir and a sibling compatibility failure; the fence records the prescription, not the final bytes.)
- [x] hook README, Verdict representation section: replace the tail that starts at the sentence with anchor text `Consumer precedence is` (currently reading the sidecar field as future and deferring to a backlog item) with exactly (r6 F7 fold: the backlog file linked below is created later in Task 7, so this commit transiently carries a dangling link; accepted):

```text
Consumer precedence is sidecar verdict field > Summary last-token rule: when the latest round's sidecar carries a `verdict` field (`yes`/`no`, written by `review-plan` since the 2026-09-05 plan-readiness-migration plan), it decides; artifacts whose sidecar lacks the field fall back to the Summary total rule. Deleting the legacy Summary grammar is TIME-GATED: eligible only once `--sweep` coverage reports covered equal to total over the live plan-review corpus; tracked in `docs/history/backlog/2026-09-05-plan-readiness-legacy-verdict-grammar-deletion.md`.
```
(r3 F3 fold: the shipped tail reads `fall back to that rule` after the r2 dual-name fix; the fence above records the Task 5 prescription, not the final bytes.)
(r4 F5 fold: the shipped headline reads `Consumer precedence is sidecar verdict field > Summary total rule (per-line, last occurrence wins):` after the r4 dual-name unification; the fence records the prescription, not the final bytes.)
- [x] hook README, Drift check section: insert this sentence after the exit-semantics sentence, and replace the sentence containing `as a pre-round check is backlogged` with exactly (r4 F2 fold):

```text
The sweep also prints a coverage line counting live plan-review artifacts whose sidecar carries a conforming `verdict` field; it is informational and never changes the exit code.
```

```text
Wiring note: review-loop runs this sweep before every round (its verdict-shape drift check).
```
- [x] hook README, Deployment note: append a paragraph starting with `Sibling compatibility handshake:` that states: vrs declares `COMPAT_VERSION`; the readiness validator checks it at every launch (gate, sweep, selftest modes) and fails loudly on a missing or mismatched value; the check catches a partially updated deployment in both repo-local and runtime copies, and post-symlink-unification it also trips when a symlink is replaced by a stale snapshot copy unless the whole pair was replaced together (the both-stale-consistent case stays invisible; accepted Low-severity residual). End the paragraph with this sentence verbatim:

```text
The check lives ONLY in the plan_readiness launch path; validate_review_staging.py never imports plan_readiness.
```
- [x] Run → expect GREEN: the Validation Commands doc-grep section passes; both selftests still pass (docs-only task). Restrict this interim run to the doc-grep lines and the forbidden-README check; the em-dash loop and the full Validation block run only at Task 8 (the em-dash loop is one line inside that block; its `test -f` pre-check fails on the Task 7 backlog file, which does not exist yet). At this task point the tie-break fixture does not exist yet
- [x] Commit: `docs: review-loop pre-round sweep + hook README verdict precedence and compat handshake`

### Task 6: Same-N cross-date tie-break fixture (backlog: same-n-tie-break-fixture)

Files:
- `scripts/plan_readiness.py`

- [x] In `run_selftest`, immediately after the `uppercase_round_suffix_ignored` block's cleanup loop, add the two-arm characterization fixture using the existing `write_clean_state`, `_review_markdown`, and `_clear_sidecar` helpers. Arm 1 `selftest#latest_round_selection_tie_break/later_dated_decides`: given `write_clean_state(verdict="yes", round_suffix="r1", date="2026-09-01")` plus a manually written `2026-09-02-plan-review-fixture-feature-r1.md` with `_review_markdown(verdict="no")` and a `_clear_sidecar(digest)` sidecar over the SAME plan bytes, and given the earlier-dated artifact AND its sidecar forced to mtime 4102444800.0 (year 2100, so any mtime participation would flip the winner), expects not-ok with `r1` in the reason. Arm 2 `selftest#latest_round_selection_tie_break/inverted_polarity_ok`: same construction with verdicts swapped (earlier `ready=no`, later `ready=yes`) and the same adversarial mtime on the earlier pair, expects ok. Clean the reviews dir between the arms and after
- [x] Run → expect GREEN (characterization: the fixture pins behavior that is correct today; both polarities probe-verified at authoring under the same adversarial mtimes). Run the full `python3 scripts/plan_readiness.py --selftest`
- [x] Commit: `test: pin same-N cross-date tie-break in latest_review_round`

### Task 7: Deletion spin-off + backlog origin bookkeeping

Files:
- `docs/history/backlog/2026-09-05-plan-readiness-legacy-verdict-grammar-deletion.md` *(new)*
- `docs/history/backlog/2026-09-03-plan-readiness-same-n-tie-break-fixture.md` (move + status)
- `docs/history/backlog/2026-09-04-plan-readiness-sidecar-verdict-field.md` (move + status)
- `docs/history/backlog/2026-09-04-validator-sibling-version-check.md` (move + status)

- [x] Create the spin-off item `docs/history/backlog/2026-09-05-plan-readiness-legacy-verdict-grammar-deletion.md` with `Status: open`, `Workflow: backlog`, source line citing the sidecar-verdict-field item's acceptance criterion 3 and this plan, `Severity: Low (time-gated)`, `Scope: scripts/plan_readiness.py`. Problem: the Summary total-rule grammar remains in `evaluate_readiness` as the legacy fallback for pre-adoption artifacts. Eligibility gate: eligible only when `python3 scripts/plan_readiness.py --sweep` prints coverage with covered equal to total (every live `*-plan-review-*.md` sidecar carries the verdict field). The item must also disposition verdict-source drift (r6 F3 fold): its fix either adds a sweep anomaly for a conforming sidecar `verdict` that contradicts the artifact Summary's last verdict token, or explicitly records the end of Summary-token drift detection as an accepted consequence of the deletion. Suggested fix: delete the Summary fallback path from the verdict step (keep the sweep's mention detector), keeping the sidecar field as the sole verdict source. No em-dashes in the file
- [x] `git mv` each of the three origin files to `docs/history/backlog/completed/` and in the SAME commit edit each moved file: `Status: done` plus one `Resolution (2026-09-05, plan-readiness-migration):` disposition line. Dispositions: tie-break item, fixture landed in the selftest's `latest_round_selection` family, both polarities pinned; sidecar item, producer + schema + consumer precedence landed, deletion half spun off to the new 2026-09-05 item; version-check item, unification half was already done 2026-09-04, detection/backstop half landed as the consumer-side-only COMPAT_VERSION handshake with the both-stale residual documented, and the origin acceptance criterion `both validators' selftests cover the mismatch path` is deliberately narrowed to: plan_readiness's selftest covers the mismatch and missing-constant paths while vrs's selftest covers the constant declaration (a mutual check is impossible without an import cycle)
- [x] Verify the rename + content pairing per the rename-commit trap: `git show HEAD:docs/history/backlog/completed/<name>` carries `Status: done` for all three, not just the rename
- [x] Run → expect GREEN: the Validation Commands doc greps still pass (the deletion item exists; the origin paths in earlier greps are unaffected)
- [x] Commit: `docs: archive plan_readiness migration backlog origins + deletion spin-off`

### Task 8: Final validation

Files: none (checks only)

- [x] Run the full `## Validation Commands` block from the repo root; every check exits 0 (selftests, sweep over the live corpus, doc greps, forbidden-pattern sweeps, hygiene scan)
- [x] `python3 scripts/plan_readiness.py --sweep` output shows the live corpus coverage count N/M on one line and exits 0
- [x] If any check fails: fix and re-run the whole block; only then report the task complete (no commit line unless a fix was needed; a fix commit reuses the owning task's commit prefix)

## Disposition of migrated backlog items

- docs/history/backlog/completed/2026-09-05-plan-readiness-migration-r5-residuals.md: disposition folded into 2026-09-05-plan-readiness-migration.md (2026-09-25); per-item file deleted.
